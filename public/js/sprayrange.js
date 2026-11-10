// The SPRAY RANGE in Training (owner, 2026-11-07): a wall left of the firing line where S&D guns shoot with the Plant &
// Defuse gunplay (spray patterns, bloom, moving spread, the recoil you pull down against), so you can learn the sprays.
// Opt-in: only while you stand in it (map.sprayRange); the rest of Training stays chaos. The last spray's bullet holes
// stay on the wall until you start the next one, with a head-sized ring to aim at.
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { hud } from './hud.js';
import { MAPS, MAP } from '/shared/map.js';

const S = { holes: [], group: null, mapId: '', inside: false, mat: null, geo: null };
const zone = () => (G.mode === 'training' && MAPS[MAP.id] && MAPS[MAP.id].sprayRange) || null;
export function inSprayRange() {
  const z = zone();
  if (!z || !ME.alive) return false;
  const p = ME.pos;
  return p[0] >= z.min[0] && p[0] <= z.max[0] && p[1] >= z.min[1] && p[1] <= z.max[1] && p[2] >= z.min[2] && p[2] <= z.max[2];
}
function label(text, w, h, size, color) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d');
  g.fillStyle = 'rgba(18,8,24,0.92)'; g.fillRect(0, 0, w, h);
  g.strokeStyle = '#ff4fd8'; g.lineWidth = 10; g.strokeRect(5, 5, w - 10, h - 10);
  g.fillStyle = color; g.font = `bold ${size}px "Comic Neue", sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  text.split('\n').forEach((t, i, a) => g.fillText(t, w / 2, h / 2 + (i - (a.length - 1) / 2) * size * 1.15));
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace;
  return new THREE.Mesh(new THREE.PlaneGeometry(w / 100, h / 100), new THREE.MeshBasicMaterial({ map: tx, transparent: true }));
}
// the sign over the wall + a head-sized ring at eye height opposite the firing spot
function build(z) {
  const g = new THREE.Group();
  const sign = label('SPRAY RANGE\nhold fire, pull down', 900, 220, 72, '#ffe14d');
  sign.position.set(z.stand[0], 7.3, z.wall + 0.3); g.add(sign);
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.11, 0.135, 32), new THREE.MeshBasicMaterial({ color: 0x4fd8ff }));
  ring.position.set(z.stand[0], z.stand[1] + 1.6, z.wall + 0.02); g.add(ring);
  const dot = new THREE.Mesh(new THREE.CircleGeometry(0.03, 12), new THREE.MeshBasicMaterial({ color: 0xffffff }));
  dot.position.copy(ring.position); g.add(dot);
  G.scene.add(g);
  S.group = g;
  S.geo = new THREE.CircleGeometry(0.045, 8);
  S.mat = new THREE.MeshBasicMaterial({ color: 0xff00dc }); // hot pink: readable on the grey stone from the firing line
}
function clearHoles() { for (const h of S.holes) S.group.remove(h); S.holes.length = 0; }
// weapons.js: a spray-range shot hit the world at p (normal n). i = which shot of the spray (0 = a new spray: wipe the wall)
export function sprayHole(p, n, i) {
  const z = zone();
  if (!z || !S.group || Math.abs(p[2] - z.wall) > 0.4 || n[2] < 0.5) return; // only holes on the wall's face
  const now = performance.now();
  if (i === 0 && now - (S.lastT || 0) > 1000) clearHoles(); // a new spray after a real pause wipes the wall
  S.lastT = now;
  const m = new THREE.Mesh(S.geo, S.mat);
  m.position.set(p[0], p[1], z.wall + 0.015 + S.holes.length * 0.0004);
  S.group.add(m); S.holes.push(m);
  if (S.holes.length > 120) S.group.remove(S.holes.shift());
}
// every frame: build the sign once per map visit, say when you walk in
export function sprayRangeFrame() {
  const z = zone();
  if (!z) { if (S.group) { clearHoles(); G.scene.remove(S.group); S.group = null; } S.inside = false; return; }
  if (!S.group || !S.group.parent) build(z);
  const inside = inSprayRange();
  if (inside && !S.inside) hud.msg('SPRAY RANGE: S&D GUNS USE S&D RECOIL HERE', 2.2, 'brag');
  S.inside = inside;
}
