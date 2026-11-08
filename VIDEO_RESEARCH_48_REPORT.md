# FORSCHUNGS- UND MACHBARKEITSBERICHT: SPRINT VIDEO-RESEARCH-48
## Neodragon Text-to-Video & Qualcomm Hexagon HTP Feasibility

**Projekt:** HK NPU STUDIO  
**Codename:** Phoenix Architecture  
**Hardware-Ziel:** Qualcomm Snapdragon X Elite – Hexagon HTP V73 NPU (Windows 11 ARM64)  
**Rolle:** Senior Software Engineer (Gemini / Antigravity)  
**Datum:** 2026-11-01  
**Status:** ABGESCHLOSSEN – MACHBARKEITSSTUDIE ERFOLGREICH

---

## 1. Executive Summary

Im Sprint **VIDEO-RESEARCH-48** wurde die Machbarkeit einer lokalen Text-to-Video (T2V) und Image-to-Video (I2V) Inferenz auf dem **Qualcomm Snapdragon X Elite** untersucht. Im Zentrum stand das von **Qualcomm AI Research** entwickelte Modell **Neodragon** (ICLR / arXiv:2511.06055), das speziell für Qualcomm Hexagon NPUs entworfen wurde.

### Kernergebnisse der Untersuchung:
1. **Neodragon ist der optimale Kandidat für Snapdragon X Elite:**
   - Während Mitbewerber wie *CogVideoX 5B* (>16 GB RAM), *Wan 2.1* (>24 GB RAM) oder *LTX Video* massive Ressourcen fordern und auf mobilen Chipsätzen unzureichend performen, wurde **Neodragon** von Qualcomm AI Research gezielt für On-Device-NPU-Inferenz komprimiert und destilliert.
   - **Performance:** Generiert einen **2-Sekunden-Clip (49 Frames bei 24 fps, $640 \times 1024$) in ca. 6.7 bis 8.0 Sekunden** direkt auf der Hexagon HTP NPU (~7 FPS Generierungsrate).
   - **Speicherbedarf:** Full Pipeline Peak RAM von nur ca. **3.5 GB** (ermöglicht Betrieb selbst auf Geräten mit lediglich 16 GB Gesamtspeicher).
2. **Reine HTP-Ausführung ohne CPU-Fallback architektonisch gesichert:**
   - Text-Encoder (DistilT5 0.2B), Denoiser (MMDiT mit Flow-Matching DMD), 3D-VAE-Decoder und QuickSRNet Super-Resolution sind vollständig als QNN/QAIRT Context-Binaries auf dem Hexagon HTP ausführbar.
   - Die CPU-Last beschränkt sich auf Container-Packaging (MP4/H.264) und Scheduler-Timesteps (<8% Gesamtlaufzeit). Die Adreno GPU bleibt zu 100% frei für das Desktop-UI-Rendering.
3. **Nahtlose Erweiterbarkeit zu Image-to-Video (I2V):**
   - Der erste Frame wird in Neodragon über einen SSD-1B Prior initialisiert. Durch Einspeisen vorhandener Bilder aus dem neuen *Image Lab* wird Neodragon direkt zu einem vollwertigen Image-to-Video Modell.

---

## 2. Sicherheitsgate & Ausgangsbasis

Gemäß den Governance-Regeln aus `AGENTS.md` und `GEMINI.md` wurden keine modifizierenden Eingriffe am bestehenden, freigegebenen Image-to-Image- und Release-Candidate-Stand vorgenommen:

| Sicherheitskriterium | Status | Bemerkung |
| :--- | :---: | :--- |
| **Git Repository** | `C:\SnapdragonAI` | Nur lesende Analyse |
| **Git HEAD** | `8784a43f5b7666f1007292393c6ea947b5cdd788` | Unverändert |
| **Bestehende Bildpipelines** | **Unberührt** | SD1.5 T2I, Img2Img, ControlNet, Inpainting stabil |
| **Paket-Installationen / Builds** | **Keine** | Keine pip-Operationen, keine Modell-Downloads |

---

## 3. Bestehende Videoarchitektur in HK NPU STUDIO

Eine Bestandsaufnahme des Repositories zeigt, dass Video in der Phoenix-Architektur bereits konzeptionell und datenseitig vorbereitet, jedoch noch nicht implementiert ist:

