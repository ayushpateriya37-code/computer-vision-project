"""
fire_dragon.py
----------------
Procedural Fire Dragon Jutsu: a stream of flame particles surging
outward from the hand along a curved (bezier-like) path, colored with a
red-orange-yellow gradient to suggest a fire dragon's body.
"""

import random
import math
import cv2
import numpy as np

from src import config
from src.effects.base_effect import BaseEffect


def _bezier(p0, p1, p2, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return x, y


class FireDragonEffect(BaseEffect):
    def __init__(self, color_bgr):
        super().__init__(color_bgr, life_frames=50)

    def on_trigger(self):
        cx, cy = self.anchor
        # curve sweeps up and away from the hand
        self._p1 = (cx + random.uniform(-60, 60), cy - 180)
        self._p2 = (cx + random.uniform(150, 260), cy - 260)

    def render(self, frame):
        overlay = np.zeros_like(frame, dtype=np.uint8)
        cx, cy = self.anchor
        n = config.FIRE_DRAGON_SEGMENTS
        reach = min(1.0, self.age / 20)  # dragon "grows" out over 20 frames

        for i in range(n):
            t = (i / n) * reach
            if t <= 0:
                continue
            x, y = _bezier((cx, cy), self._p1, self._p2, t)
            radius = max(2, int(18 * (1 - t) + 4))
            jitter_x = x + random.uniform(-4, 4)
            jitter_y = y + random.uniform(-4, 4)

            # color gradient: yellow core near hand -> deep red at the tip
            b = int(20 + 20 * t)
            g = int(160 * (1 - t) + 40 * t)
            r = 255
            cv2.circle(overlay, (int(jitter_x), int(jitter_y)), radius, (b, g, r), -1)

        overlay = cv2.GaussianBlur(overlay, (0, 0), sigmaX=6)
        frame = cv2.add(frame, overlay)
        return frame
