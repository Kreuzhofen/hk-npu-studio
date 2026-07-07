# Projektstatus – Snapdragon AI Studio

**Stand:** 07.07.2026
**Zweig:** `feature/phoenix-rebuild`
**Zielplattform:** Windows 11 ARM64 (Qualcomm Snapdragon X NPU via QNN)

---

## 1. Aktueller Status & Letzte Änderungen

Am **07.07.2026** wurden folgende Sprints abgeschlossen:

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
