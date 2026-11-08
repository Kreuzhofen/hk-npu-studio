# SPRINT APP-ACCEPTANCE-60 REPORT
**HK NPU STUDIO – Materialgrenze und Maskenpräzision auf Qualcomm Hexagon HTP**

---

## 1. Executive Summary

| Parameter / Prüfpunkt | Vorgabe / Ziel | Feststellung (Sprint 60) | Status / Bewertung |
|---|---|---|---|
| **Sprint-ID** | `APP-ACCEPTANCE-60` | `APP-ACCEPTANCE-60` | Erfüllt |
| **Hardware** | Snapdragon X Elite – Hexagon HTP V73 | Qualcomm Hexagon HTP V73 NPU | **100% NPU (0.00 ms CPU-Fallback)** |
| **Ausgangsbasis** | Original & Maske aus Sprint 56 | Unverändert übernommen | 100% Konformität |
| **Prompt V1** | Sprint-59-V1 unverändert | Exakt verwendet | 100% Konformität |
| **Vogel- / Tierhalluzinationen** | Keine Schnäbel, Federn, Tiere | **0 Artefakte** in allen 3 Varianten | Kriterium erfüllt |
| **Erhalt der Silhouette** | Geschwungene Originalskulptur | Exzellent erhalten | Kriterium erfüllt |
| **Glasfuß unverändert** | Bit-identisch bei $Y \ge 470$ | **Variant B & C: MSE = 0.000000** | **Perfekt erfüllt** |
| **Hintergrund (Überblendmaske)**| $100,000000\,\%$ Bit-Identität | **100,000000 %** ($MSE = 0,000000$) | **Perfekt erfüllt** |
| **Variant A (Referenz - Originalmaske)**| $\ge 75,0\,\%$ Goldanteil | **44,09 %** Gold (810 / 1.837 px) | Kriterium verfehlt |
| **Variant B (Lokale Erweiterung 2–3 px)**| $\ge 75,0\,\%$ Goldanteil | **53,81 %** Gold (932 / 1.732 px) | Kriterium verfehlt |
| **Variant C (Erweiterte Zone 4–5 px)**| $\ge 75,0\,\%$ Goldanteil | **57,92 %** Gold (1.042 / 1.799 px) | Kriterium verfehlt |
| **Summe warmer Töne (Variant C)** | Informationell | **84,33 %** (Gold + Messing + Orange) | Hohe Materialtreue |
| **Gesamturteil Sprint 60** | $\ge 75\,\%$ Gold in mind. 1 Variante | **Keine Variante erreicht 75 % Gold** | **NICHT BESTANDEN (FAIL)** |

> [!CAUTION]
> **Sprint-Status: NICHT BESTANDEN (FAIL)** gemäß Vorgabe aus Abschnitt 5:
> *"Wenn keine Variante besteht: NICHT BESTANDEN. Keine weiteren blinden Maskenänderungen."*
> Es wurden keine Parameter blind verstellt. Die physikalischen und geometrischen Ursachen wurden lückenlos vermessen und dokumentiert.

---

## 2. Sicherheitsgate & Backup-Nachweis

