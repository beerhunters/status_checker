# shared/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SiteBase(BaseModel):
    id: int
    url: str
    user_id: int
    is_available: bool
    last_checked: Optional[datetime] = None
    last_notified: Optional[datetime] = None


class Site(SiteBase):
    id: int
    user_id: int

    class Config:
        # orm_mode = True  # Включаем поддержку ORM для автоматического преобразования из SQLAlchemy
        from_attributes = True  # Updated from orm_mode
