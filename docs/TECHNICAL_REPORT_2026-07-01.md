# Technischer Bericht - SnapdragonAI Studio

Datum: 2026-07-01
Autor: Codex, im Auftrag von Holger Kreuzhofen
Projekt: Snapdragon AI by Holger Kreuzhofen

## Zweck dieses Dokuments

Dieses Dokument fasst den aktuell analysierten Zustand des lokalen SnapdragonAI-Projekts zusammen. Es wurden fuer diese Analyse keine Konfigurationen geaendert, keine Software installiert und keine Dateien geloescht.

Das Ziel des Gesamtprojekts ist eine moeglichst gute lokale KI-Umgebung auf Windows 11 ARM64 mit Qualcomm Snapdragon X Prozessor. Prioritaet hat dabei Qualcomm NPU-Beschleunigung ueber QNN, sofern technisch sinnvoll und stabil moeglich.

## Analysierter Hauptordner

Der eigentliche Projektordner ist:

```text
C:\SnapdragonAI
```

Der von Codex erzeugte Arbeitsordner unter `Documents\Codex` enthaelt nur die Standardordner `work` und `outputs` und ist nicht das eigentliche Projekt.

## Git-Zustand

Das Projekt `C:\SnapdragonAI` ist ein Git-Repository.

Aktiver Branch:

```text
feature/phoenix-rebuild
```

Uncommittete Aenderungen wurden gefunden in:

```text
input/image.raw
widgets/phoenix/right_panel.py
widgets/phoenix/workspace.py
```

Diese Aenderungen wurden nicht von Codex erstellt und duerfen ohne ausdrueckliche Freigabe nicht ueberschrieben oder geloescht werden.

Die letzten sichtbaren Commits zeigen eine laufende Phoenix-Rebuild-Entwicklung mit Fokus auf Batch-Adapter, Output-Handling und UI-Adapter-Grenzen.

## Projektstruktur

Die vorhandene Struktur ist bereits modular:

```text
C:\SnapdragonAI
├── app
├── assets
├── controllers
├── dialogs
├── docs
├── engine
├── gui
├── input
├── models
├── modules
├── output
├── pages
├── plugins
├── resources
├── temp
├── tools
├── widgets
└── workflows
```

Wichtige Start- und Konfigurationsdateien:

```text
config.py
gui.py
gui_v2.py
launcher.py
phoenix.py
start_gui.bat
models.json
requirements.txt
```

Die Struktur passt grundsaetzlich gut zu einer modularen lokalen KI-Anwendung. GUI, Engine, Module, Plugins, Modelle, Ressourcen und Dokumentation sind getrennt. Das ist eine gute Basis fuer ein stabiles, erweiterbares Snapdragon-X-Projekt.

## Dokumentationszustand

Vorhandene Dokumentationsdateien:

```text
docs\ARCHITECTURE.md
docs\ROADMAP.md
docs\PROJECT_STATE.md
docs\DEVELOPMENT_JOURNAL.md
docs\DEVELOPMENT_GUIDELINES.md
docs\CHANGELOG.md
```

`ARCHITECTURE.md` beschreibt die Phoenix Architecture und eine Zielstruktur mit `app`, `pages`, `widgets`, `modules`, `plugins`, `models`, `assets`, `docs` und `version.py`.

`ROADMAP.md` nennt als geplante Phasen:

```text
v1.1 Identity
v1.2 AI Library
v1.3 Dashboard
v1.5 Generation
v2.0 Phoenix
```

Mehrere Dokumentationsdateien waren zum Analysezeitpunkt leer oder kaum befuellt. Dadurch ist der technische Projektzustand noch nicht vollstaendig aus der Dokumentation heraus rekonstruierbar.

## Qualcomm AI Stack und QNN

Installierter Qualcomm AI Stack:

```text
C:\Qualcomm\AIStack\2.47.0.260601
```

Der Pfad ist im aktuellen `PATH` sichtbar:

```text
C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc
```

Gefundene QNN- und SNPE-Werkzeuge:

```text
qnn-net-run.exe
qnn-platform-validator.exe
qnn-context-binary-generator.exe
qnn-context-binary-utility.exe
qnn-profile-viewer.exe
qnn-throughput-net-run.exe
snpe-net-run.exe
snpe-platform-validator.exe
snpe-throughput-net-run.exe
```

Wichtige QNN-Bibliotheken sind vorhanden:

```text
QnnHtp.dll
QnnHtpPrepare.dll
QnnSystem.dll
QnnCpu.dll
QnnGpu.dll
QnnHtpV68Stub.dll
QnnHtpV73Stub.dll
QnnHtpV81Stub.dll
```

Fuer das Projekt besonders wichtig:

```text
C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-net-run.exe
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll
C:\SnapdragonAI\models\real_esrgan_x4plus.bin
```

Alle drei erwarteten Pfade existieren.

## QNN-Integration im Projekt

QNN ist bereits im Projekt integriert.

Zentrale Dateien:

```text
config.py
modules\qnn.py
modules\realesrgan_core.py
modules\preprocess.py
modules\postprocess.py
engine\backends\qnn_backend.py
plugins\realesrgan\plugin.py
plugins\realesrgan\plugin.json
```

`config.py` enthaelt feste Pfade zum Qualcomm AI Stack, zum QNN-Backend und zum RealESRGAN-Modell.

`modules\qnn.py` fuehrt `qnn-net-run.exe` mit `--retrieve_context`, `--backend`, `--input_list` und `--output_dir` aus.

`modules\realesrgan_core.py` verarbeitet Bilder kachelweise. Die Kacheln werden als RAW-Tensoren vorbereitet, ueber QNN ausgefuehrt und danach wieder zu einem Bild zusammengesetzt.

`engine\backends\qnn_backend.py` enthaelt eine weitere QNN-Backend-Klasse fuer RealESRGAN. Sie bereitet ein Bild auf 128 x 128 Pixel vor, schreibt `image.raw`, ruft `qnn-net-run.exe` auf, liest `upscaled_image.raw` und speichert ein PNG.

Bewertung: Es gibt aktuell mindestens zwei QNN-Ausfuehrungswege. Das ist fuer einen Prototyp verstaendlich, sollte mittelfristig aber vereinheitlicht werden, damit Fehlerbehebungen und Verbesserungen nur an einer Stelle gepflegt werden muessen.

## RealESRGAN-QNN-Modell

Installiertes Modell laut `models.json`:

```text
id: real_esrgan_x4plus_qnn
name: Real-ESRGAN x4 Plus
category: Upscaler
engine: QNN / Snapdragon NPU
file: models/real_esrgan_x4plus.bin
```

Das Modell ist als QNN Context Binary vorhanden:

```text
C:\SnapdragonAI\models\real_esrgan_x4plus.bin
```

Das RealESRGAN-Plugin meldet:

```text
id: realesrgan
name: RealESRGAN
backend: QNN
skill: image.upscale
```

Damit ist RealESRGAN aktuell der wichtigste funktionale NPU-nahe Projektpfad.

## Python-Umgebungen

Globale Python-Installation:

```text
C:\Program Files\Python311-arm64\python.exe
Python 3.11.9 ARM64
```

Diese Installation ist ARM64-nativ und passt gut zum Zielsystem.

Global installierte Pakete:

```text
numpy
pillow
pip
setuptools
tkinterdnd2
```

ONNX Runtime ist in der globalen ARM64-Python-Installation nicht installiert.

## Stable Diffusion WebUI

Gefundener Ordner:

```text
C:\AI\stable-diffusion-webui
```

Python-Umgebung:

```text
C:\AI\stable-diffusion-webui\venv
Python 3.11.9 ARM64
```

Gefundener Torch-Zustand:

```text
torch 2.12.1+cpu
CUDA: nicht vorhanden
CUDA verfuegbar: False
```

Bewertung: Die Umgebung ist ARM64-nativ, aber aktuell CPU-basiert. Das ist stabilitaetsfreundlich, nutzt aber nicht direkt die Qualcomm NPU. Sie sollte vorerst nicht veraendert werden, solange sie funktioniert.

## InvokeAI

Gefundener Ordner:

```text
C:\AI\invokeai
```

Python-Umgebung:

```text
C:\AI\invokeai\.venv
Python 3.12.9 AMD64
```

ONNX Runtime in dieser Umgebung:

```text
onnxruntime 1.19.2
Provider: AzureExecutionProvider, CPUExecutionProvider
```

Bewertung: InvokeAI scheint nicht ARM64-nativ zu laufen, sondern in einer x64-Python-Umgebung. Auf Windows ARM64 kann das funktionieren, ist aber nicht ideal fuer maximale Snapdragon-X-Effizienz. QNN ist dort nicht als ONNX Runtime Provider sichtbar.

## ONNX Runtime und ONNX Runtime GenAI

Gefundene relevante Ordner:

