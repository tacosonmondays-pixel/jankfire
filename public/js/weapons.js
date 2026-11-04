// Local weapon logic, loadouts, ammo + first-person viewmodels.
import * as THREE from 'three';
import { WEAPONS, ORDER, SLOTS, FLAGS, HIPFIRE, ARROW_TIPS, SUITS, RANKS, validLoadout, DEFAULT_LOADOUT, ITEMS, fireRate } from '/shared/weapons.js';
import { BOXES } from '/shared/map.js';
import { raycast, rayBox } from '/shared/physics.js';
import { G } from './ctx.js';
import { ME, eye, look, applyKb, hspeed } from './player.js';
import { buildWeapon, M, cardFace, tipColor, setKatana, freeTree } from './models.js';
import { fx } from './fx.js';
import { marbles } from './marbles.js';
import { sfx, loopSfx, stopLoops } from './audio.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { tracerColor, emitSkinFx } from './skins.js';
import { ANIMS, sample, sampleCh, eventsBetween, inspectFor, drawFor } from './anim.js';
import { weaponIcon, clearIcons, itemIcon } from './icons.js';

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
  hitStop: 0, heavy: false, cycle: null, flashT: 0, playing: null, hideCard: null, hideUntil: 0, handKey: '',
  lastYaw: 0, lastPitch: 0, swayX: 0, swayY: 0, runK: 0, wasGround: true, lastVy: 0,
};

// ------------------------------------------------------------ oomph: springs, recoil, punch
// Recoil and bumps are springs, not straight lines: the gun snaps back, overshoots a hair and settles.
// The camera gets its own "view punch" spring (visual only, your aim doesn't move).
const rec = { p: [0, 0, 0], pv: [0, 0, 0], r: [0, 0, 0], rv: [0, 0, 0] };
const punch = { x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0 };
G.punch = punch;
const RECOIL = {
  ar: { back: 0.9, up: 3, roll: 1.5, side: 0.15, punch: 0.012 },
  smg: { back: 0.6, up: 2.2, roll: 1.4, side: 0.2, punch: 0.008 },
  shotgun: { back: 2.4, up: 9, roll: 3, side: 0.3, punch: 0.05 },
  marbles: { back: 2.0, up: 8, roll: 2.6, side: 0.35, punch: 0.04 },
  redline: { back: 0.7, up: 2.4, roll: 1.6, side: 0.2, punch: 0.008 },
  minigun: { back: 0.35, up: 0.9, roll: 1.2, side: 0.25, punch: 0.004 },
  sniper: { back: 3, up: 11, roll: 2, side: 0.2, punch: 0.075 },
  revolver: { back: 1.6, up: 13, roll: 2.5, side: 0.2, punch: 0.045 },
  scythe_rifle: { back: 2.6, up: 9, roll: 2, side: 0.2, punch: 0.06 },
  chicken: { back: 2.8, up: 6, roll: 1.5, side: 0.3, punch: 0.045 },
  bowling: { back: 3.2, up: 5, roll: 2, side: 0.3, punch: 0.05 },
  banana: { back: 1.2, up: 3.5, roll: 2, side: 0.3, punch: 0.015 },
  duck: { back: 1.2, up: 4, roll: 3, side: 0.3, punch: 0.015 },
  bow: { back: -1.4, up: 2.5, roll: 1, side: 0.1, punch: 0.012 },
};
const rnd = () => (Math.random() < 0.5 ? -1 : 1) * (0.5 + Math.random() * 0.5);
function kickVM(id, mul = 1) {
  const k = RECOIL[id] || { back: 0.8, up: 2.5, roll: 1, side: 0.2, punch: 0.01 };
  rec.pv[2] += k.back * mul; rec.rv[0] += k.up * mul; rec.rv[2] += k.roll * rnd() * mul; rec.pv[0] += k.side * rnd() * mul;
  punchCam(k.punch * mul, k.punch * 0.35 * rnd() * mul, k.punch * 0.5 * rnd() * mul);
}
export function punchCam(pitch, yaw = 0, roll = 0) { punch.vx += pitch * 21; punch.vy += yaw * 21; punch.vz += roll * 21; }
function stepSprings(dt) {
  const n = Math.min(40, Math.max(1, Math.ceil(dt * 240))), h = dt / n;
  for (let s = 0; s < n; s++) {
    for (let i = 0; i < 3; i++) {
      rec.pv[i] += (-220 * rec.p[i] - 20 * rec.pv[i]) * h; rec.p[i] += rec.pv[i] * h;
      rec.rv[i] += (-200 * rec.r[i] - 18 * rec.rv[i]) * h; rec.r[i] += rec.rv[i] * h;
    }
    punch.vx += (-160 * punch.x - 18 * punch.vx) * h; punch.x += punch.vx * h;
    punch.vy += (-160 * punch.y - 18 * punch.vy) * h; punch.y += punch.vy * h;
    punch.vz += (-160 * punch.z - 18 * punch.vz) * h; punch.z += punch.vz * h;
  }
}

