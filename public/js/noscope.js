// No-scope hype. "ns" on a sniper hit is the shooter's word, so everything here is cosmetic (the server measured the
// distance and never changes damage for it). shooter: a NO SCOPE badge by the crosshair. kill feed: a little no-scope
// icon. victim of a long one (25 m+): the full MLG treatment. headshot: fireworks spelling the shooter's name, for everyone.
import { WEAPONS } from '/shared/weapons.js';
import { G } from './ctx.js';
import { ME } from './player.js';
import { sfx } from './audio.js';
import { launchFireworks, updateFireworks } from './fireworks.js';

const NS_LONG = 25; // metres: closer than this is just a regular no-scope (server.js uses the same 25)
const KC_HOLD = 2200; // ms the victim's killcam waits for the overlay (the server gives the respawn that much longer)
const $ = (id) => document.getElementById(id);
const R = (s = 1) => (Math.random() * 2 - 1) * s;
const STICKERS = ['WOW', 'REKT', '360', 'OHHHH', 'EZ', '+100', 'GG', 'SKILL', 'WHAT', '#1', 'NO SCOPE'];
const STICK_COLS = ['#ffe14d', '#ff4fd8', '#4fd8ff', '#7dff4f', '#ff7a1a', '#ffffff'];
const validPos = (p) => Array.isArray(p) && p.length === 3 && p.every((x) => typeof x === 'number' && Number.isFinite(x) && Math.abs(x) < 1e5);
const dist = (d) => Math.max(0, Math.min(999, Math.round(Number(d) || 0)));
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

// m = { k: shooter, v: victim, d: metres, hs, kill, p: where the victim stood }. killer / victim = [name, color]
// returns how long (ms) your pending killcam should wait for the overlay, 0 = leave it alone
export function noScope(m, killer, victim) {
  const d = dist(m.d);
  let hold = 0;
  if (m.k === G.myId) badge(d, !!m.hs, !!m.kill);
  if (m.kill) feedIcon(killer[0], victim[0]);
  if (m.v === G.myId && d >= NS_LONG) { hold = m.kill && G.killcamPending ? KC_HOLD : 0; mlgOn(killer, d, !!m.kill, hold); }
  if (m.hs && validPos(m.p)) launchFireworks(m.p, killer[0], d);
  return hold;
}
// the same event inside a killcam / play of the round: just the fireworks
export function replayNoScope(m, name) { if (m.hs && validPos(m.p)) launchFireworks(m.p, name, dist(m.d), true); }

// ------------------------------------------------------------ shooter: badge by the crosshair
// HUD bits run on the wall clock like their CSS animations (the game's dt is clamped when the fps tanks)
let badgeUntil = 0;
function badge(d, hs, kill) {
  let b = $('nsBadge');
  if (!b) { b = el('div'); b.id = 'nsBadge'; $('hud').append(b); }
  b.replaceChildren(el('b', '', 'NO SCOPE'), el('span', '', `${d}m`));
  if (hs) b.append(el('i', '', 'HEADSHOT'));
  b.className = ''; void b.offsetWidth; // restart the pop
  b.className = kill ? 'on kill' : 'on';
  badgeUntil = performance.now() + 1500;
  sfx.noscope();
}

// ------------------------------------------------------------ kill feed: a crossed-out scope next to the weapon
let iconUrl = '';
function nsIcon() {
  if (iconUrl) return iconUrl;
  const c = document.createElement('canvas'); c.width = c.height = 20;
  const x = c.getContext('2d');
  x.lineWidth = 4; x.strokeStyle = '#000';
  x.beginPath(); x.arc(10, 10, 7, 0, Math.PI * 2); x.stroke();
  x.lineWidth = 2; x.strokeStyle = '#fff';
  x.beginPath(); x.arc(10, 10, 7, 0, Math.PI * 2); x.moveTo(10, 1); x.lineTo(10, 19); x.moveTo(1, 10); x.lineTo(19, 10); x.stroke();
  x.lineWidth = 4; x.strokeStyle = '#000'; x.beginPath(); x.moveTo(3, 17); x.lineTo(17, 3); x.stroke();
  x.lineWidth = 2; x.strokeStyle = '#ff3030'; x.beginPath(); x.moveTo(3, 17); x.lineTo(17, 3); x.stroke();
  return (iconUrl = c.toDataURL());
}
// the kill row is already in the feed (the kill message comes first): find the newest one that matches
function feedIcon(kn, vn) {
  const f = $('feed'), wn = `[${WEAPONS.sniper.name}]`;
  if (!f) return;
  for (const row of f.children) {
    const s = row.children;
    if (row.dataset.ns || s.length < 3 || s[0].textContent !== kn || s[2].textContent !== vn || !s[1].textContent.includes(wn)) continue;
    const im = el('img', 'nsicon'); im.src = nsIcon(); im.alt = 'no scope'; im.title = 'no scope';
    s[1].after(im);
    row.dataset.ns = '1';
    return;
  }
}

