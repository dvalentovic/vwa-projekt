# app/services/items.py
from typing import List, Dict, Any, Optional
import sqlite3
from repositories.items import list_items as repo_list_items, insert_item as repo_insert_item, total_price as repo_total_price

class ItemsService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_items(self) -> List[Dict[str, Any]]:
        return repo_list_items(self.conn)

    def total_price(self) -> float:
        return repo_total_price(self.conn)

    def create_item(self, name: str, price: float, description: Optional[str] = None) -> int:
        return repo_insert_item(self.conn, name=name, price=price, description=description)
