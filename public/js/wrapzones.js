// Wrap zones: which part of a weapon a wrap paints.
//   A = the handle side (grip, stock, body, furniture, the stick of a slapper)
//   B = the business end (blade, barrel, slide, metal bits, the hand of a slapper)
//   N = decals and little trims that keep their own look unless the wrap is on FULL
//   AB = one-piece things (a card, an ice cube): both modes paint them
// Wrap modes (5th skin slot): normal paints A, reverse paints B, full paints everything (the old look).
//
// How a mesh gets its zone, first match wins:
//  1. o.userData.wz = 'a' | 'b' | 'n' | 'ab' set where the mesh is built
//  2. its name, or a parent's name up to the weapon: a `_wzA` / `_wzB` / `_wzN` / `_wzAB` suffix. Blender / glb models
//     use this (name the object e.g. `slide_wzB`, `grip_wzA`; Blender's `.001` style tails after it are fine)
//  3. the hand-made rule for that model below: (colour, centre, size) in weapon space (-z = muzzle, +y = up)
//  4. fallback for anything new: steel / black / grey parts -> B, coloured parts -> A
import * as THREE from 'three';
import { WRAP_MODES } from '/shared/cosmetics.js';

export { WRAP_MODES };
export const WRAP_MODE_NAMES = { normal: 'Normal', reverse: 'Reverse', full: 'Full' };

const A = 'a', B = 'b', N = 'n', AB = 'ab';
const is = (c, ...l) => l.includes(c);

// key = weapon id for its standard model, or the skin model id. c = original colour (hex), p = centre, s = size
const RULES = {
  // ---------------- guns: body / stock / grip = A, barrel / slide / mag / sights = B
  ar: (c, p) => is(c, 0x3b4a2a) || (c === 0x222222 && p.z > 0) ? A : B,
  ar_toy: (c, p) => is(c, 0x4fd8ff, 0xff4fd8) ? A : B,
  ar_bullpup: (c, p) => c === 0x2a2a30 || (c === 0x222222 && p.z < 0.05) ? A : B,
  smg: (c, p) => is(c, 0x2a2a35, 0x555566) || (c === 0x111111 && p.z > 0) ? A : B,
  smg_uzi: (c) => c === 0x222228 ? A : B, // the box body vs grip-mag, barrel + top cover
  redline: (c, p) => c === 0x24262d || (c === 0x151515 && (p.z > 0.1 || p.y > -0.11)) ? A : B, // racing stripes ride with the barrel
  redline_hotrod: (c, p) => c === 0xc8ccd4 || (c === 0x2a2a2e && (p.z > 0.1 || p.y > -0.11)) ? A : B, // flames ride with the pipes
  shotgun: (c) => c === 0x8a5a2b ? A : B, // wood pump + stock vs the steel
  shotgun_double: (c) => c === 0x6b3a1a ? A : B,
  minigun: (c) => is(c, 0x4a4a4a, 0x222222, 0x6b5a2a) ? A : B,
  minigun_gatling: (c) => is(c, 0x5a4a2a, 0x3a2a1a) ? A : B,
  revolver: (c) => is(c, 0x777777, 0x6b3a1a) ? A : B, // frame + grip vs barrel + cylinder
  revolver_flint: (c) => c === 0x6b3a1a ? A : B,
  sniper: (c) => is(c, 0x2b2b2b, 0x5a3a1a, 0x222222) ? A : B,
  sniper_musket: (c) => c === 0x6b3a1a ? A : B,
  marbles: (c) => is(c, 0x6b3a1a, 0x1a1a1a) ? A : B, // wood vs brass bell + jar lid
  marbles_gumball: (c) => c === 0xd01c2a ? A : B, // red machine vs the chrome
  chicken: (c) => c === 0x3d7a2a ? A : B, // the tube vs grip + the chicken poking out
  chicken_turkey: (c) => c === 0x6b4a2a ? A : B, // tube vs grip, ring + tail fan
  bowling: (c) => c === 0x2a2a3a ? A : B, // the tube vs grip + muzzle rings
  bowling_cannon: (c, p) => c === 0x6b3a1a || (c === 0x2a2a2a && p.z > 0.05) ? A : c === 0xff7a1a ? N : B, // grip + breech vs the barrel
  banana: (c) => is(c, 0x8a5a2b, 0x5a3a1a) ? A : B, // the gun vs its bananas
  banana_bunch: (c) => is(c, 0x6b4a2a, 0x333333) ? A : B,
  shredder: (c, p) => is(c, 0x3d4452, 0x1a1a1a, 0xd01c1c) ? A : B, // motor + handles vs rotor cage + yellow intake
  shredder_chipper: (c, p) => is(c, 0x3a7a2a, 0x8a5a2b, 0xd01c1c) || (p.z > 0.05 && !is(c, 0x22301c)) ? A : B, // body + engine vs hopper
  blower: (c, p) => c === 0x9a9a9a || p.z < -0.6 ? B : A, // leaf blower body vs its tube
  blower_dryer: (c, p) => c === 0xffffff ? N : p.y < -0.08 ? A : B, // handle vs barrel + nozzle
  scythe: (c) => c === 0x9aa4b0 ? B : A, // the gun-pole vs the blade
  scythe_rifle: (c) => c === 0x9aa4b0 ? B : A,
  scythe_reaper: (c, p) => c === 0xe8e4d8 && p.z < -0.5 ? B : A, // black pole (+ bone butt) vs the bone blade
  // ---------------- blades: handle + guard = A, blade (+ the habaki collar) = B
  knife: (c, p) => p.z < -0.045 ? B : A,
  knife_kitchen: (c, p) => p.z < -0.08 ? B : A,
  knife_bowie: (c, p) => p.z < -0.06 ? B : A,
  knife_cleaver: (c) => is(c, 0xcdd3da, 0xf6f8fa) ? B : A,
  knife_switch: (c, p) => p.z < -0.035 ? B : A,
  knife_karambit: (c, p) => p.z < -0.045 ? B : A,
  knife_butterfly: (c, p) => p.z < -0.045 ? B : A,
  katana: (c, p) => c === 0xf4f6f8 || c === 0xc9963f ? B : A,
  katana_shirasaya: (c) => c === 0xf4f6f8 || c === 0xc9963f ? B : A,
  katana_bokken: (c) => c === 0xb8714a ? B : A,
  // ---------------- melee + novelty: the bit you hold = A, the bit that hits = B
  slapper: (c) => c === 0xffe14d ? A : B,
  slapper_foam: (c) => c === 0x4fd8ff ? A : c === 0xffffff ? N : B,
  slapper_paw: (c) => c === 0x6b3a1a ? A : c === 0x5a3a20 ? B : N, // claws + pad stay
  bread: (c) => c === 0xd9a35b ? A : B, // the loaf vs its crust ends + score marks
  bread_croissant: (c) => c === 0xc8904a ? A : B, // alternate rolls
  spoon: (c) => c === 0xd8d8e0 ? A : B,
  spoon_ladle: (c) => c === 0xc8c8d0 ? A : B,
  bow: (c) => c === 0x5a3a1a || c === 0xc8a070 ? A : c === 0xff4fd8 ? N : B, // riser + arrow vs limbs + string
  bow_compound: (c) => c === 0x2a2a30 || c === 0x333333 ? A : is(c, 0x7dff4f, 0x4fd8ff) ? N : B,
  scales: (c, p) => is(c, 0xd8202a, 0xf6f6f6, 0xd8c8a0) ? N : p.y > 0.25 ? B : A, // handle + pillar vs beam, chains, pans
  scales_kangaroo: (c, p) => is(c, 0xb5651d, 0x8a4a14, 0xf4f4f4) ? N : p.y > 0.25 ? B : A, // the judge stays a kangaroo
  bloodcross: (c, p) => p.z < -0.04 || p.y > 0.035 ? B : A, // palm vs the finger barrel + thumb hammer
  bloodcross_shadow: (c, p) => p.z < -0.04 || p.y > 0.035 ? B : A,
  claw: (c) => is(c, 0x6f9a3a, 0x4a5a3a) ? A : B, // arm vs fingers + nails
  cig: (c) => c === 0xd98b3a ? A : B, // filter vs paper (also every plain item)
  cig_cigar: (c) => c === 0xc02030 ? A : B, // the band vs the leaf
  popper: (c) => is(c, 0xff6bd0, 0xffffff) ? A : B, // cone vs its rings
  popper_bottle: (c) => c === 0x2a5a2a ? A : B, // the glass vs foil + label
  duck: (c, p) => c === 0xffd23b && p.y < 0.05 ? A : B, // body vs head + beak
  slipper: (c) => c === 0xc85a8a ? A : B, // sole vs strap
  slipper_croc: (c, p) => c === 0x3a8a2a ? N : p.z > -0.08 ? A : B, // heel vs the toe
  snowball: (c) => c === 0xf2f8ff ? A : B,
  snowball_ice: () => AB,
  reverse: () => AB,
  reverse_skip: () => AB,
};

