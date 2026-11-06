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
import { organic, organicRedraw } from './organic.js';
import { navPic, navGunPic } from './navicons.js'; // the side menu's little 3D props
import { containerPic } from './crate3d.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
let opts = {}, nowT = 0, evT = 0, lastFrame = '', serverEv = ''; // serverEv: the server's event of the day (its clock decides the vote's)

// empty an element but keep its hand-cut slab (organic.js) in place
const clearKids = (e) => { for (const c of [...e.childNodes]) if (!(c.classList && c.classList.contains('org-bg'))) c.remove(); };
const SMALL = { tex: false, bits: false, rim: 3, pad: 6, shadow: [4, 4], wob: 0.9, lumps: 2, lumpA: 1.6 };
export function initHome(o) {
  opts = o; // { start(mode, cfg), look() -> [color, look], skin(id) }
  // the menu's slabs: big play buttons, links, the hero's buttons, the strip
  for (const b of document.querySelectorAll('#scr-main .home-right .big.mode')) organic(b, { rim: 5, wet: false, veins: false, lumps: 4, lumpA: 3.2, shadow: b.classList.contains('play') ? [9, 9] : [6, 6], bandL: b.classList.contains('play') ? 0 : 12 });
  // the side menu: one plaque shape for every button, its 3D prop set in a fleshy socket (primary ones are bigger)
  for (const b of document.querySelectorAll('#scr-main .hnav')) { const prim = b.classList.contains('prim'); organic(b, { bits: false, wet: false, veins: false, rim: prim ? 4 : 3, pad: prim ? 7 : 5, shadow: prim ? [6, 6] : [4, 4], wob: 1, lumps: prim ? 3 : 2, lumpA: prim ? 2.4 : 1.6, texA: 0.06, holes: [b.querySelector('.ni')] }); }
  navIcons();
  organic(document.querySelector('#scr-main .hero-under .toy'), { ...SMALL, rim: 4, shadow: [6, 6] });
  organic($('heroGun'), { ...SMALL, rim: 4, shadow: [5, 5] });
  organic($('nameRow'), { ...SMALL, shadow: [5, 5] });
  organic($('homeStrip'), { bits: false, rim: 4, lumps: 3, shadow: [6, 6], texA: 0.08 });
  organic($('homeEvent'), { rim: 6, lumps: 4, lumpA: 3.5, shadow: [8, 8] });
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
  navIcons(); // (a new loadout or skin: the CUSTOMIZE picture follows)
  renderEvent();
  pollNow();
  clearInterval(evT);
  evT = setInterval(() => { if (homeOn()) renderEvent(true); else clearInterval(evT); }, 1000);
}
// the side menu's pictures: your own gun on CUSTOMIZE, the 3D crate on CONTAINERS, props on the rest (rendered once, cached)
function navIcons() {
  for (const s of document.querySelectorAll('#scr-main .hnav .ni')) {
    const k = s.dataset.ico, im = s.querySelector('img');
    let u = '';
    if (k === 'customize') { const lo = G.settings.loadout || {}, id = WEAPONS[lo.primary] ? lo.primary : 'ar'; u = navGunPic(id, opts.skin && opts.skin(id)); }
    else if (k === 'crates') u = containerPic('crate');
    else u = navPic(k);
    if (u && im.getAttribute('src') !== u) im.src = u;
  }
}
// other screens get the crunchy preview back
export function homeLeft() { setPreviewRes(0.5); }
// a skin model that downloaded late: put it in the hero's hands
export function refreshHero() { if (homeOn()) hero(); }

function hero() {
  const lo = G.settings.loadout || {};
  const id = WEAPONS[lo.primary] ? lo.primary : 'ar';
  const [color, look] = opts.look();
  showArmed(buildCharacter, color, look, buildWeapon(id, opts.skin(id)));
  setTimeout(resizePreview, 0);
  const g = $('heroGun');
  clearKids(g);
  const w = WEAPONS[id];
  g.append(el('small', null, 'EQUIPPED'), el('b', null, w.name));
  g.querySelector('b').style.color = w.color;
}

function renderEvent(tickOnly) {
  const ev = (GAMES[serverEv] && serverEv) || eventGame();
  const box = $('homeEvent');
  const left = 86400000 - (Date.now() % 86400000), s = Math.floor(left / 1000);
  const clock = `${String(Math.floor(s / 3600)).padStart(2, '0')}:${String(Math.floor(s / 60) % 60).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  if (tickOnly && box.dataset.ev === ev) { const c = box.querySelector('.evclock'); if (c) c.textContent = clock; return; }
  box.dataset.ev = ev;
  clearKids(box);
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
  organic(b, { ...SMALL, shadow: [5, 5] });
  b.addEventListener('click', () => {
    const maps = mapsFor(ev, MAPS, MAP_ORDER);
    const map = maps.includes(G.cfg.map) ? G.cfg.map : maps[Math.floor(Math.random() * maps.length)];
    opts.start('bots', { game: ev, map, bots: 6, diff: G.settings.diff || 'normal', hip: 'normal' });
  });
  box.append(b);
  box._org.holes = [box.querySelector('.mthumb')]; requestAnimationFrame(() => organicRedraw(box)); // redraw with the picture's socket (after layout)
}

// "now playing" strip: what the online room is on and how many people are around
async function pollNow() {
  clearTimeout(nowT);
  if (!homeOn()) return;
  const strip = $('homeStrip');
  try {
    const r = await fetch('/now', { cache: 'no-store' });
    const n = await r.json();
    if (n.ev && n.ev !== serverEv) { serverEv = n.ev; renderEvent(); }
    clearKids(strip);
    const seg = (label, val, cls) => { const s = el('span', 'seg' + (cls ? ' ' + cls : '')); s.append(el('small', null, label), el('b', null, val)); return s; };
    const game = GAMES[n.game] ? GAMES[n.game].name : 'Deathmatch', map = MAPS[n.map] ? MAPS[n.map].name : '';
    strip.append(el('i', 'live'), seg('NOW PLAYING', `${game} on ${map}`, 'np'));
    strip.append(seg('SERVER', n.region || location.host || 'local'));
    strip.append(seg('ONLINE', `${n.online} player${n.online === 1 ? '' : 's'}${n.room ? ` · ${n.room} in quick play` : ''}`));
  } catch {
    clearKids(strip);
    strip.append(el('i', 'live off'), el('span', 'seg', 'server not answering. you can still try.'));
  }
  nowT = setTimeout(pollNow, 15000);
}
