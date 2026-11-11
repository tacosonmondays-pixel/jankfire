// Zombies on your screen: limbs coming off (the arm flies away still twitching, a stump is left, blood everywhere),
// legless ones dragging themselves along, one-legged ones hopping, and the special zombies' looks: Chonk's belly,
// Ankle Biters, Hard Hats (the hat dinks, then flies), the Screamer. The server decides all of it (server/zmlimbs.js);
// this draws it and shapes what you can hit to match.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { ME } from './player.js';
import { M, freeTree } from './models.js';
import { authored, nodeIn, AUTHORED, prefetch } from './glbkit.js';
import { BOXES, MAPS } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { ZL, ZL_ARMS, ZT, ZT_IDS, zlCrawl, zlHop } from '/shared/zmlimbs.js';

const ST = new Map(); // id -> [type id, limbs gone, flags] (from every snapshot)
const fly = []; // severed bits in the air / on the floor
const rings = []; // a Screamer's shriek
const PART = { [ZL.armL]: 'armL', [ZL.armR]: 'arm', [ZL.legL]: 'legL', [ZL.legR]: 'legR', [ZL.head]: 'head' };
const JOINT = { [ZL.armL]: [-0.25, 1.45, 0], [ZL.armR]: [0.25, 1.45, 0], [ZL.legL]: [-0.1, 0.9, 0], [ZL.legR]: [0.1, 0.9, 0], [ZL.head]: [0, 1.6, 0] };
const R = (k) => (Math.random() - 0.5) * 2 * k;
const pick = (a) => a[(Math.random() * a.length) | 0];
const tmpP = new THREE.Vector3(), tmpQ = new THREE.Quaternion(), tmpS = new THREE.Vector3();
const mesh = (geo, color) => new THREE.Mesh(geo, M(color));
const floorAt = (p) => { const h = raycast([p[0], p[1] + 0.6, p[2]], [0, -1, 0], 30, BOXES); return h ? h.point[1] : p[1]; };
const isZ = (r) => !!(r && r.bot && r.name === 'Zombie');

export const zlType = (r) => { const s = ST.get(r.id); return s ? ZT_IDS[s[0]] || '' : ''; };
export const zlMask = (r) => { const s = ST.get(r.id); return s ? s[1] : 0; };
let asked = false, askedMap = '';
export function zlSync(info) { // zombies.js, every frame: what the server says about each one
  bossBar(info);
  if (!asked) { asked = true; prefetch(['z_plain', 'z_stump', ...Object.keys(ZT).map((k) => 'z_' + k)], 3); } // the Blender zombies jump the download queue
  const mz = MAPS[G.cfg && G.cfg.map] && MAPS[G.cfg.map].zm; // ... and this map's own crowd
  if (mz && mz.skins && askedMap !== G.cfg.map) { askedMap = G.cfg.map; prefetch(mz.skins.map((k) => 'z_' + k), 3); }
  ST.clear();
  for (const e of (info && info.lb) || []) ST.set(e[0], [e[1], e[2], e[3]]);
}

