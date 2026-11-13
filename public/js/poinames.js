// FLOATING POI NAMES (Jank Royale / Battle Island): a big comic location name hangs over each POI in the world,
// readable from the blimp and while you glide down, fading out as you land so it's gone once you're fighting on foot.
// Billboard sprites with the POI's own colour, built once per map. royale.js drives it from brFrame (poiNamesFrame).
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { RP } from './replay.js';
import { MAPS, BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';

let group = null, sprites = [], forMap = '';
function tex(name, color) {
  const pad = 24, c = document.createElement('canvas'), x = c.getContext('2d');
  x.font = 'bold 120px "Comic Neue", "Comic Sans MS", sans-serif';
  const w = Math.ceil(x.measureText(name).width) + pad * 2, h = 180;
  c.width = w; c.height = h;
  x.font = 'bold 120px "Comic Neue", "Comic Sans MS", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.lineJoin = 'round';
  const cx = w / 2, cy = h / 2;
  x.lineWidth = 26; x.strokeStyle = '#ff00dc'; x.strokeText(name, cx + 7, cy + 8); // the hard offset shadow
  x.lineWidth = 20; x.strokeStyle = '#000'; x.strokeText(name, cx, cy);
  x.fillStyle = color || '#ffe14d'; x.fillText(name, cx, cy);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return { t, aspect: w / h };
}
// ground under a world point (for the name's height): the first thing straight down from high up
function groundY(x, z) { const top = 400, h = raycast([x, top, z], [0, -1, 0], 900, BOXES); return h ? top - h.t : 0; }
function build(id) {
  dispose();
  const map = MAPS[id], pois = map && map.royale && map.royale.pois;
  if (!pois) return;
  group = new THREE.Group(); group.name = 'br_poinames'; // (br_: the screenshot tools hide it)
  for (const p of pois) {
    const cx = p.c ? p.c[0] : (p.rect[0] + p.rect[2]) / 2, cz = p.c ? p.c[1] : (p.rect[1] + p.rect[3]) / 2;
    const base = p.c && Number.isFinite(p.y) ? p.y : groundY(cx, cz);
    const { t, aspect } = tex(p.name.toUpperCase(), p.color || '#ffe14d');
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false, depthTest: false, fog: false, sizeAttenuation: true }));
    const H = Math.min(16, 78 / aspect); // metres tall; a long name shrinks so it never gets wider than ~78 m
    sp.scale.set(H * aspect, H, 1);
    sp.position.set(cx, base + 38, cz);
    sp.renderOrder = 998;
    group.add(sp); sprites.push(sp);
  }
  G.scene.add(group);
  forMap = id;
}
function dispose() {
  if (group) { for (const s of sprites) { s.material.map.dispose(); s.material.dispose(); } G.scene.remove(group); }
  group = null; sprites = []; forMap = '';
}
export function poiNamesReset() { dispose(); }

// show them while you're up high (in the blimp, or gliding), fade with how far you've dropped toward the ground
const tmp = new THREE.Vector3();
export function poiNamesFrame(R, now) {
  const want = R.on && !RP.active && ME.alive && (R.me.inBlimp || !!R.me.fly);
  if (!want) { if (group) group.visible = false; return; }
  if (forMap !== G.cfg.map) build(G.cfg.map);
  if (!group) return;
  group.visible = true;
  // how high are you? fully shown from ~90 m up, gone by ~18 m (about where the umbrella's done its job)
  const gy = groundY(ME.pos[0], ME.pos[2]), up = ME.pos[1] - gy;
  const alt = Math.max(0, Math.min(1, (up - 18) / 72));
  for (const s of sprites) {
    const d = Math.hypot(s.position.x - ME.pos[0], s.position.z - ME.pos[2]);
    const near = Math.max(0, Math.min(1, (d - 8) / 22)); // right on top of one: don't shove it in your face
    const far = 0.45 + 0.55 * Math.max(0, Math.min(1, (620 - d) / 420)); // from the blimp you can still read the whole map
    s.material.opacity = alt * near * far;
    s.visible = s.material.opacity > 0.02;
    if (s.visible) { const base = s.userData.base ?? s.position.y; s.userData.base = base; s.position.y = base + Math.sin(now * 0.001 + base) * 0.6; } // a lazy bob
  }
}
