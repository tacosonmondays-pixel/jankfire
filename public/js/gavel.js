// Scales of Justice, ranged: the SUMMONS. Right click with the scales out and a ring of light opens under whoever you
// aimed at; a second later a pillar of light comes down on it. The server decides where, when and who is hit
// (server/gavel.js): this draws it, plays it, and tells you to MOVE when the ring is under you.
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { W } from './weapons.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { GAVEL } from '/shared/weapons.js';

const GOLD = 0xffc83a, WHITE = 0xfff3c4;
const live = new Map(); // ring id -> { g, ring, glyph, t, d, r, warned }
const bursts = []; // pillars fading out
let readyAt = 0, ringTex = null;
const SLOW = Math.max(1, Number(new URLSearchParams(location.search).get('gavelslow')) || 1); // test knob: ?gavelslow=40 holds the pillar on screen (slow headless browsers skip it)

// the ring on the floor: a thick gold band with tick marks and a pair of scales in the middle
function tex() {
  if (ringTex) return ringTex;
  const cv = document.createElement('canvas'); cv.width = cv.height = 256;
  const x = cv.getContext('2d');
  x.translate(128, 128);
  x.strokeStyle = '#ffc83a'; x.lineWidth = 12; x.beginPath(); x.arc(0, 0, 116, 0, 7); x.stroke();
  x.lineWidth = 4; x.beginPath(); x.arc(0, 0, 96, 0, 7); x.stroke();
  for (let i = 0; i < 24; i++) { x.rotate(Math.PI / 12); x.fillStyle = i % 2 ? '#ffe14d' : '#ffc83a'; x.fillRect(-3, -108, 6, i % 6 === 0 ? 22 : 10); }
  x.lineWidth = 7; x.lineCap = 'round';
  x.beginPath(); x.moveTo(0, -52); x.lineTo(0, 50); x.moveTo(-26, 52); x.lineTo(26, 52); x.moveTo(-50, -34); x.lineTo(50, -34); x.stroke(); // post, foot, beam
  for (const s of [-1, 1]) { x.beginPath(); x.moveTo(s * 50, -34); x.lineTo(s * 68, 6); x.moveTo(s * 50, -34); x.lineTo(s * 32, 6); x.stroke(); x.beginPath(); x.arc(s * 50, 6, 20, 0, Math.PI); x.stroke(); } // pans
  ringTex = new THREE.CanvasTexture(cv); ringTex.colorSpace = THREE.SRGBColorSpace;
  return ringTex;
}
const glow = (map, color, opacity) => new THREE.MeshBasicMaterial({ map, color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, toneMapped: false, fog: false });

