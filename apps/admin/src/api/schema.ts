/** All server models are aliases of generated backend OpenAPI; never edit generated sources. */
import type { components } from "./generated/schema";
type Schemas = components["schemas"];
export type Id = number;
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
export type Staff = Schemas["Staff"];
export type Login = Schemas["LoginResult"];
export type Company = Schemas["CompanyData"];
export type Product = Schemas["ProductData"];
export type Template = Schemas["TemplateData"];
export type Assistant = Schemas["AssistantData"];
export type Card = Schemas["CardData"];
export type Note = Schemas["NoteData"];
export type Revision = Schemas["HistoryData"];
export type Stats = Schemas["AdminStats"];
export type Issue = Schemas["IssueData"];
export type Lead = Schemas["LeadData"];
export type Audit = Schemas["AuditData"];
export type Setting = Schemas["SettingData"];
export type EmployeeInput = Schemas["EmployeeInput"];
export type EmployeeUpdate = Schemas["EmployeeUpdate"];
export type CardInput = Schemas["CardInput"];
export type ProductInput = Schemas["ProductInput"];
export type TemplateInput = Schemas["TemplateInput"];
export type AssistantInput = Schemas["AssistantInput"];
export type IssueStatus = Schemas["IssuePatch"]["status"];

// Contract v2 organization aliases (backend 66ae4a1 export).
export type CompanyOption = Schemas["CompanyOption"];
export type CompanyItem = Schemas["CompanyItem"];
export type CompanyInput = Company;

// Contract v2 campaign aliases (backend main export; admin campaign_* only).
export type Campaign = Schemas["CampaignData"];
export type CampaignInput = Schemas["CampaignInput"];
export type CampaignStatus = NonNullable<CampaignInput["status"]>;
export type CampaignReport = Schemas["CampaignReport"];
export type CampaignSourceRow = Schemas["SourceBreakdownRow"];

export type EmployeeImportResult = Schemas["EmployeeImportResult"];
export type KnowledgeUploadRow = Schemas["KnowledgeUploadRow"];
