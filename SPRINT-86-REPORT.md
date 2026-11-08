# SPRINT 86 – PHOENIX PROMPT ENGINE: VISUAL RELEASE ACCEPTANCE

**Sprint-ID:** SPRINT-86-VISUAL-RELEASE-ACCEPTANCE-20261104  
**Datum:** 4. November 2026  
**Zielsystem:** Qualcomm Snapdragon X Elite (Windows 11 ARM64)  
**Prüfmodus:** **STRICT READ-ONLY AUDIT** (Keine Codeänderungen, keine Seeds verändert, kein Build)  
**Status:** **AUDIT ABGESCHLOSSEN – DIFFERENZIERTE RELEASE-ENTSCHEIDUNG**

---

## 1. Executive Summary & Management-Entscheidung

In Sprint 86 wurde eine schonungslose, rein visuelle und colorimetrische Abnahmeprüfung der drei kanonischen Motive aus Sprint 85 durchgeführt. Ziel war es, isolierte Messwerte zu hinterfragen und die tatsächliche optische Übereinstimmung zwischen **Prompt**, **visuellem Eindruck** und **technischer Messung** festzustellen.

### Ergebnisübersicht

| Motiv | Prompt | Visueller Gesamteindruck | Messbefund | Prompt-Ziel | Release-Entscheidung |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **1. Roter Apfel** | *„Verwandle den Apfel in 24k Gold.“* | Glänzendes Gold, aber **rechte Flanke zeigt noch eine deutlich sichtbare dunkle Schattenfurche** | $L_{\text{valley}} = 95.8$ zwischen zwei Glanzbereichen ($L \approx 215$ und $233$); Kontrast $1.35\times$ | **Teilweise** | **ABLEHNUNG / NACHARBEIT** |
| **2. Glasskulptur** | *„Verwandle die Glasskulptur in 24k Gold.“* | **Hervorragendes, homogenes Gold**; Sockel, Hals und Flügel glänzend; Naht bei $X=215$ verschwunden | Naht $X=215$: $L=156.0$ (Min $141.3$, 0 Px $<40$); Sockel $L=195.7$, RGB $[227, 195, 119]$ | **100%** | **FREIGEGEBEN** |
| **3. Rote Jacke** | *„Mache die rote Jacke zu schwarzem Leder.“* | **KRITISCHER FEHLER: Jacke ist WEINROT / BURGUNDY, KEINESWEGS SCHWARZ!** | Mean RGB $[161, 45, 60]$, $S=0.75$; **97.6% der Pixel sind rot-dominant**; nur 4.5% echtes Schwarz | **0% (Farbe)** | **STRIPTE ABLEHNUNG** |

> [!CAUTION]
> **Zentraler Audit-Befund zu Motiv 3 (Rote Jacke):**  
> Die Rote Jacke wurde in den bisherigen Sprints als „bestanden“ deklariert, weil der *Haut- und Hintergrundschutz* ($Diff = 0.0000$, 0 Pixel Gesichtsüberlappung) perfekt funktioniert. Eine colorimetrische Überprüfung offenbart jedoch, dass die Jacke im Ergebnis zu **97.64% rot-dominant** ist ($R=161.3, G=45.0, B=60.0$). Das Prompt-Ziel *„schwarzes Leder“* wurde farblich **vollständig verfehlt**.

---

## 2. Visuelle Nachweise (Master Diagnostic Cards)

