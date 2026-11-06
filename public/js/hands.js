// PS1-style low-poly hands for every first-person viewmodel: chunky blocks (a palm, a two-joint thumb, four fingers of
// three segments each, little nail chips) and a short cuff instead of a forearm. ~260 tris a hand, flat shaded, a tiny
// 8x8 texture for creases + knuckles, and the game's vertex snap (jank.js), so Potato makes them wobble.
// One rig, posed by numbers: each finger curls round a grip of radius r (the joints bend by the angle a segment spans
// on that circle, so the fingertips really land on the handle), and the named poses are just curl amounts:
//   grip  fist round a handle (the default), trigger  the index off the grip onto a trigger,
//   point index straight, open  a flat-ish hand, pinch  index + thumb nearly meeting (cards, a shell, a juice box)
// Hand space: the gripped thing's axis is +Y, its centre is the origin; for a right hand the back of the hand faces
// +X / +Z and the fingers wrap round the front (-Z) to the left. Left hands are the mirror (built mirrored, not scaled).
// aimHand() points a hand at a grip: axis = the handle's direction, back = which way the back of the hand faces.
import * as THREE from 'three';
import { jankify } from './jank.js';
import { G } from './ctx.js';

const PI = Math.PI;
const W = 0.0118, TH = 0.0112; // a finger's width (along the grip) and thickness
const SEG = { index: [0.022, 0.016, 0.014], middle: [0.024, 0.017, 0.014], ring: [0.022, 0.016, 0.013], pinky: [0.017, 0.013, 0.011] };
const ORDER = ['index', 'middle', 'ring', 'pinky']; // top of the grip to the bottom
const THUMB = [0.022, 0.018];
const PALM = { h: 0.05, t: 0.016 }; // along the grip, thickness (back of the hand)
const PHI_BACK = -0.72; // the back of the hand sits at this angle round the grip (0 = +X, +90deg = the front, -Z)

// ------------------------------------------------------------ look: skin from your character, cuff from your top
const mats = new Map();
let tex = null;
function crease() { // 8x8: a lit middle, darker rim + a crease line: on a box it reads as knuckles / creases at PS1 res
  if (tex) return tex;
  const c = document.createElement('canvas'); c.width = c.height = 8;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 8, 8);
  g.fillStyle = '#d9d0c8'; g.fillRect(0, 0, 8, 1); g.fillRect(0, 7, 8, 1); g.fillRect(0, 0, 1, 8); g.fillRect(7, 0, 1, 8);
  g.fillStyle = '#c4b8ad'; g.fillRect(0, 3, 8, 1);
  g.fillStyle = '#ece6e0'; g.fillRect(2, 1, 1, 1); g.fillRect(5, 5, 1, 1); // a couple of dither specks
  tex = new THREE.CanvasTexture(c);
  tex.magFilter = THREE.NearestFilter; tex.minFilter = THREE.NearestFilter; tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
function mat(color, textured = true) {
  const k = color + (textured ? 't' : '');
  if (!mats.has(k)) { const m = jankify(new THREE.MeshLambertMaterial({ color, flatShading: true, map: textured ? crease() : null })); m.userData.shared = true; mats.set(k, m); }
  return mats.get(k);
}
const hex = (c, d) => { try { return new THREE.Color(c).getHex(); } catch { return d; } };
const SLEEVES = { hoodie: 1, jacket: 1, suit: 1, runner: 1, maid: 1, tee: 0.5 };
export function handLook() {
  const lk = (G.settings && G.settings.look) || {};
  const skin = lk.skin ? hex(lk.skin, 0xe6cba2) : 0xe6cba2; // the mannequin tone when you haven't picked one
  const sl = SLEEVES[lk.top];
  const cuff = sl ? hex(lk.topColor || (lk.top === 'runner' ? '#f2d02a' : lk.top === 'maid' ? '#17141c' : lk.color) || '#2a2440', 0x2a2440) : new THREE.Color(skin).multiplyScalar(0.8).getHex(); // bare arms: just the wrist (a darker end so it reads as cut off)
  return { skin, knuck: new THREE.Color(skin).multiplyScalar(0.86).getHex(), nail: new THREE.Color(skin).lerp(new THREE.Color(0xffffff), 0.45).getHex(), cuff, sleeve: !!sl };
}

