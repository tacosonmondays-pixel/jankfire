// RESET: respawn yourself without having to find a cliff (owner, 2026-11-10). Only in Training, co-op against bots and
// quick play (Online or With Bots); never in Plant & Defuse, Jank Royale, Zombies, a mode with lives, a lobby or the
// story. If someone hurt you in the last 10 s they get the kill (the same credit window as the void), so it is not a
// way out of a lost fight. Mixed into Room by installReset.
let H; // helpers from room.js (now, send)
export const RESET = { cd: 8000, afterSpawn: 2500 }; // ms between resets; ms after spawning before the first one (no chaining spawn protection)

export function installReset(Room, helpers) {
  H = helpers;
  const P = Room.prototype, handle = P.handle;
  Object.assign(P, {
    handle(p, m) {
      if (m && m.t === 'reset') { this.onReset(p); return; }
      return handle.call(this, p, m);
    },
    // '' = allowed here, else a short reason for the HUD
    resetNo() {
      if (!['training', 'coop', 'bots', 'ffa'].includes(this.mode)) return 'NO RESET HERE';
      if (this.lobby || this.warm) return 'NO RESET IN A LOBBY';
      if (this.zm) return 'NO RESET IN ZOMBIES';
      if (this.brOn) return 'NO RESET IN JANK ROYALE';
      if (this.isEcon && this.isEcon()) return 'NO RESET IN PLANT & DEFUSE';
      if (this.bomb) return 'NO RESET IN PLANT & DEFUSE';
      if (this.livesOn) return 'NO RESET: YOU ONLY GET SO MANY LIVES';
      return '';
    },
    onReset(p) {
      const n = H.now();
      if (!p || p.isBot || !p.alive) return;
      const no = this.resetNo();
      if (no) { H.send(p, { t: 'reset', no }); return; }
      if (this.round && this.round.over) return; // between rounds: you're about to be respawned anyway
      const wait = Math.max((p.resetT || 0) + RESET.cd - n, (p.spawnT || 0) + RESET.afterSpawn - n);
      if (wait > 0) { H.send(p, { t: 'reset', no: 'RESET IN ' + Math.ceil(wait / 1000) + 's', ms: Math.round(wait) }); return; }
      p.resetT = n;
      this.kill(p, null, 'reset'); // (kill() hands it to whoever hurt them last, like a fall into the void)
    },
  });
}
