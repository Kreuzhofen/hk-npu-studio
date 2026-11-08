# SPRINT 76 REPORT: PHOENIX PROMPT ENGINE – VISUAL TARGET & MASK AUDIT

**HK NPU STUDIO – Phoenix Architecture**  
**Qualcomm Snapdragon X Elite Hexagon NPU Platform**  
**Datum:** 03. November 2026  
**Status:** Audit vollständig abgeschlossen – Widersprüche und Fehlerursachen lückenlos aufgeklärt  
**Chief Software Architect:** ChatGPT  
**Senior Software Engineer:** Antigravity (Gemini)  
**Product Owner & QA:** Holger Kreuzhofen  

---

## 1. Executive Summary

In Sprint 76 wurde ein kompromissloses, pixelgenaues Read-only-Audit der in Sprint 74 und 75 erzeugten Masken, Prompts und HTP-Inferenzdaten durchgeführt. Anlass waren begründete Zweifel an der visuellen Plausibilität der Ergebnisse:
- Warum verformte sich der Apfel bei angeblichen 72,30 % Abdeckung zu einem unnatürlichen Goldklumpen?
- Warum deckte die angebliche „Jackenmaske“ in Sprint 75 Nase, Mund und Kinn des Porträts ab?
- Enthält das Porträt überhaupt eine Jacke?
- Wurden bei der Glasskulptur tatsächlich alle transparenten Randbereiche erfasst?

### Zentrale Audit-Ergebnisse auf einen Blick:

1. **Rote Jacke (`motif3_jacket`): Schwerwiegender Motiv- und Maskierungsfehler.**
   - **Befund:** Die Bilddatei `motif_portraits.png` enthält **überhaupt keine Jacke**. Es handelt sich um ein Passbild-artiges Nahaufnahme-Porträt eines bärtigen Mannes (*„Rugged Man“* aus Sprint 43).
   - **Gesichtsabdeckung:** Die in Sprint 75 von 3,46 % auf 24,91 % ausgeweitete Maske (BBox $y \in [229, 511], x \in [76, 461]$) deckt **Nasenrücken, Nasenspitze, Oberlippe, Mund, Unterlippe, Kinn, Bartstoppeln und Hals** ab.
   - **Inpainting-Ergebnis:** Dem Mann wurden Nase, Mund, Kinn und Hals mit schwarzer Ledertextur übermalt.
   - **Berichtsaussage:** Die Aussage im Sprint-75-Bericht (*„Gesicht vollständig geschützt, gesamte Jacke erfasst“*) ist **faktisch falsch**. Über 25.000 Gesichtspixel wurden überschrieben.

2. **Roter Apfel (`motif1_apple`): Massive Übersegmentierung in den Hintergrund.**
   - **Befund:** Der echte rote Apfel nimmt auf dem 512×512-Bild lediglich ca. **24.000 bis 28.000 Pixel (~9,1 % bis 10,7 %)** ein.
   - **72,30 % Maske:** Die Maske von 189.535 Pixeln überdeckte nicht nur den Apfel, sondern die **gesamte dunkle Holzwand/den Raumhintergrund** oberhalb des Tisches (Zeilen 0 bis 220), da dieser einen rötlich-braunen Grundton (Hue $\approx 15,1^\circ$) aufweist. 39,38 % der Maske (74.638 Pixel) waren reiner Hintergrund!
   - **Inpainting-Ergebnis:** Weil Stable Diffusion ein „24k Gold Apfel“-Objekt in ein gigantisches 72%-Maskenfeld generieren musste, entstand ein unförmiges Goldgebilde, das bis an die Bildränder wuchert.
   - **Hintergrundschutz:** Nur die untere Tischplatte ($y > 450$, 27,7 %) war geschützt. Der obere Raumhintergrund wurde komplett vernichtet.

3. **Grüne Glasskulptur (`motif2_glass`): Unvollständige Segmentierung (Teilverlust).**
   - **Befund:** Die 2,85 % Maske (7.482 Pixel) isoliert den Raumhintergrund zwar gut, erfasst die Skulptur aber **nur unvollständig**.
   - **Fehlende Bereiche:** Kopf und Schnabel ($y < 136$) wurden wegen starker Helligkeit/Entsättigung abgeschnitten. Der Sockel ($y > 339$) wurde wegen seines Zyan-/Teal-Farbtons (Hue $> 175^\circ$) verworfen. An den Flügelrändern fehlen 1.602 transparente Randpixel.
   - **Inpainting-Ergebnis:** Eine dreigeteilte Chimäre: Grüner Glaskopf + goldener Rumpf + zyanblauer Glassockel.

