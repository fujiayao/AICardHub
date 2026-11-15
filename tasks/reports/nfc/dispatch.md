# NFC 开发派工记录

日期：2026-11-15。负责人已授权实际开发和子代理。

基线：d9014ad；开发工作区：D:/AIWork/智能名片/worktrees/nfc-implementation；分支：feat/nfc-implementation。主仓未提交方案已独立提交，无其他改动带入。Codex managed worktree API拒绝识别该本地仓库，改用原生Git worktree，文件已实际检出；不声称app托管成功。

模型：后端与安卓 gptpro/gpt-6.1-sol；QA auto/deepseek-v4.1-flash；H5/后台UI限定 claude-2/claude-opus-5-5（量惟）；总控汇总不调用Claude做普通复核。子代理使用带模型元数据的Magpie路由工具，独立核对本机模型列表，不能据列表宣称生成成功。各agent工具闭环与完成证据见对应报告。

所有权：backend 独占后端/schema/OpenAPI；android 独占apps/nfc-android；ui独占H5/admin功能变更与生成客户端；qa只读复核和qa报告；总控拥有发布文档、安装候选、集成记录与统一提交。共享独立开发worktree，写入目录互斥，所有agent不自行commit。

契约：GET /api/v1/me/card/share-link，operation_id me_card_share_link，响应{short_url,source,campaign_id}，仅本人；App Link /share/nfc?code=&mode=emulate|write&e=，长期贴纸无e。

实际硬件：暂无手机/贴纸射频证据；不执行采购或生产部署。
