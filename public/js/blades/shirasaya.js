// Shirasaya katana skin: the same Edo-period shinogi-zukuri katana blade as the base katana (katana.js, nagasa 70 cm,
// sori 1.7 cm, gold-washed habaki), in its shirasaya: the plain "white scabbard" resting mount a blade is kept in
// between uses. The tsuka is two halves of honoki (Japanese bigleaf magnolia, pale and unfinished) carved to the
// nakago and glued: no tsuba, no seppa, no fuchi or kashira, no same and no ito, so the wood of the tsuka-guchi meets the
// back of the habaki directly. One bamboo mekugi peg holds it on, through the nakago's mekugi-ana.
// Shape: an elongated oval section (taller than wide, the sides a little flattened, the ha side a touch narrower than
// the mune side), widest at the tsuka-guchi (it has to sit round the habaki's back) and easing in towards the butt,
// following the nakago's gentle curve (the butt sits a few mm above the blade axis), the butt end cut square with a
// slightly rounded end grain; the mouth face is end grain too.
// Refs: Fitzwilliam Museum 163215, katana in shirasaya (blade 71.7 cm, tang 24.1 cm, sori 1.7 cm); Bonhams lot 2264,
//   Soshu katana in shirasaya (nagasa 67.1 cm, motohaba 3.0 cm); NBTHK Token Bijutsu 675 (nakago ~20.8 cm on a 77 cm tachi);
//   HanBon Forge shirasaya katana (blade 27.7", handle 10.5" = 26.7 cm, 41" overall) and swords-and-more / Celtic Web
//   Merchant shirasaya listings (handle 25-28 cm); islandblacksmith.ca "Shirasaya (Storage Scabbard)" + Nosyudo
//   shirasaya service (honoki is the wood; the mekugi is bamboo or horn); NMB forum threads "shirasaya the making of"
//   (an oval section planned on paper, flats added after, size dictated by the blade) and "why so many holes" (the
//   mekugi-ana sits about three finger widths behind the machi on a katana).
// Held like the katana: the tsuka is centred on the grip (z -0.13 .. +0.13), edge down, tip to -Z.
// Growth contract (same as katana.js): userData.katBlade = katanaBlade() = the blade ONLY (no habaki), origin at the
// tsuka-guchi (z = Z_MOUTH), pointing -Z, so setKatana() stretches nothing but the steel; the habaki (katanaHabaki()) is
// fixed in g itself, 3.4 cm long with its back against the wood of the mouth at every kill count;
// userData.katLen = katBlade's origin to the tip; muzzle = exactly the tip.
import { THREE, mat } from './kit.js';
import * as KAT from './katana.js';

// ---------------------------------------------------------------- measurements (metres)
const Z_MOUTH = -0.130, Z_END = 0.130;          // 26 cm tsuka: the tsuka-guchi (against the habaki) to the butt
const RISE = 0.0055;                            // the butt's centre sits this far above the blade axis (nakago sori)
const RT = (Z_END - Z_MOUTH) ** 2 / (2 * RISE); // radius of that curve, tangent to the blade axis at the mouth
const Z_MEKUGI = Z_MOUTH + 0.050;               // ~3 finger widths behind the machi
// half width (x) and half height (y) of the section along the tsuka: full at the mouth, easing in to the butt
const PROF = [[Z_MOUTH, 0.0132, 0.0201], [-0.080, 0.0129, 0.0195], [0.000, 0.0124, 0.0186], [0.080, 0.0121, 0.0181], [Z_END, 0.0120, 0.0179]];

// ---------------------------------------------------------------- colours
const HONOKI = 0xe6dbb9, END_GRAIN = 0xc9b78e, MEKUGI = 0x7a5530;

// ---------------------------------------------------------------- geometry helpers
// push triangle a, b, c ([x, y, z]) wound so its normal points away from ref
function tri(out, a, b, c, ref) {
  const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
  const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
  if (nx * nx + ny * ny + nz * nz < 1e-18) return;
  const cx = (a[0] + b[0] + c[0]) / 3 - ref[0], cy = (a[1] + b[1] + c[1]) / 3 - ref[1], cz = (a[2] + b[2] + c[2]) / 3 - ref[2];
  if (nx * cx + ny * cy + nz * cz < 0) out.push(...a, ...c, ...b); else out.push(...a, ...b, ...c);
}
function meshOf(lists, colors) {
  const pos = [], geo = new THREE.BufferGeometry();
  let at = 0;
  lists.forEach((l, i) => { for (const v of l) pos.push(v); geo.addGroup(at, l.length / 3, i); at += l.length / 3; });
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, colors.map((c) => mat(c)));
}

