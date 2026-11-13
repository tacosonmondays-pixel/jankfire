// QUICK PLAY and PLANT & DEFUSE's lobby: the staging hangar (docs/menu/LOBBY_SCENES.md). a moody line-up: your party
// in a shallow V, you in front, nameplates, pink and cyan rim lights, hazard tape, crates and sandbags, a big screen
// with the mode on it, and a rack with your loadout's guns (your skins) under it. PLANT & DEFUSE: a briefing table
// with the bomb on it and the screen says BOMB TIME. the camera drifts.
import * as THREE from 'three';
import { buildWeapon, freeTree } from '../models.js';
import { WEAPONS } from '/shared/weapons.js';

export function build(L) {
  const { G } = L, S = L.cur().scene, root = new THREE.Group(); S.add(root);
  const potato = L.potato();
  S.background = new THREE.Color(0x0a0810);
  S.fog = new THREE.Fog(0x0a0810, 12, 34);
  const flat = (o) => { o.castShadow = false; return o; };
  const conc = L.mat(0x3a3842, 0.5, 0.15); conc.map = L.speck(0x46444e, 14);
  flat(L.box(root, 34, 0.2, 26, conc, 0, -0.1, -5));
  const wall = L.mat(0x18161e, 0.9); wall.map = L.speck(0x221e2a, 6, true);
  flat(L.box(root, 34, 12, 0.4, wall, 0, 6, -11));
  const steel = L.mat(0x2a2c34, 0.42, 0.75);
  for (let i = -3; i <= 3; i++) if (i) flat(L.box(root, 0.35, 12, 0.5, steel, i * 4.5, 6, -10.7)); // (none in front of the screen)
  const tape = L.mat(0xffffff, 0.6); tape.map = L.stripes(30);
  flat(L.box(root, 14, 0.02, 0.3, tape, 0, 0.012, 0.4)); flat(L.box(root, 14, 0.02, 0.3, tape, 0, 0.012, -4.6));
  // ---- the big screen: the mode in pink, a scanline flicker
  const scrBox = L.box(root, 4.9, 1.45, 0.2, L.mat(0x111111, 0.4, 0.6), 0, 3.35, -10.75); scrBox.castShadow = false;
  let scrTex = null, scrFor = '';
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 1.15), L.basic(0xffffff)); scr.position.set(0, 3.35, -10.63); root.add(scr);
  function screen(mode) {
    const txt = mode === 'bomb' ? 'BOMB TIME' : 'QUICK PLAY';
    if (txt === scrFor) return; scrFor = txt;
    if (scrTex) scrTex.dispose();
    scrTex = L.label(txt, { bg: '#120818', fg: mode === 'bomb' ? '#ffb04f' : '#ff4fd8', border: null, w: 512, h: 128 });
    scr.material.map = scrTex; scr.material.needsUpdate = true;
  }
  // ---- the rack: your primary, secondary and melee on hooks (rebuilt when the loadout changes)
  const rack = new THREE.Group(); rack.position.set(5.2, -0.5, -10.4); rack.rotation.y = -0.2; root.add(rack); // (on the back wall, right of the screen)
  const rkG = new THREE.Group(); rack.add(rkG); // (boxes until the Blender rack lands)
  L.box(rkG, 4.4, 2.2, 0.15, L.mat(0x2a2430, 0.7), 0, 2.3, 0).castShadow = false;
  L.box(rkG, 4.6, 0.1, 0.35, L.mat(0xffc21a, 0.4, 0.3), 0, 1.15, 0.15);
  const guns = new THREE.Group(); rack.add(guns);
  let gunKey = '';
  function rackGuns() {
    const lo = G.settings.loadout || {}, ids = [lo.primary, lo.secondary, lo.melee].map((id) => (WEAPONS[id] ? id : null));
    const k = JSON.stringify([ids, ids.map((id) => id && G.equipped && G.equipped[id])]);
    if (k === gunKey) return; gunKey = k;
    freeTree(guns); guns.clear();
    ids.forEach((id, i) => { if (!id) return; try { const w = buildWeapon(id, G.equipped && G.equipped[id]); w.scale.setScalar(2.1); w.rotation.y = Math.PI / 2; w.position.set(-1.4 + i * 1.4, 2.4, 0.25); w.traverse((o) => { if (o.isMesh) o.castShadow = true; }); guns.add(w); } catch { /* (no model) */ } });
  }
  rackGuns();
  // the Blender screen frame and gun rack (x_lobby_hangarprops): the jumbotron's housing, bezel, speakers, LIVE light and
  // ticker round the mode screen (the screen itself stays the plane above), the armory rack under your guns
  L.glb('x_lobby_hangarprops', (o) => {
    const take = (n) => { const m = o.getObjectByName(n); if (m) { m.position.set(0, 0, 0); m.traverse((x) => { if (x.isMesh) { x.castShadow = !/cable/.test(x.name); x.receiveShadow = true; } }); } return m; };
    const sf = take('screenframe'); if (sf) { sf.position.set(0, 3.35, -10.75); root.add(sf); scrBox.visible = false; }
    const gr = take('gunrack'); if (gr) { freeTree(rkG); rkG.clear(); rkG.add(gr); }
  });
  // ---- props: crates, a pallet, sandbags (the map props), a cone, a briefing table for PLANT & DEFUSE
  const prop = (id, at, ry = 0, y = 0) => L.glb(id, (o) => { const l1 = o.getObjectByName('lod1'); if (l1) l1.visible = false; o.position.set(at[0], y, at[1]); o.rotation.y = ry; o.traverse((m) => { if (m.isMesh) m.castShadow = m.receiveShadow = true; }); root.add(o); });
  prop('p_crate', [6.2, -7.2], 0.2); prop('p_crate', [7.5, -6.2], -0.3); prop('p_crate', [6.6, -7.0], 0.5, 1.2);
  prop('p_pallet_load', [-7.5, -5], 0.3); prop('p_sandbags', [8.4, -2.2], -0.8); prop('p_cone', [-5.2, -1.6]); prop('p_barrel', [-8.6, -7.6]);
  const brief = new THREE.Group(); brief.position.set(-4.4, 0, -6.2); brief.rotation.y = 0.35; root.add(brief);
  L.box(brief, 2.4, 0.08, 1.3, L.mat(0x3a3a40, 0.5, 0.4), 0, 0.9, 0); for (const [x, z] of [[-1.1, -0.55], [1.1, -0.55], [-1.1, 0.55], [1.1, 0.55]]) L.box(brief, 0.08, 0.9, 0.08, steel, x, 0.45, z);
  const mapPrint = L.mat(0xffffff, 0.8); mapPrint.map = L.label('SITE A  ·  SITE B', { bg: '#d8d0b8', fg: '#2a2430', border: '#2a2430', w: 256, h: 128 }); L.box(brief, 1.3, 0.01, 0.8, mapPrint, -0.4, 0.95, 0).castShadow = false;
  const bomb = new THREE.Group(); bomb.position.set(0.75, 0.95, 0.1); brief.add(bomb);
  L.box(bomb, 0.45, 0.22, 0.3, L.mat(0x4a5a3a, 0.6), 0, 0.11, 0); for (let i = 0; i < 3; i++) L.cyl(bomb, 0.05, 0.05, 0.42, L.mat(0xc04020, 0.5), 0, 0.27, -0.09 + i * 0.09, 8).rotation.z = Math.PI / 2;
  const led = L.box(bomb, 0.06, 0.04, 0.06, L.basic(0xff3030), 0.16, 0.24, 0.12);
  // ---- lights: one hard key from above-front, pink and cyan rims from behind, the screen's glow
  S.add(new THREE.HemisphereLight(0x50406a, 0x0a0610, 0.7));
  const key = new THREE.SpotLight(0xfff0e0, 170, 26, 0.5, 0.7, 1.4); key.position.set(-2, 9, 6); key.target.position.set(0, 0, -2); S.add(key, key.target);
  if (L.shadows()) { key.castShadow = true; key.shadow.mapSize.set(potato ? 512 : 1024, potato ? 512 : 1024); key.shadow.bias = -0.0006; }
  const pk = new THREE.PointLight(0xff4fd8, 46, 11); pk.position.set(-4, 2.2, -4.5); S.add(pk);
  const cy = new THREE.PointLight(0x4fd8ff, 46, 11); cy.position.set(4, 2.2, -4.5); S.add(cy);
  const sl = new THREE.PointLight(0xff4fd8, 22, 9); sl.position.set(0, 1.4, -8.4); S.add(sl);
  // the line-up: a shallow V, you at the point (up to 6; fill 3: you and two places)
  const spots = [{ x: 0, z: -1.2, ry: 0 }, { x: -1.25, z: -1.9, ry: 0.1 }, { x: 1.25, z: -1.9, ry: -0.1 }, { x: -2.45, z: -2.6, ry: 0.18 }, { x: 2.45, z: -2.6, ry: -0.18 }, { x: 0, z: -3.0, ry: 0 }];
  return {
    spots, fill: 3, inviteH: 1.3,
    focus: { at: new THREE.Vector3(0, 1.15, -1.6), top: new THREE.Vector3(0, 2.5, -1.9), bot: new THREE.Vector3(0, 0, -1.0), w: 4.0, min: 4.8, dir: new THREE.Vector3(0, 0.1, 1).normalize(), fov: 38, drift: 0.07 },
    inviteSpot(wrap) { wrap.userData.lsPick = 'invite'; const m = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 1.8, 10, 1, true), L.basic(0x4fd8ff, { transparent: true, opacity: 0.14, depthWrite: false, side: THREE.DoubleSide })); m.position.y = 0.9; wrap.add(m); },
    update(dt, t) {
      const mode = L.mode;
      screen(mode); brief.visible = mode === 'bomb';
      if ((t * 2 | 0) !== ((t - dt) * 2 | 0)) rackGuns(); // (twice a second: a new loadout or skin goes on the rack)
      scr.material.color.setScalar(0.85 + Math.sin(t * 40) * 0.04 + (Math.random() < 0.01 ? -0.3 : 0)); // (it flickers)
      led.visible = Math.sin(t * 6) > 0;
    },
    info: () => ({ screen: scrFor, rack: guns.children.length, brief: brief.visible }),
    dispose() { if (scrTex) scrTex.dispose(); },
  };
}
