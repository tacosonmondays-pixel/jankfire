// Pits that hurt (shared/pits.js): the lava down Mount Kaboom's throat. stand in it and you burn, climb out and you
// keep burning for a moment; die in there and what's left of you gets coughed back out of the crater. nobody owns the
// lava: whoever knocked you in gets the kill (room.kill does that for 'lava' already).
import { PIT, inPit } from '../shared/pits.js';

export function installPits(Room, U) {
  const { now, r2 } = U;
  Object.assign(Room.prototype, {
    tickPits(n = now()) {
      if (!this.map.pits || (this.round && this.round.over)) return;
      const L = PIT.lava;
      for (const p of this.players.values()) {
        if (!p.alive) { p.pitBurn = 0; continue; }
        const q = inPit(this.map, p.pos);
        if (q && q.kind === 'lava' && n >= (p.pitNext || 0)) {
          p.pitNext = n + L.every * 1000; p.pitBurn = n + L.burn * 1000; p.pitBurnT = n + L.burnEvery * 1000; p.hzT = n;
          this.broadcast({ t: 'sizzle', id: p.id, p: p.pos.map(r2), hz: 1 });
          if (p.hp <= L.dmg) p.vel = [(Math.random() - 0.5) * 7, L.erupt, (Math.random() - 0.5) * 7]; // the last tick: the crater spits the bits back out
          this.damage(p, L.dmg, null, 'lava');
        } else if (!q && p.pitBurn > n && n >= (p.pitBurnT || 0)) { // out of it, still on fire
          p.pitBurnT = n + L.burnEvery * 1000; p.hzT = n;
          this.broadcast({ t: 'fx', k: 'burn', id: p.id });
          this.damage(p, L.burnDmg, null, 'lava');
        }
      }
    },
  });
}
