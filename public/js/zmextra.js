// Zombies extras on the client: the planks over every window (torn off by zombies, nailed back by you), the spinning
// power-up drops, the Cheat Machine (its reel screen, lever and siren), the modifiers bar with timers, the red arrows
// that point at whatever just clawed you, and what the modifiers do on your side (ZOOMIES, BOTTOMLESS MAG, BIG HEAD).
// The server runs all of it (server/zmextra.js); zombies.js calls in through the zx* exports.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx, synth } from './audio.js';
import { ME } from './player.js';
import { W } from './weapons.js';
import { WEAPONS, STREAKS } from '/shared/weapons.js';
import { ZM, ZM_DROPS, ZM_MODS, zmBoardTarget, zmMachPrice } from '/shared/zombies.js';
import { M } from './models.js';
import { streakIcon } from './icons.js';
import { authored, whenLate } from './glbkit.js';
import { K } from './keys.js';

const $ = (id) => document.getElementById(id);
const FONT = '"Comic Neue", "Comic Sans MS", cursive';
const UK = () => K.label('use').toUpperCase();
const X = { zm: null, group: null, boards: [], drops: new Map(), mach: null, arrows: [], last: null, flash: null, big: false };
const tone = (...a) => synth.tone(...a), noise = (...a) => synth.noise(...a);

// ------------------------------------------------------------ sounds (synthesized, like everything else)
Object.assign(sfx, {
  plankRip(pos) { noise(0.22, 0.9, 'bandpass', 1800, 500, pos, 0, 1.6); tone('square', 160, 60, 0.18, 0.28, pos, 0.02); noise(0.4, 0.4, 'highpass', 2500, 1200, pos, 0.08); }, // wood screaming off its nails
  plankNail(pos) { for (let i = 0; i < 3; i++) { tone('square', 190 - i * 15, 70, 0.07, 0.32, pos, i * 0.11); noise(0.04, 0.6, 'highpass', 2600, 4500, pos, i * 0.11); } tone('sine', 2400, 2350, 0.12, 0.08, pos, 0.33); }, // bam bam BAM, ting
  dropSpawn(pos) { [523, 784, 1046].forEach((f, i) => tone('triangle', f, f * 1.02, 0.18, 0.18, pos, i * 0.07)); },
  dropTake() { [659, 880, 1175, 1568].forEach((f, i) => tone('square', f, f, 0.1, 0.14, null, i * 0.06)); noise(0.3, 0.2, 'highpass', 5000, 8000, null, 0.2); },
  machSpin(pos) { for (let i = 0; i < 22; i++) tone('square', 900 + (i % 3) * 220, 900 + (i % 3) * 220, 0.03, 0.08, pos, i * (0.05 + i * 0.004)); tone('sawtooth', 70, 140, 0.4, 0.12, pos); },
  machWin(pos) { [392, 523, 659, 784, 1046].forEach((f, i) => { tone('square', f, f, 0.14, 0.13, pos, i * 0.09); tone('triangle', f * 2, f * 2, 0.14, 0.05, pos, i * 0.09); }); noise(0.5, 0.25, 'highpass', 6000, 9000, pos, 0.45); },
  aisle5() { tone('sawtooth', 880, 110, 1.1, 0.3); noise(1.2, 0.6, 'lowpass', 2400, 80, null, 0.1); for (let i = 0; i < 4; i++) tone('square', 1400, 1400, 0.06, 0.1, null, 0.6 + i * 0.12); }, // the PA mic squeal, then the boom
});