// ------------------------------------------------------------ victim: the MLG treatment
// dead: everything, ~2.5 s, over the death screen. still alive: smaller, up top and out of your crosshair, so a hacked
// "ns" flag can't be used to blind anyone
let mlg = null;
function mlgOn(killer, d, dead, hold) {
  mlgOff();
  const root = el('div', dead ? 'dead' : 'alive'); root.id = 'mlg';
  const spin = el('div', 'mlg-spin'), shake = el('div', 'mlg-shake');
  shake.append(el('div', 'mlg-txt', 'NO-SCOPED'));
  spin.append(shake);
  const by = el('div', 'mlg-by'), nm = el('b', '', killer[0]);
  nm.style.color = killer[1];
  by.append('by ', nm, ` · ${d}m`);
  root.append(el('div', 'mlg-flash'), spin, by);
  $('hud').append(root);
  // with a killcam waiting it's over (faded out) right as the killcam starts
  mlg = { root, t0: performance.now(), last: performance.now(), dur: dead ? (hold ? hold / 1000 : 2.5) : 1.5, dead, hit: 0.15, flare: 0.05, stick: 0.3, out: false };
  sfx.airhorn(!dead);
  G.shake = Math.max(G.shake, dead ? 1.3 : 0.5);
}
function mlgOff() { if (mlg) { mlg.root.remove(); mlg = null; } }
function bit(cls, x, y, life) {
  const e = el('div', cls);
  e.style.left = x + '%'; e.style.top = y + '%';
  mlg.root.append(e);
  setTimeout(() => e.remove(), life);
  return e;
}
// somewhere on screen; while you're alive, never the middle
function spot() {
  for (;;) {
    const x = 50 + R(46), y = 50 + R(44);
    if (mlg.dead || Math.abs(x - 50) > 22 || Math.abs(y - 50) > 20) return [x, y];
  }
}
function mlgTick(replaying) {
  const m = mlg;
  if (!m) return;
  const w = performance.now(), t = (w - m.t0) / 1000, dt = Math.min(0.25, (w - m.last) / 1000);
  m.last = w;
  if (replaying || (m.dead && ME.alive) || t >= m.dur) { mlgOff(); return; } // the killcam / respawn wins
  if (!m.out && t > m.dur - 0.35) { m.out = true; m.root.classList.add('out'); }
  if (m.out) return;
  if ((m.hit -= dt) <= 0) { // hitmarker spam
    m.hit = m.dead ? 0.06 + Math.random() * 0.05 : 0.13 + Math.random() * 0.06;
    const [x, y] = m.dead && Math.random() < 0.5 ? [50 + R(14), 47 + R(12)] : spot();
    const h = bit('mlg-hit' + (Math.random() < 0.3 ? ' red' : ''), x, y, 320);
    h.style.setProperty('--s', (0.7 + Math.random() * 1.1).toFixed(2));
    if (Math.random() < 0.3) sfx.headshot(); else sfx.hit();
  }
  if ((m.flare -= dt) <= 0) { // sparkles / lens flares
    m.flare = m.dead ? 0.09 + Math.random() * 0.09 : 0.25;
    const [x, y] = spot();
    const f = bit('mlg-flare', x, y, 600);
    f.style.setProperty('--h', String((Math.random() * 360) | 0));
    f.style.setProperty('--s', (0.5 + Math.random() * (m.dead ? 1.6 : 0.6)).toFixed(2));
  }
  if (m.dead && (m.stick -= dt) <= 0) { // WOW 360 REKT
    m.stick = 0.22 + Math.random() * 0.2;
    const [x, y] = spot();
    const s = bit('mlg-stk', x, y, 850);
    s.textContent = STICKERS[(Math.random() * STICKERS.length) | 0];
    s.style.setProperty('--c', STICK_COLS[(Math.random() * STICK_COLS.length) | 0]);
    s.style.setProperty('--r', ((Math.random() - 0.5) * 50).toFixed(0) + 'deg');
  }
}

// every frame, after the camera is placed. replaying = a killcam / play of the round owns the camera
export function updateNoScope(dt, cam, replaying) {
  if (!G.joined) mlgOff();
  if (badgeUntil && (performance.now() > badgeUntil || !G.joined)) { badgeUntil = 0; const b = $('nsBadge'); if (b) b.classList.remove('on'); }
  mlgTick(replaying);
  updateFireworks(dt, cam, replaying);
}
