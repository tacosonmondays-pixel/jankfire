// BATTLE ISLAND (docs/modes/BATTLE_ISLAND.md): Jank Royale in squads of 3. You go down instead of dying while a
// squadmate is still up, crawl, bleed out, and your squad can pick you up (hold F). The last squad standing wins.
// It plays on a royale map until the island lands. Shared by the server (server/island.js: the real rules) and the
// client (public/js/island.js: the squad HUD, markers, crawling). Every number here is a default: tune it in ISLE.
import { GAMES, GAME_ORDER, TARGETS } from './modes.js';
import './royale.js'; // (Jank Royale's maps and GAMES.br first: the island rides on it)

export const ISLE = {
  size: 3, squads: 6, // squads of 3, up to 6 of them (18 people, bots fill the gaps)
  // down, not dead: s before you bleed out, s of bleed every point of damage takes off, crawl speed (m/s), the
  // lag slack the server gives a crawl (m), how long after a shove you may fly about (ms)
  down: { bleed: 30, hurt: 0.25, crawl: 1.7, slack: 2.5, flung: 1500 },
  // picking someone up: hold F this long (s), this close (m, flat; + slack for lag, and a height band), back on your
  // feet with this much HP. gap: ms between 'use's that still counts as holding F
  revive: { hold: 4, r: 2.5, slack: 0.4, dy: 1.8, hp: 30, gap: 1000 }, // (gap: like the zombies' revive, slow clients send them late)
  stick: 25, // bots stay about this close to a human squadmate (all-bot squads: their leader, a bit looser)
  safe: 22, // a bot picks a squadmate up when no enemy it can see is this close
  // the MECH METER (0-100, the server's): full in `time` s on its own (on the ground, up, no mech out), an energy cell,
  // every 10 damage you deal, a kill. at 100 the streak key calls your hero in (MECH DROP). it breaks: back to `after`
  meter: { max: 100, time: 90, cell: 20, dmg: 0.1, kill: 25, after: 25 },
  cells: { every: 8, max: 2 }, // energy cells: one next to about every 8th loot spot (until the map tags its own)
  zoneMech: 6, // outside the zone a mech's armour takes the zone's damage x this (mechs have 9-15x a pilot's HP)
};
// the zone: 5 rings over about 12 minutes. [wait (s), shrink (s), radius as a share of the first, damage per s outside].
// the last ring is `finalR` m across at least, on land, and leans to the middle (or the map's royale.finale spots)
export const ISLE_ZONE = [[120, 75, 0.6, 2], [95, 60, 0.36, 4], [80, 50, 0.2, 7], [65, 45, 0.1, 11], [60, 45, 0, 16]];
export const ISLE_FINAL = { r: 20, lean: 0.45 }; // the last ring's radius (m), how far from the middle it may sit (share of the first ring)

// each squad's colour (markers, the HUD) and a silly-literal name
export const SQUADS = [
  null,
  { name: 'THE LOAVES', color: '#ff4fd8' }, { name: 'BIN LIDS', color: '#ffe14d' }, { name: 'WET SOCKS', color: '#4fd8ff' },
  { name: 'TAX RETURNS', color: '#7dff4f' }, { name: 'SPARE KEYS', color: '#ff9a3a' }, { name: 'LOOSE CHANGE', color: '#b07dff' },
];
export const squadOf = (sq) => SQUADS[sq] || { name: `SQUAD ${sq}`, color: '#ffffff' };
// a squad status row: [id, hp, state, bleed left (tenths of a s), who's picking them up]
export const ST = { UP: 0, DOWN: 1, OUT: 2, SKY: 3 };

Object.assign(GAMES, {
  island: { name: 'BATTLE ISLAND', desc: 'squads of 3. drop in together, go down instead of dying, hold F on a downed squadmate to pick them up. last squad standing wins', teams: false, royale: true, squads: true, mapOk: (m) => !!(m && m.royale) },
});
GAME_ORDER.push('island');
TARGETS.ffa.island = 0; TARGETS.bots.island = 0; // no kill limit: last squad standing
