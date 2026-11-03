// Generates 3D models with the Tripo API and drops them in public/models/<id>.glb.
// The game picks them up automatically on next page load (primitives are the fallback).
//
//   TRIPO_API_KEY=tsk_xxx npm run models              # generate everything missing
//   TRIPO_API_KEY=tsk_xxx npm run models -- w_cig      # just one (or several) ids
//   TRIPO_API_KEY=tsk_xxx npm run models -- --force    # regenerate even if the file exists
//
// Optional env: TRIPO_API_BASE (default https://api.tripo3d.ai/v2/openapi), TRIPO_FACE_LIMIT (default 2000)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const KEY = process.env.TRIPO_API_KEY;
const BASE = (process.env.TRIPO_API_BASE || 'https://api.tripo3d.ai/v2/openapi').replace(/\/$/, '');
const FACE_LIMIT = Number(process.env.TRIPO_FACE_LIMIT) || 2000; // low poly on purpose. this is JANKFIRE.
const OUT = path.join(ROOT, 'public/models');

if (!KEY) {
  console.error('Set TRIPO_API_KEY first. e.g.  TRIPO_API_KEY=tsk_... npm run models');
  process.exit(1);
}

const args = process.argv.slice(2);
const force = args.includes('--force');
const only = args.filter((a) => !a.startsWith('--'));
const all = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/models.json'), 'utf8'));
const todo = all.filter((m) => (!only.length || only.includes(m.id)) && (force || !fs.existsSync(path.join(OUT, m.id + '.glb'))));
fs.mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function api(method, url, body) {
  const res = await fetch(BASE + url, {
    method,
    headers: { Authorization: `Bearer ${KEY}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json;
  try { json = JSON.parse(text); } catch { throw new Error(`HTTP ${res.status}: ${text.slice(0, 300)}`); }
  if (!res.ok || (json.code !== undefined && json.code !== 0)) {
    throw new Error(`HTTP ${res.status} code ${json.code}: ${json.message || text.slice(0, 300)}`);
  }
  return json.data ?? json;
}

// Tripo has renamed output fields across versions, so hunt for any .glb URL in the result.
function findGlb(o) {
  if (!o) return null;
  for (const k of ['pbr_model', 'model', 'base_model']) {
    const v = o.output?.[k] ?? o.result?.[k];
    const u = typeof v === 'string' ? v : v?.url;
    if (u) return u;
  }
  const stack = [o];
  while (stack.length) {
    const x = stack.pop();
    if (typeof x === 'string' && /^https?:\/\//.test(x) && /\.glb(\?|$)/i.test(x)) return x;
    if (x && typeof x === 'object') stack.push(...Object.values(x));
  }
  return null;
}

async function generate(m) {
  const tag = `[${m.id}]`;
  console.log(`${tag} asking tripo for: "${m.prompt}"`);
  const task = await api('POST', '/task', { type: 'text_to_model', prompt: m.prompt, face_limit: FACE_LIMIT });
  const id = task.task_id;
  if (!id) throw new Error('no task_id in response: ' + JSON.stringify(task));
  const started = Date.now();
  for (;;) {
    await sleep(4000);
    const st = await api('GET', `/task/${id}`);
    const status = String(st.status || '').toLowerCase();
    process.stdout.write(`${tag} ${status} ${st.progress ?? ''}%   \r`);
    if (status === 'success') {
      const url = findGlb(st);
      if (!url) throw new Error('task succeeded but no .glb url found: ' + JSON.stringify(st).slice(0, 400));
      const res = await fetch(url);
      if (!res.ok) throw new Error(`download failed HTTP ${res.status}`);
      const buf = Buffer.from(await res.arrayBuffer());
      fs.writeFileSync(path.join(OUT, m.id + '.glb'), buf);
      console.log(`\n${tag} saved public/models/${m.id}.glb (${(buf.length / 1024).toFixed(0)} KB)`);
      return;
    }
    if (['failed', 'cancelled', 'banned', 'expired', 'unknown'].includes(status)) throw new Error(`task ${status}`);
    if (Date.now() - started > 10 * 60 * 1000) throw new Error('timed out after 10 min');
  }
}

if (!todo.length) {
  console.log('Nothing to do: every model already exists. Use --force to regenerate.');
  process.exit(0);
}
console.log(`Generating ${todo.length} model(s): ${todo.map((m) => m.id).join(', ')}`);
let failed = 0;
// a few at a time so we don't hammer the API
const queue = [...todo];
await Promise.all(Array.from({ length: 3 }, async () => {
  while (queue.length) {
    const m = queue.shift();
    try { await generate(m); } catch (e) { failed++; console.error(`\n[${m.id}] FAILED: ${e.message}`); }
  }
}));
console.log(failed ? `\nDone with ${failed} failure(s).` : '\nAll done. Refresh the game.');
