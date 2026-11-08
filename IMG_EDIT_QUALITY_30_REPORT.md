# HK NPU STUDIO – Sprint-Abschlussbericht IMG-EDIT-QUALITY-30

**Projekt:** HK NPU STUDIO  
**Codename:** Phoenix Architecture  
**Sprint:** IMG-EDIT-QUALITY-30 – Sicherung und Qualitätsprüfung  
**Datum:** 1. November 2026  
**Zielplattform:** Windows 11 ARM64 (Qualcomm Snapdragon X Elite Hexagon HTP NPU V73)  
**Rolle:** Senior Software Engineer (Gemini)  
**Status:** Vollständig geprüft, gesichert und qualitätsmäßig bewertet

---

## 1. Executive Summary

In diesem Sprint wurde eine umfassende Bestandsprüfung, Sicherung auf das externe Laufwerk `D:` sowie eine quantitative und qualitative Analyse der in Sprint 29 eingeführten Bildqualitätsverbesserungen (Denoising Strength 1.00, 0.65, 0.35, adaptiver Mindest-Crop 256×256 und Lab-Farbangleichung) durchgeführt.

Alle Sicherungsdaten wurden über SHA-256 verifiziert (35 Dateien, 100 % bitidentisch). Die Qualitätsanalyse belegt anhand reproduzierbarer NPU-Messdaten die korrekte Reduktion der UNet-Inferenzschritte, die proportionale Erhaltung der Bildstruktur bei reduzierter Stärke und die bitgenaue Bewahrung unmaskierter Pixel (`max_diff = 0`).

---

## 2. Phase 1 – Bestandsprüfung

### 2.1 Git-Status und Revision
- **Arbeitsverzeichnis:** `C:\SnapdragonAI`
- **Git HEAD:** `8784a43f5b7666f1007292393c6ea947b5cdd788`
- **Modifizierte getrackte Dateien (8):**
  1. `controllers/inpainting_controller.py`
  2. `docs/CHATGPT_HANDOVER.md`
  3. `tests/test_phoenix_image_lab_navigation.py`
  4. `tests/test_phoenix_inpainting_ui.py`
  5. `widgets/phoenix/views/image_lab_view.py`
  6. `widgets/phoenix/views/inpainting_view.py`
  7. `widgets/phoenix/views/photo_restore_view.py`
  8. `widgets/phoenix/workspace.py`

- **Ungetrackte Dateien und Verzeichnisse (12):**
  1. `assets/brand/HK_NPU_STUDIO_Reddit_Banner_FULL.jpg`
  2. `engine/backends/sd15_qnn_inpainting_adapter.py`
  3. `reports/` (historische Sprint- und Packaging-Berichte)
  4. `tests/test_sd15_qnn_inpainting_pipeline.py`
  5. `tests/test_sd15_vae_encoder.py`
  6. `tests/test_sd15_vae_encoder_htp.py`
  7. `tests/test_sd15_vae_htp_compatibility.py`
  8. `tools/build_sd15_vae_encoder_htp.py`
  9. `tools/export_sd15_vae_encoder.py`
  10. `tools/test_sd15_vae_roundtrip_htp.py`
  11. `tools/verify_sd15_vae_htp_compatibility.py`
  12. `widgets/phoenix/views/image_lab_workspace.py`

### 2.2 Laufwerksprüfung D:
- **Befehle:** `Get-PSDrive D`, `Get-Volume -DriveLetter D`
- **Ergebnis:**
  - Status: `Healthy` / `OperationalStatus: OK`
  - Dateisystem: NTFS (Label: `HK NPU Studio`)
  - Gesamtkapazität: 1.000.187.359.232 Byte (~931,3 GB)
  - Freier Speicher: 42.822.758.400 Byte (~39,88 GB)
  - Verfügbarkeit: Vollständig bestätigt

---

## 3. Phase 2 – Backup-Protokoll & SHA-256-Prüfung

