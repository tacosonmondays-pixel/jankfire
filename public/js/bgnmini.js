// BOARD GAME NIGHT minigames 11-15, the client (server: server/bgnmini.js). bgn.js hands it every 'bg' message and
// calls it each frame; main.js asks it about clicks (the cart BOOST), the camera (watching once you're out of bumper
// carts) and kill-feed lines. it draws:
//   BUMPER CARTS: you climb into the cart the server put under you, click = BOOST (the server okays it), a seat strip
//     (still in / OUT, team lives in 2v2) and a boost meter. out = a slow orbit over the box.
//   DUCK CATCH: the falling ducks and their shadows, the piles, the pops when someone catches, slaps or gets cursed.
//   THE BIG GUY / the bosses: the callouts and the boss's health bar.
// comic HUD (dark purple panel, pink border, hard cyan shadow), sounds from audio.js (sfx.bgm*).
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { net } from './net.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { hud } from './hud.js';
import { buildProjectile, buildCharacter } from './models.js';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';
import { boardCart } from './primaries.js';
import { BGN_NAMES as N, BGN_MINI, BGN_MINIS } from '/shared/bgn.js';
import { CART } from '/shared/primaries.js';
import { GAMES } from '/shared/modes.js';

const CM = BGN_MINI.carts;
const S = { B: null, x: null, ducks: new Map(), out: false, outT: 0, boostT: -1e9, orbit: 0, dom: null, key: '', piles: {} };
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const kind = () => (S.B && S.B.ph === 'mg' && S.B.mg && S.x ? S.x.k : null);
const mySeat = () => (S.B ? S.B.seats.find((s) => s.id === G.myId) || null : null);
const playing = () => { const s = mySeat(); return !!(s && S.B.mg && S.B.mg.seats.includes(s.i)); };
const posOf = (id) => (id === G.myId ? ME.pos : G.remotes.get(id) ? G.remotes.get(id).pos : null);

// ---------------------------------------------------------------- state from the board
export function miniState(B) {
  S.B = B;
  const x = B && B.mg && B.mg.x;
  if (x) { S.x = x; if (x.pile) S.piles = { ...x.pile }; }
  if (!B || !B.mg || B.ph !== 'mg') { if (S.x) clearAll(); S.x = null; S.out = false; }
}
function clearAll() { for (const d of S.ducks.values()) dropDuck(d); S.ducks.clear(); S.piles = {}; S.key = ''; if (S.dom) S.dom.innerHTML = ''; }

