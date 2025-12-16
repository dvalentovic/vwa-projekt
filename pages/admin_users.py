# pages/admin_users.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from starlette import status as http_status

from dependencies import auth_service, require_admin
from services.auth import AuthService, User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", name="admin_users_ui")
async def admin_users_ui(
    request: Request,
    user: User = Depends(require_admin),
    svc: AuthService = Depends(auth_service),
):
    templates = request.app.state.templates
    users = svc.list_users()
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "user": user, "users": users, "error": None, "created": None},
    )


@router.post("/users/create", name="admin_users_create")
async def admin_users_create(
    request: Request,
    user: User = Depends(require_admin),
    svc: AuthService = Depends(auth_service),
    username: str = Form(...),
    role: str = Form("player"),
):
    temp_password, err = svc.create_user(username=username, role=role)

    templates = request.app.state.templates
    users = svc.list_users()
    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "error": err,
            "created": None if err else {"username": username, "temp_password": temp_password, "role": role},
        },
        status_code=http_status.HTTP_400_BAD_REQUEST if err else http_status.HTTP_200_OK,
    )
