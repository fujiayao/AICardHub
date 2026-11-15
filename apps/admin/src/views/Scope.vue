<!-- C8 范围说明：NFC 拆为手机分享 / 贴纸写入 / 库存绑定挂失三项状态 -->
<script setup lang="ts">
import PageHeader from "@/components/shared/PageHeader.vue";

const nfcItems = [
  {
    title: "手机 NFC 分享",
    tag: "调试候选",
    type: "primary",
    lines: [
      "员工在 H5「发送名片 → 手机 NFC」打开安卓 NFC 助手，模拟标准 NDEF 网址；接收方安卓与 iPhone 由系统读取后打开 H5 名片。",
      "iPhone 仅作为接收方，不提供 iPhone 发卡。安卓助手尚未发布，暂无已验证真机清单；请勿视为全员可用。",
    ],
  },
  {
    title: "NFC 贴纸写入",
    tag: "调试候选",
    type: "primary",
    lines: [
      "安卓助手写入员工固定短链（s=nfc，不带活动参数），写后回读校验；首版不提供永久锁卡。",
      "贴纸射频与采购验收尚未完成，结果以真机/贴纸矩阵记录为准。",
    ],
  },
  {
    title: "实物卡库存 / 绑定 / 挂失",
    tag: "暂缓",
    type: "warning",
    lines: [
      "物理卡登记、绑定、解绑、挂失和换人重新绑定尚未交付；贴纸写入不替代库存管理。",
      "本地候选不提供上述操作入口，也不会把修改员工名片当成物理卡管理。",
    ],
  },
] as const;
</script>
<template>
  <section class="page">
    <PageHeader
      title="交付范围 / NFC"
      desc="说明本地候选已交付与暂缓的能力，避免把未交付功能当作已完成。"
    />
    <div v-for="item in nfcItems" :key="item.title" class="panel">
      <div class="panel-head">
        <h2>{{ item.title }}</h2>
        <el-tag :type="item.type">{{ item.tag }}</el-tag>
      </div>
      <p v-for="line in item.lines" :key="line">{{ line }}</p>
    </div>
    <p class="muted">
      安装包：未发布，需要试用请联系项目负责人。帮助：员工端「我的 → NFC
      分享」。无法使用 NFC 时，请使用二维码或复制链接分享。NFC
      来源数据来自链接参数，属于渠道归因，不代表真实碰触次数。
    </p>
    <div class="panel">
      <div class="panel-head">
        <h2>后续原计划功能</h2>
        <el-tag type="info">待交付</el-tag>
      </div>
      <p>
        已提供员工Excel逐行导入与批量Markdown解析预览入口。文件夹递归导入、评测运行、产品配图上传及排序、来源分布与员工排行仍待交付。
      </p>
      <p class="muted">
        本地候选不代表完成原计划全量一期，也不代表真实模型评测或一周灰度通过。
      </p>
    </div>
  </section>
</template>
