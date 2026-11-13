// ZOMBIES' lobby: the warehouse (docs/menu/LOBBY_SCENES.md), and you walk around in it. a boarded-up base at night:
// planks over the windows with hands poking through, green light leaking in, a generator chugging, a radio, the wall
// of tally marks, a practice zombie on a chain. three stations, three people: walk up to one and press E.
//   DEB at the PASSIVES desk, GUS at the PISTOLS counter, MARGE on THE ITEM crates
// each opens a small picker with the same choices (and the same saved setting) as CUSTOMIZE > LOADOUT > ZOMBIES, and
// says something about what you picked. nothing new on the server: it's your zombies loadout (shared/zombies.js).
import * as THREE from 'three';
import { buildCharacter, buildWeapon, buildProjectile, freeTree } from '../models.js';
import { idlePose } from '../loco.js';
import { WEAPONS, ITEMS, ITEM_ORDER } from '/shared/weapons.js';
import { ZM_PISTOLS, ZM_PASSIVES, zmValidLoadout } from '/shared/zombies.js';
import { DEFAULT_LOOK } from '/shared/looks.js';
import { net } from '../net.js';
import { npcRig } from './npcrig.js';

const pick = (a) => a[Math.floor(Math.random() * a.length)];
const NPC = {
  deb: { name: 'DEB', what: 'PASSIVES', at: [-9.2, -7.6], yaw: Math.PI * 0.72, color: '#ff9ad5',
    look: { hair: 'bun', hairColor: '#a3a3ad', top: 'suit', topColor: '#ff9ad5', bottom: 'skirt', bottomColor: '#3a3a44', skin: '#e0ac69', build: 'f', face: 'readers', back: 'handbag' },
    hi: ['pick a passive. i\'m on break in 4 minutes.', 'you again.', 'the forms are in triplicate. the passives aren\'t.', 'take a number. any number.'],
    got: { trustfund: 'trust fund. must be nice.', quickhands: 'quick hands. don\'t touch my stapler.', stubborn: 'stubborn. we\'ve met.', handyman: 'handyman. the break room tap drips.', rabbitfoot: 'the rabbit did not consent.', thickskin: 'thick skin. you\'ll need it here.', coupons: 'coupons. you\'re the person at the till.', secondwind: 'second wind. i\'m on my first.' } },
  gus: { name: 'GUS', what: 'PISTOLS', at: [0, -10.6], yaw: 0, color: '#3a6a2a',
    look: { hair: 'short', hairColor: '#4a2a10', top: 'jacket', topColor: '#3a6a2a', bottom: 'cargo', bottomColor: '#c8b48a', skin: '#c68642', build: 'm', face: 'mustache', head: 'cap', fat: 2 },
    hi: ['it\'s a gun counter. pick a gun.', 'no refunds. no returns. no questions.', 'i polish them. nobody asked.', 'one per customer. house rules.'],
    got: { revolver: 'it\'s a revolver. it revolves.', pistol: 'plan B. always plan B.', akimbo: 'two guns. zero aim.', sawnoff: 'sawn off. like my patience.', water: 'a water pistol. bold.' } },
  marge: { name: 'MARGE', what: 'THE ITEM', at: [9.2, -7.6], yaw: -Math.PI * 0.72, color: '#ff7a1a', sit: true,
    look: { hair: 'long', hairColor: '#ffffff', top: 'hoodie', topColor: '#ff7a1a', bottom: 'pants', bottomColor: '#2a4a8a', skin: '#ffdbac', build: 'f', head: 'bucket', back: 'teddy' },
    hi: ['take one. not two. one.', 'i knitted the grenade a cosy.', 'back in my day we threw rocks.', 'they\'re all loaded, dear.'],
    got: {} },
};

