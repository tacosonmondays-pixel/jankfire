// PARTIES (docs/menu/HUB_LOBBY.md, build step 2): up to 6 people who queue together. Everyone with the game open is in
// a party (of one, to start), on a menu connection: the same /ws socket, but its first message is { t: 'hub' } instead
// of 'join' (server.js hands those sockets here; they never join a room). A party has a 5-character code (no 0/O, 1/I/L)
// that anyone can join with, guests included. Only the leader picks the mode, starts, kicks and passes the lead.
// When the leader starts, the server picks or makes the room once and hands every member a one-use ticket to it, so the
// whole party lands in the same room (roomFor honours the ticket) and on the same side (room.js joinTeam / partyteams.js).
// rate limits on top of the socket's budget: a wrong code costs you (10 a minute, then a wait), joins 1 a second.
import { HUB_BACK } from './hubback.js'; // the offline single-mode picks that go back to their lobby
const rnd = (n) => globalThis.crypto.getRandomValues(new Uint8Array(n)); // (web crypto, no node: import: room.js imports this file and the story's referee runs room.js in a browser worker, where 'node:crypto' can't load)
const b64url = (u8) => { let b = ''; for (const x of u8) b += String.fromCharCode(x); return btoa(b).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }; // (base64url without Buffer: browser-safe too)

const BGN_TK = /^[A-Za-z0-9_-]{24}$/; // a board game night guest's rejoin ticket (server.js hands it out in welcome)
export const PARTY = { grace: 30000, max: 6, len: 5, abc: 'ABCDEFGHJKMNPQRSTUVWXYZ23456789', ticket: 30000, sweep: 10000, fails: 10, allFails: 600 };
let wrong = []; // every wrong code in the last minute, server-wide (many sockets guessing: they all wait)
const SIDES = ['online', 'offline'], MODES = ['qp', 'bomb', 'br', 'zm', 'isle', 'training', 'bgn'];
const parties = new Map(); // code -> { id, code, lead, members, set }
const online = new Map(); // account name_lower -> its menu connections (friends' presence, invites)
const back = new Map(); // rejoin key -> a member whose connection dropped (30 s to come back: wifi blips, reloads)
const LP_MODES = new Set(['zm', 'isle']); // the walkable lobbies
const MODE_NAMES = { qp: 'QUICK PLAY', bomb: 'PLANT & DEFUSE', br: 'JANK ROYALE', zm: 'ZOMBIES', isle: 'BATTLE ISLAND', training: 'TRAINING', bgn: 'BOARD GAME NIGHT' };
let D = null, nextId = 1;
const now = () => Date.now();
const has = (o, k) => typeof k === 'string' && Object.hasOwn(o, k);

// server.js: { roomFor, rooms, LOBBY, GAMES, MAPS, MAP_ORDER, BOT_DIFF, HIPFIRE, mapsFor, WEAPONS, mechFrame, validLook }
export function installParty(deps) {
  D = deps;
  setInterval(sweep, PARTY.sweep).unref();
}
export const partyCount = () => parties.size;

function newCode() {
  for (;;) {
    let s = '';
    for (const b of rnd(PARTY.len)) s += PARTY.abc[b % PARTY.abc.length];
    if (!parties.has(s)) return s;
  }
}
const view = (h) => ({ id: h.id, name: h.name, look: h.look, gun: h.gun, mf: h.mf, ready: h.ready ? 1 : 0, acct: h.acct ? 1 : 0, busy: h.busy ? 1 : 0, gone: h.gone ? 1 : 0 }); // (gun / mf: the lobby scenes stand you there with them)
function push(pt) {
  const base = { t: 'party', code: pt.code, lead: pt.lead.id, set: pt.set, ms: pt.members.map(view), max: PARTY.max };
  for (const h of pt.members) h.send({ ...base, me: h.id });
}
// a party of one (a fresh code): where everyone starts, and where you go when you leave or get kicked
function solo(h) {
  leave(h);
  const pt = { id: 'p' + nextId++, code: newCode(), lead: h, members: [h], set: null };
  parties.set(pt.code, pt); h.party = pt; h.ready = false;
  push(pt);
}
function leave(h) {
  const pt = h.party;
  if (!pt) return;
  pt.members = pt.members.filter((x) => x !== h); h.party = null;
  if (!pt.members.length) { parties.delete(pt.code); return; }
  if (pt.lead === h) pt.lead = pt.members.find((x) => !x.gone) || pt.members[0];
  push(pt);
}
const rate = (h, k, ms) => { const t = now(); if (t - (h.t[k] || 0) < ms) return false; h.t[k] = t; return true; };

