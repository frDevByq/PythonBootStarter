# Auth Starter

Install the distribution `pythonboot-starter-auth`; import public APIs from `pythonboot_starter_auth`.
The implementation is distributed as `pythonboot-auth` and imported as `pythonboot_auth`.
The base package depends only on PythonBoot, Pydantic and pydantic-settings, without FastAPI or Redis.
Applications own credential verification, user records, roles, and permissions.

## Installation and configuration

```bash
uv add pythonboot-starter-auth
uv add "pythonboot-starter-auth[web,redis]"
```

The base installation uses process-local memory. The second command adds optional Web and Redis dependencies.
You can select `[web]` or `[redis]` separately. Dependency direction is Starter → implementation → core;
extras depend on `pythonboot-web` and `pythonboot-redis` respectively.
Installing the Web extra does not register an interceptor or exception handler.

```yaml
pythonboot:
  auth:
    enabled: true
    check_enabled: true
    mode: async
    storage: redis
    login_type: user
    update_retries: 16
    token:
      header: Authorization
      cookie: null
      csrf_header: X-CSRF-Token
    session:
      timeout: 86400
      idle_timeout: 1800
      concurrent: true
      same_device_exclusive: true
      max_sessions: 5
    redis:
      key_prefix: "pythonboot:auth:"
      client_name: redisAsyncClient
  redis:
    enabled: true
    mode: async
    url: redis://localhost:6379/0
```

Defaults are `mode: sync` and `storage: memory`. Select enabled, mode, and storage in YAML.
Other properties support the `PYTHONBOOT_AUTH_` environment prefix and nested `__` delimiter,
for example `PYTHONBOOT_AUTH_SESSION__TIMEOUT=3600`.
Memory is shared only within one process and is lost on restart. Redis shares sessions across instances.
Use different key_prefix values to isolate applications; sharing a prefix intentionally shares sessions
and requires compatible serializers and policies.

Redis storage injects existing container clients without creating or closing additional pools.
client_name is optional; absent names follow the container's primary and ambiguity rules.
Sync authentication requires a sync client and async authentication requires an async client.
Missing extras, missing clients, ambiguity, backend failures and exhausted CAS retries raise explicit errors;
Redis never falls back to memory. Importing or constructing the backend does not execute Redis commands.


## Global check switch

```yaml
pythonboot:
  auth:
    enabled: true
    check_enabled: false
```

`check_enabled` defaults to `true`; `PYTHONBOOT_AUTH_CHECK_ENABLED=false` also disables it.
When disabled, synchronous and asynchronous `check_login`, `check_permission`, and `check_role` return
without checking tokens, querying session storage, or requiring a StpInterface. This also applies to
AuthUtil, AsyncAuthUtil and the `require_login`, `require_permission`, and `require_role` decorators.
`check_login()` returns `None` when disabled and SessionInfo when enabled.
The Web interceptor bypasses its checks, including automatic cookie CSRF checks; explicit `check_csrf()`
still validates a real session. Permission and role checks already include login checks when enabled.

`enabled` controls module auto-configuration; setting it to `false` does not bypass checks.
Disabling checks creates no synthetic identity. `current_subject()`, session access, logout and other
session operations still require valid tokens. Login and application credential verification keep their behavior.
Custom services should receive the same properties or a copy preserving `check_enabled`;
the Web interceptor uses the application container's AuthProperties.
The complete example explicitly sets `check_enabled: true` in application.yml; changing it to `false`
bypasses both sync memory and async Redis checks. Business endpoints reading identity or session data still need login.
Service creation logs a prominent security warning at ERROR level when checks are disabled, identifying the bypassed checks and the setting needed to restore them. Credentials are never logged.

## Login and sessions

```python
from pythonboot import autowired, service
from pythonboot_starter_auth import AsyncAuthService, LoginResult

@service
class LoginService:
    auth: AsyncAuthService = autowired()

    async def login_verified_user(self, user_id: int) -> LoginResult:
        result = await self.auth.login(user_id, device="browser")
        session = await self.auth.get_session(result.token)
        await session.set("user", {"id": user_id, "nickname": "Alice"})
        return result
```

