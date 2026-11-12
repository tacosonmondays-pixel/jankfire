// BATTLE ISLAND's lobby: the mech garage (docs/menu/LOBBY_SCENES.md). three bays (squads of 3), your mech in the
// middle one in its gantry, your squad in front of theirs. your mech is the loadout's MECH DROP FRAME (the server's
// hero ask for Battle Island), so changing it here or in CUSTOMIZE is the same thing: the crane swaps it, with juice.
import * as THREE from 'three';
import { buildMech, freeMech, poseMech, GLB_ID } from '../mechmodel.js';
import { MECH, FRAMES, mechFrame } from '/shared/mech.js';
import { missingGlb, want, whenGlb } from '../glbkit.js';
import { freeTree } from '../models.js';

const BAY = 7.6, MZ = -9; // bay spacing, where the mechs stand
const SWAP = 1.6, UP = 8.5; // s, the whole swap; how high the crane hauls (just out of the picture, behind the headers)
const myFrame = (G) => mechFrame(G.settings && G.settings.loadout && G.settings.loadout.mech);

export function build(L) {
  const { G } = L, S = L.cur().scene, root = new THREE.Group(); S.add(root);
  S.background = new THREE.Color(0x0c0812);
  S.fog = new THREE.Fog(0x0c0812, 22, 46);
  const potato = L.potato();
  // ---- the room
  const conc = L.mat(0x6a6670, 0.82); conc.map = L.speck(0x6a6670, 14);
  const floor = L.box(root, 46, 0.2, 34, conc, 0, -0.1, -6); floor.castShadow = false;
  const wall = L.mat(0x1d1824, 0.9); wall.map = L.speck(0x2a2433, 6, true);
  L.box(root, 46, 16, 0.4, wall, 0, 8, -16).castShadow = false;
  for (const sx of [-1, 1]) L.box(root, 0.4, 16, 34, wall, sx * 23, 8, -6).castShadow = false;
  const steel = L.mat(0x2a2c34, 0.42, 0.75), yel = L.mat(0xd9a21a, 0.42, 0.25), dark = L.mat(0x15131a, 0.6, 0.4);
  for (let i = -3; i <= 3; i++) L.box(root, 0.35, 16, 0.6, steel, i * 6.5, 8, -15.6).castShadow = false; // wall ribs
  L.box(root, 46, 0.5, 0.8, steel, 0, 14.2, -15.4).castShadow = false;
  const tape = L.mat(0xffffff, 0.6); tape.map = L.stripes(40);
  for (const z of [-3.6, -14.2]) { const t = L.box(root, 34, 0.02, 0.35, tape, 0, 0.012, z); t.castShadow = false; }
  // the sign: DAYS WITHOUT A MECH ON FIRE
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 1.05), L.basic(0xffffff, { map: L.label('DAYS WITHOUT A MECH ON FIRE: 0', { w: 512, h: 128 }) }));
  sign.position.set(-13.5, 6.4, -15.35); root.add(sign);
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
  L.box(root, 26, 0.45, 0.55, steel, 0, 13.0, MZ);
  const trolley = new THREE.Group(); trolley.position.set(0, 12.6, MZ); root.add(trolley);
  L.box(trolley, 1.4, 0.55, 1.0, yel, 0, 0, 0);
  const cable = L.cyl(trolley, 0.035, 0.035, 1, steel, 0, 0, 0, 6); cable.castShadow = false;
  const hook = new THREE.Group(); trolley.add(hook);
  L.box(hook, 0.9, 0.55, 0.7, yel, 0, 0, 0); L.box(hook, 0.16, 0.6, 0.16, steel, 0, -0.5, 0);
  const crane = { trolley, cable, hook, y: -1.2 }; // hook height under the trolley
  // ---- props: crates, a tool cart, cables on the floor, a red toolbox (code for now; the Blender kit swaps in)
  const wood = L.mat(0x7a5530, 0.8);
  for (let i = 0; i < 5; i++) L.box(root, 1, 0.8, 1, wood, -11.5 + (i % 3) * 1.08, 0.4 + Math.floor(i / 3) * 0.8, -4.6 - (i % 2) * 0.1, i * 0.2);
  L.box(root, 1.5, 0.95, 0.75, L.mat(0xc8202a, 0.35, 0.3), 11.2, 0.48, -4.4, -0.3); L.box(root, 1.4, 0.07, 0.65, steel, 11.2, 0.99, -4.4, -0.3);
  L.glb('p_barrel', (o) => { for (const [x, z] of [[13.2, -6], [13.9, -6.9], [-14, -8]]) { const c = o.clone(); c.position.set(x, 0, z); root.add(c); } });
  // ---- lights: a dim purple room, a key from the front, the bay lamps, a cyan kicker
  S.add(new THREE.HemisphereLight(0x9a88c0, 0x1a1020, 0.9));
  const key = new THREE.DirectionalLight(0xffe6f4, 1.25); key.position.set(-5, 10, 9); key.target.position.set(0, 1, -5); S.add(key, key.target);
  if (L.shadows()) { key.castShadow = true; key.shadow.mapSize.set(potato ? 512 : 2048, potato ? 512 : 2048); Object.assign(key.shadow.camera, { left: -16, right: 16, top: 14, bottom: -4, near: 1, far: 40 }); key.shadow.bias = -0.0005; key.shadow.normalBias = 0.03; }
  const kick = new THREE.PointLight(0x4fd8ff, 30, 14); kick.position.set(4.5, 3, -1.5); S.add(kick);
  const pk = new THREE.PointLight(0xff4fd8, 26, 14); pk.position.set(-4.5, 3, -1.5); S.add(pk);
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
  const spots = [{ x: 0, z: -0.6, ry: 0.05 }, { x: -2.3, z: -2.4, ry: 0.32 }, { x: 2.3, z: -2.4, ry: -0.32 }];
  return {
    spots, inviteH: 1.2,
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
        holos[bi ? 1 : 0].style.display = f ? 'none' : '';
      });
    },
    inviteSpot(wrap) { wrap.userData.lsPick = 'invite'; const m = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 1.9, 8, 1, true), L.basic(0x4fd8ff, { transparent: true, opacity: 0.12, depthWrite: false, side: THREE.DoubleSide })); m.position.y = 0.95; m.userData.lsSee = false; wrap.add(m); },
    update(dt, t) {
      const want2 = myFrame(G);
      if (bays[1].mech && want2 !== (swap ? swap.to : bays[1].frame)) startSwap(want2);
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
      holos.forEach((d, k) => { if (d.style.display !== 'none') { holoAt.set(bays[k ? 2 : 0].x, 3.4, MZ); L.at(d, holoAt); } });
      void c;
    },
    hover(h) { box.style.outline = h && h.kind === 'mymech' ? '3px solid #ffe14d' : ''; },
    click(h) { if (h.kind === 'mymech') step(1); },
    info: () => ({ mine: bays[1].frame, swapping: !!swap, bays: bays.map((b) => b.frame), glb: bays.map((b) => !!(b.mech && b.mech.glb)), gantry: bays.map((b) => !!b.blender) }),
    dispose() { gone = true; for (const b of bays) if (b.mech) { freeMech(b.mech); b.mech = null; } },
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
