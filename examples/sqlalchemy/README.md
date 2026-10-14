# SQLAlchemy 示例 / Example

安装 `pythonboot-starter-web`、`pythonboot-starter-sqlalchemy` 和 `aiosqlite`。
项目根目录为模块搜索路径，ASGI 入口是 `examples.sqlalchemy.application:app`。
数据库文件路径相对于进程工作目录。示例不自动建表，也不在导入时连接数据库。

先通过应用自己的迁移工具或 SQLite 客户端在 `example.db` 中准备表和数据：

```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL);
INSERT INTO users (id, name) VALUES (1, 'Alice');
```

`GET /users` 查询后关闭 Session；`PUT /users/1` 接收 `{"name": "Bob"}`，显式提交。
没有 Mapper、隐式事务装饰器或自动提交；未提交事务随 Session 关闭回滚。

Install `pythonboot-starter-web`, `pythonboot-starter-sqlalchemy`, and `aiosqlite`.
Use the repository root as the module search path and `examples.sqlalchemy.application:app`
as the ASGI entry point. The database file is relative to the process working directory.
Prepare the table and seed data with your migration tool or SQLite client using the SQL above.
No tables are created automatically and no database connection is opened during import.
Reads close their Session; renames explicitly commit. Uncommitted work is rolled back on close.


## 分页 / Pagination

`GET /users/page?page=1&pageSize=10` 返回 `Page[UserView]`，包含 total、page、pageSize、rows。
业务通过 `apaginate(session, select(User).order_by(User.id), PageQuery(...), mapper=UserView.model_validate)`
查询并在 Session 内转换 DTO；不传分页参数时默认第 1 页、每页 10 条。
The example demonstrates async pagination using PageQuery, Page and apaginate with a DTO mapper.
