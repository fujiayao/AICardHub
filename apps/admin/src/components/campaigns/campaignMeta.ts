import type { CampaignReport, CampaignStatus } from "@/api/schema";

export type CampaignSource = CampaignReport["source_breakdown"][number]["source"];

export const statusLabels: Record<CampaignStatus, string> = {
  draft: "草稿",
  active: "已启用",
  ended: "已结束",
};

export const statusTagType: Record<CampaignStatus, "info" | "success" | "warning"> = {
  draft: "info",
  active: "success",
  ended: "warning",
};

export const statusFilters: { value: CampaignStatus | ""; label: string }[] = [
  { value: "", label: "全部" },
  { value: "draft", label: "草稿" },
  { value: "active", label: "进行中" },
  { value: "ended", label: "已结束" },
];

export const sourceLabels: Record<CampaignSource, string> = {
  nfc: "NFC 碰一碰",
  qr: "二维码",
  poster: "海报",
  link: "分享链接",
  sig: "邮件签名",
};

const timeFormat = new Intl.DateTimeFormat("zh-CN", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

/** Server sends timezone-aware ISO strings; render in the viewer's local zone. */
export function formatTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : timeFormat.format(date);
}
