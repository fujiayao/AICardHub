import { showToast } from 'vant'
import { onMounted, onUnmounted, shallowRef } from 'vue'

interface MiniProgramBridge {
  navigateTo: (options: { url: string, fail: () => void }) => void
}

interface WechatWindow extends Window {
  __wxjs_environment?: string
  wx?: { miniProgram?: MiniProgramBridge }
}

const sdkUrl = 'https://res.wx.qq.com/open/js/jweixin-1.3.2.js'
let sdkPending: Promise<MiniProgramBridge> | undefined

/** The ordinary WeChat browser is not a mini-program web-view. */
export function isMiniProgram() {
  return typeof window !== 'undefined' && ((window as WechatWindow).__wxjs_environment === 'miniprogram'
    || /\bminiprogram\b/i.test(window.navigator.userAgent))
}

export function useMiniProgram() {
  const active = shallowRef(isMiniProgram())
  function refresh() { active.value = isMiniProgram() }
  onMounted(() => {
    document.addEventListener('WeixinJSBridgeReady', refresh)
    refresh()
  })
  onUnmounted(() => document.removeEventListener('WeixinJSBridgeReady', refresh))
  return active
}

/** This is a public routing contract; never forward the current URL or a token. */
export function miniCardSharePath(code: string, campaign?: number): string | undefined {
  if (!/^[\w:-]{1,32}$/.test(code)) return undefined
  if (campaign !== undefined && (!Number.isSafeInteger(campaign) || campaign < 1)) return undefined
  return `/pages/share/index?code=${encodeURIComponent(code)}&s=link${campaign === undefined ? '' : `&e=${campaign}`}`
}

function currentBridge() {
  const bridge = (window as WechatWindow).wx?.miniProgram
  return typeof bridge?.navigateTo === 'function' ? bridge : undefined
}

function loadBridge() {
  const existing = currentBridge()
  if (existing) return Promise.resolve(existing)
  sdkPending ??= new Promise<MiniProgramBridge>((resolve, reject) => {
    const script = document.createElement('script')
    const timeout = window.setTimeout(fail, 5000)
    function fail() {
      window.clearTimeout(timeout)
      script.remove()
      reject(new Error('Mini program bridge unavailable'))
    }
    script.src = sdkUrl
    script.onload = () => {
      const bridge = currentBridge()
      if (!bridge) return fail()
      window.clearTimeout(timeout)
      resolve(bridge)
    }
    script.onerror = fail
    document.head.append(script)
  }).finally(() => { sdkPending = undefined })
  return sdkPending
}

/** True means the mini-program owns this click, even if the bridge fails. */
export function openMiniCardShare(code: string, campaign?: number, fromStaff = false): boolean {
  if (!isMiniProgram()) return false
  const url = miniCardSharePath(code, campaign)
  if (!url) { showToast('名片或活动信息无效，请刷新后重试'); return true }
  function showFallback() {
    showToast(fromStaff ? '暂时无法转发，可改用「链接」或「二维码」' : '暂时无法打开转发页，请用右上角「···」转发名片')
  }
  void loadBridge().then(bridge => bridge.navigateTo({ url, fail: showFallback })).catch(showFallback)
  return true
}
