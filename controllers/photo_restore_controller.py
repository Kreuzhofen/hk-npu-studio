"""
HK NPU STUDIO - Phoenix Architecture
AI Photo Restore Controller

Threaded UI boundary and workflow orchestrator for AIPhotoRestoreBackend.
Dispatches progress and completion callbacks to the main UI thread via ui_dispatch.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

from engine.backends.photo_restore_backend import (
    PhotoRestoreResult,
    PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
)
from engine.backends.fidesr_photo_restore_backend import (
    FiDeSRPhotoRestoreBackend,
)

logger = logging.getLogger(__name__)


class PhotoRestoreController:
    """Threaded UI boundary for the FiDeSR Strong NPU restore pipeline."""

    def __init__(
        self,
        backend: FiDeSRPhotoRestoreBackend | None = None,
        ui_dispatch: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self.backend = backend or FiDeSRPhotoRestoreBackend()
        self.ui_dispatch = ui_dispatch or (lambda callback: callback())
        self._thread: threading.Thread | None = None
        self._running_flag: bool = False

    @property
    def running(self) -> bool:
        """Returns True if a restoration job is actively executing."""
        if not self._running_flag:
            return False
        if self._thread is not None:
            return self._thread.is_alive()
        return True

    def start(
        self,
        *,
        image_path: str | Path,
        output_dir: str | Path | None = None,
        upscale_factor: int = 4,
        auto_colorize: bool = False,
        mode: str = "faithful",
        on_progress: Callable[[str, float, str | None], None] | None = None,
        on_complete: Callable[[PhotoRestoreResult], None] | None = None,
        asynchronous: bool = True,
    ) -> None:
        """
        Launches an AI Photo Restore job.
        Runs asynchronously in a background daemon thread by default.
        """
        if self.running:
            raise RuntimeError("A Photo Restore job is already in progress.")

        self._running_flag = True

        def progress_forwarder(phase: str, value: float, detail: str | None) -> None:
            if on_progress is not None:
                try:
                    self.ui_dispatch(lambda: on_progress(phase, value, detail))
                except Exception as exc:
                    logger.warning("Failed to dispatch progress update: %s", exc)

        def execute() -> None:
            result: PhotoRestoreResult
            try:
                try:
                    result = self.backend.restore(
                        image_path=image_path,
                        output_dir=output_dir,
                        upscale_factor=upscale_factor,
                        auto_colorize=auto_colorize,
                        mode=mode,
                        progress_callback=progress_forwarder,
                    )
                except Exception as exc:
                    result = PhotoRestoreResult(
                        success=False,
                        error_code=PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                        error_message=f"{type(exc).__name__}: {exc}",
                    )

                if on_complete is not None:
                    try:
                        self.ui_dispatch(lambda: on_complete(result))
                    except Exception as exc:
                        logger.error("Failed to dispatch completion callback: %s", exc)
            finally:
                self._running_flag = False

        if asynchronous:
            self._thread = threading.Thread(
                target=execute,
                name="ai-photo-restore-ui-worker",
                daemon=True,
            )
            self._thread.start()
        else:
            execute()

    def cancel(self) -> None:
        """Requests cooperative cancellation from the backend."""
        self.backend.cancel()

    def close(self) -> None:
        """Releases backend resources and cancels active operations."""
        self._running_flag = False
        self.backend.close()