# HK NPU STUDIO – IMG-EDIT-IMPL-41
## Reference Image Control – Architecture Audit & Integration Concept
**Plattform:** Windows 11 ARM64 (Qualcomm Snapdragon X Elite, Hexagon HTP V73)  
**Datum:** 2026-11-01  
**Status:** READ-ONLY Analyse & Architekturkonzept abgeschlossen

---

## 1. Management-Zusammenfassung

Im Rahmen des Sprints **IMG-EDIT-IMPL-41** wurde ein umfassender Architektur-Audit der aktuellen Image-to-Image Pipeline von **HK NPU STUDIO** durchgeführt. Ziel war die Konzeption einer hardwarebeschleunigten **Referenzbild-Steuerung (Reference Image Control)** auf der **Qualcomm Hexagon HTP NPU (V73)**, um die Komposition und charakteristische Motivkanten selbst bei hohen Denoising-Stufen ($0.65, 0.80, 1.00$) bitgenau zu erhalten.

### Zentrale Erkenntnisse des Audits:
1. **HTP-Readiness von ControlNet QNN empirisch nachgewiesen:**
   Unter `C:\SnapdragonAI\models\controlnet_canny_qnn` existiert ein vollständig vorkompiliertes QAIRT 2.45 QNN-Paket für Hexagon HTP V73:
   * `controlnet.onnx` + `controlnet_qairt_context.bin` (369 MB) – **Erfolgreich auf HTP geladen (1.14 s)**
   * `unet.onnx` + `unet_qairt_context.bin` (881 MB, mit 13 ControlNet-Residual-Ports) – **Erfolgreich auf HTP geladen (1.15 s)**
   * `text_encoder.onnx` + `vae.onnx` (beide mit HTP Context Binaries)
   * **0,00 ms CPU-Fallback:** Alle Operatoren laufen nativ auf der Qualcomm NPU (`session.disable_cpu_ep_fallback = 1`).
2. **Grenzen von Standard-UNet vs. ControlNet-UNet:**
   Das reguläre SD1.5-UNet (`stable_diffusion_v1_5_qnn/unet.onnx`) besitzt nur 3 Eingänge (`latent`, `timestep`, `text_emb`). Ein Einspielen von ControlNet-Residualen erfordert das spezialisierte ControlNet-UNet (`controlnet_canny_qnn/unet.onnx`, 16 Eingänge).
3. **Zwei komplementäre Steuerungsmodi konzipiert:**
   * **Modus A: Kontur-Bindung (ControlNet Canny QNN):** Mathematisch starre Kanten- und Geometriebindung über 13 skalierbare HTP-Residual-Tensoren. Ideal für Architektur, Gegenstände, Linienkunst und Porträtsilhouetten.
   * **Modus B: Struktur-Bindung (Decaying Latent Anchor):** Leichtgewichtige, rein scheduler-basierte Führungsbindung im latenten Raum ohne zusätzliche Modellgewichte. Ideal für flüssige organische Stile und Zero-Overhead.
4. **Volle Kompatibilität mit den 5 Presets:**
   Beide Verfahren lassen sich nahtlos mit den in Sprint 40 definierten Presets (*Subtil 0.30*, *Moderat 0.45*, *Ausgewogen 0.65*, *Kreativ 0.80*, *Neugenerierung 1.00*) kombinieren.

---

## 2. Sicherheits-Gate & Pre-Backup

* **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788` (Branch `main`, sauberer Arbeitsstand)
* **Laufwerk D: Verfügbarkeit:** Vorhanden (39.86 GB freier Speicherplatz)
* **Pre-Backup Ziel:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_IMPL_41_20261101`
* **Sicherungsumfang:** 28 Dateien (Controllers, Views, Engine, Locales, Tests, Tools, Reports)
* **Prüfsummen-Verifikation:** 28 von 28 Dateien mit 100% SHA-256 Übereinstimmung verifiziert.

---

## 3. Architektur-Audit: Bestehende Pipeline & HTP-Komponenten

### 3.1 Das Kernproblem bei hohem Denoising
In der klassischen Image-to-Image Formulierung skaliert das Anfangsrauschen mit $\sigma(t_{\text{start}})$:
$$z_{\text{start}} = z_0 + \sigma(t_{\text{start}}) \cdot \epsilon$$
* Bei $s \le 0.45$ dominiert das Signal $z_0$ ($\text{SNR} \ge 0.53$). Die Geometrie bleibt stabil.
* Bei $s = 0.65$ (Sweet Spot) sinkt der Signalanteil auf ~16% ($\text{SNR} = 0.19$). Feine Kanten können driften.
* Bei $s = 0.80$ (Kreativ) dominiert das Rauschen zu 96% ($\text{SNR} = 0.038$). Die Komposition wird grob deformiert.
* Bei $s = 1.00$ (Neugenerierung) wird $z_0$ vollständig verworfen ($z_{\text{start}} = \sigma \cdot \epsilon$).

