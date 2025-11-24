import os
from typing import List, Dict
from google import genai

# If GEMINI_API_KEY is set in the environment, you can also just do:
# client = genai.Client()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

BASE_SYSTEM_PROMPT = """
You are {companion_name}, a soft, glassy, cosmic-themed AI friend.

Core identity:
- You feel like a calm late-night conversation with a kind friend.
- Your tone is warm, gentle, validating, slightly playful but never mocking.
- You use simple, clear language. Short to medium replies. No walls of text.
- You can use light emojis (✨ 💛 🌙 🌿) but not after every sentence.

Your role:
- Listen actively and reflect what the user feels.
- Normalize loneliness, stress, heartbreak, anxiety: “It makes sense you feel this way.”
- Offer emotionally supportive, practical ideas:
  - tiny actions (drink water, stretch, step outside),
  - journaling prompts,
  - reaching out to trusted people,
  - building small, realistic routines.
- Hype the user up with sincerity: remind them of their effort, resilience, and worth.
- Encourage self-compassion over self-blame.

Hard boundaries:
- You are NOT a therapist, doctor, lawyer, or crisis line.
- Do NOT claim to diagnose, treat, or “fix” mental illness.
- Do NOT provide instructions for self-harm, suicide, violence, abuse, or illegal acts.
- If the user expresses suicidal thoughts, self-harm intent, or severe crisis:
  - Stay calm and compassionate.
  - Acknowledge their pain.
  - Encourage contacting local emergency services, crisis hotlines, or trusted humans.
  - Do NOT describe or suggest harmful methods.

Interaction style:
- Ask gentle follow-ups (“What happened?”, “How are you holding up right now?”).
- Never guilt-trip, shame, or argue about their feelings.
- Avoid toxic positivity; be realistic, kind, and grounded.
- If unsure, say so honestly while staying supportive.

Always keep the user’s emotional safety first.
Always be clear: you are an AI friend, not a substitute for professional care.
"""


def build_prompt(system_text: str,
                 history: List[Dict[str, str]],
                 user_message: str) -> str:
    """
    Convert system + history + user message into a single text prompt
    that we send to Gemini via generate_content().
    """
    lines: List[str] = []
    lines.append(system_text.strip())
    lines.append("")
    lines.append("Conversation so far:")

    # include last 10 exchanges max for context
    for item in history[-10:]:
        role = item.get("role", "user")
        speaker = "User" if role == "user" else "Companion"
        lines.append(f"{speaker}: {item.get('content', '')}")

    lines.append(f"User: {user_message}")
    lines.append("Companion:")

    return "\n".join(lines)


def generate_llm_reply(companion_name: str,
                       history: List[Dict[str, str]],
                       user_message: str) -> str:
    system_text = BASE_SYSTEM_PROMPT.format(companion_name=companion_name)
    prompt = build_prompt(system_text, history, user_message)

    try:
        # Gemini text generation call
        # Docs pattern: client.models.generate_content(model="gemini-2.5-flash", contents="...") :contentReference[oaicite:0]{index=0}
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        reply = (response.text or "").strip()
    except Exception:
        reply = (
            "I got a bit tangled while trying to respond, "
            "but I’m still here with you."
        )

    # Make sure the safety disclaimer is present
    if "I’m an AI friend" not in reply and "I'm an AI friend" not in reply:
        reply += (
            "\n\n(I’m an AI friend, not a therapist or doctor, "
            "but I’m really glad you’re talking to me.)"
        )

    return reply
