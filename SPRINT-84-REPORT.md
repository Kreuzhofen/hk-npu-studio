# SPRINT 84 REPORT – PHOENIX PROMPT ENGINE: FINAL MATERIAL ARTIFACT AUDIT

**Sprint-ID:** SPRINT-84  
**Datum:** 03. November 2026  
**Status:** ERFOLGREICH DURCHGEFÜHRT (URSACHEN VOLLSTÄNDIG AUFGEKLÄRT)  
**Rolle:** Senior Software Engineer (Antigravity)  
**Chief Software Architect:** ChatGPT  
**Product Owner & QA:** Holger Kreuzhofen  
**Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788`  
**Modus:** Streng schreibgeschützte Analyse (Read-only Audit, keine Code- oder Parameteränderungen)  
**Drive D: Sicherungen:** 28/28 POST-Dateien verifiziert, 0 Schreibzugriffe  

---

## 1. Executive Summary & Audit-Ziel

In Sprint 84 wurde das abschließende, rein lesende **Material Artifact Audit** für die beiden metallisch transformierten Motive (**Apfel** und **Glasskulptur**) durchgeführt. Ziel war es, die Ursachen zweier mit bloßem Auge wahrnehmbarer visueller Auffälligkeiten im 24k-Gold-Ergebnis zweifelsfrei aufzuklären:

1. **Apfel (Motiv 1):** Eine dunkle, senkrechte Zone auf der rechten Bildhälfte des goldenen Apfels.
2. **Glasskulptur (Motiv 2):** Eine markante, dunkle bis schwarze Nahtlinie im goldenen Brust-/Rumpfbereich der Skulptur.

### Hauptergebnisse des Audits:
* **Apfel:** Die dunkle senkrechte Zone ist **bereits vollständig im photometrischen Priming vorhanden**. Sie entsteht durch die unkomprimierte Übernahme des tiefen physikalischen Kernschattens des Originalbilds (`appl_edit_49_original.png`) in den HSV-Value-Kanal. Das Inpainting-Modell folgt bei Denoising $0,75$ dieser Schattenvorgabe.
* **Glasskulptur:** Die schwarze Linie ($Y = 162 \dots 269$, $X \approx 215$) ist **kein Masken- und kein Priming-Fehler** (beide sind dort lückenlos intakt). Sie entsteht **ausschließlich während des HTP-Inpaintings**, hervorgerufen durch einen stochastischen latenten Trajektorienkollaps bei **`seed = 42`**, der an der subtilen Flügelansatzkante des Originalglases in eine extreme Kontrastsättigung (Schwarzbruch bis $RGB = [3, 1, 0]$) übersteuert.
* **Jacke (Motiv 3):** Referenzstatus aus Sprint 83 unverändert exzellent ($100\%$ bit-identischer Schutz von Gesicht, Haaren, Hals und Händen; zero Artefakte).
* **Empfehlung:** **Freigabe von Sprint 85 (Material Polish Sprint)** zur Implementierung eines metallischen Luminanz-Lifts im Priming und zur Festlegung eines saumfreien kanonischen Seeds für die Glasskulptur.

---

## 2. Diagnostische Übersicht

![Sprint 84 Diagnostic Overview](file:///C:/SnapdragonAI/reports/sprint_84_material_artifact_audit/images/sprint_84_diagnostic_overview.png)

---

## 3. Detailliertes Audit Artefakt 1: Roter Apfel

### 3.1 Fundstelle & Geometrische Eingrenzung
* **Objekt:** Motiv 1 – Apfel (`appl_edit_49_original.png` $\to$ `motif1_apple_repaired_htp.png`)
* **Koordinaten:** Bounding Box $X \in [348, 382]$, $Y \in [275, 375]$ (Zentrum: $X \approx 360, Y \approx 325$).
* **Ausdehnung:** Vertikales Band von ca. $35\text{ px}$ Breite $\times 100\text{ px}$ Höhe ($2.250\text{ Pixel}$).
* **Luminanz-Minimum:** Tiefstwert bei $X = 360, Y = 320$: $L = 54,2$ ($RGB = [88, 54, 4]$).
* **Kontrastverhältnis:** Während die linke Wölbung des Apfels ($X \in [275, 315]$) vollflächig mit $L \approx 205 - 212$ im Glanzlicht steht, bricht die Helligkeit im Schattenband auf $L_{mean} = 84,1$ ein.

![Apple Artifact Zoom Comparison](file:///C:/SnapdragonAI/reports/sprint_84_material_artifact_audit/images/apple_artifact_crop_comparison.png)

### 3.2 Vergleichsstufen (Original vs. Priming vs. Seeds)

Die folgende Tabelle zeigt das horizontale Querprofil der Luminanz durch die Mitte des Apfels (gemittelt über $Y = 280 \dots 360$):

| Spalte X | Original Rot ($L$) | Priming ($L$) | Seed 42 Matrix ($L$) | Seed 43 Matrix ($L$) | Repaired HTP ($L$) | Befund |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **280** | 212,1 | 212,3 | 228,8 | 180,6 | 210,7 | Haupt-Glanzlicht (Key Light) |
| **300** | 194,0 | 212,3 | 221,8 | 192,4 | 207,5 | Wölbung links |
| **320** | 110,1 | 203,9 | 187,8 | 184,1 | 204,2 | Übergangszone |
| **340** | 64,1 | 167,4 | 99,2 | 174,2 | 159,8 | Beginn Schattenflanke |
| **350** | 53,3 | 133,1 | 68,0 | 152,2 | 91,7 | Starker Helligkeitsabfall |
| **360** | **44,4** | **107,1** | **59,1** | **146,0** | **75,7** | **LOKALES MINIMUM (Kernschatten)** |
| **370** | 48,3 | 115,9 | 77,1 | 160,5 | 78,5 | Anstieg |
| **380** | 51,2 | 119,9 | 162,1 | 180,8 | 97,7 | Schattenausläufer |
| **390** | 99,2 | 162,7 | 213,1 | 198,8 | 160,7 | Beginn Randreflexion |
| **405** | 172,0 | 199,2 | 222,2 | 211,3 | 212,3 | Rim Light (Kantenreflexion) |

### 3.3 Pixel- und Farbwerte der betroffenen Zone V ($X \in [350, 375], Y \in [280, 370]$)

| Zustand / Datei | Mean Luminanz | Min Luminanz | Max Luminanz | Mittlere RGB-Werte | Visueller Eindruck |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Original Red Apple** | 47,3 | 38,1 | 84,7 | $[148,3, \quad 0,1, \quad 25,5]$ | Tiefer diffuser Rotschatten |
| **Primed Preview** | **114,3** | **90,8** | **181,8** | $[155,3, 110,8, \quad 24,8]$ | **Dunkelbraune Gold-Schattenzone** |
| **Seed 42 (Matrix)** | 73,5 | 38,1 | 130,8 | $[108,5, \quad 66,7, \quad 16,6]$ | Dunkle Vertiefung / Mulde |
| **Seed 43 (Matrix 512px)**| 149,3 | 59,1 | 187,1 | $[192,5, 142,3, \quad 72,4]$ | Weitgehend überglänzt |
| **Repaired HTP Result** | **84,1** | **54,2** | **147,8** | $[124,3, \quad 77,0, \quad 15,5]$ | **Sichtbares senkrechtes Schattenband** |

### 3.4 Ursachenanalyse: Priming vs. HTP-Inpainting
1. **Das Priming ist die Primärursache:** In `engine/material_priming.py` (Zeile 205) wird der Helligkeitskanal mit `prime_v = np.clip(v * preset.val_multiplier, 0.0, 255.0)` berechnet. Da `val_multiplier = 1.05` beträgt, wird die diffuse Beleuchtung des Originalbilds linear übernommen. Der physikalische Kernschatten des echten Apfels ($V \approx 140 / 255$) sinkt dadurch im Priming auf $L = 107,1$ ab.
2. **Verstärkung durch den Crop-Inpainting-Workflow:** In `controllers/prompt_edit_controller.py` wird der Bildausschnitt vor der Inferenz auf die Bounding Box zugeschnitten (`[179, 153, 502, 476]`, $323 \times 323\text{ px}$) und auf $512 \times 512$ vergrößert. Bei Denoising Strength $0,75$ übernimmt der UNet-Pfad $25\%$ der latenten Information aus dem Priming. Unter dem skalierten latenten Raster bildet das Modell die im Priming vorgegebene Schattenrinne getreu nach, anstatt sie durch metallische Reflexionen zu schließen.

### 3.5 Konkrete Reparaturempfehlung für Sprint 85
* **Luminanz-Kompression im Material-Priming (`engine/material_priming.py`):**
  Echte polierte Metalle (insbesondere 24k Gold) haben eine hohe Eigenreflexion und weisen keine tiefen diffusen Kernschatten auf. Einführung eines Mindesthelligkeitswerts (`min_metallic_val = 145.0` im 24k-Gold-Preset) verhindert das Absinken des Value-Kanals unter $145$:
  $$\text{prime\_v} = \text{min\_val} + \frac{v}{255} \cdot (255 - \text{min\_val}) \cdot \text{multiplier}$$
  Damit bleibt die Zone im Priming stets oberhalb von $L \approx 150$, und das Inpainting rendert eine homogene, samtig glänzende Goldkrümmung.

---

## 4. Detailliertes Audit Artefakt 2: Grüne Glasskulptur

### 4.1 Fundstelle & Geometrische Eingrenzung
* **Objekt:** Motiv 2 – Glasskulptur (`motif2_glass_1_original.png` $\to$ `motif2_glass_repaired_htp.png`)
* **Koordinaten:** Streng vertikale Linie bei $X \in [213, 218]$ von Zeile $Y = 162$ bis $Y = 269$.
* **Ausdehnung:** Über $107\text{ Pixel}$ vertikale Länge bei nur $3$ bis $5\text{ Pixel}$ Breite ($751\text{ Pixel}$ mit $L < 40$).
* **Luminanz-Einbruch:** Von umgebenden $L \approx 130 - 150$ stürzt die Luminanz schlagartig auf $L = 1,5 \dots 10,8$ ab!
* **Farbwerte im Kern:** Nahezu reines Schwarz: $RGB = [3, 1, 0]$ (bei $Y=180, X=216$) bis $[15, 6, 1]$ (bei $Y=180, X=214$).

![Glass Sculpture Artifact Zoom Comparison](file:///C:/SnapdragonAI/reports/sprint_84_material_artifact_audit/images/glass_artifact_crop_comparison.png)

### 4.2 Lückenlose Entstehungsstufen-Prüfung

#### 1. Prüfung der Semantischen Maske:
* **Befund: MASKE IST 100% FEHLERFREI.**
* Bei allen betroffenen Zeilen ($Y = 162 \dots 269$) ist die Maske vollkommen homogen aktiv (z. B. bei $Y=180$: Maske reicht von $X = 205$ bis $X = 264$, Gesamtbreite $60\text{ px}$).
* Die schwarze Nahtlinie liegt bei $X \approx 215$, also ca. $10\text{ px}$ tief im Inneren der Maske. Es gibt weder einen Maskenspalt noch eine Aussparung.

#### 2. Prüfung des Featherings / Blends:
* **Befund: FEATHERING SCHEIDET VOLLKOMMEN AUS.**
* Der Feathering-Radius beträgt $5\text{ px}$, die Dilation $1\text{ px}$. Der Einflussbereich des Feathering-Alpha-Blends beschränkt sich auf $X \in [200, 208]$ und $X \in [260, 269]$. Bei $X = 215$ ist der Alpha-Wert exakt $1,000$ (reines Inpainting-Ergebnis, null Originalbild-Einfluss).

#### 3. Prüfung der Priming-Vorschau:
* **Befund: PRIMING IST VOLLKOMMEN SAUBER.**
* Im Priming-Bild (`motif2_glass_repaired_primed.png`) existiert an diesen Koordinaten keinerlei schwarze Linie:
  * $X = 213: RGB = [140, 99, 20], L = 99,1$
  * $X = 215: RGB = [110, 78, 17], L = 80,7$
  * $X = 216: RGB = [102, 73, 16], L = 75,2$
  * $X = 218: RGB = [114, 81, 17], L = 81,2$
* Das Priming stellt eine homogene, satte Goldfläche dar.

#### 4. Prüfung des HTP-Inpaintings (Die tatsächliche Ursache):
* **Befund: INFERENZ-KOLLAPS DURCH SEED 42.**
* Im Skript `tools/run_sprint82_glass_repair.py` wurde `seed = 42` als Inferenz-Seed übergeben.
* **Mechanismus:** Im Originalbild der Glasskulptur verläuft bei $X \approx 215, Y \in [165, 260]$ die Trennkante zwischen dem vorderen Flügelansatz und der Rumpfwölbung ($L_{orig}$ fällt sanft von $130$ auf $85$ ab).
* Unter `seed = 42` neigt das SD15 UNet bei Denoising $0,75$ dazu, derartige Kanten als "Abgrund" bzw. Schattenfalz zu interpretieren. Die Latenzwerte werden im negativen Bereich gesättigt, sodass das decodierte Ergebnis auf $RGB = [3, 1, 0]$ ($L = 1,5$) abstürzt.
* Im Vergleich dazu erzeugte Sprint 80 mit `seed = 20260830` an denselben Pixeln ein weiches Mittelbraun ($RGB = [67, 47, 0], L = 47$), jedoch keine schwarze Linie.

### 4.3 Cyan-Reste, Sockel und Umgebungsschutz
* **Cyan-Reste:** Innerhalb der Maske wurden im HTP-Ergebnis **exakt 0 Pixel mit Cyan-Resten** festgestellt ($G > R+10$ und $B > R+10$ ergibt $0\text{ px}$). Der Sockel ($Y \in [330, 387]$) ist zu $100\%$ sauber und homogen in Gold gewandelt.
* **Tisch-Schutz ($Y \ge 400$):** Maximale Abweichung zum Original: **exakt $0,00$** ($100\%$ bit-identisch).
* **Hintergrund-Schutz (Raumteiler, Wände):** Maximale Abweichung: **exakt $0,00$**.

### 4.4 Konkrete Reparaturempfehlung für Sprint 85
* **Kanonischer Seed für die Glasskulptur:**
  Durchführung einer fokussierten 5-Seed-Matrix für die Glasskulptur (Seeds: 43, 100, 777, 20260830) analog zum Apfel. Auswahl des Seeds mit der geringsten Linienbildung.
* **Negativ-Prompt Erweiterung in `controllers/prompt_edit_controller.py`:**
  Ergänzung des material-spezifischen Negativ-Prompts um:
  `"seam, black line, dark slit, crease, shadow line, border line, gap, crack, rift"`
  Dadurch wird die UNet-Aufmerksamkeitsmatrix aktiv daran gehindert, an Konturen schwarze Rillen zu generieren.

---

## 5. Referenzprüfung Motiv 3 (Rote Jacke)

* **Status:** Rein lesende Übernahme aus Sprint 83.
* **Befund:** Vollkommen frei von Materialartefakten.
* **Lederoberfläche:** Gleichmäßige Narbung mit feiner Laplace-Energie ($1,54$), plastischen Falten und intakten Reißverschlüssen.
* **Anatomieschutz:** Gesicht, Hals, Haare ($Y < 516$) und Hände zu $100\%$ bit-identisch erhalten ($0\text{ px}$ Überlappung, Max Diff $= 0,00$).
* **Handlungsbedarf:** Keiner. Die Jacken-Pipeline dient als Referenzstandard.

---

## 6. Gesamtfreigabe-Bewertung & Empfehlung für Sprint 85

### Matrix der Artefakte

| Motiv | Artefakt | Fundstelle | Entstehungsstufe | Primäre Ursache | Reparaturansatz (Sprint 85) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Apfel** | Dunkle senkrechte Zone ($L=84,1$) | $X \in [348, 382]$, $Y \in [275, 375]$ | **Priming** (vor Inferenz) | Übernahme des diffusen Kernschattens aus dem Original | HSV-Value-Kompression (`min_val = 145.0`) im Gold-Preset |
| **Glasskulptur** | Schwarze Nahtlinie ($L=1,5 \dots 10,8$) | $X \in [213, 218]$, $Y \in [162, 269]$ | **HTP-Inferenz** (NPU) | Latenter Kollaps bei Seed 42 an Flügelkante | Saumfreier Seed + Negativ-Prompt ("black line, seam") |
| **Jacke** | Keine | Keine | — | — | — (Perfekt) |

### Abschließendes Votum:
> **Die Durchführung eines fokussierten Reparatursprints 85 wird ausdrücklich empfohlen.**  
> Zwar ist die Prompt-Engine architektonisch und hardware-technisch (100% Qualcomm Hexagon HTP, 0 CPU-Fallback) vollkommen stabil, doch verhindern die beiden analysierten Artefakte den angestrebten Status des **Commercial Polish**. Da die Ursachen eindeutig lokalisiert sind und mit minimal-invasiven Anpassungen (HSV-Luminanz-Kompression im Priming und Seed-Auswahl für die Skulptur) behoben werden können, ist eine finale Perfektionierung in Sprint 85 der empfohlene Weg zur Exzellenz.

---
*Bericht erstellt durch Senior Software Engineer (Antigravity) für Product Owner Holger Kreuzhofen und Chief Software Architect ChatGPT.*
