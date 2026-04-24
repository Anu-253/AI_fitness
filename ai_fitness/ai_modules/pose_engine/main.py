"""
main.py  —  v4  (pushup mode added)
--------------------------------------
Adds push-up tracking alongside the existing bicep curl system.
The curl system is completely unchanged — zero lines were modified.

What is new
-----------
- Press  M  to switch between CURL mode and PUSHUP mode.
- Each mode has its own HUD panel layout.
- PushupCounter is imported from the new pushup_counter.py module.
- The pushup HUD shows:
    * Rep count
    * Smoothed elbow angle
    * Current state (UP / DOWN / starting)
    * "REP!" flash on completion (same as curl mode)
    * "Tracking lost" banner when pose is None

Controls
--------
  Q  — quit
  R  — reset rep counter for the active mode
  M  — switch between CURL and PUSHUP mode

Camera tip for push-ups
-----------------------
Place the camera at elbow height, 1-2 metres to your side.
The side profile gives MediaPipe the clearest view of your arm angle.
"""

import logging
import sys
import time
from enum import Enum, auto

import cv2
import numpy as np

from detector       import PoseDetector
from rep_counter    import BicepCurlCounter, CurlState
from form_scorer    import FormScorer
from pushup_counter import PushupCounter, PushupState

logging.basicConfig(
    level  = logging.WARNING,
    format = "[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")


# ---------------------------------------------------------------------------
# App mode
# ---------------------------------------------------------------------------

class Mode(Enum):
    CURL   = auto()
    PUSHUP = auto()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CAMERA_INDEX      = 0
FRAME_W           = 1280
FRAME_H           = 720
MAX_READ_FAILURES = 30
REP_FLASH_FRAMES  = 12


# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------

FONT        = cv2.FONT_HERSHEY_SIMPLEX
WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
GREEN       = (  0, 210,  90)
RED         = ( 40,  40, 220)
AMBER       = (  0, 165, 255)
CYAN        = (200, 200,   0)
DARK_GREY   = ( 30,  30,  30)
PANEL_ALPHA = 0.60


# ---------------------------------------------------------------------------
# HUD helpers  (unchanged from v3)
# ---------------------------------------------------------------------------

def draw_panel(frame, x, y, w, h, color=DARK_GREY):
    try:
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        cv2.addWeighted(overlay, PANEL_ALPHA, frame, 1.0 - PANEL_ALPHA, 0, frame)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (80, 80, 80), 1)
    except Exception:
        pass


def put_text(frame, text, x, y, color=WHITE, scale=0.6, thickness=1):
    try:
        safe = str(text).encode("ascii", errors="replace").decode("ascii")
        cv2.putText(frame, safe, (x, y), FONT, scale, BLACK,
                    thickness + 2, cv2.LINE_AA)
        cv2.putText(frame, safe, (x, y), FONT, scale, color,
                    thickness, cv2.LINE_AA)
    except Exception:
        pass
    return y + int(scale * 36) + 4


def score_color(score):
    if score >= 80: return GREEN
    if score >= 55: return AMBER
    return RED


def angle_color(angle):
    if angle >= 140: return GREEN
    if angle >= 70:  return AMBER
    return RED


def curl_state_label(state):
    return {
        CurlState.DOWN:    "DOWN (extended)",
        CurlState.UP:      "UP   (curled)",
        CurlState.UNKNOWN: "---  (starting)",
    }.get(state, "unknown")


def pushup_state_label(state):
    return {
        PushupState.UP:      "UP   (arms extended)",
        PushupState.DOWN:    "DOWN (chest lowered)",
        PushupState.UNKNOWN: "---  (get into position)",
    }.get(state, "unknown")


