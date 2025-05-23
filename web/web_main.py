import os
from fastapi import FastAPI, Request, HTTPException, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi.security import HTTPBasicCredentials

from shared.logger_setup import logger
from web.routers import router as admin_router
from web.auth import AuthDependency, security, verify_basic_auth, create_jwt_token

app = FastAPI(title="Website Monitoring Admin")
templates = Jinja2Templates(directory="web/templates")


# --- Страница логина ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error},
    )


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    try:
        credentials = HTTPBasicCredentials(username=username, password=password)
        # Проверяем учетные данные через Basic Auth
        verify_basic_auth(credentials=credentials)
        # Создаем JWT-токен
        token = create_jwt_token({"sub": username})
        # Создаем ответ с перенаправлением и устанавливаем cookie
        response = RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=30 * 60,  # 30 минут
            secure=False,  # Установите True в продакшене с HTTPS
        )
        return response
    except HTTPException:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверное имя пользователя или пароль"},
            status_code=status.HTTP_200_OK,
        )


# --- Обработчики ошибок ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обрабатывает ошибки HTTP и показывает HTML страницу."""
    logger.error(f"HTTP Exception: Status={exc.status_code}, Detail={exc.detail}")
    if exc.status_code == 401:
        # Перенаправляем на страницу логина при ошибке 401
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
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


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Admin Panel Shutting Down...")
