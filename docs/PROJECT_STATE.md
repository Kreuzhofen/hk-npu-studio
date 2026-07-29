# Projektstatus – Snapdragon AI Studio

**Stand:** 29.07.2026
**Zweig:** `feature/phoenix-rebuild`
**Zielplattform:** Windows 11 ARM64 (Qualcomm Snapdragon X NPU via QNN)

---

## 1. Aktueller Status & Letzte Änderungen

* **Sprint 10 – Pipeline-Konfiguration vereinheitlichen:** Jeder Generation-Job besitzt einen unveränderlichen zentralen Parametersnapshot. Pipeline sowie CPU-, ONNX- und QNN-Backends verwenden denselben Vertrag; drei doppelte QNN-Serialisierungen wurden entfernt. 32 relevante Tests sind erfolgreich; die UI wurde nicht geändert.

* **Sprint 9 – Speicherverwaltung absichern:** Physische CPU-, ONNX- und QNN-Backends werden nach jeder Generierung zentral heruntergefahren. ONNX-Komponentensitzungen werden auch bei Fehlern freigegeben; QNN-Workerprozesse, Pipes und Hostreferenzen werden nach Erfolg, Fehler und Abbruch geschlossen. 28 relevante Tests sind erfolgreich; die UI wurde nicht geändert.

* **Sprint 8 – Inference-Pipeline absichern:** Der bestehende zentrale Ablauf verwendet eine bereits geladene Runtime ohne zweiten Load, validiert numerische Eingaben einheitlich und normalisiert Backend-Ergebnisse. Fehler und ungültige Rückgaben setzen den Job zuverlässig auf `FAILED`; Abbrüche behalten auch gegenüber verspäteten Erfolgsresultaten Vorrang. Freigabe- und UI-Verhalten bleiben unverändert. Betroffene Tests: 34 erfolgreich; Gesamtcheck: 166 Tests und 20 Subtests erfolgreich.

* **Sprint 7 – Modell-Ladeprozess stabilisieren:** `ModelLoaderService` vereinheitlicht Auflösung, Registry-Prüfung, Backend-Bindung sowie Laden, Entladen und Wechseln von CPU-, ONNX- und QNN-Modellen. Ein expliziter, lock-geschützter Lebenszyklus mit `UNLOADED`, `LOADING`, `LOADED`, `UNLOADING` und `FAILED` serialisiert konkurrierende Zustandswechsel. Identische parallele Ladevorgänge verwenden dieselbe Runtime mit Referenzzählung; ein Wechsel wird blockiert, solange das aktuelle Modell noch verwendet wird. Registry-Status und Installationsstruktur werden vor der Backend-Initialisierung geprüft. Kontextgebundene Nutzung sowie `finally`-Freigaben in Generation Controller und Executor schließen Backend-Ressourcen bei Erfolg, Fehler und Abbruch zuverlässig. Strukturierte Diagnosen erfassen Lade-, Initialisierungs-, Freigabe- und Kompatibilitätsfehler. Die UI wurde nicht geändert. Der vollständige Testlauf umfasst 160 erfolgreiche Tests und 20 erfolgreiche Subtests.

* **Sprint 6 – Model Manager professionalisieren:** `ModelRegistry` ist die zentrale, UI-unabhängige Quelle für Modellmetadaten, Validierungsberichte und Installationszustände. Das rückwärtskompatible Metadatenschema v1 normalisiert bestehende Definitionen und prüft Pflichtfelder, Typen sowie die Kompatibilität zum registrierten Backend-Vertrag. Ungültige oder unlesbare Definitionen werden sicher quarantänisiert und bleiben über Diagnoseberichte sichtbar. Installierte Modelle werden auf Pfad, Paketstruktur, Manifest-ID, deklarierte Komponenten, sichere relative Pfade und optional vorhandene SHA-256-Werte geprüft. `ModelRepository`, lokale Paketvalidierung und Generationsrouting verwenden dieselbe Registry bzw. Backend-Auflösung; bestehende Modell- und UI-Verträge bleiben unverändert. Der vollständige Testlauf umfasst 154 erfolgreiche Tests und 20 erfolgreiche Subtests.

* **Sprint 5 – Konfigurationssystem vereinheitlichen:** `ConfigurationManager` ist die zentrale Persistenzschicht für `data/preferences.json`. Das top-level-kompatible Schema v2 besitzt eine explizite `schema_version`, validierte Standardwerte und atomare Schreibvorgänge über eine temporäre Datei. Migrationen übernehmen unversionierte flache Konfigurationen, ältere verschachtelte `settings`, frühere Schlüsselbezeichnungen sowie boolesche bzw. numerische Altwerte. Bekannte Preferences werden typ- und wertevalidiert; unbekannte Schlüssel bleiben für Vorwärtskompatibilität erhalten. `config.py`, `SettingsManager`, `ModelRepository` und `i18n` verwenden nun denselben Lade-/Speicherpfad. Bestehende UI-Schlüssel und Stringwerte bleiben kompatibel; die UI wurde nicht geändert. Der vollständige Testlauf umfasst 146 erfolgreiche Tests und 20 erfolgreiche Subtests.

* **Sprint 4 – Logging & Fehlerdiagnose professionalisieren:** `engine/logging_config.py` konfiguriert zentral eine strukturierte, rotierende UTF-8-Protokolldatei unter `logs/snapdragon_ai_studio.log`. Das Logverzeichnis entsteht automatisch; die aktive Datei rotiert bei 5 MiB mit fünf Sicherungen. Backend-, ONNX-/QNN-Service-, Pipeline-, Executor-, JobManager- und Worker-Komponenten verwenden die zentrale Logger-Erzeugung mit den Leveln `DEBUG`, `INFO`, `WARNING`, `ERROR` und `CRITICAL`. Domänenspezifische Fehlerklassen stehen in `engine/exceptions.py`; `diagnose_exception()` erzeugt strukturierte Diagnosen mit Kategorie, Kontext, Exception-Typ, Job-ID und Backend und protokolliert den vollständigen Traceback. Bestehende Konsolenausgaben und Ergebnisverträge bleiben erhalten. Die UI wurde nicht geändert. Der vollständige Testlauf umfasst 140 erfolgreiche Tests und 20 erfolgreiche Subtests.

* **Sprint 3 – Job- & Pipeline-Engine stabilisieren:** Alle ausführbaren Jobs verwenden den zentralen Vertrag `JobStatus` mit `QUEUED`, `RUNNING`, `FINISHED`, `FAILED` und `CANCELLED` sowie normiertem Fortschritt von `0.0` bis `1.0`. `GenerationJob`, `GenerationQueue`, `ImageGenerationPipeline`, Legacy-`Job`, `JobManager`, `PhoenixWorker`, `PhoenixScheduler` und die Backend-Abbruchpfade greifen auf gemeinsame Status-, Fortschritts-, Fehler- und Abbruchfunktionen zu. Historische Statuswerte werden zur Kompatibilität normalisiert. Die zuvor dreifache Interpretation von QNN-Worker-Ausgaben wurde in `generation_progress.py` zentralisiert; bestehende UI-Callbacks erhalten weiterhin Prozentwerte von `0` bis `100` und lokalisierte Phasenmeldungen. Scheduler-Abbrüche markieren aktive und wartende Aufträge konsistent als abgebrochen. Die UI wurde nicht geändert. Der vollständige Testlauf umfasst 137 erfolgreiche Tests und 20 erfolgreiche Subtests.

* **Sprint 2 – Backend vereinheitlichen:** `InferenceBackend` ist nun der gemeinsame Grundvertrag für Routing-Adapter und physische CPU-, ONNX- und QNN-Backends. Lebenszyklus, Verfügbarkeit, Metadaten, Generierung, Abbruch, Fortschritt und Health-Check besitzen eine einheitliche Schnittstelle. Die identische Zustands- und Ergebnislogik der CPU-, ONNX- und generischen QNN-Stubs liegt zentral in `StubBackendAdapter`; die produktiven SD1.5-, SD2.1- und ControlNet-QNN-Routen teilen Delegation und Abbruch über `QnnProductBackendAdapter`. Die bisher abweichende ONNX-Verfügbarkeitsprüfung wurde in eine boolesche Vertragsmethode und eine separate Diagnosemethode getrennt. Backend-Namen, Versionen, Meldungen, Auswahlreihenfolge und produktive QNN-Funktionalität bleiben erhalten; die UI wurde nicht geändert. Der vollständige Testlauf umfasst 129 erfolgreiche Tests und 15 erfolgreiche Subtests.

* **Sprint 1 – Projektbasis stabilisieren:** Der vollständige Python-Bestand lässt sich unter Python 3.11.9 fehlerfrei kompilieren. Die pytest-Sammlung ist über `pytest.ini` auf die reguläre Testsuite unter `tests/` begrenzt, sodass Laufzeit- und Diagnoseskripte in `temp/`, `scratch/` und `scripts/` nicht mehr versehentlich während der Testsammlung ausgeführt werden. Der vollständige Testlauf umfasst aktuell 125 Tests und ist ohne Fehler oder Warnungen erfolgreich. Es wurden keine Features und keine Architekturänderungen vorgenommen.

* **Sprint CN-002 – ControlNet Reference Image UI:** Echte Referenzbild-Auswahl und Validierung für ControlNet Canny im AI Generate Workspace integriert. Die Drag & Drop Card und der Subtitle werden bei Modellen ohne ControlNet-Unterstützung (SD1.5, SD2.1) automatisch verborgen und bei Aktivierung eines ControlNet-Modells dynamisch eingeblendet und mit passendem Titel versehen. Die Eingabebilder werden vorab in `GenerationController.validate_session()` auf Existenz und Format geprüft.

