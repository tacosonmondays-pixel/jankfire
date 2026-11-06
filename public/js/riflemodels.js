// The rifle pack's code-built models: the fallback when a Blender file is missing, and the reference the Blender
// versions match (muzzle, sight line, grip, and where each moving part sits). Moving parts are groups whose origin is
// their pivot / seat, stored on userData the same way the Blender files name them (rifles.js moves them):
//   mag (seat, slides out down/forward), charge (charging handle, slides back), lever + hammer (Yeehaw),
//   cover (LMG feed cover, hinged at its back edge), belt (LMG links, feed tray -> box), heat (LMG barrel glow material)
import * as THREE from 'three';
import { M } from './models.js';
import { jankify } from './jank.js';

function bx(w, h, d, color, x = 0, y = 0, z = 0, basic = false) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(color, basic));
  m.position.set(x, y, z);
  return m;
}
function cyl(r, len, color, x = 0, y = 0, z = 0, seg = 8, basic = false) {
  const g = new THREE.CylinderGeometry(r, r, len, seg);
  g.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(g, M(color, basic));
  m.position.set(x, y, z);
  return m;
}
function grp(parent, x, y, z) { const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); return g; }
const tilt = (m, rx) => { m.rotation.x = rx; return m; };
const DOT = 0x7dff4f;
function post(g, y, z) { const t = bx(0.008, 0.008, 0.008, DOT, 0, y, z, true); t.userData.noWrap = true; g.add(t); }

