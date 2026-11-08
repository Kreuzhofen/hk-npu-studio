# IMG-EDIT-IMPL-44 – Adaptive Reference Control

**Projekt:** HK NPU STUDIO  
**Codename:** Phoenix Architecture  
**Hardware-Zielplattform:** Qualcomm Snapdragon X Elite (Hexagon HTP V73 NPU)  
**Rolle:** Senior Software Engineer (Gemini)  
**Datum:** 2026-11-01  
**Status:** Erfolgreich abgeschlossen (100% Definition of Done)

---

## 1. Executive Summary & Zielsetzung

Mit **IMG-EDIT-IMPL-44** wurde die Referenzbild-Steuerung in Image-to-Image von einer rein technischen Parameter-Ebene in eine intuitive, professionelle und verständliche **Adaptive Referenzsteuerung** überführt. Basierend auf den empirischen Benchmark-Ergebnissen aus Sprint 43 unterscheidet die Anwendung nun klar zwischen zwei spezialisierten Steuerungsmodi mit jeweils optimal kalibrierter Standard-Bindungsstärke:

- **Modus A – Konturtreue (ControlNet Canny QNN):**  
  Optimiert für **Architektur, Logos, CAD, Gegenstände und geometrische Motive**.  
  Standard-Fidelity: **`0.75`** (nutzt 13 HTP-Residuals auf spezialisiertem UNet für maximale Kantenschärfe).
- **Modus B – Strukturtreue (Decaying Latent Anchor):**  
  Optimiert für **Porträts, Landschaften, organische Motive und natürliche Beleuchtung**.  
  Standard-Fidelity: **`0.65`** (0 MB Zusatzgewichte, rein schedulerbasiert im latenten Raum, ~2.3 Sekunden schneller).

Alle Modi und Stärken sind jederzeit manuell anpassbar. Es findet **keine automatische Modusumschaltung ohne ausdrückliche Nutzerinteraktion** statt. Die Denoising-Presets aus Sprint 40 (0.30 / 0.45 / 0.65 / 0.80 / 1.00) bleiben vollständig erhalten.

---

## 2. Sicherheits-Gate & Backup-Verifikation

Vor Beginn der Implementierung wurden alle Governance- und Integritätsregeln geprüft:

1. **Git-Status & HEAD:**
   - Commit HEAD: `8784a43f5b7666f1007292393c6ea947b5cdd788`
   - Git-Status: Ausschließlich Sprint-Artefakte und autorisierte Handover-Dateien. Keine unerlaubten Git-Commits oder Pushes.
