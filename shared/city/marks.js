// Marks without building the city (the solo sim's worker, the server): every chunk mark in a city, precomputed by
// tools/city/gta_index.mjs into marks_<city>.js. marksNear(city, x, z, r, kind?) -> [mark] within r (metres, flat)
// kind: a mark id ('shop', 'park', 'garage', 'crowd', 'grapple', 'arena.add'...), or a test function (m) => bool.
// Shops: { id: 'shop', shop, sid, name, p, keeper, face, door, stock? } (shops.js); parking: { id: 'park', p, yaw, road? |
// sale? | lot? }; garages: { id: 'garage', p, face, home, door }. Roads and pavements: roads.js roadsNear.
import SLICE_MARKS from './marks_slice.js';

const BY = { slice: SLICE_MARKS.marks };
export function marksNear(city, x, z, r, kind) {
  const list = BY[city] || [], out = [], test = typeof kind === 'function' ? kind : kind ? (m) => m.id === kind : null;
  for (const m of list) if (Math.abs(m.p[0] - x) <= r && Math.abs(m.p[2] - z) <= r && Math.hypot(m.p[0] - x, m.p[2] - z) <= r && (!test || test(m))) out.push(m);
  return out;
}
export const allMarks = (city) => BY[city] || [];
