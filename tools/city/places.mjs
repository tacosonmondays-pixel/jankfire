// Every place id the world uses is a real location in the writer's data: node tools/city/places.mjs
// (PLACES in shared/city/slice.js, and every 'district:place' mark the slice's chunks emit). exit 1 if not.
import { PLACES } from '../../shared/city/slice.js';
import { LOCATIONS } from '../../shared/story/content/world.js';
import { buildChunk } from '../../shared/city/chunk.js';
const bad = Object.keys(PLACES).filter((k) => !Object.hasOwn(LOCATIONS, k));
const marks = new Set();
for (let cx = -5; cx < 5; cx++) for (let cz = -4; cz < 4; cz++) for (const m of buildChunk('slice', cx, cz).marks) if (m.id.includes(':')) marks.add(m.id);
const badMarks = [...marks].filter((k) => !Object.hasOwn(LOCATIONS, k));
console.log(JSON.stringify({ places: Object.keys(PLACES).length, marks: marks.size, unknown: [...bad, ...badMarks], missingInWorld: Object.keys(PLACES).filter((k) => !marks.has(k) && !['sims:suburb', 'commute:smiles_hideout', 'bottom:sunset_spot', 'bottom:dale_shed', 'bottom:rooftops', 'gut:campus'].includes(k)) }));
process.exit(bad.length || badMarks.length ? 1 : 0);
