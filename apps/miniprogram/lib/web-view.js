const unconfigured = '服务尚未配置，请联系管理员后再试。'

function showShare(enabled) {
  if (enabled) wx.showShareMenu({ menus: ['shareAppMessage'] })
  else wx.hideShareMenu()
}

function webViewPage(shareable = false) {
  return {
    data: { src: '', message: '', canRetry: false },
    onShow() {
      showShare(shareable && Boolean(this.data.src))
    },
    openWebView(src, message = unconfigured) {
      this.initialUrl = src
      this.setData({ src, message: src ? '' : message, canRetry: false })
    },
    onWebViewError() {
      if (!this.data.src) return
      this.setData({ src: '', message: '页面暂时打不开，请检查网络后重试。', canRetry: true })
      this.onShow()
    },
    retry() {
      if (!this.initialUrl || !this.data.canRetry) return
      this.openWebView(this.initialUrl)
      this.onShow()
    },
  }
}

module.exports = { showShare, unconfigured, webViewPage }
