// JANKFIRE map materials -> Roblox: a Material, a colour (the web game's own, from matcolors.json) and how see-through.
// first match wins. the colours come from the renderer itself (matcolors.cjs), so they match what players see
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const COLORS = JSON.parse(fs.readFileSync(path.join(HERE, 'matcolors.json'), 'utf8'));

const RULES = [
  [/^neon|^lamp$|^light$|glow|^tail$|^led|^tvstatic$/, 'Neon'],
  [/water/, 'Glass'],
  [/glass|^window$/, 'Glass'],
  [/^grid$|diamond|tread/, 'DiamondPlate'],
  [/rust|corrod/, 'CorrodedMetal'],
  [/metal|steel|chrome|rail|^gold$|silver|iron|pipe/, 'Metal'],
  [/^crate$|plywood|pallet|plank/, 'WoodPlanks'],
  [/wood|bark|log/, 'Wood'],
  [/brick|tenement/, 'Brick'],
  [/asphalt|road|crosswalk|tar/, 'Asphalt'],
  [/pave|sidewalk|curb/, 'Pavement'],
  [/concrete|office|roofg|cement|jersey/, 'Concrete'],
  [/carpet/, 'Carpet'],
  [/cloth|towel|fabric|tent|curtain|cushion/, 'Fabric'],
  [/tile/, 'CeramicTiles'],
  [/roofpink|rooftile|shingle/, 'ClayRoofTiles'],
  [/lawn|grass|hedge/, 'Grass'],
  [/leaves|blossom|bush|leaf/, 'LeafyGrass'],
  [/^stone$|rock|cliff/, 'Slate'],
  [/sand/, 'Sand'],
  [/tire|rubber/, 'Rubber'],
  [/pottery|plaster|adobe|stucco/, 'Plaster'],
  [/marble/, 'Marble'],
  [/cardboard/, 'Cardboard'],
  [/leather/, 'Leather'],
];

const cache = new Map();
export function rbxMat(mat) {
  if (cache.has(mat)) return cache.get(mat);
  const c = COLORS[mat];
  let material = 'SmoothPlastic';
  for (const [re, m] of RULES) if (re.test(mat)) { material = m; break; }
  let color = c ? c.c : [1, 0, 0.86]; // (an unknown material: the game's own missing-texture pink)
  let transparency = 0;
  if (c && c.op < 1) transparency = +(1 - c.op).toFixed(2);
  if (/water/.test(mat)) transparency = Math.max(transparency, 0.35);
  else if (material === 'Glass') transparency = Math.max(transparency, /block/.test(mat) ? 0.45 : 0.3);
  if (material === 'Neon') { // roblox neon glows by itself: keep the hue, a little under full so it doesn't blow out
    const m = Math.max(...color, 0.001); color = color.map((x) => Math.min(1, (x / m) * 0.92));
  }
  const out = { material, color: color.map((x) => +Math.min(1, Math.max(0, x)).toFixed(3)), transparency, known: !!c };
  cache.set(mat, out);
  return out;
}
