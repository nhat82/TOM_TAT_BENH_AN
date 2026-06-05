from pathlib import Path

SYSTEM_PROMPT = (Path(__file__).parent / "SYSTEM_PROMPT.md").read_text()
FORCE_SYNTHESIS = (Path(__file__).parent / "FORCE_SYNTHESIS.md").read_text()
