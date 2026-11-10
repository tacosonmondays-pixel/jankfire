// Zombies on the client: the mall's roller shutters, chalk wall guns, the mystery crate, the power switch and the cola
// machine; the credits HUD with +N popups and the hand-drawn round tally; what F does when you look at something;
// your limited ammo; downed friends to pick up; zombie mannequins that shamble and groan. The server runs the mode.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { ME, eye, look } from './player.js';
import { W, switchSlot, showSlots, modeFriends } from './weapons.js';
modeFriends.push((r) => !!(G.round && G.round.zm) && !(r.bot && !r.team)); // zombies: people and the squad's bots (team 1) are on your side; zombies have no team
import { MAPS, BOXES } from '/shared/map.js';
import { resetGrid } from '/shared/physics.js';
import { WEAPONS, FLAGS } from '/shared/weapons.js';
import { GAMES } from '/shared/modes.js';
import { ZM, ZM_CRATE, zmTarget, zmAmmo, zmAmmoPrice, zmAreaAt, zmOpenAreas } from '/shared/zombies.js';
import { buildWeapon, M } from './models.js';
import { weaponIcon, drawIcon } from './icons.js';
import { whenGlb } from './glbkit.js';
import { K } from './keys.js';
import { zxSetup, zxTick, zxTarget, zxPrompt, zxMeter, zxPrice, zxOff } from './zmextra.js'; // boards, drops, the cheat machine
const UK = () => K.label('use').toUpperCase(); // the buy / revive key (keys.js 'use', F by default)

const $ = (id) => document.getElementById(id);
const FONT = '"Comic Sans MS", "Comic Neue", cursive';
const SHAMBLER = '#8fd14f';
const Z = {
  on: false, map: null, mapId: '', group: null, doors: [], solid: new Set(), crate: null, power: null, cola: null,
  res: {}, prev: {}, guns: [], melee: '', credits: 0, cola2: false, target: null, useT: 0, useK: '', wasUsing: false, msgT: 0,
  tally: -1, lights: null, lit: '', lampMat: null, flickMat: null, groanT: 0, marks: new Map(), weapons: new Map(), cfgGame: null, racks: [],
};
export const isZombie = (r) => !!(r && r.bot && r.name === 'Zombie');

// ------------------------------------------------------------ HUD (built once, shown while zombies is on)
const mk = (tag, id, parent, cls) => { const e = document.createElement(tag); if (id) e.id = id; if (cls) e.className = cls; parent.append(e); return e; };
const root = mk('div', 'zmHud', $('hud'), 'hidden');
const tallyCv = mk('canvas', 'zmTally', root); tallyCv.width = 240; tallyCv.height = 120;
const cred = mk('div', 'zmCred', root);
mk('small', null, cred).textContent = 'CREDITS';
const credN = mk('b', 'zmCredN', cred);
const pops = mk('div', 'zmPops', cred);
const team = mk('div', 'zmTeam', root);
const prompt = mk('div', 'zmPrompt', root);
const banner = mk('div', 'zmBanner', root);

// the round counter: tally marks in red chalk (groups of five) up to 10, scrawled numbers after that
function drawTally(n) {
  const x = tallyCv.getContext('2d'), w = tallyCv.width, h = tallyCv.height;
  x.clearRect(0, 0, w, h);
  if (n <= 0) return;
  let seed = n * 977 + 13;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
  const j = (k = 1) => (rnd() - 0.5) * 6 * k;
  if (n > 10) {
    x.font = `bold 100px ${FONT}`; x.textBaseline = 'middle';
    x.fillStyle = 'rgba(0,0,0,0.65)'; x.fillText(String(n), 18, 68);
    for (let k = 0; k < 4; k++) { x.fillStyle = k < 2 ? '#7a0a10' : '#c8141e'; x.fillText(String(n), 12 + j(0.6), 62 + j(0.6)); }
    return;
  }
  const marks = [];
  for (let g = 0; g * 5 < n; g++) {
    const k = Math.min(5, n - g * 5), ox = 18 + g * 112;
    for (let i = 0; i < Math.min(4, k); i++) marks.push([ox + i * 20 + j(), 16 + j(), ox + i * 20 + 5 + j(), 104 + j()]);
    if (k === 5) marks.push([ox - 12 + j(), 86 + j(), ox + 76 + j(), 28 + j()]);
  }
  for (const [color, lw, off] of [['rgba(0,0,0,0.6)', 12, 4], ['#6a0810', 11, 0], ['#d0161f', 5, -1]]) {
    x.strokeStyle = color; x.lineWidth = lw; x.lineCap = 'round';
    for (const [a, b, c, d] of marks) { x.beginPath(); x.moveTo(a + off, b + off); x.quadraticCurveTo((a + c) / 2 + j(1.2) + off, (b + d) / 2 + j(1.2) + off, c + off, d + off); x.stroke(); }
  }
}
let hitPop = null;
function popup(d, why) {
  if (!d) return;
  const now = performance.now();
  if (why === 'hit' && hitPop && now - hitPop.t < 350) { hitPop.n += d; hitPop.el.textContent = `+${hitPop.n}`; return; } // a burst of hits = one popup
  const e = mk('div', null, pops, 'zpop' + (d < 0 ? ' neg' : why === 'head' || why === 'melee' ? ' big' : ''));
  hitPop = why === 'hit' ? { el: e, n: d, t: now } : null;
  e.textContent = d > 0 ? `+${d}${why === 'head' ? ' HEADSHOT' : why === 'melee' ? ' MELEE' : ''}` : String(d);
  e.style.right = `${Math.random() * 40}px`;
  setTimeout(() => e.remove(), 1100);
}
function showBanner(text, sub, cls) {
  banner.innerHTML = '';
  mk('b', null, banner).textContent = text;
  if (sub) mk('small', null, banner).textContent = sub;
  banner.className = ''; void banner.offsetWidth; banner.className = 'on ' + (cls || '');
}
const fmt = (c) => Math.round(c).toLocaleString('en-US');