// muzzle flash: a crunchy star + two side spikes, shown for a couple of frames
let flashTexture = null;
function flashTex() {
  if (flashTexture) return flashTexture;
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(16, 16, 0, 16, 16, 16);
  g.addColorStop(0, '#ffffff'); g.addColorStop(0.25, '#fff2a0'); g.addColorStop(0.6, '#ff9a1a'); g.addColorStop(1, 'rgba(255,80,0,0)');
  x.fillStyle = g;
  x.beginPath();
  for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2, r = i % 2 ? 6 : 16; x.lineTo(16 + Math.cos(a) * r, 16 + Math.sin(a) * r); }
  x.fill();
  flashTexture = new THREE.CanvasTexture(c);
  flashTexture.magFilter = THREE.NearestFilter; flashTexture.minFilter = THREE.NearestFilter;
  return flashTexture;
}
const FLASH_IDS = new Set(['ar', 'smg', 'redline', 'marbles', 'shotgun', 'minigun', 'sniper', 'revolver', 'scythe_rifle', 'chicken', 'bowling', 'banana']);
function makeFlash(big) {
  const grp = new THREE.Group();
  const mat = new THREE.MeshBasicMaterial({ map: flashTex(), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false });
  const s = big ? 1.6 : 1;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(0.24 * s, 0.24 * s), mat);
  const side1 = new THREE.Mesh(new THREE.PlaneGeometry(0.4 * s, 0.14 * s), mat);
  side1.rotation.y = Math.PI / 2; side1.position.z = -0.12 * s;
  const side2 = new THREE.Mesh(new THREE.PlaneGeometry(0.4 * s, 0.14 * s), mat);
  side2.rotation.set(-Math.PI / 2, 0, Math.PI / 2); side2.position.z = -0.12 * s;
  grp.add(face, side1, side2);
  grp.userData.face = face;
  grp.visible = false;
  return grp;
}
// brass flying out of the ejection port (square particles in the viewmodel scene)
function ejectShell(g, color = 0xd9a53a, big = false) {
  if (!G.skinFxVM || !g.userData.muzzle) return;
  g.updateMatrixWorld(true);
  tmpV.set(0.03, 0.035, g.userData.muzzle.z * 0.35);
  g.localToWorld(tmpV);
  const sz = big ? 0.03 : 0.018;
  G.skinFxVM.norm.spawn(tmpV.x, tmpV.y, tmpV.z, 0.6 + Math.random() * 0.5, 0.75 + Math.random() * 0.5, 0.1 + Math.random() * 0.25,
    0.55, sz, sz * 0.9, color, color, 1, 4.5, 0.4);
}
const SHELL_ON_FIRE = new Set(['ar', 'smg', 'redline', 'minigun', 'scythe_rifle']);

// smear trail: a fading ribbon behind the tip of whatever you swing
const TRAIL_N = 26;
const TRAIL_COLOR = { knife: 0xbfe8ff, bread: 0xffd9a0, spoon: 0xffffff, slapper: 0xffb0d0, scythe: 0xff3ad8, slipper: 0xb0ffb0, cards: 0xffffff };
const trailPts = [];
let trail = null;
const tmpV2 = new THREE.Vector3(), tcol = new THREE.Color();
function initTrail() {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(TRAIL_N * 6), 3).setUsage(THREE.DynamicDrawUsage));
  geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(TRAIL_N * 6), 3).setUsage(THREE.DynamicDrawUsage));
  const idx = [];
  for (let i = 0; i < TRAIL_N - 1; i++) { const a = i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  geo.setIndex(idx);
  trail = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false }));
  trail.frustumCulled = false;
  trail.renderOrder = 5;
  G.vmScene.add(trail);
}
function updateTrail(now, m, active, color) {
  if (!trail) return;
  if (active && m) {
    m.wrap.updateMatrixWorld(true);
    const mz = m.g.userData.muzzle;
    tmpV.copy(mz); m.g.localToWorld(tmpV);
    tmpV2.copy(mz).multiplyScalar(0.45); m.g.localToWorld(tmpV2);
    trailPts.unshift({ t: now, a: [tmpV.x, tmpV.y, tmpV.z], b: [tmpV2.x, tmpV2.y, tmpV2.z] });
  }
  while (trailPts.length > TRAIL_N || (trailPts.length && now - trailPts[trailPts.length - 1].t > 120)) trailPts.pop();
  const n = trailPts.length;
  trail.visible = n >= 3;
  if (!trail.visible) return;
  const pos = trail.geometry.attributes.position.array, col = trail.geometry.attributes.color.array;
  tcol.setHex(color);
  for (let i = 0; i < n; i++) {
    const q = trailPts[i], k = Math.max(0, 1 - (now - q.t) / 120) * (1 - i / n) * 0.9;
    pos.set(q.a, i * 6); pos.set(q.b, i * 6 + 3);
    col[i * 6] = tcol.r * k; col[i * 6 + 1] = tcol.g * k; col[i * 6 + 2] = tcol.b * k;
    col[i * 6 + 3] = tcol.r * k * 0.15; col[i * 6 + 4] = tcol.g * k * 0.15; col[i * 6 + 5] = tcol.b * k * 0.15;
  }
  trail.geometry.setDrawRange(0, (n - 1) * 6);
  trail.geometry.attributes.position.needsUpdate = true;
  trail.geometry.attributes.color.needsUpdate = true;
}