// ------------------------------------------------------------ build
const geo = new Map();
const boxG = (w, h, d) => { const k = `${w},${h},${d}`; if (!geo.has(k)) { const g = new THREE.BoxGeometry(w, h, d); g.userData.shared = true; geo.set(k, g); } return geo.get(k); };
function block(w, h, d, m, x = 0, y = 0, z = 0) { const o = new THREE.Mesh(boxG(w, h, d), m); o.position.set(x, y, z); o.userData.noWrap = true; o.userData.hand = true; return o; }

// a finger: a chain of segment groups. each joint turns about Y (the grip's axis), so curling wraps it round the grip.
// fwd = which way it points before any bend (-Z for fingers, +Z for the thumb going round the back)
function chain(lens, w, t, L, nailOn, fwd, sx) {
  const root = new THREE.Group(), joints = [];
  let parent = root;
  lens.forEach((len, i) => {
    const j = new THREE.Group(); parent.add(j); joints.push(j);
    if (i) j.position.z = fwd * lens[i - 1];
    const k = 1 - i * 0.06; // a touch thinner toward the tip
    j.add(block(t * k, w * k, len + 0.002, i ? L.skinM : L.knuckM, 0, 0, fwd * len / 2)); // (x = thickness: the joints turn about Y)
    if (i === lens.length - 1 && nailOn) j.add(block(0.0022, w * k * 0.68, len * 0.55, L.nailM, sx * t * k / 2, 0, fwd * len * 0.6)); // the nail, on the outside
    parent = j;
  });
  return { root, joints, lens, fwd };
}

export function makeHand(side = 'R', opts = {}) {
  const sx = side === 'L' ? -1 : 1, lk = handLook();
  const L = { skinM: mat(lk.skin), knuckM: mat(lk.knuck), nailM: mat(lk.nail, false), cuffM: mat(lk.cuff) };
  const h = new THREE.Group(); h.userData.hand = { side, sx, fingers: {}, thumb: null, r: opts.r ?? 0.016, arm: opts.arm || [0.35, -0.3, 1] };
  const body = new THREE.Group(); h.add(body); h.userData.hand.body = body;
  // palm / back of the hand: one slab tangent to the grip at PHI_BACK
  const palm = block(0.034, PALM.h, PALM.t, L.skinM); // (mirrored in pose(), never by a negative scale: that turns faces inside out)
  palm.userData.palm = true; body.add(palm); h.userData.hand.palm = palm;
  const kn = block(0.03, 0.006, 0.008, L.knuckM); body.add(kn); h.userData.hand.kn = kn; // the knuckle ridge across the back
  ORDER.forEach((n, i) => {
    const c = chain(SEG[n], W, TH, L, true, -1, sx);
    c.y = 0.0185 - i * 0.0128 - (n === 'pinky' ? 0.001 : 0);
    body.add(c.root); h.userData.hand.fingers[n] = c;
  });
  const th = chain(THUMB, 0.013, 0.0125, L, true, 1, sx);
  body.add(th.root); h.userData.hand.thumb = th;
  // the cuff: a short chunky sleeve end back along the arm
  const cuff = new THREE.Mesh(new THREE.CylinderGeometry(lk.sleeve ? 0.024 : 0.0205, lk.sleeve ? 0.026 : 0.0215, lk.sleeve ? 0.045 : 0.01, 7), L.cuffM);
  cuff.userData.noWrap = true; cuff.userData.hand = true; body.add(cuff); h.userData.hand.cuff = cuff;
  if (!lk.sleeve) { const wr = new THREE.Mesh(new THREE.CylinderGeometry(0.0175, 0.019, 0.026, 7), L.skinM); wr.userData.noWrap = true; body.add(wr); h.userData.hand.wrist = wr; }
  pose(h, opts.pose || 'grip', opts.r);
  return h;
}

