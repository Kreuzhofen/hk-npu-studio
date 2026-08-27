# Technical Debt - HK NPU STUDIO

Datum: 2026-07-01
Status: Analyse- und Planungsdokument

## Zweck

Dieses Dokument sammelt die aktuell sichtbaren technischen Schulden des Projekts. Es priorisiert Risiken und Verbesserungen, ohne technische Aenderungen vorzunehmen.

## Bewertungslogik

Prioritaeten:

```text
Sehr hoch: blockiert Zielarchitektur oder NPU-Strategie
Hoch: relevant fuer Stabilitaet, Wartbarkeit oder Erweiterbarkeit
Mittel: wichtig, aber nicht unmittelbar blockierend
Niedrig: kosmetisch oder spaeter optimierbar
```

## Uebersicht

| ID | Bereich | Problem | Risiko | Prioritaet |
|---|---|---|---|---|
| TD-001 | QNN | QNN-Pfade mehrfach hart codiert | SDK-Update kann mehrere Stellen brechen | Sehr hoch |
| TD-002 | QNN | Zwei QNN-Ausfuehrungswege | Fehlerbehebungen laufen auseinander | Sehr hoch |
| TD-003 | Konfiguration | `C:\SnapdragonAI` fest im Code | Projekt schlecht portierbar | Hoch |
| TD-004 | Modellverwaltung | `MODEL_REGISTRY` wird importiert, aber in `config.py` nicht definiert | Modellmanager kann zur Laufzeit brechen | Hoch |
| TD-005 | Backend-System | Keine einheitliche Backend-Schnittstelle | neue Backends werden uneinheitlich | Sehr hoch |
| TD-006 | Hardware-Erkennung | QNN-Verfuegbarkeit nur Dateipruefung | falsche Erfolgsmeldungen moeglich | Hoch |
| TD-007 | ONNX Runtime | kein klar integriertes ONNX Backend | ONNX/QNN-Potenzial bleibt ungenutzt | Hoch |
| TD-008 | Logging | `print`, UI-Log und Tracebacks gemischt | Fehlerdiagnose schwierig | Mittel |
| TD-009 | Fehlerbehandlung | keine zentralen Fehlerklassen | Nutzerhinweise uneinheitlich | Mittel |
| TD-010 | GUI | Legacy und Phoenix parallel | Dopplung und unklare Zieloberflaeche | Hoch |
| TD-011 | Plugin-System | Plugin-Vertrag noch minimal | Erweiterbarkeit begrenzt | Hoch |
| TD-012 | Workflow-System | ComfyUI-Workflowdatei nicht gesichert nachgewiesen | Generate-Funktion unvollstaendig | Mittel |
| TD-013 | Performance | QNN-Kachelung erzeugt viele Temp-Dateien | I/O-Overhead, Speicherbedarf | Hoch |
| TD-014 | ARM64 | InvokeAI nutzt AMD64-Python | Emulation und Performanceverlust | Mittel |
| TD-015 | Dokumentation | zentrale Statusdateien teils leer | Projektwissen bleibt implizit | Hoch |
| TD-016 | Statusmodell | Statuswerte deutsch/englisch gemischt | spaetere API/Tests werden schwieriger | Mittel |
| TD-017 | Magic Numbers | 128, 512, x4 mehrfach implizit | Modellwechsel schwierig | Hoch |
| TD-018 | Datenstrategie | `temp` und `output` wachsen stark | Speicherverbrauch und Unordnung | Mittel |
| TD-019 | Tests | kaum sichtbare automatisierte Tests | Refactoring riskant | Hoch |
| TD-020 | Startskripte | `start_gui.bat` startet Phoenix relativ zum Repository | Behoben | - |

## Details

### TD-001: QNN-Pfade mehrfach hart codiert

Aktueller Zustand:

- `config.py` enthaelt QNN-Pfade.
- `engine/backends/qnn_backend.py` enthaelt dieselben QNN-Pfade erneut.
- `run_realesrgan.py` enthaelt ebenfalls eigene QNN-Pfade.
- `engine/hardware_manager.py` prueft einen festen QNN-Pfad.

Risiko:

Ein Update von `C:\Qualcomm\AIStack\2.47.0.260601` auf eine neue Version wuerde mehrere Stellen brechen.

Empfehlung:

