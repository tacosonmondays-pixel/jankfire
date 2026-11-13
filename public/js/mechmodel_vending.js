// VENDING MACHINE, the code stand-in (until public/models/x_mech_vending.glb lands; same joint, marker and clip names as
// the hero model, agreed with the mech art session). A 5 m snack machine on stubby legs: a cyan cabinet with pink trim
// (your colour on the corners), a glass door full of glowing cans in rows (hinged on its left edge), a keypad, a coin
// slot for a face with glowing eyes either side, the delivery flap at the bottom, a lit JANK COLA marquee with chase
// bulbs, little robot arms, the OUT OF ORDER sign strapped to its back, heel jets. Space: faces -z, feet on y = 0.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { cbox } from './rigmodel.js';

// the skeleton: name -> [pivot (game coords, at rest), parent]
const PIV = {
  hips: [[0, 1.15, 0], 'root'], body: [[0, 1.3, 0], 'hips'], marquee: [[0, 4.5, 0], 'body'],
  door: [[-1.0, 2.75, -0.82], 'body'], flap: [[0, 1.86, -0.84], 'body'], sign: [[0, 3.05, 0.86], 'body'],
  shoulder_R: [[1.12, 3.72, 0], 'body'], upperarm_R: [[1.36, 3.68, 0], 'shoulder_R'], forearm_R: [[1.44, 2.86, -0.04], 'upperarm_R'], hand_R: [[1.46, 2.12, -0.08], 'forearm_R'],
  thigh_R: [[0.55, 1.15, 0], 'hips'], shin_R: [[0.58, 0.7, 0.02], 'thigh_R'], foot_R: [[0.6, 0.24, 0], 'shin_R'],
};
for (const [k, [at, par]] of Object.entries({ ...PIV })) if (k.endsWith('_R')) PIV[k.slice(0, -2) + '_L'] = [[-at[0], at[1], at[2]], par.endsWith('_R') ? par.slice(0, -2) + '_L' : par];
const MK = {
  mk_muzzle: ['body', [0, 4.0, -0.86]], mk_drop: ['flap', [0, 1.5, -1.0]], mk_sign: ['hips', [0, 0, -3.5]],
  mk_seat: ['body', [0, 3.3, 0]], mk_eject: ['body', [0, 4.7, 0]], mk_mark: ['marquee', [0, 5.6, 0]],
  mk_thrust_L: ['foot_L', [-0.6, 0.18, 0.32]], mk_thrust_R: ['foot_R', [0.6, 0.18, 0.32]],
};
const FZ = -0.8; // the cabinet's front face

