// BOARD GAME NIGHT: the code-built board (docs/party/DESIGN.md 5). THE KITCHEN TABLE at night: a fold-out cardboard
// board on a wooden table, candy-coloured spaces with a printed icon, the crease down the middle, mannequin pawns, the
// foam die, the golden bread on its plate, snacks as scenery. chunky boxes and lathes, drawn with the game's renderer
// (post.js presets apply). PR 4 swaps in the Blender board: everything the HUD needs goes through this small API
// (makeBoard() -> { scene, cam, sync(st), step(e), roll(e), frame(dt), pick(x, y), mark(ids), focus(seat) }).
import * as THREE from 'three';
import { G } from './ctx.js';
import { buildCharacter } from './models.js';
import { postBegin, postEnd } from './post.js';
import { BOARD, PLATE_IDS } from '/shared/bgnboard.js';
import { SPACE } from '/shared/bgn.js';

export const BS = 2.4; // board units -> metres
const TOP = 0.36; // the spaces' top
const PS = 0.78; // pawn scale (a 1.8 m mannequin -> about 1.4 m, on 2.4 m spaces)
export const spacePos = (id, out = new THREE.Vector3()) => { const p = BOARD[id].p; return out.set(p[0] * BS, TOP, p[1] * BS); };
const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: o.r ?? 0.55, metalness: o.m ?? 0, emissive: o.e || 0x000000, emissiveIntensity: o.ei ?? 1 });
const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);

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
// box faces are +x -x +y -y +z -z: these faces, so `up` shows the number
const DIE_FACES = [3, 4, 1, 6, 2, 5];
const DIE_UP = { 1: [0, 0, 0], 6: [Math.PI, 0, 0], 2: [-Math.PI / 2, 0, 0], 5: [Math.PI / 2, 0, 0], 3: [0, 0, Math.PI / 2], 4: [0, 0, -Math.PI / 2] };

