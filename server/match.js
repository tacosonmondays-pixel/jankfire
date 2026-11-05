// One match's personal record for the end screen: score, kills, deaths, rank, KDR, xp and medals.
// The server only counts what it already trusts (its own kill handling), nothing a client says.
import { WEAPONS } from '../shared/weapons.js';
import { MEDALS } from '../shared/medals.js';

export function matchReset(p) {
  p.m = { xp: 0, hsk: 0, melee: 0, best: 0, multi: 0, log: [], fast: 0, far: 0, voids: 0, revenge: 0, first: 0 };
}
// called for every kill that counts (killer !== victim, round live)
export function matchKill(room, k, t, w) {
  if (!k.m) matchReset(k);
  const m = k.m, n = Date.now();
  if (!room.firstBlood) { room.firstBlood = k.id; m.first = 1; }
  if (t.lastHs) m.hsk++;
  if (WEAPONS[w] && WEAPONS[w].slot === 'melee') m.melee++;
  if (w === 'void') m.voids++;
  if (k.lastKiller === t.id) m.revenge++;
  m.best = Math.max(m.best, k.streak || 0);
  m.log = m.log.filter((x) => n - x < 8000); m.log.push(n);
  m.multi = Math.max(m.multi, m.log.length);
  m.fast = Math.max(m.fast, Math.round(Math.hypot(k.vel[0], k.vel[1], k.vel[2]) * 3.6));
  m.far = Math.max(m.far, Math.round(Math.hypot(k.pos[0] - t.pos[0], k.pos[1] - t.pos[1], k.pos[2] - t.pos[2])));
  if (!k.acct && room.mode !== 'training') m.xp += t.isBot ? 5 : 20; // accounts get theirs through stat() (same numbers)
}
const scoreOf = (p) => { const m = p.m || {}; return p.kills * 100 + (m.hsk || 0) * 25 + (m.best || 0) * 10 + (m.first ? 50 : 0); };
// rank = place in the end-of-match order (i), list = everyone in that order
export function matchSummary(p, i, list, room) {
  const m = p.m || {};
  const score = scoreOf(p);
  const medals = [];
  const add = (id) => { if (MEDALS[id]) medals.push(id); };
  if (m.first) add('first');
  if (!p.deaths && p.kills >= 3) add('untouch');
  if (m.hsk >= 3) add('hs');
  if (m.multi >= 3) add('multi3'); else if (m.multi === 2) add('multi2');
  if (m.best >= 5) add('streak');
  if (m.fast >= 200) add('fast');
  if (m.far >= 60) add('far');
  if (m.voids) add('void');
  if (m.revenge) add('revenge');
  if (m.melee >= 3) add('melee');
  if (list.length > 2 && p.deaths >= 5 && list.every((q) => q.deaths <= p.deaths)) add('feeder');
  if (list.length > 1 && score > 0 && list.every((q) => q === p || scoreOf(q) < score)) add('mvp');
  if (!p.kills && !p.deaths) add('pacifist');
  return { score, kills: p.kills, deaths: p.deaths, rank: i + 1, of: list.length, kdr: Math.round((p.kills / Math.max(1, p.deaths)) * 100) / 100,
    xp: m.xp || 0, best: m.best || 0, hsk: m.hsk || 0, fast: m.fast || 0, far: m.far || 0, medals, game: room.game };
}
