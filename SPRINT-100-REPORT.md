# SPRINT 100 REPORT – HK NPU STUDIO
## Independent Final Release Acceptance Audit

**Projekt:** HK NPU STUDIO (Phoenix Architecture)  
**Sprint:** 100  
**Datum:** 2026-11-05  
**Rolle:** Senior Software Engineer (antigravity)  
**Chief Software Architect:** ChatGPT  
**Product Owner & QA:** Holger Kreuzhofen  
**Hardware-Ziel:** Qualcomm Snapdragon X Elite Hexagon NPU (HTP V73, 45 TOPS, INT8/W8A16, `disable_cpu_ep_fallback: 1`)  
**Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert)  
**Status:** **RELEASE BLOCKED (HARD STOP)**

---

## 1. Executive Summary & Master Release Verdict

In Sprint 100 wurde eine unabhängige, unvoreingenommene Endabnahme ("Final Release Acceptance Audit") der **Phoenix Hybrid Segmentation** auf der Qualcomm Hexagon HTP V73 NPU durchgeführt. Der Audit erfolgte streng read-only ohne Codeeingriffe oder Provisorien.

Die Auswertung der tatsächlichen Binärmasken und Referenzbilder ergab folgendes Gesamtergebnis:

| Testfall | Typ | Unabhängige Prüfkriterien | Audit-Befund | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Motif 1: Roter Apfel** | Farbig / Solide | 0 Wandpixel ($X < 233$), 0 Tischpixel ($Y \ge 425$), 4/4 Safety-Gate-2-Abweisungen | Wand: **0 px**, Tisch: **0 px**, Safety Gates: **4 / 4 abgewiesen (100%)**, Apfelkörper: **27.790 px** | **AUDIT_ACCEPTED** |
| **Motif 2: Glasskulptur** | Transluzent | 36/36 Pinholes im Patch `[242:248, 260:266]`, Stiel $> 2.500$ px, Reflexionslinie 100% | Patch: **36 / 36 px (100% geschlossen)**, Stiel: **2.842 px**, Dunkle Kante: **1.280 / 1.280 px (100,0%)** | **AUDIT_ACCEPTED** |
| **Motif 3: Rote Jacke** | Bekleidung / Porträt | Echtes Referenzbild (SHA-256 verifiziert), 0 Gesichts-/Hautgewebe-Leckage | Bild: `original_rote_jacke.jpg` ($1672\times2500$ px), SHA: `ea67e08e...`, Gesicht/Hals: **0 px**, Haut: **0 px** | **AUDIT_ACCEPTED** |
| **Motif 4: Multi-Objekt** | Disambiguierung | 0 Pixel gegenseitiges Übersprechen über $X = 256$ hinweg | Links: **11.589 px**, Rechts: **11.589 px**, Cross-talk: **0 px (0,00%)** | **AUDIT_ACCEPTED** |
| **Motif 5: Freiform & Kavität** | Freiform / Hohlraum | Kavität ($R \le 40$) vollständig frei und Außen-Spillover **exakt 0 Pixel** | Kavität: **0 px Leckage (100% frei)**, aber Außen-Spillover: **7 Pixel Extra** (3 in Q3, 4 in Q4) | **AUDIT_BLOCKED_SPILLOVER_DEVIATION** |

### Master Release Verdict: **RELEASE BLOCKED (HARD STOP)**

> [!WARNING]
> **Begründung der Freigabesperre:**  
> Während die Motive 1, 2, 3 und 4 sowie der innere Hohlraum von Motiv 5 die Release-Kriterien makellos erfüllen, verfehlt Motiv 5 die in Sprint 100 zwingend vorgegebene Nulltoleranz für den Außenbereich (**"Außen-Spillover exakt 0 Pixel"**). Die tatsächliche Binärmaske weist **7 Fremdpixel** außerhalb der Ground-Truth-Geometrie auf (Pixelkoordinaten siehe Abschnitt 2.5).  
> Gemäß Definition of Done (*"Eindeutiges Urteil RELEASE ACCEPTED oder RELEASE BLOCKED. Bei verbleibenden Abweichungen keine kommerzielle Freigabe"*) ist die kommerzielle Freigabe zu blockieren, bis der Product Owner über diese 7 Pixel entschieden hat.

---

## 2. Detaillierte forensische Auswertung der fünf Motive

