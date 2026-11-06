// Wrecking Ball killstreak, the looks: a riveted steel demolition ball with a chain stub on top, a stripe in your colour
// and the mannequin's eyes peeking out of a slot. Also its chain, the third-person camera, the HUD timer and the
// slam / ram effects. How the ball moves is in player.js (ballStep); the server judges rams and slams.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { WRECK, FLAGS, STREAKS, slamSize, ramDmg } from '/shared/weapons.js';
import { G } from './ctx.js';
import { ME, BS, C, eye, look, hookPoint, hspeed, ballOn } from './player.js';
import { W } from './weapons.js';
import { fx } from './fx.js';
import { sfx, loopLevel } from './audio.js';
import { hud } from './hud.js';
import { wreckShell, lookOf } from './streaklooks.js'; // your killstreak look: a disco / meat / bowling ball shell
import { authored, AUTHORED, whenLate, nodeIn, ownMatByName } from './glbkit.js'; // the Blender ball (tools/blender/make_wreck.py)

const R = WRECK.r;
const Y = new THREE.Vector3(0, 1, 0);
const STEEL = 0x98a1ab, DARK = 0x565e68, RIVET = 0xccd3db, LINK = 0x6a717b;
const CAM = { dist: 5.5 }; // third-person boom length

// players ignore fog (like the mannequins), so the ball reads across the map too. the shell is shiny steel.
const mats = new Map();
function mat(color, kind = 'l', glow = 0) {
  const key = color + kind + glow;
  if (!mats.has(key)) {
    mats.set(key, kind === 'b' ? new THREE.MeshBasicMaterial({ color, fog: false })
      : kind === 'o' ? new THREE.MeshBasicMaterial({ color, side: THREE.BackSide, fog: false }) // outline
      : kind === 's' ? new THREE.MeshPhongMaterial({ color, specular: 0x9aa8b8, shininess: 70, flatShading: true, fog: false })
        : new THREE.MeshLambertMaterial({ color, flatShading: true, fog: false, emissive: new THREE.Color(color).multiplyScalar(glow) }));
  }
  return mats.get(key);
}
// every ball (yours, everyone else's, replay ghosts) shares its geometry: nothing to leak when one goes away
const boxGeos = new Map();
function box(w, h, d, m, x, y, z) {
  const key = w + ',' + h + ',' + d;
  if (!boxGeos.has(key)) boxGeos.set(key, new THREE.BoxGeometry(w, h, d));
  const o = new THREE.Mesh(boxGeos.get(key), m);
  o.position.set(x, y, z);
  return o;
}

// rivets + welded seams, merged into one mesh each (the same for every ball)
let parts = null;
function ballParts() {
  if (parts) return parts;
  const rv = [], sm = [];
  const rivet = (x, y, z) => { const g = new THREE.SphereGeometry(0.05, 5, 3); g.translate(x, y, z); rv.push(g); };
  const rr = R * 1.006;
  for (const lat of [-0.22, 0.22]) for (let i = 0; i < 20; i++) { // two rows along the edges of the stripe
    const a = (i / 20) * Math.PI * 2, cl = Math.cos(lat) * rr;
    rivet(Math.cos(a) * cl, Math.sin(lat) * rr, Math.sin(a) * cl);
  }
  for (const az of [Math.PI / 4, -Math.PI / 4]) { // two seams over the top, crossing under the chain stub
    const t = new THREE.TorusGeometry(R * 1.002, 0.032, 4, 48);
    t.rotateY(-az);
    sm.push(t);
    for (let i = 0; i < 28; i++) {
      const a = (i / 28) * Math.PI * 2, y = Math.cos(a);
      if (Math.abs(y) > 0.88 || Math.abs(y) < 0.3) continue; // not under the stub, not on the stripe
      rivet(Math.cos(az) * Math.sin(a) * rr, y * rr, Math.sin(az) * Math.sin(a) * rr);
    }
  }
  parts = { rivets: mergeGeometries(rv), seams: mergeGeometries(sm), body: new THREE.SphereGeometry(R, 22, 14),
    stripe: new THREE.SphereGeometry(R * 1.008, 28, 2, 0, Math.PI * 2, Math.PI / 2 - 0.17, 0.34),
    base: new THREE.CylinderGeometry(0.28, 0.34, 0.14, 10), ring: new THREE.TorusGeometry(0.12, 0.045, 5, 12) };
  return parts;
}
const LINK_GEO = new THREE.TorusGeometry(0.13, 0.042, 4, 10).scale(1, 1.5, 1); // an oval chain link, long axis = y

