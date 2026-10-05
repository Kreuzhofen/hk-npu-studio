from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import io
import hashlib

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


def github_release(
    version="2.0.0-rc.4",
    *,
    draft=False,
    prerelease=True,
    asset_name=None,
    digest=None,
    url=None,
):
    asset_name = asset_name or f"HKNPUStudio-{version}-ARM64-Setup.exe"
    return {
        "tag_name": f"v{version}",
        "name": f"VERSION {version}",
        "draft": draft,
        "prerelease": prerelease,
        "body": "Release notes",
        "html_url": f"https://github.test/releases/{version}",
        "assets": [
            {
                "name": asset_name,
                "browser_download_url": url or f"https://github.test/{asset_name}",
                "size": 123456,
                "digest": digest or f"sha256:{'b' * 64}",
            }
        ],
    }


def test_historical_rc_versions_follow_project_release_order():
    ordered = (
        "2.0.0-rc1",
        "2.0.0-rc.2",
        "2.0.0-rc.2a",
        "2.0.0-rc.2b",
        "2.0.0-rc.3",
        "2.0.0-rc.4",
        "2.0.0",
        "2.0.1",
        "2.1.0",
    )

    for older, newer in zip(ordered, ordered[1:]):
        assert ApplicationUpdateService._compare_versions(older, newer) < 0
        assert ApplicationUpdateService._compare_versions(newer, older) > 0

    assert ApplicationUpdateService._compare_versions("2.0.0-rc1", "2.0.0-rc.1") == 0
    assert ApplicationUpdateService._compare_versions("2.0.0-rc.3", "2.0.0") < 0
    assert ApplicationUpdateService._normalize_tag("v2.0.0-rc1") == "2.0.0-rc.1"
    assert ApplicationUpdateService._normalize_tag("v2.0.0-rc.2a") == "2.0.0-rc.2a"


def test_current_rc3_ignores_all_historical_and_equal_rc_releases():
    service = ApplicationUpdateService(current_version="2.0.0-rc.3")
    result = service.check_github_releases(
        [
            github_release("2.0.0-rc1"),
            github_release("2.0.0-rc.2"),
            github_release("2.0.0-rc.2a"),
            github_release("2.0.0-rc.2b"),
            github_release("2.0.0-rc.3"),
        ]
    )

    assert result.available is False
    assert result.error_code is None
    assert "neuesten Stand" in result.message


def test_github_channel_orders_rc_and_stable_versions():
    service = ApplicationUpdateService(current_version="2.0.0-rc.3")

    rc = service.check_github_releases([github_release("2.0.0-rc.4")])
    stable = service.check_github_releases([github_release("2.0.0", prerelease=False)])

    assert rc.available is True
    assert rc.manifest.version == "2.0.0-rc.4"
    assert stable.available is True
    assert stable.manifest.version == "2.0.0"


def test_github_ignores_drafts_same_and_older_releases():
    service = ApplicationUpdateService(current_version="2.0.0-rc.3")
    result = service.check_github_releases(
        [
            github_release("2.0.0-rc.5", draft=True),
            github_release("2.0.0-rc.3"),
            github_release("2.0.0-rc.2"),
        ]
    )

    assert result.available is False
    assert result.error_code is None

    stable_service = ApplicationUpdateService(current_version="2.0.0")
    assert stable_service.check_github_releases(
        [github_release("2.0.0-rc.9")]
    ).available is False


def test_github_requires_exact_arm64_name_https_and_sha256_digest():
    service = ApplicationUpdateService(current_version="2.0.0-rc.3")
    wrong_name = service.check_github_releases(
        [github_release(asset_name="SomeOther-ARM64.exe")]
    )
    insecure = service.check_github_releases(
        [github_release(url="http://github.test/update.exe")]
    )
    missing_digest = service.check_github_releases(
        [github_release(digest="md5:" + "b" * 32)]
    )

    assert wrong_name.error_code == "installer_missing"
    assert insecure.error_code == "https_required"
    assert missing_digest.error_code == "digest_missing"


def test_github_accepts_primary_and_legacy_exact_installer_names():
    service = ApplicationUpdateService(current_version="2.0.0-rc.3")
    primary = service.check_github_releases([github_release()])
    legacy = service.check_github_releases(
        [github_release(asset_name="SnapdragonAIStudio-2.0.0-rc.4-ARM64-Setup.exe")]
    )

    assert primary.available is True
    assert legacy.available is True


def test_only_verified_installer_is_launched_with_argument_list(tmp_path):
    payload = b"verified installer"
    expected_hash = hashlib.sha256(payload).hexdigest()
    launched = []

    class Downloader:
        def download(self, _url, **kwargs):
            path = tmp_path / kwargs["filename"]
            path.write_bytes(payload)
            return SimpleNamespace(success=True, path=path, message="ok")

        def cancel(self):
            pass

    service = ApplicationUpdateService(
        current_version="2.0.0-rc.3",
        download_service=Downloader(),
        popen=lambda command, **kwargs: launched.append((command, kwargs)),
    )
    update = ApplicationUpdateManifest(
        version="2.0.0-rc.4",
        architecture="arm64",
        package_url="https://github.test/update.exe",
        sha256=expected_hash,
    )

    staged = service.stage_update(update)
    result = service.launch_installer(staged.installer_path)

    assert result.success is True
    assert launched == [([str(staged.installer_path.resolve()), "/SILENT"], {"shell": False})]


def test_hash_change_or_popen_failure_never_reports_launch_success(tmp_path):
    payload = b"verified installer"
    expected_hash = hashlib.sha256(payload).hexdigest()

    class Downloader:
        def download(self, _url, **kwargs):
            path = tmp_path / kwargs["filename"]
            path.write_bytes(payload)
            return SimpleNamespace(success=True, path=path, message="ok")

        def cancel(self):
            pass

    update = ApplicationUpdateManifest(
        version="2.0.0-rc.4",
        architecture="arm64",
        package_url="https://github.test/update.exe",
        sha256=expected_hash,
    )
    service = ApplicationUpdateService(
        current_version="2.0.0-rc.3", download_service=Downloader()
    )
    staged = service.stage_update(update)
    staged.installer_path.write_bytes(b"tampered")
    assert service.launch_installer(staged.installer_path).success is False

    failing = ApplicationUpdateService(
        current_version="2.0.0-rc.3",
        download_service=Downloader(),
        popen=lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("blocked")),
    )
    staged = failing.stage_update(update)
    assert failing.launch_installer(staged.installer_path).success is False
