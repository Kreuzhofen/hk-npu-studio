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

## 07.07.2026 – Sprint P-061 & P-061.1 & P-061.2 & P-061.3 & P-061.4 – Backend Discovery, UX Polish, Scrollable Inspector, Table Columns Polish & Hide Global Inspector

Status: Completed

### Goals

- Implementierung des `BackendDiscoveryService` und `DiscoveryResult` zur automatischen Analyse der Host-Plattform und SDKs.
- Integration einer System-Umgebungskarte im rechten Inspector-Bereich des AI Model Managers.
- Hinzufügen von `Environment`- und `QNN`-Feldern in der Generierungs-Statusleiste im AI Generate Workspace.
- Umgestaltung des Model-Inspectors in ein scrollbares Panel (`Canvas` + `Scrollbar`) zur Vermeidung von Layout-Clipping.
- Behebung des UX-Verhaltens bei Doppelklick (keine automatische Navigation mehr) und Entfernung redundanter Statusanzeigen.
- Dynamisches Ausblenden der globalen rechten Seitenleiste (Inspector) im AI Model Manager Workspace zur Maximierung der Layoutbreite.
- Anpassung und Optimierung der Spaltenbreiten im Model Manager Treeview (Status-Spalte auf 200px, Name-Spalte auf 260px vergrößert).

### Modified / Added

- `widgets/phoenix/workspace.py` (modifiziert)
- `engine/backends/backend_discovery_service.py` (neu)
- `engine/backends/discovery_result.py` (neu)
- `engine/backends/backend_manager.py` (modifiziert)
- `controllers/model_manager_controller.py` (modifiziert)
- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `modules/model_manager_gui.py` (modifiziert)
- `widgets/phoenix/views/prompt_view.py` (modifiziert)

### Notes

Durch das dynamische Ausblenden des globalen Inspectors erhält der Model Manager die volle verfügbare App-Breite. Dadurch konnten wir die Spaltenbreiten weiter optimieren, so dass alle Modellnamen und Statusangaben vollständig sichtbar sind. Der globale Inspector wird bei allen anderen Workspaces weiterhin unverändert gerendert.

## 07.07.2026 – Sprint UX-003 – AI Model Manager Workspace Redesign

Status: Completed

### Goals

- Vollständiges Redesign der Model Manager Oberfläche zu einem sauberen zweispaltigen Layout (Tabelle links, Inspector rechts).
- Entfernung des redundanten unteren Eigenschafts-Gitterpanels.
- Konsolidierung aller Modell- und Umgebungsdetails des selektierten Modells im scrollbaren rechten Inspector.
- Integration deaktivierter Platzhalter-Buttons (Installieren, Deinstallieren, Aktualisieren, Benchmark, Ordner öffnen).
- Verfeinerung des Klick-Verhaltens (Einfacher Klick aktualisiert Inspector und Status; Doppelklick ändert das aktive Modell).

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)

### Notes

Das neue Layout verleiht dem Model Manager ein unaufgeregtes, professionelles Erscheinungsbild (Commercial Polish). Die Tabelle profitiert von der gewonnenen vertikalen Höhe, während der Inspector alle Details des gewählten Modells strukturiert zusammenfasst.

## 07.07.2026 – Sprint UX-004 – AI Generate Workspace Redesign

Status: Completed

### Goals

- Vollständiges Redesign des AI Generate Workspace zu einer professionellen AI Creative Oberfläche.
- Strukturierung der linken Parametereingabe in fünf klar getrennte Gruppen: Model, Prompt, Image Size, Sampling und Output.
- Vergrößerung der Prompt-Felder (6 Zeilen für Prompt, 3 Zeilen für Negativen Prompt).
- Einführung eines einheitlichen, scrollbaren AI Generation Inspectors rechts mit drei Bereichen: Generation Status, Generation Information und Preview-Platzhalter.
- Integration von drei deaktivierten Platzhalter-Buttons (Open in Library, Open in Review, Save As).
- Neues Sampler- und Scheduler-Dropdown für zukünftige Sampling-Konfiguration.
- Beibehaltung der segmentierten Statusleiste (Status, Modell, Backend, Environment, QNN, Queue).

