// Code-built sidearms (the fallback when the Blender .glb is missing), from real references at a game scale:
//   Plan B          a 1911-pattern .45 (x1.5 like the revolver): slide, barrel bushing, spur hammer, beavertail,
//                   wood grips. `slide`, `mag` and `hammer` are their own groups (sidearms.js moves them)
//   Lefty & Righty  a MAC-10-pattern machine pistol (x1.1): stamped box receiver, mag in the grip, square guard,
//                   cocking knob on top (`cocker`), an L / R sticker on each side (`tagL` / `tagR`, one shows per hand)
//   Half a Shotgun  a side-by-side coach gun with the barrels and the stock sawn off (x1.0): two hammers, top lever,
//                   two triggers. the barrels + forend + both shells hang off `hinge` (it breaks open to reload)
// Weapon space like every gun: forward = -Z, up = +Y, the grip at the origin.
import * as THREE from 'three';
import { M } from './models.js';

function bx(w, h, d, c, x = 0, y = 0, z = 0, basic = false) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c, basic)); m.position.set(x, y, z); return m; }
function cz(r, len, c, x = 0, y = 0, z = 0, seg = 8, basic = false) {
  const g = new THREE.CylinderGeometry(r, r, len, seg); g.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(g, M(c, basic)); m.position.set(x, y, z); return m;
}
const grp = (name, x = 0, y = 0, z = 0) => { const g = new THREE.Group(); g.name = name; g.position.set(x, y, z); return g; };
const tilt = (m, rx = 0, ry = 0, rz = 0) => { m.rotation.set(rx, ry, rz); return m; };
const zone = (m, z) => { m.userData.wz = z; return m; };

// a tiny canvas sticker (the akimbo's L / R)
const stick = new Map();
function sticker(txt, bg, fg) {
  const k = txt + bg + fg;
  if (stick.has(k)) return stick.get(k);
  const c = document.createElement('canvas'); c.width = c.height = 16;
  const x = c.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, 16, 16); x.fillStyle = fg; x.font = 'bold 14px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(txt, 8, 9);
  const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.MeshBasicMaterial({ map: t }); stick.set(k, m); return m;
}

// ------------------------------------------------------------ Plan B (1911 pattern)
const PB = { steel: 0x3a3f4a, dark: 0x1b1d22, wood: 0x9a5a2a, brass: 0xd9a53a, accent: 0xa0b4ff };
export function pistolBuild(g) {
  const S = 0.0015, BY = 0.03, MZ = -0.25; // 1 mm, bore height, muzzle
  const slide = grp('slide');
  slide.add(bx(23 * S, 29 * S, 210 * S, PB.steel, 0, BY + 0.5 * S, MZ + 105 * S)); // the slide
  slide.add(bx(18 * S, 4 * S, 196 * S, PB.steel, 0, BY + 16 * S, MZ + 108 * S)); // rounded top flat
  for (let i = 0; i < 7; i++) for (const sx of [-1, 1]) slide.add(bx(1.2 * S, 22 * S, 2 * S, PB.dark, sx * 11.8 * S, BY + 1 * S, MZ + (172 + i * 5) * S)); // rear serrations
  slide.add(bx(2 * S, 12 * S, 40 * S, PB.dark, 11.6 * S, BY + 5 * S, MZ + 100 * S)); // ejection port (right)
  slide.add(bx(3 * S, 7 * S, 4 * S, PB.dark, 0, BY + 21 * S, MZ + 8 * S)); // front blade
  for (const sx of [-1, 1]) slide.add(bx(5 * S, 7 * S, 6 * S, PB.dark, sx * 5 * S, BY + 21 * S, MZ + 200 * S)); // rear notch ears
  g.add(slide);
  g.add(cz(10 * S, 6 * S, PB.dark, 0, BY, MZ + 3 * S, 10)); // barrel bushing
  g.add(cz(5.8 * S, 2 * S, 0x050505, 0, BY, MZ, 10, true)); // the bore
  // frame: dust cover, trigger guard, grip (raked 18 degrees back), mainspring housing
  g.add(bx(22 * S, 9 * S, 100 * S, PB.steel, 0, BY - 19 * S, MZ + 85 * S));
  g.add(bx(8 * S, 4 * S, 46 * S, PB.steel, 0, BY - 50 * S, MZ + 140 * S)); // guard bottom
  g.add(tilt(bx(8 * S, 28 * S, 4 * S, PB.steel, 0, BY - 37 * S, MZ + 117 * S), -0.35)); // guard front
  g.add(bx(4 * S, 14 * S, 5 * S, PB.dark, 0, BY - 30 * S, MZ + 135 * S)); // trigger
  const grip = grp('grip', 0, BY - 22 * S, MZ + 183 * S); grip.rotation.x = -0.32;
  grip.add(bx(26 * S, 94 * S, 46 * S, PB.steel, 0, -46 * S, 0));
  grip.add(zone(bx(33 * S, 70 * S, 40 * S, PB.wood, 0, -50 * S, -2 * S), 'a')); // walnut panels
  for (const sx of [-1, 1]) grip.add(bx(1 * S, 6 * S, 6 * S, PB.brass, sx * 16.8 * S, -24 * S, -2 * S)); // grip screws
  grip.add(bx(24 * S, 8 * S, 16 * S, PB.steel, 0, 4 * S, 26 * S)); // beavertail
  const mag = grp('mag', 0, -94 * S, -4 * S);
  mag.add(bx(21 * S, 60 * S, 34 * S, PB.dark, 0, 26 * S, 0)); // the tube (mostly hidden in the grip)
  mag.add(bx(24 * S, 6 * S, 38 * S, PB.dark, 0, -2 * S, 0)); // base pad
  mag.add(bx(9 * S, 5 * S, 12 * S, PB.brass, 0, 58 * S, -8 * S)); // top round
  grip.add(mag);
  g.add(grip);
  const ham = grp('hammer', 0, BY - 4 * S, MZ + 214 * S);
  ham.add(tilt(bx(7 * S, 16 * S, 6 * S, PB.dark, 0, 8 * S, 2 * S), 0.35));
  g.add(ham);
  g.add(bx(23.5 * S, 2.5 * S, 30 * S, PB.accent, 0, BY - 14 * S, MZ + 60 * S, true)); // a stripe so it reads as "yours"
  g.userData.muzzle = new THREE.Vector3(0, BY, MZ);
  g.userData.len = 0.33;
  g.userData.sight = { y: BY + 24 * S, z: MZ + 200 * S };
}

