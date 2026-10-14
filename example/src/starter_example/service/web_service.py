"""Access request and response context from an injected business service."""

from typing import Any

from pythonboot import autowired, service
from pythonboot_web import RequestContextHolder
from starter_example.config.resources import ExampleProperties


@service
class WebService:
    settings: ExampleProperties = autowired()

    async def echo(self, item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        request = RequestContextHolder.get_request()
        response = RequestContextHolder.get_response()
        trace_id = request.headers.get("x-trace-id", "example-trace")
        RequestContextHolder.putData("trace_id", trace_id)
        response.status_code = 202
        response.set_header("X-Trace-Id", trace_id)
        response.set_cookie("starter-example", "active", httponly=True, samesite="Lax")
        return {
            "item_id": item_id,
            "application": self.settings.name,
            "path": dict(request.path_params),
            "query": dict(request.query_params),
            "trace_id": RequestContextHolder.getData("trace_id"),
            "body": await request.json(),
            "payload": payload,
        }
