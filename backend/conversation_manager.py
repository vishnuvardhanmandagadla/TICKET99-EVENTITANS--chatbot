import time
from typing import Any

# In-memory session storage
_sessions: dict[str, dict[str, Any]] = {}

# Session expiry: 30 minutes
SESSION_TTL = 30 * 60


def get_or_create_session(session_id: str) -> dict[str, Any]:
    """Get existing session or create a new one."""
    now = time.time()
    if session_id not in _sessions:
        _sessions[session_id] = {
            "messages": [],
            "created_at": now,
            "last_active": now,
        }
    else:
        _sessions[session_id]["last_active"] = now
    return _sessions[session_id]


def add_message(session_id: str, role: str, content: str) -> None:
    """Add a message to the session history."""
    session = get_or_create_session(session_id)
    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": time.time(),
    })


def get_recent_history(session_id: str, max_messages: int = 6) -> list[dict[str, str]]:
    """Return last N messages as [{role, content}] for prompt assembly."""
    session = _sessions.get(session_id)
    if not session:
        return []
    messages = session["messages"][-max_messages:]
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def get_message_count(session_id: str, role: str = "user") -> int:
    """Count messages of a specific role in the session."""
    session = _sessions.get(session_id)
    if not session:
        return 0
    return sum(1 for m in session["messages"] if m["role"] == role)


def clear_session(session_id: str) -> None:
    """Remove a specific session."""
    _sessions.pop(session_id, None)


def cleanup_expired() -> int:
    """Remove sessions older than SESSION_TTL. Returns count of removed sessions."""
    now = time.time()
    expired = [
        sid for sid, data in _sessions.items()
        if now - data["last_active"] > SESSION_TTL
    ]
    for sid in expired:
        del _sessions[sid]
    return len(expired)
