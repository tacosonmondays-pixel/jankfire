// Code models for the new primaries (the fallback when the Blender .glb isn't there) and the things they shoot.
// Same space as every weapon: muzzle = -z, up = +y, the grip near the origin. Real proportions, chunky bits.
//   Nail Gun              a pneumatic framing nailer: piston cap on top, nose + safety tip forward, angled stick
//                         magazine of nails under it, rubber grip, air fitting with an orange hose stub
//   Tennis Ball Launcher  a ball can as the barrel, a racket handle with overgrip as the grip, a CO2 bottle,
//                         a hopper of balls feeding the breech, a sweatband round the muzzle
//   Shopping Cart Cannon  a fat bell-mouthed cannon, a cart's red handle as the foregrip, a coin lock with its
//                         chain, a castor wheel on the bottom and a "RETURN CARTS HERE" sign
// Each mesh carries its wrap zone in userData.wz (a = handle side, b = business end, n = keeps its look).
import * as THREE from 'three';
import { M } from './models.js';
import { lathe } from './blades/kit.js';

const tag = (m, wz) => { m.userData.wz = wz; return m; };
function bx(w, h, d, c, x, y, z, wz = 'b', glow = false) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c, glow)); m.position.set(x, y, z); if (glow) m.userData.noWrap = true; return tag(m, wz); }
function cyl(r, len, c, x, y, z, axis = 'z', seg = 10, wz = 'b', r2 = r) {
  const g = new THREE.CylinderGeometry(r2, r, len, seg);
  if (axis === 'z') g.rotateX(Math.PI / 2); else if (axis === 'x') g.rotateZ(Math.PI / 2);
  const m = new THREE.Mesh(g, M(c)); m.position.set(x, y, z); return tag(m, wz);
}
function sph(r, c, x, y, z, wz = 'b', seg = 8) { const m = new THREE.Mesh(new THREE.SphereGeometry(r, seg, Math.max(4, seg - 2)), M(c)); m.position.set(x, y, z); return tag(m, wz); }
function rod(a, b, r, c, wz = 'b', seg = 6) { // a thin bar from a to b
  const d = new THREE.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), L = d.length();
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, seg), M(c));
  m.position.set((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
  return tag(m, wz);
}

// ------------------------------------------------------------ Nail Gun
export const NAIL_COL = 0xff6f3c;
export function nailgunBuild(g) { // same layout as the Blender one: drive forward, handle down as a pistol grip, raked stick mag
  const O = NAIL_COL, K = 0x1c1c20, S = 0x8a9098, BR = 0xd8b048, AY = 0.04;
  g.add(cyl(0.072, 0.26, O, 0, AY, -0.03, 'z', 14, 'a')); // piston housing
  g.add(cyl(0.074, 0.03, K, 0, AY, 0.115, 'z', 14, 'b')); // cap
  g.add(bx(0.048, 0.085, 0.16, S, 0, AY - 0.005, -0.25)); // nose
  g.add(bx(0.042, 0.03, 0.04, 0x5a5f66, 0, AY, -0.345)); // contact trip
  g.add(bx(0.026, 0.03, 0.21, 0xe0202a, 0, AY + 0.095, -0.0, 'n')); // the spirit level sight
  const grip = new THREE.Group(); grip.position.set(0, AY - 0.19, 0.045);
  grip.add(bx(0.055, 0.2, 0.08, O, 0, 0.04, 0, 'a'));
  grip.add(bx(0.06, 0.15, 0.085, K, 0, 0.01, 0.002, 'a'));
  grip.add(bx(0.065, 0.03, 0.095, K, 0, -0.085, 0, 'b'));
  g.add(grip);
  g.add(cyl(0.012, 0.04, BR, 0, AY - 0.31, 0.045, 'y', 6, 'n'));
  const mag = new THREE.Group(); mag.position.set(0, AY - 0.16, -0.24); mag.rotation.x = 0.37; mag.name = 'mag';
  mag.add(bx(0.036, 0.3, 0.1, 0xb8bec6, 0, 0, 0, 'a'));
  for (let i = 0; i < 12; i++) mag.add(bx(0.04, 0.006, 0.06, 0xc8d0d8, 0, -0.13 + i * 0.022, -0.01, 'n'));
  g.add(mag);
  g.add(bx(0.03, 0.025, 0.2, K, 0, AY - 0.31, -0.07)); // bracket to the grip
  g.add(bx(0.01, 0.05, 0.016, 0xe0202a, 0, AY - 0.1, -0.02)); // trigger
  g.userData.muzzle = new THREE.Vector3(0, AY, -0.358);
  g.userData.len = 0.5;
}
// one nail: shank along -z, head at z = 0
let nailGeo = null;
export function nailMesh() {
  if (!nailGeo) {
    const shank = new THREE.CylinderGeometry(0.004, 0.005, 0.085, 4); shank.rotateX(Math.PI / 2); shank.translate(0, 0, -0.0425);
    const tip = new THREE.ConeGeometry(0.005, 0.012, 4); tip.rotateX(-Math.PI / 2); tip.translate(0, 0, -0.091);
    const head = new THREE.CylinderGeometry(0.011, 0.011, 0.003, 6); head.rotateX(Math.PI / 2);
    nailGeo = [shank, tip, head];
  }
  const g = new THREE.Group();
  for (const geo of nailGeo) { const m = new THREE.Mesh(geo, M(0xb8c0c8)); g.add(m); }
  return g;
}

// ------------------------------------------------------------ Tennis Ball Launcher
export const BALL_COL = 0xd4ff3a;
export function tennisBall(r = 0.1) {
  const g = new THREE.Group();
  const b = new THREE.Mesh(new THREE.SphereGeometry(r, 10, 7), M(BALL_COL)); g.add(b);
  // the white seam: two loops round the ball, tilted the way a real one curls
  for (const a of [0.45, -0.45]) {
    const s = new THREE.Mesh(new THREE.TorusGeometry(r * 1.002, r * 0.06, 3, 16, Math.PI), M(0xf4f4f0));
    s.rotation.set(Math.PI / 2 + a, a > 0 ? 0 : Math.PI, 0); g.add(s);
  }
  g.userData.ball = b;
  return g;
}
export function tennisBuild(g) {
  const CAN = 0xe8f0e0, LID = 0xf4f4f4, GR = 0x1c1c22, GRIP = 0xf8f6ee;
  // the barrel: a clear ball can, three balls stacked inside, a white lid ring at the mouth
  const can = cyl(0.042, 0.42, 0xcfe6d8, 0, 0.03, -0.31, 'z', 14, 'b');
  can.material = new THREE.MeshLambertMaterial({ color: 0xdff4e8, transparent: true, opacity: 0.35, depthWrite: false }); can.userData.noWrap = true; can.renderOrder = 2;
  g.add(can); // clear, so you see the balls
  for (let i = 0; i < 3; i++) { const b = tennisBall(0.037); b.position.set(0, 0.03, -0.42 + i * 0.08); b.traverse((o) => { o.userData.wz = 'n'; }); g.add(b); }
  g.add(cyl(0.046, 0.025, LID, 0, 0.03, -0.53, 'z', 14, 'b'));
  g.add(cyl(0.047, 0.03, 0xff4fd8, 0, 0.03, -0.46, 'z', 14, 'n')); // pink sweatband
  g.add(cyl(0.046, 0.02, CAN, 0, 0.03, -0.1, 'z', 14, 'b'));
  // breech block + the hopper feeding it (a second can standing up, balls showing)
  g.add(bx(0.07, 0.08, 0.12, GR, 0, 0.02, -0.04, 'a'));
  g.add(cyl(0.036, 0.13, 0xcfe6d8, -0.015, 0.12, -0.06, 'y', 12, 'b'));
  for (let i = 0; i < 2; i++) { const b = tennisBall(0.032); b.position.set(-0.015, 0.09 + i * 0.065, -0.06); b.traverse((o) => { o.userData.wz = 'n'; }); g.add(b); }
  g.add(cyl(0.039, 0.016, LID, -0.015, 0.19, -0.06, 'y', 12, 'b'));
  // CO2 bottle under the barrel
  g.add(cyl(0.022, 0.22, 0xc8ccd4, 0, -0.04, -0.22, 'z', 10, 'b'));
  g.add(sph(0.022, 0xc8ccd4, 0, -0.04, -0.33));
  // racket handle grip (octagonal, white overgrip, butt cap) + trigger
  const grip = new THREE.Group(); grip.position.set(0, -0.06, 0.05); grip.rotation.x = 0.32;
  grip.add(cyl(0.022, 0.15, GRIP, 0, -0.03, 0, 'y', 8, 'a'));
  for (let i = 0; i < 5; i++) grip.add(cyl(0.0235, 0.008, 0xd8d6ce, 0, -0.09 + i * 0.03, 0, 'y', 8, 'a'));
  grip.add(cyl(0.026, 0.016, GR, 0, -0.112, 0, 'y', 8, 'a'));
  g.add(grip);
  g.add(bx(0.008, 0.035, 0.012, GR, 0, -0.03, -0.01));
  g.add(bx(0.05, 0.03, 0.14, GR, 0, -0.01, 0.12, 'a')); // short stock
  g.userData.muzzle = new THREE.Vector3(0, 0.03, -0.545);
  g.userData.len = 0.72;
}

// ------------------------------------------------------------ the shopping cart (the thing that comes out)
// real cart: ~95 cm long, 60 wide, 1 m to the handle, basket tapers to the front. built in the cart's own space:
// feet at y 0, the nose (front of the basket) at -z, the handle at +z
export const CART_COL = 0x9b5cff;
export function cartModel() {
  const g = new THREE.Group(), W = 0xc8ccd4, RED = 0xe0202a, BLK = 0x1a1a1e;
  const wire = (a, b) => g.add(rod(a, b, 0.008, W, 'b', 4));
  const yb = 0.42, yt = 0.92; // basket bottom / top
  const back = 0.38, front = -0.45, hb = 0.29, hf = 0.23; // half widths at the back / front
  // top + bottom rims
  for (const [y, k] of [[yt, 1], [yb, 0.9]]) {
    const b2 = back - (k < 1 ? 0.04 : 0), f2 = front + (k < 1 ? 0.06 : 0);
    wire([-hb * k, y, b2], [hb * k, y, b2]); wire([-hf * k, y, f2], [hf * k, y, f2]);
    wire([-hb * k, y, b2], [-hf * k, y, f2]); wire([hb * k, y, b2], [hf * k, y, f2]);
  }
  // vertical wires down the sides and the front
  for (let i = 0; i <= 8; i++) {
    const t = i / 8, z = back + (front - back) * t, h = hb + (hf - hb) * t;
    for (const sx of [-1, 1]) wire([sx * h, yt, z], [sx * h * 0.9, yb, z + 0.03 * (1 - t) - 0.05 * t]);
  }
  for (let i = 0; i <= 4; i++) { const x = -hf + (2 * hf * i) / 4; wire([x, yt, front], [x * 0.9, yb, front + 0.06]); }
  // the folding back gate (the child seat flap) + handle
  for (let i = 0; i <= 5; i++) { const x = -hb + (2 * hb * i) / 5; wire([x, yt, back], [x * 0.9, yb, back - 0.04]); }
  g.add(cyl(0.02, hb * 2 + 0.06, RED, 0, 1.0, back + 0.1, 'x', 8, 'a'));
  for (const sx of [-1, 1]) wire([sx * hb, yt, back], [sx * hb, 1.0, back + 0.1]);
  // chassis: two side rails, the bottom tray, castors
  for (const sx of [-1, 1]) g.add(rod([sx * 0.24, 0.11, back + 0.02], [sx * 0.2, 0.11, front + 0.04], 0.012, W));
  for (const sx of [-1, 1]) g.add(rod([sx * 0.24, 0.11, back + 0.02], [sx * hb * 0.9, yb, back - 0.04], 0.012, W));
  g.add(bx(0.4, 0.01, 0.6, 0xa8adb4, 0, 0.18, -0.04));
  for (const [x, z] of [[-0.22, back - 0.02], [0.22, back - 0.02], [-0.19, front + 0.06], [0.19, front + 0.06]]) {
    g.add(bx(0.03, 0.05, 0.03, W, x, 0.085, z));
    const wh = cyl(0.05, 0.03, BLK, x, 0.05, z, 'x', 10, 'b'); wh.userData.wheel = true; g.add(wh);
  }
  // a store-coloured plastic corner bumper + the coin lock on the handle
  for (const sx of [-1, 1]) g.add(bx(0.06, 0.06, 0.04, CART_COL, sx * hf, yt - 0.02, front, 'a'));
  g.add(bx(0.06, 0.05, 0.04, 0xffe14d, 0.18, 1.0, back + 0.13, 'n'));
  return g;
}

// ------------------------------------------------------------ Shopping Cart Cannon
export function cartCannonBuild(g) {
  const P = CART_COL, K = 0x22222a, ST = 0xc8ccd4, RED = 0xe0202a;
  // the cannon: a fat tube flaring out to a bell mouth
  g.add(lathe([[0, 0.12], [0.075, 0.12], [0.085, 0.05], [0.085, -0.5], [0.1, -0.62], [0.13, -0.7], [0.125, -0.71], [0.095, -0.64], [0.075, -0.52], [0.0, -0.52]], P, { segs: 16, y: 0.02 }));
  for (const z of [-0.12, -0.36]) g.add(cyl(0.09, 0.03, K, 0, 0.02, z, 'z', 16, 'b'));
  // the cart handle as the foregrip (red plastic bar on two posts)
  for (const sx of [-1, 1]) g.add(bx(0.012, 0.07, 0.012, ST, sx * 0.05, -0.1, -0.3));
  g.add(cyl(0.017, 0.16, RED, 0, -0.14, -0.3, 'x', 8, 'a'));
  // coin lock + chain on the side
  g.add(bx(0.03, 0.06, 0.08, 0xffe14d, 0.09, 0.03, -0.18, 'n'));
  for (let i = 0; i < 4; i++) g.add(cyl(0.008, 0.02, ST, 0.105, -0.01 - i * 0.022, -0.16, 'y', 6, 'n'));
  // castor wheel at the bottom of the barrel
  g.add(bx(0.03, 0.05, 0.03, ST, 0, -0.09, -0.5));
  g.add(cyl(0.035, 0.025, 0x1a1a1e, 0, -0.13, -0.5, 'x', 10));
  // grip, trigger, stock pad
  const grip = bx(0.04, 0.13, 0.055, K, 0, -0.1, 0.06, 'a'); grip.rotation.x = -0.3; g.add(grip);
  g.add(bx(0.008, 0.035, 0.012, K, 0, -0.07, 0.0));
  g.add(bx(0.06, 0.1, 0.16, K, 0, -0.02, 0.22, 'a'));
  // "RETURN CARTS HERE" sign plate on top
  g.add(bx(0.07, 0.04, 0.005, 0x2a6aff, 0, 0.13, -0.08, 'n'));
  g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.71);
  g.userData.len = 0.95;
}

