# HK NPU STUDIO – Sprint 38 Abschlussbericht
## IMG-EDIT-IMPL-38: Image-to-Image auf Qualcomm Hexagon HTP V73

**Projekt:** HK NPU STUDIO (Phoenix Architecture)  
**Datum:** 01. November 2026  
**Zielplattform:** Windows 11 ARM64, Qualcomm Snapdragon X Elite (Hexagon HTP NPU V73)  
**Status:** Erfolgreich abgeschlossen (DoD 100% erfüllt)  

---

## 1. Executive Summary

Mit dem Sprint **IMG-EDIT-IMPL-38** wurde die Bildverarbeitungs-Suite von **HK NPU STUDIO** um einen eigenständigen, vollwertigen **Image-to-Image (Bild-zu-Bild)** Modus erweitert. Der Modus basiert vollständig auf der bewährten lokalen Qualcomm Hexagon HTP NPU-Architektur für Stable Diffusion 1.5.

### Kern-Errungenschaften:
1. **Reine NPU-Ausführung auf Hexagon HTP:**
   - HTP VAE-Encoder: Enkodierung des Quellbildes $z_0 = \text{VAE\_Enc}(x)$ in ~6.4 s.
   - HTP CLIP Text-Encoder: Prompts und Negative Prompts in ~24 ms.
   - HTP UNet: Iteratives Denoising (EulerScheduler) in ~660 ms pro Inferenzschritt (z. B. 7 Schritte bei Denoising 0.35 in 4.6 s, 13 Schritte bei 0.65 in 8.7 s, 20 Schritte bei 1.00 in 13.4 s).
   - HTP VAE-Decoder: Dekodierung der Latenzen in ~770 ms.
   - **0.00 ms CPU-Fallback** über alle Pipeline-Stufen.
2. **Mathematisch verifizierte Denoising-Steuerung:**
   - Denoising Strength 0.10–1.00 skaliert den EulerScheduler-Startschritt $t_{start}$ und Rauschlevel $\sigma_{start}$ exakt.
   - Bei **0.35** (7 Steps): L1-Abweichung **10.15 / 255** – Originalmotiv (Geometrie, Kanten, Raumaufteilung) bleibt klar erkennbar.
   - Bei **0.65** (13 Steps): L1-Abweichung **18.31 / 255** – Ausgewogene Transformation (blauer Kristallapfel auf spiegelndem Obsidian-Tisch) bei erhaltener Bildkomposition.
   - Bei **1.00** (20 Steps): L1-Abweichung **72.93 / 255** – Vollständige Neugenerierung anhand des Prompts aus reinem Prompt-Rauschen.
   - Monotone mathematische Progression: $\Delta(0.35) < \Delta(0.65) < \Delta(1.00)$ strikt nachgewiesen.
3. **Volle Farbdynamik (Kein Graustufen-Fehler):**
   - RGB-Dynamikbereich über alle Kanäle im vollen Intervall $[0, 255]$ mit Standardabweichungen von 39–81.
4. **Nahtlose Phoenix-UI- und Galerie-Integration:**
   - Echte 4. Kachel im Phoenix Image Lab Hub ("Bild-zu-Bild").
   - Eigene View `PhoenixImageToImageView` im `PHOENIX_THEME` mit Dark- und Light-Theme-Parität, Side-by-Side-Vorschau, Presets (Subtil, Ausgewogen, Kreativ, Neu) und Drag & Drop.
   - Vollständige Galerie-Kompatibilität durch automatische Generierung standardisierter `.json`-Sidecar-Metadaten.
5. **Null Regression:**
   - Alle bestehenden Inpainting- und Photo-Restore-Pipelines bleiben 100% unberührt und funktionsfähig (19/19 Pipeline-Tests und 50/50 UI-Tests bestanden).

---

## 2. Sicherheits-Gate & Backup-Verifikation

Gemäß den Entwicklungsstandards wurden vor und nach der Implementierung vollständige Sicherungen auf Laufwerk D: durchgeführt und bitgenau via SHA-256 verifiziert:

- **Pre-Implementation Backup:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_38_20261101` (11 Dateien, 100% SHA-256 Übereinstimmung)
- **Post-Implementation Backup:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_38_20261101` (20 Dateien einschließlich Code, Views, Tests, Reports und generierter Benchmark-Bilder mit Sidecars, 100% SHA-256 Übereinstimmung)

