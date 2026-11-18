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
export async function share(title: string, url: string, text = '') {
 if (navigator.share) { try { await navigator.share({ title, text, url }); return } catch (e) { if (e instanceof DOMException && e.name === 'AbortError') return } }
 await copyText(`${title}${text ? `\n${text}` : ''}\n${url}`)
}
/** Prepare before the share click so the native share keeps its user gesture. */
export async function prepareShareImage(url: string): Promise<File | undefined> {
 if (!navigator.canShare) return undefined
 const response = await fetch(url, { credentials: 'omit' })
 if (!response.ok) throw new Error('名片图片暂时无法生成，请重试')
 const blob = await response.blob()
 if (!blob.type.startsWith('image/')) throw new Error('名片图片格式无效，请重试')
 const file = new File([blob], '商务名片.jpg', { type: blob.type })
 return navigator.canShare({ files: [file] }) ? file : undefined
}
export async function shareImage(file: File) {
 try { await navigator.share({ files: [file] }) }
 catch (error) { if (!(error instanceof DOMException && error.name === 'AbortError')) showToast('图片分享未完成，请长按图片保存后发送') }
}
export function saveContact(code: string) { window.location.assign(vcardPath(code)) }
export function safeReturn(value: unknown) { return typeof value === 'string' && value.startsWith('/staff/') && !value.startsWith('//') && !value.includes('login') ? value : '/staff/card' }
