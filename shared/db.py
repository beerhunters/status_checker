import os
import logging
from typing import List, Optional
from sqlalchemy import create_engine, select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.config import settings
from shared.models import Base, User, Site, SystemSettings

logger = logging.getLogger("WebsiteMonitorBot")


def ensure_db_directory():
    db_dir = os.path.dirname(settings.db_name)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created database directory: {db_dir}")


async_engine = create_async_engine(settings.database_url_async, echo=False)
AsyncSessionFactory = async_sessionmaker(async_engine, expire_on_commit=False)
sync_engine = create_engine(settings.database_url_sync, echo=False)
SyncSessionFactory = sessionmaker(sync_engine, expire_on_commit=False)


async def init_db():
    ensure_db_directory()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def get_or_create_user(telegram_id: int, username: Optional[str]) -> User:
    async with AsyncSessionFactory() as session:
        stmt = select(User).filter(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if user is None:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def add_site_to_user(telegram_id: int, url: str) -> Optional[Site]:
    async with AsyncSessionFactory() as session:
        user = await get_or_create_user(telegram_id, None)
        stmt = select(Site).filter(Site.user_id == user.id, Site.url == url)
        result = await session.execute(stmt)
        if result.scalars().first():
            return None
        new_site = Site(url=url, user_id=user.id)
        session.add(new_site)
        await session.commit()
        await session.refresh(new_site)
        return new_site


async def get_user_sites(telegram_id: int) -> List[Site]:
    async with AsyncSessionFactory() as session:
        user = await get_or_create_user(telegram_id, None)
        stmt = select(Site).filter(Site.user_id == user.id).order_by(Site.id)
        result = await session.execute(stmt)
        return result.scalars().all()


async def delete_site_by_id(site_id: int, telegram_id: int) -> bool:
    async with AsyncSessionFactory() as session:
        user = await get_or_create_user(telegram_id, None)
        stmt = select(Site).filter(Site.id == site_id, Site.user_id == user.id)
        result = await session.execute(stmt)
        site = result.scalars().first()
        if site:
            await session.delete(site)
            await session.commit()
            return True
        return False


async def get_all_users_admin() -> List[dict]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User))
        users = [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "site_count": len(user.sites),
            }
            for user in result.scalars().all()
        ]
        return users


async def get_user_sites_admin(user_id: int) -> List[Site]:
    async with AsyncSessionFactory() as session:
        stmt = select(Site).filter(Site.user_id == user_id).order_by(Site.id)
        result = await session.execute(stmt)
        return result.scalars().all()


async def delete_site_admin(site_id: int) -> Optional[int]:
    async with AsyncSessionFactory() as session:
        stmt = select(Site).filter(Site.id == site_id)
        result = await session.execute(stmt)
        site = result.scalars().first()
        if site:
            user_id = site.user_id
            await session.delete(site)
            await session.commit()
            return user_id
        return None


async def get_user_by_id_admin(user_id: int) -> Optional[User]:
    async with AsyncSessionFactory() as session:
        stmt = select(User).filter(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()


async def get_user_by_id(telegram_id: int) -> Optional[User]:
    async with AsyncSessionFactory() as session:
        stmt = select(User).filter(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalars().first()


async def get_all_telegram_ids() -> List[int]:
    async with AsyncSessionFactory() as session:
        stmt = select(User.telegram_id)
        result = await session.execute(stmt)
        return [row for row in result.scalars().all()]


async def get_system_setting(key: str) -> Optional[int]:
    async with AsyncSessionFactory() as session:
        stmt = select(SystemSettings).filter(SystemSettings.key == key)
        result = await session.execute(stmt)
        setting = result.scalars().first()
        return int(setting.value) if setting else None


async def set_system_setting(key: str, value: int) -> None:
    async with AsyncSessionFactory() as session:
        stmt = select(SystemSettings).filter(SystemSettings.key == key)
        result = await session.execute(stmt)
        setting = result.scalars().first()
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSettings(key=key, value=str(value))
            session.add(setting)
        await session.commit()


def get_system_setting_sync(key: str) -> Optional[int]:
    with SyncSessionFactory() as session:
        stmt = select(SystemSettings).filter(SystemSettings.key == key)
        result = session.execute(stmt)
        setting = result.scalars().first()
        return int(setting.value) if setting else None
