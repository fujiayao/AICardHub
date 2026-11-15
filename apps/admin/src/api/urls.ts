/** Router paths remain relative to the admin history base; these are service URLs. */
export function appBasePath(adminBase = import.meta.env.BASE_URL): string {
  return adminBase.replace(/\/+$/, "").replace(/\/admin$/, "");
}

export function apiUrl(
  path: string,
  adminBase = import.meta.env.BASE_URL,
): string {
  return serviceUrl(path, "/api", adminBase);
}

export function mediaUrl(
  path: string,
  adminBase = import.meta.env.BASE_URL,
): string {
  return serviceUrl(path, "/files", adminBase);
}

function serviceUrl(
  path: string,
  namespace: string,
  adminBase: string,
): string {
  if (!new RegExp(`^${namespace}(?:/|[?#]|$)`).test(path)) return path;
  return appBasePath(adminBase) + path;
}

// Public media fields from the frozen API schema. Never rewrite arbitrary strings.
const MEDIA_FIELDS = new Set([
  "logo_url",
  "image_url",
  "photo_url",
  "photo_bg_url",
  "wechat_qr_url",
  "qr_url",
  "poster_url",
]);

export function mapAssetPaths<T>(
  value: T,
  direction: "display" | "storage" = "display",
  adminBase = import.meta.env.BASE_URL,
): T {
  const transform = (item: unknown): unknown => {
    if (Array.isArray(item)) return item.map(transform);
    if (!item || typeof item !== "object") return item;
    return Object.fromEntries(
      Object.entries(item).map(([key, entry]) => {
        if (MEDIA_FIELDS.has(key) && typeof entry === "string") {
          const prefix = appBasePath(adminBase);
          const stored =
            prefix && entry.startsWith(prefix + "/files/")
              ? entry.slice(prefix.length)
              : entry;
          return [
            key,
            direction === "storage" ? stored : mediaUrl(entry, adminBase),
          ];
        }
        return [key, transform(entry)];
      }),
    );
  };
  return transform(value) as T;
}