// ------------------------------------------------------------ materials + textures (shared by every machine)
const mats = new Map();
const cached = (k, mk) => mats.get(k) || mats.set(k, mk()).get(k);
const lam = (c, e = 0.12) => cached('l' + c + e, () => new THREE.MeshLambertMaterial({ color: c, flatShading: true, emissive: new THREE.Color(c).multiplyScalar(e) }));
const phong = (c, sh = 70, e = 0.1) => cached('p' + c + sh + e, () => new THREE.MeshPhongMaterial({ color: c, specular: 0xffffff, shininess: sh, flatShading: true, emissive: new THREE.Color(c).multiplyScalar(e) }));
const glow = (c) => cached('g' + c, () => new THREE.MeshBasicMaterial({ color: c }));
const glass = () => cached('glass', () => new THREE.MeshPhongMaterial({ color: 0xbff4ff, specular: 0xffffff, shininess: 160, transparent: true, opacity: 0.22, depthWrite: false, side: THREE.DoubleSide, emissive: 0x0c3040 }));
function canvasMat(k, w, h, draw, basic) {
  return cached(k, () => {
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    draw(c.getContext('2d'), w, h);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
    return basic ? new THREE.MeshBasicMaterial({ map: t }) : new THREE.MeshLambertMaterial({ map: t, emissive: 0x202020 });
  });
}
const FONT = 'bold {s}px "Comic Neue", "Comic Sans MS", sans-serif';
const marqueeTex = () => canvasMat('marq', 512, 112, (g, w, h) => {
  g.fillStyle = '#ff2bd6'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#1a0820'; g.fillRect(8, 8, w - 16, h - 16);
  g.font = FONT.replace('{s}', 70); g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineWidth = 10; g.strokeStyle = '#ff2bd6'; g.strokeText('JANK COLA', w / 2, h / 2 + 4);
  g.fillStyle = '#fff36a'; g.fillText('JANK COLA', w / 2, h / 2 + 4);
  g.fillStyle = '#4fd8ff'; for (const x of [34, w - 34]) { g.beginPath(); g.arc(x, h / 2, 14, 0, 7); g.fill(); }
}, true);
const signTex = () => canvasMat('sign', 256, 144, (g, w, h) => {
  g.fillStyle = '#fff6d8'; g.fillRect(0, 0, w, h);
  for (let x = -20; x < w + 20; x += 20) { g.fillStyle = '#16161a'; g.fillRect(x, 0, 10, 12); g.fillRect(x, h - 12, 10, 12); g.fillStyle = '#ffd23a'; g.fillRect(x + 10, 0, 10, 12); g.fillRect(x + 10, h - 12, 10, 12); }
  g.font = FONT.replace('{s}', 44); g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineWidth = 6; g.strokeStyle = '#000';
  g.strokeText('OUT OF', w / 2, 50); g.fillStyle = '#ff3030'; g.fillText('OUT OF', w / 2, 50);
  g.strokeText('ORDER', w / 2, 96); g.fillStyle = '#ff00dc'; g.fillText('ORDER', w / 2, 96);
});
const sideTex = () => canvasMat('side', 256, 512, (g, w, h) => { // the side panel: cyan, a pink swoosh, a huge can, "ICE COLD (ALLEGEDLY)"
  g.fillStyle = '#3fc8f0'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#ff4fd8'; g.beginPath(); g.moveTo(0, 360); g.quadraticCurveTo(w / 2, 250, w, 300); g.lineTo(w, 380); g.quadraticCurveTo(w / 2, 330, 0, 440); g.fill();
  g.fillStyle = '#e8141c'; g.fillRect(70, 70, 116, 200); g.fillStyle = '#d8dee6'; g.fillRect(70, 58, 116, 16); g.fillRect(70, 266, 116, 12);
  g.fillStyle = '#fff'; g.fillRect(70, 140, 116, 50); g.fillStyle = '#e8141c'; g.font = FONT.replace('{s}', 36); g.textAlign = 'center'; g.fillText('JANK', 128, 178);
  g.fillStyle = '#1a0820'; g.font = FONT.replace('{s}', 26); g.fillText('ICE COLD', 128, 480); g.font = FONT.replace('{s}', 18); g.fillText('(allegedly)', 128, 500);
});
const keypadTex = () => canvasMat('keys', 64, 128, (g, w, h) => {
  g.fillStyle = '#1a1424'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#39ff14'; g.fillRect(6, 6, w - 12, 22); g.fillStyle = '#063'; g.font = 'bold 16px monospace'; g.fillText('$1.50', 10, 23);
  const cols = ['#ff4fd8', '#ffe14d', '#4fd8ff'];
  for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) { g.fillStyle = cols[(r + c) % 3]; g.fillRect(8 + c * 17, 40 + r * 20, 13, 14); }
}, true);
// the cans behind the glass: 3 shelves of 5, bright colours, merged per colour (one draw call each)
const CAN_COLS = [0xff3030, 0x4fd8ff, 0x39ff14, 0xffe14d, 0xff4fd8, 0xff8a2a];
let GEO = null;
function geo() {
  if (GEO) return GEO;
  const byCol = CAN_COLS.map(() => []);
  for (let r = 0; r < 3; r++) for (let c = 0; c < 5; c++) {
    const g = new THREE.CylinderGeometry(0.11, 0.11, 0.34, 8);
    g.translate(-0.88 + c * 0.27, 2.24 + r * 0.46, FZ + 0.26);
    byCol[(r * 2 + c) % CAN_COLS.length].push(g);
  }
  const shelves = [];
  for (let r = 0; r < 3; r++) { const g = new THREE.BoxGeometry(1.42, 0.04, 0.42); g.translate(-0.33, 2.05 + r * 0.46, FZ + 0.24); shelves.push(g); }
  const bulbs = [];
  for (let i = 0; i < 14; i++) { const g = new THREE.SphereGeometry(0.055, 6, 4); g.translate(-1.06 + i * (2.12 / 13), 0, -0.77); bulbs.push(g); }
  GEO = { cans: byCol.map((l) => (l.length ? mergeGeometries(l) : null)), shelves: mergeGeometries(shelves), bulbs: mergeGeometries(bulbs), bulbs2: mergeGeometries(bulbs.map((g) => g.clone().translate(0, 0.42, 0))) };
  return GEO;
}
function add(parent, g, m, p = [0, 0, 0], r = null) { const o = new THREE.Mesh(g, m); o.position.fromArray(p); if (r) o.rotation.set(r[0], r[1], r[2]); parent.add(o); return o; }
const loc = (j, w) => [w[0] - j.userData.at[0], w[1] - j.userData.at[1], w[2] - j.userData.at[2]];
const part = (j, g, m, w, r) => add(j, g, m, loc(j, w), r);
function limb(j, to, w, d, mat) {
  const a = j.userData.at, v = new THREE.Vector3(to[0] - a[0], to[1] - a[1], to[2] - a[2]), l = v.length();
  const m = add(j, cbox(w, l, d, 0.05), mat);
  m.position.copy(v.clone().multiplyScalar(0.5)); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.normalize());
  return m;
}