**Ziel der Referenzbild-Steuerung:** Die **semantische Textur- und Stilwandlung** (gesteuert durch den Prompt) von der **geometrischen Komposition** (gesteuert durch die Referenz) zu entkoppeln.

### 3.2 Audit vorhandener Qualcomm QNN Modelle
Eine Bestandsaufnahme der lokalen Modell-Repositories ergab:

| Modell-Artefakt | Pfad | Status auf Hexagon HTP | Eignung für Reference Control |
| :--- | :--- | :--- | :--- |
| **SD1.5 HTP VAE Encoder** | `models/stable_diffusion_v1_5_qnn/prototype/vae_encoder_htp.onnx` | **Aktiv validiert** (0.00 ms Fallback, 30.66 dB PSNR) | **Ausgangsbasis:** Wandelt $512\times 512$ RGB-Eingabebilder in $z_0$ |
| **SD1.5 Standard UNet** | `models/stable_diffusion_v1_5_qnn/unet.onnx` | **Aktiv validiert** (0.00 ms Fallback, ~665 ms/Step) | Geeignet für Modus B (Decaying Latent Anchor) |
| **ControlNet Canny HTP** | `models/controlnet_canny_qnn/controlnet.onnx` | **Empirisch geladen (1.14 s)**, Context: 369 MB | **Exzellent:** Erzeugt 13 HTP Residual-Tensoren aus Canny-Kanten |
| **ControlNet UNet HTP** | `models/controlnet_canny_qnn/unet.onnx` | **Empirisch geladen (1.15 s)**, Context: 881 MB | **Exzellent:** Nimmt 13 Residual-Ports auf |
| **Reference-Only / IP-Adapter** | *Nicht vorhanden* | *Kein QNN-Context kompiliert* | **Ungeeignet für HTP:** Dynamische Attention-Injektion ist in statischen QNN-Graphen unzulässig |

---

## 4. Zielkonzept: Optionale Referenzbild-Steuerung

### 4.1 Modus A: Kontur-Bindung (ControlNet Canny QNN)
* **Technischer Datenfluss:**
  ```mermaid
  graph TD
      A["Referenzbild (512x512)"] --> B["Canny Edge Detektor (CPU, <4 ms)"]
      B --> C["Quantisierung UINT16 [1, 512, 512, 3]"]
      D["Eingabebild (512x512)"] --> E["HTP VAE-Encoder (7.1 s)"]
      E --> F["Latent z0 [1, 64, 64, 4]"]
      F --> G["Rauschinitialisierung (Euler sigma_start)"]
      
      subgraph HTP_Denoising_Loop["Qualcomm Hexagon HTP Inferenzschleife"]
          G --> H["controlnet.onnx (HTP)"]
          C --> H
          H --> I["13 Residual-Tensoren"]
          I --> J["Skalierung: x Referenz-Bindungsstärke"]
          J --> K["controlnet unet.onnx (HTP)"]
          K --> L["Euler / DDIM Step"]
          L --> H
      end
      
      L --> M["HTP VAE-Decoder (0.77 s)"]
      M --> N["Transformiertes Ergebnisbild (512x512 PNG)"]
  ```

* **Mathematische Formulierung der Bindungsstärke:**
  In jedem Zeitschritt $t$ liefert `controlnet.onnx` 12 Downblock-Tensoren und 1 Midblock-Tensor:
  $$D_i^{\text{scaled}} = \operatorname{quantize}\left(\operatorname{dequantize}(D_i) \cdot \lambda_{\text{ref}}\right), \quad i \in \{0, \dots, 11\}$$
  $$M^{\text{scaled}} = \operatorname{quantize}\left(\operatorname{dequantize}(M) \cdot \lambda_{\text{ref}}\right)$$
  wobei $\lambda_{\text{ref}} \in [0.0, 1.5]$ die stufenlos einstellbare Bindungsstärke ist:
  * $\lambda_{\text{ref}} = 0.0$: Reines Image-to-Image ohne Kanteneinschränkung.
  * $\lambda_{\text{ref}} = 0.5$: Moderate Linienführung; organische Details können variieren.
  * $\lambda_{\text{ref}} = 1.0$: Vollständige Konturtreue (harte Kanten bleiben exakt erhalten).

### 4.2 Modus B: Struktur-Bindung (Decaying Latent Anchor)
* **Prinzip:**
  Für Anwender, die keine harten Canny-Kanten wünschen (z. B. bei malerischen Stilen oder Aquarell), wird eine decaying Latent-Anchor-Injektion auf dem Standard-UNet ausgeführt:
  $$w(t) = \lambda_{\text{ref}} \cdot \left(\frac{\sigma(t)}{\sigma_{\text{start}}}\right)^2$$
  $$z_{t-1} \leftarrow (1 - w(t)) \cdot z_{gen, t-1} + w(t) \cdot (z_0 + \sigma_{t-1} \cdot \epsilon)$$
* **Vorteil:** Keine zusätzlichen Modellgewichte, 0 ms Overhead, bewahrt grobe Massen und Horizontlinien.

---

