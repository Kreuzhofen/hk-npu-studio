# HK NPU STUDIO – Phoenix Engine
## Benutzerhandbuch – Version 2.0 RC2B

> **Unabhängiges Open-Source-Projekt für Windows auf Snapdragon.**  
> HK NPU STUDIO ist kein offizielles Produkt von Qualcomm Technologies, Inc. und wird nicht von Qualcomm gesponsert oder unterstützt.

---

## 1. Willkommen

HK NPU STUDIO ist eine Desktop-Anwendung für die lokale KI-Bildgenerierung auf Windows-11-ARM64-PCs mit Snapdragon-Prozessoren. Die **Phoenix Engine** übernimmt dabei Modellverwaltung, Vorbereitung und Ausführung der unterstützten KI-Pipelines.

RC2B legt besonderen Wert auf einen geführten Ablauf: **Installieren → Modell auswählen → Bild erzeugen.** Technische Details sollen für die normale Nutzung möglichst im Hintergrund bleiben.

Die Bildgenerierung selbst läuft lokal auf dem PC. Nach der erforderlichen Einrichtung eines Modells ist für die eigentliche Generierung grundsätzlich keine Cloud-Bildgenerierung erforderlich.

---

## 2. Systemvoraussetzungen

### Unterstützte Plattform

- Windows 11 ARM64
- Qualcomm Snapdragon X Plus oder Snapdragon X Elite als primäre Zielplattform
- Aktuelle Windows- und Qualcomm-Treiber empfohlen
- Ausreichend freier SSD-Speicher für die gewünschten Modelle

### Arbeitsspeicher und Speicherplatz

Der tatsächliche Bedarf hängt vom verwendeten Modell ab. Größere Modelle benötigen deutlich mehr Speicherplatz als die Anwendung selbst. Für Stable Diffusion 3.5 Medium werden während der Einrichtung mehrere Gigabyte heruntergeladen; der Qualcomm-Modell-Download liegt derzeit bei ungefähr **3,24 GB**, zusätzlich entstehen Installations- und Arbeitsdateien.

### Internetverbindung

Eine Internetverbindung wird benötigt, wenn erforderliche Komponenten oder Modelle erstmals heruntergeladen werden. Nach erfolgreicher Installation werden die unterstützten Bildgenerierungen lokal ausgeführt.

---

## 3. RC2B installieren

1. Lade den aktuellen ARM64-Installer aus dem offiziellen GitHub-Release von HK NPU STUDIO herunter.
2. Starte `HKNPUStudio-2.0.0-rc.2b-ARM64-Setup.exe`.
3. Folge dem Windows-Installationsassistenten.
4. Starte anschließend **HK NPU STUDIO** über das Startmenü oder die angelegte Verknüpfung.

> **Windows SmartScreen:** Bei einem nicht allgemein bekannten bzw. nicht kommerziell signierten Release kann Windows eine Warnung anzeigen. Verwende ausschließlich Installer aus dem offiziellen Projekt-Repository.

Für die normale Installation über den veröffentlichten Installer muss Python nicht separat vom Benutzer eingerichtet werden.

---

## 4. Der erste Start

RC2B führt neue Benutzer wesentlich stärker durch die Ersteinrichtung als frühere Release Candidates.

Auf der Startseite zeigt HK NPU STUDIO den aktuellen Einrichtungszustand an. Ist noch kein verwendbares Modell eingerichtet, führt die Anwendung zum Modell-Manager. Nach erfolgreicher Einrichtung wird der Bereitschaftsstatus aktualisiert und der Benutzer kann direkt zur ersten Bildgenerierung wechseln.

### Grundprinzip

1. HK NPU STUDIO starten.
2. Modell-Manager öffnen.
3. Gewünschtes unterstütztes Modell auswählen.
4. Den angebotenen Installationsablauf starten.
5. Installation und Prüfung vollständig abschließen lassen.
6. Modell aktivieren bzw. die automatische Aktivierung abwarten.
7. Zur Bildgenerierung wechseln.

Du musst für den normalen geführten Ablauf keine internen ONNX-, QNN- oder Modellkomponenten einzeln auswählen.

---

## 5. Modell-Manager

