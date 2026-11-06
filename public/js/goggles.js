// Night Vision Goggles (item): G flips them down over your eyes / back up (free), MIDDLE CLICK or N fires the flash (a charge).
// On: the screen goes green and grainy inside the two eyepieces, the dark lifts, fog thins and everyone's outline glows.
// The flash: the server decides who it reaches ('flashed'); flashMe() is the white-out + ringing (any flash can use it).
// Everyone else sees the goggles on your face with the lenses lit (FLAGS.NV in snapshots) and the flash go off ('nvflash').
import * as THREE from 'three';
import { FLAGS, NVG } from '/shared/weapons.js';
import { G } from './ctx.js';
import { ME } from './player.js';
import { W, useItem } from './weapons.js';
import { net } from './net.js';
import { nvGoggles } from './gearmodels.js';
import { fx } from './fx.js';
import { sfx, setMuffle } from './audio.js';
import { hud } from './hud.js';
import { RP, RP_HOOKS, recordEv } from './replay.js';
import { K } from './keys.js';
import { whenLate } from './glbkit.js';

const NV = { on: false, t: 0, k: 0, vm: null, amb: null, fog: null, lastFlashT: 0 };
whenLate('x_nvg', () => { if (NV.vm && !NV.vm.visible) { NV.vm.removeFromParent(); NV.vm = null; } }); // the Blender goggles landed (heads get them with their next rebuild)
const ease = (x) => x * x * (3 - 2 * x);
export const nvOn = () => NV.on;

// ------------------------------------------------------------ G and H
export function nvToggle() {
  const now = performance.now();
  if (!ME.alive || now - NV.t < NVG.toggle * 1000) return;
  NV.on = !NV.on; NV.t = now;
  net.send({ t: 'nv', on: NV.on ? 1 : 0 });
  if (NV.on) sfx.nvOn(); else sfx.nvOff();
}
export function nvFlashKey() {
  if (!ME.alive) return;
  if (W.item !== 'nvg') { hud.msg(`${K.label('nvgFlash').toUpperCase()} FLASHES WITH NIGHT VISION GOGGLES (LOADOUT > ITEM)`, 1.6); return; }
  if (!NV.on || NV.k < 0.9) { hud.msg(`PUT THE GOGGLES ON FIRST (${K.label('item').toUpperCase()})`, 1.2, 'slip'); return; }
  W.nvFire = true; useItem(); W.nvFire = false;
}

