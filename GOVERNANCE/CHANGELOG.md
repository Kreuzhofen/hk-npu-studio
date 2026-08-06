# Projekt-Changelog – Snapdragon AI Studio

Alle signifikanten Änderungen und Veröffentlichungen dieses Projekts werden in diesem Dokument festgehalten. Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [2.0 RC1.2] – 2026-08-05

### Added

- Official corporate logo assets finalized.
- Added automatic GitHub Light/Dark theme logo switching.
- Updated README branding with responsive <picture> support.
- Improved GitHub, Desktop and Mobile logo compatibility.
- Redesigned README header layout to place the logo side-by-side with the title, vertically centered, forming a single brand unit.
- Fixed the license badge by replacing the dynamic "license not specified" badge with the correct static MIT license badge.














## [2.0 RC1.1] – 2026-08-04 (RC1.1 Installer & Acceptance Test Suite Pass)


### Hinzugefügt
* Dediziertes, automatisiertes Akzeptanztest-Skript unter `tools/rc1_acceptance_test.py` implementiert, um den gesamten Build- und Installationsprozess zu validieren.

### Prüfung
* **Automatisierter Release-Smoke-Test erfolgreich abgeschlossen (PASS):**
  * PyInstaller-Build (`build_app.py`) und Inno Setup-Installer-Build (`build_installer.py`) kompiliert.
  * Silent-Installation (`/VERYSILENT`) durchgeführt.
  * Start der installierten Desktop-Anwendung verifiziert und Log-Erstellung validiert.
  * `QNNExecutionProvider` in ONNX Runtime erfolgreich registriert (kein Fehler 126).
  * SMP-Modellkatalog erkennt Modelle (SD1.5, SD2.1 und SDXL) ordnungsgemäß.
  * ControlNet Drag & Drop sowie Canny UI-Steuerelemente im Phoenix-Design verifiziert.
  * Vollständige Inferenz-Generierung (SD1.5 mit Euler und SD2.1 mit DDIM) lokal durchgeführt.
  * Bildgalerie zeigt die neu generierten Bilddateien korrekt an.
  * Silent-Deinstallation und erneute Silent-Installation mit anschließender Generierungs-Verifizierung erfolgreich bestanden.

## [2.0 RC1] – 2026-08-04 (RC1 Auto Repair & Test Suite Stabilization)

### Behoben
* Tcl/Tk cross-interpreter pollution in `test_all_phoenix_pages_are_language_pure_at_runtime` behoben. `ThumbnailProvider` mit einer `<Destroy>`-Event-Bindung und einer `cleanup()`-Methode ausgestattet, um Threading-Ressourcen, `after`-Handles und `PhotoImage`-Caches beim Zerstören von Widgets zuverlässig freizugeben.
* Import-basierte Test-Pollution in `test_gallery.py` behoben. `PhoenixGalleryView` wird nun auf Modulebene statt innerhalb der Testmethode importiert, und der `ThumbnailProvider`-Patch wurde auf das lokale Modul `widgets.phoenix.gallery.thumbnail_area` eingegrenzt, wodurch das dauerhafte Einnisten von Mock-Objekten in `sys.modules` verhindert wird.
* Fehlerbehandlung in `configure_phoenix_styles` (`widgets/phoenix/theme.py`) durch explizite Prüfungen auf das Vorhandensein und die Gültigkeit des Standard- bzw. übergebenen Tk-Hauptfensters (Root) abgesichert, um `TclError`s beim Beenden von Tests oder Zerstören von GUI-Instanzen zu verhindern.

### Prüfung
* Gesamte Testsuite (318 Tests) erfolgreich durchlaufen.
* Modulkompilierung aller betroffenen Dateien über `py_compile` erfolgreich verifiziert.

## [2.0 RC1] – 2026-08-01 (CPU SDXL Generation Pipeline Fix)

### Behoben
* Kompatiblen UNet-Modellgraphen (`unet_model_mismatched.onnx` / 4.05 MB) als Standard `model.onnx` im `sdxl_base/unet`-Verzeichnis wiederhergestellt, um den Fehler mit nicht übereinstimmenden Tensor-Initialisierer-Offsets und der resultierenden Kachelungs-Struktur (Tiled/Grid-Pattern) in den Bildausgaben vollständig zu beheben.
* Dynamische Datentyp-Konvertierung in `unet_service.py` verfeinert, um `timestep` als Skalar (`shape=[]`) oder als 1D-Tensor (`shape=[1]`) mit dem exakt vom ONNX-Modell deklarierten Typ (`float32` oder `int64`) an die Inferenzsitzung zu übergeben, wodurch type mismatch Fehler behoben wurden.
* Dynamische Datentyp-Auflösung in `vae_decoder_service.py` integriert, um den erwarteten Datentyp des VAE-Eingangstensors dynamisch auszulesen, anstatt ihn hart auf `float32` festzulegen.

### Prüfung
* CPU SDXL-Pipeline erzeugt ein korrektes, kachelungsfreies End-to-End-Generierungsbild (Bergstraße mit Bergen und roten Strichen).
* Gesamte Testsuite (203 Tests) erfolgreich durchlaufen.
* Modulkompilierung über `py_compile` erfolgreich geprüft.

## [2.0 RC1] – 2026-08-01 (Test Suite Fixes / Diagnostics Robustness)

### Behoben
* Diagnoseausgabe für ONNX-Sitzungen in `CpuPipelineDiagnostics` robuster gestaltet, sodass das Fehlen des optionalen Attributs `type` bei `_TensorInfo`-Objekten per `getattr` abgefangen wird.
* Test-Mock-Klasse `_TensorInfo` in `test_cpu_pipeline_diagnostics.py` um das Attribut `type` erweitert, um dem realen ONNX-Interface zu entsprechen.
* Test `test_session_factory_passes_only_configured_cpu_provider` an Pfadauflösung und CPU-spezifische Sitzungsoptionen angepasst.

### Prüfung
* Kompilierung aller betroffenen Module per `py_compile` erfolgreich.
* Gesamte Testsuite (278 Tests) erfolgreich durchlaufen.


## [2.0 RC1] – 2026-07-30 (Release Final Status/ControlNet Fix)

### Behoben
* Backendstatus der Generierungsseite aus der gespeicherten und aktiv gerouteten Provider-Auswahl abgeleitet; `CPU EP` ersetzt den irreführenden initialen Status `CPU (Stub)`.
* Expliziten `controlnet_enabled`-Zustand vom UI-Reiter über ViewModel, Session und Request bis zu Validierung und Sidecar-Metadaten geführt.
* Canny-Bildvalidierung wird ausschließlich bei tatsächlich aktiviertem ControlNet ausgeführt.

### Prüfung
* 25 gezielte Tests und 2 Subtests erfolgreich.
* Gesamtsuite: 277 Tests und 25 Subtests erfolgreich; der einzige zustandsabhängige Tk-Bildaudit wurde isoliert erfolgreich bestätigt.
* Produktkompilierung, isolierter ARM64-Build, Release-Smoke-Test und Controller-Smoke bis zum Pipeline-Eintritt erfolgreich.
* Keine Änderungen an ONNX Runtime, SDXL, Text Encodern, UNet, VAE, Scheduler, Modellpfaden oder Inferenz.

## [2.0 RC1] – 2026-07-30 (Model Path Resolution Hotfix)

### Behoben
* Modelldefinitionsverzeichnis und Installationswurzel im `ModelRepository` getrennt.
* Installationspfade werden aus Definition, konfigurierter `models_dir` und `config.MODELS_DIR` aufgelöst.
* Vorhandene lokale Modelle werden auch bei veralteten dist-Metadaten korrekt als installiert erkannt.

### Diagnose
* Vollständige Pfadsuche einschließlich Definitionsverzeichnis, Preferences-Datei, Standardwurzel, aller Kandidaten und erstem Treffer unter `[MODEL PATH]` protokolliert.
* Keine Änderungen an Inferenzlogik oder Execution Providern.
* 34 relevante Tests, Produktkompilierung, isolierter ARM64-dist-Build und Release-Smoke-Test erfolgreich.

## [2.0 RC1] – 2026-07-30 (CPU-SDXL-Diagnoseinstrumentierung)

### Diagnose
* SDXL-CPU-Pipelinephasen, Session-Erstellung, Text Encoder 1/2, Embeddings, Scheduler, Latents, einzelne Denoising-Schritte, VAE, Bildkonvertierung und Speichern mit Start, Ende, Dauer, Thread, Provider und Modellpfad instrumentiert.
* ONNX-Session- und `Session.Run`-Diagnose um Provider sowie deklarierte und tatsächliche Tensorformen ergänzt.
* Passiver 30-Sekunden-Watchdog für lang laufende `Session.Run`-Aufrufe und vollständige phasenbezogene Exception-Diagnose ergänzt.
* UI-Fortschrittsänderungen werden mit altem/neuem Wert und Pipelinephase protokolliert; die Fortschrittssteuerung selbst bleibt unverändert.

### Umfang
* Keine Änderung an Inferenzlogik, Modellen, Modellpfaden, Execution Providern, Fallbacks oder Generierungsergebnissen.

## [2.0 RC1] – 2026-07-30 (CPU Generation Hotfix)

### Behoben
* Erfolgreiche Mock-/Alpha-Fallbacks aus Text Encoder, UNet, VAE und ONNX-Bildergebnis entfernt.
* Unvollständige oder CPU-inkompatible Modellpakete werden vor der Inferenz abgewiesen und technisch protokolliert.
* Komponenten- und Sessionfehler liefern keinen Platzhalter und kein Erfolgsresultat mehr.
* Validiertes SDXL-ONNX-Paket für den Produktmodellwähler freigegeben und an `ONNX Runtime CPU` gebunden.
* Veraltete dreisprachige Alpha-Fallback-Erfolgsmeldung entfernt.

### Prüfung
* Zwei reale SDXL-Generierungen mit identischem Seed und unterschiedlichen Prompts liefen ausschließlich über `CPUExecutionProvider`.
* Text Encoder 1/2, UNet und VAE waren real; alle Mock-Flags waren `false`.
* Beide 512×512-Bilder haben unterschiedliche SHA-256-Werte und 236.907 unterschiedliche Pixel.
* 35 relevante Tests, Produktkompilierung und 704 identische Lokalisierungsschlüssel erfolgreich geprüft.

## [2.0 RC1] – 2026-07-30 (Execution Provider Hotfix)

### Behoben
* Gespeicherte CPU-/QNN-Auswahl an Backend-Routing und zentrale ONNX-Session-Erzeugung angebunden.
* Bedingungslose QNN-Priorisierung bei gewähltem `CPUExecutionProvider` entfernt.
* Startdiagnose, Startseite und Dashboard zeigen den tatsächlich konfigurierten Provider statt eines statischen NPU-Status.
* Runtime-Bezeichnung wird aus den tatsächlich verwendeten Session-Providern abgeleitet.

