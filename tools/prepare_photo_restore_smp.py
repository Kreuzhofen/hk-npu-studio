"""
HK NPU STUDIO â€“ Sprint 113: FiDeSR SMP Package Preparation and Validation Tool

Builds the standardized photo_restore.smp archive, installs it to
%LOCALAPPDATA%\\HK NPU STUDIO\\models\\photo_restore, and verifies complete SHA-256
hash integrity, ModelRegistry compliance, and PhotoRestorePackageResolver readiness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config
from controllers.model_repository import ModelRepository
from engine.backends.photo_restore_package_resolver import PhotoRestorePackageResolver
from engine.model_install_service import ModelInstallService
from engine.model_registry import ModelHealthStatus, ModelRegistry

MANIFEST_SOURCE = REPO_ROOT / "resources" / "packages" / "photo_restore" / "package.json"
PACKAGES_DIR = REPO_ROOT / "dist" / "packages"

PACKAGE_PAYLOAD_MAP = {
    # Destination inside package -> Source on disk
    "package.json": REPO_ROOT / "resources" / "packages" / "photo_restore" / "package.json",
    "LICENSE-APACHE-2.0.txt": REPO_ROOT / "resources" / "packages" / "photo_restore" / "LICENSE-APACHE-2.0.txt",
    "LICENSE-CREATIVEML-OPENRAIL-M.txt": REPO_ROOT / "resources" / "packages" / "photo_restore" / "LICENSE-CREATIVEML-OPENRAIL-M.txt",
    "THIRD_PARTY_NOTICES.md": REPO_ROOT / "resources" / "packages" / "photo_restore" / "THIRD_PARTY_NOTICES.md",
    "models/fidesr_empty_prompt_embeds.bin": REPO_ROOT / "models" / "photo_restore" / "fidesr_empty_prompt_embeds.bin",
    "models/fidesr_epsilon_seed231.bin": REPO_ROOT / "models" / "photo_restore" / "fidesr_epsilon_seed231.bin",
    "context/fidesr_vae_encoder/fidesr_vae_encoder.serialized.bin.bin": (
        REPO_ROOT / "models" / "photo_restore_context" / "fidesr_vae_encoder" / "fidesr_vae_encoder.serialized.bin.bin"
    ),
    "context/fidesr_unet/fidesr_unet_merged.serialized.bin.bin": (
        REPO_ROOT / "models" / "photo_restore_context" / "fidesr_unet" / "fidesr_unet_merged.serialized.bin.bin"
    ),
    "context/fidesr_lrrb/fidesr_lrrb.serialized.bin.bin": (
        REPO_ROOT / "models" / "photo_restore_context" / "fidesr_lrrb" / "fidesr_lrrb.serialized.bin.bin"
    ),
    "context/fidesr_vae_decoder/fidesr_vae_decoder.serialized.bin.bin": (
        REPO_ROOT / "models" / "photo_restore_context" / "fidesr_vae_decoder" / "fidesr_vae_decoder.serialized.bin.bin"
    ),
}


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_smp_package(target_path: Path) -> Path:
    """Pack all FiDeSR components into a standardized .smp package (ZIP)."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_SOURCE.read_text(encoding="utf-8"))
    expected_components = manifest.get("components", {})

    print(f"[*] Validating {len(PACKAGE_PAYLOAD_MAP)} payload source files before packaging...")
    for arc_path, src_path in PACKAGE_PAYLOAD_MAP.items():
        if not src_path.is_file():
            raise FileNotFoundError(f"Missing required payload source: {src_path}")
        if arc_path.startswith("models/") or arc_path.startswith("context/"):
            # Check against manifest
            matched_key = next((k for k, v in expected_components.items() if v.get("path") == arc_path), None)
            if matched_key:
                actual_hash = compute_sha256(src_path)
                expected_hash = expected_components[matched_key].get("sha256", "").upper()
                if actual_hash != expected_hash:
                    raise ValueError(f"Hash mismatch for {arc_path}: actual {actual_hash} != expected {expected_hash}")
                print(f"    [OK] {arc_path} (SHA-256 verified: {actual_hash[:16]}...)")

    print(f"[*] Creating SMP archive at {target_path} (ZIP_DEFLATED)...")
    # Using ZIP_STORED or ZIP_DEFLATED (vorkompilierte QNN Kontextdateien sind bereits komprimierte BinÃ¤rdaten)
    with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as smp:
        for arc_path, src_path in PACKAGE_PAYLOAD_MAP.items():
            print(f"    Adding {arc_path} ({src_path.stat().st_size:,} bytes)...")
            smp.write(src_path, arc_path)

    print(f"[+] SMP package successfully created: {target_path} ({target_path.stat().st_size:,} bytes)")
    return target_path


