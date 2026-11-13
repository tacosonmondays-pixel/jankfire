// JANKFIRE map -> Roblox. Loads a map from shared/map.js (its real builder, so the numbers never drift), and writes:
//   roblox/build/<Map>.model.json  the map as Parts (Rojo's JSON model format; rojo build turns it into the place)
//   roblox/build/<map>.parts.json  a flat list of every Part (for the tests and the top-down picture)
//   roblox/assets/<map>/placements.json  every Blender model on the map: which file, where, how big
// Scale: 1 m = 3 studs (S below). A JANKFIRE player is 1.8 m tall = 5.4 studs, about a Roblox R15 character.
// Axes are the same in both (y up, right-handed), so a point is just (x, y, z) * 3. No offset: the roofs stay at y 0
// and Rooftop's street is 486 studs down, so the place lowers Workspace.FallenPartsDestroyHeight to -1500.
// usage: node tools/roblox/convert.mjs [mapId=rooftop] [offsetX,offsetY,offsetZ (studs)]
// an offset moves the whole map in the place (the Range sits 20000 studs east of Rooftop, in the same place); the
// parts.json list and the placements stay where shared/map.js has them (the tests compare those)
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { MAPS } from '../../shared/map.js';
import { rbxMat } from './rbxmat.mjs';
import { readGlb, bounds, meta, mul, trs, apply, ident, invert } from './glb.mjs';

export const S = 3; // studs per metre
const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.join(HERE, '..', '..');
const MODELS = path.join(ROOT, 'public', 'models');
const r3 = (x) => Math.round(x * 1000) / 1000;
const v3 = (a) => a.map((x) => r3(x * S));

// ---------------------------------------------------------------- which boxes go where
// near = the playable roofs and everything round them; the rest of the deco is the city (no shadows, no queries)
function isCity(b) {
  const cx = (b.min[0] + b.max[0]) / 2, cz = (b.min[2] + b.max[2]) / 2;
  return b.max[1] < -25 || Math.abs(cx) > 75 || Math.abs(cz) > 75;
}

// one box -> one Part record (studs). kind: solid | deco | city | pad
function partOf(b, kind) {
  const R = rbxMat(b.mat), size = [0, 1, 2].map((i) => b.max[i] - b.min[i]), c = [0, 1, 2].map((i) => (b.min[i] + b.max[i]) / 2);
  const yaw = b.rot || 0, cs = Math.cos(yaw), sn = Math.sin(yaw);
  const attrs = { Mat: { String: b.mat } };
  if (b.pv) attrs.PropId = { String: b.pv };
  if (b.av) { attrs.ArchId = { String: b.av }; attrs.ArchIndex = { Float64: b.ai ?? 0 }; }
  if (b.pad) attrs.Pad = { Vector3: v3(b.pad) }; // the launch velocity, studs/s
  if (b.fit) attrs.Picture = { String: b.mat }; // a picture (sign, ad): a colour for now, a decal once uploaded
  return {
    name: b.mat, kind, mat: b.mat, material: R.material, color: R.color, transparency: R.transparency,
    pos: v3(c), size: v3(size), yaw: r3(yaw), rot: [[r3(cs), 0, r3(sn)], [0, 1, 0], [r3(-sn), 0, r3(cs)]], attrs,
  };
}

// Roblox caps a Part at 2048 studs a side: longer ones (the city's avenues) become equal pieces along their own axes
const MAXP = 2000;
function split(p) {
  const n = p.size.map((x) => Math.max(1, Math.ceil(x / MAXP)));
  if (n.every((k) => k === 1)) return [p];
  const out = [];
  for (let i = 0; i < n[0]; i++) for (let j = 0; j < n[1]; j++) for (let k = 0; k < n[2]; k++) {
    const sz = p.size.map((x, a) => x / n[a]), off = [i, j, k].map((t, a) => (t + 0.5) * sz[a] - p.size[a] / 2);
    const w = [0, 1, 2].map((r) => p.rot[r][0] * off[0] + p.rot[r][1] * off[1] + p.rot[r][2] * off[2]); // (rows: local offset -> world)
    out.push({ ...p, pos: p.pos.map((x, a) => r3(x + w[a])), size: sz.map(r3) });
  }
  return out;
}

