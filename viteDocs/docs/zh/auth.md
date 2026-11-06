# Auth Starter

`pythonboot-starter-auth` 是安装的分发包，`pythonboot_starter_auth` 是公共导入包。
实现位于 `pythonboot-auth` / `pythonboot_auth`，基础依赖仅为核心框架、Pydantic 和
pydantic-settings，不依赖 FastAPI 或 Redis。账号密码验证及用户、角色、权限的数据来源由业务负责。

## 安装与选择

```bash
uv add pythonboot-starter-auth
uv add "pythonboot-starter-auth[web,redis]"
```

第一条安装核心鉴权与默认内存存储；第二条增加可选 Web、Redis 依赖。
也可只安装 `[web]` 或 `[redis]`。依赖方向为 Starter → 实现模块 → 核心框架；
可选 Web、Redis 分别依赖 `pythonboot-web` 和 `pythonboot-redis`。
安装 Web extra 不会注册拦截器，也不会注册异常处理器。

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

默认 `mode: sync`、`storage: memory`。`enabled`、`mode`、`storage` 由 YAML 选择；
其余属性支持 `PYTHONBOOT_AUTH_` 环境变量，嵌套属性使用 `__`，
例如 `PYTHONBOOT_AUTH_SESSION__TIMEOUT=3600`。
内存后端只在当前进程共享，重启丢失会话；Redis 用于多进程、多实例共享。
不同应用需要使用不同 `key_prefix`，相同前缀意味着主动共享会话，必须保持序列化和配置兼容。

Redis 客户端来自现有容器，`client_name` 可选，无名称时遵循 qualifier/primary 与候选歧义规则。
同步鉴权需要同步客户端，异步鉴权需要异步客户端；多个客户端存在歧义时明确报错。
客户端及连接池由原提供方管理，鉴权不重复创建或关闭连接池。
指定 Redis 而缺少依赖、客户端或后端故障时明确报错，不降级到内存。
创建对象不连接外部服务，不在导入时执行 Redis 命令。


## 全局校验开关

```yaml
pythonboot:
  auth:
    enabled: true
    check_enabled: false
```

`check_enabled` 默认 `true`，也可设置环境变量 `PYTHONBOOT_AUTH_CHECK_ENABLED=false`。
关闭后，同步／异步 `check_login`、`check_permission`、`check_role` 直接跳过，
对应 AuthUtil、AsyncAuthUtil 和 `require_login`、`require_permission`、`require_role` 装饰器同样生效。
无需提供 Token 或 StpInterface，不读取会话存储；`check_login()` 返回 `None`，开启时仍返回 SessionInfo。
Web 拦截器直接放行，包括其自动 Cookie CSRF 校验；显式 `check_csrf()` 仍校验真实会话。
权限与角色校验在开启时已包含登录校验，不必叠加 `require_login`。

`enabled` 控制模块自动装配，不能用 `enabled: false` 代替跳过校验。
关闭校验不会创建虚拟身份：`current_subject()`、Session 获取／读写、注销等仍要求有效 Token，
`login()` 及应用自己的凭据验证保持原行为。使用自定义服务时，应传入同一配置或保留
`check_enabled` 的配置副本；Web 拦截器使用应用容器中的 AuthProperties。
完整示例的 application.yml 显式设置 `check_enabled: true`，改为 `false` 同时跳过同步内存与异步 Redis 校验；
读取当前用户或会话数据的业务接口仍需要登录。
服务创建时以 ERROR 级别输出醒目的安全警告，明确登录、权限和角色校验已跳过，并提示恢复配置；不记录凭据。

## 登录与会话

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

调用 `login` 前业务必须自行验证凭据，不能直接将客户端提交的 ID 当作可信身份。
主体 ID 接受非空字符串或整数，统一规范化为字符串；登录类型隔离 user/admin 等身份。
`LoginResult` 包含 `token`、`csrf_token`、`session`，Token 和 CSRF Token 不进入对象 repr。
随机不透明 Token 对应服务端会话，存储仅保留 Token/CSRF 摘要，不记录凭据日志。

