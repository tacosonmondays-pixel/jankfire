// Per-mode leaderboards: which stats each mode keeps (in the account's inv.ms[mode], no new columns) and the boards
// built from them. Shared: the server tracks + serves them (server/modestats.js, accounts.js), the client draws the tabs.
// a board is a raw stat (top by it) or a ratio of two (with a minimum so 1 kill 0 deaths isn't the best K/D ever)
export const MODE_STATS = {
  qp: {
    name: 'QUICK PLAY', note: 'K/D needs 25 kills.', keys: ['kills', 'deaths', 'wins', 'hs', 'streak'],
    boards: [
      { id: 'kills', title: 'Most kills', key: 'kills' },
      { id: 'kd', title: 'Best K/D', ratio: ['kills', 'deaths'], min: ['kills', 25], fmt: 'x2' },
      { id: 'wins', title: 'Most wins', key: 'wins' },
      { id: 'hs', title: 'Most headshots', key: 'hs' },
      { id: 'streak', title: 'Longest streak', key: 'streak', unit: 'kills' },
    ],
  },
  bomb: {
    name: 'PLANT & DEFUSE', note: 'combat score: damage + 150 a kill + 100 a plant or defuse, per round (10 rounds to show). headshot %: 50 hits to show.', keys: ['rw', 'rounds', 'plants', 'defuses', 'clutches', 'score', 'hits', 'hsh'],
    boards: [
      { id: 'rw', title: 'Rounds won', key: 'rw' },
      { id: 'plants', title: 'Most plants', key: 'plants' },
      { id: 'defuses', title: 'Most defuses', key: 'defuses' },
      { id: 'clutches', title: 'Clutch kings', key: 'clutches' },
      { id: 'acs', title: 'Combat score / round', ratio: ['score', 'rounds'], min: ['rounds', 10], fmt: 'int' },
      { id: 'hsp', title: 'Headshot %', ratio: ['hsh', 'hits'], min: ['hits', 50], fmt: 'pct' },
    ],
  },
  zm: {
    name: 'ZOMBIES', note: 'zombies are bots, so here bot kills count.', keys: ['round', 'zk', 'rev', 'planks', 'spent', 'rolls'],
    boards: [
      { id: 'round', title: 'Highest round', key: 'round', unit: 'round', pre: 1 },
      { id: 'zk', title: 'Zombies killed', key: 'zk' },
      { id: 'rev', title: 'Most revives', key: 'rev' },
      { id: 'planks', title: 'Planks nailed', key: 'planks' },
      { id: 'spent', title: 'Credits spent', key: 'spent', unit: 'cr' },
      { id: 'rolls', title: 'Cheat Machine rolls', key: 'rolls' },
    ],
  },
  br: {
    name: 'JANK ROYALE', note: 'kills count on people. damage counts on anyone.', keys: ['wins', 'top3', 'kills', 'dmg', 'far'],
    boards: [
      { id: 'wins', title: 'Royale wins', key: 'wins' },
      { id: 'top3', title: 'Top 3 finishes', key: 'top3' },
      { id: 'kills', title: 'Most kills', key: 'kills' },
      { id: 'dmg', title: 'Most damage', key: 'dmg' },
      { id: 'far', title: 'Longest kill', key: 'far', unit: 'm' },
    ],
  },
};
export const MODE_IDS = Object.keys(MODE_STATS);
// these keep the best instead of adding up
export const MODE_MAX = new Set(['streak', 'round', 'far']);
export const modeBoard = (mode, id) => (Object.hasOwn(MODE_STATS, mode) ? MODE_STATS[mode].boards.find((b) => b.id === id) || null : null);
// a board's value for one bucket of stats (null = not on this board)
export function boardValue(b, s) {
  if (!s) return null;
  if (b.ratio) {
    const [a, c] = b.ratio, [mk, mn] = b.min || [a, 1];
    if (!((s[mk] || 0) >= mn)) return null;
    const v = (s[a] || 0) / Math.max(1, s[c] || 0);
    return b.fmt === 'pct' ? Math.round(Math.min(1, v) * 1000) / 10 : b.fmt === 'int' ? Math.round(v) : Math.round(v * 100) / 100;
  }
  return (s[b.key] || 0) > 0 ? s[b.key] : null;
}
export function fmtBoard(b, v) {
  if (b.fmt === 'pct') return `${v}%`;
  if (b.fmt === 'x2') return v.toFixed(2);
  const n = typeof v === 'number' && v >= 10000 ? `${(v / 1000).toFixed(v >= 100000 ? 0 : 1)}k` : typeof v === 'number' ? v.toLocaleString('en-US') : String(v); // 84.9k: the columns stay one line
  return b.unit === 'm' ? `${n} m` : n;
}
// a stats delta off the server's own counters: only known keys, finite, non-negative, capped (nothing from clients)
export function cleanModeDelta(d) {
  const out = {};
  if (!d || typeof d !== 'object') return out;
  for (const m of MODE_IDS) {
    const src = d[m];
    if (!src || typeof src !== 'object') continue;
    for (const k of MODE_STATS[m].keys) {
      const v = src[k];
      if (Number.isFinite(v) && v > 0) (out[m] ||= {})[k] = Math.min(v, 1e7);
    }
  }
  return out;
}
