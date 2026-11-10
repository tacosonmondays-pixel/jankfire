// Chaos modes on the client: the lava floor (glow, bubbles, sizzle, and the bounce you get when you touch it),
// duck rain warnings (a shadow + whistle where each duck will land), one in the chamber's bullets / lives and
// spectating once you're out, and the stronger grapple pull in spoons & grapples.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx, PSys } from './fx.js';
import { liquidMaterial } from './liquidmats.js'; // (the shared lava: liquidmats.js)
import { ME } from './player.js';
import { W } from './weapons.js';
import { RP } from './replay.js';
import { MAPS, BOXES } from '/shared/map.js';
import { GAMES } from '/shared/modes.js';
import { raycast } from '/shared/physics.js';
import { surfaces, lavaOk, onLava, LAVA } from '/shared/lava.js';

const $ = (id) => document.getElementById(id);
const R = (s = 1) => (Math.random() * 2 - 1) * s;
const C = { game: null, map: null, s: null, boxes: null, mesh: null, lavaT: 0, introT: 0, drops: [], oitc: null, lives: new Map(), spec: 0, specOn: false, specSnap: true, cls: '' };
let embers = null, bubbles = null;

// the mode we're playing right now (only the Online and Bots rooms have modes)
function current() {
  if (!G.joined || (G.mode !== 'ffa' && G.mode !== 'bots') || !G.round) return null;
  return GAMES[G.round.game] ? G.round.game : null;
}
export const chaosNoStreaks = () => { const g = current(); return !!(g && GAMES[g].kit && GAMES[g].kit.noStreaks); };

// hud bits live in the page only while they're needed
function el(id, cls) {
  let e = $(id);
  if (!e) { e = document.createElement('div'); e.id = id; if (cls) e.className = cls; $('hud').append(e); }
  return e;
}

// ------------------------------------------------------------ floor is lava
// (the lava's look lives in liquids.js now)
function buildLava(s) {
  const pos = [], idx = [];
  let n = 0;
  for (const t of s.tops) {
    if (!s.lava.has(t.b)) continue;
    const b = t.b, y = b.max[1] + 0.03;
    pos.push(b.min[0], y, b.min[2], b.max[0], y, b.min[2], b.max[0], y, b.max[2], b.min[0], y, b.max[2]);
    idx.push(n, n + 2, n + 1, n, n + 3, n + 2);
    n += 4;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, liquidMaterial('lava')); // the same flowing lava as the Islands volcano (liquids.js), crust, cracks, bubbles
  mesh.userData.noShadow = true;
  mesh.frustumCulled = false;
  return mesh;
}
function setLava(id) {
  if (C.mesh) { G.scene.remove(C.mesh); C.mesh.geometry.dispose(); C.mesh = null; } // (the material is shared: liquids.js keeps it)
  C.map = id; C.s = id ? surfaces(MAPS[id]) : null; C.boxes = id ? MAPS[id].boxes : null;
  el('lavaGlow').classList.toggle('on', !!id);
  if (!id) return;
  C.mesh = buildLava(C.s);
  G.scene.add(C.mesh);
}
function particles() {
  if (embers) return;
  embers = new PSys(600, THREE.AdditiveBlending);
  bubbles = new PSys(400, THREE.AdditiveBlending);
  G.scene.add(embers.points, bubbles.points);
}
// bubbles popping and embers spitting out of the floor around you
function tickLava(now) {
  const cam = G.camera.position;
  for (let i = 0; i < 4; i++) {
    const a = Math.random() * Math.PI * 2, r = 2 + Math.random() * 34;
    const x = cam.x + Math.cos(a) * r, z = cam.z + Math.sin(a) * r;
    const h = raycast([x, cam.y + 2, z], [0, -1, 0], 120, C.boxes);
    if (!h || !C.s.lava.has(h.box)) continue;
    const y = h.point[1] + 0.05;
    bubbles.spawn(x, y, z, 0, 0.3 + Math.random() * 0.4, 0, 0.5 + Math.random() * 0.7, 0.2, 0.6 + Math.random() * 0.6, 0xffd040, 0xff2a00, 0.9, 0, 0);
    if (Math.random() < 0.3) for (let k = 0; k < 4; k++) embers.spawn(x, y + 0.1, z, R(1.4), 2 + Math.random() * 3.5, R(1.4), 0.7 + Math.random() * 0.6, 0.13, 0.03, 0xffe070, 0xff2200, 1, 6, 0.3);
  }
}
// after every physics step: touching the ground floor bounces you straight back up, burns, and tells the server
export function lavaStep(now) {
  if (!C.mesh || !ME.alive || !ME.onGround || !onLava(C.s, C.boxes, ME.pos)) return;
  ME.vel[1] = Math.max(ME.vel[1], LAVA.hop); ME.onGround = false; ME.pos[1] += 0.03;
  if (now - C.lavaT < 300) return;
  C.lavaT = now;
  net.send({ t: 'lava' });
  sfx.sizzle();
  G.shake = Math.max(G.shake, 0.35);
  G.burnUntil = now + 900;
  hud.msg(['HOT HOT HOT', 'OW OW OW', 'LAVA!', 'NOT THE FLOOR'][(Math.random() * 4) | 0], 0.7, 'lava');
  const f = el('lavaHit');
  f.classList.remove('on'); void f.offsetWidth; f.classList.add('on');
  steam(ME.pos);
}
function steam(p) {
  for (let i = 0; i < 8; i++) fx.smoke([p[0] + R(0.5), p[1] + 0.1, p[2] + R(0.5)], 1, 0.3);
  particles();
  for (let i = 0; i < 10; i++) embers.spawn(p[0] + R(0.4), p[1] + 0.1, p[2] + R(0.4), R(2), 3 + Math.random() * 4, R(2), 0.6, 0.14, 0.03, 0xffe070, 0xff2200, 1, 8, 0.3);
}
net.on('sizzle', (m) => {
  if (m.id === G.myId && performance.now() - C.lavaT < 400) return; // already did it ourselves
  steam(m.p);
  sfx.sizzle(m.p);
  if (m.id === G.myId) { G.burnUntil = performance.now() + 900; G.shake = Math.max(G.shake, 0.35); }
});

