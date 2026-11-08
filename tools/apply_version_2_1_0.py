"""
HK NPU STUDIO 2.1.0 – Phoenix Evolution
Sprint Version Alignment Script
"""
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")

def update_brand_manager():
    path = REPO_ROOT / "engine" / "brand_manager.py"
    content = path.read_text(encoding="utf-8")

    # 1. Update class attributes
    target1 = '    APP_NAME = RELEASE.app_name\n    APP_VERSION = RELEASE.display_version\n\n    ENGINE_NAME = "HK NPU STUDIO"'
    repl1 = '    APP_NAME = RELEASE.app_name\n    APP_VERSION = RELEASE.display_version\n    CODENAME = RELEASE.codename\n    PRODUCT_FULL_NAME = f"{RELEASE.app_name} {RELEASE.display_version} – {RELEASE.codename}"\n\n    ENGINE_NAME = "HK NPU STUDIO"'
    if target1 not in content:
        target1 = target1.replace('\n', '\r\n')
        repl1 = repl1.replace('\n', '\r\n')
    assert target1 in content, "target1 not found in brand_manager.py"
    content = content.replace(target1, repl1, 1)

    target_win = '    WINDOW_TITLE_WITH_VERSION = APP_NAME'
    repl_win = '    WINDOW_TITLE_WITH_VERSION = PRODUCT_FULL_NAME'
    if target_win not in content:
        target_win = target_win.replace('\n', '\r\n')
        repl_win = repl_win.replace('\n', '\r\n')
    assert target_win in content, "target_win not found in brand_manager.py"
    content = content.replace(target_win, repl_win, 1)

    target_vstr = '    def version_string(self) -> str:\n        return f"VERSION {self.APP_VERSION}"'
    repl_vstr = '    def version_string(self) -> str:\n        return f"VERSION {self.APP_VERSION} – {self.CODENAME}"'
    if target_vstr not in content:
        target_vstr = target_vstr.replace('\n', '\r\n')
        repl_vstr = repl_vstr.replace('\n', '\r\n')
    assert target_vstr in content, "target_vstr not found in brand_manager.py"
    content = content.replace(target_vstr, repl_vstr, 1)

    target_wtitle = '    def window_title(self) -> str:\n        return self.HEADER_BRAND_NAME'
    repl_wtitle = '    def window_title(self) -> str:\n        return f"{self.HEADER_BRAND_NAME} {self.APP_VERSION} – {self.CODENAME}"\n\n    def codename(self) -> str:\n        return self.CODENAME\n\n    def full_product_name(self) -> str:\n        return f"{self.HEADER_BRAND_NAME} {self.APP_VERSION} – {self.CODENAME}"'
    if target_wtitle not in content:
        target_wtitle = target_wtitle.replace('\n', '\r\n')
        repl_wtitle = repl_wtitle.replace('\n', '\r\n')
    assert target_wtitle in content, "target_wtitle not found in brand_manager.py"
    content = content.replace(target_wtitle, repl_wtitle, 1)

    path.write_text(content, encoding="utf-8")
    print("Updated engine/brand_manager.py")


def update_header():
    path = REPO_ROOT / "widgets" / "phoenix" / "header.py"
    content = path.read_text(encoding="utf-8")

    # Current top-right release_group has:
    #         tk.Label(
    #             release_group,
    #             text=tr(
    #                 "version_value", "Version {version}", version=self.brand.APP_VERSION
    #             ),
    #             bg=PHOENIX_THEME.header_bg,
    #             fg=PHOENIX_THEME.accent,
    #             font=PHOENIX_THEME.font_section,
    #             anchor="e",
    #         ).pack(side="top", fill="x", anchor="e", pady=(6, 0))
    #
    #         tk.Label(
    #             release_group,
    #             text="© 2026 Holger Kreuzhofen",
    #             bg=PHOENIX_THEME.header_bg,
    #             fg=PHOENIX_THEME.text_muted,
    #             font=PHOENIX_THEME.font_small,
    #             anchor="e",
    #         ).pack(side="top", fill="x", anchor="e", pady=(0, 6))

    target = '''        tk.Label(
            release_group,
            text=tr(
                "version_value", "Version {version}", version=self.brand.APP_VERSION
            ),
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_section,
            anchor="e",
        ).pack(side="top", fill="x", anchor="e", pady=(6, 0))

        tk.Label(
            release_group,
            text="© 2026 Holger Kreuzhofen",
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="e",
        ).pack(side="top", fill="x", anchor="e", pady=(0, 6))'''

    repl = '''        tk.Label(
            release_group,
            text=self.brand.APP_VERSION,
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_section,
            anchor="e",
        ).pack(side="top", fill="x", anchor="e", pady=(6, 0))

        tk.Label(
            release_group,
            text=getattr(self.brand, "CODENAME", "Phoenix Evolution"),
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="e",
        ).pack(side="top", fill="x", anchor="e", pady=(0, 6))'''

    if target not in content:
        target = target.replace('\n', '\r\n')
        repl = repl.replace('\n', '\r\n')
    assert target in content, "target not found in header.py"
    content = content.replace(target, repl, 1)

    path.write_text(content, encoding="utf-8")
    print("Updated widgets/phoenix/header.py")


