from __future__ import annotations

import json
import os
from pathlib import Path
import config

class SettingsManager:
    """Manages persistent application settings/preferences stored in preferences.json."""

    @staticmethod
    def get_preferences_path() -> Path:
        return config.PREFERENCES_PATH

    @classmethod
    def load_settings(cls) -> dict[str, str]:
        path = cls.get_preferences_path()
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {}

    @classmethod
    def save_settings(cls, settings: dict[str, str]) -> bool:
        path = cls.get_preferences_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            # Merge with existing settings
            current = cls.load_settings()
            current.update(settings)
            
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2)
            temp_path.replace(path)
            
            # Apply hf_token dynamically to config and environment
            if "hf_token" in settings:
                token = settings["hf_token"]
                config.HF_TOKEN = token
                if token:
                    os.environ["HF_TOKEN"] = token
                else:
                    os.environ.pop("HF_TOKEN", None)
                    
            return True
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            return False

    @classmethod
    def get_hf_token(cls) -> str:
        # Check env first, then preferences
        token = os.environ.get("HF_TOKEN")
        if not token:
            prefs = cls.load_settings()
            token = prefs.get("hf_token", "")
        return token

    @classmethod
    def test_hf_token(cls, token: str) -> tuple[bool, str]:
        import urllib.request
        import urllib.error
        from app.i18n import tr

        if not token:
            return False, tr("no_token_provided", "Kein Token angegeben.")
        
        url = "https://huggingface.co/api/whoami-v2"
        req = urllib.request.Request(url, headers={
            "User-Agent": "SnapdragonAIStudio/2.0",
            "Authorization": f"Bearer {token}"
        })
        try:
            with urllib.request.urlopen(req, timeout=10.0) as response:
                if response.code == 200:
                    return True, tr("token_test_success", "Token ist gültig.")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, tr("token_test_unauthorized", "Ungültiger Token (401 Unauthorized).")
            return False, f"HTTP Error {e.code}: {e.reason}"
        except Exception as e:
            return False, f"Verbindungsfehler: {e}"
