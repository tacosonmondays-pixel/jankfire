// BATTLE ISLAND on the client: the squad panel (names, HP, down + bleed-out), squadmate markers in the world, crawling
// when you're down, the hold-F revive prompt and bar, downed people lying on the floor, squad callouts and the squad
// end screen. The server decides everything (server/island.js); this draws it and asks. Jank Royale's client
// (royale.js) still does the blimp, loot, zone and spectating.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { ME, C as PC } from './player.js';
import { W, modeFriends } from './weapons.js';
import { K } from './keys.js';
import { BOXES } from '/shared/map.js';
import { movePlayer } from '/shared/physics.js';
import { WEAPONS } from '/shared/weapons.js';
import { ISLE, ST, squadOf } from '/shared/island.js';
import { brOn, brState } from './royale.js';
import { HEROES, HERO_IDS, heroName, heroCap } from '/shared/heroes.js';
import { mechDeployBlock } from './mech.js';
import { eye } from './player.js';
import { raycast } from '/shared/physics.js';

const $ = (id) => document.getElementById(id);
const I = { on: false, sq: new Map(), down: new Set(), rows: [], rv: new Map(), mine: 0, me: false, bleed: 0, bleedT: 0, mk: new Map(), wasDown: new Set(), hero: new Map(), mm: 0, mmOut: 0, mmT: 0 };
export const isleOn = () => I.on;
export const isleDown = () => I.on && I.me && ME.alive; // (main.js: hands off everything)
modeFriends.push((r) => I.on && !!I.mine && I.sq.get(r.id) === I.mine);
G.isleCellOk = () => I.on && I.mm < ISLE.meter.max && !I.mmOut; // (royale.js: walk over an energy cell to grab it) // your squad: see-through for your bullets, never aim-assisted

