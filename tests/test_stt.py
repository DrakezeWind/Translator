import asyncio

import httpx
import pytest

from translator import stt


def test_rate_limiter_blocks_then_recovers():
    rl = stt.RateLimiter(limit=2, window=10)
    assert rl.allow("a", now=0)
    assert rl.allow("a", now=1)
    assert not rl.allow("a", now=2)
    assert rl.allow("b", now=2)  # separate client
    assert rl.allow("a", now=11)  # window passed


def test_audio_extension():
    assert stt.audio_extension("audio/webm;codecs=opus") == "webm"
    assert stt.audio_extension("audio/mp4") == "mp4"
    assert stt.audio_extension("text/plain") is None


def test_whisper_language():
    assert stt.whisper_language("auto") is None
    assert stt.whisper_language("zh-CN") == "zh"
    assert stt.whisper_language("es") == "es"


def _run(coro):
    return asyncio.run(coro)


def test_transcribe_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(stt.SttError) as e:
        _run(stt.transcribe(b"x", "audio/webm", None))
    assert e.value.status == 503


def test_transcribe_validates_input(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    with pytest.raises(stt.SttError) as e:
        _run(stt.transcribe(b"x", "text/plain", None))
    assert e.value.status == 415
    with pytest.raises(stt.SttError) as e:
        _run(stt.transcribe(b"x" * (stt.MAX_AUDIO_BYTES + 1), "audio/webm", None))
    assert e.value.status == 413


def test_transcribe_success_and_upstream_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    seen = {}

    def ok(request: httpx.Request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = request.content
        return httpx.Response(200, json={"text": " hola mundo "})

    async def go(handler):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            return await stt.transcribe(b"audio", "audio/webm;codecs=opus", "es", client=c)

    assert _run(go(ok)) == "hola mundo"
    assert seen["auth"] == "Bearer k"
    assert b'name="language"' in seen["body"]

    with pytest.raises(stt.SttError) as e:
        _run(go(lambda r: httpx.Response(500)))
    assert e.value.status == 502