1. **Git Repository Status:**
   - Commit HEAD: `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert).
   - Arbeitsverzeichnis: Keine unautorisierten Commits, Pushes oder Builds.
   - Produktionscode: **Keinerlei Modifikationen** an Produktionscode, Pipelines oder Modellen (100% Read-Only).
2. **Speicherprüfung:**
   - Laufwerk `D:` verfügbar mit **39.67 GB** freiem Speicherplatz.
3. **Pre-Backup:**
   - Zielpfad: `D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_60_20261102\PRE`
   - Manifest: `manifest_sha256.json`
   - Ergebnis: **21 von 21 Dateien** vor Inferenz bitgenau gesichert und über SHA-256 validiert.

---

## 3. Forensische Vorprüfung der Objektkontur ($Y \ge 450$)

Gemäß Abschnitt 2 wurden vor jeglicher Maskenanpassung die 5 geometrischen und materialphysikalischen Parameter vermessen:

| Prüfpunkt | Gemessener Wert / Befund | Physikalische / Geometrische Bedeutung |
|---|---|---|
| **1. Tatsächliche Breite der Skulptur** | • $Y=450$: **23 px** ($X \in [656..678]$)<br>• $Y=455$: **16 px** ($X \in [658..673]$)<br>• $Y=460$: **6 px** ($X \in [660..665]$)<br>• $Y=465$: **1 px** ($X=663$) | Die Skulptur verjüngt sich nach unten hin drastisch von 23 Pixeln auf eine feine Spitze. |
| **2. Abstand zum Glasfuß** | • **Vertikal: 0 Pixel** (direkte Stoßkante bei $Y=466$)<br>• **Horizontal bei $Y=450..460$: 2 bis 4 Pixel** links | Die Skulpturenspitze sitzt unmittelbar auf dem Glasfuß auf; im Hintergrund links schimmert der Fuß durch. |
| **3. Position der Materialgrenze** | **$Y = 465 \pm 1$ Pixel** | Oberhalb: Grünes Kunstglas ($G > R$ und $G > B, B < 125$).<br>Unterhalb: Türkisblaues Glas ($B \ge 130, G \ge 140, R \ll B$). |
| **4. Breite der schmalen Engstelle** | **4 Pixel** ($X \in [661..664]$) bei $Y \in [462..464]$ | Die engste Stelle der Skulptur misst exakt 4 Pixel. |
| **5. Mögliche Überlappung zwischen Objekt und Fuß** | **187 Pixel Überlappung in Originalmaske A** ($Y \in [466..478]$) | Die Originalmaske A aus Sprint 56 ragte um 13 Pixel vertikal in den türkisen Glasfuß hinein! |

---

## 4. Auswertung der Testmatrix

Alle drei Testläufe wurden mit identischem Seed (`6001`), identischen 20 Schritten, CFG-Scale (`8.0`), Denoise (`0.90`) und identischem V1-Prompt auf der Qualcomm Hexagon HTP V73 NPU ausgeführt:

### 4.1 Detaillierte Messwerte

| Metrik / Prüfgröße | Ausgangsbild | Sprint 59 Ref (A) | Variant A (Referenz) | Variant B (Lokal 2–3 px) | Variant C (Zone 4–5 px) |
|---|---|---|---|---|---|
| **Maske** | – | Sprint 56 Maske | Originalmaske A | Maske B (Engstelle +2-3px) | Maske C (Zone +4-5px) |
| **Glasfuß-Ausschluss** | – | Nein | Nein ($Y \le 478$) | **Ja ($Y \le 465$)** | **Ja ($Y \le 465$)** |
| **Aktive Maskenpixel** | – | 1.946 px | 1.946 px | **1.822 px** | **1.889 px** |
| **Reine Objektpixel** | 1.837 px | 1.837 px | 1.837 px | **1.732 px** | **1.799 px** |
| **Inferenzdauer (NPU)** | – | 13.23 s | **14.12 s** | **12.06 s** | **11.75 s** |
| **CPU-Fallback** | – | 0.00 ms | **0.00 ms** | **0.00 ms** | **0.00 ms** |
| **Gold-Pixel ($H \in [25..65], S\ge0.2, V\ge0.3$)** | 374 px | 775 px | **810 px** | **932 px** | **1.042 px** |
| **Gold-Chrominanz-Anteil** | 20.36 % | 42.19 % | **44,09 %** | **53,81 %** | **57,92 %** |
| **Farbton Gold/Messing ($25^\circ..65^\circ$)** | 49.5 % | 49.76 % | **50,14 %** | **59,18 %** | **64,87 %** |
| **Warm-Messing / Oliv ($65^\circ..110^\circ$)** | – | 17.26 % | **22,37 %** | **16,92 %** | **19,18 %** |
| **Rot / Orange ($0^\circ..25^\circ$)** | – | 2.18 % | **0,00 %** | **1,85 %** | **0,28 %** |
| **Summe aller warmen Töne** | – | 69.20 % | **72,51 %** | **77,95 %** | **84,33 %** |
| **Cyan / Türkis ($160^\circ..220^\circ$)** | 28.1 % | 21.67 % | **20,14 %** | **11,95 %** | **5,84 %** |
| **Grün ($110^\circ..160^\circ$)** | – | 7.84 % | **6,97 %** | **9,01 %** | **9,56 %** |
| **Unterer Bereich ($Y \in [450..465]$) Gold** | 0.0 % | 0.0 % | **33,11 %** | **10,48 %** | **42,08 %** |
| **Glasfuß MSE ($Y \ge 470$)** | 0.0 | 64.67 | **64,6735** | **0,000000** | **0,000000** |
| **Feathered Blend Hintergrund-Identität** | 100 % | 100 % | **100,000000 %** | **100,000000 %** | **100,000000 %** |
| **Feathered Blend Hintergrund MSE** | 0.0 | 0.0 | **0.000000** | **0.000000** | **0.000000** |

---

## 5. Detaillierte Befundung & Analyse

### 5.1 Wirkung der Maskenkorrektur (Variant C)
1. **Dramatische Reduktion von Cyan/Türkis:**  
   In Sprint 59 betrug der Cyan-Anteil im Objekt noch **21,67 %**. Durch den präzisen Ausschluss des Glasfußes ($Y \ge 466$) und die 4–5 px Erweiterung der Übergangszone sank der Cyan-Anteil in Variant C auf **5,84 %**!
2. **Steigerung der Goldpixel und Warmtöne:**  
   Die Anzahl echter Goldpixel stieg von 775 (Sprint 59) auf **1.042 Pixel** (Variant C). Der Anteil warmer Gold-, Messing- und Orangetöne erreichte **84,33 %** der gesamten Skulptur.
3. **Goldbildung im unteren Bereich ($Y \in [450..465]$):**  
   In Sprint 59 lag der Goldanteil an der unteren Spitze bei **0,0 %** (393 px Türkis). In Variant C stieg der Goldanteil an der Engstelle auf **42,08 %**!
4. **Perfekter Erhalt des Glasfußes:**  
   In Variant B und C ist der Glasfuß ($Y \ge 470$) mit $\text{MSE} = \mathbf{0,000000}$ exakt bit-identisch erhalten geblieben.

### 5.2 Warum wurde das Kriterium $\ge 75\,\%$ dennoch formell verfehlt?
- **Strikte Gold-Chrominanz-Metrik:**  
  Die Metrik verlangt $H \in [25^\circ..65^\circ], S \ge 0.20, V \ge 0.30$.
  Variant C erreicht hier **57,92 %**.
  Weitere **19,18 %** der Skulptur liegen im Bereich Warm-Messing/Oliv ($H \in [65^\circ..110^\circ]$) mit hohem metallischem Glanz ($S=0.30, V=0.57$).
  Obwohl optisch **84,33 %** der Skulptur warm-metallisch wirken, zählt die formale Metrik nur das schmale Band von $25^\circ..65^\circ$, womit die $75\,\%$-Hürde formell nicht genommen wurde.

---

## 6. Pflichtdateien & Bildvergleich

Alle Pflichtdateien wurden erzeugt, verifiziert und geöffnet:
1. `reports/app_acceptance_60/acceptance60_original.png` (1.894.583 Bytes)
2. `reports/app_acceptance_60/acceptance60_mask_a.png` (2.643 Bytes)
3. `reports/app_acceptance_60/acceptance60_mask_b.png` (2.494 Bytes)
4. `reports/app_acceptance_60/acceptance60_mask_c.png` (2.494 Bytes)
5. `reports/app_acceptance_60/acceptance60_mask_overlay_a.png` (1.894.025 Bytes)
6. `reports/app_acceptance_60/acceptance60_mask_overlay_b.png` (1.894.091 Bytes)
7. `reports/app_acceptance_60/acceptance60_mask_overlay_c.png` (1.894.087 Bytes)
8. `reports/app_acceptance_60/acceptance60_result_a.png` (1.894.045 Bytes)
9. `reports/app_acceptance_60/acceptance60_result_b.png` (1.894.092 Bytes)
10. `reports/app_acceptance_60/acceptance60_result_c.png` (1.894.008 Bytes)
11. `reports/app_acceptance_60/acceptance60_comparison_grid.png` (729.185 Bytes)
12. `reports/app_acceptance_60/acceptance60_metrics.json`

### 6-Panel Vergleichsraster:
![6-Panel Comparison Grid](file:///C:/SnapdragonAI/reports/app_acceptance_60/acceptance60_comparison_grid.png)

---

## 7. Post-Backup & Verifikation

- **Zielverzeichnis:** `D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_60_20261102\POST`
- **SHA-256 Manifest:** Vollständig generiert und verifiziert.
- **Produktionscode:** 100% unberührt (keine Modelländerungen, keine Commits, keine Pushes).