### 2.1 Motif 1: Roter Apfel (Forensische Abnahme)
* **Referenzbild:** `reports/sprint_73_controller_integration/images/motif1_apple_1_original.png` ($512 \times 512$ px, SHA-256 `61e14db9...`).
* **Klickpunkt:** Kanonischer Punkt $(340, 314)$ im Apfelzentrum.
* **Pixelgenaue Segmentzerlegung:**
  - Apfelkörper ($X \ge 233, Y < 425$): **27.790 px** (Soll: $> 25.000$ px).
  - Wand-Spillover ($X < 233$): **exakt 0 px** (Soll: 0).
  - Tisch-Spillover ($Y \ge 425$): **exakt 0 px** (Soll: 0).
* **Multi-Point Safety Gate 2 Audit:**
  - $(199, 235)$ Wand links: `is_valid = False`, `active_pixel_count = 0` (Erfolgreich abgewiesen).
  - $(50, 50)$ Wand oben-links: `is_valid = False`, `active_pixel_count = 0` (Erfolgreich abgewiesen).
  - $(100, 480)$ Tisch unten-links: `is_valid = False`, `active_pixel_count = 0` (Erfolgreich abgewiesen).
  - $(450, 500)$ Tisch unten-rechts: `is_valid = False`, `active_pixel_count = 0` (Erfolgreich abgewiesen).
* **Befund:** **100% EXAKT. Vollständig freigegeben.**

### 2.2 Motif 2: Glasskulptur (Pinhole- und Struktur-Audit)
* **Referenzbild:** `reports/sprint_73_controller_integration/images/motif2_glass_1_original.png` ($512 \times 512$ px, SHA-256 `a179b11b...`).
* **Klickpunkt:** $(240, 240)$ auf dem Sockel/Korpus.
* **Glanzpunkt-Pinhole-Audit (Patch `[242:248, 260:266]`):**
  - Gesamtfläche des Test-Patches: 36 Pixel ($6 \times 6$).
  - Aktive Maskenpixel: **36 / 36 px** (100,0 % Deckung).
  - Ungeheilte Glanzpunkt-Pinholes: **0 px** (Soll: 0).
* **Strukturelle Integrität:**
  - Stielbrücke ($Y \in [300, 350]$): **2.842 px** (Massiv, Soll: $> 2.500$ px).
  - Dunkle Reflexionskante ($X \in [215, 230], Y \in [180, 260]$): **1.280 / 1.280 px** (100,0 % intakt).
  - Flügelkontur ($Y \in [120, 250]$): **6.339 px** (Vollständig erhalten).
* **Befund:** **PINHOLES GEHEILT, STRUKTUREN INTAKT. Vollständig freigegeben.**