def update_version_info():
    path = REPO_ROOT / "build" / "release" / "version_info.txt"
    content = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 1, 0, 0), prodvers=(2, 1, 0, 0), mask=0x3f, flags=0x0,
    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable('040704B0', [
      StringStruct('CompanyName', 'Holger Kreuzhofen'),
      StringStruct('FileDescription', 'HK NPU STUDIO 2.1.0 – Phoenix Evolution'),
      StringStruct('FileVersion', '2.1.0'),
      StringStruct('InternalName', 'HKNPUStudio'),
      StringStruct('OriginalFilename', 'HKNPUStudio.exe'),
      StringStruct('ProductName', 'HK NPU STUDIO – Phoenix Evolution'),
      StringStruct('ProductVersion', '2.1.0')
    ])]),
    VarFileInfo([VarStruct('Translation', [1031, 1200])])
  ]
)"""
    path.write_text(content, encoding="utf-8")
    print("Updated build/release/version_info.txt")


def update_installer_iss():
    path = REPO_ROOT / "installer" / "snapdragon_ai_studio.iss"
    content = path.read_text(encoding="utf-8")

    # 1. AppVerName
    old_app_ver = "AppVerName=HK NPU STUDIO 2.0 RC4"
    new_app_ver = "AppVerName=HK NPU STUDIO 2.1.0 – Phoenix Evolution"
    assert old_app_ver in content, "old_app_ver not found in snapdragon_ai_studio.iss"
    content = content.replace(old_app_ver, new_app_ver, 1)

    # 2. English messages
    old_en = """[Messages]
english.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.0 RC4
english.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 4%nSelect the installation language:
english.WelcomeLabel1=Welcome to HK NPU STUDIO
english.WelcomeLabel2=HK NPU STUDIO · VERSION 2.0 RC4%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nPre-release version for testing and evaluation purposes.%n%nIndependent open-source project for Windows on Snapdragon. Not an official Qualcomm product.%n%n© 2026 Holger Kreuzhofen
english.FinishedHeadingLabel=HK NPU STUDIO 2.0 RC4 has been installed successfully
english.FinishedLabel=Setup has finished installing HK NPU STUDIO 2.0 RC4.%n%nThank you for testing HK NPU STUDIO RC4.

german.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.0 RC4
german.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 4%nInstallationssprache auswählen:
german.WelcomeLabel1=Willkommen bei HK NPU STUDIO
german.WelcomeLabel2=HK NPU STUDIO · VERSION 2.0 RC4%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nVorabversion zu Test- und Evaluierungszwecken.%n%nUnabhängiges Open-Source-Projekt für Windows auf Snapdragon. Kein offizielles Qualcomm-Produkt.%n%n© 2026 Holger Kreuzhofen
german.FinishedHeadingLabel=HK NPU STUDIO 2.0 RC4 wurde erfolgreich installiert
german.FinishedLabel=Die Installation von HK NPU STUDIO 2.0 RC4 wurde erfolgreich abgeschlossen.%n%nVielen Dank, dass Sie HK NPU STUDIO RC4 testen.

spanish.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.0 RC4
spanish.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Release Candidate 4%nSeleccione el idioma de instalación:
spanish.WelcomeLabel1=Bienvenido a HK NPU STUDIO
spanish.WelcomeLabel2=HK NPU STUDIO · VERSION 2.0 RC4%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nVersión preliminar para fines de prueba y evaluación.%n%nProyecto independiente de código abierto para Windows en Snapdragon. No es un producto oficial de Qualcomm.%n%n© 2026 Holger Kreuzhofen
spanish.FinishedHeadingLabel=HK NPU STUDIO 2.0 RC4 se ha instalado correctamente
spanish.FinishedLabel=HK NPU STUDIO 2.0 RC4 se ha instalado correctamente.%n%nGracias por probar HK NPU STUDIO RC4."""

    new_en = """[Messages]
english.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0
english.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Phoenix Evolution%nSelect the installation language:
english.WelcomeLabel1=Welcome to HK NPU STUDIO
english.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nIndependent open-source project for Windows on Snapdragon. Not an official Qualcomm product.%n%n© 2026 Holger Kreuzhofen
english.FinishedHeadingLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution has been installed successfully
english.FinishedLabel=Setup has finished installing HK NPU STUDIO 2.1.0 – Phoenix Evolution.

german.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0
german.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Phoenix Evolution%nInstallationssprache auswählen:
german.WelcomeLabel1=Willkommen bei HK NPU STUDIO
german.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nUnabhängiges Open-Source-Projekt für Windows auf Snapdragon. Kein offizielles Qualcomm-Produkt.%n%n© 2026 Holger Kreuzhofen
german.FinishedHeadingLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution wurde erfolgreich installiert
german.FinishedLabel=Die Installation von HK NPU STUDIO 2.1.0 – Phoenix Evolution wurde erfolgreich abgeschlossen.

