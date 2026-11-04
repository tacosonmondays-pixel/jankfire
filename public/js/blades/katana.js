// Katana: an Edo-period (Shinto) shinogi-zukuri uchigatana in full koshirae, built to collector/dealer measurements.
//   Blade: nagasa 70 cm (straight line from the mune-machi to the tip), sori 1.7 cm as one even arc (torii-zori),
//   motohaba 3.1 cm at the machi, sakihaba 2.15 cm at the yokote, kasane 7 -> 5 mm at the shinogi, chu-kissaki 4 cm
//   with its yokote, shinogi ridge 70-74% of the way up from the edge, a peaked iori-mune, a notare/gunome hamon that
//   starts straight at the machi (yakidashi) and runs into a round-turning boshi in the kissaki.
//   Koshirae: gold-washed copper habaki (3.4 cm), a seppa either side of a round iron tsuba (7.8 x 7.4 cm, 5 mm, with
//   kozuka and kogai hitsu-ana), shakudo-black fuchi (1.2 cm) and domed kashira (3.4 cm), a 26 cm tsuka with a slight
//   waist (rikko), white same under dark blue (kon) hira-maki ito with diamond windows, gold menuki staggered
//   (omote = the side that faces left when held edge down, near the tsuba; ura near the kashira), a bamboo mekugi,
//   and the last turn of cord crossing over the kashira into gold shitodome eyelets.
// Refs: NBTHK juyo papers (sori 1.38 cm, motohaba 2.95, sakihaba 2.25 cm on a shinogi-zukuri katana); dealer listings
//   (nagasa 63-70 cm, sori 1.2-1.9 cm, motohaba 3.1-3.2 cm, sakihaba 2.0-2.3 cm, motokasane 6.5-7 mm, sakikasane 5 mm);
//   Hanwei Practical Katana spec (blade 69 cm, handle 28.6 cm, 100 cm overall); kissaki sizes (ko ~3, chu 4-6 cm);
//   museum tsuba averages (7.5 x 8 cm, mimi ~4.8 mm); fuchi ~38-40 mm long axis; menuki placement guides.
// Held edge down in one hand: the tsuka is centred on the grip (z -0.13 .. +0.13, like the other katana skins), the
// blade curves up towards the tip (edge convex, mune concave): the tip sits 8.3 cm above the tsuka axis (6.8 cm above
// the mune at the machi).
// Growth contract: userData.katBlade = a group at the front face of the front seppa (where the habaki starts) holding ONLY
// the blade, pointing -Z; userData.katLen = that origin to the tip. setKatana() stretches katBlade.scale.z and moves
// userData.muzzle.z; the tip height (muzzle.y) never changes. The habaki sits outside katBlade (on g, same place), so it
// stays 3.4 cm long while the blade grows: the blade's stretched root stays hidden inside it.
import { THREE, mat, plate, lathe, pin } from './kit.js';

// ---------------------------------------------------------------- measurements (metres)
const NAGASA = 0.70, SORI = 0.017;            // straight mune-machi -> tip; deepest gap between the mune and that line
const MOTOHABA = 0.031, SAKIHABA = 0.0215;    // blade width (edge to the top of the mune) at the machi / at the yokote
const KASANE0 = 0.0070, KASANE1 = 0.0050;     // thickness across the shinogi, machi -> yokote
const KISSAKI = 0.040;                        // chu-kissaki: yokote to the tip
const RIDGE = 0.0014;                         // iori-mune: the roof's height above its shoulders
const SHINOGI0 = 0.70, SHINOGI1 = 0.74;       // the shinogi line, as a fraction of the width above the edge
const Y0 = 0.0151;                            // top of the mune at the machi (the tsuka axis is y = 0)
const HABAKI = 0.034;
// the mune is one arc of radius R, tangent to the tsuka axis at the machi and curving up
const R = (NAGASA * NAGASA / 4 + SORI * SORI) / (2 * SORI);
const T_TIP = 2 * Math.asin(NAGASA / (2 * R)), T_YOKOTE = T_TIP - KISSAKI / R;
const TIP = [-R * Math.sin(T_TIP), Y0 + R * (1 - Math.cos(T_TIP))]; // [z, y] in the blade group

