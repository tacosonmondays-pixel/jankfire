// Renderer, low-res pixel crunch, the map, the sky, the void.
import * as THREE from 'three';
import { buildScenery } from './scenery.js';
import { BOXES, MAP, setMap, MAPS } from '/shared/map.js';
import { resetGrid } from '/shared/physics.js';
import { jankify, jankUniforms } from './jank.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { G } from './ctx.js';
import { marbles } from './marbles.js';
import { updateBackrooms } from './backrooms.js';
import { addVibe } from './vibe.js';
import { addForest } from './forestmats.js';
import { addIslands } from './islandmats.js';
import { addRig } from './rigmats.js';
import { updateForest, forestMap } from './forest.js';
import { shredMap, updateShredPit } from './shredpit.js'; // the Warehouse's shredder pit: the drums, the glow, the grind
import { buildProps, hasProp } from './props.js';
import { liquidBox, buildLiquids, updateLiquids, liquidsMap, setLiquidQ } from './liquids.js'; // water that moves, lava that flows, splashes
import { updateFlames } from './flames.js'; // real fire
import { gfxGuard, initGfxGuard } from './gfxguard.js';
import { initLighting, lightingMap, lightingRefresh, updateLighting, setLightPreset, aoBegin, aoBake, aoMaterials, setSunBoxes } from './lighting.js';

// scale = render resolution multiplier, snap = vertical vertex-snap grid (0 = off)
export const JANK = [
  { name: 'Potato', scale: 0.22, snap: 160 },
  { name: 'Crusty', scale: 0.36, snap: 220 },
  { name: 'Mid', scale: 0.6, snap: 360 },
  { name: 'Too HD', scale: 1, snap: 0 },
];
let jank = JANK[1];
const clouds = [];
let sun;

