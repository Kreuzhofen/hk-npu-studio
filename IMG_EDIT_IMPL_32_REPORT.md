# HK NPU STUDIO – SPRINT IMG-EDIT-IMPL-32 REPORT
**Soft Brush, Brush Hardness & Grayscale Masking Architecture**  
**Qualcomm Snapdragon X Elite (Hexagon HTP NPU V73) | Windows 11 ARM64**  
*Datum:* 01. November 2026  
*Status:* Erfolgreich abgeschlossen (DoD erfüllt)

---

## 1. Executive Summary

Im Sprint **IMG-EDIT-IMPL-32** wurde die Maskierungsarchitektur des *Phoenix Image Lab* um eine professionelle Pinselsteuerung erweitert:
1. **Einstellbarer Pinselradius / Pinselgröße:** Präzise Steuerung von 8 bis 160 px Durchmesser (4 bis 80 px Radius) über Scale und programmatische Schnittstellen (`set_brush_size`, `set_brush_radius`, `brush_radius`-Property).
2. **Brush Hardness (0–100 %):**
   - **100 % (Hard):** Scharfe Kante ohne Weichzeichnung ($R_{core} = R$).
   - **50 % (Soft):** Fester Innenkern bis 50 % des Radius ($R_{core} = 0.5 R$), gefolgt von einem stufenlosen Cosinus-Übergang zur Außenkante.
   - **0 % (Very Soft):** Punktförmiger Spitzenwert im Zentrum ($R_{core} = 0$), fließender Cosinus-Abfall über den gesamten Radius.
3. **Live Cursor Preview (Radius & Härte):**
   - Dynamischer Doppelring-Cursor direkt auf dem Canvas: Ein äußerer Ring (`PHOENIX_THEME.accent`) zeigt den Gesamtradius $R$, ein innerer gestrichelter Ring (`PHOENIX_THEME.text_secondary`) markiert bei Härte $< 100\,\%$ exakt die Kernzone $R_{core}$.
   - Automatische Skalierung bei Canvas-Zoom (`zoom_wheel`) und Pan, unterbrechungsfreie Anzeige beim Ziehen und Malen.
4. **Symmetrisches Malen und Radieren:**
   - Sowohl der Zeichenmodus (`erase=False`, Wertezuwachs via $\max(M, S)$) als auch der Radiermodus (`erase=True`, Abzug via $\min(M, 255 - S)$) nutzen dieselbe Härtesteuerung und denselben radialen Stempel.
5. **Echte 8-Bit-Graustufenmaske (Continuous Grayscale Mask):**
   - Die weichen Übergänge bleiben als echte 8-Bit-Graustufenwerte ($0 \dots 255$) im PNG erhalten und werden nahtlos in die Inpainting-Pipeline eingespeist.
   - `generate_feathered_mask` und `align_color_lab` erhalten die kontinuierlichen Verläufe intakt, ohne sie durch harte Schwellenwerte zu zerstören.
   - **Garantie unmaskierter Pixel:** Pixel außerhalb der Maske (`mask == 0` bei `dilate_pixels == 0`) bleiben zu 100 % bitgenau identisch (`max_diff = 0`, `mean_diff = 0.0`).
   - Die Hexagon-HTP-Inferenzschleife, VAE-Quantisierung und UNet-Scheduler bleiben unberührt.

---

## 2. Mathematisches Modell des Pinsels & Falloff-Funktion

Für einen Radius $R$ und eine Härte $H \in [0.0, 1.0]$ wird der Kernradius definiert als:
$$R_{core} = R \times H$$

Für jeden Punkt mit euklidischem Abstand $d = \sqrt{\Delta x^2 + \Delta y^2}$ vom Stempelzentrum:
- **Außerhalb des Pinsels ($d > R$):** $S(d) = 0$
- **Härte 100 % ($H = 1.0$) oder innerhalb des Kerns ($d \le R_{core}$):** $S(d) = 255$
- **Übergangszone ($R_{core} < d \le R$):**  
  Normierter Übergangsparameter:
  $$t = \frac{d - R_{core}}{R - R_{core}} \in [0.0, 1.0]$$
  Cosinus-Falloff (Hermite-glatt, erste Ableitung an beiden Rändern 0):
  $$S(d) = \text{round}\left(255 \times \frac{1 + \cos(\pi \cdot t)}{2}\right)$$

### Stempelfolge & Pfadinterpolation
Beim Zeichnen eines Pinselstrichs von $(x_0, y_0)$ nach $(x_1, y_1)$ mit Distanz $D$:
$$\text{Schrittweite } s = \max(1.0, R \times 0.25)$$
$$\text{Schritte } N = \max(1, \lceil D / s \rceil)$$
An jedem Zwischenschritt wird der vorberechnete, über `@lru_cache(maxsize=128)` gecachte Stempel in den NumPy-Puffer eingearbeitet:
- **Malen:** $\text{Maske}[y, x] = \max(\text{Maske}[y, x], \text{Stempel}[sy, sx])$
- **Radieren:** $\text{Maske}[y, x] = \min(\text{Maske}[y, x], 255 - \text{Stempel}[sy, sx])$

---

## 3. Betroffene & Modifizierte Komponenten

