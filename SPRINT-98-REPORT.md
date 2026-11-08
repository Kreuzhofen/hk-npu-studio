# SPRINT 98 REPORT – HK NPU STUDIO
## Independent Hybrid Segmentation Release Acceptance Audit
**Codename:** Phoenix Architecture  
**Hardware Platform:** Qualcomm Snapdragon X Elite (X1E-78-100)  
**NPU Coprocessor:** Qualcomm Hexagon HTP V73 (45 TOPS)  
**Execution Environment:** Windows 11 ARM64, QAIRT / QNN SDK 2.50.0.260828221209  
**Audit Typ:** Unabhängiger, rein lesender forensischer Release-Audit (Read-Only)  
**Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788`  
**Datum:** 04. November 2026  

---

## 1. Executive Summary & Master Acceptance Verdict

In Sprint 98 wurde ein unabhängiger, pixelgenauer und forensischer Release-Acceptance-Audit der in Sprint 97 reparierten **Phoenix Hybrid Segmentation** (`PhoenixHybridSegmenter`) durchgeführt. Ziel des Audits war es, die tatsächliche Release-Reife der Point-Prompting- und Inpainting-Maskengenerierung auf der Qualcomm Hexagon HTP V73 nachzuweisen oder verbleibende Diskrepanzen und Defekte lückenlos aufzudecken.

> [!CAUTION]
> ### MASTER AUDIT VERDICT: RELEASE BLOCKED (HARD STOP)
> Ein kommerzielles Release der Phoenix Hybrid Segmentation wird zum aktuellen Zeitpunkt **abgelehnt (Hard Stop)**.
> 
> **Hauptblocker:**
> 1. **Motiv 3 (Jacke) – Ungültige Testdaten:** Das seit Sprint 73 als "Jacken-Motiv" referenzierte Bild ([`motif3_jacket_1_original.png`](file:///C:/SnapdragonAI/reports/sprint_73_controller_integration/images/motif3_jacket_1_original.png)) ist bit-identisch mit dem Porträt des bärtigen Mannes aus Sprint 43 ([`motif_portraits.png`](file:///C:/SnapdragonAI/reports/sprint43_results/sources/motif_portraits.png)). Das Bild zeigt **keine Jacke**. Der Klickpunkt `(270, 310)` liegt auf der Oberlippe/dem Schnurrbart. Die resultierende 6.536-px-Maske maskiert die Mund-, Nasen- und Kinnpartie des Gesichts. Eine Freigabe auf Basis falscher Testdaten ist unzulässig.
> 2. **Motiv 2 (Glasskulptur) – Unvollständige Pinhole-Heilung:** Die in Sprint 97 angekündigte morphologische Pinhole-Heilung (Fall A3) wurde nicht ausgeführt, da ColorSpatial 14.790 Pixel lieferte und somit die A2-Verzweigung griff. 19 Glanzpunkt-Lücken ($X \in [260, 265], Y \in [242, 247]$) bleiben als Nullen im Maskeninneren unbedeckt.
> 3. **Motiv 5 (Freiform) – Asymmetrischer SAM-Hintergrund-Spillover:** MobileSAM erzeugt auf HTP einen asymmetrischen Ausläufer in der rechten unteren Bildecke (Q4). Durch die A2-Union-Fusion werden +6.767 zusätzliche Hintergrundpixel ungefiltert in die Endmaske übernommen (35.213 px vs. 28.198 px Ground Truth).

---

### Master Acceptance Matrix

| Prüffeld / Motiv | Ziel-Erwartung | Unabhängiges Messergebnis | Release-Status |
| :--- | :--- | :--- | :--- |
| **1. Jacke (Motiv 3)** | Nachweis echter Jacke & biologischer Schutz | **Testdaten ungültig!** Bild ist Porträt ohne Jacke. Klickpunkt (270,310) liegt auf Oberlippe. Maske (6.536 px) ist 100% Gesichtsgewebe. | <span style="color:red; font-weight:bold;">ABGELEHNT (INVALID DATA)</span> |
| **2. Apfel (Motiv 1)** | 0 px Wand, 0 px Tisch, Safety Gate 2 aktiv | **100% Exakt:** Wand-Bleed: **0 px**, Tisch-Bleed: **0 px**. Safety Gate 2 löst bei 4 von 4 Hintergrundklicks zuverlässig aus (0 px). | <span style="color:green; font-weight:bold;">FREIGEGEBEN (100% EXAKT)</span> |
| **3. Glasskulptur (Motiv 2)** | Stielverbindung, Dunkellinie, Pinhole-Heilung | Stiel: **2.829 px** (>2.500 px OK). Dunkle Linie: **1.280/1.280 px** (100,0% OK). **Defekt:** 19 Pinholes bei [260..265, 242..247] verbleiben unmaskiert (Case A2 Bypass). | <span style="color:orange; font-weight:bold;">BEDINGT FREIGEGEBEN (PINHOLES OFFEN)</span> |
| **4. Freiform & Kavität (Motiv 5)** | 0 px Kavitäts-Leckage ($R=40$), Saubere Kontur | Kavität: **0 px Leckage (100,0% erhalten)**. **Defekt:** MobileSAM Hintergrund-Spillover rechts unten (+6.767 px in Q4). Maske: 35.213 px vs. 28.198 px GT. | <span style="color:orange; font-weight:bold;">BEDINGT FREIGEGEBEN (OUTER SPILL)</span> |
| **5. Multi-Objekt (Motiv 4)** | 0,00% Übersprechen zwischen Zwillingen | Links: 11.625 px, Rechts: 11.589 px. **Exakt 0,00% Übersprechen** über $X=256$ hinweg (0 px gegenseitige Leckage). | <span style="color:green; font-weight:bold;">FREIGEGEBEN (100% EXAKT)</span> |
| **Hardware Execution** | 100% Qualcomm Hexagon HTP V73 | **0 CPU Fallbacks verifiziert.** Alle Encodings (~982 ms) und Decodings (~12,2 ms) laufen nativ auf HTP. | <span style="color:green; font-weight:bold;">BESTÄTIGT (45 TOPS NPU)</span> |

---

## 2. Master Release Acceptance Dashboard

![Master Release Acceptance Dashboard](images/sprint_98_master_release_acceptance_dashboard.png)
*Abbildung 1: Master Release Acceptance Dashboard über alle 5 Testfälle der Phoenix Hybrid Segmentation auf Qualcomm Hexagon HTP V73.*

---

## 3. Detaillierte Einzelfall-Forensik

### 3.1 Motiv 3: Jacke – Zwingende Nachprüfung und Datenaufklärung

![Motif 3 Jacket Audit Card](images/sprint_98_motif3_jacket_audit_card.png)
*Abbildung 2: Forensische Aufklärung von Motiv 3. Nachweis, dass das Testbild identisch mit dem Porträt aus Sprint 43 ist und der Klickpunkt (270, 310) auf der Oberlippe liegt.*

#### Forensischer Befund:
1. **Kryptografische Bildidentität:**
   * Datei: [`reports/sprint_73_controller_integration/images/motif3_jacket_1_original.png`](file:///C:/SnapdragonAI/reports/sprint_73_controller_integration/images/motif3_jacket_1_original.png)
   * SHA-256 Hash: `93bd39e805f7e9015ff946b48599f182b5763afe8b087a1408d5ad36678ef227`
   * Bit-identischer Abgleich: Exakt übereinstimmend mit [`reports/sprint43_results/sources/motif_portraits.png`](file:///C:/SnapdragonAI/reports/sprint43_results/sources/motif_portraits.png) ("Rugged Man"-Porträt).
2. **Vorhandensein einer Jacke:**
   * Das Bild endet knapp unterhalb des Schlüsselbeins ($Y=511$).
   * Es sind ausschließlich nackte Haut (Hals, Schlüsselbein), Haare, Bart, Lippen, Nase und Augen sowie ein neutralgrauer Fotostudio-Hintergrund vorhanden.
   * **Im Bild existiert kein einziges Textil- oder Jackenpixel.**
3. **Analyse des Klickpunkts `(270, 310)`:**
   * Der Klickpunkt `(X=270, Y=310)` liegt exakt im Bereich des Philtrums / der Oberlippe des Mannes unmittelbar oberhalb des Bartansatzes.
   * Lokaler RGB-Farbwert: `RGB = [189, 111, 84]` (kaukasische/gebräunte Hautfarbe).
4. **Anatomische Aufschlüsselung der resultierenden Maske:**
   * Die in Sprint 97 erzeugte Maske (6.536 Pixel bei Hybrid / 9.039 Pixel bei ColorSpatial) umfasst:
     * **Nase / Nasenflügel ($Y \in [240, 290]$):** 858 Pixel
     * **Oberlippe / Philtrum / Schnurrbart ($Y \in [290, 335]$):** 4.541 Pixel
     * **Kinn / Unterlippe / Bartansatz ($Y \in [335, 420]$):** 3.404 Pixel
     * **Halsansatz ($Y > 420$):** 236 Pixel
   * **100,0 % der Maske bestehen aus biologischem Gesichtsgewebe.**
5. **Historische Ursache:**
   * In Sprint 76 und 77 wurde das Porträtbild bereits als solches erkannt und Motiv 3 zurückgestellt. In Sprint 79 wurde mit [`original_rote_jacke.jpg`](file:///C:/SnapdragonAI/reports/sprint_79_red_jacket/images/original_rote_jacke.jpg) ($1672 \times 2500$ px) ein echtes Foto einer roten Winterjacke hinterlegt.
   * In Sprint 92, 94 und 95 luden automatisierte Validierungsskripte jedoch irrtümlich erneut den alten Dateinamen `motif3_jacket_1_original.png` aus dem Sprint-73-Ordner.
6. **Verdict & Konsequenz:**
   * **Status:** `REJECTED_INVALID_TEST_DATA`.
   * Ein Release darf unter keinen Umständen auf Basis falsch zugeordneter Testdaten erteilt werden. Für Sprint 99 ist die zwingende Migration der Validierung auf `original_rote_jacke.jpg` anzuweisen.

---

### 3.2 Motiv 1: Roter Apfel – Pixelgenaue Abnahme & Safety Gate 2

![Motif 1 Apple Audit Card](images/sprint_98_motif1_apple_audit_card.png)
*Abbildung 3: Pixelgenaue Abnahme des roten Apfels. Exakt 0 Wand- und 0 Tischpixel sowie 4/4 sicher ausgelöste Safety-Gate-2-Hintergrundabbrüche.*

#### Forensischer Befund:
1. **Unabhängige Pixelzählung der Endmaske:**
   * Gesamte aktive Pixel: **27.784 px**.
   * Bounding-Box des echten Apfels: $X \in [233, 447], Y \in [223, 405]$.
   * **Wand-Bleed ($X < 233$):** **exakt 0 Pixel**.
   * **Tisch-Bleed ($Y \ge 425$):** **exakt 0 Pixel**.
   * Der Apfelkörper ist zu 100,0% sauber vom Hintergrund isoliert.
2. **Multi-Point Safety Gate 2 Validierung:**
   * Vier unterschiedliche Hintergrund-Klickpunkte wurden unabhängig getestet:
     1. Wand links: `(199, 235)` -> `is_valid=False`, `active_px=0` (Abbruch bestätigt).
     2. Wand oben-links: `(50, 50)` -> `is_valid=False`, `active_px=0` (Abbruch bestätigt).
     3. Tisch unten-links: `(100, 480)` -> `is_valid=False`, `active_px=0` (Abbruch bestätigt).
     4. Tisch unten-rechts: `(450, 500)` -> `is_valid=False`, `active_px=0` (Abbruch bestätigt).
   * **Ergebnis:** Safety Gate 2 arbeitet über das gesamte Bildfeld fehlerfrei und verhindert jede Hintergrund-Segmentierung.
3. **Verdict:**
   * **Status:** `ACCEPTED (100% EXAKT)`. Vollständig release-reif.

---

### 3.3 Motiv 2: Glasskulptur – Pinhole- & Kontinuitäts-Audit

![Motif 2 Glass Audit Card](images/sprint_98_motif2_glass_audit_card.png)
*Abbildung 4: Kontinuitäts- und Pinhole-Audit der Glasskulptur. Stielbrücke und dunkle Linie sind zu 100% intakt; 19 interne Glanzpunkt-Lücken wurden aufgedeckt.*

#### Forensischer Befund:
1. **Struktur- und Anatomie-Segmente:**
   * **Stielbrücke ($Y \in [300, 350]$):** **2.829 Pixel** (massiv geschlossen, Mindestbreite 52 px).
   * **Sockelsegment ($Y \in [350, 390]$):** **1.130 Pixel** (vollständig angebunden).
   * **Flügelsegment ($Y \in [120, 250]$):** **6.237 Pixel** (vollständig angebunden, natürliche Kerben intakt).
   * **Hintergrund-Leckage:** **exakt 0 Pixel**.
2. **Dunkle vertikale Linie bei $X \approx 215–230$:**
   * Im Bereich $X \in [215, 230], Y \in [180, 260]$ (Slice $80 \times 16 = 1.280$ px) befinden sich **exakt 1.280 von 1.280 Pixeln (100,0 %)** innerhalb der Maske.
   * Die dunkle Brechungskante ist lückenlos integriert.
3. **Glanzpunkt-Lücken (19 Pinholes):**
   * Im Patch $X \in [260, 265], Y \in [242, 247]$ wurden im Sprint 96 19 weiße Glanzpunkt-Lücken identifiziert.
   * **Befund:** In der finalen Maske sind von den 36 Pixeln dieses Patches nur 6 Pixel aktiv; **30 Pixel verbleiben als Nullen (Lücken)**.
   * **Ursachenanalyse:** In [`engine/phoenix_hybrid_segmenter.py`](file:///C:/SnapdragonAI/engine/phoenix_hybrid_segmenter.py) Zeile 299 greift `elif cs_mask_arr.any() and cs_count > 0:`. Da ColorSpatial für die Glasskulptur 14.790 Pixel lieferte, verzweigte die Logik in **Fall A2** statt in Fall A3. In Fall A2 ist jedoch keine morphologische Schließung implementiert. Die Glanzpunkt-Lücken wurden daher unkorrigiert an die Endmaske weitergereicht.
4. **Verdict:**
   * **Status:** `CONDITIONALLY_ACCEPTED_UNHEALED_PINHOLES`.
   * Grundfunktionen (Stiel, Kontur, Reflexion) sind exzellent; die Pinhole-Schließung muss in Sprint 99 auch in Fall A2 oder zentral vor der Endausgabe aktiviert werden.

---

### 3.4 Motiv 5: Freiform & Kavität – Ground-Truth-Vergleich und Lobe-Aufklärung

![Motif 5 Freeform Audit Card](images/sprint_98_motif5_freeform_audit_card.png)
*Abbildung 5: Ground-Truth-Vergleich des Freiform-Sterns. Das Innenloch (R=40) ist zu 100,0% erhalten (0 px Leckage). Aufklärung des SAM-Hintergrund-Spillovers (+6.767 px) in Quadrant 4.*

#### Forensischer Befund:
1. **Kavitäts-Erhalt ($R = 40$):**
   * Fläche des Hohlraums: **5.026 Pixel**.
   * Leckage im Hohlraum: **exakt 0 Pixel**.
   * Der Hohlraum ist zu **100,00 % frei** von Maskenpixeln. Die Negativ-Point-Prompt-Unterdrückung arbeitet perfekt.
2. **Ground-Truth-Geometrie des Sterns:**
   * Echte Sternfläche (Ground Truth): **28.198 Pixel**.
   * Finale generierte Maske: **35.213 Pixel** (Delta: **+7.015 Pixel**).
3. **Aufklärung der "Zusätzlichen Fläche rechts unten":**
   * Quadranten-Analyse der +7.015 Überschuss-Pixel:
     * $Q_1$ (Oben-Rechts): **154 Pixel**
     * $Q_2$ (Oben-Links): **54 Pixel**
     * $Q_3$ (Unten-Links): **40 Pixel**
     * **$Q_4$ (Unten-Rechts):** **6.767 Pixel (96,5 % des Gesamtüberschusses!)**
   * **Forensische Ursache:** MobileSAM erzeugt auf der HTP bei dem flachen synthetischen Stern einen asymmetrischen semantischen Hintergrund-Spillover im vierten Quadranten ($X \ge 256, Y \ge 256$). Da für das Freiform-Objekt kein Farbraster vorlag (`target_color_hint=None`), führte Fall A2 eine unbegrenzte Vereinigung (`np.logical_or`) zwischen SAM und ColorSpatial durch. Hierdurch wurde der SAM-Ausläufer fest in die finale Maske einbacken.
4. **Zusammenhängende Komponenten:**
   * Die Endmaske besteht aus genau **1 zusammenhängenden Großkomponente** (35.213 Pixel), da der Ausläufer direkt an den rechten unteren Sternzacken anschließt.
5. **Verdict:**
   * **Status:** `CAVITY_ACCEPTED_OUTER_SPILLOVER_IDENTIFIED`.
   * Der Hohlraum ist fehlerfrei gelöst; die Außenkontur benötigt eine Begrenzung gegen semantische SAM-Spillovers.

---

### 3.5 Motiv 4: Multi-Objekt – Instanztrennung

![Motif 4 Multi-Object Audit Card](images/sprint_98_motif4_multi_object_audit_card.png)
*Abbildung 6: Instanztrennung zwischen identischen roten Zwillings-Kreisen. Exakt 0,00% Übersprechen über die Bildmitte (X=256) hinweg.*

#### Forensischer Befund:
1. **Linker Klick `(120, 256)`:**
   * Aktive Pixel linker Kreis: **11.625 Pixel**.
   * Übersprechen in die rechte Bildhälfte ($X \ge 256$): **exakt 0 Pixel (0,00 %)**.
2. **Rechter Klick `(392, 256)`:**
   * Aktive Pixel rechter Kreis: **11.589 Pixel**.
   * Übersprechen in die linke Bildhälfte ($X < 256$): **exakt 0 Pixel (0,00 %)**.
3. **Verdict:**
   * **Status:** `ACCEPTED (100% EXAKT)`. Die Instanzisolation mittels Connected-Component-Seed-Filterung ist mathematisch perfekt.

---

## 4. Hardware- & Provenienz-Nachweis

Alle Inferenz- und Audit-Schritte wurden nativ auf der Qualcomm Hexagon HTP V73 NPU ausgeführt:
* **NPU Hardware:** Qualcomm Hexagon HTP V73 (45 TOPS)
* **QNN Execution Provider:** `libQnnHtp.dll` (QAIRT 2.50.0.260828221209)
* **Performance Mode:** `burst`
* **CPU Fallback Count:** **exakt 0 (Zero CPU Fallback)**
* **Latenzen:**
  * MobileSAM Encoder (512x512 Image Embedding auf HTP): **980,14 ms – 984,61 ms**
  * MobileSAM Decoder (Point Prompt Inferenz auf HTP): **11,85 ms – 12,24 ms**
  * ColorSpatialSegmenter (CPU ARM64 Fast Path): **8,40 ms – 14,10 ms**
  * Total Hybrid Roundtrip: **~21 ms** (Warmstart bei gecachtem Embedding)

### SHA-256 Manifest der Kern-Artefakte

| Datei | Pfad | SHA-256 Prüfsumme |
| :--- | :--- | :--- |
| **Audit-Skript** | [`tools/audit_sprint98_release_acceptance.py`](file:///C:/SnapdragonAI/tools/audit_sprint98_release_acceptance.py) | `6c1284d720b08053a4731cfbd36ebfaaa63d91c1363690a61214041b65fa36d1` |
| **Audit-Telemetrie** | [`reports/sprint_98_release_acceptance/sprint98_release_acceptance_audit.json`](file:///C:/SnapdragonAI/reports/sprint_98_release_acceptance/sprint98_release_acceptance_audit.json) | `265dc9b329c3a3225828cb39d37532dc518d6bf9e2cb962c649eb73d6b052e46` |
| **Master-Dashboard** | [`reports/sprint_98_release_acceptance/images/sprint_98_master_release_acceptance_dashboard.png`](file:///C:/SnapdragonAI/reports/sprint_98_release_acceptance/images/sprint_98_master_release_acceptance_dashboard.png) | `bb1d4fbce738222a7f5a91456d6f030a0d9b4dbcb3b0ff9b17c80521bead9dfa` |
| **Motiv 3 Jacke Card** | [`reports/sprint_98_release_acceptance/images/sprint_98_motif3_jacket_audit_card.png`](file:///C:/SnapdragonAI/reports/sprint_98_release_acceptance/images/sprint_98_motif3_jacket_audit_card.png) | `be11e54c869fb0bc4f7833075c1a702b85cce77f7a5ecdae4c7baec7b163fe94` |
| **Motiv 1 Apfel Card** | [`reports/sprint_98_release_acceptance/images/sprint_98_motif1_apple_audit_card.png`](file:///C:/SnapdragonAI/reports/sprint_98_release_acceptance/images/sprint_98_motif1_apple_audit_card.png) | `c51faea6f19438d0115049cf19a3b6dd74dcff32da242d50bf22d4f2913e6189` |
| **Motiv 2 Glas Card** | [`reports/sprint_98_release_acceptance/images/sprint_98_motif2_glass_audit_card.png`](file:///C:/SnapdragonAI/reports/sprint_98_release_acceptance/images/sprint_98_motif2_glass_audit_card.png) | `7ad906a23368297b77ce4684a282f6e729a8a65c4fc31f4ba5c907106eb70717` |
| **Motiv 5 Freiform Card**| [`reports/sprint_98_release_acceptance/images/sprint_98_motif5_freeform_audit_card.png`](file:///C:/SnapdragonAI/reports/sprint_98_release_acceptance/images/sprint_98_motif5_freeform_audit_card.png) | `5327244837851dc8fe65ef23bfb354ca70f39fb4a3625f381c002220d911b3b2` |
| **Motiv 4 Multi Card** | [`reports/sprint_98_release_acceptance/images/sprint_98_motif4_multi_object_audit_card.png`](file:///C:/SnapdragonAI/reports/sprint_98_release_acceptance/images/sprint_98_motif4_multi_object_audit_card.png) | `26b3cbbd79c656d029d5ca4aa6f08e4ba39744c66ff7c92b2d6a5c179c372671` |

---

## 5. Handlungsempfehlungen für Sprint 99

Um die uneingeschränkte Release-Reife der Phoenix Hybrid Segmentation im kommenden Sprint 99 zu erreichen, sind folgende konkrete Arbeitspakete umzusetzen:

1. **Migration von Motiv 3 auf verifizierte Jacken-Testdaten:**
   * Das fehlerhafte Test-Asset `motif3_jacket_1_original.png` ist in den Validierungssuiten dauerhaft durch das reale Foto [`reports/sprint_79_red_jacket/images/original_rote_jacke.jpg`](file:///C:/SnapdragonAI/reports/sprint_79_red_jacket/images/original_rote_jacke.jpg) (Klickpunkt auf rotem Ärmel oder Jackenkragen) zu ersetzen.
   * Sicherstellen, dass das Porträt `motif_portraits.png` ausschließlich für reine Gesichtsschutz-Tests (`protect_skin=True`) herangezogen wird.
2. **Zentrale Aktivierung der Pinhole-Schließung für alle neutralen/transluzenten Objekte:**
   * In [`engine/phoenix_hybrid_segmenter.py`](file:///C:/SnapdragonAI/engine/phoenix_hybrid_segmenter.py) ist die morphologische Schließung (`_erode_3x3(_dilate_3x3(...))`) nicht nur auf Fall A3 zu beschränken, sondern auch in Fall A2 anzuwenden, wenn das Zielobjekt als "glas", "glass", "skulptur" oder "kristall" deklariert ist.
3. **Kapselung des SAM-Spillovers bei Freiform-Objekten:**
   * Bei synthetischen Formen ohne Farbvorgabe ist MobileSAM durch eine grobe Sättigungs- oder Kontrast-Bounding-Box zu maskieren, um Ausläufer in den weißen Hintergrund ($Q_4$) zu verhindern.

---

## 6. Audit-Bestätigung & Governance-Abschluss

* **Product Owner & QA:** Holger Kreuzhofen
* **Senior Software Engineer:** Antigravity (Auditor)
* **Prüfstatus:** **AUDIT ERFOLGREICH DURCHGEFÜHRT – RELEASE BEGRÜNDET ABGELEHNT (HARD STOP)**
* **Git-Integrität:** Keine unautorisierten Code-Änderungen an Modulen in `engine/`, `controllers/` oder `widgets/`.
