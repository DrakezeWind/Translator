import json
import os
from datetime import datetime, timezone
from pathlib import Path

# HISTORY_FILE_PATH lets deployments point history at a mounted persistent
# volume (e.g. Fly.io); defaults to the project root for local dev.
HISTORY_FILE = Path(os.environ.get(
    "HISTORY_FILE_PATH",
    Path(__file__).resolve().parent.parent / ".translator_history.json",
))
MAX_ENTRIES = 20


def append_entry(source_lang: str, target_lang: str, source_text: str, translated_text: str) -> None:
    entries = _load_all()
    entries.append({
        "source_lang": source_lang,
        "target_lang": target_lang,
        "source_text": source_text,
        "translated_text": translated_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    entries = entries[-MAX_ENTRIES:]
    HISTORY_FILE.write_text(json.dumps(entries, indent=2))


def load_recent(limit: int = 3) -> list[dict]:
    entries = _load_all()
    return list(reversed(entries[-limit:]))


def _load_all() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text())
    except json.JSONDecodeError:
        return []