// ------------------------------------------------------------ css + hud
const CSS = `
#isleSq { position: absolute; left: 18px; top: 74px; display: flex; flex-direction: column; gap: 6px; font-family: var(--font); pointer-events: none; }
#isleSq .ih { font: bold 15px var(--font); color: var(--c); text-shadow: 2px 2px 0 #000; letter-spacing: 1px; transform: rotate(-1.5deg); }
#isleSq .ir { position: relative; width: 210px; background: rgba(18,8,24,0.92); border: 3px solid var(--c); box-shadow: 4px 4px 0 #4fd8ff; padding: 3px 8px 6px; color: #fff; transform: rotate(-0.8deg); }
#isleSq .ir:nth-child(odd) { transform: rotate(0.7deg); }
#isleSq .ir b { display: block; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
#isleSq .ir i { position: absolute; right: 7px; top: 3px; font: bold 13px var(--font); font-style: normal; color: #ffe14d; }
#isleSq .bar { height: 9px; border: 2px solid #fff; background: rgba(0,0,0,0.55); margin-top: 2px; }
#isleSq .bar div { height: 100%; background: #7dff4f; }
#isleSq .ir.dn { border-color: #ff3030; animation: isleBlink 0.6s steps(2) infinite; }
#isleSq .ir.dn .bar div { background: repeating-linear-gradient(90deg, #ff3030 0 10px, #ff00dc 10px 13px); }
#isleSq .ir.out { opacity: 0.55; border-color: #555; box-shadow: 4px 4px 0 #000; } #isleSq .ir.out b { text-decoration: line-through; color: #999; }
#isleSq .ir.me b { color: #ffe14d; }
@keyframes isleBlink { 50% { box-shadow: 4px 4px 0 #ff3030; } }
.isleMk { position: absolute; transform: translate(-50%, -100%); font: bold 13px var(--font); color: #fff; text-shadow: 1px 1px 0 #000, -1px -1px 0 #000; text-align: center; pointer-events: none; white-space: nowrap; }
.isleMk .tri { width: 0; height: 0; margin: 2px auto 0; border-left: 9px solid transparent; border-right: 9px solid transparent; border-top: 13px solid var(--c); filter: drop-shadow(2px 2px 0 #000); }
.isleMk.dn .tri { display: none; }
.isleMk .plus { display: none; margin: 0 auto; width: 30px; height: 30px; background: #ff3030; border: 3px solid #fff; box-shadow: 3px 3px 0 #000; color: #fff; font: bold 26px/26px var(--font); animation: isleBlink 0.6s steps(2) infinite; transform: rotate(-4deg); }
.isleMk.dn .plus { display: block; }
.isleMk small { display: block; font-size: 11px; color: #ffe14d; }
#isleDown { position: absolute; inset: 0; pointer-events: none; display: none; box-shadow: inset 0 0 220px 60px rgba(255,0,40,0.55); }
#isleDown .t { position: absolute; left: 50%; top: 26%; transform: translateX(-50%) rotate(-2deg); text-align: center; font: bold 52px var(--font); color: #ff3030; text-shadow: 4px 4px 0 #000, 7px 7px 0 #ff00dc; white-space: nowrap; }
#isleDown .t small { display: block; font-size: 19px; color: #fff; text-shadow: 2px 2px 0 #000; }
#isleDown .bb { position: absolute; left: 50%; top: 47%; width: 320px; height: 16px; transform: translateX(-50%) rotate(1deg); border: 3px solid #fff; background: rgba(0,0,0,0.6); box-shadow: 5px 5px 0 #000; }
#isleDown .bb div { height: 100%; background: repeating-linear-gradient(90deg, #ff3030 0 14px, #ff00dc 14px 18px); }
body.isle-down #crosshair, body.isle-down #hotbar, body.isle-down #ammo, body.isle-down #brHook, body.isle-down #brPrompt { visibility: hidden; }
#isleRv { position: absolute; left: 50%; top: 66%; transform: translateX(-50%) rotate(-1deg); display: none; font: bold 20px var(--font); color: #fff; background: rgba(18,8,24,0.92); border: 3px solid #7dff4f; box-shadow: 5px 5px 0 #000; padding: 4px 14px 8px; white-space: nowrap; text-align: center; }
#isleRv kbd { background: #ffe14d; color: #000; border: 2px solid #000; padding: 0 6px; margin-right: 8px; font: bold 16px var(--font); }
#isleRv .bar { height: 10px; border: 2px solid #fff; background: rgba(0,0,0,0.6); margin-top: 5px; display: none; }
#isleRv .bar div { height: 100%; background: #7dff4f; width: 0; }
#isleMm { position: absolute; left: 50%; bottom: 100px; width: 330px; transform: translateX(-50%) rotate(-1deg); font: bold 14px var(--font); color: #fff; text-shadow: 1px 1px 0 #000; pointer-events: none; }
#isleMm .row { display: flex; justify-content: space-between; margin-bottom: 2px; } #isleMm .row b { color: var(--hc, #4fd8ff); letter-spacing: 1px; }
#isleMm .bar { height: 14px; border: 3px solid #fff; background: rgba(18,8,24,0.85); box-shadow: 4px 4px 0 #000; }
#isleMm .bar div { height: 100%; width: 0; background: repeating-linear-gradient(90deg, #ffe14d 0 16px, #ffb000 16px 19px); }
#isleMm.ready .bar { border-color: #ffe14d; animation: isleReady 0.5s steps(2) infinite; } #isleMm.ready .bar div { background: repeating-linear-gradient(90deg, #ff4fd8 0 16px, #ffe14d 16px 22px); }
#isleMm.out .bar div { background: #555; } #isleMm .key { color: #ffe14d; }
@keyframes isleReady { 50% { box-shadow: 4px 4px 0 #ff00dc; transform: scale(1.03); } }
#isleHero { position: absolute; left: 50%; bottom: 120px; transform: translateX(-50%) rotate(0.6deg); display: none; background: rgba(18,8,24,0.92); border: 4px solid #ff4fd8; box-shadow: 8px 8px 0 #4fd8ff; padding: 8px 14px 12px; font-family: var(--font); color: #fff; text-align: center; pointer-events: none; }
#isleHero h3 { margin: 0 0 6px; font-size: 24px; color: #ffe14d; text-shadow: 3px 3px 0 #ff00dc; letter-spacing: 2px; }
#isleHero .cards { display: flex; gap: 12px; }
#isleHero .hc { position: relative; width: 190px; padding: 6px 8px 8px; border: 3px solid var(--c); background: rgba(255,255,255,0.05); box-shadow: 4px 4px 0 #000; text-align: left; }
#isleHero .hc.on { background: var(--c); color: #000; transform: rotate(-1.5deg) scale(1.04); text-shadow: none; }
#isleHero .hc.taken { opacity: 0.45; border-style: dashed; }
#isleHero .hc b { display: block; font-size: 19px; } #isleHero .hc i { font-style: normal; font-size: 12px; display: block; opacity: 0.85; } #isleHero .hc small { display: block; font-size: 12px; margin-top: 3px; }
#isleHero .hc kbd { position: absolute; right: -6px; top: -10px; background: #ffe14d; color: #000; border: 2px solid #000; font: bold 14px var(--font); padding: 0 6px; }
#isleHero .hint { font-size: 12px; color: #ccc; margin-top: 6px; }
#isleSq .ir em { display: block; font-style: normal; font-size: 11px; color: var(--hc, #ccc); letter-spacing: 1px; margin-top: -2px; }
#isleBig { position: absolute; left: 50%; top: 17%; transform: translateX(-50%) rotate(-2deg); display: none; text-align: center; white-space: nowrap; pointer-events: none; font: bold 54px var(--font); color: #ffe14d; text-shadow: 4px 4px 0 #ff00dc, 7px 7px 0 #000; }
#isleBig small { display: block; font-size: 20px; color: #fff; text-shadow: 2px 2px 0 #000; margin-top: 2px; }
#isleBig.pop { animation: islePop 0.35s ease-out; } @keyframes islePop { 0% { transform: translateX(-50%) rotate(-2deg) scale(1.6); } 100% { transform: translateX(-50%) rotate(-2deg) scale(1); } }
#roundEnd .isle-sq { margin-top: 4px; }
@media (max-height: 520px) { #isleSq { transform: scale(0.72); transform-origin: top left; top: 60px; } #isleMm { bottom: 78px; width: 240px; font-size: 12px; } #isleBig { font-size: 38px; } #isleHero { transform: translateX(-50%) scale(0.8); bottom: 90px; } } /* (small windows: nothing on top of each other) */ #roundEnd .isle-sq b { color: var(--c); }
`;
let el = null;
function ensure() {
  if (el) return el;
  const s = document.createElement('style'); s.textContent = CSS; document.head.append(s);
  const h = $('hud'), mk = (id, html = '') => { const d = document.createElement('div'); d.id = id; d.innerHTML = html; h.append(d); return d; };
  el = { sq: mk('isleSq'), down: mk('isleDown', '<div class="t"></div><div class="bb"><div></div></div>'), rv: mk('isleRv', '<span></span><div class="bar"><div></div></div>'), marks: mk('isleMarks'),
    mm: mk('isleMm', '<div class="row"><b></b><span></span></div><div class="bar"><div></div></div>'), hero: mk('isleHero'), big: mk('isleBig') };
  return el;
}
function show(v) {
  ensure();
  el.sq.style.display = v ? '' : 'none';
  el.mm.style.display = v ? '' : 'none';
  if (!v) { el.big.style.display = 'none'; el.hero.style.display = 'none'; el.down.style.display = 'none'; el.rv.style.display = 'none'; for (const m of I.mk.values()) m.remove(); I.mk.clear(); document.body.classList.remove('isle-down'); }
}
// the island's own big callouts (MECH READY, squad wiped, the win): its own element, so a district name or a royale
// twist on the shared one can't wipe them
let bigUntil = 0;
function isleBig(text, sub, secs) { ensure(); el.big.innerHTML = `${text}${sub ? '<small></small>' : ''}`; if (sub) el.big.querySelector('small').textContent = sub; el.big.style.display = 'block'; el.big.classList.remove('pop'); void el.big.offsetWidth; el.big.classList.add('pop'); bigUntil = performance.now() + secs * 1000; }
const nameOf = (id) => (id === G.myId ? G.myName : (G.names.get(id) || {}).name || '???');
const colOf = (id) => (id === G.myId ? G.myColor : (G.names.get(id) || {}).color || '#fff');

