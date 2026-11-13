// Scenery: stuff around and below each map so it isn't floating in a void. No collision, purely to look at.
// Grounded maps sit on a plateau with cliffs dropping to a valley; city maps sit in a skyline; sky maps float over clouds.
// Far things use unlit colours pre-mixed with the sky colour (fake aerial perspective) so fog doesn't erase them.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const SCENES = {
  crate: { theme: 'sealed' }, // a giant playroom: the map draws the room itself
  platform: { theme: 'ocean', isles: false }, // an offshore rig in the North Sea (no desert islands out there)
  range: { theme: 'hills', flat: true },
  rooftop: { theme: 'city' }, // the street level (map deco) is the floor now, no skirt
  skyline: { theme: 'city' },
  suburb: { theme: 'hills', flat: true }, // a forest out past the tree ring, green hills and more forest into the distance
  warehouse: { theme: 'industrial', flat: true, skyline: true }, // flat ground past the fence, a city on the horizon
  desert: { theme: 'desert', flat: true }, // the sand just keeps going: no cliff
  bazaar: { theme: 'desert', flat: true }, // sand all round outside the walls, no cliff
  islands: { theme: 'ocean' },
  battleisland: { theme: 'ocean', mtn: false }, // open ocean round the island: no mountain ring on the horizon, just the far isles
  backrooms: { theme: 'sealed' },
  jankburg: { theme: 'industrial', flat: true }, // sheds, stacks and a crane past the outer ring; the megacity is the map's own deco
  forest: { theme: 'forest', flat: true }, // the woods go on past the fog: a black tree line against the sky
};
const PAL = {
  sky: { mtn: 0x8a7aa8, snow: 0xffffff, floor: 0xffffff },
  city: { mtn: 0x5a6a8a, snow: 0xdde6f0, floor: 0x2a2f3a },
  hills: { mtn: 0x4a6a4a, snow: 0xf0f4f8, floor: 0x5a8a3a, hill: 0x4a7a32, tree: 0x2f5a24 },
  industrial: { mtn: 0x6a6070, snow: 0xe0e0e8, floor: 0x5a5650, hill: 0x6a645a },
  desert: { mtn: 0xb07a4a, snow: 0xf2dcae, floor: 0xd8b07a, hill: 0xcfa468, mesa: 0xb8683a },
  ocean: { mtn: 0x4a7a6a, snow: 0xf0f4f8, floor: 0x2a6aa8, isle: 0x3a8a3a },
  forest: { mtn: 0x0b111b, snow: 0x1e2838, floor: 0x0d1118, hill: 0x0a0f16, tree: 0x05080d },
};

let group = null;
export const sceneryGroup = () => group; // (weather.js dims the far backdrop under a storm, for the frame being drawn)
const rnd = (seed) => () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const fade = (hex, fogHex, k) => new THREE.Color(hex).lerp(new THREE.Color(fogHex), k).getHex();
const basic = (hex) => new THREE.MeshBasicMaterial({ color: hex, fog: false });