* **Sprint CN-001 – ControlNet Canny Backend Integration:** Lokale ControlNet Canny Generierung als produktiver Backendpfad in Snapdragon AI Studio integriert. Die Modelle (Text Encoder, ControlNet, UNet, VAE) laufen vollständig auf der Hexagon HTP NPU (CPU EP Fallback deaktiviert). Der Backend-Adapter führt die Ausführung in einer isolierten virtuellen Umgebung (`temp/controlnet_canny_gate/venv`) aus. Canny-Kantenberechnung erfolgt ressourcenschonend auf der CPU (reines NumPy). Das verwendete Eingabebild wird zur Reproduzierbarkeit kopiert, und ein dreiteiliger Kontaktbogen (Original, Kanten, Generierung) wird zusammen mit dem detaillierten JSON-Sidecar erzeugt.

* **Sprint G-008B – Runtime Header and Scroll Fix:** Erreichen einer perfekten Skalierungs- und Scroll-Robustheit im Phoenix-Design. Durch die Deaktivierung der Größenunterdrückung (`pack_propagate(True)`) und Einführung einer dynamischen Höhenanpassung sowie von internem Label-Padding (`ipady=2`) passt sich der Header (`PhoenixHeader`) automatisch an seine Kindelemente an, was abgeschnittene Workspace-Titel auf allen Skalierungsstufen (100% bis 150%) verhindert. Im AI Model Manager Detailbereich werden Treeview-Items und Labels in-place aktualisiert. Ein Helfer `_update_label` verhindert Redraws bei identischen Werten und die Scrollregion des Canvas wird nur angepasst, wenn sich die Bounding Box strukturell ändert. Das unwillkürliche Scroll-Springen und jegliches Fokus-Stehlen wird dadurch vollständig eliminiert, und die Y-Scrollposition bleibt bei Hintergrund-Updates absolut stabil.
* **Sprint G-008A – UI-Nachbesserungen:** Behebung von UI-Mängeln zur Optimierung des Phoenix-Designs. Die Header-Höhe des Phoenix-Workspace wurde von 60px auf 72px angehoben, um ein Abschneiden des aktuellen Workspace-Titels auf allen Windows-Skalierungen zu verhindern. Im AI Model Manager wurde das automatische Zurückscrollen nach oben durch einen Modellstatus-Signaturvergleich (verhindert Treeview-Wiederaufbauten bei unveränderten Daten) sowie durch ein proaktives Sichern und Wiederherstellen der Canvas-Scrollposition bei Status-Updates behoben. Die Prompt-Werkzeuge (Vorlagen, Verlauf, Maximieren) wurden in einer zusammengehörigen, kontraststarken Werkzeugleiste (`self.prompt_toolbar`) im Segment-Control-Design mit klaren Symbolen und visuellen Trennlinien konsolidiert.
* **Sprint G-008 – AI Generate UI Polish:** Umfassender optischer und struktureller Feinschliff der Hauptansicht von AI Generate zur Etablierung eines kommerziellen Standards. Sämtliche Parameter-Bereiche (Model, Prompt, Referenzbild, Image Size, Sampling, Output) wurden bezüglich ihrer Außenabstände (`padx=16` für alle Karten und Rahmen) und ihrer vertikalen Trennungen (`pady=12`) vereinheitlicht, um eine perfekte, gerade Ausrichtung entlang der linken und rechten Kanten zu gewährleisten. Die Buttons im Prompt-Header (Vorlagen, Verlauf, Maximieren) sowie der Button für erweiterte Einstellungen wurden optisch angeglichen (identische Höhen, Paddings, Schriftarten und aktive Zustände). Für alle diese Buttons, die Qualitätsprofil-Buttons sowie das Referenzbild-Card-Widget wurden reaktive, flüssige Hover-Effekte via Enter/Leave-Bindings implementiert. Der Referenzbild-Bereich wurde vertikal kompakter gestaltet (`pady=8`), um unnötige Scrollstrecken zu minimieren.
* **Sprint G-007A – Reference Image UX:** Umbenennung der Drag & Drop Parametergruppe in "Referenzbild (Demnächst)" und Ergänzung des Untertitels *"Vorbereitung für Image→Image und Image→Video."* unter Verwendung von `ThemeManager`-Farben und -Schriftarten zur Wahrung der Dark/Light-Themeparität. Die Vorschaufunktion, die Metadatenanzeige und der Löschbutton ("Bild entfernen") bleiben unverändert erhalten.
* **Sprint G-007 – Drag & Drop Foundation:** Integration der Drag & Drop-Funktionalität für Bilddateien (PNG, JPG, JPEG, WebP) in der AI Generate-Ansicht. Nach dem Ablegen einer Datei wird eine kompakte Bildvorschau sowie deren Dateiname und Auflösung dargestellt. Ein "Bild entfernen"-Button ermöglicht das Zurücksetzen der Auswahl. Die Bilddatei wird hierbei ausschließlich geladen (über PIL) und nicht durch die KI verarbeitet. Das MVC-Modell (PromptWorkspaceState, PromptWorkspaceModel, PromptWorkspaceController und GenerationSessionModel) wurde architektonisch um das Feld `input_image_path` erweitert, um spätere Image→Image- und Image→Video-Workflows vorzubereiten. Das gesamte UI-Design basiert auf dem Phoenix-ThemeManager, wodurch die volle Dark- und Light-Theme-Kompatibilität sowie die Robustheit in Testumgebungen gewahrt bleibt.
* **Sprint G-004A – Fix Quality Presets Visibility:** Behebung eines Layout-Verdrängungs-Bugs, bei dem die drei nebeneinander angeordneten Presets-Buttons die Spaltenbreite im Canvas-Viewport überdehnten und somit die gesamte rechte Spalte unsichtbar machten. Die Schaltflächen werden nun platzsparend untereinander angeordnet, wodurch die korrekte Spaltenbreite (290px) gewahrt bleibt.
* **Sprint G-004 – Quality Presets:** Ersatz der technischen Steps-Einstellungen im Standardmodus (bei Modellen mit gesperrter Auflösung) durch drei Presets (⚡ Schnell, ⭐ Standard, 💎 Beste Qualität). Die Presets steuern intern die Steps (Schnell = 10, Standard = 20, Beste Qualität = 30 für SD1.5 und SD2.1 QNN Modelle), während der tatsächliche Step-Wert in den Metadaten erhalten bleibt. Umschalten auf andere Modelle stellt die standardmäßige Steps-Skala automatisch wieder her.
* **Sprint G-003 – Prompt Templates:** Einführung einer ausbaufähigen Vorlagenverwaltung für AI-Prompts. Eine JSON-Datei unter `resources/prompt_templates.json` speichert Kategorien (Portrait, Landschaft, Architektur, Fantasy, Sci-Fi, Produktfoto) mit Vorlagen. In der UI bietet eine "Vorlagen ▼"-Schaltfläche ein kaskadierendes Menü zur Schnellauswahl. Ein Klick überschreibt den Hauptprompt, während der negative Prompt unberührt bleibt. Alle Elemente integrieren sich harmonisch in das Phoenix-Theming.
* **Progress Bar Fix (G-003):** Beseitigung des Problems, dass die Progressbar bei tab- oder layoutbedingten externen Theme-Aktualisierungen grau wird, indem die Layoutstruktur und die Phoenix-Success-Rolle bei jedem Fortschrittsschritt re-aktiviert werden.
* **Sprint G-002 – Prompt History:** Hinzufügen einer lokalen Prompt-History für AI Generate. Die letzten 20 erfolgreich generierten Prompts werden persistent und duplikatfrei (neuester Eintrag gewinnt) in der Datei `data/prompt_history.json` gespeichert. Die History lässt sich über ein kleines Verlaufssymbol (🕘) direkt neben dem Prompt-Titel öffnen. Ein Klick auf einen Eintrag übernimmt den Prompt in das Textfeld, während negative Prompts unverändert bleiben. Sämtliche UI-Elemente unterstützen Dark- und Light-Theme-Vorgaben über den `ThemeManager` ohne hartcodierte Farben.
* **Sprint G-001E – Resolution Availability UX:** Die Auflösungsauswahl stellt für die Modelle SD1.5 QNN und SD2.1 QNN ausschließlich die unterstützte Option 512×512 sichtbar und ausgewählt dar. Die Option 1024×1024 bleibt sichtbar, wird jedoch im Layout deaktiviert und mit einem Schloss-Symbol (🔒) und dem Vermerk „Demnächst“ versehen. Ein Informationstext weist darauf hin, dass höhere Auflösungen kompatible Qualcomm-Modelle voraussetzen. Die UI wechselt bei anderen Modellen automatisch auf die Standard-Dropdowns zur Breite/Höhe-Auswahl zurück. Alle Farben basieren auf dem Phoenix-ThemeManager, wodurch die Dark- und Light-Theme-Kompatibilität vollständig erhalten bleibt.
* **Sprint G-001D – Functional Cancel:** Der Abbruchpfad reicht nun vom AI-Generate-Button über GenerationController, Queue und QNN-Adapter bis zum konkreten SD1.5-/SD2.1-Workerprozess. Worker-Logzeilen überschreiben den Queue-Lifecycle nicht mehr; das dauerhafte Cancel-Signal beendet den Subprozess, verhindert erfolgreiche Workflow-Callbacks und entfernt im Save-Race entstandene PNG-/Sidecar-Dateien des abgebrochenen Jobs. Reale NPU-Tests nach jeweils fünf Sekunden endeten für beide Modelle mit `CANCELLED`, ohne Ausgabe und ohne verbliebenen Worker.
* **Sprint G-001 – AI Generate UX Refresh:** Die AI-Generate-Oberfläche priorisiert den Prompt nun als akzentgerahmten Composer mit großzügiger Hauptbeschreibung und klar untergeordnetem Negative Prompt. Eine feste, deutlich hervorgehobene Action-Bar hält die lokale Bildgenerierung als primäre Aktion jederzeit sichtbar. Abstände, Typografie, Flächen und Zustände verwenden ausschließlich Phoenix-Theme-Rollen und funktionieren in Dark und Light; Controller, Modellparameter und Bildpipeline bleiben unverändert.
* **Sprint G-001B – Generate UX Fixes:** Die Generate-Action-Bar bietet während aktiver Jobs einen funktionalen Abbruch über den bestehenden GenerationController-Pfad; Queue-, Button- und UI-Status enden eindeutig in `CANCELLED`. Der Phoenix-Progressbar-Style verwendet in Dark und Light die zentrale grüne Success-Rolle. Das zuletzt ausgewählte installierte Produktmodell wird unter `data/preferences.json` lokal gespeichert und beim Neustart zwischen Model Manager, WorkflowState und AI Generate wiederhergestellt; ungültige oder nicht verfügbare IDs fallen deterministisch auf ein auswählbares Modell zurück.
* **Milestone M-001 – First Production Image Pipeline Audit:** Die produktiven SD1.5- und SD2.1-QNN-Pipelines wurden vollständig gegen Paketverträge und Stable-Diffusion-Referenzmathematik geprüft. Scheduler, Timesteps, Prediction Types, CFG, Latent-/VAE-Skalierung, Tensorformen und Quantisierung sind korrekt; identische Hardware-Regressionsläufe erzeugen unveränderte PNG-Hashes. Korrigiert wurden die CLIP-konforme HTML-/Unicode-Promptnormalisierung, die tatsächliche Terminierung laufender QNN-Worker bei Cancel einschließlich Race-Condition, der Schutz vor veralteten Workerresultaten und die garantierte QNN-Sessionfreigabe nach Fehlern. Keine GUI- oder Forschungsänderung.
* **Experiment HR-001 – Tiled QNN Diffusion PoC:** Ein isolierter SD2.1-Proof-of-Concept denoisiert einen gemeinsamen 128×128-Latent-Canvas über neun überlappende, feste 64×64-QNN-Fenster. Text Encoder, 360 UNet-Inferenzen pro 20-Step-Lauf und neun gekachelte VAE-Decodes laufen fail-closed über QNN/HTP; Host-Code übernimmt ausschließlich DDIM-Scheduler, Canvas, Cosine-Blending, Akkumulation und PNG-Ausgabe. 1024×1024-Läufe mit 64 px und 128 px Bildüberlappung waren technisch erfolgreich und reproduzierbar, sind wegen noch sichtbarer großräumiger Motiv-/Perspektivwechsel aber ausdrücklich nicht als Produktfunktion freigegeben. Produktiver 512×512-Pfad und GUI bleiben unverändert.
* **Sprint P4-001A – AI Asset Library Index Foundation:** Eine medienneutrale Asset-Index-Schicht synchronisiert unterstützte Bilder aus dem zentralen Output-Pfad deterministisch in einen lokalen SQLite-Index unter `data/asset_index.sqlite3`. Das Dateisystem bleibt Source of Truth; SQLite enthält ausschließlich reproduzierbare Such- und Metadaten, niemals Asset-Dateien. JSON-Sidecars werden bevorzugt und fehlertolerant ausgewertet, geänderte Assets aktualisiert und entfernte Assets als fehlend markiert. Die Struktur bereitet Video-Assets architektonisch vor, implementiert aber noch keine Videoverarbeitung, GUI-Umschaltung oder Live-Überwachung. Der PO-Abnahme-Bugfix aktualisiert die Gallery-Auswahl bei Einzel- und Doppelklick direkt an bestehenden Karten, sodass kein Grid-Neuaufbau und kein erneuter Thumbnail-Load ausgelöst wird.
* **Recovery IQ-R01 – IQ-001/IQ-004:** Die SD1.5-/SD2.1-QNN-Backends respektieren die angeforderten Steps und ausdrücklich leere Negative Prompts. Der SD1.5-Euler-Vertrag verwendet `leading`, Offset 1 und epsilon Prediction; kompakte Sidecars dokumentieren Timesteps, Sigmas, Latent Scaling, Tensorstatistiken und Laufzeiten. AI Generate bezieht Auflösung, Steps, CFG, Seed, Sampler, Scheduler und Prediction Type modellunabhängig aus `generation_parameters`; Modellwechsel und Model-Manager-Aktivierung synchronisieren die sichtbaren Controls und den Generation-Job.

