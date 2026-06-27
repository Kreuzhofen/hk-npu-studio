import json
from pathlib import Path
from config import BASE, MODEL_REGISTRY

def load_models():
    if not MODEL_REGISTRY.exists():
        return []

    data = json.loads(MODEL_REGISTRY.read_text(encoding="utf-8"))

    for item in data:
        rel_file = item.get("file") or ""
        if item.get("status") == "installed_if_file_exists":
            file_path = BASE / rel_file
            item["resolved_path"] = str(file_path)
            item["available"] = file_path.exists()
            item["display_status"] = "Installiert" if file_path.exists() else "Datei fehlt"
        elif item.get("status") == "planned":
            item["resolved_path"] = ""
            item["available"] = False
            item["display_status"] = "Geplant"
        else:
            item["resolved_path"] = ""
            item["available"] = False
            item["display_status"] = item.get("status", "Unbekannt")

    return data
