"""Typed login and session DTOs contain no stored passwords."""

from pydantic import BaseModel, Field, SecretStr
from pythonboot_starter_auth import SessionInfo


class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=128, title="账号", description="本地演示账号 admin 或 reader")
    password: SecretStr = Field(title="密码", description="账号对应的本地演示密码")
    device: str = Field(default="browser", min_length=1, max_length=128, title="设备", description="登录设备标识")


class LoginView(BaseModel):
    token: str = Field(title="访问令牌", description="通过 Authorization Bearer 携带", repr=False)
    csrf_token: str = Field(title="CSRF 令牌", description="Cookie 模式下写操作需要携带此令牌", repr=False)
    session: SessionInfo = Field(title="会话", description="登录会话元数据")


class ProfileInput(BaseModel):
    nickname: str = Field(min_length=1, max_length=128, title="昵称", description="保存到账号 Session 的昵称")


class SessionUser(BaseModel):
    id: str = Field(title="账号", description="登录账号的唯一标识")
    nickname: str = Field(title="昵称", description="账号 Session 中保存的昵称")