// ------------------------------------------------------------ the green view
const CSS = `
#nvFx { position: absolute; inset: 0; pointer-events: none; opacity: 0; transition: opacity 0.12s; }
#nvFx.on { opacity: 1; }
#nvFx .grain { position: absolute; inset: -50%; opacity: 0.22; mix-blend-mode: screen; animation: nvGrain 0.25s steps(4) infinite; }
#nvFx .scan { position: absolute; inset: 0; background: repeating-linear-gradient(0deg, rgba(0,0,0,0.18) 0 1px, transparent 1px 3px); }
#nvFx .glow { position: absolute; inset: 0; background: radial-gradient(ellipse 55% 60% at 50% 50%, rgba(120,255,120,0.10), rgba(0,40,0,0.25) 75%); }
#nvFx .mask { position: absolute; inset: 0; background:
  radial-gradient(circle at 34% 50%, transparent 0 33vmin, rgba(0,0,0,0.0) 33vmin), radial-gradient(circle at 66% 50%, transparent 0 33vmin, rgba(0,0,0,0) 33vmin); }
#nvFx .eyes { position: absolute; inset: 0; }
#nvFx .hudtxt { position: absolute; left: 50%; top: 9%; transform: translateX(-50%); font: 700 16px monospace; color: #b8ffb0; letter-spacing: 3px; text-shadow: 0 0 6px #39ff14; }
@keyframes nvGrain { 0% { transform: translate(0,0); } 25% { transform: translate(-7%,4%); } 50% { transform: translate(5%,-6%); } 75% { transform: translate(-3%,7%); } 100% { transform: translate(0,0); } }
body.nv canvas#game { filter: grayscale(1) sepia(1) hue-rotate(58deg) saturate(3.2) brightness(var(--nvb, 1.2)) contrast(1.12); }
#flashFx { position: absolute; inset: 0; pointer-events: none; background: #fff; opacity: 0; z-index: 9; }
#flashFx.green { background: #e8ffe0; }
#afterFx { position: absolute; inset: 0; pointer-events: none; opacity: 0; z-index: 9; backdrop-filter: blur(10px) brightness(1.7) saturate(0.3); -webkit-backdrop-filter: blur(10px) brightness(1.7) saturate(0.3); }
body.replaying #nvFx, body.replaying #flashFx, body.replaying #afterFx { display: none; }`;
let ov = null, flashEl = null, afterEl = null;
function grainUrl() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d'), im = x.createImageData(128, 128);
  for (let i = 0; i < im.data.length; i += 4) { const v = Math.random() * 255; im.data[i] = v * 0.7; im.data[i + 1] = v; im.data[i + 2] = v * 0.6; im.data[i + 3] = 255; }
  x.putImageData(im, 0, 0);
  return c.toDataURL();
}
function overlay() {
  if (ov) return ov;
  const st = document.createElement('style'); st.textContent = CSS; document.head.append(st);
  ov = document.createElement('div'); ov.id = 'nvFx';
  // the two eyepieces: black everywhere except two overlapping circles (an SVG mask scales with the screen)
  ov.innerHTML = `<div class="grain" style="background-image:url(${grainUrl()})"></div><div class="scan"></div><div class="glow"></div>
    <svg class="eyes" viewBox="0 0 160 90" preserveAspectRatio="xMidYMid slice"><defs><filter id="nvSoft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
    <mask id="nvEyes"><rect width="160" height="90" fill="#fff"/><g filter="url(#nvSoft)"><circle cx="58" cy="45" r="44" fill="#000"/><circle cx="102" cy="45" r="44" fill="#000"/></g></mask></defs>
    <rect width="160" height="90" fill="#020602" fill-opacity="0.93" mask="url(#nvEyes)"/></svg><div class="hudtxt">NV-2000 · H: FLASH</div>`;
  const ref = document.getElementById('freezeFx');
  if (ref) ref.after(ov); else document.body.append(ov);
  flashEl = document.createElement('div'); flashEl.id = 'flashFx';
  afterEl = document.createElement('div'); afterEl.id = 'afterFx';
  document.body.append(afterEl, flashEl);
  return ov;
}

// ------------------------------------------------------------ getting flashed (reusable: any flash can call this)
// s = seconds blind. fully white for the first ~40%, then it fades; the blurry afterimage hangs on a bit longer
const FL = { until: 0, s: 0, t0: 0, ears: 0 }; // ears: when your hearing comes back (outlives a death or a respawn)
export function flashMe(s, green = false) {
  overlay();
  const now = performance.now();
  FL.t0 = now; FL.s = Math.max(s, (FL.until - now) / 1000); FL.until = now + FL.s * 1000; FL.ears = Math.max(FL.ears, FL.until + 400);
  flashEl.classList.toggle('green', green);
  sfx.tinnitus(FL.s);
  setMuffle(true);
  G.shake = Math.max(G.shake, 0.35);
}
export function onFlashed(m) {
  const s = Math.max(0.2, Math.min(8, Number(m.s) || 1));
  flashMe(s, NV.on);
  const by = (G.names.get(m.by) || {}).name || '???';
  hud.msg(NV.on ? 'MY EYES! (THE GOGGLES MADE IT WORSE)' : `FLASHED BY ${by}`, Math.min(2.5, s), 'slip');
}
function stepFlash(now) {
  if (!flashEl) return;
  // hearing: stays muffled for the whole flash even if you die or respawn, then eases back over a second or so
  if (FL.ears && now >= FL.ears) { FL.ears = 0; setMuffle(false, false, 0.35); }
  if (now >= FL.until + 400) { if (flashEl.style.opacity !== '0') { flashEl.style.opacity = 0; afterEl.style.opacity = 0; } return; }
  const k = (now - FL.t0) / (FL.s * 1000);
  flashEl.style.opacity = k < 0.4 ? 1 : Math.max(0, 1 - (k - 0.4) / 0.6) ** 1.5;
  afterEl.style.opacity = k < 1.3 ? Math.min(1, 1.3 - k) : 0;
}

