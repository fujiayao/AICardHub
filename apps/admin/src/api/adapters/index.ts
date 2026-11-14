import { operations as ops } from "../generated/operations";
import type {
  EmployeeInput,
  EmployeeUpdate,
  CardInput,
  Company,
  ProductInput,
  TemplateInput,
  AssistantInput,
  Note,
  IssueStatus,
  Staff,
} from "../schema";
export interface PageQuery {
  page?: number;
  page_size?: number;
  q?: string;
  status?: string;
}
export const api = {
  health: () => ops.health(),
  login: (body: { phone: string; password: string }) => ops.login({ body }),
  changePassword: (body: { old_password: string; new_password: string }) =>
    ops.changePassword({ body }),
  stats: () => ops.stats(),
  employees: (query: PageQuery) => ops.employees({ query }),
  createEmployee: (body: EmployeeInput) => ops.createEmployee({ body }),
  updateEmployee: (id: number, body: EmployeeUpdate) =>
    ops.updateEmployee({ path: { id }, body }),
  disableEmployee: (id: number) => ops.disableEmployee({ path: { id } }),
  resetPassword: (id: number, password: string) =>
    ops.resetPassword({ path: { id }, body: { password } }),
  transfer: (id: number, to_employee_id: number) =>
    ops.transfer({ path: { id }, body: { to_employee_id } }),
  company: () => ops.company(),
  saveCompany: (body: Company) => ops.saveCompany({ body }),
  products: () => ops.products(),
  saveProduct: (id: number | null, body: ProductInput) =>
    id
      ? ops.updateProduct({ path: { id }, body })
      : ops.createProduct({ body }),
  deleteProduct: (id: number) => ops.deleteProduct({ path: { id } }),
  templates: () => ops.templates(),
  saveTemplate: (id: number | null, body: TemplateInput) =>
    id
      ? ops.updateTemplate({ path: { id }, body })
      : ops.createTemplate({ body }),
  deleteTemplate: (id: number) => ops.deleteTemplate({ path: { id } }),
  defaultTemplate: (id: number) => ops.defaultTemplate({ path: { id } }),
  card: (code: string) => ops.card({ path: { code } }),
  saveCard: (code: string, body: CardInput) =>
    ops.saveCard({ path: { code }, body }),
  assistant: (code: string) => ops.assistant({ path: { code } }),
  saveAssistant: (code: string, body: AssistantInput) =>
    ops.saveAssistant({ path: { code }, body }),
  notes: (query: PageQuery) => ops.notes({ query }),
  note: (file_id: string) => ops.note({ path: { file_id } }),
  saveNote: (
    id: string | null,
    body: Pick<Note, "title" | "content" | "public" | "approved">,
  ) =>
    id
      ? ops.updateNote({ path: { file_id: id }, body })
      : ops.createNote({ body }),
  deleteNote: (file_id: string) => ops.deleteNote({ path: { file_id } }),
  history: (file_id: string) => ops.history({ path: { file_id } }),
  rollback: (file_id: string, revision: number) =>
    ops.rollback({ path: { file_id }, body: { revision } }),
  issues: (query: PageQuery) => ops.issues({ query }),
  issue: (id: number, status: IssueStatus) =>
    ops.issue({ path: { id }, body: { status } }),
  rules: () => ops.rules(),
  saveRules: (content: string) => ops.saveRules({ body: { content } }),
  setting: (key: string) => ops.setting({ path: { key } }),
  saveSetting: (key: string, value: unknown) =>
    ops.saveSetting({ path: { key }, body: { value } }),
  audits: (query: PageQuery) => ops.audits({ query }),
  leads: (query: PageQuery) => ops.leads({ query }),
};
export const maskPhone = (phone: string) =>
  phone.replace(/^(\d{3})\d{4}(\d+)$/, "$1****$2");
export const staffEnabled = (staff: Staff) => staff.status === "active";
