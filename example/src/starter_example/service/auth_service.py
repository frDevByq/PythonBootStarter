"""Validate credentials in business code before asking the framework to log in."""

import hmac
from pythonboot import autowired, service
from pythonboot_starter_auth import AsyncAuthService, AuthService, NotLoginError
from starter_example.config.auth import ExampleAuthProperties
from starter_example.domain.auth import LoginInput, LoginView, SessionUser


def verify(payload: LoginInput, properties: ExampleAuthProperties) -> None:
    expected = properties.accounts.get(payload.username)
    if expected is None or not hmac.compare_digest(
        expected.get_secret_value().encode(), payload.password.get_secret_value().encode(),
    ):
        raise NotLoginError("invalid_credentials")


@service
class AuthExampleService:
    auth: AsyncAuthService = autowired()
    properties: ExampleAuthProperties = autowired()

    async def login(self, payload: LoginInput) -> LoginView:
        verify(payload, self.properties)
        result = await self.auth.login(payload.username, device=payload.device)
        session = await self.auth.get_session(result.token)
        await session.set("user", SessionUser(id=payload.username, nickname=payload.username))
        token_session = await self.auth.get_token_session(result.token)
        await token_session.set("device", payload.device)
        return LoginView(token=result.token, csrf_token=result.csrf_token, session=result.session)

    async def profile(self) -> SessionUser | None:
        session = await self.auth.get_session()
        return await session.get("user", target_type=SessionUser)

    async def rename(self, nickname: str) -> SessionUser:
        session = await self.auth.get_session()
        user = await session.get(
            "user", SessionUser(id=await self.auth.current_subject(), nickname=nickname),
            target_type=SessionUser,
        )
        user.nickname = nickname
        await session.set("user", user)
        return user


@service
class SyncAuthExampleService:
    auth: AuthService = autowired(name="exampleSyncAuthService")
    properties: ExampleAuthProperties = autowired()

    def login(self, payload: LoginInput) -> LoginView:
        verify(payload, self.properties)
        result = self.auth.login(payload.username, device=payload.device)
        self.auth.get_session(result.token).set("user", SessionUser(id=payload.username, nickname=payload.username))
        self.auth.get_token_session(result.token).set("device", payload.device)
        return LoginView(token=result.token, csrf_token=result.csrf_token, session=result.session)