### Prüfung
* CPU-Neustart meldet `CPUExecutionProvider`; reale SDXL-Generierung verwendete ausschließlich CPU-Sessions und erzeugte ohne Mock-/Alpha-Fallback ein Bild.
* QNN-Neustart meldet `QNNExecutionProvider`; reale SD-1.5-Generierung lief verifiziert auf Hexagon HTP ohne CPU-Fallback.
* 24 gezielte Tests sowie Produktkompilierung erfolgreich.

## [2.0 RC1] – 2026-07-29 (Generation Hotfix)

### Behoben
* Frühen `ModuleNotFoundError` beim direkten Start der isolierten QNN-Worker beseitigt; Projektpfad, Arbeitsverzeichnis und Worker-Umgebung werden vor Projektimporten korrekt gesetzt.
* Fehlendes oder ungültiges Worker-JSON sowie scheinbare Erfolge ohne Bilddatei werden fail-closed behandelt.
* stdout/stderr, Exit-Code, Befehl und technische Worker-Details werden protokolliert; die UI erhält einen lokalisierten Fehlertext ohne interne Details.

### Prüfung
* SD 1.5, SD 2.1 und ControlNet Canny erzeugten auf Qualcomm Hexagon HTP V73 jeweils gültiges JSON und ein 512×512-Bild, ohne CPU- oder Stub-Fallback.
* 18 relevante Tests und 3 direkte Worker-Vertragsprüfungen bestanden; Produktcode und 705 identische Lokalisierungsschlüssel geprüft.
* ARM64-dist und Installer erfolgreich neu gebaut und validiert; portable sowie isoliert installierte Diagnose beenden mit Exit-Code 0.

## [2.0 RC1] – 2026-07-29 (Localization Hotfix)

### Geändert
* Sprachneutrale kanonische Zustände für Prompt-, Batch-, Worker-, Queue- und Lifecycle-Abläufe eingeführt.
* Zentrale Laufzeitlokalisierung für deutsche, englische und spanische Status-/Enumvarianten ergänzt.
* Statusleiste, Plugin-/Jobkarten, Queue, Prompt-Inspector, Dashboard, Galerie und Vergleich an der UI-Grenze angebunden.
* Dynamische Fehlerpräfixe, Phasen, Fortschrittstexte und Backendstatus vereinheitlicht.
* Lokalisierungsvertrag auf 704 identische Schlüssel erweitert.

### Prüfung
* Vollständiger App-Start und dynamische Statuswechsel in Deutsch, Englisch und Spanisch erfolgreich.
* 27 relevante Tests und 9 Subtests bestanden; Produktcode vollständig kompiliert.
* Keine gemischten Bildschirme festgestellt.

## [2.0 RC1] – 2026-07-29 (Visual Localization Fix)

### Geändert
* Statischen Lokalisierungs-Audit auf Dialogargumente, Status-/Logpfade und nachträglich konfigurierte Widgettexte erweitert.
* View-Titel, Startoverlay, Import-/Batch-/Queue-Zustände und Hardware-/Cache-Meldungen vollständig lokalisiert.
* Plugin- und Bildformatdialoge sowie Download-, Modelllade-, ONNX- und QNN-Ergebnismeldungen vereinheitlicht.
* Rohe Modellbeschreibungen in KI-Generierung und Modellmanager durch lokalisierte Katalogtexte ersetzt.
* Sprachdateien auf 699 identische Schlüssel für Deutsch, Englisch und Spanisch erweitert.

### Prüfung
* Vollständiger Anwendungsstart für Deutsch, Englisch und Spanisch erfolgreich.
* Alle neun Phoenix-Seiten, Haupt-/Kontextmenüs, Dialogpfade, Modelltexte und Installerdefinition geprüft: 0 gemischte Oberflächen, 0 fremdsprachige UI-Texte.
* 54 relevante Tests und 9 Subtests bestanden; Produktcode vollständig kompiliert.

## [2.0 RC1] – 2026-07-29 (Release Polish – Final)

### Geändert
* Linke Navigation mit 10–15 % größeren Icons und Texten sowie den finalen Bereichsfarben umgesetzt.
* Aktiver Menüpunkt färbt Text, Icon und Seitenindikator einheitlich in der Bereichsfarbe.
* Spanische Bezeichnungen für KI-Generierung und Modellmanager korrigiert.
* Status-Badges, Modellmanager-Detailfelder und alle Katalog-Modellbeschreibungen vollständig lokalisiert.
* Lokalisierungsvertrag auf 600 identische Schlüssel für Deutsch, Englisch und Spanisch erweitert.

### Prüfung
* 25 betroffene Navigations-, Lokalisierungs-, Modell-, Settings-, Vergleichs- und UX-Tests bestanden.
* Produktcode vollständig kompiliert; Kontextmenüs, Löschfunktionen und Bildvergleich regressionsgeprüft.
* Codesignierung und Veröffentlichung nicht durchgeführt.

## [2.0 RC1] – 2026-07-29 (Sprint 22 – Final Polish & UX Audit)

### Geändert
* Spanisch vollständig ergänzt; Deutsch, Englisch und Spanisch auf 577 identische Schlüssel und konsistente Platzhalter vereinheitlicht.
* Automatisches Lokalisierungs-Audit für Sprachdateien, Produktoberflächen und verbliebene deutsche Texte in Englisch/Spanisch ergänzt.
* Phoenix-Branding, Light-Theme-Settings-Icon, Kontraste, Terminologie und DPI-Darstellung nachgeschärft.
* Gemeinsames Kontextmenü für Texteingaben sowie einzelnes und bestätigtes vollständiges Löschen letzter Generierungen ergänzt.
* Bildvergleich als technischer Metadatenvergleich vereinfacht und um relevante Bild-, Datei- und Generierungsunterschiede erweitert.
* Inno-Setup-Installer auf Englisch, Deutsch und Spanisch lokalisiert.

### Prüfung
* 78 betroffene Tests und 9 Subtests bestanden; Produktcode vollständig kompiliert.
* ARM64-Anwendung und Installer gebaut und validiert; Installation, installierte Startdiagnose und Deinstallation erfolgreich.
* Codesignierung und Veröffentlichung nicht durchgeführt.

## [2.0 RC1] – 2026-07-29 (Release-Vorbereitung)

### Geändert
* Reproduzierbare PyInstaller-/Inno-Setup-Pipeline für native Windows-ARM64-Artefakte eingerichtet.
* Release-Metadaten, Ressourcen und veränderliche Benutzerdaten für installierte Builds getrennt.
* Lokale Modellpfade, Laufzeitlogs und Python-Cachedateien aus Release-Paketen ausgeschlossen.
* SHA-256-Artefaktmanifest und automatisierbarer Diagnose-Smoke-Test ergänzt.

### Prüfung
* ARM64-PE-Header und Version geprüft; portable und installierte Diagnose erfolgreich.
* Installation und Deinstallation mit Inno Setup 6.7.3 erfolgreich.
* 248 Tests und 23 Subtests bestanden; Produktcode vollständig kompiliert.
* Codesignierung und Veröffentlichung nicht durchgeführt.

## [2.0 RC1] – 2026-07-29 (Sprint 21 – Release Candidate)

### Geändert
* Fail-closed Auto-Update-Vertrag für HTTPS, ARM64, SemVer und SHA-256.
* Verifizierte Installer werden resumefähig und atomar bereitgestellt, nicht gestartet.
* Release-Identität auf `2.0 RC1` / `2.0.0-rc.1` vereinheitlicht.
* RC1-Checkliste und manuelle Veröffentlichungsprüfungen dokumentiert.
* Kein Release veröffentlicht.

### Prüfung
* 67 relevante End-to-End-/Release-Tests und 3 Subtests bestanden; Produktcode vollständig kompiliert.

## [2.0 Preview] – 2026-07-29 (Sprint 20 – Produktreife & Release I)

### Geändert
* Vergleichsansicht auf gemeinsamen Metadatenvertrag und testbare Differenzen finalisiert.
* Plugin-Manifeste, Aktivierungszustände und atomare Installation abgesichert.
* `release.json` als zentrale Release-Konfiguration eingeführt.
* ARM64-Inno-Setup-Konfiguration und validierendes Buildskript vorbereitet.
* Kein Release ausgeführt.

### Prüfung
* 20 relevante Compare-, Plugin-, Release-/Installer- und Metadatentests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 19 – Galerie & Dateiverwaltung absichern)

### Geändert
* Gemeinsamer Metadatenvertrag für Gallery-Loader und Asset-Index.
* Atomare Bildkopien und JSON-Sidecar-Aktualisierungen.
* Galerie-Refresh berücksichtigt reine Metadatenänderungen.
* Thumbnail-Cache und laufende Anfragen verwenden vollständige Dateisignaturen.
* Keine UI-Neugestaltung.

### Prüfung
* 30 relevante Galerie-, Asset-, Thumbnail-, Speicher- und Pipeline-Tests sowie 9 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 18 – UI-Workflow stabilisieren)

### Geändert
* Generierungsfluss von Fortschritt bis Vorschau und Speichern stabilisiert.
* Letztes gültiges Bild bleibt nach Fehler oder Abbruch verfügbar.
* Verspätete Fortschrittsereignisse überschreiben keine Terminalzustände.
* Fehlende Erfolgsdateien werden sicher als Fehler behandelt.
* Keine optische Neugestaltung oder neuen Features.

### Prüfung
* 20 relevante UI-/Controller-Tests und 9 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 17 – Release-Readiness Core)

### Geändert
* Core vollständig auf TODO/FIXME/HACK und veraltete Platzhalter geprüft.
* Nicht implementierten, ungenutzten Remote-Cloud-Stub aus Registry und Core entfernt.
* Überholte Pipeline- und Download-Kommentare an den produktiven Stand angepasst.
* Keine neuen Features oder UI-Änderungen.

### Prüfung
* 24 relevante Core-Tests und 6 Subtests bestanden; Core vollständig kompiliert.

## [2.0 Preview] – 2026-07-29 (Sprint 16 – Performance-Optimierung)

### Geändert
* Aggregierte Auswertung der Laufzeitmetriken je Vorgang.
* Doppelten rekursiven Paketbaum-Scan beim Modellladen entfernt.
* Einzelmetriken von synchronem INFO-Logging auf DEBUG reduziert.
* Keine Funktions- oder UI-Änderungen.

### Prüfung
* 20 relevante Performance-, Modell-Lifecycle- und Inference-Tests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 15 – Performance-Messung)