// ------------------------------------------------------------ styles + HUD bits (made once)
const css = document.createElement('style');
css.textContent = `
#zxMods { position: absolute; left: 14px; top: 140px; display: flex; flex-direction: column; gap: 6px; pointer-events: none; }
#zxMods .zxm { background: rgba(18,8,24,0.92); border: 3px solid var(--c); box-shadow: 4px 4px 0 #4fd8ff; padding: 3px 8px 5px; min-width: 190px; transform: rotate(-1deg); font-family: var(--font); }
#zxMods .zxm b { color: var(--c); font-size: 17px; letter-spacing: 1px; }
#zxMods .zxm i { color: #fff; font-size: 11px; font-style: normal; margin-left: 6px; opacity: 0.8; }
#zxMods .zxm .bar { height: 6px; background: #000; margin-top: 3px; border: 1px solid #000; }
#zxMods .zxm .bar span { display: block; height: 100%; background: var(--c); }
#zxMods .zxm.low { animation: zxblink 0.4s steps(2) infinite; }
@keyframes zxblink { 50% { opacity: 0.35; } }
#zxPop { position: absolute; left: 50%; top: 30%; transform: translateX(-50%); text-align: center; pointer-events: none; opacity: 0; white-space: nowrap; font-family: var(--font); }
#zxPop.on { animation: zxpop 2.6s ease-out forwards; }
#zxPop b { display: block; font-size: 58px; color: var(--c); -webkit-text-stroke: 2px #000; text-shadow: 5px 5px 0 #000; transform: rotate(-2deg); }
#zxPop small { display: block; font-size: 20px; color: #fff; text-shadow: 2px 2px 0 #000; }
@keyframes zxpop { 0% { opacity: 0; transform: translateX(-50%) scale(2.2) rotate(6deg); } 10% { opacity: 1; transform: translateX(-50%) scale(0.92); } 16% { transform: translateX(-50%) scale(1.04); } 75% { opacity: 1; } 100% { opacity: 0; transform: translateX(-50%) translateY(-30px); } }
.zxArrow { position: absolute; left: 50%; top: 50%; width: 0; height: 0; pointer-events: none; opacity: 0; }
.zxArrow i { position: absolute; left: -26px; top: -150px; width: 0; height: 0; border-left: 26px solid transparent; border-right: 26px solid transparent; border-bottom: 46px solid #ff3030; filter: drop-shadow(3px 3px 0 #000); }
.zxArrow i::after { content: ''; position: absolute; left: -12px; top: 14px; border-left: 12px solid transparent; border-right: 12px solid transparent; border-bottom: 22px solid #ffe14d; }
`;
document.head.append(css);
const mk = (tag, id, parent, cls) => { const e = document.createElement(tag); if (id) e.id = id; if (cls) e.className = cls; parent.append(e); return e; };
let modsBox = null, pop = null;
function hudEls() {
  if (modsBox || !$('zmHud')) return !!modsBox;
  modsBox = mk('div', 'zxMods', $('zmHud'));
  pop = mk('div', 'zxPop', $('zmHud'));
  for (let i = 0; i < 4; i++) { const a = mk('div', null, $('zmHud'), 'zxArrow'); mk('i', null, a); X.arrows.push({ el: a, t: 0, at: null }); }
  return true;
}
function bigPop(text, sub, color) {
  if (!hudEls()) return;
  pop.innerHTML = ''; pop.style.setProperty('--c', color || '#ffe14d');
  mk('b', null, pop).textContent = text;
  if (sub) mk('small', null, pop).textContent = sub;
  pop.className = ''; void pop.offsetWidth; pop.className = 'on';
}

