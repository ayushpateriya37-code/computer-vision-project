"""
chidori.py
-----------
Procedural Chidori: crackling white-blue lightning bolts radiating from
the user's clawed hand, regenerated with random jagged polylines each
frame for a flickering "thousand birds" effect.
"""

import random
import cv2
import numpy as np

from src import config
from src.effects.base_effect import BaseEffect


def _jagged_bolt(start, angle_deg, length, segments=6, jitter=14):
    """Generate a jagged polyline approximating a lightning bolt."""
    import math
    pts = [start]
    x, y = start
    ang = math.radians(angle_deg)
    step = length / segments
    for _ in range(segments):
        x += step * math.cos(ang) + random.uniform(-jitter, jitter)
        y += step * math.sin(ang) + random.uniform(-jitter, jitter)
        pts.append((int(x), int(y)))
    return pts


class ChidoriEffect(BaseEffect):
    def __init__(self, color_bgr):
        super().__init__(color_bgr, life_frames=40)

    def render(self, frame):
        cx, cy = int(self.anchor[0]), int(self.anchor[1])
        overlay = np.zeros_like(frame, dtype=np.uint8)

        for _ in range(config.CHIDORI_BOLT_COUNT):
            angle = random.uniform(0, 360)
            length = random.uniform(20, 55)
            bolt = _jagged_bolt((cx, cy), angle, length)
            cv2.polylines(overlay, [np.array(bolt, dtype=np.int32)], False,
                          (255, 255, 255), 2, cv2.LINE_AA)

        overlay = cv2.GaussianBlur(overlay, (0, 0), sigmaX=2.5)
        frame = cv2.add(frame, overlay)

        # bright flickering core at the hand
        flicker = random.randint(180, 255)
        cv2.circle(frame, (cx, cy), 10, (flicker, flicker, 255), -1, cv2.LINE_AA)
        return frame
