// Like dump.mjs, plus the render-only (deco) boxes tagged with the same building, each marked deco: 1. For buildings
// whose dressing (lamps, signs) is deco: the Warehouse halls. One placement, in its own frame (quarter turns undone).
// usage: node tools/arch/dumpdeco.mjs <map> <id> [out.json]
import fs from 'fs';
import { MAPS } from '../../shared/map.js';
const [mapId, id, out] = process.argv.slice(2);
const m = MAPS[mapId]; if (!m) throw new Error('no map ' + mapId);
const places = m.boxes.arch.map((a, i) => ({ ...a, ai: i })).filter((a) => a.id === id); if (places.length !== 1) throw new Error(places.length + ' placements of ' + id);
const p = places[0], inv = (x, z, r) => [[x, z], [z, -x], [-x, -z], [-z, x]][r & 3], r3 = (v) => Math.round(v * 1000) / 1000;
const loc = (b, deco) => {
  const [ax, az] = inv(b.min[0] - p.p[0], b.min[2] - p.p[2], p.r), [bx, bz] = inv(b.max[0] - p.p[0], b.max[2] - p.p[2], p.r);
  return { min: [r3(Math.min(ax, bx)), r3(b.min[1] - p.p[1]), r3(Math.min(az, bz))], max: [r3(Math.max(ax, bx)), r3(b.max[1] - p.p[1]), r3(Math.max(az, bz))], mat: b.mat, ...(deco ? { deco: 1 } : {}) };
};
const boxes = [...m.boxes.filter((b) => b.av === id).map((b) => loc(b, 0)), ...(m.deco || []).filter((b) => b.av === id).map((b) => loc(b, 1))];
console.error(`${id} on ${mapId}: ${boxes.filter((b) => !b.deco).length} boxes, ${boxes.filter((b) => b.deco).length} deco`);
const json = JSON.stringify({ map: mapId, id, boxes, places: [p] });
if (out) fs.writeFileSync(out, json); else console.log(json);
