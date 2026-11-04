// Replays. The client keeps the last few seconds of snapshots + events (for your killcam);
// the server keeps its own recording and sends the play of the round in the same format.
// clip = { frames: [{ s, p: [snapshot entries], j: [[id, kind, x, y, z, tip]] }], ev: [{ s, m }], info: { id: {...} } }
import * as THREE from 'three';
import { G } from './ctx.js';
import { Remote } from './remote.js';
import { buildProjectile, tipColor, M } from './models.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { tracerColor } from './skins.js';
import { playKillFx } from './killfx.js';
import { WEAPONS } from '/shared/weapons.js';
import { TEAMS } from '/shared/modes.js';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';

const KEEP = 10000;
export const rec = { frames: [], ev: [] };
const r2 = (x) => Math.round(x * 100) / 100;

export function recordSnap(m) {
  const j = [];
  for (const pr of G.projs.values()) j.push([pr.id, pr.k, r2(pr.p[0]), r2(pr.p[1]), r2(pr.p[2]), pr.tip || 0]);
  rec.frames.push({ s: m.s, p: m.p, j });
  while (rec.frames.length && rec.frames[0].s < m.s - KEEP) rec.frames.shift();
  while (rec.ev.length && rec.ev[0].s < m.s - KEEP) rec.ev.shift();
}
export function recordEv(m) { rec.ev.push({ s: performance.now() + G.offset, m }); }
export function clearRec() { rec.frames.length = 0; rec.ev.length = 0; }
export function serverNow() { return performance.now() + G.offset; }

export function localClip(t0, t1, infoOf) {
  const frames = rec.frames.filter((f) => f.s >= t0 && f.s <= t1);
  const ev = rec.ev.filter((e) => e.s >= t0 && e.s <= t1);
  const info = {};
  for (const f of frames) for (const e of f.p) if (!info[e[0]]) info[e[0]] = infoOf(e[0]);
  return { frames, ev, info };
}

export const RP = { active: false, mode: null };
let st = null;
const camPos = new THREE.Vector3(), camLook = new THREE.Vector3(), tmp = new THREE.Vector3();

export function playClip(clip, opts = {}) {
  stopReplay(true);
  if (!clip || !Array.isArray(clip.frames) || clip.frames.length < 3) { if (opts.onEnd) opts.onEnd(); return false; }
  const ghosts = new Map();
  for (const [k, inf] of Object.entries(clip.info || {})) {
    const id = Number(k);
    const i = inf || {};
    // team colour beats clothes on ghosts too (clips without a team field: a team colour means a team)
    const team = i.team ?? (Object.values(TEAMS).some((t) => t.color === i.color) ? 1 : 0);
    const g = new Remote(id, i.level ? `${i.name} [${i.level}]` : (i.name || '???'), i.color || '#ffffff', i.skins || {}, !!i.bot, i.look || null, team);
    // katana length at the start of the clip: one less than its first recorded growth, else what it was when clipped
    const k0 = (clip.ev || []).find((e) => e.m && e.m.t === 'kat' && e.m.id === id);
    g.katN = k0 && k0.m.n > 0 ? k0.m.n - 1 : (i.kat || 0);
    g.ghost = true;
    if (id === opts.focus) g.tag.visible = false;
    ghosts.set(id, g);
  }
  const frames = clip.frames, t0 = frames[0].s;
  st = {
    clip, opts, ghosts, projs: new Map(), t: t0, fi: 0, pa: 0,
    ei: 0, end: Math.min(opts.end || Infinity, frames[frames.length - 1].s), first: true, lastEye: null, lastYaw: 0,
  };
  while (st.ei < clip.ev.length && clip.ev[st.ei].s < t0) st.ei++;
  RP.active = true;
  RP.mode = opts.mode || 'replay';
  document.body.classList.add('replaying');
  return true;
}

export function stopReplay(silent) {
  if (!st) return;
  const s = st;
  st = null;
  for (const g of s.ghosts.values()) g.dispose();
  for (const m of s.projs.values()) G.scene.remove(m);
  RP.active = false;
  RP.mode = null;
  document.body.classList.remove('replaying');
  if (!silent && s.opts.onEnd) s.opts.onEnd();
  else if (silent && s.opts.onAbort) s.opts.onAbort();
}

