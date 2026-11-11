// node tests/story/armgrip.test.mjs : REVENUE PROTECTION's arms against the tunnel wall (public/js/story/armgrip.js, the
// look only): no rope joint and no hand is drawn outside the bore for any arm the room sends (grabbers on every rail
// spot, sweepers, snatchers, arms out of the mouth) at any point of their reach, the knot stays where the room judges
// it, and the two hauling arms plant their hands flat on the lining, ride it back with the tunnel and go hand over hand
import assert from 'node:assert/strict';
import { ARENA, GEO0, RP, armPose, armExt, gripSpots, sweepY, sweepZ, wallA } from '../../shared/story/train.js';
import { armJoints, flatK, handFit, handPts, haulHand, haulPath, jointMax, newHaul, stepHaul, plantOk, rad, HAUL, LINE, SEGR } from '../../public/js/story/armgrip.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };
const B = { R: ARENA.boreR, cy: ARENA.cy }, EPS = 1e-6;
// every arm the room makes, in every state, at a spread of THE GAP
function arms() {
  const out = [];
  for (const rear of [0, ARENA.cut]) gripSpots(rear).forEach((sp, i) => {
    const gp = sp.p, tgt = [gp[0] + sp.o[0] * 0.95, gp[1] + 0.75, gp[2] + sp.o[1] * 0.95];
    for (const sock of sp.side > 0 ? [8, 9, 10, 11, 0, 1] : [2, 3, 4, 5, 6, 7]) out.push({ k: 'grab', sock, tgt, gp, dur: RP.grab.reach });
    for (const sock of sp.side < 0 ? [0, 1] : [2, 3]) out.push({ k: 'grab', sock, mouth: 1, tgt, gp, dur: RP.grab.reach * 0.7 });
  });
  for (const side of [1, -1]) for (const hi of [false, true]) for (const rear of [0, ARENA.cut]) for (const st of ['tell', 'sweep', 'back']) for (const tt of [0, 0.5, 1.2]) {
    const a = { k: 'sweep', sock: side > 0 ? 11 : 6, side, hi, rear, st, t: tt, dur: st === 'tell' ? RP.sweep.tell : 1 }, y = sweepY(a);
    out.push({ ...a, wa: wallA(side, y), tgt: [-side * RP.sweep.x, y, sweepZ(a)], fixed: true });
  }
  for (const sock of [2, 3]) for (const p of [[0, 1, 4.7], [2.0, 1.3, 14], [-1.9, 3.45, 25], [0.5, 4.5, 2]]) out.push({ k: 'snatch', sock, tgt: [p[0], p[1] + RP.snatch.up, p[2] - 0.2], dur: RP.snatch.reach });
  return out;
}
const STATES = [['reach', [0, 0.2, 0.4, 0.6, 0.8, 1]], ['tell', [0, 0.5, 1]], ['grip', [0]], ['hold', [0]], ['back', [0, 0.5, 1]], ['cut', [0, 0.5]]];
function each(fn) {
  for (const a0 of arms()) for (const gap of [22, 14, 6, 1.5]) for (const [st, us] of a0.fixed ? [[a0.st, [a0.t / a0.dur]]] : STATES) for (const u of us) {
    const a = { ...a0, st, t: u * a0.dur }, P = armPose(GEO0, a, gap, armExt(a));
    fn(a, P, gap);
  }
}

t('every rope joint is inside the bore, its thickness and the header rings included', () => {
  let worst = -9, cnt = 0;
  each((a, P) => {
    const J = armJoints(B, P, a.mouth), nj = J.length - 1;
    for (let k = 0; k < nj; k++) { const r = rad(B, J[k]), lim = jointMax(B, flatK(a.mouth, k)); worst = Math.max(worst, r + SEGR * flatK(a.mouth, k) - (B.R - LINE)); assert.ok(r <= lim + EPS, `${a.k} ${a.st} joint ${k} at r ${r.toFixed(3)} > ${lim.toFixed(3)}`); cnt++; }
    assert.ok(rad(B, J[nj]) < B.R, 'the last joint (the wrist) is inside');
  });
  console.log(`  ${cnt} joints, the outermost rope surface ${(-worst).toFixed(3)} m clear of the rings`);
});

t('the knot stays where the room judges shots: the last joint is the wrist, untouched', () => {
  each((a, P) => { const J = armJoints(B, P, a.mouth), w = J[J.length - 1], e = Math.hypot(w[0] - P.wrist[0], w[1] - P.wrist[1], w[2] - P.wrist[2]); assert.ok(e < 0.06, `${a.k} ${a.st} ${e} ${J.length} ${P.len}`); });
});

t('no hand goes through the lining: it is laid on it, and stays on its knot', () => {
  let laid = 0, all = 0, push = 0;
  each((a, P) => {
    if (a.st === 'cut') return;
    const w = P.wrist, d = a.gp && a.st !== 'back' ? [a.gp[0] - w[0], a.gp[1] - w[1], a.gp[2] - w[2]] : P.dir, l = Math.hypot(...d), dn = d.map((x) => x / l);
    const H = handFit(B, w, dn, Math.abs(dn[1]) > 0.9 ? [0, 0, 1] : [0, 1, 0]);
    for (const p of handPts(H)) assert.ok(rad(B, p) <= B.R - LINE + 1e-3, `${a.k} ${a.st}: a hand point at r ${rad(B, p).toFixed(3)}`);
    const sep = Math.hypot(H.o[0] - w[0], H.o[1] - w[1], H.o[2] - w[2]);
    assert.ok(sep <= 0.4 + 0.45, `${a.k} ${a.st}: the hand ${sep.toFixed(2)} m off its wrist`); // (the knot is 0.5 across at the size it is drawn)
    all++; if (H.tilt > 0 || H.push > 0.01) laid++; push = Math.max(push, H.push);
  });
  console.log(`  ${laid} of ${all} hands laid on the wall, pushed in at most ${push.toFixed(2)} m`);
});

