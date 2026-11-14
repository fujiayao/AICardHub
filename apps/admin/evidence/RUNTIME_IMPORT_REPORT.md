# 运行时配置、导入与安全文案修复

本修复父提交 f6e7e5b63311b7a8f7a5aef4fe3044e35c3b8944（主干对应837e480）。仅apps/admin，未改server/contracts/QA/公司资料。

## 契约与实现

最终从主干真实contracts/openapi.json重新生成43个本应用所需函数；来源SHA256 **53e01e023e63f221fcd247e3f629de002a47c68aad18716d41de450c7b52bf6e**（89 operations全契约，包含VisitorData最新字段）。没有手写generated，没有重装依赖。生成器兼容multipart FormData，浏览器自设boundary；Prettier仍读取应用配置endOfLine:auto。

- Settings按后端runtime_settings.py固定keys，真实路径GET /api/v1/admin/runtime-settings、逐项PUT /admin/settings/{key}。包含主备URL/型号/密钥、模式、超时、备用启用、访客/名片/全局每日对话次数、三类retention、敏感词。移除inline_token_limit及虚构Token预算编辑。密钥转为已配置布尔标记，不进入表单值；空值/掩码不回填，不以空输入覆盖；clear_secret必须显式确认。完整连接配置后才能启用OpenAI；不提供假原子批量保存。
- Excel入口真实POST /admin/employees/import，20MB/500行与中英文表头说明，立即逐行创建、显示成功失败/原因/员工与名片编号，手机号脱敏、不展示口令。
- Markdown入口真实POST /admin/kb/upload，files multipart；逐篇校验，预览未保存；每篇单独确认后POST files保存，强制public=false/approved=false，上传声明不能授予发布权限。无一键自动发布。
- History确认文案改为“仅恢复正文为未发布草稿；重新审核批准后方可公开”，完成提示同步。浏览器回归增加私有rev1→当前已发布→回滚新rev私有未批准→SSE引用排除→重新审批才可引用的严格断言。
- 管理员改密后logout并回login提示新密码登录，不续用旧JWT。新密码/新增/重置统一8–20且至少字母数字，允许符号，登录不应用新密码规则。
- EmployeeForm关键输入姓名/手机号/部门/职务/初始密码有显式aria-label。NFC仍明确延期。

## 真实证据

runtime-settings-browser.json：OpenAI未完整配置禁止启用；保存敏感词下一次真实SSE立即阻止生成；对话次数限额保存GET及刷新仍一致；合成密钥更新后输入清空、刷新不回填原值/掩码；显式clear_secret=true清空成功。finally恢复原敏感词/限额并清除合成密钥。只使用Fake，未调用真实云模型。

import-browser.json：真实xlsx一成功一失败逐行展示；成功员工停用清理。Markdown有效与无效文件同批逐项结果，上传draft尚无持久化(GET404)，有效篇确认保存后GET核对title/public=false/approved=false；已删除合成知识。输入xlsx包含随机/合成口令的fixture仅存.gitignore的.local目录，不提交。可用create-import-fixture.py重建随机口令xlsx，不输出口令。

## 检查与待统一验收

pnpm lint/typecheck/build通过；pnpm test **13/13**，新增运行时值校验/密钥抹除/启用条件6项与multipart boundary保留1项。日志*-runtime.log。生产/390基线已在上一fix通过，本轮不再新增UI设计。

安全回滚新断言执行时，先遇到运行中的旧进程仍返回public=true；后端切新版后又发现后台知识列表500，已只读定位persona-*空正文触发NoteData.content min_length=1，未修改后端。最后主线程切换8000服务（当前连接拒绝），因此严格安全回滚浏览器复验、改密旧JWT失效UI脚本、集成新版/390统一验收留给主线程。不把这些未完成项写成通过，不放宽断言。

scripts/browser-knowledge-fix.mjs已加入安全断言且finally清理；browser-password-fix.mjs使用合成管理员，成功改密必须回登录/清session、旧JWT401、新密码可重登且关键字段唯一可访问，finally停用合成管理员；首次尝试8000拒绝连接，尚无通过证据。

5174原工作区服务继续运行，未停止。5175仍为上一轮生产preview，可由总控切换；无推送。
