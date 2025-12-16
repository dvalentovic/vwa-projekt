# app/services/events.py
from typing import List, Dict, Any, Optional
import sqlite3

from repositories.events import (
    list_events as repo_list_events,
    insert_event as repo_insert_event,
)


class EventsService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_events(self) -> List[Dict[str, Any]]:
        return repo_list_events(self.conn)

    def create_event(
        self,
        event_type: str,
        date: str,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        location: Optional[str] = None,
        note: Optional[str] = None,
    ) -> int:
        return repo_insert_event(
            self.conn,
            event_type=event_type,
            date=date,
            time_from=time_from,
            time_to=time_to,
            location=location,
            note=note,
        )

    def get_event(self, event_id: int):
        cur = self.conn.execute(
            """
            SELECT id, event_type, date, time_from, time_to, location, note
            FROM events
            WHERE id = ?
            """,
            (event_id,),
        )
        return cur.fetchone()

    def update_event(
            self,
            event_id: int,
            event_type: str,
            date: str,
            time_from: str | None,
            time_to: str | None,
            location: str | None,
            note: str | None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE events
            SET event_type = ?, date = ?, time_from = ?, time_to = ?, location = ?, note = ?
            WHERE id = ?
            """,
            (event_type, date, time_from, time_to, location, note, event_id),
        )
        self.conn.commit()

    def delete_event(self, event_id: int) -> None:
        self.conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.conn.commit()
