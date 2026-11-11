// Act I's set dressing for the places the missions point at (the world wiring pass): the Wok Roofs over the Lost &
// Found's yard, the service tunnel door under the depot, the Digester Wall on Peristalsis Avenue, Bev's back-room
// clinic on the Gut border and the Under-Hill Loop's portal in the Commute's east cliff. Visual only: props, render-only
// (nc) boxes, lights and marks, so no collision moves (tests/story/act1world.test.mjs checks). Each district generator
// calls its pass last. Spots come from PLACES (slice.js), so a place and its dressing move together.
import { SLICE, PLACES, groundY } from './slice.js';
import { rng } from './plan.js';
import { pick } from './kit.js';

const P = (id) => PLACES[id].p;
const mark = (B, id) => { const p = P(id); if (B.inside(p[0], p[2])) B.out.marks.push({ id, p: p.slice() }); };
const FLESH = [0x8e1622, 0xa82430, 0x7a121c, 0xc23a40, 0xa8804a];

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
