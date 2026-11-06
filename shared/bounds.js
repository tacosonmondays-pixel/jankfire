// The play area. Maps with a big walkable outside (Suburb, Warehouse) set map.bounds = [x0, z0, x1, z1]: step out of it
// and you get OOB.secs to come back before the server kills you (a void death, so whoever shoved you out gets it).
// Shared so the server's kill, the client's countdown and the bots all agree on where the edge is.
export const OOB = { secs: 3, grace: 0.35 }; // grace: the server waits a little longer than the countdown (lag)

// map.ceiling (optional, bomb maps): feet above it count as out too, so the roofs and tall stacks you could grapple onto
// don't become perches over the sites
export function outOfBounds(map, p) {
  if (map && map.ceiling != null && p[1] > map.ceiling) return true;
  const b = map && map.bounds;
  return !!b && (p[0] < b[0] || p[0] > b[2] || p[2] < b[1] || p[2] > b[3]);
}
// how far inside the play area a point is (negative = outside by that much)
export function boundsDepth(map, p) {
  const b = map && map.bounds;
  return b ? Math.min(p[0] - b[0], b[2] - p[0], p[2] - b[1], b[3] - p[2]) : 1e9;
}
export function boundsCenter(map) {
  const b = map.bounds;
  return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
}
