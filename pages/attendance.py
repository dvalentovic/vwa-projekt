from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from starlette import status
from dependencies import attendance_service, events_service, require_coach_or_admin

router = APIRouter()

@router.get("/attendance", name="attendance_overview_ui")
async def attendance_overview_ui(
    request: Request,
    event_id: int | None = None,
    _user = Depends(require_coach_or_admin),
    att = Depends(attendance_service),
    ev  = Depends(events_service),
):
    tpl = request.app.state.templates
    events = ev.list_events()

    if not events:
        return tpl.TemplateResponse("attendance_overview.html", {
            "request": request, "events": [], "selected_event": None, "overview": None
        })

    if event_id is None:
        event_id = events[0]["id"]

    selected_event = next((x for x in events if x["id"] == event_id), events[0])
    overview = att.get_event_overview(event_id)

    return tpl.TemplateResponse("attendance_overview.html", {
        "request": request,
        "events": events,
        "selected_event": selected_event,
        "overview": overview,
    })