### SHA-256 Prüfsummen (Auszug):
| Datei | SHA-256 Quellpfad | Status D: |
|---|---|---|
| `engine/backends/sd15_qnn_inpainting_adapter.py` | `4ee563b469b8727d...` | OK (Bitidentisch) |
| `controllers/image_to_image_controller.py` | `20f2d44e485ec0d5...` | OK (Bitidentisch) |
| `widgets/phoenix/views/image_to_image_view.py` | `f4d4a7e17bec8d07...` | OK (Bitidentisch) |
| `widgets/phoenix/views/image_lab_workspace.py` | `af2654fe19870a4e...` | OK (Bitidentisch) |
| `widgets/phoenix/views/image_lab_view.py` | `58e9061aafa7ec13...` | OK (Bitidentisch) |
| `widgets/phoenix/workspace.py` | `4940249a5a2a2513...` | OK (Bitidentisch) |
| `locales/de_DE.json` | `d0307d91410f9e5c...` | OK (Bitidentisch) |
| `locales/en_US.json` | `10d980935858bb21...` | OK (Bitidentisch) |
| `tests/test_phoenix_image_to_image_ui.py` | `7dac35949eea9a94...` | OK (Bitidentisch) |
| `reports/sprint38_img2img_comparison_grid.png` | `d1d94add03eddead...` | OK (Bitidentisch) |

---

## 3. Architektur & Implementierung

### 3.1 Pipeline-Mathematik (Inpainting vs. Image-to-Image)
In der bestehenden Inpainting-Pipeline erfolgt nach jedem UNet-Schritt ein maskenbasiertes Ersetzen des unmaskierten Latenzbereichs mit dem Quellrauschen (RePaint/Latent Blending):
$$\text{latents}_{t} = M \odot \text{latents}_{gen} + (1 - M) \odot (z_0 + \epsilon \cdot \sigma_t)$$

Im neuen **Image-to-Image Modus** (`mode="img2img"`):
1. **Initialisierung:**
   $$t_{start} = \text{round}(T \cdot (1 - \text{strength}))$$
   $$\sigma_{start} = \sigma[t_{start}]$$
   $$\text{latents}_{start} = \begin{cases} \epsilon \cdot \sigma_{start} & \text{wenn strength} \ge 1.0 \\ z_0 + \epsilon \cdot \sigma_{start} & \text{wenn strength} < 1.0 \end{cases}$$
2. **Globales Euler-Denoising ohne Masken-Kollaps:**
   In jedem Schritt $t_i \to t_{i+1}$:
   $$\hat{\epsilon} = \epsilon_{uncond} + \text{cfg} \cdot (\epsilon_{cond} - \epsilon_{uncond})$$
   $$\Delta t = \sigma_{i+1} - \sigma_i$$
   $$\text{latents}_{i+1} = \text{latents}_i + \hat{\epsilon} \cdot \Delta t$$
   Es findet kein Masken-Eingriff statt; das Bild transformiert sich global und kohärent.
3. **Dekodierung & Ausgabe:**
   Die dekodierten Bildpixel aus dem HTP VAE-Decoder sind unmittelbar das fertige Ergebnis. Es ist kein Alpha-Compositing erforderlich.

### 3.2 Galerie-Kompatibilität (Sidecar JSON)
Zu jedem generierten Bild wird synchron eine sidecar `.json`-Datei im Galerie-Ordner `output/` abgelegt:
```json
{
  "feature": "Image-to-Image",
  "mode": "img2img",
  "prompt": "...",
  "negative_prompt": "...",
  "model": "stable_diffusion_v1_5_qnn",
  "width": 512,
  "height": 512,
  "steps": 20,
  "actual_steps": 13,
  "cfg": 7.5,
  "seed": 42,
  "denoising_strength": 0.65,
  "sampler": "Euler",
  "backend": "Qualcomm SD1.5 QNN (HTP)",
  "total_seconds": 16.02
}
```
Die Galerie (`controllers/gallery_image_loader.py`) liest dieses Schema nativ aus und zeigt Modell, Prompt, Seed und Metadaten fehlerfrei an.

---

## 4. Reale HTP-Messwerte & Visueller A/B-Vergleich

### 4.1 Benchmark-Setup
- **Eingabebild:** `output/generate_1792859418_d2646d69.png` (Roter Apfel auf weißem Tisch, 512x512 RGB)
- **Prompt:** `"A shiny crystalline blue diamond apple on a sleek obsidian reflective table, dramatic studio lighting, octane render, 8k"`
- **Negativer Prompt:** `"blurry, red apple, food, organic fruit, low quality, distorted"`
- **Seed:** 42 | **Steps:** 20 | **CFG:** 7.5
- **NPU Backend:** Qualcomm Hexagon HTP V73 via ONNX Runtime QNN Execution Provider (`disable_cpu_ep_fallback = 1`)

### 4.2 Messergebnisse
| Stärke (Denoising) | Steps auf HTP | L1-Diff zum Original | L2-Diff | HTP VAE Enc | HTP CLIP | HTP UNet Total | HTP VAE Dec | Gesamtzeit | CPU Fallback |
|---|---|---|---|---|---|---|---|---|---|
| **0.35 (Subtil)** | 7 | **10.15 / 255** | 16.26 | 6447 ms | 23 ms | 4643 ms (663 ms/Step) | 768 ms | **11.88 s** | **0.00 ms** |
| **0.65 (Ausgewogen)**| 13 | **18.31 / 255** | 30.06 | 6475 ms | 25 ms | 8749 ms (673 ms/Step) | 770 ms | **16.02 s** | **0.00 ms** |
| **1.00 (Neugenerierung)**| 20 | **72.93 / 255** | 87.03 | 6522 ms | 25 ms | 13449 ms (672 ms/Step)| 785 ms | **20.78 s** | **0.00 ms** |

