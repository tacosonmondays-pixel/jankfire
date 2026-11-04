// Bokken katana skin: the one-piece wooden practice sword (bokuto), standard kendo/aikido daito
// (the Aramaki "standard" pattern made for the AJKF kata). Akagashi red oak, 102 cm overall: 26 cm tsuka
// (a 3.6 x 2.6 cm oval), 76 cm blade with a 1.2 cm torii-zori (one arc through the whole sword). Standard-pattern
// details: flat spine (hira-mine), flat butt, small kissaki (~2.4 cm); an egg-shaped section with a soft shinogi
// ridge and a blunt rounded ha.
// A black plastic tsuba (7.8 cm x 6.5 mm) is wedged at the front of the tsuka with a white rubber tsubadome
// in front of it. No habaki, no wrap, no pins: it is all one piece of wood.
// refs: Nine Circles Red Oak Daito (102 / 76 / 26 cm, sori 1.2 cm, tsuka 2.5 x 3.5 cm), Seido standard bokken
// (101.5 / 75.5 / 26 cm, tsuka 37 x 26 mm; flat spine, flat butt, small kissaki), Wikipedia "Bokken" (AJKF kata
// tachi ~102 cm), Seido + KuSakura plastic tsuba (7.7-7.8 cm across, ~6 mm thick, hole 2.5 x 3.5 cm).
// No source gives the blade's own height/thickness: 3.4 x 2.4 cm at the tsuba (it has to pass the 2.5 x 3.5 cm
// tsuba hole) tapering to 2.95 x 1.85 cm at the yokote (~3/4" mid-blade, as Little Raven lists) are estimates.
// contract: userData.katBlade = a group at the front face of the tsuba holding only the wooden blade, pointing -Z;
// userData.katLen = its origin to the tip. The katana grows with kills by scaling katBlade.scale.z.
import { plate, mat, THREE } from './kit.js';

const WOOD = 0xb8714a, GRIP = 0xa8643f, END = 0x86492b; // red oak; the handled tsuka a shade darker; end grain
const TSUBA = 0x1c1c1f, DOME = 0xe6e1d6;                 // black plastic tsuba, white rubber tsubadome

// side view: the sword is one gentle arc (radius R), tangent to the grip axis at z = 0, rising towards the tip
const R = 4.65;                        // 1.2 cm of sori (mune to the chord from the tsuba to the point) over the 76 cm blade
const yc = (z) => (z * z) / (2 * R);
const nrm = (z) => { const a = -z / R, l = Math.hypot(a, 1); return [a / l, 1 / l]; }; // unit normal (z, y), spine side
const at = (z, u) => { const [nz, ny] = nrm(z); return [z + nz * u, yc(z) + ny * u]; }; // u metres off the centre line

const Z_BUTT = 0.13, Z_GUARD = -0.13, TSUBA_T = 0.0065, Z_BLADE = Z_GUARD - TSUBA_T / 2;
const Z_TIP = -0.89, KISSAKI = 0.024;              // 102 cm overall; a small kissaki, 2.4 cm from the yokote to the point
const H0 = 0.034, W0 = 0.024, HY = 0.0295, WY = 0.0185; // blade height (edge -> spine) and thickness: at the tsuba, at the yokote
const U_TIP = 0.28;                                // the point sits 78% of the way up from the edge, under the mune line
// kissaki stations: [s along the fukura curve, thickness as a fraction of WY]. It thins much faster than the body, so
// its faces turn in at the yokote, and the last ones round the point off (a bokken point is blunt)
const KISSAKI_ST = [[0.14, 0.93], [0.28, 0.86], [0.42, 0.78], [0.56, 0.7], [0.69, 0.61], [0.8, 0.52], [0.89, 0.43], [0.95, 0.3]];

