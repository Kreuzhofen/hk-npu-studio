# SPRINT APP-ACCEPTANCE-48 REPORT
**HK NPU STUDIO – First Real Image Generation (Acceptance Run)**

---

## 1. Executive Summary

| Parameter | Spezifikation / Messung |
|---|---|
| **Sprint-ID** | `SPRINT APP-ACCEPTANCE-48` |
| **System** | Windows 11 ARM64 (Build 26100) |
| **Hardware** | Qualcomm Snapdragon X Elite – Hexagon HTP V73 NPU |
| **Inference Backend** | `QNNExecutionProvider` (Qualcomm QNN SDK) |
| **CPU Fallback** | **0.00 ms** (100% hardware-bound auf Hexagon HTP) |
| **Test 1: Text-to-Image** | SD 1.5 QNN HTP (512×512, Seed 4801, 15 Steps) – **20.03 s** |
| **Test 2: Image-to-Image** | Latent Anchor Modus B (Fidelity 0.65, Denoise 0.45, Seed 4802) – **20.91 s** |
| **GUI-Integration** | Vollständig verifiziert in `SnapdragonAIStudioV2` (`gui_v2.py`) |
| **Status** | **ERFOLGREICH ABGENOMMEN (PASS)** |

---

## 2. Sicherheits-Gate & Pre-Backup

Gemäß den Governance-Regeln aus `AGENTS.md` und `GEMINI.md`:
1. **Git Status & HEAD:**
   - Commit HEAD: `8784a43f5b7666f1007292393c6ea947b5cdd788` (unverändert).
   - Sauberes Arbeitsverzeichnis ohne unautorisierte Modifikationen.
2. **Speicherprüfung:**
   - Laufwerk `D:` verfügbar mit **42.72 GB** freiem Speicherplatz.
3. **Pre-Backup:**
   - Erstellt unter: `D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_48_20261101\PRE`
   - Manifest: `PRE_BACKUP_SHA256_MANIFEST.json`
   - Verifikation: **37/37 Dateien** bit-genau (100% SHA-256 Übereinstimmung).

---

## 3. Anwendungsstart & Model Manager

Der offizielle Einstiegspunkt der Desktop-Anwendung wurde über `start_gui.bat` und `gui_v2.py` ermittelt:
- **Klasse:** `SnapdragonAIStudioV2` (Tkinter GUI mit Phoenix UI Workspace Framework)
- **Startup:** Sauber ohne Fehlermeldungen oder Ausnahmen initialisiert.
- **Model Discovery:**
  - `controlnet_canny_qnn` (Qualcomm Hexagon HTP V73)
  - `stable_diffusion_v1_5_qnn` (Qualcomm Hexagon HTP V73) – *Aktiv für Sprint 48*
  - `stable_diffusion_v2_1_qnn` (Qualcomm Hexagon HTP V73)
  - `stable_diffusion_v3_5_qai` (Qualcomm QAI AppBuilder HTP)

---

## 4. Test 1: Text-to-Image (Erste reale Bildschöpfung)

### Testspezifikation
- **Workspace:** Phoenix Prompt View (`PhoenixPromptView`)
- **Modell:** `stable_diffusion_v1_5_qnn` (Qualcomm Stable Diffusion 1.5 auf Hexagon HTP V73)
- **Prompt:** `"A photorealistic red apple on a wooden table, soft natural window light, detailed skin texture, professional product photography, realistic shadows, high detail."`
- **Negative Prompt:** `"blurry, distorted, low quality, artifacts"`
- **Auflösung:** `512 × 512`
- **Seed:** `4801`
- **Steps:** `15`
- **CFG Scale:** `7.5`
- **Sampler / Scheduler:** `Euler`

### Messergebnisse & Verifikation
- **Dateiname:** `generate_1793563666_b60aa240.png`
- **Artefakt:** `reports/sprint48_results/acceptance48_text_to_image.png`
- **Dateigröße:** 440.325 Bytes
- **Gesamtlaufzeit:** **20.03 s** (Inferenz: 20.027,95 ms)
- **CPU Fallback:** **0.00 ms** (100% HTP V73)
- **JSON-Sidecar:** `reports/sprint48_results/acceptance48_text_to_image.json` vorhanden mit vollständigen Metadaten.
- **GUI-Vorschau:** Sofort in der Benutzeroberfläche gerendert und angezeigt.
- **GUI-Screenshot:** `reports/sprint48_results/acceptance48_gui_t2i.png`

---

## 5. Test 2: Image-to-Image (Latent Anchor Transformation)

### Testspezifikation
- **Workspace:** Phoenix Image Lab / Image-to-Image (`PhoenixImageToImageView`)
- **Eingangsbild:** Das in Test 1 generierte rote Apfelbild (`acceptance48_text_to_image.png`)
- **Prompt:** `"Transform the red apple into a golden yellow apple, preserve its shape and natural lighting."`
- **Negative Prompt:** `"blurry, distorted, low quality, artifacts"`
- **Referenzmodus:** **Modus B – Decaying Latent Anchor**
- **Referenzstärke (Fidelity):** `0.65`
- **Denoising Strength:** `0.45` (*Preset: Moderat*)
- **Seed:** `4802`
- **Steps:** `15` (entspricht 7 effektiven Denoising-Schritten auf NPU)

