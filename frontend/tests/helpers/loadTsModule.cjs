const fs = require("node:fs");
const path = require("node:path");
const ts = require("../../node_modules/typescript/lib/typescript");

const cache = new Map();

function loadTsModule(relativePath) {
  const normalized = path.normalize(relativePath).replace(/\\/g, "/");
  if (cache.has(normalized)) return cache.get(normalized).exports;

  const modulePath = path.join(__dirname, "..", "..", normalized);
  const source = fs.readFileSync(modulePath, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2019,
      esModuleInterop: true,
    },
  }).outputText;
  const mod = { exports: {} };
  cache.set(normalized, mod);
  const localRequire = (request) => {
    if (!request.startsWith(".")) return require(request);
    const candidate = path.join(path.dirname(normalized), request);
    const withExtension = path.extname(candidate) ? candidate : `${candidate}.ts`;
    return loadTsModule(withExtension);
  };
  new Function("require", "module", "exports", compiled)(localRequire, mod, mod.exports);
  return mod.exports;
}

module.exports = { loadTsModule };