### Geändert
* Einheitliche interne Laufzeitmetriken für Modellladen, Inference und Freigabe.
* Threadsicherer, begrenzter Metrikspeicher mit Erfolg und Kontext-Tags.
* Messfehler bleiben vollständig vom ausgeführten Vorgang isoliert.
* Keine Optimierungen oder UI-Änderungen.

### Prüfung
* 18 relevante Performance-, Modell-Lifecycle- und Inference-Tests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 14 – Ressourcenüberwachung)

### Geändert
* Zentrale Erfassung von CPU, RAM und aktivem Backend-/NPU-Zustand.
* Gedrosselte, passive Überwachung laufender Jobs im gemeinsamen Lebenszyklus.
* Einheitliche interne Warnungen für Ressourcenengpässe und Backendzustände.
* Keine Funktions- oder UI-Änderungen.

### Prüfung
* 21 relevante Ressourcen-, Job- und Pipeline-Tests sowie 5 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 13 – Start- und Diagnoseprüfung)

### Geändert
* Fail-safe Startprüfung für Umgebung, Backend-Verfügbarkeit und Modellstatus.
* Strukturierte Klassifikation und Protokollierung je Diagnosekategorie.
* Sicherer CPU-Fallback beziehungsweise Start ohne aktives Modell bei Diagnosefehlern.
* Keine UI-Änderungen.

### Prüfung
* 17 relevante Start-, Backend- und Registry-Tests sowie 6 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 12 – Model-Update absichern)

### Geändert
* Versionsprüfung für installierte Modelle und Katalogstände.
* Validiertes Staging mit atomarem Austausch der Installation.
* Automatischer Rollback auf die vorige Version bei Swap- oder Registry-Fehlern.
* Registry-Commit erst nach erfolgreicher Kandidatenvalidierung.
* Keine UI-Änderungen.

### Prüfung
* 27 relevante Update-, Registry-, Paketqualifikations- und Integritätstests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 11 – Model-Download absichern)

### Geändert
* Resumefähige `.part`-Downloads mit HTTP-Range und sicherem Neustart.
* Teil-Downloads bleiben bei Abbruch oder Netzfehler erhalten.
* Verpflichtende SHA-256-Prüfung vor Dateiübernahme und Registrierung.
* Archivpfade und ZIP-Inhalt werden vor Extraktion validiert.
* Keine UI-Änderungen.

### Prüfung
* 21 relevante Download-, Resume-, Integritäts- und Registry-Tests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 10 – Pipeline-Konfiguration vereinheitlichen)

### Geändert
* Unveränderlicher zentraler Parametersnapshot pro Generation-Job.
* Einheitliche Parameterübergabe an Pipeline, CPU, ONNX und QNN.
* Doppelte QNN-Parameter-Serialisierung entfernt.
* Keine UI-Änderungen.

### Prüfung
* 32 relevante Parameter-, Pipeline-, Sidecar-, Job-, Backend- und QNN-Tests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 9 – Speicherverwaltung absichern)

### Geändert
* Garantierter Backend-Shutdown nach Erfolg, Fehler und Abbruch.
* ONNX-Sessions werden in `finally`-Pfaden freigegeben.
* QNN-Worker, Pipes und Hostreferenzen werden zuverlässig geschlossen.
* Keine UI-Änderungen.

### Prüfung
* 28 relevante Ressourcen-, Lifecycle-, Pipeline-, Backend- und QNN-Tests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 8 – Inference-Pipeline absichern)

### Geändert
* Bereits geladene Runtimes werden ohne redundanten zweiten Modell-Load an den Executor übergeben.
* Eingaben und Backend-Ergebnisse werden zentral validiert bzw. normalisiert.
* Fehler, ungültige Ergebnisse und Abbrüche werden konsistent an die Job-Engine weitergegeben.
* Keine Architektur- oder UI-Erweiterung.

### Prüfung
* 34 betroffene Tests bestanden; kurzer Gesamtcheck: 166 Tests und 20 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 7 – Modell-Ladeprozess stabilisieren)

### Hinzugefügt
* **Gemeinsamer Lade-Lebenszyklus:** `ModelLoaderService` steuert CPU-, ONNX- und QNN-Modelle über die Zustände `UNLOADED`, `LOADING`, `LOADED`, `UNLOADING` und `FAILED`.
* **Race-Condition-Schutz:** Lock und Condition serialisieren Laden, Entladen und Wechseln; parallele Loads desselben Modells teilen Runtime und Backend über Referenzzählung.
* **Sichere Modell-Sessions:** Kontextgebundene Nutzung garantiert die Ressourcenfreigabe bei Erfolg, Fehler und Abbruch.
* **Ladediagnose:** Strukturierte Fehlerdiagnosen erfassen Registry-, Initialisierungs-, Kompatibilitäts-, Freigabe- und Bereinigungsfehler.
* **Lifecycle-Tests:** Doppel-Loads, konkurrierende Loads, Initialisierungsfehler, ungültige Installationen, Modellwechsel und Ausnahmefreigabe werden direkt geprüft.

### Geändert
* Registry-Status und Installationsstruktur werden vor jeder Backend-Initialisierung validiert.
* Backend-Auswahl, RuntimeModel-Erzeugung und Load-Plan verwenden einen gemeinsamen atomaren Ladepfad.
* Generation Controller und Generation Executor geben geladene Ressourcen in `finally`-Pfaden zuverlässig frei.
* Veraltete deklarative Modelllisten werden diagnostiziert, ohne bestehendes registriertes CPU-/ONNX-/QNN-Routing zu blockieren.
* Bestehende Funktionalität und UI bleiben unverändert.

### Prüfung
* Vollständiger Python-Build mit `compileall`: erfolgreich.
* Loader-/Registry-/Backend-Vertragstests: 18 Tests bestanden.
* Vollständige Testsuite: 160 Tests und 20 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 6 – Model Manager professionalisieren)

### Hinzugefügt
* **Zentrale ModelRegistry:** Einheitliche Verwaltung von Modellmetadaten, Validierungsberichten und Installationszuständen.
* **Metadatenschema v1:** Bestehende Definitionen werden rückwärtskompatibel normalisiert und auf Pflichtfelder, Typen und Backend-Kompatibilität geprüft.
* **Sichere Modellvalidierung:** Installationspfad, Manifest-ID, Paketstruktur, deklarierte Komponenten und gegen Verzeichnisausbruch geschützte Komponentenpfade werden validiert.
* **Optionale Integritätsprüfung:** Deklarierte SHA-256-Werte werden auf Wunsch gestreamt geprüft; Manipulationen und ungültige Hashangaben führen zu einem eindeutigen Invalid-Status.
* **Fehlerquarantäne:** Nicht lesbare oder strukturell ungültige Modelldefinitionen werden nicht aktiviert und bleiben über Diagnoseberichte auswertbar.

### Geändert
* `ModelRepository`, lokale SMP-Paketvalidierung und Generationsrouting verwenden die gemeinsame Registry und Backend-Auflösung.
* Backend-Inkompatibilität wird diagnostiziert, ohne zukünftige oder testweise Modellmetadaten vorschnell aus dem Katalog zu entfernen.
* Bestehende Modell-, Paket- und UI-Verträge bleiben kompatibel; die UI wurde nicht geändert.

### Prüfung
* Vollständiger Python-Build mit `compileall`: erfolgreich.
* Registry-/Backend-Vertragstests: 12 Tests bestanden.
* Vollständige Testsuite: 154 Tests und 20 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 5 – Konfigurationssystem vereinheitlichen)

### Hinzugefügt
* **Versioniertes Schema:** Preferences verwenden das rückwärtskompatible Schema v2 mit `schema_version`.
* **Zentrale Verwaltung:** `ConfigurationManager` kapselt Laden, Validieren, Migrieren, Zusammenführen und atomisches Speichern.
* **Migrationen:** Unversionierte, verschachtelte und ältere Schlüssel-/Wertformate werden automatisch auf Schema v2 übertragen.
* **Validierung:** Modell-ID, Token, Threads, Execution Provider, Hardwarebeschleunigung, Pfade, Theme und Sprache werden typ- und wertegeprüft.
* **Vorwärtskompatibilität:** Unbekannte Konfigurationsschlüssel bleiben bei Migration und Speicherung erhalten.

### Geändert
* `config.py`, `SettingsManager`, `ModelRepository` und `i18n` verwenden denselben Preferences-Pfad und dieselbe Persistenzlogik.
* Schreibvorgänge erfolgen atomar über eine temporäre Datei.
* Bestehende UI-Schlüssel und Stringwerte bleiben unverändert kompatibel; die UI wurde nicht geändert.

### Prüfung
* Vollständiger Python-Build mit `compileall`: erfolgreich.
* Konfigurations-, Settings-, Preferences- und i18n-Regression: 24 Tests bestanden.
* Vollständige Testsuite: 146 Tests und 20 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 4 – Logging & Fehlerdiagnose professionalisieren)

### Hinzugefügt
* **Zentrale Protokollierung:** `engine/logging_config.py` erstellt automatisch `logs/snapdragon_ai_studio.log` und konfiguriert strukturierte Einträge mit Zeitstempel, Log-Level, Loggername und Thread.
* **Logrotation:** Die UTF-8-Protokolldatei rotiert bei 5 MiB; maximal fünf Sicherungsdateien werden aufbewahrt.
* **Fehlervertrag:** Domänenspezifische Basisklassen für Backend-, Pipeline-, Job- und Konfigurationsfehler wurden ergänzt.
* **Strukturierte Diagnosen:** `diagnose_exception()` protokolliert Kategorie, Kontext, Exception-Typ, Meldung, Job-ID und Backend einschließlich Traceback.
* **Tests:** Automatische Verzeichniserstellung, strukturiertes Format, Rotation und Job-Fehlerdiagnose werden direkt geprüft.

### Geändert
* Backend-, ONNX-/QNN-Service-, Pipeline-, Executor-, JobManager- und Worker-Komponenten verwenden die zentrale Logger-Konfiguration und strukturierte Level.
* Stille bzw. verstreute Kernfehlerpfade wurden an die gemeinsame Diagnose angebunden.
* Bestehende Konsolenausgaben, Ergebnisverträge und UI-Verhalten bleiben erhalten.

### Prüfung
* Vollständiger Python-Build mit `compileall`: erfolgreich.
* Logging-/Job-/Backend-/QNN-Regression: 22 Tests und 11 Subtests bestanden.
* Vollständige Testsuite: 140 Tests und 20 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 3 – Job- & Pipeline-Engine stabilisieren)

