// a web map's layout as data, for the Roblox arena kits (tools/roblox/<map>_models.py). Loads shared/map.js (its real
// builder, so the numbers never drift) and writes tools/roblox/arenas/<id>.json: every playable box (min, max, mat and
// its flags: pad = launch velocity, ter = shaped ground, ...), the render-only deco boxes, the Blender prop and building
// placements, the spawns and team spawns, the fall line, the sky and fog. Units are the web's metres; the kits scale
// by 3 (1 m = 3 studs, tools/roblox/convert.mjs).
// usage: node --max-old-space-size=2000 tools/roblox/webmap_dump.mjs crate platform bazaar
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { MAPS } from '../../shared/map.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, 'arenas');
fs.mkdirSync(OUT, { recursive: true });
const r = (v) => Math.round(v * 1000) / 1000;
const keep = (b) => {
  const o = { min: b.min.map(r), max: b.max.map(r), mat: b.mat };
  for (const k of Object.keys(b)) if (!['min', 'max', 'mat'].includes(k)) o[k] = b[k];
  return o;
};
for (const id of process.argv.slice(2)) {
  const m = MAPS[id];
  if (!m) { console.log('no map', id); continue; }
  const data = {
    id, name: m.name, size: m.size, killY: m.killY, bounds: m.bounds || null, ceiling: m.ceiling ?? null, floorY: m.floorY ?? null,
    seaY: m.seaY ?? null, sky: m.sky, light: m.light || null, fogNear: m.fogNear, fogFar: m.fogFar, sealed: !!m.sealed,
    spawns: m.spawns, teamSpawns: m.teamSpawns || null, pools: m.pools || null,
    boxes: m.boxes.map(keep), props: m.boxes.props || [], arch: m.boxes.arch || [],
    deco: (m.deco || []).map(keep), decoProps: (m.deco && m.deco.props) || [], decoArch: (m.deco && m.deco.arch) || [],
    // the shaped ground (shared/terrain.js): a 1 m grid of vertex heights (nx+1 by nz+1), the cells that have ground
    terrain: m.boxes.terrain ? { x0: m.boxes.terrain.x0, z0: m.boxes.terrain.z0, nx: m.boxes.terrain.nx, nz: m.boxes.terrain.nz,
      H: Array.from(m.boxes.terrain.H, (v) => r(v)), ok: Array.from(m.boxes.terrain.ok) } : null,
  };
  const file = path.join(OUT, id + '.json');
  fs.writeFileSync(file, JSON.stringify(data, null, 0).replace(/\},\{/g, '},\n{'));
  console.log('wrote', path.relative(process.cwd(), file), data.boxes.length, 'boxes', data.deco.length, 'deco');
}
