// Zombies on your screen: the Warranty Voider (hold F with a weapon out: the stamp comes down, it comes back stronger,
// maybe with a side effect) and the other cola machines. Prompts, the chips on the HUD that say what you're on, the
// stamp slamming, ZAPPY arcs between zombies. The server sells and decides (server/zmshop.js).
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx, makeBeam, setBeam } from './fx.js';
import { ME } from './player.js';
import { W } from './weapons.js';
import { M } from './models.js';
import { authored, whenLate, nodeIn, prefetch } from './glbkit.js';
import { WEAPONS } from '/shared/weapons.js';
import { ZM } from '/shared/zombies.js';
import { ZM_COLAS, ZM_UP, ZM_UPFX, zmUpPrice, zmShopTarget } from '/shared/zmshop.js';
import { BR, hookCharges, hookSpend } from '/shared/royale.js'; // the grapple's charges: Jank Royale's rule and its ring
import { K } from './keys.js';

const FONT = '"Comic Sans MS", "Comic Neue", cursive';
const S = { zm: null, group: null, colas: [], up: null, mine: [], ups: {}, jank: false, beams: [], hudK: '', el: null };
const R = (k) => (Math.random() - 0.5) * 2 * k;
const JANK = { name: 'JANK COLA', color: '#ff3030' };

function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.magFilter = THREE.NearestFilter;
  return { t, c };
}
const place = (root, at, n) => { root.position.set(at[0], at[1] || 0, at[2]); root.rotation.y = Math.atan2(n[0], n[2]); return root; }; // local +z = out of the wall

