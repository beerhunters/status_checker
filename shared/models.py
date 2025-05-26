# shared/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    ForeignKey,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func  # Для времени по умолчанию

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    sites = relationship(
        "Site", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    last_checked = Column(DateTime(timezone=True), onupdate=func.now())
    last_notified = Column(
        DateTime(timezone=True), nullable=True
    )  # Время последнего уведомления
    user = relationship("User", back_populates="sites", lazy="selectin")

    # Добавляем ограничение уникальности: один URL на одного пользователя
    __table_args__ = (UniqueConstraint("user_id", "url", name="_user_url_uc"),)

    def __repr__(self):
        return f"<Site(id={self.id}, url='{self.url}', user_id={self.user_id}, available={self.is_available})>"
