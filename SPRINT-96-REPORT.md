# SPRINT 96 FORENSIC AUDIT REPORT – HK NPU STUDIO: HYBRID MASK FORENSIC AUDIT

**Datum:** 2026-11-04  
**Hardware:** Qualcomm Snapdragon X Elite (X1E-78-100)  
**NPU-Target:** Qualcomm Hexagon HTP V73 (45 TOPS)  
**Software-Stack:** QAIRT 2.50.0.260828221209 / ONNX Runtime QNN 1.27.0 (QNN 2.47/2.50)  
**Repository:** `C:\SnapdragonAI`  
**Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert)  
**Prüfmodus:** **Reiner Read-Only-Audit (HARD STOP – Keine Reparaturen am Produktionscode)**  

---

## 1. Executive Summary & Forensische Hauptbefunde

Im Rahmen von Sprint 96 wurde eine lückenlose, pixelgenaue forensische Untersuchung der in Sprint 95 erzeugten Rohmasken, Bildüberlagerungen, Messwerte und Integritätsnachweise durchgeführt.

Die forensische Analyse klärt alle Widersprüche zwischen den numerischen Behauptungen des Sprint-95-Berichts und der tatsächlichen visuellen Darstellung vollständig auf:

| Untersuchungsfeld | Behaupteter Sprint-95-Status | Tatsächlicher forensischer Befund | Diskrepanzursache / Root Cause |
| :--- | :--- | :--- | :--- |
| **1. Apfel: Wand- & Tisch-Ausschluss** | „0 px Tisch- und Wand-Spillover, 64.438 px Apfelkörper“ | **36.648 Fremdpixel (56,9 % der Maske sind Wand!)**; nur 27.790 px sind echter Apfel. | **Falscher Klickpunkt:** $(199, 235)$ liegt bei $X=199$ links außerhalb des Apfels ($X_{\min}=233$) in der rötlich-braunen Wand. Die gelbe Hintergrundfläche ist die 45%-Tönung dieser 36.648 Wandpixel! |
| **2. Jacke: Gesicht- & Hautschutz** | „100% Ausschluss von Hose, Gesicht, Haut (0 px Leakage)“ | **1.334 Gesichtspixel** ($Y \in [180, 220]$) und **1.115 Halspixel** ($Y \in [220, 250]$) in der Maske! | **Metrik-Blindspot & Filterfehler:** Der Test prüfte nur $Y < 170$ (Stirn/Augen). Die Hautschutzbedingung `(r - g) < 80.0` schlug bei warmen Wangen/Kinn (`r - g >= 80`) fehl. |
| **3. Glasskulptur: Struktur & Linie** | „15.535 px, kohärent verbunden, kein Hintergrundrauschen“ | **Bestätigt:** 15.534 px als einzelne zusammenhängende Großkomponente; Sockelbrücke 2.948 px ($Y=300..350$). | Dunkle Linie bei $X \approx 215–230$ liegt zu **100,0 % (1.280/1.280 px)** innerhalb der Maske (kein Artefakt). 19 winzige Glanzpunkt-Lücken. |
| **4a. Multi-Objekt: Instanztrennung** | „0,00 % Übersprechen zwischen identischen Objekten“ | **Bestätigt:** Exakt **0 px Übersprechen** über die Mittellinie ($X=256$) hinweg bei beiden Einzelklicks. | Perfekte Instanzisolation durch Connected-Component-Filterung. |
| **4b. Freiform: Kavitätenerhalt** | „100 % Kavitätenerhalt (0 px Center Leakage, 0 px Spill)“ | **3.840 Leckagepixel im Hohlraumring ($15 < r \le 40$)!** Nur der Kern $r \le 15$ wurde gelöscht. | **Falsche Radiusbegrenzung:** Weil SAM das Loch füllte, war `was_fg == True`. Der BFS brach fälschlich bei $r > 15$ ab. Der Test maß nur ein 10-px-Fenster ($r \le 10$). |
| **5. Laufzeiten: 331 ms vs. 1.146–1.305 ms** | „12,19 ms Decoder, 331,80 ms Hybrid, 1.146–1.305 ms Total“ | **Vollständig aufgeklärt:** 1.021 ms = einmaliger TinyViT-Encoder-Kaltstart; 12,19 ms = reiner NPU-Decoder; 331 ms = Warmstart-Abfrage. | **0 CPU Fallbacks:** QNN HTP V73 Graph-Sequenzierung verifiziert (`disable_cpu_ep_fallback: 1`). Konfidenzen $> 1.0$ rühren aus unbegrenztem MSE-MLP-Kopf. |

