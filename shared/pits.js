// Pits with something in them: map.pits = [{ kind: 'lava', box: [x0, z0, x1, z1], top, bot }]. feet inside the box
// below top = you're in it. lava burns (damage over time, then a little afterburn once you're out), the server deals it
// (server/pits.js). the rest of a map's long drops end where the map says they do: map.fall names what's down there
// ('river' the Desert's canyon, 'street' the rooftops), map.sea the sea, and killY sits at that surface, so nobody
// falls through the scenery any more. shared so the server, the bots and the client's lines agree.
export const PIT = { lava: { dmg: 15, every: 0.25, burn: 1.6, burnDmg: 4, burnEvery: 0.3, erupt: 17 } }; // dmg per tick while you're in it, s between ticks, s of afterburn, how hard what's left of you comes back out

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
// ponds you can swim in (map.pools = [{ box: [x0, z0, x1, z1], top }], on shaped ground): wade in, and once the bed
// drops away under you the water carries you. you bob with your head out and paddle (slowly: it's air control), a
// plunge from a height takes you under for a moment and brings you back up. client for you, server for its bots
export const SWIM = { ride: 1.45, up: 38, rise: 2.6, plunge: 5.5, drag: 1.6, dive: 2.6 }; // m your feet hang below the surface, how hard it lifts, m/s up and down at most, how fast it eats your speed
export function swim(map, boxes, pos, vel, dt, dive) { // dive: holding crouch = you let yourself go under (down to the bed, where you can walk about, slowly)
  const P = map && map.pools, T = boxes && boxes.terrain;
  if (!P || !T) return false;
  for (const w of P) {
    if (pos[0] < w.box[0] || pos[0] > w.box[2] || pos[2] < w.box[1] || pos[2] > w.box[3]) continue;
    const line = w.top - SWIM.ride, g = T.at(pos[0], pos[2]);
    if (g == null || g >= line - 0.02 || pos[1] > line + 0.02) continue; // standing depth, or up in the air over it
    if (dive) vel[1] = Math.max(-SWIM.dive, vel[1]); // going down, no faster than a sink
    else {
      vel[1] = Math.max(-SWIM.plunge, Math.min(SWIM.rise, vel[1] + SWIM.up * dt));
      if (pos[1] > line - 0.08 && vel[1] > -1.4) { pos[1] = line; vel[1] = 0; } // at the surface: it holds you there
    }
    const k = Math.max(0, 1 - SWIM.drag * dt); vel[0] *= k; vel[2] *= k;
    return true;
  }
  return false;
}
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
