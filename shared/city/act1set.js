// Act I's set dressing for the places the missions point at (the world wiring pass): the Wok Roofs over the Lost &
// Found's yard, the service tunnel door under the depot, the Digester Wall on Peristalsis Avenue, Bev's back-room
// clinic on the Gut border and the Under-Hill Loop's portal in the Commute's east cliff. Visual only: props, render-only
// (nc) boxes, lights and marks, so no collision moves (tests/story/act1world.test.mjs checks). Each district generator
// calls its pass last. Spots come from PLACES (slice.js), so a place and its dressing move together.
import { SLICE, PLACES, groundY, hwY } from './slice.js';
import { rng } from './plan.js';
import { pick, hook, line } from './kit.js';

const P = (id) => PLACES[id].p;
const mark = (B, id) => { const p = P(id); if (B.inside(p[0], p[2])) B.out.marks.push({ id, p: p.slice() }); };
const FLESH = [0x8e1622, 0xa82430, 0x7a121c, 0xc23a40, 0xa8804a];

// the Wok Roofs' grapple rings, the washing line (a: on the tall roof, b: over the depot's steps) and its two poles
// (the yard's ring hangs off a gallows arm 1.3 m out past the tall roof's edge, 6.6 m up: the rope lifts you up beside
// the wall and over the edge, not into it, where you'd wedge under the roof lip. the lane-side ring is on a mast)
export const WOK = { ring: [-172.6, 23, 208.4], arm: [-172.9, -169.9, 208.4, 23.9], ring2: [-163.4, 18.9, 211.6], line: [[-170, 18.8, 206.5], [-188.5, 10.6, 206.4]], poles: [[-169.7, 16.4, 206.5, 2.6], [-188.2, 6.1, 206.4, 4.6], [-170.1, 16.4, 208.4, 7.7], [-163.4, 14.3, 211.6, 4.1]] };

