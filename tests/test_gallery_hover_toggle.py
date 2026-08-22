import tkinter as tk
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.gallery.toolbar import GalleryToolbar
from widgets.phoenix.gallery.thumbnail_widget import ThumbnailWidget
from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.views.gallery_view import PhoenixGalleryView


@pytest.fixture(scope="module")
def tk_root() -> tk.Tk:
    root = tk.Tk()
    yield root
    root.destroy()


def test_hover_toggle_uses_gallery_action_style_and_reflows(tk_root: tk.Tk) -> None:
    toolbar = GalleryToolbar(
        tk_root, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        on_hover_preview_change=MagicMock(), hover_preview_enabled=True,
    )
    try:
        changed = MagicMock()
        toolbar.on_hover_preview_change = changed
        toolbar.pack(fill="x")
        tk_root.update_idletasks()
        assert isinstance(toolbar.hover_preview_btn, PhoenixButton)
        assert toolbar.hover_preview_btn.button_type == "neutral"
        assert toolbar.hover_preview_btn.icon_name == "image"
        assert toolbar.hover_preview_btn.icon_color == PHOENIX_THEME.danger
        assert int(toolbar.hover_group.grid_info()["row"]) == 0
        assert int(toolbar.hover_group.grid_info()["column"]) == 1
        toolbar._toggle_hover_preview()
        assert toolbar.hover_preview_btn.button_type == "neutral"
        assert toolbar.hover_preview_btn.icon_color == PHOENIX_THEME.danger
        changed.assert_called_once_with(False)
    finally:
        toolbar.destroy()


def _resize_toolbar(root: tk.Tk, toolbar: GalleryToolbar, width: int) -> None:
    root.geometry(f"{width}x900")
    root.update()
    toolbar._layout_toolbar_groups(MagicMock(width=toolbar.winfo_width()))
    root.update_idletasks()


def _assert_groups_fit(toolbar: GalleryToolbar) -> None:
    groups = toolbar.toolbar_groups
    assert all(group.winfo_ismapped() for group in groups)
    assert all(group.winfo_x() + group.winfo_width() <= toolbar.winfo_width() for group in groups)
    assert max(group.winfo_y() + group.winfo_height() for group in groups) <= toolbar.winfo_height()
    for index, first in enumerate(groups):
        for second in groups[index + 1:]:
            vertical_overlap = first.winfo_y() < second.winfo_y() + second.winfo_height() and second.winfo_y() < first.winfo_y() + first.winfo_height()
            if vertical_overlap:
                assert first.winfo_x() + first.winfo_width() <= second.winfo_x() or second.winfo_x() + second.winfo_width() <= first.winfo_x()


def test_gallery_toolbar_reflows_all_groups_without_losing_state(tk_root: tk.Tk) -> None:
    toolbar = GalleryToolbar(
        tk_root, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        on_hover_preview_change=MagicMock(), hover_preview_enabled=True,
    )
    try:
        toolbar.pack(fill="x")
        group_ids = tuple(id(group) for group in toolbar.toolbar_groups)
        toolbar.search_value.set("portrait")
        toolbar.sort_value.set(toolbar.SORT_OPTIONS[-1])
        toolbar.size_value.set(toolbar.SIZE_OPTIONS[-1])
        toolbar.filter_value.set(toolbar.FILTER_OPTIONS[0])

        _resize_toolbar(tk_root, toolbar, 1600)
        assert [int(group.grid_info()["row"]) for group in toolbar.toolbar_groups] == [0] * 7
        assert [int(group.grid_info()["column"]) for group in toolbar.toolbar_groups] == list(range(7))
        _assert_groups_fit(toolbar)

        _resize_toolbar(tk_root, toolbar, 800)
        assert int(toolbar.search_group.grid_info()["row"]) > 0
        assert toolbar.search_entry.winfo_width() > 0
        assert toolbar.filter_dropdown.text == "Alle"
        _assert_groups_fit(toolbar)

        _resize_toolbar(tk_root, toolbar, 400)
        assert len({int(group.grid_info()["row"]) for group in toolbar.toolbar_groups}) > 2
        assert toolbar.search_entry.winfo_width() > 0
        assert toolbar.filter_dropdown.text == "Alle"
        _assert_groups_fit(toolbar)

        _resize_toolbar(tk_root, toolbar, 1600)
        assert [int(group.grid_info()["row"]) for group in toolbar.toolbar_groups] == [0] * 7
        assert tuple(id(group) for group in toolbar.toolbar_groups) == group_ids
        assert toolbar.hover_preview_enabled is True
        assert toolbar.search_value.get() == "portrait"
        assert toolbar.sort_value.get() == toolbar.SORT_OPTIONS[-1]
        assert toolbar.size_value.get() == toolbar.SIZE_OPTIONS[-1]
        assert toolbar.filter_value.get() == "Alle"
    finally:
        toolbar.destroy()


def test_hover_toggle_translations_are_complete() -> None:
    expected = {
        "locales/de_DE.json": ("Hover-Vorschau: Ein", "Hover-Vorschau: Aus"),
        "locales/en_US.json": ("Hover preview: On", "Hover preview: Off"),
        "locales/es_ES.json": ("Vista previa al pasar: Activada", "Vista previa al pasar: Desactivada"),
    }
    for relative_path, labels in expected.items():
        translations = json.loads(Path(relative_path).read_text(encoding="utf-8"))
        assert (translations["gallery_hover_preview_on"], translations["gallery_hover_preview_off"]) == labels


def test_preference_default_true_and_invalid_values_are_safe() -> None:
    with patch("widgets.phoenix.views.gallery_view.SettingsManager.load_settings", return_value={}):
        assert PhoenixGalleryView._load_hover_preview_enabled() is True
    with patch("widgets.phoenix.views.gallery_view.SettingsManager.load_settings", return_value={"gallery_hover_preview_enabled": False}):
        assert PhoenixGalleryView._load_hover_preview_enabled() is False
    with patch("widgets.phoenix.views.gallery_view.SettingsManager.load_settings", return_value={"gallery_hover_preview_enabled": "false"}):
        assert PhoenixGalleryView._load_hover_preview_enabled() is True


def test_preference_toggle_preserves_other_settings_and_closes_previews() -> None:
    view = MagicMock()
    view.thumbnail_area = MagicMock()
    with patch("widgets.phoenix.views.gallery_view.SettingsManager.load_settings", return_value={"language": "de_DE"}) as load, patch("widgets.phoenix.views.gallery_view.SettingsManager.save_settings", return_value=True) as save:
        PhoenixGalleryView._on_hover_preview_change(view, False)
    load.assert_called_once()
    save.assert_called_once_with({"language": "de_DE", "gallery_hover_preview_enabled": False})
    view.thumbnail_area.set_hover_preview_enabled.assert_called_once_with(False)


def test_hover_preview_is_suppressed_and_open_preview_closes_when_disabled() -> None:
    widget = ThumbnailWidget.__new__(ThumbnailWidget)
    widget.selected = True
    preview = MagicMock()
    widget._hover_preview = preview
    widget.hover_preview_enabled = lambda: False
    widget.thumbnail_image = object()
    widget.image = MagicMock(path=Path("C:/does-not-matter.png"))
    ThumbnailWidget._on_enter(widget, MagicMock())
    preview.destroy.assert_called_once()
    assert widget._hover_preview is None
    ThumbnailWidget.close_hover_preview(widget)