4. **Datenintegrität:**
   - Es wurden keine Läufe vermischt. Alle Dateien innerhalb von Sprint 73, Sprint 74 und Sprint 75 sind über SHA-256 kryptografisch sauber und konsistent nachverfolgbar.
   - Die Fehlannahmen entstanden historisch: In Sprint 72 wurde `motif_portraits.png` fälschlich als „Rote Jacke“ deklariert, ohne den Bildinhalt visuell zu verifizieren. In Sprint 75 wurden die Schwellenwerte blind hochgeschraubt, um eine rein rechnerische Zielgröße von ~25 % zu erzwingen.

---

## 2. Detaillierter Prüfbericht Motiv 3: „Rote Jacke“ (`motif3_jacket`)

### 2.1 Datei- und Hash-Zuordnung
- **Originaldatei:** `C:\SnapdragonAI\reports\sprint43_results\sources\motif_portraits.png`  
  - Abmessungen: $512 \times 512$ Pixel, RGB, 407.561 Bytes  
  - SHA-256: `93bd39e805f7e9015ff946b48599f182b5763afe8b087a1408d5ad36678ef227`
- **Maskendatei (Sprint 75):** `C:\SnapdragonAI\reports\sprint_75_mask_quality\images\motif3_jacket_3_binary_mask.png`  
  - Abmessungen: $512 \times 512$ Pixel, L, 1.937 Bytes  
  - SHA-256: `14a29322a4f60cc1c34a2e58a221f185ef3bf449fb0cf137fc3f0bc80fa5fe5a`
- **Ergebnisdatei (Sprint 75):** `C:\SnapdragonAI\reports\sprint_75_mask_quality\images\motif3_jacket_5_htp_result.png`  
  - Abmessungen: $512 \times 512$ Pixel, RGB, 386.937 Bytes  
  - SHA-256: `b5681b95a24d3b318d18b3cb30fe1a603c6218d867c29ae35451e06fe3f8a002`

### 2.2 Inhaltliche Verifikation des Ausgangsbildes
Die Rückverfolgung in das Quellarchiv `output/generate_1792859244_1137524_output.json` belegt zweifelsfrei den Ursprung des Bildes:
- **Generierungs-Prompt:**  
  `"award-winning cinematic portrait of a rugged man, intense gaze directly at camera, photorealistic skin texture, visible pores, rough stubble beard, fine glowing ember cracks along cheekbones, golden fiery rim lighting, dark moody background..."`
- **Referenzbild-Quelle:**  
  `"C:\Users\holge\Desktop\Testbilder\Passbild_Deutschland_35_x_45_mm_13082018_094501_DPI_566.jpg"`
- **Tatsächlicher Bildinhalt:**
  Das Bild zeigt die **Frontalaufnahme eines Mannes** vom Scheitel bis zum Hals-/Schlüsselbeinansatz.
  - Der Mann trägt **keine rote Jacke**.
  - Im unteren Bilddrittel sind lediglich der Hals, die Bartstoppeln und ein kleiner Ausschnitt eines neutral/dunklen Hemdkragens sichtbar.

### 2.3 Pixel-Audit der Gesichtsabdeckung
In Sprint 75 wurde die Maske mit BBox $y \in [229, 511]$ und $x \in [76, 461]$ generiert (65.311 Pixel = 24,91 %).  
Das Zentrum des Gesichts liegt bei $(x=256, y=256)$.

