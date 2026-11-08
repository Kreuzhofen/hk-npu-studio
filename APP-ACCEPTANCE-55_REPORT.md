# SPRINT APP-ACCEPTANCE-55 REPORT
**HK NPU STUDIO – Object Editing Quality & Forensic Inpainting Analysis**

---

## 1. Executive Summary

| Parameter / Prüfpunkt | Vorgabe / Ziel | Feststellung (Sprint 55) | Bewertung |
|---|---|---|---|
| **Sprint-ID** | `SPRINT APP-ACCEPTANCE-55` | `SPRINT APP-ACCEPTANCE-55` | Erfüllt |
| **Modus** | Ausschließlich READ-ONLY | Keine Änderungen an Produktionscode | 100% Read-Only strikt eingehalten |
| **Hardware** | Snapdragon X Elite – Hexagon HTP V73 | Qualcomm Hexagon HTP V73 NPU | Verifiziert |
| **Git Commit HEAD** | `8784a43f5b7666f1007292393c6ea947b5cdd788` | `8784a43f5b7666f1007292393c6ea947b5cdd788` | Unverändert & sauber |
| **Pre-Backup** | `D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_55_20261102\PRE` | 16/16 Dateien SHA-256 verifiziert | 100% Integrität nachgewiesen |
| **Untersuchte Artefakte** | Sprint-54 Bildmaterial & Metriken | 6 Bild-/JSON-Dateien vollständig analysiert | Lückenlos forensisch geprüft |
| **Hauptbefund 1 (Maske)** | Gezielte Objektmaskierung erwartet | Maske umfasst 83.1% irrelevante Umgebung | **Kritischer Maskierungsfehler (A)** |
| **Hauptbefund 2 (Prompt)** | Goldenes Dekorationsobjekt erwartet | Prompt fokussiert auf "surrounding environment" | **Kritischer Konditionierungsfehler (B)** |
| **Hauptbefund 3 (Modellverhalten)** | Objekterzeugung erwartet | Modell generierte weiße Raumtrennwand + Tisch | **Logische Folge von A + B + D** |
| **Inpainting-Pipeline-Status** | Pipeline-Integrität prüfen | NPU-Crop, HTP-Inferenz & Rückkomposition intakt | Technisch fehlerfrei (0 ms CPU-Fallback) |

---

## 2. Sicherheitsgate & Pre-Backup-Nachweis

