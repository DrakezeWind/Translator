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
