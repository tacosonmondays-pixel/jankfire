// TROLLEY, the code stand-in (until public/models/x_mech_trolley.glb lands; same joint, marker and clip names as the hero
// model, agreed with the mech art session). A 4 m shopping trolley: a chrome wire basket made of real bars (tapered like
// the real thing, the front panel leaning out), a base frame with the bottom rack, four swivel casters (the front-left one
// is bent and wobbles: the passive), a red push bar with your colour on the grips, a red child seat that folds down, a
// pound coin lock on a chain, a rubber bumper in your colour, two little boosters behind for AISLE 5, and a tiny pilot in
// a hi-vis vest pushing it from the footboard. Space: faces -z, wheels on y = 0, the basket from z = -2 to +1.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { cbox } from './rigmodel.js';
import { MECH } from '/shared/mech.js';

// the skeleton: name -> [pivot (game coords, at rest), parent]
const PIV = {
  chassis: [[0, 0.62, 0], 'root'],
  basket: [[0, 1.02, -1.62], 'chassis'], // (hinged at its front-bottom edge: tips forward to scoop and dump)
  seat: [[0, 2.2, 0.98], 'basket'], // the child seat flap, hinged at the top of the back gate
  handle: [[0, 2.32, 1.44], 'chassis'],
  bumper: [[0, 0.78, -1.8], 'chassis'],
  caster_FL: [[-0.72, 0.62, -1.5], 'chassis'], caster_FR: [[0.72, 0.62, -1.5], 'chassis'],
  caster_BL: [[-0.88, 0.62, 1.15], 'chassis'], caster_BR: [[0.88, 0.62, 1.15], 'chassis'],
  wheel_FL: [[-0.72, 0.3, -1.38], 'caster_FL'], wheel_FR: [[0.72, 0.3, -1.38], 'caster_FR'], // (the wheels trail the swivel a little)
  wheel_BL: [[-0.88, 0.3, 1.27], 'caster_BL'], wheel_BR: [[0.88, 0.3, 1.27], 'caster_BR'],
};
const MK = {
  mk_seat: ['chassis', [0, 0.8, 1.95]], mk_rider: ['basket', [-0.2, 1.05, 0.05]], mk_scoop: ['basket', [0, 1.05, -0.95]],
  mk_muzzle: ['handle', [0.55, 2.55, 1.25]], mk_thrust_L: ['chassis', [-0.97, 1.3, 1.86]], mk_thrust_R: ['chassis', [0.97, 1.3, 1.86]],
  mk_eject: ['chassis', [0, 2.9, 1.9]], mk_mark: ['chassis', [0, 3.6, 0]],
};
const WR = 0.3; // wheel radius

// ------------------------------------------------------------ materials (shared by every trolley)
const mats = new Map();
const cached = (k, mk) => mats.get(k) || mats.set(k, mk()).get(k);
const chrome = () => cached('chrome', () => new THREE.MeshPhongMaterial({ color: 0xdfe6ee, specular: 0xffffff, shininess: 140, flatShading: true, emissive: 0x2a3038 }));
const steel = () => cached('steel', () => new THREE.MeshPhongMaterial({ color: 0x9aa4b0, specular: 0xdde6f0, shininess: 90, flatShading: true, emissive: 0x16191d }));
const red = () => cached('red', () => new THREE.MeshPhongMaterial({ color: 0xe8262e, specular: 0xffb0b0, shininess: 70, flatShading: true, emissive: 0x3a0406 }));
const rubber = () => cached('rubber', () => new THREE.MeshLambertMaterial({ color: 0x24272d, flatShading: true, emissive: 0x060708 }));
const dark = () => cached('dark', () => new THREE.MeshLambertMaterial({ color: 0x3a3f48, flatShading: true, emissive: 0x0a0b0d }));
const yellow = () => cached('yel', () => new THREE.MeshLambertMaterial({ color: 0xffe14d, flatShading: true, emissive: 0x4a3a00 }));
const hivis = () => cached('hivis', () => new THREE.MeshLambertMaterial({ color: 0xd8ff3a, flatShading: true, emissive: 0x3a4a00 }));
const white = () => cached('white', () => new THREE.MeshLambertMaterial({ color: 0xf4f4f0, flatShading: true, emissive: 0x303030 }));
const skin = () => cached('skin', () => new THREE.MeshLambertMaterial({ color: 0xe6cba2, flatShading: true }));
const gum = () => cached('gum', () => new THREE.MeshLambertMaterial({ color: 0xff7ad8, flatShading: true, emissive: 0x401030 }));
const gold = () => cached('gold', () => new THREE.MeshPhongMaterial({ color: 0xffc23a, specular: 0xfff0b0, shininess: 110, flatShading: true, emissive: 0x3a2400 }));

