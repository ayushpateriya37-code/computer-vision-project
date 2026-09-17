"""
rasengan.py
------------
Procedural Rasengan: a spinning blue-white spiral orb that grows in the
user's cupped palm, built entirely from OpenCV primitives (concentric
rotating arcs + a soft additive glow). No external artwork/assets used.
"""

import math
import cv2
import numpy as np

from src import config
from src.effects.base_effect import BaseEffect


class RasenganEffect(BaseEffect):
    def __init__(self, color_bgr):
        super().__init__(color_bgr, life_frames=config.RASENGAN_GROW_FRAMES + 25)

    def on_trigger(self):
        self._rotation = 0.0

    def _current_radius(self) -> float:
        grow = min(1.0, self.age / config.RASENGAN_GROW_FRAMES)
        # ease-out grow, then a gentle pulsing hold
        base = config.RASENGAN_MAX_RADIUS * grow
        if grow >= 1.0:
            base += 4 * math.sin(self.age * 0.4)
        return base

    def render(self, frame):
        radius = self._current_radius()
        if radius < 2:
            return frame

        cx, cy = int(self.anchor[0]), int(self.anchor[1])
        overlay = np.zeros_like(frame, dtype=np.uint8)

        # Core glow (soft filled circle, blurred later for a glow look)
        cv2.circle(overlay, (cx, cy), int(radius), self.color, -1, lineType=cv2.LINE_AA)

        # Spinning outer spiral arcs to suggest swirling chakra
        self._rotation += 18  # degrees per frame
        num_arcs = 4
        for i in range(num_arcs):
            angle_offset = self._rotation + i * (360 / num_arcs)
            for t in np.linspace(0, 1, 12):
                ang = math.radians(angle_offset + t * 260)
                r = radius * (0.35 + 0.65 * t)
                x = int(cx + r * math.cos(ang))
                y = int(cy + r * math.sin(ang))
                cv2.circle(overlay, (x, y), max(1, int(radius * 0.06)), (255, 255, 255), -1)

        # Blur for glow, then additively blend onto the frame
        overlay = cv2.GaussianBlur(overlay, (0, 0), sigmaX=radius * 0.15 + 3)
        frame = cv2.add(frame, overlay)

        # Crisp bright core on top
        cv2.circle(frame, (cx, cy), max(2, int(radius * 0.25)), (255, 255, 255), -1, cv2.LINE_AA)
        return frame
