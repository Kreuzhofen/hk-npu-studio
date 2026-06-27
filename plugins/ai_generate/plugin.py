from pathlib import Path
from config import WORKFLOWS_DIR
from modules.comfy_backend import check_comfyui, load_workflow, inject_prompt, submit_prompt

class Plugin:
    id = "ai_generate"
    name = "AI Generate"
    category = "Image Generation"
    engine = "ComfyUI API"
    icon = "🎨"
    description = "Prompt-zu-Bild über lokalen ComfyUI-Server. Benötigt einen exportierten API-Workflow."
    kind = "text_to_image"

    @property
    def available(self):
        ok, _ = check_comfyui()
        return ok

    def status(self):
        ok, _ = check_comfyui()
        return "ComfyUI erreichbar" if ok else "ComfyUI nicht erreichbar"

    def details(self):
        ok, info = check_comfyui()
        return (
            f"{self.name}\n\n"
            f"Kategorie: {self.category}\n"
            f"Engine: {self.engine}\n"
            f"Status: {self.status()}\n"
            f"Workflow: {WORKFLOWS_DIR / 'text2image_api.json'}\n\n"
            f"{self.description}\n\n"
            f"ComfyUI-Test:\n{info}"
        )

    def run_prompt(self, prompt: str, negative_prompt: str = "", log=None, status=None, percent=None):
        if status:
            status("ComfyUI wird geprüft...")

        ok, info = check_comfyui()
        if not ok:
            raise RuntimeError(
                "ComfyUI ist nicht erreichbar.\n\n"
                "Bitte ComfyUI starten und prüfen, ob es unter http://127.0.0.1:8188 läuft.\n\n"
                f"Fehler: {info}"
            )

        if log:
            log("ComfyUI erreichbar.")
            log("Lade Workflow...")

        workflow = load_workflow()
        workflow = inject_prompt(workflow, prompt, negative_prompt)

        if status:
            status("Sende Prompt an ComfyUI...")
        if percent:
            percent(20)
        if log:
            log("Sende Prompt an /prompt ...")

        result = submit_prompt(workflow)

        if percent:
            percent(100)
        if status:
            status("Prompt gesendet")

        if log:
            log("ComfyUI Antwort:")
            log(str(result))
            log("")
            log("Hinweis: Das Ergebnis wird aktuell in ComfyUI gespeichert/angezeigt.")
            log("Das automatische Abholen der fertigen Bilddatei bauen wir als nächsten Schritt ein.")

        return result