export function build(L) {
  const { G } = L, S = L.cur().scene, root = new THREE.Group(); S.add(root);
  S.background = new THREE.Color(0x05080a);
  S.fog = new THREE.Fog(0x0a100c, 22, 60);
  const potato = L.potato();
  const flat = (o) => { o.castShadow = false; return o; };
  const SOL = [], solid = (x0, z0, x1, z1, top = 99) => { SOL.push([x0, z0, x1, z1, top]); };
  // ---- the room: cracked concrete, brick, a tin roof on trusses, a boarded double door with EXIT over it
  const conc = L.mat(0x4a4a44, 0.9); conc.map = L.speck(0x55554c, 12);
  flat(L.box(root, 36, 0.2, 30, conc, 0, -0.1, -1));
  const brick = L.mat(0x5a3a30, 0.95); brick.map = brickTex(L);
  flat(L.box(root, 36, 9, 0.5, brick, 0, 4.5, -14.25)); flat(L.box(root, 36, 9, 0.5, brick, 0, 4.5, 12.25));
  for (const sx of [-1, 1]) flat(L.box(root, 0.5, 9, 27, brick, sx * 17.75, 4.5, -1));
  solid(-18, -14.5, 18, -14, 99); solid(-18, 12, 18, 12.5, 99);
  flat(L.box(root, 36, 0.3, 27, L.mat(0x22201c, 0.9), 0, 9.1, -1));
  const steel = L.mat(0x3a3d46, 0.45, 0.7), wood = L.mat(0x8a6a40, 0.85), dark = L.mat(0x1a1612, 0.8);
  for (let z = -11; z <= 10; z += 7) flat(L.box(root, 35, 0.35, 0.3, steel, 0, 8.6, z));
  // the windows: planks nailed across, green light through the gaps, hands poking in
  const glow = L.basic(0x39ff14), hands = [];
  const skinZ = L.mat(0x7aa86a, 0.8);
  const windows = [[-17.5, -6, Math.PI / 2], [-17.5, 4, Math.PI / 2], [17.5, -6, -Math.PI / 2], [17.5, 4, -Math.PI / 2], [-8, -14, 0], [8, -14, 0]];
  for (const [x, z, ry] of windows) {
    const w = new THREE.Group(); w.position.set(x, 3.4, z); w.rotation.y = ry; root.add(w);
    flat(L.box(w, 3, 2.2, 0.05, glow, 0, 0, 0));
    for (let i = 0; i < 4; i++) { const p = L.box(w, 3.4, 0.38, 0.12, wood, 0, -0.85 + i * 0.56, 0.14); p.rotation.z = (Math.random() - 0.5) * 0.22; }
    for (const hx of [-0.8, 0.9]) { // a hand through a gap: forearm, palm, fingers. it grabs at the air
      const h = new THREE.Group(); h.position.set(hx, -0.55 + Math.random() * 1.1, 0.3); w.add(h);
      L.box(h, 0.12, 0.12, 0.5, skinZ, 0, 0, 0.1); const palm = new THREE.Group(); palm.position.z = 0.38; h.add(palm);
      L.box(palm, 0.18, 0.06, 0.16, skinZ, 0, 0, 0.04); for (let f = 0; f < 4; f++) L.box(palm, 0.03, 0.03, 0.14, skinZ, -0.06 + f * 0.04, 0, 0.17);
      hands.push({ h, palm, ph: Math.random() * 9 });
    }
  }
  if (!potato) for (const [x, z] of [[-15.5, -1], [15.5, -1]]) { const l = new THREE.PointLight(0x39ff14, 40, 16); l.position.set(x, 3.4, z); root.add(l); } // (the windows' green, two lights for all six)
  // the door at the front: boarded, chained, EXIT (lies)
  const door = new THREE.Group(); door.position.set(0, 0, 11.95); root.add(door);
  flat(L.box(door, 4.4, 4.6, 0.2, L.mat(0x3a3a40, 0.6, 0.4), 0, 2.3, 0));
  for (let i = 0; i < 3; i++) { const p = L.box(door, 5, 0.4, 0.14, wood, 0, 1.2 + i * 1.2, -0.18); p.rotation.z = (i - 1) * 0.18; }
  const ex = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.45), L.basic(0xffffff, { map: L.label('EXIT (LIES)', { bg: '#1a3a1a', fg: '#39ff14', border: '#000', w: 256, h: 80 }) })); ex.position.set(0, 5.2, -0.15); ex.rotation.y = Math.PI; door.add(ex);
  // the tally wall: every round anyone survived, in chalk
  const tally = new THREE.Mesh(new THREE.PlaneGeometry(6, 2.4), L.basic(0xffffff, { map: tallyTex(L) })); tally.position.set(-17.45, 4.2, 6.5); tally.rotation.y = Math.PI / 2; root.add(tally);
  // ---- stations: a desk (Deb), a counter with the start pistols on a pegboard (Gus), a pile of item crates (Marge)
  const desk = new THREE.Group(); desk.position.set(-8.2, 0, -6.8); desk.rotation.y = Math.atan2(NPC.deb.at[0], NPC.deb.at[1] - 2) + Math.PI; root.add(desk); // (its customer side to the room, Deb behind it. it used to read NPC.deb.yaw before the loop below rewrote it, so the first visit had the desk end-on)
  L.box(desk, 2.4, 0.9, 1, wood, 0, 0.45, 0); L.box(desk, 2.6, 0.08, 1.2, L.mat(0x3a2a1a, 0.6), 0, 0.92, 0);
  L.box(desk, 0.4, 0.06, 0.3, L.mat(0xffffff, 0.8), -0.6, 0.98, 0); L.box(desk, 0.4, 0.1, 0.3, L.mat(0xffffff, 0.8), -0.62, 1.02, 0.05);
  let stamp = L.box(desk, 0.12, 0.2, 0.12, L.mat(0xd0202a, 0.4), 0.5, 1.06, 0), stampY = 1.06;
  L.box(desk, 0.3, 0.32, 0.08, L.mat(0x2a2a2a, 0.4), 0.9, 1.1, -0.3);
  solid(-9.6, -8.2, -6.8, -5.4, 0.95);
  const ctr = new THREE.Group(); ctr.position.set(0, 0, -9.2); root.add(ctr);
  L.box(ctr, 4, 1.05, 0.9, L.mat(0x4a3a2a, 0.7), 0, 0.52, 0); L.box(ctr, 4.2, 0.08, 1.05, L.mat(0x1a1612, 0.5, 0.3), 0, 1.08, 0);
  solid(-2.1, -9.7, 2.1, -8.7, 1.1);
  const peg = L.mat(0xc8a878, 0.8); peg.map = pegTex(L);
  const pegG = new THREE.Group(); pegG.position.set(0, 0, -13.9); root.add(pegG); flat(L.box(pegG, 5, 2.6, 0.1, peg, 0, 2.6, 0));
  Object.keys(ZM_PISTOLS).forEach((id, i) => { try { const w = buildWeapon(id); w.scale.setScalar(2.2); w.rotation.y = Math.PI / 2; w.position.set(-1.8 + i * 0.9, 2.6 + (i % 2) * 0.5, -13.75); root.add(w); } catch { /* (no model) */ } });
  const pile = new THREE.Group(); pile.position.set(9.6, 0, -7.8); root.add(pile);
  for (const [x, y, z, r] of [[0, 0, 0, 0.1], [1.25, 0, 0.2, -0.2], [0.6, 1.2, 0.1, 0.3], [-1.1, 0, 0.6, 0.4]]) { const c = L.box(pile, 1.2, 1.2, 1.2, wood, x, y + 0.6, z); c.rotation.y = r; }
  solid(8.2, -9, 11.4, -6.6, 1.2);
  // the goods on the crates: grenades, a smoke, the duck, a medkit, a shield bubble (the items' own models)
  const goods = [['p', 'frag', 8.3, -8.7], ['p', 'frag', 8.6, -8.5], ['p', 'smokegren', 8.9, -8.75], ['p', 'duck', 10.4, -7.4], ['g', 'x_medkit', 9.9, -8.6], ['g', 'x_bubble', 10.6, -8.3]];
  for (const [k, id, x, z] of goods) {
    const put = (m, sc) => { m.scale.multiplyScalar(sc); m.position.set(x, 1.22, z); m.rotation.y = x * 3; m.traverse((o) => { if (o.isMesh) o.castShadow = true; }); root.add(m); };
    if (k === 'p') { try { put(buildProjectile(id), 1.4); } catch { /* (no model) */ } } else L.glb(id, (o) => put(o, 0.9));
  }
  // signs over the stations
  for (const [txt, x, z, ry] of [['PASSIVES', -9.6, -9.4, Math.PI * 0.25], ['PISTOLS', 0, -13.4, 0], ['THE ITEM', 10.8, -9.6, -Math.PI * 0.25]]) {
    const sg = new THREE.Mesh(new THREE.PlaneGeometry(2, 0.5), L.basic(0xffffff, { map: L.label(txt, { bg: '#39ff14', w: 256, h: 64 }) })); sg.position.set(x, 4.6, z); sg.rotation.y = ry; root.add(sg);
  }
  // ---- the rest of the base: the cola machine, the cheat machine, sandbags, the generator, the radio, pallets
  L.glb('x_zmcola', (o) => { o.position.set(-16.6, 0, -1); o.rotation.y = Math.PI / 2; root.add(o); }); solid(-17.5, -1.7, -16, -0.3, 2.1);
  L.glb('x_zmmachine', (o) => { o.position.set(16.4, 0, -1.5); o.rotation.y = -Math.PI / 2; root.add(o); }); solid(15.4, -2.6, 17.5, -0.4, 2.4);
  L.glb('p_sandbags', (o) => { const l1 = o.getObjectByName('lod1'); if (l1) l1.visible = false; for (const [x, z, r] of [[-12, 8, 0], [12, 8, 0], [-4, 10.5, 0]]) { const c = o.clone(); c.position.set(x, 0, z); c.rotation.y = r; root.add(c); } });
  for (const [x, z] of [[-12, 8], [12, 8], [-4, 10.5]]) solid(x - 1.5, z - 0.5, x + 1.5, z + 0.5, 0.8);
  const gen = new THREE.Group(); gen.position.set(13.5, 0, 9); root.add(gen);
  L.box(gen, 2.2, 1.3, 1.2, L.mat(0xd9a21a, 0.4, 0.3), 0, 0.75, 0); L.box(gen, 2.3, 0.15, 1.3, dark, 0, 0.08, 0); L.cyl(gen, 0.12, 0.12, 0.8, steel, 0.8, 1.7, 0.3, 8);
  L.box(gen, 0.8, 0.5, 0.05, L.basic(0xffffff, { map: L.label('DO NOT KICK', { w: 256, h: 64 }) }), -0.3, 0.9, 0.62);
  solid(12.3, 8.3, 14.7, 9.7, 1.4);
  const radio = new THREE.Group(); radio.position.set(-6.6, 1.0, -6.4); root.add(radio);
  L.box(radio, 0.5, 0.3, 0.2, L.mat(0x8a2a2a, 0.4), 0, 0, 0); L.cyl(radio, 0.08, 0.08, 0.02, L.mat(0x111111), 0.12, 0, 0.11, 10); L.cyl(radio, 0.01, 0.01, 0.4, steel, -0.18, 0.3, 0, 4);
  const palG = new THREE.Group(); root.add(palG); for (const [x, z] of [[4, 6], [5.3, 6.2]]) { L.box(palG, 1.2, 0.15, 1.2, wood, x, 0.08, z); } solid(3.4, 5.4, 5.9, 6.8, 0.16);
  // string lights between the trusses, warm and a bit sad
  const bulbs = [];
  for (let i = 0; i < 18; i++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.08, 6, 4), L.basic([0xffe14d, 0xff4fd8, 0x39ff14][i % 3])); b.position.set(-15 + i * 1.75, 7.2 + Math.sin(i * 1.3) * 0.25, -3 + Math.cos(i * 0.7) * 1.2); b.userData.lsSee = true; root.add(b); bulbs.push(b); }
  // ---- the practice zombie: chained to a post, shuffles round it, groans. E: poke it
  const postG = new THREE.Group(); postG.position.set(-6, 0, 4); root.add(postG); L.cyl(postG, 0.15, 0.18, 2.2, steel, 0, 1.1, 0, 8).castShadow = true; solid(-6.25, 3.75, -5.75, 4.25);
  // the props, Blender-made (x_lobby_whprops: a node per prop, each where its box one stood; the boxes until it lands).
  // the stamp keeps stamping, the radio moves onto Deb's desk
  let radioNode = null;
  L.glb('x_lobby_whprops', (o) => {
    const take = (n) => { const m = o.getObjectByName(n); if (!m) return null; m.position.set(0, 0, 0); m.traverse((x) => { if (x.isMesh) { x.castShadow = true; x.receiveShadow = true; } }); return m; };
    const into = (g, n) => { const m = take(n); if (!m) return null; freeTree(g); g.clear(); g.add(m); return m; };
    const d = into(desk, 'desk');
    if (d) { const st = d.getObjectByName('stamp'); if (st) { stamp = st; stampY = st.position.y; } radioNode = d.getObjectByName('radio'); freeTree(radio); radio.clear(); }
    into(ctr, 'counter'); into(pegG, 'pegboard'); into(pile, 'crates'); into(gen, 'generator'); into(postG, 'post'); into(door, 'door');
    const pl = take('pallet'); if (pl) { freeTree(palG); palG.clear(); for (const [x, z, r] of [[4, 6, 0.1], [5.3, 6.2, -0.2]]) { const c = pl.clone(); c.position.set(x, 0, z); c.rotation.y = r; palG.add(c); } }
  });
  const zl = { ...DEFAULT_LOOK, skin: '#a8e6a1', hair: 'mohawk', hairColor: '#3a6a2a', top: 'tee', topColor: '#8a5a2b', bottom: 'shorts', bottomColor: '#3a3a44' };
  const zch = buildCharacter('#8a5a2b', zl); zch.root.scale.setScalar(1.2); root.add(zch.root);
  zch.root.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  const chain = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1, 5), steel); chain.userData.lsSee = true; root.add(chain);
  const zom = { ch: zch, a: 0, flail: 0, t: 0 };
  function poke() { zom.flail = 1.6; try { L.sfx.tone('sawtooth', 140, 70, 0.5, 0.12); L.sfx.noise(0.3, 0.2, 'lowpass', 600, 120); } catch { /* (no audio yet) */ } say(zomBub, pick(['BRAAAINS', 'hhhnnnggg', '...rent is due', 'MRRRGH']), 'PRACTICE ZOMBIE'); }
  // ---- the three NPCs (the game's own mannequins, dressed for work), each with a little job to do while they wait
  const npcs = {};
  for (const [k, n] of Object.entries(NPC)) {
    n.yaw = Math.atan2(n.at[0], n.at[1] - 2); // (facing the middle of the room)
    const ch = buildCharacter(n.color, { ...DEFAULT_LOOK, ...n.look });
    ch.root.scale.setScalar(1.2); ch.root.position.set(n.at[0], 0, n.at[1]); ch.root.rotation.y = n.yaw; root.add(ch.root);
    ch.root.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    if (k === 'gus') { const w = buildWeapon('revolver'); w.scale.setScalar(1.5); ch.slot.add(w); }
    if (n.sit) { ch.root.position.y = 1.2; } // (Marge sits on the crates)
    solid(n.at[0] - 0.45, n.at[1] - 0.45, n.at[0] + 0.45, n.at[1] + 0.45, 99);
    npcs[k] = { ch, n, bub: L.tag('bub', ''), t: Math.random() * 9, face: n.yaw, hiT: 0 };
    npcs[k].bub.style.display = 'none';
  }
  // the Blender ones (x_lobby_<k>.glb): each takes over from its mannequin when its file lands, placed against its prop
  // (meta.place: the prop's frame), and plays idle / talk / its gesture. a missing file keeps the mannequin
  const PROPS = { desk, counter: ctr, crates: pile };
  const SND = { // the gestures' cues (meta clips.gesture.marks)
    ink: () => L.sfx.noise(0.08, 0.12, 'lowpass', 900, 300),
    stamp: () => { L.sfx.noise(0.16, 0.5, 'lowpass', 1400, 90); L.sfx.tone('sine', 150, 55, 0.18, 0.4); },
    spin: () => { L.sfx.noise(0.5, 0.1, 'bandpass', 900, 2600, null, 0, 4); L.sfx.tone('square', 1200, 1900, 0.04, 0.03); },
    catch: () => { L.sfx.tone('square', 2400, 1800, 0.03, 0.06); L.sfx.noise(0.05, 0.15, 'highpass', 3000, 2000); },
    blow: () => L.sfx.noise(0.35, 0.08, 'bandpass', 700, 400, null, 0, 2),
    tick: () => { L.sfx.noise(0.06, 0.12, 'highpass', 2500, 4000); L.sfx.noise(0.05, 0.1, 'highpass', 3000, 4500, null, 0.07); },
    flip: () => L.sfx.noise(0.18, 0.12, 'bandpass', 2200, 900, null, 0, 1.5),
    pop: () => { L.sfx.tone('sine', 900, 200, 0.06, 0.2); L.sfx.noise(0.05, 0.2, 'highpass', 2000, 1000); },
  };
  const rigAt = new THREE.Vector3(), rigQ = new THREE.Quaternion(), rigE = new THREE.Euler();
  for (const [k, o] of Object.entries(npcs)) {
    L.glb('x_lobby_' + k, () => {
      if (o.rig) return;
      const R = npcRig('x_lobby_' + k, L.tex, () => !L.potato());
      if (!R) return;
      const P = R.meta.place || {}, prop = PROPS[P.prop];
      const at = Array.isArray(P.at) && P.at.length === 3 && P.at.every(Number.isFinite) ? P.at : [0, 0, 0];
      const hold = new THREE.Group();
      if (prop) { prop.updateMatrixWorld(true); hold.position.copy(rigAt.set(...at).applyMatrix4(prop.matrixWorld)); prop.getWorldQuaternion(rigQ); hold.rotation.y = rigE.setFromQuaternion(rigQ, 'YXZ').y + (Number.isFinite(P.yaw) ? P.yaw : 0); }
      else { hold.position.set(o.n.at[0], o.n.sit ? 1.2 : 0, o.n.at[1]); hold.rotation.y = o.n.yaw; }
      hold.add(R.root); root.add(hold);
      R.baseYaw = hold.rotation.y; R.onMark = (m) => { try { if (SND[m]) SND[m](); } catch { /* (no audio yet) */ } };
      o.rig = R; o.hold = hold; o.gT = 6 + Math.random() * 8;
      o.ch.root.visible = false;
    });
  }
  const zomBub = { bub: L.tag('bub', ''), t: 0 }; zomBub.bub.style.display = 'none';
  function say(o, line, who) { o.bub.innerHTML = `<small>${who}</small>`; o.bub.append(document.createTextNode(line)); o.bub.style.display = ''; o.bubT = 3.2; if (o.rig) o.rig.talk(Math.min(3, 0.9 + line.length * 0.05)); }
  // ---- the picker: the choices next to the NPC, the same data and setting as CUSTOMIZE > LOADOUT > ZOMBIES
  const css = document.createElement('style'); css.textContent = `
#lsTags .ls-pick { pointer-events: auto; left: auto !important; right: clamp(34px, 5vmin, 58px); top: clamp(220px, 33vh, 250px) !important; transform: rotate(0.6deg) !important; width: min(320px, 34vw); max-height: 52vh; overflow: auto; background: rgba(18,8,24,.94); border: 4px solid #39ff14; box-shadow: 8px 8px 0 #ff4fd8; padding: 8px 10px 10px; color: #fff; font-family: var(--font); transform-origin: 0 100%; }
#lsTags .ls-pick h4 { margin: 0 0 6px; font-size: 15px; letter-spacing: 2px; color: #39ff14; display: flex; justify-content: space-between; }
#lsTags .ls-pick h4 i { font-style: normal; color: #aaa; font-size: 11px; letter-spacing: 1px; }
#lsTags .ls-pick button { display: block; width: 100%; text-align: left; margin: 0 0 5px; padding: 4px 8px; font: 700 13px var(--font); color: #120818; background: #fff; border: 3px solid #000; box-shadow: 3px 3px 0 var(--c, #ff4fd8); cursor: pointer; }
#lsTags .ls-pick button b { display: block; font-size: 14px; }
#lsTags .ls-pick button small { display: block; font-size: 11px; color: #444; font-weight: 400; }
#lsTags .ls-pick button.on { background: #ffe14d; transform: rotate(-1deg); }`;
  document.head.append(css);
  const panel = L.tag('ls-pick', ''); panel.style.display = 'none';
  let open = null;
  const zl0 = () => (G.settings.zload = zmValidLoadout(G.settings.zload, ITEMS));
  const CHOICES = {
    deb: { k: 'perk', list: () => Object.entries(ZM_PASSIVES).map(([id, p]) => [id, p.name, p.desc, p.color]) },
    gus: { k: 'pistol', list: () => Object.entries(ZM_PISTOLS).map(([id, p]) => [id, WEAPONS[id] ? WEAPONS[id].name : id, (p.ammo == null ? 'never runs out. ' : p.ammo + ' rounds. ') + p.tip, (WEAPONS[id] && WEAPONS[id].color) || '#ffe14d']) },
    marge: { k: 'item', list: () => ITEM_ORDER.map((id) => [id, ITEMS[id].name, ITEMS[id].desc, ITEMS[id].color]) },
  };
  function openPick(k) {
    if (open === k) { closePick(); return; }
    open = k; const n = NPC[k], C = CHOICES[k], cur = zl0()[C.k];
    panel.innerHTML = `<h4>${n.what}<i>${n.name} · E closes</i></h4>`;
    for (const [id, name, desc, col] of C.list()) {
      const b = document.createElement('button'); b.className = id === cur ? 'on' : ''; b.style.setProperty('--c', col || '#ff4fd8');
      const bn = document.createElement('b'); bn.textContent = name; const sm = document.createElement('small'); sm.textContent = desc; b.append(bn, sm);
      b.addEventListener('click', (e) => { e.stopPropagation(); choose(k, id, name); });
      panel.append(b);
    }
    panel.style.display = '';
    say(npcs[k], pick(n.hi), n.name);
    const hp = npcs[k].rig && npcs[k].rig.head ? npcs[k].rig.head.getWorldPosition(_v) : null;
    const c = L.cur(); if (c.walk) c.camFocus = { at: hp ? [hp.x, hp.y - 0.15, hp.z] : [n.at[0], n.sit ? 3.3 : 2.3, n.at[1]], t: c.camFocus && c.camFocus.talk ? 1 : 0, dur: 1e9, back: -1.2, talk: true }; // (over your shoulder at them while you talk)
    try { L.sfx.tone('square', 520, 780, 0.06, 0.05); } catch { /* (no audio yet) */ }
  }
  function closePick() { open = null; panel.style.display = 'none'; const c = L.cur(), F = c.camFocus; if (F && F.talk) { F.t = Math.max(F.t, 0.35); F.dur = F.t + 0.45; } }
  function choose(k, id, name) {
    const C = CHOICES[k], cur = zl0();
    G.settings.zload = zmValidLoadout({ ...cur, [C.k]: id }, ITEMS);
    const sv = L.cur().ask.save; if (sv) sv();
    if (G.joined) net.send({ t: 'zload', zl: G.settings.zload });
    const n = NPC[k];
    say(npcs[k], n.got[id] || pick([`${name}. good choice, dear.`, `${name}. sure. why not.`, `${name}. bring it back in one piece.`]), n.name);
    try { L.sfx.tone('square', 660, 990, 0.08, 0.06); L.sfx.tone('square', 990, 1320, 0.08, 0.05, null, 0.08); } catch { /* (no audio yet) */ }
    open = null; openPick(k); // (redraw with the new pick lit)
    say(npcs[k], n.got[id] || pick([`${name}. good choice, dear.`, `${name}. sure. why not.`, `${name}. bring it back in one piece.`]), n.name); // (openPick said hi again: the reaction wins)
    if (npcs[k].rig) npcs[k].rig.gesture(); // (Deb stamps it, Gus spins one, Marge ticks it off)
  }
  // ---- lights: a dim warm room, the windows' green, a pool of light at each station
  S.add(new THREE.HemisphereLight(0xa8c0a8, 0x2a2018, 1.5));
  const key = new THREE.DirectionalLight(0xffe8c8, 1.5); key.position.set(4, 12, 10); key.target.position.set(0, 0, -2); S.add(key, key.target);
  if (L.shadows()) { key.castShadow = true; key.shadow.mapSize.set(potato ? 512 : 2048, potato ? 512 : 2048); Object.assign(key.shadow.camera, { left: -18, right: 18, top: 16, bottom: -16, near: 1, far: 40 }); key.shadow.bias = -0.0005; key.shadow.normalBias = 0.03; }
  for (const [x, z] of [[-8.5, -6.5], [0, -9], [9.5, -7]]) { const l = new THREE.SpotLight(0xffd090, 320, 14, 0.75, 0.6, 1.3); l.position.set(x, 7.5, z + 1.5); l.target.position.set(x, 0, z); S.add(l, l.target); }
  const spots = [{ x: 0, z: 6, yaw: 0 }, { x: -4.5, z: 4.5, yaw: 0.6 }, { x: 4.5, z: 4.5, yaw: -0.6 }, { x: 2.5, z: 9, yaw: -0.3 }];
  const walk = {
    spawn: [0, 6, 0, 0], bounds: [-17.2, -13.7, 17.2, 11.6], solids: SOL, camBox: [-17, 0.5, -13.5, 17, 8.4, 11.6], dist: 5,
    wander: [[-4, 2], [4, 2], [0, -4], [-10, 2], [10, 2], [-12, -3], [12, -4], [0, 8], [-8, 9], [8, 6]],
    use: [
      { at: [-8.2, 1.6, -6.0], r: 2.6, label: () => 'TALK TO DEB (PASSIVES)', act: () => openPick('deb') },
      { at: [0, 1.6, -8.4], r: 2.4, label: () => 'TALK TO GUS (PISTOLS)', act: () => openPick('gus') },
      { at: [8.6, 1.8, -6.6], r: 2.6, label: () => 'TALK TO MARGE (THE ITEM)', act: () => openPick('marge') },
      { at: [-6, 1.6, 4], r: 3, label: () => 'POKE THE ZOMBIE', act: poke },
    ],
  };
  const _v = new THREE.Vector3();
  return {
    spots, walk, inviteH: 1.3,
    focus: { at: new THREE.Vector3(0, 1.6, -2), top: new THREE.Vector3(0, 4.5, -10), bot: new THREE.Vector3(0, 0, 6), w: 12, dir: new THREE.Vector3(0, 0.25, 1).normalize(), fov: 40 },
    update(dt, t) {
      const me = L.cur().walk && L.cur().walk.me;
      for (const h of hands) { h.ph += dt; h.h.rotation.y = Math.sin(h.ph * 2.3) * 0.35; h.h.rotation.x = Math.sin(h.ph * 1.7) * 0.25; h.palm.rotation.x = Math.max(0, Math.sin(h.ph * 4)) * 0.8; }
      for (const b of bulbs) b.visible = Math.random() > 0.004; // (a bulb blinks out now and then)
      gen.position.x = 13.5 + (Math.random() - 0.5) * 0.012; gen.rotation.z = (Math.random() - 0.5) * 0.004; // (the generator chugs)
      if (npcs.deb && npcs.deb.rig) stamp.visible = false; // (Deb has it in her hand now)
      else stamp.position.y = stampY + Math.max(0, Math.sin(t * 3.1)) * 0.18; // (Deb stamps things)
      // the NPCs: idle, look at you when you're close, say hi once as you walk up
      for (const [k, o] of Object.entries(npcs)) {
        const n = o.n, d = me ? Math.hypot(me.pos[0] - n.at[0], me.pos[2] - n.at[1]) : 99;
        if (o.rig) { // the Blender one: clips + a head turn your way; a gesture now and then while nobody's chatting
          if (d < 7 && me) _v.set(me.pos[0], me.pos[1] + 2.05, me.pos[2]);
          o.rig.update(dt, d < 7 && me ? _v : null);
          if (!o.rig.busy() && open !== k && !(o.bubT > 0) && (o.gT -= dt) <= 0) { o.rig.gesture(); o.gT = 9 + Math.random() * 9; }
          if (d < 4.5 && o.hiT <= 0 && !open) { say(o, pick(n.hi), n.name); o.hiT = 14; } else if (d > 6) o.hiT = Math.min(o.hiT, 2);
          o.hiT -= dt;
          if (o.bubT > 0) { o.bubT -= dt; if (o.bubT <= 0) o.bub.style.display = 'none'; }
          continue;
        }
        o.t += dt; idlePose(o.ch, o.t);
        const want = d < 7 && me ? Math.atan2(-(me.pos[0] - n.at[0]), -(me.pos[2] - n.at[1])) : n.yaw; // (characters face -z at yaw 0)
        let dd = want - o.face; dd = Math.atan2(Math.sin(dd), Math.cos(dd)); o.face += dd * Math.min(1, dt * 3); o.ch.root.rotation.y = o.face;
        if (k === 'deb') { o.ch.arm.rotation.set(-0.9 + Math.max(0, Math.sin(t * 3.1)) * 0.5, 0, 0); o.ch.armL.rotation.set(-1.3, 0, -0.1); }
        if (k === 'gus') { o.ch.arm.rotation.set(-0.5 + Math.sin(o.t * 5) * 0.06, 0.4, 0); o.ch.armL.rotation.set(-0.7 + Math.sin(o.t * 5) * 0.15, -0.5, 0.2); } // (polishing it)
        if (k === 'marge') { o.ch.legL.rotation.x = o.ch.legR.rotation.x = 1.45; o.ch.kneeL.rotation.x = o.ch.kneeR.rotation.x = -1.5; o.ch.arm.rotation.set(-0.6 + Math.sin(o.t * 7) * 0.12, 0.5, 0); o.ch.armL.rotation.set(-0.6 - Math.sin(o.t * 7) * 0.12, -0.5, 0); } // (knitting)
        if (d < 4.5 && o.hiT <= 0 && !open) { say(o, pick(n.hi), n.name); o.hiT = 14; } else if (d > 6) o.hiT = Math.min(o.hiT, 2);
        o.hiT -= dt;
        if (o.bubT > 0) { o.bubT -= dt; if (o.bubT <= 0) o.bub.style.display = 'none'; }
      }
      if (open && me) { const n = NPC[open]; if (Math.hypot(me.pos[0] - n.at[0], me.pos[2] - n.at[1]) > 4.5) closePick(); }
      // the practice zombie: shuffles round its post on the chain, flails when poked
      zom.t += dt; zom.a += dt * 0.35;
      const zx = -6 + Math.cos(zom.a) * 1.6, zz = 4 + Math.sin(zom.a) * 1.6;
      zch.root.position.set(zx, 0, zz); zch.root.rotation.y = -zom.a + (zom.flail > 0 ? Math.sin(zom.t * 25) * 0.5 : 0);
      idlePose(zch, zom.t * 2.2);
      zch.legL.rotation.x = Math.sin(zom.t * 3) * 0.35; zch.legR.rotation.x = -Math.sin(zom.t * 3) * 0.35; zch.body.rotation.z = Math.sin(zom.t * 1.5) * 0.12;
      const fl = zom.flail > 0 ? Math.sin(zom.t * 30) * 0.8 : 0;
      zch.arm.rotation.set(-0.15 + fl, 0, 0.1); zch.armL.rotation.set(-0.2 - fl, 0, -0.1); zch.head.rotation.z = 0.5;
      if (zom.flail > 0) zom.flail -= dt;
      chain.position.set((zx - 6) / 2, 0.9, (zz + 4) / 2); chain.lookAt(-6, 0.9, 4); chain.rotateX(Math.PI / 2); chain.scale.y = Math.hypot(zx + 6, zz - 4);
      if (zomBub.bubT > 0) { zomBub.bubT -= dt; if (zomBub.bubT <= 0) zomBub.bub.style.display = 'none'; }
    },
    tags() {
      for (const o of Object.values(npcs)) if (o.bub.style.display !== 'none') { if (o.rig && o.rig.head) { o.rig.head.getWorldPosition(_v); _v.y += 0.62; } else _v.set(o.n.at[0], o.n.sit ? 3.5 : 2.75, o.n.at[1]); L.at(o.bub, _v); }
      if (zomBub.bub.style.display !== 'none') { _v.copy(zch.root.position); _v.y = 2.8; L.at(zomBub.bub, _v); }
    },
    info: () => ({ open, zload: zl0(), rigs: Object.keys(npcs).filter((k) => npcs[k].rig), clip: Object.fromEntries(Object.entries(npcs).filter(([, o]) => o.rig).map(([k, o]) => [k, o.rig.want])), ink: Object.values(npcs).filter((o) => o.rig && o.rig.ink.visible).length }),
    dispose() { css.remove(); for (const o of Object.values(npcs)) if (o.rig) o.rig.dispose(); },
  };
}