### Geändert
* **Einheitlicher Jobstatus:** `JobStatus` standardisiert ausführbare Jobs auf `QUEUED`, `RUNNING`, `FINISHED`, `FAILED` und `CANCELLED`; historische englische und deutsche Werte werden kompatibel normalisiert.
* **Einheitlicher Fortschritt:** Interner Fortschritt liegt durchgängig zwischen `0.0` und `1.0`; bestehende Callbacks erhalten weiterhin Prozentwerte zwischen `0` und `100`.
* **Gemeinsamer Lebenszyklus:** Generation-, Legacy- und Phoenix-Jobs verwenden zentrale Funktionen für Statusübergänge, Fortschritt, Fehler und Abbruch.
* **QNN-Fortschrittsmeldungen:** SD1.5, SD2.1 und ControlNet verwenden dieselbe Übersetzung von Worker-Ausgaben in lokalisierte Phasenmeldungen.
* **Abbruchbehandlung:** Backend- und Scheduler-Abbrüche setzen Abbruchsignal und Status konsistent; aktive und wartende Batch-Jobs werden eindeutig beendet.
* **Kompatibilität:** Ergebnisstatus, UI-Callbacks und bestehende Pipeline-Ausgaben bleiben erhalten; die UI wurde nicht geändert.

### Prüfung
* Vollständiger Python-Build mit `compileall`: erfolgreich.
* Job-/Pipeline-Regression: 21 Tests und 20 Subtests bestanden.
* Vollständige Testsuite: 137 Tests und 20 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 2 – Backend vereinheitlichen)

### Geändert
* **Gemeinsamer Backend-Vertrag:** `InferenceBackend` definiert jetzt die gemeinsame Schnittstelle für Routing-Adapter und physische CPU-, ONNX- und QNN-Backends einschließlich Lebenszyklus, Verfügbarkeit, Metadaten, Generierung, Abbruch, Fortschritt und Zustandsprüfung.
* **Adapter-Konsolidierung:** CPU-, ONNX- und generischer QNN-Stub verwenden `StubBackendAdapter` für ihre identische Zustands- und Ergebnislogik.
* **QNN-Routing-Konsolidierung:** SD1.5-, SD2.1- und ControlNet-QNN-Adapter verwenden `QnnProductBackendAdapter` für Delegation, laufende Backend-Bindung und Abbruch.
* **ONNX-Verfügbarkeit:** Die boolesche Vertragsmethode `is_available()` ist von der detaillierten Diagnose `check_availability()` getrennt.
* **Kompatibilität:** UI, Backend-Namen, Versionen, Meldungen, Auswahlreihenfolge und produktive QNN-Pfade bleiben unverändert.

### Prüfung
* Vollständiger Python-Build mit `compileall`: erfolgreich.
* Backend- und QNN-Regression: 32 Tests und 6 Subtests bestanden.
* Vollständige Testsuite: 129 Tests und 15 Subtests bestanden.

## [2.0 Preview] – 2026-07-29 (Sprint 1 – Projektbasis stabilisieren)

### Geändert
* **Deterministische Testsammlung:** Eine zentrale `pytest.ini` begrenzt die automatische Sammlung auf `tests/`. Dadurch werden ausführbare Diagnose- und Laufzeitskripte außerhalb der regulären Testsuite nicht mehr als Tests importiert.
* **Projektstatus:** `docs/PROJECT_STATE.md` wurde auf den geprüften Stand vom 29.07.2026 aktualisiert.

### Prüfung
* Vollständiger Python-Build mit `compileall`: erfolgreich.
* Vollständige Testsuite: 125 Tests bestanden, keine Warnungen.
* Keine Features und keine Architekturänderungen.

## [2.0 Preview] – 2026-07-27 (Sprint UX-001 – Phoenix UI Modernization)

### Hinzugefügt
* **Sprint UX-001 – Phoenix UI Modernization:**
  * **Modernes Button-System & PhoenixButton:**
    * Implementierung von `PhoenixButton` (`widgets/phoenix/controls/button.py`), einem reaktiven, Canvas-basierten Button-Widget mit abgerundeten Ecken (8-12px), uniformen Höhen und animierten Farbübergängen (Fade-Effekt bei Hover/Aktivierung) im Haupt-UI-Thread ohne zusätzlichen Overhead.
    * Unterstützung für Primary-, Neutral-, Danger- und Disabled-Stile mit automatischer Farbkontrastberechnung und Theme-Zuweisung.
    * Integration standardmäßiger Tkinter-Schnittstellen (wie `.cget("bg" / "fg" / "state" / "text")`, `.configure()`, `.invoke()`) für nahtlose Rückwärtskompatibilität und Testbarkeit.
  * **Moderne Vektor-Icon-Bibliothek:**
    * Implementierung von `PhoenixIcon` (`widgets/phoenix/controls/vector_icons.py`) für die direkte mathematische Darstellung moderner, skalierbarer Vektorgrafiken auf `tk.Canvas` zur Vermeidung von pixeligen PNGs/Emojis und Gewährleistung gestochen scharfer Icons im Dark/Light-Theme.
    * Automatisches Parsing und Mapping von Unicode-Fallback-Symbolen in Buttons und Toolbars zu den entsprechenden Vektor-Icons.
  * **Modernisiertes Navigations- & Sidebar-Layout:**
    * Umstellung der Navigationsleiste (`widgets/phoenix/sidebar.py`) und der Arbeitsbereich-Toolbars (`widgets/phoenix/layout/workspace.py`) auf das neue reaktive Vektor-Button-System mit sauberen Hover- und Active-Zuständen.
  * **Cards statt Kästen & PhoenixCard:**
    * Entwicklung des Canvas-basierten Container-Widgets `PhoenixCard` (`widgets/phoenix/controls/card.py`) zur Visualisierung moderner Karten mit abgerundeten Ecken, dezentem Rahmen und Hintergrundabstufungen.
    * Migration von `WorkspacePanel`, `WorkspaceInfoCard`, `PhoenixPluginCard` und `ComparePanel` auf `PhoenixCard` für ein ruhigeres und moderneres UI-Layout.
    * Integration eines dynamic proxies in `widgets/phoenix/views/prompt_view.py` zur automatischen Konvertierung aller klassischen Buttons und umrandeten Layout-Frames zu `PhoenixButton` und `PhoenixCard` ohne Modifikation der Geschäftslogik.

## [2.0 Preview] – 2026-07-27 (Sprint CN-033 bis CN-035e)

### Hinzugefügt
* **Sprint CN-033 – App Top Menu Bar Refinement:**
  * Bereinigung und Re-Strukturierung der oberen Hauptmenüleiste (File, Studio, View, Plugins, Tools, Help) in `gui_v2.py`.
  * Integration von Aktionen wie "Output-Ordner öffnen", "Modell-Ordner öffnen", "VRAM / NPU Cache leeren", "Hardware-Info", "Seitenleiste umschalten", "Plugins verwalten", "Log-Datei anzeigen", etc.
  * Definition globaler Tastenkombinationen (Hotkeys) für Vollbild umschalten (F11) und Beenden (Alt+F4).
* **Sprint CN-034 / CN-034b / CN-034d / CN-034e – Global Theme Switching & Persistence:**
  * Implementierung einer globalen Theme-Steuerung (Dark / Light) mit vollständiger Kaskadierung über alle View-Container und Controls via `<<ThemeChanged>>` Event-System.
  * Windows-kompatible Neustart-Logik mit `subprocess.Popen` bei Theme-Änderungen nach Bestätigung durch Benutzerdialog.
  * Boot-Phase in `gui_v2.py` liest das konfigurierte Theme aus `config.json` aus und initialisiert das UI einheitlich im gewählten Design.
* **Sprint CN-035 / CN-035b / CN-035c / CN-035d / CN-035e / CN-035f / CN-035g – Complete i18n Sweep, Sync-Audit, View Precision Fixes & Import Resolutions:**
  * Erstellung des automatischen Vollständigkeitsscanners `test_i18n_completeness.py` und des bidirektionalen Sync-Audits `test_i18n_sync.py` zur Validierung symmetrischer Translation-Keys (Deutsch/Englisch) und zur Verhinderung identischer Werte für Nicht-Eigennamen/Nicht-technische Begriffe.
  * Lückenloser Sweep durch alle Workspaces und Unterkomponenten (AI Generate, Model Manager, Gallery, Compare, Plugins, Settings, Sidebar und Home) zur Kapselung aller UI-Labels (inklusive Toolbars, Statusmeldungen, Fallback-Metadaten und Dialogfenster) in die Übersetzungsfunktion `tr(...)`.
  * Lokalisierung aller englisch-gebliebenen Schlüssel in `de_DE.json` (wie `ai_generate_title`, `nav_ai_generate`, `nav_ai_model_manager`, `nav_compare`, `nav_gallery`, `nav_home`, `nav_settings`, `gallery_title`, `tab_basic`, `tab_advanced`, `cfg_scale_label_colon`, `steps_label_colon`, `exit_code_label`, `package_status_label`, `checksum_label_colon`, `vae_decoding`, `download_failed_msg`, `msg_package_update_failed`, `queue_prefix`).
  * Direkte Behebung verbliebener deutscher Strings in den Gallery- und Compare-Workspaces (Lokalisierung von "Ausgabe", "Metadaten vergleichen", "Keine Auswahl", "Nicht geladen", "Synchron" -> "Synced", "Status Bereit" -> "Status Ready", "Ordner öffnen" -> "Open Folder", "Aktualisieren" -> "Refresh", "Bilder" -> "Images", "Auswahl" -> "Selection", "Zoom", "Mittel" -> "Medium") und Integration passender Übersetzungen in die JSON-Sprachdateien.
  * Behebung eines NameError-Absturzes beim Laden der Galerie durch Hinzufügen des fehlenden `tr` Imports in `status_bar.py`.
  * Bereinigung verdeckter hardcodierter Statusänderungen ("Bereit") im Galerie-Controller und Statusleiste durch Angleichung auf den Standardkey `tr("ready", "Bereit")`.
  * Anpassung der Testumgebung in `test_production_qnn_pipeline.py` durch Mocking von `pathlib.Path.exists`, damit QNN-Fehlerpfade auch ohne physische Modelldateien robust getestet werden können und alle Unit-Tests erfolgreich durchlaufen.

## [2.0 Preview] – 2026-07-16 (Sprint CN-002)

