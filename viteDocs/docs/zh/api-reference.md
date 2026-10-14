# Web API 参数

| API | 参数 |
| --- | --- |
| `PythonBootApplication` | `title`、`version`、`scan_packages`、`config_dir`、`auto_configure`、`exclude_auto_configurations`、`exclude`、`**FastAPI options` |
| `create_app` | 上述参数，另有 `exclude_modules` |
| `pythonboot_application` | `scan_packages`、`exclude_auto_configurations`、`exclude` |
| `controller` | 通用 Bean 参数、`prefix`、`tags`、`**APIRouter options` |
| `controller_advise` | 通用 Bean 参数 |
| `route` | `path`、`methods`、`**FastAPI add_api_route options` |
| `get/post/put/patch/delete` | `path`、`**FastAPI add_api_route options` |
| `exception_handler` | 异常类型或状态码整数 |
| `inject` | `bean_type`、`name`、`qualifier` |
| `date_time` | 非空 `format` 字符串 |
| `ResponseContext.redirect` | `url`、`status_code` |
| `ResponseContext.set_cookie` | `key`、`value`、`**SimpleCookie options` |

`controller` 与 `controller_advise` 的通用 Bean 参数为 `name`、`init_method`、`destroy_method`、`lazy`、`scope`、`primary`、`qualifiers` 和 `depends_on`。Web API 从 `pythonboot_web` 导入；核心 Bean 声明和 `autowired()` 从 `pythonboot` 导入。


## ORM 分页 API

| API | Parameters / Fields |
| --- | --- |
| `PageQuery` | `page=1`, `pageSize=10` |
| `Page[T]` | `page=1`, `pageSize=10`, `total=0`, `rows=[]` |
| `paginate` | `session: Session`, `statement: Select`, `query: PageQuery \| None = None`, `mapper=None` (keyword-only) |
| `apaginate` | `session: AsyncSession`, `statement: Select`, `query: PageQuery \| None = None`, `mapper=None` (keyword-only), awaitable |

具体行为与示例见 [分页查询](./sqlalchemy.md#分页查询)。
