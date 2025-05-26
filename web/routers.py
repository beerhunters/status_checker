# # # # # web/routers.py
# # # # from fastapi import APIRouter, Request, Depends, HTTPException, status
# # # # from fastapi.responses import HTMLResponse, RedirectResponse
# # # # from fastapi.templating import Jinja2Templates
# # # #
# # # # from shared.db import (
# # # #     get_all_users_admin,
# # # #     get_user_sites_admin,
# # # #     delete_site_admin,
# # # #     get_user_by_id_admin,
# # # # )
# # # # from web.auth import login_required, get_current_user
# # # # from shared.logger_setup import logger
# # # #
# # # # router = APIRouter()
# # # # templates = Jinja2Templates(directory="web/templates")
# # # #
# # # #
# # # # @router.get("/", response_class=RedirectResponse)
# # # # async def root():
# # # #     """Перенаправляет с корня на страницу пользователей."""
# # # #     return RedirectResponse(url="/users")
# # # #
# # # #
# # # # @router.get("/users", response_class=HTMLResponse)
# # # # async def get_users_page(request: Request, user: str = Depends(login_required)):
# # # #     """Отображает страницу со списком пользователей."""
# # # #     request.state.user = user  # Передаем имя пользователя в шаблон
# # # #     users = await get_all_users_admin()
# # # #     return templates.TemplateResponse(
# # # #         "users.html", {"request": request, "users": users}
# # # #     )
# # # #
# # # #
# # # # @router.get("/users/{user_id}", response_class=HTMLResponse)
# # # # async def get_user_sites_page(
# # # #     request: Request, user_id: int, current_user: str = Depends(login_required)
# # # # ):
# # # #     """Отображает страницу с сайтами конкретного пользователя."""
# # # #     request.state.user = current_user
# # # #     user = await get_user_by_id_admin(user_id)
# # # #     if not user:
# # # #         raise HTTPException(status_code=404, detail="User not found")
# # # #     sites = await get_user_sites_admin(user_id)
# # # #     return templates.TemplateResponse(
# # # #         "user_sites.html", {"request": request, "sites": sites, "user": user}
# # # #     )
# # # #
# # # #
# # # # @router.post("/sites/delete/{site_id}")
# # # # async def delete_site(site_id: int, current_user: str = Depends(login_required)):
# # # #     """Удаляет сайт (только для админа)."""
# # # #     logger.info(f"Admin '{current_user}' attempting to delete site ID {site_id}")
# # # #     user_id = await delete_site_admin(site_id)
# # # #     if user_id is None:
# # # #         raise HTTPException(status_code=404, detail="Site not found or already deleted")
# # # #     # Перенаправляем обратно на страницу сайтов пользователя
# # # #     return RedirectResponse(
# # # #         url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
# # # #     )
# # # # web/routers.py
# # # from fastapi import APIRouter, Request, Depends, HTTPException, status
# # # from fastapi.responses import HTMLResponse, RedirectResponse
# # # from fastapi.templating import Jinja2Templates
# # # from shared.db import (
# # #     get_all_users_admin,
# # #     get_user_sites_admin,
# # #     delete_site_admin,
# # #     get_user_by_id_admin,
# # # )
# # # from web.auth import login_required, get_current_user
# # # from shared.logger_setup import logger
# # # from shared.models import Site  # Добавляем импорт модели Site
# # # from typing import List  # Для аннотации возвращаемого типа
# # #
# # # router = APIRouter()
# # # templates = Jinja2Templates(directory="web/templates")
# # #
# # #
# # # @router.get("/", response_class=RedirectResponse)
# # # async def root():
# # #     """Перенаправляет с корня на страницу пользователей."""
# # #     return RedirectResponse(url="/users")
# # #
# # #
# # # @router.get("/users", response_class=HTMLResponse)
# # # async def get_users_page(request: Request, user: str = Depends(login_required)):
# # #     """Отображает страницу со списком пользователей."""
# # #     request.state.user = user
# # #     users = await get_all_users_admin()
# # #     return templates.TemplateResponse(
# # #         "users.html", {"request": request, "users": users}
# # #     )
# # #
# # #
# # # @router.get("/users/{user_id}", response_class=HTMLResponse)
# # # async def get_user_sites_page(
# # #     request: Request, user_id: int, current_user: str = Depends(login_required)
# # # ):
# # #     """Отображает страницу с сайтами конкретного пользователя."""
# # #     request.state.user = current_user
# # #     user = await get_user_by_id_admin(user_id)
# # #     if not user:
# # #         raise HTTPException(status_code=404, detail="User not found")
# # #     sites = await get_user_sites_admin(user_id)
# # #     return templates.TemplateResponse(
# # #         "user_sites.html", {"request": request, "sites": sites, "user": user}
# # #     )
# # #
# # #
# # # @router.post("/sites/delete/{site_id}")
# # # async def delete_site(site_id: int, current_user: str = Depends(login_required)):
# # #     """Удаляет сайт (только для админа)."""
# # #     logger.info(f"Admin '{current_user}' attempting to delete site ID {site_id}")
# # #     user_id = await delete_site_admin(site_id)
# # #     if user_id is None:
# # #         raise HTTPException(status_code=404, detail="Site not found or already deleted")
# # #     return RedirectResponse(
# # #         url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
# # #     )
# # #
# # #
# # # # Новый маршрут для API
# # # @router.get("/api/users/{user_id}/sites", response_model=List[Site])
# # # async def get_user_sites_api(user_id: int, current_user: str = Depends(login_required)):
# # #     """Получает список сайтов пользователя в формате JSON."""
# # #     logger.info(f"Admin '{current_user}' requesting sites for user ID {user_id}")
# # #     user = await get_user_by_id_admin(user_id)
# # #     if not user:
# # #         raise HTTPException(status_code=404, detail="User not found")
# # #     sites = await get_user_sites_admin(user_id)
# # #     return sites
# # # web/routers.py
# # from fastapi import APIRouter, Request, Depends, HTTPException, status
# # from fastapi.responses import HTMLResponse, RedirectResponse
# # from fastapi.templating import Jinja2Templates
# # from shared.db import (
# #     get_all_users_admin,
# #     get_user_sites_admin,
# #     delete_site_admin,
# #     get_user_by_id_admin,
# # )
# # from web.auth import login_required, get_current_user
# # from shared.logger_setup import logger
# # from shared.schemas import Site  # Импортируем Pydantic-модель
# # from typing import List
# #
# # router = APIRouter()
# # templates = Jinja2Templates(directory="web/templates")
# #
# #
# # @router.get("/", response_class=RedirectResponse)
# # async def root():
# #     """Перенаправляет с корня на страницу пользователей."""
# #     return RedirectResponse(url="/users")
# #
# #
# # @router.get("/users", response_class=HTMLResponse)
# # async def get_users_page(request: Request, user: str = Depends(login_required)):
# #     """Отображает страницу со списком пользователей."""
# #     request.state.user = user
# #     users = await get_all_users_admin()
# #     return templates.TemplateResponse(
# #         "users.html", {"request": request, "users": users}
# #     )
# #
# #
# # @router.get("/users/{user_id}", response_class=HTMLResponse)
# # async def get_user_sites_page(
# #     request: Request, user_id: int, current_user: str = Depends(login_required)
# # ):
# #     """Отображает страницу с сайтами конкретного пользователя."""
# #     request.state.user = current_user
# #     user = await get_user_by_id_admin(user_id)
# #     if not user:
# #         raise HTTPException(status_code=404, detail="User not found")
# #     sites = await get_user_sites_admin(user_id)
# #     return templates.TemplateResponse(
# #         "user_sites.html", {"request": request, "sites": sites, "user": user}
# #     )
# #
# #
# # @router.post("/sites/delete/{site_id}")
# # async def delete_site(site_id: int, current_user: str = Depends(login_required)):
# #     """Удаляет сайт (только для админа)."""
# #     logger.info(f"Admin '{current_user}' attempting to delete site ID {site_id}")
# #     user_id = await delete_site_admin(site_id)
# #     if user_id is None:
# #         raise HTTPException(status_code=404, detail="Site not found or already deleted")
# #     return RedirectResponse(
# #         url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
# #     )
# #
# #
# # @router.get("/api/users/{user_id}/sites", response_model=List[Site])
# # async def get_user_sites_api(user_id: int, current_user: str = Depends(login_required)):
# #     """Получает список сайтов пользователя в формате JSON."""
# #     logger.info(f"Admin '{current_user}' requesting sites for user ID {user_id}")
# #     user = await get_user_by_id_admin(user_id)
# #     if not user:
# #         raise HTTPException(status_code=404, detail="User not found")
# #     sites = await get_user_sites_admin(user_id)
# #     return sites  # FastAPI автоматически преобразует SQLAlchemy-модели в Pydantic благодаря orm_mode
# # web/routers.py
# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
#
# from bot.monitoring import check_website_sync
# from shared.db import (
#     get_all_users_admin,
#     get_user_sites_admin,
#     delete_site_admin,
#     get_user_by_id_admin,
#     AsyncSessionFactory,
# )
# from web.auth import login_required, get_current_user
# from shared.logger_setup import logger
# from shared.models import Site
# from shared.schemas import Site as SiteSchema
# from typing import List
# from sqlalchemy.future import select
#
# from datetime import datetime, timezone
#
# router = APIRouter()
# templates = Jinja2Templates(directory="web/templates")
#
#
# @router.get("/", response_class=RedirectResponse)
# async def root():
#     """Перенаправляет с корня на страницу пользователей."""
#     return RedirectResponse(url="/users")
#
#
# @router.get("/users", response_class=HTMLResponse)
# async def get_users_page(request: Request, user: str = Depends(login_required)):
#     """Отображает страницу со списком пользователей."""
#     request.state.user = user
#     users = await get_all_users_admin()
#     return templates.TemplateResponse(
#         "users.html", {"request": request, "users": users}
#     )
#
#
# @router.get("/users/{user_id}", response_class=HTMLResponse)
# async def get_user_sites_page(
#     request: Request, user_id: int, current_user: str = Depends(login_required)
# ):
#     """Отображает страницу с сайтами конкретного пользователя."""
#     request.state.user = current_user
#     user = await get_user_by_id_admin(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     sites = await get_user_sites_admin(user_id)
#     return templates.TemplateResponse(
#         "user_sites.html", {"request": request, "sites": sites, "user": user}
#     )
#
#
# @router.post("/sites/delete/{site_id}")
# async def delete_site(site_id: int, current_user: str = Depends(login_required)):
#     """Удаляет сайт (только для админа)."""
#     logger.info(f"Admin '{current_user}' attempting to delete site ID {site_id}")
#     user_id = await delete_site_admin(site_id)
#     if user_id is None:
#         raise HTTPException(status_code=404, detail="Site not found or already deleted")
#     return RedirectResponse(
#         url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
#     )
#
#
# @router.post("/sites/{site_id}/refresh")
# async def refresh_site(site_id: int, current_user: str = Depends(login_required)):
#     """Обновляет статус сайта (только для админа)."""
#     logger.info(f"Admin '{current_user}' attempting to refresh site ID {site_id}")
#     async with AsyncSessionFactory() as session:
#         try:
#             # Получаем сайт
#             result = await session.execute(select(Site).where(Site.id == site_id))
#             site = result.scalars().first()
#             if not site:
#                 raise HTTPException(status_code=404, detail="Site not found")
#
#             # Проверяем доступность сайта
#             is_available = check_website_sync(site.url)
#
#             # Обновляем поля
#             site.is_available = is_available
#             site.last_checked = datetime.now(timezone.utc)
#
#             await session.commit()
#             logger.info(f"Site {site_id} refreshed: is_available={is_available}")
#
#             # Перенаправляем обратно на страницу сайтов пользователя
#             return RedirectResponse(
#                 url=f"/users/{site.user_id}", status_code=status.HTTP_303_SEE_OTHER
#             )
#         except Exception as e:
#             logger.error(f"Error refreshing site {site_id}: {e}", exc_info=True)
#             await session.rollback()
#             raise HTTPException(status_code=500, detail="Error refreshing site")
#
#
# @router.get("/api/users/{user_id}/sites", response_model=List[SiteSchema])
# async def get_user_sites_api(user_id: int, current_user: str = Depends(login_required)):
#     """Получает список сайтов пользователя в формате JSON."""
#     logger.info(f"Admin '{current_user}' requesting sites for user ID {user_id}")
#     user = await get_user_by_id_admin(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     sites = await get_user_sites_admin(user_id)
#     return sites
# web/routers.py
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from shared.db import (
    get_all_users_admin,
    get_user_sites_admin,
    delete_site_admin,
    get_user_by_id_admin,
    AsyncSessionFactory,
)
from web.auth import login_required, get_current_user
from shared.logger_setup import logger
from shared.models import Site
from shared.schemas import Site as SiteSchema
from typing import List
from sqlalchemy.future import select
from shared.utils import check_website_sync  # Import from shared.utils
from datetime import datetime, timezone

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")
# Add datetime filter for Jinja2
templates.env.filters["datetimeformat"] = lambda dt: (
    dt.strftime("%d.%m.%Y %H:%M") if dt else "Not set"
)


