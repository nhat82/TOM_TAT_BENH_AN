import re
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator

from app.core.config import backend_config

MASKED_COLUMNS: frozenset[str] = backend_config.masked_fields

_PLACEHOLDER_RE = re.compile(r"\[([a-z0-9_]+)\]")


def is_masked_column(column: str) -> bool:
    return column.strip().lower() in MASKED_COLUMNS


# ── vault ─────────────────────────────────────────────────────────────────────

class MaskVault:
    """placeholder <-> raw value, for one conversation thread.

    Mutated from the tool (possibly on a worker thread) and read from the
    router, hence the lock.
    """

    def __init__(self) -> None:
        self._to_raw: dict[str, str] = {}          # "[ho_ten_1]" -> "Nguyễn Văn A"
        self._to_placeholder: dict[tuple[str, str], str] = {}
        self._counters: dict[str, int] = {}
        self._lock = threading.Lock()

    def register(self, column: str, value: Any) -> str:
        """Returns the placeholder for this (column, value), creating it once."""
        column = column.strip().lower()
        raw = str(value)
        key = (column, raw)
        with self._lock:
            existing = self._to_placeholder.get(key)
            if existing is not None:
                return existing
            index = self._counters.get(column, 0) + 1
            self._counters[column] = index
            placeholder = f"[{column}_{index}]"
            self._to_placeholder[key] = placeholder
            self._to_raw[placeholder] = raw
            return placeholder

    def resolve(self, placeholder: str) -> str | None:
        with self._lock:
            return self._to_raw.get(placeholder)

    def pairs(self) -> list[tuple[str, str]]:
        """(raw value, placeholder), longest raw first — for re-masking."""
        with self._lock:
            items = list(self._to_raw.items())
        return sorted(((raw, ph) for ph, raw in items), key=lambda p: -len(p[0]))

    def max_placeholder_length(self) -> int:
        with self._lock:
            known = max((len(p) for p in self._to_raw), default=0)
        # Room for a placeholder not registered yet.
        return max(known, max(len(c) for c in MASKED_COLUMNS) + 6)


_vaults: dict[str, MaskVault] = {}
_vaults_lock = threading.Lock()
_current_vault: ContextVar[MaskVault | None] = ContextVar("current_vault", default=None)


def get_vault(thread_id: str) -> MaskVault:
    """The vault for a conversation thread, created on first use.

    Lives as long as the process, like the agent's InMemorySaver checkpoint.
    """
    with _vaults_lock:
        vault = _vaults.get(thread_id)
        if vault is None:
            vault = MaskVault()
            _vaults[thread_id] = vault
        return vault


def current_vault() -> MaskVault | None:
    """The vault bound to the running request, if any."""
    return _current_vault.get()


@contextmanager
def masking_context(vault: MaskVault) -> Generator[MaskVault]:
    """Binds `vault` for every mask_rows() call made while running the agent."""
    token = _current_vault.set(vault)
    try:
        yield vault
    finally:
        _current_vault.reset(token)


# ── masking (tool side) ───────────────────────────────────────────────────────

def mask_row(row: dict[str, Any]) -> dict[str, Any]:
    vault = _current_vault.get()
    masked: dict[str, Any] = {}
    for column, value in row.items():
        if not is_masked_column(column) or value in (None, ""):
            masked[column] = value
        elif vault is None:
            # No active request scope: mask without a way back, never leak.
            masked[column] = f"[{column.strip().lower()}]"
        else:
            masked[column] = vault.register(column, value)
    return masked


def mask_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [mask_row(row) for row in rows]


# ── unmasking (API boundary only) ─────────────────────────────────────────────

def unmask_text(text: str, vault: MaskVault) -> str:
    """Replaces "[ho_ten_1]" & co. with real values. Unknown ones stay as-is."""
    if not text:
        return text
    return _PLACEHOLDER_RE.sub(
        lambda m: vault.resolve(m.group(0)) or m.group(0), text
    )


def remask_text(text: str, vault: MaskVault) -> str:
    """Inverse of unmask_text: real values -> placeholders.

    Needed when already-exposed text (chat history, a summary edited in the UI)
    is sent back in, so PII does not re-enter the model context.
    """
    if not text:
        return text
    for raw, placeholder in vault.pairs():
        text = text.replace(raw, placeholder)
    return text


class StreamingUnmasker:
    """Unmasks a token stream where a placeholder may straddle chunk boundaries.

    feed() emits everything that can no longer be part of a placeholder and
    holds back the rest; flush() releases the tail at end of stream.
    """

    def __init__(self, vault: MaskVault):
        self._vault = vault
        self._buffer = ""

    def feed(self, token: str) -> str:
        self._buffer += token
        cut = self._safe_cut()
        if cut == 0:
            return ""
        emitted, self._buffer = self._buffer[:cut], self._buffer[cut:]
        return unmask_text(emitted, self._vault)

    def flush(self) -> str:
        emitted, self._buffer = self._buffer, ""
        return unmask_text(emitted, self._vault)

    def _safe_cut(self) -> int:
        """Index up to which the buffer can be emitted safely."""
        open_bracket = self._buffer.rfind("[")
        if open_bracket == -1:
            return len(self._buffer)
        tail = self._buffer[open_bracket:]
        if "]" in tail:                                       # already complete
            return len(self._buffer)
        if len(tail) > self._vault.max_placeholder_length():   # cannot become one
            return len(self._buffer)
        if not re.fullmatch(r"\[[a-z0-9_]*", tail):
            return len(self._buffer)
        return open_bracket                                    # hold the partial
