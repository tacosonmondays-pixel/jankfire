// BOARD GAME NIGHT's lobby: the kitchen at night (docs/party/DESIGN.md 6). the Blender kitchen (x_bgn_kitchen, life size)
// with the board set up on the table, the toaster podium and the snacks, THE RULES GUY at the head of the table with his
// rulebook (upside down), and your party standing round the table behind the board. the pendant lamp is the only light
// on, the moon's in the window, the camera drifts. click the rules guy: he reads you a rule (wrong). code boxes stand in
// until the models land.
import * as THREE from 'three';
import { npcRig } from './npcrig.js';
import { buildCharacter } from '../models.js';
import { BGN_NAMES } from '/shared/bgn.js';
import { DEFAULT_LOOK } from '/shared/looks.js';

const K = 1.08; // the kitchen a touch bigger than life: the mannequins are tall
const RULES = ['the youngest player goes first. unless they are tall.', 'you can buy bread with coupons. or with feelings. page 9.', 'if the die falls off the table, that counts as a six.',
  'the crease is a shortcut. it is also sticky. both are true.', 'golden bread cannot be eaten. we checked.', 'no flipping the board. this is a family table.'];
export function build(L) {
  const { G } = L, S = L.cur().scene, root = new THREE.Group(); S.add(root);
  const potato = L.potato();
  S.background = new THREE.Color(0x0c0818);
  S.fog = new THREE.Fog(0x0c0818, 7, 16);
  let top = 0.76 * K; // the table top (the glb's origin)
  // ---- the code kitchen (until the Blender one lands): floor, a wall, the table, a board
  const code = new THREE.Group(); root.add(code);
  const fl = L.mat(0x2c1a3c, 0.5); fl.map = L.speck(0x3a2848, 10); L.box(code, 8, 0.1, 6, fl, 0, -0.05, -0.5).castShadow = false;
  const wall = L.mat(0x7a3a6a, 0.8); wall.map = L.speck(0x8a4a7a, 6); L.box(code, 8, 3, 0.1, wall, 0, 1.5, -2.1).castShadow = false;
  const tbl = L.mat(0x56d4e6, 0.3); L.box(code, 1.6 * K, 0.04, 0.95 * K, tbl, 0, top - 0.02, 0);
  for (const x of [-0.68, 0.68]) for (const z of [-0.36, 0.36]) L.cyl(code, 0.02, 0.016, top, L.mat(0xe8ecf4, 0.15, 1), x * K, top / 2, z * K, 8);
  const brd = L.mat(0x241238, 0.4); brd.map = L.label('BOARD GAME NIGHT', { bg: '#241238', fg: '#ffe14d', border: '#ff4fd8', w: 256, h: 210 }); L.box(code, 0.72 * K, 0.008, 0.6 * K, brd, 0, top + 0.004, 0);
  // ---- lights: night. the pendant over the table is the only light on; the moon through the window; a pink kick
  S.add(new THREE.HemisphereLight(0x4a4a8a, 0x120818, 0.6));
  const bulb = new THREE.PointLight(0xffd29a, 6, 6, 1.4); bulb.position.set(0, top + 0.7, 0.02); S.add(bulb);
  const pool = new THREE.SpotLight(0xffcf8a, 38, 8, 0.75, 0.6, 1.2); pool.position.set(0, top + 0.72, 0.02); pool.target.position.set(0, top, 0); S.add(pool, pool.target);
  if (L.shadows()) { pool.castShadow = true; pool.shadow.mapSize.set(potato ? 512 : 1024, potato ? 512 : 1024); pool.shadow.bias = -0.0005; pool.shadow.camera.near = 0.2; }
  const moon = new THREE.DirectionalLight(0x8aa0ff, 0.5); moon.position.set(-2, 3, -4); moon.target.position.set(0, 0, 0); S.add(moon, moon.target);
  const kick = new THREE.PointLight(0xff4fd8, 4, 5); kick.position.set(1.6, 1.4, 1.2); S.add(kick);
  let bread = null;
  // ---- the Blender kitchen, the toaster podium, the bakery and the die on the board
  let kit = null;
  L.glb('x_bgn_kitchen', (o, meta) => {
    kit = o; o.scale.setScalar(K); top = -(meta.floor || -0.76) * K; o.position.y = top;
    o.traverse((m) => { if (m.isMesh) { m.receiveShadow = true; m.castShadow = !/room/.test(m.name) && !(m.parent && /room/.test(m.parent.name)); } });
    root.add(o); code.visible = false;
    const lampN = o.getObjectByName('lamp'), lift = 0.85; // (the pendant hangs higher here: over the party's heads, not in front of their faces)
    if (lampN) lampN.position.y += lift / K;
    if (Array.isArray(meta.lamp)) { bulb.position.set(meta.lamp[0] * K, top + meta.lamp[1] * K + lift - 0.02, meta.lamp[2] * K); pool.position.copy(bulb.position); pool.distance = 9; }
    const pd = meta.podium || [0.585, 0.015, -0.12];
    L.glb('x_bgn_toaster', (t) => { t.scale.setScalar(K); t.position.set(pd[0] * K, top, pd[1] * K); t.rotation.y = pd[2] || 0; t.traverse((m) => { if (m.isMesh) m.castShadow = m.receiveShadow = true; }); root.add(t); });
    const sp = meta.spaces || [];
    L.glb('x_bgn_die', (d) => { const s = (0.035 / 1.4) * K; d.scale.setScalar(s); d.position.set(-0.24 * K, top + 0.0095 * K + 0.0175 * K, -0.2 * K); d.rotation.set(0.0, 0.5, 0.0); root.add(d); });
    L.glb('x_bgn_bakery', (b) => {
      const st = b.getObjectByName('stall'), br = b.getObjectByName('bread'), s = K / 40, q = sp[3] || [-0.12, -0.24];
      if (st) { st.parent.remove(st); st.position.set(q[0] * K, top + 0.0075 * K, (q[1] + 0.06) * K); st.scale.setScalar(s); st.rotation.y = Math.PI; root.add(st); }
      if (br) { br.parent.remove(br); br.position.set(q[0] * K, top + 0.022 * K, q[1] * K); br.scale.setScalar(s); root.add(br); bread = br; }
    });
  });
  // ---- THE RULES GUY at the head of the table (life size), reading the rules upside down
  const host = new THREE.Group(); host.position.set(-1.08 * K, 0, -0.42); host.rotation.y = -Math.PI / 2 - 0.55; root.add(host); // (the head of the table, turned to the room)
  host.userData.lsPick = 'host';
  let rig = null, stand = null;
  try { // (the code stand-in: a mannequin in a cardigan with a pink book)
    const ch = buildCharacter('#f2b630', { ...DEFAULT_LOOK, top: 'cardigan', topColor: '#f2b630', bottom: 'pants', bottomColor: '#463c56', skin: '#f0c49a' });
    ch.root.rotation.y = Math.PI; ch.arm.rotation.set(-0.7, 0.4, 0); ch.armL.rotation.set(-0.7, -0.4, 0);
    L.box(ch.root, 0.3, 0.4, 0.05, L.mat(0xff4fd8, 0.4), 0, 1.15, -0.34).rotation.x = 0.6;
    host.add(ch.root); stand = ch;
  } catch { /* (no model kit) */ }
  L.glb('x_bgn_rulesguy', () => {
    rig = npcRig('x_bgn_rulesguy', L.tex, () => !L.potato());
    if (!rig) return;
    if (stand) { host.remove(stand.root); stand = null; }
    rig.baseYaw = host.rotation.y; host.add(rig.root);
  });
  // the party stands round the far side of the table, facing you over the board (up to 4: the board's seats)
  const z = -0.84 * K;
  const spots = [{ x: -0.2, z, ry: 0.06 }, { x: 0.32, z: z - 0.02, ry: -0.08 }, { x: -0.7, z: z + 0.04, ry: 0.18 }, { x: 0.82, z: z + 0.03, ry: -0.2 }];
  let bub = null, bubT = 0;
  const say = (line) => {
    if (!bub) bub = L.tag('bub', '');
    bub.innerHTML = `<small>${BGN_NAMES.host}</small>`; bub.append(document.createTextNode(line)); bubT = 4;
    if (rig) rig.talk(2.8);
  };
  const _v = new THREE.Vector3();
  let next = 6;
  return {
    spots, fill: 4, inviteH: 1.3,
    focus: { at: new THREE.Vector3(0.05, 1.12, -0.42), top: new THREE.Vector3(0, 2.1, -0.85), bot: new THREE.Vector3(0, 0.82, 0.36), w: 2.7, min: 3.4, dir: new THREE.Vector3(0, 0.5, 1).normalize(), fov: 38, drift: 0.06 },
    inviteSpot(wrap) { wrap.userData.lsPick = 'invite'; const m = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 1.8, 10, 1, true), L.basic(0x4fd8ff, { transparent: true, opacity: 0.14, depthWrite: false, side: THREE.DoubleSide })); m.position.y = 0.9; wrap.add(m); },
    click(h) { if (h && h.kind === 'host') { say(RULES[Math.floor(Math.random() * RULES.length)]); if (rig && Math.random() < 0.4) rig.gesture(); } },
    update(dt, t) {
      const ppl = L.people(), me = ppl.find((p) => p.info && p.info.me);
      if (rig) { if (me) me.wrap.getWorldPosition(_v).add(new THREE.Vector3(0, 1.6, 0)); rig.update(dt, me ? _v : null); }
      if ((next -= dt) <= 0) { next = 9 + Math.random() * 6; if (Math.random() < 0.5) say(BGN_NAMES.lines.intro[Math.floor(Math.random() * BGN_NAMES.lines.intro.length)]); else if (rig) rig.gesture(); }
      if (bub) { bubT -= dt; bub.style.opacity = bubT > 0 ? '1' : '0'; host.getWorldPosition(_v); _v.y += 2.15; L.at(bub, _v, 0, -6); }
      bulb.intensity = 6 + Math.sin(t * 31) * 0.15 + (Math.random() < 0.004 ? -2.5 : 0); // (the old bulb hums)
      if (bread) bread.rotation.y += dt * 0.8;
    },
    info: () => ({ kitchen: !!kit, host: !!rig }),
    dispose() { if (rig) rig.dispose(); },
  };
}
