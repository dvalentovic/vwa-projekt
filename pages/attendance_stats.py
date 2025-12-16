from fastapi import APIRouter, Request, Depends
from dependencies import attendance_service, get_current_user

router = APIRouter()

@router.get("/attendance/stats")
def attendance_stats_ui(
    request: Request,
    svc = Depends(attendance_service),
    current_user = Depends(get_current_user),
):
    if not current_user:
        # ak máš vlastný redirect/login mechanizmus, použi ten
        return request.app.state.templates.TemplateResponse(
            "login.html", {"request": request, "error": "Prihlás sa."}
        )

    stats = svc.get_user_stats(current_user["id"], only_past=True)

    return request.app.state.templates.TemplateResponse(
        "attendance_stats.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
        },
    )