// ------------------------------------------------------------ the boards
const WOOD = [0x8a5a30, 0x6e4826, 0xa87a48, 0x5a3a20, 0x9a6a3a, 0x7a5a3a];
function codePlank(i) { // no Blender file: plain mismatched planks
  const g = new THREE.Group(), len = 2.2 + ((i * 37) % 5) * 0.05;
  const m = new THREE.Mesh(new THREE.BoxGeometry(len, 0.24, 0.06), M(i === 2 ? 0xff4fd8 : i === 4 ? 0xb8c0c8 : WOOD[i]));
  g.add(m);
  for (const s of [-1, 1]) { const n = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.05, 0.02), M(0x9a9aa0)); n.position.set(s * (len / 2 - 0.12), 0, 0.04); g.add(n); }
  g.position.set(((i * 13) % 3 - 1) * 0.05, 1.12 + i * 0.32, 0.07);
  g.rotation.z = (i % 2 ? -1 : 1) * (0.05 + ((i * 7) % 4) * 0.025);
  return g;
}
function buildBoard(w, i) {
  const g = new THREE.Group();
  g.position.set(w.at[0] + w.n[0] * 0.3, 0, w.at[2] + w.n[2] * 0.3); // the inner face of the wall
  g.rotation.y = Math.atan2(w.n[0], w.n[2]); // local +z = into the room
  const b = { g, i, w, planks: [], shown: ZM.planks, glb: false };
  const bl = authored('x_zmboard');
  if (bl) {
    g.add(bl.obj);
    for (let k = 0; k < ZM.planks; k++) { const p = bl.obj.getObjectByName('plank_' + k); if (p) b.planks.push(p); }
    b.glb = b.planks.length === ZM.planks;
  }
  if (b.planks.length < ZM.planks) { // the code ones
    if (bl) g.remove(bl.obj);
    b.planks = [];
    for (const x of [-1.05, 1.05]) { const m = new THREE.Mesh(new THREE.BoxGeometry(0.1, 2.1, 0.1), M(0x4a3018)); m.position.set(x, 1.9, 0.05); g.add(m); }
    for (let k = 0; k < ZM.planks; k++) { const p = codePlank(k); g.add(p); b.planks.push(p); }
  }
  for (const p of b.planks) p.userData.home = { p: p.position.clone(), r: p.rotation.clone() };
  for (const p of b.planks) p.userData.anim = null;
  return b;
}
function syncBoards(pk, now) {
  if (!pk) return;
  for (const b of X.boards) {
    const n = pk[b.i] ?? ZM.planks;
    while (b.shown > n) { b.shown--; rip(b, b.planks[b.shown], now); }
    while (b.shown < n) { slam(b, b.planks[b.shown], now); b.shown++; }
    for (const p of b.planks) stepPlank(p, now);
  }
}
const worldOf = (b) => [b.g.position.x, 1.9, b.g.position.z];
function rip(b, p, now) {
  if (!p) return;
  p.visible = true;
  p.userData.anim = { k: 'rip', t: now, spin: (Math.random() - 0.5) * 9, side: (Math.random() - 0.5) * 2 };
  if (now - (b.ripT || 0) > 120) { b.ripT = now; sfx.plankRip(worldOf(b)); }
}
function slam(b, p, now) {
  if (!p) return;
  p.visible = true;
  p.userData.anim = { k: 'slam', t: now };
  sfx.plankNail(worldOf(b));
}
function stepPlank(p, now) {
  const a = p.userData.anim, h = p.userData.home;
  if (!a) return;
  const t = (now - a.t) / 1000;
  if (a.k === 'rip') { // yanked out through the window and dropped in the alley
    const k = Math.min(1, t / 0.55);
    p.position.set(h.p.x + a.side * 0.5 * k, h.p.y + 0.6 * k - 2.4 * k * k, h.p.z - 1.6 * k);
    p.rotation.set(h.r.x + k * 1.2, h.r.y + a.spin * 0.2 * k, h.r.z + a.spin * k);
    if (k >= 1) { p.visible = false; p.userData.anim = null; p.position.copy(h.p); p.rotation.copy(h.r); }
  } else { // slapped on from your side, then a wobble from the nails
    const k = Math.min(1, t / 0.16), wob = t > 0.16 ? Math.sin((t - 0.16) * 40) * Math.exp(-(t - 0.16) * 9) * 0.06 : 0;
    p.position.set(h.p.x, h.p.y + 0.25 * (1 - k), h.p.z + 0.6 * (1 - k));
    p.rotation.set(h.r.x - 0.6 * (1 - k), h.r.y, h.r.z + (1 - k) * 0.5 + wob);
    if (t > 0.6) { p.position.copy(h.p); p.rotation.copy(h.r); p.userData.anim = null; }
  }
}