Der Modell-Manager zeigt die in HK NPU STUDIO bekannten Modelle und ihren Zustand an.

Je nach Modell und Entwicklungsstand kann ein Modell beispielsweise als installiert, nicht installiert, verfügbar oder experimentell gekennzeichnet sein.

### Installiert

Das benötigte Modellpaket wurde gefunden und erfolgreich geprüft.

### Aktiv

Das Modell ist aktuell für die Bildgenerierung ausgewählt.

### Nicht installiert

Die erforderlichen Modelldateien wurden noch nicht vollständig eingerichtet.

### Experimentell / In Entwicklung

Diese Modelle gehören nicht zum gleichen stabilen Benutzerpfad wie die freigegebenen Modelle. Experimentelle Einträge können zusätzliche Voraussetzungen besitzen oder noch nicht für den normalen Alltagsbetrieb vorgesehen sein.

> **Empfehlung:** Verwende für den Einstieg ein Modell, das im Modell-Manager ausdrücklich als verfügbar und unterstützt dargestellt wird.

---

## 6. Modelle installieren

RC2B verwendet je nach Modell unterschiedliche Quellen und Installationswege. Der Modell-Manager versucht, diese Unterschiede vor dem Benutzer zu verbergen und einen geführten Ablauf anzubieten.

### Stable Diffusion 1.5

Stable Diffusion 1.5 ist ein kompakter Einstieg in die lokale Bildgenerierung und eignet sich besonders für schnelle 512×512-Workflows. Bei einer unterstützten NPU-Variante übernimmt Phoenix die erforderliche Paketprüfung und Aktivierung.

### Stable Diffusion 2.1

Stable Diffusion 2.1 steht ebenfalls als Snapdragon-/Qualcomm-orientierter Bildgenerierungsweg zur Verfügung. Installation und Aktivierung erfolgen über den Modell-Manager entsprechend der für das Modell hinterlegten Quelle.

### Stable Diffusion 3.5 Medium

RC2B enthält einen deutlich stärker automatisierten Einrichtungsweg für **Stable Diffusion 3.5 Medium über Qualcomm QAI AppBuilder**. Dieser Ablauf wird im nächsten Kapitel gesondert beschrieben.

---

## 7. Stable Diffusion 3.5 Medium einrichten

Die SD3.5-Einrichtung ist umfangreicher als bei kleineren Modellpaketen. Phoenix automatisiert deshalb möglichst viele Schritte.

### Was Phoenix automatisch erledigt

Der geführte Ablauf kann:

1. das benötigte Qualcomm-QAI-AppBuilder-ZIP erkennen,
2. das Archiv vorbereiten und entpacken,
3. benötigte Python-Komponenten für die Einrichtung vorbereiten,
4. das Qualcomm-SD3.5-Skript ausführen,
5. die erforderlichen Modelldateien herunterladen,
6. die erzeugten Dateien in HK NPU STUDIO importieren,
7. Manifest und Prüfinformationen erstellen,
8. die Installation validieren,
9. das Modell anschließend aktivieren.

Währenddessen zeigt das Installationsfenster den aktuellen Schritt und den Fortschritt an.

### Qualcomm QAI AppBuilder

Für diesen Weg wird das offizielle QAI-AppBuilder-Projekt von Qualcomm verwendet. Phoenix sucht das erwartete ZIP-Archiv im Downloadbereich. Wird es nicht automatisch gefunden, kann die Anwendung zur Auswahl des ZIP-Archivs auffordern.

Die ZIP-Datei selbst wird durch den normalen Installationsvorgang nicht als Benutzerdatei gelöscht.

### Modelldownload

Das Qualcomm-Skript lädt während der Einrichtung die benötigten SD3.5-Dateien herunter. Der Download umfasst derzeit ungefähr **3,24 GB**. Geschwindigkeit und Dauer hängen von Internetverbindung, Datenträger und Systemzustand ab.

Während dieses Vorgangs HK NPU STUDIO nicht beenden und den Installationsprozess vollständig durchlaufen lassen.

### Abschluss

Nach erfolgreicher Einrichtung werden die Modelldateien geprüft und das Modell wird für HK NPU STUDIO verfügbar gemacht. Der erfolgreiche RC2B-Anwenderflow wurde als vollständige Kette getestet:

**nicht installiert → Einrichtung beim ersten Versuch → Qualcomm-Download → Import/Validierung → Aktivierung → echte Bildgenerierung.**

---

## 8. Ein Bild erzeugen

Nach Auswahl eines installierten Modells wechselst du zur Bildgenerierung.

1. Gib im Feld **Prompt** eine Beschreibung des gewünschten Bildes ein.
2. Optional kannst du einen **Negative Prompt** angeben.
3. Prüfe die gewünschten Generierungsparameter.
4. Klicke auf **Generieren**.
5. Warte, bis die Phoenix Engine die Pipeline abgeschlossen hat.
6. Das fertige Bild wird anschließend angezeigt und in den vorgesehenen Verlauf bzw. Ausgabebereich übernommen.

Die benötigte Zeit hängt stark vom Modell, der Auflösung, den Einstellungen und dem verwendeten Backend ab.

---

## 9. Prompt und Negative Prompt

### Prompt

Der Prompt beschreibt, **was im Bild erscheinen soll**.

Beispiel:

> Porträt einer Astronautin, filmische Beleuchtung, feine Details, realistischer Stil

Konkrete Angaben zu Motiv, Umgebung, Licht, Perspektive und Stil helfen dem Modell bei der Interpretation.

### Negative Prompt

Der Negative Prompt beschreibt unerwünschte Eigenschaften. Seine Wirkung hängt vom jeweiligen Modell und der Pipeline ab.

Beispiel:

> unscharf, schlechte Anatomie, Text, Wasserzeichen

---

## 10. Generierungsparameter

Je nach aktivem Modell stehen unterschiedliche Parameter zur Verfügung.

### Seed

Der Seed beeinflusst die zufällige Ausgangslage einer Generierung. Ein fester Seed erleichtert reproduzierbare Vergleiche. Ein Zufallsmodus erzeugt bei neuen Läufen unterschiedliche Ausgangszustände.

### Steps

Die Anzahl der Denoising-Schritte beeinflusst Rechenzeit und Ergebnis. Mehr Schritte bedeuten nicht automatisch ein besseres Bild.

### CFG / Guidance

Dieser Wert steuert, wie stark die Generierung dem Prompt folgen soll. Extrem hohe Werte können die Bildqualität verschlechtern.

### Auflösung

Die unterstützten Auflösungen hängen vom Modell und dessen Backend ab. Verwende bevorzugt die vom jeweiligen Modell vorgesehenen Einstellungen.

### Sampler / Scheduler

Sofern für das aktive Backend verfügbar, beeinflusst der Scheduler den Denoising-Verlauf. Nicht jede Kombination ist für jedes Modell vorgesehen.

---

## 11. Phoenix Boost

**Phoenix Boost** ist eine Funktion von HK NPU STUDIO zur Verbesserung bzw. Erweiterung von Prompts vor der Bildgenerierung.

Es gibt zwei grundsätzlich unterschiedliche Wege.

### Deterministic Boost

Der lokale deterministische Boost arbeitet ohne zusätzliches Sprachmodell. Er erweitert den Prompt nach reproduzierbaren Regeln und kann direkt verwendet werden.

### AI Boost

Der optionale AI Boost verwendet ein lokal laufendes Sprachmodell, um den Prompt intelligenter zu überarbeiten.

RC2B verwendet dafür:

- **Ollama** als lokalen Modelldienst
- **Qwen2.5 3B** als vorgesehenes lokales Sprachmodell

Ist Ollama oder Qwen noch nicht vorhanden, führt Phoenix Boost durch die erforderliche Einrichtung. Der Modelldownload kann einige Zeit dauern.

Nach erfolgreicher Installation arbeitet dieser Boost lokal auf dem Rechner. Der ursprüngliche Prompt wird nicht für eine externe Cloud-Promptoptimierung benötigt.

### Boost-Vorschau und Bearbeitung

Vor der eigentlichen Bildgenerierung bietet Phoenix Boost eine interaktive Vorschau, um den optimierten Prompt zu prüfen.