// ------------------------------------------------------------ the map's extras (built when the zombies map loads)
function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  return { t, c };
}
// a roller shutter with the area's name and price spray-painted on
function shutterTex(name, price) {
  return canvasTex(256, 192, (x, w, h) => {
    x.fillStyle = '#5a5e64'; x.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += 12) { x.fillStyle = '#6c7076'; x.fillRect(0, y, w, 7); x.fillStyle = '#3a3d42'; x.fillRect(0, y + 9, w, 2); }
    for (let i = 0; i < 90; i++) { x.fillStyle = `rgba(${130 + Math.random() * 50},${60 + Math.random() * 30},20,${0.12 + Math.random() * 0.25})`; x.fillRect(Math.random() * w, Math.random() * h, 3 + Math.random() * 16, 2 + Math.random() * 7); }
    x.fillStyle = 'rgba(12,8,14,0.8)'; x.fillRect(16, 44, w - 32, 104);
    x.strokeStyle = '#ffe14d'; x.lineWidth = 4; x.strokeRect(16, 44, w - 32, 104);
    x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillStyle = '#ffffff'; x.font = `bold 25px ${FONT}`; x.fillText(name.toUpperCase(), w / 2, 72);
    x.fillStyle = '#ffe14d'; x.font = `bold 46px ${FONT}`; x.fillText(String(price), w / 2, 118);
  }).t;
}
// wall gun: a chalkboard with the gun's outline (traced from its hotbar picture), its name and its price
function drawBoard(x, w, h, b, img) {
  x.fillStyle = '#4a3420'; x.fillRect(0, 0, w, h);
  x.fillStyle = '#1c2a22'; x.fillRect(8, 8, w - 16, h - 16);
  for (let i = 0; i < 50; i++) { x.fillStyle = `rgba(255,255,255,${Math.random() * 0.05})`; x.fillRect(8 + Math.random() * (w - 24), 8 + Math.random() * (h - 20), 10 + Math.random() * 30, 2 + Math.random() * 6); }
  if (img) {
    const o = document.createElement('canvas'); o.width = 200; o.height = 120;
    const ox = o.getContext('2d');
    ox.drawImage(img, 0, 0, 200, 120);
    ox.globalCompositeOperation = 'source-in'; ox.fillStyle = '#f4f0dc'; ox.fillRect(0, 0, 200, 120);
    const s = document.createElement('canvas'); s.width = 200; s.height = 120;
    const sx = s.getContext('2d');
    for (const [dx, dy] of [[-3, 0], [3, 0], [0, -3], [0, 3], [-2, -2], [2, 2], [-2, 2], [2, -2]]) sx.drawImage(o, dx, dy);
    sx.globalCompositeOperation = 'destination-out'; sx.drawImage(o, 0, 0);
    x.globalAlpha = 0.16; x.drawImage(img, 28, 14, 200, 120); x.globalAlpha = 1;
    x.drawImage(s, 28, 14);
  }
  x.fillStyle = '#f4f0dc'; x.font = `bold 20px ${FONT}`; x.textAlign = 'left'; x.textBaseline = 'top';
  x.fillText(WEAPONS[b.w].name.toUpperCase(), 16, 12);
  x.textAlign = 'right'; x.textBaseline = 'bottom'; x.fillStyle = '#ffe14d'; x.font = `bold 28px ${FONT}`;
  x.fillText(String(b.price), w - 16, h - 8);
}
function buyBoard(b) {
  const { t, c } = canvasTex(256, 144, (x, w, h) => drawBoard(x, w, h, b, null));
  const img = new Image();
  img.onload = () => { drawBoard(c.getContext('2d'), c.width, c.height, b, img); t.needsUpdate = true; };
  const [u, wait] = drawIcon(() => weaponIcon(b.w));
  img.src = u;
  if (wait) whenGlb(wait, () => { img.src = weaponIcon(b.w); }); // the chalk outline was the loading cube: redraw it with the real gun
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 0.96), new THREE.MeshBasicMaterial({ map: t, color: 0xd8d8d8 })); // unlit: readable in the dark
  m.position.set(b.at[0] + b.n[0] * 0.03, b.at[1], b.at[2] + b.n[2] * 0.03);
  m.rotation.y = Math.atan2(b.n[0], b.n[2]);
  const rack = new THREE.Group(); rack.position.set(0, -0.06, 0.1); m.add(rack); // the real gun hangs on the board, over its chalk outline
  Z.racks.push({ rack, w: b.w });
  mountGun(rack, b.w);
  return m;
}
// the gun itself (the Blender model once it has loaded, the code model till then), side-on, about a metre long
function mountGun(rack, w) {
  for (const c of [...rack.children]) rack.remove(c);
  if (!WEAPONS[w]) return;
  const g = buildWeapon(w), bb = new THREE.Box3(), sz = new THREE.Vector3(), mid = new THREE.Vector3();
  g.rotation.y = -Math.PI / 2; g.updateMatrixWorld(true); bb.setFromObject(g); bb.getSize(sz); bb.getCenter(mid);
  const k = Math.min(4, 1.15 / Math.max(0.05, sz.x), 0.62 / Math.max(0.05, sz.y));
  g.scale.multiplyScalar(k); g.position.copy(mid).multiplyScalar(-k); g.position.z += 0.02;
  rack.add(g);
}
export function zmModelsLoaded() { for (const r of Z.racks) mountGun(r.rack, r.w); Z.weapons.clear(); } // the Blender guns arrived after the map was built
const onWall = (g, at, n, out = 0) => { g.position.set(at[0] + n[0] * out, at[1], at[2] + n[2] * out); g.rotation.y = Math.atan2(n[0], n[2]); return g; }; // local +z = out of the wall
function buildCrate(cr, group) {
  const g = new THREE.Group(); g.position.set(cr.at[0], 0, cr.at[2]);
  const q = canvasTex(160, 64, (x, w, h) => {
    x.clearRect(0, 0, w, h);
    x.font = `bold 52px ${FONT}`; x.textAlign = 'center'; x.textBaseline = 'middle';
    for (const [cx, r] of [[30, -0.2], [80, 0.1], [130, 0.25]]) { x.save(); x.translate(cx, 34); x.rotate(r); x.fillStyle = '#000'; x.fillText('?', 3, 3); x.fillStyle = '#7fe8ff'; x.fillText('?', 0, 0); x.restore(); }
  }).t;
  const front = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.64), new THREE.MeshBasicMaterial({ map: q, transparent: true }));
  front.position.set(0, 0.47, 0.465); g.add(front);
  const lid = new THREE.Group(); lid.position.set(0, 0.9, -0.45);
  const lm = new THREE.Mesh(new THREE.BoxGeometry(1.86, 0.12, 0.96), M(0x6a4422)); lm.position.set(0, 0.06, 0.45); lid.add(lm);
  const band = new THREE.Mesh(new THREE.BoxGeometry(1.88, 0.06, 0.2), M(0xc8a040)); band.position.set(0, 0.07, 0.45); lid.add(band);
  g.add(lid);
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.66, 3.1, 10, 1, true),
    new THREE.MeshBasicMaterial({ color: 0x7fe8ff, transparent: true, opacity: 0.15, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false }));
  beam.position.y = 2.45; g.add(beam);
  const hold = new THREE.Group(); hold.position.y = 1.1; g.add(hold);
  group.add(g);
  return { g, lid, beam, hold, w: null, mesh: null, next: 0, flip: 'ar' };
}
function buildPower(pw, group) {
  const g = onWall(new THREE.Group(), pw.at, pw.n, 0.1);
  const sign = canvasTex(128, 48, (x, w, h) => { x.fillStyle = '#ffd21a'; x.fillRect(0, 0, w, h); x.fillStyle = '#111'; x.font = `bold 30px ${FONT}`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('POWER', w / 2, h / 2 + 2); }).t;
  const s = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 0.48), new THREE.MeshBasicMaterial({ map: sign })); s.position.set(0, 0.95, 0.02); g.add(s);
  const lever = new THREE.Group(); lever.position.set(0, -0.05, 0.08);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.48, 0.07), M(0x222222)); arm.position.y = 0.24; lever.add(arm);
  const knob = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.12, 0.16), M(0xc02020)); knob.position.y = 0.48; lever.add(knob);
  lever.rotation.x = -0.7; g.add(lever);
  const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.12, 0.06), new THREE.MeshBasicMaterial({ color: 0xff2020 })); lamp.position.set(0.32, 0.4, 0.04); g.add(lamp);
  group.add(g);
  return { lever, lamp };
}
function buildCola(c, group) {
  const tex = canvasTex(96, 168, (x, w, h) => {
    x.fillStyle = '#b8141c'; x.fillRect(0, 0, w, h);
    x.fillStyle = '#e8e0d0'; x.fillRect(8, 8, w - 16, 104);
    x.save(); x.translate(w / 2, 60); x.rotate(-0.12); x.fillStyle = '#b8141c'; x.font = `bold 26px ${FONT}`; x.textAlign = 'center'; x.fillText('JANK', 0, -8); x.fillText('COLA', 0, 22); x.restore();
    x.fillStyle = '#222'; x.fillRect(20, 122, w - 40, 34); x.fillStyle = '#ffe14d'; x.fillRect(26, 128, 12, 8); x.fillRect(42, 128, 12, 8); x.fillRect(58, 128, 12, 8);
  }).t;
  const mat = new THREE.MeshBasicMaterial({ map: tex, color: 0x555555 });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 1.92), mat);
  onWall(m, [c.at[0] + c.n[0] * 0.4, 1.02, c.at[2] + c.n[2] * 0.4], c.n, 0.015);
  group.add(m);
  return { mat };
}
// fluorescent panels: dead until the power comes on (a few flicker anyway)
function buildLamps(zm, group) {
  const pts = [];
  for (const a of zm.areas) {
    const [x0, z0, x1, z1] = a.r, nx = Math.max(1, Math.round((x1 - x0) / 7)), nz = Math.max(1, Math.round((z1 - z0) / 7));
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) pts.push([x0 + ((i + 0.5) * (x1 - x0)) / nx, z0 + ((j + 0.5) * (z1 - z0)) / nz]);
  }
  const geo = new THREE.BoxGeometry(1.4, 0.05, 0.45), steady = [], flick = [];
  pts.forEach((p, i) => ((i * 7) % 5 === 0 ? flick : steady).push(p));
  Z.lampMat = new THREE.MeshBasicMaterial({ color: 0x3a3630 }); Z.flickMat = new THREE.MeshBasicMaterial({ color: 0x3a3630 });
  for (const [list, mat] of [[steady, Z.lampMat], [flick, Z.flickMat]]) {
    const im = new THREE.InstancedMesh(geo, mat, list.length), o = new THREE.Object3D();
    list.forEach(([x, z], i) => { o.position.set(x, zm.H - 0.03, z); o.updateMatrix(); im.setMatrixAt(i, o.matrix); });
    group.add(im);
  }
}
function sceneLights() {
  if (Z.lights) return Z.lights;
  let hemi = null, sun = null;
  for (const o of G.scene.children) { if (o.isHemisphereLight && !hemi) hemi = o; else if (o.isDirectionalLight && !sun) sun = o; }
  return (Z.lights = { hemi, sun, h0: hemi ? hemi.intensity : 1.6, s0: sun ? sun.intensity : 1.8 });
}
function setLights(mode) { // 'off' = the dark mall, 'on' = the power's on, '' = any other map
  if (Z.lit === mode) return;
  Z.lit = mode;
  if (!mode) return; // leaving the mall: loadMap (mapLight + lighting.js) already set the new map's own light, keep it
  const L = sceneLights(), [h, s] = mode === 'off' ? [0.62, 0.4] : [1.15, 0.85];
  if (L.hemi) L.hemi.intensity = h;
  if (L.sun) L.sun.intensity = s;
}