// ------------------------------------------------------------ drops
function labelSprite(text, color) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 96;
  const x = c.getContext('2d');
  x.font = `bold 52px ${FONT}`; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.lineWidth = 10; x.strokeStyle = '#000'; x.strokeText(text, 256, 50); x.fillStyle = color; x.fillText(text, 256, 48);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false, fog: false }));
  s.scale.set(2.2, 0.41, 1);
  return s;
}
function dropModel(k) { // what floats there: the killstreak's badge, a tip jar, an ammo crate, a wet floor sign
  const g = new THREE.Group(), def = ZM_DROPS[k] || {};
  if (def.streak) {
    const tex = new THREE.TextureLoader().load(streakIcon(k)); tex.colorSpace = THREE.SRGBColorSpace; tex.magFilter = THREE.NearestFilter;
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.08, 20), [M(0xffe14d), new THREE.MeshBasicMaterial({ map: tex }), new THREE.MeshBasicMaterial({ map: tex })]);
    disc.rotation.x = Math.PI / 2; g.add(disc);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.44, 0.05, 6, 20), M(0xff4fd8)); g.add(rim);
  } else if (k === 'tipjar') {
    const jar = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.24, 0.6, 12, 1, true), new THREE.MeshLambertMaterial({ color: 0xbfefff, transparent: true, opacity: 0.45, side: THREE.DoubleSide }));
    g.add(jar);
    const lid = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.27, 0.06, 12), M(0xc0c0c8)); lid.position.y = 0.32; g.add(lid);
    for (let i = 0; i < 7; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.02, 0.14), M(i % 2 ? 0x5fcf5f : 0x3f9f3f)); b.position.set((Math.random() - 0.5) * 0.12, -0.24 + i * 0.06, (Math.random() - 0.5) * 0.12); b.rotation.set(Math.random(), Math.random() * 3, Math.random() * 0.6); g.add(b); }
    const tag = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.12, 0.02), M(0xffe14d)); tag.position.set(0, 0.05, 0.25); g.add(tag);
  } else if (k === 'restock') {
    const box = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.36, 0.38), M(0x4a5a2a)); g.add(box);
    const st = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.08, 0.4), M(0xffe14d)); st.position.y = 0.06; g.add(st);
    for (let i = 0; i < 5; i++) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.22, 6), M(0xd8a040)); b.position.set(-0.24 + i * 0.12, 0.3, 0); g.add(b); const tip = new THREE.Mesh(new THREE.ConeGeometry(0.035, 0.07, 6), M(0xb06030)); tip.position.set(-0.24 + i * 0.12, 0.44, 0); g.add(tip); }
  } else { // aisle 5: a yellow wet floor sign and a mop
    for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.75, 0.03), M(0xffe14d)); p.position.set(0, 0, s * 0.14); p.rotation.x = s * 0.32; g.add(p); const w = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.14, 0.035), M(0x111111)); w.position.set(0, 0.08, s * 0.155); w.rotation.x = s * 0.32; g.add(w); }
    const mop = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1.3, 6), M(0x6a4a2a)); mop.position.set(0.35, 0.1, 0); mop.rotation.z = 0.35; g.add(mop);
    const head = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.16, 0.2), M(0xdcdccc)); head.position.set(0.58, -0.5, 0); g.add(head);
  }
  const color = def.color || '#ffe14d';
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.6, 3.4, 10, 1, true), new THREE.MeshBasicMaterial({ color: new THREE.Color(color), transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false }));
  beam.position.y = 0.6;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.05, 4, 24), new THREE.MeshBasicMaterial({ color: new THREE.Color(color), transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending, depthWrite: false }));
  ring.rotation.x = Math.PI / 2; ring.position.y = -0.95;
  const label = labelSprite(def.streak ? STREAKS[k].name.toUpperCase() : def.name, color); label.position.y = 0.95;
  const root = new THREE.Group(), spin = new THREE.Group();
  spin.add(g); root.add(spin, beam, ring, label);
  root.userData = { spin, beam, ring };
  return root;
}
function syncDrops(dr, now) {
  const seen = new Set();
  for (const [id, k, x, y, z, left] of dr || []) {
    seen.add(id);
    let d = X.drops.get(id);
    if (!d) { d = { m: dropModel(k), k, y }; d.m.position.set(x, y, z); X.group.add(d.m); X.drops.set(id, d); }
    const u = d.m.userData;
    u.spin.rotation.y = now * 0.0035 + id;
    u.spin.position.y = Math.sin(now * 0.004 + id) * 0.12;
    u.ring.scale.setScalar(1 + Math.sin(now * 0.006) * 0.12);
    d.m.visible = left > ZM.dropBlink || Math.sin(now * (left < 2000 ? 0.05 : 0.025)) > -0.2; // blinks before it goes
  }
  for (const [id, d] of X.drops) if (!seen.has(id)) { X.group.remove(d.m); X.drops.delete(id); }
}

