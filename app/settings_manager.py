from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import config
from app.configuration_manager import ConfigurationManager

class SettingsManager:
    """Manages persistent application settings/preferences stored in preferences.json."""

    CPU_EXECUTION_PROVIDER = "CPUExecutionProvider"
    QNN_EXECUTION_PROVIDER = "QNNExecutionProvider"

    @staticmethod
    def get_preferences_path() -> Path:
        return config.PREFERENCES_PATH

    @classmethod
    def load_settings(cls) -> dict[str, Any]:
        return ConfigurationManager(cls.get_preferences_path()).load()

    @classmethod
    def save_settings(cls, settings: dict[str, Any]) -> bool:
        saved = ConfigurationManager(cls.get_preferences_path()).save(settings)
        if saved and "hf_token" in settings:
            token = str(settings["hf_token"]).strip()
            config.HF_TOKEN = token
            if token:
                os.environ["HF_TOKEN"] = token
            else:
                os.environ.pop("HF_TOKEN", None)
        return saved

    @classmethod
    def get_execution_provider(cls) -> str:
        """Return the canonical ONNX Runtime provider selected by the user."""
        preferences = cls.load_settings()
        provider = str(preferences.get("execution_provider", "QNN EP")).strip()
        hardware_accel = str(preferences.get("hardware_accel", "True")).casefold() == "true"
        if provider in {"CPU EP", "CPU"} or not hardware_accel:
            return cls.CPU_EXECUTION_PROVIDER
        return cls.QNN_EXECUTION_PROVIDER

    @classmethod
    def get_execution_provider_label(cls) -> str:
        """Return the persisted provider in the user-facing settings terminology."""
        if cls.get_execution_provider() == cls.CPU_EXECUTION_PROVIDER:
            return "CPU EP"
        return "QNN EP"

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
            "User-Agent": "HKNPUStudio/2.0",
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
