# 子路径首次改密拦截修复

2026-11-15。主线修复提交`547730a`，源提交`52be5f2`。仅修改`server/app/core/deps.py`并新增定向回归，不改API契约、数据库结构、用户密码或系统环境。

## 原因

首次改密限制用`request.url.path`匹配不带部署前缀的白名单。在`/aicardhub`部署后，请求路径不匹配，导致当前用户profile和修改密码接口自己也返回403 PASSWORD_CHANGE_REQUIRED。原密码尚未进入校验，所以与用户保证原密码正确不矛盾。

## 修复

与Starlette路由使用同一`get_route_path(request.scope)`，扣除root_path后按方法和完整路径精确放行`GET /api/v1/me/profile`及`POST /api/v1/auth/change-password`。其他首次改密受限接口继续403；账号状态、密码是否设置、令牌版本仍先验证。没有采用后缀匹配或关闭首次改密要求。

## 验证

- 修复前主线真实router＋get_current_staff的ASGI最小复现403，修复后相同命令200。
- 61项定向测试通过（首次改密40＋已有root_path21），覆盖根/单层/嵌套前缀、方法、伪造前后缀、停用及旧令牌。Ruff通过。
- 服务器修复前使用独立临时员工/管理员账号实测均403，见`before.json`。
- 修复后通过公网HTTPS，员工和管理员均：初始profile200、业务接口403、错原密码400、正确改密200、旧令牌401、新密码登录200、must_change_pwd=false、新profile200，见`after.json`。
- 测试账号无名片/任务/通知，结束后按精确ID及手机号删除。没有重置、代改或解码用户粘贴的真实账号令牌；原账号保持原状。
- 原站根页面、员工及后台登录页、API健康均200。

线上仅对当前release的`app/core/deps.py`进行带SHA-256核对的原子替换，原文件保存到root私有迁移目录。仅重启aicardhub-api，健康失败有原文件回退；本轮启动健康成功。未改系统库、MySQL、SSH、Nginx、scheduler或前端。

执行来源：指定Claude Code启动被自动审批策略拦截，未给具体原因，模型未执行；代码由Codex完成，主线独立复现、审查、定向验证及发布。没有以失败的模型调用冒充DeepSeek执行。未跑全量测试或构建，避免本机高负载。