t('a hand pointing at a rail it grips is left as it was', () => {
  for (const sp of gripSpots(0)) {
    const w = [sp.p[0] + sp.o[0] * 0.95, sp.p[1] + 0.75, sp.p[2] + sp.o[1] * 0.95], d = [sp.p[0] - w[0], sp.p[1] - w[1], sp.p[2] - w[2]], l = Math.hypot(...d), f = d.map((x) => x / l);
    const H = handFit(B, w, f);
    assert.equal(H.tilt, 0); assert.equal(H.push, 0);
    assert.ok(Math.hypot(H.o[0] - (w[0] + f[0] * 0.4), H.o[1] - (w[1] + f[1] * 0.4), H.o[2] - (w[2] + f[2] * 0.4)) < 1e-9);
  }
});

t('the haul: hands plant flat on the lining, ride it back with the tunnel, and go hand over hand', () => {
  const face = -15.36, hs = [newHaul(0, face), newHaul(1, face)], wa = [3.3, -0.36], dt = 1 / 60, plants = [[], []];
  let run = 0, dist = 0, both = 0, none = 0;
  for (let f = 0; f < 60 * 12; f++) {
    run += 12 * dt; dist = (dist + 12 * dt) % 96;
    hs.forEach((h, i) => {
      const z0 = h.z, ph0 = h.ph, ev = stepHaul(h, { dt, run, face, z0: ARENA.z0, dist, side: Math.cos(wa[i]) < 0 ? -1 : 1, a: wa[i], v: 12, other: hs[1 - i], lead: i === 0 });
      if (ev === 'plant') { plants[i].push(f * dt); const side = Math.cos(wa[i]) < 0 ? -1 : 1; assert.ok(plantOk(ARENA.z0, dist, side, h.z - HAUL.skid - HAUL.back, h.z + HAUL.front), 'planted on clean brick'); }
      if (ph0 === 'grip' && h.ph === 'grip' && h.t > HAUL.skidT + dt) assert.ok(Math.abs(z0 - h.z - 12 * dt) < 1e-6, 'a planted hand goes back with the tunnel, exactly');
      const H = haulHand(B, h);
      for (const p of handPts(H)) assert.ok(rad(B, p) <= B.R + EPS, `haul hand at r ${rad(B, p).toFixed(3)}`);
      if (h.ph === 'grip') { assert.ok(B.R - (rad(B, H.o) + 0.42) < 0.06, 'flat on the brick'); assert.ok(H.f[2] > 0.99, 'fingers up the tunnel'); }
      assert.ok(h.z > face + 0.5, 'never behind the face');
      const S0 = GEO0.sockets[i ? 10 : 7], S = [S0[0], B.cy + S0[1], face - 0.14 + S0[2]], pts = haulPath(B, S, H.o, wa[i], 0.4), J = armJoints(B, { pts, wrist: H.o }, 0);
      for (let k = 0; k < J.length - 1; k++) assert.ok(rad(B, J[k]) <= jointMax(B, flatK(0, k)) + EPS);
    });
    const g = hs.filter((h) => h.ph === 'grip').length; if (g === 2) both++; if (!g) none++;
  }
  for (const p of plants) { assert.ok(p.length >= 6, 'it keeps planting: ' + p.length); const gaps = p.slice(1).map((x, i) => x - p[i]); assert.ok(Math.max(...gaps) < 2.2, 'a plant every couple of seconds'); }
  assert.ok(both < 60 * 12 * 0.2 && none < 60 * 12 * 0.35, `mostly one hand at a time (both ${both}, none ${none} frames)`);
  console.log(`  ${plants[0].length + plants[1].length} plants in 12 s, both gripping ${(both / 720 * 100).toFixed(0)}% of the time, neither ${(none / 720 * 100).toFixed(0)}%`);
});

t('two hands that let go together do not stay in step', () => {
  const face = -10, hs = [newHaul(0, face), newHaul(1, face)], wa = [3.3, -0.36], dt = 1 / 60;
  for (const h of hs) { h.ph = 'let'; h.t = 0; h.z = face + 3; }
  let run = 0, dist = 0, both = 0;
  for (let f = 0; f < 60 * 6; f++) { run += 12 * dt; dist = (dist + 12 * dt) % 96; hs.forEach((h, i) => stepHaul(h, { dt, run, face, z0: ARENA.z0, dist, side: i ? 1 : -1, a: wa[i], v: 12, other: hs[1 - i], lead: i === 0 })); if (f > 120 && hs.every((h) => h.ph === hs[0].ph)) both++; }
  assert.ok(both < 60, `in step ${both} frames of the last 4 s`);
});

console.log(`\n${n} armgrip tests passed`);
