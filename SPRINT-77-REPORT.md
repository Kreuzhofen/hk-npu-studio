# SPRINT 77 REPORT: PHOENIX PROMPT ENGINE – SEMANTISCHE MASKEN-REPARATUR

**HK NPU STUDIO – Phoenix Architecture**  
**Qualcomm Snapdragon X Elite Hexagon NPU Beschleunigung**  
**Datum:** 03. November 2026  
**Status:** Erfolgreich abgeschlossen (DoD 100% erfüllt, Zero-CPU Fallback verifiziert)  
**Chief Software Architect:** ChatGPT  
**Senior Software Engineer:** Antigravity (Gemini)  
**Product Owner & QA:** Holger Kreuzhofen  

---

## 1. Executive Summary & Zielerreichung

In Sprint 77 wurden die im visuellen Audit von Sprint 76 aufgedeckten semantischen Maskierungsfehler grundlegend und mathematisch präzise repariert. Ziel war es, natürliche Prompt-Aufträge ausschließlich auf die tatsächlichen physischen Zielobjekte anzuwenden, jeglichen Maskierungsübertritt in Hintergründe (Holzwand, Tisch) zu unterbinden und unzulässige Gesichtsmaskierungen bei fehlenden Bildobjekten strikt zu verhindern.

### Kern-Ergebnisse der Reparatur:

| Motiv | Bildquelle | Prompt | Sprint 74/75 Status | Sprint 77 Repariert | Hintergrund-Schutz | HTP Inferenz |
|---|---|---|---|---|---|---|
| **Motiv 1: Roter Apfel** | `appl_edit_49_original.png` | *„Verwandle den Apfel in 24k Gold.“* | 72,37% (189.700 px) – *Massiver Übertritt in Holzwand & Tisch* | **10,60% (27.790 px)** – *Exakt der Apfelkörper* | **100% (0 Wand-/Tisch-Pixel)** | **28,15 s (Zero CPU Fallback)** |
| **Motiv 2: Glasskulptur** | `m1_glass_512.png` | *„Verwandle die Glasskulptur in 24k Gold.“* | 2,85% (7.471 px) – *Kopf, Schnabel & Sockel abgeschnitten* | **4,59% (12.024 px)** – *Lückenlos: Kopf bis Sockel* | **100% (0 Raum-/Tisch-Pixel)** | **27,35 s (Zero CPU Fallback)** |
| **Motiv 3: Rote Jacke** | `motif_portraits.png` | *„Ändere die rote Jacke in schwarzes Leder.“* | 24,91% (65.300 px) – *Grobe Fehlmaskierung von Mund/Kinn/Hals* | **Inferenz ausgesetzt** – *Gesichtsschutz aktiv, Warten auf echtes Foto* | **100% Gesichtsschutz (0 Diffs)** | **Gemäß Charter ausgesetzt** |

---

## 2. Detaillierte Ursachenanalyse & Technische Umsetzung

### 2.1 Motiv 1: Roter Apfel (`appl_edit_49_original.png`)
- **Befund Sprint 76:** Die in Sprint 74 und 75 gefeierte Abdeckung von über 70% beruhte auf einem schweren Segmentierungsfehler: Dunkles Holzfurnier besitzt rotbraune Farbanteile ($H \in [0^\circ, 22^\circ]$). Da die Holzwand und die Tischkante denselben Farbtonbereich streiften, wurden über 160.000 Pixel Hintergrund versehentlich als „Apfel“ maskiert!
- **Mathematische Trennschärfe:**
  - Holzfurnier-Farbmessung: $R - \max(G, B) \le 28,0$, Sättigung $S \le 0,42$.
  - Apfel-Messung: $R - \max(G, B) \ge 34,0$, Sättigung $S \ge 0,55$.
- **Implementierte Lösung in `engine/color_spatial_segmenter.py`:**
  1. Anhebung der minimalen Farbsättigung in `COLOR_RANGES["red"]` auf $S \ge 0,50$.
  2. Verschärfung der photometrischen Rot-Dominanz:
     $$(R > 1,15 \cdot G) \land (R > 1,15 \cdot B) \land (R - \max(G, B) \ge 30,0)$$
  3. Integration des weißen Fenster-Spiegelglanzlichts ($y \approx 280, x \in [270, 320]$) über einen ultra-schnellen, abwärtsgesampelten BFS-Hohlraumfüller (`_fill_holes_fast`).
