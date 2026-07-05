# Produkt-Roadmap – Snapdragon AI Studio

Diese Roadmap dokumentiert die offiziell beschlossenen Meilensteine und Entwicklungsphasen für Snapdragon AI Studio. Es werden keine hypothetischen Funktionen hinzugefügt.

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
Fokus liegt auf der Plattformstabilisierung und der Bereinigung technischer Schulden.
* **Phoenix-GUI:** Etablierung des neuen, einheitlichen Hauptfensters mit Seitenarchitektur (Pages) und Kapselung der Legacy-Oberflächen.
* **Backend Registry:** Spezifikation eines einheitlichen Schnittstellenvertrags für alle Backends (QNN, ONNX Runtime, CPU, Externe APIs).
* **Modellregistry V2:** Entwurf eines strukturierten Schemas zur Speicherung von Modellmetadaten (Auflösungen, Formate, NPU-Kompatibilität).
* **Zentralisierung der Konfiguration:** Migration verstreuter Pfade (z. B. Qualcomm AI Stack, RealESRGAN-Dateipfade) in eine konfigurierbare Systemschicht.
* **Bereinigung der Inferenz-Pfade:** Konsolidierung der doppelten QNN-Ausführungswege nach Etablierung robuster Komponententests.

### Meilenstein v3.0 – Multi-Backend Platform (Geplant)
Fokus liegt auf der nahtlosen Umschaltung verschiedener Inferenz-Backends.
* **QNN Backend:** Vollwertige Produktivnutzung der Snapdragon-NPU für kompatible Modelle.
* **ONNX Runtime Backend:** Integration von ONNX Runtime (CPU und Evaluierung des QNN Providers).
* **CPU Fallback:** Saubere, sichtbare Kennzeichnung von CPU-Inferenz-Läufen als Ausweichoption.
* **Workflow Registry:** Kapselung lokaler und externer Arbeitsabläufe (z. B. ComfyUI API-Integration über definierte JSON-Workflows).
* **Benchmarking & Monitoring:** Erste Implementierung eines Benchmark-Service zum Geschwindigkeitsvergleich von QNN vs. CPU sowie Hardware-Auslastungsanzeigen im Dashboard.

### Meilenstein v4.0 – Professional Local AI Platform (Geplant)
Fokus liegt auf der Erweiterbarkeit, Automatisierung und lokalen Dienstbereitstellung.
* **Plugin-Management:** Etablierung eines lokalen Paket- und Plugin-Verwaltungssystems.
* **Multimodale Pipelines:** Vollwertige Unterstützung für Text, Bild, Audio (Whisper OCR/TTS) und Vision-Modelle (YOLO).
* **Lokale API / CLI:** Bereitstellung von Steuerungsschnittstellen für externe Programme und Automatisierungsskripte.
* **Diagnose & Support:** Automatische Generierung von Support-Bundles (System-Konfiguration, Treibermatrizen, Logdateien) bei Ausführungsfehlern.