// half cross-sections, from the spine (v = 1) round one side to the edge (v = 0): [v, x as a fraction of half the thickness]
// blade: a flat mune (the top band), chamfers, the shinogi ridge (widest, 68% up), the hira-ji easing in to a rounded ha
const BLADE_SEC = [[1, 0], [1, 0.5], [0.955, 0.8], [0.85, 0.97], [0.68, 1], [0.4, 0.86], [0.15, 0.54], [0.04, 0.3], [0, 0]];
// tsuka (and the tsubadome): a plain oval
const OVAL_SEC = [[1, 0], [0.985, 0.48], [0.93, 0.82], [0.82, 0.98], [0.62, 1], [0.38, 0.99], [0.18, 0.93], [0.07, 0.76], [0.015, 0.44], [0, 0]];

const V = (p) => new THREE.Vector3(p[0], p[1], p[2]);
// one triangle into pos/uv, wound so its normal points away from ref
function tri(pos, uv, pts, uvs, ref) {
  const [a, b, c] = pts.map(V);
  const n = new THREE.Vector3().crossVectors(b.clone().sub(a), c.clone().sub(a));
  if (n.lengthSq() < 1e-14) return;
  const out = a.clone().add(b).add(c).multiplyScalar(1 / 3).sub(V(ref));
  for (const k of n.dot(out) < 0 ? [0, 2, 1] : [0, 1, 2]) { pos.push(...pts[k]); uv.push(...uvs[k]); }
}
// loft a section along stations [{ S: [z, y], E: [z, y], w }] (spine point, edge point, full thickness).
// caps: { start, end } close that end with material 1 (end grain). uv: u round the section, v along it (10 cm a tile)
function loft(st, sec, colors, caps = {}) {
  const ring = (s) => {
    const P = ([v, xr], sx) => [sx * xr * s.w / 2, s.E[1] + (s.S[1] - s.E[1]) * v, s.E[0] + (s.S[0] - s.E[0]) * v];
    const r = sec.map((p) => P(p, 1));
    for (let k = sec.length - 2; k >= 1; k--) r.push(P(sec[k], -1));
    return r;
  };
  const rings = st.map(ring), n = rings[0].length;
  const mid = (i) => [0, (st[i].S[1] + st[i].E[1]) / 2, (st[i].S[0] + st[i].E[0]) / 2];
  const vAt = [0];
  for (let i = 1; i < st.length; i++) { const a = mid(i - 1), b = mid(i); vAt.push(vAt[i - 1] + Math.hypot(b[1] - a[1], b[2] - a[2]) / 0.1); }
  const pos = [], uv = [], cpos = [], cuv = [];
  for (let i = 0; i < st.length - 1; i++) {
    const a = mid(i), b = mid(i + 1), ref = [0, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
    for (let k = 0; k < n; k++) {
      const k1 = (k + 1) % n, u0 = k / n, u1 = (k + 1) / n;
      const A = rings[i][k], B = rings[i][k1], C = rings[i + 1][k1], D = rings[i + 1][k];
      tri(pos, uv, [A, B, C], [[u0, vAt[i]], [u1, vAt[i]], [u1, vAt[i + 1]]], ref);
      tri(pos, uv, [A, C, D], [[u0, vAt[i]], [u1, vAt[i + 1]], [u0, vAt[i + 1]]], ref);
    }
  }
  const cap = (i, j) => { // fan over ring i, facing away from station j
    const c = mid(i), ref = mid(j), q = (p) => [p[0] / 0.05, p[1] / 0.05];
    for (let k = 0; k < n; k++) { const A = rings[i][k], B = rings[i][(k + 1) % n]; tri(cpos, cuv, [c, A, B], [q(c), q(A), q(B)], ref); }
  };
  if (caps.start) cap(0, 1);
  if (caps.end) cap(st.length - 1, st.length - 2);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute([...pos, ...cpos], 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute([...uv, ...cuv], 2));
  geo.addGroup(0, pos.length / 3, 0);
  geo.addGroup(pos.length / 3, cpos.length / 3, 1);
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, [mat(colors[0]), mat(colors[1] ?? colors[0])]);
}
const station = (z, h, w) => ({ S: at(z, h / 2), E: at(z, -h / 2), w });
const lerp = (a, b, t) => a + (b - a) * t;
const bez = (p0, p1, p2, s) => [0, 1].map((k) => (1 - s) * (1 - s) * p0[k] + 2 * (1 - s) * s * p1[k] + s * s * p2[k]);

