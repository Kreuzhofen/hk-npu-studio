SnapdragonAI Studio v1.0 ComfyUI Backend

Neu:
- AI Generate kann jetzt mit lokalem ComfyUI sprechen.
- Prüft ComfyUI über http://127.0.0.1:8188/system_stats
- Sendet Workflows an http://127.0.0.1:8188/prompt
- Benötigt eine ComfyUI API-Workflow-Datei:
  C:\SnapdragonAI\workflows\text2image_api.json

Installation:
1. ZIP entpacken.
2. Inhalt nach C:\SnapdragonAI kopieren und überschreiben.
3. ComfyUI starten.
4. In ComfyUI einen funktionierenden Text2Image-Workflow als API-JSON exportieren.
5. Datei als C:\SnapdragonAI\workflows\text2image_api.json speichern.
6. Start: start_gui.bat oder python gui.py
