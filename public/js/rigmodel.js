// Overdrive Rig killstreak, the looks: a scrap-built juggernaut exo-frame that closes around the mannequin. Mismatched
// salvage plates, hoses, hydraulic pistons, huge mechanical forearms and fists, a spine rack of missile pods, a red visor
// and neon cyan / magenta strips. The shape is built once as a template (joints + one merged mesh per material per
// joint, shared by every rig) and instanced per player with its own glow materials. Also here: the pose (heavy stomping
// walk with planted feet, punches, block, leap crouch, pods), the pistons + hoses that follow the joints, the overdrive
// trail afterimages, the hex overshield flicker, the scrap burst when it dies and the missile model.
import * as THREE from 'three';
import { mergeGeometries, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { G } from './ctx.js';
import { PSys, scaleU } from './fx.js';

// ------------------------------------------------------------ palette: salvage, all slightly different
export const C = {
  // (punchy salvage: the game is bright and saturated, a muddy grey mech disappears against the maps)
  gun: 0x3b4552, steel: 0x7d8a98, rust: 0xc0501f, ochre: 0xf0a81a, olive: 0x71843a, teal: 0x2a8088, cream: 0xe2d6b2,
  black: 0x15171b, chrome: 0xc8d2dc, brass: 0xc79a3a, red: 0xb3231a, hazard: 0xffc81e,
};
export const NEON = { cyan: 0x2ef2ff, mag: 0xff2bd6, visor: 0xff1e1e };
const mats = new Map();
function lam(color, emi = 0.12) {
  const k = 'l' + color + emi;
  if (!mats.has(k)) mats.set(k, new THREE.MeshLambertMaterial({ color, flatShading: true, fog: false, emissive: new THREE.Color(color).multiplyScalar(emi) }));
  return mats.get(k);
}
function shiny(color) {
  const k = 's' + color;
  if (!mats.has(k)) mats.set(k, new THREE.MeshPhongMaterial({ color, specular: 0xdde6f0, shininess: 90, flatShading: true, fog: false, emissive: new THREE.Color(color).multiplyScalar(0.12) }));
  return mats.get(k);
}
function neon(color) {
  const k = 'n' + color;
  if (!mats.has(k)) mats.set(k, new THREE.MeshBasicMaterial({ color, fog: false }));
  return mats.get(k);
}
// material keys a part can use: shared ones, the player's colour (accent) and per-rig glows (they light up on their own)
const SHARED = {
  gun: () => lam(C.gun), steel: () => lam(C.steel), rust: () => lam(C.rust), ochre: () => lam(C.ochre), olive: () => lam(C.olive),
  teal: () => lam(C.teal), cream: () => lam(C.cream), black: () => lam(C.black, 0.05), chrome: () => shiny(C.chrome),
  brass: () => shiny(C.brass), red: () => lam(C.red), hazard: () => lam(C.hazard, 0.16), cyan: () => neon(NEON.cyan), mag: () => neon(NEON.mag),
};
const OWN = ['accent', 'visor', 'glowL', 'glowR', 'screen', 'core'];

// ------------------------------------------------------------ geometry kit
// a box with flat chamfered edges (machined plates read much better than raw boxes)
export function cbox(w, h, d, c = 0.03) {
  const X = w / 2, Y = h / 2, Z = d / 2;
  c = Math.max(0.001, Math.min(c, X * 0.45, Y * 0.45, Z * 0.45));
  const P = [], key = {};
  const v = (x, y, z) => { P.push(x, y, z); return P.length / 3 - 1; };
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
    key[`${sx}${sy}${sz}x`] = v(sx * X, sy * (Y - c), sz * (Z - c));
    key[`${sx}${sy}${sz}y`] = v(sx * (X - c), sy * Y, sz * (Z - c));
    key[`${sx}${sy}${sz}z`] = v(sx * (X - c), sy * (Y - c), sz * Z);
  }
  const k = (sx, sy, sz, a) => key[`${sx}${sy}${sz}${a}`];
  const polys = [];
  for (const s of [-1, 1]) {
    polys.push([k(s, -1, -1, 'x'), k(s, 1, -1, 'x'), k(s, 1, 1, 'x'), k(s, -1, 1, 'x')]);
    polys.push([k(-1, s, -1, 'y'), k(1, s, -1, 'y'), k(1, s, 1, 'y'), k(-1, s, 1, 'y')]);
    polys.push([k(-1, -1, s, 'z'), k(1, -1, s, 'z'), k(1, 1, s, 'z'), k(-1, 1, s, 'z')]);
  }
  for (const a of [-1, 1]) for (const b of [-1, 1]) {
    polys.push([k(a, b, -1, 'x'), k(a, b, 1, 'x'), k(a, b, 1, 'y'), k(a, b, -1, 'y')]); // x-y edges
    polys.push([k(a, -1, b, 'x'), k(a, 1, b, 'x'), k(a, 1, b, 'z'), k(a, -1, b, 'z')]); // x-z edges
    polys.push([k(-1, a, b, 'y'), k(1, a, b, 'y'), k(1, a, b, 'z'), k(-1, a, b, 'z')]); // y-z edges
  }
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) polys.push([k(sx, sy, sz, 'x'), k(sx, sy, sz, 'y'), k(sx, sy, sz, 'z')]);
  const I = [], A = new THREE.Vector3(), B = new THREE.Vector3(), Cc = new THREE.Vector3(), N = new THREE.Vector3();
  for (const p of polys) {
    A.fromArray(P, p[0] * 3); B.fromArray(P, p[1] * 3); Cc.fromArray(P, p[2] * 3);
    N.subVectors(B, A).cross(Cc.sub(A));
    const ctr = [0, 0, 0];
    for (const i of p) { ctr[0] += P[i * 3]; ctr[1] += P[i * 3 + 1]; ctr[2] += P[i * 3 + 2]; }
    const flip = N.x * ctr[0] + N.y * ctr[1] + N.z * ctr[2] < 0; // convex and centred: outward faces away from 0
    const q = flip ? p.slice().reverse() : p;
    for (let i = 1; i < q.length - 1; i++) I.push(q[0], q[i], q[i + 1]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setIndex(I);
  return g;
}
export const cyl = (r0, r1, h, seg = 8) => new THREE.CylinderGeometry(r0, r1, h, seg);
export const cylZ = (r, h, seg = 8) => new THREE.CylinderGeometry(r, r, h, seg).rotateX(Math.PI / 2);
export const cylX = (r, h, seg = 8) => new THREE.CylinderGeometry(r, r, h, seg).rotateZ(Math.PI / 2);
// scale the low end of a geometry along `axis` by kx, ky (the other two axes), fading to 1 at the high end: a wedge
// helmet (z: the front gets narrower), a flared shin or a forearm that swells toward the fist (y: the bottom gets wider)
export function taper(g, kx, ky, axis = 'z') {
  g.computeBoundingBox();
  const bb = g.boundingBox, p = g.attributes.position, ai = axis === 'z' ? 2 : 1, lo = bb.min.getComponent(ai), hi = bb.max.getComponent(ai);
  for (let i = 0; i < p.count; i++) {
    const t = (p.getComponent(i, ai) - lo) / Math.max(1e-6, hi - lo); // 0 at the low end
    const sx = 1 + (kx - 1) * (1 - t), sy = 1 + (ky - 1) * (1 - t);
    if (axis === 'z') { p.setX(i, p.getX(i) * sx); p.setY(i, p.getY(i) * sy); } else { p.setX(i, p.getX(i) * sx); p.setZ(i, p.getZ(i) * sy); }
  }
  p.needsUpdate = true;
  return g;
}

// ------------------------------------------------------------ the template (built once, shared by every rig)
const _m = new THREE.Matrix4(), _e = new THREE.Euler(), _q = new THREE.Quaternion(), _s = new THREE.Vector3(), _p = new THREE.Vector3();
let TPL = null;
function template() {
  if (TPL) return TPL;
  const joints = [], pistons = [], hoses = [], glows = [];
  const J = (name, parent, x, y, z) => { const j = { name, i: joints.length, parent: parent ? parent.i : -1, pos: [x, y, z], parts: new Map(), out: [] }; joints.push(j); return j; };
  // put a part on a joint. o: { r: [rx, ry, rz], small: true = no outline / afterimage (rivets, bolts, grilles) }
  const put = (j, geo, mk, x, y, z, o = {}) => {
    const r = o.r || [0, 0, 0];
    _m.compose(_p.set(x, y, z), _q.setFromEuler(_e.set(r[0], r[1], r[2])), _s.set(1, 1, 1));
    geo.applyMatrix4(_m);
    if (!j.parts.has(mk)) j.parts.set(mk, []);
    j.parts.get(mk).push(geo);
    if (!o.small) j.out.push(geo);
    return geo;
  };
  const bolts = (j, mk, pts, r = 0.018) => { for (const [x, y, z] of pts) put(j, new THREE.SphereGeometry(r, 5, 3), mk, x, y, z, { small: true }); };
  const piston = (ja, a, jb, b, r = 0.045, len = 0.34) => pistons.push({ a: ja.i, pa: a, b: jb.i, pb: b, r, len });
  const hose = (ja, a, jb, b, bend, r = 0.03, rib = true) => hoses.push({ a: ja.i, pa: a, b: jb.i, pb: b, bend, r, rib });

  // ---- skeleton (root = between the feet, facing -z, right = +x). about 2.55 tall: ~1.35x the mannequin, and hunched:
  // the helmet sits low between the shoulders, behind guard plates, with the missile pods up behind it
  const root = J('root', null, 0, 0, 0);
  const hips = J('hips', root, 0, 1.08, 0.02);
  const torso = J('torso', hips, 0, 0.22, 0.04);
  const head = J('head', torso, 0, 0.8, -0.25);
  const rack = J('rack', torso, 0, 0.44, 0.38);
  const podL = J('podL', rack, -0.5, 0.34, 0.06), podR = J('podR', rack, 0.5, 0.34, 0.06);
  const lidL = J('lidL', podL, 0, 0.44, 0.17), lidR = J('lidR', podR, 0, 0.44, 0.17);
  const side = (s) => {
    const x = s === 'R' ? 1 : -1;
    const sh = J('shoulder' + s, torso, 0.66 * x, 0.8, 0.02);
    const pa = J('pauld' + s, torso, 0.66 * x, 0.82, 0.02);
    const fa = J('fore' + s, sh, 0, -0.5, 0);
    const fi = J('fist' + s, fa, 0, -0.62, 0);
    const th = J('thigh' + s, hips, 0.29 * x, -0.02, 0);
    const sn = J('shin' + s, th, 0, -0.48, 0);
    const ft = J('foot' + s, sn, 0, -0.52, 0);
    return { sh, pa, fa, fi, th, sn, ft };
  };
  const R = side('R'), Lf = side('L');

  // ---- pelvis: armoured belt, codpiece, tassets, the hip pistons' mounts
  put(hips, cbox(0.66, 0.2, 0.48, 0.04), 'gun', 0, 0, 0);
  put(hips, cbox(0.7, 0.05, 0.52, 0.02), 'black', 0, 0.1, 0);
  put(hips, cbox(0.24, 0.2, 0.08, 0.03), 'steel', 0, -0.09, -0.26, { r: [0.15, 0, 0] });
  put(hips, cbox(0.14, 0.07, 0.02, 0.008), 'hazard', 0, -0.07, -0.305, { r: [0.15, 0, 0] });
  for (let i = 0; i < 2; i++) put(hips, new THREE.BoxGeometry(0.025, 0.075, 0.01), 'black', -0.025 + i * 0.05, -0.07, -0.318, { r: [0.15, 0, 0.6], small: true });
  put(hips, cbox(0.44, 0.26, 0.07, 0.03), 'rust', 0, -0.1, 0.26, { r: [-0.2, 0, 0] });
  for (const s of [-1, 1]) {
    put(hips, cbox(0.08, 0.32, 0.38, 0.03), s < 0 ? 'gun' : 'steel', s * 0.38, -0.12, 0, { r: [0, 0, s * 0.18] });
    put(hips, cylX(0.08, 0.12), 'chrome', s * 0.33, -0.02, 0);
  }
  bolts(hips, 'chrome', [[-0.25, 0.04, -0.245], [0.25, 0.04, -0.245], [0, 0.04, -0.245], [-0.12, -0.18, 0.29], [0.12, -0.18, 0.29]]);

  // ---- torso: the pilot's flex-suit belly under segmented plates, a huge salvage chest, the reactor core
  put(torso, cbox(0.5, 0.42, 0.42, 0.05), 'black', 0, 0.12, 0);
  for (let i = 0; i < 3; i++) put(torso, cbox(0.46 - i * 0.03, 0.09, 0.08, 0.02), i === 1 ? 'gun' : 'steel', 0, 0.02 + i * 0.12, -0.21, { r: [0.12, 0, 0] });
  for (const s of [-1, 1]) put(torso, cylZ(0.035, 0.3, 6), 'chrome', s * 0.17, 0.16, 0.1, { r: [Math.PI / 2 - 0.1, 0, 0] }); // spine struts
  put(torso, taper(cbox(1.06, 0.7, 0.7, 0.09), 0.9, 0.88), 'gun', 0, 0.6, 0);
  put(torso, cbox(0.92, 0.2, 0.26, 0.05), 'steel', 0, 0.88, -0.14, { r: [0.35, 0, 0] }); // the shelf the helmet sits in
  put(torso, cbox(0.48, 0.34, 0.08, 0.04), 'rust', -0.25, 0.64, -0.36, { r: [-0.1, 0.14, 0.05] }); // left breast plate, rusted through
  put(torso, cbox(0.44, 0.32, 0.08, 0.04), 'accent', 0.25, 0.63, -0.36, { r: [-0.1, -0.16, -0.06] }); // right one, another salvage job
  put(torso, cbox(0.1, 0.3, 0.02, 0.01), 'hazard', 0.33, 0.63, -0.405, { r: [-0.1, -0.16, -0.06] }); // a stripe in your colour
  put(torso, cbox(0.34, 0.32, 0.1, 0.04), 'black', 0, 0.36, -0.35); // core housing
  put(torso, new THREE.CylinderGeometry(0.12, 0.12, 0.05, 12).rotateX(Math.PI / 2), 'core', 0, 0.36, -0.395);
  put(torso, new THREE.TorusGeometry(0.14, 0.025, 4, 12), 'chrome', 0, 0.36, -0.4);
  for (let i = -1; i <= 1; i++) put(torso, new THREE.BoxGeometry(0.28, 0.016, 0.02), 'gun', 0, 0.36 + i * 0.065, -0.425, { small: true }); // grille
  glows.push({ j: torso.i, p: [0, 0.36, -0.46], c: NEON.cyan, s: 0.4, k: 'core' });
  put(torso, new THREE.BoxGeometry(0.035, 0.42, 0.02), 'cyan', -0.5, 0.6, -0.3, { r: [0, 0.3, 0] }); // neon edge strips
  put(torso, new THREE.BoxGeometry(0.035, 0.42, 0.02), 'mag', 0.5, 0.6, -0.3, { r: [0, -0.3, 0] });
  put(torso, new THREE.BoxGeometry(0.6, 0.022, 0.02), 'mag', 0, 0.2, -0.32);
  // salvage details: a stencilled "08" plate, a bent road-sign diamond, rebar welded across the back
  put(torso, cbox(0.2, 0.13, 0.03, 0.01), 'cream', -0.31, 0.42, -0.36, { r: [0, 0.2, 0.1] });
  put(torso, new THREE.BoxGeometry(0.05, 0.085, 0.01), 'black', -0.345, 0.42, -0.38, { r: [0, 0.2, 0.1], small: true });
  put(torso, new THREE.BoxGeometry(0.05, 0.085, 0.01), 'black', -0.28, 0.43, -0.375, { r: [0, 0.2, 0.1], small: true });
  put(torso, cbox(0.22, 0.22, 0.025, 0.01), 'hazard', 0.42, 0.3, -0.26, { r: [0, -0.7, Math.PI / 4] });
  put(torso, new THREE.BoxGeometry(0.035, 0.18, 0.012), 'black', 0.425, 0.3, -0.28, { r: [0, -0.7, Math.PI / 4], small: true });
  for (const s of [-1, 1]) put(torso, cbox(0.1, 0.46, 0.5, 0.03), s < 0 ? 'teal' : 'gun', s * 0.53, 0.52, 0.02, { r: [0, 0, -s * 0.06] }); // ribs under the arms
  put(torso, cbox(0.92, 0.5, 0.12, 0.04), 'steel', 0, 0.64, 0.33, { r: [0.1, 0, 0] }); // back plate
  for (const y of [0.48, 0.78]) put(torso, cylX(0.018, 0.88, 5), 'rust', 0, y, 0.4, { small: true });
  bolts(torso, 'chrome', [[-0.44, 0.88, -0.27], [0.44, 0.88, -0.27], [-0.44, 0.34, -0.3], [0.44, 0.34, -0.3], [-0.38, 0.9, 0.39], [0.38, 0.9, 0.39], [-0.38, 0.42, 0.39], [0.38, 0.42, 0.39]], 0.022);
  for (const s of [-1, 1]) { // exhaust stacks behind the shoulders
    put(torso, cyl(0.055, 0.065, 0.44, 8), 'gun', s * 0.3, 1.02, 0.25, { r: [-0.25, 0, s * 0.1] });
    put(torso, cyl(0.07, 0.07, 0.05, 8), 'rust', s * 0.31, 1.23, 0.2, { r: [-0.25, 0, s * 0.1] });
  }
  glows.push({ j: torso.i, p: [0.31, 1.27, 0.19], c: 0xff7a3a, s: 0.25, k: 'stack', w: 0 }, { j: torso.i, p: [-0.31, 1.27, 0.19], c: 0xff7a3a, s: 0.25, k: 'stack', w: 0 });

  // ---- head: a low wedge helm with a heavy brow and one narrow red slit for a visor, a grille for a jaw
  put(head, taper(cbox(0.4, 0.3, 0.46, 0.06), 0.82, 0.78), 'gun', 0, 0.12, -0.02);
  put(head, cbox(0.44, 0.07, 0.24, 0.025), 'steel', 0, 0.235, -0.16, { r: [0.28, 0, 0] }); // brow: hangs over the visor
  put(head, cbox(0.07, 0.06, 0.38, 0.02), 'rust', 0, 0.3, 0.02); // welded crest
  put(head, cbox(0.3, 0.06, 0.04, 0.012), 'black', 0, 0.15, -0.255); // visor slot
  put(head, new THREE.BoxGeometry(0.27, 0.03, 0.02), 'visor', 0, 0.152, -0.272);
  glows.push({ j: head.i, p: [0, 0.152, -0.31], c: NEON.visor, s: 0.34, k: 'visor', w: 2.2 });
  put(head, cbox(0.28, 0.11, 0.1, 0.03), 'steel', 0, 0.04, -0.24, { r: [-0.2, 0, 0] }); // jaw
  for (let i = -2; i <= 2; i++) put(head, new THREE.BoxGeometry(0.018, 0.07, 0.01), 'black', i * 0.048, 0.035, -0.29, { r: [-0.2, 0, 0], small: true });
  for (const s of [-1, 1]) put(head, cbox(0.07, 0.17, 0.22, 0.02), s < 0 ? 'rust' : 'gun', s * 0.215, 0.12, 0, { r: [0, 0, s * 0.06] }); // cheek plates
  put(head, cylX(0.04, 0.5, 6), 'black', 0, 0.06, 0.13, { small: true }); // neck cable
  put(head, cyl(0.008, 0.008, 0.42, 4), 'chrome', 0.17, 0.45, 0.14, { r: [0.35, 0, -0.14] }); // bent antenna
  put(head, new THREE.SphereGeometry(0.022, 6, 4), 'mag', 0.2, 0.64, 0.21, { small: true });
  put(head, new THREE.BoxGeometry(0.03, 0.025, 0.3), 'cyan', -0.21, 0.22, -0.02, { small: true });

  // ---- spine rack + missile pods (they tip forward over the shoulders and their lids flip open to fire)
  put(rack, cbox(0.18, 0.86, 0.16, 0.03), 'gun', 0, 0.12, 0);
  for (let i = 0; i < 5; i++) put(rack, cbox(0.26, 0.05, 0.2, 0.015), i % 2 ? 'rust' : 'steel', 0, -0.2 + i * 0.16, 0.01);
  put(rack, cylX(0.04, 1.06, 6), 'chrome', 0, 0.34, 0.05);
  for (const [pod, lid, s] of [[podL, lidL, -1], [podR, lidR, 1]]) {
    put(pod, cbox(0.36, 0.44, 0.32, 0.04), s < 0 ? 'olive' : 'gun', 0, 0.21, 0.02);
    put(pod, cbox(0.38, 0.06, 0.34, 0.02), 'black', 0, 0.03, 0.02);
    put(pod, new THREE.BoxGeometry(0.028, 0.36, 0.02), s < 0 ? 'cyan' : 'mag', s * 0.19, 0.22, -0.13);
    put(pod, cbox(0.1, 0.3, 0.05, 0.02), 'hazard', -s * 0.12, 0.24, -0.15);
    put(pod, cbox(0.38, 0.12, 0.34, 0.02), 'accent', 0, 0.36, 0.02); // a band in your colour round each pod
    for (const x of [-0.08, 0.08]) for (const z of [-0.06, 0.08]) { // the tubes, with red tips waiting inside
      put(pod, cyl(0.06, 0.06, 0.06, 8), 'black', x, 0.43, z, { small: true });
      put(pod, new THREE.ConeGeometry(0.045, 0.08, 6), 'red', x, 0.43, z, { small: true });
    }
    put(lid, cbox(0.37, 0.04, 0.33, 0.015), s < 0 ? 'rust' : 'steel', 0, 0.02, -0.16); // hinged at its back edge
    put(lid, new THREE.BoxGeometry(0.3, 0.012, 0.02), 'hazard', 0, 0.045, -0.28, { small: true });
  }

  // ---- arms: shoulder ball, segmented pauldron with a guard plate beside the helm, an upper arm frame, and the giant
  // forearm + fist (the right one punches: a bit bigger, a chain wrapped round it; the left wears the hack deck)
  for (const [A, s] of [[R, 1], [Lf, -1]]) {
    const big = s > 0;
    put(A.sh, new THREE.SphereGeometry(0.18, 10, 7), 'black', 0, 0, 0);
    put(A.sh, cbox(0.26, 0.44, 0.27, 0.04), 'steel', 0, -0.24, 0);
    put(A.sh, cbox(0.28, 0.26, 0.22, 0.03), big ? 'rust' : 'teal', s * 0.02, -0.22, -0.07, { r: [0.1, 0, s * 0.05] });
    put(A.sh, new THREE.SphereGeometry(0.13, 8, 6), 'gun', 0, -0.5, 0);
    put(A.sh, cylX(0.075, 0.32), 'chrome', 0, -0.5, 0, { small: true });
    const pc = big ? ['ochre', 'gun', 'rust'] : ['accent', 'olive', 'steel'];
    for (let i = 0; i < 3; i++) put(A.pa, cbox(0.52 - i * 0.05, 0.13, 0.54 - i * 0.04, 0.04), pc[i], s * (0.04 + i * 0.08), 0.17 - i * 0.12, 0, { r: [0, 0, -s * (0.3 + i * 0.24)] });
    put(A.pa, cbox(0.06, 0.28, 0.4, 0.02), 'gun', -s * 0.14, 0.27, 0.02, { r: [0, 0, s * 0.22] }); // guard plate beside the helm
    put(A.pa, new THREE.BoxGeometry(0.028, 0.028, 0.5), big ? 'mag' : 'cyan', s * 0.03, 0.24, 0, { r: [0, 0, -s * 0.3] });
    if (big) put(A.pa, cbox(0.16, 0.09, 0.3, 0.02), 'accent', s * 0.13, 0.205, 0, { r: [0, 0, -s * 0.3] });
    bolts(A.pa, 'chrome', [[s * 0.17, 0.17, -0.22], [s * 0.17, 0.17, 0.22], [s * 0.27, 0.05, -0.2], [s * 0.27, 0.05, 0.2]], 0.02);
    put(A.fa, taper(cbox(0.3, 0.62, 0.34, 0.05), 1.3, 1.22, 'y'), 'gun', 0, -0.31, 0);
    put(A.fa, cbox(0.38, 0.36, 0.08, 0.03), big ? 'ochre' : 'rust', 0, -0.38, -0.2, { r: [-0.04, 0, 0] });
    put(A.fa, cbox(0.08, 0.42, 0.36, 0.02), big ? 'steel' : 'olive', s * 0.18, -0.36, 0, { r: [0, 0, s * 0.04] });
    put(A.fa, new THREE.BoxGeometry(0.024, 0.36, 0.02), 'mag', s * 0.195, -0.36, -0.13);
    put(A.fa, new THREE.BoxGeometry(0.024, 0.36, 0.02), 'cyan', -s * 0.15, -0.36, -0.16);
    for (let i = 0; i < 3; i++) put(A.fa, cbox(0.36 + i * 0.03, 0.035, 0.38 + i * 0.02, 0.01), 'black', 0, -0.12 - i * 0.16, 0, { small: true });
    put(A.fa, cyl(0.065, 0.09, 0.14, 8), 'gun', 0, -0.06, 0.15, { r: [0.5, 0, 0] }); // elbow thruster nozzle (points up + back)
    put(A.fa, cyl(0.05, 0.05, 0.02, 8), 'black', 0, 0, 0.18, { r: [0.5, 0, 0], small: true });
    if (!big) {
      put(A.fa, cbox(0.22, 0.2, 0.05, 0.015), 'black', 0, -0.44, -0.25, { r: [-0.04, 0, 0] });
      put(A.fa, new THREE.BoxGeometry(0.17, 0.15, 0.01), 'screen', 0, -0.44, -0.278, { r: [-0.04, 0, 0] });
    } else for (let i = 0; i < 6; i++) put(A.fa, new THREE.TorusGeometry(0.04, 0.012, 4, 8), 'steel', -0.13 + i * 0.05, -0.5, -0.23 + (i % 2) * 0.01, { r: [0, i % 2 ? Math.PI / 2 : 0, 0.3], small: true });
    const fs = big ? 1.18 : 1.08;
    put(A.fi, cbox(0.32 * fs, 0.24 * fs, 0.3 * fs, 0.04), 'steel', 0, -0.12, 0);
    for (let i = 0; i < 4; i++) {
      const x = (-0.11 + i * 0.075) * fs;
      put(A.fi, cbox(0.07 * fs, 0.1 * fs, 0.11 * fs, 0.02), 'gun', x, -0.25 * fs, -0.12 * fs, { r: [0.5, 0, 0] });
      put(A.fi, cbox(0.07 * fs, 0.09 * fs, 0.09 * fs, 0.02), 'gun', x, -0.31 * fs, -0.04 * fs, { r: [1.3, 0, 0] });
    }
    put(A.fi, cbox(0.08 * fs, 0.16 * fs, 0.1 * fs, 0.02), 'gun', -s * 0.17 * fs, -0.17 * fs, -0.08 * fs, { r: [0.4, 0, -s * 0.3] });
    put(A.fi, cbox(0.34 * fs, 0.07 * fs, 0.12 * fs, 0.02), big ? 'rust' : 'olive', 0, -0.2 * fs, -0.19 * fs, { r: [0.2, 0, 0] });
    put(A.fi, new THREE.BoxGeometry(0.3 * fs, 0.024, 0.024), big ? 'glowR' : 'glowL', 0, -0.2 * fs, -0.255 * fs, { r: [0.2, 0, 0] });
    for (let i = 0; i < 4; i++) put(A.fi, new THREE.ConeGeometry(0.022, 0.06, 4).rotateX(-Math.PI / 2 - 0.2), 'chrome', (-0.11 + i * 0.075) * fs, -0.17 * fs, -0.27 * fs, { small: true });
    glows.push({ j: A.fi.i, p: [0, -0.2 * fs, -0.3 * fs], c: NEON.mag, s: 0.42, k: big ? 'glowR' : 'glowL', w: 0 });
    piston(torso, [s * 0.44, 0.56, 0.12], A.sh, [s * 0.11, -0.32, 0.1], 0.04, 0.3); // shoulder ram
    piston(A.sh, [s * 0.13, -0.14, -0.1], A.fa, [s * 0.14, -0.24, -0.1], 0.042, 0.28); // elbow rams, both sides
    piston(A.sh, [-s * 0.11, -0.16, 0.08], A.fa, [-s * 0.12, -0.22, 0.12], 0.036, 0.26);
    hose(rack, [s * 0.12, 0.2, 0.06], A.fa, [s * 0.05, -0.08, 0.17], [s * 0.35, -0.05, 0.45], 0.034);
    hose(torso, [s * 0.2, 0.88, -0.24], head, [s * 0.16, 0.0, -0.05], [s * 0.12, 0.05, -0.12], 0.018, false);
    // legs: an armoured thigh, a big knee cap, a flared shin like a hydraulic ram, a stomper foot with a heel spur
    put(A.th, cbox(0.36, 0.46, 0.38, 0.05), big ? 'steel' : 'gun', 0, -0.22, 0);
    put(A.th, cbox(0.3, 0.3, 0.07, 0.03), big ? 'olive' : 'rust', 0, -0.2, -0.2, { r: [-0.05, 0, 0] });
    put(A.th, new THREE.BoxGeometry(0.024, 0.28, 0.02), big ? 'cyan' : 'mag', s * 0.18, -0.22, -0.13);
    put(A.th, cylX(0.12, 0.4), 'black', 0, -0.48, 0);
    put(A.sn, cbox(0.26, 0.22, 0.13, 0.04), big ? 'ochre' : 'cream', 0, -0.02, -0.16, { r: [0.25, 0, 0] });
    put(A.sn, taper(cbox(0.3, 0.52, 0.34, 0.05), 1.25, 1.12, 'y'), 'gun', 0, -0.27, 0.01);
    put(A.sn, cbox(0.28, 0.36, 0.06, 0.03), 'accent', 0, -0.3, -0.18);
    put(A.sn, new THREE.BoxGeometry(0.02, 0.3, 0.02), 'mag', -s * 0.15, -0.3, -0.2);
    for (let i = 0; i < 2; i++) put(A.sn, cbox(0.34, 0.03, 0.38, 0.01), 'black', 0, -0.12 - i * 0.24, 0, { small: true });
    put(A.ft, cbox(0.38, 0.17, 0.6, 0.04), 'gun', 0, -0.06, -0.08);
    put(A.ft, cbox(0.4, 0.06, 0.64, 0.02), 'black', 0, -0.12, -0.08);
    put(A.ft, cbox(0.34, 0.1, 0.16, 0.03), big ? 'rust' : 'ochre', 0, -0.03, -0.35, { r: [0.35, 0, 0] });
    put(A.ft, cbox(0.1, 0.12, 0.14, 0.02), 'steel', 0, -0.06, 0.22);
    put(A.ft, new THREE.BoxGeometry(0.3, 0.02, 0.02), 'cyan', 0, -0.09, -0.4, { small: true });
    piston(A.th, [s * 0.19, -0.08, -0.06], A.sn, [s * 0.18, -0.3, -0.04], 0.04, 0.32); // knee ram
    piston(A.sn, [0, -0.2, 0.18], A.ft, [0, -0.02, 0.2], 0.035, 0.2); // ankle ram
    piston(hips, [s * 0.18, -0.06, -0.21], A.th, [s * 0.05, -0.3, -0.18], 0.038, 0.24); // hip ram
    hose(hips, [s * 0.22, 0.02, 0.25], A.sn, [s * 0.13, -0.06, 0.17], [s * 0.15, -0.2, 0.32], 0.026);
  }

  // ---- bake: one merged mesh per material per joint, and a smooth hull per joint (outline, shield, afterimages)
  for (const j of joints) {
    j.geos = [];
    for (const [mk, list] of j.parts) {
      const flat = list.map((g) => { const n = g.index ? g.toNonIndexed() : g.clone(); n.deleteAttribute('uv'); n.deleteAttribute('normal'); return n; });
      const merged = mergeGeometries(flat, false);
      merged.computeVertexNormals();
      j.geos.push([mk, merged]);
    }
    if (j.out.length) {
      const hull = mergeVertices(mergeGeometries(j.out.map((g) => { const n = g.clone(); n.deleteAttribute('uv'); n.deleteAttribute('normal'); return n.index ? n : mergeVertices(n, 1e-4); }), false), 1e-3);
      hull.computeVertexNormals();
      j.hull = hull;
    }
  }
  // afterimage: every hull in one index buffer (each ghost bakes its own positions into a copy)
  let nv = 0;
  const idx = [];
  for (const j of joints) if (j.hull) { j.hv0 = nv; const ix = j.hull.index.array; for (let i = 0; i < ix.length; i++) idx.push(ix[i] + nv); nv += j.hull.attributes.position.count; }
  TPL = { joints, pistons, hoses, glows, ghostN: nv, ghostIndex: new THREE.BufferAttribute(new Uint32Array(idx), 1) };
  return TPL;
}

// ------------------------------------------------------------ shaders: outline, hex overshield, afterimages
const OUTLINE_VS = 'uniform float uThick; void main() { gl_Position = projectionMatrix * modelViewMatrix * vec4(position + normal * uThick, 1.0); }';
const OUTLINE_FS = 'uniform vec3 uColor; void main() { gl_FragColor = vec4(uColor, 1.0); }';
const HEX_VS = `uniform float uThick; varying vec3 vW; varying vec3 vN;
void main() { vec4 w = modelMatrix * vec4(position + normal * uThick, 1.0); vW = w.xyz; vN = normalize(mat3(modelMatrix) * normal); gl_Position = projectionMatrix * viewMatrix * w; }`;
const HEX_FS = `uniform vec3 uColor; uniform vec3 uHit; uniform float uAmt; uniform float uAge; varying vec3 vW; varying vec3 vN;
float hexd(vec2 p) { vec2 r = vec2(1.0, 1.7320508), h = r * 0.5; vec2 a = mod(p, r) - h, b = mod(p - h, r) - h; vec2 g = dot(a, a) < dot(b, b) ? a : b; vec2 q = abs(g); return 0.5 - max(q.x * 0.5 + q.y * 0.8660254, q.x); }
void main() {
  vec3 n = abs(vN); vec2 uv = n.y > max(n.x, n.z) ? vW.xz : (n.x > n.z ? vW.zy : vW.xy);
  float e = hexd(uv * 4.2), line = 1.0 - smoothstep(0.0, 0.07, e);
  float d = distance(vW, uHit), ring = exp(-pow((d - uAge * 7.0) * 3.0, 2.0)), near = exp(-d * 0.9);
  float a = uAmt * (line * (0.35 + 0.65 * near) + 0.08 + ring * 0.9);
  gl_FragColor = vec4(uColor * (1.0 + ring * 1.5), a);
}`;
const GHOST_VS = `uniform float uTime; uniform float uSeed; uniform float uGlitch; varying float vY;
void main() {
  vec3 p = position; float band = floor(p.y * 6.0 + uSeed * 7.0);
  float n = fract(sin(band * 91.7 + floor(uTime * 20.0) * 13.3 + uSeed * 31.0) * 43758.5);
  p.x += (n - 0.5) * uGlitch * step(0.62, n);
  vY = p.y; gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
}`;
const GHOST_FS = `uniform vec3 uColor; uniform float uOpacity; uniform float uTime; varying float vY;
void main() { float scan = 0.45 + 0.55 * step(0.5, fract(vY * 14.0 - uTime * 4.0)); gl_FragColor = vec4(uColor * scan, uOpacity * scan); }`;

// soft round glow (visor, core, charged fists)
let glowTex = null;
export function glowTexture() {
  if (glowTex) return glowTex;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(255,255,255,0.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  glowTex = new THREE.CanvasTexture(c);
  return glowTex;
}
// the wrist hack deck's screen: cyan glyphs (redrawn when it's in use)
export function screenTex() {
  const c = document.createElement('canvas'); c.width = 32; c.height = 32;
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter;
  t.userData = { c, x: c.getContext('2d') };
  drawScreen(t, 0);
  return t;
}
export function drawScreen(t, k) {
  const { c, x } = t.userData;
  x.fillStyle = '#021418'; x.fillRect(0, 0, c.width, c.height);
  x.fillStyle = k ? '#ff2bd6' : '#2ef2ff';
  for (let y = 2; y < 30; y += 4) { const w = 4 + ((Math.random() * 22) | 0); x.fillRect(2, y, w, 2); }
  if (k) { x.fillStyle = '#ffffff'; x.fillRect(0, (Math.random() * 30) | 0, 32, 1); }
  t.needsUpdate = true;
}

// ------------------------------------------------------------ an instance
// opts.outline: draw the coloured outline everyone else gets. returns { root, j: {name: Object3D}, ... }
export function buildRig(color, opts = {}) {
  const T = template();
  const col = new THREE.Color(color || '#ff4fd8');
  const own = {
    accent: new THREE.MeshLambertMaterial({ color: col, flatShading: true, fog: false, emissive: col.clone().multiplyScalar(0.3) }),
    visor: new THREE.MeshBasicMaterial({ color: NEON.visor, fog: false }),
    glowL: new THREE.MeshBasicMaterial({ color: 0x4a0f3e, fog: false }),
    glowR: new THREE.MeshBasicMaterial({ color: 0x4a0f3e, fog: false }),
    screen: new THREE.MeshBasicMaterial({ map: screenTex(), fog: false }),
    core: new THREE.MeshBasicMaterial({ color: NEON.cyan, fog: false }),
  };
  const outlineMat = opts.outline ? new THREE.ShaderMaterial({ uniforms: { uThick: { value: 0.013 }, uColor: { value: col.clone() } }, vertexShader: OUTLINE_VS, fragmentShader: OUTLINE_FS, side: THREE.BackSide }) : null;
  const shieldMat = new THREE.ShaderMaterial({
    uniforms: { uThick: { value: 0.07 }, uColor: { value: new THREE.Color(0x46e8ff) }, uHit: { value: new THREE.Vector3() }, uAmt: { value: 0 }, uAge: { value: 0 } },
    vertexShader: HEX_VS, fragmentShader: HEX_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  });
  const root = new THREE.Group();
  const nodes = [], j = {}, shield = [];
  for (const tj of T.joints) {
    const n = tj.i === 0 ? root : new THREE.Group();
    n.position.fromArray(tj.pos);
    n.userData.rest = tj.pos.slice();
    if (tj.parent >= 0) nodes[tj.parent].add(n);
    nodes.push(n); j[tj.name] = n;
    for (const [mk, geo] of tj.geos) {
      const m = new THREE.Mesh(geo, own[mk] || SHARED[mk]());
      n.add(m);
    }
    if (tj.hull) {
      if (outlineMat) n.add(new THREE.Mesh(tj.hull, outlineMat));
      const s = new THREE.Mesh(tj.hull, shieldMat); s.visible = false; s.renderOrder = 6; n.add(s); shield.push(s);
    }
  }
  // pistons: a cylinder on one joint aimed at the other, a chrome rod on the other aimed back (they slide in each other)
  const pist = T.pistons.map((pd) => {
    const body = new THREE.Mesh(cylGeo(pd.r, pd.len), shiny(0x7f8892));
    const rod = new THREE.Mesh(cylGeo(pd.r * 0.55, pd.len * 1.15), shiny(C.chrome));
    const a = new THREE.Object3D(), b = new THREE.Object3D();
    a.position.fromArray(pd.pa); b.position.fromArray(pd.pb);
    nodes[pd.a].add(a); nodes[pd.b].add(b);
    a.add(body); b.add(rod);
    return { a, b, body, rod };
  });
  // hoses: one dynamic ribbed tube mesh for all of them (rebuilt each frame from the joints)
  const hoseGeo = new THREE.BufferGeometry();
  const H_SEG = 14, H_RAD = 6, nvH = T.hoses.length * (H_SEG + 1) * H_RAD;
  hoseGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(nvH * 3), 3).setUsage(THREE.DynamicDrawUsage));
  hoseGeo.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(nvH * 3), 3).setUsage(THREE.DynamicDrawUsage));
  const hi = [];
  T.hoses.forEach((h, k) => {
    const base = k * (H_SEG + 1) * H_RAD;
    for (let s = 0; s < H_SEG; s++) for (let r = 0; r < H_RAD; r++) {
      const a = base + s * H_RAD + r, b = base + s * H_RAD + ((r + 1) % H_RAD), c = a + H_RAD, d = b + H_RAD;
      hi.push(a, c, b, b, c, d);
    }
  });
  hoseGeo.setIndex(hi);
  const hoses = new THREE.Mesh(hoseGeo, lam(0x22252a, 0.08));
  hoses.frustumCulled = false;
  root.add(hoses);
  const anchors = T.hoses.map((h) => {
    const a = new THREE.Object3D(), b = new THREE.Object3D();
    a.position.fromArray(h.pa); b.position.fromArray(h.pb);
    nodes[h.a].add(a); nodes[h.b].add(b);
    return { a, b, bend: new THREE.Vector3().fromArray(h.bend), r: h.r, rib: h.rib };
  });
  // glow sprites
  const glows = T.glows.map((gd) => {
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color: gd.c, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
    sp.position.fromArray(gd.p); sp.scale.setScalar(gd.s); sp.userData = { base: gd.s, k: gd.k, w: gd.w ?? 1 };
    sp.renderOrder = 7;
    nodes[gd.j].add(sp);
    return sp;
  });
  // elbow rocket flames (the punch dash) and the pods' launch flash
  const flames = ['foreR', 'foreL'].map((nm) => { // out of the elbow nozzle, up + back along the forearm
    const g = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.55, 8, 1, true).translate(0, 0.275, 0).rotateX(0.5),
      new THREE.MeshBasicMaterial({ color: 0xff3fc8, transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide }));
    g.position.set(0, -0.01, 0.19);
    g.scale.setScalar(0.001); g.visible = false; g.renderOrder = 7;
    j[nm].add(g);
    return g;
  });
  // thruster plumes (the grapple key in the rig): out of both boots and two nozzles low on the back, pointing down.
  // a hot inner core inside a magenta / orange outer flame
  const jetMat = [new THREE.MeshBasicMaterial({ color: 0xff5a2a, transparent: true, opacity: 0.75, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide }),
    new THREE.MeshBasicMaterial({ color: 0xfff0c0, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, fog: false })];
  // (flipped so the wide end sits at the nozzle and the tip points down)
  const jetGeo = [new THREE.ConeGeometry(0.16, 0.9, 8, 1, true).rotateX(Math.PI).translate(0, -0.45, 0), new THREE.ConeGeometry(0.07, 0.5, 6).rotateX(Math.PI).translate(0, -0.25, 0)];
  const jets = [['footL', [0, -0.15, 0.05]], ['footR', [0, -0.15, 0.05]], ['torso', [0.3, 0.3, 0.42]], ['torso', [-0.3, 0.3, 0.42]]].map(([nm, p]) => {
    const g = new THREE.Group(); g.position.fromArray(p);
    if (nm !== 'torso') g.scale.setScalar(1.45); // (boot jets: big enough to read from the front)
    for (let k = 0; k < 2; k++) { const m = new THREE.Mesh(jetGeo[k], jetMat[k]); m.renderOrder = 7; g.add(m); }
    if (nm === 'torso') { const n = new THREE.Mesh(cyl(0.07, 0.09, 0.12, 8), lam(C.gun)); n.position.y = 0.04; g.add(n); } // the back nozzles are always there
    g.userData.flame = g.children.slice(0, 2);
    for (const f of g.userData.flame) f.visible = false;
    j[nm].add(g);
    return g;
  });
  // torso: lean, then twist round the hips. shoulders: twist along the arm, then out to the side, then swing (so a
  // raised arm can still turn its forearm inward: the block crosses them in front of the helm)
  j.torso.rotation.order = 'YXZ';
  j.shoulderL.rotation.order = j.shoulderR.rotation.order = 'XZY';
  const inst = {
    root, j, nodes, own, outlineMat, shieldMat, shield, pist, hoses, anchors, glows, flames, jets, jetGeo, jetMat, H_SEG, H_RAD,
    // pose state: gait phase, springs, timers
    phase: 0, plant: [0, 0], bob: 0, bobV: 0, sp: {}, look: 0, lookT: 0, lookNext: 1, t: 0, hexT: 9, hexK: 0, pods: 0,
  };
  root.userData.rig = inst;
  return inst;
}
const cylGeos = new Map();
function cylGeo(r, len) { // pointing +y from its origin
  const k = r + ',' + len;
  if (!cylGeos.has(k)) cylGeos.set(k, new THREE.CylinderGeometry(r, r, len, 8).translate(0, len / 2, 0));
  return cylGeos.get(k);
}
export function freeRig(inst) {
  inst.root.removeFromParent();
  inst.hoses.geometry.dispose();
  for (const m of Object.values(inst.own)) { if (m.map) m.map.dispose(); m.dispose(); }
  if (inst.outlineMat) inst.outlineMat.dispose();
  inst.shieldMat.dispose();
  for (const g of inst.glows) g.material.dispose();
  for (const f of inst.flames) { f.geometry.dispose(); f.material.dispose(); }
  for (const g of inst.jetGeo) g.dispose();
  for (const m of inst.jetMat) m.dispose();
  if (inst.ghosts) for (const g of inst.ghosts) { g.mesh.removeFromParent(); g.mesh.geometry.dispose(); g.mesh.material.dispose(); }
  inst.ghosts = null;
}
export function setRigColor(inst, color) {
  const c = new THREE.Color(color);
  inst.own.accent.color.copy(c); inst.own.accent.emissive.copy(c).multiplyScalar(0.3);
  if (inst.outlineMat) inst.outlineMat.uniforms.uColor.value.copy(c);
}

