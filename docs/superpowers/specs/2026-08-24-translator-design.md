# Translator — Design Spec

## Purpose

A small Python desktop translator app. Primary goal right now is learning
Python; secondary goal is a reusable translation core that can later be
lifted into an Anakonis stream chat-translation bot without rewriting it.

## Scope

- Desktop GUI (Tkinter) with text input, source/target language dropdowns,
  translate button, and text output.
- Translation via the `deep-translator` package (free web endpoints,
  no API key, needs internet).
- Fixed dropdown list of ~10-15 common languages (not the full provider list).
- Single-user, single-machine, synchronous translation calls.

Out of scope (not building now): offline/local models, batch/file
translation, streaming/chat integration, saved translation history.

## Architecture

Three modules, split so the translation core has zero GUI dependency:

- `translator/engine.py` — `translate(text: str, source_lang: str, target_lang: str) -> str`.
  Thin wrapper around `deep-translator`. This is the piece that gets reused
  in a future stream bot.
- `translator/gui.py` — Tkinter window. Input textbox, two language
  dropdowns (source/target), a Translate button, output textbox. Calls
  `engine.translate()` on button press.
- `main.py` — entry point, constructs and runs the GUI.

## Data Flow

User types text → selects source/target language → clicks Translate →
`gui.py` calls `engine.translate(text, source, target)` synchronously →
result (or error message) is written into the output textbox.

## Error Handling

`engine.translate()` lets `deep-translator` exceptions (network failure,
unsupported language pair) propagate. `gui.py` catches them at the call
site and displays the error text in the output box instead of crashing
the app.

## Testing

`tests/test_engine.py` — a couple of `assert`-based checks against
`translate()` (e.g. a known short phrase translates non-empty, and an
invalid language pair raises). No framework, no fixtures.

## Tooling

- Python dependency management via `uv` (`pyproject.toml`).
- Single dependency: `deep-translator`.

## Future Extension (not built now)

`engine.py`'s `translate()` function is the seam for reuse — a future
stream-chat bot would import it directly rather than going through the
GUI. No extra abstraction is being added now to support that; the module
boundary alone is sufficient.

## Addendum — 2026-09-11

- GUI rebuilt: Tkinter (`translator/gui.py`) replaced by a NiceGUI local web
  app (`translator/web.py`), styled to match an approved dark-mode mockup.
  `translator/engine.py`'s public interface is unchanged.
- Local translation history is now in scope (reversing the original "out of
  scope" call above): recent translations are persisted to a local JSON
  file (`translator/history.py`) and shown inline on the same page. Still
  single-user, single-machine — no sync, no database.
- Nav simplified: dropped the "Translator / History / About" text links
  from the header (history is already visible inline, nothing else to
  navigate to) — kept the settings icon as decorative.
- Voice added, both directions, via the browser's native Web Speech API
  (`SpeechRecognition` for mic input, `SpeechSynthesis` for speaker
  output) — zero new Python dependencies, bridged into NiceGUI through
  its `ui.on()`/`emitEvent()` global-event mechanism. A `voice_error`
  event covers both "browser doesn't support it" (mic support is
  Chromium-only in practice) and runtime errors, surfaced via
  `ui.notify()` instead of a silently dead button.
- Real pixel-art logo (`translator/static/logo.png`) replaces the
  placeholder header dot; also set as the browser favicon.
- Deployed to Fly.io: `Dockerfile` (uv's official Python base image),
  `fly.toml` (persistent volume at `/data` so history survives restarts),
  `.dockerignore`. `translator/web.py`'s `run()` and `translator/history.py`
  now read `PORT`/`ENV`/`HISTORY_FILE_PATH` from the environment so the
  same code runs locally and in the container (dev auto-reload and
  auto-opening a browser are both disabled when `ENV=production`).
  Live at `translator.drakeze.com` (Cloudflare DNS, `A`/`AAAA` records,
  DNS-only/un-proxied per Fly's TLS requirements).
- Fixed a pre-existing bug found while containerizing: `.python-version`
  held this machine's literal absolute interpreter path
  (`/usr/bin/python3.10`) instead of a version string — broke `uv sync
  --frozen` inside the container. Corrected to `3.10`.
- Added to the Drakeze Portfolio's `/projects` page as a project card
  (`Portfolio/components/banners/TranslatorBanner.jsx`, pink accent
  `#D6336C`), linking to the live site and the now-pushed GitHub repo.
