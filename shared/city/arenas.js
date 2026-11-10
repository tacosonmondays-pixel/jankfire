// Boss arenas built for multi-phase fights (boss_fights.js: arena.layout / vertical / grapple / hazards / cover).
// The world builds the ground, the levels, the static grapple points and the hazard zones; everything that moves or
// breaks in the fight (the truck, cover, staples, adds) is a mark the fight spawns as an entity, so the world stays
// static and the set pieces stay free to wreck things.
// Marks: 'arena.<boss>' { rect, y } the arena; 'arena.boss' / 'arena.player' / 'arena.add' spawns; 'arena.cover'
// { what, yaw }; 'arena.truck' { size, crane, ramp }; 'arena.staples' { box } walls his missed staples stick in.
import { SLICE } from './slice.js';
import { rng } from './plan.js';
import { cube, hook, line, PASTEL, pick } from './kit.js';

// THE GUT BORDER GATE (overtime_1, m04 CLOCKING IN): the top of the Long Stairs where the pastel houses start to grow
// skin. A wide landing; the Gristle & Sons truck backs onto it (an entity: it rolls down the stairs at 25%); three
// stacked house-roofs on the left with washing-line poles on every roof (swing between them, zip back down); two Gut
// lungs on the right that bounce you from the landing to the roofs; acid gutters where the Gut starts.
// Three levels: the stairs, the landing, the roofs.
export const GATE_ARENA = { rect: [-78, -46, -10, 0], y: SLICE.border.y };
export const inGateArena = (x0, z0, x1, z1) => { const r = GATE_ARENA.rect; return x0 < r[2] && x1 > r[0] && z0 < r[3] && z1 > r[1]; };

