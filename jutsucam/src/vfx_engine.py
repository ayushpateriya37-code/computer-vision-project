"""
vfx_engine.py
--------------
MODULE 3: VFX Animation Engine

Owns the set of currently-active jutsu effects and is responsible for:
  1. Instantiating the right effect when gesture_classifier.py reports a
     newly triggered jutsu.
  2. Advancing every active effect by one frame (step()).
  3. Compositing all active effects onto the current video frame
     (render()), in a deterministic order.

This module has no idea HOW a rasengan or chidori actually looks -- that
lives entirely inside src/effects/*.py. It only manages lifecycle.
"""

from typing import Dict, List, Optional

from src import config
from src.effects import EFFECT_CLASSES
from src.effects.shadow_clone import ShadowCloneEffect


class VFXEngine:
    def __init__(self):
        self._active_effects: List = []

    def trigger(self, jutsu_name: str, anchor_xy, frame=None):
        """Instantiate and activate the effect for a newly confirmed jutsu."""
        meta = config.JUTSU_REGISTRY.get(jutsu_name)
        if meta is None:
            return
        effect_key = meta["effect"]
        effect_cls = EFFECT_CLASSES.get(effect_key)
        if effect_cls is None:
            return

        effect = effect_cls(meta["color_bgr"])

        # Shadow Clone needs a snapshot of the current frame to duplicate.
        if isinstance(effect, ShadowCloneEffect) and frame is not None:
            effect.trigger_with_frame(anchor_xy, frame)
        else:
            effect.trigger(anchor_xy)

        self._active_effects.append(effect)

    def update_and_render(self, frame):
        """Advance + draw every active effect; prune finished ones."""
        still_active = []
        for effect in self._active_effects:
            effect.step()
            if effect.active:
                frame = effect.render(frame)
                still_active.append(effect)
        self._active_effects = still_active
        return frame

    @property
    def active_count(self) -> int:
        return len(self._active_effects)
