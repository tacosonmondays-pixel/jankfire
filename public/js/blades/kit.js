// Blade kit: knives and swords built from real silhouettes instead of boxes.
// Model space is the same as every weapon: tip/forward = -Z, up = +Y, the grip at the origin, thickness along X.
// Blades are drawn edge down: spine on top (+Y), cutting edge at the bottom (-Y).
// Side-view profiles are lists of [z, y] points in metres; real sizes, so a 10 cm blade is 0.10 long.
import * as THREE from 'three';
import { M } from '../models.js';

export { THREE };
// flat-shaded material (shared + PS1 wobble). glow = unlit, for bits that should shine (also tag those noWrap)
export const mat = (color, glow = false) => M(color, glow);

// ---------------------------------------------------------------- 2D helpers (side view, [z, y])
// smooth curve through control points (Catmull-Rom), n points out
export function curve(ctrl, n = 16, tension = 0.5) {
  const c = new THREE.CatmullRomCurve3(ctrl.map((p) => new THREE.Vector3(p[0], p[1], 0)), false, 'catmullrom', tension);
  return c.getPoints(Math.max(2, n) - 1).map((v) => [v.x, v.y]);
}
// points on a circular arc round (cz, cy). angles in radians: 0 = +z (towards the handle end), PI/2 = +y (up)
export function arc(cz, cy, r, a0, a1, n = 8) {
  const out = [];
  for (let i = 0; i < n; i++) { const a = a0 + (a1 - a0) * (i / (n - 1)); out.push([cz + Math.cos(a) * r, cy + Math.sin(a) * r]); }
  return out;
}
// n points spread evenly along a polyline's length
export function resample(pts, n) {
  const acc = [0];
  for (let i = 1; i < pts.length; i++) acc.push(acc[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const L = acc[acc.length - 1] || 1, out = [];
  for (let k = 0; k < n; k++) {
    const s = (k / (n - 1)) * L;
    let i = 1;
    while (i < acc.length - 1 && acc[i] < s) i++;
    const t = (s - acc[i - 1]) / ((acc[i] - acc[i - 1]) || 1);
    out.push([pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t]);
  }
  return out;
}
const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
// side-on planar uvs: u along the blade (z), v up (y), about 4 texture repeats per metre
const sideUV = (pos) => { const uv = []; for (let i = 0; i < pos.length; i += 3) uv.push(-pos[i + 2] * 4, pos[i + 1] * 4); return new THREE.Float32BufferAttribute(uv, 2); };

// ---------------------------------------------------------------- the blade generator
// spine/edge: [z, y] lines from the heel (handle end) to the tip. They may meet at the tip (pointed) or not (blunt front, e.g. a cleaver).
// The flat (primary) face runs from the spine down to the grind line, then a bevel thins it out to the cutting edge.
// o = {
//   spine, edge,              required
//   thick = 0.004,            spine thickness at the heel (real knives 3-5 mm)
//   grind = 0.4,              where the bevel starts, as a fraction of the height above the edge (1 = full flat grind, 0.15 = small sabre grind)
//   taper = 0.55,             distal taper: thickness at the tip = thick * (1 - taper)
//   edgeThick = 0.0005,       the cutting edge isn't zero, so it still renders
//   color = 0xc9ced6,         flat faces + spine
//   edgeColor = 0xe9edf2,     bevel faces (they catch the light differently)
//   n = 28,                   stations along the length
//   bands: [{ from, to, color, s0 = 0, s1 = 1, glow }]  painted bands that sit on the blade's surface on both sides:
//          from/to = heights as a fraction of edge->spine (0 = edge, 1 = spine), a number or a function of s (0 heel .. 1 tip);
//          s0/s1 = where along the blade they run. Use them for a katana hamon (wavy white band at the edge), fullers, etching.
// }
export function blade(o) {
  const n = o.n || 28;
  const S = resample(o.spine, n), E = resample(o.edge, n);
  const thick = o.thick ?? 0.004, taper = o.taper ?? 0.55, grind = Math.min(1, Math.max(0.02, o.grind ?? 0.4)), et = (o.edgeThick ?? 0.0005) / 2;
  const half = (i) => (thick * (1 - taper * (i / (n - 1)))) / 2;
  // surface point at height v (0 edge .. 1 spine) on side sx (+1/-1) at station i
  const surf = (i, v, sx, lift = 0) => {
    const [sz, sy] = S[i], [ez, ey] = E[i], t = half(i), e = Math.min(et, t);
    const x = v >= grind ? t : e + (t - e) * (v / grind);
    return [sx * (x + lift), ey + (sy - ey) * v, ez + (sz - ez) * v];
  };
  const flat = [], bev = [];
  const center = (i) => [0, (S[i][1] + E[i][1]) / 2, (S[i][0] + E[i][0]) / 2];
  const tri = (out, a, b, c, ref) => {
    const A = v3(a), B = v3(b), C = v3(c);
    const nrm = new THREE.Vector3().crossVectors(B.clone().sub(A), C.clone().sub(A));
    if (nrm.lengthSq() < 1e-16) return;
    const cen = A.clone().add(B).add(C).multiplyScalar(1 / 3).sub(v3(ref));
    if (nrm.dot(cen) < 0) out.push(...a, ...c, ...b); else out.push(...a, ...b, ...c);
  };
  const ring = (i) => { // cross-section: S+, S-, G+, G-, E+, E-
    const t = half(i), e = Math.min(et, t);
    const [sz, sy] = S[i], [ez, ey] = E[i];
    const gz = ez + (sz - ez) * grind, gy = ey + (sy - ey) * grind;
    return [[t, sy, sz], [-t, sy, sz], [t, gy, gz], [-t, gy, gz], [e, ey, ez], [-e, ey, ez]];
  };
  const R = [];
  for (let i = 0; i < n; i++) R.push(ring(i));
  const strips = [[0, 1, flat], [0, 2, flat], [1, 3, flat], [2, 4, bev], [3, 5, bev], [4, 5, bev]];
  for (let i = 0; i < n - 1; i++) {
    const c0 = center(i), c1 = center(i + 1), ref = [0, (c0[1] + c1[1]) / 2, (c0[2] + c1[2]) / 2];
    for (const [a, b, out] of strips) {
      tri(out, R[i][a], R[i][b], R[i + 1][b], ref);
      tri(out, R[i][a], R[i + 1][b], R[i + 1][a], ref);
    }
  }
  // end caps: the heel always, the front if spine and edge don't meet there
  const cap = (i, j) => {
    const r = R[i], ci = center(i), cj = center(j);
    const ref = [ci[0] * 2 - cj[0], ci[1] * 2 - cj[1], ci[2] * 2 - cj[2]]; // a point beyond the cap, outside
    const poly = [r[0], r[2], r[4], r[5], r[3], r[1]];
    const mid = [0, ci[1], ci[2]];
    for (let k = 0; k < poly.length; k++) {
      const a = poly[k], b = poly[(k + 1) % poly.length];
      // orient so the normal points away from the blade (towards ref)
      const A = v3(mid), B = v3(a), C = v3(b);
      const nrm = new THREE.Vector3().crossVectors(B.clone().sub(A), C.clone().sub(A));
      if (nrm.lengthSq() < 1e-16) continue;
      const out = new THREE.Vector3(ref[0] - ci[0], ref[1] - ci[1], ref[2] - ci[2]);
      if (nrm.dot(out) < 0) flat.push(...mid, ...b, ...a); else flat.push(...mid, ...a, ...b);
    }
  };
  cap(0, 1);
  if (Math.hypot(S[n - 1][0] - E[n - 1][0], S[n - 1][1] - E[n - 1][1]) > 0.001) cap(n - 1, n - 2);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute([...flat, ...bev], 3));
  geo.setAttribute('uv', sideUV([...flat, ...bev]));
  geo.addGroup(0, flat.length / 3, 0);
  geo.addGroup(flat.length / 3, bev.length / 3, 1);
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, [mat(o.color ?? 0xc9ced6), mat(o.edgeColor ?? 0xe9edf2)]);
  if (o.x) mesh.position.x = o.x;
  if (!o.bands || !o.bands.length) return mesh;
  // painted bands, lying on the blade surface (a hair above it)
  const g = new THREE.Group(); g.add(mesh);
  for (const b of o.bands) {
    const fv = typeof b.from === 'function' ? b.from : () => b.from, tv = typeof b.to === 'function' ? b.to : () => b.to;
    const s0 = b.s0 ?? 0, s1 = b.s1 ?? 1, pos = [];
    for (let i = 0; i < n - 1; i++) {
      const sa = i / (n - 1), sb = (i + 1) / (n - 1);
      if (sb < s0 || sa > s1) continue;
      // split the band at the grind line so each piece stays on one plane
      const cuts = (s) => { const a = Math.max(0, fv(s)), z = Math.min(1, tv(s)); return a < grind && z > grind ? [[a, grind], [grind, z]] : [[a, z]]; };
      const pa = cuts(sa), pb = cuts(sb);
      for (let k = 0; k < Math.min(pa.length, pb.length); k++) {
        for (const sx of [1, -1]) {
          const A = surf(i, pa[k][0], sx, 0.00025), B = surf(i, pa[k][1], sx, 0.00025);
          const C = surf(i + 1, pb[k][1], sx, 0.00025), D = surf(i + 1, pb[k][0], sx, 0.00025);
          const ref = [0, (A[1] + C[1]) / 2, (A[2] + C[2]) / 2];
          tri(pos, A, B, C, ref); tri(pos, A, C, D, ref);
        }
      }
    }
    if (!pos.length) continue;
    const bg = new THREE.BufferGeometry();
    bg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    bg.setAttribute('uv', sideUV(pos));
    bg.computeVertexNormals();
    const bm = new THREE.Mesh(bg, mat(b.color, b.glow));
    if (b.glow) bm.userData.noWrap = true;
    if (o.x) bm.position.x = o.x;
    g.add(bm);
  }
  return g;
}

