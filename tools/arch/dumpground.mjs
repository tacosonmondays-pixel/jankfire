// Dump a map's shaped ground (boxes.terrain.at) on a grid, for Blender dressing that has to sit on it exactly
// (tools/blender/arch/make_kaboom.py). usage: node tools/arch/dumpground.mjs <map> x0 z0 x1 z1 step out.json
import fs from 'fs';
import { MAPS } from '../../shared/map.js';
const [mapId, x0, z0, x1, z1, step, out] = process.argv.slice(2);
const t = MAPS[mapId].boxes.terrain, X0 = +x0, Z0 = +z0, S = +step, nx = Math.round((+x1 - X0) / S) + 1, nz = Math.round((+z1 - Z0) / S) + 1, h = [];
for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) { const v = t.at(X0 + i * S, Z0 + j * S); h.push(v == null ? null : Math.round(v * 1000) / 1000); }
fs.writeFileSync(out, JSON.stringify({ map: mapId, x0: X0, z0: Z0, step: S, nx, nz, h }));
console.error(mapId, nx, 'x', nz, 'heights,', h.filter((v) => v == null).length, 'holes');
