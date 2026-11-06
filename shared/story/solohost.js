// the small bits of a server room the solo story host has to do itself, so weapons that wait on the server still work
// (a sim system, pure). for now: the Card Deck's hand (dealt on join, redrawn with R like server.js deal()).
// combat that needs a referee (enemy HP, projectiles, gimmick spawns) lands with the enemy lanes.
import { addSystem } from './sim.js';

function newDeck() {
  const d = [];
  for (const s of ['h', 's', 'c', 'd']) for (let r = 1; r <= 13; r++) d.push(s + r);
  d.push('j0', 'j0');
  for (let i = d.length - 1; i > 0; i--) { const j = (Math.random() * (i + 1)) | 0; [d[i], d[j]] = [d[j], d[i]]; }
  return d;
}
function deal(sim) {
  if (!sim.deck || sim.deck.length < 5) sim.deck = newDeck();
  sim.send({ t: 'hand', hand: sim.deck.splice(0, 5), left: sim.deck.length });
}
addSystem({
  id: 'solohost',
  join(sim) { deal(sim); },
  raw(sim, m) {
    if (m.t !== 'redraw') return false;
    if (sim.t - (sim.redrawT ?? -9) > 2.5) { sim.redrawT = sim.t; deal(sim); }
    return true;
  },
});
