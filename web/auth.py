from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from shared.config import settings
from shared.logger_setup import logger
import secrets
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Секретный ключ для JWT (в продакшене должен быть безопасным и храниться в .env)
JWT_SECRET_KEY = (
    settings.jwt_secret_key
    if hasattr(settings, "jwt_secret_key")
    else "your-secret-key"
)
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

security = HTTPBasic()


def create_jwt_token(data: dict):
    """Создает JWT-токен с временем жизни."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request):
    """Проверяет JWT-токен из cookie."""
    token = request.cookies.get("access_token")
    if not token:
        logger.warning("No token found in cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Invalid token: no username in payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug(f"User {username} authenticated successfully via JWT")
        return username
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


AuthDependency = Depends(get_current_user)


def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверяет Basic Auth для формы логина."""
    logger.debug(f"Attempting login with username: {credentials.username}")
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
