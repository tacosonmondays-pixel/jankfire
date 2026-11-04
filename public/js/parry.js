// Katana parry, the part everyone sees (input + viewmodel are in weapons.js, the rules on the server):
// sparks and the SHING where it happened, the parrier's flash / shout / hit stop, PARRIED for whoever got bounced,
// bullets flying home on a perfect parry, and the guard pose on other players (guard.js poses it from r.parryT).
import { G } from './ctx.js';
import { net } from './net.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { W, parryLanded, stagger } from './weapons.js';
import { recordEv } from './replay.js';
import { guardHit, guardStagger, weaponPoint, hitFrom } from './guard.js';
import { eye } from './player.js';

const bigT = new Map(); // parrier -> when we last made a big deal of it (a minigun stream shouldn't SHING ten times)

// someone raised their guard
net.on('guard', (m) => {
  recordEv(m);
  const r = G.remotes.get(m.id);
  if (r) { r.parryT = performance.now(); sfx.guard(r.pos); }
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
  // where it hit the blade: the bit of it between them and the parrier (guard.js). yours sparks in the viewmodel,
  // and at = the world point on screen over that spot
  const from = hitFrom(m, (id) => G.remotes.get(id), m.by === G.myId ? eye() : null);
  let at = m.p;
  if (mine) at = parryLanded(!!m.pf, big, from) || m.p;
  else if (r && r.alive) at = guardHit(r, m, now, big, from);
  else fx.sparks(m.p, null, big ? (m.pf ? 40 : 26) : 8, !!m.pf);
  if (big) sfx.parry(mine ? null : at, !!m.pf); else sfx.tink(mine ? null : at);
  if (m.b) { fx.reflect(at, m.b); sfx.ricochet(at); } // perfect: the bullet goes home, from the blade, for everyone
  // a parried swing: both blades spark and the swinger reels (yours: stagger() below)
  const atk = m.k === 'melee' && m.by !== G.myId ? G.remotes.get(m.by) : null;
  if (atk) { guardStagger(atk, now, m.st); const wp = weaponPoint(atk); if (wp) fx.sparks(wp, null, big ? 14 : 5, false); }
  // a batted-back projectile belongs to the parrier now (a stolen slipper goes home to them, so you can throw another)
  const pr = m.pr && G.projs.get(m.pr);
  if (pr) { if (pr.k === 'slipper' && pr.o === G.myId) W.slipperOut = false; pr.o = m.id; }
  if (mine) {
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
