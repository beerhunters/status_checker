from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text  # Импортируем text для SQL-запросов

from shared.db import (
    get_all_users_admin,
    get_user_sites_admin,
    delete_site_admin,
    get_user_by_id_admin,
    AsyncSessionFactory,
)
from shared.logger_setup import logger
from web.auth import AuthDependency
from shared.monitoring import update_site_availability

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_redirect(request: Request, username: str = AuthDependency):
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)


@router.get("/users", response_class=HTMLResponse)
async def show_users(request: Request, username: str = AuthDependency):
    try:
        users_db = await get_all_users_admin()
        users_with_count = [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "site_count": len(user.sites),
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
        sites = await get_user_sites_admin(user_id)
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


@router.post("/sites/{site_id}/refresh", response_class=HTMLResponse)
async def handle_refresh_site(
    request: Request, site_id: int, username: str = AuthDependency
):
    try:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                text(
                    "SELECT url, user_id FROM sites WHERE id = :site_id"
                ),  # Используем text()
                {"site_id": site_id},
            )
            site = result.first()
            if not site:
                raise HTTPException(status_code=404, detail="Site not found.")
            url, user_id = site
            await update_site_availability(session, site_id, url)
        redirect_url = f"/users/{user_id}/sites"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    except SQLAlchemyError as e:
        logger.error(f"Admin: Failed to refresh site {site_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Database error while refreshing site."
        )
