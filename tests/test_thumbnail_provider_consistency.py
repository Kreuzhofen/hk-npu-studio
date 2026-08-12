from __future__ import annotations

import os
import queue
from unittest.mock import MagicMock, patch

from widgets.phoenix.gallery.thumbnail_provider import ThumbnailProvider


def test_changed_file_gets_separate_thumbnail_request(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"first")
    provider = ThumbnailProvider.__new__(ThumbnailProvider)
    provider._thumbnail_cache = {}
    provider._pending_callbacks = {}
    provider._request_queue = queue.Queue()
    callback = lambda photo: None

    provider.get_thumbnail(image, 124, callback)
    first_request = provider._request_queue.get_nowait()
    image.write_bytes(b"second-version")
    os.utime(image, None)
    provider.get_thumbnail(image, 124, callback)
    second_request = provider._request_queue.get_nowait()

    assert first_request.cache_key != second_request.cache_key
    assert len(provider._pending_callbacks) == 2


def test_new_signature_evicts_stale_cached_thumbnail(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"first")
    provider = ThumbnailProvider.__new__(ThumbnailProvider)
    provider._thumbnail_cache = {}
    provider._pending_callbacks = {}
    provider._request_queue = queue.Queue()
    callback = lambda photo: None
    old_stat = image.stat()
    old_key = (
        image.resolve(),
        124,
        int(old_stat.st_mtime_ns),
        int(old_stat.st_size),
    )
    provider._thumbnail_cache[old_key] = object()
    image.write_bytes(b"changed-size")
    os.utime(image, None)

    provider.get_thumbnail(image, 124, callback)

    assert old_key not in provider._thumbnail_cache


def test_ui_poll_processes_large_thumbnail_results_in_small_batches():
    provider = ThumbnailProvider.__new__(ThumbnailProvider)
    provider.RESPONSES_PER_TICK = 4
    provider._is_cleaned_up = False
    provider._poll_handle = None
    provider.master = MagicMock()
    provider.master.winfo_exists.return_value = True
    provider._response_queue = queue.Queue()
    provider._pending_callbacks = {}
    provider._thumbnail_cache = {}
    for index in range(10):
        request = MagicMock()
        request.cache_key = (index, 124, 0, 0)
        request.callback = MagicMock()
        provider._response_queue.put((request, MagicMock()))
    with patch("widgets.phoenix.gallery.thumbnail_provider.ImageTk.PhotoImage", return_value=MagicMock()):
        provider._poll_responses()
    assert provider._response_queue.qsize() == 6
    provider.master.after.assert_called_once()
