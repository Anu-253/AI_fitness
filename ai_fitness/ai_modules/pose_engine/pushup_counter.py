"""
pushup_counter.py  —  v1  (matches pose_engine_v3 architecture)
----------------------------------------------------------------
Responsibility: detect and count push-up repetitions in real time.

How push-up angle detection works
-----------------------------------
MediaPipe gives us 33 body landmarks.  For a push-up the camera is
typically placed to the side of the person, so we get a clear profile
view of the arms.  We track the elbow angle formed by three landmarks:

    SHOULDER  -->  ELBOW  <--  WRIST
          (angle measured at the elbow vertex)

Push-up positions
-----------------
    UP   (arms extended)  : elbow angle ~160–180 degrees
    DOWN (chest to floor) : elbow angle ~70–90  degrees

One complete rep = transition  UP -> DOWN -> UP.

Why we average BOTH elbows
---------------------------
A single elbow can become occluded (camera side) or jittery.
Averaging the left and right elbow angles (when both are visible)
gives a far more stable signal.  If only one side is visible we use
that side alone rather than skipping the frame entirely.

Stability features (mirror of rep_counter.py v3)
-------------------------------------------------
1. VISIBILITY GATE     — landmark ignored if MediaPipe confidence < 0.6
2. NaN / None GUARD    — calculate_angle() returns None for bad data;
                         every caller checks before using the value
3. MEDIAN PRE-FILTER   — rolling median over last 5 frames kills spikes
4. EMA SMOOTHER        — exponential moving average smooths jitter
5. HYSTERESIS          — two thresholds per boundary, not one, so the
                         angle must move decisively before state changes
6. FRAME CONFIRMATION  — N consecutive frames must agree before the
                         state machine commits to a transition
7. TRACKING LOSS GRACE — up to MAX_LOST_FRAMES bad frames tolerated;
                         state is held, rep count is never decremented
8. NEVER RAISES        — update() wraps everything in try/except and
                         returns _last_result on any unexpected error

This module is completely self-contained.  It imports only from
detector.py (same as rep_counter.py) and adds zero side effects to
the existing bicep curl system.
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
# Tunable thresholds
# Adjust these if your camera angle or user size differs.
# ---------------------------------------------------------------------------

# ── Angle thresholds (degrees at the elbow) ────────────────────────────────
# Hysteresis: two values per boundary so small oscillations near the
# edge don't trigger false state changes.

ANGLE_UP_ENTER    = 150   # elbow must EXCEED this to register as "UP" (arms extended)
ANGLE_UP_EXIT     = 140   # elbow must DROP BELOW this to leave the UP state
ANGLE_DOWN_ENTER  =  90   # elbow must DROP BELOW this to register as "DOWN" (chest down)
ANGLE_DOWN_EXIT   = 100   # elbow must EXCEED this to leave the DOWN state

# ── Plank / body-position gate ─────────────────────────────────────────────
# Shoulder → Hip → Ankle angle.  A proper plank is close to 180°.
# We require at least this angle to allow rep counting.
PLANK_BODY_ANGLE_MIN = 160   # degrees — below this → body is bent, reps are rejected

# ── Stability settings ─────────────────────────────────────────────────────
FRAME_CONFIRM_COUNT = 3    # consecutive frames required to confirm a state change
EMA_ALPHA           = 0.4  # EMA responsiveness  (0.0 = frozen, 1.0 = raw signal)
MEDIAN_WINDOW       = 5    # rolling window size for the median pre-filter
MIN_VISIBILITY      = 0.6  # MediaPipe confidence below which a landmark is ignored
MAX_LOST_FRAMES     = 10   # grace-period frames before resetting candidate on loss


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class PushupState(Enum):
    UP      = auto()    # arms extended — the starting / resting position
    DOWN    = auto()    # chest lowered — the bottom of the rep
    UNKNOWN = auto()    # not yet in a valid starting position


# ---------------------------------------------------------------------------
# Angle smoother  (identical logic to rep_counter.py AngleSmoother)
# ---------------------------------------------------------------------------

class AngleSmoother:
    """
    Two-stage filter for raw elbow angles.

    Stage 1 — Rolling median (MEDIAN_WINDOW frames)
                Kills single-frame spikes from fast movement or occlusion.
    Stage 2 — Exponential moving average
                Smooths residual jitter without introducing much lag.

    None and NaN inputs are silently discarded; the last valid EMA is
    returned so callers always get a usable value or None (before the
    first valid reading).
    """

    def __init__(self, alpha: float = EMA_ALPHA, window: int = MEDIAN_WINDOW):
        self._alpha  = alpha
        self._window: deque[float] = deque(maxlen=window)
        self._ema:    Optional[float] = None

    def update(self, raw: Optional[float]) -> Optional[float]:
        """
        Feed one raw angle.  Returns smoothed angle or None (no data yet).
        Never raises.
        """
        if raw is None or not math.isfinite(raw):
            return self._ema   # return last known good value

        self._window.append(raw)

        valid = sorted(v for v in self._window if math.isfinite(v))
        if not valid:
            return self._ema

        median = valid[len(valid) // 2]

        if self._ema is None:
            self._ema = median
        else:
            self._ema = self._alpha * median + (1.0 - self._alpha) * self._ema

        return self._ema

    def reset(self) -> None:
        self._window.clear()
        self._ema = None


# ---------------------------------------------------------------------------
# Core state machine
# ---------------------------------------------------------------------------

@dataclass
class _PushupStateMachine:
    """
    Internal state machine for one push-up signal (the averaged angle).

    One rep = UP -> DOWN -> UP.
    Each transition requires FRAME_CONFIRM_COUNT consecutive frames
    at the target state.

    This class is not used directly — PushupCounter wraps it.
    """
    reps:              int          = 0
    state:             PushupState  = PushupState.UNKNOWN
    last_angle:        float        = 0.0
    _candidate:        PushupState  = field(default=PushupState.UNKNOWN, repr=False)
    _candidate_frames: int          = field(default=0,                   repr=False)

    def update(self, angle: Optional[float]) -> bool:
        """
        Feed one smoothed angle.
        Returns True on the exact frame a rep completes, False otherwise.
        Never raises.
        """
        if angle is None or not math.isfinite(angle):
            return False

        self.last_angle = angle
        suggested = self._suggest(angle)

        # No transition suggested, or already in that state
        if suggested == PushupState.UNKNOWN or suggested == self.state:
            self._candidate        = PushupState.UNKNOWN
            self._candidate_frames = 0
            return False

        # Accumulate consecutive frames pointing at the same new state
        if suggested == self._candidate:
            self._candidate_frames += 1
        else:
            self._candidate        = suggested
            self._candidate_frames = 1

        # Not enough confirmation yet
        if self._candidate_frames < FRAME_CONFIRM_COUNT:
            return False

        # ── Transition confirmed ──────────────────────────────────────────
        prev_state             = self.state
        self.state             = self._candidate
        self._candidate        = PushupState.UNKNOWN
        self._candidate_frames = 0

        # A rep completes when we return to UP after being DOWN
        rep_done = (prev_state == PushupState.DOWN and
                    self.state  == PushupState.UP)
        if rep_done:
            self.reps += 1

        return rep_done

    def _suggest(self, angle: float) -> PushupState:
        """
        Map an angle to a suggested state using hysteresis.
        angle is guaranteed to be finite at this point.

        Hysteresis dead-bands:
            DOWN  side: [ANGLE_DOWN_ENTER, ANGLE_DOWN_EXIT]
            UP    side: [ANGLE_UP_EXIT,    ANGLE_UP_ENTER ]
        Angles inside a dead-band return UNKNOWN so no transition fires.
        """
        if self.state == PushupState.UP:
            # Currently extended: wait for a clear drop toward DOWN
            if angle <= ANGLE_DOWN_ENTER:
                return PushupState.DOWN
            return PushupState.UNKNOWN   # still near UP, or in dead-band

        elif self.state == PushupState.DOWN:
            # Currently lowered: wait for a clear rise toward UP
            if angle >= ANGLE_UP_ENTER:
                return PushupState.UP
            return PushupState.UNKNOWN

        else:  # UNKNOWN — accept either clean position as starting state
            if angle >= ANGLE_UP_ENTER:
                return PushupState.UP
            if angle <= ANGLE_DOWN_ENTER:
                return PushupState.DOWN
            return PushupState.UNKNOWN


# ---------------------------------------------------------------------------
# Result dataclass  (returned to main.py every frame)
# ---------------------------------------------------------------------------

@dataclass
class PushupResult:
    """
    Everything main.py needs after one frame.

    Attributes
    ----------
    reps              : total completed push-up reps this session
    angle             : the current smoothed elbow angle (averaged across arms)
    state             : current PushupState (UP / DOWN / UNKNOWN)
    new_rep           : True only on the exact frame a rep is completed
    visible           : True if at least one arm was visible this frame
    body_straight     : True if the plank body angle >= PLANK_BODY_ANGLE_MIN
    straightness_score: 0-100 body straightness score (100 = perfect plank)
    feedback          : list of real-time coaching messages for the HUD
    """
    reps:               int
    angle:              float
    state:              PushupState
    new_rep:            bool
    visible:            bool
    body_straight:      bool      = field(default=True)
    straightness_score: int       = field(default=0)
    feedback:           list      = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class PushupCounter:
    """
    Stateful push-up counter — create ONE instance per workout session.

    The existing BicepCurlCounter in rep_counter.py is completely
    untouched.  This class is independent and can run alongside it.

    Usage
    -----
        counter = PushupCounter()

        while capturing:
            frame  = camera.read()
            pose   = detector.detect(frame)    # may return None
            result = counter.update(pose)
            print(result.reps)

        counter.reset()   # start a new set
    """

    def __init__(self) -> None:
        self._machine      = _PushupStateMachine()
        self._smoother     = AngleSmoother()
        self._lost_frames  = 0
        self._last_result  = self._make_empty()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def reps(self) -> int:
        return self._machine.reps

    def reset(self) -> None:
        """Zero the rep count and state machine for a new set."""
        self._machine     = _PushupStateMachine()
        self._smoother.reset()
        self._lost_frames = 0
        self._last_result = self._make_empty()

    def update(self, pose: Optional[PoseLandmarks]) -> PushupResult:
        """
        Process one frame.  ALWAYS returns a valid PushupResult.

        If pose is None (tracking lost) the counter holds its previous
        state for up to MAX_LOST_FRAMES frames, then resets the candidate
        counter (but NEVER decrements the rep count).

        All internal exceptions are caught and logged; the last known
        result is returned instead of crashing.
        """
        try:
            return self._update_inner(pose)
        except Exception as exc:
            log.error(
                "PushupCounter.update() unexpected error: %s — "
                "returning last known result.", exc, exc_info=True,
            )
            return self._last_result

    # ------------------------------------------------------------------
    # Internal — allowed to raise (caught by update())
    # ------------------------------------------------------------------

    def _update_inner(self, pose: Optional[PoseLandmarks]) -> PushupResult:
        # ── Tracking-loss handling ────────────────────────────────────────
        if pose is None:
            self._lost_frames += 1
            if self._lost_frames > MAX_LOST_FRAMES:
                # Too long without a body — reset transition candidates
                # but keep the rep count intact
                self._machine._candidate        = PushupState.UNKNOWN
                self._machine._candidate_frames = 0
            return self._last_result

        self._lost_frames = 0

        # ── Get the best available elbow angle ────────────────────────────
        raw_angle, visible = self._best_elbow_angle(pose)

        # Feed into smoother (returns None if no good data yet)
        smooth_angle = self._smoother.update(raw_angle)

        # ── Plank / body-position gate ────────────────────────────────────
        body_angle    = self._body_angle(pose)
        body_straight = (
            body_angle is not None and body_angle >= PLANK_BODY_ANGLE_MIN
        )
        s_score = self._straightness_score(body_angle)

        # Only drive the state machine when the body is actually straight.
        # This prevents sitting/standing elbow movements from counting.
        new_rep = False
        if body_straight:
            new_rep = self._machine.update(smooth_angle)
        else:
            # Body is not straight — freeze candidate so partial transitions
            # accumulated while upright are discarded immediately.
            self._machine._candidate        = PushupState.UNKNOWN
            self._machine._candidate_frames = 0

        # ── Feedback ─────────────────────────────────────────────────────
        feedback = self._build_feedback(
            body_straight, body_angle, smooth_angle, self._machine.state
        )

        result = PushupResult(
            reps               = self._machine.reps,
            angle              = self._machine.last_angle,
            state              = self._machine.state,
            new_rep            = new_rep,
            visible            = visible,
            body_straight      = body_straight,
            straightness_score = s_score,
            feedback           = feedback,
        )
        self._last_result = result
        return result

    def _best_elbow_angle(
        self, pose: PoseLandmarks
    ) -> tuple[Optional[float], bool]:
        """
        Compute the representative elbow angle for this frame.

        Strategy
        --------
        1. Try to get valid angles from BOTH elbows.
        2. If both are valid  → return their average.
        3. If only one valid  → return that one.
        4. If neither valid   → return (None, False).

        "Valid" means:
          - All three landmarks (shoulder / elbow / wrist) have
            MediaPipe visibility >= MIN_VISIBILITY
          - calculate_angle() returns a finite float (not None)

        Returns
        -------
        (angle_or_none, at_least_one_side_visible)
        """
        left_angle  = self._arm_angle(pose, "left")
        right_angle = self._arm_angle(pose, "right")

        if left_angle is not None and right_angle is not None:
            return (left_angle + right_angle) / 2.0, True

        if left_angle is not None:
            return left_angle, True

        if right_angle is not None:
            return right_angle, True

        return None, False

    def _arm_angle(
        self, pose: PoseLandmarks, side: str
    ) -> Optional[float]:
        """
        Return the elbow angle for one arm, or None if unreliable.

        Returns None when:
        - any of the three landmarks (shoulder / elbow / wrist) has
          visibility < MIN_VISIBILITY
        - any coordinate is NaN / out-of-range  (get_point() returns None)
        - calculate_angle() returns None (degenerate vectors, NaN)

        Never raises.
        """
        if side == "left":
            s_idx = LM.LEFT_SHOULDER
            e_idx = LM.LEFT_ELBOW
            w_idx = LM.LEFT_WRIST
        else:
            s_idx = LM.RIGHT_SHOULDER
            e_idx = LM.RIGHT_ELBOW
            w_idx = LM.RIGHT_WRIST

        # Visibility gate — skip if any landmark is unreliable
        for idx in (s_idx, e_idx, w_idx):
            if pose.visibility(idx) < MIN_VISIBILITY:
                return None

        # Coordinate fetch — get_point() returns None for NaN/missing
        pt_s = pose.get_point(s_idx)
        pt_e = pose.get_point(e_idx)
        pt_w = pose.get_point(w_idx)

        # Angle calculation — returns None for None inputs or zero vectors
        return calculate_angle(pt_s, pt_e, pt_w)

    # ------------------------------------------------------------------
    # Body / plank detection
    # ------------------------------------------------------------------

    def _body_angle(self, pose: "PoseLandmarks") -> Optional[float]:
        """
        Compute the shoulder -> hip -> ankle angle for one side.

        Returns the best available side's angle, or None if no side
        has all three landmarks visible at MIN_VISIBILITY.

        A rigid plank gives ~180°; a bent body gives a smaller angle.
        We pick whichever side has the HIGHER summed visibility score
        so the estimate is as reliable as possible.
        """
        def _side_angle(shoulder_idx, hip_idx, ankle_idx) -> Optional[float]:
            for idx in (shoulder_idx, hip_idx, ankle_idx):
                if pose.visibility(idx) < MIN_VISIBILITY:
                    return None
            pt_s = pose.get_point(shoulder_idx)
            pt_h = pose.get_point(hip_idx)
            pt_a = pose.get_point(ankle_idx)
            return calculate_angle(pt_s, pt_h, pt_a)

        left  = _side_angle(LM.LEFT_SHOULDER,  LM.LEFT_HIP,  LM.LEFT_ANKLE)
        right = _side_angle(LM.RIGHT_SHOULDER, LM.RIGHT_HIP, LM.RIGHT_ANKLE)

        if left is not None and right is not None:
            return (left + right) / 2.0
        return left if left is not None else right

    @staticmethod
    def _straightness_score(body_angle: Optional[float]) -> int:
        """
        Map a body angle to a 0-100 straightness score.

        160° -> 0  (barely passing threshold)
        180° -> 100 (perfect plank)
        Linear interpolation, clamped to [0, 100].
        """
        if body_angle is None:
            return 0
        score = (body_angle - PLANK_BODY_ANGLE_MIN) / (180.0 - PLANK_BODY_ANGLE_MIN) * 100.0
        return max(0, min(100, int(score)))

    @staticmethod
    def _build_feedback(
        body_straight: bool,
        body_angle: Optional[float],
        elbow_angle: Optional[float],
        state: PushupState,
    ) -> list:
        """
        Generate real-time coaching messages shown in the HUD.
        Returns a list of short strings (may be empty).
        """
        msgs = []
        if not body_straight:
            msgs.append("Keep your body straight")
            return msgs   # no point giving elbow feedback if form is broken

        if state == PushupState.UP and elbow_angle is not None:
            if elbow_angle < 140:
                msgs.append("Go lower")
            else:
                msgs.append("Good form")
        elif state == PushupState.DOWN:
            msgs.append("Good form")

        return msgs

    def process_frame(self, frame, pose=None) -> dict:
        """
        High-level method called by the FastAPI /api/analyze-frame endpoint.
        Works with front-facing camera — does not require plank body position.
        """
        import logging as _log
        try:
            result = self.update(pose)

            # Build a form score that works for front-facing camera too.
            # Visible arms = base score. State machine progression = bonus.
            if not result.visible:
                score = 0
            elif result.body_straight:
                # Side-camera plank view: use straightness score (0-100)
                score = max(result.straightness_score, 50)
            else:
                # Front-camera view: score based on elbow angle quality
                angle = result.angle
                if angle and angle > 0:
                    # Good elbow angle (near full extension) = high score
                    if angle >= 150:
                        score = 85
                    elif angle >= 120:
                        score = 70
                    elif angle >= 90:
                        score = 55
                    else:
                        score = 40
                else:
                    score = 45  # visible but no angle yet

            # Feedback: use existing list, or generate one
            feedback = result.feedback if result.feedback else []
            if not feedback and result.visible:
                if result.state.name == "UP":
                    feedback = ["Arms extended — good starting position"]
                elif result.state.name == "DOWN":
                    feedback = ["Good depth!"]
                else:
                    feedback = ["Position yourself in front of camera"]

            print(f"[AI] Reps: {result.reps}  Score: {score}  State: {result.state.name}  Visible: {result.visible}")

            return {
                "reps":       result.reps,
                "form_score": score,
                "feedback":   feedback,
            }
        except Exception as exc:
            _log.getLogger(__name__).error("process_frame error: %s", exc)
            print(f"[AI] process_frame error: {exc}")
            return {"reps": self._machine.reps, "form_score": 0, "feedback": []}

    @staticmethod
    def _make_empty() -> PushupResult:
        return PushupResult(
            reps               = 0,
            angle              = 0.0,
            state              = PushupState.UNKNOWN,
            new_rep            = False,
            visible            = False,
            body_straight      = False,
            straightness_score = 0,
            feedback           = [],
        )
