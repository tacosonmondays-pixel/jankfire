// The hidden NPCs (shared/secrets.js): five original ☺ CORP employees built on the game's own mannequin (the lore says
// everyone respawns in a returned stockroom mannequin, NPCs too), each with their own outfit, props and idle life.
// build(s) -> { root, update(dt, now, ctx) }. ctx: { eye: camera pos, near: 0..1 how close you are, talk: chatting
// with you right now, say: a line is being typed out (they "speak") }.
import * as THREE from 'three';
import { M, buildCharacter } from './models.js';
import { sfx } from './audio.js';

const mesh = (g, c, basic) => new THREE.Mesh(g, M(c, basic));
const box = (w, h, d, c, x = 0, y = 0, z = 0, basic) => { const m = mesh(new THREE.BoxGeometry(w, h, d), c, basic); m.position.set(x, y, z); return m; };
const sph = (r, c, x = 0, y = 0, z = 0, ws = 8, hs = 6) => { const m = mesh(new THREE.SphereGeometry(r, ws, hs), c); m.position.set(x, y, z); return m; };
const cyl = (r0, r1, h, c, x = 0, y = 0, z = 0, seg = 8) => { const m = mesh(new THREE.CylinderGeometry(r0, r1, h, seg), c); m.position.set(x, y, z); return m; };
const grp = (x = 0, y = 0, z = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); return g; };
const lerp = (a, b, k) => a + (b - a) * k;
const bump = (k) => (k <= 0 || k >= 1 ? 0 : Math.sin(k * Math.PI));
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
// a canvas texture: draw(g, w, h)
function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.userData.canvas = c; return t;
}
const FONT = (px) => `bold ${px}px "Comic Neue", "Comic Sans MS", cursive`;
function panel(w, h, tex, basic = false) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), basic ? new THREE.MeshBasicMaterial({ map: tex }) : new THREE.MeshLambertMaterial({ map: tex }));
  return m;
}
// yaw (0 = looking down -z) from a to b
const yawTo = (ax, az, bx, bz) => Math.atan2(-(bx - ax), -(bz - az));

// every NPC: the mannequin in an outfit. scale = players are drawn 1.2x; NPCs a hair smaller so the props fit real sizes
function mannequin(color, look) {
  const ch = buildCharacter(color, { color: '', head: 'none', face: 'none', back: 'none', skin: '', hair: 'none', hairColor: '#1a1a1a', top: 'tank', topColor: '', bottom: 'shorts', bottomColor: '', ...look });
  ch.body.rotation.z = 0; // (the random lean stays out: they hold still poses)
  ch.root.scale.setScalar(1.08);
  return ch;
}
const SIT = (ch, seatY) => { // hips on a seat seatY above the root, thighs forward, shins down
  ch.body.position.y = seatY - 0.92 + 0.07;
  ch.legL.rotation.x = ch.legR.rotation.x = 1.5; ch.kneeL.rotation.x = ch.kneeR.rotation.x = -1.5; // (+x swings a leg forward)
};
// head turns toward the camera (clamped), eased. h = the head's state { y, x }
function headLook(ch, st, eye, rootYaw, k, dt, maxY = 1.0) {
  let ty = 0, tx = 0;
  if (eye && k > 0) {
    const p = new THREE.Vector3(); ch.head.getWorldPosition(p);
    ty = Math.max(-maxY, Math.min(maxY, wrapA(yawTo(p.x, p.z, eye[0], eye[2]) - rootYaw))) * k;
    tx = Math.max(-0.5, Math.min(0.5, Math.atan2(eye[1] - p.y, Math.hypot(eye[0] - p.x, eye[2] - p.z)))) * k;
  }
  st.y = lerp(st.y, ty + (st.oy || 0), Math.min(1, dt * 4)); st.x = lerp(st.x, tx + (st.ox || 0), Math.min(1, dt * 4));
  ch.head.rotation.y = st.y; ch.head.rotation.x = st.x;
}
// turn a body group (under root) round to face the camera when you come close, back to its spot when you leave
function faceYou(root, body, ctx, k, dt, speed) {
  const want = k > 0.5 && ctx.eye ? wrapA(yawTo(root.position.x, root.position.z, ctx.eye[0], ctx.eye[2]) - root.rotation.y) : 0;
  body.rotation.y += wrapA(want - body.rotation.y) * Math.min(1, dt * speed);
}
// talking: little head nods and a hand that moves with the words
function speak(ch, now, say, k = 1) {
  if (!say) return 0;
  const t = now / 1000;
  ch.head.rotation.x += Math.sin(t * 13) * 0.04 * k + Math.sin(t * 5.3) * 0.03 * k;
  return Math.sin(t * 3.1) * 0.5 + 0.5;
}

