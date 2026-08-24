import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from translator.engine import translate


def unicode_font(size=11, default="TkDefaultFont"):
    """Pick a font with broad script coverage, falling back if Noto Sans isn't installed."""
    family = "Noto Sans" if "Noto Sans" in tkfont.families() else default
    return (family, size)


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

    text_font = unicode_font()

    input_box = tk.Text(root, height=8, width=50, font=text_font)
    input_box.grid(row=0, column=0, columnspan=2, padx=8, pady=8)

    source_var = tk.StringVar(value="English")
    target_var = tk.StringVar(value="Spanish")

    ttk.Combobox(root, textvariable=source_var, values=list(LANGUAGES), state="readonly").grid(row=1, column=0, padx=8)
    ttk.Combobox(root, textvariable=target_var, values=list(LANGUAGES), state="readonly").grid(row=1, column=1, padx=8)

    output_box = tk.Text(root, height=8, width=50, state="disabled", font=text_font)
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
        output_box.update_idletasks()

    tk.Button(root, text="Translate", command=on_translate).grid(row=2, column=0, columnspan=2, pady=4)

    root.mainloop()
