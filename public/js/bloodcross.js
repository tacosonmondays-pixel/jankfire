// Blood Cross, everything you see: the bolt (turned to face where it flies, with its trail), the X it leaves in whoever it
// hits, the two spikes that burst out through them, the pop (blood everywhere, splats on the walls, a red glow) and the
// X it leaves in walls. Live play and replays both feed server events in here; a replay passes its own ghosts + their info.
import * as THREE from 'three';
import { G } from './ctx.js';
import { PSys, setBeam } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { ME } from './player.js';
import { BLOOD_BOLTS } from './models.js';
import { BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { WEAPONS } from '/shared/weapons.js';

const W = WEAPONS.bloodcross;
const S = 1.2; // remotes are drawn 1.2x real size: marks + spikes live in their body space, so sizes here are world / 1.2
// glow = the red haze (normal blending: additive red goes pink on the sky and yellow on grass), core = the white-hot bits (additive),
// red = the bulk of the gore
export const PAL = {
  blood: { core: 0xffc0c8, glow: 0xff1a2e, red: 0xd0001a, bolt: 0xff4a5c, x: 0xff2a3a, deep: 0x9a0010, dark: 0x3a0006, splat: 0x6a0008, mist: 0xb0101c, css: '255,26,46' },
  shadow: { core: 0xf0d8ff, glow: 0xa02bff, red: 0x7414c8, bolt: 0xd070ff, x: 0xc860ff, deep: 0x30004a, dark: 0x0c0414, splat: 0x1e0028, mist: 0x3a0a50, css: '160,43,255' },
};
// Shadow Cross bleeds purple: everything that comes out of that hand follows its owner's skin
export function palOf(o, info) {
  const sk = info ? ((info[o] || {}).skins || {}).bloodcross : o === G.myId ? (G.equipped || {}).bloodcross : (G.skins.get(o) || {}).bloodcross;
  return sk && sk[3] === 'bloodcross_shadow' ? PAL.shadow : PAL.blood;
}

const R = (s = 1) => (Math.random() * 2 - 1) * s;
const tmpA = new THREE.Vector3(), tmpB = new THREE.Vector3(), tmpQ = new THREE.Quaternion();
const ray = new THREE.Raycaster();
let scene = null, blood = null, glow = null, glowTex = null, splatTex = null, GEO = null;
const marks = new Map(); // key -> a cross stuck in someone (or loose in the world once they're gone)
const walls = []; // X's in walls and floors, fizzling out
const fades = []; // glow flashes, blast rings, trail beams: things that just fade away
const splats = []; // blood on surfaces
const beamPool = { add: [], haze: [] };
const bangs = []; // other people's hands mid-'bang': thumb (the hammer) snaps down, the finger kicks up
const gore = () => G.settings.blood !== false;

export function initCrosses(sc) {
  scene = sc;
  blood = new PSys(2400, THREE.NormalBlending);
  glow = new PSys(1500, THREE.AdditiveBlending);
  sc.add(blood.points, glow.points);
}

// ------------------------------------------------------------ bits
function geo() {
  return GEO ||= {
    bar: new THREE.BoxGeometry(1, 1, 1), spike: new THREE.OctahedronGeometry(1, 0), plane: new THREE.PlaneGeometry(1, 1),
    beam: new THREE.BoxGeometry(1, 1, 1).translate(0, 0, 0.5), ring: new THREE.RingGeometry(0.92, 1, 48).rotateX(-Math.PI / 2),
  };
}
function glowTexture() {
  if (glowTex) return glowTex;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.22, 'rgba(255,255,255,0.6)'); g.addColorStop(0.55, 'rgba(255,255,255,0.16)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  return (glowTex = new THREE.CanvasTexture(c));
}
function splatTexture() { // chunky pixel splat: a blob, spikes thrown out of it, loose drops
  if (splatTex) return splatTex;
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const x = c.getContext('2d');
  const dot = (cx, cy, r) => { for (let y = -r; y <= r; y++) for (let k = -r; k <= r; k++) if (k * k + y * y <= r * r + r * 0.6) x.fillRect(cx + k, cy + y, 1, 1); };
  x.fillStyle = '#fff';
  dot(16, 16, 7);
  for (let i = 0; i < 9; i++) {
    const a = (i / 9) * Math.PI * 2 + Math.random() * 0.5, l = 8 + Math.random() * 6;
    for (let k = 6; k < l; k++) dot(16 + Math.round(Math.cos(a) * k), 16 + Math.round(Math.sin(a) * k), k > l - 2 ? 1 : k > 9 ? 1 : 2);
  }
  for (let i = 0; i < 8; i++) { const a = Math.random() * Math.PI * 2, l = 11 + Math.random() * 4; dot(16 + Math.round(Math.cos(a) * l), 16 + Math.round(Math.sin(a) * l), Math.random() < 0.5 ? 1 : 0); }
  x.fillStyle = '#d8d8d8'; dot(15, 15, 4); // a darker wet middle
  splatTex = new THREE.CanvasTexture(c);
  splatTex.magFilter = THREE.NearestFilter; splatTex.minFilter = THREE.NearestFilter; splatTex.generateMipmaps = false;
  return splatTex;
}
const basic = (color) => new THREE.MeshBasicMaterial({ color });
const additive = (color, opacity) => new THREE.MeshBasicMaterial({ color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false });
const haze = (color, opacity) => new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false });
function sprite(color, size, opacity, add = false) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color, transparent: true, opacity, blending: add ? THREE.AdditiveBlending : THREE.NormalBlending, depthWrite: false }));
  s.scale.setScalar(size);
  return s;
}
function dispose(o) { o.traverse((m) => { if (m.material) m.material.dispose(); }); }