Eine zentrale QNN-Konfiguration einfuehren, die SDK-Version, Bin-Pfad, Lib-Pfad und Backend-DLL an einer Stelle verwaltet.

Prioritaet: Sehr hoch.

### TD-002: Zwei QNN-Ausfuehrungswege

Aktueller Zustand:

- `modules/qnn.py` plus `modules/realesrgan_core.py` fuehren QNN kachelweise aus.
- `engine/backends/qnn_backend.py` fuehrt QNN ueber eine eigene Backend-Klasse aus.

Risiko:

Beide Wege koennen unterschiedliche Annahmen ueber Input, Output, Modellformate und Fehlerbehandlung entwickeln.

Empfehlung:

Einen offiziellen QNN Runner definieren. Der zweite Pfad sollte spaeter als Legacy markiert oder in den Hauptpfad ueberfuehrt werden.

Prioritaet: Sehr hoch.

### TD-003: Hart codierter Projektpfad

Aktueller Zustand:

Mehrere Dateien erwarten `C:\SnapdragonAI`.

Risiko:

Das Projekt ist schwer zu verschieben, zu testen oder in andere Arbeitsverzeichnisse zu bringen.

Empfehlung:

Projektwurzel zentral ueber Konfiguration oder Laufzeitauflösung bestimmen.

Prioritaet: Hoch.

### TD-004: Modellmanager erwartet undefinierte Konstante

Aktueller Zustand:

`modules/model_manager.py` importiert `MODEL_REGISTRY` aus `config.py`. In der gelesenen `config.py` ist `MODEL_REGISTRY` nicht definiert.

Risiko:

Die Modellverwaltung kann beim Import oder Aufruf brechen.

Empfehlung:

In der Planung Modellregistry V2 definieren. Eine technische Korrektur sollte separat freigegeben, getestet und dokumentiert werden.

Prioritaet: Hoch.

### TD-005: Keine einheitliche Backend-Schnittstelle

Aktueller Zustand:

QNN, ComfyUI und Platzhalter-Module haben unterschiedliche Muster.

Risiko:

Neue Backends wie ONNX, CPU, Open WebUI oder InvokeAI werden uneinheitlich angebunden.

Empfehlung:

Backend-Basisvertrag definieren:

```text
is_available()
validate()
get_capabilities()
run(request)
get_status()
```

Prioritaet: Sehr hoch.

### TD-006: Hardware-Erkennung zu oberflaechlich

Aktueller Zustand:

QNN gilt als verfuegbar, wenn `QnnHtp.dll` existiert.

Risiko:

DLL vorhanden bedeutet nicht automatisch, dass NPU-Ausfuehrung funktioniert.

Empfehlung:

Mehrstufige Erkennung:

```text
Datei vorhanden
DLL ladbar
QNN Tool ausfuehrbar
Plattformvalidator erfolgreich
Testmodell lauffaehig
```

Prioritaet: Hoch.

### TD-007: ONNX Runtime nicht als Backend integriert

Aktueller Zustand:

ONNX Runtime ist in Teilen der Umgebung vorhanden, aber nicht als Projektbackend. In InvokeAI wurden nur CPU-Provider erkannt.

Risiko:

Das Projekt kann ONNX-Modelle nicht sauber mit QNN oder CPU-Fallback verwalten.

Empfehlung:

ONNX Runtime als Backend-Familie betrachten: `onnx-qnn`, `onnx-cpu`, spaeter eventuell weitere Provider.

Prioritaet: Hoch.

### TD-008: Uneinheitliches Logging

Aktueller Zustand:

Es gibt `print`, UI-Logmethoden und Tracebacks.

Risiko:

Fehler sind schwer reproduzierbar. Performance- und QNN-Probleme lassen sich spaeter schlecht vergleichen.

Empfehlung:

Zentralen Logger mit Leveln einfuehren:

```text
DEBUG
INFO
WARNING
ERROR
PERFORMANCE
QNN
```

Prioritaet: Mittel.

### TD-009: Fehlerbehandlung nicht domain-spezifisch

Aktueller Zustand:

Viele Fehler werden als allgemeine Exceptions oder Tracebacks behandelt.

Risiko:

Nutzer erhalten technische Fehlermeldungen ohne klare Handlungsempfehlung.

Empfehlung:

Fehlerklassen fuer QNN, Modelle, Workflows, Backends, Eingabedateien und Hardware definieren.

