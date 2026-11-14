export function maskPhone(value: string) { return value.replace(/(\d{3})\d{4}(\d{4})/, '$1 **** $2') }
export function phoneLabel(value: string) { return value.replace(/(\d{3})(\d{4})(\d{4})/, '$1 $2 $3') }
export function dateLabel(value: string) { return value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '' }
export const leadStatuses = [{ value: 'new', label: '新线索' }, { value: 'contacted', label: '已联系' }, { value: 'converted', label: '已转化' }, { value: 'invalid', label: '无效' }]
export function statusLabel(value: string) { return leadStatuses.find(s => s.value === value)?.label || value }