// tsuka layout along z (model space): the seppa / tsuba / seppa stack sits in front of the fuchi
const Z_FUCHI = -0.130, Z_KASHIRA_END = 0.130;          // 26 cm tsuka, fuchi front to kashira end
const FUCHI_L = 0.012, KASHIRA_L = 0.034, SEPPA_T = 0.002, TSUBA_T = 0.005;
const Z_BLADE = Z_FUCHI - SEPPA_T * 2 - TSUBA_T;      // front face of the front seppa = back of the habaki
const ZW0 = Z_FUCHI + FUCHI_L - 0.0005, ZW1 = Z_KASHIRA_END - KASHIRA_L + 0.0005; // the wrapped part
const PITCH = 0.026;                                     // ito: one crossing per face every 2.6 cm (8 diamonds a side)
const Z_X0 = ZW0 + PITCH / 4;                            // first crossing on the ura (+X) face
const MENUKI_OMOTE = Z_X0 + PITCH * 1.5, MENUKI_URA = Z_X0 + PITCH * 6; // each centred under a crossing
const MENUKI_HALF = 0.023;

// ---------------------------------------------------------------- colours
const HAMON = 0xf4f6f8, JI = 0xb4bcc6, SHINOGIJI = 0x87929f, MUNE = 0x96a0ac, NARUME = 0xdde2e7; // shinogi-ji + mune burnished darker
const HABAKI_C = 0xc9963f, SEPPA_C = 0xb98b3a, TSUBA_C = 0x3b342e, TSUBA_RIM = 0x463d35, FITTING = 0x26242b;
const SAME = 0xe8e2d2, ITO = 0x26305a, MENUKI_C = 0xd8a83c, MEKUGI_C = 0xb28a52;

// ---------------------------------------------------------------- geometry helpers
// push triangle a, b, c ([x, y, z]) wound so its normal points away from ref
function tri(out, a, b, c, ref) {
  const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
  const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
  if (nx * nx + ny * ny + nz * nz < 1e-18) return;
  const cx = (a[0] + b[0] + c[0]) / 3 - ref[0], cy = (a[1] + b[1] + c[1]) / 3 - ref[1], cz = (a[2] + b[2] + c[2]) / 3 - ref[2];
  if (nx * cx + ny * cy + nz * cz < 0) out.push(...a, ...c, ...b); else out.push(...a, ...b, ...c);
}
const quad = (out, a, b, c, d, ref) => { tri(out, a, b, c, ref); tri(out, a, c, d, ref); };
// one mesh, one material per triangle list
function meshOf(lists, colors) {
  const pos = [], geo = new THREE.BufferGeometry();
  let at = 0;
  lists.forEach((l, i) => { for (const v of l) pos.push(v); geo.addGroup(at, l.length / 3, i); at += l.length / 3; });
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, colors.length === 1 ? mat(colors[0]) : colors.map((c) => mat(c)));
}
// convex cross-sections [{ z, pts: [[x, y], ...] }] (same count) joined in order, with optional end caps
function loft(secs, color, cap0 = false, cap1 = false) {
  const out = [];
  const cen = secs.map((s) => [s.pts.reduce((a, p) => a + p[0], 0) / s.pts.length, s.pts.reduce((a, p) => a + p[1], 0) / s.pts.length, s.z]);
  const P = (s, k) => [s.pts[k % s.pts.length][0], s.pts[k % s.pts.length][1], s.z];
  for (let j = 0; j < secs.length - 1; j++) {
    const ref = cen[j].map((v, i) => (v + cen[j + 1][i]) / 2);
    for (let k = 0; k < secs[j].pts.length; k++) quad(out, P(secs[j], k), P(secs[j], k + 1), P(secs[j + 1], k + 1), P(secs[j + 1], k), ref);
  }
  const cap = (j, jn) => { for (let k = 0; k < secs[j].pts.length; k++) tri(out, cen[j], P(secs[j], k), P(secs[j], k + 1), cen[jn]); };
  if (cap0) cap(0, 1);
  if (cap1) cap(secs.length - 1, secs.length - 2);
  return meshOf([out], [color]);
}
const ellipse = (a, b, n, cx = 0, cy = 0) => Array.from({ length: n }, (_, i) => { const t = (i / n) * Math.PI * 2; return [cx + Math.sin(t) * a, cy + Math.cos(t) * b]; });

