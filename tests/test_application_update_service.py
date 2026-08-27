from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import io

from engine.application_update_service import (
    ApplicationUpdateManifest,
    ApplicationUpdateService,
)


def manifest(version="2.0.0-rc.2", architecture="arm64"):
    return {
        "version": version,
        "architecture": architecture,
        "package_url": "https://updates.example.test/HKNPUStudio.exe",
        "sha256": "a" * 64,
    }


def test_newer_matching_arm64_manifest_is_available():
    result = ApplicationUpdateService(
        current_version="2.0.0-rc.1"
    ).check_manifest(manifest())

    assert result.available is True
    assert result.manifest.version == "2.0.0-rc.2"


def test_same_older_and_wrong_architecture_updates_are_rejected():
    service = ApplicationUpdateService(current_version="2.0.0-rc.1")

    assert service.check_manifest(manifest("2.0.0-rc.1")).available is False
    assert service.check_manifest(manifest("2.0.0-preview.9")).available is False
    wrong_arch = service.check_manifest(manifest(architecture="x64"))
    assert wrong_arch.available is False
    assert "inkompatibel" in wrong_arch.message


def test_manifest_requires_https_executable_and_sha256():
    service = ApplicationUpdateService(current_version="2.0.0-rc.1")
    insecure = manifest()
    insecure["package_url"] = "http://updates.example.test/update.exe"
    invalid_hash = manifest()
    invalid_hash["sha256"] = "missing"

    assert "HTTPS" in service.check_manifest(insecure).message
    assert "SHA-256" in service.check_manifest(invalid_hash).message


def test_verified_update_is_staged_without_launching_installer(tmp_path):
    calls = []

    class Downloader:
        def download(self, url, **kwargs):
            calls.append((url, kwargs))
            path = tmp_path / kwargs["filename"]
            path.write_bytes(b"verified")
            return SimpleNamespace(success=True, path=path, message="ok")

    service = ApplicationUpdateService(
        current_version="2.0.0-rc.1",
        download_service=Downloader(),
    )
    update = ApplicationUpdateManifest(**manifest())

    result = service.stage_update(update)

    assert result.success is True
    assert result.installer_path.is_file()
    assert calls[0][1]["expected_sha256"] == "a" * 64
    assert calls[0][1]["resume"] is True
    assert calls[0][1]["overwrite"] is True


def test_failed_download_never_returns_an_installer():
    class Downloader:
        def download(self, url, **kwargs):
            return SimpleNamespace(success=False, path=None, message="hash mismatch")

    service = ApplicationUpdateService(
        current_version="2.0.0-rc.1",
        download_service=Downloader(),
    )

    result = service.stage_update(ApplicationUpdateManifest(**manifest()))

    assert result.success is False
    assert result.installer_path is None
    assert result.message == "hash mismatch"


def test_https_manifest_fetch_uses_same_fail_closed_validation():
    class Response:
        def __init__(self):
            self.payload = io.BytesIO(
                __import__("json").dumps(manifest()).encode("utf-8")
            )

        def read(self, amount):
            return self.payload.read(amount)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    service = ApplicationUpdateService(
        current_version="2.0.0-rc.1",
        opener=lambda request, timeout: Response(),
    )

    result = service.fetch_and_check(
        "https://updates.example.test/manifest.json"
    )

    assert result.available is True
    assert result.manifest.sha256 == "a" * 64
