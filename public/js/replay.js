// Replays. The client keeps the last few seconds of snapshots + events (for your killcam);
// the server keeps its own recording and sends the play of the round in the same format.
// clip = { frames: [{ s, p: [snapshot entries], j: [[id, kind, x, y, z, tip]] }], ev: [{ s, m }], info: { id: {...} } }
import * as THREE from 'three';
import { G } from './ctx.js';
import { Remote } from './remote.js';
import { buildProjectile, tipColor, teamLook, M } from './models.js';
import { crossEvent } from './bloodcross.js';
import { fx } from './fx.js';
import { marbles } from './marbles.js';
import { sfx } from './audio.js';
import { tracerColor } from './skins.js';
import { playKillFx } from './killfx.js';
import { rigFx, rigDied } from './rig.js'; // overdrive rig killstreak
import { courtReplay } from './scales.js';
import { replayNoScope } from './noscope.js';
import { shredKill } from './shredder.js';
import { WEAPONS } from '/shared/weapons.js';
import { wreckFx, wreckDied } from './wreck.js';
import { TEAMS, GAMES } from '/shared/modes.js';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';
import { soapBubble, soapFlail } from './models.js';
import { TRAP, trapPreroll } from '/shared/wand.js';
import { patchPreroll } from '/shared/marbles.js';

const KEEP = 10000;
// other modules' replay bits (the new gear: photo frames, pop quizzes, laser beams, goggle flashes). each hook may have
// ev(m, ghosts, t) -> true if it handled the event, pre(m, ghosts, s) for events from before the clip that set things up,
// step(t, ghosts, dt) every replay frame, stop() when it ends, preroll(ev, t0) -> extra events a local clip needs
export const RP_HOOKS = [];
export const rec = { frames: [], ev: [] };
const r2 = (x) => Math.round(x * 100) / 100;

export function recordSnap(m) {
  const j = [];
  for (const pr of G.projs.values()) j.push([pr.id, pr.k, r2(pr.p[0]), r2(pr.p[1]), r2(pr.p[2]), pr.tip || 0]);
  rec.frames.push({ s: m.s, p: m.p, j });
  while (rec.frames.length && rec.frames[0].s < m.s - KEEP) rec.frames.shift();
  while (rec.ev.length && rec.ev[0].s < m.s - KEEP) rec.ev.shift();
}
// events come down the same socket as the snapshots, so each one happened after the last snapshot and before the next
// (50 ms later): a slow frame or a late packet can't stamp a kill after the frame that already shows the victim dead
export function recordEv(m) {
  const s = performance.now() + G.offset, last = rec.frames.length ? rec.frames[rec.frames.length - 1].s : null;
  rec.ev.push({ s: last == null ? s : Math.min(Math.max(s, last), last + 50), m });
}
export function clearRec() { rec.frames.length = 0; rec.ev.length = 0; }
export function serverNow() { return performance.now() + G.offset; }

export function localClip(t0, t1, infoOf) {
  const frames = rec.frames.filter((f) => f.s >= t0 && f.s <= t1);
  const ev = rec.ev.filter((e) => e.s >= t0 && e.s <= t1);
  ev.unshift(...trapPreroll(rec.ev, t0)); // someone already floating in a soap bubble when the clip starts
  for (const h of RP_HOOKS) if (h.preroll) ev.unshift(...h.preroll(rec.ev, t0));
  ev.unshift(...patchPreroll(rec.ev, t0)); // marbles already on the floor
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
  const tg = GAMES[G.round && G.round.game] && GAMES[G.round.game].teams;
  for (const [k, inf] of Object.entries(clip.info || {})) {
    const id = Number(k);
    const i = inf || {};
    // team colour beats clothes on ghosts too (clips without a team field: a team colour means a team, in a team game)
    const team = i.team ?? (tg && Object.values(TEAMS).some((t) => t.color === i.color) ? 1 : 0);
    const g = new Remote(id, i.level ? `${i.name} [${i.level}]` : (i.name || '???'), i.color || '#ffffff', i.skins || {}, !!i.bot, i.look || null, team);
    // katana length at the start of the clip: what it was before its first recorded change (was: our own recording
    // knows; a growth is one more than before), else what it was when clipped
    const k0 = (clip.ev || []).find((e) => e.m && e.m.t === 'kat' && e.m.id === id);
    g.katN = k0 && k0.m.was != null ? k0.m.was : k0 && k0.m.n > 0 ? k0.m.n - 1 : (i.kat || 0);
    g.ghost = true;
    g.setGrapple(i.grap);
    if (i.zs && i.zs <= clip.frames[0].s) g.setZombie(true); // infection: already a zombie when the clip starts
    if (id === opts.focus) g.tag.visible = false;
    ghosts.set(id, g);
  }
  const frames = clip.frames, t0 = frames[0].s;
  st = {
    clip, opts, ghosts, projs: new Map(), t: t0, fi: 0, pa: 0, si: 0,
    ei: 0, end: Math.min(opts.end || Infinity, frames[frames.length - 1].s), first: true, lastEye: null, lastYaw: 0,
  };
  while (st.ei < clip.ev.length && clip.ev[st.ei].s < t0) st.ei++;
  for (const e of clip.ev) if (e.s < t0 && e.m.t === 'trap') trapGhost(e.m, e.s); // sealed in before the clip starts
  for (const e of clip.ev) if (e.s < t0) for (const h of RP_HOOKS) if (h.pre) h.pre(e.m, ghosts, e.s, t0);
  RP.active = true;
  RP.mode = opts.mode || 'replay';
  RP.focus = opts.focus; // whose replay it is
  document.body.classList.add('replaying');
  return true;
}

