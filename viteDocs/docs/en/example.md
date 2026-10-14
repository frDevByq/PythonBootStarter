# Complete Starter application

The repository's `example/` is a standard src-layout PythonBoot application containing every Starter,
real PostgreSQL and Redis, and both synchronous and asynchronous HTTP APIs. The entry point is
`src/starter_example/application.py`; its application class extends `PythonBootApplication`.
Configuration, controllers, services, and domain models live in separate directories.

## Run

From the repository root:

```bash
docker compose -f example/compose.yml up -d
uv sync --all-packages
uv run --package pythonboot-starter-example python -m starter_example.application
```

The application uses `http://127.0.0.1:18000`, with `/docs` and `/openapi.json`.
PostgreSQL runs on port 15432 with database `pythonboot_example` and user/password `pythonboot`;
Redis runs on port 16379. These credentials are for local development only.
Restart existing named containers with `docker start`. After use, run
`docker stop pythonboot-starter-example-postgres pythonboot-starter-example-redis` and retain the containers and data.

The application installs distributions `pythonboot-starter-web`, `pythonboot-starter-sqlalchemy`,
and `pythonboot-starter-redis`. Each aggregates its implementation module and the `pythonboot` core.
Import startup interfaces from `pythonboot_starter_web`, routes/context from `pythonboot_web`,
ORM/Redis interfaces from the corresponding `pythonboot_starter_*` public exports, and core interfaces
from `pythonboot`. The application explicitly declares PostgreSQL drivers `asyncpg` and `psycopg[binary]`.

## Feature coverage

| Feature | HTTP API |
| --- | --- |
| Starter and lifecycle status | `GET /web/health` |
| Async ORM CRUD and filtering | `/users`, `/users/{id}` |
| Sync ORM CRUD and filtering | `/sync/users`, `/sync/users/{id}` |
| Explicit rollback | `POST /users/rollback`, `POST /sync/users/rollback` |
| Every Redis utility, native lock ownership/renewal/release | `POST /redis/demo`, `POST /redis/sync/demo` |
| Headers, query/path/body, request data, response status/headers/cookies | `POST /web/echo/{id}` |
| Parameter and body-field date formats | `GET /web/datetime`, `POST /web/schedule` |
| Redirect and custom HTTP method | `GET /web/redirect`, `OPTIONS /web/methods` |
| Explicit container binding in standalone tasks | `GET /web/task` |
| Native APIRouter and dependency bridge | `GET /native/info` |
| Exception advice and validation | Missing users/routes and invalid input (404/422) |
| AOP, property injection, settings and profiles | CRUD/Redis services and config directory |

ORM endpoints expose GET/POST/PUT/PATCH/DELETE. All business endpoints declare `BaseResult[T]`.
Both Redis demonstrations exercise every public utility: get_client, strings, TTL, counters, Hash,
List, Set, sorted sets, and native locks. Each request owns a UUID key namespace and cleans up its keys.

Installed entry points configure the default async resources. Application Beans add sync resources,
show named/qualified injection, and declare their own cleanup. Prefer `autowired()` property injection.
Each operation owns its Session and explicitly commits or rolls back. Sync routes run in FastAPI's
thread pool; async routes use async drivers. The application explicitly creates its demo schema
in a lifecycle hook; the Starter never creates schemas, and production applications should use migrations.
The container closes owned clients/pools and disposes engines, awaiting async cleanup.
Locks have a 30-second lease and a 5-second acquisition timeout, are released in finally, and require
explicit renewal. No automatic renewal is provided.

Settings live in `application.yml` and `application-local.yml`. Override connection URLs with
`PYTHONBOOT_DATASOURCE_URL`, `EXAMPLE_SYNC_DATABASE_URL`, and `PYTHONBOOT_REDIS_URL`.
Select default resource enabled/mode in YAML; adjust dependent example services when switching them.
Missing dependencies raise errors rather than silently falling back.


An application-defined async Session factory overrides its matching default auto-configuration.
The example also composes native FastAPI middleware and lifespan with framework lifecycle management.
When verification is authorized, run `uv run --package pythonboot-starter-example python example/http_smoke.py`
after starting the application. It verifies all 26 business HTTP operations and concurrent ORM, Redis, and request isolation.


Sync/async pagination: `GET /sync/users/page?page=1&pageSize=10` and `GET /users/page?page=1&pageSize=10`,
with optional name filtering. Responses use `BaseResult[Page[UserView]]` with total, page, pageSize, and rows.
