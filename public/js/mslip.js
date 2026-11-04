// Marble Shotgun marbles on the floor, the part everyone sees (the server owns the patches and who slips, see
// shared/marbles.js): the marbles resting in each patch, skittering when someone runs through, thinning on a slip
import { G } from './ctx.js';
import { net } from './net.js';
import { marbles } from './marbles.js';
import { sfx } from './audio.js';
import { recordEv } from './replay.js';
import { ME } from './player.js';
import { onPatch } from '/shared/marbles.js';

const okPatch = (m) => Number.isFinite(m.id) && Array.isArray(m.c) && m.c.length === 3 && m.c.every(Number.isFinite) && Number.isFinite(m.r) && Number.isFinite(m.n) && Number.isFinite(m.left);
export const marblePalette = (o) => { const sk = ((o === G.myId ? G.equipped : G.skins.get(o)) || {}).marbles; return sk && sk[3] === 'marbles_gumball' ? 'gumball' : 'glass'; };
export function addPatch(m) { if (okPatch(m)) marbles.addPatch(m.id, m, marblePalette(m.o)); } // also the welcome's live patches
export function clearPatches() { for (const k of [...marbles.patches.keys()]) if (k > 0) marbles.dropPatch(k); }

net.on('mpatch', (m) => { recordEv(m); addPatch(m); });
net.on('mslip', (m) => { // someone slipped on one: the marbles fly out from under them
  recordEv(m);
  if (!Array.isArray(m.p)) return;
  marbles.thinPatch(m.id, m.n, m.r, m.p);
  if (m.by !== G.myId) sfx.clatter(m.p); // (your own slip clatters in player.js)
});
net.on('mpx', (m) => { recordEv(m); marbles.dropPatch(m.id); });

// people running through a patch kick the marbles round their feet about (only looks: the patch stays where it is)
const kickT = new Map();
function skitter() {
  requestAnimationFrame(skitter);
  if (!marbles.patches.size) return;
  const now = performance.now(), movers = [];
  if (ME.alive) movers.push([G.myId, ME.pos, ME.vel]);
  for (const r of G.remotes.values()) if (r.alive && r.pos && r.vel) movers.push([r.id, r.pos, r.vel]);
  for (const [id, pos, vel] of movers) {
    if (Math.hypot(vel[0], vel[2]) < 2.5 || now - (kickT.get(id) || 0) < 60) continue;
    for (const pt of marbles.patches.values()) {
      if (!onPatch(pt, pos, 0.6)) continue;
      kickT.set(id, now);
      if (marbles.kick(pos, vel) && Math.random() < 0.5) sfx.marble(id === G.myId ? null : pos);
      break;
    }
  }
  if (kickT.size > 40) kickT.clear();
}
requestAnimationFrame(skitter);