// what you're carrying, as the lobby shows it: your primary (a real primary or nothing) and your mech frame
const gunOf = (g) => (has(D.WEAPONS, g) && D.WEAPONS[g].slot === 'primary' ? g : null);
// a menu connection says hello. who = { name, look, acct, achs } (server.js checked the token and the look), m = the hello
export function hubHello(ws, who, m = {}) {
  // back within 30 s with the key it was given (the same account, or a guest again): your old place in the party
  const old = typeof m.rk === 'string' && m.rk.length <= 24 ? back.get(m.rk) : null;
  if (old && old.gone && (old.acct || null) === (who.acct || null)) {
    back.delete(m.rk); clearTimeout(old.goneT); old.gone = 0; old.ws = ws;
    Object.assign(old, { name: who.name, look: who.look, achs: who.achs, gun: gunOf(m.gun), mf: D.mechFrame(m.mf) });
    if (!old.acct && typeof m.bt === 'string' && BGN_TK.test(m.bt)) old.bt = m.bt;
    old.send({ t: 'hubok', id: old.id, rk: old.rk });
    if (old.acct) { if (!online.has(old.acct)) online.set(old.acct, new Set()); online.get(old.acct).add(old); }
    if (old.party) push(old.party); else solo(old);
    return old;
  }
  const h = { id: nextId++, ws, rk: b64url(rnd(12)), name: who.name, look: who.look, achs: who.achs, acct: who.acct || null, gun: gunOf(m.gun), mf: D.mechFrame(m.mf), party: null, ready: false, busy: false, gone: 0, t: {}, fails: [] };
  if (!h.acct && typeof m.bt === 'string' && BGN_TK.test(m.bt)) h.bt = m.bt; // (a guest's board game night rejoin ticket, from this tab)
  h.send = (x) => { if (h.ws.readyState === 1) h.ws.send(JSON.stringify(x)); };
  h.send({ t: 'hubok', id: h.id, rk: h.rk });
  if (h.acct) { if (!online.has(h.acct)) online.set(h.acct, new Set()); online.get(h.acct).add(h); }
  solo(h);
  return h;
}
export function hubClose(h) {
  const s = h.acct && online.get(h.acct);
  if (s) { s.delete(h); if (!s.size) online.delete(h.acct); }
  if (!h.party || h.gone) return;
  // gone: kept in the party (RECONNECTING) for 30 s, in case it's a blip or a reload; then really gone
  h.gone = now(); h.ready = false; back.set(h.rk, h);
  if (h.party.lead === h) { const up = h.party.members.find((x) => !x.gone); if (up) h.party.lead = up; } // (the party doesn't wait on a dropped leader)
  h.goneT = setTimeout(() => { if (back.get(h.rk) === h) back.delete(h.rk); if (h.gone) leave(h); }, PARTY.grace);
  if (h.goneT.unref) h.goneT.unref();
  push(h.party);
}
// a friend's presence for the friends list: null = offline, else where they are (in a match: what they told us it is)
export function presenceOf(nameLower) {
  const s = online.get(nameLower);
  if (!s || !s.size) return null;
  const h = [...s].find((x) => x.busy) || [...s][0], pt = h.party;
  const size = pt ? pt.members.length : 1, full = size >= PARTY.max;
  if (h.busy) return { where: 'match', what: h.what || '', size, full };
  if (pt && pt.set && size > 1) return { where: 'lobby', what: MODE_NAMES[pt.set.mode] || '', size, full };
  return { where: 'menu', size, full };
}

