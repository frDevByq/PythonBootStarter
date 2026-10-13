# PythonBootStarter 开发规范

## 协作要求

- 使用中文回复，沟通简洁直接，尽快完成任务。
- 未经用户明确允许，不得自行编译、构建、测试或运行项目，也不得安装依赖。
- 修改完成后不自行执行检查，不使用 `git diff`。
- 如无必要，不联网查询文档；仅在确实不了解相关信息时查询。
- 如涉及界面，只添加实际产品元素，不添加设计说明文字。
- 每次完成修改后，执行一次 `git add .`，暂存当前仓库的全部改动。
- 不创建 `.gitkeep` 文件，不使用占位文件保留空目录。
- 非必要不创建 `__init__.py`；仅用于公共接口导出、必要的包解析或实际初始化逻辑，
  不为目录标记或说明文字创建。

## 项目目标

维护 PythonBoot 的扩展实现与启动依赖多项目仓库。使用 UV workspace 统一管理，
每个实现模块和 Starter 都是独立的 Python 分发包，分别构建并发布到 PyPI 或指定 Python 包源。

核心框架 `pythonboot` 保留在同级 `../PythonBoot` 仓库。
本仓库提供 Web 等扩展能力，不复制核心容器、Bean、AOP、配置或事务抽象的实现。

## 目录与职责

```text
PythonBootStarter/
  pyproject.toml                         UV 工作区及本地依赖来源
  modules/                               功能实现包
    pythonboot-web/
      pyproject.toml                     独立发布元数据及运行时依赖
      README.md                          模块说明及用法
      src/pythonboot_web/                Web 集成与启动实现
    pythonboot-sqlalchemy/
      pyproject.toml                     SQLAlchemy 实现包依赖和自动配置入口
      README.md                          配置与原生 ORM 用法
      src/pythonboot_sqlalchemy/         Engine、Session 工厂和配置属性
    pythonboot-redis/
      pyproject.toml                     redis-py 依赖和自动配置入口
      README.md                          原生客户端、静态工具和锁用法
      src/pythonboot_redis/              客户端配置、同步／异步工具和生命周期
  starters/                              用户安装的启动依赖聚合包
    pythonboot-starter-web/
      pyproject.toml                     独立发布元数据及聚合依赖
      README.md                          安装方式及入口说明
      src/pythonboot_starter_web/        必要的公共启动接口导出
    pythonboot-starter-sqlalchemy/
      pyproject.toml                     ORM 启动依赖聚合
      README.md                          安装和入口说明
      src/pythonboot_starter_sqlalchemy/ 公共工厂和配置类型导出
    pythonboot-starter-redis/
      pyproject.toml                     Redis 启动依赖聚合
      README.md                          安装和入口说明
      src/pythonboot_starter_redis/      公共客户端、配置和工具导出
  examples/sqlalchemy/                  原生 ORM 显式提交示例
  examples/redis/                       客户端注入、静态工具和分布式锁示例
  README.md                              仓库结构及工作区使用说明
  AGENTS.md                              本规范
  viteDocs/                              所有 Starter 的统一中英文文档站
../PythonBoot/
  src/pythonboot/                        框架核心
  examples/                             框架使用样例
  viteDocs/                             中英文文档站
```

- `modules/` 负责实际功能、第三方库适配和自动配置实现。
- `starters/` 负责依赖聚合及必要的公共入口导出，不承载功能实现或业务逻辑。
- 根项目用于工作区管理，不作为所有模块的统一运行时依赖包。
- 新模块遵循 `pythonboot-<能力>` 分发名和 `pythonboot_<能力>` 导入名。
- 新 Starter 遵循 `pythonboot-starter-<能力>` 分发名；存在导入包时使用
  `pythonboot_starter_<能力>`。命名以实际能力为准，避免创建无用途的模块。
- 子项目使用 `src` 布局，不创建嵌套 Git 仓库。

## 依赖清单

Python 版本要求：>=3.12。使用 UV 管理依赖；各项目的 `pyproject.toml`
是自身依赖声明的唯一来源。本清单必须与声明保持一致。

