// Code models for the new secondaries + the speed trap's radar gun (the Blender .glb versions swap in over these; these
// set the muzzle / sight / hat spots they keep). Game space: x right, y up, -z forward, metres, grip around the origin.
// Wrap zones are set per part (userData.wz): A = body / grip, B = business end, N = decals that keep their look.
import * as THREE from 'three';
import { M } from './models.js';
import { jankify } from './jank.js';

const tag = (m, wz) => { m.userData.wz = wz; return m; };
function bx(w, h, d, c, x, y, z, wz = 'a', basic = false) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c, basic)); m.position.set(x, y, z); return tag(m, wz); }
function cz(r0, r1, len, c, x, y, z, wz = 'b', seg = 10, basic = false) { const g = new THREE.CylinderGeometry(r1, r0, len, seg); g.rotateX(-Math.PI / 2); const m = new THREE.Mesh(g, M(c, basic)); m.position.set(x, y, z); return tag(m, wz); } // r0 at the back, r1 at the front
function cy(r, len, c, x, y, z, wz = 'n', seg = 10, basic = false) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), M(c, basic)); m.position.set(x, y, z); return tag(m, wz); } // upright
function grip(g, c, x, y, z, tilt = 0.32, h = 0.12) { const m = bx(0.04, h, 0.058, c, x, y, z); m.rotation.x = tilt; g.add(m); return m; }
function guard(g, c, z0, z1, y) { // a trigger guard loop + trigger
  g.add(bx(0.008, 0.008, z1 - z0, c, 0, y - 0.035, (z0 + z1) / 2, 'n'));
  g.add(bx(0.008, 0.035, 0.008, c, 0, y - 0.018, z0, 'n'));
  const t = bx(0.007, 0.028, 0.009, 0x222222, 0, y - 0.02, z0 + (z1 - z0) * 0.55, 'n'); t.rotation.x = -0.35; g.add(t);
}
const glassy = (c, o) => { const m = jankify(new THREE.MeshLambertMaterial({ color: c, transparent: true, opacity: o, depthWrite: false })); return m; };

// a 3-digit red LED readout the client writes the speed onto (radar gun) or a little screen (remote)
export function ledScreen(w, h, label) {
  const cv = document.createElement('canvas'); cv.width = 96; cv.height = 40;
  const tex = new THREE.CanvasTexture(cv); tex.magFilter = THREE.NearestFilter; tex.minFilter = THREE.NearestFilter;
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
  mesh.userData.noWrap = true; mesh.userData.wz = 'n';
  const set = (txt, col = '#ff2a2a') => {
    const x = cv.getContext('2d');
    x.fillStyle = '#1a0606'; x.fillRect(0, 0, 96, 40);
    x.font = 'bold 30px monospace'; x.textAlign = 'right'; x.textBaseline = 'middle';
    x.fillStyle = 'rgba(255,40,40,0.13)'; x.fillText('888', 90, 22); // the unlit segments
    x.fillStyle = col; x.fillText(String(txt).slice(-3), 90, 22);
    if (label) { x.font = 'bold 9px monospace'; x.textAlign = 'left'; x.fillStyle = '#ff9a9a'; x.fillText(label, 3, 8); }
    tex.needsUpdate = true;
  };
  set('---');
  mesh.userData.set = set;
  return mesh;
}

