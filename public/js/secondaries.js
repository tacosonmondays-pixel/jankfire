// The new secondaries + the speed trap, client half: Water Pistol streams + soaked people, Taser darts + lightning chains,
// TV Remote pause / rewind, the radar gun (hold G), SLOW DOWN tickets and the jail cage. The server decides every effect
// (server/secondaries.js); this draws them, plays them, and holds you still when you've been stunned, paused or caged.
// Everything others see on someone (soaked, stunned, paused, caged, ticketed, holding the radar) comes from the server's
// FLAGS bits in snapshots, so killcams and replays (ghosts get the same snapshots) draw it all for free.
import * as THREE from 'three';
import { WEAPONS, FLAGS, SPEED, ITEMS } from '/shared/weapons.js';
import { BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { G } from './ctx.js';
import { ME, eye, look, releaseHook } from './player.js';
import { W, VMX, isFriend } from './weapons.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { fx, makeBeam, setBeam } from './fx.js';
import { sfx } from './audio.js';
import { recordEv, RP_HOOKS, RP } from './replay.js';
import { buildWeapon, M, freeTree } from './models.js';

const WP = WEAPONS.water, TZ = WEAPONS.taser, RM = WEAPONS.remote;
const r2 = (x) => Math.round(x * 100) / 100;
const ok3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);
const R = (k = 1) => (Math.random() * 2 - 1) * k;
const nowMs = () => performance.now();
// you: what the server put on you (times in performance.now ms)
const S = { soak: 0, stun: 0, pause: 0, pauseAt: null, pauseVel: null, jail: 0, jailAt: null, ticket: null, radar: false, radarT: 0, radarTo: 0, radarV: null, rmCd: { pause: 0, rewind: 0 }, vhs: 0, vhsKind: '', detected: 0 };
const nameOf = (id) => (id === G.myId ? G.myName : (G.names && G.names.get(id) && G.names.get(id).name) || (G.remotes.get(id) || {}).name || '???');
const colorOf = (id) => (id === G.myId ? G.myColor : (G.names && G.names.get(id) && G.names.get(id).color) || (G.remotes.get(id) || {}).color || '#fff');

// ---------------------------------------------------------------- the HUD bits (comic zine look, like the rest)
let hudEl = null;
const css = `
#secHud { position: absolute; inset: 0; pointer-events: none; }
#secHud .layer { position: absolute; inset: 0; opacity: 0; transition: opacity 0.15s; }
#secWet { box-shadow: inset 0 0 140px 30px rgba(60, 170, 255, 0.55); background:
  radial-gradient(circle at 12% 20%, rgba(170,225,255,0.35) 0 14px, transparent 16px), radial-gradient(circle at 82% 14%, rgba(170,225,255,0.3) 0 10px, transparent 12px),
  radial-gradient(circle at 70% 78%, rgba(170,225,255,0.3) 0 18px, transparent 20px), radial-gradient(circle at 22% 70%, rgba(170,225,255,0.28) 0 9px, transparent 11px),
  radial-gradient(circle at 48% 8%, rgba(170,225,255,0.25) 0 7px, transparent 9px), radial-gradient(circle at 90% 55%, rgba(170,225,255,0.3) 0 12px, transparent 14px); }
#secStatic { background: repeating-linear-gradient(0deg, rgba(232,255,58,0.10) 0 2px, transparent 2px 5px); box-shadow: inset 0 0 120px 20px rgba(232,255,58,0.45); }
#secVhs { background: repeating-linear-gradient(0deg, rgba(255,255,255,0.07) 0 1px, transparent 1px 4px); box-shadow: inset 0 0 200px 60px rgba(20,10,60,0.55); }
#secVhsTxt { position: absolute; left: 6%; top: 9%; font: bold 46px monospace; color: #fff; text-shadow: 3px 3px 0 #2e7bff, -2px 0 0 #ff4fd8; letter-spacing: 3px; }
#secBars { background: repeating-linear-gradient(90deg, transparent 0 9%, rgba(20,20,26,0.75) 9% 11.5%); }
#secBanner { position: absolute; left: 50%; top: 22%; transform: translate(-50%, -50%) rotate(-2deg); padding: 8px 22px 10px; background: rgba(18,8,24,0.92);
  border: 4px solid #ff4fd8; box-shadow: 8px 8px 0 #4fd8ff; text-align: center; opacity: 0; white-space: nowrap; font-family: var(--font); }
#secBanner b { display: block; font-size: 52px; line-height: 1; color: #ffe14d; text-shadow: 3px 3px 0 #000; letter-spacing: 1px; }
#secBanner span { display: block; font-size: 20px; color: #fff; margin-top: 4px; }
#secBanner.cop { border-color: #2e7bff; box-shadow: 8px 8px 0 #ff3030; }
#secBanner.cop b { color: #fff; }
#secBanner.jail b { color: #ff3030; }
#secBanner.ok b { color: #39ff14; }
#secRadar { position: absolute; left: 50%; top: 50%; width: 120px; height: 120px; transform: translate(-50%, -50%); border: 3px dashed #2e7bff; opacity: 0; }
#secRadar i { position: absolute; left: 50%; top: 100%; transform: translate(-50%, 8px) rotate(-2deg); padding: 2px 10px; background: #111; border: 3px solid #000;
  box-shadow: 4px 4px 0 #2e7bff; font: bold 22px monospace; color: #ff3030; font-style: normal; white-space: nowrap; }
#secTip { position: absolute; left: 50%; top: 58%; transform: translateX(-50%); font-size: 15px; color: #fff; opacity: 0.85; white-space: nowrap; }
#secDetect { position: absolute; right: 18px; top: 38%; padding: 4px 10px; background: #ff3030; color: #fff; border: 3px solid #000; box-shadow: 4px 4px 0 #ffe14d;
  font-size: 18px; transform: rotate(3deg); opacity: 0; }
`;
function initHud() {
  if (hudEl || !document.getElementById('hud')) return;
  const st = document.createElement('style'); st.textContent = css; document.head.append(st);
  hudEl = document.createElement('div'); hudEl.id = 'secHud';
  hudEl.innerHTML = '<div id="secWet" class="layer"></div><div id="secStatic" class="layer"></div><div id="secBars" class="layer"></div><div id="secVhs" class="layer"><div id="secVhsTxt"></div></div>' +
    '<div id="secRadar"><i></i></div><div id="secTip"></div><div id="secDetect">RADAR DETECTED</div><div id="secBanner"><b></b><span></span></div>';
  document.getElementById('hud').append(hudEl);
}
const $ = (id) => document.getElementById(id);
function banner(big, small, cls = '') {
  const b = $('secBanner'); if (!b) return;
  if (!big) { b.style.opacity = 0; return; }
  b.className = cls; b.firstChild.textContent = big; b.lastChild.textContent = small || ''; b.style.opacity = 1;
}
let bannerUntil = 0, bannerLock = '';
function flashBanner(big, small, cls, ms) { bannerUntil = nowMs() + ms; bannerLock = big; banner(big, small, cls); }