// ------------------------------------------------------------ geometry helpers (built in game coords at rest)
const _up = new THREE.Vector3(0, 1, 0);
function tube(a, b, r, seg = 5) {
  const d = new THREE.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), l = d.length();
  const g = new THREE.CylinderGeometry(r, r, l, seg, 1, false);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(_up, d.normalize()));
  return g.translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
}
const lerp3 = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
const inJ = (o, j) => { o.position.set(-j.userData.at[0], -j.userData.at[1], -j.userData.at[2]); return o; }; // a mesh built in world rest coords, in its joint
function add(parent, g, m, p = null, r = null) { const o = new THREE.Mesh(g, m); if (p) o.position.fromArray(p); if (r) o.rotation.set(r[0], r[1], r[2]); parent.add(o); return o; }
const merged = (list) => { const g = mergeGeometries(list); g.userData.shared = true; return g; };

// the basket's corners (bottom / top, front / back; x is the right-hand side, mirrored)
const BF = [0.62, 1.02, -1.62], BB = [0.84, 1.02, 0.92], TF = [0.8, 2.12, -1.98], TB = [0.98, 2.24, 1.02];
const sx = (p, s) => [p[0] * s, p[1], p[2]];
// geometry shared by every trolley (in world rest coords; each piece is moved into its joint's space once)
let GEO = null;
function geo() {
  if (GEO) return GEO;
  const wire = [], rim = [], frame = [], rack = [];
  const W = 0.02, side = (s, h, k) => lerp3(lerp3(sx(BF, s), sx(BB, s), k), lerp3(sx(TF, s), sx(TB, s), k), h); // a point on a side panel
  for (const s of [-1, 1]) {
    for (let i = 1; i < 14; i++) wire.push(tube(side(s, 0, i / 14), side(s, 1, i / 14), W, 4)); // side verticals
    for (const h of [0.34, 0.67]) wire.push(tube(side(s, h, 0), side(s, h, 1), W, 4)); // side horizontals
  }
  const acrossB = (a, u) => lerp3(sx(a, -1), sx(a, 1), u);
  for (let i = 1; i < 9; i++) { const u = i / 9; wire.push(tube(acrossB(BF, u), acrossB(TF, u), W, 4)); } // front panel (it leans out at the top)
  for (const h of [0.34, 0.67]) wire.push(tube(lerp3(sx(BF, -1), sx(TF, -1), h), lerp3(sx(BF, 1), sx(TF, 1), h), W, 4));
  for (let i = 1; i < 10; i++) { const u = i / 10; wire.push(tube(acrossB(BF, u), acrossB(BB, u), W, 4)); } // the floor
  for (const k of [0.33, 0.66]) wire.push(tube(lerp3(sx(BF, -1), sx(BB, -1), k), lerp3(sx(BF, 1), sx(BB, 1), k), W, 4));
  for (let i = 1; i < 10; i++) { const u = i / 10; wire.push(tube(acrossB(BB, u), lerp3(acrossB(BB, u), acrossB(TB, u), 0.52), W, 4)); } // the back gate (the seat flap fills the top)
  wire.push(tube(lerp3(sx(BB, -1), sx(TB, -1), 0.52), lerp3(sx(BB, 1), sx(TB, 1), 0.52), W * 1.5, 4));
  // rims: thicker tubes round the top and bottom, down the corners
  const ring = (pts, r) => { for (let i = 0; i < pts.length; i++) rim.push(tube(pts[i], pts[(i + 1) % pts.length], r, 6)); };
  ring([sx(TF, -1), sx(TF, 1), sx(TB, 1), sx(TB, -1)], 0.042);
  ring([sx(BF, -1), sx(BF, 1), sx(BB, 1), sx(BB, -1)], 0.032);
  for (const s of [-1, 1]) { rim.push(tube(sx(BF, s), sx(TF, s), 0.03, 6)); rim.push(tube(sx(BB, s), sx(TB, s), 0.03, 6)); }
  // the base frame: side rails, cross bars, struts up to the basket, the back legs up to the handle
  const FL = [0.72, 0.62, -1.5], BL = [0.88, 0.62, 1.15], H = [0.98, 2.32, 1.44];
  for (const s of [-1, 1]) {
    frame.push(tube(sx(FL, s), sx(BL, s), 0.05, 6));
    frame.push(tube(sx(FL, s), lerp3(sx(BF, s), sx(BB, s), 0.04), 0.04, 6)); // front strut
    frame.push(tube(lerp3(sx(FL, s), sx(BL, s), 0.55), lerp3(sx(BF, s), sx(BB, s), 0.6), 0.035, 6)); // middle strut
    frame.push(tube(sx(BL, s), sx(H, s), 0.048, 6)); // back leg up to the handle
    frame.push(tube(lerp3(sx(BL, s), sx(H, s), 0.25), sx(BB, s), 0.03, 6)); // brace to the basket
  }
  frame.push(tube(sx(FL, -1), sx(FL, 1), 0.05, 6), tube(sx(BL, -1), sx(BL, 1), 0.05, 6));
  for (let i = 1; i < 8; i++) { const u = i / 8, x = -0.74 + 1.48 * u; rack.push(tube([x, 0.7, -1.35], [x * 1.08, 0.7, 1.0], 0.016, 4)); } // the bottom rack
  for (const z of [-1.35, -0.2, 1.0]) rack.push(tube([-0.76, 0.7, z], [0.8, 0.7, z], 0.022, 4));
  GEO = { wire: merged(wire), rim: merged(rim), frame: merged(frame), rack: merged(rack) };
  return GEO;
}

