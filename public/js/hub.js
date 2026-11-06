// The CUSTOMIZE hub: one row of tabs on top of the four dress-up screens, so they read as one place.
// LOADOUT and WEAPONS are the customize screen (customize.js) in its two modes, CHARACTER is the outfit screen,
// GRAPPLE & SPRAY is what's left of the old locker.
// each tab's picture is a little 3D render in the icon studio (icons.js studioIcon): a backpack for what you take in,
// YOUR primary (skin and all) for how it looks, a mannequin in your own look, your grapple's hook. hover wiggles it,
// the open tab is tinted (ui.css). the emoji stays if 3D can't draw
import { studioIcon, liveIcon } from './icons.js';
import { buildWeapon, buildCharacter } from './models.js';
import { hookModel, myGrapple } from './grapple.js';
import { uiPic } from './itemicons.js';
import { G } from './ctx.js';
import { WEAPONS } from '/shared/weapons.js';
import { DEFAULT_LOOK, validLook } from '/shared/looks.js';
const TABS = [['loadout', 'LOADOUT', '🎒'], ['weapons', 'WEAPONS', '🔫'], ['character', 'CHARACTER', '🧍'], ['grapple', 'GRAPPLE & SPRAY', '🪝']];
const myLook = () => validLook({ ...DEFAULT_LOOK, ...(G.settings.look || {}) }, new Set());
const PIC = {
  loadout: () => uiPic('ui_backpack', '#4fd8ff', 36),
  weapons: () => {
    const lo = G.settings.loadout || {}, id = WEAPONS[lo.primary] ? lo.primary : 'ar', sk = (G.equipped || {})[id];
    return studioIcon('hub:weapons:' + id + JSON.stringify(sk || ''), () => buildWeapon(id, sk), { w: 48, h: 36, accent: '#ff4fd8', yaw: -1.25, pitch: 0.25, roll: 0.25 });
  },
  character: () => { const lk = myLook(); return studioIcon('hub:character:' + JSON.stringify(lk), () => buildCharacter(lk.color || '#ff4fd8', lk).root, { w: 36, h: 36, accent: '#4fd8ff', yaw: 2.7, pitch: 0.12 }); },
  grapple: () => { const g = myGrapple(); return studioIcon('hub:grapple:' + g, () => hookModel(g), { w: 36, h: 36, accent: '#ffe14d', yaw: 2.2, pitch: 0.5 }); },
};
// a tab's picture (redrawn from the cache when the hub shows, new if your gun / look / grapple changed)
function setPic(b, id) {
  let im = b.querySelector('img.hub-pic');
  if (!im) { im = document.createElement('img'); im.className = 'hub-pic'; im.alt = ''; }
  if (liveIcon(im, PIC[id]) && !im.isConnected) { const i = b.querySelector('i'); if (i) i.replaceWith(im); }
}
export function hubTabs(active, show, classic) {
  const nav = document.createElement('nav');
  nav.className = 'hub-tabs';
  for (const [id, name, ico] of TABS) {
    const b = document.createElement('button');
    b.className = 'hub-tab';
    b.dataset.hub = id;
    b.innerHTML = `<i>${ico}</i>`;
    requestAnimationFrame(() => setPic(b, id)); // (after the first paint: renders aren't free)
    b.append(name);
    b.addEventListener('click', () => {
      if (id === 'loadout') show('loadout');
      else if (id === 'weapons') show('cosmetics');
      else if (id === 'character') show('character');
      else classic();
    });
    nav.append(b);
  }
  const mark = () => { const a = typeof active === 'function' ? active() : active; for (const b of nav.children) { b.classList.toggle('on', b.dataset.hub === a); if (b.querySelector('img.hub-pic')) setPic(b, b.dataset.hub); } };
  mark();
  nav.mark = mark;
  return nav;
}
