"""Optional local Ollama availability detection for Phoenix Boost."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import shutil
import threading
import time
from pathlib import Path
from urllib.request import urlopen


@dataclass(frozen=True)
class OllamaStatus:
    installed: bool
    reachable: bool
    model_available: bool = False

    @property
    def available(self) -> bool:
        return self.installed and self.reachable

    @property
    def ai_ready(self) -> bool:
        return self.available and self.model_available


class OllamaStatusService:
    """Detect Ollama without starting it or requiring additional packages."""

    API_URL = "http://127.0.0.1:11434/api/tags"
    DOWNLOAD_URL = "https://ollama.com/download/windows"
    MODEL = "qwen2.5:3b"
    _cached_status: OllamaStatus | None = None
    _cached_time: float = 0.0
    CACHE_LIFETIME_SECONDS = 3.0
    _cache_lock = threading.Lock()

    @classmethod
    def invalidate_cache(cls) -> None:
        with cls._cache_lock:
            cls._cached_status = None
            cls._cached_time = 0.0

    @classmethod
    def cached_status(cls) -> OllamaStatus | None:
        with cls._cache_lock:
            if cls._cached_status is not None:
                if time.monotonic() - cls._cached_time < cls.CACHE_LIFETIME_SECONDS:
                    return cls._cached_status
                else:
                    cls._cached_status = None
            return None

    @classmethod
    def detect(cls, timeout: float = 0.25, force: bool = False) -> OllamaStatus:
        if not force:
            cached = cls.cached_status()
            if cached is not None:
                return cached

        # Check PATH
        executable_found = shutil.which("ollama") is not None
        if not executable_found:
            # Check default installation path on Windows
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                default_path = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
                if default_path.is_file():
                    executable_found = True

        try:
            with urlopen(cls.API_URL, timeout=timeout) as response:
                reachable = 200 <= int(response.status) < 300
                payload = json.loads(response.read().decode("utf-8"))

            if isinstance(payload, dict) and "models" in payload and isinstance(payload["models"], list):
                names = {str(model.get("name", "")) for model in payload["models"] if isinstance(model, dict)}
                status = OllamaStatus(
                    installed=executable_found or reachable,
                    reachable=reachable,
                    model_available=reachable and cls.MODEL in names,
                )
            else:
                # Payload doesn't look like Ollama
                status = OllamaStatus(installed=executable_found, reachable=False, model_available=False)
        except OSError:
            status = OllamaStatus(installed=executable_found, reachable=False)
            if executable_found:
                cls.invalidate_cache()
                return status
        except (ValueError, TypeError, json.JSONDecodeError):
            cls.invalidate_cache()
            return OllamaStatus(installed=executable_found, reachable=False)

        with cls._cache_lock:
            cls._cached_status = status
            cls._cached_time = time.monotonic()
        return status