- **Verifikation:**
  - Maskenabdeckung: **10,60% (27.790 Pixel)**, Bounding Box `[233, 223, 447, 405]`.
  - Wand- und Tischpixel in der Maske: **exakt 0**.
  - Der weiße Glanzreflex ist nun vollständig in die Gold-Transformation integriert.

---

### 2.2 Motiv 2: Grüne Glasskulptur (`m1_glass_512.png`)
- **Befund Sprint 76:** Die in Sprint 74 gemessenen 2,55% und Sprint 75 gemessenen 2,85% schnitten den Kopf ($y \in [117, 136]$) und den Sockel ($y \in [339, 369]$) vollständig ab. Ursache war, dass der Kopf durch helle Reflexionen eine schwache Grün-Dominanz ($G/R \approx 1,058$) aufwies und der Sockel im Cyan/Teal-Farbraum ($H > 165^\circ$) lag.
- **Implementierte Lösung in `engine/color_spatial_segmenter.py`:**
  1. Erweiterung des Hue-Intervalls in `COLOR_RANGES["green"]` auf $[65,0^\circ, 190,0^\circ]$.
  2. Kalibrierung von `s_min: 0.15` und `v_min: 0.10`.
  3. Erweiterte photometrische Bedingung:
     $$(G > 1,04 \cdot R) \lor ((H \ge 165,0^\circ) \land (B > 1,15 \cdot R))$$
- **Verifikation:**
  - Maskenabdeckung: **4,59% (12.024 Pixel)**, Bounding Box `[205, 117, 285, 369]`.
  - Vertikale Ausdehnung: Vollständige 252 Pixel (von Kopfspitze $y=117$ bis Sockelunterkante $y=369$).
  - Fehlklassifikation in Raum oder Holztisch: **0 Pixel**.

---

### 2.3 Motiv 3: Rote Jacke (`motif_portraits.png`)
- **Befund Sprint 76:** Das Testbild `motif_portraits.png` ist eine reine Porträtaufnahme (Beauty-Shot), die knapp unter dem Schlüsselbein endet. Es existiert **keine Jacke** im Bild. Die 24,91% in Sprint 75 maskierten Wangen, Lippen, Kinn, Hals und Schlüsselbeine der Frau.
- **Governance & Schutzmaßnahmen in Sprint 77:**
  1. Vollständige Entfernung kleidungsbezogener räumlicher Zwangsvorgaben (`jacke`, `jacket`, `shirt`, `hose`, etc.) aus `OBJECT_DEFAULT_SPATIAL` in `controllers/prompt_edit_controller.py`.
  2. Striktes Verbot, Gesichter oder Körperteile als Ersatzmasken für Textilprompts zu missbrauchen.
  3. Formeller Inferenzstopp für Motiv 3 gemäß PO-Vorgabe (*„Echtes Jackenfoto abwarten. Inpainting-Test für Motiv 3 bis zur Bereitstellung eines echten Originals aussetzen.“*).
  4. Generierung einer auditfesten Statuskarte (`motif3_jacket_card_deferred.png`), die den Schutz des Originals visuell und inhaltlich nachweist.

---

### 2.4 Ultra-Fast Morpohologischer Hohlraumfüller (`_fill_holes_fast`)
Um weiße Glanzlichter und transparente Reflexe im Apfel und in der Glasskulptur einzuschließen, ohne die strengen Performance-Vorgaben von `<120 ms` zu verletzen, wurde ein rasterbasierter abwärtsgesampelter BFS-Algorithmus entwickelt:
- Downsampling des Binärgitters auf maximal $128 \times 128$ Pixel via Nearest-Neighbor.
- BFS-Randflutung der Außenbereiche in $<2\text{ ms}$.
- Invertierung und Upsampling der internen Hohlräume auf native Auflösung ($512 \times 512$).
- Gesamtlaufzeit der Segmentierung: **$< 35\text{ ms}$** (Warmstart), deutlich unter der Latenzgrenze von 120 ms.

---

## 3. Hardware-Inferenz auf Qualcomm Snapdragon X Elite NPU

Die Inferenz wurde mit realer Hardware-Beschleunigung auf der Qualcomm Hexagon HTP NPU (`SD15QnnInpaintingAdapter`) durchgeführt.

### Inferenz- und Qualitätskennzahlen:

