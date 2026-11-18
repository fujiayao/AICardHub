const { cardWebUrl, readCardEntry, sharePayload } = require('../../lib/card-entry')
const { webViewPage } = require('../../lib/web-view')

Page({
  ...webViewPage(true),
  onLoad(options) {
    this.base = getApp().h5Base
    this.entry = readCardEntry(options)
    this.openWebView(cardWebUrl(this.base, this.entry), this.entry ? undefined : '名片入口无效，请重新扫描或打开朋友转发的名片。')
  },
  onShareAppMessage(options = {}) {
    return sharePayload(this.data.src ? this.entry : undefined, this.base, options.webViewUrl)
  },
})
