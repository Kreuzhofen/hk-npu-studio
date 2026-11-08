"""
HK NPU STUDIO 2.1.0 – Phoenix Evolution
Sprint Quality & Consistency Validation Tool
"""
from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI").resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import version
from engine.brand_manager import BrandManager
from engine.release_config import RELEASE
from engine.theme_manager import ThemeManager
from widgets.phoenix.header import PhoenixHeader
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme


def validate_central_version_definition():
    print("\n--- 1. Testing Central Version Definition ---")
    assert RELEASE.app_name == "HK NPU STUDIO", f"app_name is {RELEASE.app_name}"
    assert RELEASE.display_version == "2.1.0", f"display_version is {RELEASE.display_version}"
    assert RELEASE.package_version == "2.1.0", f"package_version is {RELEASE.package_version}"
    assert RELEASE.codename == "Phoenix Evolution", f"codename is {RELEASE.codename}"
    assert RELEASE.build == "2026.11.07", f"build is {RELEASE.build}"
    assert RELEASE.architecture == "arm64", f"architecture is {RELEASE.architecture}"
    assert RELEASE.executable_name == "HKNPUStudio.exe", f"executable_name is {RELEASE.executable_name}"

    assert version.APP_NAME == "HK NPU STUDIO"
    assert version.VERSION == "2.1.0"
    assert version.PACKAGE_VERSION == "2.1.0"
    assert version.CODENAME == "Phoenix Evolution"
    assert version.BUILD == "2026.11.07"
    assert version.ARCHITECTURE == "arm64"

    brand = BrandManager()
    assert brand.APP_VERSION == "2.1.0"
    assert brand.CODENAME == "Phoenix Evolution"
    assert brand.window_title() == "HK NPU STUDIO 2.1.0 – Phoenix Evolution"
    assert brand.version_string() == "VERSION 2.1.0 – Phoenix Evolution"
    assert brand.full_product_name() == "HK NPU STUDIO 2.1.0 – Phoenix Evolution"
    print("PASS: Central version definitions and BrandManager mappings are fully synchronized.")


def validate_ui_header_and_themes():
    print("\n--- 2. Testing UI Header (Top-Right Version Display) & Themes ---")
    root = tk.Tk()
    root.withdraw()
    try:
        for theme_name in ("dark", "light"):
            ThemeManager.set_active_theme(theme_name)
            update_phoenix_theme(theme_name)
            header = PhoenixHeader(root)
            header.pack()
            root.update()

            # Children of header:
            # 0: left (logo + title_group)
            # 1: release_group (top-right)
            release_group = header.winfo_children()[1]
            labels = [w for w in release_group.winfo_children() if isinstance(w, tk.Label)]
            assert len(labels) == 2, f"Expected 2 labels in release_group, got {len(labels)}"

            top_label = labels[0]
            bottom_label = labels[1]

            version_text = top_label.cget("text")
            codename_text = bottom_label.cget("text")

            assert version_text == "2.1.0", f"Top label expected '2.1.0', got '{version_text}'"
            assert codename_text == "Phoenix Evolution", f"Bottom label expected 'Phoenix Evolution', got '{codename_text}'"

            # Check styles & colors
            assert top_label.cget("fg") == PHOENIX_THEME.accent, f"Accent mismatch: {top_label.cget('fg')} vs {PHOENIX_THEME.accent}"
            assert bottom_label.cget("fg") == PHOENIX_THEME.text_muted, f"Muted mismatch: {bottom_label.cget('fg')} vs {PHOENIX_THEME.text_muted}"
            assert top_label.cget("bg") == PHOENIX_THEME.header_bg
            assert bottom_label.cget("bg") == PHOENIX_THEME.header_bg

            print(f"PASS: Theme '{theme_name}' verified:")
            print(f"      Top-right Line 1: '{version_text}' (color: {top_label.cget('fg')}, bg: {top_label.cget('bg')})")
            print(f"      Top-right Line 2: '{codename_text}' (color: {bottom_label.cget('fg')}, bg: {bottom_label.cget('bg')})")

            header.destroy()
    finally:
        root.destroy()
        ThemeManager.set_active_theme("dark")
        update_phoenix_theme("dark")


