import json
import os
from pathlib import Path

# _run alias: module-level def run() below would shadow nicegui's run module otherwise
from fastapi.responses import JSONResponse
from nicegui import Client, app, run as _run, ui
from starlette.requests import Request

from translator import history, stt
from translator.engine import translate

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.add_static_files("/static", STATIC_DIR)

LANGUAGES = {
    "Auto-detect": "auto",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese (Simplified)": "zh-CN",
    "Arabic": "ar",
    "Hindi": "hi",
}
TARGET_LANGUAGES = {name: code for name, code in LANGUAGES.items() if name != "Auto-detect"}
NAMES_BY_CODE = {code: name for name, code in LANGUAGES.items()}

# BCP-47 locales for the Web Speech API (SpeechRecognition/SpeechSynthesis).
# "auto" has no fixed locale, so mic input falls back to the browser's default.
LOCALES = {
    "auto": None,
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
    "pt": "pt-PT",
    "ru": "ru-RU",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "zh-CN": "zh-CN",
    "ar": "ar-SA",
    "hi": "hi-IN",
}

_rate_limiter = stt.RateLimiter()


@app.post("/api/transcribe")
async def api_transcribe(request: Request, lang: str = "auto"):
    """Fallback speech-to-text: raw audio body in, {"text": ...} out."""
    if lang not in LANGUAGES.values():
        return JSONResponse({"error": "Unsupported language"}, status_code=400)
    # Fly terminates TLS in front of the app and forwards the real client IP here.
    ip = request.headers.get("fly-client-ip") or (request.client.host if request.client else "unknown")
    if not _rate_limiter.allow(ip):
        return JSONResponse({"error": "Too many requests"}, status_code=429)
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > stt.MAX_AUDIO_BYTES:
        return JSONResponse({"error": "Audio too large"}, status_code=413)
    try:
        text = await stt.transcribe(
            await request.body(),
            request.headers.get("content-type", ""),
            stt.whisper_language(lang),
        )
    except stt.SttError as e:
        return JSONResponse({"error": e.message}, status_code=e.status)
    return {"text": text}


CARD = "rounded-2xl border border-neutral-800 bg-neutral-900 shadow-xl p-6 w-full max-w-4xl"
SUBCARD = "rounded-xl border border-neutral-800 bg-neutral-900 p-4 flex-1"
MUTED = "text-neutral-500 text-sm"