// main.js calls this after every map load: build the mall's extras (or take them down on any other map)
export function zmSetup(mapId) {
  if (Z.group) { G.scene.remove(Z.group); Z.group = null; }
  zxOff();
  Z.solid.clear(); // loadMap refilled BOXES, so no shutters are in it any more
  Z.doors = []; Z.crate = null; Z.power = null; Z.cola = null; Z.mapId = mapId; Z.racks = [];
  for (const m of Z.marks.values()) G.scene.remove(m);
  Z.marks.clear();
  const zm = MAPS[mapId] && MAPS[mapId].zm;
  Z.map = zm || null;
  setLights(zm ? 'off' : '');
  if (!zm) return;
  const group = Z.group = new THREE.Group();
  for (const d of zm.doors) {
    const sx = d.box.max[0] - d.box.min[0], sy = d.box.max[1] - d.box.min[1], sz = d.box.max[2] - d.box.min[2];
    const geo = new THREE.BoxGeometry(sx, sy, sz); geo.translate(0, -sy / 2, 0); // pivot at the top: it rolls up into the housing
    const tex = shutterTex(d.name, d.price), sign = new THREE.MeshLambertMaterial({ map: tex, emissiveMap: tex, emissive: 0x777777 }), plain = M(0x4a4e54); // the sign glows a bit
    const m = new THREE.Mesh(geo, sx < sz ? [sign, sign, plain, plain, plain, plain] : [plain, plain, plain, plain, sign, sign]);
    m.position.set((d.box.min[0] + d.box.max[0]) / 2, d.box.max[1], (d.box.min[2] + d.box.max[2]) / 2);
    group.add(m);
    Z.doors.push({ m, open: false, anim: 0 });
  }
  for (const b of zm.buys) group.add(buyBoard(b));
  zxSetup(zm, group); // planks on every window, the cheat machine
  Z.crate = buildCrate(zm.crate, group);
  Z.power = buildPower(zm.power, group);
  Z.cola = buildCola(zm.cola, group);
  buildLamps(zm, group);
  G.scene.add(group);
}
// leaving zombies (or the mall): shutters out of the collision, ammo back to normal
function offMode() {
  for (const i of Z.solid) { const k = BOXES.indexOf(Z.map && Z.map.doors[i].box); if (k >= 0) BOXES.splice(k, 1); }
  if (Z.solid.size) resetGrid(BOXES);
  Z.solid.clear();
  for (const id of Object.keys(Z.res)) if (W.cd[id] > performance.now() + 1e8) W.cd[id] = 0;
  Z.res = {}; Z.prev = {}; Z.target = null; Z.tally = -1;
  prompt.textContent = '';
}
export function zmReset() { // quit to the menu
  Z.on = false; offMode(); zmSetup('');
  root.classList.add('hidden'); document.body.classList.remove('zm-on');
}

