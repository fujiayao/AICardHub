import { Button } from 'vant'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import NfcInstallHelp from '../src/components/common/NfcInstallHelp.vue'

afterEach(() => vi.unstubAllEnvs())

describe('nfc helper installation', () => {
  it('renders a real downloadable anchor using the configured HTTPS APK URL', async () => {
    vi.stubEnv('VITE_NFC_APK_URL', 'https://haiwex.com/aicardhub/downloads/aicardhub-nfc.apk')
    const app = createSSRApp(NfcInstallHelp)
    app.component('van-button', Button)
    const output = await renderToString(app)
    expect(output).toMatch(/<a [^>]*href="https:\/\/haiwex\.com\/aicardhub\/downloads\/aicardhub-nfc\.apk"/)
    expect(output).toContain('下载安卓助手')
    expect(output).not.toContain('<button')
  })
})
