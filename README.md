# Skylar – Your Gentle Companion

Skylar is a soft, glassmorphism-inspired AI companion designed to make lonely or overwhelmed people feel a little less alone.

It’s not a productivity bot or a corporate assistant. It’s “hey, talk to me about your day, I’ve got you” in app form — with safety rails.

---

## ✨ What Skylar Does

- **Warm emotional support**  
  Skylar listens, reflects your feelings, and answers in a kind, grounded, non-cringey tone.
  
- **Customizable companion**  
  Choose Skylar’s name (default: **Skylar**) and vibe (`warm`, `calm`, `playful`) so it feels like *your* friend.

- **Glassmorphism UI**  
  A clean, frosted-glass style chat interface built to feel cozy rather than clinical.

- **Streaming replies**  
  Server-Sent Events (SSE) give you smooth “typing” style responses instead of jumpy walls of text.

- **Basic memory per session**  
  Session history is kept in memory so conversations feel coherent. (Optional DB hooks are ready for long-term profiles.)

- **Safety & boundaries built-in**
  - Crisis language detection → gentle grounding + “please reach real help” style responses.
  - Content moderation hook to avoid harmful / illegal guidance.
  - Always reminds: “I’m an AI friend, not a therapist or doctor.”

---

## 🧱 Tech Stack

**Frontend**

- React + Vite (modern, fast dev + static build to `dist`)   
- Glassmorphism CSS with soft gradients, blurred panels, chat bubbles.
- Uses `@microsoft/fetch-event-source` to consume SSE from the backend.

**Backend**

- FastAPI for a clean, typed HTTP API.   
- `/start` → creates a session & sends Skylar’s opening message.  
- `/chat` → non-streaming JSON replies.  
- `/chat/stream` → streaming replies via Server-Sent Events.
- Pluggable LLM client:
  - Originally designed for OpenAI Chat Completions.
  - Can be swapped to other providers (OpenRouter, Groq, etc).
- In-memory session store by default (no external Redis required).
- Optional Postgres profile support via SQLAlchemy (if `DATABASE_URL` is set).

---

## ⚙️ Environment Variables

Backend expects:

- `OPENAI_API_KEY` (or your chosen provider’s key)  
- `DATABASE_URL` (optional, for persistent profiles)

Frontend:

- `VITE_API_BASE` – base URL of the backend API in production  
  - Local dev default: `http://localhost:8000`
  - Example (Render): `https://your-backend-service.onrender.com`

---

## 🏃 Running Locally

### 1. Backend

```bash
cd backend
python -m venv venv
# activate venv (Windows)
venv\Scripts\activate
# or (Unix/macOS)
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# set your key
set OPENAI_API_KEY=your_key_here        # Windows (cmd)
$env:OPENAI_API_KEY="your_key_here"     # PowerShell
export OPENAI_API_KEY=your_key_here     # macOS/Linux

python -m uvicorn main:app --reload
