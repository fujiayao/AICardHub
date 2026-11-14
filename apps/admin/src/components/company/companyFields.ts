import type { Field } from "@/components/FieldForm.vue";
import type { CompanyInput } from "@/api/schema";

/** Shared CompanyData fields (limits follow backend CompanyData). */
export const companyFields: Field[] = [
  { key: "name", label: "公司名称", required: true, max: 120 },
  { key: "short_name", label: "公司简称", max: 60 },
  { key: "intro", label: "公司简介", type: "textarea", max: 10000 },
  { key: "phone", label: "官方电话", max: 40 },
  { key: "address", label: "总部地址", max: 255 },
  { key: "website", label: "官方网站", type: "url", max: 255 },
  {
    key: "logo_url",
    label: "Logo 地址",
    type: "url",
    max: 500,
    hint: "填写已有的公开图片地址；本地契约暂无图片上传接口。",
  },
];

export function emptyCompany(): CompanyInput {
  return {
    name: "",
    short_name: "",
    intro: "",
    phone: "",
    address: "",
    website: "",
    logo_url: "",
    brand_color: "",
  };
}
