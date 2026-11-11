// Act I encounter stand-ins, built in code (chunky low-poly boxes and lathes, like the cast's code puppets) until the
// art lane's models land: the Unpaid's desk war-rig, the stomach-dog, an intern's lanyard and laptop shield, the soup
// pot that rides in your car, the Unpaid's desk barricade and the Gristle & Sons trade post. each is a THREE.Group with
// its parts named so the encounter code can wiggle them (wheels, legs, jaw, soup).
import * as THREE from 'three';

const MATS = new Map();
const M = (c, o = {}) => { const k = c + JSON.stringify(o); if (!MATS.has(k)) MATS.set(k, new THREE.MeshStandardMaterial({ color: c, roughness: o.r ?? 0.6, metalness: o.m ?? 0, flatShading: true, emissive: o.e ?? 0x000000, emissiveIntensity: o.ei ?? 0 })); return MATS.get(k); };
function box(g, w, h, d, c, x, y, z, o = {}) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c, o)); m.position.set(x, y, z); if (o.rx) m.rotation.x = o.rx; if (o.ry) m.rotation.y = o.ry; if (o.rz) m.rotation.z = o.rz; m.castShadow = true; g.add(m); return m; }
function cyl(g, r0, r1, h, c, x, y, z, o = {}) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, o.seg || 10), M(c, o)); m.position.set(x, y, z); if (o.rx) m.rotation.x = o.rx; if (o.rz) m.rotation.z = o.rz; g.add(m); return m; }
function label(text, w = 512, h = 96, bg = '#ffe14d', fg = '#120818') {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const x = c.getContext('2d'); x.fillStyle = bg; x.fillRect(0, 0, w, h); x.strokeStyle = fg; x.lineWidth = 8; x.strokeRect(4, 4, w - 8, h - 8);
  x.font = `bold ${Math.round(h * 0.52)}px "Comic Neue", cursive`; x.fillStyle = fg; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(text, w / 2, h / 2 + 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshBasicMaterial({ map: t, side: THREE.DoubleSide });
}

// an office desk: a top and four legs (or a drawer pedestal)
function desk(g, x, y, z, ry = 0, s = 1) {
  const d = new THREE.Group(); d.position.set(x, y, z); d.rotation.y = ry; d.scale.setScalar(s); g.add(d);
  box(d, 1.6, 0.06, 0.8, 0xc8a46a, 0, 0.74, 0, { r: 0.5 }); // the beech-effect top
  box(d, 0.42, 0.7, 0.74, 0x9aa2ac, 0.55, 0.36, 0, { m: 0.4, r: 0.4 }); // drawers
  for (const k of [0.16, 0.36, 0.56]) box(d, 0.3, 0.03, 0.02, 0x3a3a44, 0.55, k, 0.38);
  for (const lx of [-0.74]) for (const lz of [-0.34, 0.34]) box(d, 0.05, 0.7, 0.05, 0x5a5f68, lx, 0.36, lz, { m: 0.5 });
  return d;
}
// a cubicle partition panel: fabric in a metal frame, covered in sticky notes
function partition(g, w, h, x, y, z, ry = 0) {
  const p = new THREE.Group(); p.position.set(x, y, z); p.rotation.y = ry; g.add(p);
  box(p, w, h, 0.08, 0x6a7a96, 0, h / 2, 0, { r: 0.95 });
  box(p, w + 0.06, 0.06, 0.1, 0xb0b4bc, 0, h, 0, { m: 0.5 });
  for (const sx of [-1, 1]) box(p, 0.06, h, 0.1, 0xb0b4bc, sx * w / 2, h / 2, 0, { m: 0.5 });
  const notes = [0xffe14d, 0xff4fd8, 0x7dff4f, 0x4fd8ff];
  for (let i = 0; i < 7; i++) box(p, 0.14, 0.14, 0.02, notes[i % 4], (Math.sin(i * 7.3) * 0.4) * w, h * (0.35 + ((i * 0.37) % 0.55)), 0.05, { rz: Math.sin(i) * 0.3 });
  return p;
}
function chair(g, x, y, z, ry = 0) { // an office chair: five-star base, gas lift, seat, back
  const c = new THREE.Group(); c.position.set(x, y, z); c.rotation.y = ry; g.add(c);
  for (let i = 0; i < 5; i++) box(c, 0.05, 0.04, 0.32, 0x26262c, Math.sin(i * 1.2566) * 0.16, 0.05, Math.cos(i * 1.2566) * 0.16, { ry: i * 1.2566 });
  cyl(c, 0.03, 0.03, 0.38, 0x8a9098, 0, 0.26, 0, { m: 0.6 });
  box(c, 0.48, 0.08, 0.46, 0x1e1e22, 0, 0.48, 0);
  box(c, 0.44, 0.52, 0.07, 0x1e1e22, 0, 0.78, -0.22, { rx: -0.1 });
  return c;
}

// THE UNPAID WAR-RIG: a cubicle bolted to a shopping trolley the size of a van (5.1 x 2 x 2.4, the 'van' it drives as).
// front is +z (the way it drives). parts: wheels[], gun, banner
export function rigMesh() {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  // the trolley: a wire basket on a chassis (bars, not a box)
  const wire = 0x9aa2ac, red = 0xd8323c;
  box(body, 2.0, 0.12, 5.0, 0x3a3a44, 0, 0.55, 0, { m: 0.5 }); // chassis
  for (let i = 0; i <= 8; i++) box(body, 0.04, 1.0, 0.04, wire, -0.98, 1.05, -2.45 + i * 0.61, { m: 0.7, r: 0.3 });
  for (let i = 0; i <= 8; i++) box(body, 0.04, 1.0, 0.04, wire, 0.98, 1.05, -2.45 + i * 0.61, { m: 0.7, r: 0.3 });
  for (const y of [0.85, 1.55]) for (const sx of [-1, 1]) box(body, 0.05, 0.05, 4.95, wire, sx * 0.98, y, 0, { m: 0.7, r: 0.3 });
  box(body, 2.0, 0.08, 0.08, red, 0, 1.6, 2.5, { r: 0.4 }); // the red plastic trim
  box(body, 1.4, 0.12, 0.3, red, 0, 1.75, -2.75); box(body, 0.1, 0.5, 0.1, wire, -0.7, 1.45, -2.6, { m: 0.7 }); box(body, 0.1, 0.5, 0.1, wire, 0.7, 1.45, -2.6, { m: 0.7 }); // the handle
  // the cubicle on top: two desks, partitions as armour, a chair for the gunner
  desk(body, -0.45, 0.62, 0.9, Math.PI / 2, 0.95); desk(body, 0.45, 0.62, -0.6, -Math.PI / 2, 0.95);
  partition(body, 1.9, 1.3, 0, 0.62, 2.35); // the ram plate: a partition across the nose
  partition(body, 2.0, 1.1, -0.98, 1.6, 0, Math.PI / 2); partition(body, 2.0, 1.1, 0.98, 1.6, 0, Math.PI / 2);
  chair(body, 0, 1.38, -1.4, Math.PI);
  box(body, 0.5, 0.75, 0.5, 0x4fd8ff, 0.6, 1.0, -2.0, { r: 0.1, m: 0.1 }); // the water cooler (it's the fuel tank)
  cyl(body, 0.18, 0.12, 0.4, 0xbfe8ff, 0.6, 1.58, -2.0, { r: 0.05 });
  // the minigun on the partition, and the banner
  const gun = new THREE.Group(); gun.position.set(0, 2.2, 1.2); body.add(gun);
  for (let i = 0; i < 6; i++) cyl(gun, 0.035, 0.035, 1.1, 0x2a2a30, Math.cos(i * 1.047) * 0.08, Math.sin(i * 1.047) * 0.08, 0.5, { rx: Math.PI / 2, m: 0.7, r: 0.3 });
  box(gun, 0.3, 0.3, 0.45, 0x3a3a44, 0, 0, -0.1, { m: 0.6 }); box(gun, 0.06, 0.25, 0.25, 0xffe14d, 0.2, 0, -0.1);
  const ban = new THREE.Mesh(new THREE.PlaneGeometry(2.1, 0.42), label("WE'RE DISRUPTING")); ban.position.set(0, 2.15, 2.42); body.add(ban);
  box(body, 0.32, 0.5, 0.32, 0xff7a1a, -0.7, 1.95, 1.9); box(body, 0.4, 0.06, 0.4, 0xff7a1a, -0.7, 1.7, 1.9); // a traffic cone, a hat for it
  // the wheels: trolley casters, far too big
  const wheels = [];
  for (const [x, z] of [[-0.95, 1.9], [0.95, 1.9], [-0.95, -1.9], [0.95, -1.9]]) {
    const piv = new THREE.Group(); piv.position.set(x, 0.42, z); g.add(piv);
    box(piv, 0.12, 0.3, 0.3, 0x9aa2ac, 0, 0.2, 0, { m: 0.6 }); // the fork
    const sp = new THREE.Group(); piv.add(sp);
    const w = cyl(sp, 0.42, 0.42, 0.26, 0x1a1a1a, 0, 0, 0, { rz: Math.PI / 2, seg: 12 }); cyl(sp, 0.2, 0.2, 0.28, red, 0, 0, 0, { rz: Math.PI / 2, seg: 8 }); w.castShadow = true;
    wheels.push({ piv, sp, steer: z > 0 });
  }
  g.userData = { body, wheels, gun, T: { L: 5.1, W: 2.0, H: 2.4 } };
  return g;
}

// A STOMACH-DOG: a dog made mostly of stomach. pink, wet, a mouth where the oesophagus should be, four thin legs.
// front is +z. parts: legs[], jaw, tail
export function dogMesh() {
  const g = new THREE.Group(), pink = 0xe86a8a, deep = 0xa02a4a, wet = { r: 0.25, m: 0.05 };
  const belly = new THREE.Mesh(new THREE.SphereGeometry(0.55, 12, 9), M(pink, wet)); belly.scale.set(0.85, 0.7, 1.25); belly.position.set(0, 0.85, -0.05); g.add(belly);
  const crook = new THREE.Mesh(new THREE.SphereGeometry(0.34, 10, 8), M(pink, wet)); crook.position.set(0, 1.05, 0.52); g.add(crook); // the J of the stomach bends up into the neck
  for (let i = 0; i < 5; i++) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.42 - i * 0.02, 0.025, 5, 14), M(deep, wet)); r.position.set(0, 0.86, -0.45 + i * 0.22); g.add(r); } // the folds (rugae)
  const head = new THREE.Group(); head.position.set(0, 1.18, 0.82); g.add(head);
  cyl(head, 0.2, 0.3, 0.35, pink, 0, 0, 0, { rx: Math.PI / 2 - 0.3, ...wet });
  const jaw = new THREE.Group(); jaw.position.set(0, -0.08, 0.15); head.add(jaw);
  box(jaw, 0.36, 0.06, 0.36, deep, 0, -0.04, 0.12, wet);
  for (let i = 0; i < 6; i++) { box(head, 0.04, 0.09, 0.04, 0xfff4d8, -0.15 + i * 0.06, -0.02, 0.27); box(jaw, 0.04, 0.08, 0.04, 0xfff4d8, -0.15 + i * 0.06, 0.03, 0.27); }
  for (const sx of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.05, 6, 5), M(0xffe14d, { e: 0xffe14d, ei: 0.8 })); e.position.set(sx * 0.12, 0.13, 0.16); head.add(e); }
  const drool = box(jaw, 0.03, 0.22, 0.03, 0xd8ffd0, 0.08, -0.14, 0.26, { r: 0.1 }); drool.material = M(0xd8ffd0, { r: 0.1, e: 0x7dff4f, ei: 0.2 });
  const legs = [];
  for (const [x, z] of [[-0.3, 0.45], [0.3, 0.45], [-0.3, -0.5], [0.3, -0.5]]) {
    const hip = new THREE.Group(); hip.position.set(x, 0.7, z); g.add(hip);
    box(hip, 0.09, 0.42, 0.09, deep, 0, -0.2, 0, wet); const knee = new THREE.Group(); knee.position.set(0, -0.4, 0); hip.add(knee);
    box(knee, 0.07, 0.34, 0.07, deep, 0, -0.16, 0.04, wet); box(knee, 0.12, 0.05, 0.16, 0x5a1020, 0, -0.33, 0.07);
    legs.push({ hip, knee, ph: legs.length % 2 ? Math.PI : 0 });
  }
  const tail = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.05, 6, 12, Math.PI * 1.4), M(pink, wet)); tail.position.set(0, 1.0, -0.72); tail.rotation.y = Math.PI / 2; g.add(tail); // a bit of intestine for a tail
  g.userData = { legs, jaw, head, tail };
  return g;
}