### Messergebnisse & Verifikation
- **Dateiname:** `img2img_4802_1793563678.png`
- **Artefakt:** `reports/sprint48_results/acceptance48_image_to_image.png`
- **Dateigröße:** 431.059 Bytes
- **Gesamtlaufzeit:** **20.91 s** (Inferenz: 20.913,43 ms)
- **CPU Fallback:** **0.00 ms** (100% HTP V73)
- **JSON-Sidecar:** `reports/sprint48_results/acceptance48_image_to_image.json` vorhanden (`reference_control.mode: "latent_anchor"`, `fidelity: 0.65`, `denoising_strength: 0.45`).
- **GUI-Vorschau:** Sofort im Bildvergleichs-Canvas angezeigt.
- **GUI-Screenshot:** `reports/sprint48_results/acceptance48_gui_i2i.png`

---

## 6. Gegenüberstellung & Bildschöpfungs-Qualität

Die direkte Gegenüberstellung beweist die strukturelle Integrität des Apfels bei gleichzeitiger farblicher und materialbezogener Wandlung in Goldgelb:

- **Vergleichscollage:** `reports/sprint48_results/acceptance48_comparison_grid.png`

### Qualitätsbewertung
1. **Silhouette & Proportionen:** Die charakteristische Kontur, der Stielansatz und die Position auf dem Holztisch bleiben exakt erhalten.
2. **Beleuchtung & Reflexionen:** Das weiche natürliche Fensterlicht und der realistische Kontaktschatten stimmen überein.
3. **Farbwandlung:** Saubere, artefaktfreie Transformation des tiefroten Apfels in eine leuchtend goldgelbe Schale mit feinen Texturen.
4. **Keine Verzerrungen:** Keine Verformung des Motivs oder Fragmentierung des Hintergrunds.

---

## 7. Laufzeit- und Ressourcenprotokoll

Vollständiges Protokoll aus `reports/sprint48_results/sprint48_htp_runtime_protocol.json`:

```json
{
  "sprint": "SPRINT APP-ACCEPTANCE-48",
  "date": "2026-11-01",
  "platform": "Windows 11 ARM64",
  "hardware": "Qualcomm Snapdragon X Elite (Hexagon HTP V73 NPU)",
  "backend": "QNNExecutionProvider",
  "cpu_fallback_ms": 0.0,
  "stages": {
    "startup": {
      "status": "PASS",
      "window_title": "HK NPU STUDIO",
      "available_models": [
        "controlnet_canny_qnn",
        "stable_diffusion_v1_5_qnn",
        "stable_diffusion_v2_1_qnn",
        "stable_diffusion_v3_5_qai"
      ]
    },
    "text_to_image": {
      "status": "PASS",
      "output_image": "generate_1793563666_b60aa240.png",
      "file_size_bytes": 440325,
      "image_resolution": [512, 512],
      "wall_time_s": 20.03,
      "inference_ms": 20027.95,
      "cpu_fallback_ms": 0.0,
      "seed": 4801,
      "steps": 15,
      "cfg": 7.5,
      "prompt": "A photorealistic red apple on a wooden table, soft natural window light, detailed skin texture, professional product photography, realistic shadows, high detail.",
      "sidecar_present": true
    },
    "image_to_image": {
      "status": "PASS",
      "output_image": "img2img_4802_1793563678.png",
      "file_size_bytes": 431059,
      "image_resolution": [512, 512],
      "wall_time_s": 20.91,
      "inference_ms": 20913.43,
      "cpu_fallback_ms": 0.0,
      "seed": 4802,
      "steps": 15,
      "cfg": 7.5,
      "denoising_strength": 0.45,
      "reference_mode": "latent_anchor",
      "reference_fidelity": 0.65,
      "prompt": "Transform the red apple into a golden yellow apple, preserve its shape and natural lighting.",
      "sidecar_present": true
    }
  }
}
```

---

## 8. Definition of Done (DoD) Verifikation

- [x] Anwendung startet direkt über offiziellen Eintrittspfad (`start_gui.bat` / `gui_v2.py`) fehlerfrei.
- [x] SD 1.5 QNN HTP ist betriebsbereit und voll funktionsfähig.
- [x] Test 1 (Text-to-Image) generiert ein echtes PNG mit rotem Apfel auf NPU.
- [x] Test 2 (Image-to-Image) transformiert den Apfel in Goldgelb unter Beibehaltung der Konturen und Beleuchtung.
- [x] 0.00 ms CPU-Fallback (100% Qualcomm Hexagon HTP).
- [x] JSON-Sidecars vorhanden und vollständig dokumentiert.
- [x] UI-Screenshots der tatsächlichen Desktop-Applikation dokumentiert.
- [x] Dark/Light Theme-Parität intakt.
- [x] Kein Git-Commit oder Git-Push ohne PO-Freigabe ausgeführt.
- [x] Post-Backup mit SHA-256 Verifikation angelegt.

**Ergebnis:** SPRINT APP-ACCEPTANCE-48 ist zu 100% abgeschlossen und erfolgreich abgenommen.