- **Kompakte Vorschau:** Eine optimierte, platzsparende Ansicht stellt die Prompts strukturiert dar.
- **Original/Optimierter Prompt nebeneinander:** Der ursprüngliche und der verbesserte Prompt werden in einer zweispaltigen Ansicht nebeneinander dargestellt.
- **Negative Prompts nebeneinander:** Auch die negativen Prompts werden nebeneinander positioniert.
- **Feste Aktionsleiste:** Die vorhandenen Aktionsschaltflächen bleiben außerhalb des Scrollbereichs erreichbar.
- **Scroll-Fallback:** Sollte der Text länger als der verfügbare Platz sein, dient ein Scrollbereich als Fallback, damit der Inhalt zugänglich bleibt.
- **Maximierbar und wiederherstellbar:** Das Vorschaufenster ist maximierbar und wieder auf die Ausgangsgröße herstellbar.

> Phoenix Boost ist optional. Die normale Bildgenerierung darf nicht davon abhängig sein, dass Ollama oder Qwen installiert ist.

---

## 12. ControlNet Canny

Bei unterstützten Modell-/Backend-Kombinationen kann **ControlNet Canny** verwendet werden, um die Struktur eines vorhandenen Bildes stärker in die neue Generierung einzubeziehen.

Typischer Ablauf:

1. ControlNet Canny aktivieren.
2. Ausgangsbild auswählen.
3. Canny-Vorschau prüfen.
4. Falls verfügbar, die Kantenschwellen anpassen.
5. Prompt eingeben.
6. Generierung starten.

ControlNet ist nicht für jede Modellvariante verfügbar. Die Oberfläche richtet sich nach den Fähigkeiten des aktiven Modells.

---

## 13. Galerie, Verlauf und Vergleich

HK NPU STUDIO stellt erzeugte Bilder innerhalb seiner Bild- und Verlaufsansichten zur weiteren Betrachtung bereit.

### Galerie und Verlauf

Die Galerie bietet eine strukturierte Übersicht über alle lokal generierten Bilder.

- **Suche, Sortierung, Thumbnail-Größe und Filter:** Du kannst die Galerie durchsuchen, Bilder anhand der angebotenen Kriterien sortieren, die Thumbnail-Größe anpassen und Filter verwenden.
- **Ausgabeordner öffnen:** Diese Schaltfläche öffnet den für den aktuellen Benutzer konfigurierten Ausgabeordner im Windows Explorer. Fehlt der Ordner, legt die Anwendung ihn sicher an.
- **Hover-Vorschau:** Der Phoenix-Schalter „Hover-Vorschau: Ein/Aus“ befindet sich neben „Ausgabeordner öffnen“.
  - **Standard Ein:** Die Hover-Vorschau ist standardmäßig aktiviert.
  - **Bei Ein:** Das Überfahren eines Bild-Thumbnails in der Galerie mit dem Mauszeiger öffnet unmittelbar die Bildvorschau.
  - **Bei Aus:** Das Überfahren eines Thumbnails öffnet keine Vorschau.
  - **Ausschalten:** Das Ausschalten der Funktion schließt eine bereits offene Vorschau.
  - **Speicherung des Status:** Die Einstellung wird dauerhaft gespeichert.
  - **Unabhängigkeit:** Bildauswahl, Doppelklick zum Öffnen und das Kontextmenü funktionieren unabhängig von dieser Einstellung.

### Bildvergleich und Metadaten-Prüfung

Mit dem integrierten Bildvergleich kannst du zwei Bilder direkt nebeneinander analysieren.

- **Bilder laden:** Du kannst das Originalbild und das Ausgabebild nebeneinander in die Vergleichsansicht laden.
- **Zoom-Optionen:** Über die gemeinsame Toolbar lassen sich die Zoomstufen *Anpassen (Fit)*, *50 %*, *100 %* und *200 %* für die Vergleichsansicht einstellen.
- **Ausschnitt verschieben (Panning):** Wenn Bilder vergrößert dargestellt werden, kann der Ausschnitt mit gedrückter linker Maustaste verschoben werden.
- **Synchron-Schalter:**
  - Bei **Synchron: Ein** werden normalisierte Pan-Positionen auf das andere Bild übertragen (synchrone Bildpositionen).
  - Bei **Synchron: Aus** bleiben die Pan-Positionen unabhängig.
