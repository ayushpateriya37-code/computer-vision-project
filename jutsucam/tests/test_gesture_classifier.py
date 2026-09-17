"""
test_gesture_classifier.py
----------------------------
Unit tests for MODULE 2 (gesture_classifier.py).

We can't feed real camera frames into a headless CI/grading environment,
so these tests use synthetic hand landmarks (tests/manual_checks/synth_poses.py)
that reproduce the exact finger geometry of the 6 real reference hand-sign
photos used to design GESTURE_RULES. This validates the rule logic itself
in isolation from MediaPipe's detector.
"""

import pytest

from src.gesture_classifier import (
    extract_frame_features, classify_frame, GestureClassifier,
)
from tests.manual_checks.synth_poses import (
    hand_all_straight, hand_claw_spread, hand_tight_fist_down,
    hand_two_finger_seal, hand_index_only,
)


@pytest.mark.parametrize("expected,build_hands", [
    ("chidori", lambda: [hand_all_straight((400, 400), thumb_out=True)]),
    ("rasengan", lambda: [hand_claw_spread((400, 400))]),
    ("earth_release", lambda: [hand_tight_fist_down((400, 400))]),
    ("water_dragon", lambda: [hand_two_finger_seal((400, 400), thumb_extended=False, tilt=False)]),
    ("fire_dragon", lambda: [hand_two_finger_seal((400, 400), thumb_extended=True, tilt=True)]),
    ("shadow_clone", lambda: [hand_index_only((395, 400)), hand_index_only((410, 405))]),
])
def test_classify_frame_matches_expected_jutsu(expected, build_hands):
    features = extract_frame_features(build_hands())
    assert classify_frame(features) == expected


def test_no_hands_classifies_as_none():
    features = extract_frame_features([])
    assert classify_frame(features) is None


def test_two_hands_far_apart_is_not_shadow_clone():
    """Two index-only hands that are NOT crossed/close together should
    not trigger Shadow Clone -- distance matters, not just finger shape."""
    hands = [hand_index_only((50, 400)), hand_index_only((900, 400))]
    features = extract_frame_features(hands)
    assert classify_frame(features) != "shadow_clone"


def test_gesture_classifier_debounces_and_fires_once():
    """GestureClassifier should only fire after `hold_frames` consecutive
    identical detections, then require a cooldown before firing again."""
    clf = GestureClassifier(hold_frames=3, cooldown_frames=5)
    hands = [hand_all_straight((400, 400), thumb_out=True)]

    results = [clf.update(hands) for _ in range(3)]
    triggered_flags = [r[0] for r in results]
    # Should not fire before the hold window is reached
    assert triggered_flags[:2] == [None, None]
    assert triggered_flags[2] == "chidori"

    # Immediately after firing, cooldown blocks re-triggering even if
    # the pose is still held
    triggered_again, *_ = clf.update(hands)
    assert triggered_again is None


def test_gesture_classifier_progress_increases_towards_hold():
    clf = GestureClassifier(hold_frames=4, cooldown_frames=5)
    hands = [hand_claw_spread((400, 400))]
    progresses = []
    for _ in range(4):
        _, _, progress, _ = clf.update(hands)
        progresses.append(progress)
    assert progresses == sorted(progresses)
    assert progresses[-1] == 1.0
