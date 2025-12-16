# app/repositories/events.py
from typing import List, Dict, Any, Optional
import sqlite3


def list_events(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, event_type, date, time_from, time_to, location, note
        FROM events
        ORDER BY date ASC, time_from ASC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def insert_event(
    conn: sqlite3.Connection,
    event_type: str,
    date: str,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    location: Optional[str] = None,
    note: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO events(event_type, date, time_from, time_to, location, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (event_type, date, time_from, time_to, location, note),
    )
    conn.commit()
    return cur.lastrowid