// ---------------------------------------------------------------- the blade and the habaki, both with z = 0 at the habaki's back
// hamon: height of the temper line above the edge (m) along the body, s = 0 machi .. 1 yokote
function hamonAt(s) {
  const start = Math.min(1, s / 0.08), calm = Math.min(1, (1 - s) / 0.1); // yakidashi at the machi, quieter at the yokote
  const wave = 0.0021 * Math.sin(s * 58 + 0.6) + 0.0012 * Math.sin(s * 131 + 2.1) + 0.0006 * Math.sin(s * 19);
  return 0.0042 + (0.0034 + wave) * start * calm;
}
function bladeMesh() {
  const NM = 44, NK = 9;
  // stations along the mune arc: { t, W (width), rows: [[v 0 edge .. 1 mune top, half thickness]], kis }
  const st = [];
  for (let i = 0; i <= NM; i++) {
    const s = i / NM, W = MOTOHABA + (SAKIHABA - MOTOHABA) * (s * 0.85 + s * s * 0.15);
    const k = (KASANE0 + (KASANE1 - KASANE0) * s) / 2, vs = SHINOGI0 + (SHINOGI1 - SHINOGI0) * s, vh = hamonAt(s) / W;
    st.push({ t: T_YOKOTE * s, W, rows: [[0, 0], [vh, (k * vh) / vs], [vs, k], [1 - RIDGE / W, k * 0.8], [1, 0]] });
  }
  const dKs = (1 - SHINOGI1) * SAKIHABA, kY = KASANE1 / 2;
  for (let j = 1; j <= NK; j++) {
    const u = j / NK, W = SAKIHABA * (1 - u ** 1.6); // fukura: the edge sweeps up to meet the mune at the point
    if (W < 1e-5) { st.push({ t: T_TIP, W: 0, rows: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0]], kis: true }); continue; }
    const k = kY * (1 - u) ** 0.9, vks = Math.max(0.3, 1 - (dKs * (1 - u)) / W), vm = 1 - (RIDGE * (1 - u)) / W;
    const vb = Math.min(vks - 0.06, 0.0042 / W); // boshi: the hamon follows the fukura round to the point
    st.push({ t: T_YOKOTE + (T_TIP - T_YOKOTE) * u, W, rows: [[0, 0], [vb, (k * vb) / vks], [vks, k], [vm, k * 0.8], [1, 0]], kis: true });
  }
  const P = (S, r, sx) => {
    const zS = -R * Math.sin(S.t), yS = Y0 + R * (1 - Math.cos(S.t));
    const zE = zS - S.W * Math.sin(S.t), yE = yS - S.W * Math.cos(S.t), [v, x] = S.rows[r];
    return [sx * x, yE + (yS - yE) * v, zE + (zS - zE) * v];
  };
  const L = [[], [], [], [], []]; // hamon, ji, shinogi-ji, mune, kissaki face (narume)
  for (let i = 0; i < st.length - 1; i++) {
    const A = st[i], B = st[i + 1];
    const c0 = P(A, 0, 0), c1 = P(A, 4, 0), c2 = P(B, 0, 0), c3 = P(B, 4, 0);
    const ref = [0, (c0[1] + c1[1] + c2[1] + c3[1]) / 4, (c0[2] + c1[2] + c2[2] + c3[2]) / 4];
    for (const sx of [1, -1]) {
      for (let r = 0; r < 4; r++) {
        const list = r === 1 && B.kis ? L[4] : L[r];
        quad(list, P(A, r, sx), P(A, r + 1, sx), P(B, r + 1, sx), P(B, r, sx), ref);
      }
    }
  }
  return meshOf(L, [HAMON, JI, SHINOGIJI, MUNE, NARUME]);
}
function habakiMesh() {
  // a wedge sleeve round the blade: deeper and thicker at the back, where it wedges into the koiguchi
  const sec = (z, hx, top, bot) => ({ z, pts: [[hx * 0.5, top], [hx, top - 0.0026], [hx, bot + 0.0038], [hx * 0.42, bot], [-hx * 0.42, bot], [-hx, bot + 0.0038], [-hx, top - 0.0026], [-hx * 0.5, top]] });
  return loft([sec(0, 0.0066, Y0 + 0.0030, Y0 - MOTOHABA - 0.0026), sec(-HABAKI, 0.0054, Y0 + 0.0024, Y0 - MOTOHABA - 0.0018)], HABAKI_C, true, true);
}
// the blade on its own (no habaki), origin at the back of the habaki (the machi), pointing -Z (the Shirasaya skin reuses
// it). This is what grows: userData.katLen = origin to the tip, userData.tip = the tip (local)
export function katanaBlade() {
  const g = new THREE.Group();
  g.add(bladeMesh());
  g.userData.katLen = -TIP[0];
  g.userData.tip = new THREE.Vector3(0, TIP[1], TIP[0]);
  return g;
}
// the habaki on its own: back at z = 0, running forward to z = -0.034. Put it at the same place as katanaBlade() but
// OUTSIDE the growing group, so it keeps its 3.4 cm while the blade stretches.
export function katanaHabaki() {
  const m = habakiMesh();
  m.name = 'habaki';
  return m;
}