Verify credentials in business code before calling login; a caller-supplied user ID is not proof of identity.
Non-empty string or integer login IDs are normalized to strings. login_type separates identity domains.
LoginResult contains token, csrf_token and session; token fields are excluded from repr.
Opaque random credentials identify server-side sessions. Only credential digests enter storage,
and lifecycle logs contain no tokens, passwords, connection URLs or business session data.

get_session() returns account data shared by active logins of the same subject and login type.
get_token_session() returns data specific to one login token. Both expose get(key, default=None, *, target_type=None),
set(key, value), delete(key), and keys(); async handles require await for every operation.
Writes persist immediately. Reads produce independent deserialized values; call set after changing a returned value.
Every operation revalidates the associated token, so a revoked handle cannot update or read session data.
Account data is cleared after its last active login is revoked or expires; same-device replacement retains shared data.
Do not store passwords or access tokens in business session values.

timeout is an absolute lifetime; idle_timeout is a maximum idle period. Checks and session access refresh activity
without extending the absolute deadline. concurrent=false replaces all prior logins;
same_device_exclusive=true replaces prior logins on the same device. Defaults allow concurrent devices and enforce
same-device replacement. Exceeding max_sessions revokes the oldest active login.

## StpInterface and permission matching

```python
from collections.abc import Sequence
from pythonboot import component
from pythonboot_starter_auth import AsyncStpInterface

@component
class ApplicationStpInterface(AsyncStpInterface):
    async def get_permission_list(self, login_id: str, login_type: str) -> Sequence[str]:
        return ("user:*",) if login_id == "admin" else ("user:list",)

    async def get_role_list(self, login_id: str, login_type: str) -> Sequence[str]:
        return ("admin",) if login_id == "admin" else ("reader",)
```

Real providers query application-owned databases or services. Synchronous implementations subclass StpInterface;
asynchronous implementations subclass AsyncStpInterface. Register them as Beans to inject the appropriate service.
Permissions and roles are queried for each check and are not copied into sessions or cached by default.
Checking roles or permissions without the corresponding provider raises AuthConfigurationError.

```python
await auth.check_permission("user:list")
await auth.check_permission("user:list", "user:write", mode="or")
await auth.check_role("admin")
```

Permission matching is case-sensitive and covers the whole code. Only `*` in a granted permission is special,
matching zero or more characters including colons. `user:*` grants `user:list`; `*:read` grants `order:read`;
`*` grants every concrete permission. `?` and square brackets are literal characters.
Required permission codes must be concrete and cannot contain `*`. Roles always use exact matching.
Multiple codes support mode="and" (default) and mode="or".

## Public APIs

AuthService/AuthUtil are synchronous; AsyncAuthService/AsyncAuthUtil are asynchronous.

| Method | Behavior |
| --- | --- |
| login(login_id, *, login_type=None, device="default") | Return LoginResult |
| check_login(token) | Validate login and return SessionInfo when checks are enabled; otherwise return None |
| is_login(token) | Return whether a valid login exists; returns False when unauthenticated or checks are disabled |
| current_subject(token) | Return the normalized subject ID |
| logout(token) | Revoke the current login |
| kickout(login_id, *, login_type=None, device=None, session_id=None) | Revoke matching active logins and return the count |
| list_sessions(login_id, *, login_type=None, include_inactive=False) | Return metadata sorted by creation time |
| check_permission(*codes, token=..., mode="and") | Check dynamic permissions |
| check_role(*roles, token=..., mode="and") | Check dynamic roles |
| check_csrf(csrf_token, *, token=...) | Validate a login's CSRF credential |
| get_session(token) / get_token_session(token) | Obtain account/token session handles |

Omitting token uses the bound authentication context; explicit None means a missing token.
kickout and list_sessions are management capabilities: applications must authorize their callers before exposing them.
SessionInfo includes session_id, login_id, login_type, device, created_at, last_activity, expires_at and status.
Time fields are Unix seconds; metadata does not expose credential digests or business values.

