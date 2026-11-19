import type { LocationQueryRaw, RouteLocationNormalized, RouteLocationRaw } from 'vue-router'
import { sceneCampaign, sceneSource } from '@/utils/scene'

export function cardOnlyRedirect(to: RouteLocationNormalized): RouteLocationRaw | undefined {
  if (/^\/staff\/assistant(?:\/|$)/i.test(to.path)) return { name: '/staff/card/' }

  if (to.name === '/chat/[code]' && typeof to.params.code === 'string') {
    const query: LocationQueryRaw = {}
    const source = sceneSource(to.query.s)
    if (to.query.s === source) query.s = source
    const event = to.query.e
    const campaign = typeof event === 'string' && !/\D/.test(event) ? sceneCampaign(event) : undefined
    if (campaign) query.e = String(campaign)
    if (to.query.lead === '1') query.lead = '1'
    return { name: '/card/[code]', params: { code: to.params.code }, query }
  }

  if (to.name === '/card/[code]' && 'q' in to.query) {
    const query = { ...to.query }
    delete query.q
    return { path: to.path, query, hash: to.hash }
  }
}