// ------------------------------------------------------------ build (j: the joints, made from PIV; own: your materials)
function build(j, own) {
  const g = geo(), acc = own.accent, cyan = phong(0x3fc8f0, 60, 0.12), pink = phong(0xff4fd8, 60, 0.2), dark = lam(0x1d1826, 0.06), steel = phong(0xc8d0da, 110, 0.08), black = lam(0x0c0a10, 0);
  // per-machine glows (animated: freed with the mech, mechmodel.js frees own.*)
  own.vmEye = new THREE.MeshBasicMaterial({ color: 0x4fffe0 });
  own.vmMarq = marqueeTex().clone(); own.vmMarq.color = new THREE.Color(1, 1, 1);
  own.vmBulbA = new THREE.MeshBasicMaterial({ color: 0xffe14d }); own.vmBulbB = new THREE.MeshBasicMaterial({ color: 0xff4fd8 });
  own.vmBack = new THREE.MeshBasicMaterial({ color: 0xdff8ff });
  // hips: the plinth / kick plate the cabinet sits on, your colour striped across it
  part(j.hips, cbox(2.1, 0.32, 1.5, 0.06), dark, [0, 1.18, 0]);
  part(j.hips, cbox(2.14, 0.08, 1.54, 0.02), acc, [0, 1.22, 0]);
  // body: the cabinet. sides with the decal, the back, the top lip, your colour on the corners
  // (a shell, not a solid box: the window in the front shows the cans inside)
  part(j.body, cbox(2.2, 3.2, 0.12, 0.05), cyan, [0, 2.9, 0.74]); // back
  for (const sx of [-1, 1]) part(j.body, cbox(0.12, 3.2, 1.6, 0.05), cyan, [sx * 1.04, 2.9, 0]); // sides
  part(j.body, cbox(2.2, 0.12, 1.6, 0.04), cyan, [0, 4.44, 0]); part(j.body, cbox(2.2, 0.12, 1.6, 0.04), cyan, [0, 1.36, 0]);
  part(j.body, cbox(2.2, 0.56, 0.12, 0.04), cyan, [0, 1.62, FZ + 0.06]); // the flap band
  part(j.body, cbox(0.6, 1.72, 0.12, 0.04), cyan, [0.8, 2.72, FZ + 0.06]); // the keypad column
  for (const sx of [-1, 1]) {
    part(j.body, new THREE.PlaneGeometry(1.4, 2.8), sideTex(), [sx * 1.105, 2.9, 0.02], [0, sx * Math.PI / 2, 0]);
    for (const sz of [-1, 1]) part(j.body, cbox(0.14, 3.24, 0.14, 0.03), acc, [sx * 1.07, 2.9, sz * 0.77]); // corner trims
  }
  part(j.body, cbox(2.3, 0.12, 1.7, 0.04), pink, [0, 4.5, 0]);
  part(j.body, cbox(2.3, 0.1, 1.7, 0.04), pink, [0, 1.32, 0]);
  // the front: the lit back panel and shelves of cans behind the door, the keypad, the face band, the flap opening
  part(j.body, new THREE.PlaneGeometry(1.5, 1.6), own.vmBack, [-0.25, 2.72, FZ + 0.46], [0, Math.PI, 0]);
  part(j.body, g.shelves, steel, [0, 0, 0]);
  g.cans.forEach((cg, i) => { if (cg) part(j.body, cg, glow(CAN_COLS[i]), [0, 0, 0]); });
  part(j.body, cbox(1.56, 1.66, 0.06, 0.02), dark, [-0.25, 2.72, FZ + 0.52]); // (the inside's back wall)
  for (const y of [1.88, 3.56]) part(j.body, cbox(1.6, 0.06, 0.6, 0.02), dark, [-0.25, y, FZ + 0.28]); // the window's sill and lintel
  part(j.body, cbox(0.46, 1.6, 0.08, 0.03), dark, [0.78, 2.72, FZ - 0.02]); // keypad column
  part(j.body, new THREE.PlaneGeometry(0.34, 0.68), keypadTex(), [0.78, 2.95, FZ - 0.065], [0, Math.PI, 0]);
  part(j.body, cbox(0.24, 0.1, 0.06, 0.02), black, [0.78, 2.3, FZ - 0.07]); // the change slot (it never gives change)
  // the face: a dark band, a chrome coin slot with a glowing rim in the middle, glowing eyes either side, brows
  part(j.body, cbox(2.12, 0.86, 0.08, 0.03), dark, [0, 4.0, FZ - 0.02]);
  part(j.body, cbox(0.26, 0.56, 0.1, 0.04), steel, [0, 4.0, FZ - 0.06]);
  part(j.body, cbox(0.07, 0.4, 0.05, 0.01), black, [0, 4.0, FZ - 0.11]);
  part(j.body, cbox(0.3, 0.6, 0.04, 0.02), own.hatch, [0, 4.0, FZ - 0.03]); // (its rim: lit when it's waiting for you)
  const eyes = [];
  for (const sx of [-1, 1]) {
    part(j.body, new THREE.CylinderGeometry(0.2, 0.2, 0.06, 14).rotateX(Math.PI / 2), black, [sx * 0.56, 4.02, FZ - 0.07]);
    const e = part(j.body, new THREE.CylinderGeometry(0.14, 0.14, 0.05, 14).rotateX(Math.PI / 2), own.vmEye, [sx * 0.56, 4.02, FZ - 0.1]);
    const b = part(j.body, cbox(0.38, 0.07, 0.06, 0.02), pink, [sx * 0.56, 4.3, FZ - 0.1]);
    eyes.push({ e, b, sx });
  }
  j.body.userData.vm = { eyes };
  // the flap opening (the flap joint swings in front of it)
  part(j.body, cbox(1.3, 0.42, 0.06, 0.02), black, [0, 1.64, FZ + 0.02]);
  part(j.body, cbox(1.42, 0.08, 0.1, 0.02), steel, [0, 1.88, FZ - 0.02]);
  // door: the glass front, hinged on its left edge, framed in pink, a handle
  const dW = 1.6, dH = 1.72, dc = [-1.0 + dW / 2, 2.72, FZ - 0.06];
  part(j.door, cbox(dW, 0.1, 0.1, 0.03), pink, [dc[0], dc[1] + dH / 2, dc[2]]);
  part(j.door, cbox(dW, 0.1, 0.1, 0.03), pink, [dc[0], dc[1] - dH / 2, dc[2]]);
  for (const x of [-1.0, -1.0 + dW]) part(j.door, cbox(0.1, dH, 0.1, 0.03), pink, [x, dc[1], dc[2]]);
  part(j.door, new THREE.PlaneGeometry(dW - 0.1, dH - 0.1), glass(), dc).renderOrder = 3;
  part(j.door, cbox(0.06, 0.4, 0.08, 0.02), steel, [-1.0 + dW - 0.16, dc[1], dc[2] - 0.08]);
  part(j.door, cbox(0.3, 0.08, 0.02, 0.01), lam(0xffffff, 0.4), [-0.55, dc[1] + 0.6, dc[2] - 0.06], [0, 0, 0.6]); // a glint
  // flap: the delivery flap, hinged at its top
  part(j.flap, cbox(1.28, 0.42, 0.06, 0.02), steel, [0, 1.65, FZ - 0.04]);
  part(j.flap, cbox(0.5, 0.1, 0.03, 0.01), lam(0xffe14d, 0.3), [0, 1.66, FZ - 0.08]); // PUSH
  // marquee: the lit sign box on top, bulbs chasing round it
  part(j.marquee, cbox(2.3, 0.6, 1.5, 0.05), dark, [0, 4.86, 0]);
  part(j.marquee, new THREE.PlaneGeometry(2.1, 0.46), own.vmMarq, [0, 4.86, -0.765], [0, Math.PI, 0]);
  part(j.marquee, new THREE.PlaneGeometry(2.1, 0.46), own.vmMarq, [0, 4.86, 0.765]);
  const ba = part(j.marquee, g.bulbs, own.vmBulbA, [0, 4.6, 0]), bb = part(j.marquee, g.bulbs2, own.vmBulbB, [0, 4.6, 0]);
  j.marquee.userData.bulbs = [ba, bb];
  // the OUT OF ORDER sign strapped to its back
  part(j.sign, cbox(1.9, 1.06, 0.07, 0.02), dark, [0, 3.05, 0.88]);
  part(j.sign, new THREE.PlaneGeometry(1.8, 0.98), signTex(), [0, 3.05, 0.92]);
  for (const y of [2.75, 3.35]) part(j.sign, cbox(2.24, 0.08, 0.06, 0.01), black, [0, y, 0.95]); // the straps
  // arms: a ball shoulder, stubby robot arm, a three-finger mitten
  for (const s of ['L', 'R']) {
    const sg = s === 'L' ? -1 : 1, P = (k) => PIV[k + '_' + s][0];
    part(j['shoulder_' + s], new THREE.SphereGeometry(0.26, 10, 8), pink, P('shoulder'));
    limb(j['upperarm_' + s], P('forearm'), 0.3, 0.3, steel);
    part(j['upperarm_' + s], cbox(0.36, 0.14, 0.36, 0.03), acc, [P('upperarm')[0] + sg * 0.02, P('upperarm')[1] - 0.3, 0]);
    limb(j['forearm_' + s], P('hand'), 0.28, 0.28, dark);
    part(j['forearm_' + s], new THREE.SphereGeometry(0.17, 8, 6), steel, P('forearm'));
    part(j['hand_' + s], cbox(0.32, 0.26, 0.3, 0.06), pink, [P('hand')[0], P('hand')[1] - 0.14, P('hand')[2]]);
    for (const f of [-0.09, 0, 0.09]) part(j['hand_' + s], cbox(0.07, 0.18, 0.08, 0.02), steel, [P('hand')[0] + f * sg * 0.3, P('hand')[1] - 0.34, P('hand')[2] + f]);
    // legs: short and stubby, big boots, heel jets
    limb(j['thigh_' + s], P('shin'), 0.4, 0.4, dark);
    part(j['shin_' + s], new THREE.SphereGeometry(0.2, 8, 6), steel, P('shin'));
    limb(j['shin_' + s], P('foot'), 0.34, 0.36, steel);
    part(j['foot_' + s], cbox(0.62, 0.3, 0.92, 0.08), pink, [P('foot')[0], 0.15, P('foot')[2] - 0.12]);
    part(j['foot_' + s], cbox(0.64, 0.08, 0.94, 0.02), acc, [P('foot')[0], 0.04, P('foot')[2] - 0.12]);
    part(j['foot_' + s], new THREE.CylinderGeometry(0.1, 0.13, 0.12, 8).rotateX(Math.PI / 2), black, [P('foot')[0], 0.18, 0.33]);
  }
}