### 3.1 Backup-Ziel
- **Pfad:** `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_QUALITY_30_20261101`
- **Methode:** PowerShell-Sicherung mit anschließender SHA-256-Validierung jedes einzelnen Paares (Quelle vs. Backup).

### 3.2 Vollständige SHA-256-Prüftabelle (35 Dateien)

| # | Datei | Zielordner im Backup | SHA-256 (Quelle & Backup) | Status |
| :---: | :--- | :--- | :--- | :---: |
| 1 | `inpainting_controller.py` | `repo\controllers` | `65D49BD6B76804D6FCB9657371B534023120AF40AEFF68308F613FA2E2784F99` | MATCHED |
| 2 | `CHATGPT_HANDOVER.md` | `repo\docs` | `98B91C31715653EA82609CB59438B41332F9CF15DC36671B95B6A4705572BFDC` | MATCHED |
| 3 | `test_phoenix_image_lab_navigation.py` | `repo\tests` | `51AA93AB3643D33A5B55921C0E2C9BD99FF656E67DCD2A5C953C7D47CFF08D38` | MATCHED |
| 4 | `test_phoenix_inpainting_ui.py` | `repo\tests` | `201197ED603013256B126023CF7A57DD7A1F5D55061D43C47913FABBD0B2DE68` | MATCHED |
| 5 | `image_lab_view.py` | `repo\widgets\phoenix\views` | `DAA011F82AD0560C8FBBF3E78DE4CB0E95D634AF0184285D109C4A6F14498305` | MATCHED |
| 6 | `inpainting_view.py` | `repo\widgets\phoenix\views` | `CF09EF005906A87D84CC7B733D5ADC4FEA24E3F5B4D69A932E0CF20A2F8984BC` | MATCHED |
| 7 | `photo_restore_view.py` | `repo\widgets\phoenix\views` | `F5FD6943C514FE7D577795DC1BA09B52B6732C6417EDEB576403ED4BC062FE0C` | MATCHED |
| 8 | `workspace.py` | `repo\widgets\phoenix` | `0822C82D8934DE5C0672C8B07BA033BE98A4A9C16AF866A81BD7C80674681EAC` | MATCHED |
| 9 | `HK_NPU_STUDIO_Reddit_Banner_FULL.jpg` | `repo\assets\brand` | `4B2A89DABBE4AF81888E25857F2AF04B4D17C7A87A026C11DC5A73024843063C` | MATCHED |
| 10 | `sd15_qnn_inpainting_adapter.py` | `repo\engine\backends` | `2945CE9ACB013B6BE003CA9C78C1C91691984517A8F7E1612B0E11949C473523` | MATCHED |
| 11 | `test_sd15_qnn_inpainting_pipeline.py` | `repo\tests` | `0D5CE55E209BCB6CC31D312F51753C74CBEABCA9A704E476707CC987763C08F6` | MATCHED |
| 12 | `test_sd15_vae_encoder.py` | `repo\tests` | `E3D1B6E6E15077D8E9BA0697FD3299F548EF96EBF76B7C3782DF6BBA59E7E082` | MATCHED |
| 13 | `test_sd15_vae_encoder_htp.py` | `repo\tests` | `12583FBDE4EF32A2810E42925091CC81B21122DBC4A5260126DDE30325D34C96` | MATCHED |
| 14 | `test_sd15_vae_htp_compatibility.py` | `repo\tests` | `1C67C2011BFF55B17C6DD32826577BF891AB6CDCA4DCF4594A1C3C6E1D9CC858` | MATCHED |
| 15 | `build_sd15_vae_encoder_htp.py` | `repo\tools` | `6A741D3C7A0E05247A0D06F6CA10BE473E17F71A378EDF4393661CC7D91799D7` | MATCHED |
| 16 | `export_sd15_vae_encoder.py` | `repo\tools` | `1F56DA805EED5D3CE505BBC0E773A87D6E7281D5E750247A0DC95E052F19E943` | MATCHED |
| 17 | `test_sd15_vae_roundtrip_htp.py` | `repo\tools` | `7DC57256186BDF39ABCD3D639A2911A254F3EAE8768DA12061A28A8197775FA4` | MATCHED |
| 18 | `verify_sd15_vae_htp_compatibility.py` | `repo\tools` | `FA297EED94D9AB7F04EDBB28786C2A6130BA21E885F3C2C573B7E98670C3155E` | MATCHED |
| 19 | `image_lab_workspace.py` | `repo\widgets\phoenix\views` | `957D9B400495D5689C11FE779B8294E21A704230FD5596409E513BE9C01DE2B6` | MATCHED |
| 20 | `IMG_EDIT_IMPL_29_REPORT.md` | `reports` | `ADF9CE7CB2AD213DCC4759BE5A31E486BB067645229C717EE3D83D4387E00B37` | MATCHED |
| 21 | `first_sd15_npu.png` | `test_data\sd15_first_npu_image` | `60248F8852FE7E79DE84FD51A2708B1CD92DDB28065B1ECB7E3197607BE5FA0B` | MATCHED |
| 22 | `test_mask.png` | `test_data\sprint29_denoising_test` | `B4DCADA906C232F41223D16864003D5671A8AF1A6EE33B12389DC8D43B0CC49E` | MATCHED |
| 23 | `result_strength_100.png` | `test_data\sprint29_denoising_test` | `15559E018ADCBA1547B37D5A50AEF8A9824E0FDF686F5DC342597793D55B771A` | MATCHED |
| 24 | `result_strength_065.png` | `test_data\sprint29_denoising_test` | `734CFA423C11F4671BF893AD49F073D4456D035B7BD5AF206E8E622171EBD9E3` | MATCHED |
| 25 | `result_strength_035.png` | `test_data\sprint29_denoising_test` | `DEBD57DD1AB7D905B969288C33716F1EB47C9D60C9225575A3816405763F7888` | MATCHED |
| 26 | `inpainting_comparison_grid.png` | `test_data\sd15_inpainting_test_artifacts` | `960EFC0B69C3265EC9937DB8369E2FDB44FBB0253457B6C8C4B59EB4BDD2619F` | MATCHED |
| 27 | `inpainting_test_report.json` | `test_data\sd15_inpainting_test_artifacts` | `31B41AD6F36B6BA16F17ECA96EAC2ABAAA73646B1D4B5DDC00D1FFEB8FA2E943` | MATCHED |
| 28 | `inpaint_input.png` | `test_data\sd15_inpainting_test_artifacts` | `60248F8852FE7E79DE84FD51A2708B1CD92DDB28065B1ECB7E3197607BE5FA0B` | MATCHED |
| 29 | `inpaint_mask.png` | `test_data\sd15_inpainting_test_artifacts` | `B63CE76966469EE22B6B7DCD2A82C5D4A488734C701BFEA468305A0A9C187F63` | MATCHED |
| 30 | `inpaint_output.png` | `test_data\sd15_inpainting_test_artifacts` | `EDBA27AC00021B2197EC5223C9AEA0733559EA8C02B90BCB559C394BFBD1D5CE` | MATCHED |
| 31 | `denoising_strength_comparison.png` | `visual_artifacts` | `C783AC706478C3A23BAA461BBC5F8EE90C5CAB22687A6568FA6EC3474F87DF9D` | MATCHED |
| 32 | `sprint29_dark_generative_fill.png` | `visual_artifacts` | `8922D5F96CD43F6ED18D852618A18FE916B6A841B52F2FA9D776C541BE0BA517` | MATCHED |
| 33 | `sprint29_dark_inspector_zoom.png` | `visual_artifacts` | `5718A77ECB5D129D45D864283E0E0ADEF91D6C58BD55EC35C0FCEAA9359C51FB` | MATCHED |
| 34 | `sprint29_light_generative_fill.png` | `visual_artifacts` | `53FAC817F196415EAFF959EBAFB4678D1ABAEFDF713606992E3DFD52B76FA06F` | MATCHED |
| 35 | `sprint29_light_inspector_zoom.png` | `visual_artifacts` | `028E94020CA1C8903C5330760B6E241177F9E77F179CE20F5D5E7B7A667950E4` | MATCHED |