// ------------------------------------------------------------ every frame (after the weapons have updated)
export function updateZombies(dt, now) {
  const g = G.round && G.round.game;
  if (g !== Z.cfgGame) { Z.cfgGame = g; fitMaps($('cfgMap'), g); }
  if (Z.on && /^randomizer/.test($('loNote').textContent)) $('loNote').textContent = 'zombies: you only carry what you bought. your loadout comes back after the match';
  const info = G.round && G.round.zm;
  const on = !!(G.joined && info && Z.map && MAPS[G.cfg.map] && MAPS[G.cfg.map].zm);
  if (on !== Z.on) { Z.on = on; document.body.classList.toggle('zm-on', on); root.classList.toggle('hidden', !on); if (!on) offMode(); }
  if (!on) return;
  syncDoors(info, now);
  ammoTick(now);
  hudTick(info, now);
  useTick(info, now);
  crateTick(info, dt, now);
  downTick(info, now);
  zxTick(info, dt, now);
  zombiesTick(dt, now);
  setLights(info.pw ? 'on' : 'off');
  if (Z.power) { Z.power.lever.rotation.x += ((info.pw ? 0.7 : -0.7) - Z.power.lever.rotation.x) * Math.min(1, dt * 8); Z.power.lamp.material.color.setHex(info.pw ? 0x40ff40 : 0xff2020); }
  if (Z.cola) Z.cola.mat.color.setHex(info.pw ? 0xffffff : 0x555555);
  if (Z.lampMat) {
    Z.lampMat.color.setHex(info.pw ? 0xfff2c8 : 0x3a3630);
    Z.flickMat.color.setHex(Math.random() < (info.pw ? 0.97 : 0.06) ? 0xfff2c8 : 0x3a3630);
  }
}
// the shutters: in the collision while they're down, rolled up (and out of it) once bought. a new game shuts them again
function syncDoors(info, now) {
  const open = new Set(info.o);
  let changed = false;
  Z.doors.forEach((d, i) => {
    if (open.has(i) && !d.open) { d.open = true; if (!d.anim) d.anim = 1; } // opened before we got here: no show
    if (!open.has(i) && d.open) { d.open = false; d.anim = 0; d.m.visible = true; d.m.scale.y = 1; }
    if (!d.open !== Z.solid.has(i)) {
      const box = Z.map.doors[i].box;
      if (!d.open) { BOXES.push(box); Z.solid.add(i); } else { const k = BOXES.indexOf(box); if (k >= 0) BOXES.splice(k, 1); Z.solid.delete(i); }
      changed = true;
    }
    if (d.open && d.anim) { const k = Math.min(1, (now - d.anim) / 900); d.m.scale.y = Math.max(0.02, 1 - k); d.m.visible = k < 1; }
  });
  if (changed) resetGrid(BOXES);
}
// your ammo: reloads come out of the spares the server says you have; no spares, no reload
function ammoTick(now) {
  for (const id of W.slots) {
    const w = WEAPONS[id];
    if (!w || Z.res[id] == null) continue;
    if (w.mag) {
      const was = Z.prev[id] ?? W.ammo[id], cur = W.ammo[id];
      if (cur > was) { // a reload just finished (and maybe a shot or two after it)
        const got = Math.min(w.mag - was, Z.res[id]);
        Z.res[id] -= got;
        W.ammo[id] = Math.max(0, was + got - (w.mag - cur));
      }
      Z.prev[id] = W.ammo[id];
    } else if (Z.res[id] <= 0) W.cd[id] = now + 1e9; // out of rockets / arrows: the trigger does nothing
  }
  if (W.reloadId && Z.res[W.reloadId] != null && Z.res[W.reloadId] <= 0) {
    W.reloadId = null;
    if (now - Z.msgT > 1500) { Z.msgT = now; hud.msg('NO AMMO · buy some off the wall', 1.2); sfx.empty(); }
  }
  const id = W.cur, w = WEAPONS[id], a = $('ammo');
  if (!w || Z.res[id] == null) return;
  a.style.display = 'block';
  if (w.mag) { a.textContent = W.reloadId ? 'reloading' : `${W.ammo[id]} / ${Z.res[id]}`; a.style.color = W.ammo[id] === 0 ? '#ff5050' : Z.res[id] === 0 ? '#ffe14d' : '#fff'; }
  else { a.textContent = `${Z.res[id]} left`; a.style.color = Z.res[id] ? '#fff' : '#ff5050'; }
}
function hudTick(info, now) {
  credN.textContent = fmt(Z.credits);
  if (info.n !== Z.tally) { Z.tally = info.n; drawTally(info.n); }
  tallyCv.classList.toggle('pulse', info.st === 'break' || info.st === 'pre');
  if (info.st === 'pre') Z.cola2 = false;
  const rows = [];
  for (const [id, c, st] of info.pts || []) {
    if (id === G.myId) continue;
    const n = G.names.get(id);
    rows.push(`<div style="color:${n ? n.color : '#fff'}">${esc(n ? n.name : '???')} <b>${fmt(c)}</b>${st === 2 ? ' <i>DOWN</i>' : st === 3 ? ' <i>dead</i>' : ''}</div>`);
  }
  const html = rows.join('');
  if (team.dataset.k !== html) { team.dataset.k = html; team.innerHTML = html; }
}
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
// what you're looking at, the prompt for it, and the hold-F meter
function useTick(info, now) {
  const st = { open: Z.doors.map((d) => d.open), power: !!info.pw, down: (info.dn || []).map((d) => [d[0], d[1], d[2], d[3]]), me: G.myId };
  const here = zmOpenAreas(Z.map, st.open).has(zmAreaAt(Z.map, ME.pos)); // same rule as the server: you have to be somewhere open
  const t = Z.target = ME.alive && here && info.st !== 'over' ? zmTarget(Z.map, st, eye(), look()) || zxTarget(info, eye(), look()) : null;
  let text = '', ok = false;
  if (t) [text, ok] = promptFor(t, info);
  if (now < Z.flashT) { text = Z.flash; ok = Z.flashOk; }
  if (prompt.textContent !== text) prompt.textContent = text;
  prompt.className = ok ? 'ok' : 'no';
  if (G.using && t) {
    if (!Z.wasUsing || Z.useK !== t.k) { Z.useT = now; Z.useK = t.k; }
    const need = (t.kind === 'revive' ? ZM.revive * (G.settings.zload && G.settings.zload.perk === 'quickhands' ? 0.5 : 1) : t.kind === 'power' ? ZM.power : ZM.hold) * 1000;
    const zm = zxMeter(t, now - Z.useT);
    if (zm) hud.meter(...zm); else hud.meter(Math.min(1, (now - Z.useT) / need), t.kind === 'revive' ? `REVIVING... keep holding ${UK()}` : t.kind === 'power' ? 'THROWING THE SWITCH...' : `HOLD ${UK()}`, t.kind === 'revive' ? '#7dff4f' : '#ffe14d');
  }
  Z.wasUsing = G.using;
}
function promptFor(t, info) {
  const zx = zxPrompt(t, info, Z.credits);
  if (zx) return zx;
  const can = (p) => Z.credits >= zxPrice(p);
  if (t.kind === 'door') { const d = Z.map.doors[t.i]; return [`[${UK()}] OPEN ${d.name.toUpperCase()} · ${zxPrice(d.price)}`, can(d.price)]; }
  if (t.kind === 'buy') {
    const b = Z.map.buys[t.i], name = WEAPONS[b.w].name.toUpperCase();
    if (!Z.guns.includes(b.w) && Z.melee !== b.w) return [`[${UK()}] BUY ${name} · ${zxPrice(b.price)}`, can(b.price)];
    const max = zmAmmo(b.w);
    if (max == null) return [`${name} · you have it`, false];
    const have = (WEAPONS[b.w].mag ? W.ammo[b.w] || 0 : 0) + (Z.res[b.w] || 0), price = zmAmmoPrice(b.price);
    return have >= max ? [`${name} · ammo full`, false] : [`[${UK()}] ${name} AMMO · ${zxPrice(price)}`, can(price)];
  }
  if (t.kind === 'crate') {
    const bx = info.bx;
    if (!bx) return [`[${UK()}] MYSTERY CRATE · ${zxPrice(ZM.crate)} · a random weapon`, can(ZM.crate)];
    if (bx[0] === 2 && bx[1] === G.myId) return [`[${UK()}] TAKE THE ${WEAPONS[bx[2]].name.toUpperCase()}`, true];
    return [bx[0] === 1 ? 'spinning...' : `that's ${(G.names.get(bx[1]) || { name: 'someone' }).name}'s`, false];
  }
  if (t.kind === 'power') return [`[${UK()}] HOLD TO TURN THE POWER ON`, true];
  if (t.kind === 'cola') {
    if (!info.pw) return ['JANK COLA · no power (the switch is in the loading dock)', false];
    if (Z.cola2) return ['JANK COLA · you already had one', false];
    return [`[${UK()}] JANK COLA · ${zxPrice(ZM.cola)} · zombies hit you half as hard`, can(ZM.cola)];
  }
  if (t.kind === 'revive') return [`[${UK()}] HOLD TO REVIVE ${(G.names.get(t.id) || { name: '???' }).name.toUpperCase()}`, true];
  return ['', false];
}
// the crate: lid up, a weapon rising out of it flicking through the pool, slowing down, landing on yours
function crateTick(info, dt, now) {
  const c = Z.crate;
  if (!c) return;
  const bx = info.bx, st = bx ? bx[0] : 0;
  c.lid.rotation.x += ((st ? -1.9 : 0) - c.lid.rotation.x) * Math.min(1, dt * 6);
  c.beam.material.opacity = (st ? 0.06 : 0.14) + Math.sin(now * 0.003) * 0.03; // fades while a weapon is out so you can see it
  if (!st) { if (c.mesh) { c.hold.remove(c.mesh); c.mesh = null; c.w = null; } return; }
  let show = bx[2];
  if (st === 1) {
    const k = Math.max(0, Math.min(1, 1 - bx[3] / ZM.spin));
    if (k < 0.86) { if (now >= c.next) { c.next = now + 70 + 380 * k * k; const pool = Object.keys(ZM_CRATE).filter((id) => id !== c.flip); c.flip = pool[(Math.random() * pool.length) | 0]; } show = c.flip; }
    c.hold.position.y = 1.0 + k * 0.75;
  } else c.hold.position.y = 1.75 + Math.sin(now * 0.004) * 0.06;
  if (show !== c.w && WEAPONS[show]) {
    if (c.mesh) c.hold.remove(c.mesh);
    if (!Z.weapons.has(show)) { // every weapon about a metre long, turning round its middle
      const m = buildWeapon(show), w = new THREE.Group(), bb = new THREE.Box3(), sz = new THREE.Vector3(), mid = new THREE.Vector3();
      m.rotation.y = Math.PI / 2; m.updateMatrixWorld(true); bb.setFromObject(m); bb.getSize(sz); bb.getCenter(mid);
      const k = Math.min(5, 1.0 / Math.max(0.05, sz.x, sz.y, sz.z));
      m.scale.setScalar(k); m.position.copy(mid).multiplyScalar(-k); w.add(m); Z.weapons.set(show, w);
    }
    c.mesh = Z.weapons.get(show); c.hold.add(c.mesh); c.w = show;
    if (st === 1) sfx.click(c.g.position.toArray());
  }
  c.hold.rotation.y += dt * (st === 1 ? 5 : 1.4);
  c.hold.visible = !(st === 2 && bx[3] < 2500 && Math.sin(now * 0.03) < 0); // blinks before it goes back in
}
// downed friends: a red cross over them (through walls) with their bleed-out clock. you, downed: the low view + what's going on
function downTick(info, now) {
  const seen = new Set();
  for (const [id, x, y, z, left, f] of info.dn || []) {
    if (id === G.myId) continue;
    seen.add(id);
    let s = Z.marks.get(id);
    if (!s) { s = downSprite(); Z.marks.set(id, s); G.scene.add(s); }
    s.position.set(x, y + 1.0 + Math.sin(now * 0.005) * 0.08, z);
    const key = `${Math.ceil(left / 1000)}|${Math.round(f * 10)}`;
    if (s.userData.key !== key) { s.userData.key = key; drawDown(s, Math.ceil(left / 1000), f); }
  }
  for (const [id, s] of Z.marks) if (!seen.has(id)) { G.scene.remove(s); Z.marks.delete(id); }
  if (ME.alive || !G.joined) return;
  G.deadAt = now - 450; // the death camera floats up 4 m: keep it under the ceiling, over your body
  const me = (info.dn || []).find((d) => d[0] === G.myId);
  $('deadCard').innerHTML = '';
  if (info.st === 'over') setDead('', ''); // the game over box says it all, don't print over its numbers
  else if (me) setDead("YOU'RE DOWN", me[5] > 0 ? `getting revived... ${Math.round(me[5] * 100)}%` : `bleeding out in ${Math.ceil(me[4] / 1000)} · a friend can hold ${UK()} on you to revive you`);
  else setDead("YOU'RE DEAD", 'you come back when the next round starts');
}
function setDead(a, b) { if ($('deadText').textContent !== a) $('deadText').textContent = a; if ($('deadTimer').textContent !== b) $('deadTimer').textContent = b; }
function downSprite() {
  const c = document.createElement('canvas'); c.width = 96; c.height = 96;
  const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, sizeAttenuation: false, transparent: true, fog: false }));
  s.scale.set(0.11, 0.11, 1); s.renderOrder = 21; s.userData.cv = c;
  return s;
}
function drawDown(s, sec, f) {
  const c = s.userData.cv, x = c.getContext('2d');
  x.clearRect(0, 0, 96, 96);
  x.lineWidth = 7; x.strokeStyle = 'rgba(0,0,0,0.6)'; x.beginPath(); x.arc(48, 44, 30, 0, Math.PI * 2); x.stroke();
  x.strokeStyle = f > 0 ? '#7dff4f' : '#ff3030'; x.beginPath(); x.arc(48, 44, 30, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (f > 0 ? f : Math.min(1, sec / ZM.bleed))); x.stroke();
  x.fillStyle = '#ff3030'; x.fillRect(42, 26, 12, 36); x.fillRect(30, 38, 36, 12);
  x.fillStyle = '#fff'; x.font = `bold 18px ${FONT}`; x.textAlign = 'center'; x.fillText(f > 0 ? 'REVIVING' : `${sec}s`, 48, 92);
  s.material.map.needsUpdate = true;
}
// zombie mannequins: no name tags, a shamble (or a lean if they run), the odd missing arm, groans nearby
function zombiesTick(dt, now) {
  const near = [];
  for (const r of G.remotes.values()) {
    if (!isZombie(r) || !r.ch) continue;
    const ch = r.ch;
    if (r.zmCh !== ch) { r.zmCh = ch; ch.armL.visible = r.id % 3 !== 0; if (r.tag) r.tag.visible = false; }
    r.marker.visible = false;
    if (!r.alive || (r.f & FLAGS.SLIP)) continue;
    const run = r.color !== SHAMBLER, ph = now * (run ? 0.011 : 0.0045) + r.id;
    ch.body.rotation.z = ch.jank.lean * 0.3 + Math.sin(ph) * (run ? 0.08 : 0.16);
    ch.head.rotation.z += Math.sin(ph * 0.7) * 0.35;
    if (run) ch.body.rotation.x = -0.3;
    if (Math.hypot(r.pos[0] - ME.pos[0], r.pos[2] - ME.pos[2]) < 26) near.push(r);
  }
  if (now > Z.groanT && near.length) { Z.groanT = now + 900 + Math.random() * 2200 / Math.min(4, near.length); sfx.zmGroan(near[(Math.random() * near.length) | 0].pos); }
}

