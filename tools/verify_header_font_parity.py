"""
Verify font equality between HK NPU STUDIO (left) and 2.1.0 (right).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import tkinter as tk
from widgets.phoenix.header import PhoenixHeader
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme
from engine.theme_manager import ThemeManager

root = tk.Tk()
root.withdraw()
try:
    for theme in ("dark", "light"):
        ThemeManager.set_active_theme(theme)
        update_phoenix_theme(theme)
        header = PhoenixHeader(root)
        header.pack()
        root.update()

        title_label = header.title_label
        rg = header.winfo_children()[1]
        top_label = [w for w in rg.winfo_children() if isinstance(w, tk.Label)][0]
        bottom_label = [w for w in rg.winfo_children() if isinstance(w, tk.Label)][1]

        # 1. Text assertions
        assert title_label.cget("text") == "HK NPU STUDIO"
        assert top_label.cget("text") == "2.1.0"
        assert bottom_label.cget("text") == "Phoenix Evolution"

        # 2. Font assertions: exactly same font, family, size, weight
        title_font = title_label.cget("font")
        version_font = top_label.cget("font")
        small_font = bottom_label.cget("font")

        print(f"{theme.upper()} THEME:")
        print(f"  title_label font:   {title_font} -> text: '{title_label.cget('text')}'")
        print(f"  top_label font:     {version_font} -> text: '{top_label.cget('text')}'")
        print(f"  bottom_label font:  {small_font} -> text: '{bottom_label.cget('text')}'")

        assert str(title_font) == str(version_font), f"Fonts must match: {title_font} vs {version_font}"
        assert top_label.cget("anchor") == "e"
        assert bottom_label.cget("anchor") == "e"
        assert top_label.cget("fg") == PHOENIX_THEME.accent
        assert bottom_label.cget("fg") == PHOENIX_THEME.text_muted
        assert top_label.cget("bg") == PHOENIX_THEME.header_bg
        assert bottom_label.cget("bg") == PHOENIX_THEME.header_bg

        header.destroy()
    print("\nALL FONT AND ALIGNMENT REQUIREMENTS VERIFIED SUCCESSFULLY (100%).")
finally:
    root.destroy()
    ThemeManager.set_active_theme("dark")
    update_phoenix_theme("dark")
