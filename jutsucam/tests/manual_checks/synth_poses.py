"""
synth_poses.py
----------------
Builds synthetic HandLandmarks objects that geometrically approximate
each of the 6 reference hand-sign poses, WITHOUT needing a webcam or
real MediaPipe detection. Used to unit-test gesture_classifier.py and
to render preview frames of every VFX effect for visual QA.

Coordinate system: pixel space, origin top-left, y grows downward
(matches OpenCV/MediaPipe convention). A "straight finger" points from
MCP up through TIP with the tip having a smaller y (higher on screen).
A "curled finger" folds the tip back down near the MCP.
"""

from src.hand_tracker import HandLandmarks

# Landmark index layout (must match HandTracker / MediaPipe ordering):
# 0 wrist
# 1-4 thumb (cmc, mcp, ip, tip)
# 5-8 index (mcp, pip, dip, tip)
# 9-12 middle
# 13-16 ring
# 17-20 pinky


def _straight_finger(mcp, direction, length_pip=35, length_tip=35):
    """MCP -> PIP -> DIP -> TIP all extended in a straight line."""
    mx, my = mcp
    dx, dy = direction
    pip = (mx + dx * length_pip, my + dy * length_pip)
    dip = (pip[0] + dx * (length_tip * 0.5), pip[1] + dy * (length_tip * 0.5))
    tip = (pip[0] + dx * length_tip, pip[1] + dy * length_tip)
    return [pip, dip, tip]


def _curled_finger(mcp, fold_toward, length=18):
    """PIP bent sharply so the tip folds back near the MCP (fist-like)."""
    mx, my = mcp
    fx, fy = fold_toward
    pip = (mx + fx * length * 0.5, my + fy * length * 0.5)
    dip = (mx + fx * length * 0.7, my + fy * length * 0.7 - 6)
    tip = (mx + fx * length * 0.55, my + fy * length * 0.55 - 14)
    return [pip, dip, tip]


def _bent_claw_finger(mcp, direction, bend_deg_factor=0.5, length=32):
    """Partially bent finger (Rasengan claw): between straight and curled."""
    import math
    mx, my = mcp
    dx, dy = direction
    pip = (mx + dx * length * 0.5, my + dy * length * 0.5)
    # bend the second half of the finger inward toward the palm center
    ang = math.atan2(dy, dx) + bend_deg_factor
    dx2, dy2 = math.cos(ang), math.sin(ang)
    dip = (pip[0] + dx2 * length * 0.3, pip[1] + dy2 * length * 0.3)
    tip = (dip[0] + dx2 * length * 0.25, dip[1] + dy2 * length * 0.25)
    return [pip, dip, tip]


def _make_hand(wrist, mcps, fingers_xyz, handedness="Right"):
    """
    fingers_xyz: dict name -> [pip, dip, tip] (each an (x,y) tuple)
    mcps: dict name -> (x, y)
    Builds the full 21-point list in MediaPipe order.
    """
    pts = [None] * 21
    pts[0] = (*wrist, 0.0)
    # thumb: cmc, mcp, ip, tip  (we only vary mcp/ip/tip; cmc ~ near wrist)
    pts[1] = (wrist[0] + (mcps["thumb"][0] - wrist[0]) * 0.4,
              wrist[1] + (mcps["thumb"][1] - wrist[1]) * 0.4, 0.0)
    pts[2] = (*mcps["thumb"], 0.0)
    pts[3] = (*fingers_xyz["thumb"][0], 0.0)
    pts[4] = (*fingers_xyz["thumb"][2], 0.0)

    order = ["index", "middle", "ring", "pinky"]
    base = 5
    for i, name in enumerate(order):
        pts[base + i * 4 + 0] = (*mcps[name], 0.0)
        pts[base + i * 4 + 1] = (*fingers_xyz[name][0], 0.0)
        pts[base + i * 4 + 2] = (*fingers_xyz[name][1], 0.0)
        pts[base + i * 4 + 3] = (*fingers_xyz[name][2], 0.0)

    return HandLandmarks(points=pts, handedness=handedness, score=0.95)


# --- Pose builders -----------------------------------------------------

