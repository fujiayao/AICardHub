# 模板来源与改造记录

官方仓库：https://github.com/pure-admin/pure-admin-thin

实际下载：2026-11-14，默认分支 HEAD `f0ff132561ab684bb78379239adf29f9a38ac7f1`，package.json 版本 6.2.0。浅克隆到系统临时目录后选择复制到本目录，未复制嵌套 .git。

保留官方 MIT LICENSE。复制的工程入口 index.html、Pinia setupStore、layout/hooks/useBoolean.ts、ReCol、TagChrome.vue 来自该提交。布局 index.vue、NavVertical、lay-content、lay-tag、router 静态模块按该模板的导航/布局/标签结构改造；原模板组件可从上述提交对照。ReCol、TagChrome 和 useBoolean 在实际布局/工作台使用，表格使用模板的 @pureadmin/table。不是另一个后台模板。

删除示例、mock、动态菜单、Cookie token、refresh token、主题配置和多标签缓存等不需要的逻辑；登录改接直接数据接口。保留 Vue3.5 / Pinia3 / Router4 / ElementPlus2.11 / Vite7 / TypeScript5.9 的实际模板系列。依赖只保留使用项，按要求新增 md-editor-v3、DOMPurify（预览净化）及 OpenAPI 生成工具。

原模板脚本的 POSIX 环境变量赋值已换成 Windows 可直接执行的 Vite 命令。所有依赖与锁均在本应用内。
