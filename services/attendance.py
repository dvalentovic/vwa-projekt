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

    def get_user_stats(self, user_id: int, only_past: bool = True) -> Dict[str, Any]:
        """
        Vráti štatistiku dochádzky hráča:
        total_events, going, not_going, maybe, no_response, percent_going
        """
        conn, ctx = self._get_conn()
        try:
            # 1) všetky eventy (voliteľne len minulé)
            if only_past:
                total_row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM events WHERE date(event_date) <= date('now')"
                ).fetchone()
            else:
                total_row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM events"
                ).fetchone()

            total_events = int(total_row["cnt"] or 0)

            # 2) rozdelenie podľa statusov pre usera
            # (uprav si názvy statusov podľa toho, čo ukladáš: napr. 'yes'/'no'/'maybe')
            if only_past:
                rows = conn.execute(
                    """
                    SELECT a.status, COUNT(*) AS cnt
                    FROM attendance a
                    JOIN events e ON e.id = a.event_id
                    WHERE a.user_id = ?
                      AND date(e.event_date) <= date('now')
                    GROUP BY a.status
                    """,
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT status, COUNT(*) AS cnt
                    FROM attendance
                    WHERE user_id = ?
                    GROUP BY status
                    """,
                    (user_id,),
                ).fetchall()

            by_status = {r["status"]: int(r["cnt"]) for r in rows}

            going = by_status.get("going", 0)  # alebo "yes"
            not_going = by_status.get("not_going", 0)  # alebo "no"
            maybe = by_status.get("maybe", 0)

            responded = going + not_going + maybe
            no_response = max(total_events - responded, 0)

            percent_going = 0
            if total_events > 0:
                percent_going = round((going / total_events) * 100, 1)

            return {
                "total_events": total_events,
                "going": going,
                "not_going": not_going,
                "maybe": maybe,
                "no_response": no_response,
                "percent_going": percent_going,
            }
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)

    def get_players_training_summary(self):
        conn, ctx = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT
                  u.id       AS user_id,
                  u.username AS username,

                  COUNT(e.id) AS trainings_total,

                  SUM(CASE WHEN a.status = 'yes' THEN 1 ELSE 0 END) AS yes_count,
                  SUM(CASE WHEN a.status = 'no' THEN 1 ELSE 0 END)  AS no_count,

                  -- unknown berieme ako "nezadané" (alebo si môžeš spraviť vlastný stĺpec)
                  SUM(CASE WHEN a.status = 'unknown' OR a.status IS NULL THEN 1 ELSE 0 END) AS missing_count

                FROM users u
                CROSS JOIN events e
                LEFT JOIN attendance a
                  ON a.user_id = u.id
                 AND a.event_id = e.id

                WHERE u.role = 'player'
                  AND e.event_type = 'training'

                GROUP BY u.id, u.username
                ORDER BY u.username;
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)

    def get_my_trainings_yes(self, user_id: int):
        conn, ctx = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT
                  e.id,
                  e.date,
                  e.time_from,
                  e.time_to,
                  e.location,
                  e.note,
                  a.status
                FROM events e
                JOIN attendance a
                  ON a.event_id = e.id
                 AND a.user_id = ?
                WHERE e.event_type = 'training'
                  AND a.status = 'yes'
                ORDER BY e.date DESC, e.time_from DESC;
                """,
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)
    def get_my_training_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Štatistika pre jedného hráča len pre tréningy:
        trainings_total, yes_count, no_count, missing_count
        """
        conn, ctx = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT
                  COUNT(e.id) AS trainings_total,
                  SUM(CASE WHEN a.status = 'yes' THEN 1 ELSE 0 END) AS yes_count,
                  SUM(CASE WHEN a.status = 'no' THEN 1 ELSE 0 END)  AS no_count,
                  SUM(CASE WHEN a.status = 'unknown' OR a.status IS NULL THEN 1 ELSE 0 END) AS missing_count
                FROM events e
                LEFT JOIN attendance a
                  ON a.event_id = e.id
                 AND a.user_id = ?
                WHERE e.event_type = 'training'
                """,
                (user_id,),
            ).fetchone()

            # row môže byť sqlite.Row
            return {
                "trainings_total": int(row["trainings_total"] or 0),
                "yes_count": int(row["yes_count"] or 0),
                "no_count": int(row["no_count"] or 0),
                "missing_count": int(row["missing_count"] or 0),
            }
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)

    def get_my_trainings(self, user_id: int):
        """
        Vráti všetky tréningy + môj status (yes/no/unknown).
        """
        conn, ctx = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT
                  e.id,
                  e.date,
                  e.time_from,
                  e.time_to,
                  e.location,
                  e.note,
                  COALESCE(a.status, 'unknown') AS status
                FROM events e
                LEFT JOIN attendance a
                  ON a.event_id = e.id
                 AND a.user_id = ?
                WHERE e.event_type = 'training'
                ORDER BY e.date DESC, e.time_from DESC;
                """,
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            if ctx is not None:
                ctx.__exit__(None, None, None)
