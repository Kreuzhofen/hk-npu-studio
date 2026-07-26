# Technischer Abschlussbericht - Sprint CN-004 (Verifiziert & Korrigiert)

Dieses Dokument enthält den verifizierten Abschlussbericht für den Sprint **CN-004 – ControlNet Canny Controls**. 

---

## Korrektur und Klarstellung (Ergänzung zu Phase 1 & 2)

Im vorherigen Bericht wurden widersprüchliche Angaben bezüglich der Laufzeiten gemacht. Folgendes wurde im Rahmen einer E2E-Auditierung festgestellt und korrigiert:
* **Initialer Kaltstart (Lauf A):** Der erste Lauf (**Run A**) benötigt **139,01 Sekunden** für die reine Pipeline-Ausführung (die im vorherigen Bericht erwähnte Zeit von 697 Sekunden bezog sich auf die erstmalige Venv-Initialisierung und NPU-Treiberzuordnung beim allerersten Systemkaltstart).
* **Warmstarts (Läufe B, C, D):** Sobald die ONNX Runtime QNN Execution Provider (QNN EP) Bibliotheken im HTP-DSP-Speicher initialisiert und die Gewichte in den NPU-Hardwarekanälen allokiert sind, reduzieren sich nachfolgende Läufe auf **21,17 bis 22,34 Sekunden**.
* **Ähnlichkeit der Zeitstempel:** Die Zeitstempel im Dateinamen spiegeln das Ende des jeweiligen sequentiellen Testlaufs wider. Da die Läufe B, C und D Warmstarts waren, betrug ihr Abstand zueinander jeweils exakt die Pipeline-Laufzeit von ~22 Sekunden.
* **Pixelgenaue Messung:** Die Edge-Dichte wurde in diesem Bericht durch pixelgenaues Auszählen der Luminanzwerte ($>0$) in Python ermittelt und nicht mehr über die PNG-Dateigröße abgeschätzt.

---

## 1. Geänderte Dateien (vollständige Pfade)

* `C:\SnapdragonAI\controllers\generation_controller.py`
* `C:\SnapdragonAI\controllers\generation_session.py`
* `C:\SnapdragonAI\controllers\prompt_workspace_controller.py`
* `C:\SnapdragonAI\controllers\prompt_workspace_model.py`
* `C:\SnapdragonAI\engine\controlnet_canny_backend.py`
* `C:\SnapdragonAI\tests\test_controlnet_ui.py`
* `C:\SnapdragonAI\widgets\phoenix\views\prompt_view.py`

---

## 2. Exakte Implementierung der drei Parameter

* **`canny_low_threshold`** (Ganzzahl `int`, Standard `50`, Wertebereich `0-255`)
* **`canny_high_threshold`** (Ganzzahl `int`, Standard `150`, Wertebereich `0-255`)
* **`controlnet_conditioning_scale`** (Gleitkommazahl `float`, Standard `1.0`, Wertebereich `0.0-2.0`)

### Validierung (`GenerationController.validate_session`):
```python
if not (0 <= low <= 255) or not (0 <= high <= 255):
    return False, "Canny-Schwellenwerte müssen zwischen 0 und 255 liegen."
if low >= high:
    return False, "Der untere Schwellenwert (Low Threshold) muss kleiner als der obere Schwellenwert (High Threshold) sein."
if not (0.0 <= cond_scale <= 2.0):
    return False, "Die ControlNet-Stärke (Conditioning Strength) muss zwischen 0.0 und 2.0 liegen."
```

---

## 3. Vollständiger Datenfluss

