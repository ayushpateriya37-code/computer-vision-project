# JutsuCam — Real-Time Hand-Gesture Triggered Anime VFX System

**Name:** AYUSH PATERIYA
**Registration No.:** 24BAI10067

A computer vision project that watches a live webcam feed (or a video
file), recognizes six hand seals in real time using a pretrained hand-
landmark model, and overlays a hand-built anime-style visual effect
("jutsu") on screen when a seal is held — inspired by the hand signs
and techniques from *Naruto*.

No effect artwork is copied from the show — every visual (the glowing
orb, lightning arcs, flame stream, water stream, ground pillar, and
duplicate silhouettes) is generated procedurally in code using OpenCV
drawing primitives and particle-style animation, not image assets.

---

## 1. What this project does

| # | Jutsu | Hand seal required | Effect |
|---|-------|--------------------|--------|
| 1 | **Rasengan** | One hand, fingers bent into a spread-apart claw, as if cupping a ball | Glowing blue-white spinning orb grows in the palm |
| 2 | **Chidori** | One hand, open flat palm facing the camera, all 5 fingers straight and together | Crackling white-blue lightning arcs around the hand |
| 3 | **Shadow Clone Jutsu** | Both hands, wrists crossed, only the index finger extended on each hand (classic Kage Bunshin cross seal) | Two translucent duplicate silhouettes appear beside you |
| 4 | **Water Dragon Jutsu** | One hand, index + middle fingers extended together, thumb tucked in, held upright | A flowing blue water-stream arc |
| 5 | **Fire Dragon Jutsu** | One hand, index + middle fingers extended together, thumb sticking OUT to the side, wrist tilted | A curling orange-red flame stream |
| 6 | **Earth Release** | One hand, fingers curled together tightly into a loose fist (low spread) | A rock pillar grows upward from the ground |

The system is fully driven from the command line (no GUI setup
required to run it) and works in two modes:

- **Live mode** — reads from your webcam and shows an interactive
  window with an FPS/recognition HUD.
- **Headless mode** — reads from a webcam or a video file and writes
  the annotated output to an `.mp4` file, for machines without a
  display (e.g. an evaluator's CI environment).

It also keeps a CSV log of every jutsu triggered during a session and
can generate a usage-analytics report (counts per jutsu, most-used
jutsu, a bar chart) from all logged sessions.

---

## 2. How it works (architecture)

The pipeline is split into four independent modules, each in its own
file, connected by `main.py`:

```
Webcam / video frame
        │
        ▼
┌───────────────────────┐
│ 1. hand_tracker.py     │  MediaPipe Hands (pretrained CNN) → 21 hand
│    (Hand Landmark      │  landmarks per detected hand, fully offline
│     Detection)         │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 2. gesture_classifier  │  Geometric rules over landmark angles/
│    .py (Gesture /      │  distances (finger curl, fingertip spread,
│    Seal Classification)│  thumb state, hand tilt, two-hand wrist
│                        │  distance) → symbolic jutsu name + a small
│                        │  temporal debouncer (hold-to-confirm, then
│                        │  cooldown) so effects don't spam every frame
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 3. vfx_engine.py +      │  A registry of procedural effect classes
│    src/effects/*.py     │  (one per jutsu). Each effect is a small
│    (VFX Animation       │  state machine: trigger → step (per-frame
│    Engine)              │  animation update) → render (alpha-blend
│                        │  onto the live frame) → auto-expire.
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 4. session_logger.py + │  Every triggered jutsu is appended to a
│    report_generator.py │  CSV log (timestamp, session id, jutsu).
│    (Logging &          │  `python main.py report` aggregates all
│    Analytics)          │  logged sessions into summary stats + a
│                        │  bar chart.
└───────────────────────┘
```

Supporting modules: `config.py` (all tunable constants and the
jutsu registry in one place), `logger_setup.py` (centralized file +
console logging), `utils.py` (FPS counter, HUD drawing).

---

## 3. Requirements

- **Python 3.9 – 3.12** (Python 3.13/3.14 are **not** supported —
  MediaPipe does not yet ship wheels for them. If `python --version`
  shows 3.13 or later, install Python 3.11 alongside it; see
  Troubleshooting below.)
- A webcam (for live mode) — or any `.mp4`/`.avi` video file containing
  hands (for headless/video mode).
- Windows, macOS, or Linux.
- ~1 GB free disk space for the Python virtual environment and
  dependencies (OpenCV + MediaPipe).

No GPU, no API keys, no internet connection needed at runtime — the
hand-landmark model ships bundled inside the `mediapipe` pip package.

---

## 4. Setup — step by step

### 4.1 Get the code
Clone or download this repository, then open the project **root
folder** (the one containing `main.py` and `requirements.txt`) in your
terminal / VS Code.

### 4.2 Create a virtual environment

Windows (PowerShell):
```powershell
py -3.11 -m venv venv
venv\Scripts\activate
```

macOS / Linux:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

### 4.3 Install dependencies
```bash
pip install -r requirements.txt
```
This installs OpenCV, a pinned version of MediaPipe (`0.10.14` —
pinned deliberately, see note in `requirements.txt`), NumPy,
Matplotlib, and pytest. Takes 1–3 minutes.

### 4.4 Verify the install
```bash
pytest tests/ -v
```
Expected result: **29 passed**. If everything passes, your environment
is correctly set up.

---

## 5. Running the project

### 5.1 Live webcam mode
```bash
python main.py run --source 0
```
A window opens showing your webcam feed with an FPS / recognition HUD
in the top-left corner. Hold one of the six hand seals (table above)
steady for a few frames — a progress bar fills up, then the effect
triggers. Press **`q`** to quit.

If your webcam isn't found, try `--source 1` (some laptops enumerate
external/built-in cameras differently).

