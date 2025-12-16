from database.database import open_connection
from services.auth import AuthService

DDL = """
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS announcements;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

PRAGMA foreign_keys = ON;

CREATE TABLE items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  price REAL NOT NULL
);

CREATE TABLE users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL
);

CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,   -- 'training' alebo 'match'
  date TEXT NOT NULL,         -- 'YYYY-MM-DD'
  time_from TEXT,             -- napr. '18:00'
  time_to TEXT,               -- napr. '19:30'
  location TEXT,
  note TEXT
);

CREATE TABLE attendance (
  event_id   INTEGER NOT NULL,
  user_id    INTEGER NOT NULL,
  status     TEXT NOT NULL,   -- 'yes', 'no', 'unknown'
  comment    TEXT,
  updated_at TEXT,
  PRIMARY KEY (event_id, user_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE
);

CREATE TABLE announcements (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id  INTEGER NOT NULL,
  title      TEXT NOT NULL,
  body       TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES users(id)
);
"""


if __name__ == "__main__":
    with open_connection() as c:
        # pre istotu aj tu
        c.execute("PRAGMA foreign_keys = ON;")
        c.executescript(DDL)

        # admin user, ak tam ešte nikto nie je
        row = c.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        if row["cnt"] == 0:
            auth = AuthService(c)
            hash_ = auth.hash_password("admin123")
            c.execute(
                """
                INSERT INTO users (id, username, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (1, "admin", hash_, "admin"),
            )

        c.commit()
        print("DB reset + initialized.")
