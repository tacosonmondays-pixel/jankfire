// playwright e2e: play ACT I of OVERDUE start to finish in the real slice city, solo, from a fresh save.
// run: SP=<dir with pwlock.cjs> PORT=<port> node tests/story/e2e/t_act1.cjs   (needs a running server)
// env: STOP=1 stops at the first step that can't be done for real (default: fake it, note it, keep going, so one run
//      lists every gap); SHOTS=1 screenshots each step into $SP/shots/act1_*.png; FROM=m03_somethings_digesting starts
//      there (the steps before it are faked); UNTIL=m02 stops when that mission starts
//
// How each goal is played (what a player does, through the real keys and the real world):
//   reach / escort / deliver  stand a few metres outside the zone (a short travel teleport: the walk there is checked by
//                             tests/story/act1world.test.mjs on the walk graph), then WALK in holding W
//   talk                      walk up to the person (they must be standing in the world), F, then F / 1 through it
//   interact / pickup         walk to the glowing spot, F
//   flag                      a cutscene (watched 1.5 s, then skipped like a player can), a choice (pick 1), or a fight
//   enterCar                  walk to a parked car, F
// Fights and encounters belong to the other Act I lanes (B: fights, C: encounters): until they land, those steps are
// faked with the rehearsal's own events and reported as "dev:B" / "dev:C". Anything else that has to be faked is a
// BLOCKER and goes first in the report.
require(process.env.SP + '/pwlock.cjs');
const { chromium } = require('playwright');
const fs = require('fs');
const skipIntro = require('./skipintro.cjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const PORT = process.env.PORT || 3311, OUT = (process.env.SP || '.') + '/shots', STOP = process.env.STOP === '1', SHOTS = process.env.SHOTS === '1', FROM = process.env.FROM || '';
// steps owned by the fight (B) and encounter (C) sessions: [quest, step] -> who
const OWNED = { 'm02_sauce_run.ambush': 'C', 'm04_clocking_in.fight': 'B', 'm06_tickets_please.hold': 'B', 'm06_tickets_please.break': 'B' };

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 640, height: 360 } });
  const errs = [];
  pg.on('pageerror', (e) => errs.push('PAGEERR ' + e.message + ' ' + (e.stack || '').split('\n')[1]));
  pg.on('console', (m) => { if (m.type() === 'error' && !/favicon|404/.test(m.text())) errs.push(m.text()); });
  await pg.addInitScript(() => {
    localStorage.setItem('jf_giftseen_all', '1');
    localStorage.setItem('jankfire', JSON.stringify({ name: 'act1', jank: 0, loadout: { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' } }));
    if (!sessionStorage.getItem('a1')) { sessionStorage.setItem('a1', 1); localStorage.removeItem('jfStorySaves'); }
  });
  await pg.goto(`http://localhost:${PORT}/?story=1&fresh=1`); await sleep(2000);
  await pg.click('#storyBtn', { force: true }); await sleep(700);
  await pg.click('#storyPick .st-btn.yellow', { force: true }); await sleep(9000);
  const ev = (f, a) => pg.evaluate(f, a);
  const key = async (code, ms = 70) => { await pg.keyboard.down(code); await sleep(ms); await pg.keyboard.up(code); };
  // the tracked objective + what its goal really is (from the engine's quest defs)
  const obj = () => ev(async () => {
    const ST = window.JF_STORY, S = ST.S, o = S.quests.objectives().find((x) => x.kind === 'main') || null;
    const { ME } = await import('/js/player.js');
    const sc = ST.scene && ST.scene.playing(), tk = await import('/js/story/talk.js');
    if (!o) return { none: true, done: Object.keys(S.st.quests).filter((q) => S.st.quests[q].done), pos: ME.pos };
    const st = S.defs.quests[o.quest].steps.find((x) => x.id === o.step), gi = o.goals.findIndex((g) => !g.done), g = (st.goals || [st.goal])[gi < 0 ? 0 : gi];
    return { quest: o.quest, step: o.step, text: o.text, marker: o.marker, goal: g, scene: !!sc, talking: !!tk.talking(), pos: ME.pos.map((v) => +v.toFixed(1)), map: (await import('/shared/map.js')).MAP.id };
  });
  const where = (m) => ev((m) => { const p = window.JF_STORY.where(m); return p ? [...p] : null; }, m);
  const tp = (p, yaw) => ev(async ([p, yaw]) => { const { ME } = await import('/js/player.js'); ME.pos = [p[0], p[1] + 0.3, p[2]]; ME.vel = [0, 0, 0]; if (yaw != null) ME.yaw = yaw; }, [p, yaw]);
  const pos = () => ev(async () => (await import('/js/player.js')).ME.pos.slice());
  const face = (p) => ev(async (p) => { const { ME } = await import('/js/player.js'); ME.yaw = Math.atan2(-(p[0] - ME.pos[0]), -(p[2] - ME.pos[2])); ME.pitch = 0; }, p);
  const floorAt = (p) => ev(async (p) => { const { dropTo } = await import('/js/story/actors.js'); return dropTo([p[0], p[1], p[2]], 2); }, p);
  // walk (W held, steering at it every 150 ms) until within d of p, or give up after t ms
  async function walkTo(p, d = 1.2, t = 9000) {
    await face(p); await pg.keyboard.down('KeyW');
    try { // (steered in the page every frame: one round trip, the swiftshader frames are slow)
      return await ev(async ([p, d, t]) => { const { ME } = await import('/js/player.js'); const t0 = performance.now();
        return new Promise((res) => { const f = () => { const dx = p[0] - ME.pos[0], dz = p[2] - ME.pos[2]; if (Math.hypot(dx, dz) < d) return res(true); if (performance.now() - t0 > t) return res(false); ME.yaw = Math.atan2(-dx, -dz); requestAnimationFrame(f); }; f(); }); }, [p, d, t]);
    } finally { await pg.keyboard.up('KeyW'); }
  }
  // stand off r metres from p, on floor at p's height (tries 8 directions), facing p
  async function standOff(p, r) {
    const q = await ev(async ([p, r]) => {
      const { dropTo } = await import('/js/story/actors.js'), { playerOverlap, raycast } = await import('/shared/physics.js'), { BOXES } = await import('/shared/map.js');
      for (let i = 0; i < 16; i++) { // (a spot on p's floor, with nothing between it and p: you can walk straight in)
        const a = i * Math.PI / 8, q = [p[0] + Math.sin(a) * r, p[1], p[2] + Math.cos(a) * r], f = dropTo([q[0], p[1] + 1, q[2]], 1);
        if (Math.abs(f - p[1]) > 0.7 || playerOverlap([q[0], f + 0.05, q[2]], BOXES)) continue;
        const dx = p[0] - q[0], dz = p[2] - q[2], L = Math.hypot(dx, dz), h = raycast([q[0], f + 1, q[2]], [dx / L, 0, dz / L], L, BOXES);
        if (h) continue;
        return [q[0], f, q[2]];
      }
      return null;
    }, [p, r]);
    await tp(q || p); await sleep(500); return q || p;
  }
  async function shiftR() { await pg.keyboard.down('Shift'); await key('KeyR'); await pg.keyboard.up('Shift'); }
  // grapple: from `from`, aim at `ring`, hold E (+ W) until we're above `top` m or 4 s pass, let go; did we land up there?
  async function grappleUp(ring, from, top) {
    await tp(from); await sleep(500);
    await ev(async (r) => { const { ME } = await import('/js/player.js'); const dx = r[0] - ME.pos[0], dz = r[2] - ME.pos[2]; ME.yaw = Math.atan2(-dx, -dz); ME.pitch = Math.atan2(r[1] - ME.pos[1] - 1.6, Math.hypot(dx, dz)); }, ring);
    await pg.keyboard.down('KeyE'); await pg.keyboard.down('KeyW');
    let y = 0; const t0 = Date.now();
    while (Date.now() - t0 < 4000) { y = (await pos())[1]; if (y > top) break; await sleep(60); }
    await pg.keyboard.up('KeyE'); await sleep(700); await pg.keyboard.up('KeyW'); await sleep(1200);
    const q = await pos(); return { ok: q[1] > top - 2.5, y: +q[1].toFixed(1) };
  }
  // play a conversation through: F to the next line, 1 when there are answers
  async function talkThrough(max = 80) {
    for (let i = 0; i < max; i++) {
      const s = await ev(async () => { const tk = await import('/js/story/talk.js'); return { on: tk.talking(), opts: document.querySelectorAll('.st-opt').length }; });
      if (!s.on) return true;
      if (s.opts) await key('Digit1'); else await key('KeyF');
      await sleep(220);
    }
    return false;
  }

  await skipIntro(pg);
  await pg.mouse.click(320, 180); await sleep(300);
  // software GL draws the streamed city at ~1 fps: the script stops drawing (the game still runs every frame) and
  // draws again only for a screenshot (NODRAW=0 keeps drawing)
  if (process.env.NODRAW !== '0') await ev(async () => { const { G } = await import('/js/ctx.js'); const r = G.renderer, o = r.render.bind(r); r.render = (sc, c) => { if (!window.__noDraw) o(sc, c); }; window.__noDraw = true; });
  const rows = [];
  let last = '', same = 0;
  for (let n = 0; n < 140; n++) {
    if (await ev(() => !!window.JF_STORY.S.st.flags.act1_done)) { console.log('END OF ACT I (flag act1_done)'); break; }
    let o = await obj();
    if (o.none) { console.log('NO MAIN OBJECTIVE. done:', o.done.join(' ')); break; }
    // a cutscene or a talk in the way: watch a moment, then skip it / talk it through like a player
    if (o.scene) { await sleep(1500); await ev(async () => { const sc = await import('/js/story/scene.js'); if (sc.playing()) sc.skipScene(); }); rows.push({ q: o.quest, s: o.step, how: 'scene', note: 'watched 1.5 s, skipped' }); await sleep(800); continue; }
    if (o.talking) { await talkThrough(); await sleep(500); continue; }
    const id = o.quest + '.' + o.step;
    if (process.env.UNTIL && o.quest.startsWith(process.env.UNTIL)) { console.log('UNTIL ' + process.env.UNTIL + ': stopping'); break; }
    if (FROM && !id.startsWith(FROM) && !rows.some((r) => r.q === FROM)) { await shiftR(); await sleep(400); rows.push({ q: o.quest, s: o.step, how: 'skip', note: 'FROM=' + FROM }); continue; }
    if (id === last) { if (++same > 3) { // the step won't move: fake it and say so
        const who = OWNED[id];
        rows.push({ q: o.quest, s: o.step, type: o.goal.type, how: who ? 'dev:' + who : 'BLOCKED', note: who ? `${who}'s part, faked` : `stuck: ${o.text || o.goal.type} (${JSON.stringify(o.goal).slice(0, 120)})` });
        console.log((who ? 'DEV ' : 'BLOCKED ') + id, JSON.stringify(o.goal).slice(0, 160));
        if (!who && STOP) break;
        await shiftR(); await sleep(700); same = 0; last = ''; continue; } }
    else { same = 0; last = id; }
    const g = o.goal, t0 = Date.now();
    console.log(`> ${id} [${g.type}] "${o.text}" marker=${o.marker} at ${o.pos} ${o.map}`);
    if (SHOTS) { await ev(() => { window.__noDraw = false; }); await sleep(2500); await pg.screenshot({ path: `${OUT}/act1_${String(rows.length).padStart(2, '0')}_${o.step}.png` }).catch(() => {}); await ev(() => { window.__noDraw = true; }); }
    let how = 'real', note = '';
    if (OWNED[id]) { how = 'dev:' + OWNED[id]; note = 'faked (other lane)'; await shiftR(); }
    else if (g.type === 'flag' && g.flag === 'flag.sim_won') {
      // the Machine's terminal (F) opens the sims; a headless test doesn't play a whole match: it comes back the way
      // story/main.js does after one (onMain), which is what wins the step
      const T = await where('sims:suburb'); await standOff(T, 2.2); await walkTo(T, 1.6, 4000); await key('KeyF'); await sleep(2500);
      const menu = await ev(() => !document.getElementById('menu').classList.contains('hidden'));
      note = menu ? 'F at the Machine opened the sims menu; came back via onMain (no match played headless)' : 'F at the Machine did NOT open the menu';
      await ev(async () => { const { G } = await import('/js/ctx.js'); sessionStorage.setItem('jfStoryBack', JSON.stringify({ slot: G.story.cur.slot, state: 'sim' })); G.story.onMain(); });
      await sleep(9000); await pg.mouse.click(320, 180);
      if (!menu) how = 'BLOCKED';
    } else if (g.type === 'flag') { await sleep(2500); const tk = await ev(async () => (await import('/js/story/talk.js')).talking()); if (tk) { await talkThrough(); note = 'a choice: picked 1'; } else note = 'waited'; }
    else if (g.type === 'talk') {
      let p = await where(g.npc);
      if (!p) { how = 'BLOCKED'; note = g.npc + ' is nowhere'; }
      else {
        const far = await pos(); if (Math.hypot(far[0] - p[0], far[2] - p[2]) > 12) await standOff(p, 6);
        await sleep(600); p = await where(g.npc); await walkTo(p, 1.8, 7000); await face(p); await sleep(300);
        const prompt = await ev(() => document.getElementById('stPrompt').textContent);
        await key('KeyF'); await sleep(400); await talkThrough();
        note = prompt ? `"${prompt}"` : 'no TALK prompt ' + JSON.stringify(await ev(async (id) => { const { actors } = await import('/js/story/actors.js'); const { ME } = await import('/js/player.js'); const boot = await import('/js/story/boot.js'); const a = actors.get(id); return { spawned: !!a, at: a && a.pos.map((v) => +v.toFixed(1)), me: ME.pos.map((v) => +v.toFixed(1)), hidden: a && a.hidden, locked: boot.locked(), lines: !!(window.JF_STORY.S.defs.npcs[id] || {}).lines, n: actors.size }; }, g.npc));
      }
    } else if (g.type === 'interact' || g.type === 'pickup') {
      const sp = await ev((g) => { for (const v of (window.JF_STORY.spots || new Map()).values ? window.JF_STORY.spots.values() : []) if ((g.item && v.item === g.item) || (g.thing && v.thing === g.thing)) return v.p; return null; }, g);
      const p = sp || await where(g.marker || g.zone || g.thing);
      if (!p) { how = 'BLOCKED'; note = 'no spot'; }
      else { await standOff(p, 4); await walkTo(p, 1.0, 6000); await sleep(300); const prompt = await ev(() => document.getElementById('stPrompt').textContent); await key('KeyF'); await sleep(600); note = prompt ? `"${prompt}"` : 'no USE prompt'; }
    } else if (g.type === 'reach' || g.type === 'escort') {
      const p = await where(g.zone), r = await ev((z) => window.JF_STORY.S.defs.zones[z].r || 2, g.zone);
      if (!p) { how = 'BLOCKED'; note = 'zone ' + g.zone + ' has no spot'; }
      else if (g.zone === 'bottom:rooftops') { // by hand: stand in the yard, aim at the yellow ring, hold E and run at it, let go at the top
        const { WOK } = await ev(async () => import('/shared/city/act1set.js').then((m) => ({ WOK: m.WOK })));
        const up = await grappleUp(WOK.ring, [-181, 4.05, 208.2], 15);
        if (!up.ok) { await tp([p[0], p[1] + 0.5, p[2]]); note = `grapple didn't get up there (${up.y}): put on the roof`; how = 'tp'; } else note = `grappled up (top ${up.y} m)`;
      } else if (g.zone === 'bottom:lostfound' && o.step === 'line') { // by hand: from the tall roof, F on Dumpling's washing line
        const { WOK } = await ev(async () => import('/shared/city/act1set.js').then((m) => ({ WOK: m.WOK })));
        await tp([WOK.line[0][0] + 0.6, 16.45, WOK.line[0][2]], Math.PI / 2); await sleep(600);
        await key('KeyF'); await sleep(250);
        const rode = await ev(async () => { const m = await import('/js/city/ingame.js').catch(() => null); const s = m && m.cityStream(); return s ? !!s.zip : null; });
        await sleep(4000);
        const q = await pos(); note = `F on the washing line (riding: ${rode}), let go at ${q.map((v) => v.toFixed(1))}`;
        if (Math.hypot(q[0] + 189, q[2] - 200) > 7) { await standOff(p, r + 3); await walkTo(p, Math.max(0.8, r - 1), 9000); note += '; walked the rest'; }
      }
      else { await standOff(p, r + 3); const ok = await walkTo(p, Math.max(0.8, r - 1), 9000); note = ok ? `walked in (r ${r})` : `couldn't walk in from ${r + 3} m`; }
      if (g.if && !(await ev((c) => window.JF_STORY.S.test(c), g.if))) note += `; needs ${g.if}`;
    } else if (g.type === 'enterCar') {
      const c = await ev(async () => { const { G } = await import('/js/ctx.js'); return G.story.carNear(); }); // (the one the HUD points at)
      if (!c) { how = 'BLOCKED'; note = 'no car anywhere near'; }
      else { await standOff(c, 3.2); await sleep(300); await key('KeyF'); await sleep(1500); note = (await ev(async () => (await import('/js/story/drive.js')).driving())) ? 'got in' : "F didn't get in"; await key('KeyF'); await sleep(800); }
    } else if (g.type === 'survive' || g.type === 'kill' || g.type === 'killBoss') { how = 'dev:' + (g.type === 'killBoss' ? 'B' : 'C'); note = 'fight/encounter, faked'; await shiftR(); }
    else { note = 'no player action for ' + g.type; }
    await sleep(900);
    const after = await obj();
    const moved = after.none || after.quest !== o.quest || after.step !== o.step || after.scene || after.talking;
    if (!moved && how === 'real') { how = 'BLOCKED?'; }
    rows.push({ q: o.quest, s: o.step, type: g.type, how, note, ms: Date.now() - t0 });
    console.log(`  ${how} ${moved ? '-> ' + (after.none ? 'END' : after.step) : '(no change)'} ${note}`);
  }
  const done = await ev(() => Object.keys(window.JF_STORY.S.st.quests).filter((q) => window.JF_STORY.S.st.quests[q].done));
  console.log('\nLEDGER');
  for (const r of rows) console.log([r.q, r.s, r.type || '', r.how, r.note || ''].join(' | '));
  const blk = rows.filter((r) => /BLOCKED/.test(r.how));
  console.log('\nFIRST BLOCKER:', blk[0] ? `${blk[0].q}.${blk[0].s}: ${blk[0].note}` : 'none');
  console.log('missions done:', done.join(' '));
  console.log('ERRORS', errs.length, errs.slice(0, 10).join('\n'));
  fs.writeFileSync(OUT + '/act1_ledger.json', JSON.stringify({ rows, done, errs }, null, 1));
  await b.close();
})();
