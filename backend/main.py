import uuid
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

# ⛔ Removed OpenAI error imports
# from openai import RateLimitError, APIError

# ✅ Import from your Gemini llm_client
from llm_client import (
    generate_llm_reply,
    BASE_SYSTEM_PROMPT,
    build_prompt,  # Gemini-style prompt builder
    client,        # google.genai Client
)
from safety import is_crisis_text, crisis_safe_reply, moderate_text
from redis_client import (
    save_session_meta,
    get_session_meta,
    append_history,
    get_history,
)
from db import init_db_if_configured

app = FastAPI(
    title="CompanionBot Plus",
    description=(
        "A friendly, glassy AI companion with LLM support, safety filters, "
        "and gentle long-term memory (optional). Not a therapist."
    ),
    version="2.0.0",
)

# CORS for dev; restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartSessionRequest(BaseModel):
    user_name: str
    companion_name: Optional[str] = None
    style: Optional[str] = "warm"
    user_external_id: Optional[str] = None  # optional stable id for DB profile


class StartSessionResponse(BaseModel):
    session_id: str
    opening_message: str
    companion_name: str
    style: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.on_event("startup")
async def on_startup():
    # Safe: only runs if DATABASE_URL is set. No-op otherwise.
    await init_db_if_configured()


@app.post("/start", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest):
    user_name = req.user_name.strip()
    if not user_name:
        raise HTTPException(status_code=400, detail="user_name is required")

    style = (req.style or "warm").lower()
    if style not in ("warm", "calm", "playful"):
        style = "warm"

    companion_name = (req.companion_name or "Luna").strip()

    # Optional persistent profile (only if DATABASE_URL + user_external_id configured)
    if req.user_external_id:
        try:
            from db import upsert_user_profile, get_user_profile

            profile = await get_user_profile(req.user_external_id)
            if profile:
                companion_name = profile.companion_name
                style = profile.preferred_style
            else:
                await upsert_user_profile(
                    user_external_id=req.user_external_id,
                    display_name=user_name,
                    companion_name=companion_name,
                    preferred_style=style,
                )
        except Exception:
            # If DB not configured / broken, ignore and continue
            pass

    session_id = str(uuid.uuid4())
    save_session_meta(session_id, user_name, companion_name, style)

    opening = (
        f"Hey {user_name} ✨ I’m {companion_name}. "
        "You can vent, celebrate, overthink out loud, or just exist with me. "
        "I’m here to help you feel a little less alone."
        "\n\n_(I’m an AI companion, not a therapist or doctor.)_"
    )

    append_history(session_id, "assistant", opening)

    return StartSessionResponse(
        session_id=session_id,
        opening_message=opening,
        companion_name=companion_name,
        style=style,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Non-streaming chat endpoint (simple JSON response).
    Uses generate_llm_reply() which already calls Gemini.
    """
    meta = get_session_meta(req.session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found. Start a new one.")

    user_msg = (req.message or "").strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    user_name = meta["user_name"]
    companion_name = meta["companion_name"]

    append_history(req.session_id, "user", user_msg)
    history = get_history(req.session_id)

    # Crisis check
    if is_crisis_text(user_msg):
        reply = crisis_safe_reply(user_name, companion_name)
        append_history(req.session_id, "assistant", reply)
        return ChatResponse(reply=reply)

    # Moderation
    flagged, _ = moderate_text(user_msg)
    if flagged:
        safe_msg = (
            f"{user_name}, thank you for trusting me. "
            "Some of what you shared touches topics I’m not allowed to go into. "
            "I can sit with you in the feelings and support safer choices, "
            "but I can’t help with anything harmful or illegal."
            "\n\n_(I’m an AI friend, not a therapist or lawyer.)_"
        )
        append_history(req.session_id, "assistant", safe_msg)
        return ChatResponse(reply=safe_msg)

    # LLM reply (Gemini via generate_llm_reply)
    reply = generate_llm_reply(companion_name, history, user_msg)
    append_history(req.session_id, "assistant", reply)
    return ChatResponse(reply=reply)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming endpoint using Server-Sent Events (SSE).
    Now uses Gemini streaming: client.models.generate_content_stream().
    """
    meta = get_session_meta(req.session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found. Start a new one.")

    user_msg = (req.message or "").strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    user_name = meta["user_name"]
    companion_name = meta["companion_name"]

    append_history(req.session_id, "user", user_msg)
    history = get_history(req.session_id)

    # 1) Crisis handling: send one safe message, no token stream
    if is_crisis_text(user_msg):
        crisis = crisis_safe_reply(user_name, companion_name)
        append_history(req.session_id, "assistant", crisis)

        def crisis_gen():
            yield f"data: {crisis}\n\n"
            yield "data: [END]\n\n"

        return StreamingResponse(crisis_gen(), media_type="text/event-stream")

    # 2) Moderation handling
    flagged, _ = moderate_text(user_msg)
    if flagged:
        safe_msg = (
            f"{user_name}, thank you for trusting me. "
            "Some of what you shared touches topics I’m not allowed to go into. "
            "I can sit with you in the feelings and support safer choices, "
            "but I can’t help with anything harmful or illegal."
            "\n\n_(I’m an AI friend, not a therapist or lawyer.)_"
        )
        append_history(req.session_id, "assistant", safe_msg)

        def safe_gen():
            yield f"data: {safe_msg}\n\n"
            yield "data: [END]\n\n"

        return StreamingResponse(safe_gen(), media_type="text/event-stream")

    # 3) Normal LLM streaming with Gemini
    prompt = build_prompt(
        BASE_SYSTEM_PROMPT.format(companion_name=companion_name),
        history,
        user_msg,
    )

    def event_stream():
        full_reply = ""

        try:
            # Official streaming pattern with google-genai:
            # for chunk in client.models.generate_content_stream(...): print(chunk.text) :contentReference[oaicite:2]{index=2}
            stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            for chunk in stream:
                delta = (chunk.text or "").strip()
                if delta:
                    full_reply += delta
                    yield f"data: {delta}\n\n"

            # Ensure disclaimer footer
            if (
                "I’m an AI friend" not in full_reply
                and "I'm an AI friend" not in full_reply
            ):
                footer = (
                    "\n\n(I’m an AI friend, not a therapist or doctor, "
                    "but I’m really glad you’re talking to me.)"
                )
                full_reply += footer
                yield f"data: {footer}\n\n"

            append_history(req.session_id, "assistant", full_reply)

        except Exception:
            # We can't distinguish rate limit vs other errors easily here,
            # so use one gentle fallback.
            msg = (
                "I ran into an issue talking to my model just now. "
                "Can we try again in a bit? 💛"
            )
            append_history(req.session_id, "assistant", msg)
            yield f"data: {msg}\n\n"

        # Signal end of stream
        yield "data: [END]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok", "message": "CompanionBot Plus is running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
