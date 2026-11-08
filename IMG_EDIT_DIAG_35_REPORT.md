# HK NPU STUDIO – DIAGNOSEBERICHT IMG-EDIT-DIAG-35
**Forensische Ursachenanalyse: Graue generierte Bilder im Ausgabeverzeichnis**  
**Qualcomm Snapdragon X Elite (Hexagon HTP NPU V73) | Windows 11 ARM64**  
*Datum:* 01. November 2026  
*Status:* Analyse vollständig abgeschlossen (Ausschließlich READ-ONLY)

---

## 1. Executive Summary & Kernergebnis

In der forensischen Untersuchung des Projekts `C:\SnapdragonAI` wurden die im Ausgabeverzeichnis aufgetretenen grauen Bilddateien identifiziert, vermessen und ihre Entstehung lückenlos bis zur auslösenden Quellcode-Zeile zurückverfolgt:

1. **Befund:** Im Verzeichnis `C:\SnapdragonAI\output\` befinden sich exakt **56 Bilddateien** mit dem Namensmuster `generative_fill_<timestamp_ns>.png`.
2. **Messwert:** Alle 56 Dateien sind **100 % bitidentisch** zueinander (identischer SHA-256 Hash: `56e37173fa572f993328a6bb2b4687e0b263e25219a9df57fed06359c584e9e2`, Dateigröße exakt 1.878 Bytes).
3. **Kanalwerte:** Jeder einzelne Pixel in allen 56 Bildern besitzt exakt den Wert **RGB (120, 120, 120)** (Standardabweichung $\sigma = 0.0000$, hexadezimal `#787878`, monotones Mittelgrau).
4. **Fehlerursache:** Es handelt sich **nicht** um einen Hardware- oder VAE-Inferenzfehler der Qualcomm Hexagon NPU und **nicht** um einen Fehler beim PNG-Export oder der Farbnormalisierung.  
   Die Dateien wurden durch automatische Testläufe von `tests/test_phoenix_inpainting_ui.py` generiert:
   - In [`widgets/phoenix/views/inpainting_view.py`](file:///C:/SnapdragonAI/widgets/phoenix/views/inpainting_view.py#L572) generiert die Methode `_start()` den Ausgabepfad fest über `OUTPUT_DIR / f"generative_fill_{time.time_ns()}.png"`, wobei `OUTPUT_DIR` auf das reale Anwendungsverzeichnis `C:\SnapdragonAI\output` zeigt.
   - In [`tests/test_phoenix_inpainting_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_inpainting_ui.py#L61-L66) erzeugt die Mock-Klasse `DummyAdapter` / `FakeAdapter` bei jedem Aufruf deterministisch ein Testbild:
     ```python
     Image.new("RGB", (512, 512), (120, 120, 120)).save(p)
     ```
   - In drei UI-Unit-Tests (`test_view_start_passes_edge_and_cfg_parameters_to_controller`, `test_view_start_with_empty_negative_prompt`, `test_view_start_passes_denoising_strength_to_controller_and_adapter`) wird `view._start()` mit einer 100 % weißen Maske aufgerufen. Dadurch werden bei jedem Testdurchlauf genau 3 Dummy-Dateien mit RGB (120, 120, 120) direkt im Produktiv-Ordner `output/` abgelegt.
5. **Verifikation der realen HTP-Pipeline:**  
   Die reale Qualcomm Hexagon HTP Inferenz (sowohl T2I in `sd15_qnn_backend.py` als auch Inpainting in `sd15_qnn_inpainting_adapter.py` sowie der reale HTP VAE Decoder) erzeugt volle, dynamische 24-Bit-Farbbilder mit $\sigma > 45.0$ und normaler Verteilung über den gesamten Dynamikbereich $[0, 255]$.

---

## 2. Git-Status und HEAD-Dokumentation

```text
HEAD: 8784a43f5b7666f1007292393c6ea947b5cdd788
Working Tree Status:
 M controllers/inpainting_controller.py
 M docs/CHATGPT_HANDOVER.md
 M locales/de_DE.json
 M locales/en_US.json
 M tests/test_phoenix_image_lab_navigation.py
 M tests/test_phoenix_inpainting_ui.py
 M widgets/phoenix/inpainting_canvas.py
 M widgets/phoenix/views/image_lab_view.py
 M widgets/phoenix/views/inpainting_view.py
 M widgets/phoenix/views/photo_restore_view.py
 M widgets/phoenix/workspace.py
?? IMG_EDIT_IMPL_32_REPORT.md
?? IMG_EDIT_IMPL_33_REPORT.md
?? IMG_EDIT_QUALITY_30_REPORT.md
?? IMG_EDIT_QUALITY_31_REPORT.md
?? assets/brand/HK_NPU_STUDIO_Reddit_Banner_FULL.jpg
?? engine/backends/sd15_qnn_inpainting_adapter.py
?? reports/
?? tests/test_sd15_qnn_inpainting_pipeline.py
?? tests/test_sd15_vae_encoder.py
?? tests/test_sd15_vae_encoder_htp.py
?? tests/test_sd15_vae_htp_compatibility.py
?? tools/build_sd15_vae_encoder_htp.py
?? tools/export_sd15_vae_encoder.py
?? tools/test_sd15_vae_roundtrip_htp.py
?? tools/verify_sd15_vae_htp_compatibility.py
?? widgets/phoenix/views/image_lab_workspace.py
```

*Hinweis: Während dieser Diagnose wurden strikt keine Code- oder Git-Änderungen vorgenommen.*

---

## 3. Forensische Bildanalyse der grauen Bilddateien

Im Verzeichnis `C:\SnapdragonAI\output\` wurden 104 Bilddateien analysiert. Davon sind genau 56 Dateien flachgrau:

### 3.1 Übersicht der 56 grauen Bilddateien

- **Namensmuster:** `generative_fill_1793474963284442900.png` bis `generative_fill_1793519944485163300.png`
- **Erstellungszeitraum:** 30. Oktober 2026 20:09 Uhr bis 01. November 2026 08:59 Uhr (exakt synchron zu den Ausführungszeiten der Test-Suiten).
- **Dateigröße:** Exakt `1.878 Bytes` auf Datenträger (alle 56 Dateien identisch).
- **Kryptographischer Hash:**  
  `SHA-256 = 56e37173fa572f993328a6bb2b4687e0b263e25219a9df57fed06359c584e9e2` (für alle 56 Dateien bitidentisch).

### 3.2 Pixel- und Kanalmesswerte

| Kanal | Min | Max | Mittelwert ($\mu$) | Standardabweichung ($\sigma$) | Median | Einzigartige Pixelwerte |
|---|---|---|---|---|---|---|
| **Rot (R)** | 120 | 120 | 120.0000 | 0.0000 | 120 | 1 (nur 120) |
| **Grün (G)** | 120 | 120 | 120.0000 | 0.0000 | 120 | 1 (nur 120) |
| **Blau (B)** | 120 | 120 | 120.0000 | 0.0000 | 120 | 1 (nur 120) |
| **Gesamt** | 120 | 120 | 120.0000 | 0.0000 | 120 | 1 (nur 120) |

- **Dimension:** $512 \times 512$ Pixel ($262.144$ Pixel insgesamt)
- **Farbtiefe:** 24-Bit Truecolor RGB (`uint8`)
- **Farbwert:** `#787878` (vollkommen unstrukturiertes, einheitliches Grau).

---

## 4. Analyse des Erzeugungs- und Exportpfads

### 4.1 Prüfung: Vor dem Speichern vs. Export
Die Prüfung ergab, dass die Bilder **nicht** erst beim PNG-Export oder bei einer Farbraumkonvertierung grau werden, sondern bereits als monotones Array im Speicher erzeugt werden:

1. In [`tests/test_phoenix_inpainting_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_inpainting_ui.py#L65):
   ```python
   out_path = args[3] if len(args) > 3 else kwargs.get("output_path", "output.png")
   if out_path:
       p = Path(out_path)
       p.parent.mkdir(parents=True, exist_ok=True)
       Image.new("RGB", (512, 512), (120, 120, 120)).save(p)
   ```
2. In [`widgets/phoenix/views/inpainting_view.py`](file:///C:/SnapdragonAI/widgets/phoenix/views/inpainting_view.py#L572):
   ```python
   output_path = OUTPUT_DIR / f"generative_fill_{time.time_ns()}.png"
   ```
3. In den Unit-Tests [`test_phoenix_inpainting_ui.py`](file:///C:/SnapdragonAI/tests/test_phoenix_inpainting_ui.py#L758-L763):
   ```python
   view.canvas.save_mask = lambda p: Image.new("L", (512, 512), 255).save(p)
   view._start()
   ```
4. Der `InpaintingController` führt daraufhin die Komposition aus:
   ```python
   final_image = Image.composite(aligned_gen, source, feathered_mask)
   final_image.save(output_path, format="PNG")
   ```
   Da die Maske zu 100 % weiß (255) ist, entspricht `final_image` zu 100 % der Ausgabe des gemockten Adapters (`aligned_gen`), welche aus `Image.new("RGB", (512, 512), (120, 120, 120))` stammt.
5. Die PNG-Kompression (Deflate) komprimiert ein völlig monotones $512 \times 512$ Bild mit identischen Scanlines auf exakt 1.878 Bytes. Der Exportvorgang ist verlustfrei und technisch einwandfrei.

---

## 5. Analyse des Qualcomm Hexagon HTP VAE-Decoders

Zur Klärung, ob der echte Qualcomm HTP VAE Decoder jemals ein monotones Grau erzeugen könnte, wurde der Decoder auf dem Snapdragon X Elite (Hexagon HTP V73) hardwarenah diagnostiziert:

- **Modell-Pfad:** `C:\Users\holge\AppData\Local\HK NPU STUDIO\models\stable_diffusion_v1_5_qnn\vae.onnx`
- **Context-Binary:** `vae_qairt_context.bin` (64.622.592 Bytes, QAIRT 2.45)
- **Ausführungsprovider:** `QNNExecutionProvider` (HTP V73, `QnnHtp.dll`, FP16 Precision)

### 5.1 Reale Hardware-Messungen auf Qualcomm Hexagon HTP

#### Testlauf A: Typischer Latent-Tensor ($\mu \approx 0.0, \sigma = 1.0$)
- **HTP Decoder Inferenzzeit:** 255.75 ms
- **Ausgabe-Tensor (UINT16):**
  - Shape: `[1, 512, 512, 3]`
  - Min: `0`, Max: `65535`, Mittelwert: `30114.4`, Standardabweichung: `22733.5`
- **Dequantisierter Float32-Wertebereich ($[0.0, 1.0]$):**
  - Min: `0.0000`, Max: `1.0000`, Mittelwert: `0.4595`, Standardabweichung: `0.3469`
- **RGB-Kanalwerte (UINT8):**
  - Rot: Min = 0, Max = 255, $\mu = 109.66$, $\sigma = 84.76$
  - Grün: Min = 0, Max = 255, $\mu = 120.64$, $\sigma = 87.70$
  - Blau: Min = 0, Max = 255, $\mu = 120.10$, $\sigma = 92.18$
- **Ergebnis:** Voller Dynamikumfang über 0–255 in allen drei Kanälen, reiche Farbsättigung, kein Grau.

#### Testlauf B: Extremfall Null-Latent (Theoretischer UNet-Totalausfall, alle Latents = 0.0)
- **Ausgabe-Tensor (UINT16):**
  - Min: `15294`, Max: `39002`, Mittelwert: `26904.0`
- **RGB-Kanalwerte (UINT8):**
  - Rot: Min = 107, Max = 151, $\mu = 125.65$, $\sigma = 1.74$
  - Grün: Min = 85, Max = 114, $\mu = 101.58$, $\sigma = 1.57$
  - Blau: Min = 59, Max = 98, $\mu = 85.25$, $\sigma = 3.26$
- **Ergebnis:** Selbst bei völlig erloschenem UNet erzeugt der VAE Decoder durch seine internen Biases einen gedämpften Braunton ($R \ne G \ne B$), aber **keinesfalls** das homogene Grau $(120, 120, 120)$ mit $\sigma = 0.00$.

---

## 6. Dequantisierung und Normalisierung

Die Dequantisierung im produktiven Adapter [`sd15_qnn_inpainting_adapter.py`](file:///C:/SnapdragonAI/engine/backends/sd15_qnn_inpainting_adapter.py#L958-L961) lautet:

$$\text{image\_scale} = 1.5259021893143654 \times 10^{-5} \quad \left(=\frac{1}{65535}\right)$$
$$\text{image\_zp} = 0$$
$$\text{image\_float} = (\text{raw\_uint16} - \text{image\_zp}) \times \text{image\_scale}$$
$$\text{image\_rgb} = \text{clip}(\text{image\_float} \times 255.0, 0, 255).\text{astype}(\text{uint8})$$

- Die Skalierungsfaktoren stimmen exakt mit den Initializern des Qualcomm ONNX-Modells überein (`image_scale` und `image_zp` in `vae.onnx`).
- Die Abbildung ist streng linear und mathematisch umkehrbar.
- Es gibt keinen Informationsverlust oder numerische Auslöschung in der Dequantisierung.

---

## 7. PNG/JPEG-Konvertierung und RGB/BGR-Reihenfolge

- **Format im Tensor:** Die QNN-Modelle von Qualcomm AI Hub Workbench operieren standardmäßig im NHWC-Format mit Farbkanälen $[R, G, B]$.
- **Pillow-Integration:** Die Erstellung via `Image.fromarray(image_rgb)` erzeugt direkt ein 3-Kanal-RGB-Bild.
- **Kanalordnung:** Es findet keine OpenCV-Konvertierung (`cv2.cvtColor(..., BGR2RGB)`) statt, so dass keine Vertauschungen der Farbkanäle vorliegen.
- **Speicherformat:** Das Speichern via `img.save(path, format="PNG")` erzeugt konforme 24-Bit-RGB-PNGs.

---

## 8. Getrennte Betrachtung von T2I und Inpainting

| Merkmal | T2I-Pipeline (`sd15_qnn_backend.py` / SD2.1 / SD3.5) | Inpainting-Pipeline (Reale HTP-Inferenz) | UI-Test-Generierung (`test_phoenix_inpainting_ui.py`) |
|---|---|---|---|
| **Dateinamen** | `generate_<timestamp>_<id>.png` | `inpaint_output.png` / temporär | `generative_fill_<timestamp_ns>.png` |
| **Speicherort** | `C:\SnapdragonAI\output\` | `temp/sd15_inpainting_test_artifacts/` | `C:\SnapdragonAI\output\` |
| **Bildinhalt** | Fotorealistische Motive, vollfarbig | Harmonisiertes Inpaint, vollfarbig | Monotones Grau |
| **Dynamikbereich** | Min: 0, Max: 255 | Min: 0, Max: 255 | Min: 120, Max: 120 |
| **Standardabw. ($\sigma$)** | **32.67 bis 82.86** | **49.23** | **0.0000** |
| **Mittelwert ($\mu$)** | 102.63 bis 181.41 | 167.16 | 120.0000 |
| **Dateigröße** | 413 KB bis 1.940 KB | 263 KB | **1.878 Bytes** |
| **Status** | Einwandfrei funktional | Einwandfrei funktional | **Quelle der 56 grauen Dateien** |

---

## 9. Fazit & Handlungsempfehlung

### 9.1 Fazit
Die aufgetretenen grauen Bilder im Ordner `C:\SnapdragonAI\output\` sind **keine Fehlfunktion der Bildgenerierung**, sondern **Test-Artefakte** der Unit-Test-Suite:
- Die automatisierte UI-Testsuite (`test_phoenix_inpainting_ui.py`) testet die Benutzeroberfläche und den Controller mit einem schnellen Dummy-Mock (`DummyAdapter`), der ein Bild mit der Farbe `(120, 120, 120)` zurückgibt.
- Da `PhoenixInpaintingView._start()` den Pfad fest im Produktionsordner `OUTPUT_DIR = Path("output")` anlegt, landen diese Dummy-Bilder bei jedem Aufruf von `python -m unittest` im echten `output/`-Verzeichnis.
- Weder die reale T2I-Pipeline noch die reale Qualcomm Hexagon HTP Inpainting-Pipeline erzeugen graue Bilder.

### 9.2 Empfehlung für zukünftige Sprints (Nicht in diesem READ-ONLY Sprint ausgeführt)
1. In `PhoenixInpaintingView` sollte der Zielordner konfigurierbar sein oder `_start()` sollte im Testkontext ein temporäres Verzeichnis (`tempfile.TemporaryDirectory`) verwenden, anstatt in `OUTPUT_DIR` zu schreiben.
2. Die 56 verwaisten Test-Artefakte `generative_fill_*.png` in `C:\SnapdragonAI\output\` können gefahrlos bereinigt werden, da sie reine Testrückstände darstellen.
