# NFC 实施集成记录

基线d9014ad；工作分支feat/nfc-implementation。模型分配已按用户更新，实际开发已开始并形成软件候选。

## 后端检查

后端owner全套pytest首次得到532 passed、2 failed；新增NFC真实MySQL/HTTP/JWT22项通过。2个既有migration测试因新隔离库通过metadata.create_all建表缺少命名外键失败，stamp只补版本不能补结构，未改断言。

总控另建全新datadir（data-migrated），在13316仅创建aicardhub_test，执行真实alembic upgrade head，再运行tests/api/test_organization_migration.py：2 passed in 2.01s。原metadata测试库数据目录保留，不删除不冒充迁移成功。旧MySQL80和业务数据未改。后续集成全门禁使用真实迁移初始化的隔离库。

## 安卓候选

最终APK SHA256 11547df93e8746d77a1bc888d9acf06f1e54b02582670879ec8d6e12d5722304；21 JVM测试通过，lint0error5warning。已独立核对JUnit XML和签名；debug测试证书，生产签名/App Links仍需发布步骤。

## 发布准备

本地.local/nfc-candidate包含相同APK、assetlinks声明和release.json，未发布。deploy/nfc三项元数据测试通过，验证HTTPS参数、原关联保留、输出不覆盖和APK字节一致性。

## 仍待完成

Web检查/截图与独立复核正在进行。无手机/贴纸，所有射频兼容性均awaiting_hardware；无线上部署。

## 第二轮复核处置

- 活动贴纸歧义：统一V1只写固定长期链接，拒绝write&e；临时活动仅手机模拟。这是本轮技术设计选择，未取消用户已要求的任何贴纸写入能力。任务卡/采购规范/ADR同步。
- 发布base校验：与APK构建允许集一致，拒绝所有显式/非法端口和非法路径字符，新增负例并重跑3项元数据测试通过。
- 过期活动浏览器恢复：后端owner修复中，保持API JSON契约，浏览器增加明确回退操作。
- H5 canonical地址与参数：UI owner修复中，从后端公开短链推导配置地址，严格解析NFC参数，避免别名和旧路由数据。

## 最终集成结果

在真实 Alembic 初始化的隔离 MySQL8 上运行 scripts/check.ps1，exit=0：契约103操作0issue、ruff check/format、mypy44files、pytest **555 passed in264.92s**、单一迁移头、H5/admin lint/typecheck/build、H5 **11 files /48 tests** 全部通过。原始check日志在本地.local/nfc-check.log。另跑admin node tests **27 passed**、发布工具 **3 passed**。

H5测试JSON逐文件核对：nfc-link.test.ts的9条包含在总数48中，不是被测试发现器遗漏。两端生成客户端同一hash34240ff7。

总控补浏览器mock smoke：7条断言通过，确认安卓可用canonical助手入口、iPhone仅接收说明、长期write&e拒绝、公开配置页不记visit、NFC页不触发图片接口。4张390宽截图与1张后台截图已保存tasks/reports/screenshots/nfc；mock数据是合成员工，非真实资料。截图目视检查通过。未运行全产品E2E，也未将Chromium的iPhone UA当作Safari真机。

DeepSeek最终复核：software_done，V1无剩余软件阻断。复核原发现、修复与范围统一均保存在qa-review.md。原UI agent只负责页面，后来超出Scope页的admin适配层description默认值变更已由总控审查接受：生成契约类型的必需默认字段兼容，未改变知识发布规则。

交付类型：软件候选完成；Android debug APK构建/签名通过；手机/贴纸射频awaiting_hardware；App Links域名发布/生产签名awaiting_deployment。未采购、未上线，主站配置与旧业务库未改。
