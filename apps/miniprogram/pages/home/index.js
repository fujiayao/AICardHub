const { showShare, unconfigured } = require('../../lib/web-view')

Page({
  data: { configured: false, message: unconfigured },
  onLoad() {
    this.setData({ configured: Boolean(getApp().h5Base) })
  },
  onShow() {
    showShare(false)
  },
})
