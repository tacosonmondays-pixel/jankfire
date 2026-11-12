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
//   - the train and the tunnel themselves are box stand-ins built here; trainset.js swaps their looks for the Blender train
//     and tunnel kit when those files land (?trainbox=1 keeps the boxes)
// nothing here changes the fight: turn it off and it is still fought, just in the dark
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { G } from '../ctx.js';
import { hud } from '../hud.js';
import { fx } from '../fx.js';
import { sfx } from '../audio.js';
import { ME } from '../player.js';
import { MAP, MAPS, BOXES } from '/shared/map.js';
import { glbLoader, AUTHORED } from '../glbkit.js';
import { spawnActor, despawnActor, actors } from './actors.js';
import { raycast } from '/shared/physics.js';
import { TRAIN, ARENA, RP, CARS, CAR, HW, COVER, CREW, GEO0, geoFrom, armPose, armExt, armLive, sweepZ, sweepY, rayFight, SPLIT, PLATES, ss, stranded } from '/shared/story/train.js';
import { makeBloodDrive } from './blooddrive.js';
import { makeHitStop } from './hitstop.js';
import { makeTrainSet } from './trainset.js';
import { PJ } from './palletjack.js'; // Jack's own clips and damage states (pj_*: the middle scene)
import { PLACES } from '/shared/city/slice.js'; // where the Loop comes back out into the world (commute:tunnel_mouth, once the world has it)
import { handFit, haulHand, haulPath, newHaul, stepHaul, armJoints, flatK, HAUL } from './armgrip.js';

export const RP_ID = 'revenue_protection_1', RP_QUEST = 'm06_tickets_please';
const SPEED = 12, SEG = 1.5, R = ARENA.boreR, CY = ARENA.cy; // m/s the tunnel goes past · one arm_seg · the bore
const fin = Number.isFinite, clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const v3 = (a) => Array.isArray(a) && a.length === 3 && a.every(fin);
const BORE = { R, cy: CY }; // what the arms are kept inside (armgrip.js)
const TRAINQ = /[?&]train=1\b/.test(location.search); // ?story=1&storytest=1&train=1: straight onto the train, the fight starts by itself
const std = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85, ...o });

