# HK NPU STUDIO — VERSION 2.0 RC4

## Highlights

- **Dauerhafte Generierungseinstellungen (Schema v3)**: Sämtliche 18 Generierungsparameter (`prompt`, `negative_prompt`, `model_name`, `seed`, `steps`, `cfg_scale`, `width`, `height`, `sampler`, `scheduler`, `batch_size`, `upscale_profile`, `controlnet_enabled`, `canny_low_threshold`, `canny_high_threshold`, `controlnet_conditioning_scale`, `input_image_path`, `phoenix_boost_enabled`) werden atomar und versionssicher gespeichert. In der Benutzeroberfläche werden diese auf 18 diskrete Konfigurationsfelder und Bedienelemente abgebildet (einschließlich getrennter Regler für Canny Low- und High-Schwellenwerte). Sämtliche Einstellungen und Prompts bleiben nach dem Schließen und Neustarten der Anwendung zuverlässig erhalten.
- **Universelles Drag-and-Drop**: Vollständige Unterstützung für Drag & Drop über alle zentralen Workspaces hinweg. Dateien und Ordner inklusive Sidecar-Metadaten können direkt in die Galerie gezogen werden. Im Bildvergleich können Bilder gezielt dem linken („Original“) oder rechten („Ergebnis“) Panel zugewiesen werden. Im Prompt-Workspace können Referenzbilder (mit automatischer ControlNet-Aktivierung), Presets (`.json`) und Prompt-Dateien (`.txt`) direkt per Maus abgelegt werden.
- **Batch- / Mehrfachgenerierung**: Sequenzielle Generierung von 1 bis 99 Bildern direkt aus dem Prompt-Workspace. Transparente Fortschrittsanzeige für jeden Einzelschritt. Bei festem Seed wird der Seed pro Bild deterministisch inkrementiert (`base_seed + i`); bei Seed `-1` wird für jedes Bild ein neuer Zufalls-Seed generiert. Bei einem manuellen Abbruch bleiben alle bis dahin erzeugten Bilder erhalten und stehen sofort in der Galerie zur Verfügung.
- **Phoenix Boost – Semantischer Schutz & Veredelung**: 
  - Strikte semantische Validierung (`StructuralValidator` & `LockedSemantics`): Verhindert das Hinzufügen nicht angeforderter Objekte, Möbel, Requisiten oder Posen.
  - Lebensstufenschutz: Schützt juvenile Motive (`puppy`, `kitten`, `child`) vor unerwünschter Wandlung in adulte Kategorien (`dog`, `cat`, `adult`).
  - Wortlängenbegrenzung: Begrenzt die Erweiterung bei kurzen Prompts auf maximal 65 Wörter und deckelt lange Prompts auf maximal +25 % Zuwachs gegen Kontextdrift.
  - Deterministischer Detailpass (`PhoenixBoostQualityPass`): Mathematischer Luminanz-Filter zur gezielten Anhebung lokaler Kontraste und Schärfe. Farbton und Sättigung werden beibehalten und Helligkeitsanpassungen begrenzt, um Überschwinger an Konturkanten und Farbverschiebungen einzudämmen (keine absolute Artefaktfreiheit garantiert).
  - Sidecar-Dokumentation: Speichert Profil, Roh- und Veredelungs-Hashes in der PNG-Sidecar-Metadaten-Datei.
- **Konsolidierte Presets**: 14 optimierte Standard-Presets (`data/presets/*.json`) sind fest im Anwendungspaket enthalten und werden beim Erststart bei Bedarf automatisch in das Benutzerprofil bereitgestellt.
- **Integrierte Updatefunktion**: Automatische Prüfung auf GitHub-Releases über HTTPS, Erkennung von Vorabversionen, SHA-256-Integritätsprüfung vor dem Ausführen und Vorbereitung des Installers im Hintergrund.

## Verbesserungen

- Robuste Pfadzerlegung unter Windows (`widgets/phoenix/dnd_utils.py`): Schützt Backslashes und Sonderzeichen vor Tcl-Escape-Verlusten bei Drag & Drop.
- Autosave-Debouncing: Reaktive Sicherung geänderter Parameter bei Fokusverlust oder Anwendungsende ohne Blockierung der Benutzeroberfläche.
- Bereinigte Testisolation: Keine Kontamination von Nutzerdaten oder Einstellungsdateien während automatisierter Testläufe.
- Trennung von Stil und Inhalt: Kunst- und Foto-Termini werden bei Phoenix Boost streng getrennt; Fotobegriffe werden nicht in Gemälde-Prompts injiziert und umgekehrt.

## Enthaltene Funktionen aus RC3

