import type { Login } from "./schema";
export const SESSION_KEY = "aicardhub.admin.session.v1";
export function readSession(): Login | null {
  try {
    const raw: unknown = JSON.parse(
      sessionStorage.getItem(SESSION_KEY) ?? "null",
    );
    if (
      !raw ||
      typeof raw !== "object" ||
      !("token" in raw) ||
      typeof raw.token !== "string" ||
      !("staff" in raw) ||
      !raw.staff ||
      typeof raw.staff !== "object" ||
      !("role" in raw.staff) ||
      raw.staff.role !== "admin"
    )
      return null;
    return raw as Login;
  } catch {
    return null;
  }
}
export function tokenExpired(token: string): boolean {
  try {
    const part = token.split(".")[1];
    if (!part) return true;
    const p: unknown = JSON.parse(
      atob(part.replace(/-/g, "+").replace(/_/g, "/")),
    );
    return (
      !p ||
      typeof p !== "object" ||
      !("exp" in p) ||
      typeof p.exp !== "number" ||
      p.exp * 1000 <= Date.now()
    );
  } catch {
    return true;
  }
}
export function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
  window.dispatchEvent(new Event("admin-session-ended"));
}