| 项目 | 类型 | 依赖 | 版本范围 | 用途 |
| --- | --- | --- | --- | --- |
| 根工作区 | 运行时 | 无 | — | 仅组织子项目，不聚合运行时依赖 |
| pythonboot-web | 运行时 | pythonboot | >=0.1.0,<0.2 | 核心容器、Bean、配置、自动配置和上下文能力 |
| pythonboot-web | 运行时 | fastapi | >=0.115,<1 | ASGI Web 框架、路由和 OpenAPI |
| pythonboot-web | 运行时 | uvicorn[standard] | >=0.34,<1 | ASGI 服务及本地热重载 |
| pythonboot-web | 构建 | hatchling | >=1.27,<2 | 构建 src 布局的软件包 |
| pythonboot-starter-web | 运行时 | pythonboot-web | >=0.1.0,<0.2 | 聚合 Web 实现及其传递依赖 |
| pythonboot-starter-web | 构建 | hatchling | >=1.27,<2 | 构建独立 Starter 分发包 |
| pythonboot-sqlalchemy | 运行时 | pythonboot | >=0.1.0,<0.2 | 容器、配置属性、自动配置和生命周期 |
| pythonboot-sqlalchemy | 运行时 | sqlalchemy[asyncio] | >=2.0.38,<3 | 原生同步／异步 ORM、Engine、Session 工厂与 asyncio 所需 greenlet |
| pythonboot-sqlalchemy | 运行时 | pydantic | >=2.10,<3 | 嵌套配置类型和参数校验 |
| pythonboot-sqlalchemy | 运行时 | pydantic-settings | >=2.7,<3 | 配置属性和环境变量覆盖 |
| pythonboot-sqlalchemy | 构建 | hatchling | >=1.27,<2 | 构建 src 布局的 ORM 实现包 |
| pythonboot-starter-sqlalchemy | 运行时 | pythonboot-sqlalchemy | >=0.1.0,<0.2 | 聚合 ORM 实现与传递依赖 |
| pythonboot-starter-sqlalchemy | 构建 | hatchling | >=1.27,<2 | 构建独立 ORM Starter 分发包 |
| pythonboot-redis | 运行时 | pythonboot | >=0.1.0,<0.2 | 容器、配置属性、ContextUtil 和资源生命周期 |
| pythonboot-redis | 运行时 | redis | >=5.0,<8 | redis-py 同步／异步客户端、连接池和原生分布式锁 |
| pythonboot-redis | 运行时 | pydantic | >=2.10,<3 | 参数校验和 SecretStr 密码保护 |
| pythonboot-redis | 运行时 | pydantic-settings | >=2.7,<3 | Redis 配置属性和环境变量覆盖 |
| pythonboot-redis | 构建 | hatchling | >=1.27,<2 | 构建 src 布局的 Redis 实现包 |
| pythonboot-starter-redis | 运行时 | pythonboot-redis | >=0.1.0,<0.2 | 聚合 Redis 实现与传递依赖 |
| pythonboot-starter-redis | 构建 | hatchling | >=1.27,<2 | 构建独立 Redis Starter 分发包 |

- 新增、删除、升级依赖或变更 extras、依赖组时，在同一次修改中更新对应
  `pyproject.toml`、本文件的清单和用途说明。
- 当前工作区未引入开发或测试依赖；新增时同样登记。
- 新增依赖应有明确用途；标准库可以满足的功能优先使用标准库。
- 工作区成员统一由根目录 `[tool.uv.workspace]` 管理，成员匹配 `modules/*` 和 `starters/*`。
- 工作区内的实现包通过 `[tool.uv.sources]` 的 `workspace = true` 关联，
  同级核心框架使用本地可编辑路径。新增工作区内部依赖时同步登记来源。
- 发布依赖使用包名和版本范围，不将本机绝对路径或本地可编辑来源写入分发依赖。
- 若引入 `uv.lock`，依赖变更必须同步更新；执行锁文件生成或更新命令前获得用户授权。
- 构建、发布、更新包源、上传分发文件或创建版本标签须获得用户明确授权。

