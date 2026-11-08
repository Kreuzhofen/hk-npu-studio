"""
HK NPU STUDIO - SPRINT 109
Unit & Integration Test Suite for Version Derivation in tools/build_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_app import parse_version_tuple, _parse_version_tuple, _write_version_file
from engine.release_config import RELEASE
import PyInstaller.utils.win32.versioninfo as vi


def test_valid_version_derivation():
    print("\n--- Test 1: Valid Version Derivations ---")
    # Primary requirement:
    res_210 = parse_version_tuple("2.1.0")
    assert res_210 == (2, 1, 0, 0), f"Expected (2, 1, 0, 0), got {res_210}"
    print(f"PASS: '2.1.0' -> {res_210}")

    # Aliases and variants:
    assert _parse_version_tuple("2.1.0") == (2, 1, 0, 0)
    assert parse_version_tuple("2.1") == (2, 1, 0, 0)
    assert parse_version_tuple("2.0.0.0") == (2, 0, 0, 0)
    assert parse_version_tuple("2.1.0.4") == (2, 1, 0, 4)
    assert parse_version_tuple("3") == (3, 0, 0, 0)
    print("PASS: Additional valid variants ('2.1', '2.0.0.0', '2.1.0.4', '3') verified.")


def test_invalid_versions_rejected():
    print("\n--- Test 2: Invalid Versions Rejected ---")
    invalid_cases = [
        ("2.1.beta", "Non-numeric suffix"),
        ("2.1.x", "Character 'x'"),
        ("invalid", "Arbitrary text"),
        ("2.1.0-rc4", "Hyphenated pre-release tag"),
        ("-1.0.0", "Negative number"),
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        ("2.1.0.0.1", "More than 4 components"),
        ("2..0", "Empty component between dots"),
        ("2.1.70000", "Component > 65535"),
        (None, "None type"),
        (123, "Integer type"),
    ]

    for val, reason in invalid_cases:
        try:
            parse_version_tuple(val)  # type: ignore
        except ValueError as err:
            print(f"PASS: Rejected {reason} ({val!r}): {err}")
        else:
            raise AssertionError(f"Expected ValueError for {val!r} ({reason}), but it succeeded!")


def test_generated_version_info_contains_2_1_0_0():
    print("\n--- Test 3: Generated version_info.txt Contains 2.1.0.0 ---")
    generated_path = _write_version_file()
    assert generated_path.is_file(), f"version_info.txt was not created at {generated_path}"
    content = generated_path.read_text(encoding="utf-8")

    assert "2.1.0.0" in content, f"Expected '2.1.0.0' to be present in version_info.txt:\n{content}"
    assert "filevers=(2, 1, 0, 0)" in content, "Expected 'filevers=(2, 1, 0, 0)' in version_info.txt"
    assert "prodvers=(2, 1, 0, 0)" in content, "Expected 'prodvers=(2, 1, 0, 0)' in version_info.txt"
    assert "StringStruct('FileVersion', '2.1.0')" in content
    assert "StringStruct('ProductVersion', '2.1.0')" in content

    # Test PyInstaller's actual parser
    parsed = vi.load_version_info_from_text_file(str(generated_path))
    assert parsed is not None
    print(f"PASS: version_info.txt generated at {generated_path}")
    print("PASS: Verified presence of '2.1.0.0', 'filevers=(2, 1, 0, 0)', and PyInstaller parsing.")


def main():
    print("================================================================")
    print("HK NPU STUDIO - SPRINT 109 VERSION DERIVATION TEST SUITE")
    print("================================================================")
    test_valid_version_derivation()
    test_invalid_versions_rejected()
    test_generated_version_info_contains_2_1_0_0()
    print("\n================================================================")
    print("ALL SPRINT 109 TESTS PASSED (3/3)")
    print("================================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