// ---------------------------------------------------------------- labels over heads (canvas sprites, chunky)
function label(w = 256, h = 80) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const tex = new THREE.CanvasTexture(cv); tex.magFilter = THREE.NearestFilter; tex.minFilter = THREE.LinearFilter;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false, fog: false, sizeAttenuation: false }));
  sp.renderOrder = 999; sp.scale.set(0.1 * (w / h), 0.1, 1);
  let key = '';
  sp.userData.set = (text, fg, bg, border = '#000', sub = '') => {
    const k = text + fg + bg + border + sub;
    if (k === key) return; key = k;
    const x = cv.getContext('2d');
    x.clearRect(0, 0, w, h);
    x.fillStyle = border; x.fillRect(10, 10, w - 14, h - 14); // hard offset shadow
    x.fillStyle = bg; x.fillRect(2, 2, w - 14, h - 14);
    x.lineWidth = 5; x.strokeStyle = '#000'; x.strokeRect(2, 2, w - 14, h - 14);
    x.fillStyle = fg; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.font = `bold ${sub ? 30 : 38}px "Comic Neue", "Comic Sans MS", sans-serif`;
    x.fillText(text, (w - 12) / 2, sub ? h * 0.36 : (h - 12) / 2 + 2);
    if (sub) { x.font = 'bold 20px "Comic Neue", sans-serif'; x.fillText(sub, (w - 12) / 2, h * 0.7); }
    tex.needsUpdate = true;
  };
  return sp;
}

// ---------------------------------------------------------------- the cage
// a chunky steel cell: base + roof frames, bars all round, corner posts, a padlock on the front and a JAIL plate on top
let cageGeo = null;
function cagePlate() {
  const cv = document.createElement('canvas'); cv.width = 128; cv.height = 40;
  const x = cv.getContext('2d');
  x.fillStyle = '#f2f2f2'; x.fillRect(0, 0, 128, 40); x.fillStyle = '#d01c1c'; x.fillRect(0, 0, 128, 7); x.fillRect(0, 33, 128, 7);
  x.fillStyle = '#111'; x.font = 'bold 26px "Comic Neue", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('JAIL', 64, 21);
  const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter;
  return new THREE.MeshBasicMaterial({ map: t });
}
function buildCage() {
  const g = new THREE.Group(), S2 = 0.78, Hh = 2.55, IRON = 0x3c3f48, DARK = 0x24262c, YEL = 0xffd21a;
  const add = (geo, c, x, y, z) => { const m = new THREE.Mesh(geo, M(c)); m.position.set(x, y, z); g.add(m); return m; };
  cageGeo ||= { bar: new THREE.CylinderGeometry(0.03, 0.03, Hh - 0.16, 6), post: new THREE.BoxGeometry(0.11, Hh, 0.11), rail: new THREE.BoxGeometry(S2 * 2 + 0.1, 0.09, 0.1), mid: new THREE.BoxGeometry(S2 * 2, 0.05, 0.06) };
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) add(cageGeo.post, DARK, sx * S2, Hh / 2, sz * S2);
  for (const y of [0.05, Hh - 0.05]) for (let s = 0; s < 4; s++) { const r = add(cageGeo.rail, s % 2 ? IRON : DARK, 0, y, 0); r.rotation.y = (s * Math.PI) / 2; r.position.set(s === 0 ? 0 : s === 2 ? 0 : (s === 1 ? 1 : -1) * S2, y, s === 0 ? S2 : s === 2 ? -S2 : 0); }
  for (let s = 0; s < 4; s++) { const r = add(cageGeo.mid, IRON, 0, Hh * 0.55, 0); r.rotation.y = (s * Math.PI) / 2; r.position.set(s === 1 ? S2 : s === 3 ? -S2 : 0, Hh * 0.55, s === 0 ? S2 : s === 2 ? -S2 : 0); }
  for (let s = 0; s < 4; s++) for (let i = 1; i < 6; i++) { // bars
    const k = -S2 + (i / 6) * S2 * 2, b = add(cageGeo.bar, IRON, 0, Hh / 2, 0);
    if (s === 0) b.position.set(k, Hh / 2, S2); else if (s === 2) b.position.set(k, Hh / 2, -S2); else b.position.set(s === 1 ? S2 : -S2, Hh / 2, k);
    b.userData.bar = true;
  }
  add(new THREE.BoxGeometry(S2 * 2 + 0.12, 0.06, S2 * 2 + 0.12), DARK, 0, Hh + 0.02, 0); // roof
  add(new THREE.BoxGeometry(S2 * 2 + 0.16, 0.08, S2 * 2 + 0.16), DARK, 0, 0.02, 0); // floor plate
  // padlock on the front, hazard stripe on the base
  const lock = add(new THREE.BoxGeometry(0.16, 0.14, 0.07), YEL, 0.2, 1.1, -S2 - 0.06); lock.userData.lock = true;
  const sh = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.015, 4, 8, Math.PI), M(0xc8c8d0)); sh.position.set(0.2, 1.17, -S2 - 0.06); g.add(sh);
  const plate = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.28), cagePlate()); plate.position.set(0, Hh + 0.2, -S2 - 0.02); plate.rotation.y = Math.PI; g.add(plate);
  const plate2 = plate.clone(); plate2.position.z = S2 + 0.02; plate2.rotation.y = 0; g.add(plate2);
  for (const z of [-1, 1]) { const st = add(new THREE.BoxGeometry(0.06, 0.24, 0.06), DARK, z * 0.3, Hh + 0.1, -S2); st.userData.s = 1; }
  g.traverse((o) => { if (o.isMesh) o.frustumCulled = false; });
  return g;
}
// cages by who's in them: { g, at, t0 (slam start), until, out: release anim start, brk: broke out }
const cages = new Map();
function cageOn(key, at, slam = true) {
  let c = cages.get(key);
  if (!c) { c = { g: buildCage(), at: at.slice(), t0: slam ? nowMs() : nowMs() - 1000, out: 0, brk: false, landed: !slam }; G.scene.add(c.g); cages.set(key, c); }
  else { c.at = at.slice(); c.out = 0; }
  return c;
}
function cageOff(key, brk) { const c = cages.get(key); if (c && !c.out) { c.out = nowMs(); c.brk = !!brk; (brk ? sfx.cageBreak : sfx.cageUp)(c.at); if (brk) fx.sparks([c.at[0], c.at[1] + 1.2, c.at[2]], [0, 1, 0], 40, true); } }
function stepCages(now) {
  for (const [key, c] of cages) {
    const g = c.g, t = (now - c.t0) / 1000;
    // slam: drops 7 m in ~0.22 s, a little bounce, then sits
    let y = t < 0.22 ? 7 * (1 - (t / 0.22) ** 2) : t < 0.36 ? Math.sin(((t - 0.22) / 0.14) * Math.PI) * 0.18 : 0;
    if (!c.landed && t >= 0.22) {
      c.landed = true; sfx.cageSlam(c.at); fx.dust(c.at, 18); fx.ring(c.at, 3, 0xffffff, 0.35);
      const d = Math.hypot(c.at[0] - ME.pos[0], c.at[2] - ME.pos[2]); G.shake = Math.max(G.shake || 0, Math.max(0, 0.8 - d / 25));
    }
    let gone = false;
    if (c.out) {
      const u = (now - c.out) / 1000;
      if (c.brk) { // the rig rips it open: bars fly out and the frame tumbles
        g.children.forEach((o, i) => { if (o.userData.bar) { o.position.x += Math.sign(o.position.x || R()) * u * 0.6; o.position.z += Math.sign(o.position.z || R()) * u * 0.6; o.rotation.x += 0.2; o.rotation.z += 0.13 * (i % 3 - 1); } });
        y -= u * u * 6; gone = u > 0.8;
      } else { y += u * u * 30; gone = u > 0.6; } // hauled back up into the sky
    }
    g.position.set(c.at[0], c.at[1] + y, c.at[2]);
    g.visible = !RP.active || key !== 'me';
    if (gone) { G.scene.remove(g); freeTree(g); cages.delete(key); }
  }
}

