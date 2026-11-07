// Jank Royale on the client: the drop blimp, jumping + the umbrella glide, loot lying on the floor (with rarity rings
// and beams), picking things up (F) and healing (H), the violet zone wall, a minimap, the alive counter, armour,
// spectating once you're out, placements on the end screen. The server decides everything; this draws it and asks.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { ME, C as PC } from './player.js';
import { W, setLoadout, showSlots, refillAmmo } from './weapons.js';
import { RP } from './replay.js';
import { paintBoxes } from './minimap.js'; // the map-from-above painter, shared with the HUD minimap
import { buildWeapon, buildProjectile, freeTree, makeNameTag } from './models.js';
import { BOXES, MAPS } from '/shared/map.js';
import { raycast, movePlayer } from '/shared/physics.js';
import { WEAPONS, ITEMS, FLAGS } from '/shared/weapons.js';
import { BR, TIERS, STUFF, ZONE_COLOR, ARMOR_OF, blimpAt, blimpDone, zoneAt, outsideZone, lootName, lootColor, poiAt, hookCharges, hookSpend } from '/shared/royale.js';
import { weaponIcon, itemIcon } from './icons.js';
import { K } from './keys.js';

const $ = (id) => document.getElementById(id);
const st = () => performance.now() + (G.offset || 0); // the server's clock
const R = {
  on: false, path: null, zone: null, phase: '', loot: new Map(), blimp: new Set(), out: new Map(), total: 0,
  me: { inBlimp: false, fly: null, late: false, place: 0 }, inv: null, key: '', held: new Set(), reserve: {}, shots: {},
  ar: 0, heal: null, spec: 0, specSnap: true, win: -1, focus: null, autoT: new Map(), zoneTick: 0, umb: new Map(),
  leader: 0, crates: new Map(), goblins: new Map(), poi: null, vend: -1, mailAt: 0,
};
export const brOn = () => R.on;
export const brDead = () => R.on && !ME.alive;

// ------------------------------------------------------------ css + hud bits
const CSS = `
#brHud { position: absolute; right: 18px; top: 66px; display: flex; flex-direction: column; align-items: flex-end; gap: 6px; font-family: var(--font); }
#brMap { width: 176px; height: 176px; border: 4px solid #ff4fd8; box-shadow: 6px 6px 0 #4fd8ff; background: #120818; image-rendering: pixelated; transform: rotate(1deg); }
#brStat { background: rgba(18,8,24,0.92); border: 3px solid #ff4fd8; box-shadow: 4px 4px 0 #4fd8ff; padding: 4px 10px; color: #fff; font-weight: bold; font-size: 17px; text-align: right; transform: rotate(-1deg); }
#brStat b { color: #ffe14d; } #brStat i { color: #b07dff; font-style: normal; }
#brArmor { position: absolute; left: 20px; bottom: 56px; width: 240px; height: 12px; border: 3px solid #fff; background: rgba(0,0,0,0.5); transform: rotate(-1.5deg); }
#brArmor div { height: 100%; width: 0; background: repeating-linear-gradient(90deg, #4fd8ff 0 14px, #2a9fd0 14px 16px); }
#brArmor span { position: absolute; left: 6px; top: -21px; font: bold 14px var(--font); color: #4fd8ff; }
#brHeals { position: absolute; left: 270px; bottom: 22px; font: bold 16px var(--font); color: #fff; background: rgba(18,8,24,0.85); border: 3px solid #fff; padding: 2px 8px; transform: rotate(1deg); }
#brHeals b { color: #ffe14d; }
#brPrompt { position: absolute; left: 50%; top: 62%; transform: translateX(-50%) rotate(-1deg); font: bold 20px var(--font); color: #fff; background: rgba(18,8,24,0.92); border: 3px solid var(--c, #fff); box-shadow: 5px 5px 0 #000; padding: 4px 14px; white-space: nowrap; display: none; }
#brPrompt kbd { background: #ffe14d; color: #000; border: 2px solid #000; padding: 0 6px; margin-right: 8px; font: bold 16px var(--font); }
#brPrompt small { display: block; font-size: 13px; color: #ccc; font-weight: normal; }
#brZoneFx { position: absolute; inset: 0; box-shadow: inset 0 0 160px 40px rgba(138,60,255,0.75); opacity: 0; transition: opacity 0.3s; }
#brZoneFx b { position: absolute; left: 50%; top: 24%; transform: translateX(-50%) rotate(-2deg); font: bold 34px var(--font); color: #d6b4ff; text-shadow: 3px 3px 0 #2a0a5a; }
#brBig { position: absolute; left: 50%; top: 30%; transform: translateX(-50%); font: bold 46px var(--font); color: #ffe14d; text-shadow: 4px 4px 0 #ff00dc; text-align: center; display: none; white-space: nowrap; }
#brBig small { display: block; font-size: 20px; color: #fff; text-shadow: 2px 2px 0 #000; }
#brHealBar { position: absolute; left: 50%; top: 68%; transform: translateX(-50%); width: 220px; height: 14px; border: 3px solid #fff; background: rgba(0,0,0,0.6); display: none; }
#brHealBar div { height: 100%; background: #7dff4f; width: 0; }
#brHealBar span { position: absolute; left: 0; right: 0; top: -24px; text-align: center; font: bold 15px var(--font); color: #7dff4f; }
body.br-sky #hotbar, body.br-sky #ammo, body.br-sky #crosshair, body.br-spec #hotbar, body.br-spec #ammo, body.br-spec #crosshair, body.br-spec #hpbox, body.br-spec #brArmor, body.br-spec #brHeals { visibility: hidden; }
body.br-on #streakTray { display: none; }
.hslot.br-t1 { border-color: #7dff4f !important; } .hslot.br-t2 { border-color: #4fd8ff !important; } .hslot.br-t3 { border-color: #ff4fd8 !important; } .hslot.br-t4 { border-color: #ffe14d !important; box-shadow: 0 0 0 3px #ff00dc; }
.hslot .br-am { position: absolute; right: 4px; bottom: 2px; font: bold 12px var(--font); color: #ffe14d; }
#roundEnd .br-row { display: flex; gap: 10px; justify-content: space-between; }
#roundEnd .br-row b { color: #ff4fd8; min-width: 40px; }
#brHook { position: absolute; left: calc(50% + 34px); top: calc(50% + 26px); width: 56px; height: 56px; pointer-events: none; font: bold 11px var(--font); color: #fff; text-shadow: 1px 1px 0 #000; }
#brHook svg { position: absolute; inset: 0; transform: rotate(-90deg); }
#brHook .tr { fill: none; stroke: rgba(0,0,0,0.55); stroke-width: 6; } #brHook .fl { fill: none; stroke: #4fd8ff; stroke-width: 6; stroke-linecap: butt; }
#brHook.full .fl { stroke: #7dff4f; } #brHook.none .fl { stroke: #ff3030; }
#brHook span { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 17px; letter-spacing: -1px; }
#brHook small { font-size: 12px !important; color: #fff !important; }
#brHook small { position: absolute; left: 50%; top: 54px; transform: translateX(-50%); white-space: nowrap; font-size: 10px; letter-spacing: 1px; color: #ccc; }
#brHook.no { animation: brHookNo 0.35s; } @keyframes brHookNo { 0%, 100% { transform: none; } 25% { transform: translateX(-5px) rotate(-6deg); } 75% { transform: translateX(5px) rotate(6deg); } }
body.br-sky #brHook, body.br-spec #brHook, body.br-inv #brHook { display: none; }
#brInv { position: absolute; inset: 0; z-index: 20; pointer-events: auto; background: rgba(8,0,16,0.35); display: none; font-family: var(--font); color: #fff; cursor: default; text-shadow: 1px 1px 0 #000; }
body.br-inv #brInv { display: block; } body.br-inv #crosshair, body.br-inv #brPrompt { visibility: hidden; }
#brInv .bi { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -54%) rotate(-0.6deg); width: min(860px, 94vw); background: rgba(18,8,24,0.92); border: 4px solid #ff4fd8; box-shadow: 8px 8px 0 #4fd8ff; padding: 12px 16px 14px; box-sizing: border-box; }
#brInv h2 { margin: 0; font-size: 30px; color: #ffe14d; text-shadow: 3px 3px 0 #ff00dc; letter-spacing: 2px; }
#brInv .bi-help { font-size: 12px; color: #ccc; margin: 0 0 8px; }
#brInv .bi-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 220px; gap: 10px; }
#brInv .bi-h { font-size: 12px; letter-spacing: 2px; color: #4fd8ff; margin: 6px 0 3px; }
#brInv .bi-t { position: relative; min-height: 118px; background: rgba(255,255,255,0.05); border: 3px solid var(--c, #555); box-shadow: 4px 4px 0 #000; padding: 4px 6px 30px; box-sizing: border-box; }
#brInv .bi-t.empty { border-style: dashed; border-color: #555; color: #777; display: flex; align-items: center; justify-content: center; font-size: 14px; }
#brInv .bi-t.drag { opacity: 0.45; } #brInv .bi-t.over { background: rgba(255,225,77,0.18); border-color: #ffe14d; }
#brInv .bi-t[draggable="true"] { cursor: grab; }
#brInv .bi-t img { display: block; width: 100%; height: 62px; object-fit: contain; image-rendering: pixelated; }
#brInv .bi-t b { display: block; font-size: 15px; color: var(--c); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
#brInv .bi-t i { font-style: normal; font-size: 12px; color: #ffe14d; }
#brInv .bi-t kbd { position: absolute; left: -3px; top: -3px; background: #ffe14d; color: #000; border: 2px solid #000; font: bold 12px var(--font); padding: 0 5px; }
#brInv button { font-family: var(--font); font-size: 12px; padding: 1px 9px; border: 2px solid #000; background: #fff; color: #000; box-shadow: 2px 2px 0 #ff4fd8; cursor: pointer; }
#brInv button.red { background: #ff3030; color: #fff; } #brInv button.yel { background: #ffe14d; }
#brInv .bi-t .bi-b { position: absolute; left: 6px; right: 6px; bottom: 5px; display: flex; gap: 5px; justify-content: flex-end; }
#brInv .bi-swap { display: flex; align-items: center; justify-content: center; }
#brInv .bi-row { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.05); border: 2px solid rgba(255,255,255,0.15); padding: 3px 6px; margin-bottom: 4px; }
#brInv .bi-row span { flex: 1; } #brInv .bi-row b { color: #ffe14d; font-size: 17px; }
#brInv .bi-ar { height: 12px; border: 2px solid #fff; background: rgba(0,0,0,0.5); } #brInv .bi-ar div { height: 100%; background: repeating-linear-gradient(90deg, #4fd8ff 0 14px, #2a9fd0 14px 16px); }
#brInv .bi-side { background: rgba(0,0,0,0.3); border: 2px solid #ff4fd8; padding: 6px 8px; font-size: 13px; transform: rotate(0.8deg); }
#brInv .bi-side .big { font-size: 26px; color: #ffe14d; line-height: 1; } #brInv .bi-side ol { margin: 4px 0 0; padding-left: 20px; } #brInv .bi-side li.me { color: #ffe14d; } #brInv .bi-side li.dead { color: #777; text-decoration: line-through; }
`;
let el = null;
function ensureHud() {
  if (el) return el;
  const s = document.createElement('style'); s.textContent = CSS; document.head.append(s);
  const hudEl = $('hud');
  const mk = (id, html = '') => { const d = document.createElement('div'); d.id = id; d.innerHTML = html; hudEl.append(d); return d; };
  el = {
    box: mk('brHud', '<canvas id="brMap" width="176" height="176"></canvas><div id="brStat"></div>'),
    armor: mk('brArmor', '<div></div><span></span>'), heals: mk('brHeals'), prompt: mk('brPrompt'), zone: mk('brZoneFx', '<b>EVICTION NOTICE: GET IN THE ZONE</b>'),
    big: mk('brBig'), healBar: mk('brHealBar', '<div></div><span></span>'),
    hook: mk('brHook', '<svg viewBox="0 0 46 46"><circle class="tr" cx="23" cy="23" r="19"/><circle class="fl" cx="23" cy="23" r="19"/></svg><span></span><small></small>'),
    inv: mk('brInv'),
  };
  el.inv.addEventListener('mousedown', (ev) => ev.stopPropagation()); // clicks in the backpack never fire your gun
  el.inv.addEventListener('contextmenu', (ev) => ev.preventDefault());
  el.map = $('brMap'); el.stat = $('brStat');
  return el;
}
function showHud(v) {
  ensureHud();
  for (const k of ['box', 'armor', 'heals', 'hook']) el[k].style.display = v ? '' : 'none';
  if (!v) invClose(false);
  if (!v) { el.prompt.style.display = 'none'; el.zone.style.opacity = 0; el.big.style.display = 'none'; el.healBar.style.display = 'none'; }
  document.body.classList.toggle('br-on', v);
}
let bigT = 0;
function big(text, sub = '', secs = 3) { ensureHud(); el.big.innerHTML = `${text}${sub ? `<small>${sub}</small>` : ''}`; el.big.style.display = 'block'; bigT = performance.now() + secs * 1000; }

