# 模板来源

从 https://github.com/easy-temps/vue3-vant-mobile 官方仓库网络克隆至临时目录，再复制工程配置与 LICENSE 至本目录。

- 上游提交：8a46a5a41473ba3a638e2249b4c4e48b8ef7ddea
- 上游 package 版本：3.16.0；获取日期：2026-11-14；保留 MIT LICENSE。
- 基于原工程 build/vite、Vite、UnoCSS、postcss-mobile-forever 配置改造；移除国际化、示例页、ECharts、sitemap、Service Worker、发布与 Git hooks。保留文件路由、Vant 自动组件、legacy、开发 Mock 插件；vConsole 仅显式开发开关加载。
- 版本以本目录 package.json 和 pnpm-lock.yaml 实际解析结果为准；H5 独立安装，不建立 workspace。
