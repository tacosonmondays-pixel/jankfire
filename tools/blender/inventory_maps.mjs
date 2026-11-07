// What's still drawn as boxes on every map, by the builder that made it (docs/blender/INVENTORY.md's groups a, b, c):
// every box a map adds is stamped with the stack that added it (a copy of shared/ with one line added to propcap.js
// seen()), boxes a Blender model now draws are skipped, and the rest are grouped by kit function (wall(), train()...) or,
// for boxes a map function adds itself, by the "// ----" section of the map code they're in. Then each group is put in
// (a) props, (b) architecture, (c) terrain or (x) boxes on purpose: kit functions by the table below, sections by hand
// where named, else by their materials.
// usage: node tools/blender/inventory_maps.mjs [out.md=inventory_maps.md]   (also writes out.json: every group with its
// centre and size, for the screenshot sheets)
import fs from 'fs'; import os from 'os'; import path from 'path'; import url from 'url';
Error.stackTraceLimit = 80;
const root = path.resolve(path.dirname(url.fileURLToPath(import.meta.url)), '../..');
const OUT = process.argv[2] || 'inventory_maps.md';
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'jfinv-'));
fs.cpSync(path.join(root, 'shared'), path.join(tmp, 'shared'), { recursive: true });
const pc = path.join(tmp, 'shared/propcap.js'), src0 = fs.readFileSync(pc, 'utf8'), hook = 'export function seen(b, list) {\n';
if (!src0.includes(hook)) throw new Error('propcap.js seen() moved: update the stamp');
fs.writeFileSync(pc, src0.replace(hook, hook + '  b._st = new Error().stack; // (inventory: who added it)\n'));
const { MAPS } = await import(url.pathToFileURL(path.join(tmp, 'shared/map.js')).href);
await import(url.pathToFileURL(path.join(tmp, 'shared/royale.js')).href);
const models = new Set(fs.readdirSync(path.join(root, 'public/models')).filter((f) => f.endsWith('.glb')).map((f) => f.slice(0, -4)));
const SRC = {}; for (const f of ['map.js', 'jankburg.js', 'royale.js', 'props.js']) SRC[f] = fs.readFileSync(path.join(tmp, 'shared', f), 'utf8').split('\n');
const HELP = new Set(['seg', 'put', 'mer', 'pil', 'run', 'flush', 'wb', 'wd', 'side', 'post', 'beam', 'leg', 'bar', 'pane', 'tier', 'step', 'plank', 'brick', 'stud', 'rung', 'add2', 'box2']);
const INNER = /^(?:Object\.)?(?:seen|add|box|obb|L|B|local|propOf|fn)$|^L\.B$|^Array\.|^\(anon\)$|^Module|^ModuleJob|^async$/;
const frames = (st) => st.split('\n').slice(1).map((l) => { const m = /at (?:async )?(?:(\S+) \()?(?:file:\/\/)?(\/[^():]+):(\d+):(\d+)\)?/.exec(l); return m ? { fn: m[1] || '(anon)', file: path.basename(m[2]), line: +m[3] } : null; }).filter((f) => f && SRC[f.file]);
const section = (file, line) => { const L = SRC[file]; for (let i = line - 1; i >= 0; i--) { const s = L[i].trim(); if (/^\/\/ -{2,}/.test(s)) return { at: `${file}:${i + 1}`, text: s.replace(/^\/\/ -+\s*/, '').slice(0, 110) }; if (/^(export )?function /.test(s) && i < line - 1) return { at: `${file}:${i + 1}`, text: '(' + s.replace(/\s*\{.*$/, '').slice(0, 60) + ')' }; } return { at: file, text: '?' }; };
const defOf = (f) => { const L = SRC[f.file], re = new RegExp(`(?:function\\s+${f.fn.replace(/[$.]/g, '\\$&')}\\s*\\(|\\b${f.fn.replace(/[$.]/g, '\\$&')}\\s*=\\s*(?:\\(|function|async)|^\\s*${f.fn.replace(/[$.]/g, '\\$&')}\\s*\\()`); for (let i = f.line - 1; i >= 0; i--) if (re.test(L[i])) return `${f.file}:${i + 1}`; return f.file + ':?'; };
const out = {};
for (const [mid, m] of Object.entries(MAPS)) {
  const units = new Map();
  for (const [list, kind] of [[m.boxes, 'B'], [m.deco || [], 'D']]) for (const b of list) {
    if (!b._st) continue;
    if (b.pv && models.has('p_' + b.pv)) continue; // drawn by a Blender model
    let fr = frames(b._st).filter((f) => !INNER.test(f.fn));
    if (!fr.length) continue;
    // a little helper (seg, P, R, put...) is its parent's: wall(), rail(), the ship... (the unit is the thing it builds)
    while (fr.length > 1 && (fr[0].fn.length <= 3 || HELP.has(fr[0].fn))) fr = fr.slice(1);
    const outer = fr[fr.length - 1]; // the map function (the outermost shared frame)
    let key, u;
    if (fr.length === 1 || fr[0].fn === outer.fn) { const s = section(fr[0].file, fr[0].line); key = 'S ' + s.at; u = { kind: 'section', name: s.text, at: s.at }; }
    else { const s = section(outer.file, outer.line), d = defOf(fr[0]); key = 'K ' + fr[0].fn + '@' + d; u = { kind: 'kit', name: fr[0].fn, at: d, in: new Set() }; u.in.add(s.text); }
    const g = units.get(key) || { ...u, boxes: 0, deco: 0, mats: new Map(), sites: new Set(), in: u.in || null, min: [1e9, 1e9, 1e9], max: [-1e9, -1e9, -1e9] };
    if (u.in) for (const x of u.in) g.in.add(x);
    g.boxes++; if (kind === 'D') g.deco++; g.mats.set(b.mat, (g.mats.get(b.mat) || 0) + 1);
    if (fr[1]) g.sites.add(`${fr[1].line}:${fr[1].fn}`);
    for (let i = 0; i < 3; i++) { g.min[i] = Math.min(g.min[i], b.min[i]); g.max[i] = Math.max(g.max[i], b.max[i]); }
    units.set(key, g);
  }
  out[mid] = [...units.values()].map((g) => ({ kind: g.kind, name: g.name, at: g.at, in: g.in ? [...g.in].slice(0, 3) : undefined, boxes: g.boxes, deco: g.deco, copies: g.kind === 'kit' ? g.sites.size : undefined, size: g.max.map((v, i) => +(v - g.min[i]).toFixed(1)), c: g.max.map((v, i) => +((v + g.min[i]) / 2).toFixed(1)), mats: [...g.mats.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k, n]) => `${k}:${n}`).join(' ') })).sort((a, b) => b.boxes - a.boxes);
}
const A = 'a', Bg = 'b', C = 'c', X = 'x'; // x = deliberately boxes (livery pictures on the Blender trucks, gameplay skirts)
const KIT = {
  // ---- (b) architecture (the buildings lane)
  wall: [Bg, 'walls (with their door / window cuts)'], stairs: [Bg, 'switchback stairs'], slab: [Bg, 'floor slabs (stairwell holes)'], shell: [Bg, 'building shells: floors, walls, stairs inside'],
  tower: [Bg, 'office / tenement towers'], home: [Bg, 'the suburb houses'], upper: [Bg, 'upper facades of the city blocks (windows painted on)'], cityHouse: [Bg, 'the city houses (shanty blocks, TVs, AC, junk)'],
  outerRing: [Bg, 'the outer ring: shanty walls, scaffold, junk barricades'], cityWall: [Bg, 'the city wall with its neon strip'], skylineHaze: [Bg, 'the megacity out in the haze (render-only towers, the JankCorp megatower)'],
  cityBeyond: [Bg, 'the city beyond the map (render-only blocks, roofs, streets to the fog)'], streetLevel: [Bg, 'street level far below (render-only shopfronts, neon, windows)'],
  stairBridge: [Bg, 'stair bridges between the towers'], skyBridge: [Bg, 'sky bridges'], tubeBridge: [Bg, 'the glass tube bridge'], trussBridge: [Bg, 'truss bridge'], pipeBridge: [Bg, 'pipe bridge'],
  rail: [Bg, 'deck railings'], rigStair: [Bg, 'rig stairs (open grating flights)'], livingQuarters: [Bg, 'the living quarters block'], drillSide: [Bg, 'the drilling side: derrick, drill floor'], jacket: [Bg, 'the rig jacket legs and braces'],
  compressorHouse: [Bg, 'compressor house'], snackRun: [Bg, 'the boat landing, bulwarks and stair up'], facadeHouse: [Bg, 'facade houses'], dome: [Bg, 'domes (bazaar roofs, skyline crowns)'], souk: [Bg, 'souk arcades and shopfronts'],
  dressFacades: [Bg, 'facade dressing: shutters, window frames, balconies, sills'], penthouse: [Bg, 'the penthouse'], frontier: [Bg, 'the frontier-town facades (false fronts, porches)'], adobeHut: [Bg, 'adobe huts'], ruin: [Bg, 'a ruin'],
  watchtower: [Bg, 'watchtower'], stoneBridge: [Bg, 'stone bridge'], trestle: [Bg, 'the rail trestle over the canyon'], ropeBridge: [Bg, 'rope bridge'], lipFence: [Bg, 'canyon-lip fences'], woodFence: [Bg, 'wooden fences'],
  chainFence: [Bg, 'chain-link fences'], fence: [Bg, 'chain-link fence'], fort: [Bg, 'the old fort'], lighthouse: [Bg, 'the lighthouse'], cottage: [Bg, "the keeper's cottage"], baitShack: [Bg, 'the bait shack'], hut: [Bg, 'beach huts'],
  cathedral: [Bg, 'the cathedral'], slumTower: [Bg, 'the slum tower'], marketHall: [Bg, 'the market hall'], plaza: [Bg, 'the plaza building'], liberalArch: [Bg, 'the arch'], numberWorks: [Bg, 'the Number Works factory'],
  block: [Bg, 'solid city blocks (facade + roof junk)'], roofTop: [Bg, 'rooftop machine rooms and parapets'], flight: [Bg, 'stair flights'], ropeWalk: [Bg, 'rope walkways and piers'],
  // ---- (a) props (the props lane)
  train: [A, 'the train (engine, cars)'], wheels: [A, 'train wheels'], rails: [A, 'railway track'], waterTank: [A, 'water tanks on stilts'], windpump: [A, 'windpumps'], headframe: [A, 'mine headframe'],
  chopper: [A, 'helicopters (parked)'], wreck: [A, 'the shipwreck (the Soggy Biscuit)'], cannon: [A, 'cannons'], lounger: [A, 'sun loungers'], tikiBar: [A, 'the tiki bar'], bigTiki: [A, 'the big tiki head'], surfSchool: [A, 'surf school boards and rack'],
  mixerTruck: [A, 'cement mixer trucks'], bulldozer: [A, 'bulldozers'], roller: [A, 'road rollers'], crane: [A, 'tower crane'], pedCrane: [A, 'pedestal cranes'], xmasTree: [A, 'wellhead christmas trees'], separator: [A, 'separator vessels'],
  pipeRack: [A, 'pipe racks'], skyCola: [A, 'the giant cola can / sign rooftop'], skyNews: [A, 'the news rooftop (van, dish, lights)'], skyPutt: [A, 'the rooftop mini golf'], skyGarden: [A, 'the rooftop garden'], skyObs: [A, 'the observatory roof'],
  skyHeli: [A, 'the helipad heli'], skyGreen: [A, 'the rooftop greenhouse / pond'], skyBuild: [A, 'the rooftop building site'], adSign: [A, 'trail and warning signs'], stake: [A, 'property stakes'], tent: [A, 'tents'], bt: [A, 'rowboat / canoe'],
  brokenCar: [A, 'the broken-down car'], log: [A, 'fallen logs'], cube: [A, 'office cubicles'], rack: [A, 'warehouse racking'], hanging: [A, 'hanging rugs and lanterns on lines'], lampTower: [A, 'lamp towers'], siteBoard: [A, 'bomb site boards (A / B)'],
  adBoard: [A, 'ad boards'], billboard: [A, 'billboards (rooftop frames)'], hvac: [A, 'HVAC units'], planter: [A, 'planters'], pipeStack: [A, 'pipe stacks'], fountain: [A, 'the fountain'], ball: [A, 'the giant toy ball'], word: [A, 'the giant toy-block letters'],
  sign: [Bg, 'neon shop signs (shopfront: the buildings lane)'], awning: [Bg, 'shop awnings (shopfront: the buildings lane)'], stall: [A, 'market stall leftovers (rugs, goods)'], pronounPark: [A, 'the park: benches, playground, fountain'], cityDress: [A, 'neon crowns, facade ads, cables with hanging ads'],
  suburbOutside: [A, 'outside the suburb: power poles, junk, tyre piles'], farRig: [C, 'far oil rigs (render-only)'], skullRock: [C, 'Skull Rock'], gravelPile: [C, 'gravel piles'],
  // ---- (c) terrain
  dune: [C, 'dunes'], rocks: [C, 'rock formations'], boulders: [C, 'boulders'], boulder: [C, 'boulders'], sandbar: [C, 'sandbars'], isle: [C, 'islets (surf rings)'], reef: [C, 'reefs'], volcano: [C, 'the volcano (Mount Kaboom)'],
  horizon: [C, 'the horizon floor out past the map'], groundHoles: [C, 'ground slabs with holes (stairwells, canals)'], depotOutside: [C, 'the road and verge outside the depot'],
  // ---- deliberately boxes
  trailerBoxes: [X, 'livery pictures on the Blender trailers'], semiBoxes: [X, 'livery pictures on the Blender semis'], truckBoxes: [X, 'livery pictures on the Blender box truck'], busBoxes: [X, "the shuttle bus's livery picture"],
  trailerS: [X, 'gameplay side skirts under the trailers (no shooting under them)'], semiS: [X, 'gameplay side skirts under the semis'],
};
// map sections (the boxes a map function adds itself), by their "// ----" line: hand-classed where it matters
const SEC = {
  'map.js:500': [A, 'the whole CRATE map (crates, toys, the toy face)'], 'map.js:4484': [A, 'the range: targets, tyre walls, sandbags, the firing line'],
  'map.js:1160': [A, 'the pool deck: loungers, cabanas, the DJ booth, party lights'], 'map.js:1115': [Bg, 'the two towers: roofs, machine rooms'], 'map.js:1140': [Bg, 'the party block'], 'map.js:1181': [A, 'jump pads'],
  'map.js:1247': [A, 'the party block: penthouse furniture, neon, DJ'], 'map.js:1285': [A, 'the low roofs: AC, skylights, vents, crates, the corp flag'], 'map.js:1276': [A, "A, the hotel's roof: towel hut, hot tub, loungers, umbrellas"], 'map.js:1268': [A, "B, the bank's roof: machine room, JANK BANK sign, AC farm"],
  'map.js:1834': [A, 'the corner lots: sheds, trampolines, junk, kiddie pools'], 'map.js:1776': [A, "the park: playground, founder's plaza, pond footbridge"], 'map.js:1820': [A, 'the building site: frame, scaffold, digger, site office'], 'map.js:1756': [A, 'house yards: trampolines, bins, containers'],
  'map.js:1808': [A, 'the corner store: shelves, car park, bus stop'], 'map.js:1641': [A, 'A: the building site (hoarding, frame, scaffold, digger, sand)'], 'map.js:1672': [A, 'B: the MEGA-MART EXPRESS inside: aisles, tills, fridges, stockroom'],
  'map.js:1660': [Bg, 'the HOA clubhouse'], 'map.js:1585': [A, 'the main street: hedges, planters, the cul-de-sac'], 'map.js:1623': [A, 'the bus stop'],
  'map.js:2051': [A, 'the hall: tyre stacks, lamps, rack uprights'], 'map.js:2098': [A, 'the truck dock'], 'map.js:2044': [A, 'the fence and light masts'], 'map.js:2086': [A, 'the container yard crane'],
  'map.js:2238': [A, 'MID: the hall (tyre stacks, lamps, rack uprights)'], 'map.js:2282': [Bg, 'the courtyard (glass office front)'], 'map.js:2302': [A, 'B: the parcel shed (shelves, conveyors)'], 'map.js:2218': [A, 'the fence and light masts'],
  'map.js:2319': [A, 'the trailer park'], 'map.js:2270': [A, 'A: the container dock'],
  'map.js:2605': [Bg, 'the town wall: gates, towers, battlements'], 'map.js:2654': [A, 'the back lots: corral, blacksmith, outhouses, rail spur'], 'map.js:2721': [A, 'the mine: props, lamps, the shaft'], 'map.js:2617': [A, 'Main Street: hitching rails, barrels, signs, the bank'],
  'map.js:2679': [A, 'the open ground: the old fort, the mission, huts (props)'], 'map.js:2703': [Bg, 'over the canyon: bridge gates, lamps'], 'map.js:2669': [A, 'the cemetery: picket fence, graves, a crypt, the stagecoach'], 'map.js:2751': [A, 'the oasis: dock, camp'],
  'map.js:2712': [A, 'Mine Square: the well, stalls'], 'map.js:2821': [Bg, 'the town wall (S&D)'], 'map.js:2951': [A, 'B: the depot (payroll train, platform, station props)'], 'map.js:2927': [A, 'A: the mine head (props, lamps)'],
  'map.js:2861': [A, 'the back lots (S&D): corral, blacksmith, outhouses'], 'map.js:2903': [A, 'Mine Square (S&D): the well, the founder\'s cart, offices'], 'map.js:2874': [Bg, 'the church, bell tower and cemetery'], 'map.js:2833': [A, 'the stage stop: stagecoach, office'],
  'map.js:2894': [Bg, 'over the canyon (S&D): the trestle cart, bridge gates'],
  'map.js:3308': [A, 'the ways off it: pier, bait shack, boats, rope bridge posts'], 'map.js:3291': [A, 'Volcano Island: tiki village, jungle plants'], 'map.js:3392': [A, 'Volcano Island (S&D) plants'], 'map.js:3408': [A, 'the tiki bar and beach huts (S&D)'],
  'map.js:3649': [A, "grapple bait: window washers' platforms, hanging gold blocks"], 'map.js:3632': [A, 'C, the Spire hub deck: planters, benches'], 'map.js:3731': [A, 'the set pieces'], 'map.js:3725': [A, "mid: the Spire's hub deck (planters, benches)"], 'map.js:3714': [Bg, 'the links (glass block walkways)'],
  'map.js:3945': [A, 'THE GRAND BAZAAR: counters, goods, rugs, lamps (the stalls are round 4 models)'], 'map.js:3986': [Bg, 'the caravanserai (arcade, gallery)'], 'map.js:4013': [A, 'the spice market: sacks, cones of spice, lamps'], 'map.js:4048': [A, 'the gate plazas: fountains'],
  'map.js:4003': [A, 'the dye works: drying racks, canal bridges'], 'map.js:4041': [A, 'the potters: kilns, stacks of pots'], 'map.js:4034': [A, 'the tea house: cushions, garden'], 'map.js:4024': [A, 'the carpet yard: carpets on frames, rolls'], 'map.js:3935': [Bg, 'the city wall, corner towers'],
  'map.js:4120': [A, 'MID: the Grand Hall (counters, goods, lamps)'], 'map.js:4173': [A, 'EAST LANE: quays, bridges, moored boats'], 'map.js:4105': [Bg, 'the wall round it all, the gates'], 'map.js:4163': [A, 'WEST LANE: the spice alleys (lamps, awnings)'],
  'map.js:4393': [Bg, 'pillar rooms'], 'map.js:4415': [Bg, 'the pool rooms (tiles, water)'], 'map.js:4368': [Bg, 'drop ceilings and light panels'], 'map.js:4379': [Bg, 'the big hall: pillars, freestanding walls'], 'map.js:4408': [Bg, 'the Wet Room'], 'map.js:4412': [Bg, 'spawn lobbies: pillars'],
  'map.js:4717': [A, 'the radio mast yard: the mast, the radio shed, a generator'], 'map.js:4748': [A, 'the lake edge: dock, rowboat, canoe, reeds'], 'map.js:4759': [A, 'the road: fallen tree, power poles, the trailhead sign'], 'map.js:4639': [Bg, 'the cabin'],
  'map.js:4612': [A, 'the woods: dead trees, birches (the trunks left as boxes)'], 'map.js:4677': [A, 'the campsite: fire ring, log benches, picnic table, outhouse'], 'map.js:4697': [Bg, 'the fire lookout tower'], 'map.js:4631': [A, 'the clearing: standing stones, a dead tree, the office chair'],
  'map.js:4841': [Bg, 'windows onto the boarded back alley'], 'map.js:4913': [A, 'ARCADE: cabinets with glowing screens'], 'map.js:4899': [A, 'FOOD COURT: tables, the burger counter'], 'map.js:4893': [A, 'ENTRANCE HALL: the info kiosk, benches, planters'], 'map.js:4826': [Bg, 'the mall shell'],
  'map.js:817': [A, 'the cellar deck: valves, pipes, the wellbay'], 'map.js:810': [A, 'deck lights'], 'map.js:852': [A, 'the laydown deck: cargo baskets, gas bottles'], 'map.js:860': [A, 'the flare boom and its flame'], 'map.js:920': [A, 'the rig (S&D): deck lights, kit'], 'map.js:976': [A, 'the riser platform: riser module, kit'], 'map.js:961': [A, 'the bridge support platform: lifeboats, signs'],
  'jankburg.js:369': [A, 'over the streets: cables, hanging neon signs, washing lines; hazard bollards (the lights, vending machines, barrels and cars are round 4 models)'], 'jankburg.js:302': [A, 'landmarks: the HQ statue, flags'],
};
const TERR = /^(sand|wetsand|rock|rockf|rockmoss|dirt|dirtroad|grass|mud|needles|trail|basalt|lava|surf|sidewalk|asphalt|asphalt2|road|roadx|roadz|crosswalk|pavecity|wetroad|lawn|hedge|leaves2|burnt|water|lakewater)$/;
const ARCH = /^(wallpaper|brick|adobe|plaster|concrete|office|tenement|window|glassblock|glass|tile|pooltile|roof|roofg|roofpink|roofteal|roofblue|ceildark|ceilflick\d?|white|graffiti|marble|stone|cabinroof2?|logwall|towerwood|plywood)$/;
function guess(u) {
  const ms = u.mats.split(' ').map((kv) => { const [k, n] = kv.split(':'); return [k, +n]; }), tot = ms.reduce((s, [, n]) => s + n, 0) || 1;
  const t = ms.filter(([k]) => TERR.test(k)).reduce((s, [, n]) => s + n, 0) / tot, a = ms.filter(([k]) => ARCH.test(k)).reduce((s, [, n]) => s + n, 0) / tot;
  if (/^(the ground|paint|trails|the loop street)/i.test(u.name)) return C; // (floors and paint: flat, a texture job more than a model)
  if (/ground|paint|trails|outside|the look|render-only|sandbars|horizon/i.test(u.name) && t + a >= 0.5) return t >= a ? C : Bg;
  return t > 0.6 ? C : a > 0.6 ? Bg : A;
}
const NAME = { crate: 'Crate', platform: 'Platform', platform_sd: 'Platform (P&D)', rooftop: 'Rooftop', rooftop_sd: 'Rooftop (P&D)', suburb: 'Suburb', suburb_sd: 'Suburb (P&D)', warehouse: 'Warehouse', warehouse_sd: 'Warehouse (P&D)', desert: 'Desert', desert_sd: 'Desert (P&D)', islands: 'Islands', islands_sd: 'Islands (P&D)', skyline: 'Skyline', skyline_sd: 'Skyline (P&D)', bazaar: 'Bazaar', bazaar_sd: 'Bazaar (P&D)', range: 'Training range', backrooms: 'Backrooms', forest: 'Scary Forest', deadmall: 'Dead Mall', jankburg: 'Jankburg (Royale)' };
const PLAY = { range: -1, crate: 0, deadmall: 0, backrooms: 0 }; // (how often it's played: P&D layouts and the side maps a bit less)
const vis = (m, u) => { const deco = u.deco / u.boxes; let v = 1.2 + Math.log10(u.boxes) * 1.1 + (PLAY[m] ?? (/_sd$/.test(m) ? 0 : 0.4)); if (deco > 0.85) v -= 0.8; return Math.max(1, Math.min(5, Math.round(v))); };
const nice = (n) => n < 100 ? Math.round(n / 10) * 10 : n < 1000 ? Math.round(n / 50) * 50 : Math.round(n / 500) * 500;
const budget = (g, n) => { const k = g === Bg ? [6, 14] : g === C ? [4, 10] : [10, 24]; return `${nice(Math.max(40, n * k[0]))}-${nice(Math.max(120, n * k[1]))}`; }; // (tris for the whole unit, PS1 style: about what its boxes cost now, spent on shape)
const rows = { a: [], b: [], c: [], x: [] };
const unclassed = new Set();
for (const [m, us] of Object.entries(out)) for (const u of us) {
  let g, label;
  if (u.kind === 'kit') { const k = KIT[u.name]; if (!k) { unclassed.add(u.name); continue; } [g, label] = k; }
  else { const k = SEC[u.at]; if (k) [g, label] = k; else { g = guess(u); label = u.name.replace(/^\(function (\w+)\(\)\)$/, 'the rest of $1()'); } }
  rows[g].push({ map: m, c: u.c, size: u.size, label, where: u.kind === 'kit' ? `\`${u.name}()\` shared/${u.at}` : `shared/${u.at} (section)`, copies: u.copies || 1, boxes: u.boxes, deco: u.deco, vis: vis(m, u), budget: budget(g, u.boxes), mats: u.mats.split(' ').slice(0, 3).map((s) => s.split(':')[0]).join(', ') });
}
if (unclassed.size) console.error('UNCLASSED', [...unclassed].join(' '));
fs.writeFileSync(OUT.replace(/\.md$/, '') + '.json', JSON.stringify(rows, null, 1));
for (const g of ['a', 'b', 'c', 'x']) console.log(g, rows[g].length, 'units', rows[g].reduce((s, r) => s + r.boxes, 0), 'boxes');
// ---- markdown
const order = Object.keys(NAME);
const md = [];
const tot = (g) => rows[g].reduce((s, r) => s + r.boxes, 0);
const table = (g, withLane) => {
  for (const m of order) {
    const all = rows[g].filter((r) => r.map === m), rs = all.filter((r) => r.boxes >= 3).sort((x, y) => y.vis - x.vis || y.boxes - x.boxes), small = all.filter((r) => r.boxes < 3);
    if (!rs.length) continue;
    md.push(`\n#### ${NAME[m]} (\`${m}\`): ${rs.reduce((s, r) => s + r.boxes, 0)} boxes\n`);
    md.push('| What | Built in | Copies | Boxes | Vis | Budget (tris) |'); md.push('|---|---|---|---|---|---|');
    for (const r of rs) md.push(`| ${r.label.replace(/\|/g, '/')} | ${r.where} | ${r.copies} | ${r.boxes}${r.deco === r.boxes ? ' (look only)' : ''} | ${r.vis} | ${r.budget} |`);
    if (small.length) md.push(`| (${small.length} more bits of 1-2 boxes) | | | ${small.reduce((s, r) => s + r.boxes, 0)} | 1 | |`);
  }
};
md.push('<!-- GROUP_A -->'); table('a'); md.push('<!-- GROUP_B -->'); table('b'); md.push('<!-- GROUP_C -->'); table('c');
md.push('<!-- GROUP_X -->');
for (const r of rows.x) md.push(`- ${NAME[r.map]}: ${r.label} (${r.where}, ${r.boxes} boxes)`);
fs.writeFileSync(OUT, md.join('\n') + '\n');
console.log('totals a', tot('a'), 'b', tot('b'), 'c', tot('c'));
fs.rmSync(tmp, { recursive: true, force: true });
