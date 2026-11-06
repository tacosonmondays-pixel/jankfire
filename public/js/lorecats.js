// The board of directors: five hidden cats (shared/secrets.js). Chunky low-poly cats on real cat proportions (about
// 46 cm nose to rump, 25 cm at the shoulder, then 1.3x so they read in a shooter), one rig in five poses (loaf, sit,
// lie, side, box) and five coats. They breathe, blink, flick their ears and tail, watch you walk up, and react when
// petted: happy squint + purr, a slow blink, a stretch, a roll, a headbutt, or a sassy swat.
import * as THREE from 'three';
import { M } from './models.js';

const SC = 1.3; // the whole cat
// fur, second fur, belly / socks / muzzle, eye colour, patches, nose
const COATS = {
  tabby: { a: 0xe8913a, b: 0xb8621e, w: 0xf6e2c4, eye: 0x9adf3a, nose: 0xd86a6a },
  tux: { a: 0x1c1a20, b: 0x101014, w: 0xf4f4f0, eye: 0xf2d23a, nose: 0x2a2026 },
  cream: { a: 0xf3e6cf, b: 0xe2cda8, w: 0xffffff, eye: 0x5ab4ff, nose: 0xf0a0b0 },
  grey: { a: 0x8a8f99, b: 0x6c707a, w: 0xc8ccd4, eye: 0xf2a83a, nose: 0x5a4a50 },
  calico: { a: 0xf6f1e6, b: 0xe07a2a, w: 0xffffff, eye: 0x7adf8a, nose: 0xf09aa0, c: 0x26222a },
};
const mesh = (g, c) => new THREE.Mesh(g, M(c));
const sph = (r, c, x = 0, y = 0, z = 0, sx = 1, sy = 1, sz = 1, ws = 9, hs = 7) => { const m = mesh(new THREE.SphereGeometry(r, ws, hs), c); m.position.set(x, y, z); m.scale.set(sx, sy, sz); return m; };
const box = (w, h, d, c, x = 0, y = 0, z = 0) => { const m = mesh(new THREE.BoxGeometry(w, h, d), c); m.position.set(x, y, z); return m; };
const cyl = (r0, r1, h, c, y = 0, seg = 7) => { const m = mesh(new THREE.CylinderGeometry(r0, r1, h, seg), c); m.position.y = y; return m; };
const grp = (x = 0, y = 0, z = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); return g; };
const lerp = (a, b, k) => a + (b - a) * k;
const ease = (k) => (k <= 0 ? 0 : k >= 1 ? 1 : k * k * (3 - 2 * k));
const bump = (k) => (k <= 0 || k >= 1 ? 0 : Math.sin(k * Math.PI)); // 0 -> 1 -> 0

