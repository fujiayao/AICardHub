# 原生部署与数据迁移进度

日期：2026-11-15。负责人授权无Docker部署与完整业务数据迁移，正式访问路径为`https://haiwex.com/aicardhub/`。

## 当前结果（SSH修复后续部署）

负责人通过VNC修复OpenSSH/OpenSSL兼容问题后，SSH重新连接成功，主机指纹与原记录一致。本轮**没有安装或升级系统包、没有修改SSH/系统库/防火墙配置**；仅创建本应用目录、应用账号、应用服务和现有Nginx里的前缀include。

应用已在`https://haiwex.com/aicardhub/`运行。访客名片`/card/5dbb1d43`、员工`/staff/login`、后台`/admin/login`、API及短链均通过公网HTTPS检查。原网站根路径仍200，原new-api、CLIProxy与SSH服务均active。Nginx真实`nginx -t`通过后平滑reload。

系统Python3.12的ensurepip因pyexpat依赖错误不可用，本轮没有修系统库；在`/opt/aicardhub/ops/tools`放置独立uv，仅将私有CPython3.12.16安装到`/opt/aicardhub/shared/python`，项目依赖放release内venv。专用MySQL实例`aicardhub-db.service`只监听`127.0.0.1:13306`，独立数据目录，未启动或改写系统mysqld实例。

API`aicardhub-api`、数据库`aicardhub-db`、独立调度`aicardhub-scheduler`均active并开机启用。最后检查占用约API215MB、DB461MB、scheduler74MB，系统可用内存约2458MB，无swap使用。服务器已生成root私有SQL和文件备份，并启用应用专用每日备份timer；14天保留，只清理其命名范围的旧备份。

### 数据与验收边界

本机MySQL80处于Stopped，当前进程无权限启动，已请负责人管理员启动。最新快照重取未成功，**服务器恢复的是此前最近一次完整备份，不保证包含该备份之后的本地新增记录**。该备份21表记录计数、4260文件SHA-256均与服务器恢复结果相等。模型密钥重加密、新JWT轮换成功；原管理员/员工账号通过公网登录验证。

公网真实`gpt-6.1-terra`两题通过：董事长身份回答正确；业务题产生真实list/read工具审计及文档引用，SSE最终done、无error。见`live-public-ai.json`。中文海报字体使用服务器已有NotoCJK文件实测加载成功。

本机Chrome无头启动失败，当前聊天的内置浏览器工具也不可用，因此本轮**没有完成上线后的真浏览器视觉/点击验收**；HTTP页面/资源/登录/API/SSE检查已过，之前本地production-prefix浏览器证据仍保留。未把这些结果混称远端浏览器验收。外部远程知识库生产接入仍未完成，运行的是本产品自己的已迁移KnowledgeStore。

Nginx真实检查发现`location = /aicardhub/`使用文件alias会拼成`index.htmlindex.html`，已改成内部rewrite到exact index，线上根入口现200；源码模板同步修正另有提交。

以下章节保留前期准备及阻塞历史，不代表当前仍然SSH不可用。

## 已完成的事实

- 对目标服务器进行了SSH只读检查并固定主机指纹。CentOS Stream 9 x86_64、4CPU、3722MB内存，检查时可用2914MB，4GB swap、52GB可用磁盘。
- 原服务器已有Nginx、new-api、CLIProxy和其他服务。80/443由现有网站及TLS流转发占用。新应用只接入既有TLS虚拟主机的`/aicardhub/`，不得取代根站或新占443。
- 已在服务器私有备份目录保存变更前Nginx配置，随后通过dnf安装Python3.12、MySQL8、Git。依赖事务同时更新OpenSSL包。
- 本地业务MySQL快照、上传文件和产品自身KnowledgeStore（保留历史及私有状态）已备份，附表计数、文件SHA-256清单。敏感归档不在Git和本报告中。详见`migration-preparation.json`的脱敏数量。
- 迁移专用脚本已私下准备：目标专用数据库凭据、JWT轮换、模型配置重加密、导入前后表计数与文件哈希校验；尚未在服务器执行。
- 主线已合入H5与后台子路径适配、FastAPI root_path和短链前缀支持，以及Linux中文海报字体选择。
- 本地生产包子路径浏览器验收通过：访客首页、AI对话刷新、员工/后台登录页面、分享短链和vCard；资源及API请求均保持在`/aicardhub/`。见`local-prefix-browser.json`。这是模拟前缀代理，不是真实Nginx或远程上线验收。
- H5 39项、后台27项测试通过，类型/lint/build通过。H5生成器用例在机器繁忙时两次触发默认5秒启动超时，临时命令行15秒超时重跑全部39项通过，未更改断言。后端全部单元322项通过；43源文件mypy及ruff/format通过，HTTP契约102操作不变。

