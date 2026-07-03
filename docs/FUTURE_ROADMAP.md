# Future Roadmap - Snapdragon AI Studio

Datum: 2026-07-01
Status: Strategische Roadmap

## Zielbild

Snapdragon AI Studio soll eine professionelle lokale KI-Plattform fuer Windows 11 ARM64 und Qualcomm Snapdragon X werden. Die Plattform soll langfristig mehrere KI-Domaenen unter einer sauberen Architektur vereinen:

- Textgeneration
- Bildgenerierung
- Bildverbesserung
- Upscaling
- OCR
- Whisper
- Sprachausgabe
- LLMs
- Vision Modelle
- RAG
- Agenten
- Workflows
- Plugins
- Model Management
- Benchmarking
- Hardware Monitoring
- QNN Backend
- ONNX Backend
- CPU Backend
- optional spaeter Cloud Backends

Die Prioritaet bleibt: Qualcomm NPU ueber QNN zuerst, CPU nur als Fallback.

## Roadmap Version 2.0: Phoenix Foundation

Version 2.0 soll die Plattformbasis stabilisieren.

### Ziele

- Phoenix-GUI als Zieloberflaeche festlegen.
- Legacy-GUI stabil halten, aber nicht unkontrolliert erweitern.
- QNN-Konfiguration zentral planen und spaeter umsetzen.
- Doppelte QNN-Ausfuehrungswege bereinigen, nachdem Tests vorhanden sind.
- Backend Registry als Konzept einfuehren.
- Modellregistry V2 spezifizieren.
- Hardware-Erkennung verbessern.
- Dokumentation vervollstaendigen.

### Ergebnis von Version 2.0

Am Ende von V2 soll das Projekt eine stabile Architekturgrundlage haben:

```text
Phoenix GUI
Application Layer
Phoenix Engine
Backend Registry Konzept
QNN Backend als erster offizieller Backend-Pfad
Model Registry V2 Spezifikation
Hardware Profile
zentrale Dokumentation
```

### Akzeptanzkriterien

- Die Zielarchitektur ist dokumentiert.
- Der offizielle QNN-Pfad ist bekannt.
- Technische Schulden sind priorisiert.
- Neue Features koennen gegen Backend- und Plugin-Vertraege geplant werden.
- Bestehende Installationen bleiben unangetastet.

## Roadmap Version 3.0: Multi-Backend Platform

Version 3.0 soll die Plattform von einer QNN-zentrierten Anwendung zu einer kontrollierten Multi-Backend-Plattform ausbauen.

### Ziele

- QNN Backend produktiv als bevorzugtes Backend nutzen.
- ONNX Runtime als Backend-Familie integrieren.
- CPU Backend als expliziten Fallback anbieten.
- ComfyUI als External Backend sauber kapseln.
- InvokeAI und Open WebUI als externe Dienste bewerten und dokumentieren.
- Workflow Registry einfuehren.
- Modellkompatibilitaet pro Backend erfassen.
- Benchmarking fuer QNN, ONNX und CPU vorbereiten.
- Hardware Monitoring im Dashboard anzeigen.

### Ergebnis von Version 3.0

```text
Backend Registry
QNN Backend
ONNX Runtime Backend
CPU Backend
External Backend Adapter
Workflow Registry
Model Registry V2
Benchmark Service
Hardware Monitor
```

### Akzeptanzkriterien

- Backends koennen nach Faehigkeit ausgewaehlt werden.
- QNN hat Vorrang vor CPU.
- CPU-Fallback ist sichtbar und nicht versehentlich als NPU markiert.
- Modelle haben Kompatibilitaetsinformationen.
- Workflows sind registriert und validierbar.

## Roadmap Version 4.0: Professional Local AI Platform

Version 4.0 soll die Plattform in Richtung professioneller KI-Arbeitsumgebung erweitern.

### Ziele

- Plugin-Verwaltung professionalisieren.
- Workflows, Agenten und RAG integrieren.
- Text, Bild, Audio, OCR und Vision als gleichwertige Domaenen behandeln.
- Lokale API oder CLI fuer Automatisierung anbieten.
- Benchmark- und Diagnoseberichte erzeugen.
- Optional Cloud Backends als klar gekennzeichnete Fallbacks oder Spezialdienste einbinden.
- Support-Bundles fuer Fehleranalyse bereitstellen.

### Ergebnis von Version 4.0

```text
Desktop GUI
Local API
Workflow Engine
Agent Runtime
Backend Orchestrator
Plugin Management
Model and Asset Registry
Hardware and Benchmark Layer
Observability Layer
Policy Layer fuer lokale und optionale Cloud-Ausfuehrung
```

### Akzeptanzkriterien

- Plattform ist nicht mehr tool-zentriert, sondern workflow- und capability-zentriert.
- Lokale Backends bleiben bevorzugt.
- Cloud ist optional, transparent und kontrolliert.
- Diagnose, Logging und Benchmarking sind professionell nutzbar.