export function hubMsg(h, m) {
  if (!h.party || typeof m.t !== 'string') return;
  const pt = h.party, lead = pt.lead === h;
  switch (m.t) {
    case 'pjoin': { // join a party by its code
      if (!rate(h, 'join', 1000)) return;
      const t = now(); h.fails = h.fails.filter((x) => t - x < 60000);
      if (wrong.length && t - wrong[0] > 60000) wrong = wrong.filter((x) => t - x < 60000);
      if (h.fails.length >= PARTY.fails || wrong.length >= PARTY.allFails) { h.send({ t: 'perr', m: 'too many wrong codes. give it a minute' }); return; }
      const code = typeof m.code === 'string' && m.code.length <= 12 ? m.code.toUpperCase().replace(/[^A-Z0-9]/g, '') : '';
      const to = code.length === PARTY.len && [...code].every((c) => PARTY.abc.includes(c)) ? parties.get(code) : null;
      if (!to) { h.fails.push(t); wrong.push(t); h.send({ t: 'perr', m: 'no party with that code' }); return; }
      if (to === pt) return;
      if (to.members.length >= PARTY.max) { h.send({ t: 'perr', m: `that party is full (${PARTY.max})` }); return; }
      leave(h); to.members.push(h); h.party = to; h.ready = false;
      push(to);
      return;
    }
    case 'pleave': if (pt.members.length > 1 && rate(h, 'leave', 500)) solo(h); return;
    case 'pkick': case 'plead': { // the leader only, on someone else in the party
      if (!lead || !Number.isInteger(m.id) || !rate(h, 'boss', 300)) return;
      const v = pt.members.find((x) => x.id === m.id && x !== h);
      if (!v) return;
      if (m.t === 'pkick') { if (v.gone) leave(v); else { solo(v); v.send({ t: 'perr', m: 'you got kicked from the party' }); } }
      else if (!v.gone) { pt.lead = v; push(pt); } // (not to someone who's dropped)
      return;
    }
    case 'pready': if (rate(h, 'ready', 200)) { h.ready = !!m.on; push(pt); } return;
    case 'pme': { // a new outfit, primary or mech frame (back from CUSTOMIZE): the party sees it
      if (!rate(h, 'me', 1000)) return;
      if (m.look && typeof m.look === 'object' && !Array.isArray(m.look)) h.look = D.validLook(m.look, h.achs || new Set());
      if (m.gun !== undefined) h.gun = gunOf(m.gun);
      if (m.mf !== undefined) h.mf = D.mechFrame(m.mf);
      push(pt);
      return;
    }
    case 'pbusy': // in a match right now (the lineup greys them out; friends see what it is)
      if (rate(h, 'busy', 500)) { h.busy = !!m.on; h.what = h.busy && typeof m.what === 'string' ? m.what.replace(/[^\w &'!-]/g, '').slice(0, 24) : ''; push(pt); }
      return;
    case 'plp': { // where you're standing in a walkable lobby (zombies, battle island: the lobby scenes). party only, never in a match
      const t = now(); h.lpT = (h.lpT || []).filter((x) => t - x < 1000);
      if (h.lpT.length >= 12) return; // (a flood: the extras just drop)
      h.lpT.push(t);
      if (h.busy || !pt.set || !LP_MODES.has(pt.set.mode) || !Array.isArray(m.p) || m.p.length !== 3 || !m.p.every(Number.isFinite) || !Number.isFinite(m.yaw)) return;
      const c = (v, a, b) => Math.round(Math.max(a, Math.min(b, v)) * 100) / 100;
      const out = { t: 'plp', id: h.id, p: [c(m.p[0], -60, 60), c(m.p[1], -5, 30), c(m.p[2], -60, 60)], yaw: Math.round((((m.yaw % 6.2832) + 6.2832) % 6.2832) * 1000) / 1000, a: Number.isInteger(m.a) ? Math.max(0, Math.min(15, m.a)) : 0 };
      for (const x of pt.members) if (x !== h && !x.busy) x.send(out);
      return;
    }
    case 'pinvite': case 'pjoinf': { // friends only (an account each, friends in the store): invite one to your party, or join theirs
      const to = typeof m.name === 'string' && m.name.length <= 24 ? m.name.trim().toLowerCase() : '';
      if (!h.acct || !to || to === h.acct || !rate(h, m.t, 1500) || !D.areFriends) return;
      const t = m.t;
      D.areFriends(h.acct, to).then((yes) => {
        if (!h.party || h.ws.readyState !== 1) return;
        const them = online.get(to);
        if (!yes || !them || !them.size) { h.send({ t: 'perr', m: yes ? 'they are offline' : 'only friends can do that' }); return; }
        if (t === 'pinvite') { for (const x of them) x.send({ t: 'pinvite', from: h.name, code: h.party.code, mode: h.party.set ? MODE_NAMES[h.party.set.mode] || '' : '' }); h.send({ t: 'perr', m: 'invite sent' }); return; }
        const pt2 = [...them].map((x) => x.party).find((p) => p && p !== h.party);
        if (!pt2) return;
        if (pt2.members.length >= PARTY.max) { h.send({ t: 'perr', m: `their party is full (${PARTY.max})` }); return; }
        leave(h); pt2.members.push(h); h.party = pt2; h.ready = false;
        push(pt2);
      }).catch(() => {});
      return;
    }
    case 'pset': { // the leader's lobby: online / offline and the mode (members' screens follow)
      if (!lead || !rate(h, 'set', 150) || !SIDES.includes(m.side) || !MODES.includes(m.mode)) return;
      pt.set = { side: m.side, mode: m.mode };
      for (const x of pt.members) x.ready = x === h;
      push(pt);
      return;
    }
    case 'pgo': if (lead && rate(h, 'go', 3000)) go(pt, m); return;
    case 'pbt': // a guest's board game night rejoin ticket (welcome's bt): a party start can take them back to the table that kept their seat
      if (!h.acct && typeof m.bt === 'string' && BGN_TK.test(m.bt) && rate(h, 'bt', 1000)) h.bt = m.bt;
      return;
  }
}

// the leader pressed the big button: everyone goes. mode + cfg are the same ones a solo player's client would send
// to 'join' (public/js/hubmenu.js go()), checked here key by key
function go(pt, m) {
  if (!['ffa', 'bots', 'coop', 'training'].includes(m.mode)) return;
  const c = m.cfg && typeof m.cfg === 'object' && !Array.isArray(m.cfg) ? m.cfg : {}, cfg = {};
  if (has(D.LOBBY.kinds, c.lobby) && (m.mode === 'ffa' || m.mode === 'bots')) cfg.lobby = c.lobby;
  if (m.mode === 'bots' && !cfg.lobby) {
    cfg.priv = true; // a party's own bots match is always private
    if (HUB_BACK.includes(c.hub)) cfg.hub = c.hub; // an offline single-mode pick: back to its lobby after (server/hubback.js)
    if (has(D.GAMES, c.game)) cfg.game = c.game;
    if (has(D.MAPS, c.map) && D.MAP_ORDER.includes(c.map) && (!cfg.game || D.mapsFor(cfg.game, D.MAPS, D.MAP_ORDER).includes(c.map))) cfg.map = c.map;
    if (Number.isFinite(c.bots)) cfg.bots = Math.max(0, Math.min(12, Math.round(c.bots)));
    if (has(D.BOT_DIFF, c.diff)) cfg.diff = c.diff;
    if (has(D.HIPFIRE, c.hip)) cfg.hip = c.hip;
    if ([5, 10, 15].includes(c.rounds)) cfg.rounds = c.rounds; // board game night's length (shared/bgn.js BGN.roundOpts)
  }
  const out = pt.members.filter((x) => !x.gone && (!x.busy || x === pt.lead));
  const cap = cfg.lobby && D.LOBBY.kinds[cfg.lobby].cap;
  if (cap && out.length > cap) { pt.lead.send({ t: 'perr', m: `${D.LOBBY.kinds[cfg.lobby].name.toLowerCase()} takes ${cap}. there are ${out.length} of you` }); return; }
  // the last room this party was handed and nobody went to (START, back, START again): gone, so they can't pile up
  const old = pt.room;
  if (old && !old.closed && !old.humans().length && old.id !== 'ffa' && old.id !== 'coop') { old.closed = true; D.rooms.delete(old.id); }
  // every room gets tickets, the fixed ones (online quick play, coop) too: that's how the room knows who's a party
  // board game night: someone here dropped out of a table that's still keeping their seat. the party goes back to it
  // (each joins with their own account / rejoin ticket, so only they get that seat back: room.js bgnBackFor, server.js join)
  let r = null;
  if (cfg.lobby === 'bgn') for (const x of out) {
    const key = x.acct ? 'a:' + x.acct : x.bt ? 'g:' + x.bt : null;
    if (key) for (const q of D.rooms.values()) if (q.mode === m.mode && q.bgnBackFor && q.bgnBackFor(key)) { r = q; break; }
    if (r) break;
  }
  r = r || D.roomFor(m.mode, null, { ...cfg, need: out.length });
  if (!r) return;
  pt.room = r;
  r.tickets = r.tickets || new Map(); r.partyT = now();
  if (cfg.priv) r.partyCfg = cfg; // (the leader's settings, checked above: whoever of the party walks in first, these apply)
  for (const x of out) {
    const tk = b64url(rnd(9));
    r.tickets.set(tk, { party: pt.id, until: now() + PARTY.ticket });
    x.send({ t: 'pgo', mode: r.mode, /* (the room's own mode: a packed server hands out the online room) */ cfg: { ...cfg, room: r.id, ticket: tk } });
  }
  for (const x of pt.members) x.ready = false;
  push(pt);
}

// roomFor's side of a ticket: the room it's for, once (or null)
export function ticketRoom(cfg, rooms) {
  if (!cfg || typeof cfg.room !== 'string' || typeof cfg.ticket !== 'string' || cfg.room.length > 80 || cfg.ticket.length > 40) return null;
  const r = rooms.get(cfg.room), t = r && r.tickets && r.tickets.get(cfg.ticket);
  if (!t) return null;
  r.tickets.delete(cfg.ticket);
  return !r.closed && t.until > now() ? { room: r, party: t.party } : null;
}

// a room made for a party that nobody turned up to (everyone closed the game): gone after a while. old tickets too
function sweep() {
  if (!D) return;
  const t = now();
  for (const r of D.rooms.values()) {
    if (!r.tickets) continue;
    for (const [k, v] of r.tickets) if (v.until < t) r.tickets.delete(k);
    if (r.partyT && t - r.partyT > PARTY.ticket + 10000 && !r.humans().length && !r.closed && r.id !== 'ffa' && r.id !== 'coop') { r.closed = true; D.rooms.delete(r.id); }
  }
}
