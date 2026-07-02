# Architecture Plan V2 - Snapdragon AI by Holger Kreuzhofen

Datum: 2026-07-01
Status: Zielarchitektur und Planungsdokument
Geltungsbereich: C:\SnapdragonAI

## Zweck

Dieses Dokument beschreibt eine professionelle Zielarchitektur fuer Snapdragon AI by Holger Kreuzhofen. Es basiert auf der erneuten Analyse des vorhandenen Projekts, der vorhandenen Dokumentation und den Projektregeln aus `docs/CODEX_INSTRUCTIONS.md`.

Es wurden fuer dieses Dokument keine Quellcode-Dateien und keine Konfigurationen geaendert.

## Leitprinzipien

- ARM64 First
- Qualcomm NPU First
- QNN vor CPU
- CPU nur als Fallback
- klare Schichtenarchitektur
- zentrale Konfiguration statt hart codierter Pfade
- einheitliche Backend-Schnittstellen
- reproduzierbare Modellverwaltung
- dokumentierte Workflows
- saubere Fehlerbehandlung und Logging
- keine doppelten Implementierungen
- bestehende funktionierende Installationen schuetzen

## Aktueller Gesamtzustand

Das Projekt ist bereits mehr als eine Sammlung einzelner Skripte. Es besitzt eine beginnende Phoenix-Architektur mit GUI, Engine, Plugins, Modulen, Ressourcen, Modellen und Dokumentation. Der staerkste funktionale Anker ist RealESRGAN-Upscaling ueber Qualcomm QNN.

Gleichzeitig befinden sich mehrere Architekturteile noch im Uebergang:

- Legacy-GUI und Phoenix-GUI existieren parallel.
- QNN ist mehrfach implementiert.
- Konfiguration ist zentral begonnen, aber wichtige Pfade sind hart codiert.
- Modellverwaltung ist vorhanden, aber noch nicht stabil und offenbar nicht vollstaendig verdrahtet.
- Backend-Abstraktion ist noch nicht einheitlich.
- Logging ist ueberwiegend ad hoc ueber `print`, UI-Logs und Tracebacks geloest.
- ONNX Runtime ist lokal vorhanden, aber noch nicht als klares Projekt-Backend integriert.

## Ziel-Schichtenarchitektur

Die langfristige Zielarchitektur soll die folgenden Schichten sauber trennen:

```text
GUI
  ↓
Application Layer
  ↓
Engine
  ↓
Backend Registry
  ↓
Backend Implementations
  ↓
Plugin System
  ↓
Model Management
  ↓
Hardware Detection
  ↓
Configuration
  ↓
Utilities / Logging / Resources
```

### GUI

Aufgabe: Darstellung, Navigation, Nutzerinteraktion, Vorschau, Statusanzeigen.

Die GUI soll keine direkten QNN-, ONNX-, Modell- oder Dateisystemdetails kennen. Sie ruft Application Services auf und zeigt deren Status an.

### Application Layer

Aufgabe: Koordination zwischen GUI, Engine, Jobs, Workflows und Benutzeraktionen.

Diese Schicht entscheidet, welcher Use Case ausgefuehrt wird, aber nicht, wie QNN, ONNX oder CPU intern arbeiten.

### Engine

Aufgabe: Job-Verarbeitung, Queue, Scheduler, Worker, Skill-Ausfuehrung, Statusmodell.

Die Engine soll GUI-unabhaengig bleiben und spaeter auch von CLI, API oder Tests genutzt werden koennen.

### Backend Registry

Aufgabe: Verfuegbare Backends erkennen, priorisieren und auswaehlen.

Beispiel-Prioritaet:

```text
QNN Backend
ONNX Runtime QNN Backend
ONNX Runtime CPU Backend
Native CPU Backend
External Backend wie ComfyUI oder InvokeAI
```

### Backend Implementations

Aufgabe: konkrete Ausfuehrung auf QNN, ONNX, CPU, ComfyUI, InvokeAI, Open WebUI oder spaeter Cloud.

Jedes Backend soll dieselbe Basisschnittstelle anbieten:

```text
name
kind
capabilities
is_available()
validate()
run(request)
get_status()
```

### Plugin System