function canvasTex(size, draw, w) {
  const c = document.createElement('canvas');
  c.width = w || size; c.height = size;
  draw(c.getContext('2d'), size, w || size);
  const t = new THREE.CanvasTexture(c);
  // crunchy up close, but mipmapped far away so floors don't shimmer and give you a headache
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestMipmapLinearFilter; t.generateMipmaps = true;
  t.anisotropy = 4;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function speckle(g, s, rgb, vary, px = 2, w) {
  for (let y = 0; y < s; y += px) for (let x = 0; x < (w || s); x += px) {
    const k = (Math.random() - 0.5) * vary;
    g.fillStyle = `rgb(${rgb[0] + k | 0},${rgb[1] + k | 0},${rgb[2] + k | 0})`;
    g.fillRect(x, y, px, px);
  }
}
const rnd = (n) => (Math.random() * n) | 0;

// [texture, metres per tile] — UVs come from world position so neighbouring boxes line up perfectly
function makeMaterials() {
  const siding = (rgb, line) => (g, s) => { speckle(g, s, rgb, 8, 2); g.fillStyle = line; for (let y = 3; y < s; y += 4) g.fillRect(0, y, s, 1); };
  const container = (rgb) => (g, s) => { g.fillStyle = `rgb(${rgb})`; g.fillRect(0, 0, s, s); g.fillStyle = 'rgba(0,0,0,0.25)'; for (let x = 0; x < s; x += 4) g.fillRect(x, 0, 2, s); };
  const T = {
    grass: [canvasTex(16, (g, s) => { speckle(g, s, [86, 170, 64], 40, 2); }), 2],
    dirt: [canvasTex(16, (g, s) => { speckle(g, s, [130, 92, 58], 34, 2); }), 2],
    stone: [canvasTex(16, (g, s) => {
      speckle(g, s, [140, 140, 150], 24, 2);
      g.fillStyle = '#555'; g.fillRect(0, 7, s, 1); g.fillRect(0, 15, s, 1); g.fillRect(7, 0, 1, 7); g.fillRect(3, 8, 1, 7); g.fillRect(12, 8, 1, 7);
    }), 2],
    wood: [canvasTex(16, (g, s) => { speckle(g, s, [160, 110, 60], 20, 1); g.fillStyle = '#5a3a1a'; for (let y = 3; y < s; y += 4) g.fillRect(0, y, s, 1); }), 2],
    crate: [canvasTex(16, (g, s) => {
      speckle(g, s, [176, 128, 70], 20, 1);
      g.fillStyle = '#5a3a1a'; g.fillRect(0, 0, s, 2); g.fillRect(0, s - 2, s, 2); g.fillRect(0, 0, 2, s); g.fillRect(s - 2, 0, 2, s);
      for (let i = 0; i < s; i++) { g.fillRect(i, i, 2, 1); g.fillRect(s - 1 - i, i, 2, 1); }
    }), 2],
    missing: [canvasTex(32, (g) => { for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) { g.fillStyle = (x + y) % 2 ? '#000' : '#ff00dc'; g.fillRect(x * 16, y * 16, 16, 16); } }), 4],
    pad: [canvasTex(16, (g, s) => { g.fillStyle = '#00e5ff'; g.fillRect(0, 0, s, s); g.fillStyle = '#fff'; g.fillRect(7, 3, 2, 10); g.fillRect(5, 5, 6, 2); g.fillRect(4, 6, 8, 1); }), 2],
    pink: [canvasTex(16, (g, s) => { speckle(g, s, [255, 120, 200], 30, 2); }), 2],
    gold: [canvasTex(16, (g, s) => { speckle(g, s, [240, 200, 60], 40, 2); }), 2],
    sand: [canvasTex(16, (g, s) => { speckle(g, s, [222, 190, 130], 22, 1); }), 2],
    adobe: [canvasTex(16, (g, s) => { speckle(g, s, [214, 176, 128], 14, 2); g.fillStyle = '#a8845a'; g.fillRect(3, 4, 1, 5); g.fillRect(4, 8, 3, 1); g.fillRect(11, 2, 1, 3); g.fillRect(9, 12, 4, 1); }), 3],
    cloth: [canvasTex(16, (g, s) => { for (let x = 0; x < s; x += 4) { g.fillStyle = (x / 4) % 2 ? '#e8e0d0' : '#c8302a'; g.fillRect(x, 0, 4, s); } }), 2],
    concrete: [canvasTex(16, (g, s) => { speckle(g, s, [150, 150, 152], 16, 2); }), 3],
    grid: [canvasTex(16, (g, s) => { speckle(g, s, [128, 128, 132], 8, 4); g.fillStyle = '#6a6a70'; g.fillRect(0, 0, s, 1); g.fillRect(0, 0, 1, s); }), 2],
    helipad: [canvasTex(32, (g) => {
      speckle(g, 32, [60, 60, 64], 10, 2);
      g.strokeStyle = '#ffd21a'; g.lineWidth = 2; g.beginPath(); g.arc(16, 16, 12, 0, Math.PI * 2); g.stroke();
      g.fillStyle = '#fff'; g.fillRect(11, 9, 2, 14); g.fillRect(19, 9, 2, 14); g.fillRect(11, 15, 10, 2);
    }), 11],
    roadx: [canvasTex(32, (g, s) => { speckle(g, s, [58, 58, 62], 10, 2); g.fillStyle = '#e8c020'; for (let x = 0; x < s; x += 16) g.fillRect(x, 0, 8, 1); g.fillRect(0, s - 1, 0, 0); }), 12],
    roadz: [canvasTex(32, (g, s) => { speckle(g, s, [58, 58, 62], 10, 2); g.fillStyle = '#e8c020'; for (let y = 0; y < s; y += 16) g.fillRect(0, y, 1, 8); }), 12],
    road: [canvasTex(16, (g, s) => { speckle(g, s, [58, 58, 62], 10, 2); }), 3],
    sidewalk: [canvasTex(16, (g, s) => { speckle(g, s, [180, 178, 172], 12, 2); g.fillStyle = '#8a8884'; g.fillRect(0, 0, s, 1); g.fillRect(0, 0, 1, s); }), 2],
    white: [canvasTex(16, siding([235, 232, 225], '#b8b4aa')), 1.2],
    blue: [canvasTex(16, siding([120, 160, 205], '#5a7aa0')), 1.2],
    yellow: [canvasTex(16, siding([235, 210, 120], '#a89050')), 1.2],
    mint: [canvasTex(16, siding([150, 215, 180], '#6a9a80')), 1.2],
    brick: [canvasTex(16, (g, s) => {
      speckle(g, s, [160, 70, 50], 20, 2); g.fillStyle = '#d8cfc0';
      for (let y = 0; y < s; y += 4) { g.fillRect(0, y, s, 1); for (let x = (y / 4) % 2 ? 0 : 4; x < s; x += 8) g.fillRect(x, y, 1, 4); }
    }), 1.5],
    plaster: [canvasTex(16, (g, s) => { speckle(g, s, [226, 218, 200], 8, 4); }), 2],
    carpet: [canvasTex(16, (g, s) => { speckle(g, s, [140, 70, 80], 18, 1); }), 2],
    tile: [canvasTex(16, (g, s) => { speckle(g, s, [220, 230, 235], 6, 4); g.fillStyle = '#9ab'; for (let i = 0; i < s; i += 4) { g.fillRect(i, 0, 1, s); g.fillRect(0, i, s, 1); } }), 1],
    roof: [canvasTex(16, (g, s) => { speckle(g, s, [140, 52, 44], 20, 2); g.fillStyle = '#5a1a14'; for (let y = 3; y < s; y += 4) g.fillRect(0, y, s, 1); }), 1.5],
    roofg: [canvasTex(16, (g, s) => { speckle(g, s, [80, 82, 88], 14, 2); g.fillStyle = '#3a3a40'; for (let y = 3; y < s; y += 4) g.fillRect(0, y, s, 1); }), 1.5],
    metal: [canvasTex(16, (g, s) => { speckle(g, s, [150, 155, 160], 10, 2); g.fillStyle = '#7a7e84'; for (let x = 0; x < s; x += 4) g.fillRect(x, 0, 1, s); }), 1.5],
    hazard: [canvasTex(16, (g, s) => { for (let i = -s; i < s * 2; i += 8) { g.fillStyle = '#ffd21a'; g.beginPath(); g.moveTo(i, 0); g.lineTo(i + 4, 0); g.lineTo(i + 4 - s, s); g.lineTo(i - s, s); g.fill(); } }), 1],
    office: [canvasTex(32, (g) => { // a 2-bay x 1-floor chunk of skyscraper facade
      g.fillStyle = '#8a8e96'; g.fillRect(0, 0, 32, 32);
      for (const x of [2, 18]) { const lit = Math.random() < 0.35; g.fillStyle = lit ? '#ffe9a0' : '#2a3a5a'; g.fillRect(x, 6, 12, 20); g.fillStyle = lit ? '#fff6d0' : '#4a6a9a'; g.fillRect(x + 1, 7, 4, 6); }
      g.fillStyle = '#6a6e76'; g.fillRect(0, 0, 32, 2);
    }), 4],
    glassblock: [canvasTex(16, (g, s) => { g.fillStyle = '#3a5a80'; g.fillRect(0, 0, s, s); g.fillStyle = '#5a80b0'; for (let i = 0; i < s; i += 8) { g.fillRect(i, 0, 1, s); g.fillRect(0, i, s, 1); } g.fillStyle = '#9fc4ea'; g.fillRect(2, 2, 3, 3); }), 3],
    leaves: [canvasTex(16, (g, s) => { speckle(g, s, [60, 140, 50], 50, 2); }), 2],
    hedge: [canvasTex(16, (g, s) => { speckle(g, s, [50, 110, 45], 40, 2); }), 1.5],
    containerr: [canvasTex(16, container('170,52,40')), 2],
    containerb: [canvasTex(16, container('40,80,150')), 2],
    containerg: [canvasTex(16, container('50,120,70')), 2],
    billboard: [canvasTex(64, (g, s, w) => {
      g.fillStyle = '#ff4fd8'; g.fillRect(0, 0, w, s); g.fillStyle = '#ffe14d'; g.fillRect(4, 4, w - 8, s - 8);
      g.fillStyle = '#120818'; g.font = 'bold 26px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillText(['JANK COLA', 'BUY BREAD', 'GRAPPLE INC', 'SPOON BANK'][rnd(4)], w / 2, s / 2);
    }, 192), 12],
  };
  const out = {};
  const basic = new Set(['pad', 'water', 'office', 'light', 'tail', 'glass', 'billboard', 'missing']);
  for (const [k, [t, tile]] of Object.entries(T)) {
    out[k] = { mat: basic.has(k) ? new THREE.MeshBasicMaterial({ map: t }) : new THREE.MeshLambertMaterial({ map: t }), tile };
  }
  out.water = { mat: new THREE.MeshBasicMaterial({ color: 0x3a9ae8, transparent: true, opacity: 0.75 }), tile: 2 };
  out.glass = { mat: new THREE.MeshLambertMaterial({ color: 0x223448, emissive: 0x0a1420 }), tile: 2 };
  out.tire = { mat: new THREE.MeshLambertMaterial({ color: 0x1a1a1c }), tile: 1 };
  out.light = { mat: new THREE.MeshBasicMaterial({ color: 0xfff2b0 }), tile: 1 };
  out.tail = { mat: new THREE.MeshBasicMaterial({ color: 0xff2a2a }), tile: 1 };
  for (const [k, hex] of Object.entries({ carred: 0xc8202c, carblue: 0x2050b0, carwhite: 0xe8e8e8, carblack: 0x26262a, cargreen: 0x2a8a4a, caryellow: 0xe8c020, chrome: 0xc8ccd2 })) {
    out[k] = { mat: new THREE.MeshLambertMaterial({ color: hex }), tile: 1 };
  }
  // backrooms: mono-yellow wallpaper, old damp carpet, drop-ceiling tiles with a fluorescent panel in every 4 m cell
  // (the panels are in the texture and glow through an emissive map, so thousands of lights cost nothing)
  const lam = (t, tile, o) => ({ mat: new THREE.MeshLambertMaterial({ map: t, ...o }), tile });
  out.wallpaper = lam(canvasTex(32, (g, s) => {
    speckle(g, s, [206, 188, 106], 7, 2);
    g.fillStyle = 'rgba(170,148,70,0.3)'; for (let x = 0; x < s; x += 8) g.fillRect(x, 0, 2, s); // faint stripes
    g.fillStyle = 'rgba(150,128,58,0.3)'; for (let y = 0; y < s; y += 8) for (let x = 4; x < s; x += 8) { g.fillRect(x, y + 1, 1, 1); g.fillRect(x + 1, y, 1, 1); g.fillRect(x + 2, y + 1, 1, 1); } // little chevrons
  }), 1.6);
  out.carpetb = lam(canvasTex(64, (g, s) => {
    speckle(g, s, [168, 150, 96], 16, 1);
    g.fillStyle = 'rgba(70,58,26,0.13)'; // damp patches (drawn wrapped so the tile is seamless)
    for (let i = 0; i < 6; i++) { const x = rnd(s), y = rnd(s), rr = 4 + rnd(10); for (const ox of [-s, 0, s]) for (const oy of [-s, 0, s]) { g.beginPath(); g.arc(x + ox, y + oy, rr, 0, Math.PI * 2); g.fill(); } }
  }), 6);
  out.officecarpet = lam(canvasTex(16, (g, s) => { speckle(g, s, [86, 98, 130], 14, 1); g.fillStyle = 'rgba(40,44,60,0.4)'; g.fillRect(0, 0, s, 1); g.fillRect(0, 0, 1, s); }), 1);
  out.cubicle = lam(canvasTex(16, (g, s) => { speckle(g, s, [116, 126, 150], 10, 1); g.fillStyle = '#5c606a'; g.fillRect(0, 0, s, 1); }), 1.4);
  const ceil = (lit) => (g, s) => {
    speckle(g, s, [214, 208, 186], 6, 2);
    g.fillStyle = 'rgba(140,134,110,0.35)'; for (let i = 4; i < s; i += 8) { g.fillRect(i, 0, 1, s); g.fillRect(0, i, s, 1); } // 0.5 m tiles
    g.fillStyle = '#cfcab8'; g.fillRect(19, 27, 26, 10);
    g.fillStyle = lit ? '#fffdf0' : '#8f8c80'; g.fillRect(20, 28, 24, 8); // the panel, right in the middle of the cell
    if (lit) { g.fillStyle = '#efe8c8'; for (let x = 23; x < 44; x += 4) g.fillRect(x, 28, 1, 8); }
  };
  // the tiles glow a little too (light bouncing round the room), the panel a lot
  const glow = canvasTex(64, (g, s) => { g.fillStyle = '#8c8c8c'; g.fillRect(0, 0, s, s); g.fillStyle = '#fff'; g.fillRect(20, 28, 24, 8); });
  const lit = canvasTex(64, ceil(true));
  out.ceiltile = lam(lit, 4, { emissiveMap: glow, emissive: 0xfff2d2 });
  out.ceilflick = lam(lit, 4, { emissiveMap: glow, emissive: 0xfff2d2 }); // its own material so it can flicker
  out.ceilflick2 = lam(lit, 4, { emissiveMap: glow, emissive: 0xfff2d2 }); out.ceilflick3 = lam(lit, 4, { emissiveMap: glow, emissive: 0xfff2d2 }); // and two more, so they don't all blink in sync
  out.ceildark = lam(canvasTex(64, ceil(false)), 4);
  // the pool rooms: bright white tiles that seem lit from nowhere
  out.pooltile = lam(canvasTex(16, (g, s) => { speckle(g, s, [234, 242, 242], 5, 4); g.fillStyle = '#a3bcc0'; for (let i = 0; i < s; i += 4) { g.fillRect(i, 0, 1, s); g.fillRect(0, i, s, 1); } }), 1, { emissive: 0x3c4c50 });
  out.poolwater = { mat: new THREE.MeshBasicMaterial({ color: 0x86dbe6, transparent: true, opacity: 0.42, depthWrite: false }), tile: 2 };
  // (liquids.js draws the liquids; these are what a box of one looks like anywhere it isn't a liquid surface)
  out.greenglass = { mat: new THREE.MeshBasicMaterial({ color: 0x3a9ae8, transparent: true, opacity: 0.75 }), tile: 2 }; // the greenhouse's panes (used to borrow 'water')
  for (const [k, hex] of Object.entries({ dyemagenta: 0xff4fd8, dyeyellow: 0xffe14d, dyeblue: 0x4f8aff, dyemint: 0x7dffc8, dyetoyred: 0xff3a3a, dyetoyteal: 0x3ff0f0, oil: 0x0a080e, acid: 0x7dff1a, slime: 0x39ff14, cola: 0x3a1206 })) out[k] = { mat: new THREE.MeshBasicMaterial({ color: hex }), tile: 1 };
  addVibe(out, canvasTex, speckle); // the map pass look (vibe.js)
  addForest(out, canvasTex, speckle); // scary forest (forestmats.js)
  addIslands(out, canvasTex, speckle); // islands (islandmats.js)
  addRig(out, canvasTex, speckle); // the oil rig (rigmats.js)
  aoMaterials(out); // baked corner AO in the vertex colours (lighting.js)
  for (const v of Object.values(out)) if (!v.mat.onBeforeCompile || v.mat.onBeforeCompile === THREE.Material.prototype.onBeforeCompile) hazify(v.mat, v.mat.isMeshBasicMaterial ? 0.45 : 1);
  return out;
}