def install_to_appdata(smp_path: Path) -> Path:
    """Install the package into %LOCALAPPDATA%\\HK NPU STUDIO\\models\\photo_restore."""
    target_dir = config.LOCAL_APP_DATA / config.PRODUCT_DATA_DIR_NAME / "models" / "photo_restore"
    print(f"[*] Installing SMP package to {target_dir}...")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(smp_path, "r") as smp:
        smp.extractall(target_dir)

    print(f"[+] Package extracted to {target_dir}")
    return target_dir


def verify_installation(target_dir: Path) -> bool:
    """Verify that ModelRegistry and ModelRepository recognize the model as Ready."""
    print("[*] Validating installation with ModelRegistry and ModelRepository...")
    registry = ModelRegistry()
    test_model = {
        "id": "photo_restore",
        "path": str(target_dir),
        "installed": True,
        "capabilities": {"qnn_runtime": True},
    }
    validation = registry.validate_installation(test_model, verify_hashes=True)
    print(f"    Registry status: {validation.status.value} (valid: {validation.valid})")
    print(f"    Verified hashes: {validation.checked_hashes}")
    for issue in validation.issues:
        print(f"    [ISSUE] {issue.message}")

    if not validation.valid or validation.status != ModelHealthStatus.READY:
        print("[-] Registry validation failed!")
        return False

    repo = ModelRepository()
    model = repo.get_model("photo_restore")
    print(f"    Repository model status: {model.get('status')}")
    print(f"    Repository model path: {model.get('path')}")
    print(f"    Repository model installed: {model.get('installed')}")

    resolver = PhotoRestorePackageResolver()
    resolution = resolver.resolve()
    print(f"    Resolver ready: {resolution.ready} (status: {resolution.status})")
    if resolution.artifacts:
        print(f"    Resolved UNet: {resolution.artifacts.unet_context}")

    success = (
        validation.valid
        and validation.status == ModelHealthStatus.READY
        and model.get("status") == "Ready"
        and model.get("installed") is True
        and resolution.ready
    )
    if success:
        print("[+] SUCCESS: FiDeSR Photo Restore is fully valid, installed, and Ready!")
    else:
        print("[-] FAILURE: Not all verification checks passed.")
    return success


def main() -> int:
    parser = argparse.ArgumentParser(description="FiDeSR SMP Packaging and Verification Tool")
    parser.add_argument("--build", action="store_true", help="Build photo_restore.smp")
    parser.add_argument("--install", action="store_true", help="Install to %LOCALAPPDATA%\\HK NPU STUDIO\\models\\photo_restore")
    parser.add_argument("--verify", action="store_true", help="Verify installation status")
    args = parser.parse_args()

    # Default to running all steps if no args given
    do_all = not (args.build or args.install or args.verify)

    smp_target = PACKAGES_DIR / "photo_restore.smp"

    if args.build or do_all:
        build_smp_package(smp_target)

    if args.install or do_all:
        target_dir = install_to_appdata(smp_target)
    else:
        target_dir = config.LOCAL_APP_DATA / config.PRODUCT_DATA_DIR_NAME / "models" / "photo_restore"

    if args.verify or do_all:
        if not verify_installation(target_dir):
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
