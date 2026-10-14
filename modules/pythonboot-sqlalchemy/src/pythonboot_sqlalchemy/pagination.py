"""Validated pagination models and native synchronous/asynchronous query helpers."""

from collections.abc import Callable
from typing import Any, Generic, TypeVar, overload

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

T = TypeVar("T")
R = TypeVar("R")


class PageQuery(BaseModel):
    """One-based pagination request with a default page size of ten."""

    model_config = ConfigDict(validate_assignment=True)

    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1)


class Page(PageQuery, Generic[T]):
    """Materialized page containing the matching row count and current rows."""

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    total: int = Field(default=0, ge=0)
    rows: list[T] = Field(default_factory=list)


def _queries(statement: Select[Any], query: PageQuery) -> tuple[Select[Any], Select[Any]]:
    """Count the full selection and apply the requested window without mutating it."""
    if not isinstance(statement, Select):
        raise TypeError("Pagination requires a SQLAlchemy Select statement")
    if len(statement.column_descriptions) != 1:
        raise ValueError("Pagination requires exactly one selected entity or scalar column")
    unpaged = statement.limit(None).offset(None).fetch(None)
    count = select(func.count()).select_from(unpaged.order_by(None).subquery())
    rows = unpaged.offset((query.page - 1) * query.pageSize).limit(query.pageSize)
    return count, rows


@overload
def paginate(
    session: Session, statement: Select[tuple[T]], query: PageQuery | None = None,
    *, mapper: None = None,
) -> Page[T]: ...


@overload
def paginate(
    session: Session, statement: Select[tuple[T]], query: PageQuery | None = None,
    *, mapper: Callable[[T], R],
) -> Page[R]: ...


def paginate(
    session: Session, statement: Select[Any], query: PageQuery | None = None,
    *, mapper: Callable[[Any], Any] | None = None,
) -> Page[Any]:
    """Execute count and rows in the caller's Session without committing or closing it."""
    options = PageQuery.model_validate(query.model_dump() if query is not None else {})
    count, rows_query = _queries(statement, options)
    total = session.scalar(count)
    rows = session.scalars(rows_query).all()
    return Page(
        total=total, page=options.page, pageSize=options.pageSize,
        rows=[mapper(row) for row in rows] if mapper is not None else list(rows),
    )


@overload
async def apaginate(
    session: AsyncSession, statement: Select[tuple[T]], query: PageQuery | None = None,
    *, mapper: None = None,
) -> Page[T]: ...


@overload
async def apaginate(
    session: AsyncSession, statement: Select[tuple[T]], query: PageQuery | None = None,
    *, mapper: Callable[[T], R],
) -> Page[R]: ...


async def apaginate(
    session: AsyncSession, statement: Select[Any], query: PageQuery | None = None,
    *, mapper: Callable[[Any], Any] | None = None,
) -> Page[Any]:
    """Await count and rows in the caller's AsyncSession without transaction ownership."""
    options = PageQuery.model_validate(query.model_dump() if query is not None else {})
    count, rows_query = _queries(statement, options)
    total = await session.scalar(count)
    rows = (await session.scalars(rows_query)).all()
    return Page(
        total=total, page=options.page, pageSize=options.pageSize,
        rows=[mapper(row) for row in rows] if mapper is not None else list(rows),
    )
