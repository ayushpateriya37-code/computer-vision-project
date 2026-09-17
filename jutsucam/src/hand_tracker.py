"""
hand_tracker.py
----------------
MODULE 1: Hand Landmark Detection

Thin, well-documented wrapper around MediaPipe Hands -- a pretrained CNN
landmark model (no training performed by us). This module's only
responsibility is: given a BGR video frame, return a list of detected
hands, each as 21 (x, y, z) landmarks in pixel coordinates plus
handedness (Left/Right).

Keeping this isolated from gesture logic means the rest of the pipeline
never has to know anything about MediaPipe's API -- if we ever swapped
in a different landmark model, only this file would change.

Model file
----------
We deliberately use MediaPipe's classic ``solutions.hands`` API rather
than the newer "Tasks" API. The classic API ships its pretrained
weights bundled *inside* the ``mediapipe`` pip package itself, so
detection works fully offline immediately after ``pip install`` -- no
runtime model download, and nothing that can fail due to a blocked
URL or missing internet connection on the evaluator's machine.
"""

from dataclasses import dataclass
from typing import List

import cv2
import mediapipe as mp

from src.logger_setup import get_logger

logger = get_logger("hand_tracker")


@dataclass
class HandLandmarks:
    """A single detected hand's landmarks and metadata."""
    points: List[tuple]          # 21 (x_px, y_px, z_rel) tuples
    handedness: str              # "Left" or "Right"
    score: float                 # detection confidence


class HandTracker:
    # MediaPipe's 21 landmark indices, named for readability elsewhere
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    def __init__(self, max_num_hands=2, min_detection_confidence=0.6,
                 min_tracking_confidence=0.5):
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        logger.info(
            "HandTracker initialised (max_num_hands=%s, det_conf=%s, track_conf=%s)",
            max_num_hands, min_detection_confidence, min_tracking_confidence,
        )

    def process(self, frame_bgr) -> List[HandLandmarks]:
        """Run detection on a single BGR frame; returns list of hands found."""
        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        result = self._hands.process(frame_rgb)

        hands_out: List[HandLandmarks] = []
        if result.multi_hand_landmarks:
            for i, landmark_list in enumerate(result.multi_hand_landmarks):
                points = [(lm.x * w, lm.y * h, lm.z) for lm in landmark_list.landmark]
                label, score = "Right", 0.0
                if result.multi_handedness and i < len(result.multi_handedness):
                    top = result.multi_handedness[i].classification[0]
                    label, score = top.label, top.score
                hands_out.append(HandLandmarks(points=points, handedness=label, score=score))
        return hands_out

    def close(self):
        self._hands.close()
