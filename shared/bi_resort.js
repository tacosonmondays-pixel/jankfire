// THE ALL-INCLUSIVE (Battle Island, the lagoon's south-west shore: docs/maps/battleisland/DESIGN.md): a beach resort.
// The hotel along the north side (five storeys, the lobby open front to back, a balcony walk on every floor facing the
// pool, the stair tower at its east end up to the roof bar and the big rooftop letters), the porte-cochere where Resort
// Drive ends, the pool on its raised deck (the swim-up bar in the middle), cabanas along the lagoon, a jetty out into the
// lagoon with jet skis, the beach south with umbrellas, loungers and the lifeguard tower. Every piece is a Blender model
// over its boxes (tools/blender/make_resort.py reads its numbers from here with node), built at the ground's own height
// with its boxes `still`.
import { grid } from './battleisland.js';
import { propOf } from './propcap.js';
import { palm, rng } from './map.js';

const r3 = (v) => Math.round(v * 1000) / 1000;
const box6 = (a, b, c, d, e, f, m) => [r3(Math.min(a, d)), r3(Math.min(b, e)), r3(Math.min(c, f)), r3(Math.max(a, d)), r3(Math.max(b, e)), r3(Math.max(c, f)), m];
export const AI = {
  hotel: { x0: 158, x1: 200, z0: 80, z1: 92.5, g: 4.5, fh: 3.2, floors: 4, t: 0.3, slab: 0.3, // the block (outer faces), the lobby's height, the floors over it
    front: [170, 182, 3.4], back: [173.5, 178.5, 3.0], // the lobby's glass front: its doors (x0, x1, top); the back doors
    bal: 1.9, rail: 1.1, parapet: 1.1 }, // the balcony walk's depth (out from the front), rails; the roof's parapet
  tower: { x0: 200, x1: 205.6, z0: 81, z1: 94.4, w: 2.6, run: [85.4, 89.6], head: 2.6 }, // the stair tower: its footprint, each flight's width, the flights' z span, its head room over the top landing
  canopy: { x0: 168, x1: 184, z0: 92.5, z1: 101, h: 6.4, post: 0.5, roof: 0.6 }, // the porte-cochere (over the drive's end)
  deck: { x0: 184, x1: 210, z0: 98, z1: 126, h: 0.5 }, pool: { x0: 187, x1: 207, z0: 101, z1: 123 }, // the raised pool deck, the pool in it (its floor = the ground)
  bar: { c: [197, 112], hw: 2.6, h: 1.15, roof: 4.4, post: 0.25 }, // the swim-up bar: its counter's half-size, height (off the pool floor), its palapa roof
  cabanas: [[212.2, 101.5], [212.2, 108.0], [212.2, 114.5], [212.2, 121.0]], cabana: [3.6, 3.6, 3.2, 0.2], // centres; size x, z, roof height, post
  loungers: [[[188, 99.3], [192, 99.3], [196, 99.3], [200, 99.3], [204, 99.3], [208.6, 103], [208.6, 107], [208.6, 117], [208.6, 121], [185.5, 105], [185.5, 109], [185.5, 116], [185.5, 120]], // on the pool deck
    [[154, 143.5], [158, 143.5], [162, 143.5], [175, 143.5], [179, 143.5], [183, 143.5], [212, 134.5], [212, 138.5]]], // on the beach
  lounger: [0.75, 0.42, 2.0],
  umbrellas: [[156, 146.5], [164, 146.5], [177, 146.5], [185, 146.5], [214, 136.5], [189.5, 125.5], [206.0, 125.5]], umbrella: [2.4, 2.6],
  lifeguard: [169.5, 147.5], guard: [2.2, 4.6, 2.2], // the lifeguard tower: x, z; its size and height (the hut on top)
  jetty: { x0: 219, x1: 238, z: 104.5, w: 2.4, y: 0.75 }, // the jetty out into the lagoon (its deck's top, world)
  jetskis: [[231, 107.2, 0, 'carred'], [226, 107.2, 0, 'caryellow'], [233.5, 101.6, 2, 'carblue'], [178.5, 151.0, 1, 'cargreen'], [189.0, 150.5, 1, 'carred']], jetski: [3.2, 1.1, 1.2], // x, z, quarter turns, paint
  palms: [[161, 98], [166, 106], [158, 115], [164, 124], [172, 132], [182, 133], [211, 128], [214, 95], [152, 96], [152, 104], [176, 120]],
  sign: { x: 157, z: 107.5, h: 4.2, w: 7 }, // the welcome sign by the drive (two posts, the board between)
};

