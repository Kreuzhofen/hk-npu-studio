from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from controllers.model_repository import ModelRepository
from engine.model_install_service import ModelInstallService
from engine.package_catalog_service import PackageCatalogService


ROOT = Path(__file__).resolve().parents[1]
MODEL_DEFINITION = ROOT / "resources" / "models" / "photo_restore.json"
PACKAGE_CATALOG = ROOT / "resources" / "package_catalog.json"
COMPONENT_PATHS = (
    "models/fidesr_empty_prompt_embeds.bin",
    "models/fidesr_epsilon_seed231.bin",
    "context/fidesr_vae_encoder/fidesr_vae_encoder.serialized.bin.bin",
    "context/fidesr_unet/fidesr_unet_merged.serialized.bin.bin",
    "context/fidesr_lrrb/fidesr_lrrb.serialized.bin.bin",
    "context/fidesr_vae_decoder/fidesr_vae_decoder.serialized.bin.bin",
)


def package_manifest() -> dict:
    return {
        "package_id": "photo_restore",
        "package_version": "1.0.0",
        "architecture": "arm64",
        "runtime": "Qualcomm QNN / Hexagon HTP (V73)",
        "app_min_version": "2.0.0-rc.3",
        "capabilities": {"img2img": True, "qnn_runtime": True},
        "components": {
            f"component_{index}": {"path": path, "runtime": "QNN"}
            for index, path in enumerate(COMPONENT_PATHS, start=1)
        },
    }


class RepositoryStub:
    def __init__(self) -> None:
        self.model = {
            "id": "photo_restore",
            "installed": False,
            "downloaded": False,
            "path": "",
            "status": "Not Installed",
        }

    def get_model(self, model_id: str):
        return self.model if model_id == "photo_restore" else None

    def update_model(self, model_id: str, **updates) -> bool:
        if model_id != "photo_restore":
            return False
        self.model.update(updates)
        return True


class PhotoRestorePackageDefinitionTests(unittest.TestCase):
    def test_definition_loads_through_model_repository(self) -> None:
        repository = ModelRepository(models_dir=str(ROOT / "resources" / "models"))
        model = repository.get_model("photo_restore")

        self.assertIsNotNone(model)
        self.assertEqual(model["id"], "photo_restore")
        self.assertEqual(model["source_type"], "local_only")
        self.assertEqual(model["source_url"], "")
        self.assertEqual(model["package_format"], "smp_or_zip")
        self.assertEqual(model["required_files"], list(COMPONENT_PATHS))
        self.assertTrue(repository.registry.get_report("photo_restore").valid)
        self.assertEqual(repository.registry.get_invalid_reports(), {})

    def test_catalog_keeps_existing_entries_and_has_unique_ids(self) -> None:
        data = json.loads(PACKAGE_CATALOG.read_text(encoding="utf-8"))
        model_ids = [entry["model_id"] for entry in data["packages"]]
        expected_existing = {
            "cogvideox",
            "controlnet_canny_qnn",
            "flux_dev",
            "ltx_video",
            "sd35_large",
            "sdxl_base",
            "sdxl_refiner",
            "stable_diffusion_v1_5_qai",
            "stable_diffusion_v1_5_qnn",
            "stable_diffusion_v2_1_qai",
            "stable_diffusion_v2_1_qnn",
            "stable_diffusion_v3_5_qai",
            "wan22",
        }

        self.assertEqual(len(model_ids), len(set(model_ids)))
        self.assertTrue(expected_existing.issubset(model_ids))
        self.assertEqual(model_ids.count("photo_restore"), 1)

    def test_catalog_entry_is_valid_and_unavailable_for_download(self) -> None:
        catalog = PackageCatalogService(PACKAGE_CATALOG)
        entry = catalog.get_entry("photo_restore")

        self.assertIsNotNone(entry)
        self.assertEqual(entry.model_id, "photo_restore")
        self.assertEqual(entry.version, "1.0.0")
        self.assertEqual(entry.download_url, "")
        self.assertEqual(entry.catalog_status, "LOCAL PACKAGE REQUIRED")

    def test_directory_zip_and_smp_follow_existing_offline_contract(self) -> None:
        service = ModelInstallService.__new__(ModelInstallService)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "photo_restore"
            source.mkdir()
            manifest = package_manifest()
            (source / "package.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            for relative in COMPONENT_PATHS:
                target = source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"test")

            directory_result = service._validate_local_package_source(
                "photo_restore", str(source)
            )
            self.assertTrue(directory_result["success"], directory_result)

            for suffix in (".zip", ".smp"):
                archive = root / f"photo_restore{suffix}"
                with zipfile.ZipFile(archive, "w") as package:
                    package.write(source / "package.json", "photo_restore/package.json")
                    for relative in COMPONENT_PATHS:
                        package.write(source / relative, f"photo_restore/{relative}")
                result = service._validate_local_package_source(
                    "photo_restore", str(archive)
                )
                self.assertTrue(result["success"], result)

    def test_existing_install_is_not_overwritten_when_replacement_is_disabled(self) -> None:
        service = ModelInstallService.__new__(ModelInstallService)
        service.repository = RepositoryStub()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models_dir = root / "models"
            installed = models_dir / "photo_restore"
            installed.mkdir(parents=True)
            marker = installed / "keep.bin"
            marker.write_bytes(b"keep")

            source = root / "source"
            source.mkdir()
            (source / "package.json").write_text(
                json.dumps(package_manifest()), encoding="utf-8"
            )
            for relative in COMPONENT_PATHS:
                target = source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"new")

            with patch("engine.model_install_service.MODELS_DIR", models_dir):
                result = service.install_package(
                    "photo_restore", str(source), replace_existing=False
                )

            self.assertFalse(result)
            self.assertEqual(marker.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
