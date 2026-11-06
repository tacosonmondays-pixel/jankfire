// Local weapon logic, loadouts, ammo + first-person viewmodels.
import * as THREE from 'three';
import { nailSegs } from './primaries.js'; // the nail gun's nails in walls
import { beamStart, beamOn, chargeLook, chargeWhine } from './beam.js'; // Big Laser Pointer
import { WEAPONS, ORDER, SLOTS, FLAGS, HIPFIRE, ARROW_TIPS, SUITS, RANKS, validLoadout, DEFAULT_LOADOUT, ITEMS, fireRate } from '/shared/weapons.js';
import { BOXES } from '/shared/map.js';
import { raycast, rayBox } from '/shared/physics.js';
import { G } from './ctx.js';
import { palOf, crossFired } from './bloodcross.js';
import { ME, eye, look, applyKb, hspeed } from './player.js';
import { vmBob } from './vmbob.js';
import { buildWeapon, M, cardFace, tipColor, setKatana, freeTree } from './models.js';
import { heatTeeth, spinTeeth } from './models.js';
import { fx } from './fx.js';
import { marbles } from './marbles.js';
import { sfx, loopSfx, stopLoops } from './audio.js';
import { shredMotor } from './audio.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { K } from './keys.js';
import { tracerColor, emitSkinFx } from './skins.js';
import { ANIMS, sample, sampleCh, eventsBetween, inspectFor, drawFor } from './anim.js';
import { newTwirl, resetTwirl, twirling, spin, settle, twirlShot, stepTwirl, applyTwirl } from './twirl.js';
import { partsShot, stepParts } from './glbkit.js';
import { balisongStep } from './balisong.js'; // real balisong flips
import { reloadStep, reloadEvent } from './reloads.js'; // proper reloads for the guns that only dipped
import { gunHand, mirrorHand } from './hands.js'; // PS1 low-poly hands
import { bladeStep, bladeIdle, TRAIL_LIFE } from './bladefeel.js'; // snappy knives + katana: tosses, smears, idle sway
import { katanaHands, katanaStep, katanaEvent, KAT_VM } from './katanavm.js'; // two hands on the katana
import { weaponIcon, clearIcons, itemIcon } from './icons.js';
import { rigFire, rigItem, rigVM, rigBlockKey, rigReload } from './rig.js'; // overdrive rig killstreak
import { tickScalesVM } from './scales.js';
import { PARRY } from '/shared/weapons.js';
import { SIDEARMS, reloadAnim, sideParts, sideHand, sideShot, sideStep, stepOffHand, sideEvent } from './sidearms.js'; // Plan B, Lefty & Righty, Half a Shotgun
import { ROYAL } from '/shared/looks.js';
import { secFireDown, secShot } from './secondaries.js'; // taser, tv remote, water pistol streams
import { RIFLES, RF, RIFLE_VM, RIFLE_RECOIL, RIFLE_SHELLS, rifleShot, bursting, rifleReset, quickScoped, rifleStep, rifleEvent } from './rifles.js'; // the rifle pack
import { tacOn, tacShot, tacKick, tacFrame } from './tactical.js'; // Plant & Defuse: spray patterns + moving spread
import { carRay, carHit, carSwing } from './traffic.js'; // cars stop bullets (and take the damage)

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
  laser: { back: 1.8, up: 5, roll: 1.2, side: 0.15, punch: 0.03 },
  nailgun: { back: 0.8, up: 2.6, roll: 1.8, side: 0.25, punch: 0.01 }, // the new primaries: a pneumatic tap,
  tennis: { back: 1.6, up: 4.5, roll: 1.4, side: 0.2, punch: 0.025 }, // a felt THWOCK,
  cart: { back: 4.2, up: 7, roll: 2.4, side: 0.4, punch: 0.07 }, // and a whole cart leaving your shoulder
  pistol: { back: 1.1, up: 7, roll: 1.6, side: 0.15, punch: 0.022 },
  akimbo: { back: 0.7, up: 2.6, roll: 1.8, side: 0.3, punch: 0.006 }, // per hand (sidearms.js has a spring for each)
  sawnoff: { back: 3.4, up: 16, roll: 3.5, side: 0.35, punch: 0.085 },
};
Object.assign(RECOIL, RIFLE_RECOIL);
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
const FLASH_IDS = new Set(['ar', 'smg', 'redline', 'marbles', 'shotgun', 'minigun', 'sniper', 'revolver', 'scythe_rifle', 'chicken', 'bowling', 'banana', 'cart', 'pistol', 'akimbo', 'sawnoff']);
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
  if (g.userData.port) tmpV.copy(g.userData.port); else tmpV.set(0.03, 0.035, g.userData.muzzle.z * 0.35); // a model can say where its port is
  g.localToWorld(tmpV);
  const sz = big ? 0.03 : 0.018;
  G.skinFxVM.norm.spawn(tmpV.x, tmpV.y, tmpV.z, 0.6 + Math.random() * 0.5, 0.75 + Math.random() * 0.5, 0.1 + Math.random() * 0.25,
    0.55, sz, sz * 0.9, color, color, 1, 4.5, 0.4);
}
const SHELL_ON_FIRE = new Set(['ar', 'smg', 'redline', 'minigun', 'scythe_rifle', ...RIFLE_SHELLS, 'pistol', 'akimbo']);
for (const id of RIFLES) FLASH_IDS.add(id);

