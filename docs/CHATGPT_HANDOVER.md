# HK NPU STUDIO – ChatGPT-Handover

Stand: 24. September 2026, Tagesabschluss
Projekt: HK NPU STUDIO – Phoenix Engine  
Entwickler: Holger Kreuzhofen  
Entwicklungsrechner: Holger  
Clean-Testrechner: RC2CleanTest

> **AKTUELLER VORRANG-HINWEIS – 24.09.2026**
>
> Diese Datei enthält die vollständige historische Projektchronik. Bei Widersprüchen gilt immer der **neueste datierte Abschnitt**.
> Der verbindliche aktuelle Arbeitsstand steht im Abschnitt **„CHATGPT_HANDOVER – Ergänzung Tagesabschluss 24. September 2026 – VERSION 2.0 RC3 Build-/Packaging-Stand“** am Ende dieser Datei.
>
> **Aktueller Übergabestatus 24.09.2026:**
> - Release-Kandidat: **VERSION 2.0 RC3** (`display_version=2.0 RC3`, `package_version=2.0.0-rc.3`).
> - **Phoenix Image Lab = AI Fotorestaurierung**; Colorization, Generatives Füllen, Retusche und Object Removal sind aus dem RC3-Release-UI ausgeschlossen.
> - Faithful Photo Restore ist technisch/qualitativ für den definierten RC3-Pfad geprüft; neuronale Inferenz QNN/HTP/NPU-only, kein CPU-/GPU-AI-Fallback.
> - Final Release QA: **164/164 PASS**; kleine und große reale Restore-Läufe PASS.
> - DE/EN/ES, Versionsanzeige, README, User Guides und RC3 Release Notes sind aktualisiert.
> - Build-/Packaging-Blocker zu FiDeSR-Pfaden, QNN/HTP-Runtime, Photo-Restore-Ressourcen und Dokumentation wurden behoben.
> - Test-Harness: Photo-Restore-Contracts, RealESRGAN-Teardown und Tk-Order-Abhängigkeit behoben; letzter kombinierter Precheck-Scope **39/39 PASS**.
> - **Noch kein Build, Installer, Commit oder Push.**
> - Verbleibender praktischer Build-Blocker: freier Speicher auf C:. Letzt gemessen `14.639 GiB`; Ziel vor Build **≥17 GiB frei**.
> - Nächster exakter Schritt: 2–3 GB auf C: freimachen, dann finalen RC3 Build-Precheck erneut ausführen.
>
## Zweck

Diese Datei ist die verbindliche Arbeitsübergabe für die Fortsetzung mit einem anderen ChatGPT-Account. Sie enthält den bestätigten Projektstand, Holgers Arbeitsregeln, die heutigen Änderungen, Testergebnisse und den nächsten sicheren Schritt.

Ein neuer ChatGPT-Account soll diese Datei vollständig lesen und danach ohne erneute allgemeine Projektanalyse weiterarbeiten. Bei Abweichungen haben der aktuelle Git-Stand und neue Testergebnisse Vorrang.

## Startanweisung

Du übernimmst die Weiterentwicklung von Snapdragon AI Studio – Phoenix Engine gemeinsam mit Holger Kreuzhofen.

- Antworte Holger immer auf Deutsch.
- Arbeite tokenoptimiert: eng begrenzte Dateien, keine wiederholte Gesamtanalyse, keine unnötigen Volltests.
- PowerShell für einfache, eindeutig begrenzte Prüfungen und Textkorrekturen verwenden.
- Codex nur für notwendige Codeanalyse oder Implementierung verwenden.
- Antigravity nur bei einem klaren zusätzlichen Nutzen verwenden.
- Bei Codex-/Antigravity-Aufträgen am Ende immer den vollständigen integrierten Prompt ausgeben, nie nur Nachträge.
- PowerShell-Befehle immer mit vollständigen absoluten Windows-Pfaden ausgeben.
- Keine Implementierung, kein Commit und kein Push ohne den mit Holger abgestimmten Schritt.
- Niemals `git add .` verwenden.
- Bekannte untracked Dateien nicht verändern, löschen oder versehentlich stagen.
- Vor jedem Commit ausschließlich die erwarteten Dateien stagen und den staged Diff prüfen.
- Vor einem Push Tests, Diff und Commitinhalt bestätigen.
- UI muss dem bestehenden Snapdragon-AI-Studio-/Phoenix-Design entsprechen.
- Farben ausschließlich aus bestehenden Phoenix-Theme-Tokens verwenden; Light und Dark gleichzeitig berücksichtigen.
- Der Entwicklerrechner allein ist kein Release-Nachweis.
- Installer-, First-Run-, Pfad-, Sprach-, DPI-, Fensterzustands- und Systemintegrationsänderungen müssen auf RC2CleanTest geprüft werden.
- Holger ausdrücklich darauf hinweisen, wenn RC2CleanTest erforderlich ist.
- WinRAR-Sicherungen nur behandeln oder erwähnen, wenn Holger ausdrücklich danach fragt. Nicht selbst daran erinnern.
- Wenn Holger eine Arbeitspause oder Feierabend ankündigt, diese zentrale `CHATGPT_HANDOVER.md` aktualisieren.
- Nach jeder Handover-Aktualisierung die vollständige Datei zum Download bereitstellen. Holger verwendet anschließend die Desktop-Datei `C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd`, um den Download nach `C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md` zu übernehmen und dort zu überschreiben.

## Reddit-Regel

Bei Reddit-Antworten erhält Holger zuerst eine deutsche Fassung und danach die englische Version für Reddit. Die Antwort soll natürlich und persönlich klingen und nicht offensichtlich KI-generiert wirken.

Unter jede Reddit-Antwort gehört exakt:

**Holger Kreuzhofen**  
Founder & Lead Developer  
Snapdragon AI Studio – Phoenix Engine

## Rechner und wichtige Pfade

### Entwicklungsrechner Holger

- Projekt: `C:\SnapdragonAI`
- Python ARM64: `C:\Program Files\Python311-arm64\python.exe`
- Frozen-App: `C:\SnapdragonAI\dist\SnapdragonAIStudio\SnapdragonAIStudio.exe`
- Installer-Ausgabe: `C:\SnapdragonAI\dist\installer`

### RC2CleanTest

- Benutzerprofil: `C:\Users\RC2CleanTest`
- App-Daten: `C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio`
- Preferences: `C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio\data\preferences.json`
- Ausgabeordner: `C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio\output`
- Modellordner: `C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio\models`
- Wiederherstellbare RC2A-App-Datensicherung: `C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio RC2A Backup`

Die RC2A-App-Datensicherung vorerst nicht löschen.

## Aktueller Git-Stand

Branch: `main`

- Lokaler HEAD: `20beee67 UI: Add optional gallery hover preview`
- Davor: `e2d02fd UI: Make Phoenix views DPI responsive`
- Weitere lokale Commits: `e4e2a87 UI: Compact Phoenix Boost preview` und `1368aaa UI: Keep model installation controls visible`
- GitHub `origin/main`: `dfffc69 UI: Color gallery action icons`
- Lokaler Branch ist gegenüber `origin/main` **vier Commits voraus**.
- Die vier neuen Commits sind noch nicht auf `origin/main` gepusht.
- Ein kurzzeitig verwendeter öffentlicher Sicherungsbranch `backup/pre-gallery-hover-2026-08-22` wurde auf Holgers ausdrücklichen Wunsch wieder gelöscht. Keinen öffentlichen Sicherungsbranch ohne vorherige klare Erklärung und ausdrückliche Freigabe anlegen.
- Am Tagesabschluss sind keine versionierten Dateien geändert oder gestaged.
- Es sind nur bekannte untracked Dateien vorhanden.

### Relevante Commitfolge

| Commit | Inhalt | Status |
| --- | --- | --- |
| `614d8fb` | Lokalisierte SD3.5-Testerwartungen korrigiert | getestet und gepusht |
| `4616582` | Alten Preset-Test mit lokalem Modellvertrag isoliert | getestet und gepusht |
| `1d4f65d` | Qwen-Legacy-Fortschrittsformat unterstützt | getestet und gepusht |
| `8f6b82d` | Installationssprache für Erststart erhalten | RC2CleanTest, gepusht |
| `85cf632` | Galerie öffnet tatsächlichen Ausgabeordner | RC2CleanTest, gepusht |
| `6a7b79c` | Einstellungen zeigen aktive Anwendungspfade | RC2CleanTest, gepusht |
| `44cbce8` | RC2B-Testbuild vorbereitet | gebaut, getestet, gepusht |
| `f6d09ea` | Galerie- und Pfadanzeige poliert | getestet und gepusht |
| `dfffc69` | Farbige Galerie-Aktionssymbole | getestet und gepusht |
| `1368aaa` | Modellinstallation bei hoher Skalierung erreichbar halten | Tests bestanden; Build/RC2CleanTest offen |
| `e4e2a87` | Phoenix-Boost-Vorschau kompakt und maximierbar | Tests bestanden; Build/RC2CleanTest offen |
| `e2d02fd` | Phoenix-Ansichten bei hoher Windows-Skalierung responsiv | Tests und direkte Python-Abnahme bestanden; Build/RC2CleanTest offen |
| `20beee67` | Optionale Galerie-Hover-Vorschau mit responsiver Toolbar | Tests und direkte Python-Abnahme bestanden; Build/RC2CleanTest offen |

### Bekannte untracked Dateien

```text
RC2A_RELEASE_NOTES_FINAL.md
RC2_GITHUB_NOTES_CURRENT.md
RC2_GITHUB_NOTES_CURRENT_UTF8.md
RC2_GITHUB_NOTES_WITH_KNOWN_ISSUE.md
RC2_RELEASE_NOTES.md
RC2_RELEASE_NOTES_CLEAN.md
README_BEFORE_RC2A_DOCS.md
README_LOCKED_BACKUP.md
assets/brand/ChatGPT Image 9. Aug. 2026, 21_42_14.png
assets/brand/reddit_profilbild_512x512.jpg
assets/brand/snapdragon-ai-studio-x-header-1500x500.png
docs/CHATGPT_HANDOVER.md
docs/SnapdragonAI_ChatGPT_Handover_2026-08-21.md
presets/wolf.json
temp_traceback.txt
temp_venv/
```

## Heutige Änderung 1: Reddit-BUG1 / hohe Windows-Skalierung

### Bestätigte Ursache

- Der rechte Modell-Inspector war nicht scrollbar.
- Sein Inhalt konnte bei hoher Windows-Skalierung die untere Installationsschaltfläche aus dem sichtbaren Bereich drücken.
- Der direkte Modelldownload-Dialog verwendete feste Größen ohne ausreichende Begrenzung auf den Windows-Arbeitsbereich.

### Implementierung

Commit: `1368aaa UI: Keep model installation controls visible`

Geänderte Dateien:

```text
C:\SnapdragonAI\widgets\phoenix\views\model_manager_view.py
C:\SnapdragonAI\dialogs\model_direct_download_dialog.py
C:\SnapdragonAI\dialogs\studio_dialog.py
C:\SnapdragonAI\tests\test_model_download_dialog_layout.py
```

Umgesetzt:

- Der rechte Modell-Inspector besitzt einen eigenen Canvas-Scrollbereich für Details.
- Die bestehende `action_frame` mit „Modell installieren“ bleibt fest außerhalb des Scrollbereichs.
- Modellliste und Inspector besitzen getrennte Mausradbereiche.
- Der Download-Dialog hält Titel und Footer außerhalb eines scrollbaren Mittelbereichs.
- `StudioDialog` begrenzt Dialoggröße, Mindestgröße und Position auf den Windows-Arbeitsbereich.
- Bei ausreichend großem Arbeitsbereich bleiben die bisherigen Dialoggrößen erhalten.
- Download-, Installations- und Modelllogik wurden nicht verändert.

### Bestätigte Tests

- Neuer Layouttest: `3 passed`
- `test_model_direct_install_flow.py`: `30 passed, 22 subtests passed`
- `test_model_manager_beginner.py`: `7 passed`
- `test_model_manager_release_sections.py`: `5 passed`
- `test_release_polish_final.py`: `4 passed`
- `test_sd35_installer_state_machine.py`: `32 passed`

Summe dieses Prüfblocks: 81 Pytest-Tests plus 22 Subtests bestanden.

### Status BUG1

Quellcode und Tests sind abgeschlossen, aber die Korrektur ist noch nicht im Frozen-Build und noch nicht auf RC2CleanTest geprüft. Öffentlich deshalb noch nicht als vollständig behoben bezeichnen.

## Heutige Änderung 2: Phoenix-Boost-Vorschau

Commit: `e4e2a87 UI: Compact Phoenix Boost preview`

Geänderte Dateien:

```text
C:\SnapdragonAI\widgets\phoenix\views\prompt_view.py
C:\SnapdragonAI\tests\test_expandable_prompt.py
```

Umgesetzt:

- Zielgröße von `760×760` auf kompakte `760×660` reduziert.
- Mindestgröße `640×520`.
- Größe und Position werden über die vorhandenen `StudioDialog`-Arbeitsbereichshilfen begrenzt.
- Vertikaler Scrollbereich bleibt als Fallback bei geringer Arbeitshöhe erhalten.
- Die Aktionsleiste liegt fest außerhalb des Scrollbereichs.
- Originalprompt und optimierter Prompt stehen gleich breit nebeneinander.
- Vorhandener negativer Prompt und empfohlene Ergänzung stehen gleich breit nebeneinander.
- Parametervergleich, Modellhinweis und Optionen bleiben erhalten.
- Alle bestehenden Callbacks bleiben verbunden: Einrichtung, Status, Fortschritt, Restzeit, Vorlage, Übernehmen und Abbrechen.
- `popup.resizable(True, True)` erlaubt normale Größenänderung.
- Nur Phoenix Boost ist nicht mehr `transient`, damit Windows die normale Titelleiste mit Maximieren/Wiederherstellen bereitstellen kann.
- Presets, Generierungsparameter und ControlNet bleiben weiterhin `transient`.
- Light und Dark verwenden weiterhin bestehende `PHOENIX_THEME`-Werte.

### Wichtige Reparatur während der Prüfung

Eine PowerShell-Textkorrektur entfernte zwischenzeitlich alle vier identischen `popup.transient(...)`-Zeilen. Vor dem Commit wurden die drei fremden Dialogzeilen gezielt wiederhergestellt.

Bestätigter Endstand in `prompt_view.py`:

```text
3347: popup.transient(self.winfo_toplevel())
3435: popup.transient(self.winfo_toplevel())
4861: popup.transient(self.winfo_toplevel())
```

Im finalen Diff wird genau eine Transient-Zeile entfernt: die Phoenix-Boost-Zeile.

### Bestätigte Tests

- fokussierter Booster-Fenstertest: `1 passed`
- zwei korrigierte Booster-/Ollama-Tests: `2 passed`
- vollständiges `tests/test_expandable_prompt.py`: `69 passed`

Die zwei anfänglichen Fehler waren Testfehler:

- `PhoenixButton` stellt den Callback über `.command` bereit, nicht über `cget("command")`.
- Der alte Test erwartete `wraplength=470`; das kompakte Layout verwendet bewusst `500`.

## Heutige Änderung 3: Ansichtsübergreifender DPI-/Layout-Sprint

Commit: `e2d02fd UI: Make Phoenix views DPI responsive`

Der bei 175 % Windows-Skalierung bestätigte BUG1 war ansichtsübergreifend. Die Korrektur wurde auf die betroffenen Phoenix-Views, unmittelbar notwendige Vergleichskomponenten, Übersetzungen und fokussierte Tests begrenzt.

### Commit-Inhalt

```text
C:\SnapdragonAI\controllers\compare_workspace_controller.py
C:\SnapdragonAI\locales\de_DE.json
C:\SnapdragonAI\locales\en_US.json
C:\SnapdragonAI\locales\es_ES.json
C:\SnapdragonAI\tests\test_compare_release_readiness.py
C:\SnapdragonAI\tests\test_expandable_prompt.py
C:\SnapdragonAI\tests\test_home_first_run.py
C:\SnapdragonAI\tests\test_model_download_dialog_layout.py
C:\SnapdragonAI\tests\test_plugin_view.py
C:\SnapdragonAI\tests\test_settings_view.py
C:\SnapdragonAI\widgets\phoenix\compare\compare_image_canvas.py
C:\SnapdragonAI\widgets\phoenix\compare\compare_panel.py
C:\SnapdragonAI\widgets\phoenix\compare\compare_toolbar.py
C:\SnapdragonAI\widgets\phoenix\views\compare_view.py
C:\SnapdragonAI\widgets\phoenix\views\home_view.py
C:\SnapdragonAI\widgets\phoenix\views\model_manager_view.py
C:\SnapdragonAI\widgets\phoenix\views\plugin_view.py
C:\SnapdragonAI\widgets\phoenix\views\prompt_view.py
C:\SnapdragonAI\widgets\phoenix\views\settings_view.py
```

### Umsetzung je Ansicht

- Modell-Manager: Die Canvasbreite steuert die Breite des eingebetteten Inspector-Inhalts und die dynamischen Textumbruchbreiten. Die Installationsleiste bleibt fest sichtbar.
- KI-Bildgenerierung: Parameterinhalt und Inspectorinformationen besitzen begrenzte lokale Scrollbereiche. Werkzeuggruppen brechen responsiv um. Lange Status- und Aktionstexte verwenden die tatsächlich zugewiesene Widgetbreite. Die Action-Bar mit Generate-Button bleibt fest getrennt.
- Untere Generierungsstatusleiste: Die sechs bestehenden Segmente verwenden ein responsives Grid und reservieren ihre tatsächlich benötigte Footerhöhe. Kein Segment wird entfernt oder gekürzt.
- Einstellungen: Der Karteninhalt ist vertikal scrollbar; Speichern und Zurücksetzen bleiben fest außerhalb.
- Startseite: Der zentrale Inhalt ist scrollbar; Header und Navigation bleiben außerhalb.
- Erweiterungen: Fester Header, schrumpfbarer Plugin-Canvas und feste Installationsleiste verwenden getrennte Grid-Zeilen. „Plugin installieren“ bleibt bei geringer Höhe sichtbar.
- Bildvergleich: Toolbargruppen brechen kontrolliert um. Der Vergleichsbereich ist scrollbar und beide Panels behalten eine Mindesthöhe für die Bildfläche.
- Bildvergleich-Panning: Drag-Panning ist ausschließlich auf den Bild-Canvases gebunden, auf Bildgrenzen begrenzt und beim Resize geklemmt. Bei aktiver Synchronisierung werden normalisierte Pan-Positionen übertragen.
- Synchronisierung: „Synchron: Ein/Aus“ ist ein echter Umschalter; Buttonzustand, Status und Pan-Logik verwenden denselben Zustand.
- Metadatenvergleich: Eine vollbreite, dynamisch umbrochene Phoenix-Infozeile erklärt fehlende, einseitige, identische oder unterschiedliche Generierungsmetadaten. Die segmentierte Statusleiste zeigt nur die Kurzfassung.

### Unveränderte Logik

Modell-, Installations-, Generierungs-, Galerie-, Vergleichs- und Plugin-Fachlogik blieben unverändert. Insbesondere Laden, Fit, Zoom, Tauschen, Metadatenextraktion, Generierung sowie die vorhandenen Callback-Zuordnungen wurden nicht ersetzt. Die Vergleichs-Toolbar-Callback-Identität ist regressionsgetestet.

### Theme und Sprachen

- Neue Container verwenden vorhandene `PHOENIX_THEME`-Tokens.
- Scrollbars verwenden den bestehenden `Phoenix.Vertical.TScrollbar`-Style.
- DE-, EN- und ES-Beschriftungen werden dynamisch gemessen oder umbrochen und nicht gekürzt.
- Keine globale Schriftverkleinerung, keine isolierten Farbcodes und keine Änderung der Windows-Skalierung.

### Bestätigte automatisierte Tests

- `test_model_download_dialog_layout.py`: `3 passed`
- fokussierter KI-Toolbar-Test: `1 passed`
- `test_settings_view.py`: `7 passed`
- `test_home_first_run.py`: `9 passed`
- `test_compare_release_readiness.py`: `6 passed`
- `test_plugin_view.py`: `1 passed`
- `test_plugin_release_readiness.py`: `6 passed`
- `test_expandable_prompt.py`: `72/72 passed`; wegen der 30-Sekunden-Grenze in überschneidungsfreien Node-ID-Gruppen vollständig nachgewiesen
- `py_compile` und `git diff --check`: erfolgreich; nur bestehende LF-/CRLF-Hinweise

### Manuelle Abnahme

- Rechner: Entwicklungs-PC Holger
- Testart: direkter Python-App-Test über `C:\SnapdragonAI\gui_v2.py`
- keine Frozen-App, keine Überinstallation, keine saubere Neuinstallation
- Windows-Skalierung: 175 %
- Dark Mode
- Modell-Manager, KI-Bildgenerierung, Einstellungen, Startseite, Bildvergleich und Erweiterungen wurden nach den Korrekturen von Holger abgenommen.

Die Frozen-App und RC2CleanTest enthalten diesen Commit noch nicht.

## Heutige Änderung 4: Optionale Galerie-Hover-Vorschau

Commit: `20beee67 UI: Add optional gallery hover preview`

### Commit-Inhalt

```text
C:\SnapdragonAI\locales\de_DE.json
C:\SnapdragonAI\locales\en_US.json
C:\SnapdragonAI\locales\es_ES.json
C:\SnapdragonAI\tests\test_gallery.py
C:\SnapdragonAI\tests\test_gallery_hover_toggle.py
C:\SnapdragonAI\widgets\phoenix\gallery\thumbnail_area.py
C:\SnapdragonAI\widgets\phoenix\gallery\thumbnail_widget.py
C:\SnapdragonAI\widgets\phoenix\gallery\toolbar.py
C:\SnapdragonAI\widgets\phoenix\views\gallery_view.py
```

### Produktvertrag und Umsetzung

- Preference: `gallery_hover_preview_enabled`.
- Fehlender oder ungültiger Preference-Wert bedeutet sicher `True`.
- Bei „Ein“ öffnet die bestehende Hover-Vorschau weiterhin unmittelbar.
- Es wurde ausdrücklich keine Verzögerungs-, `after`- oder Callback-ID-Architektur eingeführt.
- Bei „Aus“ unterdrückt `_on_enter` die Vorschauerzeugung vollständig.
- Beim Ausschalten werden offene Vorschaufenster aller vorhandenen Thumbnails geschlossen und deren Referenzen bereinigt.
- Neue Thumbnails erhalten einen zentralen Getter aus der Gallery-View; es existiert keine veraltete Zustandskopie.
- Auswahl, Doppelklick, Kontextmenü, Refresh, Such-, Sortier-, Größen- und Filterzustände sowie deren Callbacks blieben unverändert.

### Phoenix-Design

- Der Umschalter ist ein bestehender `PhoenixButton`, kein Standard-Checkbutton.
- Er steht direkt nach „Ausgabeordner öffnen“ und vor „Aktualisieren“.
- Das vorhandene `image`-Icon wird mit dem bestehenden roten Phoenix-Theme-Token dargestellt.
- Der Button verwendet den vorhandenen neutralen Galerie-Toolbar-Stil einschließlich Phoenix-Hover-/Pressed-Verhalten.
- Alle sieben bestehenden Toolbargruppen werden anhand ihrer angeforderten Breiten umgebrochen.
- Breit: ursprüngliche Reihenfolge in einer Zeile.
- Mittel: Aktionen, danach volle mitwachsende Suchzeile, danach Sortierung, Größe und Filter.
- Schmal: Aktionen und Dropdowns brechen geordnet weiter um; Suche bleibt sichtbar und breit.
- Keine neue Buttoninstanz beim Reflow; alle Gruppen bleiben sichtbar und anklickbar.

### Bestätigte Tests

- `tests/test_gallery_hover_toggle.py`: `6 passed`
- `tests/test_gallery.py`: `10 passed`
- `py_compile` und `git diff --check`: erfolgreich

### Manuelle Abnahme

- Rechner: Entwicklungs-PC Holger
- Testart: direkter Python-App-Test über `C:\SnapdragonAI\gui_v2.py`
- keine Frozen-App, keine Überinstallation, keine saubere Neuinstallation
- Windows-Skalierung: 175 %
- Dark und Light Mode
- breite und schmale Galerieansicht, Toggle Ein/Aus, rote Icon-Darstellung, vollständige Beschriftungen und responsiver Toolbar-Reflow wurden von Holger abgenommen.

Die Frozen-App und RC2CleanTest enthalten diesen Commit noch nicht.

## Bereits bestätigte RC2B-Arbeiten

### Reddit-BUG2

Galerie öffnet den tatsächlichen `config.OUTPUT_DIR` direkt im Explorer und keinen Ordnerauswahldialog. Auf RC2CleanTest bestätigt.

### Reddit-BUG3

Einstellungen zeigen die tatsächlich verwendeten `%LOCALAPPDATA%`-Pfade für Ausgabe und Modelle. Die Felder sind lesbar und schreibgeschützt; funktionslose Auswahlschaltflächen wurden entfernt. Auf RC2CleanTest in Light und Dark bestätigt.

### Reddit-BUG4

Die im Installer gewählte Sprache wird bei einem echten Erststart als initiale Preferences-Datei gespeichert. Vorhandene Preferences bleiben unangetastet. Englischer Erststart auf RC2CleanTest bestätigt.

### SD3.5

Frische SD3.5-Modellinstallation und anschließende Nutzung auf RC2CleanTest erfolgreich.

## Aktueller RC2B-Installer ist jetzt veraltet

Der zuvor gebaute und getestete Installer lautet:

`C:\SnapdragonAI\dist\installer\SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe`

Seine damalige SHA-256-Prüfsumme:

`F79B2C879412AC31D268157BC5A49701497C4E570E0D0F1FEDF75BB4887307F5`

Dieser Installer enthält die vier lokalen Commits `1368aaa`, `e4e2a87`, `e2d02fd` und `20beee67` noch nicht. Er darf nicht für die Abnahme der neuen UI-Korrekturen und der Galerie-Hover-Funktion verwendet oder als finales RC2B-Artefakt veröffentlicht werden.

## Testumgebungseigenschaft

Tk-GUI-Testmodule können beim gemeinsamen Lauf in einem Python-Prozess sporadisch Tcl-Lebenszyklusfehler wie `invalid command name "tcl_findLibrary"` zeigen. Die betroffenen Module bestehen jeweils in separaten Python-Prozessen. GUI-Module bei Bedarf getrennt ausführen und keinen allgemeinen Testinfrastruktur-Sprint starten, solange kein Produktfehler nachweisbar ist.

Tests immer aus `C:\SnapdragonAI` starten. Ein Teststart aus `C:\Windows\System32` oder `C:\Users\holge` führt zu `ModuleNotFoundError: No module named 'app'` beziehungsweise fehlenden Projektimports und ist kein Produktfehler.

## Nächster sicherer Schritt bei Wiederaufnahme

### 1. Zustand prüfen

```powershell
Set-Location -LiteralPath 'C:\SnapdragonAI'

& 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' status --short --branch
& 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' rev-parse HEAD
& 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' rev-parse origin/main
& 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' log -5 --oneline --decorate
```

Erwartet:

```text
HEAD: 20beee67
origin/main: dfffc69
main...origin/main [ahead 4]
```

Im Status dürfen ausschließlich die dokumentierten untracked Dateien erscheinen.

### 2. Nach Holgers ausdrücklicher Freigabe einen Frozen-App-Build erstellen

- Rechner: Entwicklungs-PC Holger
- Vorgang: Frozen-App-Build, keine Installation
- keine Überinstallation, keine saubere Neuinstallation

Snapdragon AI Studio vorher vollständig schließen.

```powershell
Set-Location -LiteralPath 'C:\SnapdragonAI'

& 'C:\Program Files\Python311-arm64\python.exe' `
  'C:\SnapdragonAI\tools\build_app.py'

if ($LASTEXITCODE -ne 0) {
    throw 'Abbruch: Der Frozen-App-Build ist fehlgeschlagen.'
}
```

Noch keinen Push ausführen.

### 3. Direkter Frozen-App-Sicht- und Funktionstest

- Rechner: Entwicklungs-PC Holger
- Testart: direkter Frozen-App-Test
- keine Überinstallation, keine saubere Neuinstallation
- Windows-Skalierung: 100 %, 125 %, 150 % und besonders 175 %
- jeweils Light und Dark Mode

Frozen-App starten:

```powershell
Start-Process `
  -FilePath 'C:\SnapdragonAI\dist\SnapdragonAIStudio\SnapdragonAIStudio.exe'
```

Mindestens prüfen:

1. Modell-Manager: Inspector-Umbruch, getrennte Scrollbereiche, dauerhaft sichtbare Installationsleiste und Installationsdialog-Footer.
2. Phoenix Boost: kompakte Ansicht, Prompt-Paare, fester Footer, Maximieren/Wiederherstellen, Übernehmen und Abbrechen.
3. KI-Bildgenerierung: responsive Werkzeuggruppen, linker Parameterscrollbereich, vollständiger Inspectorstatus, feste Action-Bar und vollständig sichtbare Footersegmente.
4. Einstellungen: Inhalt vollständig scrollbar bei festem Speichern/Zurücksetzen.
5. Startseite: Schnellzugriff, Status und letzte Generierungen vollständig erreichbar; Header und Navigation bleiben fest.
6. Bildvergleich: Bilder sichtbar, Toolbar vollständig, Pan bei 50/100/200 %, Synchron Ein/Aus, Fit, Resize, Metadateninfo und Status.
7. Erweiterungen: „Plugin installieren“ bleibt bei geringer Höhe sichtbar.
8. Galerie: Hover-Vorschau Ein/Aus, unmittelbare Vorschau bei Ein, keine Vorschau bei Aus, rote Icon-Darstellung sowie Toolbar breit/schmal ohne abgeschnittene Such-, Sortier-, Größen- oder Filtergruppen.

### 4. Danach zwingend neuer Installer und RC2CleanTest

Erst nach bestandenem direkten Frozen-App-Test und erneuter ausdrücklicher Freigabe:

1. neuen RC2B-Installer bauen,
2. neue SHA-256-Prüfsumme erfassen,
3. Rechner: RC2CleanTest,
4. Testart: saubere Neuinstallation des neuen RC2B-Installers,
5. keine Überinstallation für diese finale Default-/Preference-/DPI-Abnahme,
6. 100 %, 125 %, 150 % und 175 % Skalierung prüfen,
7. Light und Dark prüfen,
8. Modell-Manager, Modelldownload-Dialog, Phoenix Boost, KI-Bildgenerierung, Einstellungen, Startseite, Bildvergleich, Erweiterungen und Galerie-Hover testen,
9. insbesondere den Standardwert `gallery_hover_preview_enabled=True`, Umschalten, Persistenz nach Neustart und Toolbar-Reflow prüfen,
10. erst nach vollständiger Abnahme und Holgers ausdrücklicher Freigabe die vier lokalen Commits auf `origin/main` pushen und über Veröffentlichung sprechen.

## Veröffentlichungsstatus

- RC2B ist noch nicht final veröffentlicht.
- BUG2, BUG3 und BUG4 sind behoben und clean getestet.
- BUG1 einschließlich der ansichtsübergreifenden DPI-Korrekturen ist implementiert, automatisiert getestet und im direkten Python-App-Test auf Holger abgenommen; Frozen-/Clean-Test steht aus.
- Phoenix Boost ist implementiert und unit-/regressionsgetestet; der direkte Python-App-Test ist erfolgt, Frozen-/Clean-Test steht aus.
- Die Galerie-Hover-Funktion ist implementiert, automatisiert getestet und im direkten Python-App-Test bei 175 % in Light und Dark abgenommen; Frozen-/Clean-Test steht aus.
- Die lokalen Commits `1368aaa`, `e4e2a87`, `e2d02fd` und `20beee67` sind noch nicht auf `origin/main`.
- Noch keinen GitHub-Release erstellen und die neuen Punkte öffentlich noch nicht als final behoben bezeichnen.

## Tagesabschlussstatus

- Arbeitsbaum ohne Änderungen an versionierten Dateien.
- Lokaler Branch vier Commits vor `origin/main`.
- Lokaler HEAD: `20beee67 UI: Add optional gallery hover preview`.
- `origin/main` unverändert auf `dfffc69`.
- Keine getrackten Änderungen; nur die bekannten untracked Dateien.
- Kein Remote-Sicherungsbranch vorhanden.
- Kein Frozen-Build nach den vier lokalen Commits.
- Kein neuer Installer nach den vier lokalen Commits.
- Kein RC2CleanTest der vier lokalen Commits.
- Kein Push auf `origin/main`.
- Nächste Aktion nach Holgers Freigabe: Zustand prüfen, Frozen-App aus `20beee67` bauen und auf dem Entwicklungs-PC Holger direkt testen.
- Diese vollständige Handover-Datei zum Download bereitstellen. Holger übernimmt sie ausschließlich über `C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd` nach `C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md`.
- WinRAR nur auf ausdrücklichen Wunsch Holgers behandeln.
# Ergänzung: Tagesabschluss 23. August 2026

Diese Ergänzung schreibt den Stand vom 22. August vollständig fort. Die älteren Abschnitte bleiben als Arbeitschronik erhalten. Bei Statusangaben, Buildwerten, Git-Stand und nächsten Schritten hat diese Ergänzung Vorrang.

## Verbindliche Aufgabenverteilung

1. ChatGPT: Koordination, Eingrenzung und Ergebnisbewertung.
2. PowerShell: Bestandsaufnahme, Prüfungen, Builds und exakt freigegebene Git-Schritte.
3. Codex: gezielte Quellcodeänderungen und zugehörige Tests.
4. Antigravity: Dokumentation, sprachliche Überarbeitung und größere Konsistenzprüfungen.
5. Holger: manuelle App-, Frozen- und RC2CleanTest-Abnahme.

Codex und Antigravity sparsam einsetzen. Für eindeutig begrenzte Prüfungen, Builds und Git-Schritte PowerShell bevorzugen.

## Aktualisierte Reddit- und Veröffentlichungsregel

- Auf Reddit wird ausschließlich auf Englisch veröffentlicht.
- Eine deutsche Fassung kann intern zur Kontrolle für Holger erstellt werden, wird aber nicht auf Reddit gepostet.
- Reddit-Texte sollen natürlich, persönlich und nicht offensichtlich KI-generiert wirken.
- Unter Reddit-Veröffentlichungen gehört weiterhin exakt:

**Holger Kreuzhofen**  
Founder & Lead Developer  
Snapdragon AI Studio – Phoenix Engine

### Noch offene Veröffentlichungsreihenfolge

Der GitHub Release ist veröffentlicht. Die Social-/Community-Veröffentlichung ist noch nicht vollständig abgeschlossen.

1. Reddit: englischer Veröffentlichungstext ist vorbereitet; tatsächliche Veröffentlichung durch Holger ist noch nicht bestätigt.
2. Danach Qualcomm.
3. Danach Instagram.
4. Danach Facebook.
5. Danach Hugging Face.
6. Danach Microsoft.

Jeden Kanal einzeln vorbereiten, an Format und Zielgruppe anpassen und erst nach Holgers Freigabe veröffentlichen. Keine dieser Veröffentlichungen als erledigt melden, solange Holger sie nicht bestätigt hat.

## Finaler Git- und Veröffentlichungsstand

Branch: main

- Lokaler HEAD: 796043f6 Docs: Align RC2B release notes with publication
- origin/main: 796043f6 Docs: Align RC2B release notes with publication
- main und origin/main stimmen überein.
- Keine getrackten oder gestagten Arbeitsbaumänderungen.
- Nur die bekannten untracked Dateien sind vorhanden.
- Annotierter Release-Tag: v2.0.0-rc.2b
- Der Tag zeigt unverändert auf 11325ce712be24ffab5eeb677aa34c1e434ec633.
- Der spätere Commit 796043f6 synchronisiert ausschließlich das getrackte Release-Notes-Quelldokument mit der öffentlichen GitHub-Beschreibung. Der Release-Tag wurde nicht verschoben.
- Kein Force-Push und kein öffentlicher Sicherungsbranch.

### Am 23. August veröffentlichte Commitfolge

| Commit | Inhalt | Status |
| --- | --- | --- |
| 1368aaaa | Modellinstallationsaktionen bei hoher Skalierung sichtbar halten | gebaut, RC2CleanTest, veröffentlicht |
| e4e2a87f | Kompakte und maximierbare Phoenix-Boost-Vorschau | gebaut, RC2CleanTest, veröffentlicht |
| e2d02fd8 | Phoenix-Ansichten DPI-responsiv gestalten | gebaut, RC2CleanTest, veröffentlicht |
| 20beee67 | Optionale Galerie-Hover-Vorschau | gebaut, RC2CleanTest, veröffentlicht |
| 5500294e | Umbruch des Generierungs-Aktionstextes korrigieren | getestet, gebaut, veröffentlicht |
| c6772c3d | Runtime-Output aus Release-Installer ausschließen | getestet, gebaut, veröffentlicht |
| a1e36a5f | Plugin-Installationsbereich an Phoenix-Design angleichen | getestet, gebaut, veröffentlicht |
| e5f7b7a3 | Ausgabeordner vor Explorer-Aufruf sicher anlegen | getestet, gebaut, veröffentlicht |
| 5f61c235 | Benutzerhandbücher für RC2B aktualisieren | geprüft, veröffentlicht |
| 11325ce7 | RC2B-Veröffentlichungsdokumentation vorbereiten | geprüft, veröffentlicht und getaggt |
| 796043f6 | Release-Notes-Quelle mit öffentlicher Beschreibung synchronisieren | geprüft und veröffentlicht |

## Zusätzliche Produktkorrekturen vom 23. August

### Generierungs-Aktionstext

Commit: 5500294e UI: Fix generation action hint wrapping

- Umbruchbreite wird aus der tatsächlich zugewiesenen inneren Labelbreite einschließlich Rahmen und Padding berechnet.
- Der deutsche Text wird bei 150 % und 175 % nicht mehr abgeschnitten.
- Action-Bar und Generate-Button bleiben fest sichtbar.
- Generierungs-, Status-, Fehler- und Callback-Logik blieben unverändert.
- Fokustest: 1 passed.
- tests/test_expandable_prompt.py: 73/73 passed, in drei überschneidungsfreien Gruppen 25 + 24 + 24.
- py_compile und git diff --check: erfolgreich.

### Installer- und Runtime-Output-Sicherheit

Commit: c6772c3d Installer: Exclude runtime output from releases

- Ursache der fälschlich mitgelieferten 19 Bilder war die rekursive Inno-Regel für dist\SnapdragonAIStudio\* einschließlich output\*.
- installer\snapdragon_ai_studio.iss schließt output\* nun strukturell aus.
- tools\build_installer.py verweigert einen Installer-Build, wenn der Frozen-Staging-Baum einen Runtime-output-Ordner enthält.
- Die Legacy-Migration bleibt unverändert, idempotent und überschreibt keine vorhandenen Dateien.
- Es wurden keine Bilder oder Sidecars gelöscht oder verändert.
- fokussierte Stagingtests: 2 passed.
- tests/test_migration.py: 6 passed.
- py_compile und git diff --check: erfolgreich.

### Plugin-Installationsbereich im Phoenix-Design

Commit: a1e36a5f UI: Align plugin installation with Phoenix design

- Readonly-Pfadfeld verwendet das bestehende Phoenix-Feldmuster und PHOENIX_THEME.
- „Ordner wählen“ und „Installieren“ verwenden PhoenixButton mit vorhandenen Icons und Theme-Tokens.
- Aktionen brechen bei schmaler Breite kontrolliert um.
- Die Installationsleiste bleibt fest außerhalb des Plugin-Scrollbereichs.
- Pfadauswahl, Installation, Controlleraufrufe, Suche, Filter, Aktivierung, Konfiguration und Entfernung blieben unverändert.
- fokussierte Plugin-Installationstests: 2 passed.
- tests/test_plugin_view.py: 3 passed.
- tests/test_plugin_release_readiness.py: 6 passed.

### Galerie-Ausgabeordner

Commit: e5f7b7a3 Gallery: Create output directory before opening

- PhoenixGalleryView._open_output_directory legt ausschließlich config.OUTPUT_DIR mit mkdir(parents=True, exist_ok=True) an, bevor Explorer gestartet wird.
- Explorer fällt bei fehlendem Ordner nicht mehr auf „Dokumente“ zurück.
- Vorhandene Dateien werden nicht geändert, gelöscht oder überschrieben.
- Bei einem Fehler wird Explorer nicht gestartet.
- Galerie-, Toolbar- und Hover-Callbacks blieben unverändert.
- fokussierte Ausgabeordnertests: 3 passed.
- tests/test_gallery.py: 12 passed.
- tests/test_gallery_hover_toggle.py: 6 passed.
- py_compile und git diff --check: erfolgreich.

## Finale Build-Artefakte

### Frozen-App

Pfad: C:\SnapdragonAI\dist\SnapdragonAIStudio\SnapdragonAIStudio.exe

- Größe: 77411162 Byte
- Zeitstempel: 2026-08-23 09:02:43
- SHA-256: D8CF83FFA8AED8D9241B29998EE6814E2F6F63118D2080919BA2E5D99B52E12C
- C:\SnapdragonAI\dist\SnapdragonAIStudio\output war nach dem Build nicht vorhanden.

### Finaler RC2B-Installer

Pfad: C:\SnapdragonAI\dist\installer\SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe

- Größe: 272026975 Byte
- Zeitstempel: 2026-08-23 09:09:52
- SHA-256: 59BE27EDF318990987E80ED3EFC7C896E8D651A456AE45BE2C8F15C02C01BDA3
- Frozen-Staging-output war vor und nach dem Installer-Build nicht vorhanden.
- Spätere Dokumentations-Commits ändern weder Frozen-App noch Installer; kein erneuter Build erforderlich.

## RC2CleanTest-Abnahme

### Testart und Reihenfolge

- Rechner: RC2CleanTest.
- Saubere Neuinstallation des korrigierten RC2B-Installers nach Deinstallation und Wegsicherung des fehlerhaften Teststands.
- Danach Überinstallation mit dem finalen RC2B-Installer.
- Die installierte EXE stimmte mit dem finalen Frozen-Build überein.

### Sicher erhaltene Teststände

- C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio Pre-RC2B-CleanTest-20260823-073615
- C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio RC2A Backup
- C:\Users\RC2CleanTest\AppData\Local\Programs\Snapdragon AI Studio Failed-Program-Payload-20260823

Diese Sicherungen nicht ohne Holgers ausdrücklichen Auftrag löschen.

### Bestätigte Ergebnisse

- Installer: Snapdragon AI Studio 2.0 RC2, Version 2.0.0-rc.2b.
- Installierte EXE-SHA-256: D8CF83FFA8AED8D9241B29998EE6814E2F6F63118D2080919BA2E5D99B52E12C.
- Erstsprache Deutsch korrekt übernommen.
- Kein Runtime-output im Programmordner.
- Nach sauberem Erststart keine eingebetteten Bilder; Galerie zeigte 0 Bilder.
- Hover-Vorschau standardmäßig Ein.
- Hover-Aus und Hover-Ein blieben jeweils nach Neustart gespeichert.
- Galerie öffnet exakt C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio\output und legt den Ordner bei Bedarf an.
- Plugin-Installationsbereich entspricht dem Phoenix-Design.
- 175 % Windows-Skalierung in Dark und Light bestanden.
- Schmales und maximiertes Fenster bestanden.
- Keine Startfehlermeldung.

Holgers finale Abnahme:

    RC2CleanTest 175 % Dark: ok
    RC2CleanTest 175 % Light: ok
    Schmales/maximiertes Fenster: ok
    Plugin-Phoenix-Design: ok

## Benutzerhandbücher und Release-Dokumentation

### Benutzerhandbücher

Commit: 5f61c235 Docs: Update user guides for RC2B

Geändert:

- docs/user-guide/USER_GUIDE_DE.md
- docs/user-guide/USER_GUIDE_EN.md
- docs/user-guide/USER_GUIDE_ES.md

Ergebnis:

- RC2B-Version, Installer, Phoenix Boost, Galerie-Hover, responsive UI, Bildvergleich, Panning, Synchronisierung, Metadatenvergleich und Ausgabeordner dokumentiert.
- DE, EN und ES inhaltlich und strukturell angeglichen.
- Suchprüfung: UNERLAUBTE_TREFFER=0.
- git diff --check erfolgreich.
- Handbücher sind nicht im Frozen-/Installer-Paket; kein erneuter Build erforderlich.

### Öffentliche RC2B-Dokumentation

Commit: 11325ce7 Docs: Prepare RC2B release documentation

Geändert beziehungsweise erstellt:

- README.md
- docs/releases/README.md
- docs/releases/RC2B_RELEASE_NOTES.md

Ergebnis:

- README-Status und Produktbeschreibung auf RC2B aktualisiert.
- Finale Installer- und Frozen-Hashes dokumentiert.
- VERBOTENE_TREFFER=0.
- FEHLENDE_PFLICHTANGABEN=0.
- TRAILING_WHITESPACE=0.
- DOKUMENTPRUEFUNG=OK.

## GitHub-Veröffentlichung RC2B

- main ohne Force-Push auf origin/main veröffentlicht.
- Annotierter Tag: v2.0.0-rc.2b.
- Tag-Commit: 11325ce712be24ffab5eeb677aa34c1e434ec633.
- GitHub Release: Snapdragon AI Studio 2.0 RC2B.
- URL: https://github.com/Kreuzhofen/snapdragon-ai-studio/releases/tag/v2.0.0-rc.2b
- Status: Pre-release True, Draft False.
- Asset: SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe.
- Asset-Digest: sha256:59be27edf318990987e80ed3efc7c896e8d651a456ae45be2c8f15c02c01bda3.

### Korrektur der öffentlichen Einleitung

- Die gelbe Markdown-Warnbox war optisch zu alarmierend und redundant.
- Die Beschreibung beginnt jetzt damit, dass RC2B der bisher stabilste, ausgereifteste und benutzerfreundlichste Release Candidate ist.
- Warnbox entfernt; normale Pre-release-Kennzeichnung bleibt aktiv.
- Nach einer fehlerhaften interaktiven PowerShell-Fortsetzung wurde die vollständige Beschreibung sofort aus der Sicherung wiederhergestellt.
- Ein anschließender UTF-8-Decodierungsfehler beschädigte zunächst die Abschnittsicons. Die Beschreibung wurde direkt aus der korrekten UTF-8-Quelldatei neu aufgebaut.
- Finale Prüfung: REMOTE_ICONS_OK=True, MOJIBAKE_TREFFER=0, WARNBOX_VORHANDEN=False, HERVORHEBUNG_VORHANDEN=True, PRERELEASE=True, DRAFT=False, UTF8_RELEASEPRUEFUNG=OK.
- Quelle und GitHub-Beschreibung: QUELLE_GITHUB_IDENTISCH=True, jeweils 6564 Zeichen.
- Commit: 796043f6 Docs: Align RC2B release notes with publication.

## Bekannte untracked Dateien am Tagesabschluss

    RC2A_RELEASE_NOTES_FINAL.md
    RC2_GITHUB_NOTES_CURRENT.md
    RC2_GITHUB_NOTES_CURRENT_UTF8.md
    RC2_GITHUB_NOTES_WITH_KNOWN_ISSUE.md
    RC2_RELEASE_NOTES.md
    RC2_RELEASE_NOTES_CLEAN.md
    README_BEFORE_RC2A_DOCS.md
    README_LOCKED_BACKUP.md
    assets/brand/ChatGPT Image 9. Aug. 2026, 21_42_14.png
    assets/brand/reddit_profilbild_512x512.jpg
    assets/brand/snapdragon-ai-studio-x-header-1500x500.png
    docs/CHATGPT_HANDOVER.md
    docs/SnapdragonAI_ChatGPT_Handover_2026-08-21.md
    presets/wolf.json
    sd35_venv/
    temp_traceback.txt
    temp_venv/

Diese Dateien wurden weder gestaged noch verändert oder gelöscht. docs/CHATGPT_HANDOVER.md wird ausschließlich über Holgers Handover-Aktualisierungs-CMD mit der hier bereitgestellten vollständigen Datei ersetzt.

## Tagesabschlussstatus 23. August 2026

- RC2B-Code, Tests, Benutzerhandbücher und Release-Dokumentation sind auf origin/main veröffentlicht.
- Lokaler und Remote-HEAD: 796043f6.
- Getrackter Arbeitsbaum sauber.
- Finaler Frozen-Build und finaler Installer erstellt und per SHA-256 dokumentiert.
- Saubere Installation des korrigierten Installers sowie finale Überinstallation auf RC2CleanTest bestanden.
- DPI-, Theme-, Fenster-, Galerie-, Ausgabeordner-, Hover- und Plugin-Prüfungen bestanden.
- Tag v2.0.0-rc.2b und GitHub Pre-release veröffentlicht.
- Öffentliche Release-Beschreibung, UTF-8-Icons, Asset und Digest final verifiziert.
- Englischer Reddit-Veröffentlichungstext vorbereitet; tatsächlicher Reddit-Post noch nicht bestätigt.
- Veröffentlichungen bei Qualcomm, Instagram, Facebook, Hugging Face und Microsoft stehen nach Reddit noch aus.
- Keine weiteren Builds, Installer, Commits, Tags oder Pushes erforderlich, solange keine Produkt- oder Quelldokumentänderung erfolgt.

## Nächster sicherer Schritt bei Wiederaufnahme

### 1. Git- und Release-Stand prüfen

    Set-Location -LiteralPath 'C:\SnapdragonAI'
    & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' fetch origin --prune
    & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' status --short --branch
    & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' rev-parse HEAD
    & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' rev-parse origin/main
    & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' log -3 --oneline --decorate
    & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\SnapdragonAI' rev-list -n 1 'v2.0.0-rc.2b'

Erwartet:

    HEAD = origin/main = 796043f6
    Tag v2.0.0-rc.2b = 11325ce7
    nur bekannte untracked Dateien

### 2. Veröffentlichungen fortsetzen

1. Prüfen, ob Holger den vorbereiteten englischen Reddit-Text bereits veröffentlicht hat.
2. Falls nicht: Reddit-Post final kontrollieren und durch Holger veröffentlichen.
3. Danach jeweils separat vorbereiten und freigeben: Qualcomm, Instagram, Facebook, Hugging Face, Microsoft.
4. Plattformtexte nicht blind duplizieren; Länge, Ton, Links, Bildformat und Zielgruppe anpassen.
5. Keine externen Veröffentlichungen ohne Holgers ausdrückliche Freigabe.

### 3. Feedbackphase

- GitHub-Issues, Installationsrückmeldungen und reale Snapdragon-Hardwareberichte auswerten.
- Neue Fehler zuerst reproduzieren und fokussiert eingrenzen.
- Keine Volltestsuite oder Refaktorierung ohne konkreten Anlass.
- Bekannte Sicherungen und untracked Dateien weiterhin unangetastet lassen.

## Handover-Übernahme

Diese vollständige aktualisierte Datei zum Download bereitstellen. Holger legt den Download in %USERPROFILE%\Downloads\CHATGPT_HANDOVER.md ab und startet anschließend:

C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd

Das CMD kopiert die Datei nach C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md, vergleicht die SHA-256-Prüfsummen und löscht den Download nur bei erfolgreicher Übernahme. Den Projektstand niemals mit einer verkürzten Handover-Datei überschreiben.

# Ergänzung: später Tagesabschluss 23. August 2026 – RC2B-Preview-Hotfix und RealESRGAN-Zwischenstand

Diese Ergänzung führt den bisherigen Tagesabschluss vollständig fort. Alle älteren Abschnitte bleiben als Chronik erhalten. Für Git-Stand, Release-Artefakte, offene Arbeiten und den nächsten Einstieg hat diese Ergänzung Vorrang.

## Kritischer RC2B-Hotfix: Ergebnisvorschau der KI-Bildgenerierung

### Gemeldeter Fehler

- In der veröffentlichten RC2B wurde ein generiertes Bild korrekt gespeichert, im rechten Generierungs-Inspector jedoch zunächst nur als schmaler horizontaler Streifen dargestellt.
- Nach Scrollen war das Bild zwar vollständig erreichbar, lag aber zu weit unten.
- Die Generierungsinformationen wurden bei vorhandener Breite unnötig einspaltig angeordnet.
- Beim schmalen Reflow konnten veraltete Grid-Zeilen Mindesthöhe beziehungsweise Gewicht behalten. Dadurch entstanden große vertikale Lücken zwischen Größe, Schritte, CFG, Seed, Sampler und Scheduler.

### Isolierter Hotfix-Arbeitsbereich

Für den Hotfix wurde der Hauptarbeitsbereich mit der bereits begonnenen RealESRGAN-Arbeit nicht verändert. Stattdessen wurde vorübergehend verwendet:

    C:\SnapdragonAI_RC2B_Preview_Hotfix

Branch:

    hotfix/rc2b-generation-preview

Der Worktree basierte auf `796043f6` und wurde nach erfolgreicher Integration ordnungsgemäß mit `git worktree remove` entfernt. Der Ordner existiert nicht mehr. Der lokale Hotfix-Branch bleibt erhalten.

### Technische Lösung

Commit:

    c86356da UI: Fix generation preview inspector layout

Geänderte Dateien:

    widgets/phoenix/views/prompt_view.py
    tests/test_expandable_prompt.py

Umgesetzt:

- Generische Mindesthöhe der Ergebnisvorschau: 180 Pixel.
- Mindesthöhe liegt auf der tatsächlich verwendeten Preview-Zeile und dem darstellenden Preview-Container.
- Die Tk-`PhotoImage`-Referenz wird zusätzlich am Bildlabel gehalten.
- Vor jedem Inspector-Reflow werden früher verwendete Zeilen auf `weight=0` und `minsize=0` zurückgesetzt.
- Nur die aktuell platzierte Preview-Zeile erhält die Preview-Mindesthöhe.
- Der Informationsblock misst angeforderte Widgetbreiten, übersetzte Texte, Werte und Grid-Abstände.
- Die sechs Generierungsinformationen bleiben zweispaltig, solange alle drei Paare tatsächlich passen.
- Erst bei echtem Platzmangel wechselt der gesamte Block lückenlos in eine Spalte.
- Nach einem erfolgreich geladenen Ergebnis scrollt ausschließlich der rechte Inspector per `after_idle` zum vorhandenen Preview-Header.
- Fehlende oder ungültige Ergebnisdateien lösen kein automatisches Scrollen aus.
- Die Action-Bar bleibt fest außerhalb des scrollbaren Ergebnisbereichs.
- Generierung, Ergebnisdatei, Sidecar, Status, Fortschritt, Galerie, Vergleich, Speichern und Explorer-Handler sowie deren Callback-Identitäten blieben unverändert.
- Keine Farben oder Theme-Tokens wurden geändert; das bestehende Phoenix-Design bleibt erhalten.

### Tests und manuelle Abnahme

- Fokustests `generation_information or result_preview`: `3 passed, 73 deselected`.
- Die vollständige Testdatei wurde mehrfach gestartet; ein fachfremder Ollama-Mockpfadfehler trat in einer Teilgruppe auf und wurde nicht durch den Hotfix verändert.
- `py_compile`: erfolgreich.
- `git diff --check`: erfolgreich; nur bestehende LF-/CRLF-Hinweise.
- Rechner: Entwicklungs-PC Holger.
- Testart: direkter Frozen-App-Test.
- Holger bestätigte nach dem finalen Build die vollständige Bildvorschau und das korrigierte Informationslayout mit `ok`.
- Die Layoutkorrektur ist für ausreichende Breite zweispaltig und für echte Engstellen einspaltig; damit ist sie nicht an einen festen 150-/175-%-Schwellwert gebunden.

## Aktualisierter RC2B-Build und sicherer Asset-Austausch

### Hotfix-Frozen-Build

Final bestätigter SHA-256 des Hotfix-Frozen-Builds:

    7865734A1CB5998DF32F8056ECD7DA9F36ECF7A6DC016C7A7902181260CA42E5

Der temporäre Worktree einschließlich seines lokalen Frozen-Stagings wurde später entfernt. Maßgebliches dauerhaft vorhandenes Artefakt ist der Installer im Hauptprojekt und auf GitHub.

### Finaler ersetzter RC2B-Installer

Lokaler Pfad:

    C:\SnapdragonAI\dist\installer\SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe

Finale Werte:

- Größe: `269157425` Byte.
- SHA-256: `1E964D56C2FDB459C24526653A7D1BC022E33AF1BB2F2EDB52C49146D94724C4`.
- Die lokale Kopie wurde nach dem Kopieren mit `Get-FileHash` exakt verifiziert.

Der Installer wurde im bestehenden GitHub-Release unter demselben Dateinamen sicher mit `--clobber` ersetzt. Es wurde keine zusätzliche Hotfix-, Fehler- oder Ankündigungsinformation veröffentlicht.

GitHub-Verifikation:

- URL: `https://github.com/Kreuzhofen/snapdragon-ai-studio/releases/tag/v2.0.0-rc.2b`
- Draft: `False`.
- Pre-release: `True`.
- Asset: `SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe`.
- Assetgröße: `269157425` Byte.
- Asset-Digest: `sha256:1e964d56c2fdb459c24526653a7d1bc022e33af1bb2f2edb52c49146d94724c4`.

### Git-Integration

Zusätzlicher Commit:

    ccf1c8d7 Docs: Update RC2B installer checksum

Aktueller veröffentlichter Stand:

- `main`: `ccf1c8d7`.
- `origin/main`: `ccf1c8d7`.
- `origin/HEAD`: `ccf1c8d7`.
- Der Hotfix-Commit `c86356da` ist Bestandteil von `main` und `origin/main`.
- Der annotierte Tag `v2.0.0-rc.2b` wurde nicht verschoben.
- Kein Force-Push.
- Kein neuer öffentlicher Sicherungsbranch.

### Noch zu prüfende Release-Beschreibung

Beim technischen Austausch des Assets wurde die GitHub-Releasebeschreibung erneut über PowerShell eingelesen. Danach meldete Holger, dass die Abschnittsicons wieder verschwunden beziehungsweise als fehlerhafte Zeichen dargestellt wurden.

Die empfohlene Reparatur lädt die committed UTF-8-Quelldatei direkt hoch, ohne den Text durch PowerShell zu dekodieren:

    & $ghExe release edit 'v2.0.0-rc.2b' `
        --repo 'Kreuzhofen/snapdragon-ai-studio' `
        --notes-file 'C:\SnapdragonAI\docs\releases\RC2B_RELEASE_NOTES.md'

Holger hat die Ausführung und anschließende Browserprüfung dieses letzten Reparaturbefehls noch nicht bestätigt. Bei Wiederaufnahme zuerst prüfen, ob die Icons auf der GitHub-Release-Seite korrekt angezeigt werden. Dabei Installer, Asset, Tag und Release-Status nicht verändern.

## Pausierter RealESRGAN-/NPU-Arbeitsstand

Die RealESRGAN-Arbeit wurde wegen des RC2B-Hotfixes bewusst unterbrochen und im Hauptarbeitsbereich vollständig erhalten.

### Bestehende Funktion klarstellen

- Snapdragon AI Studio kann bereits mit RealESRGAN ein Bild von `512 × 512` auf `1024 × 1024` hochskalieren.
- Diese vorhandene Benutzerfunktion darf nicht als noch fehlende Grundfunktion dargestellt oder neu implementiert werden.
- `512 → 1024` entspricht einem 2×-Ausgabeprofil.
- Ein echtes 4×-Ergebnis aus `512 × 512` wäre `2048 × 2048`.
- „Originalerhalt“ bedeutet davon getrennt, dass die Quelldatei nicht überschrieben und das Ergebnis als neue Datei gespeichert wird.
- Vor einer Erweiterung auf 2048 muss zunächst festgestellt werden, ob der aktuelle QNN-Pfad intern echtes x4 berechnet und anschließend auf 1024 begrenzt oder gezielt ein 2×-Ergebnis erzeugt.

### Vorhandene, noch nicht abgeschlossene Änderungen in `C:\SnapdragonAI`

Geänderte getrackte Dateien:

    engine/backends/backend_discovery_service.py
    engine/backends/discovery_result.py
    engine/backends/qnn_backend.py
    modules/qnn.py

Neue untracked Arbeitsdateien:

    engine/realesrgan_qnn_runtime.py
    tests/test_realesrgan_qnn_runtime.py

Diese Dateien gehören zur begonnenen RealESRGAN-Runtime-Härtung. Sie wurden durch Hotfix, Builds, Asset-Austausch und Worktree-Entfernung nicht verändert, gestaged oder gelöscht.

### Ziel der begonnenen Härtung

- Nutzerpfad bevorzugen: `%LOCALAPPDATA%\Snapdragon AI Studio\models\real_esrgan_x4plus.bin`.
- Quellbetrieb darf zusätzlich `C:\SnapdragonAI\models\real_esrgan_x4plus.bin` verwenden.
- Frozen-Betrieb darf nicht auf den Repository-Pfad zurückfallen.
- `qnn-net-run.exe` und `QnnHtp.dll` über `BackendDiscoveryService` auflösen.
- Strukturierte Fehlercodes bei fehlendem Modell, Runner oder HTP-Backend.
- Ausschließlich QNN-/HTP-Ausführung, kein ONNX- oder CPU-Fallback.
- Vorhandene Kachelverarbeitung, Seitenverhältnis, eindeutiger Ausgabename, Originalerhalt sowie Status-/Fortschrittscallbacks unverändert lassen.

Bereits gemeldete Tests:

- `tests/test_realesrgan_qnn_runtime.py`: `7 passed`.
- `tests/test_backend_contract.py`: `5 passed, 6 subtests passed`.
- `py_compile` und `git diff --check`: erfolgreich.

Ein echter NPU-Smoke-Test und eine abschließende Lizenz-/Paketierungsentscheidung stehen noch aus. QNN-Kontext und QAIRT-Runtime dürfen bis zur geklärten Weitergabe nicht ungeprüft in Frozen-Staging oder Installer aufgenommen werden.

### Modell- und QAIRT-Nachweis

Getracktes Modell:

    C:\SnapdragonAI\models\real_esrgan_x4plus.bin

- Größe: `38744064` Byte.
- SHA-256: `AB62398BF9CA61209E4DAB5EB5776F032760B777A759663CD67C14CFFF12E525`.- Das Laufzeitmodell unter `%LOCALAPPDATA%\Snapdragon AI Studio\models\real_esrgan_x4plus.bin` war nicht vorhanden.
- `qnn-net-run.exe` und `QnnHtp.dll` waren unter QAIRT/AIStack 2.47 vorhanden.

Eine versehentlich erzeugte Textdatei mit dem Namen `C:\SnapdragonAI\real_esrgan_x4plus.bin'` enthielt ausschließlich Pager-Hilfetext. Sie wurde nur nach exakter Prüfung von Größe `17182` Byte und SHA-256 `779381A9D9DA4EAE2F1F18ACD6F4EA8C7C29D52B4BEC2CA7B73FC9EF8BCC15E8` gelöscht. Das korrekte Modell blieb unverändert.

## Produktplanung NPU-Bildbearbeitung und größere Bilder

Holgers Ziel bleibt eine lokal auf der Snapdragon-NPU ausgeführte, ausgereifte KI-Bildbearbeitung, beispielsweise:

- Personen oder Gegenstände hinzufügen beziehungsweise entfernen.
- Aussehen, Kleidung, Gesichtsausdruck und Hintergrund per Text ändern.
- Personeninteraktionen und komplexere Bildkompositionen verändern.
- Qualität und Bildgrößen über den bisherigen 512er-Kompatibilitätsmodus hinaus verbessern.

Technischer Stand:

- SD3.5 Medium erzeugt bereits nativ `1024 × 1024`, aber mit statischem Profil.
- SD1.5, SD2.1 und ControlNet-Canny verwenden derzeit feste 512er-QNN-Kontexte.
- Das vorhandene SD3.5-QAI-Paket enthält Textencoder, Transformer, VAE-Decoder und `time_text_embed.pt`, aber keinen VAE-Encoder.
- Für echtes img2img/Inpainting fehlen insbesondere ein qualifizierter NPU-VAE-Encoder, Masked-Denoising-/Inpainting-Kontexte und später Identity-, Segmentierungs-, Pose- beziehungsweise Tiefenkomponenten.
- Deshalb kein sofortiges Produktversprechen für beliebige lokale KI-Bildbearbeitung abgeben.
- Empfohlener Einstieg ist ein eng begrenzter 1024er-NPU-Inpainting-Prototyp, sobald die benötigten Qualcomm-/QAI-Komponenten und Lizenzbedingungen geklärt sind.

## Offene Veröffentlichungen

- Reddit wird ausschließlich auf Englisch veröffentlicht; eine tatsächliche Veröffentlichung wurde im bisherigen Verlauf noch nicht eindeutig bestätigt.
- Danach stehen weiterhin Qualcomm, Instagram, Facebook, Hugging Face und Microsoft aus.
- Die Plattformtexte jeweils separat auf Zielgruppe, Länge, Bildformat und Linkführung abstimmen.
- Holger veröffentlicht beziehungsweise gibt jede externe Veröffentlichung einzeln frei.

## Tagesabschlussstatus nach Hotfix

- `main` und `origin/main` stehen auf `ccf1c8d7`.
- Der RC2B-Preview-Hotfix ist veröffentlicht.
- Der finale Installer ist lokal und als GitHub-Asset vorhanden; Hash und Asset-Digest stimmen überein.
- Temporärer Hotfix-Worktree wurde sicher entfernt.
- Lokaler Hotfix-Branch bleibt erhalten.
- Keine RealESRGAN-Datei wurde durch den Hotfix verändert oder verloren.
- Bekannte untracked Dateien bleiben erhalten.
- Die GitHub-Releaseicons müssen bei Wiederaufnahme noch visuell beziehungsweise UTF-8-sicher verifiziert werden.
- RealESRGAN-Runtime-Härtung bleibt uncommitted und pausiert.
- Kein weiterer Build oder Installer ist erforderlich, solange keine neue Produktänderung erfolgt.

## Nächster sicherer Schritt morgen

### 1. Releasebeschreibung abschließen – PowerShell/Holger

1. GitHub-Release im Browser öffnen und Icons prüfen.
2. Falls weiterhin beschädigt, die committed UTF-8-Quelldatei direkt mit `gh release edit --notes-file` hochladen.
3. Danach nur Icons, Pre-release-Status und unverändertes Asset-Digest prüfen.
4. Keine weitere PowerShell-Texttransformation der Releasebeschreibung verwenden.

### 2. RealESRGAN-Arbeit wieder aufnehmen – PowerShell, Codex, Holger

1. PowerShell: Git-Status und exakten Diff der sechs RealESRGAN-Dateien prüfen.
2. Vor jeder weiteren Änderung klären, dass die vorhandene `512 → 1024`-Funktion erhalten bleibt.
3. Codex: ausschließlich die begonnene Runtime-Härtung und deren fokussierte Tests abschließen; keine Neuimplementierung des vorhandenen Upscalers.
4. PowerShell/Holger: echten QNN-/NPU-Smoke-Test mit einem vorhandenen Bild ausführen.
5. Holger: Ergebnisqualität, Ausgabemaße, Originalerhalt und NPU-Ausführung manuell bestätigen.
6. Erst danach entscheiden, ob ein optionales echtes 4×-/2048-Profil ergänzt wird.
7. Vor Paketierung oder Veröffentlichung des QNN-Kontexts Lizenz- und Redistributionslage verbindlich klären.

### 3. Veröffentlichungen fortsetzen – ChatGPT/Holger

Nach technischer Stabilisierung beziehungsweise separat nach Holgers Priorität: Qualcomm, Hugging Face und Microsoft, anschließend Instagram und Facebook. Keine automatische Veröffentlichung.

## Handover-Übernahme nach diesem Tagesabschluss

Diese vollständige, nur ergänzte Datei zum Download bereitstellen. Holger speichert sie als `%USERPROFILE%\Downloads\CHATGPT_HANDOVER.md` und startet anschließend:

    C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd

Das CMD darf `C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md` erst nach erfolgreicher SHA-256-Prüfung überschreiben. Die ältere Chronik darf nicht gekürzt oder ersetzt werden.

# Ergänzung: Tagesabschluss 24. August 2026 – RealESRGAN-Härtung, RC2B-Portale und Start des 4×-Sprints

Diese Ergänzung führt die vollständige Chronik fort. Für den aktuellen Git-Stand, die RealESRGAN-Arbeit, Build-Artefakte, Veröffentlichungsportale und den nächsten Einstieg hat dieser Abschnitt Vorrang.

## Aktuelle Arbeitsregeln und Holgers gewünschter Ablauf

- Holger erhält alle Antworten auf Deutsch.
- Öffentliche englische Texte werden zuerst in der veröffentlichungsfertigen englischen Fassung und unmittelbar darunter in einer deutschen Kontrollfassung bereitgestellt.
- Plattformtexte werden an Zielgruppe, Länge, Bildformat und Ton des jeweiligen Portals angepasst und nicht blind dupliziert.
- ChatGPT gibt die Arbeitsreihenfolge und den nächsten sicheren Schritt selbst vor. Bei routinemäßigen Folgeschritten wie Prüfungen, Build oder Installer-Build nicht immer erneut fragen, sondern den passenden PowerShell-Befehl direkt liefern, soweit keine neue Freigabegrenze überschritten wird.
- PowerShell-Befehle immer vollständig und mit absoluten Windows-Pfaden ausgeben.
- PowerShell bevorzugen, wenn eine Prüfung, ein Build, ein Installer-Build oder ein klar begrenzter Git-Schritt ohne Codex möglich ist.
- Codex und Antigravity tokensparend einsetzen. Codex nur für notwendige Codeanalyse und Implementierung; Antigravity nur bei erkennbarem Zusatznutzen.
- Keine neue Implementierung, kein Build, Commit, Push, Tag oder Release-Austausch ohne die jeweils erforderliche Freigabe beziehungsweise den eindeutig bereits freigegebenen Arbeitsabschnitt.
- Niemals `git add .` verwenden.
- Bekannte untracked Dateien nicht löschen, verändern oder versehentlich stagen.
- Vor jedem Commit nur die exakt freigegebenen Dateien stagen, staged Dateiliste und `git diff --cached --check` prüfen.
- Vor jedem Push Commitfolge, Diff und Tests bestätigen.
- UI-Erweiterungen müssen das bestehende Snapdragon-AI-Studio-/Phoenix-Design, vorhandene Theme-Tokens, Light/Dark und DPI-Responsivität einhalten.
- Bei jedem Test Maschine und Modus nennen: Entwicklungs-PC Holger oder RC2CleanTest; direkter Python-Test, Frozen-App-Test, Überinstallation oder saubere Neuinstallation.
- Bei Feierabend oder Arbeitspause die vollständige zentrale `CHATGPT_HANDOVER.md` aktualisieren und zum Download bereitstellen.

## Verbindlicher Git-Stand am 24. August 2026

Repository:

    C:\SnapdragonAI

Branch:

    main

Aktueller veröffentlichter Stand:

- Lokaler HEAD: `4d271438 RealESRGAN: Fix frozen packaging and spaced paths`.
- `origin/main`: `4d271438`.
- `main` und `origin/main` stimmen überein.
- Push am 24. August erfolgreich: `ccf1c8d7..4d271438 main -> main`.
- Kein Force-Push.
- Keine versionierten oder gestagten Arbeitsbaumänderungen nach dem Push bestätigt.
- Nur die bekannten untracked Dateien sind vorhanden.

Neue Commitfolge:

| Commit | Inhalt | Status |
| --- | --- | --- |
| `3cf46772` | `RealESRGAN: Harden QNN runtime discovery` | getestet, echter NPU-Smoke-Test, auf `origin/main` |
| `4d271438` | `RealESRGAN: Fix frozen packaging and spaced paths` | getestet, Frozen-Build, Clean-Test, auf `origin/main` |

Gesamtdiff der beiden Commits gegenüber dem vorherigen `origin/main`:

```text
engine/backends/backend_discovery_service.py |  45 +++
engine/backends/discovery_result.py          |   2 +
engine/backends/qnn_backend.py               |  49 +---
engine/realesrgan_qnn_runtime.py             | 138 +++++++++
modules/qnn.py                               |  22 +-
modules/realesrgan_core.py                   |   9 +-
tests/test_realesrgan_qnn_runtime.py         | 406 +++++++++++++++++++++++++++
tests/test_release_packaging.py              |  33 +++
tools/build_app.py                           |   7 +
9 files changed, 653 insertions(+), 58 deletions(-)
```

`git diff --check origin/main..HEAD` war vor dem Push erfolgreich und ohne Ausgabe.

## Bekannte untracked Dateien am Tagesabschluss

```text
RC2A_RELEASE_NOTES_FINAL.md
RC2_GITHUB_NOTES_CURRENT.md
RC2_GITHUB_NOTES_CURRENT_UTF8.md
RC2_GITHUB_NOTES_WITH_KNOWN_ISSUE.md
RC2_RELEASE_NOTES.md
RC2_RELEASE_NOTES_CLEAN.md
README_BEFORE_RC2A_DOCS.md
README_LOCKED_BACKUP.md
assets/brand/ChatGPT Image 9. Aug. 2026, 21_42_14.png
assets/brand/reddit_profilbild_512x512.jpg
assets/brand/snapdragon-ai-studio-x-header-1500x500.png
docs/CHATGPT_HANDOVER.md
docs/SnapdragonAI_ChatGPT_Handover_2026-08-21.md
presets/wolf.json
sd35_venv/
temp_traceback.txt
temp_venv/
```

Diese Dateien wurden durch die RealESRGAN-Commits nicht gestaged, verändert oder gelöscht. `docs/CHATGPT_HANDOVER.md` wird ausschließlich über Holgers Handover-Aktualisierungs-CMD mit der hier bereitgestellten vollständigen Datei ersetzt.

## RealESRGAN: Ziel und unveränderte Bestandsfunktion

Die vorhandene Benutzerfunktion war bereits vor diesem Sprint funktionsfähig:

- Ein generiertes Bild mit `512 × 512` kann über RealESRGAN auf `1024 × 1024` ausgegeben werden.
- Die bestehende UI-Funktion heißt sinngemäß „Nach Generierung mit RealESRGAN 2× hochskalieren“.
- Intern erzeugt das RealESRGAN-QNN-Modell ein 4×-Zwischenergebnis; der bestehende 2×-Benutzerpfad verkleinert dieses anschließend kontrolliert auf die doppelte Originalgröße.
- Das Originalbild bleibt erhalten; das Upscaling wird als separate Datei gespeichert.
- Diese bestehende 2×-Funktion darf im kommenden 4×-Sprint weder entfernt noch semantisch verändert werden.

Das nächste Produktziel ist davon getrennt:

- zusätzliches echtes 4×-Ausgabeprofil,
- `512 × 512 -> 2048 × 2048`,
- weiterhin ausschließlich RealESRGAN/QNN auf der Snapdragon-NPU,
- Originalerhalt und separater eindeutiger Ausgabename,
- klare 2×-/4×-Auswahl im bestehenden Phoenix-/Snapdragon-Design.

## RealESRGAN-Runtime-Härtung

### Zentrale Runtime-Auflösung

Neue zentrale Datei:

    C:\SnapdragonAI\engine\realesrgan_qnn_runtime.py

Vertrag:

- Non-Frozen verwendet ausschließlich `C:\SnapdragonAI\models\real_esrgan_x4plus.bin`; Quelle `development`.
- Frozen prüft zuerst `%LOCALAPPDATA%\Snapdragon AI Studio\models\real_esrgan_x4plus.bin`; Quelle `user`.
- Wenn dort kein Benutzermodell liegt, verwendet Frozen das mitgelieferte Modell im Ordner der EXE unter `models\real_esrgan_x4plus.bin`; Quelle `bundled`.
- Non-Frozen fällt nicht auf Benutzer- oder Frozen-Pfade zurück.
- Frozen fällt nicht auf den Repository-Pfad zurück.
- Fehlendes Modell löst weiterhin `REALESRGAN_MODEL_MISSING` mit ausschließlich den modusspezifisch geprüften Pfaden aus.
- `qnn-net-run.exe` und `QnnHtp.dll` werden zentral über die Backend-Discovery aufgelöst.
- Kein ONNX-, CPU- oder Stub-Fallback wurde eingeführt; die QNN-only-Policy bleibt bestehen.

### QNN-HTP-Skeleton-Discovery

- Discovery sucht versionsoffen rekursiv nach `libQnnHtpV<Version>Skel.so`.
- Ein Skeleton-Verzeichnis wird nur übernommen, wenn dort der passende, case-insensitiv geprüfte `libqnnhtpv<Version>.cat` liegt.
- Ergebnisse werden dedupliziert und stabil sortiert als `qnn_htp_skeleton_dirs` geliefert.
- Ohne mindestens ein vollständiges Skeleton-/Katalog-Paar wird `RealESRGANRuntimeUnavailable(code="QNN_HTP_SKEL_MISSING")` ausgelöst.
- `process_environment()` erzeugt nur eine Kopie der Prozessumgebung:
  - `PATH`: HTP-DLL- und Runner-Verzeichnis vor dem bestehenden Wert,
  - `ADSP_LIBRARY_PATH`: Skeleton-Verzeichnisse vor dem bestehenden Wert.
- Es erfolgen keine globalen Umgebungsänderungen.
- Beide QNN-Aufrufstellen verwenden die zentrale Runtime-Umgebung.

### Pfade mit Leerzeichen

Ein realer Fehler wurde für absolute Input-List-Pfade mit Leerzeichen bestätigt:

- Ein absoluter Eintrag unter `%LOCALAPPDATA%\Snapdragon AI Studio\...` führte bei `qnn-net-run` zu Exitcode `17`.
- Dasselbe RAW-Input ohne Leerzeichen funktionierte mit Exitcode `0`.
- Ein relativer Eintrag `image.raw` funktionierte auch dann mit Exitcode `0`, wenn der Arbeitsordner Leerzeichen enthielt.

Finale Lösung:

- Beide Input-List-Erzeuger schreiben ausschließlich `image.raw`, nie einen absoluten Pfad.
- Beide QNN-Aufrufstellen starten `qnn-net-run` mit `cwd=input_list.parent`.
- Eine Regression mit einem temporären Pfad mit Leerzeichen prüft Input-List und `cwd` für Backend- und Kachelpfad.
- Runtime-Auflösung, Modellpriorität, Skeleton-Vertrag, QNN-only-Policy, Skalierung und Kachelung blieben unverändert.

### Bereinigter Funktionsvertrag

- `run_qnn_context` nimmt keinen unbenutzten `model_path` mehr an.
- Der einzige Aufruf übergibt Eingabeliste, Ausgabeordner und Log-Level.
- Der doppelte `REALESRGAN_MODEL`-Vorabcheck samt Import wurde entfernt.
- Allein der zentrale Runtime-Resolver ist für den Modellvertrag zuständig.

## RealESRGAN-Tests

Rechner:

    Entwicklungs-PC Holger

Modus:

    direkte Python-/Pytest-Prüfung, keine Installation

Final bestätigtes betroffenes Testpaket:

```text
.........................                                          [100%]
25 passed, 6 subtests passed in 0.54s
```

Abgedeckt sind insbesondere:

- Non-Frozen- und Frozen-Modellpriorität einschließlich ausgeschlossener Fallbacks,
- strukturierte Modell-, Runner-, HTP-DLL- und Skeleton-Fehler,
- versionsoffene Skeleton-/Katalog-Discovery,
- isolierte Prozessumgebung,
- QNNBackend- und `modules.qnn`-Aufrufverträge,
- relative Input-Lists und korrektes `cwd` bei Pfaden mit Leerzeichen,
- Kachelung, Skalierung, Originalerhalt und Callback-Verträge,
- Plugin- und Controller-Verbindung zu `image.upscale`,
- Frozen-Paketierung genau einer RealESRGAN-Modellbinärdatei.

Zusätzlich:

- `py_compile`: erfolgreich.
- `git diff --check`: erfolgreich; nur erwartete LF-/CRLF-Hinweise im damaligen Arbeitsbaum.

## Echte QNN-/NPU-Smoke-Tests

### 128er-Eingabe

Rechner:

    Entwicklungs-PC Holger

Modus:

    direkter Python-Smoke-Test mit realem qnn-net-run und Snapdragon-NPU

Ergebnis:

- Eingabe: `128 × 128`.
- Ausgabe: `512 × 512`.
- Eine Kachel.
- `Creating context from binary file`, `Executing Graphs` und `Finished Executing Graphs` bestätigt.
- Nach Bereitstellung der korrekten Skeleton-Umgebung keine `DspTransport`-Fehler mehr.
- Originaldatei blieb unverändert.

### 512er-Eingabe / echtes 4×

Rechner:

    Entwicklungs-PC Holger

Modus:

    direkter Python-Smoke-Test mit realem qnn-net-run und Snapdragon-NPU

Ergebnis:

- Eingabe: `512 × 512`.
- Ausgabe: `2048 × 2048`.
- Kachelung: `4 × 4 = 16`.
- Alle 16 QNN-Aufrufe beendeten `Executing Graphs` erfolgreich.
- Ausgabedatei: `C:\SnapdragonAI\output\realesrgan_runtime_smoke_512_20260824_165319_tile_upscaled_x4.png`.
- `ORIGINAL_UNCHANGED=True`.
- Holger bestätigte das sichtbare 2048×2048-Gitterbild.

Damit ist technisch nachgewiesen, dass der bestehende QNN-Kern echtes 4×-Upscaling über die Snapdragon-NPU ausführen kann. Der kommende Sprint betrifft die sichere zusätzliche Produkt-/UI-Anbindung, nicht die Entwicklung eines neuen Upscaling-Modells.

## Frozen-Paketierung des RealESRGAN-Modells

Geänderte Buildlogik:

- `tools\build_app.py` prüft vorab genau `models\real_esrgan_x4plus.bin`.
- Fehlt diese einzelne Produktdatei, erfolgt ein eindeutiger `FileNotFoundError`.
- PyInstaller erhält exakt eine zusätzliche `--add-data`-Regel für diese Binärdatei nach `models`.
- Der gesamte Modellordner und andere Modelle werden nicht paketiert.
- Die Frozen-Runtime verwendet zuerst ein Benutzermodell und danach das mitgelieferte Modell neben der EXE.

Verwendete isolierte Build-Umgebung:

    C:\Users\holge\AppData\Local\SnapdragonAIStudioBuild\pyinstaller-6.21

- Python ARM64, 64 Bit.
- PyInstaller `6.21.0` gemäß `requirements-build.txt`.
- `onnxruntime_qnn` war verfügbar.

Finaler lokaler Frozen-Build nach dem Pfadfix:

```text
C:\SnapdragonAI\dist\SnapdragonAIStudio\SnapdragonAIStudio.exe
Größe: 77427333 Byte
Zeitstempel: 24.08.2026 18:13:28
```

Mitgeliefertes Modell:

```text
C:\SnapdragonAI\dist\SnapdragonAIStudio\models\real_esrgan_x4plus.bin
Größe: 38744064 Byte
SHA-256: AB62398BF9CA61209E4DAB5EB5776F032760B777A759663CD67C14CFFF12E525
```

Der Modellhash stimmt exakt mit dem Quellmodell überein.

## Neuer lokaler RC2B-Installer-Kandidat und Clean-Test

Nach den RealESRGAN-Korrekturen wurde lokal ein neuer Installer gebaut:

    C:\SnapdragonAI\dist\installer\SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe

SHA-256:

    875A7C0F54F557353BE01C7569AE7443724213C67D4BF279969052FE13B5CC15

Dieser Installer wurde nach `C:\Users\Public\Downloads` kopiert und auf RC2CleanTest geprüft.

Rechner:

    RC2CleanTest

Modus:

    saubere Neuinstallation

Bestätigt:

- Installer-Hash vor Installation korrekt.
- Vorhandene Installation und Benutzerdaten wurden in eindeutig benannte Sicherungsordner verschoben, nicht gelöscht.
- Installation erfolgreich.
- Installierte EXE vorhanden.
- Mitgeliefertes Modell vorhanden.
- Installierter Modellhash entspricht `AB62398...E525`.
- `SAUBERE_NEUINSTALLATION_ERFOLGREICH=True`.
- Die vorhandene 2×-Option der KI-Bildgenerierung erzeugte auf dem installierten Stand erfolgreich ein separates `1024 × 1024`-Bild aus einem `512 × 512`-Original.
- Original und 2×-Ausgabe wurden von Holger visuell kontrolliert.

Wichtige Abgrenzung:

- Dieser neu gebaute Installer mit Hash `875A...C15` ist ein lokaler, sauber getesteter Kandidat.
- Er wurde nicht als neues GitHub-Asset hochgeladen und hat den veröffentlichten RC2B-Installer nicht ersetzt.
- Der weiterhin öffentlich vorhandene RC2B-Installer ist das zuvor veröffentlichte Asset mit SHA-256 `1E964D56C2FDB459C24526653A7D1BC022E33AF1BB2F2EDB52C49146D94724C4`.
- Die beiden neuen RealESRGAN-Commits sind zwar auf `origin/main`, aber noch nicht Bestandteil eines erneut veröffentlichten Installers.
- Kein Release-Tag wurde verschoben und kein neues Release erstellt.

## Öffentliche Kommunikation und Portale

### Verbindliche Textregel

- Veröffentlichungsfertiger Text auf Englisch.
- Unmittelbar darunter deutsche Kontrollfassung für Holger.
- Offizielle Ankündigungen erhalten die vollständige Signatur:

**Holger Kreuzhofen**  
Founder & Lead Developer  
Snapdragon AI Studio – Phoenix Engine

- Kritische oder provokative Kommentare sachlich beantworten, wenn eine Antwort sinnvoll ist; keine persönliche Beleidigung. Inhaltsleere Kritik kann als solche benannt werden. Reine Trollkommentare dürfen ignoriert werden.
- Technische Fehlerberichte konkret würdigen und nach reproduzierbaren Angaben fragen.

### Reddit

- RC2B wurde auf Reddit veröffentlicht.
- Relevante Nutzerfragen wurden beantwortet.
- Ein Asus-Zenbook-A16-Nutzer besitzt ein Snapdragon-Modell; die Antwort bittet um reale Rückmeldung zur Leistung und genaue Fehlerangaben.
- Ein technischer Bericht von `ResponsibleRain9625` bestätigt schnelle und stabile Stable-Diffusion-2.1-Ausführung auf `X2E-88-100`.
- Beim SD3.5-Installationsschritt „Final target model validation and activation“ trat `ImportError: DLL load failed while importing _ssl` auf.
- Aktuelle Einschätzung: eher Python-/OpenSSL-Runtime- beziehungsweise DLL-Konflikt als Snapdragon- oder Modelldefekt; noch nicht endgültig bewiesen.
- Nutzer soll keine DLLs aus dem Internet manuell kopieren.
- Angefordert wurden Windows-Version und Buildnummer, installierte Snapdragon-AI-Studio-Version, saubere Neuinstallation oder Upgrade sowie ein Screenshot der vollständigen in Snapdragon AI Studio angezeigten Fehlermeldung einschließlich `Technical detail`.
- Ein reproduzierbarer GitHub-Issue oder vollständiger Nutzerbericht steht noch aus.

### Qualcomm Developers Discord

- RC2B-Beitrag im Kanal `#self-promotion` wurde von Holger veröffentlicht.
- Der Text wurde an das Entwicklerpublikum angepasst und nicht blind vom Reddit-Text übernommen.

### Microsoft Tech Community

- Der vorhandene Snapdragon-AI-Studio-Thread wurde identifiziert.
- Ein RC2B-Aktualisierungstext wurde vorbereitet.
- Eine tatsächliche Veröffentlichung des RC2B-Updates wurde im Verlauf nicht eindeutig bestätigt; bei Wiederaufnahme nicht ohne Kontrolle als erledigt melden.

### Hugging Face

- Die bisherige RC2A-Landingpage wurde vollständig als RC2B-Fassung neu erstellt.
- Englische Veröffentlichungsdatei: `index.html`.
- Deutsche Kontrollfassung: `index_RC2B_DE_Kontrollfassung.html`.
- Alle `RC2A`- und `rc.2a`-Verweise wurden entfernt.
- Downloadlink zeigt auf `https://github.com/Kreuzhofen/snapdragon-ai-studio/releases/tag/v2.0.0-rc.2b`.
- `style.css` und `snapdragon-ai-studio-banner.png` bleiben unverändert.
- Empfohlene Commit-Nachricht: `Update landing page for Snapdragon AI Studio 2.0 RC2B`.
- Eine tatsächliche Hugging-Face-Commitbestätigung wurde noch nicht gemeldet; Status bei Wiederaufnahme gegebenenfalls kurz prüfen.

### Instagram und Facebook

- Vorerst bewusst zurückgestellt.
- Holger hält reine Update-Posts dort für wenig interessant.
- Vor einer Veröffentlichung soll ein überzeugender visueller Inhalt entstehen, insbesondere ein Bildgenerierungs- oder Vorher-/Nachher-Upscaling-Vergleich.
- Diese Portale nicht als aktuellen Pflichtschritt vor den 4×-Sprint setzen.

## Noch offener Lizenz-/Markenpunkt

Die Lizenz- und Redistributionsprüfung bleibt ein verbindlicher Projektpunkt:

- Rechte und Weitergabebedingungen des RealESRGAN-QNN-Kontexts prüfen.
- Bedingungen der mit beziehungsweise neben der Anwendung benötigten Qualcomm-QNN-/QAIRT-Komponenten prüfen.
- Markenhinweise und unabhängigen Projektstatus weiterhin klar darstellen.
- Keine ungeprüften Qualcomm-Runtime-Dateien zusätzlich paketieren oder veröffentlichen.

Die aktuelle Paketierung ergänzt ausschließlich die bereits getrackte Produktdatei `models\real_esrgan_x4plus.bin`. QNN-Runner, HTP-DLL und Skeleton-Dateien werden aus der vorhandenen kompatiblen Qualcomm-Laufzeit entdeckt und nicht durch diese Änderung neu mitgeliefert.

## Nächster sicherer Schritt morgen: 4×-Sprint

### Ziel

1. Bestehendes 2×-Upscaling unverändert erhalten.
2. Zusätzliches echtes 4×-Upscaling anbieten: `512 × 512 -> 2048 × 2048`.
3. Beide Profile ausschließlich über den vorhandenen RealESRGAN-QNN-/NPU-Pfad ausführen.
4. Originaldatei nie überschreiben.
5. Für jedes Ergebnis einen eindeutigen separaten Ausgabepfad verwenden.
6. 2× und 4× in der UI eindeutig und im bestehenden Phoenix-/Snapdragon-Design auswählbar machen.
7. Zuerst fokussierte Tests, danach betroffene Testmodule; keine Volltestsuite ohne konkreten Anlass.
8. Vor Frozen-Build oder Installer zunächst direkten Python-Test auf dem Entwicklungs-PC Holger durchführen.

### Erster Schritt: bestehende 2×-Verkabelung nur lesen

Tool:

    PowerShell

Rechner:

    Entwicklungs-PC Holger

Modus:

    reine Codeprüfung, kein Build und kein Test

Auszuführen:

```powershell
Set-Location -LiteralPath 'C:\SnapdragonAI'

$gitExe = 'C:\Program Files\Git\cmd\git.exe'

Write-Output 'GIT-STATUS:'

& $gitExe `
    -C 'C:\SnapdragonAI' `
    status --short --branch

Write-Output '4X-RELEVANTE STELLEN:'

& $gitExe `
    -C 'C:\SnapdragonAI' `
    grep -n -C 12 -E `
    'upscale_generated_image_2x|RealESRGAN 2[x×]|upscale.*2x|upscal.*2[x×]' `
    -- `
    'controllers/*.py' `
    'widgets/**/*.py' `
    'tests/*.py'
```

Holger sendet anschließend die Ausgabe. Danach wird der erste eng abgegrenzte Änderungsauftrag für die 2×-/4×-Auswahl erstellt. Noch keine UI- oder Controlleränderung vor dieser Bestandsaufnahme.

## Tagesabschlussstatus 24. August 2026

- `main` und `origin/main` stehen auf `4d271438`.
- Beide RealESRGAN-Commits wurden ohne Force-Push veröffentlicht.
- Runtime-Discovery, Skeleton-Umgebung, Modellpriorität, Frozen-Paketierung und Pfade mit Leerzeichen sind gehärtet.
- Fokussierte Tests: `25 passed, 6 subtests passed`.
- Echter NPU-Smoke-Test `128 -> 512` erfolgreich.
- Echter gekachelter NPU-Smoke-Test `512 -> 2048` erfolgreich; Original unverändert.
- Bestehende 2×-UI-Funktion im neuen Frozen-/Clean-Test-Stand erfolgreich.
- Neuer lokaler Installer-Kandidat mit Hash `875A...C15` sauber auf RC2CleanTest installiert und geprüft, aber nicht als GitHub-Asset veröffentlicht.
- Öffentliches RC2B-Asset bleibt der Installer mit Hash `1E964...24C4`.
- Qualcomm-Discord-Beitrag veröffentlicht.
- Reddit veröffentlicht und technische Rückmeldungen beantwortet.
- Hugging-Face-RC2B-Seite erstellt; tatsächlichen Commitstatus bei Bedarf prüfen.
- Microsoft-RC2B-Update nicht eindeutig als veröffentlicht bestätigt.
- Instagram und Facebook bis zu einem überzeugenden visuellen Vergleich zurückgestellt.
- Nächster Arbeitsschritt ist die read-only PowerShell-Prüfung der bestehenden 2×-Verkabelung als Einstieg in den 4×-Sprint.
- Heute keine weiteren Änderungen, Builds, Installer, Commits oder Pushes ausführen.

## Handover-Übernahme

Diese vollständige aktualisierte Datei zum Download bereitstellen. Holger speichert sie als:

    %USERPROFILE%\Downloads\CHATGPT_HANDOVER.md

Danach startet Holger:

    C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd

Das CMD übernimmt die Datei nach:

    C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md

Es vergleicht die SHA-256-Prüfsummen und löscht den Download nur bei erfolgreicher Übernahme. Die ältere Chronik darf nicht gekürzt oder durch eine verkürzte Zusammenfassung ersetzt werden.

## Ergänzung zum Tagesabschluss 25. August 2026 – SD3.5 `_ssl`-Korrektur

Diese Ergänzung setzt die bestehende Chronologie fort. Der zuvor vorgesehene 4×-Sprint bleibt zurückgestellt, bis der folgende SD3.5-Abschluss vollständig getestet und veröffentlicht ist.

### Ausgangsfehler

Ein Reddit-Tester mit Snapdragon X2E-88-100 meldete beim SD3.5-Installationsschritt „Final target model validation and activation“:

```text
Preflight check failed: import _ssl
ImportError: DLL load failed while importing _ssl:
The specified procedure could not be found.
```

SD 2.1 lief auf demselben Gerät schnell und stabil. Die Ursache lag nicht am Snapdragon-Prozessor und nicht am SD3.5-Modell, sondern an der DLL-Suchumgebung der Frozen-App: PyInstaller kann seinen temporären `_MEIPASS`-DLL-Pfad und zugehörige PATH-Einträge an externe Python-Prozesse vererben.

### Implementierte Korrektur

Commit:

```text
7d5fd47e SD3.5: Fix frozen SSL isolation and path reporting
```

Geänderte getrackte Dateien:

```text
dialogs/model_direct_download_dialog.py
locales/de_DE.json
locales/en_US.json
locales/es_ES.json
tests/test_model_direct_install_flow.py
tests/test_sd35_installer_state_machine.py
tools/sd35_setup_helper.py
```

Wesentliche Änderungen:

- Kindumgebungen werden kopiert; `PYTHONPATH` und `PYTHONHOME` werden entfernt.
- Im Frozen-Windows-Fall werden `_MEIPASS`-Einträge case-insensitiv aus dem Kindprozess-PATH entfernt.
- `SetDllDirectoryW(None)` gilt ausschließlich während des Starts externer SD3.5-Prozesse.
- Der vorherige DLL-Verzeichniswert wird unter Lock und in `finally` wiederhergestellt.
- Venv-Erstellung, Preflight, Pip-Prozesse und `stable_diffusion_v3_5.py` verwenden den zentralen isolierten Launcher.
- Keine globale Prozessumgebung und keine einzelnen DLL-Dateien wurden verändert.
- Die SD3.5-Erfolgsmeldung verwendet nun dynamisch `config.MODELS_DIR / "stable_diffusion_v3_5_qai"`.
- DE/EN/ES verwenden für `sd35_log_path_info` die Vorlage `{path}` statt `C:\SnapdragonAI\...`.

### Automatisierte Prüfungen

Erfolgreich:

```text
Fokussierte DLL-/PATH-Isolation: 5 passed, 32 deselected
tests/test_sd35_installer_state_machine.py: 37 passed
tests/test_model_direct_install_flow.py: 31 passed, 24 subtests passed
Neuer Pfadtest: 1 passed, 30 deselected, 2 subtests passed
py_compile: erfolgreich
git diff --check: erfolgreich; nur LF-/CRLF-Hinweise
```

### Reale Frozen-/Clean-Test-Validierung

Auf `RC2CleanTest` wurde vor der abschließenden Pfadanzeige-Korrektur bereits ein Frozen-Installer mit der `_ssl`-Isolation sauber installiert. Der vollständige SD3.5-Ablauf war erfolgreich:

```text
Abhängigkeiten installieren
Qualcomm SD3.5 vorbereiten und herunterladen
Modell importieren
Modell validieren
Modell aktivieren
Stable Diffusion 3.5 Medium erfolgreich eingerichtet
```

Danach wurde mit der installierten Frozen-App real ein SD3.5-Bild erzeugt. Es trat kein `_ssl`-, DLL- oder Preflight-Fehler mehr auf.

Der tatsächliche Modellpfad wurde separat geprüft:

```text
C:\Users\RC2CleanTest\AppData\Local\Snapdragon AI Studio\models\stable_diffusion_v3_5_qai
12 Dateien
4.219.338.709 Bytes
```

`C:\SnapdragonAI\models\stable_diffusion_v3_5_qai` existierte unter diesem Test nicht. Nur die alte Erfolgsmeldung war hart codiert; diese Anzeige ist im Commit `7d5fd47e` korrigiert.

### Finaler Build aus Commit `7d5fd47e`

Der endgültige interaktive PyInstaller-Build mit PyInstaller 6.21.0 auf ARM64 war erfolgreich:

```text
EXE:
C:\SnapdragonAI\dist\SnapdragonAIStudio\SnapdragonAIStudio.exe

EXE_SHA256:
0A07330B21831607DFB0E7776927A4425182CD3DEF8C3F49E5A387C2601E5788

RealESRGAN-Modell im Build:
38.744.064 Bytes
Hash identisch mit der Quelle: True
```

Finaler Installer:

```text
C:\SnapdragonAI\dist\installer\SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe
Größe: 303.910.290 Bytes
SHA256: D12BC7DE1DD8815F217C1A2B1B82EBC48D5D458B214E26522A44C2B2E2FA5BE9
```

Dieser Installer wurde mit identischem Hash nach folgendem Pfad kopiert:

```text
C:\Users\Public\Downloads\SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe
```

Normale PyInstaller-INFO-Ausgaben auf `stderr` hatten bei zwei früheren Orchestrierungsversuchen zu einem PowerShell-`NativeCommandError` beziehungsweise einem abgebrochenen Prozess mit `0xC000013A` geführt. Das war kein Produktcodefehler. Die alten Builds wurden jeweils recoverbar gesichert. Der erfolgreiche finale Build wurde anschließend direkt und mit sichtbarer PyInstaller-Ausgabe ausgeführt.

### Git- und Veröffentlichungsstand bei Feierabend

```text
main:        7d5fd47e
origin/main: 4d271438
Status: main ist 1 Commit voraus
```

- Commit `7d5fd47e` ist lokal vorhanden, aber noch nicht gepusht.
- Der finale Installer mit Hash `D12B...A5BE9` ist noch nicht als öffentliches GitHub-Release-Asset veröffentlicht.
- Das öffentliche RC2B-Asset bleibt bis zur finalen Abnahme unverändert.
- Bekannte untracked Dateien blieben unangetastet.
- Kein weiterer Commit und kein Push nach dem finalen Build.
- Eine englische Reddit-Zwischenantwort mit Dank, eingegrenzter Ursache, laufender Arbeit und noch unbekanntem Termin wurde vorbereitet. Ob Holger sie tatsächlich veröffentlicht hat, wurde nicht bestätigt.

### Verbindlich nächster Schritt – bewusst auf später verschoben

Holger hat den folgenden Test ausdrücklich auf später verschoben und Feierabend gemacht. Nicht direkt mit dem 4×-Sprint beginnen.

Testumgebung:

```text
Werkzeug: PowerShell plus installierte Anwendung
Rechner/Benutzer: RC2CleanTest
Modus: Überinstallation des finalen RC2B-Installers
```

Reihenfolge:

1. Hash des Installers unter `C:\Users\Public\Downloads` gegen `D12BC7DE1DD8815F217C1A2B1B82EBC48D5D458B214E26522A44C2B2E2FA5BE9` prüfen.
2. Vorhandene Snapdragon-AI-Studio-App vollständig schließen.
3. Finalen Installer als Überinstallation ausführen; keine saubere Neuinstallation und keine erneute SD3.5-Einrichtung.
4. Installierte EXE gegen `0A07330B21831607DFB0E7776927A4425182CD3DEF8C3F49E5A387C2601E5788` prüfen.
5. Prüfen, dass das vorhandene SD3.5-Modell vor und nach der Überinstallation weiterhin 12 Dateien und 4.219.338.709 Bytes umfasst.
6. Installierte App starten und kontrollieren, dass SD3.5 installiert und aktiv bleibt.
7. Mit deaktiviertem RealESRGAN-2× eine weitere reale SD3.5-Bildgenerierung durchführen.
8. Erst bei erfolgreichem Ergebnis Commit `7d5fd47e` mit `git push origin main` veröffentlichen.
9. Danach den öffentlichen RC2B-Installer beziehungsweise das Release-Asset kontrolliert aktualisieren und den Reddit-Tester informieren.
10. Erst nach Abschluss dieses SD3.5-Hotfixes mit dem 4×-Sprint fortfahren.

### Feierabend 25. August 2026

- Der ausstehende finale Überinstallationstest ist absichtlich vertagt, nicht fehlgeschlagen.
- Alle relevanten Quellcodeänderungen sind committed.
- Finaler Frozen-Build und finaler Installer sind lokal vorhanden und gehasht.
- Heute keine weiteren Tests, Installationen, Commits, Pushes oder Release-Änderungen durchführen.

# Ergänzung: Branding- und Bannerentscheidungen nach dem SD3.5-Feierabendstand

Diese Ergänzung dokumentiert ausschließlich die danach erfolgte visuelle Markenarbeit. Für den technischen Git-, Build-, Installer- und Hotfixstatus gelten weiterhin die unmittelbar vorhergehenden SD3.5-Abschnitte. Insbesondere ist die dort beschriebene finale Überinstallation nicht automatisch als abgeschlossen anzusehen.

## Eingefrorene visuelle Referenz

Holger hat einen Bannerentwurf als visuelle Referenz ausdrücklich freigegeben und zum Einfrieren bestimmt. Der freigegebene Aufbau enthält:

- die Wortmarke `HK NPU`,
- darunter `STUDIO`,
- den Claim `Your Hardware • Your AI • Your Control`,
- die Zeile `Local AI for Snapdragon® PCs`,
- das bestehende Phoenix-Motiv,
- das Chip-/NPU-Motiv,
- den bestehenden technischen Hintergrund,
- die vorhandene Symbolleiste,
- den Footer `© 2026 Holger Kreuzhofen • Founder • Product Owner • Release Manager`.

Diese Komposition dient als verbindliche visuelle Referenz für weitere Bannerarbeiten. Phoenix, Chip, Hintergrund, Symbolleiste und Footer dürfen nicht beiläufig verändert werden.

## Letzte Detailentscheidung zum Banner

Nach der ersten Freigabe wurde eine minimale professionellere Ausarbeitung diskutiert:

- Der Claim sollte sich stilistisch etwas stärker an `STUDIO` orientieren.
- Für `HK` wurde testweise etwas mehr Schattierung beziehungsweise ein leicht metallischer Eindruck erwogen.

Holgers abschließende Entscheidung:

- Die veränderte `HK`-Darstellung wurde verworfen.
- `HK` soll wieder exakt den zuvor freigegebenen ursprünglichen Charakter besitzen.
- Die übrige zurückhaltende Ausarbeitung wurde als grundsätzlich passend bewertet.
- Keine weitere eigenständige Veränderung des `HK`-Zeichens ohne neue ausdrückliche Freigabe.

## Namensdiskussion: `HK NPU Studio`

`HK NPU Studio` wurde als möglicher zukünftiger Produkt- beziehungsweise Markenname diskutiert. Dabei wurden insbesondere die Eigenständigkeit der Marke und die geringere Abhängigkeit vom Wort `Snapdragon` betrachtet.

Verbindlicher aktueller Stand:

- Eine Umbenennung der Software wurde nicht abschließend beschlossen.
- Der gegenwärtige offizielle Projekt- und Produktname bleibt `Snapdragon AI Studio – Phoenix Engine`.
- `HK NPU Studio` ist vorerst ein Branding-/Namenskandidat und Bestandteil der freigegebenen Bannerreferenz, aber noch kein bestätigter technischer Produktwechsel.
- Die Bannerfreigabe allein autorisiert keine Änderungen an Quellcode, Installer, App-Datenpfaden, Registry, Release-Metadaten, GitHub, Dokumentation oder Downloadnamen.

Eine spätere Produktumbenennung wäre ein eigener kontrollierter Sprint. Vor einer Umsetzung müssten mindestens geprüft und geplant werden:

- sichtbarer App-Name und Fenstertitel,
- Installername, Publisherdaten und Deinstallationseintrag,
- `%LOCALAPPDATA%`- und Modell-/Ausgabepfade,
- Migration vorhandener Benutzerdaten und Preferences,
- Release-Metadaten, Dokumentation und Übersetzungen,
- GitHub-/Portaltexte und Downloadlinks,
- Markenhinweise sowie die Kommunikation des unabhängigen Projektstatus.

Keine dieser Änderungen ohne Holgers ausdrückliche Entscheidung und einen verlustfreien Migrationsplan durchführen.

## Signaturen und Rollenbezeichnungen

- Der Bannerfooter bleibt in der freigegebenen Referenz: `© 2026 Holger Kreuzhofen • Founder • Product Owner • Release Manager`.
- Die bisherige vollständige Signatur für offizielle Reddit-Antworten bleibt davon unberührt:

**Holger Kreuzhofen**  
Founder & Lead Developer  
Snapdragon AI Studio – Phoenix Engine

- Eine Diskussion über eine neue allgemeine Signatur gilt noch nicht als verbindliche Ersetzung dieser bestehenden Kommunikationsregel.

## Technischer Status bleibt unverändert offen

Seit dem letzten dokumentierten SD3.5-Feierabendstand ist in den verfügbaren bestätigten Angaben kein neuer technischer Abschluss nachgewiesen. Deshalb weiterhin nicht als erledigt melden:

- finale Überinstallation des Installers mit SHA-256 `D12BC7DE1DD8815F217C1A2B1B82EBC48D5D458B214E26522A44C2B2E2FA5BE9` auf RC2CleanTest,
- abschließende Bestätigung, dass das vorhandene SD3.5-Modell unverändert erhalten und aktiv bleibt,
- reale SD3.5-Generierung mit dem finalen Überinstallationsstand,
- Push von `7d5fd47e`,
- kontrollierter Austausch des öffentlichen RC2B-Installer-Assets,
- endgültige Information an den Reddit-Tester.

Falls diese Schritte inzwischen außerhalb des dokumentierten Verlaufs abgeschlossen wurden, zuerst die vollständigen PowerShell-/Git-/Hash-Ergebnisse anfordern und danach die Übergabe erneut ergänzen. Nicht aus späterer Branding-Arbeit auf einen technischen Abschluss schließen.

## Aktuell sichere Reihenfolge bei Wiederaufnahme

1. Auf `RC2CleanTest` den in der SD3.5-Ergänzung beschriebenen finalen Überinstallationstest abschließen und protokollieren.
2. Nur bei vollständigem Erfolg `7d5fd47e` pushen und das RC2B-Asset kontrolliert ersetzen.
3. Hash, Release-Status, Tag und installierte Anwendung erneut verifizieren.
4. Den betroffenen Reddit-Tester sachlich über die bestätigte Korrektur informieren.
5. Danach den bereits geplanten echten 4×-RealESRGAN-Produktsprint fortsetzen; die vorhandene 2×-Funktion unverändert erhalten.
6. Eine mögliche Umbenennung zu `HK NPU Studio` separat behandeln und nicht mit dem 4×- oder SD3.5-Sprint vermischen.

## Handover-Übernahme nach dieser Aktualisierung

Diese vollständige, nicht gekürzte Datei als `CHATGPT_HANDOVER.md` herunterladen. Anschließend auf dem Entwicklungs-PC Holger ausführen:

```powershell
& 'C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd'
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Das CMD muss die SHA-256-Prüfung erfolgreich abschließen, bevor die heruntergeladene Datei entfernt wird.


# Ergänzung: Tagesabschluss 26. August 2026 – Rebranding auf HK NPU STUDIO abgeschlossen und veröffentlicht

Diese Ergänzung führt die bestehende Chronik fort und hat für Markenstand, Git-Stand und den nächsten Branding-Schritt Vorrang vor den älteren Abschnitten, in denen `HK NPU Studio` noch lediglich als Kandidat oder das Rebranding noch als offen beschrieben wird.

## Verbindliche Markenentscheidung

Die Namensänderung ist abgeschlossen. Holger ist mit der neuen Produktbezeichnung einverstanden.

Verbindliche Hauptmarke:

```text
HK NPU STUDIO
```

Verbindlicher Claim:

```text
Your Hardware • Your AI • Your Control
```

Verbindliche Plattformbeschreibung:

```text
Local AI for Snapdragon® PCs
```

Verbindlicher Feature-Hinweis:

```text
Featuring Phoenix Boost
```

Phoenix bleibt als Bildmarke beziehungsweise Feature-Bezeichnung erhalten. `Phoenix Engine` soll nicht mehr als konkurrierende sichtbare Produktmarke auftreten; technische Phoenix-Bezeichnungen in internen Engine-Dateien dürfen bestehen bleiben.

Für sichtbare Produktbezeichnungen gilt ab jetzt einheitlich:

```text
HK NPU STUDIO
```

`STUDIO` wird sichtbar überall in Großbuchstaben geschrieben. Gemischte sichtbare Schreibweisen wie `HK NPU Studio` sollen nicht neu eingeführt werden.

## Markenhinweis zu Snapdragon

Die Plattformbeschreibung `Local AI for Snapdragon® PCs` bleibt bewusst erhalten.

Der vereinbarte Trademark-Hinweis lautet:

```text
Snapdragon is a trademark or registered trademark of Qualcomm Incorporated.
```

Die frühere zusätzliche Formulierung, die eine mögliche Verwechslung mit Qualcomm ausdrücklich verneinte, wird nicht mehr benötigt.

Der Trademark-Hinweis soll später auch auf den öffentlichen Projektflächen, insbesondere GitHub, konsistent berücksichtigt werden. Zuerst wurde jedoch die Software selbst umgestellt.

## Phase 1A.1 – Schutz der technischen Legacy-Verträge

Vor dem sichtbaren Rebranding wurde `tests/test_rebranding_legacy_contracts.py` als Schutzschicht erstellt.

Abgesicherte Verträge:

1. Legacy-Migrationspfad:

```text
"Programs" / "Snapdragon AI Studio" / "output"
```

2. Early-Generation-Abort-Logpfad:

```text
"Snapdragon AI Studio" / "logs" / "early_generation_abort.log"
```

3. Vollständiger `app.ico`-Vertrag:
   - `BrandManager.APP_ICON`
   - PyInstaller-Icon in `tools/build_app.py`
   - `SetupIconFile` im Installer
   - Existenz von `assets/brand/icons/app.ico`

4. Technische User-Agents in:
   - `app/model_downloader.py`
   - `app/settings_manager.py`
   - `engine/application_update_service.py`
   - `engine/download_service.py`

5. Freigegebener Brand Master:
   - Existenzprüfung
   - SHA-256 aus den tatsächlichen Dateibytes
   - exakter Sollwert:

```text
3845D1D8DA50334AB14EEAC6EED282C21FDC3B2DF24A5CE8D55A627A6826ECB1
```

Zusätzliche geschützte Pfadverträge:

```text
ASSET_INDEX_DB = DATA_DIR / "asset_index.sqlite3"
REALESRGAN_MODEL = MODELS_DIR / "real_esrgan_x4plus.bin"
```

Testergebnis:

```text
15 passed
```

Der Brand-Master-Hash stimmte in Vorprüfung und Schutztest exakt überein.

## Phase 1B – sichtbares Rebranding der Software

Das sichtbare Produktbranding wurde auf `HK NPU STUDIO` umgestellt.

Betroffene zentrale Brandingquellen:

```text
release.json
engine/brand_manager.py
resources/branding.py
resources/branding/tokens.json
```

Zusätzlich wurden sichtbare Texte kontrolliert in folgenden Bereichen angepasst:

- Anwendung/Fenstertitel
- Dashboard
- Home
- Einstellungen
- About
- Plugins
- Modellmanager
- Modellinstallations- und Downloaddialoge
- Ollama- und Qwen-Setup
- Prompt-/Generierungsansicht
- Menü
- Stub-/Diagnoseanzeigen, soweit sichtbar
- DE-/EN-/ES-Lokalisierungen
- DE-/EN-/ES-Hilfetexte
- Installer-Sichttexte
- zugehörige Tests

Technische Pfade, Legacy-Migrationen, AppId, Executable-Name und technische Phoenix-Engine-Strukturen wurden bewusst nicht pauschal umbenannt.

Insbesondere bleibt der technische Executable-Name:

```text
SnapdragonAIStudio.exe
```

Bestehende `%LOCALAPPDATA%\Snapdragon AI Studio\...`-Benutzerdatenpfade bleiben aus Kompatibilitäts- und Migrationsgründen erhalten.

## Header – finale sichtbare Struktur

Nach mehreren visuellen Varianten wurde für den oberen linken Header festgelegt:

```text
HK NPU STUDIO
Local AI for Snapdragon® PCs - Startseite
```

Der Produktname soll als Wiedererkennungswert in einer Zeile erscheinen und nicht in `HK NPU` plus separate `STUDIO`-Zeile aufgeteilt werden.

Die konkrete Seitenbezeichnung wie `Startseite` bleibt über die vorhandene Lokalisierung dynamisch.

## About-Dialog – vereinbarte Informationsreihenfolge

Für den About-/Info-Bereich wurde folgende Markenstruktur festgelegt:

```text
HK NPU STUDIO
Version ...
Local AI for Snapdragon® PCs
Your Hardware • Your AI • Your Control
Featuring Phoenix Boost
```

Die Informationen stehen untereinander.

Der frühere zusätzliche Satz zur Abgrenzung beziehungsweise möglichen Verwechslungsgefahr kann entfallen. Der sachliche Trademark-Hinweis zu Snapdragon bleibt.

## Sidebar – finale Struktur

Der frühere sichtbare Text:

```text
Arbeitsbereich 1.0
```

wurde in der Sidebar ausschließlich durch:

```text
Featuring Phoenix Boost
```

ersetzt.

Final gerendert:

```text
HK NPU STUDIO
Featuring Phoenix Boost
```

Die alte Locale-Zeichenfolge `nav_workspace_version = "Arbeitsbereich 1.0"` kann als ungenutzter Legacy-Wert bestehen bleiben, wird aber nicht mehr gerendert.

### Breitenvertrag der Sidebar-Markenfläche

Holgers Vorgabe:

- `Featuring Phoenix Boost` darf nicht breiter wirken als `HK NPU STUDIO`.
- Beide Zeilen linksbündig.
- Sidebar-Breite bleibt 220 px.
- Keine künstliche horizontale Stauchung.
- Reale Tk-Fontmetriken verwenden.
- Keine Abschneidung bei 100 %, 125 %, 150 % und 175 % Windows-Skalierung.

Umgesetzt wurde eine dynamische Wahl der größten ganzzahligen Punktgröße für die Unterzeile, deren reale Tk-Messbreite die Hauptzeile nicht überschreitet.

Gemessener Stand:

| Skalierung | Hauptzeile | Unterzeile | Sidebar |
| --- | --- | --- | --- |
| 100 % | 13 pt / 101 px | 9 pt / 94 px | 220 px |
| 125 % | 13 pt / 124 px | 8 pt / 108 px | 220 px |
| 150 % | 13 pt / 155 px | 9 pt / 149 px | 220 px |
| 175 % | 13 pt / 178 px | 9 pt / 168 px | 220 px |

## Brand Master

Der freigegebene Brand Master wurde in den Rebranding-Arbeiten nicht verändert.

Datei:

```text
assets/brand/hk_npu_studio_banner_master.png
```

Verbindlicher SHA-256:

```text
3845D1D8DA50334AB14EEAC6EED282C21FDC3B2DF24A5CE8D55A627A6826ECB1
```

Dieser Hash wurde auch unmittelbar nach dem Rebranding-Commit erneut bestätigt:

```text
BRAND_MASTER_IDENTISCH=True
```

## Banner – noch ein späterer visueller Feinschliff vorgesehen

Obwohl die Namensänderung selbst abgeschlossen ist, möchte Holger den Banner bei Gelegenheit noch einmal visuell prüfen.

Aktuelle Überlegung:

- Im bisherigen Banner steht `HK NPU` in einer Zeile und `STUDIO` darunter.
- Für stärkere Wiedererkennung tendiert Holger inzwischen dazu, auch im Banner `HK NPU STUDIO` zusammenhängend in einer Zeile darzustellen.
- Diese Banneränderung wurde noch nicht als umgesetzt bestätigt.
- Den bestehenden Brand Master nicht eigenmächtig verändern.
- Vor einer tatsächlichen Änderung erneut mit Holger abstimmen und ausschließlich die gewünschte Wortmarkenanordnung ändern; Phoenix, Chip, Hintergrund, Symbolleiste, Claim und übrige freigegebene Gestaltung nicht beiläufig verändern.

## Tests des Rebrandings

Bestätigte Kernprüfungen:

```text
tests/test_rebranding_legacy_contracts.py
15 passed
```

Fokussierter Bestandslauf:

```text
52 passed
```

Gesamtstand dieses Prüfblocks:

```text
67 passed
```

Zusätzlich wurden unter anderem erfolgreich geprüft:

- Settings-/Home-Brandingtests
- `test_release_polish_final.py`
- Header-Verträge in Dark/Light und 100/125/150 %
- Sidebar-/Header-/About-/Settings-Prüfungen
- Prompt-Brandingtests
- Python-Syntax
- JSON für Release-/Branding-/Locale-Dateien
- `git diff --check`

Einige direkte Tk-Tests waren zeitweise durch die lokale Tcl/Tk-Installation unter `C:\Program Files\Python311-arm64` blockiert (`init.tcl`, `tk.tcl`, `ttk/button.tcl`). Dies wurde als lokale Testumgebungsstörung und nicht als Rebranding-Produktfehler klassifiziert.

Keine Full-Suite wurde für das Rebranding ausgeführt.

## Rebranding-Commit

Nach expliziter Commit-Freigabe wurde erstellt:

```text
86c42cec Rebrand application as HK NPU STUDIO
```

Commitumfang:

```text
38 files changed, 591 insertions(+), 217 deletions(-)
```

Neu im Commit:

```text
assets/brand/hk_npu_studio_banner_master.png
tests/test_rebranding_legacy_contracts.py
```

Die Commitprüfung ergab:

```text
ANZAHL_DATEIEN_IM_COMMIT=38
NOCH_GESTAGED=0
COMMIT_ERSTELLT=True
```

Nach dem Commit waren ausschließlich die bekannten untracked Projektdateien vorhanden.

## Rebranding-Push

Holger gab den Push ausdrücklich frei.

Der Push auf GitHub wurde anschließend erfolgreich verifiziert:

```text
LOCAL_HEAD=86c42cec3c48c3087376a96381e803ab57d3491f
ORIGIN_MAIN=86c42cec3c48c3087376a96381e803ab57d3491f
LOCAL_REMOTE_IDENTISCH=True
```

Git-Log:

```text
86c42cec (HEAD -> main, origin/main, origin/HEAD) Rebrand application as HK NPU STUDIO
```

Damit ist der bestätigte Git-Stand:

```text
main = origin/main = 86c42cec
```

Der Push änderte den Quellcode auf GitHub `main`, aber nicht automatisch die sichtbare GitHub-Startseite/README, Repository-Beschreibung, Social-Media-Flächen oder sonstige externe Markenflächen.

Diese öffentlichen Flächen sollen separat und kontrolliert auf `HK NPU STUDIO` umgestellt werden.

## Bekannte untracked Dateien nach dem Push

Nach dem verifizierten Push wurden unter anderem weiterhin folgende untracked Dateien gemeldet:

```text
RC2A_RELEASE_NOTES_FINAL.md
RC2_GITHUB_NOTES_CURRENT.md
RC2_GITHUB_NOTES_CURRENT_UTF8.md
RC2_GITHUB_NOTES_WITH_KNOWN_ISSUE.md
RC2_RELEASE_NOTES.md
RC2_RELEASE_NOTES_CLEAN.md
README_BEFORE_RC2A_DOCS.md
README_LOCKED_BACKUP.md
assets/brand/ChatGPT Image 9. Aug. 2026, 21_42_14.png
assets/brand/reddit_profilbild_512x512.jpg
assets/brand/snapdragon-ai-studio-x-header-1500x500.png
docs/CHATGPT_HANDOVER.md
docs/SnapdragonAI_ChatGPT_Handover_2026-08-21.md
presets/wolf.json
sd35_venv/
temp_traceback.txt
temp_venv/
```

Diese Dateien weiterhin nicht pauschal stagen, löschen oder verändern.

## Arbeitsweise – neue ausdrückliche Vorgabe von Holger

Holger möchte bei der gemeinsamen technischen Arbeit möglichst ohne unnötige Zwischenstopps arbeiten.

Verbindlich:

- Nach einem ausgeführten Prüfschritt direkt den nächsten passenden Befehl geben.
- Nicht nach jedem routinemäßigen Schritt mit „soll ich weitermachen?“ stoppen.
- Freigabegrenzen für echte Änderungen, Staging, Commit, Push, Build/Installer oder Veröffentlichungen bleiben bestehen.
- Wenn eine solche Freigabe erforderlich ist, klar benennen, was genau freigegeben werden soll.
- PowerShell-Befehle weiterhin vollständig mit absoluten Pfaden liefern.
- Token sparsam einsetzen.

## Hilfsdatei gegen unerwünschten Standby

Holger ist genervt davon, dass der Entwicklungs-Laptop während längerer Arbeiten ausgeht. Dafür wurde eine optionale Desktop-BAT vorgeschlagen, die während ihrer Laufzeit Standby und Bildschirmabschaltung verhindert, ohne die Windows-Energieeinstellungen dauerhaft umzuschreiben.

Die BAT verwendet `SetThreadExecutionState(0x80000003)` und hält das zugehörige PowerShell-Fenster offen. Beim Schließen des Fensters gelten wieder die normalen Windows-Energieeinstellungen.

Vorgeschlagener Desktop-Dateiname:

```text
PC_WACH_HALten.bat
```

Diese Hilfsdatei ist kein Bestandteil des Repositorys und soll nicht ins Projekt committed werden.

## Status der Namensänderung am Feierabend

Holgers ausdrückliche Bewertung:

- Die Namensänderung war schwierig, ist für ihn jetzt aber in Ordnung.
- `HK NPU STUDIO` ist die verbindliche sichtbare Produktmarke.
- `STUDIO` wird einheitlich großgeschrieben.
- `Local AI for Snapdragon® PCs` bleibt.
- `Your Hardware • Your AI • Your Control` bleibt.
- `Featuring Phoenix Boost` bleibt.
- Der Brand Master ist unverändert und per SHA-256 geschützt.
- Rebranding-Commit `86c42cec` ist erstellt und auf `origin/main` gepusht.
- Git `main` und `origin/main` sind identisch.
- Die sichtbare GitHub-Startseite und weitere externe Markenflächen wurden durch diesen Push nicht automatisch vollständig umgestellt.
- Der Banner soll später noch einmal hinsichtlich einer einzeiligen Wortmarke `HK NPU STUDIO` geprüft werden.
- Am Feierabend keine weiteren Brandingänderungen durchführen.

## Nächster sicherer Branding-Schritt bei Wiederaufnahme

Nicht erneut die Namensentscheidung aufrollen.

1. Zuerst Git-Status und HEAD kurz prüfen.
2. Danach die noch sichtbaren öffentlichen Flächen systematisch auf das neue Branding umstellen, beginnend mit GitHub/README beziehungsweise Repository-Darstellung.
3. Dabei `HK NPU STUDIO`, Claim, Plattformbeschreibung, Phoenix Boost und den vereinbarten Snapdragon-Trademark-Hinweis konsistent verwenden.
4. Technische Legacy-Pfade und Executable-Namen nicht aus kosmetischen Gründen umbenennen.
5. Banneränderung separat behandeln: nur nach erneuter Freigabe die Wortmarke von der bisherigen Zweizeilenanordnung auf `HK NPU STUDIO` in einer Zeile ändern.
6. Keine externe Veröffentlichung oder Release-Manipulation ohne ausdrückliche Freigabe.

## Handover-Übernahme nach dieser Ergänzung

Diese Datei wurde nicht gekürzt oder neu aufgebaut, sondern um diesen Tagesabschluss ergänzt.

Holger speichert die bereitgestellte Datei als:

```text
%USERPROFILE%\Downloads\CHATGPT_HANDOVER.md
```

und startet anschließend:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf nicht durch eine verkürzte Fassung ersetzt werden.


# CHATGPT_HANDOVER – Ergänzung 27. August 2026

> Diese Ergänzung ist an die vollständige bestehende `CHATGPT_HANDOVER.md` anzuhängen.
> Ältere Chronik nicht löschen oder kürzen. Bei widersprüchlichen Statusangaben hat diese neuere Ergänzung Vorrang.

## Arbeitsregel

- Sprache: Deutsch.
- Ab jetzt besonders tokenoptimiert arbeiten: kurze Antworten, kompakte Codex-Prompts, gezielte Tests statt Full-Suite.
- Keine Builds/Commits/Pushes ohne abgestimmten Schritt.
- Niemals `git add .`; bekannte untracked Dateien nicht anfassen.

## Rebranding – verbindlicher neuer Produktstand

Hauptname:

`HK NPU STUDIO`

Öffentliche Markenstruktur:

- `HK NPU`
- darunter `STUDIO`
- Claim: `Your Hardware • Your AI • Your Control`
- Unterzeile: `Local AI for Snapdragon® PCs`
- Phoenix-/Chip-Motiv und eingefrorener Bannerhintergrund unverändert.
- Phoenix Engine und Phoenix Boost bleiben als Bezeichnungen bestehen.

Das Rebranding ist technisch umgesetzt, aber noch nicht release-abgenommen.

## Git-Ausgangspunkt vor dem Rebranding-Sprint

Bestätigt:

- Repository: `C:\SnapdragonAI`
- Branch: `main`
- `HEAD = origin/main = 9e98d586`
- Commit: `Remove Qualcomm disclaimer note from README`
- Remote weiterhin: `https://github.com/Kreuzhofen/snapdragon-ai-studio.git`
- Repository-Slug wurde noch NICHT umbenannt.

## GitHub RC2B – Übergang zum Rebranding

Öffentlicher Release `v2.0.0-rc.2b` bleibt als historischer Pre-release bestehen.

Durchgeführt:

- Rebranding-Hinweis oben in Release Notes veröffentlicht:
  `Rebranding in progress`
- Hinweis erklärt Übergang von Snapdragon AI Studio zu HK NPU STUDIO.
- Alter RC2B-Installer `SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe` aus dem Release entfernt.
- Release und Tag wurden NICHT gelöscht.
- Danach: `RC2B_ASSETS=0`.
- Ältere historische Releases bleiben unangetastet.

## Rebranding-Sprint

Codex führte einen kontrollierten Rebranding-Sprint aus.

Technischer Zielvertrag:

```text
Produkt:        HK NPU STUDIO
Executable:     HKNPUStudio.exe
Distribution:   dist/HKNPUStudio/
Installer:      HKNPUStudio-<Version>-ARM64-Setup.exe
Benutzerdaten:  %LOCALAPPDATA%\HK NPU STUDIO\
Logdatei:       hk_npu_studio.log
User-Agent:     HKNPUStudio/<Version>
```

Wichtig:

- Installer-AppId bleibt unverändert, damit vorhandene Installationen als Upgrade erkannt werden.
- `%LOCALAPPDATA%\Snapdragon AI Studio\` bleibt Legacy-Quelle.
- Migration kopiert rekursiv, löscht Quellen nicht und überschreibt vorhandene Zieldateien nicht.
- Symlinks werden nicht verfolgt.
- Migration ist idempotent.
- Modelle, Preferences, Outputs, Logs und sonstige Daten werden berücksichtigt.
- bestehender alter Output-Import bleibt erhalten.
- Migration läuft vor Sprache/Settings/Logging.
- RealESRGAN besitzt weiterhin Legacy-Modellfallback.
- interner Klassenname `SnapdragonAIStudioV2` blieb bewusst bestehen.
- GitHub-Slug und `installer/snapdragon_ai_studio.iss` als technischer Dateiname blieben zunächst bestehen.
- Phoenix Engine / Phoenix Boost NICHT umbenannt.

Umfang:

`108 files changed, 435 insertions(+), 313 deletions(-)`

Kein `git add`, Commit oder Push.

### Rebranding-Tests

Bestätigt:

- Migration/Legacy/Release/Update: `34 passed`
- RealESRGAN/Frozen-Verträge: `39 passed, 7 subtests`
- Header/Sidebar/About/Settings: `5 passed`
- Installer/Launcher/Model Registry: `17 passed`
- Logging: `3 passed`
- abschließender fokussierter Lauf: `58 passed`
- `py_compile`: bestanden
- `release.json`: gültig
- `git diff --check`: bestanden; nur LF/CRLF-Hinweise
- kein Full-Suite-Lauf

Aktive Altname-Fundstellen: keine unbeabsichtigten mehr.
Verbleibende Altbezeichnungen sind Legacy-, historische oder bewusst interne Verträge.

## Neuer Frozen-Build

Erster HK-NPU-STUDIO-Frozen-Build erfolgreich:

- `C:\SnapdragonAI\dist\HKNPUStudio\HKNPUStudio.exe`
- ProductName: `HK NPU STUDIO`
- FileDescription: `HK NPU STUDIO`
- OriginalFilename: `HKNPUStudio.exe`
- InternalName: `HKNPUStudio`
- ProductVersion: `2.0.0-rc.2b`

RealESRGAN-Stagingmodell:

- Größe: `38,744,064 Bytes`
- SHA-256: `AB62398BF9CA61209E4DAB5EB5776F032760B777A759663CD67C14CFFF12E525`
- Quelle und Staging byteidentisch.

## Manueller Frozen-Test – Entwicklungs-PC Holger

Neue und alte AppData-Struktur existieren parallel:

`C:\Users\holge\AppData\Local\HK NPU STUDIO\`

und Legacy:

`C:\Users\holge\AppData\Local\Snapdragon AI Studio\`

Im neuen Pfad wurden u.a. bestätigt:

- `data`
- `input`
- `logs`
- `models`
- `output`
- `sd35_venv`
- `temp`

Legacy-Ordner blieb erhalten.

## RealESRGAN-Frozen-Test – gefundener Fehler

Beim 4×-NPU-Upscaling öffneten sich pro Tile sichtbare Konsolen-/PowerShellfenster.

Diagnose:

- `modules/qnn.py`
- `run_qnn_context()`
- `subprocess.run(...)` startete `qnn-net-run.exe` ohne `CREATE_NO_WINDOW`.
- Beim untersuchten 512×512-Bild: 5×5 Raster = 25 QNN-Prozesse.
- Zweiter produktiver QNN-Weg `engine/backends/qnn_backend.py` war bereits geschützt.

### Weißer Balken

Der sichtbare weiße vertikale Balken im 4×-Ergebnis war KEIN Stitching-/Crop-/Overlap-Fehler.

Bestätigt:

- Balken bereits im tatsächlich an RealESRGAN übergebenen 512×512-Quellbild.
- unabhängige überlappende QNN-Tiles enthielten denselben Balken bereits vor dem Stitching.
- keine Bildlogik ändern.

Tile-Daten:

- `TILE_SIZE=128`
- `SCALE=4`
- nomineller `TILE_OVERLAP=16`
- Positionen bei 512: `0, 96, 192, 288, 384`
- Raster: `5×5`
- Output: `2048×2048`

## QNN-Konsolenfix

Minimal umgesetzt in:

- `modules/qnn.py`
- `tests/test_realesrgan_qnn_runtime.py`

Änderung:

```python
subprocess.run(
    cmd,
    env=env,
    cwd=input_list.parent,
    check=True,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
```

Keine Tile-/Crop-/Overlap-/Stitching-/Bildlogik geändert.

Tests:

- neuer Konsolen-Regressions-Test: `1 passed`
- komplette `tests/test_realesrgan_qnn_runtime.py`: `34 passed`
- `py_compile`: bestanden
- `git diff --check`: bestanden

## Frozen-Build nach QNN-Fix

Neu gebaut:

`C:\SnapdragonAI\dist\HKNPUStudio\HKNPUStudio.exe`

- Größe: `77,428,727 Bytes`
- SHA-256: `80613512FFDDD8A2512260FB88902BADC1CAF767EAE3334FB13F1405342F5012`
- ProductName: `HK NPU STUDIO`
- RealESRGAN-Modellvertrag weiterhin erfüllt und byteidentisch.

## Aktueller STOP-Punkt / nächster Schritt

NOCH NICHT durchgeführt:

- manueller RealESRGAN-Frozen-Retest des NEUEN Builds nach `CREATE_NO_WINDOW`
- Installer-Build
- Installation/RC2CleanTest des rebrandeten Builds
- Commit
- Push
- GitHub-Repo-Rename
- Portal-/Post-Rebranding

### Bei Wiederaufnahme zuerst

Entwicklungs-PC Holger, Frozen-Modus:

```powershell
& 'C:\SnapdragonAI\dist\HKNPUStudio\HKNPUStudio.exe'
```

Dann denselben RealESRGAN-NPU-Upscale-Test wiederholen und nur bestätigen:

1. Konsolenfenster beim Upscaling: **NEIN**
2. Upscale erfolgreich: **JA**
3. App sonst stabil: **JA**

Nur wenn dieser Test grün ist:

1. neuen `HKNPUStudio-<Version>-ARM64-Setup.exe` bauen,
2. SHA-256 erfassen,
3. auf `RC2CleanTest` saubere Neuinstallation und danach erforderlichen Legacy-/Upgrade-Test durchführen,
4. Rebranding, Pfade, Migration, Startmenü/Shortcut, Generierung, Phoenix Boost, Galerie und RealESRGAN prüfen,
5. erst danach Commit/Push nach ausdrücklicher Freigabe,
6. anschließend GitHub-Repo von `snapdragon-ai-studio` auf `hk-npu-studio` umbenennen,
7. lokale Remote-URL aktualisieren,
8. README/GitHub-Metadaten und danach Reddit/Microsoft/weitere Portale aktualisieren.

## Statusflags

```text
REBRANDING_IMPLEMENTIERT=True
REBRANDING_RELEASE_ABGENOMMEN=False
RC2B_ALTER_INSTALLER_ENTFERNT=True
GITHUB_REPO_UMBENANNT=False
QNN_KONSOLEN_FIX_IMPLEMENTIERT=True
BILDLOGIK_GEAENDERT=False
FROZEN_BUILD_NACH_FIX=True
FROZEN_MANUELLER_RETEST_NACH_FIX=False
INSTALLER_BUILD=False
RC2CLEAN_TEST=False
GIT_ADD=False
COMMIT=False
PUSH=False
```

# Ergänzung: später 27. August 2026 – finale Rebranding-/Installer-/UI-Arbeiten

Diese spätere Ergänzung hat für den technischen Stand des 27. August Vorrang vor früheren STOP-Punkten desselben Tages. Die ältere Chronik bleibt erhalten.

## Verbindlicher Produktvertrag

- Produktname: `HK NPU STUDIO`
- Executable: `HKNPUStudio.exe`
- Distribution: `dist/HKNPUStudio/`
- Installer: `HKNPUStudio-<Version>-ARM64-Setup.exe`
- Benutzerdaten: `%LOCALAPPDATA%\HK NPU STUDIO\`
- Logdatei: `hk_npu_studio.log`
- User-Agent: `HKNPUStudio/<Version>`
- Claim: `Your Hardware • Your AI • Your Control`
- Unterzeile: `Local AI for Snapdragon® PCs`
- Feature-Badge: `Featuring Phoenix Boost`
- Phoenix-/Chip-Bildmarke bleibt bestehen.

## Rebranding – Git-Stand

Der Rebranding-Commit wurde erstellt und gepusht:

`86c42cec Rebrand application as HK NPU STUDIO`

Bestätigt:

- `main = origin/main = 86c42cec`
- 38 Dateien im Commit
- keine pauschale Staging-Aktion
- bekannte untracked Dateien blieben unangetastet

Später wurde der öffentliche GitHub-Slug auf `Kreuzhofen/hk-npu-studio` umbenannt. Frühere Handover-Stellen, die noch `Kreuzhofen/snapdragon-ai-studio` als aktuellen Slug nennen, sind historisch und überholt.

## HK-NPU-STUDIO-Frozen-Build und Installer

Der neue Frozen-Build wurde erfolgreich erzeugt unter:

`C:\SnapdragonAI\dist\HKNPUStudio\HKNPUStudio.exe`

Windows-Version-Informationen wurden auf `HK NPU STUDIO` umgestellt.

RealESRGAN-Modell im Frozen-Staging:

- Datei: `real_esrgan_x4plus.bin`
- Größe: `38,744,064 Bytes`
- SHA-256: `AB62398BF9CA61209E4DAB5EB5776F032760B777A759663CD67C14CFFF12E525`

Aktueller Installer-Kandidat:

`C:\SnapdragonAI\dist\installer\HKNPUStudio-2.0.0-rc.2b-ARM64-Setup.exe`

SHA-256:

`8CBAACD055B7CABFBEDBAF0756A31C8383AF5690A619F26D135DF795292EB459`

Der alte öffentliche RC2B-Installer wurde aus dem GitHub-Release entfernt; der historische Release/Tag blieb bestehen.

## RC2CleanTest – bestätigter HK-NPU-STUDIO-Installationsstand

Clean-Test-Benutzer:

`C:\Users\RC2CleanTest`

Vor sauberer Installation waren alte und neue App-/Programmpfade bereinigt. Die HK-NPU-STUDIO-Installation lief erfolgreich.

Bestätigt nach Installation:

- `HKNPUStudio.exe` vorhanden
- `%LOCALAPPDATA%\HK NPU STUDIO\` vorhanden
- ProductName: `HK NPU STUDIO`
- OriginalFilename: `HKNPUStudio.exe`

Für den zuletzt neu gebauten Installer mit SHA-256 `8CBAACD...EB459` blieb die finale manuelle Retest-Runde auf RC2CleanTest noch offen.

## QNN-Konsolenfenster-Fix

Ursache: `modules/qnn.py` startete `qnn-net-run.exe` pro Tile ohne `CREATE_NO_WINDOW`.

Minimalfix:

```python
subprocess.run(
    cmd,
    env=env,
    cwd=input_list.parent,
    check=True,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
```

Keine Tile-, Crop-, Overlap-, Stitching- oder sonstige Bildlogik wurde verändert.

Fokussierte Tests der RealESRGAN-QNN-Runtime bestanden; der manuelle Frozen-Test bestätigte anschließend, dass die störenden Konsolenfenster nicht mehr erscheinen.

## RealESRGAN 4× / WinError 32

Beim 4×-Upscaling trat auf RC2CleanTest beim finalen Rename kurzfristig `WinError 32` auf, weil die temporäre Datei noch durch Windows gesperrt war.

Minimalfix in `controllers/prompt_workspace_controller.py`:

- ausschließlich bei WinError 32 den finalen Rename mit kurzem Backoff mehrfach wiederholen;
- andere Fehler unverändert weiterwerfen;
- keine Bild-, Tile- oder Upscaling-Logik verändern.

Zugehöriger Regressionstest wurde ergänzt. `py_compile` und `git diff --check` bestanden. Der danach neu erzeugte Installer ist der oben dokumentierte Kandidat mit SHA-256 `8CBAACD...EB459`.

Noch offen: finale reale Bestätigung dieses letzten Retry-Builds auf RC2CleanTest mit 4×-Upscaling und vorhandener `_4x.png`.

## Generator-UI-Stabilität

Ursache des sichtbaren Layout-Sprungs während der Generierung: dynamisch wechselnde ein-/zweizeilige Phase-/Schritt-Anzeige änderte die Inspector-Höhe.

Korrektur in `widgets/phoenix/views/prompt_view.py`:

- Phase und Schritt reservieren dauerhaft stabile Grid-Zeilen.

Holger testete den Frozen-Build anschließend manuell und bestätigte: `stabil`.

## Header – eingefrorener Endstand

Final akzeptierter Wert:

`HEADER_TITLE_GROUP_UP_OFFSET = 5`

- linke Titelgruppe 5 logische Pixel nach oben
- rechter Release-Block unverändert
- Phoenix unverändert
- Headerhöhe unverändert

Holgers Abnahme: `passt`.

Header ohne neue ausdrückliche Anforderung nicht erneut verändern.

## Handover-Regel – verbindlich

Bei jeder zukünftigen Handover-Aktualisierung MUSS immer die vollständige bisherige Chronik plus alle neuen Ergänzungen in EINER Datei geliefert werden.

- niemals nur eine Ergänzungsdatei liefern;
- niemals ältere Chronik kürzen oder ersetzen;
- Download-Dateiname IMMER exakt: `CHATGPT_HANDOVER.md`;
- direkt für `C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd` geeignet.


# Ergänzung: Tagesabschluss 28. August 2026 – Online-Rebranding und Kommunikation

Diese Ergänzung führt die vollständige bisherige Chronik fort. Für öffentliche Markenflächen und den nächsten Einstieg hat dieser Abschnitt Vorrang vor älteren Portal-/Social-Media-Statusangaben.

## Arbeitsregeln – unverändert höchste Priorität

- Sprache: Deutsch.
- Token sparen ist oberstes Gebot.
- PowerShell bevorzugen; Antigravity wenn passend; Codex nur für echte notwendige Code-Sprints.
- Keine Builds, Commits oder Pushes ohne abgestimmten Schritt.
- Niemals `git add .`; untracked Dateien nicht beiläufig anfassen.
- Bei „weiter“ ohne unnötigen Zwischenstopp den nächsten sinnvollen Schritt liefern.

## Verbindliche öffentliche Marke

Produkt:

`HK NPU STUDIO`

Claim – in der öffentlichen Kommunikation bewusst in den Vordergrund stellen:

`Your Hardware • Your AI • Your Control`

Weitere verbindliche Bestandteile:

- `Local AI for Snapdragon® PCs`
- Phoenix bleibt Bild-/Projektidentität.
- `Phoenix Boost` bleibt Featurebezeichnung.
- `STUDIO` immer großschreiben.
- Freigegebenen HK-NPU-STUDIO-Banner nicht beiläufig verändern.

## GitHub – aktueller öffentlicher Slug

Verbindliche Repository-URL:

`https://github.com/Kreuzhofen/hk-npu-studio`

Alle neuen öffentlichen Links müssen diesen Slug verwenden.

## Hugging Face – aktualisiert

Space erfolgreich umbenannt:

`HolgKreu/snapdragon-ai-studio` → `HolgKreu/hk-npu-studio`

Durchgeführt:

- Space-Metadaten auf HK NPU STUDIO aktualisiert;
- Short Description: `Local AI for Snapdragon® PCs — HK NPU STUDIO`;
- Landingpage `index.html` auf das neue Branding umgestellt;
- neue GitHub-Links verwendet;
- Phoenix, Phoenix Boost, ControlNet Canny und RealESRGAN 2×/4× eingepflegt;
- alten Banner entfernt;
- neuen HK-NPU-STUDIO-Banner hochgeladen und live korrekt dargestellt;
- temporäres HF-Token nach der Repo-Umbenennung aus der PowerShell-Umgebung entfernt.

Status:

`HUGGING_FACE_AKTUALISIERT=True`

## Microsoft Tech Community – aktualisiert

Neuer HK-NPU-STUDIO-Updatebeitrag mit neuem Banner veröffentlicht.

Alte Beiträge wurden bewusst nicht gelöscht oder rückwirkend umgeschrieben; sie bleiben historische Projektchronik.

Status:

`MICROSOFT_TECH_COMMUNITY_AKTUALISIERT=True`

## Qualcomm Developers / Discord

Ein neuer HK-NPU-STUDIO-Updatepost wurde vorbereitet.

Regeln:

- alten Snapdragon-AI-Studio-Beitrag nicht löschen;
- neuen Banner verwenden;
- neuen GitHub-Link verwenden;
- Umbenennung sachlich und nicht defensiv erklären.

Im dokumentierten Stand ist die tatsächliche Veröffentlichung des neuen Discord-Posts noch nicht eindeutig bestätigt.

`QUALCOMM_DISCORD_VERÖFFENTLICHUNG_BESTÄTIGT=False`

## Reddit – finale Kommunikationslinie

Reddit bleibt besonders wichtig, weil dort ein großer Teil des praktischen positiven und kritischen Nutzerfeedbacks eingeht.

Der neue HK-NPU-STUDIO-Post soll persönlich, dankbar, ruhig und nicht defensiv wirken.

Bevorzugte Überschrift:

`🙏 Thank you for the feedback — Snapdragon AI Studio is now HK NPU STUDIO`

Namensänderung nicht als Rechtsdiskussion in den Vordergrund stellen. Bevorzugte Begründung sinngemäß:

`To avoid any possible confusion in the future between this independent project and official Snapdragon or Qualcomm software, I decided that now is the right time to give the project its own clear identity.`

Danach klar:

`Snapdragon AI Studio is now HK NPU STUDIO`

Claim deutlich hervorheben:

`Your Hardware • Your AI • Your Control`

Kernaussage:

- eigene Hardware;
- lokale KI;
- eigene Bilder und Workflows unter eigener Kontrolle.

Phoenix und Phoenix Boost bleiben.

RealESRGAN 4× nur als kurze technische Entwicklung erwähnen, nicht als Werbe-Hauptaufhänger:

- 2× und 4× NPU-Upscaling;
- Beispiel 512×512 → 2048×2048;
- lokaler QNN/NPU-Workflow;
- Originalbild separat erhalten.

Der Satz

`HK NPU STUDIO is an independent open-source project and is not an official Qualcomm product.`

soll auf Holgers ausdrücklichen Wunsch NICHT als abschließender Disclaimer unter diesem Social-Media-Post stehen. Stattdessen Claim in den Vordergrund stellen.

Zum Abschluss ausdrücklich für positives und kritisches Feedback danken. Alte Reddit-Posts und Kommentare nicht löschen.

`REDDIT_NEUER_HK_NPU_STUDIO_POST_BESTÄTIGT=False`

## Instagram / Facebook – Text vorbereitet

Instagram und Facebook werden gemeinsam bedient. Der Beitrag soll persönlicher und kürzer als Reddit sein.

Verbindliche Kernaussagen:

- großes Dankeschön an Tester und Unterstützer;
- Fehlermeldungen, Screenshots, Verbesserungsvorschläge und Meinungen wertschätzen;
- Namensänderung zur Vermeidung künftiger Verwechslungen mit offizieller Snapdragon-/Qualcomm-Software;
- `HK NPU STUDIO`;
- Claim stark hervorheben: `Your Hardware • Your AI • Your Control`;
- eigene Hardware, lokale KI, Bilder und Workflows unter eigener Kontrolle;
- Phoenix/Phoenix Boost bleiben;
- RealESRGAN-NPU-Upscaling 2× und 4× kurz erwähnen;
- positives und kritisches Feedback hilft bei der Weiterentwicklung.

Die Formulierung `I want to share something a little more personal` wurde auf Holgers Wunsch entfernt. Der Gesamttext wurde bewusst gekürzt und mit wenigen Icons aufgelockert.

`INSTAGRAM_FACEBOOK_POST_BESTÄTIGT=False`

## X – nächster Online-Schritt

Am 29. August 2026 soll noch X auf HK NPU STUDIO aktualisiert werden. Danach ist diese Runde der öffentlichen Rebranding-Aktualisierungen im Wesentlichen abgeschlossen.

Für X:

- deutlich kürzer als Reddit;
- `HK NPU STUDIO`;
- Claim `Your Hardware • Your AI • Your Control` klar hervorheben;
- Umbenennung knapp erklären;
- neuen GitHub-Slug verwenden;
- neuen Banner/passende Markenvisualisierung verwenden.

`X_AKTUALISIERT=False`

## Handbuch

Der aktuelle Handbuchtext ist inhaltlich vollständig.

Keinen neuen App-/Installer-Build ausschließlich wegen des Handbuchs erstellen.

Beim nächsten regulären Release muss der aktuelle Handbuchstand vor dem Frozen-Build in den Releaseprozess integriert werden.

## Technischer Release-Status bleibt separat offen

Die heutige Online-/Kommunikationsarbeit ist keine technische Release-Abnahme.

Zuletzt dokumentierter Installer:

`C:\SnapdragonAI\dist\installer\HKNPUStudio-2.0.0-rc.2b-ARM64-Setup.exe`

SHA-256:

`8CBAACD055B7CABFBEDBAF0756A31C8383AF5690A619F26D135DF795292EB459`

Auf RC2CleanTest weiterhin final prüfen:

1. RealESRGAN 4×;
2. kein WinError 32 beim finalen Rename;
3. finale `_4x.png` vorhanden;
4. keine QNN-Konsolenfenster;
5. Generator-UI stabil.

## Statusflags – Tagesabschluss 28. August 2026

```text
PRODUKTNAME=HK NPU STUDIO
CLAIM=Your Hardware • Your AI • Your Control
GITHUB_REPO=Kreuzhofen/hk-npu-studio
HUGGING_FACE_AKTUALISIERT=True
MICROSOFT_TECH_COMMUNITY_AKTUALISIERT=True
QUALCOMM_DISCORD_VERÖFFENTLICHUNG_BESTÄTIGT=False
REDDIT_NEUER_HK_NPU_STUDIO_POST_BESTÄTIGT=False
INSTAGRAM_FACEBOOK_POST_BESTÄTIGT=False
X_AKTUALISIERT=False
HANDBUCH_INHALT_VOLLSTÄNDIG=True
HANDBUCH_NEUBUILD_JETZT=False
RC2CLEAN_LATEST_INSTALLER_FINAL_BESTÄTIGT=False
```

## Nächste Schritte bei Wiederaufnahme

1. X auf `HK NPU STUDIO` aktualisieren.
2. Falls noch nicht bestätigt, Veröffentlichungsstatus von Reddit, Instagram/Facebook und Qualcomm Developers/Discord klären.
3. Danach Online-Rebranding-Runde als abgeschlossen dokumentieren.
4. Anschließend zum technischen Releasepfad zurückkehren.
5. Aktuellen Installer mit SHA-256 `8CBAACD055B7CABFBEDBAF0756A31C8383AF5690A619F26D135DF795292EB459` auf RC2CleanTest final validieren.
6. RealESRGAN 4× insbesondere auf WinError-32-Retry, `_4x.png` und unsichtbare QNN-Prozesse prüfen.
7. Erst danach weitere Git-/Release-Schritte kontrolliert planen.

## Verbindliche Handover-Regel

Bei jeder künftigen Aktualisierung immer die vollständige bisherige Chronik plus alle neuen Ergänzungen in einer einzigen Datei bereitstellen.

Download-Dateiname immer exakt:

`CHATGPT_HANDOVER.md`

Die Datei muss direkt für

`C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd`

geeignet sein. Niemals nur eine Ergänzungsdatei ausgeben.

# CHATGPT_HANDOVER – Ergänzung 29. August 2026

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die ältere Chronik bleibt vollständig erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsmodus / Werkzeuge

- Sprache weiterhin Deutsch.
- Tokenoptimiert arbeiten; PowerShell für klare Prüfungen, Codex für gezielte Codeänderungen.
- Antigravity steht ebenfalls zur Verfügung und kann für Dokumentation, Konsistenzprüfung oder größere, klar abgegrenzte Analyseaufgaben verwendet werden.
- Holger hat am 29. August wegen fast aufgebrauchter Codex-Tokens die Arbeiten beendet. Am nächsten Arbeitstag stehen wieder Codex-Tokens zur Verfügung.
- Keine Builds, Commits oder Pushes ohne den mit Holger abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien weiterhin nicht anfassen.
- Bei Tests Maschine und Modus nennen.
- Für produktive Pfade gilt nach Issue #1 ausdrücklich: „läuft auf dem Entwicklungs-PC“ ist kein ausreichender Portabilitätsnachweis.

## Verbindlicher Marken- und Projektstand

Produktname: `HK NPU STUDIO`  
Claim: `Your Hardware • Your AI • Your Control`  
Plattformtext: `Local AI for Snapdragon® PCs`  
Feature: `Featuring Phoenix Boost`

Phoenix-Bildmarke, Phoenix Engine und Phoenix Boost bleiben bestehen.

Repository: `https://github.com/Kreuzhofen/hk-npu-studio`  
Arbeitsrepository: `C:\SnapdragonAI`  
Branch: `main`

## Git-Stand / veröffentlichter Abschluss von Issue #1

Neuer Commit: `9dd0e96b Fix hardcoded paths and portable runtime resolution`

Commitumfang:

```text
28 files changed
981 insertions(+)
170 deletions(-)
tests/test_model_install_safety.py neu
```

Push am 29. August 2026 erfolgreich:

```text
b5962310..9dd0e96b  main -> main
```

Remote: `https://github.com/Kreuzhofen/hk-npu-studio.git`

Commit `9dd0e96b` ist auf `origin/main`.

Vor dem Commit:

```text
124 passed
2 skipped
25 subtests passed
py_compile erfolgreich
git diff --check erfolgreich
```

Zusätzlich erfolgte ein manueller direkter Python-App-Smoke-Test auf dem Entwicklungs-PC Holger. Die App lief. SD2.1-QNN wurde erfolgreich aus der GUI generiert.

## GitHub Issue #1 – abgeschlossen

Issue: `#1 [Issue] Hardcoded paths`  
Reporter: `taksheels`  
URL: `https://github.com/Kreuzhofen/hk-npu-studio/issues/1`  
Status: `closed / completed`

Abschluss erfolgte nach Push von Commit `9dd0e96b`.

Ein Abschlusskommentar wurde im Issue hinterlassen. Er enthält zusammengefasst:

- Verweis auf Commit `9dd0e96b`;
- Entfernung produktiver `C:\SnapdragonAI`-Annahmen;
- Entfernung fester QNN-SDK-Versionen aus aktiven Runtime-Pfaden;
- Nutzung dynamischer Modell-, Output-, Preset-, Log-, Temp- und Pluginpfade;
- Härtung destruktiver Modellinstallations-/Update-/Cleanup-Grenzen;
- Entfernung fester globaler Python-`site-packages`-Annahmen;
- portable QNN-DLC-Diagnosepfade;
- Erhalt echter Custom-Pfade;
- Hinweis, dass `start_gui.bat` bereits portabel war;
- Teststatus und manueller SD2.1-QNN-Smoke.

## Architektur-Lernen aus Issue #1

Für unser Projekt gilt künftig ausdrücklich:

1. Keine produktiven absoluten Maschinenpfade.
2. Modelle, Logs, Temp, Presets, Plugins, Output und Daten ausschließlich über zentrale Resolver/Konstanten.
3. SDKs und Python-Interpreter entdecken oder explizit konfigurieren; keine feste Installationsversion voraussetzen.
4. Dev und Frozen bei Pfadentscheidungen getrennt prüfen.
5. Echte Custom-Pfade des Nutzers niemals blind umschreiben oder löschen.
6. Bei Lösch-/Cleanup-Code positive Ownership-/Containment-Prüfung statt Blacklist.
7. Vor größeren Releases repo-weiten Hardcode-/Portabilitäts-Scan einplanen.
8. Unit-Tests durch realistische Fremdrechner-/Frozen-Smokes ergänzen.
9. Beim Entfernen eines Hardcodes gleichzeitig auf verdeckte Runtime-Abhängigkeiten prüfen.
10. Lokale Funktionalität nicht mit Release-Reife gleichsetzen.

## Issue #1 – wesentliche Fixbereiche

Im Verlauf von Issue #1 wurden unter anderem folgende produktive Bereiche portabel gemacht bzw. abgesichert:

- `config.py`
- `gui_v2.py`
- `engine/hardware_manager.py`
- `pages/dashboard.py`
- `engine/onnx_provider_service.py`
- `controllers/plugin_controller.py`
- `engine/controlnet_canny_backend.py`
- `engine/sd15_qnn_backend.py`
- `engine/sd21_qnn_backend.py`
- `engine/model_install_service.py`
- `tools/sd35_setup_helper.py`
- `app/configuration_manager.py`
- `app/preset_manager.py`
- `engine/onnx_image_backend.py`
- `engine/qnn_dlc_diagnostic_runner.py`
- `engine/qnn_dlc_runtime_service.py`
- zugehörige Safety-, Runtime-, Download- und Contract-Tests.

Nicht blockierende Resttreffer im finalen Scan:

- `app/model_scanner.py`: alte Fallback-Literale; produktiver Aufrufer übergibt bereits dynamisch `TEMP_DIR` und `MODELS_DIR`.
- `engine/qnn_execution_probe.py`: Diagnose-/CLI-Code ohne produktiven Aufrufer.
- `engine/experiments/tiled_sd21_qnn.py`: Experiment.
- `__pycache__`: kompilierte Altdateien, ignorieren.
- `run_realesrgan.py`: unreferenziertes Legacy-Skript, kein aktiver Produktpfad.
- `scripts/test_sd15_qnn_text_encoder.py`: Development-/Diagnoseskript.

## Model-Install-Safety nach Issue #1

`engine/model_install_service.py` wurde besonders vorsichtig gehärtet.

### Managed-Target-Vertrag

Neuer interner Vertrag sinngemäß: `_resolve_managed_model_target(model_id)`

- arbeitet ausschließlich mit dynamischem `MODELS_DIR`;
- blockiert leere, absolute und `..`-basierte Modell-IDs;
- verwendet `Path.resolve()` und echte Pfadgrenzen;
- Ziel muss echter Nachfahr von `MODELS_DIR` sein;
- `MODELS_DIR` selbst darf niemals Löschziel werden;
- Symlink-/Junction-Ausbrüche werden soweit robust erkennbar blockiert;
- kein `string.startswith()`;
- keine `C:\SnapdragonAI`-Sonderbehandlung.

### `uninstall_model()`

- physisches Löschen nur noch für exakt erwartete managed Ziele;
- Custom-Pfade bleiben physisch erhalten;
- Repository-/Registry-Status kann kontrolliert zurückgesetzt werden;
- historische Repo-Unterordner wie `C:\SnapdragonAI\docs` dürfen niemals durch einen gespeicherten Modellpfad gelöscht werden.

### `update_package()`

- Update, Backup, Swap, Rollback und Cleanup nur für verifiziertes `MODELS_DIR / model_id`;
- Custom-, historische, Eltern- und Geschwisterpfade werden abgewiesen;
- unsichere IDs werden vor Dateisystem-/Registry-Mutation blockiert;
- Backup- und Staging-Ziele müssen im managed Root bleiben;
- keine automatische Custom-Pfad-Migration.

### QAI-AppBuilder-Cleanup

`_safe_cleanup_qai_appbuilder_main()`:

- keine historischen `C:/SnapdragonAI`-Blacklists mehr;
- Cleanup ausschließlich unter dynamischem `TEMP_DIR`;
- nur konkreter Ordner `qai-appbuilder-main`;
- Root, externe Pfade, Eltern/Geschwister und Pfadausbrüche blockiert;
- Methode bleibt unbenutzt; sie wurde nicht neu produktiv eingebunden.

## SD3.5 Setup-Cleanup

`tools/sd35_setup_helper.py` wurde analog abgesichert.

`safe_cleanup_temp_dir()`:

- keine historischen `C:/`, `C:/SnapdragonAI`, `C:/SnapdragonAI/models`-Schutzlisten mehr;
- Cleanup nur für aufgelöste Nachfahren von `TEMP_DIR`;
- Root, externe Pfade, Eltern/Geschwister und Reparse-Point-Ausbrüche werden blockiert.

Tests: `40 passed, 1 skipped`; `py_compile` und `git diff --check` erfolgreich.

## ControlNet Canny und SD1.5

Aus `engine/controlnet_canny_backend.py` und `engine/sd15_qnn_backend.py` wurde die produktive importzeitige Annahme `C:\Program Files\Python311-arm64\Lib\site-packages` entfernt.

Bestehende Worker-Auflösung bleibt: Env-Override → app-eigene/Temp-venv → `sys.executable`.

Tests: `18 passed, 2 deselected, 7 subtests passed`. Zwei weitere Tests waren mangels externer Tokenizer-Testdaten nicht ausführbar.

## ConfigurationManager / PresetManager

Geändert: `app/configuration_manager.py`, `app/preset_manager.py`, `config.py`, zugehörige Tests.

Neue Pfadlogik:

- dynamischer `OUTPUT_DIR`;
- dynamischer `MODELS_DIR`;
- neuer `PRESETS_DIR = DATA_DIR / "presets"`;
- explizite Custom-Pfade bleiben unverändert;
- keine automatische Userdatenmigration in diesem Sprint.

Tests: `29 passed`; `py_compile` und `git diff --check` erfolgreich.

## ONNX Image Backend

`engine/onnx_image_backend.py`:

- Diagnosepfad jetzt unter `LOG_DIR / "diagnostics"`;
- Modellsuche über `MODELS_DIR`;
- App-Ressourcen separat über `BASE`;
- keine historischen `C:\SnapdragonAI`-Annahmen mehr.

Tests: `9 passed, 6 subtests passed`; `py_compile` und `git diff --check` erfolgreich.

## QNN-DLC Diagnose / Runtime

Letzte echten Issue-#1-Blocker waren `engine/qnn_dlc_diagnostic_runner.py` und `engine/qnn_dlc_runtime_service.py`.

Fix:

- dynamisches `BASE`;
- Modell über `MODELS_DIR`;
- Diagnosen unter `LOG_DIR / "diagnostics"`;
- bestehende QNN-Discovery unverändert;
- keine feste QAIRT-Version.

Tests: `17 passed`; `py_compile` und `git diff --check` erfolgreich.

Danach: `ISSUE_1_BLOCKER_REMAINING=False`.

## SD2.1 QNN – während Issue #1 sichtbar gewordene Runtime-Probleme

Während der Portabilitätsbereinigung wurden mehrere zuvor verdeckte SD2.1-Probleme sichtbar.

### Modellinstallation / vorhandener Download

Model: `stable_diffusion_v2_1_qnn`

Vollständiges Archiv:

`C:\SnapdragonAI\temp\downloads\stable_diffusion_v2_1-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite.zip`

Größe: `874929836 Bytes`

Der DownloadService meldete vorher trotzdem `file_exists`.

### DownloadService-Reuse-Fix

`engine/download_service.py` wurde so geändert, dass ein bereits vollständig vorhandener Download im managed Staging wiederverwendet werden kann.

Vertrag:

- nur reguläre Datei direkt im managed Download-Staging;
- bei erwartetem SHA-256 muss Hash exakt stimmen;
- ohne SHA und ohne Checksum-Pflicht wird remote `Content-Length` geprüft;
- lokale Datei muss nichtleer und exakt gleich groß sein;
- unbekannte oder falsche Größe bleibt Fehler;
- Dateien außerhalb managed Staging werden abgewiesen;
- `.part`-/Range-Verhalten bleibt unverändert.

Tests: `40 passed, 24 subtests passed`; `py_compile` und `git diff --check` erfolgreich.

Dieses Verhalten erklärte später auch, warum ControlNet Canny beim erneuten Installieren den Download übersprang: Das vollständige Archiv lag bereits im managed Staging.

ControlNet-Canny-Archiv:

`C:\SnapdragonAI\temp\downloads\controlnet_canny-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite.zip`

Größe: `951553032 Bytes`

Zeitstempel: `14.08.2026 18:19:44`

Das direkte Weitergehen zur Installation war beabsichtigtes Reuse-Verhalten, kein neuer Fehler.

## SD2.1 Worker – Pillow-/Importproblem

Produktiver Worker:

`C:\SnapdragonAI\temp\ort_qnn_245_test\venv\Scripts\python.exe`

Die Minimal-venv enthält bewusst nur `numpy`, `onnxruntime`, `onnxruntime-qnn`.

### Erster versteckter Importfehler

`engine/__init__.py` importierte vorher sofort `brand_manager`, das `PIL` benötigt. Dadurch scheiterte bereits `import engine.job_lifecycle`.

Fix:

- `BrandManager` und `BrandState` werden über `engine.__getattr__()` lazy geladen;
- `engine.__all__` bleibt kompatibel;
- `TYPE_CHECKING` stellt Typdefinitionen bereit;
- `from engine import BrandManager, BrandState` bleibt kompatibel;
- reine Engine-Submodule laden Branding/Pillow nicht mehr automatisch.

### Zweiter versteckter Pillow-Fehler

Nach dem Import-Fix lief der echte Worker vollständig bis `Saving image`, scheiterte dann aber mit `No module named 'PIL'`.

Ursache: Pillow wurde ausschließlich zum finalen PNG-Speichern benötigt.

### Finaler SD2.1-Bildexport-Fix

Geändert: `engine/sd21_qnn_backend.py`, `tests/test_qnn_worker_contract.py`.

Fix:

- dependencyfreier RGB-PNG-Writer mit NumPy und Python-Standardbibliothek (`struct`, `zlib`);
- bestehendes PNG-, Sidecar- und Metadatenformat bleibt erhalten;
- Frozen-Worker-Vertrag unverändert;
- Parent-/Worker-Command, Environment, Output-JSON, `image_path`, Success-Mapping und Cleanup getestet.

Zusätzlich korrigiert:

`MODEL_DIR = MODELS_DIR / "stable_diffusion_v2_1_qnn"`

statt `stable_diffusion_v2_1`.

Tests: `24 passed, 10 subtests passed`; `py_compile` und `git diff --check` erfolgreich.

### Echter Worker-Smoke

Input: `C:\SnapdragonAI\temp\sd21_qnn_runtime\job_input_1936ba9c.json`

Ergebnis:

```text
Exitcode=0
success=true
30/30 UNet-Schritte
VAE-Decoding auf HTP erfolgreich
PNG vorhanden
Sidecar vorhanden
PNG-Signatur gültig
Laufzeit ca. 31.37 s
```

Erzeugtes Bild: `C:\SnapdragonAI\output\generate_1788026234_1936ba9c.png`

Größe: `737612 Bytes`

Danach wurde SD2.1 erneut direkt aus HK NPU STUDIO gestartet und erfolgreich über die GUI generiert.

## Bedeutung der während Issue #1 sichtbar gewordenen Fehler

Die SD2.1-NPU-Pipeline war nicht grundsätzlich defekt. Die Portabilitätsbereinigung entfernte vorher zufällig funktionierende Entwicklungsrechner-Annahmen und machte verdeckte Abhängigkeiten sichtbar: Worker-Python-Umgebung, automatischer Branding-/Pillow-Import, Pillow-only PNG-Ausgabe, falscher SD2.1-Fallbackordner und bereits vorhandene Downloadarchive.

Lehre: Nach jeder Portabilitätsänderung die dadurch tatsächlich genutzte Runtime isoliert testen.

## Reddit – Rückmeldung am 29. August

Reddit-Nutzer `Raymanrush` schrieb: `Tolles Projekt, danke für deine Leidenschaft`.

Bevorzugte Reaktion: dankbar, kurz, persönlich. Reddit bleibt wichtig für positives und kritisches Anwenderfeedback.

## GitHub Reporter taksheels – Einordnung

`taksheels` eröffnete Issue #1 und Issue #2.

Issue #1 zeigte wahrscheinlich einen realen Lauf-/Ladefehler auf einem anderen Rechner; eine projektweite Suche nach `C:\SnapdragonAI` und der festen QAIRT-Version konnte die offensichtlichen Literale schnell sichtbar machen.

Einordnung:

- das Auffinden solcher Literale ist für einen erfahrenen Entwickler relativ schnell;
- die vollständige sichere Behebung war wesentlich aufwendiger;
- der Report war konstruktiv und technisch wertvoll;
- künftig repo-weite Portabilitätschecks frühzeitig selbst durchführen.

## GitHub Issue #2 – nächster technischer Schwerpunkt

Issue: `#2 [Issue] requirements.txt is missing nearly every runtime dependency`  
URL: `https://github.com/Kreuzhofen/hk-npu-studio/issues/2`  
Reporter: `taksheels`  
Status am Feierabend: `open`

Issue-Inhalt:

- `requirements.txt` enthält laut Report nur `numpy` und `pillow`;
- tatsächlich importiert werden unter anderem `onnxruntime`, `onnxruntime_qnn`, `qai_appbuilder`, `torch`, `transformers`, `diffusers`, `pyyaml`, `tkinterdnd2`;
- `pip install -r requirements.txt && python phoenix.py` könne daher nicht funktionieren;
- `tools/build_app.py` bricht laut Report ab, wenn `onnxruntime_qnn` fehlt.

### Einschätzung zu Issue #2

Voraussichtlich weniger aufwendig als Issue #1, aber NICHT blind alle Imports in eine Datei schreiben.

Erster Schritt morgen: **nur Analyse und Klassifizierung**.

Für jede Fremdbibliothek feststellen:

1. Haupt-App-Runtime-Abhängigkeit;
2. Build-Abhängigkeit;
3. optionales Feature;
4. isolierte Worker-Abhängigkeit;
5. Qualcomm-/SDK-externe Abhängigkeit;
6. Dev-/Test-Abhängigkeit.

Danach entscheiden, ob eine vollständige `requirements.txt`, getrennte Runtime-/Build-/Optional-Requirements oder eine andere klar dokumentierte Abhängigkeitsstruktur für unser Projekt richtig ist.

Besonders beachten:

- einige QNN-Worker laufen absichtlich in Minimal-venvs;
- `qai_appbuilder` / Qualcomm-Komponenten können nicht wie normale universelle PyPI-Abhängigkeiten behandelt werden;
- Issue #2 ist ein echtes Packaging-/Developer-Onboarding-Problem, falls ein frischer Clone nach `pip install -r requirements.txt` die App nicht starten kann.

Keine Implementierung vor dieser Analyse.

## Priorität bei Wiederaufnahme am 30. August 2026

1. Git-Status und `HEAD/origin/main` kurz prüfen.
2. Erwartet: Commit `9dd0e96b` ist auf `main` und `origin/main`.
3. Keine untracked/unrelated Dateien anfassen.
4. Issue #2 analysieren.
5. Codex steht wieder mit neuem Tokenbudget zur Verfügung.
6. Antigravity kann ergänzend verwendet werden, wenn eine größere Dependency-/Dokumentations-Konsistenzanalyse davon profitiert.
7. Erst nach Analyse einen kleinen, klar abgegrenzten Implementierungssprint definieren.
8. Danach fokussierte Tests und gegebenenfalls frischer Dev-Setup-Smoke.
9. GitHub Issue #2 erst schließen, wenn der dokumentierte Installationsweg real funktioniert oder der Issue-Vertrag nachvollziehbar korrigiert/dokumentiert wurde.

## Technischer Releasepfad – weiterhin separat

Issue #1 wurde gelöst und gepusht, das ersetzt keine vollständige neue Installer-/RC2CleanTest-Abnahme.

Zuletzt dokumentierter Installer weiterhin:

`C:\SnapdragonAI\dist\installer\HKNPUStudio-2.0.0-rc.2b-ARM64-Setup.exe`

SHA-256:

`8CBAACD055B7CABFBEDBAF0756A31C8383AF5690A619F26D135DF795292EB459`

Keine neue Build-/Installer-Freigabe am 29. August erfolgt.

## Statusflags – Feierabend 29. August 2026

```text
PRODUKTNAME=HK NPU STUDIO
GITHUB_REPO=Kreuzhofen/hk-npu-studio
ISSUE_1_HARDCODED_PATHS=COMPLETED
ISSUE_1_GITHUB_CLOSED=True
ISSUE_1_COMMIT=9dd0e96b
ISSUE_1_PUSHED=True
ISSUE_1_FINAL_TESTS=124_PASSED_2_SKIPPED_25_SUBTESTS
SD21_QNN_GUI_SMOKE=True
SD21_QNN_WORKER_SMOKE=True
DOWNLOAD_REUSE_VERTRAG_AKTIV=True
CONTROLNET_EXISTING_ARCHIVE_REUSED=True
ISSUE_2_REQUIREMENTS=OPEN
ISSUE_2_NEXT_STEP=ANALYSE_DEPENDENCY_CLASSIFICATION
CODEX_MORGEN_VERFÜGBAR=True
ANTIGRAVITY_VERFÜGBAR=True
BUILD_29_AUGUST=False
INSTALLER_29_AUGUST=False
PUSH_NACH_9DD0E96B=False
```

`PUSH_NACH_9DD0E96B=False` bedeutet: Nach dem erfolgreichen Push von `9dd0e96b` wurde kein weiterer Commit/Push vorgenommen.

## Verbindliche Handover-Regel

Diese Datei ist die vollständige zentrale Chronik.

Bei der nächsten Aktualisierung:

- ältere Inhalte nicht löschen;
- neuen Stand als weitere Ergänzung anhängen;
- bei widersprüchlichen alten Statuswerten hat der neueste Abschnitt Vorrang;
- Download-Dateiname immer exakt `CHATGPT_HANDOVER.md`;
- keine separate `ERGAENZUNG`-Datei ausgeben.

Holger übernimmt die Datei anschließend über:

`C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd`

nach:

`C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md`



# CHATGPT_HANDOVER – Ergänzung 30. August 2026

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Kommunikationsregeln – Ergänzung

- Sprache mit Holger weiterhin Deutsch.
- Bei englischsprachigen Antworten für GitHub, Reddit oder andere Plattformen immer direkt darunter eine deutsche Kontrollfassung für Holger liefern.
- Tageszeitbezogene Begrüßungen nur verwenden, wenn sie tatsächlich passen; unnötige Begrüßungen weglassen.
- Bei Handover-Aktualisierungen niemals eine neue verkürzte Datei aufbauen. Immer die bestehende vollständige Chronik 1:1 erhalten und ausschließlich unten ergänzen.
- Download-Dateiname bleibt exakt `CHATGPT_HANDOVER.md`.

## GitHub Issue #3 – Snapdragon X2 Elite

Am 30. August 2026 wurde auf GitHub direkt auf Issue #3 geantwortet.

Inhalt der Antwort:

- für das positive Feedback bedankt;
- erklärt, dass die in der Anwendung angezeigte Hardwarebezeichnung und der tatsächliche QNN/HTP-NPU-Pfad getrennte Dinge sind;
- nicht vorschnell behauptet, die X2-Unterstützung selbst sei defekt;
- um einen Screenshot der Hardwareinformationen in HK NPU STUDIO gebeten;
- um die genaue von Windows gemeldete Snapdragon-X2-Elite-Bezeichnung auf dem ASUS VivoBook S16 S3607Q gebeten;
- Ziel ist, die Hardware-Erkennungslogik gezielt anhand realer X2-Elite-Daten zu prüfen und gegebenenfalls zu ergänzen.

Status:

```text
GITHUB_ISSUE_3_X2_ELITE_REPLIED=True
GITHUB_ISSUE_3_WAITING_FOR_TESTER_DETAILS=True
```

## Phoenix Image Lab – SD3.5-Stand

Der bestehende experimentelle SD3.5-Inpainting-Pfad wurde technisch weiter untersucht und als Produktpfad für echtes Prompt-Inpainting kritisch neu bewertet.

### Experimenteller SD3.5-Pfad

Relevante Dateien:

```text
C:\SnapdragonAI\engine\experiments\sd35_inpainting_npu.py
C:\SnapdragonAI\engine\backends\sd35_inpainting_backend_adapter.py
C:\SnapdragonAI\tests\smoke_sd35_inpainting_npu.py
C:\SnapdragonAI\tests\test_sd35_inpainting_experimental.py
```

Lokaler SD3.5-VAE-Encoder:

```text
C:\SnapdragonAI\models\sd35_vae_cpu\vae
```

Bekannter Ablauf:

1. Tokenizer CPU
2. CLIP-L / CLIP-G Text Encoder QNN/HTP
3. CPU Embedding Processing
4. MM-DiT QNN/HTP
5. Decoder QNN/HTP
6. CPU Postprocessing / Softmask-Blend

Latentenkorrektur:

```text
(latent - 0.0609) * 1.5305
```

Maskenvertrag:

- Weiß = regenerieren
- Schwarz = bewahren
- Dilate 16 px
- Feather 24 px
- Gauß-Softmask
- Latentmaske 128×128

### 16-GB-RAM-Sequenz

Persistente QNN-Kontexte verursachten auf dem 16-GB-System starkes Paging und verlangsamten den CPU-VAE massiv.

Bewährte Sequenz:

```text
QNN Release → FP32 CPU-VAE → gc.collect() → QNN Reinit → HTP-Denoising
```

Gemessen etwa:

- QNN Release: ~1.7–1.9 s
- CPU-VAE: ~74–76 s
- QNN Reinit: ~16 s
- MM-DiT: ~32.4 s
- Decoder: ~1.2 s
- Gesamt: ~128 s

FP16-CPU-VAE wurde verworfen, da der Lauf auf ARM64 extrem langsam war und nach mehr als 12 Minuten nicht abgeschlossen hatte.

### Wichtige neue Erkenntnis: bisheriger SD3.5-Pfad ist kein echtes SD3-Inpainting

Die reale Diffusers-Architektur von `StableDiffusion3InpaintPipeline` verwendet für `hidden_states`:

- 16 Kanäle noisy latents
- 1 Kanal mask latent
- 16 Kanäle masked-image latents

zusammen:

```text
33 Kanäle
```

Der vorhandene Qualcomm-T2I-MM-DiT erwartet dagegen statisch:

```text
(1, 128, 128, 16)
```

Daraus folgt:

- das vorhandene 16-Kanal-T2I-Modell besitzt keine echte direkte Masken-/Masked-Image-Konditionierung;
- der bisherige Latent-Overwrite-/Blending-Pfad ist nur ein Heuristik-/PoC-Verfahren;
- dies erklärt die schlechte semantische Qualität im realen Test;
- der aktuelle 16-Kanal-Pfad darf nicht als echtes modernes „Generative Fill“ betrachtet oder vermarktet werden.

Phoenix Image Lab bleibt als Produktziel bestehen, aber die Backend-Architektur wird getrennt betrachtet.

## Phoenix Image Lab – UI-Zwischenstand

Bereits angelegte bzw. bearbeitete Komponenten:

```text
C:\SnapdragonAI\controllers\inpainting_controller.py
C:\SnapdragonAI\widgets\phoenix\inpainting_canvas.py
C:\SnapdragonAI\widgets\phoenix\views\inpainting_view.py
C:\SnapdragonAI\widgets\phoenix\workspace.py
C:\SnapdragonAI\widgets\phoenix\sidebar.py
C:\SnapdragonAI\tests\test_phoenix_inpainting_ui.py
```

GUI-Einstieg bleibt:

```text
C:\SnapdragonAI\gui_v2.py
```

Nicht `gui.py`.

Umgesetzt wurden unter anderem:

- Bild laden
- Prompt
- Steps
- Seed
- Brush / Eraser
- Brush Size
- Clear Mask
- Start / Cancel / Save
- Zoom / Pan
- native Maskenkoordinaten
- Seitenverhältnis korrekt erhalten
- Undo mit maximal 20 Maskenzuständen
- „Bild entfernen“ löscht nur den Sessionzustand, niemals die Quelldatei
- responsive Button-Anordnung
- PhoenixButton-Design

Später wurden sichtbare Buttons in mehreren Views auf PhoenixButton vereinheitlicht.

Zuletzt gemeldeter fokussierter UI-Teststand:

```text
78 tests passed
```

Der alte SD3.5-Heuristikpfad wird für weitere Produkt-UI-Arbeit vorerst nicht weitergetrieben, bis ein sinnvoller NPU-Backendpfad feststeht.

## Neue Strategie: LaMa-Dilated für Object Remove / Repair

LaMa-Dilated wurde als separater NPU-Pfad für folgende Phoenix-Image-Lab-Funktion ausgewählt:

```text
Object Remove / Repair
```

Wichtig:

- LaMa-Dilated ist kein Prompt-Modell.
- Es ersetzt kein echtes Prompt-Generative-Fill.
- Es eignet sich für Objektentfernung, Reparatur und strukturelles Hintergrundauffüllen.
- Prompt-geführtes Generative Fill bleibt ein eigener zukünftiger Backendpfad.

## Offizielles Qualcomm LaMa-Dilated-Modell

Lokaler Zielordner:

```text
C:\SnapdragonAI\models\lama_dilated
```

Heruntergeladenes Archiv:

```text
C:\SnapdragonAI\models\lama_dilated\lama_dilated-qnn_dlc-float.zip
```

SHA-256:

```text
E4CAF84495F6BB9E3E8EA6BAE069B28A5ED79AEF222C62E3EC6F356EFFEAF7E8
```

ZIP-Inhalt:

```text
lama_dilated-qnn_dlc-float/metadata.json
lama_dilated-qnn_dlc-float/lama_dilated.dlc
```

Entpacktes Modell:

```text
C:\SnapdragonAI\models\lama_dilated\lama_dilated-qnn_dlc-float\lama_dilated.dlc
```

Größe:

```text
182881612 Bytes
```

Metadata:

```text
C:\SnapdragonAI\models\lama_dilated\lama_dilated-qnn_dlc-float\metadata.json
```

## LaMa-Dilated Tensorvertrag aus metadata.json

Runtime:

```text
qnn_dlc
```

Precision:

```text
float
```

Build-QAIRT:

```text
2.45.0.260326154327
```

Tatsächliche Inputreihenfolge:

1. `mask`
   - Shape: `(1, 512, 512, 1)`
   - dtype: `float32`

2. `image`
   - Shape: `(1, 512, 512, 3)`
   - dtype: `float32`
   - Wertebereich: `[0.0, 1.0]`

Output:

`painted_image`

- Shape: `(1, 512, 512, 3)`
- dtype: `float32`
- Wertebereich: `[0.0, 1.0]`

Wichtiger Aufrufvertrag:

```python
model.Inference([mask, image])
```

Nicht:

```python
model.Inference([image, mask])
```

## Lokale Qualcomm-/QAI-Umgebung

Installierte AIStack-Version:

```text
C:\Qualcomm\AIStack\2.47.0.260601
```

Bestätigte ARM64-Libraries:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnSystem.dll
```

`qai_appbuilder` ist im `sd35_venv` importierbar.

Im realen Smoke meldete das Python-Paket:

```text
LibAppBuilder build version: v2.48.40.260702
Backend build version: v2.48.40.260702151143
```

Die ältere QAIRT-2.45-DLC konnte erfolgreich mit dieser Runtime geladen werden.

## LaMa-Dilated – echter QNN/HTP-Hardware-Smoke PASS

Maschine:

```text
Entwicklungs-PC Holger
```

Modus:

```text
direkter isolierter Python-Hardware-Smoke
```

Smoke-Datei:

```text
C:\SnapdragonAI\temp\smoke_lama_dilated_htp.py
```

Runtime:

```text
Runtime.HTP
```

### Erster Versuch

Beim ersten Versuch war die Inputreihenfolge falsch:

```python
model.Inference([image, mask])
```

Das Modell meldete jedoch:

```text
INPUT_NAMES= ['mask', 'image']
```

Daraufhin wurde exakt korrigiert auf:

```python
model.Inference([mask, image])
```

### Zweiter Versuch – vollständig erfolgreich

Eindeutige HTP-/NPU-Beweise:

```text
isGpu=0
isCpu=0
backEndPath=...\QnnHtp.dll
m_runInCpu=0
QnnContext_createFromBinary done successfully
QnnGraph_execute started
Graph ... execution finished with result 0
QnnGraph_execute done. status 0x0
QNN accelerator (execute) time
LAMA_HTP_SMOKE=PASS
```

Input-Shapes:

```text
mask  = [1, 512, 512, 1]
image = [1, 512, 512, 3]
```

Output:

```text
painted_image = [1, 512, 512, 3]
dtype = float32
```

Gemessene Zeiten:

```text
MODEL_LOAD_SECONDS=0.369
INFERENCE_SECONDS=0.096803
QAI model_inference=96.16 ms
QNN accelerator execute=87.463 ms
Accelerator execute=87.396 ms
Accelerator excluding wait=85.575 ms
```

Outputwerte:

```text
OUTPUT_MIN=0.4643554985523224
OUTPUT_MAX=0.5439453721046448
OUTPUT_MEAN=0.5001910328865051
```

Final:

```text
LAMA_HTP_SMOKE=PASS
```

Damit ist lokal technisch nachgewiesen:

```text
LaMa-Dilated läuft auf dem Snapdragon über QNN/HTP-NPU.
```

### Teardown-Warnung

Nach erfolgreicher Inferenz erschien beim finalen Backend-/Queue-Abbau:

```text
Error 0x200: failed to close queue ...
```

Dies ist nach aktuellem Nachweis kein Inferenzfehler, weil:

- Graph-Ausführung vorher `status 0x0`;
- Output vollständig vorhanden;
- `LAMA_HTP_SMOKE=PASS`;
- QNN-Context zuvor erfolgreich freigegeben.

Nicht ohne neue Evidenz als Produktblocker behandeln.

## Nächster technischer Schritt am 31. August 2026

Noch keine GUI-Integration.

Zuerst ein echter visueller Realbild-Smoke:

1. echtes Foto laden;
2. korrekt auf 512×512 vorbereiten;
3. echte weiße Objektmaske erzeugen;
4. Bild und Maske als float32 NHWC `[0,1]`;
5. Inputreihenfolge `[mask, image]`;
6. LaMa-Dilated ausschließlich über `Runtime.HTP`;
7. Output als PNG speichern;
8. Original, Maske und Ergebnis visuell vergleichen;
9. reale Inferenzzeit protokollieren;
10. bestätigen, dass die neuronale Inferenz auf QNN/HTP bleibt.

Erst bei überzeugender Qualität:

- Backend-Adapter planen;
- Controller anbinden;
- bestehende Phoenix-Image-Lab-Maske wiederverwenden;
- UI-Modus `Object Remove / Repair` integrieren.

Prompt-Feld darf bei LaMa nicht als Modellinput verwendet werden.

## Statusflags – Feierabend 30. August 2026

```text
PRODUKTNAME=HK NPU STUDIO

SD35_EXPERIMENTAL_INPAINTING_POC=True
SD35_16CH_TRUE_INPAINTING=False
SD35_TRUE_INPAINT_REQUIRES_33CH=True
SD35_16CH_UI_PRODUCT_FROZEN=True

LAMA_DILATED_MODEL_DOWNLOADED=True
LAMA_DILATED_SHA256_VERIFIED=True
LAMA_DILATED_DLC_EXTRACTED=True
LAMA_DILATED_METADATA_VERIFIED=True
LAMA_INPUT_ORDER=mask,image
LAMA_RUNTIME=QNN_HTP
LAMA_HTP_REAL_INFERENCE=True
LAMA_HTP_SMOKE_PASS=True
LAMA_HTP_PYTHON_INFERENCE_MS=96.803
LAMA_HTP_ACCELERATOR_MS=87.396
LAMA_REAL_IMAGE_VISUAL_SMOKE=False
LAMA_PRODUCT_INTEGRATION=False

GITHUB_ISSUE_3_X2_ELITE_REPLIED=True
GITHUB_ISSUE_3_WAITING_FOR_TESTER_DETAILS=True

BUILD_30_AUGUST=False
GIT_ADD_30_AUGUST=False
COMMIT_30_AUGUST=False
PUSH_30_AUGUST=False

NEXT_SESSION=LAMA_REAL_IMAGE_OBJECT_REMOVE_HTP_SMOKE
```

## Feierabend 30. August 2026

Für heute keine weiteren Änderungen, Builds, Commits oder Pushes.

Morgen direkt weiter mit:

```text
echtes Bild → echte Maske → LaMa-Dilated → QNN/HTP → PNG → visuelle Qualitätsbewertung
```

## Handover-Übernahme

Diese vollständige, nur ergänzte Datei als

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals durch eine verkürzte oder neu aufgebaute Handover ersetzt werden.

# CHATGPT_HANDOVER – Ergänzung 31. August 2026

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsmodus / Tagesabschluss

- Sprache weiterhin Deutsch.
- Tokenoptimiert arbeiten.
- PowerShell für klare lokale Prüfungen.
- Codex für größere, klar abgegrenzte technische Sprints, wenn manuelle Kleinschritte ineffizient werden.
- Keine Builds, Commits oder Pushes ohne abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien weiterhin nicht beiläufig anfassen.
- Bei Feierabend die vollständige Handover-Datei nur ergänzen, nie kürzen.

## Phoenix Image Lab – Qualitätsentscheidung

LaMa-Dilated und AOT-GAN wurden visuell als nicht produktreif eingestuft. LaMa zeigte Ghosting, Reststrukturen und Farb-/Texturabweichungen; AOT-GAN halluzinierte beim Innenwand-Test gesichts-/augenartige Strukturen. Beide Pfade bleiben technisch interessant, werden aber nicht als produktreifer Phoenix-Image-Lab-Object-Remove-Pfad integriert.

```text
LAMA_PRODUCT_QUALITY=NO_GO
AOT_GAN_PRODUCT_QUALITY=NO_GO
```

## Echtes Generative Fill – Architekturentscheidung

Für SD3/SD3.5 wurde der echte Inpainting-Vertrag bestätigt:

```text
16 noisy latents + 1 mask + 16 masked-image latents = 33 channels
```

Der vorhandene Qualcomm-SD3.5-T2I-MM-DiT-Pfad hat nur 16 Kanäle und ist daher kein echtes SD3.5-Inpainting. Der Alimama-ControlNet-Inpainting-Pfad wurde wegen zusätzlichem ControlNet, 24 Residual-Outputs, Speicherbedarf und Load/Run/Release-Aufwand auf einem 16-GB-System aktuell als nicht produktviabel eingestuft.

## Neuer Primärpfad: Dedicated SDXL Inpainting 0.1

Ausgewählt wurde:

```text
diffusers/stable-diffusion-xl-1.0-inpainting-0.1
```

Nativer Inpainting-Vertrag:

```text
4 noisy latents + 1 mask + 4 masked-image latents = 9 input channels
```

Lokales Modell:

```text
C:\SnapdragonAI\models\sdxl_inpainting
```

Bestätigt:

```text
conv_in.weight = [320, 9, 3, 3]
UNET in_channels = 9
VAE latent_channels = 4
VAE scaling_factor = 0.13025
```

## Kaggle ONNX-Export

Der lokale ARM64-Export wurde wegen zu hohem RAM-Bedarf verworfen. Der Export wurde auf Kaggle T4 x2 durchgeführt. Nach Anpassung von `use_external_data_format=True` auf `external_data=True` und Installation von `onnxscript` war der Export erfolgreich.

Verifizierte Artefakte:

```text
sdxl_inpaint_unet.onnx
SHA256=A7660031B9DE51BF381860B9EF556850724B3790EF7804537F026BFF25FE0BA5
SIZE=12531226 Bytes

sdxl_inpaint_unet.onnx.data
SHA256=CE7728656C3903C5ED11DE438F39F612AF5A57B141112EA87C94AE43AD39FAE5
SIZE=5135990784 Bytes
```

Die Dateien wurden nach Download und Hash-Prüfung dauerhaft abgelegt unter:

```text
C:\SnapdragonAI\models\sdxl_inpainting_qnn_source
```

Dort liegen:

```text
sdxl_inpaint_unet.onnx
sdxl_inpaint_unet.onnx.data
SHA256SUMS.txt
```

Die Hashes wurden nach dem Umzug erneut exakt bestätigt. Das alte Transportarchiv unter `temp` wurde anschließend gezielt entfernt.

## Speicherbereinigung

Gezielt gelöscht wurde nach Ownership-/Referenzprüfung:

```text
C:\SnapdragonAI\models_RC2_TEST_HOLD\sdxl_base_backup
```

Größe: 25.87 GB. `MODELS_DIR` wurde real als `C:\SnapdragonAI\models` bestätigt; der Test-Hold-Ordner war nicht Git-getrackt. Danach waren 58.68 GB auf C: frei.

## ONNX-Modellvertrag

Audit-venv:

```text
C:\SnapdragonAI\temp\qnn_audit_venv
onnx 1.22.0
```

Verifizierter Vertrag:

```text
IR_VERSION=10
OPSET=ai.onnx:18
sample                FLOAT16 [1, 9, 128, 128]
timestep              FLOAT16 [1]
encoder_hidden_states FLOAT16 [1, 77, 2048]
text_embeds           FLOAT16 [1, 1280]
time_ids              FLOAT16 [1, 6]
out_sample            FLOAT16 [1, 4, 128, 128]
NODE_COUNT=4981
```

## QAI Hub / Qualcomm Workbench

Lokales Paket:

```text
qai_hub 0.54.0
QAI_HUB_AUTH=PASS
DEVICE_COUNT=79
```

Gefundene Zielgeräte:

```text
Snapdragon X Elite CRD
Snapdragon X Plus 8-Core CRD
Snapdragon X2 Elite CRD
```

Für den QNN-DLC-Smoke wurde `Snapdragon X Plus 8-Core CRD` gewählt.

Der erste Compile-Job `jp1jom47p` schlug nicht wegen QNN/HTP-Operatoren fehl, sondern weil beim Upload nur die `.onnx` und nicht die externe `.onnx.data`-Datei korrekt mit übertragen wurde.

## External-Data-Paket und Typkorrektur

Qualcomm-Paketordner:

```text
C:\SnapdragonAI\models\sdxl_inpainting_qnn_package.onnx
```

Zielinhalt:

```text
sdxl_inpaint_unet.onnx
sdxl_inpaint_unet.data
```

Die External-Data-Referenzen wurden von `sdxl_inpaint_unet.onnx.data` auf `sdxl_inpaint_unet.data` geändert.

```text
REFERENCES_CHANGED=1681
EXTERNAL_LOCATIONS_AFTER=['sdxl_inpaint_unet.data']
```

Der Full-Check fand anschließend einen echten Typkonflikt am `node_concat`: `text_embeds` war FP16, `view_1` FP32. Tracing zeigte den FP32-Pfad über `time_ids -> Cast(FLOAT) -> Sin/Cos -> Concat -> view_1`. Minimal wurde vor `node_concat` ein Cast `view_1 -> FLOAT16` eingefügt und die alte `value_info` für `concat` von FLOAT auf FLOAT16 korrigiert.

Final:

```text
ONNX_FULL_CHECK=PASS
```

## Codex-Sprint – Paket, Upload und Compile

Wegen des hohen manuellen Aufwands wurde der letzte External-Data-/QAI-Hub-Schritt an Codex übergeben. Abschluss:

```text
PACKAGE_OK=True
ONNX_FULL_CHECK=PASS
UPLOAD=True
MODEL_ID=mqej003ym
COMPILE_SUBMIT=True
JOB_ID=jgord9v1g
STATUS=CREATED
```

Zusätzlich bestätigt:

- Paket enthält exakt eine `.onnx` und eine `.data`;
- External-Data-Referenzen korrekt;
- Backup nach `temp\sdxl_inpainting_package_backup_20260831` verschoben, nicht gelöscht;
- Original-Source-Hashes bestätigt;
- Source-Modell nicht verändert;
- kein App-Build;
- kein Git-Eingriff.

Letzter Statuscheck vor Feierabend:

```text
STATUS=OPTIMIZING_MODEL
```

Der Job war zu diesem Zeitpunkt noch nicht abgeschlossen und nicht fehlgeschlagen.

## Verbindlicher nächster Schritt bei Wiederaufnahme

Zuerst ausschließlich den bestehenden Compile-Job prüfen. Keinen zweiten Compile-Job starten.

```powershell
Set-Location -LiteralPath 'C:\SnapdragonAI'

$script = @'
import qai_hub as hub

JOB_ID = "jgord9v1g"

client = hub.Client()
job = client.get_job(JOB_ID)
status = job.get_status()

print("STATUS=" + str(status.code))

if status.message:
    print("MESSAGE=" + str(status.message))
'@

$script | & 'C:\Program Files\Python311-arm64\python.exe' -
```

Wenn `SUCCESS`: QNN-DLC-Artefakt identifizieren, Größe/Typ dokumentieren und erst danach Context-Binary-/HTP-Hardware-Smoke planen. Noch keine Produktintegration.

Wenn `FAILED`: vollständige `MESSAGE` sichern, Ursache klassifizieren und keinen Blind-Retry starten.

## Statusflags – Feierabend 31. August 2026

```text
PRODUKTNAME=HK NPU STUDIO
LAMA_PRODUCT_QUALITY=NO_GO
AOT_GAN_PRODUCT_QUALITY=NO_GO
SD35_16CH_TRUE_INPAINTING=False
SD35_TRUE_INPAINT_REQUIRES_33CH=True
ALIMAMA_SD3_CONTROLNET_CURRENT_PRODUCT_PATH=NO_GO
SDXL_DEDICATED_INPAINTING_SELECTED=True
SDXL_INPAINT_NATIVE_CHANNELS=9
SDXL_INPAINT_LOCAL_MODEL_DOWNLOADED=True
SDXL_INPAINT_ONNX_EXPORT=True
SDXL_INPAINT_ONNX_HASHES_VERIFIED=True
SDXL_INPAINT_ONNX_FULL_CHECK=PASS
SDXL_QNN_SOURCE=C:\SnapdragonAI\models\sdxl_inpainting_qnn_source
SDXL_QNN_PACKAGE=C:\SnapdragonAI\models\sdxl_inpainting_qnn_package.onnx
QAI_HUB_AUTH=True
QAI_HUB_MODEL_ID=mqej003ym
QAI_HUB_COMPILE_JOB_ID=jgord9v1g
QAI_HUB_TARGET=Snapdragon X Plus 8-Core CRD
QAI_HUB_COMPILE_STATUS=OPTIMIZING_MODEL
QNN_DLC_COMPILE_FINAL_RESULT=PENDING
QNN_HTP_HARDWARE_SMOKE=False
PHOENIX_IMAGE_LAB_SDXL_PRODUCT_INTEGRATION=False
BUILD_31_AUGUST=False
GIT_ADD_31_AUGUST=False
COMMIT_31_AUGUST=False
PUSH_31_AUGUST=False
```

## Feierabend 31. August 2026

Für heute keine weiteren QAI-Hub-Jobs, Builds, Commits, Pushes oder Integrationsänderungen starten.

Morgen direkt bei `jgord9v1g` fortsetzen: Status prüfen, Ergebnis bewerten, dann erst den nächsten QNN/HTP-Schritt planen.

## Handover-Übernahme

Diese vollständige, nur ergänzte Datei als `CHATGPT_HANDOVER.md` herunterladen und anschließend ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.


# CHATGPT_HANDOVER – Ergänzung 1. September 2026 – SDXL-Inpainting 2-Graph-QNN, HTP-Smoke und VAE-Decoder

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Verbindliche Arbeits- und Werkzeugregel

- Sprache weiterhin Deutsch.
- Tokenverbrauch streng begrenzen.
- **Antigravity zuerst** für lange/breite technische Analyse, Upload-/Downloadabläufe, Runtime-Prüfungen, Logauswertung und explorative Arbeit verwenden.
- **Codex nur** für gezielte Implementierung oder klar abgegrenzte konkrete Code-Fixes einsetzen.
- Keine langen Codex-Sprints, wenn Antigravity die Aufgabe sinnvoll übernehmen kann.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig anfassen.
- Für Phoenix Image Lab gilt als harte Architekturvorgabe: **alle KI-Inferenzkomponenten müssen später über Qualcomm QNN/HTP/NPU laufen**.
- CPU ist nur für leichte Orchestrierung wie Scheduler-Steuerung, Tensorverkettung, Maskenlogik, Datei-I/O und UI zulässig.
- **Keine CPU-Modell-Inferenz und kein CPU-Fallback** für Textencoder, VAE oder Denoiser.

## QAI-Hub-Gesamtgraph – Ergebnis und Entscheidung

Der komplette SDXL-Inpainting-UNet war als monolithischer QNN-Graph über QAI Hub nicht erfolgreich kompilierbar. Mehrere Whole-Graph-Versuche endeten mit `Internal compiler error`.

Daraufhin wurde ein 2-Graph-Split des nativen 9-Kanal-SDXL-Inpainting-UNets erstellt.

Teilgraphen:

```text
C:\SnapdragonAI\temp\sdxl_inpainting_2graph_prototype\graph_a
C:\SnapdragonAI\temp\sdxl_inpainting_2graph_prototype\graph_b
```

Erster Split-Compile von Graph A scheiterte nicht am QNN-Compiler selbst, sondern an doppelten ONNX-Metadaten:

```text
Tensors {...} occur in value_info but also in model IO.
```

Die betroffenen Tensoren wurden ausschließlich aus `graph.value_info` entfernt, wenn sie zugleich Modell-Input oder -Output waren. Nodes, Inputs, Outputs, Initializer, Tensor-Shapes und External Data blieben unverändert.

Finale Validierung:

```text
GRAPH_A_FULL_CHECK=PASS
GRAPH_B_FULL_CHECK=PASS
GRAPH_A_IO_VALUE_INFO_CONFLICT_COUNT=0
GRAPH_B_IO_VALUE_INFO_CONFLICT_COUNT=0
```

## 2-Graph-QNN-Compile – beide Graphen SUCCESS

Graph A:

```text
MODEL_ID=mnlj19xem
JOB_ID=jgj7yro8g
STATUS=SUCCESS
```

Graph B:

```text
MODEL_ID=mqej3reym
JOB_ID=jgk406wwp
STATUS=SUCCESS
```

Final:

```text
SPLIT_QNN_COMPILE_RESULT=SUCCESS_BOTH_GRAPHS
```

Damit ist bestätigt, dass der 2-Graph-Split durch den Qualcomm-QNN-Compiler läuft. Ein weiterer Split ist aktuell nicht erforderlich.

## SDXL Split-QNN – echter lokaler HTP-Hardware-Smoke PASS

Heruntergeladene Artefakte:

```text
C:\SnapdragonAI\models\sdxl_inpainting_qnn_split\graph_a\graph_a.dlc
C:\SnapdragonAI\models\sdxl_inpainting_qnn_split\graph_b\graph_b.dlc
```

Echter lokaler Snapdragon-QNN/HTP-Smoke:

```text
GRAPH_A_HTP=PASS
GRAPH_A_TIME_MS=457285.681

CROSS_GRAPH_TENSOR_COUNT=10
CROSS_GRAPH_TRANSFER=PASS

GRAPH_B_HTP=PASS
GRAPH_B_TIME_MS=538723.664

FINAL_OUTPUT_SHAPE=[1,4,128,128]
FINAL_OUTPUT_DTYPE=float16
FINAL_OUTPUT_FINITE=True
FINAL_OUTPUT_MIN=-2.798828125
FINAL_OUTPUT_MAX=2.732421875
FINAL_OUTPUT_MEAN=0.0012988199

END_TO_END_SPLIT_QNN_HTP_SMOKE=PASS
BLOCKER=NONE
```

Bestätigt:

- Graph A läuft real auf QNN/HTP.
- 10 echte Cross-Graph-FP16-Tensoren werden korrekt an Graph B weitergereicht.
- Graph B läuft real auf QNN/HTP.
- Das finale `out_sample` ist gültig und vollständig finite.

Die sehr hohen Laufzeiten sind aktuell ein Performance-Thema, kein Funktions- oder Kompatibilitätsblocker.

## NPU-Komponentenstatus für vollständige SDXL-Inpainting-Pipeline

Antigravity prüfte vorhandene Modellartefakte und Wiederverwendbarkeit.

Ergebnis:

```text
CLIP_L_EXISTING_NPU=YES
CLIP_G_EXISTING_NPU=YES
VAE_ENCODER_EXISTING_NPU=NO
VAE_DECODER_EXISTING_NPU=NO
```

CLIP-L und CLIP-G können über bereits vorhandene HTP-Binaries unter folgendem Bereich wiederverwendet werden:

```text
C:\SnapdragonAI\models\stable_diffusion_v3_5_qai\serialized_binaries
```

Damit fehlten für die vollständige NPU-first-Pipeline primär:

1. SDXL VAE Decoder
2. SDXL VAE Encoder

Empfohlene Reihenfolge wurde bestätigt als:

```text
VAE_DECODER -> VAE_ENCODER -> CLIP_L -> CLIP_G
```

## SDXL VAE Decoder – Export PASS

Quelle:

```text
C:\SnapdragonAI\models\sdxl_inpainting\vae
```

Export:

```text
C:\SnapdragonAI\temp\sdxl_vae_decoder_export\sdxl_vae_decoder.onnx
```

Vertrag:

```text
INPUT:
latent_sample [1,4,128,128] float16

OUTPUT:
sample [1,3,1024,1024] float16
```

Validierung:

```text
VAE_DECODER_EXPORT=PASS
ONNX_FULL_CHECK=PASS
QNN_READY=YES
COMPILE_RECOMMENDED=YES
BLOCKER=NONE
```

## SDXL VAE Decoder – QNN Compile und HTP PASS

QAI Hub:

```text
VAE_DECODER_MODEL_ID=mqpj60zjq
VAE_DECODER_JOB_ID=jgzmy0o4p
VAE_DECODER_COMPILE=SUCCESS
```

Heruntergeladenes Artefakt:

```text
C:\SnapdragonAI\models\sdxl_inpainting_qnn\vae_decoder\job_jgzmy0o4p_optimized_dlc_mqkj84vkm.dlc
```

Echter lokaler HTP-Smoke:

```text
VAE_DECODER_HTP=PASS
VAE_DECODER_TIME_MS=233256.72
OUTPUT_SHAPE=[1,3,1024,1024]
OUTPUT_FINITE=True
OUTPUT_MIN=-0.5419921875
OUTPUT_MAX=0.6396484375
OUTPUT_MEAN=0.0668599084019661
BLOCKER=NONE
```

Damit ist der SDXL-VAE-Decoder als echter Qualcomm-QNN/HTP-NPU-Baustein bestätigt.

## Harte Zielarchitektur für Phoenix Image Lab

Für die spätere Produktintegration gilt verbindlich:

```text
CLIP-L       -> NPU/HTP
CLIP-G       -> NPU/HTP
VAE Encoder  -> NPU/HTP
UNet Graph A -> NPU/HTP
UNet Graph B -> NPU/HTP
VAE Decoder  -> NPU/HTP
```

CPU darf ausschließlich leichte Orchestrierungsaufgaben übernehmen:

- Scheduler-Steuerung
- Tensor-Verkettung
- Maskenaufbereitung
- Datei-I/O
- UI

Keine CPU-Modell-Inferenz als Zwischenlösung oder Fallback.

## GitHub Sponsors – Supportticket

Der GitHub-Sponsors-Status zeigte weiterhin `Pending`; das Profil ist eingereicht und wartet auf Freigabe durch GitHub Staff.

Ein Supportticket wurde erfolgreich erstellt:

```text
GitHub Sponsors profile pending approval (Billing and payments)
#4716865
Status: open
```

Kein zweites Ticket eröffnen; auf Antwort von GitHub warten.

## Nächster sicherer Schritt am 2. September 2026

**Nicht mit Codex starten. Antigravity verwenden.**

Ziel: SDXL-VAE-Encoder exportieren, validieren, genau einmal über QAI Hub kompilieren und lokal auf QNN/HTP testen.

Quelle:

```text
C:\SnapdragonAI\models\sdxl_inpainting\vae
```

Erwarteter Vertrag:

```text
INPUT:
sample [1,3,1024,1024] float16

OUTPUT:
latent_sample [1,4,128,128] float16
```

Vorgehen:

1. lokalen SDXL-VAE-Encoder identifizieren;
2. nur Encoder nach ONNX exportieren;
3. `onnx.checker.check_model(..., full_check=True)`;
4. External Data korrekt paketieren, falls vorhanden;
5. genau ein QAI-Hub-Upload;
6. genau ein FP16-QNN-DLC-Compile auf `Snapdragon X Plus 8-Core CRD`;
7. kein Retry und keine Alternativflags;
8. nur bei SUCCESS Artefakt nach `C:\SnapdragonAI\models\sdxl_inpainting_qnn\vae_encoder` herunterladen;
9. genau einen echten lokalen QNN/HTP-Smoke ausführen;
10. Output `[1,4,128,128]`, finite, min/max/mean prüfen;
11. kein CPU-Fallback;
12. kein Build/Installer/Git.

Wenn der VAE-Encoder ebenfalls `HTP=PASS` erreicht, ist der komplette Modellbestand für eine vollständig NPU-basierte SDXL-Inpainting-Pipeline vorhanden. Danach folgt zuerst ein **isolierter kompletter NPU-Pipeline-Smoke mit echtem Bild, echter Maske und Prompt**, erst anschließend die Integration in HK NPU STUDIO.

## Statusflags – Feierabend 1. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

SDXL_INPAINT_UNET_SPLIT_2_GRAPH=True
SDXL_GRAPH_A_QNN_COMPILE=SUCCESS
SDXL_GRAPH_B_QNN_COMPILE=SUCCESS
SDXL_GRAPH_A_HTP=PASS
SDXL_GRAPH_B_HTP=PASS
SDXL_CROSS_GRAPH_TRANSFER=PASS
SDXL_SPLIT_QNN_HTP_SMOKE=PASS

SDXL_CLIP_L_NPU_AVAILABLE=True
SDXL_CLIP_G_NPU_AVAILABLE=True

SDXL_VAE_DECODER_EXPORT=PASS
SDXL_VAE_DECODER_QNN_COMPILE=SUCCESS
SDXL_VAE_DECODER_HTP=PASS

SDXL_VAE_ENCODER_EXPORT=PENDING
SDXL_VAE_ENCODER_QNN_COMPILE=PENDING
SDXL_VAE_ENCODER_HTP=PENDING

FULL_SDXL_INPAINT_MODEL_PIPELINE_NPU_READY=False
PHOENIX_IMAGE_LAB_SDXL_PRODUCT_INTEGRATION=False

CPU_MODEL_INFERENCE_ALLOWED=False
NPU_MODEL_INFERENCE_REQUIRED=True

GITHUB_SPONSORS_TICKET=4716865
GITHUB_SPONSORS_STATUS=PENDING_SUPPORT_REVIEW

NEXT_SESSION=SDXL_VAE_ENCODER_NPU
PREFERRED_TOOL=ANTIGRAVITY
CODEX_ONLY_FOR_TARGETED_FIXES=True

BUILD_1_SEPTEMBER=False
INSTALLER_1_SEPTEMBER=False
GIT_ADD_1_SEPTEMBER=False
COMMIT_1_SEPTEMBER=False
PUSH_1_SEPTEMBER=False
```

## Feierabend 1. September 2026

Für heute keine weiteren Exporte, QAI-Hub-Jobs, Builds, Installer, Commits, Pushes oder Integrationsänderungen starten.

Morgen direkt mit dem SDXL-VAE-Encoder über Antigravity fortsetzen.

## Handover-Übernahme

Diese vollständige, nur ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.


# CHATGPT_HANDOVER – Ergänzung 2. September 2026

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Qualitätsregeln – erneut verbindlich bestätigt

- Sprache weiterhin Deutsch.
- Tokenverbrauch streng begrenzen.
- **Antigravity zuerst** für breite Analyse, längere Runtime-/Log-/Modellprüfungen, Upload-/Download- und NPU-Exploration.
- **Codex nur** für eng abgegrenzte Implementierungen und konkrete Code-Fixes.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern oder löschen.
- Bei Bildfunktionen ab jetzt strikt unterscheiden:
  - `TECH PASS` = Runtime/Verträge/Tests funktionieren.
  - `FUNCTION PASS` = die reale Nutzerfunktion erfüllt sichtbar ihren Zweck.
  - `PRODUCT PASS` = Funktion, Qualität, Performance und reale Hardware-Abnahme bestanden.
- Ein gültiges PNG oder grüne Unit-Tests sind **kein** visueller Qualitätsnachweis.
- Ein isolierter Smoke ist **kein** automatischer Performance-Nachweis für den echten Studio-Pfad.
- Fehlende Gates immer ausdrücklich als offen kennzeichnen.

## Lizenzwechsel – HK NPU STUDIO ist nicht mehr MIT/Open Source

Holger möchte HK NPU STUDIO später kommerziell vermarkten und nicht erlauben, dass Dritte den Quellcode für eigene Produkte oder Entwicklungen übernehmen.

Die bisherige MIT-Lizenz war mit diesem Ziel unvereinbar.

Neue Lizenz:

```text
HK NPU STUDIO EVALUATION LICENSE
Version 2.0
Copyright © 2026 Holger Kreuzhofen
All rights reserved.
```

Kernpunkte:

- persönliche Evaluation, Test und nicht-kommerzielle Beurteilung erlaubt;
- keine kommerzielle Nutzung ohne separate schriftliche Lizenz;
- keine Nutzung des Quellcodes als Basis für andere Produkte/Services;
- keine Weiterverteilung, Unterlizenzierung oder Vermietung;
- technisch notwendige Kopien und zwingende gesetzliche Rechte bleiben unberührt;
- Drittsoftware/-modelle behalten ihre eigenen Lizenzen;
- öffentlich sichtbarer Source Code bedeutet ausdrücklich **nicht Open Source**;
- GitHub-internes Anzeigen/Forken im Rahmen der GitHub Terms ist erlaubt, verleiht aber keine zusätzlichen Wiederverwendungs-/Kommerzialisierungsrechte.

Direkt auf GitHub `main` veröffentlichte Commits:

```text
52a4c0093c7a3e32b13892575528722e8091c2fa
669cd3610343d4a3ce5f3e01fce35e9f000aa06c
60dc8fd8360d8fbd2c1130102e0dd5993e59b860
```

README angepasst:

- MIT-Badge entfernt;
- `open-source` durch `source-available proprietary` ersetzt;
- FAQ/Project-Leadership/License-Abschnitt angepasst.

Wichtig:

- lokaler Stand unter `C:\SnapdragonAI` wurde danach nicht per `git fetch/pull` verifiziert;
- bei Wiederaufnahme zuerst lokalen HEAD, `origin/main` und Arbeitsbaum prüfen;
- frühere unter MIT veröffentlichte Versionen behalten grundsätzlich die damals gewährten Rechte;
- Drittanbieter-Komponenten/Modelle werden durch Holgers Lizenz nicht umgelizenziert.

## SDXL-Inpainting – vollständiger NPU-Baustein technisch abgeschlossen

VAE Encoder:

```text
VAE_ENCODER_EXPORT=SUCCESS
VAE_ENCODER_ONNX_FULL_CHECK=PASS
VAE_ENCODER_MODEL_ID=mnowz36gq
VAE_ENCODER_JOB_ID=j567mjqnp
VAE_ENCODER_COMPILE=SUCCESS
VAE_ENCODER_ARTIFACT=C:\SnapdragonAI\models\sdxl_inpainting_qnn\vae_encoder\job_j567mjqnp_optimized_dlc_mqv304z0m.dlc
VAE_ENCODER_HTP=PASS
VAE_ENCODER_TIME_MS=115589.65
OUTPUT_SHAPE=[1,4,128,128]
OUTPUT_FINITE=True
BLOCKER=NONE
```

Damit waren alle Modellblöcke auf NPU/HTP vorhanden:

```text
CLIP-L       -> NPU/HTP
CLIP-G       -> NPU/HTP
VAE Encoder  -> NPU/HTP
UNet Graph A -> NPU/HTP
UNet Graph B -> NPU/HTP
VAE Decoder  -> NPU/HTP
```

CPU blieb nur für Scheduler, Tensorübergaben, Masken-Preprocessing, Datei-I/O und UI vorgesehen.

## Context-Binaries – 61,91× Cold-Start-Speedup

DLC-Load war der Hauptengpass:

```text
GRAPH_A_LOAD_SECONDS=501.98
GRAPH_B_LOAD_SECONDS=495.28
VAE_ENCODER_LOAD_SECONDS=111.73
VAE_DECODER_LOAD_SECONDS=225.38
DLC_TOTAL_LOAD_SECONDS=1334.37
```

Nach QNN Context Binaries:

```text
GRAPH_A_CONTEXT_LOAD_SECONDS=10.37
GRAPH_A_EXEC_SECONDS=0.81
GRAPH_B_CONTEXT_LOAD_SECONDS=8.91
GRAPH_B_EXEC_SECONDS=1.03
VAE_ENCODER_CONTEXT_LOAD_SECONDS=0.81
VAE_ENCODER_EXEC_SECONDS=1.19
VAE_DECODER_CONTEXT_LOAD_SECONDS=1.46
VAE_DECODER_EXEC_SECONDS=2.23
CONTEXT_TOTAL_LOAD_SECONDS=21.55
LOAD_SPEEDUP_FACTOR=61.91x
OUTPUT_CONTRACTS_VALID=YES
BLOCKER=NONE
```

## Vollständiger NPU-only Context-E2E technisch PASS

```text
E2E_CONTEXT_SMOKE=SUCCESS
OUTPUT_SIZE=1024x1024
TOTAL_SECONDS=40.54
DENOISE_TOTAL_SECONDS=27.63
PEAK_RAM_GB=15.61
PAGING=YES
SEQUENTIAL_RESIDENCY=YES
CPU_MODEL_INFERENCE=NO
OUTPUT_VALID=YES
BLOCKER=NONE
```

## 16-GB-Prozessisolation

Exakte Paging-Messung ohne harte Graph-Prozessisolation:

```text
TOTAL_SECONDS=63.24
PEAK_RAM_GB=15.61
MIN_AVAILABLE_RAM_GB=0.00
PEAK_COMMIT_GB=32.74
PAGE_FAULT_DELTA=921168
PAGING_SEVERITY=HIGH
PAGING_TIME_PENALTY_SECONDS=45.12
MEMORY_RECOVERY_CONFIRMED=YES
PRODUCT_RISK_16GB=MODERATE
```

Graph A/B danach jeweils in eigenem Child-Prozess, vollständiger Prozess-Exit zwischen den Graphen:

```text
PROCESS_ISOLATION=SUCCESS
E2E_CONTEXT_SMOKE=SUCCESS
TOTAL_SECONDS=41.59
PEAK_RAM_AFTER_GB=15.20
MIN_AVAILABLE_RAM_GB=0.41
PEAK_COMMIT_AFTER_GB=31.83
PAGE_FAULT_DELTA=35027
PAGING_SEVERITY=MODERATE
GRAPH_A_CHILD_EXIT_CONFIRMED=YES
GRAPH_B_CHILD_EXIT_CONFIRMED=YES
CPU_MODEL_INFERENCE=NO
BLOCKER=NONE
```

Mit geöffnetem Studio:

```text
STUDIO_IDLE_RAM_GB=0.08
E2E_WITH_STUDIO_OPEN=SUCCESS
TOTAL_SECONDS=43.77
PEAK_RAM_GB=15.61
PAGE_FAULT_DELTA=36608
PAGING_SEVERITY=MODERATE
STUDIO_RESPONSIVE_DURING_RUN=YES
STUDIO_RESPONSIVE_AFTER_RUN=YES
CPU_MODEL_INFERENCE=NO
PRODUCT_GATE_16GB=PASS
BLOCKER=NONE
```

Spätere Korrektur: Dieses `PRODUCT_GATE_16GB=PASS` war nur ein technischer Performance-/Responsiveness-Gate und kein visueller Qualitäts-PASS.

## SDXL-Inpainting – Studio-Integration und reale Qualitätsabnahme

Codex integrierte zunächst:

```text
controllers/inpainting_controller.py
engine/backends/sdxl_inpainting_qnn_context_adapter.py
widgets/phoenix/views/inpainting_view.py
tests/test_sdxl_inpainting_qnn_context_adapter.py
```

Erster Teststand:

```text
26 passed
py_compile PASS
git diff --check PASS
```

Realer Studio-Test:

- fast 5 Minuten;
- Person nicht entfernt;
- starke Ghosting-/Deformationsartefakte;
- globale Bildqualität zunächst sichtbar degradiert.

Status:

```text
TECH PASS
FUNCTION FAIL
PRODUCT FAIL
```

Gefundene und korrigierte Implementierungsfehler:

1. Originalbild statt masked image VAE-encodiert.
2. finales Masken-Composite fehlte.
3. CFG fehlte.
4. später zusätzlich: inward Gaussian blur mischte Originalpixel in den Maskenkern zurück.

Fixes:

- echter 9ch-Vertrag;
- VAE scaling `0.13025`;
- CFG;
- masked_image korrekt;
- außerhalb der Maske bitgenau Original;
- Feathering nur Randzone;
- Maskenkern 0 % Originalpixel;
- mindestens 12 Steps unterstützt.

Teststände:

```text
31 passed
```

und später:

```text
12 passed
py_compile PASS
git diff --check PASS
MASK_CORE_ORIGINAL_BLEED=NO
OUTSIDE_MASK_BIT_EXACT=YES
FEATHER_EDGE_ONLY=YES
TWELVE_STEPS_SUPPORTED=YES
RESULT=PASS
```

Trotzdem blieb der echte visuelle Person-Removal-Test schlecht.

## Entscheidender Diffusers-vs-QNN-Vergleich

```text
DIFFUSERS_REFERENCE_SUCCESS=YES
DIFFUSERS_PERSON_REMOVED=NO
DIFFUSERS_BACKGROUND_PLAUSIBLE=NO
QNN_PERSON_REMOVED=NO

INPUT_TENSORS_MATCH=YES
TIMESTEPS_MATCH=YES
CFG_MATCH=YES
SCHEDULER_OUTPUTS_MATCH=YES
UNET_OUTPUTS_NUMERICALLY_COMPARABLE=YES
QUALITY_DIVERGENCE=MODEL
```

Zusätzlicher 40-Step-Referenztest:

```text
PREVIOUS_REFERENCE_STEPS=8
FORTY_STEP_REFERENCE_SUCCESS=NO
PERSON_REMOVED=NO
BACKGROUND_PLAUSIBLE=NO
GHOSTING=YES
MODEL_QUALITY_GATE=FAIL
MODEL_SUITABLE_FOR_PHOENIX_IMAGE_LAB=NO
```

Entscheidung:

```text
diffusers/stable-diffusion-xl-1.0-inpainting-0.1
```

wird als Personen-/Objektentferner für Phoenix Image Lab **verworfen**.

Die QNN-/HTP-Portierung war technisch weitgehend korrekt; das Basismodell selbst erfüllte den Produktanspruch nicht.

## Modellvergleich – RORem ausgewählt

Verglichen:

- RORem
- OSOR-SDXL
- PowerPaint

Antigravity-Empfehlung:

```text
RECOMMENDED_MODEL=RORem (Robust Object Remover - SDXL / RORem-4S)
```

RORem wurde wegen spezialisierter Object/Person-Removal-Qualität und hoher erwarteter Wiederverwendung der SDXL-Infrastruktur gewählt.

## Speicherbereinigung

Erste sichere Temp-Bereinigung:

```text
FREE_SPACE_BEFORE_GB=3.11
FREE_SPACE_AFTER_GB=38.13
FREED_GB=34.73
```

Danach gezielt verworfenen SDXL-Inpainting-UNet-Bestand entfernt:

```text
FREE_SPACE_BEFORE_GB=37.94
FREE_SPACE_AFTER_GB=68.73
FREED_GB=30.79
```

Entfernt:

```text
C:\SnapdragonAI\models\sdxl_inpainting\unet\diffusion_pytorch_model.safetensors
C:\SnapdragonAI\models\sdxl_inpainting\unet\diffusion_pytorch_model.fp16.safetensors
C:\SnapdragonAI\models\sdxl_inpainting_qnn_split\graph_a\graph_a.dlc
C:\SnapdragonAI\models\sdxl_inpainting_qnn_split\graph_b\graph_b.dlc
C:\SnapdragonAI\models\sdxl_inpainting_qnn_context\graph_a\graph_a.serialized.bin
C:\SnapdragonAI\models\sdxl_inpainting_qnn_context\graph_b\graph_b.serialized.bin
```

Geschützt/behalten:

- CLIP-L / CLIP-G;
- Tokenizer;
- Scheduler;
- SDXL VAE;
- VAE Encoder/Decoder DLCs und Context Binaries;
- andere produktive Modelle.

Flags:

```text
SDXL_UNET_CHECKPOINT_REMOVED=YES
SDXL_UNET_ONNX_REMOVED=YES
SDXL_UNET_DLC_REMOVED=YES
SDXL_UNET_CONTEXT_REMOVED=YES
CLIP_ASSETS_PROTECTED=YES
VAE_ASSETS_PROTECTED=YES
ROREM_REUSE_ASSETS_PROTECTED=YES
BLOCKER=NONE
```

## RORem – erster echter Qualitätsnachweis PASS

RORem-mixed wurde heruntergeladen und im Original-Referenzpfad getestet:

```text
ROREM_DOWNLOAD=SUCCESS
ROREM_REFERENCE_SUCCESS=YES
MODEL_VARIANT=RORem-mixed
PERSON_REMOVED=YES
BACKGROUND_PLAUSIBLE=YES
GHOSTING=NO
NEW_OBJECT_HALLUCINATION=NO
OUTSIDE_MASK_PRESERVED=YES
OUTPUT_PNG=C:\SnapdragonAI\temp\rorem_mixed_proof\rorem_mixed_result.png
QUALITY_GATE=PASS
BLOCKER=NONE
```

## RORem – 3-Fall-Qualitätsvalidierung PASS

```text
CASE_1_PERSON_REMOVE=PASS
CASE_1_TIME_SECONDS=5260.78
CASE_1_OUTPUT=C:\SnapdragonAI\temp\rorem_validation\case1_output.png

CASE_2_OBJECT_REMOVE=PASS
CASE_2_TIME_SECONDS=2286.60
CASE_2_OUTPUT=C:\SnapdragonAI\temp\rorem_validation\case2_output.png

CASE_3_HARD_BACKGROUND=PASS
CASE_3_TIME_SECONDS=2228.84
CASE_3_OUTPUT=C:\SnapdragonAI\temp\rorem_validation\case3_output.png

QUALITY_PASS_COUNT=3/3
PEAK_RAM_GB=14.59
ROREM_PRODUCT_QUALITY_GATE=PASS
BLOCKER=NONE
```

Interpretation:

- RORem-mixed besteht aktuell das visuelle Referenz-Qualitäts-Gate **3/3**.
- Die extrem langen Zeiten gehören zum Referenz-/Diffusers-Pfad und sind kein Zielwert für die spätere NPU-Version.
- Eine NPU-Portierung ist jetzt fachlich gerechtfertigt.

## Uncommitted SDXL-Inpainting-Integrationscode – wichtig

Mindestens folgende Dateien wurden während der verworfenen SDXL-Produktintegration geändert:

```text
controllers/inpainting_controller.py
engine/backends/sdxl_inpainting_qnn_context_adapter.py
widgets/phoenix/views/inpainting_view.py
tests/test_sdxl_inpainting_qnn_context_adapter.py
```

Nach dokumentiertem Stand:

- kein `git add`;
- kein Commit;
- kein Push;
- kein Build.

Diesen Diff bei Wiederaufnahme **nicht blind committen oder verwerfen**. Zuerst prüfen, welche generischen UI-/Masken-/Controllerteile für RORem wiederverwendbar sind.

## RORem – noch offene technische Schritte

Noch nicht durchgeführt:

- lokalen RORem-Modellpfad dokumentieren;
- 9ch-UNet verifizieren;
- Topologiekompatibilität mit bisherigem SDXL-Inpainting-QNN-Pfad verifizieren;
- CLIP-L/CLIP-G/VAE/Scheduler/Masken-Reuse technisch belegen;
- ONNX FP16 + External Data;
- 2-Graph-Split;
- QAI-Hub-Compile;
- QNN Context Binaries;
- lokaler HTP-Smoke;
- Studio-Integration.

Erst nach positiver Architekturprüfung:

```text
RORem UNet
-> ONNX FP16 External Data
-> 2-Graph-Split
-> QNN Compile
-> Context Binaries
-> HTP-Smoke
```

## Statusflags – Feierabend 2. September 2026

```text
PRODUKTNAME=HK NPU STUDIO
LIZENZ=HK_NPU_STUDIO_EVALUATION_LICENSE_V2
SOURCE_AVAILABLE_PROPRIETARY=True
OPEN_SOURCE=False
MIT_CURRENT=False

LICENSE_GITHUB_COMMIT=669cd3610343d4a3ce5f3e01fce35e9f000aa06c
README_LICENSE_GITHUB_COMMIT=60dc8fd8360d8fbd2c1130102e0dd5993e59b860

SDXL_VAE_ENCODER_QNN_COMPILE=SUCCESS
SDXL_VAE_ENCODER_HTP=PASS
SDXL_FULL_MODEL_NPU_COMPONENTS_AVAILABLE=True
SDXL_CONTEXT_BINARY_SPEEDUP=61.91x
SDXL_CONTEXT_E2E_TECH_PASS=True
SDXL_PROCESS_ISOLATION=True
SDXL_16GB_TECH_GATE=True

SDXL_VISUAL_FUNCTION_PASS=False
SDXL_PRODUCT_PASS=False
SDXL_MODEL_QUALITY_GATE=FAIL
SDXL_BASE_INPAINT_MODEL_REJECTED=True

SDXL_UNET_CHECKPOINT_REMOVED=True
SDXL_UNET_DLC_REMOVED=True
SDXL_UNET_CONTEXT_REMOVED=True
SDXL_SHARED_CLIP_VAE_PROTECTED=True
FREE_SPACE_AFTER_CLEANUP_GB=68.73

ROREM_DOWNLOADED=True
ROREM_VARIANT=RORem-mixed
ROREM_REFERENCE_QUALITY_PASS=True
ROREM_QUALITY_CASES_PASS=3/3
ROREM_NPU_PORT_STARTED=False
ROREM_STUDIO_INTEGRATION=False
ROREM_PRODUCT_PASS=False

BUILD_2_SEPTEMBER=False
INSTALLER_2_SEPTEMBER=False
GIT_ADD_2_SEPTEMBER=False
LOCAL_COMMIT_2_SEPTEMBER=False
LOCAL_PUSH_2_SEPTEMBER=False

NEXT_SESSION=ROREM_ARCHITECTURE_AND_ONNX_FEASIBILITY
PREFERRED_TOOL=ANTIGRAVITY
CODEX_ONLY_FOR_TARGETED_FIXES=True
```

## Nächster sicherer Schritt am 3. September 2026

1. Zuerst lokalen Git-Status und `HEAD/origin/main` prüfen.
2. Lizenz-/README-Commits wurden direkt über GitHub veröffentlicht; lokalen Sync-Stand verifizieren.
3. Uncommitted SDXL-Inpainting-Integrationsdiff nicht blind committen oder verwerfen.
4. Antigravity: RORem-mixed Architektur prüfen:
   - lokaler Modellpfad;
   - 9ch UNet;
   - SDXL-Topologiekompatibilität;
   - CLIP-/VAE-/Scheduler-/Masken-Reuse;
   - ONNX FP16 External Data Machbarkeit;
   - Wiederverwendung des bewährten 2-Graph-Splits.
5. Noch kein QAI-Hub-Compile, kein Build und kein Git-Schritt während dieser Analyse.
6. Nur bei bestätigter technischer Kompatibilität danach den RORem-UNet-Export starten.
7. Qualitätsregel beibehalten: NPU-TECH-PASS allein ist später kein FUNCTION-/PRODUCT-PASS.

## Feierabend 2. September 2026

Für heute keine weiteren Modell-Downloads, Exporte, Compiles, NPU-Smokes, Builds, Installer, Commits oder Pushes durchführen.

Morgen direkt mit der RORem-Architektur-/ONNX-Machbarkeitsprüfung über Antigravity fortsetzen.

## Handover-Übernahme

Diese vollständige, nur unten ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.
# CHATGPT_HANDOVER – Ergänzung 3. September 2026

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Qualitätsregeln – heute erneut bestätigt

- Sprache weiterhin Deutsch.
- Tokenverbrauch strikt begrenzen.
- PowerShell für klare lokale Checks; Antigravity für breite Analyse, Modell-/Export-/QAI-Hub-Arbeit; Codex nur für eng begrenzte Fixes.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig anfassen.
- Für alle KI-Kernfunktionen gilt weiterhin: Modellinferenz ausschließlich über Qualcomm QNN/HTP/NPU.
- CPU ist nur für leichte Orchestrierung, Scheduler, Tensorverkettung, Maskenlogik, Datei-I/O, UI und ähnliche Nicht-Modellarbeit zulässig.
- Qualitätsstufen weiterhin strikt unterscheiden:
  - `TECH PASS` = technische Verträge/Runtime/Compiler bestehen.
  - `FUNCTION PASS` = reale Funktion erfüllt sichtbar ihren Zweck.
  - `PRODUCT PASS` = Funktion, Qualität, Performance und reale Hardware-Abnahme bestehen.
- RORem-mixed besitzt bereits einen starken Referenz-Qualitätsnachweis 3/3, ist aber noch kein NPU-`PRODUCT PASS`.

## RORem – Architekturprüfung und lokale Modellverifikation

Lokaler Modellpfad:

```text
C:\SnapdragonAI\models\rorem_mixed\unet
```

Verifiziert:

```text
config.json
diffusion_pytorch_model.safetensors
```

Gewichtsdatei:

```text
SIZE=5135178560 Bytes
TENSORS=1680
DTYPE=F16
```

Architektur:

```text
UNet2DConditionModel
IN_CHANNELS=9
OUT_CHANNELS=4
CROSS_ATTENTION_DIM=2048
BLOCK_OUT_CHANNELS=[320, 640, 1280]
TRANSFORMER_LAYERS_PER_BLOCK=[1, 2, 10]
```

Wichtige Tensoren:

```text
conv_in.weight=[320,9,3,3]
conv_out.weight=[4,320,3,3]
```

Ergebnis:

- RORem-mixed entspricht topologisch dem zuvor verwendeten SDXL-Inpainting-9ch-UNet.
- CLIP-L, CLIP-G, SDXL-VAE, Scheduler, 9ch-Maskenvertrag und die 2-Graph-Split-Grundarchitektur sind grundsätzlich wiederverwendbar.
- Ein kompletter nativer RORem-FP16-CPU-Forward auf ARM64 wurde bereits früher >30 Minuten ausgeführt und beendet; diesen Test nicht wiederholen.

## Lokaler ARM64-ONNX-Exportversuch – bewusst abgebrochen

Antigravity startete einen kontrollierten lokalen Low-Memory-Export mit:

```text
C:\SnapdragonAI\temp\export_rorem_unet.py
```

Ziel:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_source\rorem_unet.onnx
```

Beobachtet nach längerer Laufzeit:

- Hauptprozess PID 32904, Launcher PID 52404;
- etwa 6.46 GB Private/Commit;
- TorchScript-Tracing auf ARM64 CPU;
- weiterhin keine fertigen ONNX-Ausgabedateien;
- Abschätzung für 2.57B Parameter: etwa 60–90 Minuten oder mehr.

Vorab gesetztes Hard-Limit: 28 Minuten.

Final:

```text
EXPORT=FAILED
ONNX_FULL_CHECK=PENDING
BLOCKER=ARM64_CPU_FP16_TORCHSCRIPT_TRACE_TOO_SLOW
```

Der Prozess wurde nach 28 Minuten gezielt beendet. Kein Blind-Retry.

Entscheidung:

- kein weiterer ARM64-CPU-Exportversuch;
- keine Weight-Injection-/FakeTensor-/Dynamo-Experimente;
- stattdessen derselbe bewährte Kaggle-T4-GPU-Exportpfad wie beim früheren SDXL-Inpainting.

## Kaggle – RORem UNet GPU-Export

Kaggle-Dataset:

```text
rorem-mixed-unet
```

Hochgeladen wurden ausschließlich:

```text
config.json
diffusion_pytorch_model.safetensors
```

Kaggle-GPU:

```text
CUDA_AVAILABLE=True
GPU=Tesla T4
PYTORCH=2.10.0+cu128
```

Vorhandene Pakete:

```text
ONNX=1.22.0
DIFFUSERS=0.37.1
SAFETENSORS=0.7.0
ONNXSCRIPT=0.7.1
```

Der eigentliche Export lief auf CUDA mit FP16 und dem nativen 9ch-Vertrag.

Bestätigter CUDA-Forward vor Export:

```text
sample=(1,9,128,128) float16 cuda:0
timestep=(1,) float16 cuda:0
encoder_hidden_states=(1,77,2048) float16 cuda:0
text_embeds=(1,1280) float16 cuda:0
time_ids=(1,6) float16 cuda:0

Forward Output=(1,4,128,128) float16 cuda:0
```

ONNX-Export:

```text
OPSET=18
IR_VERSION=8
NODE_COUNT=8383
```

Der Legacy-TorchScript-Exporter erzeugte zunächst 1488 einzelne External-Data-Dateien. Das Modell selbst war technisch gültig; die vielen Dateien waren nur unpraktisch für den weiteren Qualcomm-/QAI-Hub-Pfad.

## Kaggle – External Data konsolidiert

Die 1488 External-Data-Dateien wurden anschließend in genau eine gemeinsame Datei konsolidiert.

Finale Kaggle-Artefakte:

```text
/kaggle/working/rorem_unet_packed.onnx
/kaggle/working/rorem_unet.data
```

Größen:

```text
rorem_unet_packed.onnx = 2554867 Bytes
rorem_unet.data        = 5134956168 Bytes
```

External-Data-Vertrag:

```text
EXTERNAL_LOCATIONS=['rorem_unet.data']
```

Validierung:

```text
PACKED_ONNX_FULL_CHECK=PASS
RORem External-Data-Konsolidierung erfolgreich.
```

SHA-256:

```text
PACKED_ONNX_SHA256=0CC5DD871607A6264FB47C604CAB4748688468D398A04F86628D5929F2797177
PACKED_DATA_SHA256=C5DFB639B45DF4B712C266A33CF8DB18834658D9CE86EC1144A9DC0722B63EB3
```

Kaggle-Direktdownload der großen 5.13-GB-Datei war zeitweise unzuverlässig. Über den gespeicherten Notebook-/Active-Event-/Output-Weg konnte die Datei schließlich vollständig geladen werden. Eine doppelt heruntergeladene `.data`-Datei hatte denselben SHA-256-Wert.

## Lokaler Transfer – bitgenau bestätigt

Lokale Zielpfade:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_source\rorem_unet_packed.onnx
C:\SnapdragonAI\models\rorem_mixed_qnn_source\rorem_unet.data
```

Lokale Größen:

```text
ONNX_SIZE=2554867
DATA_SIZE=5134956168
```

Lokale SHA-256-Prüfung:

```text
ONNX_SHA256=0CC5DD871607A6264FB47C604CAB4748688468D398A04F86628D5929F2797177
DATA_SHA256=C5DFB639B45DF4B712C266A33CF8DB18834658D9CE86EC1144A9DC0722B63EB3
LOCAL_SHA256=PASS
LOCAL_EXTERNAL_DATA_REFERENCE=PASS
```

Hinweis:

- `C:\Program Files\Python311-arm64\python.exe` besitzt lokal kein `onnx`-Paket.
- Deshalb wurde **kein Paket installiert**.
- Der Kaggle-Full-Check war bereits erfolgreich; lokal wurde bitgenauer Transfer plus External-Data-Referenz geprüft.

## RORem – 2-Graph-Split erfolgreich

Antigravity identifizierte den bereits bewährten SDXL-Inpainting-2-Graph-Split und bestätigte die 1:1-Topologiekompatibilität.

Referenzen:

```text
docs\CHATGPT_HANDOVER.md – früherer SDXL-2-Graph-Split
sdxl_inpainting_qnn_context_adapter.py – CROSS_GRAPH_SHAPES
graph_a_info.json
graph_b_info.json
```

Splitter:

```text
C:\SnapdragonAI\tools\split_rorem_unet_onnx.py
```

Split:

### Graph A – Down + Mid

Enthält:

```text
time_proj
time_embedding
add_time_proj
add_embedding
conv_in
down_blocks.0
down_blocks.1
down_blocks.2
mid_block
```

Graph A Inputs:

```text
sample [1,9,128,128] FP16
timestep [1] FP16
encoder_hidden_states [1,77,2048] FP16
text_embeds [1,1280] FP16
time_ids [1,6] FP16
```

Graph A Outputs:

```text
10 Cross-Graph-Tensoren
```

### Graph B – Up + Output

Enthält:

```text
up_blocks.0
up_blocks.1
up_blocks.2
conv_norm_out
conv_out
```

Graph B Inputs:

```text
4 Conditioning-Inputs
10 Cross-Graph-Tensoren
```

Graph B Output:

```text
out_sample [1,4,128,128] FP16
```

### Cross-Graph-Tensoren

```text
1.  /unet/conv_in/Conv_output_0
    [1,320,128,128] FP16

2.  /unet/down_blocks.0/resnets.0/Div_output_0
    [1,320,128,128] FP16

3.  /unet/down_blocks.0/resnets.1/Div_output_0
    [1,320,128,128] FP16

4.  /unet/down_blocks.0/downsamplers.0/conv/Conv_output_0
    [1,320,64,64] FP16

5.  /unet/down_blocks.1/attentions.0/Add_output_0
    [1,640,64,64] FP16

6.  /unet/down_blocks.1/attentions.1/Add_output_0
    [1,640,64,64] FP16

7.  /unet/down_blocks.1/downsamplers.0/conv/Conv_output_0
    [1,640,32,32] FP16

8.  /unet/down_blocks.2/attentions.0/Add_output_0
    [1,1280,32,32] FP16

9.  /unet/down_blocks.2/attentions.1/Add_output_0
    [1,1280,32,32] FP16

10. /unet/mid_block/resnets.1/Div_output_0
    [1,1280,32,32] FP16
```

Erzeugte Teilgraphen:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_a\graph_a.onnx
C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_a\graph_a.data
C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_b\graph_b.onnx
C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_b\graph_b.data
```

Technische Werte:

```text
Graph A:
Nodes=4078
Initializers=808
full_check=True PASS

Graph B:
Nodes=4376
Initializers=880
full_check=True PASS
```

Zusätzlich:

```text
CROSS_GRAPH_TENSORS_MATCH=10/10
VALUE_INFO_CONFLICTS_GRAPH_A=0
VALUE_INFO_CONFLICTS_GRAPH_B=0
EXTERNAL_DATA_LOCAL_AND_CONSISTENT=YES
```

Final:

```text
TECH_PASS=YES
SPLIT_REUSE=YES
BLOCKER=NONE
```

## QAI Hub – RORem QNN-DLC Compile freigegeben und erfolgreich

Holger gab den QAI-Compile ausdrücklich frei.

Bewährter Referenzworkflow:

```text
QAI Hub Python SDK v0.55.0
C:\SnapdragonAI\sd35_venv\Scripts\python.exe
```

Zielgerät:

```text
Snapdragon X Plus 8-Core CRD
Chipset=qualcomm-snapdragon-x-plus-8-core / sc8340xp
Hexagon=v73
OS=Windows 11
```

Compile-Optionen:

```text
--target_runtime qnn_dlc --qnn_options default_graph_htp_precision=FLOAT16
```

Backend:

```text
Qualcomm QNN DLC / HTP FP16
```

### Graph A Compile

Vor Upload:

```text
graph_a.onnx=1651525 Bytes
graph_a.data=2486762880 Bytes
External Data=graph_a.data
full_check=True PASS
```

QAI Hub:

```text
MODEL_ID=mm66w726m
JOB_ID=jp2wq8l6p
STATUS=SUCCESS
```

Lokales DLC:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_a\graph_a.dlc
```

Größe:

```text
4975477996 Bytes
```

SHA-256:

```text
4aab49508c6fc7d481f908c8fb472692fbf3802cded80935ff0b81a07e180307
```

### Graph B Compile

Vor Upload:

```text
graph_b.onnx=1754950 Bytes
graph_b.data=2662785288 Bytes
External Data=graph_b.data
full_check=True PASS
```

Erster Job:

```text
JOB_ID=jp0j8qy9g
STATUS=FAILED
```

Exakte Ursache:

```text
Model input '/unet/down_blocks.0/resnets.0/Div_output_0' has dynamic shapes.
Please use a static shape.
```

Analyse:

- kein Größenfehler;
- kein HTP-Operatorfehler;
- im extrahierten Graph B waren an 9 intermediate Inputs symbolische Batch-Dimensionen (`unk__...`) verblieben.

Minimaler Fix:

- analog zum bewährten SDXL-Inpainting-Compile;
- statische FP16-Shapes für alle 14 Graph-B-Inputs über `input_specs`;
- bereits hochgeladenes QAI-Hub-Modell wiederverwendet;
- **kein erneuter 2.6-GB-Upload**.

Zweiter Job:

```text
MODEL_ID=mnlpx84jm
JOB_ID=jpyxkww85
STATUS=SUCCESS
```

Lokales DLC:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_b\graph_b.dlc
```

Größe:

```text
5327711148 Bytes
```

SHA-256:

```text
becfbaca891e6b0a89116eb25776d9776706cff8520304ae0c9db555c7166e07
```

## QAI Compile – verbindlicher Gesamtstatus

```text
TECH_PASS=YES
REFERENCE_WORKFLOW=SDXL Split-QNN via QAI Hub SDK v0.55.0
TARGET_DEVICE=Snapdragon X Plus 8-Core CRD
TARGET_BACKEND=Qualcomm QNN DLC (HTP FP16)
COMPILE_OPTIONS=--target_runtime qnn_dlc --qnn_options default_graph_htp_precision=FLOAT16

GRAPH_A_JOB_ID=jp2wq8l6p
GRAPH_A_STATUS=SUCCESS
GRAPH_A_ARTIFACT=C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_a\graph_a.dlc
GRAPH_A_SIZE=4975477996
GRAPH_A_SHA256=4aab49508c6fc7d481f908c8fb472692fbf3802cded80935ff0b81a07e180307

GRAPH_B_JOB_ID=jpyxkww85
GRAPH_B_STATUS=SUCCESS
GRAPH_B_ARTIFACT=C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_b\graph_b.dlc
GRAPH_B_SIZE=5327711148
GRAPH_B_SHA256=becfbaca891e6b0a89116eb25776d9776706cff8520304ae0c9db555c7166e07

CONTEXT_BINARY_CREATED=NO
LOCAL_HTP_SMOKE_RUN=NO
PRODUCT_INTEGRATION=NO
BLOCKER=NONE
```

Damit ist heute ausdrücklich **nicht** bewiesen:

```text
RORem lokale HTP-Ausführung
RORem Cross-Graph-Lauf auf echter NPU
RORem NPU-Visual-Quality
RORem FUNCTION PASS
RORem PRODUCT PASS
```

## Geänderte/erzeugte Dateien durch die heutige RORem-Arbeit

Neu bzw. erzeugt:

```text
C:\SnapdragonAI\tools\split_rorem_unet_onnx.py
C:\SnapdragonAI\tools\compile_rorem_qnn.py

C:\SnapdragonAI\models\rorem_mixed_qnn_source\rorem_unet_packed.onnx
C:\SnapdragonAI\models\rorem_mixed_qnn_source\rorem_unet.data

C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_a\graph_a.onnx
C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_a\graph_a.data
C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_b\graph_b.onnx
C:\SnapdragonAI\models\rorem_mixed_qnn_split\graph_b\graph_b.data

C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_a\graph_a.dlc
C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_b\graph_b.dlc
```

Mögliche temporäre Export-/Hilfsdateien aus der Antigravity-/Kaggle-Vorbereitung nicht pauschal bereinigen. Vor jedem Cleanup zuerst Ownership und Git-Status prüfen.

Es erfolgte heute:

```text
NO_BUILD=True
NO_INSTALLER=True
NO_GIT_ADD=True
NO_COMMIT=True
NO_PUSH=True
```

## Verbindlicher nächster Schritt

Nächste Freigabegrenze:

```text
Context Binary Build
```

Erst nach Holgers ausdrücklicher Freigabe:

1. aus `graph_a.dlc` und `graph_b.dlc` lokale QNN Context Binaries erzeugen;
2. denselben bereits bewährten Context-Binary-Pfad wie beim SDXL-Inpainting verwenden;
3. keine bestehenden SDXL-Artefakte überschreiben;
4. Größen und SHA-256 dokumentieren;
5. danach lokaler echter QNN/HTP-Smoke:
   - Graph A HTP;
   - 10 Cross-Graph-Tensoren;
   - Graph B HTP;
   - `out_sample [1,4,128,128] FP16`;
   - finite Werte;
6. erst nach diesem TECH PASS einen echten RORem-NPU-Bildtest mit realem Bild und echter Maske durchführen;
7. Referenzqualität 3/3 bleibt Vergleichsmaßstab;
8. erst nach überzeugender NPU-Visual-Quality `FUNCTION PASS`/`PRODUCT PASS` diskutieren;
9. Produktintegration in Phoenix Image Lab weiterhin erst danach.

## Statusflags – Tagesabschluss 3. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

ROREM_VARIANT=RORem-mixed
ROREM_REFERENCE_QUALITY_PASS=True
ROREM_REFERENCE_QUALITY_CASES=3/3

ROREM_ARCHITECTURE_VERIFIED=True
ROREM_NATIVE_IN_CHANNELS=9
ROREM_OUT_CHANNELS=4
ROREM_CROSS_ATTENTION_DIM=2048
ROREM_TOPOLOGY_MATCHES_SDXL_INPAINT=True

ROREM_LOCAL_ARM64_ONNX_EXPORT=ABORTED_TOO_SLOW
ROREM_KAGGLE_T4_EXPORT=SUCCESS
ROREM_PACKED_ONNX_FULL_CHECK=PASS
ROREM_PACKED_ONNX_SHA256=0CC5DD871607A6264FB47C604CAB4748688468D398A04F86628D5929F2797177
ROREM_PACKED_DATA_SHA256=C5DFB639B45DF4B712C266A33CF8DB18834658D9CE86EC1144A9DC0722B63EB3
ROREM_LOCAL_TRANSFER_SHA256=PASS

ROREM_2GRAPH_SPLIT=True
ROREM_SPLIT_REUSE=YES
ROREM_GRAPH_A_FULL_CHECK=PASS
ROREM_GRAPH_B_FULL_CHECK=PASS
ROREM_CROSS_GRAPH_TENSORS=10
ROREM_VALUE_INFO_CONFLICTS=0

ROREM_GRAPH_A_QAI_JOB=jp2wq8l6p
ROREM_GRAPH_A_QNN_COMPILE=SUCCESS
ROREM_GRAPH_A_DLC=C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_a\graph_a.dlc

ROREM_GRAPH_B_FIRST_QAI_JOB=jp0j8qy9g
ROREM_GRAPH_B_FIRST_COMPILE=FAILED_DYNAMIC_SHAPES
ROREM_GRAPH_B_QAI_JOB=jpyxkww85
ROREM_GRAPH_B_QNN_COMPILE=SUCCESS
ROREM_GRAPH_B_DLC=C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_b\graph_b.dlc

ROREM_QNN_COMPILE_TECH_PASS=True
ROREM_CONTEXT_BINARY_CREATED=False
ROREM_LOCAL_HTP_SMOKE=False
ROREM_NPU_VISUAL_FUNCTION_PASS=False
ROREM_PRODUCT_PASS=False
ROREM_STUDIO_INTEGRATION=False

BUILD_3_SEPTEMBER=False
INSTALLER_3_SEPTEMBER=False
GIT_ADD_3_SEPTEMBER=False
COMMIT_3_SEPTEMBER=False
PUSH_3_SEPTEMBER=False

NEXT_SESSION=ROREM_CONTEXT_BINARY_BUILD
NEXT_GATE=HOLGER_EXPLICIT_CONTEXT_BINARY_BUILD_APPROVAL
PREFERRED_TOOL=ANTIGRAVITY
CODEX_ONLY_FOR_TARGETED_FIXES=True
```

## Handover-Übernahme

Diese vollständige, nur unten ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.

# CHATGPT_HANDOVER – Ergänzung 4. September 2026 – RORem Contexts, echter HTP-/NPU-Bildtest, Qualitätsdiagnose und PC-Absturz

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsmodus / wichtige Regeln

- Sprache weiterhin Deutsch.
- Tokenverbrauch streng begrenzen.
- PowerShell für klar begrenzte lokale Prüfungen.
- Antigravity für breite Analyse, Modell-/Runtime-/Log-/QAI-Arbeit.
- Codex für eng begrenzte konkrete Code-Fixes.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern oder löschen.
- Für KI-Kernfunktionen gilt weiterhin verbindlich:
  - Modellinferenz ausschließlich über Qualcomm QNN/HTP/NPU.
  - CPU nur für leichte Orchestrierung, Scheduler, RNG, Tensorverkettung, Maskenlogik, Datei-I/O, UI und Postprocessing.
  - Kein CPU-/GPU-Modellfallback als Produktlösung.
- Qualitätsstufen weiter strikt trennen:
  - `TECH PASS`
  - `FUNCTION PASS`
  - `PRODUCT PASS`
- Ein technisch gültiger NPU-Lauf ist kein automatischer Qualitäts-PASS.

## RORem – QNN Context Binaries erfolgreich erzeugt

Freigabe:

```text
Context Binary Build freigegeben
```

Verwendeter Qualcomm-Workflow:

```text
qnn-context-binary-generator
QnnModelDlc.dll
QnnHtp.dll
QnnSystem.dll
QAIRT 2.47.0.260601
```

Exakter Context-Generator:

```text
C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-context-binary-generator.exe
```

Backend:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll
```

System-Library:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnSystem.dll
```

Graph A:

```text
DLC_SHA256=4aab49508c6fc7d481f908c8fb472692fbf3802cded80935ff0b81a07e180307
CONTEXT_STATUS=SUCCESS
CONTEXT=C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_a\graph_a.serialized.bin
CONTEXT_SIZE=2523844608
CONTEXT_SHA256=e801d04e127895f001ad02696f2f8f9adbfc80bf5b0b8cc788d34337a53cf1c7
BUILD_SECONDS=576.80
```

Graph B:

```text
DLC_SHA256=becfbaca891e6b0a89116eb25776d9776706cff8520304ae0c9db555c7166e07
CONTEXT_STATUS=SUCCESS
CONTEXT=C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_b\graph_b.serialized.bin
CONTEXT_SIZE=2706165760
CONTEXT_SHA256=04a4c8872465e1f943875e8e1da01dd3f0eb34a9c69cbbe6df6866c63d49805d
BUILD_SECONDS=739.85
```

Final:

```text
TECH_PASS=YES
BLOCKER=NONE
LOCAL_HTP_SMOKE_RUN=NO
CROSS_GRAPH_EXECUTION_RUN=NO
VISUAL_TEST_RUN=NO
PRODUCT_INTEGRATION=NO
```

Erzeugte Dateien:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_a\graph_a.serialized.bin
C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_a\graph_a_info.json
C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_b\graph_b.serialized.bin
C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_b\graph_b_info.json
```

## RORem – echter lokaler QNN/HTP-Smoke PASS

Freigabe:

```text
HTP Smoke freigegeben
```

Referenzworkflow:

```text
temp/run_sdxl_e2e_context_smoke.py
```

QAIRT:

```text
v2.47.0.260601114230
```

Backend:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll
```

Graph A:

```text
GRAPH_A_CONTEXT_SHA256=e801d04e127895f001ad02696f2f8f9adbfc80bf5b0b8cc788d34337a53cf1c7
GRAPH_A_CONTEXT_LOAD_SECONDS=13.0110
GRAPH_A_EXEC_SECONDS=0.7307
GRAPH_A_HTP=PASS
GRAPH_A_OUTPUT_COUNT=10
```

Cross-Graph:

```text
CROSS_GRAPH_TENSOR_COUNT=10
CROSS_GRAPH_NAMES_MATCH=YES
CROSS_GRAPH_SHAPES_MATCH=YES
CROSS_GRAPH_DTYPE=FP16
CROSS_GRAPH_FINITE=YES
CROSS_GRAPH_TRANSFER=PASS
```

Graph B:

```text
GRAPH_B_CONTEXT_SHA256=04a4c8872465e1f943875e8e1da01dd3f0eb34a9c69cbbe6df6866c63d49805d
GRAPH_B_CONTEXT_LOAD_SECONDS=11.5014
GRAPH_B_EXEC_SECONDS=0.9170
GRAPH_B_HTP=PASS
```

Final Output:

```text
FINAL_OUTPUT_NAME=out_sample
FINAL_OUTPUT_SHAPE=[1,4,128,128]
FINAL_OUTPUT_DTYPE=float16
FINAL_OUTPUT_FINITE=YES
FINAL_OUTPUT_MIN=-0.663086
FINAL_OUTPUT_MAX=0.658691
FINAL_OUTPUT_MEAN=0.002691
```

Final:

```text
TECH_PASS=YES
CPU_MODEL_INFERENCE=NO
GPU_MODEL_INFERENCE=NO
VISUAL_TEST_RUN=NO
PRODUCT_INTEGRATION=NO
BLOCKER=NONE
```

Temporäre Smoke-Datei:

```text
C:\SnapdragonAI\temp\smoke_rorem_htp.py
```

Damit ist technisch nachgewiesen, dass RORem Graph A und Graph B real auf der Snapdragon-NPU über QNN/HTP laufen.

## Speicherbereinigung vor dem realen NPU-Bildtest

Während der Arbeit wurde C: knapp. Es ging ausdrücklich um Festplattenspeicher, nicht RAM.

Erste sichere Bereinigung:

- Download-Duplikate der zuvor verifizierten Kaggle-Artefakte wurden gelöscht.
- Danach wurden alte, nicht mehr benötigte SDXL-/Temp-/Transportartefakte gezielt entfernt.

Vor der größeren Bereinigung:

```text
FREE_GB=27.29
USED_GB=447.43
```

Gelöscht wurden:

```text
C:\SnapdragonAI\models\sdxl_inpainting_qnn_source
C:\SnapdragonAI\models\sdxl_inpainting_qnn_package.onnx
C:\SnapdragonAI\models\sdxl_inpainting_qnn_source.zip
C:\SnapdragonAI\temp\sd21_qnn_package
C:\SnapdragonAI\temp\controlnet_official_fetch
C:\SnapdragonAI\temp\issue2_requirements_smoke
C:\SnapdragonAI\temp\downloads
```

Danach:

```text
FREE_GB=49.3
USED_GB=425.42
```

WICHTIG:

```text
C:\SnapdragonAI\.git\objects\pack\pack-b1e45c32b366aec351d75f510378c14b28e51f97.pack
```

war ca. 6.14 GB groß und wurde ausdrücklich NICHT gelöscht. Git-Objekte niemals manuell aus `.git\objects\pack` entfernen.

Weiterhin geschützt/behalten:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_context
C:\SnapdragonAI\models\stable_diffusion_v3_5_qai
C:\SnapdragonAI\models\rorem_mixed
```

sowie benötigte Shared-CLIP-/VAE-NPU-Artefakte und Referenzbilder.

## RORem – erster vollständiger realer NPU-Bildtest

Freigabe:

```text
RORem NPU Bildtest freigegeben
```

Antigravity identifizierte und verwendete:

```text
C:\SnapdragonAI\temp\run_rorem_validation_cases.py
C:\SnapdragonAI\temp\run_rorem_npu_visual_test.py
```

Testfall:

```text
REFERENCE_CASE=Person Removal (Case 1)
INPUT_IMAGE=C:\SnapdragonAI\temp\rorem_validation\case1_input.png
MASK_IMAGE=C:\SnapdragonAI\temp\rorem_validation\case1_mask.png
REFERENCE_OUTPUT=C:\SnapdragonAI\temp\rorem_validation\case1_output.png
NPU_OUTPUT=C:\SnapdragonAI\temp\rorem_npu_visual_test\npu_result.png
```

Gemeldeter Lauf:

```text
STEPS=20
SEED=20260830
SCHEDULER=EulerDiscreteScheduler
PROMPT=empty background, high quality, photorealistic
NEGATIVE_PROMPT=NONE
```

NPU-Komponenten:

```text
CLIP_L_HTP=PASS
CLIP_G_HTP=PASS
VAE_ENCODER_HTP=PASS
ROREM_GRAPH_A_HTP=PASS
ROREM_GRAPH_B_HTP=PASS
VAE_DECODER_HTP=PASS
```

Timing:

```text
DENOISE_SECONDS=528.45
TOTAL_SECONDS=567.29
PEAK_RAM_GB=15.60
PAGING=YES
```

Gemeldete Funktionsflags:

```text
PERSON_OR_OBJECT_REMOVED=YES
BACKGROUND_PLAUSIBLE=YES
GHOSTING=NO
NEW_OBJECT_HALLUCINATION=NO
OUTSIDE_MASK_PRESERVED=YES
CPU_MODEL_INFERENCE=NO
GPU_MODEL_INFERENCE=NO
BLOCKER=NONE
```

Erzeugte temporäre Artefakte:

```text
C:\SnapdragonAI\temp\run_rorem_npu_visual_test.py
C:\SnapdragonAI\temp\rorem_npu_visual_test\summary.json
C:\SnapdragonAI\temp\rorem_npu_visual_test\npu_result.png
C:\SnapdragonAI\temp\rorem_npu_visual_test\npu_decoded_raw.png
C:\SnapdragonAI\temp\rorem_npu_visual_test\comparison_grid.png
C:\SnapdragonAI\temp\rorem_npu_visual_test\original.png
C:\SnapdragonAI\temp\rorem_npu_visual_test\mask.png
C:\SnapdragonAI\temp\rorem_npu_visual_test\reference_diffusers_result.png
```

Keine versionierten Projektdateien wurden modifiziert, kein Git-Add/Commit/Push, keine Paketinstallation.

## Manuelle Qualitätsbewertung durch Holger – erster NPU-Lauf NICHT gut genug

Antigravity hatte den Fall zunächst als `FUNCTION_PASS=YES` bewertet.

Holger sah sich jedoch das Vergleichsbild an und stellte ausdrücklich fest:

```text
das Ergebnis ist nicht gut
```

Sichtbare Schwächen:

- rekonstruierter Bereich deutlich verschmiert/weich;
- strukturell unsauber;
- sichtbarer Qualitätsbruch im Inpaint-Bereich;
- NPU-Ergebnis nicht überzeugend auf Niveau der Diffusers-Referenz.

Daher korrigierte Einordnung:

```text
TECH_PASS=YES
FUNCTION_PASS=YES
PRODUCT_PASS=NO
QUALITY_GATE=FAIL
```

Wichtig: Diese Einordnung wurde anschließend nochmals präzisiert, weil sich herausstellte, dass der NPU-Test nicht denselben Referenzvertrag verwendete.

## RORem Case 1 – statischer Paritätsaudit und Root-Cause-Diagnose

Antigravity führte anschließend eine gezielte Qualitätsdiagnose durch, ohne einen weiteren kompletten NPU-Lauf und ohne CPU-Referenz-Neulauf.

Verglichen wurden unter anderem:

```text
C:\SnapdragonAI\temp\run_rorem_validation_cases.py
C:\SnapdragonAI\temp\run_rorem_npu_visual_test.py
```

Entscheidender Befund:

### Diffusers-Referenz

```text
strength=0.9999
num_inference_steps=20
effektiv ausgeführte Denoising-Schritte=19
erster tatsächlicher Timestep=901
Timestep 951 wird übersprungen
```

Initial-Latents:

```text
scheduler.add_noise(image_latents, noise, 901)
```

Die Referenz startet also NICHT aus reinem Rauschen, sondern aus VAE-Image-Latents plus Noise bei Timestep 901.

### Alter NPU-Test

```text
effektiv strength=1.0
20 Schritte
Start bei Timestep 951
latents = noise * 11.0736
```

Der NPU-Test startete aus reinem Gauß-Rauschen und hatte damit einen anderen und schwierigeren Inpainting-Vertrag.

Zusätzliche Abweichungen:

- Referenz effektiv 19 statt 20 Steps.
- Seed-/Generatorverbrauch unterscheidet sich, weil im Diffusers-Referenzpfad VAE-Sampling Generatorzustand verbraucht.
- NPU benutzt QNN-VAE-Mode/deterministische Latents.
- Finales Composite:
  - Diffusers-Referenz bei `padding_mask_crop=None`: kein finales Original-Composite.
  - NPU-Test: Original außerhalb der Maske bitgenau wieder eingesetzt.

Postprocessing-Diagnose:

```text
RAW_ALREADY_BAD=YES
COMPOSITE_ADDS_ARTIFACTS=NO
```

Die Unschärfe war bereits in:

```text
C:\SnapdragonAI\temp\rorem_npu_visual_test\npu_decoded_raw.png
```

vorhanden. Das Composite verursachte die schlechte Struktur nicht.

Abschluss der Diagnose:

```text
TECH_DIAGNOSIS=COMPLETE

REFERENCE_PARAMETER_MATCH=NO
SCHEDULER_MATCH=YES
TIMESTEPS_MATCH=NO
NOISE_INIT_MATCH=NO
VAE_SCALING_MATCH=YES
MASK_CONTRACT_MATCH=YES
MASKED_IMAGE_MATCH=YES
NINE_CHANNEL_ORDER_MATCH=YES
CLIP_CONDITIONING_MATCH=YES
CFG_MATCH=YES
VAE_DECODE_CONTRACT_MATCH=YES
COMPOSITE_MATCH=NO

RAW_ALREADY_BAD=YES
COMPOSITE_ADDS_ARTIFACTS=NO

ROOT_CAUSE=LATENT_INITIALIZATION_AND_TIMESTEP_MISMATCH_DUE_TO_STRENGTH_0_9999
ROOT_CAUSE_CATEGORY=NOISE

FIX_IDENTIFIED=YES
REFERENCE_STEP_NUMERIC_COMPARE=NOT_FEASIBLE_LOCALLY
BLOCKER=NONE
CHANGED_FILES=None
```

Verbindliche neue Einordnung:

```text
ROREM_NPU_TECH_PASS=True
ROREM_NPU_QUALITY_GATE=NOT_YET_VALID
NPU_NUMERICAL_QUALITY_LOSS_PROVEN=False
ROOT_CAUSE=PIPELINE_PARITY_MISMATCH
```

Der bisherige schlechte NPU-Lauf darf NICHT als Beweis gewertet werden, dass QNN/HTP die RORem-Bildqualität verschlechtert.

## Geplanter Codex-Fix – Parität Case 1

Nach der Diagnose wurde entschieden, den eng begrenzten Paritätsfix mit Codex durchzuführen.

Ziel-Datei ausschließlich:

```text
C:\SnapdragonAI\temp\run_rorem_npu_visual_test.py
```

Geplanter Fix:

1. `strength=0.9999` exakt wie Diffusers-Referenz abbilden.
2. `set_timesteps(20)` beibehalten.
3. effektive Steps auf 19 reduzieren.
4. Timestep 951 überspringen.
5. bei Timestep 901 starten.
6. echtes `init_image` über den vorhandenen QNN/HTP-VAE-Encoder encodieren.
7. Initial-Latents über:

```text
scheduler.add_noise(image_latents, noise, first_effective_timestep)
```

erzeugen.

8. keine Pure-Noise-Initialisierung mehr.
9. RNG-Reihenfolge gegenüber Referenz explizit prüfen.
10. falls QNN-VAE deterministische Mode-Latents nutzt und die Diffusers-VAE-Sample-RNG-Reihenfolge nicht 1:1 reproduzierbar ist:
    - keinen CPU-VAE-Fallback einsetzen;
    - CPU-RNG für modellfreie Zufallszahlen ist erlaubt;
    - Paritätsgrenze dokumentieren.
11. Prompt, Seed, CFG, Maskenvertrag, 9ch-Reihenfolge, CLIP-L/G HTP, RORem Graph A/B HTP und VAE Decoder HTP unverändert lassen.
12. Vor Volltest zwingend statisch bestätigen:

```text
EFFECTIVE_STEPS=19
FIRST_TIMESTEP=901
INITIAL_LATENTS_USE_IMAGE_LATENTS=YES
PURE_NOISE_INITIALIZATION=NO
```

13. Nur wenn alle vier Werte korrekt sind, Case 1 genau EINMAL vollständig auf NPU ausführen.
14. neue Ergebnisse isoliert unter:

```text
C:\SnapdragonAI\temp\rorem_npu_visual_test_parity
```

speichern.
15. Case 2 und Case 3 noch NICHT automatisch starten.

## WICHTIG: PC-Absturz während des Codex-Auftrags

Am 4. September 2026 stürzte der Entwicklungs-PC während des oben beschriebenen Codex-Paritätsauftrags ab.

Damit ist der Status des Codex-Auftrags:

```text
CODEX_PARITY_FIX_STARTED=True
CODEX_PARITY_FIX_COMPLETED=UNKNOWN
PC_CRASH_DURING_CODEX_TASK=True
FULL_NPU_PARITY_RERUN_CONFIRMED=False
```

Es ist NICHT bestätigt, ob Codex vor dem Absturz bereits Teiländerungen an:

```text
C:\SnapdragonAI\temp\run_rorem_npu_visual_test.py
```

oder neue Dateien unter:

```text
C:\SnapdragonAI\temp\rorem_npu_visual_test_parity
```

angelegt hat.

Keine Annahmen über den Stand treffen.

## Verbindlicher nächster Schritt bei Wiederaufnahme

Nach Neustart NICHT sofort den 9-Minuten-NPU-Test starten.

Zuerst den Absturzstand kontrollieren.

### 1. Git-Status und Dateizustand prüfen

PowerShell, Entwicklungs-PC Holger, reine Prüfung:

```powershell
Set-Location -LiteralPath 'C:\SnapdragonAI'

$git = 'C:\Program Files\Git\cmd\git.exe'

& $git -C 'C:\SnapdragonAI' status --short --branch

Write-Output ''
Write-Output 'NPU-TESTSCRIPT:'

if (Test-Path -LiteralPath 'C:\SnapdragonAI\temp\run_rorem_npu_visual_test.py') {
    Get-Item -LiteralPath 'C:\SnapdragonAI\temp\run_rorem_npu_visual_test.py' |
    Select-Object FullName, Length, LastWriteTime
}
else {
    Write-Output 'FEHLT'
}

Write-Output ''
Write-Output 'PARITY-OUTPUTORDNER:'

if (Test-Path -LiteralPath 'C:\SnapdragonAI\temp\rorem_npu_visual_test_parity') {
    Get-ChildItem -LiteralPath 'C:\SnapdragonAI\temp\rorem_npu_visual_test_parity' -File -ErrorAction SilentlyContinue |
    Select-Object Name, Length, LastWriteTime
}
else {
    Write-Output 'NICHT_VORHANDEN'
}
```

### 2. Danach Codex-Auftrag fortsetzen oder vollständig wiederholen

- Wenn das Testscript unverändert beziehungsweise der Fix unvollständig ist:
  - denselben Codex-Paritätsauftrag vollständig wiederholen.
- Wenn Teiländerungen vorhanden sind:
  - Codex zuerst den aktuellen Stand lesen lassen;
  - prüfen, welche der vier Pflichtbedingungen bereits korrekt umgesetzt sind;
  - nur fehlende Teile ergänzen;
  - keinen Volltest starten, bevor alle vier statischen Bedingungen erfüllt sind.
- Keine Produktdateien anfassen.
- Kein Build/Installer/Git.
- Kein CPU-Diffusers-Neulauf.
- Kein Case 2/3.

Der entscheidende statische Gate bleibt:

```text
EFFECTIVE_STEPS=19
FIRST_TIMESTEP=901
INITIAL_LATENTS_USE_IMAGE_LATENTS=YES
PURE_NOISE_INITIALIZATION=NO
```

Erst danach genau ein neuer Case-1-NPU-Paritätslauf.

## Aktueller verbindlicher Gesamtstatus 4. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

ROREM_REFERENCE_QUALITY_PASS=True
ROREM_REFERENCE_QUALITY_CASES=3/3

ROREM_QNN_COMPILE_TECH_PASS=True
ROREM_CONTEXT_BINARY_CREATED=True
ROREM_GRAPH_A_CONTEXT_HTP=PASS
ROREM_GRAPH_B_CONTEXT_HTP=PASS
ROREM_CROSS_GRAPH_TRANSFER=PASS
ROREM_LOCAL_HTP_SMOKE_TECH_PASS=True

ROREM_FIRST_FULL_NPU_CASE1_RUN=True
ROREM_FIRST_FULL_NPU_CASE1_TECH_PASS=True
ROREM_FIRST_FULL_NPU_CASE1_VISUAL_QUALITY=NOT_GOOD_ENOUGH
ROREM_FIRST_FULL_NPU_CASE1_REFERENCE_PARITY=False

ROREM_PARITY_DIAGNOSIS_COMPLETE=True
ROREM_PARITY_ROOT_CAUSE=LATENT_INITIALIZATION_AND_TIMESTEP_MISMATCH_DUE_TO_STRENGTH_0_9999
ROREM_NPU_NUMERICAL_QUALITY_LOSS_PROVEN=False
ROREM_QUALITY_GATE_VALID=False

ROREM_PARITY_FIX_IDENTIFIED=True
ROREM_PARITY_FIX_STARTED=True
ROREM_PARITY_FIX_COMPLETED=UNKNOWN
ROREM_PARITY_FULL_RERUN=False

PC_CRASH_DURING_CODEX_TASK=True

ROREM_PRODUCT_PASS=False
ROREM_STUDIO_INTEGRATION=False

BUILD_4_SEPTEMBER=False
INSTALLER_4_SEPTEMBER=False
GIT_ADD_4_SEPTEMBER=False
COMMIT_4_SEPTEMBER=False
PUSH_4_SEPTEMBER=False

NEXT_SESSION=RECOVER_CODEX_RORem_CASE1_PARITY_FIX_AFTER_PC_CRASH
NEXT_GATE=VERIFY_PARTIAL_CODEX_STATE_THEN_CONTINUE_OR_REPEAT
```

## Feierabend / Pause 4. September 2026

Holger macht nach dem PC-Absturz zunächst Pause und setzt die Arbeit später fort.

Beim nächsten Einstieg:

1. Absturzstand prüfen.
2. Codex-Paritätsfix fortführen oder wiederholen.
3. statisches 4-Punkte-Gate bestätigen.
4. genau einen neuen Case-1-NPU-Paritätslauf ausführen.
5. neues `comparison_grid.png` manuell durch Holger bewerten.
6. erst bei überzeugender Case-1-Parität über Case 2/3 entscheiden.
7. noch keine Phoenix-Image-Lab-Produktintegration.

## Handover-Übernahme

Diese vollständige, nur unten ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.


# CHATGPT_HANDOVER – Ergänzung 4. September 2026, später Abend – Qualitäts-Screening und FLUX.2-klein-Setup

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsregel – heute erneut ausdrücklich bestätigt

Holger möchte bei technischen Tests keine unnötigen Rückfragen oder Zwischenstopps.

Verbindlich:

- Wenn der nächste sichere Schritt eindeutig ist, direkt den vollständigen ausführbaren Schritt liefern.
- Keine fragmentarischen Codeänderungen; bei Kaggle-/Python-Schritten immer den vollständigen benötigten Zellcode liefern.
- Anweisungen vor Ausgabe exakt auf Pfade, Abhängigkeiten, Reihenfolge und bereits bestätigte Artefakte prüfen.
- Keine geratenen Dateinamen oder Modellpfade verwenden.
- Nach Möglichkeit erst statische/importseitige Gates prüfen, bevor große Modelle erneut geladen oder lange Inferenzläufe gestartet werden.
- Bei Modellkandidaten zuerst Lizenz/Weights/Inference-Verfügbarkeit prüfen, dann genau einen echten Qualitätslauf, erst danach NPU-Portierung.
- Manuelle Bildbewertung durch Holger und sichtbare Artefakte haben Vorrang vor optimistischen Metriken.
- Ein `TECH PASS` ist kein `FUNCTION PASS` und kein `PRODUCT PASS`.

## RORem – endgültige Qualitätskorrektur

Der zuvor dokumentierte RORem-Referenzstatus `3/3 PASS` wurde nach strenger manueller Sichtprüfung korrigiert.

Wichtige neue Einordnung:

- Case 1 Person Removal: sichtbare Geister-/Rekonstruktionsartefakte, nicht produktreif.
- Case 2 Frame/Object Removal: Objekt/Frame nicht überzeugend entfernt; die damalige Maske war zusätzlich nicht ausreichend repräsentativ.
- Case 3 nur begrenzt aussagekräftig.

Die NPU-Portierung von RORem war technisch erfolgreich:

- 2-Graph-QNN-Compile erfolgreich;
- Context Binaries vorhanden;
- Graph A/B laufen real auf QNN/HTP;
- Cross-Graph-FP16-Transfer funktioniert;
- Full-NPU-Case-1 technisch ausführbar;
- Paritätsprobleme bei `strength=0.9999`, Timestep-Start und Latent-Initialisierung wurden identifiziert und korrigiert.

Trotzdem blieb die sichtbare Produktqualität der realen Entfernung unzureichend. Entscheidend ist, dass auch die Referenzqualität selbst die Produktanforderung nicht zuverlässig erfüllt.

Aktueller verbindlicher Status:

```text
ROREM_NPU_TECH_PASS=YES
ROREM_NPU_NUMERICAL_QUALITY_LOSS_PROVEN=NO
ROREM_REFERENCE_CASE1_QUALITY=FAIL
ROREM_REFERENCE_CASE2_QUALITY=FAIL
ROREM_PRODUCT_QUALITY_GATE=FAIL
ROREM_PRODUCT_INTEGRATION=STOP
```

Keine weitere Studio-Integration von RORem. Bestehende Shared Assets wie CLIP/VAE nur behalten, wenn sie für andere Kandidaten weiterverwendbar sind.

## PowerPaint v2-1 – Qualitätsstand

PowerPaint v2-1 wurde auf Kaggle T4 als Referenz getestet.

Positiver Fall:

- Bilderrahmen-/Frame-Removal auf dem 1600×900-Innenraumbild konnte mit geeigneter Maske überzeugend funktionieren.
- Ein exaktes Outside-Mask-Composite erhielt den restlichen Bildbereich.

Person-Removal:

- auf dem Wasser-/Personenbild mehrfach deutliche Halluzinationen, Säulen-/Stein-/Baum-artige Rekonstruktionen beziehungsweise Ghosting;
- die ursprüngliche Personenmaske war an Schuh/Fuß/Körper zu eng und wurde später als solcher Fehler erkannt;
- spätere direkte Testversuche wurden teilweise durch die bereits veränderte Kaggle-Runtime beziehungsweise ungeeignete direkte Pipeline-Aufrufe verfälscht;
- ein sauberer offizieller `PowerPaintController.predict(...)`-Retest mit korrigierter Maske wurde nicht als erfolgreich abgeschlossen bestätigt.

Aktuelle Einordnung:

```text
POWERPAINT_FRAME_REMOVAL=PASS_POTENTIAL
POWERPAINT_PERSON_REMOVAL=FAIL_SO_FAR
POWERPAINT_GENERAL_PRODUCT_GATE=NO
POWERPAINT_CORRECTED_MASK_OFFICIAL_CONTROLLER_RETEST=NOT_CONFIRMED
```

PowerPaint nicht als allgemeinen Product-GO behandeln.

## BrushNetX / BrushEdit – TECH/FUNCTION PASS, PRODUCT FAIL

Für BrushNetX wurde auf Kaggle eine kompatible isolierte Laufzeit aufgebaut:

```text
HF_HUB_VERSION=0.24.7
TRANSFORMERS_VERSION=4.38.2
TOKENIZERS_VERSION=0.15.2
DIFFUSERS_VERSION=0.27.0.dev0
BRUSHNET_IMPORT=PASS
```

Selektiv geladene Modelle:

```text
/kaggle/working/BrushEdit_min/brushnetX
/kaggle/working/BrushEdit_min/base_model/realisticVisionV60B1_v51VAE
```

Der echte Personen-Removal-Lauf veränderte den Maskenbereich numerisch, entfernte die Person visuell aber nicht überzeugend.

Dokumentierter Endstand:

```text
BRUSHNETX_TECH_PASS=YES
BRUSHNETX_FUNCTION_PASS=YES
BRUSHNETX_PERSON_REMOVAL=FAIL
BACKGROUND_REPLACEMENT=INSUFFICIENT
OUTSIDE_MASK_PRESERVATION=PASS
BRUSHNETX_PRODUCT_QUALITY_GATE=FAIL
NPU_PORT_EVALUATION=STOP
```

## ZITS – erster klar guter einfacher Personenfall, aber kein allgemeiner Product-GO

ZITS wurde über `iopaint==1.5.3` auf Kaggle getestet.

### Wasser-/Personenbild

Die ursprüngliche Maske war zu eng:

- linker Schuh/Fuß teilweise nicht sicher enthalten;
- Körper/Beine/Arme fast pixelgenau;
- zu wenig Sicherheitsrand.

Nach Maskenerweiterung mit ungefähr 20 px Radius:

- Person vollständig entfernt;
- Wasser/Horizont plausibel fortgesetzt;
- Felsen weitgehend erhalten;
- kein offensichtliches Ghosting;
- nur geringe Weichheit oberhalb des Felsens.

Dieser Fall war der erste deutlich überzeugende einfache Personen-Removal-Test.

### Bilderrahmen

ZITS entfernte den Rahmen grundsätzlich gut und füllte die Wand plausibel.

Problem:

- unpräzise Maske überlappte die davor stehende Frau;
- mit manueller engerer Rahmenmaske plus Schutzpolygon blieb an der Occlusion-Grenze ein dunkler Rest.

Schlussfolgerung: Für solche Fälle ist die Präzision der Benutzer-/Schutzmaske entscheidend.

### Komplexer 3-Personen-Fall

Beim früheren Bild mit drei Personen und Entfernung der linken Person:

- große milchig-/hautfarbene Verschmierung;
- deutlicher Ghost-/Restbereich;
- zwei verbleibende Personen blieben, aber der entfernte Bereich war nicht brauchbar.

Verbindlicher Status:

```text
ZITS_TECH_PASS=YES
ZITS_SIMPLE_OBJECT_REMOVAL=PASS
ZITS_SIMPLE_PERSON_REMOVAL=PASS
ZITS_COMPLEX_PERSON_REMOVAL=FAIL
ZITS_GENERAL_PRODUCT_CANDIDATE=NO
ZITS_SPECIALIZED_REMOVAL_CANDIDATE=YES
```

ZITS nicht als allgemeine Personenentfernung vermarkten. Als spezialisierter einfacher Repair-/Removal-Pfad kann es später erneut bewertet werden.

## LaMa / Big-LaMa – erneuter Optimierungsversuch endgültig FAIL

LaMa-Dilated war bereits zuvor real auf QNN/HTP technisch sehr schnell:

```text
~96.8 ms
TECH PASS
```

Die visuelle Qualität war jedoch bereits NO-GO.

Am 4. September wurde zusätzlich `SimpleLaMa` / Big-LaMa auf Kaggle mit dem Wasser-/Personenbild getestet.

Modell:

```text
big-lama.pt
ca. 196 MB
```

Optimierungsversuch:

- korrigierte Personenmaske;
- lokaler Crop um die Person;
- 2-Pass-Inpainting;
- Rand-/Naht-Reparatur;
- Outside-Mask-Composite.

Ein technischer 1-Pixel-Broadcastingfehler im Composite wurde repariert, ohne die bereits berechneten Inpainting-Pässe erneut auszuführen.

Sichtbares Ergebnis:

- Person wird überschrieben;
- lange dunkle/hautartige Säule bleibt;
- Wasser/Horizont werden nicht plausibel rekonstruiert;
- zweiter Pass verbessert den Kernfehler nicht.

Endstand:

```text
LAMA_MASK=PASS
LAMA_CROP_OPTIMIZATION=PASS
LAMA_TWO_PASS=PASS
LAMA_PERSON_REMOVAL=FAIL
GHOST_COLUMN=YES
BACKGROUND_RECONSTRUCTION=FAIL
LAMA_PRODUCT_QUALITY_GATE=FAIL
```

Lizenzseitig wurden sowohl `simple-lama-inpainting` als auch das originale LaMa-Repository als Apache-2.0 eingeordnet. Damit ist LaMa grundsätzlich kommerziell nutzbar, bleibt aber aus Qualitätsgründen für allgemeine Personenentfernung verworfen.

## Lizenz-/Kandidaten-Screening

Neue verbindliche Reihenfolge für jeden Kandidaten:

```text
LICENSE/WEIGHTS RIGHTS
-> RUNNABLE PRETRAINED WEIGHTS
-> ONE REAL QUALITY TEST
-> MANUAL VISUAL GATE
-> ONLY THEN NPU PORT ANALYSIS
```

### FLUX.1 Fill [dev]

- technisch stark;
- Modelllizenz nicht als frei kommerziell nutzbarer Produktpfad geeignet;
- daher für HK NPU STUDIO ausgeschlossen, solange keine passende kommerzielle Lizenz vorliegt.

### MI-GAN

Technisch attraktiv:

- explizit für mobile Inpainting-Szenarien entwickelt;
- ONNX-/mobile Ausrichtung interessant für Snapdragon/NPU;
- Repository-Code MIT.

Aber:

- kommerzielle Rechte der veröffentlichten Gewichte sind nicht sauber geklärt;
- offener Lizenzpunkt wegen Distillation/Teacher-Herkunft, insbesondere Co-Mod-GAN-/NVIDIA-Bedingungen.

Status:

```text
MIGAN_CODE_LICENSE=MIT
MIGAN_WEIGHTS_COMMERCIAL_RIGHTS=UNRESOLVED
MIGAN_PRODUCT_CANDIDATE=HOLD
```

Nicht als Produktmodell integrieren, solange die Gewichtsrechte unklar sind.

### FcF-Inpainting

- Hauptrepo wirkt Apache-2.0;
- enthält/berührt jedoch StyleGAN2-ADA-Komponenten unter NVIDIA Non-Commercial-Bedingungen;
- daher nicht als sauberer kommerzieller Produktkandidat behandeln.

### MAT

- Research-/Non-Commercial-orientierte Modellbedingungen;
- ausgeschlossen.

### EdgeConnect

- CC BY-NC;
- ausgeschlossen.

### CM-GAN

Offizielles Repo:

```text
htzheng/CM-GAN-Inpainting
```

- Repository-Lizenz Apache-2.0;
- Architektur explizit mit object-aware training für bessere Objektentfernung.

Entscheidender praktischer Blocker:

- offizielles Repository stellt keinen klaren produktionsreifen Inferenzpfad für eigene Bilder bereit;
- keine eindeutig bereitgestellten/pretrained nutzbaren Modellgewichte für einen normalen Einzelbildtest bestätigt;
- README veröffentlicht primär Paper, Ergebnisse, Dataset-/Maskengenerator-Bestand.

Status:

```text
CMGAN_CODE_LICENSE=APACHE-2.0
CMGAN_OBJECT_REMOVAL_DESIGN=YES
CMGAN_PUBLIC_INFERENCE_PIPELINE=NO
CMGAN_PUBLIC_PRETRAINED_CHECKPOINT=NOT_CONFIRMED
CMGAN_IMMEDIATE_KAGGLE_TEST=NO
```

Keinen erfundenen Kaggle-Pfad bauen.

## Neuer Kandidat: FLUX.2 [klein] 4B

Ausgewählt wurde anschließend:

```text
black-forest-labs/FLUX.2-klein-4B
```

zusammen mit einer Object-Removal-LoRA.

Arbeitsklassifikation:

```text
BASE_MODEL_LICENSE=APACHE-2.0
OBJECT_REMOVAL_LORA_LICENSE=APACHE-2.0
PRETRAINED_WEIGHTS=YES
PUBLIC_INFERENCE=YES
LOCAL_USE=YES
COMMERCIAL_PRODUCT_USE=LICENSING_GATE_CURRENTLY_POSITIVE
```

Vor einer späteren tatsächlichen Distribution bleiben übliche Third-Party-License-/Notice-Prüfungen erforderlich.

Potenzielle weitere Nutzung des Basismodells, noch nicht produktverifiziert:

- Text-to-Image;
- Image-to-Image/Edit per Text;
- Objekte entfernen;
- Objekte ersetzen;
- Objekte hinzufügen;
- Hintergrund ändern;
- Material-/Stiländerungen;
- Multi-Reference Editing;
- Produkt-/Designvarianten.

Diese Zusatzfunktionen wurden heute nur als Modellpotenzial besprochen, nicht als HK-NPU-STUDIO-Produktfunktion bestätigt.

## FLUX.2-klein – Kaggle Dependency Gate

Die erste `DiffusionPipeline.from_pretrained(...)`-Variante scheiterte, weil die normale installierte Diffusers-Version `Flux2KleinPipeline` noch nicht kannte.

Danach wurde Diffusers direkt aus dem offiziellen GitHub-Main installiert und die Hugging-Face-Komponenten aktualisiert.

Nach Kernel-Neustart bestätigter Gate:

```text
huggingface-hub = 1.30.0
diffusers       = 0.41.0.dev0
transformers    = 5.16.1
accelerate      = 1.14.0
peft            = 0.20.0
safetensors     = 0.8.0

HUGGINGFACE_HUB_IMPORT=PASS
DIFFUSERS_IMPORT=PASS
FLUX2_KLEIN_PIPELINE_IMPORT=PASS
DEPENDENCY_GATE=PASS
```

## FLUX.2-klein – Basismodell geladen

Auf Kaggle T4 wurde das Basismodell erfolgreich geladen:

```text
MODEL_LOAD=START
Download/Reconstruction ca. 16.0 GB
BASE_MODEL_LOAD=PASS
```

Damit ist das Basismodell selbst im Hugging-Face-Cache vorhanden.

Noch keine eigentliche Bildinferenz durchgeführt.

## FLUX.2-klein Object-Removal-LoRA – 58,4-MB-Datei unbrauchbar

Erster LoRA-Pfad:

```text
fal/flux-2-klein-4B-object-remove-lora
flux-object-remove-lora.safetensors
```

Download:

```text
LORA_SIZE_BYTES=58441728
LORA_SIZE_MB=55.73
SHA256=70ceea34a8bcd6e7d0249ba26bb59a3cd8b8c38745fab65a3eb112a5c13e3c69
```

Trotz vollständigem Neudownload und exakt passendem Hash:

```text
SafetensorError:
Error while deserializing header:
incomplete metadata, file not fully covered
```

Ein Diffusers-Mirror:

```text
xocialize/object-remove-FLUX.2-klein-4B-lora
```

lieferte exakt dieselbe 58.441.728-Byte-Datei und denselben SHA-256. Auch dort identischer Safetensors-Fehler.

Manuelle Headerdiagnose bewies:

```text
TRUNCATED=True
MISSING_BYTES=17597344
```

Damit ist die 58,4-MB-Datei für den verwendeten normalen Safetensors-/Diffusers-Pfad nicht brauchbar. Keine weiteren Downloads derselben Datei.

## FLUX.2-klein – gültige 76-MB-ComfyUI-LoRA bestätigt

Zweite Datei aus dem offiziellen FAL-Repo:

```text
kDEkt5q7tDLKOpQJIVMPx_pytorch_lora_weights_comfy_converted.safetensors
```

Bestätigte Werte:

```text
SIZE_BYTES=76038936
SIZE_MB=72.52
SHA256=dc197de62e174863f83fc4052465603f4389de7c3a78e17f3d41a1f6f11488ec
SHA256_GATE=PASS

SAFETENSORS_VALIDATION=PASS
TENSOR_COUNT=136
COMFY_LORA_FILE_GATE=PASS
```

Beispiel der Tensor-Keys:

```text
diffusion_model.double_blocks.0.img_attn.proj.lora_A.weight
diffusion_model.double_blocks.0.img_attn.proj.lora_B.weight
diffusion_model.double_blocks.0.img_attn.qkv.lora_A.weight
diffusion_model.double_blocks.0.img_attn.qkv.lora_B.weight
...
```

Damit ist diese 76-MB-Datei technisch intakt.

## Aktueller FLUX.2-klein-Blocker: torchao-Version

Beim direkten Laden der gültigen 76-MB-LoRA in die bereits geladene `Flux2KleinPipeline`:

```text
OLD_LORA_UNLOAD=PASS
LORA_LOAD=FAIL
```

Exakter Fehler:

```text
ImportError:
Found an incompatible version of torchao.
Found version 0.10.0,
but only versions above 0.16.0 are supported
```

Traceback-Pfad:

```text
diffusers
-> peft
-> peft.tuners.lora.torchao
-> is_torchao_available()
```

Damit ist der aktuelle Blocker nicht mehr:

- Basismodell,
- Diffusers-Import,
- LoRA-Dateiintegrität,
- Safetensors,
- oder Maskenlogik,

sondern ausschließlich die zu alte Kaggle-`torchao`-Version.

Aktueller Zustand:

```text
FLUX2_KLEIN_BASE_MODEL_LOAD=PASS
FLUX2_KLEIN_BASE_MODEL_CACHED=YES
FLUX2_KLEIN_DIFFUSERS_IMPORT_GATE=PASS

FLUX2_OBJECT_REMOVE_LORA_58MB=INVALID_FOR_CURRENT_SAFETENSORS_PATH
FLUX2_OBJECT_REMOVE_LORA_76MB_FILE_VALID=YES
FLUX2_OBJECT_REMOVE_LORA_76MB_TENSOR_COUNT=136

TORCHAO_CURRENT_VERSION=0.10.0
TORCHAO_REQUIRED_MINIMUM=0.16.0
FLUX2_LORA_LOAD=BLOCKED_BY_TORCHAO_VERSION

FLUX2_IMAGE_INFERENCE_RUN=False
FLUX2_PERSON_REMOVAL_QUALITY_GATE=PENDING
FLUX2_NPU_PORT_ANALYSIS=NOT_STARTED
```

## Verbindlich nächster Kaggle-Schritt

Noch keinen neuen Modellkandidaten anfangen.

Zuerst nur `torchao` reparieren.

Geplanter Schritt:

1. `torchao==0.16.0` installieren.
2. Kernel neu starten, weil PEFT/torchao bereits importiert waren.
3. Import-Gate prüfen:

```text
TORCH_IMPORT=PASS
TORCHAO_IMPORT=PASS
PEFT_IMPORT=PASS
DIFFUSERS_IMPORT=PASS
FLUX2_KLEIN_PIPELINE_IMPORT=PASS
TORCHAO_GATE=PASS
```

4. Basismodell aus dem vorhandenen Hugging-Face-Cache erneut in RAM laden; kein erneuter 16-GB-Internetdownload erforderlich, sofern Cache erhalten.
5. ausschließlich die validierte 76-MB-ComfyUI-LoRA laden.
6. Adapterstärke zunächst `1.1`.
7. genau einen realen Test mit dem bekannten Wasser-/Personenbild durchführen.
8. korrigierte Personenmaske beziehungsweise markiertes Eingabebild verwenden.
9. keine Seed-Lotterie und keine Serie von Varianten.
10. Ergebnis manuell prüfen:
   - Person vollständig weg?
   - Wasserlinie plausibel?
   - keine Säule/kein Ghosting?
   - Felsen erhalten?
   - Übergang unauffällig?
11. Nur bei klarem sichtbarem PASS NPU-Portierbarkeit analysieren.
12. Bei sichtbarem FAIL FLUX.2-klein Object Removal sofort verwerfen.

## Kaggle-Datasets / aktueller Notebookkontext

Im aktuellen Notebook sind weiterhin sichtbar:

```text
Bild222222
  case_frame_input.jpg
  case_frame_mask.png

Person_test
  case_person_input.jpg
  case_person_mask.png

powerpaint_test_2
```

Notebook-/Kaggle-Session wurde über viele Modelltests hinweg verändert. Bei unerwarteten Paketkonflikten nicht automatisch neue globale Downgrade-/Upgrade-Ketten starten; möglichst durch Gates oder sauberen Kernel-Neustart isolieren.

## Keine lokalen Produktänderungen durch die heutigen Kaggle-Tests

Die heutigen Qualitäts-/Kaggle-Arbeiten waren Referenz- und Kandidatenprüfung.

Nicht durchgeführt:

```text
HK NPU STUDIO Produktintegration
Build
Installer
git add
Commit
Push
Release
```

Keine aus den Kaggle-Tests abgeleitete Modellintegration in `C:\SnapdragonAI` vornehmen, bevor ein Kandidat den sichtbaren Qualitäts-Gate bestanden hat.

## Aktueller Gesamtstatus – später Abend 4. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

ROREM_PRODUCT_QUALITY_GATE=FAIL
POWERPAINT_GENERAL_PRODUCT_GATE=NO
BRUSHNETX_PRODUCT_QUALITY_GATE=FAIL

ZITS_SIMPLE_PERSON_REMOVAL=PASS
ZITS_COMPLEX_PERSON_REMOVAL=FAIL
ZITS_GENERAL_PRODUCT_CANDIDATE=NO
ZITS_SPECIALIZED_REMOVAL_CANDIDATE=YES

LAMA_PRODUCT_QUALITY_GATE=FAIL
LAMA_COMMERCIAL_LICENSE_GATE=PASS_APACHE_2_0

MIGAN_PRODUCT_CANDIDATE=HOLD_LICENSE_WEIGHTS_UNRESOLVED
CMGAN_IMMEDIATE_KAGGLE_TEST=NO
FCF_COMMERCIAL_GATE=PROBLEMATIC
MAT_COMMERCIAL_GATE=FAIL
EDGECONNECT_COMMERCIAL_GATE=FAIL

FLUX2_KLEIN_SELECTED_FOR_NEXT_QUALITY_TEST=True
FLUX2_KLEIN_BASE_LICENSE=APACHE_2_0
FLUX2_KLEIN_BASE_MODEL_LOAD=PASS
FLUX2_KLEIN_BASE_MODEL_CACHED=YES

FLUX2_OBJECT_REMOVE_LORA_58MB_VALID=False
FLUX2_OBJECT_REMOVE_LORA_76MB_VALID=True
FLUX2_OBJECT_REMOVE_LORA_76MB_SHA256=dc197de62e174863f83fc4052465603f4389de7c3a78e17f3d41a1f6f11488ec
FLUX2_OBJECT_REMOVE_LORA_76MB_TENSORS=136

FLUX2_CURRENT_BLOCKER=TORCHAO_0_10_TOO_OLD
FLUX2_REQUIRED_TORCHAO=>=0.16.0
FLUX2_REAL_PERSON_REMOVAL_RUN=False
FLUX2_PRODUCT_QUALITY_GATE=PENDING
FLUX2_NPU_ANALYSIS=False

BUILD_4_SEPTEMBER_LATE=False
INSTALLER_4_SEPTEMBER_LATE=False
GIT_ADD_4_SEPTEMBER_LATE=False
COMMIT_4_SEPTEMBER_LATE=False
PUSH_4_SEPTEMBER_LATE=False

NEXT_SESSION=KAGGLE_TORCHAO_FIX_THEN_ONE_FLUX2_KLEIN_PERSON_REMOVAL_TEST
```

## Verbindlicher nächster Einstieg

Nicht wieder bei LaMa, RORem, PowerPaint, BrushNetX, ZITS oder CM-GAN anfangen.

Direkt fortsetzen bei:

```text
Kaggle
-> torchao 0.10.0 auf 0.16.0 aktualisieren
-> Kernel restart
-> Import-Gate
-> FLUX.2-klein Base aus Cache laden
-> gültige 76-MB-LoRA laden
-> genau EIN Wasser-/Personen-Removal-Test
-> manuelle Qualitätsentscheidung
```

Erst wenn dieser eine FLUX.2-klein-Test sichtbar überzeugt, lohnt sich eine Architektur-/ONNX-/QNN-/NPU-Bewertung.

## Handover-Übernahme

Diese vollständige, nur unten ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt, neu aufgebaut oder durch eine separate Ergänzungsdatei ersetzt werden.

# CHATGPT_HANDOVER – Ergänzung 5. September 2026 – FLUX.2-klein Qualitäts-PASS, HTP-ROI-Durchbruch, echte Gewichte und vollständiger 25-Block-NPU-Schritt

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Architekturregeln – am 5. September verbindlich bestätigt

- Sprache mit Holger weiterhin Deutsch.
- FLUX.2-klein 4B ist für Object Removal jetzt **gesetzt**. Keine weitere Modellsuche für diese Funktion.
- Core-AI-Inferenz im Produkt bleibt **NPU-only**. Kein CPU-/GPU-Fallback für Transformer, VAE oder andere Kernmodelle.
- CPU ist nur für leichte Orchestrierung zulässig, z. B. Scheduler, Tensor-Concat/Split, RAW-I/O, Maskenlogik, Crop/Resize, Compositing und UI.
- Kaggle/GPU bleibt ausschließlich Referenz-/Qualitäts- und Export-/Konvertierungsumgebung, niemals Produktinferenz.
- TECH PASS, FUNCTION PASS und PRODUCT PASS immer getrennt bewerten.
- Nach den langen Sprints heute künftig eng begrenzte Gates verwenden; keine offenen Trial-and-Error-Schleifen.
- Wenn ein Sprint länger als sinnvoll läuft: harten Zeitrahmen setzen, laufenden Schritt zu Ende führen oder abbrechen und nur den vorhandenen Stand auswerten.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- Bestehende modified/untracked Dateien nicht anfassen.

## FLUX.2-klein – Referenzqualität auf Kaggle endgültig PASS

Nach den Paket-/torchao-Problemen vom 4. September wurde der FLUX.2-klein-Referenzpfad am 5. September erfolgreich abgeschlossen.

Erfolgreiche Kaggle-Umgebung:

```text
torch=2.10.0+cu128
torchao=0.17.0
peft=0.19.1
diffusers=0.37.1
transformers=5.0.0
accelerate=1.13.0
```

Wichtige Korrektur beim Laden:

- `dtype=torch.bfloat16` wurde von der verwendeten Diffusers-Version ignoriert und führte zu FP32-/RAM-Problemen.
- Erfolgreicher Pfad:
  - `torch_dtype=torch.float16`
  - `low_cpu_mem_usage=True`
  - `enable_sequential_cpu_offload()`

Verwendete gültige Object-Removal-LoRA:

```text
kDEkt5q7tDLKOpQJIVMPx_pytorch_lora_weights_comfy_converted.safetensors
SIZE=76038936 Bytes
SHA256=dc197de62e174863f83fc4052465603f4389de7c3a78e17f3d41a1f6f11488ec
TENSORS=136
```

Die frühere 58-MB-Datei `flux-object-remove-lora.safetensors` war abgeschnitten/ungültig und darf nicht mehr verwendet werden.

Referenzlauf:

```text
PROMPT=Remove the highlighted object from the scene
LORA_SCALE=1.1
WORK_SIZE=672x960
MASK_WHITE_RATIO=0.0711
MASK_EXPANSION≈14px
```

Ergebnis:

```text
INFERENCE_SECONDS=19.76
CUDA_PEAK_ALLOCATED_GB=1.48
INFERENCE=PASS

RAW_OUTPUT=/kaggle/working/flux2_person_test/flux2_person_raw.png
FINAL_OUTPUT=/kaggle/working/flux2_person_test/flux2_person_removed.png
COMPARISON_OUTPUT=/kaggle/working/flux2_person_test/flux2_person_comparison.png

OUTSIDE_MASK_BIT_EXACT=True
```

Visuelle Abnahme des Wasser-/Personenfalls:

```text
FLUX2_KLEIN_TECH_PASS=YES
FLUX2_KLEIN_FUNCTION_PASS=YES
PERSON_REMOVAL=PASS
BACKGROUND_RECONSTRUCTION=PASS
GHOSTING=NO
HUMAN_REMAINS=NO
MASK_BOUNDARY=PASS
OUTSIDE_MASK_PRESERVATION=PASS
REFERENCE_PERSON_CASE_QUALITY=PASS
PRODUCT_QUALITY_GATE=PASS
```

Wichtig: `PRODUCT_QUALITY_GATE=PASS` bezieht sich auf die Bildqualität des Referenzfalls, nicht auf die vollständige HK-NPU-STUDIO-Produktreife.

## FLUX.2-klein – technische Architektur für den NPU-Pfad

Bestätigte Architektur:

1. Qwen3 Text Encoder
   - Hidden Size 2560
   - 36 Layer
   - 32 Query Heads
   - 8 KV Heads
   - Head Dim 128
   - Prompt Embeddings aus Layern 9, 18, 27 gestapelt -> 7680

2. `Flux2Transformer2DModel`
   - 5 Dual-Stream-Blöcke
   - 20 Single-Stream-Blöcke
   - 24 Heads × 128 = 3072
   - `in_channels=128`
   - `joint_attention_dim=7680`
   - `axes_dims_rope=[32,32,32,32]`

3. `AutoencoderKLFlux2`
   - 32 Latent Channels

4. FlowMatch Euler Scheduler
   - CPU-Orchestrierung zulässig

Die Object-Removal-LoRA kann offline in den Transformer fusioniert werden; Runtime-LoRA ist für den späteren NPU-Graph nicht erforderlich.

## HTP-PoCs – grundlegende FLUX.2-Operatoren/Blöcke PASS

### Attention Core

Statischer Vertrag:

```text
query/key/value=[1,5168,24,128] FP16
rope_cos/sin=[5168,128] FP16
```

Ergebnis:

```text
ATTENTION_CORE_HTP=PASS
FLUX2_FULL_LENGTH_ATTENTION_HTP=PASS

NPU/HTP wall≈3.649 s
MAE=4.292760e-05
MAX_ABS=1.098633e-03
RMSE=5.560204e-05
COSINE=0.999998
```

### Full Single Transformer Block – synthetische deterministische Gewichte

```text
hidden=[1,5168,3072]
temb_mod=[1,9216]
rope_cos/sin=[5168,128]
PARAMETERS=122683648
FP16_WEIGHT_BYTES=245367296
```

Ergebnis:

```text
SINGLE_BLOCK_HTP=PASS
FLUX2_SINGLE_TRANSFORMER_BLOCK_HTP=PASS
NPU_ACCELERATOR_TIME=4.613 s
MAE=9.042607e-06
MAX_ABS=3.906250e-03
RMSE=7.132191e-05
COSINE=1.000000
```

### Full Dual-Stream Transformer Block – synthetische deterministische Gewichte

```text
image_hidden=[1,5040,3072]
text_hidden=[1,128,3072]
temb_mod_img/txt=[1,18432]
rope_cos/sin=[5168,128]
PARAMETERS=245367296
FP16_WEIGHT_BYTES=490734592
```

Ergebnis:

```text
DUAL_BLOCK_HTP=PASS
FLUX2_DUAL_TRANSFORMER_BLOCK_HTP=PASS
NPU_ACCELERATOR_TIME=2.831 s

IMAGE_MAE=6.904372e-06
TEXT_MAE=6.839047e-06
IMAGE_COSINE=1.000000
TEXT_COSINE=1.000000
```

Gesamt:

```text
ATTENTION_CORE_HTP=PASS
SINGLE_BLOCK_HTP=PASS
DUAL_BLOCK_HTP=PASS
```

## W8A16 – QNN 2.47 auf HTP V73 blockiert

Der W8A16-Single-Block-Compile selbst war möglich:

```text
QAI_W8A16_COMPILE=PASS
W8A16_DLC_SIZE≈122.7 MB
```

HTP-Context-Generierung scheiterte jedoch reproduzierbar an gemischten Datentypen innerhalb von strukturellen Reshape-/Unsqueeze-Operationen:

```text
in[0]=QNN_DATATYPE_FLOAT_32
out[0]=QNN_DATATYPE_UFIXED_POINT_16
error=0xc26
```

Rescue-Sprint Pfad A:

- Unsqueeze/Gather/RoPE-Struktur umgebaut;
- danach reines FP16-ONNX ohne Cast-Knoten erzeugt;
- W8A16-Compile jeweils SUCCESS;
- HTP-Context weiterhin FAIL an `/Reshape`.

Rescue-Sprint Pfad B:

- Heavy-Core als separater W8A16-Graph isoliert;
- QAI-Compile SUCCESS;
- HTP-Context FAIL an einem **vom QNN-Compiler selbst erzeugten**:

```text
/to_qkv_mlp_proj/MatMul_pre_reshape
```

Befund:

```text
SOURCE_ONNX_REUSED=YES
QNN_W8A16_CONVERSION=PASS
HTP_W8A16_CONTEXT=FAIL
HTP_W8A16_EXECUTION=FAIL
FLUX2_W8A16_PERFORMANCE_GATE=BLOCKED
```

Entscheidung:

- W8A16 auf aktueller AIStack/QNN-2.47-Toolchain nicht weiter verfolgen.
- Kein weiterer W8A16-Repair-Sprint.
- FLUX.2 bleibt gesetzt.
- Optimierung wird über ROI, Graph-Layout und später Runtime-Persistenz durchgeführt.

## ROI-Strategie – zentraler Performance-Durchbruch

Für Object Removal muss nicht das komplette Bild durch den Transformer laufen. Stattdessen wird eine erweiterte Bounding Box um die Objektmaske auf einen statischen Produktbucket gebracht.

Erster bestätigter Bucket:

```text
ROI_WIDTH=384
ROI_HEIGHT=640
```

Patchified pro Bild:

```text
24 × 40 = 960 Tokens
```

Für die ersten Performance-PoCs:

```text
Noise Tokens=960
Reference Tokens=960
Text Tokens=32
Total Sequence=1952
```

### ROI Single Block – synthetische Gewichte

```text
FULL_SEQUENCE=5168
ROI_SEQUENCE=1952

FULL_NPU_SECONDS=4.613
ROI_NPU_SECONDS=0.861
ROI_SPEEDUP=5.356x
TIME_REDUCTION=81.3%

MAE=9.292329e-06
COSINE=1.000000
NUMERICAL_MATCH=PASS

ROI_CONTEXT_SIZE_BYTES=255148032
ROI_SPILL_BYTES=423503872
ROI_FILL_BYTES=138749952

ROI_PERFORMANCE_GATE=PASS
```

### ROI Dual Block – synthetische Gewichte

```text
FULL_SEQUENCE=5168
ROI_SEQUENCE=1952

FULL_DUAL_NPU_SECONDS=2.831
ROI_DUAL_NPU_SECONDS=0.686
ROI_DUAL_SPEEDUP=4.125x
TIME_REDUCTION=75.8%

IMAGE_MAE=6.882541e-06
TEXT_MAE=6.873956e-06
IMAGE_COSINE=1.000000
TEXT_COSINE=1.000000

ROI_DUAL_CONTEXT_SIZE_BYTES=496537600
ROI_DUAL_SPILL_BYTES=549527552
ROI_DUAL_FILL_BYTES=165879808

ROI_DUAL_PERFORMANCE_GATE=PASS
```

Die synthetische Hochrechnung sank damit von ca. 106,4 s auf ca. 20,65 s Transformer-Rechenzeit pro Denoising-Schritt.

## Lokale echte FLUX.2-Gewichte und LoRA heruntergeladen

Lokaler Basisordner:

```text
C:\SnapdragonAI\models\flux2_klein_4b
```

Transformer:

```text
C:\SnapdragonAI\models\flux2_klein_4b\transformer\config.json
C:\SnapdragonAI\models\flux2_klein_4b\transformer\diffusion_pytorch_model.safetensors
TRANSFORMER_BYTES=7751109744
```

Object-Removal-LoRA:

```text
C:\SnapdragonAI\models\flux2_klein_4b\lora\kDEkt5q7tDLKOpQJIVMPx_pytorch_lora_weights_comfy_converted.safetensors
LORA_BYTES=76038936
LORA_SHA256=dc197de62e174863f83fc4052465603f4389de7c3a78e17f3d41a1f6f11488ec
```

Download-/Hash-Gates:

```text
FLUX2_TRANSFORMER_DOWNLOAD=PASS
OBJECT_REMOVAL_LORA_DOWNLOAD=PASS
LORA_HASH_GATE=PASS
```

## Echter FLUX.2 Single Block mit echter LoRA – HTP PASS

Lokale Umgebung:

```text
DIFFUSERS_VERSION=0.40.0
TORCH_VERSION=2.14.0.dev20260808+cpu
```

Transformer:

```text
TRANSFORMER_CLASS=Flux2Transformer2DModel
NUM_DUAL_BLOCKS=5
NUM_SINGLE_BLOCKS=20
```

Erster echter Single Block:

```text
REAL_BLOCK_MODULE=single_transformer_blocks.0
REAL_BLOCK_CLASS=Flux2SingleTransformerBlock
REAL_BLOCK_PARAMETER_COUNT=122683648
REAL_BLOCK_FP16_WEIGHT_BYTES=245367296
```

LoRA-Konvertierung:

```text
LORA_TOTAL_TENSORS=136
CONVERTED_LORA_TENSORS=176
BLOCK_MATCHING_LORA_TENSORS=4
```

Betroffene Module:

```text
single_transformer_blocks.0.attn.to_qkv_mlp_proj
single_transformer_blocks.0.attn.to_out
```

Offline-Fusion:

```text
LORA_SCALE=1.1
LORA_FUSION=PASS
FUSED_MODULE_COUNT=2
```

Nachgewiesene Gewichtsänderungen u. a.:

```text
to_qkv_mlp_proj.q_slice=True
to_qkv_mlp_proj.k_slice=True
to_qkv_mlp_proj.v_slice=True
to_qkv_mlp_proj.mlp_slice=True
to_out=True
```

Echter ROI-Blockvertrag:

```text
SEQUENCE=1952
hidden_states=[1,1952,3072]
temb_mod=[1,9216]
rope_cos/sin=[1952,128]
```

ONNX/QAI/HTP:

```text
REAL_WEIGHT_ONNX=PASS
REAL_ONNX_BYTES=490774027
REAL_ONNX_SHA256=327d82c08055bcc85d8d7e43b7230ce8e4f4783e203f2c2857d21d1513dab495

QAI_FP16_COMPILE=PASS
QAI_JOB_ID=j5qy8rl7g
DLC_BYTES=490811916

HTP_CONTEXT=PASS
REAL_BLOCK_CONTEXT_BYTES=254988288
REAL_BLOCK_SPILL_BYTES=423503872
REAL_BLOCK_FILL_BYTES=138749952

HTP_EXECUTION=PASS
REAL_BLOCK_HTP_WALL_SECONDS=2.326675
REAL_BLOCK_NPU_ACCELERATOR_SECONDS=0.816552
```

Numerik:

```text
MAE=5.764329e-03
MAX_ABS_ERROR=2.500000e-01
RMSE=9.738794e-03
COSINE_SIMILARITY≈0.9999997
FINITE=True
NAN_COUNT=0
INF_COUNT=0
NUMERICAL_MATCH=PASS
```

Vergleich:

```text
SYNTHETIC_ROI_SINGLE_NPU_SECONDS=0.861
REAL_ROI_SINGLE_NPU_SECONDS=0.816552
REAL_VS_SYNTHETIC_RATIO=0.9484
```

Final:

```text
REAL_FLUX2_ROI_ARCHITECTURE_GATE=PASS
```

## Echter FLUX.2 Dual Block mit echter LoRA – HTP PASS

Erster echter Dual Block:

```text
REAL_DUAL_BLOCK_MODULE=transformer_blocks.0
REAL_DUAL_BLOCK_CLASS=Flux2TransformerBlock
REAL_DUAL_PARAMETER_COUNT=245367296
REAL_DUAL_FP16_WEIGHT_BYTES=490734592
```

LoRA:

```text
DUAL_BLOCK_MATCHING_LORA_TENSORS=16
DUAL_LORA_FUSION=PASS
DUAL_FUSED_MODULE_COUNT=8
```

Betroffene Module:

```text
transformer_blocks.0.attn.add_k_proj
transformer_blocks.0.attn.add_q_proj
transformer_blocks.0.attn.add_v_proj
transformer_blocks.0.attn.to_add_out
transformer_blocks.0.attn.to_k
transformer_blocks.0.attn.to_out.0
transformer_blocks.0.attn.to_q
transformer_blocks.0.attn.to_v
```

ONNX/QAI/HTP:

```text
REAL_DUAL_ONNX=PASS
REAL_DUAL_ONNX_BYTES=981595340
REAL_DUAL_ONNX_SHA256=08d0b3381574fc8d3def37c22245d19431612ceb4b56eb06a6f775d765e7ba73

DUAL_QAI_FP16_COMPILE=PASS
DUAL_QAI_JOB_ID=jgk4zyvwp
DUAL_DLC_BYTES=981661436

DUAL_HTP_CONTEXT=PASS
REAL_DUAL_CONTEXT_BYTES=496541696
REAL_DUAL_SPILL_BYTES=549527552
REAL_DUAL_FILL_BYTES=165879808

DUAL_HTP_EXECUTION=PASS
REAL_DUAL_HTP_WALL_SECONDS=2.432613
REAL_DUAL_NPU_ACCELERATOR_SECONDS=0.676897
```

Numerik:

```text
IMAGE_MAE=6.794115e-03
TEXT_MAE=8.060144e-03

IMAGE_MAX_ABS_ERROR=1.875000e-01
TEXT_MAX_ABS_ERROR=1.562500e-01

IMAGE_COSINE_SIMILARITY=0.999999
TEXT_COSINE_SIMILARITY=0.999999

IMAGE_NUMERICAL_MATCH=PASS
TEXT_NUMERICAL_MATCH=PASS
```

Vergleich:

```text
SYNTHETIC_ROI_DUAL_SECONDS=0.686
REAL_ROI_DUAL_SECONDS=0.676897
REAL_VS_SYNTHETIC_DUAL_RATIO=0.9867
```

Reale Blockhochrechnung:

```text
REAL_SINGLE_SECONDS=0.816552
REAL_DUAL_SECONDS=0.676897
TRANSFORMER_SECONDS_PER_STEP_ESTIMATE=19.7155
FOUR_STEP_TRANSFORMER_ESTIMATE=78.8621
ESTIMATE_ONLY=YES
```

Final:

```text
REAL_FLUX2_DUAL_ARCHITECTURE_GATE=PASS
```

## Full-Stack-Versuch – 5 Dual Blocks in einem Graph zu groß

Erste Produkt-Grapharchitektur:

```text
GRAPH_DUAL_ALL
  transformer_blocks.0..4

GRAPH_SINGLE_00_04
GRAPH_SINGLE_05_09
GRAPH_SINGLE_10_14
GRAPH_SINGLE_15_19
```

Alle fünf ONNX-Exports und alle fünf QAI-Hub-Compiles waren erfolgreich.

DLC-Größen:

```text
GRAPH_DUAL_ALL≈4.908 GB

GRAPH_SINGLE_00_04≈2.454 GB
GRAPH_SINGLE_05_09≈2.454 GB
GRAPH_SINGLE_10_14≈2.454 GB
GRAPH_SINGLE_15_19≈2.454 GB
```

Single-Chunk-Context:

```text
GRAPH_SINGLE_00_04 HTP_CONTEXT=PASS
CONTEXT_BYTES=1272422400
SPILL_BYTES=2140645376
FILL_BYTES=715237376
```

`GRAPH_DUAL_ALL` scheiterte erst beim Context-Binary-Speichern an einem persistenten Weight-Buffer:

```text
Error allocating buffer
Failed to allocate a buffer of size 2455764992
Failed to allocate buffer for weights
Could not allocate persistent weights buffer
QnnContext_getBinary: bad allocation
```

Wichtig:

- QAI-Compile selbst PASS.
- HTP-Graph-Preparation lief bis 100 %.
- Blocker war die persistente Weight-Buffer-Größe, nicht ein FLUX-Operatorproblem.

Der erste Full-Stack-Gate endete daher:

```text
ALL_LORA_FUSED=YES
ALL_SINGLE_CHUNK_ONNX=PASS
ALL_QAI_COMPILES=PASS
ALL_HTP_CONTEXTS=FAIL
FULL_25_BLOCK_HTP_EXECUTION=FAIL
REAL_FULL_BLOCK_STACK_GATE=FAIL
```

## Speicherfix – Dual-Stream 3+2 Split

`GRAPH_DUAL_ALL` wurde ausschließlich in zwei Teilgraphen geschnitten:

```text
GRAPH_DUAL_00_02
transformer_blocks.0..2

GRAPH_DUAL_03_04
transformer_blocks.3..4
```

Die vier Single-Chunks blieben unverändert.

Wichtige Korrektur:

- Ein 3-Dual-Block-DLC liegt nicht unter 2,5 GB.
- Entscheidend ist die persistente FP16-Weight-Buffer-Größe.
- 3 Dual Blocks liegen bei ca. 1,47 GB reinen FP16-Gewichten.
- 2 Dual Blocks liegen bei ca. 0,98 GB.
- Damit ist der 3+2-Split für das beobachtete HTP-Allokationslimit passend.

## Vollständiger echter 25-Block-Denoising-Schritt auf HTP – PASS

Finale Architektur:

```text
GRAPH_DUAL_00_02
GRAPH_DUAL_03_04

CPU: nur Tensor-Concat / Orchestrierung

GRAPH_SINGLE_00_04
GRAPH_SINGLE_05_09
GRAPH_SINGLE_10_14
GRAPH_SINGLE_15_19
```

Damit:

```text
TOTAL_HTP_CONTEXTS=6
REAL_DUAL_BLOCKS=5
REAL_SINGLE_BLOCKS=20
ALL_LORA_FUSED=YES
```

Finaler Gate:

```text
FLUX2_REAL_ROI_25_BLOCK_EXECUTION_GATE

DUAL_SPLIT=3+2

DUAL_00_02_ONNX=PASS
DUAL_03_04_ONNX=PASS

DUAL_00_02_QAI=PASS
DUAL_03_04_QAI=PASS

DUAL_00_02_HTP_CONTEXT=PASS
DUAL_03_04_HTP_CONTEXT=PASS

SINGLE_CONTEXTS_READY=4/4
TOTAL_HTP_CONTEXTS_READY=6/6

FULL_25_BLOCK_HTP_EXECUTION=PASS
REAL_25_BLOCK_GATE=PASS
```

Hardware-Profiling:

```text
GRAPH_DUAL_00_02:
DLC=2944982536 Bytes
CONTEXT=1488543744 Bytes
NPU=2.215292 s

GRAPH_DUAL_03_04:
DLC=1963297204 Bytes
CONTEXT=992546816 Bytes
NPU=1.480281 s

CPU Tensor Concat:
≈0.021400 s

GRAPH_SINGLE_00_04:
DLC=2453988868 Bytes
CONTEXT=1272422400 Bytes
NPU=4.673072 s

GRAPH_SINGLE_05_09:
DLC=2453988868 Bytes
CONTEXT=1272422400 Bytes
NPU=4.568578 s

GRAPH_SINGLE_10_14:
DLC=2453988836 Bytes
CONTEXT=1272422400 Bytes
NPU=4.536819 s

GRAPH_SINGLE_15_19:
DLC=2453988868 Bytes
CONTEXT=1272422400 Bytes
NPU=4.642842 s
```

Gesamt:

```text
TOTAL_DUAL_NPU_SECONDS=3.695573
TOTAL_SINGLE_NPU_SECONDS=18.421311

MEASURED_ONE_STEP_NPU_SECONDS=22.116884
TOTAL_25_BLOCK_WALL_SECONDS=53.469927
HOST_ORCHESTRATION_AND_GRAPH_OVERHEAD_SECONDS=31.353043

FOUR_STEP_TRANSFORMER_ESTIMATE=88.467536
FOUR_STEP_TRANSFORMER_ESTIMATE_ONLY=YES
```

Die gemessene reale NPU-Zeit liegt damit ca. 12 % über der isolierten Block-Hochrechnung von 19,7155 s.

Numerische End-to-End-Abweichung gegenüber der PyTorch-Referenz:

```text
FINITE=True
MAE=0.127748
MAX_ABS_ERROR=20.000000
RMSE=0.220919
COSINE_SIMILARITY=0.999998
NUMERICAL_MATCH=REVIEW
```

Interpretation:

- Cosine Similarity bleibt extrem hoch.
- MAE und Max-Abweichung zeigen sichtbare Akkumulation über 25 Blöcke.
- Nicht weiter an Hidden-State-Grenzwerten forschen.
- Das reale Bild entscheidet jetzt, ob diese Akkumulation visuell relevant ist.

Aktuelle Einordnung:

```text
FLUX2_TRANSFORMER_TECH_PASS=YES
FLUX2_REAL_25_BLOCK_HTP=PASS
FLUX2_FULL_STACK_NUMERICAL_STATUS=REVIEW
FLUX2_FUNCTION_PASS_ON_SNAPDRAGON=NOT_YET
FLUX2_PRODUCT_PASS=NOT_YET
```

## Host-/Graph-Overhead als spätere Optimierungsbaustelle

Ein Denoising-Schritt:

```text
NPU_ACCELERATOR=22.116884 s
WALL=53.469927 s
OVERHEAD≈31.353043 s
```

Das ist für den ersten echten Bildtest akzeptiert.

Erst wenn die Bildqualität auf NPU PASS ist, soll ein persistenter Runtime-Worker/Context-Lifecycle entwickelt werden, um Context-Load-/Graph-Switch-/Host-Overhead zu reduzieren.

Keine Performance-Optimierung vor dem ersten echten NPU-Bild.

## Disk-Space-Krise und Bereinigung

Während der Full-Stack-Arbeiten sank der freie Platz auf C: zeitweise auf:

```text
C_FREE_BEFORE_GB=0.60
```

Ein erster PowerShell-Löschblock wurde wegen interaktiver `if`/`else`-Eingabe nicht ausgeführt; danach waren noch ca. 0,59 GB frei.

Danach wurden gezielte Temp-/PoC-Bereinigungen veranlasst. Der erfolgreiche aktuelle 3+2-Stand und das eigentliche FLUX-Modell sollten dabei geschützt bleiben:

```text
BEHALTEN:
C:\SnapdragonAI\models\flux2_klein_4b
C:\SnapdragonAI\temp\flux2_real_roi_25block_3plus2_20260905_180748
```

Überholte FLUX-PoC-Familien wurden als löschbar klassifiziert, darunter u. a.:

```text
flux2_attention_core_poc_*
flux2_single_block_poc_*
flux2_dual_block_poc_*
flux2_single_block_w8a16_poc_*
flux2_w8a16_rescue_*
flux2_roi_single_block_poc_*
flux2_roi_dual_block_poc_*
flux2_real_weight_single_roi_*
flux2_real_weight_dual_roi_*
flux2_real_roi_full_stack_*
```

Keine `.git`-Packs oder produktive Modellbestände manuell löschen.

## Vollständige lokale FLUX.2-Komponenten für den ersten Bildlauf vorhanden

Nach der Bereinigung wurden die noch fehlenden offiziellen Komponenten heruntergeladen.

Lokaler Basisordner:

```text
C:\SnapdragonAI\models\flux2_klein_4b
```

Vorhanden:

```text
TRANSFORMER
TEXT_ENCODER / QWEN3
TOKENIZER
VAE
SCHEDULER
OBJECT-REMOVAL LORA
```

Bestätigte Größen:

```text
TEXT_ENCODER_PRESENT=True
TEXT_ENCODER_BYTES=8045016597

VAE_PRESENT=True
VAE_BYTES=168121699

TOKENIZER_PRESENT=True
TOKENIZER_BYTES=15882232

SCHEDULER_PRESENT=True

FLUX2_E2E_COMPONENT_DOWNLOAD=PASS
```

Nach dem Download:

```text
C_FREE_GB_AFTER=42.09
```

Damit ist aktuell wieder ausreichend Platz für den ersten echten E2E-NPU-Bildlauf vorhanden.

## Wichtige Korrektur für den echten Qualitätslauf: Prompt-Tokens

Die ROI-Performance-PoCs verwendeten:

```text
TEXT_TOKENS=32
TOTAL_SEQUENCE=1952
```

Das war ausschließlich ein Performance-Vertrag.

Für den echten Qualitätslauf muss der Referenzvertrag verwendet werden:

```text
PROMPT_TOKENS=128
```

Bei ROI 384×640:

```text
Noise Tokens=960
Reference Image Tokens=960
Prompt Tokens=128

TOTAL_ATTENTION_SEQUENCE=2048
```

Daher müssen die für den ersten echten Qualitätslauf benötigten vollständigen Transformer-Graphs statisch mit `S=2048` erzeugt werden.

Die bewiesene 3+2/5er-Chunk-Architektur bleibt gleich; nur der echte Promptvertrag wird verwendet.

## Verbindlicher nächster FLUX-Schritt

Keine weiteren Block-PoCs.

Nächster Schritt ist der erste reale End-to-End-Bildlauf:

```text
echtes Person-Bild
+ echte Maske
→ ROI aus Maske
→ 384×640 Bucket
→ echtes Prompt-Encoding mit Qwen3, 128 Tokens
→ VAE Encoder auf HTP
→ FLUX.2 Transformer auf HTP
   6 Contexts
   4 Denoising-Schritte
→ VAE Decoder auf HTP
→ Outside-Mask Original bitgenau zurück
→ PNG
→ visuelle Qualitätsprüfung
```

Bekannter Prompt:

```text
Remove the highlighted object from the scene
```

Bekannter Referenzfall:

```text
case_person_input.jpg
case_person_mask.png
```

Diese Dateien sollen read-only gesucht und nur verwendet werden, wenn lokal vorhanden. Keine Ersatzbilder verwenden.

Für den ersten realen Lauf:

- VAE Encoder/Decoder Core-Inferenz: NPU/HTP.
- Transformer: NPU/HTP.
- 4 Denoising-Schritte.
- CPU nur für erlaubte Orchestrierung.
- Nach erfolgreichem PNG **sofort stoppen**.
- Keine Performanceoptimierung und keine Varianten vor manueller Bildprüfung.

Zielartefakte:

```text
flux2_person_removed_npu.png
flux2_person_comparison_npu.png
```

Finale Bewertung danach:

```text
TECH_PASS
FUNCTION_PASS
PRODUCT_PASS
```

erst anhand des echten NPU-Bilds.

## AI PHOTO RESTORE – als nächster Produktblock nach FLUX festgelegt

Holger möchte mit HK NPU STUDIO außerdem aus sehr kleinen, schlechten oder alten Bildern hochwertige große Bilder erzeugen, einschließlich Schwarzweiß-Kolorierung.

Zielbeispiel:

```text
sehr kleines / pixeliges / unscharfes Foto
→ hochwertig restauriertes Bild
→ plausible Detailrekonstruktion
→ optional Schwarzweiß zu Farbe
→ großes scharfes Endbild
```

Wichtig:

- RealESRGAN allein reicht dafür nicht, weil bei sehr kleinen Bildern echte Bildinformationen fehlen.
- Zusätzlich ist generative Restaurierung/Detailrekonstruktion notwendig.
- Gesichtserhalt muss ein eigenes Qualitäts-Gate sein; die KI darf nicht einfach eine andere Person erzeugen.

Nach FLUX verbindlich als nächster Produktblock:

```text
HK NPU STUDIO – AI PHOTO RESTORE

1. DiffBIR
   → generative Restaurierung / Detailrekonstruktion

2. DDColor
   → Schwarzweiß → Farbe

3. RealESRGAN
   → finales 2×/4× Upscaling

4. Face Identity Preservation
   → Gesicht maximal erhalten
```

Geplanter Produktworkflow:

```text
schlechtes / kleines Bild
→ Grundrestaurierung
→ generative Detailrekonstruktion
→ Identity Preservation
→ Colorization
→ Super Resolution
→ Final Sharpen / Detail Merge
```

Zwei spätere Modi sind sinnvoll:

```text
Faithful Restoration
→ Identität und Originalstruktur maximal erhalten

Maximum Detail
→ stärkere generative Rekonstruktion
```

Dieser Produktblock startet **erst nachdem FLUX Object Removal den echten NPU-Bild-Gate abgeschlossen hat**.

## Aktueller Git-/Arbeitsbaumhinweis

Während der FLUX-PoCs wurde wiederholt bestätigt, dass die Experimente nur unter `C:\SnapdragonAI\temp` und `C:\SnapdragonAI\models\flux2_klein_4b` arbeiteten und keine Produktdateien absichtlich verändert wurden.

Zuletzt gemeldeter HEAD in den Real-Weight-Sprints:

```text
ee284600b141266e6a87197a21141f3d28a28ab5
```

Der Arbeitsbaum enthielt bereits vor den FLUX-Sprints mehrere modified/untracked Dateien. Diese wurden in den FLUX-Sprints nicht verändert.

Wichtig:

- `git status --short` vor/nach den FLUX-Sprints war laut den jeweiligen Berichten identisch.
- Bestehende modified/untracked Dateien nicht bereinigen oder stagen.
- Kein Build, Installer, Commit oder Push wurde durch die FLUX-Arbeit am 5. September durchgeführt.

## Statusflags – Tagesabschluss 5. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

FLUX2_KLEIN_FIXED_PRODUCT_MODEL=True
FLUX2_BASE_LICENSE=APACHE_2_0
FLUX2_OBJECT_REMOVE_LORA_VALID=True
FLUX2_OBJECT_REMOVE_LORA_SHA256=dc197de62e174863f83fc4052465603f4389de7c3a78e17f3d41a1f6f11488ec

FLUX2_REFERENCE_PERSON_REMOVAL_QUALITY=PASS
FLUX2_REFERENCE_OUTSIDE_MASK_BIT_EXACT=True

FLUX2_ATTENTION_CORE_HTP=PASS
FLUX2_SYNTHETIC_SINGLE_BLOCK_HTP=PASS
FLUX2_SYNTHETIC_DUAL_BLOCK_HTP=PASS

FLUX2_W8A16_QAI_COMPILE=PASS
FLUX2_W8A16_HTP_CONTEXT=BLOCKED_QNN_2_47
FLUX2_W8A16_FURTHER_RESCUE=False

FLUX2_ROI_BUCKET=384x640
FLUX2_ROI_SYNTHETIC_SINGLE_NPU_SECONDS=0.861
FLUX2_ROI_SYNTHETIC_SINGLE_SPEEDUP=5.356x
FLUX2_ROI_SYNTHETIC_DUAL_NPU_SECONDS=0.686
FLUX2_ROI_SYNTHETIC_DUAL_SPEEDUP=4.125x

FLUX2_REAL_TRANSFORMER_LOCAL=True
FLUX2_REAL_LORA_LOCAL=True
FLUX2_REAL_SINGLE_BLOCK_HTP=PASS
FLUX2_REAL_SINGLE_NPU_SECONDS=0.816552
FLUX2_REAL_DUAL_BLOCK_HTP=PASS
FLUX2_REAL_DUAL_NPU_SECONDS=0.676897

FLUX2_REAL_25_BLOCK_HTP=PASS
FLUX2_REAL_25_BLOCK_CONTEXTS=6
FLUX2_REAL_DUAL_SPLIT=3+2
FLUX2_REAL_SINGLE_CHUNKS=4

FLUX2_REAL_ONE_STEP_NPU_SECONDS=22.116884
FLUX2_REAL_ONE_STEP_WALL_SECONDS=53.469927
FLUX2_REAL_ONE_STEP_OVERHEAD_SECONDS=31.353043

FLUX2_REAL_25_BLOCK_COSINE=0.999998
FLUX2_REAL_25_BLOCK_MAE=0.127748
FLUX2_REAL_25_BLOCK_MAX_ABS=20.0
FLUX2_FULL_STACK_NUMERICAL_STATUS=REVIEW

FLUX2_FOUR_STEP_TRANSFORMER_ESTIMATE_SECONDS=88.467536
FLUX2_FOUR_STEP_ESTIMATE_ONLY=True

FLUX2_TEXT_ENCODER_LOCAL=True
FLUX2_VAE_LOCAL=True
FLUX2_TOKENIZER_LOCAL=True
FLUX2_SCHEDULER_LOCAL=True
FLUX2_E2E_COMPONENT_DOWNLOAD=PASS
C_FREE_GB_AT_END=42.09

FLUX2_NEXT_GATE=FIRST_REAL_NPU_OBJECT_REMOVAL_IMAGE
FLUX2_NEXT_PROMPT_TOKENS=128
FLUX2_NEXT_TOTAL_SEQUENCE=2048
FLUX2_FUNCTION_PASS_ON_SNAPDRAGON=PENDING_REAL_IMAGE
FLUX2_PRODUCT_PASS=PENDING_REAL_IMAGE

AI_PHOTO_RESTORE_NEXT_AFTER_FLUX=True
AI_PHOTO_RESTORE_DIFFBIR_PLANNED=True
AI_PHOTO_RESTORE_DDCOLOR_PLANNED=True
AI_PHOTO_RESTORE_REALESRGAN_PLANNED=True
AI_PHOTO_RESTORE_FACE_IDENTITY_GATE_REQUIRED=True

BUILD_5_SEPTEMBER=False
INSTALLER_5_SEPTEMBER=False
GIT_ADD_5_SEPTEMBER=False
COMMIT_5_SEPTEMBER=False
PUSH_5_SEPTEMBER=False
```

## Verbindlicher Einstieg am nächsten Arbeitstag

Nicht erneut:

- Modellkandidaten suchen;
- W8A16 reparieren;
- synthetische Single-/Dual-Block-PoCs wiederholen;
- 25-Block-Performance erneut hochrechnen.

Direkt fortsetzen mit:

```text
FLUX.2-klein
→ erster echter NPU-Object-Removal-Bildlauf
→ echter Promptvertrag mit 128 Tokens / S=2048
→ VAE Encoder HTP
→ 6 Transformer-Contexts HTP
→ 4 Denoising-Schritte
→ VAE Decoder HTP
→ Outside Mask bitgenau Original
→ Comparison PNG
→ manuelle visuelle Qualitätsentscheidung
```

Erst wenn das reale NPU-Bild qualitativ PASS ist:

1. persistenten Runtime-/Context-Worker zur Reduktion des ca. 31-s-Host-/Graph-Overheads entwickeln;
2. danach Produktintegration in HK NPU STUDIO;
3. anschließend den festgelegten Produktblock `AI PHOTO RESTORE` beginnen.

## Handover-Übernahme

Diese vollständige, nur unten ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt, neu aufgebaut oder durch eine separate Ergänzungsdatei ersetzt werden.

# CHATGPT_HANDOVER – Ergänzung 6. September 2026 – FLUX.2-klein Full-Frame, Kaggle-Contract-Audit und Person-Removal-Endstand

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Neue verbindliche Arbeitsregeln aus dem 6.-September-Sprint

- Holger möchte bei **jedem zukünftigen Antigravity-/Codex-/Kaggle-/NPU-Sprint vor dem Start** zusätzlich immer sehen:
  1. Ziel,
  2. realistische erwartete Dauer,
  3. erwarteten Speicherbedarf,
  4. klare Stop-/Abbruchgrenze.
- Bei laufenden längeren Sprints soll ChatGPT in jeder Antwort einen sichtbaren Zeitstand mitführen (`SPRINT-ZEIT`) und die verstrichene Zeit sowie Restspanne aktualisieren, wenn ein neuer Screenshot oder Zwischenstand kommt.
- Keine langen Wartephasen ohne Fortschrittsgate: bei einzelnen Schritten typischerweise nach 45–60 Minuten ohne neue Artefakte/Logs Status prüfen; nach >90 Minuten ohne Fortschritt nicht blind weiterlaufen lassen.
- Holger möchte nicht selbst alle Speicher-/Risikoaspekte mitdenken müssen; ChatGPT soll diese vorab prüfen und explizit benennen.
- Weiterhin gilt strikt: technische PASS-Meldungen sind kein Funktions- oder Produktnachweis. Entscheidend ist das sichtbare Ergebnis.

## Ausgangslage des Tages

Der 384×640-ROI-Pfad von FLUX.2-klein war technisch auf HTP/NPU lauffähig, entfernte die Person aber nicht zuverlässig. Ein exakter 384×640-Kaggle-GPU-Referenzlauf wurde deshalb durchgeführt, um zu klären, ob die Ursache im ROI-Kontext oder im NPU-Trajektorienpfad liegt.

Kaggle-Umgebung beim Referenzlauf:

```text
torch=2.10.0+cu128
torchao=0.18.0
peft=0.19.1
diffusers=0.37.1
GPU=Tesla T4
```

Warnung:

```text
Skipping import of cpp extensions due to incompatible torch version.
Please upgrade to torch >= 2.11.0 (found 2.10.0+cu128).
```

Diese Warnung war nicht blockierend. LoRA wurde erfolgreich geladen und mit Scale 1.1 fusioniert.

## 384×640 Kaggle-Referenzlauf

Ergebnis:

```text
RETURN_CODE=0
LORA=PASS
INFERENCE=PASS
WORK_SIZE=384x640
STEPS=4
PROMPT=Remove the highlighted object from the scene
OUTSIDE_MASK_BIT_EXACT=True
```

Erzeugte Dateien:

```text
/kaggle/working/flux2_kaggle_decoded_roi_384x640.png
/kaggle/working/flux2_kaggle_roi384_result.png
/kaggle/working/flux2_kaggle_roi384_comparison.png
/kaggle/working/flux2_kaggle_roi384_fullframe_comparison.png
```

Visuell blieb die Person auch im 384×640-Kaggle-PyTorch-Lauf sichtbar.

Daraus wurde zunächst korrekt abgeleitet:

```text
ROI_CONTEXT_CAUSE=CONFIRMED
```

Der 384×640-Pfad wurde funktional verworfen; kein weiterer ROI-Compile-/NPU-Sprint sollte erfolgen.

## Full-Frame-Migrationsplan 672×960

Antigravity leitete den statischen Full-Frame-Vertrag ab:

```text
REFERENCE_WORK_SIZE=672x960
VAE_INPUT_SHAPE=[1,3,960,672]
VAE_LATENT_SHAPE=[1,32,120,84]
PATCHIFIED_LATENT_SHAPE=[1,128,60,42]
TOKENS_PER_IMAGE=2520
IMAGE_STREAM_TOKENS=5040
PROMPT_TOKENS=128
TOTAL_ATTENTION_SEQUENCE=5168
```

Positions-/Timestep-Vertrag:

```text
txt_ids=[128,4]
img_ids noise T=0
img_ids reference T=10
Timestep=COS_THEN_SIN
Scheduler=FlowMatchEulerDiscreteScheduler
Seed=20260905
Steps=4
```

Beibehaltener Split:

```text
Dual:   3 + 2
Single: 5 + 5 + 5 + 5
```

Speicherplan:

```text
C_FREE_GB≈26.63
ESTIMATED_REQUIRED_FREE_GB≈12.0
EXPECTED_CONTEXT_TOTAL_GB≈7.4 (Estimate)
```

Wichtig: nur sequentielles Export→Compile→Context→Cleanup, niemals alle ONNX/DLC-Artefakte gleichzeitig halten.

## Full-Frame-Context-Sprint 672×960

Der Sprint wurde nach einer Antigravity-Netzwerkunterbrechung **in place** fortgesetzt, nicht neu gestartet.

Die Unterbrechung trat nach erfolgreichem QAI-Compile von `GRAPH_SINGLE_00_04` bzw. während späterer Download-/Context-Schritte auf. Der Resume-Sprint rekonstruierte zuerst vorhandene Artefakte und übersprang bereits valide Contexts.

Finaler Report:

```text
GRAPH_DUAL_00_02_CONTEXT=PASS
GRAPH_DUAL_03_04_CONTEXT=PASS
GRAPH_SINGLE_00_04_CONTEXT=PASS
GRAPH_SINGLE_05_09_CONTEXT=PASS
GRAPH_SINGLE_10_14_CONTEXT=PASS
GRAPH_SINGLE_15_19_CONTEXT=PASS
VAE_ENCODER_CONTEXT=PASS
VAE_DECODER_CONTEXT=PASS

DUAL_CONTEXTS_READY=2/2
SINGLE_CONTEXTS_READY=4/4
VAE_CONTEXTS_READY=2/2
TOTAL_CONTEXTS_READY=8/8

FULLFRAME_CONTEXT_GATE=PASS
TECH_PASS=YES
FUNCTION_PASS=NOT_YET
PRODUCT_PASS=NOT_YET
```

Valide Context-Dateien und Größen:

```text
vae_encoder.serialized.bin.bin            94,740,480 bytes
vae_decoder.serialized.bin.bin           149,184,512 bytes
GRAPH_DUAL_00_02.serialized.bin.bin    1,529,237,504 bytes
GRAPH_DUAL_03_04.serialized.bin.bin    1,020,919,808 bytes
GRAPH_SINGLE_00_04.serialized.bin.bin  1,416,310,784 bytes
GRAPH_SINGLE_05_09.serialized.bin.bin  1,416,310,784 bytes
GRAPH_SINGLE_10_14.serialized.bin.bin  1,416,310,784 bytes
GRAPH_SINGLE_15_19.serialized.bin.bin  1,416,310,784 bytes
```

Gesamtgröße:

```text
TOTAL_CONTEXT_BYTES=8459325440
```

Freier Speicher nach Abschluss:

```text
C_FREE_GB=22.77
```

Alle großen temporären ONNX-/DLC-Dateien wurden nach erfolgreicher Context-Erzeugung wie geplant entfernt. Fertige `.serialized`-Contexts, Modelle, LoRA, Referenzbilder, Skripte und Logs blieben erhalten.

## Erster realer 672×960 Full-Frame-NPU-Bildlauf

Exakter NPU-Pfad:

```text
8/8 HTP Contexts
VAE Encoder HTP
4 Transformer-Schritte HTP
VAE Decoder HTP
672x960 Work Size
Prompt=Remove the highlighted object from the scene
Seed=20260905
LoRA Scale=1.1
```

Artefakte:

```text
flux2_672x960_npu_raw.png
flux2_672x960_npu_result.png
flux2_672x960_npu_comparison.png
```

Technisch:

```text
TECH_PASS=YES
OUTSIDE_MASK_BIT_EXACT=True
```

Visuell:

- Person wurde nicht entfernt.
- Person wurde stark verändert / in eine andere menschliche Figur umgeneriert.
- Damit:

```text
FUNCTION_PASS=NO
PRODUCT_PASS=NO
```

Zu diesem Zeitpunkt war klar, dass Full Frame allein die Funktion nicht löst.

## Codex-Contract-Audit des erfolgreichen Kaggle-Laufs

Holger schlug zurecht vor, den früher erfolgreichen Kaggle-Pfad durch Codex gegen den NPU-Pfad zu diffen.

Codex-Report zunächst:

```text
KAGGLE_REFERENCE_RECONSTRUCTED=PARTIAL
MISSING_CONDITIONING_STEP=UNPROVEN
NPU_TRANSFORMER_CONTRACT=MATCH
NPU_CONTEXTS_REUSABLE=YES
RECOMPILE_REQUIRED=NO
```

Grund: Der konkrete `pipe(...)`-Aufruf des erfolgreichen 672×960-Laufs war lokal nicht dokumentiert.

Der später rekonstruierte 384×640-ROI-Kaggle-Test verwendete nachweislich **kein** Highlight, war aber nicht identisch mit dem ursprünglichen erfolgreichen 672×960-Notebook.

## Entscheidend: Originaler erfolgreicher Kaggle-Code wurde gefunden

Holger fand das alte Kaggle-Notebook und stellte den vollständigen erfolgreichen Testcode bereit.

Der fehlende Conditioning-Schritt war damit **bewiesen**:

```python
highlight_np = orig_np.astype(np.float32)

red = np.zeros_like(highlight_np, dtype=np.float32)
red[..., 0] = 255.0

highlight_alpha = 0.72

highlight_np[mask_bin] = (
    highlight_np[mask_bin] * (1.0 - highlight_alpha)
    + red[mask_bin] * highlight_alpha
)

highlight_np = np.clip(highlight_np, 0, 255).astype(np.uint8)
highlight_image = Image.fromarray(highlight_np)
```

Danach wurde nicht das Originalbild, sondern das markierte Bild an FLUX übergeben:

```python
result = pipe(
    image=work_image,
    prompt="Remove the highlighted object from the scene",
    num_inference_steps=4,
    guidance_scale=1.0,
).images[0]
```

Dabei war:

```text
work_image = highlight_image
```

Damit:

```text
MISSING_CONDITIONING_STEP=YES
EXACT_MISSING_STEP=72-percent red highlight inside binary removal mask before VAE encoding
NPU_CONTEXTS_REUSABLE=YES
RECOMPILE_REQUIRED=NO
EXPECTED_FIX_SCOPE=PREPROCESSING_ONLY
```

Zusätzlich war auch der reale erfolgreiche Kaggle-Compositing-Vertrag anders als zuvor rekonstruiert:

```text
MaxFilter(15)
GaussianBlur(3)
```

und nicht:

```text
MaxFilter(29)
Feather=0
```

## Kontrollierter NPU-Retest mit rotem Highlight

Die vorhandenen 8/8 Full-Frame-HTP-Contexts wurden unverändert wiederverwendet; kein Export und kein Recompile.

Highlight-Vertrag:

```text
Color=(255,0,0)
Alpha=0.72
nur innerhalb der binären Personenmaske
```

Artefakte:

```text
flux2_npu_highlight_input.png
flux2_npu_highlight_raw.png
flux2_npu_highlight_result.png
flux2_npu_highlight_comparison.png
```

Visueller Befund:

- Kopf, Schultern, Arme und Oberkörper wurden vollständig entfernt.
- Himmel/Meereshorizont wurden kohärent rekonstruiert.
- Verbleibende Körperanteile lagen dort, wo die ursprüngliche Maske die Beine nur unvollständig abdeckte.

Zwischenstatus:

```text
TECH_PASS=YES
RED_HIGHLIGHT_CONDITIONING=CONFIRMED
FUNCTION_PASS=PARTIAL
PRODUCT_PASS=NO
```

Dieser Lauf bestätigte den roten Highlight-Conditioning-Mechanismus eindeutig.

## Finaler Retest mit vollständig deckender Personenmaske

Ziel: komplette Person einschließlich Beine/Füße vollständig markieren, sonst **nichts** ändern.

Verwendeter Masken-BBox:

```text
MASK_COMPLETE_BBOX=(207,289,411,841)
```

Artefakte:

```text
flux2_person_mask_complete.png
flux2_npu_highlight_complete_input.png
flux2_npu_complete_raw.png
flux2_npu_complete_result.png
flux2_npu_complete_comparison.png
```

Technisch:

```text
CONTEXTS_REUSED=8/8
TECH_PASS=YES
NaN/Inf=NONE
C_FREE_GB≈23.56
```

Visuell:

- Statt vollständiger Entfernung regenerierte das Modell die Person erneut.
- Die Person erhielt u. a. eine rötliche Hauttönung.
- Der Erfolg des engeren Highlight-Runs war damit nicht robust auf die vollständig deckende Maske übertragbar.

Finale Funktionsbewertung für **Person Removal mit genau dieser FLUX.2-klein + Object-Removal-LoRA-Konfiguration**:

```text
TECH_PASS=YES
FUNCTION_PASS=NO
PRODUCT_PASS=NO
```

Begründung:

- Enge Highlight-Maske: Teilentfernung erfolgreich.
- Vollständige Highlight-Maske: Person wird erneut generiert.
- Verhalten ist nicht ausreichend reproduzierbar und nicht produktstabil.

## Aktuelle Entscheidung zu FLUX.2-klein

FLUX.2-klein wird **nicht als NPU-Modell an sich verworfen**.

Die technisch aufwendig erarbeitete NPU-Infrastruktur bleibt wertvoll:

- 8/8 Full-Frame HTP V73 Contexts;
- VAE Encoder/Decoder NPU;
- alle 25 Transformer-Blöcke NPU;
- Full-Frame S=5168;
- korrigierte txt_ids/img_ids;
- `COS_THEN_SIN` Timestep;
- FlowMatch-Scheduler-Vertrag;
- LoRA-Fusion und Prompt-Vertrag;
- reales 4-Step-NPU-E2E technisch PASS.

Aber für die konkrete Funktion:

```text
Person aus Bild entfernen
```

ist der aktuelle FLUX.2-klein + `fal/flux-2-klein-4B-object-remove-lora`-Pfad **nicht robust genug für HK NPU STUDIO**.

Keine weiteren Blindtests mit:

- anderen Seeds,
- anderen Step-Zahlen,
- anderen Alpha-Werten,
- anderen Farben,
- weiteren Maskenvarianten,
- erneutem Compile,
- neuen Context-Splits

ohne einen neuen klar belegten Grund.

## Was mit FLUX weiterhin sinnvoll sein kann

Die NPU-Portierung kann später für andere generative Bildfunktionen wiederverwendet werden, insbesondere dort, wo kreative Rekonstruktion erwünscht ist, z. B.:

- Objekt ersetzen;
- Hintergrund ändern;
- Outpainting / Bild erweitern;
- generative Retusche;
- Stil-/Look-Änderungen;
- Objekte hinzufügen;
- generative Bildverbesserung.

Für diese Funktionen muss jeweils zuerst ein sichtbarer Referenz-Qualitätsnachweis erfolgen, bevor weiterer Produkt-/NPU-Aufwand investiert wird.

## Harte Auswahlregel für künftige Person-/Objektentferner

Bevor ein neuer Kandidat auf NPU portiert wird, muss er zuerst drei Eintrittsgates erfüllen:

```text
1. sichtbare Referenzqualität auf Holgers echtem Testbild
2. kommerziell / produktseitig nutzbare Lizenz
3. realistische QNN/HTP/NPU-Portierbarkeit
```

Erst wenn **alle drei** plausibel sind, darf ein großer Portierungs-/Compile-Sprint beginnen.

MAT wurde kurz als möglicher Qualitätskandidat diskutiert, aber aufgrund der Research-only-Lizenz für den HK-NPU-STUDIO-Produktpfad sofort verworfen. Solche Kandidaten künftig vor technischem Aufwand bereits am Lizenz-Gate aussortieren.

## AI PHOTO RESTORE bleibt nächster großer Produktblock

Nach Abschluss bzw. Stopp des aktuellen Person-Removal-Pfads bleibt der bereits festgelegte nächste Produktblock bestehen:

```text
HK NPU STUDIO – AI PHOTO RESTORE

1. DiffBIR
   -> generative Restaurierung / Detailrekonstruktion

2. DDColor
   -> Schwarzweiß -> Farbe

3. RealESRGAN
   -> finales 2x/4x Upscaling

4. Face Identity Preservation
   -> Identität maximal erhalten
```

Wichtig:

- verlorene Details werden generativ plausibel rekonstruiert, nicht tatsächlich „wiedergefunden“;
- Face Identity Preservation ist ein eigenes hartes Qualitäts-Gate;
- NPU-only bleibt für KI-Inferenz verbindlich.

## Git-/Build-/Produktdatei-Status 6. September

Während der heutigen FLUX-Full-Frame-, Kaggle- und NPU-Retests wurden nach dokumentiertem Stand keine Produktdateien absichtlich geändert.

Kein:

```text
Build
Installer
git add
Commit
Push
```

Die Arbeit blieb in vorhandenen Modell-/Temp-/Context-/Referenzbereichen.

Bestehende dirty/untracked Dateien weiterhin nicht anfassen.

## Statusflags – Tagesabschluss 6. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

FLUX2_FULLFRAME_WORK_SIZE=672x960
FLUX2_FULLFRAME_TOTAL_SEQUENCE=5168
FLUX2_FULLFRAME_CONTEXTS_READY=8/8
FLUX2_FULLFRAME_CONTEXT_GATE=PASS
FLUX2_FULLFRAME_CONTEXT_BYTES=8459325440

FLUX2_VAE_ENCODER_HTP=PASS
FLUX2_VAE_DECODER_HTP=PASS
FLUX2_DUAL_CONTEXTS=2/2
FLUX2_SINGLE_CONTEXTS=4/4

FLUX2_KAGGLE_ORIGINAL_CONTRACT_RECOVERED=True
FLUX2_MISSING_CONDITIONING_STEP_FOUND=True
FLUX2_HIGHLIGHT_COLOR=255,0,0
FLUX2_HIGHLIGHT_ALPHA=0.72
FLUX2_HIGHLIGHT_CONDITIONING_CONFIRMED=True
FLUX2_RECOMPILE_REQUIRED_FOR_HIGHLIGHT=False

FLUX2_HIGHLIGHT_PARTIAL_MASK_FUNCTION=PARTIAL_PASS
FLUX2_COMPLETE_MASK_FUNCTION=FAIL
FLUX2_PERSON_REMOVAL_TECH_PASS=True
FLUX2_PERSON_REMOVAL_FUNCTION_PASS=False
FLUX2_PERSON_REMOVAL_PRODUCT_PASS=False

FLUX2_NPU_INFRASTRUCTURE_REUSABLE=True
FLUX2_OTHER_GENERATIVE_FEATURES_POSSIBLE=True

PERSON_REMOVAL_NEXT_MODEL_REQUIRES_REFERENCE_QUALITY_GATE=True
PERSON_REMOVAL_NEXT_MODEL_REQUIRES_COMMERCIAL_LICENSE_GATE=True
PERSON_REMOVAL_NEXT_MODEL_REQUIRES_NPU_PORTABILITY_GATE=True

AI_PHOTO_RESTORE_NEXT_AFTER_PERSON_REMOVE=True
AI_PHOTO_RESTORE_DIFFBIR_PLANNED=True
AI_PHOTO_RESTORE_DDCOLOR_PLANNED=True
AI_PHOTO_RESTORE_REALESRGAN_PLANNED=True
AI_PHOTO_RESTORE_FACE_IDENTITY_GATE_REQUIRED=True

SPRINT_TIME_ESTIMATE_REQUIRED=True
SPRINT_STORAGE_ESTIMATE_REQUIRED=True
SPRINT_STOP_GATE_REQUIRED=True
SPRINT_VISIBLE_ELAPSED_TIME_REQUIRED=True

BUILD_6_SEPTEMBER=False
INSTALLER_6_SEPTEMBER=False
GIT_ADD_6_SEPTEMBER=False
COMMIT_6_SEPTEMBER=False
PUSH_6_SEPTEMBER=False
```

## Verbindlicher Einstieg bei Wiederaufnahme

Nicht erneut blind FLUX-Person-Removal optimieren.

Wenn Person-/Objektentfernung weiterverfolgt wird:

1. nur Kandidaten mit produktgeeigneter Lizenz betrachten;
2. zuerst sichtbarer Referenztest auf demselben echten Bild;
3. erst bei klarer Referenzqualität QNN-/HTP-Portierbarkeit prüfen;
4. erst danach Export/Compile/Context-Arbeit starten.

Alternativ bzw. als nächster bereits festgelegter Produktblock:

```text
AI PHOTO RESTORE
```

mit DiffBIR → DDColor → RealESRGAN → Face Identity Preservation.

Vor jedem neuen Sprint immer Dauer, Speicherbedarf und Stop-Gate nennen.

## Handover-Übernahme

Diese vollständige, nur unten ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt, neu aufgebaut oder durch eine separate Ergänzungsdatei ersetzt werden.

# CHATGPT_HANDOVER – Ergänzung 7. September 2026 – AI PHOTO RESTORE

> Diese Ergänzung setzt die vollständige bestehende Chronik fort. Ältere Inhalte bleiben unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser Abschnitt Vorrang.

## Neue verbindliche Handover-Regel

Ab sofort gilt:

- Sobald Holger eine `CHATGPT_HANDOVER` bereitstellt, wird sie ohne Rückfrage aktualisiert.
- Bestehende Chronik nie kürzen oder ersetzen.
- Den aktuellen Tagesstand ausschließlich unten ergänzen.
- Download-Dateiname immer exakt `CHATGPT_HANDOVER.md`.
- Nach Aktualisierung nur die Datei zum Download bereitstellen, ohne weiteren Kommentar.
- Übernahme weiterhin über `C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd` nach `C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md`.

## Neue wirtschaftliche Arbeitsregel

Nach den mehrtägigen Person-Removal-Versuchen gilt für neue KI-Funktionen verbindlich:

```text
1. Produktnutzen
2. Lizenz
3. sichtbarer Qualitätsbeweis auf echten Testbildern
4. Wiederholbarkeit
5. NPU/QNN-Machbarkeit
6. Performance
7. erst danach Integration
```

Keine große Portierung mehr auf Verdacht.

Jeder Sprint enthält erwartete Dauer, Worst-Case-Zeit, Speicherbedarf und klare Stop-/Abort-Grenzen.

## FLUX.2-klein 4B – Person Removal abgeschlossen

Der zuvor fehlende erfolgreiche Kaggle-Conditioning-Schritt wurde rekonstruiert:

```text
Prompt: Remove the highlighted object from the scene
Steps: 4
Guidance: 1.0
LoRA scale: 1.1
Conditioning: 72 % rotes Highlight innerhalb der Removal-Maske
```

Der erfolgreiche Kaggle-Pfad übergab nicht das unmarkierte Original, sondern ein rot markiertes `work_image`.

Erster kontrollierter NPU-Retest mit rotem Highlight:
- Kopf, Schultern, Arme und Oberkörper entfernt;
- Hintergrund teilweise plausibel;
- Restkörper wegen unvollständiger Maskenabdeckung sichtbar.

Zweiter kontrollierter NPU-Retest mit vollständiger Maske:
- `MASK_COMPLETE_BBOX=(207, 289, 411, 841)`;
- 8/8 HTP-V73-Kontexte technisch fehlerfrei;
- keine NaNs/Infs;
- freier Speicher ca. 23,56 GB;
- Modell regenerierte die Person mit rötlicher Tönung statt sie vollständig zu entfernen.

Final:

```text
TECH_PASS=YES
FUNCTION_PASS=NO
PRODUCT_PASS=NO
FLUX_PERSON_REMOVAL=NO_GO
```

Die vorhandene FLUX-NPU-Plattform und 8/8 Full-Frame-Contexts bleiben erhalten. FLUX kann später für generatives Editieren, Objekt-Ersetzen, Material-/Kleidungsänderungen oder optionalen Generative-Restore genutzt werden, aber nicht mehr als verlässlicher Person-Removal-Pfad.

## Neues priorisiertes Produktziel: AI PHOTO RESTORE

Holgers Ziel:

> Aus einem sehr kleinen, schlechten, ggf. schwarzweißen Foto ein großes, scharfes, farbiges, hochwertiges KI-Bild erzeugen.

Bevorzugte Pipeline:

```text
schlechtes / kleines Schwarzweißbild
→ Restoration / Deblur / Denoise
→ Colorization
→ optional Generative Detail Restore
→ vorhandenes RealESRGAN NPU 2× / 4×
→ hochauflösendes Farbbild
```

RealESRGAN QNN/HTP ist bereits vorhanden und soll wiederverwendet werden.

## Phase 0 – Machbarkeits-Gate

Bevorzugte Kandidaten:

```text
RESTORE=NAFNet-DeBlur
COLORIZATION=DDColor
OPTIONAL_GENERATIVE=FLUX.2-klein-4B
```

Verworfen bzw. nicht als Basis empfohlen:

```text
CodeFormer=NO_GO_NON_COMMERCIAL
MAT=NO_GO_RESEARCH_ONLY
SUPIR=NO_GO_16GB_RISK
DiffBIR=zu schwer für Basisworkflow
DeOldify=Qualität nicht ausreichend
GFPGAN=nur optionaler Face-Restorer
```

Status nach Gegenprüfung:

```text
AI_PHOTO_RESTORE_FEASIBILITY=PROVISIONAL_GO
LICENSE_GATE=PASS
NPU_FEASIBILITY=PASS
REAL_PRODUCT_QUALITY=NOT_YET_PROVEN
PORTING_APPROVAL=NO
```

## Phase 0B – echter 3-Bild-Quality-Gate

Verbindliches Testset:

```text
C:\Users\holge\Desktop\Testbilder\37.jpg
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
C:\Users\holge\Desktop\Testbilder\3.jpg
```

Diese drei Bilder sind ausschließlich Testbilder. Keine Bildgenerierung im Chat mit ihnen.

Case 1 (`37.jpg`, 1277×1231, historisches Schwarzweiß-Familienfoto):

```text
Pipeline=NAFNet-DeBlur -> DDColor
DETAIL_RECOVERY=GOOD
BLUR_REDUCTION=GOOD
NOISE_ARTIFACT_REDUCTION=GOOD
FACE_IDENTITY_PRESERVED=YES
NEW_FACE_HALLUCINATION=NO
STRUCTURE_PRESERVED=YES
COLOR_NATURAL=YES
COLOR_BLEEDING=MINOR
BACKGROUND_PRESERVED=YES
OVERALL_VISIBLE_IMPROVEMENT=YES
CASE_1_OVERALL=PASS
```

Case 2 (`142461_s16323864_5162d47f5655.jpg`, 500×179, kleines Farbfoto):

```text
Pipeline=NAFNet-DeBlur
DETAIL_RECOVERY=GOOD
BLUR_REDUCTION=GOOD
NOISE_ARTIFACT_REDUCTION=GOOD
FACE_IDENTITY_PRESERVED=YES
NEW_FACE_HALLUCINATION=NO
STRUCTURE_PRESERVED=YES
BACKGROUND_PRESERVED=YES
OVERALL_VISIBLE_IMPROVEMENT=YES
CASE_2_OVERALL=PASS
```

Case 3 (`3.jpg`, 169×226, kleines Schwarzweiß-Porträt):

```text
Pipeline=NAFNet-DeBlur -> DDColor
DETAIL_RECOVERY=GOOD
BLUR_REDUCTION=GOOD
NOISE_ARTIFACT_REDUCTION=GOOD
FACE_IDENTITY_PRESERVED=YES
NEW_FACE_HALLUCINATION=NO
STRUCTURE_PRESERVED=YES
COLOR_NATURAL=YES
COLOR_BLEEDING=NO
BACKGROUND_PRESERVED=YES
OVERALL_VISIBLE_IMPROVEMENT=YES
CASE_3_OVERALL=PASS
```

Phase-0B-Gesamtstatus:

```text
QUALITY_PASS_COUNT=3/3
CASE_1_PRODUCT_RELEVANT_GATE=PASS
QUALITY_GATE=PASS
LICENSE_GATE=PASS
NPU_RUNTIME_USED=NO
QAI_COMPILE_USED=NO
ONNX_EXPORT_USED=NO
RECOMPILE_USED=NO
TOTAL_SECONDS=28.32
C_FREE_GB_AFTER=23.07
OUTPUT_DIR=C:\SnapdragonAI\temp\ai_photo_restore_gate
```

Phase 0B lief bewusst nur als Referenz über ONNX Runtime CPUExecutionProvider.

Verwendete Modelle/Lizenzen:

```text
NAFNet-DeBlur:
Qualcomm AI Hub / Megvii REDS width64
Code: MIT / Apache 2.0
Weights: Apache 2.0 / MIT

DDColor:
Qualcomm AI Hub / ddcolor_paper_tiny
Code: Apache 2.0
Weights: Apache 2.0
```

## Phase 1C – Controlled Local NPU Feasibility Gate

Am 7. September 2026 wurde Case 1 lokal auf Holgers Snapdragon-Entwicklungs-PC über Qualcomm QNN/HTP/NPU ausgeführt.

Runtime:

```text
Qualcomm AI Stack 2.47.0.260601
QnnHtp.dll
Hexagon v73
4 HVX Threads
```

CPU-Modell-Fallback war deaktiviert. CPU nur für Bild-I/O, CIE-Lab, Tiling, Feather-Blending und leichte Orchestrierung.

### NAFNet-DeBlur NPU

```text
Model=nafnet_deblur.dlc
Input=Float32 NHWC [1,360,640,3]
Tiles=12
NAFNET_QNN_HTP=PASS
Graph Compose=0.37 s
HTP Finalize/Prepare=79.21 s
NetRun Init Total=79.58 s
NPU pro Tile≈0.355 s
HTP Accelerator Execute=354.75 ms
12 Tiles≈4.26 s
NAFNET_CPU_MODEL_INFERENCE=NO
PSNR=62.22 dB
SSIM=1.0000
MAE=0.0390 / 255
NAFNET_NPU_QUALITY_PASS=YES
```

### DDColor NPU

```text
Model=ddcolor.dlc
Input=Float32 NHWC [1,256,256,3]
Output=NCHW [1,2,256,256]
DDCOLOR_QNN_HTP=PASS
Graph Compose=0.29 s
HTP Finalize/Prepare=40.90 s
NetRun Init Total=41.19 s
HTP Accelerator Execute=264.58 ms
NetRun Avg=268.39 ms
DDCOLOR_CPU_MODEL_INFERENCE=NO
PSNR=49.47 dB
SSIM=1.0000
MAE=0.4734 / 255
DDCOLOR_NPU_QUALITY_PASS=YES
```

Gesamtstatus Phase 1C:

```text
NPU_FULL_CHAIN=PASS
TECH_PASS=YES
FUNCTION_PASS=YES
PRODUCT_PASS=NOT_YET
CORE_NPU_INFERENCE≈4.52 s
C_FREE_GB_AFTER=22.54
OUTPUT_DIR=C:\SnapdragonAI\temp\ai_photo_restore_npu_gate
```

Outputs:

```text
case1_nafnet_npu.png
case1_ddcolor_npu.png
case1_npu_comparison.png
```

NPU-Ausgabe war visuell und numerisch praktisch identisch mit der CPU-Referenz.

## Offenes Performance-Gate

Noch keine RealESRGAN-End-to-End-Integration.

Problem:

```text
NAFNet Cold Start≈79.58 s
DDColor Cold Start≈41.19 s
Combined Cold Start≈120.77 s
Core NPU Inference≈4.52 s
```

Daher aktuell:

```text
QUALITY_GATE=PASS
LICENSE_GATE=PASS
NPU_TECH_GATE=PASS
FUNCTION_PASS=YES
PERFORMANCE_GATE=OPEN
PRODUCT_PASS=NOT_YET
```

## Nächster verbindlicher Sprint – Phase 1D

Ziel:

```text
NPU Runtime / Cold-Start Performance Gate
```

Priorität 1:

```text
NAFNet einmal laden/finalisieren -> mehrere Jobs ohne Reload
DDColor einmal laden/finalisieren -> mehrere Jobs ohne Reload
```

Messen:

```text
NAFNET_FIRST_LOAD_SECONDS
NAFNET_JOB1_INFERENCE_SECONDS
NAFNET_JOB2_INFERENCE_SECONDS
NAFNET_RELOAD_BETWEEN_JOBS
DDCOLOR_FIRST_LOAD_SECONDS
DDCOLOR_JOB1_INFERENCE_SECONDS
DDCOLOR_JOB2_INFERENCE_SECONDS
DDCOLOR_RELOAD_BETWEEN_JOBS
```

Priorität 2 – nur falls Residency nicht genügt:

```text
serialized context binaries für NAFNet und DDColor
```

Regeln:

```text
kein QAI-Hub-Compile
kein ONNX-Export
keine Modelländerung
keine UI
kein RealESRGAN in Phase 1D
kein FLUX
kein Build
kein Commit
kein Push
```

Ziel:

```text
MODEL_RELOAD_SECONDS <= 5 s
Core NPU≈4–6 s
```

Zeit:

```text
EXPECTED=30–60 Minuten
HARD_STOP=90 Minuten
```

Speicher:

```text
wenn C_FREE_GB < 15 -> STOPP
maximal ca. 2 GB neue temporäre Assets
```

Wenn `PERFORMANCE_GATE=PASS`:

```text
Phase 1E:
NAFNet -> DDColor -> vorhandenes RealESRGAN NPU 4×
```

auf genau einem realen Testbild.

Wenn `PERFORMANCE_GATE=FAIL`:

```text
STOP AI PHOTO RESTORE integration
und Wirtschaftlichkeit neu bewerten
```

## Statusflags – 7. September 2026

```text
FLUX_PERSON_REMOVAL=NO_GO
FLUX_NPU_PLATFORM=BEHALTEN
AI_PHOTO_RESTORE=ACTIVE_PRIMARY_PATH
RESTORE_MODEL=NAFNet-DeBlur
COLORIZATION_MODEL=DDColor
FINAL_UPSCALER=Existing RealESRGAN QNN/HTP
QUALITY_GATE=PASS
QUALITY_PASS_COUNT=3/3
LICENSE_GATE=PASS
NAFNET_NPU=PASS
DDCOLOR_NPU=PASS
NPU_FULL_CHAIN=PASS
NPU_NUMERIC_PARITY=PASS
FUNCTION_PASS=YES
PERFORMANCE_GATE=OPEN
PRODUCT_PASS=NOT_YET
COLD_START_SECONDS_APPROX=120.77
CORE_NPU_SECONDS_APPROX=4.52
NEXT_SESSION=AI_PHOTO_RESTORE_PHASE_1D_RUNTIME_PERFORMANCE_GATE
```
# CHATGPT_HANDOVER – Ergänzung 8. September 2026 – AI PHOTO RESTORE, eigenes DetailNet und Phase 3L Generalization

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsmodus / Priorität

- Sprache weiterhin Deutsch.
- Holger möchte ohne unnötige Zwischenstopps arbeiten: nach einem klaren Prüfschritt direkt den nächsten passenden Schritt liefern.
- Höchste Priorität bleibt sichtbare Produktqualität. Technische PASS-Werte, PSNR, gültige PNGs oder erfolgreiche Trainingsläufe sind kein `PRODUCT_PASS`.
- Weiterhin strikt trennen:
  - `TECH_PASS`
  - `FUNCTION_PASS`
  - `PRODUCT_PASS`
- Keine Produktintegration, ONNX-/QNN-Portierung, Builds, Commits oder Pushes, solange die Bildqualität nicht vorher sichtbar überzeugt.
- Keine CPU-/GPU-KI-Inferenz im späteren Produktpfad; KI-Inferenz soll auf QNN/HTP/NPU laufen. CPU nur für Orchestrierung/Pre-/Postprocessing.
- Kaggle/NVIDIA wird nur für Training, Referenztests und Export verwendet, nicht als Produktinferenz.
- Keine fremden generativen Modelle mit unklarer kommerzieller Trainingsdaten-/Lizenzprovenienz als Produktpfad übernehmen.
- Das Produktziel für AI Photo Restore bleibt deutlich über klassischen Upscalern: historische Bilder vollständig restaurieren, natürlich kolorieren und sehr kleine/unscharfe Bilder sichtbar hochwertig rekonstruieren.
- Verbindliche visuelle Zielreferenz:

```text
C:\Users\holge\Desktop\Testbilder\HK_NPU_STUDIO_TARGET_REFERENCE.png
```

Relevante Testbilder:

```text
C:\Users\holge\Desktop\Testbilder\37.jpg
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
C:\Users\holge\Desktop\Testbilder\3.jpg
```

## AI PHOTO RESTORE – Phase 3H Runtime-Audit

Der zunächst lokal gestartete RRDBNet-Prototyp lief irrtümlich vollständig auf dem Snapdragon-X-Elite-Entwicklungs-PC in PyTorch-CPU-FP32.

Audit:

```text
GPU_NAME=NONE
CUDA_AVAILABLE=NO
MODEL_ON_CUDA=NO
AMP_ACTIVE=NO
STEP_MEANS=OPTIMIZER_UPDATE
SECONDS_PER_OPTIMIZER_UPDATE=46.36
PRIMARY_BOTTLENECK=FP32 CPU CONVOLUTION COMPUTE ON ARM64
EXPECTED_2500_STEP_HOURS=32.36
THREE_HOUR_GATE=FAIL
```

Profiling pro Optimizer-Update:

```text
Data Loading & Degradation:      54.60 ms
Forward Pass:                26,697.62 ms
  Frozen Prefix:             17,645.41 ms
  Trainable Tail:             9,052.21 ms
Loss:                           183.98 ms
Backward Pass:               27,410.71 ms
Optimizer Step:                 78.19 ms
```

Der Lauf wurde kontrolliert nach Step 150 gestoppt und vollständig gesichert.

Validierungsentwicklung:

```text
Step 0:   PSNR 29.31 dB / SSIM 0.7458 / Val Loss 0.03510
Step 50:  PSNR 30.27 dB / SSIM 0.7663 / Val Loss 0.03264
Step 100: PSNR 30.93 dB / SSIM 0.7789 / Val Loss 0.03120
Step 150: PSNR 31.37 dB / SSIM 0.7877 / Val Loss 0.03035
```

Damit war ein klarer Lerntrend vorhanden, aber die lokale ARM64-CPU ist für dieses Training nicht wirtschaftlich. Training wird ab diesem Punkt ausschließlich auf Kaggle/NVIDIA durchgeführt.

## Phase 3H-V – Step-150-Visual-Gate

Checkpoint:

```text
C:\SnapdragonAI\temp\hk_npu_rrdb_prototype_v1\checkpoints\step_0150.pth
SHA256=9e24ea8632da0bae4ae5a2d53649b56e5a8e5133b209852760780f490c3d4026
```

Gemeinsamer pixelidentischer Input:

```text
C:\SnapdragonAI\temp\ai_photo_restore_new_quality_gate\color_3_natural_photographic.png
SHA256=57dfc0275839c4be160c9b610df00d85d47eca85ee38be13f18dcb6e47857797
```

Ergebnis:

```text
FACE_IDENTITY=PASS
HAND_ANATOMY=PASS
PHOTOGRAPHIC_REALISM=PASS
BETTER_THAN_BSRGAN_FACE=YES
BETTER_THAN_BSRGAN_EYES=YES
BETTER_THAN_BSRGAN_HAIR=YES
BETTER_THAN_BSRGAN_HANDS=YES
BETTER_THAN_BSRGAN_CLOTHING=YES
DIRECTIONAL_VISUAL_GAIN=YES
PRODUCT_PASS=PENDING_HOLGER_VISUAL_CONFIRMATION
```

Holgers visuelle Bewertung: Step 150 ist besser als BSRGAN, aber zur Zielreferenz besteht weiterhin ein sehr großer Abstand. `Detail Reconstruction` ist zwingend erforderlich.

## Phase 3I – RRDBNet Detail Reconstruction

Ziel: auf Step 150 aufbauen und gezielt mehr feine Details lernen.

Kaggle-Umgebung:

```text
PYTHON=3.12.13
TORCH=2.10.0+cu128
CUDA_AVAILABLE=True
GPU_NAME=Tesla T4
```

Erster Kaggle-Start scheiterte nur an einer SSIM-FP16/FP32-Metrikinkompatibilität:

```text
RuntimeError: expected scalar type Half but found Float
```

Es wurde ausschließlich die SSIM-Metrik auf FP32 korrigiert:

```text
SSIM_FP32_FIX=PASS
PY_COMPILE=PASS
TRAINING_CODE_CHANGED=NO
VALIDATION_METRIC_FIX_ONLY=YES
```

Danach Trainingslauf:

```text
Microbatch=4
GradAccum=2
EffectiveBatch=8
Max Updates=1000
Runtime Step25=0.658 s/update
Estimated 1000 Steps=10.97 min
```

Final:

```text
BEST_STEP=1000
TOTAL_TRAINING_MINUTES=15.16
```

Der erste Kaggle-Run mit Hash `dfdc271c...` ging anschließend mit der temporären Kaggle-Session verloren. Der erneut ausgeführte und tatsächlich heruntergeladene Step-1000-Lauf ist verbindlich:

```text
best_generator.pth
SHA256=a13c38d42897d12d1078a42f3328a1c4a4be6524aaffdeb2b68e472877d67764
BEST_STEP=1000
```

Der alte Hash

```text
dfdc271cffdda90b108fa9c6f135e5847e15db9bcbdf52217c1148290f4e38e7
```

gehört nur zum verlorenen ersten Kaggle-Lauf und darf nicht mehr als Soll-Hash verwendet werden.

Schneller lokaler Crop-Gate:

```text
C:\SnapdragonAI\temp\hk_npu_detail_reconstruction_prototype_v1\visual_gate_fast\
```

Master:

```text
comparison_detail_grid.png
```

Ergebnis:

```text
NEW_FACE_DETAIL=PARTIAL
NEW_EYE_DETAIL=PARTIAL
NEW_HAIR_DETAIL=PARTIAL
NEW_SKIN_DETAIL=PARTIAL
NEW_HAND_DETAIL=PARTIAL
NEW_CLOTHING_DETAIL=PARTIAL
IDENTITY_PRESERVED=YES
ANATOMY_PRESERVED=YES
FAKE_TEXTURE=NO
PLASTIC_SKIN=MINOR
DETAIL_RECONSTRUCTION_GAIN=PARTIAL
TARGET_REFERENCE_DISTANCE=SAME
PRODUCT_PASS=PENDING_HOLGER_VISUAL_CONFIRMATION
```

Holgers Bewertung: Step 1000 ist zur Zielreferenz weiterhin deutlich zu weit entfernt. Weitere RRDB-Schritte allein werden den notwendigen Qualitätssprung voraussichtlich nicht liefern.

## Strategische Entscheidung: eigenes HK-NPU-STUDIO-Modell

Holger und ChatGPT haben entschieden, einen eigenen, später weiter trainierbaren Modellpfad aufzubauen.

Offizieller technischer Name:

```text
HK NPU STUDIO DetailNet v1
```

Das Modell soll später bei Bedarf gezielt weitertrainiert und um Spezialfähigkeiten erweitert werden können, z. B. für:

- Gesichter/Augen/Haar
- Hände/Finger
- Textilien/Materialien
- historische Fotostrukturen
- Tiny/Blurred Photos
- spätere spezialisierte Varianten

Austauschen/Ersetzen von Objekten soll später nicht in DetailNet gepresst werden, sondern wäre ein eigener Modellbaustein, z. B. `HK NPU STUDIO EditNet/ReplaceNet`.

## HK NPU STUDIO DetailNet v1 – erster Architekturversuch

Verbindliche Grundidee:

```text
3 Kanäle conservative restored RGB
3 Kanäle bicubic source RGB
1 Kanal normalized source gradient
= 7 Input-Kanäle
```

NPU-/QNN-first Operatorziel:

```text
Conv
DepthwiseConv
LeakyReLU
Add
Concat
Resize
Tanh
Mul
Clip
```

Erste v1-Implementierung:

```text
GENERATOR_PARAMETER_COUNT=7,187,091
MODEL_FP16_MB=13.71
ONNX_EXPORT_FEASIBILITY=HIGH
QNN_HTP_FEASIBILITY=HIGH
```

8-Bilder-Overfit-Sanity-Test auf Kaggle T4:

```text
COMPLETED_STEPS=500
BEST_STEP=500
BEST_VAL_PSNR=43.39
SECONDS_PER_OPTIMIZER_UPDATE=0.557
TOTAL_TRAINING_MINUTES=4.64
```

Die ersten visuellen Panels zeigten jedoch nicht die geforderte echte Detailrekonstruktion:

```text
CAN_RECONSTRUCT_EYES=NO
CAN_RECONSTRUCT_HAIR=NO
CAN_RECONSTRUCT_HAND_DETAIL=NOT_VALIDATED
CAN_RECONSTRUCT_TEXTILE_DETAIL=NO
OVERFIT_SANITY_PASS=NO
```

Zusätzlich wurde entdeckt, dass der damalige Hand-Crop inhaltlich falsch war und ein Blatt/Pflanzendetail zeigte. Konsequenz: keine 100-Bilder-Fortsetzung mit v1.

## HK NPU STUDIO DetailNet v1.1 – Architekturupgrade

Die Architektur wurde gezielt verstärkt, ohne Transformer/Attention und weiterhin QNN-first:

```text
Input: 7 Kanäle
Levels: 64 -> 128 -> 256 -> 384
4-Level Encoder/Decoder
10 ContextDetailBlocks im 1/8 Bottleneck
Dual Residual Heads
alpha_structure=0.04
alpha_texture=0.10
GENERATOR_PARAMETER_COUNT=13,717,510
MODEL_FP16_MB=26.16
DISCRIMINATOR_PARAMETER_COUNT=1,926,402
```

Die v1.1-Sanity-Daten wurden visuell neu auditiert. Insbesondere echte Hände, echte Portraitdetails und echte Textilien mit deterministischen Bounding Boxes.

Kaggle-Paket:

```text
hk_npu_studio_detailnet_v11_kaggle_package.zip
```

Erster Start scheiterte nur an einer falschen dynamischen `images_dir`-Auflösung auf das alte v1-Dataset. Vor Training wurden exakt 0 Steps ausgeführt.

Korrektur:

```text
DATASET_PATH_FIX=PASS
CORRECTED_V11_IMAGES_DIR=/kaggle/input/datasets/hknpustudio/hk-npu-studio-detailnet-v11/images
ALL_8_IMAGES_FOUND=YES
PY_COMPILE=PASS
TRAINING_STEPS_ALREADY_EXECUTED=0
READY_TO_RUN=YES
```

Der danach korrekte v1.1-Kaggle-Lauf:

```text
GPU_NAME=Tesla T4
CUDA_AVAILABLE=YES
AMP_ACTIVE=YES
COMPLETED_STEPS=750
BEST_STEP=750
BEST_VAL_PSNR=43.88
SECONDS_PER_OPTIMIZER_UPDATE=0.829
TOTAL_TRAINING_MINUTES=10.36
```

Output:

```text
/kaggle/working/hk_npu_studio_detailnet_v11_outputs.zip
```

Lokal entpackt:

```text
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_overfit\
```

## DetailNet v1.1 – Visual-Gate-Crop-Reparatur

Die ersten v1.1-Panels enthielten erneut zwei unbrauchbare Textil-Crops:

- `textile_weave` lag im unscharfen Hintergrund.
- `textile_fibers` zeigte in Ground Truth keine echten Fasern/Twill-Strukturen.

Daraufhin kein Retraining, sondern ausschließlich Crop-Audit und Neuauswertung mit dem bestehenden Step-750-Checkpoint.

Korrigierte Validierungsquellen:

```text
portrait_eyes:
C1_portrait_05.jpg
BBox [850,680,384,384]

portrait_hair:
C1_portrait_08.jpg
BBox [950,650,384,384]

hand_fingers:
C2_hands_06.jpg
BBox [500,700,384,384]

hand_skin:
C2_hands_02.jpg
BBox [600,800,384,384]

textile_weave:
C3_textiles_01.jpg
BBox [1500,2750,384,384]

textile_fibers:
C3_textiles_20.jpg
BBox [1950,3450,384,384]
```

Alle sechs Ground-Truth-Crops enthalten nun sichtbar das jeweils angekündigte Detailmerkmal.

Gemessener v1.1-Gewinn gegenüber v1:

```text
portrait_eyes:     40.96 -> 44.29 dB  (+3.33)
portrait_hair:     35.22 -> 38.27 dB  (+3.05)
hand_fingers:      34.85 -> 37.81 dB  (+2.96)
hand_skin:         43.27 -> 47.04 dB  (+3.77)
textile_weave:     41.06 -> 45.47 dB  (+4.41)
textile_fibers:    43.12 -> 46.99 dB  (+3.87)
```

Finaler Overfit-Sanity-Gate:

```text
PORTRAIT_EYES_CROP_VALID=YES
PORTRAIT_HAIR_CROP_VALID=YES
HAND_FINGERS_CROP_VALID=YES
HAND_SKIN_CROP_VALID=YES
TEXTILE_WEAVE_CROP_VALID=YES
TEXTILE_FIBERS_CROP_VALID=YES
ALL_VISUAL_CROPS_VALID=YES

CAN_RECONSTRUCT_EYES=YES
CAN_RECONSTRUCT_HAIR=YES
CAN_RECONSTRUCT_HAND_DETAIL=YES
CAN_RECONSTRUCT_TEXTILE_DETAIL=YES

DETAILNET_V11_CLEARLY_BETTER_THAN_V1=YES
OVERFIT_SANITY_PASS=YES

PRODUCT_PASS=NO
```

Interpretation:

- `ARCHITECTURE_CAPACITY=PASS`
- v1.1 kann die gewünschten Detailarten grundsätzlich lernen.
- Das ist ausdrücklich noch kein Generalisierungs- oder Produktnachweis, weil der 8-Bilder-Test absichtlich auf Overfitting ausgelegt war.

## Phase 3L – 100-Image Generalization Prototype vorbereitet

Nächster Schritt ist der erste echte Generalisierungstest mit derselben unveränderten DetailNet-v1.1-Architektur.

Wichtige methodische Entscheidung:

- Der 8-Bilder-Overfit-Checkpoint wird NICHT als Startgewicht verwendet.
- Der Generalization-Prototyp startet mit FRISCH initialisierten DetailNet-v1.1-Gewichten, damit kein Memorization Leakage entsteht.

Datensatz:

```text
100 verifizierte PD12M-Fotografien
TRAIN=80
VALIDATION=20
TRAIN_VAL_HASH_OVERLAP=0
TRAIN_TEST_HASH_OVERLAP=0
```

Split:

```text
TRAIN:
24 portraits
16 hands
16 textiles
24 scenes

VALIDATION:
6 portraits
4 hands
4 textiles
6 scenes
```

Für alle 20 Validierungsbilder wurden feste, category-aware 384×384-Bounding-Box-Crops auditiert und gespeichert:

```text
validation_20image_fixed_crops.json
```

Trainingskonfiguration:

```text
Generator Parameter=13,717,510
Input=7 Kanäle
alpha_structure=0.04
alpha_texture=0.10
Fresh Random Initialization
AMP FP16
Microbatch=2
Effective Batch=4
Max Optimizer Updates=2000
Validation alle 250 Steps
Early Stop ab Step 1000
Runtime Hard Gate <60 min
```

Best-Model-Auswahl erfolgt auf den 20 unbekannten Validierungsbildern anhand eines Composite Validation Scores:

```text
S_val =
Charbonnier
+ 0.4 * LowFreq
+ 0.05 * Sobel
+ 0.3 * Laplacian
+ 0.1 * Frequency
```

Resume-fähige Checkpoints müssen Generator, beide Discriminatoren, Optimizer, AMP-Scaler, RNG-States, global_step, Config und Split-Hashes enthalten.

Autarkes Kaggle-Paket:

```text
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization_kaggle_package.zip
```

Größe:

```text
ca. 222 MB
```

Der echte Kaggle-Generalization-Lauf wurde am 8. September noch NICHT gestartet.

## Verbindlicher nächster Schritt am 9. September 2026

Nicht erneut an der Architektur arbeiten.

Zuerst Phase 3L auf Kaggle T4 starten.

1. Neues Kaggle Notebook.
2. Accelerator `GPU T4 x1`.
3. Preflight:

```python
import torch

print("PYTORCH_VERSION =", torch.__version__)
print("CUDA_AVAILABLE =", torch.cuda.is_available())

if not torch.cuda.is_available():
    raise RuntimeError("HARD STOP: CUDA ist nicht aktiv.")

print("GPU_NAME =", torch.cuda.get_device_name(0))
```

4. Trainingsskript suchen:

```python
import os

matches = []

for root, dirs, files in os.walk("/kaggle"):
    if "train_detailnet_v11_generalization_kaggle.py" in files:
        matches.append(
            os.path.join(root, "train_detailnet_v11_generalization_kaggle.py")
        )

print("FOUND =", len(matches))

for p in matches:
    print(p)
```

5. Wenn exakt ein Skript gefunden wird, genau diesen Pfad starten.
6. Beim Start prüfen:

```text
TRAIN_COUNT=80
VALIDATION_COUNT=20
TRAIN_VAL_HASH_OVERLAP=0
GENERATOR_PARAMETER_COUNT=13717510
CUDA_AVAILABLE=YES
AMP_ACTIVE=YES
```

7. Bei Step 25 muss erscheinen:

```text
SECONDS_PER_OPTIMIZER_UPDATE=
ESTIMATED_2000_STEP_MINUTES=
```

Wenn `ESTIMATED_2000_STEP_MINUTES <= 60`, Lauf bis Ende oder Early Stop weiterlaufen lassen.

8. Ergebnis-Archiv:

```text
/kaggle/working/hk_npu_studio_detailnet_v11_generalization_outputs.zip
```

Nach Abschluss zuerst Kaggle `Save Version`, damit der Output nicht verloren geht, dann herunterladen.

9. Lokal ablegen:

```text
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization_outputs.zip
```

10. Danach:
- Hash-/Log-/Resume-Audit;
- 20-Image-Unseen-Validation auswerten;
- nur wenn Generalization-Gate besteht, Fast-Crop-Test auf `37.jpg`;
- noch keine Vollbild-CPU-Inferenz;
- noch keine Dataset-Erweiterung;
- noch kein ONNX/QNN;
- noch keine Studio-Integration.

## Phase-3L-Entscheidungsgate

Der Prototyp darf nur weitergehen, wenn auf unbekannten Daten sichtbar echte Rekonstruktionsgewinne auftreten.

Zu bewerten:

```text
UNSEEN_VALIDATION_GAIN=
GENERALIZATION_EYES=
GENERALIZATION_HAIR=
GENERALIZATION_HANDS=
GENERALIZATION_TEXTILES=
GENERALIZATION_SCENES=

37_FACE_DETAIL_GAIN=
37_EYE_DETAIL_GAIN=
37_HAIR_DETAIL_GAIN=
37_HAND_DETAIL_GAIN=
37_CLOTHING_DETAIL_GAIN=

IDENTITY_PRESERVED=
ANATOMY_PRESERVED=
FAKE_TEXTURE=
PLASTIC_SKIN=
TARGET_REFERENCE_DISTANCE=
```

`GENERALIZATION_PASS=YES` nur bei echtem Gain auf den unbekannten 20 Validation-Bildern und ohne Identitäts-/Anatomieschaden.

Auch dann:

```text
PRODUCT_PASS=PENDING_HOLGER_VISUAL_CONFIRMATION
```

Wenn auf `37.jpg`:

```text
TARGET_REFERENCE_DISTANCE=SAME
```

oder

```text
WORSE
```

dann STOP:

- kein Dataset-Ausbau;
- kein ONNX;
- kein QNN;
- keine Studio-Integration.

Nur wenn `TARGET_REFERENCE_DISTANCE=SMALLER` und Holger den sichtbaren Fortschritt bestätigt, folgt der Ausbau auf 1500–3000 echte Fotografien und danach ein finales DetailNet-Training.

## Speicherstatus / Schutzregel

Am 8. September trat erneut starker Speicherplatzdruck auf.

Zwischenstände:

```text
C:\SnapdragonAI\temp   ca. 24.56 GB
C:\SnapdragonAI\models ca. 37.45 GB
C:\Users\holge\.cache  ca. 24.82 GB
```

Große TEMP-Bestände enthielten u. a. FLUX2-QNN-/Serialized-Binary-Artefakte. Holger hat ausdrücklich festgelegt:

```text
Nichts löschen, was grundsätzlich noch für HK NPU STUDIO benötigt wird.
```

Nach kontrollierter Bereinigung/Prüfung wurden später wieder ungefähr:

```text
C: FreeGB=33.6
```

gemeldet.

Weiterhin niemals große Modell-/QNN-/Context-/Training-Artefakte pauschal löschen. Vor jeder Bereinigung Ownership, Wiederverwendbarkeit und aktuellen Produktbezug prüfen.

## Statusflags – Feierabend 8. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

AI_PHOTO_RESTORE_TARGET_REFERENCE=
C:\Users\holge\Desktop\Testbilder\HK_NPU_STUDIO_TARGET_REFERENCE.png

RRDB_PHASE3H_LOCAL_CPU_RUNTIME_GATE=FAIL
RRDB_STEP150_CHECKPOINT_PRESERVED=True
RRDB_STEP150_DIRECTIONAL_VISUAL_GAIN=True

RRDB_PHASE3I_KAGGLE_STEP1000=True
RRDB_PHASE3I_CURRENT_HASH=
a13c38d42897d12d1078a42f3328a1c4a4be6524aaffdeb2b68e472877d67764
RRDB_PHASE3I_DETAIL_GAIN=PARTIAL
RRDB_PHASE3I_TARGET_REFERENCE_DISTANCE=SAME
RRDB_AS_FINAL_DETAIL_SOLUTION=False

OWN_DETAIL_MODEL_PATH=True
DETAIL_MODEL_NAME=HK NPU STUDIO DetailNet v1

DETAILNET_V1_PARAMETER_COUNT=7187091
DETAILNET_V1_OVERFIT_SANITY_PASS=False

DETAILNET_V11_PARAMETER_COUNT=13717510
DETAILNET_V11_BEST_STEP=750
DETAILNET_V11_BEST_VAL_PSNR=43.88
DETAILNET_V11_OVERFIT_SANITY_PASS=True
DETAILNET_V11_CAN_RECONSTRUCT_EYES=True
DETAILNET_V11_CAN_RECONSTRUCT_HAIR=True
DETAILNET_V11_CAN_RECONSTRUCT_HAND_DETAIL=True
DETAILNET_V11_CAN_RECONSTRUCT_TEXTILE_DETAIL=True
DETAILNET_V11_CLEARLY_BETTER_THAN_V1=True

DETAILNET_V11_GENERALIZATION_PACKAGE_READY=True
DETAILNET_V11_GENERALIZATION_KAGGLE_RUN_STARTED=False
DETAILNET_V11_GENERALIZATION_PASS=PENDING
DETAILNET_V11_PRODUCT_PASS=False

NEXT_SESSION=PHASE_3L_100_IMAGE_GENERALIZATION_KAGGLE_T4
NO_ARCHITECTURE_CHANGE_BEFORE_PHASE3L=True

ONNX_DETAILNET=False
QNN_DETAILNET=False
STUDIO_DETAILNET_INTEGRATION=False

BUILD_8_SEPTEMBER=False
GIT_ADD_8_SEPTEMBER=False
COMMIT_8_SEPTEMBER=False
PUSH_8_SEPTEMBER=False
```

## Feierabend 8. September 2026

Für heute keine weiteren Trainingsläufe, Exporte, QNN-Jobs, Builds, Commits, Pushes oder Produktintegrationen starten.

Morgen direkt mit Phase 3L auf Kaggle T4 fortsetzen.

## Verbindliche Handover-Regel

Bei jeder künftigen Aktualisierung:

- die vollständige bestehende Chronik 1:1 erhalten;
- nur den neuen Tagesstand unten anhängen;
- niemals eine verkürzte oder rekonstruierte Teilfassung ausgeben;
- Download-Dateiname immer exakt:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt die Datei ausschließlich über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```


# CHATGPT_HANDOVER – Ergänzung 9. September 2026 – DetailNet v1.1 Phase 3L Generalisierung abgeschlossen

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Qualitätsregeln – unverändert verbindlich

- Sprache weiterhin Deutsch.
- Keine unnötigen Zwischenstopps bei routinemäßigen Folgeschritten; den nächsten sicheren Schritt direkt liefern.
- Vor jedem neuen Bildmodell-/Qualitätssprint weiterhin strikt zwischen `TECH_PASS`, `FUNCTION_PASS` und `PRODUCT_PASS` unterscheiden.
- Gute PSNR-/SSIM-Werte allein sind kein Produktqualitätsnachweis.
- Kein ONNX-/QNN-Port und keine Studio-Integration, bevor ein externer visueller Qualitätsgewinn gegenüber dem bisherigen Stand belegt und von Holger bestätigt ist.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`; untracked/unrelated Dateien nicht beiläufig anfassen.

## DetailNet v1.1 – Phase 3L 100-Image Generalization Prototype

Der vorbereitete 100-Bilder-Generalization-Prototyp wurde am 9. September auf Kaggle mit NVIDIA Tesla T4 vollständig ausgeführt.

### Datensatz- und Split-Vertrag

Verwendet wurde der reparierte, auditierte 100-Bilder-PD12M-Fotografie-Subset-Split:

```text
TRAIN_COUNT=80
VALIDATION_COUNT=20
TRAIN_VAL_HASH_OVERLAP=0
```

Kategorien:

```text
TRAIN:
24 Portraits
16 Hände
16 Textilien
24 Szenen

VALIDATION:
6 Portraits
4 Hände
4 Textilien
6 Szenen
```

Die 20 Validation-Bilder verwenden feste category-aware 384×384-Crops mit sichtbaren Ground-Truth-Zielmerkmalen. Unter anderem wurden Augen, Haut-/Fingerleisten, Textilgewebe/-stickerei und feine Szenen-/Materialstrukturen auditiert.

Die drei externen Testbilder sowie die Zielreferenz waren nicht Teil von Train oder Validation:

```text
C:\Users\holge\Desktop\Testbilder\37.jpg
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
C:\Users\holge\Desktop\Testbilder\3.jpg
C:\Users\holge\Desktop\Testbilder\HK_NPU_STUDIO_TARGET_REFERENCE.png
```

## Kaggle-Paket – gefundene Laufzeitfehler und Reparaturen

Der ursprüngliche Kaggle-Paketlauf war nicht direkt reproduzierbar und benötigte drei eng begrenzte Working-Copy-Reparaturen. Es wurde dabei keine Modellarchitektur geändert.

### 1. Falscher Dataset-Resolver

Das Generalization-Skript löste zunächst den alten 8-Bilder-v1.1-Ordner auf und scheiterte an fehlenden Dateien wie:

```text
C1_portrait_01.jpg
```

Fehlerhafter Pfad:

```text
/kaggle/input/datasets/hknpustudio/hk-npu-studio-detailnet-v11/images
```

Der tatsächliche 100-Bilder-Ordner wurde programmgesteuert anhand aller 100 Dateinamen aus `dataset_split.csv` gesucht und verifiziert.

Final verwendeter Pfad:

```text
/kaggle/input/datasets/hknpustudio/detailnet-v11-generalization/images
```

Verifikation:

```text
REQUIRED_IMAGES_FOUND=100
MISSING_IMAGES=0
DATASET_PATH_FIX=PASS
```

### 2. Fehlende PSNR-Hilfsfunktion

Beim Step-0-Validation-Gate brach der erste korrigierte Lauf ab mit:

```text
NameError: name 'compute_psnr' is not defined
```

`compute_psnr()` wurde ausschließlich in der Kaggle-Working-Copy ergänzt. Danach:

```text
PSNR_HELPER_FIX=PASS
PY_COMPILE=PASS
```

Es waren zu diesem Zeitpunkt noch keine Optimizer-Schritte ausgeführt worden.

### 3. Fehlende SSIM-Hilfsfunktion

Der nächste Lauf erreichte Step 250 und brach beim ersten regulären Validation-Gate ab mit:

```text
NameError: name 'compute_ssim_quick' is not defined
```

`compute_ssim_quick()` wurde als reine Validation-Metrik ausschließlich in der Working-Copy ergänzt. Danach wurde der Generalization-Lauf bewusst frisch von Step 0 neu gestartet, statt einen unsauberen Resume nach Step 250 zu erzwingen.

```text
SSIM_HELPER_FIX=PASS
COMPUTE_SSIM_DEFINITION_COUNT=1
COMPUTE_PSNR_DEFINITION_COUNT=1
PY_COMPILE=PASS
RESTART_STRATEGY=FRESH_STEP_0
```

Wichtig für spätere Reproduzierbarkeit:

- diese drei Reparaturen wurden in `/kaggle/working/...` ausgeführt;
- das ursprüngliche Kaggle-Dataset-/Paket unter `/kaggle/input/...` ist dadurch nicht automatisch dauerhaft korrigiert;
- vor einem erneuten Phase-3L-Lauf muss das Paket sauber regeneriert oder dieselben drei Punkte verbindlich in der Paketquelle korrigiert werden.

Die PyTorch-Warnungen zur veralteten `torch.cuda.amp`-API waren nur `FutureWarning` und kein Laufzeitfehler.

## Phase 3L – technischer Trainingslauf vollständig PASS

Finale Umgebung:

```text
GPU_NAME=Tesla T4
CUDA_AVAILABLE=YES
CUDA_VERSION=12.8
PYTORCH_VERSION=2.10.0+cu128
MODEL_ON_CUDA=YES
AMP_ACTIVE=YES
GENERATOR_PARAMETER_COUNT=13717510
DISCRIMINATOR_PARAMETER_COUNT=1926402
MODEL_FP16_MB=26.16
```

Step-25-Runtime-Gate:

```text
SECONDS_PER_OPTIMIZER_UPDATE=0.7749
ESTIMATED_2000_STEP_MINUTES=25.83
RUNTIME_GATE=PASS
```

Finaler Gesamtbericht:

```text
COMPLETED_STEPS=2000
TOTAL_TRAINING_MINUTES=30.39
SECONDS_PER_OPTIMIZER_UPDATE=0.9116
BEST_STEP=1500
BEST_VAL_SCORE=0.009906394482241013
RESUME_CHECKPOINT_COMPLETE=YES
```

Der Lauf endete regulär bei Step 2000; Early Stop wurde nicht ausgelöst.

Kaggle-Ergebnisarchiv:

```text
/kaggle/working/hk_npu_studio_detailnet_v11_generalization_outputs.zip
ARCHIVE_SIZE=1728.25 MB
```

Lokaler Download / extrahierter Bestand:

```text
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization_outputs.zip
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\
```

## Checkpoints

Vorhanden:

```text
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\best_generator.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\best_training_checkpoint.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_0250.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_0500.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_0750.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_1000.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_1250.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_1500.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_1750.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\checkpoint_step_2000.pth
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\final_training_checkpoint.pth
```

Best Generator:

```text
BEST_STEP=1500
BEST_GENERATOR_SHA256=7D92A56791DD8133D472B0DB44AA8499D0D22D2A8E540F36136260B5D78A9A24
BEST_GENERATOR_SIZE=54982593 Bytes
```

Vollständige Training-Checkpoints liegen jeweils bei rund 188 MB und enthalten laut Report den vollständigen Resume-State.

Ab jetzt für alle Qualitätsprüfungen ausschließlich `best_generator.pth` / Step 1500 verwenden, nicht Step 2000.

## Quantitative Generalisierung – klarer Gain auf 20 ungesehenen Bildern

Step-0-Ausgangspunkt:

```text
STEP_0_INITIAL_UNSEEN_VAL_SCORE=0.03823
STEP_0_INITIAL_UNSEEN_PSNR=33.86 dB
```

Best Step 1500:

```text
BEST_VAL_SCORE=0.009906394482241013
BEST_VAL_PSNR=45.612698554992676 dB
BEST_VAL_SSIM=0.9907812416553498
VAL_CHARBONNIER=0.005409788317047059
VAL_LOW_FREQ=0.0008339467560290359
VAL_SOBEL=0.007642908510752023
VAL_LAPLACIAN=0.011240915802773088
VAL_FREQUENCY=0.004086072964128107
```

Gegenüber Step 0 entspricht das ungefähr:

```text
VAL_SCORE_IMPROVEMENT≈74%
PSNR_GAIN≈+11.75 dB
```

Category Scores bei Step 1500:

```text
PORTRAIT_SCORE=0.011139221873600036
HAND_SCORE=0.004752994060982018
TEXTILE_SCORE=0.011557065136730672
SCENE_SCORE=0.011008720268728211
```

Zum Vergleich Step 250:

```text
PORTRAIT_SCORE=0.0330375911667943
HAND_SCORE=0.009403962723445148
TEXTILE_SCORE=0.03422332534100861
SCENE_SCORE=0.029105628654360772
```

Damit verbesserten sich alle vier Kategorien deutlich auf unbekannten Validation-Bildern.

### Sättigung nach Step 1500

Step 1750:

```text
VAL_SCORE=0.009955367220973128
VAL_PSNR=45.531102538108826
VAL_SSIM=0.9907813489437103
```

Step 2000:

```text
FINAL_VAL_SCORE=0.010242592208087445
FINAL_VAL_PSNR=45.17655825614929
FINAL_VAL_SSIM=0.9904824256896972
```

Interpretation:

- Step 1500 ist der echte Best-Checkpoint.
- Ab Step 1500 setzt leichte Sättigung / minimale Verschlechterung ein.
- Weitere Trainingsschritte sind für diesen 100-Bilder-Prototyp aktuell nicht begründet.

## Visueller Validation-Gate auf ungesehenen Bildern

Holger stellte das Step-BEST-Master-Grid mit vier gezeigten Kategorien bereit:

1. Portrait / Augen
2. Hand / Hautleisten
3. Textil / Stickerei bzw. Gewebe
4. Szene / Steinrelief und Materialstruktur

Spalten:

```text
1. Degraded (Source Bicubic)
2. Conservative Restored
3. DetailNet v1.1 (Step BEST)
4. Ground Truth HR
```

Visuelle Bewertung des bereitgestellten Grids:

```text
VISUAL_EYES_GAIN=YES
VISUAL_HAND_DETAIL_GAIN=YES
VISUAL_TEXTILE_DETAIL_GAIN=YES
VISUAL_SCENE_DETAIL_GAIN=YES
STRUCTURE_PRESERVED=YES
ANATOMY_PRESERVED=YES
FAKE_TEXTURE=NO
PLASTIC_SKIN=NO
HALOS=NO_OR_NEGLIGIBLE
DETAILNET_V11_CLOSER_TO_GT_THAN_CONSERVATIVE=YES
```

Beobachtet:

- Augen: Lidkante, Iris-/Pupillenübergang und fotografische Feinstruktur näher am Ground Truth.
- Hand: Hautleisten/Falten klarer, ohne sichtbare künstliche Linien oder Anatomieverformung.
- Textil: Stickerei-/Gewebedetails sichtbar näher am Ground Truth.
- Szene: Stufenkanten und Materialstruktur klarer und plausibel rekonstruiert.

Im bereitgestellten Master-Grid war kein eigener Haar-Crop sichtbar. Daher nicht erfinden:

```text
GENERALIZATION_HAIR_VISUAL_CONFIRMATION=PENDING
```

Aktueller methodischer Status:

```text
ARCHITECTURE_CAPACITY_PASS=YES
NUMERIC_UNSEEN_GENERALIZATION_GAIN=YES
NUMERIC_GENERALIZATION_PASS=YES
VISUAL_GENERALIZATION_GATE=PASS_FOR_SHOWN_CATEGORIES
GENERALIZATION_PASS=QUALIFIED_PASS
PRODUCT_PASS=NO
```

`QUALIFIED_PASS` bedeutet: Die 20-Bilder-Generalisation ist quantitativ klar belegt und für die gezeigten Kategorien visuell bestätigt; der externe reale Produkt-Qualitätstest auf `37.jpg` steht noch aus.

## Wichtig: noch KEIN Produkt- oder NPU-Port-Gate

Noch nicht durchgeführt:

```text
DETAILNET_V11_EXTERNAL_37_TEST=False
DETAILNET_V11_TARGET_REFERENCE_DISTANCE=PENDING
DETAILNET_V11_FINAL_DATASET_EXPANSION=False
DETAILNET_V11_ONNX=False
DETAILNET_V11_QNN=False
DETAILNET_V11_HTP=False
DETAILNET_V11_STUDIO_INTEGRATION=False
PRODUCT_PASS=False
```

Keine ONNX-/QNN-Arbeit beginnen, solange der externe Test nicht sichtbar belegt, dass DetailNet v1.1 näher an Holgers Qualitätsziel kommt.

## Verbindlich nächster Schritt

Als nächstes ausschließlich der externe Realtest mit:

```text
C:\Users\holge\Desktop\Testbilder\37.jpg
```

Verwenden:

```text
C:\SnapdragonAI\temp\hk_npu_studio_detailnet_v11_generalization\checkpoints\best_generator.pth
BEST_STEP=1500
SHA256=7D92A56791DD8133D472B0DB44AA8499D0D22D2A8E540F36136260B5D78A9A24
```

Kein CPU-Vollbildlauf als erstes Gate. Nur die bereits festgelegten relevanten Crops:

```text
adult face
child face
eyes
hair
hands
clothing
```

Vergleich:

```text
1 Previous BSRGAN
2 RRDB Step150
3 RRDB Detail Step1000
4 HK NPU STUDIO DetailNet v1.1 Step1500
5 Target Reference
```

Zielreferenz:

```text
C:\Users\holge\Desktop\Testbilder\HK_NPU_STUDIO_TARGET_REFERENCE.png
```

Entscheidungsfragen:

```text
37_FACE_DETAIL_GAIN=
37_EYE_DETAIL_GAIN=
37_HAIR_DETAIL_GAIN=
37_HAND_DETAIL_GAIN=
37_CLOTHING_DETAIL_GAIN=
IDENTITY_PRESERVED=
ANATOMY_PRESERVED=
FAKE_TEXTURE=
PLASTIC_SKIN=
TARGET_REFERENCE_DISTANCE=SMALLER / SAME / WORSE
```

Hard Stop:

```text
Wenn TARGET_REFERENCE_DISTANCE=SAME oder WORSE:
STOP.
Kein Dataset-Ausbau.
Kein ONNX.
Kein QNN.
Keine Studio-Integration.
```

Nur wenn:

```text
TARGET_REFERENCE_DISTANCE=SMALLER
```

und Holger den sichtbaren Fortschritt selbst bestätigt, folgt:

```text
PD12M Dataset Expansion auf ca. 1500–3000 echte Fotografien
-> finales DetailNet-Training
-> ONNX
-> QNN/HTP
-> HK NPU STUDIO Integration
```

## Statusflags – aktueller Stand 9. September 2026

```text
PRODUKTNAME=HK NPU STUDIO
DETAIL_MODEL_NAME=HK NPU STUDIO DetailNet v1.1

DETAILNET_V11_PARAMETER_COUNT=13717510
DETAILNET_V11_OVERFIT_SANITY_PASS=True

PHASE3L_TRAIN_COUNT=80
PHASE3L_VALIDATION_COUNT=20
PHASE3L_TRAIN_VAL_HASH_OVERLAP=0
PHASE3L_COMPLETED_STEPS=2000
PHASE3L_TOTAL_TRAINING_MINUTES=30.39
PHASE3L_BEST_STEP=1500
PHASE3L_BEST_VAL_SCORE=0.009906394482241013
PHASE3L_BEST_VAL_PSNR=45.612698554992676
PHASE3L_BEST_VAL_SSIM=0.9907812416553498
PHASE3L_BEST_GENERATOR_SHA256=7D92A56791DD8133D472B0DB44AA8499D0D22D2A8E540F36136260B5D78A9A24
PHASE3L_RESUME_CHECKPOINT_COMPLETE=True

PHASE3L_NUMERIC_GENERALIZATION_PASS=True
PHASE3L_VISUAL_EYES_GAIN=True
PHASE3L_VISUAL_HAND_GAIN=True
PHASE3L_VISUAL_TEXTILE_GAIN=True
PHASE3L_VISUAL_SCENE_GAIN=True
PHASE3L_VISUAL_HAIR_CONFIRMATION=PENDING
PHASE3L_GENERALIZATION_PASS=QUALIFIED_PASS

DETAILNET_V11_EXTERNAL_37_TEST=False
DETAILNET_V11_TARGET_REFERENCE_DISTANCE=PENDING
DETAILNET_V11_PRODUCT_PASS=False

DETAILNET_V11_ONNX=False
DETAILNET_V11_QNN=False
DETAILNET_V11_HTP=False
DETAILNET_V11_STUDIO_INTEGRATION=False

BUILD_9_SEPTEMBER=False
GIT_ADD_9_SEPTEMBER=False
COMMIT_9_SEPTEMBER=False
PUSH_9_SEPTEMBER=False

NEXT_SESSION=DETAILNET_V11_EXTERNAL_37_FAST_VISUAL_GATE
```

## Handover-Übernahme

Diese vollständige, nur ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.

# CHATGPT_HANDOVER – Ergänzung 9. September 2026, später Tagesabschluss – RestoreNet v1/v2 Qualitätsgate und Entscheidung für v3

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neueste Abschnitt Vorrang.

## Arbeitsregel – ab jetzt zusätzlich verbindlich

Holger möchte vor jedem technischen Sprint immer sichtbar erhalten:

```text
SPRINT-ZEIT=
WORST CASE=
SPEICHER=
HARD STOP=
```

Diese vier Angaben nicht vergessen.

Weiterhin:

- Sprache: Deutsch.
- Nach einem klaren Prüfschritt direkt den nächsten sinnvollen Schritt liefern.
- Keine unnötigen Rückfragen.
- Keine Builds, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht anfassen.
- Für das Produktziel gilt weiterhin strikt:
  - KI-Inferenz im finalen HK-NPU-STUDIO-Pfad nur über QNN/HTP/NPU;
  - CPU nur für Orchestrierung, I/O, Resize, Masken, Tensorvorbereitung und Compositing;
  - keine CPU-/GPU-KI als gleichwertige Produktlösung.
- Technische PASS-Werte sind kein Qualitäts- oder Produkt-PASS.
- Keine ONNX-/QNN-Portierung, wenn das visuelle Qualitätsgate nicht bestanden ist.

## Strategiewechsel von DetailNet v1.1 zu RestoreNet

Der zuvor dokumentierte DetailNet-v1.1-Pfad wurde nach weiterer Prüfung nicht weiter in Richtung Dataset-Ausbau/QNN geführt.

Wesentliche neue Erkenntnis:

- Der frühere Degradations-/Restore-Vertrag war für ein echtes Rekonstruktionsmodell nicht sauber genug.
- Insbesondere wurde erkannt, dass Ground-Truth-Information in einem früheren Restore-/Degradationspfad indirekt in den Input gelangen konnte.
- Für den neuen Rekonstruktionspfad wurde deshalb ein harter SOURCE-only-Vertrag eingeführt:

```text
CLEAN HR
-> realistische Degradation
-> SOURCE
-> conservative restore ausschließlich aus SOURCE
-> RestoreNet ausschließlich aus SOURCE-abgeleiteten Inputs
-> Ziel = CLEAN HR
```

RestoreNet-Input:

```text
RESTORED RGB        3 Kanäle
SOURCE_BICUBIC RGB  3 Kanäle
SOURCE_GRADIENT     1 Kanal
-----------------------------
x7                  7 Kanäle
```

Ground Truth darf niemals Modellinput sein.

Verwendete Degradationsprofile:

```text
PROFILE_A_HISTORICAL_BW_SCAN
PROFILE_B_LOW_RES_BW_DIGITAL
PROFILE_C_LOW_RES_WARM_COLOR
GENERIC_MIXED
```

## RestoreNet v1 – Architektur

Architekturdatei im Phase-3O-A-Gate:

```text
C:\SnapdragonAI\temp\hk_npu_studio_restorenet_v1_architecture_gate\hk_restorenet_v1.py
```

Bestätigter Architekturvertrag:

```text
MODEL_CLASS=HKRestoreNetV1
PARAMETER_COUNT=46940591
INPUT_CHANNELS=7
OUTPUT_CHANNELS=3
```

Erlaubte NPU-/QNN-first Operatoren:

```text
Conv2D
DepthwiseConv
1x1 Conv
LeakyReLU
Add
Concat
Resize
Mul
Tanh
Clip
```

Nicht vorgesehen:

```text
Transformer
Attention
PixelShuffle
```

Phase 3O-A:

```text
PARAMETER_COUNT=46,940,591
FP32≈179.06 MB
FP16≈89.53 MB
FORWARD_GATE=PASS
FINITE=PASS
RANGE=PASS
TECH_PASS=YES
QUALITY=NOT_TESTED
PRODUCT_PASS=NO
```

## RestoreNet v1 – erster 8-Bilder-Trainingslauf und entdeckter Protokollfehler

Der erste Phase-3O-B-Lauf auf Kaggle T4 lief technisch vollständig:

```text
MAX_STEPS=1200
PATCH_SIZE=384
BATCH_SIZE=1
BEST_STEP=1200
TOTAL_MINUTES=14.50
TRAINING_GATE=PASS
```

Best-Checkpoint:

```text
/kaggle/working/hk_npu_studio_phase_3o_b_kaggle/output/checkpoints/best.pt
```

Der visuelle Kontaktbogen zeigte jedoch nur geringe Veränderungen gegenüber `Conservative Restore`.

Qualitätsurteil:

```text
EYES_DETAIL=FAIL
HAIR_DETAIL=FAIL
HAND_DETAIL=FAIL
SKIN_DETAIL=FAIL
TEXTILE_DETAIL=FAIL
MATERIAL_DETAIL=FAIL
IDENTITY_PRESERVED=PASS
ANATOMY_PRESERVED=PASS
FAKE_TEXTURE=PASS
PLASTIC_SKIN=PASS
RINGING=PASS
QUALITY_BOOST=SMALL/NEAR_ZERO
OUTPUT_MUCH_CLOSER_TO_CLEAN_HR=NO
PRODUCT_PASS=NO
```

Danach wurde ein echter Protokollfehler gefunden:

- `__len__ = 1200`;
- pro Index wurde eine neue Degradation mit neuem Seed erzeugt;
- dadurch waren es nicht acht feste SOURCE→CLEAN-Paare, sondern bis zu 1200 unterschiedliche Degradationen;
- der Direct-Reconstruction-Branch hatte außerdem keine eigene explizite Loss-Supervision.

## RestoreNet v1 – C2 korrigierter echter Extreme-Overfit

C2 korrigierte genau diese beiden Punkte.

Vertrag:

```text
FIXED_SOURCE_CLEAN_PAIRS=8
PAIR_REPETITIONS=150
DYNAMIC_TRAIN_DEGRADATION=NO
DIRECT_AUX_WEIGHT=1.0
MAX_STEPS=1200
PATCH_SIZE=384
BATCH_SIZE=1
```

Isolierter Arbeitsbereich:

```text
/kaggle/working/hk_npu_studio_phase_3o_c2
```

C2-Training:

```text
TRAIN_EXIT_CODE=0
LAST_STEP=1200
TOTAL_MINUTES=14.01
BEST_STEP=1000
BEST_SCORE=0.06209051748737693
C2_TRAINING_GATE=PASS
```

Best-Checkpoint:

```text
/kaggle/working/hk_npu_studio_phase_3o_c2/output/checkpoints/best.pt
```

## RestoreNet v1 C2 – visuelles Ergebnis

Der korrigierte C2-Lauf war sichtbar etwas besser als der ursprüngliche B-Lauf, erreichte aber weiterhin nicht das Produktziel.

Strenge Bewertung:

```text
EYES_DETAIL=FAIL
HAIR_DETAIL=FAIL
HAND_DETAIL=FAIL
SKIN_DETAIL=FAIL
TEXTILE_DETAIL=FAIL
MATERIAL_DETAIL=FAIL
IDENTITY_PRESERVED=PASS
ANATOMY_PRESERVED=PASS
FAKE_TEXTURE=PASS
PLASTIC_SKIN=PASS
RINGING=PASS
OUTPUT_MUCH_CLOSER_TO_CLEAN_HR=NO
QUALITY_BOOST=SMALL
TARGET_REFERENCE_DISTANCE=NOT_MUCH_SMALLER
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

## RestoreNet v1 C2 – Branch-Diagnose

C2 zeigte jetzt klar, dass der Direct-Branch tatsächlich lernt und der Confidence-Gate nicht mehr das Hauptproblem ist.

Aggregat:

```text
MEAN_RESTORED=0.07553198
MEAN_DIRECT=0.06181448
MEAN_OUTPUT=0.06208994
MEAN_GATE=0.86645488
MEAN_DELTA_DIRECT=0.02497429
MEAN_DELTA_OUTPUT=0.02270634

DIRECT_BETTER_THAN_RESTORED=True
DIRECT_BETTER_THAN_OUTPUT=True
OUTPUT_BETTER_THAN_RESTORED=True
```

Interpretation:

```text
DIRECT_BRANCH_LEARNS=YES
CONFIDENCE_GATE_PRIMARY_PROBLEM=NO
FINAL_OUTPUT_TRACKS_DIRECT=YES
```

## RestoreNet v1 C2 – Konvergenzdiagnose

Validation-Verlauf:

```text
STEP=100   SCORE=0.07411631
STEP=200   SCORE=0.07309218
STEP=300   SCORE=0.06895073
STEP=400   SCORE=0.06721437
STEP=500   SCORE=0.06499804
STEP=600   SCORE=0.06301000
STEP=700   SCORE=0.06491303
STEP=800   SCORE=0.06298671
STEP=900   SCORE=0.06499444
STEP=1000  SCORE=0.06208994
STEP=1100  SCORE=0.06220409
STEP=1200  SCORE=0.06220546
```

Ergebnis:

```text
FIRST_TO_BEST_IMPROVEMENT_PERCENT=16.23
BEST_STEP=1000
STEP_1000_TO_1200=PLATEAU / MINIMAL_WORSE
CONVERGENCE_PLATEAU=YES
```

Entscheidung:

```text
RESTORENET_V1_TECH_PASS=YES
TRUE_EXTREME_OVERFIT_PROTOCOL=PASS
DIRECT_BRANCH_LEARNS=YES
QUALITY_BOOST=LARGE=NO
QUALITY_PASS=NO
PRODUCT_PASS=NO
LONGER_V1_TRAINING=STOP
QNN_PORT=STOP
```

RestoreNet v1 wird nicht weiter trainiert oder auf QNN portiert.

## RestoreNet v2 – neue Architektur

V2 wurde bewusst als neue Architektur erstellt und nicht als kleiner Patch auf v1.

Arbeitsbereich:

```text
/kaggle/working/hk_npu_studio_restorenet_v2
```

Architekturziele:

- 7-Kanal-Input bleibt;
- echte Multi-Scale-Pyramide:
  - 384
  - 192
  - 96
  - 48
- Cross-Scale-Fusion über `Resize + Concat + Conv`;
- kein Confidence-Gate im Capacity-Test;
- direkte RGB-Synthese;
- Multi-Scale-Ausgänge:
  - `coarse_48`
  - `coarse_96`
  - `coarse_192`
  - `detail_384`
  - `output`;
- weiterhin ausschließlich NPU-/QNN-freundliche Grundoperatoren.

Bestätigtes Architecture Gate:

```text
MODEL=HKRestoreNetV2
PARAMETER_COUNT=68724047
OUTPUT_SHAPE=(1,3,64,64)
COARSE_48_SHAPE=(1,3,8,8)
COARSE_96_SHAPE=(1,3,16,16)
COARSE_192_SHAPE=(1,3,32,32)
DETAIL_384_SHAPE=(1,3,64,64)
FINITE=True
RANGE_OK=True
RESTORENET_V2_ARCHITECTURE_GATE=PASS
```

## RestoreNet v2 – Trainervertrag

Trainer:

```text
/kaggle/working/hk_npu_studio_restorenet_v2/train_restorenet_v2.py
```

Vertrag:

```text
PATCH_SIZE=384
BATCH_SIZE=1
MAX_STEPS=1200
FIXED_SOURCE_CLEAN_PAIRS=8
PAIR_REPETITIONS=150
DYNAMIC_DEGRADATION=NO
MULTISCALE_SUPERVISION=YES
CONFIDENCE_GATE=NO
PARAMETER_COUNT=68724047
```

Multi-Scale-Supervision:

```text
final output      Gewicht 1.00
detail_384        Gewicht 0.75
coarse_192        Gewicht 0.40
coarse_96         Gewicht 0.25
coarse_48         Gewicht 0.15
```

Dry-Run:

```text
V2_DRY_RUN_GATE=PASS
CUDA_TRAINING_STARTED=NO
PRODUCT_PASS=NO
```

## RestoreNet v2 – erster Trainingsstart OOM

Der erste echte V2-Trainingsstart scheiterte bereits vor Step 1:

```text
CUDA OOM
GPU=T4 14.56 GiB
LAST_STEP=0
BEST_CHECKPOINT_EXISTS=False
V2_TRAINING_GATE=FAIL
HARD_STOP=YES
```

Die Patchgröße wurde ausdrücklich nicht reduziert.

## RestoreNet v2 – Training-only Activation Checkpointing

Als reine Trainingsoptimierung wurde Activation Checkpointing ergänzt.

Wichtig:

```text
PATCH_SIZE_CHANGED=NO
PARAMETERS_CHANGED=NO
INFERENCE_GRAPH_INTENT_CHANGED=NO
TRAINING_ACTIVATION_CHECKPOINTING=YES
```

Backup der unveränderten Referenz:

```text
/kaggle/working/hk_npu_studio_restorenet_v2/model/hk_restorenet_v2_PRE_CHECKPOINTING_REFERENCE.py
```

384×384 Forward-/Backward-VRAM-Probe:

```text
PARAMETER_COUNT=68724047
LOSS=0.53633726
FINAL_LOSS=0.20281208
DETAIL_LOSS=0.20451567

VRAM_ALLOC_GB=0.55
VRAM_RESERVED_GB=6.45
VRAM_PEAK_ALLOC_GB=5.93
CUDA_FREE_AFTER_BACKWARD_GB=7.97
CUDA_TOTAL_GB=14.56

FORWARD_PASS=YES
BACKWARD_PASS=YES
OPTIMIZER_STEP=NO
VRAM_PROBE_GATE=PASS
```

Damit war der Speicherblocker gelöst, ohne die Inferenzarchitektur zu verkleinern.

## RestoreNet v2 – echter 1200-Step-Lauf

Training mit Activation Checkpointing:

```text
TRAIN_EXIT_CODE=0
LAST_STEP=1200
TOTAL_MINUTES=25.66
LIVE_BEST_STEP=1100
LIVE_BEST_SCORE=0.06334061
BEST_CHECKPOINT_EXISTS=True
LATEST_CHECKPOINT_EXISTS=True
V2_TRAINING_GATE=PASS
PATCH_SIZE=384
```

Best-Checkpoint:

```text
/kaggle/working/hk_npu_studio_restorenet_v2/output/checkpoints/best.pt
```

Wichtiger numerischer Vergleich:

```text
RestoreNet v1 C2 best = 0.06209052
RestoreNet v2 best    = 0.06334061
```

V2 war damit im Composite-Score ungefähr 2 % schlechter als v1 C2.

## RestoreNet v2 – visuelles Qualitätsgate

Kontaktbogen:

```text
/kaggle/working/hk_npu_studio_restorenet_v2/output/panels/step_1100_contact_sheet.png
```

Der Kontaktbogen zeigte:

- V2 verändert Farbe/Ton deutlich stärker als v1;
- es entstehen jedoch keine überzeugend rekonstruierten verlorenen Details;
- Augen bleiben weich;
- Haare bekommen keine echten feinen Strähnen;
- Finger/Hände werden farblich verändert, aber Haut-/Fingerstruktur wird nicht wiederhergestellt;
- Textilgewebe und Fasern bleiben deutlich hinter Clean HR;
- Szenen bekommen Ton-/Farbänderungen, aber keine echte Detailrekonstruktion;
- bei der Gottesanbeterin wird eher eine Gesamtfarbinterpretation erzeugt als echte strukturelle Wiederherstellung;
- beim Dachbild entstehen ebenfalls Tonwertänderungen statt verlorener Dachdetails.

Strenge Bewertung:

```text
EYES_DETAIL=FAIL
HAIR_DETAIL=FAIL
HAND_DETAIL=FAIL
SKIN_DETAIL=FAIL
TEXTILE_DETAIL=FAIL
MATERIAL_DETAIL=FAIL
SCENE_DETAIL=FAIL

IDENTITY_PRESERVED=PASS
ANATOMY_PRESERVED=PASS
FAKE_TEXTURE=PASS
PLASTIC_SKIN=PASS
RINGING=PASS

QUALITY_BOOST=LARGE=NO
OUTPUT_MUCH_CLOSER_TO_CLEAN_HR=NO
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

Entscheidung:

```text
RESTORENET_V2_TECH_PASS=YES
RESTORENET_V2_TRAINING_PASS=YES
RESTORENET_V2_QUALITY_PASS=NO
MORE_V2_STEPS=STOP
QNN_PORT=STOP
PRODUCT_PASS=NO
```

## Technische Schlussfolgerung aus v1 und v2

Zwei deutlich unterschiedliche Architekturen zeigen dasselbe Grundproblem:

- Loss und Zielrepräsentation belohnen zuverlässig:
  - Farbannäherung;
  - Helligkeit;
  - Konturen;
  - Grobstruktur;
- sie erzwingen aber nicht stark genug die Rekonstruktion von:
  - Augen;
  - feinen Haarsträhnen;
  - Hautmikrostruktur;
  - Fingerdetails;
  - Textilfasern;
  - feinen Materialstrukturen.

Daher wird nicht weiter mit kleinen v2-Patches oder einfach mehr Steps gearbeitet.

## Nächster Primärpfad: RestoreNet v3 / Detail-Reconstruction-Training

Für morgen ist der nächste echte Architektur-/Loss-Sprint vorgesehen.

Ziel:

```text
RESTORENET_V3
```

Nicht einfach größer, sondern andere Zielrepräsentation.

Geplante Leitidee:

1. getrennter `Structure`-Pfad;
2. getrennter `Texture`-Pfad;
3. getrennter `RGB Reconstruction`-Pfad;
4. Detailzweige direkt gegen hochfrequente Clean-HR-Ziele trainieren;
5. stärkere Edge-/Texture-/Frequency-Supervision;
6. Multi-Scale-Kontext beibehalten, wenn sinnvoll;
7. weiterhin QNN-/HTP-freundliche Operatoren;
8. kein Transformer/Attention, solange nicht vorher QNN-Produktviabilität belegt ist;
9. zuerst wieder harter 8-Fixed-Pair-Capacity-Test;
10. erst bei klar sichtbarem `QUALITY_BOOST=LARGE` an Generalisierung/QNN denken.

Morgen zunächst nur Architecture + Loss Gate, noch kein QNN.

Vorgesehener Sprint:

```text
SPRINT-ZEIT≈20–35 Min.
WORST_CASE≈45 Min.
SPEICHER=<100 MB vor Training
HARD_STOP=kein v2-Retry, kein QNN-Port, kein Produktintegration
```

## Statusflags – Feierabend 9. September 2026, aktueller Vorrang

```text
PRODUKTNAME=HK NPU STUDIO
AI_PHOTO_RESTORE_PRIMARY_PATH=RESTORENET_RESEARCH

OLD_DETAILNET_V11_PATH=SUPERSEDED_BY_SOURCE_ONLY_RESTORENET_RESEARCH
GROUND_TRUTH_INPUT_ALLOWED=False
RESTORENET_INPUT_CHANNELS=7

RESTORENET_V1_PARAMETER_COUNT=46940591
RESTORENET_V1_TRUE_FIXED_PAIR_PROTOCOL=True
RESTORENET_V1_BEST_STEP=1000
RESTORENET_V1_BEST_SCORE=0.06209051748737693
RESTORENET_V1_DIRECT_BRANCH_LEARNS=True
RESTORENET_V1_CONVERGENCE_PLATEAU=True
RESTORENET_V1_QUALITY_PASS=False
RESTORENET_V1_PRODUCT_PASS=False
RESTORENET_V1_QNN_PORT=STOP

RESTORENET_V2_PARAMETER_COUNT=68724047
RESTORENET_V2_ARCHITECTURE_GATE=PASS
RESTORENET_V2_PATCH_SIZE=384
RESTORENET_V2_ACTIVATION_CHECKPOINTING=True
RESTORENET_V2_VRAM_PEAK_GB=5.93
RESTORENET_V2_TRAIN_EXIT_CODE=0
RESTORENET_V2_COMPLETED_STEPS=1200
RESTORENET_V2_TOTAL_MINUTES=25.66
RESTORENET_V2_BEST_STEP=1100
RESTORENET_V2_BEST_SCORE=0.06334061175584793
RESTORENET_V2_VISUAL_PANEL_GATE=PASS
RESTORENET_V2_QUALITY_PASS=False
RESTORENET_V2_PRODUCT_PASS=False
RESTORENET_V2_MORE_STEPS=STOP
RESTORENET_V2_QNN_PORT=STOP

NEXT_SESSION=RESTORENET_V3_STRUCTURE_TEXTURE_RGB_ARCHITECTURE_AND_LOSS_GATE

BUILD_9_SEPTEMBER_LATE=False
INSTALLER_9_SEPTEMBER_LATE=False
GIT_ADD_9_SEPTEMBER_LATE=False
COMMIT_9_SEPTEMBER_LATE=False
PUSH_9_SEPTEMBER_LATE=False
```

## Feierabend 9. September 2026

Für heute keine weiteren Trainingsläufe, Architekturänderungen, ONNX-/QNN-Arbeiten, Builds, Installer, Commits oder Pushes durchführen.

Morgen direkt mit RestoreNet v3 weiter:

```text
Structure + Texture + RGB Reconstruction
-> High-Frequency/Edge/Texture Loss Gate
-> 8 feste SOURCE→CLEAN-Paare
-> erst danach Training
```

## Handover-Übernahme

Diese vollständige, nur ergänzte Datei als:

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.


# CHATGPT_HANDOVER – Ergänzung 10. September 2026 – AI Photo Restore: RestoreNet-Abschluss, VOSR-/FiDeSR-Bakeoff und OSDFace-Entscheidung

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Qualitätsregeln – erneut verbindlich

- Sprache mit Holger weiterhin Deutsch; Antworten kurz und direkt.
- Bei technischen Sprints vor dem ausführbaren Auftrag immer sichtbar nennen:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Keine Builds, Installer, `git add`, Commits, Pushes, Tags oder Releases ohne den jeweils abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern oder löschen.
- Für das Produktziel gilt weiterhin hart: eigentliche KI-Inferenz nur über Qualcomm QNN/HTP/NPU. CPU nur für Orchestrierung, I/O, Resize, Masken, Tensorvorbereitung und Compositing. Keine CPU-/GPU-KI als gleichwertiger Produktpfad.
- `TECH PASS`, `QUALITY PASS` und `PRODUCT PASS` strikt getrennt bewerten.
- Kein QNN-Port, solange das visuelle Qualitäts-Gate nicht bestanden ist.
- Holger möchte für AI Photo Restore keinen endlosen Kleinschritt-/Tuningpfad mehr, sondern sichtbare große Qualitätsfortschritte.

## Produktziel AI Photo Restore / Extreme Photo Enhance

Das Ziel wurde am 10. September 2026 nochmals präzisiert:

- nicht nur alte Fotos oder Porträts;
- allgemein kleine beziehungsweise qualitativ schlechte Fotos stark verbessern;
- vorhandene echte Bildinformationen möglichst vollständig erhalten;
- fehlende Details durch KI plausibel rekonstruieren;
- Gesichter so identitätsgetreu wie technisch möglich erhalten;
- keine akzeptierte Lösung, die lediglich schärft, glättet oder Farbe/Ton ändert.

Wichtige technische Einordnung:

```text
LQ Original
-> Degradation Removal
-> Structure / Identity Lock
-> Generative Detail Reconstruction
-> High-Frequency Refinement
-> 4x / optionaler späterer NPU-Scaler
```

Exakt verlorene Mikrodaten können mathematisch nicht aus nicht mehr vorhandenen Pixelinformationen zurückgewonnen werden. Der realistische Produktvertrag ist daher:

- vorhandene Geometrie und Identitätsmerkmale hart bewahren;
- teilweise vorhandene Details rekonstruieren;
- nur wirklich fehlende Mikrodetails generativ ergänzen;
- Gesichter mit zusätzlichem Identity-/Geometry-Lock behandeln.

## RestoreNet v3 – abgeschlossen und als Qualitätsweg gestoppt

Nach RestoreNet v1/v2 wurde ein dritter lokaler Capacity-/Quality-Sprint durchgeführt.

Bestätigte Kerndaten:

```text
RESTORENET_V3_PARAMETER_COUNT=63401354
PATCH_SIZE=384
TRAINING_STEPS=1200
AMP_FP16=True
ACTIVATION_CHECKPOINTING=True
GPU=T4 GPU1
TOTAL_MINUTES=55.48
BEST_STEP=1200
```

Numerischer Vergleich Source -> Output:

```text
MEAN_MAE_SOURCE=0.04621803
MEAN_MAE_OUTPUT=0.03374280
PSNR_SOURCE=26.1293
PSNR_OUTPUT=28.0992
MAE_IMPROVED=7/8
```

Strenge visuelle Bewertung:

```text
EYES=PARTIAL
HAIR=PARTIAL
FINGERS_SKIN=FAIL
TEXTILE_WEAVE=PARTIAL
TEXTILE_FIBERS=GOOD/PARTIAL+
SCENE_01=FAIL
FAR_DETAIL=FAIL
FAKE_TEXTURE_MAJOR=NO
PLASTIC_SKIN_MAJOR=NO
RINGING_MAJOR=NO
QUALITY_BOOST_LARGE=NO
QUALITY_PASS=NO
PRODUCT_PASS=NO
QNN_PORT=STOP
```

Zusätzliche wichtige Erkenntnis:

- Die historischen BW-Profile A/B waren gegen farbige CLEAN-Ziele trainiert und erzeugten damit implizit eine ill-posed Colorization-Aufgabe.
- Colorization soll künftig eine getrennte optionale Funktion sein und nicht still in Restoration eingebaut werden.

Entscheidung:

```text
CUSTOM_RESTORENET_INCREMENTAL_PATH=STOP
RESTORENET_V3_QNN_PORT=NO
```

## Strategiewechsel – starker GPU-Teacher zuerst

Nach v1/v2/v3 wurde der kleinschrittige Custom-Model-Pfad beendet.

Neue Strategie:

1. bestehendes starkes GPU-Referenzmodell auf realen Nutzerfotos testen;
2. nur bei deutlich besserer Qualität als Teacher/Qualitätsziel akzeptieren;
3. danach erst Distillation/Adaption/Architektur für den späteren NPU-Pfad planen;
4. GPU-Teacher ist ausschließlich Entwicklungs-/Qualitätsreferenz und niemals finaler Produktfallback.

Verbindliche reale Testbilder:

```text
C:\Users\holge\Desktop\Testbilder\37.jpg
C:\Users\holge\Desktop\Testbilder\3.jpg
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
```

Kaggle persistente Quelle während des Bakeoffs:

```text
/kaggle/input/datasets/hknpustudio/test-bilder/37.jpg
/kaggle/input/datasets/hknpustudio/test-bilder/3.jpg
/kaggle/input/datasets/hknpustudio/test-bilder/142461_s16323864_5162d47f5655.jpg
```

## DiffBIR – technisch lauffähig, visuell klar verworfen

DiffBIR v2.1 wurde auf denselben realen Bildern getestet.

Ergebnis:

```text
DIFFBIR_TECH_PASS=YES
DIFFBIR_QUALITY_PASS=NO
IDENTITY_PRESERVATION=FAIL
CONTENT_PRESERVATION=FAIL
HALLUCINATION=SEVERE
HK_NPU_STUDIO_CANDIDATE=NO
FURTHER_DIFFBIR_TUNING=STOP
```

Insbesondere `3.jpg` und `142461...jpg` zeigten starke Überinterpretation beziehungsweise Content-/Person-Drift. DiffBIR nicht erneut testen.

## VOSR – erster starker Teacher-Kandidat

Getestet wurden:

```text
VOSR_1.4B_ms
VOSR_0.5B_os
```

### VOSR 1.4B Multi-Step

- `3.jpg` und `142461...jpg` erfolgreich.
- `37.jpg` war auf T4 im Full-Frame-Pfad praktisch nicht sinnvoll: nativer tiled-VAE-Lauf erzeugte sehr viele Tiles und wurde nach langer Laufzeit gestoppt.
- Multi-Step bleibt daher allenfalls Qualitätsreferenz, nicht praktischer Produktpfad.

### VOSR 0.5B One-Step

Alle drei Testbilder wurden verarbeitet.

Visuelle Bewertung:

```text
QUALITY_PASS=YES
CONTENT_PRESERVATION=PASS
DETAIL_RECONSTRUCTION=PASS
IDENTITY_PRESERVATION=PARTIAL_PASS
PRODUCT_CANDIDATE=YES
QNN_PORT=NO_YET
```

Stärken:

- deutlicher Detailgewinn;
- Szene und Pose stabiler als bei DiffBIR;
- Haare, Kleidung und Konturen sichtbar verbessert.

Schwäche:

- Augen, Mund/Zähne und andere Gesichtsmikrodetails sind teilweise generativ und nicht 1:1 verifizierbar.

## FiDeSR – aktueller globaler Qualitäts-Sieger

Ausgewählt wurde anschließend:

```text
FiDeSR
High-Fidelity and Detail-Preserving One-Step Diffusion Super-Resolution
```

Offizieller Repo-Stand während des Tests:

```text
REPO=https://github.com/Ar0Kim/FiDeSR.git
COMMIT=8042f139fc3f6f91ac450c41f69a14c45f16ac4b
```

Kaggle-Arbeitsbereich:

```text
/kaggle/working/hk_npu_fidesr_bakeoff
```

Isolierte Runtime während des Tests:

```text
Python 3.10.21
FiDeSR requirements isolated from Kaggle/VOSR environment
```

FiDeSR-spezifischer Checkpoint:

```text
fidesr.pkl
```

### Speicher-/Download-Erkenntnis

Ein erster vollständiger SD2.1-Snapshot füllte `/kaggle/working` bis auf 0 MB, weil zusätzlich unnötige große Root-Checkpoints geladen wurden.

Korrektur:

- fehlgeschlagenen partiellen Snapshot gezielt entfernt;
- nur benötigte Diffusers-Komponenten heruntergeladen;
- redundante `.bin`-Gewichte entfernt, wenn entsprechende `.safetensors` vorhanden waren;
- dadurch `4.81 GB` zurückgewonnen.

### Latent-Tiling-Fix

Erster Lauf scheiterte bei einem Latent von `89x250` mit:

```text
latent_tiled_size=96
RuntimeError: tensor a (89) != tensor b (96)
```

Technischer Fix ohne Modell-/Qualitätsänderung:

```text
latent_tiled_size=64
latent_tiled_overlap=16
```

### Full-Resolution-Limit von `37.jpg`

Bei `37.jpg` scheiterte FiDeSR nach erfolgreichem VAE-/Latent-Tiling an:

```text
RuntimeError: quantile() input tensor is too large
```

Der Fehler liegt in FiDeSRs Detail-Map-/`torch.quantile()`-Pfad auf sehr großen 4x-RGB-Tensoren.

Für den reinen Qualitäts-Bakeoff wurde `37.jpg` ohne Crop und bei erhaltenem Seitenverhältnis auf maximal 1024 px Eingangsseitenlänge begrenzt.

Ergebnis:

```text
FIDESR_37_PASS=YES
37_QUALITY_TEST_MAX_SIDE=1024
37_RUNTIME_MIN=4.67
```

Die zwei kleineren Bilder liefen ohne diesen Workaround vollständig durch.

### FiDeSR Qualitätsbewertung

Kontaktbogen:

```text
/kaggle/working/hk_npu_fidesr_bakeoff/fidesr_final_contact_sheet.jpg
```

Bewertung:

- `37.jpg`: klarer QUALITY PASS; Personen, Boot, Kleidung und Strand bleiben stabil, sichtbarer Schärfe-/Detailgewinn.
- `3.jpg`: stärkster sichtbarer Gewinn; Haare, Bart, Hemd, Augenpartie und Konturen deutlich rekonstruiert. Augen, Zähne/Mund und einzelne Haarstrukturen bleiben teilweise generativ erfunden.
- `142461...jpg`: deutlich verbessert; Körper, Bett, Stoffe und Gesicht bleiben stabil; sauber und wenig aggressiv.

Gesamturteil gegenüber VOSR:

- FiDeSR wirkt insgesamt etwas natürlicher und strukturtreuer.
- VOSR erzeugt an einzelnen Stellen aggressiver zusätzliche Details.
- Für Gesichtstreue ist FiDeSR aktuell vorzuziehen.
- FiDeSR ist damit der derzeit beste globale Teacher-/Baseline-Kandidat, aber noch keine fertige Produktlösung.

Status:

```text
FIDESR_TECH_PASS=YES
FIDESR_QUALITY_PASS=YES
FIDESR_CONTENT_PRESERVATION=PASS
FIDESR_IDENTITY_PRESERVATION=GOOD_NOT_EXACT
FIDESR_DETAIL_RECONSTRUCTION=PASS
FIDESR_HALLUCINATION=LOW_TO_MODERATE_FACE_MICRODETAIL
FIDESR_BETTER_THAN_DIFFBIR=YES
FIDESR_PREFERRED_OVER_VOSR_AS_GLOBAL_BASELINE=YES
FIDESR_PRODUCT_PASS=NO_YET
FIDESR_QNN_PORT=NO_YET
```

## OSDFace – Identity-Kandidat getestet und klar verworfen

OSDFace wurde als separater One-Step-Face-Restoration-/Identity-Vergleich getestet, nicht als globaler Bildersatz.

Repo:

```text
https://github.com/jkwang28/OSDFace.git
```

Kaggle-Arbeitsbereich:

```text
/kaggle/working/hk_npu_osdface_bakeoff
```

Verwendete spezifische Gewichte:

```text
associate_2.ckpt
embedding_change_weights.pth
pytorch_lora_weights.safetensors
```

SD2.1 wurde aus dem vorhandenen FiDeSR-Bestand wiederverwendet; kein zweiter Base-Model-Download.

Mehrere reine Runtime-/Legacy-Dependency-Probleme wurden vor der Inferenz behoben:

- Kaggle `MPLBACKEND` -> Child-Prozess auf `Agg` gesetzt;
- `imageio==2.35.1` plus zugehörige Image-Abhängigkeiten ergänzt;
- `pytorch-lightning==1.0.8`, `test-tube`, `tensorboard` ergänzt;
- `setuptools==69.5.1` für `pkg_resources` ergänzt.

Technischer Single-Test:

```text
INPUT=3.jpg
OSDFACE_EXIT_CODE=0
OUTPUT_MATCH_COUNT=1
OUTPUT=/kaggle/working/hk_npu_osdface_bakeoff/out_osdface_3_only/3.jpg
OSDFACE_3JPG_TECH_PASS=YES
```

Visuelle Bewertung des direkten Vergleichs `SOURCE | OSDFACE`:

- Stirn/Haut stark ausgebrannt beziehungsweise zu weiß;
- Augen und Lider deutlich umgezeichnet;
- Mund und Zähne stark generativ verändert;
- Bartkante und Haaransatz künstlich;
- Gesicht wirkt wie eine neu interpretierte Person statt wie eine identitätsstabile Rekonstruktion.

Entscheidung:

```text
OSDFACE_TECH_PASS=YES
OSDFACE_QUALITY_PASS=NO
OSDFACE_IDENTITY_PRESERVATION=FAIL
OSDFACE_HALLUCINATION=HIGH
OSDFACE_TEST_37=NO
OSDFACE_FURTHER_WORK=STOP
OSDFACE_QNN_PORT=NO
```

OSDFace nicht erneut testen oder für den Produktpfad portieren.

## Nächster Primärschritt – FiDeSR Identity-Lock ohne neues großes Modell

Der nächste Test soll keinen weiteren großen Teacher-Download starten.

Ziel:

```text
SOURCE-Gesichtsgeometrie / Low Frequency festhalten
+
FiDeSR High-Frequency / Detailgewinn übernehmen
```

Leitidee:

- Augenform, Mundlage, Nase, Kopfproportionen und andere harte Gesichtsstrukturen stärker aus dem Original ableiten;
- Haare, Bart, Hautstruktur und andere hochfrequente Details aus FiDeSR übernehmen;
- nicht das gesamte Ergebnis weich zurückblenden;
- zuerst nur Qualitäts-Prototyp auf den bereits vorhandenen Source-/FiDeSR-Paaren;
- noch kein neues Training, kein QNN, keine Produktintegration.

Harter Qualitätsentscheid:

```text
Wenn Identity-Lock nur weichzeichnet oder keinen sichtbaren Vorteil gegenüber purem FiDeSR bringt -> Ansatz sofort verwerfen.
```

Vorgesehener nächster Sprint:

```text
SPRINT-ZEIT=5-10 Min.
WORST_CASE=15 Min.
SPEICHER=<200 MB
HARD_STOP=kein sichtbarer Identity-Vorteil oder Detailverlust
```

## Kaggle Tagesabschluss / Backup 10. September 2026

Vor Feierabend wurde ein kleines transportables Backup erzeugt:

```text
/kaggle/working/HK_NPU_PhotoRestore_20260910_backup.zip
BACKUP_MB=33.5
BACKUP=PASS
```

Enthalten:

```text
hk_npu_fidesr_bakeoff/input/37.jpg
hk_npu_fidesr_bakeoff/input/3.jpg
hk_npu_fidesr_bakeoff/input/142461_s16323864_5162d47f5655.jpg
hk_npu_fidesr_bakeoff/out_fidesr/3.jpg
hk_npu_fidesr_bakeoff/out_fidesr/142461_s16323864_5162d47f5655.jpg
hk_npu_fidesr_bakeoff/out_fidesr_37_quality_test/37.jpg
hk_npu_fidesr_bakeoff/fidesr_final_contact_sheet.jpg
hk_npu_fidesr_bakeoff/FiDeSR/preset/models/fidesr.pkl
```

Die großen SD2.1-Gewichte und Python-VENV-Verzeichnisse wurden bewusst nicht in das Backup aufgenommen.

Wichtig:

```text
BACKUP_CREATED=True
BACKUP_DOWNLOADED_TO_PC=NOT_CONFIRMED_IN_CHAT
```

Holger wurde empfohlen, die ZIP lokal herunterzuladen und zusätzlich `Save Session` in Kaggle zu verwenden. Auf `Save Session` allein soll morgen nicht vertraut werden.

## Statusflags – Feierabend 10. September 2026, aktueller Vorrang

```text
PRODUKTNAME=HK NPU STUDIO
AI_PHOTO_RESTORE_GOAL=GENERAL_EXTREME_PHOTO_ENHANCEMENT
FINAL_PRODUCT_AI_INFERENCE=NPU_QNN_HTP_ONLY

RESTORENET_V1_QUALITY_PASS=False
RESTORENET_V2_QUALITY_PASS=False
RESTORENET_V3_QUALITY_PASS=False
RESTORENET_INCREMENTAL_CUSTOM_PATH=STOP

DIFFBIR_TECH_PASS=True
DIFFBIR_QUALITY_PASS=False
DIFFBIR_FURTHER_WORK=STOP

VOSR_0P5B_OS_TECH_PASS=True
VOSR_0P5B_OS_QUALITY_PASS=True
VOSR_0P5B_OS_IDENTITY=PARTIAL_PASS
VOSR_1P4B_MS_FULL_37_PRACTICAL=False

FIDESR_TECH_PASS=True
FIDESR_QUALITY_PASS=True
FIDESR_CURRENT_GLOBAL_BASELINE=True
FIDESR_FULL_RES_37_TORCH_QUANTILE_LIMIT=True
FIDESR_37_QUALITY_TEST_MAX_SIDE=1024
FIDESR_PRODUCT_PASS=False
FIDESR_QNN_PORT=False

OSDFACE_TECH_PASS=True
OSDFACE_QUALITY_PASS=False
OSDFACE_IDENTITY_PRESERVATION=FAIL
OSDFACE_FURTHER_WORK=STOP
OSDFACE_QNN_PORT=False

KAGGLE_BACKUP_CREATED=True
KAGGLE_BACKUP_FILE=HK_NPU_PhotoRestore_20260910_backup.zip
KAGGLE_BACKUP_SIZE_MB=33.5
KAGGLE_BACKUP_DOWNLOADED_TO_PC=NOT_CONFIRMED

NEXT_SESSION=FIDESR_SOURCE_GEOMETRY_IDENTITY_LOCK_HIGH_FREQUENCY_DETAIL_TEST
BUILD_10_SEPTEMBER=False
INSTALLER_10_SEPTEMBER=False
GIT_ADD_10_SEPTEMBER=False
COMMIT_10_SEPTEMBER=False
PUSH_10_SEPTEMBER=False
```

## Feierabend 10. September 2026

Für heute keine weiteren Teacher-Tests, Trainingsläufe, QNN-Ports, Builds, Installer, Commits oder Pushes durchführen.

Morgen direkt weiter mit:

```text
SOURCE-Geometrie / Low-Frequency Lock
+
FiDeSR High-Frequency Detail
-> direkter visueller Identity-/Detailvergleich
-> nur bei klarem Qualitätsgewinn weiter
```

OSDFace bleibt verworfen und wird nicht erneut gerechnet.

## Handover-Übernahme

Diese vollständige, nur ergänzte Datei als exakt

```text
CHATGPT_HANDOVER.md
```

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die ältere Chronik darf nicht gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.


# CHATGPT_HANDOVER – Ergänzung 11. September 2026 – Photo Restore Teacher-Bakeoff, neuer Qualitätsmaßstab und nächster Einstieg

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Qualitätsregeln – erneut verbindlich

- Sprache weiterhin Deutsch.
- Vor jedem technischen Sprint sichtbar angeben:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Keine unnötigen Rückfragen, wenn der nächste Schritt klar ist.
- Bei Kaggle konkrete vollständige Codezellen liefern, nicht nur Teilhinweise.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern oder löschen.
- Für HK NPU STUDIO gilt weiterhin:
  - finale KI-Inferenz ausschließlich über `NPU / QNN / HTP`;
  - GPU-Teacher sind nur Entwicklungs-/Qualitätsreferenz;
  - kein CPU-/GPU-KI-Fallback als Produktlösung.
- Bewertungsstufen weiterhin strikt trennen:
  - `TECH PASS`
  - `QUALITY PASS`
  - `PRODUCT PASS`
- Ein technisch gültiges Ergebnis ist kein Qualitäts-PASS.
- QNN/NPU-Port erst dann, wenn die visuelle Qualität den Produktmaßstab erfüllt.

## Neuer verbindlicher visueller Qualitätsmaßstab für AI Photo Restore

Holger hat zwei Vorher-/Nachher-Beispiele als verbindlichen Zielstandard festgelegt.

Der Zielzustand ist ausdrücklich **nicht**:

- nur etwas schärfer;
- nur weniger Rauschen;
- nur 4× hochskaliert;
- nur weich geglättet;
- nur künstlich kontrastreicher.

Der verbindliche Zielzustand ist:

```text
kleines / weiches / beschädigtes / detailarmes Foto
->
hochwertig restauriertes, glaubwürdig detailliertes,
natürliches, modernes Foto
```

Dabei gilt:

1. **Identität maximal erhalten**
   - Gesicht, Ausdruck, Kopf-/Körperproportionen, Blick, Mund, Nase und Pose dürfen nicht frei neu interpretiert werden.
   - Bei Gesichtern ist möglichst hohe Identitätstreue wichtiger als spektakuläre, aber erfundene Mikrodetails.

2. **Fehlende Details sichtbar rekonstruieren**
   - Haare
   - Bart
   - Augenregion
   - Haut
   - Hände/Finger
   - Kleidung/Stoff
   - Sand/Wasser/Umgebung
   - kleine technische/strukturelle Details

3. **Bestehende Details bewahren**
   - keine künstlichen neuen Konturen;
   - keine geätzten Haar-/Bartkanten;
   - keine Plastikhaut;
   - kein Verlust von Szene, Personen oder Originalgeometrie.

4. **Natürliches Endergebnis**
   - kein typischer KI-/HDR-Look;
   - keine starke Überschärfung;
   - keine auffälligen Fake-Texturen;
   - keine künstlich dunklen Linien um Gesicht, Bart oder Augen.

5. **Schwarzweiß-Restauration**
   - zunächst Struktur/Details restaurieren;
   - anschließend Colorization als eigener Schritt;
   - natürliche, plausible Haut-, Haar-, Kleidungs-, Wasser-, Himmels- und Umgebungsfarben;
   - Colorization darf die wiederhergestellte Grauwert-/Strukturinformation nicht zerstören.

Verbindliche Produktentscheidung:

```text
QUALITY_TARGET_REFERENCE=HOLGERS_VORHER_NACHHER_BEISPIELE
PRODUCT_PASS_REQUIRES_LARGE_VISIBLE_QUALITY_JUMP=True
MINOR_SHARPENING_ONLY=FAIL
IDENTITY_DRIFT=FAIL
FAKE_TEXTURES=FAIL
OVERPROCESSED_AI_LOOK=FAIL
```

Die beiden gezeigten Beispiele dienen **nur als Qualitätsmaßstab**. Sie sind kein Auftrag an ChatGPT, selbst neue Beispielbilder zu erzeugen.

## Colorization – weiterhin eigener zweiter Produktpfad

Schwarzweiß-Fotos sollen später nicht nur restauriert, sondern auch farbig rekonstruiert werden.

Verbindliche Reihenfolge:

```text
1. Restore / Reconstruct
2. Identity / Structure Preserve
3. Colorize
4. Final detail / natural tone refinement
```

Für HK NPU STUDIO sollen daraus später getrennte Funktionen entstehen:

```text
AI Photo Restore
AI Colorize / Restore Color
```

Auch die Colorization muss im finalen Produkt über NPU/QNN/HTP laufen.

## Kaggle – Session-Wiederherstellung am 11. September

Die neue Kaggle-Session enthielt den vorherigen `/kaggle/working`-Stand nicht mehr.

Der gesicherte Photo-Restore-Stand war in Kaggle als Dataset `Restore` bereits entpackt verfügbar.

Wiederhergestellt wurde nach:

```text
/kaggle/working/hk_npu_fidesr_bakeoff
```

Audit:

```text
FREE_DISK_GB=19.47
SOURCE_3JPG=PASS
FIDESR_3JPG=PASS
ALL_3_TEST_IMAGES=PASS
FIDESR_CHECKPOINT=PASS
RESTORE_FROM_DATASET=PASS
HARD_STOP=NO
```

Die drei Testbilder sowie FiDeSR-Ergebnisse und `fidesr.pkl` waren damit wieder verfügbar.

## Identity-Lock v1 – technisch PASS, qualitativ verworfen

Auf `3.jpg` wurde ein Multi-Frequency-Identity-Lock getestet.

Varianten:

```text
LOCK_STRONG
LOCK_BALANCED
LOCK_LIGHT
```

Technischer Lauf:

```text
PHASE_3W_B=PASS
MODEL_INFERENCE=NO
TRAINING=NO
QNN_PORT=NO
```

Visuelle Bewertung:

- `LOCK_STRONG`: zu weich, verliert Mikrodetail.
- `LOCK_BALANCED`: bester Kompromiss der drei Varianten.
- `LOCK_LIGHT`: fast identisch zu FiDeSR.
- Keine Variante korrigiert Identität sichtbar genug.
- Kein großer Qualitätsfortschritt gegenüber purem FiDeSR.

Entscheidung:

```text
IDENTITY_LOCK_V1_TECH_PASS=True
IDENTITY_LOCK_V1_QUALITY_PASS=False
IDENTITY_LOCK_V1_LARGE_GAIN=False
IDENTITY_LOCK_V1_FURTHER_TUNING=STOP
```

Keine Parameter-Endlosschleife.

## FiDeSR Strong – leicht besser, aber weiterhin unter Produktmaßstab

FiDeSR wurde noch einmal gezielt mit stärkerem High-Frequency-Schwerpunkt getestet.

Erfolgreicher Laufvertrag:

```text
seed=231
process_size=512
upscale=4
align_method=wavelet
vae_encoder_tiled_size=512
vae_decoder_tiled_size=224
latent_tiled_size=64
latent_tiled_overlap=16
mixed_precision=fp16
lf_scale=0.12
hf_scale=0.40
```

Wichtiger Runtime-Fix:

`torch==2.0.1` unterstützt nicht:

```text
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

Für FiDeSR wurde diese Variable vollständig entfernt.

Ergebnis:

```text
EXIT_CODE=0
ELAPSED_MIN=0.50
OUTPUT=/kaggle/working/hk_npu_fidesr_stage2/out_3_strong_corrected/3.jpg
PHASE_3X_B3=PASS
```

Vergleich:

```text
SOURCE
FIDESR BASELINE 0.20/0.20
FIDESR STRONG 0.40/0.12
```

Visuelle Entscheidung:

- Strong etwas besser bei Haarstruktur, Bart, Augenbrauen und Stoff.
- Kein großer neuer Rekonstruktionssprung.
- Gesichtsflächen weiterhin zu glatt/zu flach.
- Keine deutlich neuen glaubwürdigen Mikrodetails.
- Strong ist aber die beste bisherige FiDeSR-Variante.

Gesichert unter:

```text
/kaggle/working/hk_npu_fidesr_bakeoff/fidesr_strong_final/3_FIDESR_STRONG_0.40_0.12.jpg
/kaggle/working/hk_npu_fidesr_bakeoff/fidesr_strong_final/3_BASELINE_vs_STRONG_FULL.jpg
/kaggle/working/hk_npu_fidesr_bakeoff/fidesr_strong_final/3_BASELINE_vs_STRONG_FACE.jpg
```

Der temporäre Stage-2-Runtime-Baum wurde danach entfernt.

Cleanup:

```text
FREE_DISK_AFTER_GB=19.46
FREED_GB=10.01
FIDESR_STRONG_PRESERVED=YES
COMPARISON_PRESERVED=YES
STAGE2_RUNTIME_REMOVED=YES
FIDESR_TUNING_FINISHED=YES
```

Status:

```text
FIDESR_STRONG_CURRENT_REFERENCE=True
FIDESR_STRONG_QUALITY_PASS=PARTIAL
FIDESR_STRONG_PRODUCT_PASS=False
FIDESR_MORE_PARAMETER_TUNING=STOP
```

## PiSA-SR – technisch PASS, qualitativ kein Durchbruch

PiSA-SR wurde als nächster Teacher-Kandidat getestet.

Varianten:

```text
PISA_BALANCED
lambda_pix=1.0
lambda_sem=1.0

PISA_DETAIL
lambda_pix=0.8
lambda_sem=1.3
```

Beide Läufe waren technisch erfolgreich.

Direkter Vergleich:

```text
SOURCE
FIDESR STRONG
PISA BALANCED
PISA DETAIL
```

Visuelle Bewertung:

### PiSA Balanced

- minimal detailreicher als FiDeSR Strong;
- kein klarer Qualitätsvorsprung;
- Gesicht bleibt zu glatt;
- kein ausreichender Rekonstruktionssprung.

### PiSA Detail

- stärkerer Detail-/Kantenoutput;
- Bart, Haare, Augen und Kleidung stellenweise geätzt/überschärft;
- unnatürlicher als FiDeSR Strong;
- Produktqualität nicht akzeptabel.

Entscheidung:

```text
PISA_TECH_PASS=True
PISA_BALANCED_QUALITY_PASS=PARTIAL
PISA_DETAIL_QUALITY_PASS=False
PISA_CLEARLY_BEATS_FIDESR=False
PISA_PRODUCT_PASS=False
PISA_FURTHER_TUNING=STOP
```

Ergebnisse dauerhaft gesichert:

```text
/kaggle/working/hk_npu_fidesr_bakeoff/pisa_final_comparison/3_PISA_BALANCED.jpg
/kaggle/working/hk_npu_fidesr_bakeoff/pisa_final_comparison/3_PISA_DETAIL.jpg
/kaggle/working/hk_npu_fidesr_bakeoff/pisa_final_comparison/3_SOURCE_FIDESR_PISA_FULL.jpg
/kaggle/working/hk_npu_fidesr_bakeoff/pisa_final_comparison/3_SOURCE_FIDESR_PISA_FACE.jpg
```

PiSA-Runtime danach entfernt:

```text
FREE_DISK_AFTER_GB=19.46
FREED_GB=9.97
PISA_RESULTS_PRESERVED=YES
PISA_RUNTIME_REMOVED=YES
PISA_TUNING_FINISHED=YES
```

## TVT – technisch PASS, qualitativ schwächer als FiDeSR Strong

TVT wurde als weiterer Teacher getestet.

Kernkomponenten:

```text
TVTUNet
VAED4
model_TVT.pkl
```

Für den ersten Qualitätsvergleich wurde der sehr große RAM-Captioner bewusst nicht verwendet.

Stattdessen:

```text
TVT_MODE=CORE_FIXED_PROMPT
PROMPT="clean, high-resolution, 8k"
RAM_CAPTIONER_USED=NO
RAM_5_63GB_DOWNLOADED=NO
```

Technischer Lauf:

```text
TVT_EXIT_CODE=0
TVT_ELAPSED_MIN=0.50
OUTPUT=/kaggle/working/hk_npu_tvt_bakeoff/out_3_tvt_core/3.jpg
FREE_DISK_END_GB=9.40
TVTUNET=YES
VAED4=YES
TVT_MODEL=YES
UPSCALE=4
TILED_SIZE=96
TILED_OVERLAP=32
PHASE_3Z=PASS
```

Direkter Vergleich:

```text
SOURCE
FIDESR STRONG
TVT CORE
```

Visuelle Bewertung:

- TVT erhält Szene und Identität brauchbar.
- Gesichtsflächen wirken glatter.
- Haar-/Bartstruktur ist gröber und weniger natürlich als bei FiDeSR Strong.
- Kein zusätzlicher glaubwürdiger Mikrodetailgewinn.
- TVT schlägt FiDeSR Strong nicht.

Entscheidung:

```text
TVT_TECH_PASS=True
TVT_QUALITY_PASS=False
TVT_IDENTITY=ACCEPTABLE_NOT_BETTER
TVT_DETAIL_RECONSTRUCTION=WEAKER_THAN_FIDESR_STRONG
TVT_PRODUCT_PASS=False
TVT_FURTHER_TUNING=STOP
```

Wichtig:

```text
TVT_RUNTIME_CLEANUP_AFTER_RESULT=NOT_CONFIRMED
```

Der TVT-Arbeitsbereich kann in der aktuellen Kaggle-Session noch unter

```text
/kaggle/working/hk_npu_tvt_bakeoff
```

vorhanden sein.

## Aktuelle Teacher-Rangfolge

Aktueller Stand nach allen Sichtprüfungen:

```text
1. FiDeSR Strong 0.40 / 0.12
2. PiSA Balanced
3. VOSR 0.5B One-Step
4. TVT Core
```

Nicht mehr weiterverfolgen:

```text
DiffBIR
OSDFace
Identity-Lock v1
PiSA Detail
weiteres FiDeSR-Mikrotuning
weiteres TVT-Mikrotuning
```

Wichtig:

**Auch Platz 1 erfüllt den neuen verbindlichen Qualitätsmaßstab noch nicht.**

Damit ist:

```text
CURRENT_BEST_TEACHER=FIDESR_STRONG
CURRENT_BEST_TEACHER_PRODUCT_PASS=False
```

## Nächster Teacher-Kandidat – FaithDiff

Als nächster größerer Qualitätskandidat wurde festgelegt:

```text
FaithDiff
```

Begründung:

- expliziter Fokus auf faithful image super-resolution;
- Zielbereiche umfassen Old Photo Revival, Social Media Restoration und allgemeines Image Enhancement;
- soll stärker auf fidelity-preserving generative reconstruction ausgerichtet sein als die zuletzt getesteten kleinen Variationen;
- Single-GPU-/Offload-Pfade sind grundsätzlich vorhanden.

Status:

```text
FAITHDIFF_SELECTED_AS_NEXT_CANDIDATE=True
FAITHDIFF_SETUP_STARTED=False
FAITHDIFF_INFERENCE_STARTED=False
FAITHDIFF_QUALITY_RESULT=PENDING
```

Noch kein FaithDiff-Download, kein Lauf und kein Ergebnis in diesem Chat bestätigt.

## Kaggle-Sicherungsstand 11. September

Am Morgen wurde der ältere Sicherungsstand wiederhergestellt und die neuen FiDeSR-/PiSA-/TVT-Ergebnisse erzeugt.

Ein neuer Backup-Block für

```text
HK_NPU_PhotoRestore_20260911_backup.zip
```

wurde vorbereitet, aber bis zu diesem Handover-Stand ist die erfolgreiche Ausführung **nicht bestätigt**.

Daher:

```text
KAGGLE_BACKUP_20260910_EXISTS_AS_RESTORE_DATASET=True
KAGGLE_BACKUP_20260911_CREATED=NOT_CONFIRMED
KAGGLE_BACKUP_20260911_DOWNLOADED_TO_PC=NOT_CONFIRMED
```

Wenn die aktuelle Kaggle-Session noch läuft, vor Beenden unbedingt:

1. relevante Results sichern;
2. `fidesr.pkl` sichern;
3. Source-Bilder sichern;
4. FiDeSR Strong sichern;
5. PiSA-Vergleiche sichern;
6. TVT-Ergebnis und TVT-Vergleiche sichern;
7. danach neue ZIP lokal herunterladen.

Große Python-VENVs, SD2.1-Basismodelle, PiSA-/TVT-Runtimes müssen nicht ins Backup.

## Verbindlicher nächster Einstieg

Wenn wieder Zeit vorhanden ist:

### 1. Kaggle-Sicherung zuerst prüfen

Falls `HK_NPU_PhotoRestore_20260911_backup.zip` noch nicht erstellt und lokal heruntergeladen wurde:

```text
BACKUP ZUERST
```

### 2. TVT-Runtime bereinigen

Nur wenn Ergebnisse vorher gesichert wurden:

```text
/kaggle/working/hk_npu_tvt_bakeoff
```

löschen, um Speicher zurückzugewinnen.

### 3. FaithDiff starten

Nur:

```text
3.jpg
```

Zuerst genau ein kontrollierter Teacher-Test.

Kein Parameter-Sweep.

Harter Qualitätsentscheid:

```text
Wenn FaithDiff FiDeSR Strong nicht klar sichtbar schlägt
oder Identität sichtbar driftet
-> FaithDiff sofort verwerfen.
```

Noch kein QNN-Port.

## Statusflags – Stand 11. September 2026

```text
PRODUKTNAME=HK NPU STUDIO
AI_PHOTO_RESTORE_GOAL=GENERAL_EXTREME_PHOTO_ENHANCEMENT
QUALITY_TARGET_REFERENCE=HOLGERS_VORHER_NACHHER_BEISPIELE
FINAL_PRODUCT_AI_INFERENCE=NPU_QNN_HTP_ONLY

RESTORENET_INCREMENTAL_CUSTOM_PATH=STOP
DIFFBIR_FURTHER_WORK=STOP
OSDFACE_FURTHER_WORK=STOP

VOSR_0P5B_OS_QUALITY_PASS=True
VOSR_0P5B_OS_IDENTITY=PARTIAL_PASS

FIDESR_STRONG_CURRENT_REFERENCE=True
FIDESR_STRONG_HF_SCALE=0.40
FIDESR_STRONG_LF_SCALE=0.12
FIDESR_STRONG_PRODUCT_PASS=False
FIDESR_MORE_PARAMETER_TUNING=STOP

IDENTITY_LOCK_V1_QUALITY_PASS=False
IDENTITY_LOCK_V1_FURTHER_TUNING=STOP

PISA_TECH_PASS=True
PISA_BALANCED_QUALITY_PASS=PARTIAL
PISA_DETAIL_QUALITY_PASS=False
PISA_PRODUCT_PASS=False
PISA_FURTHER_TUNING=STOP

TVT_TECH_PASS=True
TVT_QUALITY_PASS=False
TVT_PRODUCT_PASS=False
TVT_FURTHER_TUNING=STOP

FAITHDIFF_SELECTED_AS_NEXT_CANDIDATE=True
FAITHDIFF_STARTED=False

BLACK_WHITE_COLORIZATION_REQUIRED=True
COLORIZATION_SEPARATE_STAGE=True
COLORIZATION_FINAL_NPU_REQUIRED=True

KAGGLE_BACKUP_20260910_RESTORED=True
KAGGLE_BACKUP_20260911_CREATED=NOT_CONFIRMED
KAGGLE_BACKUP_20260911_DOWNLOADED_TO_PC=NOT_CONFIRMED

QNN_PORT_PHOTO_RESTORE=False
PRODUCT_PASS_PHOTO_RESTORE=False

BUILD_11_SEPTEMBER=False
INSTALLER_11_SEPTEMBER=False
GIT_ADD_11_SEPTEMBER=False
COMMIT_11_SEPTEMBER=False
PUSH_11_SEPTEMBER=False
```

## Handover-Regel – unverändert verbindlich

Diese Datei muss immer als vollständige Gesamtchronik behandelt werden.

Bei der nächsten Aktualisierung:

- ältere Inhalte niemals löschen;
- neueren Stand nur unten anhängen;
- bei Widersprüchen hat der neueste Abschnitt Vorrang;
- Download-Dateiname immer exakt:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt die Datei anschließend über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende zentrale Handover-Datei niemals mit einer verkürzten Fassung überschreiben.

# CHATGPT_HANDOVER – Ergänzung 11. September 2026 – Finaler Photo-Restore-Teacher, Qualitätsentscheidung und Tagesbackup

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsmodus – heute erneut verbindlich bestätigt

- Sprache mit Holger weiterhin Deutsch.
- Bei technischen Sprints vorab immer sichtbar angeben:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Für Kaggle immer vollständige, direkt kopierbare Codeblöcke liefern; keine Anweisungen wie „ändere Zeile X“.
- Kaggle-Code vor Ausgabe gegen den tatsächlich verwendeten Repository-Stand, Python-/Torch-/CUDA-Versionen, Imports, Pfade und bereits vorhandene Dateien prüfen.
- Keine unnötigen Neuinstallationen, Redownloads oder Blind-Retries.
- Keine weiteren Open-Model-Bakeoffs nach der heutigen finalen Entscheidung.
- Das Produktziel bleibt strikt:

```text
AI-Inferenz in HK NPU STUDIO = QNN / HTP / NPU
```

CPU darf nur Orchestrierung, I/O, Resize, Masken-/Tensoraufbereitung und Compositing übernehmen. CPU-/GPU-AI-Fallbacks sind kein Produktziel.

## Qualitätsziel – unverändert

Holgers bereitgestellte Vorher-/Nachher-Beispiele bleiben die verbindliche visuelle Zielreferenz für `AI Photo Restore`.

Gefordert sind insbesondere:

- sehr großer sichtbarer Rekonstruktions-/Upscale-Sprung;
- Identität, Gesichtsausdruck, Proportionen, Pose, Personenzahl und Szene müssen erhalten bleiben;
- plausible Rekonstruktion fehlender Details bei Augen, Mund, Haaren, Bart, Haut, Händen, Kleidung und Umgebung;
- keine Plastikhaut;
- keine geätzten Haare/Bärte;
- keine künstliche Mikrotextur;
- kein HDR-/AI-Look;
- kein aggressives Überschärfen;
- vorhandener Bildinhalt muss erhalten bleiben;
- Schwarzweiß→Farbe bleibt ein separater späterer Schritt.

Wichtig: fehlende Mikrodetails können nicht sicher „zurückgeholt“ werden. Ziel ist starke Identitäts-/Geometriesicherung plus plausible Rekonstruktion.

## Heute abgeschlossene Kandidatenbewertung

### FaithDiff – vollständig getestet

Offizieller Stand:

```text
Repo: JyChen9811/FaithDiff
Commit: f11af6c81a03784ba51284b5dbe9943f05b69d81
Runtime: /root/hk_npu_faithdiff
Python: 3.12 venv
Torch: 2.10 CUDA 12.8
```

Verwendete Komponenten:

- FaithDiff.bin
- RealVisXL-Teilmodell
- VAE
- Diffusers 0.28
- Transformers 4.46.1
- Accelerate 1.1.1
- huggingface_hub 0.25.2

One-shot-Test auf `3.jpg`:

```text
4×
20 steps
guidance=5
seed=42
start_point=lr
AdaIN
kein LLaVA
kein BSRNet
```

Ergebnisdatei:

```text
/kaggle/working/hk_npu_faithdiff_bakeoff/one_shot_3jpg/3_FAITHDIFF_OFFICIAL_ONESHOT.png
```

Vergleichsdateien:

```text
3_SOURCE_FIDESR_FAITHDIFF_FULL.jpg
3_SOURCE_FIDESR_FAITHDIFF_FACE.jpg
```

Bewertung:

```text
FAITHDIFF_TECH_PASS=True
FAITHDIFF_QUALITY_PASS=False
FAITHDIFF_PRODUCT_PASS=False
FAITHDIFF_IDENTITY=ACCEPTABLE_BUT_NOT_IMPROVED
FAITHDIFF_FURTHER_TUNING=STOP
```

FaithDiff war glatter/flacher als FiDeSR Strong und bei Augen, Mund, Bart und Kleidung schwächer. Kein Benchmark-Sprung.

Hinweis: Ein Face-ROI-Vergleichsskript behandelte `(x, y, w, h)` versehentlich als `(x1, y1, x2, y2)`. Das beeinflusst nicht das Gesamturteil, weil der Full-Frame-Vergleich ausreichend war.

## Wiederhergestellter Kaggle-Backup-Stand

Der Sep-11-Backup-Datensatz wurde in einem frischen Kaggle-Notebook erfolgreich wiederhergestellt.

Bestätigt:

```text
SOURCE_3JPG=PASS
FIDESR_STRONG=PASS
PISA_RESULTS=PASS
TVT_RESULT=PASS
BACKUP_20260911_RESTORED=PASS
```

Wiederhergestellte Arbeitsordner:

```text
/kaggle/working/hk_npu_fidesr_bakeoff
/kaggle/working/hk_npu_tvt_bakeoff
```

Freier Speicher zu diesem Zeitpunkt:

```text
/kaggle/working ~19.36 GB
/root ~986 GB
```

## Finale Open-Model-Teacher-Strategie

Holger hat ausdrücklich entschieden:

```text
„ich möchte jetzt die beste lösung und nicht mehr rumtesten“
```

Daraufhin wurde die letzte Open-Model-Teacher-Pipeline fest eingefroren als:

```text
CODSR Full Frame
-> SSDiff Face Restore
-> source-geometry / identity locked composite
```

Keine weiteren Kandidaten danach.

### CODSR

Offizielles Repo:

```text
https://github.com/Chanson94/CODSR
Commit: 2ad75f5cd4ba58c045301fcd6f06168ac017c2b6
```

Lokal/Kaggle:

```text
/root/hk_npu_final_teacher/CODSR
/root/hk_npu_final_teacher/teacher_env
```

CODSR-Checkpoint:

```text
/root/hk_npu_final_teacher/models/CODSR/codsr.pkl
Bytes: 143606151
SHA256: cc2eee227bd09d30d4e8841a5371aa31309c530ce7a527ce8e1d26d87e527cb9
```

DAPE:

```text
/root/hk_npu_final_teacher/models/CODSR/DAPE.pth
SHA256: a7028be2edcbe9ab0bd1c4ab6f2a2a86f4b44d32261a4faa50ae10fdd9b2feba
```

RAM:

```text
/root/hk_npu_final_teacher/models/CODSR/RAM/ram_swin_large_14m.pth
SHA256: 15c729c793af28b9d107c69f85836a1356d76ea830d4714699fb62e55fcc08ed
```

SD2.1-Original war ohne HF-Token nicht erreichbar. Verwendet wurde ein öffentlicher Mirror der benötigten Diffusers-Komponenten unter:

```text
/root/hk_npu_final_teacher/models/CODSR/SD21Base
```

CODSR Runtime:

```text
Python 3.10.20
Torch 2.0.1+cu118
Torchvision 0.15.2+cu118
Diffusers 0.25.0
Transformers 4.40.0
PEFT 0.9.0
Xformers 0.0.20
NumPy 1.26.4
CUDA_AVAILABLE=True
GPU=Tesla T4
CODSR_RUNTIME=PASS
```

CODSR Checkpoint-Gate:

```text
KEY_COUNT=12
CODSR_CHECKPOINT_GATE=PASS
CODSR_CONSTRUCT=PASS
CODSR_READY_FOR_INFERENCE=YES
```

CODSR-Konstruktion benötigte nur etwa 2.56 GB Peak Allocation und war damit kein VRAM-Blocker.

## SSDiff – Runtimeaufbau und notwendige Kompatibilitätsfixes

Offizielles Repo:

```text
https://github.com/PRIS-CV/SSDiff
Commit: ebe79d059e56557c4301c70a460f45a6f8e67f9a
```

Lokal/Kaggle:

```text
/root/hk_npu_final_teacher/SSDiff
/root/hk_npu_final_teacher/ssdiff_env
Python 3.8.20
```

Offizielle Modelle:

```text
/root/hk_npu_final_teacher/SSDiff/models/iddpm_ffhq512_ema500000.pth
/root/hk_npu_final_teacher/SSDiff/models/face_parsing/resnet34.pt
/root/hk_npu_final_teacher/SSDiff/models/restorer/codeformer.pth
/root/hk_npu_final_teacher/SSDiff/models/vqgan/vqgan_code1024.pth
/root/hk_npu_final_teacher/SSDiff/CAP_VSTNet/checkpoints/photo_image.pt
```

Technische Runtime-Hürden und Fixes:

1. `setuptools==80.9.0` war mit Python 3.8 inkompatibel.
   Final verwendet:

```text
pip==24.3.1
setuptools==75.3.4
wheel==0.45.1
```

2. uv-Python-3.8 / Setuptools-Distutils-Konflikt:

```text
SETUPTOOLS_USE_DISTUTILS=stdlib
PYTHONNOUSERSITE=1
```

3. `basicsr` fehlte trotz indirekter Nutzung durch CodeFormer.
   Installiert:

```text
basicsr==1.4.2
```

4. PyPI-BasicSR 1.4.2 enthielt die von SSDiff/CodeFormer erwartete Funktion `get_device()` nicht.
   Deshalb wurde ausschließlich in der Kaggle-Runtime ein Kompatibilitätspatch in:

```text
/root/hk_npu_final_teacher/ssdiff_env/lib/python3.8/site-packages/basicsr/utils/misc.py
```

ergänzt.

Backup:

```text
.../basicsr/utils/misc.py.before_hk_npu_ssdiff_patch
```

Verifiziert:

```text
GET_DEVICE=cuda
GET_DEVICE_0=cuda:0
BASICSR_CODEFORMER_COMPAT=PASS
```

5. SSDiff importierte `matplotlib`, obwohl es im Haupt-Requirements-Vertrag nicht enthalten war. Runtime wurde entsprechend ergänzt.

6. SSDiffs Face-Parsing-ResNet verwendete mit torchvision 0.15.2 einen inkompatiblen Aufruf:

```python
weights.get_state_dict(progress=progress, check_hash=True)
```

Torchvision 0.15.2 unterstützt nur:

```python
get_state_dict(self, progress)
```

Daher wurde ausschließlich diese eine Stelle in:

```text
/root/hk_npu_final_teacher/SSDiff/guided_diffusion/face_parsing/resnet.py
```

auf den kompatiblen Aufruf geändert.

Backup:

```text
.../resnet.py.before_torchvision_015_compat
```

### Vollständiger SSDiff-Runtime-Nachweis

Face-Parser:

```text
CREATE_FACE_PARSING=PASS
FACE_PARSING_CHECKPOINT_TYPE=collections.OrderedDict
MISSING_KEYS=0
UNEXPECTED_KEYS=0
OUTPUT_0_SHAPE=(1,19,512,512)
OUTPUT_1_SHAPE=(1,19,512,512)
OUTPUT_2_SHAPE=(1,19,512,512)
OUTPUT_3_SHAPE=(1,256,64,64)
FACE_PARSING_CHECKPOINT_LOAD=PASS
FACE_PARSING_CUDA_FORWARD=PASS
```

Offizieller finaler SSDiff-Start mit leerem Input:

```text
Creating model and diffusion...
Loading restorer for codebook...
Loading face pasring prediction...
Sampling...
Sampling complete!
EXIT_CODE=0
SSDIFF_FINAL_FULL_INIT=PASS
SSDIFF_RUNTIME_FULL_PREFLIGHT=PASS
```

Damit war die komplette SSDiff-Runtime technisch bereit.

## Finaler echter Teacher-Lauf auf `3.jpg`

Quelle:

```text
/kaggle/working/hk_npu_final_teacher/3.jpg
```

Pipeline:

```text
CODSR Full Frame 4×
-> Source Geometry Lock
-> SSDiff old_photo_restoration_pseudo
-> SSDiff old_photo_restoration
-> Identity-Locked Composite
```

CODSR verwendete den offiziellen Testpfad mit:

```text
upscale=4
process_size=512
align_method=adain
mixed_precision=fp16
seed=42
```

SSDiff verwendete offiziell:

Pseudo:

```text
task=old_photo_restoration_pseudo
guidance_scale=0.001
seed=4321
```

Final:

```text
task=old_photo_restoration
guidance_scale=0.0035
seed=4321
```

Source-Geometry-Lock:

- Face-Geometrie wurde aus einer geometrisch unveränderten 4×-Vergrößerung des Originals bestimmt.
- Dieselbe affine Geometrie wurde auf CODSR angewendet.
- SSDiff durfte damit die Gesichtsposition nicht frei verschieben.
- Zero-Scratch-Mask, weil keine künstliche Kratzerbehandlung erzwungen werden sollte.

Identity-Locked Composite:

- Rückwarp über source-basierte Affine-Matrix.
- CODSR-Chroma blieb erhalten; keine Colorization.
- Tieffrequente Gesichtsgeometrie überwiegend aus CODSR.
- SSDiff lieferte primär mittlere/feine Detailanteile.
- Soft Inner-Face-Mask zur Begrenzung des Eingriffs.

Finale Laufzeit:

```text
TOTAL_ELAPSED_MIN=6.30
```

Finale Artefakte:

```text
FINAL_IMAGE=/kaggle/working/hk_npu_final_teacher/final_codsr_ssdiff_3jpg/07_locked_composite/3_FINAL_CODSR_SSDIFF_LOCKED.png

COMPARISON=/kaggle/working/hk_npu_final_teacher/final_codsr_ssdiff_3jpg/08_comparison/3_SOURCE_FIDESR_FINAL_COMPARISON.png
```

Technischer Abschluss:

```text
SOURCE_3JPG=PASS
CODSR_FULL_FRAME=PASS
SOURCE_GEOMETRY_LOCK=PASS
SSDIFF_PSEUDO=PASS
SSDIFF_FINAL=PASS
IDENTITY_LOCKED_COMPOSITE=PASS
COLORIZATION_APPLIED=NO
HARD_STOP=NO
```

## Finale visuelle Qualitätsentscheidung

Holger stellte den direkten Vergleich bereit:

```text
SOURCE | FiDeSR Strong | FINAL CODSR + SSDiff
```

Bewertung:

```text
CODSR_SSDIFF_TECH_PASS=True
CODSR_SSDIFF_QUALITY_PASS=False
CODSR_SSDIFF_PRODUCT_PASS=False
```

Konkrete Gründe:

- Identität grundsätzlich erkennbar, aber SSDiff verändert Augenpartie, Mund/Zähne, Nase und Bartkontur subtil.
- Haare enthalten rechts neue lockige/strähnige Strukturen, die im Original nicht belegt sind.
- Haut ist zu glatt und wirkt teilweise künstlich/wachsartig.
- Bart verliert gegenüber FiDeSR natürliche Einzelstruktur.
- Augen sind im Final weicher und weniger glaubwürdig als bei FiDeSR Strong.
- Kleidung verliert feine Textur.
- Gesamteindruck wirkt eher wie KI-Neuinterpretation als hochpräzise Restaurierung.
- Holgers Referenzstandard wird klar nicht erreicht.

Zusätzliche zentrale Erkenntnis:

```text
SSDiff verschlechtert einige zuvor gute CODSR/FiDeSR-Details wieder.
```

Damit lohnt sich die zusätzliche Pipeline-Komplexität nicht.

## Verbindliche Entscheidung nach dem finalen Open-Model-Test

Ab sofort:

```text
NO_MORE_OPEN_MODEL_BAKEOFFS=True
NO_MORE_PARAMETER_SWEEPS=True
CODSR_SSDIFF_REJECTED=True
FAITHDIFF_REJECTED=True
PISA_REJECTED=True
TVT_REJECTED=True
VOSR_REJECTED_AS_PRODUCT=True
OSDFACE_REJECTED=True
DIFFBIR_REJECTED=True
RESTORENET_INCREMENTAL_PATH=STOP
```

FiDeSR Strong bleibt ausschließlich als Qualitätsbaseline:

```text
HF=0.40
LF=0.12
```

Status:

```text
FIDESR_STRONG_CURRENT_REFERENCE=True
FIDESR_STRONG_PRODUCT_PASS=False
```

Die Teacher-Pipeline CODSR+SSDiff wird **nicht** auf QNN/NPU portiert.

## Neue Produktstrategie: eigener HK NPU Photo Restore Student

Nächster Entwicklungsweg:

```text
High-quality Ground Truth
-> synthetische realistische Alt-/Low-Res-Degradation
-> HK NPU Photo Restore Student
-> Vergleich gegen echtes Ground Truth
-> ONNX
-> QNN
-> HTP / NPU
-> HK NPU STUDIO
-> AI Photo Restore
```

Warum:

- kein fremdes Diffusionsmodell soll erfundene Gesichtsdetails als Wahrheit vorgeben;
- Training hat echtes Ground Truth;
- Identität, Augen, Mund, Nase, Haare, Bart, Kleidung und Struktur können gezielt gegen reale Zielbilder optimiert werden;
- Architektur kann von Anfang an QNN-/HTP-freundlich gebaut werden.

Geplante Losses:

- Pixel-/Charbonnier-Loss
- Perceptual Loss
- Gradient-/Edge-Loss
- Face-Identity-Loss

Architekturziel:

- überwiegend Conv-/Residual-Blöcke;
- feste Shapes;
- keine unnötigen dynamischen oder exotischen Attention-Pfade;
- von Beginn an ONNX/QNN/HTP-kompatibel denken.

Qualitäts-Gate vor jeder QNN-Portierung:

```text
Source
|
FiDeSR Strong
|
HK NPU Restore Student
```

Der Student muss FiDeSR Strong sichtbar schlagen und gleichzeitig Identität/Proportionen/Originalinhalt besser bewahren.

Wenn nicht:

```text
DO_NOT_PORT_TO_QNN
```

Colorization bleibt separat und wird nicht in den Restore-Studenten vermischt.

## End-of-Day-Backup – 11. September 2026

Zum Feierabend wurde ein vollständiges, kompaktes Tagesbackup erstellt.

Backup-Ordner:

```text
/kaggle/working/HK_NPU_PHOTORESTORE_EOD_20260911
```

ZIP:

```text
/kaggle/working/HK_NPU_PHOTORESTORE_EOD_20260911.zip
```

Gesichert wurden:

- kompletter finaler CODSR+SSDiff-Run;
- finales Vergleichsbild;
- `3.jpg` Source;
- FiDeSR Strong Referenz;
- SSDiff-BasicSR-Kompatibilitätspatch plus Original-Backup;
- SSDiff-ResNet/torchvision-Kompatibilitätspatch plus Original-Backup;
- Git-Commit-/Status-/Diff-Informationen der CODSR-/SSDiff-Repos;
- `pip freeze` / Python-Versionen beider Umgebungen;
- SHA-256-Manifest der gesicherten Resultate;
- `HANDOVER_NEXT_SESSION.txt` mit heutiger Qualitätsentscheidung und nächstem Entwicklungsweg.

Finales Backup-Gate:

```text
FINAL_RUN_SAVED=YES
FIDESR_REFERENCE_SAVED=True
SSDIFF_PATCHES_SAVED=YES
REPO_STATE_SAVED=YES
PYTHON_ENVIRONMENTS_SAVED=YES
HANDOVER_SAVED=YES
BACKUP_READY=YES
ZIP=/kaggle/working/HK_NPU_PHOTORESTORE_EOD_20260911.zip
HARD_STOP=NO
```

Wichtig:

`/kaggle/working` ist nicht dauerhaft. Die ZIP muss zusätzlich auf Holgers PC heruntergeladen oder als privates Kaggle-Dataset persistent gespeichert werden.

Die großen CODSR-/SSDiff-Modellgewichte wurden bewusst nicht erneut in die kleine EOD-ZIP kopiert, weil die heutige Pipeline als Produktkandidat verworfen wurde und diese Modelle für den nächsten Student-Pilot nicht benötigt werden.

## Verbindlicher Einstieg beim nächsten Arbeitstag

Nicht erneut FaithDiff, CODSR, SSDiff, FiDeSR-Parameter oder andere Open-Model-Kandidaten testen.

Direkt starten mit:

```text
HK NPU PHOTO RESTORE STUDENT PILOT
```

Reihenfolge:

1. kleine QNN-freundliche Student-Architektur festlegen;
2. synthetische Degradationspipeline definieren;
3. Ground-Truth-Trainingsdaten strukturieren;
4. kleiner Pilot auf Kaggle/GPU;
5. `3.jpg` als reales externes Testbild verwenden;
6. Vergleich gegen FiDeSR Strong;
7. nur bei sichtbarem Qualitätsgewinn weiter zu ONNX/QNN/HTP;
8. erst danach Integration in HK NPU STUDIO als `AI Photo Restore`.

Keine großen Trainingsläufe starten, bevor der Pilot fachlich Sinn ergibt.

## Statusflags – Feierabend 11. September 2026

```text
PRODUKTNAME=HK NPU STUDIO
AI_PHOTO_RESTORE_TARGET=GENERAL_EXTREME_PHOTO_ENHANCEMENT
FINAL_PRODUCT_AI_INFERENCE=NPU_QNN_HTP_ONLY

FAITHDIFF_TECH_PASS=True
FAITHDIFF_QUALITY_PASS=False
FAITHDIFF_PRODUCT_PASS=False
FAITHDIFF_FURTHER_TUNING=STOP

CODSR_TECH_PASS=True
SSDIFF_TECH_PASS=True
CODSR_SSDIFF_FINAL_TEACHER_TECH_PASS=True
CODSR_SSDIFF_FINAL_TEACHER_QUALITY_PASS=False
CODSR_SSDIFF_FINAL_TEACHER_PRODUCT_PASS=False
CODSR_SSDIFF_QNN_PORT=False

FIDESR_STRONG_CURRENT_REFERENCE=True
FIDESR_STRONG_HF_SCALE=0.40
FIDESR_STRONG_LF_SCALE=0.12
FIDESR_STRONG_PRODUCT_PASS=False

NO_MORE_OPEN_MODEL_BAKEOFFS=True
NO_MORE_RESTORE_PARAMETER_SWEEPS=True

HK_NPU_PHOTO_RESTORE_STUDENT_SELECTED=True
HK_NPU_PHOTO_RESTORE_STUDENT_TRAINED=False
HK_NPU_PHOTO_RESTORE_STUDENT_QUALITY_GATE=False
HK_NPU_PHOTO_RESTORE_STUDENT_ONNX=False
HK_NPU_PHOTO_RESTORE_STUDENT_QNN=False
HK_NPU_PHOTO_RESTORE_STUDENT_HTP=False
HK_NPU_PHOTO_RESTORE_STUDIO_INTEGRATION=False

COLORIZATION_SEPARATE_STAGE=True
COLORIZATION_FINAL_NPU_REQUIRED=True

EOD_BACKUP_20260911_READY=True
EOD_BACKUP_20260911_ZIP=/kaggle/working/HK_NPU_PHOTORESTORE_EOD_20260911.zip
EOD_BACKUP_20260911_PERSISTENT_COPY=TO_BE_CONFIRMED

BUILD_11_SEPTEMBER=False
INSTALLER_11_SEPTEMBER=False
GIT_ADD_11_SEPTEMBER=False
COMMIT_11_SEPTEMBER=False
PUSH_11_SEPTEMBER=False

NEXT_SESSION=HK_NPU_PHOTO_RESTORE_STUDENT_PILOT
```

## Handover-Regel – unverändert verbindlich

Diese Datei bleibt die vollständige Gesamtchronik.

Bei jeder nächsten Aktualisierung:

- ältere Inhalte niemals löschen;
- neuen Stand ausschließlich unten anhängen;
- bei Widersprüchen hat der neueste Abschnitt Vorrang;
- Download-Dateiname immer exakt:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt die Datei anschließend über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende zentrale Handover-Datei niemals mit einer verkürzten Fassung überschreiben.

# CHATGPT_HANDOVER – Ergänzung 12. September 2026 – HK NPU Photo Restore Student: QNN-Feasibility, Training und klarer Quality-Fail

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Neue verbindliche Arbeits- und Kommunikationsregeln

- Holger möchte **keine unnötigen Rückfragen**. Wenn der nächste technische Schritt aus dem vorliegenden Stand eindeutig ist, direkt liefern.
- Bei technischen Sprints weiterhin vor dem ausführbaren Block sichtbar angeben:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Wenn Code auszuführen ist, immer einen **vollständigen direkt einfügbaren Codeblock** liefern; keine fragmentarischen Änderungsanweisungen.
- Bei längeren Kaggle-Zellen sichtbaren Timer/Fortschritt ausgeben, soweit praktisch.
- Holger entscheidet selbst, **wann** weitergearbeitet wird. Keine Formulierungen wie „morgen machen wir …“ oder andere selbst gesetzte Zeitpunkte verwenden.
- Keine wiederholten Vertröstungen. TECH PASS, GENERALIZATION PASS, QUALITY PASS und PRODUCT PASS strikt getrennt benennen.
- Ein guter PSNR-Wert ist **kein** visueller Qualitätsnachweis.
- Für HK NPU STUDIO gilt unverändert: finale KI-Inferenz für produktive Kernfunktionen ausschließlich über Snapdragon-NPU / Qualcomm QNN / HTP. CPU nur für Orchestrierung, I/O, Resize, Masken-/Tensorvorbereitung und Compositing.
- Antigravity steht wieder zur Verfügung und soll bei breiten Environment-/Runtime-/Trainingsanalysen bevorzugt eingesetzt werden. Codex nur für eng begrenzte Repo-Codeänderungen.

## Ausgangspunkt des 12. September

Am 11. September waren alle getesteten offenen Restore-Teacherpfade visuell unter dem Produktziel geblieben. FiDeSR Strong blieb die beste Referenz, aber ebenfalls ohne PRODUCT PASS.

Verbindliche Entscheidung vom 11. September:

```text
NO_MORE_OPEN_MODEL_BAKEOFFS=True
NO_MORE_RESTORE_PARAMETER_SWEEPS=True
HK_NPU_PHOTO_RESTORE_STUDENT_SELECTED=True
```

Der neue Pfad sollte ein eigener kleiner, von Anfang an QNN-freundlicher Student sein. Training auf sauberen Ground-Truth-Bildern mit synthetischer Degradation; `3.jpg` als externer Realtest; FiDeSR Strong als visuelle Referenz; nur bei sichtbarem Qualitätsgewinn weitere QNN-Produktportierung.

## Student – Referenzzustand wiederhergestellt

In der frischen Kaggle-Session wurden Quelle und FiDeSR-Referenz erfolgreich aus dem persistenten Backup-Dataset wiedergefunden und nach `/kaggle/working` kopiert.

Quelle:

```text
/kaggle/working/hk_npu_restore_student/reference/3_SOURCE.jpg
169×226 RGB
```

FiDeSR Strong:

```text
/kaggle/working/hk_npu_restore_student/reference/3_FIDESR_STRONG_0.40_0.12.jpg
672×904 RGB
```

Status:

```text
SOURCE_3_RESTORED=YES
FIDESR_REFERENCE_RESTORED=YES
REFERENCE_STATE_READY=YES
```

## Ground-Truth-Datensatz und Degradationspipeline

DIV2K wurde als allgemeiner High-Quality-Ground-Truth-Datensatz vorbereitet.

Bestätigt:

```text
DIV2K_DATASET=PASS
DIV2K_TRAIN_COUNT=760
DIV2K_VAL_COUNT=40
GT_PATCH_SIZE=512
LQ_PATCH_SIZE=128
UPSCALE_FACTOR=4
DEGRADATION_PIPELINE=PASS
FFHQ_USED=NO
```

Training sollte damit 512×512-GT auf synthetisch degradierte 128×128-LQ-Patches abbilden.

## QNN-freundliche Student-Architektur

Architekturdatei:

```text
/root/hk_npu_restore_student/model/hk_npu_restore_student.py
```

Bestätigter Vertrag:

```text
PARAMETERS=1101283
INPUT=[1,3,128,128] float32
OUTPUT=[1,3,512,512] float32
SCALE=4
```

Struktur:

- Conv
- ReLU
- Residual/Add
- 2× DepthToSpace / PixelShuffle
- bicubic base path
- gelernter Residualpfad auf Bicubic
- finaler Clamp auf `[0,1]`
- keine Attention
- keine Dynamic Shapes

Der Student wurde so initialisiert, dass er vor Training exakt `clamp(bicubic(input),0,1)` ausgibt.

### Prüfcodefehler – wichtig dokumentiert

Zwei Fehler lagen in den von ChatGPT gelieferten Prüfblöcken, nicht in der Architektur:

1. Der erste Identity-Gate verglich geclampte Modellausgabe mit **ungeclampter** Bicubic-Ausgabe. Das erzeugte fälschlich `INITIAL_MAX_ABS_DIFF=0.2219...`. Korrigierter Vergleich ergab exakt `0.0`.
2. Beim ersten ONNX-Export war das Modell zuvor auf CUDA verschoben worden, der Exportinput aber auf CPU. Fehler: `Input type torch.FloatTensor and weight type torch.cuda.FloatTensor should be the same`. Mit frischem CPU-Modell war der Export sauber.

Holger war über diese wiederholten vermeidbaren Fehler deutlich verärgert. Künftig technische Blöcke vor Ausgabe sorgfältiger gegen aktuellen Device-/State-Kontext prüfen.

## ONNX – PASS

Finaler ONNX-Export:

```text
/root/hk_npu_restore_student/onnx/hk_npu_restore_student_x4.onnx
SIZE_MB=4.21
```

Bestätigt:

```text
IDENTITY_GATE=PASS
CPU_FORWARD=PASS
ONNX_EXPORT=PASS
ONNX_FULL_CHECK=PASS
ONNX_IO_CONTRACT=PASS
ONNX_OPERATOR_AUDIT=PASS
```

Operatoren:

```text
Add          x12
Clip         x1
Constant     x3
Conv         x27
DepthToSpace x2
Relu         x15
Resize       x1
```

Forbidden Ops:

```text
[]
```

## QAI Hub – Setup und Auth

In der frischen Kaggle-Session fehlte zunächst `qai_hub`. Installiert wurde:

```text
qai_hub 0.55.0
```

Danach fehlte `/root/.qai_hub/client.ini`. Ein weiterer Versuch über Kaggle Secrets schlug zunächst fehl, weil noch kein Secret angelegt war.

Holger legte anschließend in Kaggle erfolgreich an:

```text
QAI_HUB_API_TOKEN
```

Secret-Visibility-Gate:

```text
SECRET_VISIBLE=YES
TOKEN_PRINTED=NO
TOKEN_LENGTH_VALID=True
HARD_STOP=NO
```

Read-only QAI-Hub-Auth-Test:

```text
QAI_HUB_VERSION=0.55.0
MATCHING_DEVICE_COUNT=1
TARGET_DEVICE=Snapdragon X Plus 8-Core CRD
QAI_HUB_AUTH=PASS
TARGET_DEVICE_GATE=PASS
UPLOAD_STARTED=NO
COMPILE_STARTED=NO
```

### Antigravity-Audit zu QAI Hub

Antigravity wurde erfolgreich zur breiten Environment-/API-Prüfung eingesetzt. Es bestätigte für `qai_hub 0.55.0` die relevanten API-Signaturen (`ClientConfig`, `Client`, `upload_model`, `submit_compile_job`, `get_devices`, `get_status`, `get_target_model`, `download`) und empfahl Kaggle Secret als Auth-Basis.

Nicht als bewiesene Produktfakten behandeln:

- angeblich kompletter Fit des Modells in NPU-TCM;
- angeblich erwartete `<15–20 ms` Inferenz.

Diese Werte wurden **nicht** durch reales Profiling bestätigt.

## QNN-Feasibility-Compile – SUCCESS

Der untrainierte Student wurde genau einmal über QAI Hub kompiliert.

Ziel:

```text
Snapdragon X Plus 8-Core CRD
```

Runtime:

```text
qnn_dlc
```

HTP precision:

```text
FLOAT16
```

Ergebnis:

```text
QNN_COMPILE=SUCCESS
QNN_FEASIBILITY=PASS
SOURCE_MODEL_ID=mqe0rdyvn
JOB_ID=jgzl3ld65
TARGET_MODEL_ID=mnze5r0dn
DLC_SIZE_MB=4.27
AUTOMATIC_RETRY=NO
TRAINING_ALLOWED=YES
TOTAL_ELAPSED_MIN=0.82
```

Lokales DLC:

```text
/kaggle/working/hk_npu_restore_student/qnn_feasibility/hk_npu_restore_student_x4_untrained.dlc
```

**Wichtig:** Dieses DLC ist **untrainiert** und dient ausschließlich als Architektur-/QNN-Feasibility-Nachweis. Nicht als Produktmodell verwenden.

Damit technisch bewiesen:

```text
PyTorch -> ONNX -> QAI Hub -> QNN DLC / HTP FP16
```

## Pilottraining 01 – klarer FAIL

Erster Trainingslauf:

```text
TOTAL_STEPS=3000
BATCH_SIZE=2
LOSS=Charbonnier + 0.12 Edge + 0.15 Multiscale
OPTIMIZER=AdamW
LR=2e-4
WEIGHT_DECAY=1e-4
SCHEDULER=CosineAnnealing
AMP=float16
```

Baseline:

```text
UNTRAINED_STUDENT_PSNR=26.0760
BICUBIC_PSNR=26.0760
```

Validation wurde im Verlauf schlechter als Bicubic. Beispiele:

```text
step 250  -> 26.0142  delta -0.0618 dB
step 1000 -> 25.9567  delta -0.1193 dB
step 2000 -> 25.8972  delta -0.1788 dB
step 3000 -> 25.8299  delta -0.2461 dB
```

Am Ende wurde kein `best.pt` erzeugt, weil `best_psnr` mit der Bicubic-Baseline initialisiert war und der Student sie nie übertraf.

Interpretation:

- der Checkpoint-RuntimeError war nur die Folge des echten Qualitätsfails;
- der Student hatte im breiten Rezept **nicht** generalisiert;
- kein QNN-Recompile.

## Antigravity-Training-Audit

Antigravity wurde für die Ursachenanalyse hinzugezogen. Die sinnvolle Kernempfehlung war: zuerst einen isolierten Overfit-Sanity-Test auf wenigen festen Paaren durchführen, bevor erneut breit trainiert wird.

Eine einzelne Antigravity-Aussage wurde ausdrücklich verworfen: eine behauptete FP16-`sqrt(gx²+gy²+1e-12)`-Problematik traf auf den tatsächlich verwendeten `edge_loss()`-Code nicht zu. Der reale Edge-Loss verwendete Sobel-X/Y + `F.l1_loss()` ohne diese Wurzelkonstruktion.

## 4-Paar-Overfit-Sanity – WEAK PASS

Diagnosebedingungen:

```text
4 feste Paare
GT 512×512
LQ nur bicubic 128×128
keine Augmentierung
kein Noise/JPEG/Blur
LOSS=L1_ONLY
OPTIMIZER=Adam
LR=5e-4
WEIGHT_DECAY=0
SCHEDULER=NONE
AMP=NO
FP32
500 Steps
```

Ergebnis:

```text
BEST_STEP=500
FINAL_L1=0.015937
BICUBIC_PSNR=29.9835
STUDENT_PSNR=31.2584
PSNR_GAIN_DB=+1.2749
OVERFIT_DIAGNOSTIC=WEAK_PASS
```

Best-Checkpoint:

```text
/kaggle/working/hk_npu_restore_student/overfit_sanity_4pairs/hk_npu_restore_student_overfit4_best.pt
```

## Erweiterter 4-Paar-Overfit – PASS

Der gleiche Test wurde vom Step-500-Checkpoint auf insgesamt 2000 Schritte verlängert, mit konservativerem LR `2e-4`.

Ergebnis:

```text
BEST_STEP=2000
FINAL_L1=0.010157
BICUBIC_PSNR=29.9835
STUDENT_PSNR=35.3267
PSNR_GAIN_DB=+5.3431
ALL_PAIRS_IMPROVED=True
OVERFIT_CAPACITY_GATE=PASS
```

Checkpoint:

```text
/kaggle/working/hk_npu_restore_student/overfit_sanity_4pairs_extended/hk_npu_restore_student_overfit4_extended_best.pt
```

Damit belastbar gezeigt:

- Architektur ist lernfähig;
- Residualpfad/Gradient/Backprop funktionieren;
- QNN-kompatible Architektur muss wegen dieses Fehlers nicht ersetzt werden;
- der erste Fail lag im Full-Training-Rezept bzw. in dessen Generalisierung, nicht in einem fundamentalen Architekturbruch.

## Repariertes Full Training – TECH/GENERALIZATION PASS

Das Volltraining wurde anschließend bewusst vereinfacht und kontrollierter aufgebaut.

Wesentliche Änderungen gegenüber Pilot 01:

- frischer Student, kein Overfit-Checkpoint als Start;
- `L1_ONLY`;
- `Adam` statt AdamW;
- `weight_decay=0`;
- kein Scheduler;
- kein AMP, FP32;
- effektive Batchgröße 4 durch Gradient Accumulation;
- keine Desaturation/Colorization-Degradation;
- kontrollierte Phase A und Phase B;
- Colorization bleibt separate spätere Funktion.

Training:

```text
TOTAL_OPTIMIZER_STEPS=12000
EFFECTIVE_BATCH_SIZE=4
LOSS=L1_ONLY
OPTIMIZER=ADAM
WEIGHT_DECAY=0
SCHEDULER=NONE
AMP=NO
```

Phase A:

```text
4000 Schritte
LR=2e-4
leichte Restoration-Degradation
```

Phase B:

```text
8000 Schritte
LR=1e-4
Mild/Medium Blur + Noise + JPEG, selten leichter Motion Blur
```

Finaler Validierungsstand über 40 feste Validation-Bilder:

```text
BEST_STEP=10500
BEST_PHASE=B
BICUBIC_PSNR=24.3309
STUDENT_PSNR=25.0214
PSNR_GAIN_DB=+0.6905
FINAL_L1=0.041542
GENERALIZATION_GATE=PASS
```

Best-Checkpoint:

```text
/root/hk_npu_restore_student/training/full_repaired_01/checkpoints/hk_npu_restore_student_repaired_best.pt
```

Weitere Checkpoints:

```text
/root/hk_npu_restore_student/training/full_repaired_01/checkpoints/hk_npu_restore_student_phase_a_best.pt
/root/hk_npu_restore_student/training/full_repaired_01/checkpoints/hk_npu_restore_student_repaired_last.pt
```

Student-Realtest:

```text
/kaggle/working/hk_npu_restore_student/full_repaired_01/images/3_HK_NPU_RESTORE_STUDENT_REPAIRED.png
```

Vergleich:

```text
/kaggle/working/hk_npu_restore_student/full_repaired_01/images/3_SOURCE_FIDESR_STUDENT_REPAIRED_COMPARISON.png
```

Laufzeit:

```text
TOTAL_ELAPSED_MIN=57.11
PEAK_VRAM_GB=8.56
```

## Visueller Quality-Gate gegen FiDeSR Strong – KLARER FAIL

Holger zeigte das Vergleichsbild `SOURCE | FIDESR STRONG | HK NPU RESTORE STUDENT`.

Holgers Bewertung des rechten Student-Bildes war eindeutig: **katastrophal / unbrauchbar**.

Visuelle Probleme des Students:

- Gesicht stark kaputtgeglättet;
- Augen verlieren Form und Kontrast;
- Mund/Zähne verwaschen;
- Bart wird zu dunkler, flächiger Struktur;
- Haare verlieren glaubhafte Detailstruktur;
- Haut wirkt künstlich glatt/maskenhaft;
- Hemd und andere Texturen werden matschig;
- Resultat wirkt eher wie aggressives Denoising/Glätten als echte Restaurierung.

FiDeSR Strong bleibt visuell deutlich überlegen.

Damit aktueller Qualitätsstatus:

```text
TECH_PASS=True
QNN_FEASIBILITY_PASS=True
OVERFIT_CAPACITY_PASS=True
GENERALIZATION_METRIC_PASS=True
QUALITY_PASS_VS_FIDESR=False
PRODUCT_PASS=False
TRAINED_QNN_RECOMPILE=False
```

Der PSNR-Gewinn `+0.6905 dB` ist hier ausdrücklich **kein** Produktqualitätsbeleg. Das reale Bild zeigt, dass die pixelmetrische Verbesserung visuell in die falsche Richtung geht.

## Entscheidung zum aktuellen Student-Zweig

- Den trainierten Student **nicht** in HK NPU STUDIO integrieren.
- Den trainierten Checkpoint **nicht** als Produktmodell zu QNN/HTP kompilieren.
- Das bereits erzeugte QNN-DLC ist untrainiert und bleibt nur Feasibility-Artefakt.
- Kein weiterer langer Lauf mit demselben L1-only-Rezept.
- Kein weiterer Blindversuch nur aufgrund guter Metriken.
- FiDeSR Strong bleibt weiterhin die bessere visuelle Referenz, ist aber selbst weiterhin kein PRODUCT PASS.

Ein möglicher zukünftiger Trainingsansatz könnte zusätzliche Detail-/Perceptual-/Gradient-Komponenten benötigen, aber **keine weitere Ausführung ohne neue ausdrückliche Entscheidung von Holger**.

## Sicherung – noch zu bestätigen

Zum aktuellen Stand wurde ein finaler Backup-Block vorbereitet, der folgende Artefakte sichern soll:

- Student-Architektur;
- ONNX;
- best/phase-A/last trainierte Checkpoints;
- untrainiertes QNN-Feasibility-DLC;
- QAI-Hub IDs;
- Overfit-Diagnosen;
- `3_SOURCE.jpg`;
- FiDeSR Strong;
- Student-Failbild;
- Vergleichsbild;
- Trainings-/QNN-Reports;
- SHA-256-Manifeste;
- Statusdatei mit `QUALITY_GATE=FAIL` und `PRODUCT_PASS=NO`.

Vorgesehener ZIP-Name:

```text
/kaggle/working/HK_NPU_PHOTORESTORE_STATE_20260912.zip
```

**Wichtig:** Im bisher bestätigten Verlauf wurde die erfolgreiche Ausgabe `BACKUP_READY=YES` für diese 12.-September-Sicherung noch nicht gemeldet. Daher nicht behaupten, dass diese Sicherung bereits persistent abgeschlossen ist.

Vor Beenden einer Kaggle-Session sicherstellen, dass der ZIP-Stand entweder heruntergeladen oder als privates/persistentes Kaggle-Dataset gespeichert wurde.

## Prozessbewertung / Qualitätswarnung

Holger hat am 12. September ausdrücklich seine massive Enttäuschung über den bisherigen Verlauf geäußert. Nach eigener Angabe sind **14 Tage ohne brauchbares Endergebnis** vergangen. Wiederholte Vertröstungen und vermeidbare Code-/Prüffehler haben das Vertrauen stark belastet.

Daraus verbindlich für die weitere Zusammenarbeit:

- keine Schönfärberei von Zwischenergebnissen;
- sichtbare schlechte Ergebnisse sofort als FAIL benennen;
- keine Zukunftsversprechen ohne belastbare Grundlage;
- keine selbst gesetzten Zeitpunkte wie „morgen“;
- keine unnötigen Rückfragen;
- Holger entscheidet über Fortsetzung und Prioritäten;
- Qualitätsgates vor technischem Weiterportieren ernst nehmen;
- bei schlechtem Realbild niemals PSNR oder TECH PASS als Erfolg verkaufen.

## Statusflags – 12. September 2026

```text
PRODUKTNAME=HK NPU STUDIO
AI_PHOTO_RESTORE_TARGET=GENERAL_EXTREME_PHOTO_ENHANCEMENT
FINAL_PRODUCT_AI_INFERENCE=NPU_QNN_HTP_ONLY

DIV2K_DATASET=PASS
DIV2K_TRAIN_COUNT=760
DIV2K_VAL_COUNT=40

HK_NPU_RESTORE_STUDENT_ARCHITECTURE_CREATED=True
HK_NPU_RESTORE_STUDENT_PARAMETERS=1101283
HK_NPU_RESTORE_STUDENT_INPUT=1x3x128x128
HK_NPU_RESTORE_STUDENT_OUTPUT=1x3x512x512
HK_NPU_RESTORE_STUDENT_ONNX=PASS
HK_NPU_RESTORE_STUDENT_QNN_FEASIBILITY=PASS
HK_NPU_RESTORE_STUDENT_QNN_TARGET=Snapdragon_X_Plus_8_Core_CRD
HK_NPU_RESTORE_STUDENT_QAI_MODEL_ID=mqe0rdyvn
HK_NPU_RESTORE_STUDENT_QAI_JOB_ID=jgzl3ld65
HK_NPU_RESTORE_STUDENT_QAI_TARGET_MODEL_ID=mnze5r0dn
HK_NPU_RESTORE_STUDENT_UNTRAINED_DLC_SIZE_MB=4.27

HK_NPU_RESTORE_OVERFIT_4PAIR_PASS=True
HK_NPU_RESTORE_OVERFIT_BICUBIC_PSNR=29.9835
HK_NPU_RESTORE_OVERFIT_STUDENT_PSNR=35.3267
HK_NPU_RESTORE_OVERFIT_GAIN_DB=5.3431

HK_NPU_RESTORE_FULL_TRAINING_COMPLETED=True
HK_NPU_RESTORE_FULL_TRAINING_STEPS=12000
HK_NPU_RESTORE_FULL_TRAINING_BEST_STEP=10500
HK_NPU_RESTORE_FULL_TRAINING_BEST_PHASE=B
HK_NPU_RESTORE_FULL_TRAINING_BICUBIC_PSNR=24.3309
HK_NPU_RESTORE_FULL_TRAINING_STUDENT_PSNR=25.0214
HK_NPU_RESTORE_FULL_TRAINING_GAIN_DB=0.6905
HK_NPU_RESTORE_GENERALIZATION_METRIC_PASS=True

HK_NPU_RESTORE_VISUAL_QUALITY_PASS=False
HK_NPU_RESTORE_PRODUCT_PASS=False
HK_NPU_RESTORE_STUDENT_RESULT=SEVERE_OVERSMOOTHING_UNUSABLE
HK_NPU_RESTORE_TRAINED_QNN_RECOMPILE=False
HK_NPU_RESTORE_STUDIO_INTEGRATION=False

FIDESR_STRONG_CURRENT_REFERENCE=True
FIDESR_STRONG_PRODUCT_PASS=False
NO_MORE_OPEN_MODEL_BAKEOFFS=True

ANTIGRAVITY_AVAILABLE=True
CODEX_AVAILABLE=True

BACKUP_20260912_FINAL_STATE_READY=TO_BE_CONFIRMED
BACKUP_20260912_EXPECTED_ZIP=/kaggle/working/HK_NPU_PHOTORESTORE_STATE_20260912.zip

BUILD_12_SEPTEMBER=False
INSTALLER_12_SEPTEMBER=False
GIT_ADD_12_SEPTEMBER=False
COMMIT_12_SEPTEMBER=False
PUSH_12_SEPTEMBER=False
```

## Nächster technischer Einstieg – nur nach Holgers Entscheidung

Keinen automatischen nächsten Sprint annehmen.

Wenn Holger die Photo-Restore-Arbeit fortsetzen möchte, zuerst den gesicherten Stand verifizieren und den aktuellen Student als **QUALITY FAIL** behandeln. Keine QNN-Neukompilierung des trainierten Checkpoints und keine Studio-Integration starten, solange nicht ein neuer Ansatz visuell klar gegen FiDeSR Strong gewinnt.

## Handover-Regel – unverändert verbindlich

Diese Datei bleibt die vollständige zentrale Chronik.

Bei jeder nächsten Aktualisierung:

- ältere Inhalte niemals löschen;
- neuen Stand ausschließlich unten anhängen;
- bei Widersprüchen hat der neueste Abschnitt Vorrang;
- Download-Dateiname immer exakt:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt die Datei anschließend über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die bestehende zentrale Handover-Datei niemals mit einer verkürzten Fassung überschreiben.



# CHATGPT_HANDOVER – Ergänzung 12. September 2026 – FiDeSR Strong Direct Port, QNN/HTP 4/4, Full-NPU-Pipeline und Qualitäts-Tuning

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Qualitätsregeln – erneut bestätigt

- Sprache mit Holger weiterhin Deutsch.
- Vor jedem technischen Sprint sichtbar angeben:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Bei Ausführungsaufträgen vollständige PowerShell-/Python-Blöcke liefern, keine kleinteiligen Zeilenänderungsanweisungen.
- Keine unnötigen Rückfragen; bei klarer Evidenz den nächsten sicheren Schritt selbst bestimmen.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern.
- Für HK NPU STUDIO bleibt verbindlich:
  - eigentliche KI-Inferenz nur über Snapdragon NPU / Qualcomm QNN / HTP,
  - CPU nur für Orchestrierung, I/O, Resize, Masken, Tensorvorbereitung, Compositing und nicht-neuronale Mathematik,
  - kein CPU-/GPU-AI-Fallback als Produktlösung.
- Qualitätsgates strikt trennen:
  - `TECH PASS`
  - `QUALITY PASS`
  - `PRODUCT PASS`
- Ein technisch gültiger NPU-Lauf ist kein automatischer visueller Qualitäts-PASS.
- Keine erneuten Modell-Bakeoffs oder Parameter-Sweeps ohne klare Hypothese.
- Keine QNN-Neukompilierung, solange die vorhandenen Graphen technisch korrekt sind und nur die Bildqualität/Orchestrierung untersucht wird.

## Strategische Modellentscheidung – Student verworfen, FiDeSR Strong direkt portiert

Der zuvor trainierte/kompilierte Student erreichte die visuelle Qualität von FiDeSR Strong nicht ausreichend.

Finale Student-Entscheidung:

```text
QUALITY_PASS_VS_FIDESR_STRONG=NO
PRODUCT_PASS=NO
```

Daraufhin wurde entschieden:

```text
NO_MORE_STUDENT_TRAINING=True
DIRECT_FIDESR_STRONG_PORT=True
```

Referenzmodell:

```text
Ar0Kim/FiDeSR
Commit: 8042f139fc3f6f91ac450c41f69a14c45f16ac4b
```

FiDeSR-Checkpoint:

```text
/root/hk_npu_fidesr_port/FiDeSR/preset/models/fidesr.pkl
SHA256=EBFF7CAD32B40470045D00D8D00250AB51430F81A24C19964E109FAD2AD6556D
```

Stable-Diffusion-Basis:

```text
Manojb/stable-diffusion-2-1-base
```

## Eingefrorener FiDeSR-Strong-Qualitätsvertrag

Der reproduzierte FiDeSR-Strong-Referenzpfad bestand den visuellen Gate gegen die gespeicherte Strong-Referenz.

Eingefrorene Parameter:

```text
process_size=512
upscale=4
align=wavelet

vae_encoder_tiled_size=512
vae_decoder_tiled_size=224

latent_tiled_size=64
latent_tiled_overlap=16

hf_scale=0.40
lf_scale=0.12

lf_rc=0.10
lf_order=2
lf_tau=0.8
lf_sharp=10
lf_dmap_gamma=1.2

hf_rc=0.32
hf_order=2
hf_dmap_gamma=1.2

lf_hf_merge_ratio=0.5
```

Status:

```text
TECH_PASS=YES
FIDESR_STRONG_RUNTIME_RESTORED=YES
QUALITY_PASS_VS_SAVED_FIDESR_STRONG=YES
VISUAL_QUALITY_GATE=PASS
TRAINING_REQUIRED=NO
MODEL_ALTERNATIVE_REQUIRED=NO
```

Wichtig:

- FiDeSR nutzt bei offizieller Inferenz einen leeren Prompt.
- Runtime-CLIP kann deshalb durch ein eingefrorenes Empty-Prompt-Embedding ersetzt werden.
- LF/HF-FFT, Detail-Gates und Wavelet-Fix sind deterministische nicht-neuronale Mathematik und dürfen auf CPU laufen.
- Der offizielle VAE-Tile-Hook nutzt Padding und globale GroupNorm-Behandlung über Tiles; dies ist für spätere Produktqualität relevant.
- Der offizielle `--seed` wird im Inferenzpfad nicht tatsächlich zur RNG-Steuerung angewendet. Das gespeicherte `seed231`-Epsilon ist ein deterministischer Produktkonstantenstand, aber kein Beweis dafür, dass der historische Strong-Lauf bitgenau mit diesem Seed erzeugt wurde.

## Isolierte FiDeSR-Portierungsumgebung

Kaggle-Pfad:

```text
/root/hk_npu_fidesr_port
```

Hermetische Python-3.10-Umgebung:

```text
/root/hk_npu_fidesr_port/venv_fidesr_py310
```

Bestätigte Kernversionen:

```text
Python 3.10.21
torch 2.1.2+cu121
torchvision 0.16.2+cu121
diffusers 0.25.0
transformers 4.28.1
tokenizers 0.13.3
peft 0.9.0
huggingface_hub 0.20.3
accelerate 0.28.0
numpy 1.26.4
onnx 1.16.2
onnxruntime-gpu 1.19.2
qai-hub 0.55.0
```

Globales Kaggle-Environment wurde nicht ersetzt.

## Statischer ONNX-Vertrag

Vier AI-Graphen wurden statisch nach ONNX Opset 17 exportiert:

### VAE Encoder

```text
image   [1,3,512,512] FP16
epsilon [1,4,64,64]   FP16
->
latent  [1,4,64,64]
```

### Merged LoRA UNet

```text
sample                [1,4,64,64]   FP16
timestep              [1]           INT64 im ursprünglichen ONNX-Vertrag
encoder_hidden_states [1,77,1024]   FP16
->
model_pred            [1,4,64,64]
```

### LRRB

```text
latent_cat [1,8,64,64] FP16
->
delta      [1,4,64,64]
```

### VAE Decoder

```text
latent [1,4,64,64] FP16
->
image  [1,3,512,512]
```

Alle vier ONNX-Graphen bestanden:

```text
ONNX_CHECKER=PASS
PYTORCH_VS_ONNX_NUMERIC=PASS
OVERALL_NUMERIC_PASS=True
```

## QAI Hub / QNN-DLC Compile – alle vier Graphen SUCCESS

Zielgerät:

```text
Snapdragon X Plus 8-Core CRD
```

Runtime:

```text
qnn_dlc
```

HTP-Präzision:

```text
FLOAT16
```

Der UNet benötigte zusätzlich `--truncate_64bit_io` wegen des externen INT64-Timestep-Inputs.

### LRRB

```text
Source Model=mm661482m
Job=jgk2726vg
Target Model=mq3x912rq
DLC_BYTES=2942724
SHA256=F031AC1FD72EF9BECF8BF4E06F67C23B096457EFFAA169A4F8F89C2217B76ABF
QNN_COMPILE=PASS
```

### VAE Encoder

```text
Source Model=mnze84wzn
Job=jp3zvzom5
Target Model=mm5lpw99q
DLC_BYTES=136829868
SHA256=088E8F2C07FB7E1106CAB2ADB15E609943FEB752CB894CFE3414EE1B7EC20139
QNN_COMPILE=PASS
```

### VAE Decoder

```text
Source Model=mq8owx1vn
Job=jgzlolz45
Target Model=mqp4wyygq
DLC_BYTES=198175252
SHA256=2F72BAB5E68602CF9BAD81189D63ED45DD5FE94B075DBC2F02CA115339F7CAF7
QNN_COMPILE=PASS
```

### Merged UNet

Erster Compile `jp4ykye2p` scheiterte ausschließlich wegen fehlendem `--truncate_64bit_io`.

Retry:

```text
Source Model=mn0w7999q
Job=jp8e0erqp
Target Model=mqye9wwxn
DLC_BYTES=3465354564
SHA256=2E086AC02267177419C4B31D8849C353E1632A8E045AF14C32A20831737B12DC
QNN_COMPILE=PASS
```

Final:

```text
ALL_4_QNN_GRAPHS_COMPILED=YES
UNET_SPLIT_REQUIRED=NO
RECOMPILE_REQUIRED=NO
```

## Eingefrorene Produktkonstanten

```text
fidesr_empty_prompt_embeds.bin
BYTES=157696
SHA256=26E5E7D387699FDF4BB52EBD914A3BC686801604CC1C11CBCDD7FD6FE28B5604

fidesr_epsilon_seed231.bin
BYTES=32768
SHA256=F24A5790735DCBF9D05B027D2CF1C0D23064A82EB8FB7E24198884A5FB983E1B
```

## Kaggle-ZIP und lokaler Transfer

Transport-ZIP:

```text
/kaggle/working/HK_NPU_FiDeSR_QNN_Final_20260912.zip
```

ZIP-Test:

```text
No errors detected in compressed data
```

Lokales Ziel:

```text
C:\SnapdragonAI\models\photo_restore
```

Alle sechs Produktartefakte wurden lokal per SHA256 bitgenau geprüft:

```text
ALL_HASHES_PASS=True
TRANSFER_INTEGRITY=PASS
```

## Lokale QAIRT-/AIStack-Umgebung

```text
C:\Qualcomm\AIStack\2.47.0.260601
```

Runner:

```text
C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-net-run.exe
```

HTP-Backend:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll
```

DLC-Loader:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnModelDlc.dll
```

Korrekte DLC-Ausführung:

```text
--model QnnModelDlc.dll
--dlc_path <file.dlc>
```

## Echter lokaler NPU-Nachweis – 4/4 PASS

### LRRB

```text
LRRB_DLC_LOAD=PASS
QNN_HTP_EXECUTION=PASS
RAW_OUTPUT_CREATED=YES
OUTPUT_SHAPE=[1,4,64,64]
OUTPUT_FP16_SANITY=PASS
```

### VAE Encoder

```text
QNN_EXIT_CODE=0
QNN_RUNTIME_SEC=18.19
OUTPUT_SHAPE=[1,4,64,64]
OUTPUT_FINITE=True
VAE_ENCODER_LOCAL_NPU=PASS
```

### VAE Decoder

```text
OUTPUT_ELEMENTS=786432
OUTPUT_FINITE=True
OUTPUT_MIN=-1.21484375
OUTPUT_MAX=-0.361328125
OUTPUT_MEAN=-0.78662109375
DECODER_FP32_RECHECK=PASS
VAE_DECODER_LOCAL_NPU=PASS
```

Das zwischenzeitliche `OUTPUT_STD=inf` war ausschließlich ein FP16-Statistikoverflow in NumPy, kein Decoderfehler.

### Merged UNet

```text
OUTPUT_ELEMENTS=16384
OUTPUT_FINITE=True
OUTPUT_MIN=-0.80029296875
OUTPUT_MAX=0.740234375
OUTPUT_MEAN_FP32=-0.039160698652267456
OUTPUT_STD_FP32=0.22280889749526978

UNET_DLC_INTEGRITY=PASS
EMPTY_PROMPT_INTEGRITY=PASS
UNET_DLC_LOAD=PASS
QNN_HTP_EXECUTION=PASS
RAW_OUTPUT_CREATED=YES
OUTPUT_FP16_SANITY=PASS
UNET_MERGED_LOCAL_NPU=PASS
```

Final:

```text
LRRB_LOCAL_NPU=PASS
VAE_ENCODER_LOCAL_NPU=PASS
VAE_DECODER_LOCAL_NPU=PASS
UNET_MERGED_LOCAL_NPU=PASS
LOCAL_NPU_GRAPHS_PASS=4_OF_4
ALL_FIDESR_AI_GRAPHS_LOCAL_QNN_HTP=PASS
```

## Full-NPU-Pipeline – erstes sichtbares Realbild

Testbild:

```text
C:\Users\holge\Desktop\Testbilder\3.jpg
```

Original:

```text
169x226
```

Produkt-Preprocessing:

```text
672x904
```

Neuronale Stufen:

```text
VAE Encoder -> QNN/HTP
UNet        -> QNN/HTP
LRRB        -> QNN/HTP
VAE Decoder -> QNN/HTP
```

CPU ausschließlich für:

```text
Tiling
Tensor-Assembly
FFT / LF-HF
Detail-Gates
Wavelet Color Fix
Datei-I/O
```

Ergebnis:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_STRONG.png
```

Status:

```text
TECH_PASS=YES
NPU_PIPELINE_VISIBLE_RESULT=YES
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

## Qualitätsanalyse

Aktuelle visuelle Schwächen:

- Haut zu glatt / teilweise wachsig.
- feine Hautstruktur und kleine Unebenheiten fehlen.
- Bartstoppeln werden nicht deutlich genug herausgearbeitet.
- Haare/Bart wirken teils härter als die Haut.
- aktueller Produkt-Tiling-Pfad erreicht die eingefrorene FiDeSR-Strong-Qualität noch nicht.

Wichtiger technischer Unterschied:

Der offizielle FiDeSR-VAEHook verwendet Padding, eigene Tile-Crops und globale GroupNorm-Statistik über Tiles. Der aktuelle Produkt-Prototyp verwendet statische 512/64-Tiles mit externem Blending.

## Microdetail-Tuning – kontrollierter Versuch

Getestet:

```text
HF_SCALE            0.40 -> 0.48
HF_RC               0.32 -> 0.27
HF_DMAP_GAMMA       1.20 -> 1.00
LF_SCALE            0.12 -> 0.08
LF_HF_MERGE_RATIO   0.50 -> 0.45
```

Ergebnis:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_MICRODETAIL.png
```

A/B-Auswertung:

- Bildgröße weiterhin 672x904.
- globaler Pixelunterschied extrem klein;
- mittlere absolute Pixelabweichung etwa 0.32/255 pro Kanal;
- Bart- und Hautdetails nur minimal verändert;
- Bartstoppeln nicht deutlich genug stärker sichtbar;
- Haut bleibt zu glatt;
- keine deutliche Verschlechterung, aber auch kein ausreichender Qualitätsgewinn.

Entscheidung:

```text
MICRODETAIL_NPU_RUN=PASS
MICRODETAIL_PARAMETER_CHANGE_VISIBLE=MINIMAL
MICRODETAIL_QUALITY_GAIN=INSUFFICIENT
QUALITY_PASS=NO
PRODUCT_PASS=NO
MICRODETAIL_ADOPTED_AS_NEW_BASELINE=False
BASELINE_REFERENCE_PRESERVED=YES
```

## Aktueller Gesamtstatus Photo Restore / FiDeSR

```text
FIDESR_STRONG_REFERENCE_QUALITY=PASS
FIDESR_DIRECT_PORT_SELECTED=True

ONNX_EXPORT_4_GRAPHS=PASS
ONNX_NUMERIC_VALIDATION=PASS

QNN_COMPILE_LRRB=PASS
QNN_COMPILE_VAE_ENCODER=PASS
QNN_COMPILE_VAE_DECODER=PASS
QNN_COMPILE_UNET=PASS

LOCAL_NPU_LRRB=PASS
LOCAL_NPU_VAE_ENCODER=PASS
LOCAL_NPU_VAE_DECODER=PASS
LOCAL_NPU_UNET=PASS

LOCAL_NPU_GRAPHS_PASS=4_OF_4
ALL_FIDESR_AI_GRAPHS_LOCAL_QNN_HTP=PASS

FULL_NPU_PIPELINE_VISIBLE_RESULT=YES
FULL_NPU_PIPELINE_TECH_PASS=YES

FULL_NPU_PIPELINE_QUALITY_PASS=NO
PHOTO_RESTORE_PRODUCT_PASS=NO

RECOMPILE_REQUIRED=NO
NEW_MODEL_REQUIRED=NO
STUDIO_INTEGRATION_READY=NO
```

## Nächster sicherer technischer Schritt

Nicht weiter blind an HF/LF-Parametern drehen.

Zuerst die Qualitätsabweichung strukturell lokalisieren:

1. vorhandene Zwischenoutputs sichern;
2. VAE-Tiling gegen den offiziellen `VAEHook`-Vertrag prüfen;
3. insbesondere Padding/Crop und globale GroupNorm-Behandlung untersuchen;
4. UNet/LRRB-Tiling separat von VAE-Tiling isolieren;
5. LF/HF und Wavelet erst danach als Fehlerquelle bewerten;
6. keine neue QNN-Kompilierung, solange die statischen Graphen technisch korrekt laufen;
7. erst nach sichtbarem `QUALITY_PASS` Codex für eine eng begrenzte Studio-Integration einsetzen.

## Lokale Artefakte

Finale FiDeSR-QNN-Artefakte:

```text
C:\SnapdragonAI\models\photo_restore
```

Full-Pipeline-Arbeitsstand:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test
```

Wichtige Ergebnisbilder:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_STRONG.png
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_MICRODETAIL.png
```

Lokale Sicherung:

```text
C:\Users\holge\Downloads\HK_NPU_PHOTORESTORE_STATE_20260912.zip
```

## Git-/Build-Status dieses FiDeSR-Sprints

Für diese FiDeSR-QNN-/Full-NPU-Arbeit wurde kein bestätigter neuer Produktcommit, Build, Installer, Tag oder Push durchgeführt.

Vor jedem späteren Repo-Eingriff zuerst aktuellen Git-Status prüfen.

## Lizenzhinweis

- FiDeSR-Repository: Apache 2.0.
- SD2.1-Basis und verwendete Modellgewichte besitzen eigene Lizenzbedingungen.
- Vor kommerzieller Auslieferung die konkreten Rechte der Modellartefakte separat verbindlich prüfen.
- Technischer QNN/NPU-PASS bedeutet nicht automatisch Redistributability.

## Statusflags – Tagesabschluss 12. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

PHOTO_RESTORE_MODEL=FiDeSR_Strong_Direct_Port
PHOTO_RESTORE_STUDENT_REJECTED=True

FIDESR_REFERENCE_QUALITY_PASS=True
FIDESR_STRONG_REPRODUCED=True

FIDESR_ONNX_4_GRAPHS=PASS
FIDESR_QNN_4_GRAPHS=PASS
FIDESR_LOCAL_QNN_HTP_4_OF_4=PASS

FIDESR_FULL_NPU_PIPELINE_VISIBLE=True
FIDESR_FULL_NPU_PIPELINE_TECH_PASS=True
FIDESR_FULL_NPU_PIPELINE_QUALITY_PASS=False
FIDESR_PRODUCT_PASS=False

MICRODETAIL_TEST_COMPLETED=True
MICRODETAIL_QUALITY_GAIN=INSUFFICIENT
MICRODETAIL_ADOPTED_AS_NEW_BASELINE=False

RECOMPILE_REQUIRED=False
UNET_SPLIT_REQUIRED=False
NEW_MODEL_REQUIRED=False
STUDIO_INTEGRATION_DONE=False

NEXT_SESSION=FIDESR_PRODUCT_TILING_QUALITY_DIAGNOSIS
NEXT_FOCUS=VAE_TILING_PADDING_CROP_GROUPNORM
```

## Handover-Übernahme

Diese vollständige Datei unter exakt folgendem Namen verwenden:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie anschließend über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die ältere Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.


# CHATGPT_HANDOVER – Ergänzung 12. September 2026 – Photo Restore Qualitätsdiagnose, VAE-Roundtrip und Zielarchitektur

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsregeln – weiterhin verbindlich

- Sprache mit Holger: Deutsch.
- Vor jedem technischen Sprint sichtbar angeben:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Keine unnötigen Rückfragen; bei klarer technischer Evidenz den nächsten sicheren Schritt selbst bestimmen.
- PowerShell-Befehle vollständig und mit absoluten Windows-Pfaden liefern.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne abgestimmten Schritt.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern.
- Für HK NPU STUDIO bleibt verbindlich:
  - eigentliche KI-Inferenz nur über Snapdragon NPU / Qualcomm QNN / HTP;
  - CPU nur für Orchestrierung, I/O, Resize, Masken, Tensorvorbereitung, Compositing und nicht-neuronale Mathematik;
  - kein CPU-/GPU-AI-Fallback als Produktlösung.
- Qualitätsgates strikt trennen:
  - `TECH PASS`
  - `QUALITY PASS`
  - `PRODUCT PASS`

## Ausgangsstand Photo Restore / FiDeSR

Der direkte FiDeSR-Strong-Port ist technisch weit fortgeschritten.

Bestätigt:

```text
FIDESR_REFERENCE_QUALITY_PASS=True
FIDESR_STRONG_REPRODUCED=True

FIDESR_ONNX_4_GRAPHS=PASS
FIDESR_QNN_4_GRAPHS=PASS
FIDESR_LOCAL_QNN_HTP_4_OF_4=PASS

FIDESR_FULL_NPU_PIPELINE_VISIBLE=True
FIDESR_FULL_NPU_PIPELINE_TECH_PASS=True
```

Alle vier neuronalen FiDeSR-Komponenten wurden lokal auf dem Snapdragon über QNN/HTP erfolgreich ausgeführt:

```text
LRRB_LOCAL_NPU=PASS
VAE_ENCODER_LOCAL_NPU=PASS
VAE_DECODER_LOCAL_NPU=PASS
UNET_MERGED_LOCAL_NPU=PASS

LOCAL_NPU_GRAPHS_PASS=4_OF_4
ALL_FIDESR_AI_GRAPHS_LOCAL_QNN_HTP=PASS
```

Produktartefakte liegen unter:

```text
C:\SnapdragonAI\models\photo_restore
```

## Baseline-Full-NPU-Ergebnis – Bild 3

Testbild:

```text
C:\Users\holge\Desktop\Testbilder\3.jpg
```

Full-NPU-Ergebnis:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_STRONG.png
```

Bildgröße:

```text
672x904
```

Bewertung:

- Gesicht geometrisch grundsätzlich stabil;
- Person/Identität/Grundstruktur bleiben erhalten;
- Haut wirkt zu glatt / teilweise wachsig;
- feine Hautunebenheiten und Poren fehlen;
- Bartstoppeln sind zu wenig differenziert;
- Haare/Bart wirken teils härter als die Haut;
- aktueller Produkt-Tiling-Pfad erreicht die eingefrorene FiDeSR-Strong-Qualität noch nicht.

Status:

```text
TECH_PASS=YES
NPU_PIPELINE_VISIBLE_RESULT=YES
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

Wichtig: Bild 3 zeigt **keine relevante Gesichtsverzerrung**. Das Gesicht ist groß genug im Bild und wird geometrisch gut erhalten. Das Qualitätsproblem bei Bild 3 ist hauptsächlich:

```text
zu glatte Haut
zu wenig Mikrodetail
zu wenig sichtbare Bartstoppeln
```

## Microdetail-Tuning – HF/LF-Parameterexperiment

Kontrollierter Versuch:

```text
HF_SCALE            0.40 -> 0.48
HF_RC               0.32 -> 0.27
HF_DMAP_GAMMA       1.20 -> 1.00
LF_SCALE            0.12 -> 0.08
LF_HF_MERGE_RATIO   0.50 -> 0.45
```

Ergebnis:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_MICRODETAIL.png
```

Bewertung:

- technisch sauber;
- sichtbarer Unterschied nur minimal;
- Bartstoppeln nicht deutlich genug stärker erkennbar;
- Haut bleibt zu glatt;
- kein ausreichender Qualitätsgewinn.

Entscheidung:

```text
MICRODETAIL_NPU_RUN=PASS
MICRODETAIL_PARAMETER_CHANGE_VISIBLE=MINIMAL
MICRODETAIL_QUALITY_GAIN=INSUFFICIENT
MICRODETAIL_ADOPTED_AS_NEW_BASELINE=False
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

## Real-Source-Microdetail-Reinjection

Zusätzlicher nicht-neuronaler Versuch:

- vorhandene Hochfrequenz aus dem Originalbild zurückführen;
- nur Luminanzdetails;
- keine künstliche Körnung;
- keine neue AI-Inferenz;
- QNN-Modelle unverändert.

Ergebnis:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_REAL_MICRODETAIL.png
```

Technischer Status:

```text
REAL_SOURCE_MICRODETAIL=PASS
AI_INFERENCE_ADDED=NO
QNN_RECOMPILE=NO
HARD_STOP=NO
```

Visuelle Bewertung:

- praktisch kein sichtbarer Unterschied zum Baseline-Ergebnis;
- Bartstoppeln weiterhin nicht klarer;
- Hautunebenheiten weiterhin nicht ausreichend sichtbar.

Entscheidung:

```text
REAL_SOURCE_MICRODETAIL_VISIBLE_GAIN=NO
REAL_SOURCE_MICRODETAIL_ADOPTED=False
```

Schlussfolgerung:

Die fehlenden Mikrodetails gehen **bereits vor dem finalen Postprocessing** verloren. Weitere einfache HF-/Schärfe-/Reinjection-Maßnahmen sind nicht der richtige Primärhebel.

## Zweites Diagnosebild – kleines Gesicht

Testbild:

```text
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
```

Ziel:

Untersuchen, ob bei kleinen Gesichtern bereits der VAE-Roundtrip Geometrie und Details verändert.

### VAE-only-Diagnoselauf

Pipeline:

```text
Bild
-> VAE Encoder QNN/HTP
-> VAE Decoder QNN/HTP
-> PNG
```

Explizit **nicht** verwendet:

```text
UNet
LRRB
LF/HF
Wavelet
CPU-AI-Fallback
```

Erzeugte Dateien:

```text
C:\SnapdragonAI\temp\fidesr_vae_roundtrip_142461\142461_SOURCE_512.png
C:\SnapdragonAI\temp\fidesr_vae_roundtrip_142461\142461_VAE_NPU_ROUNDTRIP.png
```

Technischer Status:

```text
VAE_ENCODER_QNN_HTP=PASS
VAE_DECODER_QNN_HTP=PASS
UNET_USED=NO
LRRB_USED=NO
LF_HF_USED=NO
WAVELET_USED=NO
CPU_AI_FALLBACK=NO
VAE_ONLY_DIAGNOSTIC=PASS
```

## Visuelle Diagnose kleines Gesicht

Beim Vergleich von Source-512 und VAE-Roundtrip wurde festgestellt:

- feine Bilddetails werden bereits im VAE-Roundtrip geglättet;
- Körperhaar/feine Textur geht sichtbar zurück;
- kleine Gesichtsdetails werden weicher;
- das kleine Gesicht verändert sich sichtbar in Ausdruck/Geometrie.

Besonders auffällig:

- Mund/Lächeln verändert;
- Nase weicher bzw. leicht umgeformt;
- Augenbereich weniger exakt;
- Wange/Kiefer geglättet;
- Gesamtausdruck nicht exakt identisch.

Wichtig: Dies gilt **nicht pauschal für alle Gesichter**.

Korrekte Einordnung:

```text
Bild 3:
großes Gesicht
-> Geometrie weitgehend stabil
-> Hauptproblem = zu glatte Haut / fehlende Mikrodetails

142461:
kleines Gesicht
-> VAE-Roundtrip verändert Gesicht sichtbar
-> zusätzlich Identitäts-/Geometrieverlust
```

Die frühere pauschale Aussage „VAE ist generell der Hauptfehler“ wurde damit korrigiert. Der VAE ist insbesondere für **kleine Gesichter / kleine feine Strukturen** ein kritischer Flaschenhals.

## Zero-Epsilon-Diagnose

Hypothese:

Ein Teil der Gesichtsveränderung könnte durch das feste Epsilon-Sampling des VAE-Encoders entstehen.

Test:

```text
epsilon = 0
```

Erzeugtes Ergebnis:

```text
C:\SnapdragonAI\temp\fidesr_vae_roundtrip_142461\142461_VAE_NPU_ROUNDTRIP_EPSILON_ZERO.png
```

Technischer Status:

```text
VAE_ENCODER_QNN_HTP=PASS
VAE_DECODER_QNN_HTP=PASS
EPSILON_MODE=ZERO
UNET_USED=NO
LRRB_USED=NO
LF_HF_USED=NO
CPU_AI_FALLBACK=NO
HARD_STOP=NO
```

Visuelle Bewertung:

- leicht stabiler als die Seed-231-Variante;
- etwas weniger zufällige Veränderung;
- Grundproblem bleibt:
  - kleines Gesicht weiterhin zu weich;
  - Identität/Geometrie nicht stabil genug;
  - Details fehlen weiterhin.

Entscheidung:

```text
ZERO_EPSILON_IMPROVEMENT=SLIGHT
ZERO_EPSILON_SOLVES_SMALL_FACE_DISTORTION=NO
```

Schlussfolgerung:

Das Sampling trägt etwas bei, aber der VAE-Roundtrip selbst bleibt für kleine Gesichter ein wesentlicher Qualitätslimiter.

## Produktziel HK NPU STUDIO – Photo Restore

Holgers Ziel wurde ausdrücklich bestätigt:

HK NPU STUDIO soll später:

- Bilder insgesamt scharf und detailreich restaurieren;
- vorhandene Bartstoppeln sichtbar erhalten bzw. besser rekonstruieren;
- kleine Hautunebenheiten/Poren natürlicher darstellen;
- keine Plastikhaut erzeugen;
- Haare nicht künstlich überschärfen;
- keine künstlichen Poren/Stoppeln halluzinieren;
- große Gesichter geometrisch stabil erhalten;
- **kleine Gesichter unverzerrt** und identitätsnah wiedergeben;
- KI-Inferenz weiterhin ausschließlich über QNN/HTP/NPU ausführen.

## Verbindliche Zielarchitektur

Der reine Full-Frame-FiDeSR-Pfad reicht alleine nicht für alle Motive.

Zielarchitektur:

```text
FULL_IMAGE_FIDESR_NPU
        |
        +--> FACE_PRESERVING_ROI_PASS
        |
        +--> DETAIL_PRESERVE
        |
        +--> CLEAN_COMPOSITE
        |
        +--> FINAL_IMAGE
```

Oder als Produktlogik:

```text
FULL_IMAGE_FIDESR_NPU
+ FACE_PRESERVING_ROI_PASS
+ CONSERVATIVE_MICRODETAIL_RECOVERY
+ CLEAN_RECOMPOSITING
```

### Full-Image-Pfad

- bestehende FiDeSR-QNN-Graphen weiterverwenden;
- gesamtes Bild restaurieren;
- NPU-only für neuronale Inferenz.

### Face-Preserving-ROI-Pfad

Ziel:

Kleine Gesichter lokal mit höherer wirksamer Auflösung bearbeiten, damit sie nicht im 512->64-VAE-Flaschenhals zu stark komprimiert werden.

Prinzip:

```text
Gesamtbild
-> Gesichts-/ROI-Bereich bestimmen
-> ROI hochskalieren / auf 512x512 vorbereiten
-> FiDeSR NPU auf ROI
-> geometrisch sauber zurücksetzen
-> sauber ins Gesamtbild recompositen
```

CPU darf hier ausschließlich übernehmen:

```text
Crop
Resize
Mask
Geometrie
Compositing
```

Die eigentliche AI-Inferenz bleibt auf QNN/HTP/NPU.

### Microdetail-Preserve-Pfad

Ziel:

Bei großen Gesichtern zusätzlich:

- reale Bartstoppeln besser sichtbar;
- kleine Hautunebenheiten/Poren besser erhalten;
- feine Haar-/Textilstruktur erhalten;
- keine künstliche Körnung;
- keine Halluzination.

Nicht als aggressives Sharpening lösen.

## Geplante Qualitätssprints

### Sprint 1 – Face-Preserve-Grundpfad

Ziel:

```text
kleine Gesichter nicht mehr verzerren
```

Testbild:

```text
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
```

Qualitäts-Gates:

```text
Mund/Nase/Augen unverzerrt
Proportionen stabil
Identität stabil
keine sichtbare ROI-Einsatzkante
Hintergrund außerhalb ROI unverändert
```

### Sprint 2 – echte Mikrodetails

Ziel:

```text
Bartstoppeln
Poren
kleine Hautunebenheiten
Haarstruktur
Stoffstruktur
```

Qualitäts-Gates:

```text
keine Plastikhaut
keine Halos
keine künstliche Körnung
keine erfundenen Details
keine künstlich gezeichneten Bart-/Haarstrukturen
```

### Danach erst Produktintegration

Erst wenn folgende Gates erfüllt sind:

```text
TECH_PASS=YES
FACE_PRESERVATION_PASS=YES
MICRODETAIL_PASS=YES
QUALITY_PASS=YES
```

dann:

- eng begrenzte Codex-Integration in HK NPU STUDIO;
- reale App-Tests mit mehreren Bildern;
- danach erst `PRODUCT_PASS`.

## Testbilder für spätere Produktabnahme

Mindestens:

```text
C:\Users\holge\Desktop\Testbilder\3.jpg
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
C:\Users\holge\Desktop\Testbilder\37.jpg
```

Interpretation:

```text
3.jpg
-> großes Gesicht
-> Detail-/Haut-/Bart-Gate

142461...
-> kleines Gesicht
-> Identity-/Geometrie-/ROI-Gate

37.jpg
-> weiterer Realbild-Regressionstest
```

## Erwartbare Produktfähigkeit

Realistische Zielaussage:

- große Gesichter können qualitativ deutlich verbessert werden;
- kleine Gesichter brauchen einen Face-Preserving-ROI-Pfad;
- ein brauchbarer, produktiver HK-NPU-STUDIO-Pfad ist mit den vorhandenen QNN-Artefakten grundsätzlich realistisch;
- die fehlende Arbeit ist jetzt primär Produktlogik, ROI-Verarbeitung und Qualitätsabsicherung;
- nicht mehr die grundsätzliche FiDeSR-Portierung.

Nicht versprechen:

- jedes Bild wird perfekt;
- jedes extrem kleine Gesicht wird wie ein Studio-Porträt rekonstruiert;
- aus nicht vorhandenen Details dürfen künstliche Details erzeugt werden.

## Aktueller Status

```text
PRODUKTNAME=HK NPU STUDIO

PHOTO_RESTORE_MODEL=FiDeSR_Strong_Direct_Port

FIDESR_ONNX_4_GRAPHS=PASS
FIDESR_QNN_4_GRAPHS=PASS
FIDESR_LOCAL_QNN_HTP_4_OF_4=PASS

FULL_NPU_PIPELINE_TECH_PASS=True
FULL_NPU_PIPELINE_VISIBLE=True

LARGE_FACE_GEOMETRY_STABLE_ON_IMAGE_3=True
LARGE_FACE_MICRODETAIL_QUALITY_PASS=False

SMALL_FACE_VAE_DISTORTION_CONFIRMED=True
ZERO_EPSILON_IMPROVEMENT=SLIGHT
ZERO_EPSILON_FIX_SUFFICIENT=False

MICRODETAIL_HF_LF_TUNING_GAIN=INSUFFICIENT
REAL_SOURCE_MICRODETAIL_GAIN=INSUFFICIENT

FACE_PRESERVING_ROI_REQUIRED=True
MICRODETAIL_PRESERVE_REQUIRED=True

QUALITY_PASS=False
PRODUCT_PASS=False

RECOMPILE_REQUIRED=False
NEW_MODEL_REQUIRED=False
STUDIO_INTEGRATION_READY=False
```

## Nächster sicherer Einstieg

Nicht weiter blind an HF/LF-Reglern drehen.

Nächster Sprint:

```text
FACE_PRESERVING_ROI_PROTOTYPE
```

mit:

```text
C:\Users\holge\Desktop\Testbilder\142461_s16323864_5162d47f5655.jpg
```

Zuerst isoliert außerhalb der Studio-UI testen.

Ziel:

```text
kleines Gesicht lokal größer verarbeiten
FiDeSR-NPU wiederverwenden
Gesicht unverzerrt zurücksetzen
keine sichtbaren Kanten
außerhalb ROI keine unerwartete Veränderung
```

Noch nicht:

```text
kein Recompile
kein neues Modell
keine Studio-Integration
kein Build
kein Installer
kein Commit
kein Push
```

## Verbindliche Handover-Regel

Diese Datei ist die vollständige zentrale Chronik.

Bei jeder weiteren Aktualisierung:

- ältere Inhalte nicht löschen;
- neuen Stand als weitere Ergänzung anhängen;
- bei widersprüchlichen alten Statuswerten hat der neueste Abschnitt Vorrang;
- Download-Dateiname immer exakt:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie anschließend über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Keine separate Ergänzungsdatei ausgeben.


# Ergänzung: Tagesabschluss 13. September 2026 – MicroDetail Stage B

Diese Ergänzung hat für den MicroDetail-Stand vom 13.09.2026 Vorrang vor älteren MicroDetail-/FiDeSR-Notizen.

## Verbindliche Arbeitsregeln

- Sprache Deutsch; kurz, direkt, technisch, Schritt für Schritt.
- Vor jedem technischen Sprint sichtbar: SPRINT-ZEIT, WORST CASE, SPEICHER, HARD STOP.
- Bei Ausführung immer kompletter Sprint; nicht auf ein zusätzliches „weiter“ warten.
- Nach jeder Ergebnisbewertung automatisch den unmittelbar nächsten vollständigen Sprint inklusive Code liefern.
- Finales Produktziel: KI-Inferenz nur über Snapdragon NPU/QNN/HTP.
- CPU nur für Orchestrierung, I/O, Resize, Masken, Compositing und nicht-AI-Mathematik.
- Kein ONNX/QNN-Compile, bevor die visuelle Qualität eines neuen MicroDetail-Modells bewiesen ist.
- TECH PASS != QUALITY PASS != PRODUCT PASS.
- Kein Git/Build/Commit/Push ohne ausdrückliche Freigabe.
- Keine image_gen-Nutzung für technische Bildvergleiche.

## Body-Hair-Qualitätsreferenzen

1. `C:\Users\holge\Desktop\Testbilder\ChatGPT Image 2. Sept. 2026, 19_58_19.png`
2. `C:\Users\holge\Desktop\Testbilder\ref22.jpg`

Qualitätsziel:
- natürliche, einzeln erkennbare Haare
- unterschiedliche Richtung, Länge und Dichte
- sichtbare Haut zwischen den Haaren
- keine parallelen Linien, Loops, Hatching oder Plastikhaut

## Dataset / Curation

Source:
`C:\Users\holge\Desktop\Testbilder\male hair`

Kanonischer Source-Count: 161

Final akzeptierte GT-Patches: 33
- HEAD_HAIR: 29, 56, 97, 171, 185, 223, 301, 391, 407
- BEARD: 26, 40, 195, 266, 408
- BODY_HAIR_SKIN: 1, 2, 55, 63, 75, 103, 116, 142, 159, 183, 205, 209, 257, 333, 352, 355, 382, 421, 457

GT-Gate:
`C:\SnapdragonAI\temp\microdetail_final_gt_gate`

Pairset P0:
`C:\SnapdragonAI\temp\microdetail_pairset_p0`

Profiles:
- P1_MILD = VALIDATION_ONLY
- P2_MEDIUM = TRAIN_PRIMARY
- P3_STRONG = TRAIN_HARD
- P4_STAGEA_PROXY = VALIDATION_ONLY

Active Training: 66 Pairs
Validation: 66 Pairs

Kaggle-safe Package:
`C:\SnapdragonAI\temp\HK_NPU_MICRODETAIL_TRAINING_P0_KAGGLE.zip`

Verifizierter Kaggle-Root:
`/kaggle/input/datasets/hknpustudio/hk-npu-microdetail-training-p0-kaggle`

## P0 Resultat

MicroDetailNetP0, 1,048,948 Parameter, 1200 Steps.

- FINAL_TRAIN_INPUT_PSNR=34.805
- FINAL_TRAIN_OUTPUT_PSNR=34.859
- FINAL_TRAIN_GAIN_DB=+0.054
- FINAL_VALIDATION_INPUT_PSNR=37.882
- FINAL_VALIDATION_OUTPUT_PSNR=37.899
- FINAL_VALIDATION_GAIN_DB=+0.017
- FINAL_ALPHA_MEAN=0.127753
- FINAL_DELTA_ABS_MEAN=0.002095
- OVERFIT_SIGNAL_PASS=NO
- PRODUCT_PASS=NO

Interpretation: praktisch Identität, kein Lernnachweis.

## P0.1 Hard Overfit Diagnostic

8 P2_MEDIUM-Paare, keine Augmentation, 800 Steps.

- INITIAL_ALPHA=0.5
- direkte Residual-Supervision
- keine Residual-Regularisierung
- FINAL_INPUT_PSNR=36.208
- FINAL_OUTPUT_PSNR=36.221
- FINAL_GAIN_DB=+0.013
- FINAL_ALPHA_MEAN=0.256612
- FINAL_DELTA_ABS_MEAN=0.000172
- HARD_OVERFIT_PASS=NO
- PRODUCT_PASS=NO

Ergebnis: ebenfalls praktisch kein Delta.

## P0.2 One-Patch Delta-only

Candidate 63, P2_MEDIUM, 500 Steps, kein Alpha/Gating.

- PARAMETERS=108003
- INPUT_PSNR=33.942
- FINAL_OUTPUT_PSNR=34.725
- FINAL_GAIN_DB=+0.783
- GT_DELTA_ABS_MEAN=0.01287509
- FINAL_DELTA_ABS_MEAN=0.00364460
- FINAL_DELTA_ABS_MAX=0.07132687
- OUTPUT_HEAD_WEIGHT_CHANGE=1.98038448e-01
- MAX_STEM_GRAD_NORM=1.80045824e-02
- MAX_BOTTLENECK_GRAD_NORM=2.20447273e-02
- MAX_OUTPUT_HEAD_GRAD_NORM=3.73876970e-01
- ONE_PATCH_OVERFIT_PASS=NO
- DIAGNOSIS=WEAK_OR_INSUFFICIENT_MEMORIZATION

Wichtig: Gradientenpfad funktioniert; Gewichte ändern sich real.

## P0.3 Root Cause

TEST A: Free Delta Oracle
- INPUT_PSNR=33.942
- ORACLE_FINAL_PSNR=122.451
- ORACLE_GAIN_DB=+88.509
- ORACLE_DELTA_ERROR=0.0000006276
- ORACLE_PASS=YES

TEST B: Plain CNN
- CNN_PARAMETERS=1001763
- CNN_STEPS=1000
- CNN_FINAL_PSNR=33.943
- CNN_GAIN_DB=+0.000
- CNN_DELTA_ABS_MEAN=0.00006049
- CNN_DELTA_ABS_MAX=0.00936820
- CNN_DELTA_ERROR=0.01288293
- MAX_BODY_GRAD=2.61797453e-03
- MAX_HEAD_GRAD=2.31015285e-02
- CNN_ONE_PATCH_PASS=NO
- DIAGNOSIS=CONVOLUTIONAL_MAPPING_OR_OPTIMIZATION_STILL_INSUFFICIENT

Schlussfolgerung: Daten-/Pairing-/Loss-Pipeline ist gesund; einfache CNN-Memorization reicht für dieses Mapping nicht.

## P1 Residual U-Net

Robust Discovery Fix bestätigte:
- GT_TARGETS=33
- P2_MEDIUM=33
- P3_STRONG=33
- TRAINING_PAIRS=66

MicroDetailUNetP1:
- PARAMETERS=4,111,635
- TRAINING_EPOCHS=80
- TRAINING_STEPS=1360
- TRAINING_TIME=16.21 min
- BASELINE_MEAN_PSNR=34.805
- FINAL_MEAN_PSNR=36.846
- FINAL_GAIN_DB=+2.041
- P2_MEAN_PSNR=38.535
- P3_MEAN_PSNR=35.157

Kaggle model:
`/kaggle/working/hk_npu_microdetail_p1_unet_fix/microdetail_p1_unet.pt`

## P1.1 Unseen Validation

P1_MILD:
- INPUT_PSNR=41.165
- OUTPUT_PSNR=36.041
- GAIN=-5.124 dB
- 0/33 verbessert
- BODY_HAIR_GAIN=-5.032 dB

P4_STAGEA_PROXY:
- INPUT_PSNR=34.599
- OUTPUT_PSNR=35.635
- GAIN=+1.036 dB
- 33/33 verbessert
- BODY_HAIR_GAIN=+1.078 dB, 19/19 verbessert

Interpretation: P1 ist nicht universell einsetzbar; P4-Proxy war positiv, musste aber mit echten FiDeSR-Ausgaben geprüft werden.

## Echter FiDeSR-Stage-A-Test

Lokales Gate:
`C:\SnapdragonAI\temp\microdetail_real_stagea_gate`

Echte FiDeSR-Strong-Ausgaben:
- REF01 Original: 2172×724
- REF01 Stage A: 8688×2896 = exakt 4×
- REF22 Original: 1484×1060
- REF22 Stage A: 5936×4240 = exakt 4×

ZIP:
`C:\SnapdragonAI\temp\HK_NPU_MICRODETAIL_REAL_STAGEA_GATE.zip`

Finale ZIP-Größe am 13.09.2026:
67,965,579 Byte

Kaggle Dataset nach Neuupload:
`/kaggle/input/datasets/hknpustudio/hk-npu-microdetail-real-stagea-gate2`

## P1.2 V3 – echter 4× FiDeSR-Test

Auto-Discovery PASS, Modell gefunden, CUDA PASS.

REF01:
- Stage A Downsample PSNR=27.870
- P1 Downsample PSNR=27.593
- Gain=-0.278 dB
- DELTA_MEAN=0.00503513
- DELTA_MAX=0.41507658

REF22:
- Stage A Downsample PSNR=26.060
- P1 Downsample PSNR=25.582
- Gain=-0.478 dB
- DELTA_MEAN=0.00672114
- DELTA_MAX=0.46231148

TECH_PASS=YES
QUALITY_PASS=VISUAL_GATE_REQUIRED
PRODUCT_PASS=NO

## P1.3 Full Coverage Visual Gate

24 native 4× regions (12 je Referenz) wurden verglichen:
- FiDeSR Strong
- FiDeSR + P1
- ABS DIFF

Visuelle Entscheidung vom 13.09.2026:
- P1 liefert auf echten FiDeSR-Ausgaben keine belastbare Verbesserung der Körperhaarqualität.
- Änderungen betreffen primär Kanten/Oberflächen/Kontrast.
- Keine überzeugende Verbesserung bei einzeln erkennbaren Haaren, Richtung, Länge oder Dichte.
- Zusammen mit den negativen echten Stage-A-PSNR-Gains ist P1 kein QUALITY PASS.

Finale Entscheidung:
- TECH PASS=YES
- QUALITY PASS=NO
- PRODUCT PASS=NO
- P1=STOP
- KEIN ONNX/QNN-COMPILE für P1

## Nächster Ansatz: P2 mit echten FiDeSR-Artefakten

Kein weiteres Proxy-Training.

Ziel:
Aus den 33 kuratierten GT-Patches echte FiDeSR-Strong-NPU-Ausgaben erzeugen und genau diese als Trainingsinput verwenden. Die kuratierten Originalpatches bleiben Targets.

Geplanter lokaler Pairset-Ordner:
`C:\SnapdragonAI\temp\microdetail_real_fidesr_pairset_p2`

Nächster sicherer Sprint:
1. Vorhandenen echten Full-NPU-FiDeSR-Batch-/Smoke-Pfad im Repo identifizieren.
2. Die 33 GT-Patches unverändert durch FiDeSR Strong NPU/QNN laufen lassen.
3. 33 echte Stage-A-Inputs + 33 GT-Targets bilden.
4. Contact Sheets / visuelles Pairing-Gate prüfen.
5. Erst danach neues P2-Modell trainieren.
6. Kein ONNX/QNN-Compile, bevor P2 auf echten FiDeSR-Ausgaben einen visuellen QUALITY PASS zeigt.

## Tagesabschluss 13.09.2026

- Kein Git/Build/Commit/Push im MicroDetail-Sprint.
- Kein ONNX-Export.
- Kein QNN-Compile des MicroDetail-Modells.
- P1 wurde nach echtem FiDeSR-Full-Coverage-Gate verworfen.
- Wichtigster nächster Schritt: reales FiDeSR-Trainingspairset P2 erzeugen; keine Proxy-Daten mehr.
- Kaggle-`/working` ist nicht als dauerhafte Speicherung zu behandeln; wichtige Artefakte lokal sichern.


# Ergänzung: 13.09.2026 Abend – Studio-Bildverbesserung vs. FiDeSR Strong

## Kritischer Befund

Die aktuell in HK NPU STUDIO sichtbare Funktion „AI Photo Restore / Bildverbesserung“ nutzt NICHT den am 12.09.2026 validierten FiDeSR-Strong-NPU-Pfad.

Aktueller Studio-Pfad:
- `widgets\phoenix\views\photo_restore_view.py`
- `controllers\photo_restore_controller.py`
- `engine\backends\photo_restore_backend.py`

Studio-Backend:
1. NAFNet-DeBlur auf QNN/HTP
2. optional DDColor auf QNN/HTP bei Graustufenbildern
3. RealESRGAN 2x/4x auf QNN/HTP

Die aktuelle schlechte Studio-Ausgabe ist daher nicht identisch mit dem FiDeSR-Strong-Referenzpfad.

Die lokale Änderung in `widgets\phoenix\views\image_view.py` betrifft nur PhoenixButton-/Compare-UI und ist kein Restaurationsalgorithmus.

## Exakter validierter FiDeSR-Strong-Runner

Runner:
`C:\SnapdragonAI\temp\fidesr_full_npu_test\run_fidesr_full_npu.py`

Bekannte Referenzausgabe:
`C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_STRONG.png`

Runner SHA256:
`ADFDEBD8729E23A33D6572C6EDAE6ABFB824FE14426F6C97B7B742EA168C196D`

FiDeSR-QNN-Modelle:
- `C:\SnapdragonAI\models\photo_restore\fidesr_vae_encoder.dlc`
- `C:\SnapdragonAI\models\photo_restore\fidesr_unet_merged.dlc`
- `C:\SnapdragonAI\models\photo_restore\fidesr_lrrb.dlc`
- `C:\SnapdragonAI\models\photo_restore\fidesr_vae_decoder.dlc`
- `C:\SnapdragonAI\models\photo_restore\fidesr_empty_prompt_embeds.bin`
- `C:\SnapdragonAI\models\photo_restore\fidesr_epsilon_seed231.bin`

Frozen Strong Contract:
- `UPSCALE = 4`
- `PROCESS_SIZE = 512`
- `HF_SCALE = 0.40`
- `LF_SCALE = 0.12`
- `HF_RC = 0.32`
- `HF_ORDER = 2`
- `HF_DMAP_GAMMA = 1.2`
- `LF_HF_MERGE_RATIO = 0.5`

NPU-Stage-Reihenfolge:
1. VAE Encoder – NPU/QNN/HTP, externes Product-Tiling
2. UNet merged – NPU/QNN/HTP, Latent-Tiling
3. LRRB – NPU/QNN/HTP
4. VAE Decoder – NPU/QNN/HTP, Latent-Tiling

QNN Runtime:
- Qualcomm AIStack 2.47.0.260601
- `qnn-net-run.exe`
- `QnnHtp.dll`
- `QnnModelDlc.dll`
- Hexagon v73
- Runner meldet `ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS`

CPU ist im validierten FiDeSR-Strong-Pfad nur für:
- Tiling / Stitching
- LF/HF nicht-AI-Mathematik
- Butterworth-Filter
- Wavelet Color Fix
- I/O / Orchestrierung

## Produktentscheidung für nächsten Sprint

Keine weiteren Proxy-MicroDetail-Experimente vor der Studio-Integration.

Priorität:
1. Produktiven FiDeSR-Strong-Backendadapter entwerfen.
2. Bestehende Photo-Restore-UI/Controller-Schnittstelle möglichst beibehalten.
3. NAFNet als primären Restore-Pfad durch FiDeSR Strong ersetzen.
4. DDColor nur separat/optional behandeln, falls weiterhin gewünscht.
5. RealESRGAN nicht blind hinter FiDeSR schalten; nur wenn der validierte FiDeSR-Outputpfad dies tatsächlich benötigt.
6. Zuerst 1:1 Studio-vs-Runner-Qualitätsparität auf den Referenzbildern beweisen.
7. Erst danach MicroDetail P2 fortsetzen.

WICHTIG:
- Noch keine produktive Codeänderung freigegeben.
- Kein Git/Build/Commit/Push ohne ausdrückliche Freigabe.
- Nächster Codeänderungs-Sprint benötigt Freigabe.



# CHATGPT_HANDOVER – Ergänzung 15. September 2026 – FiDeSR Strong, DDColor NPU, Qualitätsreferenz und VAE-Root-Cause

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeits- und Tokenregel – ab jetzt besonders streng

- Sprache weiterhin Deutsch.
- Holger hat ausdrücklich darauf hingewiesen, dass zwei zu breite Codex-Sprints zuvor etwa **93 % des verfügbaren Codex-Tokenbudgets** verbraucht haben.
- Deshalb ab jetzt verbindlich:
  - Codex nur für **einen einzigen eng begrenzten Auftrag pro Sprint**.
  - Zielgröße: **5–10 Minuten** und möglichst nur etwa **6–7 % Tokenbudget pro Sprint**.
  - Keine langen Wiederholungen des gesamten Projektkontexts in Codex-Prompts.
  - Keine breiten Entscheidungsbäume oder Nebenanalysen, wenn ein kleiner isolierter Test genügt.
  - Bei sehr niedrigem Codex-Budget Antigravity bevorzugen.
  - Vor jedem Codex-/Antigravity-Sprint exakt prüfen, welcher einzelne Auftrag wirklich nötig ist.
- Holger verlangt weiterhin vollständige ausführbare PowerShell-Blöcke, wenn PowerShell eingesetzt wird; keine Teil-Snippets.
- Keine Builds, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- TECH PASS, QUALITY PASS und PRODUCT PASS weiterhin strikt getrennt bewerten.

## Verbindliche NPU-Produktregel

Für HK NPU STUDIO gilt weiterhin:

- eigentliche KI-Inferenz nur über Snapdragon NPU / Qualcomm QNN / HTP;
- CPU nur für nicht-neuronale Orchestrierung, Resize, Tiling, Stitching, Masken, Datei-I/O, Farb-/Wavelet-Mathematik und ähnliche deterministische Verarbeitung;
- keine CPU- oder GPU-KI-Pfade als gleichwertige Produktlösung.

## FiDeSR Strong – produktiver NPU-Basispfad

Produktive Modelle:

```text
C:\SnapdragonAI\models\photo_restore\fidesr_vae_encoder.dlc
C:\SnapdragonAI\models\photo_restore\fidesr_unet_merged.dlc
C:\SnapdragonAI\models\photo_restore\fidesr_lrrb.dlc
C:\SnapdragonAI\models\photo_restore\fidesr_vae_decoder.dlc
C:\SnapdragonAI\models\photo_restore\fidesr_empty_prompt_embeds.bin
C:\SnapdragonAI\models\photo_restore\fidesr_epsilon_seed231.bin
```

Eingefrorene Parameter:

```text
UPSCALE=4
PROCESS_SIZE=512
HF_SCALE=0.40
LF_SCALE=0.12
LF_RC=0.10
LF_ORDER=2
LF_TAU=0.8
LF_SHARP=10.0
LF_DMAP_GAMMA=1.2
HF_RC=0.32
HF_ORDER=2
HF_DMAP_GAMMA=1.2
LF_HF_MERGE_RATIO=0.5
LATENT_TILE=64
LATENT_OVERLAP=16
VAE_PIXEL_TILE=512
```

Kanonischer Runner:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\run_fidesr_full_npu.py
SHA256=ADFDEBD8729E23A33D6572C6EDAE6ABFB824FE14426F6C97B7B742EA168C196D
```

Kanonischer Output:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_STRONG.png
672x904
SHA256=E6434B7C4F15AE1F898AF20EBEB0552065FC1AC307A8A43E47E3A05810EC7D81
```

Input:

```text
C:\Users\holge\Desktop\Testbilder\3.jpg
169x226
```

Status:

```text
FIDESR_TECH_PASS=YES
FIDESR_QUALITY_PASS=NO
FIDESR_PRODUCT_PASS=NO
```

Hauptproblem: Haut wirkt zu glatt/wachsartig; natürliche Poren, Bartstoppeln und einzelne Haare fehlen.

## FiDeSR Strong – Studio-Integration

Produktiver Adapter:

```text
C:\SnapdragonAI\engine\backends\fidesr_photo_restore_backend.py
```

Runner-Template:

```text
C:\SnapdragonAI\engine\backends\fidesr_strong_runner_template.py
```

Controller:

```text
C:\SnapdragonAI\controllers\photo_restore_controller.py
```

Der Controller verwendet FiDeSRPhotoRestoreBackend als Standardpfad. Controller-Smoke und Studio-Parität wurden bestätigt; die Studio-/Controller-Ausgabe war pixelidentisch zum kanonischen FiDeSR-Output. Keine Aussage daraus als QUALITY PASS ableiten.

## DDColor – produktiver QNN/HTP-Pfad integriert

Produktiver DDColor-Context:

```text
C:\SnapdragonAI\models\photo_restore\ddcolor.dlc.bin
SHA256=944256D21BDB9213E1072F3EAA92FA1E66D4C1373796B6305CAA399EEC3CCB70
```

FiDeSR-Backend nach Integration:

```text
C:\SnapdragonAI\engine\backends\fidesr_photo_restore_backend.py
SHA256=874DFAC383C56B7E7F76BC03F1257BDD6AC962B967B30020CE7A60F7CF690841
```

Vertrag:

```text
Graustufenbild + Auto Colorize ON -> DDColor QNN/HTP
Farbbild + Auto Colorize ON       -> DDColor wird übersprungen
Auto Colorize OFF                 -> DDColor wird übersprungen
CPU_AI_INFERENCE=NO
GPU_AI_INFERENCE=NO
```

Colorize-Checkbox bleibt erhalten.

Realer DDColor-QNN/HTP-Smoke:

```text
INPUT=C:\SnapdragonAI\temp\fidesr_ddcolor_integration_20260915\3_FIDESR_DDCOLOR_INPUT_GRAY.png
OUTPUT=C:\SnapdragonAI\temp\fidesr_ddcolor_integration_20260915\3_FIDESR_DDCOLOR_NPU.png
GRAY_INPUT_SIZE=(672,904)
DDCOLOR_SECONDS=1.64
GRAY_INPUT_CHANNEL_SPREAD=0.000000
DDCOLOR_OUTPUT_CHANNEL_SPREAD=45.545689
MEAN_ABS_CHANGE=17.163404
DDCOLOR_NEURAL_INFERENCE=QNN_HTP
CPU_AI_INFERENCE=NO
GPU_AI_INFERENCE=NO
DDCOLOR_QNN_HTP_SMOKE=PASS
TECH_PASS=YES
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

Nach erfolgreicher Inferenz erschien beim Teardown `Error 0x200: failed to close queue ...`. Da Inferenz, Output und Modell-Destroy zuvor erfolgreich waren, aktuell als Cleanup-/Runtime-Warnung klassifiziert, nicht als Inferenzfehler.

## DDColor – visuelle Qualitätsentscheidung

Holger stellte reale Zielreferenzen bereit. Bewertung des aktuellen DDColor-Ergebnisses:

- Farbzonen grundsätzlich plausibel.
- Keine groben Flächenfehler.
- Haut jedoch deutlich zu warm/orange.
- Lippen teilweise zu rosa/magenta.
- Innenraum insgesamt zu kräftig warm/braun.
- Hauptproblem bleibt zusätzlich die zu glatte FiDeSR-Hautstruktur.

Ein geplanter Chroma-0.75-Tuning-Sprint wurde bewusst **nicht** weitergeführt, nachdem die Referenzbilder zeigten, dass das Hauptproblem deutlich größer ist als reine Farbsättigung.

Status:

```text
DDCOLOR_TECH_PASS=YES
DDCOLOR_QUALITY_PASS=NO
DDCOLOR_PRODUCT_PASS=NO
```

## Neue visuelle Qualitätsreferenz

Holgers Referenzbilder definieren ab jetzt verbindlich die Zielqualität für Photo Restore. Ziel:

- natürliche Hautporen;
- kleine Hautunregelmäßigkeiten;
- einzelne Bartstoppeln;
- einzelne Haare;
- natürlicher Haaransatz;
- feine Augenbrauen;
- glaubwürdige Stoffstruktur;
- natürliche Hautfarben;
- kein Airbrush-/Wachs-/Plastiklook.

Künstliche Fantasiehaare, Hatching, Halos, Doppelkonturen und Rauschtextur sind kein Qualitätsgewinn. Referenzbilder dienen als visuelle Zielqualität, nicht als Pixelkopie.

## MicroDetail P2 – Status bleibt offen, nicht verworfen

```text
BEST_EPOCH=180
BEST_VAL_GAIN_DB=+1.5708
TRAIN_GAIN_DB=+2.6316
VAL_IMPROVED=2/2
P2_TECH_PASS=YES
P2_NUMERIC_GATE=PASS
P2_QUALITY_PASS=NO
P2_PRODUCT_PASS=NO
P2_ONNX_EXPORT=NO
P2_QNN_COMPILE=NO
P2_STUDIO_INTEGRATION=NO
```

P2 ist nicht aufgegeben. Erst FiDeSR-Glättungsursache eingrenzen, danach P2 mit größerem realem FiDeSR-Datensatz für Haut/Haar/Bart neu optimieren. ONNX/QNN erst nach sichtbarem QUALITY PASS.

## FiDeSR-Root-Cause – Ergebnisse

Codex bestätigte u. a.:

- produktiver und kanonischer Runner textgleich;
- für `3.jpg` Encoder-Pixelpositionen `X=[0,160]`, `Y=[0,384,392]`;
- UNet-/Decoder-Latentpositionen `X=[0,20]`, `Y=[0,48,49]`;
- letzte Decoder-Zeilen überlappen 504 von 512 Ausgabepixeln;
- lokaler NPU-Pfad decodiert sechs unabhängige 64×64-Latent-Tiles.

### Test 1 – Gaussian Decoder Fusion

Diagnoseordner:

```text
C:\SnapdragonAI\temp\fidesr_decoder_fusion_ab_20260915
```

Ein reproduzierbarer QNN/HTP-Lauf dauerte 284.46 s. Sechs Decoder-Tiles:

```text
Latent XY: (0,0),(20,0),(0,48),(20,48),(0,49),(20,49)
Pixel XY:  (0,0),(160,0),(0,384),(160,384),(0,392),(160,392)
Output Shape je Tile: [1,3,512,512]
```

A = bestehende Gaussian-Mischung, B = Winner-Takes-Highest-Weight. Ergebnis:

```text
A_VS_B_PRE_MAE=0.078128
A_VS_B_PRE_PSNR=57.273394 dB
A_VS_B_FINAL_MAE=0.076129
A_VS_B_FINAL_PSNR=57.465378 dB
DECODER_FUSION_DETAIL_LOSS=NOT_PRIMARY
DECODER_FUSION_REPLACEMENT=REJECTED
TECH_PASS=YES
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

A stimmte pixelgenau mit der normalen Runner-Ausgabe überein. Die letzte Gaussian-Fusion ist nicht die Hauptursache. B nicht integrieren.

### Test 2 – Halo / valid crop

```text
HALO_IMPROVES_NATURAL_DETAIL=NO
SEAMS_OR_ARTIFACTS=YES
TECH_PASS=YES
QUALITY_PASS=NO
```

Halo/valid-crop bringt beim vorhandenen statischen Decoder keinen sichtbaren natürlichen Detailgewinn und erzeugt zusätzliche Nähte/Artefakte. Nicht integrieren.

### Test 3 – Single-Tile VAE Decoder

ROI:

```text
Latent [y=48..112, x=0..64]
-> Pixel [y=384..896, x=0..512]
Gesicht/Wange/Bart
```

Ergebnis:

```text
SINGLE_TILE_DECODER_RUN=PASS
QNN_HTP=PASS
EXIT_CODE=0
RUNTIME_SECONDS=122.01
MAX_ABS_DIFF=0.000000
SINGLE_TILE_ALREADY_SMOOTH=YES
MICRODETAIL_PRESENT=NO
TECH_PASS=YES
QUALITY_PASS=NO
```

Der Single-Tile-Output war bitgenau identisch zum entsprechenden Decoder-Tile des bisherigen Laufs. Damit sind Gaussian-Fusion, Winner-Takes-All, Halo, Stitching und Tile-Auswahl praktisch entlastet.

Wichtig: Noch nicht bewiesen ist, ob der VAE-Decoder selbst glättet oder das Eingabelatent bereits zu detailarm ist.

## Decoder-Graph-Vertrag

```text
INPUT_SHAPE=[1,4,64,64]
DTYPE=FLOAT16
LAYOUT=NCHW
OUTPUT_SHAPE=[1,3,512,512]
FULL_FRAME_WITH_EXISTING_DLC=NO
```

Das aktuelle Full-Frame-Latent 84×113 passt nicht in den statischen Decodergraphen. Keine Neucompilierung gestartet.

## Disk-Cleanup 14./15. September 2026

Sicher bereinigt:

```text
C:\SnapdragonAI\temp\flux2_first_real_npu_image_20260906_092320   ~8.228 GB
C:\SnapdragonAI\temp\flux2_fullframe_672x960_s5168              ~7.885 GB
C:\Users\holge\Downloads\HK_NPU_FiDeSR_QNN_Final_20260912.zip  ~3.542 GB
2394 __pycache__ Ordner                                               ~337.29 MB
```

Ergebnis:

```text
C_FREE_BEFORE_GB=9.71
C_FREE_AFTER_GB=29.73
ACTUAL_FREED_GB=20.02
```

Cleanup-Report:

```text
C:\SnapdragonAI\temp\disk_cleanup_20260914\cleanup_result.txt
SHA256=A35EB55607BD5AFC7E59B052FAE93E91D37C0C7740704CEBDCCE638FD9FA1E26
```

Keine Produktmodelle, Source-Dateien, P2-Beweise, Git-Daten oder relevante Backups wurden gelöscht.

## Geschützte P2-Artefakte

Nicht löschen:

```text
C:\SnapdragonAI\temp\HK_NPU_MICRODETAIL_P2_REAL_FIDESR_PROOF8_RESULT.zip
SHA256=3ABE4EC5F50128A7D2A27D36B2BE951F58000FB5CDA18D5C45981945C749BE92

C:\SnapdragonAI\temp\HK_NPU_MICRODETAIL_P2_VISUAL_GATE.zip
SHA256=E59F0528AC24EACAD923441CAA84A07858257CC93279B08A7EFCE340CC71DE29

C:\SnapdragonAI\temp\HK_NPU_MICRODETAIL_P2_REAL_FIDESR_PROOF8.zip
SHA256=42A44403DD7D4EDED848DCDA228F6E0AA5856D0B630535AA9BBCBAAB2D360E4A
```

## Git-/Build-Status dieser Photo-Restore-Arbeit

```text
BUILD=NO
INSTALLER=NO
GIT_ADD=NO
COMMIT=NO
PUSH=NO
QNN_RECOMPILE=NO
ONNX_EXPORT=NO
```

Es existieren lokale geänderte/untracked Dateien aus den aktuellen Studio-/Photo-Restore-Arbeiten. Nichts pauschal bereinigen, zurücksetzen oder stagen.

## Exakter Wiedereinstieg

Bei Wiederaufnahme nicht erneut Gaussian, Halo oder Winner-Takes-All testen. Zuerst nur prüfen, ob bereits ein eindeutig zuordenbarer FiDeSR-VAE-only-Roundtrip für `3.jpg` vorhanden ist:

```text
Encoder -> Decoder
ohne UNet
ohne LRRB
ohne LF/HF
ohne Wavelet
```

Wenn vorhanden, nur visuell vergleichen: Stirn, Wange, Bart, Haaransatz, Augenbraue, Hemd.

Wenn VAE-only bereits dieselbe Glätte zeigt:

```text
VAE_ALONE_CAUSES_SMOOTHING=YES
```

Dann Fokus auf VAE-Bottleneck / geeigneten NPU-VAE-Pfad bzw. später MicroDetail-Refiner.

Wenn VAE-only deutlich mehr natürliche Mikrodetails zeigt:

```text
VAE_ALONE_CAUSES_SMOOTHING=NO
```

Dann Fokus auf Encoder-Latent / UNet / LRRB / LF-HF vor dem Decoder.

Wenn kein eindeutiger bestehender Roundtrip vorhanden ist: STOP und erst dann minimalen neuen NPU-Test planen. Keine FFT-/PSD-Analyse des Latents vor diesem Vergleich.

## Statusflags – Arbeitspause 15. September 2026

```text
PRODUKTNAME=HK NPU STUDIO
FIDESR_STRONG_NPU_TECH_PASS=True
FIDESR_STRONG_QUALITY_PASS=False
FIDESR_STRONG_PRODUCT_PASS=False
FIDESR_STUDIO_INTEGRATED=True
FIDESR_STUDIO_PARITY_PASS=True
DDCOLOR_NPU_TECH_PASS=True
DDCOLOR_QUALITY_PASS=False
DDCOLOR_PRODUCT_PASS=False
DDCOLOR_CHECKBOX_KEPT=True
DDCOLOR_CPU_AI=False
DDCOLOR_GPU_AI=False
GAUSSIAN_DECODER_FUSION_PRIMARY_CAUSE=False
HALO_IMPROVES_NATURAL_DETAIL=False
HALO_ARTIFACTS=True
SINGLE_TILE_DECODER_ALREADY_SMOOTH=True
SINGLE_TILE_MICRODETAIL_PRESENT=False
FIDESR_DECODER_INPUT_SHAPE=1x4x64x64
FIDESR_FULL_FRAME_WITH_EXISTING_DECODER_DLC=False
MICRODETAIL_P2_NUMERIC_PASS=True
MICRODETAIL_P2_QUALITY_PASS=False
MICRODETAIL_P2_QNN_COMPILE=False
NEXT_SESSION=CHECK_EXISTING_VAE_ONLY_ROUNDTRIP_FOR_3JPG
PREFERRED_TOOL=ANTIGRAVITY_IF_CODEX_BUDGET_LOW
CODEX_SPRINT_TARGET=ONE_SMALL_TASK_ONLY
CODEX_SPRINT_TIME_TARGET=5_TO_10_MINUTES
BUILD_15_SEPTEMBER=False
INSTALLER_15_SEPTEMBER=False
GIT_ADD_15_SEPTEMBER=False
COMMIT_15_SEPTEMBER=False
PUSH_15_SEPTEMBER=False
```

## Arbeitspause 15. September 2026

Holger hat die Arbeit bewusst unterbrochen. Heute keine weiteren Codex-/Antigravity-Sprints, QNN-Läufe, Builds, Installer, Commits, Pushes oder Recompiles.

## Handover-Übernahme

Diese vollständige Datei als exakt `CHATGPT_HANDOVER.md` bereitstellen. Holger übernimmt sie anschließend über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die ältere Chronik niemals kürzen oder durch eine separate Ergänzungsdatei ersetzen.
# CHATGPT_HANDOVER – Ergänzung Tagesabschluss 15. September 2026 – FiDeSR Root-Cause, MicroDetail P3 und Kaggle-Fingerprint

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt vollständig erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsmodus – verbindlich

- Sprache mit Holger: Deutsch.
- Antworten kurz, direkt und technisch vollständig.
- Nach einem ausgewerteten Ergebnis unmittelbar den nächsten sinnvollen Schritt geben; nicht routinemäßig mit „soll ich?“ stoppen.
- PowerShell bevorzugen, wenn die Aufgabe lokal eindeutig und ohne Codex/Antigravity lösbar ist.
- Codex- und Antigravity-Sprints strikt tokenoptimiert und klein halten; typisches Ziel 5–10 Minuten und ein einzelner klarer Auftrag.
- Vor jedem technischen Sprint sichtbar angeben:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern oder löschen.
- Für Produktfunktionen gilt weiterhin:
  - `TECH PASS` ≠ `QUALITY PASS` ≠ `PRODUCT PASS`.
- Für HK NPU STUDIO gilt:
  - KI-Inferenz nur über Snapdragon NPU / QNN / HTP.
  - CPU nur für Orchestrierung, I/O, Resize, Masken, Compositing und deterministische Mathematik.
  - keine CPU-/GPU-KI-Pfade als Produktlösung.
- Kein ONNX-/QNN-Compile für MicroDetail, solange der visuelle Qualitäts-Gate nicht bestanden ist.

## Wichtige neue Ausführungsregel für Kaggle

Nach mehreren unnötigen Fehlern wurde folgende Regel ausdrücklich verbindlich gemacht:

- **Kaggle:** ausschließlich Python-Zellen.
- **Windows-PC:** PowerShell ausschließlich lokal und klar als `WINDOWS – POWERSHELL` kennzeichnen.
- Vor ausführbarem Code immer Zielumgebung, Dateityp, Pfadformat und Syntax gegeneinander prüfen.
- Kaggle-Uploads dürfen nicht blind als ZIP-Datei angenommen werden; zuerst real prüfen, ob Kaggle die Datei als ZIP oder bereits entpackt/mounted bereitstellt.
- Für Kaggle-/Linux-ZIPs keine Windows-Pfade mit `\` verwenden.
- Kaggle-safe ZIPs mit Python `zipfile` und POSIX-Pfaden `/` erzeugen.
- `Compress-Archive` nicht mehr für Kaggle-/Linux-Datensätze verwenden.

## FiDeSR Strong – Root-Cause-Diagnose abgeschlossen

Ausgangspunkt:

```text
C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_STRONG.png
Input: C:\Users\holge\Desktop\Testbilder\3.jpg
Inputgröße: 169x226
Outputgröße: 672x904
```

Technischer Pfad:

```text
VAE Encoder -> UNet -> LRRB -> VAE Decoder
```

Zusätzlich deterministisch:

```text
LF/HF -> Wavelet / Merge
```

Die sichtbare Hauptschwäche war weiterhin glatte/wachsartige Haut mit zu wenig Poren, Bartstoppeln und feinen Haaren.

### VAE-only-Test

Arbeitsordner:

```text
C:\SnapdragonAI\temp\fidesr_vae_only_3jpg_20260915
```

Messwerte:

```text
QNN Encoder: 20.54 s
QNN Decoder: 52.56 s
Gesamt: 73.10 s
```

Regionen:

```text
Forehead: MAE 0.49 / PSNR 50.97
Cheek:    MAE 0.62 / PSNR 48.82
Beard:    MAE 0.87 / PSNR 46.42
Hairline: MAE 1.31 / PSNR 42.32
Eyebrow:  MAE 0.82 / PSNR 47.09
Shirt:    MAE 0.99 / PSNR 45.72
```

Ergebnis:

```text
VAE_ALONE_CAUSES_SMOOTHING=NO
VAE_ONLY_QUALITY_PASS=YES
```

### UNet-Isolation

```text
UNET_CAUSES_SMOOTHING=YES
QUALITY_FAIL=YES
```

Messung:

```text
QNN UNet: 79.14 s
QNN Decoder: 54.75 s
Gesamt: 133.89 s
```

Der UNet ist die primäre Quelle der wachsartigen Glättung.

### LRRB-Isolation

```text
LRRB_RESTORES_DETAIL=YES
LRRB_WORSENS=NO
LRRB_EFFECT=RESTORES
QUALITY_PASS=YES
```

Detailwirkung:

```text
Forehead: 3.15 -> 7.63
Cheek:   16.69 -> 90.06
Beard:   50.91 -> 356.79
Hairline:73.64 -> 647.05
Eyebrow: 29.69 -> 275.13
Shirt:   28.14 -> 246.25
```

LRRB stellt vorhandene Kanten-/Haarinformation deutlich wieder her, rekonstruiert aber verlorene flache Haut-Mikrotextur nicht vollständig.

### LF/HF-Isolation

```text
LFHF_RESTORES_DETAIL=NO
LFHF_WORSENS=NO
LFHF_EFFECT=NEUTRAL_TO_LIGHT_EXISTING_HF_BOOST
```

LF/HF erzeugt keine neuen natürlichen Poren/Haare; es verstärkt hauptsächlich vorhandene Hochfrequenzinformation.

### Finale Root-Cause

```text
VAE = sauber
UNet = Hauptquelle der Glättung
LRRB = teilweise Detailwiederherstellung
LF/HF = neutral bis leichte Verstärkung vorhandener HF
MICRODETAIL_STAGE_B_REQUIRED=YES
```

## MicroDetail P2 – Bewertung

```text
Parameter: 1,947,715
Residual U-Net
Loss: L1 + 0.35 Sobel
Epochs: 180
BEST_VAL_GAIN_DB=+1.5708
TRAIN_GAIN_DB=+2.6316
VAL_IMPROVED=2/2
```

Visuell jedoch:

- zu viel allgemeine Schärfung,
- falsche Textur,
- Linien-/Kantenartefakte,
- nicht gezielt genug auf Poren/Bart/Haar.

Status:

```text
MICRODETAIL_P2_NUMERIC_PASS=True
MICRODETAIL_P2_QUALITY_PASS=False
```

Geschützte Archive bleiben unverändert erhalten.

## MicroDetail P3 – initialer 5-Paar-Proof

Arbeitsordner:

```text
C:\SnapdragonAI\temp\microdetail_p3_pairset_20260915
```

Akzeptierte Paare:

```text
P3_01_BEARD_0149_026
P3_02_BEARD_0115_040
P3_03_BEARD_0125_195
P3_05_BEARD_0116_266
P3_06_BEARD_0149_408
```

Loss:

```text
L = 1.0 * L1_RGB + 0.25 * clipped_DoG_HF
sigma1=0.5
sigma2=1.5
tau=0.15
```

Kein Sobel.

Training:

```text
180 Epochs
Adam
LR=0.0002
```

Ergebnis:

```text
BEST_EPOCH=180
TRAIN_GAIN_DB=+1.399
VAL_GAIN_DB=+0.733
VAL_IMPROVED=1/1
PORES=subtle_improved
BEARD_STUBBLE=natural_reconstruction
HAIR=improved
EYEBROW=moderate
HALOS=none
FAKE_LINES=none
OVERSHARPENING=none
COLOR_DRIFT=none
P3_TECH_PASS=YES
P3_QUALITY_PASS=PARTIAL_PASS
P3_PRODUCT_PASS=NO
```

## Erweiterung des P3-Pairsets

Kontaktblatt:

```text
C:\SnapdragonAI\temp\microdetail_p3_gt001_011_review_20260915\GT_001_011_CONTACT_SHEET.png
SHA256=0AC89A42B7B6C3FC842D25ACFFD3FAF779BFA93E24EC9746F1B2C27834F88844
```

Für die Erweiterung nach echten FiDeSR-Strong-QNN/HTP-Läufen behalten:

```text
GT_001
GT_003
GT_006
GT_007
GT_011
```

Verworfen:

```text
GT_004
```

Extended-Pairset:

```text
C:\SnapdragonAI\temp\microdetail_p3_pairset_extended_20260915
```

## Finaler P3 Training10-Datensatz

```text
C:\SnapdragonAI\temp\microdetail_p3_training10_20260915
```

Ergebnis:

```text
INPUT_COUNT=10
GT_COUNT=10
ALIGNMENT_PASS=YES
DATASET_READY=YES
SKIN_PAIRS=10
BEARD_PAIRS=7
HAIR_PAIRS=9
EYEBROW_PAIRS=6
FABRIC_PAIRS=2
```

Manifest:

```text
C:\SnapdragonAI\temp\microdetail_p3_training10_20260915\TRAINING_MANIFEST.txt
```

### Kaggle-safe ZIP-Regel

Erste ZIP mit Windows-Pfadtrennern nicht mehr verwenden:

```text
C:\SnapdragonAI\temp\HK_NPU_MICRODETAIL_P3_TRAINING10_20260915.zip
SHA256=83D1486E8B4C2C4E542C4680753DB07ADF1EB3F54108C2AA47C0178EE8FBFC70
```

Kaggle-safe ZIP wurde mit Python `zipfile` und POSIX-Pfaden erzeugt:

```text
C:\SnapdragonAI\temp\HK_NPU_MICRODETAIL_P3_TRAINING10_KAGGLE_SAFE_20260915.zip
```

Kaggle mountet den Datensatz unter:

```text
/kaggle/input/datasets/hknpustudio/p3-training/microdetail_p3_training10_20260915
```

Preflight:

```text
PYTORCH_VERSION=2.10.0+cu128
CUDA_AVAILABLE=True
GPU_NAME=Tesla T4
INPUT_COUNT=10
GT_COUNT=10
PAIR_ID_MATCH=PASS
DATASET_PREFLIGHT=PASS
READY_FOR_P3_TRAINING10=YES
```

## P2-Checkpoint – exakter Parametervertrag

Kaggle:

```text
/kaggle/input/datasets/hknpustudio/p2-real-fidesr/microdetail_p2_real_fidesr_proof8.pt
```

Verifiziert:

```text
BYTES=7803313
TENSOR_COUNT=30
TOTAL_PARAMETERS=1947715
best_epoch=180
best_val_gain_db=1.5707593256661028
train_gain_db=2.6316035523379693
val_gain_db=1.5707593256661028
val_improved=2
val_count=2
runtime_sec=105.94173510500002
seed=20260914
epochs=180
learning_rate=0.0002
```

Tensor-/Kanalstruktur:

```text
e1: 3 -> 32 -> 32
e2: 32 -> 64 -> 64
e3: 64 -> 128 -> 128
mid: 128 -> 256 -> 256
u3: 384 -> 128 -> 128
u2: 192 -> 64 -> 64
u1: 96 -> 32 -> 32
out: 32 -> 3
```

Wichtig:

Der Checkpoint beweist Gewichte, Shapes und Parametrisierung, aber nicht vollständig Aktivierungsfunktionen, Pooling, Upsampling, Residual-Skalierung und Output-Transformation. Diese Details dürfen nicht aus dem Checkpoint allein als „exakt rekonstruiert“ bezeichnet werden.

## P3 Training10 – erster Lauf QUALITY FAIL

Kaggle-Arbeitsordner:

```text
/kaggle/working/HK_NPU_MICRODETAIL_P3_TRAINING10
```

Erzeugt:

```text
microdetail_p3_training10_best.pt
P3_TRAINING10_CONTACT_SHEET.png
P3_TRAINING10_METRICS.json
```

Das Kontaktblatt zeigte:

- MicroDetail-Ausgabe vielfach weicher als FiDeSR-Input,
- Bartstoppeln reduziert,
- Haare reduziert,
- Hautstruktur reduziert,
- Konturen geglättet.

Status:

```text
P3_TRAINING10_TECH_RUN=COMPLETED
P3_TRAINING10_QUALITY_PASS=NO
P3_TRAINING10_PRODUCT_PASS=NO
ONNX_EXPORT=NO
QNN_COMPILE=NO
```

Nicht weiterverwenden.

## Originaler P2-Trainingscode – nicht gefunden

Das geschützte P2-Ergebnisarchiv enthält Checkpoint, Daten, Split und Ergebnisbilder, aber keinen Trainingscode.

Gezielte lokale Suche in `microdetail_*` ergab keinen Original-Trainingscode.

Gefunden wurde nur:

```text
C:\SnapdragonAI\temp\microdetail_real_fidesr_pairset_p2\build_kaggle_safe_zip.py
```

Status:

```text
ORIGINAL_P2_TRAINING_CODE_FOUND=False
```

## P2-Fingerprint-Datensatz in Kaggle

```text
/kaggle/input/datasets/hknpustudio/p2-real-fidesr
```

Vorhanden:

```text
8 Inputs
8 Targets
data/split.csv
P2 Checkpoint
8 BEFORE_AFTER_GT Ergebnisbilder
```

Validation:

```text
ref01_p2_03
ref22_p2_04
```

Fingerprint readiness:

```text
P2_FINGERPRINT_READY=YES
```

## Architektur-Fingerprint – erster Variantenraum nicht ausreichend

Getestet wurden Kombinationen aus ReLU/LeakyReLU/SiLU/GELU, finaler Blockaktivierung, Max/Avg-Pooling, Nearest/Bilinear-Upsampling, Residual an/aus und Output none/clamp/sigmoid.

Erwartet:

```text
EXPECTED_VAL_GAIN_DB=1.5707593256661028
EXPECTED_VAL_IMPROVED=2/2
```

Bester gefundener Kandidat:

```text
FOUND_GAIN=-7.851450107596953
ABS_ERROR=9.422209433263056
VAL_IMPROVED=0/2
ACT=silu
FINAL_ACTIVATION=True
POOL=avg
UPSAMPLE=bilinear_true
RESIDUAL=True
OUTPUT_MODE=clamp
ARCHITECTURE_FINGERPRINT=NOT_EXACT_YET
```

Damit den Forward-Pfad nicht weiter blind raten.

## Exakter Wiedereinstieg am nächsten Arbeitstag

Die alten P2-Ergebnisbilder enthalten `BEFORE | AFTER | GT`.

Nächster Schritt:

1. Geometrie der 8 `*_BEFORE_AFTER_GT.png` auslesen.
2. Originales `AFTER`-Panel pixelgenau extrahieren.
3. Kandidaten direkt pixelweise gegen dieses originale P2-`AFTER` vergleichen.
4. Zusätzliche unbekannte Forward-Details identifizieren.
5. Erst bei reproduzierbarem Original-Fingerprint Training10 erneut starten.
6. Kein ONNX/QNN vorher.

## Kaggle-Sicherungsbedarf bei Feierabend

Der erste Training10-Lauf ist QUALITY FAIL, seine Artefakte sind aber als Diagnose wertvoll.

Zu sichern:

```text
/kaggle/working/HK_NPU_MICRODETAIL_P3_TRAINING10
```

Empfohlene ZIP:

```text
/kaggle/working/HK_NPU_MICRODETAIL_P3_TRAINING10_DIAGNOSTIC_20260915.zip
```

Die P2-/P3-Trainingsdaten unter `/kaggle/input/...` müssen nicht dupliziert werden.

## Git-/Build-Status

```text
BUILD_15_SEPTEMBER=False
INSTALLER_15_SEPTEMBER=False
GIT_ADD_15_SEPTEMBER=False
COMMIT_15_SEPTEMBER=False
PUSH_15_SEPTEMBER=False
MICRODETAIL_ONNX_EXPORT=False
MICRODETAIL_QNN_COMPILE=False
```

## Statusflags – Feierabend 15. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

FIDESR_VAE_ONLY_QUALITY_PASS=True
FIDESR_VAE_PRIMARY_SMOOTHING_CAUSE=False
FIDESR_UNET_CAUSES_SMOOTHING=True
FIDESR_LRRB_RESTORES_DETAIL=True
FIDESR_LFHF_EFFECT=NEUTRAL_TO_LIGHT_EXISTING_HF_BOOST

MICRODETAIL_P2_NUMERIC_PASS=True
MICRODETAIL_P2_QUALITY_PASS=False

MICRODETAIL_P3_PAIRSET_INITIAL=5
MICRODETAIL_P3_PROOF_TECH_PASS=True
MICRODETAIL_P3_PROOF_QUALITY_PASS=PARTIAL_PASS
MICRODETAIL_P3_PRODUCT_PASS=False

MICRODETAIL_P3_TRAINING10_PAIR_COUNT=10
MICRODETAIL_P3_TRAINING10_DATASET_READY=True
MICRODETAIL_P3_TRAINING10_KAGGLE_PREFLIGHT=PASS
MICRODETAIL_P3_TRAINING10_FIRST_RUN_QUALITY_PASS=False
MICRODETAIL_P3_TRAINING10_FIRST_RUN_PRODUCT_PASS=False

P2_CHECKPOINT_PARAMS=1947715
P2_ORIGINAL_TRAINING_CODE_FOUND=False
P2_FINGERPRINT_READY=True
P2_FIRST_ARCHITECTURE_FINGERPRINT_EXACT_MATCH=False

NEXT_SESSION=P2_RESULT_GEOMETRY_AND_PIXEL_EXACT_AFTER_FINGERPRINT
KAGGLE_SAVE_DIAGNOSTIC_ZIP=True
```

## Feierabend 15. September 2026

Für heute keine weiteren Trainingsläufe, Architektur-Suchen, Kaggle-Experimente, ONNX-Exporte, QNN-Compiles, Builds, Installer, Commits oder Pushes.

Morgen direkt fortsetzen mit:

```text
P2 BEFORE_AFTER_GT Geometrie
-> originales AFTER extrahieren
-> pixelgenauer Architektur-Fingerprint
-> erst danach korrigiertes Training10
```

## Handover-Übernahme

Diese vollständige Datei als exakt `CHATGPT_HANDOVER.md` bereitstellen.

Übernahme auf dem Entwicklungs-PC:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

Ziel:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die ältere Chronik niemals kürzen oder durch eine separate Ergänzungsdatei ersetzen.

# CHATGPT_HANDOVER – Ergänzung 16. September 2026 – FiDeSR-Glättungsursache, MicroDetail-Abbruch und Detail-Preservation-Durchbruch

> Diese Ergänzung gehört zur vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die ältere Chronik bleibt vollständig erhalten. Bei Widersprüchen gilt dieser neuere Stand.
> **Datum: 16. September 2026.**

## Verbindliche Arbeitsregeln

- Sprache: Deutsch; kurz, direkt, vollständig.
- Nach Ergebnisbewertung direkt den nächsten notwendigen Schritt liefern.
- Codex/Antigravity nur tokenoptimiert und eng begrenzt einsetzen.
- KAGGLE = nur Python.
- WINDOWS lokal = PowerShell, klar als `WINDOWS – POWERSHELL` kennzeichnen.
- Kaggle-ZIPs nur mit Python `zipfile` und POSIX-Pfaden erzeugen.
- Keine Builds, Installer, Git-Staging-Aktionen, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- TECH PASS, QUALITY PASS und PRODUCT PASS strikt trennen.
- Keine neue ONNX-/QNN-Kompilierung vor bestandenem visuellen Qualitäts-Gate.
- Produktziel bleibt: neuronale KI-Inferenz ausschließlich Snapdragon NPU / QNN / HTP.
- CPU nur für deterministische Orchestrierung, I/O, Resize, Masken, Compositing und Frequenz-/Farbraum-Mathematik.

## FiDeSR Strong – bestätigte Glättungsursache

Canonical Runner:

`C:\SnapdragonAI\temp\fidesr_full_npu_test\run_fidesr_full_npu.py`

Canonical Output:

`C:\SnapdragonAI\temp\fidesr_full_npu_test\3_FIDESR_NPU_STRONG.png`

Isolationsbefund:

```text
VAE_ALONE_CAUSES_SMOOTHING=NO
UNET_CAUSES_SMOOTHING=YES
LRRB_RESTORES_DETAIL=YES
LF_HF_STAGE_WORSENS=NO
```

Interpretation:

- VAE ist nicht die Hauptursache.
- UNet vernichtet die sichtbaren 1–3-px-Mikrodetails wie Poren, Bartstoppeln und feine Haare.
- LRRB stellt Kanten und einen Teil der Textur zurück, rekonstruiert verlorene biologische Mikrodetails aber nicht vollständig.

## P2-Forward-Pfad pixelgenau rekonstruiert

P2-Checkpoint:

`/kaggle/input/datasets/hknpustudio/p2-real-fidesr/microdetail_p2_real_fidesr_proof8.pt`

Parameter:

`1,947,715`

Originale P2-Resultate:

```text
SIZE=1536x562
Y_OFFSET=50
BEFORE_PANEL=0
AFTER_PANEL=1
GT_PANEL=2
P2_PANEL_EXTRACTION=PIXEL_EXACT_PASS
```

Exakter rekonstruierter Forward-Vertrag:

```text
ConvBlock = Conv -> SiLU -> Conv -> SiLU
Pooling = AvgPool2d(2)
Upsample = bilinear
align_corners = False
Concat = [upsampled, skip]
Residual = x + 0.2 * tanh(raw)
Output = clamp(..., 0, 1)
Quantization = torch_round
```

Finaler Nachweis:

```text
P2_FORWARD_FINGERPRINT=PIXEL_EXACT_PASS
DIFFERENT_RGB_PIXELS=0
DIFFERENT_CHANNEL_VALUES=0
MAX_ERROR=0
```

## P3 Training10 – technisch grün, visuell weiterhin FAIL

Korrigierter Lauf mit exakt rekonstruierter Architektur:

```text
BEST_EPOCH=105
TRAIN_GAIN_DB=+2.241944
TRAIN_IMPROVED=8/8
VAL_GAIN_DB=+1.596799
VAL_IMPROVED=2/2
RUNTIME_SEC=47.279
PARAMS=1947715
FORWARD=clamp(x+0.2*tanh(raw),0,1)
```

Checkpoint:

`/kaggle/working/HK_NPU_MICRODETAIL_P3_TRAINING10_CORRECTED_20260916/microdetail_p3_training10_corrected.pt`

SHA-256:

`C9A723F96921ADE7788FD30A9740E6DDA73B3AEE7B7D86CBC788013D686022C3`

Visuell:

- Poren verschwinden.
- Bartstoppeln werden geglättet.
- Haare/Haaransatz und Augenbrauen verlieren Struktur.
- Farbdrift/Halos sind nicht das Hauptproblem.

```text
TECH_TRAINING_PASS=YES
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

## Warum das MicroDetail-Training glättet

Antigravity bestätigte:

- Trainingsinput = generativ veränderte FiDeSR-Ausgabe.
- GT = ursprüngliches reales Foto.
- Mikrodetails sind lokal um ca. 1–2 px phasenverschoben oder durch das Diffusions-Prior anders rekonstruiert.
- Pixel-Loss/DoG bestraft vorhandene Details bei Positionsabweichung.
- Das Regressionsminimum wird dadurch Glättung/Mittelwertbildung.

Der getestete Highpass-Residual-Smoke auf `P3T_02_OLD_BEARD115_040` scheiterte ebenfalls:

```text
INPUT_HF=0.011164045
MICRO_HF=0.009376910
GT_HF=0.010903046
HF_TARGET_IMPROVED=NO
```

Dieser Ansatz wurde verworfen.

## P4 Aligned Dataset – Trainingsfehler isoliert bewiesen

Pfad:

`/kaggle/working/MICRODETAIL_P4_ALIGNED10_20260916`

Vertrag:

```text
PAIR_COUNT=10
DETAIL_SIGMA=1.0
DETAIL_KEEP=0.3
PIXEL_ALIGNMENT=BY_CONSTRUCTION
GENERATIVE_FIDESR_INPUT_USED_FOR_TRAINING=NO
```

Kontaktbogen:

`/kaggle/working/MICRODETAIL_P4_ALIGNED10_20260916/P4_ALIGNED10_CONTACT_SHEET.png`

SHA-256:

`E7F24448BE3E52457C63E58B168FB8169E1783B3127ECC185CB572B0AD3C338D`

## P4 Residual Training10 – aligned Qualitäts-PASS

Trainingsziel:

```text
target_residual = GT - ALIGNED_INPUT
pred_residual   = OUTPUT - ALIGNED_INPUT
```

Loss:

```text
residual_L1 + 0.5 * residual_DoG + 0.1 * RGB_L1
```

Ergebnis:

```text
BEST_EPOCH=220
TRAIN_GAIN_DB=+12.317806
TRAIN_IMPROVED=8/8
VAL_GAIN_DB=+10.388018
VAL_IMPROVED=2/2
RUNTIME_SEC=45.401
PARAMS=1947715
```

Checkpoint:

`/kaggle/working/MICRODETAIL_P4_RESIDUAL_TRAINING10_20260916/microdetail_p4_residual_training10.pt`

SHA-256:

`186481878ECBDC7BD70541490D66914379D342922DFC8CEC11CD893D69CF623D`

Visuell auf aligned Inputs:

```text
TECH_TRAINING_PASS=YES
ALIGNED_QUALITY_PASS=YES
```

Bartstoppeln, Poren, Haare und Hautstruktur wurden sauber rekonstruiert.

## P4 auf echten FiDeSR-Inputs – Generalisierung FAIL

Kontaktbogen:

`/kaggle/working/MICRODETAIL_P4_REAL_FIDESR_GATE_20260916/P4_ON_REAL_FIDESR_CONTACT.png`

Ergebnis:

```text
REAL_FIDESR_GENERALIZATION_QUALITY_PASS=NO
```

Beobachtung:

- künstlich gleichmäßige Poren,
- zu harte/dichte Bartstoppeln,
- überschärfte Haare,
- kantige Augenbrauen/Haaransätze,
- leichte Halos,
- Fake-Texture/Sandpapier-Haut,
- geringe Farbdrift.

Damit gilt:

```text
ALIGNED_TRAINING_WORKS=True
REAL_FIDESR_DISTRIBUTION_MATCH=False
```

## FiDeSR-Degradation-Profil und Simulator – verworfen

Antigravity-Profil:

```text
SIGMA_RANGE=0.45..0.80
MEAN_SIGMA≈0.63
HF_RATIO_RANGE=0.99..1.20
MICROCONTRAST_RANGE=0.96..1.41
PHASE_JITTER=0 px global, 1–2 px lokal
NOISE_RATIO=0.36..0.86
COLOR_DRIFT≈0
RESAMPLING=Lanczos/Sinc-Ripples
```

FiDeSR-like-Simulator gegen echte FiDeSR-Ausgaben:

```text
OLD_P4_MEAN_MAE=7.354094
NEW_SIM_MEAN_MAE=7.203319
OLD_P4_HF_ERROR=0.007491800
NEW_SIM_HF_ERROR=0.010700196
OLD_P4_GRAD_ERROR=0.005407569
NEW_SIM_GRAD_ERROR=0.007852549

MAE_IMPROVED=YES
HF_PROFILE_IMPROVED=NO
EDGE_PROFILE_IMPROVED=NO
```

Der Simulator wurde verworfen. Kein weiteres Training darauf.

## Strategiewechsel – MicroDetail-CNN für FiDeSR-Glättung beendet

Der nachgeschaltete MicroDetail-CNN-Pfad wird für dieses Problem nicht weiter verfolgt:

```text
MICRODETAIL_TRAINING_PATH_FOR_FIDESR_SMOOTHING=STOPPED
MICRODETAIL_ONNX_EXPORT=False
MICRODETAIL_QNN_COMPILE=False
```

Grund: authentische Mikrodetails werden vom FiDeSR-UNet generativ verändert; aligned Training funktioniert, generalisiert aber nicht sauber auf echte FiDeSR-Verteilung.

## Durchbruch: deterministischer Detail-Preservation-Bypass

Antigravity untersuchte den echten FiDeSR-Strong-Pfad und bestätigte die Lösung an der Ursache.

```text
UNET_DETAIL_LOSS_CONFIRMED=YES
```

Bypass-Quelle:

`pre-UNet 4x Source (rgb01 / source_hwc)`

Einfügepunkt:

`Pixel-Space Wavelet-Stufe / bestehende Wavelet-Color-Fix CPU-Orchestrierung`

Methode:

```text
DoG Bandpass
sigma1=0.6
sigma2=1.8
Zielband≈1–3 px
adaptive Varianz-Defizit-Steuerung
Makrokanten-Dämpfung
grad_base/0.12 -> starke Konturen erhalten 0% Detailinjektion
nur Y-Luminanz
Cb/Cr bleiben gegenüber FiDeSR Strong unverändert
```

Isolierter Proof:

```text
DETAIL_GAIN=+1.85 dB HF-Energie
SKIN_TEXTURE=WIEDERHERGESTELLT
BEARD_STUBBLE=REKONSTRUIERT
FINE_HAIR=DEUTLICH_VERBESSERT
HALO=KEINE
COLOR_DRIFT=0.000
FAKE_TEXTURE=KEINE
QUALITY_ASSESSMENT=PASS
```

Artefakte:

```text
C:\SnapdragonAI\temp\fidesr_detail_preservation_proof_20260916\A_FIDESR_BASE.png
C:\SnapdragonAI\temp\fidesr_detail_preservation_proof_20260916\B_DETAIL_BYPASS.png
C:\SnapdragonAI\temp\fidesr_detail_preservation_proof_20260916\C_PRESERVED.png
C:\SnapdragonAI\temp\fidesr_detail_preservation_proof_20260916\CONTACT_SHEET.png
```

Wichtig:

- keine zusätzliche KI,
- keine Halluzination,
- echte Quellfrequenzen werden deterministisch erhalten/zurückgeführt,
- AI-Pfad bleibt NPU/QNN/HTP,
- CPU übernimmt nur deterministische Frequenz-/Farbraum-Mathematik.

## Aktuell laufender Integrationssprint beim Arbeitsstopp

Holger lässt am 16. September 2026 noch einen tokenoptimierten Antigravity-Sprint laufen und muss danach zur Arbeit.

Ziel:

`C:\SnapdragonAI\engine\backends\fidesr_strong_runner_template.py`

Nur falls technisch zwingend:

`C:\SnapdragonAI\engine\backends\fidesr_photo_restore_backend.py`

Verbindliche Regeln:

- Proof exakt übernehmen, nicht neu interpretieren.
- Parameter unverändert.
- Source = pre-UNet `rgb01/source_hwc`.
- Injection nach FiDeSR Strong / Wavelet Color Fix im Pixelraum.
- nur Y verändern; Cb/Cr unverändert.
- AI-Pfad `VAE Encoder -> UNet -> LRRB -> VAE Decoder` bleibt QNN/HTP.
- kein Training.
- kein ONNX/QNN-Compile.
- kein Build.
- kein Git.
- keine UI-Änderung.

Geplanter Integrationstest:

```text
INPUT:
C:\Users\holge\Desktop\Testbilder\3.jpg

OUTPUT:
C:\SnapdragonAI\temp\fidesr_detail_preservation_integration_20260916\A_CANONICAL_FIDESR.png
C:\SnapdragonAI\temp\fidesr_detail_preservation_integration_20260916\B_INTEGRATED_PRESERVED.png
C:\SnapdragonAI\temp\fidesr_detail_preservation_integration_20260916\CONTACT_SHEET.png
```

Zum Zeitpunkt dieser Handover-Aktualisierung ist der Sprint noch nicht abgeschlossen.

Daher:

```text
FIDESR_DETAIL_PRESERVATION_INTEGRATION=RUNNING
INTEGRATION_TECH_PASS=UNKNOWN
INTEGRATION_QUALITY_PASS=UNKNOWN
INTEGRATION_PRODUCT_PASS=UNKNOWN
```

## Exakter nächster Einstieg nach Holgers Arbeitspause

1. Abschlussbericht des laufenden Antigravity-Integrationssprints lesen.
2. `C:\SnapdragonAI\temp\fidesr_detail_preservation_integration_20260916\CONTACT_SHEET.png` visuell prüfen.
3. Wenn integrierter Runner denselben Qualitäts-PASS wie der isolierte Proof hält: `TECH_PASS=YES`, `QUALITY_PASS=YES`.
4. Danach echter Studio-Test auf Entwicklungs-PC Holger.
5. Noch kein Build/Installer/Git ohne ausdrückliche Freigabe.
6. Nicht wieder zum MicroDetail-Training zurückkehren, solange keine neue belastbare Evidenz gegen den Preservation-Bypass vorliegt.

## Statusflags – 16. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

FIDESR_STRONG_NPU_TECH_PASS=True
FIDESR_UNET_MAIN_SMOOTHING_CAUSE=True
FIDESR_VAE_MAIN_SMOOTHING_CAUSE=False
FIDESR_LRRB_RESTORES_PARTIAL_DETAIL=True

P2_FORWARD_RECONSTRUCTED_PIXEL_EXACT=True
P2_FORWARD_PARAMS=1947715
P2_FORWARD_RESIDUAL=x+0.2*tanh(raw)

P3_TRAINING10_TECH_PASS=True
P3_TRAINING10_QUALITY_PASS=False

P4_ALIGNED_TRAINING_PASS=True
P4_ALIGNED_QUALITY_PASS=True
P4_REAL_FIDESR_GENERALIZATION_PASS=False

MICRODETAIL_TRAINING_PATH_FOR_FIDESR_SMOOTHING=STOPPED
MICRODETAIL_ONNX_EXPORT=False
MICRODETAIL_QNN_COMPILE=False

FIDESR_DETAIL_PRESERVATION_PROOF=True
FIDESR_DETAIL_PRESERVATION_PROOF_QUALITY=PASS
FIDESR_DETAIL_PRESERVATION_AI_PATH=NPU_QNN_HTP_UNCHANGED
FIDESR_DETAIL_PRESERVATION_CPU_ROLE=DETERMINISTIC_ONLY

FIDESR_DETAIL_PRESERVATION_INTEGRATION=RUNNING
INTEGRATION_TECH_PASS=UNKNOWN
INTEGRATION_QUALITY_PASS=UNKNOWN
INTEGRATION_PRODUCT_PASS=UNKNOWN

BUILD_16_SEPTEMBER=False
INSTALLER_16_SEPTEMBER=False
GIT_ADD_16_SEPTEMBER=False
COMMIT_16_SEPTEMBER=False
PUSH_16_SEPTEMBER=False
```

## Arbeitsstopp 16. September 2026

Holger muss zur Arbeit und stoppt nach Abschluss des bereits laufenden Antigravity-Integrationssprints.

Danach heute keine neuen Trainingsläufe, Kaggle-Sprints, ONNX-/QNN-Compiles, Builds, Installer, Git-Staging-Aktionen, Commits oder Pushes starten.

## Handover-Übernahme

Diese vollständige, nur ergänzte Datei als exakt:

`CHATGPT_HANDOVER.md`

herunterladen.

Danach auf dem Entwicklungs-PC Holger ausführen:

`C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd`

Ziel:

`C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md`

Die Chronik darf niemals gekürzt oder durch eine separate Ergänzungsdatei ersetzt werden.

# CHATGPT_HANDOVER – Nachtrag 16. September 2026 – FiDeSR Detail-Preservation Integration PASS

> Dieser Nachtrag ergänzt den unmittelbar vorhergehenden Stand vom **16. September 2026**.
> Die ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Angaben hat dieser Nachtrag Vorrang.

## Antigravity-Integrationssprint – abgeschlossen

Geändert wurde ausschließlich:

```text
C:\SnapdragonAI\engine\backends\fidesr_strong_runner_template.py
```

Nicht geändert:

- kein Training
- kein ONNX-/QNN-Compile
- kein Build
- kein Installer
- kein Git-Staging
- kein Commit
- kein Push
- keine UI-Änderung

## Integrierter Detail-Preservation-Vertrag

AI-Pfad weiterhin unverändert:

```text
VAE Encoder -> UNet -> LRRB -> VAE Decoder
```

Ausführung:

```text
QNN / HTP / NPU
```

Bestätigt:

```text
AI_PATH_QNN_HTP_UNCHANGED=YES
```

Bypass-Quelle:

```text
pre-UNet 4x Source
source_hwc / rgb01
```

Bandpass:

```text
DoG sigma1=0.6
DoG sigma2=1.8
Zielband: 1–3 px Mikrodetails
```

Kantenschutz:

```text
grad_base / 0.12
adaptive variance deficit
keine Makrokanten-Dopplung
```

Farbraumvertrag:

```text
nur Luminanz Y wird verändert
Cb/Cr bleiben gegenüber FiDeSR Strong erhalten
```

## Reale Integrationsprüfung

Input:

```text
C:\Users\holge\Desktop\Testbilder\3.jpg
```

Output:

```text
C:\SnapdragonAI\temp\fidesr_detail_preservation_integration_20260916\B_INTEGRATED_PRESERVED.png
```

Abmessungen:

```text
672x904
```

Identisch zum FiDeSR-Basisoutput.

Gemeldete Qualitätsmerkmale:

```text
COLOR_DRIFT=NONE
HALO=NONE
SKIN_TEXTURE=PRESERVED
BEARD_STUBBLE=PRESERVED
FINE_HAIR=PRESERVED
FAKE_TEXTURE=NONE
TECH_PASS=YES
QUALITY_PASS=YES
PRODUCT_PASS=YES
```

Zusatzdetail zur Farbe:

```text
mean delta Cb/Cr <= 0.012
nur Quantisierungsrundung
```

## Verbindliche Einordnung

Der deterministische Detail-Preservation-Bypass hat den zuvor bestätigten FiDeSR-Glättungsfehler im Integrationssprint technisch und visuell bestanden, ohne zusätzliche generative KI und ohne Veränderung des NPU-KI-Pfads.

Der vorherige MicroDetail-CNN-Trainingspfad bleibt beendet und wird für dieses Problem nicht wieder aufgenommen.

```text
MICRODETAIL_TRAINING_PATH_FOR_FIDESR_SMOOTHING=STOPPED
FIDESR_DETAIL_PRESERVATION_INTEGRATION=PASS
INTEGRATION_TECH_PASS=YES
INTEGRATION_QUALITY_PASS=YES
INTEGRATION_PRODUCT_PASS=YES
```

## Noch offener letzter Product-Owner-Gate

Trotz Antigravity-Bewertung soll bei Wiederaufnahme zuerst der erzeugte Kontaktbogen von Holger/ChatGPT visuell kontrolliert werden:

```text
C:\SnapdragonAI\temp\fidesr_detail_preservation_integration_20260916\CONTACT_SHEET.png
```

Danach:

1. visueller Product-Owner-Check des Kontaktbogens;
2. echter Studio-Test auf Entwicklungs-PC Holger;
3. nur bei Bestätigung weitere Release-Schritte planen;
4. weiterhin kein Build/Installer/Git ohne ausdrückliche Freigabe.

## Statusflags – finaler Arbeitsstopp 16. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

FIDESR_UNET_MAIN_SMOOTHING_CAUSE=True
FIDESR_DETAIL_PRESERVATION_PROOF=True
FIDESR_DETAIL_PRESERVATION_INTEGRATION=PASS

AI_PATH_QNN_HTP_UNCHANGED=True
BYPASS_SOURCE=PRE_UNET_4X_SOURCE
BANDPASS_DOG_SIGMA1=0.6
BANDPASS_DOG_SIGMA2=1.8
EDGE_SUPPRESSION_GRAD_BASE=0.12
COLOR_INJECTION=Y_ONLY

TECH_PASS=YES
QUALITY_PASS=YES
PRODUCT_PASS=YES

MICRODETAIL_TRAINING_PATH_FOR_FIDESR_SMOOTHING=STOPPED
MICRODETAIL_ONNX_EXPORT=False
MICRODETAIL_QNN_COMPILE=False

BUILD_16_SEPTEMBER=False
INSTALLER_16_SEPTEMBER=False
GIT_ADD_16_SEPTEMBER=False
COMMIT_16_SEPTEMBER=False
PUSH_16_SEPTEMBER=False

NEXT_EXACT_STEP=VISUAL_REVIEW_CONTACT_SHEET_THEN_STUDIO_TEST
```

## Arbeitsstopp

Holger muss zur Arbeit. Nach diesem Stand heute keine weiteren Trainingsläufe, Kaggle-Sprints, ONNX-/QNN-Compiles, Builds, Installer, Git-Staging-Aktionen, Commits oder Pushes starten.


# CHATGPT_HANDOVER – Tagesabschluss 16. September 2026 – Faithful/Enhanced Restoration, generative Qualitätsgates und RealESRGAN-Fine-Tuning-Datensatz

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Angaben hat dieser neueste Abschnitt Vorrang.
> Der zuvor am 16.09.2026 dokumentierte Antigravity-Wert `PRODUCT_PASS=YES` für den FiDeSR-Detail-Preservation-Bypass wurde durch spätere unabhängige visuelle Prüfung **korrigiert**.

## Verbindliche Arbeitsweise

- Sprache: Deutsch.
- Holger möchte keine weiteren langen Blindversuche; drei Wochen Experimentieren ohne belastbares Ergebnis gelten ausdrücklich als Desaster.
- PowerShell bevorzugen, wenn eine Aufgabe lokal eindeutig, lesend oder deterministisch lösbar ist.
- Antigravity für visuelle Klassifizierung, breite Analyse und klar abgegrenzte technische Sprints.
- Codex nur für gezielte Implementierung.
- Für Codex-/Antigravity-Sprints möglichst 5–10 Minuten und tokenoptimiert; breite unklare Aufträge vermeiden.
- Nach jedem Ergebnis direkt mit dem nächsten notwendigen Schritt fortfahren; nicht routinemäßig nachfragen.
- Für technische Sprints sichtbar angeben:
  - `SPRINT-ZEIT`
  - `WORST CASE`
  - `SPEICHER`
  - `HARD STOP`
- Keine Builds, Installer, Git-Staging-Aktionen, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- Untracked/Unrelated-Dateien nicht beiläufig verändern.
- Produktziel bleibt: eigentliche KI-Inferenz nur über Snapdragon NPU / Qualcomm QNN / HTP. CPU nur für deterministische Orchestrierung, I/O, Resize, Masken, Color/Tone und vergleichbare Nicht-KI-Schritte.

## Korrektur: FiDeSR Detail-Preservation ist nicht referenzreif

Der zuvor von Antigravity gemeldete Integrations-PASS wurde unabhängig anhand des erzeugten Kontaktbogens und späterer Studio-Ausgaben strenger bewertet.

Ergebnis:

```text
FIDESR_DETAIL_PRESERVATION_TECH_PASS=YES
FIDESR_DETAIL_PRESERVATION_ARTIFACT_SAFETY_PASS=YES
FIDESR_DETAIL_PRESERVATION_QUALITY_PASS=PARTIAL
FIDESR_DETAIL_PRESERVATION_PRODUCT_PASS=NO
```

Beobachtung:

- keine auffälligen Halos,
- keine relevante Farbdrift,
- kein dominantes Sandpapier-/Fake-Texture-Artefakt,
- leichte Verbesserung an Haaransatz, Augenbraue und Bart,
- Stirn/Wange bleiben jedoch deutlich zu glatt,
- echte Poren/Mikrostruktur werden nicht annähernd auf Referenzniveau rekonstruiert.

Die Antigravity-Aussage `PRODUCT_PASS=YES` aus dem vorherigen Nachtrag ist damit überholt.

## Strength-125-Proof – Wirkung praktisch null

Vergleich:

```text
CURRENT_STRENGTH=0.85
TEST_STRENGTH=1.0625
```

Ergebnis:

```text
SKIN_DETAIL_GAIN=NEGLIGIBLE
BEARD_DETAIL_GAIN=MINIMAL
HAIR_DETAIL_GAIN=MINIMAL
HALO=NONE
FAKE_TEXTURE=NONE
COLOR_DRIFT=NONE
OVER_SHARPEN=NO
TECH_PASS=YES
QUALITY_ASSESSMENT=INSUFFICIENT
```

Root Cause:

```text
deficit = clamp(std_src - std_base)
```

blockiert etwa 93 % der relevanten Hautbereiche, weil `std_base > std_src`.

Ein weiches Makrokanten-Gate wurde als nächster Filtertest diskutiert, aber nach der späteren strategischen Neubewertung nicht als alleinige Referenzlösung weiterverfolgt.

## Harte Grundsatzkorrektur zur Referenzqualität

Mehrere externe Gegenprüfungen (Gemini, Perplexity) und die eigenen Tests führten zur verbindlichen Erkenntnis:

- Ein deterministischer Hochpass-/DoG-Bypass kann nur Detail erhalten oder verstärken, das im Ausgangssignal vorhanden ist.
- Bei sehr kleinen Quellen wie `3.jpg` mit ungefähr `169×226` fehlen viele Referenzdetails physikalisch.
- Fehlende Poren, feine Bartstoppeln und einzelne Körperhaare können dann nur **plausibel synthetisiert**, nicht originalgetreu wiederhergestellt werden.
- RealESRGAN, Diffusion, GFPGAN/CodeFormer usw. sind daher generative Rekonstruktion, keine beweisbare Wiederherstellung des historischen Originals.

Produktseitig wurden deshalb zwei klar getrennte Modi definiert:

```text
FAITHFUL RESTORATION
= möglichst originaltreu, keine bewusst erfundenen Mikrodetails

ENHANCED / GENERATIVE RESTORATION
= sichtbar detailreicher, plausible Rekonstruktion zulässig
```

## SDXL-Inpainting als Microtexture-Restorer – Stop-Gate FAIL

Vorbereitung:

```text
A_FACE_CROP.png / A_FACE_MASK.png
B_HAIR_CROP.png / B_HAIR_MASK.png
C_BODYHAIR_CROP.png / C_BODYHAIR_MASK.png
```

Alle 1024×1024.

Test mit zwei niedrigen Denoising-Stärken / SAFE und STRONGER.

Ergebnis:

```text
A_FACE_PASS=FAIL
B_HAIR_PASS=FAIL
C_BODYHAIR_PASS=FAIL
OVERALL_PASS=NO
```

Details:

- Gesicht: keine Porengewinn; STRONGER verstärkt Glättung/Wachslook.
- Kopfhaar: feine Einzelhaare bleiben weich; STRONGER verklumpt Strähnen.
- Körperhaar: SAFE dünnt Haare leicht aus; STRONGER wirkt als Object Removal und entfernt Haare aktiv.

Entscheidung:

```text
SDXL_INPAINT_MICRODETAIL_PATH=STOPPED
```

Keine weitere Denoising-/Prompt-Parametersuche für diesen Zweck.

## Fertigmodell-Suche – beendet

Es wurden genau definierte Quality Gates gefahren.

### DiffBIR

Hardware:

```text
GPU=NVIDIA Tesla T4 16 GB
FREE_VRAM=14.8 GB
DISK_USED=8.2 GB
```

Ergebnis:

```text
FACE_RESULT=FAIL
HEAD_HAIR_RESULT=FAIL
BODY_HAIR_RESULT=FAIL
IDENTITY_CHANGE=MODERATE_TO_HIGH
GEOMETRY_CHANGE=YES
FAKE_TEXTURE=DOMINANT
REFERENCE_SIMILARITY=LOW
BETTER_THAN_FIDESR_REALESRGAN=NO
QUALITY_GATE=DIFFBIR_FAIL
```

Beobachtungen:

- Fake-Poren / glasierte Haut,
- Gesichtsdrift,
- synthetische Haarcluster,
- wurmartige/ schwarze Fäden bei Körperhaar.

DiffBIR wird nicht weiter verfolgt.

### SUPIR

Resource Gate:

```text
GPU=NVIDIA Tesla T4 16 GB
FREE_VRAM=14.8 GB
DISK_REQUIRED=21.4 GB
SETUP_PASS=NO
QUALITY_GATE=SUPIR_NOT_FEASIBLE
```

Kein Workaround gestartet.

### StableSR

```text
GPU=NVIDIA Tesla T4 16 GB
FREE_VRAM=14.8 GB
DISK_REQUIRED=10.5 GB
SETUP_PASS=YES
```

Ergebnis:

```text
FACE_RESULT=FAIL
HEAD_HAIR_RESULT=FAIL
BODY_HAIR_RESULT=FAIL
IDENTITY_CHANGE=MODERATE
GEOMETRY_CHANGE=YES
FAKE_TEXTURE=DOMINANT
REFERENCE_SIMILARITY=LOW
BETTER_THAN_FIDESR_REALESRGAN=NO
QUALITY_GATE=STABLESR_FAIL
```

Beobachtungen:

- glasierte/überzeichnete Haut,
- Geometriedrift,
- synthetische Strähnencluster,
- wurmartige Körperhaarartefakte.

Entscheidung:

```text
GENERAL_READYMADE_GENERATIVE_MODEL_SEARCH=STOPPED
```

Keine vierte Fertigmodell-Runde starten.

## Faithful Restoration Mode – implementiert

Verbindlicher Produktvertrag:

```text
Input
-> FiDeSR Strong QNN/HTP
-> deterministisches Resize/Tone/Color-Finishing
-> Output
```

RealESRGAN wird im Faithful-Modus **nicht** aufgerufen.

Antigravity-Sprint:

```text
SPRINT=FAITHFUL_RESTORATION_MODE
FIDESR_QNN_HTP=PASS
REALESRGAN_CALLED=NO
CPU_AI_FALLBACK=NO
GPU_AI_FALLBACK=NO
INPUT_OVERWRITTEN=NO
OUTPUT_VALID=YES
TEST_RESULT=PASS
```

Geänderte Dateien:

```text
engine/backends/fidesr_photo_restore_backend.py
controllers/photo_restore_controller.py
widgets/phoenix/views/photo_restore_view.py
engine/backends/photo_restore_backend.py
tests/test_faithful_restoration_mode.py
```

Tests:

```text
4/4 tests in test_faithful_restoration_mode.py
24/24 regression contract tests
```

Kein Build, Commit oder Push.

## Enhanced Restoration Mode – implementiert

Produktvertrag:

```text
Input
-> FiDeSR Strong QNN/HTP
-> RealESRGAN x4 QNN/HTP
-> Lanczos auf finale Zielgröße
-> Output
```

FiDeSR liefert native 4×-Größe; RealESRGAN erzeugt intern raw 16× relativ zum Ursprung; anschließend wird deterministisch mit `Image.Resampling.LANCZOS` auf die gewünschte finale Produktgröße zurückgerechnet.

Ergebnis:

```text
FAITHFUL_UNCHANGED=YES
FIDESR_QNN_HTP=PASS
REALESRGAN_QNN_HTP=PASS
CPU_AI_FALLBACK=NO
GPU_AI_FALLBACK=NO
INPUT_OVERWRITTEN=NO
OUTPUT_VALID=YES
FOCUSED_TESTS=5/5 PASS
REGRESSION_TESTS=24/24 PASS
TECH_PASS=YES
QUALITY_PASS=NOT_EVALUATED
```

Geänderte Dateien:

```text
engine/backends/fidesr_photo_restore_backend.py
widgets/phoenix/views/photo_restore_view.py
tests/test_faithful_restoration_mode.py
```

Kein Build, Commit oder Push.

## Visual Gate Faithful vs Enhanced – unabhängige Abnahme

Testinput:

```text
C:\Users\holge\Desktop\Testbilder\3.jpg
```

Beide Outputs:

```text
672x904
```

Kontaktbogen:

```text
C:\SnapdragonAI\temp\visual_enhanced_restoration_gate_20260916\CONTACT_SHEET.png
```

ChatGPT hat den Kontaktbogen unabhängig geprüft:

```text
FAITHFUL_TECH_PASS=YES
ENHANCED_TECH_PASS=YES

FACE_SKIN:
FAITHFUL=natürlicher, aber weich
ENHANCED=schärfer, weiterhin zu glatt

BEARD:
ENHANCED=BESSER

EYEBROW_HAIRLINE:
ENHANCED=KLAR_BESSER

HEAD_HAIR:
ENHANCED=BESSER

IDENTITY_CHANGE=NO
GEOMETRY_CHANGE=NO
COLOR_DRIFT=NO
HALO_RINGING=NO

FAITHFUL_QUALITY_PASS=YES
ENHANCED_QUALITY_PASS=YES
ENHANCED_REFERENCE_QUALITY=NO
```

Produktentscheidung:

- `Faithful Restoration` bleibt Standard für möglichst natürliche/originaltreue Restaurierung.
- `Enhanced Restoration` bleibt als bewusst wählbare Option für mehr Bart-/Haar-/Kantendetail.
- Enhanced erreicht die scharfe Referenzqualität bei Hautporen/Mikrostruktur **noch nicht**.
- Faithful und Enhanced sollen nicht weiter blind getunt werden.

## RealESRGAN gezielt feintrainieren – Feasibility Gate PASS

Produktmodell:

```text
C:\SnapdragonAI\models\real_esrgan_x4plus.bin
```

Architektur:

```text
RealESRGAN / ESRGAN (RRDBNet)
RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
```

Produktvertrag:

```text
INPUT_SHAPE=(1,128,128,3) NHWC
OUTPUT_SHAPE=(1,512,512,3) NHWC
COLOR_SPACE=RGB
VALUE_RANGE=[0.0,1.0]
DATATYPE=Float32
TILE_SIZE=128
```

Runner:

```text
engine.realesrgan_qnn_runtime
modules.realesrgan_core
```

Ergebnis:

```text
ARCH_MATCH_TRAINABLE=YES
TRAINABLE_CHECKPOINT_TYPE=PyTorch state_dict (params_ema or params)
REPLACEMENT_POSSIBLE_WITHOUT_CODE_CHANGE=YES
FEASIBILITY_GATE=PASS
```

Bedingungen:

```text
identische RRDBNet-Architektur
ONNX export [1,128,128,3] float32
QNN HTP v73
graph=real_esrgan_x4plus
input=image
output=upscaled_image
```

Damit kann ein gezielt feintrainierter architekturidentischer RealESRGAN-Generator grundsätzlich denselben bestehenden Produktpfad verwenden.

## Trainingsstrategie – verbindliche Korrektur gegenüber P2/P3/P4

Nicht mehr:

```text
FiDeSR output -> GT
```

als Trainingspaar verwenden.

Stattdessen:

```text
echtes scharfes HR-Foto
-> realistische synthetische Degradation / Downsample
-> LR-Input

HR bleibt Ground Truth
```

Dadurch ist LR/HR pixelgenau ausgerichtet.

Zielklassen:

1. Gesichtshaut / Poren
2. Bartstoppeln
3. Augenbrauen
4. Kopfhaar / Einzelsträhnen
5. Körperbehaarung auf Haut
6. Kleidung / Hintergrundtexturen

Keine AI-generierten/restaurierten Bilder als HR Ground Truth.

## Lokales Datensatz-Inventar – PowerShell PASS

Suchwurzeln:

```text
C:\SnapdragonAI\temp
C:\Users\holge\Desktop\Testbilder
```

Erstes Inventar:

```text
TOTAL_IMAGES=3234
HIRES_1024_PLUS=758
```

CSV:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_dataset_gate_20260916\IMAGE_INVENTORY.csv
```

SHA256-Deduplizierung:

```text
HIRES_RAW=758
HIRES_UNIQUE=404
DUPLICATE_ALIASES_REMOVED=354
```

Hints:

```text
FACE_HINTS=62
BEARD_HINTS=1
HEAD_HAIR_HINTS=40
BODY_HAIR_HINTS=10
BACKGROUND_HINTS=69
UNCLASSIFIED=230
```

CSVs:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_dataset_gate_20260916\HIRES_HASHED_ALL.csv
C:\SnapdragonAI\temp\realesrgan_microdetail_dataset_gate_20260916\HIRES_UNIQUE.csv
```

Wichtige Einordnung:

- Die BODY_HAIR-Hints enthalten auch ungeeignete Derivate wie StableSR-/DiffBIR-/SDXL-Ausgaben und Masken.
- Dateinamen reichen daher nicht.
- Die 230 unklassifizierten Bilder müssen visuell mitbetrachtet werden.
- Megapixelanzeige im PowerShell-Output war wegen deutscher Dezimaldarstellung optisch irreführend (`308` bedeutet z.B. ungefähr `3,08 MP`); dies betrifft nur die Anzeige, nicht die Bildabmessungen.

## Aktuell laufender Sprint bei Feierabend: visuelles HR-GT-Dataset-Gate

Antigravity-Sprint:

```text
SPRINT=REALESRGAN_MICRODETAIL_VISUAL_DATASET_GATE
```

Harte Mindestziele:

```text
FACE_SKIN_BEARD >= 8
EYEBROW_HEAD_HAIR >= 5
BODY_HAIR >= 8
CLOTHING_BACKGROUND >= 5
```

Body Hair ist das kritische Gate.

Antigravity prüft aktuell insbesondere:

```text
C:\SnapdragonAI\temp\microdetail_final_gt_gate\
C:\SnapdragonAI\temp\microdetail_bodyhair_grid_review\
C:\SnapdragonAI\temp\pd12m_photo_subset_repaired\images\
C:\SnapdragonAI\temp\pd12m_historical_clean_subset_proof\images\
C:\SnapdragonAI\temp\pd12m_sample_audit\images\
C:\Users\holge\Desktop\Testbilder\
```

und relevante `UNCLASSIFIED`-Kandidaten aus `HIRES_UNIQUE.csv`.

Bereits im laufenden visuellen Review erkannt:

- einige Body-Hair-Quellen zeigen brauchbare echte Haare,
- einige Kandidaten sind zu weich oder ungeeignet,
- `BODYHAIR_GRID_0011.png` wurde wegen Wasserzeichen/Qualität abgelehnt,
- `C_BODYHAIR_CROP.png` ist ein degradierter/abgeleiteter Testcrop und kein GT,
- `stagea_01_leg_crop.png` zeigt Hinweise auf AI-Upscaling/abgeleitete Bearbeitung und darf nicht als echte HR-GT übernommen werden,
- vorhandene StableSR-/DiffBIR-/SDXL-Ausgaben, Masken, Contact Sheets, Vergleichsgrids und sonstige Derivate müssen verworfen werden.

Zum Zeitpunkt des Feierabends läuft dieser Sprint noch.

Daher:

```text
VISUAL_DATASET_CLASSIFICATION=RUNNING
DATASET_GATE=PENDING
TRAINING_STARTED=NO
```

## Verbindlicher nächster Einstieg

Morgen zuerst **nur den Abschlussbericht des bereits laufenden Antigravity-Sprints lesen**.

Gesuchte Werte:

```text
FACE_SKIN_BEARD_USABLE=
EYEBROW_HEAD_HAIR_USABLE=
BODY_HAIR_USABLE=
CLOTHING_BACKGROUND_USABLE=
ACCEPTED_TOTAL=
DATASET_GATE=
MISSING_CATEGORY=
NEXT_EXACT_STEP=
```

Entscheidungsregel:

- Wenn `BODY_HAIR_USABLE < 8` oder eine andere Mindestkategorie scheitert: **kein Training starten**. Gezielt echte HR-Quellen beschaffen/auswählen.
- Wenn `DATASET_GATE=PASS`: erst dann den kleinen Proof-Datensatz bauen und genau **einen** architekturidentischen RRDBNet-Fine-Tune-Proof aufsetzen.
- Kein Training mit FiDeSR-Outputs als Input.
- Kein QNN/ONNX-Export vor sichtbarem Qualitäts-PASS des Fine-Tune-Proofs.
- Faithful und Enhanced bleiben unverändert.

## Git-/Build-Status am Feierabend 16. September 2026

```text
BUILD_16_SEPTEMBER=False
INSTALLER_16_SEPTEMBER=False
GIT_ADD_16_SEPTEMBER=False
COMMIT_16_SEPTEMBER=False
PUSH_16_SEPTEMBER=False
```

Es existieren lokale getrackte Änderungen aus Faithful/Enhanced/FiDeSR-Integrationsarbeiten. Diese morgen nicht blind committen oder verwerfen.

## Feierabend 16. September 2026

Holger beendet für heute die Arbeit, während der visuelle Dataset-Gate-Sprint noch läuft.

Heute keine weiteren Trainingsläufe, Kaggle-Sprints, Modell-Downloads, ONNX-/QNN-Compiles, Builds, Installer, Git-Staging-Aktionen, Commits oder Pushes starten.

Morgen direkt beim Ergebnis von `REALESRGAN_MICRODETAIL_VISUAL_DATASET_GATE` fortsetzen.

## Handover-Übernahme

Diese vollständige Datei muss exakt heißen:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie anschließend ausschließlich über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die gesamte ältere Chronik muss vollständig erhalten bleiben; diese Datei ist nur ergänzt und im Kopfdatum auf den 16. September 2026 korrigiert.


# CHATGPT_HANDOVER – Ergänzung 17. September 2026 – RealESRGAN-Microdetail-Dataset, Fine-Tune-Proofs und finale Qualitätsentscheidung

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt vollständig erhalten. Bei widersprüchlichen Statusangaben hat dieser neueste Abschnitt Vorrang.

## Arbeitsregeln – weiterhin verbindlich

- Sprache mit Holger: Deutsch.
- Nach jedem Prüfergebnis direkt den nächsten sinnvollen Schritt liefern; keine unnötigen Rückfragen.
- PowerShell bevorzugen, wenn lokal deterministisch möglich.
- Kaggle: ausschließlich Python, niemals PowerShell.
- Codex/Antigravity nur für eng abgegrenzte Sprints; tokenoptimiert.
- Vor jedem technischen Sprint sichtbar angeben: `SPRINT-ZEIT`, `WORST CASE`, `SPEICHER`, `HARD STOP`.
- Keine Builds, Installer, `git add`, Commits oder Pushes ohne ausdrückliche Freigabe.
- Niemals `git add .`.
- Produkt-KI bleibt NPU/QNN/HTP-only; CPU nur Orchestrierung, I/O, Resize, Masken und deterministische Mathematik.
- `TECH_PASS`, `QUALITY_PASS` und `PRODUCT_PASS` strikt trennen.
- Kein ONNX/QNN-Port eines Fine-Tune-Modells vor sichtbarem Qualitäts-PASS.

## 1. Visuelles HR-GT-Dataset-Gate abgeschlossen – PASS

Der am 16. September laufende Sprint wurde abgeschlossen.

Finaler Bericht:

```text
SPRINT=REALESRGAN_MICRODETAIL_VISUAL_DATASET_GATE
UNIQUE_IMAGES_REVIEWED=404
FACE_SKIN_BEARD_USABLE=10
EYEBROW_HEAD_HAIR_USABLE=8
BODY_HAIR_USABLE=10
CLOTHING_BACKGROUND_USABLE=7
BODY_HAIR_HARD_GATE=PASS
FACE_HARD_GATE=PASS
HAIR_HARD_GATE=PASS
BACKGROUND_HARD_GATE=PASS
DERIVED_IMAGES_REJECTED=78
MASKS_COMPOSITES_REJECTED=46
REAL_PHOTO_GT_ONLY=YES
ACCEPTED_TOTAL=35
DATASET_GATE=PASS
MISSING_CATEGORY=NONE
```

Bericht:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_dataset_gate_20260916\VISUAL_DATASET_GATE.txt
```

Kontaktbogen:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_dataset_gate_20260916\ACCEPTED_CANDIDATES_CONTACT_SHEET.png
```

Wichtige Konsequenz:

- 35 echte fotografische HR-GT-Quellen/Crops wurden freigegeben.
- Keine AI-restaurierten, hochskalierten, generierten, Grid-/Masken-/Composite-Bilder als GT.
- Body-Hair-Hard-Gate wurde mit 10 geeigneten Beispielen bestanden.

## 2. Pixelgenauer LR/HR-Pairset V1 erstellt

Lokaler Pairset-Ordner:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_pairs_v1_20260917
```

Finale Zusammenfassung:

```text
ACCEPTED_HR_RECORDS=35
UNIQUE_SOURCE_GROUPS=27
TRAIN_HR_RECORDS=27
VAL_HR_RECORDS=8
DEGRADATION_VARIANTS_PER_HR=3
TOTAL_LR_PAIRS=105
SCALE=4
HR_GT_COPIED=NO
HR_GT_MODIFIED=NO
AI_DEGRADATION_USED=NO
TRAIN_VAL_SOURCE_LEAKAGE=NO

BODY_HAIR_TRAIN=8
BODY_HAIR_VAL=2
CLOTHING_BACKGROUND_TRAIN=5
CLOTHING_BACKGROUND_VAL=2
EYEBROW_HEAD_HAIR_TRAIN=6
EYEBROW_HEAD_HAIR_VAL=2
FACE_SKIN_BEARD_TRAIN=8
FACE_SKIN_BEARD_VAL=2
```

Wichtiger Split-Vertrag:

- Train/Validation werden nach tatsächlicher Ursprungsquelle gruppiert.
- Mehrere Crops derselben Quelle dürfen nie in unterschiedlichen Splits landen.
- `TRAIN_VAL_SOURCE_LEAKAGE=NO` wurde separat geprüft.

Drei deterministische Degradationsstufen:

```text
D1 = mild
D2 = mittel
D3 = stärker
```

## 3. Pairset Visual Alignment Gate – PASS

Antigravity prüfte 12 Quellen aus allen Zielkategorien.

Final:

```text
SPRINT=PAIRSET_VISUAL_ALIGNMENT_GATE
SOURCES_REVIEWED=12
PIXEL_ALIGNMENT=PASS
D1_REALISM=PASS
D2_REALISM=PASS
D3_REALISM=PASS
BODY_HAIR_PROGRESSIVE_DEGRADATION=PASS
FACE_BEARD_PROGRESSIVE_DEGRADATION=PASS
HEAD_HAIR_PROGRESSIVE_DEGRADATION=PASS
CLOTHING_PROGRESSIVE_DEGRADATION=PASS
VAL_SOURCE_INDEPENDENCE=PASS
MOIRE=NONE
RINGING=NONE
JPEG_OVERDAMAGE=NONE
NOISE_OVERDAMAGE=NONE
ARTIFICIAL_BLUR=NONE
PAIRSET_VISUAL_GATE=PASS
FILES_CHANGED=NO
```

Kontaktbogen:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_pairs_v1_20260917\PAIRSET_VISUAL_GATE.png
```

## 4. Selbstständiges Kaggle-Paket erstellt – PASS

Lokaler Paketordner:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_kaggle_v1_20260917
```

ZIP:

```text
C:\SnapdragonAI\temp\realesrgan_microdetail_kaggle_v1_20260917.zip
```

Finale Paketwerte:

```text
KAGGLE_PACKAGE_BUILD=PASS
ZIP_BYTES=268948132
ZIP_MB=256.49
ZIP_SHA256=8B39082DA5A61B0E7263E04C5FB394492F7C72FF1AF2CE7DBEB668F844F3923D
HR_RECORDS=35
LR_PAIRS=105
TRAIN_PAIRS=81
VAL_PAIRS=24
UNIQUE_SOURCE_GROUPS=27
TRAIN_VAL_SOURCE_LEAKAGE=NO
ZIP_POSIX_PATHS=PASS
ZIP_CRC=PASS
```

Kaggle mountete den Datensatz als bereits expandierten Dataset-Input:

```text
/kaggle/input/datasets/hknpustudio/microdetail-kaggle-v1
```

Dataset-Validierung auf Kaggle:

```text
DATASET_VALIDATION=PASS
TRAIN_PAIRS=81
VAL_PAIRS=24
SOURCE_GROUPS=27
TRAIN_VAL_SOURCE_LEAKAGE=NO
```

## 5. Kaggle-/BasicSR-Kompatibilitätsfix

Kaggle-Umgebung:

```text
PYTHON=3.12.13
TORCH=2.10.0+cu128
TORCHVISION=0.25.0+cu128
GPU=Tesla T4
GPU_VRAM_GB=14.56
```

BasicSR 1.4.2 importierte noch:

```text
torchvision.transforms.functional_tensor
```

Dieses Modul existiert in der verwendeten aktuellen Torchvision-Version nicht mehr.

Kaggle-only Kompatibilitätspatch:

```text
/usr/local/lib/python3.12/dist-packages/basicsr/data/degradations.py
```

Fallback auf:

```python
from torchvision.transforms.functional import rgb_to_grayscale
```

Resultat:

```text
PATCH_APPLIED=YES
RRDBNET_IMPORT=PASS
RRDBNET_INSTANTIATION=PASS
RRDBNET_PARAM_COUNT=16697987
```

Dieser Patch betrifft nur die Kaggle-Trainingsumgebung, nicht das Produktrepo.

## 6. Offizieller RealESRGAN-x4plus-Checkpoint – korrigierter Download

Ein zunächst verwendeter GitHub-Release-Link unter `v0.2.5.0` war falsch und lieferte HTTP 404.

Korrigierter offizieller Download:

```text
https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
```

Checkpoint auf Kaggle:

```text
/kaggle/working/HK_NPU_REALESRGAN_MICRODETAIL_PROOF_V1/RealESRGAN_x4plus.pth
```

Verifiziert:

```text
PRETRAIN_BYTES=67040989
PRETRAIN_SHA256=4FA0D38905F75AC06EB49A7951B426670021BE3018265FD191D2125DF9D682F1
CHECKPOINT_SOURCE=params_ema
ARCH_COMPATIBILITY=PASS
RRDBNET_PARAM_COUNT=16697987
TRAINING_STARTED=NO
```

Architektur:

```text
RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
```

## 7. Fine-Tune-Proof V1 – numerisch stark, visuell FAIL

Wegen einiger 256×256-HR-GT-Crops wurde für das Training korrekt auf folgenden Patchvertrag gewechselt:

```text
LR 64×64 -> HR 256×256
```

Die RRDBNet-Architektur blieb vollständig convolutional und damit weiterhin kompatibel zum späteren Produktvertrag:

```text
128×128 -> 512×512
```

V1 Training:

```text
ACTUAL_STEPS=2500
BEST_STEP=1000
EARLY_STOP=YES
EARLY_STOP_REASON=NO_VALIDATION_IMPROVEMENT
BASELINE_VAL_L1=0.028582548800234992
BEST_VAL_L1=0.018806724246436108
VAL_L1_IMPROVEMENT_PERCENT=34.2020742171129
BASELINE_VAL_GRAD=0.03888432223660251
BEST_VAL_GRAD=0.029935824451968074
```

Best-Checkpoint:

```text
/kaggle/working/HK_NPU_REALESRGAN_MICRODETAIL_PROOF_V1/microdetail_rrdbnet_proof_best.pth
SHA256=06F36EEFA0E9863CF6377A3E80FFE753455990C284BBBAA50C1E62D44CE0A634
```

Visual-Gate:

```text
/kaggle/working/HK_NPU_REALESRGAN_MICRODETAIL_PROOF_V1/RRDBNET_FINETUNE_VISUAL_GATE.png
```

Der erste Visual-Gate-Code verlangte fälschlich 8 unabhängige Validation-Source-Groups. Tatsächlich stehen 6 unabhängige Validation-Groups zur Verfügung. Training und Best-Checkpoint waren davon nicht betroffen. Ein Recovery-Gate erzeugte den Kontaktbogen ohne neues Training.

Unabhängige visuelle Bewertung:

```text
TECH_PASS=YES
NUMERIC_PASS=YES
QUALITY_PASS=NO
PRODUCT_PASS=NO
ONNX_QNN=STOP
```

Beobachtungen:

- Fine-tuned V1 glättete Körperhaare stärker weg.
- Gesicht/Bart wurden weicher und wachsiger.
- Kopfhaarsträhnen verschmolzen stärker.
- Textilien verloren feine Konturen.
- 34,2 % bessere L1-Metrik entsprach keinem sichtbaren Mikrodetaillierungsgewinn.

Entscheidung:

```text
V1_FINE_TUNE_REJECTED_FOR_PRODUCT=YES
```

## 8. Letzter Loss-korrigierter Fine-Tune-Proof V2

Um zu prüfen, ob der Fehler primär aus der Zielfunktion kam, wurde genau ein letzter kurzer Proof durchgeführt.

Unverändert:

- gleicher Datensatz;
- gleicher Train/Val-Split;
- gleiche RRDBNet-Architektur;
- kein GAN;
- kein ONNX/QNN;
- maximal 1000 Steps.

Loss-Gewichtung:

```text
PIXEL_WEIGHT=0.35
GRAD_WEIGHT=0.35
LAPLACIAN_WEIGHT=0.20
PERCEPTUAL_WEIGHT=0.10
```

Perceptual Feature Network:

```text
VGG19 ImageNet features[:18]
```

V2 Trainingsergebnis:

```text
ACTUAL_STEPS=1000
BEST_STEP=750
BASELINE_VAL_L1=0.028582548800234992
BASELINE_VAL_GRAD=0.03888432223660251
BASELINE_VAL_LAPLACIAN=0.04535704432055354
BEST_VAL_L1=0.02095361042302102
BEST_VAL_GRAD=0.031013029705112178
BEST_VAL_LAPLACIAN=0.035715145796226956
RUNTIME_MINUTES=8.186294603347779
BEST_CHECKPOINT_SHA256=9304ADCA473FC8515CBFE63F731F982033DD5AB6C06767A8A3A99B15439CEBC1
```

Kontaktbogen:

```text
/kaggle/working/HK_NPU_REALESRGAN_MICRODETAIL_LOSS_PROOF_V2/RRDBNET_LOSSPROOF_VISUAL_GATE.png
```

Best-Checkpoint:

```text
/kaggle/working/HK_NPU_REALESRGAN_MICRODETAIL_LOSS_PROOF_V2/microdetail_rrdbnet_lossproof_best.pth
```

Technisch:

```text
TECH_PASS=YES
GAN=NO
ONNX_QNN=NO
```

## 9. Finale visuelle Entscheidung V2 – FAIL

Der V2-Kontaktbogen wurde unabhängig direkt verglichen:

```text
LR Bicubic
Original RealESRGAN
Loss-Proof RRDBNet
HR Ground Truth
```

Finale Bewertung:

```text
QUALITY_PASS=NO
PRODUCT_PASS=NO
BEST_OF_TWO=ORIGINAL_REALESRGAN
LOSS_PROOF_V2=REJECT_FOR_PRODUCT
ONNX_QNN=STOP
```

Bereichsweise:

- Körperhaar: kein überzeugender Gewinn; einzelne Haare im Loss-Proof eher weicher.
- Gesicht/Haut/Bart: Poren und Stoppeln bleiben zu weich, kein Durchbruch Richtung GT.
- Kopfhaar: Haartrennung nicht verbessert, eher diffuser.
- Textilien: feine Konturen/Gewebestruktur werden geglättet.
- Gesamt: Numerische Verbesserung korreliert erneut nicht mit sichtbarem Mikrodetaillierungsgewinn.

Damit ist der aktuelle Custom-RRDBNet-Fine-Tuning-Pfad **nicht produktreif**.

## 10. Verbindliche Entscheidung zum Fine-Tuning-Pfad

Nicht tun:

- V1 oder V2 nach ONNX exportieren;
- V1 oder V2 nach QNN/HTP portieren;
- weitere blinde Loss-/Hyperparameter-Versuche starten;
- die numerischen Val-Metriken als Qualitäts-PASS auslegen.

Aktueller Vergleich:

```text
ORIGINAL_REALESRGAN > V1_FINE_TUNE
ORIGINAL_REALESRGAN > V2_LOSS_PROOF
```

Der produktive RealESRGAN-Basispfad bleibt deshalb unverändert das vorhandene originale RealESRGAN-QNN-Modell.

Produktiver Modellvertrag bleibt:

```text
C:\SnapdragonAI\models\real_esrgan_x4plus.bin
```

Bekannter Modellhash:

```text
AB62398BF9CA61209E4DAB5EB5776F032760B777A759663CD67C14CFFF12E525
```

## 11. Aktueller Produktstatus Photo Restore

Weiterhin gültig:

### Faithful Restoration

```text
Input
-> FiDeSR Strong QNN/HTP
-> deterministische Resize/Tone/Color-Finishing-Schritte
-> Output
```

Kein RealESRGAN im Faithful-Modus.

### Enhanced Restoration

```text
Input
-> FiDeSR Strong QNN/HTP
-> Original RealESRGAN x4 QNN/HTP
-> deterministisches Lanczos-Finishing
-> Output
```

Der vorhandene originale RealESRGAN-Pfad bleibt der aktuell beste produktive Upscaling-/Schärfungsbaustein.

Bekannter visueller Stand:

- Enhanced ist schärfer als Faithful;
- Bart, Augenbrauen/Haarlinie und Kopfhaar profitieren;
- Haut/Poren bleiben jedoch deutlich unter der scharfen Referenzqualität;
- `ENHANCED_REFERENCE_QUALITY=NO`.

Die Custom-Fine-Tune-Proofs vom 17. September verbessern diesen Punkt nicht.

## 12. Artefakte, die NICHT produktiv portiert werden dürfen

V1:

```text
microdetail_rrdbnet_proof_best.pth
SHA256=06F36EEFA0E9863CF6377A3E80FFE753455990C284BBBAA50C1E62D44CE0A634
```

V2:

```text
microdetail_rrdbnet_lossproof_best.pth
SHA256=9304ADCA473FC8515CBFE63F731F982033DD5AB6C06767A8A3A99B15439CEBC1
```

Beide sind Forschungsartefakte mit `QUALITY_PASS=NO`.

## 13. Git-/Build-Status 17. September 2026

Für die heutigen Dataset-/Kaggle-/Training-Proofs wurden keine Produkt-Builds oder Git-Schritte durchgeführt.

```text
BUILD_17_SEPTEMBER=False
INSTALLER_17_SEPTEMBER=False
GIT_ADD_17_SEPTEMBER=False
COMMIT_17_SEPTEMBER=False
PUSH_17_SEPTEMBER=False
```

Lokale bereits vorhandene Faithful-/Enhanced-/FiDeSR-Integrationsänderungen weiterhin nicht blind committen oder verwerfen.

## 14. Verbindlicher nächster Einstieg

Der RRDBNet-Custom-Fine-Tune-Pfad ist für jetzt beendet.

Bei Wiederaufnahme nicht erneut mit V1/V2 weitertrainieren und nicht zu ONNX/QNN gehen.

Sicherer nächster Schritt:

1. bestehenden Original-RealESRGAN-Produktpfad unverändert lassen;
2. Faithful/Enhanced ebenfalls unverändert lassen;
3. falls Mikrodetaillierung weiter verfolgt wird, zuerst eine **neue methodische Strategie** definieren, die sichtbaren Haar-/Poren-Gewinn explizit als primären Gate hat;
4. keine weitere Architektur-/Loss-Iteration allein aufgrund besserer L1-/Gradient-/Laplacian-Werte;
5. neue Strategie muss auf held-out Realbild-Gates Körperhaar, Bart, Kopfhaar und Haut sichtbar besser als Original-RealESRGAN sein, bevor irgendeine NPU-Portierung beginnt.

Bis zu dieser neuen Strategie gilt:

```text
CUSTOM_REALESRGAN_FINETUNE_PATH=STOPPED
ORIGINAL_REALESRGAN_PRODUCT_BASELINE=KEEP
V1_ONNX_QNN=NO
V2_ONNX_QNN=NO
NEXT_EXACT_STEP=DEFINE_NEW_MICRODETAIL_STRATEGY_OR_KEEP_CURRENT_PRODUCT_PATH
```

## Handover-Übernahme

Diese vollständige Datei muss exakt heißen:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie anschließend ausschließlich über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die gesamte ältere Chronik muss vollständig erhalten bleiben. Diese Aktualisierung ergänzt nur den 17.-September-Stand und korrigiert das Kopfdatum auf den 17. September 2026.


# CHATGPT_HANDOVER – Ergänzung später 17. September 2026 – HAT/VOSR/OSDFace-Gates, Codex-Gesamtvergleich und Flow-NPU-Machbarkeit

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neuere Abschnitt Vorrang.

## Arbeitsmodus / neue harte Regeln

- Sprache weiterhin Deutsch.
- Holger möchte technische Sprints konsequent tokenoptimiert.
- Vor jedem technischen Sprint sichtbar angeben: `SPRINT-ZEIT`, `WORST CASE`, `SPEICHER`, `HARD STOP`.
- PowerShell bevorzugen, wenn eine lokale Prüfung eindeutig und klein ist.
- Antigravity verwenden, wenn Analyse lokaler SDK-/Runtime-Strukturen breiter wird oder PowerShell unnötig iterativ würde.
- Codex wegen Tokenverbrauch nur noch für klar notwendige, eng begrenzte Implementierung/Analyse verwenden. Der letzte große Codex-Gesamtvergleich verbrauchte ca. 60 % des Tokenbudgets; danach standen nur noch ca. 22 % zur Verfügung.
- Nach einem ausgewerteten Ergebnis ohne unnötige Rückfrage direkt den nächsten notwendigen Schritt geben.
- PowerShell-/Kaggle-Code immer vollständig liefern.
- Kaggle = ausschließlich Python; Windows lokal = PowerShell.
- Keine Builds, Commits, Pushes, Installationen oder produktiven Änderungen ohne klare Freigabe.
- Niemals `git add .`.
- TECH PASS, QUALITY PASS und PRODUCT PASS strikt trennen.
- Für HK NPU STUDIO bleibt verbindlich: produktive KI-Inferenz ausschließlich über Snapdragon NPU / QNN / HTP. CPU nur für I/O, Scheduler, Resize, Masken, Compositing und andere deterministische Hilfslogik.

## Ausgangslage Photo Restore / Microdetail

Aktuell bestätigte Produktbasis bleibt:

### Faithful

```text
Input
-> FiDeSR Strong QNN/HTP
-> deterministische Resize/Tone/Color-Finishing-Schritte
-> Output
```

### Enhanced

```text
Input
-> FiDeSR Strong QNN/HTP
-> Original RealESRGAN x4 QNN/HTP
-> deterministisches Lanczos-Finishing
-> Output
```

Bekannte Qualitätsgrenze:

- Haare, Bart, Augenbrauen und textile Kanten werden gegenüber Faithful schärfer.
- Hautporen und sehr feine Haar-/Körperhaar-Mikrostruktur bleiben deutlich unter Referenzqualität.
- `ENHANCED_REFERENCE_QUALITY=NO`.

Produktives RealESRGAN-Modell bleibt unverändert:

```text
C:\SnapdragonAI\models\real_esrgan_x4plus.bin
SHA256=AB62398BF9CA61209E4DAB5EB5776F032760B777A759663CD67C14CFFF12E525
```

## HAT / Real-HAT – abgeschlossen, kein Produktpfad

Offizieller HAT-Pfad wurde auf Kaggle geprüft.

Repository:

```text
https://github.com/XPixelGroup/HAT
```

Offizielle Modelle:

```text
Real_HAT_GAN_SRx4.pth
SHA256=F5B1E3BBBB05147CA2BEEFCC715279CB647D7976CBDA67D62EA7E6E20D5FFCC7

Real_HAT_GAN_sharper.pth
SHA256=5800B67136006EB8CAB3B4ED7C8D73B6A195BB18E6CC709B674F9AA069C00271
```

Architektur-Load und FP32-Inferenz bestanden. FP16-Autocast erzeugte NaNs und wurde verworfen.

Der synthetische D2-Vergleich sah für HAT Sharper zunächst gut aus; im realen Produktketten-Gate auf FiDeSR brachte HAT aber keinen robusten Gewinn bei menschlicher Mikrostruktur.

Final:

```text
HAT_REAL_CHAIN_QUALITY_PASS=NO
PRODUCT_PASS=NO
PRODUCT_CANDIDATE=ORIGINAL_REALESRGAN
ONNX_QNN_GATE=STOP
```

HAT war auf Textilien teilweise natürlicher und reduzierte bestimmte linienartige/holzartige Artefakte, löste aber das zentrale Poren-/Haarproblem nicht.

## VOSR 0.5B One-Step – TECH PASS, QUALITY FAIL

Offizieller Pfad:

```text
Repo: https://github.com/cswry/VOSR
HF: CSWRY/VOSR
```

Gezielt heruntergeladene Kernartefakte:

```text
VOSR_0.5B_os/checkpoints/ema_model.safetensors
SIZE=1948337520 Bytes

sd21_lwdecoder.pth
SIZE=52086482 Bytes
```

Ein erster Versuch lief wegen VAE-Vollbild-Encoding bei 2688×3616 in T4-OOM.

Recovery mit offiziellen Tile-Parametern:

```text
--vae_tile_size 1024
--tile_size 512
--vae_tile_overlap 64
--posterior_mode
--force_rerun
```

Ergebnis:

```text
INPUT=672x904
OUTPUT=2688x3616
RUNTIME_SECONDS≈77.71
TECH_PASS=YES
```

Visuell:

- Kopfhaar, Bart und Materialmikrostruktur besser als RealESRGAN/HAT.
- Haut deutlich zu glatt/wachsig, praktisch poreless.

Final:

```text
VOSR_REAL_CHAIN_QUALITY_PASS=NO
REASON=SKIN_TOO_SMOOTH
MICRODETAIL_GOAL=NOT_REACHED
PRODUCT_PASS=NO
QNN_NPU_FEASIBILITY_GATE=STOP
```

Keine NPU-Portierung.

## OSDFace – direkter und FiDeSR-basierter Qualitätsgate

Offizieller Pfad:

```text
https://github.com/jkwang28/OSDFace
```

OSDFace-Pretrained-Artefakte:

```text
associate_2.ckpt
SIZE=1874023023
SHA256=D51FF7F0DDB0BD84B20B75B261EF01618CA6C3FDED63F7B612BE9E2D38257B23

embedding_change_weights.pth
SIZE=1580312
SHA256=3B13AB83FED678ED15CDC5ACDF36A948630EA197A0D3BFCD693C040DD4D59876

pytorch_lora_weights.safetensors
SIZE=67853416
SHA256=BF7095B4D79F3E991EB6B27774E44E23CBEE73998E1E5AFA0BFAB5E8CB9C834E
```

### OSDFace auf FiDeSR

Technischer Lauf erfolgreich:

```text
TECH_PASS=YES
OUTPUT=512x512
```

Qualität:

- Haare, Haarlinie, Augenbrauen, Bart/Stoppeln deutlich stärker ausgeprägt.
- Stirn und Wangen weiterhin sehr glatt/poreless.
- sichtbar stärker gezeichnet/kontrastiert.
- Halluzinationsrisiko bei Haar-/Bartdetails.

Zwischenfazit:

```text
FIDESR_TO_OSDFACE_QUALITY_PASS=NO
```

Wichtig: Dieser Test allein war nicht fair genug, weil FiDeSR bereits Hautdetails glättet.

### Direkter OSDFace-Test auf drei Originalbildern

Kaggle-Dataset:

```text
/kaggle/input/datasets/hknpustudio/testbilder1-3
```

Originale:

```text
Bild1.jpg
SIZE=169x226
SHA256=657B2B621F8A88AFC7D6818E5BD217F135E7147B27F327CC4B92D72534AD7EC7

Bild2.jpg
SIZE=362x650
SHA256=638EAF1A5DCA99014706C58E3B05FBBD00BB5B95C15DC1CEF040F5369818C379

Bild3.jpg
SIZE=500x179
SHA256=1B4F61215891EAC863CC69806A10E5A9E69330E7B71ECB2716F4266605AD3275
```

Direkter Vergleich `Original -> OSDFace` zeigte:

- Bild1: Haare/Bart/Konturen stärker, aber Gesicht sichtbar illustrativ/gezeichnet.
- Bild2/Bild3: hauptsächlich mehr lokale Schärfe/Kontrast; keine überzeugende neue Körperbehaarung.
- Haut weiterhin glatt; fehlende Poren werden nicht überzeugend rekonstruiert.

Final:

```text
OSDFACE_DIRECT_ORIGINAL_QUALITY_PASS=NO
FACE_IDENTITY=PARTIAL
FACE_HAIR_DETAIL=IMPROVED_BUT_SYNTHETIC
SKIN_PORES=NO
BODY_HAIR=NO_MEANINGFUL_GAIN
NATURALNESS=NO
OVER_SHARPENING=YES
ILLUSTRATIVE_LOOK=YES
HALLUCINATION_RISK=MEDIUM_HIGH
WHOLE_PERSON_SOLUTION=NO
PRODUCT_PASS=NO
QNN_PORTING=STOP
```

OSDFace wird nicht als globale Produktlösung verfolgt.

## Codex-Gesamtvergleich – visueller Inventar-Review

Holgers relevante Ergebnisbilder liegen unter:

```text
C:\Users\holge\Downloads
```

Erster Codex-Lauf prüfte nur 7 Vergleichstafeln und stoppte korrekt bei:

```text
VISUAL_REVIEW_COMPLETE=NO
```

Grund: `REAL_CHAIN_3X3_DETAIL_COMPARISON.png` ließ sich nicht zuverlässig dekodieren.

Danach wurde ein Recovery-Sprint definiert, der Bilder read-only normalisiert und maximal drei Review-Kontaktbögen erzeugt.

Der spätere Codex-Gesamtvergleich erreichte schließlich vollständige visuelle Prüfung mit 66 relevanten Quelldateien und bewertete den zentralen Real-Chain-Vergleich mit.

Wesentliche belastbare Schlussfolgerungen:

- Aktuelle produktnahe Basis bleibt `FiDeSR Strong -> Original RealESRGAN`.
- Custom-RRDB-Fine-Tunes stoppen.
- P3/P4 nicht als globalen Mikrodetailfilter verfolgen.
- OSDFace nicht global verwenden.
- HAT/VOSR nicht als generellen RealESRGAN-Ersatz verfolgen.
- Hauptdefekt bleibt fehlende natürliche Mikrodetail-Rekonstruktion unter Unsicherheit.
- Mikrodetail-Stufe sollte, wenn überhaupt, nach dem letzten glättenden Upscaler liegen.

Neue Architekturhypothese aus dem Review:

```text
Restoration / Identity Recovery
-> region-aware generative microdetail reconstruction
-> face/hair/body-hair specific refinement
-> NPU super-resolution
-> deterministic finishing
```

Ein möglicher neuer Ansatz ist ein kleiner regionskonditionierter Normalizing-Flow-/SRFlow-artiger Detailzweig. Vor Training muss aber die QNN/HTP-Machbarkeit bewiesen werden.

## Flow-/SRFlow-NPU-Machbarkeit – lokaler Qualcomm-SDK-Audit

Installierte Qualcomm AIStack:

```text
C:\Qualcomm\AIStack\2.47.0.260601
```

### Dokumentations-Gate

Geprüfte flow-relevante Operatoren:

```text
Exp
Log
Reshape
Transpose
Split
Concat
Slice
Mul
Add
Sub
Div
Sigmoid
Softplus
Squeeze
Unsqueeze
DepthToSpace
SpaceToDepth
```

Ergebnis der Qualcomm-Dokumentationsprüfung:

```text
CHECKED_OPERATORS=17
EXPECTED_OPERATORS=17
NO_SUPPORTED_OPS_COUNT=0
NO_ONNX_COUNT=0
NO_HTP_DOC_COUNT=6
DOCUMENTATION_GATE_COMPLETE=YES
```

Die 6 ohne expliziten HTP-Dokumenttreffer:

```text
Exp
Softplus
Squeeze
Unsqueeze
DepthToSpace
SpaceToDepth
```

Sie sind dennoch in allgemeinen SupportedOps- und ONNX-Converter-Dokumenten vorhanden. Daher:

```text
FLOW_DOCUMENTATION_GATE=PASS
SUPPORTED_OPS=17/17
ONNX_SUPPORT=17/17
HTP_RUNTIME_PROOF=NOT_YET
TRAINING_ALLOWED=NOT_YET
NEXT_GATE=REAL_STATIC_QNN_HTP_COMPILE_PROOF
```

### Lokale QNN-Toolchain vorhanden

Gefunden wurden u.a.:

```text
C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-context-binary-generator.exe
C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-net-run.exe
C:\Qualcomm\AIStack\2.47.0.260601\bin\arm64x-windows-msvc\qnn-onnx-converter
C:\Qualcomm\AIStack\2.47.0.260601\bin\x86_64-windows-msvc\qnn-onnx-converter
```

Summary:

```text
TOTAL_TOOL_MATCHES=16
QNN_NET_RUN_COUNT=2
ONNX_CONVERTER_COUNT=3
```

### ONNX-Python-Bestand

Lokale Python-Interpreter wurden geprüft.

ONNX vorhanden in:

```text
C:\SnapdragonAI\temp\qnn_audit_venv\Scripts\python.exe
ONNX=1.22.0

C:\SnapdragonAI\temp\sd21_wrapper_venv\Scripts\python.exe
ONNX=1.20.0
```

Keiner dieser Interpreter konnte die Qualcomm-QTI-Module vollständig für den Converter laden.

Qualcomm Python-Paketpfad:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\python
```

`import qti.aisw` funktioniert mit gesetztem `PYTHONPATH`, aber der Converter scheitert an:

```text
ModuleNotFoundError: No module named 'libPyIrGraph'
```

### Root Cause – durch Antigravity verifiziert

Antigravity untersuchte read-only die lokale AIStack-Struktur, Doku, Setup-Skripte und nativen Extensions.

Finaler Befund:

```text
EXPECTED_PYTHON_VERSION=3.10
EXPECTED_ARCHITECTURE=x86_64 / AMD64
PYTHON310_REQUIRED=YES
LOCAL_PYTHON310_FOUND=NO
LOCAL_PYTHON310_PATH=NONE
REQUIRED_PYTHONPATH=C:\Qualcomm\AIStack\2.47.0.260601\lib\python
OFFICIAL_SETUP_SCRIPT=C:\Qualcomm\AIStack\2.47.0.260601\bin\envsetup.ps1
CAN_RUN_CONVERTER_WITH_EXISTING_FILES=NO
```

Wichtige Details:

- Qualcomm Windows-Dokumentation nennt Python 3.10 als unterstützte Version.
- Native Windows-Extensions heißen durchgehend `*310.pyd`.
- Beispiel:

```text
C:\Qualcomm\AIStack\2.47.0.260601\lib\python\qti\aisw\converters\common\windows-arm64ec\libPyIrGraph310.pyd
C:\Qualcomm\AIStack\2.47.0.260601\lib\python\qti\aisw\converters\common\windows-x86_64\libPyIrGraph310.pyd
```

- Diese nativen Module sind fest an `python310.dll` gebunden.
- Lokaler Python-Bestand:
  - Python 3.11.9 ARM64 unter `C:\Program Files\Python311-arm64\`
  - Python 3.11.9 x64 unter `C:\Users\holge\AppData\Local\Programs\Python\Python311-x64\`
  - kein Python 3.10 / keine `python310.dll` gefunden.

Root Cause:

```text
QNN_CONVERTER_BLOCKER=PYTHON_3_10_X64_MISSING
```

Damit ist die bisherige Converter-Fehlerkette vollständig erklärt. Nicht weiter versuchen, den Converter mit Python 3.11 zu starten.

## Aktueller Flow-NPU-Status

```text
FLOW_DOCUMENTATION_GATE=PASS
QNN_TOOLCHAIN_PRESENT=YES
QNN_CONVERTER_BLOCKER=PYTHON_3_10_X64_MISSING
FLOW_HTP_GATE=NOT_YET_TESTED
TRAINING_ALLOWED=NO
```

Es wurde noch kein echter Flow-Mikrograph erfolgreich durch QNN/HTP kompiliert oder ausgeführt.

## Verbindlicher nächster Schritt am 18. September 2026

Holger hat am Feierabend ausdrücklich freigegeben, morgen mit einer isolierten Python-3.10-x64-Laufzeit für den Qualcomm-QNN-Converter weiterzumachen.

Ziel:

```text
Python 3.10.x AMD64
-> isolierte QNN-Converter-Umgebung
-> C:\Qualcomm\AIStack\2.47.0.260601\bin\envsetup.ps1
-> ONNX/QTI Import PASS
-> statischen Flow-Mikrographen erzeugen
-> qnn-onnx-converter
-> echter HTP-V73 Compile/Runtime-Gate
```

Wichtig:

- bestehende Python-3.11-ARM64-Produktumgebung nicht verändern;
- keine globale Python-Ersetzung;
- isolierte Umgebung nur für QNN-Converter;
- noch kein Flow-Training;
- kein Codex für diesen Schritt;
- PowerShell bevorzugen, Antigravity nur falls die Qualcomm-Umgebungsaktivierung/ABI-Konfiguration erneut unklar wird;
- erst wenn der Mikrograph wirklich auf HTP kompiliert und läuft, darf `FLOW_NPU_GATE=PASS` gesetzt werden;
- erst danach überhaupt entscheiden, ob ein kleiner SRFlow-/Normalizing-Flow-Qualitätsproof trainiert wird.

## Fehler / Lessons Learned vom 17. September

Mehrere lokale Prüfskripte hatten vermeidbare Probleme. Für die Fortsetzung verbindlich:

1. PowerShell-Ausgaben nicht künstlich als `PASS` setzen, wenn vorherige Schritte fehlgeschlagen sind.
2. Bei `$ErrorActionPreference='Stop'` beachten, dass native Python-Fehler Schleifen abbrechen können.
3. Bei Copy/Paste keine getrennten `if { } else { }`-Blöcke verwenden, wenn PowerShell sie interaktiv als getrennte Statements interpretieren kann.
4. QNN-Converter-Skripte zuerst auf Shebang/ABI prüfen; nicht wie native EXEs behandeln.
5. Vor Tool-Aufrufen exakte lokale Python-/SDK-Versionen und native Modulnamen prüfen.
6. Kein Training starten, solange ein echtes HTP-Compile-/Runtime-Gate fehlt.

## Git-/Build-Status dieser späten Arbeiten

Die HAT-, VOSR-, OSDFace-, Codex-Review- und Flow-Machbarkeitsarbeiten waren Analyse-/Forschungsarbeiten. Es wurde in diesem Abschnitt kein neuer Produkt-Build, Installer, Commit oder Push durchgeführt.

```text
BUILD_LATE_17_SEPTEMBER=False
INSTALLER_LATE_17_SEPTEMBER=False
GIT_ADD_LATE_17_SEPTEMBER=False
COMMIT_LATE_17_SEPTEMBER=False
PUSH_LATE_17_SEPTEMBER=False
```

Lokale bereits vorhandene Faithful-/Enhanced-/FiDeSR-Integrationsänderungen weiterhin nicht blind committen oder verwerfen.

## Statusflags – Feierabend 17. September 2026

```text
PRODUKTNAME=HK NPU STUDIO

ORIGINAL_REALESRGAN_PRODUCT_BASELINE=KEEP
CUSTOM_REALESRGAN_FINETUNE_PATH=STOPPED
HAT_PRODUCT_PATH=STOPPED
VOSR_PRODUCT_PATH=STOPPED
OSDFACE_GLOBAL_PRODUCT_PATH=STOPPED

FIDESR_STRONG_TECH_PASS=True
FAITHFUL_QUALITY_PASS=True
ENHANCED_QUALITY_PASS=True
ENHANCED_REFERENCE_QUALITY=False

MICRODETAIL_MAIN_DEFECT=SKIN_PORES_AND_FINE_HAIR_RECONSTRUCTION
REGION_AWARE_GENERATIVE_MICRODETAIL_REQUIRED=LIKELY

FLOW_DOCUMENTATION_GATE=PASS
FLOW_SUPPORTED_OPS=17_OF_17
FLOW_ONNX_SUPPORT=17_OF_17
FLOW_HTP_RUNTIME_PROOF=False
FLOW_TRAINING_ALLOWED=False

QNN_TOOLCHAIN_PRESENT=True
QNN_CONVERTER_EXPECTED_PYTHON=3.10_X64
LOCAL_PYTHON310_FOUND=False
QNN_CONVERTER_BLOCKER=PYTHON_3_10_X64_MISSING

NEXT_SESSION=INSTALL_ISOLATED_PYTHON310_X64_FOR_QNN_CONVERTER_THEN_FLOW_HTP_MICROGATE
PREFERRED_TOOL=POWERSHELL
ANTIGRAVITY_IF_ENVIRONMENT_NEEDS_DEEPER_ANALYSIS=True
CODEX_FOR_NEXT_STEP=False

BUILD_LATE_17_SEPTEMBER=False
INSTALLER_LATE_17_SEPTEMBER=False
GIT_ADD_LATE_17_SEPTEMBER=False
COMMIT_LATE_17_SEPTEMBER=False
PUSH_LATE_17_SEPTEMBER=False
```

## Feierabend 17. September 2026

Für heute keine weiteren Installationen, QNN-Compiles, Trainings, Builds, Commits oder Pushes durchführen.

Morgen direkt beim isolierten Python-3.10-x64-QNN-Converter-Setup fortsetzen. Danach statischen Flow-Mikrographen tatsächlich durch QNN/HTP testen. Erst danach weitere Qualitätsforschung.

## Handover-Übernahme

Diese vollständige Datei muss exakt heißen:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie anschließend ausschließlich über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die gesamte ältere Chronik muss vollständig erhalten bleiben. Diese Aktualisierung ergänzt ausschließlich den späten Stand vom 17. September 2026.


# CHATGPT_HANDOVER – Ergänzung 18. September 2026 – Produktpfad gegenüber SDXL/Kaggle abgegrenzt und Priorität für morgen festgelegt

> Diese Ergänzung ist Bestandteil der vollständigen bestehenden `CHATGPT_HANDOVER.md`.
> Die gesamte ältere Chronik bleibt vollständig erhalten. Bei widersprüchlichen Status- oder Prioritätsangaben hat dieser neueste Abschnitt Vorrang.

## Heutiger Anlass

Für eine persönliche, dauerhaft wiederverwendbare Kaggle-Bildverbesserung wurde **SDXL Base + Refiner** als externer GPU-Workflow besprochen. Ziel dieses separaten Kaggle-Werkzeugs ist promptgesteuerte Bildverbesserung mit besonderem Augenmerk auf scharf dargestellte Haare.

Diese Kaggle-Lösung ist ausdrücklich **kein Produktpfad für HK NPU STUDIO**:

- GPU-/Cloud-Ausführung statt Qualcomm QNN/HTP/NPU;
- generative Rekonstruktion mit möglicher Identitäts- und Geometrieabweichung;
- kein bestehender NPU-Port und kein bestätigter Produktvertrag;
- nicht mit der verbindlichen NPU-only-Architektur des Studios gleichsetzen.

```text
SDXL_BASE_REFINER_KAGGLE_TOOL=YES
SDXL_BASE_REFINER_HK_NPU_STUDIO_PRODUCT_PATH=NO
```

## Verbindlicher Produktpfad für HK NPU STUDIO

### Faithful Restoration – Standardmodus

```text
Input
-> FiDeSR Strong QNN/HTP
-> deterministisches Resize-/Tone-/Color-Finishing
-> Output
```

- möglichst natürliche und originaltreue Restaurierung;
- kein RealESRGAN-Aufruf in diesem Modus;
- keine CPU-/GPU-KI und kein generativer SDXL-Pfad.

### Enhanced Restoration – bewusst wählbare Option

```text
Input
-> FiDeSR Strong QNN/HTP
-> originales RealESRGAN x4 QNN/HTP
-> deterministisches Lanczos-Finishing auf die Zielgröße
-> Output
```

- stärkerer sichtbarer Gewinn bei Bart, Augenbrauen/Haarlinie, Kopfhaar und Kanten;
- Identität, Geometrie und Farben blieben im bisherigen Vergleich stabil;
- Hautporen und feinste Mikrostruktur erreichen noch nicht die gewünschte Referenzqualität.

## Bestätigte technische Entscheidung

- Das vorhandene originale `real_esrgan_x4plus.bin` bleibt die produktive RealESRGAN-Baseline.
- Die Custom-RRDBNet-Fine-Tunes V1 und V2 bleiben verworfen und werden nicht nach ONNX/QNN portiert.
- Der SDXL-Inpainting-Microdetail-Pfad bleibt gestoppt.
- Keine erneuten blinden Loss-, Hyperparameter- oder Fertigmodell-Runden.
- Faithful und Enhanced nicht durch SDXL + Refiner ersetzen.
- Der Flow-/QNN-Mikrograph bleibt eine spätere Forschungsoption, wird aber vorerst nicht vor das sichtbare Studio-Produktgate gesetzt.

## Tatsächlicher Integrationsstatus

Die lokalen Faithful-/Enhanced-Änderungen und fokussierten Tests existieren. Sie sind jedoch noch nicht als produktive neue Studio-Version gesichert:

```text
FAITHFUL_LOCAL_IMPLEMENTATION=YES
ENHANCED_LOCAL_IMPLEMENTATION=YES
COMMIT=NO
BUILD=NO
INSTALLER=NO
RELEASE=NO
VISIBLE_RELEASED_STUDIO_PATH=NAFNET_OPTIONAL_DDCOLOR_REALESRGAN
```

Lokale vorhandene Änderungen nicht blind committen, verwerfen oder überschreiben.

## Verbindlicher nächster Einstieg am 19. September 2026

Holger hat entschieden, morgen mit diesem Produktpfad weiterzumachen.

Reihenfolge:

1. Git-Status, HEAD/origin/main und ausschließlich die lokalen Faithful-/Enhanced-/FiDeSR-Diffs prüfen.
2. Keine unrelated oder untracked Dateien verändern.
3. Faithful und Enhanced direkt im echten HK NPU STUDIO auf dem Entwicklungs-PC Holger testen.
4. Beide Ausgaben mit demselben realen Eingangsbild vergleichen und mindestens prüfen:
   - Identität und Gesichtsgeometrie;
   - Haut/Natürlichkeit;
   - Bart, Augenbrauen und Haarlinie;
   - Kopfhaar;
   - Farbe, Halos und Artefakte;
   - korrekter NPU/QNN/HTP-Pfad ohne CPU-/GPU-KI-Fallback.
5. Erst nach Holgers visueller Freigabe den kleinsten sicheren Commit-/Build-Schritt planen.
6. Kein Build, Installer, Git-Staging, Commit oder Push ohne ausdrückliche Freigabe.
7. Den isolierten Python-3.10-x64-QNN-Converter-/Flow-Mikrotest bis nach diesem Studio-Gate pausieren; nicht löschen oder als verworfen markieren.

```text
NEXT_SESSION=VERIFY_AND_TEST_FAITHFUL_ENHANCED_IN_REAL_STUDIO
FLOW_HTP_MICROGATE=PAUSED_NOT_REJECTED
PREFERRED_TOOL=POWERSHELL_FOR_STATUS_THEN_CODEX_ONLY_IF_TARGETED_FIX_REQUIRED
BUILD_18_SEPTEMBER=False
INSTALLER_18_SEPTEMBER=False
GIT_ADD_18_SEPTEMBER=False
COMMIT_18_SEPTEMBER=False
PUSH_18_SEPTEMBER=False
```

## Handover-Übernahme

Diese vollständige Datei muss exakt heißen:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie anschließend ausschließlich über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die gesamte ältere Chronik muss vollständig erhalten bleiben. Diese Aktualisierung ergänzt ausschließlich den Stand vom 18. September 2026.


# CHATGPT_HANDOVER – Ergänzung Tagesabschluss 19. September 2026 – RORem NPU End-to-End, CFG-Batching und Case3-Qualitätsgate

> Diese Ergänzung führt die vollständige bestehende Chronik fort. Ältere Inhalte bleiben unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neueste Abschnitt Vorrang.

## Arbeitsstand / Feierabend

Holger beendet die Arbeit für heute. Keine weiteren NPU-Läufe, Builds, Commits, Pushes oder Integrationsänderungen ausführen. Morgen an exakt diesem Stand fortsetzen.

## RORem-DLC-Artefakte wiederhergestellt

Die zuvor lokal fehlenden RORem-QNN-DLCs wurden aus den bereits erfolgreichen QAI-Hub-Compile-Jobs zurückgeholt; kein neuer Export, Split oder Compile war erforderlich.

Graph A:

```text
QAI_JOB=jp2wq8l6p
TARGET_MODEL_ID=mng7rzyen
PATH=C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_a\graph_a.dlc
BYTES=4975477996
SHA256=4AAB49508C6FC7D481F908C8FB472692FBF3802CDED80935FF0B81A07E180307
RECOVERY_GATE=PASS
```

Graph B:

```text
QAI_JOB=jpyxkww85
TARGET_MODEL_ID=mq8ozjopn
PATH=C:\SnapdragonAI\models\rorem_mixed_qnn_dlc\graph_b\graph_b.dlc
BYTES=5327711148
SHA256=BECFBACA891E6B0A89116EB25776D9776706CFF8520304AE0C9DB555C7166E07
RECOVERY_GATE=PASS
```

## Lokale HTP-Smokes – Graph A und Graph B

Graph A wurde direkt über folgenden bewiesenen Pfad auf QNN/HTP ausgeführt:

```text
qnn-net-run.exe
--model QnnModelDlc.dll
--backend QnnHtp.dll
--dlc_path graph_a.dlc
--input_list ...
--use_native_input_files
--use_native_output_files
```

Ergebnis:

```text
QNN_NET_RUN_EXIT=0
RAW_OUTPUT_COUNT=10
GRAPH_A_OUTPUT_SHAPE_GATE=PASS
GRAPH_A_LOCAL_HTP_SMOKE=PASS
CPU_AI_FALLBACK=NO
```

Graph-A-Ausgänge:

```text
output_0 [1,320,128,128]
output_1 [1,320,128,128]
output_2 [1,320,128,128]
output_3 [1,320,64,64]
output_4 [1,640,64,64]
output_5 [1,640,64,64]
output_6 [1,640,32,32]
output_7 [1,1280,32,32]
output_8 [1,1280,32,32]
output_9 [1,1280,32,32]
```

Graph B wurde danach mit den echten Graph-A-Ausgaben und denselben Conditioning-Tensoren auf QNN/HTP ausgeführt.

```text
QNN_NET_RUN_EXIT=0
RAW_OUTPUT_COUNT=1
GRAPH_B_OUTPUT_SHAPE_GATE=PASS
GRAPH_B_LOCAL_HTP_SMOKE=PASS
RORem_SPLIT_LOCAL_HTP_TECH_GATE=PASS
CPU_AI_FALLBACK=NO
```

Finaler Graph-B-Output:

```text
out_sample [1,4,128,128] FP16
131072 Bytes
finite
```

## Minimaler produktionsnaher RORem-DLC-Adapter implementiert

Antigravity implementierte zwei neue Dateien:

```text
C:\SnapdragonAI\engine\backends\rorem_dlc_inpainting_adapter.py
C:\SnapdragonAI\tests\test_rorem_dlc_inpainting_adapter.py
```

Bestehende Produktdateien wurden in diesem Sprint nicht modifiziert.

Der Adapter kapselt:

```text
prepared FP16 tensors
-> RORem Graph A / QNN HTP
-> 10 strikt gemappte Cross-Graph-Tensoren
-> RORem Graph B / QNN HTP
-> out_sample [1,4,128,128] FP16
```

Tests:

```text
PY_COMPILE=PASS
UNIT_TESTS=PASS
UNIT_TEST_COUNT=13
GRAPH_A_HTP=PASS
GRAPH_B_HTP=PASS
FINAL_OUT_SHAPE=(1,4,128,128)
FINAL_OUT_DTYPE=float16
FINAL_OUT_FINITE=True
CPU_AI_FALLBACK=NO
TECH_PASS=YES
QUALITY_PASS=NOT_TESTED
PRODUCT_PASS=NO
```

## Real-Image-End-to-End-HTP-Pipeline implementiert

Der Adapter wurde anschließend auf echten 1024x1024-Bildbetrieb erweitert.

Neuronale Inferenzpfade:

```text
CLIP-L -> Qualcomm HTP
CLIP-G -> Qualcomm HTP
VAE Encoder -> Qualcomm HTP
RORem Graph A -> Qualcomm HTP
RORem Graph B -> Qualcomm HTP
VAE Decoder -> Qualcomm HTP
```

CPU nur für Scheduler/CFG/Noise/I/O/Masken-/Compositing-Logik.

Erster echter 1-Step-End-to-End-Smoke:

```text
REAL_INPUT_IMAGE=C:\SnapdragonAI\temp\rorem_validation\case2_input.png
REAL_INPUT_MASK=C:\SnapdragonAI\temp\rorem_validation\case2_mask.png
REAL_OUTPUT_IMAGE=C:\SnapdragonAI\temp\rorem_validation\case2_rorem_e2e_htp_smoke_1step.png
OUTPUT_RESOLUTION=1024x1024
OUTPUT_IS_RGB=YES
OUTPUT_FINITE=YES
OUTSIDE_MASK_PRESERVED=YES
TECH_PASS=YES
QUALITY_PASS=NOT_TESTED
PRODUCT_PASS=NO
```

Gemessene Laufzeit:

```text
ELAPSED_SECONDS=984.33
ca. 16.4 Minuten für 1 Step
```

Der Lauf belegte technisch die vollständige NPU-Pipeline, aber die erste Maske lag nur auf einer einfachen Wandfläche und war daher kein belastbarer Qualitätsnachweis.

## Case3 – härterer Qualitätsfall: Wandbild entfernen

Für einen aussagekräftigeren visuellen Gate wurde das gerahmte Wandbild maskiert.

```text
CASE3_INPUT=C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_input.png
CASE3_MASK=C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_mask_remove_wall_frame.png
CASE3_PREVIEW=C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_mask_overlay_preview.png
MASK_BOX=(620,105,795,450)
MASK_TARGET=WALL_FRAME
```

### Case3 1-Step

```text
REAL_OUTPUT=C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_rorem_remove_wall_frame_1step.png
RESULT_SUCCESS=True
OUTPUT_VALID_PNG=YES
OUTPUT_SIZE=1024x1024
OUTPUT_FINITE=YES
OUTSIDE_MASK_MAX_DIFF=0
OUTSIDE_MASK_CHANGED_PIXELS=0
INSIDE_MASK_CHANGED_PIXELS=60528
INSIDE_MASK_TOTAL_PIXELS=60896
OUTSIDE_MASK_PRESERVED=YES
STEPS_EXECUTED=1
CPU_AI_FALLBACK=NO
TECH_PASS=YES
```

Laufzeit:

```text
ELAPSED_SECONDS=932.35
ca. 15.5 Minuten
```

Ein PowerShell-Wrapper meldete danach fälschlich einen HARD STOP wegen leerem `Process.ExitCode`; das war kein Pipelinefehler.

```text
WRAPPER_FALSE_FAILURE=YES
RERUN_REQUIRED=NO
```

Visuelle Bewertung durch ChatGPT und Holger-Bildvergleich:

```text
OBJECT_REMOVAL=FAIL
BACKGROUND_RECONSTRUCTION=FAIL
MASK_EDGE=PASS
OUTSIDE_MASK_PRESERVATION=PASS
VISIBLE_CHANGE=MINIMAL
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

Das Wandbild blieb praktisch vollständig sichtbar. 1 Step ist kein brauchbarer Object-Removal-Qualitätsnachweis.

## CFG-Batch-Laufzeitoptimierung

Die bisherige Runtime startete pro Denoising-Step vier große QNN-Prozesse:

```text
A uncond
A cond
B uncond
B cond
```

Antigravity optimierte dies auf zwei Prozessstarts pro Step über je zwei Input-Sets pro Graph.

Neuer Vertrag:

```text
Graph A: 1 qnn-net-run Start, 2 CFG-Inferenz-Sets
Graph B: 1 qnn-net-run Start, 2 CFG-Inferenz-Sets
Result_0=negative
Result_1=positive
```

Messung im synthetischen HTP-Smoke:

```text
GRAPH_A_PROCESS_STARTS=1
GRAPH_A_INFERENCE_SETS=2
GRAPH_A_ELAPSED_SECONDS=224.61

GRAPH_B_PROCESS_STARTS=1
GRAPH_B_INFERENCE_SETS=2
GRAPH_B_ELAPSED_SECONDS=243.00

TOTAL_DENOISING_STEP_SECONDS=467.61
OLD_PROCESS_STARTS_PER_STEP=4
NEW_PROCESS_STARTS_PER_STEP=2
RUNTIME_REDUCTION=49.8%
CPU_AI_FALLBACK=NO
```

Tests danach:

```text
UNIT_TESTS=PASS
UNIT_TEST_COUNT=37
TECH_PASS=YES
QUALITY_PASS=NO
PRODUCT_PASS=NO
```

## Case3 Mehrschritt-/Batch-Test

Ein echter Batch-Qualitätslauf wurde mit `steps=4`, `strength=0.9999`, `seed=20260830`, `guidance_scale=7.5` gestartet.

Wichtiger Scheduler-Befund:

```text
STEPS_REQUESTED=4
STEPS_EXECUTED=3
```

Grund: Diffusers-Euler-Scheduler-Contract bei strength=0.9999 führte deterministisch zu `init_timestep=3` und damit genau drei ausgeführten Denoising-Schritten.

Prozess-/Batch-Vertrag im Realbildlauf:

```text
GRAPH_A_PROCESS_STARTS_TOTAL=3
GRAPH_A_INFERENCE_SETS_TOTAL=6
GRAPH_B_PROCESS_STARTS_TOTAL=3
GRAPH_B_INFERENCE_SETS_TOTAL=6
TOTAL_PROCESS_STARTS_DENOISING=6
TOTAL_INFERENCE_SETS_DENOISING=12
```

NPU-Treue:

```text
VAE_ENCODE_BACKEND=HTP
CLIP_BACKEND=HTP
GRAPH_A_BACKEND=HTP
GRAPH_B_BACKEND=HTP
VAE_DECODE_BACKEND=HTP
CPU_AI_FALLBACK=NO
```

Output:

```text
OUTPUT_FILE=C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_rorem_remove_wall_frame_4step_batch.png
OUTPUT_EXISTS=YES
OUTPUT_SHAPE=1024x1024
OUTPUT_CHANNELS=3
OUTSIDE_MASK_PRESERVED=YES
OUTSIDE_MASK_MAX_DIFF=0
```

Laufzeiten:

```text
TOTAL_RUNTIME_SECONDS=3902.58
TOTAL_RUNTIME_MINUTES≈65.04

STEP_1_ELAPSED_SECONDS=1353.08
STEP_2_ELAPSED_SECONDS=1219.90
STEP_3_ELAPSED_SECONDS=1280.74
STEP_4_ELAPSED_SECONDS=NOT_EXECUTED

VAE_ENCODE_SECONDS=7.65
CLIP_SECONDS=25.12
VAE_DECODE_SECONDS=6.82
GRAPH_A_TOTAL_SECONDS=1898.57
GRAPH_B_TOTAL_SECONDS=1954.58
```

Die reale Laufzeitbasis für zukünftige Schätzungen ist damit deutlich höher als zuvor angenommen. Künftige Zeitangaben müssen sich an diesen realen Messwerten orientieren.

Status des Mehrschritt-Laufs:

```text
TECH_PASS=YES
QUALITY_PASS=NOT_TESTED
PRODUCT_PASS=NO
NEXT_EXACT_STEP=MANUAL_COMPARE_CASE3_1STEP_VS_4STEP
```

Das 4-Step-Batch-Ausgabebild wurde am Feierabend noch nicht manuell visuell bewertet.

## Aktueller Produktstatus RORem

```text
RORem_DLC_RECOVERY=PASS
RORem_GRAPH_A_LOCAL_HTP=PASS
RORem_GRAPH_B_LOCAL_HTP=PASS
RORem_SPLIT_LOCAL_HTP_TECH_GATE=PASS
RORem_BACKEND_ADAPTER_IMPLEMENTED=True
RORem_UNIT_TESTS=37_PASS
RORem_REAL_IMAGE_E2E_HTP=PASS
RORem_CPU_AI_FALLBACK=NO
RORem_CFG_BATCH_OPTIMIZATION=PASS
RORem_CASE3_1STEP_TECH_PASS=YES
RORem_CASE3_1STEP_QUALITY_PASS=NO
RORem_CASE3_MULTI_STEP_TECH_PASS=YES
RORem_CASE3_MULTI_STEP_QUALITY_PASS=NOT_TESTED
RORem_PRODUCT_PASS=NO
```

## Git / Build / Release-Gates

Während der beschriebenen RORem-Sprints wurden keine Builds, Installer, Commits oder Pushes ausgeführt.

Mindestens neu/uncommitted aus den RORem-Sprints:

```text
C:\SnapdragonAI\engine\backends\rorem_dlc_inpainting_adapter.py
C:\SnapdragonAI\tests\test_rorem_dlc_inpainting_adapter.py
```

Zusätzliche Änderungen innerhalb dieser beiden Dateien durch E2E- und CFG-Batch-Erweiterungen sind uncommitted. Vor jedem späteren Commit erst Git-Status und Diff exakt prüfen. Keine fremden/untracked Dateien anfassen. Niemals `git add .`.

## Verbindlicher nächster Schritt morgen

**Noch keinen neuen NPU-Lauf starten.**

Zuerst nur das bereits erzeugte Mehrschrittbild visuell gegen Input und 1-Step vergleichen:

```text
INPUT:
C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_input.png

MASK PREVIEW:
C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_mask_overlay_preview.png

1-STEP:
C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_rorem_remove_wall_frame_1step.png

MULTI-STEP/BATCH:
C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_rorem_remove_wall_frame_4step_batch.png
```

Bewerten:

1. Ist der Rahmen tatsächlich entfernt?
2. Ist das Motiv verschwunden?
3. Wird die Wand plausibel rekonstruiert?
4. Maskenrand/Feathering sauber?
5. Artefakte?
6. Sichtbarer Gewinn gegenüber 1-Step?

Wenn der Rahmen auch nach drei real ausgeführten Denoising-Schritten praktisch stehen bleibt:

```text
KEINE weiteren Steps verschwenden.
NEXT_EXACT_STEP=ANALYZE_RORem_DENOISING_STRENGTH_MASK_PROMPT_CONTRACT
```

Wenn die Entfernung deutlich besser ist:

```text
NEXT_EXACT_STEP=DEFINE_PRODUCT_LATENCY_AND_STUDIO_INTEGRATION_GATE
```

## Tagesabschluss 19. September 2026

```text
FEIERABEND=True
NO_MORE_NPU_RUNS_TODAY=True
NO_BUILD_TODAY=True
NO_COMMIT_TODAY=True
NO_PUSH_TODAY=True
NEXT_SESSION=MANUAL_CASE3_MULTI_STEP_VISUAL_REVIEW
```

## Handover-Übernahme

Diese vollständige Datei muss als exakt

```text
CHATGPT_HANDOVER.md
```

bereitgestellt werden. Holger übernimmt sie anschließend ausschließlich über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die ältere Chronik darf niemals gekürzt oder durch eine reine Ergänzungsdatei ersetzt werden.

# CHATGPT_HANDOVER – Ergänzung Tagesabschluss 20. September 2026 – FiDeSR Photo Restore, Phoenix Image Lab, SD3.5-NPU-Gap und Übergabe an Gemini/Antigravity

> Diese Ergänzung führt die vollständige bestehende Chronik fort. Ältere Inhalte bleiben unverändert erhalten. Bei widersprüchlichen Statusangaben hat dieser neueste Abschnitt vom **20. September 2026** Vorrang.

## Arbeitsmodus ab 21. September 2026

Holger beendet die Arbeit für heute.

Ab morgen wird das Projekt vorerst mit **Gemini + Antigravity** weitergeführt, weil ChatGPT/Codex aktuell zu teuer sind.

Verbindlich:

```text
PRIMARY_ASSISTANT=Gemini
PRIMARY_ANALYSIS_TOOL=Antigravity
CHATGPT_CODEX_DEFAULT=PAUSED_COST_REASON
LANGUAGE=Deutsch
```

Gemini erhält zusätzlich zu dieser vollständigen Handover-Datei die separaten „HK NPU STUDIO – ARBEITSREGELN FÜR GEMINI“.

Bei jedem neuen Arbeitstag zuerst:

```text
CURRENT_STATE=
NEXT_EXACT_STEP=
DO_NOT_TOUCH=
```

ausgeben, erst danach Sprints oder Änderungen planen.

## Arbeitsregeln für Gemini – verbindlich

Projekt:

```text
Repo=C:\SnapdragonAI
Produkt=HK NPU STUDIO
Zielplattform=Windows 11 ARM64 / Snapdragon X
```

Produktregel:

- KI-Kernfunktionen ausschließlich über Qualcomm NPU / QNN / HTP.
- CPU/GPU-basierte neuronale KI-Inferenz ist keine akzeptable Produktlösung.
- CPU darf nur nicht-neuronale Aufgaben übernehmen: I/O, Resize, Masken, Compositing, deterministische Mathematik und parameterlose Berechnungen.

Handover-Regel:

- `CHATGPT_HANDOVER.md` ist die zentrale Projektquelle.
- Neuester Eintrag gewinnt bei Widersprüchen.
- Verworfene Pfade nicht wiederbeleben.
- Keine neue Modellforschung beginnen, solange ein vorhandener Pfad noch sauber fertiggestellt werden kann.
- Keine langen Blindläufe.
- TECH_PASS, QUALITY_PASS und PRODUCT_PASS strikt trennen.
- PRODUCT_PASS nur nach realem Studio-/Sichttest.

Vor technischen Sprints immer:

```text
SPRINT-ZEIT=
WORST CASE=
SPEICHER=
HARD STOP=
```

Git-/Dateiregeln:

- keine Builds, Commits oder Pushes ohne ausdrückliche Freigabe;
- niemals `git add .`;
- untracked/unrelated Dateien nicht anfassen;
- PowerShell-Befehle vollständig und möglichst atomar liefern;
- Windows lokal = PowerShell;
- Kaggle = nur Python.

## RORem – endgültig verworfen

Finaler Status:

```text
ROREM_TECH_PASS=YES
ROREM_QUALITY_PASS=NO
ROREM_PRODUCT_PASS=NO
ROREM_PRODUCT_PATH=REJECTED
ROREM_FURTHER_NPU_WORK=STOP
NO_MORE_RORem_RUNS=YES
```

Gründe: QNN/HTP-End-to-End technisch möglich, aber reale Objekt-/Personenentfernung qualitativ unbrauchbar und extrem langsam. RORem nicht erneut vorschlagen oder optimieren.

## AI Photo Restore – FiDeSR Faithful

Sichtbarer Produktmodus:

```text
FAITHFUL_VISIBLE=YES
ENHANCED_VISIBLE=NO
DEFAULT_MODE=faithful
```

Enhanced wurde aus der sichtbaren UI entfernt, weil das Ergebnis sichtbar überprozessiert war.

Neuronale FiDeSR-Stufen:

```text
VAE Encoder -> QNN/HTP
UNet        -> QNN/HTP
LRRB        -> QNN/HTP
VAE Decoder -> QNN/HTP
CPU_AI_FALLBACK=NO
```

Task-Manager 0 % NPU ist kein Beleg für CPU-Fallback; der HTP-Pfad wurde über `qnn-net-run.exe`, `QnnHtp.dll`, QNN-Logs und erfolgreiche HTP-Ausführung belegt.

### 128px-Downscale verworfen

Ein zwischenzeitlich eingeführter globaler 128px-Input-Bound verursachte stark veränderte Gesichter bei Bild 45.

```text
128PX_INPUT_BOUND=REJECTED
INPUT_128_DOWNSCALE_REMOVED=YES
NATIVE_MULTI_TILE_RESTORED=YES
```

Der native FiDeSR-Multi-Tile-Pfad bleibt der einzige akzeptierte Restore-Pfad.

### Process-Lifecycle-Fix

Erhalten:

- nach letzter Kachel reguläres `proc.wait(...)`;
- `terminate()/kill()` nur bei Fehler, Timeout oder Benutzerabbruch;
- kein künstlicher Exitcode-1 durch vorzeitiges Beenden während HTP-Teardown.

### Bild 45

Nach Rückkehr zum nativen Multi-Tile-Pfad:

- Gesichter deutlich näher am Original;
- Ergebnis insgesamt brauchbarer;
- Haut weiterhin zu glatt / weich rekonstruiert.

```text
IMAGE_45_NATIVE_MULTITILE=SUCCESS
FACE_IDENTITY_PRESERVATION=MUCH_BETTER
FACE_SMOOTHING=STILL_TOO_STRONG
QUALITY_PASS=PARTIAL
PRODUCT_PASS=NO
```

### Vorgemerkte Produktverbesserung „Natürliche Hauttextur / Anti-Glättung“

Später optionaler Veredelungsschritt:

- keine einfache globale Rauschüberlagerung;
- dezente Mikrotextur / Porenwirkung;
- sehr feines organisches Filmkorn;
- leichter lokaler Mikrokontrast;
- bevorzugt nur Haut-/Gesichtsbereiche;
- Identität/Gesichtsform niemals verändern;
- mögliche Stufen: Aus / Leicht / Mittel;
- bevorzugt für Faithful Restoration.

Dieser Schritt darf niemals falsch rekonstruierte Gesichter kaschieren.

## FiDeSR RAM-Optimierung

Audit vor Optimierung, realer Lauf Bild 45, 1262x1181 -> 5048x4720, 156 Kacheln je Modellstufe:

- UNet-DLC ~3.3 GB, `qnn-net-run.exe` Peak mehrere GB;
- zahlreiche gleichzeitig gehaltene Full-Resolution-Float32-Arrays;
- PyTorch Detail-Preservation mit vielen 24-MP-Tensoren;
- Tile-Records und temporäre RAW-Dateien;
- kein systematisches `del`/`gc.collect()`.

### Phase 1

Geändert:

```text
engine/backends/fidesr_strong_runner_template.py
```

Maßnahmen:

- große Full-Res-Objekte nach letztem Gebrauch freigeben;
- Tile-Records nur noch Koordinaten/RAW-Pfade;
- PyTorch-Temporaries freigeben;
- sichere RAW-Cleanup-Logik;
- Restore-Mathematik unverändert;
- QNN/HTP-Pfad unverändert;
- Process-Lifecycle-Fix erhalten.

Tests:

```text
47/47 PASS
```

### Phase 2

Zusätzlich:

```text
tests/test_fidesr_postprocess_ram.py
```

Maßnahmen:

- 256-Zeilen-Streifen;
- Buffer-Reuse;
- In-place-Ausgabe;
- Full-Resolution-Wavelet-/Detail-/PyTorch-Peaks reduziert;
- mathematische Gleichheit über Streifengrenzen geprüft.

```text
50/50 PASS
NUMERICAL_EQUIVALENCE=PASS
RESTORE_MATH_CHANGED=NO
```

### Reale RAM-Messung nach Phase 2

Vorher:

```text
PEAK_PYTHON_GB=8.74
PEAK_QNN_GB=6.98
PEAK_SYSTEM_USED_GB=15.61
MIN_AVAILABLE_RAM_GB=0
```

Nach Phase 2:

```text
PEAK_PYTHON_GB=1.60
PEAK_QNN_GB=6.70
PEAK_COMBINED_GB=6.81
PEAK_SYSTEM_USED_GB=15.60
MIN_AVAILABLE_RAM_GB=0.01
```

Interpretation:

```text
PYTHON_RAM_FIX=PASS
PYTHON_PEAK_REDUCTION≈82%
SYSTEM_RAM_CAUSE=NOT_FULLY_EXPLAINED
```

Weitere FiDeSR-Codeänderungen nur wegen der System-RAM-Anzeige nicht vornehmen, bevor außerhalb von Python liegende Speicherquellen sauber belegt sind.

Ein späterer CSV-Auswertungsversuch war wegen deutschem Dezimaltrennzeichen/Komma als CSV-Trenner ungültig. Ein weiterer Logger mit englischen `Get-Counter`-Namen scheiterte auf deutschem Windows. Daraus keine Produktdiagnose ableiten.

## Phoenix Image Lab – UI/Navigation

Zielstruktur:

```text
Phoenix Image Lab
├─ AI-Fotorestaurierung
├─ Generatives Füllen & Retusche / Objekte entfernen
└─ Vergleich & Inspektion
```

Separater Sidebar-Doppeleintrag „AI-Fotorestaurierung“ wurde entfernt.

Codex-Sprint meldete:

```text
PHOENIX_IMAGE_LAB_HUB=PASS
PHOTO_RESTORE_SIDEBAR_DUPLICATE_REMOVED=YES
GENERATIVE_FILL_ENTRY=YES
RETOUCH_ENTRY=YES
NAVIGATION_DEAD_ENDS=NO
TECH_PASS=YES
```

Geänderte Dateien u. a.:

```text
widgets/phoenix/sidebar.py
widgets/phoenix/workspace.py
widgets/phoenix/views/image_lab_view.py
widgets/phoenix/views/inpainting_view.py
locales/de_DE.json
tests/test_phoenix_image_lab_navigation.py
GOVERNANCE/CHANGELOG.md
```

Wichtig:

- `GOVERNANCE/CHANGELOG.md` war nicht Kern des UI-Auftrags; vor späterem Commit Diff prüfen.
- Alle Image-Lab-Buttons müssen einheitliches HK-NPU-STUDIO-/Phoenix-Design verwenden.
- Keine Mischung aus blauem Primary-Button und weißen Standard-Buttons.
- Generatives Füllen und Retusche aktuell nicht künstlich als getrennte technische Funktionen darstellen, wenn beide denselben Workflow öffnen.

## Generatives Füllen & Retusche – realer Studio-Test

Die bestehende UI öffnet einen maskenbasierten Inpainting-Bereich mit Bild laden, Pinsel/Radierer, Rückgängig, Maske löschen, Prompt, Steps, Seed, Start/Abbrechen/Speichern.

Testziel: gerahmtes Wandbild entfernen.

Prompt:

```text
remove the framed picture and reconstruct the wall naturally
```

Der Start brach vor Inferenz ab mit:

```text
ERR_CONTEXT_BINARIES_MISSING
```

Fehlende Dateien:

```text
C:\SnapdragonAI\models\sdxl_inpainting_qnn_context\graph_a\graph_a.serialized.bin
C:\SnapdragonAI\models\sdxl_inpainting_qnn_context\graph_b\graph_b.serialized.bin
```

Inventar bestätigte:

```text
SDXL_VAE_ENCODER_CONTEXT=YES
SDXL_VAE_DECODER_CONTEXT=YES
SDXL_GRAPH_A_CONTEXT=NO
SDXL_GRAPH_B_CONTEXT=NO
```

Vorhanden:

```text
C:\SnapdragonAI\models\sdxl_inpainting_qnn\vae_encoder\job_j567mjqnp_optimized_dlc_mqv304z0m.dlc
C:\SnapdragonAI\models\sdxl_inpainting_qnn\vae_decoder\job_jgzmy0o4p_optimized_dlc_mqkj84vkm.dlc
C:\SnapdragonAI\models\sdxl_inpainting_qnn_context\vae_encoder\vae_encoder.serialized.bin
C:\SnapdragonAI\models\sdxl_inpainting_qnn_context\vae_decoder\vae_decoder.serialized.bin
```

SDXL Graph A/B nicht blind neu bauen.

## SD3.5-Inpainting – NPU-only Lücken

Vor Audit:

```text
Text Encoder 1 = QNN/HTP
Text Encoder 2 = QNN/HTP
Transformer    = QNN/HTP
VAE Decoder    = QNN/HTP
VAE Encoder    = CPU/PyTorch
Time/Text Embed= CPU/PyTorch
```

Damit war der vorhandene SD3.5-Pfad nicht produktfähig.

### VAE Encoder

```text
CLASS=diffusers.AutoencoderKL
INPUT=sample [1,3,1024,1024] FP32
OUTPUT=raw_original [1,16,128,128] FP32
POST_MATH=(raw_original - 0.0609) * 1.5305
```

SDXL-VAE-Encoder ist nicht kompatibel:

```text
SDXL output=[1,4,128,128]
SD3.5 requires=[1,16,128,128]
```

### Time/Text

```text
CLASS=CombinedTimestepTextProjEmbeddings
INPUTS=timestep [1] FP32; pooled_projection [1,2048] FP32
OUTPUT=conditioning [1,1536] FP32
TRAINED_PARAMETERS=8263680 FP32
```

Parameterlose Sin/Cos-Timestep-Projektion darf CPU-Mathematik bleiben. Trainierte MLPs müssen HTP laufen.

## SD3.5 Export-Spezifikation und ONNX

Erstellt:

```text
tools/sd35_npu_export_spec.py
tests/test_sd35_npu_export_spec.py
temp/sd35_npu_export_reference/
```

Transformer-Vertrag verbindlich bestätigt:

```text
temb=[1,1536] FP32
CONDITIONING_DIM_CONFIRMED=1536
```

VAE ONNX:

```text
C:\SnapdragonAI\models\sd35_inpainting_qnn_source\vae_encoder\vae_encoder.onnx
SIZE=137200006
ONNX_CHECK=PASS
OUTPUT=[1,16,128,128] FP32
MAX_ABS_ERROR=0.01049184799194336
MEAN_ABS_ERROR=0.0019131588540348687
```

Time/Text ONNX:

```text
C:\SnapdragonAI\models\sd35_inpainting_qnn_source\time_text_embed\time_text_embed.onnx
SIZE=33056786
ONNX_CHECK=PASS
OUTPUT=[1,1536] FP32
MAX_ABS_ERROR=0.00002288818359375
MEAN_ABS_ERROR=0.00000281536995317
```

Beide statisch, FP32, numerisch validiert.

## QNN/HTP – SD3.5 VAE Encoder

QNN-Artefakt:

```text
C:\SnapdragonAI\models\sd35_inpainting_qnn\vae_encoder\vae_encoder.serialized.bin
SIZE=101199872
DLC_SIZE=137264044
```

HTP-Ausführung:

```text
VAE_HTP_RUN=EXECUTION_PASS
OUTPUT_SHAPE=[1,16,128,128] FP32
```

Qualitätsgate:

```text
VAE_QNN_MAX_ABS_ERROR=0.13935303688049316
VAE_QNN_MEAN_ABS_ERROR=0.02137631933933018
QUALITY_PASS=NO
```

Damit:

```text
VAE_HTP_EXECUTION=PASS
VAE_HTP_QUALITY=FAIL
```

## Time/Text QNN-Job

Compile-Job wurde eingereicht:

```text
JOB_ID=jgzl8my65
```

Wegen VAE-HARD-STOP wurde er noch nicht lokal heruntergeladen/validiert.

```text
TIME_TEXT_LOCAL_VALIDATION=NO
ALL_TRAINED_LAYERS_HTP=NO
NPU_ONLY_COMPONENTS_READY=NO
```

Time/Text-Arbeit vorerst nicht weiterführen, solange der VAE-Qualitätsfehler nicht verstanden ist.

## VAE HTP Precision – zwei Compiles, identische Abweichung

Original:

```text
OLD_PRECISION=HTP FP16
Short-Depth-Convolution auf HMX standardmäßig aktiv
```

Kontrollversuch:

```text
NEW_PRECISION=HTP FP16
default_graph_htp_disable_short_depth_conv_on_hmx=true
```

Ergebnis exakt unverändert:

```text
NEW_MAX_ABS=0.13935303688049316
NEW_MEAN_ABS=0.02137631933933018
QUALITY_PASS=NO
TECH_PASS=YES
SHORT_DEPTH_CONV_CHANGE_EFFECT=NONE
NO_MORE_BLIND_PRECISION_FLAG_RETRIES=YES
```

## VAE QNN Root-Cause-Audit

```text
LIKELY_ERROR_STAGE=Kumulative FP16-Abweichung im Encoder-Hauptpfad, besonders GroupNorm/Residual-Blöcke und Bottleneck-Attention
PRECISION_TRANSITIONS=FP32 Input -> interner HTP-FP16-Graph -> FP32 Output
INTEGER_QUANTIZATION=NO
```

Verdächtige Operatoren:

```text
21x GroupNormalization
wiederholte Conv2d/Add/Sigmoid×Mul-SiLU
Bottleneck MatMul/Softmax
```

Belege:

- I/O-Metadaten FP32;
- keine Quantize/Dequantize-Knoten;
- HTP-Ausgabe liegt nahezu exakt auf FP16-Werten;
- Fehler flächig und kanalabhängig;
- HMX-Deaktivierung änderte keinen Messwert;
- keine Intermediate-Tensoren exportiert.

```text
ROOT_CAUSE_CONFIDENCE=HIGH für kumulative interne FP16-Arithmetik
GROUPNORM_FIRST_DOMINANT_STAGE=MEDIUM confidence
```

## Exakter nächster technischer Schritt

Noch **kein weiterer Compile**.

Zuerst Intermediate-Debugpunkte spezifizieren:

```text
1. conv_in
2. nach jedem DownEncoderBlock
3. Mid-Block vor GroupNorm
4. nach Mid-GroupNorm
5. nach Attention
6. conv_out / latent_mode
```

Für jeden Punkt Tensorname, Shape, dtype, PyTorch-/ONNX-Referenz und mögliche QNN-Debug-Ausgabe dokumentieren.

Ziel:

```text
FIRST_DOMINANT_ERROR_STAGE exakt bestimmen
```

Erst danach genau einen gezielten Debug-Graph freigeben.

## DO NOT TOUCH – 21. September 2026

```text
NO_RORem=True
NO_NEW_SDXL_GRAPH_AB_BUILD=True
NO_BLIND_VAE_RECOMPILE=True
NO_TIME_TEXT_LOCAL_VALIDATION_UNTIL_VAE_DEBUG=True
NO_NEW_MODEL_RESEARCH=True
NO_STUDIO_INPAINTING_RUN=True
NO_BUILD=True
NO_COMMIT=True
NO_PUSH=True
```

## Startstatus für Gemini/Antigravity am 21. September 2026

```text
CURRENT_STATE=
HK NPU STUDIO läuft; FiDeSR Photo Restore technisch NPU-only und RAM stark optimiert.
Phoenix Image Lab UI vorhanden.
Generatives Füllen aktuell blockiert.
SD3.5 NPU-only Completion ist prinzipiell möglich.
VAE Encoder läuft auf HTP, aber numerische Qualität scheitert durch vermutlich kumulative interne FP16-Arithmetik.

NEXT_EXACT_STEP=
Nur Intermediate-Debug-Spezifikation für SD3.5 VAE Encoder erstellen.
Noch kein neuer Compile.
Danach nur bei klarer lokalisierter Fehlerstufe einen einzigen gezielten Debug-Graph planen.

DO_NOT_TOUCH=
RORem
SDXL Graph A/B-Neubau
FiDeSR-Restore-Architektur
Time/Text-Download/Validierung vor VAE-Debug
Build/Installer
git add
Commit
Push
```

## Git-/Release-Hinweis

Die heutigen lokalen Änderungen sind nicht committed oder gepusht.

Vor jedem späteren Commit:

1. `git status --short --branch`
2. exakten Diff prüfen;
3. unrelated/untracked Dateien nicht anfassen;
4. niemals `git add .`;
5. nur ausdrücklich freigegebene Dateien stagen.

Mindestens heute neu/ändert lokal:

```text
engine/backends/fidesr_strong_runner_template.py
tests/test_fidesr_postprocess_ram.py
widgets/phoenix/sidebar.py
widgets/phoenix/workspace.py
widgets/phoenix/views/image_lab_view.py
widgets/phoenix/views/inpainting_view.py
locales/de_DE.json
tests/test_phoenix_image_lab_navigation.py
GOVERNANCE/CHANGELOG.md
tools/sd35_npu_export_spec.py
tests/test_sd35_npu_export_spec.py
tools/compile_sd35_missing_htp.py
models/sd35_inpainting_qnn_source/
models/sd35_inpainting_qnn/
temp/sd35_npu_export_reference/
temp/sd35_missing_htp_validation/
```

Diese Liste ist kein Staging-Auftrag. Vor späterem Git-Schritt Zustand erneut exakt prüfen.

## Tagesabschluss 20. September 2026

```text
FEIERABEND=True
PRIMARY_ASSISTANT_NEXT=Gemini
PRIMARY_TOOL_NEXT=Antigravity
CHATGPT_CODEX_PAUSED_COST_REASON=True

RORem_PRODUCT_PATH=REJECTED

PHOTO_RESTORE_TECH_PASS=YES
PHOTO_RESTORE_CPU_AI_FALLBACK=NO
PHOTO_RESTORE_QUALITY_PASS=PARTIAL
PHOTO_RESTORE_PRODUCT_PASS=NO
PHOTO_RESTORE_PYTHON_RAM_FIX=PASS

PHOENIX_IMAGE_LAB_NAV_TECH_PASS=YES
GENERATIVE_FILL_PRODUCT_PASS=NO

SD35_VAE_ONNX=PASS
SD35_VAE_HTP_EXECUTION=PASS
SD35_VAE_HTP_QUALITY=FAIL
SD35_TIME_TEXT_JOB_SUBMITTED=True
SD35_TIME_TEXT_LOCAL_VALIDATION=False
SD35_NPU_ONLY_COMPONENTS_READY=False

NEXT_SESSION=SD35_VAE_INTERMEDIATE_DEBUG_SPEC
```

## Handover-Übernahme

Diese vollständige Datei muss exakt heißen:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie anschließend ausschließlich über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die gesamte ältere Chronik muss vollständig erhalten bleiben. Diese Aktualisierung ergänzt ausschließlich den Stand vom **20. September 2026**.

---

## Object Removal – finaler Produktstand 21. September 2026 (newest wins)

Dieser Abschnitt ersetzt für Object Removal den älteren Status vom 20. September 2026. Die ältere Chronik bleibt als Historie erhalten.

```text
OBJECT_REMOVAL_BACKEND=RORem QNN/HTP
OBJECT_REMOVAL_TECH_PASS=YES
OBJECT_REMOVAL_QUALITY_PASS=YES
OBJECT_REMOVAL_PRODUCT_PASS=YES

REQUESTED_STEPS=4
EXECUTED_STEPS=4
REPORTED_STEPS=4

CPU_AI_FALLBACK=NO
OUTSIDE_MASK_BIT_EXACT=YES
RIGHT_BLACK_FRAME_REMAINS=NO

FINAL_RESULT=C:\SnapdragonAI\temp\rorem_validation\case3_frame_gate\case3_studio_controller_4step_fixed.png
FINAL_RESULT_SHA256=16852FB4085170F7B90440C75CBE1866DB3C687AD7F5CD2901B94A870D1EA5FB

PY_COMPILE=PASS
FOCUSED_TESTS=PASS 26/26
REGRESSION_RISK=LOW
```

Der funktionierende Studio-Produktpfad für „Generatives Füllen & Retusche“ verwendet den bestehenden `RORemDlcInpaintingAdapter`. Trainierte Inferenz läuft ausschließlich über Qualcomm QNN/HTP; ein CPU-/GPU-AI-Fallback existiert nicht. CPU-Verarbeitung bleibt auf Orchestrierung, Scheduler-Mathematik, Masken, Compositing und I/O beschränkt.

Die Step-Abweichung entstand durch `int(4 * 0.9999) == 3`. Die ceil-basierte, auf `1..steps` begrenzte Berechnung führt nun vier angeforderte Steps auch viermal aus und meldet vier Steps. Die Grenzfälle 1/2/4/8 Steps sowie Strength 0.5/0.75/1.0 wurden geprüft.

Der schwarze Rahmenrest war kein Crop-, Padding-, Resize- oder Koordinatenfehler. Die frühere Case3-final_v2-Maske schloss den rechten unteren Rahmen aus; diese unmaskierten Originalpixel wurden vertragsgemäß bitgenau zurückkopiert. Der finale Smoke verwendete eine vollständige temporäre Objektmaske. Keine Case3-Maske und kein Case3-Pfad ist in der Produktlogik hardcodiert.

Für diesen abgeschlossenen Referenzpfad sind keine weiteren Modell-, Compile- oder Precision-Experimente erforderlich.

# CHATGPT_HANDOVER – Ergänzung 22. September 2026 – App-Stabilisierung, Galerie-Freeze behoben und auf GitHub gesichert

> Diese Ergänzung hat für den aktuellen App-Stabilitäts-, Galerie- und Git-Stand Vorrang vor älteren Abschnitten. Die vollständige ältere Chronik bleibt unverändert erhalten.

## Arbeitsmodus und Priorität

Am 22. September 2026 wurde die Arbeit ausschließlich auf die Wiederherstellung einer stabilen, bedienbaren HK-NPU-STUDIO-App konzentriert.

Verbindlich:

```text
PRIORITY=APP_STABILITY
NEW_FEATURES_DURING_STABILIZATION=NO
BUILD=NO
INSTALLER=NO
```

Object Removal / RORem und Photo Restore / FiDeSR blieben als bereits gesicherte Produktpfade unangetastet.

## Ausgangslage

Der letzte gesicherte Remote-Stand vor der Stabilisierung war:

```text
origin/main=49eb1de69f85b258edf7bb0628a6e3e7f0798ac8
COMMIT=feat: complete NPU image lab integration
```

Der ursprüngliche lokale Arbeitsbaum war davor divergent und dirty:

```text
LOCAL_HEAD=186e1c993f123568b0d7417a87d8406be5897a21
REMOTE_HEAD=49eb1de69f85b258edf7bb0628a6e3e7f0798ac8
```

Die am 21. September lokal begonnenen UI-/Image-Lab-Arbeiten hatten zu einem vollständigen App-Hang geführt. Windows Error Reporting hatte bestätigt:

```text
EVENT_ID=1001
EVENT_NAME=AppHangTransient
PROCESS=python.exe
PYTHON_TRACEBACK=NONE
```

## Sicherheitsbackup vor Rücksetzung

Vor jeder Rücksetzung wurde der lokale Stand gesichert.

Backup-Verzeichnis:

```text
C:\SnapdragonAI\temp\pre_baseline_reset_20260922_082939
```

Dort wurden unter anderem gespeichert:

```text
git_status_short.txt
git_status_full.txt
working_tree.patch
index.patch
untracked_files.txt
commit_state.txt
```

Größe des Working-Tree-Patches:

```text
WORKING_TREE_PATCH_BYTES=2800751
```

Zusätzlich wurden die wichtigsten lokalen Image-Lab-/UI-Dateien einzeln kopiert:

```text
controllers\inpainting_controller.py
widgets\phoenix\inpainting_canvas.py
widgets\phoenix\views\inpainting_view.py
widgets\phoenix\views\image_lab_view.py
widgets\phoenix\views\home_view.py
tests\test_phoenix_inpainting_ui.py
tests\test_home_first_run.py
```

Es gab keine staged Änderungen:

```text
STAGED_CHANGES=NO
```

Die große Zahl untracked Dateien stammte fast vollständig aus lokalen virtuellen Umgebungen:

```text
UNTRACKED_COUNT=14466
sd35_venv=13628
temp_venv=771
```

Diese wurden nicht gelöscht.

Zusätzlicher Sicherungsbranch:

```text
backup/pre-baseline-reset-20260922
```

Dieser Branch zeigt auf den früheren lokalen HEAD:

```text
186e1c993f123568b0d7417a87d8406be5897a21
```

## Rückkehr auf stabile Baseline

Nach Backup wurde der getrackte Original-Arbeitsbaum kontrolliert auf:

```text
49eb1de69f85b258edf7bb0628a6e3e7f0798ac8
```

zurückgesetzt.

Wichtig:

```text
git clean=NICHT verwendet
untracked Dateien=NICHT gelöscht
```

Ein isolierter Worktree auf derselben Baseline war zuvor bereits manuell stabil gelaufen.

## Erste neue Beobachtung nach Rücksetzung

Der originale Ordner `C:\SnapdragonAI` startete zwar wieder, zeigte aber zunächst weiterhin Bedienungsprobleme. Der Unterschied zum isolierten Worktree lag damit nicht mehr im getrackten Code allein.

Zur Eingrenzung wurden drei untracked Runtime-Dateien aus dem Repo in Quarantäne verschoben:

```text
engine/backends/sd35_inpainting_backend_adapter.py
engine/backends/sdxl_inpainting_qnn_context_adapter.py
engine/experiments/sd35_inpainting_npu.py
```

Quarantäne:

```text
C:\SnapdragonAI_UntrackedQuarantine_20260922_084730
```

Diese Dateien wurden nicht gelöscht. Sie gehören nicht zum späteren Galerie-Fix.

## Galerie-Freeze – entscheidende reale Eingrenzung

Nach Rückkehr auf die stabile Baseline zeigte sich ein klar reproduzierbares Muster:

```text
APP_START=OK
CLICK_GALLERY=FREEZE
WHOLE_UI_UNRESPONSIVE=YES
```

Die Galerie lief hingegen stabil, sobald der bestehende Inhalt von `C:\SnapdragonAI\output` temporär aus dem Repo verschoben wurde.

Output-Quarantäne:

```text
C:\SnapdragonAI_OutputQuarantine_20260922_085550
```

Originalbildanzahl:

```text
31 Bilder
```

Mit leerem `output`:

```text
START=OK
GALERIE_OEFFNEN=OK
GALERIE_REAGIERT=JA
SIDEBAR_NACH_GALERIE=OK
FREEZE=NEIN
```

Damit war der Freeze eindeutig an den realen Galerie-Inhalt gekoppelt.

## Bildprofiling – große Photo-Restore-Ausgaben

Die 31 Originalbilder wurden außerhalb der GUI einzeln mit dem relevanten PIL-Thumbnailpfad geprüft.

Sechs große FiDeSR-/Photo-Restore-Ausgaben waren besonders langsam:

```text
37_faithful_x4.png        5104x4920  25.112 MP  1.3867 s
45_faithful_x4.png        5048x4724  23.847 MP  1.2721 s
45_faithful_x4_001.png    5048x4720  23.827 MP  1.3513 s
45_faithful_x4_002.png    5048x4720  23.827 MP  1.3326 s
45_faithful_x4_003.png    5048x4720  23.827 MP  1.0552 s
45_faithful_x4_004.png    5048x4720  23.827 MP  0.6926 s
```

Diese sechs Bilder verursachten zusammen rund:

```text
7.09 Sekunden
```

reine synchrone Thumbnail-Dekodierzeit.

Die Bilder waren nicht beschädigt. Der Fehler lag in der synchronen Verarbeitung im Tk-Hauptthread.

## Erster Galerie-Fix war am falschen Pfad

Zunächst wurde irrtümlich `widgets/phoenix/views/image_view.py` optimiert.

Spätere Runtime-Pfadanalyse bewies:

```text
PREVIOUS_IMAGE_VIEW_FIX_WAS_ACTIVE_PATH=NO
```

Die Sidebar-Galerie verwendet nicht `PhoenixImageView`.

`widgets/phoenix/views/image_view.py` wurde deshalb wieder vollständig auf `HEAD` zurückgesetzt und ist nicht Bestandteil des finalen Commits.

## Tatsächlicher produktiver Galeriepfad

Der echte Navigationspfad wurde exakt bestätigt:

```text
PhoenixSidebar._navigate("gallery")
→ PhoenixWorkspace.show_view("gallery")
→ PhoenixGalleryView
→ GalleryThumbnailArea
→ GalleryController
→ ImageLoader
```

Relevante Dateien:

```text
controllers/gallery_controller.py
controllers/gallery_image_loader.py
widgets/phoenix/views/gallery_view.py
widgets/phoenix/gallery/thumbnail_area.py
widgets/phoenix/gallery/thumbnail_widget.py
```

## Finale Root Cause des Galerie-Hangs

Der reale produktive Galeriepfad lud beim Öffnen synchron Bildmetadaten und Bilddaten im Tk-Mainthread.

Gemessen:

```text
GalleryController.__init__
→ refresh
→ ImageLoader.load_folder
→ ImageLoader._read_image
```

Acht `_read_image`-Aufrufe benötigten jeweils etwa:

```text
0.341–2.127 Sekunden
```

Gesamtdauer:

```text
load_folder=12.685732 Sekunden
```

Zusätzlich dekodierte auch die Hover-Vorschau große Bilder synchron im Tk-Mainthread.

Finale Diagnose:

```text
ROOT_CAUSE=Synchrones Laden von Bildmetadaten/Bilddaten im echten Galeriepfad
BLOCKER_ON_TK_MAIN_THREAD=YES
MODEL_REFRESH_BLOCKER=YES
HOVER_PREVIEW_BLOCKER=YES
THUMBNAIL_BLOCKER=NO
```

## Finaler Galerie-Fix

Der echte Gallery-Pfad wurde auf asynchrones Laden umgestellt.

Ergebnis:

```text
GALLERY_FIRST_PAINT_SECONDS=0.079395
REAL_GALLERY_NO_IMAGE_DECODE_ON_TK_MAIN=PASS
REAL_GALLERY_LARGE_IMAGES_ASYNC=PASS
HOVER_PREVIEW_NO_MAIN_THREAD_DECODE=PASS
SIDEBAR_RESPONSIVE_DURING_LOAD=PASS
```

Die 31 Originalbilder wurden wieder nach:

```text
C:\SnapdragonAI\output
```

zurückgestellt.

Der reale manuelle Test mit den Originalbildern bestand:

```text
START=OK
GALERIE_OEFFNEN=OK
ERSTER_AUFBAU=OK
THUMBNAILS_LADEN=OK
SIDEBAR_WAEHREND_LADEN=OK
SCROLLEN=OK
HOVER_GROSSES_BILD=OK
FENSTER_REAGIERT=OK
FREEZE=NEIN
```

Damit gilt:

```text
GALLERY_PRODUCT_MANUAL_PASS=YES
APP_FREEZE_FROM_GALLERY=RESOLVED
```

## Testbereinigung

Tests aus dem ersten falschen `PhoenixImageView`-Versuch wurden gezielt entfernt.

Bestätigt:

```text
STALE_IMAGE_VIEW_TESTS_REMOVED=YES
REAL_GALLERY_TESTS_RETAINED=YES
PRODUCT_CODE_CHANGED_THIS_CLEANUP=NO
```

Finale automatische Prüfung:

```text
PY_COMPILE=PASS
REAL_GALLERY_FOCUSED_TESTS=PASS
TEST_COUNT=17/17
```

Hinweis:

Ein vorheriger Testlauf mit dem globalen Python zeigte zwei rote Tests:

1. `TclError: invalid command name "tcl_findLibrary"`
2. einen Timingtest für den falschen `PhoenixImageView`-Pfad

Diese gehörten nicht zum finalen echten Galeriepfad. Nach Entfernung der veralteten falschen Tests bestand der relevante Satz vollständig.

## Finaler Commitumfang

Exakt fünf Dateien:

```text
controllers/gallery_controller.py
tests/test_gallery.py
widgets/phoenix/gallery/thumbnail_area.py
widgets/phoenix/gallery/thumbnail_widget.py
widgets/phoenix/views/gallery_view.py
```

Nicht enthalten:

```text
widgets/phoenix/views/image_view.py
```

Finale Prüfungen:

```text
COMMIT_SCOPE=PASS 5 FILES
PY_COMPILE=PASS
REAL_GALLERY_FOCUSED_TESTS=17/17
MANUAL_GALLERY_TEST=PASS
APP_FREEZE=NO
```

## Commit und Push – final gesichert

Mit Holgers ausdrücklicher Freigabe wurde erstellt:

```text
c6757d8aa4743e42f0aa9104c51f84cb33a86cc6
fix: keep gallery responsive with large images
```

Commitumfang:

```text
5 files changed
354 insertions
30 deletions
```

Push:

```text
49eb1de6..c6757d8a  main -> main
```

Final verifiziert:

```text
REMOTE_HEAD_AFTER=c6757d8aa4743e42f0aa9104c51f84cb33a86cc6
GALLERY_FIX_COMMIT=PASS
GALLERY_FIX_PUSH=PASS
REMOTE_MATCH=YES
```

Neuer verbindlicher Remote-Safe-Point:

```text
origin/main=c6757d8aa4743e42f0aa9104c51f84cb33a86cc6
```

## Was durch den Galerie-Fix nicht verändert wurde

Nicht betroffen:

```text
RORem / Object Removal
Photo Restore / FiDeSR
QNN/HTP
NPU-Backends
Inpainting Controller
Modelldateien
Build-/Installerlogik
```

Es wurde kein neuer Build oder Installer erstellt.

## Noch vorhandene Sicherungen / Recovery

Wichtig aufbewahren:

```text
C:\SnapdragonAI\temp\pre_baseline_reset_20260922_082939
C:\SnapdragonAI\temp\gallery_fix_verified_20260922_103408
C:\SnapdragonAI_UntrackedQuarantine_20260922_084730
backup/pre-baseline-reset-20260922
```

Der frühere lokale Image-Lab-/UI-Stand ist damit weiterhin recoverbar.

## Nächster sicherer Schritt

Nicht sofort alle alten lokalen UX-Änderungen wieder einspielen.

Zuerst vom neuen sicheren Remote-Stand ausgehen:

```text
c6757d8aa4743e42f0aa9104c51f84cb33a86cc6
```

Dann gewünschte lokale Image-Lab-Funktionen einzeln zurückholen:

```text
1. arbitrary-source-size support
2. Move/Pan
3. Progress-/Running-Status
4. Prompt-/Preset-UX
```

Nach jedem Schritt zwingender manueller Responsiveness-Test:

```text
APP_START=OK
STARTSEITE=OK
SIDEBAR=OK
GALERIE=OK
WINDOW_MOVE=OK
MINIMIZE_RESTORE=OK
MAXIMIZE=OK
IMAGE_LAB=OK
FREEZE=NO
```

Kein Featureblock darf zusammen mit mehreren anderen ungeprüft wieder eingebaut werden.

## Statusflags – 22. September 2026

```text
DATE=2026-09-22

REMOTE_MAIN=c6757d8aa4743e42f0aa9104c51f84cb33a86cc6
REMOTE_SAFE_POINT=c6757d8aa4743e42f0aa9104c51f84cb33a86cc6

GALLERY_REAL_ROUTE_IDENTIFIED=YES
GALLERY_ROOT_CAUSE_FOUND=YES
GALLERY_MAINTHREAD_BLOCK_SECONDS_BEFORE=12.685732
GALLERY_FIRST_PAINT_SECONDS_AFTER=0.079395
GALLERY_LARGE_IMAGES_ASYNC=YES
GALLERY_HOVER_MAINTHREAD_DECODE=NO
GALLERY_MANUAL_TEST=PASS
GALLERY_FOCUSED_TESTS=17/17
APP_FREEZE_FROM_GALLERY=RESOLVED

PREVIOUS_IMAGE_VIEW_FIX_INCLUDED=NO

OBJECT_REMOVAL_REMOTE_COMPLETE=YES
PHOTO_RESTORE_REMOTE_COMPLETE=YES
CPU_AI_FALLBACK=NO

PRE_BASELINE_BACKUP_EXISTS=YES
BACKUP_BRANCH_EXISTS=YES
UNTRACKED_RUNTIME_QUARANTINE_EXISTS=YES

BUILD_22_SEPTEMBER=NO
INSTALLER_22_SEPTEMBER=NO
COMMIT_22_SEPTEMBER=c6757d8aa4743e42f0aa9104c51f84cb33a86cc6
PUSH_22_SEPTEMBER=PASS

NEXT_PRIORITY=REINTRODUCE_IMAGE_LAB_UX_ONE_BLOCK_AT_A_TIME
```

## Handover-Übernahme

Diese vollständige zentrale Handover-Datei muss weiterhin exakt heißen:

```text
CHATGPT_HANDOVER.md
```

Holger übernimmt sie über:

```text
C:\Users\holge\Desktop\SnapdragonAI_Handover_Aktualisieren.cmd
```

nach:

```text
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Die vollständige historische Chronik muss erhalten bleiben.
# Ergänzung: später Tagesabschluss 22. September 2026 – FiDeSR-Performance/Qualität, RORem-Grenze und SD2-Inpainting-Ausblick

Diese Ergänzung hat für den aktuellen Git-Stand, Photo-Restore-Performance, Object-Removal-Entscheidungen und den nächsten technischen Einstieg Vorrang vor früheren Abschnitten desselben Tages. Die vollständige ältere Chronik bleibt erhalten.

## Arbeitsregeln – neu ausdrücklich bestätigt

Bei jedem künftigen Codex-/Antigravity-Sprint sichtbar angeben:

```text
TOOL: Codex / Antigravity
REASONING: GERING / MEDIUM
TOKENOPTIMIERT: GEPRÜFT
```

Zusätzlich weiterhin vor jedem Sprint:

```text
SPRINT-ZEIT
WORST CASE
SPEICHER
HARD STOP
```

Codex/Antigravity-Prompts immer als vollständigen integrierten Auftrag liefern, nicht als Nachtrag. So kurz wie möglich, aber vollständig. Holger möchte nach Prüfergebnissen ohne unnötige Rückfrage direkt den nächsten sinnvollen Schritt erhalten.

## Git-Stand am Feierabend

Aktueller bestätigter Remote-Stand:

```text
main = origin/main = 868516a3e46ce3df268914deb531b6a4c348f5f6
```

Letzte zwei heute zusätzlich veröffentlichte Commits:

```text
f059feecabe37e294a852f80a1118d8668f39111
perf: accelerate FiDeSR photo restore with serialized HTP contexts

868516a3e46ce3df268914deb531b6a4c348f5f6
quality: improve FiDeSR color fidelity and skin detail
```

Beide Pushes wurden durch `LOCAL_HEAD == REMOTE_MAIN` verifiziert.

Kein Build und kein Installer nach diesen beiden Commits.

Zuletzt sichtbare weiterhin lokale/getrackte Änderungen außerhalb der FiDeSR-Commits:

```text
controllers/inpainting_controller.py
docs/CHATGPT_HANDOVER.md
engine/backends/rorem_dlc_inpainting_adapter.py
```

Zusätzlich weiterhin bekannte untracked Dateien, darunter:

```text
tests/test_rorem_serialized_context_runtime.py
```

sowie die bereits länger bekannten Release-, Brand-, Temp-, Test- und Tool-Dateien. Niemals `git add .`; untracked/unrelated Dateien nicht beiläufig anfassen.

## Image Lab – Arbitrary Source Size lokal wiederhergestellt

Der erste alte UX-/Funktionsblock wurde kontrolliert wiederhergestellt:

```text
ARBITRARY_SIZE_RESTORED=YES
SOURCE_600x371=PASS
SOURCE_371x600=PASS
SOURCE_2048x1365=PASS
EDGE_MASK=PASS
DIRECT_1024_PATH_UNCHANGED=PASS
MODEL_INPUT_ALWAYS_1024=PASS
OUTPUT_NATIVE_SIZE=PASS
OUTSIDE_MASK_BIT_EXACT=PASS
GLOBAL_STRETCH=NO
CPU_AI_FALLBACK=NO
NPU_PRODUCT_PATH=PASS
PY_COMPILE=PASS
FOCUSED_TESTS=11/11
```

Kein UI-/Gallery-Code wurde dabei geändert.

Move/Pan, Progress-/Running-Status und Prompt-/Preset-UX wurden danach bewusst pausiert, weil zuerst die katastrophale Laufzeit von Object Removal und Photo Restore untersucht wurde.

## Object Removal / RORem – Performance-Forensik

Realer problematischer Lauf:

```text
JOB=C:\SnapdragonAI\temp\rorem_dlc_runtime\rorem_img_993e9e306b
JOB_CREATED=2026-09-22 11:07:50
MEASUREMENT=2026-09-22 11:33:42
JOB_ELAPSED=00:25:51
```

Dabei:

```text
vae_encode_source ≈ 3 s
vae_encode_masked ≈ 3 s
step_000 Graph A ≈ 6m44s
step_000 Graph B ≈ 11m29s
step_001 Graph A lief anschließend erneut minutenlang
```

Root Cause:

- Graph A und Graph B wurden produktiv als große `.dlc`-Dateien über `qnn-net-run --dlc_path` gestartet.
- Dadurch fand bei jedem Denoising-Step erneut Online-DLC-Vorbereitung/HTP-Kompilierung statt.
- Zusätzlich Prozess-Churn und große RAW-Datei-I/O.
- Nicht die eigentliche NPU-Inferenz war langsam.

### RORem Phase 1 – vorhandene serialized contexts

Vorhandene Kontexte:

```text
C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_a\graph_a.serialized.bin
2523844608 Bytes

C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_b\graph_b.serialized.bin
2706165760 Bytes
```

Produktpfad lokal auf `--retrieve_context` umgestellt.

Messung:

```text
VAE_ENCODER_SOURCE_SECONDS=4.404
VAE_ENCODER_MASKED_SECONDS=4.183
GRAPH_A_CONTEXT_AND_EXEC_SECONDS=28.323
GRAPH_B_CONTEXT_AND_EXEC_SECONDS=18.093
VAE_DECODER_SECONDS=7.139
TOTAL_1_STEP_SECONDS=108.513

PRODUCT_PERFORMANCE_BEFORE_SECONDS_PER_STEP≈1093
PRODUCT_PERFORMANCE_AFTER_SECONDS_PER_STEP≈46.416
SPEEDUP≈23.55x

CPU_AI_FALLBACK=NO
GPU_AI_FALLBACK=NO
QNN_HTP=YES
PY_COMPILE=PASS
FOCUSED_TESTS=12/12
```

Trotz 23.55× Verbesserung blieb ein vollständiger 1-Step-Lauf mit 108.5 s zu langsam.

### RORem Phase 2 – persistente Kontexte

Experiment: Graph A und Graph B gleichzeitig persistent über In-Process-QNNContext.

Ergebnis:

```text
GRAPH_A_CONTEXT_CREATED=YES
GRAPH_B_CONTEXT_CREATED=YES
GRAPH_A_INFERENCE_STARTED
GRAPH_A_INFERENCE_COMPLETED=NO
NATIVE_CRASH=YES
CRASH_CLASS=NATIVE_MEMORY_ACCESS_ERROR
PERSISTENT_AB_CONTEXT_SAFE=NO
```

Einzelkontexte wurden danach separat getestet.

Graph A:

```text
CONTEXT_CREATE=6.921s
EXEC=0.828s
RAM_BEFORE=10174.36 MB
RAM_AFTER_LOAD=12558.78 MB
RAM_AFTER_RELEASE=10003.02 MB
NATIVE_CRASH=NO
```

Graph B:

```text
CONTEXT_CREATE=10.210s
EXEC=0.950s
RAM_BEFORE=9860.74 MB
RAM_AFTER_LOAD=12282.40 MB
RAM_AFTER_RELEASE=9547.23 MB
NATIVE_CRASH=NO
```

Damit ist ein einzelner großer Kontext sicher, beide gleichzeitig auf dem 16-GB-System jedoch nicht.

### RORem sequentiell In-Process

Vollständiger 1-Step-Diagnoselauf mit:

```text
Graph A create -> execute -> release
Graph B create -> execute -> release
```

Messung:

```text
GRAPH_A_CONTEXT_CREATE_SECONDS=10.494
GRAPH_A_EXEC_SECONDS=1.583
GRAPH_A_RELEASE_SECONDS=4.601

GRAPH_B_CONTEXT_CREATE_SECONDS=11.791
GRAPH_B_EXEC_SECONDS=1.940
GRAPH_B_RELEASE_SECONDS=4.357

SEQUENTIAL_GRAPH_AB_SECONDS=35.205
TOTAL_1_STEP_SECONDS=65.799

RAM_A_PEAK_MB=12071.06
RAM_AFTER_A_RELEASE_MB=9328.71
RAM_B_PEAK_MB=11786.44
RAM_AFTER_B_RELEASE_MB=8865.82
AVAILABLE_RAM_MIN_MB=3911.68
SEVERE_PAGING=NO

FINAL_OUTPUT_VALID=YES
MEMORY_SAFETY_PASS=YES
```

Reine A+B-NPU-Inferenz war nur rund 3.5 s; Kontext-Erstellung/-Freigabe dominierte.

Entscheidung:

```text
RORem_TECH_PASS=YES
RORem_QUALITY_PASS=YES
RORem_PRODUCT_PERFORMANCE_PASS=NO
RORem_CURRENT_ARCHITECTURE_PRODUCT_VIABLE=NO
```

RORem nicht weiter mit derselben 2-Graph-Rotation optimieren.

## Photo Restore / FiDeSR – Performance-Ursache

Read-only Audit zeigte denselben grundlegenden DLC-Fehler:

- VAE Encoder, UNet, LRRB und VAE Decoder wurden mit `--dlc_path` gestartet.
- Keine FiDeSR-serialized contexts existierten.
- `--perf_profile burst` war nicht gesetzt.
- Hauptzeit ging in Online-DLC-Vorbereitung statt NPU-Ausführung.

Frühere reale Größenordnung:

```text
~321 s für 169x226 -> 672x904 / 6 Tiles
```

## FiDeSR – vier serialized HTP contexts erzeugt und bit-exakt validiert

### VAE Encoder

```text
C:\SnapdragonAI\models\photo_restore_context\fidesr_vae_encoder\fidesr_vae_encoder.serialized.bin.bin
SIZE=77647872
SHA256=9a12999304cb34d19c0c7ba03e8593c2df528628d404f6a512fb513f7e657b50
CONTEXT_RETRIEVE_SECONDS=0.5080
VAE_ENCODER_EXEC_SECONDS=0.2100
TOTAL_CONTEXT_TEST_SECONDS=1.5235
BIT_EXACT=YES
```

### UNet Merged

```text
C:\SnapdragonAI\models\photo_restore_context\fidesr_unet\fidesr_unet_merged.serialized.bin.bin
SIZE=1741705216
SHA256=3a169a72d76ce949f803d5c49da4efbb2568a7d16668b61e1344134ec28c94ae
CONTEXT_RETRIEVE_SECONDS=4.2511
UNET_EXEC_SECONDS=0.2801
TOTAL_CONTEXT_TEST_SECONDS=6.0313
BIT_EXACT=YES
```

### LRRB

```text
C:\SnapdragonAI\models\photo_restore_context\fidesr_lrrb\fidesr_lrrb.serialized.bin.bin
SIZE=1548288
SHA256=1cde7cc8979611168ee81845c4e14702dee636ccc0f683dd76fdd679b97ca9f9
CONTEXT_RETRIEVE_SECONDS=0.0416
LRRB_EXEC_SECONDS=0.0069
TOTAL_CONTEXT_TEST_SECONDS=0.5661
BIT_EXACT=YES
```

### VAE Decoder

```text
C:\SnapdragonAI\models\photo_restore_context\fidesr_vae_decoder\fidesr_vae_decoder.serialized.bin.bin
SIZE=113999872
SHA256=c9c78e694a88ef6ea4d5d7fd7af02fe7c5337f097bdacbf5d1547f66692c5d84
CONTEXT_RETRIEVE_SECONDS=0.7341
VAE_DECODER_EXEC_SECONDS=0.4558
TOTAL_CONTEXT_TEST_SECONDS=2.0803
BIT_EXACT=YES
```

Alle vier Contexts:

```text
QNN_HTP=YES
OUTPUT_VALID=YES
OUTPUT_FINITE=YES
BIT_EXACT=YES
```

WICHTIG FÜR RELEASE/PORTABILITÄT:

Diese großen generierten Context-Dateien wurden als lokale Modellartefakte erzeugt. Die Performance-Commits enthielten nur Runner-/Backend-/Testcode, nicht diese Multi-GB-Modellartefakte. Vor einem neuen Build/Installer/Release muss deshalb ausdrücklich geklärt werden, wie diese Contexts auf Fremdrechnern bereitgestellt, installiert oder erzeugt werden. Ein Remote-Code-Push allein macht Photo Restore auf einem frischen Rechner nicht automatisch vollständig.

## FiDeSR Product Runner – Performance-Fix

Geändert und committed:

```text
engine/backends/fidesr_strong_runner_template.py
engine/backends/fidesr_photo_restore_backend.py
tests/test_fidesr_serialized_context_runtime.py
```

Commit:

```text
f059feecabe37e294a852f80a1118d8668f39111
perf: accelerate FiDeSR photo restore with serialized HTP contexts
```

Tests:

```text
PY_COMPILE=PASS
FOCUSED_TESTS=53/53
DLC_PATH_USED=NO
DLC_FALLBACK_PRESENT=NO
CPU_AI_FALLBACK=NO
GPU_AI_FALLBACK=NO
QNN_HTP=YES
```

Realer End-to-End-Benchmark:

```text
INPUT=C:\Users\holge\Desktop\Testbilder\Bild1.jpg
INPUT_SIZE=169x226
OUTPUT_SIZE=672x904
TILE_COUNT=6_PER_STAGE

PREPROCESS_SECONDS=0.80
VAE_ENCODER_STAGE_SECONDS=2.96
UNET_STAGE_SECONDS=13.68
LRRB_STAGE_SECONDS=0.60
VAE_DECODER_STAGE_SECONDS=5.74
POSTPROCESS_SECONDS=5.99
TOTAL_SECONDS=29.77

BASELINE_TOTAL_SECONDS=321.02
TOTAL_SPEEDUP=10.78x
```

Damit:

```text
PHOTO_RESTORE_PRODUCT_PERFORMANCE_PASS=YES
```

## FiDeSR Quality Phase 1 – Farbe, Hauthelligkeit, Mikrodetails

Manueller Vergleich mit einer echten Farbreferenz zeigte:

- vorheriger Restore zu warm/orange,
- Haut zu hell/glatt,
- Holz zu orange,
- Bartstoppeln/Poren schwächer als Referenz.

Ermittelte Ursachen:

- unmoderierte DDColor-Chrominanz,
- Highlight-Clipping bei hoher Luminanz/Chroma,
- Wavelet-/Detailpfad verwarf bzw. nutzte echte Quellen-Hochfrequenzen zu schwach.

Minimal korrigiert:

- Soft-Knee/Moderation der warmen Chrominanz,
- sanfter Highlight-Rolloff,
- auf 4×-Skala kalibrierte deterministische Mikrodetail-Rückführung,
- keine Änderung an Neural Models, Contexts, QNN Runtime oder Tiling.

Messung:

```text
BEFORE_TOTAL_SECONDS=29.77
AFTER_TOTAL_SECONDS=17.85
COLOR_WARMTH_REDUCED=YES
SKIN_BRIGHTNESS_REDUCED=YES
MICRODETAIL_PRESERVED_BETTER=YES
HALOS_PRESENT=NO
RINGING_PRESENT=NO
TILE_SEAMS_PRESENT=NO
BLACK_FRAME_PRESENT=NO
PY_COMPILE=PASS
FOCUSED_TESTS=27/27
```

## FiDeSR Quality Phase 2 – graue Oberlider / Oberlippe

Holger bemerkte im Ergebnis:

- Oberlider grau/aschig,
- Teil der Oberlippe grau/kühl.

Root Cause:

- DDColor 256x256-Chroma-Upsampling ließ die Entsättigung von Sklera/Zähnen in schmale Haut-/Lippenübergänge bluten.
- Die globale positive-b-Absenkung aus Phase 1 verstärkte dort die lokale Entsättigung.

Korrektur:

- Soft-Knee statt pauschaler b-Absenkung,
- content-adaptive skin-adjacent Chroma-Floor,
- content-adaptive Lip-Red-Seed-Dilation,
- keine festen Pixelkoordinaten,
- keine filename-/referenzspezifische Logik.

Messung:

```text
BEFORE_TOTAL_SECONDS=17.85
AFTER_TOTAL_SECONDS=17.69

EYELID_GRAY_CAST_FIXED=YES
UPPER_LIP_GRAY_CAST_FIXED=YES
GLOBAL_ORANGE_CAST_RETURNED=NO
SKIN_OVERWARMED=NO
LIP_OVERSATURATED=NO
HALOS_PRESENT=NO
RINGING_PRESENT=NO
TILE_SEAMS_PRESENT=NO
BLACK_FRAME_PRESENT=NO

PY_COMPILE=PASS
FOCUSED_TESTS=27/27
```

Manuelle ChatGPT-Sichtprüfung des `after_phase2.png`:

- Oberlippen-Grauband deutlich/weitgehend behoben,
- globale Orangefärbung kehrte nicht zurück,
- Oberlid deutlich besser, aber noch leicht kühl/entsättigt wirkend.

Deshalb visuell nicht als absolut endgültig/perfekt dokumentieren. Technische und Generalisierungsprüfung ist bestanden; ein späterer subtiler visueller Feinschliff bleibt möglich.

## FiDeSR Generalization Check

Read-only statischer Audit:

```text
FIX_USES_PIXEL_COORDINATES=NO
FIX_USES_FILENAME_SPECIFIC_LOGIC=NO
FIX_USES_FIXED_FACE_GEOMETRY=NO
FIX_USES_REFERENCE_COLOR_HARDCODING=NO
FIX_IS_CONTENT_ADAPTIVE=YES
```

Fünf unterschiedliche Porträts wurden durch den aktuellen Product-Pfad geschickt.

Laufzeiten:

```text
Case 01: 22.53s
Case 02: 13.27s
Case 03: 17.69s
Case 04: 12.90s
Case 05: 16.37s
```

Automatisiert/diagnostisch bei allen gültigen Fällen:

```text
ORANGE_CAST=NO
SKIN_OVERWARMED=NO
SKIN_DESATURATED=NO
HALOS=NO
TILE_SEAMS=NO
BLACK_FRAME=NO
OUTPUT_VALID=YES
```

Ergebnis:

```text
GENERALIZATION_PASS=YES
PERFORMANCE_PATH_CHANGED=NO
QNN_RUNTIME_CHANGED=NO
SERIALIZED_CONTEXTS_CHANGED=NO
CPU_AI_FALLBACK=NO
GPU_AI_FALLBACK=NO
QNN_HTP=YES
```

## FiDeSR Quality Commit und Push

Commit:

```text
868516a3e46ce3df268914deb531b6a4c348f5f6
quality: improve FiDeSR color fidelity and skin detail
```

Scope exakt:

```text
engine/backends/fidesr_photo_restore_backend.py
engine/backends/fidesr_strong_runner_template.py
```

Push verifiziert:

```text
LOCAL_HEAD=868516a3e46ce3df268914deb531b6a4c348f5f6
REMOTE_MAIN=868516a3e46ce3df268914deb531b6a4c348f5f6
REMOTE_MATCH=YES
FIDESR_QUALITY_PUSH=PASS
```

## Object Removal – Alternativkandidaten

Read-only Audit identifizierte sieben Kandidaten.

### LaMa-Dilated

Technisch:

```text
QNN/HTP=YES
SINGLE_CONTEXT=YES
NPU_EXEC≈87 ms
TOTAL_PYTHON_INFERENCE≈97 ms
MEMORY_RISK=MINIMAL
```

Qualität früher schlecht: weiße/unscharfe Schmierfüllungen bei großen Personenmasken.

Ein isolierter Mask-Contract-Test prüfte, ob der Fehler nur durch falsches Hole-Filling entstand.

Ergebnis:

```text
TENSOR_DIFF_A_VS_B=0.000000
```

Das DLC enthält intern bereits:

```text
masked_image = image * (1 - mask)
```

White-hole vs zero-hole extern erzeugt daher bit-identische Tensoren.

Realbilder bestätigten weiterhin:

- smeared/unstructured fill,
- ghost contours,
- unplausible large-mask reconstruction.

Entscheidung:

```text
LAMA_PRODUCT_PATH=REJECTED
```

### AOT-GAN

Sehr schnell und klein, aber bereits qualitativ verworfen, weil auf einfachen Flächen gesichts-/augenartige Halluzinationen entstanden.

```text
AOT_GAN_PRODUCT_PATH=REJECTED
```

### SD3.5

Aktuell kein geeigneter Produktpfad:

- vorhandener DiT ist 16-channel T2I, kein nativer 33-channel Inpainting-DiT,
- VAE-Encoder-HTP scheiterte früher am Precision-Gate,
- CPU-VAE wäre wegen NPU-only-Produktziel unzulässig und ~75 s langsam,
- hoher Speicherbedarf.

```text
SD35_INPAINTING_PRODUCT_PATH=REJECTED_CURRENTLY
```

### SDXL Inpainting / RORem

Erbt dieselbe 2-Graph-/Speicherfalle wie RORem.

```text
SDXL_NATIVE_INPAINTING_CURRENT_16GB_PATH=REJECTED
```

## Neuer Object-Removal-Kandidat: native SD2 Inpainting 9-channel

Read-only Feasibility Audit:

Lokaler nativer 9-channel UNet:

```text
LOCAL_NATIVE_9CH_UNET_FOUND=NO
```

Vorhandener lokaler SD2.1-QNN-UNet:

```text
C:\SnapdragonAI\models\stable_diffusion_v2_1_qnn\unet.bin
881569792 Bytes
CHANNELS=4
REUSABLE_FOR_TRUE_INPAINTING=NO
```

Vorhandene Komponenten:

```text
TEXT_ENCODER_REUSABLE=YES (architecture; final parity still required)
VAE_ENCODER_AVAILABLE=NO
VAE_DECODER_AVAILABLE=YES
VAE_DECODER_REUSABLE=YES (architecture; final parity still required)
```

Zielmodell:

```text
native SD2 inpainting
UNet input  = [1,9,64,64]
UNet output = [1,4,64,64]
cross_attention_dim=1024
pixel resolution=512x512
```

Erwartung:

- 9-channel UNet bleibt wegen nahezu identischem Backbone wahrscheinlich ein einzelner ~840–900-MB-Kontext,
- kein 2-Graph-Split erwartet, aber noch unbewiesen,
- 16-GB-Memory-Risk deutlich niedriger als RORem.

Keine kompatiblen lokalen LCM-Assets; keine ungeprüfte LCM-4-Step-Behauptung verwenden.

## SD2 native Inpainting – Quelle

Der frühere offizielle `stabilityai`-Endpoint lieferte trotz HF-Token 404.

Verwendet wurde deshalb der öffentlich dokumentierte `sd2-community`-Mirror der ursprünglichen Stability-AI-Dateien, gepinnt auf:

```text
REVISION=5f74973c...
```

Vertrag verifiziert:

```text
PIPELINE=StableDiffusionInpaintPipeline
UNET_IN_CHANNELS=9
UNET_OUT_CHANNELS=4
CROSS_ATTENTION_DIM=1024
SAMPLE_SIZE=64
SCHEDULER=PNDM
PREDICTION_TYPE=epsilon (Diffusers default)
```

Nur minimal benötigte Dateien wurden lokal bezogen; große SHA256-Werte stimmten mit den Repository-Metadaten überein.

Lokaler Source-/Arbeitsbereich:

```text
C:\SnapdragonAI\models\sd2_inpainting_source\
C:\SnapdragonAI\temp\sd2_inpainting_export_20260922\
```

## SD2 Export – lokaler ARM64-CPU-Pfad abgebrochen

Lokaler statischer FP16-Export wurde auf ARM64 gestartet.

Problem:

- PyTorch-FP16-UNet-Ausführung praktisch single-core/langsam,
- Referenzläufe + Export-Tracing benötigen mehrere vollständige UNet-Durchläufe.

Ein einzelner Exportprozess blieb technisch stabil:

```text
PID=30360
PRIVATE_MEMORY≈2.3 GB
NO_PAGING_FAILURE
NO_NATIVE_CRASH
```

Nach mehr als 3.5 Stunden reiner CPU-Zeit existierten noch keine ONNX-/External-Data-Artefakte.

Final vor Abbruch:

```text
CPU_SECONDS_FINAL=12620.95
PRIVATE_MB_FINAL=2282.33
```

Kontrolliert beendet:

```text
EXPORT_PROCESS_TERMINATED=YES
FILES_DELETED=NO
SOURCE_MODELS_DELETED=NO
PRODUCT_FILES_CHANGED=NO
BUILD=NO
COMMIT=NO
PUSH=NO
```

Erhaltene Temp-Dateien:

```text
C:\SnapdragonAI\temp\sd2_inpainting_export_20260922\export_and_validate.py
C:\SnapdragonAI\temp\sd2_inpainting_export_20260922\validation.json
```

Wichtig:

```text
LOCAL_ARM64_EXPORT_PATH=ABGEBROCHEN_WEGEN_LAUFZEIT
TECHNISCHER_MODELLFEHLER=NICHT_NACHGEWIESEN
```

## Kaggle / Colab

Kaggle ist für Holger derzeit gesperrt und wird nicht verwendet.

Geplanter Ersatz:

```text
Google Colab GPU
```

Nur für Offline-Modellvorbereitung:

- nativen SD2-9ch-UNet statisch FP16 nach ONNX exportieren,
- passenden deterministischen VAE-Encoder exportieren,
- PyTorch-vs-ONNX-Parität prüfen,
- Artefakte als ZIP zurückholen.

Spätere Produktinferenz bleibt ausschließlich QNN/HTP/NPU.

Codex war am Ende des Tages ebenfalls wegen Nutzungslimit nicht mehr verfügbar. Deshalb wurde der Colab-Notebook-Sprint noch nicht ausgeführt.

Vorgesehener Notebook-Pfad nach nächster Codex-Verfügbarkeit:

```text
C:\SnapdragonAI\temp\sd2_inpainting_colab_export_20260922.ipynb
```

## Nächster exakter Schritt bei Wiederaufnahme

Priorität 1:

```text
TOOL: Codex
REASONING: MEDIUM
TOKENOPTIMIERT: GEPRÜFT
```

Codex soll einen vollständigen Google-Colab-GPU-Export-Notebook erstellen für:

```text
sd2-community/stable-diffusion-2-inpainting
revision 5f74973c...
```

Notebook-Ziele:

```text
/content/sd2_inpainting_export/unet/sd2_inpaint_unet.onnx
/content/sd2_inpainting_export/unet/sd2_inpaint_unet.data

/content/sd2_inpainting_export/vae_encoder/sd2_vae_encoder.onnx
(+ external data falls nötig)

/content/sd2_inpainting_export.zip
```

Pflichten:

1. CUDA/GPU prüfen.
2. Nur minimal nötige/pinned Pakete und Modellkomponenten.
3. statischer Batch-1-FP16-Export.
4. UNet-Vertrag 9->4 / 64x64 / cross-attention 1024 erhalten.
5. deterministischen VAE-Encoder exportieren, keine zufällige Sampling-Node.
6. `onnx.checker(..., full_check=True)`.
7. PyTorch-vs-ONNX-Parität für UNet und VAE.
8. Größen + SHA256 aller Artefakte ausgeben.
9. ZIP erzeugen und per Colab Download bereitstellen.
10. Noch KEIN QNN-Compile.

Nur wenn beide ONNX-Exporte und Referenzparität PASS sind:

Nächster Schritt danach = genau EIN lokaler QNN/HTP-Compile-Versuch des 9-channel UNets. Erst wenn dieser als einzelner Context funktioniert, VAE-Encoder separat kompilieren und die Wiederverwendung des vorhandenen Textencoders/Decoders per Referenzparität bestätigen.

## Tagesabschlussflags – später 22. September 2026

```text
DATE=2026-09-22

REMOTE_MAIN=868516a3e46ce3df268914deb531b6a4c348f5f6
REMOTE_MATCH=YES

APP_STABLE=YES
GALLERY_FREEZE=RESOLVED

PHOTO_RESTORE_PERFORMANCE_PASS=YES
PHOTO_RESTORE_BASELINE_SECONDS=321.02
PHOTO_RESTORE_FAST_SECONDS=29.77
PHOTO_RESTORE_QUALITY_TUNED_SECONDS=17.69
PHOTO_RESTORE_GENERALIZATION_PASS=YES
PHOTO_RESTORE_QNN_HTP_ONLY=YES
PHOTO_RESTORE_CPU_AI_FALLBACK=NO
PHOTO_RESTORE_GPU_AI_FALLBACK=NO
PHOTO_RESTORE_CONTEXT_DELIVERY_FOR_FRESH_INSTALL=OPEN

RORem_TECH_PASS=YES
RORem_QUALITY_PASS=YES
RORem_PRODUCT_PERFORMANCE_PASS=NO
RORem_CURRENT_ARCHITECTURE_PRODUCT_VIABLE=NO

LAMA_PRODUCT_PATH=REJECTED
AOT_GAN_PRODUCT_PATH=REJECTED
SD35_INPAINTING_PRODUCT_PATH=REJECTED_CURRENTLY
SDXL_INPAINTING_16GB_PATH=REJECTED

SD2_NATIVE_9CH_CANDIDATE=ACTIVE
SD2_SOURCE_CONTRACT_VERIFIED=YES
SD2_LOCAL_ARM64_EXPORT=ABORTED_FOR_RUNTIME
SD2_TECHNICAL_MODEL_FAILURE=NO
KAGGLE_AVAILABLE=NO
NEXT_EXPORT_ENVIRONMENT=GOOGLE_COLAB_GPU

BUILD_AFTER_FIDESR_COMMITS=NO
INSTALLER_AFTER_FIDESR_COMMITS=NO
NEXT_PRIORITY=CREATE_AND_RUN_SD2_INPAINTING_COLAB_GPU_EXPORT_NOTEBOOK
```

## Feierabend

Holger beendet die Arbeit für heute.

Heute keine weiteren:

```text
Tests
Exports
Builds
Installer
Commits
Pushes
Model-Compiles
```

ausführen.

# CHATGPT_HANDOVER – Ergänzung Tagesabschluss 23. September 2026 – Object Removal / SD2 / MI-GAN / RORem Performance Rescue

> Diese Ergänzung führt die vollständige bestehende Chronik fort. Ältere Abschnitte bleiben unverändert erhalten. Für Object Removal, SD2 Native Inpainting, MI-GAN, RORem-Performance, Qualcomm-AI-Hub-Artefakte und den nächsten Einstieg hat dieser Abschnitt Vorrang.
>
> Holger beendet die Arbeit am 23.09.2026 ausdrücklich für heute. Keine weiteren Tests, Compiles, Modellversuche, Builds, Commits, Pushes oder Integrationen durchführen, bis Holger die Fortsetzung vorgibt.

## Kritische Arbeitsregel nach dem 23.09.2026

- Holger entscheidet, welcher technische Weg weiterverfolgt, integriert oder veröffentlicht wird.
- ChatGPT darf nicht eigenmächtig festlegen, dass ein Pfad integriert/veröffentlicht wird oder dass die Arbeit beendet wird.
- Nach mehreren langen technischen Sackgassen gilt für neue Object-Removal-Kandidaten verbindlich: Qualitätsplausibilität zuerst, NPU-Portierung/Compile erst danach.
- Kein automatischer Wechsel auf einen neuen Modellkandidaten ohne Holgers Auftrag.
- TECH PASS, QUALITY PASS und PRODUCT PASS strikt trennen.
- Produktziel bleibt: neuronale Inferenz ausschließlich über Snapdragon NPU / QNN / HTP. CPU nur für nicht-neuronale Orchestrierung, I/O, Masken, Scheduler-/Deterministik-/Compositing-Aufgaben. Kein CPU-/GPU-AI-Produktfallback.

## Git-/Release-Stand

```text
main = origin/main = 868516a3e46ce3df268914deb531b6a4c348f5f6
FILES_CHANGED_PRODUCT=NO
BUILD=NO
INSTALLER=NO
COMMIT=NO
PUSH=NO
```

Lokale, bereits zuvor bestehende/unveröffentlichte Arbeiten dürfen weiterhin nicht verloren oder pauschal reverted werden, insbesondere soweit vorhanden:

```text
C:\SnapdragonAI\controllers\inpainting_controller.py
C:\SnapdragonAI\engine\backends\rorem_dlc_inpainting_adapter.py
C:\SnapdragonAI\tests\test_rorem_serialized_context_runtime.py
C:\SnapdragonAI\tests\test_inpainting_arbitrary_size.py
C:\SnapdragonAI\docs\CHATGPT_HANDOVER.md
```

Kein `git clean`. Niemals `git add .`.

## SD2 Native Inpainting – technischer Erfolg, visuell verworfen

Quelle:

```text
sd2-community/stable-diffusion-2-inpainting
revision 5f74973cbb64c8568780732c17f43eb269d63a0d
StableDiffusionInpaintPipeline
UNet 9 -> 4
cross_attention_dim=1024
sample_size=64
scheduler=PNDM
prediction_type=epsilon
```

Bereitgestelltes FP16-ONNX:

```text
C:\SnapdragonAI\temp\sd2_inpainting_onnx_audit_20260923\unet\model.onnx
SIZE=1732953907
SHA256=A0EBD54F7E4F926B0172B907CB7EE26DDE7ABC19054085159E2375EAC3FBBAA6
ONNX_FULL_CHECK=PASS
```

VAE Source:

```text
C:\SnapdragonAI\temp\sd2_inpainting_onnx_audit_20260923\vae_encoder\model.onnx
SIZE=68430178
SHA256=F0DA9070D007DEF0D6A4E7C10A21462BB6172E460EF2587C3FE91191397B4CEA
```

SD2 9ch UNet QNN Context:

```text
C:\SnapdragonAI\models\sd2_inpainting_qnn_candidate\unet\sd2_inpaint_unet.serialized.bin
SIZE=1741692928
SHA256=713EBACAFC87DDA342851E47F4B2F806143E272A9D65E0CA9F2F0FD23269A62D
HTP_EXEC=PASS
UNET_EXEC≈0.359s
```

Deterministischer VAE Encoder ONNX:

```text
C:\SnapdragonAI\temp\sd2_inpainting_vae_deterministic_20260923\sd2_vae_encoder_deterministic.onnx
SIZE=68427282
SHA256=522A5A15629AC0DD530C563F13F83B270AB34C40BBD2FA65D1783CBD98FA41B5
RandomNormalLike=0
ONNX_FULL_CHECK=PASS
ORT_REPRODUCIBLE=YES
```

VAE Encoder HTP Context:

```text
C:\SnapdragonAI\models\sd2_inpainting_qnn_candidate\vae_encoder\sd2_vae_encoder.serialized.bin
SIZE=76734464
SHA256=2848AF660D677A19424DBAC0144C5C3C52348905C830649E76C775C5B61B4A3F
HTP_EXEC=PASS
```

Kompletter E2E-Pfad:

```text
Text:        [1,77] int32 -> [1,77,1024]
VAE Encoder: [1,3,512,512] -> [1,4,64,64]
UNet:        [1,9,64,64] + timestep + [1,77,1024] -> [1,4,64,64]
Decoder:     [1,64,64,4] NHWC -> [1,512,512,3]
LATENT_SCALE=0.18215
TECH_GATE=PASS
OUTSIDE_MASK_BIT_EXACT=YES
CPU_AI_FALLBACK=NO
GPU_AI_FALLBACK=NO
```

Qualität:

```text
8 STEPS=FAIL
25 STEPS=FAIL
```

Drei reale Fälle zeigten weiterhin Ghosting, Halluzinationen, Struktur-/Farbfehler und sichtbare Maskennähte. Der Pipelinevertrag wurde separat vollständig auditiert und bestätigt.

```text
SD2_NATIVE_TECH_PASS=YES
SD2_NATIVE_PERFORMANCE_PASS=YES
SD2_NATIVE_QUALITY_PASS=NO
SD2_NATIVE_PRODUCT_PATH=REJECTED
```

## MI-GAN 512 Places2 – Quality-first geprüft

```text
C:\SnapdragonAI\temp\migan_quality_gate_20260923\migan.onnx
SIZE=29546882
SHA256=593EBA0B7E04730F1B61C0A3CBCA68D97D8D6A7FF5C6A44A7B9D7FCD880FC5AE
ONNX_FULL_CHECK=PASS
CODE_LICENSE=MIT
WEIGHTS_LICENSE=MIT
```

Drei reale Fälle:

```text
CASE1_PERSON=FAIL
CASE2_OBJECT=FAIL
CASE3_LARGE_MASK=FAIL
TOTAL_SECONDS=6.49
OUTSIDE_MASK_BIT_EXACT=YES
MIGAN_VISUAL_GATE=FAIL
READY_FOR_QNN_COMPILE=NO
```

Kein QNN-Compile durchgeführt.

## RORem – weiterhin einziger qualitativ bestandener Pfad

FP16-Kontexte:

```text
Graph A:
C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_a\graph_a.serialized.bin
SIZE=2523844608

Graph B:
C:\SnapdragonAI\models\rorem_mixed_qnn_context\graph_b\graph_b.serialized.bin
SIZE=2706165760
```

Bekannter sicherer sequentieller 1-Step-Pfad:

```text
TOTAL≈65.799s
GRAPH_A_CREATE≈10.494s
GRAPH_A_EXEC≈1.583s
GRAPH_A_RELEASE≈4.601s
GRAPH_B_CREATE≈11.791s
GRAPH_B_EXEC≈1.940s
GRAPH_B_RELEASE≈4.357s
GRAPH_A+B≈35.205s
MEMORY_SAFE=YES
```

Hauptproblem ist nicht die NPU-Inferenz, sondern Context Create/Release/Mapping.

## RORem Phase 3A – W8A16

Graph A scheiterte an HTP-/Conv2D-Datentypvalidierung und CPU Activation Generation / Pagefile-Speicher:

```text
Tensor 2 and 3 have mismatching datatypes
Op specific validation failed
QnnBackend_validateOpConfig failed 3110
mem alloc failed for *buffer
The paging file is too small for this operation to complete
```

```text
GRAPH_A_W8A16_COMPILE_SUCCESS=NO
GRAPH_B_W8A16_COMPILE_SUCCESS=NOT_ATTEMPTED
RORem_W8A16_PRODUCT_GATE=FAIL
```

## RORem Phase 3B – ein gemeinsamer Multi-Graph-Context

QNN 2.47 unterstützt Multi-Graph grundsätzlich:

```text
MULTIGRAPH_SUPPORTED_BY_QNN_247=YES
```

Versuch scheiterte beim Mapping des zweiten persistenten Weight-Buffers:

```text
Failed to map buffer of size 2667577344
Failed to map weights buffer to device
Could not allocate persistent weights buffer
```

```text
COMBINED_CONTEXT_CREATED=NO
RORem_COMBINED_CONTEXT_PRODUCT_GATE=FAIL
```

## RORem Source-Recovery aus Qualcomm AI Hub

Historische Jobs/Modelle:

```text
Graph A compile job=jp2wq8l6p
Graph A source model=mm66w726m
Graph B compile job=jpyxkww85
Graph B source model=mnlpx84jm
Graph B earlier failed job=jp0j8qy9g
```

Recovered Graph A:

```text
C:\SnapdragonAI\temp\rorem_onnx_recovery_20260923\graph_a\graph_a.onnx
SIZE=1651525
SHA256=795EBD07751AA36FC0DBDB82B0E913ECF4A5B19D9620488F8AB04A67B118D916

C:\SnapdragonAI\temp\rorem_onnx_recovery_20260923\graph_a\graph_a.data
SIZE=2486762880
SHA256=6749434BED0A59CDDD92E5C631224E811EEB9FDFD4B4ED500F45AFF1CF138C40
```

Recovered Graph B:

```text
C:\SnapdragonAI\temp\rorem_onnx_recovery_20260923\graph_b\graph_b.onnx
SIZE=1754950
SHA256=7F832EE699D990FCFB95BAF39605373E4013D1E96486E5F4654E679F077860CA

C:\SnapdragonAI\temp\rorem_onnx_recovery_20260923\graph_b\graph_b.data
SIZE=2662785288
SHA256=98C4CBF869DD49DE40B04E91EDE06CD69C452D0B9379D658BE9302217735371B
```

Beide `onnx.checker(full_check=True)=PASS`.

Die redundanten Recovery-ZIP-Dateien wurden später nach Verifikation auf Holgers Freigabe gelöscht. Die entpackten ONNX-/data-Dateien bleiben erhalten.

## RORem reale A8W8-Kalibrierung

Reale Fälle:

```text
CASE_1_SOURCE=C:\SnapdragonAI\temp\rorem_validation\case1_input.png
CASE_1_MASK=C:\SnapdragonAI\temp\rorem_validation\case1_mask.png
CASE_2_SOURCE=C:\SnapdragonAI\temp\rorem_validation\case2_input.png
CASE_2_MASK=C:\SnapdragonAI\temp\rorem_validation\case2_mask.png
CASE_3_SOURCE=C:\SnapdragonAI\temp\rorem_validation\case3_input.png
CASE_3_MASK=C:\SnapdragonAI\temp\rorem_validation\case3_mask.png
```

Wiederverwendet:

```text
RORemDlcRuntime._prepare_inputs
_encode_prompt
run_context
_build_unet_sample
LATENT_SCALE=0.13025
CONCAT_ORDER=noisy_latent,latent_mask,masked_image_latent
SEED=20260830
GRAPH_A_B_EXECUTED=NO
```

Kalibrierung:

```text
CALIBRATION_SAMPLE_COUNT=12
CALIBRATION_CASE_COUNT=3
CALIBRATION_TIMESTEPS=951,651,301,1
CALIBRATION_ALL_DISTINCT=YES
CALIBRATION_REAL_DATA=YES
CALIBRATION_FINITE=YES
CALIBRATION_CONTRACT_PASS=YES
```

## Qualcomm AI Hub Graph-A A8W8

```text
QAI_HUB_SDK=0.55.0
GRAPH_A_A8W8_QUANTIZE_JOB_ID=jg9zm9nqp
GRAPH_A_A8W8_QUANTIZE_STATUS=SUCCESS
QUANTIZED_MODEL_ID=mqpkx56on
QUANTIZED_MODEL_TYPE=SourceModelType.ONNX
```

Compile:

```text
COMPILE_JOB_ID=jg9zm93vp
COMPILE_STATUS=FAILED
COMPILE_OPTIONS=--target_runtime qnn_dlc
```

Fehler:

```text
[ShapeInferenceError]
DequantizeLinear ... x_scale expects tensor(float),
but received unsupported tensor(float16)
```

Quantisiertes Modell lokal:

```text
MODEL_SIZE_BYTES=1647019877
MODEL_OPSET=18
ORIGINAL_ONNX_SHA256=0EF8DAC0EB2332CE7A193C1E6E16D0DF6FE2A78D2BC94BAFCE58FCADBC5C8A4F
ORIGINAL_DATA_SHA256=AEE35D1E126CA8255FD63CEFE410365179E9B56B259E72C75160445A8ACF6586
ARCHIVE_SHA256=3893C57A85F3E708290E415BE61C0DAB94A2E05CA4237C50D1B04CAA1D792AB1
QUANTIZE_LINEAR_COUNT=3390
DEQUANTIZE_LINEAR_COUNT=3692
FP16_SCALE_COUNT=6636
FP32_SCALE_COUNT=446
DYNAMIC_SCALE_COUNT=0
```

Scale-only-Fix:

```text
PATCHED_SCALE_COUNT=3469
TOPOLOGY_CHANGED=NO
ZERO_POINTS_CHANGED=NO
QUANTIZED_VALUES_CHANGED=NO
ALL_SCALE_VALUES_EXACTLY_PRESERVED_AFTER_CAST=YES
ONNX_FULL_CHECK=FAIL
SHAPE_INFERENCE_PASS=FAIL
```

Verbleibender Blocker:

```text
QuantizeLinear receives x as tensor(float16);
opset 18 permits only tensor(float)
```

Opset-19-Test:

```text
ORIGINAL_OPSET=18
NEW_OPSET=19
Q_FP16_INPUT_LEGAL_OPSET19=YES
Q_FP16_SCALE_LEGAL_OPSET19=YES
DQ_FP16_SCALE_LEGAL_OPSET19=YES
VERSION_CONVERTER_USED=YES
NODE_COUNT_ORIGINAL=11139
NODE_COUNT_OPSET19=11139
TOPOLOGY_SEMANTICS_CHANGED=NO
WEIGHT_DATA_CHANGED=NO
SCALE_VALUES_CHANGED=NO
ZERO_POINTS_CHANGED=NO
OPSET19_ONNX_FULL_CHECK=FAIL
OPSET19_SHAPE_INFERENCE_PASS=FAIL
```

Restfehler:

```text
QuantizeLinear ... float32 x input + float16 y_scale.
Opset 19 requires both to use the same T1 type.
```

Damit:

```text
ROREM_A8W8_QUANTIZE_STATUS=SUCCESS
ROREM_A8W8_COMPILE_STATUS=FAILED_QDQ_SCHEMA
ROREM_A8W8_SCALE_ONLY_FIX=FAIL
ROREM_A8W8_OPSET19_FIX=FAIL
```

Kein weiterer QDQ-Umbau automatisch starten.

## RORem Minimum-Step-Quality-Test

1 Schritt:

```text
CASE1_TOTAL=49.924s
CASE2_TOTAL=37.915s
CASE3_TOTAL=37.173s
AVG=41.671s
CASE1_PASS=NO
CASE2_PASS=NO
CASE3_PASS=NO
```

2 Schritte:

```text
CASE1_TOTAL=65.845s
CASE2_TOTAL=61.853s
CASE3_TOTAL=61.807s
AVG=63.169s
CASE1_PASS=NO
CASE2_PASS=NO
CASE3_PASS=NO
```

3 Schritte:

```text
CASE1_TOTAL=89.391s
CASE2_TOTAL=84.694s
CASE3_TOTAL=89.366s
AVG=87.817s
CASE1_PASS=NO
CASE2_PASS=NO
CASE3_PASS=NO
```

3-Step-Ausgaben:

```text
C:\SnapdragonAI\temp\rorem_min_steps_20260923\3step\case1\case1_3step.png
C:\SnapdragonAI\temp\rorem_min_steps_20260923\3step\case2\case2_3step.png
C:\SnapdragonAI\temp\rorem_min_steps_20260923\3step\case3\case3_3step.png
```

Bekannter bisheriger Qualitätsstand:

```text
MINIMUM_ACCEPTABLE_STEPS=4_EXISTING_KNOWN_GOOD_BASELINE_NOT_RETESTED
```

Dieser 4-Step-Stand wurde am Ende des 23.09. nicht erneut gemessen.

## Bestätigte Laufzeitursache

Beispiel 3-Step Case 1:

```text
TOTAL=89.391s
GRAPH_A_LOAD_TOTAL=34.456s
GRAPH_A_EXEC_TOTAL=4.284s
GRAPH_B_LOAD_TOTAL=26.060s
GRAPH_B_EXEC_TOTAL=5.490s
OTHER=19.101s
```

Die reine Graph-A/B-NPU-Ausführung beträgt zusammen nur ca. 9.8 s; Context Loads ca. 60.5 s. Hauptproblem bleibt die große FP16-Graph-A/B-Context-Rotation.

Getestete Wege:

```text
dual FP16 residency                FAIL – native memory access
single multi-graph FP16 context    FAIL – CDSP mapping limit
W8A16                              FAIL – HTP/Conv2D + activation-generation constraints
A8W8                               QuantizeJob PASS, QDQ compile schema-invalid
1-3 denoising steps               QUALITY FAIL
```

## Object-Removal-Matrix am Tagesende

```text
RORem:
TECH PASS
QUALITY PASS beim bekannten 4-Step-Pfad
PERFORMANCE weiterhin problematisch
1-3 Steps QUALITY FAIL

LaMa:
PERFORMANCE PASS
QUALITY FAIL

AOT-GAN:
PERFORMANCE PASS
QUALITY FAIL

SD2 Native:
TECH PASS
PERFORMANCE PASS
QUALITY FAIL

MI-GAN:
QUALITY FAIL
kein QNN-Compile

SD3.5 / SDXL:
aktuell kein geeigneter 16-GB-Produktpfad
```

Gesamt:

```text
OBJECT_REMOVAL_PRODUCT_SOLUTION_FINALIZED=NO
OBJECT_REMOVAL_RUNTIME_PROBLEM_SOLVED=NO
```

## Speicherstand

Zuletzt gemeldet:

```text
FREE_GB_AFTER=14.451
AVAILABLE_RAM_MB=4298.57
```

Vor weiteren großen Downloads/Compiles zuerst freien Speicher prüfen.

## Was bei Wiederaufnahme NICHT automatisch geschehen darf

Nicht automatisch:

- RORem integrieren;
- neuen Modellkandidaten suchen;
- A8W8-QDQ weiter reparieren;
- 4-Step-RORem als Releaseentscheidung festlegen;
- Build/Installer erstellen;
- Commit/Push durchführen;
- große Temp-/Modelldateien löschen.

Holger entscheidet den nächsten Weg.

## Finale Statusflags – 23. September 2026

```text
DATE=2026-09-23
REMOTE_MAIN=868516a3e46ce3df268914deb531b6a4c348f5f6
REMOTE_MATCH=YES
PRODUCT_FILES_CHANGED_TODAY=NO
BUILD=NO
INSTALLER=NO
COMMIT=NO
PUSH=NO
SD2_NATIVE_TECH_PASS=YES
SD2_NATIVE_PERFORMANCE_PASS=YES
SD2_NATIVE_QUALITY_PASS=NO
SD2_NATIVE_PRODUCT_PATH=REJECTED
MIGAN_VISUAL_GATE=FAIL
MIGAN_QNN_COMPILE_ATTEMPTED=NO
ROREM_QUALITY_KNOWN_GOOD_4STEP=YES
ROREM_1STEP_QUALITY_PASS=NO
ROREM_2STEP_QUALITY_PASS=NO
ROREM_3STEP_QUALITY_PASS=NO
ROREM_W8A16_GATE=FAIL
ROREM_MULTIGRAPH_CONTEXT_GATE=FAIL
ROREM_SOURCE_GRAPH_A_RECOVERED=YES
ROREM_SOURCE_GRAPH_B_RECOVERED=YES
ROREM_A8W8_QUANTIZE_JOB=jg9zm9nqp
ROREM_A8W8_QUANTIZE_STATUS=SUCCESS
ROREM_A8W8_MODEL_ID=mqpkx56on
ROREM_A8W8_COMPILE_JOB=jg9zm93vp
ROREM_A8W8_COMPILE_STATUS=FAILED_QDQ_SCHEMA
ROREM_A8W8_SCALE_ONLY_FIX=FAIL
ROREM_A8W8_OPSET19_FIX=FAIL
OBJECT_REMOVAL_PRODUCT_SOLUTION_FINALIZED=NO
OBJECT_REMOVAL_RUNTIME_PROBLEM_SOLVED=NO
NEXT_PRIORITY=HOLGER_ENTSCHEIDET
```

## Feierabend 23. September 2026

Holger beendet die Arbeit nach einem langen, erneut erfolglosen Object-Removal-/Performance-Tag ausdrücklich für heute.

Heute keine weiteren Tests, Modelle, Downloads, Exporte, Quantisierungen, QNN-Compiles, Integrationen, Builds, Installer, Commits oder Pushes ausführen.

Bei Wiederaufnahme zuerst diesen neuesten Abschnitt lesen und Holgers Entscheidung zum weiteren Object-Removal-/Release-Weg abwarten.

# Ergänzung: 24. September 2026 – VERSION 2.0 RC3 Dokumentationsstand

## Release-Identität

- Sichtbare Version: `VERSION 2.0 RC3`
- `display_version`: `2.0 RC3`
- `package_version`: `2.0.0-rc.3`
- Referenz-HEAD: `868516a3e46ce3df268914deb531b6a4c348f5f6`

## Phoenix Image Lab im RC3-Release

- Phoenix Image Lab führt direkt zur AI Fotorestaurierung.
- Der sichtbare Produktpfad verwendet Faithful Restore, Dust Cleanup V4, Detailerhalt, native Multi-Tile-Verarbeitung und 4×-Ausgabe.
- Neuronale Restaurierung läuft über QNN/HTP auf der Snapdragon® NPU.
- CPU- und GPU-AI-Fallback sind nicht Bestandteil des Produktpfads.
- Graustufenbilder bleiben Graustufenbilder; Colorization und DDColor wurden aus der sichtbaren Release-Oberfläche entfernt.
- Generatives Füllen, Retusche und Object Removal sind aus dem RC3-Release-UI ausgeschlossen.
- Künstliche Microtexture und Skin-Reinjection sind nicht Bestandteil des RC3-Produktpfads.

## Dokumentation und QA

- README und Benutzerhandbücher in Deutsch, Englisch und Spanisch wurden auf denselben RC3-Funktionsumfang gebracht.
- Neue Release Notes: `docs/releases/RC3_RELEASE_NOTES.md`.
- Final Release QA: PASS mit 164 fokussierten Tests und 0 Fehlern.
- Reale Restaurierungsläufe: kleines Bild 27,42 s; großes Bild 415,14 s.
- Navigation/UI-Follow-up: 49/49 PASS.
- Locale-Follow-up: 55/55 fokussierte Tests PASS.
- Versions-Follow-up: 22/22 PASS.
- `py_compile`: PASS.
- `git diff --check`: PASS.
- Versionsupdate: PASS.
- Issue #4 ist im Code berücksichtigt; der Status des GitHub-Issues wird nicht als geschlossen behauptet.

## Sicherungen

- `C:\SnapdragonAI_BACKUP_20260924_200739`
- `C:\SnapdragonAI_BACKUP_20260924_202317`
- `C:\SnapdragonAI_BACKUP_20260924_203413`

## Status dieses Dokumentationssprints

```text
BUILD=NO
COMMIT=NO
PUSH=NO
```

# CHATGPT_HANDOVER – Ergänzung Tagesabschluss 24. September 2026 – VERSION 2.0 RC3 Build-/Packaging-Stand

Diese Ergänzung ist der **verbindliche neueste Arbeitsstand**. Bei Widersprüchen mit älteren Abschnitten gilt dieser Abschnitt.

## Datum und Release-Identität

```text
DATE=2026-09-24
VERSION=VERSION 2.0 RC3
DISPLAY_VERSION=2.0 RC3
PACKAGE_VERSION=2.0.0-rc.3
HEAD=868516a3e46ce3df268914deb531b6a4c348f5f6
ORIGIN_MAIN=868516a3e46ce3df268914deb531b6a4c348f5f6
HEAD_MATCHES_ORIGIN_MAIN=YES
```

Sichtbare Versionsanzeige rechts oben und About: `VERSION 2.0 RC3`.

## Finaler RC3-Produktumfang

Phoenix Image Lab führt im RC3-Release direkt zu **AI Fotorestaurierung**.

Enthalten:
- Faithful Photo Restore
- Dust Cleanup V4
- Source-Detail-Preservation
- native Multi-Tile-Verarbeitung
- 4× Upscaling
- QNN/HTP/NPU-only für neuronale Inferenz
- DE / EN / ES

Nicht enthalten:
- Colorization / DDColor als sichtbare Produktfunktion
- Generatives Füllen
- Retusche
- Object Removal
- künstliche Microtexture
- Skin-Reinjection

Verbindlicher deutscher Produkttext:

`Historische und Schwarz-Weiß-Fotos restaurieren, Details bewahren und hochskalieren – lokal auf der Snapdragon® NPU.`

Graustufenbilder bleiben Graustufenbilder. `auto_colorize=False`. Im aktiven RC3-Produktpfad wird kein DDColor-Context geladen und keine DDColor-Inferenz aufgerufen.

## Release-QA und reale Läufe

```text
FINAL_RELEASE_QA=PASS
FOCUSED_TESTS=164 passed / 0 failures
QNN_HTP_ONLY=YES
CPU_AI_FALLBACK=NO
GPU_AI_FALLBACK=NO

SMALL_REAL_RUN=PASS
SMALL_TOTAL_SECONDS=27.42

LARGE_REAL_RUN=PASS
LARGE_TOTAL_SECONDS=415.14

TILE_SEAMS=NO
BLACK_FRAME=NO
OOM=NO
```

Weitere bestätigte Prüfungen:
- UI-/Navigation-Follow-up: `49/49 PASS`
- Locale-Follow-up: `55/55 focused PASS`
- Versions-Follow-up: `22/22 PASS`
- Test-Harness-Fix: `60/60 PASS`
- letzter kombinierter Build-Precheck-Testscope: `39/39 PASS`
- `py_compile=PASS`
- `git diff --check=PASS`

## Sprachen, UI und Dokumentation

DE / EN / ES sind auf denselben RC3-Releaseumfang angepasst.

Aktualisiert:
- `README.md`
- `docs/CHATGPT_HANDOVER.md`
- `docs/releases/README.md`
- `docs/releases/RC3_RELEASE_NOTES.md`
- `docs/user-guide/USER_GUIDE_DE.md`
- `docs/user-guide/USER_GUIDE_EN.md`
- `docs/user-guide/USER_GUIDE_ES.md`
- `release.json`
- aktive Versions-/Brand-/Installer-Metadaten

Historische RC2B-Dokumente und RC2B-Bezüge bleiben als Historie erhalten.

Issue-Fixes #1–#4 sind in den RC3 Release Notes dokumentiert. Issue #4 wird nicht fälschlich als geschlossen bezeichnet.

## Build-/Packaging-Arbeit 24.09.2026

Der erste RC3 Build-Precheck war FAIL. Die gefundenen technischen Build-/Packaging-Blocker wurden anschließend gezielt bearbeitet.

### Build-Umgebung

Dedizierte Build-Python:

`C:\Users\holge\AppData\Local\SnapdragonAIStudioBuild\pyinstaller-6.21\Scripts\python.exe`

```text
BUILD_ENVIRONMENT=DEDICATED_WINDOWS_ARM64_PYTHON_3.11.9
BUILD_DEPENDENCIES_READY=YES
```

Die Produkt-Python-Installation wurde nicht als Ersatz-Buildumgebung missbraucht.

### FiDeSR-Portabilität

Behoben:
- kein aktiver fester Repo-Pfad `C:\SnapdragonAI`
- kein fester `C:\Qualcomm\AIStack\2.47.0.260601`-Pfad als alleiniger Runtime-Pfad
- install-/resource-relative Auflösung
- versionsoffene QNN-Discovery
- Frozen-App-kompatibler interner Runner-Dispatch statt problematischem `sys.executable runner.py`

Inferenzlogik und Mathematik wurden nicht geändert.

### RC3-Packaging

```text
PHOTO_RESTORE_PACKAGING_READY=YES
QNN_RUNTIME_PACKAGING_READY=YES
DDCOLOR_REQUIRED=NO
OBJECT_REMOVAL_REQUIRED=NO
CURRENT_GUIDES_PACKAGED=YES
RC3_RELEASE_NOTES_PACKAGED=YES
IMPORT_PRECHECK=PASS
```

Pakettiert/berücksichtigt:
- FiDeSR QNN/HTP Contexts und Hilfsressourcen
- benötigte QNN/HTP-Runtime
- qnn-net-run / HTP-Komponenten / Hexagon-Skeleton soweit benötigt
- aktuelle DE/EN/ES User Guides
- RC3 Release Notes
- keine zwingende DDColor-Abhängigkeit
- keine zwingende Object-Removal-Abhängigkeit

Ermittelte Größen:

```text
PHOTO_RESTORE_PACKAGE_SIZE_GB=1.80
QNN_RUNTIME_PACKAGE_SIZE_GB=0.022
ESTIMATED_PAYLOAD_GB=3.39_CONSERVATIVE_UPPER_BOUND
ESTIMATED_INSTALLER_GB=2.2–3.4
ESTIMATED_TEMP_BUILD_GB=10.2
RECOMMENDED_FREE_SPACE_GB=15.0
```

## Test-Harness-Befunde und Korrekturen

### Photo-Restore-Contracts

14 Fehler waren **keine Produktregression**. Ursache: `qai_appbuilder` fehlte im Test-Python-Pfad, wodurch vorhandene Mock-Kontexte nicht ausgeführt wurden.

Nach Test-Harness-Korrektur:

`PHOTO_RESTORE_CONTRACTS=14 passed / 0 failures`

### RealESRGAN Windows-Teardown

Zwei Fehler:
- `test_04_realesrgan_2x_path`
- `test_05_realesrgan_4x_path`

Ursache: offene PIL-Dateihandles verhinderten Temp-Cleanup.

Nach Test-Korrektur:

`REALESRGAN_TESTS=2 passed / 0 failures`

### Tk / About-Dialog Order-Abhängigkeit

Im kombinierten Build-Precheck gab es einen order-dependent Tk-PhotoImage-/Root-Konflikt. Der betroffene Test bestand isoliert.

Es wurde ausschließlich der Test-Harness korrigiert:

```text
RC3_TK_TEST_ISOLATION=PASS
PRODUCT_CODE_CHANGED=NO
COMBINED_PRECHECK_TESTS=39 passed / 0 failures
ISOLATED_ABOUT_TEST=PASS
ORDER_DEPENDENCY_REMAINING=NO
```

## Aktueller Build-Status am Feierabend

Der letzte Build-Precheck-Rerun meldete vor der inzwischen behobenen Tk-Testkorrektur:

```text
FIDESR_PORTABLE_RESOLUTION=YES
PHOTO_RESTORE_PACKAGING_READY=YES
QNN_RUNTIME_PACKAGING_READY=YES
CURRENT_GUIDES_PACKAGED=YES
RC3_RELEASE_NOTES_PACKAGED=YES
DDCOLOR_REQUIRED=NO
OBJECT_REMOVAL_REQUIRED=NO

FREE_SPACE_C_GB=14.639
RECOMMENDED_FREE_SPACE_GB=15.0
CURRENT_FREE_SPACE_SUFFICIENT=NO

READY_TO_BUILD=NO
```

Der Tk-Testblocker ist danach beseitigt worden. **Verbleibender praktischer Blocker ist der freie Speicher auf C:.**

Vor dem echten Build nicht auf den Minimalpuffer von 15 GiB gehen, sondern **2–3 GB zusätzlich freimachen; Ziel ≥17 GB frei**.

Nichts aus folgenden Bereichen löschen:
- `C:\SnapdragonAI`
- Modellordner
- dokumentierte Backups

## Sicherungen 24.09.2026

```text
C:\SnapdragonAI_BACKUP_20260924_200739
C:\SnapdragonAI_BACKUP_20260924_202317
C:\SnapdragonAI_BACKUP_20260924_203413
C:\SnapdragonAI_BACKUP_20260924_210305
C:\SnapdragonAI_BACKUP_20260924_214606
```

Letzte bestätigte Sicherung:

```text
BACKUP=C:\SnapdragonAI_BACKUP_20260924_214606
HEAD=868516a3e46ce3df268914deb531b6a4c348f5f6
BACKUP_OK=True
```

## Morgen – exakter Wiedereinstieg

1. `C:` auf mindestens **17 GB freien Speicher** bringen.
2. Keine Projekt-, Modell- oder Backup-Dateien löschen.
3. Finalen kurzen RC3 Build-Precheck erneut ausführen.
4. Erwartung: alle Tests/Packaging-Gates grün und `CURRENT_FREE_SPACE_SUFFICIENT=YES`.
5. Nur bei `READY_TO_BUILD=YES` den echten RC3 Frozen-App-Build freigeben.
6. Danach direkter Frozen-App-Test auf dem Entwicklungs-PC.
7. Danach Installer-Build.
8. Danach Clean-Test / Installations- und Produkttest.
9. Erst nach bestandener Abnahme und ausdrücklicher Freigabe gezielt stagen; niemals `git add .`.
10. Danach Commit, Push und Veröffentlichung separat freigeben.

## Feierabendstatus 24.09.2026

```text
BUILD=NO
INSTALLER=NO
COMMIT=NO
PUSH=NO
TECHNICAL_PACKAGING_BLOCKERS_FIXED=YES
TEST_HARNESS_BLOCKERS_FIXED=YES
CURRENT_BUILD_BLOCKER=FREE_DISK_SPACE
TARGET_FREE_SPACE_GB=>=17
NEXT_EXACT_STEP=FREE_2_TO_3_GB_ON_C_THEN_FINAL_RC3_BUILD_PRECHECK
```

Heute keine weiteren Builds, Installer, Commits oder Pushes ausführen.
