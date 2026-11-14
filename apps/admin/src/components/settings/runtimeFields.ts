// Fixed keys/ranges agreed with backend RuntimeSettings; unknown keys cannot be edited.
export interface RuntimeField {
  key: string;
  label: string;
  group: string;
  kind:
    | "text"
    | "url"
    | "number"
    | "boolean"
    | "secret"
    | "mode"
    | "words"
    | "protocol";
  min?: number;
  max?: number;
  integer?: boolean;
  hint?: string;
}
export type ProviderPrefix = "llm" | "llm_fallback" | "llm_tertiary";
const protocols = ["responses", "chat_completions"] as const;
function providerFields(prefix: ProviderPrefix, label: string): RuntimeField[] {
  return [
    {
      key: prefix + "_base_url",
      label: label + "接口地址",
      group: label,
      kind: "url",
      max: 500,
    },
    {
      key: prefix + "_model",
      label: label + "名称",
      group: label,
      kind: "text",
      max: 160,
    },
    {
      key: prefix + "_api_mode",
      label: label + "接口协议",
      group: label,
      kind: "protocol",
    },
    {
      key: prefix + "_api_key",
      label: label + "密钥",
      group: label,
      kind: "secret",
      max: 4096,
    },
    ...(prefix === "llm"
      ? []
      : [
          {
            key: prefix + "_enabled",
            label: "启用" + label,
            group: label,
            kind: "boolean" as const,
          },
        ]),
  ];
}
export const runtimeFields: RuntimeField[] = [
  ...providerFields("llm", "主模型"),
  {
    key: "llm_timeout",
    label: "模型超时（秒）",
    group: "主模型",
    kind: "number",
    min: 1,
    max: 120,
  },
  { key: "llm_mode", label: "模型运行方式", group: "主模型", kind: "mode" },
  ...providerFields("llm_fallback", "备用模型"),
  ...providerFields("llm_tertiary", "兜底模型"),
  {
    key: "visitor_daily_limit",
    label: "单访客每日对话次数",
    group: "限额",
    kind: "number",
    min: 1,
    max: 100000,
    integer: true,
  },
  {
    key: "card_daily_limit",
    label: "单名片每日对话次数",
    group: "限额",
    kind: "number",
    min: 1,
    max: 10000000,
    integer: true,
  },
  {
    key: "global_daily_limit",
    label: "全局每日对话次数",
    group: "限额",
    kind: "number",
    min: 1,
    max: 100000000,
    integer: true,
  },
  {
    key: "test_retention_days",
    label: "测试对话保留天数",
    group: "数据保留",
    kind: "number",
    min: 1,
    max: 3650,
    integer: true,
  },
  {
    key: "notification_retention_days",
    label: "通知保留天数",
    group: "数据保留",
    kind: "number",
    min: 1,
    max: 3650,
    integer: true,
  },
  {
    key: "visitor_retention_days",
    label: "访客与对话保留天数",
    group: "数据保留",
    kind: "number",
    min: 1,
    max: 3650,
    integer: true,
  },
  {
    key: "sensitive_words",
    label: "敏感词（每行一个）",
    group: "内容规则",
    kind: "words",
    hint: "最多200个，每项1–100字；从下一次对话请求开始应用。",
  },
];
export interface RuntimeSnapshot {
  values: Record<string, unknown>;
  configured: Record<string, boolean>;
  supported: string[];
}
export function sanitizeRuntime(
  settings: Record<string, unknown>,
): RuntimeSnapshot {
  const values: Record<string, unknown> = {},
    configured: Record<string, boolean> = {};
  for (const field of runtimeFields) {
    if (!Object.hasOwn(settings, field.key)) continue;
    const value = settings[field.key];
    if (field.kind === "secret") {
      configured[field.key] = typeof value === "string" && value.length > 0;
    } else values[field.key] = value;
  }
  return {
    values,
    configured,
    supported: runtimeFields
      .filter((field) => Object.hasOwn(settings, field.key))
      .map((field) => field.key),
  };
}
export function providerReady(
  snapshot: RuntimeSnapshot,
  prefix: ProviderPrefix = "llm",
): boolean {
  return (
    ["_base_url", "_model"].every(
      (suffix) =>
        typeof snapshot.values[prefix + suffix] === "string" &&
        String(snapshot.values[prefix + suffix]).trim().length > 0,
    ) &&
    protocols.includes(
      snapshot.values[prefix + "_api_mode"] as (typeof protocols)[number],
    ) &&
    snapshot.configured[prefix + "_api_key"] === true
  );
}
export function canActivate(snapshot: RuntimeSnapshot): boolean {
  return (
    providerReady(snapshot) &&
    (!snapshot.values.llm_fallback_enabled ||
      providerReady(snapshot, "llm_fallback")) &&
    (!snapshot.values.llm_tertiary_enabled ||
      providerReady(snapshot, "llm_tertiary"))
  );
}
export function validateRuntimeValue(
  field: RuntimeField,
  value: unknown,
): unknown {
  if (field.kind === "number") {
    if (
      typeof value !== "number" ||
      !Number.isFinite(value) ||
      value < (field.min ?? 0) ||
      value > (field.max ?? Infinity) ||
      (field.integer && !Number.isInteger(value))
    )
      throw new Error(
        `请输入${field.min}–${field.max}${field.integer ? "之间的整数" : "之间的数字"}`,
      );
    return value;
  }
  if (field.kind === "boolean") {
    if (typeof value !== "boolean") throw new Error("请选择启用状态");
    return value;
  }
  if (field.kind === "mode") {
    if (value !== "fake" && value !== "openai")
      throw new Error("请选择允许的模型方式");
    return value;
  }
  if (field.kind === "protocol") {
    if (value !== "responses" && value !== "chat_completions")
      throw new Error("请选择支持的接口协议");
    return value;
  }
  if (field.kind === "words") {
    if (typeof value !== "string") throw new Error("请按每行一项填写敏感词");
    const words = value
      .split("\n")
      .map((word) => word.trim())
      .filter(Boolean);
    if (words.length > 200 || words.some((word) => word.length > 100))
      throw new Error("最多200个敏感词，每项不超过100字");
    return [...new Set(words)];
  }
  if (typeof value !== "string") throw new Error("请填写文本");
  if (value.length > (field.max ?? 500)) throw new Error("内容长度超过限制");
  if (field.kind === "secret") {
    if (!value.trim() || value === "********")
      throw new Error("请输入新密钥；空值及掩码不会覆盖已有密钥");
    return value;
  }
  if (field.kind === "url" && value) {
    let url: URL;
    try {
      url = new URL(value);
    } catch {
      throw new Error("请输入有效的 http(s) 接口地址");
    }
    if (
      !["http:", "https:"].includes(url.protocol) ||
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      value.includes("\\") ||
      [...value].some((char) => char.charCodeAt(0) < 32)
    )
      throw new Error("接口地址不得包含凭据、查询参数或片段");
  }
  return value;
}

export function providerForKey(key: string): ProviderPrefix {
  return key.startsWith("llm_tertiary_")
    ? "llm_tertiary"
    : key.startsWith("llm_fallback_")
      ? "llm_fallback"
      : "llm";
}
export function canClearSecret(
  snapshot: RuntimeSnapshot,
  key: string,
): boolean {
  if (snapshot.values.llm_mode === "fake") return true;
  const prefix = providerForKey(key);
  return prefix !== "llm" && snapshot.values[prefix + "_enabled"] !== true;
}
