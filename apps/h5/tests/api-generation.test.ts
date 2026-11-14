import { execFileSync } from 'node:child_process'
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
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
 it('resolves the default contract from the package root regardless of current directory', () => {
  const temporary = mkdtempSync(path.join(tmpdir(), 'h5-default-contract-'))
  try {
   const packageRoot = path.join(temporary, 'repo/apps/h5')
   const scripts = path.join(packageRoot, 'scripts')
   const contracts = path.join(temporary, 'repo/contracts')
   mkdirSync(scripts, { recursive: true }); mkdirSync(contracts, { recursive: true })
   for (const name of ['generate-api.mjs', 'endpoints.mjs']) copyFileSync(`scripts/${name}`, path.join(scripts, name))
   const registry = readFileSync('scripts/endpoints.mjs', 'utf8')
   const paths: Record<string, Record<string, unknown>> = {}
   for (const match of registry.matchAll(/(\w+): \['(\w+)', '([^']+)', '\w+'\]/g)) {
    const alias = match[1]!; const method = match[2]!; const url = match[3]!
    const multipart = ['uploadPhoto', 'uploadWechatQR', 'importNotes'].includes(alias)
    paths[url] ||= {}
    paths[url][method] = { operationId: alias, responses: { 200: { description: 'test' } },
     ...(multipart ? { requestBody: { required: true, content: { 'multipart/form-data': { schema: { type: 'object', properties: { file: { type: 'string', format: 'binary' } } } } } } } : {}) }
   }
   writeFileSync(path.join(contracts, 'openapi.json'), JSON.stringify({ openapi: '3.1.0', info: { title: 'default-path-fixture' }, paths, components: { schemas: {} } }))
   execFileSync(process.execPath, [path.join(scripts, 'generate-api.mjs')], { cwd: temporary, stdio: 'pipe' })
   const result = JSON.parse(readFileSync(path.join(packageRoot, 'src/api/generated/provenance.json'), 'utf8')) as { title: string, operations: number }
   expect(result.title).toBe('default-path-fixture')
   expect(result.operations).toBeGreaterThan(40)
  } finally { rmSync(temporary, { recursive: true, force: true }) }
 })
})
