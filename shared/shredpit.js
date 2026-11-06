// The shredder pits (the Warehouse has one by the west door): map.shredders = [{ box: [x0, z0, x1, z1], y, axis }].
// two toothed drums turn a few metres down the pit; drop in past y (the tips of the teeth) and the server kills you
// there. it's a void kill (whoever knocked you in gets it) and the kill message says pit: 1, so every client plays the
// chew (public/js/shredpit.js). axis 'z' = the drums lie along z (side by side across x), 'x' = along x
export const PIT = { idle: 1.8, rev: 3.2, jam: 0.32, chew: 1.1, heat: 4.5, hear: 30 }; // rad/s, rev boost, s jammed, s chewing, s to cool, m you hear it from

export function inShredder(map, p) {
  const s = map && map.shredders;
  if (!s) return null;
  for (const q of s) if (p[1] < q.y && p[1] > q.y - 30 && p[0] > q.box[0] && p[0] < q.box[2] && p[2] > q.box[1] && p[2] < q.box[3]) return q;
  return null;
}
