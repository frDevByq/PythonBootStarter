"""Opt-in logical deletion and restoration with explicit transaction boundaries."""

from sqlalchemy import Boolean, String, false, select
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pythonboot_sqlalchemy import (
    AsyncSessionFactory, AsyncSoftDeleteSession, SoftDeleteMixin, SoftDeleteProperties,
)


class Base(DeclarativeBase):
    """Application-owned metadata; schema changes require application migrations."""


class Record(SoftDeleteMixin, Base):
    """Declare the configured deletion field in the application model."""

    __tablename__ = "example_soft_delete_record"
    __table_args__ = {"comment": "Example record"}

    id: Mapped[str] = mapped_column(String(32), primary_key=True, comment="Primary key")
    is_delete: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False, comment="Deletion flag",
    )


async def delete_record(factory: AsyncSessionFactory, record_id: str) -> None:
    """The configured Session converts deletion into an update during flush."""
    async with factory() as session:
        record = await session.get(Record, record_id)
        if record is not None:
            await session.delete(record)
            await session.commit()


async def restore_record(factory: AsyncSessionFactory, record_id: str) -> None:
    """An explicit include-deleted query allows restoration before committing."""
    async with factory() as session:
        statement = select(Record).where(Record.id == record_id).execution_options(include_deleted=True)
        record = await session.scalar(statement)
        if record is not None:
            record.is_delete = False
            await session.commit()


def create_example_factory(engine: AsyncEngine) -> AsyncSessionFactory:
    """Custom factories explicitly opt in, just like the default auto-configuration."""
    return AsyncSessionFactory(
        bind=engine, class_=AsyncSoftDeleteSession, expire_on_commit=False,
        soft_delete=SoftDeleteProperties(enabled=True),
    )