// the cross: an upright beam with the crossbar in its upper third, each bar a bright core on a dark-red rim (so it reads as
// a cross, not a red smudge), a white-hot line down each, a soft glow behind. len = beam height, th = bar thickness
function makeX(pal, len, th) {
  const g = new THREE.Group();
  for (const [w, h, y] of [[th, len, 0], [len * 0.62, th, len * 0.2]]) { // beam, then crossbar
    const rim = new THREE.Mesh(geo().bar, basic(pal.deep)); rim.scale.set(w + th * 0.75, h + th * 0.75, th * 0.35); rim.position.set(0, y, -th * 0.1); g.add(rim);
    const bar = new THREE.Mesh(geo().bar, basic(pal.x)); bar.scale.set(w, h, th * 0.45); bar.position.y = y; g.add(bar);
    const core = new THREE.Mesh(geo().bar, additive(pal.core, 0.7)); core.scale.set(w > h ? w * 0.82 : th * 0.34, w > h ? th * 0.34 : h * 0.82, th * 0.6); core.position.y = y; g.add(core);
  }
  g.userData.glow = sprite(pal.glow, len * 2.1, 0.3);
  g.userData.hot = sprite(pal.core, len * 0.7, 0.4, true);
  g.userData.glow.position.z = g.userData.hot.position.z = -th * 0.3;
  g.add(g.userData.glow, g.userData.hot);
  return g;
}
// the eruption: two long shards in a big upright cross in the parent's XY plane, a few thorns on each so it reads as torn-out blood
function makeSpikes(pal, len) {
  const g = new THREE.Group(), parts = [];
  for (const s of [-1, 1]) {
    const one = new THREE.Group(); one.rotation.z = s < 0 ? 0 : Math.PI / 2; if (s > 0) one.position.y = len * 0.2; // a cross: the upright beam, then the crossbar high on it
    const core = new THREE.Mesh(geo().spike, basic(pal.deep)); core.scale.set(0.075, len / 2, 0.075);
    const hot = new THREE.Mesh(geo().spike, haze(pal.glow, 0.4)); hot.scale.set(0.14, (len / 2) * 1.05, 0.14);
    const vein = new THREE.Mesh(geo().spike, additive(pal.core, 0.5)); vein.scale.set(0.018, (len / 2) * 0.8, 0.085); // a hot line down the middle
    one.add(core, hot, vein);
    for (let i = 0; i < 6; i++) {
      const th = new THREE.Mesh(geo().spike, basic(pal.deep)), side = i % 2 ? 1 : -1;
      th.position.set(side * 0.05, (i / 5 - 0.5) * len * 0.8 + R(0.08), 0);
      th.scale.set(0.024, 0.13 + Math.random() * 0.08, 0.024);
      th.rotation.z = -side * (0.55 + Math.random() * 0.3);
      one.add(th);
    }
    one.scale.set(0.3, 0.001, 0.3);
    g.add(one); parts.push({ one, hot });
  }
  g.userData.parts = parts;
  g.userData.glow = sprite(pal.glow, len * 0.8, 0);
  g.add(g.userData.glow);
  g.visible = false;
  return g;
}
// trail segments: red haze, or a thin white-hot core (add)
function beam(a, b, color, th, life, add = false, op = 1) {
  const pool = add ? beamPool.add : beamPool.haze;
  const m = pool.pop() || new THREE.Mesh(geo().beam, add ? additive(color, 1) : haze(color, 1));
  m.material.color.setHex(color); m.material.opacity = op; m.frustumCulled = false;
  setBeam(m, a, b, th);
  scene.add(m);
  fades.push({ obj: m, life, ml: life, op, beam: pool });
}
// something that grows from s0 to s1 and fades out over life seconds (glow flashes, the blast ring)
function flash(obj, p, life, s0, s1, flat) {
  obj.position.set(p[0], p[1], p[2]);
  scene.add(obj);
  fades.push({ obj, life, ml: life, op: obj.material.opacity, s0, s1, flat });
}
function spurt(p, pal, n, dir, sz = 1) {
  for (let i = 0; i < n; i++) {
    const v = dir ? [dir[0] * 3 + R(2), dir[1] * 3 + R(1.5) + 1, dir[2] * 3 + R(2)] : [R(3), R(2) + 1.5, R(3)];
    if (gore()) blood.spawn(p[0], p[1], p[2], v[0], v[1], v[2], 0.4 + Math.random() * 0.4, 0.08 * sz, 0.04 * sz, pal.red, pal.dark, 1, 14, 0.4);
    if (i % 2) blood.spawn(p[0], p[1], p[2], R(4), R(4), R(4), 0.2, 0.12 * sz, 0.02, pal.glow, pal.red, 1, 0, 3);
    if (i % 4 === 1) glow.spawn(p[0], p[1], p[2], R(3), R(3), R(3), 0.15, 0.05 * sz, 0.01, pal.core, pal.glow, 1, 0, 3); // white-hot specks
  }
}