// ------------------------------------------------------------ pose
// s: { spd, fwd, side (local m/s), air, vy, block, charge, leap, punchT, punchC, missT, hackT, hitT, landT, landK,
//      pitch, dash, on (0..1 assembly), dt }. one call per frame
const LEG = { thigh: 0.48, shin: 0.52, ankle: 0.14 };
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const smooth = (u) => u * u * (3 - 2 * u);
const hump = (t, a, b) => (t < a ? t / a : t < b ? 1 : Math.max(0, 1 - (t - b) / 0.3)); // up, hold, down (0..1)
// a damped spring per joint channel: heavy servos that overshoot a hair
function spr(inst, key, target, k, dt, d = 2 * Math.sqrt(k) * 0.82) {
  let st = inst.sp[key];
  if (!st) st = inst.sp[key] = { x: target, v: 0 };
  const n = Math.max(1, Math.ceil(dt * 240)), h = dt / n;
  for (let i = 0; i < n; i++) { st.v += (k * (target - st.x) - d * st.v) * h; st.x += st.v * h; }
  return st.x;
}
// two-bone leg IK in the hips' frame: aim the thigh, bend the knee forward, keep the sole flat
function legIK(inst, th, sn, ft, target, toe) {
  const hp = th.position, dx = target[0] - hp.x, dy = target[1] - hp.y, dz = target[2] - hp.z;
  const L1 = LEG.thigh, L2 = LEG.shin, D = clamp(Math.hypot(dx, dy, dz), 0.25, L1 + L2 - 0.002);
  const cosK = clamp((L1 * L1 + L2 * L2 - D * D) / (2 * L1 * L2), -1, 1), bend = Math.PI - Math.acos(cosK);
  const alpha = Math.acos(clamp((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1));
  const phi = Math.atan2(-dz, Math.hypot(dx, dy)); // forward of straight down
  th.rotation.set(phi + alpha, 0, Math.atan2(dx, -dy));
  sn.rotation.set(-bend, 0, 0);
  ft.rotation.set(-(phi + alpha - bend) + toe, 0, -th.rotation.z);
}
export function poseRig(inst, s, dt) {
  const J = inst.j;
  inst.t += dt;
  const t = inst.t, spd = s.spd || 0, run = clamp(spd / 16, 0, 1.4);
  // ---- gait: the phase runs with speed, a stance foot stays planted while the body passes over it
  const cyc = clamp(0.8 + spd * 0.09, 0.8, 2.1);
  const moving = spd > 0.6 && !s.air;
  if (moving) inst.phase = (inst.phase + dt * cyc) % 1;
  const stride = clamp(spd / cyc, 0, 1.55) * (s.block ? 0.6 : 1);
  const dirx = spd > 0.1 ? (s.side || 0) / spd : 0, dirz = spd > 0.1 ? (s.fwd || 0) / spd : 1;
  const duty = 0.58, lift = 0.16 + 0.14 * clamp(run, 0, 1);
  const stomp = (k) => { inst.bobV -= (0.55 + run * 0.6) * k; if (inst.onStep) inst.onStep(k); };
  const crouch = Math.max(s.leap ? 0.3 * s.leap + 0.08 : 0, s.block ? 0.1 : 0, s.landT < 0.45 ? (s.landK || 0.5) * 0.32 * Math.sin(Math.min(1, s.landT / 0.45) * Math.PI) : 0);
  // hips bounce on each foot plant (a spring), sink for a crouch
  for (let n = Math.min(40, Math.max(1, Math.ceil(dt * 240))), h = dt / n, i = 0; i < n; i++) { inst.bobV += (-200 * inst.bob - 16 * inst.bobV) * h; inst.bob += inst.bobV * h; } // (substepped: slow frames)
  const hipsY = 1.1 - crouch + clamp(inst.bob, -0.12, 0.08) - (moving ? 0.03 * run : 0);
  J.hips.position.y = hipsY;
  const legs = [[J.thighL, J.shinL, J.footL, 0], [J.thighR, J.shinR, J.footR, 0.5]];
  for (let i = 0; i < 2; i++) {
    const [th, sn, ft, off] = legs[i];
    const ph = (inst.phase + off) % 1;
    const baseX = th.position.x * 1.08, baseZ = 0.03;
    let u = 0, y = 0, toe = 0;
    if (s.air) { // tucked
      const k = clamp((s.vy || 0) / 8, -1, 1);
      th.userData.air = true;
      legIK(inst, th, sn, ft, [baseX, -0.78 + k * 0.08 - i * 0.06, -0.12 - i * 0.12], 0.25);
      continue;
    }
    if (moving) {
      if (ph < duty) u = stride * (0.5 - ph / duty);
      else { const w = (ph - duty) / (1 - duty); u = stride * (smooth(w) - 0.5); y = lift * Math.sin(w * Math.PI); toe = Math.sin(w * Math.PI) * 0.35; }
      // foot plant: it just touched down
      const was = inst.plant[i];
      inst.plant[i] = ph < duty ? 1 : 0;
      if (!was && inst.plant[i]) stomp(0.6 + 0.5 * clamp(run, 0, 1));
    } else if (inst.plant[i] === 0 || th.userData.air) { inst.plant[i] = 1; if (th.userData.air) stomp(0.5); }
    th.userData.air = false;
    const fx = baseX + dirx * u, fz = baseZ - dirz * u;
    // where the sole is relative to the hips joint (the root is at the ground)
    legIK(inst, th, sn, ft, [fx, -hipsY + LEG.ankle + y, fz - J.hips.position.z], toe);
  }
  // ---- torso: leans into speed, rolls over the stance leg, breathes, twists with the punch
  const roll = moving ? Math.sin(inst.phase * Math.PI * 2) * 0.05 * (0.5 + run * 0.5) : 0;
  const lean = -0.14 - run * 0.2 * (moving ? 1 : 0) - (s.leap ? 0.22 * s.leap : 0) + (s.block ? 0.12 : 0); // always hunched (braced upright to block)
  const breathe = Math.sin(t * 1.6) * 0.018;
  const P = clamp(s.punchT ?? 9, 0, 9), pk = P < 0.5 ? (P < 0.06 ? P / 0.06 : 1 - smooth(clamp((P - 0.22) / 0.28, 0, 1))) : 0; // punch extension 0..1
  const ck = clamp(s.charge || 0, 0, 1), cw = spr(inst, 'cw', s.charge > 0 ? 1 : 0, 120, dt);
  const bw = spr(inst, 'bw', s.block ? 1 : 0, 160, dt);
  const hk = (s.hackT ?? 9) < 0.8 ? hump(s.hackT, 0.15, 0.55) : 0;
  const shake = (cw * ck * ck * 0.06 + (s.hitT < 0.15 ? 0.05 : 0)) * (Math.random() - 0.5);
  const twist = -0.75 * cw * (1 - pk) + 0.55 * pk;
  J.torso.rotation.set(
    spr(inst, 'tx', lean + breathe, 90, dt) + (s.hitT < 0.25 ? 0.1 * (1 - s.hitT / 0.25) : 0),
    spr(inst, 'ty', twist + (moving ? -roll * 1.4 : 0), pk > 0 ? 700 : 110, dt) + shake,
    spr(inst, 'tz', roll, 80, dt));
  // ---- head: scans the room in little servo snaps, looks where they aim, ducks behind the block
  if (t > inst.lookNext) { inst.lookT = (Math.random() - 0.5) * 0.9; inst.lookNext = t + 0.8 + Math.random() * 2.2; }
  const aimY = s.charge > 0 || pk > 0 || bw > 0.5 || hk > 0 ? 0 : inst.lookT;
  J.head.position.set(0, 0.8 - bw * 0.1, -0.25 + bw * 0.2); // ducks back behind the forearms
  J.head.rotation.set(spr(inst, 'hx', clamp((s.pitch || 0) * 0.6, -0.5, 0.5) - J.torso.rotation.x * 0.7 - hk * 0.45 - bw * 0.3, 260, dt),
    spr(inst, 'hy', aimY - J.torso.rotation.y * 0.6 + hk * 0.45, 420, dt), 0);
  // ---- arms. a walk swing (fists pumping), then the combat poses blend over it
  const sw = moving ? Math.cos(inst.phase * Math.PI * 2) : 0, amp = (0.18 + 0.42 * clamp(run, 0, 1)) * (moving ? 1 : 0);
  const idle = Math.sin(t * 1.3) * 0.03;
  // [shoulder swing (+ forward), twist (+ turns the forearm inward on the right), out (+ right), elbow, fist] per side
  const R = [sw * amp + 0.12 + idle, 0, 0.16, 0.42 + run * 0.55 + Math.max(0, sw) * run * 0.5, 0.1];
  const L = [-sw * amp + 0.12 - idle, 0, -0.16, 0.42 + run * 0.55 + Math.max(0, -sw) * run * 0.5, 0.1];
  const mix = (a, b, k) => { for (let i = 0; i < a.length; i++) a[i] += (b[i] - a[i]) * k; };
  if (s.air) { mix(R, [0.5, 0, 0.5, 0.9, 0.2], 0.7); mix(L, [0.5, 0, -0.5, 0.9, 0.2], 0.7); }
  if (s.leap) { mix(R, [-0.7, 0, 0.35, 0.6, 0.3], s.leap); mix(L, [-0.7, 0, -0.35, 0.6, 0.3], s.leap); }
  if (hk > 0) mix(L, [1.0, -0.6, -0.1, 1.9, -0.3], hk); // the wrist deck up in front of the visor
  if (cw > 0) { // wind-up: right fist cocked back by the shoulder, left forward on guard, shaking harder as it charges
    const j2 = ck * ck * 0.12;
    mix(R, [-1.05 + (Math.random() - 0.5) * j2, 0.35, 0.55, 2.15 + (Math.random() - 0.5) * j2, 0.45], cw);
    mix(L, [0.8, -0.35, -0.1, 1.6, 0.1], cw * 0.85);
  }
  if (pk > 0) { mix(R, [1.55, 0, 0.05, 0.05, 0], pk); mix(L, [-0.35, 0, -0.3, 1.2, 0.2], pk * 0.8); }
  if (bw > 0) { mix(R, [1.35, 1.0, -0.35, 1.25, 0.3], bw); mix(L, [1.27, -1.0, 0.35, 1.2, 0.3], bw); } // forearms crossed in front of the helm
  const k = pk > 0 ? 900 : 170;
  J.shoulderR.rotation.set(spr(inst, 'rsx', R[0], k, dt), spr(inst, 'rsy', R[1], k, dt), spr(inst, 'rsz', R[2], k, dt));
  J.foreR.rotation.set(spr(inst, 'rex', R[3], k, dt), 0, 0);
  J.fistR.rotation.set(spr(inst, 'rfx', R[4], 200, dt), 0, 0);
  J.shoulderL.rotation.set(spr(inst, 'lsx', L[0], 170, dt), spr(inst, 'lsy', L[1], 170, dt), spr(inst, 'lsz', L[2], 170, dt));
  J.foreL.rotation.set(spr(inst, 'lex', L[3], 170, dt), 0, 0);
  J.fistL.rotation.set(spr(inst, 'lfx', L[4], 200, dt), 0, 0);
  // pauldrons ride along with the arms (a bit), the pods tip forward and the lids flip open to fire
  J.pauldR.rotation.set(J.shoulderR.rotation.x * 0.35, 0, Math.max(0, J.shoulderR.rotation.z) * 0.5);
  J.pauldL.rotation.set(J.shoulderL.rotation.x * 0.35, 0, Math.min(0, J.shoulderL.rotation.z) * 0.5);
  const M = s.missT ?? 9, open = M < 1.6 ? hump(M, 0.18, 1.1) : 0;
  inst.pods = spr(inst, 'pod', open, 140, dt);
  J.podL.rotation.set(-0.75 * inst.pods, 0, -0.3 * inst.pods);
  J.podR.rotation.set(-0.75 * inst.pods, 0, 0.3 * inst.pods);
  J.lidL.rotation.x = J.lidR.rotation.x = 1.9 * clamp(inst.pods * 1.4 - 0.2, 0, 1);
  // ---- glows: the charged fist goes from dull to white-hot, the visor flares on a punch, the core pulses
  const gR = Math.max(ck * cw, pk * 0.8, (s.punchT ?? 9) < 0.7 ? 0.5 : 0);
  glowColor(inst.own.glowR, gR, ck >= 1 && cw > 0.5);
  glowColor(inst.own.glowL, hk * 0.4, false);
  const vis = 0.75 + Math.sin(t * 9) * 0.08 + pk * 0.6 + gR * 0.3;
  inst.own.visor.color.setRGB(Math.min(1, vis), 0.08 * vis, 0.06 * vis);
  inst.own.core.color.setRGB(0.15, 0.75 + Math.sin(t * 4) * 0.2, 1);
  for (const g of inst.glows) {
    const w = g.userData.k === 'glowR' ? gR * 1.5 : g.userData.k === 'glowL' ? hk : g.userData.k === 'visor' ? vis * 0.9 : 0.8 + Math.sin(t * 4) * 0.2;
    g.scale.setScalar(g.userData.base * (0.4 + w * g.userData.w * (g.userData.k === 'glowR' ? 1 + Math.random() * 0.25 * ck : 1)));
    g.material.opacity = clamp(w, 0, 1);
    g.visible = w > 0.03;
  }
  if (hk > 0 && Math.random() < dt * 20) drawScreen(inst.own.screen.map, 1); else if (Math.random() < dt * 2) drawScreen(inst.own.screen.map, 0);
  // elbow rockets fire during the punch dash
  const fl = s.dash ? 1 : pk > 0 && P < 0.3 ? 0.6 : 0;
  inst.flames[0].visible = fl > 0;
  if (fl > 0) inst.flames[0].scale.set(1 + Math.random() * 0.3, fl * (0.8 + Math.random() * 0.6), 1 + Math.random() * 0.3);
  inst.flames[1].visible = false;
  // thrusters: a big flicker for the burst, tapering over 0.45 s
  const th = (s.thrustT ?? 9) < 0.45 ? 1 - (s.thrustT ?? 9) / 0.45 : 0;
  for (const g of inst.jets) for (const f of g.userData.flame) {
    f.visible = th > 0;
    if (th > 0) f.scale.set(0.8 + th * 0.4 + Math.random() * 0.2, th * (0.7 + Math.random() * 0.6), 0.8 + th * 0.4 + Math.random() * 0.2);
  }
  // ---- assembly (when it comes on): the plates fly in and snap shut, joint by joint
  const on = s.on ?? 1;
  // each part flies in from outside along its own direction (up and out), grows and snaps shut, feet first, pods last
  if (on < 1) inst.nodes.forEach((n, i) => {
    if (i === 0) return;
    const r = n.userData.rest, o = n.userData.off || (n.userData.off = new THREE.Vector3());
    const order = clamp(1 - (r[1] + 0.3) / 1.6, 0, 1) * 0.35 + (i % 5) * 0.03; // lower joints first
    const k2 = clamp(on * 1.7 - order, 0, 1);
    n.scale.setScalar(Math.max(0.001, k2 < 1 ? 0.2 + 0.8 * backOut(k2) : 1));
    n.position.sub(o);
    const l = Math.hypot(r[0], r[2]) || 1, f = (1 - smooth(k2)) * 0.42; // (offsets add up down the chain: keep each small)
    o.set((r[0] / l) * f * (Math.abs(r[0]) > 0.05 ? 1 : 0.3), f * 0.8, (r[2] / l) * f * 0.5);
    n.position.add(o);
  });
  else if (inst.assembling) { inst.assembling = false; for (const n of inst.nodes) { n.scale.setScalar(1); if (n.userData.off) { n.position.sub(n.userData.off); n.userData.off.set(0, 0, 0); } } }
  if (on < 1) inst.assembling = true;
  updatePistons(inst);
  updateHoses(inst);
  // hex overshield flicker after a hit
  inst.hexT += dt;
  const hx = inst.hexT < 0.45 ? (1 - inst.hexT / 0.45) * inst.hexK : 0;
  for (const m of inst.shield) m.visible = hx > 0.01;
  inst.shieldMat.uniforms.uAmt.value = hx;
  inst.shieldMat.uniforms.uAge.value = inst.hexT;
}
const backOut = (u) => { const c = 1.7; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };
function glowColor(mat, k, hot) {
  if (hot) mat.color.setRGB(1, 0.75 + Math.random() * 0.25, 1);
  else mat.color.setRGB(0.29 + 0.71 * k, 0.06 + 0.2 * k * k, 0.24 + 0.6 * k);
}
// someone shot the shield: flash the hex skin, rippling out from where it hit (world point)
export function rigHex(inst, at, k = 1) {
  inst.hexT = 0; inst.hexK = Math.min(1.4, 0.55 + k);
  inst.shieldMat.uniforms.uHit.value.set(at[0], at[1], at[2]);
}

const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _d = new THREE.Vector3(), _up = new THREE.Vector3(0, 1, 0), _iq = new THREE.Quaternion(), _wq = new THREE.Quaternion();
// aim a +y part sitting on `from` at the world point `at`
function aimAt(obj, from, at) {
  from.getWorldPosition(_a);
  _d.subVectors(at, _a);
  if (_d.lengthSq() < 1e-8) return;
  _d.normalize();
  _wq.setFromUnitVectors(_up, _d);
  from.getWorldQuaternion(_iq).invert();
  obj.quaternion.multiplyQuaternions(_iq, _wq);
}
function updatePistons(inst) {
  inst.root.updateMatrixWorld(true);
  for (const p of inst.pist) {
    p.b.getWorldPosition(_b); aimAt(p.body, p.a, _b);
    p.a.getWorldPosition(_a); aimAt(p.rod, p.b, _a.clone());
  }
}
const _inv = new THREE.Matrix4(), _c0 = new THREE.Vector3(), _c1 = new THREE.Vector3(), _c2 = new THREE.Vector3(), _t = new THREE.Vector3(), _n1 = new THREE.Vector3(), _n2 = new THREE.Vector3(), _pt = new THREE.Vector3(), _ref = new THREE.Vector3();
function updateHoses(inst) {
  const pos = inst.hoses.geometry.attributes.position.array, nor = inst.hoses.geometry.attributes.normal.array;
  _inv.copy(inst.root.matrixWorld).invert();
  const S = inst.H_SEG, RD = inst.H_RAD;
  inst.anchors.forEach((h, k) => {
    h.a.getWorldPosition(_c0).applyMatrix4(_inv);
    h.b.getWorldPosition(_c2).applyMatrix4(_inv);
    _c1.addVectors(_c0, _c2).multiplyScalar(0.5).add(h.bend); // a quadratic curve bowing out
    let o = k * (S + 1) * RD * 3;
    for (let i = 0; i <= S; i++) {
      const u = i / S, iu = 1 - u;
      _pt.set(iu * iu * _c0.x + 2 * iu * u * _c1.x + u * u * _c2.x, iu * iu * _c0.y + 2 * iu * u * _c1.y + u * u * _c2.y, iu * iu * _c0.z + 2 * iu * u * _c1.z + u * u * _c2.z);
      _t.set(2 * iu * (_c1.x - _c0.x) + 2 * u * (_c2.x - _c1.x), 2 * iu * (_c1.y - _c0.y) + 2 * u * (_c2.y - _c1.y), 2 * iu * (_c1.z - _c0.z) + 2 * u * (_c2.z - _c1.z)).normalize();
      _ref.set(Math.abs(_t.y) < 0.9 ? 0 : 1, Math.abs(_t.y) < 0.9 ? 1 : 0, 0);
      _n1.crossVectors(_t, _ref).normalize(); _n2.crossVectors(_t, _n1);
      const r = h.r * (h.rib && i % 2 ? 1.22 : 1) * (i === 0 || i === S ? 1.3 : 1);
      for (let j2 = 0; j2 < RD; j2++) {
        const a = (j2 / RD) * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
        const nx = _n1.x * ca + _n2.x * sa, ny = _n1.y * ca + _n2.y * sa, nz = _n1.z * ca + _n2.z * sa;
        pos[o] = _pt.x + nx * r; pos[o + 1] = _pt.y + ny * r; pos[o + 2] = _pt.z + nz * r;
        nor[o] = nx; nor[o + 1] = ny; nor[o + 2] = nz;
        o += 3;
      }
    }
  });
  inst.hoses.geometry.attributes.position.needsUpdate = true;
  inst.hoses.geometry.attributes.normal.needsUpdate = true;
}

// ------------------------------------------------------------ the overdrive trail: afterimages
// a glitchy translucent copy of the rig's current pose, cyan and magenta in turn, fading over 0.4 s. each rig has a
// little pool; a ghost bakes every joint's hull into its own position buffer (one draw call per ghost)
const GHOST_LIFE = 0.4, GHOSTS = 9;
const live = new Set();
// local: your own (they fade in as they fall behind your camera, so you never stand inside one)
export function rigGhost(inst, color, local = false) {
  const T = template();
  if (!inst.ghosts) {
    inst.ghosts = [];
    for (let i = 0; i < GHOSTS; i++) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(T.ghostN * 3), 3).setUsage(THREE.DynamicDrawUsage));
      geo.setIndex(T.ghostIndex);
      const mat = new THREE.ShaderMaterial({
        uniforms: { uColor: { value: new THREE.Color() }, uOpacity: { value: 0 }, uTime: { value: 0 }, uSeed: { value: Math.random() }, uGlitch: { value: 0.2 } },
        vertexShader: GHOST_VS, fragmentShader: GHOST_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.matrixAutoUpdate = false; mesh.frustumCulled = false; mesh.visible = false; mesh.renderOrder = 4;
      inst.ghosts.push({ mesh, age: 9, inst });
    }
    inst.gi = 0;
  }
  const gh = inst.ghosts[inst.gi = (inst.gi + 1) % GHOSTS];
  inst.root.updateMatrixWorld(true);
  _inv.copy(inst.root.matrixWorld).invert();
  const dst = gh.mesh.geometry.attributes.position.array, rel = new THREE.Matrix4();
  T.joints.forEach((tj, i) => {
    if (!tj.hull) return;
    rel.multiplyMatrices(_inv, inst.nodes[i].matrixWorld);
    const e = rel.elements, src = tj.hull.attributes.position.array;
    for (let v = 0, o = tj.hv0 * 3; v < src.length; v += 3, o += 3) {
      const x = src[v], y = src[v + 1], z = src[v + 2];
      dst[o] = e[0] * x + e[4] * y + e[8] * z + e[12];
      dst[o + 1] = e[1] * x + e[5] * y + e[9] * z + e[13];
      dst[o + 2] = e[2] * x + e[6] * y + e[10] * z + e[14];
    }
  });
  gh.mesh.geometry.attributes.position.needsUpdate = true;
  gh.mesh.matrix.copy(inst.root.matrixWorld);
  gh.mesh.matrixWorld.copy(inst.root.matrixWorld);
  gh.mesh.material.uniforms.uColor.value.setHex(color);
  gh.mesh.material.uniforms.uSeed.value = Math.random();
  gh.age = 0; gh.local = local;
  if (!gh.mesh.parent) G.scene.add(gh.mesh);
  gh.mesh.visible = true;
  live.add(gh);
}
const _gp = new THREE.Vector3(), _cam = new THREE.Vector3();
export function updateGhosts(dt, cam) {
  if (cam) cam.getWorldPosition(_cam);
  for (const gh of live) {
    gh.age += dt;
    const k = 1 - gh.age / GHOST_LIFE;
    if (k <= 0) { gh.mesh.visible = false; live.delete(gh); continue; }
    const u = gh.mesh.material.uniforms;
    let near = 1;
    if (gh.local && cam) { _gp.setFromMatrixPosition(gh.mesh.matrixWorld); _gp.y += 1.6; near = Math.max(0, Math.min(1, (_gp.distanceTo(_cam) - 1.4) / 2.2)); }
    u.uOpacity.value = 0.5 * k * k * near;
    u.uTime.value += dt;
    u.uGlitch.value = 0.12 + (1 - k) * 0.5;
  }
}
export function hideGhosts(inst) { if (inst.ghosts) for (const g of inst.ghosts) { g.mesh.visible = false; live.delete(g); } }

