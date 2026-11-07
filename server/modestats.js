// Per-mode stats for the per-mode leaderboards (shared/modestats.js has the boards). Nothing here touches the Room
// code itself: it wraps a few Room methods and watches what the room broadcasts, then keeps a per-player batch that goes
// to the store (inv.ms) at the end of a match, when they leave, and every 90 s. It follows the existing stat rules by
// reading them off the account counters (p.acct.d): kills only count on people (bot kills don't), nothing counts in
// training, co-op or a lobby's warm-up, and guests keep nothing. Zombies is the one mode where killing bots is the point.
// Install it after every other installer (it wraps zombies' zmGive): installModeStats(Room, { store }).
import { MODE_MAX } from '../shared/modestats.js';

const FLUSH_MS = 90e3;
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

// which board a room's stats go on (null = none)
export function modeBucket(room) {
  if (!room || room.warm || (room.mode !== 'ffa' && room.mode !== 'bots')) return null; // training, co-op, story: no
  if (room.zm) return 'zm';
  if (room.brOn) return 'br';
  if (room.game === 'bomb') return 'bomb';
  return 'qp';
}

export function installModeStats(Room, { store }) {
  const P = Room.prototype, tracked = new Set();
  const add = (room, p, k, v = 1) => {
    const B = modeBucket(room);
    if (!B || !p || p.isBot || !p.acct || !(v > 0)) return;
    const d = ((p.msd ||= {})[B] ||= {});
    d[k] = MODE_MAX.has(k) ? Math.max(d[k] || 0, v) : (d[k] || 0) + v;
    tracked.add(p);
  };
  const flush = (p) => {
    tracked.delete(p);
    if (!p.msd || !p.acct) { p.msd = null; return; }
    const d = p.msd; p.msd = null;
    store.addModeStats(p.acct.n, d).catch((e) => console.error('mode stats save failed', e.message));
  };
  setInterval(() => { for (const p of [...tracked]) flush(p); }, FLUSH_MS).unref?.();
  const counted = (room) => room.humans().filter((p) => p.acct).map((p) => [p, p.acct.d, { ...p.acct.d }]); // account counters before
  const diff = (p, d, before, k) => (p.acct && p.acct.d === d ? (d[k] || 0) - (before[k] || 0) : 0); // (a flush in between: nothing new)

  // kills + deaths, as the account counted them. streaks are this mode's (people only, a death resets it)
  const kill0 = P.kill;
  P.kill = function (t, attacker, w) {
    const B = modeBucket(this);
    if (!B || !t || !t.alive) return kill0.call(this, t, attacker, w);
    const snap = counted(this), tp = t.pos.slice(), zombie = !!t.zmz;
    const r = kill0.call(this, t, attacker, w);
    if (zombie && attacker && attacker !== t) add(this, attacker, 'zk');
    for (const [p, d, b] of snap) {
      const dk = diff(p, d, b, 'kills'), dd = diff(p, d, b, 'deaths');
      if (B === 'qp') {
        if (dk > 0) { add(this, p, 'kills', dk); p.msStreak = (p.msStreak || 0) + dk; add(this, p, 'streak', p.msStreak); }
        if (dd > 0) { add(this, p, 'deaths', dd); p.msStreak = 0; }
      } else if (B === 'br' && dk > 0) {
        add(this, p, 'kills', dk);
        if (p === attacker) add(this, p, 'far', Math.round(dist3(p.pos, tp)));
      } else if (B === 'bomb' && dk > 0) add(this, p, 'score', 150 * dk); // a kill is worth 150 combat score
    }
    return r;
  };
  // damage that landed (hp actually went down): royale damage, P&D combat score + headshot %
  const dmg0 = P.damage;
  P.damage = function (t, amt, attacker, w, hs, from) {
    const B = modeBucket(this), hp0 = t && t.hp, ad = attacker && attacker.acct && attacker.acct.d, h0 = ad ? ad.headshots || 0 : 0;
    const r = dmg0.call(this, t, amt, attacker, w, hs, from);
    if (B === 'qp' && ad && attacker.acct.d === ad && (ad.headshots || 0) > h0) add(this, attacker, 'hs', ad.headshots - h0); // headshots as the account counted them
    if (!B || !attacker || attacker === t || attacker.isBot || !attacker.acct || !(hp0 > 0)) return r;
    const dealt = Math.min(100, Math.max(0, hp0 - Math.max(0, t.hp || 0)));
    if (!(dealt > 0)) return r;
    if (B === 'br') add(this, attacker, 'dmg', Math.round(dealt));
    else if (B === 'bomb') { add(this, attacker, 'score', Math.round(dealt)); add(this, attacker, 'hits'); if (hs) add(this, attacker, 'hsh'); }
    return r;
  };
  // the match ended: quick play wins as the account counted them (same rules: enough bots / people, a kill), then save
  const end0 = P.endRound;
  P.endRound = function (...a) {
    const B = modeBucket(this), snap = B === 'qp' ? counted(this) : [];
    const r = end0.apply(this, a);
    for (const [p, d, b] of snap) { const dw = diff(p, d, b, 'wins'); if (dw > 0) add(this, p, 'wins', dw); }
    for (const p of this.humans()) flush(p);
    return r;
  };
  // leaving: a zombies run counts the round you got to, then everything you had goes in
  const rm0 = P.remove;
  P.remove = function (p, ...a) {
    if (p && !p.isBot && this.zm && this.zs && p.z) add(this, p, 'round', this.zs.n || 0);
    if (p && !p.isBot) flush(p);
    return rm0.call(this, p, ...a);
  };
  // credits spent in zombies (every buy goes through zmGive with a minus)
  if (P.zmGive) {
    const give0 = P.zmGive;
    P.zmGive = function (p, d, why) { if (d < 0) add(this, p, 'spent', -d); return give0.call(this, p, d, why); };
  } else console.warn('  !! modestats: no zmGive (install it after the zombies installer): zombies credits spent will not count');

  // what the room tells everyone: plants, defuses, P&D rounds, planks, cheat machine rolls, revives, royale placements
  const bc0 = P.broadcast;
  P.broadcast = function (m, ex) {
    const r = bc0.call(this, m, ex);
    try { if (m && (m.t === 'bombev' || m.t === 'zplank' || m.t === 'zmach' || m.t === 'zdown' || m.t === 'zmover' || (m.t === 'br' && m.k === 'out') || (m.t === 'round' && m.over && m.br))) onEvent(this, m); } catch (e) { console.error('modestats', e); }
    return r;
  };
  function onEvent(room, m) {
    const who = (id) => room.players.get(id);
    if (m.t === 'bombev') {
      if (m.k === 'planted') { add(room, who(m.id), 'plants'); add(room, who(m.id), 'score', 100); }
      else if (m.k === 'defused') { add(room, who(m.id), 'defuses'); add(room, who(m.id), 'score', 100); }
      else if (m.k === 'win' && (m.team === 1 || m.team === 2)) {
        const fs = room.fighters().filter((p) => p.team === 1 || p.team === 2), mine = fs.filter((p) => p.team === m.team), up = mine.filter((p) => p.alive);
        for (const p of fs) { add(room, p, 'rounds'); if (p.team === m.team) add(room, p, 'rw'); }
        if (up.length === 1 && mine.length >= 2) add(room, up[0], 'clutches'); // the last one standing on the winning side
      }
    } else if (m.t === 'zplank' && m.k === 'nail') add(room, who(m.by), 'planks');
    else if (m.t === 'zmach' && m.k === 'spin') add(room, who(m.by), 'rolls');
    else if (m.t === 'zdown' && m.k === 'up' && m.by) add(room, who(m.by), 'rev');
    else if (m.t === 'zmover') { for (const p of room.humans()) if (p.z) add(room, p, 'round', m.n || 0); }
    else if (m.t === 'br' && m.k === 'out' && m.place >= 2 && m.place <= 3) add(room, who(m.id), 'top3');
    else if (m.t === 'round' && Array.isArray(m.br)) for (const [id, place] of m.br) if (place === 1) { add(room, who(id), 'wins'); add(room, who(id), 'top3'); }
  }
  return { flush, modeBucket };
}