// cards you flick fly off the fan, spinning flat like a real thrown card
const flying = [];
const CARD_GEO = new THREE.PlaneGeometry(0.08, 0.12);
function throwCards(m) {
  const pl = W.playing;
  if (!pl || !m) return;
  const fan = m.g.userData.fan;
  const src = fan && fan[Math.min(pl.sel, fan.length - 1)];
  m.wrap.updateMatrixWorld(true);
  if (src) src.getWorldPosition(tmpV); else m.g.getWorldPosition(tmpV);
  const n = pl.n;
  for (let i = 0; i < n; i++) {
    const mesh = new THREE.Mesh(CARD_GEO, cardFace(pl.card));
    mesh.material.side = THREE.DoubleSide;
    mesh.position.copy(tmpV);
    mesh.rotation.set(-1.25, 0, 0);
    mesh.visible = false;
    G.vmScene.add(mesh);
    const spread = n > 1 ? (i / (n - 1) - 0.5) * (pl.ult ? 2.4 : 1.2) : 0;
    flying.push({ mesh, delay: i * 0.035, life: 0.42, v: [spread * 1.2 - 0.2, 0.5 + Math.random() * 0.2, -3.6 - Math.random() * 1.2], spin: 28 + Math.random() * 10 });
  }
  W.hideCard = pl.card; W.hideUntil = performance.now() + 1200;
}
function updateFlying(dt) {
  for (let i = flying.length - 1; i >= 0; i--) {
    const f = flying[i];
    if (f.delay > 0) { f.delay -= dt; continue; }
    f.mesh.visible = true;
    f.life -= dt;
    if (f.life <= 0) { G.vmScene.remove(f.mesh); flying.splice(i, 1); continue; }
    f.mesh.position.x += f.v[0] * dt; f.mesh.position.y += f.v[1] * dt; f.mesh.position.z += f.v[2] * dt;
    f.v[1] -= 1.5 * dt;
    f.mesh.rotateZ(f.spin * dt);
  }
}

// ------------------------------------------------------------ card deck
export function cycleCard() { const n = (G.hand || []).length; if (n) { W.cardSel = (W.cardSel + 1) % n; sfx.click(); } }
export function redrawCards() { net.send({ t: 'redraw' }); sfx.swing(); }
function playCard(now) {
  const hand = G.hand || [];
  if (!hand.length) return;
  setCd('cards', now);
  const i = Math.min(W.cardSel, hand.length - 1);
  net.send({ t: 'fire', w: 'cards', i, o: eye().map(r2), d: look().map(r2) });
  const card = hand[i], suit = card[0], rank = Number(card.slice(1));
  const ult = suit === 'j' || rank >= 11;
  W.playing = { card, suit, rank, ult, sel: i, n: suit === 's' ? (ult ? 8 : Math.max(1, Math.min(6, rank))) : 1 };
  cancelInspect();
  playAnim(suit === 'h' || rank === 1 ? 'raise_card' : ult ? 'throw_card_ult' : 'throw_card', 'throw');
}
const isScythe = (id) => id === 'scythe' || id === 'scythe_rifle';

// where the gun sits at full ADS (viewmodel space: camera at the origin looking down -z)
const EYE_RELIEF = 0.17; // how far in front of your eye the rear sight sits
const adsCache = new Map();
function adsPose(id, m) {
  const g = m.g, s = m.cfg.s;
  const key = id + ':' + g.uuid;
  if (adsCache.has(key)) return adsCache.get(key);
  let pose;
  const sg = g.userData.sight;
  if (sg) pose = [0, -sg.y * s, -EYE_RELIEF - sg.z * s]; // sight line exactly through the middle
  else {
    // no sights: keep the whole thing under (and a bit right of) the middle of the screen.
    // measured in the gun's own space (no wrap, viewmodel root or scale), so * s below is the only scaling
    g.updateMatrixWorld(true);
    const inv = g.matrixWorld.clone().invert(), rel = new THREE.Matrix4(), box = new THREE.Box3();
    const underHat = (o) => { for (; o && o !== g; o = o.parent) if (o.userData.isHat) return true; return false; }; // hidden while aiming
    g.traverse((o) => { if (o.isMesh && !underHat(o)) { o.geometry.computeBoundingBox(); box.union(o.geometry.boundingBox.clone().applyMatrix4(rel.multiplyMatrices(inv, o.matrixWorld))); } });
    const w = WEAPONS[id];
    if (id === 'bow') pose = [-0.07, -0.03 - g.userData.muzzle.y * s, w.ads.p[2], 0.42]; // canted, riser left of the arrow
    else pose = [Math.max(w.ads.p[0], 0.06), Math.min(w.ads.p[1], -0.03 - box.max.y * s), w.ads.p[2]];
  }
  adsCache.set(key, pose);
  return pose;
}

// katana: longer blade + more reach per kill (the server says how long)
export function setMyKatana(n) { W.kat = n; if (models.katana) { setKatana(models.katana.g, n); adsCache.clear(); } }

