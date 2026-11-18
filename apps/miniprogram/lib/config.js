const hostLabel = '[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?'
const httpsBase = new RegExp(`^https://(${hostLabel}(?:\\.${hostLabel})*)(/[a-z0-9._~/-]*)?$`, 'i')

function normalizeH5Base(value) {
  if (typeof value !== 'string') return ''
  const parts = httpsBase.exec(value.trim())
  if (!parts || !parts[1].includes('.') || !/[a-z]/i.test(parts[1].split('.').at(-1))) return ''
  const path = parts[2] || ''
  if (path.includes('//') || path.split('/').some(segment => segment === '.' || segment === '..')) return ''
  return `https://${parts[1].toLowerCase()}${path.replace(/\/$/, '')}`
}

function readH5Base(platform) {
  try {
    const files = platform.getFileSystemManager()
    const config = JSON.parse(files.readFileSync('config.local.json', 'utf8'))
    return normalizeH5Base(config && config.h5BaseUrl)
  } catch {
    return ''
  }
}

module.exports = { normalizeH5Base, readH5Base }
