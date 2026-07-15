# R-004 – Reproducible EPContext Build

Isoliertes Forschungsprojekt zur praktischen Prüfung, ob zwei identische Builds mit ONNX Runtime `ModelCompiler` und dem lokalen QNN-2.47-Stack bitgleiche EPContext-Artefakte erzeugen.

Der Runner:

- erzeugt einen deterministischen statischen Q/DQ-Conv-Testgraphen,
- erstellt eine CPU-Referenzausgabe,
- kompiliert getrennte Builds in `build_a` und `build_b`,
- lädt beide Wrapper mit deaktiviertem CPU-Fallback,
- vergleicht Wrapper, Context-Binaries und numerische Ausgaben,
- erzeugt zwei Buildmanifeste, einen JSON-Vergleich und einen Markdown-Bericht.

Der Runner verweigert die Ausführung, sobald eines seiner Ausgabeziele bereits existiert. Dadurch werden bestehende Artefakte niemals überschrieben.

Ausführung mit dem lokal konfigurierten ARM64-Python:

```powershell
python research\r004_epcontext_reproducibility\run_experiment.py
```
