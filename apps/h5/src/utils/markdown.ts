// 极简、安全的 Markdown 解析：只产出结构化数据，由组件用文本插值渲染（禁止 v-html）。
// 支持：段落、无序/有序列表、# ~ ### 标题、**加粗**。其余语法按纯文本显示。
export interface MdInline { text: string, bold?: boolean }
export interface MdBlock { type: 'p' | 'ul' | 'ol' | 'h', items: MdInline[][] }

export function parseInline(line: string): MdInline[] {
  const parts: MdInline[] = []
  let rest = line
  while (rest) {
    const start = rest.indexOf('**')
    const end = start < 0 ? -1 : rest.indexOf('**', start + 2)
    if (start < 0 || end < 0 || end === start + 2) { parts.push({ text: rest }); break }
    if (start > 0) parts.push({ text: rest.slice(0, start) })
    parts.push({ text: rest.slice(start + 2, end), bold: true })
    rest = rest.slice(end + 2)
  }
  return parts.length ? parts : [{ text: line }]
}

type LineKind = { kind: 'h' | 'ul' | 'ol' | 'p', body: string }

/** 逐字符识别行首标记，避免回溯型正则 */
function classify(line: string): LineKind {
  let hashes = 0
  while (hashes < line.length && line[hashes] === '#') hashes++
  if (hashes >= 1 && hashes <= 3 && line[hashes] === ' ') return { kind: 'h', body: line.slice(hashes + 1).trim() }
  if ((line[0] === '-' || line[0] === '*') && line[1] === ' ') return { kind: 'ul', body: line.slice(2).trim() }
  let digits = 0
  while (digits < line.length && line[digits]! >= '0' && line[digits]! <= '9') digits++
  if (digits > 0 && line[digits] === '.' && line[digits + 1] === ' ') return { kind: 'ol', body: line.slice(digits + 2).trim() }
  return { kind: 'p', body: line }
}

export function parseMarkdown(text: string): MdBlock[] {
  const blocks: MdBlock[] = []
  const state: { list: { type: 'ul' | 'ol', items: MdInline[][] } | null, para: string[] } = { list: null, para: [] }
  const flushPara = () => { if (state.para.length) blocks.push({ type: 'p', items: [parseInline(state.para.join(' '))] }); state.para = [] }
  const flushList = () => { if (state.list) blocks.push({ type: state.list.type, items: state.list.items }); state.list = null }

  for (const raw of (text || '').replace(/\r\n/g, '\n').split('\n')) {
    const line = raw.trim()
    if (!line) { flushPara(); flushList(); continue }
    const { kind, body } = classify(line)
    if (kind === 'h') { flushPara(); flushList(); blocks.push({ type: 'h', items: [parseInline(body)] }) }
    else if (kind === 'ul' || kind === 'ol') {
      flushPara()
      if (state.list?.type !== kind) { flushList(); state.list = { type: kind, items: [] } }
      state.list.items.push(parseInline(body))
    }
    else { flushList(); state.para.push(body) }
  }
  flushPara(); flushList()
  return blocks
}
