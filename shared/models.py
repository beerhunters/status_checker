# from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Boolean
# from sqlalchemy.orm import declarative_base, relationship
#
# Base = declarative_base()
#
#
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True)
#     telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
#     username = Column(String, nullable=True)
#     sites = relationship(
#         "Site", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
#     )
#
#
# class Site(Base):
#     __tablename__ = "sites"
#     id = Column(Integer, primary_key=True)
#     url = Column(String, nullable=False, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
#     is_available = Column(Boolean, default=True)  # Поле для статуса доступности
#     user = relationship("User", back_populates="sites", lazy="selectin")
#
#     __table_args__ = (
#         # Уникальность URL для каждого пользователя
#         # UniqueConstraint('user_id', 'url', name='_user_url_uc'),
#     )
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    ForeignKey,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    sites = relationship(
        "Site", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_available = Column(Boolean, default=True)
    last_notified = Column(DateTime, nullable=True)  # Время последнего уведомления
    user = relationship("User", back_populates="sites", lazy="selectin")
