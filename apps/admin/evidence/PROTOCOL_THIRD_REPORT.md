# Responses协议与三级模型配置界面

父提交 f148b2cd545c964e88a955221aacc7766c648543（主干已集成104a4af）；仅apps/admin。

依据：只读backend工作区runtime_settings.py实际新增字段与枚举。未读取产品真实Key或受控配置文件，未调用模型，未写入产品LLM配置。

字段：llm_api_mode、llm_fallback_api_mode、llm_tertiary_enabled/base_url/model/api_key/api_mode。协议下拉只接受responses/chat_completions；主/备用/兜底组均沿用固定field模式，不重写页面。地址、型号、协议从runtime读取，无产品真实base/model/key常量。旧服务未返回的新字段不显示。

主模型启用要求自身完整，备用/兜底只有已启用时才阻止主模型切换；每级必须完整配置地址/型号/协议/密钥才允许从false启用；已true但连接不完整仍允许关闭，false不会被误拦截。密钥只存在configured布尔标记；新增第三级也不回填原值/掩码，活动配置的clear遵守对应启用状态。

界面说明备用仅在首内容输出前失败切换；部分输出后失败不重放。不展示产品三模型清单或额外供应商细节。

验证：typecheck/lint/build实际通过，test 16/16（新增3条三级协议、第三密钥抹除、第三禁用/清空边界）。合成Edge/Playwright全部API拦截：三协议保存、第三密钥无回填、true→false关闭、关闭后不完整配置不能开启、1440及390px界面通过，console/page错误0、未知API0。截图及详细结果protocol-third-synthetic*。

合成检查使用虚构token及内存runtime数据，不读取任何真实账户或密钥文件，不请求实际API、不实际生成；真实Responses/三级流式可用性由主线程和后端独立验收，不把超时或仅配置成功标成生成成功。

OpenAPI仍为上次主干真实53e01e023e63f221fcd247e3f629de002a47c68aad18716d41de450c7b52bf6e，RuntimeConfiguration.settings是动态键字典，新增keys不改变其形状；本次没有手写generated。5174保留运行，无推送。
