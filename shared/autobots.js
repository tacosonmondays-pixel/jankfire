// AUTO BOTS (the owner, 2026-11-14: "for offline there is a bot count, it should be automatic unless youre doing a custom
// match"): how many bots an OFFLINE hub match gets. by the map's size (the same size tag the vote's map cards show):
// small maps fewer, big maps more. a team mode always comes out even (you + the bots split in two). modes that size
// their own room return null and keep doing it: royale + battle island (their crowd / squads), zombies (the horde),
// plant & defuse (always 5v5, server/sdtune.js), board game night (4 seats). CUSTOM (the bots setup menu) still sends
// its own count, and the server honours any count it's sent (clamped 0-12); no count = this.
export const AUTO_BOTS = { tiny: 3, small: 4, medium: 5, large: 7, huge: 9, 'extra large': 11 };
const OWN = (g) => !g || g.royale || g.zombies || g.board || g.bgn;

// game: a GAMES entry's id, map: a MAPS id. GAMES / MAPS passed in (the server and the client each have theirs)
export function autoBots(game, map, GAMES, MAPS) {
  const g = GAMES[game];
  if (OWN(g) || game === 'bomb' || game === 'island') return null;
  let n = AUTO_BOTS[MAPS[map] && MAPS[map].size] || AUTO_BOTS.medium;
  if (g.teams && n % 2 === 0) n += 1; // you + an odd number of bots = even teams
  return n;
}
