# SPRINT APP-ACCEPTANCE-59 REPORT
**HK NPU STUDIO – Goldtransformation mit korrigiertem CLIP-Prompt auf Qualcomm Hexagon HTP**

---

## 1. Executive Summary

| Parameter / Prüfpunkt | Vorgabe / Ziel | Feststellung (Sprint 59) | Status / Bewertung |
|---|---|---|---|
| **Sprint-ID** | `APP-ACCEPTANCE-59` | `APP-ACCEPTANCE-59` | Erfüllt |
| **Hardware** | Snapdragon X Elite – Hexagon HTP V73 | Qualcomm Hexagon HTP V73 NPU | **100% NPU (0.00 ms CPU-Fallback)** |
| **Ausgangsbasis** | Original & Maske aus Sprint 56 | Unverändert übernommen (Bit-identisch) | 100% Konformität |
| **Prompt V1** | Ohne `glass`, ohne Vögel, Gold an Pos 1–5 | Exakt nach Sprint-58-Empfehlung verwendet | 100% Konformität |
| **Vogel- / Falkenmerkmale** | Keine Schnäbel, Federn, Tierformen | **0 Vogelmerkmale** in allen 3 Varianten | Kriterium erfüllt |
| **Erhalt der Silhouette** | Geschwungene Originalskulptur | Exzellent erhalten (keine Formdeformation) | Kriterium erfüllt |
| **Umgebungserhalt (Überblendmaske)**| $100,000000\,\%$ Bit-Identität | **100,000000 %** ($MSE = 0,000000$, PSNR = 100 dB) | **Perfekt erfüllt** |
| **Umgebungserhalt (Rohmaske)** | Referenzmessung | **99,9734 %** ($MSE = 0,017$, 513 px Cosinus-Blend) | Vollständig erklärt |
| **Variante A ($D=0.90$, Seed 5901)**| $\ge 75,0\,\%$ Goldanteil | **42,19 %** Goldanteil (775 / 1.837 px) | Kriterium verfehlt |
| **Variante B ($D=0.95$, Seed 5901)**| $\ge 75,0\,\%$ Goldanteil | **39,36 %** Goldanteil (723 / 1.837 px) | Kriterium verfehlt |
| **Variante C ($D=1.00$, Seed 5901)**| $\ge 75,0\,\%$ Goldanteil | **37,40 %** Goldanteil (687 / 1.837 px) | Kriterium verfehlt |
| **Gesamturteil Sprint 59** | $\ge 75\,\%$ Gold in mind. 1 Variante | **Keine Variante erreicht 75 % Gold** | **NICHT BESTANDEN (FAIL)** |

> [!CAUTION]
> **Sprint-Status: NICHT BESTANDEN (FAIL)** gemäß Vorgabe aus Abschnitt 5:
> *"Wenn keine Variante die Kriterien erfüllt: formal NICHT BESTANDEN. Keine blinden Parameteränderungen."*
> Es wurden keine Parameter blind verstellt. Die Ergebnisse wurden vollständig quantitativ vermessen und dokumentiert.

---

## 2. Sicherheitsgate & Backup-Nachweis

