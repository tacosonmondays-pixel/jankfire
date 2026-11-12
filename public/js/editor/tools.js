// The map editor's sandbox tools (our own take on a sandbox game's tool guns):
//   GRABBY BEAM  hold left click on a thing: a wobbly pink/cyan beam picks it up. it floats where you grabbed it, the
//                wheel pushes / pulls, hold R and move the mouse to turn it (90 degree clicks: collision stays boxes),
//                right click freezes it right there, let go and it drops to the floor below. let go while swinging
//                and it flies: an arc, a thud, a squash.
//   PLOP CANNON  shoots the hotbar's thing where you aim: a see-through preview on the floor, R turns, wheel sizes,
//                click = pew + it pops in.
//   YEET RAY     zaps a thing away in a cartoon poof.
//   EDIT WAND    the old select / carry / copy / delete tools (editor.js).
// Every tool's change is an ordinary edit op (undo, CHANGES, EXPORT all work). api: editor.js internals.
import * as THREE from 'three';
import { ghostOf, dropGhost } from './modelghost.js';
import { buildVM, setTool, updateVM, vmKick, vmHold, vmLook, setVMMoving, muzzleNDC, TOOLS, vmVisible } from './vm.js';
import { sfxEd, humOn, humOff, humPitch, unlockAudio } from './sfx.js';

let A = null, tool = 'grab', item = null, held = null, fall = null, prev = null, rot = null, landing = false, frozeAt = 0;
const anims = []; // { t, dur, fn(k), end() }
const V = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const TURN = [[1, 0], [0, 1], [-1, 0], [0, -1]];
const yawV = (v, q) => { const [c, s] = TURN[q & 3]; return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c]; }; // (three's rotation.y by q quarter turns)

export function initTools(api) {
  A = api;
  buildVM(A.G.vmScene);
  initFx(A.G.scene);
}
export const curTool = () => tool;
export const curItem = () => item;
export const busy = () => !!(held || fall || landing); // (landing: the squash before the move is saved)
export const justFroze = () => performance.now() - frozeAt < 400; // (the right-click that froze it isn't a fly click)
export function resetPreview() { endPreview(); } // (SOLID changed: the next plop is built again)
export function pickTool(t) {
  if (!TOOLS[t] || t === tool) return;
  if (held) letGo(false);
  tool = t; setTool(t); sfxEd.swap(); endPreview();
  A.onTool && A.onTool(t);
}
export function loadItem(it) { item = it; endPreview(); if (tool !== 'plop') pickTool('plop'); A.onTool && A.onTool(tool); }

// ---------------------------------------------------------------- the aim: what the crosshair (or mouse) lands on
function aimSurface(skip, far = 140) {
  const [o, d] = A.aimRay(), h = A.pick(o, d, skip, true, true), th = A.terrainHit(o, d, Math.min(far, h ? h.dist : far));
  let dist = h ? h.dist : null, top = h ? h.top : false;
  if (th != null && (dist == null || th < dist)) { dist = th; top = true; }
  return { o: o.clone(), d: d.clone(), dist, top };
}