### 5.2 Run on a video file (no webcam needed)
```bash
python main.py run --source path/to/video.mp4
```

### 5.3 Headless mode (no display — saves output to a file)
```bash
python main.py run --source 0 --headless --output data/logs/session_output.mp4
```
Useful for servers/CI, or for capturing a demo clip.

### 5.4 Limit the run length (useful for quick tests)
```bash
python main.py run --source path/to/video.mp4 --headless --max-frames 150
```

### 5.5 Generate the usage analytics report
```bash
python main.py report
```
Reads every session logged so far from `data/logs/jutsu_session_log.csv`
and prints a summary (total triggers, most-used jutsu, per-jutsu
breakdown), and writes a CSV + bar chart to `data/reports/`.

---

## 6. Project structure

```
jutsucam/
├── main.py                     # CLI entry point (run / report commands)
├── requirements.txt
├── README.md
├── src/
│   ├── config.py                # all tunables + jutsu registry
│   ├── hand_tracker.py          # Module 1: hand landmark detection
│   ├── gesture_classifier.py    # Module 2: gesture/seal classification
│   ├── vfx_engine.py            # Module 3: effect lifecycle manager
│   ├── effects/
│   │   ├── base_effect.py       # shared effect state-machine base class
│   │   ├── rasengan.py
│   │   ├── chidori.py
│   │   ├── shadow_clone.py
│   │   ├── fire_dragon.py
│   │   ├── water_dragon.py
│   │   └── earth_release.py
│   ├── session_logger.py        # Module 4a: CSV event logging
│   ├── report_generator.py      # Module 4b: analytics + chart generation
│   ├── logger_setup.py          # centralized logging config
│   └── utils.py                 # FPS counter, HUD drawing helpers
├── tests/
│   ├── test_gesture_classifier.py
│   ├── test_vfx_engine.py
│   ├── test_session_logger.py
│   └── manual_checks/synth_poses.py   # synthetic hand-landmark test fixtures
└── data/
    ├── logs/                    # session CSV logs + app log (generated)
    └── reports/                 # analytics CSV + chart (generated)
```

---

## 7. Troubleshooting

**`ERROR: No matching distribution found for mediapipe==0.10.14`**
Your Python version is too new (3.13+) or too old for this MediaPipe
release. Install Python 3.11, then recreate the venv with
`py -3.11 -m venv venv` (Windows) or `python3.11 -m venv venv`
(macOS/Linux) and reinstall.

**Webcam window doesn't open / `cv2.error` about display**
You're likely on a machine without a display (SSH/CI). Re-run with
`--headless --output <file>.mp4` instead.

**Gestures aren't triggering / trigger as the wrong jutsu**
Lighting and camera angle affect landmark accuracy. Make sure your
whole hand (wrist to fingertips) is clearly visible in frame, and hold
the seal steady for about half a second. If it's consistently
misclassifying, the angle/spread thresholds in
`src/config.py` (`FINGER_EXTENDED_ANGLE_DEG`, and the threshold
constants inside `src/gesture_classifier.py`) can be tuned for your
camera and hand size.

**`pip install` fails with a permissions error**
Make sure your virtual environment is activated (you should see
`(venv)` in the prompt) before running `pip install`.

---

## 8. Notes on design choices

- **MediaPipe is pinned to `0.10.14`** deliberately: this is the last
  release whose Python API ships the classic `mp.solutions.hands`
  module with its pretrained model bundled *inside* the pip package.
  Newer releases moved to a "Tasks" API that downloads its model file
  from Google Cloud Storage on first run — an extra runtime dependency
  and failure point that this project avoids so it works fully offline
  immediately after `pip install`.
- **Gesture classification is rule-based, not a trained classifier.**
  Each jutsu's hand seal is encoded as a small set of geometric
  predicates (finger-curl angles, fingertip spread, thumb state, hand
  tilt) calibrated directly against reference photos of each real hand
  seal. This keeps the system fully explainable, fast, and independent
  of any training dataset.
- **All VFX are procedurally generated**, not pre-made image/video
  assets — built frame-by-frame with OpenCV drawing primitives
  (circles, lines, alpha blending) inside each `src/effects/*.py`
  class.
