from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from starlette import status
from services.items import ItemsService
from services.auth import User
from dependencies import items_service, get_current_user, require_admin

router = APIRouter()


@router.get("/", name="items_ui")
async def items_ui(
    request: Request,
    svc: ItemsService = Depends(items_service),
    user: Optional[User] = Depends(get_current_user),
):
    items: List[Dict[str, Any]] = svc.list_items()
    total = svc.total_price()
    return request.app.state.templates.TemplateResponse(
        "items.html",
        {"request": request, "items": items, "total": total, "user": user},
    )

@router.get("/new", name="create_item_ui")
async def create_item_ui(
    request: Request,
    user: User = Depends(require_admin),
):
    return request.app.state.templates.TemplateResponse(
        "create_item.html",
        {
            "request": request,
            "form": {"name": "", "price": "", "description": ""},
            "user": user,
        },
    )

@router.post("/new", name="create_item_post")
async def create_item_post(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    description: Optional[str] = Form(None),
    svc: ItemsService = Depends(items_service),
    user: User = Depends(require_admin),
):
    # validation
    errors: Dict[str, str] = {}

    if not name or len(name.strip()) < 3:
        errors["name"] = "Název musí mít alespoň 3 znaky."

    if price <= 0:
        errors["price"] = "Cena musí být kladné číslo."

    if description and len(description) > 200:
        errors["description"] = "Popis nesmí být delší než 200 znaků."

    # in case of errors, re-render the form with error messages
    if errors:
        return request.app.state.templates.TemplateResponse(
            "create_item.html",
            {
                "request": request,
                "errors": errors,
                "form": {"name": name, "price": price, "description": description},
                "user": user,
            },
        )

    # if no errors, create the item
    svc.create_item(name=name.strip(), price=price, description=description)

    # in case of success, redirect to the items list to prevent sending the form again by reloading the page
    return RedirectResponse(url=request.url_for("items_ui"), status_code=status.HTTP_303_SEE_OTHER)