spanish.SelectLanguageTitle=HK NPU STUDIO · VERSION 2.1.0
spanish.SelectLanguageLabel=© 2026 Holger Kreuzhofen · Phoenix Evolution%nSeleccione el idioma de instalación:
spanish.WelcomeLabel1=Bienvenido a HK NPU STUDIO
spanish.WelcomeLabel2=HK NPU STUDIO 2.1.0 – Phoenix Evolution%n%nYour Hardware • Your AI • Your Control%nLocal AI for Snapdragon® PCs%nFeaturing Phoenix Boost%n%nProyecto independiente de código abierto para Windows en Snapdragon. No es un producto oficial de Qualcomm.%n%n© 2026 Holger Kreuzhofen
spanish.FinishedHeadingLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution se ha instalado correctamente
spanish.FinishedLabel=HK NPU STUDIO 2.1.0 – Phoenix Evolution se ha instalado correctamente."""

    if old_en not in content:
        old_en = old_en.replace('\n', '\r\n')
        new_en = new_en.replace('\n', '\r\n')
    assert old_en in content, "old_en not found in snapdragon_ai_studio.iss"
    content = content.replace(old_en, new_en, 1)

    path.write_text(content, encoding="utf-8")
    print("Updated installer/snapdragon_ai_studio.iss")


def update_application_py():
    path = REPO_ROOT / "app" / "application.py"
    content = path.read_text(encoding="utf-8")

    old_title = "        self.root.title(version.APP_NAME)"
    new_title = '        self.root.title(f"{version.APP_NAME} {version.VERSION} – {version.CODENAME}")'
    if old_title not in content:
        old_title = old_title.replace('\n', '\r\n')
        new_title = new_title.replace('\n', '\r\n')
    assert old_title in content, "old_title not found in app/application.py"
    content = content.replace(old_title, new_title, 1)

    path.write_text(content, encoding="utf-8")
    print("Updated app/application.py")


def update_changelog():
    path = REPO_ROOT / "GOVERNANCE" / "CHANGELOG.md"
    content = path.read_text(encoding="utf-8")

    entry = """## [2.1.0] – 2026-11-07 (HK NPU STUDIO 2.1.0 – Phoenix Evolution)

### Versionsumstellung & Produkt-Branding
- **Produktversion**: Offizieller Übergang von RC4 auf **HK NPU STUDIO 2.1.0 – Phoenix Evolution**.
- **Zentrale Versionsdefinition**:
  - `release.json`: `display_version`: "2.1.0", `package_version`: "2.1.0", `codename`: "Phoenix Evolution", `build`: "2026.11.07".
  - `engine/brand_manager.py`: Zentrale Bereitstellung von `APP_VERSION` ("2.1.0"), `CODENAME` ("Phoenix Evolution") und `PRODUCT_FULL_NAME` ("HK NPU STUDIO 2.1.0 – Phoenix Evolution").
  - `version.py`: Vollständige Synchronisation von `APP_NAME`, `VERSION`, `PACKAGE_VERSION`, `CODENAME` und `BUILD`.
  - `build/release/version_info.txt`: Windows PE Version 2.1.0.0, FileDescription/ProductName auf Phoenix Evolution aktualisiert.
- **Benutzeroberfläche (UI)**:
  - Header oben rechts: Aktualisiert auf `2.1.0` (Akzentfarbe) und `Phoenix Evolution` (Muted), 100% Theme-Parität in Dark und Light.
  - Hauptfenstertitel: `HK NPU STUDIO 2.1.0 – Phoenix Evolution`.
  - About-Dialog & System-Info: Konsistente Anzeige von Version 2.1.0 und Phoenix Evolution.
  - Home-View: Projektstatus-Metrik zeigt Version 2.1.0.
- **Installer-Konfiguration**:
  - `installer/snapdragon_ai_studio.iss`: Zielname `HKNPUStudio-2.1.0-ARM64-Setup.exe`.
  - `AppVerName`: `HK NPU STUDIO 2.1.0 – Phoenix Evolution`.
  - Sprachdateien (DE, EN, ES): Willkommens- und Abschlussseiten auf 2.1.0 – Phoenix Evolution aktualisiert.
  - NPU-Hardwareprüfung (`InitializeSetup`), Pfadstruktur (`{localappdata}\\Programs\\HK NPU STUDIO`) und QNN-Runtime-Paketierung vollständig geschützt.

"""
    marker = "## [Sprint 108] – 2026-11-05"
    assert marker in content, "marker not found in CHANGELOG.md"
    content = content.replace(marker, entry + marker, 1)

    path.write_text(content, encoding="utf-8")
    print("Updated GOVERNANCE/CHANGELOG.md")


if __name__ == "__main__":
    update_brand_manager()
    update_header()
    update_version_info()
    update_installer_iss()
    update_application_py()
    update_changelog()
    print("All version updates successfully applied.")
