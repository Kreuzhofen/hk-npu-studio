from __future__ import annotations

import tkinter as tk
from pathlib import Path
from unittest.mock import patch

import widgets.phoenix.views.home_view as home_module
from app.i18n import set_language, tr
from dialogs.about_dialog import AboutDialog
from engine.brand_manager import BrandManager
from engine.theme_manager import ThemeManager
from widgets.phoenix.header import (
    HEADER_TEXT_TOP_OFFSET,
    HEADER_TITLE_GROUP_UP_OFFSET,
    PhoenixHeader,
)
from widgets.phoenix.controls.vector_icons import draw_vector_icon
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme
from widgets.phoenix.views.home_view import PhoenixHomeView
from widgets.text_context_menu import install_text_context_menu


def test_about_dialog_uses_the_canonical_window_icon():
    root = tk.Tk()
    root.withdraw()
    brand = BrandManager()
    root.brand = brand
    try:
        with patch.object(
            BrandManager, "apply_window_icon", wraps=BrandManager.apply_window_icon
        ) as apply_icon:
            dialog = AboutDialog(root, brand)
        apply_icon.assert_called_once_with(dialog)
        assert dialog._dialog_images
        assert dialog._dialog_images[0].width() == 128
        assert dialog._dialog_images[0].height() == 128
        visible_texts = [
            child.cget("text")
            for child in dialog.body.winfo_children()
            if isinstance(child, tk.Label) and "text" in child.keys()
        ]
        expected_branding = [
            BrandManager.HEADER_BRAND_NAME,
            "Version 2.0 RC2B",
            BrandManager.PLATFORM_DESCRIPTION,
            BrandManager.SLOGAN,
            BrandManager.PHOENIX_BOOST_CREDIT,
        ]
        branding_positions = [visible_texts.index(text) for text in expected_branding]
        assert branding_positions == sorted(branding_positions)
        assert "HK NPU Studio 1.0" not in visible_texts
        assert BrandManager.TRADEMARK_NOTICE in visible_texts
        dialog.destroy()
    finally:
        root.destroy()


def test_spanish_language_is_complete_and_selectable():
    try:
        set_language("es_ES")
        assert tr("settings_title") == "Ajustes"
        assert tr("home_delete_all") == "Eliminar todo"
        assert tr("generation_cancelled") == "Generación cancelada."
    finally:
        set_language("de_DE")


def test_single_and_all_generation_deletion_include_sidecars(tmp_path, monkeypatch):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    for image in (first, second):
        image.write_bytes(b"image")
        image.with_suffix(".json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(home_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(home_module.messagebox, "askyesno", lambda *a, **k: True)
    view = object.__new__(PhoenixHomeView)
    view.refresh = lambda **kwargs: None

    view._delete_generation(first)
    assert not first.exists()
    assert not first.with_suffix(".json").exists()
    assert second.exists()

    view._delete_all_generations()
    assert not second.exists()
    assert not second.with_suffix(".json").exists()


def test_delete_all_respects_confirmation(tmp_path, monkeypatch):
    image = tmp_path / "kept.png"
    image.write_bytes(b"image")
    monkeypatch.setattr(home_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(home_module.messagebox, "askyesno", lambda *a, **k: False)
    view = object.__new__(PhoenixHomeView)
    view.refresh = lambda **kwargs: None

    view._delete_all_generations()

    assert image.exists()


def test_global_text_context_menu_is_bound_to_all_text_inputs():
    class BindingRoot:
        def __init__(self):
            self.bindings = {}

        def bind_class(self, widget_class, event, callback, add=None):
            self.bindings[(widget_class, event)] = (callback, add)

    root = BindingRoot()
    install_text_context_menu(root)
    for widget_class in ("Entry", "TEntry", "Text", "Spinbox", "TSpinbox"):
        assert (widget_class, "<Button-3>") in root.bindings


def test_phoenix_header_branding_and_theme_contrast_at_dpi_scalings():
    set_language("en_US")
    root = tk.Tk()
    root.geometry("1000x300")
    try:
        for theme_name in ("dark", "light"):
            update_phoenix_theme(theme_name)
            for scaling in (1.0, 1.25, 1.5, 1.75):
                root.tk.call("tk", "scaling", scaling)
                header = PhoenixHeader(root)
                header.pack(fill="x")
                root.update()
                title_group = header.title_label.master
                logo_label = title_group.master.winfo_children()[0]
                release_group = header.winfo_children()[1]
                assert header.title_label.cget("text") == BrandManager.HEADER_BRAND_NAME
                assert header.view_label.cget("text") == (
                    f"{BrandManager.PLATFORM_DESCRIPTION} - Home"
                )
                assert header.title_label.cget("fg") == PHOENIX_THEME.accent
                assert title_group.pack_info()["pady"] == (
                    HEADER_TEXT_TOP_OFFSET - HEADER_TITLE_GROUP_UP_OFFSET,
                    HEADER_TITLE_GROUP_UP_OFFSET,
                )
                assert release_group.pack_info()["pady"] == (HEADER_TEXT_TOP_OFFSET, 0)
                assert title_group.winfo_y() == (
                    HEADER_TEXT_TOP_OFFSET - HEADER_TITLE_GROUP_UP_OFFSET
                )
                assert release_group.winfo_y() == HEADER_TEXT_TOP_OFFSET
                assert title_group.pack_info()["fill"] == "none"
                assert release_group.pack_info()["fill"] == "none"
                assert (
                    logo_label.cget("image") == str(header.logo_image)
                    and header.logo_image.width() == 73
                    and header.logo_image.height() == 73
                )
                assert logo_label.winfo_y() == 2
                assert title_group.winfo_height() >= title_group.winfo_reqheight()
                assert release_group.winfo_height() >= release_group.winfo_reqheight()
                assert header.winfo_reqheight() == max(
                    title_group.master.winfo_reqheight(), release_group.winfo_reqheight()
                )
                assert 40 < header.winfo_reqheight() <= 96
                header.destroy()
    finally:
        root.destroy()
        set_language("de_DE")
        ThemeManager.set_active_theme("dark")
        update_phoenix_theme("dark")


def test_settings_icon_uses_primary_contrast_in_light_theme():
    class RecordingCanvas:
        def __init__(self):
            self.colors = []

        def create_oval(self, *args, **kwargs):
            self.colors.append(kwargs.get("outline"))
            return len(self.colors)

        def create_line(self, *args, **kwargs):
            self.colors.append(kwargs.get("fill"))
            return len(self.colors)

    update_phoenix_theme("light")
    canvas = RecordingCanvas()

    draw_vector_icon(
        canvas,
        "settings",
        12,
        12,
        20,
        PHOENIX_THEME.text_secondary,
    )

    assert canvas.colors
    assert set(canvas.colors) == {PHOENIX_THEME.text_primary}
    update_phoenix_theme("dark")
