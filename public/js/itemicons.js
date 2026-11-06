// Item and killstreak pictures, rendered from their real 3D models in the icon studio (icons.js studioIcon: one light
// rig, a 3/4 view, an ink outline, a hard shadow in the item's colour). Blender models where there are some (the grenade,
// duck, smoke bomb, popper, reverse card, camera, calculator, goggles, wand, the wrecking ball, the rig, the scythe;
// tools/blender/make_icons.py made the moon boots, spinbot shades, satellite, medkit, shield bubble, the chicken strike's
// target and the duck's black hole). While a model downloads the picture is the loading cube; the old 2D drawings
// (icons.js itemIcon2d / streakIcon2d) only come back if WebGL can't draw them. Cached like every other icon.
import * as THREE from 'three';
import { ITEMS } from '/shared/weapons.js';
import { studioIcon, itemIcon, set3dPics } from './icons.js';
import { buildProjectile, buildWeapon, freeTree } from './models.js';
import { authored } from './glbkit.js';
import { instantCamera, calculator, lcdTexture, nvGoggles } from './gearmodels.js';
import { wandMesh } from './wand.js';

const A = (id) => { const b = authored(id); return b ? b.obj : null; };
const grp = (...o) => { const g = new THREE.Group(); for (const x of o) if (x) g.add(x); return g; };
// all the parts or nothing (a half-built picture is worse than the drawing)
const all = (parts, make) => (parts.every(Boolean) ? make(...parts) : (parts.forEach((p) => p && freeTree(p)), null));

// killstreaks: the model, its colour (shadow + rim light), and how it faces the camera
const STREAK = {
  moonboots: { c: '#b0b8ff', b: () => A('x_moonboots'), yaw: 2.3 },
  chickenstrike: { c: '#ff3030', b: () => all([A('x_target'), buildProjectile('chicken')], (t, ch) => { ch.position.set(0.02, 0.42, 0.12); ch.rotation.set(-0.9, Math.PI - 0.5, 0); ch.scale.setScalar(1.25); return grp(t, ch); }), yaw: 0, pitch: 0.75 },
  scythe: { c: '#3ee6c8', b: () => buildWeapon('scythe'), yaw: -1.35, roll: 0.55 },
  overdrive: { c: '#ff2bd6', b: () => A('x_rig'), yaw: 2.6, rim: '#2ef2ff' },
  spinbot: { c: '#ff4fd8', b: () => A('x_spinbot'), yaw: 2.95, pitch: 0.08 },
  wreckingball: { c: '#ffe14d', b: () => A('x_wreck'), yaw: 2.7 },
  satellite: { c: '#4fa8ff', b: () => A('x_satellite'), yaw: 2.5, pitch: 0.35 },
  giantduck: { c: '#b07dff', b: () => all([A('x_blackhole'), buildProjectile('duck')], (h, d) => { d.scale.setScalar(0.55); d.position.set(-0.34, 0.06, 0.26); d.rotation.y = Math.PI - 0.9; return grp(h, d); }), yaw: 0, pitch: 0.22 },
};
export function streakPic(id) {
  const s = STREAK[id];
  return s ? studioIcon('streak3d:' + id, s.b, { w: 96, h: 96, accent: s.c, yaw: s.yaw, pitch: s.pitch, roll: s.roll, rim: s.rim }) : '';
}

// items: 96 x 60 like the old drawings (the HUD and the loadout tiles size them)
const GEAR = {
  frag: () => buildProjectile('frag'), smoke: () => buildProjectile('smokegren'), duck: () => buildProjectile('duck'),
  camera: () => instantCamera(), quiz: () => calculator(lcdTexture(['80085', ''])), nvg: () => nvGoggles(),
  wand: () => wandMesh(), medkit: () => A('x_medkit'), bubble: () => A('x_bubble'),
};
const ITEM_VIEW = { wand: { yaw: 2.8, roll: -0.35 }, quiz: { yaw: 2.8, pitch: 0.55 }, nvg: { yaw: 2.6 }, bubble: { pitch: 0.3 }, medkit: { yaw: 2.65, pitch: 0.3 } };
export function item3d(id, skin) {
  const it = ITEMS[id];
  if (!it) return '';
  const v = ITEM_VIEW[id] || {}, o = { w: 96, h: 60, accent: it.color, yaw: v.yaw, pitch: v.pitch, roll: v.roll };
  if (it.w) return studioIcon('item3d:' + id + '|' + (Array.isArray(skin) ? skin.join(',') : ''), () => buildWeapon(it.w, skin), { ...o, yaw: v.yaw ?? -1.2 }); // popper / reverse / radar: the real thing, your skin and all
  return GEAR[id] ? studioIcon('item3d:' + id, GEAR[id], o) : '';
}
set3dPics(streakPic, item3d);

export function itemPic(id, skin) { return item3d(id, skin) || itemIcon(id); }