Static utilities resolve the current container on each call and never cache global services.
get_service(name=..., qualifier=...) selects named or qualified service Beans. Prefer autowired() property injection.
Independent tasks bind both the application container and the authentication token:

```python
from pythonboot import ContextUtil
from pythonboot_starter_auth import AuthContextHolder, AsyncAuthUtil

with ContextUtil.use(context), AuthContextHolder.use(token):
    subject = await AsyncAuthUtil.current_subject()
```

Omitting a token outside a bound authentication scope raises NotLoginError with the message `Not logged in`.
The reason remains available through the reason attribute. Permission and role checks validate login first.
Calling AuthContextHolder.current() directly still requires a bound context and otherwise raises AuthContextError.
Injected service instances accept explicit tokens without an HTTP request or a utility container binding.

## Explicit Web interceptor registration

```python
from fastapi import FastAPI
from pythonboot_starter_web import PythonBootApplication
from pythonboot_auth.web import install_auth_interceptor

class Application(PythonBootApplication):
    def configure(self, app: FastAPI) -> None:
        install_auth_interceptor(app, include=("/api/*",), exclude=("/api/login",))
```

Alternatively use AuthInterceptor(include=..., exclude=...).install(app).
Register once during application configuration before startup. Existing and subsequently registered FastAPI API routes
receive authentication dependencies. WebSocket routes, mounted subapplications and underlying documentation routes
are not automatically protected; mount targets need their own integration.
The default include list is empty, so only explicitly decorated endpoints require authentication.
Path patterns support only `*`, including across `/`. Exclusions bypass path rules but never explicit decorators.
Checks execute as route dependencies inside application exception handling.

By default the adapter extracts Authorization: Bearer credentials. Headers take precedence over optional cookies;
malformed or duplicate headers are not replaced with cookie credentials. Query-string tokens are not supported.
ContextVar bindings for the token and application container are restored after the request.
Default service selection follows pythonboot.auth.mode; synchronous storage checks run in a worker thread.
Applications with several services can pass a synchronous service_resolver(request) to AuthInterceptor,
returning the appropriate AuthService/AsyncAuthService; the complete example selects separate sync and async services.

```python
from pythonboot_starter_auth import require_login, require_permission, require_role
from pythonboot_web import controller, get
from starter_example.domain.common import BaseResult

@controller(prefix="/api/users")
@require_login
class UserController:
    @get("", response_model=BaseResult[list[str]])
    @require_permission("user:list")
    async def list_users(self) -> BaseResult[list[str]]:
        return BaseResult.success(["Alice"])
```

Decorators also work on business functions and preserve signatures and metadata.
Class decorators apply to instance methods declaring PythonBoot routes. Class and method checks compose.
Sync decorators resolve AuthService, async decorators resolve AsyncAuthService; register matching Beans.
Custom interceptor service selection must agree with business injection, utilities and decorators.
Use names, qualifiers or primary to make multi-service selection explicit.

Cookies are disabled by default. When token.cookie is configured, applications write their own cookies using suitable
Secure, HttpOnly and SameSite settings. Protected cookie-authenticated requests with unsafe methods require the login's
csrf_token in token.csrf_header; otherwise CsrfError is raised. Header authentication does not require this CSRF token.
The framework never sets cookies, returns tokens in HTTP responses, or changes response envelopes automatically.

## Application-owned exception handling

Authentication raises typed errors, without registering handlers, generating HTTP responses or changing business returns:

| Error | Meaning |
| --- | --- |
| NotLoginError | Missing/malformed credentials, expired/invalid login, logout, kickout or replacement |
| NotPermissionError | Required permissions not granted |
| NotRoleError | Required roles not granted |
| CsrfError | Missing or invalid CSRF credential on a protected cookie write |
| AuthStorageError | Storage failure or exhausted concurrent-update retries |
| SessionSerializationError | Value encoding/decoding failed |
| AuthConfigurationError | Requested capability is not configured |
| AuthContextError | No authentication context bound |

