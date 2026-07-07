# Projektstatus – Snapdragon AI Studio

**Stand:** 07.07.2026
**Zweig:** `feature/phoenix-rebuild`
**Zielplattform:** Windows 11 ARM64 (Qualcomm Snapdragon X NPU via QNN)

---

## 1. Aktueller Status & Letzte Änderungen

Am **07.07.2026** wurden folgende Sprints abgeschlossen:

* **Sprint UX-001 (AI Model Manager Professional UX):**
  * **Professional Layout:** Umwandlung des Model Managers in ein strukturiertes zweispaltiges Design (Links: Liste + Property Grid für die getroffene Auswahl; Rechts: Vertikaler Model Inspector für das aktuell aktive System-Modell).
  * **Auswahl- vs. Aktivitäts-Zustand:** Trennung der temporären Tabellenauswahl (blaue Zeile) von der systemweit aktiven Generierungsmodell-Auswahl (✓-Haken in der ersten Spalte).
  * **Status-Feedback & Navigation:** Etablierung einer Statusleiste am unteren Bildschirmrand, die Änderungen wie „Aktives Modell geändert: <Modellname>“ anzeigt.
  * **Property View:** Kompletter Verzicht auf Debug-Textfelder oder JSON-Dumps. Alle Modell-Metadaten werden übersichtlich formatiert in strukturierten Label-Wert-Paaren ausgegeben.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py)

* **Sprint P-055.5 (Active Model Selection Feedback):**
  * **Zentraler Auswahlstatus:** Einführung einer Single Source of Truth (`_active_model_id`) als klassenweites Attribut in `ModelRepository`, inklusive Standard-Fallback auf das erste geladene Modell.
  * **Visuelles Feedback:** Hinzufügen einer Spalte „Aktiv“ an erster Stelle der Modellliste. Das aktuell aktive Modell wird mit einem Haken-Symbol („✓“) markiert.
  * **Doppelklick-Aktivierung:** Doppelklicken auf eine Tabellenzeile setzt das Modell als aktiv, erneuert die Tabellenhaken und zeigt die Status-Bestätigung: „*** Aktives Modell: <name> ***“ an.
  * **Nahtlose AI Generate Synchronisation:** Der Workspace „AI Generate“ (`prompt_view.py`) synchronisiert seine Dropdown-Modellauswahl (`model_var`) und die zugrundeliegenden Inferenzparameter automatisch in beide Richtungen über die Single Source of Truth.
  * **Dateien:** [model_repository.py](file:///C:/SnapdragonAI/controllers/model_repository.py), [model_manager_controller.py](file:///C:/SnapdragonAI/controllers/model_manager_controller.py), [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint P-055.4 (Remove Model Manager Refresh Button):**
  * **Redundanter Refresh-Button entfernt:** Vollständige Entfernung des manuellen "Aktualisieren"-Buttons aus der Workspace-View und dem Legacy-Dialog für eine modernere, buttonfreie Interaktion.
  * **Automatisches Laden:** Die Modellliste lädt sich beim Öffnen des Workspaces vollautomatisch aus dem Repository. Die interne Refresh-Logik bleibt erhalten, um über künftige Dateisystemüberwachungen angestoßen zu werden.
  * **Stabile Selektion:** Die Benutzerauswahl bleibt permanent stabil und springt nicht zurück.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py)

* **Sprint P-055.3 (Model Manager UX Cleanup):**
  * **UX-Bereinigung:** Der redundante Button "Details anzeigen" wurde aus der Workspace-View und dem Legacy-Dialog vollständig entfernt, da die Details ohnehin live beim Zeilenklick angezeigt werden.
  * **Optimierte Selektions-Logik:** Sicherstellung, dass das automatische Auswählen des ersten Modelleintrags nur initial aufgerufen wird und die Benutzerauswahl danach über alle Refresh-Zyklen (500ms Loop) hinweg stabil bleibt.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py)

