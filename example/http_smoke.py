"""Verify the running example over real HTTP, PostgreSQL and Redis connections."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

BASE_URL = os.environ.get("EXAMPLE_HTTP_URL", "http://127.0.0.1:18000")
checks = 0


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call(method, path, payload=None, status=200, headers=None, envelope=True):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        BASE_URL + path, data=body, method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        response = build_opener(NoRedirect).open(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        assert response.code == status, (method, path, response.code, raw.decode())
        data = json.loads(raw) if raw and "application/json" in response.headers.get("Content-Type", "") else raw.decode()
        if envelope:
            expected_code = 200 if status < 400 else 500
            assert data["code"] == expected_code, data
            if expected_code == 200:
                assert data["message"] == "操作成功", data
        return data, {key.lower(): value for key, value in response.headers.items()}


def verify(label, work):
    global checks
    work()
    checks += 1
    print(f"PASS {label}", flush=True)


def orm(prefix, other):
    user_id = None
    name = f"http-smoke-{uuid4().hex}"
    try:
        data, _ = call("POST", prefix, {"name": name}, 201)
        user_id = data["result"]["id"]
        assert data["result"]["name"] == name
        assert "T" not in data["result"]["created_at"]
        data, _ = call("GET", f"{other}/{user_id}")
        assert data["result"]["name"] == name
        data, _ = call("GET", prefix + "?" + urlencode({"name": name}))
        assert [item["id"] for item in data["result"]] == [user_id]
        data, _ = call("GET", prefix + "/page?" + urlencode({"name": name}))
        assert data["result"]["total"] == 1
        assert data["result"]["page"] == 1 and data["result"]["pageSize"] == 10
        assert [item["id"] for item in data["result"]["rows"]] == [user_id]
        data, _ = call("GET", prefix + "/page?" + urlencode({"name": name, "page": 2, "pageSize": 1}))
        assert data["result"] == {"page": 2, "pageSize": 1, "total": 1, "rows": []}
        data, _ = call("GET", prefix + "/page?" + urlencode({"name": name + "-missing"}))
        assert data["result"]["total"] == 0 and data["result"]["rows"] == []
        call("GET", prefix + "/page?page=0", status=422)
        call("GET", prefix + "/page?pageSize=0", status=422)
        for method in ("PUT", "PATCH"):
            data, _ = call(method, f"{prefix}/{user_id}", {"name": name + method})
            assert data["result"]["name"] == name + method
        data, _ = call("POST", prefix + "/rollback")
        assert data["result"] is True
        call("DELETE", f"{prefix}/{user_id}")
        call("GET", f"{prefix}/{user_id}", status=404)
        user_id = None
        call("POST", prefix, {"name": ""}, 422)
        call("GET", prefix + "/0", status=422)
    finally:
        if user_id is not None:
            call("DELETE", f"{prefix}/{user_id}")



def pagination(prefix):
    user_ids = []
    name = f"pagination-smoke-{uuid4().hex}"
    try:
        for _ in range(5):
            data, _ = call("POST", prefix, {"name": name}, 201)
            user_ids.append(data["result"]["id"])
        data, _ = call("GET", prefix + "/page?" + urlencode({"name": name}))
        result = data["result"]
        assert set(result) == {"total", "page", "pageSize", "rows"}
        assert result["total"] == 5 and result["page"] == 1 and result["pageSize"] == 10
        assert [row["id"] for row in result["rows"]] == user_ids
        for page in (1, 2, 3, 4):
            data, _ = call("GET", prefix + "/page?" + urlencode({"name": name, "page": page, "pageSize": 2}))
            result = data["result"]
            assert result["total"] == 5 and result["page"] == page and result["pageSize"] == 2
            assert [row["id"] for row in result["rows"]] == user_ids[(page - 1) * 2:page * 2]
            assert all(row["name"] == name for row in result["rows"])
        for query in ({"page": -1}, {"pageSize": -1}, {"page": "invalid"}, {"pageSize": "invalid"}):
            call("GET", prefix + "/page?" + urlencode(query), status=422)
    finally:
        for user_id in user_ids:
            call("DELETE", f"{prefix}/{user_id}")


def redis(path):
    data, _ = call("POST", path)
    values = data["result"]
    expected = {
        "native_ping": True, "named_client": True, "set": True, "get": "hello",
        "exists": 1, "expire": True, "incr": 3, "decr": 2,
        "hset": 2, "hget": "Alice", "hgetall": {"name": "Alice", "role": "reader"}, "hdel": 1,
        "lpush": 1, "rpush": 2, "lrange": ["first", "last"], "lpop": "first", "rpop": "last",
        "sadd": 2, "smembers": ["a", "b"], "srem": 1,
        "zadd": 2, "zrange": ["low", "high"], "zrem": 1,
        "acquire_lock": True, "lock_owned": True, "extend_lock": True,
        "released_lock_owned": False, "delete": 5, "remaining_keys": 0,
    }
    for name, value in expected.items():
        assert values[name] == value, (path, name, values[name], value)
    assert 0 < values["ttl"] <= 120


def web():
    data, health_headers = call("GET", "/web/health")
    assert health_headers["x-application"] == "pythonboot-starter-example"
    assert data["result"] == {"ready": True, "native_lifespan": True, "starters": ["web", "sqlalchemy", "redis"]}
    data, _ = call("GET", "/native/info")
    assert data["result"] == "PythonBoot Starter Local Example"
    data, _ = call("GET", "/web/task")
    assert data["result"] == "PythonBoot Starter Local Example"
    data, headers = call("POST", "/web/echo/7?source=smoke", {"message": "hello"}, 202, {"X-Trace-Id": "smoke"})
    assert data["result"]["path"] == {"item_id": "7"}
    assert data["result"]["query"] == {"source": "smoke"}
    assert data["result"]["body"] == data["result"]["payload"] == {"message": "hello"}
    assert data["result"]["trace_id"] == "smoke"
    assert headers["x-trace-id"] == "smoke"
    assert "starter-example=active" in headers["set-cookie"] and "HttpOnly" in headers["set-cookie"]
    data, _ = call("GET", "/web/datetime?" + urlencode({"at": "2026/10/14"}))
    assert data["result"]["at"] == "2026-10-14 00:00:00"
    data, _ = call("POST", "/web/schedule", {"at": "2026/10/14 09:30"})
    assert data["result"]["at"] == "2026-10-14 09:30:00"
    call("GET", "/web/datetime?at=wrong", status=422)
    call("POST", "/web/schedule", {"at": "wrong"}, 422)
    data, headers = call("GET", "/web/redirect", status=307)
    assert headers["location"] == "/docs"
    data, _ = call("OPTIONS", "/web/methods")
    assert data["result"] == ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    call("GET", "/missing", status=404)


def docs():
    data, _ = call("GET", "/docs", envelope=False)
    assert "swagger-ui" in data
    data, _ = call("GET", "/openapi.json", envelope=False)
    assert data["info"]["title"] == "PythonBoot Starter Example"
    expected = {
        "/users": {"get", "post"}, "/users/{user_id}": {"get", "put", "patch", "delete"},
        "/sync/users": {"get", "post"}, "/sync/users/{user_id}": {"get", "put", "patch", "delete"},
        "/users/page": {"get"}, "/sync/users/page": {"get"},
        "/users/rollback": {"post"}, "/sync/users/rollback": {"post"},
        "/redis/demo": {"post"}, "/redis/sync/demo": {"post"},
        "/web/health": {"get"}, "/web/echo/{item_id}": {"post"},
        "/web/datetime": {"get"}, "/web/schedule": {"post"},
        "/web/redirect": {"get"}, "/web/methods": {"options"}, "/web/task": {"get"}, "/native/info": {"get"},
    }
    assert set(data["paths"]) == set(expected)
    for path, methods in expected.items():
        assert set(data["paths"][path]) == methods, path
    print(f"HTTP operations documented: {sum(map(len, expected.values()))}", flush=True)


def concurrent():
    def echo(index):
        trace = f"trace-{index}"
        data, headers = call("POST", f"/web/echo/{index + 1}", {"index": index}, 202, {"X-Trace-Id": trace})
        assert data["result"]["trace_id"] == headers["x-trace-id"] == trace
        assert data["result"]["body"] == {"index": index}
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(echo, range(4)))
        list(pool.map(redis, ["/redis/demo", "/redis/sync/demo"] * 2))
        list(pool.map(lambda args: orm(*args), [("/users", "/sync/users"), ("/sync/users", "/users")]))


if __name__ == "__main__":
    verify("async ORM CRUD, cross-read, rollback, validation and errors", lambda: orm("/users", "/sync/users"))
    verify("sync ORM CRUD, cross-read, rollback, validation and errors", lambda: orm("/sync/users", "/users"))
    verify("async pagination defaults, total, multiple pages, bounds and validation", lambda: pagination("/users"))
    verify("sync pagination defaults, total, multiple pages, bounds and validation", lambda: pagination("/sync/users"))
    verify("async Redis utilities and locks", lambda: redis("/redis/demo"))
    verify("sync Redis utilities and locks", lambda: redis("/redis/sync/demo"))
    verify("Web context, response, dates, native DI, task and errors", web)
    verify("API documentation and complete route coverage", docs)
    verify("concurrent ORM, Redis and request context isolation", concurrent)
    print(f"Passed {checks} HTTP verification groups", flush=True)