// an intern's kit, hung on the mannequin: a lanyard, an office-chair back for armour, a laptop for a shield
export function internBits() {
  const g = new THREE.Group();
  box(g, 0.04, 0.42, 0.02, 0xffe14d, 0, 1.35, 0.17); box(g, 0.14, 0.18, 0.02, 0xffffff, 0, 1.12, 0.18); box(g, 0.1, 0.03, 0.025, 0xff4fd8, 0, 1.17, 0.19); // lanyard + INTERN badge
  box(g, 0.5, 0.6, 0.07, 0x1e1e22, 0, 1.3, -0.22); // the chair back
  const lap = new THREE.Group(); lap.position.set(-0.3, 1.1, 0.25); lap.rotation.set(-0.2, 0.3, 0.1); g.add(lap);
  box(lap, 0.36, 0.25, 0.025, 0x8a9098, 0, 0, 0, { m: 0.6, r: 0.3 }); box(lap, 0.08, 0.08, 0.03, 0xffffff, 0, 0, 0.012); // (a bitten-fruit-ish sticker, original: a pear)
  return g;
}

// the soup pot: sharon's big red pot of tomato, a lid that rattles, the soup level as a disc that sinks
export function potMesh() {
  const g = new THREE.Group();
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.3, 0.46, 16, 1, true), M(0xd8323c, { r: 0.35, m: 0.3 })); pot.material.side = THREE.DoubleSide; pot.position.y = 0.23; g.add(pot);
  cyl(g, 0.3, 0.3, 0.03, 0x8a2a2a, 0, 0.015, 0);
  for (const sx of [-1, 1]) box(g, 0.1, 0.04, 0.06, 0x2a2a30, sx * 0.38, 0.4, 0);
  const soup = new THREE.Mesh(new THREE.CircleGeometry(0.31, 16), M(0xe0401a, { r: 0.15, e: 0x601000, ei: 0.3 })); soup.rotation.x = -Math.PI / 2; soup.position.y = 0.42; g.add(soup);
  const lid = cyl(g, 0.36, 0.36, 0.03, 0xb0b4bc, 0, 0.48, 0, { m: 0.7, r: 0.3, seg: 16 }); cyl(lid, 0.05, 0.05, 0.05, 0x1e1e22, 0, 0.04, 0);
  g.userData = { soup, lid };
  return g;
}
export function potLevel(g, k) { const s = g.userData.soup; s.visible = k > 0.01; s.position.y = 0.05 + 0.37 * Math.max(0, Math.min(1, k)); }

