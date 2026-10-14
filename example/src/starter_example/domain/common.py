"""Typed response envelope shared by all example endpoints."""

from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseCode(IntEnum):
    SUCCESS = 200
    FAILURE = 500


class BaseResult(BaseModel, Generic[T]):
    code: ResponseCode = Field(default=ResponseCode.SUCCESS, title="响应状态码", description="业务处理状态码")
    message: str = Field(default="操作成功", title="响应消息", description="业务处理结果")
    result: T | None = Field(default=None, title="响应数据", description="业务返回数据")

    @classmethod
    def success(cls, result: T | None = None) -> "BaseResult[T]":
        return cls(result=result)

    @classmethod
    def failure(cls, message: str) -> "BaseResult[T]":
        return cls(code=ResponseCode.FAILURE, message=message)


class UserNotFoundError(ValueError):
    """The requested user does not exist."""
