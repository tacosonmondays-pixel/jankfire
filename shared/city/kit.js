// The story city's building kit: pieces the district generators (bottom.js, gut.js, commute.js) share. Everything
// takes the chunk builder B (chunk.js chunkBuilder) and world coordinates, and is deterministic given its rng.
// Collision is always boxes; the look comes from tints, render-only trims (nc), shapes and Blender props.

export const PASTEL = [0xffb3c7, 0xffe58a, 0x5fd3c6, 0xb6f2c8, 0xd2b6ff, 0xffc8a0, 0xa8e6ff, 0xff9ec0];
export const pick = (r, a) => a[(r() * a.length) | 0];

// how far a flight runs for a rise of dy (stairsZ / stairsX steps: <= 0.4 m up, 0.55 m deep)
export const flightLen = (dy) => Math.max(1, Math.ceil(Math.abs(dy) / 0.4)) * 0.55;

// a flight of steps along z (dir +1 / -1) or x: from (x0..x1) at a0, rising ya -> yb. returns where it ends
export function stairsZ(B, x0, x1, a0, dir, ya, yb, mat = 'concrete', o) {
  const n = Math.max(1, Math.ceil(Math.abs(yb - ya) / 0.4)), h = (yb - ya) / n, run = 0.55;
  for (let i = 1; i <= n; i++) { const za = a0 + dir * (i - 1) * run, zb = a0 + dir * i * run; B.add(x0, Math.min(ya, yb) - 0.2, za, x1, ya + i * h, zb, mat, o); }
  return a0 + dir * n * run;
}
export function stairsX(B, z0, z1, a0, dir, ya, yb, mat = 'concrete', o) {
  const n = Math.max(1, Math.ceil(Math.abs(yb - ya) / 0.4)), h = (yb - ya) / n, run = 0.55;
  for (let i = 1; i <= n; i++) { const xa = a0 + dir * (i - 1) * run, xb = a0 + dir * i * run; B.add(xa, Math.min(ya, yb) - 0.2, z0, xb, ya + i * h, z1, mat, o); }
  return a0 + dir * n * run;
}
// a smooth-looking ramp for wheels and feet: 0.12 m steps (under the 0.6 m step-up, so you just run up it)
export function rampZ(B, x0, x1, z0, z1, y0, y1, mat = 'asphalt', o) {
  const L = Math.abs(z1 - z0), n = Math.max(1, Math.ceil(Math.abs(y1 - y0) / 0.12)), dz = (z1 - z0) / n;
  for (let i = 0; i < n; i++) B.add(x0, Math.min(y0, y1) - 1.5, z0 + dz * i, x1, y0 + (y1 - y0) * (i + 1) / n, z0 + dz * (i + 1), mat, o);
  return L;
}

