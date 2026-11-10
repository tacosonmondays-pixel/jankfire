// Dump a Blender building's boxes (tagged { av: id } in shared/map.js) in its own local frame, for tools/blender/arch.
// usage: node tools/arch/dump.mjs <map> <id> [out.json]. checks every placement of id on the map has the same boxes
// (the paint may differ: mats are written as the first placement's, plus the placement list)
import fs from 'fs';
import { MAPS } from '../../shared/map.js';
const [mapId, id, out] = process.argv.slice(2);
const m = MAPS[mapId]; if (!m) throw new Error('no map ' + mapId);
const places = m.boxes.arch.map((a, i) => ({ ...a, ai: i })).filter((a) => a.id === id); if (!places.length) throw new Error('no ' + id + ' on ' + mapId);
const tagged = m.boxes.filter((b) => b.av === id);
// world -> local: undo the quarter turn of builder local(): T(x, z) = [[x, z], [-z, x], [-x, -z], [z, -x]][rot]
const inv = (x, z, r) => [[x, z], [z, -x], [-x, -z], [-z, x]][r & 3];
const r3 = (v) => Math.round(v * 1000) / 1000;
const inside = (b, p) => b.ai === p.ai;
const sets = places.map((p) => tagged.filter((b) => inside(b, p)).map((b) => {
  const [ax, az] = inv(b.min[0] - p.p[0], b.min[2] - p.p[2], p.r), [bx, bz] = inv(b.max[0] - p.p[0], b.max[2] - p.p[2], p.r);
  return { min: [r3(Math.min(ax, bx)), r3(b.min[1] - p.p[1]), r3(Math.min(az, bz))], max: [r3(Math.max(ax, bx)), r3(b.max[1] - p.p[1]), r3(Math.max(az, bz))], mat: b.mat };
}).sort((a, b) => JSON.stringify(a.min.concat(a.max)) < JSON.stringify(b.min.concat(b.max)) ? -1 : 1));
const key = (s) => s.map((b) => b.min.concat(b.max).join(',')).join(';');
let maxSet = 0;
sets.forEach((s, i) => { if (s.length > sets[maxSet].length) maxSet = i; });
sets.forEach((s, i) => { const k = new Set(s.map((b) => b.min.concat(b.max).join(','))); const miss = sets[maxSet].filter((b) => !k.has(b.min.concat(b.max).join(','))); console.error(`placement ${i} at ${places[i].p} r${places[i].r}: ${s.length} boxes${miss.length ? `, ${miss.length} fewer than the fullest (${miss.map((b) => b.mat).join(' ')})` : ''}`); });
const json = JSON.stringify({ map: mapId, id, boxes: sets[maxSet], places }, null, 0);
if (out) fs.writeFileSync(out, json); else console.log(json);
