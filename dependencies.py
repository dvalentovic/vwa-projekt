import sqlite3
from typing import Iterator, Optional
from fastapi import Depends, HTTPException, Request, status
from database.database import open_connection
from services.items import ItemsService
from services.events import EventsService
from services.auth import AuthService, User
from services.session import session_store, SESSION_COOKIE_NAME
from services.attendance import AttendanceService

def get_conn() -> Iterator[sqlite3.Connection]:
    with open_connection() as conn:
        yield conn

def items_service(conn: sqlite3.Connection = Depends(get_conn)) -> ItemsService:
    return ItemsService(conn)

def events_service(conn: sqlite3.Connection = Depends(get_conn)) -> EventsService:
    return EventsService(conn)

def auth_service(conn: sqlite3.Connection = Depends(get_conn)) -> AuthService:
    return AuthService(conn)

def attendance_service() -> AttendanceService:
    return AttendanceService()


def get_current_user(request: Request) -> Optional[User]:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    return session_store.get_user(session_id)

def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return user

def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
def require_coach_or_admin(user: User = Depends(require_user)) -> User:
    if user.role not in ("admin", "coach"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach/Admin access required")
    return user

