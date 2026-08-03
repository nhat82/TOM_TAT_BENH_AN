"""Audit logging for everything the agents do with tools.

Answers three questions from the log alone:

  1. Which tool did the model call, with which arguments, and how did it end?
  2. What rows came back from `run_sql_query` — always scrubbed, so no
     personally identifiable value ever reaches a log file.
  3. Did the model try anything other than a read (INSERT/UPDATE/DROP/...)?
     Such a statement is logged at WARNING with the offending keywords.

Scrubbing reuses the masking vault (see `masking.py`): identity columns become
their placeholder, and any raw value already registered in the vault is replaced
even when it shows up inside a free-text column. Logging is best effort — a
failure here must never break a tool call.

Records are emitted as single-line JSON under the "ai.audit" logger:

    LOG: ... INFO ai.audit — {"event": "tool_call", "tool": "run_sql_query", ...}
"""

from __future__ import annotations

import json
import logging
import re
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator

from .masking import MASKED_COLUMNS, current_vault, is_masked_column

log = logging.getLogger("ai.audit")

# Truncation limits — keep one log line readable and bounded.
MAX_LOGGED_ROWS = 5
MAX_VALUE_LENGTH = 120
MAX_SQL_LENGTH = 2000


# ── request scope ─────────────────────────────────────────────────────────────

_current_scope: ContextVar[dict[str, Any] | None] = ContextVar("audit_scope", default=None)


@contextmanager
def audit_context(**fields: Any) -> Generator[dict[str, Any]]:
    """Tags every audit record made inside with `fields` (thread_id, agent, ...)."""
    scope = dict(fields)
    token = _current_scope.set(scope)
    try:
        yield scope
    finally:
        _current_scope.reset(token)


def _emit(level: int, event: str, **fields: Any) -> None:
    record = {"event": event, **(_current_scope.get() or {}), **fields}
    try:
        line = json.dumps(record, ensure_ascii=False, default=str)
    except Exception:                                   # pragma: no cover
        line = repr(record)
    log.log(level, line)


# ── SQL inspection ────────────────────────────────────────────────────────────

# Anything that is not a plain read. Checked as whole words on SQL with string
# literals and comments removed, so a diagnosis text containing "update" or a
# column named `create_date` does not trigger a false positive.
NON_SELECT_KEYWORDS: frozenset[str] = frozenset({
    "insert", "update", "delete", "merge", "upsert", "replace",
    "drop", "create", "alter", "truncate", "rename", "comment",
    "grant", "revoke", "set", "reset",
    "copy", "vacuum", "analyze", "reindex", "cluster", "refresh",
    "call", "do", "execute", "prepare", "listen", "notify",
    "begin", "commit", "rollback", "savepoint", "lock",
    "pg_sleep", "pg_read_file", "pg_write_file", "dblink",
})

_ALLOWED_LEADING = frozenset({"select", "with", "table", "values", "explain", "show"})

_COMMENT_RE = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)
_STRING_RE = re.compile(r"('(?:''|[^'])*'|\"(?:\"\"|[^\"])*\")", re.DOTALL)
_WORD_RE = re.compile(r"[a-z_][a-z0-9_]*")


def _strip_noise(query: str) -> str:
    """SQL with comments and quoted literals/identifiers blanked out."""
    stripped = _COMMENT_RE.sub(" ", query)
    return _STRING_RE.sub(" ", stripped).lower()


def inspect_sql(query: str) -> dict[str, Any]:
    """Static read-only check on a statement the model wants to run.

    Returns {"read_only": bool, "operations": [...], "statements": int}.
    `operations` lists the non-SELECT keywords found, `statements` counts
    top-level statements (more than one means a stacked query).
    """
    body = _strip_noise(query or "")
    parts = [p for p in body.split(";") if p.strip()]
    words = _WORD_RE.findall(body)

    operations = sorted({w for w in words if w in NON_SELECT_KEYWORDS})
    leading = words[0] if words else ""
    if leading and leading not in _ALLOWED_LEADING and leading not in operations:
        operations = sorted({*operations, leading})

    return {
        "read_only": not operations and len(parts) <= 1,
        "operations": operations,
        "statements": len(parts),
    }