// the Blender chain link (one oval link, long axis y), centred: the chain instances it. null = ours
let blLink;
function linkOf() {
  if (blLink !== undefined) return blLink;
  const a = AUTHORED.x_wreck;
  if (!a) return null; // (not loaded yet: ours, and look again next time)
  let m = null;
  const n = nodeIn(a.scene, 'link');
  if (n) n.traverse((o) => { if (!m && o.isMesh) m = o; });
  if (m && m.material.fog) { m.material.fog = false; m.material.needsUpdate = true; } // (players ignore fog, chain too)
  blLink = m ? { geo: m.geometry.clone().center(), mat: m.material } : null;
  return blLink;
}
// the player's face peeking out of the slot: skin plate, the shadow under the frame, eyes (the pupils look around)
function wreckFace(slot, lk) {
  slot.add(box(0.62, 0.17, 0.06, mat(lk.skin ? new THREE.Color(lk.skin).getHex() : 0xe6cba2), 0, 0, -0.01));
  slot.add(box(0.62, 0.035, 0.07, mat(0x000000, 'b'), 0, 0.07, -0.015)); // shadow under the top of the frame
  const pupils = [];
  for (const sx of [-1, 1]) {
    slot.add(box(0.11, 0.08, 0.02, mat(0xffffff, 'b'), sx * 0.12, -0.005, -0.05));
    const p = box(0.045, 0.05, 0.02, mat(0x000000, 'b'), sx * 0.12, -0.012, -0.062);
    p.userData.x = sx * 0.12;
    pupils.push(p); slot.add(p);
  }
  if (lk.face === 'shades' || lk.face === 'visor') slot.add(box(0.4, 0.07, 0.02, mat(lk.face === 'visor' ? 0x3ee6c8 : 0x111111, 'b'), 0, -0.005, -0.075));
  return pupils;
}
// the ball. origin = its centre. userData.hook = where the chain comes out (top of the stub)
export function buildWreckBall(color, look, opts = {}) {
  const P = ballParts(), g = new THREE.Group();
  const c = new THREE.Color(color || '#ff4fd8').getHex();
  const bl = authored('x_wreck');
  if (bl) { // the Blender ball: its band in your colour, your face in its slot, our outline + chain
    g.add(bl.obj);
    bl.obj.traverse((o) => { if (o.isMesh) for (const m of [].concat(o.material)) if (m.fog) { m.fog = false; m.needsUpdate = true; } }); // players ignore fog, like ours
    const lnk = nodeIn(bl.obj, 'link'); if (lnk) lnk.removeFromParent(); // (that one's the chain's)
    ownMatByName(g, 'wb_accent', mat(c, 'l', 0.3));
    if (opts.skin) wreckShell(bl.obj, opts.skin);
    const slot = nodeIn(bl.obj, 'slot');
    g.userData.pupils = slot ? wreckFace(slot, look || {}) : [];
    if (opts.outline) { const o = new THREE.Mesh(P.body, mat(c, 'o')); o.scale.setScalar(1.06); g.add(o); }
    const hk = bl.meta.hook;
    g.userData.hook = Array.isArray(hk) && hk.length === 3 && hk.every(Number.isFinite) ? new THREE.Vector3(...hk) : new THREE.Vector3(0, R + 0.95, 0);
    g.userData.glb = 'blender';
    return g;
  }
  g.add(new THREE.Mesh(P.body, mat(STEEL, 's')));
  g.add(new THREE.Mesh(P.stripe, mat(c, 'l', 0.3)));
  g.add(new THREE.Mesh(P.seams, mat(DARK)));
  g.add(new THREE.Mesh(P.rivets, mat(RIVET, 's')));
  // chain stub: base plate, lifting lug, a ring and two links
  const base = new THREE.Mesh(P.base, mat(DARK));
  base.position.y = R - 0.03; g.add(base);
  g.add(box(0.09, 0.3, 0.26, mat(DARK), 0, R + 0.16, 0));
  const ring = new THREE.Mesh(P.ring, mat(LINK, 's'));
  ring.position.y = R + 0.31; g.add(ring);
  for (const [y, ry] of [[R + 0.55, Math.PI / 2], [R + 0.8, 0]]) { const l = new THREE.Mesh(LINK_GEO, mat(LINK, 's')); l.position.y = y; l.rotation.y = ry; g.add(l); }
  // the viewing slot, front and a bit up: a steel frame, and the mannequin in there looking out
  const lk = look || {};
  const slot = new THREE.Group(), lat = 0.42;
  slot.position.set(0, Math.sin(lat) * R, -Math.cos(lat) * R);
  slot.rotation.x = lat;
  for (const [w, h, x, y] of [[0.76, 0.06, 0, 0.115], [0.76, 0.06, 0, -0.115], [0.07, 0.29, -0.345, 0], [0.07, 0.29, 0.345, 0]]) slot.add(box(w, h, 0.18, mat(DARK), x, y, 0));
  const pupils = wreckFace(slot, lk);
  g.add(slot);
  if (opts.outline) { // same coloured outline every other player gets
    const o = new THREE.Mesh(P.body, mat(c, 'o'));
    o.scale.setScalar(1.06); g.add(o);
  }
  g.userData.hook = new THREE.Vector3(0, R + 0.95, 0);
  g.userData.pupils = pupils;
  return g;
}

