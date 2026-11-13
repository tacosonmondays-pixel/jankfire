// The look-only (deco) boxes a Blender model stands in for (tagged { av: id } in map.deco), in the same frame as
// dump.mjs writes the solid ones (one placement at the origin: map coordinates). For models that also redraw a map's
// neon, canopies, grilles... usage: node tools/arch/dump_deco.mjs <map> <id> [out.json]
import fs from 'fs';
import { MAPS } from '../../shared/map.js';
const [mapId, id, out] = process.argv.slice(2);
const m = MAPS[mapId]; if (!m) throw new Error('no map ' + mapId);
const r3 = (v) => Math.round(v * 1000) / 1000;
const boxes = (m.deco || []).filter((b) => b.av === id).map((b) => ({ min: b.min.map(r3), max: b.max.map(r3), mat: b.mat }));
const json = JSON.stringify({ map: mapId, id, boxes });
if (out) fs.writeFileSync(out, json); else console.log(json);
console.error(`${id} on ${mapId}: ${boxes.length} deco boxes`);