# ── scrubbing ─────────────────────────────────────────────────────────────────

def _scrub_value(column: str, value: Any) -> Any:
    """One cell, safe to log."""
    if value is None:
        return None
    if is_masked_column(column):
        # Already a placeholder if the tool masked it; mask again otherwise.
        text = str(value)
        if re.fullmatch(r"\[[a-z0-9_]+\]", text):
            return text
        vault = current_vault()
        return vault.register(column, text) if vault else f"[{column.strip().lower()}]"
    if isinstance(value, (int, float, bool)):
        return value

    text = str(value)
    # Defense in depth: a raw identity value leaking through a free-text column.
    vault = current_vault()
    if vault is not None:
        for raw, placeholder in vault.pairs():
            if raw and raw in text:
                text = text.replace(raw, placeholder)
    if len(text) > MAX_VALUE_LENGTH:
        text = text[:MAX_VALUE_LENGTH] + "…"
    return text


def scrub_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows with identity columns masked and long values truncated."""
    return [
        {column: _scrub_value(column, value) for column, value in row.items()}
        for row in rows
    ]


def scrub_parameters(parameters: dict[str, Any] | None) -> dict[str, Any]:
    """Bound SQL parameters, masked by parameter name where it names an identity."""
    return {
        name: _scrub_value(name, value) for name, value in (parameters or {}).items()
    }


def pii_columns(columns: list[str]) -> list[str]:
    return [c for c in columns if is_masked_column(c)]


# ── public logging API ────────────────────────────────────────────────────────

def log_tool_call(tool: str, **arguments: Any) -> float:
    """Logs the start of a tool call. Returns a start timestamp for `log_tool_result`."""
    _emit(logging.INFO, "tool_call", tool=tool, arguments=arguments)
    return time.perf_counter()


def log_tool_result(tool: str, started: float, status: str = "ok", **fields: Any) -> None:
    _emit(
        logging.INFO if status == "ok" else logging.ERROR,
        "tool_result",
        tool=tool,
        status=status,
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
        **fields,
    )


def log_sql_query(query: str, parameters: dict[str, Any] | None) -> dict[str, Any]:
    """Logs the SQL the model wants to run and returns its inspection result.

    A statement carrying anything beyond a read is logged at WARNING; the caller
    decides what to do with `read_only`.
    """
    verdict = inspect_sql(query)
    trimmed = query if len(query) <= MAX_SQL_LENGTH else query[:MAX_SQL_LENGTH] + "…"
    payload = {
        "sql": trimmed,
        "parameters": scrub_parameters(parameters),
        **verdict,
    }
    if verdict["read_only"]:
        _emit(logging.INFO, "sql_query", **payload)
    else:
        _emit(logging.WARNING, "sql_non_select", **payload)
    return verdict


def log_sql_rows(columns: list[str], rows: list[dict[str, Any]]) -> None:
    """Logs the result set: shape, which columns were PII, and scrubbed samples."""
    masked = pii_columns(columns)
    sample = scrub_rows(rows[:MAX_LOGGED_ROWS])
    _emit(
        logging.INFO,
        "sql_rows",
        columns=columns,
        masked_columns=masked,
        contains_pii=bool(masked),
        row_count=len(rows),
        truncated=len(rows) > MAX_LOGGED_ROWS,
        rows=sample,
    )


def log_tool_error(tool: str, started: float, error: BaseException, **fields: Any) -> None:
    log_tool_result(
        tool,
        started,
        status="error",
        error_type=type(error).__name__,
        error=str(error)[:MAX_VALUE_LENGTH],
        **fields,
    )


__all__ = [
    "MASKED_COLUMNS",
    "audit_context",
    "inspect_sql",
    "log_sql_query",
    "log_sql_rows",
    "log_tool_call",
    "log_tool_error",
    "log_tool_result",
    "scrub_parameters",
    "scrub_rows",
]
