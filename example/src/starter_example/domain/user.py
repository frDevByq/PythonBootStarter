"""Application-owned ORM schema and validated HTTP models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Metadata belongs to the application, not the Starter."""


class User(Base):
    __tablename__ = "starter_example_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UserInput(BaseModel):
    name: str = Field(min_length=1, max_length=100, title="用户名称", description="用户显示名称")


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(title="用户编号", description="用户唯一编号")
    name: str = Field(title="用户名称", description="用户显示名称")
    created_at: datetime = Field(title="创建时间", description="用户创建时间")