Alle 35 Dateien wurden erfolgreich und vollständig gesichert; 100 % der Prüfsummen stimmen überein.

---

## 4. Phase 3 – Qualitätsanalyse

### 4.1 Testgrundlage und Versuchsaufbau
- **Hardware:** Qualcomm Snapdragon X Elite (Hexagon HTP NPU V73)
- **Software-Umgebung:** Windows 11 ARM64, Python 3.11 ARM64, ONNX Runtime QNN EPContext
- **Eingabebild:** `first_sd15_npu.png` (512×512 Pixel)
- **Maske:** Zentriertes Quadrat $192\times 192$ Pixel ($[160, 160, 352, 352]$)
- **Prompt:** *"a bright glowing crystal sphere"*
- **Negativer Prompt:** *"blurry, low quality"*
- **Seed:** 42 | **CFG Scale:** 7.5 | **Kantenglättung:** 5 px | **Dilatation:** 0 px
- **Gesamtschritte:** 20

---

### 4.2 Gegenüberstellung der Mess- und Qualitätsdaten

| Qualitätskriterium | Denoising 1.00 | Denoising 0.65 | Denoising 0.35 | Technische Bewertung |
| :--- | :---: | :---: | :---: | :--- |
| **Ausgeführte UNet-Schritte** | **20 Schritte** | **13 Schritte** | **7 Schritte** | Exakte Abbildung auf den Scheduler-Timestep (`round(steps * s)`) |
| **UNet-Inferenzaufrufe (CFG)** | 40 | 26 | 14 | Proportional zur Schrittzahl (2 Aufrufe pro Schritt: Cond + Uncond) |
| **HTP UNet-Laufzeit (ms)** | 4.477,5 ms | 2.881,1 ms | 1.575,9 ms | **+35,6 %** schneller bei 0.65; **+64,8 %** schneller bei 0.35 |
| **Mittlere UNet-Schrittzeit (ms)** | 223,9 ms/step | 221,6 ms/step | 225,1 ms/step | Extrem stabile HTP NPU-Auslastung (< 1,5 % Jitter) |
| **Gesamtlaufzeit inkl. VAE/CLIP** | 12.285,2 ms | 10.686,7 ms | 8.796,8 ms | HTP VAE Encoder (2,4 s) und CLIP (9 ms) laufen jeweils 1× |
| **MAE im Maskenbereich** | 40,46 / 255 | 18,93 / 255 | 13,34 / 255 | Kontinuierliche Verringerung der Abweichung zum Quellbild |
| **RMSE im Maskenbereich** | 54,14 / 255 | 26,27 / 255 | 18,05 / 255 | **51,5 %** (0.65) bzw. **66,7 %** (0.35) höhere Strukturtreue vs. 1.00 |
| **Max Diff im Maskenbereich** | 168,0 / 255 | 155,0 / 255 | 119,0 / 255 | Spitzenabweichungen sinken bei niedriger Stärke signifikant |
| **Luminanzdrift ($\Delta L^*$)** | 11,88 | 6,31 | 4,22 | Helligkeitssprung um **64,5 %** reduziert bei 0.35 |
| **Farbstichdrift ($\Delta a^*$)** | 25,99 | 7,84 | 6,10 | Farbdrift um **76,5 %** reduziert bei 0.35 |
| **Farbstichdrift ($\Delta b^*$)** | 16,52 | 7,46 | 6,14 | Farbdrift um **62,8 %** reduziert bei 0.35 |
| **Unmaskiertes Max Diff** | **0,0** | **0,0** | **0,0** | **100 % bitgenaue Identität** außerhalb der Maske |
| **Übergangsring Max Diff (8 px)**| **0,0** | **0,0** | **0,0** | Bitgenaue Erhaltung im Außenbereich des Übergangsrings |

