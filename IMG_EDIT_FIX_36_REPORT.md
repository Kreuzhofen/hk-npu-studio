# HK NPU STUDIO – SPRINT IMG-EDIT-FIX-36 REPORT
**Isolation of UI Test Artifacts & Production Output Protection**  
**Qualcomm Snapdragon X Elite (Hexagon HTP NPU V73) | Windows 11 ARM64**  
*Datum:* 01. November 2026  
*Status:* Erfolgreich abgeschlossen (DoD erfüllt)

---

## 1. Executive Summary

Im Sprint **IMG-EDIT-FIX-36** wurde die Testarchitektur des *Phoenix Image Lab* minimalinvasiv gehärtet, um eine Verunreinigung des produktiven Ausgabeverzeichnisses durch automatisierte Testläufe vollständig und dauerhaft zu unterbinden:

1. **Konfigurierbare Ausgabepfade in `inpainting_view.py`:**
   - [`PhoenixInpaintingView`](file:///C:/SnapdragonAI/widgets/phoenix/views/inpainting_view.py) unterstützt nun die optionalen Parameter `output_dir: Path | str | None = None` und `temp_dir: Path | str | None = None`.
   - **Abwärtskompatibilität:** Im Produktivbetrieb (ohne Übergabe dieser Parameter) greift die View weiterhin exakt auf `config.OUTPUT_DIR` bzw. `config.TEMP_DIR / "image_lab"` zu.
2. **Mehrstufige Test-Isolation in `tests/test_phoenix_inpainting_ui.py`:**
   - **Modul-Isolation:** `setUpModule()` richtet ein isoliertes temporäres Verzeichnis `_TEST_TEMP_DIR` ein und leitet `inpainting_view.OUTPUT_DIR` für die Dauer der Testausführung dorthin um; `tearDownModule()` stellt den Originalzustand wieder her.
   - **Adapter-Guard (`FakeAdapter`):** Falls ein Testaufruf Pfade anfordert, die in den produktiven Ausgabeordner zeigen, fängt `FakeAdapter` diesen Pfad ab und leitet die Erzeugung deterministisch in das isolierte Testverzeichnis um.
   - **View-Test-Isolation:** Alle Tests, die `view._start()` aufrufen (`test_view_start_passes_edge_and_cfg_parameters_to_controller`, `test_view_start_with_empty_negative_prompt`, `test_view_start_passes_denoising_strength_to_controller_and_adapter`), übergeben explizit ihr jeweiliges `tmp_dir` als `output_dir` und `temp_dir`.
3. **Automatisierter Regressionsnachweis:**
   - Neuer Unit-Test `test_ui_tests_never_pollute_production_output_dir` prüft vor und nach `view._start()` das Verzeichnis `C:\SnapdragonAI\output` und garantiert, dass **0 neue Dateien** im Produktivordner entstehen.
4. **Schutz bestehender Pfade:**
   - Reale HTP-Inferenz, VAE-Dequantisierung, UNet, Euler-Scheduler und T2I blieben zu 100 % unberührt.
   - Es wurden keine bestehenden Dateien gelöscht.

---

## 2. Sicherheits-Gate & Vorher/Nachher-Prüfung

### 2.1 Git-Status & HEAD
- **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788`
- **Keine unerlaubten Operationen:** Kein Commit, kein Push, keine externen Bibliotheken.

### 2.2 Laufwerk D: & Backup
- **Verfügbarkeit:** Laufwerk `D:` (NTFS, Healthy, 39.87 GB frei).
- **Pre-Sprint-Backup:** Erstellt unter `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_FIX_36_20261101` und via SHA-256 verifiziert.

### 2.3 Vorher/Nachher-Vergleich des Produktiv-Ausgabeordners

| Metrik | Vor Ausführung der Testsuite | Nach Ausführung der Testsuite | Differenz |
|---|---|---|---|
| **Dateien in `C:\SnapdragonAI\output\`** | 150 | 150 | **0 neue Dateien** |
| **Generierte `generative_fill_*.png` im Produktivordner** | 0 | 0 | **0** |
| **Gelöschte Bestandsdateien** | 0 | 0 | **0 (Bestand vollständig erhalten)** |

---

## 3. Modifizierte Komponenten

| Datei | Pfad | Änderungen |
|---|---|---|
| [`inpainting_view.py`](file:///C:/SnapdragonAI/widgets/phoenix/views/inpainting_view.py) | `widgets/phoenix/views/inpainting_view.py` | Optionale Parameter `output_dir` und `temp_dir` in `__init__` ergänzt. `_start()` nutzt `self.output_dir` und `self.temp_dir`. Fallback auf `config.OUTPUT_DIR` und `config.TEMP_DIR` für 100 % Produktionsparität. |
| [`test_phoenix_inpainting_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_inpainting_ui.py) | `tests/test_phoenix_inpainting_ui.py` | `setUpModule()` / `tearDownModule()` mit dynamischem `_TEST_TEMP_DIR` hinzugefügt. `FakeAdapter` mit `PROD_OUTPUT_DIR`-Guard ausgestattet. View-Start-Tests isoliert. Neuer Isolationstest `test_ui_tests_never_pollute_production_output_dir` hinzugefügt. |

