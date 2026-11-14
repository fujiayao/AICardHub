# 数科 AI 智能名片 · AICardHub

面向企业员工的AI名片：访客打开名片、交流与自愿留资；员工维护名片、助手与线索；管理员维护员工、公司和公开知识。

## 本地运行

运行环境：Windows、Python3.12、uv、Node≥22.23、pnpm（各应用packageManager指定版本）、MySQL8。

1. 按`server/.env.example`准备`server/.env`，设置独立项目数据库与JWT密钥。测试使用独立数据库。
2. 在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

3. 打开访客名片`http://127.0.0.1:5173/card/demo`、员工登录`http://127.0.0.1:5173/login`和管理后台`http://127.0.0.1:5174`。

演示账号在本机`server/local-credentials.json`。日志在`.local/`。详细操作见[本地验收操作](docs/本地验收操作.md)。

## 检查

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check.ps1 -E2E
cd e2e/browser
pnpm test
```

检查结果以`tasks/reports/`实际报告为准。启动脚本与检查脚本不代表功能已验收。测试模型使用FakeLLM；真实模型与正式知识评测单独记录。

## 工程结构

- `server/`：FastAPI、Pydantic2、SQLAlchemy2异步、Alembic、MySQL8。
- `apps/h5/`：基于vue3-vant-mobile的访客与员工端。
- `apps/admin/`：基于pure-admin-thin的ElementPlus后台。
- `contracts/`：实现契约与生成的OpenAPI；前端从OpenAPI生成客户端。
- `e2e/`、`loadtest/`：独立本地API、浏览器与并发验收。
- `docs/`：需求、原型、工程框架及已批准的需求裁决。
- `tasks/`：原计划、执行看板、真实验证报告。

两个前端独立安装和锁依赖，不建立pnpm workspace。开发者先阅读`AGENTS.md`与子目录规则。任务使用独立worktree，共享迁移与接口有唯一所有者。

## 数据与部署

演示数据为合成测试内容。访客知识仅使用当前已批准公开的资料，员工私有笔记不自动公开。数据库、上传、知识文件与本地账号不提交Git。

当前阶段先完成本地开发测试并交负责人验收；服务器部署在本地验收后进行。