// ------------------------------------------------------------ a bit comes off
// the real limb leaves the body (an empty stand-in takes its place, so the walk cycle has something to wave) and
// tumbles away on its own. quiet: it was already gone when we first saw this zombie
function cut(r, bit, dir, quiet) {
  const ch = r.ch, key = PART[bit];
  if (!ch || !key || (ch.zlGone & bit)) return;
  ch.zlGone = (ch.zlGone || 0) | bit;
  const part = ch[key];
  ch.root.updateMatrixWorld(true);
  const part0 = ch[key], j = bit === ZL.head ? JOINT[bit] : [part0.position.x, JOINT[bit][1], 0], at = tmpP.set(j[0], j[1], j[2]).applyMatrix4(ch.body.matrixWorld).toArray();
  const stand = new THREE.Group(); stand.position.copy(part.position); stand.userData.zlKeep = true;
  if (key === 'arm') stand.add(ch.slot); // (the hand slot stays with the mannequin)
  ch[key] = stand; ch.body.add(stand);
  if (quiet || !part.parent) { part.removeFromParent(); freeTree(part); }
  else {
    G.scene.attach(part); // keeps where it is in the world
    const d = dir || [0, 0.3, 0], sp = 4 + Math.random() * 4;
    fly.push({ m: part, v: [d[0] * sp + R(2), 3.5 + Math.random() * 3.5 + d[1] * 2, d[2] * sp + R(2)], av: [R(9), R(9), R(9)], life: 7 + Math.random() * 3, floorY: floorAt(at), drip: 0, tw: Math.random() * 6, kn: key === 'legL' ? ch.kneeL : key === 'legR' ? ch.kneeR : null, rest: bit === ZL.head ? 0.16 : 0.07 });
    if (fly.length > 40) drop(0);
    if (G.settings.blood !== false) fx.blood(at, [d[0], 0.4, d[2]], 34, floorAt(at));
    sfx.zmLimb(at, bit === ZL.head);
  }
  const so = authored('z_stump'); // the empty socket (Blender), turned to face where the limb was
  if (so) {
    const n = so.obj; n.position.set(j[0], j[1], j[2]);
    if (bit & ZL_ARMS) n.rotation.z = bit === ZL.armL ? Math.PI / 2 : -Math.PI / 2; else if (bit !== ZL.head) n.rotation.x = Math.PI;
    n.scale.setScalar(bit === ZL.head ? 0.8 : bit & ZL_ARMS ? 1 : 1.25);
    n.traverse((o) => { if (o.isMesh) o.material = plain(o.material); });
    n.userData.zlKeep = true; ch.body.add(n);
    return;
  }
  // the stump: a ragged red end where it was (and a bit of bone)
  const st = new THREE.Group(); st.position.set(j[0], j[1], j[2]);
  const meat = mesh(new THREE.IcosahedronGeometry(bit === ZL.head ? 0.06 : 0.075, 0), 0x8a0a0a); meat.scale.set(1, 0.7, 1); st.add(meat);
  const bone = mesh(new THREE.CylinderGeometry(0.02, 0.025, 0.09, 5), 0xe8e0c8);
  if (bit & ZL_ARMS) { bone.rotation.z = Math.PI / 2; bone.position.x = bit === ZL.armL ? -0.05 : 0.05; } else bone.position.y = bit === ZL.head ? 0.05 : -0.05;
  st.add(bone);
  ch.body.add(st);
}
function drop(i) { const f = fly[i]; G.scene.remove(f.m); freeTree(f.m); fly.splice(i, 1); }

