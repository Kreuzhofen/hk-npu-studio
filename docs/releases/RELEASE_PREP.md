# Release Prep – 2.0 RC1

Stand: 29.07.2026

## Erzeugte Artefakte

* `dist/SnapdragonAIStudio/` – native Windows-ARM64-Anwendung
* `dist/installer/SnapdragonAIStudio-2.0.0-rc.1-ARM64-Setup.exe`
* `dist/release-artifacts.json` – Größen und SHA-256-Prüfsummen

## Lokale Validierung

* Programmdatei: PE-Maschine `0xAA64`, Version `2.0.0-rc.1`
* Portable Diagnoseprüfung: Exitcode 0
* Unbeaufsichtigte Installation: Exitcode 0
* Diagnoseprüfung aus der Installation: Exitcode 0
* Unbeaufsichtigte Deinstallation: Exitcode 0
* Keine Laufzeitlogs, lokalen Modellpfade oder Python-Cachedateien im Paket
* Gesamttest: 248 Tests und 23 Subtests erfolgreich; Produktcode kompiliert

## SHA-256

* `SnapdragonAIStudio.exe`: `e59bf1232eac936fe06e77989052cf5666eea97ead687cec8c4d3100c7924c05`
* Installer: `2a7c4370a89aa07ae2587bfd72552041346ed064fc11d3dd9ba282309b30a5cd`

## Noch erforderlich

* Authenticode-Signierung mit einem gültigen Code-Signing-Zertifikat
* Signierte Artefakte erneut hashen und validieren
* Veröffentlichung nach separater Freigabe