export function makeBoard() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x140d24);
  const cam = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.1, 400);
  scene.add(new THREE.HemisphereLight(0x9a8cff, 0x2a1410, 0.55));
  const lamp = new THREE.PointLight(0xffd59a, 380, 90, 1.6); lamp.position.set(-4, 26, -6); scene.add(lamp); // the kitchen lamp
  const key = new THREE.DirectionalLight(0xffffff, 0.8); key.position.set(10, 30, 16); scene.add(key);
  const rim = new THREE.DirectionalLight(0xff4fd8, 0.6); rim.position.set(-20, 8, -20); scene.add(rim);
  // the table and the floor under it
  const table = box(64, 1.6, 46, mat(0x6b3f22, { r: 0.7 })); table.position.y = -0.8; scene.add(table);
  for (let i = -3; i <= 3; i++) { const s = box(64.2, 0.05, 0.12, mat(0x4a2a16)); s.position.set(0, 0.01, i * 6.4); scene.add(s); } // planks
  const floor = box(200, 0.5, 200, mat(0x2a1a2e, { r: 0.9 })); floor.position.y = -18; scene.add(floor);
  for (const [x, z] of [[-29, -20], [29, -20], [-29, 20], [29, 20]]) { const l = box(1.6, 17, 1.6, mat(0x5a3319)); l.position.set(x, -9.5, z); scene.add(l); }
  // the board: cardboard, two halves either side of the crease
  const card = mat(0xd8b47a, { r: 0.85 }), edge = mat(0xb48a52, { r: 0.9 });
  for (const sx of [-1, 1]) { const h = box(13.6, 0.24, 24, card); h.position.set(sx * 6.9, 0.12, 0); scene.add(h); const e = box(13.6, 0.18, 0.5, edge); e.position.set(sx * 6.9, 0.18, -11.8); scene.add(e); const e2 = e.clone(); e2.position.z = 11.8; scene.add(e2); }
  const crease = box(0.5, 0.26, 24, mat(0x7a5a33)); crease.position.y = 0.12; scene.add(crease);
  // the spaces
  const tiles = new Map(), texs = {};
  for (const sp of BOARD) {
    const m = new THREE.MeshStandardMaterial({ map: texs[sp.k] || (texs[sp.k] = iconTex(sp.k)), roughness: 0.35, metalness: 0.05 });
    const side = mat(new THREE.Color(SPACE[sp.k].color).multiplyScalar(0.6).getHex(), { r: 0.4 });
    const big = sp.k === 'L' ? 1.25 : 1;
    const t = new THREE.Mesh(new THREE.BoxGeometry(1.9 * big, 0.12, 1.9 * big), [side, side, m, side, side, side]);
    spacePos(sp.id, t.position); t.position.y = TOP - 0.06;
    t.userData.id = sp.id;
    scene.add(t); tiles.set(sp.id, t);
    if (PLATE_IDS.includes(sp.id)) { const pl = new THREE.Mesh(new THREE.TorusGeometry(0.98, 0.09, 6, 24), mat(0xffffff, { r: 0.3 })); pl.rotation.x = Math.PI / 2; pl.position.copy(t.position); pl.position.y = TOP + 0.03; scene.add(pl); } // a plate's rim: the bakery can sit here
  }
  // scenery: a soda can, a pizza box, a chip bag, the lamp's glow on the table
  const can = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 3, 14), mat(0xff3030, { m: 0.6, r: 0.25 })); can.position.set(17, 1.5, -8); scene.add(can);
  const can2 = can.clone(); can2.material = mat(0x4fd8ff, { m: 0.6, r: 0.25 }); can2.position.set(18.6, 1.5, -6.4); can2.rotation.z = 0.08; scene.add(can2);
  const pizza = box(9, 0.8, 9, mat(0xc89a5a, { r: 0.9 })); pizza.position.set(-20, 0.4, 9); pizza.rotation.y = 0.3; scene.add(pizza);
  const chips = box(5, 1.8, 3.2, mat(0xffe14d, { r: 0.3 })); chips.position.set(19, 0.9, 10); chips.rotation.set(0.2, -0.5, 0.15); scene.add(chips);
  // the golden bread (and fake ones: a bit too shiny)
  const loaf = (fake) => {
    const g = new THREE.Group(), m = mat(0xffb300, { m: 0.75, r: fake ? 0.05 : 0.25, e: 0x553300, ei: fake ? 1.4 : 0.6 });
    const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.42, 0.9, 6, 12), m); b.rotation.z = Math.PI / 2; b.position.y = 0.42; g.add(b);
    for (let i = -1; i <= 1; i++) { const cut = box(0.08, 0.1, 0.6, mat(0x8a5a00)); cut.position.set(i * 0.32, 0.84, 0); cut.rotation.y = 0.5; g.add(cut); }
    return g;
  };
  const bakery = loaf(false); scene.add(bakery);
  // the die
  const die = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.4, 1.4), DIE_FACES.map((n) => new THREE.MeshStandardMaterial({ map: dieTex(n), roughness: 0.8 })));
  die.visible = false; scene.add(die);
  const dieA = { t: 0, dur: 0, from: new THREE.Vector3(), to: new THREE.Vector3(), spin: new THREE.Euler(), end: new THREE.Euler(), on: false, hold: 0 };
  // pawns
  const pawns = new Map(); // seat -> { g, pos, q: [], hop, base }
  const traps = new Map(); // space -> mesh
  const marks = new THREE.Group(); scene.add(marks);
  const camA = { pos: new THREE.Vector3(0, 30, 24), look: new THREE.Vector3(0, 0, 1.5), want: null, top: false };
  let st = null, focusSeat = -1;

  function pawnFor(s) {
    let P = pawns.get(s.i);
    const n = G.names && G.names.get(s.id), look = n && n.look, key = s.id + '|' + s.color;
    if (P && P.key === key) return P;
    if (P) { scene.remove(P.g); }
    const g = new THREE.Group();
    let ch;
    try { ch = buildCharacter(s.color, look || undefined).root; } catch { ch = new THREE.Mesh(new THREE.CapsuleGeometry(0.4, 0.8, 4, 8), mat(s.color)); ch.position.y = 0.8; }
    ch.scale.setScalar(PS);
    ch.rotation.set((Math.random() - 0.5) * 0.18, Math.random() * 6, (Math.random() - 0.5) * 0.18); // built-in jank: a random tilt
    g.add(ch);
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.58, 0.16, 14), mat(s.color, { r: 0.3, e: s.color, ei: 0.25 })); base.position.y = 0.07; g.add(base);
    scene.add(g);
    const pos = spacePos(s.at, new THREE.Vector3()).add(off(s.i));
    g.position.copy(pos);
    P = { i: s.i, g, ch, key, pos, q: [], hop: 0, from: pos.clone(), to: pos.clone(), at: s.at };
    pawns.set(s.i, P);
    return P;
  }
  const off = (i) => new THREE.Vector3((i % 2 ? 0.5 : -0.5), 0, (i < 2 ? -0.5 : 0.5)); // four pawns share a space
  const trapMesh = (k) => {
    if (k === 'fake') return loaf(true);
    const g = new THREE.Group();
    if (k === 'peel') { const p = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.12, 6, 10, Math.PI * 1.2), mat(0xffe14d, { r: 0.4 })); p.rotation.x = -Math.PI / 2; p.position.y = 0.12; g.add(p); }
    if (k === 'sign') { for (const s of [-1, 1]) { const b = box(0.7, 1.1, 0.06, mat(0xffe14d, { r: 0.3 })); b.position.set(0, 0.55, s * 0.2); b.rotation.x = s * 0.35; g.add(b); } }
    return g;
  };

  return {
    scene, cam,
    sync(s) { // the whole state: pawns, bakery, traps (no animation: hops come from step())
      st = s;
      for (const seat of s.seats) {
        const P = pawnFor(seat);
        if (!P.q.length && !P.hop && P.at !== seat.at) { P.at = seat.at; P.pos.copy(spacePos(seat.at)).add(off(seat.i)); P.g.position.copy(P.pos); }
      }
      spacePos(s.bakery, bakery.position);
      const want = new Map(s.traps.map(([at, k]) => [at, k]));
      for (const [at, m] of traps) if (want.get(at) !== m.userData.k) { scene.remove(m); traps.delete(at); }
      for (const [at, k] of want) if (!traps.has(at)) { const m = trapMesh(k); m.userData.k = k; spacePos(at, m.position); scene.add(m); traps.set(at, m); }
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
    frame(dt, t) {
      // hops: 0.3 s each, an arc and a squash on landing
      for (const [, P] of pawns) {
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
      bakery.rotation.y += dt * 0.8; bakery.position.y = TOP + 0.25 + Math.sin(t * 2) * 0.12;
      for (const [, m] of traps) if (m.userData.k === 'fake') { m.rotation.y -= dt * 0.8; m.position.y = TOP + 0.25 + Math.sin(t * 2 + 1) * 0.12; }
      for (const r of marks.children) r.scale.setScalar(1 + Math.sin(t * 6) * 0.06);
      if (dieA.on) {
        dieA.t += dt;
        const k = Math.min(1, dieA.t / dieA.dur), e = 1 - (1 - k) ** 3;
        die.position.lerpVectors(dieA.from, dieA.to, e); die.position.y += Math.sin(k * Math.PI) * 1.6 * (1 - k);
        die.rotation.set(dieA.end.x + dieA.spin.x * (1 - e), dieA.end.y + dieA.spin.y * (1 - e), dieA.end.z + dieA.spin.z * (1 - e));
        if (k >= 1) { dieA.on = false; if (G.bgnThunk) G.bgnThunk(); }
      } else if (die.visible && (dieA.hold -= dt) <= 0) die.visible = false;
      // camera: follow whoever's moving, overview otherwise, top-down on Tab
      const portrait = innerHeight > innerWidth * 1.1, pull = portrait ? 1.9 : 1;
      cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix();
      const P = focusSeat >= 0 && pawns.get(focusSeat);
      let p, l;
      if (camA.top) { p = new THREE.Vector3(0, 46 * pull, 0.01); l = new THREE.Vector3(0, 0, 0); }
      else if (P && st && (st.ph === 'move' || st.ph === 'roll' || st.ph === 'land' || st.ph === 'turn' || st.ph === 'duel' || st.ph === 'event')) { const g = P.g.position; p = new THREE.Vector3(g.x * 0.6, 15 * pull, g.z * 0.6 + 12.5 * pull); l = new THREE.Vector3(g.x * 0.8, 0, g.z * 0.8); }
      else { p = new THREE.Vector3(0, 30 * pull, 23 * pull); l = new THREE.Vector3(0, 0, 1.5); }
      const a = 1 - Math.exp(-dt * 3);
      camA.pos.lerp(p, a); camA.look.lerp(l, a);
      cam.position.copy(camA.pos); cam.lookAt(camA.look);
      const r = G.renderer, post = postBegin(r);
      r.setClearColor(scene.background, 1); r.clear();
      r.render(scene, cam);
      if (post && !postEnd(r)) { r.setRenderTarget(null); r.clear(); r.render(scene, cam); }
    },
  };
}
