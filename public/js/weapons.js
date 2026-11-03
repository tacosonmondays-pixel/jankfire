// Local weapon logic, loadouts, ammo + first-person viewmodels.
import * as THREE from 'three';
import { WEAPONS, ORDER, SLOTS, FLAGS, HIPFIRE, ARROW_TIPS, SUITS, RANKS, validLoadout, DEFAULT_LOADOUT } from '/shared/weapons.js';
import { BOXES } from '/shared/map.js';
import { raycast, rayBox } from '/shared/physics.js';
import { G } from './ctx.js';
import { ME, eye, look, applyKb, hspeed } from './player.js';
import { buildWeapon, M, cardFace, tipColor } from './models.js';
import { fx } from './fx.js';
import { sfx, loopSfx, stopLoops } from './audio.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { tracerColor, emitSkinFx } from './skins.js';
import { ANIMS, sample, eventsBetween, inspectFor } from './anim.js';

export const W = {
  slots: [DEFAULT_LOADOUT.primary, DEFAULT_LOADOUT.secondary, DEFAULT_LOADOUT.melee],
  slot: 0, prevSlot: 1, cur: DEFAULT_LOADOUT.primary,
  held: false, cd: {}, ammo: {}, reloadId: null, reloadUntil: 0, bloom: 0, spin: 0,
  charge: 0, exhale: 0, coughLock: false, fuel: { blower: WEAPONS.blower.fuel }, tick: 0,
  swing: 0, swingId: null, pendingSwing: 0, kick: 0, swap: 0, flags: 0, bob: 0,
  slipperOut: false, slipperT: 0, reverseUntil: 0,
  aimHeld: false, aim: 0, zoom: 1, scoped: false,
  anim: null, lastSwingT: 0, combo: 0, pendingThrow: 0, inspectSpin: 0,
  hasScythe: false, dashHeld: false, dashFuel: WEAPONS.dash.max, dashHitT: new Map(),
  draw: 0, cardSel: 0,
};

// ------------------------------------------------------------ card deck
export function cycleCard() { const n = (G.hand || []).length; if (n) { W.cardSel = (W.cardSel + 1) % n; sfx.click(); } }
export function redrawCards() { net.send({ t: 'redraw' }); sfx.swing(); }
function playCard(now) {
  const hand = G.hand || [];
  if (!hand.length) return;
  setCd('cards', now);
  const i = Math.min(W.cardSel, hand.length - 1);
  net.send({ t: 'fire', w: 'cards', i, o: eye().map(r2), d: look().map(r2) });
  W.kick = 0.6;
  sfx.swing();
}
const isScythe = (id) => id === 'scythe' || id === 'scythe_rifle';

function playAnim(name, kind) { if (ANIMS[name]) W.anim = { name, kind, t: 0 }; }
function cancelInspect() { if (W.anim && W.anim.kind === 'inspect') W.anim = null; }
export function inspect() {
  if (!ME.alive || W.reloadId || W.aim > 0.1 || (W.anim && W.anim.kind !== 'inspect')) return;
  if (W.cur === 'slipper' && W.slipperOut) return;
  playAnim(inspectFor(W.cur, models[W.cur] && models[W.cur].g.userData.model), 'inspect');
}

