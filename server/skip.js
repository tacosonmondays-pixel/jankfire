// /skip (or /voteskip) in chat: vote to skip the match that's on. A majority of the humans in the room skips it (bots
// don't vote; alone, your vote is enough). The vote runs 30 s; one that fails puts /skip on a minute's cooldown. When it
// passes the match ends there and then and the end-of-match vote starts, without the skipped mode on the cards.
// A skipped match pays no winner's container and doesn't count for Never Landed (server.js checks round.skipped),
// or skipping would be a free farm.
import { GAMES } from '../shared/modes.js';

export const SKIP = { window: 30000, cooldown: 60000, again: 1500 };
export const isSkipCmd = (text) => /^\/(vote)?skip(\s|$)/i.test(text);
export const skipNeed = (humans) => Math.floor(humans / 2) + 1; // more than half: 1 of 1, 2 of 2, 2 of 3, 3 of 4...

const tell = (room, p, m) => room.sendTo(p, { t: 'chat', id: 0, m });
const live = (room) => (room.mode === 'ffa' || room.mode === 'bots') && room.round && !room.round.over;
const name = (g) => (GAMES[g] ? GAMES[g].name : g);
function count(room) {
  const v = room.skip, ids = new Set(room.humans().map((h) => h.id));
  for (const id of v.votes) if (!ids.has(id)) v.votes.delete(id); // whoever left takes their vote with them
  return { n: v.votes.size, need: skipNeed(ids.size) };
}
// what clients are told about the vote that's on (null: none)
export function skipInfo(room) {
  const v = room.skip;
  if (!v) return null;
  const { n, need } = count(room);
  return { game: v.game, name: name(v.game), n, need, left: Math.max(0, v.ends - Date.now()), by: v.by };
}
function update(room) {
  const s = skipInfo(room);
  if (!s) return;
  if (s.n >= s.need) { pass(room); return; }
  room.broadcast({ t: 'skipvote', ...s });
}
function pass(room) {
  const g = room.skip.game;
  room.skip = null;
  room.skipped = g; // the next vote leaves it off the cards
  room.broadcast({ t: 'skipvote', end: 1, ok: 1, game: g, name: name(g) });
  room.broadcast({ t: 'chat', id: 0, m: `${name(g)} skipped. the people have spoken` });
  room.round.skipped = true;
  room.endRound();
}
function stop(room, failed) {
  const v = room.skip;
  room.skip = null;
  room.broadcast({ t: 'skipvote', end: 1, ok: 0, game: v.game, quiet: failed ? 0 : 1 });
  if (!failed) return;
  room.skipCool = Date.now() + SKIP.cooldown;
  room.broadcast({ t: 'chat', id: 0, m: `not enough votes to skip ${name(v.game)}. it goes on` });
}

// a human typed /skip
export function skipCommand(room, p) {
  if (p.isBot) return;
  if (room.mode !== 'ffa' && room.mode !== 'bots') { tell(room, p, 'nothing to skip here'); return; }
  if (room.warm) { tell(room, p, `this is the lobby. press READY (everyone ready = 5 seconds)`); return; } // nothing to skip till the match starts
  if (!live(room)) { tell(room, p, room.hubBack ? 'the match is already over. PLAY AGAIN or back to the lobby, on the end screen' : 'the match is already over. pick the next one on the end screen'); return; }
  const n = Date.now();
  if (n - (p.skipT || 0) < SKIP.again) return; // spam
  p.skipT = n;
  if (!room.skip) {
    if (n < (room.skipCool || 0)) { tell(room, p, `a skip vote just failed. try again in ${Math.ceil((room.skipCool - n) / 1000)}s`); return; }
    room.skip = { game: room.game, votes: new Set(), ends: n + SKIP.window, by: p.name };
  }
  if (room.skip.votes.has(p.id)) { tell(room, p, 'you already voted to skip'); return; }
  room.skip.votes.add(p.id);
  const { n: got, need } = count(room);
  if (got < need) room.broadcast({ t: 'chat', id: 0, m: `${p.name} votes to skip ${name(room.skip.game)} (${got}/${need}). type /skip to agree` });
  update(room);
}
// every round tick: the vote runs out, or the match ended on its own first
export function skipTick(room, n) {
  if (!room.skip) return;
  if (!live(room) || room.skip.game !== room.game) { stop(room, false); return; }
  if (n >= room.skip.ends) stop(room, true);
}
// someone joined or left: the majority moved (a leaver can tip it over, a joiner raises the bar)
export function skipPeople(room) { if (room.skip) { if (live(room)) update(room); else stop(room, false); } }
