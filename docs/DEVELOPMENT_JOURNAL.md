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

## 07.07.2026 – Sprint P-054 – AI Backend Adapter Architecture Foundation

Status: Completed

### Goals

- Entwicklung einer Backend-Abstraktionsschicht (ABC `BackendAdapter`).
- Erstellung eines `BackendManager` zur Registrierung und Aktivierung von Adaptern.
- Implementation von vier Adaptern (CPU, QNN, ONNX, Remote) als Stubs mit Kommentaren für FLUX/SDXL.
- Integration der Backend-Ausführung im `GenerationController`.
- Erweiterung des Inspectors im Prompt Workspace zur Anzeige der Engine, des aktiven Modells und des aktuellen Status.

### Modified / Added

- `engine/backends/backend_adapter.py` (neu)
- `engine/backends/backend_manager.py` (neu)
- `engine/backends/cpu_backend_adapter.py` (neu)
- `engine/backends/qnn_backend_adapter.py` (neu)
- `engine/backends/onnx_backend_adapter.py` (neu)
- `engine/backends/remote_backend_adapter.py` (neu)
- `controllers/generation_controller.py` (modifiziert)
- `widgets/phoenix/views/prompt_view.py` (modifiziert)

### Notes

Das Backend-Abstraktionsgerüst ist nun vollständig implementiert und mit dem UI-Inspector verdrahtet. Der `GenerationController` leitet die eingereihten Jobs direkt an das im `BackendManager` ausgewählte aktive Backend (standardmäßig `CPU (Stub)`) weiter.

## 07.07.2026 – Sprint P-055 – AI Model Repository & Model Manager Foundation

Status: Completed

### Goals

- Etablierung des Model Repositories unter `resources/models/` mit JSON-Metadaten.
- Implementierung der Klasse `ModelRepository` zum Laden und Validieren von JSON-Modelldaten.
- Erstellung von `ModelManagerModel` und `ModelManagerController` (MVC).
- Dynamischer Aufbau des Model Repository Managers (`model_manager_gui.py`) aus der Datenquelle ohne Hardcodierungen.
- Dynamische Anpassung des OptionMenus für Modelle im Prompt-Workspace.
- Vorbereitung von Kommentaren für Downloads, Installationen und Signaturen.

### Modified / Added

