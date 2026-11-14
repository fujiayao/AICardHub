# AGENTS.md —— 数科 AI 智能名片

> 本文件放在代码仓库根目录。所有参与开发的 AI 智能体每次开工前必须完整阅读。
> 详细依据见 `docs/工程框架方案.md`；本文件与其冲突时以 `docs/工程框架方案.md` 为准，并提出问题。

## 项目是什么

数科员工的“AI 分身”数字名片。访客通过 NFC / 二维码 / 链接打开 H5 名片，可与员工的 AI 分身对话、留下联系方式；员工在员工端 H5 维护名片和 AI 助手、跟进线索；管理员在后台维护企业信息、AI 模板和公司知识库。仅数科内部使用，一期只有 H5，不涉及小程序、服务号、企业微信。

## 必读文档

| 文档 | 管什么 |
|---|---|
| `docs/工程框架方案.md` | 技术选型、目录结构、编码规则、协作流程（最高优先级） |
| `docs/业务流程与开发方案.md` | 业务流程、数据模型（§8）、接口清单（§9）、知识库规则（§6） |
| `docs/UI设计规范.md` + `docs/H5原型.html` | 页面、组件、交互、视觉 tokens |
| `docs/adr/` | 已批准的偏离方案的决定 |

## 技术栈（不得更换，不得引入同类替代品）

- 后端：Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.0 异步、Alembic、asyncmy、MySQL 8、httpx、openai SDK、APScheduler 3.11、uv、ruff、mypy、pytest
- H5（apps/h5）：vue3-vant-mobile 模板（Vue 3 + Vite + Vant 4 + Pinia + Vue Router 文件路由 + UnoCSS），pnpm
- 后台（apps/admin）：pure-admin-thin 模板（Vue 3 + Element Plus），pnpm
- 不使用：Redis、LangChain/LlamaIndex、SQLModel、第二个 UI 库或图标库、SQLite（含开发环境）

## 目录约定

```text
server/app/core/          基础设施（未经允许不要改）
server/app/modules/<模块>/ router.py → service.py → repo.py → models.py，schemas.py
server/app/kb/            知识库引擎（纯 Python，不 import fastapi）
server/app/integrations/  llm/、storage/（测试用 Fake 实现替换）
server/tests/acceptance/  验收测试（禁止修改）
contracts/openapi.json    生成文件（禁止手改）
apps/*/src/api/generated/ 生成文件（禁止手改）
apps/h5/src/pages/        文件路由；页面首行注释写原型编号
apps/h5/src/platform/     唯一允许判断运行环境的地方
```

## 常用命令

```bash
docker compose -f deploy/docker-compose.dev.yml up -d   # 启动开发数据库
cd server && uv run fastapi dev app/main.py             # 后端
cd server && uv run alembic revision --autogenerate -m "xxx"  # 新增迁移
cd apps/h5 && pnpm dev                                   # H5
cd apps/admin && pnpm dev                                # 后台
scripts/gen-api.sh                                       # 导出 OpenAPI 并生成前端类型
scripts/check.sh                                         # 交付前必须全部通过
```

## 必须遵守