// brick: rows of rough bricks with mortar, tiny and crunchy
function brickTex(L) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 64; const g = cv.getContext('2d');
  g.fillStyle = '#3a2a24'; g.fillRect(0, 0, 64, 64);
  for (let y = 0; y < 8; y++) for (let x = -1; x < 5; x++) { const k = 0.8 + Math.random() * 0.35; g.fillStyle = `rgb(${(122 * k) | 0},${(58 * k) | 0},${(44 * k) | 0})`; g.fillRect(x * 16 + (y % 2) * 8 + 1, y * 8 + 1, 14, 6); }
  const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(8, 3); t.colorSpace = THREE.SRGBColorSpace; return L.tex(t);
}
function pegTex(L) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 32; const g = cv.getContext('2d');
  g.fillStyle = '#c8a878'; g.fillRect(0, 0, 32, 32); g.fillStyle = '#5a4020'; for (let y = 2; y < 32; y += 4) for (let x = 2; x < 32; x += 4) g.fillRect(x, y, 1, 1);
  const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(5, 3); t.colorSpace = THREE.SRGBColorSpace; return L.tex(t);
}
// the tally wall: ROUNDS SURVIVED in chalk and a lot of little gates of five
function tallyTex(L) {
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 205; const g = cv.getContext('2d');
  g.fillStyle = '#22201c'; g.fillRect(0, 0, 512, 205);
  g.fillStyle = '#e8e8d8'; g.font = '900 30px "Comic Neue", sans-serif'; g.fillText('ROUNDS SURVIVED', 16, 36);
  g.strokeStyle = '#e8e8d8'; g.lineWidth = 3;
  let x = 18, y = 60;
  for (let n = 0; n < 37; n++) {
    const i = n % 5;
    if (i < 4) { g.beginPath(); g.moveTo(x + i * 9, y); g.lineTo(x + i * 9 + (Math.random() - 0.5) * 3, y + 34); g.stroke(); }
    else { g.beginPath(); g.moveTo(x - 4, y + 30); g.lineTo(x + 32, y + 4); g.stroke(); x += 50; if (x > 470) { x = 18; y += 48; } }
  }
  g.fillStyle = '#ff4fd8'; g.font = '700 18px "Comic Neue", sans-serif'; g.fillText('(gary counted twice)', 300, 190);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return L.tex(t);
}
