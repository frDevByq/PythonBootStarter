# Redis 示例 / Example

安装 `pythonboot-starter-web` 和 `pythonboot-starter-redis`，并准备 Redis 服务。
修改 `config/application.yml` 中的 URL；默认连接本机 6379、数据库 0。
模块搜索路径为仓库根目录，ASGI 入口为 `examples.redis.application:app`。

- `GET /redis/messages`：通过注入的原生 `AsyncRedisClient` 查询 List。
- `POST /redis/messages`：接收 `{"value": "hello"}`，通过 `AsyncRedisUtil` 获取原生锁、
  写入带 TTL 的字符串并追加 List，最后释放锁。

示例不会在模块导入时连接 Redis。锁只提供互斥，两个写入命令并非原子事务。
所有参与该业务的写入方都应使用同一锁键；业务不能超过锁租期，必要时显式续期。

Install `pythonboot-starter-web` and `pythonboot-starter-redis`, prepare a Redis server, and
configure its URL in `config/application.yml`. Use the repository root as the module search path
and `examples.redis.application:app` as the ASGI entry point.
GET lists queue values through an injected native client; POST acquires a native lock through
static utilities, writes a TTL string, appends to the List, and releases the lock.
No connection is opened during module import. The lock provides mutual exclusion, not atomicity
across the two commands. All writers must use the same lock key and stay within or explicitly extend the lease.
