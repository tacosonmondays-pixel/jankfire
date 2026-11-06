// Props: Blender models (tools/blender/make_<prop>.py -> public/models/p_<id>.glb) placed on a map. Visual only:
// collisions stay boxes. A map keeps its own boxes for the prop and tags them { pv: id }: the client draws those
// boxes only while the model isn't loaded (missing file = the old box look), and draws the model instead.
// Two ways to use it from a map builder (shared/map.js):
//   prop(L, 'forklift', x, z, r)             catalog boxes below + the model, in one call (new placements)
//   L.P('car', x, z, r, { color }) -> tag    just the model; pass the returned tag as the extra of your own boxes
// L is a builder local frame (B.local); r = extra quarter turns like local()'s rot (1 = front turned from +x to +z).
// opts: v = variant (numball digit, 'bay'/'frame' for racks, 0/1 for pallets), color = a car paint mat name, s = scale.

// local boxes per prop: [x0, y0, z0, x1, y1, z1, mat], front = +x (vehicles), y = 0 on the ground
export const PROPS = {
  car: [[-2.2, 0.32, -0.92, 2.2, 0.95, 0.92, 'carred'], [-1.1, 0.95, -0.8, 0.9, 1.5, 0.8, 'glass'], [-1.15, 1.5, -0.82, 0.95, 1.6, 0.82, 'carred']],
  bus: [[-5.5, 0.45, -1.22, 5.5, 3.1, 1.22, 'caryellow'], [5.5, 0.45, -1.1, 6.5, 1.75, 1.1, 'caryellow']],
  forklift: [[-1.2, 0, -0.8, 1.2, 1.4, 0.8, 'caryellow'], [-0.9, 1.4, -0.7, 0.4, 2.4, 0.7, 'glass'], [1.2, 0, -0.4, 2.6, 0.2, 0.4, 'metal'], [1.2, 0, -0.6, 1.4, 3, 0.6, 'metal']],
  pallet: [[-0.6, 0, -0.4, 0.6, 0.144, 0.4, 'wood']],
  pallet_load: [[-0.6, 0, -0.4, 0.6, 0.144, 0.4, 'wood'], [-0.58, 0.144, -0.38, 0.58, 1.3, 0.38, 'crate']],
  streetlight: [[-0.125, 0, -0.125, 0.125, 6, 0.125, 'metal'], [0, 5.8, -0.12, 1.6, 6.0, 0.12, 'metal'], [1.3, 5.675, -0.2, 1.9, 5.925, 0.2, 'light']],
  numball: [[-0.42, 0, -0.42, 0.42, 1, 0.42, 'gold']],
  rack: [], // racks are built by the map (long decks + uprights), the model is drawn bay by bay
};

const turn = (x, z, r) => [[x, z], [-z, x], [-x, -z], [z, -x]][r & 3]; // same as builder local()

// catalog boxes + the model. returns the tag so a caller can add more boxes that vanish with the model
export function prop(L, id, x, z, r = 0, o = {}) {
  const tag = L.P ? L.P(id, x, z, r, o) : undefined;
  const s = o.s || 1, y = o.y || 0;
  for (const [x0, y0, z0, x1, y1, z1, mat] of PROPS[id] || []) {
    const [ax, az] = turn(x0 * s, z0 * s, r), [bx, bz] = turn(x1 * s, z1 * s, r);
    L(x + ax, y + y0 * s, z + az, x + bx, y + y1 * s, z + bz, id === 'car' && o.color && mat !== 'glass' ? o.color : mat, tag);
  }
  return tag;
}