// a hollow cube house on a 2 m-ish grid: walls with a door on `door` side (0 -z, 1 +x, 2 +z, 3 -x), windows,
// a slab roof you can stand on (the next house stacks on it). w/d/h in metres. container = corrugated walls
export function cube(B, x, y, z, w, d, h, r, o = {}) {
  const t = 0.25, x0 = x - w / 2, x1 = x + w / 2, z0 = z - d / 2, z1 = z + d / 2;
  const tint = o.tint ?? pick(r, PASTEL), mat = o.container ? 'container' : 'plaster';
  const sides = [[0, x0, x1, z0, 'x'], [2, x0, x1, z1, 'x'], [3, z0, z1, x0, 'z'], [1, z0, z1, x1, 'z']];
  const ops = [[], [], [], []], hung = []; // for the kit pass (cubeKit): each side's openings, and what already hangs in a window
  for (const [side, a0, a1, f, ax] of sides) {
    const len = a1 - a0, mid = (a0 + a1) / 2;
    const openings = [];
    if (side === o.door) openings.push([mid - 0.6, mid + 0.6, 0, 2.2]);
    else if (len > 3 && r() < 0.8) { const c = mid + (r() - 0.5) * (len - 3); openings.push([c - 0.7, c + 0.7, 1.0, 2.1]); }
    if (o.open === side) openings.length = 0, openings.push([a0 + 0.3, a1 - 0.3, 0, h - 0.4]); // a shopfront: the whole side open
    ops[side] = openings;
    const seg = (s0, s1, y0, y1) => {
      if (s1 - s0 < 0.05 || y1 - y0 < 0.05) return;
      const fo = side === 0 || side === 3 ? 0 : -t;
      if (ax === 'x') B.add(s0, y + y0, f + fo, s1, y + y1, f + fo + t, mat, { tint, l0: true });
      else B.add(f + fo, y + y0, s0, f + fo + t, y + y1, s1, mat, { tint, l0: true });
    };
    let s = a0;
    for (const [oa, ob, oy0, oy1] of openings.sort((p, q) => p[0] - q[0])) { seg(s, oa, 0, h); seg(oa, ob, 0, oy0); seg(oa, ob, oy1, h); s = ob; }
    seg(s, a1, 0, h);
    // window glow (render only, a hair inside the opening) + a frame prop
    for (const [oa, ob, oy0, oy1] of openings) if (oy0 > 0.5) {
      const c = (oa + ob) / 2, inset = side === 0 || side === 3 ? t * 0.6 : -t * 0.6;
      if (ax === 'x') B.add(oa, y + oy0, f + inset, ob, y + oy1, f + inset + 0.02, r() < 0.6 ? 'window' : 'glass', { nc: true });
      else B.add(f + inset, y + oy0, oa, f + inset + 0.02, y + oy1, ob, r() < 0.6 ? 'window' : 'glass', { nc: true });
      if (o.props !== false && r() < 0.5) {
        const yaw = [0, -Math.PI / 2, Math.PI, Math.PI / 2][side], out = 0.02;
        const px = ax === 'x' ? c : f + (side === 1 ? out : -out), pz = ax === 'x' ? f + (side === 2 ? out : -out) : c;
        const pid = r() < 0.5 ? 'shutter' : 'acunit', low = r() < 0.5; // (same draws, same order as ever: id, height, colour)
        B.prop(pid, px, y + (low ? oy0 - 0.1 : oy1 + 0.2), pz, yaw, 1, (r() * 8) | 0);
        hung.push([side, oa, pid, low]);
      }
    }
    if (side === o.door && o.props !== false) {
      const yaw = [0, -Math.PI / 2, Math.PI, Math.PI / 2][side];
      B.prop('door_bottom', ax === 'x' ? mid : f, y, ax === 'x' ? f : mid, yaw, 1, (r() * 8) | 0);
    }
  }
  B.add(x0, y - 0.15, z0, x1, y + 0.12, z1, 'concrete'); // floor
  B.add(x0 - 0.1, y + h, z0 - 0.1, x1 + 0.1, y + h + 0.3, z1 + 0.1, o.roofMat || 'concrete', { tint: o.roofTint }); // roof = the next floor
  B.add(x0, y, z0, x1, y + h, z1, mat, { l1: true, tint }); // far away: one box (the mid ring draws this instead of the walls)
  if (o.lit !== false && r() < 0.55) B.light(x + (r() - 0.5) * w, y + h * 0.6, (o.door === 0 ? z0 - 1.2 : z1 + 1.2), pick(r, [0xffc070, 0xffb060, 0xff9ad0, 0x9ae0ff]), 6, 0.55); // a lit window spills out
  return { x0, x1, z0, z1, top: y + h + 0.3, y, h, tint, roofTint: o.roofTint || 0, container: !!o.container, ops, hung };
}

// an outside stair up the side of a house: from y0 to y1 along side 1 (+x) or 3 (-x), running along z
export function sideStair(B, cx, y0, y1, z0, dir, mat = 'metal', o) {
  const end = stairsZ(B, cx - 0.6, cx + 0.6, z0, dir, y0, y1, mat);
  B.add(cx - 0.6, y1 - 0.15, Math.min(end, end + dir * 1.2), cx + 0.6, y1, Math.max(end, end + dir * 1.2), mat); // landing
  if (!o || o.rail !== false) B.add(cx + 0.62, y0, Math.min(z0, end), cx + 0.68, y1 + 1, Math.max(z0, end), 'metal', { nc: true }); // rail (look only; stairKit's posts replace it)
  return end;
}

