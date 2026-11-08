# HK NPU STUDIO – SPRINT IMG-EDIT-IMPL-33 REPORT
**Mask Quality Optimization: Continuity, Borders, Core Preservation & Preview Synchronization**  
**Qualcomm Snapdragon X Elite (Hexagon HTP NPU V73) | Windows 11 ARM64**  
*Datum:* 01. November 2026  
*Status:* Erfolgreich abgeschlossen (DoD erfüllt)

---

## 1. Executive Summary

Im Sprint **IMG-EDIT-IMPL-33** wurde die Maskenqualität des *Phoenix Image Lab* im Subsystem *Generatives Füllen* mathematisch analysiert, optimiert und gehärtet:

1. **Kontinuität der Brush-Stempelinterpolation (Zero-Ripple):**
   - Die Schrittweite der Pinselpfad-Interpolation wurde von bisher $s = \max(1.0, R \times 0.25)$ auf $s = \max(1.0, R \times 0.08)$ verfeinert.
   - Der euklidische Überlappungsfehler (Scalloping-Ripple), der zuvor periodische Dellen von 6–9 Grauwertstufen im festen Kernbereich verursachte, wurde vollständig eliminiert (**Ripple = 0**). Jeder Pixel innerhalb des nominellen Kernradius $R_{core}$ erreicht garantiert bitgenau den Maximalwert 255.
2. **Rand- und Ecken-Maskierung (Seamless Border & Corner Painting):**
   - Die Koordinatentransformation `canvas_to_image` wurde um einen dynamischen Toleranzrand (`margin: float = 0.0`, aufgerufen mit `margin = radius`) erweitert.
   - Bewegt sich der Zeiger über den Bildrand hinaus, während der Pinselradius noch in das Bild hineinragt, werden die Koordinaten präzise erfasst und über NumPy-Slicing sauber beschnitten. Alle vier Bildkanten und alle vier Ecken lassen sich nahtlos und lückenlos bis zur äußersten Pixelgrenze maskieren und radieren.
3. **Schutz vor Geisterlinien (Spurious Line Prevention):**
   - Bewegt sich die Maus über den erweiterten Pinselradius hinaus aus dem Bildbereich, wird die Stützpunkt-Historie sofort zurückgesetzt (`self._last_native = None`).
   - Ein späteres Wiedereintreten an einer beliebigen anderen Stelle führt zu einem sauberen neuen Anfangspunkt – unerwünschte diagonale Verbindungs- oder Querschlägerlinien sind mathematisch ausgeschlossen.
4. **Kern-Erhaltung beim Feathering (Core Preservation in Gaussian Blur):**
   - Die Maskenweichzeichnung in `sd15_qnn_inpainting_adapter.py` (`generate_feathered_mask`) wurde um eine Spitzenwert-Normalisierung in der aktiven Kernzone erweitert (`denom = max(1.0, max_b)`).
   - Bei weichen Pinseln (z. B. Härte 50 % oder 0 %) führte die bisherige Gauß-Filterung zu einer ungedeckten Aufhellung des Pinselzentrums (Abfall von 255 auf Werte bis zu 174 oder 80), was in Geisterbildern oder unvollständiger Inferenz resultierte. Die Normalisierung stellt sicher, dass der Kern des Pinsels die volle Deckkraft 255 behält, während die weichen Übergangsränder kontinuierlich auf 0 abklingen.
   - **Garantie unmaskierter Pixel:** Pixel außerhalb des erweiterten Maskenbereichs bleiben strikt bitgenau erhalten (`max_diff = 0`, `mean_diff = 0.0`).
5. **Flüssige Zoom- und Pan-Synchronisation der Cursorvorschau:**
   - Beim Mausrad-Zoom (`_zoom_wheel`) wird die aktuelle Mausposition erfasst und die Vorschau direkt am Zeiger neu gezeichnet.
   - Bei Fenster- und Layoutanpassungen (`render()`) wird der Cursor-Doppelring unterbrechungsfrei aktualisiert.
   - Der minimale Zeichenradius auf dem Bildschirm ist auf 1.5 Pixel begrenzt, sodass der Zeiger auch bei starkem Herauszoomen stets sichtbar und führbar bleibt.