// ------------------------------------------------------------ the bolt (every one, live or replay: models.js keeps the list)
export function crossShot(m, pr) {
  if (!scene) return;
  const pal = palOf(m.o);
  if (pr && pr.mesh) {
    tintBolt(pr.mesh, pal);
    const L = Math.hypot(m.v[0], m.v[1], m.v[2]) || 1, d = [m.v[0] / L, m.v[1] / L, m.v[2] / L], b = pr.mesh;
    b.userData.dir = d;
    b.lookAt(b.position.x - d[0], b.position.y - d[1], b.position.z - d[2]);
  }
  // yours: weapons.js already did the thump + the finger flick. the bolt means the server took the blood: now you feel it
  // (a shot it refused, on HP the client hadn't caught up on, never flashes)
  if (m.o === G.myId) { hud.hurt(10); return; }
  sfx.bcBeat(m.p);
  const r = G.remotes.get(m.o);
  if (r && r.alive) { const a = r.muzzle(); beam(a, m.p, pal.glow, 0.035, 0.1, false, 0.85); beam(a, m.p, pal.core, 0.012, 0.07, true, 0.9); spurt(a, pal, 8, null, 0.7); }
  const u = r && r.weaponMesh && r.weaponMesh.userData;
  if (u && u.thumb) bangs.push({ u, t: 0 });
}
// your own shot: a thin tracer of blood from the fingertip out along your aim, until the real bolt shows up past 1.6 m
export function crossFired(from, to) {
  if (!scene) return;
  const pal = palOf(G.myId);
  beam(from, to, pal.glow, 0.022, 0.08, false, 0.85);
  beam(from, to, pal.core, 0.008, 0.06, true, 0.9);
}
function tintBolt(b, pal) {
  const u = b.userData.bolt;
  if (!u || pal === PAL.blood) return;
  b.userData.pal = pal;
  u.core.material.color.setHex(pal.bolt); u.shell.material.color.setHex(pal.glow); u.halo.material.color.setHex(pal.glow);
}
function bolts() {
  const cam = G.camera.position, live = !document.body.classList.contains('replaying');
  for (const b of BLOOD_BOLTS) {
    if (!b.parent) { BLOOD_BOLTS.delete(b); continue; }
    const p = b.position, u = b.userData;
    const far = (x, y, z) => Math.hypot(x - cam.x, y - cam.y, z - cam.z) > 1.6;
    if (live) b.visible = far(p.x, p.y, p.z); // your own bolt starts right in your face: a red blob over the crosshair. show it from 1.6 m out
    if (u.lx != null) {
      const dx = p.x - u.lx, dy = p.y - u.ly, dz = p.z - u.lz, L = Math.hypot(dx, dy, dz);
      if (L > 1e-3 && L < 25) {
        u.dir = [dx / L, dy / L, dz / L];
        if (b.visible && (!live || far(u.lx, u.ly, u.lz))) trail([u.lx, u.ly, u.lz], [p.x, p.y, p.z], u.pal || PAL.blood);
      }
    }
    if (u.dir) b.lookAt(p.x - u.dir[0], p.y - u.dir[1], p.z - u.dir[2]); // nose first, whatever the projectile loop did to it
    u.lx = p.x; u.ly = p.y; u.lz = p.z;
  }
}
function trail(a, c, pal) { // one unbroken red streak per frame (a bolt covers 1.25 m a frame), white-hot down the middle, fine haze
  beam(a, c, pal.red, 0.12, 0.2, false, 0.9);
  beam(a, c, pal.core, 0.03, 0.08, true, 0.9);
  for (let i = 0; i < 4; i++) {
    const k = Math.random(), x = a[0] + (c[0] - a[0]) * k, y = a[1] + (c[1] - a[1]) * k, z = a[2] + (c[2] - a[2]) * k;
    blood.spawn(x, y, z, R(0.3), R(0.3), R(0.3), 0.2 + Math.random() * 0.15, 0.09, 0.02, pal.glow, pal.deep, 0.7, 0, 1); // red haze
    if (i === 0) glow.spawn(x, y, z, R(0.6), R(0.6), R(0.6), 0.15, 0.05, 0.01, pal.core, pal.glow, 1, 0, 1); // sparks
  }
  if (gore() && Math.random() < 0.6) blood.spawn(c[0], c[1], c[2], R(0.6), -0.4, R(0.6), 0.6, 0.07, 0.04, pal.deep, pal.dark, 1, 14, 0.3); // drips
}