// ---------------------------------------------------------------- events
const EV = {
  mini(m) { S.x = m.x; S.out = false; S.piles = {}; const k = m.x && m.x.k; if (!playing()) return;
    if (k === 'carts') hud.msg('RAM THEM OFF THE BOX', 2.2, 'brag');
    else if (k === 'ducks') hud.msg('LOOK UP', 1.8, 'brag');
    else if (k === 'boss') { hud.msg(N.call.boss, 2.2, 'lava'); sfx.bgmBoss(); }
    else if (k === 'bigguy') hud.msg(N.call.bigguy, 2, 'brag'); },
  boost(m) { const p = posOf(m.id); if (m.id !== G.myId && p) { sfx.bgmBoost(p); fx.smoke([p[0], p[1] - 0.4, p[2]], 4, 0.4); } },
  ram(m) {
    const p = posOf(m.b);
    if (p) { sfx.bgmClank(p, Math.min(1.5, (m.s || 8) / 10)); if (Math.random() < 0.5) sfx.bgmHonk(p); }
    if (m.b === G.myId) { hud.msg(N.call.ram, 1.1, 'lava'); G.shake = Math.max(G.shake || 0, 0.9); }
    else if (m.a === G.myId) hud.msg('BONK', 0.8, 'brag');
  },
  fell(m) {
    if (m.x) S.x = m.x;
    if (m.id !== G.myId) return;
    if (m.out) { S.out = true; S.outT = performance.now(); sfx.bgmOut(); hud.msg(N.call.cartOut, 2.6, 'lava'); setTimeout(() => hud.dead(true, [[m.by ? N.feed.cartDead : N.feed.cartDeadSelf, '#fff']]), 60); }
    else hud.msg(m.x && m.x.pool ? '-1 TEAM LIFE' : '-1 LIFE', 1.6, 'lava');
  },
  cartback(m) { if (m.id === G.myId) hud.msg(N.call.cartBack, 1.2, 'brag'); },
  duck(m) { addDuck(m); },
  duckx(m) {
    if (m.all) { for (const d of S.ducks.values()) dropDuck(d); S.ducks.clear(); return; }
    const d = S.ducks.get(m.id);
    if (d) { if (m.by) fx.spray([d.cur.x, d.cur.y + 0.3, d.cur.z], 10, d.g ? [0xffc400, 0xffffff] : [0xffd23b, 0xff8a00, 0xffffff], 5, 0.5, 0.12, 9, 1); dropDuck(d); S.ducks.delete(m.id); }
    if (m.seat != null) S.piles[m.seat] = m.pile;
    if (m.by === G.myId) { (m.g ? sfx.bgmGold : sfx.bgmCatch)(!!m.air); hud.msg(`+${m.v} ${m.g ? N.call.gold : m.air ? N.call.duckAir : 'DUCK'}`, 0.9, 'brag'); }
  },
  slap(m) {
    if (m.seat != null) S.piles[m.seat] = m.pile;
    if (m.b === G.myId && m.n) { hud.msg(`${N.call.slapped} -${m.n}`, 1.2, 'lava'); sfx.bgmLost(); }
    else if (m.a === G.myId && m.n) hud.msg(`KNOCKED ${m.n} LOOSE`, 1, 'brag');
  },
  curse(m) { if (m.seat != null) S.piles[m.seat] = m.pile; if (m.id === G.myId) { hud.msg(`${N.call.cursed} -${m.n}`, 1.8, 'lava'); sfx.bgmCurse(); } },
  cursed(m) { if (playing() && ME.alive && Math.hypot(m.p[0] - ME.pos[0], m.p[2] - ME.pos[2]) < 10) hud.msg('CURSED DUCK INBOUND', 1.4, 'lava'); },
  boss(m) { if (S.x && S.x.k === 'boss') { S.x.hp = m.hp; S.x.max = m.max; } },
  bossdown(m) { if (S.x) { S.x.down = 1; S.x.hp = 0; } const b = BGN_NAMES_BOSS(); hud.msg(b ? b.down : N.call.bossDown, 2.6, 'brag'); sfx.bgmBossDown(); G.shake = Math.max(G.shake || 0, 1); },
  bossback(m) { if (S.x) S.x.hp = Math.max(0, (S.x.hp || 0) - (m.cut || 0)); if (playing()) hud.msg(m.w !== 'void' ? `HE SHRUGGED IT OFF. -${m.cut} ARMOUR` : m.cut ? `SPLASH! -${m.cut} ARMOUR` : 'HE FELL IN. A CRANE PUT HIM BACK', 1.6, 'brag'); },
  rig(m) { if (!playing()) return; hud.msg(m.id === G.myId ? 'YOU ARE THE BIG GUY' : 'THE BIG GUY IS BACK', 1.6, 'brag'); },
};
const BGN_NAMES_BOSS = () => (S.B && S.B.mg ? N.boss[S.B.mg.id] : null);
export function miniEv(m) { const f = EV[m.k]; if (f) f(m); }

// bumper carts: the server put you in a cart (its id + yours): climb in (primaries.js does the riding)
net.tap((m) => { if (m.t === 'cart' && kind() === 'carts' && m.r === G.myId && ME.alive && ME.ride !== m.id && Number.isInteger(m.id) && boardCart(m.id) && Number.isFinite(m.y)) { ME.yaw = m.y; ME.pitch = -0.12; } }); // (facing the way the cart does: into the middle)

