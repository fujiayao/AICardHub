export function maskPhone(value: string) { return value.replace(/(\d{3})\d{4}(\d{4})/, '$1 **** $2') }
export function phoneLabel(value: string) { return value.replace(/(\d{3})(\d{4})(\d{4})/, '$1 $2 $3') }
export function dateLabel(value: string) { return value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '' }
export const leadStatuses = [{ value: 'new', label: '新线索' }, { value: 'contacted', label: '已联系' }, { value: 'converted', label: '已转化' }, { value: 'invalid', label: '无效' }]
export function statusLabel(value: string) { return leadStatuses.find(s => s.value === value)?.label || value }
const weekdayChars = ['日', '一', '二', '三', '四', '五', '六']
const shanghaiWeekday = new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Shanghai', weekday: 'short' })
const shanghaiIndex: Record<string, number> = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }
// 近 7 天柱状的日期标签：最后一天显示“今”，其余显示星期几，按 Asia/Shanghai 判断星期几（避免机器本地时区偏差）。
export function weekdayLabel(date: string, isLast: boolean) {
  if (isLast) return '今'
  const d = new Date(`${date}T12:00:00+08:00`)
  if (Number.isNaN(d.getTime())) return date.slice(5)
  const idx = shanghaiIndex[shanghaiWeekday.format(d)]
  return idx === undefined ? date.slice(5) : weekdayChars[idx]
}
// 今日较昨日增量：返回带符号文本与方向，0 与负数如实显示（+N / 0 / −N），不隐藏。
export function deltaValue(today: number, yesterday: number): { text: string, dir: 'up' | 'down' | 'flat' } {
  const diff = today - yesterday
  const sign = diff > 0 ? '+' : diff < 0 ? '−' : ''
  const dir = diff > 0 ? 'up' : diff < 0 ? 'down' : 'flat'
  return { text: `${sign}${Math.abs(diff)}`, dir }
}
const sourceLabels: Record<string, string> = { nfc: 'NFC 碰一碰', qr: '扫码', poster: '海报扫码', link: '微信链接', sig: '签名链接' }
export function sourceLabel(value?: string | null) { return value ? sourceLabels[value] || value : '' }
export const intentLevelLabels: Record<string, string> = { A: 'A 高意向', B: 'B 中意向', C: 'C 一般意向' }