// a sagging line between two points: a tube shape (drawn) + optional hanging props + a zipline trigger
export function line(B, a, b, o = {}) {
  const n = 6, sag = o.sag ?? Math.hypot(b[0] - a[0], b[2] - a[2]) * 0.06, pts = [];
  for (let i = 0; i <= n; i++) { const t = i / n; pts.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - Math.sin(t * Math.PI) * sag, a[2] + (b[2] - a[2]) * t]); }
  B.shape({ kind: 'tube', pts, r: o.r || 0.03, seg: 4, mat: o.mat || 'metal', tint: o.tint, step: 2, lod: false, at: a });
  if (o.zip && B.inside((a[0] + b[0]) / 2, (a[2] + b[2]) / 2)) B.out.triggers.push({ kind: 'zip', a, b, sag }); // stored once: by the chunk holding its middle
  const L = Math.hypot(b[0] - a[0], b[2] - a[2]), yaw = Math.atan2(-(b[2] - a[2]), b[0] - a[0]);
  if (o.hang) for (let s = 1.6; s < L - 1.4; s += 3.2) {
    const t = s / L, y = a[1] + (b[1] - a[1]) * t - Math.sin(t * Math.PI) * sag;
    B.prop(o.hang[((s * 7) | 0) % o.hang.length], a[0] + (b[0] - a[0]) * t, y, a[2] + (b[2] - a[2]) * t, yaw, 1, (s * 13) | 0);
  }
  return pts;
}
// festoon bulbs: the cable + glowing bulb blobs every metre
export function bulbs(B, a, b, r) {
  const pts = line(B, a, b, { r: 0.02, mat: 'metal', sag: Math.hypot(b[0] - a[0], b[2] - a[2]) * 0.08 });
  const cols = [0xffe14d, 0xff4fd8, 0x4fd8ff, 0xffb070, 0x7dff4f];
  const L = Math.hypot(b[0] - a[0], b[2] - a[2]), sag = L * 0.08;
  for (let s = 0.8; s < L; s += 1.1) {
    const t = s / L, y = a[1] + (b[1] - a[1]) * t - Math.sin(t * Math.PI) * sag - 0.12;
    const col = pick(r, cols);
    B.shape({ kind: 'blob', c: [a[0] + (b[0] - a[0]) * t, y, a[2] + (b[2] - a[2]) * t], r: 0.09, seg: 4, mat: 'neon', tint: col, lod: false });
    if (((s * 10) | 0) % 3 === 0) B.light(a[0] + (b[0] - a[0]) * t, y - 0.3, a[2] + (b[2] - a[2]) * t, col, 9, 0.9);
  }
  return pts;
}

// a retaining wall along x at z (the face toward +z, i.e. downhill to the south) from y0 up to y1, with buttresses
export function retaining(B, x0, x1, z, y0, y1, r, mat = 'concrete') {
  B.add(x0, y0 - 1, z - 1.2, x1, y1, z, mat, { tint: 0xd8c8c0 });
  for (let x = x0 + 4 + r() * 4; x < x1 - 2; x += 7 + r() * 6) B.add(x, y0, z, x + 0.8, y1 - 0.5 - r(), z + 0.6, mat, { tint: 0xc8b8b0 });
  // graffiti and patches: render-only paint panels just proud of the face
  for (let x = x0 + 2; x < x1 - 3; x += 9 + r() * 9) if (r() < 0.6) B.add(x, y0 + 0.5, z + 0.01, x + 2 + r() * 3, y0 + 1.2 + r() * (y1 - y0 - 1.5), z + 0.03, 'paint', { nc: true, tint: pick(r, [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff7a1a]) });
}

// rubble: a heap of tilted concrete chunks (render only) on one collision box
export function rubble(B, x, y, z, s, r) {
  B.add(x - s * 0.5, y, z - s * 0.5, x + s * 0.5, y + s * 0.35, z + s * 0.5, 'rubble', { hide: true });
  for (let i = 0; i < 4 + s * 2; i++) {
    const a = r() * 6.283, d = r() * s * 0.45, sz = 0.4 + r() * s * 0.35;
    B.obb(x + Math.cos(a) * d, y + sz * 0.3 + r() * s * 0.15, z + Math.sin(a) * d, sz * (1 + r()), sz * (0.4 + r() * 0.6), sz, r() * 3.14, r() < 0.2 ? 'brick' : 'rubble', { tint: r() < 0.3 ? pick(r, PASTEL) : 0 });
  }
  if (r() < 0.4) B.obb(x, y + s * 0.3, z, 0.08, 0.08, s, r() * 3.14, 'rust'); // rebar
}

