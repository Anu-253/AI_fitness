/**
 * useWorkout.js
 * -------------
 * Full workout lifecycle hook:
 *   1. startWorkout()  — resets counter on backend, starts camera, begins sending frames
 *   2. Per-frame loop  — POSTs canvas snapshot to /api/analyze-frame (multipart)
 *   3. stopWorkout()   — stops camera, POSTs final stats to /api/save-session
 *
 * Backend endpoints used:
 *   POST /api/analyze-frame/reset  — reset rep counter at session start
 *   POST /api/analyze-frame        — multipart frame → { reps, form_score, feedback }
 *   POST /api/save-session         — JSON summary → stored in MongoDB for analytics
 */

import { useRef, useState, useCallback, useEffect } from "react";

const BASE_URL   = "http://localhost:8000";   // change if backend runs elsewhere
const FRAME_MS   = 200;                        // send a frame every 200ms (5fps)
const USER_ID    = "default_user";             // replace with auth user_id if using auth

export function useWorkout(exerciseType = "bicep_curl") {
  const videoRef    = useRef(null);
  const canvasRef   = useRef(null);
  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);

  // Live state updated on every frame response
  const [reps,      setReps]      = useState(0);
  const [formScore, setFormScore] = useState(0);
  const [feedback,  setFeedback]  = useState([]);
  const [leftAngle,  setLeftAngle]  = useState(0);
  const [rightAngle, setRightAngle] = useState(0);

  const [isRunning, setIsRunning] = useState(false);
  const [isSaving,  setIsSaving]  = useState(false);
  const [error,     setError]     = useState(null);
  const [lastSaved, setLastSaved] = useState(null);  // session_id of last saved session

  // Keep a ref to latest reps/form_score so stopWorkout closure can read them
  const latestReps      = useRef(0);
  const latestFormScore = useRef(0);

  // ── sendFrame ────────────────────────────────────────────────────────────
  const sendFrame = useCallback(async () => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    // Draw current video frame onto hidden canvas
    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas → Blob (JPEG) and POST as multipart/form-data
    canvas.toBlob(async (blob) => {
      if (!blob) return;

      const fd = new FormData();
      fd.append("frame", blob, "frame.jpg");  // field name "frame" matches backend
      fd.append("exercise_type", exerciseType); // NEW: tells backend which counter to use

      try {
        const res = await fetch(`${BASE_URL}/api/analyze-frame`, {
          method: "POST",
          body: fd,
          // Do NOT set Content-Type header — browser sets it with boundary automatically
        });

        if (!res.ok) {
          const txt = await res.text();
          console.error("analyze-frame error:", res.status, txt);
          setError(`Server error ${res.status}`);
          return;
        }

        const data = await res.json();
        // Update all live stats
        const r = data.reps       ?? 0;
        const s = data.form_score ?? 0;
        setReps(r);
        setFormScore(s);
        setFeedback(Array.isArray(data.feedback) ? data.feedback : [data.feedback ?? ""]);
        setLeftAngle(data.left_angle   ?? 0);
        setRightAngle(data.right_angle ?? 0);
        setError(null);

        // Update refs so stopWorkout can read latest values
        latestReps.current      = r;
        latestFormScore.current = s;

      } catch (err) {
        console.error("sendFrame fetch failed:", err);
        setError("Cannot reach backend — is it running on port 8000?");
      }
    }, "image/jpeg", 0.8);
  }, []);

  // ── startWorkout ─────────────────────────────────────────────────────────
  const startWorkout = useCallback(async () => {
    setError(null);
    setReps(0);
    setFormScore(0);
    setFeedback([]);
    setLastSaved(null);
    latestReps.current      = 0;
    latestFormScore.current = 0;

    // 1. Reset backend rep counter
    try {
      await fetch(`${BASE_URL}/api/analyze-frame/reset`, { method: "POST" });
    } catch (err) {
      console.warn("Could not reset counter:", err);
    }

    // 2. Start camera
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (err) {
      setError("Camera access denied or unavailable.");
      return;
    }

    // 3. Begin frame loop
    startTimeRef.current = Date.now();
    setIsRunning(true);
    intervalRef.current = setInterval(sendFrame, FRAME_MS);
  }, [sendFrame]);

  // ── stopWorkout ──────────────────────────────────────────────────────────
  const stopWorkout = useCallback(async () => {
    // Stop frame loop
    clearInterval(intervalRef.current);
    intervalRef.current = null;
    setIsRunning(false);

    // Stop camera stream
    const video = videoRef.current;
    if (video && video.srcObject) {
      video.srcObject.getTracks().forEach((t) => t.stop());
      video.srcObject = null;
    }

    // Calculate duration
    const durationSec = startTimeRef.current
      ? Math.round((Date.now() - startTimeRef.current) / 1000)
      : 0;

    // Save session to backend → shows up in analytics
    setIsSaving(true);
    try {
      const res = await fetch(`${BASE_URL}/api/save-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id:       USER_ID,
          exercise_type: exerciseType,
          reps:          latestReps.current,
          form_score:    latestFormScore.current,
          duration_sec:  durationSec,
        }),
      });

      if (res.ok) {
        const saved = await res.json();
        setLastSaved(saved.session_id);
        console.log("Session saved:", saved.session_id);
      } else {
        const txt = await res.text();
        console.error("save-session failed:", res.status, txt);
        setError("Workout ended but could not save to database.");
      }
    } catch (err) {
      console.error("save-session fetch failed:", err);
      setError("Workout ended but server was unreachable.");
    } finally {
      setIsSaving(false);
    }
  }, [exerciseType]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(intervalRef.current);
    };
  }, []);

  return {
    // Refs for JSX elements
    videoRef,
    canvasRef,
    // Live pose data
    reps,
    formScore,
    feedback,
    leftAngle,
    rightAngle,
    // Status
    isRunning,
    isSaving,
    error,
    lastSaved,
    // Actions
    startWorkout,
    stopWorkout,
  };
}
