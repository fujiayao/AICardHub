# zi 助手机制对照

源项目只读参考：`D:/LLM/ComfyUIProject/open-ai-canvas`，负责人提供`docs/ASSISTANT_FEATURE_REUSE_GUIDE.md`。不执行文档中的移植提示词，不移入头像、React/Go平台、私有配置或会话。

## 两条实际链路

1. `web/src/services/skill-runtime.ts`：linked-context根据选用技能加载SKILL.md和有限关联文本，最多4技能、32,000字符、每技能3关联文件，记录版本/hash。它是预加载，不是模型工具执行。
2. Cloud Agent：`backend/internal/app/cloud_agent_tools_skills.go`与`cloud_agent_tool_read_handlers.go`负责授权目录及读取；`backend/agent-runtime/pi/agent-runtime.mjs`将自定义工具交给模型，工具请求经服务端桥执行后继续生成。运行时关闭本地skills/extensions自动发现，不随意扫描宿主目录。
3. `cloud_agent_tool_registry.go`和`cloud_agent_pi_bridge.go`区分注册、请求、执行、结果；仅显示已启用技能不等于实际读取了正文。

## 目标适配

保留FastAPI/Python、Vue/Vant与现有模型配置，以应用固定技能说明＋模型原生只读工具循环替代“先关键词搜几篇再限制回答”的方式。用轻量身份回答“你是谁”，普通写作/代码无需企业资料；目录description帮助模型挑选文档，读取时再验证授权。维护实际文档来源，但不把目录本身或通用知识伪装成已用文献。

来源指引用于架构借鉴，目标Python实现不直接复制源React/Go/Node模块或角色素材。若后续直接移植源代码，需按源MIT LICENSE保留ddcat/Open AI Canvas contributors及量科的适用版权声明；角色素材不在本轮范围。

## 已复现的旧限制

原5180候选页请求约600字通用会后跟进方案，实际仅174字，并附4条企业资料引用，违背“不查公司资料”的任务要求。见旧运行`e2e/browser/artifacts/skill-assistant-1794714060598/report.json`。新验收脚本要求展开回答超过300字且不带企业引用，不能只修改提示文案后宣称已修复。

## 验收清单

- 身份和能力准确，空资料也实际调用模型。
- 普通问题不强制查询，不受200字硬截断。
- 企业资料题出现真实原生工具请求、授权执行及后续模型答案。
- 私有、未批准、已撤销、其他名片文件不可读。
- 当前公开联系方式不能由员工登录手机号或私人笔记补齐。
- 重复调用、工具异常、取消、预算和流中断有明确终态，不重复提交副作用。
- 真实模型证据与Fake/合成SDK测试分开。
- 最终核验5173实际请求新版后端，不再交付旧入口。