- **Tauschen:** Mit einem Klick kannst du die Position der beiden geladenen Bilder vertauschen (links/rechts).
- **Generierungsmetadaten vergleichen:** Du kannst die eingebetteten Parameter der Generierung (wie Prompt, Seed, Steps etc.) beider Bilder direkt vergleichen.
  - *Wichtige Klarstellung:* Der Metadatenvergleich ist ein rein textbasierter Abgleich der technischen Erzeugungsparameter. Es handelt sich **nicht** um einen visuellen Pixelvergleich, und es werden **keine** unterschiedlichen Bildbereiche farbig hervorgehoben.
  - *Statusmeldungen:* Die Anwendung vergleicht die Metadaten präzise und unterscheidet in den Meldungen klar zwischen:
    - *Fehlenden Metadaten* (keine Metadaten in beiden Bildern vorhanden),
    - *Einseitigen Metadaten* (nur eines der Bilder enthält Metadaten),
    - *Identischen Metadaten* (beide Bilder wurden mit exakt denselben Parametern erzeugt),
    - *Unterschiedlichen Metadaten* (die Parameter weichen voneinander ab).

Die genaue Darstellung kann sich zwischen Release Candidates weiterentwickeln.

---

## 14. Sprache, Designs und Windows-Skalierung

Die Benutzeroberfläche unterstützt:

- Deutsch
- Englisch
- Spanisch

### Design-Optionen (Light & Dark)

Es stehen ein **Light Theme** (helles Design) und ein **Dark Theme** (dunkles Design) zur Verfügung. Die Sprache und das Design können jederzeit über die Anwendungseinstellungen geändert werden. Die Theme-Parität stellt sicher, dass alle Bedienelemente in beiden Farbvarianten visuell ansprechend und kontrastreich lesbar bleiben.

### Windows-Skalierung und Responsivität

Die Phoenix-Oberfläche ist für Windows-Bildschirmskalierungen von **100 % bis 175 %** optimiert.

- **Flexibler Umbruch:** Bedienelemente und Aktionsleisten passen sich dynamisch der Fenstergröße und Skalierung an. Ein automatischer Umbruch verhindert das Abschneiden von Schaltflächen.
- **Lokale Scrollbereiche:** Scrollbereiche sorgen dafür, dass Inhalte und wichtige Aktionen auch bei hoher Skalierung oder geringer Fensterhöhe erreichbar bleiben.

---

## 15. Lokale Daten und Modelle

HK NPU STUDIO speichert Anwendungseinstellungen, Arbeitsdaten und installierte Modelle lokal.

Bei einer normalen Installer-Installation können produktive Modelldaten unter dem lokalen Anwendungsbereich des Windows-Benutzers liegen, beispielsweise unter:

```text
%LOCALAPPDATA%\HK NPU STUDIO\models
```

Interne Pfade können sich zwischen Entwicklungs- und Installer-Version unterscheiden. **Verschiebe oder lösche Modelldateien nicht manuell**, solange du nicht gezielt eine Fehlerdiagnose durchführst.

Die Anwendung prüft Modellinstallationen anhand der erwarteten Dateien und Metadaten. Ein manuell unvollständig gelöschtes oder verschobenes Modell kann deshalb als ungültig erkannt werden.

---

## 16. Datenschutz und Offline-Betrieb

Das zentrale Ziel von HK NPU STUDIO ist lokale KI-Ausführung.

### Lokal

- Prompts werden für die Bildgenerierung lokal verarbeitet.
- Unterstützte Bildmodelle laufen lokal auf dem PC.
- Generierte Bilder bleiben lokal gespeichert.
- Phoenix Boost arbeitet nach Einrichtung von Ollama/Qwen lokal.

### Internet wird trotzdem teilweise benötigt

„Lokal“ bedeutet nicht, dass die komplette Einrichtung ohne Internet möglich ist. Downloads von Anwendungskomponenten, Modellen, Qualcomm-Ressourcen, Ollama oder Qwen benötigen zunächst eine Internetverbindung.

Nach erfolgreicher Einrichtung können die dafür vorgesehenen lokalen Generierungsfunktionen ohne Cloud-Bildgenerierungsdienst verwendet werden.

---

## 17. Problemlösung

