const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../src/lib/event-source.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const loaded = { exports: {} };
new Function('exports', compiled)(loaded.exports);
const label = loaded.exports.eventSourceLabel;
assert.equal(label({ source: 'ring', integrity: { signature_verified: true } }),
  'Source unconfirmed (legacy event)');
assert.equal(label({ source: 'ring', integrity: { authenticated_source: true } }),
  'Ring history (may include Playground)');
assert.equal(label({ source: 'ring', integrity: { ingestion_method: 'ring_history' } }),
  'Ring history (may include Playground)');
assert.equal(label({ source: 'ring', integrity: { ingestion_method: 'webhook', simulation_declared: true } }),
  'Simulation (sender-declared)');
assert.equal(label({ source: 'ring', integrity: { ingestion_method: 'webhook', authenticated_source: true } }),
  'Webhook (origin unconfirmed)');
assert.equal(label({}), 'Source unconfirmed (legacy event)');
console.log('6 source-label checks passed.');