## 当前阻塞：服务器SSH

dnf事务完成后，新的SSH连接在banner前立即断开；Paramiko和独立TCP读取均复现。主线没有修改sshd配置，也没有重启sshd；OpenSSL依赖升级与故障时间相邻，但原因尚待控制台日志确认，不能写成已证明。

主线已停止重复登录，向负责人请求通过云厂商网页控制台执行`sshd -t`、`journalctl -u sshd`及版本查询。不可通过已有网关或其他业务服务绕过SSH执行命令。域名现有HTTPS根页面检查仍返回200。

负责人再次提供目标并要求连接后，主线重新检查：部署连接程序与Windows自带OpenSSH均在密码验证前收到连接重置，后者明确返回`kex_exchange_identification: read: Connection reset`。这不是已证实的密码错误，也没有建立可执行远程命令的会话。未重复运行安装或尝试其他现有应用作为远程执行通道。

因此：**尚未导入业务数据、尚未启用AICardHub服务、尚未安装正式Nginx路径映射，也没有完成远程上线。** 不把本地测试和安装依赖等同于部署成功。

SSH恢复后，应先确认旧服务健康和新MySQL状态，再完成隔离目录/账号、运行依赖、数据库恢复、文件恢复、JWT轮换重加密及校验。先启动API验收，再启用scheduler，最后校验Nginx并接入现有TLS站点。切换前更新一致性快照，避免准备期间新增数据遗漏。

## 外部知识库检查

已有专用SSH别名连接到知识服务器健康接口成功；本地受控隧道完成MCP initialize和tools/list，列出8工具。指南中的示例`smart-business-card`项目使用现有codex-windows开发身份调用返回工具错误，未验证实际项目权限。设备清单没有产品专属只读身份。

因此暂保留产品当前自己的知识资料，**不复制外部服务器SQLite/其他项目私库，不将开发凭据放进产品，不宣称产品已接入远程知识库**。完整业务数据迁移包含本产品自己原有私有草稿与历史，状态保持不变；不意味着公开这些资料。

## 执行来源

部署模板由官方Codex CLI经Magpie的`workbuddy/deepseek-v4.1-flash`实际工具调用生成，独立标记写读校验成功；GPT-6.1-Sol完成关键方案复核。H5/后台及后端路径兼容补丁由明确范围的Codex子代理完成，不冒称所有修改都由DeepSeek生成。部署模板具体最终验证与遗留项应以其交付报告为准，未通过前不得执行。

按负责人后续指示，最终部署模板修正改由**ClaudeCode＋Magpie WorkBuddy DeepSeek V4.1 Flash**执行，Codex＋GPT-6.1-Sol监督。仅一执行进程、单核、BelowNormal，仅Read/Edit工具；48个工具回执、正常退出0。退出后串行运行一次轻量配置检查（25项）和Shell语法检查，均通过，没有并行构建或全量测试。源分支`56d3201`＋`ecb29cf`已审查合入主线`850fa57`＋`cbd2fac`。这是本地材料验证，不代表真实Nginx/systemd、恢复或上线验收。

没有把SSH密码、产品API密钥、数据库归档或原始运行环境写入本报告或版本库。未执行推送。