def validate_about_dialog():
    print("\n--- 3. Testing About Dialog Branding ---")
    root = tk.Tk()
    root.withdraw()
    try:
        from dialogs.about_dialog import AboutDialog
        brand = BrandManager()
        dialog = AboutDialog(root, brand)
        root.update()

        labels = [w for w in dialog.body.winfo_children() if isinstance(w, tk.Label)]
        texts = [w.cget("text") for w in labels]

        assert "HK NPU STUDIO" in texts, "Header brand name missing from About dialog"
        assert "VERSION 2.1.0 – Phoenix Evolution" in texts, f"Version string missing from About dialog: {texts}"
        print(f"PASS: About dialog displays: 'HK NPU STUDIO' and 'VERSION 2.1.0 – Phoenix Evolution'.")
        dialog.destroy()
    finally:
        root.destroy()


def validate_installer_configuration():
    print("\n--- 4. Testing Installer Configuration ---")
    iss_path = REPO_ROOT / "installer" / "snapdragon_ai_studio.iss"
    content = iss_path.read_text(encoding="utf-8")

    assert "AppVerName=HK NPU STUDIO 2.1.0 – Phoenix Evolution" in content
    assert "OutputBaseFilename=HKNPUStudio-{#AppVersion}-ARM64-Setup" in content
    assert "english.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0" in content
    assert "english.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution" in content
    assert "german.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0" in content
    assert "german.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution" in content
    assert "spanish.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0" in content
    assert "spanish.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution" in content

    # Check that NPU Hardware check is intact
    assert "Function InitializeSetup(): Boolean;" in content or "function InitializeSetup(): Boolean;" in content
    assert "qcadsprpc" in content
    assert "ArchitecturesAllowed=arm64" in content
    assert "ArchitecturesInstallIn64BitMode=arm64" in content

    from tools.build_installer import build_command
    cmd = build_command("ISCC.exe")
    assert "/DAppVersion=2.1.0" in cmd, f"Expected /DAppVersion=2.1.0, got: {cmd}"
    assert "/DAppName=HK NPU STUDIO" in cmd
    assert "/DExecutableName=HKNPUStudio.exe" in cmd

    target_installer_name = f"HKNPUStudio-{RELEASE.package_version}-ARM64-Setup.exe"
    assert target_installer_name == "HKNPUStudio-2.1.0-ARM64-Setup.exe"
    print(f"PASS: Installer target executable name: {target_installer_name}")
    print("PASS: Installer strings, parameters, and architecture validation verified.")


def validate_version_info_txt():
    print("\n--- 5. Testing build/release/version_info.txt ---")
    info_path = REPO_ROOT / "build" / "release" / "version_info.txt"
    content = info_path.read_text(encoding="utf-8")
    assert "filevers=(2, 1, 0, 0)" in content
    assert "prodvers=(2, 1, 0, 0)" in content
    assert "StringStruct('FileVersion', '2.1.0')" in content
    assert "StringStruct('ProductVersion', '2.1.0')" in content
    assert "StringStruct('FileDescription', 'HK NPU STUDIO 2.1.0 – Phoenix Evolution')" in content
    print("PASS: Windows PE version_info.txt verified with version 2.1.0.")


def main():
    print("=================================================================")
    print("HK NPU STUDIO 2.1.0 – PHOENIX EVOLUTION VALIDATION SUITE")
    print("=================================================================")
    validate_central_version_definition()
    validate_ui_header_and_themes()
    validate_about_dialog()
    validate_installer_configuration()
    validate_version_info_txt()
    print("\n=================================================================")
    print("ALL SPRINT VALIDATION CHECKS PASSED (5/5)")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