// a chain of real links from a to b (instanced: up to ~95 m of chain in one draw call). sag = how far its middle hangs
// below the straight line (a slack chain droops). world = true: the mesh lives under something that moves, so the
// caller cancels the parent's transform and we work in world space
const _m = new THREE.Matrix4(), _p = new THREE.Vector3(), _qa = new THREE.Quaternion(), _one = new THREE.Vector3(1, 1, 1), _dir = new THREE.Vector3();
const QUARTER = new THREE.Quaternion().setFromAxisAngle(Y, Math.PI / 2);
export class Chain {
  constructor(parent, world = false, max = 300) {
    this.max = max;
    const bl = linkOf(); // (the Blender link once the ball's model is in)
    this.mesh = new THREE.InstancedMesh(bl ? bl.geo : LINK_GEO, bl ? bl.mat : mat(LINK, 's'), max);
    this.mesh.frustumCulled = false;
    this.mesh.count = 0;
    this.mesh.visible = false;
    if (world) this.mesh.matrixAutoUpdate = false;
    parent.add(this.mesh);
  }
  set(a, b, sag = 0) {
    const dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2];
    const len = Math.hypot(dx, dy, dz);
    if (len < 0.05) { this.mesh.visible = false; return; }
    const s4 = 4 * Math.min(sag, len * 0.45);
    const n = Math.min(this.max, Math.max(1, Math.round((len + s4 * 0.6) / 0.32)));
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n;
      _p.set(a[0] + dx * t, a[1] + dy * t - s4 * t * (1 - t), a[2] + dz * t);
      _dir.set(dx, dy - s4 * (1 - 2 * t), dz).normalize(); // the slope of the curve here
      _qa.setFromUnitVectors(Y, _dir);
      if (i & 1) _qa.multiply(QUARTER); // every other link turned 90 degrees
      this.mesh.setMatrixAt(i, _m.compose(_p, _qa, _one));
    }
    this.mesh.count = n;
    this.mesh.instanceMatrix.needsUpdate = true;
    this.mesh.visible = true;
  }
  hide() { this.mesh.visible = false; }
  dispose() { this.mesh.removeFromParent(); this.mesh.dispose(); } // (frees the instance buffer)
}
// how far a chain of length L hangs between two points d apart (parabola: L = d + 8 sag^2 / 3d)
const sagOf = (d, L) => (L > d ? Math.sqrt((3 * d * (L - d)) / 8) : 0);

