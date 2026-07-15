# R-005 – Automatisches QNN Package Qualification Gate

## Zweck

Das headless Gate prüft lokale Modellpakete vor einer Produktfreigabe. Es trennt statische Paket-Eignung, Strict Load, reale QNN-Ausführung und belegte HTP-Inferenz ausdrücklich voneinander. Die Produktanwendung und das Porting Toolkit bleiben getrennt; es gibt keine Integration in Phoenix-Views, Controller oder die produktive Generierung.

## Statusmodell

- `QUALIFIED`: alle für diesen Status definierten realen QNN-Prüfungen einschließlich Ausführung sind bestanden. R-005 vergibt diesen Status derzeit bewusst nicht allein aufgrund eines Strict Loads.
- `CONDITIONALLY_QUALIFIED`: statischer Vorcheck und unterstützte Strict-QNN-Loads sind bestanden, aber reale Ausführung beziehungsweise HTP-Nachweis fehlen.
- `REJECTED`: mindestens ein harter Ablehnungsgrund liegt vor.
- `INCOMPLETE`: die Prüfung ist ohne harten Defekt unvollständig, etwa ohne ausreichenden QNN-Nachweis.
- `ERROR`: Paket oder Manifest kann grundlegend nicht untersucht werden.

Jeder Befund enthält Code, Schweregrad, Komponente, Beschreibung und empfohlene Maßnahme. Das versionierte JSON-Schema ist deterministisch sortierbar; ein fest vorgegebener Timestamp ermöglicht bitgleichen Testoutput.

## CLI

```powershell
python tools\qnn_package_qualifier.py inspect --package models\sdxl_base
python tools\qnn_package_qualifier.py qualify --package models\stable_diffusion_v2_1 --strict
```

Mit `--output <datei>` wird derselbe JSON-Bericht gespeichert. `inspect` ist rein statisch. `qualify --strict` lädt ausschließlich bereits vorhandene QNN-EPContext-Wrapper über den zentralen Provider-Service und deaktiviert CPU-Fallback. `--allow-build` fordert nur die sichere Build-Bewertung an; R-005 startet ohne zusätzlich definierten Nachweis keinen Compiler.

## Sicherheits- und Abbruchregeln

- Externe ONNX-Gewichtsdaten werden nie geladen. ONNX-Protobuf-Dateien oberhalb von 64 MiB werden nicht geparst.
- Externe Daten werden über Metadaten und Dateigrößen geprüft; identische externe Dateien werden bei der Größenbewertung nur einmal gezählt.
- Ein statischer Fehler verhindert Strict Load und Build.
- Ein Build verlangt einen expliziten Schalter, bestandenen Vorcheck, Komponentenlimit, ausreichenden freien RAM und einen konkreten zusätzlichen Nachweis. Fehlt eines davon, bleibt er deaktiviert.
- Es gibt keine CPU-Ersatzinferenz und keine automatische Großmodellkompilierung.

## Verhältnis zu R-004

R-005 übernimmt aus R-004 die explizite QNN-EP-Geräteauswahl, Provider-Optionen und `session.disable_cpu_ep_fallback=1`. Der R-004-Research-Runner bleibt unverändert. Seine `ModelCompiler`- und Inferenzverfahren werden nicht in eine neue große Compiler-Abstraktion verschoben.

## Nachweisgrenzen und Produktfreigabe

Statische Eignung belegt Manifestkonsistenz, ONNX-Verträge, EPContext-Struktur, Context-Dateien, Größen und Risiken. Ein erfolgreicher Strict Load belegt, dass ONNX Runtime die Wrapper ohne CPU-Knotenzuweisung initialisieren kann. Er belegt noch keine Ausführung auf der NPU.

Für eine echte HTP-Produktfreigabe fehlen mindestens deterministische reale Eingaben je Komponente, erfolgreiche Session-Ausführung, QNN-Profiling-/Tracing-Nachweise für HTP, numerischer Referenzvergleich, End-to-End-Bildtest, Performance-/RAM-Grenzen und reproduzierbare Artefaktidentität. Diese Nachweise müssen auf der freigegebenen Snapdragon-X-Zielhardware erbracht werden.
