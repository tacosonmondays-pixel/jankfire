// PARTIES (docs/menu/HUB_LOBBY.md, build step 2): up to 6 people who queue together. Everyone with the game open is in
// a party (of one, to start), on a menu connection: the same /ws socket, but its first message is { t: 'hub' } instead
// of 'join' (server.js hands those sockets here; they never join a room). A party has a 5-character code (no 0/O, 1/I/L)
// that anyone can join with, guests included. Only the leader picks the mode, starts, kicks and passes the lead.
// When the leader starts, the server picks or makes the room once and hands every member a one-use ticket to it, so the
// whole party lands in the same room (roomFor honours the ticket) and on the same side (room.js joinTeam / partyteams.js).
// rate limits on top of the socket's budget: a wrong code costs you (10 a minute, then a wait), joins 1 a second.
import crypto from 'node:crypto';

export const PARTY = { max: 6, len: 5, abc: 'ABCDEFGHJKMNPQRSTUVWXYZ23456789', ticket: 30000, sweep: 10000, fails: 10 };
const SIDES = ['online', 'offline'], MODES = ['qp', 'bomb', 'br', 'zm', 'isle', 'training'];
const parties = new Map(); // code -> { id, code, lead, members, set }
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
    for (const b of crypto.randomBytes(PARTY.len)) s += PARTY.abc[b % PARTY.abc.length];
    if (!parties.has(s)) return s;
  }
}
const view = (h) => ({ id: h.id, name: h.name, look: h.look, gun: h.gun, mf: h.mf, ready: h.ready ? 1 : 0, acct: h.acct ? 1 : 0, busy: h.busy ? 1 : 0 }); // (gun / mf: the lobby scenes stand you there with them)
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
  if (pt.lead === h) pt.lead = pt.members[0];
  push(pt);
}
const rate = (h, k, ms) => { const t = now(); if (t - (h.t[k] || 0) < ms) return false; h.t[k] = t; return true; };

// what you're carrying, as the lobby shows it: your primary (a real primary or nothing) and your mech frame
const gunOf = (g) => (has(D.WEAPONS, g) && D.WEAPONS[g].slot === 'primary' ? g : null);
// a menu connection says hello. who = { name, look, acct, achs } (server.js checked the token and the look), m = the hello
export function hubHello(ws, who, m = {}) {
  const h = { id: nextId++, ws, name: who.name, look: who.look, achs: who.achs, acct: who.acct || null, gun: gunOf(m.gun), mf: D.mechFrame(m.mf), party: null, ready: false, busy: false, t: {}, fails: [] };
  h.send = (m) => { if (ws.readyState === 1) ws.send(JSON.stringify(m)); };
  h.send({ t: 'hubok', id: h.id });
  solo(h);
  return h;
}
export function hubClose(h) { leave(h); }

export function hubMsg(h, m) {
  if (!h.party || typeof m.t !== 'string') return;
  const pt = h.party, lead = pt.lead === h;
  switch (m.t) {
    case 'pjoin': { // join a party by its code
      if (!rate(h, 'join', 1000)) return;
      const t = now(); h.fails = h.fails.filter((x) => t - x < 60000);
      if (h.fails.length >= PARTY.fails) { h.send({ t: 'perr', m: 'too many wrong codes. give it a minute' }); return; }
      const code = typeof m.code === 'string' && m.code.length <= 12 ? m.code.toUpperCase().replace(/[^A-Z0-9]/g, '') : '';
      const to = code.length === PARTY.len && [...code].every((c) => PARTY.abc.includes(c)) ? parties.get(code) : null;
      if (!to) { h.fails.push(t); h.send({ t: 'perr', m: 'no party with that code' }); return; }
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
      if (m.t === 'pkick') { solo(v); v.send({ t: 'perr', m: 'you got kicked from the party' }); }
      else { pt.lead = v; push(pt); }
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
    case 'pbusy': if (rate(h, 'busy', 500)) { h.busy = !!m.on; push(pt); } return; // in a match right now (the lineup greys them out)
    case 'pset': { // the leader's lobby: online / offline and the mode (members' screens follow)
      if (!lead || !rate(h, 'set', 150) || !SIDES.includes(m.side) || !MODES.includes(m.mode)) return;
      pt.set = { side: m.side, mode: m.mode };
      for (const x of pt.members) x.ready = x === h;
      push(pt);
      return;
    }
    case 'pgo': if (lead && rate(h, 'go', 3000)) go(pt, m); return;
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
    if (has(D.GAMES, c.game)) cfg.game = c.game;
    if (has(D.MAPS, c.map) && D.MAP_ORDER.includes(c.map) && (!cfg.game || D.mapsFor(cfg.game, D.MAPS, D.MAP_ORDER).includes(c.map))) cfg.map = c.map;
    if (Number.isFinite(c.bots)) cfg.bots = Math.max(0, Math.min(12, Math.round(c.bots)));
    if (has(D.BOT_DIFF, c.diff)) cfg.diff = c.diff;
    if (has(D.HIPFIRE, c.hip)) cfg.hip = c.hip;
  }
  const out = pt.members.filter((x) => !x.busy || x === pt.lead);
  // the fixed rooms (online quick play, coop) need no ticket: everyone joins the one room
  if ((m.mode === 'ffa' && !cfg.lobby) || m.mode === 'coop') { for (const x of out) x.send({ t: 'pgo', mode: m.mode, cfg }); return; }
  const r = D.roomFor(m.mode, null, { ...cfg, need: out.length });
  if (!r) return;
  r.tickets = r.tickets || new Map(); r.partyT = now();
  for (const x of out) {
    const tk = crypto.randomBytes(9).toString('base64url');
    r.tickets.set(tk, { party: pt.id, until: now() + PARTY.ticket });
    x.send({ t: 'pgo', mode: m.mode, cfg: { ...cfg, room: r.id, ticket: tk } });
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