function open(m) {
  const r = Number(m.r) || GAVEL.r, d = Math.max(0.2, Math.min(5, Number(m.d) || GAVEL.delay));
  const g = new THREE.Group();
  g.position.set(m.p[0], m.p[1] + 0.06, m.p[2]);
  const ring = new THREE.Mesh(new THREE.PlaneGeometry(r * 2.1, r * 2.1), glow(tex(), 0xffffff, 0.95)); ring.rotation.x = -Math.PI / 2; g.add(ring);
  const close = new THREE.Mesh(new THREE.RingGeometry(0.96, 1, 40), glow(null, WHITE, 0.9)); close.rotation.x = -Math.PI / 2; close.position.y = 0.02; g.add(close); // shrinks onto the ring: that's the clock
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.98, r * 0.98, 26, 28, 1, true), glow(null, GOLD, 0.1)); shaft.position.y = 13; g.add(shaft); // a faint column so you can see it from across the map
  G.scene.add(g);
  live.set(m.gid, { g, ring, close, shaft, t: 0, d, r, warned: false });
  sfx.gavelCall(m.p);
}
function strike(m) {
  const L = live.get(m.gid);
  if (L) { G.scene.remove(L.g); L.g.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); } }); live.delete(m.gid); }
  const r = Number(m.r) || GAVEL.r, p = m.p;
  const g = new THREE.Group(); g.position.set(p[0], p[1], p[2]);
  const core = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.55, r * 0.55, 60, 20, 1, true), glow(null, 0xffffff, 1)); core.position.y = 30; g.add(core);
  const halo = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 60, 24, 1, true), glow(null, GOLD, 0.6)); halo.position.y = 30; g.add(halo);
  const flash = new THREE.Mesh(new THREE.CircleGeometry(r * 1.5, 28), glow(null, WHITE, 1)); flash.rotation.x = -Math.PI / 2; flash.position.y = 0.08; g.add(flash);
  G.scene.add(g);
  bursts.push({ g, core, halo, flash, t: 0 });
  fx.spray([p[0], p[1] + 0.4, p[2]], 26, [GOLD, 0xffe14d, 0xffffff], 9, 0.9, 0.16, 9, 1.2);
  sfx.gavelBang(p);
  const d = Math.hypot(ME.pos[0] - p[0], ME.pos[2] - p[2]);
  if (d < 14) G.shake = Math.max(G.shake || 0, d < r + 1 ? 0.9 : 0.4);
  if (Array.isArray(m.hit) && m.hit.includes(G.myId)) hud.msg('JUDGED', 1.4, 'slip');
}
// right click with the scales out (main.js aimDown). true = it was ours
export function gavelAim() {
  if (W.cur !== 'scales' || !ME.alive) return false;
  const now = performance.now();
  if (now < readyAt) { sfx.empty(); return true; }
  readyAt = now + 600; // the server's answer sets the real one
  const cp = Math.cos(ME.pitch), d = [-Math.sin(ME.yaw) * cp, Math.sin(ME.pitch), -Math.cos(ME.yaw) * cp];
  net.send({ t: 'gavel', o: [ME.pos[0], ME.pos[1] + 1.6, ME.pos[2]].map((v) => Math.round(v * 100) / 100), d: d.map((v) => Math.round(v * 1000) / 1000) });
  return true;
}
export function gavelFx(m) {
  if (m.k === 'gavel') { if (Array.isArray(m.p) && m.p.length === 3 && m.p.every(Number.isFinite)) open(m); if (m.id === G.myId) hud.msg('COURT IS IN SESSION', 1, 'brag'); return true; }
  if (m.k === 'gavelx') { if (Array.isArray(m.p) && m.p.length === 3 && m.p.every(Number.isFinite)) strike(m); return true; }
  return false;
}
export function initGavel() {
  W.gavelCharge = gavelCharge;
  net.on('gavel', (m) => {
    if (m.no) { readyAt = 0; hud.msg('NOWHERE TO HOLD COURT', 0.9, 'slip'); return; }
    if (Number.isFinite(m.cd)) readyAt = performance.now() + Math.max(0, Math.min(60000, m.cd));
  });
}
// how much of the recharge is left, 0..1 (0 = ready), for the HUD meter while the scales are out
export function gavelCharge() { const left = readyAt - performance.now(); return left > 700 ? Math.min(1, left / (GAVEL.cd * 1000)) : 0; }
export function updateGavel(dt) {
  dt = Math.min(dt, 0.05); // a lag spike shouldn't eat the whole pillar
  for (const L of live.values()) {
    L.t += dt;
    const k = Math.min(1, L.t / L.d);
    L.ring.rotation.z += dt * (1.2 + k * 5);
    L.close.scale.setScalar(L.r * (2.6 - 1.6 * k));
    L.ring.material.opacity = 0.7 + 0.3 * Math.sin(L.t * 22);
    L.shaft.material.opacity = 0.1 + 0.28 * k * k;
    const inside = ME.alive && Math.hypot(ME.pos[0] - L.g.position.x, ME.pos[2] - L.g.position.z) < L.r && Math.abs(ME.pos[1] - L.g.position.y) < GAVEL.h;
    if (inside && !L.warned) { L.warned = true; hud.msg('YOU HAVE BEEN SUMMONED · MOVE', 1, 'slip'); sfx.ting(); }
    if (L.t > L.d + 1.5) { G.scene.remove(L.g); live.delete([...live].find(([, v]) => v === L)[0]); } // the strike never came (we lost the message): don't leave it lit
  }
  for (let i = bursts.length - 1; i >= 0; i--) {
    const B = bursts[i]; B.t += dt / SLOW;
    const k = B.t / 0.55;
    if (k >= 1) { G.scene.remove(B.g); B.g.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); } }); bursts.splice(i, 1); continue; }
    B.core.scale.set(1 - k * 0.9, 1, 1 - k * 0.9); B.core.material.opacity = 1 - k;
    B.halo.scale.set(1 + k * 0.5, 1, 1 + k * 0.5); B.halo.material.opacity = 0.6 * (1 - k);
    B.flash.scale.setScalar(1 + k * 1.6); B.flash.material.opacity = (1 - k) * (1 - k);
  }
}
export function gavelReset() {
  for (const L of live.values()) G.scene.remove(L.g);
  live.clear();
  for (const B of bursts) G.scene.remove(B.g);
  bursts.length = 0; readyAt = 0;
}