### 2.3 Motif 3: Rote Jacke (Testdaten-Integrität & Anatomischer Schutz)
* **Referenzbild-Prüfung:**
  - Bildpfad: [original_rote_jacke.jpg](file:///C:/SnapdragonAI/reports/sprint_79_red_jacket/images/original_rote_jacke.jpg).
  - Abmessungen: $1672 \times 2500$ px (Originalauflösung).
  - SHA-256 Hash: `ea67e08e8792892ed8d3305444234b76e085e27531e9fec56a42cd96a29991db` (Bit-exakt verifiziert).
  - Abgrenzung: Keine Übereinstimmung mit dem alten Porträt-Mockup `motif3_jacket_1_original.png` (SHA-256 `93bd39e8...`). Es handelt sich um eine authentische Ganzkörperaufnahme mit roter Jacke.
* **Klickpunkt:** $(836, 1250)$ auf dem Jackenkorpus.
* **Anatomischer Gewebeschutz:**
  - Jacken-Maskierung: **152.174 px** solider Korpus.
  - Kopf-/Gesichtsregion ($Y < 635$): **exakt 0 px Leckage** (100% geschützt).
  - Unabhängiger Vollbild-Hautdetektor (HSV/RGB-Normierung): **exakt 0 px Hautgewebe** in der Maske.
* **Befund:** **AUTHENTISCHE TESTDATEN, 0 PX BIOLOGISCHE LEITUNG. Vollständig freigegeben.**

### 2.4 Motif 4: Multi-Objekt Disambiguierung (Instanztrennung)
* **Prüfaufbau:** Zwei identische rote Kreise ($R = 60$, RGB $[210, 30, 30]$) auf hellem Canvas ($RGB [240, 240, 240]$) bei $(120, 256)$ und $(392, 256)$.
* **Linker Klick $(120, 256)$:**
  - Linkes Objekt: **11.589 px**.
  - Übersprechen nach rechts ($X \ge 256$): **exakt 0 px** ($0,00\%$).
* **Rechter Klick $(392, 256)$:**
  - Rechtes Objekt: **11.589 px**.
  - Übersprechen nach links ($X < 256$): **exakt 0 px** ($0,00\%$).
* **Befund:** **VOLLKOMMENE INSTANZEN-ISOLATION (0,00% CROSS-TALK). Vollständig freigegeben.**

### 2.5 Motif 5: Freiform & Kavität (Pixelgenauer Ground-Truth-Abgleich)
* **Prüfaufbau:** 5-Zacken-Stern ($R_{\text{out}} = 160, R_{\text{in}} = 70$), zentrale Kavität ($R = 40$).
* **Punkte:** Positiver Klick $(256, 120)$, negativer Ausschluss $(256, 256)$.
* **Kavitäts-Audit ($R \le 40$):**
  - Gesamtfläche der inneren Kreiskavität: 5.025 px.
  - Maskenpixel innerhalb der Kavität: **exakt 0 px Leckage** (100,0 % Hohlraumerhalt).
* **Ground-Truth-Vergleich der Sterngeometrie:**
  - Ground Truth Sternfläche: 28.198 px.
  - Aktive Hybrid-Maske: 28.095 px.
  - True Positives (Übereinstimmung): 28.088 px ($99,61\%$).
  - False Negatives (fehlende Pixel): 110 px (Subpixel-Ecken der Sternspitzen).
  - **False Positives (Außen-Spillover): 7 Pixel**.
* **Quadranten-Aufschlüsselung der 7 Fremdpixel:**
  - Quadrant 1 ($X \ge 256, Y < 256$): **0 px**
  - Quadrant 2 ($X < 256, Y < 256$): **0 px**
  - Quadrant 3 ($X < 256, Y \ge 256$): **3 px**
  - Quadrant 4 ($X \ge 256, Y \ge 256$): **4 px**
* **Exakte Koordinaten und Farbwerte der 7 Fremdpixel:**

| Index | Koordinate $(X, Y)$ | Quadrant | Bild-Farbwert (RGB) | Ground Truth | Finale Maske |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | $(188, 277)$ | Q3 (Unten-Links) | $(245, 245, 245)$ [Hintergrund] | 0 (Hintergrund) | 1 (Maskiert) |
| 2 | $(188, 278)$ | Q3 (Unten-Links) | $(245, 245, 245)$ [Hintergrund] | 0 (Hintergrund) | 1 (Maskiert) |
| 3 | $(255, 327)$ | Q3 (Unten-Links) | $(245, 245, 245)$ [Hintergrund] | 0 (Hintergrund) | 1 (Maskiert) |
| 4 | $(323, 277)$ | Q4 (Unten-Rechts) | $(245, 245, 245)$ [Hintergrund] | 0 (Hintergrund) | 1 (Maskiert) |
| 5 | $(323, 278)$ | Q4 (Unten-Rechts) | $(245, 245, 245)$ [Hintergrund] | 0 (Hintergrund) | 1 (Maskiert) |
| 6 | $(256, 327)$ | Q4 (Unten-Rechts) | $(245, 245, 245)$ [Hintergrund] | 0 (Hintergrund) | 1 (Maskiert) |
| 7 | $(257, 327)$ | Q4 (Unten-Rechts) | $(245, 245, 245)$ [Hintergrund] | 0 (Hintergrund) | 1 (Maskiert) |

* **Ursachenanalyse:**
  Die 7 Fremdpixel liegen unmittelbar an den Spitzen des Sterns (bei $Y = 277..278$ und an der unteren Spitze bei $Y = 327$). Sie stammen aus der morphologischen Glättung (`_dilate_3x3` gefolgt von `_erode_3x3`) in `ColorSpatialSegmenter`, die in Fall A2 via `np.logical_or(sam_clean, cs_mask_arr)` in die Endmaske einfließt. MobileSAMs asymmetrischer Großflächen-Spillover von 7.015 px wurde zwar zu $99,94\%$ beseitigt, jedoch verbleiben diese 7 Pixel aus der Farbmodell-Randrundung im weißen Hintergrund.
* **Befund:** **ABWEICHUNG ZUM FREIGABEKRITERIUM (7 PX > 0 PX). Status: BLOCKED.**

---

## 3. Hardware- und Telemetrieprüfung (Qualcomm Hexagon HTP V73)

Alle fünf Motive wurden unabhängig auf dem Qualcomm Hexagon NPU Coprozessor (HTP V73) ohne CPU-Fallback ausgeführt:

* **Hardware-Target:** Qualcomm Snapdragon X Elite Hexagon HTP V73 (45 TOPS).
* **QNN Execution Provider Performance-Modus:** `burst`.
* **CPU Fallback Count:** **0** (Vollständige NPU-Ausführung, `disable_cpu_ep_fallback: 1`).
* **Inferenzlatenzen (MobileSAM Decoder/Encoder):**
  - Motif 1 (Apfel, $512\times512$): Decoder 995,78 ms.
  - Motif 2 (Glas, $512\times512$): Decoder 997,46 ms.
  - Motif 3 (Jacke, $1672\times2500$): Decoder 997,63 ms.
  - Motif 4 (Multi, $512\times512$): Decoder 994,01 ms.
  - Motif 5 (Freiform, $512\times512$): Decoder 986,23 ms.
* **Gesamtdauer des unabhängigen Audits:** 246,43 Sekunden.

Die maschinenlesbare Telemetrie ist abgelegt unter [sprint100_acceptance_telemetry.json](file:///C:/SnapdragonAI/reports/sprint_100_final_acceptance/sprint100_acceptance_telemetry.json).

---

## 4. Diskrepanzanalyse: Dashboard, Telemetrie-JSON und Binärmasken

Gemäß Prüfauftrag wurden die Daten aus Sprint 99 gegen die tatsächlichen Maskenwerte aus Sprint 100 abgeglichen:

1. **Dashboard vs. JSON:**  
   Die visuelle Differenzkarte auf der Sprint-99- und Sprint-100-Audit-Card weist den Text `Differenz: Extra=7 px (Q4=4 px)` korrekt aus. Es liegt keine grafische Verfälschung vor.
2. **Sprint 99 Bericht vs. Sprint 100 Kriterien:**  
   Im Sprint 99 Bericht wurde transparent dokumentiert: *"Q4-Spillover um 99.94% beseitigt (4 px vs. 7.015 px)"* und *"Gesamte Fremdpixel außerhalb der Ground Truth: 7 px"*. Sprint 99 hatte dies jedoch als "ACCEPTED_RELEASE_READY" bewertet, da eine 99,94%ige Reduktion als kommerziell ausreichend angesehen wurde.
3. **Konflikt mit dem Sprint-100-Auftrag:**  
   Der Prüfauftrag von Sprint 100 definiert die Anforderung nun explizit und unmissverständlich als **"Außen-Spillover exakt 0 Pixel"** und verknüpft dies mit der strikten Regel: **"Bei verbleibenden Abweichungen keine kommerzielle Freigabe"**.
   Da $7 \ne 0$ ist, führt die unveränderte Übernahme dieser 7 Pixel zwingend zur Nicht-Erfüllung des Kriteriums 5.

---

## 5. Forensische Bildnachweise & Dashboards

Alle Audit-Cards und das Master-Dashboard wurden unabhängig erzeugt und unter `reports/sprint_100_final_acceptance/images/` hinterlegt:

* **Sprint 100 Master Acceptance Dashboard:**  
  [sprint_100_master_acceptance_dashboard.png](file:///C:/SnapdragonAI/reports/sprint_100_final_acceptance/images/sprint_100_master_acceptance_dashboard.png)  
  *Gesamtübersicht aller fünf Audit-Karten mit rotem Master-Banner `RELEASE BLOCKED (HARD STOP)`.*
* **Motif 1: Roter Apfel (0 Wand, 0 Tisch, 4/4 Gates):**  
  [sprint_100_motif1_apple_card.png](file:///C:/SnapdragonAI/reports/sprint_100_final_acceptance/images/sprint_100_motif1_apple_card.png) (Status: FREIGEGEBEN)
* **Motif 2: Glasskulptur (36/36 Pinholes, Stiel & Kante intakt):**  
  [sprint_100_motif2_glass_card.png](file:///C:/SnapdragonAI/reports/sprint_100_final_acceptance/images/sprint_100_motif2_glass_card.png) (Status: FREIGEGEBEN)
* **Motif 3: Rote Jacke (Echtes Referenzbild, 0 Gesichts-/Hautgewebe):**  
  [sprint_100_motif3_jacket_card.png](file:///C:/SnapdragonAI/reports/sprint_100_final_acceptance/images/sprint_100_motif3_jacket_card.png) (Status: FREIGEGEBEN)
* **Motif 4: Multi-Objekt (0,00% gegenseitiges Übersprechen):**  
  [sprint_100_motif4_multi_object_card.png](file:///C:/SnapdragonAI/reports/sprint_100_final_acceptance/images/sprint_100_motif4_multi_object_card.png) (Status: FREIGEGEBEN)
* **Motif 5: Freiform & Kavität (Differenzkarte mit 7 Extra-Pixeln):**  
  [sprint_100_motif5_freeform_card.png](file:///C:/SnapdragonAI/reports/sprint_100_final_acceptance/images/sprint_100_motif5_freeform_card.png) (Status: ABWEICHUNG: 7 PX EXTRA)

---

## 6. Sicherung auf Festplatte D & SHA-256 Manifest

Alle Audit-Ergebnisse, Telemetriedaten und Dashboards wurden vollständig auf Festplatte D: gesichert:

* **Sicherungsverzeichnis:**  
  `D:\HK_NPU_STUDIO_BACKUPS\SPRINT_100_FINAL_ACCEPTANCE_20261105\`
* **Kryptografische Manifeste:**  
  - [MANIFEST_SHA256_SPRINT100.json](file:///D:/HK_NPU_STUDIO_BACKUPS/SPRINT_100_FINAL_ACCEPTANCE_20261105/MANIFEST_SHA256_SPRINT100.json)
  - [MANIFEST_SHA256_SPRINT100.txt](file:///D:/HK_NPU_STUDIO_BACKUPS/SPRINT_100_FINAL_ACCEPTANCE_20261105/MANIFEST_SHA256_SPRINT100.txt)

| Datei auf Festplatte D: | SHA-256 Prüfsumme | Größe (Bytes) |
| :--- | :--- | :--- |
| `sprint100_acceptance_telemetry.json` | `f6eb379497a2726b5b24...` | 7.866 |
| `images/sprint_100_master_acceptance_dashboard.png` | `9050500d5f5d1d088806...` | 425.880 |
| `images/sprint_100_motif1_apple_card.png` | `21c397a46fcedbafbcb3...` | 104.703 |
| `images/sprint_100_motif2_glass_card.png` | `002226ea40ec0ccd0ca0...` | 108.771 |
| `images/sprint_100_motif3_jacket_card.png` | `9b8ef422bf4e67e89e01...` | 108.019 |
| `images/sprint_100_motif4_multi_object_card.png` | `a4aba7247d1c8f65d970...` | 37.424 |
| `images/sprint_100_motif5_freeform_card.png` | `628971a68e57f12377d7...` | 49.538 |

---

## 7. Einhaltung der Governance & Definition of Done

1. **Reine Leseanalyse:**  
   Es wurden keinerlei Produktionsmodule (`engine/`, `controllers/`, `widgets/`) verändert. Der Quellcode ist bit-identisch zum Sprint-99-Zustand.
2. **Git-Status:**  
   Git HEAD ist unberührt auf `8784a43f5b7666f1007292393c6ea947b5cdd788`. Keine Commits, keine Pushes, keine externen Bibliotheken.
3. **Definition of Done:**  
   Ein unmissverständliches Urteil wurde gefällt. Das Urteil lautet begründet: **RELEASE BLOCKED**.

---

## 8. Empfehlung für Product Owner (Holger Kreuzhofen) & Software Architect (ChatGPT)

Zur Auflösung der Freigabesituation stehen dem Product Owner zwei saubere Wege offen:

* **Weg 1 (Technische Perfektionierung auf exakt 0 Pixel):**  
  In Fall A2 von `PhoenixHybridSegmenter` wird `cs_mask_arr` vor der Fusion mit der Farbkonsistenzmaske maskiert (`cs_mask_arr = cs_mask_arr & (color_dist < 50.0)`), sodass die 7 Randpixel der morphologischen Rundung vollständig abgeschnitten werden. Dies erfordert einen kurzen Sprint 101 mit anschließendem Release.
* **Weg 2 (Kommerzielle Ermessensfreigabe durch den Product Owner):**  
  Der Product Owner stuft 7 Pixel Randrundung bei 28.095 Pixel Gesamtmaskengröße ($0,025\%$ Abweichung) als vernachlässigbare Polygon-Rasterungstoleranz ein und erteilt die formale Produktivfreigabe für das Gesamtrelease.