// ------------------------------------------------------------ 3D: the blimp
let blimp = null, zoneWall = null, zoneNext = null, myUmb = null;
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; }
const mat = (c, o = {}) => new THREE.MeshLambertMaterial({ color: c, ...o });
function buildBlimp() {
  const g = new THREE.Group();
  // the envelope: a fat pink sausage with yellow bands, a face on the front (it is smiling, it should not be)
  const env = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), mat(0xff4fd8));
  env.scale.set(7, 6.2, 17); g.add(env);
  for (const z of [-8, 0, 8]) { const band = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 0.9, 20, 1, true), mat(0xffe14d, { side: THREE.DoubleSide })); band.rotation.x = Math.PI / 2; const k = Math.sqrt(Math.max(0, 1 - (z / 17) ** 2)); band.scale.set(7.08 * k, 1, 6.28 * k); band.position.z = z; g.add(band); }
  const banner = canvasTex(512, 128, (x, w, h) => { x.fillStyle = '#120818'; x.fillRect(0, 0, w, h); x.fillStyle = '#ffe14d'; x.font = 'bold 86px Comic Neue, Comic Sans MS, sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('JANK AIR', w / 2, h / 2 + 4); x.strokeStyle = '#ff00dc'; x.lineWidth = 8; x.strokeRect(4, 4, w - 8, h - 8); });
  for (const s of [-1, 1]) { const b = new THREE.Mesh(new THREE.PlaneGeometry(12, 3), new THREE.MeshBasicMaterial({ map: banner, side: THREE.DoubleSide })); b.position.set(s * 7.05, 0.6, 0); b.rotation.y = s * Math.PI / 2; g.add(b); }
  const face = canvasTex(256, 256, (x) => { x.fillStyle = '#ff4fd8'; x.fillRect(0, 0, 256, 256); x.fillStyle = '#fff'; x.beginPath(); x.arc(80, 100, 34, 0, 7); x.arc(176, 100, 34, 0, 7); x.fill(); x.fillStyle = '#000'; x.beginPath(); x.arc(88, 108, 14, 0, 7); x.arc(170, 96, 14, 0, 7); x.fill(); x.lineWidth = 12; x.beginPath(); x.arc(128, 150, 60, 0.2, Math.PI - 0.2); x.stroke(); });
  const fc = new THREE.Mesh(new THREE.CircleGeometry(3.2, 20), new THREE.MeshBasicMaterial({ map: face })); fc.position.z = -16.6; fc.rotation.y = Math.PI; g.add(fc);
  // fins + the gondola full of idiots + two propellers
  for (const [rx, ry, rz, sx, sy] of [[0, 4.5, 14, 0.4, 5], [0, -4.5, 14, 0.4, 5], [4.5, 0, 14, 5, 0.4], [-4.5, 0, 14, 5, 0.4]]) { const f = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, 5), mat(0xffe14d)); f.position.set(rx, ry, rz); g.add(f); }
  const gon = new THREE.Mesh(new THREE.BoxGeometry(5, 2.6, 11), mat(0x4fd8ff)); gon.position.y = -7.2; g.add(gon);
  for (let i = 0; i < 4; i++) for (const s of [-1, 1]) { const wdw = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1, 1.6), new THREE.MeshBasicMaterial({ color: 0xffe14d })); wdw.position.set(s * 2.52, -7, -3.6 + i * 2.4); g.add(wdw); }
  for (const s of [-1, 1]) { const strut = new THREE.Mesh(new THREE.BoxGeometry(0.3, 2.5, 0.3), mat(0x333333)); strut.position.set(s * 1.6, -5.4, 0); g.add(strut); }
  const props = [];
  for (const s of [-1, 1]) {
    const hub = new THREE.Group(); hub.position.set(s * 3.4, -7.2, 6.4);
    for (let k = 0; k < 3; k++) { const bl = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3.4, 0.12), mat(0x222222)); bl.rotation.z = k * 2.1; hub.add(bl); }
    g.add(hub); props.push(hub);
  }
  g.userData.props = props;
  g.traverse((o) => { o.frustumCulled = false; });
  return g;
}

// ------------------------------------------------------------ 3D: the zone
const ZONE_VS = `varying vec3 vW; varying vec2 vUv;
void main() { vUv = uv; vec4 wp = modelMatrix * vec4(position, 1.0); vW = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`;
const ZONE_FS = `uniform float uTime; uniform vec3 uColor; varying vec3 vW; varying vec2 vUv;
void main() {
  float a = atan(vW.z, vW.x);
  float bands = step(0.5, fract(vW.y * 0.12 - uTime * 0.35));
  float hatch = step(0.9, fract((a * 30.0) + vW.y * 0.04 + uTime * 0.2));
  float fade = smoothstep(0.0, 0.08, vUv.y) * (1.0 - smoothstep(0.55, 1.0, vUv.y));
  float alpha = (0.07 + 0.07 * bands + 0.2 * hatch) * fade;
  gl_FragColor = vec4(uColor * (0.8 + 0.4 * hatch), alpha);
}`;
function buildZone() {
  const m = new THREE.ShaderMaterial({ uniforms: { uTime: { value: 0 }, uColor: { value: new THREE.Color(ZONE_COLOR) } }, vertexShader: ZONE_VS, fragmentShader: ZONE_FS, transparent: true, depthWrite: false, side: THREE.DoubleSide });
  const w = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 96, 1, true), m);
  w.frustumCulled = false; w.renderOrder = 5;
  const n = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 96, 1, true), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35, side: THREE.DoubleSide, depthWrite: false }));
  n.frustumCulled = false;
  return [w, n];
}

