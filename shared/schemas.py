# shared/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SiteBase(BaseModel):
    url: str
    is_available: bool
    last_checked: Optional[datetime] = None
    last_notified: Optional[datetime] = None


class Site(SiteBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True  # Включаем поддержку ORM для автоматического преобразования из SQLAlchemy