Aufgabe: Fachfunktionen bereitstellen, zum Beispiel `image.upscale`, `image.generate`, `text.generate`, `audio.transcribe`.

Plugins sollen Backends nicht hart verdrahten, sondern ueber die Backend Registry anfordern.

### Model Management

Aufgabe: Modelle registrieren, Verfuegbarkeit pruefen, Backend-Kompatibilitaet dokumentieren, Pfade aufloesen, Metadaten pflegen.

Ein Modell sollte nicht nur ein Dateipfad sein, sondern ein Datensatz mit:

```text
id
name
task
format
backend_compatibility
precision
quantization
input_shape
output_shape
source
license
local_path
status
```

### Hardware Detection

Aufgabe: Windows ARM64, Snapdragon X, NPU/QNN, RAM, Python-Architektur, SDK-Versionen und Backend-Faehigkeiten erkennen.

Die Hardware-Erkennung soll nicht nur Dateien pruefen, sondern Validierungsstufen besitzen:

```text
installed
loadable
validated
benchmark_ready
```

### Configuration

Aufgabe: zentrale Verwaltung aller Pfade, Ports, Backend-Prioritaeten und Laufzeitoptionen.

Ziel: keine verstreuten hart codierten Pfade fuer `C:\SnapdragonAI`, `C:\Qualcomm\AIStack` oder ComfyUI-Ports.

## Komponentenbewertung

| Komponente | Aktueller Zustand | Staerken | Schwaechen | Risiken | Verbesserungspotenzial | Prioritaet |
|---|---|---|---|---|---|---|
| Gesamtarchitektur | Phoenix-Struktur begonnen, Legacy-Anteile vorhanden | klare Ordner fuer Engine, GUI, Plugins, Module | Uebergangszustand, teilweise doppelte Pfade | schleichende Kopplung zwischen UI und Runtime | Zielschichten verbindlich dokumentieren und schrittweise umsetzen | Hoch |
| GUI | Tkinter-GUI, Phoenix UI und Legacy-Anteile parallel | lauffaehige Oberflaeche, Adapter fuer Batch vorhanden | Phoenix-Adapter teilweise Platzhalter, Logik teils in GUI | UI kann Backend-Details dauerhaft fest verdrahten | GUI auf Application Services reduzieren | Hoch |
| Application Layer | `ApplicationController` und Adapter vorhanden | gute Richtung fuer Entkopplung | noch stark an konkrete Widgets und Controller gebunden | schwer testbare Ablaufe | Use-Case-Services einfuehren | Hoch |
| Engine | Queue, Scheduler, Worker, Skill-System vorhanden | GUI-unabhaengige Kernbausteine erkennbar | Statuswerte teils deutsch/englisch gemischt, kein persistentes Jobmodell | Inkonsistente Zustandslogik | einheitliches Job- und Statusmodell | Hoch |
| Backend-System | QNN direkt, ComfyUI direkt, CPU-Platzhalter | QNN funktioniert konzeptionell | keine einheitliche Backend-Schnittstelle | doppelte Implementierungen und schwerer Fallback | Backend Registry mit Prioritaeten | Sehr hoch |
| Plugin-System | JSON-Metadaten und Skill-Registry vorhanden | erweiterbarer Ansatz | Plugin-API noch klein, Fehlerbehandlung einfach | Plugins koennen Backend-Details hart verdrahten | Plugin-Vertrag und Capability-Modell definieren | Hoch |
| Hardware-Erkennung | ARM64, RAM, QNN-Dateipruefung vorhanden | einfacher Einstieg | QNN wird nur ueber Datei existiert erkannt | falsche positive Ergebnisse moeglich | Validierung ueber QNN-Tools und Test-Inferenz | Hoch |
| Qualcomm QNN | RealESRGAN-QNN vorhanden | wichtigster NPU-Anker | Pfade mehrfach hart codiert, doppelte QNN-Wege | SDK-Update bricht Code | zentrale QNN-Konfiguration und Runner | Sehr hoch |
| ONNX Runtime | lokal vorhanden, aber nicht integriert | Potenzial fuer standardisierte Inferenz | kein aktiver QNN Provider nachgewiesen | CPU-Fallback wird irrtuemlich fuer NPU gehalten | ONNX Backend sauber evaluieren | Hoch |
| NPU-Integration | QNN fuer RealESRGAN nutzbar | echte NPU-Richtung | keine allgemeine NPU-Abstraktion | jedes Modell braucht Sondercode | NPU Capability Layer | Sehr hoch |
| Modellverwaltung | `models.json`, `model_manager.py` vorhanden | Registry-Idee vorhanden | `MODEL_REGISTRY` in `config.py` nicht definiert | Modellseite kann brechen | Modellregistry V2 mit Schema | Hoch |
| Workflow-System | ComfyUI API vorbereitet | lokaler Workflow-Ansatz sinnvoll | Workflow-Datei vermutlich nicht vorhanden | Generate-Funktion unvollstaendig | Workflow Registry fuer ComfyUI und interne Workflows | Mittel |
| Konfigurationssystem | `config.py` vorhanden | zentraler Startpunkt | harte Pfade, Magic Numbers, kein Profilkonzept | geringe Portabilitaet | Settings-Datei plus Pfadauflösung | Sehr hoch |
| Logging | UI-Log, `print`, Tracebacks | Fehler werden teilweise sichtbar | kein einheitlicher Logger | Debugging wird schwer | zentrales Logging mit Leveln und Logdateien | Mittel |
| Fehlerbehandlung | Exceptions, Tracebacks, UI-Meldungen | Fehler verschwinden nicht komplett | keine Fehlerklassen, keine Recovery-Strategie | schlechte Nutzerdiagnose | Fehlerdomänen und Benutzerhinweise | Mittel |
| Performance | QNN-Kachelung vorhanden | NPU-orientierter Ansatz | sequenzielle Kachelverarbeitung, viele Temp-Dateien | I/O und Overhead bei grossen Bildern | Benchmarking, Profiling, Batch-Optimierung | Hoch |
| ARM64-Kompatibilitaet | globale Python ARM64, SD WebUI ARM64 | wichtige Basis stimmt | InvokeAI AMD64, ORT-QNN nicht geklaert | Emulation kostet Leistung | ARM64-Kompatibilitaetsmatrix | Hoch |
| Wartbarkeit | Module und Docs vorhanden | gute Grundlage | leere Docs, doppelte Implementierungen | Wissen bleibt implizit | Architekturentscheidungen dokumentieren | Hoch |
| Erweiterbarkeit | Plugins, Skills, Module | klare Absicht | Plugin-Vertrag noch zu schwach | neue Features werden uneinheitlich | Capabilities, Backend Registry, Modellregistry | Sehr hoch |

