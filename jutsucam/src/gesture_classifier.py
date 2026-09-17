"""
gesture_classifier.py
----------------------
MODULE 2: Gesture / Hand-Seal Classification

Takes the raw landmarks produced by hand_tracker.py and turns them into
a symbolic gesture label (e.g. "rasengan", "chidori", "shadow_clone").

Design notes
------------
Classification is rule-based (no training data needed), built from two
layers:

  1. Low-level geometric features per hand: which fingers are extended
     vs curled, how sharply each finger is bent, how spread the
     fingertips are, whether the thumb is tucked or splayed out, and
     the hand's overall orientation. For two-hand poses we also look
     at the spatial relationship between the two wrists.

  2. GESTURE_RULES: a declarative table mapping each jutsu to a
     predicate function over those features. This table is the ONLY
     place that encodes what each hand-seal looks like.

Reference poses (from the 6 supplied hand-sign photos)
--------------------------------------------------------
1. Shadow Clone  -- TWO hands, wrists crossed in front of the body;
   each hand shows ONLY the index finger extended straight up, the
   other three fingers curled into the palm (classic Kage Bunshin
   cross seal).
2. Chidori       -- ONE hand, open flat palm facing the camera, all
   five fingers (including thumb) extended and together.
3. Rasengan      -- ONE hand, claw-like: fingers partially bent
   (not straight, not a closed fist) and clearly SPREAD APART, as if
   cupping a ball. Thumb also relaxed/bent.
4. Water Dragon  -- ONE hand, index + middle fingers extended together
   (touching each other), ring + pinky curled into the palm, thumb
   tucked in close to the palm (NOT sticking out). A classic two-
   finger seal held with the palm roughly upright.
5. Fire Dragon   -- ONE hand, same index+middle-together seal as Water
   Dragon, but the THUMB IS EXTENDED OUT to the side and the hand/
   wrist is held at a clear diagonal tilt rather than upright. Thumb
   state is what separates it from Water Dragon.
6. Earth Release -- ONE hand, fingers curled TIGHTLY together (a loose
   fist, low spread) with the fingertips curled down/inward toward the
   palm -- distinct from Rasengan's spread-apart claw.

A small temporal state machine (GestureClassifier) then debounces the
per-frame predictions: a gesture must be seen for GESTURE_HOLD_FRAMES
consecutive frames before it "fires", and then cannot re-fire again
until GESTURE_COOLDOWN_FRAMES have passed, so the effect doesn't
re-trigger every single frame while a pose is held.
"""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src import config
from src.hand_tracker import HandLandmarks, HandTracker


FINGER_JOINTS = {
    "thumb": (HandTracker.THUMB_MCP, HandTracker.THUMB_IP, HandTracker.THUMB_TIP),
    "index": (HandTracker.INDEX_MCP, HandTracker.INDEX_PIP, HandTracker.INDEX_TIP),
    "middle": (HandTracker.MIDDLE_MCP, HandTracker.MIDDLE_PIP, HandTracker.MIDDLE_TIP),
    "ring": (HandTracker.RING_MCP, HandTracker.RING_PIP, HandTracker.RING_TIP),
    "pinky": (HandTracker.PINKY_MCP, HandTracker.PINKY_PIP, HandTracker.PINKY_TIP),
}

# Fingers used for "spread" / curl-averaging computations (excludes thumb,
# which has very different geometry).
NON_THUMB_FINGERS = ("index", "middle", "ring", "pinky")


def _angle_deg(a, b, c) -> float:
    """Angle ABC (at vertex b) in degrees, given three (x, y[, z]) points."""
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    cx, cy = c[0], c[1]
    v1 = (ax - bx, ay - by)
    v2 = (cx - bx, cy - by)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 * mag2 == 0:
        return 180.0
    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


@dataclass
class HandFeatures:
    handedness: str
    finger_extended: Dict[str, bool]        # e.g. {"thumb": False, "index": True, ...}
    finger_curl_angle: Dict[str, float]     # raw mcp-pip-tip angle per finger (deg)
    palm_center: tuple
    wrist: tuple
    palm_size: float                        # wrist -> middle_mcp distance (scale reference)
    extended_count: int
    fingertip_spread: float                 # avg adjacent-fingertip distance / palm_size
    thumb_extended: bool
    hand_tilt_deg: float                    # angle of wrist->middle_mcp vector from vertical-up


