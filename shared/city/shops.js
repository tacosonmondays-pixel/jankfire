// Shops as real places (the GTA side: "lots of shops"): an open shopfront on the street, a counter, a shopkeeper's spot
// behind it, a lit sign, shelves. The systems lane runs the trade: every shop is a mark
//   { id: 'shop', shop: <kind>, sid, name, p: <where you stand at the counter>, keeper, face: <keeper's yaw>, door, stock? }
// kinds: guns, meat_mechanic, tooth_stall, vending, car_dealer, outfits. A garage is { id: 'garage', p, face, home }.
// Places are fixed (SHOPS): the generators keep their houses / offices out of each shop's rect (shopRects()).
import { SLICE, hwY } from './slice.js';
import { rng, hash2 } from './plan.js';
import { cube } from './kit.js';

const yB = (k) => k * SLICE.bottom.rise, laneN = (k) => 256 - SLICE.bottom.terr * k - 7; // the Bottom: a terrace's height, its lane's back edge
const GY = SLICE.gut.y;
// open: which side is the shopfront (0 = -z, 1 = +x, 2 = +z, 3 = -x)
export const SHOPS = [
  // the Bottom: on the terrace lanes, open to the lane (+z)
  { sid: 'pew_pew_pawn', kind: 'guns', name: 'PEW PEW PAWN', district: 'bottom', rect: [-104, laneN(1) - 9, -94, laneN(1)], y: yB(1), open: 2, tint: 0xff3030, h: 3.4 },
  { sid: 'second_hand_self', kind: 'outfits', name: 'SECOND-HAND SELF', district: 'bottom', rect: [-26, laneN(1) - 9, -14, laneN(1)], y: yB(1), open: 2, tint: 0xff4fd8, h: 3.4 },
  { sid: 'soup_and_shoes', kind: 'outfits', name: 'SOUP & SHOES', district: 'bottom', rect: [-136, laneN(3) - 9, -126, laneN(3)], y: yB(3), open: 2, tint: 0xffe14d, h: 3.2 },
  // the Gut: on the campus streets, open to the street (-z)
  { sid: 'meat_mechanics', kind: 'meat_mechanic', name: 'MEAT MECHANICS', district: 'gut', rect: [-122, -94, -104, -82], y: GY, open: 0, tint: 0xfff0f0, h: 4.2 },
  { sid: 'bone_arms', kind: 'guns', name: 'BONE ARMS', district: 'gut', rect: [-170, -94, -158, -84], y: GY, open: 0, tint: 0xf4ead0, h: 3.6 },
  // the Commute: off the old ring road's on-ramp
  { sid: 'previously_loved', kind: 'car_dealer', name: 'PREVIOUSLY LOVED MOTORS', district: 'commute', rect: [112, 202, 126, 210], y: null, open: 2, tint: 0x4fd8ff, h: 3.4, lot: [112, 210, 156, 232] },
  { sid: 'petrol_and_pistols', kind: 'guns', name: 'PETROL & PISTOLS', district: 'commute', rect: [124, 124, 138, 132], y: null, open: 2, tint: 0x39ff14, h: 3.6 },
];
// where the Machine-style vending machines stand (the ☺ CORP ones that still work): [x, z, yaw, district]
export const VENDING = [[-148.5, 236, -Math.PI / 2, 'bottom'], [-61.5, 236, Math.PI / 2, 'bottom'], [9.2, 140, -Math.PI / 2, 'bottom'], [-95.6, 221.4, Math.PI, 'bottom'],
  [-60, -117, Math.PI, 'gut'], [16, -172, Math.PI, 'gut'], [-105.6, -92.6, 0, 'gut'], [128, 214, Math.PI, 'commute'], [140, 133.2, Math.PI, 'commute']];
// the safehouse garage: by the Lost & Found on terrace 2, its door on the lane
export const GARAGES = [{ home: 'bottom:lostfound', rect: [-232, laneN(2) - 10, -224, laneN(2)], y: yB(2), open: 2 }];
const gY = (s) => (s.y ?? Math.max(hwY(s.rect[1], true), hwY(s.rect[3], true)));
export const shopRects = (district) => [...SHOPS.filter((s) => s.district === district).map((s) => s.lot ? [Math.min(s.rect[0], s.lot[0]), Math.min(s.rect[1], s.lot[1]), Math.max(s.rect[2], s.lot[2]), Math.max(s.rect[3], s.lot[3])] : s.rect),
  ...(district === 'bottom' ? GARAGES.map((g) => g.rect) : [])];