// ------------------------------------------------------------ poses
// curl k per finger: 1 = wrapped round a grip of radius r. thumb: [k, lift] (lift tips it up the grip / out)
export const POSES = {
  grip: { f: [1, 1, 1, 1], t: [1, 0] },
  trigger: { f: [0.42, 1, 1, 1], t: [1, 0], idx: 0.004 }, // index out on the trigger, a bit higher
  point: { f: [0.05, 1, 1, 1], t: [0.7, 0.2] },
  open: { f: [0.18, 0.15, 0.15, 0.2], t: [0.2, 0.5] },
  pinch: { f: [0.6, 0.85, 1, 1], t: [0.9, 0.35] },
  hold: { f: [0.55, 0.62, 0.7, 0.8], t: [0.35, 0.3] }, // a loose hold (cards fan, a box): fingers behind, thumb in front
};
const chordA = (len, R) => 2 * Math.asin(Math.min(1, len / (2 * R)));
// p = a POSES name or { f: [4], t: [k, lift] }. r = the grip radius (hand units)
export function pose(h, p = 'grip', r) {
  const H = h.userData.hand; if (!H) return;
  if (r != null) H.r = r;
  const P = typeof p === 'string' ? POSES[p] || POSES.grip : p, sx = H.sx;
  const R = H.r + TH / 2 + 0.0008; // the circle the finger centres run round
  const at = (phi, rr = R) => [rr * Math.cos(phi), -rr * Math.sin(phi)]; // [x, z] on the circle
  // palm: tangent at PHI_BACK, pushed out by half its thickness
  const [px, pz] = at(PHI_BACK, H.r + PALM.t / 2 + 0.001);
  H.palm.position.set(sx * px, -0.004, pz); H.palm.rotation.set(0, sx * (PHI_BACK + PI / 2), 0);
  const [kx, kz] = at(PHI_BACK + 0.55, H.r + PALM.t + 0.0015); H.kn.position.set(sx * kx, 0.004, kz); H.kn.rotation.y = sx * (PHI_BACK + 0.55 + PI / 2);
  // fingers start at the palm's front edge and wrap forward round the grip
  const phi0 = PHI_BACK + 0.034 / 2 / (H.r + 0.008) + 0.08;
  ORDER.forEach((n, i) => {
    const c = H.fingers[n], k = P.f[i] ?? 1, [x, z] = at(phi0, R);
    c.root.position.set(sx * x, c.y + (i === 0 ? P.idx || 0 : 0), z);
    const a = c.lens.map((len) => chordA(len, R) * k);
    c.root.rotation.set(0, sx * (phi0 + a[0] / 2), 0);
    c.joints.forEach((j, s) => { if (s) j.rotation.y = sx * (a[s - 1] / 2 + a[s] / 2); });
  });
  // thumb: from the web (high up, round the back) going the other way round, toward the left side
  const [tk, tl] = P.t, tphi = PHI_BACK - 0.9, [tx, tz] = at(tphi, R + 0.001);
  const th = H.thumb, ta = th.lens.map((len) => chordA(len, R + 0.002) * tk);
  th.root.position.set(sx * tx, 0.022, tz);
  th.root.rotation.set(-0.35 - tl * 0.6, sx * (tphi - ta[0] / 2 - tl * 0.9), 0, 'YXZ');
  th.joints[1].rotation.y = -sx * (ta[0] / 2 + ta[1] / 2);
  // the cuff, back along the arm from the heel of the hand
  const arm = new THREE.Vector3(sx * H.arm[0], H.arm[1], H.arm[2]).normalize();
  // the heel: the palm's far edge from the fingers (round the back), a little low
  const [hx, hz] = at(PHI_BACK - 0.45, H.r + PALM.t * 0.6);
  const base = new THREE.Vector3(sx * hx, -0.012, hz).addScaledVector(arm, 0.006);
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), arm);
  const cl = H.cuff.geometry.parameters.height;
  if (H.wrist) { H.wrist.position.copy(base).addScaledVector(arm, 0.015); H.wrist.quaternion.copy(q); H.cuff.position.copy(base).addScaledVector(arm, 0.02 + cl / 2); }
  else H.cuff.position.copy(base).addScaledVector(arm, cl / 2 + 0.004);
  H.cuff.quaternion.copy(q);
  H.pose = P;
}