// ------------------------------------------------------------ 3D: loot on the floor
const ringGeo = new THREE.RingGeometry(0.55, 0.85, 20), beamGeo = new THREE.CylinderGeometry(0.12, 0.12, 1, 6, 1, true);
const ringMats = TIERS.map((t) => new THREE.MeshBasicMaterial({ color: t.color, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false }));
const beamMats = TIERS.map((t) => new THREE.MeshBasicMaterial({ color: t.color, transparent: true, opacity: 0.35, depthWrite: false, blending: THREE.AdditiveBlending }));
function stuffMesh(l) {
  const g = new THREE.Group(), add = (geo, c, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(geo, mat(c)); m.position.set(x, y, z); g.add(m); return m; };
  if (l.id === 'ammo') { // a bucket of loose bullets
    add(new THREE.CylinderGeometry(0.28, 0.22, 0.42, 10), 0xff9a2a, 0, 0.21);
    for (let i = 0; i < 7; i++) { const a = i * 0.9, r = 0.14; add(new THREE.CylinderGeometry(0.035, 0.035, 0.26, 5), 0xffd84a, Math.cos(a) * r, 0.5, Math.sin(a) * r).rotation.z = (i - 3) * 0.12; }
    add(new THREE.TorusGeometry(0.27, 0.025, 4, 12), 0x333333, 0, 0.42).rotation.x = Math.PI / 2;
  } else if (l.id === 'cola') { // jank cola: a red can with a white band
    for (const k of [0, 1]) { add(new THREE.CylinderGeometry(0.1, 0.1, 0.3, 10), 0xff2030, k * 0.24 - 0.12, 0.15); add(new THREE.CylinderGeometry(0.102, 0.102, 0.07, 10), 0xffffff, k * 0.24 - 0.12, 0.17); }
  } else if (l.id === 'medkit') {
    add(new THREE.BoxGeometry(0.6, 0.3, 0.42), 0xf4f4f4, 0, 0.15); add(new THREE.BoxGeometry(0.34, 0.31, 0.1), 0xff2020, 0, 0.155); add(new THREE.BoxGeometry(0.1, 0.31, 0.3), 0xff2020, 0, 0.156);
    add(new THREE.BoxGeometry(0.2, 0.06, 0.06), 0x333333, 0, 0.33);
  } else if (l.id === 'plate') { add(new THREE.BoxGeometry(0.6, 0.08, 0.7), 0xc9a36a, 0, 0.04); add(new THREE.BoxGeometry(0.62, 0.02, 0.1), 0xb08850, 0, 0.09); }
  else if (l.id === 'vest') { for (const s of [-1, 1]) { const d = add(new THREE.CylinderGeometry(0.3, 0.3, 0.06, 12), 0x9aa4ae, 0, 0.05 + (s + 1) * 0.04, s * 0.1); d.rotation.x = 0.1 * s; } add(new THREE.BoxGeometry(0.62, 0.04, 0.1), 0xdddddd, 0, 0.16); }
  else if (l.id === 'fridge') { add(new THREE.BoxGeometry(0.62, 0.16, 0.95), 0xff9ad5, 0, 0.08); add(new THREE.BoxGeometry(0.06, 0.06, 0.5), 0xdddddd, 0.2, 0.19); }
  return g;
}
function lootMesh(l) {
  let g;
  if (l.k === 'gun' || l.k === 'melee') { g = buildWeapon(l.id); g.scale.setScalar(1.6); }
  else if (l.k === 'gadget') {
    const it = ITEMS[l.id] || {};
    g = it.proj ? buildProjectile(it.proj) : WEAPONS[l.id] ? buildWeapon(l.id) : new THREE.Mesh(new THREE.SphereGeometry(0.2, 10, 8), mat(l.id === 'bubble' ? 0x9fe8ff : 0xff4fd8, { transparent: true, opacity: 0.8 }));
    g.scale.multiplyScalar(1.6);
  } else g = stuffMesh(l);
  const holder = new THREE.Group(); holder.add(g); holder.userData.item = g;
  return holder;
}
// each loot entry: [i, k, id, tier, n, a, x, y, z]
function addLoot(e) {
  const [i, k, id, tier, n, a, x, y, z] = e;
  if (R.loot.has(i)) removeLoot(i);
  const l = { i, k, id, tier, n, a: a < 0 ? null : a, p: [x, y, z], mesh: null, ring: null, beam: null, ph: Math.random() * 6 };
  const t = k === 'gun' || k === 'melee' || k === 'gadget' ? tier : k === 'armor' ? (id === 'fridge' ? 3 : id === 'vest' ? 2 : 0) : 0;
  l.vt = t;
  l.ring = new THREE.Mesh(ringGeo, ringMats[t]); l.ring.rotation.x = -Math.PI / 2; l.ring.position.set(x, y + 0.04, z); l.ring.visible = false; G.scene.add(l.ring);
  if (t >= 2) { l.beam = new THREE.Mesh(beamGeo, beamMats[t]); l.beam.scale.set(1, 7 + t * 2, 1); l.beam.position.set(x, y + (7 + t * 2) / 2, z); l.beam.visible = false; G.scene.add(l.beam); }
  R.loot.set(i, l);
}
function removeLoot(i) {
  const l = R.loot.get(i);
  if (!l) return;
  for (const m of [l.mesh, l.ring, l.beam]) if (m) G.scene.remove(m);
  if (l.mesh) freeTree(l.mesh);
  R.loot.delete(i);
}
function clearLoot() { for (const i of [...R.loot.keys()]) removeLoot(i); }

// ------------------------------------------------------------ umbrellas (the glide)
function umbrella() {
  const g = new THREE.Group();
  const cols = [0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f, 0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f];
  for (let i = 0; i < 8; i++) {
    const seg = new THREE.Mesh(new THREE.ConeGeometry(1.25, 0.55, 3, 1, true, i * Math.PI / 4, Math.PI / 4), mat(cols[i], { side: THREE.DoubleSide }));
    g.add(seg);
  }
  const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.5, 5), mat(0x222222)); stick.position.y = -0.7; g.add(stick);
  const hook = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.025, 4, 8, Math.PI), mat(0x222222)); hook.position.y = -1.45; hook.rotation.z = Math.PI; g.add(hook);
  return g;
}

// ------------------------------------------------------------ the minimap: the map from above, drawn once per map
let mapImg = null, mapFor = '', mapView = null;
function drawMapBase() {
  const map = MAPS[G.cfg.map], z0 = (map.royale && map.royale.zone0) || [0, 0, 150];
  const S = 176, ext = z0[2] * 1.05, c = document.createElement('canvas'); c.width = S; c.height = S;
  const x = c.getContext('2d');
  mapView = { cx: z0[0], cz: z0[1], ext, S };
  x.fillStyle = '#2a1a10'; x.fillRect(0, 0, S, S);
  paintBoxes(x, map, toMap, S, { style: 'royale' }); // the shared painter (minimap.js), in royale's sandy colours
  mapImg = c; mapFor = G.cfg.map;
}
function toMap(wx, wz) { const v = mapView; return [((wx - v.cx) / v.ext * 0.5 + 0.5) * v.S, ((wz - v.cz) / v.ext * 0.5 + 0.5) * v.S]; }
let mapT = 0;
function drawMap(now, zn) {
  if (now - mapT < 120) return;
  mapT = now;
  if (mapFor !== G.cfg.map || !mapImg) drawMapBase();
  const x = el.map.getContext('2d'), S = mapView.S, k = S / (mapView.ext * 2);
  x.drawImage(mapImg, 0, 0);
  if (zn) {
    const [cx, cz] = toMap(zn.c[0], zn.c[1]);
    x.save(); x.fillStyle = 'rgba(110,40,220,0.45)'; x.beginPath(); x.rect(0, 0, S, S); x.arc(cx, cz, zn.r * k, 0, Math.PI * 2, true); x.fill('evenodd'); x.restore();
    x.strokeStyle = '#b07dff'; x.lineWidth = 2; x.beginPath(); x.arc(cx, cz, zn.r * k, 0, Math.PI * 2); x.stroke();
    if (zn.next) { const [nx, nz] = toMap(zn.next.c[0], zn.next.c[1]); x.strokeStyle = '#fff'; x.setLineDash([4, 3]); x.beginPath(); x.arc(nx, nz, Math.max(1.5, zn.next.r * k), 0, Math.PI * 2); x.stroke(); x.setLineDash([]); }
  }
  if (R.path && R.phase !== 'live') {
    const a = toMap(R.path.a[0], R.path.a[1]), b = toMap(R.path.a[0] + R.path.d[0] * BR.blimp.len * 2, R.path.a[1] + R.path.d[1] * BR.blimp.len * 2);
    x.strokeStyle = '#ffe14d'; x.lineWidth = 2; x.setLineDash([6, 4]); x.beginPath(); x.moveTo(a[0], a[1]); x.lineTo(b[0], b[1]); x.stroke(); x.setLineDash([]);
    const bp = blimpAt(R.path, st()), [bx, bz] = toMap(bp[0], bp[2]);
    x.fillStyle = '#ff4fd8'; x.fillRect(bx - 4, bz - 3, 8, 6);
  }
  // POIs, supply crates, the kill leader
  const pois = MAPS[G.cfg.map].royale && MAPS[G.cfg.map].royale.pois;
  if (pois) { x.font = 'bold 9px sans-serif'; x.textAlign = 'center'; for (const d of pois) { const [px, pz] = toMap((d.rect[0] + d.rect[2]) / 2, (d.rect[1] + d.rect[3]) / 2); x.fillStyle = '#000'; x.fillText(d.name.toUpperCase(), px + 1, pz + 1); x.fillStyle = d.color; x.fillText(d.name.toUpperCase(), px, pz); } }
  for (const c of R.crates.values()) { const [px, pz] = toMap(c.x, c.z); x.fillStyle = '#ffe14d'; x.strokeStyle = '#000'; x.lineWidth = 2; x.strokeRect(px - 4, pz - 4, 8, 8); x.fillRect(px - 4, pz - 4, 8, 8); }
  const ld = R.leader && R.leader !== G.myId && G.remotes.get(R.leader);
  if (ld && ld.alive) { const [px, pz] = toMap(ld.pos[0], ld.pos[2]), k2 = 3 + Math.sin(now / 150) * 1.5; x.fillStyle = '#ffe14d'; x.beginPath(); x.arc(px, pz, 4 + k2, 0, 7); x.fill(); x.fillStyle = '#ff00dc'; x.beginPath(); x.arc(px, pz, 3, 0, 7); x.fill(); }
  // you: an arrow (or who you're watching)
  const who = ME.alive ? { pos: ME.pos, yaw: ME.yaw } : G.remotes.get(R.spec);
  if (who) {
    const [px, pz] = toMap(who.pos[0], who.pos[2]);
    x.save(); x.translate(px, pz); x.rotate(-(who.yaw || 0)); x.fillStyle = '#ffe14d'; x.strokeStyle = '#000'; x.lineWidth = 2;
    x.beginPath(); x.moveTo(0, -7); x.lineTo(5, 5); x.lineTo(0, 2); x.lineTo(-5, 5); x.closePath(); x.stroke(); x.fill(); x.restore();
  }
}