// ------------------------------------------------------------ the Blender zombies (tools/blender/make_zombies.py)
// public/models/z_<kind>.glb: the mannequin as part_<joint> nodes, each with its origin on the joint. every part goes
// into the same joint group of the code mannequin (whose own boxes and balls come out), so the walk, the crawl and
// limbs popping off all still work on it. skin / top / bottom are tinted to this zombie's colours. no file = the code one
const JOINTS = ['body', 'head', 'arm', 'armL', 'legL', 'legR', 'kneeL', 'kneeR'];
const tints = new Map(), plains = new WeakMap(), hulls = new Map();
function tinted(m, base, want) { // the material, repainted from the colour it was made in to this zombie's
  const key = m.uuid + want;
  if (!tints.has(key)) {
    const c = m.clone(), b = new THREE.Color(base), w = new THREE.Color(want);
    c.color.setRGB(Math.min(4, w.r / Math.max(0.01, b.r)), Math.min(4, w.g / Math.max(0.01, b.g)), Math.min(4, w.b / Math.max(0.01, b.b)));
    c.fog = false; c.onBeforeCompile = () => {}; c.customProgramCacheKey = () => 'zskin';
    tints.set(key, c);
  }
  return tints.get(key);
}
function plain(m) { // like every other player: no fog, no potato wobble (it mushes them far away)
  if (!plains.has(m)) { const c = m.clone(); c.fog = false; c.onBeforeCompile = () => {}; c.customProgramCacheKey = () => 'zskin'; plains.set(m, c); }
  return plains.get(m);
}
function hull(color) { // the outline: the same mesh drawn inside out, pushed out along its normals
  if (!hulls.has(color)) {
    const m = new THREE.MeshBasicMaterial({ color, side: THREE.BackSide, fog: false });
    m.onBeforeCompile = (sh) => { sh.vertexShader = sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n transformed += normalize(normal) * 0.024;'); };
    m.customProgramCacheKey = () => 'zhull';
    hulls.set(color, m);
  }
  return hulls.get(color);
}
// which model a zombie wears: its special type's, else its map's own crowd (look.zs, from the server), else the plain one
const skinId = (r, ty) => { const zs = !ty && r.outfit && typeof r.outfit.zs === 'string' && /^[a-z]{1,16}$/.test(r.outfit.zs) ? r.outfit.zs : ''; return 'z_' + (ty || (zs && AUTHORED['z_' + zs] ? zs : '') || 'plain'); };
function skin(r, ty) {
  const ch = r.ch, a = authored(skinId(r, ty));
  if (!a) return false;
  const obj = a.obj, meta = a.meta || {}, lk = r.outfit || {}, tint = meta.tint || {};
  const want = { z_skin: lk.skin, z_top: lk.topColor, z_bot: lk.bottomColor }, out = hull(new THREE.Color(r.color).getHex());
  const keep = new Set([ch.legL, ch.legR, ch.kneeL, ch.kneeR, ch.head, ch.arm, ch.armL, ch.slot]);
  const parts = JOINTS.map((k) => [k, nodeIn(obj, 'part_' + k)]);
  if (parts.some(([, n]) => !n)) return false;
  const off = { arm: ZL.armR, armL: ZL.armL, legL: ZL.legL, kneeL: ZL.legL, legR: ZL.legR, kneeR: ZL.legR, head: ZL.head }, gone = ch.zlGone || 0;
  for (const [k, node] of parts) {
    const g = ch[k];
    if (off[k] & gone) continue; // already lost that one
    for (const c of [...g.children]) if (!keep.has(c) && !c.userData.zlKeep) { g.remove(c); freeTree(c); } // the code mannequin's own pieces
    node.position.set(0, 0, 0); g.add(node);
  }
  for (const [k, at] of Object.entries(meta.joints || {})) if (ch[k] && k !== 'kneeL' && k !== 'kneeR') ch[k].position.x = at[0]; // (a Chonk's hips and shoulders are wider)
  const extra = (name, at) => { const n = nodeIn(obj, name); if (n && at) { n.position.set(at[0], at[1], at[2]); ch.head.add(n); } return n && at ? n : null; };
  ch.zlHat = extra('part_hat', meta.hat);
  ch.zlJawN = extra('part_jaw', meta.jaw);
  const meshes = [];
  ch.body.traverse((o) => { if (o.isMesh && !o.userData.outline) meshes.push(o); });
  for (const o of meshes) {
    const base = Object.keys(tint).find((n) => o.material.name && o.material.name.startsWith(n));
    o.material = base && want[base] ? tinted(o.material, tint[base], want[base]) : plain(o.material);
    const sh = new THREE.Mesh(o.geometry, out); sh.userData.outline = true; o.add(sh);
  }
  r.shells = (r.shells || []).filter((sh) => { let p = sh; while (p && p !== ch.root) p = p.parent; return !!p; }); // (the old outlines went with the old pieces)
  ch.body.scale.set(1, 1, 1);
  ch.zlGlb = true; ch.zlSkinId = skinId(r, ty);
  return true;
}

// ------------------------------------------------------------ the specials' looks (added on top of the mannequin)
function dress(r, ty) {
  const ch = r.ch, def = ZT[ty];
  r.zmK = (def && def.scale) || 1; // remote.js: drawn (and hit-tested) this much bigger
  if (skin(r, ty)) return; // the Blender one. below: the code stand-ins, if its file didn't load
  if (!def) return;
  if (ty === 'chonk') {
    ch.body.scale.set(1.55, 0.86, 1.6); // wide and squat
    const skin = r.outfit && r.outfit.skin ? new THREE.Color(r.outfit.skin).getHex() : 0x7f9f4a;
    const belly = mesh(new THREE.SphereGeometry(0.34, 9, 7), skin); belly.position.set(0, 1.14, -0.08); belly.scale.set(1, 1.05, 0.95); ch.body.add(belly);
    const button = mesh(new THREE.SphereGeometry(0.03, 5, 4), 0x3a4a22); button.position.set(0, 1.08, -0.4); ch.body.add(button);
    for (const [x, y, z, k] of [[0.2, 1.34, -0.2, 1], [-0.16, 0.98, -0.34, 0.75], [-0.24, 1.3, 0.12, 0.9], [0.1, 0.92, -0.33, 0.55]]) { // it's full of something purple
      const boil = new THREE.Mesh(new THREE.SphereGeometry(0.075, 6, 5), M(0xb07dff, true)); boil.position.set(x, y, z); boil.scale.setScalar(k); ch.body.add(boil);
    }
    ch.zlBelly = belly;
  }
  if (ty === 'biter') { // all mouth
    const jaw = new THREE.Group(); jaw.position.set(0, 0.06, -0.1);
    for (let i = -2; i <= 2; i++) for (const up of [1, -1]) { const t = mesh(new THREE.ConeGeometry(0.018, 0.05, 4), 0xfff8e0); t.position.set(i * 0.035, up * 0.022, -0.035 + Math.abs(i) * 0.012); t.rotation.x = up > 0 ? Math.PI : 0; jaw.add(t); }
    const gob = mesh(new THREE.BoxGeometry(0.2, 0.07, 0.04), 0x2a0808); gob.position.z = -0.012; jaw.add(gob);
    ch.head.add(jaw); ch.zlJaw = jaw;
  }
  if (ty === 'hardhat') {
    const hat = new THREE.Group(); hat.position.set(0, 0.25, 0);
    const dome = mesh(new THREE.SphereGeometry(0.155, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), 0xffd21f); dome.scale.set(1, 0.85, 1.12); hat.add(dome);
    const brim = mesh(new THREE.CylinderGeometry(0.19, 0.19, 0.02, 12), 0xffd21f); brim.scale.z = 1.18; brim.position.z = -0.03; hat.add(brim);
    const ridge = mesh(new THREE.BoxGeometry(0.035, 0.03, 0.3), 0xffe98a); ridge.position.y = 0.125; hat.add(ridge);
    ch.head.add(hat); ch.zlHat = hat;
    // hi-vis vest, two silver stripes
    const vest = mesh(new THREE.BoxGeometry(0.47, 0.42, 0.3), 0xff7a1a); vest.position.set(0, 1.3, 0); ch.body.add(vest);
    for (const sx of [-1, 1]) { const s = mesh(new THREE.BoxGeometry(0.06, 0.43, 0.31), 0xdfe6ea); s.position.set(sx * 0.11, 1.3, 0); ch.body.add(s); }
    const band = mesh(new THREE.BoxGeometry(0.48, 0.05, 0.31), 0xdfe6ea); band.position.set(0, 1.16, 0); ch.body.add(band);
  }
  if (ty === 'screamer') { // a mouth that's far too big
    const mouth = mesh(new THREE.SphereGeometry(0.07, 8, 6), 0x1a0408); mouth.position.set(0, 0.07, -0.115); mouth.scale.set(0.9, 1.25, 0.5); ch.head.add(mouth);
    for (const sx of [-1, 1]) { const eye = new THREE.Mesh(new THREE.SphereGeometry(0.03, 6, 5), M(0xff4fd8, true)); eye.position.set(sx * 0.055, 0.2, -0.12); ch.head.add(eye); }
    ch.zlMouth = mouth;
  }
}

// ------------------------------------------------------------ every frame, every zombie (zombies.js zombiesTick, after its own pose)
// returns true when it posed the body itself (crawling): the shamble doesn't apply
export function zlPose(r, now, dt) {
  const ch = r.ch, s = ST.get(r.id), ty = s ? ZT_IDS[s[0]] || '' : '', mask = s ? s[1] : 0, fl = s ? s[2] : 0;
  if (ch.zlT0 == null) ch.zlT0 = now;
  if (ch.zlTy == null && (ty || now - ch.zlT0 > 350)) { ch.zlTy = ty; dress(r, ty); } // (a special's type rides in the snapshot: give it a moment before calling it plain)
  else if (ch.zlTy === '' && ty) { r.setLook(r.outfit); return false; } // it was special after all: start over on a fresh mannequin
  else if (ch.zlTy != null && (!ch.zlGlb ? AUTHORED[skinId(r, ch.zlTy)] : ch.zlSkinId !== skinId(r, ch.zlTy))) { r.setLook(r.outfit); return false; } // its Blender model (or its map's own one) only just arrived
  if (s) for (const bit of [1, 2, 4, 8, 16]) if ((mask & bit) && !((ch.zlGone || 0) & bit)) cut(r, bit, null, !ch.zlSeen); // (the 'zlb' message usually got there first, with the fling)
  if (s) ch.zlSeen = true;
  if (ch.zlHat && s && !(fl & 1)) hatOff(r, null);
  const gone = ch.zlGone || 0, crawl = zlCrawl(gone), ph = now * 0.006 + r.id;
  r.zmHit = crawl ? crawlBoxes : null;
  if (ch.zlJaw) ch.zlJaw.position.y = 0.06 + Math.abs(Math.sin(now * 0.03 + r.id)) * 0.02; // chattering
  if (ch.zlBelly) ch.zlBelly.scale.y = 1.05 + Math.sin(now * 0.004 + r.id) * 0.06;
  if (fl & 4) { // shrieking: head back, arms up, shaking
    ch.head.rotation.x = -0.75; ch.head.scale.setScalar(1.25 + Math.sin(now * 0.09) * 0.12);
    ch.arm.rotation.x = 1.9; ch.armL.rotation.x = 1.9;
    ch.body.rotation.z = Math.sin(now * 0.08) * 0.07;
    if (ch.zlMouth) ch.zlMouth.scale.set(1.5, 2.1, 0.5);
    if (ch.zlJawN) ch.zlJawN.rotation.x = -0.42 + Math.sin(now * 0.07) * 0.06; // jaw right down
    return true;
  }
  if (ch.zlMouth) ch.zlMouth.scale.set(0.9, 1.25, 0.5);
  if (ch.zlJawN) ch.zlJawN.rotation.x = Math.sin(now * 0.004 + r.id) * 0.05;
  if (crawl) { // face down, dragging itself along by whatever arms are left
    const mv = Math.min(1, Math.hypot(r.vel[0], r.vel[2]) / 0.8), a = Math.sin(ph * 1.6) * mv;
    ch.body.rotation.set(-1.32 + Math.abs(a) * 0.06, a * 0.14, a * 0.1);
    ch.body.position.set(0, -0.03, 1.35); // (chest over where the server has it: head a bit ahead, hips behind)
    ch.arm.rotation.set(1.25 + a * 0.55, 0, 0); ch.armL.rotation.set(1.25 - a * 0.55, 0, 0);
    ch.head.rotation.set(0.95 + Math.sin(ph * 0.7) * 0.15, Math.sin(ph * 0.5) * 0.3, ch.jank.tilt);
    return true;
  }
  if (zlHop(gone)) { // one leg: hop, hop, leaning off the side that's left
    const side = gone & ZL.legL ? 1 : -1, hop = Math.abs(Math.sin(ph * 1.9));
    ch.body.position.y += hop * 0.16 - 0.02;
    ch.body.rotation.z = side * 0.14 + Math.sin(ph * 1.9) * 0.05;
    ch.arm.rotation.z = -0.5 * hop; ch.armL.rotation.z = 0.5 * hop; // arms out for balance
    return false;
  }
  if (fl & 2) ch.body.rotation.x -= 0.18 + Math.sin(now * 0.05 + r.id) * 0.04; // hyped by a Screamer: head down, charging
  return false;
}
// a crawler is flat on the floor: what you can hit is too (remote.js hitboxes; it scales them for distance after)
function crawlBoxes() {
  const [x, y, z] = this.pos, fx0 = -Math.sin(this.yaw), fz0 = -Math.cos(this.yaw);
  const seg = (a, b, r, h0, h1, head) => {
    const ax = x + fx0 * a, az = z + fz0 * a, bx = x + fx0 * b, bz = z + fz0 * b;
    return { head, min: [Math.min(ax, bx) - r, y + h0, Math.min(az, bz) - r], max: [Math.max(ax, bx) + r, y + h1, Math.max(az, bz) + r] };
  };
  return [seg(-0.65, 0.3, 0.4, 0, 0.62, false), seg(0.25, 0.72, 0.3, 0.12, 0.9, true)];
}

// ------------------------------------------------------------ the server's news
function hatOff(r, dir) {
  const ch = r.ch, hat = ch && ch.zlHat;
  if (!hat) return;
  ch.zlHat = null;
  ch.root.updateMatrixWorld(true);
  const at = hat.getWorldPosition(tmpP).toArray();
  G.scene.attach(hat);
  const d = dir || [R(1), 0, R(1)];
  fly.push({ m: hat, v: [d[0] * 5 + R(2), 7 + Math.random() * 3, d[2] * 5 + R(2)], av: [R(14), R(6), R(14)], life: 8, floorY: floorAt(at), drip: -1, tw: 0, kn: null, rest: 0.03 });
}
net.on('zlb', (m) => {
  if (!m || typeof m !== 'object') return;
  const r = G.remotes.get(m.id), d = Array.isArray(m.d) && m.d.length === 3 && m.d.every(Number.isFinite) ? m.d : null;
  if (m.k === 'cut' && isZ(r) && r.ch && PART[m.l]) {
    const had = r.ch.zlGone || 0;
    cut(r, m.l, d, false);
    r.ch.zlSeen = true;
    if (m.by === G.myId && !m.x) { // your work
      const gone = r.ch.zlGone || 0;
      if (zlCrawl(gone) && !zlCrawl(had)) hud.msg(pick(['LEGLESS', 'NO LEGS', 'FLOOR GANG', 'WALK IT OFF']), 1.1, 'brag');
      else if ((gone & ZL_ARMS) === ZL_ARMS && (had & ZL_ARMS) !== ZL_ARMS) hud.msg(pick(['DISARMED', 'NO HANDS', 'HUGS CANCELLED']), 1.1, 'brag');
    }
  } else if (m.k === 'dink' && r) { sfx.zmDink(r.pos); sparks(r, 5); }
  else if (m.k === 'hat' && isZ(r)) { sfx.zmDink(r.pos, true); sparks(r, 12); hatOff(r, d); }
  else if (m.k === 'scream' && Array.isArray(m.a) && m.a.every(Number.isFinite)) scream(m.a);
  else if (bossNews(m, r)) { /* a mini boss */ }
  else if (m.k === 'pop' && Array.isArray(m.a) && m.a.every(Number.isFinite)) pop(m.a);
});
function sparks(r, n) {
  const P = fx.parts().fire, k = (r.zmK || 1) * 1.2, y = r.pos[1] + 2.1 * k;
  for (let i = 0; i < n; i++) P.spawn(r.pos[0], y, r.pos[2], R(5), 2 + Math.random() * 4, R(5), 0.25 + Math.random() * 0.2, 0.09, 0.02, 0xfff2a0, 0xff9a20, 1, 14, 1);
}
function scream(a) {
  sfx.zmScream(a);
  for (let i = 0; i < 3; i++) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(1, 0.045, 5, 28), new THREE.MeshBasicMaterial({ color: 0xff4fd8, transparent: true, opacity: 0.9, depthWrite: false }));
    ring.rotation.x = Math.PI / 2; ring.position.set(a[0], a[1] - 0.6 + i * 0.25, a[2]);
    G.scene.add(ring); rings.push({ m: ring, t: -i * 0.16, r: ZT.screamer.reach });
  }
  const d = Math.hypot(a[0] - ME.pos[0], a[2] - ME.pos[2]);
  if (d < 22 && G.settings.shake !== false) G.shake = Math.max(G.shake, 0.35 * (1 - d / 22));
}
function pop(a) {
  sfx.zmPop(a);
  const P = fx.parts(), fl = floorAt(a);
  for (let i = 0; i < 46; i++) { const an = Math.random() * 6.283, sp = 3 + Math.random() * 9; P.misc.spawn(a[0], a[1] + 1, a[2], Math.cos(an) * sp, 2 + Math.random() * 9, Math.sin(an) * sp, 0.7 + Math.random() * 0.6, 0.22 + Math.random() * 0.2, 0.05, Math.random() < 0.4 ? 0xb07dff : 0x7dff4f, 0x2a5a10, 1, 20, 0.6); }
  for (let i = 0; i < 10; i++) P.smoke.spawn(a[0] + R(1), a[1] + 0.8 + R(0.5), a[2] + R(1), R(3), 1 + Math.random() * 2, R(3), 1.1 + Math.random() * 0.6, 0.6, 2.2, 0x9aff6a, 0x3a6a20, 0.5, -0.4, 0.8);
  if (G.settings.blood !== false) for (let i = 0; i < 3; i++) fx.blood([a[0] + R(1.5), a[1] + 1, a[2] + R(1.5)], [R(1), 0.5, R(1)], 30, fl);
  const d = Math.hypot(a[0] - ME.pos[0], a[2] - ME.pos[2]);
  if (d < 16 && G.settings.shake !== false) G.shake = Math.max(G.shake, 0.9 * (1 - d / 16));
  if (d < ZT.chonk.blast) hud.msg('CHONK POPPED', 1.2, 'brag');
}

