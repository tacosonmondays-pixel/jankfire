// The pre-game area (owner, 2026-11-13): pick a mode with a lobby (PLANT & DEFUSE, JANK ROYALE, ZOMBIES) and the lobby's
// countdown happens on a small deck floating off the edge of the match's map, with the map out there in the distance.
// everyone in the match is on it: run, jump, grapple, spray, shove each other about. nothing hurts. a big board shows
// the top 3 here by their record in this mode. when the countdown's up everyone goes to their real spawns.
// shared by the server (bounds, spawns, bots' floor, the board) and the client (the same boxes to walk on, the board).
// where the deck goes is worked out from the map itself (nothing per map to keep up to date) and cached.
export const PREGAME = {
  w: 26, d: 18, // the deck (m): x by z
  rail: 1.1, // the low wall round the edge (jump it and you're put back)
  lift: 14, // the deck floor: this far over the map's highest spawn
  gap: 22, // at least this far past the play area's edge
  out: 4, // past the deck's edge by this much (or `drop` below it, `up` above it): back on the deck
  drop: 7, up: 60,
  shove: { cd: 650, range: 3.4, push: 12, lift: 5 }, // the harmless shove: knockback only, no damage (rate-limited)
  board: { every: 1000 }, // ms between the server's board checks (it only sends when it changes)
};
// how it looks: rotates by the week (Monday to Sunday, UTC). one look for now; a new one goes on the end and the
// rotation picks it up. id: what the client builds (PR 2: the Blender deck)
export const LOOKS = [{ id: 'deck', name: 'THE OVERLOOK' }];
export function lookFor(t = Date.now()) { const wk = Math.floor((t / 864e5 + 3) / 7); return LOOKS[((wk % LOOKS.length) + LOOKS.length) % LOOKS.length].id; } // (day 0 was a Thursday: +3 starts weeks on Monday)
// emotes: the hook. an id here becomes a valid 'emote' message (the server rate-limits and relays it); none yet
export const EMOTES = {};
export const EMOTE = { cd: 1500 };
// the stat the big board ranks by, per lobby kind (shared/modestats.js has the stats). zombies: highest round
export const BOARD_STAT = { bomb: 'rw', br: 'wins', zm: 'round', qp: 'kills' };

