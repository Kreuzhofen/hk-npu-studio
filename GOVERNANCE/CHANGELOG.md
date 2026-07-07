# Projekt-Changelog – Snapdragon AI Studio

Alle signifikanten Änderungen und Veröffentlichungen dieses Projekts werden in diesem Dokument festgehalten. Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [2.0 Preview] – 2026-07-07 (Laufende Phoenix-Entwicklung)

### Hinzugefügt
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
