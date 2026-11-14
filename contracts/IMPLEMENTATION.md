# 本地验收契约 v1

2026-11-14。负责人已批准四项需求裁决，要求完成本地开发与测试后验收。采用原生Windows、Python3.12、MySQL8；两个前端独立依赖锁。后台端口5174，H5端口5173，API端口8000；开发代理保留/api前缀。所有API前缀/api/v1，JSON snake_case，成功直接返回数据；分页 {items,total,page,page_size}；错误 {code,message}。所有datetime输出UTC带时区。Bearer JWT，visitor/staff用途分离。

## 协作所有权

后端执行者唯一拥有server（除app/kb、app/integrations/llm与对应unit tests），共享core、模型、依赖、Alembic、OpenAPI导出。AI执行者仅拥有上述两个目录与tests/unit/test_kb.py、test_llm.py。H5与后台执行者分别拥有apps/h5、apps/admin，不改其他目录；各自负责生成客户端脚本，从真实OpenAPI生成路径类型/函数。总控拥有contracts、scripts、deploy、docs、tasks和独立验收测试。初次实现不得修改验收测试。

## 核心接口

- POST /auth/login、/admin/auth/login {phone,password} → {token,must_change_pwd,staff:{id,name,phone,role}}；管理员入口拒绝员工。POST /auth/change-password {old_password,new_password} → {ok:true}。首次改密前仅允许修改密码和/me/profile。
- GET /me/profile → staff。GET /public/cards/{code} → {code,status,name,dept,title,photo_url,photo_bg_url,mobile,email,intro,business_scope,company:{name,short_name,intro,phone,address,website,logo_url},products:[{id,title,summary,image_url,ask_question}],assistant:{opening,guide_questions}}。停用返回status=disabled，个人字段不再公开，只返回公司联络数据。
- POST /public/visitor/init {} → {anon_id,visitor_token}；不接受任意anon_id恢复身份，凭现有visitor bearer恢复。POST /public/visits {card_code,source} → {visit_id}；PATCH /public/visits/{id} {stay_seconds} → {ok:true}。
- POST /public/chat/sessions {card_code} → {session_id,opening,guide_questions}；GET /public/chat/sessions/{id}/messages → {items:[{id,role,content,kb_refs}],total,page,page_size}。POST同路径 {content} → SSE delta:{text}, lead_prompt:{reason,title}, done:{message_id,kb_refs,nokb,model}, error:{code,message}。手机号检测只提示，绝不自动创建线索。
- POST /public/leads {card_code,session_id?,name,phone,company_name,need,consent:true} → {id,status}；consent必需且必须true；session必须属于当前访客与当前名片。
- GET /public/cards/{code}/vcard → text/vcard；GET /c/{code} → 302 /card/{code}?s=link（校验source枚举）。
- GET/PUT /me/card（PUT {display_title,mobile,email,intro,photo_url?,photo_bg_url?,wechat_qr_url?}）→ 名片对象；GET /me/card/share → {short_url,qr_url,poster_url}。POST /me/card/photo multipart file → {photo_url,photo_bg_url}。
- GET/PUT /me/assistant → {template_id,persona_extra,opening,guide_questions}；GET /me/assistant/templates → 模板数组；POST /me/assistant/polish {text,field} → {text}。
- GET /me/leads?page=1&page_size=20&status=&q= → Page<Lead>；GET/PATCH /me/leads/{id}，PATCH {status?,remark?}；Lead={id,name,phone,company_name,need,status,remark,created_at,card_id,session_id}。所有权按owner_employee_id；他人id返回404。
- GET /me/stats?range=7d → {visits,visitors,chats,leads,conversion_rate,daily:[{date,visits,chats,leads}]}。
- GET /me/visitors → Page<Visitor>；GET /me/visitors/{id} → {id,anon_id,last_seen_at,sessions:[{id,summary,messages:[]}]}，限定本人名片。
- GET /me/notifications → Page<{id,title,content,read_at,created_at}>；GET /me/notifications/unread-count → {count}；POST /me/notifications/{id}/read、/me/notifications/read-all → {ok:true}。
- GET/POST /me/kb/notes → Page<Note> / Note；GET/PUT/DELETE /me/kb/notes/{file_id}，Note={file_id,title,content,public,approved,revision}；个人笔记默认不公开，只有admin明确批准才可用于访客回答。
- POST /me/kb/import file → {drafts:[{title,content}]}，不直接发布。GET/POST /me/corrections、DELETE /me/corrections/{id}；POST /me/issues {question}。
- POST /me/test-chat/sessions {} → 同访客会话结构；POST /me/test-chat/sessions/{id}/messages {content} SSE；测试不计统计。

