"""Validated CRUD endpoints backed by an injected ORM service."""

from fastapi import Body, Path, Query

from pythonboot_starter_sqlalchemy import Page, PageQuery
from pythonboot import autowired
from pythonboot_web import controller, delete, get, patch, post, put
from starter_example.domain.common import BaseResult
from starter_example.domain.user import UserInput, UserView
from starter_example.service.user_service import UserService


@controller(prefix="/users", tags=["异步用户管理"])
class UserController:
    user_service: UserService = autowired()

    @get("/page", summary="分页查询用户", response_model=BaseResult[Page[UserView]])
    async def find_page(
        self,
        page: int = Query(default=1, ge=1, title="页码", description="从 1 开始的页码"),
        pageSize: int = Query(default=10, ge=1, title="每页条数", description="每页返回的最大条数"),
        name: str | None = Query(default=None, title="用户名称", description="按名称筛选用户"),
    ) -> BaseResult[Page[UserView]]:
        return BaseResult.success(await self.user_service.find_page(PageQuery(page=page, pageSize=pageSize), name))

    @get("", summary="查询用户列表", response_model=BaseResult[list[UserView]])
    async def list_users(
        self,
        name: str | None = Query(default=None, title="用户名称", description="按名称筛选用户"),
    ) -> BaseResult[list[UserView]]:
        return BaseResult.success(await self.user_service.list_users(name))

    @get("/{user_id}", summary="查询用户详情", response_model=BaseResult[UserView])
    async def get_user(
        self,
        user_id: int = Path(ge=1, title="用户编号", description="用户唯一编号"),
    ) -> BaseResult[UserView]:
        return BaseResult.success(await self.user_service.get_user(user_id))

    @post("", summary="创建用户", response_model=BaseResult[UserView], status_code=201)
    async def create_user(
        self,
        payload: UserInput = Body(title="用户信息", description="需要创建的用户"),
    ) -> BaseResult[UserView]:
        return BaseResult.success(await self.user_service.create_user(payload.name))

    @put("/{user_id}", summary="更新用户", response_model=BaseResult[UserView])
    @patch("/{user_id}", summary="修改用户名称", response_model=BaseResult[UserView])
    async def rename_user(
        self,
        payload: UserInput = Body(title="用户信息", description="新的用户名称"),
        user_id: int = Path(ge=1, title="用户编号", description="需要修改的用户编号"),
    ) -> BaseResult[UserView]:
        return BaseResult.success(await self.user_service.rename_user(user_id, payload.name))

    @delete("/{user_id}", summary="删除用户", response_model=BaseResult[bool])
    async def delete_user(
        self,
        user_id: int = Path(ge=1, title="用户编号", description="需要删除的用户编号"),
    ) -> BaseResult[bool]:
        return BaseResult.success(await self.user_service.delete_user(user_id))

    @post("/rollback", summary="演示显式回滚", response_model=BaseResult[bool])
    async def rollback_demo(self) -> BaseResult[bool]:
        return BaseResult.success(await self.user_service.rollback_demo())
