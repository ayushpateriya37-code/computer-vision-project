"""
logger_setup.py
-----------------
Centralized logging configuration (addresses the "Logging / Monitoring"
non-functional requirement). All modules should obtain their logger via
get_logger(__name__) rather than configuring logging themselves, so
format/level/output stays consistent project-wide.
"""

import logging
import os

from src import config

_LOG_FILE = os.path.join(config.LOG_DIR, "jutsucam.log")
_CONFIGURED = False


def _configure_root_logger():
    global _CONFIGURED
    if _CONFIGURED:
        return
    os.makedirs(config.LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root = logging.getLogger("jutsucam")
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root_logger()
    return logging.getLogger(f"jutsucam.{name}")