// ------------------------------------------------------------ particles: sparks (additive), smoke, debris
let sparks = null, smoke = null, debris = null;
function psys() {
  if (sparks || !G.scene) return !!sparks;
  sparks = new PSys(1500, THREE.AdditiveBlending, { scale: scaleU });
  smoke = new PSys(900, THREE.NormalBlending, { scale: scaleU });
  debris = new PSys(700, THREE.NormalBlending, { scale: scaleU });
  G.scene.add(smoke.points, debris.points, sparks.points);
  return true;
}
const Rn = (s = 1) => (Math.random() * 2 - 1) * s;
export const rfx = {
  update(dt) { if (sparks) { sparks.update(dt); smoke.update(dt); debris.update(dt); } },
  sparks(p, n, speed = 8, cols = [0xfff2b0, 0xff8a3a, 0xff2bd6], life = 0.5, size = 0.12, dir = null) {
    if (!psys()) return;
    for (let i = 0; i < n; i++) {
      let v = [Rn(), Rn() + 0.4, Rn()];
      if (dir) v = [dir[0] + Rn(0.6), dir[1] + Rn(0.6) + 0.2, dir[2] + Rn(0.6)];
      const l = Math.hypot(...v) || 1, s2 = speed * (0.35 + Math.random() * 0.65);
      sparks.spawn(p[0], p[1], p[2], v[0] / l * s2, v[1] / l * s2, v[2] / l * s2, life * (0.5 + Math.random() * 0.7), size, size * 0.2, cols[(Math.random() * cols.length) | 0], 0x401020, 1, 14, 1.5);
    }
  },
  smoke(p, n, col = 0x6a6e74, size = 0.6, rise = 1, life = 1.2, spread = 0.3) {
    if (!psys()) return;
    for (let i = 0; i < n; i++) smoke.spawn(p[0] + Rn(spread), p[1] + Rn(spread), p[2] + Rn(spread), Rn(0.6), rise * (0.4 + Math.random()), Rn(0.6), life * (0.6 + Math.random() * 0.6), size * 0.4, size * 1.6, col, 0x2a2c30, 0.55, -0.2, 1.2);
  },
  dust(p, n, radius = 1, speed = 4) { // a ring of dust rolling out along the floor
    if (!psys()) return;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 + Rn(0.2), s2 = speed * (0.6 + Math.random() * 0.6);
      smoke.spawn(p[0] + Math.cos(a) * radius * 0.3, p[1] + 0.1 + Math.random() * 0.2, p[2] + Math.sin(a) * radius * 0.3, Math.cos(a) * s2, 0.4 + Math.random() * 1.2, Math.sin(a) * s2,
        0.6 + Math.random() * 0.7, 0.5, 1.6 + radius * 0.25, 0xcab896, 0x8a7a5e, 0.6, 0, 2.4);
    }
  },
  debris(p, n, speed = 7, cols = [0x7a6e5e, 0x4e4842, 0x9a8c74]) {
    if (!psys()) return;
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2, s2 = speed * (0.4 + Math.random() * 0.8);
      debris.spawn(p[0] + Rn(0.4), p[1] + 0.2, p[2] + Rn(0.4), Math.cos(a) * s2, 4 + Math.random() * speed, Math.sin(a) * s2, 0.9 + Math.random() * 0.8, 0.12 + Math.random() * 0.14, 0.1, cols[(Math.random() * cols.length) | 0], 0x2a2622, 1, 24, 0.3);
    }
  },
  glitch(p, n, r = 0.8) { // hacked: little cyan / magenta / black squares jittering round them
    if (!psys()) return;
    for (let i = 0; i < n; i++) debris.spawn(p[0] + Rn(r), p[1] + Rn(r * 1.4), p[2] + Rn(r), Rn(1.5), Rn(1.5), Rn(1.5), 0.15 + Math.random() * 0.25, 0.08 + Math.random() * 0.12, 0.05, [0x2ef2ff, 0xff2bd6, 0x000000][(Math.random() * 3) | 0], 0x000000, 1, 0, 3);
  },
};