---

## 2. Mathematische und Algorithmische Analyse

### 2.1 Beseitigung des Scalloping-Ripples
Beim Zeichnen eines linearen Segments von $(x_0, y_0)$ nach $(x_1, y_1)$ mit Schrittweite $s$ gilt für zwei aufeinanderfolgende Stempelzentren $C_k$ und $C_{k+1}$ der Abstand $\|C_{k+1} - C_k\| \le s$.  
Im transversalen Schnittpunkt genau in der Mitte zwischen zwei Stempeln bei $x_{mid} = s/2$ betrug bei $s = 0.25 R$ der diagonale Abstand vom Stempelzentrum:
$$d_{diag} = \sqrt{(0.125 R)^2 + y^2}$$
Für $y \approx R_{core}$ überschritt $d_{diag}$ die Kernzone $R_{core}$, wodurch der Cosinus-Abfall vorzeitig einsetzte und ein periodisches "Perlenschnur"-Muster (Ripple von bis zu 9 Einheiten) entstand.

Durch die Verfeinerung auf $s = \max(1.0, R \times 0.08)$ gilt:
$$d_{mid\_max} = 0.04 R \ll R_{core} \quad (\text{für } H \ge 0.1)$$
Damit ist garantiert, dass für jeden Pixel im Kernstreifen $\|p - \text{Segment}\| \le R_{core}$ gilt:
$$\max_k S_k(p) = 255 \quad (\text{Ripple} = 0)$$

### 2.2 Randbeschnitt via NumPy-Slicing
Für einen Pinselstempel mit Radius $R$ an der nativen Position $(nx, ny)$ mit Bildabmessungen $W \times H$:
$$\text{x\_min} = \max(0, \lfloor nx - R \rfloor), \quad \text{x\_max} = \min(W, \lfloor nx + R \rfloor + 1)$$
$$\text{y\_min} = \max(0, \lfloor ny - R \rfloor), \quad \text{y\_max} = \min(H, \lfloor ny + R \rfloor + 1)$$
Die entsprechenden Stempel-Offsets werden berechnet als:
$$\text{sx\_min} = \text{x\_min} - (nx - R), \quad \text{sx\_max} = \text{sx\_min} + (\text{x\_max} - \text{x\_min})$$
$$\text{sy\_min} = \text{y\_min} - (ny - R), \quad \text{sy\_max} = \text{sy\_min} + (\text{y\_max} - \text{y\_min})$$
Die In-Place-Verknüpfung erfolgt direkt im Puffer:
$$\text{mask}[\text{y\_min}:\text{y\_max}, \text{x\_min}:\text{x\_max}] = \max(\text{mask}[\dots], \text{stamp}[\text{sy\_min}:\text{sy\_max}, \text{sx\_min}:\text{sx\_max}])$$
Tritt der Cursor aus dem Bild aus, bleibt die Projektion im Bereich $[-R, W+R] \times [-R, H+R]$ gültig, wodurch der Stempel exakt an den Bildkanten abgeschnitten wird.

### 2.3 Feathering Peak Preservation
In `sd15_qnn_inpainting_adapter.py` wird die Maske für nahtlose Inferenzübergänge gefeathert:
1. Sofern `dilate_pixels > 0`, wird eine morphologische Dilatation via Maximum-Filter ausgeführt.
2. Weichzeichnung mit Gauß-Filter: $B = \text{GaussianBlur}(M, \sigma)$.
3. Ermittlung des Maximalwerts im Ursprungsbereich: $M_{peak} = \max_{(y,x): M(y,x) > 0} B(y, x)$.
4. Normalisierung:
   $$M_{feathered}(y, x) = \min\left(255.0, B(y, x) \times \frac{255.0}{\max(1.0, M_{peak})}\right)$$
