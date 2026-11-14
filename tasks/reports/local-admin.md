# 本地管理后台候选交付（frontend/admin）

- 分支：feat/local-admin；独立工作区 D:/AIWork/智能名片/worktrees/admin；base 3fca087。
- 所有权：仅 apps/admin/** 与本角色报告；未修改 server、共享 contracts、验收测试或主检查入口。没有数据库迁移，没有推送。
- 实现契约 SHA256：238989ff74e5c075bab000a9a5bbd53e3872c837fc3ff047e4fc1f7333461f25。
- 真实 OpenAPI source：后端工作区 contracts/openapi.json，当前生成 SHA256 6e06c35ef71cd5cd99b25f7047942d3cea3197a7fe26c99938859040af1bfadc；生成40个后台所需函数。生成脚本 gen:api 支持参数、OPENAPI_SOURCE及默认仓库contracts路径，缺少真实源直接失败。没有手写generated；schema.ts仅为真实generated模型别名。
- 模板：官方 pure-admin/pure-admin-thin，实际克隆6.2.0 / f0ff132561ab684bb78379239adf29f9a38ac7f1，选择复制保留LICENSE与来源。见 apps/admin/TEMPLATE_SOURCE.md。静态菜单、ElementPlus、@pureadmin/table、独立package与pnpm锁；md-editor-v3已按T23/T38要求引入，DOMPurify净化预览。
- 启动：pnpm --dir apps/admin dev，127.0.0.1:5174（交付时继续运行，不停止）；proxy /api → 8000，不rewrite。生产默认base=/admin/，history跟随BASE_URL，VITE_BASE可覆盖；开发默认根路径。

## 完成

C1管理员真实登录与强制首次改密；C2核心stats/每日数据与线索列表；C3公司和产品增改删（既有图片URL）；C4模板增改删/默认；C5回答规则；C6公开知识Markdown草稿、明确批准发布、撤回、历史、回滚、删除；C7员工新增修改停用重置密码转交、名片及助手代改；C9问题池状态；C10非敏感配置记录、运行模型真实health状态、审计元数据。

管理员独立sessionStorage键；不读写H5员工/访客凭据；401/过期清理管理员登录，不刷新token；不能停用/转交自己；审计不展示原始detail，设置不读/回填/提交密钥或掩码。无mock/假登录/无效按钮。

## 实际验证

- pnpm install实际执行，独立pnpm-lock.yaml；锁住依赖；允许esbuild/vue-demi必要构建脚本。
- pnpm typecheck、lint、test、build：候选实际运行通过（日志 apps/admin/evidence/）。test包含6个关键请求/会话测试：用途隔离、过期、登录不带旧bearer、401无重试、路径编码、首次改密错误。
- 浏览器真实Edge/Playwright：登录、stats、员工新增/修改/重置/转交/停用、名片与助手代改、公司保存、产品新增删除通过；无请求错误及pageerror。可复用脚本在 apps/admin/scripts/browser-smoke.mjs，凭据仅从未跟踪文件读取，无输出。
- 模板新增编辑删除、知识Markdown草稿/发布、历史/回滚真实接口已通过。复验脚本曾暴露知识PUT多传file_id/revision导致422，已修复为只发送title/content/public/approved；随后发布/回滚通过。后续撤回/删除的脚本因回滚到已发布版本后反向切换开关而等待错误按钮，尚未完成全流程复验；不声称这条脚本全绿。
- favicon原无显式资源导致隐式404，已添加BASE_URL感知的本地SVG；全新浏览器登录页 console error=0、pageerror=0、HTTP error=0，脚本 check-login-console.mjs。
- 截图：apps/admin/evidence/dashboard-desktop.png、knowledge-history-desktop.png。后台不适用H5视觉原型；390×844与生产子路径浏览器仍需集成复核。
- 构建成功但ElementPlus/Markdown包存在>500KB体积警告；路由级懒加载已启用，未伪称警告不存在。
- 机械UI检查返回[]。未运行全仓scripts/check.ps1：该base不含主线程已添加入口，且server/H5由其他所有者实现，交由总控集成检查。

## 范围与风险

- C8独立物理NFC登记/绑定/解绑/挂失明确延期，页面标为未交付，不计完成。
- 知识批量/文件夹上传、格式校验、评测，Excel员工导入，产品图上传，来源分布/排行/热门未命中问题未冻结对应接口，页面列出未交付范围，不用静态控件代替。
- 当前设置GET/PUT只持久化配置表，后端运行模型/限额仍读环境；页面明确说明保存不代表生效，运行时应用需后端接入。未声称模型/限额动态生效。
- 当前后台知识列表后端仅返回公司scope，个人笔记审批的可发现入口仍待后端契约；前端不虚报支持全部个人笔记审批。
- 合成测试新增员工均为本地测试资料；成功完整脚本新增员工已停用，失败脚本残留临时员工/知识待总控统一清理，绝非真实业务资料。
- 管理员后端权限、真实模型评测、50并发SSE、全仓验收、部署和一周灰度不在本角色已通过证据范围。

候选按主线程要求先交可集成提交，后续QA精确缺陷另fix；不修改验收以掩盖失败。