// ------------------------------------------------------------ your goggles: flipping them down (viewmodel) + the view
function vm() {
  if (NV.vm) return NV.vm;
  NV.vm = nvGoggles();
  NV.vm.visible = false;
  G.vmScene.add(NV.vm);
  return NV.vm;
}
// the dark lifts: one ambient light that's always in the scene (0 when off, so turning it up never recompiles shaders)
function ambient() {
  if (!NV.amb && G.scene) { NV.amb = new THREE.AmbientLight(0xffffff, 0); G.scene.add(NV.amb); }
  return NV.amb;
}
const glowOutline = new THREE.MeshBasicMaterial({ color: 0xd8ffd0, side: THREE.BackSide, fog: false });
function outlines(on) { // everyone else's outline glows while you wear them (and goes back after)
  for (const r of G.remotes.values()) for (const sh of r.shells || []) {
    if (on && sh.material !== glowOutline) { sh.userData.orig = sh.material; sh.material = glowOutline; }
    else if (!on && sh.userData.orig) { sh.material = sh.userData.orig; sh.userData.orig = null; }
  }
}
function stepView(dt, now) {
  // k: 0 = up on your forehead, 1 = down over your eyes. the view switches on once they're down
  const want = NV.on && ME.alive && G.joined ? 1 : 0;
  NV.k += Math.sign(want - NV.k) * Math.min(Math.abs(want - NV.k), dt / 0.3);
  const g = vm(), k = ease(NV.k);
  g.visible = NV.k > 0.01 && NV.k < 0.99 && !RP.active;
  if (g.visible) { // swings down from above your head, right into your face
    g.position.set(0, 0.32 - 0.33 * k, -0.06 - 0.08 * (1 - k));
    g.userData.pivot.rotation.x = -1.3 * (1 - k);
    g.rotation.set(0.15 * (1 - k), 0, 0.05 * Math.sin(now * 0.02) * (1 - k));
  }
  const view = NV.k >= 0.99 && !RP.active;
  overlay().classList.toggle('on', view);
  document.body.classList.toggle('nv', view);
  // how much it lifts depends on how dark the map is (a sunny map barely changes; a dark one gets readable)
  if (view && !NV.boost) {
    const hemi = G.scene.children.find((o) => o.isHemisphereLight), sun = G.scene.children.find((o) => o.isDirectionalLight);
    const lit = (hemi ? hemi.intensity : 1.6) + (sun ? sun.intensity : 1.8);
    NV.boost = Math.max(0.2, Math.min(2.6, 3.3 - lit));
    document.body.style.setProperty('--nvb', String(1.05 + Math.min(0.5, NV.boost * 0.2)));
  }
  if (!view) NV.boost = 0;
  const a = ambient();
  if (a) a.intensity = view ? NV.boost : 0;
  // fog thins (horror forest: you can see the trees now, and the thing between them)
  const f = G.scene && G.scene.fog;
  if (f) {
    if (view) { if (!NV.fog || f.far !== NV.fog.set) NV.fog = { near: f.near, far: f.far, set: f.far * 2.4 }; f.near = NV.fog.near * 2.4; f.far = NV.fog.set; }
    else if (NV.fog) { if (f.far === NV.fog.set) { f.near = NV.fog.near; f.far = NV.fog.far; } NV.fog = null; }
  }
  outlines(view);
}