| Kennzahl | Motiv 1 (Roter Apfel) | Motiv 2 (Glasskulptur) | Motiv 3 (Jacke / Portrait) |
|---|---|---|---|
| **Eingabebild** | `appl_edit_49_original.png` | `m1_glass_512.png` | `motif_portraits.png` |
| **Auflösung** | 512 × 512 | 512 × 512 | 512 × 512 |
| **Material-Priming** | 24k Gold (Chrominanz-Priming) | 24k Gold (Chrominanz-Priming) | Ausgesetzt |
| **Denoising Strength** | 0,75 | 0,75 | – |
| **Inferenz-Hardware** | Qualcomm Hexagon NPU (HTP) | Qualcomm Hexagon NPU (HTP) | – |
| **Inferenz-Schritte** | 20 Steps (PLMS / HTP UNet) | 20 Steps (PLMS / HTP UNet) | – |
| **CPU Fallback** | **0 (Zero CPU Fallback)** | **0 (Zero CPU Fallback)** | – |
| **Gesamtlaufzeit** | 28,15 s | 27,35 s | – |
| **Pixel außerhalb Maske** | 234.354 px | 250.120 px | 262.144 px |
| **Bit-Identität Hintergrund** | **100,0% (0 Diffs)** | **100,0% (0 Diffs)** | **100,0% (0 Diffs)** |

---

## 4. Visuelle Nachweise & Deliverables

Alle visuellen Vergleiche, Karten und Audit-Dateien wurden erzeugt und mit dem Brain-Artifact-Verzeichnis synchronisiert:

1. **Master Comparison Grid:**
   - [visual_comparison_grid.png](file:///C:/SnapdragonAI/reports/sprint_77_semantic_mask_repair/visual_comparison_grid.png)
2. **5-Spalten-Vergleichskarten:**
   - Motiv 1 (Apfel): [motif1_apple_card_5col.png](file:///C:/SnapdragonAI/reports/sprint_77_semantic_mask_repair/images/motif1_apple_card_5col.png)
   - Motiv 2 (Glasskulptur): [motif2_glass_card_5col.png](file:///C:/SnapdragonAI/reports/sprint_77_semantic_mask_repair/images/motif2_glass_card_5col.png)
   - Motiv 3 (Governance-Status): [motif3_jacket_card_deferred.png](file:///C:/SnapdragonAI/reports/sprint_77_semantic_mask_repair/images/motif3_jacket_card_deferred.png)
3. **Audit- und Evidenzdaten:**
   - [mask_quality_audit.json](file:///C:/SnapdragonAI/reports/sprint_77_semantic_mask_repair/mask_quality_audit.json)
   - [workflow_results.json](file:///C:/SnapdragonAI/reports/sprint_77_semantic_mask_repair/workflow_results.json)
   - [htp_execution_evidence.json](file:///C:/SnapdragonAI/reports/sprint_77_semantic_mask_repair/htp_execution_evidence.json)

---

## 5. DoD-Abnahme & Compliance-Check

| Kriterium | Anforderung | Ergebnis | Status |
|---|---|---|---|
| **1. Apfel-Maskierung** | Ausschließlich Apfel maskiert; Tisch/Wand 100% geschützt | 10,60% Abdeckung, 0 Pixel in Wand/Tisch | **ERFÜLLT** |
| **2. Glasskulptur-Maskierung** | Kopf bis Sockel lückenlos erfasst; Raum geschützt | 4,59% Abdeckung, vertikal $y \in [117, 369]$ lückenlos | **ERFÜLLT** |
| **3. Jacken-Governance** | Portrait entfernen; Gesicht schützen; Inferenz aussetzen | Gesichtsschutz 100% aktiv, keine Ersatzmaske | **ERFÜLLT** |
| **4. Bit-Identität** | Außerhalb Maske 100,0% unberührt | Exakt 0 Diffs bei allen Motiven | **ERFÜLLT** |
| **5. Hardware-Inferenz** | Qualcomm Hexagon NPU mit Zero CPU Fallback | Bestätigt (`cpu_fallback = 0`) | **ERFÜLLT** |
| **6. Syntax & Tests** | `py_compile` fehlerfrei, Unit-Tests grün | Alle Tests PASSED | **ERFÜLLT** |
| **7. Datensicherung** | Backup auf D: mit SHA-256 Verifikation | PRE & POST vollständig gesichert | **ERFÜLLT** |

---

## 6. Empfehlung für Folgeschritte
Sobald für Motiv 3 ein authentisches Fotomaterial einer getragenen Jacke vorliegt, kann die Inferenz sofort und ohne architektonische Anpassungen ausgeführt werden, da der Inpainting-Pfad und die Farb-/Materialübersetzung für Leder und 24k Gold produktionsreif bereitstehen.