// the Unpaid's roadblock: desks on their sides, partitions, an office plant, a banner across the road
export function barricadeMesh(width = 14) {
  const g = new THREE.Group();
  for (let x = -width / 2 + 1; x < width / 2; x += 1.9) { const d = desk(g, x, 0, 0, (x * 1.7) % 0.6, 1); d.rotation.z = Math.sin(x) > 0 ? Math.PI / 2 : 0; d.position.y = Math.sin(x) > 0 ? 0.8 : 0; }
  for (let x = -width / 2 + 2; x < width / 2; x += 3.7) partition(g, 1.8, 1.4, x, 0, -0.8, (x % 3) * 0.2);
  for (const x of [-width / 2 + 0.4, width / 2 - 0.4]) { box(g, 0.15, 3.4, 0.15, 0x5a5f68, x, 1.7, 0.6, { m: 0.5 }); }
  const ban = new THREE.Mesh(new THREE.PlaneGeometry(width - 1, 0.8), label('YOU ARE ENTERING A WORKSPACE', 1024, 96, '#ff4fd8', '#120818')); ban.position.set(0, 3.0, 0.6); g.add(ban);
  const plant = new THREE.Group(); plant.position.set(width / 2 - 1.5, 0, 0.9); g.add(plant); cyl(plant, 0.22, 0.18, 0.4, 0xd8d0c0, 0, 0.2, 0); for (let i = 0; i < 6; i++) box(plant, 0.08, 0.7, 0.2, 0x3fae5a, Math.sin(i) * 0.15, 0.7, Math.cos(i) * 0.15, { rz: Math.sin(i * 2) * 0.5, rx: Math.cos(i * 3) * 0.4 });
  return g;
}

