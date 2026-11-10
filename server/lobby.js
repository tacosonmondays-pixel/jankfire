// Mode lobbies (shared/lobby.js has the rules): a lobby phase on a Room, before each match.
// this.lobby = { kind, online, next } stays for the room's life (it's a mode lobby room); this.warm is set while the
// lobby is on (the warm-up: plain deathmatch on the match's map, no score, no stats, instant respawns), and
// this.locked once the match has started (nobody new gets in until the next lobby).
// the warm-up plays as 'dm' on purpose: no bomb, no blimp, no zombie rounds can start until startMatch hands over.
import { GAMES, mapsFor } from '../shared/modes.js';
import { MAPS, MAP_ORDER } from '../shared/map.js';
import { BR } from '../shared/royale.js';
import { LOBBY, lobbyGame } from '../shared/lobby.js';
import { VOTE, mapCards } from '../shared/vote.js';

const now = () => Date.now();
if (process.env.JF_LOBBY_WAIT) LOBBY.wait = Number(process.env.JF_LOBBY_WAIT) || LOBBY.wait; // test knobs (ms)
if (process.env.JF_LOBBY_AGAIN) LOBBY.again = Number(process.env.JF_LOBBY_AGAIN) || LOBBY.again;
if (process.env.JF_LOBBY_MIN) for (const k of Object.values(LOBBY.kinds)) k.min = Math.max(1, Number(process.env.JF_LOBBY_MIN) || k.min);
const pick = (a) => a[Math.floor(Math.random() * a.length)];

