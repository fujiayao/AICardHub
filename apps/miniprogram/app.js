const { readH5Base } = require('./lib/config')

App({
  h5Base: '',
  onLaunch() {
    this.h5Base = readH5Base(wx)
  },
})
