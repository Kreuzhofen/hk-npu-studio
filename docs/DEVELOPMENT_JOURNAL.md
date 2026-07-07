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

