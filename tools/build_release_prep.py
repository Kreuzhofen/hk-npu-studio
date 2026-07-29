from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.build_app import main as build_app
from tools.build_installer import main as build_installer
from tools.validate_release_artifacts import main as validate_artifacts


def main() -> int:
    for step in (build_app, build_installer, validate_artifacts):
        result = step()
        if result:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