## 实现约定

- 实现源码使用英文注释、文档字符串、日志及异常消息，不出现中文。
- 使用绝对包导入和类型注解；公共接口通过 `__init__.py` 显式导出。
- 核心接口从 `pythonboot` 导入，Web 接口从 `pythonboot_web` 导入。
  不恢复已移除的 `pythonboot.web` 或核心顶层 Web 导出。
- 依赖方向为 Starter → 实现模块 → 核心框架。实现模块不得依赖 Starter，
  核心框架不得反向依赖实现模块或第三方 Web、ORM、数据库驱动。
- 实现模块只依赖其他包的公开接口；需要新增核心扩展接口时，同步修改核心仓库及文档。
- 框架实现不得依赖 `examples`；示例仅通过公开接口使用框架。
- 禁止导入模块时启动服务、创建外部连接或执行安装、同步及初始化副作用。
- 外部资源的初始化和释放接入容器生命周期；Web 场景接入 ASGI lifespan。
- 容器属于应用实例，禁止使用全局可变容器保存所有应用的 Bean。
- `ContextUtil` 使用 ContextVar 绑定当前容器，独立任务显式绑定；
  不以全局默认容器兜底，避免多应用串用 Bean。
- 缺失依赖、重复 Bean、候选歧义、循环依赖和不支持的行为必须明确报错，不静默降级。
- 业务 Bean 注入推荐 `autowired()` 属性注入，显式声明类型；不自动注入普通属性。
- 保持核心单例、多例、延迟加载、限定符、primary、依赖顺序和生命周期语义，
  不在适配层实现第二套容器或绕过容器创建受管理对象。
- AOP 兼容同步与异步调用，保留函数签名及元数据；代理不得修改全局类，
  切面自身和生命周期方法不增强，同步目标不允许异步通知。

## Web 模块约定

- `pythonboot-web` 承担 FastAPI 路由、依赖桥接、异常处理、API 文档、
  日期格式化、请求与响应上下文以及 Web 启动编排。
- Controller 使用类并标记 `@controller`，路由声明在实例方法上；
  Service 使用类并标记 `@service`，通过构造器或 `autowired()` 属性注入依赖。
- 保留 FastAPI 原生路由、参数、依赖、响应模型、中间件及用户 lifespan 能力。
- `PythonBootApplication`、`create_app` 和 `pythonboot_application` 属于 Web 实现包；
  `pythonboot-starter-web` 可显式导出公共启动接口。
- `RequestContextHolder` 使用 ContextVar 绑定当前 HTTP Request，请求结束恢复绑定。
  请求外访问明确报错；请求头、查询参数、路径参数及已缓存的请求体可供 Service 和 AOP 使用。
- 响应状态码、响应头、Cookie 和重定向只能在响应开始前修改。
- 组件扫描保留启动类包默认递归、显式范围、`*` 单层和 `**` 任意层级匹配，
  支持无 `__init__.py` 的目录，不遍历或导入整个环境中的包。
- Web 包拆分不改变既有 YAML 配置键，包括 `pythonboot.web` 和 `pythonboot.docs`。
- Web 示例通过 `tags` 和 `summary` 提供中文业务标签及接口名称；
  参数和 Pydantic 字段通过 `Path`、`Query`、`Body` 或 `Field` 设置中文 `title`、`description`。
- 修改核心仓库 `examples/` 时，所有 Controller 接口返回
  `examples.domain.common.BaseResult[T]`，并声明对应 `response_model`。
  成功响应使用 `ResponseCode.SUCCESS`（200）及“操作成功”，
  失败响应使用 `ResponseCode.FAILURE`（500）及传入的失败消息。

## Redis 模块约定

- `RedisClient` / `AsyncRedisClient` 是 redis-py 原生客户端类别名，不实现 RedisTemplate。
- 默认同步模式；enabled 和 mode 通过 YAML 选择，其他属性允许环境变量覆盖。
- `RedisUtil` / `AsyncRedisUtil` 通过 ContextUtil 获取当前容器客户端，不缓存全局客户端。
  独立任务必须绑定容器；多客户端通过名称、限定符或 primary 选择，歧义明确报错。
