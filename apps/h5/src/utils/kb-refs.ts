// 知识引用 kb_refs → 公开可读标签。契约类型为 unknown[]：实际观察到字符串标识（如 "demo-public"），
// 也兼容对象形态（title / category / name）。任何疑似文件路径、内部/私有标识一律映射为通用标签，绝不外显路径。
export const GENERIC_REF_LABEL = '知识资料'

const CATEGORY_LABELS: Record<string, string> = {
  company: '公司资料',
  product: '产品资料',
  products: '产品资料',
  card: '名片资料',
  cards: '名片资料',
  faq: '常见问题',
  note: '员工笔记',
  notes: '员工笔记',
  correction: '纠错记录',
  corrections: '纠错记录',
  public: '公开资料',
}

const PRIVATE_HINT = /private|internal|secret|personal|staff[-_]?only|私有|内部/i
const PATH_LIKE = /[\\/]|\.(?:md|txt|pdf|docx?|json|ya?ml|csv)$|^[a-z]:/i

function fromIdentifier(raw: string): string {
  const value = raw.trim()
  if (!value || PRIVATE_HINT.test(value) || PATH_LIKE.test(value)) return GENERIC_REF_LABEL
  const key = value.toLowerCase().split(/[-_:.\s]/)[0] ?? ''
  if (CATEGORY_LABELS[key]) return CATEGORY_LABELS[key]
  // 公开标识但无法识别分类：仍用通用标签，避免把内部命名当作标题展示
  return GENERIC_REF_LABEL
}

function readField(ref: object, field: string): string {
  const value: unknown = (ref as Record<string, unknown>)[field]
  return typeof value === 'string' ? value.trim() : ''
}

function fromObject(ref: object): string {
  const scope = readField(ref, 'scope') || readField(ref, 'visibility')
  if (scope && PRIVATE_HINT.test(scope)) return GENERIC_REF_LABEL
  const title = readField(ref, 'title') || readField(ref, 'name')
  if (title && !PATH_LIKE.test(title) && !PRIVATE_HINT.test(title)) return title.slice(0, 40)
  const category = readField(ref, 'category') || readField(ref, 'type')
  if (category) return fromIdentifier(category)
  return GENERIC_REF_LABEL
}

/** 返回去重后的公开标签列表 */
export function publicRefLabels(refs: readonly unknown[] | null | undefined): string[] {
  if (!refs?.length) return []
  const labels = refs.map((ref) => {
    if (typeof ref === 'string') return fromIdentifier(ref)
    if (ref && typeof ref === 'object') return fromObject(ref)
    return GENERIC_REF_LABEL
  })
  return [...new Set(labels)]
}