`get_session()` 获取账号 Session，同一账号同一登录类型的多个活跃登录共享扩展数据；
`get_token_session()` 获取当前 Token 的独立 Session。两者提供 `get(key, default=None, *, target_type=None)`、
`set(key, value)`、`delete(key)`、`keys()`，异步版本每次操作都需要 await。
写入立即持久化；读取得到独立的反序列化值，修改后必须再次 `set`。
每次操作重新验证关联 Token，已注销的旧 Session 句柄不能继续读写。
最后一个活跃登录退出或过期后，账号扩展数据清除；同端替换保留共享账号数据。
不要保存密码或令牌到业务扩展数据。

`timeout` 是绝对有效期，`idle_timeout` 是最大空闲时长，校验或 Session 操作更新活动时间，
不会延长绝对有效期。`concurrent: false` 替换全部旧登录；
`same_device_exclusive: true` 替换同设备旧登录；默认允许多端共存，并启用同端互斥。超过 `max_sessions` 时踢掉最早的活跃登录。

## StpInterface 与权限

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

实际项目由业务查询数据库或其他服务。同步实现继承 `StpInterface`，方法为普通 def；
异步实现继承 `AsyncStpInterface`。注册为 Bean 后注入对应鉴权服务，权限和角色默认每次动态读取，
不保存到登录会话，不进行本地缓存。未提供对应接口却执行权限/角色检查时抛出 `AuthConfigurationError`。

```python
await auth.check_permission("user:list")
await auth.check_permission("user:list", "user:write", mode="or")
await auth.check_role("admin")
```

权限码大小写敏感、全字符串匹配；只有授权列表中的 `*` 是通配符，可匹配零个或多个字符，
包括冒号。`user:*` 匹配 `user:list`，`*:read` 匹配 `order:read`，`*` 匹配所有权限。
`?` 和 `[]` 无特殊含义。要求的权限必须是具体权限码，不能携带 `*`。
角色始终精确匹配；多权限/角色支持 `mode="and"`（默认）或 `mode="or"`。

## 公共 API

同步 `AuthService` / `AuthUtil` 与异步 `AsyncAuthService` / `AsyncAuthUtil` 提供：

| 方法 | 行为 |
| --- | --- |
| `login(login_id, *, login_type=None, device="default")` | 创建登录并返回 LoginResult |
| `check_login(token)` | 开启校验时验证登录并返回 SessionInfo；关闭时返回 None |
| `is_login(token)` | 返回是否存在有效登录；未登录或校验关闭时返回 False |
| `current_subject(token)` | 返回规范化主体 ID |
| `logout(token)` | 撤销当前 Token |
| `kickout(login_id, *, login_type=None, device=None, session_id=None)` | 撤销匹配的活跃会话，返回数量 |
| `list_sessions(login_id, *, login_type=None, include_inactive=False)` | 按创建顺序返回元数据 |
| `check_permission(*codes, token=..., mode="and")` | 检查动态权限 |
| `check_role(*roles, token=..., mode="and")` | 检查动态角色 |
| `check_csrf(csrf_token, *, token=...)` | 校验当前会话的 CSRF Token |
| `get_session(token)` / `get_token_session(token)` | 获取账号/Token Session |

省略 token 时使用当前鉴权上下文，显式传入 None 表示缺失 Token。
`kickout` 与 `list_sessions` 是管理能力，调用方必须自行保证操作者权限，不能直接暴露为公共接口。
SessionInfo 包含 session_id、login_id、login_type、device、created_at、last_activity、expires_at、status，
时间字段是 Unix 秒，不包含 Token 摘要或业务数据。

静态工具每次通过 `ContextUtil` 获取当前容器服务，不缓存全局对象。
`get_service(name=..., qualifier=...)` 支持选择多服务 Bean；可直接使用返回的服务实例。
业务推荐 `autowired()` 属性注入。独立任务同时显式绑定容器和 Token：

```python
from pythonboot import ContextUtil
from pythonboot_starter_auth import AuthContextHolder, AsyncAuthUtil

with ContextUtil.use(context), AuthContextHolder.use(token):
    login_id = await AsyncAuthUtil.current_subject()
```

