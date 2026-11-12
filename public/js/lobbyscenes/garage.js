// BATTLE ISLAND's lobby: the mech garage (docs/menu/LOBBY_SCENES.md), and you walk around in it. a big hangar: three
// bays (squads of 3) along the back, your mech in the middle one in its gantry, your squad's in theirs. your mech is the
// loadout's MECH DROP FRAME (the server's hero ask for Battle Island), so the bay terminal, the < > plate and CUSTOMIZE
// all change the same thing: the crane swaps it, with juice. hop in (E at its feet) and stomp round the fenced test pad,
// hop out and it flies home. a break room with a cola machine, a test-fire range, the hangar door open on the island.
import * as THREE from 'three';
import { buildMech, freeMech, poseMech, GLB_ID } from '../mechmodel.js';
import { MECH, FRAMES, mechFrame } from '/shared/mech.js';
import { missingGlb, want, whenGlb } from '../glbkit.js';
import { freeTree } from '../models.js';

const BAY = 9.5, MZ = -9; // bay spacing, where the mechs stand
const SWAP = 1.6, UP = 8.5; // s, the whole swap; how high the crane hauls (just out of the picture, behind the headers)
const myFrame = (G) => mechFrame(G.settings && G.settings.loadout && G.settings.loadout.mech);

export function build(L) {
  const { G } = L, S = L.cur().scene, root = new THREE.Group(); S.add(root);
  S.background = new THREE.Color(0x9aa8e0);
  S.fog = new THREE.Fog(0x4a3a5a, 40, 260);
  const potato = L.potato();
  // ---- the room: concrete, ribbed walls, a roof with trusses, the big door at the front (open), the apron outside
  const conc = L.mat(0x6a6670, 0.82); conc.map = L.speck(0x6a6670, 16);
  const floor = L.box(root, 50, 0.2, 50, conc, 0, -0.1, 8); floor.castShadow = false;
  const wall = L.mat(0x1d1824, 0.9); wall.map = L.speck(0x2a2433, 6, true);
  const steel = L.mat(0x2a2c34, 0.42, 0.75), yel = L.mat(0xd9a21a, 0.42, 0.25), dark = L.mat(0x15131a, 0.6, 0.4);
  const flat = (o) => { o.castShadow = false; return o; };
  flat(L.box(root, 50, 17, 0.5, wall, 0, 8.5, -16.25));
  for (const sx of [-1, 1]) flat(L.box(root, 0.5, 17, 38.5, wall, sx * 24.25, 8.5, 3));
  for (const sx of [-1, 1]) flat(L.box(root, 13.5, 17, 0.5, wall, sx * 17.75, 8.5, 22.25)); // the front wall either side of the door
  flat(L.box(root, 22, 5, 0.5, wall, 0, 14.5, 22.25)); // over the door
  flat(L.box(root, 50, 0.4, 38.5, L.mat(0x120e18, 0.9), 0, 17.2, 3)); // the roof
  for (let z = -12; z <= 20; z += 8) flat(L.box(root, 48, 0.6, 0.4, steel, 0, 16.4, z)); // trusses
  for (let i = -3; i <= 3; i++) flat(L.box(root, 0.35, 16, 0.6, steel, i * 7, 8, -15.8)); // wall ribs
  for (const sx of [-1, 1]) for (let z = -10; z <= 18; z += 7) flat(L.box(root, 0.6, 16, 0.35, steel, sx * 23.8, 8, z));
  const tape = L.mat(0xffffff, 0.6); tape.map = L.stripes(40);
  for (const z of [-3.9, -14.4]) flat(L.box(root, 34, 0.02, 0.35, tape, 0, 0.012, z));
  // the door: two big panels slid open into the wall, hazard edges, the opening's frame
  const doorM = L.mat(0x3a3e4a, 0.5, 0.6); doorM.map = L.speck(0x3a3e4a, 4, true);
  for (const sx of [-1, 1]) { flat(L.box(root, 6.2, 12, 0.4, doorM, sx * 14.2, 6, 21.6)); const e = L.box(root, 0.3, 12, 0.45, tape, sx * 11.25, 6, 21.6); e.castShadow = false; }
  flat(L.box(root, 22.4, 0.5, 0.7, yel, 0, 12.1, 22.1));
  // outside: the apron, a barrier, the sea and the island, a lot of sky
  const sky = new THREE.Mesh(new THREE.SphereGeometry(400, 16, 10), L.tex(new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    vertexShader: 'varying vec3 p; void main(){ p = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'varying vec3 p; void main(){ float h = normalize(p).y; vec3 lo = vec3(1.0, 0.62, 0.78), hi = vec3(0.32, 0.55, 1.0); gl_FragColor = vec4(mix(lo, hi, smoothstep(-0.05, 0.45, h)), 1.0); }' })));
  sky.userData.lsSee = true; root.add(sky);
  const apron = L.mat(0x4a4850, 0.9); apron.map = L.speck(0x4a4850, 10);
  flat(L.box(root, 60, 0.2, 30, apron, 0, -0.12, 37));
  for (let x = -22; x <= 22; x += 4) L.box(root, 3.6, 0.9, 0.5, tape, x, 0.45, 32.6);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(900, 900), L.mat(0x2b86d8, 0.25, 0.1)); sea.rotation.x = -Math.PI / 2; sea.position.set(0, -2, 300); root.add(sea);
  const isle = new THREE.Mesh(new THREE.ConeGeometry(70, 26, 9), L.mat(0x58c24a, 0.9)); isle.position.set(-60, 8, 260); root.add(isle);
  const peak = new THREE.Mesh(new THREE.ConeGeometry(26, 34, 6), L.mat(0x7a6a8a, 0.9)); peak.position.set(-72, 26, 270); root.add(peak);
  const sand = new THREE.Mesh(new THREE.CylinderGeometry(78, 82, 3, 9), L.mat(0xf2dc9a, 0.9)); sand.position.set(-60, -1.5, 260); root.add(sand);
  // the sign: DAYS WITHOUT A MECH ON FIRE
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 1.05), L.basic(0xffffff, { map: L.label('DAYS WITHOUT A MECH ON FIRE: 0', { w: 512, h: 128 }) }));
  sign.position.set(-16, 6.4, -15.95); root.add(sign);
  // ---- three bays: a floor plate with a glowing ring, the gantry (Blender model, boxes until it lands), a lamp, a number
  const bays = [-BAY, 0, BAY].map((x, i) => {
    const b = { i, x, g: new THREE.Group(), mech: null, frame: null, want: null, lamp: null, ring: null, num: null, holo: null };
    b.g.position.set(x, 0, MZ); root.add(b.g);
    const plate = L.box(b.g, 6.4, 0.06, 5.2, dark, 0, 0.03, 0); plate.castShadow = false;
    const rm = L.basic(i === 1 ? 0xff4fd8 : 0x4fd8ff, { transparent: true, opacity: 0.85 });
    b.ring = new THREE.Mesh(new THREE.RingGeometry(2.05, 2.3, 8), rm); b.ring.rotation.x = -Math.PI / 2; b.ring.position.y = 0.07; b.g.add(b.ring);
    const gan = new THREE.Group(); b.g.add(gan); b.gantry = gan;
    codeGantry(L, gan, { steel, yel, dark });
    b.arms = ['arm_L', 'arm_R'].map((n) => gan.getObjectByName(n)); b.beacons = [gan.getObjectByName('beacon_L'), gan.getObjectByName('beacon_R')];
    L.glb('x_lobby_gantry', (o) => { freeTree(gan); gan.clear(); gan.add(o); o.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); b.arms = ['arm_L', 'arm_R'].map((n) => o.getObjectByName(n)).filter(Boolean); b.blender = true; b.beacons = []; o.traverse((m) => { if (/beacon/i.test(m.name) && m.isMesh) b.beacons.push(m); }); });
    const nm = L.label('BAY 0' + (i + 1), { w: 256, h: 64 });
    b.num = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.375), L.basic(0xffffff, { map: nm })); b.num.position.set(0, 9.25, 1.32); b.g.add(b.num);
    b.lamp = new THREE.SpotLight(i === 1 ? 0xffe8f6 : 0xbfe6ff, i === 1 ? 420 : 260, 26, 0.5, 0.65, 1.5);
    b.lamp.position.set(x, 13.2, MZ + 4.5); b.lamp.target.position.set(x, 1.5, MZ); root.add(b.lamp, b.lamp.target);
    b.lampBase = b.lamp.color.clone(); b.lampI = b.lamp.intensity;
    L.cyl(root, 0.32, 0.42, 0.45, L.mat(0x111111, 0.4, 0.7), x, 13.4, MZ + 4.5, 8);
    return b;
  });
  // ---- the crane: a rail over all three bays, a trolley, a cable and a hook block (they move during a swap)
  L.box(root, 30, 0.45, 0.55, steel, 0, 13.0, MZ);
  const trolley = new THREE.Group(); trolley.position.set(0, 12.6, MZ); root.add(trolley);
  L.box(trolley, 1.4, 0.55, 1.0, yel, 0, 0, 0);
  const cable = L.cyl(trolley, 0.035, 0.035, 1, steel, 0, 0, 0, 6); cable.castShadow = false;
  const hook = new THREE.Group(); trolley.add(hook);
  L.box(hook, 0.9, 0.55, 0.7, yel, 0, 0, 0); L.box(hook, 0.16, 0.6, 0.16, steel, 0, -0.5, 0);
  const crane = { trolley, cable, hook, y: -1.2 }; // hook height under the trolley
  // ---- solid things you bump into (walk.js): [x0, z0, x1, z1, top]. tops under ~1.6 m can be jumped onto
  const SOL = [], solid = (x0, z0, x1, z1, top = 99) => { SOL.push([x0, z0, x1, z1, top]); };
  solid(-24.5, 21.8, -11, 22.6); solid(11, 21.8, 24.5, 22.6); // the front wall either side of the door
  for (const b of [-BAY, 0, BAY]) { for (const sx of [-3.4, 3.4]) solid(b + sx - 0.55, MZ - 1.45, b + sx + 0.55, MZ + 1.45); solid(b - 3.8, MZ + 1.3, b - 3.0, MZ + 2.1); solid(b - 1.5, MZ - 1.4, b + 1.5, MZ + 1.3); } // towers, ladders, the mechs
  solid(-24.5, 32.3, 24.5, 32.9, 0.9); // the apron barrier (hop it? no: it's the edge of the world)
  // ---- props: crates (Blender, boxes until they land), a tool cart, barrels
  const wood = L.mat(0x7a5530, 0.8);
  const prop = (id, at, fb) => { const g = new THREE.Group(); g.position.set(at[0], 0, at[1]); g.rotation.y = at[2] || 0; root.add(g); if (fb) fb(g); L.glb(id, (o) => { const l1 = o.getObjectByName('lod1'); if (l1) l1.visible = false; o.traverse((m) => { if (m.isMesh) m.castShadow = m.receiveShadow = true; }); if (fb) { freeTree(g); g.clear(); } g.add(o); }); return g; };
  for (const [x, z, r, y] of [[-14.5, -6.5, 0.2, 0], [-13.2, -6.2, -0.1, 0], [-14, -6.4, 0.5, 1.2], [14.6, -5.8, 0.3, 0]]) {
    const g = prop('p_crate', [x, z, r], (g) => L.box(g, 1.2, 1.2, 1.2, wood, 0, 0.6, 0)); g.position.y = y; solid(x - 0.65, z - 0.65, x + 0.65, z + 0.65, y + 1.2);
  }
  L.box(root, 1.5, 0.95, 0.75, L.mat(0xc8202a, 0.35, 0.3), 5.2, 0.48, -4.6, -0.3); L.box(root, 1.4, 0.07, 0.65, steel, 5.2, 0.99, -4.6, -0.3); solid(4.4, -5.1, 6, -4.1, 1.0); // a tool cart
  for (const [x, z] of [[16.2, -7.2], [17, -6.4], [-17.5, -7.5]]) { prop('p_barrel', [x, z]); solid(x - 0.4, z - 0.4, x + 0.4, z + 0.4, 1.0); }
  // ---- the test pad: a fenced square out front, a gap at the back to walk (or stomp) in
  const pad = L.mat(0x26222e, 0.7); const padT = L.box(root, 14, 0.04, 12, pad, 0, 0.02, 10); padT.castShadow = false;
  const lineM = L.basic(0xffe14d);
  for (const [w, d, x, z] of [[14, 0.18, 0, 4.1], [14, 0.18, 0, 15.9], [0.18, 12, -6.9, 10], [0.18, 12, 6.9, 10]]) flat(L.box(root, w, 0.02, d, lineM, x, 0.05, z));
  const cross = L.mat(0xffffff, 0.6); cross.map = L.label('TEST PAD · STOMP RESPONSIBLY', { bg: '#26222e', fg: '#ffe14d', border: null, w: 512, h: 64 }); flat(L.box(root, 8, 0.02, 1, cross, 0, 0.05, 15));
  const fence = (x0, z0, x1, z1) => { const n = Math.max(1, Math.round(Math.hypot(x1 - x0, z1 - z0) / 2)); for (let i = 0; i <= n; i++) L.box(root, 0.12, 1.1, 0.12, yel, x0 + (x1 - x0) * i / n, 0.55, z0 + (z1 - z0) * i / n); const l = L.box(root, Math.abs(x1 - x0) + 0.1, 0.08, Math.abs(z1 - z0) + 0.1, yel, (x0 + x1) / 2, 1.05, (z0 + z1) / 2); l.castShadow = false; L.box(root, Math.abs(x1 - x0) + 0.1, 0.06, Math.abs(z1 - z0) + 0.1, yel, (x0 + x1) / 2, 0.55, (z0 + z1) / 2).castShadow = false; solid(Math.min(x0, x1) - 0.1, Math.min(z0, z1) - 0.1, Math.max(x0, x1) + 0.1, Math.max(z0, z1) + 0.1, 1.1); };
  fence(-7.2, 3.8, -7.2, 16.2); fence(7.2, 3.8, 7.2, 16.2); fence(-7.2, 16.2, 7.2, 16.2); fence(-7.2, 3.8, -3, 3.8); fence(3, 3.8, 7.2, 3.8);
  // ---- the bay terminal: a pedestal with a screen. E: SWAP MECH
  const term = new THREE.Group(); term.position.set(2.6, 0, MZ + 2.7); term.rotation.y = -0.4; root.add(term);
  L.box(term, 0.5, 1.0, 0.4, steel, 0, 0.5, 0); L.box(term, 0.8, 0.06, 0.5, yel, 0, 1.02, 0);
  const scr = L.box(term, 0.72, 0.46, 0.06, L.basic(0xffffff, { map: L.label('SWAP >', { bg: '#120818', fg: '#4fd8ff', border: '#ff4fd8', w: 128, h: 80 }) }), 0, 1.3, 0.08); scr.rotation.x = -0.35;
  solid(2.25, MZ + 2.35, 2.95, MZ + 3.05, 1.05);
  // ---- the break room (front left): the cola machine, a table, a couch, the coffee, a sign
  const brk = L.mat(0x3a2a4a, 0.8);
  flat(L.box(root, 8.5, 0.03, 9, L.mat(0x5a3a2a, 0.7), -19.5, 0.02, 16)); // (a rug, of sorts)
  prop('p_vending', [-23.2, 13, Math.PI / 2], (g) => L.box(g, 1.2, 2, 0.9, L.mat(0xd0202a, 0.4), 0, 1, 0)); solid(-24, 12.4, -22.6, 13.6, 2);
  L.box(root, 1.6, 0.08, 1, L.mat(0xe8e0d0, 0.5), -19, 0.78, 16.5); L.box(root, 0.1, 0.74, 0.1, steel, -19, 0.37, 16.5); solid(-19.8, 16, -18.2, 17, 0.82);
  for (const dx of [-1.2, 1.2]) { L.box(root, 0.5, 0.06, 0.5, L.mat(0xff4fd8, 0.4), -19 + dx, 0.48, 16.5); L.box(root, 0.06, 0.48, 0.06, steel, -19 + dx, 0.24, 16.5); }
  L.box(root, 3.2, 0.5, 1.0, brk, -22.8, 0.45, 18.6, Math.PI / 2); L.box(root, 3.2, 0.7, 0.3, brk, -23.3, 0.9, 18.6, Math.PI / 2); solid(-23.6, 17, -22.2, 20.2, 0.7); // the couch
  L.box(root, 1.6, 1, 0.6, steel, -15.6, 0.5, 21.2); L.box(root, 0.35, 0.45, 0.3, L.mat(0x111111, 0.3, 0.5), -15.9, 1.22, 21.2); solid(-16.4, 20.9, -14.8, 21.6, 1.0); // counter + coffee
  const bs = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 0.85), L.basic(0xffffff, { map: L.label('BREAK ROOM · NO MECHS', { w: 512, h: 128 }) })); bs.position.set(-23.95, 4, 16.5); bs.rotation.y = Math.PI / 2; root.add(bs);
  // ---- the test-fire range (front right): a counter, three targets on the wall
  L.box(root, 0.8, 1.05, 8, L.mat(0x4a3a2a, 0.7), 16, 0.52, 15); solid(15.6, 11, 16.4, 19, 1.05);
  const targets = [11.5, 15, 18.5].map((z) => { const t = new THREE.Group(); t.position.set(23.6, 1.6, z); root.add(t); L.cyl(t, 0.07, 0.07, 1.6, steel, 0, -0.8, 0, 6); const face = new THREE.Group(); t.add(face);
    for (const [r, c] of [[0.55, 0xffffff], [0.42, 0xff3030], [0.28, 0xffffff], [0.14, 0xff3030]]) { const d = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.06 + (0.55 - r) * 0.05, 16), L.mat(c, 0.5)); d.rotation.z = Math.PI / 2; face.add(d); }
    return { g: t, face, spin: 0 }; });
  const rs = new THREE.Mesh(new THREE.PlaneGeometry(3, 0.75), L.basic(0xffffff, { map: L.label('TEST FIRE · E', { w: 512, h: 128 }) })); rs.position.set(23.95, 4, 15); rs.rotation.y = -Math.PI / 2; root.add(rs);
  // ---- lights: a dim purple room, a key from the front, the bay lamps, a cyan kicker
  S.add(new THREE.HemisphereLight(0x9a88c0, 0x1a1020, 0.9));
  const key = new THREE.DirectionalLight(0xffe6f4, 1.25); key.position.set(-6, 14, 16); key.target.position.set(0, 0, 0); S.add(key, key.target);
  if (L.shadows()) { key.castShadow = true; key.shadow.mapSize.set(potato ? 512 : 2048, potato ? 512 : 2048); Object.assign(key.shadow.camera, { left: -26, right: 26, top: 24, bottom: -20, near: 1, far: 60 }); key.shadow.bias = -0.0005; key.shadow.normalBias = 0.03; }
  const kick = new THREE.PointLight(0x4fd8ff, 40, 18); kick.position.set(16, 4, 14); S.add(kick); // (the range)
  const pk = new THREE.PointLight(0xff4fd8, 40, 18); pk.position.set(-18, 4, 15); S.add(pk); // (the break room)
  const sunIn = new THREE.SpotLight(0xffd6a0, 600, 50, 0.7, 0.8, 1.2); sunIn.position.set(0, 11, 34); sunIn.target.position.set(0, 0, 8); S.add(sunIn, sunIn.target); // daylight through the door
  // ---- fx: welding sparks (points), the dust ring on landing
  const SN = potato ? 0 : 90, sp = { n: SN, p: new Float32Array(SN * 3), v: new Float32Array(SN * 3), life: new Float32Array(SN) };
  const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(sp.p, 3).setUsage(THREE.DynamicDrawUsage));
  const sparks = new THREE.Points(sg, L.tex(new THREE.PointsMaterial({ color: 0xffd040, size: 0.11, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })));
  sparks.frustumCulled = false; sparks.userData.lsSee = true; root.add(sparks);
  for (let i = 0; i < SN; i++) sp.p[i * 3 + 1] = -99;
  const dust = new THREE.Mesh(new THREE.RingGeometry(0.6, 1.4, 16), L.basic(0xd8cfe0, { transparent: true, opacity: 0, depthWrite: false })); dust.rotation.x = -Math.PI / 2; dust.position.set(0, 0.1, MZ); dust.userData.lsSee = true; root.add(dust);
  function burst(x, y, z, n, up = 3) { for (let k = 0, i = 0; i < sp.n && k < n; i++) if (sp.life[i] <= 0) { k++; sp.life[i] = 0.5 + Math.random() * 0.6; sp.p.set([x, y, z], i * 3); sp.v.set([(Math.random() - 0.5) * 5, Math.random() * up, (Math.random() - 0.2) * 4], i * 3); } }

  // ---- the mechs
  function setMech(b, frame, color) {
    if (b.mech) { freeMech(b.mech); b.mech = null; }
    b.frame = frame; b.color = color;
    if (!frame) return;
    const id = GLB_ID[frame];
    if (missingGlb(id)) { want(id, b.i === 1 ? 3 : 2); whenGlb([id], () => { if (b.frame === frame && b.mech && !b.mech.glb && !gone) setMech(b, frame, color); }); }
    const m = buildMech(frame, color);
    m.root.position.set(0, 0, 0); m.root.rotation.y = Math.PI; // (mechs face -z too)
    m.root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.userData.lsPickMech = 1; } });
    m.root.userData.lsPick = b.i === 1 ? 'mymech' : 'mech';
    b.mech = m; b.g.add(m.root);
    b.st = { spd: 0, fwd: 0, side: 0, air: false, vy: 0, landT: 9, landK: 1, pitch: 0, empty: true, intro: false, falling: false, boost: 0, swingT: 9, gunT: 9, swarmT: 9 };
  }
  let gone = false, list = [], swap = null, shown = null;
  // the swap: lights go red + a klaxon, the hook comes down and hauls the old one up, the new one comes down swinging,
  // CLANK, dust, sparks off the gantry, the lights come back one bank at a time, the plate stamps the new name
  function startSwap(to) {
    const b = bays[1];
    if (swap) { swap.to = to; return; }
    swap = { t: 0, from: b.frame, to, swapped: false, landed: false };
    const c = L.cur(); if (c.walk && !ride) c.camFocus = { at: [0, 4.2, MZ], t: 0, dur: SWAP + 0.5, back: 5 }; // (look up at the bay while it happens)
    try { L.sfx.tone('square', 520, 380, 0.22, 0.08); L.sfx.tone('square', 520, 380, 0.22, 0.08, null, 0.3); } catch { /* (no audio yet) */ }
  }
  function swapTick(dt) {
    const b = bays[1], s = swap;
    if (!s) return;
    s.t += dt;
    const t = s.t, red = t < 1.15 ? 1 : Math.max(0, 1 - (t - 1.15) / 0.35);
    b.lamp.color.copy(b.lampBase).lerp(RED, red); b.lamp.intensity = b.lampI * (red ? 0.55 + 0.45 * (Math.sin(t * 22) > 0 ? 1 : 0.35) : 1);
    for (const o of [bays[0], bays[2]]) o.lamp.intensity = o.lampI * (t < 1.2 ? 0.25 : t < 1.32 ? 0.6 : 1); // the banks come back one at a time
    if (b.arms) for (const a of b.arms) a.rotation.y = (a.name === 'arm_L' ? 1 : -1) * Math.min(1, t / 0.2, Math.max(0, (1.45 - t) / 0.25)) * 0.9; // clamps open, then shut
    const hookY = (y) => { crane.y = y - 12.6; };
    const top = (f) => (f ? MECH[f].h + 0.4 : 3);
    if (t < 0.3) hookY(14 - (14 - top(s.from)) * ease(t / 0.3)); // the hook comes down onto the old one
    else if (t < 0.65) { const k = ease((t - 0.3) / 0.35); hookY(top(s.from) + k * UP); if (b.mech) { b.mech.root.position.y = k * UP; b.st.air = true; } }
    else if (t < 1.15) {
      if (!s.swapped) { s.swapped = true; setMech(b, s.to, b.color); b.st.air = true; shown = s.to; plate(); }
      const k = Math.min(1, ((t - 0.65) / 0.5) ** 1.6), y = (1 - k) * UP; // (falls a bit faster at the end: it lands, it doesn't park)
      hookY(top(s.to) + y); if (b.mech) { b.mech.root.position.y = y; b.mech.root.rotation.z = Math.sin(t * 9) * 0.06 * (1 - k); }
    } else {
      if (!s.landed) { // CLANK
        s.landed = true; L.shake = 0.35;
        if (b.mech) { b.mech.root.position.y = 0; b.mech.root.rotation.z = 0; b.st.air = false; b.st.landT = 0; b.st.landK = 1; }
        try { L.sfx.noise(0.5, 0.9, 'lowpass', 1400, 60); L.sfx.tone('sine', 120, 40, 0.4, 0.6); L.sfx.tone('square', 1800, 900, 0.06, 0.08); L.sfx.noise(0.35, 0.25, 'bandpass', 4000, 2500, null, 0.12); } catch { /* (no audio yet) */ }
        dust.material.opacity = 0.75; dust.scale.setScalar(1);
        for (const sx of [-3.1, 3.1]) burst(sx, 4.4, MZ + 0.6, 26, 4);
        stamp = 0.4;
      }
      hookY(top(s.to) + Math.min(1, (t - 1.15) / 0.45) * (14 - top(s.to)));
      if (t >= SWAP) { swap = null; b.lamp.color.copy(b.lampBase); b.lamp.intensity = b.lampI; if (b.arms) for (const a of b.arms) a.rotation.y = 0; if (s.to !== b.frame) startSwap(s.to); }
    }
  }
  const RED = new THREE.Color(0xff2020);
  const ease = (k) => k * k * (3 - 2 * k);
  let stamp = 0;

  // ---- the plate over your bay: < PAPER PLANE > (buttons) and the empty bays' + INVITE holograms
  const box = L.tag('ls-swap ui', '<button data-d="-1">&lt;</button><b></b><button data-d="1">&gt;</button>');
  const css = document.createElement('style'); css.textContent = `
#lsTags .ls-swap { display: flex; gap: 8px; align-items: center; background: rgba(18,8,24,.92); border: 3px solid #ff4fd8; box-shadow: 5px 5px 0 #4fd8ff; padding: 4px 8px; color: #fff; font-weight: 900; font-size: 15px; letter-spacing: 1px; transform-origin: 50% 100%; }
#lsTags .ls-swap b { min-width: 118px; text-align: center; }
#lsTags .ls-swap b small { display: block; font-size: 10px; color: #ffe14d; letter-spacing: 2px; }
#lsTags .ls-swap button { font: 900 15px var(--font); background: #fff; color: #000; border: 2px solid #000; box-shadow: 2px 2px 0 #ff4fd8; padding: 0 7px; cursor: pointer; }
#lsTags .ls-swap button:active { transform: translate(2px, 2px); box-shadow: none; }
#lsTags .ls-swap.stamp b { animation: lsStamp 0.4s ease-out; }
@keyframes lsStamp { 0% { transform: scale(1.8) rotate(-8deg); color: #ffe14d; } 100% { transform: none; } }
#lsTags .ls-holo { color: #4fd8ff; font-weight: 900; font-size: 20px; letter-spacing: 2px; text-align: center; text-shadow: 0 0 8px #4fd8ff, 2px 2px 0 #120818; animation: lsHolo 1.6s steps(2) infinite; }
#lsTags .ls-holo small { display: block; font-size: 11px; color: #fff; letter-spacing: 1px; text-shadow: 2px 2px 0 #120818; }
@keyframes lsHolo { 50% { opacity: 0.75; } }`;
  box.append(css);
  for (const btn of box.querySelectorAll('button')) btn.addEventListener('click', (e) => { e.stopPropagation(); step(Number(btn.dataset.d)); });
  function step(d) {
    const lo = G.settings.loadout || (G.settings.loadout = {}), i = FRAMES.indexOf(myFrame(G));
    lo.mech = FRAMES[(i + d + FRAMES.length) % FRAMES.length];
    const sv = L.cur().ask.save; if (sv) sv();
  }
  function plate() { const f = shown || myFrame(G); box.querySelector('b').innerHTML = `<small>YOUR MECH</small>${MECH[f].name}`; box.classList.remove('stamp'); void box.offsetWidth; if (stamp || swap) box.classList.add('stamp'); }
  const holos = [0, 2].map((i) => { const d = L.tag('ls-holo', '+ INVITE<small>BAY 0' + (i + 1) + ' IS EMPTY</small>'); d.style.display = 'none'; return d; });
  const holoAt = new THREE.Vector3(), plateAt = new THREE.Vector3(0, 0, 0);

  // where people stand: you in front of your bay, your squad in front of theirs (slightly in, so they stay in the middle)
  const spots = [{ x: 0, z: -2.4, yaw: 0 }, { x: -BAY + 1.5, z: -3, yaw: 0.4 }, { x: BAY - 1.5, z: -3, yaw: -0.4 }];

  // ---- your mech as a ride: E at its feet, it walks where you push, E again and you hop down, it flies home
  let ride = null, ret = null, stompT = 0;
  const RIDE_SOL = SOL.filter((b) => !(b[0] > -1.6 && b[2] < 1.6 && b[1] < MZ + 1.4 && b[3] > MZ - 1.5)); // (not your own bay's mech box)
  function hopIn() {
    const b = bays[1], walk = L.cur().walk;
    if (!b.mech || swap || ret || ride || !walk) return;
    const f = b.frame, F = MECH[f];
    ride = { pos: [0, 0, MZ], yaw: Math.PI, vel: [0, 0, 0], air: false, speed: f === 'nightshift' ? 6 : 7.5, r: 1.7, h: F.h + 0.6, camDist: 13, camH: 4.2,
      solids: RIDE_SOL, bounds: [-22.5, MZ - 0.2, 22.5, 31],
      moved(dt, hs) {
        const m = b.mech; if (!m) return;
        m.root.position.set(this.pos[0], this.pos[1], this.pos[2] - MZ); m.root.rotation.y = this.yaw;
        b.st.spd = hs; b.st.fwd = hs; b.st.air = this.air;
        stompT -= dt * hs / 4;
        if (hs > 1 && stompT <= 0) { stompT = 1; L.shake = Math.max(L.shake, 0.12); try { L.sfx.noise(0.18, 0.35, 'lowpass', 500, 60); } catch { /* (no audio yet) */ } }
      },
      exit() { hopOut(); } };
    walk.setRide(ride); walk.me.hidden = true; b.st.empty = false;
    try { L.sfx.tone('sawtooth', 120, 260, 0.35, 0.12); L.sfx.tone('square', 900, 1400, 0.08, 0.05, null, 0.25); } catch { /* (no audio yet) */ }
  }
  function hopOut() {
    const b = bays[1], walk = L.cur().walk;
    if (!ride || !walk) return;
    const me = walk.me, sy = Math.sin(ride.yaw), cy = Math.cos(ride.yaw);
    me.pos = [ride.pos[0] + cy * 2.4, 0, ride.pos[2] - sy * 2.4]; me.vel = [cy * 2, 5, -sy * 2]; me.air = true; me.hidden = false; me.yaw = ride.yaw;
    ret = { t: 0, from: ride.pos.slice(), yaw: ride.yaw };
    walk.setRide(null); ride = null; b.st.empty = true;
    try { L.sfx.whoosh(0.5, 0.3, 300, 1600); } catch { /* (no audio yet) */ }
  }
  function retTick(dt) { // home: a jet-hop back into the bay, turning round on the way, CLANK
    const b = bays[1], m = b.mech;
    if (!ret || !m) { ret = null; return; }
    ret.t += dt;
    const k = Math.min(1, ret.t / 1.3), e = k * k * (3 - 2 * k), x = ret.from[0] * (1 - e), z = ret.from[2] + (MZ - ret.from[2]) * e, y = Math.sin(k * Math.PI) * 3.5;
    m.root.position.set(x, y, z - MZ); let d = Math.PI - ret.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); m.root.rotation.y = ret.yaw + d * e;
    b.st.air = k < 1; b.st.boost = k < 0.9 ? 1 : 0; b.st.spd = 0;
    if (k >= 1) { ret = null; m.root.position.set(0, 0, 0); m.root.rotation.y = Math.PI; b.st.landT = 0; b.st.landK = 0.7; b.st.boost = 0; L.shake = 0.25; dust.material.opacity = 0.6; dust.scale.setScalar(1); try { L.sfx.noise(0.4, 0.7, 'lowpass', 1200, 60); } catch { /* (no audio yet) */ } }
  }
  // ---- the range: TEST FIRE. three shots down the range, a tracer each, the targets spin. DINK
  const tracers = [];
  function testFire() {
    const walk = L.cur().walk; if (!walk) return;
    const me = walk.me;
    targets.forEach((t, i) => setTimeout(() => {
      if (gone) return;
      const from = new THREE.Vector3(me.pos[0], me.pos[1] + 1.7, me.pos[2]), to = new THREE.Vector3(23.4, 1.6, t.g.position.z);
      const g = new THREE.BufferGeometry().setFromPoints([from, to]), ln = new THREE.Line(g, L.basic(0xffe14d, { transparent: true }));
      ln.userData.lsSee = true; root.add(ln); tracers.push({ ln, life: 0.12 });
      t.spin = 1;
      try { L.sfx.noise(0.08, 0.5, 'highpass', 2000, 800); L.sfx.tone('square', 1900, 1500, 0.09, 0.08, null, 0.05); } catch { /* (no audio yet) */ }
    }, i * 220));
    me.yaw = -Math.PI / 2;
  }
  // ---- the cola machine
  const colaLines = ['a Jank Cola. it\'s warm.', 'it ate your coin. classic.', 'diet Jank Cola. somehow worse.', 'a can of air. limited edition.'];
  const bubble = L.tag('bub', ''); bubble.style.display = 'none'; let bubbleT = 0;
  function cola() { bubble.innerHTML = '<small>THE MACHINE</small>' + colaLines[Math.floor(Math.random() * colaLines.length)]; bubble.style.display = ''; bubbleT = 2.6; try { L.sfx.tone('square', 300, 200, 0.12, 0.06); L.sfx.noise(0.25, 0.3, 'lowpass', 900, 200, null, 0.15); } catch { /* (no audio yet) */ } }
  const bubbleAt = new THREE.Vector3(-22.6, 2.5, 13);
  const walkSpec = {
    spawn: [0, -2.4, 0, 0], bounds: [-23.6, -15.6, 23.6, 32], solids: SOL, camBox: [-23.3, 0.5, -15.3, 23.3, 15.6, 45], dist: 5.6,
    wander: [[-12, -2], [12, -2], [0, 2], [-4, 10], [4, 10], [-18, 14], [-19, 18], [17, 9], [14, 18], [0, 26], [-8, 27], [9, 27], [-6, -3], [6, -3]],
    use: [
      { at: [2.6, 1.2, MZ + 2.7], r: 1.9, label: () => 'SWAP MECH', show: () => !ride && !ret, act: () => step(1) },
      { at: [0, 1.4, MZ + 1.9], r: 2.1, label: () => 'HOP IN', show: () => !ride && !ret && !swap && !!bays[1].mech, act: hopIn },
      { at: [-22.4, 1.4, 13], r: 1.9, label: () => 'GET A COLA', act: cola },
      { at: [15.3, 1.3, 15], r: 2.2, label: () => 'TEST FIRE', act: testFire },
    ],
  };
  return {
    spots, inviteH: 1.2, walk: walkSpec,
    focus: { at: new THREE.Vector3(0, 3.0, -4.6), top: new THREE.Vector3(0, 7.6, MZ), bot: new THREE.Vector3(0, 0, -0.2), w: 7.2, dir: new THREE.Vector3(0, 0.1, 1).normalize(), fov: 34, drift: 0.05 },
    party(l) {
      list = l;
      const myF = myFrame(G), me = l[0] || {};
      if (!bays[1].mech && !swap) { setMech(bays[1], myF, me.color || '#ff4fd8'); shown = myF; plate(); }
      else if (bays[1].mech && me.color && me.color !== bays[1].color && !swap) setMech(bays[1], bays[1].frame, me.color);
      [[1, 0], [2, 2]].forEach(([pi, bi]) => { // party slot -> bay
        const p = l[pi], b = bays[bi];
        const f = p && !p.invite ? mechFrame(p.mech || FRAMES[(pi + (G.myId | 0)) % FRAMES.length]) : null, c = p && !p.invite ? p.color || '#4fd8ff' : null;
        if (f !== b.frame || c !== b.color) setMech(b, f, c);
        holos[bi ? 1 : 0].style.display = 'none'; // (walking: the + INVITE spot in front of the bay says it)
      });
    },
    inviteSpot(wrap) { wrap.userData.lsPick = 'invite'; const m = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 1.9, 8, 1, true), L.basic(0x4fd8ff, { transparent: true, opacity: 0.12, depthWrite: false, side: THREE.DoubleSide })); m.position.y = 0.95; m.userData.lsSee = false; wrap.add(m); },
    update(dt, t) {
      const want2 = myFrame(G);
      if (bays[1].mech && !ride && !ret && want2 !== (swap ? swap.to : bays[1].frame)) startSwap(want2);
      retTick(dt);
      for (const t of targets) if (t.spin > 0) { t.spin = Math.max(0, t.spin - dt * 1.2); t.face.rotation.y = (1 - t.spin) * Math.PI * 4; }
      for (let i = tracers.length - 1; i >= 0; i--) { const tr = tracers[i]; tr.life -= dt; tr.ln.material.opacity = Math.max(0, tr.life / 0.12); if (tr.life <= 0) { root.remove(tr.ln); tr.ln.geometry.dispose(); tr.ln.material.dispose(); tracers.splice(i, 1); } }
      if (bubbleT > 0) { bubbleT -= dt; if (bubbleT <= 0) bubble.style.display = 'none'; }
      swapTick(dt);
      crane.hook.position.y = crane.y; crane.cable.scale.y = Math.max(0.1, -crane.y); crane.cable.position.y = crane.y / 2;
      for (const b of bays) {
        if (b.mech) poseMech(b.mech, b.st, dt);
        if (b.st) b.st.landT += dt;
        if (b.beacons) for (const m of b.beacons) m.visible = Math.sin(t * 6 + b.i) > -0.2;
        b.ring.material.opacity = 0.6 + Math.sin(t * 2 + b.i) * 0.25;
      }
      if (stamp > 0) stamp = Math.max(0, stamp - dt);
      if (dust.material.opacity > 0) { dust.material.opacity = Math.max(0, dust.material.opacity - dt * 1.4); dust.scale.multiplyScalar(1 + dt * 3.2); }
      if (sp.n) { // sparks: fall, bounce once, die
        for (let i = 0; i < sp.n; i++) {
          if (sp.life[i] <= 0) continue;
          sp.life[i] -= dt; const j = i * 3;
          sp.v[j + 1] -= 14 * dt; sp.p[j] += sp.v[j] * dt; sp.p[j + 1] += sp.v[j + 1] * dt; sp.p[j + 2] += sp.v[j + 2] * dt;
          if (sp.p[j + 1] < 0.05) { sp.p[j + 1] = 0.05; sp.v[j + 1] *= -0.3; sp.v[j] *= 0.6; sp.v[j + 2] *= 0.6; }
          if (sp.life[i] <= 0) sp.p[j + 1] = -99;
        }
        sg.attributes.position.needsUpdate = true;
        if (!swap && Math.random() < dt * 0.6) burst(bays[1].x + (Math.random() < 0.5 ? -3.1 : 3.1), 4.4, MZ + 0.6, 6, 2); // the odd weld, idle
      }
    },
    tags(c) {
      plateAt.set(0, 7.3, MZ + 0.6); // (stays put while the mechs move)
      L.at(box, plateAt);
      if (bubbleT > 0) L.at(bubble, bubbleAt);
      holos.forEach((d, k) => { if (d.style.display !== 'none') { holoAt.set(bays[k ? 2 : 0].x, 3.4, MZ); L.at(d, holoAt); } });
      void c;
    },
    hover(h) { box.style.outline = h && h.kind === 'mymech' ? '3px solid #ffe14d' : ''; },
    click(h) { if (h.kind === 'mymech') step(1); },
    info: () => ({ mine: bays[1].frame, swapping: !!swap, riding: !!ride, home: !ret, bays: bays.map((b) => b.frame), glb: bays.map((b) => !!(b.mech && b.mech.glb)), gantry: bays.map((b) => !!b.blender) }),
    dispose() { gone = true; for (const tr of tracers) { tr.ln.geometry.dispose(); tr.ln.material.dispose(); } for (const b of bays) if (b.mech) { freeMech(b.mech); b.mech = null; } },
  };
}

