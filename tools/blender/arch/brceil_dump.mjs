// Dump what the Backrooms' ceiling model (make_backrooms_ceil.py) is built over: the ceiling slabs, the flicker / dead
// light overlays (render-only), and the walls (for the AO and to keep missing tiles off them).
// usage: node tools/blender/arch/brceil_dump.mjs [out = tools/blender/arch/boxes/backrooms_ceil.json]
import fs from 'fs';
import { MAPS } from '../../../shared/map.js';
const m = MAPS.backrooms, r3 = (v) => Math.round(v * 1000) / 1000, bx = (b) => ({ min: b.min.map(r3), max: b.max.map(r3), mat: b.mat });
const out = {
  id: 'backrooms_ceil',
  boxes: m.boxes.filter((b) => b.av === 'backrooms_ceil').map(bx),
  lights: (m.deco || []).filter((b) => b.av === 'backrooms_ceil').map(bx),
  walls: m.boxes.filter((b) => b.mat === 'wallpaper').map(bx),
};
fs.writeFileSync(process.argv[2] || 'tools/blender/arch/boxes/backrooms_ceil.json', JSON.stringify(out));
console.log('ceilings', out.boxes.length, 'lights', out.lights.length, 'walls', out.walls.length, out.lights.map((b) => b.mat).join(' '));