| Datei | Pfad | Änderungen |
|---|---|---|
| `inpainting_canvas.py` | `widgets/phoenix/inpainting_canvas.py` | Radiale Stempelberechnung (`_generate_brush_stamp`), Härte-Attribute (`brush_hardness`, `brush_radius`), `paint_mask` mit kontinuierlicher Pfadinterpolation und Härte, Live-Doppelring-Cursor-Vorschau (`_draw_brush_preview`), Behebung von rekursivem `after_idle` bei nicht-gemappten Fenstern. |
| `inpainting_view.py` | `widgets/phoenix/views/inpainting_view.py` | Ergänzung der Werkzeugleiste um Härte-Schieberegler (0–100 %), Prozentanzeige, dynamische Handler (`_on_brush_size_change`, `_on_brush_hardness_change`), volle Dark/Light-Theme-Parität. |
| `sd15_qnn_inpainting_adapter.py` | `engine/backends/sd15_qnn_inpainting_adapter.py` | Erhaltung kontinuierlicher Graustufenverläufe in `generate_feathered_mask` und `align_color_lab`, bitgenaue Erhaltung unmaskierter Pixel (`max_diff = 0`), Erhalt der HTP-UNet-Quantisierung. |
| `inpainting_controller.py` | `controllers/inpainting_controller.py` | Bilineare Skalierung für Arbeitsausschnitte (`Image.Resampling.BILINEAR`), um Graustufenabstufungen treu an das 512x512-Modellgitter zu übergeben. |
| `de_DE.json` / `en_US.json` | `locales/` | Neue Lokalisierungsschlüssel: `"inpainting_brush_hardness": "Härte"` / `"Hardness"`. |
| `test_phoenix_inpainting_ui.py` | `tests/` | 7 neue Unit-Tests für 100 %, 50 % und 0 % Härte, Radieren mit Härte, Einmalklick-Stempel, Properties und View-Synchronisation. |
| `test_sd15_qnn_inpainting_pipeline.py` | `tests/` | 2 neue Pipeline-Vertragstests für Graustufenmaskenerhaltung, Dilatation/Feathering auf Soft Masks und Bit-Identität unmaskierter Pixel (`max_diff = 0`). |

---

## 4. Validierung & Testergebnisse

### 4.1 Unit- und UI-Tests
- **Befehl:** `python -m unittest discover -s tests -p "test_phoenix_inpainting_ui.py"`
- **Ergebnis:** `Ran 46 tests in 3.416s – OK` (alle 46 Tests erfolgreich, 0 Fehler).

### 4.2 Inpainting-Pipeline & HTP-Inferenz
- **Befehl:** `python -m unittest discover -s tests -p "test_sd15_qnn_inpainting_pipeline.py"`
- **Ergebnis:** `Ran 19 tests in 12.788s – OK` (alle 19 Tests erfolgreich, 0 Fehler).
- **HTP-Hardwaremessung auf Snapdragon X Elite (HTP V73):**
  - HTP VAE Encoder: 2291.88 ms
  - CPU VAE Encoder: 0.00 ms (CPU-Fallback deaktiviert)
  - HTP CLIP Text: 7.98 ms
  - HTP UNet Total: 3221.58 ms (15 Schritte, 214.77 ms/Schritt)
  - HTP VAE Decoder: 254.20 ms
  - Gesamtpipeline: 5775.65 ms
  - Unmaskierte Pixel: `max_diff = 0`, `mean_diff = 0.0` (100 % bitgenau identisch).

### 4.3 Navigation
- **Befehl:** `python -m unittest discover -s tests -p "test_phoenix_image_lab_navigation.py"`
- **Ergebnis:** `Ran 6 tests in 0.891s – OK`.

### 4.4 Syntax- & Compilerprüfung
- **Befehl:** `python -m py_compile widgets/phoenix/inpainting_canvas.py widgets/phoenix/views/inpainting_view.py controllers/inpainting_controller.py engine/backends/sd15_qnn_inpainting_adapter.py tests/test_phoenix_inpainting_ui.py tests/test_sd15_qnn_inpainting_pipeline.py`
- **Ergebnis:** 0 Fehler, saubere Kompilierung.

---

## 5. Visuelle Artefakte & Theme-Parität

Die generierten Bild-Artefakte stehen im Artefaktverzeichnis bereit:

1. **Pinsel-Härteprofile & Cosinus-Falloff:**  
   `sprint32_brush_hardness_profiles.png`  
   Empirischer Querschnittsvergleich zwischen Härte 100 %, 50 % und 0 %.
2. **Dark Theme Gesamtsicht:**  
   `sprint32_dark_soft_brush_view.png`  
   Generatives Füllen im Dark-Theme mit Werkzeugleiste (Pinselgröße 64, Härte 50 %), Doppelring-Cursor-Vorschau und weichem Maskenauftrag.
3. **Dark Theme Werkzeugleiste (Zoom):**  
   `sprint32_dark_toolbar_zoom.png`  
   Fokus auf Pinselgröße, Härte-Schieberegler und Prozentanzeige.
4. **Light Theme Gesamtsicht:**  
   `sprint32_light_soft_brush_view.png`  
   Vollständige Theme-Parität im Light-Theme.
5. **Light Theme Werkzeugleiste (Zoom):**  
   `sprint32_light_toolbar_zoom.png`  
   Visuelle Sauberkeit aller Phoenix-Komponenten im hellen Farbschema.

---

## 6. Sicherheitsprüfung & Backup-Verifikation

Vor und nach den Arbeiten wurden alle betroffenen Dateien auf Laufwerk D: gesichert:
- **Backup-Pfad:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_32_20261101`
- **Prüfsummenverfahren:** SHA-256 Bit-für-Bit-Abgleich.
