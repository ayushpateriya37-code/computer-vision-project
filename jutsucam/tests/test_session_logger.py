"""
test_session_logger.py
------------------------
Unit tests for MODULE 4a (session_logger.py): the CSV-backed event log
that every triggered jutsu gets written to.
"""

import os
import tempfile

from src.session_logger import SessionLogger


def test_log_event_creates_file_with_header(tmp_path):
    csv_path = str(tmp_path / "events.csv")
    logger = SessionLogger(csv_path=csv_path)
    assert os.path.exists(csv_path)

    with open(csv_path) as f:
        header = f.readline().strip()
    assert header == "session_id,timestamp,jutsu_key,jutsu_display_name"


def test_log_event_appends_rows(tmp_path):
    csv_path = str(tmp_path / "events.csv")
    logger = SessionLogger(csv_path=csv_path)
    logger.log_event("rasengan")
    logger.log_event("chidori")

    events = logger.read_all_events()
    assert len(events) == 2
    assert events[0]["jutsu_key"] == "rasengan"
    assert events[1]["jutsu_key"] == "chidori"
    # every row should share the same session id
    assert events[0]["session_id"] == events[1]["session_id"] == logger.session_id


def test_read_all_events_on_missing_file_returns_empty_list(tmp_path):
    csv_path = str(tmp_path / "does_not_exist.csv")
    logger = SessionLogger(csv_path=csv_path)
    os.remove(csv_path)
    assert logger.read_all_events() == []


def test_display_name_resolved_from_registry(tmp_path):
    csv_path = str(tmp_path / "events.csv")
    logger = SessionLogger(csv_path=csv_path)
    logger.log_event("shadow_clone")
    events = logger.read_all_events()
    assert events[0]["jutsu_display_name"] != "shadow_clone"  # resolved to a display name
    assert "Clone" in events[0]["jutsu_display_name"] or "clone" in events[0]["jutsu_display_name"].lower()
