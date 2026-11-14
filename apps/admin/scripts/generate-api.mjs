import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { createHash } from "node:crypto";
import { format } from "prettier";
import openapiTS, { astToString } from "openapi-typescript";
import { operations } from "./operations.mjs";
const root = fileURLToPath(new URL("..", import.meta.url));
const source =
  process.argv[2] ??
  process.env.OPENAPI_SOURCE ??
  path.resolve(root, "../../contracts/openapi.json");
const bytes = /^https?:/.test(source)
  ? Buffer.from(await (await fetch(source)).arrayBuffer())
  : await readFile(path.resolve(source));
const schema = JSON.parse(bytes.toString("utf8"));
if (!schema.openapi || !schema.paths || !schema.components)
  throw new Error("需要后端真实导出的 OpenAPI，不接受空的或手写占位 schema");
const hash = createHash("sha256").update(bytes).digest("hex");
const header = `// Generated from backend OpenAPI. DO NOT EDIT. Source SHA256: ${hash}\n`;
const output = path.join(root, "src/api/generated");
const names = new Set();
const bindings = [];
// Match normalized path shape so parameter names are taken from the real backend, never guessed.
for (const [alias, [method, expected]] of Object.entries(operations)) {
  const shape = (p) => p.replace(/\{[^}]+\}/g, "{}");
  const actual = Object.keys(schema.paths).find(
    (p) => shape(p) === shape(expected) && schema.paths[p][method],
  );
  if (!actual)
    throw new Error(`真实 OpenAPI 缺少 ${method.toUpperCase()} ${expected}`);
  const op = schema.paths[actual][method];
  const name = op.operationId;
  if (!name || !/^[A-Za-z_$][\w$]*$/.test(name) || names.has(name))
    throw new Error(`需要稳定且唯一的 operation_id: ${method} ${actual}`);
  names.add(name);
  bindings.push({ alias, method, actual, name });
}
const helper = `import type { paths } from './schema';\nimport {request} from '../client';\ntype Json<T> = T extends {content:{'application/json':infer J}}?J:never;\ntype Param<T,K extends PropertyKey> = T extends {parameters:infer P}? K extends keyof P?NonNullable<P[K]>:Record<string,never>:Record<string,never>;\ntype Body<T> = T extends {requestBody:infer B}?Json<B>:never;\ntype Result<T> = T extends {responses:infer R}?{[K in keyof R]:K extends 200|201|202?Json<R[K]>:K extends 204?void:never}[keyof R]:never;\n`;
let funcs = header + helper;
for (const { alias, method, actual, name } of bindings) {
  const type = `paths[${JSON.stringify(actual)}][${JSON.stringify(method)}]`;
  const hasPath = actual.includes("{");
  const body = !!schema.paths[actual][method].requestBody;
  const hasQuery = (schema.paths[actual][method].parameters ?? []).some(
    (p) => p.in === "query",
  );
  const args = [
    ...(hasPath ? [`path:Param<${type},'path'>`] : []),
    ...(hasQuery ? [`query?:Param<${type},'query'>`] : []),
    ...(body ? [`body:Body<${type}>`] : []),
    "signal?:AbortSignal",
  ];
  const optional = !hasPath && !body;
  funcs += `\n/** ${alias}: ${method.toUpperCase()} ${actual} */\nexport function ${name}(options:{${args.join(";")}}${optional ? " = {}" : ""}):Promise<Result<${type}>> { return request(${JSON.stringify(method.toUpperCase())},${JSON.stringify(actual)},{${[...(hasPath ? ["path:options.path"] : []), ...(hasQuery ? ["query:options.query"] : []), ...(body ? ["body:options.body"] : []), "signal:options.signal"].join(",")}}); }\n`;
}
funcs += `\nexport const operations={${bindings.map((b) => `${b.alias}:${b.name}`).join(",")}};\n`;
await mkdir(output, { recursive: true });
await writeFile(
  path.join(output, "schema.ts"),
  await format(header + astToString(await openapiTS(schema)), {
    parser: "typescript",
  }),
);
await writeFile(
  path.join(output, "operations.ts"),
  await format(funcs, { parser: "typescript" }),
);
await writeFile(
  path.join(output, "source.json"),
  JSON.stringify(
    { sha256: hash, openapi: schema.openapi, operation_count: bindings.length },
    null,
    2,
  ) + "\n",
);
console.info(
  `Generated ${bindings.length} typed API functions from real OpenAPI; SHA256 ${hash}`,
);
