# Release Prep – 2.0 RC4

Stand: 25.10.2026

## Vorbereitung des Release-Kandidaten 2.0 RC4

Dieses Dokument beschreibt die Release-Vorbereitungs- und Prüfschritte für den geplanten Release Candidate **HK NPU STUDIO 2.0 RC4**.

### Ausgangsbasis
* **Repository-Zweig:** `integration_20261024`
* **Verbindlicher Ausgangs-HEAD:** `be0f1b5fe12fce24721f822d4a5a326e8a9664ad`
* **Geplante Paketversion:** `2.0.0-rc.4`
* **Zielarchitektur:** Windows 11 ARM64 (`arm64`)

> **Wichtiger Hinweis zu Artefakten und Hashes:**
> In diesem reinen Dokumentationssprint erfolgt **keine** Neuerstellung der Build-Artefakte. Für RC4 werden vorab keine Prüfsummen oder Dateigrößen erfunden. Die vorhandenen Dateien `release.json` und `dist/release-artifacts.json` verbleiben im unveränderten Zustand des bestehenden RC3-Builds, bis der offizielle RC4-Build-Schritt separat autorisiert und ausgeführt wird.

---

## Vorgesehene Build- und Packaging-Schritte für RC4

1. **Syntax- und Strukturprüfung:**
   ```powershell
   python -m py_compile tools/build_app.py tools/build_installer.py tools/build_release_prep.py tools/validate_release_artifacts.py
   python -m pytest tests/test_release_packaging.py
   ```
2. **App-Build (PyInstaller ARM64):**
   ```powershell
   python tools/build_app.py
   ```
   *Zielordner:* `dist/HKNPUStudio/` (Ausführbare Datei: `HKNPUStudio.exe`)
3. **Installer-Build (Inno Setup 6 / ISCC):**
   ```powershell
   python tools/build_installer.py
   ```
   *Zielordner:* `dist/installer/`
4. **Artefaktvalidierung:**
   ```powershell
   python tools/validate_release_artifacts.py
   ```
   *Ausgabe:* Erzeugung des aktuellen `dist/release-artifacts.json` mit tatsächlichen Byte-Größen und SHA-256-Prüfsummen.

---

## Historische Referenz: RC3-Build-Artefakte

Die im vorherigen Integrationslauf erzeugten und verifizierten RC3-Artefakte dienen als direkte Referenz:

* **Executable:** `dist/HKNPUStudio/HKNPUStudio.exe`
  * Dateigröße: `79.211.722` Byte
  * SHA-256: `54e62e7e374ca940bec4270ee521efdf1dd9981dffd15eba465a505d1a12d7f4`
* **Installer:** `dist/installer/HKNPUStudio-2.0.0-rc.3-ARM64-Setup.exe`
  * Dateigröße: `2.049.325.309` Byte
  * SHA-256: `18e974deb98d50149d1b4f97f4e9c5a4f6ffd9d5951b37dbcd8f0ca7af539c6b`

---

## Qualitäts- und Abnahmegates für RC4

* **Sicherheit:** Staging-Verzeichnis `dist/HKNPUStudio/output` darf vor Installer-Kompilierung nicht existieren.
* **Packaging-Gate:** Installer-Größe muss unter dem GitHub-Limit (`2.147.483.648` Byte) sowie der internen Sicherheitsgrenze (`2.100.000.000` Byte) bleiben.
* **RC2CleanTest:** Vor Veröffentlichung sind folgende Kernprüfungen auf dem Testsystem nachzuweisen:
  1. Fehlerfreier Start der Anwendung.
  2. Persistenz von Prompt und Negative Prompt nach Anwendungsneustart (Schema v3).
  3. Erfolgreiche Batch-Generierung mit Aufnahme aller Einzelergebnisse in die Galerie.
* **Code-Signatur:** Das Manifest weist `"signed": false` aus; Tester sind über den Windows SmartScreen-Hinweis für unsignierte Vorabversionen zu informieren.
