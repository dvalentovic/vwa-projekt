from database.database import open_connection
from services.auth import AuthService

def upsert_user(username: str, password: str, role: str):
    with open_connection() as c:
        auth = AuthService(c)
        pw_hash = auth.hash_password(password)

        existing = c.execute(
            "SELECT id FROM users WHERE username=?",
            (username,),
        ).fetchone()

        if existing:
            c.execute(
                "UPDATE users SET password_hash=?, role=? WHERE username=?",
                (pw_hash, role, username),
            )
            print("UPDATED", username, role)
        else:
            c.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
                (username, pw_hash, role),
            )
            print("CREATED", username, role)

        c.commit()

if __name__ == "__main__":
    upsert_user("coach", "coach123", "coach")
    upsert_user("player1", "player123", "player")
