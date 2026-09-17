"""
test_vfx_engine.py
--------------------
Unit tests for MODULE 3 (vfx_engine.py + src/effects/*.py).

Verifies: every jutsu in config.JUTSU_REGISTRY has a working effect
class that can be triggered and rendered without crashing, that
VFXEngine's lifecycle (trigger -> update_and_render -> auto-prune on
expiry) behaves correctly, and that rendering never changes the
frame's shape/dtype (a common source of silent corruption bugs when
mixing overlay compositing with the base frame).
"""

import numpy as np
import pytest

from src import config
from src.vfx_engine import VFXEngine
from src.effects import EFFECT_CLASSES


def _blank_frame(w=640, h=480):
    return np.full((h, w, 3), (30, 30, 30), dtype=np.uint8)


@pytest.mark.parametrize("jutsu_key", list(config.JUTSU_REGISTRY.keys()))
def test_every_registered_jutsu_has_a_working_effect(jutsu_key):
    meta = config.JUTSU_REGISTRY[jutsu_key]
    assert meta["effect"] in EFFECT_CLASSES, (
        f"'{jutsu_key}' references effect key '{meta['effect']}' which is "
        f"missing from EFFECT_CLASSES"
    )


@pytest.mark.parametrize("jutsu_key", list(config.JUTSU_REGISTRY.keys()))
def test_vfx_engine_trigger_and_render_all_jutsu(jutsu_key):
    engine = VFXEngine()
    frame = _blank_frame()
    engine.trigger(jutsu_key, anchor_xy=(320, 240), frame=frame)
    assert engine.active_count == 1

    out = engine.update_and_render(frame.copy())
    assert out.shape == frame.shape
    assert out.dtype == frame.dtype


def test_vfx_engine_prunes_expired_effects():
    engine = VFXEngine()
    frame = _blank_frame()
    engine.trigger("chidori", anchor_xy=(320, 240), frame=frame)
    assert engine.active_count == 1

    life = EFFECT_CLASSES["chidori"](config.JUTSU_REGISTRY["chidori"]["color_bgr"]).life_frames
    for _ in range(life + 2):
        frame = engine.update_and_render(frame)

    assert engine.active_count == 0


def test_vfx_engine_supports_multiple_concurrent_effects():
    engine = VFXEngine()
    frame = _blank_frame()
    engine.trigger("rasengan", anchor_xy=(200, 200), frame=frame)
    engine.trigger("chidori", anchor_xy=(400, 300), frame=frame)
    assert engine.active_count == 2
    out = engine.update_and_render(frame)
    assert out.shape == frame.shape


def test_unknown_jutsu_key_is_ignored_gracefully():
    engine = VFXEngine()
    engine.trigger("not_a_real_jutsu", anchor_xy=(100, 100))
    assert engine.active_count == 0