// ------------------------------------------------------------ pose
// s (from mech.js + the play kit): spd, fwd, side, air, vy, landT, landK, empty, falling, boost, pitch, coinT, coining,
// dispT, wallT, stockT, kickT (s since each), jam (0/1), signOut (your wall is up: the sign's off its back)
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = (u) => u * u * (3 - 2 * u);
const env = (t, a, b, c) => (t < 0 || t > c ? 0 : t < a ? ease(t / a) : t < b ? 1 : 1 - ease((t - b) / (c - b))); // up by a, held to b, down by c
const tt = (x) => (Number.isFinite(x) ? x : 9); // (an empty mech in the world has no kit state: everything long ago)
const norm = (s) => (s.vmN ? s : Object.assign(s, { vmN: 1, coinT: tt(s.coinT), dispT: tt(s.dispT), wallT: tt(s.wallT), stockT: tt(s.stockT), kickT: tt(s.kickT), landT: tt(s.landT) }));
function clipOf(inst, s) {
  norm(s);
  if (s.jam) return 'stuck';
  if (s.kickT < 0.45) return 'kicked';
  if (s.stockT < 1.1) return 'restock';
  if (s.wallT < 0.7) return 'out_of_order';
  if (s.dispT < 0.8) return 'dispense';
  if (s.landT < 0.35) return 'land';
  if (s.air) return 'jump';
  if (s.coining || s.coinT < 0.25) return 'coin_fire';
  return s.spd > 12 * 0.7 ? 'run' : s.spd > 0.6 ? 'walk' : 'idle';
}
// a hero model with clips: the walk matched to the speed
function mix(inst, s) { if (inst.act && (inst.clip === 'walk' || inst.clip === 'run')) inst.act.timeScale = clamp(s.spd / 6, 0.4, 2.2); }
function pose(inst, s, dt, spr) {
  norm(s);
  const j = inst.j, T = inst.t, VM = inst.vm || (inst.vm = { ph: 0 });
  const run = clamp((s.spd || 0) / 12, 0, 1.3);
  if (!s.air && s.spd > 0.6) VM.ph += dt * (2.2 + s.spd * 0.42); // short stubby steps: a quick waddle
  const ph = VM.ph * Math.PI, sw = Math.sin(ph) * run;
  const coin = s.coinT < 0.12 ? 1 - s.coinT / 0.12 : 0, firing = s.coining || s.coinT < 0.25 ? 1 : 0;
  const disp = env(s.dispT, 0.12, 0.45, 0.85), wall = s.wallT < 0.9 ? s.wallT : 9, stock = env(s.stockT, 0.18, 0.85, 1.25), kick = s.kickT < 0.5 ? 1 - s.kickT / 0.5 : 0;
  const land = s.landT < 0.45 ? Math.sin(clamp(s.landT / 0.45, 0, 1) * Math.PI) * (0.35 + (s.landK || 0) * 0.65) : 0;
  const jam = s.jam ? 1 : 0;
  // ---- legs: stubby, alternating, the knee that bends a bit wrong (the jank)
  for (const [L, sg] of [['L', 1], ['R', -1]]) {
    const leg = sw * sg * 0.55, k = Math.max(0, -Math.sin(ph) * sg) * run;
    const crouch = land * 0.9 + stock * 0.25 + (s.air ? 0.3 : 0);
    j['thigh_' + L].rotation.x = spr(inst, 'th' + L, -leg - crouch * 0.6, 160, dt);
    j['shin_' + L].rotation.x = spr(inst, 'sn' + L, crouch * 1.2 + k * 0.9 + (inst.jank.knee === L ? 0.1 : 0), 160, dt);
    j['foot_' + L].rotation.x = spr(inst, 'ft' + L, leg - crouch * 0.6 - k * 0.6 + (s.air ? 0.3 : 0), 180, dt);
    j['thigh_' + L].rotation.z = spr(inst, 'tz' + L, sg * -0.04 * run, 120, dt);
  }
  // ---- the cabinet: waddles side to side, bobs, squashes on landings, rattles when jammed, jolts when kicked
  const rat = jam ? 1 : 0, rnd = () => (Math.random() - 0.5) * 2;
  j.hips.position.y = spr(inst, 'hy', j.hips.userData.rest[1] - Math.abs(Math.sin(ph)) * 0.1 * run - land * 0.4 + stock * 0.12 * Math.sin(T * 18), 260, dt);
  j.hips.scale.set(1 + land * 0.08, 1 - land * 0.1, 1 + land * 0.08);
  j.body.rotation.z = spr(inst, 'bz', Math.sin(ph) * 0.09 * run - clamp((s.side || 0) / 12, -1, 1) * 0.06 + inst.jank.tilt + kick * 0.25 * Math.sin(s.kickT * 30) + rat * rnd() * 0.04, 140, dt);
  j.body.rotation.x = spr(inst, 'bx', clamp((s.fwd || 0) / 12, -1, 1.3) * 0.06 + coin * 0.05 + firing * 0.03 - disp * 0.08 + rat * rnd() * 0.03 - kick * 0.12, 200, dt);
  j.body.rotation.y = spr(inst, 'by', Math.sin(ph * 0.5) * 0.04 * run + rat * rnd() * 0.04, 120, dt);
  j.body.position.z = spr(inst, 'bpz', j.body.userData.rest[2] + coin * 0.08, 400, dt); // coin recoil
  j.body.position.x = j.body.userData.rest[0] + rat * rnd() * 0.05;
  // ---- door swings open on a dispense, wide on a RESTOCK; the flap flips out; the marquee chases (flashes on RESTOCK)
  j.door.rotation.y = spr(inst, 'door', -(disp * 0.9 + stock * 1.7), 90, dt);
  j.flap.rotation.x = spr(inst, 'flap', disp > 0.2 ? -0.9 : 0, 220, dt);
  const B = j.marquee.userData.bulbs;
  if (B) { const on = Math.floor(T * (stock ? 16 : 5)) % 2 === 0; B[0].visible = jam ? Math.random() < 0.4 : on; B[1].visible = jam ? Math.random() < 0.4 : !on; }
  if (inst.own.vmMarq) { const f = jam ? (Math.random() < 0.5 ? 0.2 : 1) : stock ? (Math.floor(T * 12) % 2 ? 1.6 : 0.6) : 1; inst.own.vmMarq.color.setScalar(f); }
  j.marquee.rotation.z = spr(inst, 'mz', stock * Math.sin(T * 20) * 0.05 + coin * 0.02, 200, dt);
  j.marquee.position.y = spr(inst, 'my', j.marquee.userData.rest[1] + stock * 0.25, 160, dt);
  // ---- the face: eyes narrow while it fires, go wide on a RESTOCK, red (and jittering) when jammed; brows angry when firing
  const V = j.body.userData.vm;
  if (V) {
    if (inst.own.vmEye) inst.own.vmEye.color.setHex(jam ? (Math.floor(T * 8) % 2 ? 0xff3030 : 0x400000) : stock ? 0xffe14d : firing ? 0xff4fd8 : 0x4fffe0);
    for (const E of V.eyes) {
      E.e.scale.set(1 + stock * 0.3, 1, firing && !stock ? 0.45 : 1 + stock * 0.3); // (the cylinder's z is its height on the face)
      E.b.rotation.z = spr(inst, 'brow' + E.sx, firing ? E.sx * 0.35 : jam ? -E.sx * 0.3 : stock ? E.sx * -0.15 : 0, 200, dt);
      E.b.position.y = (E.b.userData.y0 ??= E.b.position.y) + stock * 0.08;
    }
  }
  // ---- arms. rest: hanging at its sides. firing: braced forward. dispense: one points at the flap. OUT OF ORDER: both
  // reach up and back, haul the sign over its head and slam it down in front. RESTOCK: both up, waving
  let xL = 0.12 * sw, xR = -0.12 * sw, zL = -0.12, zR = 0.12, fL = -0.25, fR = -0.25;
  if (firing) { xL = xR = -0.9; fL = fR = -0.7; zL = -0.25; zR = 0.25; xR += coin * 0.15; xL += coin * 0.15; }
  if (disp) { xR += (-0.6 - xR) * disp; fR += (-0.4 - fR) * disp; zR += (-0.1 - zR) * disp; }
  let signY = 0, signX = 0, signZ = 0, signVis = !s.signOut;
  if (wall < 0.9) {
    const up = clamp(wall / 0.22, 0, 1), down = clamp((wall - 0.22) / 0.14, 0, 1), back = clamp((wall - 0.45) / 0.4, 0, 1);
    const a = -3.0 * ease(up) + 2.0 * ease(down) + 1.0 * ease(back);
    xL = xR = a; zL = -0.3 * (1 - back); zR = 0.3 * (1 - back); fL = fR = -0.5 * (1 - down) - 0.1;
    signVis = wall < 0.36 || !s.signOut; // (once it's down the wall in the world is the sign)
    if (wall < 0.36) { // the sign comes off its back, up over its head, and down in front
      const k = ease(clamp(wall / 0.36, 0, 1));
      signX = -Math.PI * k; signY = Math.sin(k * Math.PI) * 2.2 + k * -1.2; signZ = -k * 2.1;
    }
  }
  if (stock) { const wv = Math.sin(T * 14) * 0.25; xL += (-2.9 - xL) * stock; xR += (-2.9 - xR) * stock; zL += (-0.45 + wv - zL) * stock; zR += (0.45 + wv - zR) * stock; fL += (-0.2 - fL) * stock; fR += (-0.2 - fR) * stock; }
  if (jam) { xL += rnd() * 0.15; xR += rnd() * 0.15; zL = -0.5; zR = 0.5; fL = fR = -1.2; } // hands up: "it's not me"
  j.upperarm_L.rotation.x = spr(inst, 'xL', xL, 260, dt); j.upperarm_R.rotation.x = spr(inst, 'xR', xR, 260, dt);
  j.upperarm_L.rotation.z = spr(inst, 'zL', zL, 200, dt); j.upperarm_R.rotation.z = spr(inst, 'zR', zR, 200, dt);
  j.forearm_L.rotation.x = spr(inst, 'fL', fL, 220, dt); j.forearm_R.rotation.x = spr(inst, 'fR', fR, 220, dt);
  j.sign.visible = signVis;
  j.sign.rotation.x = spr(inst, 'sx', signX, 500, dt);
  j.sign.position.y = j.sign.userData.rest[1] + signY; j.sign.position.z = j.sign.userData.rest[2] + signZ;
}

export const VMM = { PIV, MK, PRE: 'vm_', build, clipOf, mix, pose, ATT: ['body', 'door', 'flap', 'marquee', 'sign'] };
