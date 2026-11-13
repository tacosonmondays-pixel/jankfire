// BACK TO THE LOBBY: an OFFLINE single-mode match from the hub (Plant & Defuse, Jank Royale, Zombies, Battle Island:
// public/js/hubmenu.js plan() sends cfg.hub) has no quick play vote at the end. the end screen offers PLAY AGAIN /
// LOBBY instead; when its timer runs out everyone who didn't pick PLAY AGAIN goes back to that mode's lobby (the
// menu), the rest get the same mode again. offline quick play keeps its vote, online mode lobbies keep LOBBY.again.
// (room.js imports this: browser-safe, no node: imports. the story's referee runs room.js in a worker)
export const HUB_BACK = ['bomb', 'br', 'zm', 'isle'];
export const HB = { wait: 20000 }; // nobody stayed and someone's still here (an old client): the same mode again after this

// the match is over: instead of the vote (room.startVote)
export function hubBackOpen(room) {
  const r = room.round;
  for (const p of room.players.values()) p.hbAgain = false;
  if (r) r.hbSent = false;
  room.broadcast({ t: 'hubback', k: 'open', mode: room.hubBack });
}
// PLAY AGAIN on / off ('hbagain' from a client; room.js checked the room and that the match is over)
export function hubBackPick(room, p, on) {
  if (p.isBot || p.watch || p.hbAgain === on) return;
  p.hbAgain = on;
  const hs = room.humans(), n = hs.filter((h) => h.hbAgain).length, r = room.round;
  room.broadcast({ t: 'hubback', k: 'again', n, of: hs.length });
  if (on && n === hs.length && r && !r.hbSent) r.next = Math.min(r.next, Date.now() + 600); // everyone wants more: straight in
}
// the end screen's timer ran out (room.tickRound): true = handled, no new match yet
export function hubBackDue(room, n) {
  const r = room.round;
  if (!r || r.hbSent) return false; // (second time round: whoever's still here plays the same mode again)
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
