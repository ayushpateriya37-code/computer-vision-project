"""
base_effect.py
---------------
Shared lifecycle contract for every procedural VFX effect (rasengan,
chidori, shadow_clone, fire_dragon, water_dragon, earth_release).

Every effect is self-contained: it owns its own particle/geometry state,
advances one "tick" per video frame, and knows how to alpha-blend itself
onto the current frame. vfx_engine.py only needs to know these four
methods -- it never needs to know how a given jutsu is actually drawn.
"""

from abc import ABC, abstractmethod


class BaseEffect(ABC):
    def __init__(self, color_bgr, life_frames=60):
        self.color = color_bgr
        self.life_frames = life_frames
        self.age = 0
        self.anchor = (0, 0)
        self.active = False

    def trigger(self, anchor_xy):
        """Called once, the frame a jutsu is confirmed. Resets the effect."""
        self.anchor = anchor_xy
        self.age = 0
        self.active = True
        self.on_trigger()

    def on_trigger(self):
        """Optional hook for subclasses to (re)initialize particle state."""
        pass

    def update_anchor(self, anchor_xy):
        """Called every frame while active so the effect can follow the hand."""
        self.anchor = anchor_xy

    def step(self) -> bool:
        """Advance one frame. Returns True while still active."""
        if not self.active:
            return False
        self.age += 1
        if self.age >= self.life_frames:
            self.active = False
        return self.active

    @abstractmethod
    def render(self, frame):
        """Draw this effect's current state onto `frame` (BGR ndarray, in place
        or returning a new array) and return the frame."""
        raise NotImplementedError

    @property
    def progress(self) -> float:
        """0.0 (just triggered) to 1.0 (about to expire)."""
        return min(1.0, self.age / max(1, self.life_frames))