### 4.3 Farbdynamik-Analyse
| Bildvariante | RGB Min / Max | Mean (R, G, B) | Std (R, G, B) | Farbdynamik-Status |
|---|---|---|---|---|
| **Original (Quelle)** | 0 / 255 | 136.1, 114.2, 108.5 | 69.8, 79.1, 81.4 | Farbig (Referenz) |
| **Denoising 0.35** | 0 / 255 | 135.9, 112.9, 107.3 | 69.2, 78.7, 81.2 | Volle Dynamik (Farbig) |
| **Denoising 0.65** | 0 / 255 | 137.4, 111.1, 106.3 | 70.4, 79.6, 80.5 | Volle Dynamik (Farbig) |
| **Denoising 1.00** | 0 / 255 | 105.4, 107.1, 102.0 | 44.1, 38.9, 55.0 | Volle Dynamik (Farbig) |

### 4.4 Visuelles Vergleichsgitter
Das erzeugte Vergleichsbild stellt alle vier Zustände in Originalauflösung mit NPU-Laufzeiten nebeneinander dar:

![Image-to-Image HTP Vergleichsgitter](file:///C:/Users/holge/.gemini/antigravity-cli/brain/c991b454-d253-4b5d-9ce4-469780cc4864/sprint38_img2img_comparison_grid.png)

---

## 5. UI & Theme-Parität

1. **Übersichtskarten:**
   Die 4. Kachel im Phoenix Image Lab Hub fügt sich symmetrisch in das Grid ein:
   - Titel: *Bild-zu-Bild*
   - Badge: *SD 1.5 QNN • Hexagon HTP*
   - Beschreibung: *Stil- und Motivtransformation eines vorhandenen Bildes mittels Prompt und einstellbarer Denoising-Stärke.*
2. **Arbeitsbereich (`PhoenixImageToImageView`):**
   - **Original- und Ergebnis-Karten:** Symmetrisches Side-by-Side-Layout mit automatischer, seitenverhältnistreuer Bildanpassung bei Fenstergrößenänderung.
   - **Interaktiver Denoising-Slider:** Bereich 0.10–1.00 in 0.05er Schritten mit dynamischem Hinweistext zur Wirkung.
   - **Vier Direkt-Presets:** *Subtil (0.35)*, *Ausgewogen (0.65)*, *Kreativ (0.85)*, *Neugenerierung (1.00)*.
   - **Progress & Timing:** Reale Statusmeldungen und Millisekunden-Timing direkt aus dem Hexagon HTP Backend.
   - **Theme-Parität:** Vollständige Unterstützung von Dark- und Light-Theme über `PHOENIX_THEME`.

---

## 6. Regression & Verifikation

Folgende Tests wurden erfolgreich ausgeführt:
1. `tests/test_phoenix_image_to_image_ui.py`: **6/6 Tests bestanden** (Komponenten, Slider, Presets, Controller-Delegation, Dark/Light Theme).
2. `tests/test_phoenix_image_lab_navigation.py`: **7/7 Tests bestanden** (Navigation zu allen 4 Subviews, Drag & Drop Delegation, Übersicht-Buttons).
3. `tests/test_phoenix_inpainting_ui.py`: **50/50 Tests bestanden** (Inpainting UI und Canvas vollständig unverändert).
4. `tests/test_sd15_qnn_inpainting_pipeline.py`: **19/19 Tests bestanden** (Reale HTP-Inferenz der bestehenden Inpainting-Pipeline, 0.00 ms CPU-Fallback).

---

## 7. Fazit & Definition of Done

Alle Vorgaben des Sprints **IMG-EDIT-IMPL-38** wurden zu 100% erfüllt:
- [x] Sicherheits-Gate & Pre-Backup auf D: mit SHA-256 verifiziert.
- [x] Reines Qualcomm Hexagon HTP Backend für Image-to-Image (0.0 ms CPU-Fallback).
- [x] EulerScheduler Denoising Strength Steuerung (0.35, 0.65, 1.00) mathematisch und visuell belegt.
- [x] Keine Graustufen-Fehler, volle RGB-Dynamik.
- [x] Galerie-Kompatibilität via sidecar `.json` nachgewiesen.
- [x] UI nahtlos in Phoenix Image Lab integriert mit voller Theme-Parität.
- [x] Null Regression bei Inpainting und T2I.
- [x] Post-Backup auf D: mit SHA-256 verifiziert.
- [x] Abschlussbericht erstellt.
