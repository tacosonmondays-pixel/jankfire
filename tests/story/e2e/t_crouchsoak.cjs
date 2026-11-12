// playwright soak: hold crouch for a few minutes in story mode (next to an NPC at the start, then in the Gut by a bile
// pool with the crowd about) and check nothing piles up: JS heap, GPU geometries / textures / shader programs, Web
// Audio nodes made per second, DOM nodes, scene objects, story-worker traffic. no tab crash, no lost GL context.
// also checks the "Leave site?" guard (crouch is Left Ctrl too, and Ctrl+W closes a browser tab).
// the owner's report: holding crouch in liquid in front of an npc crashed the tab (browser, not the exe).
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_crouchsoak.cjs   (needs a running server)
// env: MINS=1 minutes of crouch per spot (default 1), KEY=KeyC or ControlLeft
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3411, MINS = +(process.env.MINS || 1), KEY = process.env.KEY || 'KeyC';
const fails = [];
const check = (ok, what) => { console.log((ok ? 'ok   ' : 'FAIL ') + what); if (!ok) fails.push(what); };

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--enable-precise-memory-info'] });
  const pg = await b.newPage({ viewport: { width: 640, height: 360 } });
  const errs = [];
  let crashed = false;
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  pg.on('console', (m) => { if (m.type() === 'error' && !/favicon|404/.test(m.text())) errs.push(m.text().slice(0, 200)); });
  pg.on('crash', () => { crashed = true; });
  await pg.addInitScript(() => {
    localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'soak', jank: 0 }));
    if (!sessionStorage.getItem('soak')) { sessionStorage.setItem('soak', 1); localStorage.removeItem('jfStorySaves'); }
    // counters: every Web Audio node made, the story worker's messages both ways, lost GL contexts
    const M = window.__M = { audioN: 0, toW: 0, fromW: 0, fromWB: 0, lost: 0 };
    const P = BaseAudioContext.prototype;
    for (const k of Object.getOwnPropertyNames(P)) if (k.startsWith('create') && typeof P[k] === 'function') { const o = P[k]; P[k] = function (...a) { M.audioN++; return o.apply(this, a); }; }
    const W0 = window.Worker;
    window.Worker = class extends W0 {
      constructor(...a) { super(...a); this.addEventListener('message', (e) => { M.fromW++; if (typeof e.data === 'string') M.fromWB += e.data.length; }); }
      postMessage(d, ...r) { M.toW++; return super.postMessage(d, ...r); }
    };
    document.addEventListener('webglcontextlost', () => { M.lost++; }, true);
  });
  await pg.goto(`http://localhost:${PORT}/?story=1&fresh=1`); await sleep(2000);
  await pg.click('#storyBtn', { force: true }); await sleep(700);
  await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000);
  await skipIntro(pg);
  await pg.mouse.click(320, 180); await sleep(300);
  const ev = (f, a) => pg.evaluate(f, a);
  await ev(() => { const f = () => { window.__fr = (window.__fr || 0) + 1; requestAnimationFrame(f); }; f(); });

  // the guard: mid-run, a beforeunload is cancelled (Chrome then asks "Leave site?"). test browsers skip it unless asked
  const guard = await ev(() => { window.__jfUnloadGuard = true; const e = new Event('beforeunload', { cancelable: true }); dispatchEvent(e); window.__jfUnloadGuard = false; return e.defaultPrevented; });
  check(guard, 'mid-run, closing / reloading the tab asks first (beforeunload guard)');

  const sample = () => ev(async () => {
    const { G } = await import('/js/ctx.js'); const { ME } = await import('/js/player.js');
    const i = G.renderer.info, M = window.__M; let objs = 0; G.scene.traverse(() => objs++);
    return { at: performance.now(), heap: performance.memory.usedJSHeapSize / 1048576, geo: i.memory.geometries, tex: i.memory.textures, prog: i.programs ? i.programs.length : 0,
      audio: M.audioN, toW: M.toW, fromW: M.fromW, fromWB: M.fromWB, lost: M.lost, dom: document.getElementsByTagName('*').length, objs, fr: window.__fr, crouch: !!ME.crouching, y: ME.pos[1] };
  });
  // hold crouch MINS minutes (a held key repeats in a real browser: repeat keydowns ~30/s), sampling every 10 s
  async function soak(name) {
    await sleep(3000);
    const rows = [await sample()];
    await pg.keyboard.down(KEY);
    const t0 = Date.now(); let next = 10000;
    while (Date.now() - t0 < MINS * 60000 && !crashed) {
      await pg.keyboard.down(KEY); await sleep(33);
      if (Date.now() - t0 >= next) { next += 10000; rows.push(await sample()); }
    }
    await pg.keyboard.up(KEY);
    if (crashed) { check(false, `${name}: the tab did not crash`); return; }
    const a = rows[1] || rows[0], z = rows[rows.length - 1], s = (z.at - a.at) / 1000, fr = Math.max(1, z.fr - a.fr);
    const heaps = rows.slice(1).map((r) => r.heap), half = Math.floor(heaps.length / 2), avg = (x) => x.reduce((p, q) => p + q, 0) / Math.max(1, x.length);
    console.log(`${name}: ${rows.length} samples over ${s.toFixed(0)} s, ${fr} frames, crouched ${z.crouch}, y ${z.y.toFixed(2)}`);
    console.log(`  heap ${a.heap.toFixed(0)} -> ${z.heap.toFixed(0)} MB, geo ${a.geo} -> ${z.geo}, tex ${a.tex} -> ${z.tex}, programs ${a.prog} -> ${z.prog}, dom ${a.dom} -> ${z.dom}, scene ${a.objs} -> ${z.objs}`);
    console.log(`  audio nodes ${(z.audio - a.audio)} (${((z.audio - a.audio) / s).toFixed(1)}/s, ${((z.audio - a.audio) / fr).toFixed(2)}/frame), worker in ${((z.fromW - a.fromW) / s).toFixed(1)} msg/s ${((z.fromWB - a.fromWB) / s / 1024).toFixed(1)} KB/s, out ${((z.toW - a.toW) / s).toFixed(1)} msg/s`);
    check(z.crouch, `${name}: actually crouched`);
    check(avg(heaps.slice(half)) - avg(heaps.slice(0, half)) < 25, `${name}: JS heap flat (second half vs first half of the soak)`);
    check(z.geo - a.geo <= 4 && z.tex - a.tex <= 2 && z.prog - a.prog <= 2, `${name}: GPU geometries / textures / programs flat`);
    check(z.dom - a.dom <= 5 && z.objs - a.objs <= 10, `${name}: DOM and scene object counts flat`);
    check((z.audio - a.audio) / s < 40 && (z.audio - a.audio) / fr < 3, `${name}: Web Audio nodes are not made every frame`);
    check((z.fromW - a.fromW) / s < 40 && (z.toW - a.toW) / s < 40, `${name}: story worker traffic steady (no pile-up)`);
    check(z.lost === 0, `${name}: GL context never lost`);
  }

  // 1. the start: crouched right in front of Dale
  await ev(async () => {
    const { ME } = await import('/js/player.js'); const { actors } = await import('/js/story/actors.js');
    const p = actors.get('dale').pos; ME.pos = [p[0] + 2, p[1] + 0.2, p[2] + 1]; ME.vel = [0, 0, 0]; ME.hold = ME.pos.slice();
    ME.yaw = Math.atan2(-(p[0] - ME.pos[0]), -(p[2] - ME.pos[2])); ME.pitch = 0;
  });
  await soak('start, by Dale');
  // 2. the Gut: by the bile pool with the most crowd people round it (bubbles, pops, green mist)
  if (!crashed) {
    await ev(async () => { const { ME } = await import('/js/player.js'); ME.pos = [-290, 41, -183]; ME.vel = [0, 0, 0]; ME.hold = ME.pos.slice(); });
    await sleep(15000);
    const g = await ev(async () => {
      const { ME } = await import('/js/player.js'); const { cityStream } = await import('/js/city/ingame.js'); const S = cityStream(), goo = [];
      for (const c of S.chunks.values()) if (c && c.packed && c.packed.shapes) for (const s of c.packed.shapes) if (s.goo) goo.push(s.goo);
      if (!goo.length) return null;
      const ppl = S.crowd.root.children.map((o) => o.position), n = (q) => ppl.filter((p) => Math.hypot(p.x - q[0], p.z - q[1]) < 8).length;
      goo.sort((a, c) => n(c) - n(a));
      // (some pools sit under a membrane or a stall: you'd be put on top of it. take the first you really stand in)
      for (const q of goo.slice(0, 12)) {
        ME.pos = [q[0], 40.05, q[1]]; ME.vel = [0, 0, 0]; ME.hold = ME.pos.slice();
        await new Promise((r) => setTimeout(r, 1500));
        if (Math.abs(ME.pos[1] - 40) < 0.6 && Math.hypot(ME.pos[0] - q[0], ME.pos[2] - q[1]) < 1) return { pools: goo.length, people: n(q), y: ME.pos[1] };
      }
      return { pools: goo.length, people: n(goo[0]), y: ME.pos[1], missed: true };
    });
    check(!!g, 'the Gut streamed in with its bile pools');
    if (g) { console.log(`  gut: ${g.pools} bile pools, ${g.people} people by this one, standing at y ${g.y.toFixed(2)}${g.missed ? ' (not in one!)' : ''}`); check(!g.missed, 'standing in a bile pool'); await soak('the Gut, in a bile pool'); }
  }
  check(!crashed, 'the tab never crashed');
  check(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  await b.close();
  console.log(fails.length ? `\n${fails.length} FAILED` : '\nALL OK');
  process.exit(fails.length ? 1 : 0);
})();
