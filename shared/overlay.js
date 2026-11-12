// z-fighting guard (public/js/zfight.js): which materials are layered just on top of which in a map's drawn boxes.
// shared so tests can check every map without a browser
export const OVERLAY_DY = 0.05, OVERLAY_MIN = 0.25, OVERLAY_THIN = 0.3, OVERLAY_MAX = 6; // a thin slab (under OVERLAY_THIN tall) whose top is this close over another top is an overlay; boxes narrower than OVERLAY_MIN are ignored; tiers stop at OVERLAY_MAX

// which materials are layered on top of which, from the drawn boxes: material -> tier (0 = not an overlay)
export function overlayTiers(boxes) {
  const all = boxes.filter((b) => b && !b.hidden && b.max[0] - b.min[0] > OVERLAY_MIN && b.max[2] - b.min[2] > OVERLAY_MIN);
  const byTop = new Map(), q = (y) => Math.round(y * 25);
  for (const b of all) { const k = q(b.max[1]); if (!byTop.has(k)) byTop.set(k, []); byTop.get(k).push(b); }
  const above = new Map(); // mat -> set of mats it sits on
  for (const b of all) {
    const y = b.max[1];
    for (let dk = -2; dk <= 2; dk++) for (const c of byTop.get(q(y) + dk) || []) {
      if (c === b || c.mat === b.mat || c.max[1] - c.min[1] > OVERLAY_THIN) continue; // (only thin slabs: a road, a rug, a crosswalk. a tree's leaf boxes or a curb aren't overlays)
      const dy = c.max[1] - y;
      if (dy < 0 || dy > OVERLAY_DY) continue;
      if (dy === 0 && c.mat > b.mat) continue; // (exactly level: pick one order, by name, so it's the same every time)
      if (Math.min(b.max[0], c.max[0]) - Math.max(b.min[0], c.min[0]) <= 0.02 || Math.min(b.max[2], c.max[2]) - Math.max(b.min[2], c.min[2]) <= 0.02) continue;
      if (!above.has(c.mat)) above.set(c.mat, new Set());
      above.get(c.mat).add(b.mat);
    }
  }
  const tier = new Map(); // longest chain under each material (a cycle stops at 6 layers)
  const depth = (m, seen) => { if (tier.has(m)) return tier.get(m); if (seen.size > 6 || seen.has(m)) return 0; seen.add(m); let t = 0; for (const u of above.get(m) || []) t = Math.max(t, depth(u, seen) + 1); seen.delete(m); return t; };
  for (const m of above.keys()) tier.set(m, Math.min(OVERLAY_MAX, depth(m, new Set())));
  return tier;
}
