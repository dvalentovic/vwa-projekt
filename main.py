# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pages.items import router as items_router  # ← DŮLEŽITÉ: přímý import modulu
from pages.dashboard import router as dashboard_router  # ← DŮLEŽITÉ: přímý import modulu
from pages.auth import router as auth_router
from pages.events import router as events_router
from pages.home import router as home_router
from pages.admin_users import router as admin_users_router
from pages.attendance import router as attendance_router
from pages.attendance_stats import router as attendance_stats_router
from dependencies import items_service, auth_service, get_current_user,events_service
from services.items import ItemsService
from services.auth import AuthService
from services.events import EventsService

def create_app() -> FastAPI:
    app = FastAPI(title="Mini FastAPI – Items")

    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.state.templates = Jinja2Templates(directory="templates")
    app.include_router(home_router, prefix="")
    app.include_router(items_router, prefix="/items", tags=["items"])
    app.include_router(auth_router, prefix="", tags=["auth"])
    app.include_router(events_router, prefix="/events", tags=["events"])
    app.include_router(admin_users_router)
    app.include_router(attendance_stats_router, prefix="/attendance/stats", tags=["attendance_stats"])
    # DEBUG: vypiš zaregistrované cesty
    print("=== ROUTES ===")
    for r in app.routes:
        try:
            print(getattr(r, "methods", ""), getattr(r, "path", ""))
        except Exception:
            pass

    # Pokud používáš override přes třídu, nech, jinak ho klidně vyhoď
    app.dependency_overrides[ItemsService] = items_service
    app.dependency_overrides[AuthService] = auth_service
    app.dependency_overrides[EventsService] = events_service

    app.add_middleware(SessionMiddleware, secret_key="dev-secret")

    app.state.templates.env.globals.update(get_user=lambda request: getattr(request.state, "user", None))

    @app.middleware("http")
    async def inject_user(request: Request, call_next):
        request.state.user = get_current_user(request)
        response = await call_next(request)
        return response

    return app

app = create_app()