// ---------------------------------------------------------------- the Blender models' placements (propfield.js / archfield.js)
const glbCache = new Map();
function glbOf(file) {
  if (!glbCache.has(file)) glbCache.set(file, fs.existsSync(file) ? readGlb(file) : null);
  return glbCache.get(file);
}
const hash = (x, z) => { const s = Math.sin(x * 12.9898 + z * 78.233) * 43758.5453; return s - Math.floor(s); };
const PARKED = ['p_car_sedan', 'p_car_hatch'], TAXI = ['p_car_taxi', 'p_car_sedan', 'p_car_hatch'];
const has = (mid) => fs.existsSync(path.join(MODELS, mid + '.glb'));
function modelFor(p) { // = propfield.js modelFor
  if (!p.a) return has('p_' + p.id) ? { mid: 'p_' + p.id, turn: 0 } : null;
  if (p.id === 'car') {
    const list = p.t === 'caryellow' ? TAXI : PARKED, k = p.t === 'caryellow' ? 0 : (hash(p.a[0], p.a[2]) * list.length) | 0;
    for (let i = 0; i < list.length; i++) { const m = list[(k + i) % list.length]; if (has(m)) return { mid: m, turn: Math.PI / 2 }; }
    return has('p_car') ? { mid: 'p_car', turn: 0 } : null;
  }
  return has('p_' + p.id) ? { mid: 'p_' + p.id, turn: 0 } : null;
}
let fixed = null;
function fixedExtent(id) { // = propfield.js fixedExtent, over every map
  if (!fixed) {
    fixed = new Map(); const seen = new Map();
    for (const m of Object.values(MAPS)) for (const l of [m.boxes && m.boxes.props, m.deco && m.deco.props]) for (const p of l || []) {
      if (!p.a) continue;
      const e = seen.get(p.id);
      if (!e) seen.set(p.id, { lo: p.lo, hi: p.hi, same: true });
      else if (e.same && [0, 1, 2].some((i) => Math.abs(e.lo[i] - p.lo[i]) > 0.02 || Math.abs(e.hi[i] - p.hi[i]) > 0.02)) e.same = false;
    }
    for (const [id, e] of seen) if (e.same) fixed.set(id, { lo: e.lo, hi: e.hi });
  }
  return fixed.get(id) || null;
}
const ry = (a) => trs([0, 0, 0], [0, Math.sin(a / 2), 0, Math.cos(a / 2)]);
const T = (x, y, z) => trs([x, y, z]);
const Sc = (x, y, z) => trs(undefined, undefined, [x, y, z]);
function boxApply(m, lo, hi) { // an axis-aligned box through a matrix -> its new axis-aligned bounds
  const a = [Infinity, Infinity, Infinity], b = [-Infinity, -Infinity, -Infinity];
  for (let c = 0; c < 8; c++) { const p = apply(m, [c & 1 ? hi[0] : lo[0], c & 2 ? hi[1] : lo[1], c & 4 ? hi[2] : lo[2]]); for (let k = 0; k < 3; k++) { a[k] = Math.min(a[k], p[k]); b[k] = Math.max(b[k], p[k]); } }
  return { lo: a, hi: b };
}

// file space -> world (metres): the same matrix the web game draws the model with (propfield.js placeMatrix + kindOf)
function propMatrix(p, mid, turn) {
  const j = glbOf(path.join(MODELS, mid + '.glb'));
  let rootInv = ident();
  if (p.v !== undefined && p.v !== null) {
    const names = [String(p.v), 'n' + p.v, 'v' + p.v];
    const n = (j.nodes || []).findIndex((x) => names.includes(x.name));
    if (n >= 0) { // the variant's own frame (its world matrix: walk the parents)
      const parent = new Map(); (j.nodes || []).forEach((x, i) => (x.children || []).forEach((c) => parent.set(c, i)));
      let w = ident(); for (let i = n; i != null; i = parent.get(i)) { const x = j.nodes[i]; w = mul(x.matrix || trs(x.translation, x.rotation, x.scale), w); }
      rootInv = invert(w);
    }
  }
  const base = mul(ry(turn), rootInv);
  const own = bounds(j, p.v ?? null), kb = boxApply(ry(turn), own.lo, own.hi); // the model's box (lod0, the variant, turned)
  let M;
  if (!p.a) { // round 1: position, quarter turns, uniform scale
    M = mul(T(...p.p), ry(-(p.r || 0) * Math.PI / 2));
    if (p.s) M = mul(M, Sc(p.s, p.s, p.s));
  } else {
    const mt = meta(j), mb = mt && Array.isArray(mt.box) && mt.box.length === 2 ? boxApply(ry(turn), mt.box[0], mt.box[1]) : null;
    const ref = mb || fixedExtent(p.id) || kb;
    const md = (i) => ref.hi[i] - ref.lo[i], ex = (i) => p.hi[i] - p.lo[i], sc = (i) => (md(i) > 1e-3 && ex(i) > 1e-3 ? ex(i) / md(i) : 1);
    if (p.f !== undefined) { const sh = (sc(0) + sc(2)) / 2; M = mul(mul(mul(T(p.a[0], p.a[1] + p.lo[1], p.a[2]), ry(p.y)), Sc(sh, sc(1), sh)), T(0, -ref.lo[1], 0)); }
    else M = mul(mul(mul(mul(T(...p.a), ry(p.y)), T(...p.lo)), Sc(sc(0), sc(1), sc(2))), T(-ref.lo[0], -ref.lo[1], -ref.lo[2]));
  }
  return { M: mul(M, base), file: bounds(j) };
}

