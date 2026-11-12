// WRECKING BALL, the code stand-in (until public/models/x_mech_wrecking.glb lands; same joint, marker and clip names as
// the hero model, agreed with the mech art session). A 4 m hamster ball: steel side caps on the axle, a clear rolling
// tread with grip bars, a hamster wheel inside with the pilot in it (it spins with every roll: the jank), a hazard-
// striped yoke ring round the middle that never rolls, a pail handle with the chain's shackle, fold-out stabiliser feet
// and two little rockets for the PILE DRIVER. Space: faces -z, ball on y = 0, centre at y = 2.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { G } from './ctx.js';
import { cbox } from './rigmodel.js';
import { Chain } from './wreck.js';

const R = 2, C = [0, R, 0];
// the skeleton: name -> [pivot (game coords, at rest), parent]
const PIV = {
  hips: [[0, R, 0], 'root'], ball: [[0, R, 0], 'hips'], cage: [[0, R, 0], 'hips'], yoke: [[0, R, 0], 'hips'],
  handle: [[0, R, 0], 'yoke'], foot_L: [[-1.75, 1.05, 0], 'yoke'], foot_R: [[1.75, 1.05, 0], 'yoke'], hook: [[0, 4.62, 0], 'root'],
};
const MK = {
  mk_chain: ['handle', [0, 4.42, 0]], mk_hook_eye: ['hook', [0, 4.78, 0]], mk_window: ['yoke', [0, R, -2.3]],
  mk_seat: ['cage', [0, 0.75, 0]], mk_eject: ['yoke', [0, 4.2, 0]], mk_mark: ['yoke', [0, 5.3, 0]],
  mk_thrust_L: ['yoke', [-1.45, 1.55, 0.95]], mk_thrust_R: ['yoke', [1.45, 1.55, 0.95]], mk_slam: ['hips', [0, 0, 0]],
};

