"""Native ORM operations with explicit Session and transaction boundaries."""

from sqlalchemy import select

from pythonboot import autowired, service
from pythonboot_starter_sqlalchemy import SessionFactory, Page, PageQuery, paginate
from starter_example.config.logging_aspect import logged
from starter_example.domain.common import UserNotFoundError
from starter_example.domain.user import User, UserView


@service
class SyncUserService:
    session_factory: SessionFactory = autowired(name="exampleSyncSessionFactory")

    @logged
    def find_page(self, query: PageQuery, name: str | None = None) -> Page[UserView]:
        with self.session_factory() as session:
            statement = select(User).order_by(User.id)
            if name is not None:
                statement = statement.where(User.name == name)
            return paginate(session, statement, query, mapper=UserView.model_validate)

    @logged
    def list_users(self, name: str | None = None) -> list[UserView]:
        with self.session_factory() as session:
            statement = select(User).order_by(User.id)
            if name is not None:
                statement = statement.where(User.name == name)
            users = (session.scalars(statement)).all()
            return [UserView.model_validate(user) for user in users]

    @logged
    def get_user(self, user_id: int) -> UserView:
        with self.session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                raise UserNotFoundError(f"User {user_id} not found")
            return UserView.model_validate(user)

    @logged
    def create_user(self, name: str) -> UserView:
        with self.session_factory() as session:
            user = User(name=name)
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserView.model_validate(user)

    @logged
    def rename_user(self, user_id: int, name: str) -> UserView:
        with self.session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                raise UserNotFoundError(f"User {user_id} not found")
            user.name = name
            session.commit()
            return UserView.model_validate(user)

    @logged
    def delete_user(self, user_id: int) -> bool:
        with self.session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                raise UserNotFoundError(f"User {user_id} not found")
            session.delete(user)
            session.commit()
            return True

    @logged
    def rollback_demo(self) -> bool:
        with self.session_factory() as session:
            user = User(name="rollback-demo")
            session.add(user)
            session.flush()
            user_id = user.id
            session.rollback()
            return session.get(User, user_id) is None
