// JANKBURG: the big Battle Royale city (docs/CITY_DESIGN.md). A walled corporate city, 360 x 360 m inside the
// "firewall", an outer ring of sprawl out to 250 m, the megacity in the haze beyond. Six districts, each a POI that
// bends one rule while you're inside it (shared/royale.js), a plaza with a smiling fountain in the middle.
// PLAN is the master plan (all numbers in metres, x east, z south, north = -z); build() turns it into boxes.
// Collisions are boxes like every other map; anything decorative and turned goes in deco.

export const PLAN = {
  wall: { half: 180, h: 14, t: 4, chamfer: 26, towerEvery: 60 },
  ground: 250, // walkable ground out to here (the outer ring)
  gates: [ // name, centre, which wall
    { id: 'N', name: 'Data Gate', x: 0, z: -180, axis: 'x' },
    { id: 'S', name: 'Freight Gate', x: 0, z: 180, axis: 'x' },
    { id: 'E', name: 'East Toll', x: 180, z: 0, axis: 'z' },
    { id: 'W', name: 'West Toll', x: -180, z: 0, axis: 'z' },
  ],
  breaches: [{ x: -180, z: 112, axis: 'z' }, { x: 116, z: -180, axis: 'x' }, { x: -104, z: 180, axis: 'x' }],
  // roads: [x0, z0, x1, z1, kind]. avenues run gate to gate (and on out as highway stubs), the ring road ~90 m out
  roads: [
    [-10, -250, 10, 250, 'avenue'], [-250, -10, 250, 10, 'avenue'],
    [-95, -95, 95, -85, 'ring'], [-95, 85, 95, 95, 'ring'], [-95, -85, -85, 85, 'ring'], [85, -85, 95, 85, 'ring'],
  ],
  plaza: [-32, -32, 32, 32],
  // side streets: polylines [[x, z], ...] with a width. crooked on purpose (an old downtown that grew), a couple of
  // diagonal cuts, a cul-de-sac. buildings line up along them facing the street, their backs make the alleys
  streets: [
    // Overdraft Heights: lanes squeezed between slum towers, one diagonal shortcut
    { name: 'Debt St', w: 7, pts: [[-85, -58], [-118, -64], [-146, -60], [-178, -66]] },
    { name: 'Credit Alley', w: 6, pts: [[-124, -178], [-128, -132], [-116, -104], [-122, -66], [-118, -10]] },
    { name: 'Minimum Payment Way', w: 7, pts: [[-85, -96], [-112, -122], [-150, -160], [-164, -178]] },
    { name: 'Late Fee Ln', w: 6, pts: [[-178, -118], [-150, -114], [-128, -132]] },
    // Corp Hill: wide, clean, nearly straight (they paid for the straight lines)
    { name: 'Dividend Rd', w: 9, pts: [[-85, -104], [-60, -106], [-10, -104]] },
    { name: 'Synergy St', w: 9, pts: [[10, -150], [40, -150], [60, -152], [85, -150]] },
    { name: 'Quarterly Way', w: 8, pts: [[62, -178], [64, -152]] },
    { name: 'Bonus Close', w: 8, pts: [[-58, -178], [-60, -160], [-60, -106]] },
    // Neon Market: a diagonal market street, a noodle lane, an arcade row
    { name: 'Market Diagonal', w: 8, pts: [[95, -40], [126, -64], [150, -86], [178, -104]] },
    { name: 'Arcade Row', w: 7, pts: [[104, -178], [100, -140], [104, -95]] },
    { name: 'Noodle Ln', w: 6, pts: [[95, -26], [130, -30], [152, -24], [178, -28]] },
    { name: 'Pixel Alley', w: 5, pts: [[140, -178], [136, -150], [150, -130], [152, -86]] },
    // Number Works: service roads between the factory yards
    { name: 'Conveyor Rd', w: 9, pts: [[-178, 56], [-140, 60], [-95, 58]] },
    { name: 'Remainder St', w: 8, pts: [[-150, 10], [-146, 30], [-150, 60]] },
    { name: 'Integer Rd', w: 9, pts: [[-95, 128], [-60, 126], [-30, 130]] },
    { name: 'Prime Ln', w: 7, pts: [[-178, 158], [-140, 160], [-122, 150], [-112, 178]] },
    // Liberal Lane: the lane itself winds south from the plaza, a cul-de-sac off it, a crescent on the west side
    { name: 'Liberal Lane', w: 8, pts: [[10, 44], [32, 48], [50, 62], [52, 85], [48, 112], [30, 128], [10, 132]] },
    { name: 'Lane Close', w: 7, pts: [[10, 150], [30, 152], [42, 160]], end: [44, 162, 11] },
    { name: 'Helping Crescent', w: 7, pts: [[-10, 44], [-34, 50], [-50, 70], [-52, 85]] },
    { name: 'Seconds Row', w: 7, pts: [[-10, 140], [-36, 138], [-58, 146], [-85, 148]] },
    // Pronoun Park: paths, not streets (drawn as paths), and the quay along the canal
    { name: 'Their Walk', w: 4, path: true, pts: [[95, 40], [116, 58], [140, 54], [162, 70], [170, 96]] },
    { name: 'Your Walk', w: 4, path: true, pts: [[95, 76], [112, 96], [128, 118], [150, 124], [178, 120]] },
    { name: 'Quay', w: 7, pts: [[60, 142], [120, 140], [178, 142]] },
  ],
  canal: { z0: 148, z1: 160, x0: 60, x1: 250 }, // a canal along the south of the park, out through the wall to the river
  pond: { x: 132, z: 92, r: 11 },
  // the six districts (POIs). rect = [x0, z0, x1, z1]; mod = the rule it bends (royale.js POI)
  districts: [
    { id: 'corp', name: 'Corp Hill', rect: [-60, -178, 60, -10], color: '#4fd8ff', loot: 0.25, mod: 'dividend', blurb: 'kills here pay a shareholder dividend: +25 armour' },
    { id: 'neon', name: 'Neon Market', rect: [60, -178, 178, -10], color: '#ff4fd8', loot: 0.1, mod: 'vending', blurb: 'shoot a vending machine, get a gadget' },
    { id: 'overdraft', name: 'Overdraft Heights', rect: [-178, -178, -60, -10], color: '#b07dff', loot: 0.1, mod: 'lowgrav', blurb: 'your credit score went negative and so did gravity' },
    { id: 'numbers', name: 'Number Works', rect: [-178, 10, -60, 178], color: '#ffe14d', loot: 0.2, mod: 'numbers', blurb: 'every hit is a lucky 7 or an unlucky 13' },
    { id: 'liberal', name: 'Liberal Lane', rect: [-60, 10, 60, 178], color: '#7dff4f', loot: 0.45, mod: 'large', blurb: 'liberal helpings: everything comes in a large' },
    { id: 'pronoun', name: 'Pronoun Park', rect: [60, 10, 178, 178], color: '#ff9a3a', loot: 0.05, mod: 'pronouns', blurb: 'no names in the park: everyone is THEY' },
  ],
  // landmarks: where the plan puts them (and the minimap draws them)
  landmarks: [
    { id: 'fountain', name: 'Smiling Fountain', x: 0, z: 0 },
    { id: 'cathedral', name: 'Cathedral of Shareholder Value', x: 38, z: -58 },
    { id: 'hq', name: 'JankCorp HQ', x: -34, z: -132 },
    { id: 'hall', name: 'Neon Market Hall', x: 118, z: -118 },
    { id: 'stacks', name: 'Smokestacks', x: -118, z: 128 },
    { id: 'letters', name: 'THEY / YOU / WE', x: 118, z: 96 },
    { id: 'blimp', name: 'Crashed Blimp', x: 214, z: -208 },
  ],
  outer: [ // what's in the outer ring
    { id: 'shanty', name: 'Sprawl', rect: [-250, -150, -184, 150] },
    { id: 'orchard', name: 'Plastic Orchard', rect: [-150, 184, 150, 250] },
    { id: 'crash', name: 'Crash Site', rect: [184, -250, 250, -150] },
    { id: 'highway', name: 'Highway Stubs', rect: [184, -14, 250, 14] },
  ],
};

// ------------------------------------------------------------ the build
import { MAPS, MAP_ORDER, prop, builder, rng, wall, stairs, shell, car, tree, streetlight, tower, horizon, home, lollipop, conifer, adBoard, stall, pot, groundHoles, unstick } from './map.js';
import { buildNav } from './nav.js';
import { outOfBounds } from './bounds.js';

const F = 3.4; // storey height
const pickR = (r, a) => a[(r() * a.length) | 0];
// facade colours per house variant (no two neighbours on a street share one: the lot packer checks)
const PAINT = ['sidepink', 'sidelemon', 'sidelilac', 'sidemint', 'sideorange', 'white', 'tenement', 'brick', 'magenta', 'plaster', 'roofteal', 'pink'];

// a point at distance t along polyline pts, and its direction
function along(pts, t) {
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[i + 1], l = Math.hypot(bx - ax, bz - az);
    if (t <= l || i === pts.length - 2) { const k = Math.min(1, t / l); return { p: [ax + (bx - ax) * k, az + (bz - az) * k], u: [(bx - ax) / l, (bz - az) / l] }; }
    t -= l;
  }
  return null;
}
const plen = (pts) => pts.slice(1).reduce((s, q, i) => s + Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]), 0);
// distance from a point to a polyline
function segDist(px, pz, pts) {
  let best = 1e9;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[i + 1], dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz || 1;
    const k = Math.max(0, Math.min(1, ((px - ax) * dx + (pz - az) * dz) / l2));
    best = Math.min(best, Math.hypot(px - ax - dx * k, pz - az - dz * k));
  }
  return best;
}
// does rect [x0, z0, x1, z1] come within m of the polyline? (sample its outline + middle)
function rectNear(r, pts, m) {
  for (let x = r[0]; x <= r[2] + 0.01; x += Math.max(1, (r[2] - r[0]) / 6)) for (let z = r[1]; z <= r[3] + 0.01; z += Math.max(1, (r[3] - r[1]) / 6)) if (segDist(x, z, pts) < m) return true;
  return false;
}
const overlap = (a, b, g = 0) => a[0] < b[2] + g && a[2] > b[0] - g && a[1] < b[3] + g && a[3] > b[1] - g;
const inside = (r, R, m = 0) => r[0] >= R[0] + m && r[2] <= R[2] - m && r[1] >= R[1] + m && r[3] <= R[3] - m;

