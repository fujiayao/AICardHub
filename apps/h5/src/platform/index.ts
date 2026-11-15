import { showToast } from 'vant'
import { vcardPath } from '@/utils/app-path'
export const isWechat = /MicroMessenger/i.test(navigator.userAgent)
export const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
/** Guidance only: chooses which instructions to show. Never treated as NFC/HCE hardware support. */
export const isAndroid = !isIOS && /Android/i.test(navigator.userAgent)
/** User-initiated navigation to an Android App Link. Browsers cannot tell whether the helper is installed. */
export function openAppLink(url: string) { window.location.assign(url) }
export function callPhone(phone: string) { window.location.href = `tel:${phone.replace(/[^+\d]/g, '')}` }
export async function copyText(text: string) {
 try { await navigator.clipboard.writeText(text); showToast('已复制') }
 catch { showToast('无法自动复制，请长按文字复制') }
}
export function openMap(address: string) { window.open(`https://uri.amap.com/search?keyword=${encodeURIComponent(address)}`, '_blank', 'noopener,noreferrer') }
export async function share(title: string, url: string) {
 if (navigator.share) { try { await navigator.share({ title, url }); return } catch (e) { if (e instanceof DOMException && e.name === 'AbortError') return } }
 await copyText(`${title} ${url}`)
}
export function saveContact(code: string) { window.location.assign(vcardPath(code)) }
export function safeReturn(value: unknown) { return typeof value === 'string' && value.startsWith('/staff/') && !value.startsWith('//') && !value.includes('login') ? value : '/staff/card' }