export function gateArena(B) {
  const [ax0, az0, ax1, az1] = GATE_ARENA.rect, y = GATE_ARENA.y, G = SLICE.gate, r = rng(0x0417);
  if (!B.touches(GATE_ARENA.rect, 4)) return;
  // the landing: old municipal paving going to gum at the north end
  B.add(ax0 + 14, y - 0.02, az0 + 22, ax1 - 4, y + 0.03, az1 - 1, 'tile', { nc: true, tint: 0xd8c8c0 });
  B.add(ax0 + 14, y - 0.02, az0 + 3, ax1 - 4, y + 0.03, az0 + 22, 'gums', { nc: true });
  // the left: three stacked house-roofs climbing west (1, 2, 3 floors), a pole with a ring on every roof and washing
  // lines between them and down to the landing (zip back down)
  const stacks = [[-60, 1], [-66.5, 2], [-73, 3]], tops = [];
  for (const [sx, n] of stacks) {
    let fy = y, top = y;
    for (let f = 0; f < n; f++) { const c = cube(B, sx, fy, -13, 6, 14, 2.8, r, { door: f ? 1 : 1, tint: pick(r, PASTEL) }); fy = top = c.top; }
    if (B.inside(sx, -13)) B.add(sx - 3, top, -20, sx + 3, top + 0.25, -6, 'concrete', { tint: 0xc8b8b0 }); // a flat roof to fight on
    const pole = [sx + 1.8, top, -8];
    if (B.inside(pole[0], pole[2])) B.add(pole[0] - 0.1, top, pole[2] - 0.1, pole[0] + 0.1, top + 5.2, pole[2] + 0.1, 'rust');
    hook(B, pole[0], top + 5.8, pole[2], { s: 1.3 });
    tops.push([pole[0], top + 5, pole[2]]);
  }
  for (let i = 0; i + 1 < tops.length; i++) line(B, tops[i + 1], tops[i], { zip: true, hang: ['laundry_a', 'laundry_b'], mat: 'metal' }); // roof to roof
  line(B, tops[0], [-46, y + 3.2, -6], { zip: true, hang: ['laundry_b'], mat: 'metal' }); // down onto the landing
  if (B.inside(-46, -6)) B.add(-46.1, y, -6.1, -45.9, y + 3.4, -5.9, 'rust');
  if (B.inside(-66, -6)) B.out.marks.push({ id: 'arena.staples', p: [-66, y, -6], box: [-76, y, -6.2, -57, y + 8.6, -5.8] }); // the house fronts: missed staples stick here
  // the right: two Gut lungs, landing -> roof height
  for (const [lx, lz] of [[-18, -10], [-16, -24]]) {
    if (!B.inside(lx, lz)) continue;
    B.prop('lung', lx, y, lz, r() * 6.28, 0.85, 0);
    B.add(lx - 2.2, y, lz - 2.2, lx + 2.2, y + 1, lz + 2.2, 'flesh', { hide: true });
    B.out.triggers.push({ kind: 'bounce', box: [lx - 2.4, y + 0.6, lz - 2.4, lx + 2.4, y + 2.6, lz + 2.4], v: 21, name: 'LUNG' });
  }
  // a mast on the right so the landing has a high point both sides (and the gate's arch top is a ring too)
  if (B.inside(-14, -36)) { B.add(-14.2, y, -36.2, -13.8, y + 13, -35.8, 'rust', { tint: 0xff7ab0 }); }
  hook(B, -14, y + 13.7, -36, {});
  hook(B, G.x, y + 13.7, G.z, { s: 2 });
  // the acid gutters at the foot of the Gut's cliff (6 HP/s; the collectors won't step in them), open at the gate stairs
  for (const [gx0, gx1] of [[ax0 + 2, G.x - 4], [G.x + 4, ax1 - 1]]) {
    const ga = Math.max(gx0, B.X0), gb = Math.min(gx1, B.X1);
    if (gb <= ga || !B.touches([ga, -46, gb, -43.5])) continue;
    B.add(ga, y - 0.6, -45.6, gb, y - 0.05, -43.8, 'acid', { nc: true });
    B.out.triggers.push({ kind: 'acid', box: [ga, y - 1, -45.6, gb, y + 0.4, -43.8], dps: 6 });
    if (B.inside((ga + gb) / 2, -44.7)) B.light((ga + gb) / 2, y + 0.8, -44.7, 0xa6e22e, 10, 0.7);
  }
  // the fight's pieces (entities): spawns, the truck, cover
  if (B.inside(G.x, -12)) {
    B.out.marks.push(
      { id: 'gut:border', p: [G.x, y, -14] }, // (the writer's LOCATIONS id for this arena)
      { id: 'arena.overtime_1', p: [G.x, y, -14], rect: GATE_ARENA.rect, y, name: 'THE GUT BORDER GATE' },
      { id: 'arena.boss', p: [G.x + 2, y, -26], face: Math.PI }, // (facing the stairs)
      // Overtime's beats (story lane WP8 names): he walks in through the gate, sits on the top step of the Long Stairs for
      // the Coffee Break (facing the landing), and retreats up the bone stairs into the Gut. face = yaw (0 looks north, -z)
      { id: 'ot_enter', p: [G.x, y, -30], face: Math.PI },
      { id: 'ot_stairs', p: [G.x + 1.5, y - 0.2, 1.2], face: 0 },
      { id: 'ot_retreat', p: [G.x, SLICE.gut.y, -52], face: 0 },
      { id: 'arena.player', p: [G.x, y, -2], face: 0 }, // (facing the gate)
      ...[[-34, -6], [-30, -4], [-24, -14], [-38, -20]].map(([x, z]) => ({ id: 'arena.add', p: [x, y, z], kind: 'collector' })),
      // the Gristle & Sons truck: backed onto the landing (rear south, the ramp toward the stairs), the loading crane on
      // its left side reaching over the box (a grapple point), the ramp is the crush zone
      { id: 'arena.truck', p: [-29, y, -16], face: 0, size: [3, 4.2, 10], crane: [-31.5, y + 9.5, -12], ramp: [-30.5, y, -11, -27.5, y + 1.5, -7] },
      ...[[-52, -4], [-50, -18], [-36, -28], [-22, -6], [-40, -10], [-56, -26]].map(([x, z], i) => ({ id: 'arena.cover', p: [x, y, z], what: 'fridge', yaw: i * 0.7 })),
      ...[[-46, -14], [-26, -26], [-58, -32], [-20, -30]].map(([x, z], i) => ({ id: 'arena.cover', p: [x, y, z], what: 'laundry_cart', yaw: i * 1.3 })),
    );
  }  gateDress(B, y, G);
}