export function build(g) {
  // ---- tsuka: the handle is the same piece of wood, an oval a touch fuller at the butt, flat-cut end with a small chamfer
  g.add(loft([
    station(Z_BUTT, 0.032, 0.022),
    station(Z_BUTT - 0.002, 0.036, 0.026),
    station(0, 0.0355, 0.0255),
    station(Z_GUARD, 0.035, 0.025),
    station(Z_GUARD - 0.003, 0.035, 0.025), // runs on under the tsuba
  ], OVAL_SEC, [GRIP, END], { start: true }));

  // ---- tsuba: plain round plastic disc, wedged where the tsuka meets the blade
  const circ = [];
  for (let i = 0; i < 24; i++) { const a = (i / 24) * Math.PI * 2; circ.push([Math.cos(a) * 0.038, Math.sin(a) * 0.038]); }
  const tsuba = plate(circ, TSUBA_T - 0.002, TSUBA, { z: Z_GUARD, bevel: 0.001 });
  tsuba.position.y = yc(Z_GUARD);
  g.add(tsuba);

  // ---- tsubadome: the rubber ring that keeps the tsuba from sliding up the blade
  const zd = Z_BLADE;
  g.add(loft([
    station(zd, 0.042, 0.032),
    station(zd - 0.0125, 0.042, 0.032),
    station(zd - 0.0145, 0.0385, 0.0285),
  ], OVAL_SEC, [DOME], { end: true }));

  // ---- the blade (katBlade): body from the tsuba to the yokote, then the kissaki
  // zp = where the unblunted point would be; solved below so the blunted point lands exactly on Z_TIP
  const stations = (zp) => {
    const zy = zp + KISSAKI, st = [];
    const NB = 10;
    for (let k = 0; k <= NB; k++) {
      const f = k / NB, z = lerp(Z_BLADE + 0.001, zy, f);
      st.push(station(z, lerp(H0, HY, f), lerp(W0, WY, f)));
    }
    // kissaki: the edge sweeps up (fukura) and the mune line rounds down a little to meet it at the point.
    // the curves are [t along the kissaki 0..1, u across in heights (+0.5 = mune line, -0.5 = edge line)]
    const zEnd = zp - nrm(zp)[0] * U_TIP * HY, kz = (t) => lerp(zy, zEnd, t);
    for (const [s, wf] of KISSAKI_ST) {
      const sp = bez([0, 0.5], [0.5, 0.5], [1, U_TIP], s), ed = bez([0, -0.5], [0.4, -0.5], [1, U_TIP], s);
      st.push({ S: at(kz(sp[0]), sp[1] * HY), E: at(kz(ed[0]), ed[1] * HY), w: WY * wf });
    }
    return st;
  };
  const tipOf = (st) => { const l = st[st.length - 1]; return [(l.S[0] + l.E[0]) / 2, (l.S[1] + l.E[1]) / 2]; }; // centre of the blunt end
  let zp = Z_TIP;
  zp += Z_TIP - tipOf(stations(zp))[0];
  const st = stations(zp);
  const blade = loft(st, BLADE_SEC, [WOOD, END], { end: true });
  blade.geometry.translate(0, 0, -Z_BLADE);
  const bl = new THREE.Group();
  bl.position.z = Z_BLADE;
  bl.add(blade);
  g.add(bl);

  const [tz, ty] = tipOf(st);
  g.userData.katBlade = bl;
  g.userData.katLen = Z_BLADE - tz;
  g.userData.muzzle = new THREE.Vector3(0, ty, tz);
  g.userData.len = Z_BUTT - tz;
}
// the hat sits on top of the tsuka, over the hand
export const hatAt = [[0, 0.0178, 0.05], 0.06];
