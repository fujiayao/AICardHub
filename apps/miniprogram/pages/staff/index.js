const { webViewPage } = require('../../lib/web-view')

Page({
  ...webViewPage(),
  onLoad() {
    const base = getApp().h5Base
    this.openWebView(base ? `${base}/staff/login` : '')
  },
})