// fallback for meshes no rule knows: steel / greys / black read as "metal" (B), anything coloured is A
const hsl = {};
export function guessZone(color) {
  if (!color) return A;
  color.getHSL(hsl);
  return hsl.s < 0.2 || hsl.l < 0.12 ? B : A;
}

const NAME_RE = /_wz(ab|a|b|n)(?![a-z])/i;
export function nameZone(o, root) {
  for (let x = o; x && x !== root; x = x.parent) {
    const m = x.name && NAME_RE.exec(x.name);
    if (m) return m[1].toLowerCase();
  }
  return null;
}

const inv = new THREE.Matrix4(), mm = new THREE.Matrix4(), box = new THREE.Box3(), ctr = new THREE.Vector3(), sz = new THREE.Vector3();
// zone of every mesh, worked out once per built weapon. key = model id (or weapon id), color = its original colour
export function zoneOf(o, g, key, color) {
  if (o.userData.wz) return o.userData.wz;
  const n = nameZone(o, g);
  if (n) return n;
  const rule = RULES[key];
  if (!rule) return guessZone(color);
  if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
  mm.multiplyMatrices(inv.copy(g.matrixWorld).invert(), o.matrixWorld);
  box.copy(o.geometry.boundingBox).applyMatrix4(mm);
  box.getCenter(ctr); box.getSize(sz);
  return rule(color ? color.getHex() : 0xffffff, ctr, sz, o);
}
// does this wrap mode paint a mesh in that zone
export const paints = (mode, zone) => mode === 'full' || (zone === AB) || (mode === 'normal' ? zone === A : zone === B);