const groundAt = (x, z) => grid().at(x, z);
const Bx = (o) => (a, b, c, d, e, f, m = 'white') => o.push(box6(a, b, c, d, e, f, m));

// the hotel and its stair tower (one model): anchor = its front's middle at the ground (x middle, z = z1)
export function hotelBoxes() {
  const H = AI.hotel, Tw = AI.tower, cx = (H.x0 + H.x1) / 2, cz = H.z1, o = [], B = Bx(o), t = H.t;
  const X0 = H.x0 - cx, X1 = H.x1 - cx, Z0 = H.z0 - cz, Z1 = 0, top = H.g + H.floors * H.fh;
  // the lobby: its floor, the back wall (doors), the ends, the glass front (doors), the columns; the floors over it (rooms: shut)
  B(X0 + t, 0, Z0 + t, X1 - t, 0.12, Z1 - t, 'tile');
  const [b0, b1, bt] = H.back.map((v, i) => (i < 2 ? v - cx : v)), [f0, f1, ft] = H.front.map((v, i) => (i < 2 ? v - cx : v));
  B(X0, 0, Z0, b0, H.g, Z0 + t); B(b1, 0, Z0, X1, H.g, Z0 + t); B(b0, bt, Z0, b1, H.g, Z0 + t);
  B(X0, 0, Z0 + t, X0 + t, H.g, Z1); B(X1 - t, 0, Z0 + t, X1, H.g, Z1);
  B(X0 + t, 0, Z1 - 0.15, f0, H.g, Z1, 'glass'); B(f1, 0, Z1 - 0.15, X1 - t, H.g, Z1, 'glass'); B(f0, ft, Z1 - 0.15, f1, H.g, Z1, 'glass');
  for (const x of [X0 + 7, X0 + 14, X1 - 14, X1 - 7]) B(x - 0.3, 0, -6.5, x + 0.3, H.g, -5.9, 'white'); // the lobby's columns
  B(X0 + 3.0, 0, Z0 + 2.2, X0 + 9.5, 1.1, Z0 + 3.2, 'wood'); // the reception desk
  B(X0, H.g, Z0, X1, top, Z1, 'white'); // the rooms (shut)
  B(X0 - 0.2, top, Z0 - 0.2, X1 + 0.2, top + 0.3, Z1 + 0.2, 'white'); // the roof
  const gap = AI.tower.run[1] - cz; // (the east parapet's gap: where the stair tower comes up)
  for (const [a, c, d, e] of [[X0 - 0.2, Z0 - 0.2, X1 + 0.2, Z0], [X0 - 0.2, Z1, X1, Z1 + 0.2], [X0 - 0.2, Z0, X0, Z1], [X1, Z0, X1 + 0.2, gap]]) B(a, top + 0.3, c, d, top + 0.3 + H.parapet, e);
  const sy = top + 0.3 + H.parapet; B(-15, sy, Z1 - 0.5, 15, sy + 3.3, Z1 - 0.12, 'white'); // the big letters along the roof's front edge (cover up there)
  // the balcony walk on every floor: its slab out front, its rail (open at the tower's end)
  for (let k = 0; k < H.floors; k++) {
    const y = H.g + k * H.fh;
    B(X0, y - H.slab, Z1, X1, y, Z1 + H.bal);
    B(X0, y, Z1 + H.bal - 0.08, X1, y + H.rail, Z1 + H.bal); B(X0, y, Z1, X0 + 0.08, y + H.rail, Z1 + H.bal - 0.08);
  }
  // the stair tower: a landing at each floor (south, onto the balconies), mid landings north, switchback flights between
  const tx0 = Tw.x0 - cx, tx1 = Tw.x1 - cx, tz0 = Tw.z0 - cz, tz1 = Tw.z1 - cz, [r0, r1] = Tw.run.map((v) => v - cz), w = Tw.w;
  const levels = [0, ...Array.from({ length: H.floors }, (_, k) => H.g + k * H.fh), top + 0.3]; // ground, each floor, the roof's surface
  for (let i = 0; i + 1 < levels.length; i++) {
    const ya = levels[i], yb = levels[i + 1], ym = (ya + yb) / 2, n = Math.max(6, Math.round((yb - ya) / 2 / 0.27));
    if (i > 0) B(tx0, ya - 0.25, r1, tx1, ya, tz1); // the floor's landing (south)
    B(tx0, ym - 0.25, tz0, tx1, ym, r0); // the mid landing (north)
    for (let s = 1; s <= n; s++) { // up the west flight going north, back down... up the east flight going south
      const ya1 = ya + (ym - ya) * s / n, yb1 = ym + (yb - ym) * s / n, za = r1 - (r1 - r0) * (s - 1) / n, zb = r1 - (r1 - r0) * s / n;
      B(tx0, ya1 - 0.15, Math.min(za, zb), tx0 + w, ya1, Math.max(za, zb));
      const zc = r0 + (r1 - r0) * (s - 1) / n, zd = r0 + (r1 - r0) * s / n;
      B(tx1 - w, yb1 - 0.15, zc, tx1, yb1, zd);
    }
  }
  const ttop = levels.at(-1);
  B(tx0, ttop - 0.25, r1, tx1, ttop, tz1); // the roof's landing (west onto the roof through the parapet's gap)
  B(tx0, 0, r1, tx1, 0.12, tz1, 'concrete'); // its ground landing (the first flight starts at the south)
  for (const [a, c, d, e] of [[tx1 - 0.1, tz0, tx1, tz1], [tx0, tz0, tx1, tz0 + 0.1]]) B(a, 0.12, c, d, ttop + Tw.head, e, 'white'); // its outer screen walls (east, north)
  B(tx0, ttop + Tw.head, tz0, tx1, ttop + Tw.head + 0.3, tz1, 'white'); // its roof (the flights come up onto the hotel's roof at the top)
  return o;
}
export function canopyBoxes() { // anchor = its middle at the ground
  const C = AI.canopy, L = C.x1 - C.x0, W = C.z1 - C.z0, X = L / 2, Z = W / 2, o = [], B = Bx(o), p = C.post;
  for (const sx of [-1, 1]) B(sx * X - (sx > 0 ? p : 0), 0, Z - p, sx * X + (sx < 0 ? p : 0), C.h, Z); // two posts out at the front (the back rests on the hotel)
  B(-X - 0.3, C.h, -Z, X + 0.3, C.h + C.roof, Z + 0.3);
  return o;
}
export function deckBoxes() { // anchor = the deck's middle at the ground: the deck round the pool, the pool's coping
  const D = AI.deck, P = AI.pool, cx = (D.x0 + D.x1) / 2, cz = (D.z0 + D.z1) / 2, o = [], B = Bx(o), h = D.h;
  const X0 = D.x0 - cx, X1 = D.x1 - cx, Z0 = D.z0 - cz, Z1 = D.z1 - cz, p0 = P.x0 - cx, p1 = P.x1 - cx, q0 = P.z0 - cz, q1 = P.z1 - cz;
  B(X0, 0, Z0, X1, h, q0, 'tile'); B(X0, 0, q1, X1, h, Z1, 'tile'); B(X0, 0, q0, p0, h, q1, 'tile'); B(p1, 0, q0, X1, h, q1, 'tile');
  // the swim-up bar in the middle of the pool, its palapa roof on four posts
  const Bc = AI.bar, bx = Bc.c[0] - cx, bz = Bc.c[1] - cz, hw = Bc.hw, pp = Bc.post;
  B(bx - hw, 0, bz - hw, bx + hw, Bc.h, bz + hw, 'wood');
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) B(bx + sx * (hw - 0.4) - pp / 2, Bc.h, bz + sz * (hw - 0.4) - pp / 2, bx + sx * (hw - 0.4) + pp / 2, Bc.roof, bz + sz * (hw - 0.4) + pp / 2, 'wood');
  B(bx - hw - 1.0, Bc.roof, bz - hw - 1.0, bx + hw + 1.0, Bc.roof + 0.5, bz + hw + 1.0, 'wood'); B(bx - hw * 0.5, Bc.roof + 0.5, bz - hw * 0.5, bx + hw * 0.5, Bc.roof + 1.95, bz + hw * 0.5, 'wood'); // (its thatch's peak)
  return o;
}
export function cabanaBoxes() { const [sx, sz, h, p] = AI.cabana, X = sx / 2, Z = sz / 2, o = [], B = Bx(o);
  for (const a of [-1, 1]) for (const b of [-1, 1]) B(a * (X - 0.3) - p / 2, 0, b * (Z - 0.3) - p / 2, a * (X - 0.3) + p / 2, h, b * (Z - 0.3) + p / 2, 'wood');
  B(-X, h, -Z, X, h + 0.7, Z, 'wood'); B(-X / 2, h + 0.7, -Z / 2, X / 2, h + 1.8, Z / 2, 'wood'); B(-X + 0.6, 0, -Z + 0.6, X - 0.6, 0.5, Z - 0.6, 'cloth'); return o; } // the posts, the thatch (its peak), the daybed
