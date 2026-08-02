"""Optional local Ollama availability detection for Phoenix Boost."""

from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import threading
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
    _cache_lock = threading.Lock()

    @classmethod
    def invalidate_cache(cls) -> None:
        with cls._cache_lock:
            cls._cached_status = None

    @classmethod
    def cached_status(cls) -> OllamaStatus | None:
        with cls._cache_lock:
            return cls._cached_status

    @classmethod
    def detect(cls, timeout: float = 0.25, force: bool = False) -> OllamaStatus:
        if not force:
            cached = cls.cached_status()
            if cached is not None:
                return cached
        executable_found = shutil.which("ollama") is not None
        try:
            with urlopen(cls.API_URL, timeout=timeout) as response:
                reachable = 200 <= int(response.status) < 300
                payload = json.loads(response.read().decode("utf-8"))
            names = {str(model.get("name", "")) for model in payload.get("models", [])}
            status = OllamaStatus(
                installed=executable_found or reachable,
                reachable=reachable,
                model_available=reachable and cls.MODEL in names,
            )
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
        return status