// ------------------------------------------------------------ items (G)
W.item = DEFAULT_LOADOUT.item;
W.ic = {}; // id -> { n, next (performance.now ms) }
export function setItem(id) { if (ITEMS[id]) W.item = id; }
export function resetItems() { W.ic = {}; }
function charges(id) {
  const it = ITEMS[id];
  let c = W.ic[id];
  if (!c) c = W.ic[id] = { n: it.charges, next: 0 };
  const n = performance.now();
  while (c.n < it.charges && c.next && n >= c.next) { c.n++; c.next = c.n < it.charges ? c.next + it.recharge * 1000 : 0; }
  return c;
}
export function syncItem(id, n, nextMs) { if (!ITEMS[id]) return; W.ic[id] = { n, next: nextMs ? performance.now() + nextMs : 0 }; }
export function useItem() {
  const id = W.item, it = ITEMS[id];
  if (!it || !ME.alive || (W.eco && W.eco.dry('item'))) return;
  const c = charges(id);
  if (performance.now() - (W.itemT || 0) < 420) return; // same spam limit as the server
  if (c.n <= 0) { sfx.empty(); hud.msg(`${it.name}: recharging`, 0.8); return; }
  W.itemT = performance.now();
  c.n--; if (!c.next && !W.eco) c.next = performance.now() + it.recharge * 1000;
  net.send({ t: 'item', i: id, o: eye().map(r2), d: look().map(r2) });
  if (!W.anim || W.anim.kind === 'inspect' || W.anim.kind === 'draw') playAnim('toss_item', 'item');
  if (id === 'medkit') sfx.heal(); else if (id === 'bubble') sfx.reverse(); else sfx.swing();
}

// knife right click: CS-style heavy stab. returns false when this weapon has no heavy attack
export function heavyAttack() {
  const id = W.cur, w = WEAPONS[id], now = performance.now();
  if (!w || !w.heavy || !ANIMS['stab_' + id]) return false;
  const model = models[id] && models[id].g.userData.model;
  const stab = model && ANIMS['stab_' + model] ? 'stab_' + model : 'stab_' + id;
  if (!ME.alive || !ready(id, now) || now < (W.cd[id + 'H'] || 0)) return true;
  cancelInspect();
  W.cd[id] = now + w.heavy.cd * 1000; // no slashing in the middle of a stab
  W.cd[id + 'H'] = now + w.heavy.cd * 1000;
  W.swingId = id; W.swing = 1; W.heavy = true;
  net.send({ t: 'fire', w: id, o: eye().map(r2), d: look().map(r2), heavy: 1 });
  playAnim(stab, 'swing');
  W.pendingSwing = ANIMS[stab].hit;
  return true;
}

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
  redline: { p: [0.2, -0.2, -0.37], r: [0, 0.04, 0], s: 0.72 },
  marbles: { p: [0.18, -0.19, -0.34], r: [0, 0.05, 0], s: 0.8 },
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
  snowball: { p: [0.17, -0.19, -0.33], r: [0.2, 0.2, 0.1], s: 0.75 },
  spoon: { p: [0.15, -0.15, -0.3], r: [0.2, 0.25, 0.1], s: 1.3 },
  knife: { p: [0.16, -0.17, -0.3], r: [0.15, 0.2, 0.15], s: 1.3 },
  katana: { p: [0.2, -0.22, -0.34], r: [0.35, 0.25, -0.15], s: 0.85 },
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
  adsCache.clear();
  clearIcons();
  for (const id of ORDER) {
    if (!VM[id]) continue;
    if (models[id]) { vmRoot.remove(models[id].wrap); freeTree(models[id].wrap); if (models[id].flash) models[id].flash.userData.face.material.dispose(); }
    const wrap = new THREE.Group();
    const g = buildWeapon(id, (W.skinOver || G.equipped || {})[id]);
    const cfg = VM[id];
    g.scale.setScalar(cfg.s);
    wrap.add(g);
    const hand = new THREE.Mesh(new THREE.BoxGeometry(0.052, 0.062, 0.09), M(0xf1c27d)); // a fist, not a brick
    hand.position.set(0.004, -0.042, 0.03);
    wrap.add(hand);
    wrap.position.set(...cfg.p);
    wrap.rotation.set(...cfg.r);
    wrap.visible = id === W.cur;
    vmRoot.add(wrap);
    let flash = null;
    if (FLASH_IDS.has(id) && g.userData.muzzle) { flash = makeFlash(id === 'shotgun' || id === 'sniper'); flash.position.copy(g.userData.muzzle); g.add(flash); }
    models[id] = { wrap, g, cfg, flash };
  }
  if (models.katana) setKatana(models.katana.g, W.kat || 0);
  if (!trail) initTrail();
}

// ------------------------------------------------------------ killstreak scythe (4th slot)
export function grantScythe() {
  W.hasScythe = true;
  W.slots[3] = 'scythe';
  W.dashFuel = WEAPONS.dash.max;
  W.ammo.scythe_rifle = WEAPONS.scythe_rifle.mag;
  showSlots();
  equip(3);
}
export function loseScythe() {
  if (!W.hasScythe) return;
  W.hasScythe = false;
  W.slots.length = 3;
  ME.dashing = false;
  showSlots();
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
  for (const id of ORDER) if (WEAPONS[id].mag && !W.eco) W.ammo[id] = WEAPONS[id].mag;
  W.reloadId = null;
  W.fuel.blower = WEAPONS.blower.fuel;
  W.slipperOut = false;
}

export function setLoadout(lo) {
  const v = validLoadout(lo);
  W.item = v.item;
  const streakSlot = W.hasScythe ? (W.slots[3] || 'scythe') : null;
  W.slots = SLOTS.map((s) => v[s]);
  if (streakSlot) W.slots[3] = streakSlot;
  if (W.slot >= W.slots.length) W.slot = 0;
  showSlots();
  W.cur = null;
  equip(W.slot);
}