### Hinzugefügt
* **Sprint CN-002 – ControlNet Reference Image UI:**
  * **Dynamische Sichtbarkeit:** Die Referenzbild-Drag-&-Drop-Auswahl (`dnd_card` und `dnd_subtitle`) wird für Modelle ohne ControlNet-Unterstützung (SD1.5, SD2.1) automatisch ausgeblendet und bei Aktivierung eines ControlNet-Modells dynamisch eingeblendet.
  * **Dynamischer Titel:** Der Beschreibungstext wird bei ControlNet-Modellen automatisch auf `"Referenzbild für ControlNet Canny:"` angepasst.
  * **Echtzeit-Validierung:** Integration einer Vorabprüfung in `GenerationController.validate_session()`. Bei fehlendem oder ungültigem Bild wird die Generierung abgebrochen und eine klare Fehlermeldung per Dialogbox ("Eingabebild für ControlNet Canny fehlt oder ist ungültig.") im UI angezeigt.
  * **Komplette Testabdeckung:** Erstellung dedizierter UI- und Validierungstests in `tests/test_controlnet_ui.py` und Erweiterung von `tests/test_generate_ux_state.py`.

## [2.0 Preview] – 2026-07-16 (Sprint CN-001)

### Hinzugefügt
* **Sprint CN-001 – ControlNet Canny Backend Integration:**
  * **Modell-Registrierung:** Hinzufügen der Modell-Metadaten-Definition `controlnet_canny_qnn.json` unter `resources/models` für das offizielle Qualcomm ControlNet-Canny w8a16-Paket.
  * **Inferenz-Backend-Adapter:** Implementierung von `ControlNetCannyQnnBackend` in `engine/controlnet_canny_backend.py`. Es führt das komplette ControlNet-Canny-Modellpaket (Text-Encoder, ControlNet, UNet, VAE) vollständig auf der Qualcomm Hexagon HTP NPU aus (CPU EP Fallback komplett deaktiviert via `session.disable_cpu_ep_fallback=1`).
  * **Isolierter Subprocess-Worker:** Der Backend-Adapter kapselt die QAIRT 2.45 / ORT 1.25.0 Inferenzlaufzeit in einem separaten Subprozess-Worker, welcher das isolierte Virtual Environment `temp/controlnet_canny_gate/venv` nutzt.
  * **Canny Preprocessing & DDIM Scheduler:** Integration eines reinen NumPy-basierten Canny-Kantendetektors (CPU) und eines DDIM-Schedulers für die passgenaue Tensor-Requantisierung und latente Rauschreduzierung.
  * **Schnittstellen & Factory-Registrierung:** Registrierung des Backends in der `InferenceBackendFactory` und des Adapters `ControlNetCannyQnnBackendAdapter` im `BackendManager`.
  * **Reproduzierbarkeit & Diagnostik:** Automatisches Kopieren des verwendeten Eingabebildes in den Test-/Ausgabeordner und Speichern eines 3-teiligen Kontaktbogens (Original, Canny-Kanten, Generierung) zusammen mit einem detaillierten JSON-Diagnose-Sidecar.

## [2.0 Preview] – 2026-07-16 (Sprint IQ-008 & UI-008)

### Hinzugefügt
* **Sprint IQ-008 – SD1.5 vs. SD2.1 Quality Profile:** Durchführung eines systematischen Qualitätsvergleichs auf der Hexagon NPU (HTP V73). SD2.1 QNN dominiert in Anatomie, Tiertexturen und Architektur, während SD1.5 QNN bei künstlerischen Fantasy-Motiven überlegen ist.
* **Sprint UI-008 – AI Generate Workspace Polish:**
  * **Logische Gruppierung:** Strukturierung der Bedienelemente in die vier Kernbereiche: Model, Prompt, Generation Parameters und Actions.
  * **Modellbeschreibung:** Visuelle Hervorhebung der Modellbeschreibung in einer separaten elevated Card mit dezentem Rahmen und Hintergrund.
  * **Schreibgeschützte Parameter:** Automatische Visualisierung gesperrter Optionen (z. B. Sampler und Scheduler) mit einem Schloss-Symbol (🔒) im Label und dezent verblasster Textfarbe (`disabledforeground`).
  * **Konsistentes Layout:** Ausrichtung sämtlicher Abstände und Rahmen zur Etablierung eines vollendeten kommerziellen Standards.

## [2.0 Preview] – 2026-07-14 (Laufende Phoenix-Entwicklung)

### Hinzugefügt
* **R-005 – QNN Package Qualification Gate:** Headless Paketprüfung mit deterministischem JSON-Bericht, sicherer ONNX-/External-Data-/EPContext-Analyse und optionalem Strict-QNN-Load ohne CPU-Fallback. Das produktive SD2.1-QNN-Paket erreicht `CONDITIONALLY_QUALIFIED`; `sdxl_base` wird ohne Laden großer Gewichte oder Compile-Versuch begründet abgelehnt.
* **Runtime Header and Scroll Fix (G-008B):**
  * **Dynamischer Header:** Entfernung der festen Header-Höhe und Deaktivierung der Größenunterdrückung (`pack_propagate(True)` und `grid_propagate(True)`). Title- und View-Labels nutzen nun internes Padding (`ipady=2`), wodurch der Header sich dynamisch an seine Kindelemente anpasst und abgeschnittene Slogans und Untertitel bei jeglicher Windows-Skalierung (100% bis 150%) robust verhindert werden.
  * **In-Place Updates & Scroll-Erhaltung:** Treeview-Items und Detail-Labels werden direkt in-place aktualisiert (`_update_label` verhindert Redraws bei identischen Werten). Die Scrollregion des Canvas wird über `_on_content_configure` nur noch dann angepasst, wenn sich die Bounding Box tatsächlich physisch verändert. Die Y-Scrollposition bleibt somit bei periodischen Updates absolut fest, und der Detailbereich springt nur bei einem bewussten Modellwechsel an den Anfang. Dies stellt die dauerhafte Sichtbarkeit und Bedienbarkeit der erweiterten Einstellungen sicher.
* **UI-Nachbesserungen (G-008A):**
  * **Workspace-Titel:** Die Höhe des Workspace-Headers (`PhoenixHeader`) wurde von `60px` auf `72px` erhöht, und die vertikalen Abstände wurden angepasst. Dies stellt sicher, dass der Titel unter "Snapdragon AI Studio" (z. B. "AI Model Manager", "AI Generate") bei unterschiedlichen Schriftlängen und DPI-Skalierungen auf allen Systemen niemals abgeschnitten wird.
  * **Model Manager Scroll-Stabilisierung:** Behebung des automatischen Scrollens nach oben im AI Model Manager. Es wurde ein Signatur-Abgleich der Modelle implementiert, so dass die Treeview bei unverändertem Status nicht periodisch gelöscht und neu aufgebaut wird. Zudem wird bei normalen Status-Updates die Scrollposition des Detailbereichs (`inspector_canvas`) ermittelt und nach Layout-Berechnungen wiederhergestellt. Ein bewusster Modellwechsel in der Treeview setzt die Scrollposition wie gewünscht an den Anfang zurück.
  * **Prompt-Werkzeuge:** Vorlagen, Verlauf und Maximieren wurden in einer zusammengehörigen, visuell abgegrenzten Werkzeugleiste (`self.prompt_toolbar`) gruppiert. Die Buttons nutzen die Eigenschaft `text_primary` für optimalen Kontrast, sind mit Trennlinien unterteilt und verfügen über klare Icons (`📋 Vorlagen`, `🕘 Verlauf`, `⛶ Maximieren`).