@ui.page("/", favicon=str(STATIC_DIR / "logo.png"))
async def index(client: Client):
    ui.dark_mode().enable()
    ui.query("body").classes("bg-black")

    with ui.column().classes("w-full items-center bg-black min-h-screen gap-8 py-10"):
        with ui.row().classes("w-full max-w-4xl items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                ui.image("/static/logo.png").classes("w-8 h-8 rounded-lg")
                ui.label("lingo.").classes("font-serif text-xl text-white")
            ui.icon("settings").classes("text-neutral-400")

        with ui.column().classes("w-full max-w-4xl items-start gap-3"):
            ui.label("✨ Translation, without the noise").classes(
                "rounded-full border border-neutral-700 px-4 py-1 text-sm text-neutral-300"
            )
            ui.label("Say it in any language.").classes("font-serif text-5xl text-white")
            ui.label("A calm, clear space to find the right words. Translate naturally, compare "
                     "meaning, and keep the conversation moving.").classes("text-neutral-400")

        with ui.card().classes(CARD):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.element("div").classes("w-2 h-2 rounded-full bg-green-400")
                    ui.label("New translation").classes("text-white")
                    ui.label("/ ready when you are").classes(MUTED)
                ui.space()
                ui.button("↺ Clear all", on_click=lambda: do_clear()).props("flat dense").classes(
                    "text-neutral-400"
                )

            with ui.row().classes("w-full gap-4 items-stretch"):
                with ui.column().classes("flex-1 gap-2"):
                    source_select = ui.select(list(LANGUAGES), value="Auto-detect").props("borderless dense").classes(
                        "text-white"
                    )
                    input_box = ui.textarea(placeholder="Type to translate…").props("borderless").classes(
                        "text-lg text-white w-full"
                    )
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes("gap-2 text-neutral-500"):
                            ui.icon("attach_file")
                            mic_btn = ui.button(icon="mic", on_click=lambda: start_mic()).props(
                                "round flat dense"
                            ).classes("text-neutral-500")
                            mic_btn.disable()
                            status_label = ui.label("").classes("text-sm text-red-400")
                        counter_label = ui.label("0 / 5000").classes(MUTED)

                with ui.column().classes("justify-center"):
                    ui.button(icon="swap_vert", on_click=lambda: do_swap()).props("round flat").classes(
                        "text-neutral-400"
                    )

                with ui.column().classes("flex-1 gap-2"):
                    with ui.row().classes("w-full items-center justify-between"):
                        target_select = ui.select(list(TARGET_LANGUAGES), value="Spanish").props(
                            "borderless dense"
                        ).classes("text-white")
                        with ui.row().classes("gap-1"):
                            ui.button(icon="volume_up", on_click=lambda: speak_output()).props(
                                "round flat"
                            ).classes("text-neutral-400")
                            ui.button(
                                icon="content_copy", on_click=lambda: ui.clipboard.write(output_box.value)
                            ).props("round flat").classes("text-neutral-400")
                    output_box = ui.textarea().props("borderless readonly").classes("text-lg text-neutral-300 w-full")
                    ui.label("Natural translation").classes(MUTED)

            with ui.row().classes("w-full items-center justify-between pt-2"):
                ui.label("✨ Powered by language intelligence").classes(MUTED)
                translate_btn = ui.button("▶ Translate", on_click=lambda: do_translate()).classes(
                    "rounded-full bg-white text-black px-6 py-2"
                )

        def update_counter():
            counter_label.text = f"{len(input_box.value or '')} / 5000"

        def on_input_change(e):
            counter_label.text = f"{len(e.value or '')} / 5000"

        input_box.on_value_change(on_input_change)

        def do_clear():
            input_box.value = ""
            output_box.value = ""
            counter_label.text = "0 / 5000"

        def do_swap():
            if source_select.value == "Auto-detect":
                return
            source_select.value, target_select.value = target_select.value, source_select.value
            input_box.value, output_box.value = output_box.value, input_box.value

        # io_bound offloads the blocking Google Translate HTTP call to a thread pool
        # so the NiceGUI event loop stays responsive during the request.
        async def do_translate():
            text = (input_box.value or "").strip()
            if not text:
                return
            source_code = LANGUAGES[source_select.value]
            target_code = TARGET_LANGUAGES[target_select.value]
            translate_btn.props("loading")
            try:
                result = await _run.io_bound(translate, text, source_code, target_code)
            except Exception as e:
                result = f"Error: {e}"
            finally:
                translate_btn.props(remove="loading")
            output_box.value = result
            history.append_entry(source_code, target_code, text, result)
            recent_row.refresh()

        def on_mic_start(_):
            mic_btn.classes(remove="text-neutral-500", add="text-red-500")
            mic_btn.props("icon=stop")
            status_label.text = "Listening… click the stop button when done"

        def on_mic_end(_):
            mic_btn.classes(remove="text-red-500", add="text-neutral-500")
            mic_btn.props("icon=mic")
            if status_label.text.startswith("Listening"):
                status_label.text = ""

        def on_mic_transcribing(_):
            status_label.text = "Transcribing…"

        def on_mic_result(e):
            status_label.text = ""
            input_box.value = e.args
            update_counter()

        def on_voice_error(e):
            status_label.text = ""
            mic_btn.classes(remove="text-red-500", add="text-neutral-500")
            mic_btn.props("icon=mic")
            ui.notify(e.args, type="warning")

        ui.on("mic_result", on_mic_result)
        ui.on("mic_start", on_mic_start)
        ui.on("mic_end", on_mic_end)
        ui.on("mic_transcribing", on_mic_transcribing)
        ui.on("voice_error", on_voice_error)

        def start_mic():
            locale = LOCALES.get(LANGUAGES[source_select.value])
            lang_code = LANGUAGES[source_select.value]
            ui.run_javascript(f"""
                // Second click while the fallback recorder is running stops it and uploads.
                if (window._lingoRecorder) {{ window._lingoRecorder.stop(); return; }}
                if (window._lingoRecognizing || window._lingoStarting) return;

                const ERR = {{
                    network: 'Cannot reach speech service — check your connection',
                    'not-allowed': 'Microphone permission denied',
                    'service-not-allowed': 'Speech service blocked by browser',
                    'audio-capture': 'No microphone found',
                    'no-speech': 'No speech detected',
                    aborted: 'Microphone stopped',
                }};
                const lang = {json.dumps(locale)};

                // Fallback: record audio and have the server transcribe it, for browsers where
                // the built-in speech service is unavailable or unreachable.
                async function recordFallback() {{
                    if (!navigator.mediaDevices || !window.MediaRecorder) {{
                        emitEvent('voice_error', 'Voice input not supported in this browser');
                        return;
                    }}
                    // The speech service already failed once this page load; skip straight here next time.
                    window._lingoFallback = true;
                    window._lingoStarting = true;
                    let stream;
                    try {{
                        stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    }} catch (err) {{
                        window._lingoStarting = false;
                        emitEvent('voice_error', err.name === 'NotFoundError' ? ERR['audio-capture'] : ERR['not-allowed']);
                        return;
                    }}
                    const recorder = new MediaRecorder(stream);
                    const chunks = [];
                    window._lingoRecorder = recorder;
                    window._lingoStarting = false;
                    recorder.ondataavailable = (e) => {{ if (e.data.size) chunks.push(e.data); }};
                    recorder.onstop = async () => {{
                        window._lingoRecorder = null;
                        clearTimeout(cap);
                        stream.getTracks().forEach((t) => t.stop());
                        emitEvent('mic_end', null);
                        const blob = new Blob(chunks, {{ type: recorder.mimeType || 'audio/webm' }});
                        if (!blob.size) {{ emitEvent('voice_error', ERR['no-speech']); return; }}
                        emitEvent('mic_transcribing', null);
                        try {{
                            const res = await fetch('/api/transcribe?lang=' + encodeURIComponent({json.dumps(lang_code)}), {{
                                method: 'POST',
                                headers: {{ 'Content-Type': blob.type }},
                                body: blob,
                            }});
                            const data = await res.json().catch(() => ({{}}));
                            if (!res.ok) {{ emitEvent('voice_error', data.error || 'Transcription failed'); return; }}
                            if (data.text) emitEvent('mic_result', data.text);
                            else emitEvent('voice_error', ERR['no-speech']);
                        }} catch (err) {{
                            emitEvent('voice_error', 'Could not reach the server');
                        }}
                    }};
                    const cap = setTimeout(() => recorder.state !== 'inactive' && recorder.stop(), 15000);
                    recorder.start();
                    emitEvent('mic_start', null);
                }}

                // Chrome blocks mic access on plain HTTP origins that are not localhost.
                if (!window.isSecureContext) {{
                    emitEvent('voice_error', 'Microphone requires HTTPS or localhost');
                    return;
                }}
                const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!Recognition || window._lingoFallback) {{ recordFallback(); return; }}

                const recognition = new Recognition();
                if (lang) recognition.lang = lang;
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.onstart = () => {{ window._lingoRecognizing = true; emitEvent('mic_start', null); }};
                recognition.onend = () => {{
                    window._lingoRecognizing = false;
                    // onend follows onerror; don't clobber the fallback recorder's UI state.
                    if (!window._lingoRecorder && !window._lingoStarting) emitEvent('mic_end', null);
                }};
                recognition.onresult = (event) => emitEvent('mic_result', event.results[0][0].transcript);
                recognition.onerror = (event) => {{
                    window._lingoRecognizing = false;
                    if (event.error === 'network' || event.error === 'service-not-allowed') {{
                        recordFallback();
                        return;
                    }}
                    emitEvent('voice_error', ERR[event.error] || ('Voice error: ' + event.error));
                }};
                recognition.start();
            """)

        def speak_output():
            text = (output_box.value or "").strip()
            if not text:
                return
            locale = LOCALES.get(TARGET_LANGUAGES[target_select.value]) or "en-US"
            ui.run_javascript(f"""
                if (!('speechSynthesis' in window)) {{
                    emitEvent('voice_error', 'speech synthesis not supported in this browser');
                }} else {{
                    const utterance = new SpeechSynthesisUtterance({json.dumps(text)});
                    utterance.lang = {json.dumps(locale)};
                    speechSynthesis.speak(utterance);
                }}
            """)

        with ui.column().classes("w-full max-w-4xl gap-3"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2 text-neutral-400"):
                    ui.icon("history")
                    ui.label("Recent translations")
                ui.label("Your translations stay private on this device").classes(MUTED)

            @ui.refreshable
            def recent_row():
                with ui.row().classes("w-full gap-4"):
                    for entry in history.load_recent(limit=2):
                        with ui.card().classes(SUBCARD):
                            source_name = NAMES_BY_CODE.get(entry["source_lang"], entry["source_lang"])
                            target_name = NAMES_BY_CODE.get(entry["target_lang"], entry["target_lang"])
                            ui.label(f"{source_name} → {target_name}").classes("text-white text-sm")
                            ui.label(entry["timestamp"]).classes("text-xs text-neutral-500")
                            ui.label(entry["source_text"]).classes("text-neutral-200")
                            ui.label(entry["translated_text"]).classes("text-neutral-500")
                    with ui.card().classes(SUBCARD + " border-dashed"):
                        ui.label(
                            "Tip: Use the microphone to translate conversations in real time."
                        ).classes("text-neutral-400 text-sm")

            recent_row()

        with ui.row().classes("w-full max-w-4xl items-center justify-between text-neutral-500 text-sm"):
            ui.label("lingo.")
            ui.label("Made for words that travel.")

    # Enable mic only after the Socket.IO handshake completes.
    # Without this guard, emitEvent() and ui.run_javascript() silently drop on cold
    # start (machine was sleeping, WS not ready when user clicks mic immediately).
    await client.connected()
    mic_btn.enable()

    # Keep mic disabled whenever this client's connection is lost (e.g. Cloudflare idle
    # timeout) and re-enable on reconnect so clicks never silently fail. Per-client, so
    # handlers don't pile up on the global app or touch another visitor's button.
    client.on_disconnect(lambda: mic_btn.disable())
    client.on_connect(lambda: mic_btn.enable())


def run():
    is_production = os.environ.get("ENV") == "production"
    ui.run(
        title="lingo.",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=not is_production,
        show=not is_production,
    )
