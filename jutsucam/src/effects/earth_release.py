"""
earth_release.py
-------------------
Procedural Earth Release: a jagged rock pillar rises from the ground
near the user's hand, built from a stack of randomly-jittered polygon
"strata" bands in earthy tones, growing upward over time.
"""

import random
import cv2
import numpy as np

from src import config
from src.effects.base_effect import BaseEffect


class EarthReleaseEffect(BaseEffect):
    def __init__(self, color_bgr):
        super().__init__(color_bgr, life_frames=config.EARTH_PILLAR_GROW_FRAMES + 25)

    def on_trigger(self):
        # jitter offsets for each band so the pillar edge looks jagged/rocky
        self._band_jitter = [random.uniform(-10, 10) for _ in range(14)]

    def render(self, frame):
        h, w = frame.shape[:2]
        cx = int(self.anchor[0])
        ground_y = h  # pillar rises from the bottom of the frame
        grow = min(1.0, self.age / config.EARTH_PILLAR_GROW_FRAMES)
        pillar_height = int(grow * h * 0.55)
        pillar_width = 90

        overlay = frame.copy()
        top_y = ground_y - pillar_height
        num_bands = max(2, int(14 * grow))
        band_h = max(1, pillar_height // max(1, num_bands))

        earth_tones = [(40, 70, 90), (35, 90, 110), (45, 110, 130), (60, 130, 150)]

        for i in range(num_bands):
            y1 = ground_y - i * band_h
            y2 = y1 - band_h
            jitter = self._band_jitter[i % len(self._band_jitter)]
            half_w = pillar_width * (0.55 + 0.45 * (i / max(1, num_bands)))
            x1 = int(cx - half_w + jitter)
            x2 = int(cx + half_w + jitter)
            color = earth_tones[i % len(earth_tones)]
            cv2.rectangle(overlay, (x1, y2), (x2, y1), color, -1)

        # blend the pillar in (not full opaque, so the scene stays visible)
        frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        return frame