没有绑定上下文且省略 Token 时抛出 `NotLoginError`，消息为“Not logged in”，原因保留在 `reason` 属性中。
权限和角色检查先校验登录；直接调用 `AuthContextHolder.current()` 仍要求绑定上下文，否则抛出 `AuthContextError`。
直接注入的服务可以显式接收 Token，
不需要 HTTP 请求或容器工具上下文。

## 应用显式注册 Web 拦截器

```python
from fastapi import FastAPI
from pythonboot_starter_web import PythonBootApplication
from pythonboot_auth.web import install_auth_interceptor

class Application(PythonBootApplication):
    def configure(self, app: FastAPI) -> None:
        install_auth_interceptor(
            app,
            include=("/api/*",),
            exclude=("/api/login",),
        )
```

也可调用 `AuthInterceptor(include=..., exclude=...).install(app)`。
注册发生在应用 configure 阶段、启动前，只允许一次。
已有与后续注册的 FastAPI API 路由均接入校验；WebSocket、Mount 子应用和文档底层路由不自动保护，
子应用需单独接入。默认 include 为空，只有显式鉴权装饰器生效。
路径规则只支持 `*` 通配符，可跨 `/`；排除路径只放行路由规则，不覆盖显式装饰器。
拦截器在路由依赖阶段抛出异常，应用异常处理器可以正常接收。

默认从 `Authorization: Bearer <token>` 获取 Token，Header 优先，格式错误不回退到 Cookie；
重复 Header 明确视为格式错误，不从 Query 参数提取 Token。
请求期间使用 ContextVar 绑定 Token 与应用容器，结束后恢复原绑定。
拦截器默认根据 `pythonboot.auth.mode` 选择服务，同步存储操作在线程池中执行。
同一应用有多个鉴权服务时可给 `AuthInterceptor` 提供同步 `service_resolver(request)`，
返回当前路由应该使用的 AuthService/AsyncAuthService，参见全量示例的同步与异步路径选择。

```python
from pythonboot_starter_auth import require_login, require_permission, require_role
from pythonboot_web import controller, get
from starter_example.domain.common import BaseResult

@controller(prefix="/api/users")
@require_login
class UserController:
    @get("", summary="查询用户", response_model=BaseResult[list[str]])
    @require_permission("user:list")
    async def list_users(self) -> BaseResult[list[str]]:
        return BaseResult.success(["Alice"])
```

装饰器也可用于业务函数，直接调用时仍执行校验并保留函数签名、元数据。
类级装饰器应用到声明了 PythonBoot 路由的实例方法，类级与方法级检查叠加。
同步装饰器使用 AuthService，异步装饰器使用 AsyncAuthService，需要注册对应 Bean。
装饰器通过当前容器解析服务；使用自定义 Web service_resolver 时，应确保其服务选择与业务注入、
静态工具和装饰器使用的服务一致。可在自定义服务之间用 name/qualifier/primary 明确选择。

Cookie 默认关闭；启用 `token.cookie` 后，应用自行写入 Cookie，推荐 Secure、HttpOnly 和适当 SameSite。
受保护接口通过 Cookie 鉴权且使用 POST/PUT/PATCH/DELETE 等非安全方法时，
必须携带登录返回的 csrf_token 到 `token.csrf_header`，否则抛出 CsrfError。
Header Token 鉴权不要求 CSRF Token。框架不会自动设置 Cookie、返回 Token 或修改响应。

## 异常由应用处理

框架只抛出异常，不生成 HTTP 响应、不注册异常处理器、不修改业务返回结构：

| 异常 | 含义 |
| --- | --- |
| `NotLoginError` | 缺失、格式错误、失效或过期、注销、被踢、被替换 |
| `NotPermissionError` | 缺少要求的权限 |
| `NotRoleError` | 缺少要求的角色 |
| `CsrfError` | Cookie 写操作缺少有效 CSRF Token |
| `AuthStorageError` | 存储故障或并发重试耗尽 |
| `SessionSerializationError` | 扩展值序列化/反序列化失败 |
| `AuthConfigurationError` | 请求了未配置的能力 |
| `AuthContextError` | 当前执行作用域没有鉴权上下文 |