### Modified / Added

- `widgets/phoenix/views/prompt_view.py` (modifiziert)

### Notes

Das neue Layout verleiht dem AI Generate Workspace eine ruhige, übersichtliche Struktur auf Commercial-Quality-Niveau. Keine Geschäftslogik wurde verändert – das Refactoring betrifft ausschließlich die UI-Schicht. Die `_on_model_changed`-Methode wurde bereinigt, um direkt auf die Slider- und Entry-Widgets zuzugreifen statt auf nicht existierende StringVar-Referenzen.

## 07.07.2026 – Sprint UX-004.3 – AI Generate No-Scroll Layout Fix

Status: Completed

### Goals

- Verdichtung des AI Generate Workspace Layouts zur vollständigen, scrollfreien Anzeige auf 1080p-Monitoren.
- Platzsparende horizontale Ausrichtung der Steuerungselemente in Model, Image Size, Sampling und Output.
- Reduzierung der Textfeldhöhen (Prompt auf 3 Zeilen, Negativer Prompt auf 1 Zeile).
- Entfernung der Scrollbar im rechten Inspector und Ersatz durch ein kompaktes, 4-spaltiges Grid.

### Modified / Added

- `widgets/phoenix/views/prompt_view.py` (modifiziert)

### Notes

Durch die Optimierung der Paddings und das Zusammenlegen von Steuerungselementen in Inline-Zeilen konnten ca. 170-190px Vertikalhöhe eingespart werden. Der Workspace wirkt dadurch aufgeräumter und ist ohne Scrollen vollständig lesbar.


## 07.07.2026 – Sprint P-070 – Local AI Model Installation Foundation

Status: Completed

### Goals

- Implementierung des neuen Service `ModelInstallService` zur Verwaltung lokaler Modell-Installationen.
- Validierung lokaler Modelldateien, Bestimmung der Modellgröße, freier Speicherplatz-Check mit Sicherheits-Puffer.
- Integration mit dem `ModelRepository` zum Persistieren von Status, Installationsflags und Dateipfaden.
- UI-Integration im Model Manager (Buttons „Installieren“, „Deinstallieren“, „Ordner öffnen“ voll funktionsfähig angebunden).
- Vorbereitung zukunftssicherer Download- und Stornierungs-Hooks für HF/API-Anbindungen.

### Modified / Added

- `engine/model_install_service.py` (neu)
- `controllers/model_manager_controller.py` (modifiziert)
- `widgets/phoenix/views/model_manager_view.py` (modifiziert)

### Notes

Der neue Dienst ermöglicht das vollständige Verwalten lokaler Modellsätze inklusive robustem Datei-Kopieren, Speicherplatzvalidierung und GUI-Rückmeldung via MessageBoxes. Im Zusammenspiel mit dem Repository werden Änderungen auf der Festplatte persistiert.

## 07.07.2026 – Sprint UX-005 – Model Manager Table Polish

Status: Completed

### Goals

- Optimierung des Tabellenlayouts im Model Manager zur Vermeidung von Textkürzungen (insbesondere in der Spalte „Kategorie“).
- Ausgleich der Spaltenbreiten und Deaktivierung der Streckung für die Spalte „Aktiv“.
- Gewährleistung eines harmonischen, lesbaren und professionellen Gesamteindrucks.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)

### Notes

Die Breiten wurden so austariert, dass Texte wie „Text-to-Image“ oder „Available for Download“ vollflächig lesbar sind. Die erste Spalte („Aktiv“) behält nun eine feste Breite von 45px und dehnt sich bei Skalierung des Programmfensters nicht weiter aus.

## 07.07.2026 – Sprint UX-005.1 – Model Manager Card Appearance Restore

Status: Completed

### Goals

- Beseitigung störender 3D-Tkinter/TTK-Standardrahmungen aus der Modell-Tabelle.
- Verfeinerung des Treeview-Stylings auf flat/borderless-Ebene, um sich nahtlos in das umgebende Phoenix-Card-Design einzufügen.
- Einführung von dynamischen Hover-Effekten (Phoenix-Akzentfarbe) für Spaltenüberschriften.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)

### Notes

