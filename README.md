# AI Fitness Assistant
Built a real-time computer vision system that analyzes human movement and provides automated fitness feedback.

A full-stack web application for real-time workout tracking using computer vision. The system uses a live camera feed to detect body pose, count repetitions, and score exercise form — all processed in the browser and analyzed via a Python backend.

---

## Features

- **Real-time pose detection** via webcam using MediaPipe
- **Automated rep counting** for bicep curls, push-ups, and squats
- **Form scoring** with per-session feedback (0–100 scale)
- **Session persistence** — workouts saved to MySQL with duration and score
- **Analytics dashboard** — total sessions, average score, personal best, and trend tracking
- **Fitness chatbot** — keyword-based guidance for workouts, diet, and weight management

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | React.js, inline styles           |
| Backend   | FastAPI (Python 3.10+)            |
| AI / CV   | MediaPipe Pose, OpenCV            |
| Database  | MySQL 8.x                         |
| API Comm. | REST (JSON + multipart/form-data) |

---

## Architecture


Browser (React)
  └── Captures webcam frames every 1s (JPEG via canvas)
  └── POST /api/analyze-frame  →  FastAPI
                                    └── MediaPipe Pose Detection
                                    └── Rep counter + form scorer
                                    └── Returns: reps, form_score, feedback
  └── POST /api/save-session   →  FastAPI  →  MySQL
  └── GET  /api/analytics      →  FastAPI  →  MySQL  →  Dashboard


---

## Folder Structure


```bash

ai_fitness/
├── frontend/                  # React application
│   └── src/
│       ├── components/        # WorkoutCamera, Chatbot, StatCard, etc.
│       ├── pages/             # Dashboard, Analytics, Diet, Habits, Landing
│       ├── hooks/             # useWorkout (custom hook)
│       ├── context/           # AuthContext
│       └── utils/             # api.js (Axios wrappers)
│
└── backend/                   # FastAPI application
    ├── main.py                # App entry point, CORS, route registration
    ├── routes/
    │   ├── analyze.py         # /api/analyze-frame
    │   ├── sessions.py        # /api/save-session
    │   └── analytics.py       # /api/analytics
    ├── pose/
    │   ├── detector.py        # MediaPipe wrapper
    │   ├── rep_counter.py     # Angle-based rep logic per exercise
    │   └── form_scorer.py     # Form analysis + feedback generation
    └── db/
        ├── connection.py      # MySQL connection pool
        └── models.py          # Table schema definitions

```
---

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.10+
- MySQL 8.x running locally
- Webcam access

---

### Backend


cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database
# Create a MySQL database named: ai_fitness
# Update connection settings in db/connection.py

# Run the server
uvicorn main:app --reload --port 8000


API base URL: 'http://127.0.0.1:8000/api'



### Frontend


cd frontend

# Install dependencies
npm install

# Start development server
npm start


App runs at: `http://localhost:3000`

---

## API Reference

| Method | Endpoint                    | Description                        |
|--------|-----------------------------|------------------------------------|
| POST   | `/api/analyze-frame`        | Accepts JPEG frame, returns reps, form score, feedback |
| POST   | `/api/analyze-frame/reset`  | Resets rep counter for new session |
| POST   | `/api/save-session`         | Persists session data to MySQL     |
| GET    | `/api/analytics`            | Returns aggregated user statistics |

**analyze-frame request** — multipart/form-data

frame         : image/jpeg
exercise_type : "bicep_curl" | "push_up" | "squat"


**analyze-frame response** — `application/json
{
  "reps": 8,
  "form_score": 74,
  "feedback": ["Keep your back straight", "Full range of motion detected"]
}




## Environment Notes

- The backend must be running before the frontend can track workouts or load analytics.
- Camera access requires HTTPS in production; localhost is exempt.
- CORS is configured in `main.py` to allow `http://localhost:3000`.

---

## Screenshots

### Landing Page
![Landing Page](./screenshots/landing.png)
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/8d1d2073-13e4-42f7-8b82-c7834905fe48" />


### Dashboard with Analytics and Chatbot
![Dashboard](./screenshots/dashboard.png)

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/78554312-2491-42a1-9eef-bdb0a855e2b5" />


### Backend API Logs (FastAPI + Uvicorn)
![Backend](./screenshots/backend.png)
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/88b699aa-0be0-4bf5-aa5e-045b8d2e84e8" />

---

## Future Improvements

- **User authentication** — JWT-based login with per-user workout history
- **Additional exercises** — shoulder press, deadlift, plank hold timer
- **3D skeleton overlay** — render pose landmarks on the live video feed
- **AI chatbot upgrade** — integrate LLM API for context-aware fitness coaching
- **Mobile support** — responsive layout with rear-camera toggle
- **Export** — download session history as CSV or PDF report
- **Progressive Web App** — offline support and installable on mobile

---

## License

MIT