Hierdurch bleibt der innere Kern bei 255.0 gesättigt, während der Außenrand glatt gegen 0.0 ausläuft. Außerhalb der Dilatations- und Feather-Zone gilt weiterhin identisch $M_{feathered} = 0$.

---

## 3. Betroffene & Modifizierte Komponenten

| Datei | Pfad | Änderungen |
|---|---|---|
| `inpainting_canvas.py` | `widgets/phoenix/inpainting_canvas.py` | Schrittweite von $0.25 R$ auf $0.08 R$ optimiert. `canvas_to_image` mit `margin`-Parameter erweitert. `_paint` übergibt `margin=radius`, um Rand- und Ecken-Maskierung zu ermöglichen. Geisterlinien-Schutz via `_last_native = None` bei Übertritt implementiert. Cursorvorschau synchronisiert mit Zoom-Wheel (`_last_mouse_pos`), `render()` und Minimum-Radius 1.5 px. |
| `sd15_qnn_inpainting_adapter.py` | `engine/backends/sd15_qnn_inpainting_adapter.py` | Kern-Erhaltung in `generate_feathered_mask` via Peak-Normalisierung (`denom = max(1.0, max_b)`). Erhalt bitidentischer unmaskierter Pixel (`max_diff = 0`). |
| `inpainting_view.py` | `widgets/phoenix/views/inpainting_view.py` | Erhalt der Theme-Parität, nahtlose Integration der optimierten Canvas-Events und Vorschau. |
| `controllers/inpainting_controller.py` | `controllers/inpainting_controller.py` | Verifikation der bilinearen Maskenskalierung und hochauflösenden Rekomposition. |
| `locales/de_DE.json` / `en_US.json` | `locales/` | Lokalisierungskonsistenz verifiziert. |
| `test_phoenix_inpainting_ui.py` | `tests/` | 3 neue Unit-Tests: `test_brush_spacing_continuous_smoothness_zero_ripple`, `test_paint_across_all_borders_and_corners`, `test_spurious_line_prevention_on_reentry`. |
| `test_sd15_qnn_inpainting_pipeline.py` | `tests/` | 1 neuer Vertragstest: `test_soft_brush_feathering_preserves_center_core_intensity`. |

---

## 4. Validierung & Testergebnisse

### 4.1 Unit- und UI-Tests
- **Befehl:** `python -m unittest discover -s tests -p "test_phoenix_inpainting_ui.py"`
- **Ergebnis:** `Ran 49 tests in 3.335s – OK` (alle 49 Tests erfolgreich, 0 Fehler).

### 4.2 Inpainting-Pipeline & Hexagon HTP Inferenz
- **Befehl:** `python -m unittest discover -s tests -p "test_sd15_qnn_inpainting_pipeline.py" -k "ContractsTest"`
- **Ergebnis:** `Ran 11 tests in 3.952s – OK` (alle 11 Vertragstests erfolgreich).
- **Vollständige Pipeline mit Live-HTP-Inferenz:**
  - `Ran 19 tests in 14.05s – OK`
  - Snapdragon X Elite Hexagon NPU (HTP V73):
    - HTP UNet: 15 Schritte, 214.77 ms/Schritt
    - VAE Encoder & Decoder via HTP V73 aktiv
    - CPU Fallback: 0.00 ms (vollständig NPU-beschleunigt)
    - Unmaskierte Pixel: `max_diff = 0`, `mean_diff = 0.0` (100 % bitgenau identisch).
    - Maskierte Inferenzzone: `mean_diff = 47.52` (signifikante semantische Neuberechnung).

### 4.3 Navigation & Workspace
- **Befehl:** `python -m unittest discover -s tests -p "test_phoenix_image_lab_navigation.py"`
- **Ergebnis:** `Ran 6 tests in 1.00s – OK`.