def extract_hand_features(hand: HandLandmarks) -> HandFeatures:
    """Compute finger-curl states and palm geometry for one hand."""
    pts = hand.points
    finger_extended = {}
    finger_curl_angle = {}
    for name, (mcp_i, pip_i, tip_i) in FINGER_JOINTS.items():
        angle = _angle_deg(pts[mcp_i], pts[pip_i], pts[tip_i])
        finger_curl_angle[name] = angle
        finger_extended[name] = angle > config.FINGER_EXTENDED_ANGLE_DEG

    palm_ids = [HandTracker.WRIST, HandTracker.INDEX_MCP, HandTracker.MIDDLE_MCP,
                HandTracker.RING_MCP, HandTracker.PINKY_MCP]
    px = sum(pts[i][0] for i in palm_ids) / len(palm_ids)
    py = sum(pts[i][1] for i in palm_ids) / len(palm_ids)

    wrist = pts[HandTracker.WRIST][:2]
    middle_mcp = pts[HandTracker.MIDDLE_MCP][:2]
    palm_size = max(1e-6, _dist(wrist, middle_mcp))

    # Fingertip spread: average distance between adjacent non-thumb
    # fingertips, normalised by palm size. Large -> fingers splayed
    # apart (Rasengan claw). Small -> fingers curled together (Earth
    # Release fist, or a two-finger seal where only 2 fingers matter).
    tip_ids = {
        "index": HandTracker.INDEX_TIP, "middle": HandTracker.MIDDLE_TIP,
        "ring": HandTracker.RING_TIP, "pinky": HandTracker.PINKY_TIP,
    }
    adjacent_pairs = [("index", "middle"), ("middle", "ring"), ("ring", "pinky")]
    spread_vals = [
        _dist(pts[tip_ids[a]], pts[tip_ids[b]]) / palm_size
        for a, b in adjacent_pairs
    ]
    fingertip_spread = sum(spread_vals) / len(spread_vals)

    # Hand tilt: angle between (wrist -> middle_mcp) and straight "up"
    # in image space (0, -1). 0 deg = hand pointing straight up,
    # larger = more diagonal/sideways tilt.
    vx, vy = middle_mcp[0] - wrist[0], middle_mcp[1] - wrist[1]
    up = (0.0, -1.0)
    mag = math.hypot(vx, vy) or 1e-6
    cos_t = max(-1.0, min(1.0, (vx * up[0] + vy * up[1]) / mag))
    hand_tilt_deg = math.degrees(math.acos(cos_t))

    return HandFeatures(
        handedness=hand.handedness,
        finger_extended=finger_extended,
        finger_curl_angle=finger_curl_angle,
        palm_center=(px, py),
        wrist=wrist,
        palm_size=palm_size,
        extended_count=sum(finger_extended.values()),
        fingertip_spread=fingertip_spread,
        thumb_extended=finger_extended["thumb"],
        hand_tilt_deg=hand_tilt_deg,
    )


@dataclass
class FrameFeatures:
    hands: List[HandFeatures] = field(default_factory=list)

    @property
    def num_hands(self):
        return len(self.hands)


def extract_frame_features(hands: List[HandLandmarks]) -> FrameFeatures:
    return FrameFeatures(hands=[extract_hand_features(h) for h in hands])


# ---------------------------------------------------------------------------
# GESTURE_RULES
# ---------------------------------------------------------------------------
# Each predicate receives a FrameFeatures and returns True/False. These
# are calibrated against the 6 reference hand-sign photos supplied for
# this project (see module docstring for the pose description each
# rule encodes).

def _two_finger_seal(hf: HandFeatures) -> bool:
    """Shared shape for Water Dragon / Fire Dragon: index+middle
    extended together, ring+pinky curled."""
    return (hf.finger_extended["index"] and hf.finger_extended["middle"]
            and not hf.finger_extended["ring"] and not hf.finger_extended["pinky"])


def _is_rasengan(f: FrameFeatures) -> bool:
    """One hand, claw shape: fingers partially bent (neither straight
    nor a tight fist) and clearly spread apart, as if cupping a ball."""
    if f.num_hands != 1:
        return False
    hf = f.hands[0]
    avg_curl = sum(hf.finger_curl_angle[n] for n in NON_THUMB_FINGERS) / len(NON_THUMB_FINGERS)
    return (60.0 <= avg_curl <= 165.0) and hf.fingertip_spread >= 0.6


def _is_chidori(f: FrameFeatures) -> bool:
    """One hand, open flat palm: all five fingers (incl. thumb)
    extended and roughly together."""
    if f.num_hands != 1:
        return False
    hf = f.hands[0]
    return hf.extended_count == 5