export const RIFLE_WB = {
  // Hat Trick: FAMAS-pattern bullpup. carry handle on top (the sights are in it), mag behind the grip, a bipod folded
  burst(g) {
    const body = 0x2e3a5c, dark = 0x15161c, blue = 0x4f8bff;
    g.add(bx(0.075, 0.12, 0.62, body, 0, -0.01, 0.12)); // the long receiver / stock
    g.add(bx(0.08, 0.04, 0.12, dark, 0, -0.03, 0.47)); // butt pad
    g.add(cyl(0.016, 0.42, dark, 0, 0.012, -0.44)); // barrel
    g.add(bx(0.06, 0.07, 0.24, body, 0, -0.005, -0.3)); // handguard
    g.add(bx(0.03, 0.03, 0.06, dark, 0, 0.012, -0.64)); // flash hider
    g.add(bx(0.02, 0.05, 0.5, dark, 0, 0.1, -0.05)); // carry handle spine
    g.add(bx(0.02, 0.06, 0.03, dark, 0, 0.07, -0.29)); g.add(bx(0.02, 0.06, 0.03, dark, 0, 0.07, 0.19)); // its legs
    g.add(bx(0.02, 0.025, 0.02, dark, 0, 0.13, -0.27)); post(g, 0.145, -0.27); // front sight in the handle
    for (const sx of [-1, 1]) g.add(bx(0.006, 0.03, 0.012, dark, sx * 0.01, 0.135, 0.12)); // rear aperture ears
    g.add(tilt(bx(0.04, 0.12, 0.05, dark, 0, -0.12, -0.08), -0.2)); // pistol grip (forward, bullpup)
    g.add(bx(0.012, 0.02, 0.1, dark, 0, -0.08, -0.12)); // trigger guard
    const ch = grp(g, 0, 0.065, -0.1); g.userData.charge = ch; ch.add(bx(0.03, 0.02, 0.04, blue, 0, 0, 0)); // charging handle
    const mag = grp(g, 0, -0.07, 0.12); g.userData.mag = mag;
    mag.add(tilt(bx(0.04, 0.17, 0.07, dark, 0, -0.08, 0.01), 0.18)); mag.add(bx(0.045, 0.02, 0.08, blue, 0, -0.165, 0.025));
    g.add(bx(0.01, 0.02, 0.3, blue, 0.04, 0.0, 0.12)); // stripe
    g.userData.muzzle = new THREE.Vector3(0, 0.012, -0.67);
    g.userData.sight = { y: 0.145, z: 0.12 };
    g.userData.len = 1.15;
  },
  // Belt Sander: M249-pattern LMG. box on the left-bottom, a belt up into the feed tray, a hot barrel with a carry handle
  lmg(g) {
    const body = 0x3a3d33, dark = 0x17181a, tan = 0xb89a62;
    const heat = jankify(new THREE.MeshBasicMaterial({ color: 0x2a2a2a })); g.userData.heat = heat;
    g.add(bx(0.09, 0.12, 0.42, body, 0, 0, -0.02)); // receiver
    const bar = cyl(0.02, 0.55, 0x222222, 0, 0.02, -0.5); bar.material = heat; bar.userData.noWrap = true; g.add(bar); // barrel (glows)
    g.add(cyl(0.028, 0.09, dark, 0, 0.02, -0.82)); // flash hider
    g.add(bx(0.03, 0.04, 0.18, dark, 0, -0.03, -0.32)); // gas tube
    g.add(bx(0.025, 0.05, 0.14, dark, 0, 0.09, -0.32)); // carry handle
    g.add(bx(0.01, 0.04, 0.01, dark, 0, 0.065, -0.72)); post(g, 0.088, -0.72); // front post
    for (const sx of [-1, 1]) g.add(bx(0.006, 0.03, 0.012, dark, sx * 0.012, 0.09, 0.0)); // rear sight
    const cv = grp(g, 0, 0.065, 0.08); g.userData.cover = cv; cv.add(bx(0.085, 0.025, 0.2, body, 0, 0, -0.1)); // feed cover (hinged at the back)
    g.add(tilt(bx(0.045, 0.13, 0.06, dark, 0, -0.12, 0.11), -0.25)); // pistol grip
    g.add(bx(0.06, 0.13, 0.3, tan, 0, -0.03, 0.36)); // stock
    const mag = grp(g, -0.02, -0.1, -0.08); g.userData.mag = mag; mag.add(bx(0.11, 0.13, 0.15, tan, 0, -0.04, 0)); // ammo box
    const belt = []; // links from the feed tray down into the box
    for (let i = 0; i < 10; i++) {
      const k = i / 9, l = bx(0.05, 0.012, 0.016, 0xd9a53a, 0, 0, 0);
      l.position.set(-0.05 - 0.02 * Math.sin(k * 2.5), 0.03 - k * 0.12, -0.06 - k * 0.02); l.rotation.x = -0.9 * k;
      g.add(l); belt.push(l);
    }
    g.userData.belt = belt;
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.87);
    g.userData.sight = { y: 0.088, z: 0.0 };
    g.userData.len = 1.3;
  },
  // Second Opinion: SVD-pattern marksman rifle. skeleton stock, long barrel, a little scope on a side rail
  dmr(g) {
    const wood = 0x8a4a2a, dark = 0x1b1b20, vio = 0xb07dff;
    g.add(bx(0.07, 0.1, 0.36, dark, 0, 0, -0.02)); // receiver
    g.add(cyl(0.017, 0.62, 0x111111, 0, 0.02, -0.5)); // barrel
    g.add(cyl(0.024, 0.08, dark, 0, 0.02, -0.84)); // muzzle brake
    g.add(bx(0.07, 0.08, 0.3, wood, 0, 0, -0.33)); // handguard
    g.add(tilt(bx(0.045, 0.13, 0.06, wood, 0, -0.1, 0.12), -0.3)); // grip
    g.add(bx(0.05, 0.03, 0.34, wood, 0, 0.0, 0.33)); g.add(bx(0.05, 0.03, 0.3, wood, 0, -0.11, 0.33)); // skeleton stock
    g.add(bx(0.05, 0.14, 0.03, wood, 0, -0.05, 0.49)); g.add(bx(0.045, 0.05, 0.12, wood, 0, 0.035, 0.3)); // butt + cheek rest
    g.add(cyl(0.028, 0.26, dark, 0, 0.12, -0.03, 12)); g.add(cyl(0.036, 0.06, dark, 0, 0.12, -0.17, 12)); // scope + objective bell
    g.add(cyl(0.032, 0.05, dark, 0, 0.12, 0.11, 12)); g.add(bx(0.02, 0.06, 0.1, dark, 0, 0.07, -0.03)); // eyepiece + mount
    const lens = cyl(0.03, 0.005, vio, 0, 0.12, -0.2, 12, true); lens.userData.noWrap = true; g.add(lens);
    const ch = grp(g, 0.045, 0.02, 0.0); g.userData.charge = ch; ch.add(bx(0.03, 0.015, 0.02, dark, 0, 0, 0));
    const mag = grp(g, 0, -0.05, -0.06); g.userData.mag = mag; mag.add(tilt(bx(0.04, 0.13, 0.08, dark, 0, -0.06, 0.02), 0.3));
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.89);
    g.userData.sight = { y: 0.12, z: 0.12 };
    g.userData.len = 1.4;
  },
  // Yeehaw: 1892-pattern lever-action carbine, big loop lever (for the spin-cock), tube magazine under the barrel
  lever(g) {
    const wood = 0xa0582a, steel = 0x2a2a30, brass = 0xd9a53a, pink = 0xff6b8b;
    g.add(bx(0.05, 0.08, 0.2, brass, 0, -0.005, 0.0)); // receiver (brass, it's a fun one)
    g.add(cyl(0.015, 0.6, steel, 0, 0.02, -0.4)); g.add(cyl(0.012, 0.52, steel, 0, -0.012, -0.36)); // barrel + mag tube
    g.add(bx(0.05, 0.05, 0.24, wood, 0, -0.005, -0.22)); // forend
    g.add(bx(0.008, 0.03, 0.01, steel, 0, 0.042, -0.66)); post(g, 0.06, -0.66); // front blade
    for (const sx of [-1, 1]) g.add(bx(0.008, 0.02, 0.012, steel, sx * 0.012, 0.05, -0.2)); // buckhorn rear
    g.add(tilt(bx(0.045, 0.08, 0.36, wood, 0, -0.06, 0.28), 0.18)); // stock
    g.add(bx(0.05, 0.12, 0.03, pink, 0, -0.1, 0.46)); // butt plate
    const lever = grp(g, 0, -0.04, -0.02); g.userData.lever = lever; // the lever pivots on its front pin
    lever.add(bx(0.014, 0.014, 0.12, steel, 0, -0.005, 0.06)); lever.add(bx(0.014, 0.06, 0.014, steel, 0, -0.035, 0.12));
    lever.add(bx(0.014, 0.014, 0.1, steel, 0, -0.065, 0.07)); lever.add(bx(0.014, 0.04, 0.014, steel, 0, -0.045, 0.02));
    const ham = grp(g, 0, 0.03, 0.09); g.userData.hammer = ham; ham.add(bx(0.012, 0.03, 0.012, steel, 0, 0.012, 0));
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.71);
    g.userData.sight = { y: 0.06, z: -0.2 };
    g.userData.len = 1.15;
  },
  // Lawn Mower: Saiga-12-pattern auto shotgun. AK-style body, a fat box mag, a big muzzle brake
  autoshot(g) {
    const body = 0x2d4a2f, dark = 0x161816, green = 0x4ad66b;
    g.add(bx(0.07, 0.11, 0.38, dark, 0, 0, -0.02)); // receiver
    g.add(cyl(0.022, 0.5, 0x111111, 0, 0.02, -0.42)); g.add(cyl(0.032, 0.1, dark, 0, 0.02, -0.7)); // barrel + brake
    g.add(bx(0.075, 0.085, 0.24, body, 0, -0.005, -0.3)); // handguard
    g.add(bx(0.06, 0.02, 0.36, dark, 0, 0.062, -0.05)); // dust cover / rail
    g.add(bx(0.008, 0.04, 0.012, dark, 0, 0.055, -0.62)); post(g, 0.078, -0.62); // front post
    for (const sx of [-1, 1]) g.add(bx(0.006, 0.026, 0.012, dark, sx * 0.011, 0.085, 0.05)); // rear notch
    g.add(tilt(bx(0.04, 0.12, 0.05, dark, 0, -0.11, 0.12), -0.3)); // grip
    g.add(bx(0.055, 0.12, 0.3, body, 0, -0.03, 0.34)); // stock
    const ch = grp(g, 0.045, 0.03, -0.03); g.userData.charge = ch; ch.add(bx(0.03, 0.015, 0.02, dark, 0, 0, 0));
    const mag = grp(g, 0, -0.055, -0.08); g.userData.mag = mag;
    mag.add(tilt(bx(0.06, 0.15, 0.12, dark, 0, -0.07, 0.015), 0.12)); mag.add(bx(0.065, 0.02, 0.125, green, 0, -0.145, 0.03));
    g.add(bx(0.01, 0.03, 0.22, green, 0.04, -0.005, -0.3)); // grass-green stripe
    g.userData.muzzle = new THREE.Vector3(0, 0.02, -0.76);
    g.userData.sight = { y: 0.078, z: 0.05 };
    g.userData.len = 1.2;
  },
};

// a Blender rifle's moving parts, named in its metadata (same hooks as the code models above)
const nodeIn = (g, n) => { let r = null; if (typeof n === 'string') g.traverse((o) => { if (!r && o.name === n) r = o; }); return r; };
export function bindRifle(g, meta) {
  // (the lever's hammer is `lhammer`: plain `hammer` is the revolver's flick in glbkit.js)
  for (const [k, u] of [['mag', 'mag'], ['charge', 'charge'], ['lever', 'lever'], ['lhammer', 'hammer'], ['cover', 'cover']]) { const n = meta[k] && nodeIn(g, meta[k].node || meta[k]); if (n) g.userData[u] = n; }
  if (Array.isArray(meta.belt)) { const b = meta.belt.map((n) => nodeIn(g, n)).filter(Boolean); if (b.length) g.userData.belt = b; }
  if (typeof meta.heat === 'string') { // the LMG barrel: one unlit material that rifles.js heats up (like the Redline's vents)
    const hm = jankify(new THREE.MeshBasicMaterial({ color: 0x2a2a2a }));
    g.traverse((o) => { if (o.isMesh && o.material && o.material.name === meta.heat) { o.material = hm; o.userData.noWrap = true; } });
    g.userData.heat = hm;
  }
}
