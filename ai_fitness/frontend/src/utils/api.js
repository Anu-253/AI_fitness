import axios from 'axios';

const BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach token ────────────────────────────────────
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('fitness_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  console.log(`[API] ${cfg.method?.toUpperCase()} ${cfg.baseURL}${cfg.url}`, cfg.data || '');
  return cfg;
});

// ── Response interceptor: handle 401 ────────────────────────────────────
api.interceptors.response.use(
  res => {
    console.log(`[API] ✓ ${res.config.url}`, res.data);
    return res;
  },
  err => {
    const status = err?.response?.status;
    const url    = err?.config?.url || '';
    console.error(`[API] ✗ ${url} → ${status}`, err?.response?.data || err.message);
    if (status === 401) {
      localStorage.removeItem('fitness_token');
      localStorage.removeItem('fitness_user');
      localStorage.removeItem('fitness_user_id');
      localStorage.removeItem('fitness_username');
      window.location.reload();
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────
export const register = (data) => api.post('/register', data);
export const login    = (data) => api.post('/login', data);
export const getMe    = ()     => api.get('/me');

// ── Realtime ──────────────────────────────────────────────────────────────
export const getRealtimeFrame = (encode = true) =>
  api.get(`/realtime/frame?encode=${encode}`);
export const resetReps = () => api.post('/realtime/reset');

// ── Workout ───────────────────────────────────────────────────────────────
export const startWorkout      = (data)                  => api.post('/start-workout', data);
export const endWorkout        = (data)                  => api.post('/end-workout', data);
export const getWorkoutHistory = (userId = 'default_user', limit = 20) =>
  api.get('/workout-history', { params: { user_id: userId, limit } });

// ── Performance ───────────────────────────────────────────────────────────
export const postPerformance = (data) => api.post('/performance', data);
export const getSessionPerf  = (id)   => api.get(`/performance/${id}`);

// ── Analytics ─────────────────────────────────────────────────────────────
// FIX: was /analytics?user_id=... — backend expects /analytics/{user_id}
export const getAnalytics = (userId = 'default_user', limit = 30) =>
  api.get(`/analytics/${userId}`, { params: { limit } });

// ── Diet ──────────────────────────────────────────────────────────────────
export const getDietPlan = (data) => api.post('/diet', data);

// ── Habit ─────────────────────────────────────────────────────────────────
export const logHabit        = (data)   => api.post('/habit', data);
export const getHabitSummary = (userId) => api.get(`/habit/${userId}`);

// ── Health ────────────────────────────────────────────────────────────────
export const healthCheck = () =>
  axios.get(
    `${process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000'}/health`,
    { timeout: 3000 }
  );

export default api;

// ── Delete workout history ────────────────────────────────────────────────
export const deleteWorkout    = (sessionId) => api.delete(`/workout/${sessionId}`);
export const deleteAllHistory = (userId)    => api.delete(`/workout-history/${userId}`);