// ------------------------------------------------------------ mini bosses: the callouts, the bar, the floor rippling
const BOSS_LINES = {
  manager: { in: 'THE FLOOR MANAGER HAS CLOCKED IN', out: 'MANAGER FIRED', meet: 'MEETING. NOW.' },
  mascot: { in: 'THE MASCOT WANTS A HUG', out: 'MASCOT RETIRED' },
};
const v3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);
function ring(a, r, color, secs = 0.7, y = 0.15) { // a ring on the floor growing out to r
  const m = new THREE.Mesh(new THREE.TorusGeometry(1, 0.06, 5, 36), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9, depthWrite: false, fog: false }));
  m.rotation.x = Math.PI / 2; m.position.set(a[0], a[1] + y, a[2]);
  G.scene.add(m); rings.push({ m, t: 0, r, secs });
}
function bossNews(m, r) {
  const L = BOSS_LINES[m.ty] || (r && BOSS_LINES[zlType(r)]) || {};
  if (m.k === 'bosswarn') { hud.msg('BOSS ROUND', 2.2, 'brag'); sfx.zmBossIn(); return true; }
  if (m.k === 'boss') { if (L.in) hud.msg(L.in, 2.6, 'brag'); sfx.zmBossIn(r ? r.pos : null); return true; }
  if (m.k === 'meeting' && v3(m.a)) { scream(m.a); if (L.meet && Math.hypot(m.a[0] - ME.pos[0], m.a[2] - ME.pos[2]) < 30) hud.msg(L.meet, 1.4, 'brag'); return true; }
  if (m.k === 'charge' && r) { sfx.zmCharge(r.pos); ring(r.pos, 2.4, 0xff3030, 0.8); return true; }
  if (m.k === 'jump' && r) { sfx.zmCharge(r.pos); if (v3(m.to)) ring(m.to, 6.5, 0x4fd8ff, Math.max(0.3, (m.ms || 900) / 1000), 0.08); return true; } // where it's coming down
  if (m.k === 'slam' && v3(m.a)) {
    const rr = Number.isFinite(m.r) ? Math.min(12, m.r) : 6;
    sfx.zmPop(m.a); ring(m.a, rr, 0xffe14d, 0.5); ring(m.a, rr * 0.6, 0xff4fd8, 0.5);
    const P = fx.parts().smoke;
    for (let i = 0; i < 18; i++) { const an = (i / 18) * 6.283; P.spawn(m.a[0] + Math.cos(an) * 1.2, m.a[1] + 0.3, m.a[2] + Math.sin(an) * 1.2, Math.cos(an) * 7, 1.5, Math.sin(an) * 7, 0.8, 0.5, 1.8, 0xd8d0c0, 0x8a8478, 0.5, -0.5, 1.2); }
    const d = Math.hypot(m.a[0] - ME.pos[0], m.a[2] - ME.pos[2]);
    if (d < 20 && G.settings.shake !== false) G.shake = Math.max(G.shake, 1.1 * (1 - d / 20));
    return true;
  }
  if (m.k === 'bossdead' && v3(m.a)) {
    hud.msg(L.out || 'BOSS DOWN', 2.6, 'brag'); sfx.zmBossOut(m.a);
    const P = fx.parts().fire, cols = [0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f];
    for (let i = 0; i < 90; i++) { const an = Math.random() * 6.283, up = Math.random() * 12, sp = 3 + Math.random() * 9; P.spawn(m.a[0], m.a[1] + 1, m.a[2], Math.cos(an) * sp, 3 + up, Math.sin(an) * sp, 0.9 + Math.random() * 0.8, 0.22, 0.04, cols[i % 4], cols[(i + 1) % 4], 1, 16, 0.6); }
    return true;
  }
  return false;
}
let bar = null, barK = '';
function bossBar(info) { // a long HP bar under the round line while one's alive
  const bs = info && info.bs, def = bs && ZT[bs[1]];
  const key = def ? `${bs[1]}|${Math.round((bs[2] / Math.max(1, bs[3])) * 200)}` : '';
  if (key === barK) return;
  barK = key;
  if (!bar) { bar = document.createElement('div'); bar.id = 'zbBar'; bar.style.cssText = 'position:fixed;left:50%;top:64px;transform:translateX(-50%) rotate(-0.6deg);width:min(520px,60vw);pointer-events:none;z-index:6;font-family:"Comic Sans MS","Comic Neue",cursive;text-align:center;'; document.body.appendChild(bar); }
  bar.innerHTML = def ? `<div style="color:#ffe14d;font-weight:bold;font-size:17px;text-shadow:2px 2px 0 #120818;letter-spacing:1px">${def.name}</div><div style="height:16px;background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:6px 6px 0 #4fd8ff"><div style="height:100%;width:${Math.max(0, Math.min(100, (bs[2] / Math.max(1, bs[3])) * 100)).toFixed(1)}%;background:#ff3030"></div></div>` : '';
}

