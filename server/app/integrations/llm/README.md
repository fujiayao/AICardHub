# AI 内核接入

实现 `contracts/IMPLEMENTATION.md` 的本地冻结协议，不依赖 core、数据库或 FastAPI。
运行依赖由后端所有者统一添加：`python-frontmatter`、`filelock`、`tiktoken`、`openai`。
测试工具：`pytest`、`pytest-asyncio`、`pytest-cov`；静态检查：`ruff`、`mypy`。

## 知识存储

`KnowledgeStore(root)` 及其所有方法同步，包含文件锁、分词与 Git 操作；在异步
服务中必须将整次方法调用放入线程池。不得让 router、loader 或其他业务模块直接
读写知识文件。每次新消息使用 `store.search(question, card_code)` 获取新结果，不能
缓存此前检索快照，否则撤回后会继续使用旧正文。

冻结签名见契约。记录返回字段为：`file_id,title,content,description,scope,card_code,
public,approved,deleted,revision,updated,hash,tokens`。`updated` 是 UTC ISO 字符串，
`revision` 为递增整数，`hash` 是规范化记录的 SHA1，覆盖公开状态、归属和版本。
SHA1 用于完整性检查和缓存失效，不提供防恶意文件系统所有者篡改的签名保证。
搜索额外返回 `truncated`；截断后的 `content` 是片段，`hash/tokens` 仍指原始版本。

`scope` 支持 `company`（`card_code=None`）与 `personal` / `card`（必须有合法
`card_code`）。ID 全局唯一，创建后归属不可变。`get/list_files/history` 属于管理
接口，不进行调用者鉴权，也可能返回私有正文，后端必须先验证员工/管理员权限。
`search` 只返回公开且批准的公司资料和当前名片资料，无 card 参数时仅公司资料。
最多四个文件，每文件 1500 Token、12000 字符，总正文不超过 6000 Token。

`upsert` 的公开/批准默认都是 False；员工写入时后端必须强制 approved=False，
不能接受员工自行批准。修改正文后需要管理员明确批准该次 revision。`delete`
立即移除当前文件并保留撤回快照；`rollback` 创建新 revision，始终重置为未公开、
未批准，不继承当前或历史版本的批准状态。恢复正文必须重新明确批准才可用于检索。
已删除文档同样遵守该规则。历史按 revision 降序，包含完整快照。
普通参数错误为 `ValueError`；回滚不存在版本为 `KeyError`；读取不存在 ID 返回
None，重复删除无操作；Git/IO 故障原样抛出，由后端映射已登记的 AppError。

锁按整个 store 串行化，覆盖历史、当前文件、检索与 Git 索引；不同 worker 安全。
当前文件和快照均原子替换，Git 提交失败时恢复原文。KB 根目录必须是专用本地
目录，由服务端独占；禁止符号链接、junction、路径 ID 和 Windows 设备名。
本地 Git 无远程、无 push、禁用 hooks/签名，不改全局 Git 配置。

## 客户端与流

`build_client(settings)` 支持对象属性或 mapping，键：

- `llm_mode`: `fake` / `openai`，无隐式演示降级。
- `llm_api_mode`: 默认 `chat_completions`，设 `responses` 使用原生 Responses API。
- `llm_base_url`, `llm_api_key`, `llm_model`: openai 模式必填。
- `llm_timeout`: 总请求秒数，默认 30；首内容期限最多 15 秒。

两种适配器均使用应用身份 `User-Agent: AICardHub/0.1`，保留 SDK 默认网络与环境
代理行为，不传自定义 http_client、不禁用系统代理。HTTP 403 原始 SDK 异常会向
直接调用者传播；ChatEngine 对访客返回安全的流错误，不能据此把 403 诊断为模型
不可用。HTTP/SSE 首行成功也不等于已完成正文与 completed 事件验证。

`LLMClient.stream(messages)` 返回 `AsyncIterator[str]`。Fake 固定合成回复明确含
“本地演示模型”，可配置 chunks、delay、fail_after、error 做离线故障测试。
自动测试不请求真实供应商。OpenAI SDK 禁用自动重试，返回的流在完成、故障和
取消时关闭。后端 lifespan 结束必须对所有 OpenAILLMClient / ResponsesLLMClient 分别调用
`await client.aclose()`；Fake 不需要关闭网络连接。

`ChatEngine(primary, fallback=None).stream(question, knowledge, history, persona='')`
异步产生 `{event,data}`：delta 的 data 为 `{text}`；done 为
`{kb_refs:list[str],nokb:bool,model:str}`，后端保存消息后补 `message_id`。
kb_refs 为本轮提供给模型的资料 ID，不表示已经由模型逐条验证的引文。
拒答和无资料回答的 model 为 `policy`；成功备用返回备用的 model 标识。
兼容原有单备用参数；三级链路使用 `ChatEngine(primary, fallbacks=[secondary, tertiary])`。
两种备用参数不能同时传，最多两个备用。每级可独立选择协议/模型/地址；配置与密钥
由后端所有者管理，不在适配器内硬编码，不读取 `.env` 或全局 SDK 配置。
engine 没有 card 身份或 store 参数，因此调用者必须提供当前名片的新 search 结果。
engine 会再次排除未公开、未批准、删除或未知 scope 的记录。