export function installLobby(Room, H) {
  const { send, rooms } = H;
  Object.assign(Room.prototype, {
    // a fresh mode lobby: a random map the mode can be played on, then the countdown
    lobbyInit(kind, online) {
      const K = LOBBY.kinds[kind];
      this.lobby = { kind, online: !!online, next: K.game || K.first || 'dm' };
      const maps = mapsFor(this.lobby.next, MAPS, MAP_ORDER);
      const forced = process.env.JF_LOBBY_MAP && maps.includes(process.env.JF_LOBBY_MAP) ? process.env.JF_LOBBY_MAP : null; // test knob
      this.cfg.map = forced || pick(maps) || this.cfg.map;
      this.setGame(this.lobby.next);
      this.enterWarm(LOBBY.wait, true);
    },
    lobbyMin() { return this.lobby && this.lobby.online ? LOBBY.kinds[this.lobby.kind].min : 1; },
    lobbyHumans() { return this.humans().filter((p) => !p.watch); },
    // can someone who picked `kind` join this room right now?
    lobbyOpen(mode, kind) {
      if (!this.lobby || this.mode !== mode || this.lobby.kind !== kind || !this.warm || this.locked || this.closed) return false;
      const h = this.lobbyHumans().length;
      return this.lobby.online ? h < (LOBBY.kinds[kind].cap || LOBBY.cap.online) : h < this.lobbySize(); // (zombies: a squad of 4)
    },
    // a bots lobby: how many fighters it holds (humans take bots' places)
    lobbySize() {
      const royale = GAMES[this.lobby.next] && GAMES[this.lobby.next].royale;
      if (LOBBY.kinds[this.lobby.kind].squad) return LOBBY.kinds[this.lobby.kind].squad; // zombies: 4, people take the bots' places
      const n = Math.max(0, Math.min(12, this.cfg.bots | 0));
      return 1 + (royale ? Math.max(n, Math.min(31, Number(process.env.JF_BR_BOTS) || BR.bots)) : n);
    },
    // the lobby phase: from a new room (first) or after a match's vote. the vote's map (and in quick play its mode)
    // becomes the next match; the warm-up itself is deathmatch on that map
    enterWarm(ms, first) {
      if (!first) {
        this.resolveVote();
        this.lobby.next = lobbyGame(this.lobby.kind, this.game);
        if (!this.setGame(this.lobby.next)) { // (shouldn't happen: the vote only offers its maps) a map that mode can be played on
          this.cfg.map = pick(mapsFor(this.lobby.next, MAPS, MAP_ORDER)) || this.cfg.map;
          if (!this.setGame(this.lobby.next)) this.lobby.next = this.game;
        }
      }
      const map0 = this.cfg.map;
      this.game = 'dm'; // (no setGame: the map stays the version the match plays, e.g. the S&D one)
      this.cfg.map = map0;
      this.locked = false;
      this.warm = { ends: now() + ms, ready: new Set(), t0: now(), waiting: false, after: !first };
      if (!first) this.broadcast({ t: 'cfg', cfg: this.cfg });
      this.startRound(); // clears the last match away: zombies, the blimp, the bomb, kills. airStart / econ stay off (no bomb, warm)
      this.round.target = 0; this.round.ends = this.warm.ends;
      if (this.mode === 'bots') this.fillBots();
      this.broadcast({ t: 'lobby', ...this.warmInfo() });
    },
    // the end-of-match vote in a one-mode lobby: straight to the map stage, for that mode. true = handled
    lobbyVote() {
      const g = this.lobby && LOBBY.kinds[this.lobby.kind].game;
      if (!g) return false;
      const maps = mapCards(g, MAPS, MAP_ORDER, this.cfg.map);
      if (maps.length < 2) return true; // one map: nothing to vote on
      this.vote = { stage: 'map', options: maps, votes: new Map(), ends: now() + VOTE.map, game: g, event: 0, map: null };
      this.botVotes();
      this.broadcast({ t: 'vote', ...this.voteInfo() });
      return true;
    },
    warmInfo() {
      const w = this.warm;
      if (!w) return null;
      const hs = this.lobbyHumans();
      return { k: this.lobby.kind, on: this.lobby.online ? 1 : 0, game: this.lobby.next, left: Math.max(0, w.ends - now()),
        ready: hs.filter((p) => w.ready.has(p.id)).map((p) => p.id), n: hs.length, min: this.lobbyMin(), wait: w.waiting ? 1 : 0, after: w.after ? 1 : 0 };
    },
    onReady(p, m) {
      const w = this.warm;
      if (!w || p.isBot || p.watch) return;
      const n = now();
      if (n - (p.readyT || 0) < 250) return;
      p.readyT = n;
      const on = m.on === undefined ? !w.ready.has(p.id) : !!m.on;
      if (on === w.ready.has(p.id)) return;
      if (on) w.ready.add(p.id); else w.ready.delete(p.id);
      this.broadcast({ t: 'lobby', ...this.warmInfo() });
    },
    // every tick while the lobby is on
    tickWarm(n) {
      const w = this.warm, hs = this.lobbyHumans();
      for (const id of w.ready) if (!hs.some((p) => p.id === id)) w.ready.delete(id);
      const enough = hs.length >= this.lobbyMin();
      if (enough && hs.length && hs.every((p) => w.ready.has(p.id)) && w.ends > n + LOBBY.ready) { // everyone's ready: 5 seconds
        w.ends = n + LOBBY.ready; this.round.ends = w.ends;
        this.broadcast({ t: 'chat', id: 0, m: 'everyone is ready. 5 seconds' });
        this.broadcast({ t: 'lobby', ...this.warmInfo() });
      }
      if (n < w.ends) return;
      if (!this.humans().length) { this.closed = true; rooms.delete(this.id); return; } // nobody came: the lobby closes
      if (!enough) { // online: not enough people yet. go again
        w.ends = n + LOBBY.wait; w.waiting = true; this.round.ends = w.ends;
        this.broadcast({ t: 'chat', id: 0, m: `waiting for players (${hs.length}/${this.lobbyMin()})` });
        this.broadcast({ t: 'lobby', ...this.warmInfo() });
        return;
      }
      this.startMatch();
    },
    // countdown's up: shut the door and start the real thing (the econ buy phase, the blimp, zombies round 1)
    startMatch() {
      this.warm = null;
      this.locked = true;
      if (!this.setGame(this.lobby.next)) this.lobby.next = this.game;
      for (const p of this.players.values()) { p.streak = 0; p.pocket = []; if (!p.isBot) send(p, { t: 'streak', reset: 1 }); } // warm-up kills don't count toward streaks
      this.broadcast({ t: 'lobby', end: 1 });
      this.startRound();
      if (this.mode === 'bots' || this.isEcon()) this.fillBots(); // Online Plant & Defuse too: bots fill the empty seats
      console.log(`[lobby] ${this.id}: ${GAMES[this.game].name} on ${this.map.name}, ${this.humans().length} human(s), ${this.players.size - this.humans().length} bot(s)`);
    },
  });
}