// a file->world matrix -> a Roblox placement: the model's box as a CFrame + Size (studs), and K, how many studs one
// file metre becomes along each of the file's own axes (props are fitted per axis onto their boxes)
function placementOf(M, file) {
  const cols = [0, 1, 2].map((c) => [M[c * 4], M[c * 4 + 1], M[c * 4 + 2]]);
  const k = cols.map((c) => Math.hypot(...c)), Rc = cols.map((c, i) => c.map((x) => x / (k[i] || 1)));
  const fc = [0, 1, 2].map((i) => (file.lo[i] + file.hi[i]) / 2), fs_ = [0, 1, 2].map((i) => file.hi[i] - file.lo[i]);
  const centre = apply(M, fc);
  return {
    pos: v3(centre), rot: [0, 1, 2].map((r) => [0, 1, 2].map((c) => r3(Rc[c][r]))), // rows of the rotation (Roblox order)
    size: fs_.map((x, i) => r3(Math.max(0.05, x * k[i] * S))), K: k.map((x) => r3(x * S)), fileCenter: fc.map(r3), fileSize: fs_.map(r3),
  };
}

function propPlacements(def) {
  const out = [], skipped = new Map();
  for (const [layer, list] of [['solid', def.boxes.props], ['deco', def.deco.props]]) for (const p of list || []) {
    const mf = modelFor(p);
    if (!mf) { skipped.set(p.id, (skipped.get(p.id) || 0) + 1); continue; }
    const { M, file } = propMatrix(p, mf.mid, mf.turn);
    out.push({ kind: 'prop', id: p.id, model: mf.mid, layer, variant: p.v ?? null, tint: p.t || p.color || null, ...placementOf(M, file) });
  }
  return { out, skipped };
}
function archPlacements(def) {
  const out = [], nth = new Map();
  (def.boxes.arch || []).forEach((a, ai) => {
    const file = path.join(MODELS, 'arch', a.id + '.glb'), j = glbOf(file);
    if (!j) return;
    const vk = nth.get(a.id) || 0; nth.set(a.id, vk + 1);
    const M = mul(T(...a.p), ry(-(a.r || 0) * Math.PI / 2));
    out.push({ kind: 'arch', id: a.id, model: 'arch_' + a.id, archIndex: ai, variant: 'v' + (vk % 3), hide: a.hide || null, fence: a.fence ?? null, paint: a.paint || null, ...placementOf(M, bounds(j)) });
  });
  return out;
}

