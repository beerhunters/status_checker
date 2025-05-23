import os
import secrets
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import SQLAlchemyError

from shared.config import settings
from shared.logger_setup import logger
from web.routers import router as admin_router

app = FastAPI(title="Website Monitoring Admin")
security = HTTPBasic()
templates = Jinja2Templates(directory="web/templates")


# --- Аутентификация ---
def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, settings.admin_username
    )
    correct_password = secrets.compare_digest(
        credentials.password, settings.admin_password
    )
    if not (correct_username and correct_password):
        logger.warning(f"Failed login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    logger.debug(f"User {credentials.username} authenticated successfully.")
    return credentials.username


# --- Зависимость (чтобы можно было импортировать в роутеры) ---
AuthDependency = Depends(get_current_user)


# --- Обработчики ошибок ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обрабатывает ошибки HTTP и показывает HTML страницу."""
    logger.error(f"HTTP Exception: Status={exc.status_code}, Detail={exc.detail}")
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Обрабатывает ошибки БД."""
    logger.critical(f"Unhandled SQLAlchemy Error: {exc}", exc_info=True)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": "Internal Server Error: Database issue.",
        },
        status_code=500,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обрабатывает все остальные ошибки."""
    logger.critical(f"Unhandled General Error: {exc}", exc_info=True)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": "An unexpected internal server error occurred.",
        },
        status_code=500,
    )


# --- Подключение роутера ---
app.include_router(admin_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Admin Panel Starting Up...")
    # Инициализацию БД лучше делать в боте или отдельном скрипте,
    # но можно и здесь, если веб-сервер стартует первым.
    # await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Admin Panel Shutting Down...")
