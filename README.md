# PythonBootStarters

基于 UV 管理的 PythonBoot Starter 多项目仓库。

## 结构

- `starters/pythonboot-starter-web`：Web 应用启动依赖。
- `modules/pythonboot-web`：Web 功能实现，独立发布为 `pythonboot-web`。

各 Starter 是独立的可发布 Python 包，并由根目录 UV workspace 统一管理。

`viteDocs/` 是全部 Starter 的统一中英文文档站；每个 Starter 的安装、配置、API 和示例
都在该站中维护。

依赖链：`pythonboot-starter-web` → `pythonboot-web` → `pythonboot`。
核心 `pythonboot` 保留在同级 `PythonBoot` 仓库；本地 UV sources 使用可编辑路径，
发布元数据仍使用包名和版本范围。每个实现包和 Starter 分别构建、发布到 PyPI。

应用安装 `pythonboot-starter-web`，核心接口从 `pythonboot` 导入，
Web 接口从 `pythonboot_web` 导入。本地工作区使用 `uv sync --all-packages` 同步。
