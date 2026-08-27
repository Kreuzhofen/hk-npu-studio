# Project Charter – HK NPU STUDIO

## 1. Projektvision
HK NPU STUDIO ist eine professionelle, kommerziell ausgereifte Desktop-Anwendung für lokale KI-Bildverarbeitung auf Windows 11 ARM64-Systemen mit Qualcomm Snapdragon X Prozessoren. Es handelt sich nicht um eine einfache Tkinter-Demo, sondern um eine stabile, erweiterbare und performante Software-Plattform für Entwickler und Anwender. Jede architektonische Entscheidung dient der Etablierung eines professionellen Industriestandards.

## 2. Projektziele
* **NPU-First Execution:** Maximale Beschleunigung von Modellen (wie RealESRGAN x4, Stable Diffusion, LLMs) direkt auf der Snapdragon-NPU.
* **Commercial Polish & Professional UX:** Bereitstellung eines nahtlosen, ansprechenden und konsistenten Benutzererlebnisses, das dem Anspruch einer kommerziellen Desktop-Software entspricht.
* **Modulare Plattform-Architektur:** Saubere Entkopplung von GUI-Präsentationslogik und Backend-Inferenz über standardisierte Controller und Registries.
* **Sicherheit & Integrität:** Lokale Ausführung ohne Internetzwang, Schutz privater Nutzerdaten und Vermeidung externer Abhängigkeiten.
* **Hohe Wartbarkeit:** Klar definierte Schichten, saubere Dokumentation und strikte Codierungsstandards.

## 3. Grundprinzipien
* **ARM64 First:** Entwicklung und Optimierung sind primär auf Windows ARM64 ausgerichtet.
* **Qualcomm NPU First:** Die Ausführung auf der Qualcomm NPU über QNN hat höchste Priorität.
* **QNN vor CPU:** CPU-Inferenz dient ausschließlich als Fallback bei inkompatiblen Modellen oder fehlenden Hardwaretreibern.
* **Clean Architecture & Separation of Concerns:** Strikte Aufteilung in Model, View und Controller.
* **Keine Logik in Views:** Benutzeroberflächen dienen rein der Anzeige und Interaktion; die Steuerung erfolgt über dedizierte Controller.
* **Boy Scout Rule:** Hinterlasse den Code bei jeder Bearbeitung sauberer, als du ihn vorgefunden hast (kontinuierliches Refactoring).

## 4. Qualitätsanspruch
* **Release-Qualität:** Jedes Arbeitsergebnis muss stabil, lauffähig und fehlerfrei sein. Provisorische Übergangslösungen ("Hacks") sind unzulässig.
* **Zwei-Theme-Parität:** Modifikationen am Design müssen gleichermaßen im Dark- und Light-Theme getestet und freigegeben werden.
* **Strikte Validierung:** Hardware-Erkennung und Treibervalidierung müssen robust sein, um Fehlstarts oder Abstürze zu verhindern.
* **Keine eigenmächtigen Abhängigkeiten:** Keine Installation neuer Python-Bibliotheken ohne fundierte architektonische Begründung.

## 5. Nicht-Ziele (Out of Scope)
* **Cloud-First-Ansatz:** Das Studio ist für lokale Ausführung optimiert; Cloud-Dienste sind maximal optionale Fallbacks und stehen nicht im Fokus.
* **Unterstützung klassischer AMD64-Systeme:** Keine Optimierung für x86/x64-Systeme auf Kosten der ARM64/NPU-Leistung.
* **Automatisierte Paketdownloads:** Keine automatischen Downloads oder `pip`-Installationen im Hintergrund zur Laufzeit der Anwendung.
* **Automatische Git-Veränderung:** KIs oder Skripte dürfen niemals eigenständig Commits oder Pushes im Git-Repository durchführen.