// ------------------------------------------------------------ materials (shared by every ball)
const mats = new Map();
const cached = (k, mk) => mats.get(k) || mats.set(k, mk()).get(k);
const steel = () => cached('steel', () => new THREE.MeshPhongMaterial({ color: 0x8f99a6, specular: 0xdde6f0, shininess: 90, flatShading: true, emissive: 0x14181c }));
const dark = () => cached('dark', () => new THREE.MeshLambertMaterial({ color: 0x2b3038, flatShading: true, emissive: 0x08090b }));
const chrome = () => cached('chrome', () => new THREE.MeshPhongMaterial({ color: 0xd8dee6, specular: 0xffffff, shininess: 130, flatShading: true, emissive: 0x1a1d22 }));
const yellow = () => cached('yel', () => new THREE.MeshLambertMaterial({ color: 0xffd23a, flatShading: true, emissive: 0x3a2a00 }));
const glass = () => cached('glass', () => new THREE.MeshPhongMaterial({ color: 0x9fe8ff, specular: 0xffffff, shininess: 160, transparent: true, opacity: 0.26, depthWrite: false, side: THREE.DoubleSide, emissive: 0x0b2a36 }));
const skin = () => cached('skin', () => new THREE.MeshLambertMaterial({ color: 0xe6cba2, flatShading: true }));
const glowW = () => cached('glow', () => new THREE.MeshBasicMaterial({ color: 0xfff3b0 }));
// the yoke's hazard stripes: a canvas texture (yellow / black diagonals)
function hazard() {
  return cached('hazard', () => {
    const c = document.createElement('canvas'); c.width = 256; c.height = 32;
    const g = c.getContext('2d');
    g.fillStyle = '#ffd23a'; g.fillRect(0, 0, 256, 32);
    g.fillStyle = '#16161a';
    for (let x = -32; x < 288; x += 32) { g.beginPath(); g.moveTo(x, 32); g.lineTo(x + 16, 32); g.lineTo(x + 32, 0); g.lineTo(x + 16, 0); g.closePath(); g.fill(); }
    const t = new THREE.CanvasTexture(c); t.wrapS = THREE.RepeatWrapping; t.repeat.set(6, 1); t.colorSpace = THREE.SRGBColorSpace;
    return new THREE.MeshLambertMaterial({ map: t, side: THREE.DoubleSide, emissive: 0x201800 });
  });
}
// geometry shared by every ball
let GEO = null;
function geo() {
  if (GEO) return GEO;
  const th = Math.acos(0.3); // the caps cover |x| > 0.6 m (of the 2 m radius)
  const capR = new THREE.SphereGeometry(R, 22, 8, 0, Math.PI * 2, 0, th).rotateZ(-Math.PI / 2);
  const capL = new THREE.SphereGeometry(R, 22, 8, 0, Math.PI * 2, 0, th).rotateZ(Math.PI / 2);
  const belt = new THREE.SphereGeometry(R * 0.985, 26, 6, 0, Math.PI * 2, th, Math.PI - 2 * th).rotateZ(Math.PI / 2);
  const rv = [], bars = [];
  const rr = Math.sqrt(R * R - 0.36);
  for (const sx of [-1, 1]) for (let i = 0; i < 18; i++) { const a = i / 18 * Math.PI * 2, g = new THREE.SphereGeometry(0.06, 5, 3); g.translate(sx * 0.62, Math.cos(a) * rr, Math.sin(a) * rr); rv.push(g); }
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2, g = new THREE.BoxGeometry(1.2, 0.07, 0.16); g.translate(0, R * 0.99, 0); g.rotateX(a); bars.push(g); } // grip bars on the tread (they show it rolling)
  const cg = [];
  for (const sx of [-0.5, 0.5]) cg.push(new THREE.TorusGeometry(1.5, 0.055, 5, 26).rotateY(Math.PI / 2).translate(sx, 0, 0));
  for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2, g = new THREE.CylinderGeometry(0.035, 0.035, 1.0, 5).rotateZ(Math.PI / 2); g.translate(0, Math.cos(a) * 1.5, Math.sin(a) * 1.5); cg.push(g); }
  for (const sx of [-0.5, 0.5]) for (let i = 0; i < 4; i++) { const g = new THREE.BoxGeometry(0.04, 3.0, 0.05); g.rotateX(i * Math.PI / 4); g.translate(sx, 0, 0); cg.push(g); } // the wheel's spokes
  GEO = { capR, capL, belt, rivets: mergeGeometries(rv), bars: mergeGeometries(bars), cage: mergeGeometries(cg),
    band: new THREE.CylinderGeometry(R + 0.2, R + 0.2, 0.44, 40, 1, true), rim: new THREE.TorusGeometry(R + 0.2, 0.05, 4, 40).rotateX(Math.PI / 2),
    handle: new THREE.TorusGeometry(2.42, 0.09, 6, 24, Math.PI), port: new THREE.TorusGeometry(0.46, 0.1, 6, 18), stripe: new THREE.TorusGeometry(1.53, 0.09, 4, 30).rotateY(Math.PI / 2) };
  return GEO;
}
function add(parent, g, m, p = [0, 0, 0], r = null) { const o = new THREE.Mesh(g, m); o.position.fromArray(p); if (r) o.rotation.set(r[0], r[1], r[2]); parent.add(o); return o; }
const loc = (j, w) => [w[0] - j.userData.at[0], w[1] - j.userData.at[1], w[2] - j.userData.at[2]];

