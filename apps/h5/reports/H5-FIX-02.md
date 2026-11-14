# H5 修复 02：B11 访客关联与真实轨迹

基于 4fe98bd，仅补 B11，不扩其他业务，不修改 demo 或 QA 数据。

- 从主仓库真实 contracts/openapi.json 重新生成 42 操作；SHA256 `53e01e023e63f221fcd247e3f629de002a47c68aad18716d41de450c7b52bf6e`。generated 未手改。
- 线索详情通过 LeadData.visitor_id 的链接进入 `/staff/customers/{visitor_id}?kind=visitor`，不使用 lead.id/session_id 代替访客 ID。移除旧“未提供访客编号”提示。
- CustomerHistory 组件展示 VisitorDetail.visits 的 source、created_at、stay_seconds；每段真实会话的 summary、intent_level、tags。空 visits/sessions 明确显示空状态，未返回意向不补写等级。保留对话与纠错入口。
- 去除访客详情“尚未提供联系方式”的推断文案，联系电话由对应线索详情展示。
- 新增2项组件渲染测试：真实字段/来源/秒数/意向/标签渲染与标签转义；空轨迹和会话不编造数据。复用已有 @vitejs/plugin-vue，未加依赖。

检查：pnpm lint、typecheck、6文件15测试、build 全通过。构建仅既有 PostCSS from-option 与插件耗时警告。此次没有业务写操作，没有重跑或修改独立验收脚本；全仓最终集成由主线程执行。5173 保持运行。