// ================================================================ GARY, regional manager. the site office, at his desk
function gary(s) {
  const root = grp(), base = grp(); root.add(base);
  // office chair: five-star base on casters, gas lift, seat, backrest, armrests. the top half swivels
  for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2, leg = box(0.05, 0.04, 0.32, 0x26262c, Math.sin(a) * 0.15, 0.07, Math.cos(a) * 0.15); leg.rotation.y = a; base.add(leg); base.add(sph(0.032, 0x111114, Math.sin(a) * 0.3, 0.032, Math.cos(a) * 0.3)); }
  base.add(cyl(0.03, 0.03, 0.34, 0x9aa0aa, 0, 0.26, 0));
  const swivel = grp(); root.add(swivel);
  swivel.add(box(0.5, 0.08, 0.48, 0x2a2a34, 0, 0.47, 0)); swivel.add(box(0.46, 0.03, 0.44, 0x3a3a48, 0, 0.515, 0)); // seat + cushion
  const back = box(0.46, 0.56, 0.07, 0x2a2a34, 0, 0.88, 0.26); back.rotation.x = 0.12; swivel.add(back);
  swivel.add(box(0.06, 0.32, 0.05, 0x26262c, 0, 0.62, 0.25));
  for (const sx of [-1, 1]) { swivel.add(box(0.05, 0.22, 0.05, 0x26262c, sx * 0.25, 0.6, 0.02)); swivel.add(box(0.07, 0.03, 0.26, 0x1a1a20, sx * 0.25, 0.72, 0.0)); }
  const ch = mannequin('#3a3a44', { top: 'suit', topColor: '#454a58', bottom: 'pants', bottomColor: '#30333c', hair: 'short', hairColor: '#7a6a5a', skin: '#ffdbac' });
  swivel.add(ch.root); SIT(ch, 0.54);
  // a comb-over: three strands across the bald patch, and the tie pulled loose
  for (let i = 0; i < 3; i++) { const st = box(0.24, 0.012, 0.02, 0x7a6a5a, 0.01, 0.305, -0.05 + i * 0.04); st.rotation.z = -0.08; ch.head.add(st); }
  // the desk is the map's; his stuff on it (desk top 0.73 above the floor he's on, a metre in front)
  const desk = grp(0, 0.73, -1.18); root.add(desk);
  const crt = grp(0.25, 0, 0.12); desk.add(crt);
  crt.add(box(0.44, 0.38, 0.4, 0xd8d0b8, 0, 0.24, 0)); crt.add(box(0.3, 0.26, 0.2, 0xcfc6ad, 0, 0.24, -0.26)); crt.add(box(0.2, 0.04, 0.2, 0xcfc6ad, 0, 0.02, 0.02));
  const scr = canvasTex(128, 96, () => {});
  const screen = panel(0.36, 0.28, scr, true); screen.position.set(0, 0.25, 0.201); crt.add(screen); // facing him
  desk.add(box(0.42, 0.025, 0.14, 0x2a2a2e, 0.2, 0.012, 0.34)); // keyboard
  const mugT = canvasTex(128, 64, (g, w, h) => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.fillStyle = '#c02030'; g.font = FONT(14); g.textAlign = 'center'; g.fillText("WORLD'S", w / 2, 22); g.fillText('OKAYEST', w / 2, 38); g.fillText('MANAGER', w / 2, 54); });
  const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.042, 0.1, 12), [new THREE.MeshLambertMaterial({ map: mugT }), M(0xffffff), M(0x3a2010)]);
  mug.position.set(-0.32, 0.05, 0.25); mug.rotation.y = 0.6; desk.add(mug);
  { const h = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.009, 5, 10), M(0xffffff)); h.position.set(-0.36, 0.05, 0.28); h.rotation.y = 0.6 + Math.PI / 2; desk.add(h); }
  for (let i = 0; i < 6; i++) { const p = box(0.21, 0.012, 0.29, i % 2 ? 0xf4f4ee : 0xe8e8e0, -0.12, 0.006 + i * 0.012, -0.05); p.rotation.y = (Math.random() - 0.5) * 0.25; desk.add(p); } // the paperwork
  const plate = canvasTex(128, 32, (g, w, h) => { g.fillStyle = '#c8a040'; g.fillRect(0, 0, w, h); g.fillStyle = '#1a1208'; g.font = FONT(15); g.textAlign = 'center'; g.fillText('GARY · REGIONAL MGR', w / 2, 21); });
  const np = panel(0.26, 0.065, plate); np.position.set(-0.05, 0.04, 0.4); np.rotation.set(-0.35, Math.PI, 0, 'YXZ'); desk.add(np); // facing whoever walks in
  desk.add(box(0.28, 0.05, 0.04, 0x3a2a1a, -0.05, 0.025, 0.42)); // its stand
  // a very dead office plant
  desk.add(cyl(0.05, 0.04, 0.09, 0xb05a2a, -0.5, 0.045, -0.1));
  { const st = cyl(0.006, 0.006, 0.22, 0x6a5030, -0.5, 0.18, -0.1, 4); st.rotation.z = 0.25; desk.add(st); const lf = box(0.06, 0.004, 0.025, 0x8a7040, -0.47, 0.25, -0.1); lf.rotation.z = -0.9; desk.add(lf); }
  // screen: the quarterly targets chart, the bars going down, the line going down faster
  let drawT = 0;
  const drawScreen = (t) => {
    const c = scr.userData.canvas, g = c.getContext('2d');
    g.fillStyle = '#0a1a40'; g.fillRect(0, 0, 128, 96);
    g.fillStyle = '#4fd8ff'; g.font = FONT(12); g.fillText('Q4 TARGETS', 8, 15);
    for (let i = 0; i < 6; i++) { const hgt = Math.max(3, 52 - i * 9 + Math.sin(t * 2 + i) * 3); g.fillStyle = i === 5 ? '#ff3030' : '#ffe14d'; g.fillRect(10 + i * 18, 86 - hgt, 12, hgt); }
    g.strokeStyle = '#ff4fd8'; g.lineWidth = 2; g.beginPath(); g.moveTo(10, 30); g.lineTo(118, 90 + Math.sin(t * 3) * 2); g.stroke();
    if (Math.sin(t * 4) > 0) { g.fillStyle = '#ff3030'; g.fillText('☹', 104, 15); }
    scr.needsUpdate = true;
  };
  const st = { y: 0, x: 0 }, turn = {};
  return {
    root, update(dt, now, ctx) {
      const t = now / 1000, k = ctx.near;
      if (t - drawT > 0.2) { drawT = t; drawScreen(t); }
      // spins round in the chair to face you when you walk in
      const want = k > 0.4 && ctx.eye ? wrapA(yawTo(root.position.x, root.position.z, ctx.eye[0], ctx.eye[2]) - root.rotation.y) : Math.sin(t * 0.4) * 0.08;
      turn.y = lerp(turn.y || 0, want, Math.min(1, dt * (k > 0.4 ? 3 : 1.2)));
      swivel.rotation.y = turn.y;
      // slumped. a big sigh every few seconds (shoulders up, then down further)
      const sigh = bump(((t % 7) - 5) / 1.6), atDesk = 1 - Math.min(1, Math.abs(turn.y) * 1.5);
      ch.body.rotation.x = 0.16 * atDesk - sigh * 0.06;
      ch.arm.rotation.x = lerp(-0.95, -0.25, atDesk) + Math.sin(t * 9) * 0.03 * atDesk; // one finger typing at the desk, arms down when he's turned
      ch.armL.rotation.x = lerp(-1.1, -0.35, atDesk) + Math.sin(t * 7.3 + 1) * 0.02 * atDesk;
      st.ox = -0.25 * atDesk - sigh * 0.12; // head down at the screen
      headLook(ch, st, ctx.eye, root.rotation.y + swivel.rotation.y, k, dt, 0.8);
      const g = speak(ch, now, ctx.say); if (g) ch.armL.rotation.x += g * 0.4; // a tired hand gesture
    },
  };
}

