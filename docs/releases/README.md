# Release-Planung & Bereitstellungsberichte

Dieses Verzeichnis dient der Ablage von Release-Checklisten, Upgrade-Anleitungen und spezifischen Deployment-Protokollen für stabile Versionen von Snapdragon AI Studio.

## Installer-Vorbereitung

Die zentrale Release-Konfiguration liegt in `release.json`. Anwendung, Branding
und Installer-Build beziehen Name, Anzeige-/Paketversion, Build, Codename,
Publisher, ARM64-Architektur und Executable-Namen aus dieser Datei.

Voraussetzungen:

1. Der paketierte ARM64-Build liegt unter
   `dist/SnapdragonAIStudio/SnapdragonAIStudio.exe`.
2. Inno Setup mit `ISCC.exe` ist installiert und über `PATH` erreichbar.

Der vorbereitete Installer wird aus dem Projektstamm gebaut:

```powershell
python tools/build_installer.py
```

Die Ausgabe wird unter `dist/installer/` erzeugt. Der Build-Schritt veröffentlicht
oder signiert das Paket nicht automatisch.
