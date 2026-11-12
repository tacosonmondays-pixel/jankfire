// node --test tests/static.test.mjs : static files (server/static.js). gzip comes back byte-identical, a second ask is
// a 304, models/sounds may be shown stale while the browser rechecks (code never), and a gzipped copy is kept on disk
// so a file past the memory cap isn't gzipped again for every player.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import zlib from 'node:zlib';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const PORT = 3990 + Math.floor(Math.random() * 9);
const B = `http://localhost:${PORT}`;

test('static files: gzip, 304s, media caching, the disk copy', async () => {
  const srv = spawn(process.execPath, ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(PORT), JF_DATA_DIR: fs.mkdtempSync(path.join(os.tmpdir(), 'jfstatic-')) }, stdio: 'ignore' });
  try {
    for (let i = 0; i < 80; i++) { try { await fetch(B + '/health'); break; } catch { await new Promise((r) => setTimeout(r, 200)); } }
    const glb = 'public/models/cast/c_dale.glb', js = 'public/js/story/looks.js';
    const raw = fs.readFileSync(path.join(ROOT, glb));
    // fetch() would undo the gzip for us: ask with plain http to see the bytes on the wire
    const get = (p, h = {}) => new Promise((ok, no) => import('node:http').then(({ default: http }) => http.get(B + p, { headers: { 'accept-encoding': 'gzip', ...h } }, (r) => { const b = []; r.on('data', (d) => b.push(d)); r.on('end', () => ok({ code: r.statusCode, h: r.headers, body: Buffer.concat(b) })); }).on('error', no)));
    const a = await get('/models/cast/c_dale.glb');
    assert.equal(a.code, 200);
    assert.equal(a.h['content-encoding'], 'gzip');
    assert.ok(zlib.gunzipSync(a.body).equals(raw), 'gzip comes back byte-identical');
    assert.match(a.h['cache-control'], /stale-while-revalidate/, 'a model may be shown while the browser rechecks it');
    const again = await get('/models/cast/c_dale.glb', { 'if-none-match': a.h.etag });
    assert.equal(again.code, 304, 'same version: 304');
    const j = await get('/js/story/looks.js');
    assert.equal(j.code, 200); assert.equal(j.h['cache-control'], 'no-cache', 'code is always rechecked');
    assert.ok(zlib.gunzipSync(j.body).equals(fs.readFileSync(path.join(ROOT, js))));
    // the disk copy: there, and it is the same gzip
    const dir = path.join(os.tmpdir(), 'jf-gz');
    const hit = fs.readdirSync(dir).filter((f) => f.endsWith('.gz')).map((f) => fs.readFileSync(path.join(dir, f))).some((b) => b.equals(a.body));
    assert.ok(hit, 'a gzipped copy was kept on disk');
  } finally { srv.kill(); }
});