## 后台接口

- GET/PUT /admin/company → company；GET/POST /admin/product-cards，PUT/DELETE /admin/product-cards/{id}。
- GET /admin/employees → Page<Staff>；POST {name,phone,dept,title,password,role?} 自动创建名片与助手，返回{id,...,card_code}；PUT /admin/employees/{id}；POST /{id}/reset-password {password}；POST /{id}/disable；POST /{id}/transfer {to_employee_id}（审核记录）。不得停用/转交自己管理员身份。
- GET /admin/stats → 同stats，含employees,cards,overdue_leads；GET /admin/leads → Page<Lead>（额外便捷管理接口）。
- GET/PUT /admin/cards/{code} 与 /admin/cards/{code}/assistant。
- GET/POST /admin/templates、PUT/DELETE /admin/templates/{id}、PUT /admin/templates/{id}/default。Template={id,name,persona,opening,guide_questions,is_default,enabled}。
- GET /admin/kb/files → Page<Note>；POST /admin/kb/files {title,content,public,approved}；GET/PUT/DELETE /admin/kb/files/{file_id}；GET /{file_id}/history；POST /{file_id}/rollback {revision}。公开与批准必须均true，撤销必须立即对检索失效。
- GET/PATCH /admin/issues（PATCH /{id} {status}）；GET/PUT /admin/rules {content}；GET/PUT /admin/settings/{key} → {key,value}，密钥不通过通用设置公开返回；GET /admin/audit-logs。
- NFC独立物理管理在当前裁决中延期；不能做假可用按钮。导入、评测等原计划功能须明确交付/未交付，不以静态界面冒充完成。

## AI内核可独立开发的协议

app/kb/store.py: KnowledgeStore(root: str|Path)，upsert(file_id:str,title:str,content:str,*,public:bool=False,approved:bool=False,scope:str='company',card_code:str|None=None)->dict；list_files(scope=None,card_code=None)->list[dict]；get(file_id)->dict|None；delete(file_id)->None；history(file_id)->list[dict]；rollback(file_id,revision)->dict；search(query:str,card_code:str|None=None,limit:int=4)->list[dict]。文件内容唯一经此读写，filelock，安全ID（禁止路径），revision/hash，公开批准在每次检索时检查，卡片隔离。所有方法同步，调用端在线程池运行。

app/integrations/llm/client.py: LLMClient Protocol async stream(messages:list[dict[str,str]]) -> AsyncIterator[str]；FakeLLMClient固定合成演示答复，不编造真实公司事实；OpenAILLMClient(base_url,api_key,model,timeout=30)；build_client(settings) 按settings.llm_mode选择。app/integrations/llm/service.py: ChatEngine(client, fallback=None)，async stream(question:str,knowledge:list[dict],history:list[dict],persona:str='')->AsyncIterator[dict]（{event,data}）。报价类拒绝、无知识诚实说明、资料当数据而非指令；仅首token前可备援，部分输出后失败发error且不重放；结束done含kb_refs,nokb,model。接入后端负责消息落库/会话所有权/限流，engine不接触数据库。

## 本地数据

### 2026-11-15 对话行为补充（ADR-003）

本条取代上文“无知识诚实说明”的固定拒答解释：无检索命中仍调用模型，通用知识可正常回答；仅缺少依据的公司特定事实需要明确待确认。`ChatEngine.stream`兼容原参数，并新增可选关键字`public_card:dict|None`，仅接收当前访客可见名片的白名单投影，作为独立事实数据，不伪造文档引用。未批准、未公开、其他名片的知识仍不进入访客模型上下文。普通定义解释不因出现“合同”等词被当作代签约或承诺。

访问归因不再阻断正常流程：已验证会话优先，其次同访客同名片访问，最后有效公开活动提示。缺失或外来visit提示忽略，不能关联其数据；session身份隔离、停用名片限制、显式留资同意保持。HTTP/OpenAPI与SSE事件结构不变。

后端命令python -m app.seed幂等创建明确标记“演示数据”的公司、管理员和两个员工与demo/colleague名片；随机生成本地演示账号口令并写未跟踪文件，不写到Git。设置开发Fake模型时UI明确显示“本地演示模型”；不得声称真实模型评测已过。
