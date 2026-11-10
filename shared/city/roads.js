// The slice's road net (the GTA side: driving) and pavements (the crowd's extras), for the systems lane:
//   chunk lanes  { kind: 'road', id, pts: [[x, y, z], ...], w, dir: 1 | 2 } (dir 1 = one way, along pts)
//                { kind: 'walk', id, pts, w }
//   chunk marks  { id: 'park', p, yaw, road }  kerbside parking (cars spawn here)
// RAW() is the network as designed (from the plan). tools/city/gta_index.mjs drives a car-sized box along every road
// and a walker along every pavement against the real collision, keeps the clear runs (split where something's in the
// way, heights fitted to the ground), finds the clear kerb spots and writes shared/city/slice_gta.js. Chunks clip that
// (gtaInto), so it's deterministic and costs nothing at runtime. Re-run the tool when a generator changes (the test
// fails if it's stale).
import { SLICE, hwY } from './slice.js';
import { rampZ } from './kit.js';
import GTA from './slice_gta.js';

const T = SLICE.bottom, zS = (k) => 256 - T.terr * k, yB = (k) => k * T.rise, GY = SLICE.gut.y, H = SLICE.highway;
const AVES = [-286, -234, -182, -130, -44, 8, 60], STREETS = [-232, -188, -100, -60];
const line = (a, b, step = 6) => { const L = Math.hypot(b[0] - a[0], b[2] - a[2]), n = Math.max(1, Math.round(L / step)), o = []; for (let i = 0; i <= n; i++) { const t = i / n; o.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]); } return o; };