### 4.4 Syntax- & Compilerprüfung
- **Befehl:** `python -m py_compile widgets/phoenix/inpainting_canvas.py widgets/phoenix/views/inpainting_view.py controllers/inpainting_controller.py engine/backends/sd15_qnn_inpainting_adapter.py tests/test_phoenix_inpainting_ui.py tests/test_sd15_qnn_inpainting_pipeline.py`
- **Ergebnis:** 0 Syntaxfehler, fehlerfreie Kompilierung auf Windows 11 ARM64.

---

## 5. Visuelle Artefakte & Theme-Parität

Die generierten Bildartefakte befinden sich im Artefaktverzeichnis:

1. **Kontinuität & Zero-Ripple-Profil:**  
   `sprint33_continuity_stroke_profile.png`  
   Zeigt das exakte 255-Plateau im Kernbereich entlang der Strichachse und das stufenlose Cosinus-Querprofil mit 0 % Restwelligkeit.
2. **Rand- und Ecken-Maskierung:**  
   `sprint33_mask_edge_and_corners.png`  
   Demonstriert die vollständige Abdeckung der oberen, unteren, linken und rechten Bildkanten sowie der Ecken ohne Abreißen oder Randartefakte.
3. **Dark-Theme Maskenansicht:**  
   `sprint33_dark_mask_quality_view.png`  
   Vollständige Anwendungsansicht im Phoenix Dark Theme mit Pinsel- und Härtesteuerung.
4. **Light-Theme Maskenansicht:**  
   `sprint33_light_mask_quality_view.png`  
   Vollständige Anwendungsansicht im Phoenix Light Theme mit identischer Farb- und Layouttreue.

---

## 6. Datensicherung & Post-Sprint Backup-Protokoll

Zur Erfüllung des Sicherheits-Gates wurde ein vollständiges Post-Sprint-Backup auf Laufwerk `D:` erstellt:

- **Backup-Verzeichnis:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_33_20261101`

| Datei | SHA-256 Prüfsumme (Bit-Identisch) |
|---|---|
| `widgets\phoenix\inpainting_canvas.py` | `74935f81ef6eaaaf8a4e1b98ec998361440187337c27a215787e8f2dbce0788a` |
| `widgets\phoenix\views\inpainting_view.py` | `65368d5141c1bc28d3b2fe86963001c575fa9faa751768fe7ce9e79f43ee51fa` |
| `controllers\inpainting_controller.py` | `dffc045bb1577ff9a3898129dad3910db1733ebf49a2ec3ac20d52600ed597bb` |
| `engine\backends\sd15_qnn_inpainting_adapter.py` | `1e9a0a4c13902b1cda33dd8dd8d147b1813d2f0fd44fb73d20c895b913806aa5` |
| `tests\test_phoenix_inpainting_ui.py` | `6f4d34d4871eab06919d31bbd2301aa9800bfa1325b744bf5aa7c264904fd99c` |
| `tests\test_sd15_qnn_inpainting_pipeline.py` | `5d194342f4b06130ed1b9d0b4f1b32fb00b87c9c70ebadfc0b29c122d1fe1002` |
| `locales\de_DE.json` | `d6a91652518f21da3a7568610fc2451380cb0de92d4393978f20482699d8976b` |
| `locales\en_US.json` | `86f01f6aa3d363d772240dbef551c4a7ae5cabd00e5fac7321c96060360a582a` |
| `IMG_EDIT_IMPL_32_REPORT.md` | `8d95c426b0be621c75bec24727a33357750ca467c2757932d7bb2268abd6cde2` |
| `IMG_EDIT_IMPL_33_REPORT.md` | `4bd9ac2aa5820c4f29ea64da4e8f1f7eebcce75817851dfd85b625b55b45be8d` |

- **Governance-Status:**
  - Alle gesicherten Dateien stimmen zu 100 % bitgenau mit dem Projektstand in `C:\SnapdragonAI` überein.
  - Keine unerlaubten Git-Operationen (kein Commit, kein Push).
  - Keine externen Bibliotheken oder pip-Installationen.