// a box mesh for a map box. huge ones (the long street, the lawn out to the horizon) get cut into <= 32 m pieces:
// a single triangle hundreds of metres long with corners behind the camera gets dropped by some GPUs (whole lawns vanished)
const SEG = (v) => Math.min(48, Math.max(1, Math.ceil(v / 32)));
const boxGeo = (sx, sy, sz) => new THREE.BoxGeometry(sx, sy, sz, SEG(sx), SEG(sy), SEG(sz));

// height haze (map.haze, the city maps): a fog layer that gets thicker the lower and further you look, so the streets far
// below are soft shapes and lights in a haze while fights across the rooftops stay clear. one shared set of uniforms,
// patched into the map materials' fog. glowing stuff (neon, lit windows, signs) only takes part of it: lights shine through
export const hazeUniforms = { uHaze: { value: new THREE.Vector4(0, 0, -1, 100) }, uHazeColor: { value: new THREE.Color(0) } }; // strength, top y, bottom y, depth scale
const HAZE_FOG = `#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	vec3 fogC = fogColor;
	if ( uHaze.x > 0.0 ) {
		float hz = clamp( ( uHaze.y - vHazeY ) / ( uHaze.y - uHaze.z ), 0.0, 1.0 );
		float hf = uHaze.x * uHazeK * hz * ( 0.35 + 0.65 * hz ) * ( 1.0 - exp( - vFogDepth / uHaze.w ) );
		fogC = mix( fogColor, uHazeColor, clamp( hf / max( 0.001, fogFactor + hf ), 0.0, 1.0 ) );
		fogFactor = 1.0 - ( 1.0 - fogFactor ) * ( 1.0 - hf );
	}
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogC, fogFactor );
#endif`;
export function hazify(mat, k) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uHaze = hazeUniforms.uHaze; sh.uniforms.uHazeColor = hazeUniforms.uHazeColor; sh.uniforms.uHazeK = { value: k };
    sh.vertexShader = 'varying float vHazeY;\n' + sh.vertexShader.replace('#include <fog_vertex>', '#include <fog_vertex>\n\tvHazeY = ( modelMatrix * vec4( transformed, 1.0 ) ).y;');
    sh.fragmentShader = 'uniform vec4 uHaze;\nuniform vec3 uHazeColor;\nuniform float uHazeK;\nvarying float vHazeY;\n' + sh.fragmentShader.replace('#include <fog_fragment>', HAZE_FOG);
  };
  mat.customProgramCacheKey = () => 'haze';
}

