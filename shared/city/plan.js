// OVERDUE city master plan: the chunk grid, the cities (the 1 km stress test, the slice), their districts and sky.
// Pure data + tiny helpers: shared by the server's chunk cache, the client's chunk worker and the streamer.
// x east, z south (north = -z, up the hill). a chunk is CHUNK x CHUNK metres, id 'city:cx:cz'.
export const CHUNK = 64;
export const chunkOf = (x) => Math.floor(x / CHUNK);
export const chunkId = (city, cx, cz) => city + ':' + cx + ':' + cz;
export function parseChunkId(id) {
  if (typeof id !== 'string' || id.length > 40) return null;
  const m = /^([a-z]{1,12}):(-?\d{1,3}):(-?\d{1,3})$/.exec(id);
  return m ? { city: m[1], cx: +m[2], cz: +m[3] } : null;
}

// the materials a chunk box can have. index = what packs into a Uint8 (the order is the wire format: add at the end)
// fam = which tile of the city atlas it draws with, rgb = its paint (multiplied over the tile), kind = the mesh it goes in
export const MATS = [
  ['ground', 'dirt', 0x9a8070], ['asphalt', 'asphalt', 0x55535a], ['concrete', 'concrete', 0xb4b0ac], ['plaster', 'plaster', 0xffffff],
  ['brick', 'brick', 0xc0705a], ['metal', 'metal', 0x9aa0a8], ['rust', 'metal', 0xc0683a], ['wood', 'wood', 0xb07a4a],
  ['tile', 'tile', 0xe8e0d0], ['glass', 'glass', 0x9fd8ff, 'glass'], ['glow', 'glow', 0xffe14d, 'glow'], ['flesh', 'flesh', 0xff6f91, 'flesh'],
  ['liver', 'flesh', 0x8a2a4a, 'flesh'], ['fat', 'flesh', 0xffd27a, 'flesh'], ['bone', 'bone', 0xf2e8d0], ['bile', 'flesh', 0xa6e22e, 'acid'],
  ['pink', 'plaster', 0xffb3c7], ['yellow', 'plaster', 0xffe58a], ['teal', 'plaster', 0x5fd3c6], ['mint', 'plaster', 0xb6f2c8],
  ['lilac', 'plaster', 0xd2b6ff], ['peach', 'plaster', 0xffc8a0], ['container', 'corrug', 0xffffff], ['tarp', 'fabric', 0xffffff],
  ['tiedye', 'tiedye', 0xffffff], ['rubble', 'concrete', 0x9a948e], ['ash', 'dirt', 0x77757a], ['road', 'asphalt', 0x4a484f],
  ['paint', 'paint', 0xffffff], ['teeth', 'bone', 0xfff4dc], ['rib', 'rib', 0xff8aa6, 'flesh'], ['bruise', 'flesh', 0x5b3a8f, 'flesh'],
  ['neon', 'glow', 0xff4fd8, 'glow'], ['cyanglow', 'glow', 0x4fd8ff, 'glow'], ['greenglow', 'glow', 0x39ff14, 'glow'], ['window', 'window', 0xffd88a, 'glow'],
  ['acid', 'flesh', 0xb8ff3a, 'acid'], ['sky', 'glow', 0x2a1840, 'glow'],
  ['gums', 'gumcobble', 0xffffff, 'flesh'], ['blood', 'flesh', 0x7a0a1c, 'flesh'],
];
export const MAT_ID = Object.fromEntries(MATS.map((m, i) => [m[0], i]));
export const FAMS = ['dirt', 'asphalt', 'concrete', 'plaster', 'brick', 'metal', 'wood', 'tile', 'corrug', 'fabric', 'tiedye', 'bone', 'paint', 'rib', 'window', 'flesh', 'glass', 'glow', 'gumcobble'];

// render presets (world.js JANK index): ring radii in metres. active = collision + props, near = full meshes,
// mid = one merged lod1 mesh per chunk, far = the heightfield impostor (one draw call for every far chunk).
// props = instanced props drawn out to here; propsHi = the Blender model inside this, the code box model past it
export const RINGS = [
  { name: 'Potato', active: 96, near: 128, mid: 160, far: 520, props: 96, propsHi: 0 },
  { name: 'Crusty', active: 96, near: 160, mid: 320, far: 640, props: 128, propsHi: 32 },
  { name: 'Mid', active: 96, near: 224, mid: 480, far: 900, props: 160, propsHi: 48 },
  { name: 'Too HD', active: 96, near: 224, mid: 640, far: 1100, props: 224, propsHi: 72 },
];

// a city = bounds in chunks + districts. districts are rects with their own generator, sky, fog and light.
// gen = module key in shared/city/chunk.js (GENS). sky colours like shared/map.js maps.
export const CITIES = {
  stress: {
    name: 'Stress Test', cx0: -8, cz0: -8, cx1: 8, cz1: 8, // 16 x 16 chunks = 1024 m square
    districts: [
      { id: 'blocks', name: 'Generic Blocks', rect: [-512, -512, 512, 512], gen: 'blocks',
        sky: { top: 0x3a5aa0, mid: 0xc8a0c8, bot: 0x6a5a70, fog: 0xc8a8c8 }, fogNear: 120, fogFar: 900, light: { hemi: [0xcfe8ff, 0x7a4a6a, 1.5], sun: [0xfff0dd, 1.8] } },
    ],
    spawn: [0, 2, 0],
  },
};
export function registerCity(id, def) { CITIES[id] = def; } // district files add their city (shared/city/slice.js)

export function districtAt(city, x, z) {
  const c = CITIES[city];
  if (!c) return null;
  for (const d of c.districts) if (x >= d.rect[0] && x < d.rect[2] && z >= d.rect[1] && z < d.rect[3]) return d;
  return c.districts[0];
}
// how much each district counts at (x, z): blends sky and fog over `band` metres across a border
export function districtWeights(city, x, z, band = 40) {
  const c = CITIES[city], out = [];
  if (!c) return out;
  let sum = 0;
  for (const d of c.districts) {
    const [x0, z0, x1, z1] = d.rect;
    const dx = Math.max(x0 - x, 0, x - x1), dz = Math.max(z0 - z, 0, z - z1), out2 = Math.hypot(dx, dz); // 0 inside
    const ins = Math.min(x - x0, x1 - x, z - z0, z1 - z); // > 0 inside: distance to the edge
    const w = out2 > 0 ? Math.max(0, 1 - out2 / (band / 2)) * 0.5 : 0.5 + Math.min(0.5, ins / band);
    if (w > 0) { out.push([d, w]); sum += w; }
  }
  if (!out.length) { // outside every district (flying past the edge): the nearest one
    let best = null, bd = Infinity;
    for (const d of c.districts) { const [x0, z0, x1, z1] = d.rect, dd = Math.hypot(Math.max(x0 - x, 0, x - x1), Math.max(z0 - z, 0, z - z1)); if (dd < bd) { bd = dd; best = d; } }
    return best ? [[best, 1]] : out;
  }
  for (const e of out) e[1] /= sum || 1;
  return out;
}
export const inCity = (city, cx, cz) => { const c = CITIES[city]; return !!c && cx >= c.cx0 && cx < c.cx1 && cz >= c.cz0 && cz < c.cz1; };

// tiny deterministic hashes: a chunk's seed, a lot's seed. same on every machine
export function hash2(a, b, s = 0) {
  let h = Math.imul(a | 0, 0x27d4eb2d) ^ Math.imul(b | 0, 0x165667b1) ^ Math.imul(s | 0, 0x2545f491);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b); h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}
export function rng(seed) { // mulberry32, like shared/map.js
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const strHash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; };