Durch Setzen von `borderwidth=0` und `relief="flat"` auf der Treeview- und Heading-Klasse wird der doppelte Rahmen entfernt. Die Tabelle verschmilzt optisch mit dem Kartenhintergrund und wirkt dank der Hover-Indikatoren auf den Header-Schaltflächen hochgradig interaktiv und professionell.

## 07.07.2026 – Sprint P-071 – Backend Manager Routing Foundation

Status: Completed

### Goals

- Implementierung der Kern-Routinginfrastruktur für automatische Backend-Auswahl im `BackendManager`.
- Auswertung des bevorzugten Modell-Backends aus der JSON-Konfigurationsdatei des Repositorys.
- Realisierung eines geordneten Fallbacks: QNN (NPU) -> ONNX (Runtime) -> CPU (Stub) basierend auf der lokalen Hardware-Verfügbarkeit.
- Unterstützung von `dict` (Metadaten), `str` (Model-ID) und `None` (Standard-Auswahl) als Parameter.

### Modified / Added

- `engine/backends/backend_manager.py` (modifiziert)

### Notes

Das Routing arbeitet robust und greift auf die `is_available()` Schnittstelle der Backend-Adapter zurück. Falls ein Modell ein bevorzugtes Backend definiert und dieses auf dem Host-System lauffähig ist, wird es bevorzugt. Andernfalls wird kaskadierend nach der allgemeinen Priorität (NPU -> ONNX -> CPU) ausgewählt. Die Methode `get_best_backend` ist vollständig rückwärtskompatibel.

## 07.07.2026 – Sprint P-072 – Backend Routing in GenerationController

Status: Completed

### Goals

- Nutzung des automatischen Routings in `GenerationController.queue_generation` via `BackendManager.get_best_backend`.
- Auflösung der Modell-Metadaten aus dem `ModelRepository` anhand der in der Sitzung aktiven `model_name` (Model-ID).
- Weiterleitung des optimalen, lokal verfügbaren Backend-Adapters an die `ImageGenerationPipeline`.
- Aktive Statusleisten- und Inspector-Aktualisierungen im AI Generate Workspace, um das tatsächlich geroutete Backend anzuzeigen.
- Anreicherung des Generierungsergebnisses (`GenerationResult`) mit Routing-Metadaten.

### Modified / Added

- `controllers/generation_controller.py` (modifiziert)

### Notes

Der Generierungs-Workflow verbindet nun automatisch Systemumgebungs-Erkennungen mit Modellspezifikationen. Bei der Generierung wird das bevorzugte Backend der JSON geladen, auf Verfügbarkeit geprüft und dynamisch im System umgeschaltet. Das Ergebnis spiegelt das genutzte Backend korrekt wider. Der CPU-Stub verbleibt als voll funktionsfähiger Fallback.

## 07.07.2026 – Sprint P-072.2 – Connect QNN Availability to Backend Discovery

Status: Completed

### Goals

- Anbindung der Verfügbarkeit des `QNNBackendAdapter` an die Diagnoseergebnisse des `BackendDiscoveryService`.
- Dynamische Aktivierung des QNN-Backends (`is_available` liefert `True`), wenn `qnn_sdk_found` und `qnn_tools_found` im System als wahr erkannt wurden.
- Einführung eines Klassen-Caches (`_cached_is_available`), um wiederholte Festplatten-Scans bei UI-Refreshes zu vermeiden.
- Entfernung aller temporären `[DEBUG P-072.1]` print-Anweisungen aus `backend_manager.py`.

### Modified / Added

- `engine/backends/backend_manager.py` (modifiziert)
- `engine/backends/qnn_backend_adapter.py` (modifiziert)

### Notes

Durch die Anbindung an den Discovery-Service schaltet die Anwendung nun auf Windows-ARM64-Systemen mit installiertem Qualcomm AI Stack (HTP Driver + qnn-net-run.exe vorhanden) automatisch auf Qualcomm QNN NPU um, wenn ein Modell dieses bevorzugt. Der Klassen-Cache stellt sicher, dass die Dateisystemdiagnosen nur einmalig beim ersten Abruf durchgeführt werden, was die UI-Performance im Idle-Zustand maximiert.

## 07.07.2026 – Sprint P-073 – Model Validation 2.0