// ------------------------------------------------------------ the machines
// a cola machine: the Blender one (x_zmcola: cola_paint takes the flavour's colour, the name goes on its label panel)
// or a painted box if its file isn't there
function buildCola(c, def) {
  const root = place(new THREE.Group(), c.at, c.n), bl = authored('x_zmcola'), col = new THREE.Color(def.color);
  let label = { c: [0, 1.45, 0.41], w: 0.9, h: 0.5 };
  const lit = [];
  if (bl) {
    root.add(bl.obj);
    if (bl.meta && bl.meta.label) label = bl.meta.label;
    const paints = new Map();
    bl.obj.traverse((o) => {
      if (!o.isMesh) return;
      const one = (m) => {
        if (/^cola_paint/.test(m.name || '')) { if (!paints.has(m)) { const k = m.clone(); k.color.copy(col); if (k.emissive) k.emissive.copy(col).multiplyScalar(0.12); paints.set(m, k); } return paints.get(m); }
        if (/^zm_neon/.test(m.name || '')) { const k = m.clone(); k.userData.e0 = k.emissiveIntensity ?? 1; lit.push(k); return k; }
        return m;
      };
      o.material = Array.isArray(o.material) ? o.material.map(one) : one(o.material);
    });
  } else {
    const body = new THREE.Mesh(new THREE.BoxGeometry(1.16, 2.06, 0.76), M(col.getHex())); body.position.y = 1.03; root.add(body);
    const win = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.7, 0.04), M(0x15101c)); win.position.set(-0.1, 0.85, 0.375); root.add(win);
    const flap = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.16, 0.04), M(0x222222)); flap.position.set(-0.1, 0.25, 0.375); root.add(flap);
  }
  const tex = canvasTex(192, Math.max(32, Math.round(192 * label.h / label.w)), (x, w, h) => {
    x.fillStyle = '#f4f0e4'; x.fillRect(0, 0, w, h); x.fillStyle = def.color; x.fillRect(0, 0, w, 8); x.fillRect(0, h - 8, w, 8);
    const words = def.name.split(' '), fs = Math.min(h / (words.length + 0.6), (w / Math.max(...words.map((s) => s.length))) * 1.5);
    x.font = `bold ${fs}px ${FONT}`; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.save(); x.translate(w / 2, h / 2); x.rotate(-0.06);
    words.forEach((s, i) => { const y = (i - (words.length - 1) / 2) * fs * 0.95; x.fillStyle = '#120818'; x.fillText(s, 3, y + 3); x.fillStyle = def.color; x.fillText(s, 0, y); });
    x.restore();
  }).t;
  const mat = new THREE.MeshBasicMaterial({ map: tex, color: 0x555555, fog: false });
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(label.w, label.h), mat); sign.position.set(label.c[0], label.c[1], label.c[2] + 0.004); root.add(sign);
  return { root, mat, lit, glb: !!bl };
}
// the voider: the Blender one (x_zmvoider: `stamp` comes down, zm_neon lights with the power, the screen is ours) or a
// bench with a red block over it
function buildUp(u) {
  const root = place(new THREE.Group(), u.at, u.n), bl = authored('x_zmvoider');
  let screen = { c: [0.5, 1.55, 0.21], w: 0.5, h: 0.32 }, drop = 0.5, tray = [0, 1.02, 0.15], stamp = null;
  const lit = [];
  if (bl) {
    root.add(bl.obj);
    const mt = bl.meta || {};
    if (mt.screen) screen = mt.screen;
    if (mt.stamp && Number.isFinite(mt.stamp.drop)) drop = mt.stamp.drop;
    if (mt.tray && mt.tray.c) tray = mt.tray.c;
    stamp = nodeIn(bl.obj, 'stamp');
    bl.obj.traverse((o) => {
      if (!o.isMesh) return;
      const one = (m) => { if (!/^zm_neon|^zm_lamp/.test(m.name || '')) return m; const k = m.clone(); k.userData.e0 = k.emissiveIntensity ?? 1; lit.push(k); return k; };
      o.material = Array.isArray(o.material) ? o.material.map(one) : one(o.material);
    });
  } else {
    const bench = new THREE.Mesh(new THREE.BoxGeometry(1.76, 1.0, 1.0), M(0x3a3f4a)); bench.position.set(0, 0.5, 0.08); root.add(bench);
    const back = new THREE.Mesh(new THREE.BoxGeometry(1.76, 1.4, 0.6), M(0x2a2e38)); back.position.set(0, 1.7, -0.12); root.add(back);
    const rim = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.04, 0.5), M(0xffe14d)); rim.position.set(-0.2, 1.02, 0.25); root.add(rim);
    stamp = new THREE.Group(); stamp.position.set(-0.2, 1.75, 0.25);
    const head = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.22, 0.34), M(0xd01818)); stamp.add(head);
    const ram = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.7, 8), M(0xc8ccd4)); ram.position.y = 0.45; stamp.add(ram);
    root.add(stamp); drop = 0.55; tray = [-0.2, 1.05, 0.25];
  }
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = Math.max(32, Math.round(256 * screen.h / screen.w));
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(screen.w, screen.h), new THREE.MeshBasicMaterial({ map: tex, fog: false }));
  scr.position.set(screen.c[0], screen.c[1], screen.c[2] + 0.004); root.add(scr);
  const light = new THREE.PointLight(0xff4fd8, 0, 6, 1.6); light.position.set(0, 1.7, 0.9); root.add(light);
  return { root, cv, tex, stamp, y0: stamp ? stamp.position.y : 0, drop, tray, lit, light, slam: -1e9, drawK: '', glb: !!bl };
}
function drawScreen(u, pw, now) {
  const w = WEAPONS[W.cur], cur = S.ups[W.cur] || { t: 0, fx: '' }, price = zmUpPrice(cur.t);
  const slamming = now - u.slam < 1400;
  const key = !pw ? 'off' + (((now / 400) | 0) % 2) : slamming ? 'slam' + (((now / 120) | 0) % 2) : `${W.cur}|${cur.t}|${cur.fx}`;
  if (key === u.drawK) return;
  u.drawK = key;
  const c = u.cv, x = c.getContext('2d'), cw = c.width, ch = c.height;
  x.fillStyle = '#07030c'; x.fillRect(0, 0, cw, ch);
  x.textAlign = 'center'; x.textBaseline = 'middle';
  const line = (s, y, px, col) => { x.font = `bold ${px}px ${FONT}`; x.fillStyle = col; x.fillText(s, cw / 2, y, cw - 12); };
  if (!pw) line('NO POWER', ch / 2, ch * 0.3, key.endsWith('1') ? '#ff3030' : '#5a1010');
  else if (slamming) line('VOID', ch / 2, ch * 0.5, key.endsWith('1') ? '#ff4fd8' : '#ffe14d');
  else {
    line(w ? w.name.toUpperCase() : 'NO WEAPON', ch * 0.22, ch * 0.2, '#4fd8ff');
    line(cur.t ? ZM_UP.tier[cur.t] + (cur.fx && ZM_UPFX[cur.fx] ? ' · ' + ZM_UPFX[cur.fx].name : '') : 'WARRANTY: INTACT', ch * 0.5, ch * 0.17, '#f4f0e4');
    line(price == null ? 'FULLY VOID' : `VOID IT · ${price}`, ch * 0.8, ch * 0.2, price == null ? '#7dff4f' : '#ffe14d');
  }
  u.tex.needsUpdate = true;
}