// ------------------------------------------------------------ net
function start(m) {
  const first = !I.on;
  I.on = true; I.sq = new Map(m.l); I.mine = I.sq.get(G.myId) || 0; I.hero = new Map(m.hero || []);
  if (first) { I.mm = 0; I.mmOut = 0; }
  I.down = new Set(m.dn || []); I.rv.clear(); I.me = false; I.rows = [];
  show(true);
  if (I.mine && first) { const S = squadOf(I.mine); setTimeout(() => { if (I.on) hud.chat(null, null, `you're in ${S.name}. stick together: hold ${K.label('use')} on a downed squadmate to pick them up`); }, 600); }
}
function stop() { if (!I.on) return; I.on = false; I.sq.clear(); I.down.clear(); I.me = false; I.mine = 0; for (const id of I.wasDown) standUp(G.remotes.get(id)); I.wasDown.clear(); show(false); }
export function isleReset() { stop(); }
net.on('isle', (m) => {
  if (m.k === 'sq') { start(m); return; }
  if (!I.on) return;
  const me = m.id === G.myId, mate = I.sq.get(m.id) === I.mine;
  if (m.k === 'hero') { if (m.id && m.h) I.hero.set(m.id, m.h); if (me && m.no) { hud.msg(m.why ? m.why.toUpperCase() : 'TAKEN', 1.4); sfx.empty(); } else if (me) sfx.cash(); return; }
  if (m.k === 'mm') { // your mech meter (the server's): MECH READY when it fills
    const was = I.mm;
    I.mm = m.v; I.mmOut = m.out; if (m.h) I.hero.set(G.myId, m.h);
    if (was < ISLE.meter.max && m.v >= ISLE.meter.max) { isleBig('MECH READY', `${heroName(I.hero.get(G.myId))} is waiting · press ${K.label('streak1')} where you want it`, 3.5); sfx.choir(); G.shake = Math.max(G.shake || 0, 0.5); }
    else if (m.v > was + 12 && !m.out) { hud.msg(`+${Math.round(m.v - was)}% MECH`, 0.8, 'brag'); }
    return;
  }
  if (m.k === 'call') { hud.feed([[nameOf(m.id), colOf(m.id)], ['  called in  ', '#ffe14d'], [heroName(m.h), (HEROES[m.h] || {}).color || '#fff']]); if (me) hud.msg(`${heroName(m.h)} INBOUND`, 1.6, 'brag'); return; }
  if (m.k === 'st') { I.rows = m.m; const r = m.m.find((x) => x[0] === G.myId); if (r && r[2] === ST.DOWN) { I.bleed = r[3] * 100; I.bleedT = performance.now(); } return; }
  if (m.k === 'down') {
    I.down.add(m.id);
    const w = WEAPONS[m.w];
    hud.feed([[nameOf(m.by) && m.by ? nameOf(m.by) : '', colOf(m.by)], [m.by ? `  [${w ? w.name : m.w}]  ` : '', w ? w.color : '#aaa'], [nameOf(m.id), colOf(m.id)], ['  KNOCKED', '#ff3030']].filter((p) => p[0]));
    if (me) {
      I.me = true; I.bleed = ISLE.down.bleed * 1000; I.bleedT = performance.now();
      const R = brState(); if (R.me) R.me.fly = null; // (knocked out of the sky: you land as a crawler, no umbrella)
      W.held = false; ME.hook = null; G.shake = Math.max(G.shake || 0, 1);
      sfx.crunch(); hud.msg('', 0);
    } else if (m.by === G.myId) { hud.msg('KNOCKED!', 1.2, 'brag'); sfx.kill(); }
    else if (mate) { hud.msg(`${nameOf(m.id).toUpperCase()} IS DOWN`, 1.6, 'brag'); sfx.oob(false); }
  } else if (m.k === 'up') {
    I.down.delete(m.id); I.rv.delete(m.id);
    standUp(G.remotes.get(m.id));
    if (me) { I.me = false; hud.msg('BACK ON YOUR FEET', 1.6, 'brag'); sfx.heal(); }
    else if (m.by === G.myId) { hud.msg(`PICKED UP ${nameOf(m.id).toUpperCase()}`, 1.4, 'brag'); sfx.cash(); }
    if (m.by) hud.feed([[nameOf(m.by), colOf(m.by)], ['  picked up  ', '#7dff4f'], [nameOf(m.id), colOf(m.id)]]);
    const r = G.remotes.get(m.id), p = r ? r.pos : me ? ME.pos : null;
    if (p) fx.ring([p[0], p[1] + 0.3, p[2]], 1.8, 0x7dff4f);
  } else if (m.k === 'dead') { I.down.delete(m.id); I.rv.delete(m.id); if (me) I.me = false; standUp(G.remotes.get(m.id)); }
  else if (m.k === 'rv') I.rv.set(m.id, { by: m.by, t0: performance.now(), ms: m.ms });
  else if (m.k === 'rvx') { I.rv.delete(m.id); if (m.by === G.myId && m.why !== 'released') hud.msg(m.why === 'shot' ? 'REVIVE CANCELLED: YOU SHOT' : 'REVIVE CANCELLED', 0.8); }
  else if (m.k === 'fix') { if (Array.isArray(m.p) && m.p.length === 3) { ME.pos[0] = m.p[0]; ME.pos[1] = m.p[1]; ME.pos[2] = m.p[2]; ME.vel = [0, Math.min(0, ME.vel[1]), 0]; } }
  else if (m.k === 'sqout') {
    const S = squadOf(m.sq), mine = m.sq === I.mine;
    hud.feed([[S.name, S.color], [`  WIPED  #${m.place}`, '#ff3030']]);
    if (mine) setTimeout(() => { if (I.on) isleBig('SQUAD WIPED', `${S.name} finished #${m.place} · click to watch someone else`, 4); }, 300);
    else hud.chat(null, null, `${S.name} is out (#${m.place}). ${m.left} squad${m.left === 1 ? '' : 's'} left`);
  } else if (m.k === 'win') {
    const S = squadOf(m.sq);
    const names = (m.ids || []).map(nameOf).join(', ');
    if (m.sq && m.sq === I.mine) { isleBig('LAST SQUAD STANDING', `${S.name} took the island: ${names}`, 6); sfx.choir(); sfx.kill(); }
    else if (m.sq) isleBig(`${S.name} WIN`, `last squad standing: ${names}`, 5);
    else isleBig('NOBODY WINS', 'the zone got everyone', 4);
  }
});