// the Bottom's slip road: terrace 1's lane runs off the hill's east end down a ramp onto the Commute's ground, then
// along to the ring road's start (the terraces are metres above the wasteland: this is the one way down for a car)
export const SLIP = { z: zS(1) - 2.7, x0: 96, x1: 118, rect: [96, zS(1) - 8, 210, zS(1) + 1], ex: H.x0 - 8, sz: H.zLow + 4 };
SLIP.rects = [SLIP.rect, [SLIP.ex - 5, SLIP.z, SLIP.ex + 5, SLIP.sz + 3], [SLIP.ex, SLIP.sz - 3, H.x1, SLIP.sz + 3]]; // (commute.js keeps its junk off all of it)
// the ring road's top turns west into the Gut along here (just north of the Tooth Market, onto avenue 60): gut.js keeps
// its offices off it
export const GUT_LINK = { z: -164, rect: [56, -168.5, 97, -159.5] };
export function slipRoad(B) {
  const z0 = SLIP.z - 2.6, z1 = SLIP.z + 2.6, ya = yB(1), yb = hwY(SLIP.z, true), n = Math.ceil((ya - yb) / 0.12), dx = (SLIP.x1 - SLIP.x0) / n;
  if (B.touches([SLIP.x0, z0, SLIP.x1, z1])) {
    for (let i = 0; i < n; i++) { const x = SLIP.x0 + i * dx; B.add(x, yb - 1, z0, x + dx, ya - (ya - yb) * i / n, z1, 'asphalt', { tint: 0x5a5658 }); }
    for (const z of [z0 - 0.4, z1]) B.add(SLIP.x0, yb, z, SLIP.x1, ya + 0.9, z + 0.4, 'concrete', { tint: 0xd0c8c0 }); // kerbs / crash barriers
  }
  // then south round the ring road's foot: a smooth ramp over the wasteland's half-metre terraces
  if (B.touches([SLIP.ex - 3, z0, SLIP.ex + 3, SLIP.sz])) rampZ(B, SLIP.ex - 2.6, SLIP.ex + 2.6, SLIP.sz, z0, 0, yb, 'asphalt', { tint: 0x5a5658 }); // (from under the turn: flush with the road)
}
// no driving through the landmarks (a road that crosses one is cut there)
export const NODRIVE = [SLICE.lostFound.rect, SLICE.plaza.rect, SLICE.gym.rect, SLICE.teeth.rect, [SLICE.choir.x - 26, SLICE.choir.z - 30, SLICE.choir.x + 26, SLICE.choir.z + 22]];
// the designed network. y is a hint: the tool snaps every point to the ground under it
export function RAW() {
  const roads = [], walks = [];
  // the Bottom: every terrace lane, end to end (one lane each way); terrace 0's runs east onto the ring road
  for (let k = 0; k < T.n; k++) {
    const z = zS(k) - 2.7, y = yB(k); // (toward the lip: the lane's stalls sit at the back)
    if (k > 0) roads.push({ id: 'bottom_lane_' + k, w: 4.8, dir: 2, pts: line([-318, y, z], [k === 1 ? SLIP.x0 : 94, y, z]) }); // (terrace 0's lane is half under the rim)
    walks.push({ id: 'bottom_walk_' + k, w: 1, pts: line([-318, y, zS(k) - 6.3], [94, y, zS(k) - 6.3]) });
  }
  // the old ring road: the jam fills the middle, the hard shoulders are clear (one each way), up to the top and the
  // west turn into the Gut
  const deck = (x, z0, z1) => { const o = []; for (let z = z0; z1 < z0 ? z >= z1 : z <= z1; z += z1 < z0 ? -6 : 6) o.push([x, hwY(z), z]); return o; };
  const sy = hwY(SLIP.z, true), ex = SLIP.ex, sz = SLIP.sz; // (round the ring road's south end: its sides have barriers)
  roads.push({ id: 'slip_road', w: 4.8, dir: 2, pts: [...line([SLIP.x0, yB(1), SLIP.z], [SLIP.x1, sy, SLIP.z], 3), ...line([SLIP.x1, sy, SLIP.z], [ex, sy, SLIP.z]).slice(1), ...line([ex, sy, SLIP.z], [ex, 0, sz]).slice(1), ...line([ex, 0, sz], [H.x1 - 1.6, 0, sz]).slice(1), [H.x1 - 1.6, hwY(H.zLow - 2), H.zLow - 2]] });
  roads.push({ id: 'ring_road_up', w: 3, dir: 1, pts: [...deck(H.x1 - 1.6, H.zLow - 2, H.zTop - 6), [H.x1 - 1.6, H.yTop, GUT_LINK.z]] }); // (up into the west turn)
  roads.push({ id: 'ring_road_down', w: 3, dir: 1, pts: [[H.x0 + 1.6, H.yTop, GUT_LINK.z], ...deck(H.x0 + 1.6, H.zTop - 6, H.zLow - 2), [H.x0 + 1.6, 0, SLIP.sz]] }); // (from the west turn, down onto the slip road)
  const wz = (H.westZ[0] + H.westZ[1]) / 2;
  roads.push({ id: 'ring_west', w: 6, dir: 2, pts: line([H.x1 - 1.6, H.yTop, GUT_LINK.z], [60, GY, GUT_LINK.z]) }); void wz;
  // the Gut: the campus grid (avenues north-south, streets east-west, Rib Avenue through the old time office)
  for (const a of AVES) {
    roads.push({ id: 'gut_ave_' + a, w: 5, dir: 2, pts: line([a, GY, -254], [a, GY, -50]) });
    for (const s of [-1, 1]) walks.push({ id: 'gut_ave_walk_' + a + (s > 0 ? 'e' : 'w'), w: 1, pts: line([a + s * 5.6, GY, -254], [a + s * 5.6, GY, -50]) });
  }
  for (const st of STREETS) {
    roads.push({ id: 'gut_st_' + st, w: 5, dir: 2, pts: line([-318, GY, st], [94, GY, st]) });
    for (const s of [-1, 1]) walks.push({ id: 'gut_st_walk_' + st + (s > 0 ? 's' : 'n'), w: 1, pts: line([-318, GY, st + s * 5.6], [94, GY, st + s * 5.6]) });
  }
  return { roads, walks };
}

// the chunk's share of the checked net (lanes clipped to the chunk by segment midpoint, kerb spots by position)
export function gtaInto(B) {
  if (B.out.city !== 'slice') return;
  for (const [kind, list] of [['road', GTA.roads], ['walk', GTA.walks]]) for (const r of list) {
    let run = null;
    for (let i = 0; i + 1 < r.pts.length; i++) {
      const a = r.pts[i], b = r.pts[i + 1];
      if (B.inside((a[0] + b[0]) / 2, (a[2] + b[2]) / 2)) { if (!run) { run = { kind, id: r.id, w: r.w, ...(kind === 'road' ? { dir: r.dir } : {}), pts: [a] }; B.out.lanes.push(run); } run.pts.push(b); } else run = null;
    }
  }
  for (const k of GTA.park) if (B.inside(k.p[0], k.p[2])) B.out.marks.push({ id: 'park', p: k.p, yaw: k.yaw, road: k.road });
}
// for code that wants the net without building chunks (the sim's worker, the server): roads / walks within r of x, z
export function roadsNear(x, z, r, kind = 'road') {
  const list = kind === 'walk' ? GTA.walks : GTA.roads, out = [];
  for (const l of list) if (l.pts.some((p) => Math.abs(p[0] - x) < r && Math.abs(p[2] - z) < r)) out.push(l);
  return out;
}