Status: Completed

### Goals

- Vertiefung und Härtung der lokalen Modellvalidierung vor der Installation im `ModelInstallService`.
- Implementierung von detaillierten Prüfungen: Dateiexistenz, Dateityp (reguläre Datei oder Ordner), Leserechte (`os.access`) sowie gültige Modell-Dateiendungen (`.onnx`, `.bin`, `.safetensors`, `.gguf`, `.json`, `.pb`, `.pt`, `.pth`).
- Rückgabe strukturierter Validierungsergebnisse (Dictionary mit `success`, `message`, `warnings`, `size_bytes`).
- Ausgeben von Dateigrößen- und Dateitypwarnungen zur Information des Nutzers.
- Vollständige Integration des neuen Validierungsformats in den Kopiervorgang (`install_model`).

### Modified / Added

- `engine/model_install_service.py` (modifiziert)

### Notes

Die Validierungslogik führt nun dedizierte Prüfungen auf erlaubte Endungen und Lesbarkeit durch, ohne zeitintensive KI-Modell-Ladevorgänge oder externe ML-Abhängigkeiten einzubringen. Durch das strukturierte Rückgabeformat erhält der Installationsdienst direkt die Dateigröße und kann Warnungen (z.B. über beigefügte Begleitdateien im Verzeichnis) an die Log-Ebene melden.

## 07.07.2026 – Sprint P-073.1 – Refresh Model Manager after Install/Uninstall

Status: Completed

### Goals

- Fehlerbehebung bei der visuellen Aktualisierung des Model Managers nach Installation/Deinstallation.
- Umstellung der Treeview-Referenzierung von Zeilenindizes auf eindeutige Element-IDs (iid über `model_id`), um willkürliche Listensortierungen bei Dateiänderungen abzufangen.
- Hinzufügen einer sichtbaren Pfad-Eigenschaft („Pfad:“) im Inspector-Panel zur Nachverfolgung der Installationen.
- Korrekte Steuerung und Deaktivierung der Schaltflächen (Installieren, Deinstallieren, Ordner öffnen) basierend auf dem Modellzustand.
- Automatischer Repository-Reload bei Workspace-Wechseln im Prompt-Workspace zur Vermeidung veralteter In-Memory-Stände.

### Modified / Added

- `widgets/phoenix/views/model_manager_view.py` (modifiziert)
- `widgets/phoenix/views/prompt_view.py` (modifiziert)

### Notes

Die UI arbeitet nun vollständig robust. Da die Treeview-Einträge die `model_id` als `iid` tragen, ist der Abruf der Modelldetails unbeeinflusst von Dateisystem- und Reihungsänderungen. Der Inspector visualisiert den absoluten Pfad des installierten Modells und alle Aktionen werden unmittelbar nach der Installation oder Deinstallation passend freigegeben oder gesperrt. Switchen in den AI-Generate-Workspace lädt die Modelldatenbank automatisch frisch von der Platte, womit die Datenbanksynchronität über alle Workspace-Ebenen hinweg sichergestellt ist.

## 07.07.2026 – Sprint P-074 – Model Loader Foundation

Status: Completed

### Goals

- Schaffung einer sicheren und performanten Schnittstelle zur Modellauflösung vor Generierungsdurchläufen.
- Bereitstellung von `ModelLoaderService` mit Funktionen zur Prüfung von Installationen, Pfadermittlungen, Dateiscans und Ladeplanerstellung.
- Unterstützung strukturierter Ladepläne mit Schrittfolgen für QNN-, ONNX- und CPU-Hardware.
- Rückgabe detaillierter Ergebnisse via `ModelResolveResult` ohne ressourcenintensive Ladevorgänge.
- Frühe Validierung des Modell-Installationszustands in `GenerationController.queue_generation()` zur Verhinderung fehlerhafter Pipeline-Durchläufe.

### Modified / Added

- `engine/model_loader_service.py` (neu)
- `controllers/generation_controller.py` (modifiziert)

### Notes

