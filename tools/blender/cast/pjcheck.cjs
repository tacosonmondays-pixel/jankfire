// PALLET JACK through the game's own actor path (no pictures, numbers):
//   node tools/blender/cast/pjcheck.cjs <port>
// spawnActor('pallet_jack') -> the glb dressed onto the code skeleton, every part name there -> PJ.play each clip
// with updateActors + pjFrame stepping it: the joints have to move, the marks have to fire at their times, the damage
// states have to show and hide the right pieces, the far LOD has to swap in. exits 1 if anything is off.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [PORT = 3000] = process.argv.slice(2);
const parts = JSON.parse(fs.readFileSync(path.join(__dirname, '../../../public/models/cast/c_pallet_jack.parts.json'), 'utf8'));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 640, height: 360 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(800);
  const res = await pg.evaluate(async (want) => {
    const THREE = await import('three');
    const { G } = await import('/js/ctx.js');
    const looks = await import('/js/story/looks.js');
    const A = await import('/js/story/actors.js');
    const { PJ, pjFrame } = await import('/js/story/palletjack.js');
    const got = await looks.loadCast(['pallet_jack'], 30000);
    const out = { got, bad: [], clips: {} };
    const sc = new THREE.Scene(); G.scene = sc; PJ.fx = false;
    const cam = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 200); cam.position.set(0, 1.6, -6); cam.lookAt(0, 1, 0); cam.updateMatrixWorld(true);
    const a = A.spawnActor('pj_check', { look: 'pallet_jack', voice: {} }, [0, 0, 0], 0);
    out.blender = !!a.L.blender; out.kind = a.L.kind;
    // every tagged piece and marker the parts file promises is on him
    const tags = Object.keys(a.L.parts || {});
    out.tags = tags.length;
    for (const t of want.tags) if (!a.L.parts[t]) out.bad.push('no part ' + t);
    for (const m of want.marks) { const p = PJ.at(a, m); if (!p || !Number.isFinite(p.x + p.y + p.z)) out.bad.push('no marker ' + m); }
    let meshes = 0, named = 0; a.ch.root.traverse((o) => { if (o.isMesh) { meshes++; if (/^part_|^ot_|pj_/.test(o.name) || /^part_/.test(o.parent?.name || '')) named++; } });
    out.meshes = meshes;
    const evs = []; PJ.on((e) => evs.push([e.mark, e.clip]));
    const J = ['body', 'spine', 'head', 'arm', 'armL', 'foreR', 'foreL', 'legL', 'legR', 'kneeL', 'kneeR'];
    const snap = () => J.map((k) => { const o = a.ch[k]; return o ? [o.rotation.x, o.rotation.y, o.rotation.z, o.position.y] : [0, 0, 0, 0]; }).flat();
    let now = 0;
    const step = (dt) => { now += dt; A.updateActors(dt, now, [0, 1.6, -6]); pjFrame(dt, cam); };
    for (const clip of PJ.clips) {
      const C = PJ.data.clips[clip]; const len = C.len || C.loop || C.keys[C.keys.length - 1].t || 1;
      evs.length = 0; PJ.dmg(a, 'fresh'); PJ.vest(a, true);
      PJ.play(a, clip, { hold: true });
      const s0 = snap(); let moved = 0, nan = false;
      for (let t = 0; t < len + 0.4; t += 1 / 30) { step(1 / 30); const s = snap(); for (let i = 0; i < s.length; i++) { if (!Number.isFinite(s[i])) nan = true; moved = Math.max(moved, Math.abs(s[i] - s0[i])); } }
      const fired = evs.filter((e) => e[1] === clip).map((e) => e[0]);
      const need = C.marks.filter(([mt]) => mt <= len).map((m) => m[1]);
      const missing = need.filter((m) => !fired.includes(m));
      out.clips[clip] = { len: +len.toFixed(2), moved: +moved.toFixed(3), marks: fired.length + '/' + need.length };
      if (nan) out.bad.push(clip + ': a joint went NaN');
      if (moved < 0.02 && clip !== 'pj_carried') out.bad.push(clip + ': nothing moved');
      if (missing.length) out.bad.push(clip + ': marks never fired: ' + missing.join(' '));
    }
    // damage states: what shows, what hides
    const vis = (t) => { const g = a.L.parts[t]; if (!g) return null; let v = true; for (let o = g; o && o !== a.ch.root.parent; o = o.parent) v = v && o.visible; return v; };
    out.states = {};
    for (const [st, S] of Object.entries(want.states)) {
      PJ.play(a, 'pj_fight_idle'); PJ.vest(a, false); PJ.dmg(a, st); step(1 / 30);
      const on = (S.on || []).filter((t) => vis(t) !== true), off = (S.off || []).filter((t) => vis(t) !== false);
      out.states[st] = { shows: (S.on || []).length - on.length + '/' + (S.on || []).length, hides: (S.off || []).length - off.length + '/' + (S.off || []).length };
      if (on.length) out.bad.push(st + ': not showing ' + on.join(' ')); if (off.length) out.bad.push(st + ': not hiding ' + off.join(' '));
    }
    // the far LOD: past 28 m the lod pieces show and the near ones don't
    PJ.dmg(a, 'fresh'); PJ.vest(a, true); step(1 / 30);
    const tri = () => { let n = 0; a.ch.root.updateMatrixWorld(true); a.ch.root.traverse((o) => { if (!o.isMesh) return; let v = true; for (let p = o; p; p = p.parent) v = v && p.visible; if (v && o.geometry) n += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; }); return Math.round(n); };
    out.nearTris = tri();
    cam.position.set(0, 1.6, -40); cam.updateMatrixWorld(true); step(1 / 30); step(1 / 30); out.farTris = tri();
    cam.position.set(0, 1.6, -6); cam.updateMatrixWorld(true); step(1 / 30); step(1 / 30); out.nearAgain = tri();
    if (!(out.farTris < out.nearTris * 0.25)) out.bad.push('far LOD did not swap in');
    if (out.nearAgain !== out.nearTris) out.bad.push('near pieces did not come back');
    return out;
  }, { tags: Object.keys(parts.parts || {}).filter((t) => !/^_/.test(t)), marks: Object.keys(parts.markers || {}), states: parts.states || {} });
  console.log(JSON.stringify(res, null, 1));
  const bad = [...res.bad, ...new Set(errs)];
  console.log(bad.length ? 'FAILED:\n' + bad.join('\n') : 'PJ_CHECK ok: ' + Object.keys(res.clips).length + ' clips played through spawnActor, every mark fired, every state and the far LOD swapped');
  await b.close(); process.exit(bad.length ? 1 : 0);
})();