* **AI Generate UI Polish (G-008):** Umfassender optischer und struktureller Feinschliff der Hauptansicht von AI Generate zur Etablierung eines kommerziellen Standards. Sämtliche Parameter-Bereiche (Model, Prompt, Referenzbild, Image Size, Sampling, Output) wurden bezüglich ihrer Außenabstände (`padx=16` für alle Karten und Rahmen) und ihrer vertikalen Trennungen (`pady=12`) vereinheitlicht, um eine perfekte, gerade Ausrichtung entlang der linken und rechten Kanten zu gewährleisten. Die Buttons im Prompt-Header (Vorlagen, Verlauf, Maximieren) sowie der Button für erweiterte Einstellungen wurden optisch angeglichen (identische Höhen, Paddings, Schriftarten und aktive Zustände). Für alle diese Buttons, die Qualitätsprofil-Buttons sowie das Referenzbild-Card-Widget wurden reaktive, flüssige Hover-Effekte via Enter/Leave-Bindings implementiert. Der Referenzbild-Bereich wurde vertikal kompakter gestaltet (`pady=8`), um unnötige Scrollstrecken zu minimieren.
* **Reference Image UX (G-007A):** Umbenennung der Drag & Drop Parametergruppe in "Referenzbild (Demnächst)" und Ergänzung des Untertitels *"Vorbereitung für Image→Image und Image→Video."* unter Verwendung von `ThemeManager`-Farben und -Schriftarten zur Wahrung der Dark/Light-Themeparität. Die Vorschaufunktion, die Metadatenanzeige und der Löschbutton ("Bild entfernen") bleiben unverändert erhalten.
* **Drag & Drop Foundation (G-007):** Integration der Drag & Drop-Funktionalität für Bilddateien (PNG, JPG, JPEG, WebP) in der AI Generate-Ansicht. Nach dem Ablegen einer Datei wird eine kompakte Bildvorschau sowie deren Dateiname und Auflösung dargestellt. Ein "Bild entfernen"-Button ermöglicht das Zurücksetzen der Auswahl. Die Bilddatei wird hierbei ausschließlich geladen (über PIL) und nicht durch die KI verarbeitet. Das MVC-Modell (PromptWorkspaceState, PromptWorkspaceModel, PromptWorkspaceController und GenerationSessionModel) wurde architektonisch um das Feld `input_image_path` erweitert, um spätere Image→Image- und Image→Video-Workflows vorzubereiten. Das gesamte UI-Design basiert auf dem Phoenix-ThemeManager, wodurch die volle Dark- und Light-Theme-Kompatibilität sowie die Robustheit in Testumgebungen gewahrt bleibt.
* **Prompt Counter (G-006):** Integration eines Live-Zählers für Zeichen und Wörter direkt unter dem Prompt-Eingabefeld im Hauptbereich. Zudem wurde ein identischer Live-Zähler unter der Textfläche des großen Prompt-Editor-Popups (G-005) implementiert. Beide Zähler synchronisieren sich in Echtzeit bei Tastatureingaben, Vorlagenauswahlen (Templates) oder dem Laden aus der Prompt-History. Die Zähleranzeige und das Layout passen sich über den `ThemeManager` nahtlos an Dark- und Light-Themes an.
* **Expandable Prompt Editor (G-005):** Hinzufügen eines großen, zentrierten Prompt-Editor-Popups (ca. 80% der Hauptfenstergröße), das über eine neue Schaltfläche "⛶ Maximieren" im Prompt-Header geöffnet werden kann. Der Editor spiegelt den Text des Hauptfensters in Echtzeit wider. Änderungen in beiden Textfeldern werden bidirektional über dedizierte Synchronisationsmethoden abgeglichen. Das Popup unterstützt das ESC-Tastenkürzel zum Schließen und Übernehmen sowie das Laden von Vorlagen und Einträgen aus dem Verlauf, welche sich bei geöffnetem Zustand parallel synchronisieren. Sämtliche GUI-Elemente unterstützen Dark- und Light-Theme-Vorgaben über den `ThemeManager` ohne hartcodierte Farben.
* **Advanced Settings Popup Preview (G-004D):** Hinzufügen einer alternativen, kompakten AI-Generate-Darstellung für den direkten Vergleich durch den Product Owner. Der Hauptbereich zeigt nur noch essenzielle Felder (Modell, Prompts, Qualitätsprofile, Generierungskontrollen) sowie eine Schaltfläche "Erweiterte Einstellungen". Ein Klick darauf öffnet ein zentralisiertes, modales Popup-Fenster mit detaillierten Optionen (Auflösung, CFG-Scale, Sampler/Scheduler, Seed/Batch). Die bidirektionale Bindung an dieselben `tk.Variable`-Instanzen sorgt für sofortige und fehlerfreie Wertübernahmen, während das Umschalten von Modellen (z. B. SD1.5 ↔ SD2.1) dynamisch im Popup reflektiert wird. Über die Klassenkonstante `COMPACT_PREVIEW_MODE = True` in `PhoenixPromptView` kann jederzeit nahtlos auf die bisherige Vollbild-Variante zurückgewechselt werden.
* **Fix Quality Presets Visibility (G-004A):** Behebung eines Layoutproblems, bei dem die nebeneinander liegenden Preset-Schaltflächen in der schmalen Parameter-Spalte (Spalte 1) zu breit waren und die gesamte rechte Spalte über den sichtbaren Bereich des Scroll-Canvas hinausgeschoben haben. Durch die vertikale Anordnung der drei Preset-Schaltflächen (⚡ Schnell, ⭐ Standard, 💎 Beste Qualität) wurde die Spaltenbreite stabilisiert und die Sichtbarkeit im Workspace für SD1.5 und SD2.1 vollständig wiederhergestellt.
* **Quality Presets (G-004):** Ersatz der technischen Steps-Einstellungen im Standardmodus (bei Modellen mit gesperrter Auflösung) durch drei Presets (⚡ Schnell, ⭐ Standard, 💎 Beste Qualität). Die Presets steuern intern die Steps (Schnell = 10, Standard = 20, Beste Qualität = 30 für SD1.5 und SD2.1 QNN Modelle), während der tatsächliche Step-Wert in den Metadaten erhalten bleibt. Umschalten auf andere Modelle stellt die standardmäßige Steps-Skala automatisch wieder her.
* **Prompt Templates (G-003):** Einführung einer ausbaufähigen Vorlagenverwaltung für AI-Prompts. Eine JSON-Datei unter `resources/prompt_templates.json` speichert Kategorien (Portrait, Landschaft, Architektur, Fantasy, Sci-Fi, Produktfoto) mit Vorlagen. In der UI bietet eine "Vorlagen ▼"-Schaltfläche ein kaskadierendes Menü zur Schnellauswahl. Ein Klick überschreibt den Hauptprompt, während der negative Prompt unberührt bleibt. Alle Elemente integrieren sich harmonisch in das Phoenix-Theming.
* **Progress Bar Fix (G-003):** Nachhaltige Beseitigung des Fehlers, bei dem der Fortschrittsbalken nach mehreren Generierungen (z. B. durch Inzidenz externer `theme_use()`-Aufrufe) grau wurde. Die Progressbar-Layoutstruktur und Farbgebung werden nun bei jedem Fortschrittsschritt über die Methode `_ensure_progress_style()` überwacht und neu verankert.
* **Prompt History (G-002):** Hinzufügen einer lokalen Prompt-History für AI Generate. Die letzten 20 erfolgreich generierten Prompts werden persistent und duplikatfrei (neuester Eintrag gewinnt) in der Datei `data/prompt_history.json` gespeichert. Die History lässt sich über ein kleines Verlaufssymbol (🕘) direkt neben dem Prompt-Titel öffnen. Ein Klick auf einen Eintrag übernimmt den Prompt in das Textfeld, während negative Prompts unverändert bleiben. Sämtliche UI-Elemente unterstützen Dark- und Light-Theme-Vorgaben über den `ThemeManager` ohne hartcodierte Farben.
* **Resolution Availability UX (G-001E):** Die Auflösungsauswahl stellt für die Modelle SD1.5 QNN und SD2.1 QNN ausschließlich die unterstützte Option 512×512 sichtbar und ausgewählt dar. Die Option 1024×1024 bleibt sichtbar, wird jedoch im Layout deaktiviert und mit einem Schloss-Symbol (🔒) und dem Vermerk „Demnächst“ versehen. Ein Informationstext weist darauf hin, dass höhere Auflösungen kompatible Qualcomm-Modelle voraussetzen. Die UI wechselt bei anderen Modellen automatisch auf die Standard-Dropdowns zur Breite/Höhe-Auswahl zurück. Alle Farben basieren auf dem Phoenix-ThemeManager, wodurch die Dark- und Light-Theme-Kompatibilität vollständig erhalten bleibt.


