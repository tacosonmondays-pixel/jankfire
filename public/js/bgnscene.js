// BOARD GAME NIGHT: the board scene (docs/party/DESIGN.md 5). THE KITCHEN TABLE at night: a fold-out cardboard
// board on the kitchen table, candy-coloured spaces with a printed icon, the crease down the middle, mannequin pawns, the
// foam die, the golden bread on its plate, snacks as scenery, THE RULES GUY at the side, the toaster podium. drawn with
// the game's renderer (post.js presets apply). the Blender set (x_bgn_kitchen, x_bgn_die, x_bgn_bakery, x_bgn_rulesguy,
// x_bgn_toaster: tools/blender/bgn/) swaps in when it lands; the code board below is the fallback, and its tiles stay
// for picking either way. everything the HUD needs goes through this small API:
// makeBoard() -> { scene, cam, sync(st), step(e), roll(e), frame(dt), pick(x, y), mark(ids), focus(seat), say(), jank(), cere(final), cereOn() }
import * as THREE from 'three';
import { G } from './ctx.js';
import { buildCharacter } from './models.js';
import { postBegin, postEnd } from './post.js';
import { authored, want, whenGlb, missingGlb } from './glbkit.js';
import { npcRig } from './lobbyscenes/npcrig.js';
import { PSys } from './fx.js';
import { sfx } from './audio.js';
import { BOARD, PLATE_IDS } from '/shared/bgnboard.js';
import { SPACE } from '/shared/bgn.js';
import { DEFAULT_LOOK } from '/shared/looks.js';

export const BS = 2.4; // board units -> metres
const TOP = 0.36; // the spaces' top
const PS = 0.78; // pawn scale (a 1.8 m mannequin -> about 1.4 m, on 2.4 m spaces)
const KS = 40; // the Blender kitchen is life size: x40 for the pawns (a 6 cm square = 2.4 m)
const KP = 30; // the toaster podium a bit smaller than the kitchen (still a giant toaster), so the pawns read on it
const CS = 1.5; // the pawns grow for THE TOASTING (their moment)
export const spacePos = (id, out = new THREE.Vector3()) => { const p = BOARD[id].p; return out.set(p[0] * BS, TOP, p[1] * BS); };
const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: o.r ?? 0.55, metalness: o.m ?? 0, emissive: o.e || 0x000000, emissiveIntensity: o.ei ?? 1 });
const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
// a Blender model: right after makeBoard (already loaded, e.g. by the kitchen lobby), or later when it lands (a missing
// file = the code model stays). never inside makeBoard: the callbacks use the whole scene
function glb(id, cb) {
  const a = authored(id);
  if (a) { queueMicrotask(() => cb(a.obj, a.meta)); return; }
  if (!missingGlb(id)) return;
  want(id, 3);
  whenGlb([id], () => { const b = authored(id); if (b) cb(b.obj, b.meta); });
}
// the kitchen's spaces have to be the board's spaces (shared/bgnboard.js), or the pawns would stand off the print
export function kitchenFits(meta) {
  if (!meta || meta.kind !== 'bgnkitchen' || !Array.isArray(meta.spaces) || meta.spaces.length !== BOARD.length || !(meta.scale > 0)) return false;
  if (!(Math.abs(meta.top * meta.scale - TOP) < 0.02)) return false;
  return BOARD.every((sp, i) => { const q = meta.spaces[i]; return Array.isArray(q) && Math.abs(q[0] * meta.scale - sp.p[0] * BS) < 0.05 && Math.abs(q[1] * meta.scale - sp.p[1] * BS) < 0.05; });
}

// the printed icon on a space (one canvas per kind)
const ICON = { c: '+3', f: '-3', j: '?!', s: '$', p: '~', L: 'LID', b: '' };
function iconTex(k) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 128;
  const x = cv.getContext('2d');
  x.fillStyle = SPACE[k].color; x.fillRect(0, 0, 128, 128);
  x.strokeStyle = 'rgba(0,0,0,0.55)'; x.lineWidth = 10; x.strokeRect(5, 5, 118, 118);
  x.fillStyle = k === 'L' || k === 's' || k === 'c' ? '#111' : '#fff';
  x.font = `bold ${k === 'L' ? 40 : 64}px "Comic Neue", "Comic Sans MS", sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(ICON[k], 64, 68);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}
function labelTex(txt, bg, fg, w = 256, h = 96) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const x = cv.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, w, h); x.fillStyle = fg;
  x.font = `bold ${Math.floor(h * 0.5)}px "Comic Neue", "Comic Sans MS", sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(txt, w / 2, h / 2 + 2);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
// a foam die face with its pips
function dieTex(n) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 128;
  const x = cv.getContext('2d');
  x.fillStyle = '#fff6e8'; x.fillRect(0, 0, 128, 128);
  x.strokeStyle = '#ff4fd8'; x.lineWidth = 8; x.strokeRect(4, 4, 120, 120);
  const P = { 1: [[64, 64]], 2: [[34, 34], [94, 94]], 3: [[30, 30], [64, 64], [98, 98]], 4: [[34, 34], [94, 34], [34, 94], [94, 94]], 5: [[32, 32], [96, 32], [64, 64], [32, 96], [96, 96]], 6: [[34, 28], [94, 28], [34, 64], [94, 64], [34, 100], [94, 100]] };
  x.fillStyle = n === 1 ? '#ff3030' : '#1a0a20';
  for (const [a, b] of P[n]) { x.beginPath(); x.arc(a, b, 12, 0, Math.PI * 2); x.fill(); }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