// unit vectors per open side: out of the shop
const OUT = [[0, -1], [1, 0], [0, 1], [-1, 0]];
const YAW = [0, -Math.PI / 2, Math.PI, Math.PI / 2]; // a yaw that faces out of that side (0 looks -z)
function shopfront(B, s) {
  const [x0, z0, x1, z1] = s.rect, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, y = gY(s), r = rng(hash2(x0 | 0, z0 | 0, 0x5409));
  const [ox, oz] = OUT[s.open], w = x1 - x0, d = z1 - z0;
  if (!B.touches(s.rect, 3)) return;
  B.add(x0, y - 2, z0, x1, y, z1, 'concrete', { tint: 0xc8bcb4 }); // its own floor slab (the Commute's ground steps)
  cube(B, cx, y, cz, w, d, s.h, r, { open: s.open, door: s.open, tint: s.tint === 0xfff0f0 ? 0xf4f4f4 : undefined });
  // the counter across the shop, 40% of the way in; the keeper behind it; you in front of it
  const depth = s.open % 2 ? w : d, across = s.open % 2 ? d : w, at = (k) => [cx + ox * (depth / 2 - depth * k), cz + oz * (depth / 2 - depth * k)];
  const [kx, kz] = at(0.6), [px, pz] = at(0.42), [qx, qz] = at(0.82), [dx, dz] = at(-0.15);
  const ca = across - 2.4;
  if (s.open % 2) B.add(kx - ox * 0.4 - 0.4, y, kz - ca / 2, kx - ox * 0.4 + 0.4, y + 1.05, kz + ca / 2, 'wood', { tint: 0xb07a4a });
  else B.add(kx - ca / 2, y, kz - oz * 0.4 - 0.4, kx + ca / 2, y + 1.05, kz - oz * 0.4 + 0.4, 'wood', { tint: 0xb07a4a });
  // shelves along the back wall (crates / jars / fridges by kind) and the sign over the front
  const stuff = { guns: ['crate_soup', 'locker'], outfits: ['wardrobe', 'laundry_a'], meat_mechanic: ['organjar', 'organjar', 'fridge'], car_dealer: ['filecab', 'officechair'], tooth_stall: ['tooth'], vending: [] }[s.kind];
  for (let i = 0; i < 3; i++) { const t = (i + 0.5) / 3 - 0.5, sx = s.open % 2 ? qx : cx + t * (across - 2), sz = s.open % 2 ? cz + t * (across - 2) : qz; B.prop(stuff[i % stuff.length], sx, y, sz, YAW[s.open], 1, i); }
  const sy = y + s.h + 0.1, fx = cx + ox * (depth / 2 + 0.1), fz = cz + oz * (depth / 2 + 0.1);
  if (s.open % 2) B.add(fx - 0.1, sy, cz - across / 2 + 0.5, fx + 0.1, sy + 1.3, cz + across / 2 - 0.5, 'glow', { nc: true, tint: s.tint });
  else B.add(cx - across / 2 + 0.5, sy, fz - 0.1, cx + across / 2 - 0.5, sy + 1.3, fz + 0.1, 'glow', { nc: true, tint: s.tint });
  B.light(fx + ox * 2, sy, fz + oz * 2, s.tint, 12, 0.9); B.light(cx, y + s.h - 0.6, cz, 0xffe8c0, 8, 0.7);
  if (B.inside(cx, cz)) B.out.marks.push({ id: 'shop', shop: s.kind, sid: s.sid, name: s.name, p: [px, y, pz], keeper: [kx - ox * 1.2, y, kz - oz * 1.2], face: YAW[s.open], door: [dx, y, dz] });
  // a car dealer's forecourt: bunting, stock spots (park marks with sale: true)
  if (s.lot) {
    const [lx0, lz0, lx1, lz1] = s.lot;
    for (let x = lx0 + 3; x < lx1 - 2; x += 5.5) for (const z of [lz0 + 5, lz0 + 14]) { const yy = hwY(z, true); if (B.inside(x, z)) B.out.marks.push({ id: 'park', p: [x, yy, z], yaw: Math.PI / 2, sale: s.sid }); }
    for (let x = lx0; x < lx1; x += 4) if (B.inside(x, lz1)) B.prop('stringlights', x + 2, hwY(lz1, true) + 3.2, lz1, 0, 1, 0);
  }
}
function vending(B, [x, z, yaw, district]) {
  if (!B.inside(x, z)) return;
  const y = district === 'gut' ? GY : district === 'commute' ? hwY(z, true) : (() => { for (let k = 0; k < SLICE.bottom.n; k++) if (z <= 256 - SLICE.bottom.terr * k && z > 256 - SLICE.bottom.terr * (k + 1)) return yB(k); return 0; })();
  B.prop('vendo', x, y, z, yaw, 1, 0);
  B.add(x - 0.5, y, z - 0.5, x + 0.5, y + 1.9, z + 0.5, 'metal', { hide: true });
  B.light(x - Math.sin(yaw) * 0.8, y + 1.4, z - Math.cos(yaw) * 0.8, 0x4fd8ff, 5, 0.6);
  B.out.marks.push({ id: 'shop', shop: 'vending', sid: 'vendo_' + Math.round(x) + '_' + Math.round(z), name: '☺ VENDO', p: [x - Math.sin(yaw) * 1.2, y, z - Math.cos(yaw) * 1.2], keeper: null, face: yaw, door: null });
}
function garage(B, g) {
  const [x0, z0, x1, z1] = g.rect, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, r = rng(0x6a7a6e);
  if (!B.touches(g.rect, 2)) return;
  cube(B, cx, g.y, cz, x1 - x0, z1 - z0, 3.4, r, { open: g.open, tint: 0x9aa0a8, container: true });
  const [ox, oz] = OUT[g.open];
  B.prop('garagedoor', cx + ox * ((z1 - z0) / 2 - 0.1), g.y, cz + oz * ((z1 - z0) / 2 - 0.1), YAW[g.open], 1, 0); // (rolled half up)
  if (B.inside(cx, cz)) B.out.marks.push({ id: 'garage', p: [cx, g.y, cz], face: YAW[g.open] + Math.PI, home: g.home, door: [cx + ox * ((z1 - z0) / 2 + 2), g.y, cz + oz * ((z1 - z0) / 2 + 2)] });
}