// ------------------------------------------------------------ build (j: the joints, made from PIV; own: your materials)
function build(j, own) {
  const g = geo(), acc = own.accent;
  // ball: the steel caps (on the axle), the clear tread, grip bars, rivets, a ring of your paint on each cap
  add(j.ball, g.capR, steel()); add(j.ball, g.capL, steel());
  add(j.ball, g.belt, glass()).renderOrder = 3;
  add(j.ball, g.bars, chrome());
  add(j.ball, g.rivets, chrome());
  for (const sx of [-1.3, 1.3]) add(j.ball, g.stripe, acc, [sx, 0, 0]);
  for (const sx of [-1, 1]) add(j.ball, cbox(0.1, 0.5, 0.5, 0.04), dark(), [sx * 1.98, 0, 0]); // the hub plates
  // cage: the hamster wheel and the pilot running in it (it spins with every roll: you go round with it)
  add(j.cage, g.cage, chrome());
  const pil = new THREE.Group(); pil.position.set(0, -1.08, 0); j.cage.add(pil);
  const body = add(pil, cbox(0.34, 0.42, 0.22, 0.05), acc, [0, 0.5, 0]);
  add(pil, new THREE.SphereGeometry(0.15, 8, 6), skin(), [0, 0.84, 0]);
  add(pil, cbox(0.3, 0.07, 0.06, 0.02), dark(), [0, 0.86, -0.13]); // goggles
  const legs = [-0.09, 0.09].map((x) => { const l = new THREE.Group(); l.position.set(x, 0.3, 0); pil.add(l); add(l, cbox(0.11, 0.32, 0.12, 0.03), dark(), [0, -0.16, 0]); return l; });
  const arms = [-0.22, 0.22].map((x) => { const a = new THREE.Group(); a.position.set(x, 0.66, 0); pil.add(a); add(a, cbox(0.09, 0.3, 0.09, 0.03), acc, [0, -0.14, 0]); return a; });
  j.cage.userData.pilot = { g: pil, legs, arms, body };
  // yoke: the hazard ring round the middle, its rims, the axle pins, the porthole at the front, rockets under it
  add(j.yoke, g.band, hazard());
  for (const y of [-0.24, 0.24]) add(j.yoke, g.rim, dark(), [0, y, 0]);
  for (const sx of [-1, 1]) {
    add(j.yoke, new THREE.CylinderGeometry(0.3, 0.34, 0.5, 10).rotateZ(Math.PI / 2), dark(), [sx * 2.2, 0, 0]);
    add(j.yoke, new THREE.CylinderGeometry(0.2, 0.2, 0.12, 10).rotateZ(Math.PI / 2), acc, [sx * 2.5, 0, 0]);
    add(j.yoke, new THREE.CylinderGeometry(0.17, 0.22, 0.55, 8), dark(), loc(j.yoke, [sx * 1.45, 1.85, 0.95])); // rocket pods
    add(j.yoke, new THREE.CylinderGeometry(0.12, 0.17, 0.12, 8), chrome(), loc(j.yoke, [sx * 1.45, 1.53, 0.95]));
  }
  add(j.yoke, g.port, chrome(), [0, 0, -2.3]);
  add(j.yoke, new THREE.TorusGeometry(0.38, 0.045, 4, 18), own.hatch, [0, 0, -2.33]); // (the hatch glow: lit when it's empty and waiting)
  for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; add(j.yoke, new THREE.SphereGeometry(0.045, 4, 3), chrome(), [Math.cos(a) * 0.46, Math.sin(a) * 0.46, -2.42]); }
  add(j.yoke, cbox(0.5, 0.16, 0.06, 0.02), yellow(), [0, 0.68, -2.27]); // the little "WB-1" plate over the porthole
  // handle: a pail handle over the top from axle to axle, with the shackle at the top
  add(j.handle, g.handle, yellow());
  add(j.handle, cbox(0.36, 0.14, 0.3, 0.04), dark(), [0, 2.42, 0]);
  add(j.handle, new THREE.TorusGeometry(0.16, 0.05, 5, 12).rotateY(Math.PI / 2), chrome(), [0, 2.62, 0]);
  // feet: struts with pads (rest = folded out, standing on the floor)
  for (const [k, sx] of [['foot_L', -1], ['foot_R', 1]]) {
    const f = j[k], a = f.userData.at, tip = [sx * 2.45, 0.12, 0], v = new THREE.Vector3(tip[0] - a[0], tip[1] - a[1], 0), l = v.length();
    const st = add(f, cbox(0.22, l, 0.3, 0.05), dark()); st.position.copy(v.clone().multiplyScalar(0.5)); st.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.normalize());
    add(f, cbox(0.7, 0.14, 0.62, 0.05), yellow(), loc(f, [sx * 2.5, 0.07, 0]));
    add(f, new THREE.CylinderGeometry(0.13, 0.13, 0.36, 8).rotateX(Math.PI / 2), chrome(), [0, 0, 0]);
  }
  // hook: parked on the shackle (the chain moves it)
  const hk = add(j.hook, new THREE.TorusGeometry(0.34, 0.09, 6, 14, Math.PI * 1.35), chrome(), [0, -0.3, 0], [0, 0, Math.PI * 0.95]);
  add(j.hook, cbox(0.14, 0.5, 0.14, 0.03), chrome(), [0.0, 0.08, 0]);
  add(j.hook, new THREE.SphereGeometry(0.08, 6, 4), glowW(), [0.33, -0.3, 0]);
  hk.userData.hook = true;
}