export function stopReplay(silent) {
  if (!st) return;
  const s = st;
  st = null;
  for (const g of s.ghosts.values()) if (g.soap) { G.scene.remove(g.soap.mesh); g.soap.mesh.material.dispose(); }
  for (const h of RP_HOOKS) if (h.stop) h.stop();
  for (const g of s.ghosts.values()) g.dispose();
  for (const m of s.projs.values()) G.scene.remove(m);
  for (const k of s.mp || []) marbles.dropPatch(k); // the replay's marbles on the floor
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
    for (const e of f.p) {
      const g = st.ghosts.get(e[0]);
      if (!g) continue;
      const up = g.alive || g.downAt;
      g.snap(f.s, e);
      // frames go in early (for smooth movement) but a death only shows once the replay gets there: they're still standing when the shot lands
      if (!e[11] && up && f.s > st.t) { g.alive = true; g.downAt = g.downAt || f.s; }
    }
  }
}

function applyEv(m) {
  for (const h of RP_HOOKS) if (h.ev && h.ev(m, st.ghosts, st.t)) return;
  if (m.t === 'trap' || m.t === 'trapx') { trapGhost(m, st.t); return; }
  if (m.t === 'mpatch' || m.t === 'mslip' || m.t === 'mpx') { ghostPatch(m); return; }
  const g = st.ghosts.get(m.id);
  const info = st.clip.info || {};
  if (m.t === 'fx' && m.k === 'verdict') return courtReplay(m, g, st.opts.focus); // scales of justice: the stamp + gold
  if (m.t === 'fx' && m.k === 'shot') {
    const w = WEAPONS[m.w];
    if (!w || !Array.isArray(m.s)) return;
    if (g && w.fanHammer) g.revShot(!!m.fan); // ghosts twirl their revolvers too
    const fast = w.rate > 8, mz = g ? g.muzzle() : null;
    const col = tracerColor(((info[m.id] || {}).skins || {})[m.w], w.tracer || 0xfff0a0);
    if (w.marbles) { const sk = ((info[m.id] || {}).skins || {})[m.w]; marbles.shootSegs(m.s, mz, sk && sk[3] === 'marbles_gumball' ? 'gumball' : 'glass', 2); if (m.s.length) sfx.gun(m.w, m.s[0].slice(0, 3)); return; }
    m.s.forEach((s, i) => fx.tracer(mz && (i === 0 || w.pellets) ? mz : s.slice(0, 3), s.slice(3), col, w.thick || (fast ? 0.03 : 0.045), fast ? 0.07 : 0.2));
    if (m.s.length) sfx.gun(m.w, m.s[0].slice(0, 3));
  } else if (m.t === 'fx' && m.k === 'swing') {
    if (g) g.swingT = performance.now();
    if (m.w === 'popper' && g) { g.popItem('popper', 450); fx.confetti(g.itemMuzzle(), g.look(), g.vel); sfx.popper(g.pos); return; } // the popper item
    sfx.swing(g ? g.pos : null);
  } else if (m.t === 'fx' && m.k === 'tbag') {
    fx.explosion(m.p, 6); sfx.boom(m.p);
  } else if (m.t === 'fx' && (m.k === 'slam' || m.k === 'ram')) {
    wreckFx(m, true); // wrecking ball slams + rams (the ghost itself already rolls as a ball from its snapshot flags)
  } else if (m.t === 'guard') { // katana parry: the guard pose
    if (g) g.parryT = performance.now();
  } else if (m.t === 'parry') { // ...and what it bounced. only the first thing in a window SHINGs (n = its count), like live
    if (g) g.parryHitT = performance.now();
    const big = !(m.n > 1), dl = g ? Math.hypot(m.p[0] - g.pos[0], m.p[2] - g.pos[2]) || 1 : 0;
    fx.sparks(m.p, g ? [(m.p[0] - g.pos[0]) / dl, 0, (m.p[2] - g.pos[2]) / dl] : null, big ? (m.pf ? 40 : 24) : 8, !!m.pf);
    if (big) sfx.parry(m.p, !!m.pf); else sfx.tink(m.p);
    if (m.b) fx.tracer(m.p, m.b, 0xffffff, 0.07, 0.3);
  } else if (m.t === 'kill') {
    const v = st.ghosts.get(m.v);
    if (v && m.w === 'shredder' && shredKill(m, st.ghosts)) m.fx = 'none'; // through the killer's machine
    if (v) {
      const vi = info[m.v] || {};
      const replaced = m.fx && m.fx !== 'none' && playKillFx(m.fx, { pos: v.pos.slice(), vel: m.vel || v.vel, yaw: v.yaw, color: v.color, look: teamLook(vi.look, v.team), name: vi.name });
      wreckDied(v, m.vel); // they died as a wrecking ball: it bursts open
      if (replaced) v.ch.root.visible = false; else v.breakApart(m.vel || v.vel);
      v.alive = false; v.downAt = 0; // now they're down
      v.iceUntil = 0;
      rigDied(v, m.vel); // died in the overdrive rig: it bursts into scrap
      v.rpAlive = false; // gone from here on, even if the frame saying so is a few ms later
    }
    if (st.opts.onKill) st.opts.onKill(m);
    if (m.k === st.opts.focus) sfx.kill();
  } else if (m.t === 'boom') {
    fx.explosion(m.p, m.r); sfx.boom(m.p);
  } else if (m.t === 'bcross') {
    crossEvent(m, st.ghosts, info); // the X sticks to the ghost, bursts, pops
  } else if (m.t === 'pd' && m.x) {
    fx.explosion(m.p, WEAPONS.chicken.radius); sfx.boom(m.p);
  } else if (m.t === 'he') {
    fx.blast(m.p, WEAPONS.duck.blastR); sfx.holePop(m.p);
  } else if (m.t === 'rig') {
    rigFx(m, st.ghosts); // overdrive rig punches, hacks, missiles, landings (the ghosts wear the rig from their snapshots)
  } else if (m.t === 'ns') { // no-scope headshot: the fireworks again, on a faster fuse
    replayNoScope(m, (info[m.k] || {}).name);
  } else if (m.t === 'kat') {
    if (g) g.setKat(m.n);
  } else if (m.t === 'freeze') {
    if (g) g.iceUntil = st.t + m.dur; // on the replay clock, which runs slow at the good bits
  } else if (m.t === 'fx' && m.k === 'shatter') {
    fx.spray(m.p, 70, [0xffffff, 0xbfe8ff, 0x7fd0ff], 11, 1.4, 0.2, 14, 0.5); sfx.crunch(m.p);
    if (g) g.iceUntil = 0;
  }
}