// ------------------------------------------------------------ marks
function who(id, ghosts) {
  if (ghosts) return { r: ghosts.get(id) || null };
  return id === G.myId ? { me: true } : { r: G.remotes.get(id) || null };
}
const under = (o, roots) => { for (let p = o; p; p = p.parent) if (roots.includes(p)) return true; return false; };
function inScene(o) { while (o.parent) o = o.parent; return o === scene; }
function newMark(key, m, info) {
  return { key, o: m.o, to: m.to, pal: palOf(m.o, info), t: 0, te: -1, tb: -1, fuse: m.f || W.fuse, off: m.off || [0, 1.5, 1], p: m.p, me: false, grp: null, x: null, sp: null, r: null, loose: false };
}
// stick it on their mannequin: aim at their middle from outside at the hit height and put the X where the ray meets skin
// (the hitbox is a lot fatter than the body you see). the group's +Z points out of them through the X
function attach(mk, r) {
  const body = r.ch.body, lh = mk.off[1] / S;
  r.ch.root.updateMatrixWorld(true);
  const ax = body.localToWorld(tmpA.set(0, lh, 0));
  const dir = body.localToWorld(tmpB.set(mk.off[0], lh, mk.off[2])).sub(ax).normalize();
  ray.set(ax.clone().addScaledVector(dir, 1.6), dir.clone().negate());
  ray.far = 1.7; ray.camera = G.camera;
  const skip = [r.ch.arm, r.ch.armL, ...[...marks.values()].map((m) => m.grp)]; // skin only: not the arms, not another cross already in them
  const hit = ray.intersectObject(body, true).find((h) => h.object.isMesh && !h.object.userData.outline && !under(h.object, skip));
  const depth = hit ? Math.max(0.04, Math.min(0.45, body.worldToLocal(hit.point.clone()).setY(0).length())) : 0.17;
  const grp = new THREE.Group();
  grp.position.set(0, lh, 0);
  grp.rotation.y = Math.atan2(mk.off[0], mk.off[2]);
  body.add(grp);
  dress(mk, grp, depth);
  mk.r = r;
}
// no body to stick to (not built yet, or gone): hang it in the world facing whoever is looking
function loose(mk, p) {
  const grp = new THREE.Group();
  grp.position.set(p[0], p[1], p[2]);
  grp.scale.setScalar(S);
  grp.lookAt(G.camera.position.x, p[1], G.camera.position.z);
  scene.add(grp);
  dress(mk, grp, 0.12);
  mk.loose = true;
}
function dress(mk, grp, depth) {
  mk.grp = grp;
  grp.userData.bcMark = mk.key;
  mk.x = makeX(mk.pal, 0.62, 0.075); // big enough to read from across the map
  mk.x.position.z = depth + 0.02;
  mk.sp = makeSpikes(mk.pal, 2.5 / S);
  mk.sp.position.z = depth * 0.3; // through the middle of them, a hair toward the side it hit
  grp.add(mk.x, mk.sp);
}
function centerOf(mk) {
  if (mk.me) { // you: the middle of your chest, on the side it hit
    const c = Math.cos(ME.yaw), s = Math.sin(ME.yaw), o = mk.off;
    return [ME.pos[0] + (o[0] * c + o[2] * s) * 0.18, ME.pos[1] + o[1], ME.pos[2] + (o[2] * c - o[0] * s) * 0.18];
  }
  if (mk.sp && inScene(mk.sp)) { mk.sp.updateWorldMatrix(true, false); mk.sp.getWorldPosition(tmpA); return [tmpA.x, tmpA.y, tmpA.z]; }
  return mk.p;
}
function stick(m, key, ghosts, info) {
  if (marks.has(key)) dropMark(marks.get(key)); // the same replay played again (killcam, then the play of the round)
  const mk = newMark(key, m, info), tg = who(m.to, ghosts);
  if (tg.me) { mk.me = true; ov.start(mk); hud.msg('BLOOD CROSSED', 0.9, 'reverse'); hud.impact(0.55); }
  else if (tg.r && tg.r.alive && tg.r.ch) attach(mk, tg.r);
  else loose(mk, m.p);
  if (!ghosts && m.o === G.myId && !tg.me) { hud.hit(false); sfx.hit(); } // you marked them: the pop is 0.85 s away
  marks.set(key, mk);
  const c = centerOf(mk);
  sfx.bcStick(c); sfx.bcWhine(c, mk.fuse);
  if (!mk.me) spurt(c, mk.pal, 10); // particles at your own chest are giant blocks over your face: you get the screen X instead
}
function erupt(mk) {
  if (mk.te >= 0) return;
  mk.te = 0;
  if (mk.sp) mk.sp.visible = true;
  const c = centerOf(mk), P = mk.pal;
  sfx.bcErupt(c);
  if (mk.me) ov.erupt();
  // it bursts out of all four ends at once
  if (mk.sp) for (const { one } of mk.sp.userData.parts) {
    one.updateWorldMatrix(true, false);
    tmpA.set(0, 1, 0).applyQuaternion(one.getWorldQuaternion(tmpQ));
    for (const s of [-1, 1]) {
      const d = [tmpA.x * s, tmpA.y * s, tmpA.z * s], e = [c[0] + d[0] * 1.2, c[1] + d[1] * 1.2, c[2] + d[2] * 1.2];
      for (let i = 0; i < 10; i++) {
        const sp = 3 + Math.random() * 5;
        if (gore()) blood.spawn(e[0], e[1], e[2], d[0] * sp + R(1), d[1] * sp + R(1) + 1, d[2] * sp + R(1), 0.5 + Math.random() * 0.4, 0.1, 0.05, P.red, P.dark, 1, 15, 0.4);
        blood.spawn(e[0], e[1], e[2], d[0] * sp * 1.4 + R(1), d[1] * sp * 1.4 + R(1), d[2] * sp * 1.4 + R(1), 0.25, 0.14, 0.03, P.glow, P.red, 1, 0, 2);
        if (i % 3 === 0) glow.spawn(e[0], e[1], e[2], d[0] * sp * 1.6, d[1] * sp * 1.6, d[2] * sp * 1.6, 0.18, 0.06, 0.01, P.core, P.glow, 1, 0, 2);
      }
    }
  }
  if (!mk.me) spurt(c, P, 16);
}
function boom(mk) {
  if (mk.tb >= 0) return;
  mk.tb = 0;
  const c = centerOf(mk);
  if (mk.grp && !mk.loose && inScene(mk.grp)) { scene.attach(mk.grp); mk.loose = true; } // they come apart, the cross stays where they were
  if (mk.me) ov.boom();
  { const d = G.camera ? G.camera.position.distanceTo(new THREE.Vector3(c[0], c[1], c[2])) : 99, k = mk.me ? 1 : d < 30 ? 0.75 - d / 60 : 0; if (k > 0) hud.impact(k); } // red impact frames
  burst(c, mk.pal, mk.me);
  sfx.bcBoom(c);
  const d = Math.hypot(c[0] - ME.pos[0], c[1] - ME.pos[1], c[2] - ME.pos[2]);
  G.shake = Math.max(G.shake, mk.me ? 1 : Math.max(0, 1 - d / 22));
}
function dropMark(mk) {
  if (mk.grp) { if (mk.grp.parent) mk.grp.parent.remove(mk.grp); dispose(mk.grp); }
  marks.delete(mk.key);
}
function tickMark(mk, dt) {
  mk.t += dt;
  if (mk.te >= 0) mk.te += dt;
  if (mk.tb >= 0) mk.tb += dt;
  if (mk.t > mk.fuse + W.burst + 3) { dropMark(mk); return; } // never heard how it ended
  if (mk.me) { if (mk.tb > 0.7) dropMark(mk); return; }
  if (!mk.grp || !inScene(mk.grp)) { dropMark(mk); return; } // the body it was on is gone (left, rebuilt, replay over)
  if (mk.r && !mk.loose && !mk.r.alive) { scene.attach(mk.grp); mk.loose = true; } // killed by something else: stay on the spot
  const P = mk.pal;
  if (mk.tb < 0) { // stuck in them: pulses faster as it gets ready, bleeds
    const k = Math.min(1, mk.t / mk.fuse), beat = Math.abs(Math.sin(mk.t * (7 + 18 * k)));
    mk.x.scale.setScalar(1 + 0.25 * beat * (0.4 + k) + (mk.te >= 0 ? 0.3 : 0));
    mk.x.userData.glow.material.opacity = 0.22 + 0.35 * k * beat + (mk.te >= 0 ? 0.25 : 0);
    mk.x.userData.hot.material.opacity = 0.25 + 0.45 * beat * k;
    if (gore() && Math.random() < dt * 22) { mk.x.getWorldPosition(tmpA); blood.spawn(tmpA.x + R(0.05), tmpA.y + R(0.05), tmpA.z + R(0.05), R(0.3), -0.3, R(0.3), 0.6, 0.06, 0.04, P.deep, P.dark, 1, 14, 0.2); }
  }
  if (mk.te >= 0 && mk.sp) { // burst out: overshoot, settle, throb
    const e = mk.te, k = e < 0.06 ? (e / 0.06) * 1.2 : e < 0.13 ? 1.2 - ((e - 0.06) / 0.07) * 0.2 : 1, w = 0.3 + 0.7 * Math.min(1, e / 0.06);
    const fade = mk.tb >= 0 ? Math.min(1, mk.tb / 0.45) : 0;
    for (const p of mk.sp.userData.parts) {
      p.one.scale.set(Math.max(0.001, w * (1 - fade)), Math.max(0.001, k * (1 + 0.25 * fade)), Math.max(0.001, w * (1 - fade)));
      p.hot.material.opacity = (0.45 + 0.2 * Math.sin(mk.t * 40)) * (1 - fade) + (mk.tb >= 0 && mk.tb < 0.06 ? 0.5 : 0);
    }
    mk.sp.userData.glow.material.opacity = 0.5 * (1 - fade);
  }
  if (mk.tb >= 0) {
    const k = Math.min(1, mk.tb / 0.45);
    mk.x.scale.setScalar(Math.max(0.001, 1.3 * (1 - k)));
    if (k >= 1) dropMark(mk);
  }
}

