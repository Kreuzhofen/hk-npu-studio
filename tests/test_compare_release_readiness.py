from __future__ import annotations

import json

from PIL import Image

from controllers.compare_workspace_controller import CompareWorkspaceController


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