## Domaenen-Roadmap

| Domaene | V2 | V3 | V4 |
|---|---|---|---|
| Upscaling | RealESRGAN-QNN stabilisieren | weitere Upscaler pruefen | Workflow- und Batch-Optimierung |
| Bildgenerierung | ComfyUI-Anbindung dokumentieren | ComfyUI Backend kapseln | Workflow Engine integrieren |
| Textgeneration | Zielbackend definieren | Open WebUI / lokale LLMs anbinden | Agenten und RAG |
| OCR | planen | ONNX/QNN-Modell pruefen | Dokumenten-Workflows |
| Whisper | planen | lokales Backend pruefen | Audio-Pipeline |
| TTS | planen | Backend evaluieren | multimodale Workflows |
| Vision | YOLO/Depth als Platzhalter dokumentieren | ONNX/QNN Vision evaluieren | Vision-Agenten |
| Benchmarking | Konzept | Service | Vergleichsberichte |
| Hardware Monitoring | Konzept | Dashboard | Diagnosepakete |

## Backend-Roadmap

### QNN Backend

Kurzfristig:

- offiziellen QNN Runner definieren
- QNN-Konfiguration zentralisieren
- RealESRGAN als Referenzpipeline nutzen

Mittelfristig:

- QNN-Verfuegbarkeit validieren
- QNN-Profiling auswerten
- weitere QNN-Modelle aufnehmen

Langfristig:

- QNN als Standard-Backend fuer kompatible Modelle etablieren

### ONNX Runtime Backend

Kurzfristig:

- vorhandene ONNX Runtime Komponenten dokumentieren
- Provider-Status erfassen

Mittelfristig:

- ONNX CPU Backend definieren
- ONNX QNN Provider separat evaluieren

Langfristig:

- ONNX als Standardformat fuer portable lokale Modelle nutzen, sofern QNN-kompatibel

### CPU Backend

Kurzfristig:

- nur als Fallback definieren

Mittelfristig:

- CPU-Ausfuehrung klar kennzeichnen

Langfristig:

- CPU fuer Diagnose, Tests und nicht NPU-faehige Modelle nutzen

### External Backends

Kurzfristig:

- ComfyUI, InvokeAI, Open WebUI dokumentieren

Mittelfristig:

- External Backend Adapter einfuehren

Langfristig:

- externe Dienste als kontrollierte Plattformbausteine integrieren

## Priorisierter Maßnahmenplan

### 🟢 Sofort sinnvoll

1. Architekturplan V2, technische Schulden und Roadmap dokumentieren.
2. Projektstatus und bestehende uncommittete Aenderungen schuetzen.
3. QNN als bevorzugten Plattformanker bestaetigen.
4. Doppelte QNN-Pfade als technische Schuld behandeln.
5. `MODEL_REGISTRY`-Problem in der Modellverwaltung als Risiko aufnehmen.
6. Backend Registry als kuenftigen Architekturvertrag festlegen.
7. Dokumentation in deutscher Sprache aktuell halten.

### 🟡 Mittelfristig

1. Zentrale Konfigurationsschicht entwerfen und nach Freigabe umsetzen.
2. QNN Runner vereinheitlichen und testen.
3. Model Registry V2 spezifizieren und spaeter implementieren.
4. Backend-Schnittstelle fuer QNN, ONNX, CPU und External Backends definieren.
5. Logging und Fehlerbehandlung vereinheitlichen.
6. Workflow Registry fuer ComfyUI und spaeter interne Workflows planen.
7. ARM64-Kompatibilitaetsmatrix fuer alle lokalen Tools pflegen.
8. Benchmarking fuer RealESRGAN-QNN als ersten Standardtest einfuehren.

### 🔴 Langfristig

1. ONNX Runtime QNN produktiv evaluieren und integrieren.
2. Multi-Backend-Orchestrierung ausbauen.
3. RAG, Agenten, OCR, Whisper, TTS und Vision Modelle integrieren.
4. Plugin-System professionalisieren.
5. Hardware Monitoring und Diagnoseberichte bereitstellen.
6. Optional Cloud Backends mit klaren Datenschutz- und Ausfuehrungsregeln einfuehren.
7. Plattform als lokale KI-Arbeitsumgebung mit API, CLI und Desktop-GUI abrunden.

## Strategische Empfehlung

Die naechste Entwicklungsphase sollte nicht mit neuen grossen Features beginnen. Der groesste Wert entsteht zuerst durch Stabilisierung der Plattformbasis:

```text
Konfiguration zentralisieren
QNN vereinheitlichen
Backend Registry definieren
Model Registry V2 aufbauen
Logging und Fehlerbehandlung ordnen
```

Erst danach sollten weitere KI-Domaenen wie OCR, Whisper, LLMs, RAG und Agenten aktiv integriert werden. Dadurch bleibt Snapdragon AI Studio langfristig wartbar, stabil und wirklich NPU-orientiert.
