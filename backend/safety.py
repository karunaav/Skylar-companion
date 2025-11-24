from typing import Tuple, Dict
import os
import json

from google import genai
from google.genai import types

# Gemini client – uses GEMINI_API_KEY from env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end it all", "no reason to live",
    "self harm", "self-harm", "cut myself", "hurt myself",
    "can't go on", "want to die", "life is pointless",
]


def is_crisis_text(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in CRISIS_KEYWORDS)


def crisis_safe_reply(user_name: str, companion_name: str) -> str:
    return (
        f"{user_name}, I’m really glad you told me this. "
        f"I’m {companion_name}, and I care about your safety.\n\n"
        "You deserve real, human support for how intense this feels.\n"
        "• If you can, reach out right now to someone you trust.\n"
        "• Consider contacting a local mental health professional.\n"
        "• If you feel close to acting on these thoughts, please contact your local "
        "emergency number or a crisis hotline immediately.\n\n"
        "You are not alone, and your pain is real. "
        "We can talk about what led you here, if you’d like."
        "\n\n_(I’m an AI companion, not a crisis line or clinician.)_"
    )


def moderate_text(text: str) -> Tuple[bool, Dict]:
    """
    Use Gemini as a lightweight moderation classifier.

    Returns:
        (is_flagged, categories_dict)

    categories_dict is a simple mapping like:
    {
        "self_harm": true/false,
        "violence": ...,
        "hate_speech": ...,
        ...
    }
    """
    prompt = f"""
You are a strict safety and content moderation classifier for a mental health
companion chat app.

Classify the following user message for safety concerns.

Return ONLY valid JSON with this exact structure:

{{
  "flagged": true or false,
  "categories": {{
    "self_harm": true or false,
    "violence": true or false,
    "hate_speech": true or false,
    "sexual_content": true or false,
    "illegal_activities": true or false,
    "other_dangerous_content": true or false
  }}
}}

Message:
\"\"\"{text}\"\"\"
"""

    try:
        # Use JSON mode so the response is machine-parsable
        # (Gemini JSON / structured output feature). :contentReference[oaicite:0]{index=0}
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )

        raw = resp.text or "{}"
        data = json.loads(raw)

        flagged = bool(data.get("flagged", False))
        categories = data.get("categories", {}) or {}

        # Ensure categories is a dict
        if not isinstance(categories, dict):
            categories = {}

        return flagged, categories

    except Exception:
        # If moderation is unavailable, fail soft:
        # rely on crisis keywords + Gemini's own built-in safety for generation. :contentReference[oaicite:1]{index=1}
        return False, {}