// ------------------------------------------------------------ pose
// s (from mech.js + the play kit): spd, fwd, side, air, vy, landT, landK, empty, falling, boost, rev (0/1), chain
// (world point or null), slam (0 / 1 up / 2 down), pile (0 / 1 up / 2 hang / 3 down)
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const _q = new THREE.Quaternion(), _ax = new THREE.Vector3(), _v = new THREE.Vector3(), _w = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);
function clipOf(inst, s) {
  if (s.pile === 3) return 'pile_drop';
  if (s.pile) return 'pile_driver';
  if (s.chain) return inst.clips && inst.clips.chain_swing ? 'chain_swing' : 'jump';
  if (s.slam) return 'slam';
  if (s.landT < 0.35) return 'land';
  if (s.air) return 'jump';
  return s.spd > 0.6 || s.rev ? 'roll' : 'idle';
}
// a hero model with clips: the roll matched to the speed, the hamster wheel layered on top, the hook to the chain
function mix(inst, s, dt) {
  if (inst.act && inst.clip === 'roll') { const c = inst.clips.roll; inst.act.timeScale = clamp((s.rev ? 14 : s.spd) / (2 * Math.PI * R) * (c ? c.duration : 1), 0, 6); }
  if (inst.clips.cage_spin) {
    if (!inst.cageAct) { inst.cageAct = inst.mixer.clipAction(inst.clips.cage_spin); inst.cageAct.play(); }
    inst.cageAct.timeScale = 0.6 + s.spd / 5 + (s.rev ? 6 : 0);
  }
  hookTo(inst, s);
}
function pose(inst, s, dt, spr) {
  const j = inst.j, W = inst.wb || (inst.wb = { q: new THREE.Quaternion(), w: new THREE.Vector3(), cage: 0, run: 0 });
  // squash on landings, a little bob while rolling, stretch on the pile driver's rise
  const land = s.landT < 0.45 ? Math.sin(clamp(s.landT / 0.45, 0, 1) * Math.PI) * (0.35 + (s.landK || 0) * 0.65) : 0;
  const sq = spr(inst, 'sq', land * 0.16 - (s.pile === 1 ? 0.1 : 0) - (s.pile === 3 ? 0.12 : 0), 260, dt);
  j.hips.scale.set(1 + sq * 0.6, 1 - sq, 1 + sq * 0.6);
  j.hips.position.y = j.hips.userData.rest[1] - sq * R * 0.9 + (s.rev ? (Math.random() - 0.5) * 0.06 : 0); // (revving: it rattles)
  // the shell rolls: no slipping on the floor, keeps spinning in the air, wheel-spins on a rev
  if (s.rev) W.w.set(-16, 0, 0);
  else if (s.pile === 3) W.w.set(-14, 0, 0);
  else if (!s.air) W.w.set(-(s.fwd || 0) / R, 0, -(s.side || 0) / R);
  else W.w.multiplyScalar(Math.max(0, 1 - dt * 0.4));
  const ang = W.w.length() * dt;
  if (ang > 1e-6) { _q.setFromAxisAngle(_ax.copy(W.w).normalize(), ang); W.q.premultiply(_q); }
  j.ball.quaternion.copy(W.q);
  // the hamster wheel: faster than the shell (the pilot's legging it), the pilot goes round with it
  const spin = s.rev ? -30 : s.pile === 3 ? -20 : -(s.fwd || 0) / 1.5 * 1.3;
  W.cage += (s.air && !s.rev && !s.pile ? spin * 0.4 : spin) * dt;
  j.cage.rotation.x = W.cage;
  const P = j.cage.userData.pilot;
  if (P) { W.run += dt * (2 + Math.abs(spin) * 0.8); const k = Math.sin(W.run * 2.2); P.legs[0].rotation.x = k * 0.9; P.legs[1].rotation.x = -k * 0.9; P.arms[0].rotation.x = -k * 0.8; P.arms[1].rotation.x = k * 0.8; }
  // the yoke leans into the roll (it never rolls), with its built-in wonk
  j.yoke.rotation.x = spr(inst, 'yx', clamp((s.fwd || 0) / 22, -1, 1.6) * 0.07 + (s.pile === 3 ? 0.4 : 0), 70, dt);
  j.yoke.rotation.z = spr(inst, 'yz', -clamp((s.side || 0) / 22, -1, 1) * 0.08 + inst.jank.tilt * 0.5, 70, dt);
  // the handle: trails back when it's going, points up the chain when it's on one, wobbles
  if (!s.chain) {
    j.handle.rotation.x = spr(inst, 'hx', clamp((s.fwd || 0) / 22, -0.8, 1.5) * 0.55 + Math.sin(inst.t * 7) * 0.04 * Math.min(1, s.spd / 8) - (s.air ? clamp(s.vy / 30, -0.4, 0.4) : 0), 50, dt);
    j.handle.rotation.z = spr(inst, 'hz', -clamp((s.side || 0) / 22, -1, 1) * 0.4, 50, dt);
  }
  // feet: out when it stops, revs, slams or waits; tucked while it rolls
  const out = s.empty || s.rev || s.slam === 2 || (!s.air && s.spd < 2.5 && !s.chain && !s.pile) ? 1 : 0;
  for (const [k, sg] of [['foot_L', 1], ['foot_R', -1]]) j[k].rotation.z = spr(inst, k, (1 - out) * -1.6 * sg, 120, dt);
  hookTo(inst, s);
}
// the hook: out at the chain's anchor while it's on one, parked on the shackle otherwise. and the chain between
function hookTo(inst, s) {
  const j = inst.j, hk = j.hook;
  if (!hk) return;
  inst.root.updateMatrixWorld(true);
  const sh = inst.att && inst.att.mk_chain;
  if (s.chain) {
    _v.set(s.chain[0], s.chain[1], s.chain[2]);
    hk.position.copy(inst.root.worldToLocal(_v.clone())).sub(new THREE.Vector3(0, 0.16, 0));
    if (sh) { sh.getWorldPosition(_w); _w.sub(_v).normalize(); hk.quaternion.setFromUnitVectors(Y, _w.applyQuaternion(inst.root.getWorldQuaternion(_q).invert())); }
  } else if (sh) {
    sh.getWorldPosition(_w); hk.position.copy(inst.root.worldToLocal(_w)).add(new THREE.Vector3(0, 0.2, 0)); hk.quaternion.identity();
  }
  // the chain: shackle -> hook eye, instanced links (a slack one sags)
  if (!sh) return;
  if (s.chain && inst.root.visible) {
    if (!inst.wbChain) inst.wbChain = new Chain(G.scene, false);
    sh.getWorldPosition(_w);
    const eye = inst.att.mk_hook_eye ? inst.att.mk_hook_eye.getWorldPosition(new THREE.Vector3()) : _v;
    inst.wbChain.set([_w.x, _w.y, _w.z], [eye.x, eye.y, eye.z], 0.05);
  } else if (inst.wbChain) inst.wbChain.hide();
}
function free(inst) { if (inst.wbChain) { inst.wbChain.dispose(); inst.wbChain = null; } }

export const WBM = { PIV, MK, PRE: 'wb_', build, clipOf, mix, pose, free, ATT: ['ball', 'cage', 'yoke', 'handle', 'hook'] };