// ------------------------------------------------------------ every frame: loose limbs, hats, shriek rings
export function zlTick(dt) {
  for (let i = fly.length - 1; i >= 0; i--) {
    const f = fly[i], p = f.m.position;
    f.life -= dt;
    f.v[1] -= 22 * dt;
    p.x += f.v[0] * dt; p.y += f.v[1] * dt; p.z += f.v[2] * dt;
    const low = f.floorY + f.rest;
    if (p.y < low) {
      p.y = low;
      const hard = Math.abs(f.v[1]) > 3;
      f.v[1] = Math.abs(f.v[1]) * 0.32; f.v[0] *= 0.55; f.v[2] *= 0.55;
      f.av = f.av.map((a) => a * 0.5);
      if (hard && f.drip >= 0 && G.settings.blood !== false) fx.blood([p.x, p.y, p.z], [0, 0.2, 0], 8, f.floorY);
    }
    const air = p.y > low + 0.02 || Math.abs(f.v[1]) > 0.6;
    if (air) { f.m.rotation.x += f.av[0] * dt; f.m.rotation.y += f.av[1] * dt; f.m.rotation.z += f.av[2] * dt; }
    else if (f.drip >= 0 && f.life > 2) { // on the floor: it still twitches
      f.tw += dt;
      const k = Math.max(0, Math.sin(f.tw * 9)) * Math.max(0, Math.sin(f.tw * 1.3)) * 0.35;
      f.m.rotation.y += k * dt * 3;
      if (f.kn) f.kn.rotation.x = k * 2.2;
    }
    if (f.drip >= 0 && air && (f.drip += dt) > 0.07 && G.settings.blood !== false) { f.drip = 0; fx.blood([p.x, p.y, p.z], [0, -0.2, 0], 1, null); }
    if (f.life < 0.5) f.m.scale.multiplyScalar(Math.max(0, 1 - dt * 6));
    if (f.life <= 0) drop(i);
  }
  for (let i = rings.length - 1; i >= 0; i--) {
    const g = rings[i];
    g.t += dt;
    const k = Math.max(0, g.t / (g.secs || 0.7));
    g.m.visible = g.t > 0;
    g.m.scale.setScalar(0.4 + k * g.r);
    g.m.material.opacity = Math.max(0, 0.9 * (1 - k));
    if (k >= 1) { G.scene.remove(g.m); g.m.geometry.dispose(); g.m.material.dispose(); rings.splice(i, 1); }
  }
}
export function zlClear() { // the mode ended / a new map
  while (fly.length) drop(0);
  for (const g of rings) { G.scene.remove(g.m); g.m.geometry.dispose(); g.m.material.dispose(); }
  rings.length = 0; ST.clear(); bossBar(null);
}
// credits popups (zombies.js): what a 'why' reads as
export const ZL_WHY = { limb: ' LIMB', chonk: ' CHONK', screamer: ' SCREAMER', boss: ' BOSS DOWN', tip: ' TIP' };