// ---------------------------------------------------------------- GRABBY BEAM
function grabStart() {
  const [o, d] = A.aimRay(), h = A.pick(o, d, null);
  if (!h) { sfxEd.nope(); vmKick(0.3); return; }
  const ts = A.sel.has(h.t) && A.sel.size > 1 ? [...A.sel] : [h.t];
  const piv = A.pivotFor(ts), hit = [o.x + d.x * h.dist, o.y + d.y * h.dist, o.z + d.z * h.dist];
  const ghost = ghostOf(ts, piv, A.edgesFor(ts)); ghost.position.set(...piv); A.G.scene.add(ghost);
  const rel = A.relBounds(ts, piv); // (before it leaves the map: edge snapping needs its size)
  A.select([]); A.hide(ts); // (the real one leaves the map while you hold it)
  held = { ts, o: piv, off: [piv[0] - hit[0], piv[1] - hit[1], piv[2] - hit[2]], dist: h.dist, q: 0, d: [0, 0, 0], rel, ghost, vel: new THREE.Vector3(), last: null, end: V(hit) };
  sfxEd.grab(); humOn(); vmHold(true); vmKick(0.4); A.callout('YOINK');
  sparks(V(hit), 18);
}
function grabMove(dt) {
  const [o, d] = A.aimRay(), H = held;
  const tgt = [o.x + d.x * H.dist, o.y + d.y * H.dist, o.z + d.z * H.dist], off = yawV(H.off, H.q);
  const want = [tgt[0] + off[0], tgt[1] + off[1], tgt[2] + off[2]], s = A.snap();
  const dd = [want[0] - H.o[0], want[1] - H.o[1], want[2] - H.o[2]];
  if (s) for (let i = 0; i < 3; i++) dd[i] = Math.round(dd[i] / s) * s;
  H.d = A.edgeSnap(H.rel, H.o, H.q, 1, dd); const e = H.d; dd[0] = e[0]; dd[1] = e[1]; dd[2] = e[2];
  const p = new THREE.Vector3(H.o[0] + dd[0], H.o[1] + dd[1], H.o[2] + dd[2]);
  if (H.last && dt > 0) H.vel.lerp(p.clone().sub(H.last).divideScalar(dt), 0.35); // (how fast you're swinging it)
  H.last = p.clone();
  H.ghost.position.copy(p); H.ghost.rotation.y = H.q * Math.PI / 2;
  H.end.set(tgt[0], tgt[1], tgt[2]);
  humPitch(1 + Math.min(1, H.dist / 80) * 0.6);
  if (Math.random() < dt * 20) sparks(H.end, 2);
  A.grid([p.x, p.y, p.z]);
}
// let go: fling = let it fly (or just drop to the floor below); freeze = stay right where it is
function letGo(fling, freeze) {
  const H = held; held = null; humOff(); vmHold(false); rot = null; A.grid(null);
  if (!H) return;
  if (freeze) { finish(H, H.d); sfxEd.freeze(); A.callout('FROZEN'); frozeAt = performance.now(); return; }
  const v = fling ? H.vel.clone() : new THREE.Vector3();
  if (v.length() < 7) v.set(0, 0, 0); else { v.clampLength(0, 45); sfxEd.whoosh(); }
  fall = { H, p: new THREE.Vector3(H.o[0] + H.d[0], H.o[1] + H.d[1], H.o[2] + H.d[2]), v, t: 0, spin: v.length() > 0 ? new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize().multiplyScalar(v.length() * 0.6) : null };
}
const G_FALL = 32;
function fallStep(dt) {
  const F = fall, H = F.H, skip = new Set(H.ts);
  F.t += dt; F.v.y -= G_FALL * dt;
  const step = F.v.clone().multiplyScalar(dt), len = step.length();
  if (len > 1e-6) {
    const dir = step.clone().divideScalar(len), from = F.p.clone().add(new THREE.Vector3(0, 0.05, 0));
    const h = A.pick(from, dir, skip, true, true), th = A.terrainHit(from, dir, len + 0.1);
    let hd = h ? h.dist : null, top = h ? h.top : false;
    if (th != null && (hd == null || th < hd)) { hd = th; top = true; }
    if (hd != null && hd <= len + 0.06) {
      const at = from.clone().addScaledVector(dir, hd);
      if (top || dir.y < -0.7) { land(at); return; }
      F.v.x *= -0.25; F.v.z *= -0.25; F.p.copy(at).addScaledVector(dir, -0.08); F.p.y -= 0.05; sfxEd.thud(false); sparks(at, 8); // (hit a wall: bounce off it a little)
    } else F.p.add(step);
  }
  H.ghost.position.copy(F.p);
  if (F.spin) { H.ghost.rotation.x += F.spin.x * dt; H.ghost.rotation.z += F.spin.z * dt; H.ghost.rotation.y += F.spin.y * dt; }
  if (F.p.y < (A.MAP.killY ?? -45) + 2 || F.t > 6) { // the void: it comes back where it was
    fall = null; dropGhost(H.ghost); A.unhide(H.ts); A.rebuild(); sfxEd.nope(); A.callout('THE VOID SAID NO');
  }
}
function land(at) {
  const F = fall, H = F.H; fall = null;
  const s = A.snap(), d = [at.x - H.o[0], at.y - H.o[1], at.z - H.o[2]];
  if (s) { d[0] = Math.round(d[0] / s) * s; d[2] = Math.round(d[2] / s) * s; const e = A.edgeSnap(H.rel, H.o, H.q, 1, d); d[0] = e[0]; d[2] = e[2]; d[1] = Math.max(d[1], e[1]); }
  H.ghost.position.set(H.o[0] + d[0], H.o[1] + d[1], H.o[2] + d[2]); H.ghost.rotation.set(0, H.q * Math.PI / 2, 0);
  const big = F.v.length() > 12;
  sfxEd.thud(big); sparks(H.ghost.position, big ? 26 : 10);
  if (big) A.callout(['YEETED', 'SKRRT', 'BONK', 'NICE'][(Math.random() * 4) | 0]);
  landing = true;
  anim(0.16, (k) => { const q = Math.sin(k * Math.PI); H.ghost.scale.set(1 + q * 0.18, 1 - q * 0.25, 1 + q * 0.18); }, () => { landing = false; finish(H, d); });
}
function finish(H, d) {
  dropGhost(H.ghost);
  A.unhide(H.ts); // (back exactly as it was, then the move is an ordinary op)
  if (!A.alive(H.ts)) { A.rebuild(); return; } // (gone from the map meanwhile: nothing to move)
  if (d.every((v) => Math.abs(v) < 1e-4) && !H.q) { A.rebuild(); return; }
  A.opXf(H.ts, H.o, 1, H.q, d);
  sfxEd.clunk();
}