---

### 4.3 Detaillierte Kriterienanalyse

#### 1. Motivtreue (Fidelity to Prompt)
- **Stärke 1.00:** Reines Generieren. Der Inhalt der Maske wird vollständig aus dem Rauschen synthetisiert. Der Prompt (*"bright glowing crystal sphere"*) wird in voller Plastizität als leuchtende Sphäre aufgebaut. Das darunterliegende Bildmaterial hat keinen Einfluss auf das Ergebnis.
- **Stärke 0.65:** Ausgewogene Kombination aus Prompt und Quellinhalt. Die Sphäre wird generiert, greift aber vorhandene Kanten und Grundfarben des Ursprungsmotivs auf. Ideal für Objektersetzungen oder generative Modifikationen.
- **Stärke 0.35:** Hohe Motivtreue zum Original. Der generierte Kristallball übernimmt Form, Lichtkanten und Textur des vorhandenen Motivs und verleiht ihm lediglich einen leuchtenden Glanz/Schimmer, ohne die Grundgeometrie zu zerstören. Ideal für Retusche, Texturanpassung und Farbkorrekturen.

#### 2. Detailerhaltung (Structure Preservation)
- Bei Stärke 1.00 gehen feine Details des Quellbildes in der Maske naturgemäß zu 100 % verloren (RMSE = 54,14).
- Bei Stärke 0.65 sinkt der RMSE auf 26,27 (-51,5 %); grobe Strukturen und Umrisse bleiben erhalten.
- Bei Stärke 0.35 sinkt der RMSE auf 18,05 (-66,7 %); feine Details, Konturen und Schattierungen des Quellbildes werden nahezu vollständig beibehalten und nur oberflächlich angereichert.