// ------------------------------------------------------------ the pop
function burst(c, P, me) {
  const g = gore();
  if (me) { if (g) splatter(c, P); ring(c, P); return; } // it went off in your chest: the screen flash is the burst, the room still gets painted
  if (g) for (let i = 0; i < 170; i++) { // heavy blood: flung out sideways more than up, falls, lands
    const a = [R(), R() * 0.6 + 0.2, R()], l = Math.hypot(...a) || 1, sp = 2 + Math.random() * 7.5;
    blood.spawn(c[0] + R(0.15), c[1] + R(0.25), c[2] + R(0.15), (a[0] / l) * sp, (a[1] / l) * sp + 1.5, (a[2] / l) * sp,
      0.7 + Math.random() * 0.8, 0.08 + Math.random() * 0.13, 0.05, Math.random() < 0.4 ? P.glow : Math.random() < 0.6 ? P.red : P.deep, P.dark, 1, 17, 0.7);
  }
  for (let i = 0; i < (g ? 22 : 12); i++) blood.spawn(c[0] + R(0.5), c[1] + R(0.5), c[2] + R(0.5), R(2.2), R(1.2) + 0.5, R(2.2), 0.7 + Math.random() * 0.6, 0.25, 0.75, P.glow, P.deep, 0.3, -0.4, 2.2); // a red mist that hangs
  for (let i = 0; i < 60; i++) { // glowing droplets: bright red ones + a few white-hot sparks
    const a = [R(), R(), R()], l = Math.hypot(...a) || 1, sp = 4 + Math.random() * 9;
    if (i % 4) blood.spawn(c[0], c[1], c[2], (a[0] / l) * sp, (a[1] / l) * sp + 1.5, (a[2] / l) * sp, 0.3 + Math.random() * 0.35, 0.16, 0.03, P.glow, P.red, 1, 7, 1.4);
    else glow.spawn(c[0], c[1], c[2], (a[0] / l) * sp, (a[1] / l) * sp + 1.5, (a[2] / l) * sp, 0.2 + Math.random() * 0.25, 0.08, 0.015, P.core, P.glow, 1, 7, 1.4);
  }
  flash(sprite(P.glow, 1, 0.55), c, 0.55, 1.2, 6); // the slight red glow
  flash(sprite(P.core, 1, 0.8, true), c, 0.12, 0.4, 1.8); // white-hot at the very middle, for a blink
  ring(c, P);
  if (g) splatter(c, P);
}
function ring(c, P) { // the blast radius, on the floor
  const fl = raycast(c, [0, -1, 0], 4, BOXES);
  flash(new THREE.Mesh(geo().ring, haze(P.glow, 0.9)), [c[0], fl ? fl.point[1] + 0.06 : c[1], c[2]], 0.3, 0.3, W.blastR, true);
}
function splatter(c, P) {
  for (let i = 0; i < 18; i++) {
    const d = i < 5 ? [R(0.35), -1, R(0.35)] : [R(), R() * 0.7 - 0.15, R()];
    const l = Math.hypot(...d) || 1;
    const h = raycast(c, [d[0] / l, d[1] / l, d[2] / l], 5.5, BOXES);
    if (h) decal(h.point, h.normal, (0.35 + Math.random() * 0.55) * (1.3 - h.t / 5.5), P);
  }
}
function decal(p, n, sz, P) {
  let d = splats.length >= 70 ? splats.shift() : null; // reuse the oldest
  if (!d) {
    d = { mesh: new THREE.Mesh(geo().plane, new THREE.MeshBasicMaterial({ map: splatTexture(), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 })) };
    scene.add(d.mesh);
  }
  const m = d.mesh;
  m.material.color.setHex(P.splat);
  m.material.opacity = 0.95;
  m.position.set(p[0] + n[0] * 0.015, p[1] + n[1] * 0.015, p[2] + n[2] * 0.015);
  m.lookAt(m.position.x + n[0], m.position.y + n[1], m.position.z + n[2]);
  m.rotateZ(Math.random() * Math.PI * 2);
  m.scale.set(sz, sz, 1);
  d.life = 12;
  splats.push(d);
}

