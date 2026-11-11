// REVENUE PROTECTION's arms against the tunnel wall (trainfight.js draws them; this is the look only, the room never
// sees it). pure math, no three, so node can test it. B = { R, cy }: the bore is round about (0, cy), along z
//   - nothing of an arm is drawn outside the bore: the rope's joints are kept in, and a hand that would go through the
//     lining is swung in about its wrist until its fingertips are on the brick, then laid on it (palm out, back in)
//   - the knot (the wrist: where the room judges shots) is never moved. the hand starts 0.4 m past it, as before
//   - the two hauling arms plant their hands flat on the lining, ride it back with the tunnel, and let go (stepHaul)
export const LINE = 0.11; // the lining's header rings stand this far in from the bore (rp_tunnel.glb: 4.49 against 4.6)
export const SEGR = 0.31; // arm_seg's half thickness out toward the wall (rp_arm.glb)
// rp_arm.glb's arm_hand: wrist at the origin, fingers along +z, palm toward -y. palm: its underside · len: to the fingertips
export const HAND = { off: 0.4, palm: 0.42, len: 1.9 };
// points on the hand (its own x, y, z) that must stay in: the palm's four corners underneath, the knuckles' backs, the fingertips
const SAMPLES = [[0.55, -0.42, 0], [-0.55, -0.42, 0], [0.55, -0.42, 0.95], [-0.55, -0.42, 0.95], [0.5, 0.4, 0.5], [-0.5, 0.4, 0.5], [0.55, -0.1, 1.8], [-0.55, -0.1, 1.8], [0, -0.1, 1.9]];
const TIPS = SAMPLES.slice(6);
const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a, f = [0, 0, 1]) => { const l = Math.hypot(a[0], a[1], a[2]); return l > 1e-6 ? [a[0] / l, a[1] / l, a[2] / l] : f.slice(); };
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ss = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
export const rad = (B, p) => Math.hypot(p[0], p[1] - B.cy);
export const inward = (B, p) => norm([-p[0], B.cy - p[1], 0], [0, 1, 0]); // toward the bore's axis
// how far out a rope joint may be drawn: the header rings, less the rope's own thickness (sy: the length's flattening)
export const jointMax = (B, sy = 1) => B.R - LINE - SEGR * sy - 0.02;
export function keepIn(B, p, rmax) { const x = p[0], y = p[1] - B.cy, r = Math.hypot(x, y); if (r <= rmax || r < 1e-6) return p; const k = rmax / r; return [x * k, B.cy + y * k, p[2]]; }
export const flatK = (mouth, k) => (mouth ? 1 : k < 2 ? 0.35 : k < 4 ? 0.35 + 0.325 * (k - 1) : 1); // the first lengths are flat: a whole rope doesn't fit past the rim
// the rope's joints every `seg` metres along a path P ({ pts, wrist }: armPose's): each length is drawn from one to the
// next. every joint but the wrist is kept inside the bore (the wrist is the knot, where the room has it)
export function armJoints(B, P, mouth, seg = 1.5) {
  const pts = P.pts, J = [pts[0]];
  let need = seg, i = 1, cur = pts[0];
  while (i < pts.length && J.length < 46) { // (46: a sweeper at the van's front with the face 22 m back is 60 m of rope; 34 left its knot hanging off the end)
    const q = pts[i], l = Math.hypot(q[0] - cur[0], q[1] - cur[1], q[2] - cur[2]);
    if (l < need) { need -= l; cur = q; i++; continue; }
    const k = need / l; cur = [cur[0] + (q[0] - cur[0]) * k, cur[1] + (q[1] - cur[1]) * k, cur[2] + (q[2] - cur[2]) * k]; J.push(cur); need = seg;
  }
  if (need < seg - 0.05) J.push(P.wrist);
  const n = J.length - 1;
  for (let k = 0; k < n; k++) J[k] = keepIn(B, J[k], jointMax(B, flatK(mouth, Math.min(k, n - 1))));
  return J;
}
// u (the hand's +y, its back) square to f
const square = (u, f, alt) => { const v = add(u, f, -dot(u, f)); return Math.hypot(v[0], v[1], v[2]) > 0.05 ? norm(v) : norm(add(alt, f, -dot(alt, f))); };
export const handPts = (H, pts = SAMPLES) => { const x = cross(H.u, H.f); return pts.map((s) => add(add(add(H.o, x, s[0]), H.u, s[1]), H.f, s[2])); };
const over = (B, H, pts, lim) => Math.max(...handPts(H, pts).map((p) => rad(B, p) - lim));
// where the hand goes for a wrist w pointing along d (unit). up0: its back's way off the wall (world up, as before).
// returns { o (the hand's origin), f (fingers), u (its back), wall (0..1: lying on the wall), tilt, push }
export function handFit(B, w, d, up0 = [0, 1, 0], lim = B.R - LINE) {
  let f = norm(d);
  const nin = inward(B, w), out0 = -dot(f, nin);
  // the nearer the wall, the more it lies on it (unless it is pointing off it, at a rail or at you)
  let wall = ss((rad(B, w) - 3.1) / 0.9) * clamp(1 - Math.max(0, -out0) * 1.6, 0, 1);
  let H = { o: add(w, f, HAND.off), f, u: square(add(up0, nin, 0), f, [0, 0, 1]), wall: 0, tilt: 0, push: 0 };
  const lay = (k) => square(add(up0, add(nin, up0, -1), k), H.f, nin);
  H.u = lay(wall);
  if (over(B, H, TIPS, lim) > 0) { // the fingers would go through: swing it in about the wrist, back to the axis, until they touch
    wall = 1;
    const p = square(nin, f, [0, 0, 1]), at = (a) => { const g = norm(add(f.map((x) => x * Math.cos(a)), p, Math.sin(a))); const h = { o: add(w, g, HAND.off), f: g, u: square(nin, g, [0, 0, 1]) }; return h; };
    let lo = 0, hi = 1.6;
    if (over(B, at(hi), TIPS, lim) > 0) lo = hi; else for (let i = 0; i < 14; i++) { const m = (lo + hi) / 2; if (over(B, at(m), TIPS, lim) > 0) lo = m; else hi = m; }
    H = { ...at(hi), tilt: hi, push: 0 };
  }
  H.wall = wall;
  for (let i = 0; i < 4; i++) { const e = over(B, H, SAMPLES, lim) + 1e-4; if (e <= 1e-4) break; H.push += e; H.o = add(H.o, inward(B, H.o), e); } // whatever still sticks out (the palm on the brick): the whole hand comes in
  return H;
}

