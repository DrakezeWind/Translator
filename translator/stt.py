"""Server-side speech-to-text fallback for when the browser's Web Speech service is unreachable."""
import os
import time
from collections import defaultdict, deque

import httpx

WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-1"
MAX_AUDIO_BYTES = 5 * 1024 * 1024
RATE_LIMIT = 10  # requests per window, per client
RATE_WINDOW = 60.0

_EXTENSIONS = {"webm": "webm", "ogg": "ogg", "mp4": "mp4", "mpeg": "mp3", "wav": "wav", "x-wav": "wav"}


class SttError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class RateLimiter:
    """In-memory sliding window; fine for a single Fly machine."""

    def __init__(self, limit: int = RATE_LIMIT, window: float = RATE_WINDOW):
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if not hits:
            self._hits.pop(key, None)
            hits = self._hits[key]
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True


def audio_extension(content_type: str) -> str | None:
    """File extension for an audio content type, or None when it isn't audio."""
    base = content_type.split(";")[0].strip().lower()
    if not base.startswith("audio/"):
        return None
    return _EXTENSIONS.get(base.removeprefix("audio/"), "webm")


def whisper_language(code: str) -> str | None:
    """Whisper wants ISO-639-1 ('zh'), not BCP-47 ('zh-CN'); 'auto' means no hint."""
    if code == "auto":
        return None
    return code.split("-")[0]


async def transcribe(
    audio: bytes,
    content_type: str,
    language: str | None,
    client: httpx.AsyncClient | None = None,
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SttError(503, "Voice fallback not configured")
    ext = audio_extension(content_type)
    if ext is None:
        raise SttError(415, "Audio required")
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise SttError(413, "Audio empty or too large")

    data = {"model": WHISPER_MODEL}
    if language:
        data["language"] = language
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=30)
    try:
        res = await client.post(
            WHISPER_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (f"audio.{ext}", audio, content_type.split(";")[0])},
            data=data,
        )
    except httpx.HTTPError:
        raise SttError(502, "Transcription service unreachable")
    finally:
        if owns_client:
            await client.aclose()
    if res.status_code != 200:
        raise SttError(502, "Transcription failed")
    return (res.json().get("text") or "").strip()