| Vertikale Koordinate | Anatomischer Bereich | RGB-Werte (Original) | Maskenstatus | Befund |
| :--- | :--- | :--- | :---: | :--- |
| $y = 100 \dots 220$ | Stirn, Augen, Schläfen | $[236, 171, 125]$ | `False` (Unmaskiert) | Stirn und Augen unberührt |
| $y = 240$ | Nasenrücken | $[231, 157, 112]$ | **`True` (Maskiert)** | **Maske schneidet mitten ins Gesicht** |
| $y = 270$ | Nasenspitze / Philtrum | $[232, 142, 111]$ | **`True` (Maskiert)** | **Nase vollständig in der Maske** |
| $y = 300 \dots 320$ | Oberlippe, Mund | $[210, 119, 83]$ | **`True` (Maskiert)** | **Mund vollständig in der Maske** |
| $y = 330$ | Unterlippe, Kinn | $[180, 105, 74]$ | **`True` (Maskiert)** | **Kinn vollständig in der Maske** |
| $y = 360 \dots 400$ | Bartstoppeln / Kiefer | $[226, 129, 100]$ | **`True` (Maskiert)** | **Kiefer und Bart in der Maske** |
| $y = 420 \dots 511$ | Hals, Schlüsselbein | $[199, 115, 81]$ | **`True` (Maskiert)** | **Hals vollständig in der Maske** |

### 2.4 Kausalitätskette des Fehlers
1. **Sprint 72:** Das Bild `motif_portraits.png` wurde willkürlich als Testbild für die Aufgabe *„Rote Jacke vor mehrfarbigem Hintergrund“* ausgewählt. Der Segmenter fand mangels Jacke nur 3,5 % rötliche Pixel (Kinn/Halsstoppeln).
2. **Sprint 74:** Die 3,46 % (9.070 Pixel) isolierten das Kinn.
3. **Sprint 75 (Fehlinterpretation):** Ohne visuelle Prüfung wurde angenommen, 3,46 % sei eine „Untersegmentierung einer Jacke“. Um künstlich ~25 % Abdeckung zu erreichen:
   - Wurde der Rot-Winkel in `COLOR_RANGES["red"]` auf bis zu $22,0^\circ$ erweitert.
   - Wurde `OBJECT_DEFAULT_SPATIAL` für `jacke` auf `"bottom"` gesetzt.
   - Da kaukasische/gebräunte menschliche Gesichtshaut und Lippen genau in den Farbtonwinkel $17^\circ \dots 22^\circ$ fallen, fraß sich die Maske über das gesamte Gesicht des Mannes.
4. **HTP-Inferenz:** Der Prompt lautete:  
   `"A photorealistic black leather Jacke, authentic fine leather grain texture, subtle specular highlights..."`  
   Die NPU übermalte die untere Gesichtshälfte des Mannes buchstabengetreu mit schwarzem Leder!

### 2.5 Urteil zu Motiv 3
> [!CAUTION]
> **Eindeutiges Audit-Urteil (Motiv 3):**  
> **Totaler Fehlschlag durch ungeeignetes Ausgangsmotiv und fatale Parameter-Eskalation.**  
> Das Bild enthält keine Jacke. Die Behauptung im Sprint-75-Bericht (*„Gesicht vollständig geschützt“*) ist widerlegt: Nase, Lippen, Mund, Kinn und Hals wurden maskiert und mit Ledertextur übermalt.  
> **Empfehlung für Sprint 77:** Das Motiv `motif3_jacket` muss durch ein reales Foto einer Person mit tatsächlicher Jacke ersetzt werden (oder die Porträtaufgabe muss wahrheitsgemäß auf Gesichtsmerkmale umgestellt werden).

---

## 3. Detaillierter Prüfbericht Motiv 1: „Roter Apfel“ (`motif1_apple`)

### 3.1 Datei- und Hash-Zuordnung
- **Originaldatei:** `C:\SnapdragonAI\reports\appl_edit_test_49\appl_edit_49_original.png`  
  - Abmessungen: $512 \times 512$ Pixel, RGB, 440.325 Bytes  
  - SHA-256: `61e14db93c80ea9f864cfb0e99d3eb84e4a775e523f668205f2abcf3681498b3`
- **Maskendatei (Sprint 75):** `C:\SnapdragonAI\reports\sprint_75_mask_quality\images\motif1_apple_3_binary_mask.png`  
  - Abmessungen: $512 \times 512$ Pixel, L, 2.854 Bytes  
  - SHA-256: `2147d6d4bea1afb639201f8d484439c2c62c2f42a5a549a175e119bf5fba2f26`