// rolling: spin about the axis across the way you're going. on a chain the stub swings round to point up the chain;
// stopped on the floor, the mannequin inside turns the ball so it can peek out where you're looking.
const _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _w = new THREE.Vector3(), _d = new THREE.Vector3(), _v = new THREE.Vector3();
function spinBall(st, vel, grounded, dt, anchor, c, yaw) {
  const hs = Math.hypot(vel[0], vel[2]);
  if (anchor) st.w.multiplyScalar(Math.max(0, 1 - dt * 6));
  else if (grounded) st.w.set(vel[2] / R, 0, -vel[0] / R); // no slipping
  else st.w.multiplyScalar(Math.max(0, 1 - dt * 0.35)); // keeps spinning in the air
  const ang = st.w.length() * dt;
  if (ang > 1e-6) { _q.setFromAxisAngle(_w.copy(st.w).normalize(), ang); st.q.premultiply(_q); }
  if (anchor) {
    _d.set(anchor[0] - c[0], anchor[1] - c[1], anchor[2] - c[2]);
    if (_d.lengthSq() > 1e-4) { _q2.setFromUnitVectors(Y, _d.normalize()).multiply(_q.setFromAxisAngle(Y, yaw)); st.q.slerp(_q2, Math.min(1, dt * 7)); }
  } else if (grounded && hs < 1.5) st.q.slerp(_q2.setFromAxisAngle(Y, yaw), Math.min(1, dt * 2.5));
  st.q.normalize();
}
// the eyes in the slot dart about
function lookAround(g, now, seed) {
  const t = Math.floor(now / 650 + seed);
  const dx = ((((t * 9301 + 49297) % 233280) + 233280) % 233280 / 233280 - 0.5) * 0.06;
  for (const p of g.userData.pupils) p.position.x = p.userData.x + dx;
}
const newSpin = (yaw) => ({ q: new THREE.Quaternion().setFromAxisAngle(Y, yaw), w: new THREE.Vector3() });

// what a ball is hit-tested as (other players shoot at what they see)
export function ballBoxes(pos, k = 1) {
  const r = R * k, [x, y, z] = pos;
  return [{ min: [x - r, y, z - r], max: [x + r, y + 2 * r, z + r], head: false }];
}

// the ball bursts open when you die in it: two steel halves tumble away in a spray of rivets
const HALF = new THREE.SphereGeometry(R, 16, 6, 0, Math.PI * 2, 0, Math.PI / 2).translate(0, -R * 0.375, 0); // origin = its middle
export function wreckBurst(c, vel = [0, 0, 0]) {
  fx.spray(c, 42, [0x98a1ab, 0xccd3db, 0x565e68, 0xfff2b0], 10, 0.9, 0.16, 18, 1);
  fx.dust([c[0], c[1] - R, c[2]], 10);
  sfx.clang(c, 1);
  const fl = raycast(c, [0, -1, 0], 40, BOXES);
  for (const s of [1, -1]) {
    const m = new THREE.Mesh(HALF, mat(STEEL, 's')); // shared material: the gib cleanup only removes the mesh
    m.position.set(c[0], c[1] + s * R * 0.375, c[2]);
    if (s < 0) m.rotation.x = Math.PI;
    G.scene.add(m);
    G.gibs.push({
      m, floorY: fl ? fl.point[1] + 0.4 : -1e9, life: 3.5 + Math.random(),
      v: [vel[0] * 0.5 + (Math.random() - 0.5) * 6, 5 + s * 3 + Math.random() * 3, vel[2] * 0.5 + (Math.random() - 0.5) * 6],
      av: [(Math.random() - 0.5) * 9, (Math.random() - 0.5) * 9, (Math.random() - 0.5) * 9],
    });
  }
}