// a market stall: counter + canopy (tarp prop or a tie-dye canopy box)
export function stall(B, x, y, z, yaw4, r) {
  const L = B.local(x, z, yaw4, y);
  L(-1.4, 0, -0.6, 1.4, 1.0, 0.6, 'wood');
  L(-1.5, 2.3, -1.0, 1.5, 2.4, 1.0, 'tiedye', { nc: true });
  for (const sx of [-1.4, 1.4]) L(sx - 0.05, 0, -0.95, sx + 0.05, 2.3, -0.85, 'metal', { nc: true });
  L.P(pick(r, ['crate_soup', 'crate_soup', 'fridge', 'pchair']), 0, 1.0, 0, r() * 6.28, 0.6 + r() * 0.2, (r() * 8) | 0);
}

// a grapple anchor (DESIGN: the districts are grapple playgrounds): a glowing yellow ring you can read from 90 m on a
// short bracket, with an invisible collision block round it so the rope (which hooks collision boxes) bites on it.
// s = block size (bigger is easier to hit), yaw = which way the ring faces, host = 'hang' (ring under the point) or
// 'side'. a 'grapple' mark tells the bots and tools/city/grapple.mjs where the anchors are. kept by the chunk holding it
export function hook(B, x, y, z, o = {}) {
  if (!B.inside(x, z)) return;
  const s = o.s || 1.4, yaw = o.yaw || 0, R = 0.62, c = Math.cos(yaw), sn = Math.sin(yaw), pts = [];
  B.add(x - s / 2, y - s / 2, z - s / 2, x + s / 2, y + s / 2, z + s / 2, 'metal', { hide: true });
  for (let i = 0; i <= 10; i++) { const a = (i / 10) * Math.PI * 2, u = Math.cos(a) * R; pts.push([x + u * c, y - 0.75 + Math.sin(a) * R, z - u * sn]); }
  B.shape({ kind: 'tube', pts, r: 0.1, seg: 5, mat: 'glow', tint: 0xffe14d, step: 0.5, at: [x, y, z] }); // (kept in the mid ring too: readable far off)
  B.add(x - 0.06, y - 0.15, z - 0.06, x + 0.06, y + 0.25, z + 0.06, 'metal', { nc: true, tint: 0x3a3a44 }); // the bracket
  B.out.marks.push({ id: 'grapple', p: [x, y, z], s });
}