// ---------------------------------------------------------------- the haul: two arms that walk the face up the tunnel
// the lining (trainset.js lays rp_tunnel.glb's 6 m pieces at z0 + 6 J - dist): every piece has a proud ring at its start,
// a niche piece (J % 4 == 1) a manhole low on the left, a lining_b piece (J % 4 == 3) a drain pipe down the right wall.
// a hand is planted where none of them is under it
export const KIT = { seg: 6, ring: [-0.08, 0.55], niche: [2.35, 3.95], pipe: [3.15, 3.45] };
export function plantOk(z0, dist, side, a, b) { // the hand covers z a..b on the wall, on the left (side < 0) or the right
  for (let J = Math.floor((a - z0 + dist) / KIT.seg) - 1; J <= Math.floor((b - z0 + dist) / KIT.seg) + 1; J++) {
    const s = z0 + KIT.seg * J - dist, k = ((J % 4) + 4) % 4, bad = [KIT.ring];
    if (k === 1 && side < 0) bad.push(KIT.niche); if (k === 3 && side > 0) bad.push(KIT.pipe);
    for (const [p, q] of bad) if (a < s + q && b > s + p) return false;
  }
  return true;
}
export const HAUL = { ahead: 10.5, let: 2.6, reach: 0.6, off: 0.18, skid: 0.28, skidT: 0.14, lift: 0.95, hold: 1.6, back: 0.2, front: 1.95 }; // where it plants (ahead of the face) and lets go · seconds to reach, to peel off · how far it skids as the fingers bite · how far off the wall at the top of a reach · the most a hand holds · the hand's reach behind / in front of its wrist
// the nearest z to `want` where a planted hand (and its skid) has clean brick under it
export function plantZ(want, z0, dist, side) {
  const ok = (z) => plantOk(z0, dist, side, z - HAUL.skid - HAUL.back, z + HAUL.front);
  for (let i = 0; i <= 80; i++) for (const s of i ? [1, -1] : [1]) { const z = want + s * i * 0.1; if (ok(z)) return z; }
  return want;
}
// one arm's step. h: its state (newHaul). c: { dt, run (how far the tunnel has gone, all told), face (the face's z),
// z0 / dist (where the kit's pieces are), side, a (its wall angle), v (the tunnel's speed), other (the other arm's state), lead (this one goes first) }. returns 'plant', 'let' or ''
export const newHaul = (i, face) => ({ ph: i ? 'reach' : 'let', t: i ? 0.25 : 0, z: face + 5, lift: 0.5, a: 0, from: { z: face + 5, lift: 0.5, a: 0 }, zT: face + 9, runT: 0, zP: 0, run0: 0, prog: 0 });
export function stepHaul(h, c) {
  h.t += c.dt; let ev = '';
  if (h.ph === 'grip') {
    const ride = c.run - h.run0;
    h.z = h.zP - ride - HAUL.skid * ss(h.t / HAUL.skidT); h.lift = 0;
    h.prog = clamp((h.zP - h.z) / Math.max(1, h.zP - (c.face + HAUL.let)), 0, 1);
    if (h.z < c.face + HAUL.let || h.t > HAUL.hold) { h.ph = 'let'; h.t = 0; ev = 'let'; }
  } else if (h.ph === 'let') { // it peels off: still dragged a little by the brick, lifting, the fingers letting go
    const k = ss(h.t / HAUL.off);
    // it reaches again once the other hand has hold (hand over hand; if both have let go, the lead one goes first), or if that takes too long
    if (h.t < HAUL.off) h.z -= (c.v || 0) * c.dt * (1 - k * 0.6); h.lift = HAUL.lift * 0.45 * k; h.prog = 0;
    if (h.t >= HAUL.off && (!c.other || c.other.ph === 'grip' || (c.other.ph === 'let' && c.lead) || h.t > HAUL.off + 0.6)) { h.ph = 'reach'; h.t = 0; h.from = { z: h.z, lift: h.lift, a: h.a }; h.aT = c.a + (Math.random() - 0.5) * 0.12; h.zT = plantZ(c.face + HAUL.ahead + c.v * HAUL.reach, c.z0, c.dist, c.side); h.runT = c.run; }
  } else { // reach: up off the wall, forward, and slammed down on a spot that is coming at it with the tunnel
    const u = clamp(h.t / HAUL.reach, 0, 1), zT = h.zT - (c.run - h.runT), e = 1 - (1 - u) ** 3;
    h.z = h.from.z + (zT - h.from.z) * e; h.lift = h.from.lift * (1 - u) + HAUL.lift * Math.sin(Math.PI * u ** 0.8) ** 0.7; h.a = h.from.a + ((h.aT ?? c.a) - h.from.a) * ss(u); h.prog = 0;
    if (u >= 1) { h.ph = 'grip'; h.t = 0; h.zP = zT; h.run0 = c.run; h.lift = 0; ev = 'plant'; }
  }
  if (!h.a) h.a = c.a;
  return ev;
}
// the hand of a hauling arm: planted flat (palm on the brick, fingers up the tunnel), or lifted off it by h.lift
export function haulHand(B, h) {
  const n = [Math.cos(h.a), Math.sin(h.a), 0], nin = [-n[0], -n[1], 0], r = B.R - HAND.palm - 0.04 - h.lift; // (0.04: the palm is flat, the wall is round)
  const pitch = h.ph === 'reach' ? 0.32 * Math.sin(Math.PI * clamp(h.t / HAUL.reach, 0, 1)) : h.ph === 'let' ? 0.25 * ss(h.t / HAUL.off) : 0; // (the fingers lift first on a reach)
  const f = norm([nin[0] * pitch, nin[1] * pitch, 1]);
  return { o: [r * n[0], B.cy + r * n[1], h.z], f, u: square(nin, f, [0, 1, 0]), wall: 1, tilt: 0, push: 0 };
}
// a hauling arm's rope: off the rim (S, the socket), along the wall, to the wrist (W) at wall angle aw. bow: how far its
// middle bends in off the wall (an elbow, as the face hauls itself up to the hand)
export function haulPath(B, S, W, aw, bow = 0, n = 16) {
  let a0 = Math.atan2(S[1] - B.cy, S[0]);
  while (a0 - aw > Math.PI) a0 -= Math.PI * 2; while (aw - a0 > Math.PI) a0 += Math.PI * 2;
  const r0 = rad(B, S), rw = jointMax(B, 1), rW = rad(B, W), aW = Math.atan2(W[1] - B.cy, W[0]), out = [];
  let a1 = aW; while (a1 - aw > Math.PI) a1 -= Math.PI * 2; while (aw - a1 > Math.PI) a1 += Math.PI * 2;
  for (let i = 0; i <= n; i++) {
    const u = i / n, z = S[2] + (W[2] - S[2]) * u, an = a0 + (a1 - a0) * ss(u * 2.2);
    let r = u < 0.2 ? r0 + (rw - r0) * ss(u / 0.2) : u > 0.75 ? rw + (rW - rw) * ss((u - 0.75) / 0.25) : rw;
    r -= bow * Math.sin(Math.PI * u) ** 1.2;
    out.push(i === n ? W.slice() : [r * Math.cos(an), B.cy + r * Math.sin(an), z]);
  }
  return out;
}