// ------------------------------------------------------------ duck rain: a shadow + whistle where each one lands
const DISC = new THREE.CircleGeometry(1, 16).rotateX(-Math.PI / 2);
const RING = new THREE.RingGeometry(0.82, 1, 20).rotateX(-Math.PI / 2);
net.on('skyduck', (m) => {
  if (!G.joined) return;
  const po = { transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -6 };
  const disc = new THREE.Mesh(DISC, new THREE.MeshBasicMaterial({ color: 0x000000, opacity: 0.25, ...po }));
  const ring = new THREE.Mesh(RING, new THREE.MeshBasicMaterial({ color: 0xff2a2a, opacity: 0.9, fog: false, ...po }));
  const g = new THREE.Group();
  g.add(disc, ring);
  g.position.set(m.p[0], m.p[1] + 0.05, m.p[2]);
  G.scene.add(g);
  const ms = Math.max(300, m.ms || 1600);
  C.drops.push({ g, disc, ring, p: m.p, born: performance.now(), ms, warned: false });
  sfx.whistle(m.p, ms / 1000);
});
function tickDrops(now) {
  for (let i = C.drops.length - 1; i >= 0; i--) {
    const d = C.drops[i], k = (now - d.born) / d.ms;
    if (k > 1.1 || !G.joined) {
      G.scene.remove(d.g); d.disc.material.dispose(); d.ring.material.dispose();
      C.drops.splice(i, 1);
      continue;
    }
    const s = 0.4 + Math.min(1, k) * 1.9;
    d.disc.scale.setScalar(s);
    d.disc.material.opacity = 0.18 + Math.min(1, k) * 0.5;
    d.ring.scale.setScalar(s * (1.15 + Math.sin(now * (0.012 + k * 0.03)) * 0.12));
    d.ring.material.opacity = Math.sin(now * (0.015 + k * 0.04)) > -0.3 ? 0.95 : 0.25;
    if (!d.warned && k > 0.25 && ME.alive && Math.hypot(d.p[0] - ME.pos[0], d.p[2] - ME.pos[2]) < 3.5 && Math.abs(d.p[1] - ME.pos[1]) < 4) { d.warned = true; hud.msg('LOOK UP', 0.6, 'lava'); }
  }
}