- `resources/models/flux_dev.json` (neu)
- `resources/models/sdxl_base.json` (neu)
- `resources/models/sdxl_refiner.json` (neu)
- `resources/models/sd35_large.json` (neu)
- `resources/models/wan22.json` (neu)
- `resources/models/cogvideox.json` (neu)
- `resources/models/ltx_video.json` (neu)
- `resources/backends/README.md` (neu)
- `resources/capabilities/README.md` (neu)
- `resources/licenses/README.md` (neu)
- `controllers/model_repository.py` (neu)
- `controllers/model_manager_model.py` (neu)
- `controllers/model_manager_controller.py` (neu)
- `controllers/prompt_workspace_controller.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)

### Notes

Die gesamte Modellauflistung und Parameteranzeige arbeitet nun rein datengetrieben. Es gibt keinerlei Modellnamen mehr hartcodiert im UI-Code. Wenn künftig neue JSON-Metadaten im Repository-Ordner abgelegt werden, werden diese sofort automatisch in der Suite erkannt.

## 07.07.2026 – Sprint P-055.1 – AI Model Manager Workspace Integration

Status: Completed

### Goals

- Integration des AI Model Managers als vollwertigen Phoenix Workspace (kein Popup/Dialog mehr).
- Hinzufügen des Navigationspunktes "AI Model Manager" in die Phoenix-Seitenleiste (Sidebar).
- Implementierung der View `PhoenixModelManagerView` mitsamt `PHOENIX_THEME`-konformem Styling und anpassbarem Treeview-Design.
- Einhalten des strikten MVC-Musters und Beibehaltung der bestehenden Datenstrukturen.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (neu)
- `widgets/phoenix/workspace.py` (modifiziert)
- `widgets/phoenix/sidebar.py` (modifiziert)

### Notes

Der Model Manager ist nun voll in die Anwendungsstruktur als Workspace integriert. Die Navigation und das Theming greifen perfekt ineinander, während die Datenanbindung über das `ModelRepository` unberührt und stabil bleibt.

## 07.07.2026 – Sprint P-055.2 – Model Manager Selection Fix

Status: Completed

### Goals

- Beheben des Auswahlfehlers im Treeview des Model Managers.
- Implementierung einer robusten, dynamischen Zeilenindexsuche via `tree.index()`.
- Hinzufügen von automatischen Updates des Detailbereichs bei Klick/Selektion (`<<TreeviewSelect>>`) und Doppelklick.
- Automatisches Auswählen des ersten Tabelleneintrags beim ersten Laden.
- Löschen/Bereinigen ungenutzter Test-Modell-JSONs im Repository.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)

### Notes

Durch den Verzicht auf feste, eventuell inkompatible iid-Konvertierungen und den Einsatz von `tree.index()` ist die Zeilenauflösung 100% stabil. Die Selektion bleibt auch bei Fokusverlust sichtbar, und durch Event-Bindings werden Details jetzt komfortabel sofort bei Klick auf eine Reihe geladen.

## 07.07.2026 – Sprint P-055.3 – Model Manager Selection Persistence Fix

Status: Completed

### Goals

- Beheben des automatischen Resets der Zeilenauswahl im Model Manager Workspace.
- Speicherung und Wiederherstellung der `selected_model_id` über Refresh-Zyklen.
- Schutz des Detailbereichs vor unerwünschtem Überschreiben durch Statusberichte während der Hintergrundaktualisierung.
- Sicherstellen einer stabilen Interaktion für Klicks, Doppelklicks und Detail-Schaltflächen.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)

### Notes

Die Ursache lag im globalen 500ms-Hintergrund-Workspace-Refresh (`_refresh_views`), der bei jedem Durchlauf die Treeview-Elemente neu aufbaute und die Benutzerauswahl verwarf. Durch das Caching der ausgewählten Modell-ID und die gezielte Wiederherstellung nach dem Neuaufbau bleibt die Selektion nun dauerhaft und stabil auf der vom Benutzer gewünschten Zeile.

## 07.07.2026 – Sprint P-055.3 – Model Manager UX Cleanup

Status: Completed

### Goals

- Entfernung des redundanten "Details anzeigen"-Buttons aus der Workspace-View und der Legacy-View.
- Sicherstellen, dass die Details rein ereignisbasiert geladen werden.
- Stabilität der Selektion und Vermeidung des automatischen Resets auf Zeile 0 während der periodischen Widget-Aktualisierung.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)

### Notes

Der Button wurde aus beiden Ansichten entfernt, da die Auslesung vollautomatisch und live beim Selektions-Event (`<<TreeviewSelect>>`) erfolgt. Die Auto-Selektion wurde so korrigiert, dass sie nur initial oder beim Fehlen einer gültigen Auswahl eingreift und die Benutzerauswahl ansonsten absolut stabil bestehen bleibt.

## 07.07.2026 – Sprint P-055.4 – Remove Model Manager Refresh Button

Status: Completed

### Goals

- Vollständige Entfernung des manuellen "Aktualisieren"-Buttons aus der Workspace-View und der Legacy-View.
- Sicherstellen, dass die Modellliste automatisch beim Laden oder Initialisieren geladen wird.
- Beibehalten der internen Refresh-Logik zur Vorbereitung automatischer Dateisystemüberwachungen.
- Erhalt der stabilen Selektion und Interaktion.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)

### Notes

Der "Aktualisieren"-Button wurde aus den Oberflächen entfernt, da die Suite durch den periodischen Refresh-Loop (500ms) ohnehin vollautomatisch im Hintergrund aktualisiert wird und die Benutzerauswahl dabei stabil bleibt. Die Benutzeroberfläche des Model Managers ist nun vollständig buttonfrei und arbeitet rein interaktiv.

## 07.07.2026 – Sprint P-055.5 – Active Model Selection Feedback

Status: Completed

### Goals

- Einführung einer Single Source of Truth (`_active_model_id` / Klasse `ModelRepository`) zur Verwaltung des aktiven Modells.
- Visuelles Feedback über eine Tabellenspalte "Aktiv" mit einem Haken-Symbol ("✓") für das aktive Modell.
- Doppelklick-Gestenbindung zur Aktivierung des ausgewählten Modells.
- Automatischer Parameterabgleich im Workspace "AI Generate" und Aktualisierung der Modellauswahl-Dropdowns.

### Modified / Added

- `controllers/model_repository.py` (modifiziert)
- `controllers/model_manager_controller.py` (modifiziert)
- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modmodified)
- `widgets/phoenix/views/prompt_view.py` (modifiziert)

### Notes

Durch die klassenübergreifende Speicherung der `_active_model_id` in `ModelRepository` konnte eine saubere Single Source of Truth etabliert werden. Die Synchronisation zwischen Model Manager und AI Generate läuft vollautomatisch über die bidirektional verkabelten `refresh()`-Methoden und den `StringVar`-Trace.

## 07.07.2026 – Sprint UX-001 – AI Model Manager Professional UX

Status: Completed

### Goals

- Etablierung eines professionellen zweispaltigen Layouts (Links: Liste & Properties; Rechts: Model Inspector).
- Visuelle und logische Trennung der temporären Tabellenauswahl (blau) von der systemweit aktiven Modell-Auswahl (✓).
- Implementierung eines Property Grids aus formatierten Label-Wert-Paaren anstelle von Debug-Textausgaben.
- Einführung einer Statusleiste am unteren Bildschirmrand für System-Feedback wie "Aktives Modell geändert".
- Hinzufügen von Code-Kommentaren und Hooks für künftige automatische Navigation nach Doppelklick.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)

### Notes

Mit diesem Sprint wurde die Benutzeroberfläche des Model Managers auf kommerzielles Desktop-Niveau (Commercial Quality) gehoben. Alle Dumps und JSON-Fragmente wurden durch ein sauberes, strukturiertes Grid-System ersetzt, das dem Anwender klare Informationen bietet, ohne ihn zu überfordern.

## 07.07.2026 – Sprint UX-002 – Cross Workspace Workflow Foundation

Status: Completed

### Goals

- Einführung eines zentralen `WorkflowController` (Singleton) und eines transienten `WorkflowState` zur workspaceübergreifenden Koordination.
- Implementierung der automatischen Workspace-Umschaltung zu AI Generate nach Doppelklick im Model Manager.
- Erweiterung des AI Generate Statusbereichs in eine segmentierte Statusleiste (Status, Modell, Backend, Queue) ohne Hartcodierungen.
- Integration von Vorbereitungs-Hooks (Kontextmenüs) im Compare- und Gallery-Workspace.

### Modified / Added

- `controllers/workflow_controller.py` (neu)
- `gui/controllers/ui_builder.py` (modifiziert)
- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)
- `widgets/phoenix/views/prompt_view.py` (modifiziert)
- `widgets/phoenix/gallery/thumbnail_area.py` (modifiziert)
- `widgets/phoenix/views/compare_view.py` (modifiziert)

### Notes

Die Anwendung verhält sich nun wie eine integrierte Suite. Durch den `WorkflowController` entfällt die direkte View-zu-View-Kopplung, und Aktionen in einem Workspace (wie das Auswählen eines Modells) steuern den Anwender direkt und nahtlos zum nächsten logischen Workflow-Schritt.

## 07.07.2026 – Sprint P-060 & P-060.1 – AI Engine Pipeline Foundation & Bugfix

Status: Completed

### Goals

- Einführung der Standardklassen `ImageGenerationPipeline` und `GenerationResult` zur Vereinheitlichung der Inferenz.
- Integration der `ImageGenerationPipeline` in den `GenerationController`.
- Behebung des AttributeErrors durch Anpassung aller Parameterzugriffe von `job.parameters` auf `job.session`.
- Robustes Auslesen des Modells über `job.session.model_name` auch im Fehlerfall.

### Modified / Added

- `controllers/generation_pipeline.py` (neu)
- `controllers/generation_result.py` (neu)
- `controllers/generation_controller.py` (modifiziert)
- `controllers/prompt_workspace_controller.py` (modifiziert)
- `engine/backends/backend_adapter.py` (modifiziert)
- `engine/backends/cpu_backend_adapter.py` (modifiziert)
- `engine/backends/onnx_backend_adapter.py` (modifiziert)
- `engine/backends/qnn_backend_adapter.py` (modifiziert)
- `engine/backends/remote_backend_adapter.py` (modifiziert)

### Notes

Durch die saubere Schichten-Trennung über die `ImageGenerationPipeline` und das `GenerationResult` sind wir bereit für die physische NPU-Integration. Die Parameter-Zugriffe wurden vollumfänglich von dem redundanten `parameters`-Entwurf auf die native `session`-Eigenschaft umgestellt.

## 07.07.2026 – Sprint P-061 – Backend Discovery & Environment Detection

Status: Completed

### Goals

- Implementierung des `BackendDiscoveryService` und `DiscoveryResult` zur automatischen Analyse der Host-Plattform und SDKs.
- Verknüpfung des Discovery Service mit dem `BackendManager` und Exponierung via `ModelManagerController`.
- Integration einer System-Umgebungskarte im rechten Inspector-Bereich des AI Model Managers.
- Hinzufügen von `Environment`- und `QNN`-Feldern in der Generierungs-Statusleiste im AI Generate Workspace.

### Modified / Added

- `engine/backends/backend_discovery_service.py` (neu)
- `engine/backends/discovery_result.py` (neu)
- `engine/backends/backend_manager.py` (modifiziert)
- `controllers/model_manager_controller.py` (modifiziert)
- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)
- `widgets/phoenix/views/prompt_view.py` (modifiziert)

### Notes

Der `BackendDiscoveryService` führt eine saubere, nicht-blockierende Erkennung der Systemparameter durch. Er scannt Windows ARM64, Python-Versionen, das Vorhandensein von ONNX Runtime und das Qualcomm QNN SDK (einschließlich `qnn-net-run.exe`), ohne externe SDK-Runtimes direkt laden zu müssen.