// ---------------------------------------------------------------- the tsuka
// cross-section: a slightly squared oval, 12 points (phi 0 = top / mune side, 90 = +X, 180 = edge side)
const PHI = [0, 35, 62.5, 90, 117.5, 145, 180, 215, 242.5, 270, 297.5, 325].map((d) => (d * Math.PI) / 180);
const spow = (v) => Math.sign(v) * Math.abs(v) ** 0.85;
const ovalAt = (a, b, phi) => [a * spow(Math.sin(phi)), b * spow(Math.cos(phi))];
// half-width / half-height of the wooden core (under the same) along z: wide at the fuchi, a waist, a little wider again
const CORE = [[Z_FUCHI, 0.0114, 0.0165], [ZW0, 0.0113, 0.0163], [-0.03, 0.0106, 0.0152], [0.04, 0.0106, 0.0153], [ZW1, 0.0109, 0.0156], [Z_KASHIRA_END, 0.0109, 0.0156]];
function coreAB(z) {
  if (z <= CORE[0][0]) return [CORE[0][1], CORE[0][2]];
  for (let i = 1; i < CORE.length; i++) if (z <= CORE[i][0]) { const [z0, a0, b0] = CORE[i - 1], [z1, a1, b1] = CORE[i], t = (z - z0) / (z1 - z0); return [a0 + (a1 - a0) * t, b0 + (b1 - b0) * t]; }
  const l = CORE[CORE.length - 1]; return [l[1], l[2]];
}
const tsukaPt = (z, phi, lift = 0) => { const [a, b] = coreAB(z), [x, y] = ovalAt(a + lift, b + lift, phi); return [x, y, z]; };

