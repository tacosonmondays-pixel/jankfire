// Loadouts per mode on the customize screen: QUICK PLAY (the usual loadout) and ZOMBIES (the pistol you start with,
// the item you bring, one passive). Plant & Defuse and Jank Royale hand out their own gear, so they have no tab.
// The zombies one is saved in your settings (and your account profile, like the rest of them) and sent to the server,
// which checks it and hands it out when a zombies game starts (server/zmextra.js).
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { WEAPONS, ITEMS, ITEM_ORDER } from '/shared/weapons.js';
import { ZM_PISTOLS, ZM_PASSIVES, zmValidLoadout } from '/shared/zombies.js';
import { weaponIcon, objIcon } from './icons.js';
import { itemPic } from './itemicons.js';
import { K } from './keys.js';

let tab = 'qp', bar = null;
export const zlGet = () => (G.settings.zload = zmValidLoadout(G.settings.zload, ITEMS)); // always a good one
export function zlWant() { return zlGet(); } // for the join message
export const zlTab = () => tab;

// the QUICK PLAY / ZOMBIES switch over the loadout rows (customize.js calls this when it opens in loadout mode)
export function zlMount(root, redraw) {
  if (!bar) {
    bar = document.createElement('div');
    bar.className = 'zl-tabs';
    for (const [id, name, sub] of [['qp', 'QUICK PLAY', ''], ['zm', 'ZOMBIES', '']]) {
      const b = document.createElement('button');
      b.dataset.zl = id;
      b.innerHTML = `<b>${name}</b>${sub ? `<small>${sub}</small>` : ''}`; // (the rows under the tabs already say what's in them)
      b.addEventListener('click', () => { tab = id; mark(); redraw(); });
      bar.append(b);
    }
    const note = document.createElement('span'); note.className = 'zl-note'; note.textContent = 'plant & defuse and jank royale: you get your gear in the match';
    bar.append(note);
    const css = document.createElement('style');
    css.textContent = `
#scr-customize .zl-tabs { transform: rotate(-1deg); display: flex; gap: 10px; align-items: flex-end; white-space: nowrap; align-self: flex-start; margin-left: 12px; }
#scr-customize:not(.lo-mode) .zl-tabs { display: none; }
#scr-customize .zl-tabs button { font-family: var(--font); background: #fff; color: #000; border: 3px solid #000; box-shadow: 4px 4px 0 var(--pink); padding: 4px 14px 3px; cursor: pointer; text-align: left; }
#scr-customize .zl-tabs button b { display: block; font-size: 17px; letter-spacing: 1px; }
#scr-customize .zl-tabs button small { display: block; font-size: 10px; opacity: 0.7; }
#scr-customize .zl-tabs button.on { background: var(--yellow); transform: rotate(-2deg) translateY(-3px); box-shadow: 5px 5px 0 var(--cyan); }
#scr-customize .zl-tabs button[data-zl="zm"].on { background: #7dff4f; }
#scr-customize .zl-tabs .zl-note { font-size: 11px; color: #c8b8d8; text-shadow: 1px 1px 0 #000; margin-left: 6px; }
#scr-customize.zl-zm .cz-left .cz-list { opacity: 0.35; pointer-events: none; filter: grayscale(0.7); }
#scr-customize .cz-tile.zl-perk .pic img { image-rendering: auto; }`;
    document.head.append(css);
  }
  const lo = root.querySelector('.cz-lo');
  if (lo && bar.nextElementSibling !== lo) lo.before(bar); // above the rows (renderLo empties the rows box)
  mark();
  function mark() { for (const b of bar.querySelectorAll('button')) b.classList.toggle('on', b.dataset.zl === tab); root.classList.toggle('zl-zm', tab === 'zm' && root.classList.contains('lo-mode')); }
}

// the ZOMBIES rows. true = drawn (customize.js skips its own rows). h: { loTile, toast, save }
export function zlRender(box, h) {
  if (tab !== 'zm') return false;
  const cur = zlGet();
  const row = (title, list) => { const r = document.createElement('div'); r.className = 'cz-lorow'; const t = document.createElement('div'); t.className = 'cz-lot'; t.textContent = title; const tl = document.createElement('div'); tl.className = 'cz-tiles'; tl.append(...list); r.append(t, tl); box.append(r); };
  const set = (k, v, what) => {
    G.settings.zload = zmValidLoadout({ ...cur, [k]: v }, ITEMS);
    h.save();
    if (G.joined) net.send({ t: 'zload', zl: G.settings.zload });
    h.toast(`${what} for zombies${G.joined ? ' · from your next zombies game' : ''}`);
    h.redraw();
  };
  row('START PISTOL', Object.entries(ZM_PISTOLS).map(([id, p]) => {
    const w = WEAPONS[id];
    return h.loTile('lo-item', () => weaponIcon(id), w.name, p.ammo == null ? '∞' : `${p.ammo}`, cur.pistol === id, [`START PISTOL · ${p.ammo == null ? 'NEVER RUNS OUT' : p.ammo + ' ROUNDS'}`, p.tip], w.color || '#ffe14d', () => set('pistol', id, `${w.name} it is`));
  }));
  row(`ITEM (${K.label('item')})`, ITEM_ORDER.map((id) => {
    const it = ITEMS[id];
    return h.loTile('lo-item', () => itemPic(id, G.equipped[it.w]), it.name, `x${it.charges}`, cur.item === id, [`ITEM · ${it.charges} CHARGE${it.charges > 1 ? 'S' : ''} · ${it.recharge}s REFILL`, it.desc], it.color, () => set('item', id, `${it.name} packed`));
  }));
  row('PASSIVE · PICK 1', Object.entries(ZM_PASSIVES).map(([id, p]) => h.loTile('lo-item zl-perk', () => perkIcon(id), p.name, '', cur.perk === id, ['PASSIVE · ZOMBIES ONLY', p.desc], p.color, () => set('perk', id, `${p.name} on`))));
  return true;
}

