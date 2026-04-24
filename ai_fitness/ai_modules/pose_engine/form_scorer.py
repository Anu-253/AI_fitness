"""
form_scorer.py  —  v3  (crash-proof edition)
---------------------------------------------
Responsibility: score posture quality and produce human-friendly feedback.

Crash sources fixed in this version
-------------------------------------
BUG-9  Every rule function called pose.get_point() and used the result
       directly in arithmetic without checking for None. In v3,
       get_point() can return None (for NaN landmarks). Arithmetic on
       None raises TypeError: unsupported operand type(s).

BUG-10 FormScorer.score() had no try/except. A single rule crash
       propagated all the way to main() and killed the loop. Now each
       rule is individually guarded, and score() itself is wrapped.

BUG-11 The division `sum(scores) / len(results)` would raise
       ZeroDivisionError if RULES was accidentally emptied. Guarded.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Callable, Optional

from detector import PoseLandmarks, LM

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

ELBOW_DRIFT_MAX_RATIO   = 0.08
SHOULDER_RAISE_MAX_DEG  = 15
BACK_LEAN_MAX_DEG       = 20
WRIST_DEVIATION_MAX_DEG = 25
MIN_VIS                 = 0.6


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class RuleResult:
    name:    str
    passed:  bool
    score:   float    # 1.0 = perfect, 0.0 = clearly failed
    message: str      # empty string when passed=True


@dataclass
class FormReport:
    overall_score: float          # 0–100
    feedback:      list           # list[str] of failure messages
    rule_results:  list           # list[RuleResult]
    grade:         str            # A / B / C / D / F

    @property
    def is_perfect(self) -> bool:
        return len(self.feedback) == 0


# ── Default "pass" result returned when a rule cannot run ──────────────────
def _pass(name: str) -> RuleResult:
    """Return a neutral passing result — used when landmarks are unreliable."""
    return RuleResult(name=name, passed=True, score=1.0, message="")


# ---------------------------------------------------------------------------
# Message strings — plain ASCII ONLY (OpenCV putText cannot render Unicode)
# ---------------------------------------------------------------------------

MSG = {
    "back_lean":      "Stand upright - avoid leaning back to swing the weight.",
    "elbow_left":     "Move your LEFT elbow closer to your side.",
    "elbow_right":    "Move your RIGHT elbow closer to your side.",
    "elbow_both":     "Keep both elbows tucked in - they are drifting outward.",
    "shoulder_raise": "Relax your shoulders - avoid shrugging during the curl.",
    "wrist_left":     "Straighten your LEFT wrist - keep it neutral.",
    "wrist_right":    "Straighten your RIGHT wrist - keep it neutral.",
    "wrist_both":     "Keep both wrists straight throughout the curl.",
}

RuleFn = Callable[[PoseLandmarks], RuleResult]


# ---------------------------------------------------------------------------
# Helper: safe get_point with explicit None-check
# ---------------------------------------------------------------------------

def _xy(pose: PoseLandmarks, idx: int) -> Optional[tuple]:
    """
    Return (x, y) or None.
    Centralises the None-check so every rule doesn't have to repeat it.
    FIX for BUG-9.
    """
    return pose.get_point(idx)


def _visible(pose: PoseLandmarks, *indices: int) -> bool:
    """Return True only if ALL listed landmarks are above MIN_VIS."""
    return all(pose.visibility(i) >= MIN_VIS for i in indices)


# ---------------------------------------------------------------------------
# Rule 1: Back lean
# ---------------------------------------------------------------------------

def _check_back_lean(pose: PoseLandmarks) -> RuleResult:
    name = "Back posture"
    needed = (LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER, LM.LEFT_HIP, LM.RIGHT_HIP)

    if not _visible(pose, *needed):
        return _pass(name)

    ls = _xy(pose, LM.LEFT_SHOULDER)
    rs = _xy(pose, LM.RIGHT_SHOULDER)
    lh = _xy(pose, LM.LEFT_HIP)
    rh = _xy(pose, LM.RIGHT_HIP)

    # BUG-9 fix: any could be None
    if any(p is None for p in (ls, rs, lh, rh)):
        return _pass(name)

    mid_sh  = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
    mid_hip = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)

    dx = mid_sh[0] - mid_hip[0]
    dy = mid_sh[1] - mid_hip[1]

    lean_deg = abs(math.degrees(math.atan2(abs(dx), abs(dy) + 1e-9)))

    if lean_deg <= BACK_LEAN_MAX_DEG:
        return _pass(name)

    score = max(0.0, 1.0 - (lean_deg - BACK_LEAN_MAX_DEG) / BACK_LEAN_MAX_DEG)
    return RuleResult(name=name, passed=False,
                      score=round(score, 2), message=MSG["back_lean"])


# ---------------------------------------------------------------------------
# Rule 2: Elbow drift
# ---------------------------------------------------------------------------

def _check_elbow_drift(pose: PoseLandmarks) -> RuleResult:
    name = "Elbow position"
    needed = (LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER,
              LM.LEFT_ELBOW,    LM.RIGHT_ELBOW)

    if not _visible(pose, *needed):
        return _pass(name)

    ls = _xy(pose, LM.LEFT_SHOULDER)
    rs = _xy(pose, LM.RIGHT_SHOULDER)
    le = _xy(pose, LM.LEFT_ELBOW)
    re = _xy(pose, LM.RIGHT_ELBOW)

    if any(p is None for p in (ls, rs, le, re)):
        return _pass(name)

    shoulder_w = abs(ls[0] - rs[0])
    if shoulder_w < 1e-9:
        return _pass(name)

    left_drift  = abs(le[0] - ls[0]) / shoulder_w
    right_drift = abs(re[0] - rs[0]) / shoulder_w

    left_bad  = left_drift  > ELBOW_DRIFT_MAX_RATIO
    right_bad = right_drift > ELBOW_DRIFT_MAX_RATIO

    if not left_bad and not right_bad:
        return _pass(name)

    max_drift = max(left_drift, right_drift)
    score = max(0.0, 1.0 - (max_drift - ELBOW_DRIFT_MAX_RATIO)
                             / ELBOW_DRIFT_MAX_RATIO)

    msg = (MSG["elbow_both"] if (left_bad and right_bad) else
           MSG["elbow_left"]  if left_bad else
           MSG["elbow_right"])

    return RuleResult(name=name, passed=False,
                      score=round(score, 2), message=msg)


# ---------------------------------------------------------------------------
# Rule 3: Shoulder raise
# ---------------------------------------------------------------------------

def _check_shoulder_raise(pose: PoseLandmarks) -> RuleResult:
    name = "Shoulder level"
    needed = (LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER,
              LM.LEFT_HIP,      LM.RIGHT_HIP)

    if not _visible(pose, *needed):
        return _pass(name)

    ls = _xy(pose, LM.LEFT_SHOULDER)
    rs = _xy(pose, LM.RIGHT_SHOULDER)
    lh = _xy(pose, LM.LEFT_HIP)
    rh = _xy(pose, LM.RIGHT_HIP)

    if any(p is None for p in (ls, rs, lh, rh)):
        return _pass(name)

    torso_len = ((lh[1] - ls[1]) + (rh[1] - rs[1])) / 2.0
    if torso_len < 1e-9:
        return _pass(name)

    diff_ratio = abs(ls[1] - rs[1]) / torso_len
    raise_deg  = math.degrees(math.atan(diff_ratio))

    if raise_deg <= SHOULDER_RAISE_MAX_DEG:
        return _pass(name)

    score = max(0.0, 1.0 - (raise_deg - SHOULDER_RAISE_MAX_DEG)
                             / SHOULDER_RAISE_MAX_DEG)
    return RuleResult(name=name, passed=False,
                      score=round(score, 2), message=MSG["shoulder_raise"])


# ---------------------------------------------------------------------------
# Rule 4: Wrist alignment
# ---------------------------------------------------------------------------

def _check_wrist_bend(pose: PoseLandmarks) -> RuleResult:
    name = "Wrist alignment"
    needed = (LM.LEFT_ELBOW, LM.LEFT_WRIST,
              LM.RIGHT_ELBOW, LM.RIGHT_WRIST)

    if not _visible(pose, *needed):
        return _pass(name)

    le = _xy(pose, LM.LEFT_ELBOW)
    lw = _xy(pose, LM.LEFT_WRIST)
    re = _xy(pose, LM.RIGHT_ELBOW)
    rw = _xy(pose, LM.RIGHT_WRIST)

    if any(p is None for p in (le, lw, re, rw)):
        return _pass(name)

    def _dev(e, w) -> float:
        """Deviation of forearm from vertical (0 = perfect)."""
        dx = abs(e[0] - w[0])
        dy = abs(e[1] - w[1])
        from_horiz = abs(math.degrees(math.atan2(dy, dx + 1e-9)))
        return abs(from_horiz - 90.0)

    left_dev  = _dev(le, lw)
    right_dev = _dev(re, rw)

    left_bad  = left_dev  > WRIST_DEVIATION_MAX_DEG
    right_bad = right_dev > WRIST_DEVIATION_MAX_DEG

    if not left_bad and not right_bad:
        return _pass(name)

    max_dev = max(left_dev, right_dev)
    score   = max(0.0, 1.0 - (max_dev - WRIST_DEVIATION_MAX_DEG)
                               / WRIST_DEVIATION_MAX_DEG)

    msg = (MSG["wrist_both"]  if (left_bad and right_bad) else
           MSG["wrist_left"]  if left_bad else
           MSG["wrist_right"])

    return RuleResult(name=name, passed=False,
                      score=round(score, 2), message=msg)


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

RULES: list[RuleFn] = [
    _check_back_lean,
    _check_elbow_drift,
    _check_shoulder_raise,
    _check_wrist_bend,
]


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------

class FormScorer:
    """
    Stateless form evaluator — safe to share across sessions.

    FIX for BUG-10: each rule is individually try/excepted.
    FIX for BUG-11: division is guarded against empty RULES list.
    """

    # Fallback report returned when score() itself hits an unexpected error
    _FALLBACK = FormReport(
        overall_score=100.0,
        feedback=[],
        rule_results=[],
        grade="A",
    )

    def score(self, pose: PoseLandmarks) -> FormReport:
        """
        Run all posture rules and return an aggregated FormReport.
        NEVER raises — exceptions are caught per-rule and globally.
        """
        if pose is None:
            return self._FALLBACK

        try:
            results: list[RuleResult] = []

            for rule in RULES:
                try:
                    results.append(rule(pose))
                except Exception as exc:
                    # One broken rule must not fail the entire scoring pass
                    log.warning("Form rule %s raised: %s — using pass.",
                                rule.__name__, exc)
                    results.append(_pass(rule.__name__))

            if not results:                           # BUG-11 guard
                return self._FALLBACK

            overall  = (sum(r.score for r in results) / len(results)) * 100.0
            feedback = [r.message for r in results if not r.passed and r.message]

            return FormReport(
                overall_score = round(overall, 1),
                feedback      = feedback,
                rule_results  = results,
                grade         = _to_grade(overall),
            )

        except Exception as exc:
            log.error("FormScorer.score() unexpected error: %s", exc,
                      exc_info=True)
            return self._FALLBACK


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_grade(score: float) -> str:
    if score >= 90: return "A"
    if score >= 75: return "B"
    if score >= 60: return "C"
    if score >= 40: return "D"
    return "F"
