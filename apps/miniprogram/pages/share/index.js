const { readCardOptions, shareCover, sharePayload } = require('../../lib/card-entry')
const { showShare, unconfigured } = require('../../lib/web-view')

Page({
  data: { ready: false, message: '', cover: shareCover },
  onLoad(options) {
    this.entry = readCardOptions(options)
    const configured = Boolean(getApp().h5Base)
    this.setData({
      ready: Boolean(configured && this.entry),
      message: configured ? '名片入口无效，请返回后重试。' : unconfigured,
    })
  },
  onShow() {
    showShare(this.data.ready)
  },
  onShareAppMessage() {
    return sharePayload(this.data.ready ? this.entry : undefined)
  },
})
