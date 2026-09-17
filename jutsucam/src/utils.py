"""
utils.py
---------
Small shared helpers: on-screen HUD text/FPS overlay. Kept separate from
main.py so the CLI loop stays readable.
"""

import time
import cv2


class FPSCounter:
    def __init__(self, smoothing=0.9):
        self._last_time = time.time()
        self._fps = 0.0
        self._smoothing = smoothing

    def tick(self) -> float:
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        if dt > 0:
            instant_fps = 1.0 / dt
            self._fps = (self._smoothing * self._fps
                         + (1 - self._smoothing) * instant_fps)
        return self._fps


def draw_hud(frame, fps: float, candidate: str, progress: float, last_triggered: str,
             active_effects: int):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 70), (20, 20, 20), -1)
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Active FX: {active_effects}", (150, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)

    cand_text = f"Recognizing: {candidate or '-'}"
    cv2.putText(frame, cand_text, (10, 46),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 1, cv2.LINE_AA)

    # progress bar
    bar_x, bar_y, bar_w, bar_h = 220, 36, 150, 12
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), 1)
    fill_w = int(bar_w * max(0.0, min(1.0, progress)))
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 220, 255), -1)

    if last_triggered:
        cv2.putText(frame, f"Last jutsu: {last_triggered}", (10, 66),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.putText(frame, "Press 'q' to quit", (w - 180, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
    return frame