// ------------------------------------------------------------ build (j: the joints, made from PIV; own: your materials)
function build(j, own) {
  const g = geo(), acc = own.accent;
  // chassis: the frame, the rack, the footboard, the boosters
  inJ(add(j.chassis, g.frame, chrome()), j.chassis); inJ(add(j.chassis, g.rack, steel()), j.chassis);
  add(j.chassis, cbox(0.86, 0.07, 0.8, 0.02), rubber(), [0, 0.78 - 0.62, 1.78]); // the footboard the pilot stands on
  add(j.chassis, cbox(0.88, 0.02, 0.06, 0.008), yellow(), [0, 0.82 - 0.62, 2.16]);
  for (const s of [-1, 1]) {
    const b = new THREE.Group(); b.position.set(s * 0.97, 1.3 - 0.62, 1.55); j.chassis.add(b);
    add(b, new THREE.CylinderGeometry(0.13, 0.15, 0.5, 10).rotateX(Math.PI / 2), chrome());
    add(b, new THREE.CylinderGeometry(0.155, 0.155, 0.1, 10).rotateX(Math.PI / 2), acc, [0, 0, -0.05]);
    add(b, new THREE.ConeGeometry(0.13, 0.14, 10).rotateX(Math.PI / 2), dark(), [0, 0, 0.3]);
    add(b, new THREE.SphereGeometry(0.13, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2).rotateX(-Math.PI / 2), red(), [0, 0, -0.25]); // (a red nose)
    add(j.chassis, tube([s * 0.92, 1.3, 1.35], [s * 0.97, 1.3, 1.45], 0.04), dark()).position.set(0, -0.62, 0);
  }
  // basket: the wire mesh, the rims, a little price-tag sign on the front
  inJ(add(j.basket, g.wire, chrome()), j.basket);
  inJ(add(j.basket, g.rim, chrome()), j.basket);
  add(j.basket, cbox(0.62, 0.3, 0.03, 0.01), yellow(), [0, 0.86, -0.18]).rotation.x = -0.32; // the "AISLE 5" sign on the front
  add(j.basket, cbox(0.5, 0.06, 0.035, 0.01), red(), [0, 0.92, -0.2]).rotation.x = -0.32;
  // seat: the red child seat flap (folded up against the back gate), with its two leg holes
  add(j.seat, cbox(1.5, 0.62, 0.05, 0.02), red(), [0, -0.33, 0.0]);
  for (const s of [-1, 1]) add(j.seat, cbox(0.3, 0.2, 0.06, 0.04), dark(), [s * 0.3, -0.5, 0]);
  add(j.seat, cbox(1.52, 0.06, 0.08, 0.02), red(), [0, -0.02, 0]);
  // handle: the red push bar, your colour on the grips and end caps, the pound coin lock hanging off it
  add(j.handle, new THREE.CylinderGeometry(0.075, 0.075, 2.0, 12).rotateZ(Math.PI / 2), red());
  for (const s of [-1, 1]) {
    add(j.handle, new THREE.CylinderGeometry(0.088, 0.088, 0.38, 12).rotateZ(Math.PI / 2), acc, [s * 0.52, 0, 0]);
    add(j.handle, new THREE.SphereGeometry(0.09, 10, 6), acc, [s * 1.02, 0, 0]);
  }
  add(j.handle, cbox(0.3, 0.1, 0.03, 0.01), white(), [0, 0.0, -0.08]); // a little plate on the bar
  const lock = new THREE.Group(); lock.position.set(-0.78, -0.06, -0.02); j.handle.add(lock); // the pound coin lock
  add(lock, cbox(0.17, 0.24, 0.12, 0.025), red(), [0, -0.1, 0]);
  add(lock, new THREE.CylinderGeometry(0.06, 0.06, 0.015, 14).rotateZ(Math.PI / 2), gold(), [0, -0.01, 0]); // the coin, half in the slot
  for (let i = 0; i < 4; i++) add(lock, new THREE.TorusGeometry(0.035, 0.01, 4, 8), steel(), [0, -0.26 - i * 0.06, 0], [0, i % 2 ? Math.PI / 2 : 0, 0]);
  add(lock, cbox(0.07, 0.1, 0.04, 0.01), red(), [0, -0.52, 0]);
  j.handle.userData.lock = lock;
  // bumper: rubber, in your colour, round the front
  add(j.bumper, cbox(1.68, 0.18, 0.2, 0.06), acc);
  for (const s of [-1, 1]) add(j.bumper, cbox(0.2, 0.18, 0.46, 0.06), acc, [s * 0.86, 0, 0.16]);
  // casters: swivel plate + fork; the wheel: rubber tyre, chrome hub, a hub cap with a stripe (so you see it spin)
  for (const k of ['FL', 'FR', 'BL', 'BR']) {
    const c = j['caster_' + k], w = j['wheel_' + k], s = k[1] === 'L' ? -1 : 1, trail = w.userData.rest[2], wonky = k === 'FL';
    add(c, new THREE.CylinderGeometry(0.1, 0.1, 0.06, 10), dark(), [0, 0, 0]);
    const fork = new THREE.Group(); c.add(fork);
    for (const f of [-1, 1]) add(fork, cbox(0.03, 0.36, 0.12, 0.01), steel(), [f * 0.1, -0.17, trail * 0.6]);
    add(fork, cbox(0.24, 0.04, 0.14, 0.01), steel(), [0, -0.02, trail * 0.3]);
    if (wonky) { fork.rotation.z = 0.12; add(fork, new THREE.SphereGeometry(0.05, 6, 4), gum(), [0.11, -0.12, 0.05]); } // bent, with gum on it
    add(w, new THREE.CylinderGeometry(WR, WR, 0.15, 14).rotateZ(Math.PI / 2), rubber());
    add(w, new THREE.CylinderGeometry(0.15, 0.15, 0.17, 10).rotateZ(Math.PI / 2), chrome());
    add(w, cbox(0.02, 0.26, 0.05, 0.005), wonky ? yellow() : red(), [s * 0.09, 0, 0]);
    add(w, cbox(0.02, 0.26, 0.05, 0.005), wonky ? yellow() : red(), [-s * 0.09, 0, 0]);
    c.userData.fork = fork;
  }
  // the pilot: a tiny trolley pusher in your colour with a hi-vis vest and a cap, hands on the bar, on the footboard. it
  // hangs off the bar (pivot at the hands) so it can lean, run, and fly out behind at top speed
  const P = new THREE.Group(); j.handle.add(P);
  const body = new THREE.Group(); P.add(body);
  add(body, cbox(0.38, 0.46, 0.24, 0.06), acc, [0, -0.62, 0.46]);
  add(body, cbox(0.41, 0.34, 0.27, 0.05), hivis(), [0, -0.56, 0.46]);
  for (const y of [-0.52, -0.64]) add(body, cbox(0.42, 0.035, 0.28, 0.01), white(), [0, y, 0.46]);
  const head = new THREE.Group(); head.position.set(0, -0.2, 0.46); body.add(head);
  add(head, new THREE.SphereGeometry(0.15, 10, 8), skin(), [0, 0, 0]);
  add(head, new THREE.CylinderGeometry(0.155, 0.16, 0.08, 10), acc, [0, 0.08, 0]);
  add(head, cbox(0.24, 0.025, 0.14, 0.01), acc, [0, 0.05, -0.15]); // the cap's brim
  for (const s of [-1, 1]) add(head, new THREE.SphereGeometry(0.025, 5, 4), dark(), [s * 0.06, 0.0, -0.135]); // eyes
  const arms = [-1, 1].map((s) => { const a = new THREE.Group(); a.position.set(s * 0.21, -0.42, 0.44); body.add(a); add(a, tube([0, 0, 0], [s * 0.07, 0.42, -0.44], 0.05, 6), acc); add(a, new THREE.SphereGeometry(0.06, 6, 4), skin(), [s * 0.07, 0.42, -0.44]); return a; });
  const legs = [-1, 1].map((s) => { const l = new THREE.Group(); l.position.set(s * 0.1, -0.84, 0.48); body.add(l); add(l, cbox(0.13, 0.6, 0.14, 0.03), dark(), [0, -0.3, 0]); add(l, cbox(0.14, 0.08, 0.24, 0.03), white(), [0, -0.62, -0.05]); return l; });
  j.handle.userData.pilot = { P, body, head, arms, legs };
  // one draw per material per moving part: the static bits under each joint (and the boosters, the forks) baked together
  for (const k of Object.keys(PIV)) pack(j[k], k === 'chassis' ? j.chassis.children.filter((o) => o.isGroup && !Object.hasOwn(PIV, o.name)) : k.startsWith('caster_') ? [j[k].userData.fork] : []);
  for (const o of [lock, body, head, ...arms, ...legs]) pack(o, []);
}
// merge a node's own meshes (+ those of the static groups in `fold`) by material, in the node's space
const _m = new THREE.Matrix4();
function pack(node, fold) {
  const by = new Map();
  const take = (m, pre) => { if (!m.isMesh) return; m.updateMatrix(); _m.copy(m.matrix); if (pre) _m.premultiply(pre); (by.get(m.material) || by.set(m.material, []).get(m.material)).push([m, _m.clone()]); };
  for (const m of node.children) take(m, null);
  for (const g of fold) { g.updateMatrix(); for (const m of g.children) take(m, g.matrix); }
  for (const [mat, list] of by) {
    if (list.length < 2) continue;
    const geos = list.map(([m, mx]) => { let g = m.geometry.clone(); for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k); if (g.index) g = g.toNonIndexed(); return g.applyMatrix4(mx); });
    const mg = mergeGeometries(geos, false);
    for (const g of geos) g.dispose();
    if (!mg) continue; // (shapes that don't merge: left as they are)
    for (const [m] of list) { m.removeFromParent(); if (!m.geometry.userData.shared) m.geometry.dispose(); }
    node.add(new THREE.Mesh(mg, mat));
  }
  for (const g of fold) if (!g.children.length) g.removeFromParent();
}