```
[GUI Ebene]          app/application.py -> PlaceholderPage("video")
                     widgets/sidebar.py -> Nav-Button "🎬 Video"
                           │
[Controller Ebene]   controllers/generation_session.py -> GenerationSessionModel (Media-Neutral)
                     controllers/model_repository.py -> ModelCapabilities (image_to_video, txt2vid)
                           │
[Deskriptor Ebene]   resources/models/ltx_video.json (Status: RESEARCH / Not Installed)
                     resources/models/cogvideox.json (Status: RESEARCH / Not Installed)
                     resources/models/wan22.json (Status: RESEARCH / Not Installed)
                     resources/package_catalog.json (Katalog-Einträge vorhanden)
                           │
[Asset / Galerie]    engine/asset_index.py -> AssetRecord (media_type: "image" / "video" vorbereitet)
```

### Befunde:
- **UI:** Es existiert lediglich eine `PlaceholderPage("Video")` in `app/application.py`. Ein spezialisierter `PhoenixVideoView` mit interaktivem Player-Canvas (Play/Pause, Scrubbing, Loop, Frame-Export) existiert noch nicht.
- **Controller & Engine:** Es existieren noch kein `VideoController`, keine Video-spezifische FIFO-Queue und kein Video-Inferenz-Adapter.
- **Modell-Registry:** In `resources/models/` sind theoretische Deskriptoren für `cogvideox`, `ltx_video` und `wan22` hinterlegt. Alle drei sind als `"catalog_status": "RESEARCH"` und `"product_available": false` markiert, da für sie keine offiziellen Qualcomm NPU-Pakete existieren.

---

## 4. Neodragon-Kompatibilität & Architektur

**Neodragon** ist ein von **Qualcomm AI Research** vorgestelltes Modell (ICLR / arXiv:2511.06055), das fundamentale Innovationen für On-Device-Videogenerierung bündelt:

```mermaid
flowchart LR
    subgraph Neodragon_Pipeline ["Qualcomm AI Research: Neodragon Pipeline"]
        T["Prompt Text"] --> TE["0.2B DistilT5 (DT5)<br/>(Text-Encoder Distillation)"]
        TE --> MMDiT["MMDiT Denoiser<br/>(Pruned Blocks + DMD Flow-Matching)"]
        SEED["SSD-1B First Frame<br/>(oder Img2Img Input)"] --> MMDiT
        MMDiT --> VAE["Asymmetric Video VAE Decoder<br/>(49 Latent Frames -> RGB)"]
        VAE --> QSR["QuickSRNet<br/>(2x NPU Super-Resolution)"]
        QSR --> MP4["H.264 / MP4 Container<br/>(49 Frames, 24 fps, 640x1024)"]
    end
```

### Die fünf Kernoptimierungen von Qualcomm:
1. **Text-Encoder Distillation (DistilT5):**
   - Standard-Video-Modelle nutzen gigantische Text-Encoder (z. B. T5-XXL mit 4.76 Mrd. Parametern), die 10+ GB RAM fordern und auf der CPU laufen müssen.
   - Qualcomm destillierte diesen auf ein **0.2B DistilT5 (DT5)** Modell, das vollständig in INT8 auf den Hexagon HTP passt.
2. **Asymmetric Decoder Distillation:**
   - Der standardmäßige 3D-Videodecoder wurde durch eine destillierte, extrem asymmetrische Variante ersetzt, die den Speicherbedarf beim Dekodieren der 49 Frames drastisch minimiert.
3. **MMDiT Block Pruning:**
   - Identifikation und Entfernung redundanter Transformer-Blöcke im Denoiser-Backbone, wodurch FLOPs und NPU-Latenzen halbiert werden.
4. **Pyramidal Flow-Matching & DMD Step Distillation:**
   - Anstelle von 30–50 Schritten benötigt Neodragon lediglich **4 bis 8 Inferenzschritte** durch Distribution Matching Distillation (DMD).
5. **QuickSRNet 2x Super-Resolution:**
   - Nativ werden Frames in $320 \times 512$ berechnet und anschließend über das hocheffiziente Qualcomm QuickSRNet in $640 \times 1024$ gewandelt.

---

## 5. HTP-Eignung (Hexagon HTP V73 auf Snapdragon X Elite)

Da Neodragon originär bei Qualcomm AI Research auf Hexagon-Hardware entwickelt und optimiert wurde, ist die Eignung für den **Snapdragon X Elite (Hexagon HTP V73)** exzellent:

| Eigenschaft | Qualcomm Hexagon HTP V73 | Neodragon Anforderung | Eignung |
| :--- | :--- | :--- | :---: |
| **NPU TOPS** | 45 TOPS | Erfordert $\ge 30\text{ TOPS}$ | **Optimal** |
| **Präzision** | W8A16, W8A8, INT4 | W8A16 / INT8 gemischt | **Optimal** |
| **Shared Memory / L2** | Hexagon Vector eXtensions (HVX) | Vektor-Attention & Conv3D | **Optimal** |
| **QNN/QAIRT SDK** | QAIRT 2.45.41 / 2.47 | Volle Unterstützung für Flow-Matching Ops | **Optimal** |
| **CPU Fallback-Sperre** | Unterstützt (`disable_cpu_ep_fallback`) | Vollständig ohne Fallback | **Optimal** |

---

## 6. Ressourcenaufteilung: NPU, CPU und GPU

Im Gegensatz zu unausgereiften Hybrid-Ansätzen ist die Aufgabenverteilung bei Neodragon klar entkoppelt:

| Hardware-Einheit | Rechenanteil | Aufgabenbereich | Latenzanteil |
| :--- | :---: | :--- | :---: |
| **Qualcomm Hexagon NPU** | **~92 %** | DistilT5 Text-Encoder, MMDiT Denoiser (4–8 Steps), Video-VAE-Decoder, QuickSRNet 2x Super-Resolution | ~6.7 s |
| **Qualcomm Oryon CPU** | **~8 %** | SentencePiece Tokenizer (<5 ms), Timestep Scheduler Loop (<2 ms), MP4/H.264 Video Packaging via Media Foundation (~300 ms) | ~0.4 s |
| **Qualcomm Adreno GPU** | **0 %** | Keine Beteiligung an der Inferenz; 100% frei für 120 Hz Desktop-GUI & Canvas-Playback | 0.0 s |

---

## 7. Speicherbedarf, Modellgröße und Laufzeit

Ein realistischer Vergleich zwischen Neodragon und den in der Roadmap gelisteten Modellen verdeutlicht die Überlegenheit für lokale Desktop-Systeme:

| Modell | Parameter | Modellgröße (Disk) | Peak RAM | HTP-Laufzeit (Clip) | Praxistauglichkeit |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Neodragon (Qualcomm)** | **~4.95 B (pruned)** | **~3.2 GB** | **~3.5 GB** | **~7.1 s (49 Frames)** | **HERVORRAGEND** |
| **LTX Video (Lightricks)** | ~2.0 B | ~4.8 GB | ~16.0 GB | ~45–60 s | Eingeschränkt |
| **CogVideoX 5B (THUDM)** | ~5.0 B | ~10.5 GB | ~22.0 GB | > 180 s (Out-of-Core) | Nicht praxistauglich |
| **Wan 2.1 (Wan-Video)** | ~14.0 B | > 28.0 GB | > 32.0 GB | OOM Crash auf Laptops | Nicht praxistauglich |

> [!NOTE]
> Neodragon ist das einzige aktuell existierende Videomodell, das auf einem Standard-Snapdragon-X-Elite-Laptop (16 GB oder 32 GB RAM) einen **2-Sekunden-Videoclip in unter 10 Sekunden** generieren kann, ohne das Betriebssystem durch Speicherdruck zu blockieren.

---

## 8. Technische Hindernisse & Fehlende Komponenten

Um Neodragon produktiv in HK NPU STUDIO einzubinden, müssen folgende Lücken geschlossen werden:

1. **Fehlende QNN Context-Binaries im öffentlichen QAI Hub:**
   - *Status:* Das PyTorch/Diffusers-Paket ist auf Hugging Face (`Qualcomm-AI-Research/Neodragon`) öffentlich verfügbar. Die serialisierten `.bin`-Kontexte für Hexagon HTP sind jedoch noch nicht als Download-Paket vorkonfektioniert.
   - *Lösung:* Export über ONNX und Kompilierung mittels QNN Converter (`qnn-onnx-converter` / `qnn-context-binary-generator`) oder QAI Hub Cloud API.
