"""
config.py
---------
Central configuration for JutsuCam.

Keeping all tunables in one place makes the system easy to calibrate
(e.g. when adjusting gesture thresholds for a new camera / new hand-sign
reference images) without touching logic code elsewhere.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

ATTENDANCE_LOG_CSV = os.path.join(LOG_DIR, "jutsu_session_log.csv")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Camera / capture settings
# ---------------------------------------------------------------------------
FRAME_WIDTH = 960
FRAME_HEIGHT = 540
FLIP_HORIZONTAL = True          # mirror view feels natural for a webcam
TARGET_FPS = 30

# ---------------------------------------------------------------------------
# MediaPipe Hands settings
# ---------------------------------------------------------------------------
MAX_NUM_HANDS = 2
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.5

# ---------------------------------------------------------------------------
# Gesture recognition settings
# ---------------------------------------------------------------------------
# A gesture must be held (matched on consecutive frames) for this many
# frames before a jutsu is confirmed as "triggered". This suppresses
# flicker/false positives from a single noisy frame.
GESTURE_HOLD_FRAMES = 6

# Cooldown (in frames) after a jutsu fires before the same jutsu can
# trigger again, to avoid spamming the effect every frame while the
# pose is held.
GESTURE_COOLDOWN_FRAMES = 45

# Finger "curl" classification threshold: the mcp-pip-tip angle (degrees)
# above which a finger counts as "extended" (straight) rather than
# "curled". A fully straight finger measures ~175-180 deg; a tightly
# curled finger measures roughly 0-30 deg; a partially bent "claw"
# finger (as in the Rasengan pose) lands in the 90-150 deg middle
# ground. 150 deg cleanly separates "straight" from "any amount of
# bend", which is what every GESTURE_RULES predicate assumes.
FINGER_EXTENDED_ANGLE_DEG = 150

# ---------------------------------------------------------------------------
# VFX engine settings
# ---------------------------------------------------------------------------
VFX_MAX_PARTICLE_LIFE = 40          # frames
RASENGAN_MAX_RADIUS = 70
RASENGAN_GROW_FRAMES = 25
CHIDORI_BOLT_COUNT = 14
SHADOW_CLONE_COUNT = 2
SHADOW_CLONE_ALPHA = 0.45
FIRE_DRAGON_SEGMENTS = 18
WATER_DRAGON_SEGMENTS = 18
EARTH_PILLAR_GROW_FRAMES = 30

# ---------------------------------------------------------------------------
# Jutsu registry
# ---------------------------------------------------------------------------
# This is the single source of truth mapping a gesture name to display
# name / effect module / color theme. Once the reference hand-sign images
# are available, only GESTURE_RULES in gesture_classifier.py needs to be
# edited to match real seals -- this registry (names, colors, effect
# hookup) does not need to change.
JUTSU_REGISTRY = {
    "rasengan": {
        "display_name": "Rasengan",
        "effect": "rasengan",
        "color_bgr": (255, 180, 40),      # spinning blue-white orb
        "hold_seconds_hint": "cupped palm, fingers curled toward center",
    },
    "chidori": {
        "display_name": "Chidori",
        "effect": "chidori",
        "color_bgr": (255, 255, 255),     # white-blue lightning
        "hold_seconds_hint": "clawed/bent fingers, arm thrust forward",
    },
    "shadow_clone": {
        "display_name": "Shadow Clone Jutsu",
        "effect": "shadow_clone",
        "color_bgr": (200, 200, 200),
        "hold_seconds_hint": "index+middle crossed seal (Kage Bunshin sign)",
    },
    "fire_dragon": {
        "display_name": "Fire Dragon Jutsu",
        "effect": "fire_dragon",
        "color_bgr": (0, 90, 255),
        "hold_seconds_hint": "tiger seal, hand near mouth then thrust",
    },
    "water_dragon": {
        "display_name": "Water Dragon Jutsu",
        "effect": "water_dragon",
        "color_bgr": (255, 140, 0),
        "hold_seconds_hint": "ox seal, sweeping arm motion",
    },
    "earth_release": {
        "display_name": "Earth Release: Rising Rock Pillar",
        "effect": "earth_release",
        "color_bgr": (30, 120, 90),
        "hold_seconds_hint": "palm pressed flat, pushing down/forward",
    },
}