export const SEC_WB = {
  // a chunky plastic squirt pistol: blue body, a clear tank of water on top, a yellow pump under the nose, orange nozzle
  water(g) {
    const BODY = 0x2a8cff, DARK = 0x1c62c8, PUMP = 0xffd23b, NOZ = 0xff7a1a;
    g.add(bx(0.052, 0.07, 0.2, BODY, 0, 0.012, -0.05));
    g.add(bx(0.044, 0.05, 0.06, BODY, 0, 0.0, -0.175)); // the nose
    grip(g, DARK, 0, -0.068, 0.07);
    guard(g, PUMP, -0.005, 0.045, -0.02);
    // the tank: a clear bottle laid along the top, two thirds full of water
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(0.036, 0.036, 0.15, 12), glassy(0xcff6ff, 0.35)); tank.rotation.x = Math.PI / 2;
    tank.position.set(0, 0.083, -0.03); tank.renderOrder = 2; tank.userData.noWrap = true; tank.userData.wz = 'n'; g.add(tank);
    const water = new THREE.Mesh(new THREE.BoxGeometry(0.052, 0.04, 0.14), glassy(0x2fb6ff, 0.75)); water.position.set(0, 0.07, -0.03);
    water.renderOrder = 1; water.userData.noWrap = true; water.userData.wz = 'n'; g.add(water); g.userData.water = water;
    g.add(cz(0.03, 0.03, 0.02, NOZ, 0, 0.083, 0.055, 'b', 10)); // the filler cap at the back
    g.add(cz(0.037, 0.037, 0.012, PUMP, 0, 0.083, -0.105, 'b', 12)); // tank collar
    // pump handle under the barrel, on a rod
    g.add(cz(0.007, 0.007, 0.11, 0xdddddd, 0, -0.03, -0.2, 'b', 6));
    const pump = cz(0.022, 0.022, 0.075, PUMP, 0, -0.03, -0.215, 'b', 10); g.add(pump); g.userData.pump = pump;
    for (let i = 0; i < 3; i++) g.add(cz(0.024, 0.024, 0.006, 0xe0a810, 0, -0.03, -0.192 - i * 0.022, 'n', 10));
    // nozzle
    g.add(cz(0.017, 0.012, 0.07, NOZ, 0, 0.01, -0.235, 'b', 10));
    g.add(cz(0.006, 0.004, 0.02, 0x222222, 0, 0.01, -0.275, 'b', 6));
    // sights: a bead on the tank collar, a notch at the back
    g.add(bx(0.008, 0.016, 0.008, NOZ, 0, 0.125, -0.105, 'n'));
    for (const s of [-1, 1]) g.add(bx(0.007, 0.018, 0.01, NOZ, s * 0.01, 0.126, 0.04, 'n'));
    g.userData.sight = { y: 0.13, z: 0.04 };
    g.userData.muzzle = new THREE.Vector3(0, 0.01, -0.29);
    g.userData.len = 0.4;
  },
  // a stun gun: yellow polymer body, black grip, a black cartridge in the nose with two dart ports, a laser under it
  taser(g) {
    const BODY = 0xe8ff3a, BLK = 0x1a1a1e, CART = 0x26262c;
    g.add(bx(0.044, 0.062, 0.15, BODY, 0, 0.012, -0.045));
    g.add(bx(0.03, 0.012, 0.13, BLK, 0, 0.049, -0.045, 'b')); // top strip
    grip(g, BLK, 0, -0.066, 0.06, 0.25, 0.115);
    guard(g, BLK, -0.03, 0.02, -0.02);
    // the cartridge: a black block with a yellow band, two ports in its face
    g.add(bx(0.05, 0.068, 0.05, CART, 0, 0.012, -0.142, 'b'));
    g.add(bx(0.052, 0.012, 0.03, BODY, 0, 0.04, -0.142, 'n'));
    for (const y of [0.028, -0.004]) {
      g.add(cz(0.008, 0.008, 0.012, 0xb8bcc4, 0, y, -0.168, 'b', 8));
      g.add(cz(0.004, 0.004, 0.004, 0x050505, 0, y, -0.175, 'n', 6, true));
    }
    const lens = cz(0.006, 0.006, 0.01, 0xff2020, 0, -0.03, -0.12, 'n', 8, true); g.add(lens); // the laser
    g.add(bx(0.02, 0.016, 0.05, BLK, 0, -0.03, -0.1, 'b'));
    const led = bx(0.012, 0.006, 0.012, 0x39ff14, 0, 0.044, 0.02, 'n', true); g.add(led); g.userData.led = led; // ARMED
    // sights: notch + post on the top strip
    g.add(bx(0.006, 0.012, 0.006, BODY, 0, 0.061, -0.105, 'n'));
    for (const s of [-1, 1]) g.add(bx(0.006, 0.014, 0.008, BLK, s * 0.009, 0.062, 0.01, 'n'));
    g.userData.sight = { y: 0.066, z: 0.01 };
    g.userData.muzzle = new THREE.Vector3(0, 0.012, -0.172);
    g.userData.len = 0.26;
  },
  // a fat old tv remote: rubber buttons, a red power button, the big PAUSE and REWIND keys, the IR window at the front
  remote(g) {
    const BODY = 0x2a2a31, BTN = 0x6a6a74;
    g.add(bx(0.05, 0.026, 0.21, BODY, 0, 0.0, -0.06));
    g.add(bx(0.044, 0.012, 0.18, 0x34343c, 0, 0.016, -0.055)); // the raised button deck
    g.add(bx(0.052, 0.03, 0.015, 0x401010, 0, 0.0, -0.17, 'n')); // the IR window
    g.add(cy(0.008, 0.008, 0xd01c1c, 0.012, 0.024, -0.14, 'n', 10)); // power
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) g.add(cy(0.0045, 0.006, BTN, (c - 1) * 0.013, 0.024, -0.112 + r * 0.014, 'n', 6)); // number pad
    g.add(bx(0.016, 0.007, 0.016, 0x2e7bff, -0.01, 0.025, -0.055, 'n')); // PAUSE
    g.add(bx(0.016, 0.007, 0.016, 0xff5a8a, 0.01, 0.025, -0.055, 'n')); // REWIND
    for (let i = 0; i < 2; i++) g.add(bx(0.003, 0.003, 0.009, 0xffffff, -0.013 + i * 0.006, 0.029, -0.055, 'n', true)); // ‖ on pause
    g.add(cy(0.006, 0.006, BTN, 0, 0.024, -0.025, 'n', 8)); // ok
    for (let i = 0; i < 4; i++) g.add(bx(0.03, 0.004, 0.004, 0x1c1c22, 0, 0.022, 0.0 + i * 0.008, 'n')); // grippy ridges
    g.add(bx(0.03, 0.004, 0.04, 0x1c1c22, 0, -0.014, 0.0, 'n')); // battery door
    const ir = bx(0.012, 0.01, 0.004, 0xff3030, 0, 0.0, -0.178, 'n', true); g.add(ir); g.userData.ir = ir;
    g.userData.muzzle = new THREE.Vector3(0, 0.0, -0.18);
    g.userData.len = 0.24;
  },
  // a hand-held police radar gun: pistol grip, a black horn up front, the LED speed readout on the back facing you
  radar(g) {
    const BODY = 0x3a3f4a, BLK = 0x16161a, BLUE = 0x2e7bff;
    g.add(bx(0.06, 0.07, 0.12, BODY, 0, 0.03, -0.03));
    g.add(bx(0.062, 0.012, 0.12, BLUE, 0, 0.0, -0.03, 'n')); // police stripe
    grip(g, BLK, 0, -0.05, 0.03, 0.18, 0.11);
    guard(g, BLK, -0.03, 0.015, -0.005);
    const horn = cz(0.032, 0.05, 0.11, BLK, 0, 0.03, -0.145, 'b', 14); g.add(horn);
    g.add(cz(0.046, 0.046, 0.006, 0x222833, 0, 0.03, -0.2, 'b', 14));
    // the readout box on the back
    g.add(bx(0.056, 0.04, 0.02, BLK, 0, 0.06, 0.04, 'b'));
    const scr = ledScreen(0.048, 0.022, 'KM/H'); scr.position.set(0, 0.06, 0.0505); g.add(scr); g.userData.screen = scr; // faces you (+z)
    const lamp = bx(0.012, 0.008, 0.012, 0xff2020, 0.022, 0.068, -0.0, 'n', true); g.add(lamp); g.userData.lamp = lamp;
    g.userData.muzzle = new THREE.Vector3(0, 0.03, -0.205);
    g.userData.len = 0.28;
  },
};
// where a hat sits on each one, and how tall
export const SEC_HATS = { water: [[0, 0.12, -0.03], 0.07], taser: [[0, 0.056, -0.05], 0.06], remote: [[0, 0.03, -0.06], 0.05], radar: [[0, 0.08, 0.04], 0.06] };
// a Blender model swapped in (models.js buildWeapon): find its moving / glowing bits by part name, and put the radar
// gun's readout where its `screen` metadata says ([x, y, z, w, h], facing +z)
export function secAuthored(id, g, mt) {
  if (!SEC_WB[id]) return;
  const find = (pre) => { let f = null; g.traverse((o) => { if (!f && o.name && o.name.toLowerCase().startsWith(pre)) f = o; }); return f; };
  for (const k of ['water', 'pump', 'led', 'ir', 'lamp']) { const o = find(k); if (o) g.userData[k] = o; else delete g.userData[k]; }
  delete g.userData.screen;
  const s = Array.isArray(mt.screen) && mt.screen.length === 5 && mt.screen.every(Number.isFinite) ? mt.screen : null;
  if (s) { const scr = ledScreen(s[3], s[4], 'KM/H'); scr.position.set(s[0], s[1], s[2]); g.add(scr); g.userData.screen = scr; }
}