// the gantry, in boxes, until the Blender one lands (same size and spots): two lattice towers, a top beam, a walkway at
// chest height, clamp arms that swing open for a swap, warning beacons
function codeGantry(L, g, { steel, yel, dark }) {
  for (const sx of [-3.4, 3.4]) {
    for (const dz of [-1.1, 1.1]) L.box(g, 0.32, 9, 0.32, yel, sx, 4.5, dz);
    for (let y = 1; y < 9; y += 1.5) { L.box(g, 0.14, 0.14, 2.2, steel, sx, y, 0); const d = L.box(g, 0.1, 1.9, 0.1, steel, sx, y + 0.75, 0); d.rotation.x = 0.85; }
    const arm = new THREE.Group(); arm.name = sx < 0 ? 'arm_L' : 'arm_R'; arm.position.set(sx, 4.4, 0.6); g.add(arm);
    L.box(arm, 1.4, 0.3, 0.3, dark, -Math.sign(sx) * 0.7, 0, 0);
    const bc = L.box(g, 0.25, 0.25, 0.25, L.basic(0xffa020), sx, 9.2, 1.1); bc.name = 'beacon_' + (sx < 0 ? 'L' : 'R');
  }
  L.box(g, 7.1, 0.5, 0.5, yel, 0, 9, 1.1); L.box(g, 7.1, 0.5, 0.5, yel, 0, 9, -1.1);
  L.box(g, 6.5, 0.12, 1.1, steel, 0, 5.2, -1.4); L.box(g, 6.5, 0.07, 0.07, yel, 0, 6.2, -0.9);
}
