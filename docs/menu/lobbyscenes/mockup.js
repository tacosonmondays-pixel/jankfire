// LOBBY SCENES mockups (docs/menu/LOBBY_SCENES.md): quick three.js blockouts drawn behind the real hub lobby screen,
// with the real characters, guns and mechs. not the shipped scenes: the Blender props replace these boxes.
// window.__lsMock(kind): 'garage' | 'warehouse' | 'royale' | 'hangar'
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { buildCharacter, buildWeapon } from '/js/models.js';
import { buildMech } from '/js/mechmodel.js';
import { idlePose } from '/js/loco.js';
import { DEFAULT_LOOK } from '/shared/looks.js';

const css = `
#lsCv{position:fixed;inset:0;width:100vw;height:100vh;z-index:0;display:block}
body.ls-on #menu.home-on{background:none}
body.ls-on #menu.home-on::before{opacity:.25}
body.ls-on #hubStage #preview{visibility:hidden}
#lsTags{position:fixed;inset:0;pointer-events:none;z-index:50;font-family:var(--font)}
#lsTags .np{position:absolute;transform:translate(-50%,-100%);text-align:center;white-space:nowrap}
#lsTags .np b{display:block;font-size:15px;color:#fff;text-shadow:2px 2px 0 #120818;letter-spacing:1px}
#lsTags .np i{display:inline-block;font-style:normal;font-size:11px;font-weight:900;color:#120818;background:#7dff4f;border:2px solid #000;padding:0 6px;transform:rotate(-2deg)}
#lsTags .np.inv b{color:#4fd8ff}
#lsTags .np.inv i{background:#fff}
#lsTags .bub{position:absolute;transform:translate(-50%,-100%);max-width:220px;background:#fff;color:#120818;border:3px solid #000;box-shadow:5px 5px 0 #ff4fd8;padding:6px 10px;font-size:14px;font-weight:700;line-height:1.15}
#lsTags .bub::after{content:'';position:absolute;left:30px;bottom:-14px;border:7px solid transparent;border-top-color:#000}
#lsTags .bub small{display:block;font-size:11px;color:#ff00dc;font-weight:900;letter-spacing:1px;margin-bottom:2px}
#lsTags .sign{position:absolute;transform:translate(-50%,-50%) rotate(-2deg);background:#ffe14d;color:#120818;border:3px solid #000;box-shadow:4px 4px 0 #120818;font-weight:900;font-size:12px;letter-spacing:2px;padding:1px 8px}
#lsTags .swap{position:absolute;transform:translate(-50%,-50%);display:flex;gap:6px;align-items:center;background:rgba(18,8,24,.92);border:3px solid #ff4fd8;box-shadow:5px 5px 0 #4fd8ff;padding:4px 8px;color:#fff;font-weight:900;font-size:14px;letter-spacing:1px}
#lsTags .swap span{background:#fff;color:#000;border:2px solid #000;padding:0 6px}
`;
const L = new GLTFLoader();
const glb = (u) => new Promise((ok) => L.load(u, (g) => ok(g.scene), undefined, () => ok(null)));
const std = (c, r = 0.6, m = 0, e) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m, emissive: e || 0, flatShading: false });
const basic = (c) => new THREE.MeshBasicMaterial({ color: c });
function box(g, w, h, d, mat, x, y, z, ry = 0) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); m.rotation.y = ry; m.castShadow = m.receiveShadow = true; g.add(m); return m; }
function cyl(g, r, h, mat, x, y, z, seg = 10) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; g.add(m); return m; }
function stripes(w, h, a = '#ffe14d', b = '#120818', n = 8) { // hazard tape
  const cv = document.createElement('canvas'); cv.width = 128; cv.height = 16; const x = cv.getContext('2d');
  x.fillStyle = a; x.fillRect(0, 0, 128, 16); x.fillStyle = b;
  for (let i = -2; i < 18; i++) { x.beginPath(); x.moveTo(i * 16, 16); x.lineTo(i * 16 + 8, 16); x.lineTo(i * 16 + 16, 0); x.lineTo(i * 16 + 8, 0); x.fill(); }
  const t = new THREE.CanvasTexture(cv); t.wrapS = THREE.RepeatWrapping; t.repeat.set(n, 1); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function speck(hex, rep = 8, seams = true) {
  const n = 32, cv = document.createElement('canvas'); cv.width = cv.height = n; const g = cv.getContext('2d'), c = new THREE.Color(hex);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { const k = 0.82 + Math.random() * 0.3; g.fillStyle = `rgb(${(c.r * 255 * k) | 0},${(c.g * 255 * k) | 0},${(c.b * 255 * k) | 0})`; g.fillRect(x, y, 1, 1); }
  if (seams) { g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(0, 0, n, 1); g.fillRect(0, 0, 1, n); }
  const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function label(txt, bg = '#ffe14d', fg = '#120818', w = 256, h = 64) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h; const x = cv.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, w, h); x.strokeStyle = '#000'; x.lineWidth = 8; x.strokeRect(0, 0, w, h);
  x.fillStyle = fg; x.font = `900 ${Math.floor(h * 0.55)}px "Comic Neue", sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(txt, w / 2, h / 2 + 2);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function plane(g, tex, w, h, x, y, z, ry = 0, emi = false) { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), emi ? new THREE.MeshBasicMaterial({ map: tex }) : new THREE.MeshStandardMaterial({ map: tex, roughness: 0.5 })); m.position.set(x, y, z); m.rotation.y = ry; g.add(m); return m; }

// a person: the real character renderer, scaled to 1.8 m, feet on y=0
const LOOKS = [
  ...[],
  { ...DEFAULT_LOOK },
  { ...DEFAULT_LOOK, hair: 'spiky', hairColor: '#ff4fd8', top: 'hoodie', topColor: '#4fd8ff', bottom: 'cargo', bottomColor: '#3a3a44', skin: '#c68642' },
  { ...DEFAULT_LOOK, hair: 'bun', hairColor: '#d9b45a', top: 'jacket', topColor: '#ffe14d', bottom: 'pants', bottomColor: '#1a1a1a', skin: '#ffdbac', build: 'f' },
  { ...DEFAULT_LOOK, hair: 'afro', hairColor: '#1a1a1a', top: 'tee', topColor: '#7dff4f', bottom: 'shorts', bottomColor: '#2a4a8a', skin: '#8d5524', bigHead: 2 },
  { ...DEFAULT_LOOK },
  { ...DEFAULT_LOOK, hair: 'mohawk', hairColor: '#7dff4f', top: 'jacket', topColor: '#3a6a2a', bottom: 'cargo', bottomColor: '#c8b48a', skin: '#a8e6a1', fat: 2 },
  { ...DEFAULT_LOOK, hair: 'bun', hairColor: '#a3a3ad', top: 'suit', topColor: '#ff9ad5', bottom: 'skirt', bottomColor: '#3a3a44', skin: '#e0ac69', build: 'f' },
  { ...DEFAULT_LOOK, hair: 'long', hairColor: '#c02030', top: 'hoodie', topColor: '#ff7a1a', bottom: 'overalls', bottomColor: '#2a4a8a', skin: '#9ad0ff' },
];
const people = [];
function person(g, i, x, z, ry = 0, gun) {
  const ch = buildCharacter(['#ff4fd8', '#4fd8ff', '#ffe14d', '#7dff4f'][i % 4], LOOKS[i % LOOKS.length]);
  ch.root.updateMatrixWorld(true);
  const b = new THREE.Box3().setFromObject(ch.root), s = 1.8 / Math.max(0.3, b.max.y - b.min.y);
  const w = new THREE.Group(); w.add(ch.root); ch.root.position.y = -b.min.y; w.scale.setScalar(s); w.position.set(x, 0, z); w.rotation.y = ry + Math.PI; g.add(w);
  ch.root.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  if (gun) { const wp = buildWeapon(gun); wp.scale.setScalar(1.5); ch.arm.rotation.x = ch.armL.rotation.x = -0.12; ch.slot.add(wp); }
  people.push({ ch, t: Math.random() * 9 });
  return w;
}
const tags = [];
function tag(html, cls, at) { const d = document.createElement('div'); d.className = cls; d.innerHTML = html; $tags.append(d); tags.push([d, new THREE.Vector3(...at)]); }
let $tags, R, scene, cam, camBase, kind0, t0 = performance.now(), extra = () => {};

async function garage(g) {
  scene.background = new THREE.Color(0x0d0912); scene.fog = new THREE.Fog(0x0d0912, 14, 34);
  const conc = std(0x55525a, 0.85); conc.map = speck(0x6a6670, 10);
  const floor = box(g, 40, 0.2, 30, conc, 0, -0.1, -8);
  const steel = std(0x2a2c34, 0.45, 0.7), yel = std(0xc8961a, 0.5, 0.3), pink = std(0xff4fd8, 0.35, 0.1, 0x2a0020);
  box(g, 40, 14, 0.4, std(0x1a1720, 0.9), 0, 7, -15); // back wall
  for (let i = -3; i <= 3; i++) box(g, 0.25, 14, 0.5, steel, i * 6, 7, -14.6); // ribs
  for (const z of [-1.4, -12.6]) { const t = box(g, 30, 0.02, 0.35, new THREE.MeshStandardMaterial({ map: stripes(30, 0.35, '#ffe14d', '#120818', 60), roughness: 0.6 }), 0, 0.011, z); t.receiveShadow = true; }
  for (const bx of [-9, 0, 9]) { // three bays: a gantry each (two towers, a top beam, a walkway), the bay number on the floor
    for (const sx of [-3.4, 3.4]) { box(g, 0.45, 8.5, 0.45, yel, bx + sx, 4.25, -8); box(g, 0.45, 8.5, 0.45, yel, bx + sx, 4.25, -10.5); for (let y = 1; y < 8; y += 1.4) box(g, 0.12, 0.12, 2.5, steel, bx + sx, y, -9.25); }
    box(g, 7.25, 0.5, 0.5, yel, bx, 8.6, -8); box(g, 7.25, 0.5, 0.5, yel, bx, 8.6, -10.5);
    box(g, 5.2, 0.15, 1, steel, bx, 4.6, -10); // walkway
    box(g, 5.6, 0.12, 0.08, yel, bx, 5.6, -9.5);
    const ring = new THREE.Mesh(new THREE.RingGeometry(1.9, 2.2, 8), new THREE.MeshBasicMaterial({ color: bx ? 0x4fd8ff : 0xff4fd8 })); ring.rotation.x = -Math.PI / 2; ring.position.set(bx, 0.02, -9); g.add(ring);
    plane(g, label('BAY 0' + (bx / 9 + 2), '#ffe14d'), 1.6, 0.4, bx, 9.4, -7.7);
    const lamp = new THREE.SpotLight(bx ? 0x9fdcff : 0xffd0f0, bx ? 120 : 260, 22, 0.55, 0.6, 1.6); lamp.position.set(bx, 12.5, -5.5); lamp.target.position.set(bx, 2, -9); lamp.castShadow = !bx; g.add(lamp, lamp.target);
    cyl(g, 0.35, 0.3, std(0x111111, 0.5, 0.6), bx, 12.6, -5.5, 8); // the lamp's can
  }
  box(g, 22, 0.4, 0.4, steel, 0, 12.8, -9.25); // the crane rail
  const hook = new THREE.Group(); hook.position.set(0, 12.6, -9.25); g.add(hook); box(hook, 1.2, 0.5, 0.8, yel, 0, 0, 0); cyl(hook, 0.03, 2.6, steel, 0, -1.5, 0, 6);
  // the mechs: yours in bay 2, a teammate's in bay 3, bay 1 waits for someone
  const mine = buildMech('paperplane', '#ff4fd8'), mate = buildMech('nightshift', '#4fd8ff');
  for (const [m, x, s] of [[mine, 0, 1], [mate, 9, 0.88]]) { m.root.position.set(x, 0, -9); m.root.scale.setScalar(s); g.add(m.root); m.root.traverse((o) => { if (o.isMesh) o.castShadow = true; }); }
  for (let i = 0; i < 4; i++) box(g, 0.9, 0.7, 0.9, std(0x6b4a2a, 0.8), -9 - (i % 2) * 1, 0.35 + Math.floor(i / 2) * 0.7, -4 - (i % 2) * 0.2); // crates
  box(g, 1.4, 1, 0.7, std(0xc03030, 0.4, 0.3), 3.6, 0.5, -3.2); box(g, 1.3, 0.08, 0.6, steel, 3.6, 1.04, -3.2); // tool cart
  for (let i = 0; i < 9; i++) { const c = cyl(g, 0.04, 0.02, basic(0xffe14d), -2 + Math.random() * 4, 0.02, -6 - Math.random() * 3, 5); c.scale.set(1 + Math.random() * 3, 1, 1); }
  scene.add(new THREE.HemisphereLight(0x8a7aa8, 0x1a1020, 0.9));
  const key = new THREE.DirectionalLight(0xffe0f4, 1.4); key.position.set(-4, 9, 6); key.castShadow = true; key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -14, right: 14, top: 14, bottom: -6 }); scene.add(key);
  const rim = new THREE.PointLight(0x4fd8ff, 30, 12); rim.position.set(4, 3, -2); scene.add(rim);
  person(g, 0, 0, 0, -0.15, 'ar'); person(g, 1, 1.5, -0.8, -0.3, 'smg');
  tag('<b>taco</b><i>YOU</i>', 'np', [0, 2.1, 0]); tag('<b>noodle_arms</b><i>READY</i>', 'np', [1.5, 2.1, -0.8]);
  tag('<b>+ INVITE</b><i>BAY 01 IS EMPTY</i>', 'np inv', [-1.6, 1.2, -0.8]);
  tag('<span>&lt;</span> PAPER PLANE <span>&gt;</span>', 'swap', [0, 6.2, -9]);
  cam.position.set(0, 2.0, 10); camBase = cam.position.clone(); cam.lookAt(0, 3.0, -4); cam.fov = 38; cam.updateProjectionMatrix();
}

async function warehouse(g) {
  scene.background = new THREE.Color(0x070a07); scene.fog = new THREE.Fog(0x070a07, 10, 28);
  const conc = std(0x4a4a44, 0.9); conc.map = speck(0x55554c, 10);
  box(g, 34, 0.2, 26, conc, 0, -0.1, -6);
  const brick = std(0x3a2a24, 0.95); brick.map = speck(0x4a3028, 6);
  box(g, 34, 9, 0.4, brick, 0, 4.5, -13); box(g, 0.4, 9, 26, brick, -12, 4.5, -6); box(g, 0.4, 9, 26, brick, 12, 4.5, -6);
  const wood = std(0x8a6a40, 0.85);
  for (const [x, z, ry] of [[-6, -12.75, 0], [6, -12.75, 0], [-11.75, -6, Math.PI / 2]]) { // boarded windows, green light leaking through
    const w = new THREE.Group(); w.position.set(x, 4, z); w.rotation.y = ry; g.add(w);
    box(w, 3, 2.2, 0.05, new THREE.MeshBasicMaterial({ color: 0x39ff14 }), 0, 0, 0);
    for (let i = 0; i < 4; i++) { const p = box(w, 3.4, 0.38, 0.12, wood, 0, -0.8 + i * 0.55, 0.12); p.rotation.z = (Math.random() - 0.5) * 0.25; }
    const l = new THREE.SpotLight(0x39ff14, 60, 16, 0.6, 0.8, 1.5); l.position.set(0, 0, 0.6); w.add(l); l.target.position.set(0, -4, 6); w.add(l.target);
  }
  for (let i = -1; i <= 1; i++) for (let y = 0; y < 3; y++) box(g, 2.8, 0.1, 1, std(0xff7a1a, 0.6, 0.3), -9 + i * 0.01, 0.6 + y * 1.5, -10 + i * 2.4); // a pallet rack
  for (let i = 0; i < 3; i++) box(g, 0.1, 4.2, 0.1, std(0x2a4a8a, 0.5, 0.5), -10.4, 2.1, -12 + i * 2.4);
  // stations: a desk (passive), the gun counter (starting pistol), a crate pile (the item)
  const st = [[-3.3, -5.6, 0.3, 'PASSIVES', 2], [0, -6.4, 0, 'PISTOLS', 1], [3.3, -5.6, -0.3, 'THE ITEM', 3]];
  for (const [x, z, ry, name, who] of st) {
    const s = new THREE.Group(); s.position.set(x, 0, z); s.rotation.y = ry; g.add(s);
    box(s, 2.2, 1, 0.8, wood, 0, 0.5, 0.6); box(s, 2.4, 0.1, 1, std(0x2a1a10, 0.7), 0, 1.05, 0.6);
    plane(s, label(name, '#39ff14'), 1.8, 0.45, 0, 2.45, -0.3, 0, true);
    cyl(s, 0.02, 1.6, std(0x111111), -0.8, 3.45, -0.3, 4); cyl(s, 0.02, 1.6, std(0x111111), 0.8, 3.45, -0.3, 4);
    const bulb = new THREE.PointLight(0xffd080, 40, 8); bulb.position.set(0, 2.8, 1.6); s.add(bulb);
    const np = person(s, who + 4, 0, -0.2, 0); np.position.y = 0;
  }
  const cola = await glb('/models/x_zmcola.glb'), mach = await glb('/models/x_zmmachine.glb');
  if (cola) { cola.position.set(-9.5, 0, -3); cola.rotation.y = Math.PI / 2; g.add(cola); }
  if (mach) { mach.position.set(9.4, 0, -3.5); mach.rotation.y = -Math.PI / 2; g.add(mach); }
  for (let i = 0; i < 5; i++) box(g, 1, 0.12, 1, wood, -2 + i * 0.3, 0.06 + i * 0.12, 2.5 - i * 0.05).rotation.y = i * 0.4; // plank pile
  for (let i = 0; i < 12; i++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.06, 6, 4), basic([0xffe14d, 0xff4fd8, 0x39ff14][i % 3])); b.position.set(-8 + i * 1.45, 6.2 + Math.sin(i) * 0.3, -9 + Math.cos(i * 0.8) * 0.5); g.add(b); } // string lights
  scene.add(new THREE.HemisphereLight(0x8aa88a, 0x201410, 1.3));
  const key = new THREE.DirectionalLight(0xfff0d0, 1.6); key.position.set(3, 10, 6); key.castShadow = true; key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -12, right: 12, top: 12, bottom: -6 }); scene.add(key);
  person(g, 0, 0, 0.8, 0, 'revolver'); person(g, 3, -1.4, 0.2, 0.2);
  tag('<b>taco</b><i>YOU</i>', 'np', [0, 2.1, 0.8]); tag('<b>bot_greg</b><i>BOT</i>', 'np', [-1.4, 2.1, 0.2]);
  tag('<small>DEB · PASSIVES · CLICK</small>"trust fund again? must be nice."', 'bub', [-3.3, 1.75, -5.6]);
  cam.position.set(0, 4.6, 8.6); camBase = cam.position.clone(); cam.lookAt(0, 1.7, -3); cam.fov = 40; cam.updateProjectionMatrix();
}

async function royale(g) {
  const sky = new THREE.Mesh(new THREE.SphereGeometry(200, 24, 12), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, uniforms: {}, vertexShader: 'varying vec3 p;void main(){p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}', fragmentShader: 'varying vec3 p;void main(){float h=normalize(p).y;vec3 a=vec3(1.,.72,.86),b=vec3(.31,.62,1.);gl_FragColor=vec4(mix(a,b,smoothstep(-.1,.5,h)),1.);}' }));
  g.add(sky);
  const sea = new THREE.Mesh(new THREE.CircleGeometry(190, 32), std(0x2a8adf, 0.3, 0.1)); sea.rotation.x = -Math.PI / 2; sea.position.y = -15; g.add(sea);
  const isl = new THREE.Mesh(new THREE.CylinderGeometry(40, 50, 6, 9), std(0x5fcf4f, 0.9)); isl.position.set(-30, -12, -210); g.add(isl);
  const sand = new THREE.Mesh(new THREE.CylinderGeometry(52, 55, 2, 9), std(0xf2dc9a, 0.9)); sand.position.set(-30, -14.5, -210); g.add(sand);
  const mt = new THREE.Mesh(new THREE.ConeGeometry(16, 22, 6), std(0x7a6a8a, 0.9)); mt.position.set(-38, 0, -220); g.add(mt);
  for (let i = 0; i < 26; i++) { // clouds: puffs of chunky balls
    const c = new THREE.Group(), a = (i / 26) * Math.PI * 2, r = 30 + (i % 5) * 14;
    c.position.set(Math.sin(a) * r, -8 - (i % 4) * 9 + (i % 3) * 3, Math.cos(a) * r - 20);
    for (let k = 0; k < 5; k++) { const s = new THREE.Mesh(new THREE.IcosahedronGeometry(2.4 + Math.random() * 2, 0), std(0xffffff, 1)); s.position.set((k - 2) * 2.4, Math.random() * 1.2, Math.random() * 1.5); c.add(s); }
    g.add(c);
  }
  const deck = std(0xb07a4a, 0.8); deck.map = speck(0xb07a4a, 6, true);
  box(g, 12, 0.3, 9, deck, 0, -0.15, 1.5); // the gondola deck, railings, the envelope above
  const rail = std(0xff4fd8, 0.35, 0.2);
  box(g, 12, 0.1, 0.1, rail, 0, 1.05, -2.95); for (let x = -5.8; x <= 5.8; x += 1.16) box(g, 0.08, 1.05, 0.08, rail, x, 0.52, -2.95);
  box(g, 0.1, 0.1, 9, rail, -5.95, 1.05, 1.5); box(g, 0.1, 0.1, 9, rail, 5.95, 1.05, 1.5);
  const gond = std(0xf6f2e6, 0.4, 0.2); for (const x of [-6.6, 6.6]) { box(g, 1.2, 4, 9, gond, x, 1.7, 1.5); box(g, 0.1, 0.4, 0.1, gond, x, 0, 0); }
  const sg = plane(g, label('GATE 7 · NO REFUNDS', '#ffe14d'), 3, 0.45, -6.0, 2.6, -1.0, Math.PI / 2);
  const flag = box(g, 0.05, 2.4, 0.05, std(0x222222), 5.4, 2.2, -2.9); void flag; void sg; box(g, 0.9, 0.55, 0.02, std(0xffe14d, 0.6), 5.85, 3.1, -2.9);
  const env = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), std(0xff4fd8, 0.35, 0.1)); env.scale.set(9, 6, 22); env.position.set(0, 9.5, 4); g.add(env);
  const band = new THREE.Mesh(new THREE.CylinderGeometry(1.002, 1.002, 0.12, 20, 1, true), std(0xffe14d, 0.4)); band.rotation.z = Math.PI / 2; band.scale.set(6.05, 9.05, 22.05); band.rotation.set(0, 0, Math.PI / 2); band.position.copy(env.position); g.add(band);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xffc0e0, 1.4));
  const sun = new THREE.DirectionalLight(0xfff4dd, 2.2); sun.position.set(6, 12, 8); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -8, right: 8, top: 8, bottom: -4 }); scene.add(sun);
    const xs = [0, -1.35, 1.35]; const zs = [-0.6, -1.3, -1.3];
  xs.forEach((x, i) => person(g, i, x, zs[i], -x * 0.12, i === 0 ? 'shotgun' : undefined));
  ['taco', 'noodle_arms', 'glizzy_rex'].forEach((n, i) => tag(`<b>${n}</b><i>${i === 0 ? 'YOU' : 'READY'}</i>`, 'np', [xs[i], 2.1, zs[i]]));
  tag('<b>+ INVITE</b><i>SQUAD 3/4</i>', 'np inv', [2.6, 1.1, -1.9]);
  const conf = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.08, 0.14), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, vertexColors: false }), 260), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  const cols = [0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f], P = [];
  for (let i = 0; i < 260; i++) { P.push([(Math.random() - 0.5) * 12, Math.random() * 6, (Math.random() - 0.5) * 6 - 1, Math.random() * 6]); conf.setColorAt(i, new THREE.Color(cols[i % 4])); }
  g.add(conf);
  extra = (t) => { P.forEach((p, i) => { const y = ((p[1] - t * 0.6) % 6 + 6) % 6; e.set(t * 3 + p[3], t * 2 + i, 0); q.setFromEuler(e); m4.compose(new THREE.Vector3(p[0] + Math.sin(t + p[3]) * 0.3, y, p[2]), q, new THREE.Vector3(1, 1, 1)); conf.setMatrixAt(i, m4); }); conf.instanceMatrix.needsUpdate = true; };
  cam.position.set(0, 1.9, 7.2); camBase = cam.position.clone(); cam.lookAt(0, 1.2, -2); cam.fov = 40; cam.updateProjectionMatrix();
}

async function hangar(g) {
  scene.background = new THREE.Color(0x0a0810); scene.fog = new THREE.Fog(0x0a0810, 9, 26);
  const conc = std(0x3a3842, 0.55, 0.1); conc.map = speck(0x46444e, 12);
  box(g, 30, 0.2, 24, conc, 0, -0.1, -6);
  box(g, 30, 10, 0.4, std(0x18161e, 0.9), 0, 5, -10);
  const scr = plane(g, label('QUICK PLAY', '#120818', '#ff4fd8', 512, 128), 4.2, 1.05, 0, 4.3, -9.7, 0, true); // the big screen
  box(g, 4.5, 1.3, 0.2, std(0x111111, 0.4, 0.6), 0, 4.3, -9.85);
  const sl = new THREE.RectAreaLight ? null : null; void sl; void scr;
  const rack = new THREE.Group(); rack.position.set(0, -0.4, -9.6); g.add(rack); // your loadout's guns on a wall rack
  box(rack, 3.6, 2.6, 0.2, std(0x2a2430, 0.7), 0, 1.9, 0); box(rack, 3.8, 0.12, 0.4, std(0xffc21a, 0.4, 0.3), 0, 0.55, 0.15);
  ['ar', 'shotgun', 'sniper'].forEach((id, i) => { const w = buildWeapon(id); w.scale.setScalar(2.2); w.rotation.y = Math.PI / 2; w.position.set(0, 2.8 - i * 0.7, 0.25); rack.add(w); });
  const crate = await glb('/models/p_crate.glb'), pal = await glb('/models/p_pallet_load.glb'), bag = await glb('/models/p_sandbags.glb');
  if (crate) for (const [x, y, z, r] of [[5.4, 0, -7.5, 0.2], [6.5, 0, -6.4, -0.3], [5.8, 1.05, -7.3, 0.5]]) { const c = crate.clone(); c.position.set(x, y, z); c.rotation.y = r; g.add(c); }
  if (pal) { const p = pal.clone(); p.position.set(-7.5, 0, -4); g.add(p); }
  if (bag) { const b = bag.clone(); b.position.set(7.2, 0, -2.4); b.rotation.y = -0.8; g.add(b); }
  const tape = new THREE.MeshStandardMaterial({ map: stripes(12, 0.3, '#ffe14d', '#120818', 40), roughness: 0.6 });
  box(g, 12, 0.02, 0.3, tape, 0, 0.011, 0.6); box(g, 12, 0.02, 0.3, tape, 0, 0.011, -4.2);
  scene.add(new THREE.HemisphereLight(0x50406a, 0x0a0610, 0.6));
  const key = new THREE.SpotLight(0xfff0e0, 260, 24, 0.5, 0.7, 1.4); key.position.set(-2, 9, 5); key.target.position.set(0, 0, -2); key.castShadow = true; key.shadow.mapSize.set(2048, 2048); scene.add(key, key.target);
  const pk = new THREE.PointLight(0xff4fd8, 40, 10); pk.position.set(-4, 2, -4); scene.add(pk);
  const cy = new THREE.PointLight(0x4fd8ff, 40, 10); cy.position.set(4, 2, -4); scene.add(cy);
  const scrL = new THREE.PointLight(0xff4fd8, 20, 9); scrL.position.set(0, 4, -8); scene.add(scrL);
  const xs = [0, -1.3, 1.3, -2.5]; const zs = [-1.2, -1.9, -1.9, -2.6];
  ['taco', 'noodle_arms', 'glizzy_rex', 'bot_steve'].forEach((n, i) => { person(g, i, xs[i], zs[i], -xs[i] * 0.07, ['ar', 'smg', 'shotgun', 'sniper'][i]); tag(`<b>${n}</b><i>${i ? 'READY' : 'YOU'}</i>`, 'np', [xs[i], 2.15, zs[i]]); });
  tag('<b>+ INVITE</b><i>PARTY 4/6</i>', 'np inv', [2.5, 1.2, -2.6]);
  cam.position.set(0, 2.0, 6.6); camBase = cam.position.clone(); cam.lookAt(0, 1.55, -2);
}

const KINDS = { garage, warehouse, royale, hangar };
window.__lsMock = async (kind) => {
  if (!document.getElementById('lsCss')) { const s = document.createElement('style'); s.id = 'lsCss'; s.textContent = css; document.head.append(s); }
  if (!R) {
    const cv = document.createElement('canvas'); cv.id = 'lsCv'; document.getElementById('game').after(cv);
    R = new THREE.WebGLRenderer({ canvas: cv, antialias: true }); R.setPixelRatio(1); R.shadowMap.enabled = true; R.shadowMap.type = THREE.PCFSoftShadowMap;
    R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.1; R.outputColorSpace = THREE.SRGBColorSpace;
    $tags = document.createElement('div'); $tags.id = 'lsTags'; document.body.append($tags);
    const loop = () => { requestAnimationFrame(loop); if (!scene || !camBase) return; const t = (performance.now() - t0) / 1000; for (const p of people) idlePose(p.ch, p.t + t); extra(t);
      cam.position.x = camBase.x + Math.sin(t * 0.25) * 0.15; R.render(scene, cam);
      for (const [d, v] of tags) { const p = v.clone().project(cam); d.style.left = ((p.x + 1) / 2 * innerWidth) + 'px'; d.style.top = ((1 - p.y) / 2 * innerHeight) + 'px'; } };
    loop();
  }
  document.body.classList.add('ls-on');
  R.setSize(innerWidth, innerHeight, false);
  scene = new THREE.Scene(); cam = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.1, 400); camBase = null; people.length = 0; tags.length = 0; $tags.innerHTML = ''; extra = () => {};
  const g = new THREE.Group(); await KINDS[kind](g); scene.add(g); kind0 = kind;
  return kind0;
};