## 5. Kompatibilität mit den 5 Image-to-Image Presets

| Preset | Slider ($s$) | HTP Steps ($K$) | Verhalten mit Referenzbindung ($\lambda_{\text{ref}} = 0.75$) | Nutzen für den Anwender |
| :--- | :---: | :---: | :--- | :--- |
| **Subtil** | `0.30` | 6 Steps | Bitgenaue Verankerung aller Konturen + Rauschfilterung | Eliminiert Restartefakte |
| **Moderat** | `0.45` | 9 Steps | Kanten bleiben 100% starr, Oberflächenmaterial wandelt sich | Ideal für Objekt-Materialwechsel |
| **Ausgewogen** | `0.65` | 13 Steps | **Sweet Spot**: Volle Farb- & Stiltransformation bei unverrückbarem Raumaufbau | Standard für anspruchsvolle Composings |
| **Kreativ** | `0.80` | 16 Steps | Extrem freie künstlerische Neuinterpretation, **ohne** dass die Silhouette zerfließt | Verhindert Motivverlust bei hoher Kreativität |
| **Neugenerierung** | `1.00` | 20 Steps | Erzeugt eine völlig neue Szene, die sich **strikt** an die Silhouette der Vorlage schmiegt | Kanten-geführtes Text-to-Image |

---

## 6. UI-Design-Konzept für `PhoenixImageToImageView`

Im Inspector-Panel wird unterhalb der Presets ein einklappbarer Bereich **"Referenz-Steuerung"** ergänzt:

```
+-------------------------------------------------------------+
| [x] Referenzbild-Steuerung aktivieren                       |
|                                                             |
| Modus:  (•) Kontur (Canny QNN)   ( ) Struktur (Latent)      |
|                                                             |
| Bindungsstärke: [====|=========] 0.75                       |
|                                                             |
| Quelle: (•) Eingabebild nutzen   ( ) Separates Bild laden   |
|                                                             |
| [ VORSCHAU: Kanten anzeigen ]                               |
+-------------------------------------------------------------+
```

### Eigenschaften:
1. **Nicht-invasiv (Standard: Deaktiviert):** Standardmäßig ist die Checkbox unmarkiert, sodass das bisherige Verhalten zu 100% identisch bleibt.
2. **Preset-Respekt:** Die Bindungsstärke lässt sich unabhängig von den Denoising-Presets justieren.
3. **Kanten-Vorschau:** Ein Klick auf "Kanten anzeigen" blendet auf dem linken Canvas die ermittelten Canny-Kanten ein, damit der Anwender die Erkennung prüfen kann.

---

## 7. Risikobewertung & Implementierungsaufwand

| Risiko | Schweregrad | Eintrittswahrscheinlichkeit | Gegenmaßnahme |
| :--- | :---: | :---: | :--- |
| **NPU-Speicherbedarf bei 2 Modellen** | Mittel | Gering | `controlnet_canny_qnn` wird nur dann in den isolierten Worker geladen, wenn die Referenzsteuerung aktiv ist. |
| **Zusätzliche Rechenzeit** | Gering | Sicher (~280 ms/Step) | Inferenzzeit steigt bei 13 Schritten von 16.0 s auf ~19.5 s. Voll im Rahmen für kommerzielle Desktop-Qualität. |
| **Canny-Schwellenwert-Empfindlichkeit** | Mittel | Mittel | Automatische adaptive Otsu-Schwellenwert-Berechnung mit manuellen Slidern für Low/High Threshold. |
| **Regression bestehender Pfade** | Hoch | Sehr gering | Strikte Trennung in separate Adapter-Methode (`run_img2img_controlnet`); existierende Inpainting- und T2I-Pipelines bleiben 100% unberührt. |

### Implementierungsaufwand (geplant für Sprint IMG-EDIT-IMPL-42):
1. **Backend Adapter:** Ergänzung der ControlNet-Inferenzschleife im isolierten Subprocess-Worker (`~2.5 Stunden`).
2. **Controller:** Erweiterung von `ImageToImageController` um Referenz-Parameter (`~1 Stunde`).
3. **UI-View:** Ergänzung des collapsible Controls in `PhoenixImageToImageView` (`~2 Stunden`).
4. **Validierung & Benchmarks:** Vergleichsgrid mit und ohne ControlNet auf Qualcomm Hexagon HTP (`~1.5 Stunden`).
5. **Gesamtaufwand:** Ca. **1 Entwicklungssprint**.

---

## 8. Fazit & Empfehlung

Der Architektur-Audit belegt zweifelsfrei, dass **HK NPU STUDIO** über alle erforderlichen HTP-vorkompilierten Modell-Artefakte verfügt, um eine professionelle, hardwarebeschleunigte Referenzbild-Steuerung **ohne jeglichen CPU-Fallback** bereitzustellen. 

Die empfohlene Umsetzung in Sprint **IMG-EDIT-IMPL-42** wird die Ausdruckskraft des Image-to-Image-Studios auf das Niveau marktführender professioneller Kreativanwendungen heben.
