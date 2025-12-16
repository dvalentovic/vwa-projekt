import sqlite3
import secrets
from dataclasses import dataclass
from typing import Optional
from passlib.context import CryptContext
from repositories.users import get_user_by_username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class User:
    id: int
    username: str
    role: str


class AuthService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = get_user_by_username(self.conn, username)
        if not user:
            return None
        if not pwd_context.verify(password, user["password_hash"]):
            return None
        return User(id=user["id"], username=user["username"], role=user["role"])

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_user(self, username: str, role: str = "player", temp_password: str | None = None):
        username = username.strip()
        if not username:
            return None, "Username je povinný"

        cur = self.conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            return None, "Používateľ už existuje"

        if temp_password is None:
            temp_password = secrets.token_urlsafe(8)  # napr. dočasné heslo

        # tu použi rovnaké hashovanie ako pri authenticate()
        pw_hash = self.hash_password(temp_password)  # alebo tvoja existujúca funkcia
        self.conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, pw_hash, role),
        )
        self.conn.commit()

        return temp_password, None

    def list_users(self):
        cur = self.conn.execute("SELECT id, username, role FROM users ORDER BY username")
        return cur.fetchall()

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        row = self.conn.execute(
            "SELECT id, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if not row:
            raise ValueError("Používateľ neexistuje")

        if not pwd_context.verify(old_password, row["password_hash"]):
            raise ValueError("Staré heslo nie je správne")

        new_hash = pwd_context.hash(new_password)

        self.conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id),
        )
        self.conn.commit()