export const loungerBoxes = () => { const [w, h, l] = AI.lounger; return [box6(-w / 2, 0, -l / 2, w / 2, h, l / 2, 'white'), box6(-w / 2, h, -l / 2, w / 2, 0.9, -l / 2 + 0.6, 'white')]; }; // (its seat, its back propped up)
export const umbrellaBoxes = () => { const [r, h] = AI.umbrella; return [box6(-0.06, 0, -0.06, 0.06, h - 0.3, 0.06, 'metal'), box6(-r / 2, h - 0.3, -r / 2, r / 2, h, r / 2, 'cloth')]; };
export function lifeguardBoxes() { const [w, h, d] = AI.guard, o = [], B = Bx(o);
  for (const a of [-1, 1]) for (const b of [-1, 1]) B(a * (w / 2 - 0.15) - 0.1, 0, b * (d / 2 - 0.15) - 0.1, a * (w / 2 - 0.15) + 0.1, h - 2.2, b * (d / 2 - 0.15) + 0.1, 'wood');
  B(-w / 2, h - 2.2, -d / 2, w / 2, h - 2.0, d / 2, 'wood'); // its platform
  B(-w / 2, h - 2.0, -d / 2, w / 2, h - 1.0, -d / 2 + 0.1, 'wood'); B(-w / 2, h - 2.0, -d / 2 + 0.1, -w / 2 + 0.1, h - 1.0, d / 2, 'wood'); B(w / 2 - 0.1, h - 2.0, -d / 2 + 0.1, w / 2, h - 1.0, d / 2, 'wood'); // its hut's half walls (open to the sea)
  B(-w / 2 - 0.2, h - 0.2, -d / 2 - 0.2, w / 2 + 0.2, h, d / 2 + 0.2, 'roof'); // its roof
  for (let s = 1; s <= 8; s++) { const y = (h - 2.2) * s / 8, z = d / 2 + 2.4 - 2.4 * s / 8; B(-0.5, y - 0.08, z, 0.5, y, z + 0.3, 'wood'); } // its ladder (from the sea side)
  B(w / 2 - 0.1, h, d / 2 - 0.1, w / 2, h + 1.6, d / 2, 'metal'); // its flagpole
  return o; }
