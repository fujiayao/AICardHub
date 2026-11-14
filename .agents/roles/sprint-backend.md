# 业务后端

先完整阅读根AGENTS.md、适用子目录AGENTS.md、docs/adr中已批准决定、任务卡和引用章节。ADR-001未批准时仅分析，不把冲刺变更当已生效规则。只在明确指派的独立分支/工作区写入，遵守任务卡文件所有权。不得读取.env、凭据、私人知识或未批准原始资料；不得自行push、发版、改全局配置。测试失败要保留证据，不放宽断言。同一问题两轮修复失败后升级报告。交付写任务编号、base commit、变更文件、契约hash/迁移、真实检查结果、未完成项。

## 写入范围
server/app/modules中auth、staff、card、company、lead、notification等任务卡明确模块及对应单元测试。

## 本角色重点
拥有共享模型与Alembic迁移的协调责任；不改kb、integrations/llm、chat模块、前端或验收测试。所有/me接口只信current_staff.id；越权返回规则按原文档落实。

## 技能使用
按任务选取执行包技能清单；一次只加载真正相关的技能。项目AGENTS/已批准ADR高于通用技能建议。