// viewmodel placement per weapon: position, rotation, scale
const VM = {
  ar: { p: [0.2, -0.2, -0.38], r: [0, 0.04, 0], s: 0.7 },
  smg: { p: [0.2, -0.19, -0.36], r: [0, 0.05, 0], s: 0.8 },
  shotgun: { p: [0.2, -0.2, -0.36], r: [0, 0.04, 0], s: 0.7 },
  minigun: { p: [0.22, -0.26, -0.42], r: [0, 0.03, 0], s: 0.7 },
  sniper: { p: [0.2, -0.2, -0.38], r: [0, 0.03, 0], s: 0.5 },
  chicken: { p: [0.22, -0.2, -0.42], r: [0, 0.04, 0], s: 0.65 },
  bowling: { p: [0.24, -0.24, -0.42], r: [0, 0.04, 0], s: 0.6 },
  banana: { p: [0.2, -0.2, -0.38], r: [0, 0.05, 0], s: 0.8 },
  revolver: { p: [0.17, -0.16, -0.32], r: [0, 0.06, 0], s: 1.0 },
  cig: { p: [0.15, -0.17, -0.3], r: [0.15, 0.6, 0.2], s: 1.1 },
  blower: { p: [0.24, -0.27, -0.45], r: [0, 0.05, 0], s: 0.6 },
  popper: { p: [0.17, -0.18, -0.34], r: [0.1, 0.1, 0], s: 0.75 },
  reverse: { p: [0.15, -0.15, -0.34], r: [0.3, -0.3, 0.15], s: 0.65 },
  duck: { p: [0.17, -0.18, -0.4], r: [0.1, 0.5, 0], s: 0.55 },
  bread: { p: [0.3, -0.3, -0.42], r: [0.35, 0.2, -0.25], s: 0.55 },
  slipper: { p: [0.17, -0.18, -0.36], r: [0.2, 0.3, 0.3], s: 0.7 },
  spoon: { p: [0.15, -0.15, -0.3], r: [0.2, 0.25, 0.1], s: 1.3 },
  knife: { p: [0.16, -0.17, -0.3], r: [0.15, 0.2, 0.15], s: 1.3 },
  bow: { p: [0.1, -0.12, -0.36], r: [0, 0.05, 0.3], s: 1.0 },
  cards: { p: [0.1, -0.15, -0.3], r: [-0.35, 0.15, 0.05], s: 1.15 },
  slapper: { p: [0.22, -0.24, -0.42], r: [0.25, 0.1, 0], s: 0.7 },
  scythe: { p: [0.3, -0.33, -0.46], r: [0.25, 0.25, -0.3], s: 0.55 },
  scythe_rifle: { p: [0.2, -0.21, -0.4], r: [0, 0.03, 0], s: 0.6 },
};

let vmRoot;
const models = {};
const tmpV = new THREE.Vector3();

export function initWeapons() {
  vmRoot = new THREE.Group();
  G.vmScene.add(vmRoot);
  rebuildViewmodels();
  refillAmmo();
}

export function rebuildViewmodels() {
  for (const id of ORDER) {
    if (!VM[id]) continue;
    if (models[id]) vmRoot.remove(models[id].wrap);
    const wrap = new THREE.Group();
    const g = buildWeapon(id, (G.equipped || {})[id]);
    const cfg = VM[id];
    g.scale.setScalar(cfg.s);
    wrap.add(g);
    const hand = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.08, 0.12), M(0xf1c27d));
    hand.position.set(0.005, -0.05, 0.04);
    wrap.add(hand);
    wrap.position.set(...cfg.p);
    wrap.rotation.set(...cfg.r);
    wrap.visible = id === W.cur;
    vmRoot.add(wrap);
    models[id] = { wrap, g, cfg };
  }
}

// ------------------------------------------------------------ killstreak scythe (4th slot)
export function grantScythe() {
  W.hasScythe = true;
  W.slots[3] = 'scythe';
  W.dashFuel = WEAPONS.dash.max;
  W.ammo.scythe_rifle = WEAPONS.scythe_rifle.mag;
  hud.slots(W.slots);
  equip(3);
}
export function loseScythe() {
  if (!W.hasScythe) return;
  W.hasScythe = false;
  W.slots.length = 3;
  ME.dashing = false;
  hud.slots(W.slots);
  if (W.slot === 3) { W.cur = null; equip(0); }
}
export function toggleScythe() {
  if (!isScythe(W.cur) || W.anim && W.anim.kind === 'swing') return;
  W.slots[3] = W.cur === 'scythe' ? 'scythe_rifle' : 'scythe';
  equip(3);
  W.swap = 0;
  playAnim('fold_scythe', 'fold');
}

export function refillAmmo() {
  for (const id of ORDER) if (WEAPONS[id].mag) W.ammo[id] = WEAPONS[id].mag;
  W.reloadId = null;
  W.fuel.blower = WEAPONS.blower.fuel;
  W.slipperOut = false;
}

export function setLoadout(lo) {
  const v = validLoadout(lo);
  const streakSlot = W.hasScythe ? (W.slots[3] || 'scythe') : null;
  W.slots = SLOTS.map((s) => v[s]);
  if (streakSlot) W.slots[3] = streakSlot;
  if (W.slot >= W.slots.length) W.slot = 0;
  hud.slots(W.slots);
  W.cur = null;
  equip(W.slot);
}

export function rebuildOne(id) {
  rebuildViewmodels();
  for (const k of ORDER) if (models[k]) models[k].wrap.visible = k === W.cur;
}

function equip(i) {
  const id = W.slots[i];
  if (id === W.cur) return;
  W.aim = 0;
  W.anim = null; W.pendingThrow = 0;
  stopLoops();
  W.charge = 0; W.exhale = 0; W.spin = 0; W.reloadId = null;
  W.swing = 0; W.pendingSwing = 0;
  W.cur = id;
  W.slot = i;
  W.swap = 1;
  for (const k of ORDER) if (models[k]) models[k].wrap.visible = k === id;
  hud.weapon(id, i);
  sfx.click();
}