// ---------------------------------------------------------------- ducks
const DISC = new THREE.CircleGeometry(1, 16).rotateX(-Math.PI / 2), RING = new THREE.RingGeometry(0.8, 1, 20).rotateX(-Math.PI / 2);
const PO = { transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -6 };
const LINE = new THREE.CylinderGeometry(0.035, 0.035, 1, 5).translate(0, 0.5, 0); // the drop line under a falling duck (so you can tell where it's going from anywhere)
const GOLD = new THREE.MeshStandardMaterial({ color: 0xffc400, metalness: 0.85, roughness: 0.22, emissive: 0x6a4a00, emissiveIntensity: 0.6 });
function addDuck(m) {
  if (!G.scene || !Array.isArray(m.p) || S.ducks.has(m.id)) return;
  const mesh = buildProjectile('duck');
  if (m.g) mesh.traverse((o) => { if (o.isMesh && o.material && o.material.color && o.material.color.getHex() === 0xffd23b) o.material = GOLD; });
  mesh.scale.setScalar(m.g ? 1.9 : 1.5);
  const line = new THREE.Mesh(LINE, new THREE.MeshBasicMaterial({ color: m.g ? 0xffc400 : 0xffe14d, transparent: true, opacity: 0.35, depthWrite: false, fog: false }));
  const disc = new THREE.Mesh(DISC, new THREE.MeshBasicMaterial({ color: 0x000000, opacity: 0.25, ...PO }));
  const ring = new THREE.Mesh(RING, new THREE.MeshBasicMaterial({ color: m.g ? 0xffc400 : 0xffe14d, opacity: 0.9, fog: false, ...PO }));
  const mark = new THREE.Group(); mark.add(disc, ring, line); mark.position.set(m.p[0], m.p[1] + 0.05, m.p[2]);
  G.scene.add(mesh, mark);
  const now = performance.now();
  S.ducks.set(m.id, { id: m.id, p: m.p, h: m.h || 0, t0: now, t1: now + (m.ms || 0), g: !!m.g, mesh, mark, disc, ring, line, spin: Math.random() * 6, cur: new THREE.Vector3(m.p[0], m.p[1] + (m.h || 0), m.p[2]) });
}
function dropDuck(d) { if (G.scene) G.scene.remove(d.mesh, d.mark); d.disc.material.dispose(); d.ring.material.dispose(); d.line.material.dispose(); }
function tickDucks(now, dt) {
  for (const d of S.ducks.values()) {
    const k = d.t1 > d.t0 ? Math.min(1, (now - d.t0) / (d.t1 - d.t0)) : 1, fall = k < 1;
    const y = d.p[1] + d.h * (1 - k) + (fall ? 0 : 0.18 + Math.sin(now * 0.004 + d.spin) * 0.06);
    d.spin += dt * (fall ? 7 : 1.4);
    d.cur.set(d.p[0], y, d.p[2]);
    d.mesh.position.copy(d.cur);
    d.mesh.rotation.set(fall ? Math.sin(d.spin) * 0.6 : 0, d.spin, fall ? Math.cos(d.spin * 0.7) * 0.5 : 0);
    const s = fall ? 0.35 + k * 0.75 : 0.9;
    d.disc.scale.setScalar(s); d.ring.scale.setScalar(s * (1.1 + Math.sin(now * 0.012) * 0.1));
    d.disc.material.opacity = fall ? 0.15 + k * 0.4 : 0.3;
    d.ring.material.opacity = fall ? 0.9 : 0.45;
    d.line.visible = fall; d.line.scale.y = Math.max(0.01, y - d.p[1]);
    d.mesh.visible = fall || now - d.t1 < BGN_MINI.ducks.floorMs - 3000 || Math.floor(now / 160) % 2 === 0; // (blinks before it goes)
  }
}