def _is_shadow_clone(f: FrameFeatures) -> bool:
    """Two hands, wrists crossed close together, each hand showing only
    the index finger extended (classic Kage Bunshin cross seal)."""
    if f.num_hands != 2:
        return False
    h1, h2 = f.hands
    one_finger_each = all(
        hf.finger_extended["index"]
        and not hf.finger_extended["middle"]
        and not hf.finger_extended["ring"]
        and not hf.finger_extended["pinky"]
        for hf in (h1, h2)
    )
    if not one_finger_each:
        return False
    avg_palm = (h1.palm_size + h2.palm_size) / 2
    wrists_close = _dist(h1.wrist, h2.wrist) <= 2.2 * avg_palm
    return wrists_close


def _is_water_dragon(f: FrameFeatures) -> bool:
    """One hand, two-finger seal with the thumb tucked in (not
    sticking out) -- held roughly upright."""
    if f.num_hands != 1:
        return False
    hf = f.hands[0]
    return _two_finger_seal(hf) and not hf.thumb_extended


def _is_fire_dragon(f: FrameFeatures) -> bool:
    """One hand, two-finger seal like Water Dragon, but the thumb is
    extended out to the side and the wrist is held at a diagonal tilt."""
    if f.num_hands != 1:
        return False
    hf = f.hands[0]
    return _two_finger_seal(hf) and hf.thumb_extended and hf.hand_tilt_deg >= 12.0


def _is_earth_release(f: FrameFeatures) -> bool:
    """One hand, fingers curled tightly together into a loose fist
    (low spread), fingertips curling down/inward toward the palm --
    distinct from Rasengan's spread-apart claw."""
    if f.num_hands != 1:
        return False
    hf = f.hands[0]
    avg_curl = sum(hf.finger_curl_angle[n] for n in NON_THUMB_FINGERS) / len(NON_THUMB_FINGERS)
    return avg_curl < 165.0 and hf.fingertip_spread < 0.6


GESTURE_RULES = {
    "shadow_clone": _is_shadow_clone,
    "water_dragon": _is_water_dragon,
    "fire_dragon": _is_fire_dragon,
    "chidori": _is_chidori,
    "rasengan": _is_rasengan,
    "earth_release": _is_earth_release,
}


def classify_frame(features: FrameFeatures) -> Optional[str]:
    """Returns the first matching jutsu name for this frame, or None.

    Rules are checked in a fixed order (most geometrically-specific
    first: two-hand pose, then two-finger seals, then the two
    single-hand curl shapes last since they are closest to each other
    and benefit from the two-finger seals being ruled out first) so
    that if two predicates could ever both match on a borderline
    frame, the result is deterministic rather than dict-order-dependent.
    """
    for name in GESTURE_RULES:
        rule = GESTURE_RULES[name]
        if rule(features):
            return name
    return None


class GestureClassifier:
    """
    Temporal debouncer / state machine on top of classify_frame().

    Call update(hands) once per frame. It returns a GestureEvent-like
    tuple (triggered_jutsu_or_None, current_candidate_or_None, progress)
    where:
      - triggered_jutsu: fires exactly once when a gesture has been held
        for GESTURE_HOLD_FRAMES frames (subject to cooldown).
      - current_candidate: the gesture currently being recognized this
        frame (even before it "fires"), useful for the VFX engine to
        show a build-up animation (e.g. Rasengan growing in the palm).
      - progress: 0.0-1.0 how far through the hold window we are, for
        smooth build-up animations.
    """

    def __init__(self, hold_frames=None, cooldown_frames=None):
        self.hold_frames = hold_frames or config.GESTURE_HOLD_FRAMES
        self.cooldown_frames = cooldown_frames or config.GESTURE_COOLDOWN_FRAMES
        self._history = deque(maxlen=self.hold_frames)
        self._cooldowns: Dict[str, int] = {name: 0 for name in config.JUTSU_REGISTRY}

    def update(self, hands: List[HandLandmarks]):
        features = extract_frame_features(hands)
        candidate = classify_frame(features)
        self._history.append(candidate)

        # tick down cooldowns
        for name in self._cooldowns:
            if self._cooldowns[name] > 0:
                self._cooldowns[name] -= 1

        progress = 0.0
        triggered = None

        if candidate is not None:
            same_streak = sum(1 for g in self._history if g == candidate)
            progress = min(1.0, same_streak / self.hold_frames)
            if same_streak >= self.hold_frames and self._cooldowns[candidate] == 0:
                triggered = candidate
                self._cooldowns[candidate] = self.cooldown_frames
                self._history.clear()

        return triggered, candidate, progress, features