// point a hand at a grip (in its parent's space): axis = the handle's direction (where the index end of the fist goes),
// back = which way the back of the hand should face. both are bent square to each other
const mA = new THREE.Matrix4(), vX = new THREE.Vector3(), vY = new THREE.Vector3(), vZ = new THREE.Vector3(), vB = new THREE.Vector3();
export function aimHand(h, axis, back) {
  const sx = h.userData.hand ? h.userData.hand.sx : 1;
  vY.set(...axis).normalize();
  // in hand space the back of the hand points at PHI_BACK round the grip: (cos, 0, -sin), mirrored for a left hand
  const bl = new THREE.Vector3(sx * Math.cos(PHI_BACK), 0, -Math.sin(PHI_BACK));
  vB.set(...back); vB.addScaledVector(vY, -vB.dot(vY)).normalize();
  // the hand's X/Z axes are bl rotated: find the world X, Z that send bl to vB about Y
  const ang = Math.atan2(bl.x, bl.z); // bl = sin(ang) X + cos(ang) Z
  const P = new THREE.Vector3().crossVectors(vY, vB); // vY x vB: a quarter turn from vB about Y
  vX.copy(vB).multiplyScalar(Math.sin(ang)).addScaledVector(P, Math.cos(ang));
  vZ.copy(vB).multiplyScalar(Math.cos(ang)).addScaledVector(P, -Math.sin(ang));
  h.quaternion.setFromRotationMatrix(mA.makeBasis(vX, vY, vZ));
  return h;
}

// blend two poses (for animating a hand between grips): returns a pose object
export function mixPose(a, b, u) {
  const A = typeof a === 'string' ? POSES[a] : a, B = typeof b === 'string' ? POSES[b] : b;
  return { f: A.f.map((v, i) => v + (B.f[i] - v) * u), t: [A.t[0] + (B.t[0] - A.t[0]) * u, A.t[1] + (B.t[1] - A.t[1]) * u], idx: (A.idx || 0) + ((B.idx || 0) - (A.idx || 0)) * u };
}