// ------------------------------------------------------------ you
const me = { g: null, key: '', st: newSpin(0), chain: null, was: false, camLen: 0, shadowBig: false, dur: 0 };
whenLate('x_wreck', () => { me.key = ''; blLink = undefined; if (me.chain) { me.chain.dispose(); me.chain = null; } }); // the Blender ball landed: rebuild yours (others rebuild with their mannequin)
function poof(p) { fx.spray([p[0], p[1] + R, p[2]], 26, [0xb8c4d0, 0x8a96a4, 0xffffff], 7, 0.7, 0.18, 10, 1.5); fx.dust(p, 12); }
function onStart() {
  W.held = false; W.aimHeld = false; W.dashHeld = false;
  me.dur = Math.max(1, (ME.ballUntil - performance.now()) / 1000); // (for the HUD bar: the server may have said a longer one)
  me.st = newSpin(ME.yaw);
  document.body.classList.add('wrecking'); // (the HUD moves out of the ball's way)
  sfx.wreck();
  poof(ME.pos);
  G.shake = Math.max(G.shake, 0.4);
}
function onEnd() {
  W.swap = 1; // the gun comes back up
  document.body.classList.remove('wrecking');
  if (ME.alive) { poof(ME.pos); sfx.clang(null, 0.5); } else if (me.g && me.g.visible) wreckBurst(me.g.position.toArray(), ME.vel);
  loopLevel('roll', 0);
  hud.ball(null);
}
// every frame (main loop): your own ball, its chain (instead of your rope) and shadow, the rumble, the HUD timer, and no
// guns while it lasts
export function updateWreck(dt, now, replaying, shadow, rope) {
  const on = G.joined && ballOn(now);
  if (on !== me.was) { me.was = on; if (on) onStart(); else onEnd(); }
  // died in it: the death cam starts from your own eyes, not the ball's camera pivot 3 m up (the server ends the streak
  // just before it says you died, so this can't wait for endBall)
  if (!ME.alive && ME.eyeH > C.standEye) ME.eyeH = C.standEye;
  if (!on) {
    if (me.g) me.g.visible = false;
    if (me.chain) me.chain.hide();
    if (me.shadowBig && shadow) { shadow.scale.setScalar(1); me.shadowBig = false; }
    return;
  }
  W.held = false; W.aimHeld = false; W.dashHeld = false; // no hands
  if (rope) rope.visible = false; // the ball swings on its own chain
  const sk = lookOf('me', 'wreckingball');
  const key = G.myColor + '|' + JSON.stringify(G.settings.look || {}) + JSON.stringify(sk) + (sk && AUTHORED['x_' + sk[3]] ? '+' : ''); // (+: its shell's file landed)
  if (!me.g || me.key !== key) {
    if (me.g) G.scene.remove(me.g);
    me.g = buildWreckBall(G.myColor, G.settings.look, { skin: sk });
    me.key = key;
    G.scene.add(me.g);
  }
  if (!me.chain) me.chain = new Chain(G.scene);
  const c = [ME.pos[0], ME.pos[1] + R, ME.pos[2]];
  const hp = hookPoint();
  spinBall(me.st, ME.vel, ME.onGround, dt, hp, c, ME.yaw);
  me.g.position.set(c[0], c[1], c[2]);
  me.g.quaternion.copy(me.st.q);
  // a wall right behind you squeezes the camera boom: then the camera sits on the chain stub, so hide the ball rather
  // than fill the screen with it (and never show the inside of a ball)
  const near = me.camLen < 1.8 || G.camera.position.distanceTo(me.g.position) < R + 0.2;
  me.g.visible = !replaying && !near;
  lookAround(me.g, now, 0);
  if (hp && !replaying) {
    me.g.updateMatrixWorld(true);
    const s = me.g.localToWorld(_v.copy(me.g.userData.hook));
    const ch = BS.chain, d = Math.hypot(hp[0] - s.x, hp[1] - s.y, hp[2] - s.z);
    if (near && d > 2) s.lerp(_d.set(hp[0], hp[1], hp[2]), 1.4 / d); // (no giant links right in front of the camera)
    me.chain.set([s.x, s.y, s.z], hp, ch && !ch.taut ? sagOf(d, ch.len - R - 0.95) : d * 0.008); // (the physics measures from the middle of the ball)
  } else me.chain.hide();
  // a big shadow under the ball, on the floor or not
  const sh = raycast([ME.pos[0], ME.pos[1] + 0.1, ME.pos[2]], [0, -1, 0], 120, BOXES);
  if (shadow) {
    shadow.visible = !!sh && !replaying;
    if (sh) shadow.position.set(ME.pos[0], sh.point[1] + 0.03, ME.pos[2]);
    shadow.scale.setScalar(2.4); me.shadowBig = true;
  }
  // rumble + dust while it rolls
  const hs = hspeed();
  loopLevel('roll', ME.onGround && !replaying ? Math.min(1, hs / 26) : 0);
  if (ME.onGround && hs > 12 && Math.random() < dt * hs * 0.3) fx.dust(ME.pos, 2);
  // the HUD: time left, and how big a slam would be from up here (the higher, the bigger)
  const ready = 1 - Math.max(0, BS.slamReady - now) / (WRECK.slamCd * 1000);
  const h = !ME.onGround && !BS.slam && sh ? BS.top - sh.point[1] : null;
  // what a ram would do right now (the server's rule: rolling, swinging and falling count, rising and the slam dive don't)
  const v = ME.vel, rs = Math.hypot(v[0], v[2], v[1] < 0 && v[1] > 8 - WRECK.slamV ? v[1] : 0);
  const ram = Math.round(ramDmg(rs));
  const bh = G.myBody && G.myBody.k === 'wreckingball' ? G.myBody : null; // its HP (bodyhp.js): it lasts until that breaks
  hud.ball(Math.max(0, (ME.ballUntil - now) / 1000), me.dur || STREAKS.wreckingball.dur, { ready, h, size: h != null ? slamSize(h) : null, speed: rs, ram, hp: bh ? bh.hp : null, max: bh ? bh.max : null });
}

