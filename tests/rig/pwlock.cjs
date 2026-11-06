// Machine-wide cap on concurrent headless browsers. Loaded into every node process via NODE_OPTIONS=--require.
// Too many Chromium instances at once took the whole container down, so chromium.launch waits for a free slot.
// Slots are directories (mkdir is atomic); a slot whose owner process died is reclaimed.
const Module = require('module');
const fs = require('fs');
const path = require('path');
const DIR = path.join(require('os').tmpdir(), 'jf-pwslots'); // machine-wide
const SLOTS = Number(process.env.PW_SLOTS) || 2;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const alive = (pid) => { try { process.kill(pid, 0); return true; } catch (e) { return e.code === 'EPERM'; } };

async function acquire() {
  fs.mkdirSync(DIR, { recursive: true });
  let warned = false;
  for (;;) {
    for (let i = 0; i < SLOTS; i++) {
      const d = path.join(DIR, 'slot' + i);
      try {
        fs.mkdirSync(d);
        fs.writeFileSync(path.join(d, 'pid'), String(process.pid));
        return d;
      } catch (e) {
        if (e.code !== 'EEXIST') throw e;
        let pid = 0;
        try { pid = Number(fs.readFileSync(path.join(d, 'pid'), 'utf8')); } catch { /* being created */ }
        let age = 0;
        try { age = Date.now() - fs.statSync(d).mtimeMs; } catch { /* gone */ }
        if ((pid && !alive(pid)) || (!pid && age > 10000)) fs.rmSync(d, { recursive: true, force: true }); // stale
      }
    }
    if (!warned) { warned = true; process.stderr.write(`[pwlock] waiting for a free browser slot (${SLOTS} max)...\n`); }
    await sleep(400 + Math.random() * 400);
  }
}
const release = (d) => { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* fine */ } };

const origLoad = Module._load;
Module._load = function (request) {
  const m = origLoad.apply(this, arguments);
  if ((request === 'playwright' || request === 'playwright-core') && m && m.chromium && !m.chromium.__pwlock) {
    const ch = m.chromium, launch = ch.launch.bind(ch);
    ch.__pwlock = true;
    ch.launch = async (...args) => {
      const slot = await acquire();
      let done = false;
      const rel = () => { if (!done) { done = true; release(slot); } };
      process.once('exit', rel);
      try {
        const b = await launch(...args);
        const close = b.close.bind(b);
        b.close = async (...a) => { try { return await close(...a); } finally { rel(); } };
        b.on('disconnected', rel);
        return b;
      } catch (e) { rel(); throw e; }
    };
  }
  return m;
};
