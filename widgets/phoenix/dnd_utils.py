"""
HK NPU STUDIO - Universal Drag & Drop Utilities
Provides safe path parsing for Windows TkDND events, registration helpers, and validation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable
import tkinter as tk

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}


def parse_dnd_paths(event_data: object) -> list[str]:
    """
    Safely parse dropped file paths from TkDND event data on Windows.
    Handles space-separated lists, curly-brace quoted items, double-quoted items,
    and preserves backslashes.
    """
    if not event_data:
        return []

    if isinstance(event_data, (list, tuple)):
        result = []
        for item in event_data:
            cleaned = str(item).strip('{}""\'\'').strip()
            if cleaned:
                result.append(cleaned)
        return result

    text = str(event_data).strip()
    if not text:
        return []

    pattern = r'\{([^}]+)\}|"([^"]+)"|\'([^\']+)\'|(\S+)'
    matches = re.findall(pattern, text)
    paths = []
    for m in matches:
        raw = m[0] or m[1] or m[2] or m[3]
        cleaned = raw.strip('{}""\'\'').strip()
        if cleaned:
            paths.append(cleaned)
    return paths


def register_dnd_target(
    widget: tk.Widget | None,
    dnd_files: object,
    on_drop_callback: Callable[[object], None],
    recursive: bool = False,
    exclude: set[tk.Widget] | None = None,
) -> None:
    """Register widget (and optionally its children) as TkDND drop targets."""
    if widget is None:
        return

    exclude_set = exclude or set()
    if widget in exclude_set:
        return

    try:
        widget.drop_target_register(dnd_files)
        widget.dnd_bind("<<Drop>>", on_drop_callback)
    except Exception:
        pass

    if recursive and hasattr(widget, "winfo_children"):
        try:
            for child in widget.winfo_children():
                if child not in exclude_set:
                    register_dnd_target(child, dnd_files, on_drop_callback, recursive=True, exclude=exclude_set)
        except Exception:
            pass