## Zielarchitektur Version 2.0

Version 2.0 soll die Phoenix-Basis stabilisieren. Der Fokus liegt nicht auf moeglichst vielen Features, sondern auf einer tragfaehigen Plattformstruktur.

Ziele:

- Phoenix-GUI als primäre Oberflaeche stabilisieren.
- Legacy-GUI nicht abrupt entfernen, sondern kontrolliert einfrieren.
- QNN-Konfiguration zentralisieren.
- Einen offiziellen QNN-Ausfuehrungsweg definieren.
- Modellregistry V2 entwerfen und dokumentieren.
- Backend Registry als Architekturvertrag einfuehren.
- Hardware-Erkennung erweitern, ohne Installationen zu veraendern.
- Dokumentation vervollstaendigen.

Empfohlene V2-Schichten:

```text
GUI Phoenix
ApplicationController / Use Case Services
Phoenix Engine
Backend Registry
QNN Backend
Plugin System
Model Registry V2
Hardware Profile
Configuration Service
Logging Service
```

Nicht-Ziele fuer V2:

- keine grossen Installationsumbauten
- keine Entfernung funktionierender Legacy-Komponenten ohne Tests
- keine automatische Paketinstallation
- kein Cloud-Backend

## Zielarchitektur Version 3.0

Version 3.0 soll aus der stabilisierten Plattform eine Multi-Backend-KI-Umgebung machen.

Ziele:

- QNN Backend als Standard fuer kompatible Modelle.
- ONNX Runtime Backend mit klarer Provider-Erkennung.
- CPU Backend als definierter Fallback.
- ComfyUI und InvokeAI als externe Backends sauber kapseln.
- Workflow Registry fuer lokale und externe Workflows.
- Benchmarking fuer QNN, ONNX und CPU.
- Model Management mit Kompatibilitaetspruefung.
- Hardware Monitoring im Dashboard.

