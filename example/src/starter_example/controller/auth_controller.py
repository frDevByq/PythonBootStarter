"""Async Redis-backed authentication and dynamic permission examples."""

from fastapi import Body, Path
from pythonboot import autowired
from pythonboot_starter_auth import AsyncAuthUtil, SessionInfo, require_login, require_permission, require_role
from pythonboot_web import controller, get, post, put
from starter_example.domain.auth import LoginInput, LoginView, ProfileInput, SessionUser
from starter_example.domain.common import BaseResult
from starter_example.service.auth_service import AuthExampleService


@controller(prefix="/auth", tags=["异步鉴权"])
class AuthController:
    service: AuthExampleService = autowired()

    @post("/login", summary="验证账号并登录", response_model=BaseResult[LoginView])
    async def login(self, payload: LoginInput = Body(title="登录信息", description="本地演示账号与密码")) -> BaseResult[LoginView]:
        return BaseResult.success(await self.service.login(payload))

    @post("/logout", summary="注销当前登录", response_model=BaseResult[bool])
    @require_login
    async def logout(self) -> BaseResult[bool]:
        await AsyncAuthUtil.logout()
        return BaseResult.success(True)

    @get("/me", summary="读取账号 Session 中的用户", response_model=BaseResult[SessionUser])
    @require_permission("example:read")
    async def me(self) -> BaseResult[SessionUser]:
        return BaseResult.success(await self.service.profile())

    @put("/me", summary="修改账号 Session 中的昵称", response_model=BaseResult[SessionUser])
    @require_permission("example:write")
    async def rename(self, payload: ProfileInput = Body(title="用户信息", description="新的昵称")) -> BaseResult[SessionUser]:
        return BaseResult.success(await self.service.rename(payload.nickname))

    @get("/either", summary="校验任一权限", response_model=BaseResult[bool])
    @require_permission("example:read", "example:write", mode="or")
    async def either(self) -> BaseResult[bool]:
        return BaseResult.success(True)

    @get("/device", summary="读取独立 Token Session", response_model=BaseResult[str])
    async def device(self) -> BaseResult[str]:
        session = await AsyncAuthUtil.get_token_session()
        return BaseResult.success(await session.get("device", ""))

    @post("/kickout/{login_id}", summary="管理员踢下线", response_model=BaseResult[int])
    @require_role("admin")
    @require_permission("admin:session:kickout")
    async def kickout(self, login_id: str = Path(title="账号", description="需要撤销全部登录的账号")) -> BaseResult[int]:
        return BaseResult.success(await AsyncAuthUtil.kickout(login_id))


@controller(prefix="/auth/sessions", tags=["登录会话"])
@require_login
class AuthSessionController:
    @get("", summary="查询当前账号的多端会话", response_model=BaseResult[list[SessionInfo]])
    async def sessions(self) -> BaseResult[list[SessionInfo]]:
        return BaseResult.success(await AsyncAuthUtil.list_sessions(await AsyncAuthUtil.current_subject()))
