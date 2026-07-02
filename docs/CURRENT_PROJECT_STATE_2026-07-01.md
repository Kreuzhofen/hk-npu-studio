# Aktueller Projektzustand - SnapdragonAI Studio

Datum: 2026-07-01

## Kurzstatus

Das Projekt `C:\SnapdragonAI` ist ein lokales Windows-ARM64-KI-Projekt mit Fokus auf Qualcomm Snapdragon X und QNN/NPU-Beschleunigung.

Der aktuelle Schwerpunkt liegt auf der Phoenix-Rebuild-Architektur und einer vorhandenen RealESRGAN-QNN-Pipeline.

## Hauptpfade

```text
Projekt:              C:\SnapdragonAI
Qualcomm AI Stack:    C:\Qualcomm\AIStack\2.47.0.260601
Modelle:              C:\SnapdragonAI\models
Plugins:              C:\SnapdragonAI\plugins
Dokumentation:        C:\SnapdragonAI\docs
Stable Diffusion UI:  C:\AI\stable-diffusion-webui
InvokeAI:             C:\AI\invokeai
Comfy Desktop:        C:\Users\holge\AppData\Roaming\Comfy Desktop
ONNX Runtime GenAI:   C:\Users\holge\oga\onnxruntime-genai-0.14.0-win-arm64
```

## Git

```text
Branch: feature/phoenix-rebuild
```

Nicht von Codex erstellte uncommittete Aenderungen:

```text
input/image.raw
widgets/phoenix/right_panel.py
widgets/phoenix/workspace.py
```

Diese Dateien muessen geschuetzt werden.

## Funktionaler Kern

Aktuell wichtigste NPU-nahe Funktion:

```text
RealESRGAN x4 Upscaling ueber QNN / Snapdragon NPU
```

Relevante Dateien:

```text
models\real_esrgan_x4plus.bin
plugins\realesrgan\plugin.py
modules\qnn.py
modules\realesrgan_core.py
engine\backends\qnn_backend.py
```

## QNN-Status

Vorhanden:

```text
qnn-net-run.exe
QnnHtp.dll
QnnSystem.dll
QnnHtpPrepare.dll
```

Das Projekt kann QNN grundsaetzlich finden, weil die erwarteten Dateien existieren.

## Python-Status

Globale Python-Installation:

```text
Python 3.11.9 ARM64
C:\Program Files\Python311-arm64\python.exe
```

Stable Diffusion WebUI:

```text
Python 3.11.9 ARM64
torch 2.12.1+cpu
```

InvokeAI:

```text
Python 3.12.9 AMD64
onnxruntime 1.19.2
Provider: AzureExecutionProvider, CPUExecutionProvider
```

## Architekturstatus

Vorhanden und sinnvoll getrennt:

```text
GUI
Application Layer
Engine
Plugins
Modules
Models
Resources
Docs
```

Noch zu klaeren:

```text
Einheitlicher QNN-Ausfuehrungsweg
Zentrale SDK-Konfiguration
Saubere ONNX Runtime QNN-Erkennung
ComfyUI Workflow-Datei
Datenstrategie fuer output und temp
```

## Aktuelle Bewertung

Das Projekt ist in einem guten Prototyp- bis Fruehprodukt-Zustand. QNN ist nicht nur geplant, sondern bereits konkret eingebunden. Die naechsten Arbeiten sollten vorsichtig, dokumentiert und testbar erfolgen, damit bestehende funktionierende Installationen nicht beschaedigt werden.