function feed(upTo) {
  const fr = st.clip.frames;
  while (st.fi < fr.length && fr[st.fi].s <= upTo) {
    const f = fr[st.fi++];
    for (const e of f.p) { const g = st.ghosts.get(e[0]); if (g) g.snap(f.s, e); }
  }
}

function applyEv(m) {
  const g = st.ghosts.get(m.id);
  const info = st.clip.info || {};
  if (m.t === 'fx' && m.k === 'shot') {
    const w = WEAPONS[m.w];
    if (!w || !Array.isArray(m.s)) return;
    const fast = w.rate > 8, mz = g ? g.muzzle() : null;
    const col = tracerColor(((info[m.id] || {}).skins || {})[m.w], w.tracer || 0xfff0a0);
    m.s.forEach((s, i) => fx.tracer(mz && (i === 0 || w.pellets) ? mz : s.slice(0, 3), s.slice(3), col, w.thick || (fast ? 0.03 : 0.045), fast ? 0.07 : 0.2));
    if (m.s.length) sfx.gun(m.w, m.s[0].slice(0, 3));
  } else if (m.t === 'fx' && m.k === 'swing') {
    if (g) g.swingT = performance.now();
    sfx.swing(g ? g.pos : null);
  } else if (m.t === 'fx' && m.k === 'tbag') {
    fx.explosion(m.p, 6); sfx.boom(m.p);
  } else if (m.t === 'kill') {
    const v = st.ghosts.get(m.v);
    if (v) {
      const vi = info[m.v] || {};
      const replaced = m.fx && m.fx !== 'none' && playKillFx(m.fx, { pos: v.pos.slice(), vel: m.vel || v.vel, yaw: v.yaw, color: v.color, look: vi.look, name: vi.name });
      if (replaced) v.ch.root.visible = false; else v.breakApart(m.vel || v.vel);
      v.iceUntil = 0;
    }
    if (st.opts.onKill) st.opts.onKill(m);
    if (m.k === st.opts.focus) sfx.kill();
  } else if (m.t === 'boom') {
    fx.explosion(m.p, m.r); sfx.boom(m.p);
  } else if (m.t === 'pd' && m.x) {
    fx.explosion(m.p, WEAPONS.chicken.radius); sfx.boom(m.p);
  } else if (m.t === 'he') {
    fx.blast(m.p, WEAPONS.duck.blastR); sfx.holePop(m.p);
  } else if (m.t === 'kat') {
    if (g) g.setKat(m.n);
  } else if (m.t === 'freeze') {
    if (g) g.iceUntil = st.t + m.dur; // on the replay clock, which runs slow at the good bits
  } else if (m.t === 'fx' && m.k === 'shatter') {
    fx.spray(m.p, 70, [0xffffff, 0xbfe8ff, 0x7fd0ff], 11, 1.4, 0.2, 14, 0.5); sfx.crunch(m.p);
    if (g) g.iceUntil = 0;
  }
}

function updateProjs(t, dt) {
  const fr = st.clip.frames;
  while (st.pa < fr.length - 2 && fr[st.pa + 1].s <= t) st.pa++;
  const A = fr[st.pa], B = fr[st.pa + 1] || A;
  const k = B.s > A.s ? Math.max(0, Math.min(1, (t - A.s) / (B.s - A.s))) : 0;
  const seen = new Set();
  const info = st.clip.info || {};
  for (const a of A.j || []) {
    const [id, kind, x, y, z, tip] = a;
    if (!WEAPONS[kind]) continue;
    seen.add(id);
    let mesh = st.projs.get(id);
    if (!mesh) {
      mesh = buildProjectile(kind);
      if (kind === 'bow' && mesh.userData.tip && tip) mesh.userData.tip.material = M(tipColor(tip), true);
      mesh.userData.spin = 0;
      G.scene.add(mesh);
      st.projs.set(id, mesh);
    }
    const b = (B.j || []).find((q) => q[0] === id) || a;
    const px = x + (b[2] - x) * k, py = y + (b[3] - y) * k, pz = z + (b[4] - z) * k;
    const vx = b[2] - x, vy = b[3] - y, vz = b[4] - z;
    mesh.position.set(px, py, pz);
    if ((kind === 'chicken' || kind === 'bow' || kind === 'card') && Math.hypot(vx, vy, vz) > 0.01) mesh.lookAt(px - vx, py - vy, pz - vz);
    else { mesh.userData.spin += dt * 14; mesh.rotation.set(mesh.userData.spin, mesh.userData.spin * 0.7, 0); }
    if (kind === 'chicken' && Math.random() < dt * 8) fx.feathers([px, py, pz], 1);
  }
  for (const [id, mesh] of st.projs) if (!seen.has(id)) { G.scene.remove(mesh); st.projs.delete(id); }
}