export function zsSetup(zm, group) { // the map was built (zombies.js zmSetup)
  S.zm = zm; S.group = group; S.colas = []; S.up = null; S.mine = []; S.ups = {}; S.jank = false;
  clearBeams();
  if (!zm) { hudOff(); return; }
  prefetch(['x_zmcola', 'x_zmvoider'], 3);
  const build = () => {
    for (const c of S.colas) group.remove(c.root);
    if (S.up) group.remove(S.up.root);
    S.colas = [];
    if (zm.cola) S.colas.push(buildCola(zm.cola, JANK)); // (zombies.js still draws Jank Cola's old flat sign too: this stands in front of it)
    for (const c of zm.colas || []) if (ZM_COLAS[c.id]) S.colas.push(buildCola(c, ZM_COLAS[c.id]));
    for (const c of S.colas) group.add(c.root);
    S.up = zm.up ? buildUp(zm.up) : null;
    if (S.up) group.add(S.up.root);
  };
  const re = () => { if (S.zm === zm && S.group === group) build(); };
  build();
  if (S.colas.length && !S.colas[0].glb) whenLate('x_zmcola', re);
  if (S.up && !S.up.glb) whenLate('x_zmvoider', re);
}

// ------------------------------------------------------------ F: what you're looking at, and what it says
export function zsTarget(e, d) { return S.zm ? zmShopTarget(S.zm, e, d) : null; }
export function zsHold(t) { return t.kind === 'up' ? ZM_UP.hold : null; } // seconds of F
export function zsPrompt(t, info, credits, price, UK) {
  const can = (p) => credits >= price(p), n = S.mine.length + (S.jank ? 1 : 0);
  if (t.kind === 'cola2') {
    const d = ZM_COLAS[t.id];
    if (!d) return null;
    if (!info.pw) return [`${d.name} · no power (the switch is in the loading dock)`, false];
    if (S.mine.includes(t.id)) return [`${d.name} · you already had one`, false];
    if (n >= ZM.colaMax) return [`${d.name} · ${ZM.colaMax} colas is the limit`, false];
    return [`[${UK}] ${d.name} · ${price(d.price)} · ${d.desc}`, can(d.price)];
  }
  if (t.kind === 'up') {
    if (!info.pw) return [`${ZM_UP.name} · no power (the switch is in the loading dock)`, false];
    const w = WEAPONS[W.cur], cur = S.ups[W.cur] || { t: 0 }, p = zmUpPrice(cur.t);
    if (!w) return [`${ZM_UP.name} · hold a weapon`, false];
    if (p == null) return [`${w.name.toUpperCase()} · it can't get any more void`, false];
    return [`[${UK}] HOLD TO VOID YOUR ${w.name.toUpperCase()} · ${price(p)} · ${cur.t ? 'hits harder, new side effect' : 'hits harder, holds more'}`, can(p)];
  }
  return null;
}

// ------------------------------------------------------------ the HUD: a chip for every cola you're on, and what the gun in your hands has had done to it
function hudEl() {
  if (S.el) return S.el;
  const el = S.el = document.createElement('div');
  el.id = 'zsHud';
  el.style.cssText = `position:fixed;right:18px;bottom:150px;display:flex;flex-direction:column;align-items:flex-end;gap:6px;pointer-events:none;z-index:6;font-family:${FONT};`;
  document.body.appendChild(el);
  return el;
}
function hudOff() { if (S.el) { S.el.innerHTML = ''; S.hudK = ''; } }
const chip = (text, color, sub) => `<div style="background:rgba(18,8,24,0.92);border:3px solid ${color};box-shadow:4px 4px 0 #4fd8ff;color:${color};font-weight:bold;font-size:13px;padding:2px 8px;transform:rotate(-1deg)">${text}${sub ? `<span style="color:#f4f0e4;font-size:11px"> · ${sub}</span>` : ''}</div>`;
function drawHud() {
  const u = S.ups[W.cur], rows = [];
  if (u && u.t) { const f = ZM_UPFX[u.fx]; rows.push(chip(ZM_UP.tier[u.t], '#ff4fd8', f ? f.name : '')); }
  if (S.jank) rows.push(chip(JANK.name, JANK.color));
  for (const id of S.mine) if (ZM_COLAS[id]) rows.push(chip(ZM_COLAS[id].name, ZM_COLAS[id].color));
  const html = rows.join('');
  if (html !== S.hudK) { S.hudK = html; hudEl().innerHTML = html; }
}