// ---------------------------------------------------------------- the HUD (only while one of these is on and you're in it)
const CSS = `
#bgmHud{position:fixed;inset:0;pointer-events:none;z-index:44;font-family:var(--font,'Comic Neue',sans-serif);color:#fff}
#bgmHud .bm-p{background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff}
.bm-boss{position:absolute;left:50%;top:76px;transform:translateX(-50%) rotate(-1deg);width:min(620px,88vw);padding:6px 14px 10px;text-align:center}
.bm-boss b{display:block;font-size:30px;line-height:1.05;color:#ffe14d;-webkit-text-stroke:1.5px #000;text-shadow:4px 4px 0 #ff00dc;letter-spacing:1px}
.bm-boss small{display:block;font-size:14px;color:#ffd6f7;font-style:italic;margin-bottom:4px}
.bm-bar{position:relative;height:22px;background:#000;border:3px solid #000;box-shadow:4px 4px 0 #000}
.bm-bar i{position:absolute;left:0;top:0;bottom:0;background:#ff3030;transition:width .2s}
.bm-bar i.lag{background:#ffe14d;transition:width .9s .25s}
.bm-bar span{position:absolute;inset:0;font-size:15px;font-weight:700;line-height:22px;-webkit-text-stroke:.5px #000}
.bm-seats{position:absolute;left:50%;top:64px;transform:translateX(-50%);display:flex;gap:10px;align-items:flex-start}
.bm-seat{position:relative;min-width:118px;padding:4px 10px 4px 16px;background:rgba(18,8,24,0.92);border:3px solid #ff4fd8;box-shadow:4px 4px 0 #000}
.bm-seat.me{box-shadow:6px 6px 0 #4fd8ff}
.bm-seat .st{position:absolute;left:0;top:0;bottom:0;width:8px}
.bm-seat b{display:block;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:130px}
.bm-seat em{display:block;white-space:nowrap;font-style:normal;font-size:22px;font-weight:700;color:#ffe14d;-webkit-text-stroke:1px #000}
.bm-seat.out{opacity:.55}.bm-seat.out em{color:#ff3030}
.bm-duck{display:inline-block;width:16px;height:12px;border-radius:8px 8px 5px 5px;background:#ffd23b;border:2px solid #000;margin-right:5px;vertical-align:1px}
.bm-team{align-self:center;padding:4px 10px;font-size:16px;font-weight:700;border:3px solid #000;box-shadow:4px 4px 0 #000;color:#000}
.bm-boost{position:absolute;left:50%;bottom:150px;transform:translateX(-50%) rotate(-1.5deg);padding:4px 12px;font-size:18px;font-weight:700;text-align:center}
.bm-boost .bm-bar{width:200px;height:14px;margin-top:3px}.bm-boost .bm-bar i{background:#4fd8ff;transition:none}
.bm-boost.ready{color:#ffe14d}
.bm-spec{position:absolute;left:50%;bottom:22%;transform:translateX(-50%);padding:6px 16px;font-size:20px;font-weight:700}
@media (max-width:640px){.bm-boss b{font-size:20px}.bm-seats{top:96px;gap:4px}.bm-seat{min-width:0;padding:2px 4px 2px 10px}.bm-seat b{font-size:11px;max-width:70px}.bm-seat em{font-size:15px}.bm-boost{bottom:150px}}`;
function ensureDom() {
  if (S.dom) return;
  const st = el('style'); st.textContent = CSS; document.head.append(st);
  S.dom = el('div'); S.dom.id = 'bgmHud'; document.body.append(S.dom);
}
function render(now) {
  ensureDom();
  const k = kind(), on = !!k && playing() && G.joined;
  S.dom.style.display = on ? '' : 'none';
  if (!on) return;
  const B = S.B, mg = B.mg, me = mySeat();
  // only rebuild when something changed (the bars are styled in place)
  const key = JSON.stringify([k, S.x.out, S.x.pool, S.x.lives, S.piles, S.x.down, mg.seats, S.out, k === 'boss' ? Math.round((S.x.hp / Math.max(1, S.x.max)) * 200) : 0]);
  if (key !== S.key) {
    S.key = key;
    S.dom.innerHTML = '';
    if (k === 'boss') {
      const nm = N.boss[mg.id] || { name: 'THE BOSS', title: '' }, pc = Math.max(0, Math.min(1, (S.x.hp || 0) / Math.max(1, S.x.max || 1)));
      const box = el('div', 'bm-boss bm-p'); box.append(el('b', null, nm.name), el('small', null, S.x.down ? nm.down : nm.title));
      const bar = el('div', 'bm-bar'), lag = el('i', 'lag'), fill = el('i'); lag.style.width = fill.style.width = `${pc * 100}%`;
      bar.append(lag, fill, el('span', null, `${Math.round(S.x.hp || 0)} / ${Math.round(S.x.max || 0)} ARMOUR`)); box.append(bar); S.dom.append(box);
    } else if (k === 'carts' || k === 'ducks') {
      const row = el('div', 'bm-seats');
      const chip = (i) => {
        const s = B.seats[i], out = k === 'carts' && S.x.out && S.x.out.includes(i), c = el('div', 'bm-seat' + (me && me.i === i ? ' me' : '') + (out ? ' out' : ''));
        const stripe = el('i', 'st'); stripe.style.background = s.color; c.append(stripe);
        const nm = el('b', null, s.name); nm.style.color = s.color; c.append(nm);
        if (k === 'ducks') { const v = el('em'); v.append(el('i', 'bm-duck'), String(S.piles[i] || 0)); c.append(v); }
        else c.append(el('em', null, out ? 'OUT' : S.x.lives && S.x.lives[i] != null ? '♥'.repeat(S.x.lives[i]) : 'STILL IN'));
        return c;
      };
      if (mg.teams && mg.sides) mg.sides.forEach((side, t) => {
        const tm = el('div', 'bm-team', k === 'carts' && S.x.pool ? `${t ? 'BLUE' : 'RED'} ${'♥'.repeat(S.x.pool[t + 1] || 0) || 'NO LIVES'}` : `${t ? 'BLUE' : 'RED'} ${side.reduce((a, i) => a + (S.piles[i] || 0), 0)}`);
        tm.style.background = t ? '#4fa8ff' : '#ff4f4f';
        if (t) row.append(tm);
        for (const i of side) row.append(chip(i));
        if (!t) row.append(tm);
      });
      else for (const i of mg.seats) row.append(chip(i));
      S.dom.append(row);
      if (k === 'carts' && !S.out) { const b = el('div', 'bm-boost bm-p'); b.append(el('div', 'bm-lbl', N.call.boost), Object.assign(el('div', 'bm-bar'), {})); b.lastChild.append(el('i')); S.dom.append(b); }
      if (k === 'carts' && S.out) S.dom.append(el('div', 'bm-spec bm-p', 'OUT. WATCHING THE CARTS'));
    }
  }
  const bb = S.dom.querySelector('.bm-boost');
  if (bb) {
    const f = Math.max(0, Math.min(1, (now - S.boostT) / CM.boostCd)), ready = f >= 1 && !!ME.ride;
    bb.classList.toggle('ready', ready); bb.style.display = ME.ride ? '' : 'none';
    bb.querySelector('.bm-lbl').textContent = ready ? `${N.call.boost} [CLICK]` : N.call.boost;
    bb.querySelector('i').style.width = `${f * 100}%`;
  }
}