// above the floors you can walk into: one solid block of facade (the windows are painted on), a roof you can stand on
function upper(L, w, d, from, floors, mat, roof) {
  const y0 = from * F + 0.3, y1 = floors * F + 0.3, hw = w / 2, hd = d / 2;
  L(-hw, y0, -hd, hw, y1, hd, mat);
  L(-hw - 0.2, y1, -hd - 0.2, hw + 0.2, y1 + 0.3, hd + 0.2, roof);
  L(-hw, y1 + 0.3, -hd, hw, y1 + 1.1, -hd + 0.3, mat); L(-hw, y1 + 0.3, hd - 0.3, hw, y1 + 1.1, hd, mat);
  return y1 + 0.3;
}
// ------------------------------------------------------------ the 12 houses (one kit, parts picked by variant)
// local frame like every builder: footprint x [-w/2, w/2], z [-d/2, d/2], the front door at -z (the street side)
export const VARIANTS = ['capsule', 'noodle', 'bodega', 'walkup', 'model', 'container', 'squat', 'dorm', 'arcade', 'pastel', 'biolab', 'pawn'];
function cityHouse(B, D, x, z, rot, w, d, v, paint, r) {
  const L = B.local(x, z, rot), Ld = D.local(x, z, rot), hw = w / 2, hd = d / 2;
  const sign = (y, mat) => Ld(-Math.min(2.6, hw - 0.6), y, -hd - 0.45, Math.min(2.6, hw - 0.6), y + 0.9, -hd - 0.2, mat, { fit: 1 });
  const awning = (y, mat) => L(-hw + 0.4, y, -hd - 1.8, hw - 0.4, y + 0.18, -hd, mat);
  const ac = (y) => { for (let i = 0; i < 1 + ((r() * 3) | 0); i++) L.B(-hw + 2 + i * 2.4, y + 0.6, hd - 1.6, 1.8, 1.2, 1.2, 'metal'); };
  let floors = 2, top;
  switch (v) {
    case 'capsule': { // stacked sleep pods: tiny windows everywhere, ladders up the front
      floors = 3 + ((r() * 2) | 0);
      ({ top } = shell(L, w, d, 1, F, 'white', { floor: 'tile', roof: 'roofteal', winSpacing: 3, backDoor: true, parapet: false }));
      top = upper(L, w, d, 1, floors, 'white', 'roofteal');
      for (let f = 1; f < floors; f++) L(-hw - 0.05, f * F + 0.2, -hd - 0.9, hw + 0.05, f * F + 0.35, -hd, 'grid'); // pod balconies
      L(hw - 1.2, 0, -hd - 0.95, hw - 1.0, top, -hd - 0.75, 'metal'); L(hw - 0.4, 0, -hd - 0.95, hw - 0.2, top, -hd - 0.75, 'metal');
      sign(2.7, 'neonhotel'); ac(top);
      break;
    }
    case 'noodle': { // noodle shop with a flat above: open front, counter, steaming pots
      ({ top } = shell(L, w, d, 1, F, paint, { floor: 'tile', roof: 'roofg', backDoor: true, winSpacing: 5.5, parapet: false })); top = upper(L, w, d, 1, 2, paint, 'roofg');
      awning(2.6, pickR(r, ['cloth', 'toypink', 'toyyellow'])); sign(2.9, 'neonnoodle');
      L(-hw + 1, 0.12, -hd + 1.4, hw - 1, 1.05, -hd + 2.1, 'wood'); // counter
      for (let i = 0; i < 3; i++) L.B(-hw + 2 + i * 2, 1.35, -hd + 1.75, 0.7, 0.6, 0.7, 'chrome');
      for (let i = 0; i < 4; i++) L.B(-hw + 1.5 + i * 1.6, 0.4, -hd + 0.6, 0.5, 0.8, 0.5, 'seat');
      break;
    }
    case 'bodega': { // corner shop, a garden on the roof
      ({ top } = shell(L, w, d, 1, F, paint, { floor: 'tile', roof: 'roofg', backDoor: true, sideDoor: [-1.5, 0], winSpacing: 5.5, parapet: false })); top = upper(L, w, d, 1, 2, paint, 'roofg');
      awning(2.6, 'toyteal'); sign(2.9, 'signopen');
      for (let i = 0; i < 3; i++) L(-hw + 0.8, 0.12, -hd + 2.5 + i * 2.2, hw - 3, 1.6, -hd + 3.1 + i * 2.2, 'shelfstock');
      L(-hw + 0.5, top, -hd + 0.5, hw - 0.5, top + 0.25, 0, 'grass');
      L(-hw + 0.6, top + 0.25, -hd + 0.6, -hw + 3, top + 1.1, -hd + 1.2, 'hedge'); lollipop(L, hw - 2.5, -hd + 2.5, 2.2 + r(), r);
      break;
    }
    case 'walkup': { // narrow four-storey walk-up with a fire escape up the side
      floors = 4;
      ({ top } = shell(L, w, d, 1, F, paint, { floor: 'wood', roof: 'roofg', backDoor: true, parapet: false, winSpacing: 5, parapet: false }));
      top = upper(L, w, d, 1, floors, pickR(r, ['tenement', 'brick']), 'roofg');
      for (let f = 1; f < floors; f++) {
        L(hw, f * F + 0.15, -hd + 1, hw + 1.3, f * F + 0.3, hd - 1, 'grid'); // landing
        L(hw + 1.2, f * F + 0.3, -hd + 1, hw + 1.3, f * F + 1.3, hd - 1, 'metal'); // rail
      }
      for (let f = 0; f < floors - 1; f++) { // ladders between landings (climb them, or just jump: jank)
        const y = f * F + (f ? 0.3 : 0); for (let s = 0; s < 6; s++) L(hw + 0.2, y + s * 0.55, hd - 1.6 - s * 0.45, hw + 1.1, y + s * 0.55 + 0.12, hd - 1.1 - s * 0.45, 'metal');
      }
      sign(2.8, pickR(r, ['neonbar', 'neonwork'])); ac(top);
      break;
    }
    case 'model': { // the glossy "model home": shiny plastic, a lawn, a picket fence, a toy on the lawn (Liberal Lane)
      ({ top } = shell(L, w, d, 2, F, pickR(r, ['pink', 'toyteal', 'toyyellow', 'chrome']), { floor: 'carpet', roof: 'roofpink', roofAccess: false, backDoor: true, winSpacing: 5.5 }));
      L(-hw + 0.4, top, -hd + 0.4, hw - 0.4, top + 0.5, hd - 0.4, 'roofpink'); L(-hw + 1.6, top + 0.5, -hd + 1.6, hw - 1.6, top + 1, hd - 1.6, 'roofpink'); L(-hw + 3, top + 1, -hd + 3, hw - 3, top + 1.5, hd - 3, 'roofpink');
      L(-hw - 1, 0, -hd - 6, hw + 1, 0.06, -hd, 'lawn');
      L(-hw - 1, 0, -hd - 6.1, -1.2, 1.1, -hd - 5.9, 'picket'); L(1.2, 0, -hd - 6.1, hw + 1, 1.1, -hd - 5.9, 'picket');
      L(-1, 0.06, -hd - 6, 1, 0.12, -hd, 'sidewalk');
      if (r() < 0.5) L(-hw + 0.5, 0.06, -hd - 4.6, -hw + 2.8, 2.3, -hd - 2.3, 'toyface', { fit: 1 }); else lollipop(L, -hw + 1.8, -hd - 3, 3 + r() * 1.5, r);
      Ld(-1.6, 2.62, -hd - 0.33, 1.6, 3.1, -hd - 0.17, 'signopen', { fit: 1 });
      break;
    }
    case 'container': { // two rusted shipping containers stacked, a hole cut for the door
      const cm = pickR(r, ['containerr', 'containerg', 'containerb']);
      ({ top } = shell(L, w, d, 2, 2.9, cm, { floor: 'metal', roof: 'rust', roofAccess: true, backDoor: true, winSpacing: 5 }));
      L(-hw - 0.15, 2.9, -hd - 0.15, hw + 0.15, 3.1, hd + 0.15, 'rust'); // the seam
      L(-hw + 1, 0.12, hd - 2.5, -hw + 4, 1.1, hd - 1, 'pallet');
      break;
    }
    case 'squat': { // a tagged squat: plywood, graffiti, somebody kicked a hole in the side wall
      ({ top } = shell(L, w, d, 1, F, 'graffiti', { floor: 'plywood', roof: 'plywood', backDoor: true, sideDoor: [-2.5, 0.5], winSpacing: 5.5, parapet: false })); top = upper(L, w, d, 1, 2, 'graffiti', 'plywood');
      L(-hw + 0.5, 0.12, -hd + 1, -hw + 2.5, 0.6, -hd + 3.5, 'cardboard'); L(hw - 3, 0.12, hd - 3, hw - 1, 1.2, hd - 1, 'barrelr');
      L(-hw - 0.6, 0, -hd - 1.6, -hw + 1.6, 1.0, -hd - 0.5, 'jersey');
      break;
    }
    case 'dorm': { // corporate dorm block: five storeys of identical windows, a flag with the logo
      floors = 5;
      ({ top } = shell(L, w, d, 1, F, 'office', { floor: 'officecarpet', roof: 'roofg', backDoor: true, winSpacing: 5, parapet: false }));
      top = upper(L, w, d, 1, floors, 'office', 'roofg');
      Ld(-0.08, top, -hd + 1, 0.08, top + 6, -hd + 1.16, 'metal'); Ld(0.1, top + 3.6, -hd + 1, 3.1, top + 5.6, -hd + 1.12, 'flagcorp', { fit: 1 });
      L(-hw + 1, 0.12, -hd + 1, -hw + 3.5, 1.1, -hd + 2, 'marble'); // reception desk
      ac(top);
      break;
    }
    case 'arcade': { // an arcade with a flat on top: rows of cabinets, screens of static, loud neon
      ({ top } = shell(L, w, d, 1, F, 'magenta', { floor: 'carpetb', roof: 'roofg', backDoor: true, winSpacing: 5.5, parapet: false })); top = upper(L, w, d, 1, 2, 'magenta', 'roofg');
      for (let i = 0; i < Math.floor((w - 2) / 1.6); i++) for (const zz of [-hd + 2.6, 0.5]) { L.B(-hw + 1.6 + i * 1.6, 0.9, zz, 1, 1.8, 0.9, 'metal'); L.B(-hw + 1.6 + i * 1.6, 1.4, zz - 0.47, 0.8, 0.6, 0.05, 'tvstatic'); }
      sign(2.9, pickR(r, ['neonbar', 'neonhotel'])); Ld(-hw, 3.3, -hd - 0.2, hw, 3.45, -hd - 0.05, pickR(r, ['neonpink', 'neoncyan', 'neonyellow']));
      break;
    }
    case 'pastel': { // a pastel suburb house with a pitched toy roof and a porch
      ({ top } = shell(L, w, d, 2, F, paint, { floor: 'wood', roof: 'roofblue', backDoor: true, winSpacing: 5.5 }));
      const rm = pickR(r, ['roofpink', 'roofblue', 'roofteal']);
      L(-hw + 0.3, top, -hd + 0.3, hw - 0.3, top + 0.45, hd - 0.3, rm); L(-hw + 1.6, top + 0.45, -hd + 1.3, hw - 1.6, top + 0.9, hd - 1.3, rm); L(-hw + 2.9, top + 0.9, -hd + 2.3, hw - 2.9, top + 1.35, hd - 2.3, rm);
      L(-2.6, 0, -hd - 1.6, 2.6, 0.25, -hd, 'wood'); L(-2.8, 2.9, -hd - 1.8, 2.8, 3.1, -hd - 0.1, rm);
      L(-2.5, 0.25, -hd - 1.5, -2.25, 2.9, -hd - 1.25, 'wood'); L(2.25, 0.25, -hd - 1.5, 2.5, 2.9, -hd - 1.25, 'wood');
      break;
    }
    case 'biolab': { // a bio-lab front: green glass, vats bubbling inside
      ({ top } = shell(L, w, d, 1, F, 'glass', { floor: 'tile', roof: 'roofg', backDoor: true, winSpacing: 3, parapet: false })); top = upper(L, w, d, 1, 2, 'glass', 'roofg');
      for (let i = 0; i < 3; i++) { const vx = -hw + 2.5 + i * 2.8; L.B(vx, 1.1, 1, 1.8, 2, 1.8, 'poolwater'); L.B(vx, 2.2, 1, 2, 0.2, 2, 'chrome'); L.B(vx, 0.2, 1, 2, 0.3, 2, 'chrome'); }
      Ld(-hw, 2.6, -hd - 0.2, hw, 2.75, -hd - 0.05, 'neongreen');
      sign(2.9, 'neonwork');
      break;
    }
    case 'pawn': { // pawn + repair shop: a roller door you can walk through, tyres, a car on bricks
      ({ top } = shell(L, w, d, 1, F, paint, { floor: 'concrete', roof: 'roofg', backDoor: true, winSpacing: 5.5, parapet: false })); top = upper(L, w, d, 1, 2, paint, 'roofg');
      // the roller door, rolled up over the front
      L(-3, 2.6, -hd - 0.35, 3, 3.3, -hd + 0.05, 'metal');
      sign(3.5, 'signopen');
      for (let i = 0; i < 3; i++) L.B(hw - 1.4, 0.35 + i * 0.4, -hd + 1.5, 1, 0.38, 1, 'tire');
      if (w >= 12) car(L, 0, 1.5, 0, pickR(r, ['carred', 'carblue', 'cargreen', 'caryellow']));
      break;
    }
  }
  return { top: top || floors * F + 0.3 };
}

