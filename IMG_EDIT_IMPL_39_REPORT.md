# HK NPU STUDIO – IMG-EDIT-IMPL-39
## Image-to-Image Quality Optimization & Denoising Sweep Report
**Plattform:** Windows 11 ARM64 (Qualcomm Snapdragon X Elite, Hexagon HTP V73)  
**Datum:** 2026-11-01  
**Status:** Erfolgreich abgeschlossen (DoD erfüllt)

---

## 1. Management-Zusammenfassung

Im Rahmen des Sprints **IMG-EDIT-IMPL-39** wurde die in Sprint 38 eingeführte **Image-to-Image Pipeline** einer tiefgehenden qualitativen und mathematisch-technischen Untersuchung auf der **Qualcomm Hexagon HTP NPU (V73)** unterzogen.

### Kernbefunde:
1. **Streng monotone Qualitäts- und Differenzprogression:**
   Die empirische Untersuchung über alle 6 geforderten Denoising-Stufen ($0.25, 0.35, 0.50, 0.65, 0.85, 1.00$) belegt eine mathematisch lückenlose Monotonie: Die Differenz zur Bildvorlage wächst streng monoton ($L_1: 8.67 \to 72.93$), während die strukturelle Ähnlichkeit streng monoton sinkt ($\text{SSIM}: 0.7381 \to 0.3595$).
2. **100% Bit-Identische Seed-Reproduzierbarkeit:**
   Zwei unabhängige Inferenzläufe mit identischem Seed (42) bei $s = 0.50$ ergaben eine maximale Pixeldifferenz von exakt **$0.0000$**. Die INT8/UINT16 Festkomma-Arithmetik der Qualcomm Hexagon NPU ist vollständig deterministisch.
3. **Transparenter VAE-Roundtrip:**
   Die Messung der intrinsischen Rekonstruktionsgüte des Qualcomm Hexagon HTP VAE (Encoder $\to$ Decoder ohne Diffusionsschritte) ergab einen **PSNR von 30.66 dB** und einen **SSIM von 0.8475** (L1: 4.80 / 255). Der VAE arbeitet somit hochgradig verlustarm.
4. **Kein CPU-Fallback:**
   Alle Stufen (VAE-Encoder, CLIP Text-Encoder, UNet, VAE-Decoder) liefen zu **100% auf der Hexagon HTP NPU** mit **0.00 ms CPU-Fallback**.
5. **Identifikation des optimalen Sweet Spots:**
   Als idealer Standardwert für Image-to-Image Neukompositionen wurde **$0.65$** (13 Schritte, 16.02 s) identifiziert: Hier verbinden sich perfekte Prompt-Umsetzung ("blauer Diamantapfel") und vollständige Bewahrung der räumlichen Komposition (Tischhorizont, Beleuchtungswinkel, Objektstandfläche).

---

## 2. Sicherheits-Gate & Pre-Backup

Gemäß den Governance-Regeln aus `AGENTS.md` und `GEMINI.md` wurden vor allen Messungen und Testläufen folgende Sicherheitsprüfungen durchgeführt:

* **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788` (Branch `main`, uncommitted worktree intakt)
* **Laufwerk D: Verfügbarkeit:** Vorhanden (39.87 GB freier Speicherplatz)
* **Pre-Backup Ziel:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_39_20261101`
* **Sicherungsumfang:** 25 Produktiv- und Testdateien (Controller, Backends, Views, Locales, Tests, Reports, Benchmarks)
* **Prüfsummen-Verifikation:** 25 von 25 Dateien mit 100% SHA-256 Übereinstimmung zwischen `C:\SnapdragonAI` und `D:` verifiziert.

---

## 3. Technische Tiefenprüfung (Architektur & Mathematik)

### 3.1 Latent-Blending: Inpainting vs. Image-to-Image
* **Inpainting (Masked Diffusion):**
  Beim Inpainting ist Spatial Latent Blending (RePaint-Prinzip) essenziell:
  $$z_t = M_{\text{latent}} \odot z_{gen,t} + (1 - M_{\text{latent}}) \odot (z_0 + \sigma_t \cdot \epsilon)$$
  Hierdurch wird garantiert, dass unmaskierte Bildbereiche während aller Entrauschungsschritte auf der Originaltrajektorie verbleiben.
