# HK NPU STUDIO – IMG-EDIT-IMPL-40
## Image-to-Image Presets Integration Report
**Plattform:** Windows 11 ARM64 (Qualcomm Snapdragon X Elite, Hexagon HTP V73)  
**Datum:** 2026-11-01  
**Status:** Erfolgreich abgeschlossen (Definition of Done erfüllt)

---

## 1. Management-Zusammenfassung

Auf Basis der empirischen Qualitätsanalyse und der Benchmark-Ergebnisse aus Sprint 39 wurden im Sprint **IMG-EDIT-IMPL-40** die fünf offiziellen **Image-to-Image Presets** als verbindlicher Standard in [`PhoenixImageToImageView`](file:///C:/SnapdragonAI/widgets/phoenix/views/image_to_image_view.py) integriert.

### Die fünf verbindlichen Presets:
1. **Subtil (`0.30`):** 6 HTP-Schritte, ~11.4 s (SSIM ~0.72, L1: 9.4 / 255)  
   *Einsatz:* Rauschglättung, Detail-Finishing, subtile Glanzlichter bei 95% Motivdeckung.
2. **Moderat (`0.45`):** 9 HTP-Schritte, ~13.8 s (SSIM ~0.67, L1: 12.1 / 255)  
   *Einsatz:* Gezielter Material- und Oberflächenwechsel bei starrer Bildgeometrie.
3. **Ausgewogen (`0.65`, Standard):** 13 HTP-Schritte, ~16.0 s (SSIM ~0.62, L1: 18.3 / 255)  
   *Einsatz:* **Der Sweet Spot**: Ideale Balance aus semantischer Prompt-Transformation und Erhalt der Bildkomposition.
4. **Kreativ (`0.80`):** 16 HTP-Schritte, ~18.9 s (SSIM ~0.54, L1: 28.5 / 255)  
   *Einsatz:* Hohe Entropie, freie Variationen, exploratives Concept Art Design.
5. **Neugenerierung (`1.00`):** 20 HTP-Schritte, ~20.8 s (SSIM ~0.36, L1: 72.9 / 255)  
   *Einsatz:* Reines Text-to-Image Re-Sampling aus Gaußschem Rauschen.

### Wichtige Interaktions-Garantien:
* **Manuelle Feinjustierung:** Der stufenlose Denoising-Slider (`0.10` bis `1.00`, Schrittweite `0.05`) und die numerische Spinbox bleiben uneingeschränkt aktiv.
* **Aktives Preset-Highlighting:** Der dem aktuellen Denoising-Wert entsprechende Preset-Button wird automatisch visuell hervorgehoben (`button_type="secondary"`). Bei manuellen Zwischenwerten (z. B. `0.55`) schalten alle Preset-Buttons auf den neutralen Zustand (`button_type="neutral"`).
* **Exakte Scheduler-Schritte:** Für alle fünf Presets werden die realen HTP-Inferenzschritte deterministisch berechnet ($K = \max(1, \operatorname{round}(N \cdot s))$).
* **Theme-Parität:** Vollständige Unterstützung von Dark- und Light-Theme über `PHOENIX_THEME`.
* **Hardwarebeschleunigung:** **0,00 ms CPU-Fallback** auf Qualcomm Hexagon HTP V73.

---

## 2. Sicherheits-Gate & Pre-Backup

* **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788` (Branch `main`, sauberer Arbeitsstand)
* **Laufwerk D: Verfügbarkeit:** Vorhanden (39.86 GB freier Speicherplatz)
* **Pre-Backup Ziel:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_40_20261101`
* **Sicherungsumfang:** 24 Dateien (Controllers, Views, Engine, Locales, Tests, Tools, Reports)
* **Prüfsummen-Verifikation:** 24 von 24 Dateien mit 100% SHA-256 Übereinstimmung verifiziert.

---

## 3. Architektur & UI-Integration

### 3.1 Preset-Panel & Layout in `PhoenixImageToImageView`
Im Inspector-Panel wurde der Preset-Bereich symmetrisch und platzoptimiert gegliedert:
* **Zeile 0:** `Subtil (0.30)` (Spalte 0) | `Moderat (0.45)` (Spalte 1)
* **Zeile 1:** `Ausgewogen (0.65)` (Spalte 0) | `Kreativ (0.80)` (Spalte 1)
* **Zeile 2:** `Neugenerierung (1.00)` (Spalten 0–1, volle Breite)

```python
self._preset_buttons = {
    0.30: self.btn_subtle,
    0.45: self.btn_moderate,
    0.65: self.btn_balanced,
    0.80: self.btn_creative,
    1.00: self.btn_regen,
}
```

### 3.2 Dynamisches Highlight-Management
Die Methode `_update_preset_highlights()` vergleicht den aktuellen Slider-Wert mit den hinterlegten Preset-Werten:
```python
def _update_preset_highlights(self) -> None:
    try:
        val = round(float(self.strength_var.get()), 2)
    except (ValueError, tk.TclError):
        return

    for preset_val, btn in getattr(self, "_preset_buttons", {}).items():
        if abs(val - preset_val) < 0.01:
            if getattr(btn, "button_type", None) != "secondary":
                btn.configure(button_type="secondary")
        else:
            if getattr(btn, "button_type", None) != "neutral":
                btn.configure(button_type="neutral")
```
* Beim Aufruf der View startet das System mit dem Standardwert `0.65`, wodurch der Button **Ausgewogen (0.65)** unmittelbar als aktiv (`secondary`) hervorgehoben ist.
* Klickt der Anwender einen anderen Preset-Button, übernimmt die UI dessen Stärke-, Schritt- und CFG-Parameter und passt das Highlight an.
* Verstellt der Anwender den Regler manuell auf einen exakten Preset-Wert (z. B. `0.45`), springt das Highlight auf **Moderat (0.45)**.
* Verstellt der Anwender den Regler auf einen Zwischenwert (z. B. `0.55`), werden alle fünf Preset-Buttons neutral dargestellt.

### 3.3 Lokalisierung (`de_DE.json` & `en_US.json`)
Die Preset-Texte wurden in beiden Sprachdateien hinterlegt:
* `img2img_preset_subtle`: `"Subtil (0.30)"` / `"Subtle (0.30)"`
* `img2img_preset_moderate`: `"Moderat (0.45)"` / `"Moderate (0.45)"`
* `img2img_preset_balanced`: `"Ausgewogen (0.65)"` / `"Balanced (0.65)"`
* `img2img_preset_creative`: `"Kreativ (0.80)"` / `"Creative (0.80)"`
* `img2img_preset_regen`: `"Neugenerierung (1.00)"` / `"Regenerate (1.00)"`

---

## 4. Scheduler-Schritte & Inferenzzeiten ($N=20$)

| Preset | Stärke ($s$) | Steps ($N$) | CFG | Reale HTP-Schritte ($K$) | HTP UNet Zeit | Gesamtlaufzeit HTP |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Subtil** | `0.30` | 20 | 7.5 | **6 Schritte** | ~4.0 s | ~11.4 s |
| **Moderat** | `0.45` | 20 | 7.5 | **9 Schritte** | ~6.0 s | ~13.8 s |
| **Ausgewogen (Standard)** | `0.65` | 20 | 7.5 | **13 Schritte** | ~8.6 s | ~16.0 s |
| **Kreativ** | `0.80` | 20 | 8.0 | **16 Schritte** | ~10.6 s | ~18.9 s |
| **Neugenerierung** | `1.00` | 20 | 7.5 | **20 Schritte** | ~13.3 s | ~20.8 s |

*Hinweis:* VAE-Encoder (~6.45 s) und VAE-Decoder (~0.77 s) laufen pro Generierung je einmal hardwarebeschleunigt auf der NPU.

---

## 5. Visuelle Dokumentation

Die visuelle Referenzkarte der fünf Presets und ihrer technischen Garantien wurde erstellt und archiviert:  
[`sprint40_img2img_presets_overview.png`](file:///C:/Users/holge/.gemini/antigravity-cli/brain/c991b454-d253-4b5d-9ce4-469780cc4864/sprint40_img2img_presets_overview.png)

---

## 6. Regressionstests & Validierung

Alle Testsuiten wurden auf Windows 11 ARM64 erfolgreich ausgeführt:
1. **Image-to-Image UI Suite:** [`tests/test_phoenix_image_to_image_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_image_to_image_ui.py)
   * 7/7 Tests bestanden (Presets, Highlights, manuelle Verstellung, Controller-Delegation, Theme-Parität, Scheduler-Schritte).
2. **Navigation Suite:** [`tests/test_phoenix_image_lab_navigation.py`](file:///C:/SnapdragonAI/tests/test_phoenix_image_lab_navigation.py)
   * 7/7 Tests bestanden.
3. **Inpainting UI Suite:** [`tests/test_phoenix_inpainting_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_inpainting_ui.py)
   * 50/50 Tests bestanden.
4. **Qualcomm Hexagon HTP Pipeline Suite:** [`tests/test_sd15_qnn_inpainting_pipeline.py`](file:///C:/SnapdragonAI/tests/test_sd15_qnn_inpainting_pipeline.py)
   * 19/19 Tests bestanden auf Hexagon NPU V73 (0.00 ms CPU-Fallback).
5. **Gesamtergebnis:** **83 von 83 Tests erfolgreich (100% Pass Rate)**.

---

## 7. Post-Backup & Verifikation

Das Post-Backup wurde unter `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_40_20261101` abgelegt und per SHA-256 verifiziert.
* **Dateien gesichert:** 28 Dateien
* **SHA-256 Übereinstimmung:** 100%
* **Git-Operationen:** Keine Commits, Pushes oder Builds (Governance strikt gewahrt).

---
*Senior Software Engineer (Gemini) – HK NPU STUDIO*