export function switchSlot(i) {
  if (i < 0 || i >= W.slots.length || i === W.slot) return;
  W.prevSlot = W.slot;
  equip(i);
}
export function lastSlot() { switchSlot(W.prevSlot); }
export function cycleSlot(dir) { const n = W.slots.length; switchSlot((W.slot + dir + n) % n); }

export function reload() {
  cancelInspect();
  if (W.cur === 'cards') { redrawCards(); return; }
  const id = W.cur, w = WEAPONS[id];
  if (!w.mag || W.reloadId || W.ammo[id] >= w.mag || !ME.alive) return;
  W.reloadId = id;
  W.reloadUntil = performance.now() + w.reload * 1000;
  sfx.reload();
}

export function muzzleWorld() {
  const m = models[W.cur];
  vmRoot.updateMatrixWorld(true);
  tmpV.copy(m.g.userData.muzzle);
  m.g.localToWorld(tmpV);
  G.camera.updateMatrixWorld();
  G.camera.localToWorld(tmpV);
  return [tmpV.x, tmpV.y, tmpV.z];
}

const ready = (id, now) => (W.cd[id] || 0) <= now;
function interval(id) { const w = WEAPONS[id]; return w.rate ? 1 / w.rate : w.cd; }
function setCd(id, now) {
  const iv = interval(id) * 1000;
  W.cd[id] = Math.max(W.cd[id] || 0, now - Math.min(40, iv * 0.5)) + iv; // keeps auto fire rate steady at low fps
}

function rayPlayers(o, d, maxT) {
  let best = null;
  for (const r of G.remotes.values()) {
    if (!r.alive) continue;
    for (const hb of r.hitboxes()) {
      const h = rayBox(o, d, hb, best ? best.t : maxT);
      if (h && (!best || h.t < best.t)) best = { t: h.t, r, head: hb.head };
    }
  }
  return best;
}

function conePlayers(o, d, range, cone) {
  const out = [], cosC = Math.cos(cone);
  for (const r of G.remotes.values()) {
    if (!r.alive) continue;
    const tx = r.pos[0] - o[0], ty = r.pos[1] + 1 - o[1], tz = r.pos[2] - o[2];
    const dist = Math.hypot(tx, ty, tz);
    if (dist > range || dist < 1e-3) continue;
    const dir = [tx / dist, ty / dist, tz / dist];
    if (dist > 1.5 && dir[0] * d[0] + dir[1] * d[1] + dir[2] * d[2] < cosC) continue;
    if (raycast(o, dir, dist, BOXES)) continue;
    out.push({ r, dist, dir });
  }
  return out;
}

function spreadDir(d, s) {
  if (!s) return d;
  const up = Math.abs(d[1]) < 0.99 ? [0, 1, 0] : [1, 0, 0];
  let r = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]];
  const rl = Math.hypot(...r); r = r.map((x) => x / rl);
  const u = [r[1] * d[2] - r[2] * d[1], r[2] * d[0] - r[0] * d[2], r[0] * d[1] - r[1] * d[0]];
  const a = Math.random() * Math.PI * 2, m = Math.sqrt(Math.random()) * s;
  const out = [d[0] + (r[0] * Math.cos(a) + u[0] * Math.sin(a)) * m, d[1] + (r[1] * Math.cos(a) + u[1] * Math.sin(a)) * m, d[2] + (r[2] * Math.cos(a) + u[2] * Math.sin(a)) * m];
  const l = Math.hypot(...out);
  return out.map((x) => x / l);
}

const r2 = (x) => Math.round(x * 100) / 100;

function currentSpread(w) {
  if (G.spinning) return 0; // spinbot = no spread
  const hip = (HIPFIRE[G.cfg.hip] || HIPFIRE.normal).mul;
  const base = (w.spread || 0) + W.bloom;
  const ads = w.ads ? base * (w.ads.spread ?? 1) * Math.min(1, hip) : base * hip;
  const hipS = base * hip;
  return hipS + (ads - hipS) * W.aim;
}

