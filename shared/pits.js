// Pits with something in them: map.pits = [{ kind: 'lava', box: [x0, z0, x1, z1], top, bot }]. feet inside the box
// below top = you're in it. lava burns (damage over time, then a little afterburn once you're out), the server deals it
// (server/pits.js). the rest of a map's long drops end where the map says they do: map.fall names what's down there
// ('river' the Desert's canyon, 'street' the rooftops), map.sea the sea, and killY sits at that surface, so nobody
// falls through the scenery any more. shared so the server, the bots and the client's lines agree.
export const PIT = { lava: { dmg: 10, every: 0.25, burn: 1.6, burnDmg: 4, burnEvery: 0.3, erupt: 17, sink: 0.45, drag: 4, under: 1.75 } }; // dmg per tick while you're in it, s between ticks, s of afterburn, how hard what's left of you comes back out

// deep sea (map.seaY = its surface): you don't drop through it like air, you sink. slow enough to grapple back out,
// and you're gone as your head goes under (killY sits there). the client does this to you, the server to its bots
export const SINK = { v: 1.7, from: 0.6 }; // m/s you go down at, how far under the surface your feet are before it holds you (the wading shallows are shallower than that)
export function sink(map, pos, vel) {
  if (map && map.seaY != null && pos[1] < map.seaY - SINK.from && vel[1] < -SINK.v) vel[1] = -SINK.v;
}
// the end of a long drop (the river, the street, the sea bed): you stop there. the server's kill takes a moment to
// arrive and at 60 m/s that moment used to be several metres of falling on through the scenery (client only)
export function bottomOut(map, pos, vel) {
  if (!map || (!map.fall && map.seaY == null) || pos[1] >= map.killY - 0.1) return;
  pos[1] = map.killY - 0.1; vel[0] = vel[1] = vel[2] = 0;
}
// lava is deep and thick: you don't stand in it, you go down into it, slowly (PIT.lava.sink m/s), burning all the way,
// and it has you by the legs (drag). a grapple still pulls you out. feet PIT.lava.under below its surface = your head's
// gone under, and so are you (the server's call: server/pits.js). the client does the sinking to you, the server to its bots
export function mire(map, pos, vel, dt, hooked) {
  const q = inPit(map, pos);
  if (!q || q.kind !== 'lava') return false;
  const L = PIT.lava;
  if (vel[1] < -L.sink) vel[1] = -L.sink;
  if (!hooked) { const k = Math.max(0, 1 - L.drag * dt); vel[0] *= k; vel[2] *= k; }
  return true;
}
export const pitUnderLine = (q) => q.top - 0.1 - PIT.lava.under; // (q.top sits 0.1 over the lava's surface)
export function inPit(map, p) {
  const s = map && map.pits;
  if (!s) return null;
  for (const q of s) if (p[1] < q.top && p[1] > q.bot && p[0] > q.box[0] && p[0] < q.box[2] && p[2] > q.box[1] && p[2] < q.box[3]) return q;
  return null;
}
// is there a pit under (x, z), below y? (bots look before they step: a pit has a floor now, so "nothing down there" no longer warns them)
export function pitUnder(map, x, y, z, m = 0.3) {
  const s = map && map.pits;
  if (!s) return null;
  for (const q of s) if (y > q.bot && x > q.box[0] - m && x < q.box[2] + m && z > q.box[1] - m && z < q.box[3] + m) return q;
  return null;
}