1. 开工前读本文件、任务卡、任务卡引用的方案章节和原型页面。不清楚就停下来问，不要猜。
2. 只改任务卡允许修改的目录。需要改别处时停下，在交付说明里提出。
3. 不得偏离文档。确需偏离，先在 `docs/adr/` 写决策记录并等待确认。
4. 不得新增依赖，除非任务卡允许或已有 ADR。
5. 接口改动走契约流程：改 schema（`response_model`、`operation_id` 必填）→ `scripts/gen-api.sh` → 提交生成结果。
6. 路由只做参数接收和调用 service；service 不 import fastapi；模块之间只能调用对方的 service。
7. `/me/**` 接口只用 `current_staff.id` 过滤数据，并为每个接口写“访问他人数据返回 404”的测试。
8. 业务错误抛 `AppError` 并在 `core/errors.py` 登记错误码；不得吞掉异常。
9. 成功响应直接返回数据，不包 `{code,data,msg}`；分页统一 `Page[T]`；JSON 字段 snake_case；时间存 UTC、返回带时区 ISO 8601。
10. 异步代码中禁止 `requests`、`time.sleep`；pymupdf / python-docx / Pillow / bcrypt / git 用 `run_in_threadpool`。
11. 流式对话的生成器内自行 `async with SessionLocal()`，不用依赖注入的会话。
12. 定时任务只写在 `app/jobs/`，只由 `app.scheduler` 进程运行，不在 FastAPI 启动时启动调度器。
13. 知识库文件只通过 `app/kb/store.py` 读写，写入加 filelock。
14. 测试中只用 `FakeLLMClient`，不调用真实大模型。
15. 前端：只通过 `api/generated` 调接口（SSE 只用 `api/sse.ts`）；不写 `any`、`@ts-ignore`；不写颜色字面量；单文件 ≤ 300 行；访客页不得引用员工端代码；只用 Vant（H5）/ Element Plus（后台）。
16. 不得编造公司业务内容；不得硬编码密钥、域名、模型名。
17. 不得修改 `tests/acceptance/`；不得放宽断言或 mock 被测对象来让测试通过。
18. 同一问题连续两次修复失败，停止修改，报告现象、已尝试方法和怀疑原因。
19. 交付前 `scripts/check.sh` 全部通过；前端任务附 390×844 截图并与原型对比。

## 禁用写法

| ❌ 禁用 | ✅ 使用 |
|---|---|
| Pydantic `class Config` / `orm_mode` / `.dict()` / `parse_obj` / `@validator` | `model_config = ConfigDict(...)` / `from_attributes` / `.model_dump()` / `model_validate` / `@field_validator` |
| `from pydantic import BaseSettings` | `from pydantic_settings import BaseSettings` |
| `session.query(...)`、`Column(...)`、`declarative_base()` | `select(...)` + `await session.execute/scalars`、`Mapped[...] = mapped_column(...)`、`class Base(DeclarativeBase)` |
| 异步中依赖懒加载关联 | `selectinload(...)`；关系默认 `lazy="raise"` |
| `@app.on_event("startup")` | `lifespan` |
| APScheduler 4.x API | APScheduler 3.11 `AsyncIOScheduler` |
| Options API、Vuex、`this.$router` | `<script setup lang="ts">`、Pinia、`useRouter()` |
| Vant `Toast()`、`Dialog.confirm()` | `showToast()`、`showConfirmDialog()` |
| H5 中手写 routes 数组 | `src/pages` 文件路由 |
| `print(`、`console.log`、无编号的 `TODO` | logger；删除；`TODO(任务编号)` |

## 角色与任务

- 本项目有三个智能体角色，各自的职责、可修改目录和标准流程见 `.agents/roles/`：`integrator.md`（集成与质量）、`backend.md`（后端）、`frontend.md`（前端）。启动提示词会告诉你是哪个角色
- 任务卡在 `tasks/T*.md`；看板 `tasks/BOARD.md` 只由集成智能体和项目负责人更新
- 每个任务一个分支：`git switch -c feat/T{xx}-<英文短名> main`；交付报告写 `tasks/reports/T{xx}.md`；前端截图放 `tasks/reports/screenshots/T{xx}/`
- 审查意见在 `tasks/reviews/T{xx}-r{n}.md`（被打回时先 `git rebase main` 再读）
- 执行顺序与协作方式见 `docs/开发执行计划.md`

## 交付说明格式

```markdown
## 任务 {编号} 交付说明
- 完成内容：{逐条对应验收标准}
- 修改文件：{列表}
- 数据库迁移：{文件名 / 无}
- 接口变更：{operation_id 列表 / 无}
- 检查结果：{check.sh 输出末尾}
- 截图：{路径}
- 未完成 / 风险 / 需要确认：{如实写，没有就写“无”}
```
