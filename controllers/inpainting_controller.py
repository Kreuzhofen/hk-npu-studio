from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from engine.backends.rorem_dlc_inpainting_adapter import RORemDlcInpaintingAdapter, RORemDlcResult


class InpaintingController:
    """Threaded Studio boundary for RORem object removal on Qualcomm HTP."""

    def __init__(
        self,
        adapter: RORemDlcInpaintingAdapter | None = None,
        ui_dispatch: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self.adapter = adapter or RORemDlcInpaintingAdapter()
        self.ui_dispatch = ui_dispatch or (lambda callback: callback())
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        *,
        input_image_path: str | Path,
        mask_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        steps: int = 1,
        seed: int = 20260830,
        negative_prompt: str | None = None,
        on_progress: Callable[[str, float, str | None], None] | None = None,
        on_complete: Callable[[RORemDlcResult], None] | None = None,
        asynchronous: bool = True,
    ) -> None:
        if self.running:
            raise RuntimeError("Inpainting is already running")

        def progress(phase: str, value: float, detail: str | None) -> None:
            if on_progress is not None:
                self.ui_dispatch(lambda: on_progress(phase, value, detail))

        def execute() -> None:
            try:
                result = self.adapter.run(
                    input_image_path,
                    mask_image_path,
                    prompt,
                    output_path,
                    negative_prompt=negative_prompt or "",
                    steps=steps,
                    seed=seed,
                    progress_callback=progress,
                )
            except Exception as exc:
                result = RORemDlcResult(
                    success=False,
                    error_code="ERR_NPU_INFERENCE_FAILED",
                    error_message=f"{type(exc).__name__}: {exc}",
                )
            if on_complete is not None:
                self.ui_dispatch(lambda: on_complete(result))

        if asynchronous:
            self._thread = threading.Thread(target=execute, name="rorem-inpainting-ui", daemon=True)
            self._thread.start()
        else:
            execute()

    def cancel(self) -> None:
        self.adapter.cancel()

    def close(self) -> None:
        close = getattr(self.adapter, "close", None)
        if close is not None:
            close()