// ---------------------------------------------------------------- PLOP CANNON
let prv = null; // { key, data, t, pv, ghost, q, k, at }
function endPreview() { if (prv) { dropGhost(prv.ghost); prv = null; } }
function preview() {
  if (!item) return null;
  const key = item.kind + ':' + item.id;
  if (!prv || prv.key !== key || !prv.data) {
    const data = A.itemData(item.kind, item.id);
    if (prv && prv.key === key && !data) return null;
    endPreview();
    if (!data) { prv = { key, data: null }; return null; } // (its model is still loading: asked again next frame)
    const t = A.thingFrom(data), b = A.boundsOf(t), pv = [(b.lo[0] + b.hi[0]) / 2, b.lo[1], (b.lo[2] + b.hi[2]) / 2];
    prv = { key, data, t, pv, rel: A.relBounds([t], pv), ghost: ghostOf([t], pv, A.edgesFor([t]), true), q: 0, k: 1, at: null };
    A.G.scene.add(prv.ghost);
  }
  return prv;
}
function plopMove() {
  const P = preview(); if (!P || !P.ghost) return;
  const a = aimSurface(null), dist = a.dist != null && a.dist < 140 ? a.dist : 12, s = A.snap();
  const at = [a.o.x + a.d.x * dist, a.o.y + a.d.y * dist, a.o.z + a.d.z * dist];
  if (s) { at[0] = Math.round(at[0] / s) * s; at[2] = Math.round(at[2] / s) * s; const e = A.edgeSnap(P.rel, P.pv, P.q, item.kind === 'arch' ? 1 : P.k, [at[0] - P.pv[0], at[1] - P.pv[1], at[2] - P.pv[2]]); for (let i = 0; i < 3; i++) at[i] = P.pv[i] + e[i]; }
  P.at = at; P.ghost.position.set(...at); P.ghost.rotation.y = P.q * Math.PI / 2; P.ghost.scale.setScalar(P.k);
  A.grid(at);
}
function plopFire() {
  const P = preview();
  if (!P || !P.ghost || !P.at) { sfxEd.nope(); A.toast(item ? 'loading it...' : 'pick something first: E opens the menu, or 5-9 on the hotbar'); return; }
  sfxEd.pew(); vmKick(1);
  const at = P.at.slice(), q = P.q, k = P.k, t = A.thingFrom(P.data), pv = P.pv;
  A.xfThing(t, pv, item.kind === 'arch' ? 1 : k, q, [at[0] - pv[0], at[1] - pv[1], at[2] - pv[2]]);
  const pop = ghostOf([A.thingFrom(P.data)], pv, null); pop.position.set(...at); pop.rotation.y = q * Math.PI / 2; A.G.scene.add(pop);
  beamFlash(V(at), 0xffe14d);
  anim(0.2, (x) => { const s = x < 0.7 ? 0.2 + (x / 0.7) * 0.95 : 1.15 - ((x - 0.7) / 0.3) * 0.15; pop.scale.set(s * k, s * k * (x < 0.7 ? 1.1 : 1), s * k); }, () => {
    dropGhost(pop); A.opAdd([A.thingData(t)]); sfxEd.pop(); sparks(V(at), 10); A.recent && A.recent(item);
  });
  A.callout('PLOP');
}