// ---------------------------------------------------------------- lightning, wires, water streams
const bolts = []; // { segs: [mesh], a, b, life, ml, next, th, col }
function bolt(a, b, col = 0xe8ff3a, life = 0.35, th = 0.05) {
  const segs = [];
  for (let i = 0; i < 7; i++) { const m = makeBeam(i % 2 ? 0xffffff : col, 0.95); m.material.blending = THREE.AdditiveBlending; m.material.depthWrite = false; G.scene.add(m); segs.push(m); }
  const o = { segs, a: a.slice(), b: b.slice(), life, ml: life, next: 0, th, col };
  bolts.push(o); jag(o);
  return o;
}
function jag(o) {
  const n = o.segs.length, a = o.a, b = o.b, len = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]), k0 = Math.min(0.3, len * 0.05);
  let prev = a;
  for (let i = 0; i < n; i++) {
    const f = (i + 1) / n, end = i === n - 1, k = k0 * Math.sin(f * Math.PI) * (0.4 + f * 0.6); // tight at your end, wild near them
    const p = end ? b : [a[0] + (b[0] - a[0]) * f + R(k), a[1] + (b[1] - a[1]) * f + R(k), a[2] + (b[2] - a[2]) * f + R(k)];
    setBeam(o.segs[i], prev, p, o.th * (0.6 + Math.random() * 0.8));
    prev = p;
  }
}
const wires = []; // the taser's two darts on their wires: { m: [mesh, mesh], a(), b, life }
function darts(from, to) {
  const m = [0, 1, 2, 3].map(() => { const b = makeBeam(0x202024, 1); G.scene.add(b); return b; }); // near + far half of each wire
  const tip = [0, 1].map(() => { const t = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.05, 0.12), M(0xe8ff3a, true)); G.scene.add(t); return t; });
  wires.push({ m, tip, from, to: to.slice(), life: 0.75, t: 0 });
}
const streams = []; // water: a sagging arc of beams + a splash at the end
function waterArc(a, b) {
  const n = 6, segs = [], len = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]), sag = Math.min(0.9, len * 0.035);
  let prev = a;
  for (let i = 1; i <= n; i++) {
    const f = i / n, p = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f - Math.sin(f * Math.PI) * sag * (f < 1 ? 1 : 0), a[2] + (b[2] - a[2]) * f];
    const m = makeBeam(i % 2 ? 0x2fa8ff : 0x9fe0ff, 0.92); m.material.depthWrite = false;
    setBeam(m, prev, p, 0.05 + f * 0.05); G.scene.add(m); segs.push(m);
    if (i > 1 && Math.random() < 0.5) fx.spray(p, 1, [0x5cc8ff, 0xbfeaff], 0.6, 0.35, 0.06, 14, 0.5); // drops falling off the stream
    prev = p;
  }
  streams.push({ segs, life: 0.13, ml: 0.13 });
  fx.spray(b, 7, [0x3fb8ff, 0xbfeaff, 0xffffff], 3.5, 0.5, 0.09, 12, 1);
}
// hitscan water: draw the stream instead of a tracer (true = handled). own: your shot, from your viewmodel's nozzle
export function secShot(segs, mz) {
  if (!Array.isArray(segs)) return false;
  segs.forEach((s, i) => { if (Array.isArray(s) && s.length >= 6) waterArc(i === 0 && mz ? mz : s.slice(0, 3), s.slice(3, 6)); });
  return true;
}
function stepFx(dt, now) {
  for (let i = bolts.length - 1; i >= 0; i--) {
    const o = bolts[i];
    o.life -= dt;
    if (o.life <= 0) { for (const m of o.segs) { G.scene.remove(m); m.material.dispose(); } bolts.splice(i, 1); continue; }
    if (now > o.next) { o.next = now + 40; jag(o); }
    for (const m of o.segs) m.material.opacity = 0.95 * Math.min(1, o.life / (o.ml * 0.5));
  }
  for (let i = wires.length - 1; i >= 0; i--) {
    const w = wires[i];
    w.t += dt; w.life -= dt;
    const a = w.life > 0 ? w.from() : null, k = Math.min(1, w.t / 0.07);
    if (!a) { for (const m of w.m) { G.scene.remove(m); m.material.dispose(); } for (const t of w.tip) { G.scene.remove(t); t.geometry.dispose(); } wires.splice(i, 1); continue; }
    for (let j = 0; j < 2; j++) {
      const off = j ? 0.09 : -0.07, b = [a[0] + (w.to[0] - a[0]) * k, a[1] + (w.to[1] + off - a[1]) * k, a[2] + (w.to[2] - a[2]) * k];
      const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 0.15 * k, (a[2] + b[2]) / 2]; // slack wire: it droops in the middle
      setBeam(w.m[j * 2], a, mid, 0.012); setBeam(w.m[j * 2 + 1], mid, b, 0.012);
      w.tip[j].position.set(b[0], b[1], b[2]); w.tip[j].lookAt(a[0], a[1], a[2]);
    }
  }
  for (let i = streams.length - 1; i >= 0; i--) {
    const s = streams[i];
    s.life -= dt;
    if (s.life <= 0) { for (const m of s.segs) { G.scene.remove(m); m.material.dispose(); } streams.splice(i, 1); continue; }
    for (const m of s.segs) m.material.opacity = 0.92 * Math.min(1, (s.life / s.ml) * 1.6);
  }
  for (let i = trails.length - 1; i >= 0; i--) {
    const t = trails[i];
    t.life -= dt;
    if (t.life <= 0) { G.scene.remove(t.g); freeTree(t.g); trails.splice(i, 1); continue; }
    t.g.children.forEach((m, j) => { const on = (t.ml - t.life) * 14 - (t.g.children.length - j); m.material.opacity = Math.max(0, Math.min(0.55, on)) * Math.min(1, t.life / 0.25); });
  }
}
// rewind: VHS afterimages along the path back (newest first, so it plays like the tape going backwards)
const trails = [];
function rewindTrail(pts) {
  const g = new THREE.Group();
  pts.forEach((p, i) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.55, 1.75, 0.32), new THREE.MeshBasicMaterial({ color: i % 2 ? 0xff4fd8 : 0x4fd8ff, transparent: true, opacity: 0, depthWrite: false }));
    m.position.set(p[0] + (i % 2 ? 0.06 : -0.06), p[1] + 0.9, p[2]); g.add(m);
  });
  G.scene.add(g);
  trails.push({ g, life: 0.9, ml: 0.9 });
}