function fireHitscan(id, now) {
  const w = WEAPONS[id];
  if (w.mag && G.mode !== 'training') W.ammo[id]--;
  setCd(id, now);
  const o = eye(), base = look(), mz = muzzleWorld();
  const hits = new Map();
  const segs = [];
  const pellets = w.pellets || 1;
  for (let i = 0; i < pellets; i++) {
    let d = spreadDir(base, currentSpread(w));
    let from = o, left = w.range, bounces = w.ricochet || 0, drawFrom = mz;
    for (;;) {
      const mh = raycast(from, d, left, BOXES);
      const maxT = mh ? mh.t : left;
      const ph = rayPlayers(from, d, maxT);
      const t = ph ? ph.t : maxT;
      const end = [from[0] + d[0] * t, from[1] + d[1] * t, from[2] + d[2] * t];
      segs.push([...drawFrom, ...end]);
      if (ph) {
        const h = hits.get(ph.r.id) || { n: 0, h: 0, d };
        h.n++; if (ph.head) h.h++; h.d = d;
        hits.set(ph.r.id, h);
        break;
      }
      if (!mh) break;
      fx.impact(end, mh.normal);
      if (bounces-- <= 0) break;
      const dn = d[0] * mh.normal[0] + d[1] * mh.normal[1] + d[2] * mh.normal[2];
      d = [d[0] - 2 * dn * mh.normal[0], d[1] - 2 * dn * mh.normal[1], d[2] - 2 * dn * mh.normal[2]];
      from = [end[0] + mh.normal[0] * 0.02, end[1] + mh.normal[1] * 0.02, end[2] + mh.normal[2] * 0.02];
      drawFrom = from;
      left -= t;
      sfx.ricochet(end);
    }
  }
  for (const [rid, h] of hits) net.send({ t: 'hit', to: rid, w: id, d: h.d.map(r2), n: h.n, h: h.h });
  const fast = w.rate > 8;
  const skin = (G.equipped || {})[id];
  for (const s of segs) fx.tracer(s.slice(0, 3), s.slice(3), tracerColor(skin, w.tracer || 0xfff0a0), w.thick || (fast ? 0.03 : 0.045), fast ? 0.07 : 0.2);
  net.send({ t: 'fire', w: id, o: o.map(r2), s: segs.slice(0, 12).map((s) => s.map(r2)) });
  if (w.recoil) applyKb([-base[0] * w.recoil, -base[1] * w.recoil, -base[2] * w.recoil]);
  ME.pitch = Math.min(1.55, ME.pitch + (w.kick || 0) * (0.6 + Math.random() * 0.8) * (1 - W.aim * 0.5));
  ME.yaw += (Math.random() - 0.5) * (w.kick || 0) * 0.5;
  W.bloom = Math.min(w.maxBloom || 0, W.bloom + (w.bloom || 0));
  W.kick = Math.min(1, W.kick + (fast ? 0.25 : 1));
  if (id === 'sniper' || id === 'shotgun') G.shake = Math.max(G.shake, 0.6);
  sfx.gun(id);
  if (w.mag && W.ammo[id] <= 0) reload();
}

function fireProj(id, now, fromAnim) {
  const w = WEAPONS[id];
  if (id === 'slipper') {
    if (W.slipperOut) return;
    if (!fromAnim) { setCd(id, now); playAnim('throw_slipper', 'throw'); W.pendingThrow = ANIMS.throw_slipper.hit; return; }
    W.slipperOut = true;
    W.slipperT = now;
  }
  if (!fromAnim) setCd(id, now);
  net.send({ t: 'fire', w: id, o: eye().map(r2), d: look().map(r2) });
  if (id === 'chicken') sfx.squawk();
  else if (id === 'duck') sfx.squeak();
  else if (id === 'bowling') sfx.thunk();
  else if (id === 'slipper') { /* the throw animation already whooshed */ }
  else sfx.pew();
  W.kick = id === 'chicken' || id === 'bowling' ? 0.8 : 0.35;
}

function swing(id, now) {
  const w = WEAPONS[id];
  setCd(id, now);
  W.swing = 1;
  W.swingId = id;
  net.send({ t: 'fire', w: id, o: eye().map(r2), d: look().map(r2) });
  if (id === 'popper') {
    const d = look();
    fx.confetti(muzzleWorld(), d, ME.vel);
    sfx.popper();
    applyKb([-d[0] * w.recoil, -d[1] * w.recoil, -d[2] * w.recoil]);
    playAnim('yank_popper', 'swing');
    resolveSwing(id);
    return;
  }
  // chain swings: click again quickly and you get the backhand / second stab
  W.combo = now - W.lastSwingT < 750 ? W.combo + 1 : 0;
  W.lastSwingT = now;
  const name = `swing_${id}${W.combo % 2 ? '2' : ''}`;
  if (ANIMS[name]) { playAnim(name, 'swing'); W.pendingSwing = ANIMS[name].hit; }
  else { sfx.swing(); W.pendingSwing = w.delay || 0.05; }
}