const cache = new WeakMap();
const hits = (b, lo, hi) => b.min[0] < hi[0] && b.max[0] > lo[0] && b.min[1] < hi[1] && b.max[1] > lo[1] && b.min[2] < hi[2] && b.max[2] > lo[2];
const box = (x0, y0, z0, x1, y1, z1, k) => ({ min: [x0, y0, z0], max: [x1, y1, z1], pg: k }); // pg: which part (the client's placeholder colours)
// the deck for a map: { c: [x, floorY, z], boxes, spawns, board: {p, yaw}, look, face (yaw that looks at the map) }
export function padFor(map) {
  if (!map) return null;
  let pad = cache.get(map);
  if (pad) return pad;
  const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  for (const b of map.boxes) {
    if (b.max[0] - b.min[0] > 400 || b.max[2] - b.min[2] > 400) continue; // (the sea / the ground plane)
    for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], b.min[i]); hi[i] = Math.max(hi[i], b.max[i]); }
  }
  const B = map.bounds; // the play area if the map has one (the rest is scenery you can walk on)
  const x0 = B ? B[0] : lo[0], x1 = B ? B[2] : hi[0], z1 = B ? B[3] : hi[2];
  const { w, d, lift, gap, rail } = PREGAME;
  const fy = Math.round(Math.max(0, ...map.spawns.map((s) => s[1])) + lift);
  const cx = Math.round((x0 + x1) / 2);
  // out past the +z edge, the nearest spot where nothing of the map is in the way (deck, rails, the board, headroom)
  let cz = z1 + gap + d / 2;
  for (let i = 0; i < 80; i++, cz += 6) {
    const a = [cx - w / 2 - 4, fy - 2, cz - d / 2 - 4], b = [cx + w / 2 + 4, fy + 14, cz + d / 2 + 4];
    if (!map.boxes.some((x) => hits(x, a, b))) break;
  }
  cz = Math.round(cz);
  const X0 = cx - w / 2, X1 = cx + w / 2, Z0 = cz - d / 2, Z1 = cz + d / 2, t = 0.3;
  const boxes = [
    box(X0, fy - 1, Z0, X1, fy, Z1, 'floor'),
    box(X0, fy, Z0, X1, fy + rail * 0.6, Z0 + t, 'rail'), // (the side facing the map: lower, so you can see over it)
    box(X0, fy, Z1 - t, X1, fy + rail, Z1, 'rail'),
    box(X0, fy, Z0, X0 + t, fy + rail, Z1, 'rail'),
    box(X1 - t, fy, Z0, X1, fy + rail, Z1, 'rail'),
    box(cx - 5.5, fy, Z1 - 1.6, cx + 5.5, fy + 0.5, Z1 - t, 'step'), // the board's base: a step to stand on
    box(cx - 5, fy + 0.5, Z1 - 1.1, cx + 5, fy + 6.5, Z1 - 0.5, 'board'), // the big board (faces the deck and the map)
    box(X0 + 2, fy, Z1 - 4, X0 + 3.4, fy + 1.4, Z1 - 2.6, 'crate'), // a couple of crates to hop on
    box(X1 - 3.6, fy, Z1 - 3.8, X1 - 2.2, fy + 1.4, Z1 - 2.4, 'crate'),
    box(X1 - 3.4, fy + 1.4, Z1 - 3.6, X1 - 2.4, fy + 2.4, Z1 - 2.6, 'crate'),
  ];
  const spawns = [];
  for (let i = 0; i < 16; i++) spawns.push([cx - 9 + (i % 4) * 6 + ((i >> 2) % 2) * 1.5, fy, cz - 5.5 + (i >> 2) * 2.6]);
  pad = { c: [cx, fy, cz], w, d, boxes, spawns, face: Math.PI, // (yaw PI looks down -z: at the map)
    board: { p: [cx, fy + 3.5, Z1 - 1.12], yaw: Math.PI }, lo: [X0, fy, Z0], hi: [X1, fy, Z1] };
  cache.set(map, pad);
  return pad;
}
// is p (feet) somewhere it shouldn't be: off the deck past its edge, fallen below it, or flown off above it
export function offPad(pad, p) {
  const o = PREGAME.out;
  return p[0] < pad.lo[0] - o || p[0] > pad.hi[0] + o || p[2] < pad.lo[2] - o || p[2] > pad.hi[2] + o || p[1] < pad.c[1] - PREGAME.drop || p[1] > pad.c[1] + PREGAME.up;
}
// the board's rows from what each player's account has (their inv.ms when they joined, plus this session's batch):
// [{ id, name, v (null: unranked), lvl, bot }] best first, 3 at most. the best of whoever's there: ranked people first,
// then unranked people by level, bots last
export function boardRows(kind, players) {
  const own = Object.hasOwn(BOARD_STAT, kind), key = own ? BOARD_STAT[kind] : BOARD_STAT.qp, ms = own ? kind : 'qp', mx = key === 'round' || key === 'streak' || key === 'far';
  const rows = players.map((p) => {
    const a = p.inv && p.inv.ms && p.inv.ms[ms], b = p.msd && p.msd[ms];
    const av = a && Number.isFinite(a[key]) ? a[key] : 0, bv = b && Number.isFinite(b[key]) ? b[key] : 0;
    const v = p.isBot || !p.acct ? 0 : mx ? Math.max(av, bv) : av + bv;
    return { id: p.id, name: String(p.name || '').slice(0, 20), v: v > 0 ? Math.round(v) : null, lvl: p.level | 0, bot: p.isBot ? 1 : 0 };
  });
  rows.sort((a, b) => (b.v || 0) - (a.v || 0) || a.bot - b.bot || b.lvl - a.lvl || a.id - b.id);
  return rows.slice(0, 3);
}
