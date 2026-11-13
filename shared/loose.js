// Loose pieces (mannequin gibs, a zombie's severed limbs, hats): gravity, walls, and the floor under where the piece
// is NOW. They used to keep the floor found under the body when it died, so a piece that flew off a staircase, a bench,
// a bed or a balcony stopped in mid-air at that height (and one that left through a wall hung there too).
import { raycast } from './physics.js';

const NONE = -1e9; // nothing under it: it keeps falling until its time is up
export function floorUnder(boxes, x, y, z) { const h = raycast([x, y + 0.35, z], [0, -1, 0], 80, boxes); return h ? h.point[1] : NONE; }

// one step for a piece. boxes = the map's collision. o = { v: [x, y, z], floorY, ft? }, p = its position ({ x, y, z }), rest = how high its origin
// lies when it's down. returns 0 in the air or lying still, 1 for a soft landing, 2 for a hard one (the caller splats)
export function looseStep(boxes, o, p, dt, rest = 0.05, bounce = 0.35, drag = 0.6) {
  const hv = Math.hypot(o.v[0], o.v[2]);
  if (hv > 0.4) { // a wall in the way: off it, slower
    const h = raycast([p.x, p.y + 0.06, p.z], [o.v[0] / hv, 0, o.v[2] / hv], hv * dt + 0.14, boxes);
    if (h && h.axis !== 1) { o.v[h.axis] *= -0.4; o.v[h.axis === 0 ? 2 : 0] *= 0.8; }
  }
  o.v[1] -= 22 * dt;
  p.x += o.v[0] * dt; p.y += o.v[1] * dt; p.z += o.v[2] * dt;
  const still = Math.abs(o.v[1]) < 0.7 && hv < 0.3 && p.y <= o.floorY + rest + 0.03;
  o.ft = (o.ft || 0) - dt;
  if (o.ft <= 0 || p.y < o.floorY + rest) { o.ft = still ? 0.5 : 0.08; o.floorY = floorUnder(boxes, p.x, Number.isFinite(o.floorY) && o.floorY > NONE / 2 ? Math.max(p.y, Math.min(o.floorY, p.y + 1)) : p.y, p.z); } // (asked again as it moves, and now and then at rest: a shutter it lay on may have opened)
  if (p.y >= o.floorY + rest) return 0;
  p.y = o.floorY + rest;
  const hard = Math.abs(o.v[1]) > 3;
  o.v[1] = Math.abs(o.v[1]) * bounce; o.v[0] *= drag; o.v[2] *= drag;
  if (o.v[1] < 0.45) o.v[1] = 0; // (no endless tiny bounces)
  if (!o.v[1] && Math.hypot(o.v[0], o.v[2]) < 0.35) o.v[0] = o.v[2] = 0; // ... and it stops sliding
  return hard ? 2 : 1;
}
