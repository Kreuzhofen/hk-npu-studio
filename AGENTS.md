# AI Development Framework – HK NPU STUDIO

Willkommen bei HK NPU STUDIO. Dieses Dokument dient als zentraler Einstiegspunkt für KI-Agenten und Entwicklungsmodelle (z. B. Gemini, Codex, ChatGPT). Es beschreibt den Entwicklungsprozess, Qualitätsstandards und architektonische Rahmenbedingungen.

Ziel ist ein hocheffizienter Entwicklungsprozess mit minimalem Einarbeitungskontext. Jede Entscheidung und Codeänderung muss sich an den hier festgelegten Regeln orientieren.

---

## 1. Projektidentität
* **Name:** HK NPU STUDIO
* **Codename:** Phoenix Architecture
* **Zweck:** Lokale, professionelle Desktop-Anwendung für Windows 11 ARM64 mit Qualcomm Snapdragon X NPU-Beschleunigung (über QNN).
* **Fokus:** Etablierung eines kommerziell ausgereiften Standards (keine Tkinter-Demo).
* **Details:** Siehe [PROJECT_CHARTER.md](file:///C:/SnapdragonAI/GOVERNANCE/PROJECT_CHARTER.md).

## 2. Rollen und Verantwortlichkeiten
* **Product Owner & Test/QA:** Holger Kreuzhofen (Fachentscheider und Repository-Eigentümer).
* **Chief Software Architect:** ChatGPT (Lead Developer & Software Architect) (Architekturrichtlinien und Design-Vorgaben).
* **Senior Software Engineer:** Der aktuell eingesetzte KI-Entwicklungsagent (z. B. antigravity) (Implementierung und Dokumentation).
* **Details:** Siehe [TEAM.md](file:///C:/SnapdragonAI/GOVERNANCE/TEAM.md).

## 3. Entwicklungsworkflow
Jede Entwicklungsaufgabe folgt einem festen, sequenziellen Ablauf:
1. **Analyse:** Vorhandene Projektstruktur und betroffene Dokumente/Codebestandteile analysieren.
2. **Planung:** Änderungsvorschlag und Risikobewertung formulieren.
3. **Freigabe:** Bei Codeänderungen oder strukturellen Anpassungen vorab die Zustimmung des Product Owners einholen.
4. **Umsetzung:** Code implementieren (unter Beachtung der Boy Scout Rule).
5. **Code Review:** Überprüfung der Implementierung auf Sauberkeit und Einhaltung der Codestandards.
6. **Test:** Validierung (Funktionstest, Theme-Parität, Syntaxprüfung).
7. **Dokumentation:** Projektstatus und Changelog pflegen.
8. **Details:** Siehe [DEVELOPMENT_STANDARD.md](file:///C:/SnapdragonAI/GOVERNANCE/DEVELOPMENT_STANDARD.md).

## 4. Architekturregeln
* **Schichtenmodell:** Strikte Separation von Präsentation (GUI), Anwendungssteuerung (Controller/Application) und Inferenz (Engine/Backends).
* **Schnittstellen:** Verwendung von Registries (Backend Registry, Model Registry) statt harter Kopplung.
* **MVC-Muster:** Einhaltung des Model-View-Controller-Prinzips. 
* **Details:** Siehe [ARCHITECTURE.md](file:///C:/SnapdragonAI/GOVERNANCE/ARCHITECTURE.md).

## 5. Qualitätsregeln
* **Commercial Polish:** Hoher ästhetischer und funktionaler Anspruch an alle GUI-Elemente.
* **Ausfallsicherheit:** Robuste Fehlerbehandlung und aussagekräftiges Logging.
* **Keine Behelfslösungen:** Provisorische Code-Hacks ("Workarounds") sind unzulässig.
* **Details:** Siehe [DEVELOPMENT_STANDARD.md](file:///C:/SnapdragonAI/GOVERNANCE/DEVELOPMENT_STANDARD.md).

## 6. Python-Regeln
* **ARM64 First:** Neue Python-Komponenten werden primär für Windows ARM64 entwickelt.
* **Zentralisierung:** Pfade, Modellspezifikationen und Ports werden in [config.py](file:///C:/SnapdragonAI/config.py) verwaltet. Keine Magic Numbers oder hart codierten Systempfade.
* **Syntax-Prüfung:** Nach jedem Code-Sprint ist die Kompilierung über `py_compile` zu prüfen.
* **Details:** Siehe [DEVELOPMENT_STANDARD.md](file:///C:/SnapdragonAI/GOVERNANCE/DEVELOPMENT_STANDARD.md#14-keine-magic-numbers--hart-codierte-pfade).

## 7. Theme-Regeln
* **Theme-Parität:** Änderungen an der UI müssen gleichermaßen im Dark- und Light-Theme funktionieren und visuell fehlerfrei sein.
* **Theme-Wechsel:** Theme-Wechsel dürfen keinerlei Auswirkungen auf Layout oder Funktionalität besitzen.
* **Styling-Kapselung:** Farben und Schriftarten werden ausschließlich über den `ThemeManager` aufgelöst.
* **Details:** Siehe [ARCHITECTURE.md](file:///C:/SnapdragonAI/GOVERNANCE/ARCHITECTURE.md#23-thememanager).

## 8. Autonomie des Senior Software Engineer
* **Selbstständige Detailentscheidungen:** Erlaubt für nicht-strukturelle Code-Änderungen und Dokumentationsarbeiten, solange keine *Breaking Changes* eingeführt werden.
* **Zustimmungspflichtig:** Löschen/Überschreiben von funktionierendem Code, Installation neuer Bibliotheken (pip), automatische Git-Operationen (Commit/Push) und Treibermodifikationen.
* **Details:** Siehe [TEAM.md](file:///C:/SnapdragonAI/GOVERNANCE/TEAM.md#2-kommunikations-und-freigabeprozess).

## 9. Definition of Done (DoD)
Eine Aufgabe gilt als abgeschlossen ("Done"), wenn:
1. Der Code vollständig implementiert und syntaktisch fehlerfrei kompiliert (`py_compile`).
2. Die Funktion im Dark- und Light-Theme erfolgreich getestet wurde.
3. Alle Architekturregeln aus [ARCHITECTURE.md](file:///C:/SnapdragonAI/GOVERNANCE/ARCHITECTURE.md) wurden eingehalten.
4. Keine unautorisierten externen Bibliotheken oder Git-Operationen ausgeführt wurden.
5. Alle betroffenen Dokumente aktualisiert wurden (insb. Changelog und Projektstatus).
6. Der Product Owner das Ergebnis abgenommen hat.

## 10. Governance-Referenzen
Die Detailregeln und Spezifikationen befinden sich in folgenden Dokumenten:
* **Projektvision & Prinzipien:** [PROJECT_CHARTER.md](file:///C:/SnapdragonAI/GOVERNANCE/PROJECT_CHARTER.md)
* **Plattform-Architektur & Ordnerstruktur:** [ARCHITECTURE.md](file:///C:/SnapdragonAI/GOVERNANCE/ARCHITECTURE.md)
* **Entwicklungsrichtlinien & Standards:** [DEVELOPMENT_STANDARD.md](file:///C:/SnapdragonAI/GOVERNANCE/DEVELOPMENT_STANDARD.md)
* **Produkt-Roadmap & langfristige Entwicklung:** [ROADMAP.md](file:///C:/SnapdragonAI/GOVERNANCE/ROADMAP.md)
* **Rollen & Freigaben:** [TEAM.md](file:///C:/SnapdragonAI/GOVERNANCE/TEAM.md)
* **Veröffentlichungen & Historie:** [CHANGELOG.md](file:///C:/SnapdragonAI/GOVERNANCE/CHANGELOG.md)