// ------------------------------------------------------------ you're down: crawl, hands off everything
// player.js stepPlayer: true = moved you here
G.isleStep = (dt, inp, now) => {
  if (!I.on || !I.me || !ME.alive) return false;
  const v = ME.vel, fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * st, wz = -c * fw - s * st;
  const wl = Math.hypot(wx, wz); if (wl) { wx /= wl; wz /= wl; }
  ME.hook = null; ME.sliding = false; ME.crouching = true; ME.sprinting = false; ME.jumpBuf = 0;
  if (ME.onGround) { const k = Math.min(1, dt * 6); v[0] += (wx * ISLE.down.crawl - v[0]) * k; v[2] += (wz * ISLE.down.crawl - v[2]) * k; }
  v[1] -= PC.grav * dt;
  ME.eyeH += (0.55 - ME.eyeH) * Math.min(1, dt * 8);
  const res = movePlayer(ME.pos, v, dt, BOXES, ME.onGround);
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (wl && ME.onGround) G.shake = Math.max(G.shake || 0, 0.06 + Math.abs(Math.sin(now * 0.008)) * 0.05); // dragging yourself along
  return true;
};
const DOWN_KEYS = ['fire', 'aim', 'grapple', 'item', 'dash', 'spray', 'streak1', 'streak2', 'streak3', 'slot1', 'slot2', 'slot3', 'slot4', 'lastSlot', 'reload', 'jump', 'crouch', 'scythe', 'use', 'parry'];
// the blimp's hero pick keys: your 1-4 (weapon slots, rebindable), then plain 5-9 for heroes 5+ (no slot action there)
const HERO_SLOTS = ['slot1', 'slot2', 'slot3', 'slot4'];
function heroKeyAt(e) { const k = HERO_SLOTS.findIndex((a) => K.matches(a, e)); if (k >= 0) return k; const d = /^(?:Digit|Numpad)([5-9])$/.exec(e.code || ''); return d ? Number(d[1]) - 1 : -1; }
const heroKeyLabel = (i) => (i < HERO_SLOTS.length ? K.label(HERO_SLOTS[i]) : String(i + 1));
// main.js pressed(): true = swallowed. down: nothing but walking, looking, chat and the menu. up next to a downed
// squadmate: the use key picks them up (before royale.js grabs it for loot)
export function isleKey(e, startUse) {
  if (!I.on || !ME.alive) return false;
  if (I.me) return DOWN_KEYS.some((a) => K.matches(a, e));
  if (K.matches('use', e) && !e.repeat && reviveTarget()) { startUse(); return true; }
  const R = brState();
  if (R.me && R.me.inBlimp) { const k = heroKeyAt(e); if (k >= 0 && HERO_IDS[k]) { if (!e.repeat) net.send({ t: 'hero', h: HERO_IDS[k] }); return true; } } // the hero pick, on the blimp
  if (['streak1', 'streak2', 'streak3'].some((a) => K.matches(a, e))) { if (!e.repeat) callMech(); return true; } // the streak key: your mech
  return false;
}
// the streak key at 100%: MECH DROP's own marker where you aim (mech.js checks it first; the server has the last word)
function callMech() {
  const R = brState();
  if (R.me && (R.me.inBlimp || R.me.fly)) return;
  if (I.mmOut) { hud.msg('YOUR MECH IS ALREADY OUT', 1.2); sfx.empty(); return; }
  if (I.mm < ISLE.meter.max) { hud.msg(`MECH METER ${Math.floor(I.mm)}%`, 1.2); sfx.empty(); return; }
  const e = eye(), cp = Math.cos(ME.pitch), d = [-Math.sin(ME.yaw) * cp, Math.sin(ME.pitch), -Math.cos(ME.yaw) * cp];
  const h = raycast(e, d, 300, BOXES), at = h ? h.point : [e[0] + d[0] * 60, e[1] + d[1] * 60, e[2] + d[2] * 60];
  const hr = I.hero.get(G.myId);
  if (mechDeployBlock('mechdrop', at, hr && HEROES[hr] ? HEROES[hr].frame : 'paperplane')) return;
  net.send({ t: 'deploy', r: 'mechdrop', at: at.map((x) => Math.round(x * 100) / 100) });
}
function reviveTarget() {
  if (I.me || !I.mine) return null;
  let best = null, bd = ISLE.revive.r + 0.2;
  for (const id of I.down) {
    if (I.sq.get(id) !== I.mine) continue;
    const r = G.remotes.get(id);
    if (!r || !r.alive) continue;
    const d = Math.hypot(r.pos[0] - ME.pos[0], r.pos[2] - ME.pos[2]);
    if (d < bd && Math.abs(r.pos[1] - ME.pos[1]) < ISLE.revive.dy) { bd = d; best = r; }
  }
  return best;
}