// the Gate dressed for the fight (static: nothing here breaks or blocks, so the fight's cover and set pieces stay
// free): the Timekeeping queue (rails of punch-clock posts, the Bottom's people waiting to be collected), the loading
// bay the truck backs into (hazard stripes; the ramp's crush zone), Overtime's 17:29 clock on the gate, floodlights
// for a readable fight, Leg Day's banner, and the intro's camera spots for the story lane ('arena.cam')
function gateDress(B, y, G) {
  const paint = (x0, z0, x1, z1, tint) => B.add(x0, y + 0.031, z0, x1, y + 0.045, z1, 'paint', { nc: true, tint });
  // the queue: three lanes of posts and tape snaking from the stairs to the truck's ramp
  const rows = [-3.2, -5.6, -8];
  rows.forEach((z, i) => {
    for (let x = -40; x <= -32; x += 2) { if (B.inside(x, z)) B.prop('punchpost', x, y, z, 0, 1, (x * 3) | 0); }
    if (i < rows.length - 1) for (let x = -40 + (i % 2 ? 2 : 0); x < -32 + (i % 2 ? 0 : -2) + 2; x += 2) if (B.inside(x + 1, z)) B.add(x, y + 0.9, z - 0.02, x + 2, y + 0.98, z + 0.02, 'paint', { nc: true, tint: i % 2 ? 0xffe14d : 0xff3030 }); // the tape
  });
  paint(-41, -9, -31, -2, 0x8a7a70); // the queue's worn patch
  if (B.inside(-36, -6)) for (let i = 0; i < 9; i++) B.out.marks.push({ id: 'crowd', kind: 'queue', p: [-39.2 + (i % 4) * 2, y, rows[i % 3] + 1.2], face: -Math.PI / 2 }); // they face the truck
  // the loading bay: yellow / black stripes round where the truck backs in, hazard hatching on the ramp (it crushes)
  const T0 = [-30.8, -21.2, -27.2, -11];
  for (const [x0, z0, x1, z1] of [[T0[0] - 0.3, T0[1], T0[0], T0[3]], [T0[2], T0[1], T0[2] + 0.3, T0[3]], [T0[0] - 0.3, T0[1] - 0.3, T0[2] + 0.3, T0[1]]]) paint(x0, z0, x1, z1, 0xffe14d);
  for (let z = -11; z < -7; z += 0.8) paint(-30.8, z, -27.2, z + 0.4, 0x111111), paint(-30.8, z + 0.4, -27.2, z + 0.8, 0xffe14d);
  // Overtime's clock on the gate arch: stopped at 17:29 like every clock in the district, but this one ticks
  if (B.inside(G.x, G.z)) { B.prop('punchclock_big', G.x, y + 7.2, G.z + 1.7, Math.PI, 1, 0); B.light(G.x, y + 8.5, G.z + 4, 0xfff4d0, 12, 1); }
  // floodlights (masts with a ring on top): the landing lit from both ends for the fight
  for (const [fx, fz, yaw] of [[-16, -2, Math.PI * 0.75], [-56, -40, -Math.PI * 0.25]]) {
    if (B.inside(fx, fz)) { B.add(fx - 0.2, y, fz - 0.2, fx + 0.2, y + 11, fz + 0.2, 'metal', { tint: 0x9aa0a8 }); B.prop('floodlight', fx, y + 11, fz, yaw, 1, 0); B.light(fx - Math.sin(yaw) * 10, y + 6, fz - Math.cos(yaw) * 10, 0xfff0d0, 26, 1.4); }
    hook(B, fx, y + 12.6, fz, {});
  }
  // Leg Day's banner across the first roof's front (Lumps carried the fridges up for it)
  if (B.inside(-60, -6)) B.add(-62.6, y + 3.3, -5.9, -57.4, y + 4.5, -5.8, 'tiedye', { nc: true });
  // the intro's camera spots (story lane): a wide from over the stairs, the gate close-up, the roofs looking down
  if (B.inside(G.x, -12)) B.out.marks.push(
    { id: 'arena.cam', name: 'wide', p: [-22, y + 9, 6], look: [G.x, y + 5, G.z] },
    { id: 'arena.cam', name: 'gate', p: [G.x + 3, y + 2.2, -15], look: [G.x, y + 6, G.z] },
    { id: 'arena.cam', name: 'roofs', p: [-73, y + 11.5, -4], look: [-36, y + 1, -14] },
  );
}
