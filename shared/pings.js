// PINGS (the big map, M): one shared rulebook for the client (public/js/fullmap.js) and the server (server/pings.js).
// a ping is a spot on the map for you and your side: team, squad, co-op humans. solo modes: just you
export const PING = {
  life: 8000,      // ms a ping stays up
  keep: 3,         // pings alive per person (a 4th pushes the oldest off)
  burst: 3,        // at most this many...
  win: 2500,       // ...in this many ms
  gap: 250,        // and never closer together than this
  y: [-120, 600],  // height range a ping can be at (the blimp flies at ~200 on Jankburg)
  slack: 8,        // m past the map's edge that still counts (a click on the rim)
  far: 600,        // world ping key: how far the look ray goes
};
// the area a map is played in: the royale circle, else its bounds, else its boxes (scenery past 320 m is cut).
// the same rule the minimap paints with (minimap.js mapExtent), cached per map object
const cache = new WeakMap();
export function pingBox(map) {
  if (!map) return null;
  let b = cache.get(map);
  if (b) return b;
  if (map.royale && map.royale.zone0) { const [cx, cz, r] = map.royale.zone0; b = [cx - r * 1.05, cz - r * 1.05, cx + r * 1.05, cz + r * 1.05]; }
  else if (map.bounds) { const m = map.bounds; b = [m[0] - 6, m[1] - 6, m[2] + 6, m[3] + 6]; }
  else {
    let x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9;
    for (const o of map.boxes || []) { if (o.noCol) continue; x0 = Math.min(x0, o.min[0]); z0 = Math.min(z0, o.min[2]); x1 = Math.max(x1, o.max[0]); z1 = Math.max(z1, o.max[2]); }
    const c = (v) => Math.max(-320, Math.min(320, v));
    b = x0 > x1 ? [-320, -320, 320, 320] : [c(x0) - 4, c(z0) - 4, c(x1) + 4, c(z1) + 4];
  }
  b = [b[0] - PING.slack, b[1] - PING.slack, b[2] + PING.slack, b[3] + PING.slack];
  cache.set(map, b);
  return b;
}
export const inPingBox = (map, x, z) => { const b = pingBox(map); return !!b && x >= b[0] && x <= b[2] && z >= b[1] && z <= b[3]; };

// the PENCIL on the big map: lines your side sees on their big map (and faintly on the minimap). a stroke is a flat
// list [x0, z0, x1, z1, ...] in world metres, snapped to q, at most pts points
export const DRAW = {
  life: 30000,     // ms a stroke stays up (the last few seconds it fades)
  pts: 64,         // points per stroke
  keep: 6,         // strokes alive per person (a 7th rubs out your oldest)
  burst: 4,        // at most this many strokes...
  win: 3000,       // ...in this many ms
  gap: 200,        // and never closer together than this
  q: 0.5,          // m: points snap to this grid
};
export const drawQ = (v) => Math.round(v / DRAW.q) * DRAW.q;