// third person: a boom straight back from the pivot above the ball along your view, so the crosshair (and your chain)
// still points exactly through the pivot. it pulls out a bit at speed, pulls in when something is behind you and eases
// back out. dead: straight back to your own eyes.
export function ballCam(cam, dt) {
  if (!G.joined || !ME.alive) { me.camLen = 0; return; }
  const on = ballOn();
  if (!on && me.camLen < 0.02) { me.camLen = 0; return; }
  const e = eye(), d = look();
  const want = CAM.dist + Math.min(1.5, hspeed() * 0.04);
  const hit = raycast(e, [-d[0], -d[1], -d[2]], want + 0.5, BOXES);
  // stay this far off whatever it hit, measured square to its face (looking steeply down in a low room, the boom
  // goes up into the ceiling at a slant, and the near plane would poke through it)
  const ax = hit && hit.axis >= 0 ? Math.abs(d[hit.axis]) : 1; // (axis -1: the pivot itself is inside something)
  const free = hit ? Math.max(0.15, Math.min(want, hit.t - Math.min(1, 0.3 / Math.max(0.3, ax)))) : want;
  const target = on ? free : 0;
  if (me.camLen > free) me.camLen = free; // never through a wall
  me.camLen += (target - me.camLen) * Math.min(1, dt * (target > me.camLen ? 3 : 10));
  cam.position.set(e[0] - d[0] * me.camLen, e[1] - d[1] * me.camLen, e[2] - d[2] * me.camLen);
}