// ------------------------------------------------------------ inventory from the server
const hooks = {
  canReload(id) { return (R.reserve[id] ?? 0) > 0; },
  take(id, n) { const got = Math.min(n, R.reserve[id] || 0); R.reserve[id] = (R.reserve[id] || 0) - got; return got; }, // one akimbo hand's mag
  reloaded(id) { const w = WEAPONS[id], want = w.mag - (W.ammo[id] || 0), got = Math.min(want, R.reserve[id] || 0); W.ammo[id] = (W.ammo[id] || 0) + got; R.reserve[id] = (R.reserve[id] || 0) - got; },
  dry(id) { // shot-counted weapons (no magazine): out = no shooting
    if (!R.on || WEAPONS[id].mag || R.shots[id] == null) return false;
    if (R.shots[id] > 0) return false;
    sfx.empty(); hud.msg('OUT OF AMMO: FIND AN AMMO BUCKET', 1, 'brag');
    return true;
  },
  hud(id, reloading) {
    const w = WEAPONS[id];
    const a = $('ammo'), n = W.ammo[id] || 0, res = R.reserve[id] ?? 0;
    if (!w.mag && R.shots[id] == null) { a.style.display = 'none'; return; }
    a.style.display = 'block';
    a.textContent = reloading ? 'reloading' : w.mag ? `${n} / ${res >= 999 ? '∞' : res}` : `${R.shots[id]} left`;
    a.style.color = reloading || (w.mag ? n === 0 : R.shots[id] === 0) ? '#ff5050' : (w.mag ? n + res : R.shots[id]) <= (w.mag || 6) ? '#ffe14d' : '#fff';
  },
};
function applyInv(m) {
  R.inv = m;
  const guns = m.s.filter(Boolean), slots = guns.map((g) => g[0]);
  if (m.m) slots.push(m.m[0]);
  const held = new Set();
  for (const [w, , a] of guns) {
    held.add(w);
    const wd = WEAPONS[w];
    if (a < 0) { if (wd.mag) { if (!R.held.has(w)) W.ammo[w] = wd.mag; R.reserve[w] = 999; } delete R.shots[w]; continue; }
    if (wd.mag) {
      if (!R.held.has(w)) W.ammo[w] = Math.min(wd.mag, a);
      if (W.ammo[w] > a) W.ammo[w] = a;
      R.reserve[w] = Math.max(0, a - (W.ammo[w] || 0));
    } else R.shots[w] = a;
  }
  const fresh = guns.find((g) => !R.held.has(g[0]));
  R.held = held;
  R.ar = m.ar;
  R.heal = m.hl ? { k: m.hl[0], until: performance.now() + m.hl[1], ms: BR.healMs[m.hl[0]] } : null;
  const key = slots.join(',') + '|' + (m.g ? m.g[0] : '');
  if (key !== R.key) {
    R.key = key;
    const cur = W.cur, holdingMelee = !cur || (WEAPONS[cur] && WEAPONS[cur].slot === 'melee');
    let idx = slots.indexOf(cur);
    if (fresh && holdingMelee) idx = slots.indexOf(fresh[0]); // picked up your first gun: in your hands right away
    W.slot = idx >= 0 ? idx : 0;
    setLoadout({ only: slots, item: m.g ? m.g[0] : 'none' });
  }
  paintSlots();
}
function paintSlots() {
  const m = R.inv;
  if (!m) return;
  const tiers = m.s.filter(Boolean).map((g) => g[1]);
  if (m.m) tiers.push(m.m[1]);
  tiers.forEach((t, i) => { const s = $('slot-' + i); if (s) { s.classList.remove('br-t1', 'br-t2', 'br-t3', 'br-t4'); if (t) s.classList.add('br-t' + t); } });
}

// ------------------------------------------------------------ net
function start(m) {
  R.on = true; R.path = m.path; R.zone = m.zone; R.phase = m.phase;
  clearLoot(); for (const e of m.loot) addLoot(e);
  R.blimp = new Set(m.blimp); R.out = new Map(m.out); R.total = m.blimp.length + m.out.length;
  R.me = { inBlimp: R.blimp.has(G.myId), fly: null, late: false, place: 0 };
  R.inv = null; R.key = ''; R.held = new Set(); R.reserve = {}; R.shots = {}; R.ar = 0; R.heal = null; R.spec = 0; R.win = -1; R.autoT.clear();
  R.hook = null; R.hookHad = false; R.hookN = BR.hook.charges;
  W.br = hooks; G.noOob = true; G.brStep = step; G.hookGate = hookGate;
  twistsReset(); R.leader = m.leader || 0; for (const c of m.crates || []) addCrate(c); for (const id of m.goblins || []) R.goblins.set(id, null);
  if (!blimp) { blimp = buildBlimp(); [zoneWall, zoneNext] = buildZone(); myUmb = umbrella(); myUmb.visible = false; }
  for (const o of [blimp, zoneWall, zoneNext, myUmb]) if (!o.parent) G.scene.add(o);
  showHud(true);
  if (R.me.inBlimp) { big('JANK ROYALE', `SPACE to jump out of the blimp · F pick up · H heal · ${K.label('scores')} backpack`, 4); sfx.partyHorn(); }
}
function stop() {
  if (!R.on) return;
  R.on = false; W.br = null; G.noOob = false; G.brStep = null; G.brGlide = false; G.hookGate = null;
  clearLoot();
  for (const o of [blimp, zoneWall, zoneNext, myUmb]) if (o && o.parent) o.parent.remove(o);
  for (const u of R.umb.values()) if (u.parent) u.parent.remove(u);
  R.umb.clear();
  twistsReset();
  showHud(false);
  document.body.classList.remove('br-sky', 'br-spec');
  setLoadout(G.forcedLoadout || G.settings.loadout); refillAmmo();
}
function jump(auto) {
  if (!R.me.inBlimp) return;
  const bp = blimpAt(R.path, st());
  if (bp[3] <= 0 && !auto) { hud.msg('HOLD ON, WE HAVEN\'T TAKEN OFF', 1, 'brag'); return; }
  net.send({ t: 'brjump' });
  R.me.inBlimp = false; R.me.fly = 'fall';
  ME.pos = [bp[0], bp[1] - 3, bp[2]]; ME.vel = [R.path.d[0] * BR.blimp.speed * 0.5, 0, R.path.d[1] * BR.blimp.speed * 0.5];
  sfx.yeet(); hud.msg('GERONIMOOO', 1.2, 'brag');
}
net.on('br', (m) => {
  if (m.k === 'start') { start(m); return; }
  if (m.k === 'off') { stop(); return; }
  if (!R.on) return;
  const me = m.id === G.myId;
  if (m.k === 'hook') { R.hook = m.h || null; if (m.no) hookDenied(); return; }
  if (m.k === 'loot') for (const e of m.l) addLoot(e);
  else if (m.k === 'take') { const l = R.loot.get(m.i); if (l && m.by === G.myId) { sfx.cash(); hud.msg(`+ ${lootName(l)}`, 1, 'brag'); } removeLoot(m.i); }
  else if (m.k === 'board') { R.blimp.add(m.id); R.total++; if (me) R.me.inBlimp = true; }
  else if (m.k === 'jump') { R.blimp.delete(m.id); const r = G.remotes.get(m.id); if (r) r.buf.length = 0; }
  else if (m.k === 'eject') { if (R.me.inBlimp) jump(true); }
  else if (m.k === 'out') {
    R.out.set(m.id, m.place);
    if (me) {
      R.me.place = m.place; R.spec = m.by && m.by !== G.myId ? m.by : 0; R.specSnap = true;
      if (m.w === 'zone') hud.dead(true, [['the zone ate you', '#d6b4ff']]);
      setTimeout(() => { if (R.on && !ME.alive) big(`#${m.place}`, `out of ${R.total} · click to watch someone else`, 4); }, 400);
    }
  } else if (m.k === 'win') {
    R.win = m.id;
    if (me) { big('LAST IDIOT STANDING', 'you won the jank royale', 5); sfx.choir(); sfx.kill(); }
    else if (m.id) { const n = G.names.get(m.id); big(`${n ? n.name : '???'} WINS`, 'last one standing', 4); }
    else big('NOBODY WINS', 'the zone got everyone', 4);
  } else if (m.k === 'heal') { const r = G.remotes.get(m.id); sfx.heal(r ? r.pos : null); }
  else if (m.k === 'crack') { const r = G.remotes.get(m.id), p = r ? r.pos : ME.pos; sfx.crunch(r ? r.pos : null); fx.ring([p[0], p[1] + 1.1, p[2]], 1.6, 0x4fd8ff); if (me) hud.msg('ARMOUR BROKE', 1, 'brag'); }
  else if (m.k === 'late') { R.me.late = true; ME.alive = false; G.deadAt = performance.now(); big('MATCH IN PROGRESS', 'you can watch till the next drop', 4); }
  else twist(m, me);
});
net.on('brinv', (m) => { if (R.on) { applyInv(m); if (invOpen) invRender(); } });
net.on('brar', (m) => { R.ar = m.ar; });
// outgoing shots spend shot-counted ammo here too (the server counts the same 'fire's)
const send0 = net.send.bind(net);
net.send = (o) => { if (R.on && o && o.t === 'fire' && R.shots[o.w] != null && R.shots[o.w] > 0) R.shots[o.w]--; send0(o); };