- **Ergebnisdatei (Sprint 75):** `C:\SnapdragonAI\reports\sprint_75_mask_quality\images\motif1_apple_5_htp_result.png`  
  - Abmessungen: $512 \times 512$ Pixel, RGB, 430.708 Bytes  
  - SHA-256: `5d6ea3258f2ebfab1263d5dd9a28fb60d1b31529ea4b4765aa370e51ee189914`

### 3.2 Maskenpolarität & tatsächliche Apfelfläche
- **Maskenpolarität:**
  - Wert `255` (Weiß): Inpainting-Zielbereich (wird durch Inferenz neu generiert).
  - Wert `0` (Schwarz): Geschützter Originalbereich (wird 1:1 unverändert übernommen).
  - Weiß-Pixel in Sprint 75: **189.535 Pixel = 72,30 %**.
  - Bounding Box der Weiß-Pixel: $y \in [0, 501], x \in [0, 511]$.
- **Reale geometrische Apfelfläche im Originalbild:**
  - Der echte Apfel liegt bei Zeilen $y \in [220, 400]$ und Spalten $x \in [290, 460]$.
  - Begrenzungsrechteck des echten Apfels: $180 \times 170 = 30.600$ Pixel.
  - Reale elliptische Apfelfläche: ca. **24.000 bis 28.000 Pixel (~9,1 % bis 10,7 % der Bildfläche)**.

### 3.3 Ursache der 72,30 % Übersegmentierung
- Oberhalb des Holztisches (Zeilen 0 bis 220) befindet sich eine dunkle Holzwand / Raumhintergrund.
- Diese Wand hat einen mittleren Farbton von **Hue $= 15,1^\circ$**, Sättigung $= 0,44$, Helligkeit $= 0,31$.
- Da in `ColorSpatialSegmenter` der Rotbereich auf $0^\circ \dots 22^\circ$ eingestellt war und kein `spatial_hint` vorlag, klassifizierte der Segmenter die gesamte Hintergrundwand als „rot“.
- **74.638 Pixel (39,38 % der gesamten Maske!)** entfallen auf den Raumhintergrund oberhalb des Tisches!

```
+-------------------------------------------------------------+
| Zeilen 0..220:   Dunkle Holzwand (Hue=15.1°)                |
|                  -> FÄLSCHLICH MASKIERT (100% Weiß)         |
+-------------------------------------------------------------+
| Zeilen 220..400: Echter Apfel (x: 290..460)                 |
|                  -> MASKIERT (Weiß)                         |
|                  Linker Bildbereich: Dunkler Hintergrund    |
|                  -> FÄLSCHLICH MASKIERT (Weiß)              |
+-------------------------------------------------------------+
| Zeilen 450..512: Heller Holztisch (Sättigung S=0.18 < 0.22) |
|                  -> Einziger geschützter Bereich (Schwarz)  |
+-------------------------------------------------------------+
```

### 3.4 Warum das HTP-Ergebnis deformiert ist
Beim Inpainting mit Prompt:  
`"A solid polished 24k Gold Apfel, sleek smooth curved metallic shape..."`  
generiert das UNet das gewünschte Objekt in das **gesamte weiße Maskenfeld**.  
Da das weiße Feld 72,30 % des Bildes umfasst und bis in die Ecken $(0,0)$ und $(0,511)$ reicht, versuchte das Modell einen riesigen, unnatürlichen Goldapfel über die gesamte Wand und Tischkante zu erzeugen. Das Resultat ist kein zentrierter Goldapfel auf einem Tisch, sondern eine diffuse, metallische Goldmasse, die die Komposition zerstört.

### 3.5 Urteil zu Motiv 1
> [!WARNING]
> **Eindeutiges Audit-Urteil (Motiv 1):**  
> **Massive Übersegmentierung in den Hintergrund.**  
> Der Apfel ist keineswegs „formatfüllend“ (er belegt nur ~10 % der Bildfläche). 39,4 % der Maske sind Hintergrundwand. Das HTP-Ergebnis ist deformiert, weil die Inpainting-Maske siebenmal größer als das eigentliche Zielobjekt war.  
> **Empfehlung für Sprint 77:** Kalibrierung über minimale Sättigung (`s_min >= 0.50` für Rot) oder Farbdifferenzierung zwischen Apfelrot und Hintergrundbraun, sodass die Maske strikt auf die ~26.000 Apfelpixel begrenzt wird.

