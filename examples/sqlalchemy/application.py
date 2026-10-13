"""Native ORM usage with explicit commits and application-scoped factory injection."""

from pathlib import Path

from fastapi import Path as PathParameter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pythonboot import autowired, service
from pythonboot_sqlalchemy import AsyncSessionFactory
from pythonboot_web import PythonBootApplication, controller, get, put, pythonboot_application


class Base(DeclarativeBase):
    """Application-owned ORM metadata."""


class User(Base):
    """User table managed by application migrations."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class UserView(BaseModel):
    """Materialized API representation independent of the Session lifetime."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(title="用户编号", description="用户唯一编号")
    name: str = Field(title="用户名称", description="用户显示名称")


class RenameUser(BaseModel):
    """Validated rename input."""

    name: str = Field(min_length=1, max_length=100, title="用户名称", description="新的用户显示名称")


@service
class UserService:
    """Create a Session per operation and commit changes explicitly."""

    session_factory: AsyncSessionFactory = autowired()

    async def list_users(self) -> list[UserView]:
        async with self.session_factory() as session:
            users = (await session.scalars(select(User).order_by(User.id))).all()
            return [UserView.model_validate(user) for user in users]

    async def rename_user(self, user_id: int, name: str) -> UserView | None:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                return None
            user.name = name
            await session.commit()
            return UserView.model_validate(user)


@controller(prefix="/users", tags=["用户管理"])
class UserController:
    """Expose native ORM service operations."""

    user_service: UserService = autowired()

    @get("", summary="查询用户列表", response_model=list[UserView])
    async def list_users(self) -> list[UserView]:
        return await self.user_service.list_users()

    @put("/{user_id}", summary="修改用户名称", response_model=UserView | None)
    async def rename_user(
        self,
        payload: RenameUser,
        user_id: int = PathParameter(title="用户编号", description="需要修改的用户编号", ge=1),
    ) -> UserView | None:
        return await self.user_service.rename_user(user_id, payload.name)


@pythonboot_application(scan_packages=("examples.sqlalchemy",))
class Application(PythonBootApplication):
    """Web application with installed SQLAlchemy entry-point auto-configuration."""


application = Application(config_dir=Path(__file__).parent / "config")
app = application.app