// ---------------------------------------------------------------- YEET RAY
function yeetFire() {
  const [o, d] = A.aimRay(), h = A.pick(o, d, null);
  vmKick(0.8);
  if (!h) { sfxEd.nope(); return; }
  const ts = A.sel.has(h.t) && A.sel.size > 1 ? [...A.sel] : [h.t], piv = A.pivotFor(ts), hit = V([o.x + d.x * h.dist, o.y + d.y * h.dist, o.z + d.z * h.dist]);
  const g = ghostOf(ts, piv, null); g.position.set(...piv); A.G.scene.add(g);
  sfxEd.zap(); beamFlash(hit, 0xff3030);
  A.opDel(ts); sfxEd.poof(); poof(V(piv).add(new THREE.Vector3(0, 0.6, 0)));
  const spin = (Math.random() - 0.5) * 14;
  anim(0.42, (k) => { const s = Math.max(0.001, 1 - k * k); g.scale.set(s, s * (1 + k * 0.6), s); g.position.y = piv[1] + k * k * 3; g.rotation.y = k * spin; }, () => dropGhost(g));
  A.callout('YEET');
}

// ---------------------------------------------------------------- input from editor.js (true = the tool took it)
export function toolDown(btn) {
  unlockAudio();
  if (tool === 'wand') return false;
  if (btn === 0) { if (tool === 'grab' && !held && !fall) grabStart(); else if (tool === 'plop') plopFire(); else if (tool === 'yeet') yeetFire(); return true; }
  if (btn === 2 && held) { letGo(false, true); return true; }
  return false;
}
export function toolUp(btn) { if (btn === 0 && held) { letGo(true); return true; } return tool !== 'wand' && btn === 0; }
export function toolWheel(dy) {
  if (held) { held.dist = Math.max(1.5, Math.min(160, held.dist * (dy > 0 ? 0.88 : 1.12))); return true; }
  if (tool === 'plop' && prv && prv.data && item && item.kind !== 'arch') { prv.k = Math.max(0.25, Math.min(6, prv.k * (dy > 0 ? 1 / 1.1 : 1.1))); A.toast('size x' + prv.k.toFixed(2)); return true; }
  return false;
}
// R: hold while grabbing to turn it with the mouse; tap with the plop cannon to turn the preview
export function toolKey(code, down, shift) {
  if (code !== 'KeyR') return false;
  if (held) { if (down) { if (!rot) { rot = { acc: 0 }; held.q = (held.q + (shift ? 3 : 1)) & 3; sfxEd.click(); } } else rot = null; return true; } // (a tap turns it once; held, the mouse keeps turning it)
  if (tool === 'plop' && down) { if (prv) { prv.q = (prv.q + (shift ? 3 : 1)) & 3; sfxEd.click(); } return true; }
  return false;
}
export function toolMouse(mx, my) { // false: the camera looks as normal
  vmLook(mx, my);
  if (!held || !rot) return false;
  rot.acc += mx;
  if (Math.abs(rot.acc) > 110) { held.q = (held.q + (rot.acc > 0 ? 1 : 3)) & 3; held.off = held.off; rot.acc = 0; sfxEd.click(); vmKick(0.2); }
  return true;
}
export function updateTools(dt, moving) {
  setVMMoving(moving ? 1 : 0); updateVM(dt);
  if (held) grabMove(dt);
  if (fall) fallStep(dt);
  if (tool === 'plop' && !held && !fall) plopMove(); else if (prv && prv.ghost) prv.ghost.visible = false;
  if (prv && prv.ghost) prv.ghost.visible = tool === 'plop';
  for (let i = anims.length - 1; i >= 0; i--) { const a = anims[i]; a.t += dt; const k = Math.min(1, a.t / a.dur); a.fn(k); if (k >= 1) { anims.splice(i, 1); a.end && a.end(); } }
  updateFx(dt);
}
export const hideVM = (v) => vmVisible(!v);
function anim(dur, fn, end) { anims.push({ t: 0, dur, fn, end }); }