function resolveSwing(id) {
  const w = WEAPONS[id];
  const o = eye(), d = look();
  const targets = conePlayers(o, d, w.range, w.cone);
  if (targets.length) {
    for (const tg of targets) net.send({ t: 'hit', to: tg.r.id, w: id, d: d.map(r2) });
    if (id === 'spoon') sfx.ting(); else if (id !== 'popper') sfx.bonk();
    G.shake = Math.max(G.shake, 0.35);
    return;
  }
  if (w.pogo) {
    const mh = raycast(o, d, w.range, BOXES);
    if (mh) {
      applyKb([-d[0] * w.pogo, -d[1] * w.pogo, -d[2] * w.pogo]);
      fx.impact(mh.point, mh.normal);
      sfx.bonk();
    }
  }
}

function useReverse(now) {
  const w = WEAPONS.reverse;
  setCd('reverse', now);
  W.reverseUntil = now + w.dur * 1000;
  net.send({ t: 'fire', w: 'reverse', o: eye().map(r2), d: look().map(r2) });
  sfx.reverse();
  hud.msg('REVERSE', w.dur, 'reverse');
}

function cough() {
  net.send({ t: 'cough' });
  sfx.cough();
  hud.msg('*cough cough*', 1.2);
  fx.smoke(eye(), 25, 0.4);
  W.charge = 0;
  W.coughLock = true;
  G.shake = Math.max(G.shake, 0.5);
}

export function fireDown() {
  W.held = true;
  cancelInspect();
  const id = W.cur, w = WEAPONS[id], now = performance.now();
  if (!ME.alive || W.reloadId === id || !ready(id, now)) return;
  if (w.kind === 'hitscan' && !w.auto && !w.spinup) {
    if (W.ammo[id] > 0) fireHitscan(id, now); else { sfx.empty(); reload(); }
  } else if (w.kind === 'melee') swing(id, now);
  else if (w.kind === 'proj' && !w.auto) fireProj(id, now);
  else if (w.kind === 'reverse') useReverse(now);
  else if (w.kind === 'cards') playCard(now);
}

export function fireUp() {
  W.held = false;
  W.coughLock = false;
  if (W.cur === 'bow') {
    const now = performance.now();
    if (W.draw >= 0.15 && ME.alive && ready('bow', now)) {
      setCd('bow', now);
      net.send({ t: 'fire', w: 'bow', o: eye().map(r2), d: look().map(r2), c: Math.round(W.draw * 100) / 100 });
      sfx.bowShot(); W.kick = 0.5;
    }
    W.draw = 0;
  }
  if (W.cur === 'cig') {
    if (W.charge > 0.12) {
      W.exhale = Math.min(W.charge, WEAPONS.cig.maxCharge) * WEAPONS.cig.exhaleMul;
      W.tick = 0;
    }
    W.charge = 0;
  }
}

export function onSlipperBack() { W.slipperOut = false; if (W.cur === 'slipper') playAnim('catch_slipper', 'catch'); }

const evPos = new THREE.Vector3();
function animEvent(ev, g) {
  g.getWorldPosition(evPos); // viewmodel space
  const sys = G.skinFxVM;
  const R = (k) => (Math.random() - 0.5) * k;
  switch (ev) {
    case 'whoosh': sfx.swing(); break;
    case 'thwack': sfx.thwack(); break;
    case 'crunch': sfx.crunch(); break;
    case 'crumbs': for (let i = 0; i < 14; i++) sys.norm.spawn(evPos.x + R(0.08), evPos.y + R(0.05), evPos.z + R(0.08), R(0.6), 0.2 + Math.random() * 0.5, R(0.6), 0.7, 0.025, 0.02, 0xd9a35b, 0x8a5a2b, 1, 2.5); break;
    case 'ting': sfx.ting(); for (let i = 0; i < 6; i++) sys.add.spawn(evPos.x + R(0.05), evPos.y + R(0.05), evPos.z + R(0.05), R(0.2), R(0.2), R(0.2), 0.4, 0.03, 0, 0xffffff, 0xaaccff); break;
    case 'squeak': sfx.squeak(); break;
    case 'squawk': sfx.squawk(); break;
    case 'click': sfx.click(); break;
    case 'blow': sfx.blow(); for (let i = 0; i < 6; i++) sys.norm.spawn(evPos.x + R(0.04), evPos.y, evPos.z + R(0.04), R(0.15), 0.1, R(0.15), 0.6, 0.02, 0.06, 0xdddddd, 0xffffff, 0.4); break;
    case 'smoke': for (let i = 0; i < 12; i++) sys.norm.spawn(evPos.x - 0.05 + R(0.05), evPos.y + 0.02, evPos.z - 0.1 + R(0.05), R(0.3), 0.15 + Math.random() * 0.2, -0.3 - Math.random() * 0.3, 1.4, 0.03, 0.2, 0xcccccc, 0x777777, 0.55, -0.1, 0.8); break;
    case 'spark': for (let i = 0; i < 10; i++) sys.add.spawn(evPos.x + R(0.03), evPos.y, evPos.z + R(0.03), R(0.8), 0.3 + Math.random() * 0.6, R(0.8), 0.5, 0.025, 0.005, 0xffcc44, 0xff3300, 1, 3); break;
    case 'spin': W.inspectSpin = 1.5; sfx.reload(); break;
    case 'rev': sfx.rev(); break;
  }
}

