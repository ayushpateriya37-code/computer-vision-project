"""
shadow_clone.py
-----------------
Procedural Shadow Clone Jutsu: captures a snapshot region of the current
frame around the user and re-draws translucent, slightly offset "ghost"
duplicates beside them -- approximating the classic Kage Bunshin effect
without needing person segmentation/matting models.
"""

import cv2
import numpy as np

from src import config
from src.effects.base_effect import BaseEffect


class ShadowCloneEffect(BaseEffect):
    def __init__(self, color_bgr):
        super().__init__(color_bgr, life_frames=55)
        self._snapshot = None
        self._crop_box = None  # (x1, y1, x2, y2)

    def trigger_with_frame(self, anchor_xy, frame):
        """Use this instead of trigger() so we can snapshot the current frame."""
        h, w = frame.shape[:2]
        cx, cy = int(anchor_xy[0]), int(anchor_xy[1])
        half_w, half_h = int(w * 0.16), int(h * 0.38)
        x1, y1 = max(0, cx - half_w), max(0, cy - half_h)
        x2, y2 = min(w, cx + half_w), min(h, cy + half_h)
        self._crop_box = (x1, y1, x2, y2)
        self._snapshot = frame[y1:y2, x1:x2].copy()
        self.trigger(anchor_xy)

    def render(self, frame):
        if self._snapshot is None or self._snapshot.size == 0:
            return frame

        h, w = frame.shape[:2]
        x1, y1, x2, y2 = self._crop_box
        crop_w, crop_h = x2 - x1, y2 - y1

        fade = max(0.0, 1.0 - self.progress)
        alpha = config.SHADOW_CLONE_ALPHA * fade

        n = config.SHADOW_CLONE_COUNT
        spacing = int(crop_w * 1.05)
        offsets = []
        for i in range(1, n + 1):
            offsets.append(-spacing * i)
            offsets.append(spacing * i)

        # Slight blue tint for a "chakra clone" look, computed once.
        tinted = cv2.addWeighted(self._snapshot, 0.8,
                                  np.full_like(self._snapshot, (255, 200, 150)), 0.2, 0)

        for dx in offsets[: n * 2]:
            nx1 = x1 + dx
            nx2 = nx1 + crop_w
            # Clamp into frame bounds (shift, don't skip) so a clone still
            # renders even when the seal is made near the left/right edge
            # or the frame is too narrow to fit the full offset spacing.
            if nx1 < 0:
                nx2 -= nx1
                nx1 = 0
            if nx2 > w:
                nx1 -= (nx2 - w)
                nx2 = w
            nx1, nx2 = max(0, nx1), min(w, nx2)
            if nx2 - nx1 != crop_w:
                continue  # frame narrower than one crop width -- skip cleanly

            roi = frame[y1:y2, nx1:nx2]
            if roi.shape != self._snapshot.shape:
                continue
            blended = cv2.addWeighted(roi, 1 - alpha, tinted, alpha, 0)
            frame[y1:y2, nx1:nx2] = blended

        return frame
