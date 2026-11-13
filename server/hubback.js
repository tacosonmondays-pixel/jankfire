// BACK TO THE LOBBY: an OFFLINE single-mode match from the hub (Plant & Defuse, Jank Royale, Zombies, Battle Island:
// public/js/hubmenu.js plan() sends cfg.hub) has no quick play vote at the end. the end screen offers PLAY AGAIN /
// LOBBY instead; when its timer runs out everyone who didn't pick PLAY AGAIN goes back to that mode's lobby (the
// menu), the rest get the same mode again. offline quick play keeps its vote, online mode lobbies keep LOBBY.again.
// (room.js imports this: browser-safe, no node: imports. the story's referee runs room.js in a worker)
export const HUB_BACK = ['bomb', 'br', 'zm', 'isle'];
export const HB = { wait: 20000, flip: 250 }; // wait: nobody stayed and someone's still here (an old client): the same mode again after this. flip: PLAY AGAIN on / off no faster
const GAME_HUB = { bomb: 'bomb', br: 'br', zm: 'zm', island: 'isle' }; // a game -> the hub lobby it belongs to

// the match is over: instead of the vote (room.startVote)
export function hubBackOpen(room) {
  const r = room.round;
  for (const p of room.players.values()) p.hbAgain = false;
  if (r) { r.hbSent = false; r.hbT = Date.now(); }
  room.broadcast({ t: 'hubback', k: 'open', mode: room.hubBack });
}
// PLAY AGAIN on / off ('hbagain' from a client; room.js checked the room and that the match is over)
export function hubBackPick(room, p, on) {
  const t = Date.now(), r = room.round;
  if (p.isBot || p.watch || p.hbAgain === on || !r || r.hbSent || t - (p.hbFlip || 0) < HB.flip) return;
  p.hbAgain = on; p.hbFlip = t;
  const hs = room.humans(), n = hs.filter((h) => h.hbAgain).length;
  if (on && n === hs.length) { r.next = Math.min(r.next, Math.max(t + 600, (r.hbT || t) + 1800)); room.holdForHl(); } // everyone wants more: straight in (after the play of the round, which starts 1.6 s in)
  room.broadcast({ t: 'hubback', k: 'again', n, of: hs.length, total: Math.max(0, r.next - t) });
}
// someone walked in while the end screen is up (a party member on a late ticket): they get the cards too
export function hubBackJoin(room, p) {
  const r = room.round;
  if (room.hubBack && r && r.over && !r.hbSent && p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify({ t: 'hubback', k: 'open', mode: room.hubBack }));
}
// the pause menu switched this private match's mode: back to the lobby that mode belongs to (or a vote, if none)
export function hubBackGame(room) { if (room.hubBack) room.hubBack = GAME_HUB[room.game] || null; }
// the end screen's timer ran out (room.tickRound): true = handled, no new match yet
export function hubBackDue(room, n) {
  const r = room.round;
  if (!r || r.hbSent) return false; // (second time round: whoever's still here plays the same mode again)
  if (r.hlEnd && n < r.hlEnd) { r.next = r.hlEnd; return true; } // the play of the round is still on: let it finish
  r.hbSent = true;
  const stay = [];
  for (const p of room.humans()) {
    if (p.hbAgain) stay.push(p);
    else if (p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify({ t: 'hubback', k: 'go', mode: room.hubBack }));
  }
  if (stay.length) return false; // the ones who stay: a new match now (the rest are on their way out)
  r.next = n + HB.wait;
  return true;
}
