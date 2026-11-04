// Homing slippers on the client. The server sends where a slipper is every 0.1 s ('pu', with its locked target and phase).
// In between we fly it with the same steering the server uses (toward the target on the way out, at the thrower on the
// way back), and when an update lands we keep drawing it where it was and melt the gap away instead of snapping.
import { G } from './ctx.js';
import { ME } from './player.js';
import { WEAPONS } from '/shared/weapons.js';
import { PH } from '/shared/physics.js';
import { steer } from '/shared/homing.js';

const SMOOTH = 12; // 1/s: how fast a correction fades
const SNAP = 4; // m: further off than this (lag spike, teleport) and we just jump

const LEAD = 0.11; // s: remotes are drawn this far behind the server clock (main.js INTERP_MS), the slipper isn't

// where a player is in the slipper's timeline, so the predicted curve bends toward where the server is aiming it
function posOf(id) {
  if (id === G.myId) return ME.alive ? ME.pos : null;
  const r = G.remotes.get(id);
  if (!r || !r.alive) return null;
  const v = r.vel || [0, 0, 0];
  return [r.pos[0] + v[0] * LEAD, r.pos[1] + v[1] * LEAD, r.pos[2] + v[2] * LEAD];
}

function init(pr) {
  if (pr.sp) return;
  pr.sp = pr.p.slice(); pr.sv = pr.v.slice(); pr.off = [0, 0, 0]; pr.tg = 0; pr.ph = 0;
}

export function slipperUpdate(pr, m, at = performance.now()) {
  init(pr);
  pr.uAt = at; // the next frame flies it only from here, not for the whole frame (or it runs a frame ahead)
  for (let k = 0; k < 3; k++) pr.off[k] = pr.p[k] - m.p[k];
  if (Math.hypot(...pr.off) > SNAP) pr.off = [0, 0, 0];
  pr.sp = m.p.slice(); pr.sv = m.v.slice(); pr.v = m.v.slice();
  pr.tg = m.tg || 0; pr.ph = m.ph || 0;
}

export function slipperStep(pr, dt, now = performance.now()) {
  init(pr);
  const sp = pr.sp, sv = pr.sv;
  const fly = pr.uAt != null ? Math.max(0, Math.min(dt, (now - pr.uAt) / 1000)) : dt;
  pr.uAt = null;
  const o = pr.ph ? posOf(pr.o) : null;
  if (o) { // on the way back: straight at the thrower's hand, like the server, and wait there for the catch
    const to = [o[0] - sp[0], o[1] + PH.eye - 0.3 - sp[1], o[2] - sp[2]], d = Math.hypot(...to), s = Math.hypot(...sv);
    if (d > 1e-3) {
      for (let k = 0; k < 3; k++) sv[k] = (to[k] / d) * s;
      const st = Math.min(s * fly, Math.max(0, d - 1));
      for (let k = 0; k < 3; k++) sp[k] += (to[k] / d) * st;
    }
  } else {
    const t = !pr.ph && pr.tg ? posOf(pr.tg) : null;
    if (t) steer(sv, sp, [t[0], t[1] + 0.9, t[2]], WEAPONS.slipper.homeTurn * fly);
    for (let k = 0; k < 3; k++) sp[k] += sv[k] * fly;
  }
  const f = Math.exp(-SMOOTH * dt);
  for (let k = 0; k < 3; k++) { pr.off[k] *= f; pr.p[k] = sp[k] + pr.off[k]; }
  pr.v = sv;
}