// the tsuka's centre line: an arc tangent to the blade axis (y = 0) at the mouth, rising towards the butt
const yc = (z) => (z - Z_MOUTH) ** 2 / (2 * RT);
const nrm = (z) => { const s = (z - Z_MOUTH) / RT, l = Math.hypot(s, 1); return [-s / l, 1 / l]; }; // (z, y), mune side
function ab(z) {
  if (z <= PROF[0][0]) return [PROF[0][1], PROF[0][2]];
  for (let i = 1; i < PROF.length; i++) if (z <= PROF[i][0]) { const [z0, a0, b0] = PROF[i - 1], [z1, a1, b1] = PROF[i], t = (z - z0) / (z1 - z0); return [a0 + (a1 - a0) * t, b0 + (b1 - b0) * t]; }
  const l = PROF[PROF.length - 1]; return [l[1], l[2]];
}
// section: 16 points, phi 0 = mune (top), 90 = +X, 180 = ha. Sides a little flattened, the ha side a little narrower
const NSEC = 16, spow = (v, p) => Math.sign(v) * Math.abs(v) ** p;
function section(z, k = 1) {
  const [a, b] = ab(z), [nz, ny] = nrm(z), y0 = yc(z), pts = [];
  for (let i = 0; i < NSEC; i++) {
    const phi = (i / NSEC) * Math.PI * 2, c = Math.cos(phi);
    const x = a * k * spow(Math.sin(phi), 0.78) * (c < 0 ? 1 + 0.07 * c : 1), u = b * k * spow(c, 0.9);
    pts.push([x, y0 + u * ny, z + u * nz]);
  }
  return pts;
}
const centre = (z) => [0, yc(z), z];

function tsukaMesh() {
  // stations: [z, scale]. A 1 mm chamfer at the mouth, a rounded edge and a slightly domed end at the butt
  const st = [[Z_MOUTH, 0.955], [Z_MOUTH + 0.0012, 1], [-0.08, 1], [-0.02, 1], [0.04, 1], [0.1, 1], [Z_END - 0.0045, 1], [Z_END - 0.0015, 0.965], [Z_END, 0.88]];
  const rings = st.map(([z, k]) => section(z, k));
  const side = [], ends = [];
  for (let j = 0; j < rings.length - 1; j++) {
    const ref = centre((st[j][0] + st[j + 1][0]) / 2);
    for (let i = 0; i < NSEC; i++) {
      const i1 = (i + 1) % NSEC, A = rings[j][i], B = rings[j][i1], C = rings[j + 1][i1], D = rings[j + 1][i];
      tri(side, A, B, C, ref); tri(side, A, C, D, ref);
    }
  }
  // the mouth face (flat, against the habaki) and the butt (domed 1.5 mm)
  const [enz, eny] = nrm(Z_END); // the centre line's tangent towards the butt is (eny, -enz)
  const dome = [0, yc(Z_END) - enz * 0.0015, Z_END + eny * 0.0015];
  const last = rings[rings.length - 1], first = rings[0];
  for (let i = 0; i < NSEC; i++) {
    const i1 = (i + 1) % NSEC;
    tri(ends, dome, last[i], last[i1], centre(Z_END - 0.01));
    tri(ends, centre(Z_MOUTH), first[i], first[i1], centre(Z_MOUTH + 0.01));
  }
  return meshOf([side, ends], [HONOKI, END_GRAIN]);
}

// the bamboo mekugi: a slightly tapered peg across the tsuka, the thick end standing proud on the omote (-X) side
function mekugiMesh() {
  const [a] = ab(Z_MEKUGI), len = a * 2 + 0.0011;
  const geo = new THREE.CylinderGeometry(0.0026, 0.0030, len, 8); // top (+Y before the turn) = thin end
  geo.rotateZ(-Math.PI / 2);                                       // +Y -> +X: the thin end on +X (ura)
  const m = new THREE.Mesh(geo, mat(MEKUGI));
  m.position.set(-0.0003, yc(Z_MEKUGI), Z_MEKUGI);
  return m;
}

// the katana's blade and habaki as two objects, both in the blade frame (origin at the habaki's back, pointing -Z).
// katana.js exports katanaHabaki() beside a blade-only katanaBlade(); with an older katana.js, whose katanaBlade() still
// holds the habaki, the habaki (the child that stays within 5 cm of the origin) is lifted out of it here
function bladeAndHabaki() {
  const bl = KAT.katanaBlade();
  if (typeof KAT.katanaHabaki === 'function') return [bl, KAT.katanaHabaki()];
  const hb = bl.children.find((c) => new THREE.Box3().setFromObject(c).min.z > -0.05);
  bl.remove(hb);
  return [bl, hb];
}

export function build(g) {
  const [bl, hb] = bladeAndHabaki();
  bl.position.z = Z_MOUTH;                                                // the stretching part: steel only
  hb.position.z += Z_MOUTH - new THREE.Box3().setFromObject(hb).max.z;   // the habaki's back on the tsuka-guchi
  g.add(bl, hb, tsukaMesh(), mekugiMesh());
  const tip = bl.userData.tip;
  g.userData.katBlade = bl;
  g.userData.katLen = bl.userData.katLen;
  g.userData.muzzle = new THREE.Vector3(0, tip.y, Z_MOUTH + tip.z);
  g.userData.len = Z_END + 0.0015 - (Z_MOUTH + tip.z);
}
// the hat sits on top of the tsuka, over the hand
export const hatAt = [[0, yc(0.03) + ab(0.03)[1] - 0.0004, 0.03], 0.055];