// box faces are +x -x +y -y +z -z: these faces, so `up` shows the number (x_bgn_die has its pips the same way round)
const DIE_FACES = [3, 4, 1, 6, 2, 5];
const DIE_UP = { 1: [0, 0, 0], 6: [Math.PI, 0, 0], 2: [-Math.PI / 2, 0, 0], 5: [Math.PI / 2, 0, 0], 3: [0, 0, Math.PI / 2], 4: [0, 0, -Math.PI / 2] };
// THE TOASTING's podium in its own frame (life size metres, x40 in the game). x_bgn_toaster's meta carries the same keys.
// spots: where 1st (on top of the toaster) .. 4th (the table, in the crumbs) end up. slot: the slot the winner goes in
const POD = { at: [0.585, 0.015, -0.12], top: 0.265, slot: [-0.024, 0.0], lever: [0.0, 0.235, 0.142], leverDrop: 0.1,
  spots: [[0.0, 0.265, 0.0], [-0.12, 0.107, 0.025], [0.12, 0.075, 0.025], [0.0, 0.0, 0.17]] };
const HOST = [-0.55, 0.38, -1.9]; // where THE RULES GUY stands on the table (x, z, yaw; life size)
const CERE = { hop: [0.3, 0.75, 1.2, 1.65], dur: 0.75, down: 2.5, pop: 4.4, apex: 5.05, land: 5.7, card: 7.6 }; // THE TOASTING's beats (s)
export const CERE_MS = CERE.card * 1000; // the end card waits for the toast