### Hinzugefügt
* **Experimental Tiled QNN Diffusion PoC (HR-001):** Isolierter SD2.1-Hochauflösungsversuch mit gemeinsamem 128×128-Latent-Canvas, generischer randbündiger Tile-Planung, überlappenden festen 64×64-QNN-UNet-/VAE-Fenstern, separabler Cosine-Gewichtung und globalem DDIM-v_prediction-Schritt. Erfolgreiche 1024×1024-QNN/HTP-Läufe mit 64 px und 128 px Bildüberlappung einschließlich vollständiger Diagnose-Sidecars und reproduzierbarem PNG-Hash. Keine GUI- oder produktive Backendintegration; wegen verbleibender semantischer Kohärenzgrenzen noch keine Produktfreigabe.
* **AI Asset Library Index Foundation (P4-001A):** Einführung eines versionierten, vollständig aus dem Dateisystem reproduzierbaren SQLite-Asset-Indexes. Die medienneutrale Schicht aus unveränderlichem `AssetRecord`, parametrisiertem `AssetIndexRepository` und fehlertolerantem `AssetScanner` indiziert PNG/JPG/JPEG/WebP samt Sidecars, erkennt neue, geänderte, entfernte und wiederhergestellte Dateien und bewahrt Favorit/Bewertung bei Metadaten-Rescans. Asset-Binärdaten verbleiben ausschließlich im Dateisystem; Video-Unterstützung ist im Schema vorbereitet, jedoch nicht implementiert.
* **Recovery IQ-R01 (IQ-001/IQ-004):** Wiederherstellung der modellabhängigen `generation_parameters`-Verträge für SD1.5 und SD2.1 einschließlich gesperrter 512×512-Auflösung, modellgebundener Steps-/CFG-Grenzen, fester Sampler/Scheduler und Prediction Types. Konsolidierung der Controller-Validierung auf den Repository-Vertrag sowie Erweiterung der QNN-Sidecars um Schedulerfolgen, SD1.5-Sigmas, Tensorstatistiken, Laufzeiten, Modellversion, Backend und Gerät.
* **First Real AI Image Integration (M3.1 – P-107 bis P-109):** Fertigstellung und Validierung des gesamten End-to-End-Inferenzflusses für das echte SDXL Snapdragon Model Package (SMP). Ausbau der detaillierten Fehlerprotokollierung zur genauen Nennung fehlender oder ungültiger Modellschnittstellen und Dateipfade im Generierungs-Protokoll, um die Diagnose vor Ort beim Endanwender zu maximieren.
* **Automatic Runtime Activation (M2.2 – P-104 bis P-106):** Erweiterung des `ModelRuntimePackage` um die Verifizierungsmethode `verify_components()` zur Statusermittlung aller 6 Kernkomponenten (`tokenizer`, `text_encoder`, `text_encoder_2`, `unet`, `vae_decoder`, `scheduler`) mit den Statuswerten `READY`, `FOUND`, `MISSING`, `INVALID`. Vollautomatische Aktivierungssteuerung der echten ONNX-Pipeline im `OnnxImageBackend` nur bei durchgehend einsatzbereiten Modulgewichten (`is_fully_ready()`). Fehlt eine Komponente oder ist ungültig (z. B. 0-Byte/Stub-Modelle), degradieren die Services geräuschlos direkt in den deterministischen Mock-Modus, ohne unnötige Inferenzsitzungs-Ladeversuche zu unternehmen.
* **First Real Image (M2.1 – P-101 bis P-103):** Etablierung des echten lokalen SDXL Inferenz-Pipeline-Flusses über das Snapdragon Model Package (SMP) Format. Koppelung der Teilsysteme (`TextEmbeddingService`, `UNetService`, `VAEDecoderService`) im `OnnxImageBackend` zur vollständigen Bildsynthese. Robuste Fehlerbehandlung: Auslegung der anfänglichen Modellprüfung als nicht-fataler Verifizierungsschritt. Fehlen reale physikalische Modellartefakte oder werfen sie Parsingfehler, fangen die Teildienste diese ab und springen geräuschlos auf ihre mathematisch/prozedural korrekten Ersatz-Algorithmen (Mock-Latents, Mock-Embeddings, Concentric-Rings-VAE-Rendering) über.
* **Model Package Architecture (M1.3 – P-098 bis P-100):** Entwurf und Implementierung der endgültigen, professionellen, modellunabhängigen und rein datengesteuerten Snapdragon Model Package (SMP) Architektur. Einführung der `package.json`-Spezifikation für Modellpakete zur Definition von Metadaten (`package_version`, `author`, `display_name`), Fähigkeiten (`capabilities`) und Komponentenpfaden/-laufzeitumgebungen (CPU, ONNX, QNN). Erweiterung des `ModelRepository` zum automatischen Parsen des SMP-Formats unter Beibehaltung einer robusten Abwärtskompatibilität (Legacy Fallback). Bereitstellung von `package.json`-Paketen für `flux_dev` und `sdxl_base` sowie Migration des `flux_dev` Pfads zur Verzeichnisebene.
* **End-to-End AI Pipeline (M1.2 – P-095 bis P-097):** Implementierung des `VAEDecoderService` zur Wandlung von Latent-Tensors in vollaufgelöste RGB-Bilder. Dynamische ONNX-Inferenz des VAE-Decoders via `InferenceSession` und ausfallsicherer Fallback auf eine hochqualitative prozedurale Bildrendering-Generierung basierend auf Latents-Statistiken. Erfolgreiche Verbindung der E2E-Pipeline (`TextEmbeddingService` -> `UNetService` -> `VAEDecoderService`) im `OnnxImageBackend`. Erweiterung der Sidecar-Metadaten um `embedding_shape`, `latent_shape`, `decoder_backend`, `is_mock_decoder` und `is_mock_unet`.
* **First UNet Execution Foundation (P-094):** Implementierung des `UNetService` zur Rauschvorhersage und Latents-Aktualisierung. Dynamische Erzeugung von SDXL-Anfangs-Latents (z. B. `(1, 4, 64, 64)` bei `512x512` Bildgröße). Vorbereitung des echten UNet-ONNX-Inferenzpfades über `InferenceSession` und dynamischem Mapping der Eingangs-Variablen. Ausfallsicherer Fallback auf Euler-aktualisierte Mock-Latents im Falle von Modellfehlern oder fehlendem ONNX-Support. Vollständige Koppelung an die Inferenz-Pipeline im `OnnxImageBackend`, Darstellung der finalen Latent-Form auf dem Diagnose-PNG und Erfassung in den JSON-Sidecars.
* **First Real AI Execution (P-093):** Implementierung des `TextEmbeddingService` zur echten Prompt-Tokenisierung (77 Token, SOS/EOS, Zero-Padding) und Text-Encoder-Inferenzierung via `onnxruntime.InferenceSession`. Falls der physische Text-Encoder fehlt oder Fehler wirft, wird dies abgefangen und über ein stochastisch-deterministisches Mock-Embedding (`(1, 77, 768)` für SDXL) kompensiert. Einbindung des TextEmbeddingService in das Generierungs-Backend zur Visualisierung von Token-Sequenzen und Einbettungsdimensionen auf dem Diagnose-PNG sowie zur Ablage im Sidecar-JSON.
* **SDXL Runtime Architecture (P-092):** Vorbereitung der Datenstruktur für die erste echte SDXL-Bildgenerierung. Implementierung der Klasse `ModelRuntimePackage` zur modellunabhängigen Verwaltung der Dateipfade und Ziel-Execution-Runtimes der 6 Kernkomponenten (`tokenizer`, `text_encoder`, `text_encoder_2`, `unet`, `vae_decoder`, `scheduler`). Erweiterung des `ModelRepository` um die Fabrikmethode `build_runtime_package(model_id)` zur Pfadauflösung und Paketvalidierung (`is_valid_package()`).
* **AI Model Capability System (P-091):** Implementierung der Klasse `ModelCapabilities` zur Daten-gesteuerten Abfrage von Modellfähigkeiten (Unterstützung von `txt2img`, `img2img`, `inpainting`, `outpainting`, `lora`, `controlnet`, `image_to_video`, `batch_generation`, `onnx_runtime`, `qnn_runtime`). Anpassung der Validierung im `ModelRepository` (Erzwingung der `capabilities`-Metadaten) und Ausbau aller 7 Modell-JSON-Metadatendateien um detaillierte Fähigkeitsprofile. Vermeidung harter Codierung im Inferenzfluss.
* **First ONNX Inference Session (P-089):** Implementierung des ersten echten Lade- und Initialisierungsschrittes für die `onnxruntime.InferenceSession`. Nach erfolgreichem Laden einer kompatiblen `.onnx`-Datei werden die Input- und Output-Informationen des Modells ausgelesen, protokolliert und die Session-Ressourcen anschließend sauber freigegeben (`del session`). Saubere Fehlerberichterstattung und Fallback-Handling bei ungültigen Dateien oder fehlendem ONNX-Support.
* **First ONNX Runtime Detection (P-088):** Erweiterung des `OnnxImageBackend` zur detaillierten Erkennung der installierten ONNX Runtime. Auslesung der Bibliotheksversion und der Liste der verfügbaren Hardware-Execution-Provider. Verifizierung von `CPUExecutionProvider` und strukturierte Behandlung des optionalen `QNNExecutionProvider` (Protokollierung als Warning/Info-Meldung statt als kritischer Fehler).
* **ONNX Runtime Readiness (P-085):** Vorbereitung und Validierung der ONNX-Inferenz. Das `OnnxImageBackend` verifiziert das Vorhandensein der `onnxruntime`-Bibliothek (inklusive Protokollierung von Version und Execution Providern) und scannt das Modellpaket rekursiv nach `.onnx`-Dateien. Die gefundenen Modelle werden auf Existenz und Größe geprüft, um ihre prinzipielle Ladbarkeit sicherzustellen, ohne bereits eine `InferenceSession` zu instanziieren.
* **Generation Parameter Contract (P-082):** Durchgängige Transportierung aller 12 Inferenzparameter (`prompt`, `negative_prompt`, `model`, `backend`, `seed`, `width`, `height`, `steps`, `cfg`, `sampler`, `scheduler`, `batch_count`) von der GUI bis zum Inferenz-Backend. Vollständige Dokumentierung aller Parameter im Metadaten-Sidecar-JSON. Zeichnen einer erweiterten Parameter-Leiste (`Seed`, `Steps`, `CFG`) auf der Stub-Diagnosekarte (sowohl CPU/QNN-Stub als auch ONNX-Stub).
* **Live Preview Integration (P-081):** Automatische Aktualisierung des AI Generate Workspace nach erfolgreicher Generierung. Das erzeugte PNG-Bild wird per Pillow geladen, herunterskaliert und im Preview-Label des Inspectors dargestellt. Aktivierung der Aktionsschaltflächen *"Open in Library"* (Ausgabeordner öffnen), *"Open in Review"* (Bild in Standardbetrachter öffnen) und *"Save As"* (Bild kopieren/speichern unter), sobald ein valides Ausgabebild basierend auf der `GenerationResponse` erzeugt wurde.
* **Model Runtime Integration (P-081):** Verknüpfung von `ModelLoaderService` und `InferenceBackendFactory`. Der `GenerationExecutor` baut aus dem Ladeplan des ausgewählten Modells ein `RuntimeModel` auf und leitet dieses über den Adapter an die Fabrikmethode weiter. Das zugewiesene Backend (`StubImageBackend` oder `OnnxImageBackend`) verwendet die geladene Modell-ID dynamisch für die Beschriftung der Diagnose-Ausgabebilder und Metadaten-Sidecars, was fest codierte Modellnamen vollständig überflüssig macht. Protokollierung von `Selected Model`, `Runtime Model` und `Target Backend` im Inferenzlauf.
* **Inference Backend Plugin Framework (P-080):** Implementierung der `InferenceBackendFactory` zur dynamischen Registrierung und Verwaltung von Inferenz-Backends. Einführung des Platzhalters `OnnxImageBackend` (mit eigenem ONNX-Diagnosebild) neben dem `StubImageBackend`. Der `LocalImageGeneratorAdapter` wurde vollständig entkoppelt und bezieht Backend-Instanzen zur Generierung nun ausschließlich über the Factory per `backend.generate(job)`.
* **Inference Backend Foundation (P-079):** Einführung der abstrakten Schnittstellen-Klasse `InferenceBackend` und deren erster Implementierung `StubImageBackend`. Der `LocalImageGeneratorAdapter` wurde vollständig entkoppelt und zeichnet das Stub-Bild nicht mehr selbst, sondern delegiert die Inferenz und Dateierstellung an das zugrunde liegende Backend.
* **Stub Preview Image & Output Integration (P-078 & P-077):** Erzeugung eines informativen Diagnosebildes mit Phoenix-Design (Dunkelblau, 512x512-Pixel) inklusive Textmarkierungen für App-Name, Modell, Backend und Prompt-Auszug anstelle einer leeren schwarzen Fläche. Härtung der Ausgabeschnittstelle über Pillow (Behebung des Dateifehlers aus P-077) und automatische Generierung von JSON-Sidecar-Metadatendateien mit 9 zentralen Inferenzattributen zur nahtlosen Erkennung in der Phoenix-Galerie. Exponierung des `output_path` auf der `GenerationResponse`.
* **Local Image Generator Adapter Foundation (P-076):** Implementierung der Generator-Adapter-Stufe mit `LocalImageGeneratorAdapter` und dem `GenerationExecutor`. Der Executor steuert die Validierung des Modellinstallationsstatus über den `ModelLoaderService` und leitet die Aufträge an den Adapter weiter, welcher ein 1x1-Pixel PNG-Dummy-Bild erzeugt. Protokollierung des vollständigen Inferenz-Flusses (Executor -> Adapter -> Result) über Standard-Logging-Mechanismen zur Vorbereitung künftiger NPU/ONNX/QNN-Generatoren.

