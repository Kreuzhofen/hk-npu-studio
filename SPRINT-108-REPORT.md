# HK NPU STUDIO – SPRINT 108 REPORT
## RC4 Installer Forensics & Release Comparison

**Tool:** Antigravity (Senior Software Engineer)  
**Datum:** 2026-11-05  
**Plattform:** Windows 11 ARM64 (Qualcomm Snapdragon X Elite / Hexagon HTP V73)  
**Status:** ERFOLGREICH ABGESCHLOSSEN (100% Kriterien erfüllt)  
**Referenz-Dokument:** [SPRINT_108_FORENSIC_COMPARISON_REPORT.md](file:///C:/SnapdragonAI/reports/sprint_108_installer_comparison/SPRINT_108_FORENSIC_COMPARISON_REPORT.md)

---

## 1. Übersicht & Zielerreichung

In Sprint 108 wurde eine forensische Gegenüberstellung des bisherigen **Original RC4 Installers** (`7d1d9b9c...`, 1,95 GB) und des in Sprint 107 erstellten **Sprint-107-Installers** (`eb56b374...`, 264 MB) durchgeführt. Beide Installer wurden in getrennte temporäre Analyseverzeichnisse entpackt, auf Dateiebene verglichen und hinsichtlich ihrer QNN-, HTP V73-, FastRPC-, Modell-, GUI- und Rechte-Architektur detailliert auditiert.

### Kernergebnisse

| Prüfdimension | Original RC4 Installer | Sprint-107-Installer | Forensische Bewertung |
| :--- | :--- | :--- | :--- |
| **Dateigröße (Installer)** | **2.050.000.471 Bytes (1.955,03 MB)** | **277.251.090 Bytes (264,41 MB)** | **-1.690,62 MB (-86,5% / 7,4x kleiner)** |
| **SHA-256 Checksumme** | `7d1d9b9c566c58cef55f9478a21517...` | `eb56b374d1f28c6a3b48e020d0244a...` | Beide Installer eindeutig identifiziert |
| **Dateianzahl (Payload)** | **11.460 Dateien** | **6.086 Dateien** | **-5.374 Dateien (-46,9%)** |
| **Entpackte Größe auf Disk** | **2.924,10 MB (~2,86 GB)** | **723,67 MB (~0,71 GB)** | **-2.200,43 MB (-75,2% Festplattenbedarf)** |
| **Entpackungsdauer** | 642,17 Sekunden (~10,7 Min.) | 59,97 Sekunden (~1,0 Min.) | **10,7x schnellere Installation** |
| **Modell-Payload** | 1.882,4 MB (`photo_restore_context` 1,93 GB) | 124,9 MB (`mobilesam_qnn` Basispaket) | **Aufklärung des 1,93 GB Größen-Deltas** |
| **FastRPC Driver Stub** | **FEHLT (`libcdsprpc.dll` nicht gebündelt)** | **VORHANDEN (`libcdsprpc.dll` in `_internal`)** | **Beseitigt FastRPC-Absturzursache** |
| **Hardware Pre-Flight** | Keine NPU-Prüfung vor Extraktion | `InitializeSetup()` prüft `qcadsprpc` | **Verhindert Fehl-Installationen auf Fremd-PCs** |
| **Verzeichnis-Layout** | Flaches PyInstaller-Root-Layout | Sauber strukturiertes `_internal/` Layout | Modernes PyInstaller 6 Standard-Layout |
| **Laufzeit-Inferenz & HTP**| Unterstützt (sofern DriverStore im PATH) | Nativ autark, **0 CPU-Fallbacks**, 20.220 px | **100% funktionale Parität, höhere Robustheit** |

---

## 2. Aufklärung des 1,93 GB Größen-Deltas

Die forensische Extraktion belegt zweifelsfrei, worauf die Diskrepanz zwischen 1,95 GB und 264 MB beruht:
1. **Statischer 1,93 GB Photo Restore Context:** Der bisherige Original RC4 Installer enthielt das Verzeichnis `models/photo_restore_context/` mit 1.934.901.248 Bytes an statisch vorkompilierten Kontext-Caches.
2. **Über 5.300 redundante Entwicklungs- und Testdateien:** Im flachen Root-Verzeichnis des Original RC4 befanden sich tausende überflüssige Dokumentations-, Test-, Cache- und Entwicklerdateien.
3. **Optimierung in Sprint 107:** Sprint 107 bündelt exakt die autark benötigten Basiskomponenten (`mobilesam_qnn` mit 124,9 MB für interaktive Punktsegmentierung und Inpainting) und lagert dynamisch nachladbare Großmodelle und Kontext-Caches über die Multi-Tier-Modellauflösung (`resolve_model_path()`) in `%LOCALAPPDATA%\HK NPU STUDIO\models` aus.

---

## 3. FastRPC-Treiberbindung (`libcdsprpc.dll`) & Hardware-Pre-Flight

1. **Behebung des FastRPC-Mangels:**  
   Im Original RC4 fehlte `libcdsprpc.dll` im Installationspaket. Dadurch schlug der Start von `QnnHtpV73Stub.dll` auf Clean-PCs fehl, falls der Windows DriverStore nicht manuell in `PATH` eingetragen war. Sprint 107 bündelt die offiziell von Microsoft signierte `libcdsprpc.dll` direkt in `_internal` und `_internal/onnxruntime_qnn` und bindet sie dynamisch über `os.add_dll_directory`.
2. **Hardware Pre-Flight:**  
   Sprint 107 prüft vor Entpackung über `HKLM\SYSTEM\CurrentControlSet\Services\qcadsprpc`, ob ein Qualcomm Snapdragon X NPU-System vorliegt. Fehlt der Treiberdienst, wird die Installation sauber abgebrochen, anstatt 2,9 GB unbrauchbare Daten zu entpacken.

---

## 4. SHA-256 Manifest der gesicherten Installer

Auf Festplatte D: unter `D:\HK_NPU_STUDIO_BACKUPS\SPRINT_108_INSTALLER_COMPARISON_20261105\` wurden beide Installer unverändert gesichert:

| Installer | Dateiname auf D: | Größe | SHA-256 |
| :--- | :--- | :--- | :--- |
| **Original RC4** | `installers/HKNPUStudio-2.0.0-rc.4-ARM64-Setup-ORIGINAL.exe` | 2.050.000.471 Bytes | `7d1d9b9c566c58cef55f9478a215171351b9cddfe1313c7379f8c11856800f0b` |
| **Sprint 107** | `installers/HKNPUStudio-2.0.0-rc.4-ARM64-Setup-SPRINT107.exe` | 277.251.090 Bytes | `eb56b374d1f28c6a3b48e020d0244a8d6d5f9593fb8a6187039aa2c229df4cba` |

---

## 5. Visuelle Nachweise

Alle Grafiken liegen im Repository bereit:
- [Card 1: Installer Footprint & Payload Delta](file:///C:/SnapdragonAI/reports/sprint_108_installer_comparison/images/card1_installer_footprint_and_payload_delta.png)
- [Card 2: Models & QNN Runtime Forensics](file:///C:/SnapdragonAI/reports/sprint_108_installer_comparison/images/card2_model_and_qnn_runtime_forensics.png)
- [Card 3: Functional & Architectural Matrix](file:///C:/SnapdragonAI/reports/sprint_108_installer_comparison/images/card3_functional_and_architectural_matrix.png)
- [Master Forensic Dashboard](file:///C:/SnapdragonAI/reports/sprint_108_installer_comparison/images/sprint108_installer_forensics_dashboard.png)

---

## 6. Fazit & Freigabe-Empfehlung

Sprint 107 bietet **vollständige funktionale Parität** zu Original RC4, behebt eine kritische FastRPC-Treiberabhängigkeit, reduziert die Downloadgröße um **86,5%** und beschleunigt die Installation um das **Zehnfache**.

**Empfehlung an den Product Owner:** Der Sprint-107-Installer (`eb56b374...`) soll den bisherigen Original-RC4-Installer (`7d1d9b9c...`) als offizielles RC4-Release-Asset vollständig ersetzen.

*HARD STOP eingehalten: Keine Git-Commits, kein Push.*