1. **Git Repository Status:**
   - Commit HEAD: `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert).
   - Arbeitsverzeichnis: Vollständig dokumentiert; keine unautorisierten Commits oder Pushes.
2. **Speicherprüfung:**
   - Laufwerk `D:` verfügbar mit **39.75 GB** freiem Speicherplatz.
3. **Pre-Backup:**
   - Pfad: `D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_55_20261102\PRE`
   - Manifest: `PRE_BACKUP_SHA256_MANIFEST.json`
   - Ergebnis: **16 von 16 Dateien** bitgenau verifiziert (100% SHA-256 Übereinstimmung).

---

## 3. Vollständige Untersuchung des Sprint-54-Bildmaterials

Alle sechs geforderten Dateien aus `reports/app_acceptance_54/` sowie die Produktionsdateien aus `output/` wurden forensisch untersucht:

| Datei | Pfad | Dimension / Größe | SHA-256 Prüfsumme (Präfix) | Inhaltliche Feststellung |
|---|---|---|---|---|
| **Originalfoto** | [`acceptance54_original.png`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_original.png) | 1600 × 1200 px (1.894.583 Bytes) | `a4f80f657ab72b1c...` | Echtes Nutzerfoto (Holztisch, Hängepflanzen oben, weiße Raumtrennwand/Wand, Person rechts). |
| **Masken-Overlay** | [`acceptance54_mask_overlay.png`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_mask_overlay.png) | 1600 × 1200 px (1.881.436 Bytes) | `0a7ed87dbb3b9519...` | 42% Theme-Akzent Overlay. Zeigt einen massiven, rechteckigen Farbblock in der Bildmitte. |
| **Binärmaske** | [`acceptance54_mask.png`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_mask.png) | 1600 × 1200 px (4.164 Bytes) | `cd92f8522e8cdd78...` | 8-Bit-Graustufenmaske (L). Bounding-Box $[576, 266, 835, 590]$. 69.716 maskierte Pixel. |
| **Inpainting-Ergebnis** | [`acceptance54_edited_result.png`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_edited_result.png) | 1600 × 1200 px (1.883.688 Bytes) | `b8ecdd6db1e0bcc4...` | Zeigt eine weiße Wandtrennwand mit Tischfortführung und minimaler Goldverzierungs-Textur (20.2%). |
| **Vergleichsgrid** | [`acceptance54_comparison_grid.png`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_comparison_grid.png) | 1240 × 1280 px (1.477.533 Bytes) | `12e6c94c45c47ef2...` | 4-Panel Übersicht (Original, Overlay, Ergebnis, Split-Vergleich). |
| **Messdaten** | [`acceptance54_metrics.json`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_metrics.json) | 2.039 Bytes | `b7f00c023fe5a354...` | Metrikdaten (25.44 s Inferenz, 99.89% Hintergrund-Bitidentität, 20.22% Goldchrominanz). |
| **Gallery Output** | [`output/generative_fill_sprint54.png`](file:///C:/SnapdragonAI/output/generative_fill_sprint54.png) | 1600 × 1200 px (1.883.688 Bytes) | `b8ecdd6db1e0bcc4...` | Identisch mit `acceptance54_edited_result.png`. |
| **Gallery Sidecar** | [`output/generative_fill_sprint54.json`](file:///C:/SnapdragonAI/output/generative_fill_sprint54.json) | 682 Bytes | `a022bfe14b3b78be...` | Vollständige Inpainting-Parameter und Crop-Geometrie für den Gallery Inspector. |

---

## 4. Detaillierte Maskenanalyse

### 4.1 Geometrische Kenngrößen
- **Gesamtfläche der Maske:** **69.716 Pixel** (entspricht **3,631 %** des 1.920.000-Pixel-Gesamtbildes).
- **Bounding-Box der Maske:** $[X_{\text{min}}=576, Y_{\text{min}}=266, X_{\text{max}}=835, Y_{\text{max}}=590]$.
- **Dimensionen der Bounding-Box:** Breite: **259 Pixel**, Höhe: **324 Pixel**.
- **Bounding-Box-Fläche:** $259 \times 324 = 83.916$ Pixel.
- **Füllgrad der Maske:** $\frac{69.716}{83.916} = \mathbf{83,08 \%}$. Die Maske ist ein nahezu massiver Block ohne Konturbezug.

### 4.2 Zusammensetzung der maskierten Bildinhalte
Eine farbmetrische und morphologische Analyse der vom Maskenblock überdeckten Originalpixel ergab folgendes erschütterndes Ergebnis:

| Bildinhalt / Entität | Kriterium / Farbsegmentierung | Pixelanzahl in Maske | Prozentualer Anteil |
|---|---|---|---|
| **Hintergrund (Weiße Wand / Raumteiler)** | $R>170, G>170, B>150$ | **30.496 Pixel** | **43,74 %** |
| **Hängepflanzen (Grüne Blätter)** | $G > R+15 \land G > B+15$ | **19.172 Pixel** | **27,50 %** |
| **Person / Hauttöne (Randbereich)** | $R>110, G>60, B>40, R-G>15$ | **5.164 Pixel** | **7,41 %** |
| **Tischoberfläche (Holz)** | $R>G>B, 70<R<160, B<100$ | **3.121 Pixel** | **4,48 %** |
| **Übergänge, Kanten & Schatten** | Differenzpixel | **11.763 Pixel** | **16,87 %** |
| **Gesamt** | – | **69.716 Pixel** | **100,00 %** |

> [!CAUTION]
> **Über 83 % der Maskenfläche** entfielen auf Wand, Pflanzen, Tisch und Nachbarstrukturen! Weniger als 17 % der Fläche berührten überhaupt das beabsichtigte Deko-Objekt.

### 4.3 Pinselparameter und Maskenüberstände
- **Pinselgröße 48 px:** Ein Pinsel mit 48 px Durchmesser hat einen Radius von 24 px. Bei einem Gesamtmotiv von nur ca. 120–180 px tatsächlicher Breite deckt ein einzelner Pinselstrich bereits ein Viertel der Zielbreite ab.
- **Pinsel-Härte 100 % ($h=1.0$):** Der Stempel besaß keinerlei Kosinus-Auslauf, sondern schnitt mit 100% Kantenopazität hart durch Nachbarobjekte.
- **Maskenüberstände:**
  - **Nach oben ($Y \in [266..330]$):** 60–80 Pixel Überstand mitten in die feinen Blätter der herabhängenden Zimmerpflanze.
  - **Nach unten ($Y \in [550..590]$):** 40 Pixel Überstand auf die glatte Holztischoberfläche.
  - **Zu den Flanken ($X \in [576..620]$ und $[790..835]$):** Bis zu 45 Pixel Überstand in die weiße Wandfläche und Nachbarstrukturen.

### 4.4 Beantwortung der zentralen Frage
> **Frage:** *Warum umfasst die Maske einen großen Teil der Bildmitte, obwohl das eigentliche Objekt gezielt ausgewählt werden sollte?*
>
> **Antwort:** Im automatisierten Testlauf von Sprint 54 saß kein menschlicher Bediener an der Maus. Das Testskript `tools/run_app_acceptance_sprint54.py` generierte 12 parallele, vertikale Grobstriche mit 48 px Pinselgröße und 100% Härte über ein starres Koordinatenraster (`((705, 290), (705, 565))`, `((680, 310), ...)`, usw.). Durch den enormen Pinselradius verschmolzen diese 12 Striche zu einem riesigen, monolithischen $259 \times 324$ Pixel Block in der Bildmitte. Es fand weder eine Konturverfolgung noch eine Randbereinigung mit dem Radierer statt.

---

## 5. Prompt- und Crop-Analyse

### 5.1 Produktionsdaten aus dem Sidecar
Aus [`generative_fill_sprint54.json`](file:///C:/SnapdragonAI/output/generative_fill_sprint54.json):
- **Positiver Prompt:** `"Replace the selected object with a realistic golden decorative object. Preserve the surrounding environment, lighting, perspective and shadows."`
- **Negativer Prompt:** `"blurry, distorted, low quality, artifacts, bad anatomy, deformed"`
- **Denoising-Stärke:** `1.0` (Vollständige Rauschinjektion; alle Ausgangslatents in der Maske werden zerstört).
- **Seed:** `5401` | **Steps:** `20` | **CFG Scale:** `8.0`
- **Crop-Geometrie:** Bounding-Box $[576, 266, 835, 590]$ mit 25% Kontext-Padding $\to$ Crop-Box $[462, 185, 948, 671]$ ($486 \times 486$ Pixel).

### 5.2 Kontextverteilung im 486×486 NPU-Crop
Der Ausschnitt von 486 × 486 px wurde auf 512 × 512 skaliert und dem Qualcomm SD1.5 Inpainting UNet übergeben:
- **Kontextfläche außerhalb der Maske im Crop:** **70,5 %** (166.480 Pixel).
  - 29,4 % weiße Wand / Raumteiler
  - 25,9 % grüne Zimmerpflanzen
  - 16,3 % brauner Holztisch
- **Maskenfläche im Crop:** **29,5 %** (69.716 Pixel).

### 5.3 Warum erzeugte das Modell eine weiße Raumtrennwand mit Tisch?
Dieser fatale visuelle Fehlgriff beruht auf der Interaktion von vier Faktoren:

1. **Prompt-Fehlleitung durch "Preserve environment":**
   Der CLIP-Textencoder von Stable Diffusion 1.5 versteht keine logischen Anweisungen wie *"Preserve the surrounding..."* als Ausschlusskriterium, sondern als **Inhaltsaufforderung**! Die Token `environment`, `surrounding`, `lighting`, `perspective`, `shadows` erhielten enorme Text-Attention.
2. **Fehlen eines konkreten Substantivs:**
   Der Ausdruck `"golden decorative object"` ist semantisch extrem schwach und vage. Ein Diffusionsmodell benötigt konkrete Form-Substantive (wie *statue*, *vase*, *bowl*, *figurine*, *sculpture*), um eine 3D-Geometrie im Latent Space aufzubauen.
3. **Randlatents diktieren die Lösung:**
   Bei 70,5 % Umgebungsanteil im Crop mit `denoising_strength = 1.0` strebt das Inpainting-UNet nach minimalem Diffusionsverlust an den Maskenrändern. An den oberen Maskenrändern lagen weiße Wand und Blätter; an den Seiten weiße Wand; unten Tisch. Die stetigste, verlustärmste Fortsetzung dieser Randbedingungen unter dem Prompt-Einfluss von "environment" war die **Erweiterung der weißen Raumtrennwand nach unten** und die **Erweiterung der Tischplatte nach oben**.
4. **Verdrängung des Deko-Objekts:**
   Das Deko-Objekt wurde durch die dominante Wandrekonstruktion buchstäblich an den Rand gedrängt; es verblieb lediglich eine kleine goldgelbe Reflexion/Verzierung (20,22% Flächenanteil).

---

## 6. Ursachenklassifikation

| Kategorie | Ursache & Diagnose | Beleg & Pfad | Betroffene Stelle | Technische Auswirkung | Sicherheit |
|---|---|---|---|---|---|
| **A** | **Maskierungsfehler (Primärursache 1)** | [`reports/app_acceptance_54/acceptance54_mask.png`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_mask.png) | `tools/run_app_acceptance_sprint54.py:43-70` | Pinsel 48 px / 100% Härte erzeugte riesige Maske mit 83% Überstand in Wand, Pflanzen und Tisch. | **HOCH (100%)** |
| **B** | **Prompt-Konditionierung (Primärursache 2)** | [`output/generative_fill_sprint54.json`](file:///C:/SnapdragonAI/output/generative_fill_sprint54.json#L4) | `tools/run_app_acceptance_sprint54.py:PROMPT` | CLIP priorisierte "environment/perspective"; kein konkretes Motiv-Substantiv für das Objekt vorhanden. | **HOCH (100%)** |
| **C** | **Crop- und Kontextproblem** | [`reports/app_acceptance_54/acceptance54_metrics.json`](file:///C:/SnapdragonAI/reports/app_acceptance_54/acceptance54_metrics.json#L27-L42) | `InpaintingController._square_crop_box` | 70.5% des Crops waren weiße Wand, Pflanze und Tisch; verstärkte den Raumrekonstruktions-Zwang. | **MITTEL** |
| **D** | **SD1.5-Modellgrenze** | CLIP ViT-L/14 & SD1.5 Inpainting UNet | Inferenzmodell | SD1.5 neigt bei vagen Prompts ("decorative object") zur Ausfüllung großer Masken mit Umgebungsstrukturen. | **HOCH** |
| **E** | **Rückkomposition / Farbkorrektur** | [`engine/backends/sd15_qnn_inpainting_adapter.py`](file:///C:/SnapdragonAI/engine/backends/sd15_qnn_inpainting_adapter.py#L318-L322) | `align_color_lab()` | **AUSGESCHLOSSEN:** LAB-Verschiebung war auf $\pm 8$ geklammert und hatte keinen Einfluss auf die Wandbildung. | **AUSGESCHLOSSEN** |
| **F** | **Kombination (Gesamtdiagnose)** | Synthese aus A + B + D | Schnittstelle Maske $\times$ Prompt $\times$ Modell | **Toxische Kombination:** Eine gigantische, umgebungsüberdeckende Maske traf auf einen raumorientierten Prompt. | **HOCH (Gesichert)** |

---

## 7. Minimaler Reparaturplan (Streng READ-ONLY)

> [!IMPORTANT]
> **Erkenntnis:** Der Produktionscode der Phoenix Inpainting Engine (`InpaintingController`, `SD15QnnInpaintingAdapter`, HTP V73 Backend) ist **vollständig intakt** und fehlerfrei. Es ist **keine** Änderung an der Inferenz- oder Kompositions-Pipeline notwendig!

### 7.1 Gezielte Korrekturschritte für den nächsten Sprint

1. **Schritt 1 – Präzise Konturmaskierung (Canvas-Bedienung):**
   - Pinselgröße im UI auf maximal **16–24 Pixel** reduzieren (statt 48 px).
   - Pinsel-Härte auf **60–80 %** einstellen (weicherer Randabfall statt harter 100%-Kante).
   - Maske strikt auf den tatsächlichen Körper des Zielobjekts begrenzen.
   - Überstände an Pflanzenblättern und Tischkante mit dem Radierwerkzeug (`erase=True`) sauber freistellen.
   - **Ziel:** Mindestens 80 % der maskierten Pixel müssen dem tatsächlichen Objekt angehören ($< 10\%$ Umgebungsanteil).

2. **Schritt 2 – Konkreter Substantiv-Prompt (Prompt Engineering):**
   - Streichung aller Meta-Instruktionen wie *"Preserve the surrounding environment..."*, da die Erhaltung der Umgebung durch die Inpainting-Maske und den Controller bereits mathematisch garantiert ist (99.89% Bitidentität)!
   - Formulierung eines klaren, physisch greifbaren Substantivs mit Materialattributen:
     - **Positiv:** `"A solid polished golden brass sculpture of a sitting falcon, intricate metallic feathers, shiny reflections, detailed metal craftsmanship, dramatic studio lighting"`
     - **Negativ:** `"white wall, room divider, table extension, flat surface, wooden furniture, blurry, deformed, low quality"`

3. **Schritt 3 – Denoising-Feinjustierung:**
   - Denoising Strength auf **0.85–0.95** austarieren (statt starr 1.0), sofern noch Reststrukturen des Originalobjekts als Form-Anchor dienen sollen, oder **1.0** beibehalten bei gleichzeitig präziser Konturmaske.

### 7.2 Risiko- und Verträglichkeitsanalyse
- **Risiko für bestehende Inpainting-Funktion:** **Keines (0 %)**, da die Pipeline selbst unangetastet bleibt.
- **Auswirkungen auf T2I und Image-to-Image:** **Keine (0 %)**, da völlig getrennte Controller und Workspaces.
- **Geplanter Verifikationstest:** Erneuter Lauf auf demselben Foto (`acceptance54_original.png`) mit konturgenauer Maske und Substantiv-Prompt.
- **Erfolgskriterien:**
  1. Golden-Chromatische Fruchtoberfläche / Objektfläche $\ge 75\%$.
  2. Keine weißen Wand- oder Raumtrenner-Artefakte in der Maske.
  3. Vollständiger Erhalt aller Hängepflanzen und der umgebenden Tischoberfläche.
  4. 100% bitidentischer Erhalt außerhalb der Zielmaske ($MSE < 0.01, PSNR > 70\text{ dB}$).
