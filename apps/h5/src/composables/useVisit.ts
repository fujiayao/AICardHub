import type { Source } from '@/utils/scene'
import { createVisit } from '@/api/generated'
import { sceneKey } from '@/utils/scene'

// 按场景键（code.campaign.source）管理访问记录，首页与对话页共享。
// 首页：forceNew，每次进入/刷新/返回首页都新建一次访问，并作为该场景的进行中请求。
// 对话页：优先复用进行中请求（首页刚发出未返回），其次复用缓存；都没有时（直连对话）创建一次。
const inflight = new Map<string, Promise<number>>()

export function cachedVisit(code: string, campaign: number | undefined, source: Source): number | undefined {
  const value = Number(sessionStorage.getItem(sceneKey(code, campaign, source)))
  return Number.isSafeInteger(value) && value > 0 ? value : undefined
}

export function ensureVisit(
  ensure: () => Promise<unknown>,
  code: string,
  campaign: number | undefined,
  source: Source,
  options: { forceNew?: boolean } = {},
): Promise<number> {
  const key = sceneKey(code, campaign, source)
  if (!options.forceNew) {
    const pending = inflight.get(key)
    if (pending) return pending
    const cached = cachedVisit(code, campaign, source)
    if (cached) return Promise.resolve(cached)
  } else {
    sessionStorage.removeItem(key)
  }
  let task!: Promise<number>
  // eslint-disable-next-line prefer-const -- Assigned separately for the async closure's identity guard.
  task = (async () => {
    await ensure()
    const result = await createVisit({ body: { card_code: code, source, campaign_id: campaign } })
    // 仅当仍是该场景最新请求时写缓存，避免被替换的旧 forceNew 覆盖新访问。
    if (inflight.get(key) === task) sessionStorage.setItem(key, String(result.visit_id))
    return result.visit_id
  })().finally(() => { if (inflight.get(key) === task) inflight.delete(key) })
  inflight.set(key, task)
  return task
}
