// TICKETS, PLEASE on the client (OVERDUE, m06): what you see of the REVENUE PROTECTION fight. the combat referee owns
// all of it (server/storytrain.js: HP, phases, arms, hits, THE GAP, the fail); this only shows what its events say:
//   - the tunnel going past a train that stands still: ribs, sleepers and weak bulbs scroll by, and the bulbs go out
//     where the mask has been
//   - the mask (revenue_protection.glb, loaded here and not by the city's prop loader) at THE GAP, hauling: reach, grip,
//     drag. plates craze and fall, the left eye blows, the lower third drops, the Inspector glows
//   - every arm the room has: a chain of arm_seg along the same path the room checks shots against
//     (shared/story/train.js armPose), the blue wrist knot, the hand (fingers curl on a grip), a stump when severed
//   - THE GAP big on the HUD, the callouts, the finish (it comes apart along a cross) and the fail
//   - the quest glue for m06's fight steps, and the Blood Drive in your hands while you are on the train
// nothing here changes the fight: turn it off and it is still fought, just in the dark
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { G } from '../ctx.js';
import { hud } from '../hud.js';
import { fx } from '../fx.js';
import { sfx } from '../audio.js';
import { ME } from '../player.js';
import { MAP, MAPS } from '/shared/map.js';
import { glbLoader } from '../glbkit.js';
import { raycast } from '/shared/physics.js';
import { TRAIN, ARENA, RP, GEO0, geoFrom, armPose, armExt, armLive, sweepZ, rayFight, SPLIT, PLATES, ss } from '/shared/story/train.js';
import { makeBloodDrive } from './blooddrive.js';

export const RP_ID = 'revenue_protection_1', RP_QUEST = 'm06_tickets_please';
const SPEED = 12, SEG = 1.5, R = ARENA.boreR, CY = ARENA.cy; // m/s the tunnel goes past · one arm_seg · the bore
const fin = Number.isFinite, clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const v3 = (a) => Array.isArray(a) && a.length === 3 && a.every(fin);
const TRAINQ = /[?&]train=1\b/.test(location.search); // ?story=1&storytest=1&train=1: straight onto the train, the fight starts by itself
const std = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85, ...o });

function css() {
  if (document.getElementById('rpCss')) return;
  const s = document.createElement('style'); s.id = 'rpCss';
  s.textContent = `#rpGap{position:fixed;left:18px;top:58px;transform:rotate(-1.5deg);z-index:39;pointer-events:none;font-family:var(--font);color:#fff;text-align:center;
    background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:2px 18px 8px;min-width:200px}
  #rpGap.hidden,#rpFail.hidden{display:none}
  #rpGap .l{font-weight:700;letter-spacing:3px;font-size:14px;color:#4fd8ff} #rpGap .n{line-height:.95}
  #rpGap .n b{font-size:58px;color:#ffe14d;text-shadow:4px 4px 0 #ff00dc} #rpGap .n i{font-style:normal;font-weight:700;font-size:22px;margin-left:4px}
  #rpGap .tr{position:relative;height:10px;margin-top:4px;background:#000;outline:2px solid #fff} #rpGap .tr u{position:absolute;right:0;top:0;bottom:0;background:#4fd8ff}
  #rpGap .jk{display:flex;align-items:center;gap:6px;margin-top:7px;font-size:12px;font-weight:700;color:#7dff4f} #rpGap .jk s{flex:1;height:6px;background:#000;outline:2px solid #7dff4f;position:relative;text-decoration:none} #rpGap .jk u{position:absolute;left:0;top:0;bottom:0;background:#7dff4f}
  #rpGap .jk.hidden,#rpGap .bl.hidden{display:none} #rpGap .bl{margin-top:5px;font-size:13px;font-weight:700;color:#ff1f3d;text-transform:uppercase}
  #rpGap .vx{font-size:14px;font-style:italic;opacity:.85;min-height:16px;margin-top:3px;text-transform:lowercase}
  #rpGap.near{border-color:#ff3030;animation:rpShake .12s infinite} #rpGap.near .n b{color:#ff3030;text-shadow:4px 4px 0 #000} #rpGap.near .tr u{background:#ff3030}
  #rpGap.open .n b{color:#7dff4f}
  @keyframes rpShake{0%{transform:rotate(-1.5deg)}50%{transform:translate(3px,2px) rotate(1deg)}100%{transform:rotate(-1.5deg)}}
  #rpFail{position:fixed;inset:0;z-index:58;pointer-events:none;font-family:var(--font)}
  #rpFail i{position:absolute;background:#050307;width:34vw;height:120vh;top:-10vh;border-radius:17vw;transition:transform .32s cubic-bezier(.3,1.5,.5,1)}
  #rpFail i:nth-child(1){left:-6vw;transform:translateY(-130vh) rotate(8deg)} #rpFail i:nth-child(2){left:16vw;transform:translateY(130vh) rotate(-5deg)} #rpFail i:nth-child(3){left:38vw;transform:translateY(-130vh) rotate(3deg)}
  #rpFail i:nth-child(4){left:60vw;transform:translateY(130vh) rotate(-7deg)} #rpFail i:nth-child(5){left:80vw;transform:translateY(-130vh) rotate(6deg)}
  #rpFail.on i{transform:translateY(0) rotate(0deg)} #rpFail.on i:nth-child(2){transition-delay:.25s} #rpFail.on i:nth-child(3){transition-delay:.5s} #rpFail.on i:nth-child(4){transition-delay:.75s} #rpFail.on i:nth-child(5){transition-delay:1s}
  #rpFail p{position:absolute;left:0;right:0;top:44%;margin:0;text-align:center;color:#fff;font-size:34px;font-weight:700;opacity:0;transition:opacity .5s 1.5s} #rpFail.on p{opacity:1}`;
  document.head.appendChild(s);
}
const el = (tag, cls, text) => { const d = document.createElement(tag); if (cls) d.className = cls; if (text != null) d.textContent = text; return d; };
// a node turned about a point of its parent's space (the mask hanging off its last bolt, the face falling flat)
function pivot(node, P, rx, rz) {
  const M = new THREE.Matrix4().makeTranslation(P[0], P[1], P[2]).multiply(new THREE.Matrix4().makeRotationZ(rz)).multiply(new THREE.Matrix4().makeRotationX(rx)).multiply(new THREE.Matrix4().makeTranslation(-P[0], -P[1], -P[2]));
  M.decompose(node.position, node.quaternion, node.scale);
}