// ------------------------------------------------------------ movement: the blimp, falling, the umbrella
function step(dt, inp, now) {
  if (!R.on || !ME.alive) return false;
  if (R.me.inBlimp) {
    const bp = blimpAt(R.path, st());
    ME.pos[0] = bp[0]; ME.pos[1] = bp[1] - 3; ME.pos[2] = bp[2]; ME.vel = [0, 0, 0]; ME.hook = null; ME.onGround = false;
    if (inp.jumpPressed) { inp.jumpPressed = false; jump(false); }
    if (blimpDone(R.path, st())) jump(true);
    return true;
  }
  const f = R.me.fly;
  if (!f) return false;
  ME.hook = null;
  const v = ME.vel, fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), sd = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * sd, wz = -c * fw - s * sd;
  const wl = Math.hypot(wx, wz); if (wl) { wx /= wl; wz /= wl; }
  const below = raycast([ME.pos[0], ME.pos[1], ME.pos[2]], [0, -1, 0], 300, BOXES), h = below ? below.t : 300;
  if (f === 'fall') {
    const dive = Math.max(0, -ME.pitch); // look down to dive faster
    v[1] = Math.max(-BR.fall.vMax * (1 + dive * 0.45), v[1] - 26 * dt);
    const sp = BR.fall.steer * (1 - dive * 0.3);
    v[0] += (wx * sp - v[0]) * Math.min(1, dt * 1.5); v[2] += (wz * sp - v[2]) * Math.min(1, dt * 1.5);
    if (h < BR.fall.open || (inp.jumpPressed && h > BR.glide.minOpen)) { R.me.fly = 'glide'; inp.jumpPressed = false; sfx.bigPop(); hud.msg('UMBRELLA OUT', 0.8, 'brag'); }
  } else {
    v[1] += (-BR.glide.vy - v[1]) * Math.min(1, dt * 4);
    if (!wl) { wx = -s * 0.35; wz = -c * 0.35; } // drift on the way you face
    v[0] += (wx * BR.glide.speed - v[0]) * Math.min(1, dt * 2); v[2] += (wz * BR.glide.speed - v[2]) * Math.min(1, dt * 2);
  }
  ME.eyeH += (PC.standEye - ME.eyeH) * Math.min(1, dt * 14);
  const res = movePlayer(ME.pos, v, dt, BOXES, false);
  ME.onGround = !!res.ground && v[1] <= 0;
  if (ME.onGround) { R.me.fly = null; v[0] *= 0.4; v[2] *= 0.4; sfx.thunk(); G.shake = Math.max(G.shake || 0, 0.4); }
  return true;
}

// ------------------------------------------------------------ cameras: the blimp ride (third person), spectating
const camPos = new THREE.Vector3(), tmp = new THREE.Vector3();
export function brCam(dt, cam) {
  if (!R.on || RP.active) return false;
  if (ME.alive && R.me.inBlimp) {
    const bp = blimpAt(R.path, st()), cp = Math.cos(ME.pitch);
    const d = [-Math.sin(ME.yaw) * cp, Math.sin(ME.pitch), -Math.cos(ME.yaw) * cp];
    cam.position.set(bp[0] - d[0] * 46, bp[1] + 6 - d[1] * 46, bp[2] - d[2] * 46);
    cam.lookAt(bp[0], bp[1] - 2, bp[2]);
    return true;
  }
  if (ME.alive) return false;
  // out: watch whoever got you (or anyone still in it)
  let r = G.remotes.get(R.spec);
  if (!r || !r.alive) { r = nextSpec(); }
  if (!r) return false;
  const yaw = r.yaw || 0, e = [r.pos[0], r.pos[1] + 1.9, r.pos[2]];
  const d = [Math.sin(yaw) * 4.6, 1.3, Math.cos(yaw) * 4.6], L = Math.hypot(...d);
  const hit = raycast(e, d.map((x) => x / L), L, BOXES);
  const k = hit ? Math.max(0.3, hit.t - 0.3) / L : 1;
  tmp.set(e[0] + d[0] * k, e[1] + d[1] * k, e[2] + d[2] * k);
  if (R.specSnap) { camPos.copy(tmp); R.specSnap = false; } else camPos.lerp(tmp, Math.min(1, dt * 10));
  cam.position.copy(camPos);
  cam.lookAt(e[0] - Math.sin(yaw) * 10, e[1] - 0.5, e[2] - Math.cos(yaw) * 10);
  return true;
}
function nextSpec() {
  const alive = [...G.remotes.values()].filter((x) => x.alive && !R.blimp.has(x.id) && !R.out.has(x.id));
  if (!alive.length) return null;
  const i = alive.findIndex((x) => x.id === R.spec);
  const r = alive[(i + 1) % alive.length];
  if (r.id !== R.spec) { R.spec = r.id; R.specSnap = true; }
  return r;
}

// ------------------------------------------------------------ grapple charges (BR.hook): the server counts, this shows + predicts
function hookGate() { // player.js tryHook asks first: true = no charge, no rope
  if (!R.on || !ME.alive || hookCharges(R.hook, st()).n >= 1) return false;
  hookDenied();
  return true;
}
function hookDenied() {
  ME.hook = null; // (the server cut it, or it never fired)
  const now = performance.now();
  if (now - (R.noT || 0) < 300) return;
  R.noT = now;
  const c = hookCharges(R.hook, st());
  sfx.hookNo(); hud.msg(`GRAPPLE RECHARGING · ${Math.max(1, Math.ceil((1 - c.k) * BR.hook.cd))}s`, 0.8, 'brag');
  if (el) { el.hook.classList.remove('no'); void el.hook.offsetWidth; el.hook.classList.add('no'); }
}
const RING = 2 * Math.PI * 19;
function hookFrame() {
  const roped = !!ME.hook;
  if (roped && !R.hookHad) R.hook = hookSpend(R.hook, st()) || R.hook; // a new rope: spend one now (the server's count follows)
  R.hookHad = roped;
  const H = BR.hook, c = hookCharges(R.hook, st());
  if (c.n > R.hookN && ME.alive) sfx.hookReady();
  R.hookN = c.n;
  const h = el.hook, full = c.n >= H.charges;
  h.className = full ? 'full' : c.n === 0 ? 'none' : '';
  h.querySelector('.fl').style.strokeDasharray = `${(full ? 1 : c.k) * RING} ${RING}`;
  h.querySelector('span').textContent = '●'.repeat(c.n) + '○'.repeat(H.charges - c.n);
  h.querySelector('small').textContent = full ? `${K.label('grapple')} GRAPPLE` : `${K.label('grapple')} ${Math.ceil((1 - c.k) * H.cd)}s`;
}

