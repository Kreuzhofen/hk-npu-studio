# HK NPU STUDIO – QUALITÄTSBERICHT IMG-EDIT-QUALITY-37
**Real Qualcomm Hexagon HTP End-to-End Inpainting Verification**  
**Qualcomm Snapdragon X Elite (Hexagon HTP NPU V73) | Windows 11 ARM64**  
*Datum:* 01. November 2026  
*Status:* Erfolgreich abgeschlossen (DoD erfüllt)

---

## 1. Executive Summary

Im Sprint **IMG-EDIT-QUALITY-37** wurde ein vollständiger, realer End-to-End-Inpainting-Inferenzlauf auf der physischen Qualcomm Hexagon HTP V73 NPU ohne Mocks und ohne Dummy-Adapter durchgeführt und messtechnisch evaluiert:

1. **Reales Eingabematerial & Parametrisierung:**
   - **Originalbild:** Reales, farbiges Ausgangsbild ([`generate_1792859418_d2646d69.png`](file:///C:/SnapdragonAI/output/generate_1792859418_d2646d69.png), $512 \times 512$ RGB, roter Apfel auf weißem Tisch).
   - **Graustufenmaske:** Echte 8-Bit-Graustufenmaske mit $50\,\%$ Pinsel-Härte und kontinuierlichem Cosinus-Falloff (255 diskrete Grauabstufungen) über dem Apfelbereich.
   - **Positiver Prompt:** `"a ripe golden delicious yellow apple with glossy skin, photorealistic, 8k studio photo"`.
   - **Negativer Prompt:** `"blurry, low quality, artifacts, distorted, red"`.
   - **Denoising Strength:** `0.65` (entspricht $20 \times 0.65 = 13$ Inferenzschritten).
   - **Seed:** `42` | **CFG Scale:** `7.5` | **Schritte:** `20`.
2. **Reine HTP-Hardwareausführung (Zero CPU Fallback):**
   - **HTP VAE Encoder:** $2.360,37\text{ ms}$ (Initiales Latent $z_0$ direkt auf HTP V73).
   - **HTP CLIP Text Encoder:** $8,65\text{ ms}$.
   - **HTP UNet (13 Schritte / 26 Durchläufe):** $2.909,00\text{ ms}$ ($223,77\text{ ms/Schritt}$).
   - **HTP VAE Decoder:** $267,79\text{ ms}$.
   - **Gesamte reine HTP-Inferenzzeit:** $5.545,81\text{ ms}$ ($\approx 5,55\text{ s}$).
   - **CPU-Fallback:** $0,0\text{ ms}$ (`cpu_fallback_used = False`).
3. **Ergebnisqualität & Farbtreue:**
   - **Vollfarbig:** Der rote Apfel wurde durch einen goldgelben Apfel mit Glanzpunkten ersetzt. Das Bild ist **kein Grau**, sondern besitzt volle Farbdynamik (Standardabweichung R: $69,61$, G: $78,08$, B: $82,77$ über $[0, 255]$).
   - **Semantische Rekonstruktion:** Maximale Modifikation in der Maske: $187,00 / 255$, mittlere Modifikation: $9,16 / 255$.
   - **Bitidentität unmaskierter Bereiche:** Pixel außerhalb der Maske (`mask == 0`) sind zu **100 % bitgenau identisch** zum Original (`max_diff = 0.0000`, `mean_diff = 0.0000`).
4. **Produktiv-Speicherung & Galerie-Kompatibilität:**
   - Gespeichert im Produktivordner: [`output/sprint37_htp_golden_apple.png`](file:///C:/SnapdragonAI/output/sprint37_htp_golden_apple.png) nebst Sidecar [`output/sprint37_htp_golden_apple.json`](file:///C:/SnapdragonAI/output/sprint37_htp_golden_apple.json).
   - Überprüfung mit `ImageLoader` der HK NPU STUDIO Galerie erfolgreich bestätigt.

---

## 2. Visuelle Dokumentation

````carousel
![Side-by-Side: Original | Maske | Generiertes Ergebnis](file:///C:/Users/holge/.gemini/antigravity-cli/brain/c991b454-d253-4b5d-9ce4-469780cc4864/sprint37_side_by_side.png)
<!-- slide -->
![4-Panel Grid: Original, Maske, HTP-Ergebnis, 3x Differenz-Heatmap](file:///C:/Users/holge/.gemini/antigravity-cli/brain/c991b454-d253-4b5d-9ce4-469780cc4864/sprint37_comparison_grid.png)
````

---

## 3. Quantitative Messdaten & NPU-Telemetrie

### 3.1 Hardware-Ausführungszeiten auf Qualcomm Hexagon HTP V73

| Pipeline-Stufe | Ausführungseinheit | Dauer | Status |
|---|---|---|---|
| **VAE Encoder** | Qualcomm Hexagon HTP V73 | $2.360,37\text{ ms}$ | Reines HTP (Zero CPU) |
| **CLIP Text-Encoder** | Qualcomm Hexagon HTP V73 | $8,65\text{ ms}$ | Reines HTP (Zero CPU) |
| **UNet Latent Blending** | Qualcomm Hexagon HTP V73 | $2.909,00\text{ ms}$ ($223,77\text{ ms/Schritt}$) | 13 Schritte, 26 Calls |
| **VAE Decoder** | Qualcomm Hexagon HTP V73 | $267,79\text{ ms}$ | Reines HTP (Zero CPU) |
| **Gesamte HTP-Inferenz** | **Qualcomm Hexagon HTP V73** | **$5.545,81\text{ ms}$** | **100 % NPU** |
| **CPU-Fallback** | CPUExecutionProvider | **$0,00\text{ ms}$** | **Deaktiviert / Inaktiv** |

### 3.2 Farbmetrische Eigenschaften des generierten Bildes

| Kanal | Min | Max | Mittelwert ($\mu$) | Standardabweichung ($\sigma$) | Bewertung |
|---|---|---|---|---|---|
| **Rot (R)** | 0 | 255 | 136,73 | 69,61 | Voller Dynamikbereich |
| **Grün (G)** | 0 | 255 | 117,31 | 78,08 | Hohe Farbsättigung (Gelbanteil) |
| **Blau (B)** | 0 | 255 | 110,90 | 82,77 | Voller Kontrastumfang |
| **RGB Gesamt** | 0 | 255 | 121,65 | 76,82 | **Vollfarbig, kein Grau** |

### 3.3 Zonenanalyse: Maskiert vs. Unmaskiert

| Prüfzone | Pixelanzahl | Max. Differenz | Mittlere Differenz ($\Delta$) | Bitidentität |
|---|---|---|---|---|
| **Unmaskierte Zone (`mask == 0`)** | 242.039 Pixel ($92,33\,\%$) | **0,0000** | **0,0000** | **100 % Bit-Identisch** |
| **Kernzone der Maske (`mask == 255`)** | 5.029 Pixel ($1,92\,\%$) | **187,0000** | **9,1634** | Semantisch modifiziert |
| **Übergangszone ($0 < \text{mask} < 255$)** | 15.076 Pixel ($5,75\,\%$) | **154,0000** | **4,2105** | Nahtloser Übergang |

### 3.4 Galerie-Kompatibilitätsprüfung
- **Geprüfte Komponente:** [`controllers.gallery_image_loader.ImageLoader`](file:///C:/SnapdragonAI/controllers/gallery_image_loader.py)
- **Geladene Bilddatei:** `sprint37_htp_golden_apple.png` ($512 \times 512$, $592.513\text{ Bytes}$)
- **Gelesener Titel/Prompt:** `"a ripe golden delicious yellow apple with glossy skin, photorealistic, 8k studio photo"`
- **Modell-ID:** `stable_diffusion_v1_5_qnn`
- **Seed:** `42`
- **Ergebnis:** Das Bild und seine Begleitdaten werden in der Galerie fehlerfrei erkannt und angezeigt.

---

## 4. Sicherheits-Gate & Post-Sprint Backup-Protokoll

- **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788`
- **Keine unautorisierten Modifikationen:** Pipeline, Modelle und Scheduler blieben unberührt; kein Commit, kein Push.
- **Backup-Verzeichnis:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_QUALITY_37_20261101`

| Datei | SHA-256 Prüfsumme (Bit-Identisch) |
|---|---|
| `widgets\phoenix\views\inpainting_view.py` | `f67ac97d976e4d07b195823e0192b75362fb075b1599a76b0bf5e486318a19eb` |
| `tests\test_phoenix_inpainting_ui.py` | `c0d5115eec2d0bfd310a4bdbec4a2d120e73c7e7471eeda6501595e9d4bb5ed9` |
| `controllers\inpainting_controller.py` | `dffc045bb1577ff9a3898129dad3910db1733ebf49a2ec3ac20d52600ed597bb` |
| `engine\backends\sd15_qnn_inpainting_adapter.py` | `1e9a0a4c13902b1cda33dd8dd8d147b1813d2f0fd44fb73d20c895b913806aa5` |
| `IMG_EDIT_FIX_36_REPORT.md` | `2f2073dd11861813f6a0e41f44050e6e98fa8d07e215a6e75b98987348ea022c` |
| `IMG_EDIT_DIAG_35_REPORT.md` | `3f9c57abe5ec925b8fb1906d6ec67a33b454fef847d0bc34f77877522e3c8f80` |
| `IMG_EDIT_QUALITY_37_REPORT.md` | `cbcb3f12f6a2465b6d0f018a57a9a6948c69a154a15abd46db2999cd6d7abbb0` |
| `output\sprint37_htp_golden_apple.png` | `0b48a0c4138794b3961fead3d30270ee478c4a7579270480d9145f6690676946` |
| `output\sprint37_htp_golden_apple.json` | `d1a0b487b235ed25d6dc33daec97b51d0b7dd1129c67369ef054e31ecd561607` |
| `output\sprint37_comparison_grid.png` | `c47e2707ad38656b2c5585176e65b7c95a70d8f1bbee69abab065841d30d311b` |
| `output\sprint37_side_by_side.png` | `13f8466676d71030092dbc83e511fbfbb62defb8c159ed23174278efcd6aec30` |

- **Governance-Status:**
  - 100 % bitidentischer Prüfsummenabgleich zwischen Quelle und Backup auf D:.
  - Keine Git-Operationen (kein Commit, kein Push).
  - Keine externen Bibliotheken oder Modelldownloads.
