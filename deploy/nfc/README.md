# NFC APK 与 App Links 发布准备

本目录准备本地候选材料，不访问服务器、不安装 APK，也不证明手机/贴纸兼容性。

1. 按 `apps/nfc-android/README.md` 构建与目标域名一致的 APK；使用 `apksigner verify --print-certs` 取得这个 APK 的证书 SHA-256，而不是猜测证书值。
2. 将站点现有 `/.well-known/assetlinks.json` 保存为本地受控输入。已有应用的声明必须保留。
3. 使用 `prepare_release.py --help`。传入实际 APK、包名、证书指纹、HTTPS 公开 base、新输出目录；有原关联文件时加 `--existing-assetlinks`。debug 构建使用 `--channel debug-test`。
4. 检查新输出的 APK 哈希、`release.json` 与合并后的 `assetlinks.json`。该工具校验元数据，不代替 APK 签名验证，发布者必须确认包名和指纹与 APK 一致。
5. 域名根 `/.well-known/assetlinks.json` 需由原站配置以 JSON、无登录、无重定向形式提供。不要把它放到 `/aicardhub/.well-known/`，不要替换原站其他关联。
6. 原生 Manifest 仅关联 `/aicardhub/share/nfc`（实际 base 为准），`/c/*` 和 `/card/*` 继续进入 H5。部署后用 Android 系统 App Links 验证命令和真机点击核查，不能仅凭文件返回 200 就认定关联成功。
7. APK 下载位置由本次发布确定，再将有效 HTTPS URL 配置到 H5 `VITE_NFC_APK_URL` 重新构建；未发布时显示联系管理员。不要预先提供 404 下载按钮。

debug APK 仅供受控验证；生产 APK 使用独立受控签名，私钥不入 Git。升级需保持包名与签名策略。正式发布还必须完成 NFC 三条射频链路和既有 H5/旧站回归。新增下载 location 与域名根配置由发布负责人准备、检查后再执行，不改动现有生产站点来进行本地开发。

元数据工具本地验证：在此目录运行 `python -m unittest -v test_prepare_release.py`。测试仅使用临时合成 APK 字节，不将其视作有效安卓安装包。