// ---------------------------------------------------------------- hooks
// every frame (bgn.js's bgnFrame, board up or not)
export function miniFrame(dt) {
  const now = performance.now();
  if (S.ducks.size) tickDucks(now, dt);
  render(now);
  if (kind() === 'carts' && S.out && !ME.alive && now - S.outT > 1800) { const d = document.getElementById('dead'); if (d) d.classList.add('hidden'); }
}
// main.js mousedown: in your cart a click is a BOOST, not a slap. true = taken
export function miniMouse(e) {
  if (kind() !== 'carts' || !ME.ride || !ME.alive || e.button !== 0) return false;
  const now = performance.now();
  if (now - S.boostT < CM.boostCd) return true;
  S.boostT = now;
  const fx0 = -Math.sin(ME.rideYaw || ME.yaw), fz0 = -Math.cos(ME.rideYaw || ME.yaw);
  ME.vel[0] += fx0 * CM.boost; ME.vel[2] += fz0 * CM.boost;
  const sp = Math.hypot(ME.vel[0], ME.vel[2]), cap = CART.ride.maxSp;
  if (sp > cap) { ME.vel[0] *= cap / sp; ME.vel[2] *= cap / sp; }
  net.send({ t: 'bg', k: 'boost' });
  sfx.bgmBoost(null); G.shake = Math.max(G.shake || 0, 0.35);
  fx.smoke([ME.pos[0] - fx0, ME.pos[1] - 0.5, ME.pos[2] - fz0], 5, 0.4);
  return true;
}
// main.js's camera: out of bumper carts = a slow orbit over the box (it's always the Crate, centred on 0, 0). true = taken
export function miniCam(dt, cam) {
  if (kind() !== 'carts' || !S.out || ME.alive || performance.now() - S.outT < 1800) return false;
  S.orbit += dt * 0.16;
  cam.position.set(Math.sin(S.orbit) * 27, 21, Math.cos(S.orbit) * 27);
  cam.lookAt(0, 0, 0);
  return true;
}
// main.js's camera, in your cart: a chase cam a few metres back (you see yourself in the cart, and who's coming).
// the mannequin standing in it is you (nobody draws your own body otherwise). true = it's on
let rideLen = 0, selfCh = null;
const lookV = () => { const c = Math.cos(ME.pitch); return [-Math.sin(ME.yaw) * c, Math.sin(ME.pitch), -Math.cos(ME.yaw) * c]; };
export function miniRideCam(cam, dt) {
  const on = kind() === 'carts' && !!ME.ride && ME.alive && G.joined;
  if (!selfCh && on && G.scene) { try { selfCh = buildCharacter(G.myColor || '#ff4fd8', (G.settings && G.settings.look) || undefined).root; } catch { selfCh = buildCharacter(G.myColor || '#ff4fd8').root; } G.scene.add(selfCh); }
  if (selfCh) { selfCh.visible = on; if (on) { selfCh.position.set(ME.pos[0], ME.pos[1], ME.pos[2]); selfCh.rotation.set(0, (ME.rideYaw ?? ME.yaw) + Math.sin(performance.now() * 0.009) * 0.05, 0); } }
  if (!on) { rideLen = 0; return false; }
  const d = lookV(), e = [ME.pos[0], ME.pos[1] + 2.2, ME.pos[2]], want = 3.6;
  const hit = raycast(e, [-d[0], -d[1], -d[2]], want + 0.4, BOXES), free = hit ? Math.max(0.3, hit.t - 0.35) : want;
  rideLen = Math.min(free, rideLen + (want - rideLen) * Math.min(1, dt * 4));
  cam.position.set(e[0] - d[0] * rideLen, e[1] - d[1] * rideLen + 0.4, e[2] - d[2] * rideLen);
  return true;
}
export const miniHideVM = () => kind() === 'carts' && !!ME.ride && ME.alive;
// main.js's round line: the minigame's name and the clock (null = the usual)
export function miniRoundText(r, clock) {
  const k = kind();
  if (!k || !r || r.over || !S.B.mg || (GAMES[r.game] && GAMES[r.game].teams)) return null; // (team games: the team bar says it, miniTeamText)
  const nm = (BGN_MINIS[S.B.mg.id] || {}).name || '';
  return `${S.B.mg.sd ? N.call.sd + ' · ' : ''}${nm} · ${clock(r.left)}`;
}
// objective.js's team bar (the bosses, the big guy): the minigame, its real limit (if it has one) and the clock, not "TEAM DEATHMATCH · to 999"
export function miniTeamText(r, clock) {
  const k = kind(), def = S.B && S.B.mg && BGN_MINIS[S.B.mg.id];
  if (!k || !r || !def) return null;
  return `${def.name}${def.target && def.target < 999 ? ` · to ${r.target}` : ''}${r.over ? '' : ' · ' + clock(r.left)}`;
}
// main.js's kill feed: bumper carts' void lines. null = the usual
export function miniFeed(m, kn, kc, vn, vc) {
  if (kind() !== 'carts' || m.w !== 'void') return null;
  return m.k ? [[kn, kc], ['  [CART]  ', '#9b5cff'], [vn, vc], [`  ${N.feed.cartKo}`, '#aaa']] : [[vn, vc], [`  ${N.feed.cartSelf}`, '#aaa']];
}
// the intro card: the controls line, and the boss's name in big
export function miniCtl(def) { return N.ctl[def.ctl] || N.ctl.def; }
export function miniIntro(mg) {
  const b = N.boss[mg.id];
  if (mg.fmt !== 'boss' || !b) return null;
  const box = el('div', 'bg-bossart'), who = el('div', 'bg-sides');
  for (const i of mg.seats) { const s = S.B && S.B.seats[i]; if (!s) continue; const d = el('div', null, s.name); d.style.background = s.color; d.style.color = '#000'; who.append(d); }
  const vs = el('div', 'bg-one', 'VS'); vs.style.fontSize = '40px';
  const nm = el('div', 'rule', b.title); nm.style.color = '#ff8a8a';
  box.append(who, vs, nm);
  return box;
}
// the results card: what each seat did (boss damage + MVP, ducks, still in / out)
export function miniRes(r, i) {
  const x = r.x || {};
  if (r.id === 'bigguy' && r.sc) return i === r.one ? `${r.sc[1]} pts (kills x3)` : r.sides && r.sides[0][0] === i ? `the three: ${r.sc[0]} kills` : '';
  if (r.fmt === 'boss' && r.dmg) { const d = r.dmg.find((e) => e[0] === i); return `${d ? d[1] : 0} dmg${r.mvp === i ? ` · ${N.call.mvp}` : ''}`; }
  if (BGN_MINIS[r.id] && BGN_MINIS[r.id].game === 'bgducks' && x.pile) return `${x.pile[i] || 0} ducks`;
  if (BGN_MINIS[r.id] && BGN_MINIS[r.id].game === 'bgcarts' && x.falls) return x.out && x.out.includes(i) ? 'OUT' : x.falls[i] ? `${x.falls[i]} fall${x.falls[i] > 1 ? 's' : ''}` : 'never fell';
  return '';
}