Die Modelllade-Infrastruktur nutzt das `ModelRepository` als einzige Datenquelle. Nicht installierte Modelle werden vor dem Pipeline-Start sicher abgefangen und führen zu einer sauberen und informativen Benachrichtigung des Nutzers über ein fehlerhaftes `GenerationResult` (Status "LoadError", Fehlermeldung "Model is not installed."). Der Ladeplan erlaubt eine spätere Integration der tatsächlichen Bibliotheksbindungen auf der NPU.

## 07.07.2026 – Sprint UX-006 – Navigation Preparation & Splash Size Fix

Status: Completed

### Goals

- Bereinigung der Workspace-Navigation in der Phoenix Seitenleiste zur Ausrichtung an zukünftigen Produktversionen.
- Ausblenden des "Image"-Eintrags aus der Navigations-Schaltflächenliste, ohne den eigentlichen Code oder die Quelldateien des Image-Workspaces anzutasten.
- Sicherstellung der vollen Funktionalität aller verbleibenden Seitenleisten-Links (Home, AI Generate, AI Model Manager, Gallery, Compare, Plugins, Settings).
- Behebung des überdimensionierten Splash-Screens beim Anwendungsstart durch Ersetzen der alten Vollbild-Frame-Logik.
- Reduzierung des Splash-Screens auf eine feste Desktop-Größe von 600x420 Pixeln, Zentrierung auf dem Bildschirm, Nutzung von rahmenlosem Toplevel (`overrideredirect(True)`) und Implementierung eines sanften Ausblend-Transparenzeffekts (Alpha-Fading).

### Modified / Added

- `widgets/phoenix/sidebar.py` (modifiziert)
- `widgets/startup_overlay.py` (modifiziert)

### Notes

Der Eintrag "Image" wurde in der Seitenleiste auskommentiert, bleibt aber im Code voll einsatzbereit. Der Splash-Screen arbeitet nun als eigenständiges Toplevel-Fenster anstatt als raumgreifendes Overlay-Frame auf dem Hauptfenster, was für einen erheblich professionelleren Startvorgang der Desktop-App sorgt. Durch das Alpha-Fading blendet sich das Fenster über Windows-Attribute elegant aus, ehe es sich schließt.

## 08.07.2026 – Sprint P-076 – Local Image Generator Adapter Foundation

Status: Completed

### Goals

- Vorbereitung der ersten echten lokalen Bildgenerierung über einen austauschbaren Generator-Adapter.
- Implementierung von `LocalImageGeneratorAdapter` zur Kapselung lokaler Inferenzschritte (Stub-Generierung eines 1x1 PNG-Dummybildes für die GUI-Galerie).
- Einführung von `GenerationExecutor` zur Validierung des Modellinstallationszustands und Dispatching an die Adapter-Stufe.
- Integration von `GenerationResponse` (Unterklasse von `GenerationResult`) zur Gewährleistung abwärtskompatibler Rückgabewerte.
- Einführung strukturierter Protokolle zur Visualisierung des Inferenz-Flusses: `Executor` -> `Adapter` -> `Result`.
- Sicherer Abbruch bei fehlender Modellinstallation anstelle eines Anwendungsabsturzes.

### Modified / Added

- `engine/local_image_generator_adapter.py` (neu)
- `engine/generation_executor.py` (neu)
- `engine/generation_response.py` (neu)
- `controllers/generation_pipeline.py` (modifiziert)

### Notes

Die Architektur ist nun optimal auf künftige physische Inferenzpakete (Qualcomm QNN NPU, ONNX Runtime, CPU etc.) vorbereitet. Der Inferenzlauf erzeugt ein echtes Mini-PNG in `output/`, wodurch die GUI-Vorschau und die Galerie das Resultat ohne Fehlverhalten laden und anzeigen können. Der Fluss ist durchgehend protokolliert.

## 08.07.2026 – Sprints P-077, P-078 & P-079 – Decoupled Inference Backend & Diagnostics Preview

Status: Completed

### Goals

