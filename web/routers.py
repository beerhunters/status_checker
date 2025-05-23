from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError

from shared.db import (
    get_all_users_admin,
    get_user_sites_admin,
    delete_site_admin,
    get_user_by_id_admin,
)
from shared.logger_setup import logger
from web.web_main import AuthDependency  # Импортируем зависимость

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_redirect(request: Request, username: str = AuthDependency):
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)


@router.get("/users", response_class=HTMLResponse)
async def show_users(request: Request, username: str = AuthDependency):
    try:
        users_db = await get_all_users_admin()
        # Оптимизация: Используем данные, загруженные через selectinload
        users_with_count = [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "site_count": len(user.sites),  # N+1 ИЗБЕЖАЛИ!
            }
            for user in users_db
        ]
        return templates.TemplateResponse(
            "users.html", {"request": request, "users": users_with_count}
        )
    except SQLAlchemyError as e:
        logger.error(f"Admin: Failed to get users: {e}")
        raise HTTPException(
            status_code=500, detail="Database error while fetching users."
        )


@router.get("/users/{user_id}/sites", response_class=HTMLResponse)
async def show_user_sites(
    request: Request, user_id: int, username: str = AuthDependency
):
    try:
        user = await get_user_by_id_admin(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        sites = await get_user_sites_admin(
            user_id
        )  # Здесь N+1 не было, но запрос остается
        return templates.TemplateResponse(
            "user_sites.html",
            {"request": request, "sites": sites, "user_id": user_id, "user": user},
        )
    except SQLAlchemyError as e:
        logger.error(f"Admin: Failed to get sites for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Database error while fetching sites."
        )


@router.post("/sites/{site_id}/delete", response_class=HTMLResponse)
async def handle_delete_site(
    request: Request, site_id: int, username: str = AuthDependency
):
    try:
        user_id = await delete_site_admin(site_id)
        if user_id is None:
            raise HTTPException(status_code=404, detail="Site not found to delete.")

        redirect_url = f"/users/{user_id}/sites"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    except SQLAlchemyError as e:
        logger.error(f"Admin: Failed to delete site {site_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Database error while deleting site."
        )