export function jettyBoxes() { const J = AI.jetty, L = J.x1 - J.x0, Z = J.w / 2; return [box6(-L / 2, -0.25, -Z, L / 2, 0, Z, 'wood'), ...[-L / 2 + 5, L / 2 - 4].map((x) => box6(x - 0.18, 0, Z - 0.38, x + 0.18, 2.68, Z - 0.02, 'metal'))]; } // anchor = its deck's middle at the deck's top (its two lamps)
export const jetskiBoxes = () => { const [l, h, w] = AI.jetski; return [box6(-l / 2, 0, -w / 2, l / 2, h, w / 2, 'white')]; };
export function signBoxes() { const S = AI.sign, o = [], B = Bx(o); for (const sx of [-1, 1]) { B(sx * S.w / 2 - 0.2, 0, -0.2, sx * S.w / 2 + 0.2, S.h, 0.2, 'wood'); B(sx * S.w / 2 - 0.45, S.h, -0.45, sx * S.w / 2 + 0.45, S.h + 0.5, 0.45, 'wood'); } B(-S.w / 2 - 0.17, S.h - 1.8, -0.15, S.w / 2 + 0.17, S.h, 0.15, 'white'); return o; }

// a piece's boxes at (x, z) on the ground (or at y), q quarter turns, as model `id`
function piece(B, id, boxes, x, z, q = 0, o = {}, y = null) {
  const c = [1, 0, -1, 0][q & 3], s = [0, 1, 0, -1][q & 3], S = { still: 1 };
  if (y === null) { y = 1e9; for (const [x0, , z0, x1, , z1] of boxes) for (const [u, v] of [[x0, z0], [x1, z0], [x0, z1], [x1, z1], [(x0 + x1) / 2, (z0 + z1) / 2]]) y = Math.min(y, groundAt(x + u * c + v * s, z - u * s + v * c)); }
  propOf(id, [x, y, z], q * Math.PI / 2, () => { for (const [x0, y0, z0, x1, y1, z1, m] of boxes) B.add(x + x0 * c + z0 * s, y + y0, z - x0 * s + z0 * c, x + x1 * c + z1 * s, y + y1, z - x1 * s + z1 * c, m, S); }, o);
  return y;
}

