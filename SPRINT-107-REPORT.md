# HK NPU STUDIO – SPRINT 107 REPORT
## ARM64 Installer, Installation & Uninstall Validation

**Tool:** Antigravity (Senior Software Engineer)  
**Datum:** 2026-11-05  
**Plattform:** Windows 11 ARM64 (Qualcomm Snapdragon X Elite / Hexagon HTP V73)  
**Status:** ERFOLGREICH ABGESCHLOSSEN (100% Gates erfüllt)  
**Referenz-Dokument:** [SPRINT_107_INSTALLER_VALIDATION_REPORT.md](file:///C:/SnapdragonAI/reports/sprint_107_installer_validation/SPRINT_107_INSTALLER_VALIDATION_REPORT.md)

---

## 1. Übersicht & Zielerreichung

Im Rahmen von Sprint 107 wurde das in Sprint 106 verifizierte Standalone-Bundle (`dist/HKNPUStudio`, 6.084 Dateien, 717,78 MB) zu einem nativen, kommerziell ausgereiften Windows 11 ARM64 Installer (`HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe`) paketiert und einem lückenlosen Lifecycle-Audit unterzogen.

| Kriterium | Vorgabe | Ergebnis | Status |
| :--- | :--- | :--- | :--- |
| **Inno Setup ARM64 Installer** | Native Kompilierung für AArch64 | `HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe` (264,41 MB) | **ERFÜLLT** |
| **Komprimierungsrate** | LZMA2 Solid Compression | **63,16% Einsparung** gegenüber 717,8 MB Payload | **ERFÜLLT** |
| **Rechte-Modell** | `PrivilegesRequired=lowest` | Standard-Benutzerkonto, **0 UAC-Prompts**, keine Adminrechte | **ERFÜLLT** |
| **Hardware Pre-Flight Check** | Prüfung auf Qualcomm FastRPC vor Extraktion | `InitializeSetup()` prüft `Services\qcadsprpc`; Abbruch bei Fremd-CPU | **ERFÜLLT** |
| **Treiber-DLL & Signatur** | Klärung Herkunft `libcdsprpc.dll` | Microsoft DriverStore, Microsoft Authenticode signiert | **ERFÜLLT** |
| **HTP V73 Laufzeit-Inferenz** | MobileSAM-Inferenz auf NPU | `QNNExecutionProvider`, `disable_cpu_ep_fallback: 1`, **0 CPU-Fallbacks** | **ERFÜLLT** |
| **MobileSAM Pixel-Präzision** | Exakte Segmentierungsmaske | **20.220 Pixel** (100% numerische Ground-Truth Parität) | **ERFÜLLT** |
| **Pfad- & Daten-Isolation** | Trennung Binary vs. State | Binary: `{localappdata}\Programs` · State: `{localappdata}\HK NPU STUDIO` | **ERFÜLLT** |
| **In-Place Upgrade** | Aktualisierung bestehender Installation | 106,16s, 0 File-Lock Konflikte, Benutzerzustand unberührt | **ERFÜLLT** |
| **Sichere Deinstallation** | Löschen der App ohne Datenverlust | `unins000.exe` löscht `{app}`, **User-Modelle/Logs 100% erhalten** | **ERFÜLLT** |

---

## 2. Detaillierte Audit-Ergebnisse

### 2.1 Hardware Pre-Flight & Treiber-Herkunft
1. **Qualcomm FastRPC Registry Service:**  
   Inno Setup führt in `InitializeSetup()` eine Prüfung des Schlüssels `HKLM\SYSTEM\CurrentControlSet\Services\qcadsprpc` durch. Dieser Schlüssel ist unter Windows NT standardmäßig für jeden nicht privilegierten Benutzer lesbar. Wird der Dienst nicht vorgefunden (z. B. auf Intel/AMD x64 oder fremden ARM-Systemen), wird ein lokalisierter kritischer Fehlerdialog (DE/EN/ES) angezeigt und das Setup ohne Schreibzugriffe beendet.
2. **`libcdsprpc.dll` Provenienz:**  
   Die Datei stammt aus dem signierten Treiberpaket `qcadsprpc8380.inf_arm64_92990f4e56566bee` im Windows DriverStore (`C:\Windows\System32\DriverStore\FileRepository\`). Sie trägt eine gültige Authenticode-Katalogschnittstelle von *Microsoft Windows Hardware Compatibility Publisher*. Das Bündeln in `_internal` ermöglicht das dynamische Laden durch `QnnHtpV73Stub.dll` via `os.add_dll_directory`, ohne Systempfade zu manipulieren oder Administrationsrechte zu fordern.

### 2.2 Installation & Laufzeit-Inferenz
1. **Erstinstallation:**  
   In 105,16s wurden 6.086 Dateien (6.084 Anwendungsdateien + Deinstallationsroutinen) in das isolierte Verzeichnis `Programs\HK NPU STUDIO` entpackt.
2. **NPU-Inferenz:**  
   Der Aufruf von `HKNPUStudio.exe --validate-standalone` lieferte folgendes Audit-JSON:
   - `selected_backend`: `"QNNExecutionProvider"`
   - `sam_htp_active`: `true`
   - `cpu_fallback_count`: `0`
   - `disable_cpu_ep_fallback`: `1`
   - `active_pixels`: `20220`
   - `config_user_base`: `C:\Users\holge\AppData\Local\HK NPU STUDIO`
   - `logs`: `C:\Users\holge\AppData\Local\HK NPU STUDIO\logs\hk_npu_studio.log` (3,64 MB)

### 2.3 Upgrade & Deinstallations-Sicherheit
1. **Upgrade-Test:**  
   Erneute Ausführung des Setups über die bestehende Testinstallation verlief reibungslos (106,16s), ersetzte die Binärdateien sauber und ließ den Canary-Marker intakt.
2. **Deinstallations-Test:**  
   Der Aufruf von `unins000.exe /VERYSILENT` entfernte die Anwendungsdateien in `{app}` in 14,71s vollständig. Die im Benutzerverzeichnis hinterlegten Checkpoints (`models/user_custom_checkpoint_sprint107.bin`), Präferenzen (`data/preferences.json`) und Logdateien blieben zu **100% unangetastet**.

---

## 3. SHA-256 Manifest

| Komponente | Datei | SHA-256 |
| :--- | :--- | :--- |
| **ARM64 Installer** | `HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe` | `eb56b374d1f28c6a3b48e020d0244a8d6d5f9593fb8a6187039aa2c229df4cba` |
| **Hauptprogramm** | `HKNPUStudio.exe` | `489b068963e8d089c344c53658632702a2e08e7a26806edf53e4603d928cdd8b` |
| **Release Meta** | `release.json` | `4642bba2e55c44e88845da6123ea9cc65cf8b3de8e7988d0c30995208c2bd70d` |
| **FastRPC Stub** | `_internal/libcdsprpc.dll` | `ff431f8ad2f279a9caf75e07d589984359d37769514a33d5f6130d1268e1f6fe` |
| **QNN HTP DLL** | `_internal/onnxruntime_qnn/QnnHtp.dll` | `87e99b434e949af79fb907ff539f40e8d79bb92eb7de6a308866576b3735830e` |
| **HTP V73 Skel** | `_internal/onnxruntime_qnn/libQnnHtpV73Skel.so` | `b5084469a693b05e372eedf8861e29e92c6e012c1cf543144c894f6141a5348f` |

---

## 4. Visuelle Nachweise & Dashboard

Alle Grafiken liegen hochauflösend im Repository vor:
- [Card 1: Architektur & Rechte-Modell](file:///C:/SnapdragonAI/reports/sprint_107_installer_validation/images/card1_installer_architecture_and_security.png)
- [Card 2: Hardware Pre-Flight & FastRPC](file:///C:/SnapdragonAI/reports/sprint_107_installer_validation/images/card2_hardware_preflight_and_driver_binding.png)
- [Card 3: Lifecycle, Upgrade & Deinstallation](file:///C:/SnapdragonAI/reports/sprint_107_installer_validation/images/card3_install_upgrade_uninstall_lifecycle.png)
- [Master Audit Dashboard](file:///C:/SnapdragonAI/reports/sprint_107_installer_validation/images/sprint107_installer_validation_dashboard.png)

---

## 5. Hard Stop & Ausblick

- **HARD STOP eingehalten:** Kein Git-Commit, kein Push, keine externe Veröffentlichung ohne Freigabe.
- Der Installer liegt als internes, verifiziertes Testartefakt unter `dist/installer/` bereit.