// ------------------------------------------------------------ downed people lie on the floor and drag themselves along
const DN = { tx: -1, tz: 0 }; // face down, head first (remote.js napPose: the front)
function standUp(r) { if (!r || !r.ch) return; const b = r.ch.body; b.rotation.x = 0; b.rotation.z = 0; b.position.y = 0; }
function downPose(r, now) {
  const ch = r.ch, mv = Math.hypot(r.vel ? r.vel[0] : 0, r.vel ? r.vel[2] : 0) > 0.3;
  r.napPose(DN, 1, Math.PI / 2 - 0.12, 0.32 + Math.sin(now * 0.004) * 0.015);
  const k = mv ? Math.sin(now * 0.009) : Math.sin(now * 0.002) * 0.15; // reaching forward, one arm then the other
  ch.arm.rotation.x = 1.35 + k * 0.45; ch.armL.rotation.x = 1.35 - k * 0.45; // (0 = straight ahead of the chest: on your belly that's the floor, so up the body = along the floor past your head)
  ch.legL.rotation.x = 0.1 + k * 0.25; ch.legR.rotation.x = 0.1 - k * 0.25;
}

// ------------------------------------------------------------ every frame (main.js, after the remotes move)
const tv = new THREE.Vector3();
export function isleFrame(dt, now) {
  if (!I.on) return;
  if (!brOn()) { stop(); return; } // (the royale ended or switched off)
  ensure();
  if (bigUntil && now > bigUntil) { el.big.style.display = 'none'; bigUntil = 0; }
  for (const id of I.down) { const r = G.remotes.get(id); if (r && r.alive && r.ch && r.ch.root.visible) { downPose(r, now); I.wasDown.add(id); } }
  for (const id of I.wasDown) if (!I.down.has(id)) { standUp(G.remotes.get(id)); I.wasDown.delete(id); }
  // me down
  document.body.classList.toggle('isle-down', I.me && ME.alive);
  el.down.style.display = I.me && ME.alive ? 'block' : 'none';
  if (I.me && ME.alive) {
    const left = Math.max(0, I.bleed - (now - I.bleedT)), being = I.rv.get(G.myId);
    el.down.querySelector('.t').innerHTML = `YOU'RE DOWN<small>${being ? `${nameOf(being.by)} is picking you up. hang in there` : `crawl to your squad · ${Math.ceil(left / 1000)} s till you bleed out`}</small>`;
    const bar = el.down.querySelector('.bb div');
    bar.style.width = `${being ? Math.min(100, (now - being.t0) / being.ms * 100) : Math.min(100, left / (ISLE.down.bleed * 10))}%`;
    bar.style.background = being ? '#7dff4f' : ''; // green: someone's on it
  }
  // the revive prompt / bar
  const mine = [...I.rv].find(([, v]) => v.by === G.myId), tgt = !mine && ME.alive && !I.me ? reviveTarget() : null;
  if (mine || tgt) {
    const nm = nameOf(mine ? mine[0] : tgt.id);
    el.rv.style.display = 'block';
    el.rv.querySelector('span').innerHTML = mine ? `PICKING UP <b></b>... keep holding ${K.label('use')}` : `<kbd>${K.label('use')}</kbd>HOLD TO PICK UP <b></b>`;
    el.rv.querySelector('b').textContent = nm.toUpperCase();
    el.rv.querySelector('.bar').style.display = mine ? 'block' : 'none';
    if (mine) el.rv.querySelector('.bar div').style.width = `${Math.min(100, (now - mine[1].t0) / mine[1].ms * 100)}%`;
  } else el.rv.style.display = 'none';
  squadPanel(now);
  meterHud(now);
  markers(now);
}
let panelT = 0;
function squadPanel(now) {
  if (now < panelT || !I.mine) return;
  panelT = now + 120;
  const S = squadOf(I.mine), rows = I.rows.length ? I.rows : [...I.sq].filter(([, s]) => s === I.mine).map(([id]) => [id, 100, ST.UP, 0, 0]);
  let h = `<div class="ih" style="--c:${S.color}">${S.name}</div>`;
  for (const [id, hp, st, left] of rows) {
    const cls = st === ST.DOWN ? 'dn' : st === ST.OUT ? 'out' : '', w = st === ST.DOWN ? Math.min(100, left * 10 / ISLE.down.bleed) : st === ST.OUT ? 0 : Math.min(100, hp);
    const tag = st === ST.DOWN ? `DOWN ${Math.ceil(left / 10)}s` : st === ST.OUT ? 'OUT' : st === ST.SKY ? 'IN THE SKY' : `${hp}`;
    const hr = I.hero.get(id);
    h += `<div class="ir ${cls}${id === G.myId ? ' me' : ''}" style="--c:${S.color};--hc:${hr && HEROES[hr] ? HEROES[hr].color : '#ccc'}"><b>${esc(nameOf(id))}</b>${hr ? `<em>${heroName(hr)}</em>` : ''}<i>${tag}</i><div class="bar"><div style="width:${w}%"></div></div></div>`;
  }
  el.sq.innerHTML = h;
}
// the mech meter under your crosshair, and the hero pick while you're still on the blimp
let heroKey = '';
function meterHud(now) {
  const R = brState(), sky = R.me && R.me.inBlimp, hr = I.hero.get(G.myId);
  el.mm.style.display = ME.alive && !sky && !I.me ? '' : 'none';
  el.mm.classList.toggle('ready', I.mm >= ISLE.meter.max && !I.mmOut);
  el.mm.classList.toggle('out', !!I.mmOut);
  el.mm.style.setProperty('--hc', hr && HEROES[hr] ? HEROES[hr].color : '#4fd8ff');
  el.mm.querySelector('b').textContent = `MECH · ${heroName(hr)}`;
  el.mm.querySelector('span').innerHTML = I.mmOut ? 'OUT THERE' : I.mm >= ISLE.meter.max ? `READY · <span class="key">${K.label('streak1')}</span>` : `${Math.floor(I.mm)}%`;
  el.mm.querySelector('.bar div').style.width = `${I.mmOut ? 100 : Math.min(100, I.mm)}%`;
  el.hero.style.display = sky && ME.alive && I.mine ? 'block' : 'none';
  if (!sky) return;
  const mates = [...I.sq].filter(([id, s]) => s === I.mine && id !== G.myId).map(([id]) => [id, I.hero.get(id)]);
  const key = hr + '|' + mates.map((m) => m.join(':')).join(',');
  if (key === heroKey) return;
  heroKey = key;
  const size = mates.length + 1, cap = heroCap(size);
  let h = '<h3>PICK YOUR MECH</h3><div class="cards">';
  HERO_IDS.forEach((id, i) => {
    const by = mates.filter((m) => m[1] === id), taken = id !== hr && by.length >= cap, H = HEROES[id];
    h += `<div class="hc${id === hr ? ' on' : ''}${taken ? ' taken' : ''}" style="--c:${H.color}"><kbd>${heroKeyLabel(i)}</kbd><b>${heroName(id)}</b><i>${H.role}</i><small>${taken ? `taken: ${by.map((m) => esc(nameOf(m[0]))).join(', ')}` : H.blurb}</small></div>`;
  });
  el.hero.innerHTML = h + `</div><div class="hint">no doubles in a squad · fill your meter on the island, then ${K.label('streak1')} drops it on your crosshair</div>`;
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
// squadmates in the world: a squad-coloured arrow with name + distance over their head, a big red + when they're down
function markers(now) {
  const cam = G.camera, live = new Set();
  if (!cam || !I.mine) return;
  const W2 = innerWidth / 2, H2 = innerHeight / 2, col = squadOf(I.mine).color;
  for (const [id, s] of I.sq) {
    if (s !== I.mine || id === G.myId) continue;
    const r = G.remotes.get(id);
    if (!r || !r.alive || !r.ch) continue;
    const dn = I.down.has(id);
    tv.set(r.pos[0], r.pos[1] + (dn ? 1.1 : 2.75), r.pos[2]).project(cam);
    if (tv.z > 1 || Math.abs(tv.x) > 1.05 || Math.abs(tv.y) > 1.05) continue;
    live.add(id);
    let m = I.mk.get(id);
    if (!m) { m = document.createElement('div'); m.className = 'isleMk'; m.innerHTML = '<div class="plus">+</div><small></small><div class="tri"></div>'; el.marks.append(m); I.mk.set(id, m); }
    m.style.setProperty('--c', col);
    m.classList.toggle('dn', dn);
    m.style.left = `${W2 + tv.x * W2}px`; m.style.top = `${H2 - tv.y * H2}px`;
    const d = Math.hypot(r.pos[0] - ME.pos[0], r.pos[2] - ME.pos[2]);
    m.querySelector('small').textContent = dn ? (I.rv.has(id) ? 'GETTING UP' : `DOWN · ${Math.round(d)} m`) : `${Math.round(d)} m`;
  }
  for (const [id, m] of I.mk) if (!live.has(id)) { m.remove(); I.mk.delete(id); }
}

// ------------------------------------------------------------ the end: squads by place (main.js, after brRoundEnd)
export function isleRoundEnd(m, box) {
  if (!m.isle || !m.isle.sq) return;
  const h = box.querySelector('h3');
  const won = m.isle.win && m.isle.win === I.mine;
  if (h && m.isle.win) { const S = squadOf(m.isle.win); h.textContent = won ? `${S.name} WIN (YOU)` : `${S.name} WIN`; h.style.color = S.color; }
  for (const row of [...box.children]) if (row.tagName !== 'H3') row.remove();
  for (const [sq, place, ids] of m.isle.sq.slice().sort((a, b) => (a[1] || 99) - (b[1] || 99))) {
    const S = squadOf(sq), d = document.createElement('div');
    d.className = 'isle-sq'; d.style.setProperty('--c', S.color);
    d.innerHTML = `<b>#${place || '?'} ${S.name}</b> · <span></span>`;
    d.querySelector('span').textContent = ids.map(nameOf).join(', ');
    if (sq === I.mine) d.style.color = '#ffe14d';
    box.append(d);
  }
}
export const isleWon = (m) => (m && m.isle && m.isle.win ? m.isle.win === I.mine : null); // (endscreen.js: your squad won)
export const isleState = () => I; // (tests + the console)
export { isleBig }; // (screenshot scripts: the callout on a slow test browser)