* **Navigation Preparation & Splash Size Fix (UX-006):** Ausblendung der "Image"-Schaltfläche aus der linken Seitenleisten-Navigation, um die UI auf zukünftige Produktvisionen vorzubereiten (Quelldateien bleiben funktionsfähig). Behebung der Splashscreen-Größe durch Umbau der Klasse `StartupOverlay` von einem 1400x900-Pixel-Frame-Overlay zu einem eigenständigen `tk.Toplevel`-Fenster mit festen Dimensionen (600x420 Pixel), rahmenlosem Design, zentrierter Bildschirmausrichtung und sanfter Alpha-Transparenz-Ausblendung.
* **Model Loader Foundation (P-074):** Implementierung des `ModelLoaderService` als sichere Schnittstelle zur Modellauflösung vor Generierungen. Der Loader prüft die Installation, scannt die zugehörigen Modelldateien, baut Ladepläne für die Ziel-Hardware (QNN, ONNX, CPU) und liefert strukturierte Resultate (`ModelResolveResult`) zurück, ohne Gewichte direkt in den Arbeitsspeicher zu laden. Integration des Loaders in den `GenerationController`, wodurch Generierungen mit nicht installierten Modellen frühzeitig mit der Fehlermeldung `"Model is not installed."` abgefangen werden.
* **Refresh Model Manager after Install/Uninstall (P-073.1):** Härtung und Behebung der UI-Aktualisierungslogik im Model Manager. Umstellung der Treeview- und Detailsuche von fragilen Zeilenindizes auf eindeutige Element-IDs (iids basierend auf `model_id`), wodurch willkürliche Listensortierungen bei Dateioperationen abgefangen werden. Hinzufügen einer Pfad-Eigenschaft („Pfad:“) im Inspector zur Visualisierung des absoluten Installationspfads. Dynamische Verknüpfung der Schaltflächenzustände (Installieren, Deinstallieren, Ordner öffnen) an den neuen Modellstatus und Integration automatischer Repository-Reloads bei Workspace-Wechseln in der Generierungsvorschau.
* **Model Validation 2.0 (P-073):** Umfassende Erweiterung der Modellvalidierung vor einer Installation im `ModelInstallService`. Die Methode `validate_model()` prüft nun neben Existenz und Leserechten auch erlaubte Modell-Dateiendungen (`.onnx`, `.bin`, `.safetensors`, `.gguf`, `.json`, `.pb`, `.pt`, `.pth`). Für Ordner wird mindestens eine Modell-Datei mit gültiger Endung verlangt. Die Methode liefert nun ein strukturiertes Resultat (Dictionary mit `success`, `message`, `warnings` und `size_bytes`) zurück, das Warnungen bei Dateigrößen (> 10 GB) oder bei Vorhandensein von Nicht-Modell-Dateien ausgibt.
* **Connect QNN Availability to Backend Discovery (P-072.2):** Anbindung der Verfügbarkeit des `QNNBackendAdapter` an die Diagnoseergebnisse des `BackendDiscoveryService`. Der Adapter meldet sich nun dynamisch als verfügbar (`True`), wenn im System sowohl das QNN SDK als auch die QNN Tools (`qnn-net-run.exe`) vorhanden sind. Zur Leistungssteigerung bei regelmäßigen UI-Refreshes wurde ein klassenweiter Cache (`_cached_is_available`) eingeführt. Alle temporären Debug-Ausgaben aus P-072.1 wurden rückstandsfrei aus dem `BackendManager` entfernt.
* **Backend Routing in GenerationController (P-072):** Integration des automatischen Backend-Routings im `GenerationController`. Während der Einreihung eines Generierungsauftrags wird der `model_name` der Generierungssitzung über das `ModelRepository` aufgelöst. Das am besten geeignete Backend wird über den `BackendManager` ermittelt, auf diesem aktiv geschaltet (sodass die UI-Statusleiste und der Inspector im AI Generate Workspace dynamisch aktualisiert werden) und der `ImageGenerationPipeline` übergeben. Das resultierende `GenerationResult` wird mit dem tatsächlichen Backend-Namen und den entsprechenden Metadaten angereichert.
* **Backend Manager Routing Foundation (P-071):** Einführung der Infrastruktur für automatische Backend-Auswahl in `BackendManager`. Die neue Methode `get_best_backend(model)` wertet das bevorzugte Backend eines Modells aus dem Repository als Primärpräferenz aus und führt andernfalls einen geordneten, robusten Fallback gemäß lokaler Hardware-Verfügbarkeit durch (Reihenfolge: Qualcomm QNN NPU -> ONNX Runtime -> CPU Fallback Stub).
* **Model Manager Card Appearance Restore (UX-005.1):** Wiederherstellung und Verfeinerung des Phoenix-Card-Designs für das Modell-Treeview im Model Manager. Durch Konfiguration von `borderwidth=0` und `relief="flat"` auf der Treeview- und Heading-Ebene wurden störende Standard-3D-Bordüren von Tkinter entfernt. Überschriften reagieren nun bei Hover mit einem Phoenix-Akzentfarbton-Mapping, wodurch sich die Tabelle nahtlos in die umgebende Karte integriert.
* **Model Manager Table Polish (UX-005):** Optimierung der Spaltenbreiten der Modell-Tabelle im Model Manager. Die Spalte „Aktiv“ wurde auf 45px Breite fixiert und vom automatischen Strecken ausgeschlossen. Die Spalten „Modellname“ (240px), „Kategorie“ (160px), „Ziel-Backend“ (130px) und „Status“ (180px) wurden neu gewichtet und so skaliert, dass wichtige Metadaten wie Kategorien („Text-to-Image“, „Text-to-Video“) und Download-Statusangaben ohne Kürzungen oder Abschneiden lesbar sind.
* **Local AI Model Installation Foundation (P-070):** Einführung der Model-Installationsinfrastruktur durch Erstellung des neuen `ModelInstallService`. Dieser Dienst validiert lokale Modelldateien/Ordner, berechnet deren Größe, überprüft den verfügbaren Speicherplatz auf der Festplatte mit einem 50MB-Sicherheits-Puffer und kopiert sie in den Standardordner `models`. Bei der Deinstallation werden installierte lokale Modelldateien sicher gelöscht. Der Installationsstatus und -pfad werden direkt im `ModelRepository` persisiert. Die Inspector-Buttons „Installieren“, „Deinstallieren“ und „Ordner öffnen“ im Model Manager wurden funktional angebunden und mit Benutzerdialogen (Dateiauswahl, Bestätigungen) versehen. Zukunftssichere Download- und Stornierungs-Hooks für Hugging Face/API-Anbindungen wurden vorbereitet.
* **AI Generate Workspace Redesign (UX-004):** Vollständiges Redesign des AI Generate Workspace. Gruppierung der Parametereingabe in fünf Bereiche (Model, Prompt, Image Size, Sampling, Output). Einführung eines scrollbaren AI Generation Inspectors mit Generation Status, Generation Information und Preview-Platzhalter. Integration von Sampler- und Scheduler-Dropdowns sowie drei deaktivierten Aktions-Buttons (Open in Library, Open in Review, Save As).
* **AI Model Manager Workspace Redesign (UX-003):** Vollständiges Redesign der Model-Manager-Oberfläche. Entfernung des unteren Eigenschaftsgitters zur Maximierung der Tabellenhöhe. Zusammenfassung aller Modell- und Systemumgebungs-Eigenschaften des selektierten Modells im scrollbaren rechten Inspector. Integration von fünf deaktivierten Aktions-Buttons (Installieren, Deinstallieren, Aktualisieren, Benchmark, Ordner öffnen).
* **Backend Discovery & Environment Detection (P-061 & P-061.1 & P-061.2 & P-061.3 & P-061.4):** Einführung des `BackendDiscoveryService` und der Datenklasse `DiscoveryResult` zur automatischen OS-, Python-, ONNX- und Qualcomm QNN SDK-Erkennung. Umgestaltung des Model-Inspectors in ein scrollbares Panel (`Canvas` + `Scrollbar`). Feinschliff der Treeview-Spaltenbreiten im Model Manager zur optimalen Lesbarkeit ohne Text-Clipping (z. B. "Available for Download"). Dynamisches Ausblenden der globalen rechten Seitenleiste (Inspector) im AI Model Manager Workspace zur Maximierung der Layoutbreite.
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
* **AI Generate UX Refresh (G-001):** Visuelle Fokussierung der Prompt-Eingabe durch einen eigenständigen, akzentgerahmten Composer, mehr Raum für die Bildbeschreibung und einen klar untergeordneten Negative Prompt. Die feste Generate-Action-Bar wurde mit stärkerer Typografie, konsistenten Abständen und eindeutiger Primäraktion modernisiert. Sämtliche Farben, Schriften und Abstände stammen aus dem Phoenix-ThemeManager; Dark-/Light-Parität bleibt gewahrt. Keine Änderungen an Controllern, Modellparametern oder Generierungspipelines.
* **Generate UX Fixes (G-001B):** Ergänzung eines laufzeitgebundenen Abbruch-Buttons über den bestehenden Cancel-Pfad einschließlich korrektem Queue-Lifecycle und eindeutigem `CANCELLED`-Status. Einführung eines benannten Phoenix-Progressbar-Styles mit zentraler grüner Success-Rolle für Dark und Light. Persistenz des zuletzt ausgewählten, installierten Produktmodells in einer lokalen Preference-Datei mit validiertem Fallback; Model Manager, WorkflowState und AI Generate verwenden weiterhin das gemeinsame ModelRepository als Single Source of Truth.
* **AI Generate No-Scroll Layout Fix (UX-004.3):** Optimierung der Benutzeroberfläche des Generierungs-Workspace zur Gewährleistung der vollständigen Sichtbarkeit aller Bedienelemente und Statusanzeigen auf 1080p-Monitoren ohne vertikales Scrollen. Die Steuerungselemente in den Bereichen Model, Image Size, Sampling und Output wurden platzsparend horizontal gruppiert (Breite/Höhe, CFG/Steps, Sampler/Scheduler, Seed/Batch nebeneinander). Textfelder für Prompt und Negative-Prompt wurden in ihrer Höhe reduziert (3 bzw. 1 Zeile), Abstände und Ränder minimiert. Die Scrollbar im rechten Inspector wurde entfernt und durch ein kompaktes, 4-spaltiges Eigenschaftsraster ersetzt.
* **Ausgabeverzeichnisschutz:** Refactoring von [gui_controller.py](file:///C:/SnapdragonAI/engine/gui_controller.py) und [realesrgan_core.py](file:///C:/SnapdragonAI/modules/realesrgan_core.py) zur Nutzung der neuen Dateinamens-Infrastruktur, um das versehentliche Überschreiben bestehender Bilder projektweit zu verhindern.
* Standardisierung der Benutzeroberfläche von klassischen, fensterbasierten Dialogen hin zu einem einheitlichen Single-Window-Design.
* Migration von Bildverarbeitungsschritten in dedizierte Module (`modules/qnn.py`, `modules/realesrgan_core.py`).

### Behoben
* **Functional Cancel (G-001D):** Der Job-Lifecycle bleibt während QNN-Worker-Statusausgaben stabil auf `RUNNING`, sodass die GenerationQueue den aktiven Auftrag zuverlässig findet. Ein dauerhaftes Cancel-Signal wird vom Button über Controller und Adapter bis zur tatsächlich laufenden physischen Backend-Instanz weitergereicht; deren SD1.5-/SD2.1-Subprozess wird terminiert und abgewartet. Verspätete PNG-/Sidecar-Ausgaben desselben Jobs werden verworfen. Reale QNN-Abbrüche nach fünf Sekunden bestätigen `CANCELLED`, beendete Worker und keine gespeicherten Bilder.
* **First Production Image Pipeline Audit (M-001):** Härtung der produktiven SD1.5-/SD2.1-QNN-Bildpipeline nach vollständigem mathematischem Vertragsvergleich. CLIP-Prompts unterstützen nun referenzkonforme doppelte HTML-Unescape-Normalisierung und Unicode-Buchstabensegmentierung. QNN-Worker werden bei Cancel tatsächlich beendet, ohne dass Worker-Statuszeilen den Abbruchzustand überschreiben; veraltete Resultatdateien werden vor dem Start entfernt und fehlende Workerresultate enthalten den Exitcode. QNN-Sessions werden bei Erfolg und Fehler garantiert einzeln finalisiert. Hardware-Regression bestätigt unveränderte SD1.5-/SD2.1-PNG-Hashes und weiterhin ausschließlich QNN/HTP ohne CPU-Fallback.
* **Gallery-Doppelklick ohne Thumbnail-Neuaufbau (P4-001A PO-Abnahme):** Einzel- und Doppelklick aktualisieren den Auswahlzustand bestehender Thumbnail-Karten nun in-place. Die Übergabe an Compare zerstört das Gallery-Grid nicht mehr und löst keinen erneuten asynchronen Thumbnail-Load aus; Kontextmenü und bestehender Compare-Workflow bleiben unverändert.
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