---

## 2. Detaillierte Forensik der 5 Prüffelder

### 2.1 Motiv 1: Apfel – Aufklärung der gelben Hintergrundfläche

![Apple Forensic Breakdown](images/sprint_96_apple_forensic_breakdown.png)

#### Forensischer Befund:
1. **Lage des echten Apfels:**
   * Anhand der referenzgeprüften Sprint-87-Maske ([`motif1_apple_corrected_mask.png`](file:///C:/SnapdragonAI/reports/sprint_87_final_color_correction/images/motif1_apple_corrected_mask.png)) liegt der physische Apfel exakt im Koordinatenbereich:
     $$X \in [233, 447], \quad Y \in [223, 405]$$
   * Echte Apfelfläche: **27.790 Pixel**.
   * Zentrum des Apfels: $(X \approx 340, Y \approx 314)$.
2. **Lage des verwendeten Klickpunkts:**
   * In Sprint 94 und 95 wurde der Klickpunkt $(199, 235)$ verwendet.
   * Da $X = 199 < 233$, befindet sich der Klickpunkt **außerhalb des Apfels in der rötlich-braunen Hintergrundwand**!
3. **Pixelaufschlüsselung der 64.438 Maskenpixel:**
   * **Echte Apfelpixel:** **27.790 px** (100,0 % des Apfels wurden miterfasst).
   * **Fremdpixel (Wand links vom Apfel):** **36.648 px** (**56,9 % der Gesamtmaske sind Hintergrundwand!**).
   * Tisch-Spillover ($Y > 425$): **0 px** (die vertikale Kapselung auf $Y \le 421$ schnitt den Tisch zwar ab, ließ aber die gesamte Wand links vom Apfel passieren).
4. **Ursache der gelben Hintergrundfläche:**
   * In [`run_sprint95_hybrid_validation.py`](file:///C:/SnapdragonAI/tools/run_sprint95_hybrid_validation.py) Zeile 393 wurde `create_mask_overlay(..., tint_color=(255, 200, 30), alpha=0.45)` aufgerufen.
   * Die 36.648 fälschlich maskierten Wandpixel wurden mit 45 % Goldgelb überlagert, was visuell zu der massiven gelben Wandfläche führte.
5. **Gegenprobe bei echtem Klickpunkt $(340, 314)$:**
   * Bei Klick in das reale Apfelzentrum beträgt die Maskengröße **28.439 px** (27.790 px echter Apfel + 649 px weiche Kante, 0 px Wand).

---

### 2.2 Motiv 2: Rote Jacke – Gesichts- und Halsüberlappung

![Jacket Forensic Breakdown](images/sprint_96_jacket_forensic_breakdown.png)

#### Forensischer Befund:
1. **Anatomische Aufschlüsselung der 16.205 behaupteten Pixel:**
   * **Echte Jacke (Brust, Schultern, Revers, Rumpf ab $Y \ge 250$):** **13.756 px** (84,9 %)
   * **Hals / Kehle ($Y \in [220, 250]$):** **1.115 px** (6,9 % Fremdüberlappung)
   * **Unteres Gesicht / Kinn / Wange ($Y \in [180, 220]$):** **1.334 px** (8,2 % Fremdüberlappung)
   * **Haare:** **0 px** (Haaransatz bei $Y < 80$ blieb frei)
   * **Hose / Beine:** **0 px** (das Porträtbild [`motif_portraits.png`](file:///C:/SnapdragonAI/reports/sprint43_results/sources/motif_portraits.png) endet bei $Y=512$ am Oberkörper; es sind keine Hosen im Bild vorhanden)
   * **Hände:** **0 px** (Hände sind im Bildausschnitt nicht sichtbar)
2. **Ursache des Test-Blindspots:**
   * In [`run_sprint95_hybrid_validation.py`](file:///C:/SnapdragonAI/tools/run_sprint95_hybrid_validation.py) Zeile 522 wurde die Gesichtsprüfung wie folgt implementiert:
     ```python
     face_leakage = int(fused_jacket_arr[:170, :].sum())
     ```
   * Diese Zeile prüfte ausschließlich die Zeilen $Y < 170$ (Stirn- und Augenbereich).
   * Die tatsächlichen Gesichtsanteile (Mund, Kinn, Wange) befinden sich zwischen $Y=180$ und $Y=220$. Dort lagen **1.334 aktive Maskenpixel**, die durch die $Y < 170$-Bedingung im Testprotokoll zu `0 px` verfälscht wurden!
3. **Ursache des Versagens von `_protect_biological_tissue`:**
   * In [`engine/color_spatial_segmenter.py`](file:///C:/SnapdragonAI/engine/color_spatial_segmenter.py) Zeile 240:
     ```python
     is_skin = (r > 65.0) & (g > 0.42 * r) & (b > 0.25 * r) & (r > g) & (g > b) & ((r - g) < 80.0)
     ```
   * Bei gut ausgeleuchteter, sonnengebräunter oder rötlicher Haut im Kinn- und Wangenbereich liegt die Farbdifferenz $(r - g)$ bei durchschnittlich **86,26** ($r - g \ge 80.0$).
   * Die Bedingung `(r - g) < 80.0` stufte 4.170 dieser Hautpixel fälschlicherweise als rote Kleidung ein und schützte sie nicht.

---

### 2.3 Motiv 3: Glasskulptur – Komponenten & Kontinuität

![Glass Forensic Breakdown](images/sprint_96_glass_forensic_breakdown.png)

#### Forensischer Befund:
1. **Zusammenhängende Komponenten:**
   * Von den 15.535 Maskenpixeln entfallen **15.534 Pixel (99,99 %)** auf eine einzige, zusammenhängende Großkomponente.
   * Nur 1 einzelnes Pixel liegt als isoliertes Artefakt bei $(283, 265)$.
2. **Sockel- und Flügelverbindung:**
   * Die Verbindungsbrücke (Stiel) zwischen Körper und Sockel bei $Y \in [300, 350]$ ist **durchgehend geschlossen (2.948 Pixel)** mit einer Mindestbreite von 51 bis 74 Pixeln.
   * Flügelanteil ($Y \in [120, 250]$): **6.580 Pixel** (vollständig verbunden).
   * Sockelanteil ($Y \in [350, 390]$): **1.248 Pixel** (vollständig verbunden).
3. **Dunkle vertikale Linie bei $X \approx 215–230$:**
   * Der Bereich $X \in [215, 230], Y \in [180, 260]$ liegt zu exakt **100,0 % (1.280 von 1.280 Pixeln)** innerhalb der Maske.
   * Es handelt sich wie in Sprint 89 ermittelt um eine natürliche Reflexions- und Brechungskante des Glases, nicht um ein Inpainting- oder Maskierungsartefakt.
4. **Innenkonturen und Glanzpunkt-Lücken:**
   * Es wurden **19 Pixel** interne Lücken (Pinholes) bei $X \in [260, 265], Y \in [242, 247]$ festgestellt, die durch extreme Reflexions-Highlights (Weißausriss) entstanden sind.

---

### 2.4 Motiv 4: Multi-Objekt & Freiform-Kavitäten

![Freeform Cavity Forensic Breakdown](images/sprint_96_freeform_cavity_forensic_breakdown.png)

#### Forensischer Befund Multi-Objekt:
* Linker Klick $(120, 256)$: **11.657 Pixel**, rechte Bildhälfte ($X \ge 256$): **exakt 0 Pixel (0,00 % Übersprechen)**.
* Rechter Klick $(392, 256)$: **11.657 Pixel**, linke Bildhälfte ($X < 256$): **exakt 0 Pixel (0,00 % Übersprechen)**.
* **Ergebnis:** Die Multi-Objekt-Instanztrennung ist mathematisch perfekt.

#### Forensischer Befund Freiform & Kavität:
1. **Kavitäts-Dimension:**
   * Das zentrale Innenloch des synthetischen Sterns hat einen Radius von $R = 40$ px (Fläche: **5.026 Pixel**).
2. **Tatsächliche Maskierungsleckage im Hohlraum:**
   * Der Negativ-Klickpunkt $(256, 256)$ selbst ist `False` (0 px).
   * Der innere Kernbereich bis $r \le 15$ px (706 Pixel) wurde erfolgreich subtrahiert.
   * **Im äußeren Kreisring des Hohlraums ($15 < r \le 40$ px) verblieben jedoch 3.840 aktive Pixel in der Maske!**
3. **Ursache der Diskrepanz:**
   * In [`engine/phoenix_hybrid_segmenter.py`](file:///C:/SnapdragonAI/engine/phoenix_hybrid_segmenter.py) Zeile 291:
     Da MobileSAM das Innenloch im Ausgangstensor fälschlich geschlossen hatte, war `was_fg = bool(fused_arr[ny, nx])` beim Betreten des Negativ-Schritts `True`!
   * Dadurch griff fälschlicherweise die Schutzbedingung für Klicks auf Vordergrundobjekte:
     ```python
     if was_fg and ((adj_x - nx) ** 2 + (adj_y - ny) ** 2 > 15 ** 2): continue
     ```
   * Der Breitensuche-Flutungsalgorithmus wurde starr bei $r = 15$ px gekappt, anstatt die gesamte farbgleiche Kavität bis zur blauen Sternkante ($r = 40$ px) zu leeren!
4. **Ursache des Test-Blindspots:**
   * In [`run_sprint95_hybrid_validation.py`](file:///C:/SnapdragonAI/tools/run_sprint95_hybrid_validation.py) Zeile 603:
     ```python
     cavity_circle_sum = int(fused_freeform_arr[246:266, 246:266].sum())
     ```
   * Das Testfenster $[246, 265]$ prüfte nur einen Kasten von $\pm 10$ Pixeln um das Zentrum. Da der Kern bis $r=15$ leer war, meldete der Test `0 px Spill` und täuschte eine vollständige Hohlraumbefreiung vor, obwohl **3.840 Pixel (76,4 % des Innenlochs)** maskiert blieben!

---

### 2.5 Laufzeiten, HTP-Inferenz & Telemetrie

#### 1. Aufklärung der Latenzwerte (12 ms vs. 331 ms vs. 1.146–1.305 ms):
* **1.021,23 ms – TinyViT Image Encoder (Qualcomm Hexagon HTP):**
  * Wird nur **einmalig** beim Laden eines neuen Bildes ausgeführt.
  * Das resultierende 256-Kanal Feature-Embedding ($[1, 256, 64, 64]$) wird im Arbeitsspeicher gecacht.
* **12,19 ms – Transformer Mask Decoder (Qualcomm Hexagon HTP):**
  * Die reine hardwareseitige NPU-Ausführungszeit pro interaktivem Benutzerklick auf dem gecachten Embedding. Ermöglicht $> 80$ Interaktionen pro Sekunde.
* **~80–319 ms – Hybrid Postprocessing (ARM64 CPU):**
  * Farbraumanalyse, morphologisches Schließen, Connected-Component-Clustering, Sobel Edge-Snapping und Masken-Overlay-Generierung.
* **331,80 ms – Gesamte Warmstart-Interaktion:**
  * Decoder ($12\text{ ms}$) + Postprocessing ($\sim 320\text{ ms}$) bei Folgeklicks auf demselben Bild.
* **1.146–1.305 ms – Gesamte Kaltstart-Interaktion:**
  * Encoder ($1.021\text{ ms}$) + Decoder ($12\text{ ms}$) + Postprocessing ($\sim 113–272\text{ ms}$) beim allerersten Klick.

#### 2. Nachweis des reinen Hexagon-HTP-Betriebs (Zero CPU Fallback):
* In [`engine/backends/mobilesam_qnn_adapter.py`](file:///C:/SnapdragonAI/engine/backends/mobilesam_qnn_adapter.py) Zeile 133 ist zwingend konfiguriert:
  ```python
  opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
  ```
* Das QNN-Treiberprotokoll bestätigt die vollständige Sequenzierung auf HTP V73 ohne Fallback:
  * `Graph Preparation Initializing`
  * `Graph Optimizations`
  * `Graph Sequencing for Target (HTP V73)`
  * `VTCM Allocation`
  * `Finalizing Graph Sequence`
  * `DDR Bandwidth: spill_bytes=470790144, fill_bytes=460115968`
* Bei auch nur einem einzigen nicht unterstützten Operator hätte `disable_cpu_ep_fallback: 1` den Prozess mit einem fatalen Laufzeitfehler abgebrochen.

#### 3. Konfidenzwerte und IoU-Skalierung:
* Der MobileSAM IoU-Prediction-Head ist ein 3-Schichten-MLP, das mit MSE-Loss ohne Sigmoid-Aktivierung trainiert wurde.
* Bei kontrastreichen Objekten gibt das Modell rohe Werte von z. B. $1,0425$ ($104,25 \%$) aus.
* Das in Sprint 95 implementierte Clamping auf $\min(1.0, \max(0.0, \text{score}))$ ist mathematisch korrekt, um im UI saubere Wahrscheinlichkeiten darzustellen.

---

## 3. Governance- und Integritätsnachweis

* **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert).
* **Git-Status:** Keine Commits, keine Pushes, keine Staging-Änderungen.
* **Codebasis-Integrität:** Reiner Read-Only-Audit. Keine Modifikationen an Produktionscode oder Backends ausgeführt.
* **Drive D: Backups:**
  * PRE-Backup: `D:\HK_NPU_STUDIO_BACKUPS\SPRINT_95_HYBRID_SEGMENTATION_20261104\PRE\` (8/8 Dateien verifiziert).
  * POST-Backup: `D:\HK_NPU_STUDIO_BACKUPS\SPRINT_95_HYBRID_SEGMENTATION_20261104\POST\` (17/17 Dateien bit-identisch per SHA-256 verifiziert).

---

## 4. Handlungsempfehlungen für die separate Reparaturfreigabe (Sprint 97)

Auf Basis der forensischen Beweise werden folgende zielgerichtete Reparaturen für den Folge-Sprint empfohlen:

1. **Apfel (Klickpunkt-Korrektur):**
   * Den kanonischen Klickpunkt von $(199, 235)$ (Wand) auf das reale Apfelzentrum $(340, 314)$ korrigieren.
   * Farbraumbasierte Klickpunkt-Validierung: Warnt den Benutzer, wenn ein Klickpunkt außerhalb der Farb-Dominanz des gesuchten Objekts liegt.
2. **Jacke (Biologischer Schutz & Metrik):**
   * Die Hauterkennungsbedingung in `_protect_biological_tissue` von `((r - g) < 80.0)` auf einen adaptiven chrominanten Schwellenwert umstellen bzw. Hals und Gesicht per vertikaler Bounding-Box schützen ($Y < 235$ bei Apparel sperren, falls nicht explizit Halsband/Schal gewünscht).
   * Die Testmetrik in der Validierungssuite von `:170` auf `:240` korrigieren, um Mund und Kinn realistisch abzubilden.
3. **Freiform (Kavitäten-BFS):**
   * In `PhoenixHybridSegmenter` die Entscheidung `was_fg` nicht anhand der vom Modell fehlerhaft geschlossenen Maske treffen, sondern anhand der **tatsächlichen Farbabweichung des Klickpunkts im Originalbild** im Vergleich zum Vordergrund (`np.linalg.norm(img[pt] - fg_col) > threshold`). Liegt der Klickpunkt auf Hintergrundfarbe, wird der gesamte zusammenhängende Hohlraum ohne 15-px-Begrenzung befreit.
   * Das Validierungsfenster im Benchmark von $\pm 10$ px auf den vollen Kavitätsradius ($r \le 40$ px) erweitern.
4. **Glasskulptur:**
   * Morphologisches Schließen der 19 Glanzpunkt-Lücken.

---

## 5. Fazit

Der forensische Audit Sprint 96 hat die Ursachen aller visuellen und numerischen Diskrepanzen zweifelsfrei, mathematisch exakt und pixelgenau aufgedeckt. Es wurden keine unautorisierten Reparaturen vorgenommen. Die Codebasis verbleibt im stabilen, dokumentierten Zustand und ist bereit für die Freigabe der Reparaturmaßnahmen.
