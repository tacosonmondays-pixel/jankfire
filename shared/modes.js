// Game types for the Online and Bots rooms (the room type ffa / bots / coop / training is separate).
export const GAMES = {
  dm: { name: 'Deathmatch', desc: 'everyone for themselves. first to the kill limit', teams: false },
  tdm: { name: 'Team Deathmatch', desc: 'red vs blue. first team to the kill limit', teams: true },
  tags: { name: 'Tags', desc: "kills drop tags. grab enemy tags to score, grab your own team's to deny them", teams: true },
  bomb: { name: 'Plant & Defuse', desc: 'attackers plant the bomb at A or B (hold F). defenders stop them or defuse it', teams: true, sites: true },
  rand: { name: 'Randomizer', desc: 'everyone gets a random loadout every life. first to the kill limit', teams: false, random: true },
  zm: { name: 'Zombies', desc: 'co-op vs endless rounds of zombies. hits and kills earn credits: look at a door, wall gun or the crate and hold F to buy. hold F on a downed friend to revive them', teams: false, zombies: true },
};
export const GAME_ORDER = ['dm', 'tdm', 'tags', 'bomb', 'rand', 'zm'];
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
  order = order.filter((id) => !GAMES[game].zombies === !(maps[id] && maps[id].zm)); // zombie maps go with zombies and nothing else
  return order.filter((id) => id !== 'range' && maps[id] && (!GAMES[game].sites || (maps[id].sites && maps[id].sites.length)));
}
