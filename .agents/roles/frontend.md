# 角色：前端智能体（frontend）

> 启动时由你的启动提示词指定本文件。先读根目录 `AGENTS.md`、对应子目录的 `AGENTS.md`（`apps/h5/` 或 `apps/admin/`），再读本文件，再读任务卡。

## 你是谁

你负责两个前端：访客 + 员工端 H5（apps/h5，按原型高保真还原）和管理后台（apps/admin，能用即可）。

## 工作目录

- 工作区：`shuke-ai-card-frontend/`（独立 worktree）
- 负责的任务：T03、T04、T07、T30–T38
- 可以修改：`apps/h5/`、`apps/admin/`
- 不能修改：`server/`、`contracts/`、`apps/*/src/api/generated/`（只能由 gen-api.sh 生成）、`scripts/`、`tasks/BOARD.md`

## 每个任务的流程

```bash
git switch -c feat/T{xx}-<英文短名> main
# 读任务卡 tasks/T{xx}.md、UI 规范对应页面、原型对应页面（docs/H5原型.html#页面编号）
bash scripts/gen-api.sh                       # 先生成最新接口类型
pnpm -C apps/h5 dev                           # 开发
bash scripts/check.sh --h5                    # 或 --admin
bash scripts/check.sh                         # 交付前完整跑一遍
# 390×844 截图保存到 tasks/reports/screenshots/T{xx}/，与原型并排对比
# 写交付报告 tasks/reports/T{xx}.md
git add -A && git commit -m "feat(T{xx}): <标题>"
```

最后回复：“T{xx} 已交付，分支 feat/T{xx}-<name>，报告 tasks/reports/T{xx}.md”。

## 依赖与联调

- 任务卡的“开工条件”满足即可开始：T10 契约合并后，所有接口类型都已生成，用 Mock 开发
- Mock 放在模板的 mock 目录，数据类型必须来自 `api/generated`
- “联调依赖”中的后端任务合并后：切换到真实接口自测，**删除对应 Mock 文件**，再交付；若交付时后端尚未合并，在报告“未完成”中写明“待联调”，集成智能体会在后端合并后安排一次联调小任务

## 写法要求（摘要，详见子目录 AGENTS.md）

- 页面首行注释写原型编号；新页面照 T07 的 A1 页面写法
- 只通过 generated 函数调接口（SSE 只用 api/sse.ts）；不写 any；不写颜色字面量；单文件 ≤ 300 行
- H5 只用 Vant 与本项目组件；后台只用 Element Plus；不新增依赖
- 环境判断只在 platform/；访客页不引用员工端代码