// over-the-shoulder camera on whoever the replay is about
function updateCam(dt, cam) {
  const f = st.ghosts.get(st.opts.focus);
  let eye, dir, yaw;
  if (f && f.alive && f.buf.length) {
    eye = [f.pos[0], f.pos[1] + 1.95, f.pos[2]];
    dir = f.look();
    yaw = f.yaw;
    st.lastEye = eye; st.lastYaw = yaw; st.lastDir = dir;
  } else if (st.lastEye) { // they died: drift around where they were
    st.lastYaw += dt * 0.6;
    eye = st.lastEye; yaw = st.lastYaw;
    dir = [-Math.sin(yaw) * 0.8, -0.45, -Math.cos(yaw) * 0.8];
  } else {
    const any = [...st.ghosts.values()].find((g) => g.buf.length);
    if (!any) return;
    eye = [any.pos[0], any.pos[1] + 2, any.pos[2]]; yaw = any.yaw; dir = any.look();
  }
  const right = [Math.cos(yaw), 0, -Math.sin(yaw)];
  // try the right shoulder, the left shoulder and straight up-and-behind; take whichever has the most room
  const back = 5.4;
  let best = null;
  for (const [side, up] of [[st.side || 1, 0.9], [-(st.side || 1), 0.9], [0, 2.8]]) {
    const sx = side * 1.35;
    const want = [eye[0] - dir[0] * back + right[0] * sx, eye[1] - dir[1] * back + up, eye[2] - dir[2] * back + right[2] * sx];
    const d = [want[0] - eye[0], want[1] - eye[1], want[2] - eye[2]], L = Math.hypot(...d) || 1;
    const hit = raycast(eye, [d[0] / L, d[1] / L, d[2] / L], L, BOXES);
    const free = hit ? Math.max(0.3, hit.t - 0.35) : L;
    if (!best || free > best.free + 0.4) best = { free, d, L, side };
    if (free >= L) break;
  }
  if (best.side) st.side = best.side;
  const { d, L } = best;
  tmp.set(eye[0] + (d[0] / L) * best.free, eye[1] + (d[1] / L) * best.free, eye[2] + (d[2] / L) * best.free);
  const look = new THREE.Vector3(eye[0] + dir[0] * 30, eye[1] + dir[1] * 30, eye[2] + dir[2] * 30);
  if (st.first) { camPos.copy(tmp); camLook.copy(look); st.first = false; }
  camPos.lerp(tmp, Math.min(1, dt * 14));
  camLook.lerp(look, Math.min(1, dt * 10));
  cam.position.copy(camPos);
  cam.up.set(0, 1, 0);
  cam.lookAt(camLook);
  if (Math.abs(cam.fov - 72) > 0.05) { cam.fov = 72; cam.updateProjectionMatrix(); }
}

// returns true while a replay owns the camera
export function updateReplay(dt, now, cam) {
  if (!st) return false;
  const o = st.opts;
  const slow = o.slow && o.slow.some(([a, b]) => st.t >= a && st.t <= b);
  const sp = slow ? 0.3 : 1;
  st.t += dt * 1000 * sp;
  feed(st.t + 260);
  // ghosts size themselves by distance to the camera: measure from the replay camera, not wherever you are
  if (!st.first) { cam.position.copy(camPos); cam.lookAt(camLook); cam.updateMatrixWorld(); }
  while (st.ei < st.clip.ev.length && st.clip.ev[st.ei].s <= st.t) { try { applyEv(st.clip.ev[st.ei].m); } catch (e) { console.warn('replay ev', e); } st.ei++; }
  for (const g of st.ghosts.values()) { g.frozenUntil = st.t < (g.iceUntil || 0) ? now + 1000 : 0; g.update(st.t, dt * sp, now); }
  updateProjs(st.t, dt * sp);
  updateCam(dt, cam);
  if (o.onTick) o.onTick(st.t, slow);
  if (st.t >= st.end) { stopReplay(false); return true; }
  return true;
}
