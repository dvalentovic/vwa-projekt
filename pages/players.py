from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from dependencies import get_current_user, attendance_service

router = APIRouter()

@router.get("/players")
def players_attendance_ui(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # (voliteľné) len tréner/admin
    role = user["role"] if isinstance(user, dict) else user.role
    if role not in ("admin", "coach"):
        return RedirectResponse(url="/", status_code=302)

    svc = attendance_service()
    players = svc.get_players_training_summary()  # toto vracia zoznam hráčov so sumármi

    return request.app.state.templates.TemplateResponse(
        "players.html",
        {"request": request, "user": user, "players": players},
    )