// ito: two cords wound in opposite directions (hira-maki). On each side face they cross every PITCH (alternating faces),
// run steeply across the faces and straight round the top and bottom, so the white same shows in diamonds on the sides.
const LIFT = 0.0011, OVER = 0.0005, CROWN = 0.0008; // cord off the same; the top cord at a crossing; the cord's rounded back
const MENUKI_H = 0.0046;
function menukiBump(z, phi) {
  const s = Math.sin(phi);
  for (const [zm, side] of [[MENUKI_OMOTE, -1], [MENUKI_URA, 1]]) if (s * side > 0.99 && Math.abs(z - zm) < MENUKI_HALF) return MENUKI_H * 0.75;
  return 0;
}
// ribbons round the tsuka from samples [{ z, phi, wz (width along z), lift }]: two facets across, so each cord shows a ridge
function ribbons(paths, z0, z1, surf = tsukaPt) {
  const out = [];
  for (const smp of paths) {
    const cut = (S) => {
      const za = Math.min(z1, Math.max(z0, S.z - S.wz / 2)), zb = Math.min(z1, Math.max(z0, S.z + S.wz / 2)), zc = Math.min(z1, Math.max(z0, S.z));
      return [surf(za, S.phi, S.lift), surf(zc, S.phi, S.lift + CROWN), surf(zb, S.phi, S.lift)];
    };
    let prev = cut(smp[0]);
    for (let i = 1; i < smp.length; i++) {
      const cur = cut(smp[i]), ref = [0, 0, (smp[i - 1].z + smp[i].z) / 2];
      quad(out, prev[0], prev[1], cur[1], cur[0], ref);
      quad(out, prev[1], prev[2], cur[2], cur[1], ref);
      prev = cur;
    }
  }
  return out;
}
function itoMesh() {
  const L = PITCH;
  // one turn of cord A from a crossing on the ura (+X) face: [phi in degrees, z offset]. Cord B is its mirror (phi -> 180 - phi).
  // Widths along z: narrow at the crossing, wide enough part-way up the face to close each window into a diamond
  const turn = [[145, -L / 4], [117.5, -L / 8], [90, 0], [62.5, L / 8], [35, L / 4], [0, L / 4], [-35, L / 4], [-62.5, 3 * L / 8], [-90, L / 2], [-117.5, 5 * L / 8], [-145, 3 * L / 4], [-180, 3 * L / 4]];
  const turns = Math.ceil((ZW1 - ZW0) / L) + 1, paths = [];
  for (const cord of [0, 1]) {
    const smp = [];
    for (let m = -1; m <= turns; m++) {
      for (const [p, dz] of turn) {
        const phi = ((cord ? 180 - p : p) * Math.PI) / 180, z = Z_X0 + dz + m * L, s = Math.sin(phi), as = Math.abs(s);
        if (z < ZW0 - L / 2 || z > ZW1 + L / 2) continue;
        const over = (cord === 0 && s > 0.8) || (cord === 1 && s < -0.8);
        smp.push({ phi, z, wz: as > 0.99 ? 0.0112 : as > 0.8 ? 0.75 * L + 0.0016 : L / 2, lift: LIFT + (over ? OVER : 0) + menukiBump(z, phi) });
      }
    }
    paths.push(smp);
  }
  return meshOf([ribbons(paths, ZW0, ZW1)], [ITO]);
}
function coreMesh() {
  const zs = [ZW0 - 0.004, -0.03, 0.04, ZW1 + 0.004];
  return loft(zs.map((z) => ({ z, pts: PHI.map((p) => tsukaPt(z, p).slice(0, 2)) })), SAME);
}
// menuki: a pair of gold ornaments (two lobes and a waist) lying on the side faces under the cord
function menukiMesh(zc, side) {
  const prof = [[-1, 0], [-0.72, 0.62], [0, 1], [0.72, 0.62], [1, 0]]; // across the face: [height fraction, outward fraction]
  const along = [[-1, 0.3], [-0.78, 0.85], [-0.42, 1], [0, 0.72], [0.42, 1], [0.78, 0.85], [1, 0.3]];
  const secs = along.map(([f, sc]) => {
    const z = zc + f * MENUKI_HALF, [a] = coreAB(z);
    return { z, pts: prof.map(([u, h]) => [side * (a - 0.001 + h * (MENUKI_H + 0.001) * sc), u * 0.0074 * sc]) };
  });
  return loft(secs, MENUKI_C, true, true);
}