---

## 4. Detaillierter Prüfbericht Motiv 2: „Grüne Glasskulptur“ (`motif2_glass`)

### 4.1 Datei- und Hash-Zuordnung
- **Originaldatei:** `C:\SnapdragonAI\reports\temp_motive_selection\m1_glass_512.png`  
  - Abmessungen: $512 \times 512$ Pixel, RGB, 328.443 Bytes  
  - SHA-256: `a179b11b19baa3b3b44b8ee34bc8ca184e62241b71d9d9e6e4f3ca4d2e7b51b3`
- **Maskendatei (Sprint 75):** `C:\SnapdragonAI\reports\sprint_75_mask_quality\images\motif2_glass_3_binary_mask.png`  
  - Abmessungen: $512 \times 512$ Pixel, L, 1.299 Bytes  
  - SHA-256: `4c84772708cd7d2ad5285741639f289899327d91e6047c0a9e701927702e8418`
- **Ergebnisdatei (Sprint 75):** `C:\SnapdragonAI\reports\sprint_75_mask_quality\images\motif2_glass_5_htp_result.png`  
  - Abmessungen: $512 \times 512$ Pixel, RGB, 329.226 Bytes  
  - SHA-256: `3ac64dd1c4b7aeb7ff590a56821213fe3a4f6154b5df16a75f5669bcfec19e7a`

### 4.2 Geometrische Abdeckung & Randbereich-Verlust
- **Maskenabdeckung:** 7.482 Pixel = **2,85 %**, BBox $y \in [136, 339], x \in [207, 284]$.
- **Tatsächliche physische Ausdehnung der Skulptur:**
  - Die Skulptur reicht vertikal von $y \approx 120$ (Kopf/Schnabelspitze) bis $y \approx 355$ (Sockel/Fuß).
  - Gesamthöhe der Skulptur: ca. 235 Pixel (statt der maskierten 203 Pixel).
- **Pixel-Audit der abgeschnittenen Bereiche:**
  1. **Kopf & Schnabel ($y = 120 \dots 135$):**  
     Pixel wie $(x=245, y=130)$ haben RGB $[229, 240, 172]$ (sehr helles, lichtdurchflutetes Glas). Durch die hohe Helligkeit ($V = 0,94$) und geringe Sättigung ($S = 0,28$) fielen diese Pixel durch das Raster $\to$ **Kopf blieb unmaskiert!**
  2. **Sockel & Standfuß ($y = 340 \dots 355$):**  
     Pixel wie $(x=245, y=345)$ haben RGB $[27, 114, 124]$ (bläulich-grünes Teal/Zyan mit Hue $\approx 185^\circ$). Da der Grün-Bereich bei $168^\circ$ endete, wurde der Sockel komplett verworfen $\to$ **Sockel blieb unmaskiert!**
  3. **Transluzente Randpixel:**  
     Entlang der Flügelkanten wurden 1.602 schwach gesättigte Glaspixel nicht erfasst.

### 4.3 Visuelle Auswirkung im HTP-Ergebnis
In `motif2_glass_5_htp_result.png`:
- $y \in [120, 135]$ (Kopf): Unverändertes grünes Originalglas.
- $y \in [136, 339]$ (Rumpf): Neu generiertes 24k Gold.
- $y \in [340, 355]$ (Sockel): Unverändertes blau-grünes Glas.
Die Skulptur wurde dadurch zu einer unfreiwilligen Dreifach-Chimäre.

### 4.4 Urteil zu Motiv 2
> [!NOTE]
> **Eindeutiges Audit-Urteil (Motiv 2):**  
> **Grundsätzlich richtige Größenordnung (~3–4 %), aber unvollständige Objekterfassung (Kopf und Sockel fehlen).**  
> Die Annahme aus Sprint 75, dass 2,85 % „fachlich vollkommen korrekt“ sei, stimmt nur hinsichtlich des Hintergrundschutzes. Das Objekt selbst wurde an den Extremitäten (Kopf $y<136$ und Sockel $y>339$) amputiert.  
> **Empfehlung für Sprint 77:** Öffnung des Grün-Bereichs nach Zyan (bis $190^\circ$) und Absenkung der Helligkeits-/Sättigungsschwellen für Glashighlights oder Einbeziehung einer Morphologie-/Dilation-Stufe, um Kopf und Sockel mitzunehmen (~3,6 % bis 4,0 % Gesamtabdeckung).