// ================================================================ DALE, vending machine guy. behind the Mega-Mart
function vendingMachine() {
  const g = grp(), R = 0xd02030, Rd = 0x9a1424;
  // a hollow cabinet (back, sides, top, base) so you can see in with the door open
  g.add(box(0.95, 1.86, 0.05, R, 0, 0.93, -0.375)); for (const sx of [-1, 1]) g.add(box(0.05, 1.86, 0.8, R, sx * 0.45, 0.93, 0));
  g.add(box(0.97, 0.08, 0.82, Rd, 0, 1.88, 0)); g.add(box(0.95, 0.16, 0.8, 0x222226, 0, 0.08, 0));
  g.add(box(0.88, 1.66, 0.04, 0x1a1a1e, 0, 0.95, -0.36)); // the dark back wall inside
  for (let i = 0; i < 5; i++) { // shelves of cans, lit from the top
    const y = 0.36 + i * 0.29;
    g.add(box(0.84, 0.02, 0.6, 0x8a8f99, 0, y, 0.05));
    for (let j = 0; j < 6; j++) g.add(cyl(0.033, 0.033, 0.12, [0xff2a3a, 0x2a6cff, 0x7dff4f, 0xffe14d, 0xff4fd8][(i + j) % 5], -0.33 + j * 0.13, y + 0.07, 0.25 + (j % 2) * 0.02, 8));
  }
  g.add(box(0.8, 0.03, 0.03, 0xfff8e0, 0, 1.78, 0.36, true)); // the strip light
  // wires hanging out (the repair)
  for (const [x, c, l] of [[-0.2, 0xff4040, 0.4], [-0.15, 0xffe14d, 0.55], [-0.1, 0x40a0ff, 0.35]]) { const w = cyl(0.007, 0.007, l, c, x, 1.78 - l / 2, 0.38, 4); w.rotation.z = 0.15; g.add(w); }
  // the door, swung open on its left hinge: glass front, logo panel, buttons, coin slot, the OUT OF ORDER note
  const hinge = grp(0.475, 0, 0.42); g.add(hinge); // hinged on the side away from him, so the cans show
  const door = grp(-0.475, 0, 0); hinge.add(door);
  door.add(box(0.95, 1.84, 0.06, R, 0, 0.94, 0.0));
  door.add(new THREE.Mesh(new THREE.BoxGeometry(0.62, 1.3, 0.02), new THREE.MeshLambertMaterial({ color: 0x9adfff, transparent: true, opacity: 0.35 }))).position.set(-0.1, 1.05, 0.03);
  const logo = canvasTex(64, 192, (c, w, h) => {
    c.fillStyle = '#ffe14d'; c.fillRect(0, 0, w, h); c.fillStyle = '#d02030'; c.save(); c.translate(w / 2 + 8, h / 2); c.rotate(-Math.PI / 2); c.font = FONT(26); c.textAlign = 'center'; c.fillText('JANK COLA', 0, 0); c.restore();
    c.fillStyle = '#120818'; c.font = FONT(10); c.save(); c.translate(w / 2 + 24, h / 2); c.rotate(-Math.PI / 2); c.textAlign = 'center'; c.fillText('0% water', 0, 0); c.restore();
  });
  const lp = panel(0.2, 0.9, logo); lp.position.set(0.33, 1.25, 0.035); door.add(lp);
  for (let i = 0; i < 6; i++) door.add(box(0.06, 0.04, 0.02, i === 2 ? 0x7dff4f : 0xe8e8e8, 0.33, 0.7 - i * 0.07, 0.04));
  door.add(box(0.05, 0.1, 0.02, 0x222222, 0.33, 0.25, 0.04)); door.add(box(0.5, 0.18, 0.03, 0x1a1a1e, -0.1, 0.22, 0.04)); // coin slot, the flap
  const note = canvasTex(64, 64, (c, w, h) => { c.fillStyle = '#fff8c8'; c.fillRect(0, 0, w, h); c.fillStyle = '#c02030'; c.font = FONT(13); c.textAlign = 'center'; c.fillText('OUT OF', w / 2, 24); c.fillText('ORDER', w / 2, 40); c.fillStyle = '#333'; c.font = FONT(8); c.fillText('since tuesday', w / 2, 56); });
  const np = panel(0.17, 0.17, note); np.position.set(-0.12, 1.3, 0.045); np.rotation.z = 0.12; door.add(np);
  door.add(box(0.06, 0.02, 0.005, 0xd8d0a0, -0.17, 1.39, 0.048)); // tape
  hinge.rotation.y = 1.95;
  g.userData.door = hinge;
  return g;
}
function dale(s) {
  const root = grp();
  const vm = vendingMachine(); vm.position.set(-0.25, 0, -0.74); root.add(vm); // back to the wall, its open front to him
  // toolbox on the ground, lid up, a few tools in it
  const tb = grp(0.6, 0, -0.3); tb.rotation.y = -0.4; root.add(tb);
  tb.add(box(0.46, 0.2, 0.22, 0xd02030, 0, 0.1, 0)); tb.add(box(0.47, 0.025, 0.23, 0x9a1424, 0, 0.2, 0));
  const lid = box(0.46, 0.02, 0.22, 0xd02030, 0, 0.21, 0.11); lid.rotation.x = -1.2; lid.position.set(0, 0.29, 0.15); tb.add(lid);
  tb.add(box(0.2, 0.02, 0.02, 0x222222, 0, 0.26, 0)); tb.add(box(0.02, 0.06, 0.02, 0x222222, -0.1, 0.23, 0)); tb.add(box(0.02, 0.06, 0.02, 0x222222, 0.1, 0.23, 0));
  { const sd = cyl(0.012, 0.012, 0.22, 0xffe14d, 0.1, 0.25, 0.04, 5); sd.rotation.z = 0.6; tb.add(sd); }
  const ch = mannequin('#ff7a1a', { top: 'tee', topColor: '#f4f4f0', bottom: 'overalls', bottomColor: '#2a4a8a', head: 'cap', face: 'mustache', skin: '#8d5524', hair: 'short', hairColor: '#1a1a1a' });
  const body = grp(); root.add(body); body.add(ch.root);
  // name patch on the bib, and a wrench in his hand
  const patch = canvasTex(64, 32, (c, w, h) => { c.fillStyle = '#fff'; c.beginPath(); c.ellipse(w / 2, h / 2, w / 2 - 2, h / 2 - 2, 0, 0, 7); c.fill(); c.strokeStyle = '#c02030'; c.lineWidth = 3; c.stroke(); c.fillStyle = '#c02030'; c.font = FONT(17); c.textAlign = 'center'; c.fillText('Dale', w / 2, 22); });
  const pp = panel(0.1, 0.05, patch); pp.position.set(0.0, 1.27, -0.178); pp.rotation.y = Math.PI; pp.rotation.x = -0.1; ch.body.add(pp);
  const wr = grp(); ch.slot.add(wr); wr.rotation.x = Math.PI / 2;
  wr.add(box(0.03, 0.3, 0.015, 0xb8bcc4, 0, 0.05, 0)); wr.add(box(0.07, 0.05, 0.016, 0xb8bcc4, 0, 0.21, 0)); wr.add(box(0.03, 0.03, 0.02, 0x2a2a2a, 0, 0.23, 0)); wr.add(box(0.034, 0.12, 0.02, 0xc02030, 0, -0.06, 0));
  const st = { y: 0, x: 0 };
  let hitAt = 1.2, shake = 0;
  return {
    root, update(dt, now, ctx) {
      const t = now / 1000, k = ctx.near;
      faceYou(root, body, ctx, k, dt, 2.2);
      const busy = Math.max(0, 1 - Math.abs(body.rotation.y) * 1.2);
      // hits the machine with the wrench every couple of seconds (it shakes, it clanks), peers in between
      if (t > hitAt) { hitAt = t + 1.8 + Math.random() * 1.6; if (busy > 0.8) { shake = 1; if (ctx.dist < 25) sfx.clang(ctx.pos, 0.25); } }
      const sw = Math.max(0, 1 - (hitAt - t) / 0.35);
      shake = Math.max(0, shake - dt * 4);
      vm.rotation.z = Math.sin(t * 60) * 0.012 * shake; vm.position.x = -0.25 + Math.sin(t * 47) * 0.01 * shake;
      vm.userData.door.rotation.y = 1.95 + Math.sin(t * 40) * 0.05 * shake;
      ch.arm.rotation.x = lerp(1.1, lerp(1.6, -0.1, sw), busy); // wrench up, then down onto the machine
      ch.arm.rotation.y = 0.2 * busy;
      ch.armL.rotation.x = lerp(-1.3, 0.2, busy); // leaning on the machine with the other hand
      ch.body.rotation.x = 0.12 * busy;
      st.ox = busy * (0.05 + Math.sin(t * 0.7) * 0.06); st.oy = busy * Math.sin(t * 0.5) * 0.2;
      headLook(ch, st, ctx.eye, root.rotation.y + body.rotation.y, k, dt, 0.9);
      const g = speak(ch, now, ctx.say); if (g) ch.armL.rotation.x = lerp(ch.armL.rotation.x, -0.4, g);
    },
  };
}

