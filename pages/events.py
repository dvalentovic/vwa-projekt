# pages/events.py
from __future__ import annotations

from typing import Optional, Dict

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette import status as http_status

from services.events import EventsService
from services.attendance import AttendanceService
from services.auth import User
from dependencies import (
    events_service,
    attendance_service,
    get_current_user,
    require_admin,
    require_coach_or_admin,
)

router = APIRouter()  # prefix /events je nastavený v main.py


@router.get("/events-debug")
async def events_debug() -> dict:
    return {"ok": True}


@router.get("/", name="events_ui")
async def events_ui(
    request: Request,
    svc: EventsService = Depends(events_service),
    att_svc: AttendanceService = Depends(attendance_service),
    user: Optional[User] = Depends(get_current_user),
):
    events = svc.list_events()

    # NEW: prehľad dochádzky pre všetkých (na každý event)
    attendance_overview = att_svc.get_attendance_overview()

    # tvoja dochádzka (pre zvýraznenie tlačidiel Idem/Neviem/Neprídem)
    user_statuses: Dict[int, str] = {}
    if user is not None:
        user_statuses = att_svc.get_statuses_for_user(user.id)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "events": events,
            "user": user,
            "user_statuses": user_statuses,
            "attendance_overview": attendance_overview,  # NEW
        },
    )



@router.get("/create", name="create_event_ui")
async def create_event_ui(
    request: Request,
    user: User = Depends(require_coach_or_admin),
):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "create_event.html",
        {
            "request": request,
            "errors": [],
            "form": {
                "event_type": "",
                "date": "",
                "time_from": "",
                "time_to": "",
                "location": "",
                "note": "",
            },
            "user": user,
        },
    )


@router.post("/create", name="create_event_submit")
async def create_event_submit(
    request: Request,
    svc: EventsService = Depends(events_service),
    user: User = Depends(require_coach_or_admin),
    event_type: str = Form(""),
    date: str = Form(""),
    time_from: str = Form(""),
    time_to: str = Form(""),
    location: str = Form(""),
    note: str = Form(""),
):
    errors: list[str] = []

    if not event_type.strip():
        errors.append("Typ udalosti je povinný (napr. training/match).")
    if not date.strip():
        errors.append("Dátum je povinný (YYYY-MM-DD).")

    if errors:
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "create_event.html",
            {
                "request": request,
                "errors": errors,
                "form": {
                    "event_type": event_type,
                    "date": date,
                    "time_from": time_from,
                    "time_to": time_to,
                    "location": location,
                    "note": note,
                },
                "user": user,
            },
        )

    svc.create_event(
        event_type=event_type.strip(),
        date=date.strip(),
        time_from=time_from or None,
        time_to=time_to or None,
        location=location or None,
        note=note or None,
    )

    return RedirectResponse(
        url=request.url_for("events_ui"),
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


# ---------- EDIT ----------


@router.get("/{event_id}/edit", name="edit_event_ui")
async def edit_event_ui(
    event_id: int,
    request: Request,
    svc: EventsService = Depends(events_service),
    user: User = Depends(require_coach_or_admin),
):
    event = svc.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Udalosť neexistuje")

    templates = request.app.state.templates
    form = {
        "event_type": event["event_type"],
        "date": event["date"],
        "time_from": event["time_from"] or "",
        "time_to": event["time_to"] or "",
        "location": event["location"] or "",
        "note": event["note"] or "",
    }
    return templates.TemplateResponse(
        "edit_event.html",
        {
            "request": request,
            "errors": [],
            "form": form,
            "user": user,
            "event_id": event_id,
        },
    )


@router.post("/{event_id}/edit", name="edit_event_submit")
async def edit_event_submit(
    event_id: int,
    request: Request,
    svc: EventsService = Depends(events_service),
    user: User = Depends(require_coach_or_admin),
    event_type: str = Form(""),
    date: str = Form(""),
    time_from: str = Form(""),
    time_to: str = Form(""),
    location: str = Form(""),
    note: str = Form(""),
):
    errors: list[str] = []

    if not event_type.strip():
        errors.append("Typ udalosti je povinný.")
    if not date.strip():
        errors.append("Dátum je povinný (YYYY-MM-DD).")

    if errors:
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "edit_event.html",
            {
                "request": request,
                "errors": errors,
                "form": {
                    "event_type": event_type,
                    "date": date,
                    "time_from": time_from,
                    "time_to": time_to,
                    "location": location,
                    "note": note,
                },
                "user": user,
                "event_id": event_id,
            },
        )

    svc.update_event(
        event_id=event_id,
        event_type=event_type.strip(),
        date=date.strip(),
        time_from=time_from or None,
        time_to=time_to or None,
        location=location or None,
        note=note or None,
    )

    return RedirectResponse(
        url=request.url_for("events_ui"),
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


# ---------- DELETE ----------


@router.post("/{event_id}/delete", name="delete_event_submit")
async def delete_event_submit(
    event_id: int,
    request: Request,
    svc: EventsService = Depends(events_service),
    user: User = Depends(require_coach_or_admin),
):
    svc.delete_event(event_id)
    return RedirectResponse(
        url=request.url_for("events_ui"),
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


# ---------- ATTENDANCE (DOCHÁDZKA) ----------


@router.post("/{event_id}/attendance", name="set_attendance")
async def set_attendance(
    event_id: int,
    request: Request,
    att_svc: AttendanceService = Depends(attendance_service),
    user: Optional[User] = Depends(get_current_user),
    status: str = Form(...),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Musíš byť prihlásený")

    if status not in ("yes", "no", "unknown"):
        raise HTTPException(status_code=400, detail="Neplatný status")

    att_svc.set_status(
        event_id=event_id,
        user_id=user.id,
        status=status,
    )

    return RedirectResponse(
        url=request.url_for("events_ui"),
        status_code=http_status.HTTP_303_SEE_OTHER,
    )
