# Software-Architektur – Snapdragon AI Studio

## 1. Übersicht & Schichtenmodell
Snapdragon AI Studio (Codename: **Phoenix Architecture**) basiert auf einer klaren Trennung von Benutzeroberfläche (GUI), Anwendungssteuerung (Application Layer), Ausführungs-Engine (Engine) und Hardware-Abstraktion (Backends/Modules).

```text
       [ GUI / Views ] (Präsentationsschicht)
              │
              ▼
   [ Application Controller ] (Vermittlungsschicht)
              │
              ▼
      [ Phoenix Engine ] (Ablaufsteuerung & Jobs)
        │            │
        ▼            ▼
[ Backend Registry ] [ Model Registry ]
        │            │
        ▼            ▼
  [ QNN / ONNX ] [ plugins/ ] (Inferenz & Fachfunktionen)
        │
        ▼
[ Qualcomm NPU Stack ] (Hardware-Beschleunigung)
```

---

## 2. Strukturierte Hauptkomponenten

### 2.1 Workspace-System (Workspace Framework)
Das Workspace-System wird über [PhoenixWorkspace](file:///C:/SnapdragonAI/widgets/phoenix/workspace.py) gesteuert. Es fungiert als zentraler Host für alle Seiten (`Views`) der Anwendung.
* **Dynamische Ansichtenregistrierung:** Ansichten wie `home`, `dashboard`, `plugins`, `settings`, `image`, `gallery` und `compare` werden über eine Factory-Registry (`self._view_factories`) instanziiert und geladen.
* **Layout-Grid:** Konfiguriert das Hauptfenster in Header, Sidebar, Inhaltsbereich (`content_host`) und ein optionales rechtes Aktions-Panel (`right_panel`).
* **Navigations-Handler:** Die Sidebar steuert die Umschaltung der Views über `show_view()`, ohne dass die Views selbst die globale Navigation kennen müssen.

### 2.2 MVC-Struktur & Controller-Architektur
Die Einhaltung des **Model-View-Controller (MVC)**-Entwurfsmusters ist zwingend erforderlich. Es darf **keine Anwendungs- oder Inferenzlogik in den Views** verbleiben.
* **Views (Präsentation):** Liegen in `widgets/phoenix/views/` oder `pages/`. Sie empfangen Interaktionen, leiten diese an den zugeordneten Controller weiter und zeigen den Zustand des Models an.
* **Controllers (Steuerung):** Liegen in [controllers/](file:///C:/SnapdragonAI/controllers/). Sie koordinieren den Datenfluss, laden Bilder (z. B. über den [CompareWorkspaceController](file:///C:/SnapdragonAI/controllers/compare_workspace_controller.py)) und aktualisieren das Model.
* **Models (Daten & Zustand):** Speichern den internen Zustand (z. B. [CompareWorkspaceModel](file:///C:/SnapdragonAI/controllers/compare_workspace_model.py)). Sie sind unabhängig von Tkinter-Klassen und können separat getestet werden.

### 2.3 ThemeManager
Der [ThemeManager](file:///C:/SnapdragonAI/engine/theme_manager.py) verwaltet die Farbpaletten und Darstellungsmodi der Anwendung.
* **Theme-Typen:** Unterstützt `PROFESSIONAL_DARK` (Standard) und `PROFESSIONAL_LIGHT`.
* **Farb-Mapping:** Weist UI-Elementen abstrakte Rollen zu (z. B. `background`, `surface`, `card`, `border`, `accent`, `text`).
* **Design-Richtlinie:** Alle Widgets greifen über den ThemeManager auf Farbtupel zu, statt Farbwerte fest in den Quellcode zu schreiben (z. B. `ThemeManager.color("background")`).

### 2.4 BrandManager
Der [BrandManager](file:///C:/SnapdragonAI/engine/brand_manager.py) steuert die Corporate Identity und die Marken-Assets des Produkts.
* **Metadaten:** Verwaltet Produktname (`Snapdragon AI Studio`), Version (`2.0 Preview`), Engine-Version (`Phoenix Engine 1.0`), Urheberrechtshinweise (`Holger Kreuzhofen`) und Beschreibungen.
* **Asset-Pfade:** Löst die Speicherorte für Master-Vektoren, App-Icons, Splashscreens, Header-Bilder und das About-Fenster auf.
* **Dynamische CI-Erstellung:** Passt Logos und Assets zur Laufzeit an das aktive Theme an (z. B. Erzeugung des hellen Logos per Pixel-Transformation im Light Theme).

### 2.5 IconManager
Der [IconManager](file:///C:/SnapdragonAI/resources/icons.py) abstrahiert die Benennung, das Laden und das Caching von Icons.
* **Unicode-Symbole:** Nutzt systemeigene Unicode-Symbole (z. B. für Dashboard, Plugins, Settings) als ressourcenschonende Icon-Alternative.
* **Bitmap-Caching:** Verwaltet Bildsymbole in einem Cache (`_photo_image_cache`), um redundantes Laden von Datenträgern zu verhindern.
* **DPI/Größen-Skalierung:** Bietet Methoden zur Skalierung und Anpassung an verschiedene Widget-Größen.

### 2.6 Plugin-System
Die Fachfunktionen der Anwendung sind als eigenständige Plugins implementiert (z. B. RealESRGAN x4).
* **Plugin-Ordner:** Jedes Plugin liegt in [plugins/](file:///C:/SnapdragonAI/plugins/).
* **Schnittstellen-Vertrag:** Jedes Plugin deklariert seine Fähigkeiten in einer `plugin.json` (z. B. Skill, unterstützte Backend-Kategorie, Name und ID).
* **Entkopplung:** Plugins greifen nicht direkt auf Hardware-DLLs zu, sondern beantragen benötigte Fähigkeiten (z. B. `image.upscale`) bei der Backend Registry.

---

## 3. Aktuelle Projektstruktur
Die Dateiorganisation von Snapdragon AI Studio stellt sich wie folgt dar:

```text
C:\SnapdragonAI
├── app/                  # Kernanwendung, Hauptfenster & Theme-Definition
├── assets/               # Branding-Assets (Logos, Icons, Splashscreens)
├── controllers/          # MVC-Controller und Models für Anwendungsseiten
├── dialogs/              # Modale GUI-Fenster (z. B. About-Dialog)
├── docs/                 # Dokumentationen und Berichte
├── engine/               # Ausführungs-Engine, HardwareManager & BrandManager
├── GOVERNANCE/           # Projektgovernance & Richtlinien (neu)
├── gui/                  # Legacy- und Phoenix-GUI-Adapter
├── input/                # Eingabeverzeichnisse für Rohdaten
├── models/               # KI-Modell-Dateien (z. B. .bin, .onnx) & model_manager
├── modules/              # Hilfsmodule (QNN-Wrapper, Vor- und Nachverarbeitung)
├── output/               # Ausgabeordner für fertig verarbeitete Bilder
├── pages/                # Präsentationsseiten (Dashboard, Library, etc.)
├── plugins/              # Erweiterungen (z. B. realesrgan-Plugin)
├── resources/            # IconManager, Themes und UI-Ressourcen
├── temp/                 # Temporäre Bildkacheln und Laufzeitdateien
├── tools/                # Diagnose- und Hilfswerkzeuge
├── widgets/              # Wiederverwendbare UI-Komponenten (Sidebar, Cards)
├── workflows/            # JSON-Beschreibungen für Anwendungsabläufe
├── config.py             # Zentrale Konfigurationsparameter (Pfade, Ports)
├── gui_v2.py             # Phoenix-GUI-Einstiegspunkt
├── launcher.py           # Anwendungsstarter
├── phoenix.py            # Phoenix-Umgebungs-Einstiegspunkt
└── version.py            # Versionsinformationen der Anwendung
```
