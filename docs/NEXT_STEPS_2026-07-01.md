# Empfohlene naechste Schritte - SnapdragonAI Studio

Datum: 2026-07-01

## Grundregel

Keine bestehende funktionierende Installation darf gebrochen werden. Jede technische Aenderung soll vorher erklaert, separat freigegeben und dokumentiert werden.

## Prioritaet 1: Dokumentation stabilisieren

Ziel: Der Projektzustand soll jederzeit rekonstruierbar sein.

Empfohlene Dokumente:

```text
docs\PROJECT_STATE.md
docs\CHANGELOG.md
docs\DEVELOPMENT_GUIDELINES.md
docs\QNN_SETUP.md
docs\BACKENDS.md
```

Hinweis: Dieses Dokument legt nur Empfehlungen fest. Es aendert keine Konfiguration.

## Prioritaet 2: QNN-Konfiguration zentralisieren

Aktueller Zustand: QNN-Pfade stehen mehrfach im Code.

Risiko: Ein Update des Qualcomm AI Stack kann mehrere Stellen gleichzeitig brechen.

Spaetere Zielidee:

```text
Eine zentrale QNN-Konfiguration
Eine zentrale QNN-Verfuegbarkeitspruefung
Ein klarer Fallback, falls QNN nicht verfuegbar ist
```

Diese Aenderung sollte erst nach expliziter Freigabe umgesetzt werden.

## Prioritaet 3: QNN-Ausfuehrungswege vereinheitlichen

Aktuell gibt es mindestens zwei QNN-Pfade:

```text
modules\qnn.py + modules\realesrgan_core.py
engine\backends\qnn_backend.py
```

Empfehlung: Einen Hauptpfad festlegen, den anderen als Legacy markieren oder spaeter entfernen. Vorher muessen Tests und ein Backup-Konzept vorhanden sein.

## Prioritaet 4: ONNX Runtime QNN untersuchen

Aktuell wurde kein aktiver QNN Execution Provider in Python nachgewiesen.

Untersuchung ohne Installation:

```text
Vorhandene ONNX Runtime Pakete inventarisieren
ARM64-Binaries pruefen
Provider-Listen dokumentieren
Kompatibilitaet mit Qualcomm AI Stack pruefen
```

Keine Installation ohne Freigabe.

## Prioritaet 5: ComfyUI-Anbindung dokumentieren

Das Projekt erwartet:

```text
http://127.0.0.1:8188
C:\SnapdragonAI\workflows\text2image_api.json
```

Empfehlung: Dokumentieren, wie ComfyUI gestartet wird, wo Workflows liegen und welche Modelle verwendet werden.

## Prioritaet 6: Installationen getrennt halten

Bestehende Installationen sollten weiter getrennt bleiben:

```text
C:\SnapdragonAI
C:\AI\stable-diffusion-webui
C:\AI\invokeai
Comfy Desktop
Open WebUI
NPUrun
ONNX Runtime GenAI
```

Das reduziert das Risiko, dass eine Aenderung an einem System ein anderes System beschaedigt.

## Zusammenfassung

Der naechste technische Fortschritt sollte nicht durch grosse Umbauten entstehen, sondern durch saubere Dokumentation, zentrale QNN-Erkennung und vorsichtige Konsolidierung. Die RealESRGAN-QNN-Pipeline ist der beste vorhandene Anker fuer weitere NPU-Arbeit.
