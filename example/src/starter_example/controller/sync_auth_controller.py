"""Synchronous process-local authentication examples."""

from fastapi import Body
from pythonboot import autowired
from pythonboot_starter_auth import AuthUtil, require_permission
from pythonboot_web import controller, get, post
from starter_example.domain.auth import LoginInput, LoginView, SessionUser
from starter_example.domain.common import BaseResult
from starter_example.service.auth_service import SyncAuthExampleService


@controller(prefix="/sync/auth", tags=["同步鉴权"])
class SyncAuthController:
    service: SyncAuthExampleService = autowired()

    @post("/login", summary="同步验证账号并登录", response_model=BaseResult[LoginView])
    def login(self, payload: LoginInput = Body(title="登录信息", description="同步内存会话演示")) -> BaseResult[LoginView]:
        return BaseResult.success(self.service.login(payload))

    @get("/me", summary="同步读取账号 Session", response_model=BaseResult[SessionUser])
    @require_permission("example:read")
    def me(self) -> BaseResult[SessionUser]:
        return BaseResult.success(AuthUtil.get_session().get("user", target_type=SessionUser))

    @post("/logout", summary="同步注销当前登录", response_model=BaseResult[bool])
    def logout(self) -> BaseResult[bool]:
        AuthUtil.logout()
        return BaseResult.success(True)