// ------------------------------------------------------------ walls + floors: an X that fizzles out
function wallX(m, P) {
  const n = m.n || [0, 1, 0], p = [m.p[0] - n[0] * (W.r - 0.02), m.p[1] - n[1] * (W.r - 0.02), m.p[2] - n[2] * (W.r - 0.02)]; // the bolt stops r short of the wall
  const grp = new THREE.Group();
  grp.position.set(p[0], p[1], p[2]);
  grp.lookAt(p[0] + n[0], p[1] + n[1], p[2] + n[2]);
  grp.rotateZ(R(0.08)); // a cross stands (nearly) upright
  const x = makeX(P, 0.95, 0.1);
  x.position.z = 0.02; x.scale.setScalar(0.001);
  grp.add(x);
  scene.add(grp);
  walls.push({ grp, x, t: 0, P, n, p });
  sfx.bcStick(p);
  spurt(p, P, 6, n, 0.6);
  if (gore()) decal(p, n, 0.55, P); // it leaves a stain when it goes
}
function tickWall(w, dt) {
  w.t += dt;
  const t = w.t;
  w.x.scale.setScalar(t < 0.08 ? (t / 0.08) * 1.25 : t < 0.7 ? 1 + 0.08 * Math.sin(t * 25) : Math.max(0.001, 1 - (t - 0.7) / 0.3));
  if (t > 0.6 && Math.random() < dt * 40) blood.spawn(w.p[0] + R(0.2), w.p[1] + R(0.2), w.p[2] + R(0.2), w.n[0] + R(0.8), w.n[1] + R(0.8) + 0.5, w.n[2] + R(0.8), 0.25, 0.07, 0.02, w.P.glow, w.P.red, 1, 2, 1); // sizzle
  if (t < 1) return false;
  for (let i = 0; i < 14; i++) blood.spawn(w.p[0] + w.n[0] * 0.1, w.p[1] + w.n[1] * 0.1, w.p[2] + w.n[2] * 0.1, w.n[0] * 1.2 + R(0.8), w.n[1] * 1.2 + R(0.8) + 0.4, w.n[2] * 1.2 + R(0.8), 0.5 + Math.random() * 0.4, 0.12, 0.45, w.P.mist, w.P.dark, 0.6, -0.5, 2); // the puff
  for (let i = 0; i < 8; i++) blood.spawn(w.p[0], w.p[1], w.p[2], w.n[0] * 2 + R(2), w.n[1] * 2 + R(2), w.n[2] * 2 + R(2), 0.25, 0.1, 0.02, w.P.glow, w.P.red, 1, 0, 2);
  sfx.bcFizzle(w.p);
  scene.remove(w.grp); dispose(w.grp);
  return true;
}

