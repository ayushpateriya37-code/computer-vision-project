"""
fixtures.py
------------
Synthetic HandLandmarks builder used across the test suite so tests do
not depend on a live webcam, a real hand, or the MediaPipe model file
being downloaded. Unit tests should be fast, deterministic, and runnable
offline -- this module makes that possible.
"""

from src.hand_tracker import HandLandmarks, HandTracker

FINGER_JOINTS = {
    "thumb": (HandTracker.THUMB_MCP, HandTracker.THUMB_IP, HandTracker.THUMB_TIP),
    "index": (HandTracker.INDEX_MCP, HandTracker.INDEX_PIP, HandTracker.INDEX_TIP),
    "middle": (HandTracker.MIDDLE_MCP, HandTracker.MIDDLE_PIP, HandTracker.MIDDLE_TIP),
    "ring": (HandTracker.RING_MCP, HandTracker.RING_PIP, HandTracker.RING_TIP),
    "pinky": (HandTracker.PINKY_MCP, HandTracker.PINKY_PIP, HandTracker.PINKY_TIP),
}


def make_hand(extended: dict, handedness="Right", origin=(300, 300)) -> HandLandmarks:
    """
    Build a synthetic 21-point hand with controllable per-finger curl.

    extended: dict like {"thumb": False, "index": True, "middle": True,
                          "ring": False, "pinky": False}
              Any finger omitted defaults to False (curled).
    """
    ox, oy = origin
    points = [(0.0, 0.0, 0.0)] * 21
    points[HandTracker.WRIST] = (ox, oy, 0.0)

    finger_order = ["thumb", "index", "middle", "ring", "pinky"]
    for i, name in enumerate(finger_order):
        mcp_i, pip_i, tip_i = FINGER_JOINTS[name]
        base_x = ox - 60 + i * 30
        mcp = (base_x, oy - 40, 0.0)
        is_ext = extended.get(name, False)
        if is_ext:
            # Straight finger pointing up: mcp -> pip -> tip roughly colinear
            pip = (base_x, oy - 70, 0.0)
            tip = (base_x, oy - 100, 0.0)
        else:
            # Curled finger: tip folds back sharply toward the palm
            pip = (base_x, oy - 55, 0.0)
            tip = (base_x + 15, oy - 45, 0.0)
        points[mcp_i] = mcp
        points[pip_i] = pip
        points[tip_i] = tip

        # also set the "MCP-1" precursor joint used only for thumb CMC etc.
        if name == "thumb":
            points[HandTracker.THUMB_CMC] = (base_x - 5, oy - 20, 0.0)

    return HandLandmarks(points=points, handedness=handedness, score=0.95)


ALL_CURLED = {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}
ALL_EXTENDED = {"thumb": True, "index": True, "middle": True, "ring": True, "pinky": True}