// ------------------------------------------------------------ the Cheat Machine
const REEL = Object.keys(ZM_MODS);
function codeMachine() { // no Blender file: a plain cabinet
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.1, 2.16, 0.8), M(0x2a1030)); body.position.y = 1.08; g.add(body);
  const top = new THREE.Mesh(new THREE.BoxGeometry(1.14, 0.3, 0.84), new THREE.MeshBasicMaterial({ color: 0xff4fd8 })); top.position.y = 2.3; top.material.name = 'zm_neon'; g.add(top);
  const lever = new THREE.Group(); lever.name = 'lever'; lever.position.set(0.62, 1.2, 0.1);
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.5, 6), M(0xc0c0c8)); arm.position.y = 0.25; lever.add(arm);
  const ball = new THREE.Mesh(new THREE.SphereGeometry(0.08, 8, 6), M(0xff3030)); ball.position.y = 0.52; lever.add(ball);
  g.add(lever);
  const lamp = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 0.16, 8), new THREE.MeshBasicMaterial({ color: 0xffe14d })); lamp.name = 'lamp_wzN'; lamp.position.y = 2.53; g.add(lamp);
  return { g, meta: { screen: { c: [0, 1.6, 0.405], w: 0.75, h: 0.5 }, lever: { pivot: [0.62, 1.2, 0.1] } } };
}
function buildMach(mc) {
  const root = new THREE.Group();
  root.position.set(mc.at[0], 0, mc.at[2]); root.rotation.y = Math.atan2(mc.n[0], mc.n[2]);
  const bl = authored('x_zmmachine');
  const { g, meta } = bl ? { g: bl.obj, meta: bl.meta || {} } : codeMachine();
  root.add(g);
  const sc = (meta && meta.screen) || { c: [0, 1.6, 0.405], w: 0.75, h: 0.5 };
  const cv = document.createElement('canvas'); cv.width = 384; cv.height = Math.round(384 * sc.h / sc.w);
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(sc.w, sc.h), new THREE.MeshBasicMaterial({ map: tex, fog: false }));
  screen.position.set(sc.c[0], sc.c[1], sc.c[2] + 0.004); root.add(screen);
  const neon = [];
  g.traverse((o) => { if (o.isMesh) for (const m of [].concat(o.material)) if (m && /zm_neon|zm_lamp/.test(m.name || '') && !neon.includes(m)) neon.push(m); });
  for (const m of neon) m.userData.c0 = m.color ? m.color.clone() : null, m.userData.e0 = m.emissive ? m.emissive.clone() : null;
  const light = new THREE.PointLight(0xff4fd8, 0, 7, 1.6); light.position.set(0, 1.8, 0.9); root.add(light);
  return { root, cv, tex, leverPull: (meta && meta.lever && meta.lever.pull) || 1.2, lever: g.getObjectByName('lever'), lamp: g.getObjectByName('lamp_wzN'), neon, light, drawK: '', pull: 0, win: null, reel: [0, 0, 0], glb: !!bl };
}
function drawScreen(m, mc, pw, now) {
  const c = m.cv, x = c.getContext('2d'), w = c.width, h = c.height;
  const [st, k, left, uses, cd] = mc || [0, '', 0, 0, 0];
  const winning = m.win && now < m.win.until;
  const key = !pw ? 'off' + ((now / 400) | 0) % 2 : st ? 'spin' + ((now / 40) | 0) : winning ? 'win' + ((now / 150) | 0) : `idle${uses}|${Math.ceil(cd / 1000)}|${((now / 600) | 0) % 2}`;
  if (key === m.drawK) return;
  m.drawK = key;
  x.fillStyle = '#07030c'; x.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 4) { x.fillStyle = 'rgba(255,79,216,0.05)'; x.fillRect(0, y, w, 2); } // scanlines
  x.textAlign = 'center'; x.textBaseline = 'middle';
  if (!pw) { x.fillStyle = key.endsWith('1') ? '#ff3030' : '#5a1010'; x.font = `bold 54px ${FONT}`; x.fillText('NO POWER', w / 2, h / 2); m.tex.needsUpdate = true; return; }
  if (st || winning) { // three reels of modifier symbols, stopping left to right on the same one
    const t = st ? 1 - left / ZM.machSpin : 1, rw = w / 3 - 12;
    for (let i = 0; i < 3; i++) {
      const stop = 0.5 + i * 0.18, rx = 8 + i * (rw + 10);
      x.fillStyle = '#16081e'; x.fillRect(rx, 10, rw, h - 70); x.strokeStyle = '#ffe14d'; x.lineWidth = 4; x.strokeRect(rx, 10, rw, h - 70);
      let ids;
      if (t < stop) { const off = (now * (0.03 - i * 0.004)) % 1, base = ((now * 0.012) | 0) + i * 3; ids = [-1, 0, 1].map((d) => [REEL[(base + d + REEL.length * 9) % REEL.length], d - off]); }
      else ids = [[k, 0]];
      x.save(); x.beginPath(); x.rect(rx, 10, rw, h - 70); x.clip();
      for (const [id, d] of ids) { const md = ZM_MODS[id]; if (!md) continue; const cy = 10 + (h - 70) / 2 + d * 70; x.fillStyle = md.color; x.font = `bold 64px ${FONT}`; x.fillText(md.ico, rx + rw / 2, cy); }
      x.restore();
    }
    const md = ZM_MODS[k];
    if (t >= 0.86 && md) { x.fillStyle = (now / 150 | 0) % 2 && winning ? '#fff' : md.color; x.font = `bold 34px ${FONT}`; x.fillText(md.name, w / 2, h - 30); }
    else { x.fillStyle = '#ff4fd8'; x.font = `bold 30px ${FONT}`; x.fillText('ROLLING...', w / 2, h - 30); }
  } else {
    x.fillStyle = '#ff4fd8'; x.font = `bold 40px ${FONT}`; x.fillText('CHEAT MACHINE', w / 2, h * 0.28);
    if (cd > 0) { x.fillStyle = '#4fd8ff'; x.font = `bold 32px ${FONT}`; x.fillText(`COOLING DOWN ${Math.ceil(cd / 1000)}`, w / 2, h * 0.62); }
    else { x.fillStyle = key.endsWith('1') ? '#ffe14d' : '#fff'; x.font = `bold 46px ${FONT}`; x.fillText(`${zxPrice(zmMachPrice(uses))}`, w / 2, h * 0.6); x.font = `bold 22px ${FONT}`; x.fillStyle = '#c8b8d8'; x.fillText(`HOLD ${UK()} · A RANDOM CHEAT`, w / 2, h * 0.85); }
  }
  m.tex.needsUpdate = true;
}
function stepMach(info, dt, now) {
  const m = X.mach;
  if (!m) return;
  const pw = !!info.pw, mc = info.mc, spin = mc && mc[0] === 1;
  drawScreen(m, mc, pw, now);
  if (m.lever) { m.pull = spin ? Math.min(1, m.pull + dt * 6) : Math.max(0, m.pull - dt * 2); m.lever.rotation.x = m.pull * m.leverPull; } // the Blender lever swings forward on +x
  if (m.lamp) { m.lamp.rotation.y += dt * (spin ? 14 : pw ? 1.5 : 0); m.lamp.visible = !spin || Math.sin(now * 0.03) > -0.3; }
  for (const mat of m.neon) {
    const k = !pw ? 0.12 : spin ? 0.7 + Math.sin(now * 0.04) * 0.3 : 1;
    if (mat.userData.c0 && mat.isMeshBasicMaterial) mat.color.copy(mat.userData.c0).multiplyScalar(k);
    if (mat.userData.e0) mat.emissive.copy(mat.userData.e0).multiplyScalar(k);
  }
  m.light.intensity = !pw ? 0 : spin ? 2.5 + Math.sin(now * 0.03) * 1.5 : 1.2;
  if (m.win && now < m.win.until) m.light.color.set(ZM_MODS[m.win.k] ? ZM_MODS[m.win.k].color : '#ff4fd8'); else m.light.color.set(0xff4fd8);
}

