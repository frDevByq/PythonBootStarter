# pythonboot-starter-auth

鉴权启动依赖包，导入名 `pythonboot_starter_auth`，仅聚合 `pythonboot-auth` 并显式导出公共接口。
实现位于 `pythonboot_auth`，不在 Starter 内实现业务功能。
权限和角色检查先校验登录；未绑定上下文且未传 Token 时抛出 NotLoginError，消息仅为“Not logged in”，原因通过 reason 属性获取。

```bash
uv add pythonboot-starter-auth
# 按需选择 web、redis 或两者
uv add "pythonboot-starter-auth[web,redis]"
```

默认不引入 Web/Redis，使用同步 API 与内存会话。`pythonboot.auth.mode`、`storage` 由 YAML 明确选择。
`[web]` 提供 Web 依赖，应用自行从 `pythonboot_auth.web` 注册 AuthInterceptor；
`[redis]` 提供 Redis 依赖，复用现有客户端。安装依赖不自动保护路由。

支持账号/Token Session、可替换的 JSON 序列化、StpInterface 动态权限/角色、`*` 通配权限、
鉴权装饰器、过期、多端策略和踢人。失败只抛特定异常，应用自行决定返回结构。
推荐使用 `autowired()` 注入 AuthService/AsyncAuthService，或在绑定的上下文使用静态工具。

详见 [中文](../../viteDocs/docs/zh/auth.md)、[English](../../viteDocs/docs/en/auth.md)、
[全量示例](../../example/README.md)。

This Starter aggregates and explicitly re-exports the authentication implementation. The base package
has no Web or Redis dependency; select extras independently. Applications explicitly register Web interceptors,
provide dynamic permission/role providers, verify credentials, and handle typed authentication exceptions.
Session values use replaceable JSON serialization across memory and Redis backends.

## Session 对象存取 / Session objects

使用 `AuthUtil.is_login()` 或 `AsyncAuthUtil.is_login()` 可直接判断当前 Token 是否有效，未登录时返回 `False`。

默认 JSON 自动序列化 Pydantic、dataclass 和普通对象，读取时显式指定目标类型：

```python
await session.set("user", user)
user = await session.get("user", target_type=User)

sync_session.set("user", user)
user = sync_session.get("user", target_type=User)
```

支持 `target_type=list[User]` 等泛型与声明的嵌套模型；不指定类型时返回 JSON 原生数据。
不存在的键原样返回 default，存储的 null 返回 None；转换失败抛 SessionSerializationError。
自定义 SessionSerializer 接口保持兼容，内存和 Redis 后端行为一致。

Default JSON serialization accepts Pydantic models, dataclasses and ordinary objects directly.
Use get(key, target_type=User) to reconstruct a model, or target_type=list[User] for typed collections.
Type conversion follows caller-selected declarations without stored class metadata. Missing keys preserve
supplied defaults and null stays None; invalid values raise SessionSerializationError.


## 全局校验开关 / Global check switch

```yaml
pythonboot:
  auth:
    enabled: true
    check_enabled: false
```

`check_enabled` 默认 true，可用 `PYTHONBOOT_AUTH_CHECK_ENABLED=false` 关闭。
关闭后同步／异步登录、权限、角色校验及对应装饰器、静态工具、Web 拦截器直接跳过，
不读取 Token 或会话存储，也不要求权限提供者；`check_login()` 返回 None。
拦截器自动 CSRF 校验一并跳过；显式 check_csrf、当前用户和 Session 操作仍要求真实登录。
`enabled` 仅控制自动装配；自定义服务应传入同一 AuthProperties 或保留开关的副本。

Set `pythonboot.auth.check_enabled: false` or `PYTHONBOOT_AUTH_CHECK_ENABLED=false` to bypass
sync/async login, permission and role checks, decorators, utilities, and the Web interceptor.
Checks require no token, provider or storage access; check_login returns None. The interceptor also skips
automatic CSRF checks. Explicit CSRF checks, identity and session operations still require real authentication.
The default is true. The existing enabled setting controls auto-configuration only.
Custom services must receive properties preserving this switch.

关闭鉴权校验时，服务创建会以 ERROR 级别输出醒目的安全警告及恢复配置提示。
Disabling authentication checks emits a prominent ERROR-level security warning when the service is created, including instructions to restore checks.
