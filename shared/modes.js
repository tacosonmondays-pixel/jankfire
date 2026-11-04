// Game types for the Online and Bots rooms (the room type ffa / bots / coop / training is separate).
export const GAMES = {
  dm: { name: 'Deathmatch', desc: 'everyone for themselves. first to the kill limit', teams: false },
  tdm: { name: 'Team Deathmatch', desc: 'red vs blue. first team to the kill limit', teams: true },
  tags: { name: 'Tags', desc: "kills drop tags. grab enemy tags to score, grab your own team's to deny them", teams: true },
  bomb: { name: 'Plant & Defuse', desc: 'attackers plant the bomb at A or B (hold F). defenders stop them or defuse it', teams: true, sites: true },
  rand: { name: 'Randomizer', desc: 'everyone gets a random loadout every life. first to the kill limit', teams: false, random: true },
  gun: { name: 'Gun Game', desc: 'one weapon at a time. a kill moves you up the ladder, a melee death knocks you back. first kill with the spoon wins', teams: false, ladder: true },
  inf: { name: 'Infection', desc: 'someone starts infected. whoever the zombies kill turns into one. survive the timer', teams: false, infect: true },
};
export const GAME_ORDER = ['dm', 'tdm', 'tags', 'bomb', 'rand', 'gun', 'inf'];
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
// gun game: everyone climbs the same ladder, guns -> silly -> melee. a kill with your rung's weapon moves you up,
// dying to any melee weapon knocks you back one. the first kill with the last rung (the spoon) wins the match.
// update 2 adds the Shredder (with the close-range guns), the Blood Cross (with the silly ones) and the Scales of Justice
// (with the melee): 19 rungs
export const LADDER = ['ar', 'smg', 'redline', 'shotgun', 'minigun', 'shredder', 'revolver', 'marbles', 'sniper', 'bow', 'chicken', 'bloodcross', 'banana', 'cards', 'slapper', 'bread', 'scales', 'katana', 'spoon'];
export const GUNGAME = { time: 600 }; // match clock in seconds: 19 rungs take longer than a kill limit
// infection: patient zero turns a few seconds in (two of them from `two` fighters up). zombies get the claw,
// more HP and more speed; anyone who dies as a survivor comes back as a zombie. survivors win if anyone lasts the timer.
export const INFECT = { time: 180, delay: 6, two: 8, hp: 200, color: '#7dff4f' };

// which bomb site (if any) a point is in
export function siteAt(map, p) {
  for (const s of (map && map.sites) || []) {
    if (p[0] >= s.min[0] && p[0] <= s.max[0] && p[2] >= s.min[2] && p[2] <= s.max[2] && p[1] >= s.min[1] - 1 && p[1] <= s.max[1] + 4) return s;
  }
  return null;
}
// can someone standing at pos defuse a bomb at bp? a cylinder, not a ball: a bomb planted on a prop (up to 4 m above
// the site, see siteAt) can still be defused from the floor under it. it only reaches up: standing on a roof you can't
// defuse a bomb on the floor beneath it. slack: the extra room you get while holding F
export function canDefuse(pos, bp, slack = 0) {
  const dy = bp[1] - pos[1];
  return Math.hypot(pos[0] - bp[0], pos[2] - bp[2]) < BOMB.defuseRange + slack && dy < 4.6 + slack && dy > -1.6 - slack;
}
export function mapsFor(game, maps, order) {
  return order.filter((id) => id !== 'range' && maps[id] && (!GAMES[game].sites || (maps[id].sites && maps[id].sites.length)));
}
