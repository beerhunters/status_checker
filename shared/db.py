# shared/db.py
from typing import List, Optional, Callable, TypeVar, Coroutine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func  # Добавляем для COUNT

from shared.models import Base, User, Site
from shared.config import settings
from shared.logger_setup import logger

# --- Asynchronous Setup ---
logger.info("Creating async database engine...")
async_engine = create_async_engine(settings.database_url_async, echo=False)
AsyncSessionFactory = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)
logger.info("Async database engine and session factory created.")

# --- Synchronous Setup (for Celery) ---
logger.info("Creating sync database engine...")
sync_engine = create_engine(
    settings.database_url_sync,
    echo=False,
    pool_pre_ping=True,
)
SyncSessionFactory = sessionmaker(bind=sync_engine, expire_on_commit=False)
logger.info("Sync database engine and session factory created.")


async def init_db():
    """Инициализирует схему БД."""
    async with async_engine.begin() as conn:
        logger.info("Initializing database schema...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")


# --- Async Operations ---
T = TypeVar("T")


async def run_async_db_operation(
    operation: Callable[..., Coroutine[None, None, T]], *args, **kwargs
) -> T:
    """Обертка для выполнения асинхронных операций с БД."""
    async with AsyncSessionFactory() as session:
        try:
            result = await operation(session, *args, **kwargs)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error during async {operation.__name__}: {e}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during async {operation.__name__}: {e}")
            await session.rollback()
            raise


# --- Внутренние асинхронные функции ---
async def _get_or_create_user(
    session: AsyncSession, telegram_id: int, username: Optional[str]
) -> User:
    stmt = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        logger.info(f"Creating new user: {telegram_id} ({username})")
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
    elif user.username != username:
        logger.debug(
            f"Updating username for {telegram_id}: {user.username} -> {username}"
        )
        user.username = username
        await session.flush()
    return user


async def _add_site_to_user(
    session: AsyncSession, telegram_id: int, url: str
) -> Optional[Site]:
    user = await _get_or_create_user(session, telegram_id, None)
    stmt = select(Site).filter(Site.user_id == user.id, Site.url == url)
    result = await session.execute(stmt)
    if result.scalars().first():
        logger.warning(f"Site {url} already exists for user {telegram_id}")
        return None
    logger.info(f"Adding site {url} for user {telegram_id}")
    new_site = Site(url=url, user_id=user.id)
    session.add(new_site)
    await session.flush()
    return new_site


async def _get_user_sites(session: AsyncSession, telegram_id: int) -> List[Site]:
    stmt = (
        select(Site)
        .join(User)
        .filter(User.telegram_id == telegram_id)
        .order_by(Site.id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def _delete_site_by_id(
    session: AsyncSession, site_id: int, telegram_id: int
) -> bool:
    stmt = (
        select(Site)
        .join(User)
        .filter(Site.id == site_id, User.telegram_id == telegram_id)
    )
    result = await session.execute(stmt)
    site_to_delete = result.scalars().first()
    if site_to_delete:
        logger.info(f"Deleting site {site_id} for user {telegram_id}")
        await session.delete(site_to_delete)
        return True
    logger.warning(
        f"Attempted to delete non-existent site {site_id} for user {telegram_id}"
    )
    return False


async def _get_all_users_admin(session: AsyncSession) -> List[dict]:
    """Возвращает список всех пользователей с количеством их сайтов."""
    try:
        stmt = (
            select(
                User.id,
                User.telegram_id,
                User.username,
                func.count(Site.id).label("site_count"),
            )
            .outerjoin(Site, User.id == Site.user_id)
            .group_by(User.id, User.telegram_id, User.username)
            .order_by(User.id)
        )
        result = await session.execute(stmt)
        users = [
            {
                "id": row.id,
                "telegram_id": row.telegram_id,
                "username": row.username,
                "site_count": row.site_count,
            }
            for row in result
        ]
        logger.debug(f"Fetched {len(users)} users with site counts")
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}", exc_info=True)
        return []


async def _get_user_sites_admin(session: AsyncSession, user_id: int) -> List[Site]:
    stmt = select(Site).filter(Site.user_id == user_id).order_by(Site.id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def _delete_site_admin(session: AsyncSession, site_id: int) -> Optional[int]:
    stmt = select(Site).filter(Site.id == site_id)
    result = await session.execute(stmt)
    site_to_delete = result.scalars().first()
    if site_to_delete:
        user_id = site_to_delete.user_id
        logger.info(f"Admin deleting site {site_id} (User: {user_id})")
        await session.delete(site_to_delete)
        return user_id
    logger.warning(f"Admin attempted to delete non-existent site {site_id}")
    return None


async def _get_user_by_id_admin(session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).filter(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalars().first()


# --- Публичные асинхронные функции ---
async def get_or_create_user(telegram_id: int, username: Optional[str]) -> User:
    return await run_async_db_operation(_get_or_create_user, telegram_id, username)


async def add_site_to_user(telegram_id: int, url: str) -> Optional[Site]:
    return await run_async_db_operation(_add_site_to_user, telegram_id, url)


async def get_user_sites(telegram_id: int) -> List[Site]:
    return await run_async_db_operation(_get_user_sites, telegram_id)


async def delete_site_by_id(site_id: int, telegram_id: int) -> bool:
    return await run_async_db_operation(_delete_site_by_id, site_id, telegram_id)


async def get_all_users_admin() -> List[dict]:
    return await run_async_db_operation(_get_all_users_admin)


async def get_user_sites_admin(user_id: int) -> List[Site]:
    return await run_async_db_operation(_get_user_sites_admin, user_id)


async def delete_site_admin(site_id: int) -> Optional[int]:
    return await run_async_db_operation(_delete_site_admin, site_id)


async def get_user_by_id_admin(user_id: int) -> Optional[User]:
    return await run_async_db_operation(_get_user_by_id_admin, user_id)