// ---------------------------------------------------------------- extrusions
const shapeOf = (pts, holes) => {
  const s = new THREE.Shape(pts.map((p) => new THREE.Vector2(p[0], p[1])));
  for (const h of holes || []) s.holes.push(new THREE.Path(h.map((p) => new THREE.Vector2(p[0], p[1]))));
  return s;
};
// side-view shape ([z, y] points) extruded across the knife (along X), centred on o.x.
// handles, scales, liners, bolsters, spines, flat guards seen from the side. o = { x, holes: [[[z,y]...]], bevel, glow }
// bevel rounds the edges a little (adds that much on every side).
export function slab(pts, thick, color, o = {}) {
  const geo = new THREE.ExtrudeGeometry(shapeOf(pts, o.holes), {
    depth: thick, bevelEnabled: !!o.bevel, bevelThickness: o.bevel || 0, bevelSize: o.bevel || 0, bevelSegments: 1, curveSegments: 6, steps: 1,
  });
  geo.translate(0, 0, -thick / 2);
  geo.rotateY(-Math.PI / 2); // shape x -> model z, extrusion -> model x
  const m = new THREE.Mesh(geo, mat(color, o.glow));
  m.position.x = o.x || 0;
  if (o.glow) m.userData.noWrap = true;
  return m;
}
// front-view shape ([x, y] points, looking down the blade) extruded along the blade (Z), centred on o.z.
// crossguards, a katana tsuba (with holes), ferrules, pommel caps. o = { z, holes, bevel, glow }
export function plate(pts, depth, color, o = {}) {
  const geo = new THREE.ExtrudeGeometry(shapeOf(pts, o.holes), {
    depth, bevelEnabled: !!o.bevel, bevelThickness: o.bevel || 0, bevelSize: o.bevel || 0, bevelSegments: 1, curveSegments: 8, steps: 1,
  });
  geo.translate(0, 0, -depth / 2);
  const m = new THREE.Mesh(geo, mat(color, o.glow));
  m.position.z = o.z || 0;
  if (o.glow) m.userData.noWrap = true;
  return m;
}
// round parts turned around the blade axis: profile [[radius, z], ...]. o = { segs = 8, sx = 1, sy = 1 (oval), x, y, phase, glow }
export function lathe(prof, color, o = {}) {
  const geo = new THREE.LatheGeometry(prof.map((p) => new THREE.Vector2(Math.max(0, p[0]), p[1])), o.segs || 8, o.phase || 0);
  geo.rotateX(Math.PI / 2); // lathe axis (y) -> z
  geo.scale(o.sx || 1, o.sy || 1, 1);
  const m = new THREE.Mesh(geo, mat(color, o.glow));
  m.position.set(o.x || 0, o.y || 0, 0);
  if (o.glow) m.userData.noWrap = true;
  return m;
}

