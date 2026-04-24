"""
detector.py  —  v3  (crash-proof edition)
------------------------------------------
Responsibility: run MediaPipe Pose on one BGR frame and return
clean, validated landmark data.

Crash sources fixed in this version
-------------------------------------
BUG-1  detect() had no try/except around cv2.cvtColor() or
       self._pose.process(). A corrupt frame (wrong shape, wrong
       dtype, or a camera glitch) raised an unhandled exception and
       killed the loop.

BUG-2  PoseLandmarks.get_point() and .visibility() did direct index
       access on self.landmarks[index] with NO bounds check. If
       MediaPipe ever returned fewer than 33 landmarks (rare but
       possible on first detection), this caused an IndexError.

BUG-3  calculate_angle() was called from rep_counter.py with raw
       get_point() tuples. If a landmark's x or y was NaN (MediaPipe
       occasionally emits NaN for off-screen joints), np.arccos(NaN)
       returned NaN, which propagated into the smoother and eventually
       crashed a comparison operator.

BUG-4  draw_colored_skeleton() did int(lm.x * w) with no guard.
       If lm.x was NaN the int() cast raised a ValueError.

All four are fixed below.
"""

import logging

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Landmark index constants
# ---------------------------------------------------------------------------

class LM:
    """MediaPipe Pose landmark indices used by this engine."""
    NOSE          = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER= 12
    LEFT_ELBOW    = 13
    RIGHT_ELBOW   = 14
    LEFT_WRIST    = 15
    RIGHT_WRIST   = 16
    LEFT_HIP      = 23
    RIGHT_HIP     = 24
    LEFT_ANKLE    = 27
    RIGHT_ANKLE   = 28

    # Total landmarks MediaPipe guarantees
    TOTAL = 33


RELEVANT_LANDMARKS  = {11, 12, 13, 14, 15, 16}
RELEVANT_CONNECTIONS = [
    (11, 13), (13, 15),   # left  arm
    (12, 14), (14, 16),   # right arm
    (11, 12),             # shoulder bar
]

MIN_VISIBILITY = 0.5


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------

@dataclass
class PoseLandmarks:
    """
    Safe wrapper around MediaPipe landmark data.

    All accessor methods do bounds checking and NaN guarding so callers
    never need to worry about raw MediaPipe data integrity.
    """
    landmarks:   list          # list of mediapipe NormalizedLandmark (33 items)
    image_shape: tuple         # (height, width)

    # ------------------------------------------------------------------
    # Safe accessors
    # ------------------------------------------------------------------

    def _safe_lm(self, index: int):
        """
        Return the landmark at index, or None if index is out of range.
        Protects against MediaPipe returning fewer than 33 landmarks.
        """
        if index < 0 or index >= len(self.landmarks):
            return None
        return self.landmarks[index]

    def get_point(self, index: int) -> Optional[tuple]:
        """
        Return (x, y) in normalised [0, 1] space.
        Returns None if the landmark doesn't exist or contains NaN.
        """
        lm = self._safe_lm(index)
        if lm is None:
            return None
        # Guard against NaN coordinates
        if not (np.isfinite(lm.x) and np.isfinite(lm.y)):
            return None
        return float(lm.x), float(lm.y)

    def get_pixel_point(self, index: int) -> Optional[tuple]:
        """
        Return (x, y) in pixel coordinates.
        Returns None if the landmark doesn't exist or contains NaN.
        """
        pt = self.get_point(index)
        if pt is None:
            return None
        h, w = self.image_shape
        return int(pt[0] * w), int(pt[1] * h)

    def visibility(self, index: int) -> float:
        """
        MediaPipe confidence that this landmark is visible (0-1).
        Returns 0.0 (treat as invisible) if landmark is missing or invalid.
        """
        lm = self._safe_lm(index)
        if lm is None:
            return 0.0
        v = lm.visibility
        # Visibility can theoretically be NaN on corrupted frames
        return float(v) if np.isfinite(v) else 0.0


