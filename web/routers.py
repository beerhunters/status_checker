from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from shared.db import (
    AsyncSessionFactory,
    get_all_users_admin,
    get_user_by_id_admin,
    get_user_sites_admin,
    delete_site_admin,
    get_system_setting,
    set_system_setting,
)
from shared.models import User, Site
from shared.schemas import Site as SiteSchema
from shared.monitoring import check_website_async
from web.auth import login_required
import starlette.status as status
from sqlalchemy.future import select
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: str = Depends(login_required)):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User))
        user_count = len(result.scalars().all())
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "current_user": current_user, "user_count": user_count},
    )


@router.get("/users", response_class=HTMLResponse)
async def get_users_page(request: Request, user: str = Depends(login_required)):
    users = await get_all_users_admin()
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users}
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def get_user_page(
    request: Request, user_id: int, current_user: str = Depends(login_required)
):
    user = await get_user_by_id_admin(user_id)
    if not user:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": 404,
                "detail": "Пользователь не найден",
            },
        )
    sites = await get_user_sites_admin(user_id)
    return templates.TemplateResponse(
        "user_sites.html", {"request": request, "user": user, "sites": sites}
    )


@router.post("/sites/delete/{site_id}")
async def delete_site(site_id: int, current_user: str = Depends(login_required)):
    user_id = await delete_site_admin(site_id)
    if user_id:
        return RedirectResponse(
            url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
        )
    return templates.TemplateResponse(
        "error.html",
        {"request": Request, "status_code": 404, "detail": "Сайт не найден"},
    )


@router.post("/sites/{site_id}/refresh")
async def refresh_site(site_id: int, current_user: str = Depends(login_required)):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Site).filter(Site.id == site_id))
        site = result.scalars().first()
        if site:
            site.is_available = await check_website_async(site.url)
            await session.commit()
            return RedirectResponse(
                url=f"/users/{site.user_id}", status_code=status.HTTP_303_SEE_OTHER
            )
    return templates.TemplateResponse(
        "error.html",
        {"request": Request, "status_code": 404, "detail": "Сайт не найден"},
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, current_user: str = Depends(login_required)):
    check_interval = await get_system_setting("check_interval_minutes")
    check_interval_minutes = check_interval if check_interval else 5
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "check_interval_minutes": check_interval_minutes},
    )


@router.post("/settings", response_class=HTMLResponse)
async def update_settings(
    request: Request,
    check_interval_minutes: int = Form(...),
    current_user: str = Depends(login_required),
):
    try:
        await set_system_setting("check_interval_minutes", check_interval_minutes)
        message = f"Настройки успешно обновлены. Новый интервал ({check_interval_minutes} мин) будет применен в ближайшее время."
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "message": message,
                "check_interval_minutes": check_interval_minutes,
            },
        )
    except Exception as e:
        error = f"Ошибка при обновлении настроек: {str(e)}"
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "error": error,
                "check_interval_minutes": check_interval_minutes,
            },
        )


@router.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request, current_user: str = Depends(login_required)):
    return templates.TemplateResponse("broadcast.html", {"request": request})


@router.post("/broadcast", response_class=HTMLResponse)
async def broadcast_message(
    request: Request,
    broadcast_message: str = Form(...),
    current_user: str = Depends(login_required),
):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User.telegram_id))
        telegram_ids = [row for row in result.scalars().all()]
    for user_id in telegram_ids:
        await send_notification_async(user_id, broadcast_message)
    return templates.TemplateResponse(
        "broadcast.html",
        {"request": request, "message": "Сообщение отправлено всем пользователям"},
    )


@router.get("/api/users/{user_id}/sites", response_model=List[SiteSchema])
async def get_user_sites_api(user_id: int, current_user: str = Depends(login_required)):
    sites = await get_user_sites_admin(user_id)
    return sites