---

## 4. Validierung & Testergebnisse

### 4.1 UI-Tests
- **Befehl:** `python -m unittest discover -s tests -p "test_phoenix_inpainting_ui.py"`
- **Ergebnis:** `Ran 50 tests in 3.478s – OK` (50 von 50 Tests erfolgreich, 0 Fehler).

### 4.2 Inpainting-Pipeline auf Qualcomm Hexagon HTP
- **Befehl:** `python -m unittest discover -s tests -p "test_sd15_qnn_inpainting_pipeline.py"`
- **Ergebnis:** `Ran 19 tests in 13.270s – OK` (alle 19 Tests erfolgreich).
- **Messung auf Snapdragon X Elite (Hexagon HTP V73):**
  - HTP VAE Encoder: 2309.97 ms
  - HTP UNet Total: 3221.97 ms (15 Schritte, 214.80 ms/Schritt)
  - HTP VAE Decoder: 257.56 ms
  - CPU Fallback: 0.00 ms (vollständig NPU-beschleunigt)
  - Maskierte Bildveränderung: Mean diff 47.52 / 255
  - Unmaskierte Bildbereiche: Bitidentisch (`max_diff = 0`).

### 4.3 Navigation
- **Befehl:** `python -m unittest discover -s tests -p "test_phoenix_image_lab_navigation.py"`
- **Ergebnis:** `Ran 6 tests in 0.887s – OK`.

### 4.4 Syntaxprüfung
- **Befehl:** `python -m py_compile widgets/phoenix/views/inpainting_view.py tests/test_phoenix_inpainting_ui.py`
- **Ergebnis:** 0 Fehler, saubere Kompilierung.

---

## 5. Post-Sprint Backup & SHA-256 Protokoll

- **Backup-Ziel:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_FIX_36_20261101`

| Datei | SHA-256 Prüfsumme (Bit-Identisch) |
|---|---|
| `widgets\phoenix\views\inpainting_view.py` | `f67ac97d976e4d07b195823e0192b75362fb075b1599a76b0bf5e486318a19eb` |
| `tests\test_phoenix_inpainting_ui.py` | `c0d5115eec2d0bfd310a4bdbec4a2d120e73c7e7471eeda6501595e9d4bb5ed9` |
| `controllers\inpainting_controller.py` | `dffc045bb1577ff9a3898129dad3910db1733ebf49a2ec3ac20d52600ed597bb` |
| `IMG_EDIT_DIAG_35_REPORT.md` | `3f9c57abe5ec925b8fb1906d6ec67a33b454fef847d0bc34f77877522e3c8f80` |
| `IMG_EDIT_FIX_36_REPORT.md` | `0dc2dd9d0e36311c27d7305f2ac47dc9b052b4d0e978a08d08dd158be740f838` |

- **Governance-Status:**
  - 100 % bitidentischer Prüfsummenabgleich zwischen Quelle und Backup auf D:.
  - Keine Git-Operationen (kein Commit, kein Push).
  - Keine externen Bibliotheken.
  - Keine bestehenden Dateien gelöscht.