# ---------------------------------------------------------------------------
# Utility: angle between three (x, y) points
# ---------------------------------------------------------------------------

def calculate_angle(
    a: Optional[tuple],
    b: Optional[tuple],
    c: Optional[tuple],
) -> Optional[float]:
    """
    Return the interior angle at vertex b formed by rays b→a and b→c.
    All coordinates must be in the same space (normalised or pixel).

    Returns
    -------
    float   degrees in [0, 180]  on success
    None    if any input is None, any coordinate is NaN/Inf, or the
            vectors are degenerate (zero length)

    IMPORTANT: callers must check for None before using the result.
    This is the primary fix for the NaN-propagation crash (BUG-3).
    """
    # Reject None inputs (missing landmarks)
    if a is None or b is None or c is None:
        return None

    try:
        av = np.array(a, dtype=float)
        bv = np.array(b, dtype=float)
        cv_ = np.array(c, dtype=float)

        # Reject if any coordinate is not a real finite number
        if not (np.all(np.isfinite(av)) and
                np.all(np.isfinite(bv)) and
                np.all(np.isfinite(cv_))):
            return None

        ba = av - bv
        bc = cv_ - bv

        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)

        # Degenerate vectors (landmarks on top of each other)
        if norm_ba < 1e-9 or norm_bc < 1e-9:
            return None

        cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = float(np.degrees(np.arccos(cos_angle)))

        # Final sanity check — arccos should never give NaN after clipping,
        # but guard anyway
        return angle if np.isfinite(angle) else None

    except Exception as exc:                          # pragma: no cover
        log.warning("calculate_angle() exception: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class PoseDetector:
    """
    Crash-proof wrapper around MediaPipe Pose.

    Parameters
    ----------
    min_detection_confidence : float
    min_tracking_confidence  : float
    model_complexity         : int  (0 = fast, 2 = accurate; 1 = balanced)
    draw_landmarks           : bool
        When True, detect() draws arm-only skeleton in neutral grey.
        In production (FastAPI), set False and call
        draw_colored_skeleton() manually with the form report.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence:  float = 0.7,
        model_complexity:         int   = 1,
        draw_landmarks:           bool  = True,
    ):
        self._mp_pose = mp.solutions.pose
        self._pose    = self._mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity,
        )
        self.draw_landmarks = draw_landmarks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray) -> Optional[PoseLandmarks]:
        """
        Run pose detection on a BGR frame.

        Returns PoseLandmarks on success, None on any failure (no person
        detected, corrupt frame, MediaPipe internal error, etc.).

        This method NEVER raises — all exceptions are caught and logged
        so the webcam loop always continues.

        FIX for BUG-1: wraps everything in try/except.
        """
        if frame is None or frame.size == 0:
            log.warning("detect(): received empty or None frame — skipping.")
            return None

        try:
            # MediaPipe requires RGB; OpenCV gives BGR
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            result = self._pose.process(rgb)
            rgb.flags.writeable = True

        except cv2.error as exc:
            log.warning("detect(): OpenCV error during conversion: %s", exc)
            return None
        except Exception as exc:
            log.warning("detect(): MediaPipe error: %s", exc)
            return None

        if not result or not result.pose_landmarks:
            return None

        # Validate landmark count before wrapping
        lm_list = result.pose_landmarks.landmark
        if len(lm_list) < LM.TOTAL:
            log.warning(
                "detect(): MediaPipe returned only %d landmarks (expected %d).",
                len(lm_list), LM.TOTAL,
            )
            # Still usable — PoseLandmarks.visibility() returns 0.0 for
            # out-of-range indices, so callers will skip those landmarks.

        pose = PoseLandmarks(
            landmarks   = lm_list,
            image_shape = frame.shape[:2],
        )

        if self.draw_landmarks:
            self._draw_arms_only(frame, pose)

        return pose

    def draw_colored_skeleton(
        self,
        frame:    np.ndarray,
        pose:     PoseLandmarks,
        feedback: list,
    ) -> None:
        """
        Draw arm skeleton with per-arm color encoding form quality.

        GREEN  = arm form is correct
        RED    = a form rule has flagged this arm
        AMBER  = torso/back or shoulder issue

        FIX for BUG-4: pixel coordinate computation is now wrapped in
        try/except and skips landmarks with NaN coordinates.
        """
        if frame is None or pose is None:
            return

        COLOR_GOOD = (  0, 210,  90)
        COLOR_BAD  = ( 40,  40, 220)
        COLOR_WARN = (  0, 165, 255)

        left_bad  = any("LEFT"    in msg for msg in feedback)
        right_bad = any("RIGHT"   in msg for msg in feedback)
        back_bad  = any("lean"    in msg.lower() or
                        "upright" in msg.lower() for msg in feedback)
        shrug_bad = any("shrug"   in msg.lower() or
                        "shoulder" in msg.lower() for msg in feedback)

        left_color  = COLOR_BAD  if left_bad  else COLOR_GOOD
        right_color = COLOR_BAD  if right_bad else COLOR_GOOD
        torso_color = COLOR_WARN if (back_bad or shrug_bad) else COLOR_GOOD

        def _safe_pixel(idx):
            """Return pixel (x, y) or None — never raises."""
            return pose.get_pixel_point(idx)   # already NaN-safe in v3

        def _line(a_idx, b_idx, color, thickness=3):
            if pose.visibility(a_idx) < MIN_VISIBILITY:
                return
            if pose.visibility(b_idx) < MIN_VISIBILITY:
                return
            p1 = _safe_pixel(a_idx)
            p2 = _safe_pixel(b_idx)
            if p1 is None or p2 is None:
                return
            try:
                cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)
            except Exception as exc:
                log.debug("_line() draw error: %s", exc)

        def _dot(idx, color, radius=7):
            if pose.visibility(idx) < MIN_VISIBILITY:
                return
            pt = _safe_pixel(idx)
            if pt is None:
                return
            try:
                cv2.circle(frame, pt, radius, color,           -1, cv2.LINE_AA)
                cv2.circle(frame, pt, radius, (255, 255, 255),  1, cv2.LINE_AA)
            except Exception as exc:
                log.debug("_dot() draw error: %s", exc)

        _line(11, 13, left_color)
        _line(13, 15, left_color)
        _line(12, 14, right_color)
        _line(14, 16, right_color)
        _line(11, 12, torso_color)

        for idx in [11, 12]:
            _dot(idx, torso_color)
        for idx in [13, 15]:
            _dot(idx, left_color)
        for idx in [14, 16]:
            _dot(idx, right_color)

    def close(self):
        """Release MediaPipe resources — call once when shutting down."""
        try:
            self._pose.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _draw_arms_only(self, frame: np.ndarray, pose: PoseLandmarks) -> None:
        """Neutral grey skeleton — used when draw_landmarks=True."""
        for start_idx, end_idx in RELEVANT_CONNECTIONS:
            if (pose.visibility(start_idx) < MIN_VISIBILITY or
                    pose.visibility(end_idx)   < MIN_VISIBILITY):
                continue
            p1 = pose.get_pixel_point(start_idx)
            p2 = pose.get_pixel_point(end_idx)
            if p1 is None or p2 is None:
                continue
            try:
                cv2.line(frame, p1, p2, (200, 200, 200), 2, cv2.LINE_AA)
            except Exception:
                continue

        for idx in RELEVANT_LANDMARKS:
            if pose.visibility(idx) < MIN_VISIBILITY:
                continue
            pt = pose.get_pixel_point(idx)
            if pt is None:
                continue
            try:
                cv2.circle(frame, pt, 6, (0, 255, 128), -1, cv2.LINE_AA)
                cv2.circle(frame, pt, 6, (255, 255, 255),  1, cv2.LINE_AA)
            except Exception:
                continue
