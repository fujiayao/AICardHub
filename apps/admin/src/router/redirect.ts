// Safe post-login redirect handling. Pure module: no store/router imports.
export const FALLBACK_TARGET = "/dashboard";
const AUTH_PATHS = ["/login", "/change-password"];
const ORIGIN = "http://admin.invalid";

const SCHEME = /^\/*[a-z][a-z0-9+.-]*:/i;
// eslint-disable-next-line no-control-regex
const CONTROL_OR_BACKSLASH = /[\u0000-\u001f\u007f\\]/;

/**
 * Returns a normalized internal path+query+hash, or null when unsafe.
 * The path is validated after a single decode and after URL normalization;
 * query/hash keep their original encoding (e.g. `q=100%25`) and are never
 * treated as part of the destination path.
 */
export function safeRedirect(raw: unknown): string | null {
  if (typeof raw !== "string" || raw.length === 0 || raw.length > 2048)
    return null;
  if (CONTROL_OR_BACKSLASH.test(raw)) return null;
  // Malformed percent escapes anywhere, encoded controls/backslash anywhere.
  if (/%(?![0-9a-f]{2})/i.test(raw)) return null;
  if (/%(?:[01][0-9a-f]|7f|5c)/i.test(raw)) return null;
  const rawPath = raw.split(/[?#]/, 1)[0];
  // Encoded slash / encoded percent in the path enable double-decode tricks.
  if (/%(?:2f|25)/i.test(rawPath)) return null;
  let decodedPath: string;
  try {
    decodedPath = decodeURIComponent(rawPath);
  } catch {
    return null;
  }
  for (const v of [rawPath, decodedPath]) {
    if (!v.startsWith("/") || v.startsWith("//")) return null;
    if (SCHEME.test(v) || CONTROL_OR_BACKSLASH.test(v)) return null;
  }
  let url: URL;
  try {
    url = new URL(raw, ORIGIN);
  } catch {
    return null;
  }
  if (url.origin !== ORIGIN) return null;
  // Revalidate the normalized destination ("/x/..//evil" → "//evil").
  let normalizedPath: string;
  try {
    normalizedPath = decodeURIComponent(url.pathname);
  } catch {
    return null;
  }
  for (const v of [url.pathname, normalizedPath]) {
    if (v.startsWith("//") || SCHEME.test(v) || CONTROL_OR_BACKSLASH.test(v))
      return null;
  }
  const authCheck = normalizedPath.replace(/\/+$/, "").toLowerCase() || "/";
  if (AUTH_PATHS.includes(authCheck)) return null;
  const output = `${url.pathname}${url.search}${url.hash}`;
  if (!output.startsWith("/") || output.startsWith("//")) return null;
  return output;
}

export function resolveTarget(raw: unknown): string {
  return safeRedirect(raw) ?? FALLBACK_TARGET;
}

/** Query object carrying the target, empty when unsafe or the fallback. */
export function redirectQuery(target: unknown): { redirect?: string } {
  const safe = safeRedirect(target);
  return safe && safe !== FALLBACK_TARGET && safe !== "/"
    ? { redirect: safe }
    : {};
}

// One-shot hand-off used when a password change invalidates the session:
// the session-ended listener consumes it to keep the original target.
let handoff: string | null = null;
export function setLoginHandoff(target: unknown) {
  handoff = safeRedirect(target);
}
export function takeLoginHandoff(): string | null {
  const value = handoff;
  handoff = null;
  return value;
}
