// BATTLE ISLAND's mech heroes (docs/mechs/ROSTER.md): who you can pick in the lobby / loadout. Each hero calls in its
// mech with MECH DROP (server/mech.js) when your MECH METER is full. A new hero is one row here plus its frame in
// shared/mech.js (and its kit's server judging): the pick, the clash rules, the HUD and the bots all read this list.
import { MECH } from './mech.js';

export const HEROES = {
  paperplane: { frame: 'paperplane', role: 'dive / air', color: '#4fd8ff', blurb: 'nimble flyer. hover, lunge, jet mode' },
  nightshift: { frame: 'nightshift', role: 'tank / melee', color: '#b07dff', blurb: 'big knight. sword, shield, ground slam' },
  wrecking: { frame: 'wrecking', role: 'dive tank', color: '#ffd23a', blurb: 'a hamster ball. ram, chain swing, ground slam, PILE DRIVER' },
  vending: { frame: 'vending', role: 'support', color: '#ff4fd8', blurb: 'a vending machine on legs. coins, colas for the squad, an OUT OF ORDER wall, RESTOCK' },
  trolley: { frame: 'trolley', role: 'speed', color: '#39ff14', blurb: 'a shopping trolley with a wonky wheel. tin cans, drift, ram, CLEAN UP AISLE 5' },
};
export const HERO_IDS = Object.keys(HEROES); // (the order the pick shows them in)
export const isHero = (h) => typeof h === 'string' && Object.hasOwn(HEROES, h);
export const heroName = (h) => (isHero(h) && MECH[HEROES[h].frame] ? MECH[HEROES[h].frame].name : '???');
// how many of one hero a squad may field: one each, until the squad is bigger than the roster (2 heroes, squads of 3)
export const heroCap = (squadSize) => Math.max(1, Math.ceil(squadSize / HERO_IDS.length));
// the hero someone gets: what they asked for if the squad has room for another, else the least picked one (ties: the
// roster order). taken = the heroes the rest of the squad already has
export function heroFor(want, taken, squadSize) {
  const n = (h) => taken.filter((x) => x === h).length, cap = heroCap(squadSize);
  if (isHero(want) && n(want) < cap) return want;
  return HERO_IDS.slice().sort((a, b) => n(a) - n(b))[0];
}
