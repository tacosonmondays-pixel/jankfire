// Main menu (the "home" screen): logo up top, your character with your gun in the middle, big play buttons on the
// right, links on the left, today's EVENT card, and a "now playing" strip from the server's /now endpoint.
import { G } from './ctx.js';
import { GAMES } from '/shared/modes.js';
import { MAPS, MAP_ORDER } from '/shared/map.js';
import { WEAPONS } from '/shared/weapons.js';
import { mapsFor } from '/shared/modes.js';
import { eventGame } from '/shared/vote.js';
import { buildCharacter, buildWeapon } from './models.js';
import { showArmed, resizePreview, setPreviewRes } from './preview.js';
import { modeThumb } from './modeart.js';
import { fleshFrame } from './flesh.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
let opts = {}, nowT = 0, evT = 0, lastFrame = '';

export function initHome(o) {
  opts = o; // { start(mode, cfg), look() -> [color, look], skin(id) }
  addEventListener('resize', () => { if (homeOn()) { frame(); resizePreview(); } });
}
const homeOn = () => !$('scr-main').classList.contains('hidden') && !$('menu').classList.contains('hidden');
function frame() {
  const k = `${innerWidth}x${innerHeight}`;
  if (k === lastFrame) return;
  lastFrame = k;
  $('homeFrame').innerHTML = fleshFrame(innerWidth, innerHeight);
}

// every time the main menu shows
export function homeShown() {
  lastFrame = '';
  frame();
  $('heroSlot').append($('preview'));
  setPreviewRes(0.75);
  hero();
  renderEvent();
  pollNow();
  clearInterval(evT);
  evT = setInterval(() => { if (homeOn()) renderEvent(true); else clearInterval(evT); }, 1000);
}
// other screens get the crunchy preview back
export function homeLeft() { setPreviewRes(0.5); }

function hero() {
  const lo = G.settings.loadout || {};
  const id = WEAPONS[lo.primary] ? lo.primary : 'ar';
  const [color, look] = opts.look();
  showArmed(buildCharacter, color, look, buildWeapon(id, opts.skin(id)));
  setTimeout(resizePreview, 0);
  const g = $('heroGun');
  g.innerHTML = '';
  const w = WEAPONS[id];
  g.append(el('small', null, 'EQUIPPED'), el('b', null, w.name));
  g.querySelector('b').style.color = w.color;
}

function renderEvent(tickOnly) {
  const ev = eventGame();
  const box = $('homeEvent');
  const left = 86400000 - (Date.now() % 86400000), s = Math.floor(left / 1000);
  const clock = `${String(Math.floor(s / 3600)).padStart(2, '0')}:${String(Math.floor(s / 60) % 60).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  if (tickOnly && box.dataset.ev === ev) { const c = box.querySelector('.evclock'); if (c) c.textContent = clock; return; }
  box.dataset.ev = ev;
  box.innerHTML = '';
  const g = GAMES[ev];
  if (!g) return;
  box.append(el('span', 'evtag', "TODAY'S EVENT"));
  const row = el('div', 'evrow');
  row.append(modeThumb(ev, g.name));
  const t = el('div', 'evtxt');
  t.append(el('b', null, g.name), el('span', null, g.desc));
  row.append(t);
  box.append(row);
  const foot = el('div', 'evfoot');
  foot.append(el('span', null, 'on every end-of-match vote · ends in '), el('span', 'evclock', clock));
  box.append(foot);
  const b = el('button', 'toy small', 'PLAY IT WITH BOTS');
  b.addEventListener('click', () => {
    const maps = mapsFor(ev, MAPS, MAP_ORDER);
    const map = maps.includes(G.cfg.map) ? G.cfg.map : maps[Math.floor(Math.random() * maps.length)];
    opts.start('bots', { game: ev, map, bots: 6, diff: G.settings.diff || 'normal', hip: 'normal' });
  });
  box.append(b);
}

// "now playing" strip: what the online room is on and how many people are around
async function pollNow() {
  clearTimeout(nowT);
  if (!homeOn()) return;
  const strip = $('homeStrip');
  try {
    const r = await fetch('/now', { cache: 'no-store' });
    const n = await r.json();
    strip.innerHTML = '';
    const seg = (label, val, cls) => { const s = el('span', 'seg' + (cls ? ' ' + cls : '')); s.append(el('small', null, label), el('b', null, val)); return s; };
    const game = GAMES[n.game] ? GAMES[n.game].name : 'Deathmatch', map = MAPS[n.map] ? MAPS[n.map].name : '';
    strip.append(el('i', 'live'), seg('NOW PLAYING', `${game} on ${map}`, 'np'));
    strip.append(seg('SERVER', n.region || location.host || 'local'));
    strip.append(seg('ONLINE', `${n.online} player${n.online === 1 ? '' : 's'}${n.room ? ` · ${n.room} in quick match` : ''}`));
  } catch {
    strip.innerHTML = '';
    strip.append(el('i', 'live off'), el('span', 'seg', 'server not answering. you can still try.'));
  }
  nowT = setTimeout(pollNow, 15000);
}
