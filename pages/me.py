from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from dependencies import attendance_service, get_current_user

router = APIRouter()

@router.get("/me")
def my_attendance_ui(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    svc = attendance_service()
    user_id = user["id"] if isinstance(user, dict) else user.id

    stats = svc.get_my_training_summary(user_id)   # ✅ toto berie user_id
    trainings = svc.get_my_trainings(user_id)      # ✅ toto berie user_id

    return request.app.state.templates.TemplateResponse(
        "my_attendance.html",
        {"request": request, "user": user, "stats": stats, "trainings": trainings},
    )