// ------------------------------------------------------------ grapple charges (BR.hook, as in Jank Royale): the server counts, this shows + predicts
const HK = { h: null, had: false, n: BR.hook.charges, noT: 0, el: null };
const st = () => performance.now() + (G.offset || 0); // the server's clock
const RING = 2 * Math.PI * 19;
function hookEl() {
  if (HK.el) return HK.el;
  const css = document.createElement('style'); // (the same ring as royale.js's #brHook)
  css.textContent = `#zmHook { position: absolute; left: calc(50% + 34px); top: calc(50% + 26px); width: 56px; height: 56px; pointer-events: none; font: bold 11px var(--font); color: #fff; text-shadow: 1px 1px 0 #000; z-index: 6; }
#zmHook svg { position: absolute; inset: 0; transform: rotate(-90deg); }
#zmHook .tr { fill: none; stroke: rgba(0,0,0,0.55); stroke-width: 6; } #zmHook .fl { fill: none; stroke: #4fd8ff; stroke-width: 6; stroke-linecap: butt; }
#zmHook.full .fl { stroke: #7dff4f; } #zmHook.none .fl { stroke: #ff3030; }
#zmHook span { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 17px; letter-spacing: -1px; }
#zmHook small { position: absolute; left: 50%; top: 54px; transform: translateX(-50%); white-space: nowrap; font-size: 10px; letter-spacing: 1px; color: #fff; }
#zmHook.no { animation: zmHookNo 0.35s; } @keyframes zmHookNo { 0%, 100% { transform: none; } 25% { transform: translateX(-5px) rotate(-6deg); } 75% { transform: translateX(5px) rotate(6deg); } }
#zmHook.hidden { display: none; }`;
  document.head.appendChild(css);
  const e = document.createElement('div'); e.id = 'zmHook';
  e.innerHTML = '<svg viewBox="0 0 46 46"><circle class="tr" cx="23" cy="23" r="19"/><circle class="fl" cx="23" cy="23" r="19"/></svg><span></span><small></small>';
  (document.getElementById('hud') || document.body).appendChild(e);
  return (HK.el = e);
}
function hookDenied() {
  ME.hook = null; // (the server cut it, or it never fired)
  const now = performance.now();
  if (now - HK.noT < 300) return;
  HK.noT = now;
  const c = hookCharges(HK.h, st());
  sfx.hookNo(); hud.msg(`GRAPPLE RECHARGING · ${Math.max(1, Math.ceil((1 - c.k) * BR.hook.cd))}s`, 0.8, 'brag');
  const e = hookEl(); e.classList.remove('no'); void e.offsetWidth; e.classList.add('no');
}
function hookGate() { // player.js tryHook asks first: true = no charge, no rope
  if (!S.zm || !ME.alive || hookCharges(HK.h, st()).n >= 1) return false;
  hookDenied();
  return true;
}
function hookFrame() {
  if (G.hookGate !== hookGate) G.hookGate = hookGate;
  const roped = !!ME.hook;
  if (roped && !HK.had) HK.h = hookSpend(HK.h, st()) || HK.h; // a new rope: spend one now (the server's count follows)
  HK.had = roped;
  const H = BR.hook, c = hookCharges(HK.h, st());
  if (c.n > HK.n && ME.alive) sfx.hookReady();
  HK.n = c.n;
  const e = hookEl(), full = c.n >= H.charges;
  e.className = (full ? 'full' : c.n === 0 ? 'none' : '') + (ME.alive ? '' : ' hidden');
  e.querySelector('.fl').style.strokeDasharray = `${(full ? 1 : c.k) * RING} ${RING}`;
  e.querySelector('span').textContent = '●'.repeat(c.n) + '○'.repeat(H.charges - c.n);
  e.querySelector('small').textContent = full ? `${K.label('grapple')} GRAPPLE` : `${K.label('grapple')} ${Math.ceil((1 - c.k) * H.cd)}s`;
}
function hookOff() { if (G.hookGate === hookGate) G.hookGate = null; HK.h = null; HK.had = false; HK.n = BR.hook.charges; if (HK.el) HK.el.className = 'hidden'; }
net.on('zhook', (m) => { if (!m || typeof m !== 'object') return; const h = m.h; HK.h = h && Number.isFinite(h.n) && Number.isFinite(h.t0) ? { n: h.n, t0: h.t0 } : null; if (m.no) hookDenied(); });