export function buildScenery(scene, map, id, voidMesh) {
  if (group) { // everything in here was made for this map: geometries, materials and the city texture
    scene.remove(group);
    group.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
  }
  group = new THREE.Group();
  scene.add(group);
  const cfg = map.stream ? { theme: 'sealed' } : SCENES[id] || (map.base && SCENES[map.base]) || { theme: 'sky' }; // an S&D version stands in its map's world; a streamed city (OVERDUE) brings its own horizon
  if (cfg.theme === 'sealed') { if (voidMesh) voidMesh.visible = false; return; } // indoors all the way round: nothing out there
  const pal = PAL[cfg.theme];
  const fog = map.sky.fog;
  const r = rnd(id.length * 7919 + 13);
  // how big is the playable area, and where is "the ground"
  let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9, ground = 0;
  for (const b of map.boxes) {
    if (b.max[1] < -6 || b.min[1] > 2) continue;
    x0 = Math.min(x0, b.min[0]); x1 = Math.max(x1, b.max[0]); z0 = Math.min(z0, b.min[2]); z1 = Math.max(z1, b.max[2]);
  }
  if (x0 > x1) { x0 = -50; x1 = 50; z0 = -50; z1 = 50; }
  for (const b of map.boxes) if (b.max[1] <= 0.5 && b.max[1] > -6 && (b.max[0] - b.min[0]) * (b.max[2] - b.min[2]) > 400) ground = Math.min(ground, b.min[1]);
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, R = Math.max(x1 - x0, z1 - z0) / 2;
  const floorY = cfg.flat ? -0.06 : map.floorY ?? map.killY - 35; // where the scenery stands (flat: on the map's own ground)
  const planeY = map.floorY ?? floorY; // the far floor plane: flat maps with holes in them (canyons, pits) put it under the holes // flat: the map's ground goes out a long way, the floor carries on from it

  // ---- a ring of mountains, far away (unlit, faded into the sky)
  const mtnMat = basic(fade(pal.mtn, fog, 0.5)), snowMat = basic(fade(pal.snow, fog, 0.35));
  const drop = cfg.theme === 'sky' ? 50 : 0; // sky maps: the void plane sits under the cloud sea, so the bases go down past it
  for (let i = 0; i < (cfg.mtn === false ? 0 : 34); i++) {
    const a = (i / 34) * Math.PI * 2 + r() * 0.15, d = 700 + r() * 300;
    const h = 140 + r() * 260, rad = 90 + r() * 120;
    const m = new THREE.Mesh(new THREE.ConeGeometry(rad, h + drop, 5 + ((r() * 3) | 0)), mtnMat);
    m.position.set(cx + Math.cos(a) * d, floorY + (h - drop) / 2 - 20, cz + Math.sin(a) * d);
    m.rotation.y = r() * 3;
    group.add(m);
    // the cap is the top 0.32 h of the cone, so its base is as wide as the (taller, steeper) mountain is there
    if (cfg.theme !== 'desert' && h > 260) { const cap = new THREE.Mesh(new THREE.ConeGeometry(rad * 0.32 * h / (h + drop), h * 0.32, m.geometry.parameters.radialSegments), snowMat); cap.position.set(m.position.x, floorY + h - h * 0.16 - 20, m.position.z); cap.rotation.y = m.rotation.y; group.add(cap); }
  }

  // ---- the floor far below (valley / city streets / ocean / cloud sea)
  if (cfg.theme !== 'sky') {
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000).rotateX(-Math.PI / 2), basic(fade(pal.floor, fog, 0.35)));
    floor.position.set(cx, planeY, cz);
    group.add(floor);
    if (voidMesh) voidMesh.visible = false;
  } else if (voidMesh) { voidMesh.visible = true; voidMesh.position.y = map.killY - 85; } // below the clouds (they reach killY-73), not through them

  // ---- cliffs: the map sits on a plateau
  if (cfg.skirt) {
    const mat = cfg.skirt === 'tower'
      ? new THREE.MeshLambertMaterial({ color: 0x4a5060, flatShading: true })
      : new THREE.MeshLambertMaterial({ color: cfg.theme === 'desert' ? 0xa8764a : 0x6a5a4a, flatShading: true });
    const top = ground - 0.05, bot = floorY;
    const seg = 9;
    const edge = (ax, az, bx, bz, nx, nz) => {
      const len = Math.hypot(bx - ax, bz - az), n = Math.max(1, Math.round(len / seg));
      for (let i = 0; i < n; i++) {
        const t0 = i / n, t1 = (i + 1) / n;
        const px = ax + (bx - ax) * (t0 + t1) / 2, pz = az + (bz - az) * (t0 + t1) / 2;
        const out = cfg.skirt === 'tower' ? 0 : r() * 4;
        const w = len / n + 0.5, d = 6 + r() * 6, hgt = top - bot - r() * 12;
        const g = new THREE.BoxGeometry(Math.abs(nx) ? d : w, hgt, Math.abs(nx) ? w : d);
        const m = new THREE.Mesh(g, mat);
        m.position.set(px + nx * (d / 2 - 1 + out), top - hgt / 2, pz + nz * (d / 2 - 1 + out));
        group.add(m);
      }
    };
    edge(x0, z0, x1, z0, 0, -1); edge(x0, z1, x1, z1, 0, 1); edge(x0, z0, x0, z1, -1, 0); edge(x1, z0, x1, z1, 1, 0);
  }

  // ---- theme dressing on the valley floor
  const near = (min, max) => { const a = r() * Math.PI * 2, d = R + min + r() * (max - min); return [cx + Math.cos(a) * d, cz + Math.sin(a) * d]; };
  if (cfg.theme === 'hills' || cfg.theme === 'industrial') {
    const hillMat = basic(fade(pal.hill, fog, 0.3));
    for (let i = 0; i < 40; i++) { const [x, z] = near(40, 500); const s = 30 + r() * 70; const m = new THREE.Mesh(new THREE.SphereGeometry(s, 7, 4, 0, Math.PI * 2, 0, Math.PI / 2), hillMat); m.scale.y = 0.35 + r() * 0.3; m.position.set(x, floorY, z); group.add(m); }
  }
  if (cfg.theme === 'hills') {
    const treeMat = basic(fade(pal.tree, fog, 0.25)), trunk = basic(fade(0x5a3a1a, fog, 0.3));
    for (let i = 0; i < 160; i++) { const [x, z] = near(15, 420); const h = 10 + r() * 14; const t = new THREE.Mesh(new THREE.ConeGeometry(h * 0.35, h, 5), treeMat); t.position.set(x, floorY + h / 2 + 2, z); group.add(t); const tr = new THREE.Mesh(new THREE.BoxGeometry(1.2, 4, 1.2), trunk); tr.position.set(x, floorY + 2, z); group.add(tr); }
  }
  if (cfg.theme === 'industrial') {
    const shed = basic(fade(0x5a5a64, fog, 0.3)), roof = basic(fade(0x7a3a2a, fog, 0.3)), stack = basic(fade(0x8a8078, fog, 0.3));
    for (let i = 0; i < 26; i++) { const [x, z] = near(30, 380); const w = 30 + r() * 50, d = 20 + r() * 40, h = 12 + r() * 18; const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), shed); m.position.set(x, floorY + h / 2, z); group.add(m); const rf = new THREE.Mesh(new THREE.BoxGeometry(w + 2, 2, d + 2), roof); rf.position.set(x, floorY + h + 1, z); group.add(rf); }
    for (let i = 0; i < 8; i++) { const [x, z] = near(60, 360); const h = 60 + r() * 60; const m = new THREE.Mesh(new THREE.CylinderGeometry(3, 4.5, h, 8), stack); m.position.set(x, floorY + h / 2, z); group.add(m); }
    { const [x, z] = near(50, 120); const crane = basic(fade(0xffd21a, fog, 0.3)); const mast = new THREE.Mesh(new THREE.BoxGeometry(3, 90, 3), crane); mast.position.set(x, floorY + 45, z); group.add(mast); const jib = new THREE.Mesh(new THREE.BoxGeometry(60, 2.5, 2.5), crane); jib.position.set(x + 20, floorY + 88, z); group.add(jib); }
  }
  if (cfg.theme === 'desert') {
    const dune = basic(fade(pal.hill, fog, 0.3)), mesa = basic(fade(pal.mesa, fog, 0.35)), mesaTop = basic(fade(0xd08a50, fog, 0.35));
    for (let i = 0; i < 50; i++) { const [x, z] = near(30, 520); const s = 25 + r() * 60; const m = new THREE.Mesh(new THREE.SphereGeometry(s, 7, 4, 0, Math.PI * 2, 0, Math.PI / 2), dune); m.scale.set(1.6, 0.25 + r() * 0.2, 1); m.rotation.y = r() * 3; m.position.set(x, floorY, z); group.add(m); }
    for (let i = 0; i < 14; i++) { const [x, z] = near(120, 520); const h = 40 + r() * 70, rr = 25 + r() * 35; const m = new THREE.Mesh(new THREE.CylinderGeometry(rr, rr * 1.25, h, 7), mesa); m.position.set(x, floorY + h / 2, z); group.add(m); const tp = new THREE.Mesh(new THREE.CylinderGeometry(rr * 1.02, rr * 1.02, 2, 7), mesaTop); tp.position.set(x, floorY + h, z); group.add(tp); }
  }
  if (cfg.theme === 'ocean' && cfg.isles !== false) {
    const isle = basic(fade(pal.isle, fog, 0.35)), sand = basic(fade(0xe8d8a0, fog, 0.35)), palm = basic(fade(0x2f6a2a, fog, 0.3));
    for (let i = 0; i < 18; i++) { const [x, z] = near(80, 600); const s = 20 + r() * 50; const b = new THREE.Mesh(new THREE.CylinderGeometry(s, s * 1.2, 3, 8), sand); b.position.set(x, floorY + 1.5, z); group.add(b); const h = new THREE.Mesh(new THREE.ConeGeometry(s * 0.7, s * 0.6, 6), isle); h.position.set(x, floorY + 3 + s * 0.3, z); group.add(h); for (let k = 0; k < 3; k++) { const p = new THREE.Mesh(new THREE.ConeGeometry(3, 8, 5), palm); p.position.set(x + (r() - 0.5) * s, floorY + 8, z + (r() - 0.5) * s); group.add(p); } }
  }
  if (cfg.theme === 'city') {
    const c = document.createElement('canvas'); c.width = 16; c.height = 32;
    const x = c.getContext('2d'); x.fillStyle = '#1a1f2a'; x.fillRect(0, 0, 16, 32);
    for (let yy = 1; yy < 32; yy += 3) for (let xx = 1; xx < 16; xx += 3) { x.fillStyle = Math.random() < 0.4 ? '#ffe9a8' : '#2a3242'; x.fillRect(xx, yy, 2, 2); }
    const tex = new THREE.CanvasTexture(c); tex.magFilter = THREE.NearestFilter; tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    const towerMat = new THREE.MeshBasicMaterial({ map: tex, fog: false, color: new THREE.Color(1, 1, 1).lerp(new THREE.Color(fog), 0.25) });
    const hMax = map.cityCap != null ? map.cityCap - floorY : Math.max(40, ground - 18 - floorY); // you look down on the city: nothing pokes up to roof level to fake-grapple
    const from = map.cityR ? map.cityR - R + 40 : 60; // the map draws its own city out to cityR: these are just the horizon past it
    for (let i = 0; i < 220; i++) {
      const [px, pz] = near(from, from + 600);
      const w = 14 + r() * 24, h = Math.min(hMax, 40 + r() * 260);
      const g = new THREE.BoxGeometry(w, h, w);
      const uv = g.attributes.uv; for (let k = 0; k < uv.count; k++) uv.setXY(k, uv.getX(k) * w / 10, uv.getY(k) * h / 20);
      const m = new THREE.Mesh(g, towerMat);
      m.position.set(px, floorY + h / 2, pz);
      group.add(m);
    }
  }
  if (cfg.skyline) { // a downtown on the horizon: a tight cluster of towers off to one side, windows lit, faded by distance
    const c = document.createElement('canvas'); c.width = 16; c.height = 32;
    const x = c.getContext('2d'); x.fillStyle = '#141828'; x.fillRect(0, 0, 16, 32);
    for (let yy = 1; yy < 32; yy += 3) for (let xx = 1; xx < 16; xx += 3) { const k = Math.random(); x.fillStyle = k < 0.35 ? '#ffe9a8' : k < 0.42 ? '#ff4fd8' : k < 0.48 ? '#19e6ff' : '#262c40'; x.fillRect(xx, yy, 2, 2); }
    const tex = new THREE.CanvasTexture(c); tex.magFilter = THREE.NearestFilter; tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    const mat = new THREE.MeshBasicMaterial({ map: tex, fog: false, color: new THREE.Color(1, 1, 1).lerp(new THREE.Color(fog), 0.3) });
    const a0 = -2.4;
    for (let i = 0; i < 46; i++) {
      const a = a0 + (r() - 0.5) * 0.9, d = 480 + r() * 260, w = 18 + r() * 30, h = 50 + r() * 240 * (1 - Math.abs(a - a0));
      const g = new THREE.BoxGeometry(w, h, w);
      const uv = g.attributes.uv; for (let k = 0; k < uv.count; k++) uv.setXY(k, uv.getX(k) * w / 10, uv.getY(k) * h / 20);
      const m = new THREE.Mesh(g, mat); m.position.set(cx + Math.cos(a) * d, floorY + h / 2, cz + Math.sin(a) * d); group.add(m);
    }
  }
  if (cfg.theme === 'forest') { // ridge after ridge of pines, black against the night, out to the mountains
    const tree = basic(fade(pal.tree, fog, 0.12)), tree2 = basic(fade(pal.tree, fog, 0.32)), hill = basic(fade(pal.hill, fog, 0.2));
    for (let i = 0; i < 46; i++) { const [x, z] = near(150, 620); const s = 40 + r() * 90; const m = new THREE.Mesh(new THREE.SphereGeometry(s, 7, 4, 0, Math.PI * 2, 0, Math.PI / 2), hill); m.scale.y = 0.3 + r() * 0.35; m.position.set(x, floorY, z); group.add(m); }
    for (let i = 0; i < 520; i++) { const [x, z] = near(70, 600); const far = Math.hypot(x - cx, z - cz) > R + 300; const h = 14 + r() * 22; const t = new THREE.Mesh(new THREE.ConeGeometry(h * 0.3, h, 5), far ? tree2 : tree); t.position.set(x, floorY + h / 2 + (far ? 6 : 0), z); t.rotation.y = r() * 3; group.add(t); }
  }
  if (cfg.theme === 'sky') { // a sea of clouds below
    // merged into one mesh, the clouds aren't sorted against each other: no depth writes, or near ones cut holes in far ones
    const cl = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, fog: false, depthWrite: false });
    for (let i = 0; i < 90; i++) { const [x, z] = near(-R * 0.5, 700); const s = 30 + r() * 60; const m = new THREE.Mesh(new THREE.SphereGeometry(s, 7, 4), cl); m.scale.y = 0.25; m.position.set(x, map.killY - 30 - r() * 20, z); group.add(m); }
  }
  mergeByMaterial(group);
}

// one draw call per material instead of one per mountain / tree / tower: bake each piece's transform and merge
// (like the map boxes). the clouds lose per-cloud sorting, which doesn't show at one opacity without depth writes.
function mergeByMaterial(g) {
  const byMat = new Map();
  for (const m of g.children) {
    m.updateMatrix(); m.geometry.applyMatrix4(m.matrix);
    m.position.set(0, 0, 0); m.rotation.set(0, 0, 0); m.scale.set(1, 1, 1);
    if (!byMat.has(m.material)) byMat.set(m.material, []);
    byMat.get(m.material).push(m);
  }
  g.clear();
  for (const [mat, list] of byMat) {
    const merged = list.length > 1 ? mergeGeometries(list.map((m) => m.geometry), false) : null;
    if (!merged) { for (const m of list) g.add(m); continue; } // one piece, or shapes that don't merge: keep them as they are
    for (const m of list) m.geometry.dispose();
    g.add(new THREE.Mesh(merged, mat));
  }
}
