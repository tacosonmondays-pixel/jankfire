// Shops as real places (the GTA side: "lots of shops"): an open shopfront on the street, a counter, a shopkeeper's spot
// behind it, a lit sign, shelves. The systems lane runs the trade: every shop is a mark
//   { id: 'shop', shop: <kind>, sid, name, p: <where you stand at the counter>, keeper, face: <keeper's yaw>, door, stock? }
// kinds: guns, meat_mechanic, tooth_stall, vending, car_dealer, outfits. A garage is { id: 'garage', p, face, home }.
// Places are fixed (SHOPS): the generators keep their houses / offices out of each shop's rect (shopRects()).
import { SLICE, hwY, groundY } from './slice.js';
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
  cube(B, cx, y, cz, w, d, s.h, r, { open: s.open, door: -1, tint: s.tint === 0xfff0f0 ? 0xf4f4f4 : undefined });
  // the inside, in the shop's own frame: u = metres in from the open front, v = across (right of the doorway +)
  const depth = s.open % 2 ? w : d, across = s.open % 2 ? d : w, rx = -oz, rz = ox;
  const W = (u, v) => [cx + ox * (depth / 2 - u) + rx * v, cz + oz * (depth / 2 - u) + rz * v];
  const box = (u0, v0, u1, v1, y0, y1, mat, o) => { const [ax, az] = W(u0, v0), [bx, bz] = W(u1, v1); B.add(Math.min(ax, bx), y + y0, Math.min(az, bz), Math.max(ax, bx), y + y1, Math.max(az, bz), mat, o); };
  const yawTo = (dx, dz) => Math.atan2(-dx, -dz); // (0 looks -z)
  const put = (id, u, v, face, i = 0) => { const [x, z] = W(u, v); B.prop(id, x, y, z, face, 1, i); };
  const inward = YAW[s.open] + Math.PI, outward = YAW[s.open], toRight = yawTo(rx, rz), toLeft = yawTo(-rx, -rz);
  // the counter (a gap at the right end so the keeper can get out), the till on it; the keeper's nook behind it (a
  // stool, a lamp); a partition with a doorway into the back room (stock, a fridge, the kettle); displays down the walls
  const cu = depth * 0.5, half = across / 2, pu = Math.max(cu + 2.2, depth * 0.78);
  box(cu - 0.4, -half + 0.3, cu + 0.4, half - 1.6, 0, 1.05, 'wood', { tint: s.kind === 'meat_mechanic' ? 0xf0f0f0 : 0xb07a4a });
  put('till', cu, -half * 0.35, outward);
  put('pchair', cu + 1.2, -half * 0.35 + 0.8, outward, 1); B.light(...(([x, z]) => [x, y + 2.2, z])(W(cu + 1.4, 0)), 0xffd8a0, 6, 0.8);
  if (pu < depth - 1.2) {
    box(pu, -half + 0.25, pu + 0.2, half - 1.9, 0, s.h, 'plaster', { tint: 0xd8ccc4 }); box(pu, half - 0.7, pu + 0.2, half - 0.25, 0, s.h, 'plaster', { tint: 0xd8ccc4 }); // (the doorway between)
    box(pu, half - 1.9, pu + 0.2, half - 0.7, 2.2, s.h, 'plaster', { tint: 0xd8ccc4 });
    put('crate_soup', depth - 0.9, -half + 1, inward, 2); put('crate_soup', depth - 0.9, -half + 2.2, inward, 3); put('fridge', depth - 0.7, 0.2, inward, 4);
  }
  const KIND = {
    guns: { wall: ['gun_rack', 'gun_rack'], back: 'gun_rack' }, outfits: { wall: ['clothes_rail', 'clothes_rail'], back: 'shelf_wall', window: 'mannequin' },
    meat_mechanic: { wall: ['dentist_chair', 'jar_shelf'], back: 'jar_shelf' }, car_dealer: { wall: ['shelf_wall', 'officechair'], back: 'filecab' },
  }[s.kind] || { wall: ['shelf_wall'], back: 'shelf_wall' };
  for (const [side, face] of [[-1, toRight], [1, toLeft]]) KIND.wall.forEach((id, k) => { const u = 1.4 + k * Math.max(1.6, (cu - 2) / KIND.wall.length); if (u < cu - 0.8) put(id, u, side * (half - 0.55), face, k + (side > 0 ? 5 : 0)); });
  for (const v of [-half * 0.55, half * 0.15]) put(KIND.back, pu - 0.35, v, outward, 7);
  if (KIND.window) for (const v of [-half + 1.2, half - 1.2]) put(KIND.window, 0.7, v, outward, 8);
  const [px, pz] = W(cu - 1.3, -half * 0.35), [kx, kz] = W(cu + 1.1, -half * 0.35), [dx, dz] = W(-1.2, 0);
  const sy = y + s.h + 0.1, fx = cx + ox * (depth / 2 + 0.1), fz = cz + oz * (depth / 2 + 0.1);
  if (s.open % 2) B.add(fx - 0.1, sy, cz - across / 2 + 0.5, fx + 0.1, sy + 1.3, cz + across / 2 - 0.5, 'glow', { nc: true, tint: s.tint });
  else B.add(cx - across / 2 + 0.5, sy, fz - 0.1, cx + across / 2 - 0.5, sy + 1.3, fz + 0.1, 'glow', { nc: true, tint: s.tint });
  B.light(fx + ox * 2, sy, fz + oz * 2, s.tint, 12, 0.9); B.light(cx, y + s.h - 0.6, cz, 0xffe8c0, 8, 0.7);
  if (B.inside(cx, cz)) B.out.marks.push({ id: 'shop', shop: s.kind, sid: s.sid, name: s.name, p: [px, y, pz], keeper: [kx, y, kz], face: YAW[s.open], door: [dx, y, dz] });
  // a car dealer's forecourt: bunting, stock spots (park marks with sale: true)
  if (s.lot) {
    const [lx0, lz0, lx1, lz1] = s.lot;
    for (let x = lx0 + 3; x < lx1 - 2; x += 5.5) for (const z of [lz0 + 5, lz0 + 14]) { const yy = groundY(x, z); if (B.inside(x, z)) B.out.marks.push({ id: 'park', p: [x, yy, z], yaw: Math.PI / 2, sale: s.sid }); }
    for (let x = lx0; x < lx1; x += 4) if (B.inside(x, lz1)) B.prop('stringlights', x + 2, groundY(x + 2, lz1) + 3.2, lz1, 0, 1, 0);
  }
}
function vending(B, [x, z, yaw, district]) {
  if (!B.inside(x, z)) return;
  const y = district === 'gut' ? GY : district === 'commute' ? groundY(x, z) : (() => { for (let k = 0; k < SLICE.bottom.n; k++) if (z <= 256 - SLICE.bottom.terr * k && z > 256 - SLICE.bottom.terr * (k + 1)) return yB(k); return 0; })();
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