// ------------------------------------------------------------ Lefty & Righty (MAC-10 pattern)
const AK = { body: 0x2c3138, dark: 0x16181c, mint: 0x00e5a0, steel: 0x6a7380 };
export function akimboBuild(g) {
  const S = 0.0011, BY = 0.03, MZ = -0.2;
  g.add(bx(50 * S, 62 * S, 215 * S, AK.body, 0, BY - 2 * S, MZ + 152 * S)); // upper + lower receiver, one box
  g.add(bx(52 * S, 3 * S, 215 * S, AK.dark, 0, BY - 18 * S, MZ + 152 * S)); // the seam
  g.add(cz(9 * S, 46 * S, AK.steel, 0, BY, MZ + 23 * S, 10)); // threaded barrel stub
  for (let i = 0; i < 4; i++) g.add(cz(10 * S, 2 * S, AK.dark, 0, BY, MZ + (6 + i * 8) * S, 10));
  g.add(cz(4 * S, 2 * S, 0x050505, 0, BY, MZ - 0.5 * S, 8, true));
  g.add(bx(4 * S, 10 * S, 6 * S, AK.dark, 0, BY + 33 * S, MZ + 60 * S)); // front sight
  for (const sx of [-1, 1]) g.add(bx(6 * S, 12 * S, 10 * S, AK.dark, sx * 14 * S, BY + 34 * S, MZ + 250 * S)); // rear sight ears
  g.add(bx(8 * S, 2 * S, 120 * S, AK.dark, 0, BY + 29.5 * S, MZ + 150 * S)); // cocking slot
  const ck = grp('cocker', 0, BY + 31 * S, MZ + 130 * S);
  ck.add(cz(7 * S, 14 * S, AK.mint, 0, 5 * S, 0, 10)); ck.add(bx(5 * S, 8 * S, 8 * S, AK.dark, 0, 0, 0));
  g.add(ck);
  // grip in the middle (the mag goes up through it), square trigger guard in front
  const grip = grp('grip', 0, BY - 33 * S, MZ + 200 * S); grip.rotation.x = -0.1;
  grip.add(zone(bx(40 * S, 100 * S, 46 * S, AK.body, 0, -50 * S, 0), 'a'));
  for (let i = 0; i < 5; i++) grip.add(bx(42 * S, 3 * S, 40 * S, AK.dark, 0, (-20 - i * 15) * S, 0)); // grip ridges
  const mag = grp('mag', 0, -100 * S, -2 * S);
  mag.add(bx(30 * S, 80 * S, 34 * S, AK.steel, 0, 30 * S, 0)); mag.add(bx(36 * S, 7 * S, 40 * S, AK.mint, 0, -12 * S, 0));
  grip.add(mag);
  g.add(grip);
  g.add(bx(8 * S, 4 * S, 60 * S, AK.body, 0, BY - 80 * S, MZ + 142 * S)); // guard bottom
  g.add(bx(8 * S, 46 * S, 4 * S, AK.body, 0, BY - 57 * S, MZ + 114 * S)); // guard front
  g.add(bx(5 * S, 22 * S, 6 * S, AK.dark, 0, BY - 46 * S, MZ + 152 * S)); // trigger
  g.add(bx(14 * S, 14 * S, 18 * S, AK.dark, 0, BY - 2 * S, MZ + 268 * S)); // rear stock plate
  // L / R stickers on both sides (sidearms.js shows the right one for each hand)
  for (const [nm, txt] of [['tagL', 'L'], ['tagR', 'R']]) {
    const t = grp(nm);
    for (const sx of [-1, 1]) {
      const p = new THREE.Mesh(new THREE.PlaneGeometry(26 * S, 26 * S), sticker(txt, '#00e5a0', '#111111'));
      p.position.set(sx * 25.6 * S, BY + 8 * S, MZ + 175 * S); p.rotation.y = sx * Math.PI / 2; p.userData.noWrap = true; t.add(p);
    }
    g.add(t);
  }
  g.userData.muzzle = new THREE.Vector3(0, BY, MZ);
  g.userData.len = 0.33;
}