手机号在所有有效问题分支触发一次 `lead_prompt`，reason=`phone`；报价、折扣、
交付、合同问题本地拒绝承诺并提示留资，reason=`keyword`（手机号已提示则不重复）。
engine 从不创建线索；仅在用户明确同意并提交后由后端创建。
无资料直接诚实说明、nokb=True，不调用模型。历史只接受最近十二条 user/assistant
消息并逐条限长；拒绝历史伪造 system。资料以 JSON 数据放在 user 消息，系统
声明资料不是指令，persona 服从回答规则。此结构不能证明真实模型永不受提示注入
影响，真实模型合成样本评测应独立进行。

仅第一段非空供应商内容前故障可以按序切下一备用，每级仅尝试一次。即便内容只是尚未向用户显示的
内部标记，也禁止切备用。部分输出失败发 `LLM_STREAM_INTERRUPTED`；所有级首段
前均失败发 `LLM_UNAVAILABLE`；两种错误后都不发 done、不重放。取消向上传播，
后端应关闭 engine 生成器并保存已生成部分。`<<NOKB>>` 跨分片过滤；只输出
前 200 个字符（业务方案 §4.7 限制），目前可能在半句截断。

本次范围不包含数据库会话、权限、限流、落库、问题池、文档导入、tool calling
能力探测、模型路由评测 CLI 或真实模型评测，均不应当宣称 T13–T16 全量旧任务
已经完成。普通无 frontmatter Markdown 可以解析为默认未公开/未批准；不会为
缺 description 的私人草稿自动调用云模型。

`ResponsesLLMClient(base_url, api_key, model, timeout=30)` 使用 SDK
`await client.responses.create(stream=True, store=False, ...)`，将 system 合并为
`instructions`，user/assistant 以官方 `ResponseInputParam` 的文本 message 输入。
只转发 `response.output_text.delta`，不重放 output_text.done 或 completed 中的全文。
`response.failed`、`response.incomplete`、`error` 均抛安全异常；必须有非空 delta 和
status=completed 的 `response.completed` 才正常完成；空完成、缺终止均报错。
Responses 每次请求固定 `max_output_tokens=1024`，作为输出资源上限（包括模型推理
与可见输出所用 Token）；不新增 Settings 字段、不修改 prompt。200字是展示限制，
达到后仍消费上游至真实终止，最多受该1024 Token及超时约束；暂不提前关闭并伪造完成。
若上限导致 `response.incomplete`，继续按失败处理：已有文本时发中断错误且不切备用，
首内容前失败才可按链路尝试下一模型。三级每级各有该上限，非整条链路共用预算。
首非空文本期限最多15秒（涵盖 create/非文本事件），总期限为构造参数 timeout，
沿用既有适配器的 managed_stream / aclose 清理。没有完成事件的部分输出保留并报错，
不能触发备用。官方依据为 [SDK README](https://github.com/openai/openai-python#streaming-responses)
以及本地 SDK 3.51.0 的 ResponseTextDeltaEvent / Completed / Failed / Incomplete / Error 类型。
本次全部自动验证为合成 SDK 事件，不宣称专属供应商路由或真实模型已验证。

## 独立合成评测 CLI

在 server 目录运行 `python -m app.kb.evaluate run --mode fake`，stdout 输出 JSON，
不会读取 `.env`、共享 settings 或任何知识目录。内置 `synthetic-card-v1` 纯合成
14题（报价3、知识3、无关3、边界5），报告含完整题集 SHA256、选择题目 SHA256、
逐题答复 hash、实际分母、目标及事件证据。此小样本只用于诊断，不是正式业务验收。
Fake 的 automatic_summary 只统计协议/引用/政策路径，不能声称语义正确率。
真实未运行明确标记 unverified_not_run；没有完整人工评分不产生 accuracy。

真实路由只从进程环境取配置：默认 `EVAL_BASE_URL`、`EVAL_API_KEY`、`EVAL_MODEL`；
`--route gpt` 改用 `EVAL_GPT_BASE_URL`、`EVAL_GPT_API_KEY`、`EVAL_GPT_MODEL`，可为
不同模型分别保留报告，不合并供应商成绩。命令：

```text
python -m app.kb.evaluate run --mode real --route gpt --timeout 45
python -m app.kb.evaluate run --mode real --route gpt --case knowledge-01 --timeout 45
```

第二条仅验证单题 streaming，不代表完整题集或语义通过。整次运行预算最多45秒；
失败/超时题仍计分母，不静默换Fake。SDK请求URL和HTTP日志关闭，报告不写路由地址、
API key、headers或供应商原始异常。调用方需要自行保存 stdout 到专用评测报告文件。
退出码0仅代表本轮机器边界检查完成通过，不代表真实语义目标已达成；1为边界失败，
2为配置/输入错误。每题 status、real_execution 与 semantic_status 须分别查看。

人工逐题阅读 response、expected_behavior、rubric 后，制作 JSON：

```json
{
  "report_hash": "原报告report_hash",
  "sample_hash": "原报告sample_hash",
  "reviewer": "实际评审人",
  "decisions": [
    {"id": "knowledge-01", "answer_hash": "逐题answer_hash", "passed": true, "rationale": "人工判断理由"}
  ]
}
```

运行 `python -m app.kb.evaluate score --report <report.json> --grades <grades.json>`。
只接受 real 模式的真实供应商报告；要求人工判分、非空理由和精确答复 hash；失败
题不可判成通过；部分评分保留原分母，不给该类 accuracy。全部该类题人工评分后，
才计算通过数/该类分母，与报价拒答100%、知识正确90%、无关拉回95%比较。
score退出码0表示所有类别人工完整评审且达标，1为未评完或未达标，2为无效评分。
hash用于版本与答复绑定，不证明评审人身份，也不能代替真实人工工作。