- **Lokale KI-Fotorestaurierung**: Vollständig lokaler Pfad über FiDeSR Strong auf der Qualcomm Hexagon NPU mit Faithful Restore, Dust Cleanup V4, Detailerhalt und 4×-Upscaling. Die erforderlichen Modelle sind im Setup-Paket gebündelt.
- **Stable Diffusion 3.5 Medium**: Geführte Einrichtung und lokaler Inferenzpfad via QAI-AppBuilder in einer isolierten Laufzeitumgebung.
- **Snapdragon NPU-Inferenz**: QNN/HTP-Beschleunigung für kompatible Modelle (SD 1.5, SD 2.1, ControlNet Canny, FiDeSR).

## QA & Teststatus

- **RC2CleanTest Manuelle Abnahme (Bestätigt):**
  - HK NPU STUDIO startet sauber und fehlerfrei.
  - Prompt und Negative Prompt bleiben nach dem Schließen und Neustarten der Anwendung zuverlässig erhalten (**PASS**).
  - Batch-Generierung mit zwei Bildern erfolgreich durchgeführt; beide Ergebnisse erscheinen vollständig in der Galerie (**PASS**).
- **Automatisierte Regressionstests:**
  - `test_generation_settings_persistence.py`: PASS (7/7 Tests)
  - `test_universal_drag_and_drop.py`: PASS (12/12 Tests)
  - `test_expandable_prompt.py`: PASS (11/11 Tests)
  - `test_phoenix_boost_quality.py`: PASS (5/5 Tests)
  - `test_preset_manager.py`: PASS (7/7 Tests)
  - `test_application_update_service.py` & `test_update_workflow.py`: PASS (33/33 Tests)
  - `test_release_packaging.py`: PASS (13/13 Packaging-Gates)

## Bekannte Einschränkungen & Offene Punkte

- **Phoenix Boost Visuelle Qualitätsbewertung**: Die syntaktischen und semantischen Schutzregeln (`StructuralValidator`, `LockedSemantics`, Wortbegrenzung) sowie der mathematische Luminanzfilter sind durch automatisierte Regressionstests belegt. Die kontrollierte visuelle A/B-Qualitätsbewertung (Seed 42 gegen neutrale Baseline) ist eine offene Folgeaufgabe und gilt weiterhin nicht als pauschal nachgewiesen.
- **Updatefunktion Clean-Test**: Die Updatefunktion ist vollständig implementiert und mit 33 Unit-/Workflow-Tests automatisiert verifiziert. Ein vollständiger Live-Update-Lauf auf einem bereinigten Testsystem (mit echtem GitHub-Asset-Download, UAC-Elevation und Neustart) ist noch nicht unabhängig bestätigt und bleibt eine offene Abnahmeaufgabe.
- **Photo Restore Modell-Externalisierung**: Die Auslagerung der 1,94 GB großen FiDeSR-Modelle aus dem Hauptinstaller in ein separates NPU-Paket (`.smp`) wartet auf die formale Freigabe der Qualcomm AI Hub BYOM-Redistribution.
- **Code-Signatur & Windows 11 Smart App Control (SAC)**:
  - *Hintergrund*: HK NPU STUDIO bündelt wissenschaftliche Open-Source-Laufzeitbibliotheken (u. a. NumPy mit OpenBLAS, PyTorch), die upstream auf Windows ARM64 aktuell ohne kommerzielles Authenticode-Zertifikat ausgeliefert werden. Vorabversionen besitzen zudem noch kein kostenpflichtiges EV-Zertifikat.
  - *SmartScreen*: Beim ersten Ausführen kann Windows SmartScreen einen Hinweis auf einen unbekannten Herausgeber anzeigen („Weitere Informationen“ → „Trotzdem ausführen“).
  - *Smart App Control (SAC)*: Auf Systemen mit aktiviertem Smart App Control im strikten Modus **„Ein“ (Enforced)** blockiert die Windows-Codeintegrität (`ci.dll`, Event ID 3077) das Laden unsignierter Drittanbieter-DLLs (insb. `scipy_openblas-*.dll`), wodurch der Start mit einem DLL-Initialisierungsfehler abbricht.
  - *Sichere Alternativen & Transparenz*:
    - Im standardmäßigen **Evaluierungsmodus** von Smart App Control ist die Ausführung uneingeschränkt möglich.
    - Für Systeme mit dauerhaft erzwungenem Modus („Ein“) wird empfohlen, Vorabversionen in einer separaten Test-/Evaluierungsumgebung oder direkt aus dem Quellcode über die lokale Python-ARM64-Umgebung (`python gui_v2.py`) zu betreiben.
    - Eine pauschale Deaktivierung von Windows-Sicherheitsfunktionen wird ausdrücklich nicht empfohlen.
    - Für zukünftige Releases wird die Anbindung an Microsoft Trusted Signing evaluiert, um auch in strikt geschützten Umgebungen eine signierte Ausführung zu ermöglichen.