* **Sprint P-055.3 (Model Manager Selection Persistence Fix):**
  * **Behebung des Auswahl-Resets:** Speichern des `selected_model_id`-Status vor jedem Refresh, um die Zeilenauswahl nach dem Neuaufbau der Tabelle im 500ms-Loop stabil wiederherzustellen.
  * **Erhalts des Detailbereichs:** Verhindern, dass die Modellbeschreibung bei jedem automatischen Refresh gelöscht und durch die Standardsumme ersetzt wird, sofern ein Element aktiv ausgewählt ist.
  * **Unterbrechungsfreie Interaktion:** Sowohl Klicks als auch der "Details anzeigen"-Button und Doppelklicks lesen nun den persistenten Auswahlstatus aus, ohne dass die Selektion zurückspringt.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py)

* **Sprint P-055.2 (Model Manager Selection Fix):**
  * **Fehlerursache behoben:** Behebung des Auswahlfehlers im Treeview, der durch fehlerhafte iid-Konvertierungen und Fokusverluste beim Klicken auf Details verursacht wurde.
  * **Dynamische Indexsuche:** Umstellung des Modellauslesens auf das native, hierarchieunabhängige `tree.index()`-Verfahren zur sicheren Ermittlung der selektierten Reihe.
  * **Live-Details & Interaktion:** Hinzufügen von automatischen Selektions-Event-Bindings (`<<TreeviewSelect>>`) zur Echtzeit-Anzeige der Details sowie Doppelklick-Bindings (`<Double-1>`).
  * **Auto-Select auf Start:** Der Model Manager wählt beim Laden oder Aktualisieren der Seite automatisch das erste Modell in der Tabelle aus.
  * **Aufräumarbeiten:** Verifikation, dass keine ungenutzten Testdateien (wie `custom_test_model.json`) im Repository verbleiben.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py)

