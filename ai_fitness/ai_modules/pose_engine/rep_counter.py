"""
rep_counter.py  —  v3  (crash-proof edition)
---------------------------------------------
Responsibility: count bicep curl repetitions accurately and safely.

Crash sources fixed in this version
-------------------------------------
BUG-5  _elbow_angle() called calculate_angle() and assumed it would
       return a float. In v3, calculate_angle() returns None for bad
       inputs. The old code passed that None straight into
       AngleSmoother.update(), which called sorted([..., None]) and
       raised a TypeError: '<' not supported between instances of
       'NoneType' and 'float'.

BUG-6  ArmCounter.update() compared angle (float) with threshold
       constants using >=/<= operators.  If angle was somehow NaN
       (from an older version of calculate_angle), both comparisons
       return False in Python/NumPy without raising — but the state
       machine got permanently stuck in UNKNOWN, which looked like a
       freeze rather than a crash.  Now explicitly blocked.

BUG-7  BicepCurlCounter.update() had no try/except.  Any exception
       inside _elbow_angle() or the ArmCounter would propagate to
       main(), which had no handler either, crashing the entire loop.

BUG-8  AngleSmoother.update() with a single item in the deque called
       sorted(deque)[len//2] = sorted(deque)[0] — fine — but if the
       deque somehow contained a None from old code, sorted() raised
       TypeError. Explicit None filter added.
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from detector import PoseLandmarks, LM, calculate_angle

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tunable constants
# ---------------------------------------------------------------------------

ANGLE_DOWN_ENTER    = 155   # arm must exceed this to be "extended" (DOWN)
ANGLE_DOWN_EXIT     = 145   # must drop below this to leave DOWN
ANGLE_UP_ENTER      =  45   # arm must drop below this to be "curled" (UP)
ANGLE_UP_EXIT       =  55   # must exceed this to leave UP

FRAME_CONFIRM_COUNT =   3   # consecutive frames required to confirm a state change
EMA_ALPHA           = 0.4   # smoother responsiveness (0=frozen, 1=raw)
MEDIAN_WINDOW       =   5   # rolling window for median pre-filter
MIN_VISIBILITY      = 0.6   # landmark confidence threshold
MAX_LOST_FRAMES     =  10   # grace period before resetting candidates on loss


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class CurlState(Enum):
    DOWN    = auto()
    UP      = auto()
    UNKNOWN = auto()


# ---------------------------------------------------------------------------
# Angle smoother  (median + EMA, NaN-safe)
# ---------------------------------------------------------------------------

class AngleSmoother:
    """
    Two-stage filter: rolling median (kills spikes) → EMA (smooths jitter).

    FIX for BUG-5 and BUG-8: update() accepts only finite floats.
    None or NaN inputs are silently ignored (the window is not updated),
    and the last valid EMA value is returned instead.
    """

    def __init__(self, alpha: float = EMA_ALPHA, window: int = MEDIAN_WINDOW):
        self._alpha  = alpha
        self._window: deque[float] = deque(maxlen=window)
        self._ema: Optional[float] = None

    def update(self, raw: Optional[float]) -> Optional[float]:
        """
        Feed one angle reading.
        Returns the smoothed angle, or None if no valid data yet.

        FIX: returns None instead of crashing when raw is None/NaN.
        """
        # Reject None and non-finite values
        if raw is None or not math.isfinite(raw):
            return self._ema          # return last known good value (may be None)

        self._window.append(raw)

        # Only keep finite values in the sort (defensive — should always be true)
        valid = sorted(v for v in self._window if math.isfinite(v))
        if not valid:
            return self._ema

        median = valid[len(valid) // 2]

        if self._ema is None:
            self._ema = median
        else:
            self._ema = self._alpha * median + (1.0 - self._alpha) * self._ema

        return self._ema

    def reset(self):
        self._window.clear()
        self._ema = None


# ---------------------------------------------------------------------------
# Per-arm state machine
# ---------------------------------------------------------------------------

@dataclass
class ArmCounter:
    """
    State machine for one arm.

    FIX for BUG-6: update() explicitly rejects None/NaN angles and
    checks math.isfinite() before any threshold comparison.
    """
    reps:              int       = 0
    state:             CurlState = CurlState.UNKNOWN
    last_angle:        float     = 0.0

    _candidate:        CurlState = field(default=CurlState.UNKNOWN, repr=False)
    _candidate_frames: int       = field(default=0,                 repr=False)

    def update(self, angle: Optional[float]) -> bool:
        """
        Feed one smoothed angle. Returns True when a rep completes.
        Returns False (never raises) for None or non-finite inputs.
        """
        # BUG-6 fix: block bad values before any comparison
        if angle is None or not math.isfinite(angle):
            return False

        self.last_angle = angle
        suggested = self._suggest_state(angle)

        if suggested == CurlState.UNKNOWN or suggested == self.state:
            self._candidate        = CurlState.UNKNOWN
            self._candidate_frames = 0
            return False

        if suggested == self._candidate:
            self._candidate_frames += 1
        else:
            self._candidate        = suggested
            self._candidate_frames = 1

        if self._candidate_frames < FRAME_CONFIRM_COUNT:
            return False

        # Commit transition
        prev_state             = self.state
        self.state             = self._candidate
        self._candidate        = CurlState.UNKNOWN
        self._candidate_frames = 0

        rep_done = (prev_state == CurlState.UP and self.state == CurlState.DOWN)
        if rep_done:
            self.reps += 1

        return rep_done

    def _suggest_state(self, angle: float) -> CurlState:
        """Hysteresis-based state suggestion. angle is guaranteed finite here."""
        if self.state == CurlState.DOWN:
            return CurlState.UP      if angle <= ANGLE_UP_ENTER    else CurlState.UNKNOWN
        elif self.state == CurlState.UP:
            return CurlState.DOWN    if angle >= ANGLE_DOWN_ENTER   else CurlState.UNKNOWN
        else:   # UNKNOWN
            if angle >= ANGLE_DOWN_ENTER:
                return CurlState.DOWN
            if angle <= ANGLE_UP_ENTER:
                return CurlState.UP
            return CurlState.UNKNOWN


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------

@dataclass
class RepResult:
    left_reps:   int
    right_reps:  int
    total_reps:  int
    left_angle:  float
    right_angle: float
    left_state:  CurlState
    right_state: CurlState
    new_rep:     bool


# ---------------------------------------------------------------------------
# Public counter  (BUG-7 fix: full try/except around update())
# ---------------------------------------------------------------------------

class BicepCurlCounter:
    """
    Stateful rep counter — one instance per workout session.

    Usage
    -----
        counter = BicepCurlCounter()
        while True:
            pose   = detector.detect(frame)      # may be None
            result = counter.update(pose)
            print(result.total_reps)
        counter.reset()
    """

    def __init__(self):
        self._left         = ArmCounter()
        self._right        = ArmCounter()
        self._left_smooth  = AngleSmoother()
        self._right_smooth = AngleSmoother()
        self._lost_frames  = 0
        self._last_result  = self._make_empty()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def total_reps(self) -> int:
        return self._left.reps + self._right.reps

    # ------------------------------------------------------------------
    # Core update — NEVER raises
    # ------------------------------------------------------------------

    def update(self, pose: Optional[PoseLandmarks]) -> RepResult:
        """
        Process one frame. Always returns a valid RepResult, even on error.

        FIX for BUG-7: the entire body is wrapped in try/except so that
        any unexpected exception inside _elbow_angle(), AngleSmoother, or
        ArmCounter is caught, logged, and the last good result is returned
        instead of crashing the webcam loop.
        """
        try:
            return self._update_inner(pose)
        except Exception as exc:
            log.error(
                "BicepCurlCounter.update() unexpected error: %s — "
                "returning last known result.", exc, exc_info=True,
            )
            return self._last_result

    def reset(self):
        """Zero rep counts and state for a new set."""
        self._left         = ArmCounter()
        self._right        = ArmCounter()
        self._left_smooth.reset()
        self._right_smooth.reset()
        self._lost_frames  = 0
        self._last_result  = self._make_empty()

    # ------------------------------------------------------------------
    # Internal — can raise (caught by update())
    # ------------------------------------------------------------------

    def _update_inner(self, pose: Optional[PoseLandmarks]) -> RepResult:
        # Handle tracking loss
        if pose is None:
            self._lost_frames += 1
                        # ----------- POSTURE FILTER (ADD THIS) -----------

            # Get shoulder & hip positions (RIGHT side for simplicity)
            shoulder = pose.get_point(LM.RIGHT_SHOULDER)
            hip = pose.get_point(LM.RIGHT_HIP)

            # If points are missing, skip frame safely
            if shoulder is None or hip is None:
                return self._last_result

            # Only allow counting if upright (shoulder above hip)
            if shoulder[1] >= hip[1]:
                return self._last_result
            if self._lost_frames > MAX_LOST_FRAMES:
                self._left._candidate_frames  = 0
                self._right._candidate_frames = 0
            return self._last_result

        self._lost_frames = 0
        new_rep = False

        # Left arm
        raw_left = self._elbow_angle(pose, "left")
        smooth_left = self._left_smooth.update(raw_left)
        if smooth_left is not None:
            if self._left.update(smooth_left):
                new_rep = True

        # Right arm
        raw_right = self._elbow_angle(pose, "right")
        smooth_right = self._right_smooth.update(raw_right)
        if smooth_right is not None:
            if self._right.update(smooth_right):
                new_rep = True

        result = RepResult(
            left_reps   = self._left.reps,
            right_reps  = self._right.reps,
            total_reps  = self.total_reps,
            left_angle  = self._left.last_angle,
            right_angle = self._right.last_angle,
            left_state  = self._left.state,
            right_state = self._right.state,
            new_rep     = new_rep,
        )
        self._last_result = result
        return result

    def _elbow_angle(self, pose: PoseLandmarks, side: str) -> Optional[float]:
        """
        Return smoothed elbow angle for one arm.

        Returns None (never raises) if:
        - any landmark visibility is below threshold
        - any landmark coordinate is NaN / missing
        - calculate_angle() returns None
        """
        if side == "left":
            s, e, w = LM.LEFT_SHOULDER,  LM.LEFT_ELBOW,  LM.LEFT_WRIST
        else:
            s, e, w = LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW, LM.RIGHT_WRIST

        # Visibility gate
        for idx in (s, e, w):
            if pose.visibility(idx) < MIN_VISIBILITY:
                return None

        # get_point() returns None for NaN / out-of-range (BUG-2 / BUG-3 fix)
        pt_s = pose.get_point(s)
        pt_e = pose.get_point(e)
        pt_w = pose.get_point(w)

        # calculate_angle() returns None for None inputs or degenerate vectors
        return calculate_angle(pt_s, pt_e, pt_w)

    @staticmethod
    def _make_empty() -> RepResult:
        return RepResult(
            left_reps=0, right_reps=0, total_reps=0,
            left_angle=0.0, right_angle=0.0,
            left_state=CurlState.UNKNOWN, right_state=CurlState.UNKNOWN,
            new_rep=False,
        )
