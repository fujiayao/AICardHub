# Prototype fidelity page checklist

Source: exact external prototype and main 390×844 references. Status below is coordinator observation, not implementation claim.

| Page | Name | Route | Implementation / visual acceptance |
|---|---|---|---|
| A1 | 名片首页 | /card/:code | Candidate4740503+fix56d9132; real390x844 checked; final details/fallback pending |
| A2 | AI 对话页 | /chat/:code | Partial uncommitted; screenshot rejected avatar positioning; lint import-sort fails |
| A3 | 留资成功 | /chat/:code（弹层提交后页内切换） | Not ported / not visually accepted |
| A4 | 名片停用 | /card/:code（status=disabled） | Not ported / not visually accepted |
| A5 | 微信内打开引导 | A1 上的浮层 | Not ported / not visually accepted |
| B1 | 登录 / 首次改密 | /staff/login | Not ported / not visually accepted |
| B2 | 名片（Tab 首页） | /staff/card | Not ported / not visually accepted |
| B3 | 编辑名片 | /staff/card/edit | Not ported / not visually accepted |
| B4 | 发送名片 | /staff/card/share | Not ported / not visually accepted |
| B5 | AI 助手（Tab） | /staff/assistant | Not ported / not visually accepted |
| B6 | 个人知识 | /staff/assistant/notes | Not ported / not visually accepted |
| B7 | 文档导入预览 | /staff/assistant/import | Not ported / not visually accepted |
| B8 | 纠错记录 | /staff/assistant/corrections | Not ported / not visually accepted |
| B9 | 试聊调试 | /staff/assistant/test | Not ported / not visually accepted |
| B10 | 客户（Tab） | /staff/customers | Not ported / not visually accepted |
| B11 | 访客详情 | /staff/customers/:visitorId | Not ported / not visually accepted |
| B12 | 我的（Tab） | /staff/me | Not ported / not visually accepted |
| B13 | 消息中心 | /staff/messages | Not ported / not visually accepted |

## Authorized deviations

- OS status bar/device shell omitted; business content retained.
- Real fields only from APIs; absent photo uses exact anonymous prototype SVG, never fake executive image.
- Phone/WeChat actions hidden when corresponding data unavailable.
- Phone detection is suggestion only; explicit consent required before lead submission.
- B2 today is stats(today); yesterday pending additive contract.
- B3 company locked row retained; actual affiliation pending additive CardData.
- NFC status strip retained, feature unenabled; no fake binding serial.

## Verification

- Baseline lint/typecheck passed before implementation; this is not candidate validation.
- Main reference18 screenshots exist. No candidate visual pass claimed yet.


Latest authoritative coordinator assessment: delivery.md. B1/login/menu externally owned. B2/B5 only partial uncommitted; new API fields available so pending bindings are implementation gaps, not data restrictions.
