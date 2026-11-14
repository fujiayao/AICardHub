import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
describe('real generated contract', () => {
 it('records a real backend schema and the critical operation IDs', () => {
  const provenance = JSON.parse(readFileSync('src/api/generated/provenance.json', 'utf8')) as { title: string, sha256: string, operations: number }
  expect(provenance.title).not.toContain('TEMPORARY'); expect(provenance.sha256).toMatch(/^[a-f0-9]{64}$/); expect(provenance.operations).toBeGreaterThan(35)
  const source = readFileSync('src/api/generated/index.ts', 'utf8')
  expect(source).toContain('card_get_public'); expect(source).toContain('me_lead_update'); expect(source).toContain('encodeURIComponent')
 })
 it('fails closed for missing schema input', () => {
  expect(() => execFileSync(process.execPath, ['scripts/generate-api.mjs', 'missing-openapi.json'], { stdio: 'pipe' })).toThrow()
 })
})
