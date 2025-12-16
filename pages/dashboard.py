from fastapi import APIRouter, Depends, Request
from services.auth import User
from dependencies import get_current_user

router = APIRouter()


@router.get("/", name="dashboard_ui")
async def dashboard_ui(request: Request, user: User | None = Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user},
    )