// a label texture (the box says LEGAL)
function labelTex(text, bg, fg) {
  const c = document.createElement('canvas'); c.width = 128; c.height = 64;
  const g = c.getContext('2d'); g.fillStyle = bg; g.fillRect(0, 0, 128, 64);
  g.font = 'bold 30px "Comic Neue", "Comic Sans MS", cursive'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillStyle = fg; g.fillText(text, 64, 34); g.strokeStyle = fg; g.lineWidth = 3; g.strokeRect(6, 6, 116, 52);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

export function buildCat(s) {
  const C = COATS[s.coat] || COATS.tabby, root = new THREE.Group(), rig = grp(); rig.scale.setScalar(SC); root.add(rig);
  const fat = s.coat === 'grey' ? 1.28 : 1; // Meatloaf is a big boy
  const fluff = s.coat === 'cream' ? 1.12 : 1;
  // ---- body: a long egg, the chest a bit higher than the rump, a belly, haunches
  const body = grp(0, 0.17, 0); rig.add(body);
  const torso = sph(0.12, C.a, 0, 0, 0.02, 0.92 * fat * fluff, 0.86 * fluff, 1.75); body.add(torso);
  body.add(sph(0.1, C.w, 0, -0.035, -0.02, 0.8 * fat, 0.7, 1.5)); // the pale belly
  body.add(sph(0.085, C.w, 0, 0.01, -0.165, 1.05 * fluff, 1.1 * fluff, 0.8)); // chest fluff
  for (const sx of [-1, 1]) body.add(sph(0.075, C.a, sx * 0.065 * fat, -0.01, 0.13, 1, 1.05, 1.15)); // haunches
  // coat details: tabby stripes over the back, tux white chest blaze, calico patches
  if (s.coat === 'tabby' || s.coat === 'grey') for (let i = 0; i < 5; i++) { // stripes: thin slices of the torso, a hair bigger, so they sit on the fur
    const z = -0.1 + i * 0.055, f = Math.sqrt(Math.max(0, 1 - ((z - 0.02) / (0.12 * 1.75)) ** 2)) * 1.035;
    body.add(sph(0.12, C.b, 0, 0.004, z, 0.92 * fat * fluff * f, 0.86 * fluff * f, 0.1));
  }
  if (s.coat === 'calico') {
    body.add(sph(0.07, C.b, 0.04, 0.05, 0.08, 1.2, 0.7, 1.3)); body.add(sph(0.06, C.c, -0.05, 0.06, -0.05, 1.1, 0.6, 1.2));
    body.add(sph(0.05, C.b, -0.04, 0.03, 0.17, 1, 0.8, 1)); body.add(sph(0.045, C.c, 0.07, 0.02, -0.12, 0.8, 0.8, 1));
  }
  // ---- legs: front at the chest, back under the haunches. each a pivot with a leg and a paw (white socks on some)
  const legs = [];
  const sock = s.coat === 'tux' || s.coat === 'calico' || s.coat === 'cream' ? C.w : C.a;
  for (const [x, z, fr] of [[-0.055, -0.13, 1], [0.055, -0.13, 1], [-0.06, 0.15, 0], [0.06, 0.15, 0]]) {
    const L = grp(x * fat, -0.03, z); body.add(L);
    L.add(cyl(0.028, 0.024, 0.13, C.a, -0.065));
    const paw = sph(0.03, sock, 0, -0.13, -0.012, 1, 0.65, 1.3); L.add(paw);
    for (const tx of [-0.012, 0, 0.012]) L.add(sph(0.008, sock, tx, -0.135, -0.048, 1, 0.8, 1)); // toe beans, sort of
    legs.push({ g: L, fr });
  }
  // ---- head on a neck pivot: skull, cheeks, muzzle, nose, eyes with slit pupils, ears, whiskers
  const neck = grp(0, 0.075, -0.19); body.add(neck);
  const head = grp(0, 0.04, -0.03); neck.add(head);
  head.add(sph(0.078, C.a, 0, 0, 0, 1.12 * fluff, 0.96 * fluff, 1.0));
  for (const sx of [-1, 1]) head.add(sph(0.045, C.a, sx * 0.05, -0.022, -0.02, 1.1 * fluff, 0.85, 0.9)); // cheeks
  if (s.coat === 'tux') head.add(sph(0.05, C.w, 0, -0.025, -0.045, 1.05, 0.9, 0.9)); // the white lower face
  if (s.coat === 'calico') head.add(sph(0.05, C.b, 0.04, 0.03, -0.01, 1, 0.9, 1));
  if (s.coat === 'tabby' || s.coat === 'grey') for (const dx of [-0.018, 0, 0.018]) { const m = box(0.007, 0.026, 0.004, C.b, dx, 0.044, -0.063); m.rotation.set(-0.7, 0, dx * -12); head.add(m); } // the M on the forehead
  const muz = sph(0.03, C.w, 0, -0.03, -0.07, 1.35, 0.85, 0.9); head.add(muz);
  head.add(box(0.022, 0.014, 0.012, C.nose, 0, -0.012, -0.096)); // nose
  head.add(box(0.004, 0.016, 0.004, 0x3a2a2a, 0, -0.03, -0.097)); // the line under it
  const eyes = [];
  for (const sx of [-1, 1]) {
    const e = grp(sx * 0.036, 0.012, -0.068); head.add(e);
    e.add(sph(0.021, 0xf8f8f0, 0, 0, 0, 1.1, 1, 0.5, 8, 6)); // white rim
    e.add(sph(0.018, C.eye, 0, 0, -0.004, 1.05, 1, 0.5, 8, 6));
    const pu = box(0.007, 0.028, 0.006, 0x050505, 0, 0, -0.012); e.add(pu);
    e.add(box(0.005, 0.005, 0.004, 0xffffff, sx * -0.006, 0.008, -0.016)); // glint
    e.rotation.z = sx * -0.12; // a little almond tilt
    eyes.push({ e, pu });
  }
  const ears = [];
  for (const sx of [-1, 1]) {
    const p = grp(sx * 0.048, 0.055, 0.0); p.rotation.set(-0.05, 0, -sx * 0.28); head.add(p);
    p.add(mesh(new THREE.ConeGeometry(0.04, 0.056, 4).rotateY(Math.PI / 4).scale(1, 1, 0.5), C.a));
    p.children[0].position.y = 0.024;
    const inn = mesh(new THREE.ConeGeometry(0.025, 0.038, 4).rotateY(Math.PI / 4).scale(1, 1, 0.3), 0xf2a0b4); inn.position.set(0, 0.018, -0.009); p.add(inn);
    if (s.coat === 'calico' && sx > 0) p.children[0].material = M(C.c);
    ears.push({ p, sx });
  }
  for (const sx of [-1, 1]) for (let i = 0; i < 3; i++) { // whiskers
    const w = box(0.075, 0.0025, 0.0025, 0xffffff, sx * 0.065, -0.03 - i * 0.008, -0.075); w.rotation.set(0, sx * 0.15, sx * (0.12 - i * 0.12)); head.add(w);
  }
  // ---- tail: eight segments off the rump
  const tail = [], tailBase = grp(0, 0.02, 0.2); body.add(tailBase);
  let par = tailBase;
  for (let i = 0; i < 8; i++) {
    const g = grp(0, i ? 0.045 : 0, 0); par.add(g);
    const r = 0.022 * fluff * (1 - i * 0.05);
    g.add(cyl(r * 0.92, r, 0.05, i === 7 && s.coat === 'tux' ? C.w : i % 2 && (s.coat === 'tabby' || s.coat === 'grey') ? C.b : C.a, 0.025));
    g.add(sph(r, C.a, 0, 0, 0, 1, 1, 1, 6, 4));
    tail.push(g); par = g;
  }
  // ---- the executive touch
  if (s.coat === 'cream') { // Princess Gravy: a tiny crown
    const cr = grp(0, 0.085, 0.005); head.add(cr);
    cr.add(cyl(0.032, 0.032, 0.022, 0xffc21a, 0, 8));
    for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2, k = mesh(new THREE.ConeGeometry(0.009, 0.026, 4), 0xffc21a); k.position.set(Math.cos(a) * 0.028, 0.022, Math.sin(a) * 0.028); cr.add(k); }
    cr.add(sph(0.007, 0xff3a6a, 0, 0.012, -0.032, 1, 1, 1, 6, 4)); cr.rotation.z = 0.25;
  }
  if (s.coat === 'tux') { // Beans: a little red tie
    const t = box(0.026, 0.06, 0.008, 0xd02030, 0, -0.06, -0.228); t.rotation.x = 0.3; body.add(t);
    body.add(box(0.03, 0.018, 0.012, 0xa01020, 0, -0.03, -0.22));
  }
  if (s.coat === 'tabby') { // Biscuit (CFO): reading glasses down the nose
    for (const sx of [-1, 1]) { const r = mesh(new THREE.TorusGeometry(0.017, 0.003, 4, 10), 0x2a2a30); r.position.set(sx * 0.024, -0.008, -0.094); head.add(r); }
    head.add(box(0.012, 0.003, 0.003, 0x2a2a30, 0, -0.005, -0.095));
  }
  if (s.coat === 'grey') { // Meatloaf: an employee lanyard
    const lan = mesh(new THREE.TorusGeometry(0.06, 0.005, 4, 12, Math.PI), 0x2a6cff); lan.rotation.set(Math.PI / 2 + 0.5, 0, 0); lan.position.set(0, 0.04, -0.16); body.add(lan);
    body.add(box(0.035, 0.045, 0.004, 0xffffff, 0, -0.02, -0.235));
  }
  let boxG = null;
  if (s.pose === 'box') { // Gremlin (legal): in a cardboard box, flaps open, LEGAL on the side
    boxG = grp(); root.add(boxG);
    const CB = 0xb8874a, CBd = 0x9a6c36, W = 0.5, H = 0.24, D = 0.84;
    boxG.add(box(W, 0.012, D, CBd, 0, 0.006, 0));
    for (const [w, d, x, z] of [[W, 0.014, 0, -D / 2], [W, 0.014, 0, D / 2], [0.014, D, -W / 2, 0], [0.014, D, W / 2, 0]]) boxG.add(box(w, H, d, CB, x, H / 2, z));
    for (const [x, z, ax, w, d, r] of [[0, -D / 2, 'x', W, 0.18, 1], [0, D / 2, 'x', W, 0.18, -1], [-W / 2, 0, 'z', 0.15, D, -1], [W / 2, 0, 'z', 0.15, D, 1]]) {
      const f = grp(x, H, z); boxG.add(f);
      const fl = box(w, 0.01, d, CBd, ax === 'x' ? 0 : r * w / 2, 0, ax === 'x' ? -r * d / 2 : 0); f.add(fl);
      if (ax === 'x') f.rotation.x = r * 1.95; else f.rotation.z = r * 1.85; // flopped open
    }
    boxG.add(box(W + 0.002, 0.04, 0.05, 0xd8c890, 0, H - 0.02, -D / 2)); // tape
    const lab = new THREE.Mesh(new THREE.PlaneGeometry(0.26, 0.13), new THREE.MeshLambertMaterial({ map: labelTex('LEGAL', '#c89a5a', '#1a1208') }));
    lab.position.set(W / 2 + 0.009, H * 0.5, 0.05); lab.rotation.y = Math.PI / 2; boxG.add(lab);
  }
  const cat = { root, rig, body, torso, legs, neck, head, eyes, ears, tail, tailBase, boxG, s, coat: C,
    seed: Math.random() * 100, blinkAt: 1 + Math.random() * 3, twitch: [0, 0], twitchAt: 2 + Math.random() * 3, flickAt: 3, pet: null, look: [0, 0] };
  setPose(cat, s.pose);
  return cat;
}

