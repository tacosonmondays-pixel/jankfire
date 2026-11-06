// Mode lobbies (ONLINE / WITH BOTS on the home menu): pick Plant & Defuse, Jank Royale or Zombies, land in a lobby on that mode's map, run around in a
// warm-up while a big countdown runs, then the match starts. once it's going the lobby is shut: anyone else who picks
// that mode gets a fresh lobby. after the match (and its vote) the same room goes back to a short lobby.
// shared by the server (the rules) and the client (the cards, the names, the countdown).
export const LOBBY = {
  wait: 60000, // the countdown (ms)
  again: 10000, // the lobby after a match, before the next one
  ready: 5000, // everyone hit READY: the countdown jumps to this
  respawn: 900, // warm-up deaths: back in almost straight away
  cap: { online: 16 }, // most humans in one Online mode lobby (bots lobbies: the room's size, bots included)
  // game: the mode the match plays. lobby: false = no lobby (quick play: drop in anytime, Online = the 'ffa' room,
  // With Bots = an open bots room with a bot for you to replace, the end-of-match vote picks any mode)
  // min: real players needed for the match to start (Online only. with bots, one of you is enough)
  kinds: {
    qp: { name: 'QUICK PLAY', game: null, lobby: false, min: 1, desc: 'drop in anytime, you take a bot\'s place. vote the next mode', art: 'dm' },
    bomb: { name: 'PLANT & DEFUSE', game: 'bomb', min: 2, desc: 'attackers plant, defenders defuse. buy guns between rounds', art: 'bomb' },
    br: { name: 'JANK ROYALE', game: 'br', min: 2, desc: 'blimp, umbrella, loot, shrinking zone. last one standing', art: 'br' },
    zm: { name: 'ZOMBIES', game: 'zm', min: 1, desc: 'you and your friends vs endless rounds of zombies. buy doors', art: 'zm' },
  },
  order: ['qp', 'bomb', 'br', 'zm'],
};
// the mode a lobby's match plays (quick play: whatever the vote last picked)
export const lobbyGame = (kind, cur) => (LOBBY.kinds[kind] && LOBBY.kinds[kind].game) || cur || 'dm';
export const hasLobby = (kind) => !!LOBBY.kinds[kind] && LOBBY.kinds[kind].lobby !== false;