// ------------------------------------------------------------ district profiles: which houses, how big, what's behind them
const SIZE = { capsule: [8, 10, 8, 10], noodle: [10, 13, 10, 12], bodega: [10, 12, 10, 12], walkup: [7, 9, 11, 13], model: [12, 14, 10, 11], container: [6, 7, 12, 12], squat: [9, 11, 10, 12], dorm: [15, 18, 12, 14], arcade: [12, 15, 11, 13], pastel: [12, 13, 10, 11], biolab: [11, 13, 10, 12], pawn: [12, 14, 11, 12] };
const PROF = {
  overdraft: { v: ['capsule', 'walkup', 'squat', 'container', 'walkup', 'capsule'], fill: { mats: ['tenement', 'graffiti', 'brick', 'tenement'], h: [14, 42], p: 0.75 } },
  corp: { v: ['dorm', 'dorm', 'bodega', 'dorm'], fill: { mats: ['office', 'glass', 'office', 'concrete'], h: [20, 62], p: 0.8 } },
  neon: { v: ['noodle', 'arcade', 'pawn', 'capsule', 'noodle', 'arcade'], fill: { mats: ['magenta', 'tenement', 'graffiti', 'sidepink'], h: [8, 22], p: 0.7 } },
  numbers: { v: ['pawn', 'container', 'biolab', 'pawn', 'squat'], fill: { mats: ['brick', 'metal', 'rust', 'concrete'], h: [7, 16], p: 0.6 } },
  liberal: { v: ['model', 'pastel', 'model', 'pastel', 'bodega'], fill: null },
  pronoun: { v: ['pastel', 'bodega', 'noodle', 'pastel'], fill: null },
};
const districtAt = (x, z) => PLAN.districts.find((d) => x >= d.rect[0] && x <= d.rect[2] && z >= d.rect[1] && z <= d.rect[3]) || null;