// ---------------------------------------------------------------- fittings
function fuchiMesh() {
  const sec = (z, a, b) => ({ z, pts: PHI.map((p) => ovalAt(a, b, p)) });
  return loft([sec(Z_FUCHI, 0.0138, 0.0198), sec(Z_FUCHI + FUCHI_L - 0.0015, 0.0136, 0.0195), sec(Z_FUCHI + FUCHI_L, 0.0130, 0.0186)], FITTING);
}
const KA = 0.0134, KB = 0.0184, Z_SHITODOME = Z_KASHIRA_END - KASHIRA_L + 0.016;
function kashiraMesh() {
  const z0 = Z_KASHIRA_END - KASHIRA_L, sec = (z, k) => ({ z, pts: PHI.map((p) => ovalAt(KA * k, KB * k, p)) });
  return loft([sec(z0, 0.97), sec(z0 + 0.002, 1), sec(Z_KASHIRA_END - 0.007, 1), sec(Z_KASHIRA_END - 0.0025, 0.9), sec(Z_KASHIRA_END - 0.0005, 0.66), sec(Z_KASHIRA_END, 0.4)], FITTING, false, true);
}
// the ito's last turn: each cord crosses over the top of the kashira into the shitodome eyelet on the far side
function kashiraCord() {
  const kSurf = (z, phi, lift) => { const [x, y] = ovalAt(KA + lift, KB + lift, phi); return [x, y, z]; };
  const z0 = Z_KASHIRA_END - KASHIRA_L + 0.004;
  const paths = [1, -1].map((sd) => [75, 35, 0, -35, -70, -90].map((d, i, a) => ({ phi: (sd * d * Math.PI) / 180, z: z0 + (Z_SHITODOME - z0) * (i / (a.length - 1)), wz: 0.0080, lift: -0.0002 + (sd > 0 ? OVER : 0) })));
  return meshOf([ribbons(paths, z0 - 0.0035, Z_KASHIRA_END - 0.007, kSurf)], [ITO]);
}
function tsubaMesh() {
  // maru-gata iron tsuba with the two hitsu-ana: kozuka (a D) on the omote (-X) side, kogai (two lobes) on the ura,
  // and a raised rim (mimi)
  const kozuka = [[-0.0150, 0.0125], [-0.0150, -0.0125], ...Array.from({ length: 7 }, (_, i) => { const t = Math.PI * (1 - (i + 1) / 8); return [-0.0150 - 0.0072 * Math.sin(t), 0.0125 * Math.cos(t)]; })];
  const kogai = [[0.0150, 0.0125], [0.0193, 0.0121], [0.0221, 0.0088], [0.0207, 0.0038], [0.0186, 0], [0.0207, -0.0038], [0.0221, -0.0088], [0.0193, -0.0121], [0.0150, -0.0125]];
  const zc = Z_FUCHI - SEPPA_T - TSUBA_T / 2, zf = zc - TSUBA_T / 2, zb = zc + TSUBA_T / 2;
  const body = plate(ellipse(0.0368, 0.0388, 24), TSUBA_T, TSUBA_C, { z: zc, holes: [kozuka, kogai] });
  const mimi = lathe([[0.0334, zf - 0.0006], [0.0372, zf - 0.0006], [0.0372, zb + 0.0006], [0.0334, zb + 0.0006]], TSUBA_RIM, { segs: 24, sy: 0.0392 / 0.0372 });
  return [body, mimi];
}

export function build(g) {
  const bl = katanaBlade();
  bl.position.z = Z_BLADE;
  g.add(bl);
  // habaki: fixed on g (not in katBlade), back at Z_BLADE, front at Z_BLADE - 0.034
  const hb = katanaHabaki();
  hb.position.z = Z_BLADE;
  g.add(hb);
  // seppa / tsuba / seppa
  const seppa = ellipse(0.0146, 0.0216, 16);
  g.add(plate(seppa, SEPPA_T, SEPPA_C, { z: Z_BLADE + SEPPA_T / 2 }));
  g.add(...tsubaMesh());
  g.add(plate(seppa, SEPPA_T, SEPPA_C, { z: Z_FUCHI - SEPPA_T / 2 }));
  // tsuka
  g.add(fuchiMesh(), coreMesh(), itoMesh(), kashiraMesh(), kashiraCord(), menukiMesh(MENUKI_OMOTE, -1), menukiMesh(MENUKI_URA, 1));
  g.add(pin(0.0022, coreAB(Z_X0)[0] * 2 + 0.0004, MEKUGI_C, 0, 0, Z_X0, 6)); // mekugi, in the first omote diamond
  g.add(pin(0.0026, KA * 2 + 0.0012, MENUKI_C, 0, 0, Z_SHITODOME, 8));       // shitodome eyelets either side of the kashira
  g.userData.katBlade = bl;
  g.userData.katLen = bl.userData.katLen;
  g.userData.muzzle = new THREE.Vector3(0, TIP[1], Z_BLADE + TIP[0]);
  g.userData.len = Z_KASHIRA_END - (Z_BLADE + TIP[0]);
}
export const hatAt = [[0, 0.019, -0.01], 0.055];