export function rebuildOne(id) {
  rebuildViewmodels();
  for (const k of ORDER) if (models[k]) models[k].wrap.visible = k === W.cur;
  showSlots();
}
// hotbar: a picture of each weapon you're carrying, with your skin on it
export function showSlots() {
  hud.slots(W.slots, W.slots.map((id) => (id ? weaponIcon(id, (W.skinOver || G.equipped || {})[id]) : '')));
  hud.slotOn(W.slot);
  hud.itemSlot(W.item, itemIcon(W.item));
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
  W.swap = 0.2;
  W.heavy = false; W.cycle = null; W.hitStop = 0;
  trailPts.length = 0;
  playAnim(drawFor(id, models[id] && models[id].g.userData.model), 'draw');
  for (const k of ORDER) if (models[k]) models[k].wrap.visible = k === id;
  hud.weapon(id, i);
  sfx.click();
}

// Plant & Defuse (econ.js): the server's inventory fills the slots (null = an empty box). i = the slot to hold now
// (null keeps the one in hand), anim = how the new one comes in
export function setSlots(ids, i, anim) {
  W.slots = ids.slice();
  if (i != null && W.slots[i]) {
    if (i !== W.slot) W.prevSlot = W.slot;
    W.cur = null; equip(i);
    if (anim) playAnim(anim, 'draw');
  }
  showSlots();
}
export function playVM(name, kind) { playAnim(name, kind); }

export function switchSlot(i) {
  if (i < 0 || i >= W.slots.length || i === W.slot || !W.slots[i]) return;
  W.prevSlot = W.slot;
  equip(i);
}
export function lastSlot() { switchSlot(W.prevSlot); }
export function cycleSlot(dir) { const n = W.slots.length; let i = (W.slot + dir + n) % n; while (!W.slots[i] && i !== W.slot) i = (i + dir + n) % n; switchSlot(i); }

