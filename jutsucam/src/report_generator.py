"""
report_generator.py
----------------------
MODULE 4b: Reporting & Analytics

Reads the CSV event log produced by session_logger.py and generates:
  - a plain-text/CSV summary (counts per jutsu, most-used jutsu, total
    sessions, total triggers)
  - a bar chart (PNG) of jutsu usage frequency

This is intentionally decoupled from the live video loop: it can be run
at any time via `python main.py report` against the accumulated log.
"""

import csv
import os
from collections import Counter
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")  # headless-safe backend, no display required
import matplotlib.pyplot as plt

from src import config
from src.session_logger import SessionLogger
from src.logger_setup import get_logger

logger = get_logger("report_generator")


def summarize(events: List[Dict]) -> Dict:
    counts = Counter(e["jutsu_display_name"] for e in events)
    sessions = set(e["session_id"] for e in events)
    return {
        "total_triggers": len(events),
        "total_sessions": len(sessions),
        "counts_by_jutsu": dict(counts.most_common()),
        "most_used_jutsu": counts.most_common(1)[0][0] if counts else None,
    }


def write_summary_csv(summary: Dict, out_path: str):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["total_triggers", summary["total_triggers"]])
        writer.writerow(["total_sessions", summary["total_sessions"]])
        writer.writerow(["most_used_jutsu", summary["most_used_jutsu"]])
        writer.writerow([])
        writer.writerow(["jutsu", "trigger_count"])
        for jutsu, count in summary["counts_by_jutsu"].items():
            writer.writerow([jutsu, count])


def plot_usage_chart(summary: Dict, out_path: str):
    counts = summary["counts_by_jutsu"]
    if not counts:
        logger.warning("No events to plot; skipping chart generation.")
        return None

    names = list(counts.keys())
    values = list(counts.values())

    plt.figure(figsize=(8, 5))
    bars = plt.bar(names, values, color="#3B6FE0")
    plt.title("Jutsu Usage Frequency")
    plt.xlabel("Jutsu")
    plt.ylabel("Times Triggered")
    plt.xticks(rotation=25, ha="right")
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                  str(val), ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def generate_report(csv_log_path: str = None, output_dir: str = None) -> Dict:
    """Full report pipeline: load events -> summarize -> write CSV + chart."""
    csv_log_path = csv_log_path or config.ATTENDANCE_LOG_CSV
    output_dir = output_dir or config.REPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    session_logger = SessionLogger(csv_path=csv_log_path)
    events = session_logger.read_all_events()
    summary = summarize(events)

    summary_csv_path = os.path.join(output_dir, "usage_summary.csv")
    chart_path = os.path.join(output_dir, "usage_chart.png")

    write_summary_csv(summary, summary_csv_path)
    chart_result = plot_usage_chart(summary, chart_path)

    logger.info("Report generated: %s events across %s sessions",
                summary["total_triggers"], summary["total_sessions"])

    return {
        "summary": summary,
        "summary_csv_path": summary_csv_path,
        "chart_path": chart_result,
    }
