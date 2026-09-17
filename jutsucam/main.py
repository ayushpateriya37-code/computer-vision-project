#!/usr/bin/env python3
"""
main.py
--------
JutsuCam CLI entry point.

Usage
-----
Run a live jutsu-recognition session from a webcam:
    python main.py run --source 0

Run against a pre-recorded video file (useful for evaluators without a
webcam, or for reproducible demos):
    python main.py run --source demo_videos/sample.mp4

Run headless (no GUI window) and save the annotated result to a file --
useful on machines/CI without a display:
    python main.py run --source demo_videos/sample.mp4 --headless --output out.mp4

Generate the usage analytics report from all logged sessions so far:
    python main.py report
"""

import argparse
import sys

import cv2

from src import config
from src.hand_tracker import HandTracker
from src.gesture_classifier import GestureClassifier
from src.vfx_engine import VFXEngine
from src.session_logger import SessionLogger
from src.report_generator import generate_report
from src.utils import FPSCounter, draw_hud
from src.logger_setup import get_logger

logger = get_logger("main")


def _open_capture(source: str):
    """Accepts either a webcam index ('0', '1', ...) or a video file path."""
    cap_source = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(cap_source)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video source '{source}'. If using a webcam, "
            f"check the device index (try 0 or 1). If using a file, check "
            f"the path is correct."
        )
    return cap


def run_session(source: str, headless: bool, output_path: str, max_frames: int):
    logger.info("Starting session | source=%s headless=%s", source, headless)

    try:
        cap = _open_capture(source)
    except RuntimeError as exc:
        logger.error(str(exc))
        print(f"[ERROR] {exc}")
        sys.exit(1)

    tracker = HandTracker(
        max_num_hands=config.MAX_NUM_HANDS,
        min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
    )
    classifier = GestureClassifier()
    vfx = VFXEngine()
    session_logger = SessionLogger()
    fps_counter = FPSCounter()

    writer = None
    last_triggered_display = None
    frame_count = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                logger.info("End of video stream reached.")
                break

            frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
            if config.FLIP_HORIZONTAL and source.isdigit():
                frame = cv2.flip(frame, 1)

            hands = tracker.process(frame)
            triggered, candidate, progress, features = classifier.update(hands)

            anchor = None
            if features.num_hands > 0:
                # Average palm center across all detected hands so a
                # two-hand pose (Shadow Clone) anchors between the
                # crossed wrists rather than favouring hand[0].
                ax = sum(h.palm_center[0] for h in features.hands) / features.num_hands
                ay = sum(h.palm_center[1] for h in features.hands) / features.num_hands
                anchor = (ax, ay)

            if triggered and anchor is not None:
                vfx.trigger(triggered, anchor, frame)
                session_logger.log_event(triggered)
                last_triggered_display = config.JUTSU_REGISTRY[triggered]["display_name"]
            elif candidate is not None and anchor is not None:
                # keep effects that need to track the hand (rare) updated
                pass

            frame = vfx.update_and_render(frame)

            fps = fps_counter.tick()
            frame = draw_hud(frame, fps, candidate, progress,
                              last_triggered_display, vfx.active_count)

            if headless:
                if writer is None and output_path:
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    writer = cv2.VideoWriter(output_path, fourcc, config.TARGET_FPS,
                                              (config.FRAME_WIDTH, config.FRAME_HEIGHT))
                if writer is not None:
                    writer.write(frame)
            else:
                try:
                    cv2.imshow("JutsuCam", frame)
                except cv2.error as exc:
                    logger.error("No display available (%s). Re-run with --headless.", exc)
                    print("[ERROR] No display available. Re-run with --headless "
                          "and --output <file.mp4> to save the result instead.")
                    break
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    logger.info("Quit key pressed by user.")
                    break

            frame_count += 1
            if max_frames and frame_count >= max_frames:
                logger.info("Reached max_frames=%s, stopping.", max_frames)
                break

    finally:
        cap.release()
        tracker.close()
        if writer is not None:
            writer.release()
        if not headless:
            cv2.destroyAllWindows()
        logger.info("Session ended. Total frames processed: %s", frame_count)
        print(f"Session ended. {frame_count} frames processed. "
              f"Events logged to {config.ATTENDANCE_LOG_CSV}")


def run_report():
    result = generate_report()
    summary = result["summary"]
    print("\n=== JutsuCam Usage Report ===")
    print(f"Total triggers   : {summary['total_triggers']}")
    print(f"Total sessions   : {summary['total_sessions']}")
    print(f"Most used jutsu  : {summary['most_used_jutsu']}")
    print("\nBreakdown:")
    for jutsu, count in summary["counts_by_jutsu"].items():
        print(f"  - {jutsu}: {count}")
    print(f"\nSummary CSV : {result['summary_csv_path']}")
    if result["chart_path"]:
        print(f"Usage chart : {result['chart_path']}")
    print()


def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="jutsucam",
        description="JutsuCam -- real-time hand-gesture-triggered anime VFX system.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Start a live/video jutsu-recognition session.")
    run_parser.add_argument("--source", default="0",
                             help="Webcam index (e.g. 0) or path to a video file. Default: 0")
    run_parser.add_argument("--headless", action="store_true",
                             help="Run without opening a GUI window (writes to --output instead).")
    run_parser.add_argument("--output", default="data/logs/session_output.mp4",
                             help="Output video path when --headless is set.")
    run_parser.add_argument("--max-frames", type=int, default=0,
                             help="Stop after N frames (0 = unlimited). Useful for automated testing.")

    subparsers.add_parser("report", help="Generate the usage analytics report from logged sessions.")

    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.command == "run":
        run_session(args.source, args.headless, args.output, args.max_frames)
    elif args.command == "report":
        run_report()


if __name__ == "__main__":
    main()
