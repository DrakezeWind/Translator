import tkinter as tk

import pytest

from translator.gui import unicode_font


def _needs_display():
    try:
        root = tk.Tk()
        root.destroy()
    except tk.TclError:
        pytest.skip("no display available")


def test_unicode_font_falls_back_when_family_missing():
    _needs_display()
    root = tk.Tk()
    try:
        family, size = unicode_font(size=12, default="TkDefaultFont")
        assert size == 12
        assert family in ("Noto Sans", "TkDefaultFont")
    finally:
        root.destroy()