// ---------------------------------------------------------------- Rojo JSON model
const MATERIAL_ENUM = { Plastic: 256, SmoothPlastic: 272, Neon: 288, Wood: 512, WoodPlanks: 528, Marble: 784, Slate: 800, Concrete: 816, Granite: 832, Brick: 848, Pebble: 864, Cobblestone: 880, CorrodedMetal: 1040, DiamondPlate: 1056, Foil: 1072, Metal: 1088, Grass: 1280, Sand: 1296, Fabric: 1312, Ice: 1536, Glass: 1568, Asphalt: 1376, Pavement: 1440, LeafyGrass: 1284, Rubber: 1808, Carpet: 2065, CeramicTiles: 2066, ClayRoofTiles: 2067, Cardboard: 1824, Leather: 2068, Plaster: 2069 };
let OFF = [0, 0, 0]; // studs: where this map sits in the place
const off = (v) => v.map((x, i) => r3(x + OFF[i]));
function rojoPart(p) {
  const solid = p.kind === 'solid' || p.kind === 'pad';
  return {
    Name: p.name, ClassName: 'Part',
    Properties: {
      Anchored: true, CanCollide: solid, CanQuery: solid, CanTouch: p.kind === 'pad', CastShadow: p.kind !== 'city' && p.transparency < 0.5,
      Size: { Vector3: p.size.map((x) => Math.max(0.01, x)) }, CFrame: { CFrame: { position: off(p.pos), orientation: p.rot } },
      Color: { Color3: p.color }, Material: { Enum: MATERIAL_ENUM[p.material] ?? 272 }, Transparency: p.transparency,
      TopSurface: { Enum: 0 }, BottomSurface: { Enum: 0 }, Attributes: { Attributes: p.attrs },
    },
  };
}
const folder = (Name, Children) => ({ Name, ClassName: 'Folder', Children });
const PAINT = { carred: 0xc8202c, carblue: 0x2050b0, carwhite: 0xe8e8e8, carblack: 0x26262a, cargreen: 0x2a8a4a, caryellow: 0xe8c020, burnt: 0x2a2624, cloth: 0xc8302a }; // (propfield.js PAINT + TINT)
const tintColor = (t) => (PAINT[t] !== undefined ? [(PAINT[t] >> 16) & 255, (PAINT[t] >> 8) & 255, PAINT[t] & 255].map((x) => r3(x / 255)) : rbxMat(t).color);
function markerPart(m) { // an invisible box where a Blender model goes: MeshSwap (roblox/src/server) reads its attributes
  const a = { Model: { String: m.model }, K: { Vector3: m.K }, FileCenter: { Vector3: m.fileCenter }, FileSize: { Vector3: m.fileSize } };
  if (m.variant != null) a.Variant = { String: String(m.variant) };
  if (m.tint) { a.Tint = { String: m.tint }; a.TintColor = { Color3: tintColor(m.tint) }; }
  if (m.archIndex != null) a.ArchIndex = { Float64: m.archIndex };
  if (m.hide) a.Hide = { String: m.hide.join(',') };
  if (m.paint) a.Paint = { String: JSON.stringify(m.paint) };
  return {
    Name: `${m.kind}:${m.id}`, ClassName: 'Part',
    Properties: { Anchored: true, CanCollide: false, CanQuery: false, CanTouch: false, CastShadow: false, Transparency: 1, Size: { Vector3: m.size }, CFrame: { CFrame: { position: off(m.pos), orientation: m.rot } }, Attributes: { Attributes: a } },
  };
}