* **Sprint P-055.1 (AI Model Manager Workspace Integration):**
  * **Workspace-Integration:** Umwandlung und Registrierung des AI Model Managers als nativer Phoenix Workspace. Der Umschalt- und Anzeigemechanismus ist voll in den `WorkspaceManager` integriert.
  * **Sidebar-Navigation:** Hinzufügen des Menüpunktes "AI Model Manager" in der Sidebar unterhalb von "AI Generate" und oberhalb von "Image".
  * **UI-Styling & Theme-Parität:** Implementierung von `PhoenixModelManagerView` unter Verwendung von `PHOENIX_THEME`. Die Darstellung der Modellliste verwendet ein angepasstes Treeview-Design, das HSL Dark- und Light-Theming unterstützt.
  * **Erhalt des MVC-Musters:** Die Modell-Datenzugriffe laufen weiterhin unverändert über `ModelManagerController` und `ModelRepository`, ohne Eingriffe in die Datenlogik selbst.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [workspace.py](file:///C:/SnapdragonAI/widgets/phoenix/workspace.py), [sidebar.py](file:///C:/SnapdragonAI/widgets/phoenix/sidebar.py)

* **Sprint P-055 (AI Model Repository & Model Manager Foundation):**
  * **Modell-Repository:** Erstellung einer datengetriebenen Modellstruktur unter `resources/models/` mit JSON-Metadatendokumenten für `flux_dev.json`, `sdxl_base.json`, `sdxl_refiner.json`, `sd35_large.json`, `wan22.json`, `cogvideox.json` und `ltx_video.json`.
  * **ModelRepository-Klasse:** Einführung von `ModelRepository` zum automatischen Einlesen, Validieren und Aktualisieren von JSON-Modellmetadaten von der Festplatte.
  * **ModelManagerModel & Controller:** Implementierung von `ModelManagerModel` (nutzt ModelRepository als Single Source of Truth) und `ModelManagerController` (kommuniziert mit ModelRepository und BackendManager).
  * **Dynamisches UI-Alignment:** Der Model Repository Manager (`model_manager_gui.py`) baut die Modellliste und Detailbeschreibungen vollständig dynamisch aus den Repository-Dateien auf, ohne hardcodierte Modellnamen. Zudem lädt der Prompt-Workspace (`prompt_view.py` über `PromptWorkspaceController`) die Liste der verfügbaren Modelle ebenfalls dynamisch aus der Metadatendatenbank.
  * **Dateien:** [model_repository.py](file:///C:/SnapdragonAI/controllers/model_repository.py), [model_manager_model.py](file:///C:/SnapdragonAI/controllers/model_manager_model.py), [model_manager_controller.py](file:///C:/SnapdragonAI/controllers/model_manager_controller.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py), [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py)

* **Sprint P-054 (AI Backend Adapter Architecture Foundation):**
  * **Backend-Abstraktionsschicht:** Definition der abstrakten Basisklasse `BackendAdapter` (ABC) mit Schnittstellenmethoden zur Initialisierung, Herunterfahren, Progress-Tracking, Job-Erzeugung und Stopp-Signalisierung.
  * **Registrierung & Steuerung:** Implementierung des `BackendManager` zur Registrierung, Abfrage und Aktivierung von Adaptern. Standardmäßig werden vier Stubs registriert: `CPUBackendAdapter`, `QNNBackendAdapter`, `ONNXBackendAdapter` und `RemoteBackendAdapter`.
  * **Pipeline-Integration:** `GenerationController` leitet `queue_generation()`-Aufträge nun über die `GenerationQueue` an den `BackendManager` und somit an das aktive Inferenz-Backend weiter, das den Job ausführt (Stub-generiert).
  * **UI-Inspector-Erweiterung:** Der Preview-Inspector im Prompt-Workspace wurde um eine detaillierte Infobox ("Generierungsinformationen") erweitert, die live Engine (Stub Backend), Backend (z.B. CPU (Stub)), Version, Generierungsstatus und das aktive Modell anzeigt. Alles ist komplett neutral ohne RealESRGAN-Hartcodierungen gehalten.
  * **Dateien:** [backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/backend_adapter.py), [backend_manager.py](file:///C:/SnapdragonAI/engine/backends/backend_manager.py), [cpu_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/cpu_backend_adapter.py), [qnn_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/qnn_backend_adapter.py), [onnx_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/onnx_backend_adapter.py), [remote_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/remote_backend_adapter.py), [generation_controller.py](file:///C:/SnapdragonAI/controllers/generation_controller.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint P-053 (Generation Pipeline Foundation):**
  * **Generierungs-Pipeline:** Einführung der Klassen `GenerationJob` (Datenobjekt mit UUID, Status und Fortschritt) und `GenerationQueue` (lokale FIFO-Warteschlange für anstehende Generierungsaufträge).
  * **Controller-Erweiterung:** `GenerationController` erzeugt nun bei Klick auf "BILD GENERIEREN" einen neuen `GenerationJob` (Snapshot der Session-Parameter) und schiebt diesen in die `GenerationQueue`.
  * **UI- & Inspector-Vorbereitung:** Das Generierungs-Vorschau-Panel (Rechte Seite / Inspector-Slot) zeigt nun live die Warteschlangengröße ("Queue: 0 Jobs", "Queue: 1 Job" etc.) an. Der Statusbalken unten links meldet die Anzahl der wartenden Aufträge.
  * **Produktbereinigung:** Veraltete und harte Bezüge auf das "RealESRGAN"-Plugin und die "QNN"-Engine wurden im gesamten System (Seitenleiste, Startseite, Bildbetrachter-Metadaten) neutralisiert. Es wird nun sauber "Generation Engine: Nicht verbunden" und "Backend: Noch keine Engine aktiv" / "Stub" angezeigt.
  * **Dateien:** [generation_job.py](file:///C:/SnapdragonAI/controllers/generation_job.py), [generation_queue.py](file:///C:/SnapdragonAI/controllers/generation_queue.py), [generation_controller.py](file:///C:/SnapdragonAI/controllers/generation_controller.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [image_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/image_view.py), [right_panel.py](file:///C:/SnapdragonAI/widgets/phoenix/right_panel.py), [batch_controller.py](file:///C:/SnapdragonAI/gui/controllers/batch_controller.py), [home_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/home_view.py), [job_card.py](file:///C:/SnapdragonAI/widgets/phoenix/cards/job_card.py)

* **Sprint P-052 (Generation Session & Generation Controller Foundation):**
  * **Generierungs-Architektur:** Erstellung von `GenerationSessionModel` als Single Source of Truth für Generierungsdaten und `GenerationController` zur Validierung, Verwaltung und Steuerung von Generierungen.
  * **Workspace-Integration:** `PromptWorkspaceController` wurde so angepasst, dass er alle Generierungsaufrufe über den `GenerationController` schleust und die Generierungsparameter an das `GenerationSessionModel` delegiert.
  * **Vorbereitung zukünftiger Backends:** Im `GenerationController` wurden Schnittstellenkommentare und Platzhalter für zukünftige QNN (NPU), ONNX Runtime, CPU und Remote Backends angelegt.
  * **Dateien:** [generation_session.py](file:///C:/SnapdragonAI/controllers/generation_session.py), [generation_controller.py](file:///C:/SnapdragonAI/controllers/generation_controller.py), [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py)

* **Sprint P-051 (Prompt Workspace Foundation):**
  * **Neuer Workspace „AI Generate“:** Der Workspace wurde in die Navigation/Sidebar sowie das Seiten-Routing integriert und lässt sich sauber ansteuern.
  * **UI-Foundation:** Implementierung von Prompt- und Negativ-Prompt-Eingabefeldern, Parametern (Seed, Steps, CFG Scale, Breite, Höhe) und einem Modell-Auswahl-Dropdown. Auf der rechten Seite wird ein leerer Platzhalter für das generierte Bild angezeigt. Alles ist vollständig Dark/Light-Theme-kompatibel.
  * **MVC-Architektur & Generate-Stub:** Erstellung von `PromptWorkspaceModel` und `PromptWorkspaceController`. Der „Bild generieren“-Button liest alle Eingaben aus, setzt den Status auf „Generation queued (stub)“ und gibt die gesammelten Parameter als Log-Eintrag aus.
  * **Dateien:** [prompt_workspace_model.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_model.py), [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint P-050 (Gallery → Compare Workflow Completion):**
  * **Doppelklick & Kontextmenü:** Doppelklick auf ein Galerie-Thumbnail oder Auswahl von „In Compare öffnen“ im neuen, passend gestylten Kontextmenü (Rechtsklick) öffnet das Bild stabil in der Vergleichsansicht. Die Übergabe erfolgt sauber über die MVC-Controller/Adapter-Struktur.
  * **Robuste Großbild-Vergleichsansicht:** `CompareWorkspaceController` wurde so erweitert, dass er sehr große Bilder (> 50 MP) beim Laden für die Anzeige proportional auf eine Kantenbreite von max. 4096 Pixeln herunterskaliert, während die vollständige Metadaten-Auflösung beibehalten wird. Zudem wurde `Image.MAX_IMAGE_PIXELS = None` gesetzt, um Abstürze durch Decompression Bomb Checks zu verhindern.
  * **Dateien:** [thumbnail_widget.py](file:///C:/SnapdragonAI/widgets/phoenix/gallery/thumbnail_widget.py), [thumbnail_area.py](file:///C:/SnapdragonAI/widgets/phoenix/gallery/thumbnail_area.py), [compare_workspace_controller.py](file:///C:/SnapdragonAI/controllers/compare_workspace_controller.py)

Am **06.07.2026** wurden wichtige Bugfix-Korrekturen durchgeführt:

1. **Gallery Thumbnail-Rendering nach Resize (Bugfix):**
   * **Problem:** Gallery-Thumbnails wurden nach dem Ändern der Fensterbreite (Resize / Spaltenwechsel) permanent durch Platzhalter ersetzt.
   * **Ursache:** Der Spaltenwechsel führte dazu, dass alte Widgets zerstört wurden. Der `ThumbnailProvider` blockierte jedoch nachfolgende Anfragen für dieselben `(path, size)`-Schlüssel via `_pending_paths`, sodass neue Widgets keine gültigen Callbacks erhielten.
   * **Lösung:** `ThumbnailProvider` wurde so umstrukturiert, dass er mehrere Callbacks für denselben pending Thumbnail-Ladevorgang registriert (`self._pending_callbacks`). Sobald das Laden abgeschlossen ist, werden alle registrierten Callbacks im UI-Thread ausgeführt.
   * **Dateien:** [thumbnail_provider.py](file:///C:/SnapdragonAI/widgets/phoenix/gallery/thumbnail_provider.py)

2. **Verzerrter Bild-Output im RealESRGAN-Plugin (Bugfix):**
   * **Problem:** Das vom RealESRGAN-Plugin erzeugte Ausgabebild war im Windows-Foto-Viewer verzerrt (auf quadratisches Format gestaucht).
   * **Ursache:** Der QNN-Modell-Input ist auf ein statisches Format von `128x128` festgelegt, weshalb das Eingabebild vor der Inferenz auf ein Quadrat gestaucht wurde. Das `512x512` NPU-Ergebnisbild wurde dann ohne Rescaling/Seitenverhältnis-Wiederherstellung gespeichert. Die Hilfsfunktion `_restore_target_resolution` war als No-Op implementiert.
   * **Lösung:** Implementierung von `_restore_target_resolution` im `QNNBackend` und Angleichung des Hilfsskripts `run_realesrgan.py`. Das `512x512`-Ausgabebild der NPU wird nun auf `(original_width * 4, original_height * 4)` skaliert. Dadurch wird das originale Seitenverhältnis wiederhergestellt und das Bild proportional korrekt vergrößert.
   * **Dateien:** [qnn_backend.py](file:///C:/SnapdragonAI/engine/backends/qnn_backend.py), [run_realesrgan.py](file:///C:/SnapdragonAI/run_realesrgan.py)

---

## 2. System- und Hardware-Umgebung

Das Projekt nutzt lokale NPU-Beschleunigung:
* **Entwicklungspfad:** `C:\SnapdragonAI`
* **Qualcomm AI Stack SDK:** `C:\Qualcomm\AIStack\2.47.0.260601` (enthält `qnn-net-run.exe`, `QnnHtp.dll` und Hilfsbibliotheken)
* **Python-Interpreter:** Python 3.11.9 ARM64 (`C:\Program Files\Python311-arm64\python.exe`)
* **Modellpfad für Upscaling:** `C:\SnapdragonAI\models\real_esrgan_x4plus.bin`

---

## 3. Nächste Schritte

1. **Manueller Test:** Validierung der Stabilität des Galerie-Grids beim langsamen Resize und Überprüfung der Doppelklick-Funktion.
2. **Architektur-Reviews:** Abstimmung mit dem Product Owner zur Zusammenführung der QNN-Pfade.
3. **Erweiterungen:** Vorbereitung der RAM- und Disk-Caches für den `ThumbnailProvider` ohne das bestehende Design zu brechen.

*Ältere Projektberichte siehe:*
* [CURRENT_PROJECT_STATE_2026-07-01.md](file:///C:/SnapdragonAI/docs/CURRENT_PROJECT_STATE_2026-07-01.md)
* [NEXT_STEPS_2026-07-01.md](file:///C:/SnapdragonAI/docs/NEXT_STEPS_2026-07-01.md)

---

## 4. Produktvision 2.0 & Namens-Alignment (Sprint S-001)

Mit Sprint S-001 wurde die offizielle Neuausrichtung zur **AI Creative Suite (Product Vision 2.0)** festgeschrieben. Für die bestehenden Workspaces gelten im Code vorerst noch die alten technischen Implementierungsnamen, während langfristig folgende Zielbezeichnungen im Produkt verankert werden:
* **Gallery** → **AI Asset Library** (langfristige Zielbezeichnung)
* **Compare Workspace** → **Review Workspace** (langfristige Zielbezeichnung)
* **Image Workspace** → **Asset Inspector** (langfristige Zielbezeichnung)
* **Prompt / AI Generate** → **AI Generate**

Detaillierte Vision siehe [PRODUCT_VISION_2.0.md](file:///C:/SnapdragonAI/docs/PRODUCT_VISION_2.0.md).