// ---------------------------------------------------------------- the cube kit (Blender dressing, visual props only)
// tools/blender/make_story_cubekit.py: every piece sits ON the boxes at a spot worked out from the cube, so no box
// moves. all randoms come from the caller's own stream r (never the one that laid the boxes).
export const KIT = { on: true }; // (off: the generators place none of it. tests/story/bottomkit.test.mjs builds both ways)
const YAW4 = [0, -Math.PI / 2, Math.PI, Math.PI / 2]; // a model's front (-z) turned to face out of side 0..3
const PAINT = [0xc8202c, 0x2050b0, 0xe8e8e8, 0x26262a, 0x2a8a4a, 0xe8c020, 0xff7ab0, 0x5fd3c6]; // public/js/city/props.js PAINTS: the only colours a prop's paint slot takes
// the paint variant nearest a tint (a prop can't carry a hex yet), and how far off it is
export function paintOf(tint) {
  let best = 0, bd = 1e9;
  for (let i = 0; i < PAINT.length; i++) { const d = Math.hypot((PAINT[i] >> 16) - (tint >> 16), ((PAINT[i] >> 8) & 255) - ((tint >> 8) & 255), (PAINT[i] & 255) - (tint & 255)); if (d < bd) bd = d, best = i; }
  return [best, bd];
}
// dress one cube (what cube() returned). hid(x, y, z, c) = is this point inside something solid other than c: pieces
// on a face with a wall right in front of it are skipped (nobody can stand there to see them).
// o, per side 0..3: on (dress this side at all), corner (a post on the corner it fronts), eave (chance of a lip);
// stair [x, z0, z1] (an outside stair hugs that side)
export function cubeKit(B, c, r, hid, o = {}) {
  const { x0, x1, z0, z1, y, h } = c;
  const at = (side, a, out = 0) => (side === 0 ? [a, z0 - out] : side === 2 ? [a, z1 + out] : side === 3 ? [x0 - out, a] : [x1 + out, a]);
  const seen = (side, a, yy) => { const p = at(side, a, 0.45), q = at(side, a, 1.0); return !hid(p[0], yy, p[1], c) && !hid(q[0], yy, q[1], c); };
  const put = (id, side, a, yy, s, v) => { const p = at(side, a); B.prop(id, p[0], yy, p[1], YAW4[side], s, v); };
  const [pv, pd] = paintOf(c.tint), rv = c.roofTint ? paintOf(c.roofTint)[0] : pv;
  const long = x1 - x0 >= z1 - z0 ? 0 : 1; // which pair of sides is the long one (0: the x walls, 1: the z walls)
  for (let side = 0; side < 4; side++) {
    const [a0, a1] = side % 2 ? [z0, z1] : [x0, x1], mid = (a0 + a1) / 2, ops = c.ops[side];
    if (o.on && !o.on[side]) continue;
    const stair = o.stair && ((side === 1 && o.stair[0] > x1) || (side === 3 && o.stair[0] < x0)) ? o.stair : null;
    // windows: a frame with a life in it on every 1.4 x 1.1 opening (not where a shutter already fills it)
    for (const [oa, ob, oy0] of ops) if (oy0 > 0.5) {
      const id = 'cube_window_' + 'bbbbbbaaac'[(r() * 10) | 0], v = (r() * 8) | 0, // (mostly the cheap one; c is 620 triangles)
        hg = c.hung.find((q) => q[0] === side && q[1] === oa);
      if (hg && hg[3] && hg[2] === 'shutter') continue;
      if (seen(side, (oa + ob) / 2, y + oy0 + 0.5)) put(hg && hg[3] ? 'cube_window_a' : id, side, (oa + ob) / 2, y + oy0, 1, v); // (an ac unit in it: the flat barred one)
    }
    // the corner whose front is this side: boards, a downpipe, a meter box (scaled so its top buries in the slab)
    const ca = side < 2 ? a0 : a1, cd = side < 2 ? 1 : -1;
    if ((!o.corner || o.corner[side]) && ops.every(([oa, ob]) => (cd > 0 ? oa - a0 : a1 - ob) > 1.15) && !(stair && ca > stair[2] - 1.2 && ca < stair[1] + 1.6) && seen(side, ca + cd * 0.5, y + 1.5)) put('cube_corner', side, ca, y, (h + 0.05) / 3.1, 0);
    // a tin lip under the roof slab in 2 m runs (the last one overlaps back from the far end)
    if (r() < (o.eave ? o.eave[side] : 1)) for (let a = a0 + 1; a < a1 + 0.99; a += 2) {
      const e = Math.min(a, a1 - 1);
      if (stair && e > stair[2] - 1.4 && e < stair[1] + 1.4) continue; // (it would poke through the steps)
      if (seen(side, e, y + h - 0.3)) put('cube_eave', side, e, y + h, 1, rv);
    }
    if (!c.container) continue;
    if ((side % 2) === long) { // ribs at 1 m steps along a container's long walls, cut round the openings
      const s = h / 2.8; let from = a0;
      for (const [oa, ob, oy0] of [...ops, [a1, a1, 0]]) {
        const to = oa - (oy0 > 0.5 ? 0.16 : 0.02), n = Math.floor((to - from) / s);
        for (let i = 0; i < n; i++) { const a = from + (to - from - n * s) / 2 + (i + 0.5) * s; if (seen(side, a, y + 1.4)) put('container_rib', side, a, y, s, pv); }
        from = ob + (oy0 > 0.5 ? 0.16 : 0.02);
      }
    } else { // the doors on a short end, when nothing is cut in its middle
      const s = (h - 0.15) / 2.6, hw = 1.2 * s + 0.15;
      if (a1 - a0 > 2 * hw && ops.every(([oa, ob]) => ob < mid - hw || oa > mid + hw) && seen(side, mid, y + 1.3)) put('container_doors', side, mid, y, s, pv);
    }
  }
}
// treads and railing posts on a sideStair (same numbers as stairsZ): one of each per step, posts down the open side.
// steps squeezed into the wall next door get neither
export function stairKit(B, cx, y0, y1, z0, dir, out, v, hid) {
  const n = Math.max(1, Math.ceil(Math.abs(y1 - y0) / 0.4)), dy = (y1 - y0) / n, yaw = dir < 0 ? Math.PI : 0;
  for (let i = 1; i <= n; i++) {
    const z = z0 + dir * (i - 1) * 0.55, yy = y0 + i * dy;
    if (hid && (hid(cx, yy + 0.6, z + dir * 0.27) || hid(cx + out * 0.75, yy + 0.6, z + dir * 0.27))) continue; // (a neighbour's wall has this step, or half of it)
    B.prop('stair_step', cx, yy, z, yaw, 1, 0);
    B.prop('stair_post', cx + out * 0.58, yy, z, yaw, 1, v);
  }
}