// ------------------------------------------------------------ one in the chamber: bullets, lives, spectating
net.on('oitc', (m) => {
  const was = C.oitc;
  C.oitc = { b: m.b, l: m.l, out: !!m.out };
  W.ammo.revolver = m.b; // the server counts the bullets
  if (was && m.b > was.b && ME.alive && m.l === was.l) { hud.msg(`+1 BULLET · ${m.b} IN THE CHAMBER`, 1.3, 'brag'); sfx.chamber(); }
  // out but still walking around = we (re)joined a round we're already out of: straight to spectating
  if (m.out && ME.alive && !was) { ME.alive = false; G.deadAt = performance.now() - 3000; hud.dead(true, [['out of lives this round', '#fff']]); }
  if (m.out && !(was && was.out)) { hud.msg('OUT OF LIVES', 2.4, 'brag'); C.specSnap = true; }
  else if (was && m.l < was.l && m.l > 0) hud.chat(null, null, `${m.l} ${m.l > 1 ? 'lives' : 'life'} left`);
  renderLives();
});
net.on('oitcl', (m) => { C.lives = new Map(m.list); renderLives(); });
function renderLives() {
  const box = el('chaosHud');
  const o = C.oitc, max = (GAMES.oitc && GAMES.oitc.bullets[1]) || 3;
  const key = o ? `${o.b}/${o.l}/${o.out}` : '';
  if (box.dataset.key === key) return;
  box.dataset.key = key;
  box.innerHTML = '';
  if (!o) return;
  const bl = document.createElement('div'); bl.className = 'ch-row';
  const bt = document.createElement('span'); bt.textContent = 'BULLETS'; bl.append(bt);
  for (let i = 0; i < max; i++) { const b = document.createElement('i'); b.className = 'ch-bul' + (i < o.b ? ' on' : ''); bl.append(b); }
  const ll = document.createElement('div'); ll.className = 'ch-row';
  const lt = document.createElement('span'); lt.textContent = 'LIVES'; ll.append(lt);
  for (let i = 0; i < Math.max(o.l, GAMES.oitc ? GAMES.oitc.lives : 3); i++) { const h = document.createElement('b'); h.className = 'ch-life' + (i < o.l ? ' on' : ''); h.textContent = i < o.l ? '♥' : '♡'; ll.append(h); }
  box.append(bl, ll);
}
const playersLeft = () => [...C.lives.values()].filter((l) => l > 0).length;
// the round line at the top in one in the chamber
export function chaosRoundText(r) {
  if (!r || r.over || !GAMES[r.game] || !GAMES[r.game].lives) return null;
  const s = Math.ceil(r.left / 1000);
  return `last one standing · ${playersLeft()} left · ${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
function canWatch(r) { return r && r.alive && !(r.bot && r.name === 'Dummy') && (C.lives.get(r.id) ?? 1) > 0; }
function nextSpec(dir = 1) {
  const ids = [...G.remotes.values()].filter(canWatch).map((r) => r.id).sort((a, b) => a - b);
  if (!ids.length) { C.spec = 0; return; }
  const i = ids.indexOf(C.spec);
  C.spec = ids[(i < 0 ? 0 : i + dir + ids.length) % ids.length];
  C.specSnap = true;
}
function tickLives(now) {
  const g = current(), on = !!(g && GAMES[g].lives);
  if (!on && C.oitc) { C.oitc = null; renderLives(); }
  const watch = on && C.oitc && C.oitc.out && !ME.alive && !RP.active && !G.killcamPending && now - (G.deadAt || 0) > 2500;
  C.specOn = !!watch;
  document.body.classList.toggle('chaos-spec', C.specOn);
  const bar = el('specBar');
  bar.classList.toggle('on', C.specOn);
  if (on && C.oitc && C.oitc.out && !ME.alive) $('deadTimer').textContent = 'out of lives';
  if (!C.specOn) return;
  if (!canWatch(G.remotes.get(C.spec))) nextSpec();
  $('dead').classList.add('hidden');
  const r = G.remotes.get(C.spec);
  const text = r ? `OUT OF LIVES · watching ${r.name} · click for the next one · ${playersLeft()} left` : 'OUT OF LIVES · nobody left to watch';
  if (bar.textContent !== text) bar.textContent = text;
}
addEventListener('mousedown', () => { if (C.specOn) nextSpec(1); });
addEventListener('keydown', (e) => { if (C.specOn && (e.code === 'Space' || e.code === 'ArrowRight')) nextSpec(1); else if (C.specOn && e.code === 'ArrowLeft') nextSpec(-1); });
// spectating: over the shoulder of whoever you're watching (returns true when it took the camera)
const camPos = new THREE.Vector3(), camLook = new THREE.Vector3(), tmp = new THREE.Vector3();
export function spectateCam(dt, cam) {
  if (!C.specOn) return false;
  const r = G.remotes.get(C.spec);
  if (!r) return false;
  const yaw = r.yaw || 0, e = [r.pos[0], r.pos[1] + 1.9, r.pos[2]];
  const d = [Math.sin(yaw) * 4.2, 1.1, Math.cos(yaw) * 4.2], L = Math.hypot(...d);
  const hit = raycast(e, d.map((v) => v / L), L, BOXES);
  const k = hit ? Math.max(0.3, hit.t - 0.3) / L : 1;
  tmp.set(e[0] + d[0] * k, e[1] + d[1] * k, e[2] + d[2] * k);
  if (C.specSnap) { camPos.copy(tmp); C.specSnap = false; } else camPos.lerp(tmp, Math.min(1, dt * 10));
  camLook.set(e[0] - Math.sin(yaw) * 10, e[1] - 0.5, e[2] - Math.cos(yaw) * 10);
  cam.position.copy(camPos);
  cam.lookAt(camLook);
  return true;
}

// ------------------------------------------------------------ intros + per-frame upkeep
function intro(game, now, again) {
  const loud = now - C.introT > 3000;
  if (!loud && !again) return;
  if (loud) C.introT = now;
  if (game === 'lava') { hud.msg('THE FLOOR IS LAVA', 3.2, 'lava'); if (loud) { sfx.rumble(); setTimeout(() => sfx.sizzle(), 350); } }
  else if (game === 'duckrain') { hud.msg('DUCK RAIN', 2.4, 'brag'); if (loud) for (let i = 0; i < 3; i++) setTimeout(() => sfx.squeak(), i * 170); }
  else if (game === 'spoons') { hud.msg('SPOONS & GRAPPLES', 2.4, 'brag'); if (loud) sfx.ting(); }
  else if (game === 'oitc') { hud.msg('ONE IN THE CHAMBER', 2.4, 'brag'); if (loud) sfx.chamber(); }
}
// the round just started: show this mode's intro on top of the usual one
export function chaosRoundStart(game) { if (game && GAMES[game] && (game === 'lava' || game === 'duckrain' || game === 'spoons' || game === 'oitc')) intro(game, performance.now(), true); }

export function updateChaos(dt, now) {
  const game = current(), def = game ? GAMES[game] : null;
  G.hookMul = (def && def.hookMul) || 1;
  const lavaMap = def && def.lava && lavaOk(MAPS[G.cfg.map]) ? G.cfg.map : null;
  if (lavaMap !== C.map) setLava(lavaMap);
  if (game !== C.game) {
    C.game = game;
    if (def && (def.kit || def.lava || def.duckRain)) intro(game, now);
    if (!def || !def.lives) { C.oitc = null; C.lives.clear(); C.spec = 0; renderLives(); }
  }
  // hud: no streak tray when the mode has no killstreaks, bullets + lives instead of the ammo counter
  const cls = `${def && def.kit && def.kit.noStreaks ? 'chaos-nostreaks' : ''} ${def && def.lives ? 'chaos-lives' : ''}`.trim();
  if (cls !== C.cls) {
    for (const c of C.cls.split(' ')) if (c) document.body.classList.remove(c);
    for (const c of cls.split(' ')) if (c) document.body.classList.add(c);
    C.cls = cls;
  }
  if (C.mesh) { particles(); tickLava(now); }
  tickDrops(now);
  tickLives(now);
  if (embers) { embers.update(dt); bubbles.update(dt); }
}

// floor is lava: size up each map's floor one at a time while we sit in the menus, so the bots setup screen
// doesn't freeze for half a second working them all out the first time someone picks the mode (never mid-match)
{
  const ids = Object.keys(MAPS);
  const step = () => {
    if (!ids.length) return;
    if (!G.joined) { try { surfaces(MAPS[ids.shift()]); } catch { /* a weird map just isn't lava-ready */ } }
    setTimeout(step, G.joined ? 3000 : 120);
  };
  setTimeout(step, 1500);
}
export const chaosSpecId = () => (C.specOn ? C.spec : 0); // who you're watching once you're out (pip.js shows their eyes)