// ------------------------------------------------------------ everyone else's goggles
function remoteGoggles(r, now) {
  const on = r.alive && !!(r.f & FLAGS.NV);
  if (!r.nvg && !on) return;
  if (!r.nvg || r.nvg.parent !== r.ch.head) {
    r.nvg = nvGoggles({ strap: true, big: 1.9 });
    r.nvg.position.set(0, 0.16, -0.13);
    r.ch.head.add(r.nvg);
    r.nvgK = 0;
  }
  r.nvgK += (on ? 1 : -1) * 0.05;
  r.nvgK = Math.max(0, Math.min(1, r.nvgK));
  r.nvg.visible = r.nvgK > 0;
  r.nvg.userData.pivot.rotation.x = -1.4 * (1 - ease(r.nvgK)); // flips down from the forehead
  for (const l of r.nvg.userData.lenses) l.color.setHex(on ? (Math.sin(now * 0.01 + r.id) > 0.9 ? 0xc8ffc0 : 0x39ff14) : 0x1a3a24);
}
// the flash going off on someone's face (or yours)
let flareTex = null;
function flare(p, big) {
  if (!flareTex) {
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const x = c.getContext('2d'), gr = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.3, 'rgba(220,255,210,0.85)'); gr.addColorStop(1, 'rgba(120,255,120,0)');
    x.fillStyle = gr; x.fillRect(0, 0, 64, 64); flareTex = new THREE.CanvasTexture(c);
  }
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: flareTex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false }));
  s.position.set(p[0], p[1], p[2]); s.renderOrder = 6; G.scene.add(s);
  flares.push({ s, t: 0, big });
}
const flares = [];
function stepFlares(dt) {
  for (let i = flares.length - 1; i >= 0; i--) {
    const F = flares[i]; F.t += dt;
    const k = F.t / 0.35;
    if (k >= 1) { G.scene.remove(F.s); F.s.material.dispose(); flares.splice(i, 1); continue; }
    F.s.scale.setScalar((F.big ? 9 : 5) * (0.4 + k));
    F.s.material.opacity = 1 - k;
  }
}
export function nvFlashFx(m, ghosts) {
  const r = ghosts ? ghosts.get(m.id) : G.remotes.get(m.id);
  const p = m.p;
  flare(p, true);
  fx.spray(p, 30, [0xffffff, 0xd8ffd0, 0x39ff14], 9, 0.5, 0.06, 0, 0.4);
  sfx.nvFlash(m.id === G.myId && !ghosts ? null : p);
  if (!ghosts && m.id !== G.myId) { // a pop of light for everyone near it
    const d = Math.hypot(p[0] - ME.pos[0], p[1] - ME.pos[1], p[2] - ME.pos[2]);
    NV.pop = Math.max(NV.pop || 0, 1 - d / 30);
  }
  if (r && r.nvg) r.nvg.userData.ir.color.setHex(0xffffff);
}

// ------------------------------------------------------------ every frame
let lastItemT = 0;
export function updateGoggles(dt, now) {
  if (!G.joined && NV.on) NV.on = false;
  if (!ME.alive && NV.on) NV.on = false; // they come off when you die (the server agrees)
  if (W.item !== 'nvg' && NV.on) { NV.on = false; net.send({ t: 'nv', on: 0 }); }
  if (W.itemT && W.itemT !== lastItemT) { // the flash went: your own pop (you're not blinded by your own)
    lastItemT = W.itemT;
    if (W.item === 'nvg' && W.nvFired) { W.nvFired = false; sfx.nvFlash(); hud.flash(0.45, 0.18); G.shake = Math.max(G.shake, 0.2); NV.pop = 0.6; }
  }
  W.nvOnFlag = NV.on && ME.alive; // goes out in your snapshots: everyone sees them on your face
  stepView(dt, now);
  stepFlash(now);
  stepFlares(dt);
  if (NV.pop > 0 && NV.amb) { NV.amb.intensity = Math.max(NV.amb.intensity, NV.pop * 3); NV.pop = Math.max(0, NV.pop - dt * 5); }
  if (!RP.active) for (const r of G.remotes.values()) { remoteGoggles(r, now); if (r.nvg) { const c = r.nvg.userData.ir.color; c.lerp(new THREE.Color(0x3a0808), Math.min(1, dt * 6)); } }
}
export function gogglesReset(leaving) { NV.on = false; NV.k = 0; FL.until = 0; if (leaving && FL.ears) { FL.ears = 0; setMuffle(false, true); } if (flashEl) { flashEl.style.opacity = 0; afterEl.style.opacity = 0; } } // the white goes, your ears don't (FL.ears)

// ------------------------------------------------------------ replays: goggle flashes
RP_HOOKS.push({
  ev(m, ghosts) { if (m.t === 'fx' && m.k === 'nvflash') { nvFlashFx(m, ghosts); return true; } return false; },
  step(t, ghosts) { for (const g of ghosts.values()) if (g.ch) remoteGoggles(g, performance.now()); stepFlares(1 / 60); },
});
export { NV, recordEv };
