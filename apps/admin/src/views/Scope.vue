<!-- C8 NFC 分享与贴纸使用说明 -->
<script setup lang="ts">
import PageHeader from "@/components/shared/PageHeader.vue";

function downloadUrl(value: unknown): string {
  try {
    if (typeof value !== "string" || !value.trim()) return "";
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password
      ? url.href
      : "";
  } catch {
    return "";
  }
}
const apkUrl = downloadUrl(import.meta.env.VITE_NFC_APK_URL);
const nfcItems = [
  {
    title: "手机 NFC 分享",
    tag: "可使用",
    type: "success",
    lines: [
      "员工在 H5「发送名片 → 手机 NFC」打开安卓 NFC 助手，模拟标准 NDEF 网址；接收方安卓与 iPhone 由系统读取后打开 H5 名片。",
      "使用安卓浏览器打开员工端，先下载安装助手；iPhone 作为接收方，靠近后按系统通知打开名片。",
    ],
  },
  {
    title: "NFC 贴纸写入",
    tag: "可使用",
    type: "success",
    lines: [
      "安卓助手写入员工固定短链（s=nfc，不带活动参数），写后回读校验；首版不提供永久锁卡。",
      "写入前检查贴纸是否可写及容量，写入后立即回读。请保持贴紧，看到“写入完成”后再移开。",
    ],
  },
  {
    title: "实物卡库存 / 绑定 / 挂失",
    tag: "暂缓",
    type: "warning",
    lines: [
      "物理卡登记、绑定、解绑、挂失和换人重新绑定尚未交付；贴纸写入不替代库存管理。",
      "固定名片链接可重复写入贴纸；需要更换员工时请重新写入，员工停用会同步关闭对应名片。",
    ],
  },
] as const;
</script>
<template>
  <section class="page">
    <PageHeader
      title="NFC 分享与贴纸"
      desc="使用安卓手机递名片或写入 NFC 贴纸，接收方通过系统读取并打开名片。"
    />
    <div v-for="item in nfcItems" :key="item.title" class="panel">
      <div class="panel-head">
        <h2>{{ item.title }}</h2>
        <el-tag :type="item.type">{{ item.tag }}</el-tag>
      </div>
      <p v-for="line in item.lines" :key="line">{{ line }}</p>
    </div>
    <p class="muted">
      帮助：员工端「我的 → NFC
      分享」。使用手机模拟名片时，请保持助手前台、亮屏并解锁。无法使用 NFC
      时，请使用二维码或复制链接分享。NFC
      来源数据来自链接参数，属于渠道归因，不代表真实碰触次数。
    </p>
    <p v-if="apkUrl">
      <el-button
        type="primary"
        tag="a"
        :href="apkUrl"
        target="_blank"
        rel="noopener"
        >下载安卓 NFC 助手</el-button
      >
    </p>
    <div class="panel">
      <div class="panel-head">
        <h2>其他功能进度</h2>
        <el-tag type="info">待交付</el-tag>
      </div>
      <p>
        已提供员工Excel逐行导入与批量Markdown解析预览入口。文件夹递归导入、评测运行、产品配图上传及排序、来源分布与员工排行仍待交付。
      </p>
      <p class="muted">
        上述功能按各自计划推进，不影响当前 NFC 分享与贴纸操作。
      </p>
    </div>
  </section>
</template>
