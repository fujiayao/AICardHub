export function maskPhone(value: string) { return value.replace(/(\d{3})\d{4}(\d{4})/, '$1 **** $2') }
export function phoneLabel(value: string) { return value.replace(/(\d{3})(\d{4})(\d{4})/, '$1 $2 $3') }
export function dateLabel(value: string) { return value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '' }
export const leadStatuses = [{ value: 'new', label: '新线索' }, { value: 'contacted', label: '已联系' }, { value: 'converted', label: '已转化' }, { value: 'invalid', label: '无效' }]
export function statusLabel(value: string) { return leadStatuses.find(s => s.value === value)?.label || value }
const weekdayChars = ['日', '一', '二', '三', '四', '五', '六']
// 近 7 天柱状的日期标签：最后一天显示“今”，其余显示星期几（Asia/Shanghai 口径由后端 date 决定）。
export function weekdayLabel(date: string, isLast: boolean) { if (isLast) return '今'; const d = new Date(`${date}T00:00:00+08:00`); return Number.isNaN(d.getTime()) ? date.slice(5) : weekdayChars[d.getDay()] }
// 今日较昨日增量：返回带符号文本，<=0 不显示（原型仅展示正向增量 +N）。
export function deltaText(today: number, yesterday: number) { const diff = today - yesterday; return diff > 0 ? `+${diff}` : '' }
const sourceLabels: Record<string, string> = { nfc: 'NFC 碰一碰', qr: '扫码', poster: '海报扫码', link: '微信链接', sig: '签名链接' }
export function sourceLabel(value?: string | null) { return value ? sourceLabels[value] || value : '' }
export const intentLevelLabels: Record<string, string> = { A: 'A 高意向', B: 'B 中意向', C: 'C 一般意向' }
