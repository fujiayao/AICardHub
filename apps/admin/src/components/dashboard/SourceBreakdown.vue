<script setup lang="ts">
// Traffic by entry source from GET /admin/stats `source_breakdown` (server counts only).
import { computed } from "vue";
import type { Stats } from "@/api/schema";
type Row = NonNullable<Stats["source_breakdown"]>[number];
const props = defineProps<{ rows: Stats["source_breakdown"] }>();
const order = ["nfc", "qr", "poster", "link", "sig"];
const labels: Record<string, string> = {
  nfc: "NFC 碰一碰",
  qr: "二维码",
  poster: "海报",
  link: "链接",
  sig: "邮件签名",
};
/** Unknown source codes are shown verbatim, never guessed. */
const labelOf = (code: string) => labels[code] ?? (code || "未标记");
const rank = (code: string) => {
  const i = order.indexOf(code);
  return i === -1 ? order.length : i;
};
// Hide rows where every metric is 0; keep rows with chats/leads but 0 visits.
const visible = computed<Row[]>(() =>
  (props.rows ?? [])
    .filter((r) => r.visits || r.visitors || r.chats || r.leads)
    .sort(
      (a, b) =>
        rank(a.source) - rank(b.source) || a.source.localeCompare(b.source),
    ),
);
const maxVisits = computed(() =>
  Math.max(0, ...visible.value.map((r) => r.visits)),
);
const pct = (v: number) => (maxVisits.value ? (v / maxVisits.value) * 100 : 0);
</script>
<template>
  <section class="panel" aria-labelledby="source-title">
    <div class="panel-head">
      <div>
        <h2 id="source-title">访问来源分布</h2>
        <p class="muted sub">近 7 天，按入口来源统计</p>
      </div>
    </div>
    <p v-if="!rows" class="empty">来源数据暂不可用</p>
    <p v-else-if="!visible.length" class="empty">暂无来源数据</p>
    <template v-else>
      <div class="table-wrap">
        <table class="src-table">
          <caption class="sr-only">
            各来源近 7 天访问量、访客数、对话数与线索数
          </caption>
          <thead>
            <tr>
              <th scope="col">来源</th>
              <th scope="col" class="bar-col">访问量</th>
              <th scope="col" class="num">访客</th>
              <th scope="col" class="num">对话</th>
              <th scope="col" class="num">线索</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in visible" :key="r.source">
              <th scope="row" class="name">{{ labelOf(r.source) }}</th>
              <td class="bar-col">
                <span class="bar-line">
                  <span class="track" aria-hidden="true"
                    ><span class="bar" :style="{ width: `${pct(r.visits)}%` }"
                  /></span>
                  <span class="num val">{{ r.visits }}</span>
                </span>
              </td>
              <td class="num">{{ r.visitors }}</td>
              <td class="num">{{ r.chats }}</td>
              <td class="num">{{ r.leads }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="note">
        条形长度按访问量对比。同一访客可能经多个来源进入，各来源访客数不可相加，总访客以上方指标为准。
      </p>
    </template>
  </section>
</template>
<style scoped>
.sub {
  margin: 2px 0 0;
  font-size: 12px;
}
.empty {
  margin: 0;
  padding: var(--ac-space-5) 0;
  text-align: center;
  color: var(--ac-text-muted);
  font-size: 14px;
}
.src-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.src-table th,
.src-table td {
  padding: var(--ac-space-2) var(--ac-space-3);
  border-bottom: 1px solid var(--ac-border);
  text-align: left;
  white-space: nowrap;
}
.src-table thead th {
  font-size: 12px;
  font-weight: 500;
  color: var(--ac-text-muted);
  background: var(--ac-surface-muted);
}
.name {
  font-weight: 500;
  color: var(--ac-text);
}
.bar-col {
  width: 50%;
  min-width: 160px;
}
.bar-line {
  display: flex;
  align-items: center;
  gap: var(--ac-space-2);
}
.track {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: var(--ac-surface-muted);
  border: 1px solid var(--ac-border);
  overflow: hidden;
}
.bar {
  display: block;
  height: 100%;
  background: var(--ac-primary);
  border-radius: 999px;
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.src-table td.num,
.src-table th.num {
  text-align: right;
}
.val {
  min-width: 3ch;
  color: var(--ac-text);
}
.note {
  margin: var(--ac-space-3) 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--ac-text-subtle);
}
</style>