function css() {
  if (document.getElementById('rpCss')) return;
  const s = document.createElement('style'); s.id = 'rpCss';
  s.textContent = `#rpGap{position:fixed;left:18px;top:40%;transform:rotate(-1.5deg);z-index:39;pointer-events:none;font-family:var(--font);color:#fff;text-align:center;
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
  const T = { on: false, set: null, boss: null, loading: false, geo: GEO0, parts: null, step: '', stepT: 0, spawnT: 0, auto: false, fin: null, failT: 0, retryAt: 0, tries: 0, said: -1 };
  const F = { live: false, gap: RP.gap.start, shown: RP.gap.start, rear: 0, rearS: 0, rate: 0, hp: 1, max: 1, phase: 0, stage: 0, plates: Array(PLATES).fill(0), open: 0, marrow: false, jack: 1, arms: new Map(), lunge: 0 };
  T.F = F;
  const HS = makeHitStop(); // (real time: the game's own dt is what it slows)
  let hudEl = null, failEl = null, env = null, time = 0;
  const S = () => ST.S;
  const busy = () => !!(ST.scene && ST.scene.playing());
  const Z = () => F.shown - F.rearS; // the mask is drawn at z = -Z(): THE GAP, from the train's back (which moves up when the wagon is bitten off)
  const view = () => ({ gap: F.gap - F.rear, arms: [...F.arms.values()].map((v) => v.a), plates: F.plates, open: F.open > 0, eyeL: F.stage >= 2, smile: F.stage >= 3 });
  // where a shot from o along d ends (for the Blood Drive's tracer): the fight, or the map
  const rayEnd = (o, d, max) => { const w = raycast(o, d, max, BOXES), wt = w ? w.t : max, h = F.live ? rayFight(T.geo, view(), o, d, wt) : null; return h ? { t: h.t, part: h.part, at: h.at } : { t: wt, part: w ? 'wall' : '', at: o.map((x, i) => x + d[i] * wt) }; };
  const BD = makeBloodDrive({ rayEnd, free: () => F.marrow || !!(S().st.flags.jack_marrow_taken || S().st.flags.seen_mo_carry) });
  T.drive = BD;
  const TS = makeTrainSet(); T.model = TS; // the Blender train and tunnel kit (the looks only)
  // the train's boxes are ours to draw (world.js leaves a box alone when a prop named by its `pv` is registered): a stand-in
  // built from the same table the room collides with, one group a car, so the wagon can go when it is bitten off
  if (!AUTHORED.p_rp_train) AUTHORED.p_rp_train = { scene: new THREE.Group(), meta: { kind: 'prop', id: 'rp_train' } };
  const MATC = { wood: [0x8f6238, 0.9, 0], metal: [0x6f767e, 0.55, 0.55], crate: [0xa5773f, 0.9, 0], white: [0xdcdcd4, 0.5, 0.1], yellow: [0xe2b21f, 0.6, 0.2], dark: [0x1c1a1c, 0.8, 0.3], hazard: [0xffb000, 0.7, 0] }, mats = {};
  const matOf = (k) => (mats[k] ||= std(MATC[k] ? MATC[k][0] : 0x888888, { roughness: MATC[k] ? MATC[k][1] : 0.8, metalness: MATC[k] ? MATC[k][2] : 0 }));
  function buildTrain(g) {
    const cars = {}, geo = new THREE.BoxGeometry(1, 1, 1), box = (car, x0, y0, z0, x1, y1, z1, mat) => { const m = new THREE.Mesh(geo, matOf(mat)); m.scale.set(x1 - x0, y1 - y0, z1 - z0); m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); (cars[car] ||= new THREE.Group()).add(m); };
    for (const b of MAPS[TRAIN.id].boxes) if (b.car) box(b.car, b.min[0], b.min[1], b.min[2], b.max[0], b.max[1], b.max[2], b.mat);
    for (const c of CARS) { // what the boxes don't have: underframes, wheels, the loco's face
      box(c.id, -HW + 0.5, 0.45, c.z0 + 0.3, HW - 0.5, c.deck - 0.2, c.z1 - 0.3, 'dark');
      for (const z of [c.z0 + 1, c.z1 - 2]) for (const sx of [-1, 1]) box(c.id, sx * 0.62, 0.14, z, sx * 0.9, 0.85, z + 1, 'dark');
      if (c.id === 'loco') { box(c.id, -HW + 0.38, c.deck, c.z0 - 0.03, HW - 0.38, 0.95, c.z0, 'hazard'); box(c.id, -1.2, 2.5, c.z0 + 0.27, 1.2, 3.3, c.z0 + 0.3, 'dark'); }
    }
    for (const [car, x, z, w, h, d, mat] of COVER) if (mat === 'white') for (const y of [0.5, 1.4]) box(car, x - w / 2 - 0.03, CAR[car].deck + y, z - d / 2 - 0.03, x + w / 2 + 0.03, CAR[car].deck + y + 0.06, z + d / 2 + 0.03, 'dark'); // the fridge's chains
    for (const c of Object.values(cars)) g.add(c);
    return cars;
  }
  // the crew, standing where they would fight (no AI yet: Jack at the back rail, Lumps on the flatbed, Gordo by the van's stairs)
  function crew(on) {
    for (const c of CREW) { const id = 'rp_' + c.id, n = S().defs.npcs[c.id];
      if (!on) { despawnActor(id); continue; }
      if (!actors.has(id) && n) { try { const a = spawnActor(id, { ...n, look: n.look || c.id, lines: null }, c.p.slice(), c.yaw); if (a) a.rpCrew = c; } catch (e) { console.warn('train crew', e); } } }
  }
  // the rear wagon, bitten off: its boxes leave your feet's world too (the room dropped its own), and come back on a retry
  function setWagon(on, anim) {
    const w = T.set && T.set.cars.wagon;
    if (!on && !T.cutBoxes) { T.cutBoxes = []; for (let i = BOXES.length - 1; i >= 0; i--) if (BOXES[i].car === 'wagon') T.cutBoxes.push(...BOXES.splice(i, 1)); T.cutT = anim ? 0 : 9; }
    if (on && T.cutBoxes) { BOXES.push(...T.cutBoxes); T.cutBoxes = null; if (w) { w.visible = true; w.position.set(0, 0, 0); w.rotation.set(0, 0, 0); } }
    TS.bitten(!!T.cutBoxes); // (the flatbed's torn end, on the model)
  }

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
    const lamp = new THREE.SpotLight(0xfff0dd, 110, 95, 0.5, 0.7, 1); lamp.position.set(0.4, CAR.van.roof + 0.4, CAR.van.roofZ0); lamp.target.position.set(0, CY, -RP.gap.start); g.add(lamp, lamp.target);
    const work = new THREE.PointLight(0xffd9a0, 10, 20, 1.1); work.position.set(0, 5.2, 13); g.add(work); // a work light over the cars
    const knots = [0, 1, 2].map(() => { const l = new THREE.PointLight(0x4fd8ff, 0, 4.5, 1.6); g.add(l); return l; }); // the wrist knots' glow on what is near them: a fixed three, moved to the nearest knots (a light that comes and goes with each arm would rebuild every shader)
    const cars = buildTrain(g);
    G.scene.add(g);
    T.set = { g, ribs, sl, bulbs, lights, lamp, knots, cars, off: 0, bore, cable, bz: [], bon: [] };
    crew(true);
  }
  function stepSet(dt) {
    const s = T.set, v = T.fin && T.fin.t > 2.2 ? SPEED : busy() ? SPEED * 0.6 : SPEED;
    s.off = (s.off + v * dt) % 12; s.run = (s.run || 0) + v * dt; s.v = v; // (run: all of it, for hands planted on the wall)
    s.ribs.position.z = -(s.off % 6); s.sl.position.z = -(s.off % 1.5);
    const maskZ = F.live || T.fin ? -Z() : -200, lit = [];
    for (let i = 0; i < s.bulbs.length; i++) {
      const b = s.bulbs[i], z = ARENA.z0 + i * 12 - s.off + (ARENA.z0 + i * 12 - s.off < ARENA.z0 ? ARENA.z1 - ARENA.z0 : 0);
      b.position.z = z;
      const d = z - maskZ, on = d > 3 || (d > 0.5 && Math.sin(time * 37 + i) > 0.2); // (it flickers as the face gets to it, then it is out)
      b.material.color.setHex(on ? 0xffc070 : 0x1a1210);
      if (on) lit.push(b.position);
      s.bz[i] = z; s.bon[i] = on;
    }
    if (s.kit) s.kit.step(v * dt, s.bz, s.bon); // the tunnel kit goes past at the same speed, and its bulbs are these bulbs
    lit.sort((p, q) => Math.abs(p.z - 4) - Math.abs(q.z - 4));
    s.lights.forEach((l, i) => { const p = lit[i]; l.intensity = p ? 22 : 0; if (p) l.position.set(p.x * 0.8, p.y - 0.5, p.z); });
    s.lamp.target.position.set(0, CY - 0.3, -Math.max(4, Z()));
    if (T.cutBoxes && s.cars.wagon && T.cutT < 9) { T.cutT += dt; const w = s.cars.wagon; w.position.z = -T.cutT * 16; w.position.y = -T.cutT * T.cutT * 2; w.rotation.x = -T.cutT * 0.5; w.visible = T.cutT < 0.9; if (!w.visible) T.cutT = 9; } // it goes back into the dark, and into the face
    else if (T.cutBoxes && s.cars.wagon) s.cars.wagon.visible = false;
    for (const a of actors.values()) if (a.rpCrew) a.hidden = (F.phase > a.rpCrew.until && !(a.rpCrew.id === 'pallet_jack' && S().st.flags.seen_mo_carry)) || busy() || (F.rear > 0 && a.rpCrew.p[2] < F.rear);
  }

  // ---------------------------------------------------------------- the mask (and the arm kit)
  const envMap = () => { if (!env && G.renderer) { const pm = new THREE.PMREMGenerator(G.renderer); env = pm.fromScene(new RoomEnvironment(), 0.04).texture; pm.dispose(); } return env; };
  // the Blender train and the tunnel kit, when their files land: the stand-in's looks are swapped for them (a file that
  // never comes leaves the boxes and the old bore, as before)
  function dress() {
    const s = T.set; if (!s || TS.off) return;
    if (!TS.train) { TS.load(envMap()); return; }
    if (!s.model) { s.model = TS.dress(s.cars) || null; TS.bitten(!!T.cutBoxes); }
    if (!s.kit) s.kit = TS.lay(s.g, s) || null;
  }
  function prep(root, k) {
    envMap();
    root.traverse((o) => { if (!o.isMesh) return; o.castShadow = false; o.receiveShadow = false; o.frustumCulled = false;
      for (const m of [].concat(o.material)) { // as glbkit.prepAuthored does: nearest textures, the studio reflection (dimmed: it is dark in here)
        for (const key of ['map', 'emissiveMap']) if (m[key]) { m[key].magFilter = THREE.NearestFilter; m[key].minFilter = THREE.NearestMipmapNearestFilter; m[key].anisotropy = 1; m[key].needsUpdate = true; }
        m.envMap = env; m.envMapIntensity = (m.metalness > 0.5 ? 0.5 : 0.14) * k; if (m.emissive && m.emissive.getHex() && m.emissiveIntensity > 0) m.toneMapped = false; } });
  }
  function load() {
    if (T.boss || T.loading || performance.now() < T.retryAt) return; T.loading = true; // (a load that failed waits before it tries again: 2 s, 4 s, ... a minute)
    const get = (u) => new Promise((ok, bad) => glbLoader().load(u, ok, undefined, bad));
    Promise.all([get('/models/story/revenue_protection.glb'), get('/models/story/rp_arm.glb'), fetch('/models/story/revenue_protection.parts.json').then((r) => (r.ok ? r.json() : null)).catch(() => null)]).then(([g, ga, parts]) => {
      prep(g.scene, 1); prep(ga.scene, 0.15);
      ga.scene.traverse((o) => { if (o.isMesh) for (const m of [].concat(o.material)) if (m.name !== 'rp_knot_glow') { m.roughness = Math.max(m.roughness ?? 1, 0.94); m.metalness = Math.min(m.metalness ?? 0, 0.05); } }); // charred, not glassy: no shine on the rope and the hands
      const N = {}, A = {}; g.scene.traverse((o) => { if (o.name) N[o.name] = o; }); ga.scene.traverse((o) => { if (o.name) A[o.name] = o; });
      const root = new THREE.Group(); root.add(g.scene); root.visible = false; G.scene.add(root);
      const glow = (name) => { let m = null; g.scene.traverse((o) => { if (o.isMesh) for (const x of [].concat(o.material)) if (x.name === name) m = x; }); return m; };
      // what an open eye housing shows: somewhere to put bolts
      const eyes = ['L', 'R'].map((k) => { const e = T.geo.eyes[k], m = new THREE.Mesh(new THREE.CircleGeometry(1, 20), new THREE.MeshBasicMaterial({ color: 0xff2a48, transparent: true, opacity: 0.9, toneMapped: false })); m.scale.set(e.h[0] * 0.92, e.h[1] * 0.92, 1); m.position.set(e.c[0], e.c[1], -0.12); m.visible = false; root.add(m); return m; });
      const red = new THREE.PointLight(0xff2030, 0, 16, 1.2); red.position.set(0, -1.6, 2.2); root.add(red);
      // the Inspector's chest, once the lower third is off: the crit spot has to read from the wagon
      const insp = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex(), color: 0xffe14d, transparent: true, opacity: 0.9, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); insp.position.set(T.geo.insp.crit[0], T.geo.insp.crit[1], T.geo.insp.crit[2] + 0.35); insp.visible = false; root.add(insp);
      const cross = new THREE.Group(), cm = new THREE.MeshBasicMaterial({ color: 0xff1f3d, transparent: true, opacity: 0.95, toneMapped: false, depthWrite: false });
      for (const rot of [0, Math.PI / 2]) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.7, R * 2, 0.3), cm); b.rotation.z = rot; cross.add(b); }
      cross.position.z = 0.9; cross.visible = false; root.add(cross);
      T.parts = parts; T.geo = geoFrom(parts);
      T.boss = { root, N, A, eyes, red, insp, cross, cm, inspGlow: glow('rp_inspector_glow'), eyeGlow: glow('rp_eye_glow'), hidden: new Set(parts ? parts.parts.filter((p) => p.hidden).map((p) => p.name) : []), debris: [], haul: [] };
      for (const nm of T.boss.hidden) if (N[nm]) N[nm].visible = false;
      for (const [sock, wa] of [[7, 3.3], [10, -0.36]]) T.boss.haul.push(newArm({ id: 'h' + sock, k: 'haul', sock, mouth: 0, st: 'grip', t: 0, dur: 0, tgt: [0, 0, 0], wa, hp: 1, max: 1 }, true)); // two arms on the walls that do the hauling (not targets: no knot). the left one plants high enough to be seen over the wagon's rail; the right one stays under the cables
      applyMask(); T.loading = false; T.tries = 0;
      if (!T.on) hideBoss(); // (it landed after you left: it waits, out of sight, for the next visit)
    }).catch((e) => { console.warn('revenue protection model', e); T.loading = false; T.loadErr = true; T.retryAt = performance.now() + Math.min(60000, 2000 * 2 ** T.tries++); });
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
    v.hand = b.A.arm_hand.clone(true); v.joints = []; v.fingers = []; v.hand.traverse((o) => { if (/^f\d_[abc]$/.test(o.name)) v.joints.push(o); if (/^f\d$/.test(o.name)) { o.userData.sp = o.rotation.y; v.fingers.push(o); } }); g.add(v.hand);
    v.stump = b.A.arm_stump.clone(true); v.stump.visible = false; g.add(v.stump);
    if (!decor) { // the wrist: lanyards and ID cards wound into a ball, lit from inside. it has to stand out in the dark
      v.knot = b.A.arm_knot.clone(true);
      v.knot.traverse((o) => { if (o.isMesh && [].concat(o.material).some((m) => m.name === 'rp_knot_glow')) { o.material = Array.isArray(o.material) ? o.material.map((m) => (m.name === 'rp_knot_glow' ? (v.glow = m.clone()) : m)) : (v.glow = o.material.clone()); } });
      v.halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex(), color: 0x4fd8ff, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); v.halo.scale.setScalar(3.2);
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
  const _p = new THREE.Vector3(), _q = new THREE.Vector3(), _x = new THREE.Vector3(), _y = new THREE.Vector3(), _m4 = new THREE.Matrix4();
  const CLAW = [-0.12, 0.5, 0.6]; // a hand on the brick: each finger's three joints, the first bent back, the tips dug in
  // H: a hauling arm's own path and hand (armgrip.js) instead of the room's ({ pts, wrist, dir, hand, claw, spread, curl })
  function poseArm(v, dt, gap, H) {
    const a = v.a, b = T.boss; if (!b || !v.hand) return;
    if (a.k === 'sweep') { a.tgt[2] = sweepZ(a); a.tgt[1] = sweepY(a); }
    if (a.k === 'snatch' && (a.st === 'reach' || a.st === 'hold') && ME.alive) a.tgt = [ME.pos[0], ME.pos[1] + RP.snatch.up, ME.pos[2] - 0.2];
    const P = H || armPose(T.geo, a, gap, v.decor ? v.ext : armExt(a)), J = armJoints(BORE, P, a.mouth, SEG); // (joints every 1.5 m, kept inside the bore)
    // a severed stump goes limp: as it pulls in, the rope sags off the wall toward the floor with a wobble (looks only:
    // a cut arm can't be hit). f = how far along the rope: the socket stays put, the cut end drops most
    let sw = P.wrist, sd = P.dir;
    if (a.st === 'cut' && J.length > 1) {
      const u = clamp(a.t / (a.dur || 1), 0, 1), drop = 1.9 * ss(Math.min(1, u * 1.7)), wob = 0.22 * (1 - u);
      const sag = (q, f) => [q[0] * (1 - 0.14 * (drop / 1.9) * f), Math.max(0.3, q[1] - drop * f + Math.sin(time * 13 + f * 6) * wob * f), q[2] + 0.25 * drop * f];
      for (let k = 1; k < J.length; k++) J[k] = sag(J[k], (k / (J.length - 1)) ** 1.6);
      sw = sag(P.wrist, 1); const L = J[J.length - 2], dx = sw[0] - L[0], dy = sw[1] - L[1], dz = sw[2] - L[2], dl0 = Math.hypot(dx, dy, dz) || 1; sd = [dx / dl0, dy / dl0, dz / dl0];
      if (Math.hypot(J[J.length - 1][0] - P.wrist[0], J[J.length - 1][1] - P.wrist[1], J[J.length - 1][2] - P.wrist[2]) < 1e-6) J[J.length - 1] = sw;
    }
    const n = J.length - 1;
    while (v.segs.length < n) { const s = b.A.arm_seg.clone(true); v.g.add(s); v.segs.push(s); }
    for (let k = 0; k < v.segs.length; k++) {
      const s = v.segs[k]; s.visible = k < n; if (k >= n) continue;
      const A0 = J[k], B0 = J[k + 1], rx = A0[0], ry = A0[1] - CY, rl = Math.hypot(rx, ry) || 1;
      s.position.set(A0[0], A0[1], A0[2]); s.up.set(rx / rl, ry / rl, 0); s.lookAt(_p.set(B0[0], B0[1], B0[2])); // (up = out from the bore's axis: the flat side lies on the wall)
      s.scale.set(1, flatK(a.mouth, k), clamp(Math.hypot(B0[0] - A0[0], B0[1] - A0[1], B0[2] - A0[2]) / SEG, 0.05, 1.05));
    }
    const w = sw, cut = a.st === 'cut', d = a.gp && a.st !== 'back' ? [a.gp[0] - w[0], a.gp[1] - w[1], a.gp[2] - w[2]] : P.dir, dl = Math.hypot(d[0], d[1], d[2]) || 1;
    v.hand.visible = !cut; v.stump.visible = cut;
    if (cut) { v.stump.position.set(w[0], w[1], w[2]); v.stump.up.set(0, 1, 0); v.stump.lookAt(_p.set(w[0] + sd[0], w[1] + sd[1], w[2] + sd[2])); v.stump.scale.setScalar(1.15); }
    else {
      // 0.4 m past the wrist, pointing the way it goes; a hand that would go through the lining is laid on it instead
      const hf = H ? H.hand : handFit(BORE, w, [d[0] / dl, d[1] / dl, d[2] / dl], Math.abs(d[1] / dl) > 0.9 ? [0, 0, 1] : [0, 1, 0]);
      v.hand.position.set(hf.o[0], hf.o[1], hf.o[2]); _y.set(hf.u[0], hf.u[1], hf.u[2]); _q.set(hf.f[0], hf.f[1], hf.f[2]); _x.crossVectors(_y, _q);
      v.hand.quaternion.setFromRotationMatrix(_m4.makeBasis(_x, _y, _q));
      const onWall = !H && (hf.tilt > 0 || hf.wall > 0.6) && a.st !== 'grip' && a.st !== 'hold'; // (crawling along the brick: fingers spread and dug in)
      const want = H && H.curl != null ? H.curl : a.st === 'grip' ? 0.95 : a.st === 'hold' ? 0.85 : a.st === 'sweep' ? 0.3 : 0.1 + 0.08 * Math.sin(time * 5 + (v.a.sock || 0));
      v.curl = (v.curl ?? 0.1) + (want - (v.curl ?? 0.1)) * Math.min(1, dt * 9);
      v.claw = (v.claw ?? 0) + ((H ? H.claw || 0 : onWall ? 1 : 0) - (v.claw ?? 0)) * Math.min(1, dt * (H && H.claw ? 30 : 9)); // (a planted hand bites at once)
      v.spread = (v.spread ?? 1) + ((H ? H.spread || 1 : onWall ? 1.35 : 1) - (v.spread ?? 1)) * Math.min(1, dt * 9);
      for (const j of v.joints) { const th = j.name[1] === '0' ? 0.75 : 1; j.rotation.x = (v.curl * (1 - v.claw) + CLAW['abc'.indexOf(j.name[3])] * v.claw) * th; }
      for (const f of v.fingers) f.rotation.y = f.userData.sp * v.spread;
    }
    if (v.knot) {
      const live = armLive(a); v.flash = Math.max(0, v.flash - dt * 5);
      v.knot.visible = v.halo.visible = live;
      v.knot.position.set(w[0], w[1], w[2]); v.halo.position.set(w[0], w[1], w[2]);
      const pulse = 0.5 + 0.5 * Math.sin(time * 6 + a.id), hurt = 1 - clamp(a.hp / a.max, 0, 1);
      if (v.glow) v.glow.emissiveIntensity = 2.4 + pulse * 1.2 + v.flash * 6;
      v.halo.scale.setScalar(1.9 + pulse * 0.4 + v.flash * 1.4); v.knot.scale.setScalar(1.2); v.halo.material.color.setHex(v.flash > 0.3 ? 0xffffff : hurt > 0.6 ? 0xff6a9a : 0x4fd8ff);
      v.knot.rotation.y += dt * (1 + hurt * 6);
    }
    v.wrist = w; v.dir = P.dir;
  }
  // ---------------------------------------------------------------- the haul (armgrip.js): two decor arms, no knot
  // each hand plants flat on the lining well ahead of the face, rides it back with the tunnel (it is the wall that moves:
  // the train and the face keep pace), skids as the fingers bite, lets go near the rim and reaches again, hand over hand
  function haulArms(b, dt, z) {
    const s = T.set, face = z + T.geo.faceZ, dist = s.kit ? s.kit.dist : s.off;
    for (const [i, v] of b.haul.entries()) {
      v.g.visible = b.root.visible; if (!v.hand) continue;
      const wa = v.a.wa, h = v.h ||= newHaul(i, face), S0 = T.geo.sockets[v.a.sock] || T.geo.sockets[0], S = [S0[0], CY + S0[1], z + S0[2]];
      if (T.fin) { h.zf ??= h.z; const k = ss(T.fin.t / 1.5); h.ph = 'let'; h.t = 0; h.z = h.zf + (S[2] + 1 - h.zf) * k; h.lift = 0.6 * k; if (k >= 1) v.g.visible = false; } // it lets go, and the arms go back in
      else {
        h.zf = null;
        const ev = stepHaul(h, { dt, run: s.run || 0, face, z0: ARENA.z0, dist, side: Math.cos(wa) < 0 ? -1 : 1, a: wa, v: s.v || SPEED, other: b.haul[1 - i] && b.haul[1 - i].h, lead: i === 0 });
        if (ev === 'plant' && v.g.visible) planted(v, i, face);
      }
      const hd = haulHand(BORE, h), L = hd.o[2] - S[2], bow = 0.12 + clamp((7.5 - L) / 5, 0, 1) + h.lift * 0.3; // (an elbow comes as the face hauls up to the hand)
      v.a.st = h.ph === 'grip' ? 'grip' : 'reach';
      poseArm(v, dt, 0, { pts: haulPath(BORE, S, hd.o, wa, bow), wrist: hd.o, dir: hd.f, hand: hd, claw: h.ph === 'grip' ? 1 : 0, spread: h.ph === 'reach' ? 1.5 : h.ph === 'grip' ? 1.3 : 1.1, curl: h.ph === 'grip' ? 0 : h.ph === 'let' ? 0.35 : -0.05 });
    }
    stepMarks(dt);
  }
  // a hand slapped onto the brick: dust and soot off the fingertips, a few sparks, the slap and the grind, claw marks
  function planted(v, i, face) {
    const h = v.h, hd = haulHand(BORE, h), tip = [0, 1, 2].map((n) => hd.o[n] + hd.f[n] * 1.7 - hd.u[n] * 0.3), k = clamp(1.4 - F.shown / 30, 0.3, 1.2);
    fx.dust(tip, 4); fx.spray(tip, 7, [0x7a3424, 0x4a2418, 0x15100e, 0x2a2220], 3.5, 0.55, 0.07, 12, 1); fx.sparks(tip, [0, 0, -1], 5, false);
    if (F.live) { sfx.rpGrip(tip, k); sfx.rpScrape(tip, clamp((h.zP - face - HAUL.let) / Math.max(1, T.set.v || SPEED), 0.3, 1.2), k); if (i === 0) sfx.rpHaul(tip, k); }
    mark(h, tip[2] - 0.05); // (under and just ahead of the fingertips: what they gouged as they bit and skidded)
  }
  // claw marks: a few dark gouges ahead of where the fingers bit, on the wall (so they go by with it) and fading. pooled
  let _claw = null;
  function clawTex() {
    if (_claw) return _claw;
    const c = document.createElement('canvas'); c.width = 64; c.height = 64; const x = c.getContext('2d');
    x.fillStyle = 'rgba(14,8,6,0.3)'; x.beginPath(); x.ellipse(32, 36, 26, 24, 0, 0, Math.PI * 2); x.fill(); // the soot smear
    for (const [cx, w] of [[12, 4], [25, 5], [39, 5], [52, 4]]) { // a groove a finger, deep at the far end where it bit: dark, with fresh brick along one lip
      x.fillStyle = 'rgba(214,140,96,0.55)'; x.beginPath(); x.moveTo(cx + 1, 4); x.lineTo(cx + 1 + w * 0.6, 60); x.lineTo(cx + 1 - w * 0.2, 60); x.closePath(); x.fill();
      x.fillStyle = 'rgba(6,3,2,0.9)'; x.beginPath(); x.moveTo(cx, 4); x.lineTo(cx + w / 2, 60); x.lineTo(cx - w / 2, 60); x.closePath(); x.fill(); }
    _claw = new THREE.CanvasTexture(c); return _claw;
  }
  function mark(h, zc) {
    const s = T.set;
    if (!s.marks) { s.marks = []; const geo = new THREE.PlaneGeometry(0.95, 0.75); for (let i = 0; i < 6; i++) { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: clawTex(), transparent: true, opacity: 0, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 })); m.visible = false; m.userData.t = 9; s.g.add(m); s.marks.push(m); } }
    const m = s.marks.reduce((p, q) => (q.userData.t > p.userData.t ? q : p)), a = h.a, r = R - 0.02;
    m.userData = { t: 0, z: zc, run: s.run || 0 }; m.visible = true;
    m.position.set(r * Math.cos(a), CY + r * Math.sin(a), zc); m.up.set(0, 0, 1); m.lookAt(_p.set(0, CY, zc)); // (faces the axis, its length along the tunnel)
  }
  function stepMarks(dt) {
    for (const m of T.set.marks || []) { const u = m.userData; if (!m.visible) continue; u.t += dt; m.position.z = u.z - ((T.set.run || 0) - u.run); m.material.opacity = 0.75 * (1 - ss((u.t - 1.6) / 1.4)); if (u.t > 3) m.visible = false; }
  }
  function freeArm(v) { G.scene.remove(v.g); if (v.glow) v.glow.dispose(); if (v.halo) v.halo.material.dispose(); }
  function clearArms() { for (const v of F.arms.values()) freeArm(v); F.arms.clear(); }
  function onArm(m) {
    if (!fin(m.id)) return;
    let v = F.arms.get(m.id);
    if (m.st === 'gone') { if (v) { freeArm(v); F.arms.delete(m.id); } return; }
    if (!v3(m.tgt) || typeof m.k !== 'string' || !fin(m.sock)) return;
    const a = { id: m.id, k: m.k, sock: clamp(m.sock | 0, 0, m.mouth ? 3 : 11), mouth: m.mouth ? 1 : 0, st: String(m.st), t: 0, dur: fin(m.dur) ? m.dur : 0, tgt: m.tgt.slice(), hi: !!m.hi, side: m.side || 0, rear: fin(m.rear) ? m.rear : 0, hp: fin(m.hp) ? m.hp : 1, max: fin(m.max) && m.max > 0 ? m.max : 1, ...(fin(m.wa) ? { wa: m.wa } : {}), ...(v3(m.gp) ? { gp: m.gp.slice() } : {}), ...(fin(m.e0) ? { e0: clamp(m.e0, 0, 1) } : {}) };
    if (!v) { v = newArm(a); F.arms.set(m.id, v); if (a.k === 'sweep') { hud.msg(a.hi ? 'HEAD HEIGHT. GET DOWN.' : 'KNEE HEIGHT. JUMP.', 1.3, 'reverse'); sfx.rpSweep(false); } }
    else { const was = v.a.st; v.a = a; if (a.st === 'cut' && was !== 'cut') severed(v, m); if (a.st === 'grip' && was !== 'grip') { sfx.rpHaul(v.wrist, 1.4); G.shake = Math.max(G.shake, 0.2); } if (a.st === 'hold' && was !== 'hold') hud.msg('IT HAS YOU. SHOOT THE WRIST.', 2, 'reverse'); if (a.k === 'sweep' && a.st === 'sweep' && was !== 'sweep') sfx.rpSweep(true); }
  }
  function severed(v, m) {
    const w = v.wrist || [0, 2, 0];
    sfx.rpSever(w); fx.blood(w, [0, 1, 0], 40, 0); fx.sparks(w, [0, 0, -1], 18, true); G.shake = Math.max(G.shake, 0.7); HS.hit(0.09);
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
    F.rear = fin(m.rear) && m.rear > 0 ? ARENA.cut : 0; F.rearS = F.rear; setWagon(!F.rear, false);
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
      case 'flinch': F.open = fin(ev.open) ? ev.open : RP.flinch.open; hud.msg('IT FLINCHED. THE EYES.', 2.2, 'brag'); sfx.rpFlinch(); G.shake = Math.max(G.shake, 0.6); if (T.boss) T.boss.flinch = 1; break;
      case 'swept': hud.msg(ev.hi ? 'SWEPT. SLIDE NEXT TIME.' : 'SWEPT. JUMP NEXT TIME.', 1.6, 'reverse'); G.shake = 1; break;
      case 'snatched': hud.msg('TAKEN. THE GAP WENT WITH YOU.', 2, 'reverse'); G.shake = 1; break;
      case 'lunge': if (ev.st === 'tell') { F.lunge = fin(ev.dur) ? ev.dur : RP.lunge.tell; hud.msg('IT REARS. OFF THE WAGON.', 1.5, 'reverse'); sfx.rpLunge(); } else { F.lunge = 0; G.shake = 1; if (T.boss) T.boss.bite = 1; if (fin(ev.gap)) F.gap = ev.gap;
        if (ev.cut) { F.rear = ARENA.cut; setWagon(false, true); HS.hit(0.12); hud.msg(ev.bit ? 'IT TOOK THE WAGON. AND SOME OF YOU.' : 'IT TOOK THE WAGON', 2.2, 'reverse'); sfx.rpPlate([0, 1, 4], true); sfx.rpSever([0, 1, 4]); fx.sparks([0, 1.2, CAR.wagon.z1], [0, 0, -1], 40, true); }
        else if (ev.bit) hud.msg('BITTEN', 1.2, 'reverse'); } break;
      case 'bag': hud.msg(`SOUP BAG. +${fin(ev.hp) ? ev.hp : RP.bag.hp} BLOOD`, 1.2, 'brag'); break;
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
    if (st >= 2 && was < 2) { hud.msg('THE LEFT EYE', 2, 'brag'); say('is this seat taken', 5); G.shake = 1; HS.hit(0.08); if (b) { drop('eye_L'); b.root.getWorldPosition(_p); const p = [_p.x + T.geo.eyes.L.c[0], _p.y + T.geo.eyes.L.c[1], _p.z + 0.4]; fx.sparks(p, [0, 0, 1], 30, true); fx.blood(p, [0, 0, 1], 30, 0); sfx.rpSever(p); } }
    if (st >= 3 && was < 3) { hud.msg('THE SMILE', 2.2, 'brag'); say('i\'m going to be late', 5); G.shake = 1; HS.hit(0.1); if (b) { for (const i of SPLIT) if (F.plates[i] !== 2) drop(pn(i, '_low')); drop('frame_low'); b.root.getWorldPosition(_p); sfx.rpPlate([_p.x, 1, _p.z], true); } }
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
    hud.msg('BLOOD CROSSED', 3.6, 'brag'); sfx.rpCross(); G.shake = 1; HS.hit(0.22); say('*click.*', 6);
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
    if (on !== T.on) { T.on = on; fade(0, 1.1); if (on) { if (T.set) { G.scene.add(T.set.g); setWagon(true); crew(true); } else buildSet(); load(); } else leave(); } // (the tunnel, the train and the models are built once and kept between visits)
    if (!on) { BD.tick(dt, false); return; }
    if (!T.boss) load();
    if (!T.set.model || !T.set.kit) dress();
    const held = busy(), sdt = held ? 0 : dt; // (a scene holds the room: hold the picture of it too)
    time += dt;
    stepSet(dt);
    F.gap = clamp(F.gap + F.rate * sdt, 0, RP.gap.max); F.open = Math.max(0, F.open - sdt); F.lunge = Math.max(0, F.lunge - sdt);
    if (!T.fin) F.shown += (F.gap - F.shown) * Math.min(1, dt * 6);
    F.rearS += (F.rear - F.rearS) * Math.min(1, dt * 5);
    const b = T.boss;
    if (b) {
      b.root.visible = (F.live || !!T.fin) && !(T.fin && T.fin.gone);
      // the haul: its two wall arms go hand over hand (haulArms), and the face lurches forward a little on each drag
      const lurchT = T.fin ? 0 : -0.2 + 0.5 * Math.max(0, ...b.haul.map((v) => (v.h && v.h.ph === 'grip' ? Math.sin(Math.PI * v.h.prog) : 0)));
      b.lurch = (b.lurch ?? 0) + (lurchT - (b.lurch ?? 0)) * Math.min(1, dt * 12); const lurch = b.lurch;
      const rear = F.lunge > 0 ? -1.6 * ss(1 - F.lunge / RP.lunge.tell) : 0; b.bite = Math.max(0, (b.bite || 0) - dt * 2.5);
      const z = -Z() + lurch + rear + (b.bite || 0) * 1.2;
      b.root.position.set(0, CY, z); b.root.rotation.z = T.fin ? 0 : Math.sin(time * 0.9) * 0.012 + (b.flinch || 0) * 0.05 * Math.sin(time * 40);
      b.flinch = Math.max(0, (b.flinch || 0) - dt * 1.4); b.redK = Math.max(0, (b.redK || 0) - dt * 3);
      haulArms(b, dt, z);
      // the eye housings swing open on a flinch; behind the blown left one, eyes
      const open = F.open > 0 && !T.fin ? 1 : 0; b.openK = (b.openK || 0) + (open - (b.openK || 0)) * Math.min(1, dt * 7);
      if (b.N.eye_L) b.N.eye_L.rotation.y = 1.25 * b.openK; if (b.N.eye_R) b.N.eye_R.rotation.y = -1.25 * b.openK;
      b.eyes[0].visible = b.openK > 0.2 && F.stage < 2; b.eyes[1].visible = b.openK > 0.2; for (const e of b.eyes) e.material.opacity = 0.65 + 0.3 * Math.sin(time * 14);
      if (F.stage >= 2 && b.N.eye_cluster) for (const c of b.N.eye_cluster.children) c.lookAt(_p.set(ME.pos[0], ME.pos[1] + 1.5, ME.pos[2]));
      if (b.eyeGlow) b.eyeGlow.emissiveIntensity = 1.5 + Math.sin(time * 3) * 0.5;
      // phase 3: hanging off one bolt, swinging; the Inspector lit from inside, punching a ticket that isn't there
      if (!T.fin && b.N.mask) { const hang = F.phase >= 2 && T.parts && T.parts.stages && T.parts.stages[3] && T.parts.stages[3].hang; if (hang && v3(hang.pivot)) pivot(b.N.mask, hang.pivot, -0.07, -0.06 + Math.sin(time * 1.3) * 0.035); }
      b.insp.visible = F.stage >= 3 && !T.fin; b.insp.scale.setScalar((F.phase >= 2 ? 1.5 : 0.9) + Math.sin(time * 5) * 0.2);
      if (b.inspGlow) b.inspGlow.emissiveIntensity = (F.phase >= 2 ? 3.2 : 1.2) + Math.sin(time * 5) * 0.8;
      if (b.N.insp_foreR) b.N.insp_foreR.rotation.x = Math.max(0, Math.sin(time * 4.2)) * 0.5; if (b.N.insp_punch_lever) b.N.insp_punch_lever.rotation.x = Math.max(0, Math.sin(time * 4.2)) > 0.8 ? 0.3 : 0;
      if (!T.fin) b.red.intensity = (F.stage >= 3 ? 14 : 5) + b.redK * 40 + (F.phase >= 2 ? 6 * Math.sin(time * 5) : 0);
      // sparks where the rim scrapes the brickwork, all the way round
      if (F.live && !T.fin && !held && (b.sparkT = (b.sparkT || 0) - dt) < 0) { b.sparkT = 0.05 + Math.random() * 0.12; const a = -0.6 + Math.random() * (Math.PI + 1.2); fx.sparks([R * 0.97 * Math.cos(a), CY + R * 0.97 * Math.sin(a), z + 0.3], [0, 0, 1], 5 + (Math.random() * 6 | 0), Math.random() < 0.3); }
      if (T.fin) stepFinish(dt);
      stepDebris(dt);
    }
    for (const v of F.arms.values()) { v.a.t += sdt; if (b && !v.hand) { freeArm(v); const nv = newArm(v.a); Object.assign(v, nv); } poseArm(v, dt, Z()); } // (an arm that came before the model did gets its body now)
    { const ks = [...F.arms.values()].filter((v) => v.wrist && armLive(v.a)).sort((p, q) => Math.hypot(p.wrist[0] - ME.pos[0], p.wrist[2] - ME.pos[2]) - Math.hypot(q.wrist[0] - ME.pos[0], q.wrist[2] - ME.pos[2])); T.set.knots.forEach((l, i) => { const v = ks[i]; l.intensity = v ? 3.5 + v.flash * 8 : 0; if (v) l.position.set(v.wrist[0], v.wrist[1], v.wrist[2]); }); }
    showHud();
    BD.tick(dt, ME.alive && !held && !(T.failT && !F.live), !(G.story.triggerOff && G.story.triggerOff()));
  };
  function leave() {
    if (T.back === 'fading') setTimeout(() => { if (G.story && G.story.save) G.story.save('checkpoint'); }, 3000); // back out in the world after the end of Act I: a save right there (story/main.js)
    clearArms(); F.live = false; T.fin = null; T.said = -1; T.auto = false; T.back = null; F.rear = F.rearS = 0; T.cutBoxes = null; TS.bitten(false); crew(false); HS.clear(); T.jack = 0;
    if (T.set) { G.scene.remove(T.set.g); const w = T.set.cars.wagon; if (w) { w.visible = true; w.position.set(0, 0, 0); w.rotation.set(0, 0, 0); } } // (kept: nothing to rebuild or dispose next time)
    hideBoss();
    if (hudEl) hudEl.classList.add('hidden'); if (failEl) { failEl.classList.remove('on'); failEl.classList.add('hidden'); }
  }
  function hideBoss() { const b = T.boss; if (!b) return; b.root.visible = false; for (const d of b.debris.splice(0)) G.scene.remove(d.m); for (const v of b.haul) v.g.visible = false; for (const m of (T.set && T.set.marks) || []) m.visible = false; unbreak(); }
  // a real hit-stop on a sever (story main.js multiplies the game's dt by this). only on the train, and never past leave()
  T.timeScale = () => (T.on ? HS.scale() : 1); T.hitStop = HS;
  // what your other guns can hit (bossref.js gives the room's bot these boxes): the face and every arm. the room judges the shot
  T.boxes = () => {
    if (!F.live) return null;
    const zg = F.gap - F.rear, out = [{ min: [-T.geo.maskR, CY - T.geo.maskR, -zg - 0.4], max: [T.geo.maskR, CY + T.geo.maskR, -zg + 0.4] }], bx = (p, r) => out.push({ min: [p[0] - r, p[1] - r, p[2] - r], max: [p[0] + r, p[1] + r, p[2] + r] });
    for (const v of F.arms.values()) { if (!armLive(v.a)) continue; const P = armPose(T.geo, v.a, zg); bx(P.wrist, 0.56); for (const p of P.pts) bx(p, 0.4); }
    return out;
  };

  // ---------------------------------------------------------------- the quest: m06's fight steps
  const objective = () => { const os = S().quests.objectives ? S().quests.objectives() : []; return os.find((x) => x.quest === RP_QUEST) || null; };
  const spawn = (resume) => { if (G.story && G.story.send) G.story.send('spawn', { kind: RP_ID, id: RP_ID, at: [0, CY, -RP.gap.start], ...(resume ? { resume: 1 } : {}) }); }; // resume: the fight from phase 2's start (a run reloaded past the middle scene)
  T.spawn = spawn;
  T.frame = () => {
    const o = objective(), step = o ? o.step : '', now = performance.now();
    if (step !== T.step) { T.step = step; T.stepT = now; }
    const fight = step === 'hold' || step === 'break', ride = step === 'ride';
    if (!ride) T.rode = false;
    if ((fight || ride) && G.joined && G.mode === 'story' && MAP.id !== TRAIN.id && G.story.travel && !T.going && !busy()) { // the fight is on the train: fade, then go there (story/main.js remembers where from)
      T.going = true; fade(1, 0.5);
      setTimeout(() => { if (!G.story.travel(TRAIN.id)) { T.going = false; fade(0, 0.4); } }, 550);
      return;
    }
    if (!T.on) return;
    T.going = false;
    if (ride && !T.rode && !busy() && S().defs.scenes[RIDE]) { T.rode = true; playScene(RIDE); } // the ride in plays on the train, with the crew aboard (boarding cut you here)
    if ((fight || (TRAINQ && !o && !T.auto)) && !F.live && !T.fin && now - T.spawnT > 2500 && !busy()) { T.spawnT = now; T.auto = true; spawn(step === 'break'); } // (the room has one boss at a time: asking twice is nothing)
    // the middle scene plays in full now (a moment with a choice isn't cut at 3 s: scene.js) and its [FIRE] and [TAKE]
    // are the mission's choices, opened by the scene. you fire: the bolt goes into Jack and the cross comes, small.
    // once the scene is over the step gets its flag (and the choices' flags, if the scene was skipped past them).
    // a run reloaded at this step plays the scene again first
    const fl = S().st.flags, ja = actors.get('_scene_jack') || actors.get('rp_pallet_jack'), jc = actors.get('rp_pallet_jack'); // (in the scene he's the scene's own Jack; after it, the crew's)
    dressJack();
    if (step === 'jack' && ja && !T.jackHurt) { T.jackHurt = true; PJ.dmg(ja, 'armour_broken'); }
    if (step === 'jack' && fl.jack_fired && !T.jackShot) { T.jackShot = true; if (ja) { bloom([ja.pos[0], ja.pos[1] + 1.1, ja.pos[2]]); HS.hit(0.1); } }
    if (step === 'jack' && fl.jack_marrow_taken && ja && !T.jackMarrow) { T.jackMarrow = true; PJ.dmg(ja, 'marrow_taken'); }
    if (fl.seen_mo_carry && jc && !busy() && (!jc.clip || jc.clip.name !== 'pj_last_breath')) { PJ.play(jc, 'pj_last_breath', { hold: true }); if (jc.clip) jc.clip.t = jc.clip.len; PJ.dmg(jc, 'marrow_taken'); } // after it, he stays down on the deck, hand open
    if (step !== 'jack') { T.jack = 0; T.jackShot = false; T.jackHurt = false; T.jackMarrow = false; }
    else if (busy()) T.jack = 2; // it is playing
    else if (T.jack === 2) { T.jack = 3; S().run(['flag:jack_fired', 'flag:jack_marrow_taken', 'flag:seen_mo_carry']); }
    else if (!T.jack && now - T.stepT > 4000 && S().defs.scenes.mo_carry_the_bit_that_works) { T.jack = 1; playScene('mo_carry_the_bit_that_works'); } // (the step's own scene never came: a reload)
    // done with the mission (or it was never on) after a trip here: back to where you came from
    const q = S().st.quests[RP_QUEST];
    if (!o && q && q.done && !busy() && G.story.travelBack && (!F.live || (T.fin && T.fin.t > 6)) && now - T.stepT > 4000 && !T.back) { T.back = 'fading'; fade(1, 0.6); setTimeout(() => { if (!G.story.travelBack(outAt())) { T.back = 'nowhere'; fade(0, 0.4); } }, 650); }
    // on the train with no business here (a slot started on the old ?train=1 demo link, or m06 not on its train part):
    // nothing to fight and no way off, so take them home (where they boarded, else the Bottom's spawn)
    else if (!TRAINQ && stranded(q, step) && !busy() && G.story.travelBack && !F.live && now - T.stepT > 4000 && !T.back) { T.back = 'fading'; fade(1, 0.6); setTimeout(() => { if (!G.story.travelBack(null)) { T.back = 'nowhere'; fade(0, 0.4); } }, 650); }
  };
  // m06 over: the Loop comes out of the hill at the tunnel mouth (the Commute, at dusk), not back where you boarded.
  // until the world has that spot, back where you got on (worlds.js travelHome)
  const fade = (k, d) => { const f = document.getElementById('stFade'); if (f) { f.style.transition = `opacity ${d}s`; f.style.opacity = k; } }; // (the scene layer's black: boot.js)
  const outAt = () => { const pl = PLACES['commute:tunnel_mouth']; return pl && Array.isArray(pl.p) ? { map: 'story_slice', p: pl.p.slice(), yaw: Number.isFinite(pl.yaw) ? pl.yaw : 0 } : null; };
  T.outAt = outAt;
  // the ride in (c6) is asked for when m06's ride step starts, at the service tunnel: it waits for the train, where the
  // crew is (T.frame plays it there). anything else plays where it's asked
  const RIDE = 'c6_mind_the_gap', MID = 'mo_carry_the_bit_that_works';
  // the middle scene as written has no clips for Jack: his own (docs/story/train/FIGHT.md, the pj_* table) go in at its
  // beats: the armour goes and he's down against the fridge, he takes your hand at 26 s, the breath out after you fire
  function dressJack() {
    const sc = S().defs.scenes[MID]; if (!sc || sc.pjDressed || !Array.isArray(sc.tracks)) return;
    sc.pjDressed = true;
    sc.tracks.push({ t: 0, anim: ['jack', 'pj_armour_break_fall', true] }, { t: 26, anim: ['jack', 'pj_dying_talk', true] }, { t: 52, anim: ['jack', 'pj_last_breath', true] });
  }
  T.holdScene = (id) => id === RIDE && MAP.id !== TRAIN.id;
  if (typeof window !== 'undefined') window.JF_TRAIN = T; // (tests and screenshots stage it from here)
  return T;
}