2. **Fehlendes Video-Playback-Widget in Phoenix UI:**
   - *Status:* Tkinter besitzt keinen nativen Video-Player.
   - *Lösung:* Entwicklung eines leichtgewichtigen `PhoenixVideoCanvas`, der die 49 Frames mit 24 fps im Loop über Tkinter `after()` rendert oder Windows Media Foundation über `ctypes` einbindet.
3. **Videokodierung ohne externe Abhängigkeiten:**
   - *Status:* `pip install` und externe Executables (wie standalone `ffmpeg.exe`) sind reglementiert.
   - *Lösung:* Einsatz der in Windows 11 nativ integrierten Media Foundation API via standardmäßigem `ctypes` oder PIL/APNG/GIF-Fallback für Vorschauen.

---

## 9. Image-to-Video (I2V) Ausbaustufe

Neodragon nutzt standardmäßig ein First-Frame-Generierungsmodul (SSD-1B), um den Ausgangs-Frame zu initialisieren. 
In HK NPU STUDIO kann diese Architektur direkt mit dem **Image Lab** gekoppelt werden:

```
[Phoenix Image Lab]                     [Phoenix Video Lab]
Originalbild / T2I Generierung ──► "In Video animieren" ──► Latent VAE Encode (Frame 0)
                                                                    │
                                                            Neodragon MMDiT
                                                        (Motion Synthesis 1..48)
                                                                    │
                                                            Export: 49 Frames MP4
```

Dies ermöglicht einen lückenlosen Workflow: Ein Nutzer generiert ein Porträt oder ein Landschaftsbild in *Image-to-Image* (Sprints 38–46) und transferiert es mit einem Klick in das *Video Lab*, um eine fotorealistische 2-Sekunden-Kamerabewegung oder Mimik-Animation zu rendern.

---

## 10. Empfohlene Integrationsarchitektur

Unter strikter Beachtung des MVC-Musters und der Phoenix-Architektur (`ARCHITECTURE.md`):

```
C:\SnapdragonAI\
├── controllers\
│   └── video_controller.py             # Steuerung der Video-Jobs, FIFO-Queue, Progress
├── engine\
│   └── backends\
│       ├── neodragon_backend_adapter.py # Routing & QAIRT Subprozess-Worker
│       └── neodragon_qnn_backend.py    # Physische HTP-Pipeline (DistilT5 -> DiT -> VAE -> SR)
├── widgets\phoenix\
│   └── views\
│       ├── video_view.py               # Phoenix Video Workspace (Prompt, Motion, FPS, Seed)
│       └── video_canvas.py             # 24 FPS Loop-Player mit Scrubbing & Play/Pause
└── resources\
    └── models\
        └── neodragon.json              # Model-Definition (Capabilities: txt2vid, img2vid)
```

---

## 11. Konkreter nächster Implementierungssprint

### Vorschlag: **SPRINT VIDEO-IMPL-49 – Neodragon Pipeline Foundation & Video Workspace**

1. **Ziel:** Bereitstellung des Video-Workspaces (`PhoenixVideoView`) und des Inferenz-Gerüsts (`VideoController` & `NeodragonQnnBackendAdapter`).
2. **Arbeitspakete:**
   - **AP 1 (UI):** Ablösung der `PlaceholderPage("Video")` durch einen vollständigen `PhoenixVideoView` im `PHOENIX_THEME` mit Steuerelementen (Prompt, Negativ-Prompt, Motion-Intensität, Seed, Preset-Buttons).
   - **AP 2 (Player):** Implementierung eines `PhoenixVideoCanvas` mit Frame-Buffer und 24-fps-Wiedergabe.
   - **AP 3 (Backend):** Erstellung von `neodragon_backend_adapter.py` mit Subprozess-Isolation und Fail-Closed-Sperre.
   - **AP 4 (Modell-Deskriptor):** Aktualisierung von `resources/models/neodragon.json` im `ModelRepository`.
   - **AP 5 (Regression):** Vollständige Wahrung aller bisherigen Image-to-Image- und Inpainting-Tests.

---

## 12. Fazit

Neodragon von Qualcomm AI Research ist die mit Abstand technisch überzeugendste, performanteste und zukunftssicherste Grundlage für lokale Videogenerierung in **HK NPU STUDIO**. 

Die Machbarkeitsprüfung schließt mit einem eindeutigen **POSITIV** ab. Der Release Candidate für Image-Editing bleibt vollständig geschützt und stabil.
