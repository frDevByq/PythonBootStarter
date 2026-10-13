"""Short names for native session factory classes, compatible with Bean injection."""

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

SessionFactory = sessionmaker
AsyncSessionFactory = async_sessionmaker

__all__ = ["SessionFactory", "AsyncSessionFactory"]