// world-space UVs: each face picks the two axes it spans, so textures continue across boxes
function worldUV(geo, cx, cy, cz, tile) {
  const pos = geo.attributes.position, nrm = geo.attributes.normal, uv = geo.attributes.uv;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i) + cx, y = pos.getY(i) + cy, z = pos.getZ(i) + cz;
    const ax = Math.abs(nrm.getX(i)), ay = Math.abs(nrm.getY(i));
    if (ax > 0.5) uv.setXY(i, z / tile, y / tile);
    else if (ay > 0.5) uv.setXY(i, x / tile, z / tile);
    else uv.setXY(i, x / tile, y / tile);
  }
}

// indoor maps (sealed, the mall): the ceiling slabs don't cast sun shadows, so the "sun" reads as the overhead lights
function noCastFn(def) {
  if (!def || !(def.sealed || def.zm)) return null;
  return (b) => b.min[1] >= 3.4 && b.max[1] - b.min[1] <= 1.5 && (b.max[0] - b.min[0]) * (b.max[2] - b.min[2]) >= 6;
}
const aoSmall = (sx, sy, sz) => Math.max(sx, sy, sz) < 0.35; // tiny trims: not worth the samples
function mapMesh(scene, k, merged) { // one merged map mesh. keys ending in '~' are ceilings that cast no shadow
  const nc = k.endsWith('~'), mk = nc ? k.slice(0, -1) : k;
  const m = new THREE.Mesh(merged, MAT[mk].mat);
  if (nc) m.userData.noCast = true;
  return m;
}