// ------------------------------------------------------------ every frame (zombies.js updateZombies)
export function zsTick(info, dt, now) {
  if (!S.zm) return;
  hookFrame();
  const pw = !!info.pw;
  for (const c of S.colas) { c.mat.color.setHex(pw ? 0xffffff : 0x555555); for (const m of c.lit) m.emissiveIntensity = pw ? m.userData.e0 : 0; }
  const u = S.up;
  if (u) {
    const k = (now - u.slam) / 1000; // the stamp: down hard, a beat, back up
    const d = k < 0 || k > 1.3 ? 0 : k < 0.12 ? k / 0.12 : k < 0.5 ? 1 : 1 - (k - 0.5) / 0.8;
    if (u.stamp) u.stamp.position.y = u.y0 - u.drop * Math.max(0, d);
    for (const m of u.lit) m.emissiveIntensity = pw ? m.userData.e0 * (k >= 0 && k < 1.3 ? 1.6 + Math.sin(now * 0.05) * 0.6 : 1) : 0;
    u.light.intensity = pw ? (k >= 0 && k < 0.6 ? 5 : 1.2) : 0;
    drawScreen(u, pw, now);
  }
  if (ME.alive && S.mine.includes('legday')) ME.speedMul = (ME.speedMul || 1) * ZM_COLAS.legday.speed;
  for (let i = S.beams.length - 1; i >= 0; i--) { // ZAPPY arcs fade out
    const b = S.beams[i]; b.t -= dt;
    b.m.material.opacity = Math.max(0, b.t / 0.22);
    if (b.t <= 0) { G.scene.remove(b.m); b.m.material.dispose(); S.beams.splice(i, 1); } // (the beam geometry is shared)
  }
  drawHud();
}
function clearBeams() { for (const b of S.beams) { G.scene.remove(b.m); b.m.material.dispose(); } S.beams.length = 0; }
export function zsOff() { clearBeams(); hudOff(); hookOff(); S.mine = []; S.ups = {}; S.jank = false; } // the mode ended

// ------------------------------------------------------------ the server's news
const v3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);
net.on('zshop', (m) => {
  S.jank = !!m.jank;
  S.mine = Array.isArray(m.colas) ? m.colas.filter((c) => typeof c === 'string' && Object.hasOwn(ZM_COLAS, c)) : [];
  S.ups = {};
  if (m.up && typeof m.up === 'object') for (const [w, u] of Object.entries(m.up)) if (WEAPONS[w] && u && Number.isFinite(u.t)) S.ups[w] = { t: Math.max(0, Math.min(3, u.t | 0)), fx: typeof u.fx === 'string' ? u.fx : '' };
});
net.on('zup', (m) => {
  if (!m || typeof m !== 'object') return;
  if (m.k === 'done') {
    const u = S.up, r = G.remotes.get(m.id), at = u ? u.root.localToWorld(new THREE.Vector3(u.tray[0], u.tray[1], u.tray[2])).toArray() : r ? r.pos : ME.pos;
    if (u) u.slam = performance.now();
    sfx.zmVoid(at);
    setTimeout(() => { // the stamp lands
      const P = fx.parts().fire;
      for (let i = 0; i < 26; i++) P.spawn(at[0], at[1] + 0.05, at[2], R(5), 1 + Math.random() * 5, R(5), 0.3 + Math.random() * 0.3, 0.1, 0.02, Math.random() < 0.5 ? 0xff4fd8 : 0xffe14d, 0xff3030, 1, 14, 1);
      if (G.settings.shake !== false && Math.hypot(at[0] - ME.pos[0], at[2] - ME.pos[2]) < 8) G.shake = Math.max(G.shake, 0.5);
    }, 120);
    if (m.id === G.myId) {
      const f = ZM_UPFX[m.fx];
      hud.msg(f ? `WARRANTY VOIDED · ${f.name}` : 'WARRANTY VOIDED', 1.8, 'brag');
    }
  } else if (m.k === 'zap' && v3(m.a) && Array.isArray(m.to)) {
    let from = m.a;
    for (const to of m.to.slice(0, 6)) {
      if (!v3(to)) continue;
      const mid = [(from[0] + to[0]) / 2 + R(0.4), (from[1] + to[1]) / 2 + R(0.4), (from[2] + to[2]) / 2 + R(0.4)];
      for (const [a, b] of [[from, mid], [mid, to]]) { const bm = makeBeam(0x9fe8ff, 1); bm.material.transparent = true; bm.material.fog = false; setBeam(bm, a, b, 0.05); G.scene.add(bm); S.beams.push({ m: bm, t: 0.22 }); }
      from = to;
    }
    sfx.zmZap(m.a);
  } else if (m.k === 'frost') { const r = G.remotes.get(m.id); if (r && Number.isFinite(m.ms)) r.frozenUntil = performance.now() + Math.min(3000, m.ms); }
});