// ------------------------------------------------------------ kills pay the blood back: it flies back into the hand that spilled it
function stream(a, b, P) {
  for (let i = 0; i < 46; i++) {
    const life = 0.35 + Math.random() * 0.35, s = [a[0] + R(0.4), a[1] + R(0.4), a[2] + R(0.4)];
    (i % 5 ? blood : glow).spawn(s[0], s[1], s[2], (b[0] - s[0]) / life, (b[1] - s[1]) / life, (b[2] - s[2]) / life, life, i % 5 ? 0.16 : 0.06, 0.04, i % 5 ? P.glow : P.core, i % 5 ? P.red : P.glow, 1, 0, 0);
  }
}
function floatText(text, color) {
  const box = document.getElementById('nums');
  if (!box) return;
  const d = document.createElement('div');
  d.className = 'num'; d.textContent = text;
  d.style.left = innerWidth / 2 - 45 + 'px'; d.style.top = innerHeight * 0.45 + 'px'; d.style.color = color; d.style.fontSize = '30px';
  box.append(d);
  setTimeout(() => d.remove(), 900);
}
function refund(m, ghosts, info) {
  const P = palOf(m.o, info), tg = who(m.o, ghosts);
  let to = null;
  if (tg.me) { const c = Math.cos(ME.yaw), s = Math.sin(ME.yaw); to = [ME.pos[0] + c * 0.3 - s * 0.5, ME.pos[1] + 1.2, ME.pos[2] - s * 0.3 - c * 0.5]; } // your hand, low right
  else if (tg.r && tg.r.alive) to = tg.r.muzzle();
  if (to && Array.isArray(m.p)) stream(m.p, to, P);
  if (tg.me && m.a > 0) { floatText(`+${m.a} HP`, '#7dff4f'); sfx.bcRefund(); }
}

// ------------------------------------------------------------ you got crossed: you can't see your own body, so it's on your screen
const ov = {
  el: null, bars: null, on: false, t: 0, te: -1, tb: -1, fuse: 0.6, P: PAL.blood,
  make() {
    const host = document.getElementById('hud');
    if (this.el || !host) return !!this.el;
    this.el = document.createElement('div');
    this.el.id = 'crossFx';
    this.el.style.cssText = 'position:absolute;inset:0;pointer-events:none;opacity:0;overflow:hidden;';
    this.bars = [-1, 1].map((s) => { const b = document.createElement('div'); b.style.cssText = `position:absolute;left:50%;top:50%;border-radius:999px;transform:translate(-50%,-50%) rotate(${s * 45}deg);`; this.el.append(b); return b; });
    host.append(this.el);
    return true;
  },
  start(mk) { Object.assign(this, { on: true, t: 0, te: -1, tb: -1, fuse: mk.fuse, P: mk.pal }); },
  erupt() { if (this.on) this.te = 0; },
  boom() { if (this.on) this.tb = 0; },
  tick(dt) {
    if (!this.on || !this.make()) return;
    this.t += dt;
    if (this.te >= 0) this.te += dt;
    if (this.tb >= 0) this.tb += dt;
    const diag = Math.hypot(innerWidth, innerHeight);
    let size, th, op;
    if (this.tb >= 0) { const k = Math.max(0, 1 - this.tb / 0.6); size = diag * (1.05 + this.tb * 0.4); th = 6 + 40 * k; op = k; }
    else if (this.te >= 0) { const k = Math.min(1, this.te / 0.07); size = 120 + (diag * 1.05 - 120) * k; th = 10 + 30 * k; op = 0.95; }
    else { const k = Math.min(1, this.t / this.fuse); size = 70 + 60 * k; th = 7 + 4 * k; op = 0.45 + 0.45 * Math.abs(Math.sin(this.t * (8 + 16 * k))); }
    const c = this.P.css;
    for (const b of this.bars) {
      b.style.width = size + 'px'; b.style.height = th + 'px'; b.style.background = `rgb(${c})`;
      b.style.boxShadow = `0 0 ${th}px ${th * 0.4}px rgba(${c},0.8), 0 0 ${th * 3}px ${th}px rgba(${c},0.3)`;
    }
    this.el.style.opacity = op;
    this.el.style.background = this.tb >= 0 ? `rgba(${c},${0.35 * Math.max(0, 1 - this.tb / 0.4)})` : 'transparent';
    if (this.tb > 0.6 || this.t > this.fuse + W.burst + 3) { this.on = false; this.el.style.opacity = 0; }
  },
};