// ------------------------------------------------------------ the backpack (the scoreboard key, Tab): your loot, drop it, swap the gun slots
// the mouse is free while it's open and you keep moving (wasd still works), like a looter shooter's inventory
let invOpen = false, invLock = null, invT = 0;
export const brInvOpen = () => invOpen;
export function brInvToggle(lock) { // main.js: the scores key in a royale. true = handled
  if (!R.on || !ME.alive) return false;
  if (invOpen) { invClose(true); return true; }
  ensureHud();
  invOpen = true; invLock = lock || null;
  document.body.classList.add('br-inv');
  if (document.pointerLockElement) document.exitPointerLock(); // a real cursor (main.js doesn't pause for this)
  W.held = false; W.aimHeld = false;
  invRender(); sfx.click();
  return true;
}
function invClose(relock) {
  if (!invOpen) return;
  invOpen = false;
  document.body.classList.remove('br-inv');
  if (relock && invLock && G.joined && $('menu').classList.contains('hidden')) invLock();
}
const mkEl = (tag, cls, text) => { const d = document.createElement(tag); if (cls) d.className = cls; if (text != null) d.textContent = text; return d; };
function btn(label, cls, fn) { const b = mkEl('button', cls, label); b.addEventListener('click', (ev) => { ev.stopPropagation(); fn(); sfx.click(); }); return b; }
function gunTile(m, i) {
  const g = m.s[i], t = mkEl('div', 'bi-t' + (g ? '' : ' empty'));
  const kb = mkEl('kbd', '', K.label('slot' + (i + 1)));
  if (!g) { t.append(kb, mkEl('span', '', 'empty: walk over a gun')); }
  else {
    const [w, tier, a] = g, wd = WEAPONS[w];
    t.style.setProperty('--c', TIERS[tier].color);
    const img = mkEl('img'); img.alt = ''; img.src = weaponIcon(w, (G.equipped || {})[w]);
    const ammo = a < 0 ? '∞' : wd.mag ? `${W.ammo[w] || 0} + ${R.reserve[w] || 0}` : `${R.shots[w] ?? a} shots`;
    const b = mkEl('div', 'bi-b');
    b.append(btn('⇄ SWAP', 'yel', () => net.send({ t: 'brswap' })), btn('DROP', 'red', () => net.send({ t: 'brdrop', k: 'gun', i })));
    t.append(kb, img, mkEl('b', '', `${TIERS[tier].name} ${wd.name}`), mkEl('i', '', `ammo ${ammo}`), b);
    t.draggable = true;
    t.addEventListener('dragstart', (ev) => { ev.dataTransfer.setData('text/plain', 'brgun' + i); t.classList.add('drag'); });
    t.addEventListener('dragend', () => t.classList.remove('drag'));
    t.addEventListener('contextmenu', () => { net.send({ t: 'brdrop', k: 'gun', i }); sfx.click(); }); // right click drops
  }
  t.addEventListener('dragover', (ev) => { ev.preventDefault(); t.classList.add('over'); });
  t.addEventListener('dragleave', () => t.classList.remove('over'));
  t.addEventListener('drop', (ev) => { ev.preventDefault(); t.classList.remove('over'); const d = ev.dataTransfer.getData('text/plain'); if (d === 'brgun' + (1 - i)) { net.send({ t: 'brswap' }); sfx.click(); } });
  return t;
}
function sideTile(kind, m) {
  const t = mkEl('div', 'bi-t');
  if (kind === 'melee') {
    const [w, tier] = m.m || [BR.melee, 0];
    t.style.setProperty('--c', TIERS[tier || 0].color);
    const img = mkEl('img'); img.alt = ''; img.src = weaponIcon(w, (G.equipped || {})[w]);
    t.append(mkEl('kbd', '', K.label('slot3')), img, mkEl('b', '', `${tier ? TIERS[tier].name + ' ' : ''}${WEAPONS[w] ? WEAPONS[w].name : w}`), mkEl('i', '', w === BR.melee ? 'the loaf stays with you' : 'melee'));
    if (w !== BR.melee) { const b = mkEl('div', 'bi-b'); b.append(btn('DROP', 'red', () => net.send({ t: 'brdrop', k: 'melee' }))); t.append(b); t.addEventListener('contextmenu', () => net.send({ t: 'brdrop', k: 'melee' })); }
    return t;
  }
  if (!m.g) { t.classList.add('empty'); t.append(mkEl('span', '', 'no gadget')); return t; }
  const [id, n] = m.g, it = ITEMS[id] || {};
  t.style.setProperty('--c', it.color || '#9ab04a');
  const img = mkEl('img'); img.alt = ''; img.src = itemIcon(id);
  const b = mkEl('div', 'bi-b'); b.append(btn('DROP', 'red', () => net.send({ t: 'brdrop', k: 'gadget' })));
  t.append(mkEl('kbd', '', K.label('item')), img, mkEl('b', '', it.name || id), mkEl('i', '', `x${n}`), b);
  t.addEventListener('contextmenu', () => net.send({ t: 'brdrop', k: 'gadget' }));
  return t;
}
function invSide(box) {
  box.textContent = '';
  const alive = [...G.remotes.values()].filter((r) => r.alive && !R.out.has(r.id)).length + (ME.alive && !R.out.has(G.myId) ? 1 : 0);
  box.append(mkEl('div', 'big', `${alive} ALIVE`), mkEl('div', '', `your kills: ${G.kills || 0}`));
  const zn = zoneAt(R.zone, st());
  if (zn) { const secs = Math.ceil(zn.left / 1000); box.append(mkEl('div', '', zn.shrinking ? `zone closing ${secs}s` : zn.next ? `zone closes in ${secs}s` : 'final zone')); }
  box.append(mkEl('div', 'bi-h', 'TOP JANKERS'));
  const rows = [{ id: G.myId, name: G.myName, k: G.kills || 0, me: true }, ...[...G.remotes.values()].filter((r) => !R.out.has(r.id) || r.k).map((r) => ({ id: r.id, name: r.name, k: r.k || 0 }))];
  rows.sort((a, b) => b.k - a.k);
  const ol = mkEl('ol');
  for (const r of rows.slice(0, 6)) { const li = mkEl('li', (r.me ? 'me' : '') + (R.out.has(r.id) ? ' dead' : ''), `${r.name} · ${r.k}`); ol.append(li); }
  box.append(ol, mkEl('div', 'bi-help', `hold ${K.label('brScores')}: full scoreboard`));
}
function invRender() {
  ensureHud();
  const m = R.inv || { s: [0, 0], m: [BR.melee, 0], g: 0, c: 0, k: 0, ar: 0 };
  const root = el.inv; root.textContent = '';
  const bi = mkEl('div', 'bi');
  bi.append(mkEl('h2', '', 'BACKPACK'), mkEl('p', 'bi-help', `drag a gun onto the other slot (or ⇄) to swap · DROP or right click puts it on the floor · ${K.label('scores')} / ESC close · keep walking, it's fine`));
  const grid = mkEl('div', 'bi-grid');
  const col = (h, ...kids) => { const d = mkEl('div'); for (let i = 0; i < kids.length; i++) d.append(mkEl('div', 'bi-h', h[i]), kids[i]); return d; };
  const side = mkEl('div', 'bi-side'); invSide(side);
  grid.append(col(['GUN 1'], gunTile(m, 0)), col(['GUN 2'], gunTile(m, 1)), col(['MELEE', 'GADGET'], sideTile('melee', m), sideTile('gadget', m)), side);
  const heals = mkEl('div');
  heals.append(mkEl('div', 'bi-h', 'HEALS (H) + ARMOUR'));
  for (const [k, n, cap, name] of [['cola', m.c || 0, BR.cola.n, STUFF.cola.name], ['medkit', m.k || 0, BR.medkit.n, STUFF.medkit.name]]) {
    const r = mkEl('div', 'bi-row'); r.style.borderLeft = `4px solid ${STUFF[k].color}`;
    r.append(mkEl('b', '', `${n}/${cap}`), mkEl('span', '', `${name}: +${BR[k].heal} HP`));
    if (n > 0) r.append(btn('USE', 'yel', () => net.send({ t: 'brheal', k })), btn('DROP 1', 'red', () => net.send({ t: 'brdrop', k, n: 1 })));
    heals.append(r);
  }
  const ar = mkEl('div', 'bi-row'), bar = mkEl('div', 'bi-ar'), fill = mkEl('div');
  bar.style.flex = '1'; fill.style.width = Math.min(100, R.ar || 0) + '%'; bar.append(fill);
  ar.append(mkEl('b', '', `${R.ar || 0}`), mkEl('span', '', 'armour'), bar); ar.querySelector('span').style.flex = 'none';
  heals.append(ar);
  heals.style.gridColumn = '1 / 4';
  grid.append(heals);
  bi.append(grid);
  root.append(bi);
  el.invSide = side;
}

// ------------------------------------------------------------ input
function nearest() {
  let best = null, bd = 1e9;
  const f = [-Math.sin(ME.yaw), -Math.cos(ME.yaw)];
  for (const l of R.loot.values()) {
    const dx = l.p[0] - ME.pos[0], dz = l.p[2] - ME.pos[2], d = Math.hypot(dx, dz);
    if (d > BR.pickR || l.p[1] - ME.pos[1] > 2 || ME.pos[1] - l.p[1] > 1.9) continue;
    const facing = d < 0.9 ? 1 : (dx * f[0] + dz * f[1]) / d;
    const score = d - facing * 1.2;
    if (score < bd) { bd = score; best = l; }
  }
  return best;
}
export function brKey(e) {
  if (!R.on) return false;
  if (invOpen && e.code === 'Escape') { invClose(true); return true; }
  if (!ME.alive) {
    if (e.code === 'Space') { e.preventDefault(); if (!e.repeat && !RP.active && !G.killcamPending) nextSpec(); return !RP.active && !G.killcamPending; }
    return false;
  }
  if (R.me.inBlimp && (e.code === 'KeyE' || e.code === 'KeyG' || e.code === 'KeyF')) return true;
  if (R.me.fly && e.code === 'KeyE') return true; // no grapple in the sky (you're holding an umbrella)
  if (e.code === 'KeyF' && !e.repeat && R.focus) { net.send({ t: 'brpick', i: R.focus.i, f: 1 }); return true; }
  if (e.code === 'KeyF' && !e.repeat && R.vend >= 0) { net.send({ t: 'brkick' }); return true; } // Neon Market: kick the vending machine
  if (e.code === 'KeyH' && !e.repeat) {
    const inv = R.inv || {}, need = 100 - ME.hp;
    if (need <= 0) { hud.msg('ALREADY HEALTHY', 0.8); return true; }
    const k = need > 45 && inv.k ? 'medkit' : inv.c ? 'cola' : inv.k ? 'medkit' : null;
    if (!k) { hud.msg('NO HEALS: FIND JANK COLA OR A MEDKIT', 1.2); sfx.empty(); return true; }
    net.send({ t: 'brheal', k }); return true;
  }
  return false;
}
export function brMouse(e) {
  if (!R.on) return false;
  if (!ME.alive) { if (!RP.active && !G.killcamPending && e.button === 0) { nextSpec(); return true; } return false; }
  return R.me.inBlimp || !!R.me.fly; // nothing to shoot from up here (both hands on the umbrella)
}

// kill feed lines for the zone
export function brFeed(m, vn, vc) {
  if (!R.on || m.w !== 'zone') return null;
  return [[vn, vc], ['  got eaten by the zone', '#b07dff']];
}
// end screen: placements
export function brRoundEnd(m, box) {
  if (!m.br || !m.br.length) return;
  for (const row of [...box.children]) if (row.tagName !== 'H3') row.remove();
  const rows = m.br.slice().sort((a, b) => (a[1] || 999) - (b[1] || 999));
  const shown = rows.slice(0, 8);
  const mine = rows.find((r) => r[0] === G.myId);
  if (mine && !shown.includes(mine)) shown.push(mine);
  for (const [id, place, kills] of shown) {
    const d = document.createElement('div'); d.className = 'br-row';
    const n = id === G.myId ? { name: G.myName } : G.names.get(id) || { name: '???' };
    d.innerHTML = `<b>#${place || '?'}</b><span></span><i>${kills} kill${kills === 1 ? '' : 's'}</i>`;
    d.querySelector('span').textContent = n.name;
    if (id === G.myId) d.style.color = '#ffe14d';
    box.append(d);
  }
}

