import json
import urllib.request
import urllib.error
import uuid
from pathlib import Path

from config import COMFYUI_BASE_URL, WORKFLOWS_DIR

def _request_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def check_comfyui():
    try:
        data = _request_json(f"{COMFYUI_BASE_URL}/system_stats", timeout=3)
        return True, data
    except Exception as e:
        return False, str(e)

def load_workflow(workflow_path=None):
    if workflow_path is None:
        workflow_path = WORKFLOWS_DIR / "text2image_api.json"
    workflow_path = Path(workflow_path)

    if not workflow_path.exists():
        raise FileNotFoundError(
            f"Workflow fehlt: {workflow_path}\n\n"
            "In ComfyUI bitte einen funktionierenden Workflow als API-JSON exportieren "
            "und als C:\\SnapdragonAI\\workflows\\text2image_api.json speichern."
        )

    return json.loads(workflow_path.read_text(encoding="utf-8"))

def inject_prompt(workflow, prompt, negative_prompt=""):
    """
    Best-effort: ersetzt Textfelder in CLIPTextEncode-Knoten.
    Der erste passende Text wird Positive Prompt, der zweite Negative Prompt.
    """
    count = 0

    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if class_type == "CLIPTextEncode" and "text" in inputs:
            if count == 0:
                inputs["text"] = prompt
                count += 1
            elif count == 1 and negative_prompt:
                inputs["text"] = negative_prompt
                count += 1

    return workflow

def submit_prompt(workflow):
    client_id = str(uuid.uuid4())
    payload = {
        "prompt": workflow,
        "client_id": client_id,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_BASE_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ComfyUI HTTP-Fehler {e.code}:\n{body}")
