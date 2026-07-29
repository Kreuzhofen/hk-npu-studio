# Snapdragon AI Studio 2.0 RC1

## Kandidat

- Anzeigeversion: `2.0 RC1`
- Paketversion: `2.0.0-rc.1`
- Build: `2026.07.29`
- Codename: `Phoenix`
- Zielarchitektur: Windows 11 ARM64
- Status: Code-Gate bestanden, nicht veröffentlicht

Die verbindlichen Werte stammen aus `release.json`.

## Automatisches RC-Gate

Am 29.07.2026 wurden 66 release-relevante Tests und 3 Subtests erfolgreich
ausgeführt. Der geprüfte End-to-End-Pfad umfasst:

- fail-safe Startdiagnose und Release-Konfiguration;
- validierte Plugin-Erkennung und atomare Plugin-Installation;
- Modell- und Anwendungsupdate mit Integritätsprüfung;
- Modellladen, Inference-Vertrag, Fehler/Abbruch und Ressourcenfreigabe;
- atomare Ausgabe-/Sidecar-Verarbeitung;
- Galerie, Asset-Index und Vergleichsansicht;
- vollständige Syntaxkompilierung von Engine, Controllern, App, Phoenix-UI,
  Versionsmodul und Release-Tools.

## Auto-Update-Vertrag

Der Update-Service akzeptiert ausschließlich ein HTTPS-Manifest mit:

```json
{
  "version": "2.0.0-rc.2",
  "architecture": "arm64",
  "package_url": "https://<update-host>/SnapdragonAIStudio.exe",
  "sha256": "<64 hex characters>"
}
```

Nur eine neuere semantische Version für ARM64 wird akzeptiert. Das Paket muss
ein HTTPS-Windows-Installer sein und wird über den resumefähigen Downloadpfad
mit verpflichtender SHA-256-Prüfung atomar bereitgestellt. Der Dienst startet
den Installer nicht selbst.

## Manuelle Freigabeschritte vor Veröffentlichung

- Produktiven ARM64-Build auf der Zielhardware erzeugen.
- Reale QNN/NPU-Generierung einschließlich Abbruch und Wiederholung prüfen.
- Installer mit `python tools/build_installer.py` kompilieren.
- Binärdateien und Installer signieren.
- Installer und Update-Manifest auf dem freigegebenen HTTPS-Endpunkt ablegen.
- Installation, Upgrade und Deinstallation auf einer sauberen Windows-11-ARM64-
  Umgebung prüfen.

Diese Schritte verändern externe Systeme beziehungsweise erzeugen den
veröffentlichten Release und wurden in Sprint 21 bewusst nicht ausgeführt.