// ================================================================ THE JANITOR. deep in the Backrooms pool rooms, mopping a pool
function janitor(s) {
  const root = grp();
  const ch = mannequin('#5a6a7a', { top: 'jacket', topColor: '#56677a', bottom: 'pants', bottomColor: '#56677a', head: 'beanie', face: 'mustache', skin: '#e0ac69' });
  const body = grp(); root.add(body); body.add(ch.root);
  // name tape, a key ring on the belt
  const tape = canvasTex(64, 16, (c, w, h) => { c.fillStyle = '#f4f4ee'; c.fillRect(0, 0, w, h); c.fillStyle = '#1a1a1a'; c.font = FONT(12); c.textAlign = 'center'; c.fillText('JANITOR', w / 2, 13); });
  const tp = panel(0.12, 0.03, tape); tp.position.set(-0.1, 1.42, -0.172); tp.rotation.y = Math.PI; ch.body.add(tp);
  const keys = grp(0.17, 1.0, -0.06); ch.body.add(keys);
  keys.add(new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.005, 4, 10), M(0xc8ccd4)));
  for (let i = 0; i < 4; i++) { const kk = box(0.01, 0.05, 0.004, 0xd8c070, Math.cos(i) * 0.02, -0.04, Math.sin(i) * 0.01); kk.rotation.z = (i - 1.5) * 0.3; keys.add(kk); }
  // the mop: a long handle in both hands down to the floor, a head of grey strings
  const mop = grp(); ch.slot.add(mop);
  const handle = cyl(0.016, 0.016, 1.5, 0xc8a070, 0, 0, 0, 6); handle.rotation.x = Math.PI / 2; handle.position.z = -0.2; mop.add(handle);
  const head = grp(0, 0, -0.95); mop.add(head);
  head.add(box(0.12, 0.05, 0.05, 0x3a6a9a, 0, 0, 0));
  for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2, sr = box(0.022, 0.22, 0.022, 0xb8b4a8, Math.cos(a) * 0.05, -0.05, Math.sin(a) * 0.04 - 0.11); sr.rotation.x = -1.2 + Math.sin(i * 3) * 0.2; sr.rotation.z = Math.cos(a) * 0.4; head.add(sr); }
  mop.rotation.x = -0.95; // the handle slants down to the floor in front of him
  // a yellow mop bucket on castors with the wringer, and the sign
  const bk = grp(0.75, 0, -0.4); bk.rotation.y = -0.4; root.add(bk);
  bk.add(box(0.42, 0.34, 0.32, 0xffd21a, 0, 0.24, 0)); bk.add(box(0.38, 0.02, 0.28, 0x6a8a9a, 0, 0.38, 0)); // dirty water
  bk.add(box(0.2, 0.22, 0.3, 0x5a5a62, 0.12, 0.5, 0)); bk.add(box(0.03, 0.4, 0.03, 0x5a5a62, 0.24, 0.62, 0.0));
  for (const [x, z] of [[-0.17, -0.12], [0.17, -0.12], [-0.17, 0.12], [0.17, 0.12]]) bk.add(sph(0.035, 0x222222, x, 0.035, z));
  const sign = grp(-0.8, 0, -0.9); sign.rotation.y = 0.5; root.add(sign);
  const signT = canvasTex(96, 128, (c, w, h) => {
    c.fillStyle = '#ffd21a'; c.fillRect(0, 0, w, h); c.fillStyle = '#120818'; c.textAlign = 'center';
    c.font = FONT(16); c.fillText('CAUTION', w / 2, 24); c.beginPath(); c.moveTo(w / 2, 34); c.lineTo(w / 2 + 22, 72); c.lineTo(w / 2 - 22, 72); c.closePath(); c.lineWidth = 4; c.stroke();
    c.font = FONT(26); c.fillText('!', w / 2, 68); c.font = FONT(13); c.fillText('REALITY', w / 2, 96); c.fillText('IS WET', w / 2, 112);
  });
  for (const sz of [-1, 1]) { const pnl = panel(0.32, 0.6, signT); pnl.position.set(0, 0.29, sz * 0.09); pnl.rotation.x = sz * -0.28; if (sz > 0) pnl.rotation.y = Math.PI; pnl.material.side = THREE.DoubleSide; sign.add(pnl); }
  const st = { y: 0, x: 0 };
  return {
    root, update(dt, now, ctx) {
      const t = now / 1000, k = ctx.near;
      faceYou(root, body, ctx, k, dt, 1.0); // turns round slowly
      // mopping: a slow figure eight on the floor. every 14 s he stops and stares at a wall for a while
      const cyc = t % 14, stare = cyc > 10 ? bump((cyc - 10) / 4) : 0, work = (1 - stare) * (1 - Math.min(1, k * 1.4));
      const sw = Math.sin(t * 1.6);
      mop.rotation.y = sw * 0.45 * work; mop.rotation.x = -0.95 + Math.sin(t * 3.2) * 0.06 * work;
      ch.body.rotation.y = sw * 0.12 * work;
      ch.arm.rotation.x = -0.55 + Math.sin(t * 3.2) * 0.05 * work; ch.arm.rotation.y = sw * 0.2 * work;
      ch.armL.rotation.x = -0.45; ch.armL.rotation.y = 0.35 + sw * 0.15 * work;
      st.oy = stare * 1.1; st.ox = -0.05 * work - 0.02;
      headLook(ch, st, ctx.eye, root.rotation.y + body.rotation.y, k, dt, 1.2);
      speak(ch, now, ctx.say, 0.5); // he doesn't move much when he talks
    },
  };
}