// ------------------------------------------------------------ pose
// s (from mech.js + the play kit): spd, fwd, side, air, vy, landT, landK, empty, boost, drift (0/1), push (0..1 through
// the lunge, else 0), aisle, rider, scoopT / dumpT / tossT (s since), n (people in the basket), brake
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
function clipOf(inst, s) {
  if (s.dumpT < 0.9) return 'dump';
  if (s.scoopT < 0.5) return 'scoop';
  if (s.push) return 'push';
  if (s.landT < 0.35) return 'land';
  if (s.air) return 'jump';
  if (s.aisle) return 'boost';
  if (s.drift) return 'drift';
  return s.spd > 0.6 ? 'drive' : 'idle';
}
// a hero model with clips: the drive loop matched to the speed (one loop = the wheels turn once), the seat held
function mix(inst, s, dt) {
  if (inst.act && (inst.clip === 'drive' || inst.clip === 'boost')) { const c = inst.clips[inst.clip]; inst.act.timeScale = clamp(s.spd / (2 * Math.PI * WR * (MECH.scale || 1)) * (c ? c.duration : 1), 0, 8); }
  const want = s.rider ? 'seat_down' : 'seat_up';
  if (inst.clips[want] && inst.seatClip !== want) {
    const a = inst.mixer.clipAction(inst.clips[want]); a.reset(); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; a.play();
    if (inst.seatAct) inst.seatAct.fadeOut(0.2);
    inst.seatAct = a; inst.seatClip = want;
  }
}
const angTo = (a, b) => { let d = b - a; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2; return d; };
function pose(inst, s, dt, spr) {
  const j = inst.j, T = inst.t, W = inst.tr || (inst.tr = { wheel: 0, run: 0, sw: { FL: 0, FR: 0, BL: 0, BR: 0 }, bob: 0 });
  const spd = s.spd || 0, fwd = s.fwd || 0, side = s.side || 0, k = clamp(spd / MECH.trolley.speed, 0, 1.4);
  const land = s.landT < 0.45 ? Math.sin(clamp(s.landT / 0.45, 0, 1) * Math.PI) * (0.35 + (s.landK || 0) * 0.65) : 0;
  const push = s.push || 0, pk = push ? Math.sin(Math.min(1, push * 1.4) * Math.PI) : 0;
  // wheels: they roll at the speed it goes (and keep spinning in the air); casters swivel into the way it's going,
  // drift out to 35 degrees, and the front-left one wobbles (the wonky wheel)
  W.wheel -= (s.air ? spd * 0.5 : spd) / (WR * (MECH.scale || 1)) * dt; // (drawn at size 1, the root scaled up)
  const dir = spd > 0.8 ? -Math.atan2(side, fwd) : null, dA = 35 * Math.PI / 180 * (side >= 0 ? -1 : 1);
  for (const c of ['FL', 'FR', 'BL', 'BR']) {
    const want = s.drift && spd > 3 ? dA * (c[0] === 'F' ? 1 : 0.6) : dir == null ? W.sw[c] : dir;
    W.sw[c] += angTo(W.sw[c], want) * Math.min(1, dt * (c[0] === 'F' ? 14 : 9));
    const wob = c === 'FL' ? Math.sin(T * (9 + spd * 0.9)) * 0.35 * Math.min(1, spd / 5 + 0.15) : 0;
    j['caster_' + c].rotation.y = W.sw[c] + wob;
    const w = j['wheel_' + c]; w.rotation.x = W.wheel + (c === 'FL' ? 0.7 : c === 'BR' ? 1.9 : 0);
    if (c === 'FL') w.rotation.z = Math.sin(T * (13 + spd)) * 0.12 * Math.min(1, spd / 4); // (it wobbles on its axle too)
  }
  // chassis: leans into turns and drifts, rattles at speed, squats on AISLE 5's boost and on landings, lunges on a push
  W.bob += dt * (4 + spd * 1.1);
  const rattle = Math.sin(W.bob) * 0.022 * Math.min(1, spd / 8) + (Math.random() - 0.5) * 0.012 * k;
  j.chassis.position.y = j.chassis.userData.rest[1] + rattle - land * 0.22 - (s.aisle ? 0.08 : 0) + (s.empty ? 0 : 0);
  j.chassis.rotation.z = spr(inst, 'cz', -clamp(side / 26, -1, 1) * 0.1 + (s.drift ? (side >= 0 ? -0.11 : 0.11) : 0) + inst.jank.tilt * 0.4, 90, dt);
  j.chassis.rotation.x = spr(inst, 'cx', clamp(fwd / 26, -1, 1.3) * -0.03 + (s.aisle ? 0.06 : 0) - pk * 0.1 + (s.brake ? -0.07 : 0) + (s.air ? clamp(-s.vy / 30, -0.2, 0.2) : 0), 110, dt);
  j.chassis.position.z = -pk * 0.3;
  // basket: tips forward on its front-bottom edge: a quick dip to scoop, all the way to dump, a little on AISLE 5
  const tip = s.dumpT < 0.9 ? -0.95 * Math.min(1, s.dumpT / 0.12) : s.scoopT < 0.5 ? -0.32 * Math.sin(Math.PI * s.scoopT / 0.5) : s.aisle ? -0.07 : 0;
  j.basket.rotation.x = spr(inst, 'bk', tip, s.dumpT < 0.9 ? 260 : 120, dt);
  j.basket.rotation.z = Math.sin(T * 17) * 0.006 * k; // (the wire jiggles)
  // seat: folds down for a rider
  j.seat.rotation.x = spr(inst, 'st', s.rider ? 1.42 : 0, 70, dt);
  // handle + bumper
  j.handle.rotation.x = spr(inst, 'hx', Math.sin(T * 11) * 0.015 * k - pk * 0.06, 120, dt);
  j.bumper.scale.z = 1 - pk * 0.35; j.bumper.scale.x = 1 + pk * 0.08;
  const lock = j.handle.userData.lock;
  if (lock) lock.rotation.x = spr(inst, 'lk', clamp(fwd / 26, -1, 1.4) * 0.9 + Math.sin(T * 7) * 0.08 * k, 25, dt); // (the coin lock swings on its chain)
  // the boosters burn backwards
  for (const f of inst.flames) f.rotation.set(Math.PI / 2, 0, 0);
  // the pilot: stands on the footboard, leans as it speeds up, runs flat out behind it at top speed (feet off the board),
  // swings out in a drift, shoves on a push, flies like a flag on AISLE 5, lets go with one hand to toss a can
  const Pt = j.handle.userData.pilot;
  if (Pt) {
    const run = s.aisle ? 1.45 : clamp((spd - 8) / 16, 0, 1) * 1.05;
    Pt.P.rotation.x = spr(inst, 'px', -run + pk * 0.35 - land * 0.2 + (s.empty ? 0.05 : 0), 60, dt);
    Pt.P.rotation.z = spr(inst, 'pz', s.drift ? (side >= 0 ? 0.55 : -0.55) : -clamp(side / 26, -1, 1) * 0.3, 40, dt);
    Pt.P.rotation.y = spr(inst, 'py', s.drift ? (side >= 0 ? -0.3 : 0.3) : 0, 40, dt);
    W.run += dt * (spd > 1 ? 3 + spd * 0.55 : 0) * (s.aisle ? 1.6 : 1);
    const lg = Math.sin(W.run) * (spd > 1 ? Math.min(1.2, 0.4 + spd / 20) : 0) + (s.air ? 0.5 : 0);
    Pt.legs[0].rotation.x = lg; Pt.legs[1].rotation.x = -lg * (s.air ? -1 : 1);
    Pt.body.rotation.x = Math.sin(W.run * 2) * 0.04 * Math.min(1, spd / 6);
    const toss = s.tossT < 0.35 ? Math.sin(s.tossT / 0.35 * Math.PI) : 0; // (the right arm lets go and lobs one)
    Pt.arms[1].rotation.x = spr(inst, 'ta', -toss * 2.2, 260, dt);
    Pt.arms[0].rotation.x = 0;
    Pt.head.rotation.y = Math.sin(T * 1.3) * 0.15 + (s.drift ? (side >= 0 ? 0.4 : -0.4) : 0);
    Pt.head.rotation.x = s.aisle ? -0.3 : 0;
  }
}
function free() {}

export const TRM = { PIV, MK, PRE: 'tr_', build, clipOf, mix, pose, free, ATT: ['chassis', 'basket', 'seat', 'handle', 'bumper'] };
