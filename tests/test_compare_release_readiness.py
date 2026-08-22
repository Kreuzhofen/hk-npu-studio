from __future__ import annotations

import json
import tkinter as tk
from unittest.mock import MagicMock

from PIL import Image
import pytest

from controllers.compare_workspace_controller import CompareWorkspaceController
from widgets.phoenix.compare.compare_toolbar import CompareToolbar
from widgets.phoenix.views.compare_view import PhoenixCompareView


def create_image(path, color):
    Image.new("RGB", (12, 8), color).save(path)


def test_compare_loads_shared_nested_sidecar_metadata(tmp_path):
    image = tmp_path / "output.png"
    create_image(image, "blue")
    image.with_suffix(".json").write_text(
        json.dumps(
            {
                "metadata": {
                    "prompt": "release prompt",
                    "seed": 42,
                    "sampler": "Euler",
                }
            }
        ),
        encoding="utf-8",
    )
    controller = CompareWorkspaceController()

    controller.load_output(image)

    metadata = controller.get_state().output_metadata
    assert metadata.prompt == "release prompt"
    assert metadata.seed == "42"
    assert metadata.sampler == "Euler"


def test_compare_reports_metadata_differences_deterministically(tmp_path):
    from app.i18n import set_language
    set_language("de_DE")
    original = tmp_path / "original.png"
    output = tmp_path / "output.png"
    create_image(original, "blue")
    create_image(output, "red")
    original.with_suffix(".json").write_text(
        json.dumps({"prompt": "same", "seed": 1, "sampler": "Euler"}),
        encoding="utf-8",
    )
    output.with_suffix(".json").write_text(
        json.dumps({"prompt": "same", "seed": 2, "sampler": "DDIM"}),
        encoding="utf-8",
    )
    controller = CompareWorkspaceController()
    controller.load_original(original)
    controller.load_output(output)

    differences = controller.compare_metadata()

    assert differences == {"file_size", "seed", "sampler"}
    assert "Unterschiede" in controller.get_state().status


def test_compare_includes_technical_image_differences(tmp_path):
    original = tmp_path / "original.png"
    output = tmp_path / "output.png"
    Image.new("RGB", (32, 32), "blue").save(original)
    Image.new("RGB", (64, 32), "blue").save(output)
    controller = CompareWorkspaceController()
    controller.load_original(original)
    controller.load_output(output)

    differences = controller.compare_metadata()

    assert "resolution" in differences
    assert "file_size" in differences


def test_failed_compare_load_preserves_existing_image(tmp_path):
    original = tmp_path / "original.png"
    create_image(original, "blue")
    controller = CompareWorkspaceController()
    controller.load_original(original)
    loaded = controller.get_original_image()

    try:
        controller.load_original(tmp_path / "missing.png")
    except FileNotFoundError:
        pass

    assert controller.get_original_image() is loaded
    assert controller.get_state().original_metadata.filename == "original.png"


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_compare_toolbar_wraps_action_groups_at_reduced_width(tk_root):
    callbacks = [MagicMock() for _ in range(9)]
    toolbar = CompareToolbar(tk_root, *callbacks)
    toolbar._layout_groups(700)
    assert int(toolbar.file_group.grid_info()["row"]) == 0
    assert int(toolbar.zoom_group.grid_info()["row"]) == 0
    assert int(toolbar.compare_group.grid_info()["row"]) == 1
    assert int(toolbar.compare_group.grid_info()["column"]) == 0
    toolbar._layout_groups(480)
    assert int(toolbar.zoom_group.grid_info()["row"]) == 1
    assert int(toolbar.compare_group.grid_info()["row"]) == 2
    assert toolbar._button_width("Synchronisieren") > toolbar.BUTTON_WIDTH_MEDIUM
    assert toolbar.on_sync is callbacks[6]
    toolbar.destroy()


def test_compare_canvas_preserves_image_height_after_toolbar_wrap(tk_root):
    tk_root.deiconify()
    tk_root.geometry("900x500")
    try:
        view = PhoenixCompareView(tk_root)
        view.toolbar._layout_groups(700)
        view.original_panel.set_image(Image.new("RGB", (1600, 1200), "blue"))
        view.result_panel.set_image(Image.new("RGB", (1600, 1200), "red"))
        tk_root.update_idletasks()
        assert view.compare_canvas.winfo_height() > 0
        assert view.original_panel.image_canvas.winfo_height() > 0
        assert view.result_panel.image_canvas.winfo_height() > 0
        assert view.original_panel.image_canvas.winfo_manager() == "grid"
        assert view.result_panel.image_canvas.winfo_manager() == "grid"
        canvas = view.original_panel.image_canvas
        canvas.set_zoom(2.0)
        canvas._start_pan(MagicMock(x=20, y=20))
        canvas._drag_pan(MagicMock(x=40, y=35))
        assert canvas.pan_offset_x or canvas.pan_offset_y
        assert 0.0 <= canvas.normalized_pan()[0] <= 1.0
        if view.controller.get_state().sync_label != "Synchron":
            view.controller.prepare_sync()
        view.result_panel.image_canvas.set_zoom(2.0)
        view._sync_pan("original", 1.0, 0.0)
        assert view.result_panel.image_canvas.normalized_pan()[0] == 1.0
        view.destroy()
    finally:
        tk_root.withdraw()
