from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from starlette import status
from dependencies import auth_service
from services.auth import AuthService
from services.session import SESSION_COOKIE_NAME, session_store

router = APIRouter()


@router.get("/login", name="login_ui")
async def login_ui(request: Request):
    return request.app.state.templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@router.post("/login", name="login_post")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    svc: AuthService = Depends(auth_service),
):
    user = svc.authenticate(username, password)
    if not user:
        return request.app.state.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    session_id = session_store.create_session(user)
    response = RedirectResponse(
        url=request.query_params.get("next") or request.url_for("home_ui"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True)
    return response


@router.post("/logout", name="logout")
async def logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session_store.delete_session(session_id)
    response = RedirectResponse(
        url=request.url_for("home_ui"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response

@router.get("/change-password", name="change_password_ui")
async def change_password_ui(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url=request.url_for("login_ui"), status_code=status.HTTP_303_SEE_OTHER)

    return request.app.state.templates.TemplateResponse(
        "change_password.html",
        {"request": request, "error": None, "success": None},
    )

@router.post("/change-password", name="change_password_ui")
async def change_password_submit(
    request: Request,
    svc: AuthService = Depends(auth_service),
):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url=request.url_for("login_ui"), status_code=status.HTTP_303_SEE_OTHER)

    form = await request.form()
    old_password = (form.get("old_password") or "").strip()
    new_password = (form.get("new_password") or "").strip()
    new_password2 = (form.get("new_password2") or "").strip()

    if new_password != new_password2:
        return request.app.state.templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": "Nové heslá sa nezhodujú.", "success": None},
        )

    try:
        svc.change_password(user_id=user.id, old_password=old_password, new_password=new_password)
        return request.app.state.templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": None, "success": "Heslo bolo zmenené ✅"},
        )
    except ValueError as e:
        return request.app.state.templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": str(e), "success": None},
        )

