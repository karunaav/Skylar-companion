import os
from typing import List, Dict  # ✅ add this
from openai import OpenAI, RateLimitError, APIError

# OpenAI client (reads key from env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


def build_messages(system_text: str,
                   history: List[Dict[str, str]],
                   user_message: str) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = [{"role": "system", "content": system_text}]

    # include last 10 exchanges max for context
    for item in history[-10:]:
        role = "assistant" if item["role"] in ("bot", "assistant") else "user"
        msgs.append({"role": role, "content": item["content"]})

    msgs.append({"role": "user", "content": user_message})
    return msgs


def generate_llm_reply(companion_name: str,
                       history: List[Dict[str, str]],
                       user_message: str) -> str:
    system_text = BASE_SYSTEM_PROMPT.format(companion_name=companion_name)
    messages = build_messages(system_text, history, user_message)

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=320,
        )
        reply = completion.choices[0].message.content.strip()
    except RateLimitError:
        reply = (
            "Right now I can’t reach my main model because of usage limits 🥲 "
            "but I’m still here to listen."
        )
    except APIError:
        reply = (
            "I ran into a temporary issue talking to my model. "
            "Can we try again in a bit? 💛"
        )
    except Exception:
        reply = (
            "I got a bit tangled while trying to respond, "
            "but I’m still here with you."
        )

    if "I’m an AI friend" not in reply and "I'm an AI friend" not in reply:
        reply += (
            "\n\n(I’m an AI friend, not a therapist or doctor, "
            "but I’m really glad you’re talking to me.)"
        )

    return reply
