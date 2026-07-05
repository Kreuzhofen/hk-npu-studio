# Development Standard – Snapdragon AI Studio

Dieses Dokument legt die verbindlichen Qualitäts- und Entwicklungsstandards für alle Mitwirkenden (menschliche Entwickler und KI-Modelle) fest. Die Einhaltung dieser Richtlinien ist Voraussetzung für jeden Code-Review.

---

## 1. Architektur- und Codierungsrichtlinien

### 1.1 Clean Architecture & Schichtentrennung
Der Quellcode ist strikt nach funktionalen Schichten aufzuteilen. 
* Untere Schichten (z. B. `engine/`, `modules/`) dürfen niemals obere Schichten (z. B. `gui/`, `pages/`) importieren oder von ihnen abhängig sein.
* Hardware-nahe Ausführungsdetails (z. B. QNN-Pfade, ONNX Provider) müssen gekapselt sein und dürfen nicht in Benutzeroberflächen auftauchen.

### 1.2 Controller statt View-Logik
Views (in `pages/` oder `widgets/`) dienen ausschließlich dem Aufbau der Oberfläche und der Weiterleitung von Benutzerinteraktionen.
* **Verbot:** Keine mathematischen Berechnungen, Dateisystem-Operationen, QNN-Aufrufe oder direkte Datenverarbeitung in einer View-Klasse.
* **Standard:** Alle Aktionen müssen an einen zugeordneten Controller übergeben werden (z. B. aus dem Verzeichnis [controllers/](file:///C:/SnapdragonAI/controllers/)). Der Controller manipuliert das Model, welches wiederum den Zustand speichert.

### 1.3 Boy Scout Rule
"Hinterlasse den Code sauberer, als du ihn vorgefunden hast."
* Bei jeder Bearbeitung einer Datei sollen kleinere technische Mängel (z. B. ungenutzte Imports, falsche Formatierungen, fehlende Typisierungen oder ungenaue Kommentare) direkt behoben werden.
* Größere Refactorings müssen separat als eigener Milestone geplant werden.

### 1.4 Keine Magic Numbers & Hart codierte Pfade
* Alle Modellgrößen, Skalierungsfaktoren (z. B. `x4`), Adressen und Ports müssen über Konfigurationsvariablen oder Argumente gesteuert werden.
* Globale Pfade (wie `C:\SnapdragonAI` oder `C:\Qualcomm\AIStack`) müssen über die zentrale [config.py](file:///C:/SnapdragonAI/config.py) aufgelöst werden, um die Portabilität der Anwendung auf andere Systeme zu gewährleisten.

---

## 2. UI/UX & Design-Standards

### 2.1 Commercial Polish
Snapdragon AI Studio ist kein akademischer Prototyp, sondern soll sich wie eine professionelle, kommerzielle Desktop-Anwendung anfühlen.
* Widgets müssen saubere Abstände (Padding/Margin), abgerundete Ecken und durchdachte Hover-Effekte aufweisen.
* Schriftarten müssen plattformübergreifend einheitlich geladen werden (bevorzugt "Segoe UI" auf Windows).

### 2.2 Parität von Dark & Light Theme
Das Design-System unterstützt sowohl ein dunkles als auch ein helles Theme.
* **Verpflichtung:** Jede Änderung an Widgets oder Farben muss zwingend im Dark- und Light-Theme auf visuelle Fehler, unleserliche Texte und Kontrastprobleme geprüft werden.
* Die Farben müssen dynamisch über den `ThemeManager` geladen werden. Hardcodierte Hex-Farben in Widgets sind untersagt.

---

## 3. Dependency- und Systemgovernance

### 3.1 Strict Dependency Control (Keine neuen Bibliotheken)
* Die Installation externer Bibliotheken über `pip` ist strengstens untersagt, es sei denn, es liegt eine ausdrückliche Freigabe durch den Product Owner vor.
* Es dürfen keine Bibliotheken importiert werden, die nicht in der [requirements.txt](file:///C:/SnapdragonAI/requirements.txt) definiert sind oder zur Standardbibliothek von Python gehören.

### 3.2 Git-Schutz (Niemals automatisch verändern)
* KIs und Skripte dürfen keine eigenständigen Commits, Pushes, Branch-Erstellungen oder sonstige verändernde Git-Aktionen durchführen.
* Die Versionskontrolle liegt ausschließlich in der Hand des Product Owners.

### 3.3 Verbot von Hintergrund-Downloads
* Es dürfen keine automatischen Downloads von Modellen, Binärdateien oder Programmbibliotheken aus dem Internet zur Laufzeit initiiert werden.
* Alle erforderlichen Modell- und SDK-Dateien müssen lokal im System vorhanden sein und über Konfigurationspfade aufgelöst werden.

---

## 4. Qualitätssicherung & Release-Prozesse

### 4.1 Kleine, abgeschlossene Milestones
* Entwicklungen müssen in kleine, atomare und testbare Milestones zerlegt werden. 
* Ein Milestone gilt erst dann als abgeschlossen, wenn er voll funktionsfähig ist und die Dokumentation nachgeführt wurde.

### 4.2 Syntax- und Kompilierungsprüfung (`py_compile`)
* Nach jedem Entwicklungs-Sprint muss der gesamte geänderte Python-Code auf Syntaxfehler geprüft werden.
* Hierfür ist das Python-Standardmodul `py_compile` zu nutzen:
  ```powershell
  python -m compileall -q C:\SnapdragonAI\app C:\SnapdragonAI\controllers C:\SnapdragonAI\widgets
  ```
  *(Hinweis: Für reine Governance-Sprints ohne Codeänderungen ist dieser Schritt optional).*
