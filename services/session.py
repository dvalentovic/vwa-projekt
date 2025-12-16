import secrets
from threading import Lock
from typing import Dict, Optional
from services.auth import User

SESSION_COOKIE_NAME = "session_id"


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, User] = {}
        self._lock = Lock()

    def create_session(self, user: User) -> str:
        session_id = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[session_id] = user
        return session_id

    def get_user(self, session_id: Optional[str]) -> Optional[User]:
        if not session_id:
            return None
        with self._lock:
            return self._sessions.get(session_id)

    def delete_session(self, session_id: Optional[str]) -> None:
        if not session_id:
            return
        with self._lock:
            self._sessions.pop(session_id, None)


session_store = SessionStore()