- Bereitstellung einer sauberen Backend-Abstraktion zur Entkopplung lokaler Generatoren von konkreten Laufzeitumgebungen.
- Erstellung der Schnittstellen-Basisklasse `InferenceBackend` zur Definition einheitlicher Generierungs-Aufrufe.
- Erstellung der konkreten Klasse `StubImageBackend` zur Kapselung des Pillow-basierten Diagnosebild-Generierungsschritts.
- Härtung der PNG-Erstellung über Pillow (Behebung beschädigter Dateiformate) zur vollständigen Kompatibilität mit Windows Fotos und Galerie-Loadern.
- Erzeugung eines optisch ansprechenden Phoenix-Vorschaubilds mit Markennamen, Modellname, aktivem Hardware-Backend und gekürztem Prompt.
- Speicherung aller Parameterwerte in einer JSON-Sidecar-Metadatendatei neben dem PNG-Asset.
- Umleitung des `LocalImageGeneratorAdapter` zur Inferenz-Delegation an das Backend.

### Modified / Added

- `engine/inference_backend.py` (neu)
- `engine/stub_image_backend.py` (neu)
- `engine/local_image_generator_adapter.py` (modifiziert)
- `engine/generation_response.py` (modifiziert)

### Notes

Die Kette lautet nun: `GenerationExecutor` -> `LocalImageGeneratorAdapter` -> `InferenceBackend` -> `StubImageBackend`. Dadurch kann der Stub-Generator später ohne Änderungen am Adapter oder Executor gegen echte NPU-Bibliotheken (Qualcomm QNN, ONNX Runtime) ausgetauscht werden. Die Stabilität der PNG-Dateien wurde erfolgreich unter Windows Photos und in der Gallery verifiziert.

## 08.07.2026 – Sprint P-080 – Inference Backend Plugin Framework

Status: Completed

### Goals

- Einführung einer erweiterbaren Fabrikmethode (Factory Pattern) für lokale Inferenz-Backends.
- Erstellung der Klasse `InferenceBackendFactory` zur Registrierung und Auflösung von Backend-Typen anhand ihres Anzeigenamens.
- Erstellung des Placeholders `OnnxImageBackend` zur Vorbereitung künftiger ONNX Runtime-Einbindungen.
- Registrierung des `StubImageBackend` für CPU- und NPU-Stub-Modi und des `OnnxImageBackend` für ONNX-Stub-Modi.
- Strikte Kapselung: Der `LocalImageGeneratorAdapter` instanziiert keine Backends mehr direkt, sondern holt sie ausschließlich über `InferenceBackendFactory.get_backend(name)`.
- Vereinfachung der Schnittstelle auf die klare Signatur: `backend.generate(job)`.

### Modified / Added

- `engine/inference_backend_factory.py` (neu)
- `engine/onnx_image_backend.py` (neu)
- `engine/local_image_generator_adapter.py` (modifiziert)
- `engine/inference_backend.py` (modifiziert)
- `engine/stub_image_backend.py` (modifiziert)

### Notes

Die Inferenzsteuerung ist durch die Factory vollkommen flexibel und erweiterbar. Plugins können einfach registriert und zur Laufzeit dynamisch über den Backend-Namen bezogen werden, ohne dass die Pipeline oder der Adapter angepasst werden müssen. Die vereinfachte Signatur `generate(job)` reduziert Kopplungen weiter.

## 08.07.2026 – Sprint P-081 – Model Runtime Integration

Status: Completed

### Goals

- Verbindung des Modell-Ladevorgangs mit der Inferenz-Factory.
- Übergabe des ausgewählten Modells über den `ModelLoaderService` an den `GenerationExecutor`.
- Konstruktion des `RuntimeModel` im Executor basierend auf Modellauflösung, Gewichtsdateien und Ladeplan.
- Dynamische Durchleitung des `RuntimeModel` an die `InferenceBackendFactory` und die Backend-Instanzen.
- Beseitigung hartcodierter Modellnamen in Inferenz-Klassen.
- Erweiterung des Ablauf-Logs um die Felder: `Selected Model`, `Runtime Model` und `Backend`.

### Modified / Added

- `engine/runtime_model.py` (neu)
- `engine/generation_executor.py` (modifiziert)
- `engine/inference_backend_factory.py` (modifiziert)
- `engine/local_image_generator_adapter.py` (modifiziert)
- `engine/stub_image_backend.py` (modifiziert)
- `engine/onnx_image_backend.py` (modifiziert)

### Notes