// THE BOTTOM: the Wok Roofs (the house stack east of the yard: roofs at 16.4, 14.3 and 13.9 m) and the service tunnel
export function act1Bottom(B) {
  const R = P('bottom:rooftops');
  if (B.touches([R[0] - 12, R[2] - 8, R[0] + 12, R[2] + 8])) {
    // a wok satellite dish on every roof (aimed at the Spire, still waiting for the signal), bulbs between them
    for (const [x, y, z, yaw] of [[-169.2, 16.4, 206, 2.4], [-163.4, 14.3, 211.5, 0.6], [-157.5, 13.9, 206.5, -2.2], [-157, 13.9, 211, 3.4]]) B.prop('wokdish', x, y + 0.6, z, yaw, 1.7, 0);
    B.prop('stringlights', -165, 16.6, 208.5, 0.2, 1.2, 0); B.prop('pchair', -162, 14.3, 207, 1.2, 1, 3); B.prop('pchair', -158.6, 13.9, 209.2, -0.4, 1, 5); // (Dumpling's judges' chairs)
    B.prop('smilesign', -163.4, 14.3, 205.4, Math.PI, 0.8, 0); // the scoreboard
    B.light(-163.5, 18, 208.8, 0xffe14d, 14, 1.1);
    mark(B, 'bottom:rooftops');
  }
  // the tutorial's way up and back (m01: grapple onto the roofs, ride a washing line home): a yellow ring on a mast on
  // the tall roof (seen from the yard), one on the middle roof (seen from the lane), and Dumpling's washing line from the tall roof down over the
  // yard to the depot's front steps (grab it with F, it drops you at the door)
  hook(B, ...WOK.ring, { yaw: Math.PI / 2, s: 1.4 }); hook(B, ...WOK.ring2, { yaw: 0, s: 1.4 });
  { const [ax0, ax1, az, ay] = WOK.arm; if (B.touches([ax0, az - 1, ax1, az + 1])) B.add(ax0, ay, az - 0.1, ax1, ay + 0.22, az + 0.1, 'rust'); } // (the gallows arm)
  for (const [x, y0, z, h] of WOK.poles) if (B.inside(x, z)) { B.add(x - 0.12, y0, z - 0.12, x + 0.12, y0 + h, z + 0.12, 'rust'); B.light(x, y0 + h, z, 0xffe14d, 5, 0.6); }
  if (B.touches([WOK.line[1][0] - 1, WOK.line[0][2] - 2, WOK.line[0][0] + 1, WOK.line[1][2] + 2])) line(B, WOK.line[0], WOK.line[1], { zip: true, hang: ['laundry_a', 'laundry_b'], mat: 'metal', sag: 0.9 });
  // the service tunnel: a staff door in the retaining wall under the depot, rails out of it, a hazard frame, a lamp
  const T = P('bottom:service_tunnel'), tx = T[0], y = T[1], wz = SLICE.lostFound.rect[3];
  if (B.touches([tx - 6, wz - 1, tx + 6, wz + 10])) {
    B.add(tx - 1.4, y, wz, tx + 1.4, y + 2.7, wz + 0.04, 'paint', { nc: true, tint: 0x0c0a10 }); // the dark doorway
    for (const s of [-1, 1]) for (let i = 0; i < 6; i++) B.add(tx + s * 1.55 - 0.15, y + i * 0.5, wz, tx + s * 1.55 + 0.15, y + i * 0.5 + 0.25, wz + 0.06, 'paint', { nc: true, tint: i % 2 ? 0x111111 : 0xffe14d }); // hazard posts
    B.add(tx - 1.7, y + 2.7, wz, tx + 1.7, y + 3.3, wz + 0.06, 'paint', { nc: true, tint: 0xffe14d }); // the lintel: STAFF ONLY, in yellow
    B.add(tx - 1.2, y + 2.85, wz, tx + 1.2, y + 3.15, wz + 0.08, 'paint', { nc: true, tint: 0x111111 });
    for (const rx of [-0.55, 0.55]) B.add(tx + rx - 0.05, y + 0.01, wz, tx + rx + 0.05, y + 0.08, wz + 7, 'metal', { nc: true, tint: 0x8a8f99 }); // the rails, out to the yard
    for (let i = 0; i < 6; i++) B.add(tx - 0.9, y + 0.005, wz + 0.6 + i * 1.2, tx + 0.9, y + 0.04, wz + 0.9 + i * 1.2, 'wood', { nc: true, tint: 0x5a3a2a });
    B.prop('cone', tx - 2.2, y, wz + 1.2, 0.3, 1, 0); B.prop('cone', tx + 2.3, y, wz + 1.6, 1.1, 1, 0); B.prop('handtruck', tx + 2.6, y, wz + 0.6, 2.6, 1, 0);
    B.light(tx, y + 2.4, wz + 1.5, 0xff8a2a, 7, 1.2);
    mark(B, 'bottom:service_tunnel');
  }
}

// THE GUT: the Digester Wall, the face of the office block across Peristalsis Avenue from the tube (z -140): skin
// slabs, the Bottom's missing half grown in (mannequin faces), eyes, a sick pink lamp. Dot is IN it (cast_slice.js)
export function act1Gut(B) {
  const D = P('gut:digester_wall'), wz = -140, x0 = D[0] - 10, x1 = D[0] + 10, y = D[1];
  if (!B.touches([x0 - 2, wz - 2, x1 + 2, wz + 4])) return;
  const r = rng(4417);
  for (let x = x0; x < x1; x += 2 + r() * 2) { const h = 3 + r() * 8; B.add(x, y, wz - 0.02, Math.min(x1, x + 1.6 + r() * 2.4), y + h, wz + 0.22, 'flesh', { nc: true, tint: pick(r, FLESH) }); }
  for (let i = 0; i < 7; i++) { const x = x0 + 1 + i * 3 + (r() - 0.5); if (Math.abs(x - D[0]) < 1.2) continue; B.prop('mannequin', x, y - 0.3 - r() * 0.5, wz + 0.05, Math.PI + (r() - 0.5) * 0.5, 1, i); } // (Dot's spot is left free)
  for (let i = 0; i < 6; i++) B.prop('eyeball', x0 + r() * (x1 - x0), y + 2 + r() * 6, wz + 0.25, Math.PI, 0.8 + r() * 0.8, 0);
  for (let i = 0; i < 3; i++) B.prop(i % 2 ? 'fleshblob_a' : 'fleshblob_b', x0 + 2 + i * 7, y, wz + 0.5, r() * 6.28, 1.2, 0);
  B.light(D[0], y + 4, wz + 3, 0xff6f91, 12, 1.2);
  mark(B, 'gut:digester_wall');
}