export function updateWeapons(dt, now) {
  const id = W.cur, w = WEAPONS[id];
  const alive = ME.alive;
  let smoking = false, firing = false, blowing = false, spinning = false;

  W.fuel.blower = (W.held && id === 'blower') ? W.fuel.blower : Math.min(WEAPONS.blower.fuel, W.fuel.blower + WEAPONS.blower.regen * dt);
  W.bloom = Math.max(0, W.bloom - dt * 0.06);
  if (W.slipperOut && now - W.slipperT > 4000) W.slipperOut = false;
  if (W.reloadId && now >= W.reloadUntil) { W.ammo[W.reloadId] = WEAPONS[W.reloadId].mag; W.reloadId = null; sfx.click(); }
  const canAim = !!w.ads && alive && !W.reloadId;
  W.aim = canAim && W.aimHeld ? Math.min(1, W.aim + dt * 7) : Math.max(0, W.aim - dt * 8);
  W.zoom = w.ads ? 1 + (w.ads.zoom - 1) * W.aim : 1;
  W.scoped = !!(w.ads && w.ads.scope && W.aim > 0.92);
  hud.scope(W.scoped);
  ME.speedMul = (w.speedMul || 1) * (1 - W.aim * 0.25);

  if (alive && w.kind === 'hitscan') {
    if (w.spinup) {
      W.spin = W.held && !W.reloadId ? Math.min(1, W.spin + dt / w.spinup) : Math.max(0, W.spin - dt / (w.spinup * 1.5));
      spinning = W.spin > 0;
    }
    if (W.held && (w.auto || w.spinup) && !W.reloadId && (!w.spinup || W.spin >= 1)) {
      for (let i = 0; i < 4 && ready(id, now); i++) {
        if (W.ammo[id] <= 0) { reload(); break; }
        fireHitscan(id, now);
      }
    }
  } else if (alive && id === 'banana') {
    if (W.held && ready(id, now)) fireProj(id, now);
  } else if (alive && id === 'cig') {
    if (W.held && W.exhale <= 0 && !W.coughLock) {
      W.charge += dt;
      smoking = true;
      if (Math.random() < dt * 30) fx.smoke(muzzleWorld(), 1, 0.02);
      if (W.charge > w.coughAt) cough();
    }
    if (W.exhale > 0) {
      W.exhale -= dt;
      firing = true;
      const o = eye(), d = look();
      fx.fireCone([o[0] + d[0] * 0.4, o[1] - 0.12 + d[1] * 0.4, o[2] + d[2] * 0.4], d, ME.vel, 7);
      W.tick -= dt;
      if (W.tick <= 0) {
        W.tick = w.tick;
        for (const tg of conePlayers(o, d, w.range, w.cone)) net.send({ t: 'hit', to: tg.r.id, w: 'cig', d: tg.dir.map(r2) });
      }
      ME.vel[0] -= d[0] * w.jet * dt; ME.vel[1] -= d[1] * w.jet * dt; ME.vel[2] -= d[2] * w.jet * dt;
    }
  } else if (alive && id === 'blower') {
    if (W.held && W.fuel.blower > 0) {
      W.fuel.blower -= dt;
      blowing = true;
      const o = eye(), d = look();
      ME.vel[0] -= d[0] * w.self * dt; ME.vel[1] -= d[1] * w.self * dt; ME.vel[2] -= d[2] * w.self * dt;
      if (d[1] < -0.3 && ME.onGround) { ME.onGround = false; ME.pos[1] += 0.02; }
      fx.leaves(muzzleWorld(), d, ME.vel);
      W.tick -= dt;
      if (W.tick <= 0) {
        W.tick = w.tick;
        for (const tg of conePlayers(o, d, w.range, w.cone)) net.send({ t: 'push', to: tg.r.id, w: 'blower' });
      }
    }
  }

  if (id === 'bow') {
    if (alive && W.held && ready('bow', now)) { const was = W.draw; W.draw = Math.min(1, W.draw + dt / w.draw); if (was < 1 && W.draw >= 1) sfx.click(); }
    const tip = ARROW_TIPS[G.tip] ? G.tip : 'regular';
    const mg = models.bow && models.bow.g;
    if (mg) {
      mg.userData.arrow.position.z = W.draw * 0.16;
      mg.userData.string.position.z = W.draw * 0.16;
      mg.userData.arrowTip.material = M(tipColor(tip), true);
    }
    hud.meter(W.draw, `${ARROW_TIPS[tip].name.toUpperCase()} ARROW${W.draw >= 1 ? ' · FULL DRAW' : ''}`, ARROW_TIPS[tip].color);
  }
  if (id === 'cards') {
    const hand = G.hand || [];
    if (W.cardSel >= hand.length) W.cardSel = Math.max(0, hand.length - 1);
    const fan = models.cards && models.cards.g.userData.fan;
    if (fan) fan.forEach((c, i) => {
      c.visible = i < hand.length;
      if (i < hand.length) c.material = cardFace(hand[i]);
      const a = (i - (hand.length - 1) / 2) * 0.22;
      const up = i === W.cardSel ? 0.035 : 0;
      c.position.set(Math.sin(a) * 0.09, Math.cos(a) * 0.09 - 0.07 + up, -0.002 * i + (i === W.cardSel ? 0.01 : 0));
      c.rotation.z = -a;
    });
    hud.cards(hand, W.cardSel);
  } else hud.cards(null);
  if (W.pendingSwing > 0) { W.pendingSwing -= dt; if (W.pendingSwing <= 0 && alive) resolveSwing(W.swingId); }
  if (W.pendingThrow > 0) { W.pendingThrow -= dt; if (W.pendingThrow <= 0 && alive && id === 'slipper') fireProj('slipper', now, true); }
  if (W.aimHeld) cancelInspect();
  // glitch dash: hold V with the scythe out. you turn into pixels and rush where you look, hitting everyone you pass
  const D = WEAPONS.dash;
  const dashing = alive && W.hasScythe && isScythe(id) && W.dashHeld && W.dashFuel > 0;
  if (dashing && !ME.dashing) { sfx.reverse(); cancelInspect(); }
  if (!dashing && ME.dashing) sfx.whoops();
  ME.dashing = dashing;
  if (dashing) {
    W.dashFuel = Math.max(0, W.dashFuel - dt);
    for (const r of G.remotes.values()) {
      if (!r.alive) continue;
      if (Math.hypot(r.pos[0] - ME.pos[0], r.pos[1] - ME.pos[1], r.pos[2] - ME.pos[2]) > 2.6) continue;
      if (now - (W.dashHitT.get(r.id) || 0) < 300) continue;
      W.dashHitT.set(r.id, now);
      net.send({ t: 'hit', to: r.id, w: 'dash', d: look().map(r2) });
      sfx.thwack();
    }
  } else W.dashFuel = Math.min(D.max, W.dashFuel + D.regen * dt);

  loopSfx('inhale', smoking);
  loopSfx('fire', firing);
  loopSfx('blower', blowing);
  loopSfx('spin', spinning && W.held);
  const reversed = now < W.reverseUntil;
  W.flags = (smoking ? FLAGS.SMOKE : 0) | (firing ? FLAGS.FIRE : 0) | (blowing ? FLAGS.BLOW : 0) | (spinning ? FLAGS.SPIN : 0) | (reversed ? FLAGS.REVERSE : 0) | (ME.dashing ? FLAGS.DASH : 0);

  // ---- HUD
  if (w.mag) hud.ammo(W.ammo[id], w.mag, !!W.reloadId);
  else hud.ammo(null);
  if (W.reloadId) hud.meter(1 - (W.reloadUntil - now) / (w.reload * 1000), 'RELOADING', '#ffffff');
  else if (isScythe(id)) hud.meter(W.dashFuel / D.max, ME.dashing ? 'GLITCHING' : 'V: GLITCH DASH · X: SWAP MODE', '#ff00dc');
  else if (id === 'bow') { /* set above */ }
  else if (id === 'cards') hud.meter(null);
  else if (id === 'cig') {
    if (W.exhale <= 0 && W.charge <= 0) hud.meter(null);
    else hud.meter(W.exhale > 0 ? W.exhale / (w.maxCharge * w.exhaleMul) : W.charge / w.maxCharge,
      W.exhale > 0 ? 'EXHALING' : W.charge > w.maxCharge ? 'TOO MUCH' : 'INHALE', W.charge > w.maxCharge ? '#ff3030' : '#ff9a3a');
  } else if (id === 'blower') hud.meter(W.fuel.blower / w.fuel, 'FUEL', '#ff9a3a');
  else if (w.spinup && W.spin > 0 && W.spin < 1) hud.meter(W.spin, 'SPINNING UP', '#c8c8c8');
  else if (id === 'slipper' && W.slipperOut) hud.meter(null);
  else if (w.cd && w.cd >= 1 && !ready(id, now)) hud.meter(1 - ((W.cd[id] - now) / 1000) / w.cd, 'COOLDOWN', w.color);
  else hud.meter(null);

  // ---- viewmodel animation
  const m = models[id];
  const cfg = m.cfg;
  const hs = hspeed();
  if (ME.onGround) W.bob += dt * Math.min(hs, 12) * 1.1;
  const bobA = ME.onGround ? Math.min(1, hs / 10) * 0.018 : 0;
  W.kick = Math.max(0, W.kick - dt * 6);
  W.swap = Math.max(0, W.swap - dt * 5);
  W.swing = Math.max(0, W.swing - dt * 3.5);
  let px = cfg.p[0] + Math.sin(W.bob) * bobA, py = cfg.p[1] + Math.abs(Math.cos(W.bob)) * bobA - W.swap * 0.3, pz = cfg.p[2] + W.kick * 0.08;
  let rx = cfg.r[0] + W.kick * 0.25, ry = cfg.r[1], rz = cfg.r[2];
  if (w.ads && W.aim > 0) {
    const a = W.aim * W.aim * (3 - 2 * W.aim);
    px += (w.ads.p[0] - px) * a; py += (w.ads.p[1] - py) * a; pz += (w.ads.p[2] - pz) * a;
    rx += (0 - rx) * a; ry += (0 - ry) * a; rz += (0 - rz) * a;
  }
  if (W.reloadId) { const k = Math.sin(Math.min(1, 1 - (W.reloadUntil - now) / (w.reload * 1000)) * Math.PI); py -= k * 0.12; rx -= k * 0.6; rz += k * 0.4; }
  if (id === 'cig') {
    const k = smoking ? 1 : 0;
    m.wrap.userData.k = (m.wrap.userData.k || 0) + (k - (m.wrap.userData.k || 0)) * Math.min(1, dt * 10);
    const kk = m.wrap.userData.k;
    px += (0.02 - px) * kk; py += (-0.13 - py) * kk; pz += (-0.2 - pz) * kk;
    ry += (1.45 - ry) * kk;
    if (firing) py -= 0.15;
    const tip = m.g.userData.tip;
    if (tip) tip.scale.setScalar(1 + W.charge * 0.6 + Math.random() * 0.2 * (smoking ? 1 : 0));
  }
  // keyframed animation on top of everything (swings, throws, inspects)
  let scale = 1;
  if (W.anim) {
    const t0 = W.anim.t;
    W.anim.t += dt;
    for (const ev of eventsBetween(W.anim.name, t0, W.anim.t)) animEvent(ev, m.g);
    const a = sample(W.anim.name, W.anim.t);
    if (!a) W.anim = null;
    else { px += a.p[0]; py += a.p[1]; pz += a.p[2]; rx += a.r[0]; ry += a.r[1]; rz += a.r[2]; scale = a.s; }
  }
  if (W.inspectSpin > 0) { W.inspectSpin = Math.max(0, W.inspectSpin - dt * 0.8); if (m.g.userData.barrels) m.g.userData.barrels.rotation.z += W.inspectSpin * dt * 30; }
  m.wrap.scale.setScalar(scale);
  if (id === 'reverse' && reversed) { ry += Math.sin(now * 0.03) * 0.8; py += 0.05; }
  if (m.g.userData.barrels) m.g.userData.barrels.rotation.z += W.spin * dt * 40;
  if (blowing || (spinning && W.spin >= 1 && W.held)) { px += (Math.random() - 0.5) * 0.008; py += (Math.random() - 0.5) * 0.008; }
  m.wrap.visible = !(id === 'slipper' && W.slipperOut) && !W.scoped && !ME.dashing;
  m.wrap.position.set(px, py, pz);
  m.wrap.rotation.set(rx, ry, rz);
  if (m.wrap.visible && G.skinFxVM) { m.wrap.updateMatrixWorld(true); emitSkinFx(G.skinFxVM, m.g, dt, 0.3 * cfg.s); }
}
