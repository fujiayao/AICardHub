import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { endpoints } from './endpoints.mjs'
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const input = process.argv[2] || path.resolve(root, '../..', 'contracts/openapi.json')
const text = /^https?:/.test(input) ? await (await fetch(input)).text() : await readFile(input, 'utf8')
const doc = JSON.parse(text)
if (!doc.openapi || !doc.paths || !doc.components?.schemas) throw new Error('An OpenAPI 3 schema with paths/components is required')
const hash = createHash('sha256').update(text).digest('hex')
const schemas = doc.components.schemas
function name(ref) { return ref.split('/').at(-1).replace(/\W/g, '_') }
export function schemaType(s, prefix = '') {
 if (!s || s === true) return 'unknown'
 if (s === false) return 'never'
 if (s.$ref) return prefix + name(s.$ref)
 if ('const' in s) return JSON.stringify(s.const)
 if (s.enum) return s.enum.map(v => JSON.stringify(v)).join(' | ') || 'never'
 if (s.anyOf || s.oneOf) return `(${(s.anyOf || s.oneOf).map(v => schemaType(v, prefix)).join(' | ')})`
 if (s.allOf) return `(${s.allOf.map(v => schemaType(v, prefix)).join(' & ')})`
 if (Array.isArray(s.type)) return s.type.map(t => schemaType({ ...s, type: t }, prefix)).join(' | ')
 let value = 'unknown'
 if (s.type === 'null') value = 'null'
 else if (s.type === 'string') value = 'string'
 else if (s.type === 'integer' || s.type === 'number') value = 'number'
 else if (s.type === 'boolean') value = 'boolean'
 else if (s.type === 'array') value = `Array<${schemaType(s.items, prefix)}>`
 else if (s.type === 'object' || s.properties) {
  const fields = Object.entries(s.properties || {}).map(([key, v]) => `${JSON.stringify(key)}${s.required?.includes(key) ? '' : '?'}: ${schemaType(v, prefix)}`)
  if (s.additionalProperties) fields.push(`[key: string]: ${s.additionalProperties === true ? 'unknown' : schemaType(s.additionalProperties, prefix)}`)
  value = fields.length ? `{ ${fields.join('; ')} }` : 'Record<string, unknown>'
 }
 return s.nullable ? `(${value} | null)` : value
}
function resolve(s) { return s?.$ref ? schemas[name(s.$ref)] : s }
function content(c) { return c?.['application/json']?.schema || c?.['multipart/form-data']?.schema }
const generated = []
for (const [alias, [method, url, identity]] of Object.entries(endpoints)) {
 const item = doc.paths[url]
 const op = item?.[method]
 if (!op) throw new Error(`Missing operation: ${method.toUpperCase()} ${url}`)
 if (!op.operationId) throw new Error(`operationId required: ${url}`)
 const params = [...(item.parameters || []), ...(op.parameters || [])]
 const parts = []
 for (const location of ['path', 'query']) {
  const selected = params.filter(p => p.in === location)
  if (selected.length) parts.push(`${location}${selected.some(p => p.required) ? '' : '?'}: { ${selected.map(p => `${JSON.stringify(p.name)}${p.required ? '' : '?'}: ${schemaType(p.schema, 'Schemas.')}`).join('; ')} }`)
 }
 const multipart = Boolean(op.requestBody?.content?.['multipart/form-data'])
 if (op.requestBody) parts.push(`body${op.requestBody.required ? '' : '?'}: ${multipart ? 'FormData' : schemaType(content(op.requestBody.content), 'Schemas.')}`)
 const required = params.some(p => p.required) || op.requestBody?.required
 const response = Object.entries(op.responses || {}).find(([code]) => code.startsWith('2'))?.[1]
 const returnType = content(response?.content) ? schemaType(content(response.content), 'Schemas.') : 'void'
 const pathExpression = url.replace(/\{([^}]+)\}/g, (_, key) => `\${encodeURIComponent(String(input.path[${  JSON.stringify(key)  }]))}`)
 const generatedPath = String.fromCharCode(96) + pathExpression + String.fromCharCode(96)
 generated.push(`/** ${op.operationId} */\nexport function ${alias}(${parts.length ? 'input' : '_input'}: { ${parts.join('; ')} }${required ? '' : ' = {}'}): Promise<${returnType}> { return request<${returnType}>('${method}', ${generatedPath}, ${op.requestBody ? 'input.body' : 'undefined'}, '${identity}', ${params.some(p => p.in === 'query') ? 'input.query' : 'undefined'}) }`)
 if (multipart && !resolve(content(op.requestBody.content))?.properties?.file) throw new Error(`Expected multipart file: ${url}`)
}
const out = path.join(root, 'src/api/generated')
await mkdir(out, { recursive: true })
const header = `// Generated from OpenAPI; DO NOT EDIT. SHA256 ${hash}\n`
await writeFile(path.join(out, 'schemas.ts'), `${header + Object.entries(schemas).map(([key, s]) => `export type ${name(key)} = ${schemaType(s)}`).join('\n')  }\n`)
await writeFile(path.join(out, 'index.ts'), `${header  }import { request } from '../client'\nimport type * as Schemas from './schemas'\nexport type * from './schemas'\n${  generated.join('\n')  }\n`)
await writeFile(path.join(out, 'provenance.json'), `${JSON.stringify({ source: path.basename(input), sha256: hash, title: doc.info?.title, version: doc.info?.version, operations: generated.length }, null, 2)  }\n`)
process.stdout.write(`Generated ${generated.length} operations from ${input} (${hash})\n`)