// ---------------------------------------------------------------- small parts
export function box(w, h, d, color, x = 0, y = 0, z = 0, glow = false) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(color, glow));
  m.position.set(x, y, z);
  if (glow) m.userData.noWrap = true;
  return m;
}
// cylinder along Z
export function cyl(r, len, color, x = 0, y = 0, z = 0, segs = 8, glow = false) {
  const g = new THREE.CylinderGeometry(r, r, len, segs); g.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(g, mat(color, glow));
  m.position.set(x, y, z);
  if (glow) m.userData.noWrap = true;
  return m;
}
// pin / rivet / screw head: a short cylinder across the knife (along X)
export function pin(r, len, color, x = 0, y = 0, z = 0, segs = 8) {
  const g = new THREE.CylinderGeometry(r, r, len, segs); g.rotateZ(Math.PI / 2);
  const m = new THREE.Mesh(g, mat(color));
  m.position.set(x, y, z);
  return m;
}
export function sphere(r, color, x = 0, y = 0, z = 0, glow = false) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, 8, 6), mat(color, glow));
  m.position.set(x, y, z);
  return m;
}
// a ring (torus). axis 'x' = the hole goes across the knife (a karambit finger ring), 'z' = round the blade axis, 'y' = vertical
export function ring(R, r, color, o = {}) {
  const geo = new THREE.TorusGeometry(R, r, o.tubeSegs || 6, o.segs || 14);
  if ((o.axis || 'x') === 'x') geo.rotateY(Math.PI / 2);
  else if (o.axis === 'y') geo.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(geo, mat(color, o.glow));
  m.position.set(o.x || 0, o.y || 0, o.z || 0);
  return m;
}
// a bar from point a to point b ([x,y,z]): cords, wraps, teeth, braces. w = width, h = thickness, up = which way its h points
export function strip(a, b, w, h, color, up = [0, 1, 0]) {
  const A = v3(a), B = v3(b), len = A.distanceTo(B);
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, Math.max(1e-4, len)), mat(color));
  m.position.copy(A).add(B).multiplyScalar(0.5);
  m.up.set(up[0], up[1], up[2]);
  m.lookAt(B);
  return m;
}
// a tube along a smooth 3D path ([[x,y,z]...]): cords, lanyards, bent wire
export function tube(path, r, color, o = {}) {
  const c = new THREE.CatmullRomCurve3(path.map(v3), !!o.closed);
  const m = new THREE.Mesh(new THREE.TubeGeometry(c, o.segs || path.length * 4, r, o.radial || 5, !!o.closed), mat(color, o.glow));
  return m;
}
// a group from parts
export function group(...parts) { const g = new THREE.Group(); for (const p of parts) if (p) g.add(p); return g; }
