from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
from collections.abc import Callable

from widgets.phoenix.gallery.thumbnail_service import ThumbnailService


class ThumbnailRequest:
    """Represents a request to load a thumbnail asynchronously."""
    def __init__(
        self,
        image_path: Path,
        size: int,
        callback: Callable[[ImageTk.PhotoImage], None],
        cache_key: tuple[Path, int, int, int] | tuple[Path, int, int, None],
    ) -> None:
        self.image_path = image_path
        self.size = size
        self.callback = callback
        self.cache_key = cache_key


class ThumbnailProvider:
    """Provides thumbnails for the Gallery UI, loading them asynchronously via background threads."""

    RESPONSES_PER_TICK = 4

    def __init__(self, master: tk.Misc, service: ThumbnailService | None = None) -> None:
        self.master = master
        self.service = service or ThumbnailService()
        self._poll_handle: str | None = None
        self._is_cleaned_up: bool = False
        
        # Queue for incoming requests
        self._request_queue: queue.Queue[ThumbnailRequest] = queue.Queue()
        
        # Queue for processed PIL images waiting to be converted to PhotoImage in UI thread
        self._response_queue: queue.Queue[tuple[ThumbnailRequest, Image.Image | None]] = queue.Queue()
        
        # Dictionary mapping (Path, size) to list of callbacks waiting for this thumbnail
        self._pending_callbacks: dict[
            tuple[Path, int, int, int | None],
            list[Callable[[ImageTk.PhotoImage], None]],
        ] = {}

        # Cache finished thumbnails by file signature so refreshes can reuse them without flicker.
        self._thumbnail_cache: dict[tuple[Path, int, int, int | None], ImageTk.PhotoImage] = {}
        
        # Bind destroy event to cleanup resources
        self.master.bind("<Destroy>", lambda e: self.cleanup(), add="+")

        # Start background worker thread
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        
        # Start UI thread polling loop
        self._poll_responses()

    def get_thumbnail(
        self,
        image_path: Path,
        size: int,
        callback: Callable[[ImageTk.PhotoImage], None]
    ) -> ImageTk.PhotoImage | None:
        """
        Queues an async request and returns None (placeholder should be displayed).
        Prepared for future cache lookup and storage.
        """
        try:
            stat = image_path.stat()
            cache_key: tuple[Path, int, int, int | None] = (
                image_path.resolve(),
                size,
                int(stat.st_mtime_ns),
                int(stat.st_size),
            )
        except Exception:
            cache_key = (image_path.resolve(), size, 0, None)

        cached_thumbnail = self._thumbnail_cache.get(cache_key)
        if cached_thumbnail is not None:
            return cached_thumbnail

        path_key = image_path.resolve()
        stale_keys = [
            key
            for key in self._thumbnail_cache
            if key[0] == path_key and key[1] == size and key != cache_key
        ]
        for key in stale_keys:
            self._thumbnail_cache.pop(key, None)
        
        # If already pending, register callback; otherwise, queue request
        if cache_key in self._pending_callbacks:
            self._pending_callbacks[cache_key].append(callback)
        else:
            self._pending_callbacks[cache_key] = [callback]
            self._request_queue.put(ThumbnailRequest(image_path, size, callback, cache_key))
            
        return None

    def _worker_loop(self) -> None:
        """Loop running in background thread to load and resize images."""
        while not getattr(self, "_is_cleaned_up", False):
            try:
                request = self._request_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                with Image.open(request.image_path) as img:
                    # CPU-intensive resize and orientation handling
                    resized_img = self.service.prepare_thumbnail_image(img, request.size)
                    self._response_queue.put((request, resized_img))
            except Exception:
                self._response_queue.put((request, None))
            finally:
                self._request_queue.task_done()

    def _poll_responses(self) -> None:
        """Periodic check in UI thread for finished thumbnails."""
        if getattr(self, "_is_cleaned_up", False):
            return
        # Process all available responses in this tick
        processed = 0
        while processed < self.RESPONSES_PER_TICK and not self._response_queue.empty():
            try:
                request, resized_img = self._response_queue.get_nowait()
                processed += 1
                # Fetch all registered callbacks for this key, falling back to the request's callback if none found
                callbacks = self._pending_callbacks.pop(request.cache_key, [])
                if not callbacks:
                    callbacks = [request.callback]
                
                if resized_img is not None:
                    # Convert to PhotoImage in UI thread
                    photo_image = ImageTk.PhotoImage(resized_img, master=self.master)
                    self._thumbnail_cache[request.cache_key] = photo_image
                    
                    # Invoke all callbacks
                    for cb in callbacks:
                        try:
                            cb(photo_image)
                        except Exception:
                            pass
            except queue.Empty:
                break
            except Exception:
                pass
                
        # Schedule next check if UI exists
        if self.master.winfo_exists() and not getattr(self, "_is_cleaned_up", False):
            self._poll_handle = self.master.after(30, self._poll_responses)

    def cleanup(self) -> None:
        """Stops the polling loop, clears caches, and exits worker thread."""
        self._is_cleaned_up = True
        if hasattr(self, "_poll_handle") and self._poll_handle is not None:
            try:
                self.master.after_cancel(self._poll_handle)
            except Exception:
                pass
            self._poll_handle = None
        self.clear_cache()
        while not self._request_queue.empty():
            try:
                self._request_queue.get_nowait()
                self._request_queue.task_done()
            except Exception:
                pass

    def clear_cache(self) -> None:
        """Drops all cached thumbnails."""
        self._thumbnail_cache.clear()