// ------------------------------------------------------------ everyone else (and replay ghosts): called from Remote.update
function ballOff(r, w) {
  w.on = false; w.g.visible = false; if (w.chain) w.chain.hide();
  r.ch.body.visible = true; r.marker.position.y = 2.75; r.shadow.scale.setScalar(1);
}
// a Remote (or replay ghost) going away: free its chain's instance buffer (the ball itself only uses shared geometry)
export function wreckDispose(r) {
  if (r.wreck && r.wreck.chain) r.wreck.chain.dispose();
  r.wreck = null;
}
export function wreckRemote(r, dt, now) {
  const on = !!(r.f & FLAGS.BALL) && r.alive;
  let w = r.wreck;
  if (!on) {
    if (w && w.on) { if (r.alive && r.buf.length > 2) { poof(r.pos); sfx.clang(r.pos, 0.5); } ballOff(r, w); } // ran out (dying bursts it instead)
    return;
  }
  const root = r.ch.root;
  const sk = lookOf(r.skins || r.id, 'wreckingball'), skk = JSON.stringify(sk) + (sk && AUTHORED['x_' + sk[3]] ? '+' : '') + (AUTHORED.x_wreck ? 'b' : ''); // (rebuilt as the files land)
  if (!w || w.root !== root || w.color !== r.color || w.skk !== skk) { // (re)build: first time, new look, new team colour, new ball skin
    if (w) { w.g.removeFromParent(); if (w.chain) w.chain.dispose(); }
    w = r.wreck = { g: buildWreckBall(r.color, r.outfit, { outline: true, skin: sk }), st: newSpin(r.yaw), chain: null, root, color: r.color, skk, on: false, seed: Math.random() * 9 };
    root.add(w.g);
  }
  if (!w.on) { w.on = true; w.st = newSpin(r.yaw); if (r.buf.length > 2) { poof(r.pos); sfx.wreck(r.pos); } }
  r.ch.body.visible = false;
  r.rope.visible = false;
  r.marker.position.y = 3.45;
  r.tag.position.y += 0.7;
  const k = r.distScale || 1;
  const c = [r.pos[0], r.pos[1] + R * k, r.pos[2]];
  spinBall(w.st, r.vel, Math.abs(r.vel[1]) < 1.5, dt, r.g, c, r.yaw);
  // the ball hangs off the mannequin's root, which is turned to their yaw and scaled up: undo both
  w.g.position.set(0, R / 1.2, 0);
  w.g.scale.setScalar(1 / 1.2);
  w.g.quaternion.setFromAxisAngle(Y, -r.yaw).multiply(w.st.q);
  w.g.visible = true;
  lookAround(w.g, now, w.seed);
  if (r.g) {
    if (!w.chain) w.chain = new Chain(root, true); // (only made for balls that actually swing)
    root.updateMatrixWorld(true);
    const s = w.g.localToWorld(_v.copy(w.g.userData.hook));
    w.chain.mesh.matrix.copy(root.matrixWorld).invert();
    w.chain.set([s.x, s.y, s.z], r.g, Math.hypot(r.g[0] - s.x, r.g[1] - s.y, r.g[2] - s.z) * 0.012);
  } else if (w.chain) w.chain.hide();
  r.shadow.scale.setScalar(2.4 * k);
  const hs = Math.hypot(r.vel[0], r.vel[2]);
  if (Math.abs(r.vel[1]) < 1.5 && hs > 12 && Math.random() < dt * hs * 0.2) fx.dust(r.pos, 2);
}
// they died in it (kill message, live or in a replay): burst it open
export function wreckDied(r, vel) {
  const w = r.wreck;
  if (!w || !w.on) return;
  const k = r.distScale || 1;
  wreckBurst([r.pos[0], r.pos[1] + R * k, r.pos[2]], vel || r.vel);
  ballOff(r, w);
}

// ------------------------------------------------------------ server events: slams + rams (live, or in a replay)
export function wreckFx(m, replay = false) {
  if (m.k === 'slam') {
    const S = slamSize(m.h || 0);
    fx.slam(m.p, m.r || S.r, S.k);
    sfx.slam(m.p, S.k);
    if (!replay) {
      const d = Math.hypot(m.p[0] - ME.pos[0], m.p[1] - ME.pos[1], m.p[2] - ME.pos[2]);
      G.shake = Math.max(G.shake, Math.max(0, (1 + S.k * 0.4) - d / (18 + S.k * 14)));
    }
  } else if (m.k === 'ram') {
    const k = Math.min(1, (m.s || 20) / 50);
    sfx.clang(m.p, 0.5 + k * 0.5); sfx.thwack(m.p);
    fx.spray(m.p, 10 + Math.round(k * 24), [0xfff2b0, 0xffb040, 0xffffff], 5 + k * 10, 0.4, 0.1, 12, 1);
    if (replay) return;
    if (m.to === G.myId) { G.shake = Math.max(G.shake, 0.6 + k * 0.6); hud.msg('WRECKED', 0.9, 'slip'); }
    if (m.id === G.myId) { G.shake = Math.max(G.shake, 0.35 + k * 0.45); if (m.s >= 25) hud.msg(`${Math.round(m.s * 3.6)} KM/H WRECK`, 0.9, 'brag'); }
  }
}