export function reload() {
  cancelInspect();
  if (W.cur === 'cards') { redrawCards(); return; }
  const id = W.cur, w = WEAPONS[id];
  if (!w.mag || W.reloadId || W.ammo[id] >= w.mag || !ME.alive) return;
  if (W.eco && !W.eco.canReload(id)) return;
  W.reloadId = id;
  W.reloadUntil = performance.now() + w.reload * 1000;
  sfx.reload();
  if (W.eco) W.eco.reloading(id);
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
function interval(id) { const w = WEAPONS[id]; return w.rate ? 1 / fireRate(w, ME.hp) : w.cd; }
// Redline: 0 at full HP .. 1 at death's door (drives the needle, the vents and the pitch)
const redlineK = () => { const w = WEAPONS.redline; return (fireRate(w, ME.hp) - w.rate) / (w.rateMax - w.rate); };
const marblePalette = (skin) => (skin && skin[3] === 'marbles_gumball' ? 'gumball' : 'glass');
function setCd(id, now) {
  const iv = interval(id) * 1000;
  W.cd[id] = Math.max(W.cd[id] || 0, now - Math.min(40, iv * 0.5)) + iv; // keeps auto fire rate steady at low fps
}

// teammates are see-through for your bullets and swings
export const isFriend = (r) => !!(G.myTeam && r.team && r.team === G.myTeam);
function rayPlayers(o, d, maxT) {
  let best = null;
  for (const r of G.remotes.values()) {
    if (!r.alive || isFriend(r)) continue;
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
    if (!r.alive || isFriend(r)) continue;
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
  W.lastShotT = now;
  const o = eye(), base = look(), mz = muzzleWorld();
  const hits = new Map();
  const segs = [];
  const pellets = w.pellets || 1;
  const shots = w.marbles ? [] : null; // Marble Shotgun: each pellet becomes a marble that bounces off what it hit
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
      if (shots) shots.push({ a: drawFrom, b: end, n: !ph && mh ? mh.normal : null, player: !!ph });
      if (ph) {
        const h = hits.get(ph.r.id) || { n: 0, h: 0, d };
        h.n++; if (ph.head) h.h++; h.d = d;
        hits.set(ph.r.id, h);
        break;
      }
      if (!mh) break;
      if (!shots || i % 10 === 0) fx.impact(end, mh.normal);
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
  const skin = (W.skinOver || G.equipped || {})[id];
  if (shots) marbles.shoot(shots, marblePalette(skin));
  else for (const s of segs) fx.tracer(s.slice(0, 3), s.slice(3), tracerColor(skin, w.tracer || 0xfff0a0), w.thick || (fast ? 0.03 : 0.045), fast ? 0.07 : 0.2);
  net.send({ t: 'fire', w: id, o: o.map(r2), s: segs.slice(0, 12).map((s) => s.map(r2)) });
  if (w.recoil) applyKb([-base[0] * w.recoil, -base[1] * w.recoil, -base[2] * w.recoil]);
  ME.pitch = Math.min(1.55, ME.pitch + (w.kick || 0) * (0.6 + Math.random() * 0.8) * (1 - W.aim * 0.5));
  ME.yaw += (Math.random() - 0.5) * (w.kick || 0) * 0.5;
  W.bloom = Math.min(w.maxBloom || 0, W.bloom + (w.bloom || 0));
  W.kick = Math.min(1, W.kick + (fast ? 0.25 : 1));
  if (W.anim && W.anim.kind === 'draw') W.anim = null;
  kickVM(id, W.aim > 0.5 ? 0.6 : 1);
  W.flashT = fast ? 0.035 : 0.05;
  if (SHELL_ON_FIRE.has(id) && models[id]) ejectShell(models[id].g);
  if (id === 'shotgun') W.cycle = { name: 'pump_shotgun', t: 0.22 };
  if (id === 'sniper' || id === 'scythe_rifle') W.cycle = { name: 'bolt_sniper', t: 0.32 };
  if (id === 'sniper' || id === 'shotgun') G.shake = Math.max(G.shake, 0.6);
  sfx.gun(id, null, id === 'redline' ? redlineK() : 0);
  if (w.mag && W.ammo[id] <= 0) reload();
}

function fireProj(id, now, fromAnim) {
  const w = WEAPONS[id];
  if (W.eco && W.eco.dry(id, true)) return;
  if (id === 'slipper') {
    if (W.slipperOut) return;
    if (!fromAnim) { setCd(id, now); playAnim('throw_slipper', 'throw'); W.pendingThrow = ANIMS.throw_slipper.hit; return; }
    W.slipperOut = true;
    W.slipperT = now;
  }
  if (!fromAnim) setCd(id, now);
  net.send({ t: 'fire', w: id, o: eye().map(r2), d: look().map(r2) });
  if (id === 'snowball') { playAnim('throw_snowball', 'throw'); sfx.swing(); W.kick = 0.2; return; }
  if (id === 'chicken') sfx.squawk();
  else if (id === 'duck') sfx.squeak();
  else if (id === 'bowling') sfx.thunk();
  else if (id === 'slipper') { /* the throw animation already whooshed */ }
  else sfx.pew();
  W.kick = id === 'chicken' || id === 'bowling' ? 0.8 : 0.35;
  if (id !== 'slipper') {
    if (W.anim && W.anim.kind === 'draw') W.anim = null;
    kickVM(id);
    if (FLASH_IDS.has(id)) W.flashT = 0.05;
  }
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
  W.heavy = false;
  W.combo = now - W.lastSwingT < 750 ? W.combo + 1 : 0;
  W.lastSwingT = now;
  const suffix = W.combo % 2 ? '2' : '';
  const model = models[id] && models[id].g.userData.model;
  const name = model && ANIMS[`swing_${model}${suffix}`] ? `swing_${model}${suffix}` : `swing_${id}${suffix}`;
  if (ANIMS[name]) { playAnim(name, 'swing'); W.pendingSwing = ANIMS[name].hit; }
  else { sfx.swing(); W.pendingSwing = w.delay || 0.05; }
}

function resolveSwing(id) {
  const w = WEAPONS[id];
  const hv = W.heavy && w.heavy ? w.heavy : null;
  W.heavy = false;
  const o = eye(), d = look();
  const reach = w.range + (id === 'katana' ? (W.kat || 0) * w.grow : 0);
  const targets = conePlayers(o, d, hv ? hv.range : reach, hv ? hv.cone : w.cone);
  if (targets.length) {
    for (const tg of targets) {
      net.send({ t: 'hit', to: tg.r.id, w: id, d: d.map(r2), heavy: hv ? 1 : undefined });
      const p = tg.r.pos;
      fx.blast([p[0], p[1] + 1.4, p[2]], hv ? 1.1 : 0.6, 0xffffff, 0xffe14d); // impact flash
    }
    if (id === 'spoon') sfx.ting(); else if (id !== 'popper') sfx.bonk();
    if (hv) sfx.crunch();
    // hit stop: the swing freezes for a few frames on contact so it feels like it connected
    W.hitStop = hv ? 0.11 : 0.06;
    punchCam(hv ? -0.05 : -0.025, 0.015 * rnd(), 0.03 * rnd());
    G.shake = Math.max(G.shake, hv ? 0.6 : 0.35);
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
  if (W.eco && W.eco.dry(id)) { W.held = false; return; }
  if (W.anim && W.anim.kind === 'draw') W.anim = null;
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
      sfx.bowShot(); W.kick = 0.5; kickVM('bow', 0.5 + W.draw);
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
    case 'whooshBig': sfx.swing(); sfx.blow(); break;
    case 'shing': sfx.ting(); break;
    case 'clunk': sfx.thunk(); break;
    case 'riffle': for (let i = 0; i < 4; i++) setTimeout(() => sfx.click(), i * 35); break;
    case 'shell': ejectShell(g); break;
    case 'shellRed': ejectShell(g, 0xc02020, true); break;
    case 'flick': throwCards(models.cards); sfx.swing(); punchCam(-0.006); break;
    case 'ultcharge': sfx.reverse(); for (let i = 0; i < 16; i++) sys.add.spawn(evPos.x + R(0.12), evPos.y + R(0.1), evPos.z + R(0.06), R(0.4), 0.2 + Math.random() * 0.4, R(0.3), 0.5, 0.025, 0, 0xffe14d, 0xff4fd8, 1, -0.5); break;
    case 'burst': {
      const pl = W.playing || {};
      const c = pl.suit === 'h' ? 0xff4f7a : pl.rank === 1 ? 0xff00dc : 0xffffff;
      for (let i = 0; i < 26; i++) sys.add.spawn(evPos.x + R(0.04), evPos.y + 0.04 + R(0.04), evPos.z + R(0.04), R(1.2), R(1.2) + 0.2, R(1.2), 0.45, 0.03, 0.005, c, 0xffffff, 1, 1);
      W.hideCard = pl.card; W.hideUntil = performance.now() + 1200;
      sfx.pop(); break;
    }
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
  if (W.reloadId && now >= W.reloadUntil) { if (W.eco) W.eco.reloaded(W.reloadId); else W.ammo[W.reloadId] = WEAPONS[W.reloadId].mag; W.reloadId = null; sfx.click(); }
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
    const key = hand.join(',');
    if (key !== W.handKey || now > W.hideUntil) { if (key !== W.handKey) W.handKey = key; if (now > W.hideUntil || W.hideCard) W.hideCard = W.hideCard && now <= W.hideUntil && key === W.handKey ? W.hideCard : null; }
    let hidOne = false;
    if (fan) fan.forEach((c, i) => {
      c.visible = i < hand.length;
      if (W.hideCard && !hidOne && hand[i] === W.hideCard && i === Math.min(W.playing ? W.playing.sel : -1, hand.length - 1)) { c.visible = false; hidOne = true; }
      if (i < hand.length) c.material = cardFace(hand[i]);
      const a = (i - (hand.length - 1) / 2) * 0.22;
      const up = i === W.cardSel ? 0.035 : 0;
      c.position.set(Math.sin(a) * 0.09, Math.cos(a) * 0.09 - 0.07 + up, -0.002 * i + (i === W.cardSel ? 0.01 : 0));
      c.rotation.z = -a;
    });
    hud.cards(hand, W.cardSel);
  } else hud.cards(null);
  if (W.pendingSwing > 0 && W.hitStop <= 0) { W.pendingSwing -= dt; if (W.pendingSwing <= 0 && alive) resolveSwing(W.swingId); }
  if (W.cycle) { W.cycle.t -= dt; if (W.cycle.t <= 0) { if (W.cycle.name && id === (W.cycle.name === 'pump_shotgun' ? 'shotgun' : id)) playAnim(W.cycle.name, 'cycle'); W.cycle = null; } }
  updateFlying(dt);
  if (W.pendingThrow > 0) { W.pendingThrow -= dt; if (W.pendingThrow <= 0 && alive && id === 'slipper') fireProj('slipper', now, true); }
  if (W.aimHeld) cancelInspect();
  // glitch dash: hold V with the scythe out. you turn into pixels and rush where you look, hitting everyone you pass
  const D = WEAPONS.dash;
  const stuck = now < (ME.frozenUntil || 0) || now < (ME.sleepUntil || 0); // frozen or asleep: no dashing (or dash hits)
  const dashing = alive && !stuck && W.hasScythe && isScythe(id) && W.dashHeld && W.dashFuel > 0;
  if (dashing && !ME.dashing) { sfx.reverse(); cancelInspect(); }
  if (!dashing && ME.dashing) sfx.whoops();
  ME.dashing = dashing;
  if (dashing) {
    W.dashFuel = Math.max(0, W.dashFuel - dt);
    for (const r of G.remotes.values()) {
      if (!r.alive || isFriend(r)) continue;
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
  if (ITEMS[W.item]) { const c = charges(W.item), it = ITEMS[W.item]; hud.item(c.n, it.charges, c.next ? 1 - Math.max(0, c.next - now) / (it.recharge * 1000) : 1); }
  if (W.eco) W.eco.hud(id, !!W.reloadId);
  else if (w.mag) hud.ammo(W.ammo[id], w.mag, !!W.reloadId);
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
  stepSprings(dt);
  // landing thump + jump lift
  if (ME.onGround && !W.wasGround) { const imp = Math.min(1.3, Math.abs(W.lastVy) / 14); rec.pv[1] -= imp * 0.9; rec.rv[0] -= imp * 2.2; punchCam(-imp * 0.012); }
  if (!ME.onGround && W.wasGround && ME.vel[1] > 2) rec.pv[1] += 0.35;
  W.wasGround = ME.onGround; W.lastVy = ME.vel[1];
  // the gun lags behind where you look, then catches up (weight)
  let dyaw = ME.yaw - W.lastYaw; while (dyaw > Math.PI) dyaw -= Math.PI * 2; while (dyaw < -Math.PI) dyaw += Math.PI * 2;
  const dp = ME.pitch - W.lastPitch;
  W.lastYaw = ME.yaw; W.lastPitch = ME.pitch;
  const cl = (v) => Math.max(-0.07, Math.min(0.07, v));
  const lagK = G.spinning || dt <= 0 ? 0 : 1;
  W.swayX += (cl(dyaw * 0.6) * lagK - W.swayX) * Math.min(1, dt * 9);
  W.swayY += (cl(dp * 0.6) * lagK - W.swayY) * Math.min(1, dt * 9);
  // run pose: tilt the gun when sprinting on the ground
  const running = ME.sprinting && ME.onGround && hs > 4 && W.aim < 0.1 && !W.anim;
  W.runK += ((running ? 1 : 0) - W.runK) * Math.min(1, dt * 8);
  const breathe = now * 0.001;
  // base pose (hip): bob, lag, breathing, run tilt
  let px = cfg.p[0] + Math.sin(W.bob) * bobA + W.swayX * 0.2 + Math.sin(breathe * 1.3) * 0.0025,
    py = cfg.p[1] + Math.abs(Math.cos(W.bob)) * bobA - W.swap * 0.3 - W.swayY * 0.12 + Math.sin(breathe * 2.1) * 0.0018 - W.runK * 0.03,
    pz = cfg.p[2];
  let rx = cfg.r[0] - W.swayY * 0.8 - W.runK * 0.25,
    ry = cfg.r[1] + W.swayX * 1.3 + W.runK * 0.35,
    rz = cfg.r[2] + Math.sin(breathe * 1.1) * 0.008 + W.swayX * 0.6 + W.runK * 0.2 + (ME.sliding ? 0.3 : 0);
  // aim down sights: line the sight up with the exact centre of the screen and let the gun hang below it.
  // guns without sights (launchers, minigun, bow) stay low and to the side so the middle is clear.
  if (w.ads && W.aim > 0) {
    const a = W.aim * W.aim * (3 - 2 * W.aim);
    const t = adsPose(id, m);
    px += (t[0] - px) * a; py += (t[1] - py) * a; pz += (t[2] - pz) * a;
    rx += (0 - rx) * a; ry += (0 - ry) * a; rz += ((t[3] || 0) - rz) * a;
  }
  // recoil + kick on top (smaller while aiming so the sights stay usable)
  const ra = 1 - W.aim * 0.6;
  px += rec.p[0] * ra; py += rec.p[1] * (1 - W.aim * 0.3); pz += (W.kick * 0.04 + rec.p[2]) * ra;
  rx += (W.kick * 0.12 + rec.r[0]) * ra; rz += rec.r[2] * ra;
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
  const adt = W.hitStop > 0 ? 0 : dt; // hit stop freezes the swing for a moment
  W.hitStop = Math.max(0, W.hitStop - dt);
  let trailOn = false;
  if (W.anim) {
    const t0 = W.anim.t;
    W.anim.t += adt;
    for (const ev of eventsBetween(W.anim.name, t0, W.anim.t)) animEvent(ev, m.g);
    const a = sample(W.anim.name, W.anim.t);
    const tw = ANIMS[W.anim.name] && ANIMS[W.anim.name].trail;
    if (tw && W.anim.t >= tw[0] && W.anim.t <= tw[1]) trailOn = true;
    if (!a) W.anim = null;
    else { px += a.p[0]; py += a.p[1]; pz += a.p[2]; rx += a.r[0]; ry += a.r[1]; rz += a.r[2]; scale = a.s; }
  }
  // moving parts: balisong handles, switchblade blade, karambit spinning round the ring
  const ud = m.g.userData, an = W.anim && W.anim.name, at = W.anim ? W.anim.t : 0;
  if (ud.needle) { // Redline tachometer: the needle climbs as your HP drops, and bangs off the limiter in the red
    const k = redlineK(), firingNow = W.held && now - (W.lastShotT || 0) < 200;
    const target = -2.3 + 4.6 * k + (k > 0.85 && firingNow ? Math.sin(now * 0.08) * 0.12 : 0);
    ud.needle.rotation.x += (target - ud.needle.rotation.x) * Math.min(1, dt * 12);
    if (ud.vents) ud.vents.color.setRGB(0.25 + 0.75 * k, 0.04 + 0.3 * k * k, 0.02 + (firingNow ? 0.15 * k : 0));
  }
  if (ud.handles) { const h = an && sampleCh(an, 'handles', at); ud.handles[0].rotation.x = h ? h[0] : 0; ud.handles[1].rotation.x = h ? h[1] : 0; }
  if (ud.flipBlade) { const b = an && sampleCh(an, 'blade', at); ud.flipBlade.rotation.x = b ? b[0] : 0; }
  if (ud.pivot) {
    const sp = an && sampleCh(an, 'spin', at), a = sp ? sp[0] : 0, pz = ud.pivot.z * cfg.s;
    m.g.rotation.x = a;
    m.g.position.set(0, Math.sin(a) * pz, pz - Math.cos(a) * pz);
  }
  if (W.inspectSpin > 0) { W.inspectSpin = Math.max(0, W.inspectSpin - dt * 0.8); if (m.g.userData.barrels) m.g.userData.barrels.rotation.z += W.inspectSpin * dt * 30; }
  m.wrap.scale.setScalar(scale);
  if (id === 'reverse' && reversed) { ry += Math.sin(now * 0.03) * 0.8; py += 0.05; }
  if (m.g.userData.barrels) m.g.userData.barrels.rotation.z += W.spin * dt * 40;
  if (blowing || (spinning && W.spin >= 1 && W.held)) { px += (Math.random() - 0.5) * 0.008; py += (Math.random() - 0.5) * 0.008; }
  m.wrap.visible = !(id === 'slipper' && W.slipperOut) && !W.scoped && !ME.dashing;
  m.wrap.position.set(px, py, pz);
  m.wrap.rotation.set(rx, ry, rz);
  if (m.g.userData.hat) m.g.userData.hat.visible = W.aim < 0.3;
  hud.crossFade(m.g.userData.sight ? Math.max(0, 1 - W.aim * 1.6) : 1);
  // muzzle flash
  W.flashT = Math.max(0, W.flashT - dt);
  for (const k of ORDER) { const mm = models[k]; if (mm && mm.flash) mm.flash.visible = k === id && W.flashT > 0 && m.wrap.visible; }
  if (m.flash && m.flash.visible) { m.flash.userData.face.rotation.z = Math.random() * 6.28; m.flash.scale.setScalar(0.8 + Math.random() * 0.6); }
  updateTrail(now, m, trailOn && m.wrap.visible, TRAIL_COLOR[id] || 0xffffff);
  if (m.wrap.visible && G.skinFxVM) { m.wrap.updateMatrixWorld(true); emitSkinFx(G.skinFxVM, m.g, dt, 0.3 * cfg.s); }
}
