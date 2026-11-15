# NFC HTTPS 服务器发布验收

日期：2026-11-16（Asia/Shanghai）。负责人明确授权发布到现有HTTPS服务器并用手机验收，要求产品页面不再显示调试候选。本轮由当前Codex原生子代理完成UI、安卓release和独立审查；未使用Magpie或外部模型CLI。

## 发布内容

线上current：/opt/aicardhub/releases/nfc-20261116。原release 919589c2555e保留，venv只读复用原依赖，无新增服务器Python依赖/迁移；仅新增share_link_service及更新router/schema/media与Web静态产物。生产shared env、真实账号、业务数据库、知识库与模型设置保留。没有上传本地fake配置、没有seed线上、没有替换真实资料。

上线前在/var/backups/aicardhub/nfc-20261116备份数据库、shared私有数据、旧nginx include与原current目标。新后端先在18001、aicardhub身份、生产EnvironmentFile下只读smoke，成功后nginx-t、原子切current、restart API/scheduler、health通过后reload。脚本含回滚。临时stage已停止，旧站root代理、ACME和其他服务不变。

## 真功能交付

- APK正式签名，cn.aicardhub.nfc 1.0.0/versionCode2，sha256 6bdb83bf035366aa2117e48d16ec5ec440bd7d1ef7833888383d103f08aa998c。正式签名私钥仅本地受控.local/nfc-signing，不上服务器或Git。
- Android21 release JVM通过，lintRelease0错误0警告，apksigner verify及aapt正确。
- 域名根/.well-known/assetlinks.json正确application/json，声明实际release证书。Manifest仅关联/aicardhub/share/nfc，访客/c和/card仍H5。
- APK公开地址https://haiwex.com/aicardhub/downloads/aicardhub-nfc.apk，实际664216字节PK zip，HTTP下载SHA256与源APK完全一致。
- H5和后台采用真实https下载配置；安卓点击固定package的intent URI，未安装回到同源帮助页。公开帮助页可点击已安装打开助手和复制公开链接。
- 去除调试候选/未发布文案，显示操作入口；iPhone仅接收，物理库存绑定未做的功能仍明确。

## 实际检查

H5 lint/type与生产build通过；首次51测试，下载anchor修复新增Vant SSR回归。admin lint/type、27测试与生产build通过。线上发现van-button的href渲染为button不会下载，已修tag=a、新增真实组件SSR验证，重新构建发布；不是仅改文案。

独立HTTPS只读审查通过：root200原站1079字节、health200仍openai/gpt-6.1-terra、未登录新接口401（已上线）、两个真实名片302前缀/source/no-store正确、APK与assetlinks正确、伪下载和私有env路径404、nginx-t成功、六个服务active，app源码来自新release。

## 手机验收

员工入口：https://haiwex.com/aicardhub/staff/card/share?tab=nfc
安装包：https://haiwex.com/aicardhub/downloads/aicardhub-nfc.apk
直接助手入口：https://haiwex.com/aicardhub/share/nfc?code=5dbb1d43&mode=emulate
贴纸入口：https://haiwex.com/aicardhub/share/nfc?code=5dbb1d43&mode=write
后台：https://haiwex.com/aicardhub/admin/scope

如手机装过旧debug包需先卸载再安装release。安装后在安卓Chrome或系统浏览器点击打开助手，联网预览本人名片后手动开启模拟或写贴纸；保持前台亮屏解锁。对方安卓/iPhone靠近天线按系统提示打开。写贴纸需可写且NDEF格式化，写完回读成功再移开。

网页与APK已真实发布；主机不能代替手机执行射频，碰触、Tag移开/换片、特定机型钱包路由以及iPhone读取稳定性留由用户真机验收。

## 最终线上浏览器实测

使用原网站实际员工/管理员凭据（仅私有文件进程读取，不写报告）完成真实HTTPS登录，无mock：员工NFC页『打开NFC助手』『写入NFC贴纸』均enabled，canonical链接s=nfc/无活动，下载为真实anchor，页面无调试候选文字；公开write页展示真实本人名片、已安装打开按钮enabled；iPhone UA显示仅接收说明；后台真实登录和scope说明通过。页面脚本错误0。screenshots/nfc/https保存4张线上截图。浏览器不能实际安装APK或执行手机intent/RF，已验证生成URI与部署关联配置。

最终仅文字补丁再次发布：H5 index SHA256 f0b4b63dadc93811b43cc21f9b92d627a58cc75ed8a1771cc9277cd58b067ea8；Admin index SHA256 0d61157dc992d20a7b3908bbc2719df8e2e17bab6f4322af78bf55d7fee78883。移除管理员登录和员工我的中的本地候选字样，未改变逻辑。H5最终12files/52tests全部通过。

最终状态：HTTPS后端/网页/正式签名APK/JSON域名声明已发布，可由负责人手机进行真实功能验收。设备端NFC射频测试仍由真机执行，服务器不伪造验收通过。
