# server/AGENTS.md —— 后端补充规则

> 在根目录 AGENTS.md 之后阅读。T08 审查后会补充“范本写法”。

- 模块结构：`modules/<模块>/{router,schemas,service,repo,models}.py`，照 `modules/card/` 写
- router：只做参数接收、调用 service、返回 schema；必须写 `operation_id`、`response_model`
- service：业务逻辑；不 import fastapi；需要数据库会话时作为参数传入
- repo：只做查询；“员工自己的数据”函数必须有 `employee_id` 参数
- models：`Mapped[...] = mapped_column(...)`；关系默认 `lazy="raise"`，查询时显式 `selectinload`
- 错误：`raise AppError(ErrorCode.XXX)`，新错误码登记在 `core/errors.py`
- 异步中的同步操作（pymupdf、python-docx、Pillow、bcrypt、git）用 `run_in_threadpool`
- 流式生成器内自行 `async with SessionLocal()`
- 测试：`tests/unit/`、`tests/api/`；测试名用中文描述规则；只用 FakeLLMClient；接口测试含正常、参数错误、未登录、越权
- 迁移：每个任务最多一个迁移文件；提交前 `alembic heads` 只有 1 个；不得修改已合并的迁移
- 命令：`uv run pytest`、`uv run ruff check --fix`、`uv run ruff format`、`uv run mypy app`