export function resort(B) {
  const H = AI.hotel, C = AI.canopy, D = AI.deck;
  const hy = piece(B, 'ai_hotel', hotelBoxes(), (H.x0 + H.x1) / 2, H.z1);
  piece(B, 'ai_canopy', canopyBoxes(), (C.x0 + C.x1) / 2, (C.z0 + C.z1) / 2, 0, {}, hy);
  const dy = piece(B, 'ai_deck', deckBoxes(), (D.x0 + D.x1) / 2, (D.z0 + D.z1) / 2, 0, {}, hy);
  for (const [x, z] of AI.cabanas) piece(B, 'ai_cabana', cabanaBoxes(), x, z);
  const tints = ['pink', 'yellow', 'blue', 'mint', 'white'];
  AI.loungers.forEach((list, k) => list.forEach(([x, z], i) => { // (on the deck: along z on the deck's sides, along x on its north edge)
    piece(B, 'ai_lounger', loungerBoxes(), x, z, 0, { t: tints[i % tints.length] }, k === 0 ? dy + D.h : null);
  }));
  AI.umbrellas.forEach(([x, z], i) => piece(B, 'ai_umbrella', umbrellaBoxes(), x, z, 0, { t: tints[(i + 2) % tints.length] }, z > 124 && z < 127 ? dy + D.h : null));
  piece(B, 'ai_lifeguard', lifeguardBoxes(), AI.lifeguard[0], AI.lifeguard[1]);
  const J = AI.jetty; piece(B, 'ai_jetty', jettyBoxes(), (J.x0 + J.x1) / 2, J.z, 0, {}, J.y);
  for (const [x, z, q, t] of AI.jetskis) { const y = Math.max(groundAt(x, z), -0.55); piece(B, 'ai_jetski', jetskiBoxes(), x, z, q, { t }, y); } // (afloat at the jetty: their hulls in the water)
  piece(B, 'ai_sign', signBoxes(), AI.sign.x, AI.sign.z);
  const W = B.local(0, 0, 0), r = rng(6060); for (const [x, z] of AI.palms) palm(W, x, z, 7 + r() * 3, r);
}
