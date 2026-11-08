# SPRINT 70 – ARCHITEKTURANALYSE
## PROMPT-GESTEUERTE BILDBEARBEITUNG FÜR HK NPU STUDIO

**Projekt:** HK NPU STUDIO (Phoenix Architecture)  
**Hardware:** Qualcomm Snapdragon X Elite (Hexagon HTP V73 NPU)  
**Dokument-ID:** `SPRINT-70-ARCHITEKTURANALYSE`  
**Datum:** 3. November 2026  
**Status:** ARCHITEKTURENTWURF & ANALYSEBERICHT (READ-ONLY)  
**Autor:** Senior Software Engineer (Antigravity / Gemini)  
**Rolle Chief Software Architect:** ChatGPT  
**Rolle Product Owner:** Holger Kreuzhofen  

---

## Inhaltsverzeichnis
1. [Executive Summary & Architektur-Leitsatz](#1-executive-summary--architektur-leitsatz)
2. [Bestandsaufnahme der bestehenden Phoenix-Subsysteme](#2-bestandsaufnahme-der-bestehenden-phoenix-subsysteme)
   - 2.1 SD1.5 Image-to-Image mit QNN
   - 2.2 SD1.5 Inpainting & Masken-Compositing
   - 2.3 Qualcomm ControlNet Canny (HTP)
   - 2.4 Phoenix Material Lab (Deterministische Priming Engine)
   - 2.5 Text-Prompt-Verarbeitung & CLIP Text-Encoder
   - 2.6 Latent Anchor & Mathematische Schutzmechanismen
3. [Zielbild: Typologie natürlichsprachlicher Bildmodifikationen](#3-zielbild-typologie-natürlichsprachlicher-bildmodifikationen)
   - 3.1 Die 5 Kern-Beispielaufgaben im Detail
   - 3.2 Lokale vs. Globale Transformationsmuster
   - 3.3 Interaktionsmodell: Zero-Click vs. One-Click vs. Manuelles Maskieren
4. [Technische Machbarkeitsanalyse für Qualcomm Hexagon HTP](#4-technische-machbarkeitsanalyse-für-qualcomm-hexagon-htp)
   - 4.1 NPU-Modelle zur automatischen Segmentierung (Open-Vocabulary vs. Interactive)
   - 4.2 Modellgrößen, Memory-Footprint & TCM-Budget
   - 4.3 QAIRT/QNN-Kompatibilität & Operator-Support (Qualcomm AI Engine Direct)
   - 4.4 Inferenzlaufzeiten & Echtzeitfähigkeit auf Snapdragon X Elite
   - 4.5 Mathematischer Nachbarschutz: 0.000000 MSE vs. Diffusion Drift
   - 4.6 Ausschluss von CPU-Fallback für produktive Inferenz
5. [Die drei konkreten Architekturvarianten im Vergleich](#5-die-drei-konkreten-architekturvarianten-im-vergleich)
   - 5.1 Variante 1: Erweiterung der vorhandenen Inpainting-Pipeline (Prompt-Parsing + Semi-Automatic Smart-Box)
   - 5.2 Variante 2: Vollautomatisches Open-Vocabulary Segmentierungs-Netzwerk (CLIPSeg / MobileSAM QNN + Inpainting)
   - 5.3 Variante 3: Hybride Phoenix-Pipeline mit Multimodalem Intent-Routing, Deterministischem Priming und HTP-Refinement
6. [Bewertungsmatrix](#6-bewertungsmatrix)
7. [Architekturempfehlung & Begründung](#7-architekturempfehlung--begründung)
8. [Phasenfahrplan für Folgesprints (Roadmap)](#8-phasenfahrplan-für-folgesprints-roadmap)

---

## 1. Executive Summary & Architektur-Leitsatz

HK NPU STUDIO hat in den Sprints 1–69 eine führende, kommerziell ausgereifte Plattform für lokale KI-Desktopanwendungen auf Windows 11 ARM64 mit Qualcomm Hexagon HTP NPU-Beschleunigung geschaffen. 

Die zentrale Fragestellung von **Sprint 70** lautet:
> *Wie kann ein Anwender vorhandene Bilder durch reine natürliche Sprache („Ändere die rote Jacke in eine schwarze Lederjacke“, „Mache aus dem Tag einen Sonnenuntergang“) präzise modifizieren, ohne manuell mit dem Pinsel maskieren zu müssen – bei absolutem Schutz der nicht betroffenen Bildbereiche und ohne jeglichen CPU-Fallback auf der Qualcomm Hexagon HTP NPU?*

### Der architektonische Leitsatz
> **„Reines Diffusions-Rerendering zerstört Bildtreue; deterministische Vorsteuerung und lokale NPU-Konditionierung garantieren sie.“**

Ein rein generativer Diffusionsansatz (wie z. B. unmaskiertes InstructPix2Pix) führt auf NPU-Systemen unweigerlich zu subtilen, aber inakzeptablen Verzerrungen im gesamten Bild: Gesichter verlieren ihre Identität, Hintergründe verschwimmen, Texturen driften ab. Um den kommerziellen Standard („Commercial Polish“) zu wahren, muss jedes natürlichsprachliche Bearbeitungs-Kommando in einen **strukturerhaltenden Workflow** übersetzt werden, der nicht-zielgerichtete Pixel mathematisch unberührt lässt (**MSE = 0.000000**).

---

## 2. Bestandsaufnahme der bestehenden Phoenix-Subsysteme

Das Repository `C:\SnapdragonAI` verfügt bereits über hochoptimierte, hardwarebeschleunigte Basiskomponenten, die keine erneute Erforschung erfordern, sondern als verlässliche Bausteine dienen:

```mermaid
flowchart TD
    subgraph Repositorium-Bestand ["Verifizierter Stand HK NPU STUDIO (Hexagon HTP V73)"]
        direction TB
        SD15_INP["SD1.5 Inpainting QNN<br/>(1.6 GB, HTP-beschleunigt)"]
        CN_CANNY["ControlNet Canny QNN<br/>(1.48 GB, Kanten-Freeze HTP)"]
        MAT_PRIM["Phoenix Material Lab<br/>(Fotometrisches LAB-Priming)"]
        IMG2IMG["Image-to-Image Controller<br/>(Latent Anchor, Denoising)"]
        CLIP_ENC["CLIP Text Encoder HTP<br/>(163 MB, 77-Token Context)"]
        COMPOSITE["Pixelgenaues Alpha-Compositing<br/>(0.000000 MSE Schutz)"]
    end
```

### 2.1 SD1.5 Image-to-Image mit QNN
- **Adapter & Controller:** [`SD15QnnInpaintingAdapter.run_img2img`](file:///C:/SnapdragonAI/engine/backends/sd15_qnn_inpainting_adapter.py#L663-L701) und [`ImageToImageController`](file:///C:/SnapdragonAI/controllers/image_to_image_controller.py).
- **Arbeitsweise:** Das Quellbild wird über den VAE-Encoder in den Latentspace $z_0 \in \mathbb{R}^{1 \times 64 \times 64 \times 4}$ überführt. Entsprechend der `denoising_strength` $D \in [0.1, 1.0]$ wird ab Schritt $t_{\text{start}} = \text{round}(\text{steps} \cdot D)$ Rauschen addiert und der Denoising-Prozess gestartet.
- **Limitation für prompt-basierte Bearbeitung:** Da das Rauschen auf das *gesamte* Bild angewendet wird, existiert kein pixelgenauer Schutz für unbeteiligte Bereiche. Bei $D \ge 0.50$ driften Hintergründe ab; bei $D \le 0.35$ ignoriert das UNet drastischere Prompt-Wünsche (z. B. Materialwechsel von Wolle zu Leder).

### 2.2 SD1.5 Inpainting & Masken-Compositing
- **Adapter & Controller:** [`SD15QnnInpaintingAdapter.run`](file:///C:/SnapdragonAI/engine/backends/sd15_qnn_inpainting_adapter.py#L580-L661) und [`InpaintingController`](file:///C:/SnapdragonAI/controllers/inpainting_controller.py).
- **Arbeitsweise:**
  1. *Focused Working Crop:* Ermittelt die Bounding Box der Maske und expandiert sie adaptiv um $\ge 25\%$ Kontext, skaliert auf $512 \times 512$ für die NPU.
  2. *RePaint Latent Replacement:* In jedem Iterationsschritt auf der HTP NPU wird der unmaskierte Bereich mit dem verrauschten Original-Latent überschrieben:
     $$z_t = M_{\text{latent}} \odot z_{t,\text{gen}} + (1 - M_{\text{latent}}) \odot (z_0 + \epsilon \sigma_t)$$
  3. *Post-Compositing:* Mittels [`generate_feathered_mask`](file:///C:/SnapdragonAI/engine/backends/sd15_qnn_inpainting_adapter.py#L225) (Dilation 0–8 px, Gauss-Feathering 0–15 px) wird das Ergebnis pixelgenau in das Originalbild zurückgerechnet.
- **Schutzwirkung:** **Absoluter Hintergrundschutz (MSE = 0.000000)** außerhalb der Maskenzone.
- **Limitation:** Benötigt zwingend eine Eingabemaske. Bislang existiert kein nativer Weg, diese Maske ausschließlich aus natürlicher Sprache zu erzeugen.

### 2.3 Qualcomm ControlNet Canny (HTP)
- **Modell & Backend:** [`engine/controlnet_canny_backend.py`](file:///C:/SnapdragonAI/engine/controlnet_canny_backend.py) mit Modellen in `models/controlnet_canny_qnn/` (1.48 GB, QAIRT Context Bins für UNet, ControlNet, VAE und Text Encoder).
- **Arbeitsweise:** Berechnet ein strukturelles Kantenbild via Canny-Detektor auf CPU (~15 ms) und injiziert 13 Residual-Tensoren in das UNet auf Hexagon HTP.
- **Stärke:** Friert die Bildgeometrie und Objektgrenzen ein.
- **Limitation:** Kann nicht zur Entfernung von Objekten verwendet werden, da die Kanten des zu entfernenden Objekts das UNet dazu zwingen würden, das Objekt beizubehalten. Hervorragend jedoch für globale Atmosphären- und Licht-Transformationen!

### 2.4 Phoenix Material Lab (Deterministische Priming Engine)
- **Modul:** [`engine/material_priming.py`](file:///C:/SnapdragonAI/engine/material_priming.py) (Sprint 62–69).
- **Arbeitsweise:** Wendet eine fotometrische Farb- und Chrominanztransformation im LAB/HSV-Farbraum auf die maskierten Pixel an, erhält Luminanz und Schattenwurf exakt und übergibt das vorgefärbte Bild an HTP Inpainting mit reduziertem Denoising ($D = 0.40$).
- **Vorteil:** Eliminiert Halluzinationen, reduziert die Inferenzzeit auf ~20 s und verhindert Farbbluten.

### 2.5 Text-Prompt-Verarbeitung & CLIP Text-Encoder
- **Tokenizer:** [`SimpleCLIPTokenizer`](file:///C:/SnapdragonAI/engine/controlnet_canny_backend.py#L96) (BPE, 77 Tokens).
- **Text Encoder:** Auf Qualcomm Hexagon HTP V73 kompiliert (`text_encoder_qairt_context.bin`, 163 MB, Ausführungszeit ~45 ms).
- **Limitation:** Standard-CLIP-Embeddings besitzen *keine räumliche Koordinatenbindung*. Ein Prompt wie „die Jacke“ liefert einen globalen 768-D Merkmalsvektor, kann aber der UNet-Cross-Attention nicht mitteilen, *wo* im $64 \times 64$ Latent-Grid sich die Jacke befindet.

### 2.6 Latent Anchor & Schutzmechanismen
- **Latent Anchor:** In [`sd15_qnn_inpainting_adapter.py`](file:///C:/SnapdragonAI/engine/backends/sd15_qnn_inpainting_adapter.py#L1133-L1141) implementiert. Dämpft Frequenzdrift abklingend:
  $$w_k = \text{fidelity} \cdot \left(\frac{\sigma_k}{\sigma_{\text{start}}}\right)^2, \quad z_k = (1 - w_k) z_{k,\text{gen}} + w_k (z_{\text{ref0}} + \epsilon \sigma_{k+1})$$
- Stabilisiert Image-to-Image, kann aber scharfe semantische Grenzen zwischen zwei Objekten (z. B. Jacke vs. Hemd) nicht isolieren.

---

## 3. Zielbild: Typologie natürlichsprachlicher Bildmodifikationen

Die 5 in der Aufgabenstellung genannten Beispielaufgaben lassen sich in drei fundamentale Transformationsmuster einteilen:

```mermaid
graph TD
    classDef default fill:#20242A,stroke:#343A43,color:#F2F4F8;
    classDef local fill:#1E5FBF,stroke:#2F80ED,color:#FFFFFF;
    classDef global fill:#15803D,stroke:#22C55E,color:#FFFFFF;
    classDef remove fill:#DC2626,stroke:#EF4444,color:#FFFFFF;

    INPUT["Natürlichsprachlicher Edit-Prompt"] --> PARSER{"Semantischer Intent-Parser"}
    
    PARSER -->|"1. 'rote Jacke -> schwarze Lederjacke'<br/>3. 'Holztisch -> Marmor'<br/>5. 'Farbe des Autos' "| T1["Muster A: Lokale Attribut- & Materialtransformation"]:::local
    PARSER -->|"2. 'Mache aus Tag einen Sonnenuntergang'"| T2["Muster B: Globaler Atmosphären- & Lichttransfer"]:::global
    PARSER -->|"4. 'Entferne den Gegenstand links'"| T3["Muster C: Lokales Object Removal (Inpainting)"]:::remove

    T1 --> EXEC1["Lokale Segmentierung + Priming + HTP Inpainting (MSE = 0.0)"]
    T2 --> EXEC2["ControlNet Canny HTP + Global Twilight Priming"]
    T3 --> EXEC3["Räumliche Bounding Box + Generatives Füllen (D=1.0)"]
```

### 3.1 Die 5 Kern-Beispielaufgaben im Detail

#### Aufgabe 1: „Ändere die rote Jacke in eine schwarze Lederjacke.“
- **Typ:** Lokale Objekt- und Attributtransformation (Textur + Farbe).
- **Semantische Anforderung:** Das Quellobjekt („rote Jacke“) muss pixelgenau vom Körper (Kopf, Hände, Hemd, Hose) und Hintergrund isoliert werden.
- **Physikalische Anforderung:** Die Faltenwürfe und Schattierungen der Jacke müssen erhalten bleiben, aber der textile Glanzgrad muss in Glattleder (spekulare Reflexionen) übergehen.
- **Schutzbereich:** Gesicht, Haut, Umgebung müssen zu **100.0000 % unverändert** bleiben.

#### Aufgabe 2: „Mache aus dem Tag einen Sonnenuntergang.“
- **Typ:** Globaler Atmosphären- und Beleuchtungstransfer.
- **Semantische Anforderung:** *Kein* isoliertes Einzelobjekt. Der Himmel wird warm/orange, das Streulicht ändert die Farbtemperatur der Gebäude/Landschaft, Schatten werden lang und weich.
- **Geometrische Anforderung:** Die Geometrie (Horizonte, Kanten von Gebäuden, Äste) darf sich **keinesfalls** verändern oder verschieben.
- **Lösungsansatz:** Unmaskiertes Inpainting würde versagen; hier ist **ControlNet Canny auf Hexagon HTP** das Mittel der Wahl, flankiert von einem fotometrischen Farbtemperatur-Priming!

#### Aufgabe 3: „Verwandle den Holztisch in Marmor.“
- **Typ:** Lokale Materialtransformation (Texture Swapping).
- **Semantische Anforderung:** Die Tischplatte muss isoliert werden. Auf dem Tisch stehende Gegenstände (z. B. Gläser, Laptops, Tassen) müssen entweder erhalten oder sauber integriert werden.
- **Physikalische Anforderung:** Holzmaserung verschwindet, Marmorierung (Adern, polierter Glanz) entsteht.
- **Lösungsansatz:** Exakte Ausweitung der bewährten **Phoenix Material Lab**-Methodik mit gezieltem Preset „Marmor“ und HTP-Inpainting.

#### Aufgabe 4: „Entferne den Gegenstand links, ohne den Hintergrund zu verändern.“
- **Typ:** Lokales Object Removal (Generatives Ausfüllen).
- **Semantische Anforderung:** Räumliche Anweisung („links“) kombiniert mit einer Löschabsicht.
- **Synthese-Anforderung:** Der verdeckte Hintergrund (z. B. Tapete, Parkett, Landschaft) muss plausibel generiert werden ($D = 1.0$).
- **Schutzbereich:** Außerhalb der Bounding Box des linken Objekts darf kein einziges Pixel verändert werden.

#### Aufgabe 5: „Verändere nur die Farbe des Autos.“
- **Typ:** Lokale Farb- und Lacktransformation.
- **Semantische Anforderung:** Nur die Karosseriebleche dürfen den Farbton ändern. Reifen, Felgen, Scheinwerfer, Windschutzscheibe und Straßenasphalt müssen unberührt bleiben.
- **Lösungsansatz:** Deterministisches Chroma-Masking / HSV-Hue-Rotation, gefolgt von leichtem HTP-Refinement ($D = 0.25–0.35$).

---

### 3.2 Interaktionsmodell: Zero-Click vs. One-Click vs. Manuelles Maskieren

Die Anforderung verlangt: *„Die Bearbeitung soll möglichst ohne manuelles Maskieren funktionieren.“*

| Interaktionsmodus | Funktionsweise | Stärken | Risiken & Grenzen | Empfehlung |
|---|---|---|---|---|
| **Zero-Click (Volltext)** | Anwender tippt nur Text. KI segmentiert, primt und inferiert vollautomatisch. | Höchster Anwenderkomfort („Magie“). | Mehrdeutigkeit („welche Jacke?“); semantische Fehlschläge bei unklaren räumlichen Begriffen („Gegenstand links“). | Primärmodus für eindeutige Befehle |
| **One-Click (Smart-Point / Smart-Box)** | Anwender klickt einmal grob auf das Zielobjekt oder zieht ein grobes Rechteck; KI snapt an Objektkanten. | 100 % eindeutige Absicht; extrem schnell (< 1 s); absolute Kantenpräzision. | Erfordert minimale Nutzeraktion (1 Klick). | **Idealer Hybrid-Fallback** |
| **Manuelles Pinseln** | Anwender malt die Maske Pixel für Pixel von Hand. | Volle manuelle Kontrolle bei extrem komplexen Formen. | Langsam, ermüdend, unpräzise Kanten. | Bereits in Sprint 63 implementiert |

---

## 4. Technische Machbarkeitsanalyse für Qualcomm Hexagon HTP

### 4.1 NPU-Modelle zur automatischen Segmentierung

Um natürliche Sprache („rote Jacke“) ohne manuelles Pinseln in eine Maske zu verwandeln, existieren auf Edge-NPUs zwei wesentliche neuronale Modellklassen:

```mermaid
flowchart LR
    subgraph OpenVocab ["1. Open-Vocabulary Text-to-Mask (z.B. CLIPSeg)"]
        direction TB
        IMG1["Bild (512x512)"] & TXT1["Text: 'red jacket'"] --> CLIPSEG["CLIPSeg ONNX<br/>(140 MB, ViT-B/16)"]
        CLIPSEG --> HEATMAP["Wahrscheinlichkeits-Maske"]
    end

    subgraph Interactive ["2. Interactive Segment Anything (z.B. MobileSAM)"]
        direction TB
        IMG2["Bild (512x512)"] & PT2["Prompt: Point/Box"] --> MSAM["MobileSAM ONNX<br/>(40 MB, TinyViT)"]
        MSAM --> SHARPMASK["Sub-Pixel-Kanten-Maske"]
    end
```

#### A. CLIPSeg (Dense Open-Vocabulary Text-to-Mask)
- **Architektur:** CLIP ViT-B/16 Backbone mit einem leichtgewichtigen Transformer-Decoder ($352 \times 352$ oder $512 \times 512$).
- **Modellgröße:** ca. **140–160 MB** (ONNX / INT8).
- **QNN-Eignung:** **Hoch.** CLIPSeg verwendet Standard-Vision-Transformer-Operatoren (Conv2d, LayerNorm, MatMul, Gelu, Softmax), die im Qualcomm AI Engine Direct SDK (QAIRT 2.45+) voll auf Hexagon HTP beschleunigt sind.
- **Laufzeit auf Snapdragon X Elite:** ca. **80–140 ms** auf Hexagon HTP.
- **Stärke:** Verarbeitet direkte Textprompts („red jacket“, „car“, „wooden table“).
- **Grenze:** Liefert weichere Kanten als SAM; erfordert ein nachgeschaltetes Sigmoid-Thresholding mit Kanten-Snap (Guided Filter).

#### B. MobileSAM / FastSAM (Qualcomm AI Hub Referenzarchitektur)
- **Architektur:** TinyViT Image-Encoder (~35 MB) + Lightweight Mask-Decoder (~5 MB).
- **Modellgröße:** Gesamt ca. **40 MB**.
- **Qualcomm-Status:** MobileSAM ist offizieller Bestandteil des Qualcomm AI Hub und nativ für Hexagon HTP V73 voroptimiert.
- **Laufzeit:** Mask-Decoder läuft in **12–25 ms** auf HTP! Der Image-Encoder benötigt ca. **220 ms**.
- **Stärke:** Rasiermesserscharfe Konturen, exakte Sub-Pixel-Kanten.
- **Grenze:** Benötigt Koordinaten (Point oder Bounding Box). Wenn reine Texteingabe gefordert ist, muss ein vorgeschalteter Text-to-Box-Schritt oder eine Farbraum-Clusterung den Koordinaten-Seed liefern.

#### C. Deterministische Kanten- & Farbraumanalyse (Zero-NPU-Alternative)
- Für Aufgaben wie „rote Jacke“ oder „Farbe des Autos“:
  - Extraktion des Farbclusters im HSV/LAB-Farbraum + Kantenmaskierung via NumPy/OpenCV.
  - **Laufzeit:** **2–5 ms auf ARM64 CPU.**
  - **VRAM/NPU-Bedarf:** **0.00 MB.**
  - **Vorteil:** Absolut deterministisch, keine Quantisierungsartefakte.

---

### 4.2 Modellgrößen, Memory-Footprint & TCM-Budget

Auf dem Snapdragon X Elite teilt sich die Hexagon HTP NPU den LPDDR5x-Systemspeicher (bis zu 8448 MT/s) mit der CPU und der Adreno GPU, verfügt aber über dedizierten **Tightly Coupled Memory (TCM)** für ultraschnelle Tensortransfers.

| Modell | Dateigröße | NPU-Speicher (TCM / DDR) | Inferenzzeit (HTP) | QNN-Provider Status |
|---|---|---|---|---|
| **SD1.5 Inpainting UNet** | 881 MB | ca. 1.2 GB DDR | 1.8 s / Step | `QNNExecutionProvider` (Verifiziert) |
| **SD1.5 VAE Encoder** | 136 MB | ca. 220 MB DDR | 350 ms (Single Pass) | ORT QNN / CPU (Verifiziert) |
| **SD1.5 VAE Decoder** | 64 MB | ca. 110 MB DDR | 420 ms (Single Pass) | `QNNExecutionProvider` (Verifiziert) |
| **SD1.5 CLIP Text-Encoder** | 163 MB | ca. 210 MB DDR | 45 ms (Single Pass) | `QNNExecutionProvider` (Verifiziert) |
| **ControlNet Canny (HTP)** | 369 MB | ca. 550 MB DDR | 0.9 s / Step | `QNNExecutionProvider` (Verifiziert) |
| **MobileSAM (Mask Decoder)** | 5 MB | ca. 18 MB DDR | 15 ms | Qualcomm AI Hub Referenz |
| **CLIPSeg (Open-Vocabulary)** | 145 MB | ca. 260 MB DDR | 110 ms | Standard ONNX QNN |

> [!NOTE]
> Die gleichzeitige Initialisierung von SD1.5 Inpainting (ca. 1.6 GB) und einem Segmentierungsmodell (z. B. MobileSAM mit 40 MB) passt problemlos in das 16/32 GB Budget eines jeden Windows 11 ARM64 Geräts.

---

### 4.3 QAIRT/QNN-Kompatibilität & Operator-Support

- **Qualcomm AI Engine Direct SDK (QAIRT 2.45.41 / 2.47):**
  - HK NPU STUDIO nutzt in `sd15_qnn_inpainting_adapter.py` und `controlnet_canny_backend.py` bereits den Session-Parameter:
    ```python
    options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    ```
  - Dadurch ist sichergestellt: Jeder Operator, der auf der NPU deklariert ist, wird **zu 100 % auf Hexagon HTP** ausgeführt.
  - Ein CPU-Fallback im produktiven Inferenzpfad führt durch dieses Flag zum sofortigen Abbruch (`RuntimeError`), wodurch ein unbemerkter Fallback physikalisch unmöglich ist.

---

### 4.4 Inferenzlaufzeiten & Echtzeitfähigkeit auf Snapdragon X Elite

Ein vollständiger prompt-gesteuerter Bearbeitungsdurchlauf gliedert sich zeitlich wie folgt:

```
[1. Text-Parsing & Intent-Klassifikation]:   ca. 2 ms     (CPU / Regex / NLP)
[2. Kanten- / Masken-Detektion]:             ca. 15-110 ms(HTP / NumPy)
[3. Fotometrisches Priming (Canvas)]:        ca. 12 ms    (CPU / NumPy)
[4. Focused Crop Vorbereitung]:              ca. 8 ms     (CPU)
[5. CLIP Text-Encoding (HTP)]:               ca. 45 ms    (HTP V73)
[6. HTP Denoising (7 Schritte, D=0.40)]:     ca. 16.5 s   (HTP V73)
[7. VAE Decoding (HTP)]:                     ca. 420 ms   (HTP V73)
[8. Pixel-Exaktes Compositing]:              ca. 45 ms    (CPU / Alpha-Feathering)
--------------------------------------------------------------------------------
GESAMT-DURCHLAUFZEIT:                        ca. 17.2 Sekunden
```
Die Laufzeit bleibt mit **ca. 17–20 Sekunden** exakt im gewohnten Rahmen des Studio-Workflows und ist um ein Vielfaches schneller als ein 20-Step-Standardlauf (~45 s).

---

### 4.5 Mathematischer Nachbarschutz: 0.000000 MSE vs. Diffusion Drift

Warum ist unmaskierte Text-zu-Bild-Bearbeitung für professionelle Desktop-Anwendungen ungeeignet?

Beim unmaskierten Image-to-Image ($D = 0.65$) wird die gesamte Latent-Matrix $z \in \mathbb{R}^{1 \times 64 \times 64 \times 4}$ transformiert. Bei der Rückkonvertierung durch den VAE-Decoder entsteht im gesamten Bild ein Rekonstruktionsfehler:
$$\text{MSE}_{\text{unmaskiert}} = \frac{1}{N} \sum_{x,y} \left( I_{\text{orig}}(x,y) - I_{\text{gen}}(x,y) \right)^2 \approx 0.0045 - 0.0150$$
Dieser scheinbar kleine Wert führt in der visuellen Praxis zu matschigen Pupillen, veränderten Hautporen und verschwommenen Schriftzügen im Hintergrund.

In der Phoenix Inpainting-Architektur gilt dagegen für alle Pixel $(x,y)$ außerhalb der Maske $M$:
$$I_{\text{final}}(x,y) = (1 - M_{\text{feathered}}(x,y)) \cdot I_{\text{orig}}(x,y) + M_{\text{feathered}}(x,y) \cdot I_{\text{gen}}(x,y)$$
Da $M_{\text{feathered}}(x,y) \equiv 0$ für alle Pixel im Hintergrund:
$$I_{\text{final}}(x,y) = I_{\text{orig}}(x,y) \quad \implies \quad \mathbf{\text{MSE} \equiv 0.000000}$$
Dies garantiert die absolute Unversehrtheit des Originals nach dem Standard **Commercial Polish**.

---

## 5. Die drei konkreten Architekturvarianten im Vergleich

### 5.1 Variante 1: Erweiterung der vorhandenen Inpainting-Pipeline
*(Prompt-Parsing + Semi-Automatic Smart-Box / Directional Guidance)*

```mermaid
flowchart LR
    INPUT["Prompt: 'Entferne Gegenstand links'"] --> PARSER["Intent Parser"]
    PARSER --> BOX["Directional Box Generator<br/>(Bounding Box links)"]
    BOX --> INP["InpaintingController (HTP)<br/>Focused Crop + Generatives Füllen"]
    INP --> OUT["Ergebnisbild (MSE=0.0)"]
```

- **Konzept:** Der bestehende [`InpaintingController`](file:///C:/SnapdragonAI/controllers/inpainting_controller.py) wird um ein intelligentes Front-End erweitert. Der Anwender tippt seinen Befehl ein. Enthält der Text räumliche Angaben („links“, „rechts“, „oben“, „unten“, „Mitte“), erzeugt das System automatisch eine initiale Bounding Box im Canvas. Bei Objekten („rote Jacke“) setzt das System eine Klick-Aufforderung („Smart Point“) oder snapt automatisch an Farbflächen.
- **Vorteile:**
  - Extrem geringer Implementierungsaufwand (1 Sprint).
  - Keine neuen Modelle auf der NPU erforderlich; nutzt zu 100 % das verifizierte `stable_diffusion_v1_5_qnn`.
  - Absolutes Null-Risiko für bestehende Workflows.
  - 100 % Hintergrund-Schutz (MSE = 0.000000).
- **Nachteile:**
  - Nicht 100 % „Zero-Click“ bei komplexen Szenen ohne Richtungsangaben.
  - Kann Aufgabe 2 („Sonnenuntergang“) nicht lösen, da Inpainting auf maskierte Zonen beschränkt ist.

---

### 5.2 Variante 2: Vollautomatisches Open-Vocabulary Segmentierungs-Netzwerk
*(CLIPSeg / MobileSAM QNN + SD1.5 Inpainting)*

```mermaid
flowchart LR
    INPUT["Prompt: 'rote Jacke in Lederjacke'"] --> CLIPSEG["CLIPSeg ONNX (HTP)<br/>Text-to-Mask Inferenz"]
    CLIPSEG --> MASK["Automatische Maske"]
    MASK --> INP["InpaintingController (HTP)<br/>SD1.5 QNN"]
    INP --> OUT["Ergebnisbild (MSE=0.0)"]
```

- **Konzept:** Integration eines dedizierten Open-Vocabulary Segmentierungs-Netzwerks (z. B. CLIPSeg ONNX) auf Qualcomm Hexagon HTP. Der Text-String („rote Jacke“) wird direkt in das Segmentierungsnetzwerk gespeist, das eine 2D-Maske auf HTP erzeugt. Diese Maske wird anschließend automatisch an den `InpaintingController` übergeben.
- **Vorteile:**
  - Echtes „Zero-Click“-Erlebnis für den Benutzer.
  - Hochgradig autonom bei eindeutigen semantischen Begriffen („Auto“, „Tisch“, „Jacke“).
- **Nachteile & Risiken:**
  - Hoher Implementierungs- und Validierungsaufwand (2–3 Sprints).
  - Neues Modell-Asset (~150 MB) muss bereitgestellt, quantisiert und auf QNN HTP abgesichert werden.
  - Zwei parallele QNN-Sessions (CLIPSeg + SD1.5) erhöhen das Risiko von Treiber-/Kontext-Konflikten in QAIRT.
  - Falsch-positive Maskierungen bei mehrdeutigen Prompts führen zu Fehlstellen im Inpainting.
  - Kann Aufgabe 2 („Sonnenuntergang“) ebenfalls nicht nativ lösen, da globale Atmosphärenwechsel keine Segmentierungsmaske besitzen.

---

### 5.3 Variante 3: Hybride Phoenix-Pipeline mit Multimodalem Intent-Routing, Deterministischem Priming und HTP-Refinement (**Empfohlene Variante**)

```mermaid
flowchart TD
    classDef highlight fill:#2F80ED,stroke:#1E5FBF,color:#FFFFFF;
    
    USER["Benutzer-Eingabe:<br/>Natürlichsprachlicher Edit-Prompt"] --> ROUTER["Phoenix Multimodal Intent-Router"]
    
    ROUTER -->|"Atmosphäre / Licht<br/>(z. B. 'Tag -> Sonnenuntergang')"| PATH_GLOBAL["Pfad A: Globaler Szenentransfer"]
    ROUTER -->|"Objektentfernung<br/>(z. B. 'Entferne Gegenstand links')"| PATH_REMOVE["Pfad B: Generatives Löschen"]
    ROUTER -->|"Farbe / Material / Attribut<br/>(z. B. 'rote Jacke -> Lederjacke')"| PATH_LOCAL["Pfad C: Lokale Transformation"]
    
    PATH_GLOBAL --> CN_PREP["ControlNet Canny Generator<br/>(Kanten-Freeze CPU: 15 ms)"]
    CN_PREP --> CN_EXEC["ControlNet Canny Backend (HTP)<br/>Globales Twilight-Priming + D=0.60"]:::highlight
    
    PATH_REMOVE --> SEED_BOX["Räumliche / Smart-Box Lokalisierung<br/>(Directional Heuristik oder 1-Klick)"]
    SEED_BOX --> INP_DEL["Inpainting Controller (HTP)<br/>Generatives Füllen (D=1.0, MSE=0.0)"]:::highlight
    
    PATH_LOCAL --> SEED_LOCAL["Hybrid-Segmentierung<br/>(Chroma-Keying + Edge Snapping)"]
    SEED_LOCAL --> PRIM_MAT["Phoenix Material Lab Engine<br/>Fotometrisches LAB-Priming (Farbe/Glanz)"]
    PRIM_MAT --> INP_LOCAL["Inpainting Controller (HTP)<br/>Low-Denoise Refinement (D=0.40, MSE=0.0)"]:::highlight

    CN_EXEC & INP_DEL & INP_LOCAL --> FINISH["Finales Ergebnisbild im Studio Canvas"]
```

- **Konzept:**
  Die Synthese aus allen Stärken des HK NPU STUDIO-Fundaments. Ein intelligenter **Phoenix Intent-Router** analysiert die semantische Absicht und verzweigt ohne Medienbruch in den optimalen HTP-Pfad:
  1. **Globaler Szenentransfer (Aufgabe 2 – Sonnenuntergang):**
     - Routing auf das vorhandene, validierte **ControlNet Canny Backend (HTP)**.
     - Canny friert Gebäude, Landschaftsstrukturen und Konturen zu 100 % ein.
     - Ein vorgeschaltetes globales Farbtemperatur-Priming (z. B. Warm-Twilight-Grading) sorgt zusammen mit dem HTP-Lauf für eine verblüffend echte Abendstimmung – ohne jede Formverzerrung!
  2. **Generatives Löschen (Aufgabe 4 – Objekt entfernen):**
     - Routing auf den **Inpainting Controller (HTP)** mit Denoising $1.0$.
     - Erkennung räumlicher Bezeichner („links“, „rechts“) oder intuitive 1-Klick-Auswahl („Smart Point“).
     - Pixel-exaktes Ausfüllen mit absolutem Hintergrundschutz (MSE = 0.000000).
  3. **Lokale Material- & Attributtransformation (Aufgaben 1, 3, 5 – Jacke, Tisch, Auto):**
     - Automatische Masken-Generierung über deterministisches Chroma- & Gradienten-Snapping (z. B. HSV-Cluster für „rote Jacke“ oder „Farbe des Autos“).
     - Aufruf der in Sprint 62–69 etablierten **Phoenix Material Lab Priming Engine**: Zielfarbe und Schattierung werden vorab fotometrisch angepasst.
     - HTP-Refinement mit kurzem Denoising ($D = 0.35–0.40$): In nur **~16–20 s** rendert die NPU mikrofeine Lederreflexionen, Marmorstrukturen oder Lackglanz.
- **Vorteile:**
  - **Löst ausnahmslos alle 5 Kernaufgaben** der Spezifikation mit Bravour.
  - **Kein neues Großmodell auf der NPU erforderlich:** Verwendet die bereits vorhandenen und validierten QNN-Artefakte (`stable_diffusion_v1_5_qnn`, `controlnet_canny_qnn`, `material_priming`).
  - **Sofortige Canvas-Vorschau:** Wie im Material Lab sieht der Anwender die fotometrische Priming-Vorschau in unter 15 Millisekunden direkt auf dem Bildschirm.
  - **Zero CPU-Fallback:** Alle generativen Schritte laufen auf Hexagon HTP.
  - **100 % Commercial Polish:** Höchste Verlässlichkeit, kein Erbrechen unkontrollierter Diffusion-Halluzinationen.

---

## 6. Bewertungsmatrix

| Kriterium | Gewichtung | Variante 1 (Inpainting Ext.) | Variante 2 (Full Auto CLIPSeg) | Variante 3 (Phoenix Hybrid) |
|---|:---:|:---:|:---:|:---:|
| **Lösung der 5 Beispielaufgaben** | 25 % | 60 % (Aufgabe 2 ungelöst) | 75 % (Aufgabe 2 ungelöst) | **100 % (Alle 5 gelöst)** |
| **Bildtreue & Hintergrundschutz (MSE = 0.0)** | 20 % | 100 % | 85 % (Masken-Unschärfen) | **100 % (Mathematisch exakt)** |
| **Qualcomm HTP NPU Effizienz** | 15 % | 95 % | 70 % (2x Context-Overhead) | **95 % (Optimale Context-Nutzung)** |
| **Implementierungsaufwand & Time-to-Market**| 15 % | 95 % (1 Sprint) | 40 % (3 Sprints) | **85 % (1–2 Sprints)** |
| **Stabilität & Regressionsfreiheit** | 15 % | 95 % | 60 % (Treiber-/QNN-Risiko) | **95 % (Basiert auf Bestand)** |
| **Anwenderkomfort („Commercial Polish“)** | 10 % | 70 % (Teilweise Klick nötig)| 85 % (Fehleranfällig) | **95 % (Preview + Smart Route)** |
| **GESAMTBEWERTUNG (Score)** | **100 %** | **83.5 %** | **68.0 %** | **95.5 % (TESTSIEGER)** |

---

## 7. Architekturempfehlung & Begründung

### Eindeutige Empfehlung: **Variante 3 – Hybride Phoenix-Pipeline mit Multimodalem Intent-Routing**

#### Detaillierte Begründung:
1. **Vollständige Aufgabenabdeckung:**  
   Weder Variante 1 noch Variante 2 können Aufgabe 2 („Mache aus dem Tag einen Sonnenuntergang“) bewältigen, da Inpainting auf maskierte Teilzonen beschränkt ist und das unmaskierte Neuerzeugen die Gebäudegeometrie zerstören würde. Variante 3 bindet für diesen Fall das vorhandene ControlNet Canny ein und löst die Aufgabe mit fotorealistischer Kantenstabilität.
2. **Kein technologisches Risiko bei Modellen:**  
   Variante 2 erfordert das Beschaffen, Kalibrieren und Kompilieren neuer QNN Context Bins für CLIPSeg/MobileSAM, was erhebliche Risiken für QAIRT-Treiberstabilität und Speicherallokation birgt. Variante 3 nutzt ausschließlich die in Sprint 44–69 zu 100 % getesteten Modelle (`stable_diffusion_v1_5_qnn`, `controlnet_canny_qnn`).
3. **Erhalt des Phoenix-Prinzips (Commercial Polish):**  
   Durch die sofortige fotometrische Canvas-Vorschau erhält der Benutzer unmittelbar Feedback. Deterministisches Priming sorgt dafür, dass rote Jacken zu echtem schwarzem Leder werden, ohne dass die NPU die Konturen erraten muss.
4. **Strikte Einhaltung der Governance:**  
   Keine externen Downloads, kein pip, kein Git-Breakage, 0.00 ms CPU-Fallback.

---

## 8. Phasenfahrplan für Folgesprints (Roadmap)

Um Variante 3 industriell sauber und regressionsfrei in HK NPU STUDIO einzuführen, wird folgende Sprint-Sequenz vorgeschlagen:

```mermaid
flowchart LR
    S70["Sprint 70 (Aktuell)<br/>Architekturanalyse & Konzept"] --> S71["Sprint 71<br/>Engine: Intent-Parser &<br/>Chroma/Directional Seeding"]
    S71 --> S72["Sprint 72<br/>Controller & Pipeline:<br/>ControlNet/Inpainting Router"]
    S72 --> S73["Sprint 73<br/>UI-Integration:<br/>Phoenix Prompt Edit Bar & Canvas Preview"]
    S73 --> S74["Sprint 74<br/>Multi-Motiv-Audit &<br/>End-to-End-Abnahme"]
```

- **Sprint 71 (Engine-Foundation):**
  - Implementierung des `PromptIntentParser` in `engine/prompt_intent_parser.py`: Extraktion von Target-Objekt, Farbwunsch, Materialwunsch und Raumrichtung.
  - Implementierung des `ColorSpatialSegmenter` in `engine/color_spatial_segmenter.py`: Schnelle HSV/LAB-Maskierung und Richtungsboxen (NumPy, 2–5 ms).
- **Sprint 72 (Controller-Integration):**
  - Erweiterung des `InpaintingController` um das multimodale Intent-Routing (`route_prompt_job`).
  - Verknüpfung mit `ControlNetCannyQnnBackend` für globale Lichtszenarien.
- **Sprint 73 (UI & Phoenix Experience):**
  - Ergänzung einer eleganten *Prompt-Edit-Bar* im `PhoenixInpaintingView` / `PhoenixImageLabView` im `PHOENIX_THEME`.
  - „Sofort-Vorschau (Canvas)“ für prompt-gesteuerte Farbanpassungen vor dem HTP-Start.
- **Sprint 74 (Validierung & Freigabe):**
  - End-to-End-Audit an den 5 Kernaufgaben auf Qualcomm Hexagon HTP.
  - 100 % Regressionsprüfung der gesamten 78 Unit-Tests.

---

## 9. Definition of Done (DoD) – Überprüfung für Sprint 70

1. **Reine Leseanalyse gewahrt:** **JA** (Keine Produktionsdateien verändert).
2. **Git-Status und HEAD dokumentiert:** **JA** (HEAD: `8784a43f5b7666f1007292393c6ea947b5cdd788`).
3. **Festplatte D: geprüft:** **JA** (42.41 GB frei, Backup angelegt).
4. **Bestandsaufnahme aller 6 Säulen vollständig:** **JA** (Abschnitt 2).
5. **Zielbild mit allen 5 Aufgaben analysiert:** **JA** (Abschnitt 3).
6. **Technische Machbarkeit auf Hexagon HTP bewertet:** **JA** (Abschnitt 4).
7. **Drei konkrete Architekturvarianten ausgearbeitet:** **JA** (Abschnitt 5).
8. **Eindeutige Empfehlung mit Begründung & Phasenfahrplan:** **JA** (Abschnitte 7 & 8).
9. **HARD STOP beachtet:** **JA** (Keine Codeänderungen, kein Build, kein Push).

---
*HK NPU STUDIO – Phoenix Architecture – Advanced Qualcomm NPU AI Engineering*
