# Produkt-Roadmap – HK NPU STUDIO

Diese Roadmap dokumentiert die offiziell beschlossenen Meilensteine und Entwicklungsphasen für HK NPU STUDIO. Es werden keine hypothetischen Funktionen hinzugefügt.

---

## 1. Abgeschlossene & Laufende Meilensteine

### Meilenstein v1.1 – Identity (Abgeschlossen)
* Etablierung der Corporate Identity (CI) und Branding-Assets.
* Integration des Splashscreens und des "About"-Fensters zur Lizenz- und Entwickleranzeige.
* Bereitstellung der [version.py](file:///C:/SnapdragonAI/version.py) zur zentralen Versionssteuerung.

### Meilenstein v1.2 – AI Library (Abgeschlossen)
* Implementierung von dynamischen Modellkarten (Model Cards) und Plugin-Karten.
* Anzeige von Hardware-Kompatibilitätsindikatoren zur NPU-Eignung von Modellen.
* Einführung von visuellen Statusindikatoren für geladene und aktive Plugins.

### Meilenstein v1.3 – Dashboard (Abgeschlossen)
* Erstellung des Haupt-Dashboards mit Schnellzugriffen (Quick Actions) auf Inferenz-Workflows.
* Darstellung des Hardware-Status (Betriebssystem, ARM64-Erkennung, QNN-Treiberpräsenz, RAM).
* Integration der Anzeige kürzlich bearbeiteter Projekte und verarbeiteter Bilder.

### Meilenstein v1.5 – Generation (Abgeschlossen)
* Integration von externen Backend-Schnittstellen (Stable Diffusion WebUI, InvokeAI, ComfyUI).
* Erstellung einer Modellerauswahl für Inferenz-Läufe.
* Speicherung des lokalen Prompt-Verlaufs (Prompt History).

---

## 2. Zukünftige Entwicklungsphasen

### Meilenstein v2.0 – Phoenix Foundation (Aktuelle Phase)
Fokus liegt auf dem Software-Fundament und der Entkopplung der Inferenz-Pipeline.
* **AI Generate (Prompt) Workspace:** Erstversion des Prompt- und Parameter-Panels.
* **Pipeline-Kapselung:** Steuerung über `GenerationSessionModel`, `GenerationQueue` und `GenerationController` zur vollständigen MVC-Entkopplung.
* **Inferenz-Adapter:** Abstrakte Schnittstelle `BackendAdapter` und `BackendManager` mit Stubs für CPU, QNN, ONNX und Remote APIs.
* **Namens-Alignment (Langfristige UI-Zielbezeichnungen):**
  * **Gallery** → **AI Asset Library**
  * **Compare Workspace** → **Review Workspace**
  * **Image Workspace** → **Asset Inspector**
* **Branding & Quality:** Dark/Light-Theming über den `ThemeManager` und Neutralisierung veralteter Modellschnittstellen.

### Meilenstein v3.0 – AI Platform Integration (Geplant)
Fokus liegt auf der Anbindung echter lokaler Modelle und Metadaten-Katalogisierung.
* **Model Manager:** Lokale Modell-Registry für Gewichte und Quantisierungsprofile (INT4/INT8).
* **QNN Backend:** NPU-Generierung über das Qualcomm QNN SDK (z. B. Stable Diffusion 1.5).
* **ONNX Runtime Backend:** Lokaler Fallback via ONNX (CPU und DirectML/GPU).
* **AI Asset Library:** SQLite-Metadatenbank zur persistenten Indizierung generierter Assets, Suchfunktion und Prompt-Tagging.
* **Review Workspace:** Synchronisierter Zoom- und Pan-Vergleich von Generierungsläufen.

### Meilenstein v4.0 – Professional AI Creative Suite (Geplant)
Fokus liegt auf fortgeschrittenen Modellen, Workflow-Automatisierung und Erweiterungen.
* **Creative Models:** Native HPU/NPU-Ausführung von **FLUX.1**, **SDXL**, **Stable Diffusion 3** und Videogenerierungsmodellen (**Wan2.1**, **CogVideo**, **LTX Video**).
* **Workflow Automation:** Verkettung von Generierungs- und Postprocessing-Modulen (z. B. Generate → Upscale).
* **Asset Inspector:** Einzelansicht mit detaillierter Extraktion historischer Parameter zur prompt-basierten Re-Generierung.
* **Plugin Ecosystem:** Paket- und Plugin-Verwaltungssystem für Drittentwickler.

