// no flickering roads: on every map, a material whose top sits just over another material's top (a road on a sidewalk,
// a crosswalk on a road) must be drawn in a higher overlay tier than the one under it (public/js/zfight.js), so the
// top layer always wins the depth test. Exactly level pairs (dy 0) only need different tiers.
import test from 'node:test';
import assert from 'node:assert/strict';
import '../shared/royale.js';
import { MAPS, MAP_ORDER } from '../shared/map.js';
import { overlayTiers, OVERLAY_DY, OVERLAY_MIN, OVERLAY_THIN } from '../shared/overlay.js';

const ids = [...new Set([...MAP_ORDER, 'jankburg'])].filter((id) => MAPS[id] && !MAPS[id].stream && id !== 'battleisland');
test('every overlay is drawn above what it sits on', () => {
  let pairs = 0, bad = [];
  for (const id of ids) {
    const m = MAPS[id], all = [...m.boxes, ...(m.deco || [])].filter((b) => !b.ter && !b.hidden && b.max[0] - b.min[0] > OVERLAY_MIN && b.max[2] - b.min[2] > OVERLAY_MIN);
    const tier = overlayTiers(all), t = (k) => tier.get(k) || 0;
    const byTop = new Map(), q = (y) => Math.round(y * 25);
    for (const b of all) { const k = q(b.max[1]); if (!byTop.has(k)) byTop.set(k, []); byTop.get(k).push(b); }
    const seen = new Set();
    for (const b of all) for (let dk = -2; dk <= 2; dk++) for (const c of byTop.get(q(b.max[1]) + dk) || []) {
      if (c === b || c.mat === b.mat || c.max[1] - c.min[1] > OVERLAY_THIN) continue;
      const dy = c.max[1] - b.max[1];
      if (dy < 0 || dy > OVERLAY_DY) continue;
      if (Math.min(b.max[0], c.max[0]) - Math.max(b.min[0], c.min[0]) <= 0.02 || Math.min(b.max[2], c.max[2]) - Math.max(b.min[2], c.min[2]) <= 0.02) continue;
      const key = id + ':' + c.mat + '>' + b.mat; if (seen.has(key)) continue; seen.add(key); pairs++;
      const ok = dy === 0 ? t(c.mat) !== t(b.mat) : t(c.mat) > t(b.mat);
      if (!ok) bad.push(`${id}: ${c.mat} (tier ${t(c.mat)}) ${dy === 0 ? 'level with' : dy.toFixed(3) + ' m over'} ${b.mat} (tier ${t(b.mat)})`);
    }
  }
  console.log(`${ids.length} maps, ${pairs} overlay pairs, ${bad.length} not ordered`);
  // a few can't be ordered (A over B here, B over A there, both on the same map): allowed, but they must stay rare
  assert.ok(pairs > 100, 'the scan finds overlays (roads on sidewalks...)');
  assert.ok(bad.length <= pairs * 0.05, 'unordered overlays:\n' + bad.slice(0, 30).join('\n'));
});