let MAT = null;
const mapMeshes = [];
const chunkMeshes = [];
// one merged mesh per material: thousands of boxes, a couple dozen draw calls
function buildMap(scene) {
  if (!MAT) MAT = makeMaterials();
  for (const m of mapMeshes) { scene.remove(m); m.geometry.dispose(); }
  mapMeshes.length = 0;
  chunkMeshes.length = 0;
  const def = MAPS[MAP.id];
  if (def && def.chunk) { buildChunked(scene, def); return; }
  const groups = new Map();
  const push = (k, g) => { if (!groups.has(k)) groups.set(k, []); groups.get(k).push(g); };
  // deco: drawn, never bumped into. a Blender prop stands in only for real boxes (props.js draws map.boxes.props): look-only
  // scenery keeps its boxes (the city alone has hundreds of streetlights and cars, too many models to draw one by one)
  const all = def && def.deco ? [...BOXES, ...def.deco] : BOXES, nReal = BOXES.length;
  const ncf = noCastFn(def), liq = [];
  aoBegin(all, ncf); setSunBoxes(all);
  for (let i = 0; i < all.length; i++) {
    const b = all[i];
    if (i < nReal && b.pv && hasProp(b.pv)) continue;
    if (liquidBox(b)) { liq.push(b); continue; } // water, lava, fire: liquids.js / flames.js draw those
    const sx = b.max[0] - b.min[0], sy = b.max[1] - b.min[1], sz = b.max[2] - b.min[2];
    const cx = (b.min[0] + b.max[0]) / 2, cy = (b.min[1] + b.max[1]) / 2, cz = (b.min[2] + b.max[2]) / 2;
    const mk0 = MAT[b.mat] ? b.mat : 'stone', small = aoSmall(sx, sy, sz);
    const mk = ncf && ncf(b) ? mk0 + '~' : mk0;
    if (b.fit) { const g = boxGeo(sx, sy, sz); if (b.rot) g.rotateY(b.rot); g.translate(cx, cy, cz); push(mk, aoBake(g, small).toNonIndexed()); continue; } // the texture once per face (signs, faces)
    if (b.rot) { const g = boxGeo(sx, sy, sz); worldUV(g, 0, 0, 0, MAT[mk0].tile); g.rotateY(b.rot); g.translate(cx, cy, cz); push(mk, aoBake(g, small).toNonIndexed()); continue; } // turned (render-only boxes: angled streets and blocks)
    if (b.mat === 'grass' && sy > 0.6) { // grass on top, dirt on the sides
      const g = boxGeo(sx, sy, sz);
      const top = g.clone();
      // split the box faces: index groups 2 = +y
      const keep = (geo, faces) => { const idx = []; for (const f of faces) { const gr = geo.groups[f]; for (let i = gr.start; i < gr.start + gr.count; i++) idx.push(geo.index.array[i]); } geo.setIndex(idx); geo.clearGroups(); return geo; };
      keep(top, [2]); keep(g, [0, 1, 3, 4, 5]);
      worldUV(top, cx, cy, cz, MAT.grass.tile); worldUV(g, cx, cy, cz, MAT.dirt.tile);
      top.translate(cx, cy, cz); g.translate(cx, cy, cz);
      push('grass', aoBake(top, small).toNonIndexed()); push('dirt', aoBake(g, small).toNonIndexed());
      continue;
    }
    const g = boxGeo(sx, sy, sz);
    worldUV(g, cx, cy, cz, MAT[mk0].tile);
    g.translate(cx, cy, cz);
    push(mk, aoBake(g, small).toNonIndexed());
  }
  for (const [k, list] of groups) {
    const merged = mergeGeometries(list, false);
    for (const g of list) g.dispose();
    if (!merged) continue;
    const m = mapMesh(scene, k, merged);
    if (k === 'water') m.renderOrder = 2;
    scene.add(m);
    mapMeshes.push(m);
  }
  buildLiquids(scene, liq, all, def, hazify);
}

