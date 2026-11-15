import { showToast } from 'vant'
import { vcardPath } from '@/utils/app-path'
import { nfcIntentUrl } from '@/utils/nfc-link'
export const isWechat = /MicroMessenger/i.test(navigator.userAgent)
export const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
/** Guidance only: chooses which instructions to show. Never treated as NFC/HCE hardware support. */
export const isAndroid = !isIOS && /Android/i.test(navigator.userAgent)
/** Called only by a user's click; explicit package launch avoids same-domain browser navigation. */
export function openAppLink(url: string) {
 if (isWechat) { showToast('请从右上角菜单选择在浏览器打开'); return }
 const target = isAndroid ? nfcIntentUrl(url) : undefined
 if (isAndroid && !target) { showToast('NFC 配置链接无效，请重新获取'); return }
 window.location.assign(target || url)
}
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