// the Gristle & Sons trade post at the Gut border: a counter, a turnstile grown over with skin, a sign, a ladle on a hook
export function tradePostMesh() {
  const g = new THREE.Group(), skin = 0xe8a090, deep = 0xa02a4a;
  box(g, 3.2, 1.1, 0.8, 0x6a5040, 0, 0.55, 0); box(g, 3.4, 0.08, 1.0, 0xd8c0a0, 0, 1.12, 0);
  for (let i = 0; i < 4; i++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.22 + (i % 2) * 0.1, 8, 6), M(skin, { r: 0.3 })); b.scale.y = 0.6; b.position.set(-1.4 + i * 0.9, 0.2 + (i % 3) * 0.25, 0.42); g.add(b); } // the skin creeping up the front
  const ts = new THREE.Group(); ts.position.set(2.3, 0, 0); g.add(ts);
  cyl(ts, 0.12, 0.12, 1.0, 0x8a9098, 0, 0.5, 0, { m: 0.6 });
  for (let i = 0; i < 3; i++) { const a = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.9, 6), M(skin, { r: 0.3 })); a.rotation.z = Math.PI / 2; a.rotation.y = i * 2.094; a.position.y = 0.9; ts.add(a); }
  const flesh = new THREE.Mesh(new THREE.SphereGeometry(0.3, 8, 6), M(deep, { r: 0.25 })); flesh.position.y = 0.95; flesh.scale.set(1, 0.6, 1); ts.add(flesh);
  for (const sx of [-1.6, 1.6]) box(g, 0.1, 2.6, 0.1, 0x3a2a24, sx, 1.3, -0.35);
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 0.5), label('GRISTLE & SONS · TRADE POST', 1024, 120, '#d8c0a0', '#5a1020')); sign.position.set(0, 2.45, -0.3); g.add(sign);
  const lad = new THREE.Group(); lad.position.set(-1.2, 1.9, -0.28); g.add(lad); cyl(lad, 0.02, 0.02, 0.5, 0x8a9098, 0, -0.2, 0, { m: 0.6 }); const bowl = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 6, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), M(0x8a9098, { m: 0.6 })); bowl.position.y = -0.48; lad.add(bowl);
  const tongue = box(lad, 0.06, 0.02, 0.12, 0xe86a8a, 0, -0.5, 0.06, { r: 0.2 }); tongue.rotation.x = 0.4; // (it has a tongue)
  return g;
}
