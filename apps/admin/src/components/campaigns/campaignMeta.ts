import type {
  Campaign,
  CampaignInput,
  CampaignSourceRow,
  CampaignStatus,
} from "@/api/schema";

export const statusLabels: Record<CampaignStatus, string> = {
  draft: "草稿",
  active: "已启用",
  ended: "已结束",
};

export const statusTagType: Record<
  CampaignStatus,
  "info" | "success" | "warning"
> = {
  draft: "info",
  active: "success",
  ended: "warning",
};

export const campaignStatuses: CampaignStatus[] = ["draft", "active", "ended"];

export const statusFilters: { value: CampaignStatus | ""; label: string }[] = [
  { value: "", label: "全部" },
  { value: "draft", label: "草稿" },
  { value: "active", label: "已启用" },
  { value: "ended", label: "已结束" },
];

const sourceLabels: Record<string, string> = {
  nfc: "NFC",
  qr: "二维码",
  poster: "海报",
  link: "链接",
  sig: "邮件签名",
};
/** Source codes are server strings; unknown codes are shown verbatim, never guessed. */
export const sourceName = (row: CampaignSourceRow) =>
  sourceLabels[row.source] ?? row.source;

/** Apply backend schema defaults (draft / "" / []) for fields the generated type may omit. */
export function toCampaignInput(
  row: Campaign | CampaignInput | null,
): CampaignInput {
  return {
    name: row?.name ?? "",
    status: row?.status ?? "draft",
    start_at: row?.start_at ?? "",
    end_at: row?.end_at ?? "",
    booth: row?.booth ?? "",
    location: row?.location ?? "",
    opening_override: row?.opening_override ?? "",
    guide_override: [...(row?.guide_override ?? [])],
  };
}
export const guidesOf = (row: Campaign) => row.guide_override ?? [];
export const statusOf = (row: Campaign): CampaignStatus =>
  row.status ?? "draft";

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
