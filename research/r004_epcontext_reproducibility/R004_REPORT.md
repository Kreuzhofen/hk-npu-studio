# R-004 – Reproducible EPContext Build

## Ergebnis

**GO** für einen SDXL-VAE-Piloten: bitgleiche Wrapper/Contexts, identische QNN-Ausgaben und CPU-Abweichung innerhalb eines Output-Quantisierungsschritts

## Testmodell

Statischer Q/DQ-Conv-Graph, Opset 13, UINT8-I/O `[1, 1, 4, 4]`, deterministische INT8-Gewichte und INT32-Bias. CPU-Referenz und QNN-Ausgaben verwenden denselben gespeicherten Testinput.

## Toolchain und Optionen

- ONNX Runtime: `1.27.0`
- onnxruntime-qnn: `2.3.0`
- QnnHtp.dll: `C:\Users\holge\AppData\Roaming\Python\Python311-arm64\site-packages\onnxruntime_qnn\QnnHtp.dll`
- Provider: ausschließlich `QNNExecutionProvider`
- Externer Context: `embed_compiled_data_into_model=False`
- Graphoptimierung: `ORT_DISABLE_ALL`
- Flags: `ERROR_IF_NO_NODES_COMPILED`, `ERROR_IF_OUTPUT_FILE_EXISTS`
- Strict Load: `session.disable_cpu_ep_fallback=1`

## Reproduzierbarkeit

| Artefakt | Build A | Build B | Gleich |
|---|---:|---:|:---:|
| Wrappergröße | 797 | 797 | True |
| Wrapper SHA-256 | `e18383d7b44318c8f330a2e1b3306175d1a5e033eb9a10acd3c2e2b6136e5867` | `e18383d7b44318c8f330a2e1b3306175d1a5e033eb9a10acd3c2e2b6136e5867` | True |
| Contextgröße | 28672 | 28672 | True |
| Context SHA-256 | `609c77a22cf67147c4491f38a12c8ea24171dee873a0af894e078fa4eebd0da9` | `609c77a22cf67147c4491f38a12c8ea24171dee873a0af894e078fa4eebd0da9` | True |

Bitgleiche Gesamtartefakte: **True**  
Wrapperstruktur identisch: **True**  
QNN-Ausgaben A/B identisch: **True**

## Genauigkeit

| Vergleich | Max. absolut | Max. relativ | Mittel absolut |
|---|---:|---:|---:|
| CPU vs Build A | 0 | 0 | 0 |
| CPU vs Build B | 0 | 0 | 0 |
| Build A vs Build B | 0 | 0 | 0 |

Die relative Maximalabweichung ist definiert als `abs(reference-candidate) / max(abs(reference), 1e-12)`.

## Strict-QNN-Nachweis

Beide Wrapper wurden mit ausschließlich `QNNExecutionProvider` geladen. CPU-Fallback war über `session.disable_cpu_ep_fallback=1` deaktiviert. Beide Sessions führten den deterministischen Testinput ohne Fallback aus.
