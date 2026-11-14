import type { VisitInput } from '@/api/generated'
export type Source = VisitInput['source']
const sources: Source[] = ['nfc', 'qr', 'poster', 'link', 'sig']
export function sceneSource(value: unknown): Source { return sources.includes(value as Source) ? value as Source : 'link' }
export function sceneCampaign(value: unknown): number | undefined { const id = Number(value); return Number.isSafeInteger(id) && id > 0 ? id : undefined }
export function sceneQuery(source: Source, campaign?: number) { return { s: source, ...(campaign ? { e: String(campaign) } : {}) } }
export function sceneKey(code: string, campaign?: number, source: Source = 'link') { return `shuke.scene.${  code  }.${  campaign || 'business'  }.${  source}` }