function jankburg() {
  const B = builder(), D = builder(), r = rng(4242), rv = rng(4243);
  const H = PLAN.wall.half, G = PLAN.ground, WH = PLAN.wall.h, CH = PLAN.wall.chamfer;
  const reserved = [], placed = [], spawns = [], lootHints = [];
  // ---- roads (avenues, the ring, the side streets): the floor is one flat level, roads are paint on it
  const ring = [[-68, -90], [68, -90], [90, -68], [90, 68], [68, 90], [-68, 90], [-90, 68], [-90, -68], [-68, -90]];
  const roads = [
    { name: 'North Avenue', w: 20, pts: [[0, -G], [0, -34]], av: 'z' }, { name: 'South Avenue', w: 20, pts: [[0, 34], [0, G]], av: 'z' },
    { name: 'West Avenue', w: 20, pts: [[-G, 0], [-34, 0]], av: 'x' }, { name: 'East Avenue', w: 20, pts: [[34, 0], [G, 0]], av: 'x' },
    { name: 'Ring Road', w: 10, pts: ring }, ...PLAN.streets,
  ];
  const nearRoad = (rc, extra) => roads.some((s) => rectNear(rc, s.pts, s.w / 2 + extra));
  // ---- the ground: city paving inside the walls, dirt in the outer ring, the canal cut through both
  const cn = PLAN.canal;
  groundHoles(B, -H, -H, H, H, -2, 0, 'pavecity', [[cn.x0, cn.z0, H, cn.z1]]);
  groundHoles(B, -G, -G, G, G, -2, 0, 'dirt', [[-H, -H, H, H], [H, cn.z0, G, cn.z1]]);
  B.add(cn.x0, -5, cn.z0, G, -4, cn.z1, 'concrete'); // the canal bed (you can wade it)
  B.add(cn.x0 - 0.5, -4, cn.z0, cn.x0, 0, cn.z1, 'concrete');
  for (const z of [cn.z0, cn.z1]) B.add(cn.x0, -4, z - (z === cn.z0 ? 0.01 : 0), G, -2, z + (z === cn.z0 ? 0 : 0.01), 'concrete');
  D.add(cn.x0, -1.6, cn.z0 + 0.02, G + 600, -1.4, cn.z1 - 0.02, 'seawater'); // the water (render only: you walk the bed)
  for (const x of [80, 140, 210]) { // steps out of the canal on both banks
    stairs(B.local(0, 0, 0), x, x + 3, cn.z0 + 4.6, -1, -4, 0, 'concrete', 0.5);
    stairs(B.local(0, 0, 0), x + 20, x + 23, cn.z1 - 4.6, 1, -4, 0, 'concrete', 0.5);
  }
  // ---- paint: sidewalks, asphalt, the avenues' lane lines, the plaza
  for (const s of roads) {
    for (let i = 0; i < s.pts.length - 1; i++) {
      const [ax, az] = s.pts[i], [bx, bz] = s.pts[i + 1], l = Math.hypot(bx - ax, bz - az), yaw = Math.atan2(-(bz - az), bx - ax), cx = (ax + bx) / 2, cz = (az + bz) / 2;
      if (s.av) {
        const x0 = Math.min(ax, bx), x1 = Math.max(ax, bx), z0 = Math.min(az, bz), z1 = Math.max(az, bz);
        if (s.av === 'z') { D.add(x0 - 12.5, 0, z0, x0 + 12.5, 0.03, z1, 'sidewalk'); D.add(x0 - 10, 0, z0, x0 + 10, 0.05, z1, 'roadz'); }
        else { D.add(x0, 0, z0 - 12.5, x1, 0.03, z0 + 12.5, 'sidewalk'); D.add(x0, 0, z0 - 10, x1, 0.05, z0 + 10, 'roadx'); }
        continue;
      }
      if (!s.path) D.obb(cx, 0.015, cz, l + s.w + 4, 0.03, s.w + 5, yaw, 'sidewalk');
      D.obb(cx, 0.025, cz, l + s.w * (s.path ? 0.5 : 1), 0.05, s.w, yaw, s.path ? 'dirtroad' : 'asphalt');
    }
    if (s.end) { const [ex, ez, er] = s.end; for (let k = 0; k < 4; k++) D.obb(ex, 0.025, ez, er * 2, 0.05, er * 2 * 0.42, k * Math.PI / 4, 'asphalt'); D.obb(ex, 0.04, ez, er * 0.9, 0.05, er * 0.9, 0.4, 'lawn'); }
  }
  const P = PLAN.plaza;
  D.add(P[0], 0, P[1], P[2], 0.07, P[3], 'tile'); reserved.push([P[0] - 2, P[1] - 2, P[2] + 2, P[3] + 2]);
  for (const s of [-1, 1]) { D.add(-10, 0, s * 34 - 2, 10, 0.08, s * 34 + 2, 'crosswalk'); D.add(s * 34 - 2, 0, -10, s * 34 + 2, 0.08, 10, 'crosswalk'); }

  // ---- landmarks first (they reserve their ground)
  const L0 = B.local(0, 0, 0), Ld0 = D.local(0, 0, 0);
  fountain(B, D, r); plaza(B, D, rv);
  reserved.push([16, -84, 62, -34]); cathedral(B, D, 38, -58);
  reserved.push([-60, -162, -8, -108]); hq(B, D, -34, -135, r);
  reserved.push([94, -144, 144, -94]); marketHall(B, D, 119, -119, rv);
  reserved.push([138, -72, 176, -36]); stallSquare(B, 157, -54, rv);
  reserved.push([-176, 88, -98, 150]); numberWorks(B, D, -137, 119, rv);
  reserved.push([96, 28, 178, 136]); pronounPark(B, D, rv);
  for (const [x, z] of [[-158, -140], [-138, -86], [-92, -150], [-160, -32]]) { const rc = [x - 8, z - 8, x + 8, z + 8]; if (!nearRoad(rc, 1) && !reserved.some((q) => overlap(q, rc, 1))) { reserved.push(rc); slumTower(B, D, x, z, 6 + ((r() * 3) | 0), r); lootHints.push([x, z]); } }
  liberalArch(B, D, 18, 44);
  // ---- the walls, gates, towers, breaches
  cityWall(B, D, r);

  // ---- lots: houses along every street, facing it; the backs make the alleys
  const ok = (rc) => {
    const ds = districtAt((rc[0] + rc[2]) / 2, (rc[1] + rc[3]) / 2);
    if (!ds || !inside(rc, ds.rect, 1.5)) return null;
    if (reserved.some((q) => overlap(q, rc, 1)) || placed.some((q) => overlap(q, rc, 2.4))) return null;
    if (nearRoad(rc, 1.6)) return null;
    return ds;
  };
  const lastPaint = new Map();
  for (const s of roads) {
    if (s.path) continue;
    const len = plen(s.pts);
    for (const side of [-1, 1]) {
      let t = 3 + r() * 4;
      while (t < len - 5) {
        const a = along(s.pts, t), u = a.u, v = [-u[1] * side, u[0] * side];
        const ds0 = districtAt(a.p[0] + v[0] * (s.w / 2 + 8), a.p[1] + v[1] * (s.w / 2 + 8));
        if (!ds0) { t += 6; continue; }
        const vv = pickR(r, PROF[ds0.id].v), sz = SIZE[vv];
        const w = sz[0] + r() * (sz[1] - sz[0]), d = sz[2] + r() * (sz[3] - sz[2]);
        const f = [-v[0], -v[1]], rot = Math.abs(f[0]) > Math.abs(f[1]) ? (f[0] > 0 ? 1 : 3) : (f[1] < 0 ? 0 : 2);
        const off = s.w / 2 + 2.8 + d / 2 + (vv === 'model' ? 6 : 0);
        const cx = a.p[0] + u[0] * (w / 2) + v[0] * off, cz = a.p[1] + u[1] * (w / 2) + v[1] * off;
        const ex = rot % 2 ? d / 2 : w / 2, ez = rot % 2 ? w / 2 : d / 2;
        const rc = [cx - ex, cz - ez, cx + ex, cz + ez];
        const ds = ok(rc);
        if (!ds) { t += 2.5; continue; }
        const key = s.name + side;
        let paint = pickR(r, PAINT); if (paint === lastPaint.get(key)) paint = PAINT[(PAINT.indexOf(paint) + 3) % PAINT.length];
        lastPaint.set(key, paint);
        placed.push(rc);
        cityHouse(B, D, cx, cz, rot, w, d, vv, paint, r);
        const FR = [[0, -1], [1, 0], [0, 1], [-1, 0]][rot], ext = rot % 2 ? ex : ez;
        spawns.push([cx + FR[0] * (ext + 2.4), 0.2, cz + FR[1] * (ext + 2.4)]);
        t += w + 3.5 + r() * 6;
      }
    }
  }
  // ---- filler: the solid blocks behind the street fronts (and courtyards between them)
  for (const ds of PLAN.districts) {
    const fl = PROF[ds.id].fill;
    if (!fl) continue;
    const [x0, z0, x1, z1] = ds.rect;
    for (let x = x0 + 4; x < x1 - 8; x += 11) for (let z = z0 + 4; z < z1 - 8; z += 11) {
      if (r() > fl.p) continue;
      const w = 8 + r() * 6, d = 8 + r() * 6, cx = x + w / 2 + r() * 2, cz = z + d / 2 + r() * 2;
      const rc = [cx - w / 2, cz - d / 2, cx + w / 2, cz + d / 2];
      if (!ok(rc)) continue;
      placed.push(rc);
      const h = fl.h[0] + Math.pow(r(), 1.6) * (fl.h[1] - fl.h[0]);
      block(B, D, cx, cz, w, d, h, pickR(r, fl.mats), r);
    }
  }
  // ---- street furniture: lights, bins, hydrants, vending machines, parked cars along the kerbs
  for (const s of roads) {
    if (s.path) continue;
    const len = plen(s.pts);
    for (let t = 6; t < len - 4; t += 13 + r() * 6) {
      const a = along(s.pts, t), side = r() < 0.5 ? -1 : 1, v = [-a.u[1] * side, a.u[0] * side];
      const px = a.p[0] + v[0] * (s.w / 2 + 1.4), pz = a.p[1] + v[1] * (s.w / 2 + 1.4);
      if (reserved.some((q) => px > q[0] && px < q[2] && pz > q[1] && pz < q[3]) || placed.some((q) => px > q[0] - 0.8 && px < q[2] + 0.8 && pz > q[1] - 0.8 && pz < q[3] + 0.8)) continue;
      if (Math.max(Math.abs(px), Math.abs(pz)) > H - 4) continue;
      const k = r();
      if (k < 0.35) streetlight(L0, px, pz, 1);
      else if (k < 0.5) { L0.B(px, 0.8, pz, 1.1, 1.6, 0.8, pickR(r, ['barrel', 'barrelr'])); }
      else if (k < 0.62) vending(B, px, pz, r);
      else if (k < 0.82 && !s.av) { const cpx = a.p[0] + v[0] * (s.w / 2 - 1.3), cpz = a.p[1] + v[1] * (s.w / 2 - 1.3); car(L0, cpx, cpz, Math.abs(a.u[0]) > Math.abs(a.u[1]) ? 0 : 1, pickR(r, ['carred', 'carblue', 'carwhite', 'carblack', 'cargreen', 'caryellow'])); }
      else L0.B(px, 0.45, pz, 0.5, 0.9, 0.5, 'hazard');
    }
  }
  // buses parked at the kerb of the avenues (the Blender bus)
  for (const [x, z, rr] of [[7, -122, 1], [-7, 64, 3], [7, 152, 1], [62, -7, 0], [-128, 7, 2], [150, 7, 2]]) prop(L0, 'bus', x, z, rr);
  // overhead cables and signs across the narrow streets (cover from the sky, not from bullets)
  for (const s of PLAN.streets) {
    if (s.path || s.w > 8) continue;
    const len = plen(s.pts);
    for (let t = 8; t < len - 6; t += 9 + rv() * 8) {
      const a = along(s.pts, t), yaw = Math.atan2(a.u[0], a.u[1]) /* across the street */, y = 6 + rv() * 5;
      D.obb(a.p[0], y, a.p[1], 0.08, 0.08, s.w + 6, yaw, 'metal');
      if (rv() < 0.45) D.obb(a.p[0], y - 0.9, a.p[1], 0.15, 1.4, 2.4, yaw, pickR(rv, ['neonpink', 'neoncyan', 'neonyellow', 'neongreen']));
      if (rv() < 0.3) D.obb(a.p[0], y - 0.4, a.p[1], 0.05, 0.6, s.w * 0.8, yaw, pickR(rv, ['cloth', 'leopard', 'camo'])); // washing on the line
    }
  }
  // ---- the outer ring, then the megacity out in the haze
  outerRing(B, D, r, rv);
  skylineHaze(D, rv);
  horizon(D, -G, -G, G, G, 2200, 'dirt');

  const bounds = [-G + 1, -G + 1, G - 1, G - 1];
  const sp = spawns.filter((p) => Math.max(Math.abs(p[0]), Math.abs(p[2])) < H - 6);
  for (let i = sp.length - 1; i > 0; i--) { const j = (r() * (i + 1)) | 0; [sp[i], sp[j]] = [sp[j], sp[i]]; }
  let graph = null;
  const map = {
    name: 'Jankburg', size: 'huge', royaleOnly: true, boxes: B.boxes, deco: D.boxes, killY: -40, bounds, floorY: -60,
    sky: { top: 0x2a0f5a, mid: 0xff7ab8, bot: 0x1a0626, fog: 0xc98ac8 }, fogNear: 110, fogFar: 460, chunk: 48, // (chunks: only what's in view and inside the haze is drawn)
    spawns: sp.slice(0, 48), plan: PLAN, lootHints,
    get graph() { return graph || (graph = buildNav(B.boxes, { x0: -G, z0: -G, n: 2 * G, cell: 1.25, levels: [0], band: 0.5, keep: (x, z) => Math.max(Math.abs(x), Math.abs(z)) < G - 2 }), graph.maxExpand = 40000, graph); }, // the outer ring too: bots outside find the gates and breaches. (a search gives up after 40k nodes)
  };
  unstick(map.boxes, map.spawns);
  return map;
}

