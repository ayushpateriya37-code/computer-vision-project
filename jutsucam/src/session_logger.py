"""
session_logger.py
-------------------
MODULE 4a: Session Logger

Persists every jutsu trigger event (timestamp, jutsu name, session id)
to a CSV file, and exposes a small read API used by report_generator.py.
Uses SQLite-free flat CSV storage deliberately: it keeps the project's
"storage design" trivially inspectable/portable for evaluation, while
still satisfying the course's requirement for a clear input/output data
pipeline.
"""

import csv
import os
import uuid
from datetime import datetime
from typing import List, Dict

from src import config
from src.logger_setup import get_logger

logger = get_logger("session_logger")

CSV_HEADERS = ["session_id", "timestamp", "jutsu_key", "jutsu_display_name"]


class SessionLogger:
    def __init__(self, csv_path: str = None):
        self.csv_path = csv_path or config.ATTENDANCE_LOG_CSV
        self.session_id = str(uuid.uuid4())[:8]
        self._ensure_file()
        logger.info("Session started: %s -> %s", self.session_id, self.csv_path)

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)

    def log_event(self, jutsu_key: str):
        display_name = config.JUTSU_REGISTRY.get(jutsu_key, {}).get("display_name", jutsu_key)
        row = [self.session_id, datetime.now().isoformat(timespec="seconds"),
               jutsu_key, display_name]
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)
            logger.info("Jutsu triggered: %s (%s)", display_name, jutsu_key)
        except OSError as exc:
            # Reliability requirement: a logging failure must never crash
            # the live video loop.
            logger.error("Failed to write session log entry: %s", exc)

    def read_all_events(self) -> List[Dict]:
        if not os.path.exists(self.csv_path):
            return []
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
