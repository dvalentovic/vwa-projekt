from database.database import open_connection
from services.auth import AuthService

DDL = """
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL
);
"""

if __name__ == "__main__":
    with open_connection() as c:
        c.executescript(DDL)
        existing = c.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()["cnt"]
        if existing == 0:
            hash_ = AuthService(c).hash_password("admin123")
            c.execute(
                "INSERT INTO users(id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                (1, "admin", hash_, "admin"),
            )
        c.commit()
        print("DB initialized.")