Durch die Integration des `RuntimeModel` sind die Backends vollständig entkoppelt von hartcodierten Metadaten wie dem Modellnamen. Sie lesen die ID, Dateipfade und Ladepläne dynamisch zur Laufzeit aus. Die Protokollierung zeigt den vollständigen Modell- und Hardwareauflösungsfluss transparent im Log auf.

## 08.07.2026 – Sprint P-081 – Live Preview Integration

Status: Completed

### Goals

- Automatische Anzeige des erzeugten PNG-Bildes in der GUI nach erfolgreicher Inferenz.
- Dynamische Anpassung des Vorschau-Labels des AI Generate Workspace Inspectors unter Verwendung von Pillow.
- Entfernen des statischen Textplatzhalters *"No image generated"*, sobald ein Bild geladen wurde.
- Aktivierung der interaktiven Buttons *"Open in Library"*, *"Open in Review"* und *"Save As"*, wenn ein valides Ausgabebild vorliegt.
- Bindung der Schaltflächenfunktionen an OS-Aktionen (Explorer öffnen, Bild in Bildbetrachter öffnen, ask-save-as-Dialog).
- Ausschließliche Verwendung der `GenerationResponse` als Datenquelle.

### Modified / Added

- `widgets/phoenix/views/prompt_view.py` (modifiziert)
- `controllers/prompt_workspace_controller.py` (modifiziert)

### Notes

Die Anwendung aktualisiert nun nach jedem Generierungslauf in Echtzeit das Vorschau-Bild und schaltet die dazugehörigen System-Schaltflächen frei. Wenn keine Datei vorhanden ist oder die Generierung fehlschlägt, wird der Platzhalter wiederhergestellt und die Schaltflächen werden deaktiviert. Alle Tests verliefen stabil.

## 08.07.2026 – Sprint P-082 – Generation Parameter Contract

Status: Completed

### Goals

- Etablierung eines einheitlichen Parametervertrags für alle 12 Generierungsparameter.
- Durchgängiges Transportieren der Parameter von der GUI (`prompt_view.py`) über den Workspace-Controller, den GenerationController, GenerationJob bis hin zu den Inferenz-Backends.
- Zeichnen erweiterter Parameter (`Seed`, `Steps`, `CFG`) auf der Diagnosekarte in `StubImageBackend` und `OnnxImageBackend`.
- Vollständige Aufzählung aller 12 Parameter (inkl. `negative_prompt`, `sampler`, `scheduler`, `batch_count`) im Sidecar-JSON des Ausgabeassets.

### Modified / Added

- `widgets/phoenix/views/prompt_view.py` (modifiziert)
- `controllers/prompt_workspace_controller.py` (modifiziert)
- `controllers/prompt_workspace_model.py` (modifiziert)
- `engine/stub_image_backend.py` (modifiziert)
- `engine/onnx_image_backend.py` (modifiziert)

### Notes

Die Parameter-Durchreichung ist jetzt vollständig standardisiert. Alle Parameter werden lückenlos im Asset-Ausgabeordner dokumentiert (sowohl visuell im PNG als auch strukturell im JSON). Alle Unit- und Integrationstests wurden aktualisiert und laufen erfolgreich durch.

## 08.07.2026 – Sprint P-085 – ONNX Runtime Readiness

Status: Completed

### Goals

- Erweiterung des `OnnxImageBackend` zur Prüfung der Inferenz-Bereitschaft auf Basis der `onnxruntime`.
- Automatisches Scannen des Modell-Paketverzeichnisses nach `.onnx`-Dateien.
- Überprüfung der Existenz und Größe gefundener `.onnx`-Dateien zur Validierung der prinzipiellen Ladbarkeit, ohne bereits eine `InferenceSession` zu instanziieren (wie im Sprint gefordert).
- Robuste Fehlerbehandlung: Bei Fehlen der Runtime oder der `.onnx`-Datei wird eine ordentliche `GenerationResponse` mit `success=False` und Status `unavailable` zurückgeliefert, ohne dass es zu Abstürzen kommt.

### Modified / Added

- `engine/onnx_image_backend.py` (modifiziert)

### Notes

