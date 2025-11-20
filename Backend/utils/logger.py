import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "info.log")

os.makedirs(LOG_DIR, exist_ok=True)

_DEFAULT_LOG_LEVEL = os.getenv("AI_ANIME_LOG_LEVEL", "INFO").upper()
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _configure_root_logger() -> logging.Logger:
    root_logger = logging.getLogger("ai_anime_recommender")
    if root_logger.handlers:
        return root_logger

    root_logger.setLevel(getattr(logging, _DEFAULT_LOG_LEVEL, logging.INFO))

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    root_logger.propagate = False

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a configured logger instance.

    Parameters
    ----------
    name:
        Optional logger name. When omitted, the shared application logger is returned.
    """
    root_logger = _configure_root_logger()
    if not name:
        return root_logger
    return root_logger.getChild(name)

