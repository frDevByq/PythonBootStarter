# pythonboot-auth

PythonBoot 的鉴权实现包，导入名 `pythonboot_auth`。业务安装 `pythonboot-starter-auth`；
Starter 只聚合依赖和公共导出。核心鉴权不依赖 Web 或 Redis，默认同步模式与进程内存存储。

支持随机 Token、账号与 Token 两类 Session、绝对/空闲过期、多端登录、同端替换、会话数量限制、
注销/踢人、同步/异步 API、动态 StpInterface、`*` 通配权限与 AND/OR 校验。
Session 默认 JSON 序列化，可注册自定义 SessionSerializer Bean，内存与 Redis 行为一致。
权限和角色检查先校验登录；未绑定上下文且未传 Token 时抛出 NotLoginError，消息仅为“Not logged in”，原因通过 reason 属性获取。
可使用 `AuthUtil.is_login()` 或 `AsyncAuthUtil.is_login()` 获取布尔登录状态；未登录或关闭校验时返回 `False`。

```bash
uv add "pythonboot-starter-auth[web,redis]"
```

通过 `pythonboot.auth` 配置 enabled、mode、storage 和会话策略；Redis 复用现有
pythonboot-redis 客户端，缺少依赖或故障时不回退到内存。
可选 Web 适配位于 `pythonboot_auth.web`，应用显式注册 AuthInterceptor 与保护/放行路径。
鉴权只抛特定异常，不注册响应处理器、不修改响应；用户对象、凭据验证与异常响应由业务负责。
业务推荐 `autowired()` 属性注入 AuthService/AsyncAuthService；静态工具通过当前容器解析服务。

完整配置、API、序列化扩展和示例见 [中文文档](../../viteDocs/docs/zh/auth.md)、
[English documentation](../../viteDocs/docs/en/auth.md)、[全量示例](../../example/README.md)。

The implementation provides synchronous and asynchronous server-side authentication without mandatory
Web or Redis dependencies. Opaque tokens identify account/token sessions; configurable expiry, concurrent
login policies and atomic revocation are supported. Applications supply StpInterface role/permission providers
and can replace the default JSON serializer. Optional Redis storage reuses managed clients and never falls back
to memory. Applications explicitly install the optional Web interceptor and own exception responses.

## Session 对象存取 / Session objects

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