// ---------------------------------------------------------------- beam, sparks, poofs
let beam = null, flash = null, sp = null, puffs = [];
const SPN = 220;
function initFx(scene) {
  beam = { g: new THREE.Group(), a: new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: 0xff4fd8, transparent: true, opacity: 0.9, depthWrite: false })), b: new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: 0x4fd8ff, transparent: true, opacity: 0.9, depthWrite: false })), end: new THREE.Mesh(new THREE.IcosahedronGeometry(0.22, 0), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8, depthWrite: false })) };
  beam.g.add(beam.a, beam.b, beam.end); beam.g.visible = false; beam.g.renderOrder = 990; scene.add(beam.g);
  const pos = new Float32Array(SPN * 3).fill(-9999), col = new Float32Array(SPN * 3), g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  sp = { pts: new THREE.Points(g, new THREE.PointsMaterial({ size: 5, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false })), vel: new Float32Array(SPN * 3), life: new Float32Array(SPN), n: 0 };
  sp.pts.frustumCulled = false; scene.add(sp.pts);
}
const SPC = [new THREE.Color(0xff4fd8), new THREE.Color(0x4fd8ff), new THREE.Color(0xffe14d), new THREE.Color(0xffffff)];
function sparks(at, n) {
  const P = sp.pts.geometry.attributes.position, C = sp.pts.geometry.attributes.color;
  for (let i = 0; i < n; i++) {
    const k = sp.n++ % SPN, c = SPC[(Math.random() * SPC.length) | 0];
    P.setXYZ(k, at.x, at.y, at.z); C.setXYZ(k, c.r, c.g, c.b);
    sp.vel[k * 3] = (Math.random() - 0.5) * 9; sp.vel[k * 3 + 1] = Math.random() * 7 + 1; sp.vel[k * 3 + 2] = (Math.random() - 0.5) * 9; sp.life[k] = 0.35 + Math.random() * 0.35;
  }
  P.needsUpdate = C.needsUpdate = true;
}
const puffGeo = new THREE.IcosahedronGeometry(0.5, 0);
function poof(at) {
  for (let i = 0; i < 9; i++) {
    const m = new THREE.Mesh(puffGeo, new THREE.MeshBasicMaterial({ color: i % 3 ? 0xffffff : 0xff4fd8, transparent: true, opacity: 0.9, depthWrite: false }));
    m.position.copy(at); const v = new THREE.Vector3(Math.random() - 0.5, Math.random() * 0.8, Math.random() - 0.5).normalize().multiplyScalar(2 + Math.random() * 3);
    A.G.scene.add(m); puffs.push({ m, v, t: 0 });
  }
  sparks(at, 24);
}
function beamFlash(to, col) { flash = { to: to.clone(), t: 0.14, col }; }
const _a = new THREE.Vector3(), _f = new THREE.Vector3(), _r = new THREE.Vector3(), _u = new THREE.Vector3();
function muzzleWorld(out) { // the tool's muzzle on screen, 0.7 m out from the world camera (the tool draws in its own scene)
  const n = muzzleNDC(A.G.vmCamera), cam = A.G.camera;
  if (!n) return out.copy(cam.position);
  out.set(n.x, n.y, 0.5).unproject(cam).sub(cam.position).normalize().multiplyScalar(0.7).add(cam.position);
  return out;
}
function tube(mesh, pts) { mesh.geometry.dispose(); mesh.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 22, 0.028, 5, false); }
function drawBeam(to, col, t) {
  const s = muzzleWorld(_a), cam = A.G.camera; cam.getWorldDirection(_f);
  const len = s.distanceTo(to), ctrl = s.clone().addScaledVector(_f, len * 0.45);
  _r.copy(_f).cross(cam.up).normalize(); _u.copy(_r).cross(_f).normalize();
  for (const [mesh, ph] of [[beam.a, 0], [beam.b, Math.PI]]) {
    const pts = [];
    for (let i = 0; i <= 14; i++) {
      const k = i / 14, w = Math.sin(k * Math.PI) * (0.12 + len * 0.01), a = t * 22 + k * 9 + ph;
      const p = new THREE.Vector3().copy(s).multiplyScalar((1 - k) * (1 - k)).addScaledVector(ctrl, 2 * k * (1 - k)).addScaledVector(to, k * k);
      p.addScaledVector(_r, Math.cos(a) * w).addScaledVector(_u, Math.sin(a) * w);
      pts.push(p);
    }
    tube(mesh, pts);
  }
  beam.a.material.color.setHex(col === 0xffe14d ? 0xffe14d : 0xff4fd8); beam.b.material.color.setHex(col === 0xff3030 ? 0xff3030 : 0x4fd8ff);
  beam.end.position.copy(to); beam.end.scale.setScalar(0.8 + Math.sin(t * 30) * 0.25); beam.end.rotation.set(t * 3, t * 5, 0);
  beam.g.visible = true;
}
let ft = 0;
function updateFx(dt) {
  ft += dt;
  if (held) drawBeam(held.end, 0x4fd8ff, ft);
  else if (flash) { flash.t -= dt; drawBeam(flash.to, flash.col, ft); if (flash.t <= 0) flash = null; }
  else beam.g.visible = false;
  const P = sp.pts.geometry.attributes.position;
  for (let k = 0; k < SPN; k++) {
    if (sp.life[k] <= 0) continue;
    sp.life[k] -= dt; sp.vel[k * 3 + 1] -= 18 * dt;
    if (sp.life[k] <= 0) { P.setXYZ(k, -9999, -9999, -9999); continue; }
    P.setXYZ(k, P.getX(k) + sp.vel[k * 3] * dt, P.getY(k) + sp.vel[k * 3 + 1] * dt, P.getZ(k) + sp.vel[k * 3 + 2] * dt);
  }
  P.needsUpdate = true;
  for (let i = puffs.length - 1; i >= 0; i--) {
    const p = puffs[i]; p.t += dt; p.m.position.addScaledVector(p.v, dt); p.v.multiplyScalar(Math.pow(0.05, dt));
    p.m.scale.setScalar(0.4 + p.t * 3); p.m.material.opacity = Math.max(0, 0.9 - p.t * 2.2);
    if (p.t > 0.45) { A.G.scene.remove(p.m); p.m.material.dispose(); puffs.splice(i, 1); }
  }
}
// tests: the state
export const toolState = () => ({ tool, item, held: !!held, falling: !!fall, q: held ? held.q : prv ? prv.q : 0, preview: !!(prv && prv.ghost) });