// ------------------------------------------------------------ rings, flashes, decals, beams (short-lived meshes)
const timed = [];
const RING = new THREE.RingGeometry(0.82, 1, 48).rotateX(-Math.PI / 2);
const RINGV = new THREE.RingGeometry(0.7, 1, 32); // faces +z: turned to face the punch
const BALL = new THREE.IcosahedronGeometry(1, 1);
function addTimed(mesh, life, kind, r, extra = {}) { G.scene.add(mesh); timed.push({ mesh, life, ml: life, kind, r, ...extra }); return mesh; }
export const rmesh = {
  // shockwave racing out along the floor
  ring(p, r, color = 0xffffff, life = 0.5, y = 0.12) {
    const m = new THREE.Mesh(RING, new THREE.MeshBasicMaterial({ color, transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, fog: false }));
    m.position.set(p[0], p[1] + y, p[2]);
    return addTimed(m, life, 'ring', r);
  },
  // an upright ring facing dir (the punch shockwave)
  vring(p, dir, r, color = 0xff2bd6, life = 0.3) {
    const m = new THREE.Mesh(RINGV, new THREE.MeshBasicMaterial({ color, transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, fog: false }));
    m.position.set(p[0], p[1], p[2]);
    m.lookAt(p[0] + dir[0], p[1] + (dir[1] || 0), p[2] + dir[2]);
    return addTimed(m, life, 'ring', r);
  },
  flash(p, r, color = 0xffffff, life = 0.18) {
    const m = new THREE.Mesh(BALL, new THREE.MeshBasicMaterial({ color, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
    m.position.set(p[0], p[1], p[2]);
    return addTimed(m, life, 'flash', r);
  },
  // a cracked crater on the floor (or a dent in a wall), fades after a while
  crater(p, r, normal = [0, 1, 0], life = 7) {
    const m = new THREE.Mesh(craterGeo(), new THREE.MeshBasicMaterial({ map: craterTex(), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, fog: false }));
    m.position.set(p[0] + normal[0] * 0.03, p[1] + normal[1] * 0.03, p[2] + normal[2] * 0.03);
    m.lookAt(p[0] + normal[0], p[1] + normal[1], p[2] + normal[2]);
    m.rotateZ(Math.random() * 6.28);
    m.scale.setScalar(r);
    return addTimed(m, life, 'decal', r);
  },
  // the quickhack's data beam: a jagged cyan / magenta bolt from the rig's head to the target
  beam(a, b, life = 0.35) {
    const n = 12, pts = [];
    for (let i = 0; i <= n; i++) {
      const u = i / n, j2 = i === 0 || i === n ? 0 : 0.35;
      pts.push(new THREE.Vector3(a[0] + (b[0] - a[0]) * u + Rn(j2), a[1] + (b[1] - a[1]) * u + Rn(j2), a[2] + (b[2] - a[2]) * u + Rn(j2)));
    }
    const g = new THREE.BufferGeometry().setFromPoints(pts);
    const grp = new THREE.Group();
    for (const [c, o] of [[0x2ef2ff, 0], [0xff2bd6, 0.06]]) {
      const l = new THREE.Line(g, new THREE.LineBasicMaterial({ color: c, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
      l.position.y = o;
      grp.add(l);
    }
    G.scene.add(grp);
    timed.push({ mesh: grp, life, ml: life, kind: 'beam' });
  },
  update(dt) {
    for (let i = timed.length - 1; i >= 0; i--) {
      const t = timed[i];
      t.life -= dt;
      const k = Math.max(0, t.life / t.ml);
      if (t.kind === 'ring') { t.mesh.scale.setScalar(0.3 + (1 - k) * t.r); t.mesh.material.opacity = k * k; }
      else if (t.kind === 'flash') { t.mesh.scale.setScalar(0.4 + (1 - k) * t.r); t.mesh.material.opacity = k; }
      else if (t.kind === 'decal') t.mesh.material.opacity = Math.min(1, t.life / 1.5) * 0.85;
      else if (t.kind === 'beam') for (const l of t.mesh.children) l.material.opacity = k;
      if (t.life <= 0) {
        G.scene.remove(t.mesh);
        if (t.kind === 'beam') { t.mesh.children[0].geometry.dispose(); for (const l of t.mesh.children) l.material.dispose(); }
        else t.mesh.material.dispose();
        timed.splice(i, 1);
      }
    }
  },
};
let craterG = null, craterT = null;
function craterGeo() { return craterG || (craterG = new THREE.PlaneGeometry(2, 2)); }
function craterTex() {
  if (craterT) return craterT;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(32, 32, 2, 32, 32, 30);
  g.addColorStop(0, 'rgba(20,16,12,0.95)'); g.addColorStop(0.45, 'rgba(40,32,24,0.7)'); g.addColorStop(1, 'rgba(40,32,24,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  x.strokeStyle = 'rgba(10,8,6,0.9)'; x.lineWidth = 2;
  for (let i = 0; i < 9; i++) { // cracks
    let a = (i / 9) * Math.PI * 2 + Math.random() * 0.4, r = 6, px = 32, py = 32;
    x.beginPath(); x.moveTo(px, py);
    while (r < 31) { r += 3 + Math.random() * 4; a += (Math.random() - 0.5) * 0.6; px = 32 + Math.cos(a) * r; py = 32 + Math.sin(a) * r; x.lineTo(px, py); }
    x.stroke();
  }
  craterT = new THREE.CanvasTexture(c);
  craterT.magFilter = THREE.NearestFilter;
  return craterT;
}

// ------------------------------------------------------------ it dies in the rig: the frame bursts into scrap
// every joint's plates fly off as gibs (they ride the game's gib physics), sparks, smoke and a fireball
export function rigBurst(inst, vel = [0, 0, 0]) {
  inst.root.updateMatrixWorld(true);
  const c = new THREE.Vector3();
  inst.j.torso.getWorldPosition(c);
  const at = [c.x, c.y + 0.4, c.z];
  rfx.sparks(at, 70, 14, [0xfff2b0, 0xff9a3a, 0xff2bd6, 0x2ef2ff], 0.9, 0.16);
  rfx.smoke(at, 26, 0x3a3c40, 1.2, 2, 2.2, 0.9);
  rmesh.flash(at, 3.4, 0xff8a3a, 0.3);
  const floor = inst.root.getWorldPosition(new THREE.Vector3()).y;
  for (const n of inst.nodes) {
    for (const m of n.children) {
      if (!m.isMesh || m.material.isShaderMaterial || m.material.blending === THREE.AdditiveBlending) continue;
      if (Math.random() < 0.35 && m.geometry.attributes.position.count < 60) continue;
      const g = new THREE.Mesh(m.geometry, m.material); // shared geometry + material: the gib cleanup only removes it
      m.matrixWorld.decompose(g.position, g.quaternion, g.scale);
      G.scene.add(g);
      const out = [g.position.x - c.x, g.position.z - c.z], l = Math.hypot(out[0], out[1]) || 1;
      G.gibs.push({
        m: g, own: false, floorY: floor + 0.05, life: 3.5 + Math.random() * 1.5,
        v: [vel[0] * 0.4 + out[0] / l * (3 + Math.random() * 6) + Rn(2), 4 + Math.random() * 7, vel[2] * 0.4 + out[1] / l * (3 + Math.random() * 6) + Rn(2)],
        av: [Rn(9), Rn(9), Rn(9)],
      });
    }
  }
}

// ------------------------------------------------------------ the missile
// one mesh that turns itself along its flight (from how it moved since the last frame) right before it's drawn, so
// it flies nose-first wherever it's shown (live, killcam, play of the round), trailing smoke and a pink flame
let MISSILE = null;
function missileGeo() {
  if (MISSILE) return MISSILE;
  const parts = [], add = (g, col) => { const n = g.index ? g.toNonIndexed() : g; n.deleteAttribute('uv'); const c = new THREE.Color(col), arr = []; for (let i = 0; i < n.attributes.position.count; i++) arr.push(c.r, c.g, c.b); n.setAttribute('color', new THREE.Float32BufferAttribute(arr, 3)); parts.push(n); };
  add(new THREE.CylinderGeometry(0.075, 0.075, 0.5, 8).rotateX(Math.PI / 2), 0xd8dde2);
  add(new THREE.ConeGeometry(0.075, 0.2, 8).rotateX(-Math.PI / 2).translate(0, 0, -0.35), 0xe02020);
  add(new THREE.CylinderGeometry(0.08, 0.08, 0.07, 8).rotateX(Math.PI / 2).translate(0, 0, -0.1), 0xff2bd6);
  for (let i = 0; i < 4; i++) add(new THREE.BoxGeometry(0.012, 0.13, 0.14).translate(0, 0.1, 0.2).rotateZ((i * Math.PI) / 2), 0x3b4149);
  add(new THREE.CylinderGeometry(0.06, 0.045, 0.06, 8).rotateX(Math.PI / 2).translate(0, 0, 0.27), 0x222428);
  const g = mergeGeometries(parts, false);
  g.computeVertexNormals();
  MISSILE = g;
  return g;
}
const _mp = new THREE.Vector3(), _mq = new THREE.Quaternion(), _ms = new THREE.Vector3(1, 1, 1), _z = new THREE.Vector3(0, 0, -1);
export function buildRigMissile() {
  const grp = new THREE.Group();
  const body = new THREE.Mesh(missileGeo(), new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, fog: false }));
  const flame = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.5, 6, 1, true).rotateX(Math.PI / 2).translate(0, 0, 0.55),
    new THREE.MeshBasicMaterial({ color: 0xff7ae8, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  body.add(flame);
  grp.add(body);
  const st = { last: null, dir: new THREE.Vector3(0, 1, 0), t: 0 };
  body.onBeforeRender = () => {
    grp.getWorldPosition(_mp);
    if (st.last) {
      _d.subVectors(_mp, st.last);
      const l = _d.length();
      if (l > 1e-4) {
        st.dir.lerp(_d.multiplyScalar(1 / l), 0.5).normalize();
        // smoke + sparks along the path it just flew
        const n = Math.min(6, Math.ceil(l / 0.35));
        for (let i = 0; i < n; i++) {
          const u = i / n, p = [st.last.x + (_mp.x - st.last.x) * u, st.last.y + (_mp.y - st.last.y) * u, st.last.z + (_mp.z - st.last.z) * u];
          rfx.smoke(p, 1, 0xd8d4d0, 0.35, 0.3, 0.7, 0.05);
          if (Math.random() < 0.4) rfx.sparks(p, 1, 2, [0xff7ae8, 0xffd0a0], 0.2, 0.09);
        }
      }
    } else st.last = new THREE.Vector3();
    st.last.copy(_mp);
    _mq.setFromUnitVectors(_z, st.dir);
    body.matrixWorld.compose(_mp, _mq, _ms);
    flame.matrixWorld.multiplyMatrices(body.matrixWorld, flame.matrix);
    flame.scale.z = 0.7 + Math.random() * 0.6;
  };
  flame.onBeforeRender = () => { flame.matrixWorld.multiplyMatrices(body.matrixWorld, flame.matrix); };
  return grp;
}
