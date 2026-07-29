from __future__ import annotations

from PIL import Image

from controllers.compare_workspace_controller import CompareWorkspaceController
from controllers.gallery_image_loader import ImageLoader
from engine.asset_files import atomic_write_json
from engine.asset_index import AssetIndexRepository, AssetScanner
from engine.plugin_manager import PluginManager
from engine.release_config import RELEASE
from engine.startup_diagnostics import run_startup_diagnostics


def test_rc1_startup_release_and_plugin_gate():
    startup = run_startup_diagnostics()
    plugins = PluginManager().scan()

    assert startup.safe_to_start is True
    assert RELEASE.package_version == "2.0.0-rc.1"
    assert RELEASE.architecture == "arm64"
    assert any(plugin.id == "realesrgan" for plugin in plugins)


def test_rc1_output_gallery_index_and_compare_flow(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    image_path = output / "generated.png"
    Image.new("RGB", (32, 24), "navy").save(image_path)
    atomic_write_json(
        image_path.with_suffix(".json"),
        {
            "prompt": "RC1 end-to-end",
            "model_id": "stable_diffusion_v1_5_qnn",
            "seed": 123,
            "sampler": "Euler",
        },
    )

    repository = AssetIndexRepository(tmp_path / "data" / "assets.sqlite3")
    scan = AssetScanner(repository).scan(output)
    gallery_image = ImageLoader().load_folder(output)[0]
    compare = CompareWorkspaceController()
    compare.load_output(gallery_image.path)

    indexed = repository.list_assets()[0]
    compared = compare.get_state().output_metadata
    assert scan.inserted == 1
    assert gallery_image.prompt == indexed.prompt == compared.prompt
    assert gallery_image.seed == indexed.seed == int(compared.seed)
    assert compared.resolution == "32 x 24"
