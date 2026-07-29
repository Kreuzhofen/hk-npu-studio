from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.release_config import RELEASE


DIST_ROOT = PROJECT_ROOT / "dist"
MANIFEST_PATH = DIST_ROOT / "release-artifacts.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_artifacts() -> list[dict[str, object]]:
    app = DIST_ROOT / "SnapdragonAIStudio" / RELEASE.executable_name
    installers = sorted((DIST_ROOT / "installer").glob("*.exe"))
    paths = [app, *installers]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing or not installers:
        raise FileNotFoundError(
            "Release-Artefakte fehlen: "
            + ", ".join(missing or [str(DIST_ROOT / "installer" / "*.exe")])
        )
    return [
        {
            "path": path.relative_to(DIST_ROOT).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in paths
    ]


def main() -> int:
    manifest = {
        "app_name": RELEASE.app_name,
        "display_version": RELEASE.display_version,
        "package_version": RELEASE.package_version,
        "build": RELEASE.build,
        "architecture": RELEASE.architecture,
        "signed": False,
        "artifacts": collect_artifacts(),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(MANIFEST_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