// ------------------------------------------------------------ Half a Shotgun (sawed-off coach gun)
const SO = { steel: 0x2e3238, case: 0x8a8f99, wood: 0x7a4422, red: 0xe05a3a, brass: 0xd9a53a, hull: 0xd02a2a };
export function sawnoffBuild(g) {
  const S = 0.001, BY = 0.02, MZ = -0.31, HZ = -0.012; // 1 mm, bore line, muzzle, the hinge pin
  const hinge = grp('hinge', 0, BY - 16 * S, HZ); // everything forward of the action swings down round the pin
  const L = HZ - MZ; // barrel length (0.3)
  for (const sx of [-1, 1]) {
    hinge.add(cz(11 * S, L, SO.steel, sx * 11 * S, 16 * S, -L / 2, 10));
    hinge.add(cz(8.4 * S, 2 * S, 0x050505, sx * 11 * S, 16 * S, -L - 0.5 * S, 10, true)); // bores
  }
  hinge.add(bx(8 * S, 5 * S, L, SO.steel, 0, 28 * S, -L / 2)); // rib
  hinge.add(bx(4 * S, 4 * S, 4 * S, SO.brass, 0, 32 * S, -L + 8 * S)); // bead
  hinge.add(bx(14 * S, 2 * S, 22 * S, SO.red, 0, 31 * S, -L + 30 * S, true)); // a red band where the hacksaw went
  hinge.add(zone(bx(36 * S, 22 * S, 110 * S, SO.wood, 0, -4 * S, -70 * S), 'a')); // splinter forend
  for (let i = 0; i < 2; i++) { // two shells in the chambers, rims flush with the breech face
    const sh = grp('shell' + (i + 1), (i ? 1 : -1) * 11 * S, 16 * S, 0);
    sh.add(cz(9.8 * S, 6 * S, SO.brass, 0, 0, -3 * S, 10)); sh.add(cz(9 * S, 55 * S, SO.hull, 0, 0, -32 * S, 10));
    hinge.add(sh);
  }
  g.add(hinge);
  // the action (case-hardened), top lever, two hammers, two triggers, the guard, a sawn-off grip
  g.add(bx(46 * S, 46 * S, 70 * S, SO.case, 0, BY - 6 * S, HZ + 35 * S));
  g.add(bx(46 * S, 10 * S, 30 * S, SO.case, 0, BY - 26 * S, HZ + 6 * S)); // under the pin
  g.add(tilt(bx(8 * S, 6 * S, 30 * S, SO.steel, 0, BY + 19 * S, HZ + 70 * S), 0, 0.5)); // top lever
  for (let i = 0; i < 2; i++) {
    const h = grp(i ? 'hammerR' : 'hammerL', (i ? 1 : -1) * 13 * S, BY + 8 * S, HZ + 66 * S);
    h.add(tilt(bx(7 * S, 26 * S, 8 * S, SO.steel, 0, 12 * S, 4 * S), 0.45)); h.add(bx(9 * S, 5 * S, 9 * S, SO.steel, 0, 24 * S, 11 * S));
    g.add(h);
  }
  g.add(bx(8 * S, 4 * S, 56 * S, SO.steel, 0, BY - 58 * S, HZ + 50 * S)); // guard
  for (let i = 0; i < 2; i++) g.add(bx(4 * S, 18 * S, 4 * S, SO.brass, 0, BY - 44 * S, HZ + (40 + i * 14) * S));
  const grip = grp('grip', 0, BY - 20 * S, HZ + 85 * S); grip.rotation.x = -0.55;
  grip.add(zone(bx(34 * S, 110 * S, 40 * S, SO.wood, 0, -55 * S, 0), 'a'));
  grip.add(bx(36 * S, 8 * S, 44 * S, SO.red, 0, -112 * S, 0)); // the hacksawed end, painted
  g.add(grip);
  g.userData.muzzle = new THREE.Vector3(0, BY, MZ);
  g.userData.sight = { y: BY + 18 * S, z: HZ + 62 * S }; // down the rib between the hammers, onto the bead
  g.userData.len = 0.48;
}
