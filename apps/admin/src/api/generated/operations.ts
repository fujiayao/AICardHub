// Generated from backend OpenAPI. DO NOT EDIT. Source SHA256: 6e06c35ef71cd5cd99b25f7047942d3cea3197a7fe26c99938859040af1bfadc
import type { paths } from "./schema";
import { request } from "../client";
type Json<T> = T extends { content: { "application/json": infer J } }
  ? J
  : never;
type Param<T, K extends PropertyKey> = T extends { parameters: infer P }
  ? K extends keyof P
    ? NonNullable<P[K]>
    : Record<string, never>
  : Record<string, never>;
type Body<T> = T extends { requestBody: infer B } ? Json<B> : never;
type Result<T> = T extends { responses: infer R }
  ? {
      [K in keyof R]: K extends 200 | 201 | 202
        ? Json<R[K]>
        : K extends 204
          ? void
          : never;
    }[keyof R]
  : never;

/** health: GET /api/v1/health */
export function api_health(
  options: { signal?: AbortSignal } = {},
): Promise<Result<paths["/api/v1/health"]["get"]>> {
  return request("GET", "/api/v1/health", { signal: options.signal });
}

/** login: POST /api/v1/admin/auth/login */
export function admin_auth_login(options: {
  body: Body<paths["/api/v1/admin/auth/login"]["post"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/auth/login"]["post"]>> {
  return request("POST", "/api/v1/admin/auth/login", {
    body: options.body,
    signal: options.signal,
  });
}

/** changePassword: POST /api/v1/auth/change-password */
export function auth_change_password(options: {
  body: Body<paths["/api/v1/auth/change-password"]["post"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/auth/change-password"]["post"]>> {
  return request("POST", "/api/v1/auth/change-password", {
    body: options.body,
    signal: options.signal,
  });
}

/** stats: GET /api/v1/admin/stats */
export function admin_stats(
  options: {
    query?: Param<paths["/api/v1/admin/stats"]["get"], "query">;
    signal?: AbortSignal;
  } = {},
): Promise<Result<paths["/api/v1/admin/stats"]["get"]>> {
  return request("GET", "/api/v1/admin/stats", {
    query: options.query,
    signal: options.signal,
  });
}

/** employees: GET /api/v1/admin/employees */
export function employee_list(
  options: {
    query?: Param<paths["/api/v1/admin/employees"]["get"], "query">;
    signal?: AbortSignal;
  } = {},
): Promise<Result<paths["/api/v1/admin/employees"]["get"]>> {
  return request("GET", "/api/v1/admin/employees", {
    query: options.query,
    signal: options.signal,
  });
}

/** createEmployee: POST /api/v1/admin/employees */
export function employee_create(options: {
  body: Body<paths["/api/v1/admin/employees"]["post"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/employees"]["post"]>> {
  return request("POST", "/api/v1/admin/employees", {
    body: options.body,
    signal: options.signal,
  });
}

/** updateEmployee: PUT /api/v1/admin/employees/{id} */
export function employee_update(options: {
  path: Param<paths["/api/v1/admin/employees/{id}"]["put"], "path">;
  body: Body<paths["/api/v1/admin/employees/{id}"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/employees/{id}"]["put"]>> {
  return request("PUT", "/api/v1/admin/employees/{id}", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** disableEmployee: POST /api/v1/admin/employees/{id}/disable */
export function employee_disable(options: {
  path: Param<paths["/api/v1/admin/employees/{id}/disable"]["post"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/employees/{id}/disable"]["post"]>> {
  return request("POST", "/api/v1/admin/employees/{id}/disable", {
    path: options.path,
    signal: options.signal,
  });
}

/** resetPassword: POST /api/v1/admin/employees/{id}/reset-password */
export function employee_reset_password(options: {
  path: Param<
    paths["/api/v1/admin/employees/{id}/reset-password"]["post"],
    "path"
  >;
  body: Body<paths["/api/v1/admin/employees/{id}/reset-password"]["post"]>;
  signal?: AbortSignal;
}): Promise<
  Result<paths["/api/v1/admin/employees/{id}/reset-password"]["post"]>
> {
  return request("POST", "/api/v1/admin/employees/{id}/reset-password", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** transfer: POST /api/v1/admin/employees/{id}/transfer */
export function employee_transfer(options: {
  path: Param<paths["/api/v1/admin/employees/{id}/transfer"]["post"], "path">;
  body: Body<paths["/api/v1/admin/employees/{id}/transfer"]["post"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/employees/{id}/transfer"]["post"]>> {
  return request("POST", "/api/v1/admin/employees/{id}/transfer", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** company: GET /api/v1/admin/company */
export function company_get(
  options: { signal?: AbortSignal } = {},
): Promise<Result<paths["/api/v1/admin/company"]["get"]>> {
  return request("GET", "/api/v1/admin/company", { signal: options.signal });
}

/** saveCompany: PUT /api/v1/admin/company */
export function company_update(options: {
  body: Body<paths["/api/v1/admin/company"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/company"]["put"]>> {
  return request("PUT", "/api/v1/admin/company", {
    body: options.body,
    signal: options.signal,
  });
}

/** products: GET /api/v1/admin/product-cards */
export function product_card_list(
  options: { signal?: AbortSignal } = {},
): Promise<Result<paths["/api/v1/admin/product-cards"]["get"]>> {
  return request("GET", "/api/v1/admin/product-cards", {
    signal: options.signal,
  });
}

/** createProduct: POST /api/v1/admin/product-cards */
export function product_card_create(options: {
  body: Body<paths["/api/v1/admin/product-cards"]["post"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/product-cards"]["post"]>> {
  return request("POST", "/api/v1/admin/product-cards", {
    body: options.body,
    signal: options.signal,
  });
}

/** updateProduct: PUT /api/v1/admin/product-cards/{id} */
export function product_card_update(options: {
  path: Param<paths["/api/v1/admin/product-cards/{id}"]["put"], "path">;
  body: Body<paths["/api/v1/admin/product-cards/{id}"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/product-cards/{id}"]["put"]>> {
  return request("PUT", "/api/v1/admin/product-cards/{id}", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** deleteProduct: DELETE /api/v1/admin/product-cards/{id} */
export function product_card_delete(options: {
  path: Param<paths["/api/v1/admin/product-cards/{id}"]["delete"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/product-cards/{id}"]["delete"]>> {
  return request("DELETE", "/api/v1/admin/product-cards/{id}", {
    path: options.path,
    signal: options.signal,
  });
}

/** templates: GET /api/v1/admin/templates */
export function template_list(
  options: { signal?: AbortSignal } = {},
): Promise<Result<paths["/api/v1/admin/templates"]["get"]>> {
  return request("GET", "/api/v1/admin/templates", { signal: options.signal });
}

/** createTemplate: POST /api/v1/admin/templates */
export function template_create(options: {
  body: Body<paths["/api/v1/admin/templates"]["post"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/templates"]["post"]>> {
  return request("POST", "/api/v1/admin/templates", {
    body: options.body,
    signal: options.signal,
  });
}

/** updateTemplate: PUT /api/v1/admin/templates/{id} */
export function template_update(options: {
  path: Param<paths["/api/v1/admin/templates/{id}"]["put"], "path">;
  body: Body<paths["/api/v1/admin/templates/{id}"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/templates/{id}"]["put"]>> {
  return request("PUT", "/api/v1/admin/templates/{id}", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** deleteTemplate: DELETE /api/v1/admin/templates/{id} */
export function template_delete(options: {
  path: Param<paths["/api/v1/admin/templates/{id}"]["delete"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/templates/{id}"]["delete"]>> {
  return request("DELETE", "/api/v1/admin/templates/{id}", {
    path: options.path,
    signal: options.signal,
  });
}

/** defaultTemplate: PUT /api/v1/admin/templates/{id}/default */
export function template_set_default(options: {
  path: Param<paths["/api/v1/admin/templates/{id}/default"]["put"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/templates/{id}/default"]["put"]>> {
  return request("PUT", "/api/v1/admin/templates/{id}/default", {
    path: options.path,
    signal: options.signal,
  });
}

/** card: GET /api/v1/admin/cards/{code} */
export function admin_card_get(options: {
  path: Param<paths["/api/v1/admin/cards/{code}"]["get"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/cards/{code}"]["get"]>> {
  return request("GET", "/api/v1/admin/cards/{code}", {
    path: options.path,
    signal: options.signal,
  });
}

/** saveCard: PUT /api/v1/admin/cards/{code} */
export function admin_card_update(options: {
  path: Param<paths["/api/v1/admin/cards/{code}"]["put"], "path">;
  body: Body<paths["/api/v1/admin/cards/{code}"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/cards/{code}"]["put"]>> {
  return request("PUT", "/api/v1/admin/cards/{code}", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** assistant: GET /api/v1/admin/cards/{code}/assistant */
export function admin_card_assistant_get(options: {
  path: Param<paths["/api/v1/admin/cards/{code}/assistant"]["get"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/cards/{code}/assistant"]["get"]>> {
  return request("GET", "/api/v1/admin/cards/{code}/assistant", {
    path: options.path,
    signal: options.signal,
  });
}

/** saveAssistant: PUT /api/v1/admin/cards/{code}/assistant */
export function admin_card_assistant_update(options: {
  path: Param<paths["/api/v1/admin/cards/{code}/assistant"]["put"], "path">;
  body: Body<paths["/api/v1/admin/cards/{code}/assistant"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/cards/{code}/assistant"]["put"]>> {
  return request("PUT", "/api/v1/admin/cards/{code}/assistant", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** notes: GET /api/v1/admin/kb/files */
export function kb_admin_list(
  options: {
    query?: Param<paths["/api/v1/admin/kb/files"]["get"], "query">;
    signal?: AbortSignal;
  } = {},
): Promise<Result<paths["/api/v1/admin/kb/files"]["get"]>> {
  return request("GET", "/api/v1/admin/kb/files", {
    query: options.query,
    signal: options.signal,
  });
}

/** note: GET /api/v1/admin/kb/files/{file_id} */
export function kb_admin_get(options: {
  path: Param<paths["/api/v1/admin/kb/files/{file_id}"]["get"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/kb/files/{file_id}"]["get"]>> {
  return request("GET", "/api/v1/admin/kb/files/{file_id}", {
    path: options.path,
    signal: options.signal,
  });
}

/** createNote: POST /api/v1/admin/kb/files */
export function kb_admin_create(options: {
  body: Body<paths["/api/v1/admin/kb/files"]["post"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/kb/files"]["post"]>> {
  return request("POST", "/api/v1/admin/kb/files", {
    body: options.body,
    signal: options.signal,
  });
}

/** updateNote: PUT /api/v1/admin/kb/files/{file_id} */
export function kb_admin_update(options: {
  path: Param<paths["/api/v1/admin/kb/files/{file_id}"]["put"], "path">;
  body: Body<paths["/api/v1/admin/kb/files/{file_id}"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/kb/files/{file_id}"]["put"]>> {
  return request("PUT", "/api/v1/admin/kb/files/{file_id}", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** deleteNote: DELETE /api/v1/admin/kb/files/{file_id} */
export function kb_admin_delete(options: {
  path: Param<paths["/api/v1/admin/kb/files/{file_id}"]["delete"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/kb/files/{file_id}"]["delete"]>> {
  return request("DELETE", "/api/v1/admin/kb/files/{file_id}", {
    path: options.path,
    signal: options.signal,
  });
}

/** history: GET /api/v1/admin/kb/files/{file_id}/history */
export function kb_admin_history(options: {
  path: Param<paths["/api/v1/admin/kb/files/{file_id}/history"]["get"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/kb/files/{file_id}/history"]["get"]>> {
  return request("GET", "/api/v1/admin/kb/files/{file_id}/history", {
    path: options.path,
    signal: options.signal,
  });
}

/** rollback: POST /api/v1/admin/kb/files/{file_id}/rollback */
export function kb_admin_rollback(options: {
  path: Param<
    paths["/api/v1/admin/kb/files/{file_id}/rollback"]["post"],
    "path"
  >;
  body: Body<paths["/api/v1/admin/kb/files/{file_id}/rollback"]["post"]>;
  signal?: AbortSignal;
}): Promise<
  Result<paths["/api/v1/admin/kb/files/{file_id}/rollback"]["post"]>
> {
  return request("POST", "/api/v1/admin/kb/files/{file_id}/rollback", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** issues: GET /api/v1/admin/issues */
export function issue_list(
  options: {
    query?: Param<paths["/api/v1/admin/issues"]["get"], "query">;
    signal?: AbortSignal;
  } = {},
): Promise<Result<paths["/api/v1/admin/issues"]["get"]>> {
  return request("GET", "/api/v1/admin/issues", {
    query: options.query,
    signal: options.signal,
  });
}

/** issue: PATCH /api/v1/admin/issues/{id} */
export function issue_update(options: {
  path: Param<paths["/api/v1/admin/issues/{id}"]["patch"], "path">;
  body: Body<paths["/api/v1/admin/issues/{id}"]["patch"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/issues/{id}"]["patch"]>> {
  return request("PATCH", "/api/v1/admin/issues/{id}", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** rules: GET /api/v1/admin/rules */
export function rules_get(
  options: { signal?: AbortSignal } = {},
): Promise<Result<paths["/api/v1/admin/rules"]["get"]>> {
  return request("GET", "/api/v1/admin/rules", { signal: options.signal });
}

/** saveRules: PUT /api/v1/admin/rules */
export function rules_update(options: {
  body: Body<paths["/api/v1/admin/rules"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/rules"]["put"]>> {
  return request("PUT", "/api/v1/admin/rules", {
    body: options.body,
    signal: options.signal,
  });
}

/** setting: GET /api/v1/admin/settings/{key} */
export function settings_get(options: {
  path: Param<paths["/api/v1/admin/settings/{key}"]["get"], "path">;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/settings/{key}"]["get"]>> {
  return request("GET", "/api/v1/admin/settings/{key}", {
    path: options.path,
    signal: options.signal,
  });
}

/** saveSetting: PUT /api/v1/admin/settings/{key} */
export function settings_update(options: {
  path: Param<paths["/api/v1/admin/settings/{key}"]["put"], "path">;
  body: Body<paths["/api/v1/admin/settings/{key}"]["put"]>;
  signal?: AbortSignal;
}): Promise<Result<paths["/api/v1/admin/settings/{key}"]["put"]>> {
  return request("PUT", "/api/v1/admin/settings/{key}", {
    path: options.path,
    body: options.body,
    signal: options.signal,
  });
}

/** audits: GET /api/v1/admin/audit-logs */
export function audit_log_list(
  options: {
    query?: Param<paths["/api/v1/admin/audit-logs"]["get"], "query">;
    signal?: AbortSignal;
  } = {},
): Promise<Result<paths["/api/v1/admin/audit-logs"]["get"]>> {
  return request("GET", "/api/v1/admin/audit-logs", {
    query: options.query,
    signal: options.signal,
  });
}

/** leads: GET /api/v1/admin/leads */
export function admin_lead_list(
  options: {
    query?: Param<paths["/api/v1/admin/leads"]["get"], "query">;
    signal?: AbortSignal;
  } = {},
): Promise<Result<paths["/api/v1/admin/leads"]["get"]>> {
  return request("GET", "/api/v1/admin/leads", {
    query: options.query,
    signal: options.signal,
  });
}

export const operations = {
  health: api_health,
  login: admin_auth_login,
  changePassword: auth_change_password,
  stats: admin_stats,
  employees: employee_list,
  createEmployee: employee_create,
  updateEmployee: employee_update,
  disableEmployee: employee_disable,
  resetPassword: employee_reset_password,
  transfer: employee_transfer,
  company: company_get,
  saveCompany: company_update,
  products: product_card_list,
  createProduct: product_card_create,
  updateProduct: product_card_update,
  deleteProduct: product_card_delete,
  templates: template_list,
  createTemplate: template_create,
  updateTemplate: template_update,
  deleteTemplate: template_delete,
  defaultTemplate: template_set_default,
  card: admin_card_get,
  saveCard: admin_card_update,
  assistant: admin_card_assistant_get,
  saveAssistant: admin_card_assistant_update,
  notes: kb_admin_list,
  note: kb_admin_get,
  createNote: kb_admin_create,
  updateNote: kb_admin_update,
  deleteNote: kb_admin_delete,
  history: kb_admin_history,
  rollback: kb_admin_rollback,
  issues: issue_list,
  issue: issue_update,
  rules: rules_get,
  saveRules: rules_update,
  setting: settings_get,
  saveSetting: settings_update,
  audits: audit_log_list,
  leads: admin_lead_list,
};
