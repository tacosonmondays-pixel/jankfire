// node tests/story/refbrowser.test.mjs : the story's solo referee runs the real game room (server/room.js) in a browser
// web worker (shared/story/refsys.js). a browser can't load node's own modules, so if anything room.js pulls in at
// load time imports 'node:crypto' (or fs, or any bare package name), the whole room fails to load and every story
// fight stays dead: the train never went live after server/party.js arrived with `import crypto from 'node:crypto'`.
// this follows room.js's static imports (server/ and shared/) and fails on any import a browser can't resolve.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

// every file room.js reaches through static imports, and the specifiers each one uses that aren't a relative path
function closure(entry) {
  const seen = new Set(), bad = [];
  const walk = (file) => {
    if (seen.has(file)) return; seen.add(file);
    const src = fs.readFileSync(file, 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
    for (const m of src.matchAll(/^\s*(?:import|export)\s+(?:[^'"]*?from\s+)?['"]([^'"]+)['"]/gm)) {
      const spec = m[1];
      if (spec.startsWith('./') || spec.startsWith('../')) walk(path.resolve(path.dirname(file), spec));
      else if (spec.startsWith('/')) walk(path.join(ROOT, spec)); // (served from the site root: /shared/...)
      else bad.push(`${path.relative(ROOT, file)}: '${spec}'`);
    }
    const code = src.replace(/(['"`])(?:\\.|(?!\1).)*\1/g, '""').replace(/\/\/.*$/gm, ''); // (strings out first, then what's left of the comments)
    for (const g of ['Buffer', 'require', '__dirname', '__filename']) if (new RegExp(`\\b${g}\\b`).test(code)) bad.push(`${path.relative(ROOT, file)}: uses ${g}`); // (node-only globals: a browser has none of them)
  };
  walk(entry);
  return { files: [...seen].map((f) => path.relative(ROOT, f)), bad };
}

await t('nothing room.js loads imports a node module or a bare package (the referee runs it in a browser worker)', () => {
  const { files, bad } = closure(path.join(ROOT, 'server', 'room.js'));
  assert.ok(files.includes(path.join('server', 'storyref.js')) && files.length > 20, 'the whole closure was followed');
  assert.deepEqual(bad, [], 'these imports would stop the story referee from loading in the browser:\n  ' + bad.join('\n  '));
});

await t('server/party.js still loads in node and makes its random bytes without node:crypto', async () => {
  const P = await import('../../server/party.js');
  assert.equal(typeof P.installParty, 'function');
  const src = fs.readFileSync(path.join(ROOT, 'server', 'party.js'), 'utf8');
  assert.ok(!/from\s+['"]node:/.test(src) && /globalThis\.crypto\.getRandomValues/.test(src));
  assert.equal(globalThis.crypto.getRandomValues(new Uint8Array(9)).length, 9);
});

await t('its ticket encoding matches node\'s base64url byte for byte', async () => {
  const src = fs.readFileSync(path.join(ROOT, 'server', 'party.js'), 'utf8');
  const B64 = (src.match(/const B64 = '([^']+)'/) || [])[1], b64url = new Function('B64', 'return ' + src.match(/const b64url = (\(\w+\) => \{[^\n]+?\}); \/\//)[1])(B64);
  for (let n = 0; n < 40; n++) { const b = globalThis.crypto.getRandomValues(new Uint8Array(n)); assert.equal(b64url(b), Buffer.from(b).toString('base64url'), `${n} bytes`); }
});

console.log(`${n} ok`);