---

## 5. Datenintegritäts-Matrix (Sprint 73 vs. 74 vs. 75)

Um eine Vermischung von Datensätzen auszuschließen, wurden alle SHA-256 Prüfsummen across Sprints verglichen:

| Komponente | Motiv-ID | Sprint 73 SHA-256 (Präfix) | Sprint 74 SHA-256 (Präfix) | Sprint 75 SHA-256 (Präfix) | Integritätsstatus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Originalbild** | `apple` | `61e14db93c80...` | `61e14db93c80...` | `61e14db93c80...` | **100% Identisch** |
|  | `glass` | `a179b11b19ba...` | `a179b11b19ba...` | `a179b11b19ba...` | **100% Identisch** |
|  | `jacket` | `93bd39e805f7...` | `93bd39e805f7...` | `93bd39e805f7...` | **100% Identisch** |
| **Binäre Maske** | `apple` | `db8403728e9f...` (70,06%) | `db8403728e9f...` (70,06%) | `2147d6d4bea1...` (72,30%) | Konsistent geändert |
|  | `glass` | `7a9ede207f5b...` (2,55%) | `7a9ede207f5b...` (2,55%) | `4c84772708cd...` (2,85%) | Konsistent geändert |
|  | `jacket` | `a765f05f7a2c...` (3,46%) | `a765f05f7a2c...` (3,46%) | `14a29322a4f6...` (24,91%) | Konsistent geändert |
| **HTP-Ergebnis** | `apple` | `f7523681678f...` | `3e2a5d2c78cd...` | `5d6ea3258f2e...` | Echte Neuläufe |
|  | `glass` | `a66256e80dde...` | `fd7a89bc09eb...` | `3ac64dd1c4b7...` | Echte Neuläufe |
|  | `jacket` | `9165ff255549...` | `e96b30059dff...` | `b5681b95a24d...` | Echte Neuläufe |

**Fazit zur Datenintegrität:**
Keine Datensätze wurden unbemerkt vertauscht oder überschrieben. Die Dateien spiegeln präzise die jeweiligen Code-Stände wider. Das Problem lag nicht im Datenmanagement, sondern in falschen semantischen Grundannahmen über die Bildinhalte.

---

## 6. Gesamtfazit & Leitfaden für Reparatursprint 77

Sprint 76 hat alle offenen Widersprüche schonungslos aufgeklärt:

1. **Die Jacken-Illusion:** Es gibt im gesamten Repository für dieses Motiv kein Foto einer roten Jacke. Es wurde fälschlich ein Männerporträt verwendet, wodurch in Sprint 75 das Gesicht des Mannes zu 24,91 % mit Leder übermalt wurde.
2. **Die Apfel-Täuschung:** Der Apfel ist kein 72%-Makroobjekt. Die Maske absorbierte die gesamte Holzwand im Hintergrund, wodurch ein riesiges, deformiertes Goldgebilde entstand.
3. **Das Glaskunst-Fragment:** Die Glasskulptur wurde zu eng beschnitten; Kopf und Sockel blieben wegen Helligkeit und Zyan-Farbverschiebung grün, was zu einer Chimäre führte.

### Verbindliche Vorgaben für Sprint 77 (Reparatur):
1. **Motiv 3:** Bereitstellung eines echten Testbildes mit einer tatsächlich sichtbaren roten Jacke oder Anpassung des Testmotives auf eine valide Porträt-Retuscheaufgabe.
2. **Motiv 1:** Re-Kalibrierung des Segmenters, sodass nur der tatsächliche Apfel (~10 % bzw. ~26.000 px) maskiert wird und der Hintergrund unberührt bleibt.
3. **Motiv 2:** Ausweitung der Skulpturenmaske auf Kopf ($y=120..136$) und Sockel ($y=339..355$) auf ca. 3,8 % Gesamtabdeckung.
4. **Sicherheit:** Erst nach erfolgreicher Validierung dieser drei Punkte erfolgt eine erneute HTP-Inferenz.