export function makeBoard() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x140d24);
  scene.fog = new THREE.Fog(0x140d24, 90, 260);
  const cam = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.1, 400);
  const hemi = new THREE.HemisphereLight(0x9a8cff, 0x2a1410, 0.55); scene.add(hemi);
  const lamp = new THREE.PointLight(0xffd59a, 380, 90, 1.6); lamp.position.set(-4, 26, -6); scene.add(lamp); // the kitchen lamp
  const key = new THREE.DirectionalLight(0xffffff, 0.8); key.position.set(10, 30, 16); scene.add(key);
  const rim = new THREE.DirectionalLight(0xff4fd8, 0.6); rim.position.set(-20, 8, -20); scene.add(rim);
  // the code board (the fallback): everything here hides when the Blender kitchen lands
  const code = new THREE.Group(); scene.add(code);
  const table = box(64, 1.6, 46, mat(0x6b3f22, { r: 0.7 })); table.position.y = -0.8; code.add(table);
  for (let i = -3; i <= 3; i++) { const s = box(64.2, 0.05, 0.12, mat(0x4a2a16)); s.position.set(0, 0.01, i * 6.4); code.add(s); } // planks
  const floor = box(200, 0.5, 200, mat(0x2a1a2e, { r: 0.9 })); floor.position.y = -18; code.add(floor);
  for (const [x, z] of [[-29, -20], [29, -20], [-29, 20], [29, 20]]) { const l = box(1.6, 17, 1.6, mat(0x5a3319)); l.position.set(x, -9.5, z); code.add(l); }
  const card = mat(0xd8b47a, { r: 0.85 }), edge = mat(0xb48a52, { r: 0.9 });
  for (const sx of [-1, 1]) { const h = box(13.6, 0.24, 24, card); h.position.set(sx * 6.9, 0.12, 0); code.add(h); const e = box(13.6, 0.18, 0.5, edge); e.position.set(sx * 6.9, 0.18, -11.8); code.add(e); const e2 = e.clone(); e2.position.z = 11.8; code.add(e2); }
  const crease = box(0.5, 0.26, 24, mat(0x7a5a33)); crease.position.y = 0.12; code.add(crease);
  // the spaces (kept for picking when the Blender board draws them)
  const tiles = new Map(), texs = {}, tileG = new THREE.Group(); scene.add(tileG);
  for (const sp of BOARD) {
    const m = new THREE.MeshStandardMaterial({ map: texs[sp.k] || (texs[sp.k] = iconTex(sp.k)), roughness: 0.35, metalness: 0.05 });
    const side = mat(new THREE.Color(SPACE[sp.k].color).multiplyScalar(0.6).getHex(), { r: 0.4 });
    const big = sp.k === 'L' ? 1.25 : 1;
    const t = new THREE.Mesh(new THREE.BoxGeometry(1.9 * big, 0.12, 1.9 * big), [side, side, m, side, side, side]);
    spacePos(sp.id, t.position); t.position.y = TOP - 0.06;
    t.userData.id = sp.id;
    tileG.add(t); tiles.set(sp.id, t);
    if (PLATE_IDS.includes(sp.id)) { const pl = new THREE.Mesh(new THREE.TorusGeometry(0.98, 0.09, 6, 24), mat(0xffffff, { r: 0.3 })); pl.rotation.x = Math.PI / 2; pl.position.copy(t.position); pl.position.y = TOP + 0.03; tileG.add(pl); } // a plate's rim: the bakery can sit here
  }
  // scenery: a soda can, a pizza box, a chip bag
  const can = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 3, 14), mat(0xff3030, { m: 0.6, r: 0.25 })); can.position.set(17, 1.5, -8); code.add(can);
  const can2 = can.clone(); can2.material = mat(0x4fd8ff, { m: 0.6, r: 0.25 }); can2.position.set(18.6, 1.5, -6.4); can2.rotation.z = 0.08; code.add(can2);
  const pizza = box(9, 0.8, 9, mat(0xc89a5a, { r: 0.9 })); pizza.position.set(-20, 0.4, 9); pizza.rotation.y = 0.3; code.add(pizza);
  const chips = box(5, 1.8, 3.2, mat(0xffe14d, { r: 0.3 })); chips.position.set(19, 0.9, 10); chips.rotation.set(0.2, -0.5, 0.15); code.add(chips);
  // the golden bread (and fake ones: a bit too shiny)
  const breadMat = mat(0xffb300, { m: 0.75, r: 0.25, e: 0x553300, ei: 0.6 }), fakeMat = mat(0xffb300, { m: 0.75, r: 0.05, e: 0x553300, ei: 1.4 });
  const codeLoaf = (fake) => {
    const g = new THREE.Group();
    const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.42, 0.9, 6, 12), fake ? fakeMat : breadMat); b.rotation.z = Math.PI / 2; b.position.y = 0.42; g.add(b);
    for (let i = -1; i <= 1; i++) { const cut = box(0.08, 0.1, 0.6, mat(0x8a5a00)); cut.position.set(i * 0.32, 0.84, 0); cut.rotation.y = 0.5; g.add(cut); }
    return g;
  };
  let breadSrc = null, stallSrc = null; // x_bgn_bakery's golden loaf (origin under its middle) and its little shop, once they land
  const loaf = (fake) => {
    if (!breadSrc) return codeLoaf(fake);
    const g = breadSrc.clone(true);
    if (fake) g.traverse((o) => { if (o.isMesh && o.material && /bread|gold/.test(o.material.name)) { o.material = o.material.clone(); o.material.roughness = 0.02; o.material.emissiveIntensity = (o.material.emissiveIntensity || 0.3) * 2.5; } }); // (too shiny: a sponge)
    return g;
  };
  const bakery = new THREE.Group(); scene.add(bakery); // the floating loaf over the bakery's space
  let bakeLoaf = codeLoaf(false); bakery.add(bakeLoaf);
  const stall = new THREE.Group(); scene.add(stall); // the little bakery shop on the board, facing its space
  // the die
  const die = new THREE.Group(); scene.add(die); die.visible = false;
  const dieCode = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.4, 1.4), DIE_FACES.map((n) => new THREE.MeshStandardMaterial({ map: dieTex(n), roughness: 0.8 }))); die.add(dieCode);
  const dieA = { t: 0, dur: 0, from: new THREE.Vector3(), to: new THREE.Vector3(), spin: new THREE.Euler(), end: new THREE.Euler(), on: false, hold: 0 };
  // pawns
  const pawns = new Map(); // seat -> { g, pos, q: [], hop, base }
  const traps = new Map(); // space -> mesh
  const marks = new THREE.Group(); scene.add(marks);
  const camA = { pos: new THREE.Vector3(0, 30, 24), look: new THREE.Vector3(0, 0, 1.5), want: null, top: false, shake: 0 };
  let st = null, focusSeat = -1;
  const K = { obj: null, meta: null, lampNode: null }; // the Blender kitchen, once it's in

  // ---------------------------------------------------------------- the Blender set
  glb('x_bgn_kitchen', (o, meta) => {
    if (!kitchenFits(meta)) { console.warn('x_bgn_kitchen: its spaces are not the board\'s spaces, keeping the code board'); return; }
    const s = meta.scale;
    o.scale.setScalar(s); scene.add(o);
    o.traverse((m) => { if (m.isMesh) { m.receiveShadow = true; m.castShadow = /snacks|chairs|lamp/.test(m.parent && m.parent.name) || /snacks|chairs/.test(m.name); } });
    K.obj = o; K.meta = meta; K.lampNode = o.getObjectByName('lamp');
    code.visible = false; tileG.visible = false; // (the tiles still answer pick())
    if (Array.isArray(meta.lamp)) { lamp.position.set(meta.lamp[0] * s, meta.lamp[1] * s - 1.5, meta.lamp[2] * s); spot.position.copy(lamp.position); }
    // night in the kitchen: the pendant's pool of light on the board, the rest falls off into the dark
    hemi.intensity = 0.32; key.intensity = 0.35; lamp.intensity = 140; spot.intensity = 420;
    if (G.realShadows) { spot.castShadow = true; spot.shadow.mapSize.set(1024, 1024); spot.shadow.bias = -0.0004; spot.shadow.normalBias = 0.05; }
    if (Array.isArray(meta.podium)) { POD.at = meta.podium; placePodium(); }
    if (Array.isArray(meta.host)) { HOST[0] = meta.host[0]; HOST[1] = meta.host[1]; HOST[2] = meta.host[2]; placeHost(); }
    scene.fog.near = 120; scene.fog.far = 320;
  });
  // the lamp's pool of light on the board (and the pawns' shadows on Too HD)
  const spot = new THREE.SpotLight(0xffcf8a, 0, 140, 0.8, 0.75, 1.25); spot.position.set(0, 27, 0.8); spot.target.position.set(0, 0, 0); scene.add(spot, spot.target);
  glb('x_bgn_die', (o, meta) => { if (!meta || meta.kind !== 'bgndie') return; const k = 1.4 / (meta.size || 1.4); o.scale.setScalar(k); die.remove(dieCode); die.add(o); });
  glb('x_bgn_bakery', (o, meta) => {
    if (!meta || meta.kind !== 'bgnbakery') return;
    const b = o.getObjectByName('bread'), sh = o.getObjectByName('stall');
    if (b) { b.parent.remove(b); b.position.set(0, 0, 0); breadSrc = b; bakery.remove(bakeLoaf); bakeLoaf = loaf(false); bakery.add(bakeLoaf); }
    if (sh) { sh.parent.remove(sh); sh.position.set(0, 0, 0); sh.traverse((m) => { if (m.isMesh) m.castShadow = true; }); stallSrc = sh; stall.add(sh); }
    for (const [at, m] of [...traps]) if (m.userData.k === 'fake') { scene.remove(m); traps.delete(at); } // (fakes get the shop too: from far off they look the same)
    if (st) syncTraps(st);
    if (cere && cere.win) holdBread(cere.win, true);
  });
  // THE TOASTING's podium: a toaster on a cereal box at the side of the board (code boxes until x_bgn_toaster lands)
  const pod = { g: new THREE.Group(), lever: null, lever0: 0, glow: [], code: new THREE.Group() };
  scene.add(pod.g); pod.g.add(pod.code);
  (function codePodium() {
    const c = pod.code, s = KP;
    const cb = box(0.33 * s, 0.075 * s, 0.23 * s, new THREE.MeshStandardMaterial({ color: 0xffe14d, roughness: 0.4 })); cb.position.y = 0.0375 * s; c.add(cb);
    const lab = new THREE.Mesh(new THREE.PlaneGeometry(0.3 * s, 0.2 * s), new THREE.MeshStandardMaterial({ map: labelTex("JANK O's", '#ff3030', '#ffe14d', 256, 160), roughness: 0.4 })); lab.rotation.x = -Math.PI / 2; lab.position.y = 0.0752 * s; c.add(lab);
    for (let i = 0; i < 2; i++) { const cube = box(0.016 * s, 0.016 * s, 0.016 * s, mat(0xffffff, { r: 0.6 })); cube.position.set(-0.12 * s, (0.075 + 0.008 + i * 0.016) * s, 0.025 * s); cube.rotation.y = i * 0.4; c.add(cube); }
    const chrome = mat(0xd8dce6, { m: 0.85, r: 0.18 });
    const body = box(0.155 * s, 0.19 * s, 0.27 * s, chrome); body.position.y = (0.075 + 0.095) * s; c.add(body);
    for (const x of [-0.024, 0.024]) { const sl = box(0.036 * s, 0.01 * s, 0.13 * s, new THREE.MeshStandardMaterial({ color: 0x120818, emissive: 0xff5a1a, emissiveIntensity: 0 })); sl.position.set(x * s, 0.2605 * s, 0); c.add(sl); pod.glow.push(sl.material); }
    const lev = new THREE.Group(); const knob = box(0.03 * s, 0.014 * s, 0.022 * s, mat(0xff3030, { r: 0.3 })); lev.add(knob); lev.position.set(POD.lever[0] * s, POD.lever[1] * s, POD.lever[2] * s); c.add(lev);
    pod.lever = lev; pod.lever0 = lev.position.y;
  })();
  function placePodium() { pod.g.position.set(POD.at[0] * KS, 0, POD.at[1] * KS); pod.g.rotation.y = POD.at[2] || 0; }
  placePodium();
  glb('x_bgn_toaster', (o, meta) => {
    if (!meta || meta.kind !== 'bgntoaster') return;
    for (const k of ['top', 'slot', 'lever', 'leverDrop', 'spots']) if (meta[k] != null) POD[k] = meta[k];
    o.scale.setScalar(KP); pod.g.remove(pod.code); pod.g.add(o);
    pod.glow = [];
    o.traverse((m) => { if (m.isMesh) { m.castShadow = m.receiveShadow = true; if (m.material && /toast_glow/.test(m.material.name)) { m.material = m.material.clone(); pod.glow.push(m.material); } } }); // (the slots' glow: its own copy, the lever's toast)
    const lv = o.getObjectByName('lever');
    if (lv) { pod.lever = lv; pod.lever0 = lv.position.y; }
  });
  // THE RULES GUY: an action figure of the host on the table, reading the rules (upside down)
  const host = { g: new THREE.Group(), rig: null, code: null, talkT: 0 };
  scene.add(host.g);
  (function codeHost() {
    let ch;
    try { ch = buildCharacter('#c8783a', { ...DEFAULT_LOOK, top: 'cardigan', topColor: '#c8783a', bottom: 'pants', bottomColor: '#3a3048', hair: 'none', skin: '#e0ac69' }); } catch { return; }
    const book = box(0.32, 0.42, 0.06, mat(0xff3030, { r: 0.4 })); book.position.set(0, 1.12, -0.32); book.rotation.x = 0.5; ch.root.add(book);
    ch.arm.rotation.set(-0.6, 0.35, 0); ch.armL.rotation.set(-0.6, -0.35, 0);
    ch.root.scale.setScalar(1.6); host.code = ch; host.g.add(ch.root);
  })();
  function placeHost() { host.g.position.set(HOST[0] * KS, 0, HOST[1] * KS); host.g.rotation.y = HOST[2]; if (host.rig) host.rig.baseYaw = HOST[2]; } // (facing the board and the camera)
  placeHost();
  const inks = [];
  glb('x_bgn_rulesguy', () => {
    const r = npcRig('x_bgn_rulesguy', (x) => { inks.push(x); return x; }, () => (G.settings && G.settings.jank | 0) !== 0);
    if (!r) return;
    if (host.code) { host.g.remove(host.code.root); host.code = null; }
    r.root.scale.setScalar((r.meta && r.meta.boardScale) || 1.45);
    r.root.traverse((m) => { if (m.isMesh) m.castShadow = true; });
    host.g.add(r.root); host.rig = r; r.baseYaw = HOST[2];
  });

  // ---------------------------------------------------------------- THE TOASTING: fireworks in this scene
  const fw = { a: new PSys(1600, THREE.AdditiveBlending), c: new PSys(900, THREE.NormalBlending), rockets: [] };
  scene.add(fw.a.points, fw.c.points);
  const FWC = [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff7a1a];
  const R = (s = 1) => (Math.random() * 2 - 1) * s;
  function rocket(from, to, dur, col) { fw.rockets.push({ from: from.clone(), to: to.clone(), t: 0, dur, col, trail: 0 }); try { sfx.fwWhistle(null, dur); } catch { /* (no audio yet) */ } }
  function burst(p, col, k = 1) {
    for (let i = 0; i < 12; i++) fw.a.spawn(p.x, p.y, p.z, R(20 * k), R(20 * k), R(20 * k), 0.14, 1.6 * k, 0.2 * k, 0xffffff, col, 1, 0, 6);
    for (let i = 0; i < 80; i++) {
      const a = [R(), R(), R()], l = Math.hypot(...a) || 1, v = (8 + Math.random() * 6) * k, life = 1 + Math.random() * 0.7;
      const vx = (a[0] / l) * v, vy = (a[1] / l) * v, vz = (a[2] / l) * v;
      fw.c.spawn(p.x, p.y, p.z, vx, vy, vz, life, 0.5 * k, 0.12 * k, Math.random() < 0.2 ? 0xffffff : col, col, 1, 5 * k, 1.8);
      if (i % 3 === 0) fw.a.spawn(p.x, p.y, p.z, vx, vy, vz, life * 0.8, 1.2 * k, 0.2 * k, col, col, 0.45, 5 * k, 1.8);
    }
    try { sfx.fwBang(null); sfx.fwCrackle(null); } catch { /* (no audio yet) */ }
  }
  function fwFrame(dt) {
    for (let i = fw.rockets.length - 1; i >= 0; i--) {
      const r = fw.rockets[i];
      r.t += dt;
      const k = Math.min(1, r.t / r.dur), e = 1 - (1 - k) * (1 - k);
      const x = r.from.x + (r.to.x - r.from.x) * k, y = r.from.y + (r.to.y - r.from.y) * e, z = r.from.z + (r.to.z - r.from.z) * k;
      r.trail += dt * 80;
      for (; r.trail >= 1; r.trail--) fw.a.spawn(x + R(0.1), y, z + R(0.1), R(0.8), -2 + R(0.8), R(0.8), 0.4 + Math.random() * 0.3, 0.4, 0.05, 0xffd27a, 0xff2a00, 1, 2, 1);
      if (k >= 1) { burst(r.to, r.col, 1.1); fw.rockets.splice(i, 1); }
    }
    fw.a.update(dt); fw.c.update(dt);
  }
  // a puff of toast smoke / sparks from the slots
  const puff = (p, n, col = 0x8a8090) => { for (let i = 0; i < n; i++) fw.c.spawn(p.x + R(0.6), p.y, p.z + R(1.6), R(0.6), 2 + Math.random() * 2, R(0.6), 0.9 + Math.random() * 0.6, 0.9, 2.2, col, 0x3a3440, 0.7, -0.6, 0.8); };

  // ---------------------------------------------------------------- pawns
  function pawnFor(s) {
    let P = pawns.get(s.i);
    const n = G.names && G.names.get(s.id), look = n && n.look, key = s.id + '|' + s.color;
    if (P && P.key === key) return P;
    if (P) { scene.remove(P.g); }
    const g = new THREE.Group();
    let ch, rig = null;
    try { rig = buildCharacter(s.color, look || undefined); ch = rig.root; } catch { ch = new THREE.Mesh(new THREE.CapsuleGeometry(0.4, 0.8, 4, 8), mat(s.color)); ch.position.y = 0.8; }
    ch.scale.setScalar(PS);
    ch.rotation.set((Math.random() - 0.5) * 0.18, Math.random() * 6, (Math.random() - 0.5) * 0.18); // built-in jank: a random tilt
    ch.traverse((m) => { if (m.isMesh) m.castShadow = true; });
    g.add(ch);
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.58, 0.16, 14), mat(s.color, { r: 0.3, e: s.color, ei: 0.25 })); base.position.y = 0.07; base.castShadow = true; g.add(base);
    scene.add(g);
    const pos = spacePos(s.at, new THREE.Vector3()).add(off(s.i));
    g.position.copy(pos);
    P = { i: s.i, g, ch, rig, key, pos, q: [], hop: 0, from: pos.clone(), to: pos.clone(), at: s.at, rot0: ch.rotation.clone() };
    pawns.set(s.i, P);
    if (cere) cereSnapPawn(P);
    return P;
  }
  const off = (i) => new THREE.Vector3((i % 2 ? 0.5 : -0.5), 0, (i < 2 ? -0.5 : 0.5)); // four pawns share a space
  const trapMesh = (k, at) => {
    if (k === 'fake') { // a fake bakery: the too-shiny loaf floating over the space, and (once it's in) the same little shop beside it
      const g = new THREE.Group(), l = loaf(true); g.add(l); g.userData.loaf = l;
      if (stallSrc) { const sh = stallSrc.clone(true), o = stallOff(at); sh.position.set(o.dx * BS, -0.06, o.dz * BS); sh.rotation.y = o.ry; g.add(sh); }
      return g;
    }
    const g = new THREE.Group();
    if (k === 'peel') { const p = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.12, 6, 10, Math.PI * 1.2), mat(0xffe14d, { r: 0.4 })); p.rotation.x = -Math.PI / 2; p.position.y = 0.12; g.add(p); }
    if (k === 'sign') { for (const s of [-1, 1]) { const b = box(0.7, 1.1, 0.06, mat(0xffe14d, { r: 0.3 })); b.position.set(0, 0.55, s * 0.2); b.rotation.x = s * 0.35; g.add(b); } }
    return g;
  };
  function syncTraps(s) {
    const want = new Map(s.traps.map(([at, k]) => [at, k]));
    for (const [at, m] of traps) if (want.get(at) !== m.userData.k) { scene.remove(m); traps.delete(at); }
    for (const [at, k] of want) if (!traps.has(at)) { const m = trapMesh(k, at); m.userData.k = k; spacePos(at, m.position); scene.add(m); traps.set(at, m); }
  }
  // the bakery's little shop sits one square in from its space, facing it
  function stallOff(id) { // one square in from a loop space (the crease's: beside it), its shopfront to the table's near side (the camera)
    const p = BOARD[id].p, side = Math.abs(p[0]) === 5, dx = side ? -Math.sign(p[0]) : p[0] === 0 ? 1 : 0, dz = side || p[0] === 0 ? 0 : -Math.sign(p[1]);
    return { dx, dz, ry: 0 };
  }
  function placeStall(id) {
    const p = BOARD[id].p, o = stallOff(id);
    stall.position.set((p[0] + o.dx) * BS, TOP - 0.06, (p[1] + o.dz) * BS);
    stall.rotation.y = o.ry;
  }

  // ---------------------------------------------------------------- THE TOASTING
  let cere = null; // { t, final, win, order, from: Map(seat -> Vector3) }
  const _v = new THREE.Vector3(), _w = new THREE.Vector3();
  const podPt = (p, out = new THREE.Vector3()) => { out.set(p[0] * KP, p[1] * KP, p[2] * KP); return pod.g.localToWorld(out); };
  function holdBread(i, on) { // the winner holds the golden bread up over their head
    const P = pawns.get(i);
    if (!P) return;
    if (P.bread) { P.ch.remove(P.bread); P.bread = null; }
    if (!on) return;
    const b = loaf(false); b.scale.setScalar(breadSrc ? 0.85 : 0.75); b.position.set(0, 2.55, -0.05); b.rotation.y = Math.PI / 2;
    P.ch.add(b); P.bread = b;
  }
  function startCere(final, skip) {
    if (!final || !st) return;
    pod.g.updateMatrixWorld(true);
    cere = { t: skip ? CERE.card : 0, final, win: final.win, order: final.place.map((r) => r[0]), from: new Map(), toasted: !!skip, fwT: 0, popped: !!skip, down: !!skip, ticks: 0 };
    for (const [i, P] of pawns) { P.q.length = 0; P.hop = 0; cere.from.set(i, P.g.position.clone()); P.ch.scale.setScalar(PS); }
    holdBread(cere.win, true);
    if (G.bgnCereStart) G.bgnCereStart();
  }
  function cereSnapPawn(P) { if (!cere) return; if (!cere.from.has(P.i)) cere.from.set(P.i, P.g.position.clone()); if (P.i === cere.win) holdBread(P.i, true); }
  function stopCere() {
    if (!cere) return;
    for (const [i, P] of pawns) {
      holdBread(i, false);
      P.ch.rotation.copy(P.rot0); P.ch.scale.setScalar(PS); P.g.scale.setScalar(1);
      if (P.rig) { P.rig.arm.rotation.set(0, 0, 0); P.rig.armL.rotation.set(0, 0, 0); }
      P.pos.copy(spacePos(P.at)).add(off(i)); P.g.position.copy(P.pos); P.g.visible = true;
    }
    if (pod.lever) pod.lever.position.y = pod.lever0;
    for (const m of pod.glow) m.emissiveIntensity = 0;
    cere = null;
  }
  // where each pawn ends up: 1st on the toaster, 2nd on the sugar cubes, 3rd on the box, 4th on the table
  function cereFrame(dt) {
    const c = cere; c.t += dt;
    const t = c.t;
    c.order.forEach((i, place) => {
      const P = pawns.get(i);
      if (!P) return;
      const h0g = place === 0 ? CERE.hop[3] : CERE.hop[3 - Math.min(place, 3)];
      P.g.scale.setScalar(1 + (CS - 1) * Math.min(1, Math.max(0, (t - h0g) / 0.5)));
      const spot = podPt(POD.spots[Math.min(place, 3)], _v);
      if (place === 0) { // the winner: into the slot, toasted, POP
        const slot = podPt([POD.slot[0], POD.top, POD.slot[1]], _w);
        const h0 = CERE.hop[3];
        if (t < h0) P.g.position.copy(c.from.get(i));
        else if (t < h0 + 0.85) { // a big jump up and into the slot
          const k = (t - h0) / 0.85, a = c.from.get(i);
          P.g.position.lerpVectors(a, slot, k); P.g.position.y = a.y + (slot.y - a.y) * k + Math.sin(k * Math.PI) * 7 - (k > 0.8 ? (k - 0.8) * 5 * 2.6 : 0);
          P.ch.rotation.x = P.rot0.x - k * Math.PI * 2;
        } else if (t < CERE.pop) { // in the toaster (just the bread pokes out), the toaster jiggles
          P.g.position.copy(slot); P.g.position.y = slot.y - 2.4 * PS * CS; P.ch.rotation.copy(P.rot0); P.ch.rotation.y = 0;
          if (P.bread) P.bread.visible = true;
        } else if (t < CERE.land) { // POP: straight up, spinning, then down onto the top
          const k = (t - CERE.pop) / (CERE.land - CERE.pop);
          const y0 = slot.y - 2.4 * PS * CS, top = spot.y, apex = top + 8;
          const yy = k < 0.5 ? y0 + (apex - y0) * (1 - (1 - k * 2) ** 2) : apex + (top - apex) * ((k - 0.5) * 2) ** 2;
          P.g.position.set(slot.x + (spot.x - slot.x) * k, yy, slot.z + (spot.z - slot.z) * k);
          P.ch.rotation.set(P.rot0.x * 0.3, k * Math.PI * 4, 0);
        } else { // on top, bread up, bobbing
          const k = t - CERE.land, sq = k < 0.25 ? 1 - Math.sin((k / 0.25) * Math.PI) * 0.3 : 1;
          P.g.position.copy(spot); P.g.position.y += Math.max(0, Math.sin(k * 5)) * 0.35 * (k > 0.4 ? 1 : 0);
          P.ch.rotation.set(0, Math.sin(k * 1.3) * 0.5, Math.sin(k * 2.6) * 0.06); P.ch.scale.set(PS * (2 - sq) ** 0.4, PS * sq, PS * (2 - sq) ** 0.4);
        }
        if (P.rig) { const up = t > CERE.pop ? 2.75 + Math.sin(t * 9) * 0.12 : 2.6; P.rig.arm.rotation.set(up, 0, 0.25); P.rig.armL.rotation.set(up, 0, -0.25); }
        return;
      }
      const h0 = CERE.hop[3 - Math.min(place, 3)];
      const a = c.from.get(i) || P.g.position;
      if (t < h0) P.g.position.copy(a);
      else if (t < h0 + CERE.dur) { const k = (t - h0) / CERE.dur; P.g.position.lerpVectors(a, spot, k); P.g.position.y += Math.sin(k * Math.PI) * (4 + a.distanceTo(spot) * 0.18); }
      else {
        P.g.position.copy(spot);
        const k = t - h0 - CERE.dur;
        if (place < 3) { // 2nd and 3rd clap for them (or for themselves)
          P.ch.rotation.set(0, Math.PI * 0.15 * (place === 1 ? 1 : -1), 0);
          if (P.rig && t > CERE.pop) { const cl = Math.abs(Math.sin(t * 11)) * 0.5; P.rig.arm.rotation.set(-0.2, 0.75 - cl, 0); P.rig.armL.rotation.set(-0.2, -0.75 + cl, 0); }
        } else { // 4th: on the table in the crumbs, head down
          P.ch.rotation.set(0.45, Math.sin(k * 0.6) * 0.3, 0.1);
          if (P.rig) { P.rig.arm.rotation.set(-1.5, 0, 0.05); P.rig.armL.rotation.set(-1.5, 0, -0.05); }
        }
      }
    });
    // the toaster: lever down (tick tick tick), glowing slots, smoke, then the spring
    const slotTop = podPt([POD.slot[0], POD.top + 0.004, POD.slot[1]], _w);
    if (!c.down && t >= CERE.down) { c.down = true; try { sfx.toastDown(); } catch { /* (no audio) */ } }
    if (t >= CERE.down && t < CERE.pop) {
      const k = Math.min(1, (t - CERE.down) / 0.18);
      if (pod.lever) pod.lever.position.y = pod.lever0 - POD.leverDrop * (pod.lever.parent === pod.code ? KP : 1) * k;
      for (const m of pod.glow) m.emissiveIntensity = Math.min(2.2, (t - CERE.down) * 1.4);
      const n = Math.floor((t - CERE.down) / 0.3); if (n > c.ticks) { c.ticks = n; try { sfx.toastTick(); } catch { /* (no audio) */ } puff(slotTop, 2); }
      pod.g.position.x = POD.at[0] * KS + Math.sin(t * 70) * 0.06; // (it rattles)
    }
    if (!c.popped && t >= CERE.pop) {
      c.popped = true; pod.g.position.x = POD.at[0] * KS;
      if (pod.lever) pod.lever.position.y = pod.lever0;
      try { sfx.toastPop(); } catch { /* (no audio) */ }
      camA.shake = 0.9;
      puff(slotTop, 14, 0xffd060);
      for (let k = 0; k < 3; k++) rocket(_v.copy(slotTop), new THREE.Vector3(slotTop.x + (k - 1) * 9, slotTop.y + 14 + k * 3, slotTop.z - 4 + k * 2), 0.55 + k * 0.18, FWC[(k * 2) % FWC.length]);
    }
    if (t >= CERE.pop) for (const m of pod.glow) m.emissiveIntensity = Math.max(0, m.emissiveIntensity - dt * 1.5);
    if (!c.toasted && t >= CERE.apex) { c.toasted = true; if (G.bgnToasted) G.bgnToasted(c.win); }
    if (t > CERE.land + 0.5) { c.fwT -= dt; if (c.fwT <= 0) { c.fwT = 1.4 + Math.random() * 1.2; const top = podPt(POD.spots[0], _w); rocket(top, new THREE.Vector3(top.x + R(12), top.y + 12 + Math.random() * 8, top.z - 6 + R(4)), 0.7, FWC[(Math.random() * FWC.length) | 0]); } }
  }
  // the ceremony's camera: wide on the podium for the line-up, in on the toaster for the pop, then a slow push in
  function cereCam(out, look) {
    const t = cere.t, top = podPt([0, POD.top, 0], _v);
    const k = Math.min(1, t / 1.2), push = t > CERE.land ? Math.min(1, (t - CERE.land) / 4) : 0;
    const wide = new THREE.Vector3(top.x - 3, top.y + 7, top.z + 24), close = new THREE.Vector3(top.x - 2, top.y + 6.5, top.z + 15 - push * 2.5);
    const mid = t < CERE.down ? 0 : Math.min(1, (t - CERE.down) / 1.4);
    out.copy(wide).lerp(close, mid);
    if (k < 1) out.lerp(camA.pos, 1 - k); // (fly over from wherever it was)
    look.set(top.x, top.y - (mid > 0 ? 1.2 : 3.4) + (t > CERE.pop ? Math.min(4, (t - CERE.pop) * 7) * (t < CERE.land ? 1 : 0.4) : 0), top.z);
  }

  return {
    scene, cam,
    sync(s) { // the whole state: pawns, bakery, traps (no animation: hops come from step())
      st = s;
      for (const seat of s.seats) {
        const P = pawnFor(seat);
        if (!cere && !P.q.length && !P.hop && P.at !== seat.at) { P.at = seat.at; P.pos.copy(spacePos(seat.at)).add(off(seat.i)); P.g.position.copy(P.pos); }
        P.at = seat.at;
      }
      spacePos(s.bakery, bakery.position); placeStall(s.bakery);
      syncTraps(s);
      if (s.ph === 'done' && s.final && !cere) startCere(s.final, true); // (joined during the toasting: straight to the end of it)
      if (s.ph !== 'done' && cere) stopCere(); // (play again)
    },
    step(e) { // one hop (or a slip back, a slide, a yank)
      const P = pawns.get(e.seat);
      if (!P) return;
      P.q.push({ to: e.to, fast: e.slide || e.back || e.yank });
      P.at = e.to;
      focusSeat = e.seat;
    },
    roll(e) { // throw the die from the roller's pawn; it lands on the server's face
      const P = pawns.get(e.seat);
      dieA.from.copy(P ? P.g.position : new THREE.Vector3()).add(new THREE.Vector3(0, 3, 0));
      dieA.to.copy(dieA.from).add(new THREE.Vector3(1.6, -2.2, 1.6));
      dieA.to.y = TOP + 0.7;
      const u = DIE_UP[e.v[e.v.length - 1]] || DIE_UP[1];
      dieA.end.set(u[0], u[1] + Math.random() * 0.4, u[2]);
      dieA.spin.set(6 + Math.random() * 6, 4 + Math.random() * 4, 5 + Math.random() * 5);
      dieA.t = 0; dieA.dur = 0.9; dieA.on = true; dieA.hold = 2.2;
      die.visible = true;
    },
    focus(seat) { focusSeat = seat; },
    topDown(on) { camA.top = on; },
    say() { if (host.rig) host.rig.talk(2.6); else host.talkT = 2.6; },
    jank() { if (host.rig) host.rig.gesture(); else host.talkT = 1.5; },
    cere(final) { stopCere(); startCere(final, false); },
    cereOn: () => !!cere && cere.t < CERE.card,
    // spaces you can click (sign / fake bread targets): glowing rings
    mark(ids) {
      marks.clear();
      for (const id of ids || []) { const r = new THREE.Mesh(new THREE.TorusGeometry(1.05, 0.1, 6, 20), mat(0x4fd8ff, { e: 0x4fd8ff, ei: 1.2 })); r.rotation.x = Math.PI / 2; spacePos(id, r.position); r.position.y += 0.15; r.userData.id = id; marks.add(r); }
    },
    pick(x, y) { // the space under the pointer (or null)
      const rc = new THREE.Raycaster(), v = new THREE.Vector2((x / innerWidth) * 2 - 1, -(y / innerHeight) * 2 + 1);
      rc.setFromCamera(v, cam);
      const h = rc.intersectObjects([...tiles.values()], false)[0];
      return h ? h.object.userData.id : null;
    },
    info: () => ({ kitchen: !!K.obj, die: !die.children.includes(dieCode), bakery: !!breadSrc, toaster: !pod.g.children.includes(pod.code), host: !!host.rig, cere: cere ? +cere.t.toFixed(2) : null, top: camA.top }), // (tests)
    frame(dt, t) {
      // hops: 0.3 s each, an arc and a squash on landing
      for (const [, P] of pawns) {
        if (cere) break;
        if (!P.hop && P.q.length) { const n = P.q.shift(); P.from.copy(P.g.position); P.to.copy(spacePos(n.to)).add(off(P.i)); P.hop = 0.0001; P.dur = n.fast ? 0.16 : 0.28; }
        if (P.hop) {
          P.hop = Math.min(1, P.hop + dt / P.dur);
          const k = P.hop;
          P.g.position.lerpVectors(P.from, P.to, k);
          P.g.position.y = P.from.y + Math.sin(k * Math.PI) * 1.1;
          const sq = k > 0.85 ? 1 - (1 - k) * 2 : 1; P.ch.scale.set(PS * (2 - sq) ** 0.3, PS * sq ** 0.5, PS * (2 - sq) ** 0.3);
          if (k >= 1) { P.hop = 0; P.ch.scale.setScalar(PS); if (G.bgnHop) G.bgnHop(); }
        }
      }
      if (cere) cereFrame(dt);
      fwFrame(dt);
      bakeLoaf.rotation.y += dt * 0.8; bakery.position.y = TOP + 0.25 + Math.sin(t * 2) * 0.12;
      for (const [, m] of traps) if (m.userData.k === 'fake') { const l = m.userData.loaf; l.rotation.y -= dt * 0.8; l.position.y = 0.25 + Math.sin(t * 2 + 1) * 0.12; }
      for (const r of marks.children) r.scale.setScalar(1 + Math.sin(t * 6) * 0.06);
      if (dieA.on) {
        dieA.t += dt;
        const k = Math.min(1, dieA.t / dieA.dur), e = 1 - (1 - k) ** 3;
        die.position.lerpVectors(dieA.from, dieA.to, e); die.position.y += Math.sin(k * Math.PI) * 1.6 * (1 - k);
        die.rotation.set(dieA.end.x + dieA.spin.x * (1 - e), dieA.end.y + dieA.spin.y * (1 - e), dieA.end.z + dieA.spin.z * (1 - e));
        if (k >= 1) { dieA.on = false; if (G.bgnThunk) G.bgnThunk(); }
      } else if (die.visible && (dieA.hold -= dt) <= 0) die.visible = false;
      // the host: talks when the rules guy has a line, looks at whoever's moving
      if (host.rig) { const P = focusSeat >= 0 && pawns.get(focusSeat); host.rig.update(dt, cere ? podPt([0, POD.top, 0], _w) : P ? P.g.position : null); }
      else if (host.code) { host.talkT = Math.max(0, host.talkT - dt); host.code.head.rotation.x = host.talkT > 0 ? Math.sin(t * 14) * 0.12 : 0; host.code.root.position.y = host.talkT > 0 ? Math.abs(Math.sin(t * 7)) * 0.15 : 0; }
      // camera: follow whoever's moving, overview otherwise, top-down on V, the toasting
      const portrait = innerHeight > innerWidth * 1.1, pull = portrait ? 1.9 : 1;
      cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix();
      const P = focusSeat >= 0 && pawns.get(focusSeat);
      let p, l;
      if (camA.top) { p = new THREE.Vector3(0, 46 * pull, 0.01); l = new THREE.Vector3(0, 0, 0); }
      else if (cere) { p = new THREE.Vector3(); l = new THREE.Vector3(); cereCam(p, l); if (portrait) p.sub(l).multiplyScalar(1.6).add(l); }
      else if (P && st && (st.ph === 'move' || st.ph === 'roll' || st.ph === 'land' || st.ph === 'turn' || st.ph === 'duel' || st.ph === 'event')) { const g = P.g.position; p = new THREE.Vector3(g.x * 0.6, 15 * pull, g.z * 0.6 + 12.5 * pull); l = new THREE.Vector3(g.x * 0.8, 0, g.z * 0.8); }
      else { p = new THREE.Vector3(0, 30 * pull, 23 * pull); l = new THREE.Vector3(0, 0, 1.5); }
      if (Array.isArray(G.bgnCamTest)) { const q = G.bgnCamTest; p.set(q[0], q[1], q[2]); l.set(q[3], q[4], q[5]); camA.pos.copy(p); camA.look.copy(l); } // (tests: a fixed camera for close-ups)
      const a = 1 - Math.exp(-dt * (cere ? 4 : 3));
      camA.pos.lerp(p, a); camA.look.lerp(l, a);
      cam.position.copy(camA.pos); cam.lookAt(camA.look);
      if (camA.shake > 0) { const k = camA.shake * camA.shake * 0.6; cam.position.x += R(k); cam.position.y += R(k); camA.shake = Math.max(0, camA.shake - dt * 2); }
      if (K.lampNode) K.lampNode.visible = !camA.top; // (the pendant would hang in front of the top view)
      const r = G.renderer, post = postBegin(r);
      r.setClearColor(scene.background, 1); r.clear();
      r.render(scene, cam);
      if (post && !postEnd(r)) { r.setRenderTarget(null); r.clear(); r.render(scene, cam); }
    },
  };
}
