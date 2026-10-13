from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from controllers.model_repository import ModelRepository
from engine.model_install_service import ModelInstallService


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "resources" / "packages" / "photo_restore" / "package.json"
MODEL_DEFINITION = ROOT / "resources" / "models" / "photo_restore.json"
EXPECTED_COMPONENTS = {
    "empty_prompt_embeddings": (
        "models/fidesr_empty_prompt_embeds.bin",
        "26E5E7D387699FDF4BB52EBD914A3BC686801604CC1C11CBCDD7FD6FE28B5604",
    ),
    "epsilon_seed": (
        "models/fidesr_epsilon_seed231.bin",
        "F24A5790735DCBF9D05B027D2CF1C0D23064A82EB8FB7E24198884A5FB983E1B",
    ),
    "vae_encoder_context": (
        "context/fidesr_vae_encoder/fidesr_vae_encoder.serialized.bin.bin",
        "9A12999304CB34D19C0C7BA03E8593C2DF528628D404F6A512FB513F7E657B50",
    ),
    "unet_context": (
        "context/fidesr_unet/fidesr_unet_merged.serialized.bin.bin",
        "3A169A72D76CE949F803D5C49DA4EFBB2568A7D16668B61E1344134EC28C94AE",
    ),
    "lrrb_context": (
        "context/fidesr_lrrb/fidesr_lrrb.serialized.bin.bin",
        "1CDE7CC8979611168EE81845C4E14702DEE636CCC0F683DD76FDD679B97CA9F9",
    ),
    "vae_decoder_context": (
        "context/fidesr_vae_decoder/fidesr_vae_decoder.serialized.bin.bin",
        "C9C78E694A88EF6EA4D5D7FD7AF02FE7C5337F097BDACBF5D1547F66692C5D84",
    ),
}


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _create_synthetic_package(root: Path) -> tuple[ModelInstallService, Path]:
    managed_models = root / "managed-models"
    package_root = managed_models / "photo_restore"
    package_root.mkdir(parents=True)
    manifest = copy.deepcopy(_load_manifest())
    for name, component in manifest["components"].items():
        content = f"synthetic-{name}".encode("utf-8")
        target = package_root / component["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        component["sha256"] = hashlib.sha256(content).hexdigest()
    (package_root / "package.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    definitions = root / "definitions"
    definitions.mkdir()
    definitions.joinpath("photo_restore.json").write_text(
        MODEL_DEFINITION.read_text(encoding="utf-8"), encoding="utf-8"
    )
    repository = ModelRepository(
        models_dir=str(definitions), installation_roots=[managed_models]
    )
    return ModelInstallService(repository), package_root


def test_productive_manifest_matches_real_contract() -> None:
    manifest = _load_manifest()

    assert manifest["package_id"] == "photo_restore"
    assert manifest["package_version"] == "1.0.0"
    assert manifest["architecture"] == "arm64"
    assert manifest["app_min_version"] == "2.0.0-rc.3"
    assert manifest["runtime"] == "QNN"
    assert manifest["capabilities"]["photo_restore"] is True
    assert set(manifest["components"]) == set(EXPECTED_COMPONENTS)
    for name, (path, sha256) in EXPECTED_COMPONENTS.items():
        assert manifest["components"][name] == {
            "path": path,
            "runtime": "QNN",
            "sha256": sha256,
        }
    serialized = json.dumps(manifest)
    assert "C:\\SnapdragonAI" not in serialized
    assert "download_url" not in manifest


def test_validate_package_accepts_matching_component_hashes() -> None:
    with tempfile.TemporaryDirectory() as directory:
        service, _ = _create_synthetic_package(Path(directory))

        result = service.validate_package("photo_restore")

        assert result["success"] is True
        assert result["is_fully_ready"] is True
        assert result["checksum_hint"].startswith("6 SHA-256")


def test_validate_package_rejects_tampered_component() -> None:
    with tempfile.TemporaryDirectory() as directory:
        service, package_root = _create_synthetic_package(Path(directory))
        component = package_root / EXPECTED_COMPONENTS["unet_context"][0]
        component.write_bytes(b"tampered")

        result = service.validate_package("photo_restore")

        assert result["success"] is False
        assert any("SHA-256" in issue for issue in result["issues"])


def test_validate_package_rejects_missing_component() -> None:
    with tempfile.TemporaryDirectory() as directory:
        service, package_root = _create_synthetic_package(Path(directory))
        component = package_root / EXPECTED_COMPONENTS["epsilon_seed"][0]
        component.unlink()

        result = service.validate_package("photo_restore")

        assert result["success"] is False
        assert str(component) in result["missing_files"]


def test_validate_package_rejects_wrong_package_id() -> None:
    with tempfile.TemporaryDirectory() as directory:
        service, package_root = _create_synthetic_package(Path(directory))
        manifest_path = package_root / "package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["package_id"] = "wrong_package"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = service.validate_package("photo_restore")

        assert result["success"] is False
        assert any("Package-ID" in issue for issue in result["issues"])


def test_validate_package_rejects_path_traversal() -> None:
    with tempfile.TemporaryDirectory() as directory:
        service, package_root = _create_synthetic_package(Path(directory))
        outside = package_root.parent / "outside.bin"
        outside.write_bytes(b"outside")
        manifest_path = package_root / "package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["components"]["epsilon_seed"]["path"] = "../outside.bin"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = service.validate_package("photo_restore")

        assert result["success"] is False
        assert any("ungültigen Pfad" in issue for issue in result["issues"])
