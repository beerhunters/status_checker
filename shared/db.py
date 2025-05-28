# shared/db.py
from typing import List, Optional, Callable, TypeVar, Coroutine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, update, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from psycopg2.errors import UndefinedTable  # Импортируем для обработки ошибки
from shared.models import Base, User, Site, SystemSettings
from shared.config import settings
from shared.logger_setup import logger

logger.info("Creating async database engine...")
async_engine = create_async_engine(settings.database_url_async, echo=False)
AsyncSessionFactory = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)
logger.info("Async database engine and session factory created.")

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
    try:
        async with async_engine.begin() as conn:
            logger.info("Initializing database schema...")
            await conn.run_sync(Base.metadata.create_all)  # Create tables
            logger.info("Database schema initialized.")
        # Initialize default settings
        async with AsyncSessionFactory() as session:
            try:
                stmt = select(SystemSettings).filter(
                    SystemSettings.key == "check_interval_minutes"
                )
                result = await session.execute(stmt)
                if not result.scalars().first():
                    setting = SystemSettings(
                        key="check_interval_minutes",
                        value=str(settings.check_interval_minutes),
                    )
                    session.add(setting)
                    await session.commit()
                    logger.info(
                        f"Initialized default check_interval_minutes={settings.check_interval_minutes}."
                    )
                else:
                    logger.info(
                        "check_interval_minutes already exists in system_settings."
                    )
            except SQLAlchemyError as e:
                logger.error(
                    f"Database error initializing default settings: {e}", exc_info=True
                )
                await session.rollback()
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error initializing default settings: {e}",
                    exc_info=True,
                )
                await session.rollback()
                raise
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        raise


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


async def _get_user_by_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Fetches a user by telegram_id."""
    try:
        logger.debug(f"Querying user with telegram_id: {telegram_id}")
        stmt = select(User).filter(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        logger.debug(f"User query result: {'found' if user else 'not found'}")
        return user
    except Exception as e:
        logger.error(
            f"Error fetching user by telegram_id {telegram_id}: {e}", exc_info=True
        )
        return None


async def _get_all_telegram_ids(session: AsyncSession) -> List[int]:
    stmt = select(User.telegram_id)
    result = await session.execute(stmt)
    return [row for row in result.scalars().all()]


async def _get_system_setting(session: AsyncSession, key: str) -> Optional[int]:
    """Fetches a system setting by key."""
    try:
        stmt = select(SystemSettings).filter(SystemSettings.key == key)
        result = await session.execute(stmt)
        setting = result.scalars().first()
        return int(setting.value) if setting else None
    except Exception as e:
        logger.error(f"Error fetching system setting {key}: {e}", exc_info=True)
        return None


async def _update_site_status(
    session: AsyncSession, site_id: int, is_available: bool, user_id: int
) -> None:
    """Updates the status and last_checked timestamp of a site."""
    try:
        logger.debug(f"Updating status for site_id: {site_id}, user_id: {user_id}")
        await session.execute(
            update(Site)
            .where(Site.id == site_id, Site.user_id == user_id)
            .values(is_available=is_available, last_checked=func.now())
        )
        await session.flush()
        logger.debug(f"Site status updated for site_id: {site_id}")
    except Exception as e:
        logger.error(
            f"Error updating site status for site_id {site_id}: {e}", exc_info=True
        )
        raise


def get_system_setting_sync(key: str) -> Optional[int]:
    """Synchronously fetches a system setting by key."""
    try:
        with SyncSessionFactory() as session:
            logger.debug(f"Querying system_settings for key: {key}")
            stmt = select(SystemSettings).filter(SystemSettings.key == key)
            result = session.execute(stmt)
            setting = result.scalars().first()
            if setting:
                logger.debug(f"Found setting: key={setting.key}, value={setting.value}")
                try:
                    return int(setting.value)
                except ValueError as ve:
                    logger.error(
                        f"Invalid integer value for {key}: {setting.value}",
                        exc_info=True,
                    )
                    return None
            else:
                logger.warning(f"No setting found for key: {key}")
                return None
    except SQLAlchemyError as e:
        if isinstance(e.__cause__, UndefinedTable):
            logger.warning(
                f"Table 'system_settings' does not exist yet for key: {key}. Likely database not initialized."
            )
            return None
        logger.error(
            f"Error fetching system setting {key} synchronously: {e}", exc_info=True
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching system setting {key} synchronously: {e}",
            exc_info=True,
        )
        return None


async def _set_system_setting(session: AsyncSession, key: str, value: int) -> None:
    """Sets or updates a system setting."""
    try:
        stmt = select(SystemSettings).filter(SystemSettings.key == key)
        result = await session.execute(stmt)
        setting = result.scalars().first()
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSettings(key=key, value=str(value))
            session.add(setting)
        await session.flush()
    except Exception as e:
        logger.error(f"Error setting system setting {key}: {e}", exc_info=True)
        raise


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


async def get_user_by_id(telegram_id: int) -> Optional[User]:
    return await run_async_db_operation(_get_user_by_id, telegram_id)


async def get_all_telegram_ids() -> List[int]:
    return await run_async_db_operation(_get_all_telegram_ids)


async def get_system_setting(key: str) -> Optional[int]:
    return await run_async_db_operation(_get_system_setting, key)


async def update_site_status(
    session: AsyncSession, site_id: int, is_available: bool, user_id: int
) -> None:
    await run_async_db_operation(
        _update_site_status, site_id=site_id, is_available=is_available, user_id=user_id
    )


async def set_system_setting(key: str, value: int) -> None:
    await run_async_db_operation(_set_system_setting, key, value)
