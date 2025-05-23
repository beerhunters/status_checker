import os
from typing import List, Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from shared.models import Base, User, Site
from shared.config import settings
from shared.logger_setup import logger

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        logger.info("Initializing database schema...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")


async def run_db_operation(operation, *args, **kwargs):
    """Обертка для выполнения операций с БД с обработкой ошибок."""
    async with AsyncSessionFactory() as session:
        try:
            result = await operation(session, *args, **kwargs)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error during {operation.__name__}: {e}")
            await session.rollback()
            raise  # Перевыбрасываем ошибку для дальнейшей обработки
        except Exception as e:
            logger.error(f"Unexpected error during {operation.__name__}: {e}")
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
        await session.flush()  # Получаем ID до коммита
        await session.refresh(user)
    elif user.username != username:
        logger.debug(
            f"Updating username for {telegram_id}: {user.username} -> {username}"
        )
        user.username = username  # Обновляем username, если изменился
        await session.flush()
        await session.refresh(user)
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


async def _get_all_sites_with_users(session: AsyncSession) -> List[Site]:
    stmt = (
        select(Site).options(selectinload(Site.user)).order_by(Site.id)
    )  # Eager load users
    result = await session.execute(stmt)
    return result.scalars().unique().all()


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


async def _get_all_users_admin(session: AsyncSession) -> List[User]:
    stmt = (
        select(User).options(selectinload(User.sites)).order_by(User.id)
    )  # Eager load sites
    result = await session.execute(stmt)
    return result.scalars().unique().all()


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


# --- Public functions using the wrapper ---
async def get_or_create_user(telegram_id: int, username: Optional[str]) -> User:
    return await run_db_operation(_get_or_create_user, telegram_id, username)


async def add_site_to_user(telegram_id: int, url: str) -> Optional[Site]:
    return await run_db_operation(_add_site_to_user, telegram_id, url)


async def get_user_sites(telegram_id: int) -> List[Site]:
    return await run_db_operation(_get_user_sites, telegram_id)


async def get_all_sites_with_users() -> List[Site]:
    return await run_db_operation(_get_all_sites_with_users)


async def delete_site_by_id(site_id: int, telegram_id: int) -> bool:
    return await run_db_operation(_delete_site_by_id, site_id, telegram_id)


async def get_all_users_admin() -> List[User]:
    return await run_db_operation(_get_all_users_admin)


async def get_user_sites_admin(user_id: int) -> List[Site]:
    return await run_db_operation(_get_user_sites_admin, user_id)


async def delete_site_admin(site_id: int) -> Optional[int]:
    return await run_db_operation(_delete_site_admin, site_id)


async def get_user_by_id_admin(user_id: int) -> Optional[User]:
    return await run_db_operation(_get_user_by_id_admin, user_id)