// ------------------------------------------------------------ model skins (COSMETICS.model)
// Office Stapler: a giant desk stapler. the nails still come out (the staples are for show)
export function nailgunStaple(g) {
  const R = 0xd01c2a, K = 0x1c1c20, ST = 0xc8ccd4;
  g.add(bx(0.07, 0.035, 0.46, K, 0, -0.06, -0.13, 'a')); // base
  g.add(bx(0.06, 0.012, 0.06, 0x5a5f66, 0, -0.038, -0.34)); // anvil
  const top = new THREE.Group(); top.position.set(0, -0.01, 0.08); top.rotation.x = 0.06;
  top.add(bx(0.062, 0.05, 0.44, R, 0, 0.02, -0.2, 'a'));
  top.add(bx(0.066, 0.02, 0.4, 0x8a141e, 0, 0.05, -0.19, 'a'));
  top.add(bx(0.05, 0.03, 0.3, ST, 0, -0.012, -0.2)); // the staple channel
  g.add(top);
  g.add(cyl(0.02, 0.08, ST, 0, -0.03, 0.09, 'x', 10)); // hinge
  for (let i = 0; i < 6; i++) g.add(bx(0.03, 0.004, 0.006, 0xd8dde4, 0, -0.025, -0.3 + i * 0.012, 'n'));
  g.add(bx(0.008, 0.035, 0.012, K, 0, -0.095, -0.02));
  g.add(bx(0.04, 0.1, 0.05, K, 0, -0.12, 0.05, 'a'));
  g.userData.muzzle = new THREE.Vector3(0, -0.04, -0.37);
  g.userData.len = 0.6;
}
// Ball Machine: a courtside ball machine with a basket hopper heaped with balls
export function tennisMachine(g) {
  const B = 0x1d5a3a, K = 0x1c1c22, W = 0xf4f4f0;
  g.add(bx(0.14, 0.12, 0.24, B, 0, -0.02, -0.08, 'a'));
  g.add(cyl(0.035, 0.24, K, 0, 0.0, -0.32, 'z', 12));
  g.add(cyl(0.042, 0.03, W, 0, 0.0, -0.44, 'z', 12));
  g.add(cyl(0.1, 0.1, 0xb8c0c8, 0, 0.1, -0.06, 'y', 10, 'b', 0.07));
  for (let i = 0; i < 7; i++) { const a = i * 0.9, r = i ? 0.05 : 0; const b = tennisBall(0.034); b.position.set(Math.cos(a) * r, 0.16 + (i ? 0 : 0.03), -0.06 + Math.sin(a) * r); b.traverse((o) => { o.userData.wz = 'n'; }); g.add(b); }
  for (const sx of [-1, 1]) g.add(cyl(0.035, 0.02, K, sx * 0.08, -0.08, 0.0, 'x', 10));
  g.add(bx(0.06, 0.03, 0.04, 0xff4fd8, 0.07, 0.03, -0.17, 'n')); // the speed dial
  const grip = bx(0.04, 0.12, 0.05, K, 0, -0.12, 0.06, 'a'); grip.rotation.x = -0.3; g.add(grip);
  g.add(bx(0.008, 0.035, 0.012, K, 0, -0.09, 0.01));
  g.userData.muzzle = new THREE.Vector3(0, 0.0, -0.46);
  g.userData.len = 0.62;
}
// Basket Case: a red supermarket hand basket gaffer-taped to a drain pipe
export function cartBasket(g) {
  const R = 0xe0202a, K = 0x22222a, P = 0xdcdcd2;
  g.add(cyl(0.075, 0.72, P, 0, 0.0, -0.32, 'z', 14, 'b'));
  g.add(cyl(0.085, 0.05, 0x9aa0a8, 0, 0.0, -0.66, 'z', 14, 'b'));
  const bk = new THREE.Group(); bk.position.set(0, 0.13, -0.18);
  bk.add(bx(0.2, 0.012, 0.3, R, 0, -0.07, 0, 'a'));
  for (const sx of [-1, 1]) bk.add(bx(0.012, 0.13, 0.32, R, sx * 0.11, 0, 0, 'a'));
  for (const sz of [-1, 1]) bk.add(bx(0.23, 0.13, 0.012, R, 0, 0, sz * 0.16, 'a'));
  for (const sz of [-1, 1]) bk.add(bx(0.02, 0.12, 0.02, K, 0, 0.11, sz * 0.06, 'n'));
  bk.add(cyl(0.012, 0.16, K, 0, 0.17, 0, 'z', 6, 'n'));
  g.add(bk);
  for (const z of [-0.08, -0.28]) g.add(cyl(0.078, 0.04, 0x9aa0a8, 0, 0.0, z, 'z', 14, 'n'));
  const grip = bx(0.04, 0.13, 0.055, K, 0, -0.1, 0.06, 'a'); grip.rotation.x = -0.3; g.add(grip);
  g.add(bx(0.008, 0.035, 0.012, K, 0, -0.07, 0.0));
  g.userData.muzzle = new THREE.Vector3(0, 0.0, -0.69);
  g.userData.len = 0.9;
}