// the generators call this with their district (bottom.js / gut.js / commute.js)
export function shops(B, district) {
  for (const s of SHOPS) if (s.district === district) shopfront(B, s);
  for (const v of VENDING) if (v[3] === district) vending(B, v);
  if (district === 'bottom') for (const g of GARAGES) garage(B, g);
  // Bev's back room in the Lost & Found (the clinic spot): a Meat Mechanic who doesn't sell to Corp
  if (district === 'bottom' && B.inside(-207, 186.5)) B.out.marks.push({ id: 'shop', shop: 'meat_mechanic', sid: 'bev', name: "BEV'S (BACK ROOM)", p: [-206, yB(2) + 0.15, 188], keeper: [-208.2, yB(2) + 0.15, 185.6], face: Math.PI * 0.75, door: null });
  // the Tooth Market's stalls are shops too (gut.js builds them: 2 rows of 5)
  if (district === 'gut') {
    const [x0, z0] = SLICE.teeth.rect, NAMES = ['MOLAR & SONS', 'FLOSS BOSS', 'THE ROOT CANAL', 'CROWN JEWELS', 'BITE ME', 'GUMMY', 'INCISOR TRADING', 'TOOTH FAIRY (RETIRED)', 'CHEW CHEW', 'WISDOM SALES'];
    for (let i = 0; i < 10; i++) {
      const x = x0 + 6 + (i % 5) * 12, z = z0 + 8 + Math.floor(i / 5) * 30, f = i < 5 ? 1 : -1; // stall front: +z for the first row, -z for the second
      if (B.inside(x, z)) B.out.marks.push({ id: 'shop', shop: 'tooth_stall', sid: 'tooth_' + i, name: NAMES[i], p: [x, GY, z + f * 1.6], keeper: [x, GY, z - f * 1.2], face: f > 0 ? Math.PI : 0, door: null });
    }
  }
}
