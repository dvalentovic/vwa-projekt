# app/repositories/items.py
from typing import List, Dict, Any, Optional
import sqlite3

def list_items(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, name, description, price FROM items ORDER BY id DESC"
    ).fetchall()
    return [dict(r) for r in rows]

def total_price(conn: sqlite3.Connection) -> float:
    row = conn.execute("SELECT SUM(price) AS total FROM items").fetchone()
    return row["total"] if row and row["total"] is not None else 0.0

def insert_item(
    conn: sqlite3.Connection,
    name: str,
    price: float,
    description: Optional[str] = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO items(name, description, price) VALUES (?, ?, ?)",
        (name, description, price),
    )
    conn.commit()
    return cur.lastrowid
