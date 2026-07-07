# Projekt-Changelog – Snapdragon AI Studio

Alle signifikanten Änderungen und Veröffentlichungen dieses Projekts werden in diesem Dokument festgehalten. Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [2.0 Preview] – 2026-07-07 (Laufende Phoenix-Entwicklung)

### Hinzugefügt
* **Backend Discovery & Environment Detection (P-061 & P-061.1 & P-061.2):** Einführung des `BackendDiscoveryService` und der Datenklasse `DiscoveryResult` zur automatischen OS-, Python-, ONNX- und Qualcomm QNN SDK-Erkennung. Umgestaltung des Model-Inspectors in ein scrollbares Panel (`Canvas` + `Scrollbar`) zur Vermeidung von Layout-Clipping. Entfernung der doppelten "Aktiv ausgewählt"-Statusanzeige und der automatischen Workspace-Umschaltung bei Doppelklick.
* **AI Engine Pipeline Foundation & Bugfix (P-060 & P-060.1):** Einführung der Klassen `ImageGenerationPipeline` und `GenerationResult`. Anpassung aller Parameterzugriffe von `job.parameters` auf `job.session` zur Vermeidung von `AttributeError`. Integration der Inferenzpipeline in alle Backend-Adapter und Einbindung von Workflow-Abschluss-Callbacks.
* **Cross Workspace Workflow Foundation (UX-002):** Einführung der workspaceübergreifenden Workflow-Architektur. Erstellung des zentralen `WorkflowController` (Singleton) und eines transienten `WorkflowState`. Implementierung des automatischen Wechsels vom Model Manager zu AI Generate bei Doppelklick auf ein Modell. Ausbau der AI Generate-Statusleiste in eine segmentierte, dynamische Anzeige (Status, Modell, Backend, Queue). Integration von Workflow-Hooks in Galerie- und Compare-Kontextmenüs.
* **Model Manager Professional UX (UX-001):** Umwandlung der Model Manager Ansicht in ein zweispaltiges Design mit einem integrierten Selected Property Grid und einem dedizierten vertical Model Inspector für das aktive Systemmodell. Implementierung einer systemweiten Statusbar und Trennung von tabellarischer Zeilenselektion (blau) und aktivem Modellzustand (✓).
* **Active Model Selection Feedback (P-055.5):** Einführung einer klassenweiten `_active_model_id` in `ModelRepository` als Single Source of Truth. Etablierung einer „Aktiv“-Spalte im Treeview mit Haken-Symbol („✓“) sowie Doppelklick-Gestenbindung zur Aktivierung eines Modells. Bidirektionaler Parameterabgleich mit dem „AI Generate“-Workspace über `StringVar`-Traces und Ansichtsaktualisierungen.
* **Remove Model Manager Refresh Button (P-055.4):** Vollständige Entfernung des manuellen "Aktualisieren"-Buttons aus der UI. Das Repository lädt automatisch, während die interne Refresh-Funktion für künftige Watcher-Anbindungen bereitgehalten wird.
* **Model Manager UX Cleanup (P-055.3):** Entfernung des redundanten "Details anzeigen"-Buttons. Modelldetails werden nun rein eventbasiert bei Auswahl aktualisiert. Die Benutzerauswahl bleibt über Hintergrundaktualisierungen hinweg stabil.
* **Model Manager Selection Fix (P-055.2):** Behebung des Selection-Bugs im Model Manager Treeview mittels hierarchieunabhängiger dynamischer Indexsuche, Event-Binding für Live-Details und Auto-Selection.
* **Model Manager Workspace Integration (P-055.1):** Native Integration des AI Model Managers als vollwertiger Phoenix Workspace (`PhoenixModelManagerView`) mit angepasstem Treeview-Theming.
* **Model Repository & Model Manager (P-055):** Entwicklung des datengetriebenen Modellkatalogs (`resources/models/`) und der Klassen `ModelRepository`, `ModelManagerModel` und `ModelManagerController`.
* **Dynamisches Model-Rendering (P-055):** Vollständig dynamische Benutzeroberfläche des Repository-Managers (`model_manager_gui.py`) und der Modellauswahl im Prompt-Workspace, befreit von hardcodierten Modellnamen.
* **Backend-Adapter-Architektur (P-054):** Einführung der abstrakten Basisklasse `BackendAdapter` (ABC) und des `BackendManager` zur Abstraktion und Steuerung von Generierungsprozessen.
* **Stub-Inferenz-Adapter (P-054):** Implementation der vier Adapter `CPUBackendAdapter`, `QNNBackendAdapter`, `ONNXBackendAdapter` und `RemoteBackendAdapter` als erweiterbare Stubs zur Vorbereitung künftiger NPU- und CPU-Pipelines.
* **Prompt-Workspace-Details (P-054):** Erweiterung des Preview-Inspectors im Generierungs-Workspace um eine Infobox zur Anzeige von Engine, aktivem Backend, Version und Modell.
* **Generierungssitzung & GenerationController (P-052):** Implementierung der Generierungsarchitektur durch Einführung von `GenerationSessionModel` (zentraler Parameterzustand) und `GenerationController` (Validierung, Abbrechen und Einreihen von Generierungsaufträgen).
* **Workspace-Generierungsintegration (P-052):** Umleitung aller Generierungsaufrufe im `PromptWorkspaceController` über den neuen `GenerationController`. Parameter werden in der `GenerationSession` synchron gehalten.
* **Prompt Workspace Foundation (P-051):** Neuer Workspace „AI Generate“ zur Text-zu-Bild-Generierung. Bietet Eingabefelder für Prompt und Negativ-Prompt sowie Einstellregler für Seed, Schritte, CFG, Breite und Höhe und ein Modell-Dropdown.
* **MVC-Generate-Stub (P-051):** Einführung von `PromptWorkspaceModel` und `PromptWorkspaceController`. Der Generierungsknopf sammelt die Daten, loggt die Parameter im Terminal und aktualisiert den Workspace-Status.
* **Gallery → Compare-Workflow (P-050):** Vollständige Integration des Workflows. Doppelklick auf Galerie-Bilder oder das Rechtsklick-Kontextmenü („In Compare öffnen“) öffnet das Bild sauber über Controller/Adapter in der Vergleichsansicht.
* **Robuste Großbild-Vergleichsansicht (P-050):** `CompareWorkspaceController` lädt Bilder >50MP als Vorschau in max. 4096px Kantenlänge zur RAM-Schonung unter Deaktivierung des Decompression Bomb Limits, während Metadaten-Auflösungen voll erhalten bleiben.
* **Phoenix Gallery Thumbnail Grid Foundation (P-049.0B):** Erweiterung des Galerie-Workspace um ein responsives Thumbnail-Grid mit Platzhalterkarten zur Anzeige von Vorschausymbol, Dateiname, Auflösung und Format.
* **Phoenix Gallery Workspace Shell (P-049.0A):** Implementierung der leeren Workspace-Shell mit Titel, scrollbarem Inhaltsbereich und Platzhaltertext, integriert in die Phoenix-Navigation.
* **Zentrale Dateinamens-Infrastruktur (P-048.2):** Einführung der zentralen Hilfsfunktion `get_unique_filename` in [file_utils.py](file:///C:/SnapdragonAI/engine/file_utils.py) zur automatischen und dreistelligen Nummerierung (`_001`, `_002`, etc.) von Ausgabedateien bei Namenskollisionen.
* **Phoenix-GUI-Umgebung:** Einführung der modularen Seitenarchitektur unter [widgets/phoenix/workspace.py](file:///C:/SnapdragonAI/widgets/phoenix/workspace.py) zur dynamischen Verwaltung von Seiten (Views).
* **Zentraler ThemeManager:** Implementierung von [theme_manager.py](file:///C:/SnapdragonAI/engine/theme_manager.py) für einheitliches HSL-basiertes Styling und Unterstützung von Dark & Light Mode.
* **Branding-Kapselung:** Implementierung von [brand_manager.py](file:///C:/SnapdragonAI/engine/brand_manager.py) zur dynamischen Logo- und CI-Generierung zur Laufzeit.
* **Controller-Schicht:** Hinzufügen von MVC-Controllern und Models wie [CompareWorkspaceController](file:///C:/SnapdragonAI/controllers/compare_workspace_controller.py) zur Trennung von Präsentations- und Geschäftslogik.
* **RealESRGAN x4 Inferenz-Backend:** Integration der Qualcomm NPU über das QNN SDK (`qnn-net-run.exe`) mit Kachelung (Tiling) in `engine/backends/qnn_backend.py`.

### Geändert
* **Ausgabeverzeichnisschutz:** Refactoring von [gui_controller.py](file:///C:/SnapdragonAI/engine/gui_controller.py) und [realesrgan_core.py](file:///C:/SnapdragonAI/modules/realesrgan_core.py) zur Nutzung der neuen Dateinamens-Infrastruktur, um das versehentliche Überschreiben bestehender Bilder projektweit zu verhindern.
* Standardisierung der Benutzeroberfläche von klassischen, fensterbasierten Dialogen hin zu einem einheitlichen Single-Window-Design.
* Migration von Bildverarbeitungsschritten in dedizierte Module (`modules/qnn.py`, `modules/realesrgan_core.py`).

### Behoben
* **Gallery Thumbnail-Rendering nach Resize (Bugfix):** Behebung eines Problems, bei dem Thumbnail-Widgets nach Fenster-Resizes oder Spaltenwechseln als dauerhafte Platzhalter verblieben. Der `ThumbnailProvider` wurde so erweitert, dass er mehrere Callbacks für denselben pending Thumbnail-Ladevorgang registriert und nach Fertigstellung alle auslöst.
* **Verzerrter Bild-Output im RealESRGAN-Plugin (Bugfix):** Behebung eines Problems, bei dem das vom RealESRGAN-Plugin erzeugte Ausgabebild verzerrt (quadratisch gestaucht) gespeichert wurde. `_restore_target_resolution` im `QNNBackend` wurde implementiert, um das NPU-Ergebnis proportional korrekt auf `(original_width * 4, original_height * 4)` zu skalieren und das originale Seitenverhältnis wiederherzustellen.

---

## [1.5.0] – 2026-05-15 (Generation Release)

### Hinzugefügt
* **ComfyUI-Kapselung:** Vorbereitung des API-Adapters zur Kommunikation mit lokalen ComfyUI-Instanzen über Port `8188`.
* **InvokeAI-Integration:** Schnittstellen-Entwurf für externe Inferenz-Läufe mit CPU-Ausführungspfad.
* **Modellauswahl-Widget:** Erstes Dropdown zur Auswahl installierter Bildgenerierungsmodelle.
* **Prompt History:** Speicherung und Abruf zuvor genutzter Text-Prompts im GUI-Verlauf.

---

## [1.3.0] – 2026-04-10 (Dashboard Release)

### Hinzugefügt
* **Hardware-Erkennungs-Modul:** Implementierung von [hardware_manager.py](file:///C:/SnapdragonAI/engine/hardware_manager.py) zur Validierung von Prozessorarchitektur (ARM64), Windows-Version, Systemspeicher und Vorhandensein von QNN SDK-Treibern.
* **Dashboard-Hauptseite:** Grafische Darstellung des aktuellen Hardwarezustands und Schnellstart-Karten.
* **Recent Projects:** Anzeige der Historie verarbeiteter Bilder und Ausgabepfade.

---

## [1.2.0] – 2026-03-01 (AI Library Release)

### Hinzugefügt
* **Plugin-Verzeichnis:** Einführung des [plugins/](file:///C:/SnapdragonAI/plugins/) Ordners für modulare Funktionserweiterungen.
* **Modellregistry:** Einführung der [models.json](file:///C:/SnapdragonAI/models.json) zur Erfassung installierter Inferenz-Modelle mit Backend-Kompatibilität.
* **Status-Indikatoren:** Farbige Kennzeichnungen in der GUI für die Verfügbarkeit lokaler Hardware-Ressourcen.

---

## [1.1.0] – 2025-12-15 (Identity Release)

### Hinzugefügt
* **Branding-Assets:** Integration des ersten Phoenix-Branding-Designs (Splashscreen, App-Icon, Header-Grafiken) in `assets/brand/`.
* **Projektversionierung:** Erstellung von [version.py](file:///C:/SnapdragonAI/version.py) zur zentralen Festlegung von App-Name, Versionsnummer und Copyright.
* **About-Dialog:** Modal-Fenster zur Anzeige der System-Metadaten und Lizenzvereinbarungen.