def hand_all_straight(wrist=(400, 400), thumb_out=True):
    """Chidori: all 5 fingers extended and together, palm facing camera."""
    mcps = {"thumb": (wrist[0] - 30, wrist[1] - 10), "index": (wrist[0] - 15, wrist[1] - 20),
            "middle": (wrist[0], wrist[1] - 22), "ring": (wrist[0] + 15, wrist[1] - 20),
            "pinky": (wrist[0] + 28, wrist[1] - 16)}
    fingers = {
        "thumb": _straight_finger(mcps["thumb"], (-0.9, -0.4)) if thumb_out else _curled_finger(mcps["thumb"], (0.3, -0.9)),
        "index": _straight_finger(mcps["index"], (-0.12, -1.0)),
        "middle": _straight_finger(mcps["middle"], (0.0, -1.0)),
        "ring": _straight_finger(mcps["ring"], (0.12, -1.0)),
        "pinky": _straight_finger(mcps["pinky"], (0.22, -1.0)),
    }
    return _make_hand(wrist, mcps, fingers)


def hand_claw_spread(wrist=(400, 400)):
    """Rasengan: fingers partially bent AND spread apart."""
    mcps = {"thumb": (wrist[0] - 30, wrist[1] - 10), "index": (wrist[0] - 20, wrist[1] - 20),
            "middle": (wrist[0] - 3, wrist[1] - 24), "ring": (wrist[0] + 16, wrist[1] - 20),
            "pinky": (wrist[0] + 32, wrist[1] - 14)}
    fingers = {
        "thumb": _bent_claw_finger(mcps["thumb"], (-0.9, -0.5), bend_deg_factor=0.9),
        "index": _bent_claw_finger(mcps["index"], (-0.35, -0.95), bend_deg_factor=0.9),
        "middle": _bent_claw_finger(mcps["middle"], (-0.08, -1.0), bend_deg_factor=0.9),
        "ring": _bent_claw_finger(mcps["ring"], (0.28, -0.95), bend_deg_factor=-0.9),
        "pinky": _bent_claw_finger(mcps["pinky"], (0.55, -0.85), bend_deg_factor=-0.9),
    }
    return _make_hand(wrist, mcps, fingers)


def hand_tight_fist_down(wrist=(400, 400)):
    """Earth Release: fingers curled tightly together, low spread."""
    mcps = {"thumb": (wrist[0] - 26, wrist[1] - 8), "index": (wrist[0] - 10, wrist[1] - 18),
            "middle": (wrist[0], wrist[1] - 20), "ring": (wrist[0] + 10, wrist[1] - 18),
            "pinky": (wrist[0] + 20, wrist[1] - 14)}
    fingers = {name: _curled_finger(mcps[name], (0.05 * i, 0.95)) for i, name in
               enumerate(["thumb", "index", "middle", "ring", "pinky"], start=-2)}
    return _make_hand(wrist, mcps, fingers)


def hand_two_finger_seal(wrist=(400, 400), thumb_extended=False, tilt=False):
    """Water/Fire Dragon: index+middle extended together, ring+pinky curled."""
    if tilt:
        wrist = (wrist[0], wrist[1])
    mcps = {"thumb": (wrist[0] - 28, wrist[1] - 8), "index": (wrist[0] - 6, wrist[1] - 20),
            "middle": (wrist[0] + 6, wrist[1] - 20), "ring": (wrist[0] + 16, wrist[1] - 16),
            "pinky": (wrist[0] + 25, wrist[1] - 12)}
    index_dir = (-0.55, -0.83) if tilt else (-0.05, -1.0)
    middle_dir = (-0.50, -0.85) if tilt else (0.05, -1.0)
    fingers = {
        "thumb": (_straight_finger(mcps["thumb"], (-0.95, -0.3)) if thumb_extended
                  else _curled_finger(mcps["thumb"], (0.5, -0.6))),
        "index": _straight_finger(mcps["index"], index_dir),
        "middle": _straight_finger(mcps["middle"], middle_dir),
        "ring": _curled_finger(mcps["ring"], (0.2, 0.95)),
        "pinky": _curled_finger(mcps["pinky"], (0.3, 0.9)),
    }
    return _make_hand(wrist, mcps, fingers)


def hand_index_only(wrist):
    """Shadow Clone (one hand of the pair): only index finger extended."""
    mcps = {"thumb": (wrist[0] - 24, wrist[1] - 6), "index": (wrist[0] - 4, wrist[1] - 18),
            "middle": (wrist[0] + 6, wrist[1] - 18), "ring": (wrist[0] + 14, wrist[1] - 16),
            "pinky": (wrist[0] + 22, wrist[1] - 12)}
    fingers = {
        "thumb": _curled_finger(mcps["thumb"], (0.6, -0.5)),
        "index": _straight_finger(mcps["index"], (0.0, -1.0)),
        "middle": _curled_finger(mcps["middle"], (0.1, 0.95)),
        "ring": _curled_finger(mcps["ring"], (0.2, 0.9)),
        "pinky": _curled_finger(mcps["pinky"], (0.3, 0.85)),
    }
    return _make_hand(wrist, mcps, fingers)
