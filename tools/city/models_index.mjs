// Rewrites public/models/story/index.json from the .glb files in that folder (the city's props.js reads it once, so
// a prop with no model never 404s). Run after exporting story models: node tools/city/models_index.mjs
import fs from 'node:fs';
const dir = new URL('../../public/models/story/', import.meta.url);
const ids = fs.readdirSync(dir).filter((f) => f.endsWith('.glb')).map((f) => f.slice(0, -4)).sort();
fs.writeFileSync(new URL('index.json', dir), JSON.stringify(ids) + '\n');
console.log(ids.length, 'story models');
