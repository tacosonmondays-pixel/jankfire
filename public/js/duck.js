// Rubber duck, client side. Homing ducks quack and swirl on their way in, a stuck duck wobbles on its victim
// and then its black hole rides them around. Eating your momentum inside a hole lives in player.js (holeEat).
import { G } from './ctx.js';
import { ME } from './player.js';
import { net } from './net.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { buildProjectile } from './models.js';
import { RP } from './replay.js';
import { WEAPONS } from '/shared/weapons.js';
import { steer } from '/shared/physics.js';

const D = WEAPONS.duck;

// whoever a duck or hole is on, if they're alive and we can see them (you, or a remote)
function bodyOf(id) {
  if (id === G.myId) return ME.alive ? ME : null;
  const r = G.remotes.get(id);
  return r && r.alive ? r : null;
}

// a duck locked onto someone: the server's correction, plus who it's after (we steer toward them in between)
net.on('dh', (m) => {
  const pr = G.projs.get(m.id);
  if (!pr) return;
  pr.p = m.p.slice(); pr.v = m.v.slice();
  if (m.h && !pr.h) { sfx.quack(pr.p, 1.3); pr.qT = 0.3; }
  pr.h = m.h || 0;
});

// a hole's size, who it's stuck to and its age (negative = a duck stuck on someone, about to open). sent twice a second
net.on('hu', (m) => {
  const h = G.holes.get(m.id);
  if (!h) return;
  h.R = m.R;
  const born = performance.now() - m.age * 1000;
  if (Math.abs(born - h.born) > 120) h.born = born; // ignore ping jitter, the wobble would stutter
  if (m.on && !h.on && m.age < 0) duckStuck(h, m);
  h.on = m.on || 0;
  if (!h.on || !bodyOf(h.on)) h.p = m.p;
});

// a duck just latched onto someone (main.js addHole, for a hole that's still a duck)
export function duckStuck(h, m) {
  sfx.quack(m.p, 1.8);
  fx.spray(m.p, 18, [0xffd23b, 0xffffff, 0xff8a00], 6, 0.7, 0.12, 10, 1);
  if (m.on === G.myId) hud.msg('A DUCK IS STUCK TO YOU', 1.4, 'slip');
  else if (h.o === G.myId) hud.msg('QUACK! STUCK', 0.9, 'brag');
}

// purple squeeze round the screen while a hole is eating your speed
let veil = null, veilK = -1;
function setVeil(k) {
  k = Math.round(k * 20) / 20;
  if (k === veilK) return;
  if (!veil) {
    veil = document.createElement('div');
    veil.id = 'holeFx';
    veil.style.cssText = 'position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity 0.15s;'
      + 'box-shadow:inset 0 0 220px 70px rgba(120,0,210,0.85);background:radial-gradient(circle at 50% 50%, transparent 40%, rgba(40,0,80,0.5) 100%);';
    (document.getElementById('hud') || document.body).appendChild(veil);
  }
  veilK = k;
  veil.style.opacity = k;
}

// every frame, after main.js has moved projectiles and spun the holes
export function duckFrame(now, dt) {
  for (const pr of G.projs.values()) {
    if (pr.k !== 'duck' || !pr.h) continue;
    const b = bodyOf(pr.h);
    if (b) steer(pr.v, [b.pos[0] - pr.p[0], b.pos[1] + 0.9 - pr.p[1], b.pos[2] - pr.p[2]], D.turn * dt);
    pr.qT = (pr.qT || 0) - dt;
    if (pr.qT <= 0) { pr.qT = 0.3 + Math.random() * 0.15; sfx.quack(pr.p); }
    if (!RP.active && Math.random() < dt * 30) fx.vortex(pr.p, 0.8); // locked on: it's already turning into a hole
  }
  for (const h of G.holes.values()) {
    if (h.on) { const b = bodyOf(h.on); if (b) h.p = [b.pos[0], b.pos[1] + 0.9, b.pos[2]]; }
    h.mesh.position.set(h.p[0], h.p[1], h.p[2]);
    const u = h.mesh.userData;
    if (now < h.born) { // the duck is stuck on them, wobbling, beak first into their chest
      if (!u.stuck) { u.stuck = buildProjectile('duck'); u.stuck.scale.setScalar(1.5); h.mesh.add(u.stuck); }
      for (const c of h.mesh.children) c.visible = c === u.stuck;
      h.mesh.scale.setScalar(1);
      const b = bodyOf(h.on), yaw = b ? b.yaw : 0;
      u.stuck.position.set(-Math.sin(yaw) * 0.42, 0.3, -Math.cos(yaw) * 0.42);
      u.stuck.rotation.set(Math.sin(now * 0.05) * 0.5, yaw + Math.PI + Math.sin(now * 0.04) * 0.5, Math.sin(now * 0.07) * 0.3);
    } else if (u.stuck) { // it opens on them
      h.mesh.remove(u.stuck); u.stuck = null;
      for (const c of h.mesh.children) c.visible = true;
      if (h.on) h.mesh.children[0].scale.setScalar(0.6); // smaller core: you can still see who it's eating
      sfx.quack(h.p, 1.5); sfx.hole(h.p);
      for (let i = 0; i < 4; i++) fx.vortex(h.p, 3);
    }
  }
  setVeil(G.joined && ME.alive && G.holes.size && !RP.active ? Math.min(0.9, (ME.holeF || 0) * 1.5) : 0);
}