// ---------------------------------------------------------------- poses (the rest pose each frame starts from)
function setPose(c, pose) {
  const P = c.P = { by: 0.17, brx: 0, brz: 0, bz: 0, legs: [[0, 0], [0, 0], [0, 0], [0, 0]], legVis: [1, 1, 1, 1], legS: [1, 1, 1, 1], nrx: 0, nry: 0, tail: { rx: 2.4, ry: 0, bend: [0.2, 0.25, 0.25, 0.2, 0.15, 0.1, 0.1, 0.1], side: 0 } };
  if (pose === 'loaf' || pose === 'box') { // legs tucked under, a perfect bread shape, the tail wrapped round one side
    P.by = 0.115; P.legs = [[-1.25, 0], [-1.25, 0], [1.3, 0], [1.3, 0]]; P.legVis = [1, 1, 0, 0];
    P.nrx = 0.1; P.tail = { rx: 1.75, ry: 0, bend: [0.1, 0.2, 0.3, 0.35, 0.35, 0.35, 0.3, 0.3], side: 1 };
  } else if (pose === 'sit') { // upright: front legs straight, rump down, the tail round the front paws
    P.by = 0.19; P.brx = 0.55; P.bz = 0.05; P.legs = [[-0.55, 0], [-0.55, 0], [0.75, 0], [0.75, 0]]; P.legS = [1.75, 1.75, 1, 1];
    P.nrx = 0.1; P.tail = { rx: 1.75, ry: 0.0, bend: [0.0, 0.25, 0.35, 0.4, 0.45, 0.5, 0.5, 0.5], side: 1 };
  } else if (pose === 'lie') { // sphinx: belly down, front paws out in front, head up and alert
    P.by = 0.105; P.legs = [[-1.45, 0], [-1.45, 0], [1.4, 0], [1.4, 0]]; P.nrx = -0.05;
    P.tail = { rx: 1.62, ry: 0, bend: [0.05, 0.1, 0.12, 0.1, 0.05, -0.05, -0.1, -0.15], side: 0.3 };
  } else if (pose === 'side') { // flopped on its side in the sun, legs out, belly showing
    P.by = 0.1; P.brz = 1.45; P.legs = [[-0.35, 0], [-0.55, 0], [0.4, 0], [0.6, 0]]; P.nrx = 0.25; P.nry = 0.0;
    P.tail = { rx: 1.75, ry: 0, bend: [0.05, 0.05, 0.08, 0.1, 0.1, 0.1, 0.12, 0.14], side: 0 };
  }
  if (pose === 'box') { c.rig.position.set(0, 0.07, 0.03); P.nrx = 0.25; P.tail = { rx: 0.55, ry: 0, bend: [0.35, 0.4, 0.35, 0.25, 0.1, -0.1, -0.2, -0.3], side: 0 }; } // the tail hangs out over the back edge
}