def draw_rep_flash(frame, flash_frames):
    if flash_frames <= 0:
        return
    try:
        h, w  = frame.shape[:2]
        alpha = min(1.0, flash_frames / REP_FLASH_FRAMES)
        overlay = frame.copy()
        cv2.putText(overlay, "REP!", (w // 2 - 80, h // 2 + 20),
                    FONT, 3.5, GREEN, 8, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# HUD — CURL mode  (identical to v3, untouched)
# ---------------------------------------------------------------------------

def draw_curl_hud(frame, rep_result, form_report, fps, flash_frames):
    try:
        h, w = frame.shape[:2]
        PAD  = 12

        # Mode badge
        draw_panel(frame, 8, 8, 145, 28, color=(60, 30, 0))
        put_text(frame, "MODE: CURL", 8 + PAD, 29, AMBER, 0.52)

        # Left panel: rep counts
        lp_w, lp_h = 240, 195
        draw_panel(frame, 8, 42, lp_w, lp_h)

        y = 42 + PAD + 16
        y = put_text(frame, "BICEP CURL TRACKER", 8 + PAD, y, WHITE, 0.52)
        y += 4
        y = put_text(frame, f"LEFT   reps : {rep_result.left_reps}",
                     8 + PAD, y, GREEN, 0.65)
        y = put_text(frame, f"RIGHT  reps : {rep_result.right_reps}",
                     8 + PAD, y, GREEN, 0.65)
        y = put_text(frame, f"TOTAL       : {rep_result.total_reps}",
                     8 + PAD, y, WHITE, 0.78, 2)
        y += 6
        put_text(frame, f"L: {rep_result.left_angle:.0f} deg",
                 8 + PAD,       y, angle_color(rep_result.left_angle),  0.52)
        put_text(frame, f"R: {rep_result.right_angle:.0f} deg",
                 8 + PAD + 115, y, angle_color(rep_result.right_angle), 0.52)
        y += 26
        put_text(frame, curl_state_label(rep_result.left_state),
                 8 + PAD, y, AMBER, 0.46)
        y += 20
        put_text(frame, curl_state_label(rep_result.right_state),
                 8 + PAD, y, AMBER, 0.46)

        # Right panel: form score (only once scorer has run)
        if form_report is not None:
            rp_w, rp_h = 215, 135
            rp_x = w - rp_w - 8
            draw_panel(frame, rp_x, 8, rp_w, rp_h)
            sc     = form_report.overall_score
            sc_col = score_color(sc)
            y = 8 + PAD + 16
            y = put_text(frame, "FORM SCORE",      rp_x + PAD, y, WHITE,  0.52)
            y = put_text(frame, f"{sc:.0f} / 100", rp_x + PAD, y, sc_col, 0.85, 2)
            y = put_text(frame, f"Grade : {form_report.grade}",
                         rp_x + PAD, y, sc_col, 0.62)
            put_text(frame, f"FPS   : {fps:.0f}", rp_x + PAD, y, WHITE, 0.52)

            # Bottom panel: feedback
            if form_report.feedback:
                n     = len(form_report.feedback)
                fb_h  = n * 30 + 16
                fb_y0 = h - fb_h - 8
                draw_panel(frame, 8, fb_y0, w - 16, fb_h, color=(20, 20, 150))
                y = fb_y0 + PAD + 10
                for msg in form_report.feedback:
                    y = put_text(frame, f"[!] {msg}", 8 + PAD, y, WHITE, 0.56)

        draw_rep_flash(frame, flash_frames)

    except Exception as exc:
        log.warning("draw_curl_hud() error: %s", exc)


# ---------------------------------------------------------------------------
# HUD — PUSHUP mode  (new)
# ---------------------------------------------------------------------------

def draw_pushup_hud(frame, pushup_result, fps, flash_frames):
    try:
        h, w = frame.shape[:2]
        PAD  = 12

        # Mode badge
        draw_panel(frame, 8, 8, 165, 28, color=(0, 50, 0))
        put_text(frame, "MODE: PUSH-UP", 8 + PAD, 29, GREEN, 0.52)

        # Left panel: push-up stats
        lp_w, lp_h = 270, 155
        draw_panel(frame, 8, 42, lp_w, lp_h)

        y = 42 + PAD + 16
        y = put_text(frame, "PUSH-UP TRACKER", 8 + PAD, y, WHITE, 0.52)
        y += 4
        y = put_text(frame, f"REPS  : {pushup_result.reps}",
                     8 + PAD, y, GREEN, 0.80, 2)
        y += 4

        ang     = pushup_result.angle
        ang_col = angle_color(ang)
        y = put_text(frame, f"Elbow angle : {ang:.0f} deg",
                     8 + PAD, y, ang_col, 0.58)
        y = put_text(frame, pushup_state_label(pushup_result.state),
                     8 + PAD, y, AMBER, 0.50)

        if not pushup_result.visible:
            put_text(frame, "[!] Arms not visible", 8 + PAD, y, RED, 0.50)

        # Right panel: FPS
        rp_w, rp_h = 160, 52
        rp_x = w - rp_w - 8
        draw_panel(frame, rp_x, 8, rp_w, rp_h)
        put_text(frame, f"FPS : {fps:.0f}", rp_x + PAD, 8 + PAD + 16, WHITE, 0.58)

        # Camera tip while in UNKNOWN state
        if pushup_result.state == PushupState.UNKNOWN:
            tip = "Tip: camera to your side, at elbow height"
            put_text(frame, tip, w // 2 - 250, h - 36, CYAN, 0.52)

        draw_rep_flash(frame, flash_frames)

    except Exception as exc:
        log.warning("draw_pushup_hud() error: %s", exc)


# ---------------------------------------------------------------------------
# Controls hint overlay
# ---------------------------------------------------------------------------

def draw_key_hint(frame, mode):
    try:
        h, w = frame.shape[:2]
        lines = ["Q : quit", "R : reset reps", "C : curl mode", "P : pushup mode"]
        y = h - 10 - len(lines) * 22
        for line in lines:
            put_text(frame, line, w - 170, y, (150, 150, 150), 0.44)
            y += 22
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print("  AI Fitness Tracker v4  |  Q=quit  R=reset  C=curl  P=pushup")
    print("=" * 65)

    detector       = PoseDetector(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        model_complexity=1,
        draw_landmarks=False,
    )
    curl_counter   = BicepCurlCounter()
    pushup_counter = PushupCounter()
    scorer         = FormScorer()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera index {CAMERA_INDEX}.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)

    mode               = Mode.CURL
    prev_time          = time.time()
    fps                = 0.0
    flash_frames       = 0
    read_failures      = 0

    last_curl_result   = curl_counter._last_result
    last_pushup_result = pushup_counter._last_result
    last_form_report   = None

    print("[INFO] Camera open. Default mode: CURL.")
    print("[INFO] Press P to switch to PUSH-UP mode, C to return to CURL.")
    print("[INFO] For push-ups, place camera to your side at elbow height.\n")

    try:
        while True:
            # ── Frame capture ─────────────────────────────────────────────
            try:
                ret, frame = cap.read()
            except Exception as exc:
                log.warning("cap.read() exception: %s", exc)
                ret, frame = False, None

            if not ret or frame is None or frame.size == 0:
                read_failures += 1
                log.warning("Bad frame #%d/%d.", read_failures, MAX_READ_FAILURES)
                if read_failures >= MAX_READ_FAILURES:
                    print("[ERROR] Too many consecutive camera failures.")
                    break
                time.sleep(0.05)
                continue

            read_failures = 0
            frame = cv2.flip(frame, 1)

            # ── Per-frame processing ──────────────────────────────────────
            try:
                pose = detector.detect(frame)

                if pose is not None:
                    if mode == Mode.CURL:
                        curl_result      = curl_counter.update(pose)
                        last_curl_result = curl_result
                        form_report      = scorer.score(pose)
                        last_form_report = form_report
                        detector.draw_colored_skeleton(
                            frame, pose, form_report.feedback)
                        if curl_result.new_rep:
                            flash_frames = REP_FLASH_FRAMES

                    else:  # PUSHUP
                        pushup_result      = pushup_counter.update(pose)
                        last_pushup_result = pushup_result
                        detector.draw_colored_skeleton(frame, pose, [])
                        if pushup_result.new_rep:
                            flash_frames = REP_FLASH_FRAMES

                else:
                    if mode == Mode.CURL:
                        curl_counter.update(None)
                    else:
                        pushup_counter.update(None)
                    put_text(frame,
                             "Tracking lost - stay in frame",
                             frame.shape[1] // 2 - 200, 40, AMBER, 0.65)

            except Exception as exc:
                log.error("Per-frame error: %s", exc, exc_info=True)

            if flash_frames > 0:
                flash_frames -= 1

            # ── FPS ───────────────────────────────────────────────────────
            try:
                now       = time.time()
                fps       = 0.9 * fps + 0.1 / max(now - prev_time, 1e-6)
                prev_time = now
            except Exception:
                pass

            # ── HUD ───────────────────────────────────────────────────────
            if mode == Mode.CURL:
                draw_curl_hud(frame, last_curl_result,
                              last_form_report, fps, flash_frames)
            elif mode == Mode.PUSHUP:
                draw_pushup_hud(frame, last_pushup_result, fps, flash_frames)

            draw_key_hint(frame, mode)

            # ── Display ───────────────────────────────────────────────────
            try:
                if frame is not None and frame.size > 0:
                    cv2.imshow("AI Fitness Tracker v4", frame)
            except cv2.error as exc:
                log.warning("imshow error: %s", exc)

            # ── Keys ──────────────────────────────────────────────────────
            try:
                key = cv2.waitKey(1) & 0xFF
            except Exception:
                key = 0xFF

            if key == ord("q"):
                print("\n[INFO] Quit requested.")
                break

            elif key == ord("r"):
                if mode == Mode.CURL:
                    prev = last_curl_result.total_reps
                    curl_counter.reset()
                    last_curl_result = curl_counter._last_result
                    last_form_report = None
                    print(f"[INFO] Curl reset. Previous set: {prev} reps.")
                else:
                    prev = last_pushup_result.reps
                    pushup_counter.reset()
                    last_pushup_result = pushup_counter._last_result
                    print(f"[INFO] Push-up reset. Previous set: {prev} reps.")

            elif key == ord("c") and mode != Mode.CURL:
                mode = Mode.CURL
                flash_frames = 0
                print("[INFO] Switched to CURL mode.")

            elif key == ord("p") and mode != Mode.PUSHUP:
                mode = Mode.PUSHUP
                flash_frames = 0
                print("[INFO] Switched to PUSH-UP mode.")
                print("[INFO] Camera tip: place it to your SIDE at elbow height.")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted.")

    except Exception as exc:
        log.critical("Unhandled main loop exception: %s", exc, exc_info=True)

    finally:
        print("[INFO] Releasing resources...")
        for fn in (cap.release, detector.close, cv2.destroyAllWindows):
            try:
                fn()
            except Exception:
                pass

    # ── Session summary ───────────────────────────────────────────────────
    print()
    print("-" * 55)
    print("  SESSION SUMMARY")
    print("-" * 55)
    print(f"  Bicep curl reps  : {last_curl_result.total_reps}"
          f"  (L:{last_curl_result.left_reps}  R:{last_curl_result.right_reps})")
    print(f"  Push-up reps     : {last_pushup_result.reps}")
    if last_form_report:
        print(f"  Curl form score  : {last_form_report.overall_score} / 100"
              f"  (Grade {last_form_report.grade})")
        if last_form_report.feedback:
            print("  Curl form notes:")
            for msg in last_form_report.feedback:
                print(f"    - {msg}")
    print("-" * 55)


if __name__ == "__main__":
    main()
