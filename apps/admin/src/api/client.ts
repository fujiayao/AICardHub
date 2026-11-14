import { ElMessage } from "element-plus";
import { readSession, tokenExpired, clearSession } from "./session";
export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}
export interface RequestOptions {
  path?: Record<string, string | number>;
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  signal?: AbortSignal;
}
export async function request<T>(
  method: string,
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  let path = endpoint;
  for (const [key, value] of Object.entries(options.path ?? {}))
    path = path.replace(`{${key}}`, encodeURIComponent(value));
  if (path.includes("{")) throw new Error("接口路径参数缺失");
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(options.query ?? {}))
    if (value !== undefined && value !== "") query.set(key, String(value));
  const session = readSession();
  const login = path === "/api/v1/admin/auth/login";
  if (!login && (!session || tokenExpired(session.token))) {
    clearSession();
    throw new ApiError("登录已过期，请重新登录", "UNAUTHORIZED", 401);
  }
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 30000);
  const abort = () => controller.abort();
  options.signal?.addEventListener("abort", abort, { once: true });
  const multipart = options.body instanceof FormData;
  try {
    const response = await fetch(path + (query.size ? `?${query}` : ""), {
      method,
      headers: {
        ...(!multipart ? { "Content-Type": "application/json" } : {}),
        ...(!login && session
          ? { Authorization: `Bearer ${session.token}` }
          : {}),
      },
      body:
        options.body === undefined
          ? undefined
          : multipart
            ? (options.body as FormData)
            : JSON.stringify(options.body),
      signal: controller.signal,
    });
    if (response.status === 204) return undefined as T;
    const data: unknown = await response.json();
    if (!response.ok) {
      const detail = data && typeof data === "object" ? data : {};
      const message =
        "message" in detail && typeof detail.message === "string"
          ? detail.message
          : `请求未完成（${response.status}），请核对输入后重试`;
      const code = "code" in detail ? String(detail.code) : "HTTP_ERROR";
      if (response.status === 401 && !login) clearSession();
      if (
        response.status === 403 &&
        /PASSWORD_CHANGE_REQUIRED|MUST_CHANGE_PASSWORD|PASSWORD_CHANGE/i.test(
          code,
        )
      )
        window.dispatchEvent(new Event("admin-password-required"));
      throw new ApiError(message, code, response.status);
    }
    return data as T;
  } catch (error) {
    if (options.signal?.aborted) throw error;
    const normalized =
      error instanceof ApiError
        ? error
        : new ApiError(
            error instanceof DOMException && error.name === "AbortError"
              ? "请求超时，请重试"
              : "无法连接服务，请检查后端是否启动",
            "NETWORK_ERROR",
            0,
          );
    ElMessage.error(normalized.message);
    throw normalized;
  } finally {
    window.clearTimeout(timeout);
    options.signal?.removeEventListener("abort", abort);
  }
}