// ------------------------------------------------------------ hooks for main.js / objective.js
export function zmCanUse() { return Z.on && !!Z.target; }
// round line under the tally
export function zmRoundText(r) {
  const z = r && r.zm;
  if (!z) return null;
  if (r.over || z.st === 'over') return `next match in ${Math.ceil(r.left / 1000)}`;
  if (z.st === 'pre') return `the zombies are coming · ${Math.ceil(z.br / 1000)}`;
  if (z.st === 'break') return `round ${z.n} survived · next round in ${Math.ceil(z.br / 1000)}`;
  return `${z.left} zombie${z.left === 1 ? '' : 's'} left`;
}
// scoreboard: no zombies on it, everyone's credits next to their name
export function zmScoreRows(rows) {
  if (!Z.on) return;
  for (let i = rows.length - 1; i >= 0; i--) if (rows[i].id != null && isZombie(G.remotes.get(rows[i].id))) rows.splice(i, 1);
  const pts = new Map(((G.round && G.round.zm && G.round.zm.pts) || []).map((p) => [p[0], p[1]]));
  for (const row of rows) { const c = pts.get(row.me ? G.myId : row.id); if (c != null) row.name = `${row.name} · ${fmt(c)}`; }
}
// a zombie went down: the gibs already flew, skip the kill feed (the credits popup says it all)
export function zmKillFeed(m, victim) { return Z.on && isZombie(victim); }
// setup screen / match settings: the zombies map only shows up for zombies, and only it does
function fitMaps(sel, game) {
  if (!sel) return;
  const zm = !!(GAMES[game] && GAMES[game].zombies);
  let first = '';
  for (const o of sel.options) { const ok = !!(MAPS[o.value] && MAPS[o.value].zm) === zm; o.hidden = !ok; o.disabled = !ok; if (ok && !first) first = o.value; }
  if (sel.selectedOptions[0] && sel.selectedOptions[0].disabled) sel.value = zm ? first : sel.dataset.was && !MAPS[sel.dataset.was].zm ? sel.dataset.was : 'islands';
}
setTimeout(() => { // after main.js filled the selects
  const g = $('setupGame'), m = $('setupMap');
  if (!g || !m) return;
  const sync = () => { fitMaps(m, g.value); const bots = $('setupBots'); if (bots) bots.parentElement.style.display = GAMES[g.value] && GAMES[g.value].zombies ? 'none' : ''; }; // zombies brings its own bots
  sync();
  m.addEventListener('change', () => { if (!MAPS[m.value].zm) m.dataset.was = m.value; });
  g.addEventListener('change', sync);
}, 0);

