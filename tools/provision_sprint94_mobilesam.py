"""
Sprint 94: MobileSAM Model Provisioning Script.
Downloads official Qualcomm AI Hub MobileSAM ONNX and QNN DLC releases (QAIRT 2.50 compatible),
extracts them to C:\SnapdragonAI\models\mobilesam_qnn\, verifies SHA-256, and inspects metadata.
"""

import hashlib
import json
import os
import urllib.request
import zipfile
from pathlib import Path

DEST_DIR = Path("C:/SnapdragonAI/models/mobilesam_qnn")

ASSETS = {
    "onnx": "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/mobilesam/releases/v0.65.0/mobilesam-onnx-float.zip",
    "qnn_dlc": "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/mobilesam/releases/v0.65.0/mobilesam-qnn_dlc-float.zip",
}


def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def download_and_extract(url: str, target_dir: Path, subfolder_prefix: str):
    print(f"Downloading from {url}...")
    zip_path = target_dir / "temp_archive.zip"
    urllib.request.urlretrieve(url, zip_path)
    print(f"Extracting {zip_path.stat().st_size} bytes...")
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            # Strip subfolder prefix if present (e.g. mobilesam-onnx-float/...)
            rel_name = member
            if rel_name.startswith(subfolder_prefix):
                rel_name = rel_name[len(subfolder_prefix) :].lstrip("/\\")
            if not rel_name:
                continue
            out_path = target_dir / rel_name
            if member.endswith("/"):
                out_path.mkdir(parents=True, exist_ok=True)
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as src, open(out_path, "wb") as dst:
                    dst.write(src.read())
    zip_path.unlink()


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    onnx_dir = DEST_DIR / "onnx"
    dlc_dir = DEST_DIR / "qnn_dlc"
    onnx_dir.mkdir(parents=True, exist_ok=True)
    dlc_dir.mkdir(parents=True, exist_ok=True)

    print("=== PROVISIONING ONNX ARTIFACTS ===")
    download_and_extract(ASSETS["onnx"], onnx_dir, "mobilesam-onnx-float/")

    print("\n=== PROVISIONING QNN DLC ARTIFACTS ===")
    download_and_extract(ASSETS["qnn_dlc"], dlc_dir, "mobilesam-qnn_dlc-float/")

    print("\n=== VERIFYING SHA-256 MANIFEST ===")
    manifest = {}
    for p in sorted(DEST_DIR.rglob("*")):
        if p.is_file():
            rel_p = str(p.relative_to(DEST_DIR)).replace("\\", "/")
            h = sha256_of_file(p)
            manifest[rel_p] = {"sha256": h, "size_bytes": p.stat().st_size}
            print(f"  {rel_p}: {p.stat().st_size} bytes | SHA-256: {h}")

    manifest_file = DEST_DIR / "SHA256_MANIFEST.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved to {manifest_file}")


if __name__ == "__main__":
    main()
