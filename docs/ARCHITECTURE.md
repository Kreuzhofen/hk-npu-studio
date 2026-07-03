# Snapdragon AI Studio Architecture

Created by Holger Kreuzhofen

## Codename

Phoenix Architecture

## Goal

Snapdragon AI Studio wird von einer fensterbasierten Anwendung zu einer modularen Seiten-Anwendung umgebaut.

## Target Structure

```text
SnapdragonAI
├── app/
│   ├── theme.py
│   ├── application.py
│   └── navigation.py
├── pages/
│   ├── base_page.py
│   ├── dashboard.py
│   ├── generate.py
│   ├── edit.py
│   ├── library.py
│   ├── settings.py
│   └── about.py
├── widgets/
│   ├── card.py
│   ├── sidebar.py
│   ├── topbar.py
│   └── statusbar.py
├── modules/
├── plugins/
├── models/
├── assets/
├── docs/
└── version.py
```

## Layers

### Presentation

Alles, was der Benutzer sieht:
Dashboard, Generate, AI Library, Settings, About.

### Application

Navigation, Theme, Projektverwaltung, Konfiguration.

### AI Engine

Plugins, Modelle, QNN, InvokeAI, ComfyUI, Whisper, YOLO, Llama.

## Design System

Alle neuen UI-Komponenten verwenden `app/theme.py`.