// ------------------------------------------------------------ the viewmodel hand for each weapon
// at = where the grip's centre sits in the viewmodel's wrap space (null: the gun's own cfg.hand / handGlb / default),
// axis / back as aimHand, r = the grip radius there, pose = how it holds it, hide = no hand (it's your arm already).
// Guns default to a raked pistol grip with the index on the trigger. Weapon skins inherit their base weapon's entry
// (the hold is anchored on the base weapon's spot), unless HANDS has one for the skin's model id.
const STICK = { axis: [0, 0, -1], back: [0.75, 0.6, 0.1], pose: 'grip', arm: [0.2, -1, 0.35] }; // a handle along the gun's -Z
export const HANDS = {
  default: { axis: [0, 0.95, -0.3], back: [1, 0.1, 0.45], pose: 'trigger', r: 0.0155, arm: [0.3, -0.7, 0.75] },
  knife: { ...STICK, at: [0, 0, 0.03], r: 0.0175 }, // (grip radii are wrap space: the knife viewmodel is scaled 1.3)
  knife_kitchen: { ...STICK, at: [0, 0, 0.03], r: 0.0145 }, knife_bowie: { ...STICK, at: [0, 0, 0.03], r: 0.0165 },
  knife_cleaver: { ...STICK, at: [0, 0, 0.03], r: 0.0155 }, knife_switch: { ...STICK, at: [0, 0, 0.03], r: 0.0125 },
  knife_karambit: { ...STICK, at: [0, 0, 0.026], r: 0.0145 }, knife_butterfly: { ...STICK, at: [0, 0, 0.034], r: 0.0115 },
  knife_spoon: { ...STICK, at: [0, 0, 0.036], r: 0.0105 },
  spoon: { ...STICK, at: [0, 0, 0.036], r: 0.0115 },
  bread: { ...STICK, at: [0, 0, 0.02], r: 0.03 },
  slapper: { ...STICK, at: [0, 0, 0.06], r: 0.009 },
  scythe: { ...STICK, at: [0, -0.012, 0.15], r: 0.013 },
  scales: { axis: [0, 1, 0], back: [1, 0, 0.5], pose: 'grip', r: 0.011, at: null, arm: [0.3, -0.6, 1] },
  popper: { ...STICK, at: [0, 0, 0.06], r: 0.012 },
  cig: { axis: [0, 0, -1], back: [0.7, 0.7, 0], pose: 'pinch', r: 0.006, at: [0, -0.006, 0.05], arm: [0.2, -0.6, 1] },
  snowball: { axis: [0, 1, 0], back: [1, -0.3, 0.6], pose: 'hold', r: 0.036, at: [0.012, -0.02, -0.03], arm: [0.3, -0.5, 1] },
  duck: { axis: [0, 1, 0], back: [1, -0.3, 0.6], pose: 'hold', r: 0.04, at: [0.02, -0.06, 0.0], arm: [0.3, -0.5, 1] },
  slipper: { ...STICK, at: [0, -0.01, 0.08], r: 0.012, pose: 'hold' },
  reverse: { axis: [0, 1, 0], back: [1, 0, 0.5], pose: 'pinch', r: 0.006, at: [0.04, -0.07, 0.0], arm: [0.3, -0.6, 1] },
  cards: { axis: [0.1, 1, 0.1], back: [0.8, -0.2, 0.9], pose: 'hold', r: 0.014, at: [0.01, -0.05, 0.01], arm: [0.25, -0.7, 0.8] },
  claw: { hide: true }, bloodcross: { hide: true }, katana: { hide: true }, // (the katana's two hands are its own, katanavm.js)
};
export function gunHand(id, cfg, g, model) {
  const H = (model && model !== 'default' && HANDS[model]) || HANDS[id] || HANDS.default;
  const h = makeHand('R', { pose: H.pose || 'trigger', r: H.r ?? HANDS.default.r, arm: H.arm || HANDS.default.arm });
  aimHand(h, H.axis || HANDS.default.axis, H.back || HANDS.default.back);
  const at = H.at || (g.userData.glb === 'blender' && cfg.handGlb) || cfg.hand || [0.004, -0.042, 0.03];
  h.position.set(...at);
  h.userData.handCfg = H;
  if (H.hide) h.visible = false;
  return h;
}
// the same hand for the other side (Lefty & Righty's left gun, the off hand)
export function mirrorHand(h) {
  const H = h.userData.handCfg || HANDS.default, cfgH = h.userData.hand;
  const m = makeHand(cfgH.side === 'R' ? 'L' : 'R', { pose: cfgH.pose, r: cfgH.r, arm: cfgH.arm });
  const ax = H.axis || HANDS.default.axis, bk = H.back || HANDS.default.back;
  aimHand(m, [-ax[0], ax[1], ax[2]], [-bk[0], bk[1], bk[2]]);
  m.position.copy(h.position); m.position.x *= -1; m.visible = h.visible;
  return m;
}
// point the cuff at a spot (the hand's parent space), e.g. a shoulder off screen, so the hand reads as attached
const tq = new THREE.Quaternion(), tv = new THREE.Vector3();
export function aimCuff(h, targetInParent) {
  const H = h.userData.hand; if (!H) return;
  tv.copy(targetInParent).sub(h.position).applyQuaternion(tq.copy(h.quaternion).invert());
  const sx = H.sx; H.arm = [sx * tv.x, tv.y, tv.z];
  pose(h, H.pose);
}
