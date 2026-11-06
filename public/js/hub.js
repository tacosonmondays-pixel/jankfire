// The CUSTOMIZE hub: one row of tabs on top of the four dress-up screens, so they read as one place.
// LOADOUT and WEAPONS are the customize screen (customize.js) in its two modes, CHARACTER is the outfit screen,
// GRAPPLE & SPRAY is what's left of the old locker.
// each tab's picture is a little 3D render in the icon studio (icons.js): a frag for what you take in, a gun for how it
// looks, a mannequin, the grapple hook. the emoji stays if 3D can't draw
import { studioIcon, liveIcon, itemIcon } from './icons.js';
import { buildWeapon, buildCharacter } from './models.js';
import { hookModel } from './grapple.js';
const TABS = [['loadout', 'LOADOUT', '🎒'], ['weapons', 'WEAPONS', '🔫'], ['character', 'CHARACTER', '🧍'], ['grapple', 'GRAPPLE & SPRAY', '🪝']];
const PIC = {
  loadout: () => itemIcon('frag'),
  weapons: () => studioIcon('hub:weapons', () => buildWeapon('revolver'), { w: 48, h: 36, accent: '#ff4fd8', yaw: -1.25, pitch: 0.25, roll: 0.25 }),
  character: () => studioIcon('hub:character', () => buildCharacter('#ff4fd8').root, { w: 36, h: 36, accent: '#4fd8ff', yaw: 2.7, pitch: 0.12 }),
  grapple: () => studioIcon('hub:grapple', () => hookModel('rope'), { w: 36, h: 36, accent: '#ffe14d', yaw: 2.2, pitch: 0.5 }),
};
export function hubTabs(active, show, classic) {
  const nav = document.createElement('nav');
  nav.className = 'hub-tabs';
  for (const [id, name, ico] of TABS) {
    const b = document.createElement('button');
    b.className = 'hub-tab';
    b.dataset.hub = id;
    b.innerHTML = `<i>${ico}</i>`;
    const im = document.createElement('img'); im.className = 'hub-pic'; im.alt = '';
    requestAnimationFrame(() => { if (liveIcon(im, PIC[id])) b.querySelector('i').replaceWith(im); }); // (after the first paint: renders aren't free)
    b.append(name);
    b.addEventListener('click', () => {
      if (id === 'loadout') show('loadout');
      else if (id === 'weapons') show('cosmetics');
      else if (id === 'character') show('character');
      else classic();
    });
    nav.append(b);
  }
  const mark = () => { const a = typeof active === 'function' ? active() : active; for (const b of nav.children) b.classList.toggle('on', b.dataset.hub === a); };
  mark();
  nav.mark = mark;
  return nav;
}