Prioritaet: Mittel.

### TD-010: GUI-Uebergangszustand

Aktueller Zustand:

Die Phoenix-Anwendung verwendet `gui_v2.py`, `app/application.py` und Phoenix-Widgets.

Risiko:

Neue Funktionen koennen an der falschen UI-Schicht angebaut werden.

Empfehlung:

Phoenix als alleinige GUI-Schicht beibehalten.

Prioritaet: Hoch.

### TD-011: Plugin-System noch zu minimal

Aktueller Zustand:

Plugins koennen Skills melden und ausfuehren. Metadaten sind vorhanden.

Risiko:

Kompatibilitaet, Backend-Wahl, Modellanforderungen und Fehler werden nicht standardisiert.

Empfehlung:

Plugin-Schema erweitern um:

```text
capabilities
required_backends
required_models
input_types
output_types
configuration_schema
```

Prioritaet: Hoch.

### TD-012: Workflow-System noch nicht produktreif

Aktueller Zustand:

ComfyUI-API ist vorbereitet. Die erwartete Datei `workflows/text2image_api.json` wurde nicht als vorhanden bestaetigt.

Risiko:

AI Generate wirkt integriert, ist aber vom lokalen Workflowzustand abhaengig.

Empfehlung:

Workflow Registry mit Status, Validierung und Beispiel-Workflows.

Prioritaet: Mittel.

### TD-013: Performance und Temp-Dateien

Aktueller Zustand:

RealESRGAN-QNN arbeitet kachelweise und erzeugt viele RAW- und Metadata-Dateien.

Risiko:

Bei grossen Bildern koennen I/O, Speicher und Dateisystem stark belastet werden.

Empfehlung:

Benchmarking, optionales Temp-Cleanup nach Freigabe, strukturierte Run-Verzeichnisse und spaeter Streaming- oder Batch-Optimierung.

Prioritaet: Hoch.

### TD-014: ARM64-Kompatibilitaet externer Tools

Aktueller Zustand:

Stable Diffusion WebUI ist ARM64 Python mit CPU-Torch. InvokeAI nutzt AMD64-Python.

Risiko:

Emulation kann Performance kosten und Fehler verdecken.

Empfehlung:

ARM64-Kompatibilitaetsmatrix pflegen und Installationen nicht ungefragt veraendern.

Prioritaet: Mittel.

### TD-015: Dokumentation unvollstaendig

Aktueller Zustand:

Mehrere Kerndokumente sind leer oder nur initial befuellt.

Risiko:

Architekturentscheidungen gehen verloren.

Empfehlung:

Nach jeder groesseren Aenderung `PROJECT_STATE.md` und `CHANGELOG.md` aktualisieren. Architekturentscheidungen als ADRs oder Planungsdokumente festhalten.

Prioritaet: Hoch.

## Technische-Schulden-Backlog nach Prioritaet

### 🟢 Sofort sinnvoll

- TD-001 dokumentieren und zentrale QNN-Konfiguration planen.
- TD-002 offiziellen QNN-Pfad festlegen.
- TD-004 Modellregistry-Problem als konkreten Bug markieren.
- TD-005 Backend-Schnittstelle als Architekturvertrag definieren.
- TD-015 Dokumentationsstand stabilisieren.

### 🟡 Mittelfristig

- TD-006 Hardware-Erkennung mehrstufig machen.
- TD-008 Logging vereinheitlichen.
- TD-009 Fehlerklassen einfuehren.
- TD-010 Phoenix-GUI als Ziel festlegen.
- TD-011 Plugin-Schema erweitern.
- TD-012 Workflow Registry einfuehren.

### 🔴 Langfristig

- TD-007 ONNX Runtime QNN produktiv anbinden.
- TD-013 Performance-Pipeline optimieren.
- TD-014 externe Tools ARM64-nativ bewerten oder isolieren.
- TD-018 Datenstrategie fuer Temp, Output und Artefakte.
- TD-019 automatisierte Tests und Benchmark-Suite.

## Zusammenfassung

Die kritischsten technischen Schulden betreffen QNN, Backend-Abstraktion und Konfiguration. Diese Bereiche sollten vor grossen Feature-Erweiterungen stabilisiert werden, weil sie die Grundlage fuer alle spaeteren Plattformfaehigkeiten bilden.
