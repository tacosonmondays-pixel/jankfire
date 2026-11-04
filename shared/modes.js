// Game types for the Online and Bots rooms (the room type ffa / bots / coop / training is separate).
import { lavaOk } from './lava.js';
export const GAMES = {
  dm: { name: 'Deathmatch', desc: 'everyone for themselves. first to the kill limit', teams: false },
  tdm: { name: 'Team Deathmatch', desc: 'red vs blue. first team to the kill limit', teams: true },
  tags: { name: 'Tags', desc: "kills drop tags. grab enemy tags to score, grab your own team's to deny them", teams: true },
  bomb: { name: 'Plant & Defuse', desc: 'attackers plant the bomb at A or B (hold F). defenders stop them or defuse it', teams: true, sites: true },
  rand: { name: 'Randomizer', desc: 'everyone gets a random loadout every life. first to the kill limit', teams: false, random: true },
};
export const GAME_ORDER = ['dm', 'tdm', 'tags', 'bomb', 'rand'];
export const TEAMS = { 1: { name: 'RED', color: '#ff4f4f' }, 2: { name: 'BLUE', color: '#4fa8ff' } };
// kill / point limits per room type
export const TARGETS = { ffa: { dm: 20, tdm: 40, tags: 25, rand: 20 }, bots: { dm: 15, tdm: 30, tags: 20, rand: 15 } };
export const BOMB = {
  plant: 3, defuse: 5, fuse: 35, // seconds
  roundTime: 110, wins: 4, swapAfter: 3, // first to 4 rounds, sides swap after round 3
  radius: 18, dmg: 220, pickup: 1.7, defuseRange: 2.6, respawn: 4500, between: 5000,
};
export const TAG_LIFE = 30000;
export const VOTE_MS = 14000;

// which bomb site (if any) a point is in
export function siteAt(map, p) {
  for (const s of (map && map.sites) || []) {
    if (p[0] >= s.min[0] && p[0] <= s.max[0] && p[2] >= s.min[2] && p[2] <= s.max[2] && p[1] >= s.min[1] - 1 && p[1] <= s.max[1] + 4) return s;
  }
  return null;
}
export function mapsFor(game, maps, order) {
  return order.filter((id) => id !== 'range' && maps[id] && (!GAMES[game].sites || (maps[id].sites && maps[id].sites.length)) && (!GAMES[game].lava || lavaOk(maps[id])));
}

// chaos modes (free for all). kit = the only weapons you get (no item, no killstreaks), checked by the server too.
// hookMul = grapple pull, lives = one in the chamber's lives (out of lives = spectate), bullets = start / max
Object.assign(GAMES, {
  spoons: { name: 'Spoons & Grapples', desc: 'spoons only (one hit kills) and the grapple pulls harder. swing in and bonk', teams: false, kit: { slots: ['spoon'], noItem: true, noStreaks: true }, hookMul: 1.35 },
  duckrain: { name: 'Duck Rain', desc: 'deathmatch, but rubber ducks rain from the sky and land as black holes. watch for the shadows', teams: false, duckRain: true },
  lava: { name: 'Floor Is Lava', desc: 'the ground floor burns. stay on crates, roofs and walls. bhop and grapple', teams: false, lava: true },
  oitc: { name: 'One in the Chamber', desc: 'a revolver with one bullet (any hit kills) and a knife. kills give bullets. 3 lives, last one standing wins', teams: false, kit: { slots: ['revolver', 'knife'], noItem: true, noStreaks: true, noReload: true }, lives: 3, bullets: [1, 3] },
});
GAME_ORDER.push('spoons', 'duckrain', 'lava', 'oitc');
Object.assign(TARGETS.ffa, { spoons: 20, duckrain: 20, lava: 20 });
Object.assign(TARGETS.bots, { spoons: 15, duckrain: 15, lava: 15 });
// duck rain: a drop every `every` seconds (start -> end of the match), `n` ducks per drop scaled by map size, from `height` up
export const DUCKRAIN = { every: [2.4, 1.1], n: [1.5, 3.5], height: 46, vy: 6, near: 0.5, hole: { R: 12, pull: 40, time: 2.6 } };
