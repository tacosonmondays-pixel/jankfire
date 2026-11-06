// The CUSTOMIZE hub: one row of tabs on top of the four dress-up screens, so they read as one place.
// LOADOUT and WEAPONS are the customize screen (customize.js) in its two modes, CHARACTER is the outfit screen,
// GRAPPLE & SPRAY is what's left of the old locker.
const TABS = [['loadout', 'LOADOUT', '🎒'], ['weapons', 'WEAPONS', '🔫'], ['character', 'CHARACTER', '🧍'], ['grapple', 'GRAPPLE & SPRAY', '🪝']];
export function hubTabs(active, show, classic) {
  const nav = document.createElement('nav');
  nav.className = 'hub-tabs';
  for (const [id, name, ico] of TABS) {
    const b = document.createElement('button');
    b.className = 'hub-tab';
    b.dataset.hub = id;
    b.innerHTML = `<i>${ico}</i>`;
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