// smear trail: a fading ribbon behind the tip of whatever you swing
const TRAIL_N = 26;
const TRAIL_COLOR = { knife: 0xbfe8ff, bread: 0xffd9a0, spoon: 0xffffff, slapper: 0xffb0d0, scythe: 0xff3ad8, slipper: 0xb0ffb0, cards: 0xffffff };
TRAIL_COLOR.scales = 0xffd86a; // brass
TRAIL_COLOR.claw = 0x7dff4f;
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
function updateTrail(now, m, active, color, life = 120) {
  if (!trail) return;
  if (active && m) {
    m.wrap.updateMatrixWorld(true);
    const mz = m.g.userData.muzzle;
    tmpV.copy(mz); m.g.localToWorld(tmpV);
    tmpV2.copy(mz).multiplyScalar(0.45); m.g.localToWorld(tmpV2);
    trailPts.unshift({ t: now, a: [tmpV.x, tmpV.y, tmpV.z], b: [tmpV2.x, tmpV2.y, tmpV2.z] });
  }
  while (trailPts.length > TRAIL_N || (trailPts.length && now - trailPts[trailPts.length - 1].t > life)) trailPts.pop();
  const n = trailPts.length;
  trail.visible = n >= 3;
  if (!trail.visible) return;
  const pos = trail.geometry.attributes.position.array, col = trail.geometry.attributes.color.array;
  tcol.setHex(color);
  for (let i = 0; i < n; i++) {
    const q = trailPts[i], k = Math.max(0, 1 - (now - q.t) / life) * (1 - i / n) * 0.9;
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
export function cycleCard() { if (rigBlockKey()) { W.aimHeld = true; return; } const n = (G.hand || []).length; if (n) { W.cardSel = (W.cardSel + 1) % n; sfx.click(); } }
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
  if (g.userData.adsPose) pose = g.userData.adsPose.slice(); // a Blender model with no sights says where it sits while aiming
  else if (sg) pose = [0, -sg.y * s, -EYE_RELIEF - sg.z * s]; // sight line exactly through the middle
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
export function setItem(id) { if (Object.hasOwn(ITEMS, id)) W.item = id; }
export function resetItems() { W.ic = {}; W.reverseUntil = 0; } // a reverse card doesn't survive death (the server drops it)
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
  if (performance.now() < (ME.ballUntil || 0)) return; // wrecking ball: no hands
  const id = W.item, it = ITEMS[id];
  if (rigItem()) return; // overdrive rig: G fires the missile salvo
  if (!it || !ME.alive || (W.eco && W.eco.dry('item'))) return;
  const c = charges(id);
  if (performance.now() - (W.itemT || 0) < 420) return; // same spam limit as the server
  if (W.itemHook && W.itemHook(id)) return; // new gear (gear.js): the camera's free photo, goggles on / off
  if (c.n <= 0) { sfx.empty(); hud.msg(`${it.name}: recharging`, 0.8); return; }
  W.itemT = performance.now();
  c.n--; if (!c.next && !W.eco && !W.br) c.next = performance.now() + it.recharge * 1000; // (jank royale gadgets don't recharge either)
  net.send({ t: 'item', i: id, o: eye().map(r2), d: look().map(r2) });
  if (id === 'wand' || id === 'camera' || id === 'nvg') return; // no toss: the wand, camera and goggles have their own viewmodels
  if (it.w) popItem(it.w); // party popper / reverse card: pops into your hand (see popEvent for what it does)
  if (!W.anim || W.anim.kind === 'inspect' || W.anim.kind === 'draw') playAnim('toss_item', 'item');
  if (id === 'medkit') sfx.heal(); else if (id === 'bubble') sfx.reverse(); else sfx.swing();
}

// ------------------------------------------------------------ item pop-ins: party popper, reverse card
// the item pops up in your left hand (wearing its skin), does its thing and drops away again. your gun stays out.
const POP = {
  popper: { p: [-0.16, -0.15, -0.36], r: [0.1, -0.25, -0.2], anim: 'pop_popper' },
  reverse: { p: [-0.09, -0.09, -0.3], r: [0.05, 0.3, 0.1], anim: 'pop_reverse' },
};
const CONFETTI = [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff7a1a, 0xffffff];
function popItem(id) {
  if (!POP[id] || !models[id]) return;
  cancelInspect();
  W.pop = { id, t: 0 };
  if (!W.anim || W.anim.kind === 'draw') playAnim('dip_item', 'item'); // the gun makes room
}
// the popped item's muzzle in the world (viewmodel space lines up with the camera)
function popMuzzle(m) {
  tmpV.copy(m.g.userData.muzzle); m.g.localToWorld(tmpV);
  G.camera.updateMatrixWorld(); G.camera.localToWorld(tmpV);
  return [tmpV.x, tmpV.y, tmpV.z];
}
function popEvent(ev, m) {
  const sys = G.skinFxVM, R = (k) => (Math.random() - 0.5) * k;
  vmRoot.updateMatrixWorld(true);
  tmpV.copy(m.g.userData.muzzle); m.g.localToWorld(tmpV); // viewmodel space
  const x = tmpV.x, y = tmpV.y, z = tmpV.z;
  if (ev === 'pop') { // yank: confetti, everyone in front gets shoved (the server checks you really popped one), you fly back
    const w = WEAPONS.popper, o = eye(), d = look();
    for (const tg of conePlayers(o, d, w.range, w.cone)) {
      net.send({ t: 'hit', to: tg.r.id, w: 'popper', d: d.map(r2) });
      fx.spray([tg.r.pos[0], tg.r.pos[1] + 1.3, tg.r.pos[2]], 14, CONFETTI, 6, 0.8, 0.14, 4, 1.5);
    }
    fx.confetti(popMuzzle(m), d, ME.vel);
    for (let i = 0; i < 40; i++) sys.norm.spawn(x + R(0.03), y + R(0.03), z + R(0.03), R(1.6), 0.3 + R(1.4), -1.2 - Math.random() * 2.2, 0.5, 0.022, 0.018, CONFETTI[(Math.random() * CONFETTI.length) | 0], 0xffffff, 1, 2, 1.5);
    sfx.popper(); sfx.partyHorn();
    applyKb([-d[0] * w.recoil, -d[1] * w.recoil + w.lift, -d[2] * w.recoil]);
    punchCam(-0.05, 0.02 * rnd(), 0.05 * rnd());
    G.shake = Math.max(G.shake, 0.45);
  } else if (ev === 'flash') { // reverse card: a ring of red + yellow off the card
    for (let i = 0; i < 36; i++) { const a = Math.random() * Math.PI * 2, s = 0.5 + Math.random() * 0.8; sys.add.spawn(x + R(0.02), y + R(0.02), z, Math.cos(a) * s, Math.sin(a) * s, R(0.3), 0.4, 0.03, 0.004, i % 2 ? 0xff3b3b : 0xffd23b, 0xffffff, 1, 0, 2); }
    sfx.reverse();
    punchCam(-0.02, 0, 0.03 * rnd());
  }
}
function updatePop(dt) {
  const P = W.pop;
  if (!P) return;
  const m = models[P.id], c = POP[P.id];
  const a = m && ME.alive ? sample(c.anim, P.t + dt) : null;
  if (!a) { if (m) m.wrap.visible = false; W.pop = null; return; }
  const t0 = P.t;
  P.t += dt;
  m.wrap.position.set(c.p[0] + a.p[0], c.p[1] + a.p[1], c.p[2] + a.p[2]);
  m.wrap.rotation.set(c.r[0] + a.r[0], c.r[1] + a.r[1], c.r[2] + a.r[2]);
  m.wrap.scale.setScalar(a.s);
  m.wrap.visible = !W.scoped;
  for (const ev of eventsBetween(c.anim, t0, P.t)) popEvent(ev, m);
  if (m.wrap.visible && G.skinFxVM) emitSkinFx(G.skinFxVM, m.g, dt, 0.3 * m.cfg.s);
}

// knife right click: CS-style heavy stab. returns false when this weapon has no heavy attack
export function heavyAttack() {
  if (performance.now() < (ME.ballUntil || 0)) return true; // wrecking ball: no hands
  const id = W.cur, w = WEAPONS[id], now = performance.now();
  if (rigBlockKey()) return false; // overdrive rig: right click is the block (it holds W.aimHeld)
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

// ------------------------------------------------------------ katana parry (right click)
// opens a short window that the server checks hits against (it decides what got parried and tells everyone).
// returns false when the katana isn't out, so right click does its normal thing
export function parry() {
  if (W.cur !== 'katana') return false;
  const now = performance.now();
  if (canParry(now)) doParry(now);
  else if (ME.alive && (W.parryCd || 0) - now < 150) W.parryQ = now; // a hair early: buffer it
  return true;
}
// not mid-swing, not reeling from a parried swing of our own (the server refuses that too), and not in the first
// moment of pulling it out (the server hasn't seen it in your hand yet)
const canParry = (now) => ME.alive && now >= (W.parryCd || 0) && now >= (W.staggerUntil || 0) && W.pendingSwing <= 0 && !(W.anim && W.anim.kind === 'draw' && W.anim.t < 0.12);
function doParry(now) {
  W.parryQ = 0; W.parryT = now;
  W.parryCd = now + (PARRY.win + PARRY.cd) * 1000;
  W.cd.katana = Math.max(W.cd.katana || 0, now + PARRY.win * 1000); // no slashing out of the guard
  cancelInspect();
  net.send({ t: 'parry', y: r2(ME.yaw) });
  playAnim('parry_katana', 'parry');
}
// the server says we parried something: hit stop, the blade kicks, sparks fly off it. big = the first one in a while
export function parryLanded(perfect, big) {
  const m = models.katana;
  if (!m || W.cur !== 'katana') return;
  W.hitStop = Math.max(W.hitStop, big ? (perfect ? 0.13 : 0.09) : 0.03);
  const k = big ? 1 : 0.35;
  rec.rv[0] += (perfect ? 7 : 4.5) * k; rec.pv[2] += 1.1 * k; rec.rv[2] += 3 * rnd() * k;
  punchCam((perfect ? 0.05 : 0.03) * k, 0.02 * rnd() * k, 0.04 * rnd() * k);
  if (!G.skinFxVM) return;
  m.wrap.updateMatrixWorld(true);
  const R = (s) => (Math.random() - 0.5) * s;
  for (let i = 0, n = big ? (perfect ? 34 : 22) : 8; i < n; i++) {
    tmpV.copy(m.g.userData.muzzle).multiplyScalar(0.3 + Math.random() * 0.45); m.g.localToWorld(tmpV);
    G.skinFxVM.add.spawn(tmpV.x, tmpV.y, tmpV.z, R(2.4), 0.3 + Math.random() * 1.6, -0.2 - Math.random() * 1.3,
      0.16 + Math.random() * 0.24, perfect ? 0.034 : 0.028, 0.004, Math.random() < 0.5 ? 0xffffff : 0xfff2b0, 0xff7a10, 1, 6);
  }
}
// our swing got parried: whatever we hold gets knocked away, no attacking for a moment, half speed (see parryTick)
export function stagger(dur) {
  const now = performance.now();
  W.staggerUntil = now + dur * 1000;
  for (const id of W.slots) if (id) W.cd[id] = Math.max(W.cd[id] || 0, W.staggerUntil);
  W.pendingSwing = 0; W.pendingThrow = 0; W.heavy = false; W.parryQ = 0;
  cancelInspect();
  playAnim('staggered', 'stagger');
  rec.rv[0] += 5; rec.rv[2] += 6 * rnd(); rec.pv[2] += 1.5;
  punchCam(-0.06, 0.04 * rnd(), 0.08 * rnd());
  G.shake = Math.max(G.shake, 0.45);
}
// every frame: buffered presses, stagger slow-down, and the cooldown ring round the crosshair
function parryTick(now) {
  if (now < (W.staggerUntil || 0)) ME.speedMul *= 0.5;
  if (W.parryQ) { if (now - W.parryQ > 250 || W.cur !== 'katana') W.parryQ = 0; else if (canParry(now)) doParry(now); }
  if (W.cur !== 'katana' || !ME.alive) { hud.parryRing(null); return; }
  const t = (now - (W.parryT || -1e9)) / 1000, P = PARRY;
  if (t < P.win) hud.parryRing(1, 'open'); // guard is up
  else if (t < P.win + P.cd) hud.parryRing(1 - (t - P.win) / P.cd, 'cd'); // drains while it recharges
  else if (t < P.win + P.cd + 0.25) hud.parryRing(1, 'ready'); // a blink when it's back
  else hud.parryRing(null);
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
  pistol: { p: [0.165, -0.155, -0.31], r: [0, 0.06, 0], s: 1.0, handGlb: [0.004, -0.042, -0.008] }, // a real 1911's grip sits further forward
  akimbo: { p: [0.215, -0.165, -0.4], r: [0, 0.13, 0], s: 0.8 }, // the right gun; the left one is this mirrored
  sawnoff: { p: [0.19, -0.18, -0.34], r: [0, 0.05, 0], s: 0.85 },
  cig: { p: [0.15, -0.17, -0.3], r: [0.15, 0.6, 0.2], s: 1.1 },
  blower: { p: [0.24, -0.27, -0.45], r: [0, 0.05, 0], s: 0.6 },
  shredder: { p: [0.27, -0.26, -0.46], r: [0, 0.16, 0], s: 0.46 },
  laser: { p: [0.21, -0.215, -0.4], r: [0, 0.05, 0], s: 0.62 },
  nailgun: { p: [0.2, -0.155, -0.42], r: [0, 0.3, 0], s: 0.6 }, // turned so you see the nails in the magazine
  tennis: { p: [0.21, -0.21, -0.4], r: [0, 0.04, 0], s: 0.68 },
  cart: { p: [0.25, -0.235, -0.5], r: [0, 0.2, 0], s: 0.5 }, // side-on enough to see the basket sleeve
  popper: { p: [0.17, -0.18, -0.34], r: [0.1, 0.1, 0], s: 0.75 },
  reverse: { p: [0.15, -0.15, -0.34], r: [0.3, -0.3, 0.15], s: 0.65 },
  duck: { p: [0.17, -0.18, -0.4], r: [0.1, 0.5, 0], s: 0.55 },
  bread: { p: [0.3, -0.3, -0.42], r: [0.35, 0.2, -0.25], s: 0.55 },
  slipper: { p: [0.17, -0.18, -0.36], r: [0.2, 0.3, 0.3], s: 0.7 },
  snowball: { p: [0.17, -0.19, -0.33], r: [0.2, 0.2, 0.1], s: 0.75 },
  spoon: { p: [0.15, -0.15, -0.3], r: [0.2, 0.25, 0.1], s: 1.3 },
  knife: { p: [0.16, -0.17, -0.3], r: [0.15, 0.2, 0.15], s: 1.3 },
  katana: KAT_VM, // kamae: both hands on the tsuka, blade up and forward (katanavm.js)
  bow: { p: [0.1, -0.12, -0.36], r: [0, 0.05, 0.3], s: 1.0 },
  cards: { p: [0.1, -0.15, -0.3], r: [-0.35, 0.15, 0.05], s: 1.15 },
  slapper: { p: [0.22, -0.24, -0.42], r: [0.25, 0.1, 0], s: 0.7 },
  scythe: { p: [0.3, -0.33, -0.46], r: [0.25, 0.25, -0.3], s: 0.55 },
  scythe_rifle: { p: [0.2, -0.21, -0.4], r: [0, 0.03, 0], s: 0.6 },
  scales: { p: [0.27, -0.335, -0.47], r: [0.06, 0.12, 0], s: 0.6 }, // held upright, beam across the view
  lasso: { p: [0.2, -0.24, -0.4], r: [0.1, 0.4, 0], s: 0.9 }, // (lasso.js hides this and animates its own hands + rope)
  claw: { p: [0.17, -0.17, -0.3], r: [0.25, 0.2, 0.35], s: 1.0 },
};

// Blood Cross: a bare hand low on the right, turned in side-on and rolled a little so you read it as a finger gun (from straight
// behind, the thumb hides the finger)
Object.assign(VM, RIFLE_VM);
VM.bloodcross = { p: [0.165, -0.17, -0.33], r: [0.13, 0.43, 0.28], s: 1.22 };
RECOIL.bloodcross = { back: 0.5, up: 3.5, roll: 1.2, side: 0.15, punch: 0.018 };
// the new secondaries (secondaries.js): squirt pistol, taser, tv remote held like a pistol, pointed at the screen
Object.assign(VM, { water: { p: [0.18, -0.18, -0.355], r: [0.02, 0.08, 0], s: 0.74 }, taser: { p: [0.165, -0.14, -0.31], r: [0.03, 0.12, -0.1], s: 0.95 }, remote: { p: [0.15, -0.14, -0.29], r: [0.35, 0.12, -0.12], s: 0.95 } });
const bcQ = new THREE.Quaternion(), bcY = new THREE.Vector3(0, 1, 0); // opening + closing the fist
let vmRoot;
const models = {};
const tmpV = new THREE.Vector3();
export const vmModel = (id) => models[id]; // the lasso draws its own hands and hides this one

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
    const hand = gunHand(id, cfg, g, g.userData.model); // a PS1 hand round the grip, index on the trigger (hands.js; cfg.hand / handGlb: where the grip is)
    wrap.add(hand);
    if (g.userData.bare) { hand.visible = false; g.add(g.userData.bare); } // Blood Cross: the hand is the weapon (+ your forearm)
    wrap.position.set(...cfg.p);
    wrap.rotation.set(...cfg.r);
    wrap.visible = id === W.cur;
    vmRoot.add(wrap);
    let flash = null;
    if (FLASH_IDS.has(id) && g.userData.muzzle) { flash = makeFlash(id === 'shotgun' || id === 'sniper' || id === 'autoshot' || id === 'dmr'); flash.position.copy(g.userData.muzzle); g.add(flash); }
    models[id] = { wrap, g, cfg, flash, hand };
    if (WEAPONS[id].hands) models[id].left = akLeftModel(id, cfg, hand); // Lefty & Righty: a second gun for the left hand
    if (SIDEARMS.has(id)) sideHand(g, id, 'R');
    if (id === 'katana') katanaHands(models[id], hand); // held like a katana: both fists on the tsuka
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
  for (const id of ORDER) if (WEAPONS[id].mag && !W.eco && !W.br) W.ammo[id] = WEAPONS[id].mag; // (jank royale: bullets come off the floor)
  W.reloadId = null;
  W.fuel.blower = WEAPONS.blower.fuel;
  W.slipperOut = false;
  // katana parry: a new life (spawn, join) starts with the guard ready, like the server. not on a weapon swap:
  // the server keeps your cooldown and stagger through those
  W.parryT = 0; W.parryCd = 0; W.parryQ = 0; W.staggerUntil = 0;
}

export function setLoadout(lo) {
  const v = validLoadout(lo);
  W.item = v.item;
  // chaos modes hand you a fixed kit: just these weapons, maybe no item, maybe no reloading (bullets come from kills)
  const kit = lo && Array.isArray(lo.only) ? lo.only.filter((id) => WEAPONS[id]) : null;
  if (kit && kit.length) { W.hasScythe = false; ME.dashing = false; }
  W.noReload = !!(lo && lo.noReload);
  const streakSlot = W.hasScythe ? (W.slots[3] || 'scythe') : null;
  W.slots = SLOTS.map((s) => v[s]);
  if (kit && kit.length) W.slots = kit;
  if (lo && lo.item === 'none') W.item = null;
  if (streakSlot) W.slots[3] = streakSlot;
  if (W.only) { W.slots = [W.only]; W.item = null; } // gun game / zombies: one weapon, no item
  if (W.slot >= W.slots.length) W.slot = 0;
  showSlots();
  W.cur = null;
  equip(W.slot);
}

// gun game / infection: the server hands you exactly one weapon (a fresh mag of it). null = back to `lo`
W.only = null;
export function setOnly(id, lo) {
  W.only = WEAPONS[id] ? id : null;
  if (W.only && WEAPONS[id].mag) W.ammo[id] = WEAPONS[id].mag;
  if (W.reloadId && W.reloadId !== W.only) W.reloadId = null;
  W.slot = 0;
  setLoadout(lo);
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
  const iw = ITEMS[W.item] && ITEMS[W.item].w; // popper / reverse card: a picture of the real thing, skin and all
  hud.itemSlot(W.item, (iw && weaponIcon(iw, (G.equipped || {})[iw])) || itemIcon(W.item));
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
  if (WEAPONS[id] && WEAPONS[id].hands) W.aimHeld = false; // right click is a trigger now: don't walk in with it already pulled
  W.heavy = false; W.cycle = null; W.hitStop = 0;
  rifleReset(); // no half a burst waiting when you come back
  trailPts.length = 0;
  for (const h of [W.ak.L, W.ak.R]) { h.rl = 0; h.t = -1; h.want = false; h.paid = false; } // a swap drops the akimbo reloads (the server cancels its one too)
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
  if (rigReload()) return; // overdrive rig: R is the quickhack (no gun to reload)
  cancelInspect();
  if (W.cur === 'cards') { redrawCards(); return; }
  const id = W.cur, w = WEAPONS[id];
  if (W.noReload) return; // one in the chamber: bullets only come from kills
  if (w.hands) { akReloadAll(); return; } // Lefty & Righty: each hand reloads its own
  if (!w.mag || W.reloadId || W.ammo[id] >= w.mag || !ME.alive) return;
  if (W.br && !W.br.canReload(id)) return; // jank royale: no spare bullets
  if (W.eco && !W.eco.canReload(id)) return;
  W.reloadId = id;
  W.reloadUntil = performance.now() + w.reload * 1000;
  rifleReset();
  const ra = RIFLES.has(id) && ANIMS['reload_' + id] ? 'reload_' + id : reloadAnim(id, W.ammo[id]); // a real mag swap / belt change / spin-cock; the sidearms: mag out, mag in / shells out, shells in
  if (ra) { cancelInspect(); playAnim(ra, 'reload'); } else sfx.reload();
  if (W.eco) W.eco.reloading(id);
}

// for secondaries.js: kick the viewmodel, the muzzle in the world, a viewmodel by id
export const VMX = { kick: (id, k) => kickVM(id, k), muzzle: () => muzzleWorld(), model: (id) => models[id] };
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
// game modes add their own sides here (infection: zombies vs survivors)
export const modeFriends = [];
export const isFriend = (r) => !!(G.myTeam && r.team && r.team === G.myTeam) || modeFriends.some((f) => f(r));
function rayPlayers(o, d, maxT) {
  let best = null;
  for (const r of G.remotes.values()) {
    if (!r.alive || (isFriend(r) && !(r.trapUntil > performance.now()))) continue; // a teammate in a soap bubble can be shot free
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
    if (!r.alive || (isFriend(r) && !(r.trapUntil > performance.now()))) continue; // (or swung / burned free)
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
  if (fanShot) return fanSpread(w);
  const hip = (HIPFIRE[G.cfg.hip] || HIPFIRE.normal).mul;
  const base = (w.spread || 0) + W.bloom;
  const ads = w.ads ? base * (w.ads.spread ?? 1) * Math.min(1, hip) : base * hip;
  const hipS = base * hip;
  return hipS + (ads - hipS) * W.aim + (G.heldSpread || 0); // + swinging on the end of someone's lasso
}

// the gun's own spread right now, without bloom (Plant & Defuse: the spray pattern replaces bloom; moving adds on top)
function tacBase(w) {
  if (fanShot) return fanSpread(w);
  const hip = (HIPFIRE[G.cfg.hip] || HIPFIRE.normal).mul, base = w.spread || 0;
  const ads = w.ads ? base * (w.ads.spread ?? 1) * Math.min(1, hip) : base * hip, hipS = base * hip;
  return hipS + (ads - hipS) * W.aim;
}
function fireHitscan(id, now, hand) { // hand: 'L' / 'R' = which of Lefty & Righty (they keep their own cooldowns)
  const w = WEAPONS[id];
  const tac = W.eco && tacOn() ? tacShot(id, tacBase(w), now) : null; // which spray shot, its spread, its directions
  if (tac && W.sendSnap) W.sendSnap(); // the server checks the shot against the aim in this snapshot
  if (w.mag && G.mode !== 'training') W.ammo[id]--;
  if (!hand) setCd(id, now);
  W.lastShotT = now;
  if (w.fanHammer && models[id]) applyTwirl(models[id].g, 0, models[id].cfg.s); // mid-twirl revolver: the shot leaves the resting muzzle (twirlVM spins it again before the next render)
  const o = eye(), base = look(), mz = hand ? akMuzzle(hand) : muzzleWorld();
  const hits = new Map(), carHits = new Map();
  const segs = [];
  const pellets = w.pellets || 1;
  const shots = w.marbles ? [] : null; // Marble Shotgun: each pellet becomes a marble that bounces off what it hit
  for (let i = 0; i < pellets; i++) {
    let d = tac ? tac.dir(i) : spreadDir(base, currentSpread(w));
    let from = o, left = w.range, bounces = w.ricochet || 0, drawFrom = mz;
    for (;;) {
      const mh = raycast(from, d, left, BOXES);
      const maxT = mh ? mh.t : left;
      const ph = rayPlayers(from, d, maxT);
      const ch = carRay(from, d, ph ? ph.t : maxT); // a car in the way takes it
      if (ch) {
        const end = [from[0] + d[0] * ch.t, from[1] + d[1] * ch.t, from[2] + d[2] * ch.t];
        segs.push([...drawFrom, ...end]);
        if (shots) shots.push({ a: drawFrom, b: end, n: ch.n, player: false });
        carHits.set(ch.id, (carHits.get(ch.id) || 0) + 1);
        if (!shots || i % 6 === 0) fx.sparks(end, d.map((x) => -x), 5, false);
        break;
      }
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
  const ns = id === 'sniper' && !W.scoped ? 1 : undefined; // no-scope: the server only makes it look cool, damage is the same
  const qs = (id === 'sniper' && W.scoped && now - W.scopedAt <= ROYAL.quick) || quickScoped(w, W, now) ? 1 : undefined; // quick-scope: fired right as the scope came up (Sniper Royalty only, never damage)
  for (const [cid, n] of carHits) { carHit(cid, id, n, base); hud.hit(false); }
  const r4 = (x) => Math.round(x * 10000) / 10000;
  for (const [rid, h] of hits) net.send({ t: 'hit', to: rid, w: id, d: h.d.map(tac ? r4 : r2), n: h.n, h: h.h, ns, qs, fan: fanShot ? 1 : undefined, ...(tac ? tac.msg : null), hd: hand === 'L' ? 1 : undefined });
  const fast = w.rate > 8;
  const skin = (W.skinOver || G.equipped || {})[id];
  if (shots) marbles.shoot(shots, marblePalette(skin));
  else if (!(w.water && secShot(segs, mz))) for (const s of segs) fx.tracer(s.slice(0, 3), s.slice(3), tracerColor(skin, w.tracer || 0xfff0a0), w.thick || (fast ? 0.03 : 0.045), fast ? 0.07 : 0.2);
  net.send({ t: 'fire', w: id, o: o.map(r2), s: segs.slice(0, 12).map((s) => s.map(r2)), fan: fanShot ? 1 : undefined, ...(tac ? tac.msg : null), hd: hand === 'L' ? 1 : undefined });
  if (id === 'nailgun') nailSegs(segs); // nails stay in the wall (primaries.js)
  if (w.recoil) applyKb([-base[0] * w.recoil, -base[1] * w.recoil, -base[2] * w.recoil]);
  if (tac) tacKick(id, tac.i); // Plant & Defuse: the camera climbs with the pattern (no random kick, no bloom)
  else {
    ME.pitch = Math.min(1.55, ME.pitch + (w.kick || 0) * (0.6 + Math.random() * 0.8) * (1 - W.aim * 0.5));
    ME.yaw += (Math.random() - 0.5) * (w.kick || 0) * 0.5;
    W.bloom = Math.min(w.maxBloom || 0, W.bloom + (w.bloom || 0));
  }
  if (!hand) W.kick = Math.min(1, W.kick + (fast ? 0.25 : 1));
  if (W.anim && W.anim.kind === 'draw') W.anim = null;
  if (hand) akKick(hand); // each gun kicks on its own
  else { kickVM(id, W.aim > 0.5 ? 0.6 : 1); W.flashT = fast ? 0.035 : 0.05; }
  const sg = hand ? akModel(hand) : models[id] && models[id].g;
  if (SHELL_ON_FIRE.has(id) && sg) ejectShell(sg);
  if (SIDEARMS.has(id) && sg) sideShot(sg, id); // the slide / knob kicks, the hammer drops
  if (id === 'shotgun') W.cycle = { name: 'pump_shotgun', t: 0.22 };
  if (id === 'sniper' || id === 'scythe_rifle') W.cycle = { name: 'bolt_sniper', t: 0.32 };
  if (RIFLES.has(id)) rifleShot(id, w, W, now); // bursts, heat, the lever
  if (w.fanHammer) revolverShot(w, now);
  if (models[id]) partsShot(models[id].g); // Blender guns: turn the cylinder, drop the hammer
  if (id === 'sniper' || id === 'shotgun' || id === 'dmr') G.shake = Math.max(G.shake, 0.6);
  sfx.gun(id, null, id === 'redline' ? redlineK() : id === 'lmg' ? RF.heat : 0);
  if (!hand && w.mag && W.ammo[id] <= 0) reload();
}

// ------------------------------------------------------------ revolver: twirl after every shot, hold to fan the hammer
// a tap is the accurate shot. keep holding and the rest of the cylinder goes at fanHammer.rate with wild spread and
// fan damage (the server checks both). the gun spins round your trigger finger after every shot and the whole time
// you fan. aiming down sights = plain single shots, no twirl in front of your eye.
W.twirl = newTwirl();
W.fanning = { on: false, arm: false, down: 0, next: 0, hammer: 0 };
let fanShot = false; // the shot being fired right now is a fanned one (spread + net messages read this)
const fanSpread = (w) => w.fanHammer.spread * (HIPFIRE[G.cfg.hip] || HIPFIRE.normal).mul;
function revolverShot(w, now) {
  const twirl = fanShot || (!W.aimHeld && W.aim < 0.5);
  if (!fanShot) W.fanning.next = now + 1000 / w.fanHammer.rate;
  if (twirl) twirlShot(W.twirl, fanShot);
  if (twirl && !fanShot) sfx.twirl();
}
function fanTheHammer(id, w, now) {
  const F = W.fanning, f = w.fanHammer, iv = 1000 / f.rate;
  if (F.hammer && now >= F.hammer) { F.hammer = 0; if (F.on) sfx.hammer(); }
  if (!(ME.alive && W.held && F.arm && !W.aimHeld && !W.reloadId)) {
    // let go, ran dry, aimed or died: stop fanning and catch the gun. anything but letting go needs a fresh click
    if (W.held) F.arm = false;
    if (F.on) { F.on = false; settle(W.twirl); }
    return;
  }
  if (now - F.down < f.hold * 1000 || now < F.next) return;
  if (W.ammo[id] <= 0) { reload(); return; }
  const was = F.on, p0 = ME.pitch, y0 = ME.yaw, v0 = ME.vel.slice();
  F.on = true;
  cancelInspect();
  fanShot = true;
  fireHitscan(id, now);
  fanShot = false;
  // the off hand holds it down: a fraction of the aim kick and the shove
  ME.pitch = p0 + (ME.pitch - p0) * f.kick; ME.yaw = y0 + (ME.yaw - y0) * f.kick;
  for (let i = 0; i < 3; i++) ME.vel[i] = v0[i] + (ME.vel[i] - v0[i]) * f.kick;
  W.cd[id] = now + 1000 / w.rate; // a tap after fanning waits one normal shot, not every fanned one stacked up
  F.next = (was ? Math.max(F.next, now - Math.min(40, iv * 0.5)) : now) + iv;
  F.hammer = now + iv * 0.55; // slap the hammer back between shots
}
// every frame: fan if held. anything else out = the revolver forgets it was mid-twirl, and a hold that started on
// another gun doesn't fan when you switch to it
function revolverFrame(id, w, now) {
  if (w.fanHammer) { fanTheHammer(id, w, now); return; }
  W.fanning.arm = false;
  if (W.fanning.on || twirling(W.twirl)) { W.fanning.on = false; resetTwirl(W.twirl); }
}
// spin the viewmodel round the trigger finger (the hand stays put). returns how far into the twirl pose it is
function twirlVM(m, dt) {
  const s = W.twirl;
  if (W.aimHeld && s.seg && !s.seg.quick) { spin(s, 0.12, -4, 0); s.seg.quick = true; } // aiming: finish the turn now
  const a = stepTwirl(s, dt);
  applyTwirl(m.g, a, m.cfg.s);
  if (m.flash) { // the flash hangs where the shot left the muzzle instead of spinning off with the barrel
    const mz = m.g.userData.muzzle, c = Math.cos(a), sn = Math.sin(a), y = mz.y - m.g.position.y / m.cfg.s, z = mz.z - m.g.position.z / m.cfg.s;
    m.flash.position.set(mz.x, y * c + z * sn, z * c - y * sn); m.flash.rotation.x = -a;
  }
  return s.k * (1 - W.aim);
}

// ------------------------------------------------------------ Lefty & Righty: a machine pistol in each hand
// left click = the left gun, right click (W.aimHeld: there's no aiming with these) = the right one. each hand has its
// own half of the ammo, its own fire cooldown, its own recoil spring and its own reload (in Plant & Defuse the hands
// take turns, so the server's one reload at a time stays in step). W.ammo.akimbo is the total, like any gun.
const akHand = () => ({ n: 0, cd: 0, rl: 0, t: -1, want: false, paid: false, flash: 0, p: [0, 0, 0], pv: [0, 0, 0], r: [0, 0, 0], rv: [0, 0, 0] });
W.ak = { L: akHand(), R: akHand(), tot: -1 };
const AKW = WEAPONS.akimbo, AK_HM = AKW.mag / AKW.hands; // rounds per hand
function akLeftModel(id, cfg, rh) {
  const wrap = new THREE.Group();
  const g = buildWeapon(id, (W.skinOver || G.equipped || {})[id]);
  g.scale.setScalar(cfg.s);
  wrap.add(g);
  const hand = mirrorHand(rh); wrap.add(hand); // a left hand on the left gun
  wrap.visible = false;
  vmRoot.add(wrap);
  const flash = makeFlash(false); flash.position.copy(g.userData.muzzle); g.add(flash);
  sideHand(g, id, 'L');
  return { wrap, g, flash, cfg };
}
const akModel = (hand) => { const m = models.akimbo; return m && (hand === 'L' ? m.left && m.left.g : m.g); };
function akMuzzle(hand) {
  const g = akModel(hand);
  if (!g) return eye();
  vmRoot.updateMatrixWorld(true);
  tmpV.copy(g.userData.muzzle); g.localToWorld(tmpV);
  G.camera.updateMatrixWorld(); G.camera.localToWorld(tmpV);
  return [tmpV.x, tmpV.y, tmpV.z];
}
function akKick(hand) {
  const h = W.ak[hand], k = RECOIL.akimbo, sx = hand === 'L' ? -1 : 1;
  h.pv[2] += k.back; h.rv[0] += k.up; h.rv[2] += k.roll * rnd() * sx; h.pv[0] += k.side * rnd();
  h.flash = 0.04;
  punchCam(k.punch, k.punch * 0.5 * sx, k.punch * 0.6 * sx); // the camera leans toward whichever gun went off
}
function akSprings(h, dt) {
  const n = Math.min(40, Math.max(1, Math.ceil(dt * 240))), st = dt / n;
  for (let s = 0; s < n; s++) for (let i = 0; i < 3; i++) {
    h.pv[i] += (-220 * h.p[i] - 20 * h.pv[i]) * st; h.p[i] += h.pv[i] * st;
    h.rv[i] += (-200 * h.r[i] - 18 * h.rv[i]) * st; h.r[i] += h.rv[i] * st;
  }
}
// the total changed under us (respawn refill, a Plant & Defuse buy / pickup / ammo message): share it out again
function akSync() {
  const tot = W.ammo.akimbo || 0, A = W.ak;
  if (A.L.n + A.R.n === tot && A.tot === tot) return;
  // Plant & Defuse: the server finishes a reload a bit before the animation does and tells us the new total. that's
  // the reloading hand's mag: it's paid (akFinish only has to put the gun back up)
  const h = A.L.rl && !A.L.paid ? A.L : A.R.rl && !A.R.paid ? A.R : null, diff = tot - A.L.n - A.R.n;
  if (W.eco && h && diff > 0 && diff <= AK_HM - h.n) { h.n += diff; h.paid = true; A.tot = tot; return; }
  A.L.rl = A.R.rl = 0; A.L.t = A.R.t = -1; A.L.want = A.R.want = A.L.paid = A.R.paid = false;
  A.R.n = Math.min(AK_HM, Math.ceil(tot / 2)); A.L.n = Math.min(AK_HM, tot - A.R.n);
  A.tot = tot;
}
function akReload(side, now = performance.now()) {
  const h = W.ak[side], other = W.ak[side === 'L' ? 'R' : 'L'];
  if (h.rl || h.n >= AK_HM || !ME.alive || W.noReload) return;
  if (W.br && !W.br.canReload('akimbo')) return; // jank royale: no spare bullets
  if (W.eco) {
    if ((W.res.akimbo || 0) <= 0) { W.eco.canReload('akimbo'); return; } // says OUT OF AMMO
    if (other.rl) { h.want = true; return; } // one at a time here: the server runs one reload per gun
    net.send({ t: 'rl', w: 'akimbo', n: AK_HM - h.n });
  }
  h.want = false; h.rl = now + AKW.reload * 1000; h.t = 0;
}
function akReloadAll() { akReload('R'); akReload('L'); }
function akFinish(side) {
  const h = W.ak[side], need = AK_HM - h.n;
  if (h.paid) { h.paid = false; h.rl = 0; return; } // the server's ammo message already filled it
  const mv = W.br ? W.br.take('akimbo', need) : W.eco ? Math.min(need, W.res.akimbo || 0) : need;
  if (W.eco) W.res.akimbo = (W.res.akimbo || 0) - mv;
  h.n += mv; W.ammo.akimbo = (W.ammo.akimbo || 0) + mv; W.ak.tot = W.ammo.akimbo;
  h.rl = 0;
}
function akimboFrame(id, now) {
  const A = W.ak, w = AKW;
  akSync();
  const iv = 1000 / w.rate, trig = { L: W.held, R: W.aimHeld };
  const dry = W.eco && W.eco.dry(id, true); // the buy phase
  for (const side of ['R', 'L']) {
    const h = A[side];
    if (h.rl && now >= h.rl) akFinish(side);
    if (h.want && !A[side === 'L' ? 'R' : 'L'].rl) akReload(side, now);
    if (!ME.alive || dry || !trig[side] || h.rl) continue;
    for (let i = 0; i < 3 && h.cd <= now; i++) {
      if (h.n <= 0) { akReload(side, now); break; }
      h.cd = Math.max(h.cd, now - Math.min(40, iv * 0.5)) + iv;
      if (G.mode !== 'training') h.n--;
      cancelInspect();
      fireHitscan(id, now, side);
      A.tot = W.ammo.akimbo;
      if (h.n <= 0) { akReload(side, now); break; } // empty: that hand goes for a fresh mag, the other keeps going
    }
  }
}
// both guns' poses: the left one is the right one mirrored (except the lag, which drags both the same way), plus each
// hand's own recoil and reload. P = the right gun's pose so far, sw = the lag part of it
function akimboVM(m, dt, now, P, sw) {
  const A = W.ak, L = m.left;
  if (!L) return;
  const hp = {};
  for (const side of ['R', 'L']) {
    const h = A[side];
    akSprings(h, dt);
    h.flash = Math.max(0, h.flash - dt);
    let o = { p: [0, 0, 0], r: [0, 0, 0] };
    if (h.rl) {
      const t0 = h.t; h.t += dt;
      const g = side === 'L' ? L.g : m.g, mm = side === 'L' ? L : m;
      for (const ev of eventsBetween('reload_akimbo', t0, h.t)) sideEvent(ev, mm, 'akimbo');
      const a = sample('reload_akimbo', h.t);
      if (a) o = a;
      sideStep(g, 'akimbo', 0, 'reload_akimbo', h.t, {}, sampleCh);
    } else h.t = -1;
    hp[side] = o;
  }
  const R = hp.R, Lp = hp.L, a = A.R, b = A.L;
  // right: its reload + recoil on top
  P.px += R.p[0] + a.p[0]; P.py += R.p[1] + a.p[1]; P.pz += R.p[2] + a.p[2];
  P.rx += R.r[0] + a.r[0]; P.ry += R.r[1]; P.rz += R.r[2] + a.r[2];
  // left: mirror the right's base (minus what this hand added), keep the lag the same way round
  const bx = P.px - R.p[0] - a.p[0], by = P.py - R.p[1] - a.p[1], bz = P.pz - R.p[2] - a.p[2];
  const brx = P.rx - R.r[0] - a.r[0], bry = P.ry - R.r[1], brz = P.rz - R.r[2] - a.r[2];
  L.wrap.position.set(-(bx - sw.x) + sw.x - Lp.p[0] - b.p[0], by + Lp.p[1] + b.p[1], bz + Lp.p[2] + b.p[2]);
  L.wrap.rotation.set(brx + Lp.r[0] + b.r[0], -(bry - sw.ry) + sw.ry - Lp.r[1], -(brz - sw.rz) + sw.rz - Lp.r[2] - b.r[2]);
  L.wrap.scale.copy(m.wrap.scale);
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
  else if (id === 'tennis') sfx.tennisFire();
  else if (id === 'cart') { sfx.cartFire(); G.shake = Math.max(G.shake, 0.5); applyKb(look().map((x) => -x * 6)); } // it shoves you back a step
  else if (id === 'slipper') { /* the throw animation already whooshed */ }
  else sfx.pew();
  W.kick = id === 'chicken' || id === 'bowling' || id === 'cart' ? 0.8 : 0.35;
  if (id !== 'slipper') {
    if (W.anim && W.anim.kind === 'draw') W.anim = null;
    kickVM(id);
    if (FLASH_IDS.has(id)) W.flashT = 0.05;
  }
}

// Blood Cross: point and pay. the server takes the 12 HP (and says no below 1 HP), you get the thump, the flick and a spurt of blood
function fireBlood(now) {
  const w = WEAPONS.bloodcross, m = models.bloodcross;
  if (ME.hp - w.cost < 1) { sfx.empty(); hud.msg('NOT ENOUGH BLOOD', 0.8, 'reverse'); W.cd.bloodcross = now + 300; return; }
  setCd('bloodcross', now);
  const o = eye(), d = look();
  net.send({ t: 'fire', w: 'bloodcross', o: o.map(r2), d: d.map(r2) });
  sfx.bcBeat();
  W.kick = 0.3; W.flashT = 0.07;
  playAnim('bang_bloodcross', 'bang');
  kickVM('bloodcross');
  if (!m) return;
  const P = palOf(G.myId), sys = G.skinFxVM, R = (k) => (Math.random() - 0.5) * k;
  m.wrap.updateMatrixWorld(true);
  m.g.userData.fingertip.getWorldPosition(tmpV);
  if (sys) {
    for (let i = 0; i < 18; i++) sys.add.spawn(tmpV.x, tmpV.y, tmpV.z, R(0.5), 0.05 + R(0.4), -0.5 - Math.random() * 0.9, 0.2, 0.02, 0.002, P.core, P.glow, 1, 0, 2); // hot sparks
    for (let i = 0; i < 10; i++) sys.norm.spawn(tmpV.x, tmpV.y, tmpV.z, R(0.3), 0.08 + Math.random() * 0.25, -0.2 + R(0.3), 0.5, 0.009, 0.006, P.glow, P.deep, 1, 3, 0.5); // a spurt of blood
  }
  crossFired(muzzleWorld(), [o[0] + d[0] * 7, o[1] + d[1] * 7, o[2] + d[2] * 7]);
}

function swing(id, now) {
  const w = WEAPONS[id];
  setCd(id, now);
  W.swing = 1;
  W.swingId = id;
  net.send({ t: 'fire', w: id, o: eye().map(r2), d: look().map(r2) });
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
  if (carSwing(o, d, hv ? hv.range : reach, id)) { sfx.bonk(); W.hitStop = 0.05; G.shake = Math.max(G.shake, 0.3); return; } // bonked a car
  if (w.pogo) {
    const mh = raycast(o, d, w.range, BOXES);
    if (mh) {
      applyKb([-d[0] * w.pogo, -d[1] * w.pogo, -d[2] * w.pogo]);
      fx.impact(mh.point, mh.normal);
      sfx.bonk();
    }
  }
}

// a cough: a burst of smoke billows out in front of your face (no fire), thickening as it spreads. others see it too
export function coughCloud(o, d) {
  for (let i = 0; i <= 14; i++) {
    const t = i / 14, k = 0.45 + t * 2.9;
    fx.smoke([o[0] + d[0] * k, o[1] - 0.12 + d[1] * k + t * 0.25, o[2] + d[2] * k], 2 + Math.round(t * 3), 0.05 + t * 0.45);
  }
  fx.spray([o[0] + d[0] * 0.6, o[1] - 0.1 + d[1] * 0.6, o[2] + d[2] * 0.6], 14, [0xd8d8d8, 0xa8a8a8, 0x8a8a8a], 3, 1.1, 0.32, -0.6, 1.6);
}
function cough() {
  net.send({ t: 'cough' });
  sfx.cough();
  hud.msg('*cough cough*', 1.2);
  coughCloud(eye(), look());
  W.charge = 0;
  W.coughLock = true;
  G.shake = Math.max(G.shake, 0.5);
}

export function fireDown() {
  if (performance.now() < (ME.ballUntil || 0)) return; // wrecking ball: no hands
  W.held = true;
  if (rigFire(true)) return; // overdrive rig: hold to charge the rocket punch
  cancelInspect();
  const id = W.cur, w = WEAPONS[id], now = performance.now();
  W.fanning.down = now; W.fanning.arm = true; // revolver: keep holding from here to fan the hammer
  if (w.hands) return; // Lefty & Righty: akimboFrame fires whichever triggers are held
  if (!ME.alive || W.reloadId === id || !ready(id, now)) return;
  if (W.br && W.br.dry(id)) { W.held = false; return; } // jank royale: out of shots
  if (W.eco && W.eco.dry(id)) { W.held = false; return; }
  if (W.anim && W.anim.kind === 'draw') W.anim = null;
  if (w.kind === 'hitscan' && !w.auto && !w.spinup) {
    if (W.ammo[id] > 0) fireHitscan(id, now); else { sfx.empty(); reload(); }
  } else if (w.burst && w.kind === 'hitscan') { if (W.ammo[id] > 0) fireHitscan(id, now); } // Hat Trick: the burst starts on the press, a tap finishes it (the Blood Cross's `burst` is its pop delay, not a burst)
  else if (w.kind === 'melee') swing(id, now);
  else if (w.kind === 'proj' && !w.auto) fireProj(id, now);
  else if (w.kind === 'cards') playCard(now);
  else if (w.kind === 'blood') fireBlood(now);
  else if (w.kind === 'beam') laserDown(now);
  else if (w.kind === 'zap' || w.kind === 'remote') secFireDown(id, now);
}

// ------------------------------------------------------------ Big Laser Pointer: hold to charge, let go to fire
// the server times the charge from the 'ch' we send on the press; ours is only for the looks (meter, whine, orb)
W.lz = { on: false, t: 0, k: 0, kick: 0 };
const LZ = WEAPONS.laser;
const lzK = (now) => Math.max(0, Math.min(1, ((now - W.lz.t) / 1000 - LZ.tap) / (LZ.charge - LZ.tap)));
function laserDown(now) {
  if (W.lz.on || beamOn(G.myId)) return;
  W.lz.on = true; W.lz.t = now;
  net.send({ t: 'fire', w: 'laser', ch: 1 });
  sfx.click();
}
function laserUp(now) {
  if (!W.lz.on) return;
  W.lz.on = false;
  chargeWhine(0);
  if (!ME.alive || W.cur !== 'laser') { net.send({ t: 'fire', w: 'laser', ch: 0 }); return; }
  const k = lzK(now), dur = LZ.dur[0] + (LZ.dur[1] - LZ.dur[0]) * k;
  W.cd.laser = now + (dur + LZ.cd) * 1000;
  net.send({ t: 'fire', w: 'laser', o: eye().map(r2), d: look().map(r2) });
  beamStart(G.myId, k, dur, () => (ME.alive && W.cur === 'laser' && models.laser.wrap.visible ? { o: muzzleWorld(), d: look() } : ME.alive ? { o: eye(), d: look() } : null));
  W.lz.kick = 0.25 + k * 0.4; W.lz.fireK = k;
  kickVM('laser', 0.25 + k * 0.55); W.kick = 0.2 + k * 0.3;
  punchCam(-0.02 - k * 0.05, 0.01 * rnd(), 0.025 * rnd() * k);
  if (k > 0.5) applyKb(look().map((x) => -x * k * 5)); // a full one shoves you back a bit
}
// every frame: the charge (slows you, whines, lights the meter), cancel it if you switched away or died
function laserTick(id, now, dt) {
  if (W.lz.on && (id !== 'laser' || !ME.alive)) { W.lz.on = false; chargeWhine(0); net.send({ t: 'fire', w: 'laser', ch: 0 }); }
  if (W.lz.on) { W.lz.k = lzK(now); ME.speedMul *= LZ.slow; chargeWhine(0.05 + W.lz.k * 0.95); } else W.lz.k = 0;
  W.lz.kick = Math.max(0, W.lz.kick - dt * 3);
}
function laserVM(m, now, pose) {
  const k = W.lz.on ? W.lz.k : 0, ud = m.g.userData;
  chargeLook(ud, k, W.lz.on, now);
  // the longer you hold it the harder it shakes, and you pull it in tight to your shoulder; firing kicks it up
  const sh = W.lz.on ? 0.0015 + k * k * 0.006 : beamOn(G.myId) ? 0.004 * (W.lz.fireK || 0) : 0;
  const pull = W.lz.on ? Math.min(1, (now - W.lz.t) / 250) : 0;
  pose((Math.random() - 0.5) * sh, (Math.random() - 0.5) * sh - 0.01 * pull, 0.03 * pull + W.lz.kick * 0.06, W.lz.kick * 0.25, 0, (Math.random() - 0.5) * sh * 3 + 0.04 * pull);
  if (ud.charm) { ud.charm.rotation.x = Math.sin(now * 0.004) * 0.25 - W.swayY * 4 + W.lz.kick * 1.2; ud.charm.rotation.z = Math.sin(now * 0.0031) * 0.2 + W.swayX * 3; }
}

export function fireUp() {
  W.held = false;
  if (rigFire(false)) return; // overdrive rig: let go to throw it
  if (W.lz.on) laserUp(performance.now());
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
    if (W.charge > WEAPONS.cig.maxCharge) { cough(); W.coughLock = false; return; } // let go in the TOO MUCH zone: you cough smoke instead of breathing fire
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
    case 'bloodpuff': { // Blood Cross inspect: blow the blood off your fingertip like smoke off a barrel
      const P = palOf(G.myId);
      if (g.userData.fingertip) g.userData.fingertip.getWorldPosition(evPos);
      sfx.blow();
      for (let i = 0; i < 14; i++) sys.norm.spawn(evPos.x + R(0.008), evPos.y + R(0.008), evPos.z + R(0.008), 0.06 + R(0.06), 0.05 + Math.random() * 0.06, -0.08 + R(0.06), 0.8, 0.006, 0.02, P.mist, P.dark, 0.45, -0.03, 1.5);
      for (let i = 0; i < 6; i++) sys.add.spawn(evPos.x, evPos.y, evPos.z, R(0.15), 0.06 + R(0.08), R(0.15), 0.3, 0.008, 0.001, P.glow, P.dark);
      break;
    }
    case 'blow': sfx.blow(); for (let i = 0; i < 6; i++) sys.norm.spawn(evPos.x + R(0.04), evPos.y, evPos.z + R(0.04), R(0.15), 0.1, R(0.15), 0.6, 0.02, 0.06, 0xdddddd, 0xffffff, 0.4); break;
    case 'smoke': for (let i = 0; i < 12; i++) sys.norm.spawn(evPos.x - 0.05 + R(0.05), evPos.y + 0.02, evPos.z - 0.1 + R(0.05), R(0.3), 0.15 + Math.random() * 0.2, -0.3 - Math.random() * 0.3, 1.4, 0.03, 0.2, 0xcccccc, 0x777777, 0.55, -0.1, 0.8); break;
    case 'spark': for (let i = 0; i < 10; i++) sys.add.spawn(evPos.x + R(0.03), evPos.y, evPos.z + R(0.03), R(0.8), 0.3 + Math.random() * 0.6, R(0.8), 0.5, 0.025, 0.005, 0xffcc44, 0xff3300, 1, 3); break;
    case 'spin': W.inspectSpin = 1.5; sfx.reload(); break;
    case 'startup': shredStartup(); break;
    case 'rev': sfx.rev(); break;
    case 'chains': sfx.chains(); break;
    default: if (!katanaEvent(ev, g, sys, sfx) && !reloadEvent(ev, g)) rifleEvent(ev, g, ejectShell);
  }
}

// ------------------------------------------------------------ shredder
// hold to suck: the heat climbs (overheats at w.fuel seconds) and only comes back down when you let go, like the
// blower's fuel. the client just reports who's in the cone; the server decides the pull and the shredding.
W.shred = { heat: 0, hot: false, hotK: 0, spin: 0, tick: 0, on: false, gore: 0, puff: 0 };
function updateShredder(dt, alive, now) {
  const w = WEAPONS.shredder, S = W.shred, mine = W.cur === 'shredder';
  // heat runs on real time like the server's (dt is capped at 0.1 s a frame, so under 10 fps it would fall behind)
  const rdt = S.at ? Math.min(0.3, Math.max(0, (now - S.at) / 1000)) : dt;
  S.at = now;
  if (S.life !== G.spawnT) { S.life = G.spawnT; S.heat = 0; S.hot = false; } // a new life starts cold (the server's too)
  const want = alive && mine && W.held && !S.hot;
  if (want) {
    S.heat += rdt;
    if (S.heat >= w.fuel) { S.hot = true; sfx.overheat(); hud.msg('OVERHEATED', 1.2); }
  } else {
    S.heat = Math.max(0, S.heat - w.regen * rdt);
    if (S.hot && S.heat <= w.fuel * w.coolTo) { S.hot = false; sfx.click(); }
  }
  S.on = want && !S.hot;
  S.spin = S.on ? Math.min(1, S.spin + dt / 0.35) : Math.max(0, S.spin - dt / 0.9); // teeth spin up / wind down
  shredMotor(mine ? S.spin : 0);
  if (!S.on) return;
  const m = models.shredder, o = eye(), d = look();
  fx.vacuum(vmToWorld(m, m.g.userData.muzzle, 2.2), d, ME.vel, w.range, w.cone, S.spin, dt);
  S.tick -= dt;
  if (S.tick <= 0) {
    S.tick = w.tick;
    for (const tg of conePlayers(o, d, w.range, w.cone)) net.send({ t: 'push', to: tg.r.id, w: 'shredder' });
  }
}
// the viewmodel is drawn over the world by its own camera (65°, yours is wider), so a world effect aimed at the gun has
// to go through the screen: gun-local point v -> the world point dist from your eye that lands on the same pixel
const tmpV3 = new THREE.Vector3(), tmpV4 = new THREE.Vector3(), tmpV5 = new THREE.Vector3();
function vmToWorld(m, v, dist) {
  m.wrap.updateMatrixWorld(true);
  G.camera.updateMatrixWorld();
  tmpV3.copy(v); m.g.localToWorld(tmpV3);
  tmpV3.project(G.vmCamera).setZ(0.5).unproject(G.camera);
  tmpV4.setFromMatrixPosition(G.camera.matrixWorld);
  tmpV3.sub(tmpV4).normalize().multiplyScalar(dist).add(tmpV4);
  return [tmpV3.x, tmpV3.y, tmpV3.z];
}
// gun-local point v (and direction dir) in viewmodel space, for particles that live with the gun
function vmPoint(m, v, out = tmpV) { out.copy(v); return m.g.localToWorld(out); }
function vmDir(m, v, dir, out = tmpV2) { out.copy(v).add(dir); m.g.localToWorld(out); return out.sub(vmPoint(m, v, tmpV5)).normalize(); }
const AIR = [0xf4fbff, 0xe2edf5], LEAF = [0x4caf50, 0x8bc34a, 0xff9800, 0xc0602a, 0xffd54f];
// stuff spiralling from the rim down into the teeth (each one aimed at the throat a bit round from where it started)
function throat(m, dt, rate, colors, end, size, alpha) {
  const sys = G.skinFxVM && G.skinFxVM.norm, ud = m.g.userData;
  if (!sys) return;
  for (let i = 0, n = Math.floor(dt * rate + Math.random()); i < n; i++) {
    const a = Math.random() * Math.PI * 2, r = ud.mouthR * (0.45 + Math.random() * 0.5), life = 0.09 + Math.random() * 0.09;
    const p = vmPoint(m, tmpV.set(Math.cos(a) * r, ud.axisY + Math.sin(a) * r, ud.muzzle.z + 0.012));
    const q = vmPoint(m, tmpV2.set(Math.cos(a + 1.5) * 0.035, ud.axisY + Math.sin(a + 1.5) * 0.035, ud.throatZ), tmpV2);
    sys.spawn(p.x, p.y, p.z, (q.x - p.x) / life, (q.y - p.y) / life, (q.z - p.z) / life, life, size * (0.7 + Math.random() * 0.6), size * 0.25,
      colors[(Math.random() * colors.length) | 0], end, alpha, 0, 0);
  }
}
// a burst out of the chute: n bits, blood / confetti / smoke = the share of each
function chuteVM(m, n, blood, confetti, smoke) {
  const sys = G.skinFxVM, ud = m.g.userData;
  if (!sys) return;
  const d = vmDir(m, ud.chute, ud.chuteDir), c = vmPoint(m, ud.chute, tmpV4);
  const R = (k) => (Math.random() - 0.5) * k;
  for (let i = 0; i < n; i++) {
    const kind = Math.random(), sp = 0.5 + Math.random() * 0.9;
    if (kind < smoke) sys.norm.spawn(c.x, c.y, c.z, d.x * sp * 0.4 + R(0.1), d.y * sp * 0.4 + 0.1 + R(0.1), d.z * sp * 0.4 + R(0.1), 0.5 + Math.random() * 0.3, 0.012, 0.03, 0x5a5a5a, 0x2a2a2a, 0.55, -0.15, 1.5);
    else if (kind < smoke + blood) sys.norm.spawn(c.x, c.y, c.z, d.x * sp + R(0.25), d.y * sp + R(0.25), d.z * sp + R(0.25), 0.45 + Math.random() * 0.3, 0.008 + Math.random() * 0.008, 0.005, Math.random() < 0.3 ? 0xd01010 : 0x8a0000, 0x3a0000, 1, 2.2, 0.4);
    else if (kind < smoke + blood + confetti) sys.norm.spawn(c.x, c.y, c.z, d.x * sp + R(0.35), d.y * sp + R(0.35), d.z * sp + R(0.35), 0.7 + Math.random() * 0.4, 0.008, 0.008, [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff7a1a][(Math.random() * 5) | 0], 0xffffff, 1, 1.2, 1.4);
  }
}
// viewmodel: a lean into the pull + a shake while it runs, the teeth (spinTeeth: never seem to run backwards, blur
// at speed), lamps + heat gauge, air spiralling down the throat, blood when it's chewing,
// smoke when the motor starts, a droop + steam when it's overheated
function shredderVM(m, dt, now, pose) {
  const S = W.shred, ud = m.g.userData, R = (k) => (Math.random() - 0.5) * k;
  S.hotK += ((S.hot ? 1 : 0) - S.hotK) * Math.min(1, dt * 5);
  const j = 0.011 * S.spin + (S.gore > 0 ? 0.008 : 0);
  pose(R(j), R(j) - 0.035 * S.hotK, -0.014 * S.spin, R(j * 2) - 0.24 * S.hotK, 0, R(j * 3) + 0.14 * S.hotK);
  spinTeeth(m.g, dt, S.spin + W.inspectSpin * 0.45);
  const lit = S.hot ? (now % 300 < 150 ? 0xff2020 : 0x300000) : S.spin > 0.05 ? 0xff3a2a : 0x500000;
  if (ud.lamps) for (const l of ud.lamps) l.material.color.setHex(lit);
  const heat = Math.min(1, S.heat / WEAPONS.shredder.fuel), glow = Math.max(0, (heat - 0.45) / 0.55);
  if (ud.heatNeedle) ud.heatNeedle.rotation.y = 2.3 - 4.6 * heat + R(0.12) * S.spin;
  heatTeeth(m.g, glow); // the teeth going red-hot
  S.gore = Math.max(0, S.gore - dt); S.puff = Math.max(0, S.puff - dt);
  if (!m.wrap.visible) return;
  if (S.on) throat(m, dt, 130 * S.spin, Math.random() < 0.2 ? LEAF : AIR, 0xc8d8e0, 0.009, 0.55);
  if (S.gore > 0) { throat(m, dt, 90, [0xd01010, 0x8a0000], 0x3a0000, 0.011, 1); if (Math.random() < dt * 14) chuteVM(m, 2, 0.8, 0.2, 0); }
  if (S.puff > 0) chuteVM(m, Math.floor(dt * 50 + Math.random()), 0, 0, 1);
  if (S.hot && G.skinFxVM && Math.random() < dt * 30) { // steam off the chute
    const c = vmPoint(m, ud.chute);
    G.skinFxVM.norm.spawn(c.x + R(0.01), c.y, c.z + R(0.01), R(0.03), 0.07 + Math.random() * 0.06, R(0.03), 0.6, 0.004, 0.012, 0xf0f0f0, 0xb0b0b0, 0.35, -0.04, 1.2);
  }
}
// the draw: the motor catches (teeth jump, a puff of smoke out of the chute)
function shredStartup() { W.inspectSpin = Math.max(W.inspectSpin, 1.3); W.shred.puff = 0.3; sfx.startup(); }
// you're chewing someone: thump the gun, blood down the throat and out of the chute
export function shredKick() { if (W.cur !== 'shredder') return; kickVM('shredder', 0.3); W.kick = Math.min(1, W.kick + 0.12); W.shred.gore = 0.22; }
// a chunk just came out of my chute (kills): spray it in first person too
export function shredSpitVM(big) { const m = models.shredder; if (m && W.cur === 'shredder') { chuteVM(m, big ? 40 : 6, 0.6, big ? 0.4 : 0.15, 0); kickVM('shredder', big ? 0.6 : 0.15); } }
// where my shredder's intake + chute are in the world, and which way to spit (shredder.js aims gibs at them): points
// that land on the gun on screen, the spit thrown up and out in front of you so you see it arc over the gun
export function shredderPorts() {
  const m = models.shredder;
  if (!m || W.cur !== 'shredder' || !m.wrap.visible) return null;
  const ud = m.g.userData;
  const intake = vmToWorld(m, ud.muzzle, 3), chute = vmToWorld(m, ud.chute, 2.6); // (pieces go in a bit deeper than the dust: smaller on screen)
  const tip = vmToWorld(m, tmpV5.copy(ud.chute).addScaledVector(ud.chuteDir, 0.25), 2.6), lk = look();
  const sd = [tip[0] - chute[0], tip[1] - chute[1], tip[2] - chute[2]], sl = Math.hypot(...sd) || 1;
  const d = [sd[0] / sl * 0.25 + lk[0] * 0.6, sd[1] / sl * 0.25 + 0.8 + lk[1] * 0.6, sd[2] / sl * 0.25 + lk[2] * 0.6], l = Math.hypot(...d);
  return { intake, chute, dir: d.map((x) => x / l), vel: ME.vel, mine: true };
}

export function updateWeapons(dt, now) {
  if (ME.alive && now < (ME.ballUntil || 0)) { W.held = false; W.aimHeld = false; W.dashHeld = false; W.exhale = 0; W.charge = 0; } // wrecking ball: no hands
  const id = W.cur, w = WEAPONS[id];
  if (rigVM(dt, now, vmRoot)) return; // overdrive rig: guns holstered, mechanical fists instead (rig.js)
  const alive = ME.alive;
  let smoking = false, firing = false, blowing = false, spinning = false;

  W.fuel.blower = (W.held && id === 'blower') ? W.fuel.blower : Math.min(WEAPONS.blower.fuel, W.fuel.blower + WEAPONS.blower.regen * dt);
  W.bloom = Math.max(0, W.bloom - dt * 0.06);
  if (W.slipperOut && now - W.slipperT > 4000) W.slipperOut = false;
  if (W.reloadId && now >= W.reloadUntil) { if (W.br) W.br.reloaded(W.reloadId); else if (W.eco) W.eco.reloaded(W.reloadId); else W.ammo[W.reloadId] = WEAPONS[W.reloadId].mag; W.reloadId = null; sfx.click(); }
  const canAim = !!w.ads && alive && !W.reloadId;
  W.aim = canAim && W.aimHeld ? Math.min(1, W.aim + dt * 7 * (w.adsSpeed || 1)) : Math.max(0, W.aim - dt * 8);
  W.zoom = w.ads ? 1 + (w.ads.zoom - 1) * W.aim : 1;
  const wasScoped = W.scoped;
  W.scoped = !!(w.ads && w.ads.scope && W.aim > 0.92);
  if (W.scoped && !wasScoped) W.scopedAt = now; // quick-scopes count from the moment the scope is fully up
  hud.scope(W.scoped);
  ME.speedMul = (w.speedMul || 1) * (1 - W.aim * 0.25);
  parryTick(now); // katana parry: buffered presses, stagger, cooldown ring
  laserTick(id, now, dt); // laser pointer charge

  if (alive && w.hands) akimboFrame(id, now); // Lefty & Righty: a trigger per hand
  else if (alive && w.kind === 'hitscan') {
    if (w.spinup) {
      W.spin = W.held && !W.reloadId ? Math.min(1, W.spin + dt / w.spinup) : Math.max(0, W.spin - dt / (w.spinup * 1.5));
      spinning = W.spin > 0;
    }
    if ((W.held || bursting(w)) && (w.auto || w.spinup) && !W.reloadId && (!w.spinup || W.spin >= 1)) {
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
  updateShredder(dt, alive, now);

  revolverFrame(id, w, now);
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
  if (W.cycle) { W.cycle.t -= dt; if (W.cycle.t <= 0) { if (W.cycle.name && id === (W.cycle.name === 'pump_shotgun' ? 'shotgun' : id) && !(W.reloadId && W.anim && W.anim.kind === 'reload')) playAnim(W.cycle.name, 'cycle'); W.cycle = null; } }
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
  if (W.shred.on) W.flags |= FLAGS.SUCK;
  if (W.lz.on) W.flags |= FLAGS.CHARGE; // everyone sees your pointer charging
  if (W.nvOnFlag) W.flags |= FLAGS.NV; // night vision goggles down (goggles.js)

  // ---- HUD
  if (ITEMS[W.item]) { const c = charges(W.item), it = ITEMS[W.item]; hud.item(c.n, it.charges, c.next ? 1 - Math.max(0, c.next - now) / (it.recharge * 1000) : 1); }
  updatePop(dt);
  tacFrame(dt, now, W.eco && W.cur && WEAPONS[W.cur] ? W.cur : null, W.cur && WEAPONS[W.cur] ? tacBase(WEAPONS[W.cur]) : 0); // the crosshair shows your spread
  if (W.br) W.br.hud(id, !!W.reloadId); // jank royale: mag / spare bullets
  else if (W.eco) W.eco.hud(id, !!W.reloadId);
  else if (w.hands) hud.ammo2(W.ak.L.n, W.ak.R.n, AK_HM, !!W.ak.L.rl, !!W.ak.R.rl);
  else if (w.mag) hud.ammo(W.ammo[id], w.mag, !!W.reloadId);
  else hud.ammo(null);
  if (w.hands && (W.ak.L.rl || W.ak.R.rl)) { const h = W.ak.L.rl && (!W.ak.R.rl || W.ak.L.rl < W.ak.R.rl) ? 'L' : 'R'; hud.meter(1 - (W.ak[h].rl - now) / (w.reload * 1000), h === 'L' ? 'LEFTY RELOADING' : 'RIGHTY RELOADING', w.color); }
  else if (W.reloadId) hud.meter(1 - (W.reloadUntil - now) / (w.reload * 1000), 'RELOADING', '#ffffff');
  else if (isScythe(id)) hud.meter(W.dashFuel / D.max, ME.dashing ? 'GLITCHING' : `${K.label('dash').toUpperCase()}: GLITCH DASH · ${K.label('scythe').toUpperCase()}: SWAP MODE`, '#ff00dc');
  else if (id === 'bow') { /* set above */ }
  else if (id === 'cards') hud.meter(null);
  else if (id === 'cig') {
    if (W.exhale <= 0 && W.charge <= 0) hud.meter(null);
    else hud.meter(W.exhale > 0 ? W.exhale / (w.maxCharge * w.exhaleMul) : W.charge / w.maxCharge,
      W.exhale > 0 ? 'EXHALING' : W.charge > w.maxCharge ? 'TOO MUCH' : 'INHALE', W.charge > w.maxCharge ? '#ff3030' : '#ff9a3a');
  } else if (id === 'blower') hud.meter(W.fuel.blower / w.fuel, 'FUEL', '#ff9a3a');
  else if (w.spinup && W.spin > 0 && W.spin < 1) hud.meter(W.spin, 'SPINNING UP', '#c8c8c8');
  else if (id === 'slipper' && W.slipperOut) hud.meter(null);
  else if (id === 'bloodcross') { const n = Math.max(0, Math.floor((ME.hp - 1) / w.cost)); hud.meter((ME.hp - 1) / 99, n ? `${n} SHOT${n > 1 ? 'S' : ''} OF BLOOD LEFT` : 'NOT ENOUGH BLOOD', w.color); }
  else if (w.cd && w.cd >= 1 && !ready(id, now)) hud.meter(1 - ((W.cd[id] - now) / 1000) / w.cd, 'COOLDOWN', w.color);
  else hud.meter(null);
  if (id === 'shredder') { const S = W.shred, f = S.heat / w.fuel; hud.meter(f, S.hot ? 'OVERHEATED · COOLING' : 'HEAT', S.hot ? '#ff3030' : f > 0.7 ? '#ff7a1a' : '#ffb31a'); }
  if (id === 'laser') {
    if (W.lz.on) hud.meter(Math.max(0.03, W.lz.k), W.lz.k >= 1 ? 'FULLY CHARGED · LET GO' : (now - W.lz.t) / 1000 < LZ.tap ? 'TAP = LITTLE ZAP' : 'CHARGING', W.lz.k >= 1 ? '#ffffff' : w.color);
    else if (!ready(id, now)) hud.meter(null);
  }

  // ---- viewmodel animation
  const m = models[id];
  const cfg = m.cfg;
  const hs = hspeed();
  const vb = vmBob(dt, now, hs); W.bob = vb.ph; // footstep bob by gait + the marbles stumble (vmbob.js). (lasso.js reads W.bob)
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
  let px = cfg.p[0] + vb.x + W.swayX * 0.2 + Math.sin(breathe * 1.3) * 0.0025,
    py = cfg.p[1] + vb.y - W.swap * 0.3 - W.swayY * 0.12 + Math.sin(breathe * 2.1) * 0.0018 - W.runK * 0.03,
    pz = cfg.p[2];
  let rx = cfg.r[0] + vb.rx - W.swayY * 0.8 - W.runK * 0.25,
    ry = cfg.r[1] + W.swayX * 1.3 + W.runK * 0.35,
    rz = cfg.r[2] + vb.rz + Math.sin(breathe * 1.1) * 0.008 + W.swayX * 0.6 + W.runK * 0.2 + (ME.sliding ? 0.3 : 0);
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
  if (!W.reloadId && W.anim && W.anim.kind === 'reload') W.anim = null; // (cancelled: respawn, a refill, a mode reset)
  if (W.reloadId && !(W.anim && W.anim.kind === 'reload')) { const k = Math.sin(Math.min(1, 1 - (W.reloadUntil - now) / (w.reload * 1000)) * Math.PI); py -= k * 0.12; rx -= k * 0.6; rz += k * 0.4; }
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
  { const sw = !W.anim && W.aim < 0.05 && bladeIdle(id, now, 1 - W.runK); if (sw) { px += sw[0]; py += sw[1]; pz += sw[2]; rx += sw[3]; ry += sw[4]; rz += sw[5]; } } // blades sway a little at rest
  // keyframed animation on top of everything (swings, throws, inspects)
  let scale = 1;
  const adt = W.hitStop > 0 ? 0 : dt; // hit stop freezes the swing for a moment
  W.hitStop = Math.max(0, W.hitStop - dt);
  let trailOn = false;
  if (W.anim) {
    const t0 = W.anim.t;
    W.anim.t += adt;
    if (W.anim.kind === 'reload' && W.reloadId === id && w.reload) W.anim.t = Math.max(t0, w.reload - (W.reloadUntil - now) / 1000); // on the reload's own clock: it ends on the frame the ammo comes back, at any frame rate
    for (const ev of eventsBetween(W.anim.name, t0, W.anim.t)) { animEvent(ev, m.g); if (SIDEARMS.has(id)) { sideEvent(ev, m, id); if (m.left) sideEvent(ev, m.left, id); } }
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
  if (ud.handles) balisongStep(m, an, at, sampleCh); // butterfly: the blade + free handle swing round the pivot, the held one stays put
  if (ud.index) { // Blood Cross: the finger flicks, the thumb drops like a hammer, the fist opens + closes, the fingertip beats
    const f = an && sampleCh(an, 'index', at), t = an && sampleCh(an, 'thumb', at), c = an && sampleCh(an, 'curl', at);
    ud.index.rotation.x = f ? f[0] : 0; ud.thumb.rotation.x = t ? t[0] : 0;
    for (const b of ud.curl) b.j.quaternion.copy(b.q).multiply(bcQ.setFromAxisAngle(bcY, -b.a * (c ? c[0] : 0)));
    const beat = (now % 1100) / 1100, lub = Math.exp(-Math.pow((beat - 0.1) / 0.04, 2)) + 0.6 * Math.exp(-Math.pow((beat - 0.32) / 0.04, 2));
    ud.fingertip.scale.setScalar(1 + lub * 0.45 + W.kick * 1.6);
    ud.flare.visible = W.flashT > 0 && m.wrap.visible;
    if (ud.flare.visible) { ud.flare.userData.face.rotation.z = Math.random() * 6.28; ud.flare.scale.setScalar((0.7 + Math.random() * 0.5) / (1 + W.kick * 1.6)); }
  }
  if (ud.flipBlade) { const b = an && sampleCh(an, 'blade', at); ud.flipBlade.rotation.x = b ? b[0] : 0; }
  if (ud.pivot) {
    const sp = an && sampleCh(an, 'spin', at), a = sp ? sp[0] : 0, pz = ud.pivot.z * cfg.s;
    m.g.rotation.x = a;
    m.g.position.set(0, Math.sin(a) * pz, pz - Math.cos(a) * pz);
  }
  if (id === 'knife' || id === 'katana') bladeStep(m, an, at, sampleCh); // the knife leaves the hand on a toss (the hand stays), the fingers let go
  if (w.fanHammer) { const k = twirlVM(m, dt); px -= k * 0.025; py -= k * 0.02; pz -= k * 0.1; ry += k * 0.4; rz -= k * 0.15; } // arm out + wrist turned so you see it go round (the barrel never swings through your face)
  if (W.inspectSpin > 0) { W.inspectSpin = Math.max(0, W.inspectSpin - dt * 0.8); if (m.g.userData.barrels) m.g.userData.barrels.rotation.z += W.inspectSpin * dt * 30; }
  m.wrap.scale.setScalar(scale);
  if (m.g.userData.barrels) m.g.userData.barrels.rotation.z += W.spin * dt * 40;
  stepParts(m.g, dt, an, at); // Blender guns: rack the pump, settle the cylinder + hammer, cycle the bolt
  if (RIFLES.has(id)) rifleStep(id, m, dt, now, W); // mags, charging handles, the lever, the belt, the hot barrel
  if (SIDEARMS.has(id)) { // slide / knob / hammers / mag / hinge / shells, and the off hand that reloads them
    const st = { empty: id === 'pistol' && (W.ammo.pistol || 0) <= 0 && G.mode !== 'training', fired: (w.mag || 0) - (W.ammo[id] ?? w.mag) };
    if (!(w.hands && W.ak.R.rl)) sideStep(m.g, id, dt, an, at, st, sampleCh);
    if (m.left && !W.ak.L.rl) sideStep(m.left.g, id, dt, an, at, st, sampleCh);
    stepOffHand(m, id, an, at, sampleCh);
  }
  reloadStep(m, id, an, at, sampleCh, W); // mag / bolt / cylinder / pump + the off hand and its props (reloads.js)
  if (blowing || (spinning && W.spin >= 1 && W.held)) { px += (Math.random() - 0.5) * 0.008; py += (Math.random() - 0.5) * 0.008; }
  if (id === 'shredder') shredderVM(m, dt, now, (a, b, c, d, e, f) => { px += a; py += b; pz += c; rx += d; ry += e; rz += f; });
  if (id === 'laser') laserVM(m, now, (a, b, c, d, e, f) => { px += a; py += b; pz += c; rx += d; ry += e; rz += f; });
  m.wrap.visible = !(id === 'slipper' && W.slipperOut) && !W.scoped && !ME.dashing;
  if (w.hands) { // Lefty & Righty: each gun's own recoil + reload, the left one mirrored
    const P = { px, py, pz, rx, ry, rz };
    akimboVM(m, dt, now, P, { x: W.swayX * 0.2, ry: W.swayX * 1.3, rz: W.swayX * 0.6 });
    ({ px, py, pz, rx, ry, rz } = P);
  }
  m.wrap.position.set(px, py, pz);
  m.wrap.rotation.set(rx, ry, rz);
  if (m.kh) { const kl = an && sampleCh(an, 'kl', at); katanaStep(m, kl ? kl[0] : 1); } // katana: the left hand on the grip (or off it)
  if (models.akimbo && models.akimbo.left) { const L = models.akimbo.left; L.wrap.visible = id === 'akimbo' && !ME.dashing; L.flash.visible = L.wrap.visible && W.ak.L.flash > 0; if (L.flash.visible) { L.flash.userData.face.rotation.z = Math.random() * 6.28; L.flash.scale.setScalar(0.8 + Math.random() * 0.6); } }
  if (ud.court) tickScalesVM(m.g, dt, now); // scales of justice: tip toward the verdict, swing the pans
  if (m.g.userData.hat) m.g.userData.hat.visible = W.aim < 0.3 && !(ud.sp && ud.sp.openK > 0.05); // Half a Shotgun broken open: the breech goes through the hat
  hud.crossFade(m.g.userData.sight ? Math.max(0, 1 - W.aim * 1.6) : 1);
  // muzzle flash
  W.flashT = Math.max(0, W.flashT - dt);
  for (const k of ORDER) { const mm = models[k]; if (mm && mm.flash) mm.flash.visible = k === id && W.flashT > 0 && m.wrap.visible; }
  if (w.hands && m.flash) m.flash.visible = W.ak.R.flash > 0 && m.wrap.visible; // the right gun's own flash
  if (m.flash && m.flash.visible) { m.flash.userData.face.rotation.z = Math.random() * 6.28; m.flash.scale.setScalar(0.8 + Math.random() * 0.6); }
  updateTrail(now, m, trailOn && m.wrap.visible, TRAIL_COLOR[id] || 0xffffff, TRAIL_LIFE[id]);
  if (m.wrap.visible && G.skinFxVM) { m.wrap.updateMatrixWorld(true); emitSkinFx(G.skinFxVM, m.g, dt, 0.3 * cfg.s); }
}