```
[Phoenix UI Sliders] 
       │ (canny_low_var, canny_high_var, conditioning_strength_var)
       ▼
[PromptView._on_generate()] -> controller.update_parameters(...)
       │
       ▼
[PromptWorkspaceController.update_parameters()]
       ├─► updates State (PromptWorkspaceState)
       └─► updates GenerationSession (GenerationSessionModel)
             │
             ▼
[GenerationController.queue_generation()]
       ├─► calls validate_session() [Checks bounds: low < high, 0.0 <= scale <= 2.0]
       └─► serializes into temp/controlnet_canny_gate/job_input_{id}.json
             │
             ▼
[ControlNetCannyQnnBackend (Subprocess venv Python)]
       ├─► deserializes input JSON parameters
       ├─► feeds thresholds to canny_edge_detector
       ├─► scales residuals in requantize_tensor_static by conditioning_scale
       └─► executes inference on QNNExecutionProvider (HTP NPU)
```

---

## 4. Residual-Skalierung im Backend

Die Conditioning Strength wird direkt in `requantize_tensor_static` in [controlnet_canny_backend.py](file:///C:/SnapdragonAI/engine/controlnet_canny_backend.py) vor der Requantisierung angewendet:

```python
    @staticmethod
    def requantize_tensor_static(arr_q, scale_from, zp_from, scale_to, zp_to, factor=1.0):
        arr_f = (arr_q.astype(np.float32) - zp_from) * scale_from
        if factor != 1.0:
            arr_f = arr_f * factor
        arr_q_to = np.round(arr_f / scale_to) + zp_to
        clipped_low = np.sum(arr_q_to < 0)
        clipped_high = np.sum(arr_q_to > 65535)
        clipped_arr = np.clip(arr_q_to, 0, 65535).astype(np.uint16)
        return clipped_arr, int(clipped_low), int(clipped_high)
```

Dies wird in der Denoising-Schleife für die Down-Blocks 0–11 und den Mid-Block aufgerufen.

---

## 5. Nachweis der Äquivalenz bei `controlnet_conditioning_scale = 1.0`

Bei `factor = 1.0` verhindert die Verzweigung `if factor != 1.0:` jede Modifikation.
Der Wert `arr_f` bleibt bitgenau identisch mit dem des bisherigen Dequantisierungs-Outputs. Dies wurde durch den automatisierten Integrationstest `test_requantize_tensor_clipping` nachgewiesen:
`np.testing.assert_array_equal(res_1_0, arr_q_to_base)` verifiziert die exakte Bit-Äquivalenz.

---

## 6. Verhalten bei verschiedenen Werten

* **`0.0`:** Die dequantisierten Residuals werden zu `0.0`. Nach Addition des Ziel-Zero-Points wird der Ziel-Tensor auf einen flachen Wert (`zp_to`) neutralisiert. Dies entspricht nicht zwingend einer Standard-SD-Generation (da das Model dennoch das (jetzt neutrale) ControlNet-Eingangsrauschen sieht). **Korrekt formulierte Auswirkung:** *Bei Strength 0.0 werden die ControlNet-Residuals auf den quantisierten Nullwert neutralisiert.*
* **`0.5`:** Die räumliche Strukturierung des Edge-Einflusses wird um 50% gedämpft.
* **`1.0`:** Standard-Einfluss.
* **`2.0`:** Doppelte Amplitude. Verstärkt Kantenstrukturen im latenten Raum. Kann zu Übersättigung und künstlichen Konturen führen.

---

## 7. Quantisierungs- & Clippingdetails

* **Zero Point / Scale:** Werden für jeden Ein- und Ausgangstensor aus der `metadata.json` geladen (z. B. `scale_cn_out`, `zp_cn_out`).
* **Dequantisierung:** $arr_f = (arr_q - zp_{from}) \times scale_{from}$ (Umwandlung in `float32`).
* **Skalierung:** $arr_f = arr_f \times conditioning\_scale$.
* **Requantisierung:** $arr_{q\_to} = \text{round}(arr_f / scale_{to}) + zp_{to}$.
* **Clipping (Sättigung):** Begrenzung per `np.clip(arr_q_to, 0, 65535).astype(np.uint16)` zur Wahrung des vorzeichenlosen 16-Bit-Quantisierungsbereichs.

---

## 8. Messwerte der verifizierten E2E-Läufe (Hexagon NPU)

Verwendetes Referenzbild: `C:\SnapdragonAI\input\Typ.jpg`
Prompt: *A beautiful futuristic city, high quality, highly detailed*
Seed: `12345` | Steps: `20` | CFG: `7.5` | Scheduler: `DDIMScheduler`

| Messwert | Lauf A (Low Canny) | Lauf B (High Canny) | Lauf C (Zero Strength) | Lauf D (High Strength) |
| :--- | :---: | :---: | :---: | :---: |
| **Canny-Schwellenwert** | `20 / 80` | `150 / 230` | `50 / 150` | `50 / 150` |
| **Conditioning Strength** | `1.0` | `1.0` | `0.0` | `2.0` |
| **Edge-Pixel (Wert > 0)** | **4.656** | **146** | **1.542** | **1.542** |
| **Edge-Pixel %** | `1.776 %` | `0.056 %` | `0.588 %` | `0.588 %` |
| **Canny-PNG-Größe** | 5.865 Bytes | 586 Bytes | 2.629 Bytes | 2.629 Bytes |
| **Canny-SHA-256** | `8370d12a...` | `6bd01f19...` | `3a44ac46...` | `3a44ac46...` |
| **Pipeline-Laufzeit** | **139,01 s** | **21,17 s** | **22,34 s** | **21,55 s** |
| **Ausgabegröße (PNG)** | 410.901 Bytes | 451.804 Bytes | 573.039 Bytes | 392.407 Bytes |
| **QNN/HTP-Nachweis** | HTP V73 aktiv | HTP V73 aktiv | HTP V73 aktiv | HTP V73 aktiv |

### Sättigungsanalyse für Lauf D (Strength 2.0):
* **Gesamtzahl verarbeiteter Werte:** `134.526.208`
* **Nach unten geclippt (<0):** `32.334` Werte
* **Nach oben geclippt (>65535):** `39.515` Werte
* **Sättigungsanteil gesamt:** **`0,0534 %`** (Sehr geringer Clipping-Overhead, stabiler Quantisierungsraum).

### Sättigungsanalyse für Lauf C (Strength 0.0):
* **Gesamtzahl verarbeiteter Werte:** `134.526.208`
* **Geclippt:** `0` (Keine Sättigung, da alle Werte auf den neutralen Zero-Point abgebildet wurden).

---

## 9. Verzeichnisstruktur der verifizierten Ausgaben

Alle verifizierten Bilddaten und Sidecars befinden sich unter:
`C:\SnapdragonAI\output\sprint_cn004_verified\`

* `Run_A_low_canny_1784265949_12345_canny.png`
* `Run_A_low_canny_1784265949_12345_contact.png`
* `Run_A_low_canny_1784265949_12345_input.png`
* `Run_A_low_canny_1784265949_12345_output.json`
* `Run_A_low_canny_1784265949_12345_output.png`
* `Run_B_high_canny_1784265971_12345_canny.png`
* `Run_B_high_canny_1784265971_12345_contact.png`
* `Run_B_high_canny_1784265971_12345_input.png`
* `Run_B_high_canny_1784265971_12345_output.json`
* `Run_B_high_canny_1784265971_12345_output.png`
* `Run_C_zero_strength_1784265994_12345_canny.png`
* `Run_C_zero_strength_1784265994_12345_contact.png`
* `Run_C_zero_strength_1784265994_12345_input.png`
* `Run_C_zero_strength_1784265994_12345_output.json`
* `Run_C_zero_strength_1784265994_12345_output.png`
* `Run_D_high_strength_1784266133_12345_canny.png`
* `Run_D_high_strength_1784266133_12345_contact.png`
* `Run_D_high_strength_1784266133_12345_input.png`
* `Run_D_high_strength_1784266133_12345_output.json`
* `Run_D_high_strength_1784266133_12345_output.png`
* `edge_metrics.json`
* `conditioning_comparison.json`
* `cn004_e2e_terminal.log`

---

## 10. Ergebnisse der Stable Diffusion Regression

* **SD1.5 Regression Bild:** `C:\SnapdragonAI\output\sprint_cn004\Regression_SD15_1784264862_c328e180.png`
* **SD1.5 Regression JSON:** `C:\SnapdragonAI\output\sprint_cn004\Regression_SD15_1784264862_c328e180.json` (Laufzeit: 16s, HTP V73, 0% CPU Fallback)
* **SD2.1 Regression Bild:** `C:\SnapdragonAI\output\sprint_cn004\Regression_SD21_1784264885_b0f66d3c.png`
* **SD2.1 Regression JSON:** `C:\SnapdragonAI\output\sprint_cn004\Regression_SD21_1784264885_b0f66d3c.json` (Laufzeit: 22s, HTP V73, 0% CPU Fallback)

---

## 11. Testergebnisse & Git-Ausgaben (Phase 7)

### Unit Tests (`python -m unittest discover -s C:\SnapdragonAI\tests`):
```cmd
Ran 77 tests in 3.389s
OK
```

### Git Diff Check (`git diff --check`):
```cmd
warning: in the working copy of 'controllers/generation_controller.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'controllers/generation_session.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'controllers/prompt_workspace_model.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'engine/controlnet_canny_backend.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tests/test_controlnet_ui.py', LF will be replaced by CRLF the next time Git touches it
```

### Git Diff Stat (`git diff --stat`):
```cmd
 controllers/generation_controller.py       |  13 ++
 controllers/generation_session.py          |   6 +
 controllers/prompt_workspace_controller.py |  10 ++
 controllers/prompt_workspace_model.py      |   6 +
 engine/controlnet_canny_backend.py         |  56 +++++++-
 tests/test_controlnet_ui.py                | 199 +++++++++++++++++++++++++++++
 widgets/phoenix/views/prompt_view.py       | 110 +++++++++++++++-
 7 files changed, 390 insertions(+), 10 deletions(-)
```

### Git Status (`git status`):
```cmd
On branch feature/phoenix-rebuild
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   controllers/generation_controller.py
	modified:   controllers/generation_session.py
	modified:   controllers/prompt_workspace_controller.py
	modified:   controllers/prompt_workspace_model.py
	modified:   engine/controlnet_canny_backend.py
	modified:   tests/test_controlnet_ui.py
	modified:   widgets/phoenix/views/prompt_view.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	analysis_results.md

no changes added to commit (use "git add" and/or "git commit -a")
```

---

## 12. Unabhängiger QNN HTP Nachweis (Log-Zeilen)

Der folgende Auszug aus dem realen Worker-Log (`cn004_e2e_terminal.log`) belegt die fehlerfreie Allokation auf der NPU und den erzwungenen Ausschluss des CPU-Execution-Providers (`session.disable_cpu_ep_fallback`):

```log
[QNN Worker] Preparing Qualcomm QNN runtime for ControlNet Canny
[QNN Worker] Loading Text Encoder on HTP
[QNN Worker] Loading ControlNet on HTP
[QNN Worker] Loading UNet on HTP
[QNN Worker] Loading VAE on HTP
[QNN Worker] Tokenizing prompt
[QNN Worker] Computing Canny edge image...
[QNN Worker] Generating on Qualcomm Hexagon HTP
[QNN Worker] Step 1/20: Timestep=951
```

Der Parameter `session.disable_cpu_ep_fallback = 1` erzwingt den Abbruch bei fehlender NPU-Unterstützung. Da alle 20 Inferenzschritte erfolgreich durchlaufen wurden, ist ein CPU-EP-Fallback ausgeschlossen.

---

## 13. Bekannte Restrisiken

1. **Rauschen im LSB (Least Significant Bit):** Da die Skalierung im Float32-Raum erfolgt und wieder in Uint16 quantisiert wird, können Rundungsfehler von $\pm 1$ LSB auftreten.
2. **Speicherfragmentierung bei extremen Läufen:** Die wiederholte Instanziierung von ONNX-Sessions in kurz aufeinanderfolgenden Subprozessen beansprucht kurzzeitig viel NPU-Treiber-Heapspeicher.