@router.get("/", response_class=RedirectResponse)
async def root():
    """Redirects from root to users page."""
    return RedirectResponse(url="/users")


@router.get("/users", response_class=HTMLResponse)
async def get_users_page(request: Request, user: str = Depends(login_required)):
    """Displays the list of users."""
    request.state.user = user
    users = await get_all_users_admin()
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users}
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def get_user_sites_page(
    request: Request, user_id: int, current_user: str = Depends(login_required)
):
    """Displays sites for a specific user."""
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
    """Deletes a site (admin only)."""
    logger.info(f"Admin '{current_user}' attempting to delete site ID {site_id}")
    user_id = await delete_site_admin(site_id)
    if user_id is None:
        raise HTTPException(status_code=404, detail="Site not found or already deleted")
    return RedirectResponse(
        url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/sites/{site_id}/refresh")
async def refresh_site(site_id: int, current_user: str = Depends(login_required)):
    """Refreshes a site's status (admin only)."""
    logger.info(f"Admin '{current_user}' attempting to refresh site ID {site_id}")
    async with AsyncSessionFactory() as session:
        try:
            result = await session.execute(select(Site).where(Site.id == site_id))
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


@router.get("/api/users/{user_id}/sites", response_model=List[SiteSchema])
async def get_user_sites_api(user_id: int, current_user: str = Depends(login_required)):
    """Gets a user's sites in JSON format."""
    logger.info(f"Admin '{current_user}' requesting sites for user ID {user_id}")
    user = await get_user_by_id_admin(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sites = await get_user_sites_admin(user_id)
    return sites
