"""
water_dragon.py
------------------
Procedural Water Dragon Jutsu: a sweeping curved stream of blue droplet
particles, mirroring fire_dragon.py's construction but with a cooler
color palette and a wider, more fluid sweep to suggest water.
"""

import random
import cv2
import numpy as np

from src import config
from src.effects.base_effect import BaseEffect
from src.effects.fire_dragon import _bezier


class WaterDragonEffect(BaseEffect):
    def __init__(self, color_bgr):
        super().__init__(color_bgr, life_frames=55)

    def on_trigger(self):
        cx, cy = self.anchor
        self._p1 = (cx - random.uniform(80, 160), cy - 140)
        self._p2 = (cx - random.uniform(220, 320), cy - 40)

    def render(self, frame):
        overlay = np.zeros_like(frame, dtype=np.uint8)
        cx, cy = self.anchor
        n = config.WATER_DRAGON_SEGMENTS
        reach = min(1.0, self.age / 22)

        for i in range(n):
            t = (i / n) * reach
            if t <= 0:
                continue
            x, y = _bezier((cx, cy), self._p1, self._p2, t)
            radius = max(2, int(16 * (1 - t) + 3))
            jitter_x = x + random.uniform(-5, 5)
            jitter_y = y + random.uniform(-5, 5)

            # deep blue core -> pale cyan at the tip
            b = 255
            g = int(120 + 100 * t)
            r = int(40 + 60 * t)
            cv2.circle(overlay, (int(jitter_x), int(jitter_y)), radius, (b, g, r), -1)

        overlay = cv2.GaussianBlur(overlay, (0, 0), sigmaX=5)
        frame = cv2.add(frame, overlay)
        return frame
