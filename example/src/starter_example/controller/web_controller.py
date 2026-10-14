"""Web routing, dependency bridging, date parsing, response context and standalone tasks."""

import asyncio
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic import BaseModel, Field

from pythonboot import ContextUtil, autowired
from pythonboot_web import RequestContextHolder, controller, date_time, get, inject, post, route
from starter_example.config.lifecycle import DemoSchema
from starter_example.config.resources import ExampleProperties
from starter_example.domain.common import BaseResult
from starter_example.service.web_service import WebService


class Schedule(BaseModel):
    at: Annotated[datetime, date_time("%Y/%m/%d %H:%M")] = Field(
        title="预约时间", description="格式为 YYYY/MM/DD HH:mm",
    )


@controller(prefix="/web", tags=["Web 示例"])
class WebController:
    web_service: WebService = autowired()
    schema: DemoSchema = autowired()

    @get("/health", summary="查询应用状态", response_model=BaseResult[dict[str, Any]])
    def health(self) -> BaseResult[dict[str, Any]]:
        return BaseResult.success({"ready": self.schema.ready, "native_lifespan": RequestContextHolder.get_request().app.state.native_ready, "starters": ["web", "sqlalchemy", "redis"]})

    @post("/echo/{item_id}", summary="演示请求与响应上下文", response_model=BaseResult[dict[str, Any]])
    async def echo(
        self,
        payload: dict[str, Any] = Body(title="请求内容", description="需要回显的 JSON 对象"),
        item_id: int = Path(ge=1, title="条目编号", description="需要回显的条目编号"),
        source: str = Query(default="http", title="来源", description="请求来源"),
    ) -> BaseResult[dict[str, Any]]:
        return BaseResult.success(await self.web_service.echo(item_id, payload))

    @get("/datetime", summary="演示查询时间格式", response_model=BaseResult[dict[str, datetime]])
    def datetime_query(
        self,
        at: Annotated[datetime, date_time("%Y/%m/%d"), Query(title="日期", description="格式为 YYYY/MM/DD")],
    ) -> BaseResult[dict[str, datetime]]:
        return BaseResult.success({"at": at})

    @post("/schedule", summary="演示请求体时间格式", response_model=BaseResult[Schedule])
    def schedule(
        self, payload: Annotated[Schedule, Body(title="预约信息", description="包含自定义格式的时间")],
    ) -> BaseResult[Schedule]:
        return BaseResult.success(payload)

    @get("/redirect", summary="跳转到 API 文档", response_model=BaseResult[None])
    def redirect(self) -> BaseResult[None]:
        RequestContextHolder.get_response().redirect("/docs")
        return BaseResult.success()

    @route("/methods", methods=("OPTIONS",), summary="演示自定义 HTTP 方法", response_model=BaseResult[list[str]])
    def methods(self) -> BaseResult[list[str]]:
        return BaseResult.success(["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

    @get("/task", summary="演示独立任务绑定容器", response_model=BaseResult[str])
    async def task(self) -> BaseResult[str]:
        context = ContextUtil.get_application_context()

        async def work() -> str:
            with ContextUtil.use(context):
                settings = await ContextUtil.aget_bean(ExampleProperties)
                return settings.name

        return BaseResult.success(await asyncio.create_task(work()))


router = APIRouter(prefix="/native", tags=["原生 FastAPI"])


@router.get("/info", summary="演示原生路由依赖桥接", response_model=BaseResult[str])
def native_info(settings: Annotated[ExampleProperties, Depends(inject(ExampleProperties))]) -> BaseResult[str]:
    return BaseResult.success(settings.name)
