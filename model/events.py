from pydantic import BaseModel, Field
from typing import Optional


class EventBase(BaseModel):
    event_type: str = Field(..., description="training alebo match")
    date: str = Field(..., description="YYYY-MM-DD")
    time_from: Optional[str] = Field(None, description="HH:MM")
    time_to: Optional[str] = None
    location: Optional[str] = None
    note: Optional[str] = None


class EventCreate(EventBase):
    """Vstup od klienta pri vytváraní udalosti."""
    pass


class EventPublic(EventBase):
    """Výstup smerom von (vrátane id)."""
    id: int