以上异常继承 AuthError。NotLoginError.reason 包括 missing_token、malformed_token、invalid_or_expired、
expired、logged_out、kicked_out、replaced；TTL 删除后无法区分伪造 Token 与已过期 Token，
统一为 invalid_or_expired。撤销记录保留到原绝对有效期，到期后清除。
权限异常包含所需权限/角色与组合模式。服务故障不伪装成未登录。
应用可以选择 HTTP 状态与统一响应，完整示例自行映射 401/403/503。

## 自定义序列化与存储

默认 JsonSessionSerializer 自动将 Pydantic 模型、dataclass 和带 `__dict__` 的普通对象转换为 JSON，
同时支持日期时间、Enum、UUID、set/frozenset，拒绝 NaN/Infinity 和不支持的对象。
无需手动调用 model_dump 或 model_validate：

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    nickname: str

user = User(id=1, nickname="Alice")
await session.set("user", user)
user = await session.get("user", target_type=User)

# 同步 Session 使用相同参数
sync_session.set("user", user)
user = sync_session.get("user", target_type=User)

# 泛型集合及嵌套模型也可以显式还原
await session.set("users", [User(id=1, nickname="Alice")])
users = await session.get("users", target_type=list[User])
```

Pydantic 模型、dataclass、基础类型及泛型集合通过 TypeAdapter 校验和还原，
嵌套字段按照模型/数据类声明解析。普通对象按 JSON 字典调用 `target_type(**data)`，
需要构造器接受对应字段；普通对象不自动递归恢复未声明的自定义对象。
不传 target_type 时仍返回 JSON 原生值；键不存在时原样返回 default，
存储值为 null 时返回 None，不转换为默认值。
格式或类型校验失败抛出 SessionSerializationError，不返回错误类型或静默降级。
不在存储中写入可执行类型元数据，不根据存储内容导入任意类。

需要其他编码时仍可注册自定义 Bean，serialize/deserialize 接口保持不变，
target_type 在自定义解码之后统一处理；已是目标类型的业务对象直接返回：

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

`application_codec` 是应用提供的编码器，框架不安装额外序列化依赖，也不默认使用 pickle。
内存与 Redis 使用同一序列化契约，每次扩展值存取都序列化，避免切换后端改变对象行为。
内部会话元数据使用固定 JSON 信封，自定义序列化仅负责扩展值；字节数据采用 Base64 存储，
兼容现有 Redis 客户端的 decode_responses 设置。
更换序列化器时应使用新 Redis 前缀或主动撤销旧会话，不自动迁移旧数据。

应用自定义 SessionStore / AsyncSessionStore Bean 会使默认存储退让。
接口为 get(account_id)、lookup(token_digest)、compare_and_set(account_id, revision, state, ttl)。
get 必须返回独立状态副本；CAS 必须原子更新账号记录与全部 Token 索引，并遵守 TTL，
返回 False 只表示版本冲突。自定义资源关闭由提供方声明。
Memory 后端使用进程锁；Redis 后端通过版本 CAS 和 Lua 原子更新，不使用非原子的先查后写。
同一 namespace 的账号与 Token Key 使用同一 Redis hash tag，方便跨键原子操作；
一个 namespace 占用一个槽位，不提供跨槽分片。默认客户端仍是现有独立 Redis 客户端。
高并发下 CAS 最多重试 update_retries 次，耗尽时抛 AuthStorageError。
应用实例与 Redis 服务应保持时钟同步。

## 全量示例

[全量应用](../../../example/README.md) 安装 Auth 的 web/redis extras。
`/auth/*` 使用异步 Redis，会话由多实例共享；`/sync/auth/*` 使用应用定义的同步内存 Bean。
应用显式注册拦截器并放行两个登录接口，应用 ErrorAdvice 自行处理鉴权异常。
admin/admin-demo 与 reader/reader-demo 仅供本地演示；生产应用应替换凭据来源。
示例覆盖登录/注销、账号用户对象直接写入及 target_type 还原、Token 设备数据、同端替换、多端会话、通配权限、AND/OR、
角色校验和管理员踢人，所有业务接口返回 BaseResult[T]。