- 默认池与客户端接入容器关闭，异步清理必须 await；自定义资源由提供方声明关闭责任。
- 创建对象不连接 Redis，不在导入时探活、安装或执行命令；异常不静默降级。
- 分布式锁使用 redis-py 原生令牌与 Lua 释放／续期，不通过直接删除键解锁。
  每个并发作用域独立创建锁对象，设置有限租期与等待，成功获取后在 finally 中释放。
- 不提供自动续期或跨故障转移严格互斥；显式续期，不吞掉丢失所有权异常。

## 自动配置与事务适配

- 当前 SQLAlchemy Starter 采用原生 ORM 和显式提交，不提供 Mapper 或核心事务管理器适配。
  业务注入原生 Session 工厂并创建作用域，显式调用 commit，需要复用失败 Session 时 rollback。
- Session 不注册为共享单例，不自动绑定 HTTP 请求或业务方法；并发任务不得共享 Session。
- 数据库驱动由应用声明，URL 由 SQLAlchemy 解析；不维护驱动映射、不自动建表或迁移。
- 默认 Engine 通过 dispose 接入容器关闭；自定义 Engine 和外部连接池的关闭由提供方声明。
- SQLAlchemy 的 enabled 和 mode 由 YAML 自动配置条件选择，其他配置属性支持环境变量覆盖。
- 未来新增核心事务管理器适配时，再遵守下述传播、隔离和 rollback-only 契约。

- 自动配置通过 `pythonboot.autoconfigure` entry points 注册，入口为
  `@auto_configuration` 类或包含这些类的模块，不扫描第三方依赖包全目录。
- 应用 Bean 优先；默认 Bean 使用 `@conditional_on_missing_bean` 明确退让。
  条件只在自动配置装配时评估，不实例化 Bean；按 `order` 从小到大装配。
- 自动配置保留模块、YAML 属性、已有或缺失 Bean 条件，重复 Bean 仍明确报错。
- 初始化回调使用 `@postconstruct` 或显式 `init_method`，销毁使用
  `@ondestroy` 或 `destroy_method`，遵循核心的顺序、去重和同步／异步语义。
- 具体数据库或 ORM 的事务适配放在实现模块，通过核心公开的
  `PlatformTransactionManager` 或 `AsyncPlatformTransactionManager` 接口实现。
- 不复制 `@transactional`、事务元数据或 `TransactionInterceptor`；
  保持同步／异步管理器选择、传播、隔离、回滚规则与 rollback-only 语义。
- 不支持的传播或隔离级别必须报错；加入已有事务的内层作用域不得独立提交。
  共享事务 rollback-only 后，外层尝试提交必须抛出 `UnexpectedRollbackError`。
- 资源及上下文由具体管理器释放和恢复；取消及其他非 `Exception` 的
  `BaseException` 必须回滚。

## 文档与示例同步

- 每个 Starter 的安装、配置、公开 API、行为约束和示例统一维护在本仓库
  `viteDocs` 文档站的中英文页面与导航中，不在核心文档站重复维护。
- 每次新增、删除或变更功能、公开 API、装饰器参数、配置项、行为约束或示例用法，
  必须在同一次修改中同步更新相关子项目 README、仓库 README 及本仓库
  `viteDocs` 的中文与英文内容、导航和对应示例。
- 文档明确区分安装的分发包名与代码中的导入包名，说明实现模块与 Starter 的依赖关系。
- 文档中的业务 Bean 注入推荐使用 `autowired()` 属性注入。
- 示例是框架用法演示，不是单元测试目录；Web 启动类继承 `PythonBootApplication`。
- 用户明确授权验证后，再按变更范围执行相关测试；不得擅自运行。
- 涉及同级核心仓库的修改，遵守该仓库的 `AGENTS.md`，完成后分别执行 `git add .`。