export function makeTrainFight(ST, { playScene }) {
  const T = { on: false, set: null, boss: null, loading: false, geo: GEO0, parts: null, step: '', stepT: 0, spawnT: 0, auto: false, fin: null, failT: 0, hitstop: 0, said: -1 };
  const F = { live: false, gap: RP.gap.start, shown: RP.gap.start, rate: 0, hp: 1, max: 1, phase: 0, stage: 0, plates: Array(PLATES).fill(0), open: 0, marrow: false, jack: 1, arms: new Map(), lunge: 0 };
  T.F = F;
  let hudEl = null, failEl = null, env = null, time = 0;
  const S = () => ST.S;
  const busy = () => !!(ST.scene && ST.scene.playing());
  const view = () => ({ gap: F.gap, arms: [...F.arms.values()].map((v) => v.a), plates: F.plates, open: F.open > 0, eyeL: F.stage >= 2, smile: F.stage >= 3 });
  // where a shot from o along d ends (for the Blood Drive's tracer): the fight, or the map
  const rayEnd = (o, d, max) => { const w = raycast(o, d, max, MAPS[MAP.id].boxes), wt = w ? w.t : max, h = F.live ? rayFight(T.geo, view(), o, d, wt) : null; return h ? { t: h.t, part: h.part, at: h.at } : { t: wt, part: w ? 'wall' : '', at: o.map((x, i) => x + d[i] * wt) }; };
  const BD = makeBloodDrive({ rayEnd, free: () => F.marrow || !!(S().st.flags.jack_marrow_taken || S().st.flags.seen_mo_carry) });
  T.drive = BD;

  // ---------------------------------------------------------------- the tunnel (the train stands still: this goes past)
  function buildSet() {
    const g = new THREE.Group(), len = ARENA.z1 - ARENA.z0, mid = (ARENA.z0 + ARENA.z1) / 2;
    const bore = new THREE.Mesh(new THREE.CylinderGeometry(R, R, len, 32, 1, true), std(0x4a363a, { side: THREE.BackSide, roughness: 0.95, flatShading: true }));
    bore.rotation.x = Math.PI / 2; bore.position.set(0, CY, mid); g.add(bore);
    const ribs = new THREE.Group(), ribG = new THREE.TorusGeometry(R - 0.1, 0.16, 5, 32), ribM = std(0x2c2024);
    for (let z = ARENA.z0; z < ARENA.z1; z += 6) { const r = new THREE.Mesh(ribG, ribM); r.position.set(0, CY, z); ribs.add(r); }
    g.add(ribs);
    const sl = new THREE.InstancedMesh(new THREE.BoxGeometry(2.5, 0.12, 0.3), std(0x3a2c22), Math.ceil(len / 1.5)), m4 = new THREE.Matrix4();
    for (let i = 0; i < sl.count; i++) sl.setMatrixAt(i, m4.makeTranslation(0, 0.04, ARENA.z0 + i * 1.5));
    g.add(sl);
    // a string of weak bulbs along the wall, high on the right. the ones the mask has passed are out
    const bulbs = [], bG = new THREE.SphereGeometry(0.11, 8, 6), a = 1.05;
    for (let z = ARENA.z0; z < ARENA.z1; z += 12) { const m = new THREE.Mesh(bG, new THREE.MeshBasicMaterial({ color: 0xffc070 })); m.position.set((R - 0.3) * Math.cos(a), CY + (R - 0.3) * Math.sin(a), z); g.add(m); bulbs.push(m); }
    const cable = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, len), std(0x15100f)); cable.position.set((R - 0.2) * Math.cos(a), CY + (R - 0.2) * Math.sin(a), mid); g.add(cable);
    const lights = [0, 1, 2].map(() => { const l = new THREE.PointLight(0xffb060, 0, 15, 1.4); g.add(l); return l; });
    // the lamp on the back of the flatbed: what you see the face by
    const lamp = new THREE.SpotLight(0xfff0dd, 110, 95, 0.5, 0.7, 1); lamp.position.set(0.4, 2.7, 8); lamp.target.position.set(0, CY, -RP.gap.start); g.add(lamp, lamp.target);
    const work = new THREE.PointLight(0xffd9a0, 9, 16, 1.2); work.position.set(0, 4.6, 9); g.add(work); // a work light over the cars
    const knots = [0, 1, 2].map(() => { const l = new THREE.PointLight(0x4fd8ff, 0, 7, 1.5); g.add(l); return l; }); // the wrist knots' glow on what is near them: a fixed three, moved to the nearest knots (a light that comes and goes with each arm would rebuild every shader)
    G.scene.add(g);
    T.set = { g, ribs, sl, bulbs, lights, lamp, knots, off: 0 };
  }
  function stepSet(dt) {
    const s = T.set, v = T.fin && T.fin.t > 2.2 ? SPEED : busy() ? SPEED * 0.6 : SPEED;
    s.off = (s.off + v * dt) % 12;
    s.ribs.position.z = -(s.off % 6); s.sl.position.z = -(s.off % 1.5);
    const maskZ = F.live || T.fin ? -F.shown : -200, lit = [];
    for (let i = 0; i < s.bulbs.length; i++) {
      const b = s.bulbs[i], z = ARENA.z0 + i * 12 - s.off + (ARENA.z0 + i * 12 - s.off < ARENA.z0 ? ARENA.z1 - ARENA.z0 : 0);
      b.position.z = z;
      const d = z - maskZ, on = d > 3 || (d > 0.5 && Math.sin(time * 37 + i) > 0.2); // (it flickers as the face gets to it, then it is out)
      b.material.color.setHex(on ? 0xffc070 : 0x1a1210);
      if (on) lit.push(b.position);
    }
    lit.sort((p, q) => Math.abs(p.z - 4) - Math.abs(q.z - 4));
    s.lights.forEach((l, i) => { const p = lit[i]; l.intensity = p ? 22 : 0; if (p) l.position.set(p.x * 0.8, p.y - 0.5, p.z); });
    s.lamp.target.position.set(0, CY - 0.3, -Math.max(4, F.shown));
  }

  // ---------------------------------------------------------------- the mask (and the arm kit)
  function prep(root, k) {
    if (!env && G.renderer) { const pm = new THREE.PMREMGenerator(G.renderer); env = pm.fromScene(new RoomEnvironment(), 0.04).texture; pm.dispose(); }
    root.traverse((o) => { if (!o.isMesh) return; o.castShadow = false; o.receiveShadow = false; o.frustumCulled = false;
      for (const m of [].concat(o.material)) { // as glbkit.prepAuthored does: nearest textures, the studio reflection (dimmed: it is dark in here)
        for (const key of ['map', 'emissiveMap']) if (m[key]) { m[key].magFilter = THREE.NearestFilter; m[key].minFilter = THREE.NearestMipmapNearestFilter; m[key].anisotropy = 1; m[key].needsUpdate = true; }
        m.envMap = env; m.envMapIntensity = (m.metalness > 0.5 ? 0.5 : 0.14) * k; if (m.emissive && m.emissive.getHex() && m.emissiveIntensity > 0) m.toneMapped = false; } });
  }
  function load() {
    if (T.boss || T.loading) return; T.loading = true;
    const get = (u) => new Promise((ok, bad) => glbLoader().load(u, ok, undefined, bad));
    Promise.all([get('/models/story/revenue_protection.glb'), get('/models/story/rp_arm.glb'), fetch('/models/story/revenue_protection.parts.json').then((r) => (r.ok ? r.json() : null)).catch(() => null)]).then(([g, ga, parts]) => {
      prep(g.scene, 1); prep(ga.scene, 1);
      const N = {}, A = {}; g.scene.traverse((o) => { if (o.name) N[o.name] = o; }); ga.scene.traverse((o) => { if (o.name) A[o.name] = o; });
      const root = new THREE.Group(); root.add(g.scene); root.visible = false; G.scene.add(root);
      const glow = (name) => { let m = null; g.scene.traverse((o) => { if (o.isMesh) for (const x of [].concat(o.material)) if (x.name === name) m = x; }); return m; };
      // what an open eye housing shows: somewhere to put bolts
      const eyes = ['L', 'R'].map((k) => { const e = T.geo.eyes[k], m = new THREE.Mesh(new THREE.CircleGeometry(1, 20), new THREE.MeshBasicMaterial({ color: 0xff2a48, transparent: true, opacity: 0.9, toneMapped: false })); m.scale.set(e.h[0] * 0.92, e.h[1] * 0.92, 1); m.position.set(e.c[0], e.c[1], -0.12); m.visible = false; root.add(m); return m; });
      const red = new THREE.PointLight(0xff2030, 0, 16, 1.2); red.position.set(0, -1.6, 2.2); root.add(red);
      const cross = new THREE.Group(), cm = new THREE.MeshBasicMaterial({ color: 0xff1f3d, transparent: true, opacity: 0.95, toneMapped: false, depthWrite: false });
      for (const rot of [0, Math.PI / 2]) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.7, R * 2, 0.3), cm); b.rotation.z = rot; cross.add(b); }
      cross.position.z = 0.9; cross.visible = false; root.add(cross);
      T.parts = parts; T.geo = geoFrom(parts);
      T.boss = { root, N, A, eyes, red, cross, cm, inspGlow: glow('rp_inspector_glow'), eyeGlow: glow('rp_eye_glow'), hidden: new Set(parts ? parts.parts.filter((p) => p.hidden).map((p) => p.name) : []), debris: [], haul: [] };
      for (const nm of T.boss.hidden) if (N[nm]) N[nm].visible = false;
      for (const [sock, wa] of [[7, 3.5], [10, -0.36]]) T.boss.haul.push(newArm({ id: 'h' + sock, k: 'haul', sock, mouth: 0, st: 'grip', t: 0, dur: 0, tgt: [0, 0, 0], wa, hp: 1, max: 1 }, true)); // two arms on the walls that do the hauling (not targets: no knot)
      applyMask(); T.loading = false;
    }).catch((e) => { console.warn('revenue protection model', e); T.loading = false; T.loadErr = true; });
  }
  const pn = (i, suf = '') => `plate_${String(i).padStart(2, '0')}${suf}`;
  // what the room's state says is on the face right now
  function applyMask() {
    const b = T.boss; if (!b) return; const N = b.N, st = F.stage, show = (n, v) => { if (N[n]) N[n].visible = v; };
    for (let i = 0; i < PLATES; i++) {
      const p = F.plates[i], split = SPLIT.includes(i) && st >= 2;
      show(pn(i), p === 0 && !split); show(pn(i, '_crazed'), p === 1 && !(split && st >= 3));
      show(pn(i, '_up'), split && p !== 2 && (p === 0 || st >= 3)); show(pn(i, '_low'), split && p === 0 && st < 3);
    }
    show('eye_L', st < 2); show('eye_L_blown', st >= 2); show('eye_cluster', st >= 2); show('frame_low', st < 3); show('anchors', st < 3); show('mass_lod', false);
  }
  // a piece that comes off: a copy of it falls onto the track and is left behind
  function drop(name, o = {}) {
    const b = T.boss, n = b && b.N[name]; if (!n) return;
    n.updateWorldMatrix(true, false);
    const c = n.clone(); c.visible = true; n.matrixWorld.decompose(c.position, c.quaternion, c.scale); G.scene.add(c);
    b.debris.push({ m: c, v: [(Math.random() - 0.5) * 2, 1 + Math.random() * 2, 1.5 + Math.random() * 2], w: [(Math.random() - 0.5) * 3, (Math.random() - 0.5) * 2, (Math.random() - 0.5) * 3], t: 0, life: o.life || 3, hit: false, name });
  }
  function stepDebris(dt) {
    const b = T.boss; if (!b) return;
    for (let i = b.debris.length - 1; i >= 0; i--) {
      const d = b.debris[i]; d.t += dt; d.v[1] -= 16 * dt;
      d.m.position.x += d.v[0] * dt; d.m.position.y += d.v[1] * dt; d.m.position.z += d.v[2] * dt;
      d.m.rotation.x += d.w[0] * dt; d.m.rotation.y += d.w[1] * dt; d.m.rotation.z += d.w[2] * dt;
      if (!d.hit && d.m.position.y < 0.4) { d.hit = true; d.v = [d.v[0] * 0.3, 2.5, -SPEED * 0.8]; d.w = d.w.map((x) => x * 2); const p = [d.m.position.x, 0.2, d.m.position.z]; fx.sparks(p, [0, 0, -1], 14, true); fx.dust(p, 6); if (/plate|frame/.test(d.name)) sfx.rpPlate(p, true); }
      if (d.hit && d.m.position.y < 0.15) { d.m.position.y = 0.15; d.v[1] = 0; }
      if (d.t > d.life) { G.scene.remove(d.m); b.debris.splice(i, 1); }
    }
  }

  // ---------------------------------------------------------------- arms
  function newArm(a, decor) {
    const b = T.boss, g = new THREE.Group(), v = { a: { ...a, tgt: a.tgt.slice() }, g, segs: [], decor: !!decor, flash: 0, cutDone: false, sideT: 0 };
    if (!b) return v;
    v.hand = b.A.arm_hand.clone(true); v.joints = []; v.hand.traverse((o) => { if (/^f\d_[abc]$/.test(o.name)) v.joints.push(o); }); g.add(v.hand);
    v.stump = b.A.arm_stump.clone(true); v.stump.visible = false; g.add(v.stump);
    if (!decor) { // the wrist: lanyards and ID cards wound into a ball, lit from inside. it has to stand out in the dark
      v.knot = b.A.arm_knot.clone(true);
      v.knot.traverse((o) => { if (o.isMesh && [].concat(o.material).some((m) => m.name === 'rp_knot_glow')) { o.material = Array.isArray(o.material) ? o.material.map((m) => (m.name === 'rp_knot_glow' ? (v.glow = m.clone()) : m)) : (v.glow = o.material.clone()); } });
      v.halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex(), color: 0x4fd8ff, transparent: true, opacity: 0.85, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); v.halo.scale.setScalar(3.2);
      g.add(v.knot, v.halo);
    }
    G.scene.add(g);
    return v;
  }
  let _halo = null;
  function haloTex() {
    if (_halo) return _halo;
    const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'), gr = x.createRadialGradient(32, 32, 2, 32, 32, 32);
    gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = gr; x.fillRect(0, 0, 64, 64);
    _halo = new THREE.CanvasTexture(c); return _halo;
  }
  const _p = new THREE.Vector3(), _q = new THREE.Vector3();
  function poseArm(v, dt, gap) {
    const a = v.a, b = T.boss; if (!b || !v.hand) return;
    if (a.k === 'sweep') a.tgt[2] = sweepZ(a);
    if (a.k === 'snatch' && (a.st === 'reach' || a.st === 'hold') && ME.alive) a.tgt = [ME.pos[0], ME.pos[1] + RP.snatch.up, ME.pos[2] - 0.2];
    const P = armPose(T.geo, a, gap, v.decor ? v.ext : armExt(a)), pts = P.pts, J = [pts[0]];
    // joints every 1.5 m along the path: each length looks at the next joint
    let need = SEG, i = 1, cur = pts[0];
    while (i < pts.length && J.length < 34) {
      const q = pts[i], l = Math.hypot(q[0] - cur[0], q[1] - cur[1], q[2] - cur[2]);
      if (l < need) { need -= l; cur = q; i++; continue; }
      const k = need / l; cur = [cur[0] + (q[0] - cur[0]) * k, cur[1] + (q[1] - cur[1]) * k, cur[2] + (q[2] - cur[2]) * k]; J.push(cur); need = SEG;
    }
    if (need < SEG - 0.05) J.push(P.wrist);
    const n = J.length - 1;
    while (v.segs.length < n) { const s = b.A.arm_seg.clone(true); v.g.add(s); v.segs.push(s); }
    for (let k = 0; k < v.segs.length; k++) {
      const s = v.segs[k]; s.visible = k < n; if (k >= n) continue;
      const A0 = J[k], B0 = J[k + 1], rx = A0[0], ry = A0[1] - CY, rl = Math.hypot(rx, ry) || 1;
      s.position.set(A0[0], A0[1], A0[2]); s.up.set(rx / rl, ry / rl, 0); s.lookAt(_p.set(B0[0], B0[1], B0[2])); // (up = out from the bore's axis: the flat side lies on the wall)
      s.scale.set(1, a.mouth ? 1 : k < 2 ? 0.35 : k < 4 ? 0.35 + 0.325 * (k - 1) : 1, clamp(Math.hypot(B0[0] - A0[0], B0[1] - A0[1], B0[2] - A0[2]) / SEG, 0.05, 1.05)); // the first lengths are flat: a whole rope doesn't fit past the rim
    }
    const w = P.wrist, cut = a.st === 'cut', d = a.gp && a.st !== 'back' ? [a.gp[0] - w[0], a.gp[1] - w[1], a.gp[2] - w[2]] : P.dir, dl = Math.hypot(d[0], d[1], d[2]) || 1;
    v.hand.visible = !cut; v.stump.visible = cut;
    const tip = _q.set(w[0] + d[0] / dl, w[1] + d[1] / dl, w[2] + d[2] / dl);
    if (cut) { v.stump.position.set(w[0], w[1], w[2]); v.stump.up.set(0, 1, 0); v.stump.lookAt(_p.set(w[0] + P.dir[0], w[1] + P.dir[1], w[2] + P.dir[2])); v.stump.scale.setScalar(1.15); }
    else {
      v.hand.position.set(w[0] + d[0] / dl * 0.4, w[1] + d[1] / dl * 0.4, w[2] + d[2] / dl * 0.4); v.hand.up.set(0, Math.abs(d[1] / dl) > 0.9 ? 0 : 1, Math.abs(d[1] / dl) > 0.9 ? 1 : 0); v.hand.lookAt(tip);
      const want = a.st === 'grip' ? 0.95 : a.st === 'hold' ? 0.85 : a.st === 'sweep' ? 0.3 : 0.1 + 0.08 * Math.sin(time * 5 + (v.a.sock || 0));
      v.curl = (v.curl ?? 0.1) + (want - (v.curl ?? 0.1)) * Math.min(1, dt * 9);
      for (const j of v.joints) j.rotation.x = v.curl * (j.name[1] === '0' ? 0.75 : 1);
    }
    if (v.knot) {
      const live = armLive(a); v.flash = Math.max(0, v.flash - dt * 5);
      v.knot.visible = v.halo.visible = live;
      v.knot.position.set(w[0], w[1], w[2]); v.halo.position.set(w[0], w[1], w[2]);
      const pulse = 0.5 + 0.5 * Math.sin(time * 6 + a.id), hurt = 1 - clamp(a.hp / a.max, 0, 1);
      if (v.glow) v.glow.emissiveIntensity = 2.4 + pulse * 1.2 + v.flash * 6;
      v.halo.scale.setScalar(3 + pulse * 0.7 + v.flash * 1.8); v.knot.scale.setScalar(1.2); v.halo.material.color.setHex(v.flash > 0.3 ? 0xffffff : hurt > 0.6 ? 0xff6a9a : 0x4fd8ff);
      v.knot.rotation.y += dt * (1 + hurt * 6);
    }
    v.wrist = w; v.dir = P.dir;
  }
  function freeArm(v) { G.scene.remove(v.g); if (v.glow) v.glow.dispose(); if (v.halo) v.halo.material.dispose(); }
  function clearArms() { for (const v of F.arms.values()) freeArm(v); F.arms.clear(); }
  function onArm(m) {
    if (!fin(m.id)) return;
    let v = F.arms.get(m.id);
    if (m.st === 'gone') { if (v) { freeArm(v); F.arms.delete(m.id); } return; }
    if (!v3(m.tgt) || typeof m.k !== 'string' || !fin(m.sock)) return;
    const a = { id: m.id, k: m.k, sock: clamp(m.sock | 0, 0, m.mouth ? 3 : 11), mouth: m.mouth ? 1 : 0, st: String(m.st), t: 0, dur: fin(m.dur) ? m.dur : 0, tgt: m.tgt.slice(), hi: !!m.hi, side: m.side || 0, hp: fin(m.hp) ? m.hp : 1, max: fin(m.max) && m.max > 0 ? m.max : 1, ...(fin(m.wa) ? { wa: m.wa } : {}), ...(v3(m.gp) ? { gp: m.gp.slice() } : {}) };
    if (!v) { v = newArm(a); F.arms.set(m.id, v); if (a.k === 'sweep') hud.msg(a.hi ? 'HEAD HEIGHT. GET DOWN.' : 'KNEE HEIGHT. JUMP.', 1.3, 'reverse'); }
    else { const was = v.a.st; v.a = a; if (a.st === 'cut' && was !== 'cut') severed(v, m); if (a.st === 'grip' && was !== 'grip') { sfx.rpHaul(v.wrist, 1.4); G.shake = Math.max(G.shake, 0.2); } if (a.st === 'hold' && was !== 'hold') hud.msg('IT HAS YOU. SHOOT THE WRIST.', 2, 'reverse'); }
  }
  function severed(v, m) {
    const w = v.wrist || [0, 2, 0];
    sfx.rpSever(w); fx.blood(w, [0, 1, 0], 40, 0); fx.sparks(w, [0, 0, -1], 18, true); G.shake = Math.max(G.shake, 0.7); T.hitstop = 0.09;
    if (T.boss && v.hand) { v.hand.updateWorldMatrix(true, false); const c = v.hand.clone(true); v.hand.matrixWorld.decompose(c.position, c.quaternion, c.scale); G.scene.add(c); T.boss.debris.push({ m: c, v: [0, 2, 1], w: [2, 1, 3], t: 0, life: 2.6, hit: false, name: 'hand' }); } // the hand drops onto the track
    if (fin(m.blood) && m.blood > 0) hud.msg(`SEVERED. +${m.blood} BLOOD`, 1, 'brag'); else hud.msg('SEVERED', 0.8, 'brag');
  }

  // ---------------------------------------------------------------- the HUD
  function showHud() {
    if (!hudEl) {
      css(); hudEl = el('div', 'hidden'); hudEl.id = 'rpGap';
      const n = el('div', 'n'); n.append(el('b', '', '30'), el('i', '', 'm'));
      const tr = el('div', 'tr'); tr.append(el('u'));
      const jk = el('div', 'jk'); const bar = el('s'); bar.append(el('u')); jk.append(el('span', '', 'JACK'), bar);
      hudEl.append(el('div', 'l', 'THE GAP'), n, tr, jk, el('div', 'bl'), el('div', 'vx')); document.body.appendChild(hudEl);
      failEl = el('div', 'hidden'); failEl.id = 'rpFail'; for (let i = 0; i < 5; i++) failEl.append(el('i')); failEl.append(el('p', '', 'fare evaded. briefly.')); document.body.appendChild(failEl);
    }
    const on = T.on && F.live && !busy() && !T.fin;
    hudEl.classList.toggle('hidden', !on);
    if (!on) return;
    hudEl.querySelector('b').textContent = F.shown < 9.95 ? F.shown.toFixed(1) : String(Math.round(F.shown));
    hudEl.querySelector('.tr u').style.width = `${clamp(F.shown / RP.gap.max, 0, 1) * 100}%`;
    hudEl.classList.toggle('near', F.shown < 8); hudEl.classList.toggle('open', F.rate > 0);
    const jk = hudEl.querySelector('.jk'); jk.classList.toggle('hidden', F.phase !== 0); jk.querySelector('u').style.width = `${clamp(F.jack, 0, 1) * 100}%`;
    const bl = hudEl.querySelector('.bl'), free = BD.free();
    bl.textContent = free ? 'running on jack' : ME.hp - 1 < 2 ? 'thin blood' : `${Math.floor((ME.hp - 1) / 2)} bolts of blood left`;
    const vx = hudEl.querySelector('.vx'); vx.textContent = T.lineT > time ? T.line : '';
  }
  const say = (line, dur = 4) => { if (typeof line === 'string' && line) { T.line = line.slice(0, 60); T.lineT = time + dur; } };

  // ---------------------------------------------------------------- the referee's events
  function setState(m) {
    if (fin(m.gap)) { F.gap = m.gap; F.shown = F.live ? F.shown : m.gap; }
    if (fin(m.hp)) F.hp = m.hp; if (fin(m.max) && m.max > 0) F.max = m.max;
    if (fin(m.phase)) F.phase = m.phase; if (fin(m.stage)) F.stage = m.stage;
    if (Array.isArray(m.plates) && m.plates.length === PLATES) F.plates = m.plates.map((x) => (x === 1 || x === 2 ? x : 0));
    F.open = fin(m.open) ? m.open : 0; F.marrow = !!m.marrow; F.jack = fin(m.jack) ? m.jack : 0; F.rate = 0; F.lunge = 0;
    clearArms(); for (const a of Array.isArray(m.arms) ? m.arms.slice(0, 16) : []) onArm(a);
    F.live = true; T.fin = null; T.failT = 0; if (failEl) { failEl.classList.remove('on'); failEl.classList.add('hidden'); }
    if (T.boss) { T.boss.root.visible = true; unbreak(); applyMask(); }
    if (T.said !== F.phase) { T.said = F.phase; hud.msg(['TICKETS, PLEASE', 'PENALTY FARE', 'END OF THE LINE'][F.phase] || '', 2.6, 'brag'); if (F.phase === 0) say('tickets, please.', 5); }
  }
  // back in one piece (a retry): the face on its bolts, the plug whole
  function unbreak() {
    const b = T.boss; if (!b) return; const N = b.N;
    if (N.mask) { N.mask.position.set(0, 0, 0); N.mask.quaternion.identity(); N.mask.scale.set(1, 1, 1); }
    for (const k of ['mass_ne', 'mass_nw', 'mass_sw', 'mass_se']) if (N[k]) { N[k].position.set(0, 0, 0); N[k].rotation.set(0, 0, 0); }
    b.cross.visible = false;
  }
  T.combat = (ev) => {
    if (!ev || ev.boss !== RP_ID) return false;
    const at = v3(ev.at) ? ev.at : null;
    switch (ev.type) {
      case 'state': setState(ev); break;
      case 'reset': hud.msg('AGAIN.', 1.4, 'brag'); break;
      case 'gap': if (fin(ev.gap)) F.gap = ev.gap; F.rate = fin(ev.rate) ? ev.rate : 0; if (fin(ev.jack)) F.jack = ev.jack; break;
      case 'arm': onArm(ev); break;
      case 'arms': clearArms(); break;
      case 'hit': {
        if (fin(ev.hp)) F.hp = ev.hp;
        const v = fin(ev.arm) ? F.arms.get(ev.arm) : null;
        if (v) { v.flash = 1; v.a.hp = Math.max(0, v.a.hp - (fin(ev.dmg) ? ev.dmg : 0)); if (ev.part === 'knot') sfx.rpKnot(v.wrist); }
        else if (ev.crit && T.boss) { T.boss.redK = 1; G.shake = Math.max(G.shake, 0.12); }
        break;
      }
      case 'shrug': if (at) { fx.sparks(at, [0, 0, 1], 8); sfx.rpTink(at); } break;
      case 'bloom': if (at) bloom(at); break;
      case 'plate': if (fin(ev.i) && ev.i >= 0 && ev.i < PLATES) { const i = ev.i | 0, was = F.plates[i]; F.plates[i] = ev.st === 2 ? 2 : ev.st === 1 ? 1 : 0;
        if (T.boss && F.plates[i] === 2 && was !== 2) drop(T.boss.N[pn(i, '_crazed')] ? pn(i, '_crazed') : pn(i)); // it falls away and smashes on the track; the hole stays
        else if (T.boss && F.plates[i] === 1) { T.boss.root.getWorldPosition(_p); sfx.rpPlate([_p.x, _p.y, _p.z], false); }
        applyMask(); } break;
      case 'stage': if (fin(ev.stage)) { const was = F.stage; F.stage = clamp(ev.stage | 0, 0, 3); stageFx(was, F.stage); applyMask(); } break;
      case 'flinch': F.open = fin(ev.open) ? ev.open : RP.flinch.open; hud.msg('IT FLINCHED. THE EYES. NOW.', 2.2, 'brag'); sfx.rpFlinch(); G.shake = Math.max(G.shake, 0.6); if (T.boss) T.boss.flinch = 1; break;
      case 'swept': hud.msg(ev.hi ? 'SWEPT. (SLIDE UNDER THAT ONE.)' : 'SWEPT. (JUMP THAT ONE.)', 1.6, 'reverse'); G.shake = 1; break;
      case 'snatched': hud.msg('TAKEN. THE GAP WENT WITH YOU.', 2, 'reverse'); G.shake = 1; break;
      case 'lunge': if (ev.st === 'tell') { F.lunge = fin(ev.dur) ? ev.dur : RP.lunge.tell; hud.msg('IT REARS. OFF THE WAGON.', 1.5, 'reverse'); sfx.rpLunge(); } else { F.lunge = 0; G.shake = 1; if (T.boss) T.boss.bite = 1; if (ev.bit) hud.msg('BITTEN', 1.2, 'reverse'); } break;
      case 'bag': hud.msg(`SOUP BAG, RELABELLED. +${fin(ev.hp) ? ev.hp : RP.bag.hp} BLOOD`, 1.4, 'brag'); break;
      case 'off': hud.msg('MIND THE GAP', 1.6, 'reverse'); break;
      case 'fail': T.failT = time; clearArms(); if (failEl) { failEl.classList.remove('hidden'); requestAnimationFrame(() => failEl.classList.add('on')); } sfx.rpCaught(); break;
      case 'phase': {
        if (fin(ev.phase)) F.phase = ev.phase;
        if (ev.invuln) {
          clearArms();
          if (ev.phase === 1) { // the scripted end of phase 1: the quest's next step plays the middle scene (by hand on a bare train); the room holds through it
            const o = objective();
            if (o && o.step === 'hold') S().run(['flag:rp_phase1_done']); else if (S().defs.scenes.mo_carry_the_bit_that_works) playScene('mo_carry_the_bit_that_works');
          }
        } else { T.said = F.phase; hud.msg(typeof ev.name === 'string' ? ev.name.slice(0, 40) : '', 2.8, 'brag'); if (F.phase >= 1) F.marrow = true; say(S().defs.bosses && S().defs.bosses[RP_ID] && S().defs.bosses[RP_ID].phases[F.phase] ? S().defs.bosses[RP_ID].phases[F.phase].line : '', 5); }
        break;
      }
      case 'kill': if (ev.defeat) { finish(); S().emit({ type: 'killBoss', boss: RP_ID }); } break;
    }
    return true;
  };
  function stageFx(was, st) {
    const b = T.boss; if (st <= was) return;
    if (st >= 1 && was < 1) say('excuse me. excuse me.', 3);
    if (st >= 2 && was < 2) { hud.msg('THE LEFT EYE', 2, 'brag'); say('is this seat taken', 5); G.shake = 1; T.hitstop = 0.08; if (b) { drop('eye_L'); b.root.getWorldPosition(_p); const p = [_p.x + T.geo.eyes.L.c[0], _p.y + T.geo.eyes.L.c[1], _p.z + 0.4]; fx.sparks(p, [0, 0, 1], 30, true); fx.blood(p, [0, 0, 1], 30, 0); sfx.rpSever(p); } }
    if (st >= 3 && was < 3) { hud.msg('THE SMILE', 2.2, 'brag'); say('i\'m going to be late', 5); G.shake = 1; T.hitstop = 0.1; if (b) { for (const i of SPLIT) if (F.plates[i] !== 2) drop(pn(i, '_low')); drop('frame_low'); b.root.getWorldPosition(_p); sfx.rpPlate([_p.x, 1, _p.z], true); } }
  }
  // a blood cross blooms where the sixth bolt went in
  function bloom(at) {
    for (const d of [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]]) fx.tracer(at, [at[0] + d[0] * 1.5, at[1] + d[1] * 1.5, at[2] + d[2] * 1.5], 0xff1f3d, 0.16, 0.3);
    fx.blood(at, [0, 0, 1], 16, 0); sfx.bcErupt && sfx.bcErupt(at); G.shake = Math.max(G.shake, 0.25);
    if (T.boss) T.boss.redK = 1;
  }
  // BLOOD CROSSED: one cross out of the middle of it until it touches the tunnel on all four sides. the face falls
  // forward flat on the track, the plug comes apart along the cross into four heaps, and the train leaves it behind
  function finish() {
    if (T.fin) return;
    T.fin = { t: 0, thud: false, click: false }; clearArms(); F.rate = 0;
    hud.msg('BLOOD CROSSED', 3.6, 'brag'); sfx.rpCross(); G.shake = 1; T.hitstop = 0.22; say('*click.*', 6);
  }
  function stepFinish(dt) {
    const f = T.fin, b = T.boss; f.t += dt; if (!b) return;
    const N = b.N, k = ss(f.t / 0.9);
    b.cross.visible = f.t < 3.4; b.cross.scale.set(0.2 + k * 0.8, k, 1); b.cm.opacity = f.t < 2.2 ? 0.95 : Math.max(0, 0.95 * (1 - (f.t - 2.2) / 1.2));
    b.red.intensity = 60 * Math.max(0, 1 - f.t / 3.5);
    const fall = clamp((f.t - 0.9) / 1.1, 0, 1); // the last bolt goes: the face falls forward flat
    if (N.mask) pivot(N.mask, [0, -CY + 0.1, 0.3], fall * fall * (Math.PI / 2), 0);
    if (fall >= 1 && !f.thud) { f.thud = true; G.shake = 1; b.root.getWorldPosition(_p); const p = [_p.x, 0.2, _p.z + 4]; fx.dust(p, 20); fx.sparks(p, [0, 0, 1], 24, true); sfx.rpPlate(p, true); }
    const apart = ss((f.t - 1.0) / 1.8), slump = ss((f.t - 1.5) / 2.2); // ...and what was behind it lets go, along the cross
    for (const [nm, sx, sy] of [['mass_ne', 1, 1], ['mass_nw', -1, 1], ['mass_sw', -1, -1], ['mass_se', 1, -1]]) if (N[nm]) { N[nm].position.set(sx * 0.7 * apart, sy * 0.35 * apart - (sy > 0 ? 2.6 : 0.5) * slump, -0.6 * slump); N[nm].rotation.set(sy > 0 ? 0.3 * slump : 0, 0, -sx * (sy > 0 ? 0.42 : 0.12) * slump); }
    if (f.t > 3.2 && !f.click) { f.click = true; sfx.rpClick(); } // in the middle of the wreck, the Inspector. he clicks it once
    if (f.t > 2.4) F.shown += (f.t - 2.4) * 5 * dt + 2 * dt; // nothing is hauling any more: the train leaves it behind
    if (F.shown > 95) { b.root.visible = false; F.live = false; T.fin.gone = true; }
  }

  // ---------------------------------------------------------------- every frame (boot.js, while a story world is on)
  T.tick = (dt) => {
    const on = !!(G.joined && G.mode === 'story' && MAP.id === TRAIN.id);
    if (on !== T.on) { T.on = on; if (on) { buildSet(); load(); } else leave(); }
    if (!on) { BD.tick(dt, false); return; }
    if (!T.boss) load();
    const held = busy(), sdt = held ? 0 : dt; // (a scene holds the room: hold the picture of it too)
    time += dt; T.hitstop = Math.max(0, T.hitstop - dt);
    stepSet(dt);
    F.gap = clamp(F.gap + F.rate * sdt, 0, RP.gap.max); F.open = Math.max(0, F.open - sdt); F.lunge = Math.max(0, F.lunge - sdt);
    if (!T.fin) F.shown += (F.gap - F.shown) * Math.min(1, dt * 6);
    const b = T.boss;
    if (b) {
      b.root.visible = (F.live || !!T.fin) && !(T.fin && T.fin.gone);
      // the haul: its two wall arms reach, grip and drag, and the face lurches forward a little on each drag
      const cyc = (time * 0.42) % 1, drag = cyc > 0.55 ? ss((cyc - 0.55) / 0.45) : 0, lurch = T.fin ? 0 : (cyc > 0.55 ? drag : 1 - ss(cyc / 0.55)) * 0.45 - 0.2;
      const rear = F.lunge > 0 ? -1.6 * ss(1 - F.lunge / RP.lunge.tell) : 0; b.bite = Math.max(0, (b.bite || 0) - dt * 2.5);
      const z = -F.shown + lurch + rear + (b.bite || 0) * 1.2;
      b.root.position.set(0, CY, z); b.root.rotation.z = T.fin ? 0 : Math.sin(time * 0.9) * 0.012 + (b.flinch || 0) * 0.05 * Math.sin(time * 40);
      b.flinch = Math.max(0, (b.flinch || 0) - dt * 1.4); b.redK = Math.max(0, (b.redK || 0) - dt * 3);
      if (cyc > 0.55 && !b.hauled && F.live && !T.fin) { b.hauled = true; sfx.rpHaul([0, CY, z], clamp(1.4 - F.shown / 30, 0.3, 1.2)); } if (cyc < 0.5) b.hauled = false;
      for (const [i, v] of b.haul.entries()) { const c2 = (cyc + i * 0.5) % 1, wa = v.a.wa; v.ext = T.fin ? Math.max(0.03, 1 - T.fin.t / 1.5) : c2 < 0.55 ? 0.5 + 0.5 * ss(c2 / 0.55) : 1 - 0.5 * ss((c2 - 0.55) / 0.45); v.a.st = c2 > 0.5 && !T.fin ? 'grip' : 'reach'; v.a.tgt = [4.05 * Math.cos(wa), CY + 4.05 * Math.sin(wa), -F.shown + 7]; v.g.visible = b.root.visible; poseArm(v, dt, F.shown - lurch); }
      // the eye housings swing open on a flinch; behind the blown left one, eyes
      const open = F.open > 0 && !T.fin ? 1 : 0; b.openK = (b.openK || 0) + (open - (b.openK || 0)) * Math.min(1, dt * 7);
      if (b.N.eye_L) b.N.eye_L.rotation.y = 1.25 * b.openK; if (b.N.eye_R) b.N.eye_R.rotation.y = -1.25 * b.openK;
      b.eyes[0].visible = b.openK > 0.2 && F.stage < 2; b.eyes[1].visible = b.openK > 0.2; for (const e of b.eyes) e.material.opacity = 0.65 + 0.3 * Math.sin(time * 14);
      if (F.stage >= 2 && b.N.eye_cluster) for (const c of b.N.eye_cluster.children) c.lookAt(_p.set(ME.pos[0], ME.pos[1] + 1.5, ME.pos[2]));
      if (b.eyeGlow) b.eyeGlow.emissiveIntensity = 1.5 + Math.sin(time * 3) * 0.5;
      // phase 3: hanging off one bolt, swinging; the Inspector lit from inside, punching a ticket that isn't there
      if (!T.fin && b.N.mask) { const hang = F.phase >= 2 && T.parts && T.parts.stages && T.parts.stages[3] && T.parts.stages[3].hang; if (hang && v3(hang.pivot)) pivot(b.N.mask, hang.pivot, -0.07, -0.06 + Math.sin(time * 1.3) * 0.035); }
      if (b.inspGlow) b.inspGlow.emissiveIntensity = (F.phase >= 2 ? 3.2 : 1.2) + Math.sin(time * 5) * 0.8;
      if (b.N.insp_foreR) b.N.insp_foreR.rotation.x = Math.max(0, Math.sin(time * 4.2)) * 0.5; if (b.N.insp_punch_lever) b.N.insp_punch_lever.rotation.x = Math.max(0, Math.sin(time * 4.2)) > 0.8 ? 0.3 : 0;
      if (!T.fin) b.red.intensity = (F.stage >= 3 ? 14 : 5) + b.redK * 40 + (F.phase >= 2 ? 6 * Math.sin(time * 5) : 0);
      // sparks where the rim scrapes the brickwork, all the way round
      if (F.live && !T.fin && !held && (b.sparkT = (b.sparkT || 0) - dt) < 0) { b.sparkT = 0.05 + Math.random() * 0.12; const a = -0.6 + Math.random() * (Math.PI + 1.2); fx.sparks([R * 0.97 * Math.cos(a), CY + R * 0.97 * Math.sin(a), z + 0.3], [0, 0, 1], 5 + (Math.random() * 6 | 0), Math.random() < 0.3); }
      if (T.fin) stepFinish(dt);
      stepDebris(dt);
    }
    for (const v of F.arms.values()) { v.a.t += sdt; if (b && !v.hand) { freeArm(v); const nv = newArm(v.a); Object.assign(v, nv); } poseArm(v, dt, F.shown); } // (an arm that came before the model did gets its body now)
    { const ks = [...F.arms.values()].filter((v) => v.wrist && armLive(v.a)).sort((p, q) => Math.hypot(p.wrist[0] - ME.pos[0], p.wrist[2] - ME.pos[2]) - Math.hypot(q.wrist[0] - ME.pos[0], q.wrist[2] - ME.pos[2])); T.set.knots.forEach((l, i) => { const v = ks[i]; l.intensity = v ? 9 + v.flash * 12 : 0; if (v) l.position.set(v.wrist[0], v.wrist[1], v.wrist[2]); }); }
    showHud();
    BD.tick(dt, ME.alive && !held && !(T.failT && !F.live));
  };
  function leave() {
    clearArms(); F.live = false; T.fin = null; T.said = -1; T.auto = false; T.back = null;
    if (T.set) { G.scene.remove(T.set.g); T.set = null; }
    if (T.boss) { G.scene.remove(T.boss.root); for (const d of T.boss.debris) G.scene.remove(d.m); for (const v of T.boss.haul) freeArm(v); T.boss = null; }
    if (hudEl) hudEl.classList.add('hidden'); if (failEl) { failEl.classList.remove('on'); failEl.classList.add('hidden'); }
  }
  // a real hit-stop on a sever (story main.js multiplies the game's dt by this)
  T.timeScale = () => (T.hitstop > 0 ? 0.06 : 1);
  // what your other guns can hit (bossref.js gives the room's bot these boxes): the face and every arm. the room judges the shot
  T.boxes = () => {
    if (!F.live) return null;
    const out = [{ min: [-T.geo.maskR, CY - T.geo.maskR, -F.gap - 0.4], max: [T.geo.maskR, CY + T.geo.maskR, -F.gap + 0.4] }], bx = (p, r) => out.push({ min: [p[0] - r, p[1] - r, p[2] - r], max: [p[0] + r, p[1] + r, p[2] + r] });
    for (const v of F.arms.values()) { if (!armLive(v.a)) continue; const P = armPose(T.geo, v.a, F.gap); bx(P.wrist, 0.56); for (const p of P.pts) bx(p, 0.4); }
    return out;
  };

  // ---------------------------------------------------------------- the quest: m06's fight steps
  const objective = () => { const os = S().quests.objectives ? S().quests.objectives() : []; return os.find((x) => x.quest === RP_QUEST) || null; };
  const spawn = () => { if (G.story && G.story.send) G.story.send('spawn', { kind: RP_ID, id: RP_ID, at: [0, CY, -RP.gap.start] }); };
  T.spawn = spawn;
  T.frame = () => {
    const o = objective(), step = o ? o.step : '', now = performance.now();
    if (step !== T.step) { T.step = step; T.stepT = now; }
    const fight = step === 'hold' || step === 'break';
    if (fight && G.joined && G.mode === 'story' && MAP.id !== TRAIN.id && G.story.travel && !T.going && !busy()) { T.going = G.story.travel(TRAIN.id); return; } // the fight is on the train: go there (story/main.js remembers where from)
    if (!T.on) return;
    T.going = false;
    if ((fight || (TRAINQ && !o && !T.auto)) && !F.live && !T.fin && now - T.spawnT > 2500 && !busy()) { T.spawnT = now; T.auto = true; spawn(); } // (the room has one boss at a time: asking twice is nothing)
    // the middle scene's [FIRE] and [TAKE] are not built yet (the scene engine cuts a "moment" at 3 s): once it has
    // played, the step is given its flags here so the fight can go on. stands in for the two buttons
    if (step === 'jack' && !busy() && now - T.stepT > 1500) S().run(['flag:jack_fired', 'flag:jack_marrow_taken', 'flag:seen_mo_carry']);
    // done with the mission (or it was never on) after a trip here: back to where you came from
    if (!o && !TRAINQ && !busy() && G.story.travelBack && (!F.live || (T.fin && T.fin.t > 6)) && now - T.stepT > 4000 && !T.back) T.back = G.story.travelBack() || 'nowhere';
  };
  if (typeof window !== 'undefined') window.JF_TRAIN = T; // (tests and screenshots stage it from here)
  return T;
}
