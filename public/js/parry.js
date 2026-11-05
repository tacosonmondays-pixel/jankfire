// Katana parry, the part everyone sees (input + viewmodel are in weapons.js, the rules on the server):
// sparks and the SHING where it happened, the parrier's flash / shout / hit stop, PARRIED for whoever got bounced,
// bullets flying home on a perfect parry, and the guard pose on other players (remote.js reads r.parryT).
import { G } from './ctx.js';
import { net } from './net.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { W, parryLanded, stagger } from './weapons.js';
import { recordEv } from './replay.js';

const bigT = new Map(); // parrier -> when we last made a big deal of it (a minigun stream shouldn't SHING ten times)

// someone raised their guard
net.on('guard', (m) => {
  recordEv(m);
  const r = G.remotes.get(m.id);
  if (r) r.parryT = performance.now();
});

// someone parried something. k = shot / proj / melee, pf = perfect, by = whose attack it was,
// p = where it hit the blade, b = where a perfect-parried bullet went back to, pr = the projectile that got batted back
net.on('parry', (m) => {
  recordEv(m);
  const now = performance.now(), mine = m.id === G.myId, r = G.remotes.get(m.id);
  const big = now - (bigT.get(m.id) || -1e9) > 180;
  if (big) {
    bigT.set(m.id, now);
    if (bigT.size > 16) for (const [id, t] of bigT) if (now - t > 1000) bigT.delete(id); // players come and go: forget stale ones
  }
  if (!mine) { // your own blade sparks in the viewmodel instead
    let dir = null;
    if (r) { const dx = m.p[0] - r.pos[0], dz = m.p[2] - r.pos[2], l = Math.hypot(dx, dz) || 1; dir = [dx / l, 0, dz / l]; }
    fx.sparks(m.p, dir, big ? (m.pf ? 40 : 26) : 8, !!m.pf);
    if (r) r.parryHitT = now;
  }
  if (big) sfx.parry(mine ? null : m.p, !!m.pf); else sfx.tink(mine ? null : m.p);
  if (m.b) { fx.tracer(m.p, m.b, 0xffffff, 0.07, 0.3); fx.tracer(m.p, m.b, 0x9fe8ff, 0.025, 0.5); sfx.ricochet(m.p); } // the bullet goes home
  // a batted-back projectile belongs to the parrier now (a stolen slipper goes home to them, so you can throw another)
  const pr = m.pr && G.projs.get(m.pr);
  if (pr) { if (pr.k === 'slipper' && pr.o === G.myId) W.slipperOut = false; pr.o = m.id; }
  if (mine) {
    parryLanded(!!m.pf, big);
    if (big || m.pf) {
      hud.msg(m.pf ? 'PERFECT PARRY!' : 'PARRY!', m.pf ? 1.1 : 0.8, m.pf ? 'perfect' : 'parry');
      hud.flash(m.pf ? 0.8 : 0.5, m.pf ? 0.3 : 0.2);
    }
    G.shake = Math.max(G.shake, m.pf ? 0.45 : 0.25);
  } else if (m.by === G.myId) { // it was your attack that bounced
    if (m.k === 'melee') stagger(m.st || 0.55);
    if (big) hud.msg(m.k === 'shot' && !m.pf ? 'BLOCKED' : 'PARRIED', m.k === 'shot' && !m.pf ? 0.6 : 1, 'parried');
  }
});