// ------------------------------------------------------------ events + frame
export function crossEvent(m, ghosts, info) {
  if (!scene || !m) return;
  const key = (ghosts ? 'r' : 'l') + m.id;
  if (m.k === 'stick') stick(m, key, ghosts, info);
  else if (m.k === 'erupt' || m.k === 'boom') {
    let mk = marks.get(key);
    if (!mk && Array.isArray(m.p)) { // missed the stick (just joined): show the rest where the server says it is
      mk = newMark(key, m, info);
      if (who(m.to, ghosts).me) { mk.me = true; ov.start(mk); } else loose(mk, m.p);
      mk.t = mk.fuse;
      marks.set(key, mk);
    }
    if (!mk) return;
    if (Array.isArray(m.p)) mk.p = m.p;
    if (m.k === 'erupt') erupt(mk); else boom(mk);
  } else if (m.k === 'wall' && Array.isArray(m.p)) wallX(m, palOf(m.o, info));
  else if (m.k === 'refund') refund(m, ghosts, info);
  else if (!ghosts && m.o === G.myId && m.k === 'refill') { floatText(`+${m.a} HP`, '#ff8a9a'); sfx.heal(); }
  else if (!ghosts && m.o === G.myId && m.k === 'dry') { /* thin blood: the shot still went (weapons.js says so on the HUD) */ }
}

// rpSp: how fast a replay is playing (0.3 in slow-mo). crosses from a replay ('r' keys) live on its clock, so a mark can't
// time out before its pop plays, and the spikes burst out in slow motion with the ghost they're in
export function updateCrosses(dt, rpSp = 1) {
  if (!scene) return;
  blood.update(dt); glow.update(dt);
  bolts();
  for (let i = bangs.length - 1; i >= 0; i--) {
    const b = bangs[i], t = (b.t += dt);
    b.u.thumb.rotation.x = t < 0.03 ? -0.95 * (t / 0.03) : t < 0.1 ? -0.95 : t < 0.3 ? -0.95 * (1 - (t - 0.1) / 0.2) : 0;
    b.u.index.rotation.x = t < 0.15 ? 0.25 * Math.sin((t / 0.15) * Math.PI) : 0;
    if (b.u.flare) { b.u.flare.visible = t < 0.07; b.u.flare.userData.face.rotation.z = Math.random() * 6.28; } // the red burst off their fingertip
    if (t >= 0.3) bangs.splice(i, 1);
  }
  for (const mk of [...marks.values()]) tickMark(mk, mk.key[0] === 'r' ? dt * rpSp : dt);
  for (let i = walls.length - 1; i >= 0; i--) if (tickWall(walls[i], dt)) walls.splice(i, 1);
  for (let i = fades.length - 1; i >= 0; i--) {
    const f = fades[i];
    f.life -= dt;
    const k = 1 - Math.max(0, f.life / f.ml);
    f.obj.material.opacity = f.op * (1 - k) * (1 - k);
    if (f.s1 != null) { const s = f.s0 + (f.s1 - f.s0) * (1 - (1 - k) * (1 - k)); if (f.flat) f.obj.scale.set(s, 1, s); else f.obj.scale.setScalar(s); }
    if (f.life > 0) continue;
    scene.remove(f.obj);
    if (f.beam) f.beam.push(f.obj); else f.obj.material.dispose();
    fades.splice(i, 1);
  }
  for (let i = splats.length - 1; i >= 0; i--) {
    const d = splats[i];
    d.life -= dt;
    if (d.life < 2) d.mesh.material.opacity = Math.max(0, d.life / 2) * 0.95;
    if (d.life <= 0) { scene.remove(d.mesh); d.mesh.material.dispose(); splats.splice(i, 1); }
  }
  ov.tick(dt);
}

export function clearCrosses() {
  if (!scene) return;
  for (const mk of [...marks.values()]) dropMark(mk);
  for (const w of walls) { scene.remove(w.grp); dispose(w.grp); }
  walls.length = 0;
  for (const f of fades) { scene.remove(f.obj); if (f.beam) f.beam.push(f.obj); else f.obj.material.dispose(); }
  fades.length = 0;
  for (const d of splats) { scene.remove(d.mesh); d.mesh.material.dispose(); }
  splats.length = 0;
  for (const b of bangs) { b.u.thumb.rotation.x = 0; b.u.index.rotation.x = 0; if (b.u.flare) b.u.flare.visible = false; }
  bangs.length = 0;
  ov.on = false;
  if (ov.el) ov.el.style.opacity = 0;
}