### 2.1 Master Audit Card (Gesamtübersicht aller drei Motive)
![Master Audit Card](file:///C:/SnapdragonAI/reports/sprint_86_visual_release_acceptance/images/sprint_86_master_audit_card.png)

### 2.2 Spezifische Detail-Panels
- **Apfel-Schattenprofil (Original $\to$ Priming $\to$ HTP):**  
  [audit_apple_shadow_panel.png](file:///C:/SnapdragonAI/reports/sprint_86_visual_release_acceptance/images/audit_apple_shadow_panel.png)
- **Glasskulptur Morphologie-Vergleich (Original $\to$ HTP Seed 100):**  
  [audit_glass_structure_panel.png](file:///C:/SnapdragonAI/reports/sprint_86_visual_release_acceptance/images/audit_glass_structure_panel.png)
- **Jacken-Farbanalyse (Rot-Dominanz vs. Schwarz):**  
  [audit_jacket_color_panel.png](file:///C:/SnapdragonAI/reports/sprint_86_visual_release_acceptance/images/audit_jacket_color_panel.png)

---

## 3. Motiv 1: Roter Apfel – 24k Gold

### 3.1 Visuelle Bewertung
Betrachtet man das Endergebnis [`motif1_apple_polished_htp.png`](file:///C:/SnapdragonAI/reports/sprint_85_material_polish/images/motif1_apple_polished_htp.png) unvoreingenommen als menschlicher Betrachter, fällt sofort auf:
- Die linke Flanke und das Zentrum strahlen in wunderschönem 24k Gold ($L \approx 200..215$).
- Der rechte Außenrand zeigt ein metallisches Glanzlicht ($L \approx 233$).
- **Dazwischen (bei $X \approx 345..375$) liegt eine senkrechte, dunkle Zone**, die das Gold wie eingedrückt oder oxidiert/verschmutzt wirken lässt.
- Im Sprint 85 wurde berichtet, dass die minimale Luminanz von $54.2$ auf $87.7$ stieg und keine Pixel unter $80$ existieren. Das ist mathematisch korrekt, **aber visuell reicht ein Anheben auf $87.7$ nicht aus**, um den Schatten unsichtbar zu machen, wenn die umgebenden Flächen bei $215..233$ liegen!

### 3.2 Messdaten (Äquator-Scan bei $Y \in [300, 340]$)

| X-Koordinate | Bereich | $L_{\text{orig}}$ | $L_{\text{prim}}$ | $L_{\text{res}}$ | RGB-Ergebnis ($R, G, B$) | Visueller Eindruck |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **263** | Linker Rand (beleuchtet) | $50.2$ | $149.4$ | **$207.8$** | $[244.1, 207.3, 115.0]$ | Strahlendes Gold |
| **293** | Zentrum (beleuchtet) | $219.5$ | $214.5$ | **$215.0$** | $[255.0, 214.2, 114.5]$ | Reines Gold-Highlight |
| **323** | Rechter Übergang | $75.7$ | $213.4$ | **$213.6$** | $[251.7, 214.1, 110.9]$ | Helles Gold |
| **338** | Schatten-Eintritt | $63.6$ | $202.2$ | **$183.9$** | $[233.9, 180.1, 72.1]$ | Beginn Schattenflanke |
| **353** | **Schatten-Zentrum (Tal)** | **$47.3$** | **$174.4$** | **$95.8$** | **$[141.7, 88.0, 14.9]$** | **Dunkel-olivbraune Delle!** |
| **368** | Schatten-Ausgang | $49.5$ | $176.7$ | **$124.1$** | $[174.2, 118.5, 21.6]$ | Dunkles Gold |
| **383** | Wiederanstieg | $59.8$ | $182.6$ | **$173.2$** | $[213.2, 172.1, 73.4]$ | Aufhellung |
| **398** | Rechter Rand (Spitzlicht) | $182.1$ | $214.2$ | **$232.9$** | $[254.7, 236.1, 159.2]$ | Helles Randglanzlicht |

**Befund:** Bei $X=353$ bricht die Helligkeit auf **$L=95.8$** ein, während links davon $L=213.6$ und rechts davon $L=232.9$ anliegen. Dieses Helligkeitstal ($95.8$ vs. $220$) erzeugt ein Kontrastverhältnis von **$1:2.3$** innerhalb weniger Pixel. Das menschliche Auge nimmt dies unausweichlich als auffälligen Schattenstreifen wahr.

### 3.3 Prompt-Zielerreichung & Release-Entscheidung
- **Prompt:** *„Verwandle den Apfel in 24k Gold.“*
- **Zielerreichung:** **70%** (Goldmaterial etabliert, aber Glanzkonsistenz durch vererbten Kernschatten gestört).
- **Entscheidung:** **ABLEHNUNG (NACHARBEIT ERFORDERLICH)**.

### 3.4 Konkrete Reparaturempfehlung
1. In [`engine/material_priming.py`](file:///C:/SnapdragonAI/engine/material_priming.py) reicht die lineare Luminanz-Kompression auf `min_val = 145.0` nicht aus, weil das SD1.5-Inpainting-Modell bei $denoising = 0.75$ den verbleibenden Luminanz-Gradienten des Primings verstärkt ($L=174.4 \to L=95.8$).
2. **Lösung für Sprint 87:**
   - Erhöhung von `min_val` auf mindestens **$185.0$** für `24k_gold` ODER
   - Anwendung eines **morphologischen Glättungsfilters (Bilateral / Guided Filter)** auf die Masken-Vorschau in Zone V, der den diffusen Helligkeitsabfall der rechten Flanke vor der Inferenz komplett einebnet ($L_{\text{prim}} \ge 200$ über die gesamte Breite).
   - Testweise Anhebung der `denoising_strength` von $0.75$ auf **$0.82$** für glatte Metalloberflächen.

---

## 4. Motiv 2: Grüne Glasskulptur – 24k Gold

### 4.1 Visuelle Bewertung
Betrachtet man das Endergebnis [`motif2_glass_polished_htp.png`](file:///C:/SnapdragonAI/reports/sprint_85_material_polish/images/motif2_glass_polished_htp.png):
- Der in Sprint 84 diagnostizierte, pechschwarze Riss bei $X=215, Y \in [162, 269]$ ($L_{\text{min}} = 1.5..15.3$ bei Seed 42) ist bei Seed 100 **vollständig verschwunden**.
- Die Fläche bei $X=215$ ist homogen mit hellem Gold gefüllt ($L_{\text{mean}} = 156.0$, $L_{\text{min}} = 141.3$).
- Bei genauer Untersuchung fällt eine schmale, dunklere Kontur bei $X \approx 230..245$ auf ($L \approx 68..93$).
- **Strukturanalyse gegen das Originalbild [`motif2_glass_1_original.png`](file:///C:/SnapdragonAI/reports/sprint_80_total_validation/images/motif2_glass_1_original.png):**  
  Ein pixelgenauer Abgleich belegt zweifelsfrei: An exakt dieser Stelle ($X \approx 230..245$) besitzt die echte Glasskulptur die **skulptierte Fuge zwischen Rumpf und rechtem Flügel** ($L_{\text{orig}} \approx 91..107$). Es handelt sich hierbei **nicht um ein Inpainting-Artefakt**, sondern um die korrekte Wiedergabe der dreidimensionalen Objektmorphologie (Eigenschatten der Flügelkerbe).
- Der Sockel ($Y \ge 330$) ist lückenlos mit strahlendem 24k Gold bedeckt ($L = 195.7$, RGB $[226.9, 194.7, 118.6]$).
- Hals und Kopf ($Y \in [100, 160]$) sind gestochen scharf ausgebildet ($L = 200.3$).
- Der Tisch ($Y \ge 420$) und der umgebende Raum sind mit $Max Diff = 0.0000$ zu **100% bit-identisch** geschützt.

### 4.2 Messdaten

| Parameter | Sprint 84 (Seed 42) | Sprint 85/86 (Seed 100) | Bewertung |
| :--- | :---: | :---: | :--- |
| **Nahtlinie $X=215$ Min Luminanz** | $1.5$ | **$141.3$** | **$+9320\%$ (Beseitigt)** |
| **Nahtlinie $X=215$ Mean Luminanz** | $10.8$ | **$156.0$** | **$+1344\%$ (Homogen)** |
| **Dunkle Pixel ($L < 40$) in Nahtzone** | 27 | **0** | **Vollständig nahtlos** |
| **Sockel Mean Luminanz** | $153.2$ | **$195.7$** | **Reines 24k Gold** |
| **Sockel Mean RGB** | $[194, 156, 73]$ | **$[227, 195, 119]$** | **Sattes, warmes Gold** |
| **Hintergrund-Abweichung (Diff)** | $0.0000$ | **$0.0000$** | **Bit-identisch ($100\%$)** |
| **Tisch-Abweichung ($Y \ge 420$)** | $0.0000$ | **$0.0000$** | **Bit-identisch ($100\%$)** |

### 4.3 Prompt-Zielerreichung & Release-Entscheidung
- **Prompt:** *„Verwandle die Glasskulptur in 24k Gold.“*
- **Zielerreichung:** **100%** (Makellose Goldtransformation, Beseitigung aller Unstetigkeiten, Erhaltung der Skulpturenform).
- **Entscheidung:** **VOLLSTÄNDIGE FREIGABE (RELEASE ACCEPTED)**.

### 4.4 Konkrete Reparaturempfehlung
Keine Codeänderungen erforderlich. Die Kombination aus Seed 100 und den erweiterten Negativ-Prompt-Tokens in [`controllers/prompt_edit_controller.py`](file:///C:/SnapdragonAI/controllers/prompt_edit_controller.py) ist produktionsreif.

---

## 5. Motiv 3: Rote Jacke – Schwarzes Leder

### 5.1 Visuelle Bewertung
Betrachtet man das Bild [`motif3_jacket_polished_htp.png`](file:///C:/SnapdragonAI/reports/sprint_85_material_polish/images/motif3_jacket_polished_htp.png), wird der eklatante Widerspruch zwischen Prompt und Ergebnis offensichtlich:
- Die Person trägt **keine schwarze Lederjacke**.
- Die Person trägt eine **dunkelrote / weinrote (burgundy) Jacke**!
- Das Material besitzt zwar feine Lederfalten und Lederreflexe, aber die Grundfarbe ist unübersehbar **Rot**.
- **Warum wurde dieser Fehler bisher übersehen?**  
  In Sprint 80 und 85 lag der Fokus ausschließlich auf der *Segmentierungs- und Schutzvalidierung* (Verhinderung von Gesichtsveränderungen). Der Test prüfte nur: `face_overlap == 0` und `face_diff == 0.0`. Diese Schutzprüfung bestand mit Auszeichnung. Dass das Inpainting-Ergebnis innerhalb der Maske aber **rot** blieb, wurde in den automatisierten Reports nicht als Misserfolg gewertet.

### 5.2 Colorimetrische Messdaten (1.551.351 Pixel in Jackenmaske)

| Region der Jacke | Original RGB ($R, G, B$) | Ergebnis RGB ($R, G, B$) | Luminanz | Rot-Dominanz ($R > G+20 \land R > B+20$) |
| :--- | :---: | :---: | :---: | :---: |
| **Linke Schulter** | $[243.3, 39.2, 77.1]$ | **$[185.8, 48.9, 63.2]$** | $91.4$ | **$100.0\%$ (Kräftiges Rot)** |
| **Rechte Schulter** | $[249.8, 55.6, 87.1]$ | **$[187.6, 58.1, 70.1]$** | $98.2$ | **$100.0\%$ (Kräftiges Rot)** |
| **Brustbereich (Reißverschluss)** | $[243.0, 24.6, 66.1]$ | **$[210.2, 121.1, 134.4]$** | $149.3$ | **$99.1\%$ (Helles Weinrot)** |
| **Unterer Rumpf** | $[219.5, 5.8, 43.9]$ | **$[172.2, 47.6, 63.4]$** | $86.7$ | **$99.7\%$ (Dunkelrot)** |
| **Linker Ärmel** | $[145.8, 3.4, 30.4]$ | **$[138.3, 24.5, 40.5]$** | $60.4$ | **$99.2\%$ (Dunkelrot)** |
| **Rechter Ärmel** | $[192.3, 7.7, 41.0]$ | **$[140.2, 29.1, 43.3]$** | $63.9$ | **$98.3\%$ (Dunkelrot)** |
| **Gesamte Jacke (Durchschnitt)** | **$[204.9, 13.2, 48.3]$** | **$[161.3, 45.0, 60.0]$** | **$81.5$** | **$97.64\%$ ROT-DOMINANT!** |

- **Farbsättigung (HSV):** Die Sättigung sank lediglich von $S = 0.93$ auf **$S = 0.75$**. Echtes schwarzes Leder erfordert $S \le 0.15$!
- **Echter Schwarzanteil ($R, G, B < 60$):** Lediglich **$4.46\%$** der Jackenpixel erfüllen minimale Schwarz-Kriterien!

### 5.3 Ursachenanalyse
1. In [`controllers/prompt_edit_controller.py`](file:///C:/SnapdragonAI/controllers/prompt_edit_controller.py) wird bei `target_material = "leather"` **kein Priming** ausgeführt (`material_preset = None`).
2. Dem VAE-Encoder und dem SD1.5-Inpainting-Modell wird das **knallrote Originalbild** übergeben.
3. Bei `denoising_strength = 0.80` bleiben $20\%$ der Ausgangslatents erhalten. Zudem zieht das UNet starke chromatische Vorinformationen aus den Maskenrändern.
4. Der Prompt *„A photorealistic black leather jacket...“* mit Negativ-Token *„red, fabric, cloth...“* war **nicht mächtig genug**, um die massive rote Farbinformation im Latent-Space ohne vorherige Entsättigung zu eliminieren.

### 5.4 Prompt-Zielerreichung & Release-Entscheidung
- **Prompt:** *„Mache die rote Jacke zu schwarzem Leder.“*
- **Zielerreichung:** **25%** (Textur leicht verändert, Schutzmaske perfekt, aber Farbe Schwarz komplett verfehlt).
- **Entscheidung:** **STRIPTE ABLEHNUNG (CRITICAL DEFECT)**.

### 5.5 Konkrete Reparaturempfehlung für Sprint 87
1. **Keine Änderungen an der Schutzmaskierung!** Die Segmentierung und der Hautschutz sind makellos und müssen exakt so beibehalten werden.
2. **Einführung eines `leather_black` bzw. `desaturate_darken` Primings:**  
   In [`engine/material_priming.py`](file:///C:/SnapdragonAI/engine/material_priming.py) wird für Leder bzw. Zielfarbe Schwarz eine Vorverarbeitung integriert:
   - Alle Pixel innerhalb der Jackenmaske werden vollständig entsättigt ($S \to 0.00..0.05$).
   - Die Helligkeit (Luminanz) wird auf ein dunkles Leder-Niveau kontrahiert ($L \in [30, 60]$), wobei Reißverschluss- und Faltenkontraste erhalten bleiben.
3. Wird dieses neutrale, dunkelgraue Priming an das HTP-Inpainting übergeben, erzeugt die Hexagon NPU ein tiefes, sattes Schwarz mit realistischen Studio-Glanzlichtern, ohne dass Rot-Chrominanz nachblutet.

---

## 6. Technische Integrität & NPU-Hardware-Nachweis

Alle technischen Prüfungen bestätigen eine einwandfreie Systemfunktion:
- **NPU-Hardware:** Qualcomm Hexagon NPU (HTP V73)
- **QNN DLC Context:** `sd15_inpainting_qnn_htp.dlc`
- **CPU-Fallback:** **0** über alle Stufen hinweg (`cpu_fallback = 0`)
- **Laufzeiten:**
  - Apfel: $22.43$ s (20 Steps)
  - Glasskulptur: $21.95$ s (20 Steps)
  - Rote Jacke: $26.35$ s (20 Steps, $1672 \times 2500$ Source)
- **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert)
- **Sicherheitsvorgaben:** Keine Code-Mutationen, kein Git-Push/Commit, kein Pip-Install.

---

## 7. Roadmap & Handlungsempfehlung (Sprint 87)

Aus dem Audit ergibt sich ein klar umrissener, zielgerichteter Reparatursprint (Sprint 87):

1. **Arbeitspaket 1: Jacken-Priming (Desaturate & Darken)**
   - Implementierung eines dedizierten Chrominanz-Primings für dunkle/schwarze Materialien in [`engine/material_priming.py`](file:///C:/SnapdragonAI/engine/material_priming.py).
   - Entsättigung ($S < 0.05$) und Dämpfung auf $L \approx 45$ vor der Inferenz.
   - Ziel: Mean RGB $[40..50, 40..50, 40..50]$, Rot-Dominanz $< 5\%$.

2. **Arbeitspaket 2: Apfel-Schatten-Kompensation**
   - Anhebung des Helligkeitsplateaus in Zone V durch verstärkte Priming-Homogenisierung (z. B. adaptives Blending oder `min_val = 185.0`).
   - Ziel: Tal bei $X=353$ von $L=95.8$ auf $L \ge 175$ anheben, sodass der Übergang zum Glanzlicht unsichtbar wird.

3. **Arbeitspaket 3: Glasskulptur einfrieren**
   - Die Konfiguration für die Glasskulptur (Seed 100 + Negativ-Token) ist **perfekt** und darf nicht mehr verändert werden.

**Fazit:** Der Audit war dringend notwendig. Er verhindert, dass ein offensichtlicher Farbfehler bei der Jacke und eine unvollständige Schattenentfernung beim Apfel als „Commercial Grade“ an den Kunden ausgeliefert werden.
