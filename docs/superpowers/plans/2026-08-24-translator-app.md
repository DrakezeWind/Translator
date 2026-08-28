# Translator App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small Tkinter desktop translator app with a reusable, GUI-free translation core.

**Architecture:** Three modules — `translator/engine.py` (pure translation logic via `deep-translator`), `translator/gui.py` (Tkinter window that calls the engine), `main.py` (entry point). The existing `translator.py` stub is replaced by `translator/engine.py`.

**Tech Stack:** Python, `uv` for dependency management, `deep-translator` package, Tkinter (stdlib), `pytest` for the engine test.

**Spec:** `docs/superpowers/specs/2026-08-24-translator-design.md`

## Global Constraints

- Single dependency: `deep-translator` (from spec's Tooling section).
- Dependency management via `uv` / `pyproject.toml` (from spec's Tooling section).
- Fixed dropdown list of ~10-15 common languages, not the full provider list (from spec's Scope section).
- `engine.py` has zero GUI dependency — it's the reuse seam for a future stream bot (from spec's Architecture section).

---

### Task 1: Project setup with uv

**Files:**
- Create: `pyproject.toml`
- Create: `translator/__init__.py` (empty)
- Delete: `translator.py` (old stub, superseded by `translator/engine.py` in Task 2)

**Interfaces:**
- Produces: a `translator` package directory that Task 2 and Task 3 add modules into; `deep-translator` and `pytest` installed as dependencies.

- [ ] **Step 1: Initialize uv project**

Run: `cd /home/zen-tech/projects/personal/Translator && uv init --no-readme --name translator`

This creates `pyproject.toml` and a starter `main.py` (we'll overwrite `main.py` in Task 3).

- [ ] **Step 2: Add dependencies**

Run: `uv add deep-translator` then `uv add --dev pytest`

- [ ] **Step 3: Create the package directory**

Create `translator/__init__.py` with empty content (just makes `translator/` an importable package).

- [ ] **Step 4: Remove the old stub**

Run: `rm translator.py` (the placeholder function is superseded by `translator/engine.py` in Task 2 — same name would otherwise collide with the new `translator/` package).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock translator/__init__.py
git rm translator.py
git commit -m "chore: set up uv project and translator package"
```

---

### Task 2: Translation engine

**Files:**
- Create: `translator/engine.py`
- Test: `tests/test_engine.py`

**Interfaces:**
- Consumes: `deep_translator.GoogleTranslator` (from the `deep-translator` package added in Task 1).
- Produces: `translate(text: str, source_lang: str, target_lang: str) -> str` — used by `translator/gui.py` in Task 3. Raises whatever `deep_translator` raises on failure (network error, bad language code) — caller is responsible for catching.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_engine.py`:

```python
from translator.engine import translate


def test_translate_returns_nonempty_string():
    result = translate("hello", "en", "es")
    assert isinstance(result, str)
    assert len(result) > 0


def test_translate_invalid_language_raises():
    import pytest
    with pytest.raises(Exception):
        translate("hello", "en", "not-a-real-language-code")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'translator.engine'`

- [ ] **Step 3: Write the engine implementation**

Create `translator/engine.py`:

```python
from deep_translator import GoogleTranslator


def translate(text: str, source_lang: str, target_lang: str) -> str:
    return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_engine.py -v`
Expected: PASS (requires internet access — `deep-translator` calls the live Google Translate web endpoint)

- [ ] **Step 5: Commit**

```bash
git add translator/engine.py tests/test_engine.py
git commit -m "feat: add translation engine"
```

---

### Task 3: Tkinter GUI and entry point

**Files:**
- Create: `translator/gui.py`
- Modify: `main.py` (overwrite uv's placeholder from Task 1)

**Interfaces:**
- Consumes: `translate(text, source_lang, target_lang) -> str` from `translator/engine.py` (Task 2).
- Produces: `translator.gui.run()` — launched by `main.py`.

- [ ] **Step 1: Write the GUI module**

Create `translator/gui.py`:

```python
import tkinter as tk
from tkinter import ttk

from translator.engine import translate

LANGUAGES = {
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


def run():
    root = tk.Tk()
    root.title("Translator")

    input_box = tk.Text(root, height=8, width=50)
    input_box.grid(row=0, column=0, columnspan=2, padx=8, pady=8)

    source_var = tk.StringVar(value="English")
    target_var = tk.StringVar(value="Spanish")

    ttk.Combobox(root, textvariable=source_var, values=list(LANGUAGES), state="readonly").grid(row=1, column=0, padx=8)
    ttk.Combobox(root, textvariable=target_var, values=list(LANGUAGES), state="readonly").grid(row=1, column=1, padx=8)

    output_box = tk.Text(root, height=8, width=50, state="disabled")
    output_box.grid(row=3, column=0, columnspan=2, padx=8, pady=8)

    def on_translate():
        text = input_box.get("1.0", "end").strip()
        try:
            result = translate(text, LANGUAGES[source_var.get()], LANGUAGES[target_var.get()])
        except Exception as e:
            result = f"Error: {e}"
        output_box.config(state="normal")
        output_box.delete("1.0", "end")
        output_box.insert("1.0", result)
        output_box.config(state="disabled")

    tk.Button(root, text="Translate", command=on_translate).grid(row=2, column=0, columnspan=2, pady=4)

    root.mainloop()
```

- [ ] **Step 2: Write the entry point**

Overwrite `main.py`:

```python
from translator.gui import run

if __name__ == "__main__":
    run()
```

- [ ] **Step 3: Manually verify the app launches and translates**

Run: `uv run main.py`

Expected: A window opens with input box, two language dropdowns (defaulting English → Spanish), a Translate button, and an output box. Typing "hello" and clicking Translate shows a Spanish translation in the output box. Close the window when done.

- [ ] **Step 4: Commit**

```bash
git add translator/gui.py main.py
git commit -m "feat: add Tkinter GUI and entry point"
```