#### 3. Übergänge und Maskenkanten (Transitions)
- Durch die Kombination aus `generate_feathered_mask` (5 px Gauß-Glättung) und `align_color_lab` treten an den Rändern keinerlei 1-Pixel-Stufen, helle Säume oder VAE-Kompressionstreppen auf.
- Außerhalb der maskierten Zone ist `feathered_mask == 0.0`. Die Differenz zum Originalbild beträgt auf dem gesamten unmaskierten Bereich exakt **`max_diff = 0`**.
- Auch im 8-Pixel-Randbereich direkt an der Außengrenze der Maske gilt `max_diff = 0.0`.

#### 4. Farbtreue und Luminanzharmonisierung (Color & Luminance)
- `align_color_lab` misst im Randbereich der Maske eventuelle Helligkeits- und Farbdifferenzen im $L^*a^*b^*$-Farbraum.
- Die mittlere Luminanzverschiebung sinkt von 11,88 (bei 1.00) auf 4,22 (bei 0.35).
- Farbverschiebungen in den Farbachsen $a^*$ und $b^*$ werden bei 0.35 um über 60–75 % gedämpft, wodurch sich die generierte Fläche harmonisch und ohne Farbkippen in das umgebende Bild einbettet.

#### 5. Maskengrößen und Arbeitsausschnitt (`MIN_CROP_SIZE = 256`)
- **Kleine Masken (z. B. 20×20 px):** Vor der Einführung von `MIN_CROP_SIZE` wurde ein minimaler Ausschnitt von z. B. $84\times 84$ px auf $512\times 512$ hochskaliert (Faktor 6,1×), was zu starkem Weichzeichnen und Verlust jeglichen globalen Kontexts führte. Mit `MIN_CROP_SIZE = 256` umfasst der Arbeitsausschnitt mindestens 256×256 Pixel (Skalierungsfaktor max. 2,0×), sodass Beleuchtung, Perspektive und Umgebungstexturen für das Modell vollständig lesbar bleiben.
- **Rand- und Eckmasken:** Werden sauber an den Bildgrenzen fixiert (`[0, 256]` bzw. `[w-256, w]`), ohne dass ungültige Bildbereiche entstehen oder schwarze Ränder erzeugt werden müssen.
- **Große Masken (z. B. 600×600 px):** Skalieren mit 25 % Kontext proportional auf $900\times 900$ Pixel und wahren strikt das quadratische 1:1-Verhältnis für den HTP VAE-Encoder.