// ---------------------------------------------------------------- petting
const REACT = ['squint', 'squint', 'blink', 'headbutt', 'stretch', 'roll', 'swat'];
export function petCat(c, now, kind) {
  let k = kind || REACT[(Math.random() * REACT.length) | 0];
  if (k === 'roll' && c.s.pose !== 'side' && c.s.pose !== 'lie') k = 'headbutt'; // only a lying cat rolls over
  if (k === 'stretch' && (c.s.pose === 'box' || c.s.pose === 'sit')) k = 'blink';
  c.pet = { t: now, k, dur: k === 'stretch' ? 2.4 : k === 'roll' ? 2.6 : k === 'swat' ? 1.2 : 2.0 };
  return k;
}

// ---------------------------------------------------------------- every frame. eye = the camera (they watch you)
const tmp = new THREE.Vector3();
export function updateCat(c, dt, now, eye) {
  const t = now / 1000 + c.seed, P = c.P, pet = c.pet && (now - c.pet.t) / 1000 < c.pet.dur ? c.pet : null;
  const pk = pet ? (now - pet.t) / 1000 / pet.dur : 0, K = pet ? pet.k : '';
  // look at you when you're close (a lazy, clamped head turn), otherwise a slow look around
  let wy = Math.sin(t * 0.23) * 0.35 + Math.sin(t * 0.61) * 0.15, wx = Math.sin(t * 0.37) * 0.08;
  if (eye) {
    c.neck.getWorldPosition(tmp);
    const dx = eye[0] - tmp.x, dy = eye[1] - tmp.y, dz = eye[2] - tmp.z, d = Math.hypot(dx, dz);
    if (d < 7) {
      const yaw = Math.atan2(-dx, -dz) - c.root.rotation.y - (P.brz ? 0 : 0);
      let a = Math.atan2(Math.sin(yaw), Math.cos(yaw));
      a = Math.max(-1.1, Math.min(1.1, a));
      wy = a; wx = Math.max(-0.5, Math.min(0.6, Math.atan2(dy, d) * 0.8));
    }
  }
  c.look[0] += (wy - c.look[0]) * Math.min(1, dt * 3); c.look[1] += (wx - c.look[1]) * Math.min(1, dt * 3);
  // ---- body: breathing (and a purr rumble while petted)
  const purr = pet && K !== 'swat' ? (1 - pk) * 0.004 : 0;
  let by = P.by + Math.sin(t * 2.6) * 0.003, brx = P.brx, brz = P.brz, bz = P.bz;
  const legs = P.legs.map((l) => l.slice());
  let nrx = P.nrx + c.look[1], nry = P.nry + c.look[0], earFlat = 0, squint = 0, tailUp = 0, pupil = 1;
  if (K === 'squint' || K === 'headbutt') { squint = bump(Math.min(1, pk * 1.6)) > 0 ? Math.min(1, pk * 6) * (1 - ease((pk - 0.8) * 5)) : 0; tailUp = bump(pk); }
  if (K === 'headbutt') { const h = bump(Math.min(1, pk * 2)); nrx += h * 0.5; c.neck.position.z = -0.19 - h * 0.04; } else c.neck.position.z = -0.19;
  if (K === 'blink') { const b = (pk - 0.15) / 0.45; squint = b > 0 && b < 1 ? bump(b) : 0; nrx -= squint * 0.08; }
  if (K === 'stretch') { // front paws reach out, rump up, a big yawn (head back), then settle
    const s2 = bump(Math.min(1, pk * 1.25));
    brx -= s2 * 0.38; by += s2 * 0.05; legs[0][0] = lerp(legs[0][0], -1.5, s2); legs[1][0] = lerp(legs[1][0], -1.5, s2);
    legs[2][0] = lerp(legs[2][0], 0.2, s2); legs[3][0] = lerp(legs[3][0], 0.2, s2); nrx -= s2 * 0.55; squint = s2; tailUp = s2;
  }
  if (K === 'roll') { const r = bump(Math.min(1, pk * 1.1)); brz = lerp(P.brz, P.brz ? 2.9 : 1.45, r); legs.forEach((l, i) => { l[0] += Math.sin(t * 9 + i) * 0.35 * r; }); squint = r * 0.7; } // belly up, paws wiggling
  if (K === 'swat') { // ears back, pupils wide, one paw lashes out twice
    earFlat = bump(Math.min(1, pk * 1.4)); pupil = 1 + earFlat * 2.5;
    const w = Math.max(0, Math.sin(Math.min(1, pk * 1.6) * Math.PI * 2));
    legs[1][0] = lerp(legs[1][0], -2.1, w); legs[1][1] = 0.4 * w; nrx += earFlat * 0.12;
  }
  c.body.position.y = by + (purr ? (Math.random() - 0.5) * purr : 0); c.body.position.z = bz;
  c.body.rotation.x = brx; c.body.rotation.z = brz;
  c.legs.forEach((L, i) => { L.g.rotation.x = legs[i][0]; L.g.rotation.z = legs[i][1]; L.g.scale.y = P.legS[i]; L.g.visible = !!P.legVis[i] || K === 'stretch'; });
  c.neck.rotation.set(nrx - brx * 0.85, nry, -brz * 0.55); // keep the head roughly level when the body tilts
  // ---- eyes: blink every few seconds; squint when happy; pupils wide when annoyed
  if (t > c.blinkAt) c.blinkAt = t + 2.5 + Math.random() * 4;
  const blink = c.blinkAt - t > 0 && c.blinkAt - t < 0.12 ? 1 : 0;
  const shut = Math.max(blink, squint * 0.85);
  for (const e of c.eyes) { e.e.scale.y = Math.max(0.08, 1 - shut); e.pu.scale.x = pupil; }
  // ---- ears: a twitch now and then (one ear), flat when annoyed
  if (t > c.twitchAt) { c.twitch = [Math.random() < 0.5 ? t : c.twitch[0], Math.random() < 0.5 ? t : c.twitch[1]]; c.twitchAt = t + 1.5 + Math.random() * 4; }
  c.ears.forEach((E, i) => { const tw = bump((t - c.twitch[i]) / 0.25); E.p.rotation.z = -E.sx * (0.28 + earFlat * 0.9 + tw * 0.35); E.p.rotation.x = -0.05 + earFlat * 0.5 + tw * 0.2; });
  // ---- tail: a slow curl and swish; up and quivering when happy; lashing when annoyed
  const T = P.tail;
  if (t > c.flickAt + 0.5) c.flickAt = t + 2 + Math.random() * 4;
  const fl = bump((t - c.flickAt) / 0.5);
  c.tailBase.rotation.x = lerp(T.rx, 0.35, tailUp);
  c.tailBase.rotation.y = T.ry;
  c.tail.forEach((g, i) => {
    const w = i / 7;
    g.rotation.x = lerp(T.bend[i], -0.12, tailUp) + (i > 4 ? fl * 0.4 : 0);
    g.rotation.z = T.side * 0.28 * (i > 1 ? 1 : 0) + Math.sin(t * (earFlat ? 9 : 1.4) - i * 0.6) * (earFlat ? 0.3 : 0.06 + w * 0.08) + (tailUp ? Math.sin(t * 30 + i) * 0.03 * tailUp : 0);
  });
}
