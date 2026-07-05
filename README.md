# Snapdragon AI Studio

Snapdragon AI Studio ist eine professionelle, lokale Desktop-Umgebung für KI-Bildverarbeitung und Inferenz auf ARM64-basierten Systemen. Es bietet Entwicklern und Anwendern eine integrierte Plattform zur Ausführung hochoptimierter KI-Modelle direkt auf dem Client.

## Vision

Das Ziel von Snapdragon AI Studio ist es, die Qualcomm Snapdragon X NPU über die native QNN-Engine (Qualcomm Neural Network) optimal auszureizen. Statt einer simplen Demo wird eine kommerziell ausgereifte, modulare und performante Plattform etabliert, die lokale KI-Workflows mit herausragender User Experience verbindet.

## Hauptmerkmale

* **Lokale KI-Ausführung:** Alle Modelle und Pipelines laufen zu 100 % lokal ohne Cloud-Zwang.
* **Windows 11 ARM64:** Von Grund auf optimiert für die ARM64-Architektur unter Windows 11.
* **Qualcomm Snapdragon X Optimierung:** Maximale Auslastung der Systemressourcen und Energieeffizienz der Hardware.
* **QNN-Unterstützung:** Native Hardwarebeschleunigung für Inferenz über Qualcomm Neural Network SDKs.
* **Moderne Desktop-Anwendung:** Stabile, responsive Ausführung mit Fokus auf Ausfallsicherheit und Modularität.
* **Professionelle GUI:** Ansprechendes, durchgängig gestaltetes Design mit nahtloser Dark- und Light-Theme-Umschaltung.

## Architektur

Die Anwendung basiert auf einer entkoppelten Schichtenarchitektur (Phoenix Architecture), bei der die Benutzeroberfläche (GUI) streng von der Ausführungs- und Hardware-Schicht getrennt ist. 

* Detaillierte Architekturbeschreibungen und Governanceregeln befinden sich im Ordner [GOVERNANCE/](file:///C:/SnapdragonAI/GOVERNANCE/).
* Für den Einstieg von Entwicklern und KI-Entwicklungssystemen steht das [AGENTS.md](file:///C:/SnapdragonAI/AGENTS.md) Framework zur Verfügung.

## Projektstruktur

Hier ist eine Kurzübersicht der wichtigsten Verzeichnisse:

* **[app/](file:///C:/SnapdragonAI/app/):** Kernanwendung, Anwendungssteuerung und Hauptfenster-Definitionen.
* **[controllers/](file:///C:/SnapdragonAI/controllers/):** MVC-Controller und Models zur Trennung der Inferenz- von der GUI-Logik.
* **[engine/](file:///C:/SnapdragonAI/engine/):** Kernkomponenten zur Ausführung, Hardware-Erkennung und Markenverwaltung.
* **[gui/](file:///C:/SnapdragonAI/gui/):** GUI-Adapter und Schnittstellen zur Integration der Phoenix-Seiten.
* **[resources/](file:///C:/SnapdragonAI/resources/):** Ressourcenverwaltung für Designs, Farben und Symbole (IconManager).
* **[GOVERNANCE/](file:///C:/SnapdragonAI/GOVERNANCE/):** Zentrale Richtlinien, Codierungsstandards, Roadmap und Teamrollen des Projekts.

## Entwicklung

> [!IMPORTANT]
> **Für KI-gestützte Entwicklung:** Bitte lesen Sie als ersten Schritt zwingend das Entwicklungs-Framework [AGENTS.md](file:///C:/SnapdragonAI/AGENTS.md) durch.
> 
> Die verbindlichen Architekturregeln und Codierungsrichtlinien befinden sich im Ordner [GOVERNANCE/](file:///C:/SnapdragonAI/GOVERNANCE/).

## Lizenz

Dieses Projekt befindet sich derzeit in aktiver Entwicklung.

Copyright © 2026 Holger Kreuzhofen.

Alle Rechte vorbehalten.