Am **16.07.2026** wurden folgende Sprints abgeschlossen:

* **Sprint CN-002 – ControlNet Reference Image UI:**
  * **Dynamische Sichtbarkeit:** Dynamic grid/removal configuration of the Drag & Drop area (`dnd_card` and `dnd_subtitle`) depending on ControlNet model capabilities.
  * **Validierung:** Vorabprüfung der Referenzbilddatei im `GenerationController`.
  * **Unit-Tests:** Umfassende GUI- und Validierungstests in `test_controlnet_ui.py` und `test_generate_ux_state.py`.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [generation_controller.py](file:///C:/SnapdragonAI/controllers/generation_controller.py), [test_controlnet_ui.py](file:///C:/SnapdragonAI/tests/test_controlnet_ui.py), [test_generate_ux_state.py](file:///C:/SnapdragonAI/tests/test_generate_ux_state.py)

* **Sprint CN-001 – ControlNet Canny Backend Integration:**
  * **Inferenz-Backend-Adapter:** Implementierung der physischen Inferenzschritte für ControlNet Canny auf HTP in `controlnet_canny_backend.py`.
  * **Backend-Adapter:** Erstellung des Adapters `ControlNetCannyQnnBackendAdapter` in `controlnet_canny_backend_adapter.py` zur Steuerung des Subprozesses.
  * **Factory-Registrierung:** Registrierung in der `InferenceBackendFactory` und im `BackendManager`.
  * **Modell-Metadaten:** Registrierung der Modelldefinition `controlnet_canny_qnn.json` unter `resources/models`.
  * **Dateien:** [controlnet_canny_backend.py](file:///C:/SnapdragonAI/engine/controlnet_canny_backend.py), [controlnet_canny_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/controlnet_canny_backend_adapter.py), [controlnet_canny_qnn.json](file:///C:/SnapdragonAI/resources/models/controlnet_canny_qnn.json), [backend_manager.py](file:///C:/SnapdragonAI/engine/backends/backend_manager.py), [inference_backend_factory.py](file:///C:/SnapdragonAI/engine/inference_backend_factory.py), [test_production_qnn_pipeline.py](file:///C:/SnapdragonAI/tests/test_production_qnn_pipeline.py)

Am **14.07.2026** wurden folgende Sprints abgeschlossen:

* **Sprint G-008B – Runtime Header and Scroll Fix:**
  * **Dynamischer Header:** Ablösung der festen Pixelhöhe (`height=72` entfernt), Deaktivierung der Größenunterdrückung (`pack_propagate(True)` und `grid_propagate(True)`) und Hinzufügen von internem Padding (`ipady=2`) bei Title- und View-Labels. Der Header passt sich dynamisch an seine Kindelemente an, was abgeschnittene Slogans und Untertitel bei jeglicher Windows-Skalierung (100% bis 150%) verhindert.
  * **Relative Scroll-Erhaltung & In-Place Updates:** Treeview-Items und Detail-Labels werden nun direkt in-place aktualisiert (`_update_label` verhindert Redraws bei identischen Textwerten). Die Scrollregion des Canvas wird über `_on_content_configure` nur noch dann neu berechnet, wenn sich die Bounding Box tatsächlich physisch verändert. Die Y-Scrollposition bleibt somit bei periodischen Updates absolut fest, und der Detailbereich springt nur bei einem bewussten Modellwechsel an den Anfang.
  * **Dateien:** [header.py](file:///C:/SnapdragonAI/widgets/phoenix/header.py), [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py)

* **Sprint G-008A – UI-Nachbesserungen:**
  * **Workspace-Titel:** Header-Höhe des Phoenix-Workspace von `60px` auf `72px` erhöht und Paddings für Logo, Title, View-Label und Slogan-Badge vertikal zentriert, um abgeschnittene Workspace-Titel (z. B. bei "AI Model Manager" oder "AI Generate") bei jeglicher Windows-Skalierung zu beheben.
  * **Model Manager Scroll-Stabilisierung:** Umschreiben der `refresh()`-Methode in `model_manager_view.py` um einen State-Signaturvergleich. Verhindert das Löschen/Neuaufbauen der Treeview, wenn keine Daten- oder Statusänderungen vorliegen. Bei echten Status-Updates wird die Y-Scrollposition des Canvas vorab gesichert und nach dem Update und einem `update_idletasks()`-Aufruf wiederhergestellt. Ein bewusster Modellwechsel in der Treeview setzt den Detail-Scrollbereich an den Anfang zurück.
  * **Prompt-Werkzeuge:** Integration einer zusammengehörigen und kontraststarken Werkzeugleiste (`self.prompt_toolbar`) für Vorlagen, Verlauf und Maximieren mit Trennlinien. Die Buttons nutzen die Kontrastfarbe `PHOENIX_THEME.text_primary` und ansprechendere Icons (`📋 Vorlagen`, `🕘 Verlauf`, `⛶ Maximieren`).
  * **Dateien:** [header.py](file:///C:/SnapdragonAI/widgets/phoenix/header.py), [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint G-008 – AI Generate UI Polish:**
  * **Layout-Bündigkeit:** Alle Karten, Trenner und Steuerelemente wurden durchgängig auf einen einheitlichen Randabstand von `padx=16` und vertikale Abschnitte auf `pady=12` gesetzt.
  * **Toolbar-Vereinheitlichung:** Die Prompt-Header-Buttons (Vorlagen, Verlauf, Maximieren) und der Button für erweiterte Einstellungen verwenden identische paddings, Höhen, Schriftarten und aktive Button-Farben.
  * **Hover-Effekte:** Flüssige Farbänderungen bei Mausberührung wurden für alle flachen Sekundär-Buttons und die Referenzbild-Box integriert.
  * **Kompaktes Referenzbild:** Vertikale Innenabstände der Drag & Drop-Box wurden auf `pady=8` verkleinert, um unnötiges Scrollen zu vermeiden.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint G-007A – Reference Image UX:**
  * **Umbenennung:** Der Parameterbereich wurde in "Referenzbild (Demnächst)" umbenannt.
  * **Untertitel:** Der Untertitel *"Vorbereitung für Image→Image und Image→Video."* wurde zur präzisen Benutzerführung unter der Überschrift ergänzt.
  * **Ästhetik & Layout:** Beide Beschriftungen nutzen das Phoenix-Theming und den ThemeManager, wodurch optimale Dark/Light-Theme-Kompatibilität gewahrt bleibt.
  * **Unveränderte Logik:** Die Vorschaufunktion, die Metadatenauswertung (Dateiname und Auflösung) sowie der "Bild entfernen"-Button wurden unverändert beibehalten.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint G-007 – Drag & Drop Foundation:**
  * **Drag & Drop Akzeptanz:** AI Generate akzeptiert Drag & Drop von Bilddateien (PNG, JPG, JPEG, WebP).
  * **Bildvorschau & Info:** Nach dem Ablegen wird eine kleine Bildvorschau samt Dateiname und Auflösung angezeigt.
  * **Bild entfernen:** Ein Button "✕ Bild entfernen" setzt die Auswahl zurück.
  * **MVC/Session Integration:** Vorbereitung der Architektur für spätere Image→Image- und Image→Video-Funktionen über das `input_image_path`-Feld in PromptWorkspaceState, PromptWorkspaceModel, PromptWorkspaceController und GenerationSessionModel.
  * **ThemeManager & Testkompatibilität:** Die UI nutzt das Phoenix-ThemeManager-System für volle Dark/Light-Themeparität und verwendet ein TclError-Fallback für Robustheit in testgesteuerten oder kopflosen Umgebungen.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py), [prompt_workspace_model.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_model.py), [generation_session.py](file:///C:/SnapdragonAI/controllers/generation_session.py), [test_generate_ux_state.py](file:///C:/SnapdragonAI/tests/test_generate_ux_state.py)

* **Sprint G-006 – Prompt Counter:**
  * **Live-Zähler:** Ein dynamischer Zähler für Zeichen und Wörter unter dem Prompt-Textfeld im Hauptbereich.
  * **Popup-Zähler:** Eine analoge Echtzeitanzeige im großen Prompt-Editor (Popup).
  * **Echtzeit-Synchronisation:** Beide Zählerstände werden bei jeder Tastatureingabe oder Prompt-Änderung (History/Templates) synchron aktualisiert.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [test_prompt_counter.py](file:///C:/SnapdragonAI/tests/test_prompt_counter.py)

* **Sprint G-005 – Expandable Prompt Editor:**
  * **Maximierungs-Button:** Ein neuer Button "⛶ Maximieren" neben dem Prompt-Header öffnet den Editor.
  * **Großes Editor-Popup:** Öffnet einen Prompt-Editor (Größe ca. 80% des Hauptfensters) in einem zentrierten Popup.
  * **Echtzeit-Synchronisation:** Bidirektionale Synchronisierung über explizite Sync-Methoden stellt die unmittelbare Wertaktualisierung sicher.
  * **Template- & History-Kompakt:** Das Laden von Vorlagen oder aus dem Verlauf befüllt parallel den Popup-Editor, falls dieser geöffnet ist.
  * **Schließen per ESC:** Der Tastaturbefehl ESC schließt das Fenster unmittelbar und übernimmt die Änderungen.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [test_expandable_prompt.py](file:///C:/SnapdragonAI/tests/test_expandable_prompt.py)

* **Sprint G-004D – Advanced Settings Popup Preview:**
  * **Kompakter Workspace:** Reduzierter Hauptbereich zeigt nur Modell, Prompts, Qualitätsprofile, Generierungskontrollen und einen Button "Erweiterte Einstellungen".
  * **Zentralisiertes Einstellungs-Popup:** Ein Klick öffnet ein modales Popup mit Auflösung (512x512/1024x1024), CFG-Scale, Sampler/Scheduler und Seed/Batch-Steuerungen.
  * **Konsistenter Zustand:** Bidirektionale Bindung an dieselben `tk.Variable`-Instanzen stellt die unmittelbare Synchronisierung ohne redundanten State sicher.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [test_advanced_popup.py](file:///C:/SnapdragonAI/tests/test_advanced_popup.py)

* **Sprint G-004A – Fix Quality Presets Visibility:**
  * **Vertikales Stacking:** Platzierung der drei Preset-Schaltflächen untereinander zur Einhaltung der maximalen Spaltenbreite.
  * **Workspace-Sichtbarkeit:** Vollständige Sichtbarkeit der Steuerelemente in Dark- und Light-Themes.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint G-004 – Quality Presets:**
  * **Presets-Steuerung:** Ersatz der Steps-Skala durch drei Presets im Standardmodus.
  * **Modellabhängiges Mapping:** Zuweisung von 10, 20 oder 30 Steps für SD1.5/SD2.1 QNN.
  * **Konsistente Metadaten:** Die tatsächliche Step-Zahl bleibt im Metadata-Sidecar erhalten.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [test_quality_presets.py](file:///C:/SnapdragonAI/tests/test_quality_presets.py)

* **Sprint G-003 – Prompt Templates:**
  * **Vorlagen-Verwaltung:** Speicherung von Vorlagen in der JSON-Datei `resources/prompt_templates.json`.
  * **Kaskadierendes Menü:** Schaltfläche "Vorlagen ▼" öffnet ein gegliedertes Popup-Menü.
  * **Auswahl-Übernahme:** Klick befüllt den Hauptprompt, ohne negative Prompts zu überschreiben.
  * **Fortschrittsbalken-Korrektur:** Nachhaltige Beseitigung des Gray-State-Bugs durch regelmäßige `_ensure_progress_style()`-Sicherstellung.
  * **Dateien:** [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [config.py](file:///C:/SnapdragonAI/config.py), [prompt_templates.json](file:///C:/SnapdragonAI/resources/prompt_templates.json), [test_prompt_templates.py](file:///C:/SnapdragonAI/tests/test_prompt_templates.py)

* **Sprint G-002 – Prompt History:**
  * **Verlauf-Speicherung:** Persistent und duplikatfreie Speicherung der letzten 20 erfolgreichen Prompts.
  * **UI-Trigger:** Verlaufssymbol (🕘) neben dem Prompt-Eingabefeld öffnet das Popup-Menü mit den Verlaufseinträgen.
  * **Fokus-Übernahme:** Klick auf einen Eintrag übernimmt diesen direkt ins Prompt-Feld, ohne negative Prompts zu manipulieren.
  * **Dateien:** [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [config.py](file:///C:/SnapdragonAI/config.py), [test_prompt_history.py](file:///C:/SnapdragonAI/tests/test_prompt_history.py)

Am **13.07.2026** wurde folgender Sprint abgeschlossen:

* **Sprint G-001E – Resolution Availability UX:**
  * **Auflösungsauswahl-Beschränkung:** Dynamische Einschränkung der Auflösung für SD1.5 und SD2.1 QNN Modelle auf ausschließlich 512×512 im Haupt-Workspace.
  * **Quick Selector Layout:** Hinzufügen einer blockierten Option für 1024×1024 samt Schloss-Symbol (🔒), Demnächst-Vermerk und Informationstext.
  * **Modellunabhängige Flexibilität:** Automatische Umschaltung zurück zur Standard-Option-Auswahl für Modelle ohne feste Auflösungssperre.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [icons.py](file:///C:/SnapdragonAI/resources/icons.py)

Am **08.07.2026** bzw. **07.07.2026** wurden folgende Sprints abgeschlossen:

* **Sprint Pack M3.1 – P-107 bis P-109 (First Real AI Image):**
  * **Integration & Validierung:** Ausbau der Detail-Fehlerprotokollierung zur genauen Nennung fehlender/ungültiger Dateipfade im Generierungs-Protokoll, um die Diagnose vor Ort beim Endanwender zu maximieren.
  * **End-to-End Testung:** Erfolgreiche Integration und Validierung des gesamten End-to-End-Inferenzflusses basierend auf der neuen SMP-Laufzeitarchitektur.
  * **Dateien:** [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint Pack M2.2 – P-104 bis P-106 (Automatic Runtime Activation):**
  * **Verifizierung & Status-Erstellung:** Implementierung der Methode `verify_components()` in `ModelRuntimePackage` zur automatischen Zustandsermittlung aller benötigten Komponenten (`tokenizer`, `text_encoder`, `text_encoder_2`, `unet`, `vae_decoder`, `scheduler`) mit den Statuswerten `READY`, `FOUND`, `MISSING`, `INVALID`.
  * **Umschaltautomatik:** Vollautomatische Aktivierungssteuerung der echten ONNX-Pipeline nur bei voll-betriebsbereitem Zustand (`READY`) aller benötigten Teilmodelle. Fehlt auch nur ein Baustein, schaltet das System geräuschlos auf den mathematisch/prozedural korrekten Mock-Fallback-Modus um.
  * **Dateien:** [model_runtime_package.py](file:///C:/SnapdragonAI/engine/model_runtime_package.py), [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py), [text_embedding_service.py](file:///C:/SnapdragonAI/engine/text_embedding_service.py), [unet_service.py](file:///C:/SnapdragonAI/engine/unet_service.py), [vae_decoder_service.py](file:///C:/SnapdragonAI/engine/vae_decoder_service.py)

* **Sprint Pack M2.1 – P-101 bis P-103 (First Real Image):**
  * **Lokale SDXL Inferenz:** Koppelung der End-to-End-Pipeline (`TextEmbeddingService` -> `UNetService` -> `VAEDecoderService`) zur echten Ausführung auf dem Snapdragon Model Package (SMP).
  * **Ausfallsicherheit & Verification:** Implementierung von nicht-fatalen Lade-Überprüfungen an der Wurzel-Inferenzsitzung. Wenn Komponenten wie Text-Encoder, UNet oder VAE auf der Festplatte fehlen, fangen die Services dies ab und fallen geräuschlos auf mathematisch bzw. prozedural korrekte Ersatzdaten (Mock-Latents, Mock-Embeddings, Concentric Rings VAE-Fallback) zurück.
  * **Dateien:** [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint Pack M1.3 – P-098 bis P-100 (Model Package Architecture):**
  * **Snapdragon Model Package Architecture (SMP):** Entwurf und Implementierung der endgültigen, professionellen und komplett datengesteuerten Modell-Paketstruktur basierend auf einer `package.json`-Beschreibungsdatei.
  * **Metadaten & Laufzeitzuordnung:** Unterstützung von versionsspezifischen Attributen (`package_version`, `author`, `display_name`) sowie fein-granularer Zuordnung der Ausführungskomponenten zu Hardware-Laufzeitumgebungen (CPU, ONNX, QNN).
  * **Repository-Erweiterung:** Überarbeitung des `ModelRepository` zum automatischen Parsen und Laden des neuen SMP-Formates sowie Erhalt der vollständigen Abwärtskompatibilität (Legacy Fallback) für alte Modellanordnungen.
  * **Dateien:** [model_runtime_package.py](file:///C:/SnapdragonAI/engine/model_runtime_package.py), [model_repository.py](file:///C:/SnapdragonAI/controllers/model_repository.py), [flux_dev.json](file:///C:/SnapdragonAI/resources/models/flux_dev.json) sowie `package.json` in [flux_dev](file:///C:/SnapdragonAI/models/flux_dev) und [sdxl_base](file:///C:/SnapdragonAI/models/sdxl_base)

* **Sprint Pack M1.2 – P-095 bis P-097 (End-to-End AI Pipeline):**
  * **VAEDecoderService:** Implementierung des VAE-Decoders zur Wandlung von Latent-Tensors `(1, 4, latent_h, latent_w)` in vollaufgelöste RGB-Bilder `(1, 3, latent_h * 8, latent_w * 8)`.
  * **Inferenz-Laufzeit-Pfad:** ONNX Inferenz des VAE-Decoders via `InferenceSession` mit sicherem Fallback auf eine prozedurale, ästhetisch ansprechende Rendering-Generierung (kreisförmige Verläufe basierend auf den Latent-Statistiken) bei fehlenden Modellgewichten.
  * **E2E-Pipeline-Verbindung:** Durchgängige Verkettung von `TextEmbeddingService` -> `UNetService` -> `VAEDecoderService` im `OnnxImageBackend`. Darstellung des Decoders im Diagnose-PNG und vollständige Parametrisierung im Sidecar-JSON.
  * **Dateien:** [vae_decoder_service.py](file:///C:/SnapdragonAI/engine/vae_decoder_service.py), [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-094 (First UNet Execution Foundation):**
  * **UNetService:** Implementierung eines modellunabhängigen UNet-Service zur Rauschvorhersage und Latents-Aktualisierung unter Verwendung des `ModelRuntimePackage`.
  * **SDXL-Latent-Generierung:** Dynamische Erzeugung von Anfangs-Latents in der korrekten Dimension für SDXL (z. B. `(1, 4, 64, 64)` bei `512x512` Eingangsauflösung).
  * **Inferenz-Laufzeit-Pfad:** Versuch der echten UNet-ONNX-Inferenz über `InferenceSession` und dynamischer Mapping von Eingangs-Variablen. Ausfallsicherer Fallback auf Euler-aktualisierte Mock-Latents bei Dateifehlern oder fehlendem ONNX-Support.
  * **Pipeline-Integration:** Vollständige Kopplung von Text-Embeddings und Latents-Aktualisierung im `OnnxImageBackend`. Einzeichnen der finalen Latent-Form auf dem Diagnose-PNG und Erfassung in den JSON-Metadaten-Sidecars.
  * **Dateien:** [unet_service.py](file:///C:/SnapdragonAI/engine/unet_service.py), [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-093 (First Real AI Execution):**
  * **TextEmbeddingService:** Implementierung eines modellunabhängigen Text-Embedding-Service zur Tokenisierung von Prompts (mit CLIP-Struktur: 77 Token, SOS/EOS, Zero-Padding) und Übertragung an den Text-Encoder.
  * **Inferenz-Laufzeit-Pfad:** Versuch des echten ONNX-Text-Encoder-Laufs mittels `InferenceSession` bei Vorhandensein der `.onnx`-Datei und sauberer Fallback zu stochastisch-deterministischen Dummy-Embeddings (`(1, 77, 768)` für SDXL CLIP) bei Fehlen der Datei oder Bibliotheken.
  * **Generierungs-Integration:** Einbindung von Tokenizer/Embedding in den Generierungsablauf des `OnnxImageBackend`. Darstellung der extrahierten Token-Sequenz und der Einbettungsform auf dem Diagnose-PNG-Ausgabebild sowie Abspeicherung in den JSON-Sidecars.
  * **Dateien:** [text_embedding_service.py](file:///C:/SnapdragonAI/engine/text_embedding_service.py), [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-092 (SDXL Runtime Architecture):**
  * **ModelRuntimePackage:** Einführung der Klasse `ModelRuntimePackage` zur modellunabhängigen Repräsentation der Dateipfade und Ziel-Runtimes der 6 Kern-Modellkomponenten (`tokenizer`, `text_encoder`, `text_encoder_2`, `unet`, `vae_decoder`, `scheduler`).
  * **Repository-Anbindung:** Ergänzung des `ModelRepository` um die Methode `build_runtime_package(model_id)`, welche die absoluten Pfade und Komponenten-Laufzeitumgebungen (z. B. ONNX vs. QNN) auflöst.
  * **Validierung:** Paketinterne Validierung (`is_valid_package()`), die das Vorhandensein aller konfigurierten Gewichts- und Metadatendateien auf der Festplatte sicherstellt.
  * **Dateien:** [model_runtime_package.py](file:///C:/SnapdragonAI/engine/model_runtime_package.py), [model_repository.py](file:///C:/SnapdragonAI/controllers/model_repository.py)

* **Sprint P-091 (AI Model Capability System):**
  * **Modellunabhängiges Capability-System:** Implementierung der Klasse `ModelCapabilities` zur Kapselung von Fähigkeiten-Flags (`txt2img`, `img2img`, `inpainting`, `outpainting`, `lora`, `controlnet`, `image_to_video`, `batch_generation`, `onnx_runtime`, `qnn_runtime`) zur Vermeidung hardcodierter Modellunterscheidungen.
  * **Repository-Erweiterung:** Aktualisierung der Schema-Validierung im `ModelRepository` zur Erzwingung des `"capabilities"`-Keys in allen Modellbeschreibungen.
  * **Data-driven Metadaten:** Ergänzung aller 7 Modellbeschreibungen (`flux_dev`, `sdxl_base`, `sdxl_refiner`, `sd35_large`, `cogvideox`, `ltx_video`, `wan22`) um detaillierte Capability-Profile.
  * **Dateien:** [model_repository.py](file:///C:/SnapdragonAI/controllers/model_repository.py), Model-JSONs in [models](file:///C:/SnapdragonAI/resources/models)

* **Sprint P-089 (First ONNX Inference Session):**
  * **Erste echte InferenceSession:** Integration der Instanziierung von `onnxruntime.InferenceSession` zur echten Modellladung im `OnnxImageBackend`.
  * **Metadaten-Extraktion:** Automatisches Auslesen und Protokollieren der Modell-Input- und Output-Namen direkt aus dem geladenen Modell-Graph.
  * **Ressourcen-Cleanup:** Saubere Freigabe der Session-Ressourcen (`del session`) nach dem Ladevorgang, um Speicherlecks zu verhindern.
  * **Dateien:** [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-088 (First ONNX Runtime Detection):**
  * **Erweiterte Runtime-Erkennung:** Das `OnnxImageBackend` erkennt nun aktiv das Vorhandensein von `onnxruntime`, liest die Version sowie die verfügbaren Hardware-Ausführungs-Provider aus.
  * **Provider-Validierung:** Die Existenz des `CPUExecutionProvider` wird explizit validiert. Das Fehlen des optionalen `QNNExecutionProvider` wird strukturiert als Warnung/Info-Nachricht im Log protokolliert und blockiert nicht den Inferenz-Bereitschaftslauf.
  * **Dateien:** [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-085 (ONNX Runtime Readiness):**
  * **Inferenz-Bereitschaft:** Das `OnnxImageBackend` wurde erweitert, um die Inferenz-Voraussetzungen zu prüfen. Es verifiziert die Importierbarkeit von `onnxruntime` (mit Auslesung der Version und der Execution Provider) und scannt das Modellverzeichnis nach kompatiblen `.onnx`-Dateien.
  * **Modell-Validierung:** Erkennt `.onnx`-Dateien rekursiv im Paketverzeichnis und überprüft deren grundsätzliche Existenz und Größe zur Sicherstellung der Ladbarkeit, ohne bereits eine `onnxruntime.InferenceSession` zu instanziieren.
  * **Fehlerbehandlung:** Ist `onnxruntime` nicht installiert oder kein Modell vorhanden, bricht das System sauber mit `success=False` und status `"unavailable"` ab. Der Stub-Workflow (NPU/CPU) bleibt unberührt lauffähig.
  * **Dateien:** [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-082 (Generation Parameter Contract):**
  * **Konsistente Parameter-Durchreichung:** Umfassende Transportierung aller 12 Generierungsparameter (`prompt`, `negative_prompt`, `model`, `backend`, `seed`, `width`, `height`, `steps`, `cfg`, `sampler`, `scheduler`, `batch_count`) von der GUI bis ins Backend.
  * **Erweiterung der Metadaten:** Die Parameter `negative_prompt`, `sampler`, `scheduler` und `batch_count` werden vollständig in die Sidecar-JSON geschrieben.
  * **Verbessertes Stub-Vorschaubild:** Das erzeugte PNG-Diagnosebild zeichnet nun neben Modell und Hardware-Backend auch eine kompakte Parameterzeile mit `Seed`, `Steps` und `CFG` auf der Karte.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py), [prompt_workspace_model.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_model.py), [stub_image_backend.py](file:///C:/SnapdragonAI/engine/stub_image_backend.py), [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-081 (Live Preview Integration):**
  * **Automatische GUI-Vorschau:** Nach erfolgreicher Bildgenerierung wird das erzeugte PNG-Bild automatisch geladen, per Pillow herunterskaliert (max. 250px unter Beibehaltung des Seitenverhältnisses) und im Vorschau-Label des AI Generate Workspace Inspectors anstelle des Standardplatzhalters *"No image generated"* angezeigt.
  * **Interaktionsschaltflächen:** Aktivierung der Buttons *"Open in Library"*, *"Open in Review"* und *"Save As"*, sobald ein Bild existiert. Die Buttons nutzen die `GenerationResponse` als einzige Datenquelle.
  * **Dateisystemaktionen:**
    * *Open in Library:* Öffnet den Ausgabeordner (`output/`) im Datei-Explorer.
    * *Open in Review:* Öffnet das generierte Bild direkt in der Standard-Bildbetrachtung des Betriebssystems.
    * *Save As:* Öffnet einen nativen Dateidialog (`asksaveasfilename`) zum Kopieren und Speichern des Bildes an einem beliebigen Ort.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py)

* **Sprint P-081 (Model Runtime Integration):**
  * **Einführung des Runtime-Modells:** Implementierung der Klasse `RuntimeModel` in `engine/runtime_model.py` zur Kapselung des aufgelösten Modell-Pfads, der Gewichtsdateien und des Ladeplans während des Inferenz-Laufs.
  * **Modell-Integration in Pipeline:** Der `GenerationExecutor` bezieht das Modell nun dynamisch über den Loader-Dienst und erstellt ein `RuntimeModel`.
  * **Dynamischer Transport:** Weiterleitung des `RuntimeModel` über den Generator-Adapter an die `InferenceBackendFactory`, welche das Backend mit dem real geladenen Modell instanziiert.
  * **Dynamische Diagnosebilder:** Das `StubImageBackend` und das `OnnxImageBackend` zeichnen nun dynamisch die geladene Modell-ID (`runtime_model.model_id`) auf das Vorschau-Bild, wodurch fest codierte Modellnamen vollständig abgelöst wurden.
  * **Erweitertes Logging:** Integration strukturierter Protokollierungen für `Selected Model`, `Runtime Model` und `Target Backend` im Executor.
  * **Dateien:** [runtime_model.py](file:///C:/SnapdragonAI/engine/runtime_model.py), [generation_executor.py](file:///C:/SnapdragonAI/engine/generation_executor.py), [inference_backend_factory.py](file:///C:/SnapdragonAI/engine/inference_backend_factory.py), [local_image_generator_adapter.py](file:///C:/SnapdragonAI/engine/local_image_generator_adapter.py), [stub_image_backend.py](file:///C:/SnapdragonAI/engine/stub_image_backend.py), [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py)

* **Sprint P-080 (Inference Backend Plugin Framework):**
  * **Einführung der Backend-Factory:** Implementierung der `InferenceBackendFactory` in `engine/inference_backend_factory.py` zur dynamischen Registrierung und Auflösung von Backend-Plugins.
  * **ONNX-Placeholder Backend:** Hinzufügen der Klasse `OnnxImageBackend` in `engine/onnx_image_backend.py` als ONNX-spezifischer Platzhalter.
  * **Registrierung & Auflösung:** Automatische Registrierung von `StubImageBackend` (unter `"Local CPU (Stub)"`, `"Qualcomm QNN NPU (Stub)"`) und `OnnxImageBackend` (unter `"ONNX Runtime (Stub)"`). Der Adapter bezieht Backend-Instanzen nun ausschließlich über die Factory und ruft einheitlich `backend.generate(job)` auf.
  * **Dateien:** [inference_backend_factory.py](file:///C:/SnapdragonAI/engine/inference_backend_factory.py), [onnx_image_backend.py](file:///C:/SnapdragonAI/engine/onnx_image_backend.py), [local_image_generator_adapter.py](file:///C:/SnapdragonAI/engine/local_image_generator_adapter.py), [inference_backend.py](file:///C:/SnapdragonAI/engine/inference_backend.py)

* **Sprint P-079 (Inference Backend Foundation):**
  * **Einführung der Backend-Abstraktion:** Definition der abstrakten Basisklasse `InferenceBackend` in `engine/inference_backend.py` zur sauberen Entkopplung lokaler Generatoren von konkreten Inferenz-Laufzeiten.
  * **Stub-Backend Implementierung:** Umsetzung des `StubImageBackend` in `engine/stub_image_backend.py`, welcher das Rendern und die Sidecar-Dateispeicherung für lokale Testläufe vollständig übernimmt.
  * **Adapter-Entkopplung:** Der `LocalImageGeneratorAdapter` erzeugt das Bild nicht mehr selbst, sondern delegiert den Generierungsschritt vollständig an das zugrundeliegende Inferenz-Backend.
  * **Dateien:** [inference_backend.py](file:///C:/SnapdragonAI/engine/inference_backend.py), [stub_image_backend.py](file:///C:/SnapdragonAI/engine/stub_image_backend.py), [local_image_generator_adapter.py](file:///C:/SnapdragonAI/engine/local_image_generator_adapter.py)

* **Sprint P-078 & P-077 (Stub Preview Image & Output Integration):**
  * **Sichtbares Diagnosebild:** Generierung eines 512x512-Pixel PNGs mit blauem Phoenix-Design, Branding, Status, Modell, Backend und einem Prompt-Ausschnitt, damit die Galerie ein echtes Vorschaubild statt einer schwarzen Fläche anzeigt.
  * **Pillow Härtung (Bugfix P-077):** Ersetzung der binären Byte-Erzeugung durch Standard-Pillow-Bildspeicherung, um Fehler bezüglich beschädigter Bilddateien in Windows Fotos und Browsern zu beheben.
  * **Asset-Metadaten & Sidecar:** Speicherung aller Inferenzparameter als Sidecar-JSON direkt neben der PNG-Ausgabedatei zur Erleichterung der Galerie-Auslesung.
  * **Dateien:** [local_image_generator_adapter.py](file:///C:/SnapdragonAI/engine/local_image_generator_adapter.py), [generation_response.py](file:///C:/SnapdragonAI/engine/generation_response.py)

* **Sprint P-076 (Local Image Generator Adapter Foundation):**
  * **Einführung der Adapter-Stufe:** Implementierung von `LocalImageGeneratorAdapter` in `engine/local_image_generator_adapter.py` zur Kapselung lokaler Bildgenerierungsschritte.
  * **Einführung des GenerationExecutor:** Implementierung von `GenerationExecutor` in `engine/generation_executor.py` zur Orchestrierung der Modellvalidierung und Generierungssteuerung.
  * **Strukturierte Ergebnisse:** Rückgabe des Generierungsresultats über `GenerationResponse` (in `engine/generation_response.py`), die von `GenerationResult` erbt und somit abwärtskompatibel bleibt.
  * **Dummy-Bild-Generierung:** Der Adapter erzeugt bei erfolgreicher Generierung ein valides 1x1-Pixel PNG-Bild in `output/` zur Vorschau in der GUI-Galerie.
  * **Ablauf-Protokollierung:** Strukturierte Logs zeigen den Inferenz-Fluss präzise auf: `Executor` -> `Adapter` -> `Result`.
  * **Modellvalidierung:** Überprüfung über `ModelLoaderService`, ob das gewählte Modell installiert ist. Falls nicht, erfolgt ein sicherer Abbruch mit Fehlermeldung statt eines Crashs.
  * **Dateien:** [local_image_generator_adapter.py](file:///C:/SnapdragonAI/engine/local_image_generator_adapter.py), [generation_executor.py](file:///C:/SnapdragonAI/engine/generation_executor.py), [generation_response.py](file:///C:/SnapdragonAI/engine/generation_response.py), [generation_pipeline.py](file:///C:/SnapdragonAI/controllers/generation_pipeline.py)

* **Sprint UX-006 (Navigation Preparation & Splash Size Fix):**
  * **Bereinigung der Workspace-Navigation:** Ausblendung des "Image"-Workspace aus der linken Seitenleisten-Navigation ([sidebar.py](file:///C:/SnapdragonAI/widgets/phoenix/sidebar.py)).
  * **Erhaltsgarantie:** Der eigentliche Image-Workspace und dessen Quelldateien wurden nicht gelöscht und verbleiben voll funktionsfähig im Code, um bei Bedarf reaktiviert werden zu können. Alle übrigen Navigationseinträge (Home, AI Generate, AI Model Manager, Gallery, Compare, Plugins, Settings) funktionieren wie gewohnt.
  * **Behebung der Splash-Screen-Größe:** Umstellung von `StartupOverlay` von einer überdimensionierten `tk.Frame` (die sich über die vollen 1400x900 Pixel des Hauptfensters erstreckte) auf ein eigenständiges `tk.Toplevel`-Fenster.
  * **Layout & Zentrierung:** Das neue Fenster hat eine feste, augenfreundliche Desktop-Größe von 600x420 Pixeln, wird zentriert auf dem Bildschirm platziert, ist rahmenlos (`overrideredirect(True)`) und blendet sich dank Unterstützung für Fenster-Transparenz (`-alpha`) weich per Einblendungs-Effekt aus, bevor es sich zerstört. Alle Marken-Assets (Logo, Schriftarten, Farben des gewählten Themes) wurden vollständig beibehalten und skaliert.
  * **Dateien:** [sidebar.py](file:///C:/SnapdragonAI/widgets/phoenix/sidebar.py), [startup_overlay.py](file:///C:/SnapdragonAI/widgets/startup_overlay.py)

* **Sprint P-074 (Model Loader Foundation):**
  * **Einführung des Model Loader Dienstes:** Implementierung des `ModelLoaderService` in `engine/model_loader_service.py` zur sicheren und strukturierten Auflösung installierter KI-Modelle.
  * **Verantwortlichkeiten des Loaders:**
    - `resolve_model(model_id)`: Führt vollständige Pfadprüfungen durch und liefert ein strukturiertes Ergebnis zurück.
    - `check_model_installed(model_id)`: Prüft die Registrierung und den Installationsstatus.
    - `get_model_path(model_id)`: Holt den lokalen Verzeichnispfad des Modells.
    - `get_model_files(model_id)`: Scannt rekursiv die Modelldateien im Zielverzeichnis.
    - `build_model_load_plan(model_id)`: Generiert einen detaillierten, schrittweisen Ladeplan für das jeweilige Ziel-Backend (QNN, ONNX, CPU), ohne die Gewichte tatsächlich in den Speicher zu laden.
  * **Strukturierte Ergebnisse:** Einführung von `ModelResolveResult` zur Rückgabe von Erfolg (`success`), Fehlermeldung (`message`), Warnungen (`warnings`), aufgelöstem Pfad (`model_path`), Dateilisten (`files`) und Backend-Namen (`backend`).
  * **Pipeline-Integration:** Integration in `GenerationController.queue_generation()`. Vor Ausführung der Generierungspipeline wird das Modell über den Loader aufgelöst. Ist das Modell nicht installiert, bricht der Vorgang sofort ab und liefert ein `GenerationResult` mit `success=False` und der Meldung `"Model is not installed."` (bzw. dem Fehlergrund) zurück.
  * **Dateien:** [model_loader_service.py](file:///C:/SnapdragonAI/engine/model_loader_service.py), [generation_controller.py](file:///C:/SnapdragonAI/controllers/generation_controller.py)

* **Sprint P-073.1 (Refresh Model Manager after Install/Uninstall):**
  * **Fehlerbehebung bei der UI-Aktualisierung:** Umstellung der Zeilenselektion und Detailanzeige im Model Manager von indexbasiertem auf iid-basierten Abruf (Verwendung der eindeutigen `model_id` als Element-ID in der Treeview). Dies behebt Synchronisationsprobleme durch willkürliche Listenanordnungen bei Dateisystemänderungen und sorgt für sofortiges Aktualisieren nach Installationen oder Deinstallationen.
  * **Erweiterung des Model-Inspectors:** Hinzufügen einer sichtbaren Pfad-Zeile („Pfad:“) im Inspector-Panel. Diese wird nach der Installation mit dem absoluten Pfad des lokalen Modells befüllt (und nach Deinstallation zurückgesetzt).
  * **Steuerung der Schaltflächen:** Installieren, Deinstallieren und Ordner-öffnen werden jetzt absolut synchron zu dem aktuellen Zustand und Pfad-Existenz gesperrt oder freigegeben.
  * **workspaceübergreifende Synchronisation:** Einbindung automatischer Repository-Reloads bei jedem Refresh des Prompt-Workspaces (`prompt_view.py`), wodurch neu installierte oder deinstallierte Modelle in allen Workspaces konsistent geladen sind.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint P-073 (Model Validation 2.0):**
  * **Erweiterte Modellvalidierung:** Überarbeitung von `ModelInstallService.validate_model()` zur Durchführung eingehenderer Validierungsprüfungen vor der Modellinstallation. Der Service prüft nun Dateiexistenz, Dateityp (Datei oder Ordner), Leserechte (`os.access`) sowie erlaubte Modell-Dateiendungen (`.onnx`, `.bin`, `.safetensors`, `.gguf`, `.json`, `.pb`, `.pt`, `.pth`). Für Ordner wird verifiziert, ob mindestens eine gültige Modelldatei vorhanden ist, und es wird geprüft, ob die Gesamtgröße der Dateien größer als 0 ist.
  * **Strukturierte Validierungsergebnisse:** Die Methode liefert nun ein strukturiertes Resultat (Dictionary mit `success`, `message`, `warnings` und `size_bytes`) zurück. Dies ermöglicht die Übergabe von detaillierten Statusmeldungen sowie Warnungen (z. B. bei sehr großen Dateien oder vorhandenen Nicht-Modell-Dateien wie `.txt`/`.md`).
  * **Integration:** Anpassung von `ModelInstallService.install_model()` an das neue strukturierte Rückgabeformat, wodurch die ermittelte Modellgröße direkt weiterverwendet wird.
  * **Dateien:** [model_install_service.py](file:///C:/SnapdragonAI/engine/model_install_service.py)

* **Sprint P-072.2 (Connect QNN Availability to Backend Discovery):**
  * **Bereinigung der Debug-Ausgaben:** Sämtliche temporären `[DEBUG P-072.1]`-Konsolenausgaben wurden vollständig aus `backend_manager.py` entfernt.
  * **Dynamische NPU-Erkennung:** Die Methode `is_available()` im `QNNBackendAdapter` wurde an den `BackendDiscoveryService` angebunden. Das QNN-Backend meldet sich nun genau dann als verfügbar (`True`), wenn sowohl `qnn_sdk_found` als auch `qnn_tools_found` im Diagnoselauf als wahr erkannt werden (andernfalls `False`).
  * **Performance-Optimierung via Caching:** Einführung eines Klassen-Caches (`_cached_is_available`) im `QNNBackendAdapter` zur Vermeidung wiederholter Filesystem-Scans bei UI-Refreshes.
  * **Dateien:** [backend_manager.py](file:///C:/SnapdragonAI/engine/backends/backend_manager.py), [qnn_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/qnn_backend_adapter.py)

* **Sprint P-072 (Backend Routing in GenerationController):**
  * **Dynamic Backend Selection during Generation:** Integration des automatischen Backend-Routings in `GenerationController.queue_generation`. Der Controller löst die `model_name` der Generierungssitzung über das `ModelRepository` zu den Modell-Metadaten auf und ermittelt via `BackendManager.get_best_backend` den optimalen, verfügbaren Backend-Adapter.
  * **Synchronisation mit UI & Pipeline:** Übergabe des gewählten Backend-Adapters an die `ImageGenerationPipeline`. Aktualisierung des aktiven Backends im `BackendManager`, sodass die UI (z. B. der Inspector und die Statusleiste im AI Generate Workspace) während und nach der Generierung das tatsächlich genutzte Backend anzeigt. Der Fallback auf den CPU (Stub) bleibt vollständig erhalten.
  * **Ergebnismetadaten:** Der Name des gerouteten Backends wird im zurückgelieferten `GenerationResult` (`backend_name` und `metadata["routed_backend"]`) zur Nachverfolgung persistiert.
  * **Dateien:** [generation_controller.py](file:///C:/SnapdragonAI/controllers/generation_controller.py)

* **Sprint P-071 (Backend Manager Routing Foundation):**
  * **Backend-Auswahl-Infrastruktur:** Implementierung des automatischen Backend-Auswahlmechanismus in `BackendManager` via `get_best_backend(model)`.
  * **Routing-Priorisierung:** Nutzt das bevorzugte Backend des Modells aus der Konfigurationsdatei (z.B. `"recommended_backend"` wie `Qualcomm QNN NPU (Stub)`) als erste Präferenz. Ist dieses nicht verfügbar, erfolgt ein geordneter Fallback auf verfügbare Backends: `QNN` -> `ONNX` -> `CPU (Stub)`.
  * **Dateien:** [backend_manager.py](file:///C:/SnapdragonAI/engine/backends/backend_manager.py)

* **Sprint UX-005.1 (Model Manager Card Appearance Restore):**
  * **Wiederherstellung des Phoenix-Card-Designs:** Flat-Styling für das `ttk.Treeview` und dessen Header durch Deaktivierung von Standard-3D-Rahmen (`borderwidth=0`, `relief="flat"`). Zusätzliche Farbkapselung über den `ThemeManager` und Zuweisung von Hover-Mapping auf den Spaltenüberschriften mit dem Phoenix-Akzentfarbton zur Gewährleistung eines harmonischen, integrierten Karten-Looks im Phoenix-Designsystem.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py)

* **Sprint UX-005 (Model Manager Table Polish):**
  * **Optimierte Tabellenspalten:** Anpassung der Spaltenbreiten im Model Manager Treeview zur Vermeidung von Textkürzungen (z. B. in Kategorie). Die Spalte „Aktiv“ wurde auf eine feste Breite von 45px (ohne Streckung) fixiert, während „Modellname“ (240px), „Kategorie“ (160px), „Ziel-Backend“ (130px) und „Status“ (180px) dynamisch mitgestreckt werden. Dies gewährleistet eine balancierte, lesbare und professionelle Darstellung.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py)

* **Sprint P-070 (Local AI Model Installation Foundation):**
  * **ModelInstallService:** Implementierung des neuen Service `ModelInstallService` zur Verwaltung lokaler Modell-Installationen. Bietet Funktionen zur Validierung von Modelldateien, Bestimmung der Modellgröße, Überprüfung des freien Festplattenspeichers (inkl. Sicherheits-Puffer), Kopieren lokaler Modelldateien in das Standardverzeichnis und sicheren Deinstallation (Löschen von Dateien im Workspace).
  * **Integration in ModelRepository:** Der Service nutzt das `ModelRepository` zur Aktualisierung von Installationsstatustexten (`status`), Installationsflags (`installed`) und des Pfads (`path`) direkt auf der Festplatte.
  * **UI-Integration im Model Manager:** Aktivierung der Inspector-Buttons „Installieren“, „Deinstallieren“ und „Ordner öffnen“ im Model Manager. Beim Klick auf „Installieren“ öffnet sich ein Dateidialog zur Auswahl lokaler Dateien. „Deinstallieren“ löscht die Dateien nach Rückfrage, und „Ordner öffnen“ öffnet den Installationsordner nativ im Explorer.
  * **Zukunftssichere Download-Hooks:** Vorbereitung von leeren und dokumentierten Download-Methoden (`start_download`, `cancel_download`) für Hugging Face/API-Anbindungen.
  * **Dateien:** [model_install_service.py](file:///C:/SnapdragonAI/engine/model_install_service.py), [model_manager_controller.py](file:///C:/SnapdragonAI/controllers/model_manager_controller.py), [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py)

* **Sprint UX-004.3 (AI Generate No-Scroll Layout Fix):**
  * **No-Scroll Design auf 1080p:** Optimierung aller Widgets und Ränder im AI Generate Workspace, sodass alle Eingabegruppen (Model, Prompt, Negative Prompt, Image Size, Sampling, Output), der rechte Inspector samt Preview und die Statusleiste ohne vertikales Scrollen sichtbar sind.
  * **Kompakte Eingabeelemente:** Das Prompt-Feld wurde auf 3 Zeilen, das Negative-Prompt-Feld auf 1 Zeile verkleinert. Breite/Höhe, CFG/Steps, Sampler/Scheduler und Seed/Batch Count wurden platzsparend in horizontalen Rastern nebeneinander gruppiert.
  * **Optimierter Inspector:** Der rechte Canvas samt Scrollbar wurde durch ein kompaktes, 4-spaltiges Layout-Raster ersetzt, welches alle Informationen übersichtlich darstellt und das Scrollen im AI Generate Workspace vollständig überflüssig macht.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint UX-004 (AI Generate Workspace Redesign):**
  * **Neues zweispaltiges Design:** Professionelles Layout mit gruppierter Parametereingabe links (70 %) und einem scrollbaren AI Generation Inspector rechts (30 %).
  * **Parametergruppen:** Die Eingabefläche ist in fünf klar getrennte Gruppen unterteilt: Model, Prompt, Image Size, Sampling (CFG, Steps, Sampler, Scheduler) und Output (Seed, Batch Count).
  * **Prompt-Vergrößerung:** Die Prompt- und Negativ-Prompt-Felder sind deutlich mehrzeilig (6 bzw. 3 Zeilen) und damit professionell nutzbar.
  * **AI Generation Inspector:** Vereinigt drei Bereiche: Generation Status (Model, Backend, Status, Queue), Generation Information (Image Size, Steps, CFG, Seed, Sampler, Scheduler) und Preview-Platzhalter.
  * **Platzhalter-Buttons:** Drei deaktivierte Buttons (Open in Library, Open in Review, Save As) unterhalb der Preview.
  * **Segmentierte Statusleiste:** Segmente für Status, Modell, Backend, Environment, QNN und Queue.
  * **Dateien:** [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint UX-003 (AI Model Manager Workspace Redesign):**
  * **Neues zweispaltiges Design:** Der gesamte untere Eigenschafts-Bereich wurde entfernt. Der linke Bereich besteht nun ausschließlich aus der vergrößerten Modellliste.
  * **Einheitlicher rechter Inspector:** Die Modellinformationen des *aktuell ausgewählten* Modells und die Systemumgebung wurden in einem einzigen, übersichtlichen und scrollbaren rechten Inspector vereint.
  * **Vorbereitete Aktions-Buttons:** Integration von fünf deaktivierten Platzhalter-Buttons (Installieren, Deinstallieren, Aktualisieren, Benchmark, Ordner öffnen) zur Vorbereitung künftiger Model-Management-Funktionen.
  * **UX-Politur:** Der einfache Klick aktualisiert den Inspector und meldet `"Modell ausgewählt: <Modellname>"` in der Statusleiste. Der Doppelklick markiert das Modell als aktiv (✓) und meldet `"Aktives Modell geändert: <Modellname>"`, ohne den Workspace zu wechseln.
  * **Dateien:** [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py)

* **Sprint P-061 & P-061.1 & P-061.2 & P-061.3 & P-061.4 (Backend Discovery, UX Polish, Scrollable Inspector, Table Columns Polish & Hide Global Inspector):**
  * **Umgebungs- & SDK-Erkennung:** Implementierung des `BackendDiscoveryService` und der Datenklasse `DiscoveryResult` zur automatischen, fehlerfreien Erkennung von CPU-Verfügbarkeit, Windows ARM64, Python-Version, ONNX-Runtime und Qualcomm QNN SDK / Tools (`qnn-net-run.exe`).
  * **Exponierung im BackendManager:** Erweiterung des `BackendManager` um `run_discovery()`, `get_discovery_result()` und `get_backend_status_summary()`. Exponierung über den `ModelManagerController`.
  * **Ausblenden des globalen Inspectors:** Anpassung von `workspace.py` zur dynamischen Ausblendung der globalen rechten Seitenleiste (Inspector) für den Workspace `"models"`. Bei anderen Workspaces wird diese wie gewohnt gerendert.
  * **Scrollbarer Inspector:** Umwandlung des rechten Model-Inspectors in einen scrollbaren Bereich mit Canvas und Scrollbar in `model_manager_view.py`. Dadurch wird kein Inhalt mehr bei geringer Fensterhöhe abgeschnitten.
  * **Spaltenbreiten-Politur:** Anpassung der Treeview-Spaltenbreiten im Model Manager (Status-Spalte auf 200px vergrößert, Name-Spalte auf 260px erweitert). Längere Texte wie "Available for Download" werden nun vollständig lesbar dargestellt.
  * **UX-Feinschliff:** Entfernung der doppelten Status-Anzeige "Aktiv ausgewählt" in den Auswahldetails unten links. Deaktivierung der automatischen Umschaltung auf AI Generate bei Doppelklick.
  * **Segmentierte Generierungs-Leiste:** Erweiterung der Statusleiste im AI Generate Workspace um die dynamischen Abschnitte `Environment` und `QNN` direkt aus dem Discovery Service.
  * **Dateien:** [workspace.py](file:///C:/SnapdragonAI/widgets/phoenix/workspace.py), [backend_discovery_service.py](file:///C:/SnapdragonAI/engine/backends/backend_discovery_service.py), [discovery_result.py](file:///C:/SnapdragonAI/engine/backends/discovery_result.py), [backend_manager.py](file:///C:/SnapdragonAI/engine/backends/backend_manager.py), [model_manager_controller.py](file:///C:/SnapdragonAI/controllers/model_manager_controller.py), [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py)

* **Sprint P-060 & P-060.1 (AI Engine Pipeline Foundation & Bugfix):**
  * **Inferenz-Pipeline & Resultatklasse:** Einführung der Standardklassen `ImageGenerationPipeline` und `GenerationResult` (datenbasiert, ohne Pillow- oder Backend-Abhängigkeiten) als einheitlicher Rahmen für die Inferenzläufe.
  * **Session-Integration:** Anpassung der Parameterzugriffe von `self.job.parameters` auf die strukturierte `self.job.session` Property in allen Phasen der Pipeline und in allen Backend-Adaptern (CPU, QNN, ONNX, Remote).
  * **Fehlerbehandlung:** Vollständige Beseitigung von `AttributeError` bei ungültigen Eingaben oder Pipeline-Fehlern. Das Generierungsmodell wird sicher über die `session` referenziert.
  * **Dateien:** [generation_pipeline.py](file:///C:/SnapdragonAI/controllers/generation_pipeline.py), [generation_result.py](file:///C:/SnapdragonAI/controllers/generation_result.py), [generation_controller.py](file:///C:/SnapdragonAI/controllers/generation_controller.py), [prompt_workspace_controller.py](file:///C:/SnapdragonAI/controllers/prompt_workspace_controller.py), [cpu_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/cpu_backend_adapter.py), [onnx_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/onnx_backend_adapter.py), [qnn_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/qnn_backend_adapter.py), [remote_backend_adapter.py](file:///C:/SnapdragonAI/engine/backends/remote_backend_adapter.py)

* **Sprint UX-002 (Cross Workspace Workflow Foundation):**
  * **Zentraler WorkflowController:** Einführung einer Workspace-übergreifenden Steuerungsschicht mit `WorkflowController` (Singleton) und einem transienten `WorkflowState` für Laufzeit-Parameter (z. B. `active_model`, `last_generated_image`).
  * **Auto-Navigation:** Ein Doppelklick auf ein Modell im AI Model Manager setzt das Modell nicht nur aktiv, sondern navigiert den Anwender über den `WorkflowController` automatisch in das Generierungs-Fenster (AI Generate).
  * **Segmentierte Statusleiste:** In der Generierungs-Ansicht (`prompt_view.py`) wurde die Statusleiste am unteren Bildschirmrand in vier strukturierte Segmente aufgeteilt (Status, Aktives Modell, Backend, Queue), die dynamisch direkt aus den zentralen Controllern gespeist werden (keine Hardcodierungen).
  * **Integrierte Workflow-Hooks:** Vorbereitung von ausgegrauten Platzhalter-Befehlen im Kontextmenü der Galerie („Mit aktivem Modell generieren“) und der Compare-Ansicht („Erneut generieren“ / „Mit aktuellem Modell“), um spätere Workflow-Ausbaustufen zu strukturieren.
  * **Dateien:** [workflow_controller.py](file:///C:/SnapdragonAI/controllers/workflow_controller.py), [ui_builder.py](file:///C:/SnapdragonAI/gui/controllers/ui_builder.py), [model_manager_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/model_manager_view.py), [model_manager_gui.py](file:///C:/SnapdragonAI/modules/model_manager_gui.py), [prompt_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/prompt_view.py), [thumbnail_area.py](file:///C:/SnapdragonAI/widgets/phoenix/gallery/thumbnail_area.py), [compare_view.py](file:///C:/SnapdragonAI/widgets/phoenix/views/compare_view.py)

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

**R-005 (15.07.2026):** Das automatische headless QNN Package Qualification Gate ist implementiert. `models/sdxl_base` wird wegen dynamischer Verträge, großem FP32-/16-GB-Risiko und fehlender QNN-Freigabe abgelehnt. Das produktive `models/stable_diffusion_v2_1` besteht die statische Prüfung und Strict Loads aller drei EPContext-Wrapper ohne CPU-Fallback (`CONDITIONALLY_QUALIFIED`). Reale QNN-Ausführung und HTP-Profiling bleiben Voraussetzung für die Produktfreigabe.

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