### Modell wird als „Nicht installiert“ angezeigt

Öffne den Modell-Manager und verwende den vorgesehenen Installationsweg. Kopiere nicht wahllos Modelldateien in interne Ordner.

### Installation wurde unterbrochen

Starte HK NPU STUDIO erneut und öffne den Modell-Manager. Je nach Modell kann Phoenix vorhandene vollständige Daten wiederverwenden oder einen erneuten Download anbieten.

### SD3.5 meldet unvollständige Dateien

Verwende die von Phoenix angebotene erneute Einrichtung bzw. den erneuten Download. Der Installer unterscheidet zwischen vollständigen und unvollständigen Qualcomm-Ausgabedaten und soll unvollständige Quellen nicht als fertiges Modell aktivieren.

### Qwen/Phoenix Boost funktioniert nach der Installation noch nicht

Prüfe zunächst, ob Ollama vollständig gestartet wurde und Qwen2.5 3B installiert ist. Falls der lokale Ollama-Dienst gerade erst eingerichtet wurde, kann ein Neustart der betreffenden Anwendungskomponente erforderlich sein.

### Generierung dauert lange

Größere Modelle und höhere Auflösungen benötigen mehr Zeit. Auch Vorbereitung, erstmaliges Laden eines Modells und Systemauslastung beeinflussen die Dauer.

### Anwendung reagiert scheinbar nicht

Bei langen Installations- oder Generierungsphasen zunächst den angezeigten Fortschritt abwarten. Beende die Anwendung nicht während eines aktiven Modelldownloads, solange keine eindeutige Fehlermeldung vorliegt.

### Fehler melden

Bei reproduzierbaren Problemen sind folgende Angaben hilfreich:

- HK-NPU-STUDIO-Version
- Windows-Version
- Snapdragon-Gerät/Prozessor
- verwendetes Modell
- genaue Schritte bis zum Fehler
- relevante Meldung oder Screenshot
- falls vorhanden: passende Logdateien

---

## 18. Deinstallation

HK NPU STUDIO kann über die Windows-Einstellungen unter **Apps → Installierte Apps** deinstalliert werden.

Beachte: Große Modelldateien und Benutzerdaten können je nach Installations- und Speicherstrategie separat gespeichert sein. Prüfe vor einer manuellen Löschung, ob du generierte Bilder oder Modelle behalten möchtest.

---

## 19. FAQ

### Ist HK NPU STUDIO ein offizielles Qualcomm-Produkt?

Nein. HK NPU STUDIO ist ein unabhängiges Open-Source-Projekt.

### Werden meine Prompts an einen Cloud-Bilddienst gesendet?

Die unterstützte Bildgenerierung ist auf lokale Ausführung ausgelegt. Für Downloads und Einrichtung einzelner Komponenten wird jedoch eine Internetverbindung benötigt.

### Muss ich Python installieren?

Nicht für die normale Verwendung des veröffentlichten Windows-Installers. Python 3.11 ARM64 ist vor allem für Entwicklung bzw. Ausführung aus dem Quellcode relevant. Die SD3.5-Einrichtung verwaltet ihren vorgesehenen Einrichtungsweg über Phoenix.

### Muss ich Ollama installieren?

Nur wenn du den optionalen **Phoenix AI Boost** verwenden möchtest. Die normale Bildgenerierung soll auch ohne Ollama funktionieren.

### Welches Sprachmodell verwendet Phoenix AI Boost?

RC2B verwendet **Qwen2.5 3B** über Ollama.

### Muss ich für SD3.5 einzelne Qualcomm-Dateien selbst zusammensuchen?

Der RC2B-Ablauf ist darauf ausgelegt, die Qualcomm-Einrichtung weitgehend automatisch durchzuführen. Der Benutzer soll keine einzelnen internen Modellkomponenten manuell auswählen müssen.

### Kann ich Modelle einfach aus ihren Ordnern löschen?

Davon wird im normalen Betrieb abgeraten. Verwende die vorgesehenen Verwaltungs- und Installationswege. Manuelle Änderungen können dazu führen, dass gespeicherter Zustand und tatsächliche Dateien vorübergehend voneinander abweichen.

### Welche Sprachen unterstützt die Oberfläche?

