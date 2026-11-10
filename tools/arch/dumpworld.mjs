// Dump every box (collision and look-only deco) a map tags { av: id }, in world coordinates, for a one-per-map Blender
// model (rocks: tools/blender/arch/make_rocks.py). usage: node tools/arch/dumpworld.mjs <map> <id> [out.json]
import fs from 'fs';
import { MAPS } from '../../shared/map.js';
const [mapId, id, out] = process.argv.slice(2);
const m = MAPS[mapId]; if (!m) throw new Error('no map ' + mapId);
const r3 = (v) => Math.round(v * 1000) / 1000;
const pick = (list, solid) => (list || []).filter((b) => b.av === id).map((b) => ({ min: b.min.map(r3), max: b.max.map(r3), mat: b.mat, solid }));
const boxes = [...pick(m.boxes, 1), ...pick(m.deco, 0)];
if (!boxes.length) throw new Error('no ' + id + ' boxes on ' + mapId);
const json = JSON.stringify({ map: mapId, id, boxes, places: [{ id, p: [0, 0, 0], r: 0 }] });
if (out) fs.writeFileSync(out, json); else console.log(json);
console.error(mapId, id, boxes.length, 'boxes,', boxes.filter((b) => b.solid).length, 'solid');
