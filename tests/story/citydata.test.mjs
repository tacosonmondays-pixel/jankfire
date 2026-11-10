// node tests/story/citydata.test.mjs : the city data the sim reads without building the city (WORLD lane): the road
// net / parking (shared/city/slice_gta.js) and every mark (marks_slice.js) match the generators, the shops and the
// garage are there with what the systems lane needs, and every road piece is drivable ground
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { marksNear, allMarks } from '../../shared/city/marks.js';
import { roadsNear } from '../../shared/city/roads.js';
import GTA from '../../shared/city/slice_gta.js';

// 1. not stale (the tool rebuilds it all in memory and compares)
execFileSync(process.execPath, [new URL('../../tools/city/gta_index.mjs', import.meta.url).pathname, '--check'], { stdio: 'pipe' });
// 2. shops: every kind, each with a counter spot, a name and a facing; keepers where there's a counter
const shops = allMarks('slice').filter((m) => m.id === 'shop');
for (const k of ['guns', 'meat_mechanic', 'tooth_stall', 'vending', 'car_dealer', 'outfits']) assert.ok(shops.some((s) => s.shop === k), 'no ' + k + ' shop');
for (const s of shops) { assert.ok(s.sid && s.name && Array.isArray(s.p) && s.p.length === 3 && Number.isFinite(s.face), JSON.stringify(s)); if (s.shop !== 'vending') assert.ok(Array.isArray(s.keeper), s.sid + ' has no keeper spot'); }
assert.equal(new Set(shops.map((s) => s.sid)).size, shops.length, 'shop ids are unique');
// 3. the safehouse garage, parking, the dealer's stock
assert.ok(allMarks('slice').some((m) => m.id === 'garage' && m.home === 'bottom:lostfound'), 'no garage at the Lost & Found');
assert.ok(GTA.park.length > 100, 'kerbside parking: ' + GTA.park.length);
assert.ok(allMarks('slice').filter((m) => m.id === 'park' && m.sale).length >= 8, 'the dealer has stock');
// 4. lookups: near the Lost & Found there's a garage and a meat mechanic (Bev); the Gut grid has roads
assert.ok(marksNear('slice', -210, 190, 30, 'garage').length === 1);
assert.ok(marksNear('slice', -207, 186, 5, (m) => m.id === 'shop' && m.shop === 'meat_mechanic').length === 1);
assert.ok(roadsNear(-44, -150, 20).length > 0 && roadsNear(-44, -150, 20, 'walk').length > 0);
// 5. roads: pieces have ids, widths and ground heights in range
for (const r of GTA.roads) { assert.ok(r.pts.length >= 2 && r.w > 2 && (r.dir === 1 || r.dir === 2), r.id); for (const p of r.pts) assert.ok(p[1] > -1 && p[1] < 41, r.id + ' y ' + p[1]); }
console.log(`city data ok: ${shops.length} shops, ${GTA.roads.length} road pieces, ${GTA.walks.length} pavements, ${GTA.park.length} kerb spots, ${allMarks('slice').length} marks`);
