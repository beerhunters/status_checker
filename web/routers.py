from fastapi import APIRouter, Request, HTTPException, status, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from shared.db import (
    get_all_users_admin,
    get_user_sites_admin,
    delete_site_admin,
    get_user_by_id_admin,
    AsyncSessionFactory,
    get_system_setting,
    set_system_setting,
)
from web.auth import login_required, get_current_user
from shared.logger_setup import logger
from shared.models import Site, User
from shared.schemas import Site as SiteSchema
from typing import List
from sqlalchemy.future import select
from shared.utils import check_website_sync, send_notification_sync, publish_celery_task
from shared.config import settings
from datetime import datetime, timezone

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")
templates.env.filters["datetimeformat"] = lambda dt: (
    dt.strftime("%d.%m.%Y %H:%M") if dt else "Not set"
)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: str = Depends(login_required)):
    request.state.user = current_user
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User))
        user_count = len(result.scalars().all())
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "current_user": current_user, "user_count": user_count},
    )


@router.get("/users", response_class=HTMLResponse)
async def get_users_page(request: Request, user: str = Depends(login_required)):
    request.state.user = user
    users = await get_all_users_admin()
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users}
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def get_user_sites_page(
    request: Request, user_id: int, current_user: str = Depends(login_required)
):
    request.state.user = current_user
    user = await get_user_by_id_admin(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sites = await get_user_sites_admin(user_id)
    logger.debug(f"Sites for user {user_id}: {sites}")
    return templates.TemplateResponse(
        "user_sites.html", {"request": request, "sites": sites, "user": user}
    )


@router.post("/sites/delete/{site_id}")
async def delete_site(site_id: int, current_user: str = Depends(login_required)):
    logger.info(f"Admin '{current_user}' attempting to delete site ID {site_id}")
    user_id = await delete_site_admin(site_id)
    if user_id is None:
        raise HTTPException(status_code=404, detail="Site not found or already deleted")
    return RedirectResponse(
        url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/sites/{site_id}/refresh")
async def refresh_site(site_id: int, current_user: str = Depends(login_required)):
    logger.info(f"Admin '{current_user}' attempting to refresh site ID {site_id}")
    async with AsyncSessionFactory() as session:
        try:
            result = await session.execute(select(Site).filter(Site.id == site_id))
            site = result.scalars().first()
            if not site:
                raise HTTPException(status_code=404, detail="Site not found")
            is_available = check_website_sync(site.url)
            site.is_available = is_available
            site.last_checked = datetime.now(timezone.utc)
            await session.commit()
            logger.info(f"Site {site_id} refreshed: is_available={is_available}")
            return RedirectResponse(
                url=f"/users/{site.user_id}", status_code=status.HTTP_303_SEE_OTHER
            )
        except Exception as e:
            logger.error(f"Error refreshing site {site_id}: {e}", exc_info=True)
            await session.rollback()
            raise HTTPException(status_code=500, detail="Error refreshing site")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, current_user: str = Depends(login_required)):
    request.state.user = current_user
    check_interval = await get_system_setting("check_interval_minutes")
    check_interval_minutes = (
        check_interval
        if check_interval is not None
        else settings.check_interval_minutes
    )
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "check_interval_minutes": check_interval_minutes,
            "current_user": current_user,
        },
    )


@router.post("/settings")
async def update_settings(
    request: Request,
    check_interval_minutes: int = Form(...),
    current_user: str = Depends(login_required),
):
    try:
        if check_interval_minutes < 1:
            return templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "error": "Интервал проверки должен быть больше 0 минут.",
                    "check_interval_minutes": check_interval_minutes,
                    "current_user": current_user,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        await set_system_setting("check_interval_minutes", check_interval_minutes)
        logger.info(
            f"Updated check_interval_minutes to {check_interval_minutes} by {current_user}"
        )
        # Send task to update Celery Beat schedule
        success = publish_celery_task(
            "bot.celery_app.update_check_interval", [check_interval_minutes]
        )
        if success:
            logger.info(
                f"Sent task to update Celery Beat schedule to {check_interval_minutes} minutes"
            )
            message = f"Настройки успешно обновлены. Новый интервал ({check_interval_minutes} мин) применен."
        else:
            logger.warning(
                f"Failed to send task to update Celery Beat schedule to {check_interval_minutes} minutes"
            )
            message = f"Интервал ({check_interval_minutes} мин) сохранен в базе данных, но не удалось отправить задачу для обновления расписания. Попробуйте позже."
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "message": message,
                "check_interval_minutes": check_interval_minutes,
                "current_user": current_user,
            },
        )
    except Exception as e:
        logger.error(f"Error updating settings: {e}", exc_info=True)
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "error": f"Ошибка при обновлении настроек: {str(e)}",
                "check_interval_minutes": check_interval_minutes,
                "current_user": current_user,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request, current_user: str = Depends(login_required)):
    request.state.user = current_user
    return templates.TemplateResponse(
        "broadcast.html", {"request": request, "current_user": current_user}
    )


@router.post("/broadcast")
async def send_broadcast(
    request: Request,
    broadcast_message: str = Form(...),
    current_user: str = Depends(login_required),
):
    try:
        async with AsyncSessionFactory() as session:
            result = await session.execute(select(User.telegram_id))
            telegram_ids = [row for row in result.scalars().all()]
        if not telegram_ids:
            return templates.TemplateResponse(
                "broadcast.html",
                {
                    "request": request,
                    "error": "Нет пользователей для рассылки.",
                    "current_user": current_user,
                },
            )
        for telegram_id in telegram_ids:
            send_notification_sync(telegram_id, broadcast_message)
        logger.info(
            f"Sent broadcast message to {len(telegram_ids)} users by {current_user}"
        )
        return templates.TemplateResponse(
            "broadcast.html",
            {
                "request": request,
                "message": f"Сообщение отправлено {len(telegram_ids)} пользователям.",
                "current_user": current_user,
            },
        )
    except Exception as e:
        logger.error(f"Error sending broadcast: {e}", exc_info=True)
        return templates.TemplateResponse(
            "broadcast.html",
            {
                "request": request,
                "error": "Ошибка при отправке рассылки.",
                "current_user": current_user,
            },
        )


@router.get("/api/users/{user_id}/sites", response_model=List[SiteSchema])
async def get_user_sites_api(user_id: int, current_user: str = Depends(login_required)):
    logger.info(f"Admin '{current_user}' requesting sites for user ID {user_id}")
    user = await get_user_by_id_admin(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sites = await get_user_sites_admin(user_id)
    return sites