// ================================================================ MR. SMILES (retired). sitting on a crane's hook block over Skyline
function smiles(s) {
  const root = grp();
  const Y = '#ffd21a';
  const ch = mannequin(Y, { top: 'hoodie', topColor: Y, bottom: 'pants', bottomColor: Y, skin: Y });
  root.add(ch.root); SIT(ch, 0.0);
  ch.legL.rotation.x = ch.legR.rotation.x = 1.35; // thighs out over the edge
  // the mascot head: a big glossy yellow ball with the ☺ face painted on, a seam, a little air vent on top
  for (const c of ch.head.children.slice()) c.visible = false;
  const face = canvasTex(256, 128, (c, w, h) => {
    c.fillStyle = '#ffd21a'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#120818';
    for (const x of [w * 0.4, w * 0.6]) { c.beginPath(); c.ellipse(x, h * 0.4, 9, 17, 0, 0, 7); c.fill(); }
    c.fillStyle = '#fff'; for (const x of [w * 0.4, w * 0.6]) { c.beginPath(); c.arc(x - 3, h * 0.33, 3.5, 0, 7); c.fill(); }
    c.strokeStyle = '#120818'; c.lineWidth = 9; c.lineCap = 'round'; c.beginPath(); c.arc(w / 2, h * 0.5, 34, 0.2 * Math.PI, 0.8 * Math.PI); c.stroke();
    c.fillStyle = '#ff9ad5'; for (const x of [w * 0.32, w * 0.68]) { c.globalAlpha = 0.6; c.beginPath(); c.ellipse(x, h * 0.6, 12, 7, 0, 0, 7); c.fill(); } c.globalAlpha = 1;
    c.fillStyle = '#c8a010'; c.fillRect(0, h * 0.96, w, h * 0.04);
  });
  const big = new THREE.Mesh(new THREE.SphereGeometry(0.33, 18, 12), new THREE.MeshLambertMaterial({ map: face }));
  big.rotation.y = Math.PI / 2; // the face (the middle of the texture) to the front (-z)
  big.position.set(0, 0.17, 0); ch.head.add(big);
  ch.head.add(cyl(0.12, 0.14, 0.06, 0xc8a010, 0, -0.14, 0, 12)); // the collar ring
  ch.head.add(cyl(0.03, 0.03, 0.02, 0x8a7010, 0, 0.5, 0, 8)); // air vent
  // smiley patch on the belly, giant gloves, giant red shoes
  const pt = canvasTex(64, 64, (c, w, h) => { c.fillStyle = '#ffffff'; c.beginPath(); c.arc(32, 32, 30, 0, 7); c.fill(); c.font = FONT(44); c.fillStyle = '#ff4fd8'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('☺', 32, 34); });
  const pp = panel(0.16, 0.16, pt); pp.position.set(0, 1.28, -0.19); pp.rotation.y = Math.PI; ch.body.add(pp);
  const gl = (p, x, y, z) => { const g2 = sph(0.075, 0xffffff, x, y, z, 9, 7); g2.scale.set(1, 0.9, 1.15); p.add(g2); for (let i = 0; i < 3; i++) p.add(box(0.012, 0.03, 0.002, 0xc8c8c8, x - 0.02 + i * 0.02, y + 0.03, z - 0.08)); return g2; };
  gl(ch.arm, -0.04, -0.02, -0.57); gl(ch.armL, 0.38, -0.05, -0.53);
  for (const kn of [ch.kneeL, ch.kneeR]) { const sh = sph(0.1, 0xe02030, 0, -0.44, -0.1, 9, 6); sh.scale.set(0.9, 0.6, 1.45); kn.add(sh); }
  // the balloons: three ☺ balloons tied to his left hand on strings, bobbing in the wind
  const balloons = [];
  for (const [c, dx, dz, h] of [[0xff4fd8, -0.25, 0.1, 1.6], [0x4fd8ff, 0.05, 0.3, 1.85], [0x7dff4f, 0.3, 0.05, 1.5]]) {
    const b = grp(); root.add(b);
    const ball = sph(0.2, c, 0, 0, 0, 12, 9); ball.scale.set(1, 1.18, 1); b.add(ball); b.add(box(0.035, 0.035, 0.035, c, 0, -0.24, 0));
    const string = cyl(0.003, 0.003, 1, 0xffffff, 0, 0, 0, 3); root.add(string);
    balloons.push({ b, dx, dz, h, ph: Math.random() * 6, string });
  }
  const st = { y: 0, x: 0 };
  const hand = new THREE.Vector3(), tmp = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  return {
    root, update(dt, now, ctx) {
      const t = now / 1000, k = ctx.near;
      // legs kick slowly over the drop, one then the other
      ch.kneeL.rotation.x = -1.4 + Math.sin(t * 1.3) * 0.3; ch.kneeR.rotation.x = -1.4 + Math.sin(t * 1.3 + 2.2) * 0.3;
      // a slow sad sway; leans back on his right hand
      ch.body.rotation.z = Math.sin(t * 0.6) * 0.04;
      ch.arm.rotation.x = -1.3; ch.arm.rotation.z = 0.25;
      // waves when you're close (a big mascot wave with the right hand), otherwise holds the balloons up
      const wave = k > 0.5 ? 1 : 0;
      ch.arm.rotation.x = lerp(-1.3, 2.6, wave); ch.arm.rotation.z = lerp(0.25, -0.2 + Math.sin(t * 9) * 0.35, wave);
      ch.armL.rotation.x = 0.25 + Math.sin(t * 0.8) * 0.05;
      st.oy = Math.sin(t * 0.35) * 0.35 * (1 - k); st.ox = -0.25 * (1 - k) + Math.sin(t * 0.9) * 0.05; // looking down at the city
      headLook(ch, st, ctx.eye, root.rotation.y, k, dt, 1.0);
      ch.head.rotation.z = Math.sin(t * 0.7) * 0.12; // the head tilt
      speak(ch, now, ctx.say, 1.5);
      // balloons follow his left hand (their strings from his glove to each balloon)
      root.updateMatrixWorld(true);
      ch.armL.localToWorld(hand.set(0.38, -0.05, -0.53)); root.worldToLocal(hand);
      for (const B of balloons) {
        const bx2 = hand.x + B.dx + Math.sin(t * 0.9 + B.ph) * 0.12, by2 = hand.y + B.h + Math.sin(t * 1.3 + B.ph) * 0.06, bz2 = hand.z + B.dz + Math.cos(t * 0.7 + B.ph) * 0.12;
        B.b.position.set(bx2, by2, bz2); B.b.rotation.z = Math.sin(t + B.ph) * 0.15;
        tmp.set(bx2 - hand.x, by2 - 0.24 - hand.y, bz2 - hand.z); const len = tmp.length();
        B.string.position.set(hand.x + tmp.x / 2, hand.y + tmp.y / 2, hand.z + tmp.z / 2); B.string.scale.y = len;
        B.string.quaternion.setFromUnitVectors(up, tmp.normalize());
      }
    },
  };
}