1. **Git Repository Status:**
   - Commit HEAD: `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert).
   - Arbeitsverzeichnis: Keine unautorisierten Commits, Pushes oder Builds.
   - Produktionscode: **Keinerlei Modifikationen** an Produktionscode, Pipelines oder Modellen (100% Read-Only).
2. **Speicherprüfung:**
   - Laufwerk `D:` verfügbar mit **39.69 GB** freiem Speicherplatz.
3. **Pre-Backup:**
   - Zielpfad: `D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_59_20261102\PRE`
   - Manifest: `manifest_sha256.json`
   - Ergebnis: **22 von 22 Dateien** vor Ausführung bitgenau gesichert und über SHA-256 validiert.

---

## 3. Auswertung der Testmatrix

Alle drei Testläufe wurden mit identischer Maske aus Sprint 56 (1.993 Pixel BBox $[663, 367, 686, 479]$, davon 1.837 reine Objektpixel), identischem Seed (`5901`), 20 Schritten, CFG-Scale (`8.0`) und korrigiertem V1-Prompt auf der Qualcomm Hexagon HTP V73 NPU ausgeführt:

### Verwendete Prompts
- **Positiv (V1):** `"A solid polished golden brass modern table sculpture, sleek smooth curved metallic shape, pure 24k yellow gold metal, highly reflective golden surface, heavy solid brass, warm natural highlights, photorealistic, elegant tabletop centerpiece."`
- **Negativ:** `"glass, transparent, translucent, green, blue, turquoise, bird, falcon, animal, feathers, beak, white wall, room divider, wooden furniture, plants, people, blurry, deformed."`

### 3.1 Detaillierte Messwerte

| Metrik / Prüfgröße | Ausgangsbild | Sprint 56 Ref | Sprint 57 Ref (Best) | Variante A ($D=0.90$) | Variante B ($D=0.95$) | Variante C ($D=1.00$) |
|---|---|---|---|---|---|---|
| **Denoising-Stärke** | – | 0.85 | 1.00 | **0.90** | **0.95** | **1.00** |
| **NPU-Schritte (Steps)** | – | 17 | 20 | **18** | **19** | **20** |
| **Inferenzdauer (NPU)** | – | 25.38 s | 13.14 s | **13.23 s** | **12.46 s** | **13.51 s** |
| **CPU-Fallback** | – | 0.00 ms | 0.00 ms | **0.00 ms** | **0.00 ms** | **0.00 ms** |
| **Reine Objektpixel** | 1.837 px | 1.837 px | 1.871 px | **1.837 px** | **1.837 px** | **1.837 px** |
| **Gold-Pixel ($H \in [25^\circ..65^\circ], S\ge0.2, V\ge0.3$)** | 374 px | 285 px | 114 px | **775 px** | **723 px** | **687 px** |
| **Gold-Chrominanz-Anteil** | 20.36 % | 15.21 % | 6.10 % | **42,19 %** | **39,36 %** | **37,40 %** |
| **Farbton Gold / Messing ($25^\circ..65^\circ$)** | 49.5 % | 31.3 % | 26.1 % | **49,76 %** | **47,69 %** | **54,82 %** |
| **Warm-Messing / Oliv ($65^\circ..110^\circ$)** | – | – | 32.4 % | **17,26 %** | **19,32 %** | **17,80 %** |
| **Rot / Orange ($0^\circ..25^\circ$)** | – | – | – | **2,18 %** | **1,14 %** | **1,09 %** |
| **Grün ($110^\circ..160^\circ$)** | – | 29.4 % | 40.6 % | **7,84 %** | **8,93 %** | **8,27 %** |
| **Cyan / Türkis ($160^\circ..220^\circ$)** | 28.1 % | 23.8 % | 21.1 % | **21,67 %** | **22,65 %** | **17,69 %** |
| **Mittleres RGB im Goldbereich** | – | – | $[138, 142, 140]$ | **$[126, 114, 64]$** | **$[121, 110, 62]$** | **$[136, 120, 71]$** |
| **Vogel- / Falkenmerkmale** | Keine | Ja (Kopf/Schnabel)| Keine (0 %) | **Keine (0 %)** | **Keine (0 %)** | **Keine (0 %)** |
| **Silhouetten-Erhalt** | Original | Verformt | Exzellent | **Exzellent** | **Exzellent** | **Sehr gut** |
| **Identität außerhalb Überblendmaske** | 100 % | 100 % | 100 % | **100,000000 %** | **100,000000 %** | **100,000000 %** |
| **Hintergrund MSE (Überblendmaske)** | 0.0 | 0.0 | 0.0 | **0.000000** | **0.000000** | **0.000000** |
| **Hintergrund Identität (Rohmaske)** | 100 % | 99.9732 % | 99.9733 % | **99,9734 %** | **99,9733 %** | **99,9734 %** |

---

## 4. Forensische Befundung: Was hat sich verändert?

### 4.1 Dramatischer Fortschritt gegenüber Sprint 57
- In Sprint 57 erzeugte der Prompt mit `glass` an Position 5 ein **völlig entsättigtes, weißliches Mattglas** (RGB $[138, 142, 140]$, Goldanteil 4–6 %).
- In Sprint 59 hat die Eliminierung von `glass` und die Platzierung von `solid polished golden brass` an Token-Position 1–5 den Goldanteil **verachtfacht** (von 4,14 % auf **42,19 %** in Variante A).
- Die Goldpixel weisen nun echte, warme Gold- und Messing-Farbwerte auf:  
  $$\text{RGB}_{\text{Gold}} = [126, 114, 64] \quad (R > G \gg B)$$
- Die Summe aller warmen Töne (Rot/Orange + Gold/Messing + Warm-Messing/Oliv) erreicht in Variante A **69,20 %**.

### 4.2 Räumliche Aufspaltung: Warum wurde 75 % verfehlt?
Die räumliche Koordinatenanalyse liefert den exakten physikalischen Beweis:

1. **Oberer und mittlerer Skulpturenkörper ($Y < 450$, 1.364 Objektpixel):**
   - Hier grenzt das Objekt an die weiße Tischdecke.
   - **Gold-Chrominanz: 56,8 %** (775 px).
   - Inklusive warmer Glanzlichter und Messingschattierungen ist dieser Bereich zu **über 82 %** goldfarben.
2. **Unterer Ansatzbereich ($Y \ge 450$, 473 Objektpixel):**
   - Hier geht die geschwungene Glasspitze direkt in den blau-türkisen Glasstiel und Weinkühler über.
   - **Gold-Chrominanz: 0,0 %** (0 px).
   - **Cyan / Türkis: 83,1 %** (393 px).

### 4.3 Die latente Ursache: UNet Self-Attention & Latent Receptive Field
- Der $256 \times 256$ Inpainting-Crop enthält zu **96,96 % unmaskierten Kontext**, davon 33,25 % intensiven blau-türkisen Glasfuß.
- Bei $Y \ge 450$ ist die Maske lediglich 10 bis 15 Pixel breit.
- Im $8 \times 8$ Latent Space von Stable Diffusion 1.5 entspricht dies einer Breite von lediglich **1 bis 2 Latent-Zellen**.
- Die Self-Attention-Schichten des UNets interpolieren zwischen dem unmaskierten türkisen Glasstiel und der schmalen Maskenöffnung, um einen fließenden Materialübergang zu erzeugen. Dies verhindert bei dieser engen Maskengeometrie eine vollständige Golddurchfärbung bis in die unterste Spitze.

---

## 5. Bildmaterial & Deliverables

Alle Artefakte wurden erzeugt und lokal geöffnet:
1. `reports/app_acceptance_59/acceptance59_original.png` (1.894.583 Bytes)
2. `reports/app_acceptance_59/acceptance59_mask_overlay.png` (1.894.025 Bytes)
3. `reports/app_acceptance_59/acceptance59_result_a_090.png` (1.893.797 Bytes)
4. `reports/app_acceptance_59/acceptance59_result_b_095.png` (1.893.830 Bytes)
5. `reports/app_acceptance_59/acceptance59_result_c_100.png` (1.893.901 Bytes)
6. `reports/app_acceptance_59/acceptance59_comparison_grid.png` (726.962 Bytes)
7. `reports/app_acceptance_59/acceptance59_metrics.json`

### 6-Panel-Vergleichsgitter:
![6-Panel Comparison Grid](file:///C:/SnapdragonAI/reports/app_acceptance_59/acceptance59_comparison_grid.png)

---

## 6. Post-Backup & Verifikation

- Post-Backup-Ziel: `D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_59_20261102\POST`
- Vollständiges SHA-256-Manifest verifiziert.
- Keine Produktionscode-Änderungen, keine Commits, keine Pushes.
