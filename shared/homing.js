// Homing: turn a velocity toward a point by at most maxTurn radians, keeping its speed. Mutates v.
// The server steers slippers with it and clients run the same math between 'pu' updates, so the curve doesn't snap.
const u = [0, 0, 0], h = [0, 0, 0], q = [0, 0, 0]; // scratch: steer runs every frame/tick, don't make garbage
export function steer(v, from, to, maxTurn) {
  const s = Math.hypot(v[0], v[1], v[2]);
  for (let k = 0; k < 3; k++) u[k] = to[k] - from[k];
  const l = Math.hypot(u[0], u[1], u[2]);
  if (s < 1e-6 || l < 1e-6) return v;
  for (let k = 0; k < 3; k++) { h[k] = v[k] / s; u[k] /= l; }
  const c = Math.max(-1, Math.min(1, h[0] * u[0] + h[1] * u[1] + h[2] * u[2]));
  if (Math.acos(c) <= maxTurn) { for (let k = 0; k < 3; k++) v[k] = u[k] * s; return v; }
  // rotate inside the plane of heading and wanted direction
  for (let k = 0; k < 3; k++) q[k] = u[k] - h[k] * c;
  let ql = Math.hypot(q[0], q[1], q[2]);
  if (ql < 1e-6) { q[0] = -h[2]; q[1] = 0; q[2] = h[0]; ql = Math.hypot(q[0], q[2]); } // dead behind: turn sideways
  if (ql < 1e-6) { q[0] = 1; q[1] = 0; q[2] = 0; ql = 1; } // ...or straight up/down
  const cs = Math.cos(maxTurn), sn = Math.sin(maxTurn);
  for (let k = 0; k < 3; k++) v[k] = (h[k] * cs + (q[k] / ql) * sn) * s;
  return v;
}
