from typing import Tuple, Dict
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    Use OpenAI's moderation endpoint to flag unsafe content.
    Returns (is_flagged, categories).
    """
    try:
        resp = client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
        result = resp.results[0]
        return bool(result.flagged), dict(result.categories)
    except Exception:
        # If moderation is unavailable, fail "soft":
        # rely on crisis keywords and system prompt.
        return False, {}