// huge maps (map.chunk metres): one merged mesh per material per chunk, so what's behind you or deep in the fog isn't
// drawn. map.deco boxes are drawn too but never bumped into. boxes bigger than a chunk (floors, ceilings, the long
// outer walls) go in one mesh per material that's always drawn, or they'd make their whole chunk impossible to cull
function buildChunked(scene, def) {
  const C = def.chunk, groups = new Map();
  const all = def.deco ? [...BOXES, ...def.deco] : BOXES, nReal = BOXES.length;
  const ncf = noCastFn(def), liq = [];
  aoBegin(all, ncf); setSunBoxes(all);
  for (let i = 0; i < all.length; i++) {
    const b = all[i];
    if (i < nReal && b.pv && hasProp(b.pv)) continue; // (as in buildMap: only real boxes give way to a prop)
    if (liquidBox(b)) { liq.push(b); continue; } // (liquids.js)
    const sx = b.max[0] - b.min[0], sy = b.max[1] - b.min[1], sz = b.max[2] - b.min[2];
    const cx = (b.min[0] + b.max[0]) / 2, cy = (b.min[1] + b.max[1]) / 2, cz = (b.min[2] + b.max[2]) / 2;
    const mk = MAT[b.mat] ? b.mat : 'stone', nc = ncf && ncf(b) ? '~' : '';
    const key = Math.max(sx, sz) > C ? mk + nc : mk + '|' + Math.floor(cx / C) + ',' + Math.floor(cz / C) + nc;
    const g = boxGeo(sx, sy, sz);
    if (b.rot) { if (!b.fit) worldUV(g, 0, 0, 0, MAT[mk].tile); g.rotateY(b.rot); } // turned render-only boxes (Jankburg's streets)
    else if (!b.fit) worldUV(g, cx, cy, cz, MAT[mk].tile);
    g.translate(cx, cy, cz);
    if (!groups.has(key)) groups.set(key, { k: mk, nc, list: [] });
    groups.get(key).list.push(aoBake(g, aoSmall(sx, sy, sz)).toNonIndexed());
  }
  for (const [key, { k, nc, list }] of groups) {
    const merged = mergeGeometries(list, false);
    for (const g of list) g.dispose();
    if (!merged) continue;
    const m = mapMesh(scene, k + nc, merged);
    if (k === 'water' || k === 'poolwater') m.renderOrder = 2;
    scene.add(m);
    mapMeshes.push(m);
    if (key !== k + nc) { merged.computeBoundingSphere(); chunkMeshes.push(m); }
  }
  buildLiquids(scene, liq, all, def, hazify);
}

// chunks entirely past the end of the fog are pure fog colour anyway: skip them (needs a sky the colour of the fog)
const camFwd = new THREE.Vector3(), toChunk = new THREE.Vector3();
function cullChunks() {
  if (!chunkMeshes.length) return;
  const cam = G.camera, far = G.scene.fog.far + 2;
  cam.getWorldDirection(camFwd);
  for (const m of chunkMeshes) {
    const s = m.geometry.boundingSphere;
    m.visible = toChunk.subVectors(s.center, cam.position).dot(camFwd) - s.radius < far; // fog goes by view depth, not distance
  }
}

// per-map light: the backrooms is lit by fluorescent tubes from everywhere, not by the sun
let defLight = null;
function mapLight(map) {
  const hemi = G.scene.children.find((o) => o.isHemisphereLight), sun = G.scene.children.find((o) => o.isDirectionalLight);
  if (!hemi || !sun) return;
  if (!defLight) defLight = { hemi: [hemi.color.getHex(), hemi.groundColor.getHex(), hemi.intensity], sun: [sun.color.getHex(), sun.intensity] };
  const L = (map && map.light) || defLight;
  hemi.color.setHex(L.hemi[0]); hemi.groundColor.setHex(L.hemi[1]); hemi.intensity = L.hemi[2];
  sun.color.setHex(L.sun[0]); sun.intensity = L.sun[1];
}

