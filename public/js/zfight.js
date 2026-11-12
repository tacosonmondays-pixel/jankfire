// No more flickering roads (the owner: "when you look above the roads like flicker... they're clipping in and out of
// another texture"). Two causes, two fixes:
//  1. overlays: a road 2 cm over a sidewalk 3 cm over the paving, a rug on a floor, a crosswalk on a road. Far away the
//     depth buffer can't tell 2 cm apart and the two surfaces take turns. Each map's build finds every material whose top
//     sits on another material's top (within OVERLAY.dy) and gives it a "tier": drawn a hair toward the camera
//     (polygonOffset), one more hair per layer it sits on, so the top layer always wins. Looks only: nothing moves.
//  2. height: the camera's near plane was always 10 cm, which wastes nearly all of the depth buffer's precision on the
//     first few metres. From the blimp or a glide that left about 2 cm of precision at the street. The near plane now
//     grows with your height over the ground (only above OVERLAY.from metres, where nothing is that close to your eye).
import { BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { overlayTiers, OVERLAY_DY } from '/shared/overlay.js';
export { overlayTiers };

export const OVERLAY = { dy: OVERLAY_DY, from: 12, k: 0.012, nearMax: 2.4, base: 0.1 };

// give the map's materials their tiers (and take last map's off): { key: { mat } } as world.js's MAT
export function applyOverlayTiers(MAT, tiers) {
  let n = 0;
  for (const [k, v] of Object.entries(MAT)) {
    const m = v && v.mat; if (!m) continue;
    const t = tiers.get(k) || 0, on = t > 0;
    if (m.polygonOffset !== on || m.polygonOffsetUnits !== -2 * t) { m.polygonOffset = on; m.polygonOffsetFactor = on ? -t : 0; m.polygonOffsetUnits = on ? -2 * t : 0; m.needsUpdate = true; }
    if (on) n++;
  }
  return n;
}

// the near plane: grows with the height over the ground under you (checked every few frames)
let gy = 0, frame = 0;
export function depthNear(cam) {
  if (!cam) return;
  if (frame++ % 6 === 0) { const h = raycast([cam.position.x, cam.position.y, cam.position.z], [0, -1, 0], 600, BOXES); gy = h ? h.point[1] : Math.min(gy, cam.position.y - 600); }
  const up = cam.position.y - gy, want = Math.min(OVERLAY.nearMax, Math.max(OVERLAY.base, OVERLAY.base + (up - OVERLAY.from) * OVERLAY.k));
  if (Math.abs(want - cam.near) > 0.02) { cam.near = want; cam.updateProjectionMatrix(); }
}
export const nearInfo = () => ({ ground: gy });
