// node --test tests/build.test.mjs : versioned code urls (server/build.js). the page names its code under /v/<build>/,
// those are kept for good (immutable) while the build is current, an old build's url and the plain paths are always
// rechecked, models next to a script never become immutable, every preloaded module exists, and an edited file gives a
// new build (so a page can never mix old and new code)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const PORT = 3980 + Math.floor(Math.random() * 9);
const B = `http://localhost:${PORT}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

test('versioned code urls', async () => {
  const srv = spawn(process.execPath, ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(PORT), JF_DATA_DIR: fs.mkdtempSync(path.join(os.tmpdir(), 'jfbuild-')) }, stdio: 'ignore' });
  const touched = path.join(ROOT, 'public/js/ctx.js'), st0 = fs.statSync(touched);
  try {
    for (let i = 0; i < 80; i++) { try { await fetch(B + '/health'); break; } catch { await sleep(200); } }
    const page = await fetch(B + '/'), html = await page.text();
    assert.equal(page.headers.get('cache-control'), 'no-cache', 'the page itself is always rechecked');
    const id = /\/v\/([0-9a-f]+)\//.exec(html)[1];
    const im = JSON.parse(/<script type="importmap">([\s\S]*?)<\/script>/.exec(html)[1]).imports;
    assert.equal(im.three, `/v/${id}/vendor/three/build/three.module.js`);
    assert.equal(im['/js/'], `/v/${id}/js/`, "import('/js/...') anywhere on the page gets the page's own module");
    assert.equal(im['/shared/'], `/v/${id}/shared/`);
    assert.ok(html.includes(`<script type="module" src="/v/${id}/js/main.js">`));
    assert.ok(html.includes(`<link rel="stylesheet" href="/v/${id}/style.css">`));
    const pre = [...html.matchAll(/modulepreload" href="([^"]+)"/g)].map((m) => m[1]);
    assert.ok(pre.length > 100, `the boot chain is preloaded (${pre.length})`);
    for (const u of pre) assert.equal((await fetch(B + u, { method: 'HEAD' })).status, 200, u);
    // this build's code: kept for good. an old build, the plain path, a model: rechecked
    assert.equal((await fetch(`${B}/v/${id}/js/main.js`, { method: 'HEAD' })).headers.get('cache-control'), 'public, max-age=31536000, immutable');
    { const r = await fetch(`${B}/v/0123456789/js/main.js`, { method: "HEAD" }); assert.equal(r.status, 200, "an old build still loads"); assert.doesNotMatch(r.headers.get("cache-control") || "", /immutable/); }
    assert.doesNotMatch((await fetch(`${B}/js/main.js`, { method: 'HEAD' })).headers.get('cache-control'), /immutable/);
    { const r = await fetch(`${B}/v/${id}/models/cast/c_dale.glb`, { redirect: 'manual' }); assert.equal(r.status, 302, 'media is not in the build id: its own address'); assert.equal(r.headers.get('location'), '/models/cast/c_dale.glb'); }
    { const r = await fetch(`${B}/v/${id}/models/story/index.json`, { redirect: 'manual' }); assert.equal(r.status, 302, 'json in a media folder is not in the hash either'); }
    assert.equal((await fetch(`${B}/v/${id}/vendor/three/build/three.module.js`, { method: 'HEAD' })).headers.get('cache-control'), 'public, max-age=31536000, immutable', 'three.js: its version is in the hash');
    assert.equal((await fetch(`${B}/js/main.js%00`)).status, 400, 'a null byte: 400, not a hang');
    assert.equal((await fetch(`${B}/v/${id}/../server.js`)).status, 404);
    // the page again: same ETag -> 304
    const again = await fetch(B + '/', { headers: { 'if-none-match': page.headers.get('etag') } });
    assert.equal(again.status, 304);
    // an edit: a new build, new urls, and the old build's code isn't immutable any more
    fs.utimesSync(touched, st0.atime, new Date(Date.now() + 5000));
    await sleep(2200);
    const id2 = /\/v\/([0-9a-f]+)\//.exec(await (await fetch(B + '/')).text())[1];
    assert.notEqual(id2, id, 'an edited file is a new build');
    assert.doesNotMatch((await fetch(`${B}/v/${id}/js/main.js`, { method: 'HEAD' })).headers.get('cache-control'), /immutable/);
  } finally { fs.utimesSync(touched, st0.atime, st0.mtime); srv.kill(); }
});
