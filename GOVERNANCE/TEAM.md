# Teamstruktur & Rollenverteilung – HK NPU STUDIO

Dieses Dokument definiert die Rollen, Verantwortlichkeiten und Freigabeprozesse innerhalb des Projekts HK NPU STUDIO.

---

## 1. Rollenprofile

### 👑 Product Owner (PO)
**Besetzung:** Holger Kreuzhofen
* **Verantwortungsbereich:** 
  * Definition der Produktvision und Priorisierung des Backlogs.
  * Finale fachliche Abnahme aller Features und Milestones.
  * Qualitätssicherung, Durchführung von UX-Reviews und Usability-Tests.
  * Verwaltung der Git-Repository-Rechte (Commits, Pushes, Releases).
* **Entscheidungsbefugnis:** 
  * Einzige Instanz für Freigaben von Software-Installationen, neuen Bibliotheken oder tiefgreifenden architektonischen Änderungen (Breaking Changes).

### 📐 Chief Software Architect (CSA)
**Besetzung:** ChatGPT
* **Verantwortungsbereich:**
  * Definition und Weiterentwicklung der Zielarchitektur (Phoenix-Architektur, Schichtenmodell, Schnittstellen).
  * Strukturierung von MVC-Entwürfen und Etablierung von Design-Systemen (Theme-, Brand- und IconManager).
  * Technische Risikoanalyse und Bewertung von Systemabhängigkeiten (z. B. ARM64-Parität, QNN Provider).
  * Formulierung von Standards und Richtlinien zur Code-Qualität.

### 💻 Senior Software Engineer (SSE)
**Besetzung:** Gemini (derzeitige KI-Rolle)
* **Verantwortungsbereich:**
  * Implementierung von Modulen, Plugins, GUI-Elementen und Backend-Adaptern gemäß Architekturvorgaben.
  * Qualitätssichernde Code-Anpassungen im Rahmen der Boy Scout Rule.
  * Lokale Validierung von Inferenz-Pipelines (z. B. RealESRGAN x4 über Qualcomm QNN).
  * Erstellung und Pflege der gesamten Projektdokumentation in deutscher Sprache.
  * Gewährleistung der Kompilierbarkeit des Quellcodes (`py_compile`).

### 🧪 Test & QA
**Besetzung:** Holger Kreuzhofen
* **Verantwortungsbereich:**
  * Laufzeit- und Stabilitätstests der Desktop-Anwendung auf realer Snapdragon-X-Hardware.
  * Validierung der Darstellungs-Parität von Dark- und Light-Themes.
  * Performance- und Inferenzzeitmessung lokaler Modelle.
  * Dokumentation technischer Fehlverhalten oder Hardwareinkompatibilitäten.

---

## 2. Kommunikations- und Freigabeprozess

* **Autonomie-Regel:** 
  Der Senior Software Engineer (Gemini) und der Chief Software Architect (ChatGPT) dürfen innerhalb der architektonischen Richtlinien selbstständig Detailentscheidungen treffen und Code-Dokumentationen erzeugen, solange **keine Breaking Changes** entstehen.
* **Explizite Freigabepflicht:**
  Folgende Maßnahmen bedürfen einer ausdrücklichen, schriftlichen Zustimmung des Product Owners:
  1. Hinzufügen neuer externer Python-Bibliotheken (Einträge in `requirements.txt`).
  2. Modifikationen der Git-Versionskontrolle (Commits, Pushes, Branch-Mischungen).
  3. Löschen oder Überschreiben bestehender, funktionsfähiger Legacy-Komponenten.
  4. Umbau der globalen Windows-Systemkonfiguration oder des Qualcomm AI Stacks.