// ------------------------------------------------------------ modifiers: the bar on the HUD, and what they do here
const mine = (md) => md && (ZM_MODS[md[0]] && (ZM_MODS[md[0]].team || md[1] === G.myId));
export function zxHas(info, k) { return !!(info && info.md && info.md.some((m) => m[0] === k && mine(m))); }
function stepMods(info, now) {
  if (!hudEls()) return;
  const rows = (info.md || []).filter(mine);
  const html = rows.map(([k, by, left]) => {
    const d = ZM_MODS[k];
    return `<div class="zxm${left < 3000 ? ' low' : ''}" style="--c:${d.color}"><b>${d.ico} ${d.name}</b><i>${d.team ? 'TEAM' : 'YOU'} · ${Math.ceil(left / 1000)}s</i><div class="bar"><span style="width:${Math.max(0, Math.min(100, (left / (d.dur * 1000)) * 100)).toFixed(1)}%"></span></div></div>`;
  }).join('');
  if (modsBox.dataset.k !== html) { modsBox.dataset.k = html; modsBox.innerHTML = html; }
  // what they do on your side (the server does the rest)
  if (zxHas(info, 'zoomies') && ME.alive) ME.speedMul = (ME.speedMul || 1) * 1.4;
  if (zxHas(info, 'bottomless')) { const w = WEAPONS[W.cur]; if (w && w.mag && W.ammo[W.cur] != null) { W.ammo[W.cur] = w.mag; if (W.reloadId === W.cur) W.reloadId = null; } }
  const big = zxHas(info, 'bighead');
  for (const r of G.remotes.values()) {
    if (!(r.bot && r.name === 'Zombie')) continue;
    r.zmBig = big; // remote.js hitboxes(): the bigger head counts too
    if (r.ch && r.ch.head) { const s = r.ch.head.scale.x, want = big ? 2.4 : 1; if (Math.abs(s - want) > 0.01) r.ch.head.scale.setScalar(s + (want - s) * 0.2); }
  }
}

