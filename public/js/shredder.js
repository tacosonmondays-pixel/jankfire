// Shredder, everything but the viewmodel: other people's machines (suction, teeth, motor noise), hanging in someone's
// intake (your gun goes in first, then you thrash while blood pours in), and the kill: the victim comes apart, every
// piece gets sucked into the killer's intake and comes out of the exhaust chute as chunks with blood and confetti.
// Everyone sees the same thing.
import * as THREE from 'three';
import { WEAPONS, FLAGS } from '/shared/weapons.js';
import { BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { G } from './ctx.js';
import { ME } from './player.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { buildCharacter, heatTeeth } from './models.js';
import { shredderPorts, shredKick, shredSpitVM } from './weapons.js';

const SW = WEAPONS.shredder;
const tmpA = new THREE.Vector3();
const R = (s = 1) => (Math.random() * 2 - 1) * s;
const CHUNK = new THREE.BoxGeometry(1, 1, 1);
const gore = () => G.settings.blood !== false;

// where a shredder's intake + chute are right now, and which way the chute spits.
// my own is the viewmodel; anyone else's is the gun in their hands (pool = live players, or replay ghosts)
function portsOf(id, pool = G.remotes) {
  if (id === G.myId && pool === G.remotes) return shredderPorts();
  const r = pool.get(id), g = r && r.weaponMesh;
  if (!g || r.w !== 'shredder' || !g.userData.chute) return null;
  r.ch.root.updateMatrixWorld(true);
  const pt = (v) => { tmpA.copy(v); g.localToWorld(tmpA); return [tmpA.x, tmpA.y, tmpA.z]; };
  const chute = pt(g.userData.chute), tip = pt(tmpA.copy(g.userData.chute).add(g.userData.chuteDir));
  const d = [tip[0] - chute[0], tip[1] - chute[1], tip[2] - chute[2]], l = Math.hypot(...d) || 1;
  return { intake: pt(g.userData.muzzle), chute, dir: d.map((x) => x / l), vel: r.vel, r };
}

// ------------------------------------------------------------ other people's machines
// the SUCK flag in their snapshots drives it: teeth spin up, the suction pours in, the motor drones, the gun shakes
export function remoteShredder(r, dt) {
  const on = !!(r.f & FLAGS.SUCK), now = performance.now();
  r.shredSpin = on ? Math.min(1, (r.shredSpin || 0) + dt / 0.35) : Math.max(0, (r.shredSpin || 0) - dt / 0.9);
  r.shredHeat = on ? Math.min(SW.fuel, (r.shredHeat || 0) + dt) : Math.max(0, (r.shredHeat || 0) - dt * SW.regen); // a guess at theirs
  const g = r.weaponMesh, ud = g && g.userData;
  if (!ud || !ud.teeth) return;
  ud.teeth.rotation.z -= Math.min(0.45, dt * r.shredSpin * 40); // under half a tooth a frame: never seems to run backwards
  if (ud.lamps) for (const l of ud.lamps) l.material.color.setHex(r.shredSpin > 0.05 ? 0xff3a2a : 0x500000);
  heatTeeth(g, Math.max(0, (r.shredHeat / SW.fuel - 0.45) / 0.55), 0.28); // (0.28: the glow remote.js gives players)
  const kick = Math.max(0, 1 - (now - (r.shredKickT || 0)) / 160); // a jolt each time it bites
  const j = 0.02 * r.shredSpin + 0.06 * kick;
  if (j > 0.001) g.position.set(R(j), R(j), R(j) + 0.08 * kick); else g.position.set(0, 0, 0);
  if (!on) return;
  const mz = r.muzzle();
  fx.vacuum(mz, r.look(), r.vel, SW.range, SW.cone, r.shredSpin, dt);
  r.shredSnd = (r.shredSnd || 0) - dt;
  if (r.shredSnd <= 0) { r.shredSnd = 0.3; sfx.suck(mz, r.shredSpin); }
}

// ------------------------------------------------------------ you're in someone's intake
// the server says where to hang; your client chases that point for as long as it keeps saying so
export function shredGrab(m) {
  if (!ME.alive || !Array.isArray(m.p) || m.p.length !== 3 || !m.p.every(Number.isFinite)) return;
  const n = performance.now();
  if (!ME.grab || n > ME.grab.until) hud.msg('IN THE SHREDDER', 0.9, 'slip');
  ME.grab = { p: m.p, until: n + 260 };
  ME.hook = null;
}
export function grabStep(now) {
  const g = ME.grab;
  if (!g) return;
  if (now > g.until || !ME.alive) { ME.grab = null; return; }
  for (let i = 0; i < 3; i++) ME.vel[i] = Math.max(-30, Math.min(30, (g.p[i] - ME.pos[i]) * 12));
  ME.onGround = false;
  G.shake = Math.max(G.shake, 0.45);
}

// ------------------------------------------------------------ things on their way into an intake
const pieces = []; // body parts / guns flying into a machine
const spits = []; // chunks waiting to come out of a chute
const chewed = new Set(); // people hanging in an intake right now (they thrash)
// a machine to feed: the killer's ports, followed every frame (they keep moving). kill = this one ends in a finale
function machine(k, pool, kill) {
  const get = () => portsOf(k, pool), first = get();
  return first && { get, last: first, at: 0, left: 0, crunch: 0, spat: 0, kill };
}
// where that machine is this frame (worked out once a frame, however many bits are on their way in)
function portsNow(job, n) {
  if (job.at !== n) { job.at = n; job.last = job.get() || job.last; }
  return job.last;
}
// obj (already in world space) gets pulled in after delay; mat = what its chunks look like. yank = snatched straight in
function feed(obj, job, delay, mat, yank = false) {
  G.scene.add(obj);
  pieces.push({ m: obj, job, mat, yank, t: 0, delay, from: null, dur: 0, s0: obj.scale.clone(),
    pop: [R(0.9), 0.2 + Math.random() * 0.8, R(0.9)], av: [R(8), R(8), R(8)], wob: Math.random() * 6 });
  job.left++;
}
// a world-space copy of a part of someone's mannequin
function copyOf(o) {
  const c = o.isMesh ? new THREE.Mesh(o.geometry, o.material) : o.clone();
  o.updateMatrixWorld(true);
  o.matrixWorld.decompose(c.position, c.quaternion, c.scale);
  if (!o.isMesh) c.traverse((x) => { if (x.userData.outline) x.visible = false; });
  return c;
}
function firstMat(o) { let mat = null; o.traverse((x) => { if (!mat && x.isMesh && x.material && !x.material.transparent) mat = x.material; }); return mat || new THREE.MeshBasicMaterial({ color: 0x444444 }); }
// their gun gets yanked out of their hands and goes in first (it comes back if they get away)
function eatGun(r, job) {
  const g = r.weaponMesh;
  if (!g || !g.visible || !r.ch.root.visible) return;
  feed(copyOf(g), job, 0, firstMat(g), true); // (other people's guns are drawn big: it shrinks fast on the way)
  g.visible = false;
  r.gunEaten = g;
}

// ------------------------------------------------------------ chewing
// a shred tick: the victim thrashes, blood pours out of them into the intake, the teeth crunch, the chute dribbles
const crunchT = new Map();
export function shredHit(m) {
  const n = performance.now();
  const victim = m.to === G.myId ? null : G.remotes.get(m.to);
  const vp = victim ? victim.pos : m.to === G.myId ? ME.pos : null;
  if (!vp) return;
  const c = [vp[0], vp[1] + 1.1, vp[2]];
  if (n - (crunchT.get(m.to) || 0) > 100) { crunchT.set(m.to, n); sfx.shred(m.to === G.myId ? null : c); }
  if (m.from === G.myId) { shredKick(); G.shake = Math.max(G.shake, 0.25); }
  const ports = portsOf(m.from);
  if (!ports) return;
  if (ports.r) ports.r.shredKickT = n;
  if (victim) {
    victim.chewUntil = n + 280; chewed.add(victim);
    const job = victim.weaponMesh && victim.weaponMesh.visible && machine(m.from, G.remotes, false);
    if (job) eatGun(victim, job);
  }
  if (!gore()) return;
  if (victim) fx.bloodTo(c, ports.intake, 10, ports.vel || [0, 0, 0]);
  if (Math.random() < 0.5) fx.chute(ports.chute, ports.dir, ports.vel || [0, 0, 0], 3, true, false);
}
// hanging in the teeth: the body jerks about, arms and legs flail (on top of the normal animation, every frame)
function thrash(now) {
  for (const r of chewed) {
    if (now > r.chewUntil || !r.alive) {
      if (r.gunEaten && r.gunEaten === r.weaponMesh) r.gunEaten.visible = true; // got away: here's your gun back
      r.gunEaten = null; chewed.delete(r);
      continue;
    }
    const ch = r.ch, t = now * 0.028 + r.id * 1.7;
    ch.root.position.x += R(0.05); ch.root.position.y += Math.abs(R(0.06)); ch.root.position.z += R(0.05);
    ch.root.rotation.y += Math.sin(t * 1.1) * 0.35 + R(0.15);
    ch.arm.rotation.x += Math.sin(t * 1.7) * 1.3; ch.armL.rotation.x += Math.sin(t * 1.3 + 1) * 1.4; ch.armL.rotation.z += 0.9 + Math.sin(t * 2.1) * 0.8;
    ch.legL.rotation.x += Math.sin(t * 1.9) * 0.9; ch.legR.rotation.x += Math.sin(t * 1.6 + 2) * 0.9;
    ch.head.rotation.x += Math.sin(t * 2.3) * 0.5; ch.head.rotation.z += R(0.4);
  }
}

// ------------------------------------------------------------ the kill
// v = the victim's mannequin (live remote or replay ghost) or, when it's you, me = { pos, yaw, color, look } to copy.
// returns false when there's no machine to go through (killer left / swapped guns): normal gibs then
export function shredKill(m, pool = G.remotes, me = null) {
  const job = machine(m.k, pool, true);
  if (!job) return false;
  const v = pool.get(m.v);
  let ch = v && v.ch, copy = null;
  if (!ch && me) {
    ch = buildCharacter(me.color, me.look);
    ch.root.position.set(me.pos[0], me.pos[1], me.pos[2]);
    ch.root.rotation.y = me.yaw || 0;
    ch.root.scale.setScalar(1.2);
    G.scene.add(ch.root); copy = ch.root;
  }
  if (!ch) return false;
  ch.root.updateMatrixWorld(true);
  if (v && v.weaponMesh) eatGun(v, job); // still holding it (replays don't have the chewing): in it goes first
  const gun = new Set();
  ch.slot.traverse((o) => gun.add(o));
  const parts = [];
  ch.body.traverse((o) => { if (o.isMesh && !o.userData.outline && !gun.has(o)) parts.push(o); });
  if (copy) G.scene.remove(copy);
  if (!parts.length) return false;
  const a = job.last.intake;
  G.camera.getWorldPosition(tmpA);
  const eye = tmpA.clone();
  const list = parts.map((o) => { const c = copyOf(o); return { c, mat: o.material, d: c.position.distanceToSquared(tmpA.set(a[0], a[1], a[2])) }; })
    .filter(({ c }) => !copy || c.position.distanceTo(eye) > 0.6) // it's you: the bits round your own eyes would just fill the screen
    .sort((x, y) => x.d - y.d); // nearest bits go in first
  list.forEach(({ c, mat }, i) => feed(c, job, 0.06 + (i / list.length) * 0.35 + Math.random() * 0.06, mat));
  if (v) { v.ch.root.visible = false; v.alive = false; } // the next snapshot agrees; this just stops a one-frame flash
  const c = [ch.root.position.x, ch.root.position.y + 1.1, ch.root.position.z];
  if (gore() && !copy) fx.bloodTo(c, a, 30, job.last.vel || [0, 0, 0]);
  sfx.shred(c); sfx.whoops(c);
  return true;
}

function spitChunks(s, n) {
  const p = portsNow(s.job, n), c = p.chute, d = p.dir, base = p.vel || [0, 0, 0];
  const fl = raycast([c[0], c[1], c[2]], [0, -1, 0], 40, BOXES), floorY = fl ? fl.point[1] : -1e9;
  for (let i = 0, k = 2 + (Math.random() < 0.5 ? 1 : 0); i < k; i++) {
    const m = new THREE.Mesh(CHUNK, s.mat);
    m.scale.setScalar(0.045 + Math.random() * 0.07);
    m.position.set(c[0] + R(0.04), c[1] + R(0.04), c[2] + R(0.04));
    G.scene.add(m);
    const sp = 6 + Math.random() * 6;
    G.gibs.push({ m, floorY, life: 2.2 + Math.random() * 1.6, v: [d[0] * sp + R(1.6) + base[0], d[1] * sp + R(1.6) + 1.5 + base[1], d[2] * sp + R(1.6) + base[2]], av: [R(16), R(16), R(16)] });
  }
  const last = --s.job.left === 0 && s.job.kill;
  fx.chute(c, d, base, last ? (p.mine ? 24 : 45) : 5, gore(), last || Math.random() < 0.4);
  if (p.mine) shredSpitVM(last);
  if (last || n - s.job.spat > 140) { s.job.spat = n; sfx.spit(p.mine ? null : c); }
  if (last && gore()) fx.blood(c, d, 80, floorY > -1e8 ? floorY : null); // the big finish, with puddles where it lands
}

export function updateShreds(dt) {
  const n = performance.now();
  thrash(n);
  for (let i = pieces.length - 1; i >= 0; i--) {
    const p = pieces[i], m = p.m;
    p.t += dt;
    if (p.t < p.delay) { // coming apart: everything drifts off the body for a moment first
      m.position.x += p.pop[0] * dt; m.position.y += p.pop[1] * dt; m.position.z += p.pop[2] * dt;
      m.rotation.x += p.av[0] * dt * 0.3; m.rotation.z += p.av[2] * dt * 0.3;
      continue;
    }
    const ports = portsNow(p.job, n), a = ports.intake;
    if (!p.from) { p.from = m.position.clone(); p.dur = p.yank ? 0.2 : Math.max(0.16, Math.min(0.5, p.from.distanceTo(tmpA.set(a[0], a[1], a[2])) / 11)); }
    const u = Math.min(1, (p.t - p.delay) / p.dur), e = u * u; // speeds up as it gets sucked in
    const wob = (1 - u) * 0.18 * Math.sin(u * 14 + p.wob); // a little corkscrew on the way
    m.position.set(p.from.x + (a[0] - p.from.x) * e + wob, p.from.y + (a[1] - p.from.y) * e + wob * 0.6, p.from.z + (a[2] - p.from.z) * e - wob);
    const spin = 1 + u * 4;
    m.rotation.x += p.av[0] * dt * spin; m.rotation.y += p.av[1] * dt * spin; m.rotation.z += p.av[2] * dt * spin;
    m.scale.copy(p.s0).multiplyScalar(p.yank ? 0.6 * (1 - 0.85 * Math.sqrt(u)) : 1 - 0.8 * u); // shrinks all the way in, so it fits down the throat
    if (gore() && Math.random() < dt * 22) fx.bloodTo([m.position.x, m.position.y, m.position.z], a, 1, ports.vel || [0, 0, 0]);
    if (u < 1) continue;
    G.scene.remove(m);
    pieces.splice(i, 1);
    spits.push({ at: n + 110 + Math.random() * 200, mat: p.mat, job: p.job });
    if (ports.r) ports.r.shredKickT = n;
    if (n - p.job.crunch > 90) { p.job.crunch = n; sfx.shred(ports.mine ? null : a); if (ports.mine) shredKick(); }
  }
  for (let i = spits.length - 1; i >= 0; i--) {
    if (n < spits[i].at) continue;
    const s = spits[i];
    spits.splice(i, 1);
    spitChunks(s, n);
  }
}

export function clearShreds() {
  for (const p of pieces) G.scene.remove(p.m);
  pieces.length = 0; spits.length = 0;
  for (const r of chewed) if (r.gunEaten && r.gunEaten === r.weaponMesh) r.gunEaten.visible = true;
  chewed.clear();
  if (ME.grab) ME.grab = null;
}
