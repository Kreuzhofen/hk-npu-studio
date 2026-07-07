# Snapdragon AI Studio Development Journal

Created by Holger Kreuzhofen

## 26.06.2026 – Sprint 005.2 – Theme Manager

Status: Prepared

### Goals

- Projektstruktur für die künftige Pages-Architektur vorbereiten.
- Zentrales SAI Design System einführen.
- Wiederverwendbare UI-Bausteine vorbereiten.
- Erste Dashboard-Page als Grundlage erstellen.

### Added

- `app/theme.py`
- `widgets/card.py`
- `pages/base_page.py`
- `pages/dashboard.py`
- `docs/ARCHITECTURE.md`
- `docs/DEVELOPMENT_JOURNAL.md`

### Notes

Die stabile Version 1.1 bleibt erhalten. Die Phoenix-Architektur wird parallel aufgebaut.

## 06.07.2026 – Bugfix-Korrekturen – Galerie & Upscaler

Status: Completed

### Goals

- Behebung des Problems, dass Gallery Thumbnails nach Resize als Platzhalter verbleiben.
- Behebung des verzerrten Bild-Outputs im RealESRGAN-Plugin.

### Modified

- `widgets/phoenix/gallery/thumbnail_provider.py`
- `engine/backends/qnn_backend.py`
- `run_realesrgan.py`

### Notes

1. Der `ThumbnailProvider` wurde so erweitert, dass er mehrere Callbacks für denselben pending Thumbnail-Ladevorgang registriert und nach Fertigstellung alle auslöst.
2. `_restore_target_resolution` im `QNNBackend` und das Hilfsskript `run_realesrgan.py` wurden so implementiert, dass das `512x512`-Ergebnisbild auf `(original_width * 4, original_height * 4)` skaliert wird, um das Seitenverhältnis wiederherzustellen.

## 07.07.2026 – Sprint P-050 – Gallery → Compare Workflow Completion

Status: Completed

### Goals

- Den begonnenen Gallery → Compare Workflow sauber fertigstellen.
- Doppelklick-Workflow über Controller/Adapter.
- Kontextmenü („In Compare öffnen“) mit passendem PHOENIX_THEME-Styling.
- Stabile Anzeige des geladenen Bildes als Original/Source, während die leere Ausgabe als Platzhalter verbleibt.
- Keine Abstürze bei sehr großen Bildern in der Vergleichsansicht.

### Modified

- `widgets/phoenix/gallery/thumbnail_widget.py`
- `widgets/phoenix/gallery/thumbnail_area.py`
- `controllers/compare_workspace_controller.py`

### Notes

Der Gallery → Compare-Workflow ist nun vollständig abgeschlossen. Kontextmenü-Rechtsklicks rufen dieselbe Steuerung auf wie Doppelklicks. Große Bilder werden beim Laden im Compare-Workspace zur Vermeidung von Verzögerungen und OOMs automatisch auf maximal 4096px Kantenlänge herunterskaliert, während die vollen Auflösungsmetadaten intakt bleiben.

## 07.07.2026 – Sprint P-051 – Prompt Workspace Foundation

Status: Completed

### Goals

- Neuen Prompt Workspace als stabile UI-/Architektur-Foundation erstellen (ohne echte Bildgenerierung).
- Workspace in Navigation/Sidebar einbinden.
- Parameter-UI bauen (Modell-Auswahl, Prompt, Negative Prompt, Seed, Steps, CFG, Breite, Höhe).
- Generierungs-Vorschau und Statuszeile einrichten.
- MVC-Controller und Generate-Stub implementieren.

### Modified / Added

- `controllers/prompt_workspace_model.py` (neu)
- `controllers/prompt_workspace_controller.py` (neu)
- `widgets/phoenix/views/prompt_view.py` (neu)
- `widgets/phoenix/sidebar.py` (modifiziert)
- `widgets/phoenix/workspace.py` (modifiziert)

### Notes

Der „AI Generate“ / Prompt Workspace ist nun als sauberes MVC-Fundament in der Phoenix-Architektur integriert. Der Generate-Button sammelt alle eingegebenen Parameter, gibt sie zu Diagnosezwecken im Standard-Output aus und setzt den Workspace-Status auf „Generation queued (stub)“. Die gesamte Oberfläche nutzt den ThemeManager und ist voll kompatibel zum Light- und Dark-Theme.

## 07.07.2026 – Sprint P-052 – Generation Session & Generation Controller Foundation

Status: Completed

### Goals

- Zentrale Daten- und Controllerstruktur für die Generierung schaffen (ohne AI-Backend).
- GenerationSessionModel als Single Source of Truth erstellen.
- GenerationController zur Steuerung, Validierung und Stubbierung von queue/cancel einrichten.
- PromptWorkspaceController als Vermittler umgestalten, der Aufrufe über den GenerationController an GenerationSession weiterreicht.
- Kommentare und Vorbereitungen für künftige NPU/CPU/Remote Backends einfügen.

### Modified / Added

- `controllers/generation_session.py` (neu)
- `controllers/generation_controller.py` (neu)
- `controllers/prompt_workspace_controller.py` (modifiziert)

### Notes

Das Generierungs-Fundament ist nun sauber entkoppelt von der GUI-Ebene. Der PromptWorkspaceController fungiert nur noch als Vermittler, der Eingaben an den zentralen GenerationController weiterreicht. Die Generierungsparameter werden im GenerationSessionModel als Single Source of Truth verwaltet. Validierung für Pflichtfelder und Wertebereiche ist implementiert.

## 07.07.2026 – Sprint P-053 – Generation Pipeline Foundation

Status: Completed

### Goals

- Die Generierungs-Pipeline-Architektur vorbereiten (ohne Threads/Worker/AI).
- GenerationJob-Klasse als Datenobjekt anlegen.
- GenerationQueue-Klasse als FIFO-Jobverwaltung erstellen.
- GenerationController erweitern, um Jobs per queue_generation() einzustellen.
- Prompt Workspace anpassen, um Queue-Größe und Status "X Jobs in Warteschlange" zu integrieren.
- Veraltete Bezüge auf RealESRGAN/QNN im UI und BatchController neutralisieren.
- Platzhalter für künftige Backend-Adapter vorbereiten.

### Modified / Added

- `controllers/generation_job.py` (neu)
- `controllers/generation_queue.py` (neu)
- `controllers/generation_controller.py` (modifiziert)
- `widgets/phoenix/views/prompt_view.py` (modifiziert)
- `widgets/phoenix/views/image_view.py` (modifiziert)
- `widgets/phoenix/views/home_view.py` (modifiziert)
- `widgets/phoenix/right_panel.py` (modifiziert)
- `widgets/phoenix/cards/job_card.py` (modifiziert)
- `gui/controllers/batch_controller.py` (modifiziert)

### Notes

Die Generierungs-Pipeline steht nun als stabiles Architekturgerüst. Die Übergabe erfolgt sauber von GUI -> PromptWorkspaceController -> GenerationController -> GenerationQueue -> GenerationJob. Alle veralteten RealESRGAN-Bezüge wurden erfolgreich neutralisiert und durch neutrale Engine-Platzhalter ersetzt.