Deutsch, Englisch und Spanisch.

### Kann ich HK NPU STUDIO auf Intel- oder AMD-PCs verwenden?

Das Projekt ist für Windows 11 ARM64 auf Snapdragon ausgelegt. Andere Plattformen gehören nicht zum offiziell vorgesehenen bzw. validierten Hauptziel.

---

## 20. Support und Fehlerberichte

Projekt-Repository:

`https://github.com/Kreuzhofen/hk-npu-studio`

Für reproduzierbare Fehler bitte GitHub Issues verwenden. Für allgemeine Fragen und Diskussionen kann GitHub Discussions genutzt werden, sofern für das Repository aktiviert.

Bei Fehlerberichten keine Zugangsdaten, Tokens oder andere vertrauliche Informationen in Logs oder Screenshots veröffentlichen.

---

## 21. Open Source, Lizenzen und Marken

HK NPU STUDIO wird als unabhängiges Open-Source-Projekt entwickelt. Die Anwendung selbst steht unter der im Repository angegebenen Projektlizenz. Zusätzlich gelten für verwendete Modelle, Frameworks und externe Komponenten deren jeweilige Lizenzen und Nutzungsbedingungen.

Qualcomm, Snapdragon und Hexagon sind Marken bzw. eingetragene Marken von Qualcomm Incorporated. Windows ist eine Marke von Microsoft. Weitere Marken gehören ihren jeweiligen Eigentümern.

Die Verwendung dieser Namen beschreibt technische Plattformen bzw. Kompatibilität und stellt keine offizielle Partnerschaft oder Produktzugehörigkeit dar.

---

## 22. RC2B auf einen Blick

RC2B konzentriert sich auf einen zuverlässigen und verständlichen Anwenderflow sowie eine modernisierte Oberfläche:

- **Geführte Ersteinrichtung:** Strukturierter Einstieg für neue Benutzer direkt beim ersten Start.
- **Einsteigerfreundlicher Modell-Manager:** Der Inspector bleibt scrollbar, während die Modellinstallationsleiste und ihre Aktionen erreichbar bleiben.
- **Geführte Modellquellen und Downloads:** Automatisierter Qualcomm-QAI-AppBuilder-Weg für Stable Diffusion 3.5 Medium.
- **Automatische Aktivierung:** Aktivierung des Modells unmittelbar nach erfolgreicher Installation und Validierung.
- **Status- und Fortschrittsanzeigen:** Klare Rückmeldungen während der Einrichtung und Generierung.
- **Phoenix Boost mit optionalem AI Boost:** Intelligente Prompt-Erweiterung über lokales Ollama/Qwen mit einer kompakten Boost-Vorschau (maximierbar/wiederherstellbar, nebeneinander liegende Prompts, feste Aktionsleiste und Scroll-Fallback).
- **Lokale Bildgenerierung:** Vollständig offline-fähige Ausführung auf Windows 11 ARM64 / Snapdragon.
- **Responsive Oberfläche:** Optimiert für Windows-Skalierungen von 100 % bis 175 % mit flexiblem Umbruch und lokalen Scrollbereichen.
- **Zuverlässiger Ausgabeordner:** Direktes Öffnen des Laufzeitpfades und sicheres automatisches Anlegen, falls dieser fehlt.
- **Optionale Galerie-Hover-Vorschau:** Bildvorschau beim Überfahren von Galerie-Thumbnails mit dem Mauszeiger (Schalter neben dem Ausgabeordner-Button, Status wird gespeichert, Ausschalten schließt aktive Vorschau).
- **Bildvergleich und Synchronisierung:** Gemeinsame Toolbar für Zoom (Fit, 50 %, 100 %, 200 %), Panning mit gedrückter linker Maustaste sowie synchronisiertem oder unabhängigem Verschieben (Synchron Ein/Aus).
- **Verständlicher Metadatenvergleich:** Textbasierter Abgleich der Parameter mit differenzierten Meldungen (kein visueller Pixelvergleich).

Das Ziel bleibt bewusst einfach:

> **HK NPU STUDIO installieren → Modell auswählen → Bild erzeugen.**

---

**HK NPU STUDIO – Phoenix Engine**
Holger Kreuzhofen  
Founder & Lead Developer