Empfohlene V3-Schichten:

```text
GUI Phoenix
Application Services
Workflow Engine
Phoenix Engine
Backend Registry
QNN Backend / ONNX Backend / CPU Backend / External Backend
Plugin Capability System
Model Registry V2
Benchmark Service
Hardware Monitor
Configuration Profiles
```

## Zielarchitektur Version 4.0

Version 4.0 soll die Plattform professionell und erweiterbar machen: nicht nur lokal lauffaehig, sondern als robuste KI-Arbeitsumgebung fuer Modelle, Workflows, Agenten und Automatisierung.

Ziele:

- Plugin Marketplace oder lokale Plugin-Verwaltung.
- Agenten- und RAG-Unterstuetzung.
- Text, Bild, Audio, Vision und OCR als gleichwertige Domänen.
- Erweiterbares Workflow-System.
- Saubere API fuer lokale Tools und externe UIs.
- Optional Cloud Backends als Fallback oder Spezialfaelle.
- Reproduzierbare Benchmarks und Hardwareprofile.
- Professionelle Fehlerdiagnose und Support-Bundles.

Empfohlene V4-Schichten:

```text
Desktop GUI / Local API / CLI
Application Services
Workflow and Agent Runtime
Task Engine
Backend Orchestrator
Local Backends / External Backends / Optional Cloud Backends
Plugin and Extension System
Model and Asset Registry
Hardware and Benchmark Layer
Configuration and Policy Layer
Observability Layer
```

## Zielbild fuer Backend-Auswahl

Backends sollen nicht direkt von Plugins aufgerufen werden. Stattdessen soll ein Request ueber eine zentrale Auswahl laufen.

Beispiel:

```text
Plugin: image.upscale
  -> Backend Registry fragt: Welche Backends koennen image.upscale?
  -> QNN Backend ist verfuegbar und kompatibel
  -> Modellregistry liefert RealESRGAN-QNN-Modell
  -> Engine startet Job
  -> Logging, Fortschritt und Fehler laufen zentral
```

Fallback-Regel:

```text
QNN bevorzugen
ONNX Runtime mit QNN bevorzugen, falls geeignet
CPU nur nutzen, wenn kein NPU-Pfad verfuegbar ist oder der Benutzer es explizit waehlt
```

## Priorisierter Maßnahmenplan

### 🟢 Sofort sinnvoll

- Dokumentation vervollstaendigen und aktuell halten.
- Bestehende technische Schulden sichtbar machen.
- QNN-Pfade und doppelte QNN-Implementierungen dokumentieren.
- `MODEL_REGISTRY`-Problem in der Planung festhalten.
- Backend Registry als Architekturentscheidung festlegen.
- Keine funktionierende Installation veraendern.

### 🟡 Mittelfristig

- Zentrale Konfigurationsschicht einfuehren.
- Einheitlichen QNN Runner definieren.
- Modellregistry V2 mit Schema erstellen.
- Logging vereinheitlichen.
- Fehlerklassen und Benutzerdiagnose einfuehren.
- ONNX Runtime QNN separat evaluieren.
- Workflow Registry fuer ComfyUI vorbereiten.

### 🔴 Langfristig

- Multi-Backend-Orchestrierung fuer QNN, ONNX, CPU und externe Backends.
- Benchmarking und Hardware Monitoring integrieren.
- RAG, Agenten, OCR, Whisper und TTS als Plattformfaehigkeiten einbauen.
- Plugin-Verwaltung professionalisieren.
- Optional Cloud Backends mit klarer Policy und Datenschutzregeln.

## Zusammenfassung

Die Zielarchitektur soll Snapdragon AI by Holger Kreuzhofen von einem starken Prototyp mit QNN-Anker zu einer professionellen lokalen KI-Plattform entwickeln. Der wichtigste kurzfristige Schritt ist nicht ein neues Feature, sondern eine saubere Plattformbasis: zentrale Konfiguration, einheitliche Backend-Abstraktion, stabile Modellverwaltung und klare Dokumentation.
