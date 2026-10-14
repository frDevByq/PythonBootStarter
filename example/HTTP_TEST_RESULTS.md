# HTTP 验证记录

验证日期：2026-10-14。使用真实 Uvicorn HTTP 服务、PostgreSQL 16、Redis 7；未使用模拟客户端。

执行命令：

```bash
uv run --package pythonboot-starter-example python -m starter_example.application
uv run --package pythonboot-starter-example python example/http_smoke.py
```

结果：**9 组全部通过，覆盖 OpenAPI 中的全部 26 个业务 HTTP 操作**。

- 异步 ORM：创建、详情、筛选、PUT／PATCH、删除、显式回滚、同步接口交叉读取、404／422。
- 同步 ORM：创建、详情、筛选、PUT／PATCH、删除、显式回滚、异步接口交叉读取、404／422。
- 异步分页：默认 page=1／pageSize=10、筛选总数、5 条记录按每页 2 条遍历、尾页、超范围空页、空结果与非法参数。
- 同步分页：相同分页场景，确认 total 独立于当前页行数，字段名保持 pageSize。
- 异步 Redis：原生客户端、命名客户端解析、全部数据工具、锁获取／归属／续期／释放及数据清理。
- 同步 Redis：原生客户端、命名客户端解析、全部数据工具、锁获取／归属／续期／释放及数据清理。
- Web：生命周期、原生 middleware、请求／响应上下文、状态／头／Cookie、日期查询与请求体格式、
  重定向、自定义方法、原生 DI、独立任务、异常与参数校验。
- 文档：Swagger 页面、OpenAPI 标题、完整路径与 HTTP 方法清单。
- 并发：同步／异步 ORM 操作、Redis 独立键空间，以及不同请求的上下文隔离。

启动日志确认应用生命周期建表成功，业务日志确认同步／异步 AOP 通知执行。
测试创建的用户和 Redis 演示数据由验证流程清理。
本记录只对应当前配置与本地服务，不覆盖数据库故障、跨故障转移锁互斥或生产部署。

测试后停止应用和以下容器，保留容器与服务数据：

- `pythonboot-starter-example-postgres`：`127.0.0.1:15432`
- `pythonboot-starter-example-redis`：`127.0.0.1:16379`

后续可用 `docker start pythonboot-starter-example-postgres pythonboot-starter-example-redis` 恢复服务。

## English

All nine verification groups passed against real HTTP, PostgreSQL 16 and Redis 7, covering
all 26 documented business operations plus concurrent ORM, Redis and request context isolation.
The application and service containers were stopped after verification; containers and service data
were retained. Test-created users and Redis keys were cleaned up by the verification flow.

Sync and async pagination were verified with defaults, filtered totals, five records across multiple pages,
empty/out-of-range results, exact field names, and invalid parameters.
