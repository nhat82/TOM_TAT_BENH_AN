from typing import Any

from app.core.config import settings

class PIIMasker:
    def __init__(self) -> None:
        self._column_counter: dict[str, int] = {col: 0 for col in settings.masked_fields}
        self._message_converter: dict[str, dict[str, str]] = {}

    def mask(self, message_key: str, rows: list[dict[str, Any]]):
        self._message_converter[message_key] = {}
        for row in rows:
            for col in settings.masked_fields:
                if col in row:
                    self._column_counter[col] += 1

                    raw_value = row[col]
                    masked_value = f"[{col}_{self._column_counter[col]}]"
                    row[col] = masked_value

                    self._message_converter[message_key][masked_value] = raw_value

    def unmask(self, message_key: str, response: str):
        for masked_value, raw_value in self._message_converter[message_key].items():
            response = response.replace(masked_value, str(raw_value))
            print(f"Unmasking {masked_value} -> {raw_value}")
        return response

    def forget(self, message_key: str):
        self._message_converter.pop(message_key, None)

pii_masker = PIIMasker()