// THE GUT BORDER: Bev's clinic, a back room in a pastel bungalow the skin is eating (x -89 .. -79.5, z -17.5 .. -4.5,
// its door on the south side): a dentist's chair, a bucket, a shelf of jars with dates on, a lamp over the door
export function act1Border(B) {
  const C = P('gut:clinic_bev'), cx = C[0], fy = C[1] + 0.12;
  if (!B.touches([cx - 7, -19, cx + 7, 0])) return;
  B.prop('dentist_chair', cx, fy, -11.6, Math.PI, 1.1, 0);
  B.prop('jar_shelf', -88.6, fy, -10.5, -Math.PI / 2, 1, 0); B.prop('jar_shelf', -88.6, fy, -14, -Math.PI / 2, 1, 1);
  B.prop('organjar', -80.6, fy, -15.8, 0.4, 1, 0); B.prop('firebarrel', -81, fy, -9.4, 0, 0.55, 0); // the bucket
  B.light(cx, fy + 2.4, -10, 0x9ae8ff, 8, 1.3);
  B.prop('heartlamp', cx + 1.4, C[1] + 2.4, -4.2, Math.PI, 0.8, 0); B.light(cx + 1.4, C[1] + 2.2, -3, 0xff6f91, 6, 1); // the sign of a meat mechanic
  mark(B, 'gut:clinic_bev');
}

// THE COMMUTE: the Under-Hill Loop comes out of the east cliff: a tunnel portal, rails across the wasteland to a
// broken viaduct stub (the tunnel mouth), signal lamps
export function act1Commute(B) {
  const L = P('commute:underhill_loop'), z = L[2], cliff = SLICE.x1 - 6, y = groundY(cliff - 1, z);
  if (!B.touches([L[0] - 24, z - 8, SLICE.x1, z + 8])) return;
  B.add(cliff - 0.06, y, z - 4, cliff, y + 6, z + 4, 'paint', { nc: true, tint: 0x08060c }); // the mouth: black
  B.add(cliff - 0.3, y + 6, z - 5, cliff, y + 7.2, z + 5, 'concrete', { nc: true, tint: 0xa8a098 }); // the arch's lintel
  for (const s of [-1, 1]) B.add(cliff - 0.3, y, z + s * 4.5 - 0.5, cliff, y + 6, z + s * 4.5 + 0.5, 'concrete', { nc: true, tint: 0xa8a098 });
  B.add(cliff - 0.32, y + 6.3, z - 3, cliff - 0.28, y + 6.9, z + 3, 'paint', { nc: true, tint: 0x4fd8ff }); // the line's colour band (cyan: the Loop on the old map)
  for (const rz of [-0.75, 0.75]) B.add(L[0] - 22, y + 0.01, z + rz - 0.06, cliff, y + 0.1, z + rz + 0.06, 'metal', { nc: true, tint: 0x8a8f99 });
  for (let x = L[0] - 22; x < cliff; x += 1.4) B.add(x, y + 0.005, z - 1.2, x + 0.3, y + 0.05, z + 1.2, 'wood', { nc: true, tint: 0x4a3426 });
  B.prop('jersey', L[0] - 23, y, z, Math.PI / 2, 1, 0); B.prop('cone', L[0] - 21, y, z + 2.4, 0, 1, 0);
  for (const s of [-1, 1]) { B.add(cliff - 2, y, z + s * 5.6 - 0.12, cliff - 1.76, y + 4, z + s * 5.6 + 0.12, 'metal', { nc: true, tint: 0x2a2a30 }); B.light(cliff - 1.9, y + 4.2, z + s * 5.6, s < 0 ? 0xff3030 : 0x7dff4f, 6, 1.2); }
  B.light(cliff - 3, y + 3, z, 0x4fd8ff, 10, 0.8);
  mark(B, 'commute:underhill_loop'); mark(B, 'commute:tunnel_mouth');
}

