# web/auth.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional

from shared.config import settings
from shared.logger_setup import logger

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

# Настройки JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 день

# Контекст для паролей (используем только для сравнения, т.к. пароль хранится в конфиге)
# В реальном приложении пароли должны храниться в БД в виде хешей.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    # В нашем случае 'hashed_password' - это просто пароль из конфига.
    # Это НЕБЕЗОПАСНО для продакшена. Здесь это для простоты.
    return plain_password == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request) -> Optional[str]:
    """Проверяет JWT токен из куки и возвращает имя пользователя."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


async def login_required(request: Request):
    """Зависимость, требующая авторизации. Перенаправляет на /login, если не авторизован."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
        )
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Отображает страницу входа."""
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error}
    )


@router.post("/login")
async def login(
    response: Response, username: str = Form(...), password: str = Form(...)
):
    """Обрабатывает попытку входа."""
    if username == settings.admin_username and verify_password(
        password, settings.admin_password
    ):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        # Устанавливаем токен в куки
        response = RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=int(access_token_expires.total_seconds()),
        )
        logger.info(f"Admin user '{username}' logged in.")
        return response
    else:
        logger.warning(f"Failed login attempt for user '{username}'.")
        # Перенаправляем обратно на страницу входа с сообщением об ошибке
        return RedirectResponse(
            url="/login?error=Неверное имя пользователя или пароль",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.get("/logout")
async def logout(response: Response):
    """Выход из системы (удаление куки)."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    logger.info("Admin user logged out.")
    return response
