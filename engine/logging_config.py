from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock

from config import LOG_BACKUP_COUNT, LOG_DIR, LOG_LEVEL, LOG_MAX_BYTES


LOG_FILE_NAME = "hk_npu_studio.log"
_HANDLER_MARKER = "_snapdragon_ai_managed_handler"
_CONFIG_LOCK = Lock()


def configure_logging(
    log_dir: str | Path | None = None,
    *,
    level: int | str = LOG_LEVEL,
    max_bytes: int = LOG_MAX_BYTES,
    backup_count: int = LOG_BACKUP_COUNT,
    force: bool = False,
) -> Path:
    """Konfiguriert eine zentrale, rotierende UTF-8-Protokolldatei."""
    target_dir = Path(log_dir) if log_dir is not None else LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / LOG_FILE_NAME

    with _CONFIG_LOCK:
        root_logger = logging.getLogger()
        managed_handlers = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, _HANDLER_MARKER, False)
        ]
        expected_path = log_path.resolve()
        for handler in managed_handlers:
            current_path = Path(getattr(handler, "baseFilename", "")).resolve()
            if not force and current_path == expected_path:
                root_logger.setLevel(level)
                return log_path
            root_logger.removeHandler(handler)
            handler.close()

        handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        setattr(handler, _HANDLER_MARKER, True)
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(threadName)s | %(message)s"
            )
        )
        root_logger.addHandler(handler)
        root_logger.setLevel(level)
    return log_path


def get_logger(name: str) -> logging.Logger:
    """Liefert einen Logger und stellt die zentrale Konfiguration sicher."""
    root_logger = logging.getLogger()
    if not any(
        getattr(handler, _HANDLER_MARKER, False)
        for handler in root_logger.handlers
    ):
        configure_logging()
    return logging.getLogger(name)


def close_logging() -> None:
    """Schließt ausschließlich die von Phoenix verwalteten Handler."""
    with _CONFIG_LOCK:
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            if getattr(handler, _HANDLER_MARKER, False):
                root_logger.removeHandler(handler)
                handler.close()
