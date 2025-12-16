# pages/home.py
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Request
from services.auth import User
from dependencies import get_current_user

router = APIRouter()

@router.get("/", name="home_ui")
async def home_ui(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": user},
    )