let skyGeo, voidMesh;
let skyStuff = []; // sun, clouds, void rocks: switched off on sealed maps (map.sealed), where nobody could ever see them
const voidRocks = []; // and the floating rocks only belong over a void: maps with a real floor (map.floorY) hide them
function paintSky(sky) {
  const top = new THREE.Color(sky.top), mid = new THREE.Color(sky.mid), bot = new THREE.Color(sky.bot);
  const pos = skyGeo.attributes.position, c = new THREE.Color(), cols = [];
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) / 900;
    if (y > 0) c.copy(mid).lerp(top, Math.min(1, y * 1.6)); else c.copy(mid).lerp(bot, Math.min(1, -y * 2.5));
    cols.push(c.r, c.g, c.b);
  }
  skyGeo.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
}
function buildSky(scene) {
  skyGeo = new THREE.SphereGeometry(900, 10, 8);
  paintSky(MAP.sky);
  scene.add(new THREE.Mesh(skyGeo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false })));

  sun = new THREE.Mesh(new THREE.BoxGeometry(40, 40, 40), new THREE.MeshBasicMaterial({ color: 0xffe14d, fog: false }));
  sun.position.set(300, 220, -420);
  scene.add(sun);

  const cloudMat = jankify(new THREE.MeshLambertMaterial({ color: 0xffffff, emissive: 0x996688 }));
  for (let i = 0; i < 28; i++) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(10 + Math.random() * 25, 3 + Math.random() * 4, 8 + Math.random() * 16), cloudMat);
    m.position.set((Math.random() - 0.5) * 600, 75 + Math.random() * 50, (Math.random() - 0.5) * 600);
    m.userData.speed = 1 + Math.random() * 3;
    scene.add(m);
    clouds.push(m);
  }

  // the void
  const voidMat = new THREE.MeshBasicMaterial({ color: 0x2a0018 });
  voidMesh = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000).rotateX(-Math.PI / 2), voidMat);
  voidMesh.position.y = MAP.killY - 25;
  scene.add(voidMesh);
  // floating rocks for ambiance
  const rockMat = jankify(new THREE.MeshLambertMaterial({ color: 0x6b4a3a, flatShading: true }));
  for (let i = 0; i < 40; i++) {
    const r = new THREE.Mesh(new THREE.IcosahedronGeometry(1 + Math.random() * 3, 0), rockMat);
    const a = Math.random() * Math.PI * 2, d = 40 + Math.random() * 140;
    r.position.set(Math.cos(a) * d, -25 - Math.random() * 30, Math.sin(a) * d);
    r.rotation.set(Math.random() * 3, Math.random() * 3, 0);
    scene.add(r);
    voidRocks.push(r);
  }
}

export function initWorld(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.autoClear = false;
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0xf7a1c4, 90, 330);
  const camera = new THREE.PerspectiveCamera(95, 1, 0.1, 1500);
  camera.rotation.order = 'YXZ';
  const vmScene = new THREE.Scene();
  const vmCamera = new THREE.PerspectiveCamera(65, 1, 0.01, 10);
  Object.assign(G, { renderer, scene, camera, vmScene, vmCamera });

  scene.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.6));
  const sunLight = new THREE.DirectionalLight(0xfff0dd, 1.8);
  sunLight.position.set(0.6, 1, -0.7);
  scene.add(sunLight);
  vmScene.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8));
  const vmSun = new THREE.DirectionalLight(0xffffff, 1.5);
  vmSun.position.set(0.5, 1, 0.8);
  vmScene.add(vmSun);

  const n0 = scene.children.length;
  buildSky(scene);
  skyStuff = scene.children.slice(n0).filter((o) => o !== voidMesh && o.geometry !== skyGeo);
  initLighting(sunLight, vmSun, scene.children.slice(n0)); // sky, sun cube, clouds, void, rocks: never in the shadows
  setLightPreset(G.settings ? G.settings.jank : 1);
  buildMap(scene);
  addEventListener('resize', resize);
  resize();
  initGfxGuard(canvas, { repaint: repaintMapTextures, relight: relightMap, mats: mapMats, preset: () => jank.name });
}

export function setJank(i) { jank = JANK[i] || JANK[1]; resize(); setLightPreset(JANK[i] ? i : 1); setLiquidQ(JANK[i] ? i : 1); }

// OVERDUE: a streamed map (MAPS[id].stream, the story's city) runs the city streamer instead of one built mesh.
// loaded on demand, so maps without `stream` (all of PvP) never fetch it
let city = null, cityGen = 0;
function cityFor(def) {
  const gen = ++cityGen;
  if (!def || !def.stream) { if (city) { city.stopCity(); city = null; } return; }
  import('./city/ingame.js').then((m) => { if (gen !== cityGen) return; city = m; m.startCity(def, { sky: (s) => paintSky(s) }); }).catch((e) => console.error('city failed to load', e));
}