2. **Drive D: Verfügbarkeit:**
   - Partition `D:\` mit über 39 GB freiem Speicherplatz verifiziert.
3. **Pre-Backup:**
   - Pfad: `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_44_PRE_20261101`
   - 12 Projektdateien vollständig gesichert und zu 100% über SHA-256 verifiziert (`PRE_BACKUP_SHA256_MANIFEST.json`).
4. **Post-Backup:**
   - Pfad: `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_44_POST_20261101`
   - 19 Projektdateien, Testartefakte, generierte Bilder, Sidecars und Visualisierungs-Grids gesichert.
   - Alle 19 SHA-256 Prüfsummen zu 100% bitidentisch validiert (`POST_BACKUP_SHA256_MANIFEST.json`).

---

## 3. Architektur & UI-Implementierung

### 3.1 Verständliche Modusauswahl mit `PhoenixButton`
Anstelle unübersichtlicher Radiobuttons wurde die Modusauswahl als prominente Segment-Auswahl realisiert:

- **Button A (`btn_mode_contour`):** `A · Konturtreue (Canny QNN)`  
  Aktiv (`button_type="secondary"`), Inaktiv (`button_type="neutral"`).
- **Button B (`btn_mode_structure`):** `B · Strukturtreue (Latent Anchor)`  
  Aktiv (`button_type="secondary"`), Inaktiv (`button_type="neutral"`).

### 3.2 Kontextuelle Empfehlungs- & Informationstafel
Direkt unterhalb der Modusauswahl informiert ein dynamisches Panel (`ref_mode_desc_frame`, `PHOENIX_THEME.elevated_bg`) den Anwender über empfohlene Einsatzbereiche und technische Kenndaten:

- **Bei Modus A:**
  - *Titel:* `✔ Architektur · Logos · CAD · Gegenstände · Geometrie`
  - *Detail:* `Standard-Fidelity: 0.75 | Qualcomm Hexagon ControlNet (13 Residuals)`
- **Bei Modus B:**
  - *Titel:* `✔ Porträts · Landschaften · Organische Motive · Beleuchtung`
  - *Detail:* `Standard-Fidelity: 0.65 | Latent Anchor (0 MB Zusatzgewichte, +14% Tempo)`

### 3.3 Automatische Kalibrierung & Manuelle Feineinstellung
- Bei Klick auf einen Modus-Button (`select_reference_mode`) passt die UI die Bindungsstärke automatisch auf den empfohlenen Benchmark-Standard an (`0.75` für Modus A, `0.65` für Modus B).
- Die Bindungsstärke bleibt über den horizontalen Schieberegler und die Spinbox (Bereich `0.10` bis `1.50`, Schrittweite `0.05`) jederzeit frei justierbar.
- Über den neuen Button **`Standard (0.75)`** bzw. **`Standard (0.65)`** (`btn_fidelity_default`) kann die empfohlene Kalibrierung des aktiven Modus mit einem Klick wiederhergestellt werden.

### 3.4 Strikte Nutzerautonomie ("Keine automatische Umschaltung")
- Das Laden eines neuen Bildes oder das Eingeben von Prompts (selbst mit Schlüsselwörtern wie "Face", "Cathedral" oder "Landscape") führt zu **keiner heimlichen Modusumschaltung**.
- Die Auswahl verbleibt strikt unter der Kontrolle des Benutzers.

---

## 4. Visuelle Dokumentation & HTP-Verifikation

Die folgende Vergleichsübersicht dokumentiert die beiden Modi im Zusammenspiel mit dem Originalbild auf der Qualcomm Hexagon HTP NPU:

- **Spalte 1:** Originales Eingabebild (`motif_objects.png`)
- **Spalte 2:** Modus A (Konturtreue, Canny QNN, Standard-Fidelity `0.75`)
- **Spalte 3:** Modus B (Strukturtreue, Latent Anchor, Standard-Fidelity `0.65`)

![Sprint 44 Adaptive Reference Comparison](file:///C:/Users/holge/.gemini/antigravity-cli/brain/c991b454-d253-4b5d-9ce4-469780cc4864/sprint44_adaptive_reference_comparison.png)

---

## 5. Empirische Messwerte auf Qualcomm Hexagon HTP V73

Die reale NPU-Ausführung beider Modi wurde über `tools/verify_adaptive_reference_control_sprint44.py` verifiziert:

| Messgröße | Modus A – Konturtreue (Canny QNN) | Modus B – Strukturtreue (Latent Anchor) | Delta / Vorteil |
|---|---|---|---|
| **Einsatzbereich** | Architektur, CAD, Logos, Geometrie | Porträts, Landschaften, Organik | Aufgabenspezifisch |
| **Standard-Fidelity** | **`0.75`** | **`0.65`** | Empirischer Sweet Spot |
| **HTP VAE Encoder** | 7,040.0 ms | 7,136.9 ms | Gleichstand |
| **HTP CLIP Text** | 26.3 ms | 24.7 ms | Gleichstand |
| **HTP ControlNet Pass** | **2,085.8 ms** (13 Residuals) | **0.0 ms** (Kein Modell) | Anchor benötigt 0 ms |
| **HTP UNet Schrittzeit** | 720.5 ms / Schritt | 677.4 ms / Schritt | Anchor 43 ms schneller |
| **HTP VAE Decoder** | 880.1 ms | 781.4 ms | Gleichstand |
| **Gesamte Inferenzzeit** | **15,796.3 ms** (~15.8 s) | **13,362.2 ms** (~13.4 s) | **Anchor 2.43 s schneller** |
| **CPU-Fallback** | **0.00 ms** (100% HTP) | **0.00 ms** (100% HTP) | NPU-First Garantie |
| **Zusätzlicher Modell-VRAM** | ~369 MB Context | **0 MB** | 0 Byte Zusatzspeicher |

---

## 6. Qualitätssicherung & Testprotokoll

1. **UI- & Interaktionstests:**
   - Datei: [`tests/test_phoenix_image_to_image_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_image_to_image_ui.py)
   - Ergebnis: **14/14 Tests erfolgreich** (inkl. neuer Tests für Moduswahl, Standard-Fidelity, Reset-Button, Preset-Erhalt und Nutzerautonomie).
2. **Navigationstests:**
   - Datei: [`tests/test_phoenix_image_lab_navigation.py`](file:///C:/SnapdragonAI/tests/test_phoenix_image_lab_navigation.py)
   - Ergebnis: **7/7 Tests erfolgreich**.
3. **Inpainting-Regressionstests:**
   - Datei: [`tests/test_phoenix_inpainting_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_inpainting_ui.py)
   - Ergebnis: **50/50 Tests erfolgreich**.
4. **Theme-Parität:**
   - Erfolgreich validiert für **Dark Mode** und **Light Mode** über `test_adaptive_reference_theme_parity`.
   - Alle dynamischen Panels, Buttons und Schriften passen sich ohne Layoutbrüche an das Farbschema an.
5. **Syntaxprüfung:**
   - Alle modifizierten Python-Dateien kompilieren mit `python -m py_compile` fehlerfrei (Exit Code 0).

---

## 7. Definition of Done (DoD) Verifikation

| Anforderung | Status | Nachweis |
|---|---|---|
| **Verständliche Modusauswahl** | Erfüllt | Modus A (Konturtreue) und Modus B (Strukturtreue) mit Beschreibungsbox |
| **Standard-Fidelity Kalibrierung** | Erfüllt | Modus A: 0.75, Modus B: 0.65; wiederherstellbar via Reset-Button |
| **Nutzerautonomie** | Erfüllt | Keine heimliche Modusumschaltung bei Bild- oder Promptwechsel |
| **Denoising-Presets unverändert** | Erfüllt | 0.30, 0.45, 0.65, 0.80, 1.00 vollständig intakt |
| **Theme-Parität & PHOENIX_THEME** | Erfüllt | PhoenixButtons, card_bg, elevated_bg in Dark & Light geprüft |
| **0.00 ms CPU-Fallback** | Erfüllt | Beide Modi auf Qualcomm Hexagon HTP V73 empirisch gemessen |
| **Inpainting & T2I unangetastet** | Erfüllt | Alle 50 Inpainting-Tests fehlerfrei, T2I unverändert |
| **Post-Backup mit SHA-256** | Erfüllt | 19 Dateien auf Drive D: gesichert (`POST_BACKUP_SHA256_MANIFEST.json`) |