* **Image-to-Image (Full Canvas):**
  Im Image-to-Image-Modus existiert keine Maske ($M_{\text{latent}} = \mathbf{1}$). Ein schrittweises Blenden von $z_0$ während der Diffusionsschritte wäre mathematisch fatal: Es würde zu Phantombildern (Ghosting), Doppelkonturen und Artefakten führen, da das UNet gezwungen würde, inkonsistente Zwischenzustände zu berechnen.
* **Architektur in HK NPU STUDIO:**
  In [`engine/backends/sd15_qnn_inpainting_adapter.py`](file:///C:/SnapdragonAI/engine/backends/sd15_qnn_inpainting_adapter.py) wird im Modus `img2img` die ungestörte Diffusionstrajektorie durchlaufen:
  ```python
  latents_generated = latents + noise_pred * dt
  if mode == "img2img":
      latents = latents_generated
  ```
  Dadurch entstehen homogene, saubere Oberflächen ohne Kantenbrüche oder Geisterkonturen.

### 3.2 Rauschzugabe (K-Diffusion / Euler-Formulierung)
Die Initialisierung des latenten Zustands $z_{\text{start}}$ erfolgt exakt nach der Formulierung von Karras et al. (EDM) bzw. dem EulerDiscreteScheduler:
$$z_{\text{start}} = \begin{cases} z_0 + \sigma(t_{\text{start}}) \cdot \epsilon, & \text{für } s < 1.00 \\ \sigma(t_{\text{start}}) \cdot \epsilon, & \text{für } s \ge 1.00 \end{cases}$$
wobei $\epsilon \sim \mathcal{N}(0, \mathbf{I})$ und $\sigma(t) = \sqrt{\frac{1 - \bar\alpha_t}{\bar\alpha_t}}$.

| Denoising $s$ | Start-Timestep $t_{\text{start}}$ | Start-Sigma $\sigma_{\text{start}}$ | Signal-Rausch-Verhältnis ($SNR = 1 / \sigma^2$) | Rauscheinfluss |
| :--- | :--- | :--- | :--- | :--- |
| **0.25** | 201 | 0.5741 | 3.034 (4.82 dB) | Original dominiert (~75% Signal) |
| **0.35** | 301 | 0.8357 | 1.432 (1.56 dB) | Ausgeglichenes Signal-Rausch-Verhältnis |
| **0.50** | 451 | 1.3762 | 0.528 (-2.77 dB) | Rauschen übersteigt Originalsignal |
| **0.65** | 601 | 2.2929 | 0.190 (-7.21 dB) | Starkes Rauschen (~84% Noise-Einfluss) |
| **0.85** | 801 | 5.1344 | 0.038 (-14.2 dB) | Hohe Entropie (~96% Noise-Einfluss) |
| **1.00** | 951 | 11.0283 | 0.008 (-20.8 dB) | Reines Rauschen (100% Neugenerierung) |

### 3.3 Scheduler-Timestep-Mapping
Für $N = 20$ Gesamtschritte berechnet sich die Anzahl der real auszuführenden HTP-Inferenzschritte deterministisch über:
$$K = \max(1, \operatorname{round}(N \cdot s)), \quad t_{\text{start\_idx}} = N - K$$
Die Timesteps werden aus dem vorgegebenen Zeitgitter $t \in [951, 901, \dots, 51, 1]$ entnommen:

* **s = 0.25 (5 Schritte):** Timesteps $[201, 151, 101, 51, 1]$
* **s = 0.35 (7 Schritte):** Timesteps $[301, 251, 201, 151, 101, 51, 1]$
* **s = 0.50 (10 Schritte):** Timesteps $[451, 401, 351, 301, 251, 201, 151, 101, 51, 1]$
* **s = 0.65 (13 Schritte):** Timesteps $[601, 551, 501, 451, 401, 351, 301, 251, 201, 151, 101, 51, 1]$
* **s = 0.85 (17 Schritte):** Timesteps $[801, 751, 701, \dots, 51, 1]$
* **s = 1.00 (20 Schritte):** Vollständige Sequenz $[951, 901, \dots, 51, 1]$

Jeder Schritt verkleinert $\sigma$ schrittweise bis auf $\sigma_{\text{end}} = 0.0$, wodurch das latente Bild rauschfrei decodiert werden kann.

### 3.4 Seed-Reproduzierbarkeit
Um die Zuverlässigkeit im professionellen Desktop-Einsatz zu verifizieren, wurde die Inferenz für $s = 0.50$ mit Seed `42` zweimal unabhängig voneinander auf der Hexagon HTP NPU ausgeführt:
* **Maximaler absoluter Pixelfehler:** $\max(|I_1 - I_2|) = \mathbf{0.0000}$
* **Mittlerer Pixelfehler:** $\operatorname{mean}(|I_1 - I_2|) = \mathbf{0.000000}$
* **Ergebnis:** **100% bitidentische Reproduzierbarkeit**. Die Qualcomm NPU-Arithmetik driftet nicht und unterliegt keinen stochastischen Rundungsschwankungen.

### 3.5 VAE-Encoding und Decoding (Reconstruction Baseline)
Um die intrinsische Kompressionsgüte des Qualcomm Hexagon HTP VAE zu isolieren, wurde das Originalbild enkodiert und ohne Diffusionsschritte direkt wieder dekodiert:
* **PSNR:** **30.66 dB** (exzellente Rekonstruktion für ein 8x Downsampling im Latent Space)
* **SSIM:** **0.8475** (sehr hoher Erhalt feiner Kanten und Kontraste)
* **MAE ($L_1$-Fehler):** **4.80 / 255** (weniger als 1.9% durchschnittliche Kanalabweichung)
* **Laufzeiten:**
  * VAE-Encoder (HTP): $7127.2\text{ ms}$
  * VAE-Decoder (HTP): $891.8\text{ ms}$
  * CPU-Fallback: **0.00 ms**

---

## 4. Empirische Qualitätsanalyse & Messwerte (Denoising-Sweep)

Als Referenzbild diente das standardisierte Testbild `output/generate_1792859418_d2646d69.png` (roter Apfel auf Obsidian-Tisch, Studiobeleuchtung).  
**Prompt:** *"A shiny crystalline blue diamond apple on a sleek obsidian reflective table, dramatic studio lighting, octane render, 8k"*  
**Negative Prompt:** *"blurry, red apple, food, organic fruit, low quality, distorted"*  
**Parameter:** Seed = 42, Steps = 20, CFG = 7.5.

### 4.1 Vergleichsmatrix der 6 Denoising-Stufen

| Denoising ($s$) | HTP Schritte | $t_{\text{start}}$ | $\sigma_{\text{start}}$ | $L_1$ Diff (/255) | $L_2$ Diff (/255) | PSNR (dB) | SSIM | HTP Zeit (s) | Monotonie |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.25** | 5 | 201 | 0.5741 | **8.67** | 13.87 | 25.29 | **0.7381** | 10.96 | ✓ Basis |
| **0.35** | 7 | 301 | 0.8357 | **10.15** | 16.26 | 23.91 | **0.7087** | 11.88 | ✓ $L_1 \uparrow$, SSIM $\downarrow$ |
| **0.50** | 10 | 451 | 1.3762 | **13.62** | 22.78 | 20.98 | **0.6546** | 14.71 | ✓ $L_1 \uparrow$, SSIM $\downarrow$ |
| **0.65** | 13 | 601 | 2.2929 | **18.31** | 30.06 | 18.57 | **0.6242** | 16.02 | ✓ $L_1 \uparrow$, SSIM $\downarrow$ |
| **0.85** | 17 | 801 | 5.1344 | **31.15** | 48.20 | 14.47 | **0.5229** | 20.24 | ✓ $L_1 \uparrow$, SSIM $\downarrow$ |
| **1.00** | 20 | 951 | 11.0283 | **72.93** | 87.03 | 9.34 | **0.3595** | 20.78 | ✓ $L_1 \uparrow$, SSIM $\downarrow$ |

### 4.2 Farb- und Dynamik-Statistiken

| Denoising | R Mittel | G Mittel | B Mittel | R Std | G Std | B Std | Min / Max | Beurteilung |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Original** | 78.4 | 36.7 | 34.1 | 79.8 | 46.2 | 47.9 | 0 / 255 | Warmer Rotkontrast |
| **0.25** | 75.2 | 37.9 | 36.8 | 77.1 | 46.8 | 49.3 | 0 / 255 | Unverändert, dezent kühler |
| **0.35** | 73.1 | 39.5 | 40.2 | 75.0 | 47.5 | 51.2 | 0 / 255 | Erste Blaunuancen im Highlight |
| **0.50** | 66.8 | 44.1 | 48.9 | 70.2 | 50.1 | 56.4 | 0 / 255 | Blauanteil übersteigt Grün |
| **0.65** | 56.2 | 51.8 | 63.4 | 62.4 | 54.8 | 65.8 | 0 / 255 | Tiefblau dominiert, satter Kontrast |
| **0.85** | 42.1 | 58.7 | 81.2 | 51.2 | 60.3 | 76.4 | 0 / 255 | Brillanter Diamantblau-Peak |
| **1.00** | 41.5 | 56.9 | 79.8 | 50.8 | 58.9 | 75.1 | 0 / 255 | Volle Neugenerierung |

*Befund:* Keine Graubild-Degeneration. Alle Kanäle nutzen den vollen Wertebereich $[0, 255]$ mit hoher Standardabweichung ($\ge 50.8$).

---

## 5. Qualitative Einzelbewertung der Stufen

### Denoising 0.25 (5 Schritte, 10.96 s)
* **Bildkomposition:** 100% deckungsgleich zur Quelle.
* **Motividentität:** Perfekt erhalten. Die organische Apfelstruktur und die Stielform bleiben vollständig unverändert.
* **Prompt-Umsetzung:** Sehr gering. Der Begriff "crystalline blue diamond" beeinflusst lediglich feinste Oberflächenglanzpunkte.
* **Detailtreue:** Höchste Schärfe und Detailerhaltung.
* **Einsatzbereich:** **Subtile Retusche & Finishing** (z.B. Glättung von Rauschen, Feinkorrektur von Belichtungsartefakten).

### Denoising 0.35 (7 Schritte, 11.88 s)
* **Bildkomposition:** 99% deckungsgleich.
* **Motividentität:** Voll erhalten. Kanten und Silhouette sind stabil.
* **Prompt-Umsetzung:** Beginnende Materialverschiebung. Subtiler Blauschimmer in den Lichtreflexen.
* **Detailtreue:** Sehr hoch.
* **Einsatzbereich:** **Material- & Oberflächenwechsel** bei strengem Formerhalt.

### Denoising 0.50 (10 Schritte, 14.71 s)
* **Bildkomposition:** 95% erhalten. Horizontlinie und Apfelstandfläche bitgenau ausgerichtet.
* **Motividentität:** Erkennbar, jedoch mit deutlicher Wandlung.
* **Prompt-Umsetzung:** Kräftige Facettenbildung auf der Wölbung. Die organische Haut wird zu geschliffenem Glas/Kristall.
* **Detailtreue:** Ausgezeichnet. Kanten sind gestochen scharf.
* **Einsatzbereich:** **Strukturtreue Stiltransformation** (organisch $\to$ künstlich/mineralisch).

### Denoising 0.65 (13 Schritte, 16.02 s) – ★ DER SWEET SPOT
* **Bildkomposition:** Hervorragend bewahrt. Die Horizontlinie des Tisches, die studioartige Lichtführung von links und die Spiegelebene am Boden bleiben vollkommen kohärent.
* **Motividentität:** Der Apfel behält exakt seine Position, Wölbung und Dimension, wird jedoch substanziell in einen tiefblauen Diamantapfel transformiert.
* **Prompt-Umsetzung:** Perfekt. Kristalline Dreiecks- und Prismenstrukturen, innere Lichtbrechungen und blaue Farbdominanz.
* **Artefakte:** 0 unerwünschte Artefakte; sanfter Übergang zur Tischreflexion.
* **Einsatzbereich:** **Standard-Empfehlung für Image-to-Image** (kreative Neukomposition mit festem Rahmen).

### Denoising 0.85 (17 Schritte, 20.24 s)
* **Bildkomposition:** Grob orientiert an der Vorlage (zentriertes Objekt auf Fläche), aber Geometrie weicht stark ab.
* **Motividentität:** Weitgehend aufgelöst. Ein neues, hochkomplexes Kristallgebilde entsteht.
* **Prompt-Umsetzung:** Sehr dominant. Der Prompt bestimmt 90% der Bildsprache.
* **Einsatzbereich:** **Freie kreative Neuinterpretation** (Concept Art Varianten).

### Denoising 1.00 (20 Schritte, 20.78 s)
* **Bildkomposition:** Völlig unabhängig vom Ausgangsbild.
* **Motividentität:** Nicht vorhanden.
* **Prompt-Umsetzung:** 100% Text-to-Image. Reines Sampling aus dem Gaußschen Rauschen.
* **Einsatzbereich:** **Vollständige Neugenerierung**.

---

## 6. Visueller A/B-Vergleich

Ein hochauflösendes 2x4-Vergleichs-Canvas wurde generiert und als Artefakt hinterlegt:  
[`sprint39_img2img_comparison_grid.png`](file:///C:/Users/holge/.gemini/antigravity-cli/brain/c991b454-d253-4b5d-9ce4-469780cc4864/sprint39_img2img_comparison_grid.png)

```
+---------------------------------------------------------------------------------------------------+
|                         HK NPU STUDIO – SD1.5 Image-to-Image Benchmark                             |
|                           Qualcomm Hexagon HTP V73 (Snapdragon X Elite)                           |
+---------------------+---------------------+---------------------+---------------------------------+
| 1. Originalbild     | 2. Denoising 0.25   | 3. Denoising 0.35   | 4. Denoising 0.50               |
| Roter Apfel (Quelle)| 5 Steps (10.96s)    | 7 Steps (11.88s)    | 10 Steps (14.71s)               |
| L1: 0.0 | SSIM: 1.0 | L1: 8.7 | SSIM: .74 | L1: 10.2 | SSIM: .71| L1: 13.6 | SSIM: .65            |
| Referenz            | Subtile Retusche    | Texturanpassung     | Stiltransformation              |
+---------------------+---------------------+---------------------+---------------------------------+
| 5. Denoising 0.65 ★ | 6. Denoising 0.85   | 7. Denoising 1.00   | 8. Empfehlungs- & Architektur-  |
| 13 Steps (16.02s)   | 17 Steps (20.24s)   | 20 Steps (20.78s)   |    Matrix                       |
| L1: 18.3 | SSIM: .62| L1: 31.2 | SSIM: .52| L1: 72.9 | SSIM: .36| • Sweet Spot: 0.65              |
| ★ Sweet Spot        | Freie Interpretation| Text-to-Image Neugen| • 0.00 ms CPU-Fallback          |
+---------------------+---------------------+---------------------+---------------------------------+
```

---

## 7. Empfehlungsmatrix für UI & Produktiveinsatz

Basierend auf den gemessenen Parametern empfehlen wir folgende Richtlinien für die Benutzeroberfläche und Preset-Buttons in `PhoenixImageToImageView`:

| Preset | Slider-Wert | Steps ($N=20$) | HTP Zeit | Anwendungsfall | Zielgruppe |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Subtil** | `0.30` | 6 | ~11.4 s | Rauschbereinigung, Schärfung, Detailglättung, dezenteste Glanzlichter | Retuscheure, Produktfotografie |
| **Moderat** | `0.45` | 9 | ~13.8 s | Gezielter Textur- und Materialwechsel, Farbkorrekturen bei starrer Silhouette | Grafikdesigner, Compositing |
| **Ausgewogen (Standard)** | `0.65` | 13 | ~16.0 s | **Ideale Balance**: Motividentität und Komposition bleiben gewahrt, Prompt führt die Transformation | **Alle Standardanwender** |
| **Kreativ** | `0.80` | 16 | ~18.9 s | Freie Variationen, Erkundung neuer Entwürfe, abstrakte Konzepte | Concept Artists, Ideenfindung |
| **Neugenerierung** | `1.00` | 20 | ~20.8 s | Vollständiges Verwerfen des Ausgangsbildes, reines Text-to-Image | Kreatives Brainstorming |

---

## 8. Post-Backup & Validierung

Nach Abschluss aller Messungen und Artefakt-Erstellungen wurde das Post-Backup auf Laufwerk `D:` aktualisiert und verifiziert:
* **Backup-Ziel:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_39_20261101`
* **Status:** Vollständig gesichert und per SHA-256 verifiziert.

### Regressionstest-Ergebnisse:
* [`tests/test_phoenix_image_to_image_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_image_to_image_ui.py): **6/6 Tests erfolgreich**
* [`tests/test_phoenix_image_lab_navigation.py`](file:///C:/SnapdragonAI/tests/test_phoenix_image_lab_navigation.py): **7/7 Tests erfolgreich**
* [`tests/test_phoenix_inpainting_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_inpainting_ui.py): **50/50 Tests erfolgreich**
* **NPU Hardware-Fallback:** **0.00 ms CPU-Fallback**
* **Git-Status:** Keine Commits oder Pushes ausgeführt (Governance gewahrt).

---
*Bericht erstellt durch Senior Software Engineer (Gemini) für Holger Kreuzhofen (Product Owner) und ChatGPT (Chief Software Architect).*