All inherit AuthError. NotLoginError.reason can be missing_token, malformed_token, invalid_or_expired,
expired, logged_out, kicked_out or replaced. Once TTL removes a token, expiry cannot be distinguished from a forged token;
invalid_or_expired covers both. Revocation tombstones remain until the original absolute deadline.
Permission and role errors carry the required codes and combination mode. Storage failure is not reported as logout.
Applications choose HTTP statuses and response structures. The complete example owns its 401/403/503 mappings.

## Replaceable serialization and storage

JsonSessionSerializer automatically encodes Pydantic models, dataclasses and ordinary objects with __dict__
as JSON. Dates/times, Enum, UUID and sets are also supported. Non-finite numbers and unsupported objects are rejected.
No manual model_dump or model_validate calls are required:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    nickname: str

user = User(id=1, nickname="Alice")
await session.set("user", user)
user = await session.get("user", target_type=User)

# Synchronous sessions use the same arguments.
sync_session.set("user", user)
user = sync_session.get("user", target_type=User)

# Generic collections and nested models can be explicitly reconstructed.
await session.set("users", [User(id=1, nickname="Alice")])
users = await session.get("users", target_type=list[User])
```

Pydantic models, dataclasses, built-in types and generic collections are validated and restored through TypeAdapter;
nested fields follow model/dataclass declarations. Ordinary classes use target_type(**data) for dictionary values
and must accept their serialized attributes as constructor arguments. Undeclared nested ordinary objects are not
recursively reconstructed. Omitting target_type returns decoded JSON-native values. Missing keys return the default
unchanged; stored null remains None. Encoding, decoding or target validation failures raise SessionSerializationError.
No executable type metadata is stored and no classes are imported based on stored content.

Custom SessionSerializer Beans remain supported without changing their serialize/deserialize signatures.
Target restoration applies after custom decoding; already-decoded instances of the requested business type are retained:

```python
from typing import Any
from pythonboot import bean, configuration
from pythonboot_starter_auth import SessionSerializer

class ApplicationSerializer(SessionSerializer):
    def serialize(self, value: Any) -> bytes:
        return application_codec.encode(value)

    def deserialize(self, data: bytes) -> Any:
        return application_codec.decode(data)

@configuration
class SerializationConfiguration:
    @bean
    def serializer(self) -> SessionSerializer:
        return ApplicationSerializer()
```

application_codec is supplied by the application. No additional serialization dependency or default pickle is used.
Memory and Redis both serialize on every business-value access, preserving behavior when switching backends.
Internal metadata uses a fixed JSON envelope; the replaceable serializer handles business values only.
Serialized bytes are Base64 encoded to support Redis clients with either decode_responses setting.
Changing serializers requires a new key prefix or deliberate revocation of old sessions; data is not automatically migrated.

Custom SessionStore/AsyncSessionStore Beans override default storage. Contracts are get(account_id), lookup(token_digest)
and compare_and_set(account_id, revision, state, ttl). get returns an independent copy. CAS atomically updates account
state and all token indexes with expiry, returning False only for revision conflicts. Custom providers own resource cleanup.
Memory uses a process lock; Redis uses revision CAS and Lua to atomically update state and indexes.
All account and token keys of a namespace share a Redis hash tag, so a namespace uses one slot; cross-slot sharding is not
provided. Default clients remain the existing standalone Redis clients. CAS retries are bounded by update_retries.
Keep application and Redis clocks synchronized. No local Redis-session cache delays logout or kickout propagation.

## Complete example

The complete workspace application installs Auth's web/redis extras. `/auth/*` uses async Redis storage;
`/sync/auth/*` uses an application-provided synchronous memory service. The application explicitly registers its
interceptor, excludes both login endpoints and owns its exception advice.
admin/admin-demo and reader/reader-demo are local demonstration credentials; production applications replace their source.
Endpoints demonstrate login/logout, direct account user-object storage and target_type restoration, token device data, device replacement, concurrent sessions,
wildcard permissions, AND/OR checks, roles and administrative kickout. Every business response uses BaseResult[T].