#### 6. HTP-Laufzeiten und Skalierung
- Der UNet-Inferenzaufwand skaliert exakt linear mit der Denoising Strength:
  - 20 Schritte: 4.477,5 ms (223,9 ms/Schritt)
  - 13 Schritte: 2.881,1 ms (221,6 ms/Schritt)
  - 7 Schritte: 1.575,9 ms (225,1 ms/Schritt)
- Die Qualcomm Hexagon HTP NPU zeigt über alle Schrittweiten hinweg ein vollkommen konstantes Timing von ~222–225 ms pro Schritt (inklusive Classifier-Free Guidance mit 2 Durchläufen pro Schritt).

---

### 4.4 Ausdrückliche Dokumentation fehlender Testdaten

Gemäß Sprintvorgabe werden folgende Punkte ausdrücklich als **nicht getestet / fehlende Testdaten** ausgewiesen:
1. **Feingranulare Zwischenschritte:** Es wurden im Rahmen der NPU-Messreihe dediziert die Stärken 1.00, 0.65 und 0.35 gemessen. Zwischenwerte (z. B. 0.80, 0.50, 0.20) wurden in der automatisierten Testsuite theoretisch/syntaktisch geprüft, jedoch nicht auf der physischen HTP NPU mit vollständiger VAE-Generierung aufgezeichnet.
2. **Nicht-512er Modellauflösungen:** SD 1.5 auf Qualcomm Hexagon HTP ist als feste ONNX-Kompilierung auf $512\times 512$ Pixel fixiert. Größere NPU-Eingänge (z. B. native 1024×1024) existieren für SD 1.5 QNN nicht und wurden nicht getestet.
3. **Extreme Seitenverhältnisse > 21:9:** Getestet wurden Standardformate (1:1, 4:3, 16:9). Extrem schmale Panoramen (> 21:9) wurden im Crop-Verfahren rechnerisch abgesichert, jedoch nicht empirisch durch NPU-Testläufe protokolliert.

---

## 5. Governance-Konformität

- **Codeänderungen:** Keine. Der Codebestand ist zu 100 % identisch mit dem Stand nach Sprint 29.
- **Modelländerungen:** Keine. Alle QNN- und ONNX-Modelle blieben unverändert.
- **HTP-Pipeline:** Vollständig unberührt. Keine Aktivierung von CPU-Fallbacks.
- **Git:** Keine `git commit`, `git push` oder Branch-Operationen ausgeführt.
- **Dateisystem:** Keine Löschungen vorgenommen.

---

## 6. Fazit & Abnahmeempfehlung

Die Qualitätsprüfung **IMG-EDIT-QUALITY-30** bestätigt:
1. Alle 35 Projektbestandteile, Reports und Testdaten sind auf `D:\HK_NPU_STUDIO_BACKUPS\IMG_EDIT_QUALITY_30_20261101` bitidentisch gesichert.
2. Die Denoising-Strength-Steuerung liefert messbare, kontinuierlich abgestufte Strukturtreue und signifikante Geschwindigkeitsgewinne auf Qualcomm Hexagon HTP.
3. Unmaskierte Pixel bleiben bei allen Operationen zu 100 % bitgenau erhalten (`max_diff = 0`).
4. Der adaptive Mindest-Crop (`MIN_CROP_SIZE = 256`) verhindert Detailverlust bei kleinen Masken.