// ================================================================ TODD, intern (year 40). up in the Islands wreck's crow's nest, on a missing-texture patch
function todd(s) {
  const root = grp();
  // an upturned crate to sit on, a stack of binders with the laptop on it, a coffee pot, crumpled paper
  root.add(box(0.46, 0.42, 0.42, 0xb8874a, 0, 0.21, 0.05)); root.add(box(0.47, 0.03, 0.43, 0x9a6c36, 0, 0.41, 0.05));
  const desk = grp(0.12, 0, -0.95); root.add(desk);
  for (let i = 0; i < 4; i++) { const b = box(0.36, 0.13, 0.28, [0x2a6cff, 0xc02030, 0x3a8a3a, 0xffd21a][i], 0, 0.065 + i * 0.13, 0); b.rotation.y = (i % 2 ? 1 : -1) * 0.06; desk.add(b); }
  const lap = grp(0, 0.52, 0); desk.add(lap);
  lap.add(box(0.34, 0.02, 0.24, 0x30323a, 0, 0.01, 0));
  const scr = canvasTex(128, 80, () => {});
  const lid = grp(0, 0.02, -0.12); lid.rotation.x = 0.35; lap.add(lid);
  lid.add(box(0.34, 0.22, 0.015, 0x30323a, 0, 0.11, 0));
  const sp = panel(0.31, 0.19, scr, true); sp.position.set(0, 0.11, 0.009); lid.add(sp);
  desk.add(cyl(0.06, 0.06, 0.16, 0x3a3a3a, 0.4, 0.08, 0.1, 10)); desk.add(cyl(0.055, 0.055, 0.1, 0x3a1a08, 0.4, 0.06, 0.1, 10));
  desk.add(box(0.03, 0.08, 0.02, 0x1a1a1a, 0.47, 0.1, 0.1));
  for (let i = 0; i < 6; i++) { const p = new THREE.Mesh(new THREE.IcosahedronGeometry(0.045, 0), M(0xf4f4ee)); p.position.set(-0.5 + Math.sin(i * 2.1) * 0.35, 0.04, 0.25 + Math.cos(i * 1.7) * 0.3); p.rotation.set(i, i * 2, 0); root.add(p); }
  // the bug he's patching: a floating purple and black checker cube, glitching
  const chk = canvasTex(32, 32, (c) => { for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { c.fillStyle = (x + y) % 2 ? '#000' : '#ff00dc'; c.fillRect(x * 8, y * 8, 8, 8); } });
  chk.magFilter = THREE.NearestFilter;
  const bug = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.32, 0.32), new THREE.MeshBasicMaterial({ map: chk })); bug.position.set(0.85, 1.25, -0.25); root.add(bug);
  const ch = mannequin('#ffffff', { top: 'tee', topColor: '#f4f4f0', bottom: 'pants', bottomColor: '#2a4a8a', hair: 'long', hairColor: '#e8e4dc', face: 'bigglasses', skin: '#ffdbac' });
  root.add(ch.root); SIT(ch, 0.44);
  // forty years of beard: a long white wedge from the chin down to the belly, a moustache over it
  const beard = grp(0, 0.06, -0.09); ch.head.add(beard);
  for (let i = 0; i < 5; i++) { const w = 0.2 - i * 0.03, b = box(w, 0.1, 0.09 - i * 0.008, i % 2 ? 0xe8e4dc : 0xf4f2ee, 0, -0.03 - i * 0.085, -0.01 - i * 0.012); b.rotation.x = 0.18; beard.add(b); }
  beard.add(box(0.15, 0.03, 0.05, 0xe8e4dc, 0, 0.03, -0.05));
  // the lanyard round his neck, the INTERN badge at the end of it
  const badge = canvasTex(64, 96, (c, w, h) => {
    c.fillStyle = '#fff'; c.fillRect(0, 0, w, h); c.fillStyle = '#ff4fd8'; c.fillRect(0, 0, w, 20); c.fillStyle = '#fff'; c.font = FONT(12); c.textAlign = 'center'; c.fillText('☺ CORP', w / 2, 15);
    c.fillStyle = '#c8c8d0'; c.fillRect(16, 26, 32, 32); c.fillStyle = '#7a7a80'; c.beginPath(); c.arc(32, 38, 8, 0, 7); c.fill(); c.fillRect(22, 48, 20, 10);
    c.fillStyle = '#120818'; c.font = FONT(14); c.fillText('INTERN', w / 2, 76); c.font = FONT(9); c.fillText('since 1986', w / 2, 90);
  });
  const bd = panel(0.07, 0.105, badge); bd.position.set(0.03, 1.12, -0.2); bd.rotation.y = Math.PI; bd.rotation.x = -0.15; ch.body.add(bd);
  for (const sx of [-1, 1]) { const ln = box(0.015, 0.4, 0.008, 0xff2a3a, sx * 0.06 + 0.015, 1.36, -0.185); ln.rotation.z = sx * 0.2; ln.rotation.x = -0.1; ch.body.add(ln); }
  let drawT = 0, line = 0;
  const drawScreen = (t) => {
    const c = scr.userData.canvas, g = c.getContext('2d');
    g.fillStyle = '#0a0a14'; g.fillRect(0, 0, 128, 80); g.font = '9px monospace';
    const L = ['gravity = 26 // ish', 'if (floor) slip()', 'banana.code = floor.code', 'stop() // TODO buy', 'momentum += momentum', 'texture = hope', 'knee.angle = wrong'];
    for (let i = 0; i < 7; i++) { g.fillStyle = i === 6 ? '#ff4fd8' : '#7dff4f'; g.fillText(L[(line + i) % L.length], 4, 11 + i * 10); }
    if (Math.sin(t * 6) > 0) { g.fillStyle = '#7dff4f'; g.fillRect(4, 72, 5, 2); }
    scr.needsUpdate = true;
  };
  const st = { y: 0, x: 0 };
  return {
    root, update(dt, now, ctx) {
      const t = now / 1000, k = ctx.near;
      if (t - drawT > 0.35) { drawT = t; line++; drawScreen(t); }
      bug.rotation.set(t * 0.7, t * 1.1, 0); bug.position.y = 1.25 + Math.sin(t * 1.7) * 0.05;
      bug.scale.setScalar(Math.random() < 0.04 ? 1.3 : 1); // glitch
      // typing like his life depends on it; every so often he strokes the beard and looks at the bug
      const cyc = t % 9, think = cyc > 6.5 ? bump((cyc - 6.5) / 2.5) : 0, type = (1 - think) * (1 - Math.min(1, k * 1.5));
      ch.arm.rotation.x = lerp(-0.6, -0.35 + Math.sin(t * 22) * 0.06, type); ch.armL.rotation.x = lerp(-0.6, -0.4 + Math.sin(t * 19 + 1) * 0.06, type);
      ch.armL.rotation.x = lerp(ch.armL.rotation.x, 1.2, think); // hand up to the beard
      ch.body.rotation.x = 0.2 * type;
      st.ox = -0.3 * type + 0.1 * think; st.oy = think * 0.8;
      // a wave when you get close (he's so happy someone came)
      const wv = k > 0.5 ? 1 : 0;
      ch.arm.rotation.x = lerp(ch.arm.rotation.x, 2.5, wv); ch.arm.rotation.z = lerp(0, Math.sin(t * 10) * 0.4, wv);
      headLook(ch, st, ctx.eye, root.rotation.y, k, dt, 1.0);
      speak(ch, now, ctx.say, 1.2);
    },
  };
}

const BUILD = { gary, dale, janitor, smiles, todd };
export function buildNpc(s) { return (BUILD[s.look] || gary)(s); }