// who's alive (and their flags) on the replay clock. feed() runs 260 ms ahead so positions always have a next frame to
// interpolate to, and the death frame fed that early used to hide the victim before the killing shot, so the kill had
// nobody left to blow up. here a death waits for its kill event (which can land a frame either side of the snapshot)
function killDue(id, s) {
  const ev = st.clip.ev;
  for (let i = st.ei; i < ev.length && ev[i].s <= s + 600; i++) if (ev[i].m && ev[i].m.t === 'kill' && ev[i].m.v === id) return true;
  return false;
}
function settle() {
  const fr = st.clip.frames;
  while (st.si < fr.length && fr[st.si].s <= st.t) {
    const f = fr[st.si++];
    for (const e of f.p) {
      const g = st.ghosts.get(e[0]);
      if (!g) continue;
      const was = g.rpWas;
      g.rpWas = !!e[11]; g.rpF = e[13];
      if (e[11] && !was) g.rpAlive = true; // first frame, or respawned
      else if (!e[11] && g.rpAlive && !killDue(g.id, f.s)) g.rpAlive = false; // died with no kill event on the way
    }
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

// bubble wand: a giant soap bubble round whoever was sealed in ('trap'), popped by 'trapx' or when it runs out
function trapGhost(m, s) {
  const g = st.ghosts.get(m.id), T = g && g.soap;
  if (!g) return;
  if (T) { G.scene.remove(T.mesh); T.mesh.material.dispose(); g.soap = null; }
  if (m.t === 'trapx') {
    if (T && m.why !== 'gone') { const p = T.mesh.position.toArray(); fx.droplets(p, T.mesh.scale.x, 60); sfx.bigPop(p); }
    return;
  }
  g.soap = { mesh: soapBubble(1, 28, 0.025), s, until: s + (m.left || 0) };
  G.scene.add(g.soap.mesh);
}
function stepTrapGhosts(t) {
  for (const g of st.ghosts.values()) {
    const T = g.soap;
    if (!T) continue;
    if (t > T.until + 300) { trapGhost({ t: 'trapx', id: g.id, why: 'time' }, t); continue; } // the clip lost its pop
    const ds = g.distScale || 1, x = Math.min(1, (t - T.s) / 300) - 1, grow = 1 + 2.70158 * x * x * x + 1.70158 * x * x;
    T.mesh.position.set(g.pos[0], g.pos[1] + TRAP.y * ds, g.pos[2]);
    T.mesh.scale.setScalar(TRAP.r * ds * Math.max(0.2, grow));
    T.mesh.visible = g.ch.root.visible;
    soapFlail(g.ch, t * 0.001 + g.id);
  }
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
  punchIn(cam);
}

// epic killcams: opts.punch(t) (0..1) swings the camera onto opts.victim and narrows the lens down to 72 / opts.zoom
const punchV = new THREE.Vector3();
function punchIn(cam) {
  const o = st.opts;
  if (!o.punch) return;
  const v = st.ghosts.get(o.victim);
  if (v && v.alive && v.buf.length) st.vAt = [v.pos[0], v.pos[1] + 1.3, v.pos[2]]; // after they drop, keep looking where they were
  const p = Math.max(0, Math.min(1, o.punch(st.t) || 0));
  if (!st.vAt || p <= 0) return;
  const k = p * p * (3 - 2 * p);
  cam.lookAt(punchV.set(st.vAt[0], st.vAt[1], st.vAt[2]).sub(camLook).multiplyScalar(k).add(camLook));
  cam.fov = 72 / (1 + ((o.zoom || 1) - 1) * k);
  cam.updateProjectionMatrix();
}

// returns true while a replay owns the camera
export function updateReplay(dt, now, cam) {
  if (!st) return false;
  const o = st.opts;
  // replays keep to the wall clock (the frame dt is capped at 0.1 s): on a slow PC (down to ~2 fps) the killcam still ends before the server respawns you
  dt = st.wall ? Math.min(0.5, Math.max(0, (now - st.wall) / 1000)) : dt;
  st.wall = now;
  const slow = o.slow && o.slow.find(([a, b]) => st.t >= a && st.t <= b);
  const sp = slow ? slow[2] || 0.3 : 1; // slow windows are [from, to, speed?]
  // bloodcross.js runs the replay's crosses on replay time (this wall-clock step x the slow-mo), so the spikes keep pace with the ghosts
  RP.sp = sp; RP.dt = dt;
  st.t += dt * 1000 * sp;
  feed(st.t + 260);
  for (const g of st.ghosts.values()) if (g.downAt && st.t >= g.downAt + 400) { g.alive = false; g.downAt = 0; } // died with no kill event in the clip
  // ghosts size themselves by distance to the camera: measure from the replay camera, not wherever you are
  if (!st.first) { cam.position.copy(camPos); cam.lookAt(camLook); cam.updateMatrixWorld(); }
  while (st.ei < st.clip.ev.length && st.clip.ev[st.ei].s <= st.t) { try { applyEv(st.clip.ev[st.ei].m); } catch (e) { console.warn('replay ev', e); } st.ei++; }
  settle();
  // draw them with the replay-clock state, then hand back what feed() set (it spots respawns by it)
  for (const g of st.ghosts.values()) {
    g.fedAlive = g.alive; g.fedF = g.f;
    if (g.rpAlive !== undefined) { g.alive = g.rpAlive; g.f = g.rpF; }
    g.frozenUntil = st.t < (g.iceUntil || 0) ? now + 1000 : 0; g.update(st.t, dt * sp, now);
  }
  stepTrapGhosts(st.t);
  for (const h of RP_HOOKS) if (h.step) h.step(st.t, st.ghosts, dt * sp);
  updateProjs(st.t, dt * sp);
  updateCam(dt, cam);
  for (const g of st.ghosts.values()) { g.alive = g.fedAlive; g.f = g.fedF; }
  if (o.onTick) o.onTick(st.t, slow);
  if (st.t >= st.end) { stopReplay(false); return true; }
  return true;
}

// marbles on the floor (Marble Shotgun) in a replay: keyed -id so they never mix with the live ones
function ghostPatch(m) {
  const k = -m.id;
  if (!Number.isFinite(k)) return;
  if (m.t === 'mpatch') {
    if (!Array.isArray(m.c) || marbles.patches.has(m.id)) return; // still on the floor live: don't draw it twice
    const sk = (((st.clip.info || {})[m.o] || {}).skins || {}).marbles;
    marbles.addPatch(k, m, sk && sk[3] === 'marbles_gumball' ? 'gumball' : 'glass');
    (st.mp ||= new Set()).add(k);
  } else if (m.t === 'mslip') { if (Array.isArray(m.p)) { marbles.thinPatch(k, m.n, m.r, m.p); sfx.clatter(m.p); } }
  else marbles.dropPatch(k);
}