Die Inferenz-Bereitschaftsprüfung ist nun strukturell vorbereitet und voll integriert. Falls `onnxruntime` fehlt oder kein Modellpaket bereitgestellt wird, fängt das Backend dies ohne Absturz ab und meldet den entsprechenden Bereitschaftsstatus, ohne eine `InferenceSession` zu erzwingen. Der CPU/NPU-Stub-Workflow bleibt voll lauffähig. Alle Funktionstests inklusive simulierter (gemockter) ONNX-Laufzeitumgebungen verliefen erfolgreich.

## 08.07.2026 – Sprint P-088 – First ONNX Runtime Detection

Status: Completed

### Goals

- Ausbau der Laufzeiterkennung von `onnxruntime`.
- Auslesen und Protokollieren der Bibliotheksversion sowie der verfügbaren Execution Provider.
- Sicherstellung, dass `CPUExecutionProvider` erkannt wird.
- Nichtvorhandensein von `QNNExecutionProvider` (Qualcomm QNN NPU) als unkritische Warnung/Info behandeln, um die Bereitschaftsprüfung ohne Fehler abzuschließen.
- Stub-Generierung (PNG + JSON) bleibt unberührt lauffähig.

### Modified / Added

- `engine/onnx_image_backend.py` (modifiziert)

### Notes

Das ONNX-Backend meldet nun detailliert alle verfügbaren Execution Provider. Falls der QNN Execution Provider auf dem System fehlt (weil kein QNN SDK installiert ist), wird dies ordnungsgemäß als Info/Warnung protokolliert und führt nicht zu einem Systemfehler. Alle Testfälle laufen erfolgreich.

## 08.07.2026 – Sprint P-089 – First ONNX Inference Session

Status: Completed

### Goals

- Erzeugung der ersten echten `onnxruntime.InferenceSession`.
- Laden von `.onnx`-Modellen bei Vorhandensein im Modellverzeichnis.
- Auslesen und Protokollieren der Input- und Output-Namen direkt aus dem Modell-Graph.
- Saubere Freigabe der System-Ressourcen (`del session`) nach der Modell-Initialisierung.
- Strukturierte Fehlerbehandlung bei Nichtvorhandensein der Runtime oder fehlerhaften Modellen.

### Modified / Added

- `engine/onnx_image_backend.py` (modifiziert)

### Notes

Das ONNX-Backend initialisiert nun erfolgreich die `InferenceSession` zur Vorbereitung des realen Inferenzpfades. Es extrahiert Metadaten (Eingangs- und Ausgangsvariablen) zur Verifizierung der Graphstruktur. Nach dem Ladeschritt wird die Session wieder freigegeben. Fehlerhafte protobuf-Dateien werden ordnungsgemäß abgefangen, geloggt und mit `success=False` gemeldet. Alle Funktionstests laufen erfolgreich.

## 08.07.2026 – Sprint P-091 – AI Model Capability System

Status: Completed

### Goals

- Einführung eines modellunabhängigen Capability-Systems zur Vermeidung harter Codierungen im Inferenzfluss.
- Repräsentation der Fähigkeiten über eine dedizierte Python-Klasse `ModelCapabilities`.
- Vorbereitung der strukturierten Fähigkeiten für: `txt2img`, `img2img`, `inpainting`, `outpainting`, `LoRA`, `ControlNet`, `Image-to-Video`, `Batch Generation`, `ONNX Runtime` und `QNN Runtime`.
- Erweiterung der Schema-Validierung im `ModelRepository` und Aktualisierung aller 7 Modell-JSON-Metadatendateien (`flux_dev`, `sdxl_base`, `sdxl_refiner`, `sd35_large`, `cogvideox`, `ltx_video`, `wan22`).

### Modified / Added

- `controllers/model_repository.py` (modifiziert)
- `resources/models/*.json` (alle 7 modifiziert)

### Notes

Das neue Capability-System ist komplett datengesteuert. Jedes Modell beschreibt seine individuellen Fähigkeiten in seiner zugeordneten JSON-Datei. Das `ModelRepository` validiert diese Struktur und stellt die Fähigkeiten als strukturiertes `ModelCapabilities`-Objekt bereit. Alle Regressionstests und Kompilierungsprüfungen wurden erfolgreich absolviert.
