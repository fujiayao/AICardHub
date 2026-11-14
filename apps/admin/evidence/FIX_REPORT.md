# 后台知识、生产路径与响应式修复

候选父提交 ef625252ac113f902da7e7910c6585d44d6d2de7；主干已用4fbdf82集成候选。本修复仅修改apps/admin。

- 知识按真实scope/card_code显示公司知识/个人笔记所属名片；编辑保留原范围，公开批准提示不再误称全部访客。
- 修复390px侧栏文字重复越界：窄屏改为可关闭抽屉菜单，桌面仍支持折叠且名称可访问。知识编辑器默认单栏，可切预览，避免挤压。
- 公开/批准开关显式aria-label；busy时表单禁用。
- 实际网络拦截发现md-editor即使无全屏按钮仍请求unpkg screenfull；通过其官方config禁用未使用的fullscreen扩展。验证代码块、Markdown输入及预览，无外部CDN/字体/语言资源请求。
- .prettierrc.json endOfLine:auto；生成器resolveConfig读取同一配置。73份源文件独立CRLF副本eslint/prettier均通过，无忽略检查项，无批量语义改动。

真实Edge+Playwright：知识草稿不进SSE引用、发布后有引用、撤回后重新GET(public=false,approved=false)+刷新未发布+SSE无引用、删除后GET404+刷新列表消失+SSE无引用；个人笔记显示demo范围且管理员修改后仍scope=card/card_code=demo。新合成资料finally清理，前次3个明确自有测试知识清理，未改公司资料或QA样本。

生产真实Vite build/preview http://127.0.0.1:5175/admin 与开发5174两套：390×844登录/工作台/知识编辑/抽屉导航/NFC范围，1440桌面折叠导航，深链刷新通过；生产脚本均/admin/assets/*、favicon=/admin/favicon.svg；控制台/page/HTTP错误均0。生产路径知识完整闭环也复验通过。

日志：knowledge-fix.json、responsive-production-fix.json、crlf-format-fix.json及*-fix.log；截图dev/production-*-390x844.png、knowledge-scope-desktop.png。

pnpm typecheck/lint/test(6/6)/build实际通过。构建既有大分包警告保留。5174持续运行；5175为本次生产preview。未声称完整部署nginx验收。

Settings留待后端runtime schema接入的独立fix；本次没有猜keys或改Settings。NFC延期仍明确未交付。