// ------------------------------------------------------------ the passives' pictures: little 3D things, lit like the guns
const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.35, metalness: 0.1, ...o });
const chrome = () => mat(0xd8dce4, { metalness: 0.9, roughness: 0.2 });
const box = (g, w, h, d, m, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.rotation.set(rx, ry, rz); g.add(o); return o; };
const cyl = (g, r0, r1, h, m, x = 0, y = 0, z = 0, rx = 0, rz = 0, seg = 16) => { const o = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m); o.position.set(x, y, z); o.rotation.set(rx, 0, rz); g.add(o); return o; };
function texOf(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; }
const BUILD = {
  quickhands() { // a helping hand with a green plus over it
    const g = new THREE.Group(), skin = mat(0xffc89a);
    box(g, 0.5, 0.55, 0.16, skin, 0, -0.1, 0, 0, 0, -0.15);
    for (let i = 0; i < 4; i++) box(g, 0.1, 0.38, 0.12, skin, -0.18 + i * 0.12, 0.33 + (i === 1 || i === 2 ? 0.04 : 0), 0, 0, 0, -0.15 + (i - 1.5) * 0.06);
    box(g, 0.1, 0.32, 0.12, skin, 0.33, -0.02, 0.02, 0, 0, -0.9);
    const p = mat(0x39ff14, { emissive: 0x1a8a0a }); box(g, 0.34, 0.1, 0.1, p, 0.38, 0.62, 0.12); box(g, 0.1, 0.34, 0.1, p, 0.38, 0.62, 0.12);
    box(g, 0.5, 0.12, 0.18, mat(0x4fd8ff), 0, -0.42, 0, 0, 0, -0.15); // a cuff
    return g;
  },
  trustfund() { // a money bag on a stack of coins
    const g = new THREE.Group(), gold = mat(0xffd23a, { metalness: 0.8, roughness: 0.25 });
    for (let i = 0; i < 5; i++) cyl(g, 0.2, 0.2, 0.06, gold, 0.28 + (i % 2) * 0.02, -0.42 + i * 0.065, 0.1);
    const bag = new THREE.Mesh(new THREE.SphereGeometry(0.34, 14, 10), mat(0x9a7a4a)); bag.scale.set(1, 1.05, 0.9); bag.position.set(-0.1, -0.1, 0); g.add(bag);
    cyl(g, 0.1, 0.16, 0.16, mat(0x9a7a4a), -0.1, 0.28, 0);
    box(g, 0.3, 0.05, 0.05, mat(0xff4fd8), -0.1, 0.24, 0.12);
    const t = texOf(64, 64, (x) => { x.fillStyle = '#2a6a1a'; x.font = 'bold 54px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('$', 32, 34); });
    const s = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 0.3), new THREE.MeshBasicMaterial({ map: t, transparent: true })); s.position.set(-0.1, -0.1, 0.32); g.add(s);
    return g;
  },
  stubborn() { // a cracked red heart held together with a plaster
    const g = new THREE.Group(), red = mat(0xff3030, { roughness: 0.25 });
    const sh = new THREE.Shape(); sh.moveTo(0, -0.45); sh.bezierCurveTo(-0.6, 0, -0.45, 0.45, 0, 0.22); sh.bezierCurveTo(0.45, 0.45, 0.6, 0, 0, -0.45);
    const h = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.18, bevelEnabled: true, bevelSize: 0.05, bevelThickness: 0.05, bevelSegments: 2 }), red); h.position.z = -0.09; g.add(h);
    const tan = mat(0xf0d0a0);
    box(g, 0.5, 0.13, 0.04, tan, 0, 0.02, 0.17, 0, 0, 0.6); box(g, 0.5, 0.13, 0.04, tan, 0, 0.02, 0.18, 0, 0, -0.6);
    return g;
  },
  handyman() { // a claw hammer over a plank with a bent nail
    const g = new THREE.Group();
    box(g, 0.9, 0.18, 0.08, mat(0xa87a48), 0, -0.3, 0, 0, 0, 0.08);
    cyl(g, 0.012, 0.012, 0.2, chrome(), 0.2, -0.13, 0.02, 0, 0.5, 6);
    const hm = new THREE.Group(); hm.rotation.z = 0.7; g.add(hm);
    cyl(hm, 0.05, 0.06, 0.75, mat(0xff4fd8), 0, 0, 0, 0, 0, 10);
    box(hm, 0.36, 0.12, 0.12, chrome(), 0.04, 0.4, 0); cyl(hm, 0.07, 0.07, 0.12, chrome(), -0.16, 0.4, 0, 0, Math.PI / 2, 10);
    return g;
  },
  rabbitfoot() { // a pink lucky foot on a keyring
    const g = new THREE.Group(), fur = mat(0xff8ad8, { roughness: 0.9 });
    const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.42, 6, 12), fur); f.rotation.z = 0.35; f.position.set(0.05, -0.12, 0); g.add(f);
    for (let i = 0; i < 3; i++) { const t = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 6), fur); t.position.set(0.18 - i * 0.1 + 0.08, -0.43 + i * 0.03, 0.12); g.add(t); }
    cyl(g, 0.09, 0.09, 0.08, chrome(), -0.1, 0.22, 0, 0, 0.35, 10);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.025, 6, 20), chrome()); ring.position.set(-0.2, 0.42, 0); g.add(ring);
    return g;
  },
  thickskin() { // a big bottle of moisturiser
    const g = new THREE.Group();
    cyl(g, 0.24, 0.26, 0.7, mat(0xffb347, { roughness: 0.2 }), 0, -0.1, 0);
    cyl(g, 0.12, 0.14, 0.12, mat(0xffffff), 0, 0.31, 0);
    cyl(g, 0.03, 0.03, 0.14, mat(0xffffff), 0, 0.42, 0, 0, 0, 6);
    box(g, 0.24, 0.05, 0.06, mat(0xffffff), 0.08, 0.5, 0);
    const t = texOf(96, 96, (x) => { x.fillStyle = '#fff'; x.fillRect(0, 0, 96, 96); x.fillStyle = '#c04020'; x.font = 'bold 30px sans-serif'; x.textAlign = 'center'; x.fillText('THICC', 48, 44); x.font = 'bold 15px sans-serif'; x.fillText('SKIN', 48, 70); });
    const l = new THREE.Mesh(new THREE.PlaneGeometry(0.32, 0.32), new THREE.MeshBasicMaterial({ map: t })); l.position.set(0, -0.1, 0.262); g.add(l);
    return g;
  },
  coupons() { // a coupon with a cut line and a little pair of scissors
    const g = new THREE.Group();
    const t = texOf(160, 96, (x, w, h) => { x.fillStyle = '#4fd8ff'; x.fillRect(0, 0, w, h); x.setLineDash([8, 6]); x.strokeStyle = '#000'; x.lineWidth = 4; x.strokeRect(6, 6, w - 12, h - 12); x.fillStyle = '#000'; x.font = 'bold 50px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('-10%', w / 2, h / 2 + 2); });
    box(g, 1.0, 0.6, 0.03, [mat(0x4fd8ff), mat(0x4fd8ff), mat(0x4fd8ff), mat(0x4fd8ff), new THREE.MeshBasicMaterial({ map: t }), mat(0x4fd8ff)], 0, 0, 0, 0, 0, -0.12);
    const red = mat(0xff3030);
    for (const s of [-1, 1]) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.07, 0.025, 6, 14), red); r.position.set(0.42, -0.3 + s * 0.08, 0.06); g.add(r); box(g, 0.3, 0.03, 0.02, chrome(), 0.62, -0.3 - s * 0.03, 0.06, 0, 0, s * 0.25); }
    return g;
  },
  secondwind() { // a swirl of wind round a little lung
    const g = new THREE.Group(), wind = mat(0xbfefff, { emissive: 0x2a5a6a });
    for (let i = 0; i < 3; i++) { const t = new THREE.Mesh(new THREE.TorusGeometry(0.42 - i * 0.1, 0.035, 6, 24, Math.PI * 1.4), wind); t.rotation.set(1.2, 0, i * 1.9); t.position.y = -0.15 + i * 0.16; g.add(t); }
    for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.14, 10, 8), mat(0xff7a9a)); l.scale.set(0.8, 1.2, 0.8); l.position.set(s * 0.1, 0.05, 0); g.add(l); }
    return g;
  },
};
function perkIcon(id) {
  const b = BUILD[id];
  if (!b) return '';
  return objIcon('zlperk_' + id, () => { const g = b(); g.rotation.y = -0.35; g.rotation.x = 0.12; return g; });
}
