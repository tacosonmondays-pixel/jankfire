// Dump Skull Rock's skin (shared/skullshape.js skullGrid: the same shape shared/map.js stands up as boxes) for the
// Blender model (tools/blender/arch/make_skullrock.py). usage: node tools/arch/dumpskull.mjs out.json
import fs from 'fs';
import { SKULL, skullGrid } from '../../shared/skullshape.js';
const r3 = (v) => Math.round(v * 10000) / 10000;
fs.writeFileSync(process.argv[2], JSON.stringify({ ...SKULL, grid: skullGrid().map((row) => row.map((p) => p.map(r3))) }));
console.error('skull skin:', SKULL.NP + 1, 'rows of', SKULL.NT);
