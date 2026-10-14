"""Native ORM operations with explicit Session and transaction boundaries."""

from sqlalchemy import select

from pythonboot import autowired, service
from pythonboot_starter_sqlalchemy import AsyncSessionFactory, Page, PageQuery, apaginate
from starter_example.config.logging_aspect import logged
from starter_example.domain.common import UserNotFoundError
from starter_example.domain.user import User, UserView


@service
class UserService:
    session_factory: AsyncSessionFactory = autowired()

    @logged
    async def find_page(self, query: PageQuery, name: str | None = None) -> Page[UserView]:
        async with self.session_factory() as session:
            statement = select(User).order_by(User.id)
            if name is not None:
                statement = statement.where(User.name == name)
            return await apaginate(session, statement, query, mapper=UserView.model_validate)

    @logged
    async def list_users(self, name: str | None = None) -> list[UserView]:
        async with self.session_factory() as session:
            statement = select(User).order_by(User.id)
            if name is not None:
                statement = statement.where(User.name == name)
            users = (await session.scalars(statement)).all()
            return [UserView.model_validate(user) for user in users]

    @logged
    async def get_user(self, user_id: int) -> UserView:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise UserNotFoundError(f"User {user_id} not found")
            return UserView.model_validate(user)

    @logged
    async def create_user(self, name: str) -> UserView:
        async with self.session_factory() as session:
            user = User(name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return UserView.model_validate(user)

    @logged
    async def rename_user(self, user_id: int, name: str) -> UserView:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise UserNotFoundError(f"User {user_id} not found")
            user.name = name
            await session.commit()
            return UserView.model_validate(user)

    @logged
    async def delete_user(self, user_id: int) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                raise UserNotFoundError(f"User {user_id} not found")
            await session.delete(user)
            await session.commit()
            return True

    @logged
    async def rollback_demo(self) -> bool:
        async with self.session_factory() as session:
            user = User(name="rollback-demo")
            session.add(user)
            await session.flush()
            user_id = user.id
            await session.rollback()
            return await session.get(User, user_id) is None
