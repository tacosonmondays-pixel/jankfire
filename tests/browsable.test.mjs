// node tests/browsable.test.mjs : /server/ serves only server/room.js's import closure (the story's solo referee loads
// it in a web worker). everything else under server/ (and anywhere else) is a 404, whatever the url tricks
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import net from 'node:net';
import { fileURLToPath } from 'node:url';
import { browsableServer } from '../server/browsable.js';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

await t('the list is room.js and the server modules it imports, never the store / accounts / http side', () => {
  const files = browsableServer(ROOT).files();
  assert.ok(files.includes('room.js') && files.includes('storyref.js') && files.includes('lobby.js'));
  for (const no of ['store.js', 'accounts.js', 'static.js', 'story.js', 'browsable.js', 'citycache.js']) assert.ok(!files.includes(no), no);
  assert.ok(files.every((f) => f.endsWith('.js') && !f.includes('..')));
});

await t('a symlink in the closure is never followed', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'jfb-')), sd = path.join(tmp, 'server');
  fs.mkdirSync(sd);
  fs.writeFileSync(path.join(tmp, 'outside.js'), 'export const x = 1;');
  fs.writeFileSync(path.join(sd, 'room.js'), "import './a.js';\nimport './link.js';\n");
  fs.writeFileSync(path.join(sd, 'a.js'), 'export const a = 1;');
  fs.symlinkSync(path.join(tmp, 'outside.js'), path.join(sd, 'link.js'));
  const f = browsableServer(tmp);
  assert.deepEqual(f.files(), ['a.js', 'room.js']);
  assert.equal(f('/server/link.js'), null);
  fs.rmSync(tmp, { recursive: true, force: true });
});

// the real server: status codes for the tricks, and the same caching as the other static files
// (a port the OS says is free, not a random one that may be taken; and up to a minute to boot: under a busy machine
// with the rest of the suite running beside it, the server took over the old 12 s and every request was refused)
const PORT = await new Promise((res) => { const s = net.createServer().listen(0, () => { const p = s.address().port; s.close(() => res(p)); }); });
const srv = spawn(process.execPath, ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(PORT), JF_DATA_DIR: fs.mkdtempSync(path.join(os.tmpdir(), 'jfbd-')) }, stdio: 'ignore' });
let gone = null; srv.on('exit', (code) => { gone = code; });
let up = false;
for (let i = 0; i < 300 && !up && gone === null; i++) { try { up = (await fetch(`http://localhost:${PORT}/health`)).ok; } catch { await new Promise((r) => setTimeout(r, 200)); } }
if (!up) { srv.kill(); assert.fail(gone !== null ? `the server exited (${gone}) before it was up` : `the server wasn't up on port ${PORT} after 60 s`); }
const raw = (p, h = {}) => new Promise((res, rej) => { // (fetch would clean up ../ in the url before sending it)
  import('node:http').then(({ request }) => { const r = request({ host: 'localhost', port: PORT, path: p, headers: h }, (x) => { let b = ''; x.on('data', (d) => (b += d)); x.on('end', () => res({ status: x.statusCode, headers: x.headers, body: b })); }); r.on('error', rej); r.end(); });
});
try {
  await t('served: room.js and its modules (javascript)', async () => {
    for (const f of ['room.js', 'storyref.js', 'env.js', 'lobby.js']) { const r = await raw('/server/' + f); assert.equal(r.status, 200, f); assert.match(r.headers['content-type'], /javascript/); }
  });
  await t('404: the store, accounts, static, story, the browsable list itself, env files, data, listings', async () => {
    for (const p of ['/server/store.js', '/server/accounts.js', '/server/static.js', '/server/story.js', '/server/browsable.js', '/server/citycache.js', '/server/cityworker.js',
      '/server/', '/server', '/server/.env', '/.env', '/server/../.env', '/data/jankfire-db.json', '/server/../data/jankfire-db.json', '/server/nope.js'])
      assert.equal((await raw(p)).status, 404, p);
  });
  await t('404: ../ and encoded traversal, absolute paths, query-string tricks', async () => {
    for (const p of ['/server/../server.js', '/server/..%2fserver.js', '/server/%2e%2e/server.js', '/server/%2e%2e%2fserver.js', '/server/..%5cserver.js', '/server/%252e%252e/server.js',
      '/server//etc/passwd', '/server/%2fetc%2fpasswd', '/server/./store.js', '/server/room.js/../store.js', '/server/store.js?room.js', '/server/store.js#room.js', '/server/store.js%00room.js', '/server/ROOM.JS'])
      assert.notEqual((await raw(p)).status, 200, p);
    assert.equal((await raw('/server/room.js?x=../store.js')).status, 200, 'a query on an allowed file is just ignored');
  });
  await t('the same caching as the other static files: ETag + 304, gzip', async () => {
    const a = await raw('/server/room.js', { 'accept-encoding': 'gzip' });
    assert.ok(a.headers.etag); assert.equal(a.headers['content-encoding'], 'gzip'); assert.equal(a.headers['cache-control'], 'no-cache');
    const b = await raw('/server/room.js', { 'if-none-match': a.headers.etag });
    assert.equal(b.status, 304);
  });
} finally { srv.kill(); }
console.log(n, 'passed');
