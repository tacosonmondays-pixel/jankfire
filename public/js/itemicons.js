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
import { authored, nodeIn } from './glbkit.js';
import { instantCamera, calculator, lcdTexture, nvGoggles } from './gearmodels.js';
import { wandMesh } from './wand.js';
import { lookModel, modelOf, paintLook, wreckShell } from './streaklooks.js'; // killstreak looks
import { G } from './ctx.js';

const A = (id) => { const b = authored(id); return b ? b.obj : null; };
const grp = (...o) => { const g = new THREE.Group(); for (const x of o) if (x) g.add(x); return g; };
// all the parts or nothing (a half-built picture is worse than the drawing)
const all = (parts, make) => (parts.every(Boolean) ? make(...parts) : (parts.forEach((p) => p && freeTree(p)), null));

// killstreaks: the model, its colour (shadow + rim light), and how it faces the camera. sk = the streak's look
// (streaklooks.js): its own model if it has one (the default until that file lands), in its wrap
const fitTo = (o, size) => { const bx = new THREE.Box3().setFromObject(o), v = bx.getSize(new THREE.Vector3()); o.scale.multiplyScalar(size / Math.max(v.x, v.y, v.z, 1e-3)); return o; };
const alt = (sk, id) => lookModel(modelOf(sk, id));
const STREAK = {
  moonboots: { c: '#b0b8ff', b: (sk) => alt(sk, 'moonboots') || A('x_moonboots'), yaw: 2.3 },
  chickenstrike: { c: '#ff3030', b: (sk) => { const v = alt(sk, 'chickenstrike'); return all([A('x_target'), v ? fitTo(v, 0.8) : buildProjectile('chicken')], (t, ch) => { ch.position.set(0.02, 0.42, 0.12); ch.rotation.set(-0.9, Math.PI - 0.5, 0); if (!v) ch.scale.setScalar(1.25); if (sk) paintLook(ch, sk); return grp(t, ch); }); }, yaw: 0, pitch: 0.75, own: true },
  scythe: { c: '#3ee6c8', b: (sk) => buildWeapon('scythe', sk), yaw: -1.35, roll: 0.55, own: true },
  overdrive: { c: '#ff2bd6', b: () => A('x_rig'), yaw: 2.6, rim: '#2ef2ff' },
  spinbot: { c: '#ff4fd8', b: (sk) => alt(sk, 'spinbot') || A('x_spinbot'), yaw: 2.95, pitch: 0.08 },
  wreckingball: { c: '#ffe14d', b: (sk) => { const o = A('x_wreck'); if (o && sk) wreckShell(o, sk); return o; }, yaw: 2.7, own: true },
  satellite: { c: '#4fa8ff', b: (sk) => alt(sk, 'satellite') || A('x_satellite'), yaw: 2.5, pitch: 0.35 },
  giantduck: { c: '#b07dff', b: (sk) => { const v = alt(sk, 'giantduck'); return all([A('x_blackhole'), v ? fitTo(v, 0.5) : buildProjectile('duck')], (h, d) => { if (!v) d.scale.setScalar(0.55); d.position.set(-0.34, 0.06, 0.26); d.rotation.y = Math.PI - 0.9; if (sk) paintLook(d, sk); return grp(h, d); }); }, yaw: 0, pitch: 0.22, own: true },
};
// the streak's model in a look, for the big Customize view (preview.js); a Group either way
export function streakModel(id, sk) {
  const s = STREAK[id], look = Array.isArray(sk) ? sk : null;
  const o = s && s.b(look);
  if (o && look && !s.own) paintLook(o, look);
  const g = new THREE.Group(); if (o) g.add(o);
  return g;
}
// skin: the look to draw (default: what you wear)
export function streakPic(id, skin) {
  const s = STREAK[id];
  if (!s) return '';
  const sk = skin !== undefined ? skin : (G.equipped || {})[id];
  const look = Array.isArray(sk) ? sk : null;
  return studioIcon('streak3d:' + id + (look ? '|' + look.join(',') : ''), () => { const o = s.b(look); if (o && look && !s.own) paintLook(o, look); return o; }, { w: 96, h: 96, accent: s.c, yaw: s.yaw, pitch: s.pitch, roll: s.roll, rim: s.rim });
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

// the Customize buttons' props (tools/blender/make_uiicons.py: one file, a node each): backpack, door, wrench, palette,
// crystal, skull. accent = the shadow colour; hub.js and customize.js put them on the tab bar and the round buttons
const UI_VIEW = { ui_backpack: { yaw: 2.6 }, ui_door: { yaw: 2.75, pitch: 0.2 }, ui_wrench: { yaw: 3.0, pitch: 0.1, roll: -0.7 }, ui_palette: { yaw: 3.0, pitch: 0.5 }, ui_crystal: { yaw: 2.9, pitch: 0.15 }, ui_skull: { yaw: 2.75, pitch: 0.15 } };
export function uiPic(name, accent = '#4fd8ff', size = 40) {
  const v = UI_VIEW[name] || {};
  return studioIcon('ui:' + name + accent + size, () => {
    const all = A('x_uiicons'); if (!all) return null;
    const n = nodeIn(all, name); if (!n) return null;
    n.removeFromParent(); n.position.set(0, 0, 0);
    return n;
  }, { w: size, h: size, accent, yaw: v.yaw, pitch: v.pitch, roll: v.roll });
}