// ------------------------------------------------------------ hit direction: an arrow round the crosshair toward whatever hit you
export function zxHurt(m) {
  if (!X.zm || m.to !== G.myId || !m.from || m.from === G.myId || !hudEls()) return;
  const r = G.remotes.get(m.from);
  if (!r) return;
  const a = X.arrows.reduce((o, x) => (x.t < o.t ? x : o), X.arrows[0]);
  a.t = performance.now(); a.at = r.pos.slice();
}
function stepArrows(now) {
  for (const a of X.arrows) {
    const age = (now - a.t) / 1000;
    if (!a.at || age > 1.1) { if (a.el.style.opacity !== '0') a.el.style.opacity = '0'; continue; }
    const dx = a.at[0] - ME.pos[0], dz = a.at[2] - ME.pos[2];
    const ang = Math.atan2(dx, -dz) + ME.yaw; // 0 = straight ahead, clockwise on screen
    a.el.style.transform = `rotate(${ang}rad) scale(${1 + Math.max(0, 0.25 - age) * 1.4})`;
    a.el.style.opacity = String(Math.max(0, 1 - age / 1.1));
  }
}

// ------------------------------------------------------------ hooks for zombies.js
export function zxSetup(zm, group) { // the mall was built: boards on every window, the machine
  X.zm = zm; X.group = group; X.boards = []; X.drops.clear(); X.mach = null;
  if (!zm) return;
  const re = () => { if (X.zm === zm && X.group === group) { for (const b of X.boards) group.remove(b.g); if (X.mach) group.remove(X.mach.root); build(); } };
  const build = () => {
    X.boards = zm.windows.map((w, i) => buildBoard(w, i));
    for (const b of X.boards) group.add(b.g);
    if (zm.mach) { X.mach = buildMach(zm.mach); group.add(X.mach.root); }
  };
  build();
  if (!X.boards.some((b) => b.glb)) whenLate('x_zmboard', re); // the Blender ones land later
  if (X.mach && !X.mach.glb) whenLate('x_zmmachine', re);
}
export function zxTick(info, dt, now) {
  if (!X.zm || !info) return;
  syncBoards(info.pk, now);
  syncDrops(info.dr, now);
  stepMach(info, dt, now);
  stepMods(info, now);
  stepArrows(now);
}
// F targets beyond the mode's own: the boards and the machine (same order as the server)
export function zxTarget(info, e, d) {
  const zm = X.zm;
  if (!zm || !info) return null;
  if (zm.mach) {
    const at = [zm.mach.at[0] + zm.mach.n[0] * 0.4, 1.4, zm.mach.at[2] + zm.mach.n[2] * 0.4], v = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(...v) || 1e-6;
    if (l <= 2.8 && (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l >= 0.35 && (e[0] - at[0]) * zm.mach.n[0] + (e[2] - at[2]) * zm.mach.n[2] > 0) return { k: 'mach', kind: 'mach' };
  }
  return zmBoardTarget(zm, info.pk, e, d);
}
// Coupon Book: what you really pay
export function zxPrice(p) { return G.settings.zload && G.settings.zload.perk === 'coupons' ? Math.round((p * 0.9) / 10) * 10 : p; }
export function zxPrompt(t, info, credits) {
  if (t.kind === 'board') { const n = (info.pk || [])[t.i] ?? ZM.planks; return [`[${UK()}] HOLD TO BOARD UP · ${n}/${ZM.planks}`, true]; }
  if (t.kind === 'mach') {
    const mc = info.mc || [0, '', 0, 0, 0];
    if (!info.pw) return ['CHEAT MACHINE · no power (the switch is in the loading dock)', false];
    if (mc[0] === 1) return ['CHEAT MACHINE · rolling...', false];
    if (mc[4] > 0) return [`CHEAT MACHINE · cooling down ${Math.ceil(mc[4] / 1000)}s`, false];
    const p = zxPrice(zmMachPrice(mc[3]));
    return [`[${UK()}] CHEAT MACHINE · ${p} · a random cheat`, credits >= p];
  }
  return null;
}
// hold meter: boarding loops (a plank each fill), the machine is a normal buy
export function zxMeter(t, held) {
  if (t.kind !== 'board') return null;
  const gap = ZM.board * (G.settings.zload && G.settings.zload.perk === 'handyman' ? 0.5 : 1);
  return [(held % gap) / gap, `BOARDING UP... keep holding ${UK()}`, '#c08040'];
}
export function zxOff() { X.zm = null; X.group = null; X.boards = []; X.drops.clear(); X.mach = null; for (const r of G.remotes.values()) r.zmBig = false; if (modsBox) { modsBox.innerHTML = ''; modsBox.dataset.k = ''; } }

// ------------------------------------------------------------ messages
const nameOf = (id) => (id === G.myId ? 'you' : (G.names.get(id) || { name: 'someone' }).name);
net.on('zplank', (m) => { if (m.k === 'nail' && m.by === G.myId && !m.paid && Math.random() < 0.25) hud.msg('no more pay for boards this round. still worth it', 1.2); });
net.on('zdrop', (m) => {
  if (m.k === 'new') { sfx.dropSpawn(m.a); return; }
  if (m.k !== 'take') return;
  const d = ZM_DROPS[m.kind] || {}, st = STREAKS[m.kind];
  const name = d.streak && st ? st.name.toUpperCase() : d.name || m.kind;
  sfx.dropTake();
  if (m.kind === 'aisle5') sfx.aisle5();
  bigPop(`${name}!`, `${nameOf(m.by)} grabbed it${d.desc ? ' · ' + d.desc : st ? ' · it goes off right away' : ''}`, d.color || '#ffe14d');
  hud.chat(null, null, `${nameOf(m.by)} grabbed ${name}`);
});
net.on('zmach', (m) => {
  const at = X.zm && X.zm.mach ? [X.zm.mach.at[0], 1.5, X.zm.mach.at[2]] : null;
  if (m.k === 'spin') { sfx.machSpin(at); if (X.mach) X.mach.drawK = ''; return; }
  if (m.k === 'win') {
    const d = ZM_MODS[m.mod];
    if (!d) return;
    if (X.mach) X.mach.win = { k: m.mod, until: performance.now() + 2500 };
    sfx.machWin(at);
    if (d.team || m.by === G.myId) bigPop(d.name, `${d.desc} · ${d.dur}s${d.team ? ' · everyone' : ''}`, d.color);
    hud.chat(null, null, `${nameOf(m.by)} rolled ${d.name}${d.team ? ' for everyone' : ''}`);
  }
});
export const zxState = () => X; // (tests)
