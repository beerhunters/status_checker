# web/routers.py
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shared.db import (
    get_all_users_admin,
    get_user_sites_admin,
    delete_site_admin,
    get_user_by_id_admin,
)
from web.auth import login_required, get_current_user
from shared.logger_setup import logger

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/", response_class=RedirectResponse)
async def root():
    """Перенаправляет с корня на страницу пользователей."""
    return RedirectResponse(url="/users")


@router.get("/users", response_class=HTMLResponse)
async def get_users_page(request: Request, user: str = Depends(login_required)):
    """Отображает страницу со списком пользователей."""
    request.state.user = user  # Передаем имя пользователя в шаблон
    users = await get_all_users_admin()
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users}
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def get_user_sites_page(
    request: Request, user_id: int, current_user: str = Depends(login_required)
):
    """Отображает страницу с сайтами конкретного пользователя."""
    request.state.user = current_user
    user = await get_user_by_id_admin(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sites = await get_user_sites_admin(user_id)
    return templates.TemplateResponse(
        "user_sites.html", {"request": request, "sites": sites, "user": user}
    )


@router.post("/sites/delete/{site_id}")
async def delete_site(site_id: int, current_user: str = Depends(login_required)):
    """Удаляет сайт (только для админа)."""
    logger.info(f"Admin '{current_user}' attempting to delete site ID {site_id}")
    user_id = await delete_site_admin(site_id)
    if user_id is None:
        raise HTTPException(status_code=404, detail="Site not found or already deleted")
    # Перенаправляем обратно на страницу сайтов пользователя
    return RedirectResponse(
        url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
    )