// ------------------------------------------------------------ landmarks + district pieces
const VEND = []; // vending machines (Neon Market's modifier: shoot one, get a gadget)
// a glossy ball out of stacked boxes (radius R, centre y cy): three boxes a layer, rounder than it has any right to be
function ball(L, x, cy, z, R, mat, step = 0.8) {
  for (let y = cy - R + step / 2; y < cy + R; y += step) {
    const rr = Math.sqrt(Math.max(0, R * R - (y - cy) * (y - cy)));
    if (rr < 0.3) continue;
    L.B(x, y, z, rr * 1.7, step, rr * 1.7, mat); L.B(x, y, z, rr * 2, step, rr * 1.1, mat); L.B(x, y, z, rr * 1.1, step, rr * 2, mat);
  }
}
function fountain(B, D) {
  const L = B.local(0, 0, 0), Ld = D.local(0, 0, 0);
  for (const s of [-1, 1]) { L(-11, 0, s * 10.2 - 0.6, 11, 0.9, s * 10.2 + 0.6, 'marble'); L(s * 10.2 - 0.6, 0, -9.6, s * 10.2 + 0.6, 0.9, 9.6, 'marble'); }
  for (let k = 0; k < 4; k++) D.obb(0, 0.45, 0, 23, 0.9, 1.2, Math.PI / 4 + k * Math.PI / 2, 'marble'); // (octagon corners, for the look)
  Ld(-9.6, 0, -9.6, 9.6, 0.55, 9.6, 'poolwater');
  L(-2.6, 0, -2.6, 2.6, 2.4, 2.6, 'marble');
  ball(L, 0, 8.4, 0, 6, 'toyyellow');
  for (const s of [-1, 1]) Ld(-3.4, 6, s * 5.9 - 0.15, 3.4, 11, s * 5.9 + 0.15, 'toyface', { fit: 1 });
  for (const s of [-1, 1]) for (let i = 0; i < 6; i++) { const t = i / 5; D.obb(0, 7.2 - t * t * 6.5, s * (6.2 + t * 4), 0.35, 0.6, 1.2, 0, 'neoncyan'); } // it spits
  for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4 + Math.PI / 8, x = Math.cos(a) * 15, z = Math.sin(a) * 15; if (Math.abs(x) < 11 && Math.abs(z) < 11) continue; L.B(x, 0.45, z, Math.abs(Math.cos(a)) > 0.7 ? 0.8 : 3, 0.9, Math.abs(Math.cos(a)) > 0.7 ? 3 : 0.8, 'wood'); }
}
function plaza(B, D, rv) {
  const L = B.local(0, 0, 0);
  const ads = ['adbig1', 'adcity1', 'adcity3', 'adfun'];
  [[-24, -26, 'x'], [24, 26, 'x'], [-26, 24, 'z'], [26, -24, 'z']].forEach(([x, z, a], i) => adBoard(B, x, z, 0, a, ads[i], 12, 5));
  for (const [x, z] of [[-20, -16], [20, 16], [16, -20], [-16, 20]]) { // metro kiosks (the trains stopped running in '09)
    L.B(x, 1.6, z, 4, 3.2, 3, 'glassblock'); L.B(x, 3.35, z, 4.6, 0.3, 3.6, 'roofteal');
    D.add(x - 1, 0.05, z - 1.52, x + 1, 2.4, z - 1.48, 'ceildark'); D.add(x - 1.6, 2.6, z - 1.56, x + 1.6, 3.1, z - 1.52, 'neoncyan');
  }
  for (const [x, z] of [[-28, -14], [28, 14], [-14, 28], [14, -28], [-28, 14], [28, -14]]) { L.B(x, 0.5, z, 2.4, 1, 2.4, 'concrete'); lollipop(L, x, z, 3 + rv() * 1.5, rv); }
}
function cathedral(B, D, cx, cz) {
  // the Cathedral of Shareholder Value: a corporate megachurch facing the plaza. stock-ticker stained glass, pews,
  // an organ made of server racks, a bell tower you grapple up for the best sniper spot in town
  const L = B.local(cx, cz, 2), Ld = D.local(cx, cz, 2), w = 24, d = 36, hw = 12, hd = 18, h = 14, t = 0.6;
  L(-hw, 0, -hd, hw, 0.15, hd, 'marble');
  const tall = (len) => { const o = []; for (let a = -len / 2 + 4; a < len / 2 - 3; a += 6) o.push({ a: a - 1, b: a + 1, y0: 3, y1: 10.5 }); return o; };
  wall(L, 'x', -hd, -hw, hw, 0, h, t, 'stone', [{ a: -3, b: 3, y0: 0, y1: 6.5 }, { a: -2, b: 2, y0: 8.5, y1: 12 }]);
  wall(L, 'x', hd, -hw, hw, 0, h, t, 'stone', [{ a: 7, b: 9, y0: 0, y1: 2.6 }]);
  wall(L, 'z', -hw, -hd, hd, 0, h, t, 'stone', [...tall(d), { a: -14, b: -12, y0: 0, y1: 2.6 }]);
  wall(L, 'z', hw, -hd, hd, 0, h, t, 'stone', tall(d));
  L(-hw - 0.3, h, -hd - 0.3, hw + 0.3, h + 0.6, hd + 0.3, 'roofg'); // flat roof: no cover on the way to the tower
  // stained glass that is just the stock ticker, and a ticker strip round the nave
  for (const s of [-1, 1]) for (let a = -hd + 4, i = 0; a < hd - 3; a += 6, i++) Ld(s * (hw + 0.05) - 0.05, 3, a - 1, s * (hw + 0.05) + 0.05, 10.5, a + 1, ['adcity2', 'adcity4', 'adoffice', 'adcity5'][i % 4], { fit: 1 });
  Ld(-2, 8.5, -hd - 0.05, 2, 12, -hd + 0.05, 'adcity1', { fit: 1 });
  for (const s of [-1, 1]) for (let a = -hd + 1; a < hd - 1; a += 3) Ld(s * (hw - t / 2 - 0.06), 11.3, a, s * (hw - t / 2 - 0.02), 11.9, a + 2.6, a % 6 ? 'neongreen' : 'neonred');
  for (let z = -12; z <= 8; z += 2.4) for (const s of [-1, 1]) { L(s * 2, 0.15, z, s * 10, 0.6, z + 0.5, 'wood'); L(s * 2, 0.6, z + 0.4, s * 10, 1.25, z + 0.55, 'wood'); } // pews
  L(-3, 0.15, 11, 3, 1.35, 13, 'gold'); Ld(-2.5, 5, hd - 0.4, 2.5, 10, hd - 0.3, 'flagcorp', { fit: 1 }); // altar + the logo
  for (let i = 0; i < 7; i++) { L(-9 + i * 3, 0.15, hd - 2.6, -7.4 + i * 3, 6, hd - 0.4, 'shelfstock'); Ld(-8.6 + i * 3, 6, hd - 1.8, -7.8 + i * 3, 9 + (i % 3) * 1.5, hd - 1.2, 'neoncyan'); } // the server-rack organ
  for (let i = 0; i < 4; i++) L(-6 + i * 0.2, 0, -hd - 1.4 - i * 1.2, 6 - i * 0.2, 0.15 + (3 - i) * 0.35, -hd - 0.2 - i * 1.2, 'marble'); // front steps
  // the bell tower, front right: solid to the belfry, an open belfry on top
  const tx = hw - 4.5, tz = -hd + 4.5;
  L(tx - 4, 0, tz - 4, tx + 4, 34, tz + 4, 'stone');
  for (const ox of [-3.6, 3.6]) for (const oz of [-3.6, 3.6]) L.B(tx + ox, 37, tz + oz, 0.8, 6, 0.8, 'marble');
  L(tx - 4.4, 40, tz - 4.4, tx + 4.4, 40.6, tz + 4.4, 'roofg'); L(tx - 2.6, 40.6, tz - 2.6, tx + 2.6, 42, tz + 2.6, 'gold');
  Ld(tx - 1, 35.5, tz - 1, tx + 1, 38, tz + 1, 'gold'); // the bell (a gold bar)
}
function hq(B, D, x, z, r) {
  const Ld = D.local(x, z, 0), L = B.local(x, z, 0);
  Ld(-26, 0, -27, 26, 0.09, 27, 'marble');
  tower(B, x, z, 24, 24, 152, { base: 0, tiers: 4, facade: 'glass', roof: 'helipad', r });
  for (const s of [-1, 1]) Ld(s * 12.1 - 0.1, 30, -4, s * 12.1 + 0.1, 70, 4, 'flagcorp', { fit: 1 }); // the logo, 40 m tall
  Ld(-6, 6, 12.05, 6, 9, 12.25, 'neonpink');
  // a gold stock arrow that only goes up, and planters to hide behind
  for (let i = 0; i < 6; i++) L(14 + i * 1.6, 0, 16, 15.6 + i * 1.6, 1 + i * 1.1, 18.4, 'gold');
  for (const [px, pz] of [[-20, 20], [20, -20], [-20, -20], [-8, 20], [8, 20]]) { L.B(px, 0.55, pz, 3, 1.1, 3, 'marble'); lollipop(L, px, pz, 3.5, r); }
}
function marketHall(B, D, x, z, rv) {
  const L = B.local(x, z, 0), Ld = D.local(x, z, 0), S = 44, h = S / 2;
  shell(L, S, S, 1, 10, 'tenement', { floor: 'tile', roof: 'roofg', backDoor: true, sideDoor: [-2, 2], winSpacing: 6 });
  // the two-level gallery inside, stairs up at two corners
  const g = 4, y = 5;
  L(-h + 0.3, y, -h + 0.3, h - 0.3, y + 0.3, -h + g, 'grid'); L(-h + 0.3, y, h - g, h - 0.3, y + 0.3, h - 0.3, 'grid');
  L(-h + 0.3, y, -h + g, -h + g, y + 0.3, h - g, 'grid'); L(h - g, y, -h + g, h - 0.3, y + 0.3, h - g, 'grid');
  L(-h + g, y + 0.3, -h + g - 0.1, h - g, y + 1.3, -h + g, 'metal'); L(-h + g, y + 0.3, h - g, h - g, y + 1.3, h - g + 0.1, 'metal');
  L(-h + g - 0.1, y + 0.3, -h + g, -h + g, y + 1.3, -2, 'metal'); L(h - g, y + 0.3, 2, h - g + 0.1, y + 1.3, h - g, 'metal');
  stairs(L, -h + g + 0.2, -h + g + 2, -2, 1, 0.12, y + 0.3, 'wood', 0.55);
  stairs(L, h - g - 2, h - g - 0.2, 2, -1, 0.12, y + 0.3, 'wood', 0.55);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 3; j++) stall(L, -12 + i * 8, -10 + j * 10, j % 2 ? 2 : 0, rv);
  for (let i = 0; i < 6; i++) Ld(-h + 6 + i * 6.4, 8.5, -h + 6, -h + 7 + i * 6.4, 9.5, h - 6, ['neonpink', 'neoncyan', 'neonyellow'][i % 3]); // light strips
  Ld(-8, 10.6, -h - 0.4, 8, 13.4, -h - 0.15, 'neonnoodle', { fit: 1 });
  for (let i = 0; i < 4; i++) VEND.push([x - 18 + i * 12, z - h - 1.4]);
  for (const [vx, vz] of VEND.slice(-4)) vending(B, vx, vz, rv, true);
}
function stallSquare(B, cx, cz, rv) {
  const L = B.local(0, 0, 0);
  for (let x = cx - 15; x <= cx + 15; x += 7.5) for (let z = cz - 13; z <= cz + 13; z += 8.5) stall(L, x, z, ((x + z) | 0) % 2 ? 0 : 2, rv);
}
function vending(B, x, z, r, front) {
  const L = B.local(0, 0, 0);
  L.B(x, 1, z, 1.2, 2, 0.9, 'metal'); L.B(x, 1.25, z - 0.46, 0.9, 1.3, 0.05, pickR(r, ['neonpink', 'neoncyan', 'neonyellow', 'adfun']));
  if (!front) VEND.push([x, z]);
}
function numberWorks(B, D, cx, cz, rv) {
  const L = B.local(0, 0, 0), Ld = D.local(0, 0, 0);
  // the toy factory hall: sawtooth roof, a door on each side
  const Lh = B.local(-150, 106, 0);
  shell(Lh, 36, 22, 1, 9, 'brick', { floor: 'concrete', roof: 'roofg', backDoor: true, sideDoor: [-3, 3], winSpacing: 5 });
  for (let i = 0; i < 6; i++) { Lh(-18 + i * 6, 9.3, -11, -14 + i * 6, 11.5, 11, 'roofg'); D.local(-150, 106, 0)(-14.05 + i * 6, 9.3, -10.9, -13.95 + i * 6, 11.4, 10.9, 'glassblock'); }
  for (let i = 0; i < 5; i++) Lh(-15 + i * 6.5, 0.12, -2, -11 + i * 6.5, 1.1, 2, 'rubber'); // conveyor sections
  // three smokestacks you can see from anywhere
  for (const sz of [98, 116, 134]) {
    L(-110, 0, sz - 2.5, -105, 62, sz + 2.5, 'brick');
    for (const y of [20, 40, 58]) L(-110.4, y, sz - 2.9, -104.6, y + 1.4, sz + 2.9, 'hazard');
    L(-110.5, 62, sz - 3, -104.5, 63, sz + 3, 'rust');
  }
  // vats of something green, tubes between everything
  for (const vx of [-160, -146, -132]) { L(vx - 3.5, 0, 136, vx + 3.5, 7, 143, 'rust'); L(vx - 3.8, 7, 135.7, vx + 3.8, 7.4, 143.3, 'chrome'); Ld(vx - 3.2, 7.05, 136.3, vx + 3.2, 7.2, 142.7, 'neongreen'); }
  for (const z of [110, 126]) { L(-132, 7, z - 0.6, -110, 8.2, z + 0.6, 'chrome'); for (let x = -128; x < -110; x += 8) L(x - 0.3, 0, z - 0.3, x + 0.3, 7, z + 0.3, 'metal'); }
  L(-131.6, 7, 117, -130.4, 8.2, 134, 'chrome');
  // giant glossy number balls rolled out into the yard (the Blender ones, digits and all: a lucky 7, an unlucky 1 3)
  [[-120, 96, 7], [-124, 143, 1], [-118.5, 143, 3], [-170, 92, 0], [-140, 92, 9], [-172, 140, 4]].forEach(([x, z, v]) => prop(L, 'numball', x, z, (x | 0) & 3, { v, s: 4.4 }));
  prop(L, 'forklift', -132, 97, 1); prop(L, 'pallet_load', -128, 94, 0); prop(L, 'pallet_load', -126.6, 94, 0); prop(L, 'pallet', -127.3, 95.4, 1);
  // a fence round the yard, with gaps for the roads
  for (const [x0, z0, x1, z1] of [[-176, 88, -150, 88.3], [-140, 88, -100, 88.3], [-176, 149.7, -130, 150], [-120, 149.7, -100, 150], [-176, 88, -175.7, 112], [-176, 122, -175.7, 150]]) L(x0, 0, z0, x1, 2.4, z1, 'fence');
}
function slumTower(B, D, x, z, floors, r) {
  const L = B.local(x, z, (r() * 4) | 0), Ld = D.local(x, z, 0), w = 14;
  const fm = pickR(r, ['tenement', 'graffiti', 'brick']);
  shell(L, w, w, 2, F, fm, { floor: 'plywood', roof: 'roofg', backDoor: true, sideDoor: [-2, 0], winSpacing: 4, parapet: false });
  const top = upper(L, w, w, 2, floors, fm, 'roofg');
  for (let f = 1; f < floors; f++) if (r() < 0.6) L(-3, f * F + 0.15, -w / 2 - 1.3, 3, f * F + 0.35, -w / 2, 'grid'); // balconies
  L(-5, top, 1, 0, top + 2.6, 6, pickR(r, ['plywood', 'rust', 'cardboard'])); // somebody lives on the roof
  L(-5.2, top + 2.6, 0.8, 0.2, top + 2.8, 6.2, 'rust');
  L.B(4, top + 4, -4, 0.3, 8, 0.3, 'metal');
  Ld(w / 2 + 0.1, 4, -1, w / 2 + 0.35, top - 2, 1, pickR(r, ['neonpink', 'neoncyan', 'neonyellow'])); // a sign all the way up
  return top;
}
function liberalArch(B, D, x, z) {
  const L = B.local(x, z, 0), Ld = D.local(x, z, 0);
  for (const s of [-1, 1]) L.B(0, 3.5, s * 6, 0.6, 7, 0.6, 'white');
  L.B(0, 7.4, 0, 0.6, 0.8, 12.6, 'white');
  Ld(-0.35, 7.9, -5.5, 0.35, 10.4, 5.5, 'adhoa', { fit: 1 });
  Ld(-0.4, 7, -6, 0.4, 7.15, 6, 'neongreen');
}
// a solid city block: a box of facade with a roof you can stand on and the usual roof junk
function block(B, D, x, z, w, d, h, mat, r) {
  B.box(x, h / 2, z, w, h, d, mat);
  B.box(x, h + 0.2, z, w + 0.4, 0.4, d + 0.4, 'roofg');
  const L = B.local(x, z, 0, h + 0.4), Ld = D.local(x, z, 0);
  if (h > 30 && r() < 0.6) { B.box(x, h + 0.4 + 5, z, w * 0.6, 10, d * 0.6, mat); }
  else {
    if (r() < 0.6) for (let i = 0; i < 2; i++) L.B(-w / 4 + i * 2.4, 0.6, d / 4, 1.8, 1.2, 1.2, 'metal');
    if (r() < 0.25) L.B(w / 4, 4, -d / 4, 0.3, 8, 0.3, 'metal');
    if (r() < 0.2 && w > 10) { const ad = pickR(r, ['adcity1', 'adcity2', 'adcity3', 'adcity4', 'adcity5', 'adcity6', 'adfun', 'adware']); Ld(-w / 2 + 1, h + 1.5, -0.2, w / 2 - 1, h + 5.5, 0.2, ad, { fit: 1 }); L.B(0, 0.75, 0.5, 0.3, 1.5, 0.3, 'metal'); }
  }
  if (r() < 0.5) { const s = r() < 0.5 ? -1 : 1; Ld(-w / 2 + 1, 2.6, s * (d / 2 + 0.12) - 0.1, w / 2 - 1, 3.4, s * (d / 2 + 0.12) + 0.1, pickR(r, ['neonpink', 'neoncyan', 'neonyellow', 'neongreen', 'signopen'])); }
}
const FONT = {
  T: ['#####', '..#..', '..#..', '..#..', '..#..'], H: ['#...#', '#...#', '#####', '#...#', '#...#'], E: ['#####', '#....', '####.', '#....', '#####'],
  Y: ['#...#', '.#.#.', '..#..', '..#..', '..#..'], O: ['.###.', '#...#', '#...#', '#...#', '.###.'], U: ['#...#', '#...#', '#...#', '#...#', '.###.'],
  W: ['#...#', '#...#', '#.#.#', '##.##', '#...#'],
};
// a word in giant toy blocks, standing up along x at z (you can climb it, hide behind it, stand on the Y)
function word(B, text, x0, z, px, mat) {
  const L = B.local(0, 0, 0);
  [...text].forEach((ch, i) => {
    const g = FONT[ch], lx = x0 + i * 6 * px;
    g.forEach((row, ry) => {
      const y0 = (4 - ry) * px;
      for (let c = 0; c < 5;) { if (row[c] !== '#') { c++; continue; } let e = c; while (e < 5 && row[e] === '#') e++; L(lx + c * px, y0, z, lx + e * px, y0 + px, z + px, mat); c = e; }
    });
  });
  return [x0, z, x0 + text.length * 6 * px, z + px];
}
function pronounPark(B, D, rv) {
  const L = B.local(0, 0, 0), Ld = D.local(0, 0, 0), [x0, z0, x1, z1] = [96, 28, 178, 136];
  Ld(x0, 0, z0, x1, 0.04, z1, 'lawn');
  const po = PLAN.pond;
  for (let k = 0; k < 4; k++) D.obb(po.x, 0.035, po.z, po.r * 2 + 1.6, 0.07, po.r * 0.86 + 1.6, k * Math.PI / 4, 'stone');
  for (let k = 0; k < 4; k++) D.obb(po.x, 0.045, po.z, po.r * 2, 0.08, po.r * 0.86, k * Math.PI / 4, 'poolwater');
  const words = [word(B, 'THEY', 100, 42, 1.3, 'toypink'), word(B, 'YOU', 142, 40, 1.3, 'toyteal'), word(B, 'WE', 100, 122, 1.3, 'toyyellow')];
  const lm = PLAN.landmarks.find((l) => l.id === 'letters'); if (lm) { lm.x = 118; lm.z = 43; }
  // a bandstand on the lawn
  const bx = 158, bz = 86;
  L(bx - 5, 0, bz - 5, bx + 5, 0.8, bz + 5, 'wood'); L(bx - 1.5, 0, bz - 6.2, bx + 1.5, 0.4, bz - 5, 'wood');
  for (const [ox, oz] of [[-4.4, -4.4], [4.4, -4.4], [-4.4, 4.4], [4.4, 4.4]]) L.B(bx + ox, 2.8, bz + oz, 0.4, 4, 0.4, 'white');
  L(bx - 5.4, 4.8, bz - 5.4, bx + 5.4, 5.2, bz + 5.4, 'roofpink'); L(bx - 3.5, 5.2, bz - 3.5, bx + 3.5, 5.8, bz + 3.5, 'roofpink'); L(bx - 1.6, 5.8, bz - 1.6, bx + 1.6, 6.4, bz + 1.6, 'roofpink');
  const paths = PLAN.streets.filter((s) => s.path);
  const busy = (x, z, m) => paths.some((s) => segDist(x, z, s.pts) < m) || Math.hypot(x - po.x, z - po.z) < po.r + 4 || Math.hypot(x - bx, z - bz) < 9 || words.some((w) => x > w[0] - 3 && x < w[2] + 3 && z > w[1] - 3 && z < w[3] + 3);
  for (let x = x0 + 4; x < x1 - 3; x += 8) for (let z = z0 + 4; z < z1 - 3; z += 8) {
    const tx = x + (rv() - 0.5) * 4, tz = z + (rv() - 0.5) * 4;
    if (busy(tx, tz, 4) || rv() < 0.3) continue;
    if (rv() < 0.7) lollipop(L, tx, tz, 3 + rv() * 2.5, rv); else conifer(L, tx, tz, 6 + rv() * 3, rv);
  }
  for (const s of paths) for (let t = 6; t < plen(s.pts) - 4; t += 14) { const a = along(s.pts, t), v = [-a.u[1], a.u[0]], px = a.p[0] + v[0] * 3.2, pz = a.p[1] + v[1] * 3.2; if (!busy(px, pz, 2.2)) L.B(px, 0.45, pz, Math.abs(a.u[0]) > 0.7 ? 2.6 : 0.7, 0.9, Math.abs(a.u[0]) > 0.7 ? 0.7 : 2.6, 'wood'); }
  for (const [hx, hz, len, ax] of [[100, 70, 14, 'x'], [168, 112, 10, 'z'], [120, 128, 16, 'x']]) if (!busy(hx + (ax === 'x' ? len / 2 : 0), hz + (ax === 'z' ? len / 2 : 0), 2)) L(hx, 0, hz, ax === 'x' ? hx + len : hx + 1.2, 1.3, ax === 'x' ? hz + 1.2 : hz + len, 'hedge');
  // the quay: bollards, crates, a little crane
  for (let x = 64; x < 176; x += 9) L.B(x, 0.4, 146.6, 0.5, 0.8, 0.5, 'metal');
  for (const x of [72, 98, 152]) { L(x, 0, 143.5, x + 2.4, 2.4, 146, 'crate'); L(x + 0.4, 2.4, 143.8, x + 2, 3.8, 145.6, 'crate'); }
  prop(L, 'forklift', 88, 144.8, 0); prop(L, 'pallet_load', 92, 145, 0); prop(L, 'pallet_load', 93.4, 145, 0); prop(L, 'forklift', 140, 144.8, 2); prop(L, 'pallet_load', 135, 145, 1);
  L(118, 0, 143, 121, 9, 146, 'busyellow'); L(118, 9, 143.8, 121, 10, 156, 'busyellow'); L(119.2, 3, 154.6, 119.8, 9, 155.2, 'metal');
}
function cityWall(B, D, r) {
  const H = PLAN.wall.half, WH = PLAN.wall.h, t = PLAN.wall.t, CH = PLAN.wall.chamfer, cn = PLAN.canal;
  const L = B.local(0, 0, 0), Ld = D.local(0, 0, 0);
  // world box helper along a wall: a = along the wall, n = across it (from the wall centre line)
  const wb = (axis, fixed, a0, a1, n0, n1, y0, y1, mat, ex) => (axis === 'x' ? B.add(a0, y0, fixed + n0, a1, y1, fixed + n1, mat, ex) : B.add(fixed + n0, y0, a0, fixed + n1, y1, a1, mat, ex));
  const wd = (axis, fixed, a0, a1, n0, n1, y0, y1, mat, ex) => (axis === 'x' ? D.add(a0, y0, fixed + n0, a1, y1, fixed + n1, mat, ex) : D.add(fixed + n0, y0, a0, fixed + n1, y1, a1, mat, ex));
  for (const [axis, fixed] of [['x', -H], ['x', H], ['z', -H], ['z', H]]) {
    const out = Math.sign(fixed), inn = -out, on = (p) => (axis === 'x' ? p.z === fixed : p.x === fixed), alongOf = (p) => (axis === 'x' ? p.x : p.z);
    const ops = [];
    const gate = PLAN.gates.find(on), brs = PLAN.breaches.filter(on);
    if (gate) ops.push({ a: -12, b: 12, y0: 0, y1: WH + 2 }, { a: 15, b: 18, y0: 0, y1: 3 }, { a: -18, b: -15, y0: 0, y1: 3 });
    for (const b of brs) ops.push({ a: alongOf(b) - 6, b: alongOf(b) + 6, y0: 0, y1: WH + 2 });
    if (axis === 'z' && fixed === H) ops.push({ a: cn.z0, b: cn.z1, y0: -5, y1: 2.5 });
    wall(L, axis, fixed, -H + CH, H - CH, 0, WH, t, 'concrete', ops);
    const cut = (a) => ops.some((o) => a > o.a - 1 && a < o.b + 1 && o.y0 <= 0.5);
    // the firewall's neon strip, merlons on the outer edge, a walkway you can run along on top
    for (let a = -H + CH; a < H - CH; a += 6) {
      if (cut(a) || cut(a + 6)) continue;
      wd(axis, fixed, a, a + 6, out * (t / 2) - 0.05 * (out > 0 ? 0 : 1), out * (t / 2) + 0.05 * (out > 0 ? 1 : 0), WH - 2.2, WH - 1.6, 'neonpink');
      wd(axis, fixed, a, a + 6, inn * (t / 2) - 0.05 * (inn > 0 ? 0 : 1), inn * (t / 2) + 0.05 * (inn > 0 ? 1 : 0), WH - 2.2, WH - 1.6, 'neonpink');
      wb(axis, fixed, a + 2.3, a + 3.7, out > 0 ? t / 2 - 0.8 : -t / 2, out > 0 ? t / 2 : -t / 2 + 0.8, WH, WH + 1.2, 'concrete');
    }
    // towers every 60 m, a jump pad at the foot of each (inside) that throws you up onto it
    for (const a of [-120, -60, 60, 120]) {
      if (cut(a - 5) || cut(a + 5)) continue;
      wb(axis, fixed, a - 4.5, a + 4.5, -4.5, 4.5, 0, 22, 'concrete');
      wb(axis, fixed, a - 5, a + 5, -5, 5, 22, 22.4, 'roofg');
      for (const [p0, p1, q0, q1] of [[-5, 5, -5, -4.6], [-5, 5, 4.6, 5], [-5, -4.6, -4.6, 4.6], [4.6, 5, -4.6, 4.6]]) wb(axis, fixed, a + p0, a + p1, q0, q1, 22.4, 23.4, 'concrete');
      wd(axis, fixed, a - 4.6, a + 4.6, -4.6, 4.6, 19, 19.6, 'neonpink');
      const pv = axis === 'x' ? [0, 35, out * 5] : [out * 5, 35, 0];
      wb(axis, fixed, a - 1.25, a + 1.25, inn * 10.5 - 1.25, inn * 10.5 + 1.25, 0, 0.3, 'pad', { pad: pv });
    }
    if (gate) {
      // gatehouses with a side passage each, a sign bridge over the road, barriers, booths and cover both sides
      for (const s of [-1, 1]) {
        const A = (u, v) => [Math.min(s * u, s * v), Math.max(s * u, s * v)];
        wb(axis, fixed, ...A(12, 15), -4, 4, 0, 20, 'concrete'); wb(axis, fixed, ...A(15, 18), -4, 4, 3, 20, 'concrete'); wb(axis, fixed, ...A(18, 23), -4, 4, 0, 20, 'concrete');
        wd(axis, fixed, ...A(12, 23), -4.05, 4.05, 18, 18.6, 'neonyellow');
        wb(axis, fixed, ...A(1, 11), inn * 7 - 0.12, inn * 7 + 0.12, 1, 1.25, 'hazard'); wb(axis, fixed, ...A(11, 11.4), inn * 7 - 0.3, inn * 7 + 0.3, 0, 1.4, 'metal');
        wb(axis, fixed, ...A(8, 10.4), inn * 10 - 1.2, inn * 10 + 1.2, 0, 2.8, 'white'); wb(axis, fixed, ...A(7.8, 10.6), inn * 10 - 1.4, inn * 10 + 1.4, 2.8, 3.1, 'roofteal');
        for (const k of [2, 7]) { wb(axis, fixed, ...A(k, k + 3.2), out * 9 - 0.4, out * 9 + 0.4, 0, 1.1, 'jersey'); wb(axis, fixed, ...A(k + 2, k + 5.2), inn * 16 - 0.4, inn * 16 + 0.4, 0, 1.1, 'jersey'); }
      }
      wb(axis, fixed, -12, 12, -3, 3, 15, 17.5, 'concrete');
      wd(axis, fixed, -9, 9, out * 3 - (out > 0 ? 0 : 0.2), out * 3 + (out > 0 ? 0.2 : 0), 15.2, 17.3, 'adoffice', { fit: 1 });
      wd(axis, fixed, -9, 9, inn * 3 - (inn > 0 ? 0 : 0.2), inn * 3 + (inn > 0 ? 0.2 : 0), 15.2, 17.3, 'flagcorp', { fit: 1 });
    }
    // breaches: rubble everywhere, and a pile beside the hole you can climb up onto the wall
    for (const b of brs) {
      const c = alongOf(b);
      for (let i = 0; i < 8; i++) { const a = c - 7 + r() * 14, n = (r() - 0.5) * 16, s = 0.8 + r() * 2; wb(axis, fixed, a - s, a + s, n - s, n + s, 0, s * (0.6 + r() * 0.8), pickR(r, ['concrete', 'rust', 'concrete'])); }
      for (let i = 0; i < 10; i++) wb(axis, fixed, c + 6.5 + i * 1.6, c + 8.1 + i * 1.6, inn > 0 ? t / 2 : -t / 2 - 4, inn > 0 ? t / 2 + 4 : -t / 2, 0, (i + 1) * 1.4, 'concrete');
    }
  }
  // chamfered corners: a stepped diagonal, a fat tower in the middle of each
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const n = 13;
    for (let i = 0; i < n; i++) { const k = (i + 0.5) / n, x = sx * (H - CH + CH * k), z = sz * (H - CH * k); B.box(x, WH / 2, z, 4.6, WH, 4.6, 'concrete'); }
    const tx = sx * (H - CH / 2), tz = sz * (H - CH / 2);
    B.box(tx, 12, tz, 11, 24, 11, 'concrete'); B.box(tx, 24.2, tz, 11.6, 0.4, 11.6, 'roofg'); D.add(tx - 5.6, 21, tz - 5.6, tx + 5.6, 21.6, tz + 5.6, 'neonpink');
  }
}
function outerRing(B, D, r, rv) {
  const H = PLAN.wall.half, G = PLAN.ground, L = B.local(0, 0, 0), Ld = D.local(0, 0, 0);
  // the sprawl (west): shacks of cardboard, plywood and rust, lanes between them, a few you can get into
  for (let x = -G + 6; x < -H - 6; x += 8) for (let z = -150; z < 150; z += 8) {
    const sx = x + (r() - 0.5) * 3, sz = z + (r() - 0.5) * 3;
    if (Math.abs(sz) < 15 || r() < 0.28) continue;
    const w = 3.5 + r() * 3, d = 3.5 + r() * 3, h = 2.6 + r() * 1.2, m = pickR(r, ['cardboard', 'plywood', 'rust', 'graffiti', 'containerb', 'plywood']);
    if (w > 5 && d > 5 && r() < 0.4) { shell(B.local(sx, sz, (r() * 4) | 0), w, d, 1, 2.9, m, { floor: 'dirt', roof: 'rust', parapet: false }); continue; }
    L.B(sx, h / 2, sz, w, h, d, m); D.obb(sx, h + 0.1, sz, w + 1.2, 0.15, d + 1, (r() - 0.5) * 0.3, pickR(r, ['rust', 'cloth', 'plywood']));
    if (r() < 0.15) { L.B(sx + w / 2 + 0.8, 0.5, sz, 0.8, 1, 0.8, 'barrelr'); Ld(sx + w / 2 + 0.5, 1, sz - 0.3, sx + w / 2 + 1.1, 1.3, sz + 0.3, 'neonred'); }
  }
  // the plastic orchard (south): rows of trees no tree farm would sell
  for (let x = -148; x < 150; x += 9) for (let z = H + 10; z < G - 6; z += 10) {
    if (Math.abs(x) < 16) continue;
    const tx = x + (rv() - 0.5) * 1.5, tz = z + (rv() - 0.5) * 1.5, h = 2.4 + rv() * 1.2, c = pickR(rv, ['toypink', 'toyteal', 'toyyellow', 'toygreen', 'leaves']);
    L.B(tx, h / 2, tz, 0.5, h, 0.5, 'wood'); L.B(tx, h + 0.8, tz, 3.4, 1.6, 3.4, c); L.B(tx, h + 1.9, tz, 2.2, 0.8, 2.2, c);
  }
  // farms (north): crop rows, hay, a barn and a silo
  for (let x = -170; x < 170; x += 5) if (Math.abs(x) > 16) Ld(x, 0, -G + 8, x + 2.2, 0.35, -H - 12, x % 10 ? 'leaves2' : 'dirt');
  for (let i = 0; i < 14; i++) { const x = (r() < 0.5 ? -1 : 1) * (22 + r() * 140), z = -H - 14 - r() * 50; L.B(x, 0.8, z, 1.6, 1.6, 1.6, 'gold'); }
  shell(B.local(-70, -222, 0), 16, 12, 1, 6, 'brick', { floor: 'wood', roof: 'roofteal', backDoor: true, winSpacing: 6 });
  L(-58, 0, -228, -52, 26, -222, 'concrete'); L(-58.4, 26, -228.4, -51.6, 27, -221.6, 'roofteal');
  // the crash site (north-east, outside): the last delivery blimp, nose down in the dirt, still smiling
  const cx = 214, cz = -208;
  for (let i = 0; i < 14; i++) { const t = i / 13, rr = 9 * Math.sin(Math.PI * (0.08 + t * 0.84)), x = cx - 22 + t * 44; L.B(x, Math.max(0.5, rr - 1.5), cz, 3.4, Math.max(1, rr * 2 - 3), rr * 1.8, i % 4 === 2 ? 'toyyellow' : 'pink'); }
  Ld(cx - 23.5, 3, cz - 3, cx - 23.3, 8, cz + 3, 'toyface', { fit: 1 });
  L(cx + 2, 0, cz + 9, cx + 12, 3, cz + 14, 'toyteal'); L(cx + 4, 3, cz + 9.5, cx + 10, 3.3, cz + 13.5, 'burnt');
  for (let i = 0; i < 10; i++) { const x = cx - 30 + r() * 60, z = cz - 25 + r() * 50, s = 0.5 + r() * 1.5; L.B(x, s / 2, z, s * 2, s, s, pickR(r, ['burnt', 'rust', 'metal'])); }
  for (let i = 0; i < 6; i++) { const x = cx - 26 + r() * 52, z = cz - 22 + r() * 44; Ld(x - 3, 0, z - 3, x + 3, 0.06, z + 3, 'burnt'); }
  // the highway stubs (east and west): a deck over the avenue, up a ramp, that just... stops
  for (const s of [-1, 1]) {
    const x0 = s * (H + 18), x1 = s * (G - 6), y = 8.8;
    for (let i = 0; i < 16; i++) { const a = s * (H + 2 + i), b = s * (H + 3 + i); B.add(Math.min(a, b), 0, -9, Math.max(a, b), (i + 1) * 0.55, 9, 'asphalt2'); }
    B.add(Math.min(x0, x1), y - 0.8, -9, Math.max(x0, x1), y, 9, 'asphalt2');
    B.add(Math.min(x0, x1), y, -9.4, Math.max(x0, x1), y + 1, -9, 'jersey'); B.add(Math.min(x0, x1), y, 9, Math.max(x0, x1), y + 1, 9.4, 'jersey');
    for (let x = x0; s * x < s * x1; x += s * 12) for (const z of [-6, 6]) B.add(x - 0.8, 0, z - 0.8, x + 0.8, y - 0.8, z + 0.8, 'concrete');
    for (let i = 0; i < 6; i++) D.add(x1 - 0.1, y - 0.8 + i * 0.1, -8 + i * 3, x1 + s * (0.8 + r() * 2), y - 0.7 + i * 0.1, -7.8 + i * 3, 'rust'); // rebar
    D.add(Math.min(x1 + s * 60, x1 + s * 400), y - 0.8, -9, Math.max(x1 + s * 60, x1 + s * 400), y, 9, 'asphalt2'); // the rest of it, way out there
  }
  // riverside reeds where the canal leaves town
  for (let i = 0; i < 30; i++) { const x = H + 8 + r() * (G - H - 10), z = PLAN.canal.z1 + 2 + r() * 20; L.B(x, 0.7, z, 0.4, 1.4, 0.4, 'leaves2'); }
}
// the rest of the megacity, out in the haze: towers to the horizon, the JankCorp megatower in the north
function skylineHaze(D, rv) {
  const mats = ['office', 'glass', 'tenement', 'office', 'concrete', 'magenta'];
  for (let i = 0; i < 170; i++) {
    const a = rv() * Math.PI * 2, d = 300 + Math.pow(rv(), 0.8) * 260, x = Math.cos(a) * d, z = Math.sin(a) * d;
    const w = 20 + rv() * 40, dd = 20 + rv() * 40, h = 30 + Math.pow(rv(), 1.5) * (d < 600 ? 160 : 260), yaw = (rv() - 0.5) * 0.8;
    D.obb(x, h / 2 - 4, z, w, h + 4, dd, yaw, pickR(rv, mats));
    D.obb(x, h + 0.3, z, w * 0.8, 0.6, dd * 0.8, yaw, 'roofg');
    if (rv() < 0.4) D.obb(x, h * (0.3 + rv() * 0.5), z, w + 0.4, 1.2, dd + 0.4, yaw, pickR(rv, ['neonpink', 'neoncyan', 'neonyellow']));
    if (rv() < 0.12) D.obb(x, h + 12, z, w * 0.9, 18, 1, yaw, pickR(rv, ['adbig1', 'adcity1', 'adcity2', 'adcity6', 'adfun']), { fit: 1 });
  }
  D.add(-40, -4, -900, 40, 420, -840, 'glass'); D.add(-44, 420, -904, 44, 430, -836, 'neonpink'); D.add(-20, 430, -880, 20, 470, -860, 'flagcorp', { fit: 1 });
}

export const JANKBURG = jankburg();
JANKBURG.vending = VEND.slice();
MAPS.jankburg = JANKBURG;
if (!MAP_ORDER.includes('jankburg')) MAP_ORDER.push('jankburg');