// ------------------------------------------------------------ every frame
export const brActive = () => !!R.on; // the HUD minimap stays out of the way (royale has its own map)
export function brFrame(dt, now) {
  if (!R.on) return;
  const t = st(), zn = zoneAt(R.zone, t);
  if (R.phase !== 'live' && R.path && blimpDone(R.path, t) && !R.blimp.size) R.phase = 'live';
  // blimp
  const bp = blimpAt(R.path, t), gone = blimpDone(R.path, t) && !R.me.inBlimp;
  blimp.visible = !gone && !RP.active;
  if (blimp.visible) {
    blimp.position.set(bp[0], bp[1] + 4, bp[2]);
    blimp.rotation.y = Math.atan2(-R.path.d[0], -R.path.d[1]);
    blimp.rotation.z = Math.sin(now * 0.0006) * 0.04;
    for (const p of blimp.userData.props) p.rotation.z += dt * 18;
  }
  // zone wall + the next circle on the ground
  if (zn) {
    zoneWall.position.set(zn.c[0], 120, zn.c[1]); zoneWall.scale.set(Math.max(0.1, zn.r), 360, Math.max(0.1, zn.r));
    zoneWall.material.uniforms.uTime.value = now / 1000;
    zoneNext.visible = !!zn.next && !RP.active;
    if (zn.next) { zoneNext.position.set(zn.next.c[0], 1, zn.next.c[1]); zoneNext.scale.set(Math.max(0.1, zn.next.r), 2.4, Math.max(0.1, zn.next.r)); }
  }
  // the other players: hidden while they ride the blimp; an umbrella over anyone gliding
  for (const r of G.remotes.values()) {
    const inB = R.blimp.has(r.id) && r.alive;
    if (inB) { r.ch.root.visible = false; if (r.shadow) r.shadow.visible = false; if (r.rope) r.rope.visible = false; }
    let u = R.umb.get(r.id);
    const gl = !inB && r.alive && !RP.active && (r.f & FLAGS.GLIDE);
    if (gl && !u) { u = umbrella(); R.umb.set(r.id, u); G.scene.add(u); }
    if (u) { u.visible = !!gl; if (gl) { u.position.set(r.pos[0], r.pos[1] + 3.1, r.pos[2]); u.rotation.y += dt * 2; } }
  }
  myUmb.visible = ME.alive && R.me.fly === 'glide';
  if (myUmb.visible) { myUmb.position.set(ME.pos[0], ME.pos[1] + 3.3, ME.pos[2]); myUmb.rotation.y += dt * 2; }
  G.brGlide = ME.alive && R.me.fly === 'glide';
  document.body.classList.toggle('br-sky', ME.alive && (R.me.inBlimp || !!R.me.fly));
  document.body.classList.toggle('br-spec', !ME.alive);
  // loot: models only near you, rings and beams further out
  for (const l of R.loot.values()) {
    const d = Math.hypot(l.p[0] - ME.pos[0], l.p[2] - ME.pos[2]);
    const near = d < 42 && !RP.active;
    if (near && !l.mesh) { l.mesh = lootMesh(l); l.mesh.position.set(...l.p); G.scene.add(l.mesh); }
    else if (!near && l.mesh && d > 55) { G.scene.remove(l.mesh); freeTree(l.mesh); l.mesh = null; }
    if (l.mesh) { l.mesh.visible = near; l.mesh.userData.item.position.y = 0.45 + Math.sin(now * 0.003 + l.ph) * 0.08; l.mesh.userData.item.rotation.y = now * 0.0012 + l.ph; }
    l.ring.visible = d < 70 && !RP.active;
    if (l.beam) l.beam.visible = d < 140 && d > 6 && !RP.active;
  }
  // pick-up prompt + walking over free stuff
  ensureHud();
  R.focus = ME.alive && !R.me.inBlimp && !R.me.fly ? nearest() : null;
  if (R.focus) {
    const l = R.focus, inv = R.inv;
    let sub = '';
    if (l.k === 'gun' && inv && inv.s.every(Boolean) && !inv.s.some((g) => g && g[0] === l.id)) { const hold = inv.s.find((g) => g[0] === W.cur) || inv.s[0]; sub = `swaps your ${TIERS[hold[1]].name} ${WEAPONS[hold[0]].name}`; }
    else if (l.k === 'gun' && WEAPONS[l.id]) sub = WEAPONS[l.id].desc || '';
    else if (STUFF[l.id]) sub = STUFF[l.id].desc;
    else if (l.k === 'gadget' && ITEMS[l.id]) sub = ITEMS[l.id].desc || '';
    el.prompt.innerHTML = `<kbd>F</kbd><span></span><small></small>`;
    el.prompt.querySelector('span').textContent = lootName(l);
    el.prompt.querySelector('small').textContent = sub;
    el.prompt.style.setProperty('--c', lootColor(l));
    el.prompt.style.display = 'block';
    el.prompt.querySelector('span').style.color = lootColor(l);
  } else el.prompt.style.display = 'none';
  if (ME.alive && !R.me.inBlimp && !R.me.fly && R.inv) for (const l of R.loot.values()) {
    if (l.k !== 'ammo' && l.k !== 'heal' && l.k !== 'armor') continue;
    if (Math.hypot(l.p[0] - ME.pos[0], l.p[2] - ME.pos[2]) > BR.autoR || Math.abs(l.p[1] - ME.pos[1]) > 1.6) continue;
    if (now < (R.autoT.get(l.i) || 0)) continue;
    const inv = R.inv;
    if (l.k === 'armor' && R.ar >= BR.armor.max) continue;
    if (l.k === 'heal' && (l.id === 'cola' ? inv.c >= BR.cola.n : inv.k >= BR.medkit.n)) continue;
    if (l.k === 'ammo' && !inv.s.some((g) => g && g[2] >= 0)) continue;
    R.autoT.set(l.i, now + 700);
    net.send({ t: 'brpick', i: l.i });
  }
  twistFrame(dt, now, t);
  hookFrame();
  if (invOpen && !ME.alive) invClose(false);
  if (invOpen && now > invT && el.invSide) { invT = now + 500; invSide(el.invSide); }
  // HUD: alive, kills, zone clock, armour, heals, healing bar, minimap, outside-the-zone warning
  const alive = [...G.remotes.values()].filter((r) => r.alive && !R.out.has(r.id)).length + (ME.alive && !R.out.has(G.myId) ? 1 : 0);
  const secs = zn ? Math.ceil(zn.left / 1000) : 0, mm = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
  const zt = !zn ? '' : zn.shrinking ? `<i>ZONE CLOSING ${mm}</i>` : zn.next ? `zone closes in <b>${mm}</b>` : '<i>FINAL ZONE</i>';
  el.stat.innerHTML = `<b>${alive}</b> ALIVE · <b>${G.kills || 0}</b> KILLS<br>${zt}`;
  drawMap(now, zn);
  el.armor.querySelector('div').style.width = Math.min(100, R.ar) + '%';
  el.armor.querySelector('span').textContent = R.ar > 0 ? `ARMOUR ${R.ar}` : '';
  const inv = R.inv || { c: 0, k: 0 };
  el.heals.innerHTML = `H · <b>${inv.c || 0}</b> cola · <b>${inv.k || 0}</b> medkit`;
  if (R.heal && ME.alive) {
    const k = 1 - Math.max(0, R.heal.until - performance.now()) / R.heal.ms;
    el.healBar.style.display = k < 1 ? 'block' : 'none';
    el.healBar.querySelector('div').style.width = Math.round(k * 100) + '%';
    el.healBar.querySelector('span').textContent = R.heal.k === 'cola' ? 'DRINKING JANK COLA...' : 'PATCHING UP...';
  } else el.healBar.style.display = 'none';
  const outside = ME.alive && !R.me.inBlimp && zn && outsideZone(zn, ME.pos);
  el.zone.style.opacity = outside ? 1 : 0;
  if (outside && now > R.zoneTick) { R.zoneTick = now + 1000; sfx.oob(false); }
  if (bigT && now > bigT) { el.big.style.display = 'none'; bigT = 0; }
  if (!ME.alive) {
    const r = G.remotes.get(R.spec), dt2 = $('deadTimer');
    if (dt2 && !G.killcamPending && !R.mailAt) dt2.textContent = r ? `spectating ${r.name} · click or space for someone else` : R.me.late ? 'match in progress: the next drop is soon' : 'spectating';
  }
}
export const brState = () => R; // (tests + the console)
export function brReset() { stop(); } // leaving the room (to the menu, or into another room): no royale left behind