export function convert(mapId = 'rooftop', offset = [0, 0, 0]) {
  OFF = offset;
  const def = MAPS[mapId];
  if (!def) throw new Error('no map ' + mapId);
  const parts = [];
  for (const b of def.boxes) parts.push(...split(partOf(b, b.pad ? 'pad' : 'solid')));
  for (const b of def.deco) parts.push(...split(partOf(b, isCity(b) ? 'city' : 'deco')));
  const spawns = (def.spawns || []).map((p) => v3(p));
  const team = def.teamSpawns || {};
  const props = propPlacements(def), arch = archPlacements(def);
  const markers = [...arch, ...props.out];
  const k = (kind) => parts.filter((p) => p.kind === kind).map(rojoPart);
  const sky = def.sky || {}, hexc = (n) => [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((x) => r3(x / 255)), hex = (n) => [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((x) => r3(x / 255));
  const Name = def.name.replace(/[^A-Za-z0-9]/g, '');
  const model = {
    ClassName: 'Model',
    Properties: { Attributes: { Attributes: {
      MapId: { String: mapId }, KillY: { Float64: r3((def.killY ?? -45) * S + OFF[1]) }, StudsPerMetre: { Float64: S }, Offset: { Vector3: OFF },
      // where the play area is (studs, in the place) and its sky, so the game knows which map you're on and can light it
      Bounds: { Vector3: [r3((def.bounds?.[0] ?? -100) * S + OFF[0]), r3((def.bounds?.[2] ?? 100) * S + OFF[0]), 0] },
      BoundsZ: { Vector3: [r3((def.bounds?.[1] ?? -100) * S + OFF[2]), r3((def.bounds?.[3] ?? 100) * S + OFF[2]), 0] },
      FogColor: { Color3: hexc(sky.fog ?? 0x2a2050) }, SkyTop: { Color3: hexc(sky.top ?? 0x05051a) }, FogStart: { Float64: r3((def.fogNear ?? 90) * S) }, FogEnd: { Float64: r3((def.fogFar ?? 330) * S) },
    } } },
    Children: [
      folder('Solid', k('solid')), folder('Pads', k('pad')), folder('Deco', k('deco')), folder('City', k('city')),
      folder('Spawns', spawns.map((p, i) => ({ Name: 'Spawn' + (i + 1), ClassName: 'SpawnLocation', Properties: { Anchored: true, Neutral: true, CanCollide: false, CanQuery: false, CanTouch: true, Transparency: 1, Duration: 0, Size: { Vector3: [4, 0.2, 4] }, CFrame: { CFrame: { position: off([p[0], r3(p[1] - 0.1), p[2]]), orientation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]] } } } }))),
      folder('TeamSpawns', ['att', 'def'].flatMap((t) => (team[t] || []).map((p) => ({ Name: t, ClassName: 'Part', Properties: { Anchored: true, CanCollide: false, CanQuery: false, CanTouch: false, Transparency: 1, Size: { Vector3: [2, 0.2, 2] }, CFrame: { CFrame: { position: off(v3(p)), orientation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]] } } } })))),
      folder('ModelMarkers', markers.map(markerPart)),
      folder('Dummies', (def.dummies || []).map((d, i) => ({ Name: 'Dummy' + (i + 1), ClassName: 'Part', Properties: { Anchored: true, CanCollide: false, CanQuery: false, CanTouch: false, Transparency: 1, Size: { Vector3: [2, 0.2, 2] }, CFrame: { CFrame: { position: off(v3(d.p)), orientation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]] } }, Attributes: { Attributes: { Move: { Float64: r3((d.move || 0) * S) } } } } }))),
    ],
  };
  const lighting = { fog: hex(sky.fog ?? 0x2a2050), top: hex(sky.top ?? 0x05051a), mid: hex(sky.mid ?? 0x4a2a7a), fogStart: r3((def.fogNear ?? 90) * S), fogEnd: r3((def.fogFar ?? 330) * S) };
  return { def, Name, parts, spawns, markers, props, model, lighting };
}

// ---------------------------------------------------------------- cli
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mapId = process.argv[2] || 'rooftop';
  const r = convert(mapId, process.argv[3] ? process.argv[3].split(',').map(Number) : [0, 0, 0]);
  const build = path.join(ROOT, 'roblox', 'build'), assets = path.join(ROOT, 'roblox', 'assets', mapId);
  fs.mkdirSync(build, { recursive: true }); fs.mkdirSync(assets, { recursive: true });
  fs.writeFileSync(path.join(build, r.Name + '.model.json'), JSON.stringify(r.model));
  fs.writeFileSync(path.join(build, mapId + '.parts.json'), JSON.stringify({ map: mapId, S, lighting: r.lighting, spawns: r.spawns, parts: r.parts.map(({ attrs, rot, ...p }) => p) }));
  const files = [...new Set(r.markers.map((m) => m.model))].sort();
  const pl = r.markers.map(({ kind, id, model, pos, rot, size, K, variant, tint }) => JSON.stringify({ kind, id, model, pos, rot, size, K, variant, tint }));
  fs.writeFileSync(path.join(assets, 'placements.json'), `{"map":"${mapId}","studsPerMetre":${S},"files":${JSON.stringify(files)},"placements":[\n${pl.join(',\n')}\n]}\n`); // (one placement a line)
  const count = (kind) => r.parts.filter((p) => p.kind === kind).length;
  console.log(`${r.Name}: ${r.parts.length} parts (solid ${count('solid')}, pads ${count('pad')}, deco ${count('deco')}, city ${count('city')}), ${r.spawns.length} spawns, ${r.markers.length} model placements (${files.length} files)`);
  if (r.props.skipped.size) console.log('props with no Blender file (boxes only):', Object.fromEntries(r.props.skipped));
  const unknown = [...new Set(r.parts.filter((p) => !rbxMat(p.mat).known).map((p) => p.mat))];
  if (unknown.length) console.log('materials with no colour (pink):', unknown.join(', '));
}
