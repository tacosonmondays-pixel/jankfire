// Blender props (round 4): which boxes a model draws instead. Shared by the server and the client, look-only: the boxes
// stay the collision, the bots' nav and everything else; they just get a tag the client reads.
// A kit prop wraps its boxes in propOf(): each is tagged { pv: id } (world.js skips drawing it while p_<id> is loaded)
// and one placement goes in its builder's boxes.props: the anchor, the turn, the extent of those boxes in the prop's
// own frame (the client fits the model onto it, so every copy keeps its own size), a variant and a tint (a map
// material key: the model's `tint` material takes that material's colour).
// One-box props (crates, barrels, pallets, cardboard boxes, shipping containers, jersey blocks) are spotted by their
// material and size as they're added, wherever a map puts them.

export const CAP = []; // open captures (the innermost one claims the boxes: a pot inside a market stall is the pot's)

// every box any builder adds comes through here
export function seen(b, list) {
  if (CAP.length) { CAP[CAP.length - 1].push([b, list]); return; }
  if (!b.pv) oneBox(b, list);
}

const ONE = { crate: ['crate', 2.2], cardboard: ['cardboard', 2.2], barrel: ['barrel', 2.2], barrelr: ['barrel', 2.2], pallet: ['pallet', 1.6] };
function oneBox(b, list) {
  if (b.rot || b.fit || !list.props) return;
  const sx = b.max[0] - b.min[0], sy = b.max[1] - b.min[1], sz = b.max[2] - b.min[2], o = ONE[b.mat];
  let id = null;
  if (o) { if (Math.max(sx, sy, sz) <= o[1] && (b.mat !== 'pallet' || sy <= 0.3)) id = o[0]; }
  else if (/^container[rgb]$/.test(b.mat)) { if (sy > 2.2 && sy < 3.1 && Math.max(sx, sz) > 5.5 && Math.min(sx, sz) > 2.1 && Math.min(sx, sz) < 3) id = 'container'; } // (not the container-walled houses)
  else if (b.mat === 'jersey') { if (sy > 0.8 && sy < 1.3 && Math.max(sx, sz) < 4.2 && Math.min(sx, sz) > 0.35) id = 'barrier'; } // (not the long rails)
  if (!id) return;
  const along = sz > sx, hx = (along ? sz : sx) / 2, hz = (along ? sx : sz) / 2; // the model is long along x
  b.pv = id;
  list.props.push({ id, a: [(b.min[0] + b.max[0]) / 2, b.min[1], (b.min[2] + b.max[2]) / 2], y: along ? -Math.PI / 2 : 0, lo: [-hx, 0, -hz], hi: [hx, sy, hz], t: b.mat });
}

// a turn of its own for things that look the same any way round (trees, pots): from where it stands, not the map's rng
export const spinAt = (x, z) => ((((Math.sin(x * 12.9898 + z * 78.233) * 43758.5453) % 1) + 1) % 1) * Math.PI * 2;

// at: the prop's anchor in world space. frame: its turn (three's rotation.y, radians) for the fit. o.spin: an extra
// turn for the drawing only (the fit stays in frame). o.keep(b): boxes that stay drawn (a billboard's picture) but still
// count for the fit. o.skip(b): boxes that aren't the prop's at all (the crate you climb into a truck by): left as they'd
// be outside it, not counted. o.v: variant, o.t: tint. fn may set o.frame / o.spin / o.t while it builds (read after)
export function propOf(id, at, frame, fn, o = {}) {
  const got = [];
  CAP.push(got);
  try { fn(); } finally { CAP.pop(); }
  if (o.frame !== undefined) frame = o.frame; // (a turn only known once built: a palm's lean, a pine's tiers)
  const c = Math.cos(frame), s = Math.sin(frame), lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  let owner = null;
  for (const [b, list] of got) {
    if (o.skip && o.skip(b)) { seen(b, list); continue; } // (as if added outside: an outer prop's, or a one-box prop of its own)
    if (!(o.keep && o.keep(b))) { b.pv = id; if (!owner && list.props) owner = list; }
    const cx = (b.min[0] + b.max[0]) / 2, cz = (b.min[2] + b.max[2]) / 2, hx = (b.max[0] - b.min[0]) / 2, hz = (b.max[2] - b.min[2]) / 2;
    const br = b.rot || 0, bc = Math.cos(br), bs = Math.sin(br);
    for (const dx of [-hx, hx]) for (const dz of [-hz, hz]) { // its corners (a turned deco box turns round its centre) in the prop's frame
      const px = cx + dx * bc + dz * bs - at[0], pz = cz - dx * bs + dz * bc - at[2];
      const lx = px * c - pz * s, lz = px * s + pz * c;
      if (lx < lo[0]) lo[0] = lx; if (lx > hi[0]) hi[0] = lx; if (lz < lo[2]) lo[2] = lz; if (lz > hi[2]) hi[2] = lz;
    }
    if (b.min[1] - at[1] < lo[1]) lo[1] = b.min[1] - at[1];
    if (b.max[1] - at[1] > hi[1]) hi[1] = b.max[1] - at[1];
  }
  if (!owner) return null; // (nothing it would draw)
  const p = { id, a: [at[0], at[1], at[2]], y: frame + (o.spin || 0), lo, hi };
  if (o.spin) p.f = frame; // (the fit's own frame, when the drawing turns on top of it)
  if (o.v !== undefined) p.v = o.v;
  if (o.t !== undefined) p.t = o.t;
  owner.props.push(p);
  return p;
}