```text
C:\Users\holge\ort
C:\Users\holge\oga\onnxruntime-genai-0.14.0-win-arm64
C:\Users\holge\onnxruntime-genai
```

Bewertung: Es sind ONNX-Runtime- und ONNX-Runtime-GenAI-Komponenten vorhanden, darunter ein ARM64-Paket. Diese sind jedoch noch nicht klar in `C:\SnapdragonAI` integriert. In den geprueften Python-Umgebungen wurde kein QNN Execution Provider fuer ONNX Runtime sichtbar.

## ComfyUI / Comfy Desktop

Gefundener Comfy Desktop Zustand:

```text
C:\Users\holge\AppData\Roaming\Comfy Desktop
```

Das Projekt `C:\SnapdragonAI` erwartet laut README eine lokale ComfyUI-API unter:

```text
http://127.0.0.1:8188
```

Der Browser war waehrend der Analyse auf diese Adresse geoeffnet. Das spricht dafuer, dass ComfyUI lokal erreichbar oder zumindest als Ziel aktiv ist.

Das Projekt erwartet ausserdem eine Workflow-Datei:

```text
C:\SnapdragonAI\workflows\text2image_api.json
```

Diese Datei wurde in der groben Dateiliste nicht sichtbar. Die ComfyUI-Anbindung ist daher wahrscheinlich vorbereitet, aber noch nicht vollstaendig dokumentiert oder final konfiguriert.

## Hardware-Manager

`engine\hardware_manager.py` erkennt:

```text
Windows-Plattform
Maschinenarchitektur
Prozessor
Python-Version
ARM64-Status
RAM
QNN-Verfuegbarkeit
```

Die QNN-Verfuegbarkeit wird aktuell ueber die Existenz dieser Datei bewertet:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll
```

Bewertung: Das ist ein sinnvoller erster Check. Fuer einen robusteren Produktionszustand waere spaeter eine zusaetzliche Validierung ueber `qnn-platform-validator.exe` oder einen kleinen Testlauf sinnvoll.

## Staerken des aktuellen Projekts

- ARM64-native globale Python-Installation ist vorhanden.
- Qualcomm AI Stack und QNN-Werkzeuge sind installiert.
- QNN-Hauptbibliothek `QnnHtp.dll` ist vorhanden.
- RealESRGAN-QNN-Modell ist vorhanden.
- RealESRGAN ist als Plugin angebunden.
- Es gibt eine modulare Phoenix-Architektur.
- Git ist aktiv und der Entwicklungsstand ist nachvollziehbar.
- Stable Diffusion WebUI nutzt eine ARM64-Python-Umgebung.
- ComfyUI-Anbindung ist im Projekt vorgesehen.

## Risiken und technische Schulden

- QNN-Pfade sind hart kodiert und mehrfach vorhanden.
- Es gibt doppelte QNN-Ausfuehrungswege.
- Dokumentationsdateien sind teilweise leer.
- InvokeAI nutzt eine AMD64-Python-Umgebung und ist damit nicht ideal fuer ARM64-native Ziele.
- ONNX Runtime ist nicht global installiert und in InvokeAI nur mit CPU-Provider sichtbar.
- Der ONNX Runtime QNN Execution Provider ist noch nicht als aktiver Python-Provider nachgewiesen.
- `temp` und `output` enthalten viele erzeugte Dateien; eine Datenstrategie fehlt noch.
- Vorhandene uncommittete Aenderungen muessen geschuetzt werden.

## Empfohlene naechste Schritte ohne Risiko fuer bestehende Installationen

1. Dokumentation weiter vervollstaendigen.
2. Aktuellen Projektzustand regelmaessig in `docs` festhalten.
3. QNN-Konfiguration spaeter zentralisieren, aber erst nach Freigabe.
4. Doppelte QNN-Pfade spaeter konsolidieren, aber erst nach Tests.
5. ONNX Runtime QNN separat untersuchen, ohne bestehende Python-Umgebungen zu veraendern.
6. Stable Diffusion WebUI, InvokeAI, ComfyUI und Open WebUI zunaechst unangetastet lassen.

## Zusammenfassung

Das Projekt hat bereits eine starke Basis fuer eine lokale Snapdragon-X-KI-Umgebung. Die wichtigste funktionierende NPU-nahe Komponente ist die RealESRGAN-QNN-Pipeline. Die groesste technische Aufgabe ist nicht die Grundinstallation, sondern die saubere Vereinheitlichung, Dokumentation und spaetere robuste Erkennung von QNN, ONNX Runtime und lokalen KI-Backends.
