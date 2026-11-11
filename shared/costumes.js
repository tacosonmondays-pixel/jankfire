// Costumes: whole outfits in one go. Bots roll into one now and then (server/botlook.js), players put one on with one
// click in CHARACTER > CLOTHES (public/js/main.js). One table, so a new costume shows up in both the day it lands.
// look: each field is one value or a list of takes on it; anything left out is left alone (bots: rolled).
// A costume only names pieces that already exist in shared/looks.js: what a player may actually wear is still decided
// by validLook on the server, with their own achievements. Nothing here is trusted.
import { TOPS, BOTTOMS, ACCESSORIES, HAIRS, ACHIEVEMENTS, hasAcc } from './looks.js';

export const COSTUMES = {
  corpo: { name: 'Corpo', desc: 'Suit, shades, no soul. Let\'s circle back.',
    look: { top: 'suit', topColor: ['#1a1a1a', '#3a3a44', '#2a4a8a'], bottom: 'pants', bottomColor: ['#1a1a1a', '#3a3a44'], hair: ['short', 'none', 'bun'], face: ['shades', 'bigglasses', 'none'], head: 'none', back: ['none', 'backpack'] } },
  ratking: { name: 'Rat King', desc: 'Shorts, a crown and skin that colour. Rules the bins.',
    look: { top: ['none', 'tank'], topColor: ['#8a5a2b', '#3a3a44'], bottom: 'shorts', bottomColor: ['#8a5a2b', '#3a6a2a'], skin: ['#555560', '#a8e6a1', '#c8a2ff'], hair: ['mohawk', 'spiky', 'long'], hairColor: ['#1a1a1a', '#7dff4f', '#4a2a10'], head: 'crown', face: ['eyepatch', 'clown', 'mustache'], back: ['cape', 'voidcape'] } },
  mallcop: { name: 'Mall Cop', desc: 'Sir. Sir. You can\'t grapple in here.',
    look: { top: 'jacket', topColor: ['#2a4a8a', '#1a1a1a'], bottom: 'pants', bottomColor: ['#2a4a8a', '#1a1a1a'], hair: ['short', 'bowl', 'none'], head: ['cap', 'hardhat'], face: ['mustache', 'shades'], back: 'none' } },
  delivery: { name: 'Delivery Guy', desc: 'Your order is 40 minutes late. So is he.',
    look: { top: ['tee', 'runner', 'hoodie'], topColor: ['#ff7a1a', '#ffe14d', '#ff4f4f', '#7dff4f'], bottom: ['shorts', 'pants'], bottomColor: ['#3a3a44', '#1a1a1a', '#2a4a8a'], head: ['cap', 'helmet', 'headphones'], face: ['none', 'shades'], back: 'backpack' } },
  maid: { name: 'Maid', desc: 'Here to clean up. The lobby, mostly.',
    look: { top: 'maid', topColor: ['#1a1a1a', '#ff9ad5', '#b07dff'], bottom: 'skirt', bottomColor: ['#1a1a1a', '#ffffff'], hair: ['ponytail', 'long', 'bun'], head: ['catears', 'none'], face: ['eyepatch', 'visor', 'none'], back: ['none', 'cattail', 'jetpack'] } },
  nightshift: { name: 'Night Shift', desc: 'Overalls and a hard hat. Hasn\'t seen the sun since March.',
    look: { top: ['hoodie', 'tee'], topColor: ['#3a3a44', '#3a6a2a'], bottom: 'overalls', bottomColor: ['#2a4a8a', '#c8b48a'], head: 'hardhat', face: ['visor', 'goggles'], back: 'none' } },
  influencer: { name: 'Influencer', desc: 'Like, subscribe and miss every shot.',
    look: { top: ['jacket', 'runner'], topColor: ['#ff4fd8', '#4fd8ff', '#ffffff'], bottom: ['skirt', 'shorts'], bottomColor: ['#ff9ad5', '#ffffff', '#4fd8ff'], hair: ['long', 'bun', 'afro'], hairColor: ['#ff4fd8', '#4fd8ff', '#f2e6c8'], head: ['party', 'bucket'], face: 'shades', back: 'wings' } },
  voidintern: { name: 'Void Intern', desc: 'Unpaid. Reports directly to the void.',
    look: { top: 'runner', topColor: ['#1a1a1a', '#b07dff'], bottom: 'pants', bottomColor: '#1a1a1a', hair: ['spiky', 'none'], hairColor: ['#7a4aff', '#ffffff'], head: 'headphones', face: ['visor', 'goggles'], back: 'voidcape' } },
  cowpoke: { name: 'Cowpoke', desc: 'This lobby ain\'t big enough.',
    look: { top: ['jacket', 'tank'], topColor: ['#8a5a2b', '#c8b48a'], bottom: 'pants', bottomColor: ['#2a4a8a', '#8a5a2b'], head: 'cowboy', face: ['mustache', 'bandana'], back: ['none', 'cape'] } },
};
export const COSTUME_IDS = Object.keys(COSTUMES);

// where a field's ids live (colours have no catalog entry: they're free)
const CAT = { top: TOPS, bottom: BOTTOMS, hair: HAIRS, head: ACCESSORIES.head, face: ACCESSORIES.face, back: ACCESSORIES.back };
const list = (v) => (Array.isArray(v) ? v : [v]);
const achName = (id) => (ACHIEVEMENTS[id] ? ACHIEVEMENTS[id].name : id);

// what a player with these achievements can make of a costume:
//   locked   the clothes themselves (top / bottom) need achievements they don't have: can't be worn. needs = which
//   missing  accessories they haven't earned: the costume goes on without them. [{ slot, name, ach }]
export function costumeFor(id, achs) {
  const C = COSTUMES[id];
  if (!C) return null;
  const needs = [], missing = [], opts = {};
  for (const [k, v] of Object.entries(C.look)) {
    const cat = CAT[k], all = list(v), ok = cat ? all.filter((x) => hasAcc(cat[x], achs)) : all;
    if (ok.length) { opts[k] = ok; continue; }
    const item = cat[all[0]]; // nothing they own in this slot
    if (k === 'top' || k === 'bottom') needs.push({ slot: k, name: item.name, ach: achName(item.ach) });
    else { missing.push({ slot: k, name: item.name, ach: achName(item.ach) }); opts[k] = ['none']; }
  }
  return { locked: needs.length > 0, needs, missing, opts };
}
// put it on: every field the costume names, one take each (pick chooses from a list). returns only those fields
export function costumeLook(id, achs, pick = (a) => a[0]) {
  const f = costumeFor(id, achs);
  if (!f || f.locked) return null;
  const out = {};
  for (const [k, ok] of Object.entries(f.opts)) out[k] = ok.length > 1 ? pick(ok) : ok[0];
  return out;
}
// is this look that costume (any take on it)?
export function wearing(id, look, achs) {
  const f = costumeFor(id, achs);
  return !!f && !f.locked && Object.entries(f.opts).every(([k, ok]) => ok.includes(look[k] || (k === 'skin' || k.endsWith('Color') ? '' : 'none')));
}