// THE COMMUTE: the Unpaid's jump ramp over the collapsed span of the Ring Road (z 86-100; m02's ambush ends here). The
// barricades are open in the middle lane, a ramp of desks, doors and filing cabinets climbs from z 110 to a 3 m lip at
// the south edge of the gap, and a car doing ~20 m/s lands on the deck past it. Too slow: you drop into the gap (only
// half a metre deep: the deck sits at ground level here) and drive up the scrap ramp at its north end. Cars step 0.65 m
// (drive.js), the ramp's treads are 0.16 m. The rubble heap moved to the west lanes, out of the flight line.
export const RAMP = { x0: 179.4, x1: 185.6, z0: 100.2, z1: 110, lift: 3, rubbleX: 172.5, exit: [86, 91.5], open: (x) => x > 177.5 && x < 187.5, lane: (f) => f > 0.3 && f < 0.7 }; // lane: the jam's two middle lanes (fractions of the deck) are clear, so the run-up is a road
export function act1Ramp(B) {
  const R = RAMP, n = Math.ceil((R.z1 - R.z0) / 0.4), w = R.x1 - R.x0;
  if (!B.touches([R.x0 - 4, R.exit[0] - 2, R.x1 + 4, R.z1 + 4])) return;
  const r = rng(13013), top = (z) => hwY(z) + R.lift * (R.z1 - z) / (R.z1 - R.z0); // (the deck under it, plus the climb)
  for (let i = 0; i < n; i++) { // the treads: alternating office desk wood and door paint, a little uneven (jank)
    const za = R.z0 + i * 0.4, zb = Math.min(R.z1, za + 0.4), y = top(za);
    B.add(R.x0, hwY(zb) - 0.3, za, R.x1, y, zb, i % 3 ? 'wood' : 'paint', { tint: i % 3 ? pick(r, [0x8a6a4a, 0x9a7a52, 0x6e5238]) : pick(r, [0xe8e0d0, 0x5fd3c6, 0xff7a9a]) });
  }
  for (const sx of [R.x0 - 0.3, R.x1 + 0.3]) for (let z = R.z0 + 0.6; z < R.z1 - 1; z += 2.2) B.prop(r() < 0.5 ? 'filecab' : 'raider_cabinet', sx, hwY(z), z, r() * 0.4 - 0.2 + (sx < R.x0 ? Math.PI / 2 : -Math.PI / 2), 1, (r() * 8) | 0); // filing cabinets holding it up
  B.prop('raider_chair', R.x0 + 1, top(R.z0 + 0.3), R.z0 + 0.3, Math.PI, 1, 2); B.prop('cone', R.x1 - 0.8, top(R.z0 + 0.4), R.z0 + 0.4, 0, 1, 0); // (someone sat up there to watch)
  for (const sx of [R.x0, R.x1]) B.light(sx, top(R.z0) + 1.2, R.z0, 0xffe14d, 7, 1.1);
  // the way out of the gap for anyone who came up short: a scrap ramp from the gap's floor up onto the north deck
  const [e0, e1] = R.exit, m = Math.ceil((e1 - e0) / 0.5);
  for (let i = 0; i < m; i++) { const za = e0 + i * 0.5, zb = za + 0.5, k = 1 - (i + 0.5) / m; B.add(R.x0, groundY(R.x0 + w / 2, za) - 0.2, za, R.x1, groundY(R.x0 + w / 2, za) + (hwY(e0) - groundY(R.x0 + w / 2, za)) * k, zb, 'wood', { tint: 0x6e5238 }); }
  if (B.inside((R.x0 + R.x1) / 2, R.z1 + 6)) B.out.marks.push({ id: 'commute.ramp', p: [(R.x0 + R.x1) / 2, hwY(R.z1 + 6), R.z1 + 6], face: Math.PI }); // (the run-up: JUMP IT)
}
