# Future Roadmap – HK NPU STUDIO

Datum: 2026-07-07
Status: Offizielle Produkt-Roadmap (Vision 2.0)

---

## 1. Zielbild – Local AI Creative Suite

HK NPU STUDIO entwickelt sich weg von einer breitgefächerten Utility-Sammlung hin zu einer fokussierten, professionellen **lokalen AI Creative Suite** für Snapdragon-PCs. Die Suite konzentriert sich auf die vier Kernprozesse (C.O.R.E.):
* **CREATE:** Bild- und Video-Generierung direkt auf der lokalen Snapdragon HPU/NPU.
* **ORGANIZE:** Strukturierte Speicherung, Indizierung und Metadaten-Katalogisierung (Prompts, Seeds).
* **REVIEW:** Side-by-Side-Parametervergleiche und Qualitätsbeurteilung.
* **EVOLVE:** Automatisierung von Pipelines (z. B. Generate → Upscale) und intelligentes Modell-Management.

Klassische Bildbearbeitungsfunktionen (Filter, Pinsel, manuelle Farbkorrekturen) sind explizit **out of scope**.

---

## 2. Roadmap Version 2.0: Phoenix Foundation (Abgeschlossen/Laufend)

Der Fokus liegt auf der Etablierung des Software-Fundaments und der MVC-Architektur.

### Ziele:
* **UI & Navigation:** Neue Phoenix-GUI als Standard-Oberfläche. Erste Version des **AI Generate** (Prompt) Workspaces steht.
* **MVC-Entkopplung:** Einführung von `GenerationSessionModel`, `GenerationQueue` und `GenerationController` zur Kapselung des Pipeline-Zustands von der GUI.
* **Backend Abstraktion:** Schnittstellen-Definition (`BackendAdapter` / `BackendManager`) zur Entkopplung der Inferenz. Stubs für CPU, QNN, ONNX und Remote sind angelegt.
* **Namens-Alignment (Langfristige Zielbezeichnungen in der UI):**
  * **Gallery** → **AI Asset Library** (langfristige Zielbezeichnung)
  * **Compare Workspace** → **Review Workspace** (langfristige Zielbezeichnung)
  * **Image Workspace** → **Asset Inspector** (langfristige Zielbezeichnung)

---

## 3. Roadmap Version 3.0: AI Platform Integration (Mittelfristig)

Der Übergang von Stubs zu echter lokaler Ausführung und ersten Backend-Integrationen.

### Ziele:
* **Modell-Manager:** Einführung einer zentralen Modell-Registry zur Verwaltung lokaler Gewichtsdateien und Quantisierungsprofile (INT4/INT8).
* **QNN Backend:** Echte NPU-Inferenz über das Qualcomm QNN SDK für ein erstes Bildgenerierungsmodell (z. B. Stable Diffusion 1.5).
* **ONNX Runtime Backend:** Lokale Fallback-Ausführung via ONNX (CPU & DirectML/GPU-Beschleunigung).
* **AI Asset Library (ehemals Gallery):** Indizierung generierter Assets, Speicherung von Prompts und Seeds direkt in einer lokalen SQLite-Metadatendatenbank.
* **Review Workspace (ehemals Compare):** Vollständig synchronisierter Bildvergleich mit Metadaten-Overlay.

---

## 4. Roadmap Version 4.0: Professional AI Creative Suite (Langfristig)

Erweiterung um modernste Modelle, Multimodalität und flexible Pipelines.

### Ziele:
* **State-of-the-Art Modelle:** native Unterstützung von **FLUX.1**, **SDXL**, **Stable Diffusion 3** und Videomodellen (**Wan2.1**, **CogVideo**, **LTX Video**).
* **Asset Inspector (ehemals Image Workspace):** Einzellansicht mit detaillierter Extraktion historischer Parameter (z. B. "Diesen Prompt für neuen Job wiederverwenden").
* **Workflow Automation:** Verkettung von Generierungs- und Postprocessing-Modulen (z. B. Text-zu-Bild → RealESRGAN NPU Upscaler).
* **Plugin Ecosystem:** Möglichkeit für Entwickler, eigene Pipeline-Module oder benutzerdefinierte Backends einzuklinken.

---

## 5. Domain-Roadmap

| Säule (C.O.R.E.) | Phase II (V2) | Phase III (V3) | Phase IV (V4) |
|---|---|---|---|
| **CREATE** (AI Generate) | Prompt Workspace Foundation & Parameter UI | Erste NPU-Generierung (SD 1.5) | FLUX / SDXL / SD3 & Videogenerierung (Wan) |
| **ORGANIZE** (Asset Library) | Gallery Workspace mit Async-Thumbnails | SQLite-Metadatenbank, Tagging & Prompt-Suche | Asset Inspector zur prompt-basierten Re-Generierung |
| **REVIEW** (Review Workspace) | Zoom- & Pan-Vergleichsrahmen | Synchronisierter Vergleich & Metadaten-Delta | Side-by-Side-Vergleich von Videosequenzen |
| **EVOLVE** (AI Workflows) | Backend-Adapter & Queue Stubs | Model Manager & automatische Backend-Erkennung | Workflow-Graph-Automation & Plugin-Marketplace |
