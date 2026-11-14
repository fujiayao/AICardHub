# B3 编辑名片 —— 布局还原说明

对照来源：`D:/AIWork/智能名片/claude/数科AI智能名片_H5原型.html` 第 926–955 行（`PAGES_RENDER.B3`）及其
全局样式（`.sec-title` L172、`.group` L220、`.cell`/`.cell-label` L221–233、`.textarea`/`.counter` L234–235、
`.switch` L239–242）。参考图：`main` 分支 `reference/B3.png`。

## 改动动机

重写前的 `edit.vue` 用通用 `.panel` + 居中大头像 + 散落字段，**不忠于原型**：原型是“带分组标题的分段表单”。
本次按原型重排为四个带 `sec-title` 的分组区块，并修复顶部“保存”绕过校验的问题。

## 还原后的结构（自上而下）

| 原型区块 | 实现 |
|---|---|
| `sec-title 职业照` | `<h2 class="sec-title">职业照` |
| 横向 group：左 96×128 竖版照 + 右 说明/更换按钮 | `.portrait-group`（`display:flex;gap:14px;align-items:flex-end;padding:14px 16px`），左 `.portrait`（`96×128`，`object-fit:cover`），右 `.portrait-side` 放一句说明 + 软按钮“更换职业照” + 上传限制小字 |
| 独立 group：同时作为对话页背景（开关） | `.group.single` 内 `van-cell` + `van-switch`，带副标题“访客和 AI 分身聊天时显示为模糊背景” |
| `sec-title 基础信息` + group（姓名/职位/部门/公司） | `.group.fields`：姓名/部门/公司为 `van-cell`（只读，label=“管理员维护”），展示职位为可编辑 `van-field` |
| `sec-title 联系方式` + group（手机/邮箱/微信二维码） | `.group.fields`：手机、邮箱 `van-field`；微信二维码走 `WechatQRUpload` |
| `sec-title 个人简介(选填)` + textarea + 计数 | `.group.intro` 内 `van-field type=textarea` + `show-word-limit`（替代原型手写 `.counter`），`maxlength=150` |
| 底部灰色说明 | `.hint.foot`：保存后访客端立即生效… |

视觉 token 对齐：`.sec-title`/`.group`/`.portrait` 的尺寸、内外边距、圆角、字号均复制原型数值，
颜色全部走 `tokens.css` 变量（`--c-ink`/`--c-text-3`/`--c-surface`/`--c-primary-soft`/`--c-bg`/`--r-*`/`--fs-*`），无颜色字面量。

## 关键决策

- **去除 PageShell 的 `.content` 默认 grid 间距**：PageShell 的 `.content { padding:16px; display:grid; gap:16px }`
  会在每个区块间多出 16px 间距、破坏原型“sec-title 贴着 group”的节奏。用**仅本页** scoped
  `:deep(.content){display:block;padding:0}` 抵消（该选择器通过本页 scope hash 命中 PageShell 根 `main.page` 下的
  `.content` 子节点），区块间距改由各 `sec-title`/`group` 自带的 margin/padding 控制，与原型一致。
- **匿名占位用 `AnonymousPortrait`**：未上传职业照时渲染精确复刻原型 `photo()` 几何的 SVG 插画，
  **不是**通用 user 图标。
- **顶部“保存”与表单提交同一校验链路**：顶部按钮 `submitFromHeader()` 调用 `formRef.value?.submit()`
  （Vant `FormInstance.submit()`），触发与底部表单提交完全相同的 `@submit="save"` 前校验；
  不再存在“顶部保存绕过校验”的旧行为。全部可编辑字段（展示职位/手机/邮箱/微信/简介）都在 `<van-form>` 内。
- **校验按“仅校验已填值”**：手机、邮箱均为选填——`mobileRules`/`emailRules` 用 `validator` 在空值时直接判定通过，
  仅对已填入的值做格式校验。未在 API 中捏造“手机必填”语义（`CardInput.mobile` 为可选）。
- **公司锁定显示真实 `company_name`**：只读 `van-cell` 显示 `data.company_name`，无则占位 `—`，不硬编码公司名。

## 保留的既有正确语义

- 职业照：原图 10MB / 裁剪 5MB 限制、`PhotoCropper` 弹层裁剪、上传成功即时保存（`cropped()` 内直接写 `photo_url/photo_bg_url`）。
- 微信二维码：`WechatQRUpload` 即时上传语义、`busy` 态禁用保存（`uploadingQR`）。
- `onBeforeRouteLeave`：未保存字段离开二次确认，`baseline` 快照比对不变。
- `photo_bg_url` 随“作为背景”开关在保存时置空/回填。

## 约束遵守

- `<script setup lang="ts">`，无 `any`/`@ts-ignore`，无 `console`，仅用 Vant 组件。
- 文件 148 行（≤300）。只改 `apps/h5/src/pages/staff/card/edit.vue`，未触碰共享/staff 组件、后端、generated、私有数据。
- 仅通过 `api/generated` 调接口。

## 待验证（未执行，交由父任务）

- `scripts/check.sh`（lint/type）**未执行**。
- 390×844 真机/模拟截图与 `reference/B3.png` 像素对比**未执行**，无可视通过结论。
  下一步命令：`cd apps/h5 && pnpm dev` 后截图 B3，或父任务既有 capture 脚本。
