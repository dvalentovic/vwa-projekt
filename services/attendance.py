from __future__ import annotations
from typing import Dict, List, Any
from database.database import open_connection

class AttendanceService:
    def __init__(self, conn=None):
        # ak sa neodovzdá conn, otvoríme si ho sami
        self.conn = conn

    def _get_conn(self):
        # helper: buď používame self.conn, alebo otvoríme connection
        if self.conn is not None:
            return self.conn, None
        ctx = open_connection()
        return ctx.__enter__(), ctx

    def get_statuses_for_user(self, user_id: int) -> Dict[int, str]:
        conn, ctx = self._get_conn()
        try:
            cur = conn.execute(
                """
                SELECT event_id, status
                FROM attendance
                WHERE user_id = ?
                """,
                (user_id,),
            )
            return {row["event_id"]: row["status"] for row in cur.fetchall()}
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)

    def get_event_overview(self, event_id: int) -> Dict[str, List[str]]:
        """
        Pre konkrétny event vráti:
        {"yes":[...], "no":[...], "unknown":[...]}
        Unknown = hráči bez záznamu v attendance
        """
        conn, ctx = self._get_conn()
        try:
            cur = conn.execute(
                """
                SELECT
                    u.username,
                    COALESCE(a.status, 'unknown') AS status
                FROM users u
                LEFT JOIN attendance a
                  ON a.user_id = u.id AND a.event_id = ?
                WHERE u.role = 'player'
                ORDER BY u.username
                """,
                (event_id,),
            )

            out = {"yes": [], "unknown": [], "no": []}
            for row in cur.fetchall():
                out[row["status"]].append(row["username"])
            return out
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)

    def set_status(self, event_id: int, user_id: int, status: str) -> None:
        """
        Uloží (insert/replace) status dochádzky pre usera na event.
        status: "yes" | "unknown" | "no"
        """
        if status not in ("yes", "unknown", "no"):
            raise ValueError("Invalid status")

        conn, ctx = self._get_conn()
        try:
            # najjednoduchšie: SQLite "upsert" cez INSERT OR REPLACE
            conn.execute(
                """
                INSERT OR REPLACE INTO attendance (event_id, user_id, status)
                VALUES (?, ?, ?)
                """,
                (event_id, user_id, status),
            )
            conn.commit()
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)

    def list_events(self):
        conn, ctx = self._get_conn()
        try:
            return conn.execute(
                "SELECT id, event_type, date, time_from, time_to, location FROM events ORDER BY date DESC"
            ).fetchall()
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)

    def get_attendance_overview(self) -> Dict[int, Dict[str, List[str]]]:
        """
        Vráti pre každý event_id zoznam hráčov podľa statusu:
        { event_id: {"yes": [...], "unknown": [...], "no": [...]} }

        POZOR: musí zahŕňať aj hráčov bez záznamu (unknown),
        preto to robíme cez users LEFT JOIN attendance.
        """
        conn, ctx = self._get_conn()
        try:
            cur = conn.execute(
                """
                SELECT
                    e.id AS event_id,
                    u.username,
                    COALESCE(a.status, 'unknown') AS status
                FROM events e
                CROSS JOIN users u
                LEFT JOIN attendance a
                  ON a.event_id = e.id AND a.user_id = u.id
                WHERE u.role = 'player'
                ORDER BY e.id, u.username
                """
            )

            out: Dict[int, Dict[str, List[str]]] = {}
            for row in cur.fetchall():
                ev_id = row["event_id"]
                st = row["status"]
                name = row["username"]

                if ev_id not in out:
                    out[ev_id] = {"yes": [], "unknown": [], "no": []}

                out[ev_id][st].append(name)

            return out
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)
