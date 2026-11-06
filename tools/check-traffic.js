// Traffic lane check: every lane on every map clear of boxes (shared/traffic.js does that when it builds) and actually
// on a road (a surface right under the wheels the whole way), plus what scenery was cleared off the lanes.
// node tools/check-traffic.js   (exit code 1 if anything is wrong)
import { MAPS } from '../shared/map.js';
const before = new Map(Object.entries(MAPS).map(([k, m]) => [k, new Set(m.deco)]));
const { TRAFFIC, trafficNet, trafficLog, poseAt, boxObb, obbOverlap } = await import('../shared/traffic.js');
let bad = 0;
for (const line of trafficLog()) { console.log('  ' + line); if (/dropped|failed/.test(line)) bad++; }
for (const id of Object.keys(TRAFFIC)) {
  const net = trafficNet(id), map = MAPS[id];
  if (!net || !net.edges.length) { console.log(`${id}: NO LANES`); bad++; continue; }
  const all = [...map.boxes, ...map.deco];
  let pts = 0, off = 0, first = null;
  for (const e of net.edges) for (let s = 0; s <= e.len; s += 2) {
    const p = poseAt(e, s); pts++;
    const here = { x: p.x, z: p.z, ux: 1, uz: 0, hu: 0.01, hv: 0.01 };
    const on = all.some((b) => Math.abs(b.max[1] - p.y) < 0.05 && Math.abs(b.min[0] + b.max[0] - 2 * p.x) < 4000 && obbOverlap(boxObb(b), here));
    if (!on) { off++; first ||= [p.x, p.z].map(Math.round); }
  }
  const gone = {}; for (const b of before.get(id)) if (!map.deco.includes(b)) gone[b.mat] = (gone[b.mat] || 0) + 1;
  console.log(`${id}: ${net.edges.length} lanes, ${net.mix.map((m) => m[0]).join('/')}, ${off}/${pts} points off the road${first ? ' (first at ' + first + ')' : ''}; scenery cleared: ${JSON.stringify(gone)}`);
  if (off) bad++;
}
console.log(bad ? `FAIL (${bad})` : 'OK');
process.exit(bad ? 1 : 0);