// swap the whole level (called when the server says the map changed)
export function loadMap(id) {
  setMap(id);
  cityFor(MAPS[MAP.id]);
  marbles.clear();
  resetGrid(BOXES);
  buildMap(G.scene);
  buildProps(G.scene, MAPS[MAP.id] && MAPS[MAP.id].boxes.props);
  paintSky(MAP.sky);
  G.scene.fog.color.setHex(MAP.sky.fog);
  G.scene.fog.near = MAP.fogNear;
  G.scene.fog.far = MAP.fogFar;
  const hz = MAPS[MAP.id] && MAPS[MAP.id].haze; // the city maps' haze layer (off everywhere else)
  hazeUniforms.uHaze.value.set(hz ? hz.k : 0, hz ? hz.top : 0, hz ? hz.bottom : -1, hz ? hz.dist : 100);
  if (hz) hazeUniforms.uHazeColor.value.setHex(hz.color);
  voidMesh.position.y = MAP.killY - 25;
  buildScenery(G.scene, MAPS[MAP.id], MAP.id, voidMesh);
  mapLight(MAPS[MAP.id]);
  for (const o of skyStuff) o.visible = !(MAPS[MAP.id] && MAPS[MAP.id].sealed);
  for (const o of voidRocks) o.visible = !(MAPS[MAP.id] && (MAPS[MAP.id].sealed || MAPS[MAP.id].floorY != null));
  const night = !!(MAPS[MAP.id] && MAPS[MAP.id].night); // night maps: the sun is a (cube) moon, and no pink clouds
  sun.material.color.setHex(night ? 0xdfe6ff : 0xffe14d);
  sun.scale.setScalar(night ? 0.8 : 1);
  if (night) sun.position.set(-260, 300, -420); else sun.position.set(300, 220, -420);
  for (const c of clouds) c.visible = !night && !(MAPS[MAP.id] && MAPS[MAP.id].sealed);
  liquidsMap(MAPS[MAP.id], MAP.sky, sun.position, night); // what the water reflects and glitters with
  forestMap(MAPS[MAP.id], MAP.id);
  shredMap(MAPS[MAP.id], MAT);
  lightingMap(MAPS[MAP.id], MAP.id, night, sun); // shadows, mood, the neon's lights (after everything above is in, the pit too)
}

// models finished loading after the map was built: redraw the boxes + props (no gameplay state touched)
export function refreshMapVisuals() {
  if (!MAP.id || !G.scene || !MAT) return;
  buildMap(G.scene);
  buildProps(G.scene, MAPS[MAP.id] && MAPS[MAP.id].boxes.props);
  lightingRefresh();
}

// ---- gfxguard.js hooks (the "everything renders black" safety net)
// fresh canvas textures on the map materials that are already in use (same material objects, so nothing has to be rebuilt)
export function repaintMapTextures() {
  if (!MAT) return 0;
  const fresh = makeMaterials();
  let n = 0;
  for (const [k, v] of Object.entries(fresh)) {
    const old = MAT[k];
    for (const slot of ['map', 'emissiveMap']) {
      const t = v.mat[slot];
      if (!t) continue;
      if (old && old.mat[slot] && old.mat[slot] !== t) { old.mat[slot].dispose(); old.mat[slot] = t; old.mat.needsUpdate = true; n++; } else t.dispose();
    }
    v.mat.dispose();
  }
  return n;
}
// the current map's own fog, sky light and sun again (a streamed city sets its own every frame)
export function relightMap() {
  const def = MAPS[MAP.id];
  if (!def || !G.scene || def.stream) return false;
  G.scene.fog.color.setHex(MAP.sky.fog); G.scene.fog.near = MAP.fogNear; G.scene.fog.far = MAP.fogFar;
  const hz = def.haze;
  hazeUniforms.uHaze.value.set(hz ? hz.k : 0, hz ? hz.top : 0, hz ? hz.bottom : -1, hz ? hz.dist : 100);
  mapLight(def);
  lightingMap(def, MAP.id, !!def.night, sun);
  return true;
}
export const mapMats = () => MAT;

export function resize() {
  const w = innerWidth, h = innerHeight;
  const rw = Math.max(80, Math.floor(w * jank.scale)), rh = Math.max(60, Math.floor(h * jank.scale));
  G.renderer.setSize(rw, rh, false);
  G.camera.aspect = w / h; G.camera.updateProjectionMatrix();
  G.vmCamera.aspect = w / h; G.vmCamera.updateProjectionMatrix();
  if (jank.snap) jankUniforms.uSnap.value.set((jank.snap * (w / h)) / 2, jank.snap / 2);
  else jankUniforms.uSnap.value.set(1e5, 1e5);
}

export function updateWorld(dt) {
  for (const c of clouds) {
    c.position.x += c.userData.speed * dt;
    if (c.position.x > 320) c.position.x = -320;
  }
  sun.rotation.y += dt * 0.3;
  sun.rotation.x += dt * 0.17;
  cullChunks();
  if (city) city.updateCity(dt);
  if (MAT) updateBackrooms(dt, [MAT.ceilflick.mat, MAT.ceilflick2.mat, MAT.ceilflick3.mat]);
  updateForest(dt);
  updateShredPit(dt);
  updateLiquids(dt);
  updateFlames(dt);
}

let lastT = 0;
export function renderFrame() {
  const r = G.renderer, now = performance.now();
  gfxGuard(now); // gfxguard.js: broken lights / fog / textures get put back before they're drawn
  updateLighting(Math.min(0.1, (now - (lastT || now)) / 1000)); lastT = now;
  r.clear();
  r.render(G.scene, G.camera);
  r.clearDepth();
  r.render(G.vmScene, G.vmCamera);
}
