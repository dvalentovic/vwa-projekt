from pydantic import BaseModel, Field
from typing import Optional

class ItemCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    price: float = Field(..., gt=0)

class Item(ItemCreate):
    id: int
    class Config:
        from_attributes = True