// ------------------------------------------------------------ the twists + POI rules (server decides, this shows them)
let crown = null;
const crateGeo = new THREE.BoxGeometry(1.6, 1.6, 1.6);
function crateMesh() {
  const g = new THREE.Group();
  const box = new THREE.Mesh(crateGeo, mat(0xc9a36a)); g.add(box);
  for (const s of [-1, 1]) { const band = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.2, 1.7), mat(0xff4fd8)); band.position.y = s * 0.5; g.add(band); }
  const u = umbrella(); u.scale.setScalar(2.4); u.position.y = 4.2; g.add(u);
  const beam = new THREE.Mesh(beamGeo, beamMats[4]); beam.scale.set(2, 60, 2); beam.position.y = 30; g.add(beam);
  return g;
}
function addCrate(c) {
  const [id, x, z, y0, land, v, t0] = c;
  const cr = { id, x, z, y0, land, v, t0, mesh: crateMesh() };
  G.scene.add(cr.mesh);
  R.crates.set(id, cr);
}
function goblinMesh() { // a vending machine with legs and googly eyes. it knows what you want
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.9, 0.9), mat(0x39ff14)); body.position.y = 1.65; g.add(body);
  const win = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.1, 0.05), new THREE.MeshBasicMaterial({ color: 0xff4fd8 })); win.position.set(0, 1.75, -0.47); g.add(win);
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff })); eye.position.set(s * 0.25, 2.45, -0.48); g.add(eye);
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.07, 6, 4), new THREE.MeshBasicMaterial({ color: 0x000000 })); pupil.position.set(s * 0.25 + 0.04, 2.42, -0.6); g.add(pupil);
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.75, 0.18), mat(0x222222)); leg.position.set(s * 0.35, 0.38, 0); leg.name = 'leg' + s; g.add(leg);
  }
  return g;
}
function twistsReset() {
  for (const c of R.crates.values()) G.scene.remove(c.mesh);
  R.crates.clear();
  for (const m of R.goblins.values()) if (m) G.scene.remove(m);
  R.goblins.clear();
  if (crown && crown.parent) crown.parent.remove(crown);
  R.leader = 0; R.poi = null; R.vend = -1; R.mailAt = 0;
  for (const r of G.remotes.values()) if (r.brTag) { r.brTag.visible = false; r.tag.visible = true; }
}
const nm = (id) => (id === G.myId ? 'YOU' : (G.names.get(id) || { name: '???' }).name);
function twist(m, me) {
  if (m.k === 'mail') {
    if (me) { R.mailAt = performance.now() + m.ms; big('RETURNED TO SENDER', 'back in 5 seconds, in a box, somewhere in the next circle', 4.5); sfx.cash(); }
    else hud.chat(null, null, `${nm(m.id)} got RETURNED TO SENDER`);
  } else if (m.k === 'mailed') {
    if (me) { R.mailAt = 0; R.me.fly = 'fall'; R.me.inBlimp = false; ME.vel = [0, -4, 0]; big('SPECIAL DELIVERY', 'you, again. fragile. this way up', 2.5); sfx.yeet(); }
    const r = G.remotes.get(m.id); if (r) r.buf.length = 0;
  } else if (m.k === 'leader') {
    R.leader = m.id;
    if (me) { hud.msg('YOU ARE THE KILL LEADER', 2.2, 'brag'); hud.chat(null, null, 'everyone can see you on the map now. there is a bounty on you'); }
    else if (m.id) hud.chat(null, null, `${nm(m.id)} is the kill leader (${m.n} kills): the bounty is a Legendary`);
  } else if (m.k === 'bounty') { hud.msg(`BOUNTY CLAIMED BY ${nm(m.by).toUpperCase()}`, 2.2, 'brag'); if (m.by === G.myId) sfx.cash(); }
  else if (m.k === 'crate') { addCrate(m.c); hud.msg('SUPPLY DROP INCOMING', 2.2, 'brag'); hud.chat(null, null, 'a supply crate is coming down over the next circle (grab it in the air)'); sfx.partyHorn(); }
  else if (m.k === 'crateopen') { const c = R.crates.get(m.id); if (c) { fx.ring([c.x, c.land + 0.5, c.z], 4, 0xffe14d); G.scene.remove(c.mesh); R.crates.delete(m.id); } if (m.by === G.myId) { hud.msg('YOU CAUGHT THE SUPPLY CRATE', 2, 'brag'); sfx.cash(); } }
  else if (m.k === 'goblin') { R.goblins.set(m.id, null); hud.msg('A LOOT GOBLIN APPEARED', 2.2, 'brag'); hud.chat(null, null, 'a vending machine on legs, full of epics. it runs'); }
  else if (m.k === 'goblinpop') { const g = R.goblins.get(m.id); if (g) { fx.ring([g.position.x, g.position.y + 1.5, g.position.z], 5, 0x39ff14); G.scene.remove(g); } R.goblins.delete(m.id); hud.msg(m.by === G.myId ? 'YOU POPPED THE LOOT GOBLIN' : `${nm(m.by)} popped the loot goblin`, 2, 'brag'); }
  else if (m.k === 'dividend') { if (me) { hud.msg('SHAREHOLDER DIVIDEND · +25 ARMOUR', 1.8, 'brag'); sfx.cash(); } }
  else if (m.k === 'num') {
    const r = me ? null : G.remotes.get(m.id);
    if (me) hud.msg(m.n === 7 ? 'LUCKY 7' : 'UNLUCKY 13', 0.8, 'brag');
    else if (r) { const v = new THREE.Vector3(r.pos[0], r.pos[1] + 2.6, r.pos[2]).project(G.camera); if (v.z < 1) hud.dmgNum((v.x * 0.5 + 0.5) * innerWidth, (-v.y * 0.5 + 0.5) * innerHeight - 30, m.n, m.n === 13); }
  } else if (m.k === 'kick') {
    if (m.ok && m.id === G.myId) { sfx.clang && sfx.clang(null, 0.6); hud.msg('THE MACHINE COUGHED UP A GADGET', 1.4, 'brag'); }
    else if (!m.ok) hud.msg("IT'S EMPTY. COME BACK IN A MINUTE", 1.2);
  }
}
// the pronoun park: name tags say THEY while you're in there
function pronounTag(r, on) {
  if (on && !r.brTag) { r.brTag = makeNameTag('THEY', '#ff9a3a'); r.brTag.material.fog = false; r.brTag.position.y = r.tag.position.y; r.ch.root.add(r.brTag); }
  if (r.brTag) r.brTag.visible = on;
  r.tag.visible = !on;
}
export function brNames(m, kn, vn) { // the kill feed in the park: no names
  if (!R.on || !m.pos) return [kn, vn];
  const p = poiAt(MAPS[G.cfg.map], m.pos);
  if (!p || p.mod !== 'pronouns') return [kn, vn];
  return [m.k === G.myId ? 'YOU' : 'THEY', m.v === G.myId ? 'YOU' : 'THEM'];
}
function twistFrame(dt, now, t) {
  const map = MAPS[G.cfg.map];
  // crates coming down
  for (const c of R.crates.values()) { const y = Math.max(c.land, c.y0 - c.v * (t - c.t0) / 1000); c.mesh.position.set(c.x, y + 0.8, c.z); c.mesh.rotation.y += dt * 0.6; c.mesh.visible = !RP.active; }
  // goblins: the vending machine over the mannequin, legs going
  for (const [id, g0] of R.goblins) {
    const r = G.remotes.get(id);
    if (!r) continue;
    let g = g0;
    if (!g) { g = goblinMesh(); G.scene.add(g); R.goblins.set(id, g); }
    r.ch.root.visible = false; if (r.shadow) r.shadow.visible = false;
    g.visible = r.alive && !RP.active;
    g.position.set(r.pos[0], r.pos[1], r.pos[2]); g.rotation.y = r.yaw || 0;
    const sp = Math.hypot(r.vel[0], r.vel[2]), ph = now * 0.02 * Math.min(1, sp / 4);
    for (const s of [-1, 1]) { const leg = g.getObjectByName('leg' + s); if (leg) leg.rotation.x = Math.sin(ph + (s > 0 ? Math.PI : 0)) * 0.8; }
  }
  // the kill leader wears a crown everyone can see
  const ld = R.leader && R.leader !== G.myId ? G.remotes.get(R.leader) : null;
  if (ld && ld.alive && !RP.active) {
    if (!crown) { crown = new THREE.Group(); const b = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.36, 0.3, 6, 1, true), new THREE.MeshBasicMaterial({ color: 0xffe14d, side: THREE.DoubleSide })); crown.add(b); for (let k = 0; k < 6; k++) { const sp = new THREE.Mesh(new THREE.ConeGeometry(0.09, 0.3, 4), new THREE.MeshBasicMaterial({ color: 0xffe14d })); sp.position.set(Math.cos(k) * 0.4, 0.28, Math.sin(k) * 0.4); crown.add(sp); } const beam = new THREE.Mesh(beamGeo, beamMats[4]); beam.scale.set(1, 30, 1); beam.position.y = 15.5; crown.add(beam); }
    if (!crown.parent) G.scene.add(crown);
    crown.position.set(ld.pos[0], ld.pos[1] + 2.75, ld.pos[2]); crown.rotation.y += dt * 2;
  } else if (crown && crown.parent) crown.parent.remove(crown);
  // POIs: a callout when you walk in, and the rule
  const me = ME.alive && !R.me.inBlimp;
  const poi = me ? poiAt(map, ME.pos) : null;
  if (poi !== R.poi) { R.poi = poi; if (poi) { big(poi.name.toUpperCase(), poi.blurb, 2.6); sfx.ting(); } }
  if (poi && poi.mod === 'lowgrav' && !R.me.fly) ME.moonUntil = Math.max(ME.moonUntil || 0, performance.now() + 600); // Overdraft Heights: moon gravity (a margin for slow frames)
  for (const r of G.remotes.values()) { const rp = poiAt(map, r.pos); pronounTag(r, !!(rp && rp.mod === 'pronouns') && !R.goblins.has(r.id)); }
  // Neon Market vending machines: F to kick one
  R.vend = -1;
  if (me && !R.focus && poi && poi.mod === 'vending') (map.vending || []).forEach((v, i) => { if (Math.hypot(v[0] - ME.pos[0], v[1] - ME.pos[2]) < 2.2) R.vend = i; });
  if (R.vend >= 0) { el.prompt.innerHTML = '<kbd>F</kbd><span>KICK THE VENDING MACHINE</span><small>it might cough up a gadget</small>'; el.prompt.style.setProperty('--c', '#ff4fd8'); el.prompt.style.display = 'block'; }
  if (R.mailAt && !ME.alive) { const dt2 = $('deadTimer'); if (dt2) dt2.textContent = `RETURNED TO SENDER: back in ${Math.max(0, Math.ceil((R.mailAt - performance.now()) / 1000))}`; }
}
export const brSpecId = () => (R.on && !ME.alive && !R.me.inBlimp ? R.spec : 0); // who you're watching (pip.js shows their eyes)