// ---------------------------------------------------------------- per-person overlays (live remotes and replay ghosts)
// key = the Remote (or ghost) object. drips (soaked), arcs (stunned), labels (PAUSED, SLOW DOWN, a radar reading), a cage
const ents = new Map();
function ent(r) {
  let e = ents.get(r);
  if (!e) {
    e = { drips: null, arcs: null, pauseL: null, ticketL: null, readL: null, readUntil: 0, read: 0, f: 0, ticketUntil: 0, puddle: null, seen: 0 };
    ents.set(r, e);
  }
  return e;
}
function dropEnt(r, e) {
  for (const k of ['drips', 'arcs', 'pauseL', 'ticketL', 'readL', 'puddle']) if (e[k]) { G.scene.remove(e[k]); freeTree(e[k]); e[k] = null; }
  if (cages.has(r)) { const c = cages.get(r); G.scene.remove(c.g); freeTree(c.g); cages.delete(r); }
  ents.delete(r);
}
const DRIP_GEO = new THREE.BoxGeometry(0.045, 0.07, 0.045);
function drips() {
  const g = new THREE.Group(), mat = new THREE.MeshBasicMaterial({ color: 0x5cc8ff, transparent: true, opacity: 0.85 });
  for (let i = 0; i < 9; i++) { const m = new THREE.Mesh(DRIP_GEO, mat); m.userData.v = 0; m.userData.y0 = 0.6 + Math.random() * 1.4; m.position.set(R(0.3), m.userData.y0 - Math.random(), R(0.25)); g.add(m); }
  return g;
}
function arcs() {
  const g = new THREE.Group();
  for (let i = 0; i < 14; i++) { const m = makeBeam(i % 3 ? 0xe8ff3a : 0xffffff, 0.95); m.material.blending = THREE.AdditiveBlending; m.material.depthWrite = false; g.add(m); }
  const glow = new THREE.Mesh(new THREE.BoxGeometry(0.9, 2.0, 0.9), new THREE.MeshBasicMaterial({ color: 0xe8ff3a, transparent: true, opacity: 0.18, blending: THREE.AdditiveBlending, depthWrite: false }));
  glow.userData.glow = true; g.add(glow);
  return g;
}
function puddle() {
  const m = new THREE.Mesh(new THREE.CircleGeometry(0.75, 10), new THREE.MeshBasicMaterial({ color: 0x3fb8ff, transparent: true, opacity: 0.45, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; return m;
}
function overlay(r, dt, now, live) {
  const e = ent(r), f = r.f || 0, vis = r.alive && (!live || (r.ch && r.ch.root.visible !== false));
  e.seen = now;
  const p = r.pos, top = p[1] + (r.rigOn ? 3.4 : 2.65);
  // soaked: drips off them + a puddle under their feet
  const soaked = vis && !!(f & FLAGS.SOAK);
  if (soaked && !e.drips) { e.drips = drips(); e.puddle = puddle(); G.scene.add(e.drips, e.puddle); }
  if (e.drips) {
    e.drips.visible = e.puddle.visible = soaked;
    if (soaked) {
      e.drips.position.set(p[0], p[1], p[2]);
      for (const d of e.drips.children) { d.userData.v += 9 * dt; d.position.y -= d.userData.v * dt; if (d.position.y < 0.02) { d.position.set(R(0.32), d.userData.y0, R(0.25)); d.userData.v = 0; } }
      const fl = raycast([p[0], p[1] + 0.4, p[2]], [0, -1, 0], 3, BOXES);
      e.puddle.position.set(p[0], (fl ? fl.point[1] : p[1]) + 0.03, p[2]);
      e.puddle.scale.setScalar(0.8 + Math.sin(now * 0.002) * 0.08);
    }
  }
  // stunned: arcs crackling round them, the body shaking
  const stunned = vis && !!(f & FLAGS.STUN);
  if (stunned && !e.arcs) { e.arcs = arcs(); G.scene.add(e.arcs); }
  if (e.arcs) {
    e.arcs.visible = stunned;
    if (stunned) {
      if (!e.arcN || now > e.arcN) {
        e.arcN = now + 45;
        e.arcs.children.forEach((m) => {
          if (m.userData.glow) { m.position.set(p[0], p[1] + 1.05, p[2]); m.material.opacity = 0.1 + Math.random() * 0.2; return; }
          const y = 0.1 + Math.random() * 2.0, a = Math.random() * 6.28, b = a + R(1.8), r0 = 0.3 + Math.random() * 0.35;
          setBeam(m, [p[0] + Math.cos(a) * r0, p[1] + y, p[2] + Math.sin(a) * r0], [p[0] + Math.cos(b) * (r0 + 0.2), p[1] + y + R(0.7), p[2] + Math.sin(b) * (r0 + 0.2)], 0.05 + Math.random() * 0.04);
        });
        if (Math.random() < 0.25) sfx.arc(p);
      }
      if (live && r.ch) { r.ch.root.rotation.z = R(0.08); r.ch.root.position.x += R(0.03); }
    }
  }
  // paused: a blinking VCR PAUSE label
  const paused = vis && !!(f & FLAGS.PAUSE);
  if (paused && !e.pauseL) { e.pauseL = label(240, 80); G.scene.add(e.pauseL); }
  if (e.pauseL) {
    e.pauseL.visible = paused && Math.floor(now / 250) % 8 !== 7; // a VCR blink
    if (paused) { e.pauseL.userData.set('❚❚ PAUSED', '#ffffff', '#2e7bff', '#ff4fd8'); e.pauseL.position.set(p[0], top + 0.15, p[2]); }
  }
  if (paused && !(e.f & FLAGS.PAUSE)) sfx.pause(p);
  if (!paused && (e.f & FLAGS.PAUSE) && r.alive) sfx.unpause(p);
  // ticketed: SLOW DOWN in police red / blue (with the countdown when we know it)
  const tk = vis && !!(f & FLAGS.TICKET);
  if (tk && !e.ticketL) { e.ticketL = label(280, 96); G.scene.add(e.ticketL); }
  if (e.ticketL) {
    e.ticketL.visible = tk;
    if (tk) {
      const left = e.ticketUntil > now ? Math.ceil((e.ticketUntil - now) / 1000) : 0, blue = Math.floor(now / 180) % 2;
      e.ticketL.userData.set('SLOW DOWN!', '#ffffff', blue ? '#2e7bff' : '#ff3030', blue ? '#ff3030' : '#2e7bff', left ? `${left}...` : '');
      e.ticketL.position.set(p[0], top + (paused ? 0.6 : 0.2), p[2]);
    }
  }
  // the latest radar reading over their head
  if (e.readL) {
    e.readL.visible = vis && now < e.readUntil;
    const k = Math.min(1, (now - (e.readUntil - 1400)) / 120);
    e.readL.position.set(p[0], top + 0.55 + (tk ? 0.45 : 0), p[2]);
    e.readL.scale.set(0.09 * 3 * (0.7 + 0.3 * k), 0.09 * (0.7 + 0.3 * k), 1);
  }
  // caged: from the flag (replays, late joiners, a missed message); the 'jail' message slams it a moment sooner
  const jailed = r.alive && !!(f & FLAGS.JAIL);
  if (jailed && !cages.has(r)) cageOn(r, p, !(e.f & FLAGS.JAIL) || !live);
  if (!jailed && cages.has(r) && (e.f & FLAGS.JAIL)) cageOff(r, e.rigOut);
  if (jailed && cages.has(r)) cages.get(r).g.visible = vis || !live;
  // holding the radar gun up
  if (live && vis && (f & FLAGS.RADAR) && r.popItem) {
    if (r.itemMesh && r.items && r.itemMesh === r.items.radar && r.itemMesh.parent) r.itemUntil = now + 250;
    else r.popItem('radar', 250);
  }
  e.f = vis ? f : 0;
}
function reading(r, v) {
  if (!r) return;
  const e = ent(r);
  if (!e.readL) { e.readL = label(240, 80); G.scene.add(e.readL); }
  const col = v >= SPEED.jail ? '#ff3030' : v > SPEED.limit ? '#ffe14d' : '#39ff14';
  e.readL.userData.set(`${v} KM/H`, col, '#111111', v > SPEED.limit ? '#ff3030' : '#2e7bff');
  e.readUntil = nowMs() + 1400; e.read = v;
}

// ---------------------------------------------------------------- the radar gun in your hand (hold G)
let radarVM = null, radarK = 0;
function ensureRadarVM() {
  if (radarVM || !G.vmScene) return radarVM;
  radarVM = new THREE.Group();
  const g = buildWeapon('radar', (G.equipped || {}).radar);
  g.scale.setScalar(1.05);
  radarVM.add(g);
  const hand = new THREE.Mesh(new THREE.BoxGeometry(0.052, 0.062, 0.09), M(0xf1c27d)); hand.position.set(0, -0.05, 0.03); radarVM.add(hand);
  radarVM.userData.g = g;
  radarVM.visible = false;
  G.vmScene.add(radarVM);
  return radarVM;
}
function updateRadarVM(dt, now) {
  const vm = ensureRadarVM();
  if (!vm) return;
  radarK = S.radar && ME.alive ? Math.min(1, radarK + dt * 6) : Math.max(0, radarK - dt * 7);
  vm.visible = radarK > 0.01;
  if (!vm.visible) return;
  const e = 1 - (1 - radarK) ** 3;
  vm.position.set(-0.15, -0.16 - (1 - e) * 0.28, -0.34);
  vm.rotation.set(0.05 + (1 - e) * 0.6, -0.1, 0.04 + Math.sin(now * 0.004) * 0.01);
  const g = vm.userData.g, scr = g.userData.screen;
  if (scr) {
    const v = S.radarV;
    scr.userData.set(v == null ? '---' : String(Math.min(999, v)), v == null ? '#ff2a2a' : v >= SPEED.jail ? '#ff2a2a' : v > SPEED.limit ? '#ffe14d' : '#39ff14');
  }
  if (g.userData.lamp) g.userData.lamp.visible = Math.floor(now / 250) % 2 === 0;
}

// ---------------------------------------------------------------- aiming: who's under your crosshair
function pick(range, cone) {
  const e = eye(), d = look();
  let best = null, bs = 1e9;
  for (const r of G.remotes.values()) {
    if (!r.alive || isFriend(r)) continue;
    if (r.bot && r.name === 'Dummy' && G.mode !== 'training') continue;
    const c = [r.pos[0], r.pos[1] + 1.1, r.pos[2]], v = [c[0] - e[0], c[1] - e[1], c[2] - e[2]], dist = Math.hypot(...v);
    if (dist > range + 1 || dist < 0.05) continue;
    const ang = Math.acos(Math.max(-1, Math.min(1, (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / dist))), allow = cone + Math.atan2(0.9, dist);
    if (ang > allow || raycast(e, v.map((x) => x / dist), Math.max(0, dist - 0.4), BOXES)) continue;
    const s = ang / allow + dist * 0.002;
    if (s < bs) { bs = s; best = r; }
  }
  return best;
}

// ---------------------------------------------------------------- firing (weapons.js fireDown, main.js aimDown)
export function secBlocked(now = nowMs()) { return ME.alive && (now < S.stun || now < S.pause || now < S.jail); }
export function secFrozen(now = nowMs()) { return secBlocked(now); }
export function secFireDown(id, now) {
  if (secBlocked(now)) return;
  if (id === 'taser') {
    if ((W.cd.taser || 0) > now) return;
    W.cd.taser = now + TZ.cd * 1000;
    const t = pick(TZ.range, TZ.cone), o = eye(), d = look();
    net.send({ t: 'fire', w: 'taser', o: o.map(r2), d: d.map(r2), to: t ? t.id : 0 });
    const mz = VMX.muzzle();
    let to;
    if (t) to = [t.pos[0], t.pos[1] + 1.1, t.pos[2]];
    else { const h = raycast(o, d, TZ.range, BOXES), k = h ? h.t : TZ.range; to = [o[0] + d[0] * k, o[1] + d[1] * k, o[2] + d[2] * k]; }
    darts(() => (ME.alive && W.cur === 'taser' ? VMX.muzzle() : null), to);
    sfx.taser(); fx.sparks(mz, look(), 6);
    VMX.kick('taser', 0.8); W.kick = 0.4;
    return;
  }
  if (id === 'remote') remoteClick(0, now);
}
// right click with the remote out = REWIND (true = it took the click)
export function secAimDown() {
  if (W.cur !== 'remote' || !ME.alive) return false;
  if (W.eco && W.eco.dry('remote')) return true; // Plant & Defuse: out of batteries
  remoteClick(1, nowMs());
  return true;
}
function remoteClick(mode, now) {
  if (secBlocked(now)) return;
  const k = mode ? 'rewind' : 'pause';
  if (S.rmCd[k] > now || (S.rmLast || 0) > now - 250) { sfx.empty(); return; }
  S.rmCd[k] = now + RM[k].cd * 1000; S.rmLast = now;
  const t = pick(RM.range, RM.cone), o = eye(), d = look();
  net.send({ t: 'fire', w: 'remote', m: mode, o: o.map(r2), d: d.map(r2), to: t ? t.id : 0 });
  sfx.remoteClick();
  VMX.kick('remote', 0.35); W.kick = 0.15;
  const m = VMX.model('remote');
  if (m && m.g.userData.ir) { m.g.userData.ir.material = M(mode ? 0xff5a8a : 0x2e7bff, true); S.irT = now + 160; }
  // the IR beam (you only ever see it in cartoons)
  const mz = VMX.muzzle();
  const end = t ? [t.pos[0], t.pos[1] + 1.1, t.pos[2]] : (() => { const h = raycast(o, d, RM.range, BOXES), q = h ? h.t : RM.range; return [o[0] + d[0] * q, o[1] + d[1] * q, o[2] + d[2] * q]; })();
  fx.tracer(mz, end, mode ? 0xff5a8a : 0x2e7bff, 0.02, 0.12);
}

// ---------------------------------------------------------------- the speed trap: hold G
function radarDown() {
  if (secBlocked()) return true;
  if (!ME.alive || W.item !== 'radar') return false;
  if (!S.radar) { S.radar = true; S.radarT = 0; S.radarV = null; sfx.click(); }
  return true;
}
function radarUp() {
  if (!S.radar) return;
  S.radar = false;
  net.send({ t: 'radar', off: 1 });
}
function radarTick(now) {
  if (!S.radar) return;
  if (!ME.alive || W.item !== 'radar' || secBlocked(now)) { radarUp(); return; }
  if (now < S.radarT) return;
  S.radarT = now + SPEED.scan * 1000;
  const t = pick(SPEED.range, SPEED.cone);
  S.radarTo = t ? t.id : 0;
  if (!t) S.radarV = null;
  net.send({ t: 'radar', to: S.radarTo, d: look().map(r2) });
}

// ---------------------------------------------------------------- server messages
// who `id` is, live or in a replay (null = nobody we draw)
const liveOf = (id) => (id === G.myId ? null : G.remotes.get(id) || null);
const posOf = (id, get) => { if (id === G.myId && !RP.active) return ME.pos; const r = get(id); return r ? r.pos : null; };
const chest = (p) => (p ? [p[0], p[1] + 1.1, p[2]] : null);
// the 'fx' kinds that are ours. live = this match (it can be you); get = id -> remote / ghost
function fxOf(m, live, get) {
  const now = nowMs();
  if (m.k === 'zap') {
    const from = m.id === G.myId && live ? () => (ME.alive && W.cur === 'taser' ? VMX.muzzle() : eye()) : () => { const r = get(m.id); return r && r.alive ? r.muzzle() : null; };
    const links = Array.isArray(m.l) ? m.l : [];
    if (!m.self && links.length && !(m.id === G.myId && live)) { const L0 = links[0]; if (L0.length >= 8) darts(from, L0.slice(5, 8)); }
    if (!links.length && ok3(m.e) && !(m.id === G.myId && live)) darts(from, m.e);
    links.forEach((L, i) => {
      if (!Array.isArray(L) || L.length < 8 || !L.every((x, j) => j < 2 || Number.isFinite(x))) return;
      const a = L.slice(2, 5), b = L.slice(5, 8);
      if (m.self) { for (let j = 0; j < 4; j++) bolt([b[0] + R(0.3), b[1] + R(0.6), b[2] + R(0.3)], [b[0] + R(0.4), b[1] + R(0.8), b[2] + R(0.4)], 0xe8ff3a, 0.3, 0.04); }
      else if (i === 0) bolt(m.id === G.myId && live ? VMX.muzzle() : a, b, 0xe8ff3a, 0.45, 0.06);
      else { setTimeout(() => { bolt(a, b, 0x9ff6ff, 0.5, 0.07); fx.sparks(b, null, 14, true); sfx.arc(b); }, i * 70); }
      fx.sparks(b, null, 10, true);
    });
    const p0 = links.length ? links[0].slice(5, 8) : m.e;
    if (ok3(p0)) sfx.buzz(p0, 0.5 + Math.min(0.6, links.length * 0.1), 1);
    if (live && links.length > 2) hud.msg(`${links.length} WAY CHAIN!`, 1.2, 'brag');
    return true;
  }
  if (m.k === 'pause') {
    const p = ok3(m.p) ? m.p : posOf(m.id, get);
    if (p) { fx.ring(p, 2.2, 0x2e7bff, 0.3); sfx.pause(chest(p)); }
    if (live && m.id === G.myId && Number.isFinite(m.dur)) {
      S.pause = now + m.dur * 1000; S.pauseAt = ME.pos.slice(); S.pauseVel = ME.vel.slice(); releaseHook();
      W.held = false; W.aimHeld = false;
    }
    if (live && m.by === G.myId) hud.msg(`PAUSED ${nameOf(m.id)}`, 1, 'brag');
    return true;
  }
  if (m.k === 'rewind') {
    if (!ok3(m.a) || !ok3(m.b)) return true;
    const tr = Array.isArray(m.tr) ? m.tr.filter(ok3) : [];
    if (!(live && m.id === G.myId)) rewindTrail([m.a, ...tr, m.b]); // (yours is the VHS screen, not boxes in your face)
    sfx.rewind(chest(m.b)); sfx.rewind(chest(m.a));
    fx.ring(m.b, 2, 0xff4fd8, 0.35);
    if (live && m.id === G.myId) {
      ME.pos = m.b.slice(); ME.vel = [0, 0, 0]; releaseHook(); S.pause = 0;
      S.vhs = now + 900; S.vhsKind = '◀◀ REWIND';
    } else if (live) { const r = get(m.id); if (r && r.buf) r.buf.length = 0; } // don't interpolate the jump
    if (live && m.by === G.myId) hud.msg(`REWOUND ${nameOf(m.id)}`, 1, 'brag');
    return true;
  }
  if (m.k === 'rmiss') {
    const r = get(m.id);
    if (r && ok3(m.e) && !(live && m.id === G.myId)) fx.tracer(r.muzzle(), m.e, m.m ? 0xff5a8a : 0x2e7bff, 0.02, 0.12);
    return true;
  }
  if (m.k === 'radar') {
    const v = Number.isFinite(m.v) ? Math.max(0, Math.min(9999, m.v | 0)) : 0;
    if (live && m.to === G.myId) { S.detected = now + 1200; if (v > SPEED.limit) sfx.radarBeep(null, true); }
    else reading(get(m.to), v);
    if (live && m.id === G.myId) { S.radarV = v; sfx.radarBeep(null, v > SPEED.limit); }
    return true;
  }
  if (m.k === 'grounded') { const p = posOf(m.id, get); if (p) { fx.sparks([p[0], p[1] + 1.5, p[2]], null, 16); sfx.arc(p); } return true; }
  return false;
}
function onSoak(m, live, get) {
  const p = posOf(m.id, get), now = nowMs();
  if (p) { fx.spray([p[0], p[1] + 1.3, p[2]], 12, [0x3fb8ff, 0xbfeaff, 0xffffff], 4, 0.6, 0.09, 10, 1); sfx.splash(chest(p), m.id === G.myId && live ? 0.6 : 1); }
  if (m.x && p) { sfx.sizzle(chest(p)); for (let i = 0; i < 4; i++) fx.smoke([p[0] + R(0.3), p[1] + 1 + Math.random(), p[2] + R(0.3)], 2, 0.3); }
  if (live && m.id === G.myId && Number.isFinite(m.dur)) {
    if (now > S.soak) hud.msg(m.x ? 'FIRE PUT OUT' : 'SOAKED', 0.9, 'slip');
    S.soak = now + m.dur * 1000;
    if (m.x) G.burnUntil = 0;
  }
}
function onJail(m, live, get) {
  if (!ok3(m.p)) return;
  const now = nowMs(), key = live && m.id === G.myId ? 'me' : get(m.id);
  if (key) cageOn(key, m.p, !m.late);
  if (m.rig) { if (key === 'me') S.rigOut = true; else if (key) ent(key).rigOut = true; } // an overdrive rig rips it open
  if (!live) return;
  if (!m.late) sfx.siren(m.p, 1.2);
  if (m.id === G.myId) {
    S.jail = now + (Number.isFinite(m.dur) ? m.dur : SPEED.jailT) * 1000; S.jailAt = m.p.slice(); S.ticket = null; S.pause = 0;
    ME.pos = m.p.slice(); ME.vel = [0, 0, 0]; releaseHook(); W.held = false; W.aimHeld = false;
    S.jailV = m.v;
  }
  if (!m.late && m.by) hud.feed([[nameOf(m.by), colorOf(m.by)], ['  [Speed Trap]  ', ITEMS.radar.color], [nameOf(m.id), colorOf(m.id)], [`  JAILED${m.v ? ` (${m.v} km/h)` : ''}`, '#ff3030']]);
  if (m.by === G.myId && m.id !== G.myId) flashBanner('BUSTED!', `${nameOf(m.id)} was doing ${m.v || '???'} km/h`, 'cop', 1600);
}
function onJailx(m, live, get) {
  if (live && m.id === G.myId) { S.jail = 0; cageOff('me', S.rigOut); S.rigOut = false; return; }
  const r = get(m.id);
  if (r) cageOff(r, ent(r).rigOut);
}

export function initSec() {
  initHud();
  const prev = W.itemHook;
  W.itemHook = (id) => {
    if (secBlocked()) return true; // stunned, paused or caged: no items
    if (id === 'radar') return radarDown();
    return prev ? prev(id) : false;
  };
  addEventListener('keyup', (e) => { if (e.code === 'KeyG') radarUp(); });
  addEventListener('blur', radarUp);
  net.on('soak', (m) => { recordEv(m); onSoak(m, true, liveOf); });
  net.on('stun', (m) => {
    if (!Number.isFinite(m.dur)) return;
    S.stun = Math.max(S.stun, nowMs() + m.dur * 1000); releaseHook(); W.held = false; W.aimHeld = false;
    G.shake = Math.max(G.shake || 0, 0.6); sfx.buzz(null, Math.min(1.5, m.dur), 0.8);
    S.stunSelf = !m.by;
  });
  net.on('jail', (m) => { recordEv(m); onJail(m, true, liveOf); });
  net.on('jailx', (m) => { recordEv(m); onJailx(m, true, liveOf); });
  net.on('ticket', (m) => {
    recordEv(m);
    const now = nowMs(), s = Number.isFinite(m.s) ? m.s : SPEED.warn;
    if (m.id === G.myId) { S.ticket = { until: now + s * 1000, lim: m.lim || SPEED.limit, v: m.v }; sfx.siren(null, 0.9); }
    else { const r = liveOf(m.id); if (r) ent(r).ticketUntil = now + s * 1000; }
    if (m.by === G.myId) flashBanner('PULLED OVER', `${nameOf(m.id)}: ${m.v} km/h in a ${SPEED.limit} zone`, 'cop', 1400);
  });
  net.on('ticketx', (m) => {
    recordEv(m);
    if (m.id === G.myId) { S.ticket = null; if (m.ok) { flashBanner('WARNING', 'drive safe out there', 'ok', 1500); sfx.warning(); } }
    else { const r = G.remotes.get(m.id); if (r) ent(r).ticketUntil = 0; }
  });
  net.on('rwdfix', (m) => { if (ok3(m.p)) { ME.pos = m.p.slice(); ME.vel = [0, 0, 0]; } });
  // replays: the same messages, drawn on the ghosts
  RP_HOOKS.push({
    ev(m, ghosts) {
      const get = (id) => ghosts.get(id) || null;
      if (m.t === 'fx' && fxOf(m, false, get)) return true;
      if (m.t === 'soak') { onSoak(m, false, get); return true; }
      if (m.t === 'jail') { onJail(m, false, get); return true; }
      if (m.t === 'jailx') { onJailx(m, false, get); return true; }
      return m.t === 'ticket' || m.t === 'ticketx';
    },
    step(t, ghosts, dt) { const now = nowMs(); for (const g of ghosts.values()) overlay(g, dt, now, false); },
    stop() { for (const [r, e] of [...ents]) if (r.ghost) dropEnt(r, e); },
  });
}
// main.js 'fx': ours? (live)
export function secFx(m) {
  if (!['zap', 'pause', 'rewind', 'rmiss', 'radar', 'grounded'].includes(m.k)) return false;
  recordEv(m);
  fxOf(m, true, liveOf);
  return true;
}
export function secSpawn() {
  Object.assign(S, { soak: 0, stun: 0, pause: 0, jail: 0, ticket: null, vhs: 0 });
  S.rmCd = { pause: 0, rewind: 0 };
  if (cages.has('me')) cageOff('me');
  radarUp();
}
export function secLeave() {
  secSpawn();
  for (const [r, e] of [...ents]) dropEnt(r, e);
  for (const [k, c] of [...cages]) { G.scene.remove(c.g); freeTree(c.g); cages.delete(k); }
  if (G.renderer) G.renderer.domElement.style.filter = '';
}

// ---------------------------------------------------------------- every frame
export function updateSec(dt, now) {
  initHud();
  // you: held still, slowed, slipping
  const soaked = ME.alive && now < S.soak;
  ME.wetGrip = soaked ? WP.soak.grip : 1;
  if (soaked) ME.speedMul *= WP.soak.slow;
  if (ME.alive && now < S.pause && S.pauseAt) { ME.pos = S.pauseAt.slice(); ME.vel = [0, 0, 0]; }
  else if (S.pauseAt) { if (ME.alive && S.pauseVel) ME.vel = S.pauseVel.slice(); S.pauseAt = null; S.pauseVel = null; if (ME.alive) sfx.unpause(); } // momentum comes back
  if (ME.alive && now < S.jail && S.jailAt) { ME.pos[0] = S.jailAt[0]; ME.pos[2] = S.jailAt[2]; ME.pos[1] = Math.max(ME.pos[1], S.jailAt[1] - 0.05); ME.vel = [0, Math.min(0, ME.vel[1]), 0]; if (ME.pos[1] < S.jailAt[1] + 0.02) ME.pos[1] = S.jailAt[1]; }
  if (secBlocked(now)) { W.held = false; W.aimHeld = false; if (ME.hook) releaseHook(); }
  if (ME.alive && now < S.stun) { ME.yaw += R(0.012); ME.pitch += R(0.01); }
  if (!ME.alive && (S.jail || S.pause || S.stun || S.ticket)) secSpawn();
  if (S.irT && now > S.irT) { S.irT = 0; const m = VMX.model('remote'); if (m && m.g.userData.ir) m.g.userData.ir.material = M(0xff3030, true); }
  radarTick(now);
  updateRadarVM(dt, now);
  // others (live): overlays from their flags; anyone gone or hidden gets cleaned up
  if (!RP.active) for (const r of G.remotes.values()) overlay(r, dt, now, true);
  for (const [r, e] of [...ents]) if (now - e.seen > 400 || (!r.ghost && !RP.active && !G.remotes.has(r.id))) dropEnt(r, e);
  if (RP.active) for (const [r, e] of ents) if (!r.ghost) for (const k of ['drips', 'arcs', 'pauseL', 'ticketL', 'readL', 'puddle']) if (e[k]) e[k].visible = false;
  stepCages(now);
  stepFx(dt, now);
  drawHud(now);
}
function drawHud(now) {
  if (!hudEl) return;
  const alive = ME.alive && !RP.active;
  $('secWet').style.opacity = alive && now < S.soak ? Math.min(1, (S.soak - now) / 800) : 0;
  $('secStatic').style.opacity = alive && now < S.stun ? 0.6 + Math.random() * 0.4 : 0;
  $('secBars').style.opacity = alive && now < S.jail ? 1 : 0;
  const vhs = alive && (now < S.vhs || now < S.pause);
  $('secVhs').style.opacity = vhs ? 1 : 0;
  if (vhs) $('secVhsTxt').textContent = now < S.pause ? (Math.floor(now / 500) % 2 ? '❚❚ PAUSE' : '') : S.vhsKind;
  if (G.renderer) G.renderer.domElement.style.filter = alive && now < S.pause ? 'grayscale(0.7) contrast(1.1)' : alive && now < S.vhs ? 'hue-rotate(40deg) saturate(1.6)' : '';
  $('secDetect').style.opacity = alive && now < S.detected ? (Math.floor(now / 150) % 2 ? 1 : 0.4) : 0;
  // the radar box round your crosshair
  const ro = $('secRadar');
  ro.style.opacity = alive && S.radar ? 1 : 0;
  if (S.radar) ro.firstChild.textContent = S.radarV == null ? '--- km/h' : `${S.radarV} km/h`;
  // the big banner: whatever matters most right now
  const tip = $('secTip');
  tip.textContent = alive && W.cur === 'remote' ? `LMB ❚❚ pause ${cdTxt(S.rmCd.pause, now)}   ·   RMB ◀◀ rewind ${cdTxt(S.rmCd.rewind, now)}` : alive && S.radar ? `limit ${SPEED.limit} km/h · over ${SPEED.jail} = straight to jail` : '';
  if (now < bannerUntil) return;
  if (bannerLock) { bannerLock = ''; banner(''); }
  if (!alive) { banner(''); return; }
  if (now < S.jail) banner('JAILED', `${((S.jail - now) / 1000).toFixed(1)}s${S.jailV ? ` · you were doing ${S.jailV} km/h` : ''}`, 'jail');
  else if (S.ticket && now < S.ticket.until + 400) {
    const sp = Math.round(Math.hypot(...ME.vel) * 3.6), left = Math.max(0, Math.ceil((S.ticket.until - now) / 1000));
    banner(`SLOW DOWN! ${left}`, `${sp} km/h · get under ${S.ticket.lim}`, Math.floor(now / 200) % 2 ? 'cop' : 'jail');
  } else if (now < S.stun) banner('ZZZZT!', S.stunSelf ? 'you tased yourself. it was wet.' : 'tased', '');
  else banner('');
}
const cdTxt = (t, now) => (t > now ? `${((t - now) / 1000).toFixed(1)}s` : 'ready');
export const SEC_DEBUG = { ents, cages, S, bolts, streams }; // (tests look in here)
