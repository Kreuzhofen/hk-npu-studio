from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.qnn_package_qualification import QnnPackageQualifier, deterministic_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and qualify a local QNN package safely.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "qualify"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--package", required=True, type=Path)
        sub.add_argument("--output", type=Path)
        if command == "qualify":
            sub.add_argument("--strict", action="store_true", help="Run strict QNN loads without CPU fallback.")
            sub.add_argument("--allow-build", action="store_true", help="Request an optional safe compile assessment; builds remain disabled unless all gates allow them.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    qualifier = QnnPackageQualifier()
    if args.command == "inspect":
        report = qualifier.inspect(args.package)
    else:
        report = qualifier.qualify(args.package, strict=args.strict, allow_build=args.allow_build)
    payload = deterministic_json(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return 0 if report["qualification_status"] in {"QUALIFIED", "CONDITIONALLY_QUALIFIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
