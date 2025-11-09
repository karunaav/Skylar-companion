# Simple in-memory session store for development.
# No Redis required.

import threading

_sessions_meta = {}
_sessions_history = {}
_lock = threading.Lock()


def save_session_meta(session_id: str, user_name: str, companion_name: str, style: str):
    with _lock:
        _sessions_meta[session_id] = {
            "user_name": user_name,
            "companion_name": companion_name,
            "style": style,
        }


def get_session_meta(session_id: str):
    with _lock:
        return _sessions_meta.get(session_id)


def append_history(session_id: str, role: str, content: str):
    with _lock:
        history = _sessions_history.setdefault(session_id, [])
        history.append({"role": role, "content": content})
        # keep only last 40 messages to avoid unbounded growth
        if len(history) > 40:
            del history[0 : len(history) - 40]


def get_history(session_id: str):
    with _lock:
        return list(_sessions_history.get(session_id, []))