// ------------------------------------------------------------ messages
// what you're carrying: the server's list of your guns + melee, and how much ammo each has left
net.on('zl', (m) => {
  const slots = (m.slots || []).filter((id) => WEAPONS[id]);
  if (!slots.length) return;
  G.forcedLoadout = { zm: 1 }; // so LOADOUT can't swap your guns mid-game, and quitting puts yours back
  Z.melee = slots[slots.length - 1]; Z.guns = slots.slice(0, -1);
  if (m.c != null) Z.credits = m.c;
  const keep = m.want || W.cur;
  W.item = typeof m.it === 'string' && m.it ? m.it : (G.settings.loadout && G.settings.loadout.item) || 'frag'; // your zombies item
  W.slots = slots; W.cur = null; W.slot = -1;
  const i = slots.indexOf(keep);
  switchSlot(i >= 0 ? i : 0);
  showSlots();
  const now = performance.now();
  for (const id of Object.keys(Z.res)) if (!(id in (m.ammo || {}))) { delete Z.res[id]; if (W.cd[id] > now + 1e8) W.cd[id] = 0; }
  for (const [id, tot] of Object.entries(m.ammo || {})) {
    const w = WEAPONS[id];
    if (!w) continue;
    if (w.mag) { W.ammo[id] = Math.min(w.mag, tot); Z.res[id] = tot - W.ammo[id]; } else { Z.res[id] = tot; if (tot > 0 && W.cd[id] > now + 1e8) W.cd[id] = 0; }
  }
  Z.prev = { ...W.ammo };
});
net.on('zc', (m) => { Z.credits = m.c; popup(m.d, m.why); });
net.on('za', (m) => { Z.res[m.w] = m.n; });
net.on('zbuy', (m) => {
  Z.flash = m.ok ? `${m.m}!` : m.m; Z.flashOk = !!m.ok; Z.flashT = performance.now() + 1100;
  if (m.ok) { sfx.cash(); if (m.k === 'cola') { Z.cola2 = true; sfx.heal(); } } else sfx.error();
});
net.on('zdoor', (m) => {
  const d = Z.doors[m.i];
  if (d && !d.open) { d.open = true; d.anim = performance.now(); }
  const dd = Z.map && Z.map.doors[m.i];
  if (dd) { sfx.rollShutter(dd.at); hud.chat(null, null, `${m.by === G.myId ? 'you' : (G.names.get(m.by) || { name: 'someone' }).name} opened the ${dd.name}`); }
});
net.on('zbox', (m) => {
  const at = Z.map && Z.map.crate.at;
  if (m.k === 'spin') { if (Z.crate) Z.crate.next = 0; sfx.musicBox(at); }
  if (m.k === 'offer' && m.by === G.myId) hud.msg(`${WEAPONS[m.w].name.toUpperCase()} · ${UK()} to take it`, 2, 'brag');
  if (m.k === 'take') sfx.ting(at);
});
net.on('zround', (m) => {
  if (m.k === 'start') { showBanner(`ROUND ${m.n}`, m.n === 1 ? `hold ${UK()} on doors, guns and the crate to buy them` : `${m.count} of them`, 'start'); tallyCv.classList.remove('flash'); void tallyCv.offsetWidth; tallyCv.classList.add('flash'); sfx.roundStart(); }
  else { showBanner(`ROUND ${m.n} SURVIVED`, `next round in ${Math.round(m.ms / 1000)}`, 'clear'); sfx.roundEnd(); }
});
net.on('zpower', (m) => {
  sfx.powerOn(Z.map && Z.map.power.at);
  showBanner('POWER ON', 'the Jank Cola machine works now', 'clear');
  hud.chat(null, null, `${m.by === G.myId ? 'you' : (G.names.get(m.by) || { name: 'someone' }).name} turned the power on`);
});
net.on('zdown', (m) => {
  const me = m.id === G.myId, name = me ? 'you' : (G.names.get(m.id) || { name: '???' }).name;
  if (me && (m.k === 'down' || m.k === 'dead')) Z.cola2 = false;
  if (m.k === 'down') { hud.chat(null, null, me ? "you're down! a friend has 30 s to revive you" : `${name} is down! hold ${UK()} on them to revive`); if (!me) sfx.error(); }
  if (m.k === 'up') { hud.chat(null, null, `${name} ${me ? 'are' : 'is'} back up`); sfx.heal(); }
  if (m.k === 'out') hud.chat(null, null, `${name} bled out · back next round`);
});
// joined mid-round: you watch until the next round starts
net.on('zbench', () => { ME.alive = false; W.held = false; W.aimHeld = false; G.deadAt = performance.now(); hud.dead(true, [['you joined mid-round', '#fff']]); });
// game over: how far you got and who did what (the vote panel shows up next to it)
net.on('zmover', (m) => {
  const box = $('roundEnd');
  box.innerHTML = '';
  const h = mk('h3', null, box, 'zmOver'); h.textContent = 'GAME OVER';
  mk('div', null, box, 'zmSub').textContent = m.n > 1 ? `you made it to round ${m.n}` : 'round 1. ouch.';
  const tbl = mk('div', null, box, 'zmRows');
  const row = (cells, cls, color) => { const r = mk('div', null, tbl, 'zr ' + (cls || '')); if (color) r.style.color = color; for (const c of cells) mk('span', null, r).textContent = c; };
  row(['', 'kills', 'heads', 'downs', 'revives', 'earned'], 'head');
  for (const [id, name, k, hd, dn, rv, earned] of m.rows || []) row([name, k, hd, dn, rv, fmt(earned)], id === G.myId ? 'me' : '', id === G.myId ? '#ffe14d' : (G.names.get(id) || {}).color);
  box.classList.remove('hidden');
  sfx.death();
});
