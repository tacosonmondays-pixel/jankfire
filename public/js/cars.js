// The traffic's cars, built in code: side profiles extruded across the car (with the wheel arches cut out of them),
// greenhouses, pillars, lights, bumpers, grilles, mirrors, door seams, plates. Real proportions (a supermini, a saloon,
// a pickup, a panel van, a city bus, a box truck), then made a bit silly (the ice cream van's cone, the taxi sign).
// Every car is a handful of meshes: all the painted / plastic / glass / chrome bits merged into one vertex-coloured
// mesh, the lamps in two, a wheel each (so they spin and steer), the liveries on their own decal.
// Facing +z, origin on the ground under the middle of the car.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { CARS } from '/shared/traffic.js';

const C = (hex) => new THREE.Color(hex);
const DARK = '#1d1d22', TRIM = '#2c2c33', CHROME = '#c9ced6', GLASS = '#2e4664', GLASS_HI = '#4f6f96', PLATE = '#f4f1e4', TIRE = '#18181b';

// ------------------------------------------------------------ a little part kit
function paint(geo, hex) {
  const g = geo.index ? geo.toNonIndexed() : geo;
  const c = C(hex), n = g.attributes.position.count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[i * 3] = c.r; a[i * 3 + 1] = c.g; a[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'color') g.deleteAttribute(k);
  return g;
}
class Kit {
  constructor() { this.parts = []; this.lamps = []; this.tails = []; this.inds = []; this.decals = []; }
  box(sx, sy, sz, x, y, z, hex, o = {}) {
    const g = new THREE.BoxGeometry(sx, sy, sz);
    if (o.rx) g.rotateX(o.rx); if (o.ry) g.rotateY(o.ry); if (o.rz) g.rotateZ(o.rz);
    g.translate(x, y, z);
    (o.to || this.parts).push(paint(g, hex));
    return this;
  }
  // a bar from (z0, y0) to (z1, y1) at side x (pillars along a windscreen)
  bar(z0, y0, z1, y1, x, t, w, hex) {
    const l = Math.hypot(z1 - z0, y1 - y0), a = Math.atan2(y1 - y0, z1 - z0);
    return this.box(w, t, l, x, (y0 + y1) / 2, (z0 + z1) / 2, hex, { rx: -a });
  }
  // a side profile [[z, y], ...] extruded across the car, w wide, centred on x. arches: [[z, r]] cut out of the bottom
  prof(pts, w, hex, o = {}) {
    // pts run from the back bottom, over the top, to the front bottom. the bottom edge comes back front to back,
    // up and round each wheel arch (an arch of radius r round the hub, starting where it meets the sill)
    const s = new THREE.Shape();
    const bottom = o.bottom ?? Math.min(...pts.map((p) => p[1]));
    const path = pts.slice();
    if (o.arches && o.arches.length) {
      const hub = o.hub ?? bottom;
      for (const [az, r] of [...o.arches].sort((a, b) => b[0] - a[0])) {
        const t0 = bottom > hub ? Math.asin(Math.min(1, (bottom - hub) / r)) : 0;
        path.push([az + Math.cos(t0) * r, bottom]);
        for (let k = 0; k <= 8; k++) { const t = t0 + (k / 8) * (Math.PI - 2 * t0); path.push([az + Math.cos(t) * r, hub + Math.sin(t) * r]); }
        path.push([az - Math.cos(t0) * r, bottom]);
      }
    }
    s.moveTo(path[0][0], path[0][1]);
    for (let i = 1; i < path.length; i++) s.lineTo(path[i][0], path[i][1]);
    s.closePath();
    const bev = o.bev ?? 0.045;
    const g = new THREE.ExtrudeGeometry(s, { depth: Math.max(0.01, w - bev * 2), bevelEnabled: bev > 0, bevelThickness: bev, bevelSize: bev, bevelSegments: 1, bevelOffset: -bev, curveSegments: 1 }); // (the chamfer stays inside the outline)
    g.rotateY(-Math.PI / 2); // shape x -> car z, extrusion -> -x
    g.translate((w - bev * 2) / 2 + (o.x || 0), 0, 0);
    (o.to || this.parts).push(paint(g, hex));
    return this;
  }
  cyl(r0, r1, h, seg, x, y, z, hex, o = {}) {
    const g = new THREE.CylinderGeometry(r0, r1, h, seg, 1, false, o.t0 || 0, o.tl || Math.PI * 2);
    if (o.rx) g.rotateX(o.rx); if (o.rz) g.rotateZ(o.rz); if (o.ry) g.rotateY(o.ry);
    g.translate(x, y, z);
    (o.to || this.parts).push(paint(g, hex));
    return this;
  }
  lamp(sx, sy, sz, x, y, z, hex = '#fff6d8') { return this.box(sx, sy, sz, x, y, z, hex, { to: this.lamps }); }
  tail(sx, sy, sz, x, y, z) { return this.box(sx, sy, sz, x, y, z, '#ffffff', { to: this.tails }); }
  ind(sx, sy, sz, x, y, z) { return this.box(sx, sy, sz, x, y, z, '#ffffff', { to: this.inds }); }
  // both sides at once: fn(sign) for x = +/-
  both(fn) { fn(1); fn(-1); return this; }
}

// ------------------------------------------------------------ wheels: tyre, rim, five spokes (so you can see them turn)
const wheelCache = new Map();
function wheelGeo(r, w, dual) {
  const k = `${r}|${w}|${dual}`;
  if (wheelCache.has(k)) return wheelCache.get(k);
  const parts = [];
  const add = (g, hex) => parts.push(paint(g, hex));
  const tyre = (dx) => {
    add(new THREE.CylinderGeometry(r, r, w, 14).rotateZ(Math.PI / 2).translate(dx, 0, 0), TIRE);
    add(new THREE.CylinderGeometry(r * 0.93, r * 0.93, w + 0.02, 14).rotateZ(Math.PI / 2).translate(dx, 0, 0), '#232327'); // sidewall
  };
  tyre(0); if (dual) tyre(-w - 0.03);
  const face = w / 2 + 0.012;
  add(new THREE.CylinderGeometry(r * 0.62, r * 0.62, 0.03, 10).rotateZ(Math.PI / 2).translate(face, 0, 0), '#9aa0aa'); // rim
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    add(new THREE.BoxGeometry(0.03, r * 1.05, r * 0.16).rotateX(a).translate(face + 0.016, 0, 0), '#d8dce4');
  }
  add(new THREE.CylinderGeometry(r * 0.18, r * 0.2, 0.05, 8).rotateZ(Math.PI / 2).translate(face + 0.03, 0, 0), '#e8ecf2'); // hub cap
  for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2 + 0.6; add(new THREE.BoxGeometry(0.03, 0.04, 0.04).translate(face + 0.03, Math.cos(a) * r * 0.32, Math.sin(a) * r * 0.32), '#55585e'); } // nuts
  const g = mergeGeometries(parts);
  wheelCache.set(k, g);
  return g;
}

// ------------------------------------------------------------ text decals (liveries, signs, plates)
const texCache = new Map();
function label(key, w, h, draw) {
  if (texCache.has(key)) return texCache.get(key);
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  texCache.set(key, t);
  return t;
}
const FONT = (px, b = 'bold') => `${b} ${px}px "Comic Neue", "Comic Sans MS", sans-serif`;
function outlined(g, text, x, y, px, fill, stroke = '#111', lw = 6) { g.font = FONT(px); g.lineJoin = 'round'; g.lineWidth = lw; g.strokeStyle = stroke; g.strokeText(text, x, y); g.fillStyle = fill; g.fillText(text, x, y); }
const LIVERY = {
  taxi: () => label('taxi', 256, 64, (g, w, h) => { g.fillStyle = '#ffd21a'; g.fillRect(0, 0, w, h); for (let i = 0; i < 16; i++) for (let j = 0; j < 2; j++) { g.fillStyle = (i + j) % 2 ? '#111' : '#ffd21a'; g.fillRect(i * 16, 22 + j * 10, 16, 10); } }),
  taxisign: () => label('taxisign', 128, 48, (g, w, h) => { g.fillStyle = '#fff6c8'; g.fillRect(0, 0, w, h); g.textAlign = 'center'; g.textBaseline = 'middle'; outlined(g, 'TAXI?', w / 2, h / 2 + 2, 36, '#1a1a1a', '#fff6c8', 0); }),
  cola: () => label('cola', 512, 160, (g, w, h) => {
    g.fillStyle = '#ff2fa8'; g.fillRect(0, 0, w, h); g.fillStyle = '#ffe14d'; g.beginPath(); g.moveTo(0, h); g.lineTo(w * 0.45, h); g.quadraticCurveTo(w * 0.6, h * 0.35, w, h * 0.55); g.lineTo(w, h); g.fill();
    g.textAlign = 'left'; g.textBaseline = 'middle'; outlined(g, 'JANK COLA', 26, 58, 74, '#ffffff', '#3a0030', 10);
    g.font = FONT(26); g.fillStyle = '#3a0030'; g.fillText('now with 40% more fizz (legally)', 30, 126);
    g.fillStyle = '#4fd8ff'; g.fillRect(w - 70, 22, 34, 96); g.fillStyle = '#ffffff'; g.fillRect(w - 64, 30, 8, 80); // a bottle
  }),
  plumb: () => label('plumb', 512, 160, (g, w, h) => { g.fillStyle = '#f2f2ee'; g.fillRect(0, 0, w, h); g.fillStyle = '#2f6fe0'; g.fillRect(0, h - 34, w, 34); g.textAlign = 'left'; g.textBaseline = 'middle'; outlined(g, 'PLUMBING', 24, 56, 70, '#2f6fe0', '#f2f2ee', 0); g.font = FONT(30); g.fillStyle = '#26262c'; g.fillText('(probably)  ·  we fix leaks we caused', 26, 108); }),
  moving: () => label('moving', 512, 160, (g, w, h) => { g.fillStyle = '#e86a22'; g.fillRect(0, 0, w, h); g.textAlign = 'left'; g.textBaseline = 'middle'; outlined(g, 'MOVING DAY', 22, 60, 66, '#ffffff', '#5a2208', 8); g.font = FONT(28); g.fillStyle = '#ffffff'; g.fillText('your couch, our problem', 26, 120); }),
  hotdog: () => label('hotdog', 512, 160, (g, w, h) => { g.fillStyle = '#ffe14d'; g.fillRect(0, 0, w, h); g.textAlign = 'left'; g.textBaseline = 'middle'; outlined(g, 'HOT DOGS?', 22, 64, 76, '#e8323c', '#5a1010', 8); g.font = FONT(28); g.fillStyle = '#5a1010'; g.fillText("don't ask what's in them", 28, 126); }),
  icecream: () => label('icecream', 512, 160, (g, w, h) => {
    g.fillStyle = '#bff5e4'; g.fillRect(0, 0, w, h); for (let i = 0; i < 9; i++) { g.fillStyle = i % 2 ? '#ff9ad5' : '#ffffff'; g.fillRect(i * 58, 0, 58, 22); }
    g.textAlign = 'left'; g.textBaseline = 'middle'; outlined(g, 'ICE SCREAM', 22, 76, 70, '#ff4fd8', '#5a1040', 9); g.font = FONT(26); g.fillStyle = '#5a1040'; g.fillText('one flavour. it is pink.', 28, 132);
  }),
  bus: () => label('bus', 1024, 128, (g, w, h) => { g.clearRect(0, 0, w, h); g.textAlign = 'left'; g.textBaseline = 'middle'; outlined(g, 'JANK TRANSIT', 30, 64, 78, '#ffffff', '#1a1a1a', 10); g.font = FONT(36); g.fillStyle = '#1a1a1a'; g.fillText('we go places. eventually.', 560, 70); }),
  dest: () => label('dest', 256, 48, (g, w, h) => { g.fillStyle = '#111'; g.fillRect(0, 0, w, h); g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = FONT(30); g.fillStyle = '#ffae1a'; g.fillText('NOT IN SERVICE', w / 2, h / 2 + 2); }),
  plate: () => label('plate', 128, 32, (g, w, h) => { g.fillStyle = '#f4f1e4'; g.fillRect(0, 0, w, h); g.strokeStyle = '#333'; g.lineWidth = 3; g.strokeRect(2, 2, w - 4, h - 4); g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = 'bold 22px monospace'; g.fillStyle = '#1a1a3a'; g.fillText('JNK 420', w / 2, h / 2 + 1); }),
};
function decal(k, tex, w, h, x, y, z, ry) { // a flat sign on the body: w x h metres, facing ry
  const g = new THREE.PlaneGeometry(w, h);
  if (ry) g.rotateY(ry);
  g.translate(x, y, z);
  k.decals.push({ g, tex });
}

// ------------------------------------------------------------ the models
// each returns { kit, wheels: [{ x, y, z, r, w, front, dual }], wb, lamps: [[x, y, z]] (headlight spots for the beams) }
function sedan(col, taxi) {
  const k = new Kit(), T = CARS.sedan, W = T.W, hw = W / 2, F = 1.42, B = -1.33, R = 0.335;
  const arches = [[F, 0.4], [B, 0.4]];
  k.prof([[-2.3, 0.3], [-2.36, 0.5], [-2.34, 0.84], [-2.14, 0.95], [-1.32, 0.98], [1.3, 0.98], [2.16, 0.86], [2.34, 0.72], [2.37, 0.5], [2.31, 0.3]], W, col, { arches, hub: R });
  k.prof([[-1.31, 0.96], [-0.82, 1.39], [0.44, 1.41], [1.27, 0.96]], W - 0.22, GLASS, { bev: 0.02 }); // greenhouse
  k.prof([[-0.86, 1.36], [-0.8, 1.44], [0.46, 1.46], [0.52, 1.38]], W - 0.18, col, { bev: 0.03 }); // roof
  k.both((s) => {
    const x = s * (hw - 0.115);
    k.bar(1.27, 0.97, 0.47, 1.41, x, 0.07, 0.09, col); k.bar(-1.31, 0.97, -0.83, 1.39, x, 0.12, 0.1, col); // A + C pillars
    k.box(0.09, 0.44, 0.1, x, 1.18, -0.16, col); // B pillar
    k.box(0.01, 0.6, 0.012, s * (hw + 0.005), 0.65, 1.0, DARK).box(0.01, 0.6, 0.012, s * (hw + 0.005), 0.65, -0.16, DARK).box(0.01, 0.55, 0.012, s * (hw + 0.005), 0.67, -1.2, DARK); // door seams
    k.box(0.03, 0.04, 0.16, s * (hw + 0.01), 0.86, 0.15, CHROME).box(0.03, 0.04, 0.16, s * (hw + 0.01), 0.86, -0.98, CHROME); // handles
    k.box(0.16, 0.12, 0.1, s * (hw + 0.07), 1.04, 1.12, col).box(0.02, 0.09, 0.08, s * (hw + 0.15), 1.04, 1.12, GLASS_HI); // mirror
    k.box(0.02, 0.08, 4.1, s * (hw + 0.01), 0.34, 0, TRIM); // sill
    k.lamp(0.42, 0.12, 0.05, s * 0.58, 0.72, 2.355); k.tail(0.36, 0.13, 0.04, s * 0.6, 0.79, -2.355); k.ind(0.12, 0.08, 0.04, s * 0.85, 0.6, 2.35);
    k.ind(0.1, 0.07, 0.04, s * 0.82, 0.67, -2.34);
    k.box(0.36, 0.22, 0.3, s * 0.79, 0.65, F, DARK); k.box(0.36, 0.22, 0.3, s * 0.79, 0.65, B, DARK); // wheel tubs
  });
  k.box(0.78, 0.15, 0.04, 0, 0.62, 2.365, DARK).box(0.8, 0.025, 0.05, 0, 0.66, 2.37, CHROME); // grille
  k.box(W + 0.02, 0.18, 0.14, 0, 0.4, 2.31, TRIM).box(W + 0.02, 0.18, 0.14, 0, 0.42, -2.29, TRIM); // bumpers
  k.box(0.5, 0.11, 0.02, 0, 0.42, 2.39, PLATE).box(0.5, 0.11, 0.02, 0, 0.62, -2.36, PLATE);
  k.cyl(0.04, 0.04, 0.2, 6, -0.5, 0.3, -2.33, '#777', { rx: Math.PI / 2 }); // exhaust
  if (taxi) {
    k.box(0.62, 0.2, 0.28, 0, 1.56, -0.1, '#fff6c8'); decal(k, LIVERY.taxisign(), 0.58, 0.18, 0, 1.56, 0.045); decal(k, LIVERY.taxisign(), 0.58, 0.18, 0, 1.56, -0.245, Math.PI);
    k.both((s) => decal(k, LIVERY.taxi(), 2.6, 0.32, s * (hw + 0.012), 0.66, -0.1, s * Math.PI / 2));
  }
  return { kit: k, wheels: wheels4(F, B, R, 0.22, hw - 0.14), wb: F - B, lamps: [[0.58, 0.72, 2.36], [-0.58, 0.72, 2.36]] };
}
function hatch(col) {
  const k = new Kit(), T = CARS.hatch, W = T.W, hw = W / 2, F = 1.2, B = -1.3, R = 0.31;
  k.prof([[-1.92, 0.3], [-1.98, 0.5], [-1.96, 0.96], [1.04, 0.97], [1.8, 0.84], [1.97, 0.68], [1.98, 0.47], [1.92, 0.3]], W, col, { arches: [[F, 0.37], [B, 0.37]], hub: R });
  k.prof([[-1.93, 0.95], [-1.62, 1.42], [0.2, 1.46], [1.03, 0.96]], W - 0.22, GLASS, { bev: 0.02 });
  k.prof([[-1.68, 1.4], [-1.62, 1.49], [0.22, 1.51], [0.28, 1.43]], W - 0.16, col, { bev: 0.03 });
  k.box(W - 0.3, 0.06, 0.26, 0, 1.47, -1.7, col, { rx: -0.25 }); // little spoiler
  k.both((s) => {
    const x = s * (hw - 0.115);
    k.bar(1.03, 0.97, 0.22, 1.46, x, 0.07, 0.09, col); k.bar(-1.94, 0.97, -1.63, 1.42, x, 0.18, 0.1, col);
    k.box(0.09, 0.45, 0.1, x, 1.19, -0.5, col);
    k.box(0.01, 0.6, 0.012, s * (hw + 0.005), 0.65, 0.98, DARK).box(0.01, 0.6, 0.012, s * (hw + 0.005), 0.65, -0.52, DARK);
    k.box(0.03, 0.04, 0.15, s * (hw + 0.01), 0.86, -0.3, CHROME);
    k.box(0.15, 0.12, 0.1, s * (hw + 0.07), 1.04, 0.92, col).box(0.02, 0.09, 0.08, s * (hw + 0.14), 1.04, 0.92, GLASS_HI);
    k.box(0.02, 0.08, 3.3, s * (hw + 0.01), 0.34, -0.05, TRIM);
    k.lamp(0.36, 0.14, 0.05, s * 0.56, 0.7, 1.965); k.tail(0.16, 0.3, 0.04, s * 0.74, 0.86, -1.975); k.ind(0.1, 0.08, 0.04, s * 0.8, 0.58, 1.96); k.ind(0.12, 0.06, 0.04, s * 0.74, 0.66, -1.97);
    k.box(0.34, 0.2, 0.3, s * 0.72, 0.62, F, DARK); k.box(0.34, 0.2, 0.3, s * 0.72, 0.62, B, DARK);
  });
  k.box(0.7, 0.14, 0.04, 0, 0.58, 1.98, DARK).box(W + 0.02, 0.17, 0.13, 0, 0.39, 1.92, TRIM).box(W + 0.02, 0.17, 0.13, 0, 0.41, -1.92, TRIM);
  k.box(0.44, 0.1, 0.02, 0, 0.41, 2.0, PLATE).box(0.44, 0.1, 0.02, 0, 0.66, -1.98, PLATE);
  return { kit: k, wheels: wheels4(F, B, R, 0.2, hw - 0.13), wb: F - B, lamps: [[0.56, 0.7, 1.97], [-0.56, 0.7, 1.97]] };
}
function pickup(col, cargo) {
  const k = new Kit(), T = CARS.pickup, W = T.W, hw = W / 2, F = 1.78, B = -1.55, R = 0.39, y0 = 0.46;
  k.prof([[-0.56, y0], [-0.56, 1.13], [1.12, 1.17], [2.55, 1.11], [2.7, 0.96], [2.73, 0.62], [2.66, y0]], W, col, { arches: [[F, 0.46]], hub: R, bottom: y0 }); // cab + hood
  k.prof([[-0.5, 1.11], [-0.48, 1.78], [0.52, 1.82], [1.12, 1.14]], W - 0.24, GLASS, { bev: 0.02 });
  k.prof([[-0.53, 1.75], [-0.5, 1.88], [0.54, 1.9], [0.6, 1.8]], W - 0.18, col, { bev: 0.03 });
  k.both((s) => {
    const x = s * (hw - 0.12);
    k.bar(1.12, 1.15, 0.56, 1.82, x, 0.08, 0.1, col); k.box(0.1, 0.68, 0.14, x, 1.45, -0.48, col); k.box(0.09, 0.66, 0.1, x, 1.45, 0.2, col);
    // the bed sides, arch cut round the back wheel
    k.prof([[-2.7, y0], [-2.7, 1.14], [-0.62, 1.14], [-0.62, y0]], 0.09, col, { arches: [[B, 0.46]], hub: R, bottom: y0, x: s * (hw - 0.045), bev: 0.02 });
    k.box(0.12, 0.06, 2.1, s * (hw - 0.04), 1.16, -1.66, TRIM); // bed rail cap
    k.box(0.01, 0.62, 0.012, s * (hw + 0.005), 0.82, 0.24, DARK);
    k.box(0.03, 0.05, 0.18, s * (hw + 0.01), 1.04, 0.0, CHROME);
    k.box(0.18, 0.2, 0.08, s * (hw + 0.1), 1.25, 1.02, DARK);
    k.box(0.1, 0.2, 2.4, s * (hw - 0.05), 0.4, 0.1, '#3a3a40'); // step
    k.lamp(0.36, 0.2, 0.05, s * 0.66, 0.92, 2.72); k.tail(0.12, 0.42, 0.05, s * (hw - 0.08), 0.92, -2.72); k.ind(0.12, 0.1, 0.05, s * 0.88, 0.76, 2.71); k.ind(0.1, 0.1, 0.05, s * (hw - 0.08), 0.62, -2.72);
    k.box(0.5, 0.18, 0.95, s * 0.6, 0.88, B, DARK); // tubs in the bed
    k.box(0.4, 0.26, 0.36, s * 0.78, 0.82, F, DARK);
  });
  k.box(W - 0.14, 0.06, 2.06, 0, 0.78, -1.66, '#3a3a40'); // bed floor
  k.box(W - 0.06, 0.6, 0.08, 0, 0.84, -2.66, col).box(W * 0.5, 0.05, 0.02, 0, 0.98, -2.71, CHROME); // tailgate
  k.box(0.96, 0.32, 0.05, 0, 0.84, 2.73, CHROME).box(0.86, 0.24, 0.06, 0, 0.84, 2.735, DARK);
  for (let i = 0; i < 3; i++) k.box(0.84, 0.03, 0.07, 0, 0.75 + i * 0.09, 2.74, CHROME); // grille bars
  k.box(W + 0.06, 0.22, 0.18, 0, 0.55, 2.68, CHROME).box(W + 0.04, 0.2, 0.16, 0, 0.56, -2.7, '#3a3a40');
  k.box(0.5, 0.11, 0.02, 0, 0.56, 2.78, PLATE).box(0.5, 0.11, 0.02, 0, 0.7, -2.715, PLATE);
  k.box(0.12, 0.08, 0.3, 0, 0.42, -2.88, '#555'); // hitch
  if (cargo === 1) { k.box(0.8, 0.6, 0.7, -0.3, 1.11, -1.2, '#b0804a').box(0.6, 0.5, 0.6, 0.4, 1.06, -2.0, '#c08f55').box(0.5, 0.3, 0.5, -0.35, 1.56, -1.25, '#a87240'); }
  if (cargo === 2) { k.box(1.5, 0.28, 1.9, 0, 0.95, -1.7, '#ff9ad5', { rz: 0.08 }).box(1.4, 0.04, 1.8, 0, 1.11, -1.7, '#ffffff', { rz: 0.08 }); } // somebody's mattress
  return { kit: k, wheels: wheels4(F, B, R, 0.28, hw - 0.16), wb: F - B, lamps: [[0.66, 0.92, 2.73], [-0.66, 0.92, 2.73]] };
}
function van(col, liv, ice) {
  const T = ice ? CARS.icecream : CARS.van, k = new Kit(), W = T.W, hw = W / 2, F = 1.68, B = -1.55, R = 0.36, top = ice ? 2.56 : 2.38, half = T.L / 2;
  k.prof([[-half + 0.04, 0.36], [-half, 2.26], [-half + 0.1, top], [1.02, top], [1.86, 1.24], [half - 0.05, 1.04], [half, 0.78], [half - 0.04, 0.36]], W, col, { arches: [[F, 0.43], [B, 0.43]], hub: R });
  k.prof([[1.06, top - 0.07], [1.83, 1.27], [1.88, 1.31], [1.1, top - 0.02]], W - 0.18, GLASS, { bev: 0.015 }); // windscreen
  k.both((s) => {
    k.prof([[0.95, 1.3], [0.95, 2.1], [1.08, 2.18], [1.7, 1.38], [1.7, 1.3]], 0.02, GLASS, { x: s * (hw + 0.006), bev: 0 }); // cab side window
    k.box(0.012, 1.7, 0.014, s * (hw + 0.006), 1.25, 0.88, DARK).box(0.012, 1.55, 0.014, s * (hw + 0.006), 1.2, -0.95, DARK); // sliding door seams
    k.box(0.012, 0.02, 1.85, s * (hw + 0.006), 2.06, -0.03, DARK);
    k.box(0.03, 0.05, 0.2, s * (hw + 0.01), 1.2, 0.68, CHROME);
    k.box(0.2, 0.3, 0.08, s * (hw + 0.1), 1.72, 1.55, DARK);
    k.box(0.02, 0.1, 4.6, s * (hw + 0.01), 0.4, 0, TRIM);
    k.lamp(0.34, 0.18, 0.05, s * 0.64, 0.98, half - 0.03); k.tail(0.14, 0.5, 0.05, s * (hw - 0.09), 1.0, -half - 0.01); k.ind(0.12, 0.1, 0.05, s * 0.88, 0.84, half - 0.04); k.ind(0.12, 0.12, 0.05, s * (hw - 0.09), 0.66, -half - 0.01);
    k.box(0.38, 0.24, 0.34, s * 0.76, 0.66, F, DARK); k.box(0.38, 0.24, 0.34, s * 0.76, 0.66, B, DARK);
    if (liv && !ice) decal(k, liv, 2.6, 0.8, s * (hw + 0.014), 1.55, -1.05, s * Math.PI / 2);
  });
  k.box(0.012, 1.9, 0.02, 0, 1.3, -half - 0.012, DARK).box(0.03, 0.05, 0.16, 0.1, 1.2, -half - 0.02, CHROME); // rear doors
  k.both((s) => k.box(0.72, 0.55, 0.02, s * 0.44, 1.85, -half - 0.012, GLASS));
  k.box(0.9, 0.2, 0.04, 0, 0.82, half + 0.005, DARK).box(W + 0.02, 0.2, 0.15, 0, 0.47, half - 0.04, TRIM).box(W + 0.02, 0.2, 0.15, 0, 0.47, -half + 0.03, TRIM);
  k.box(0.5, 0.11, 0.02, 0, 0.47, half + 0.04, PLATE).box(0.5, 0.11, 0.02, 0, 0.72, -half - 0.02, PLATE);
  if (ice) {
    k.box(0.02, 0.9, 1.9, hw + 0.012, 1.55, -0.9, '#3a2030'); // the serving hatch (curb side)
    k.box(0.5, 0.05, 2.1, hw + 0.25, 2.06, -0.9, '#ff9ad5', { rz: -0.35 }); k.box(0.22, 0.06, 2.0, hw + 0.08, 1.12, -0.9, '#ffffff'); // awning + counter
    for (let i = 0; i < 5; i++) k.box(0.52, 0.055, 0.2, hw + 0.25, 2.09, -1.8 + i * 0.45, '#ffffff', { rz: -0.35 });
    // a cone the size of a child on the roof, and a speaker for the song
    k.cyl(0.42, 0.06, 1.1, 10, 0, top + 0.6, -0.6, '#d8a050'); k.cyl(0.44, 0.44, 0.08, 10, 0, top + 1.15, -0.6, '#c08a3a');
    k.box(0.72, 0.5, 0.72, 0, top + 1.42, -0.6, '#ff9ad5').box(0.56, 0.36, 0.56, 0, top + 1.72, -0.6, '#ffc2e6').box(0.16, 0.16, 0.16, 0.05, top + 1.98, -0.6, '#e8323c');
    k.cyl(0.18, 0.08, 0.3, 8, 0, top + 0.16, 0.6, '#c9ced6', { rx: Math.PI / 2 });
    decal(k, LIVERY.icecream(), 1.6, 0.5, hw + 0.016, 2.27, -0.9, Math.PI / 2); decal(k, LIVERY.icecream(), 2.6, 0.81, -hw - 0.016, 1.6, -0.9, -Math.PI / 2);
  }
  return { kit: k, wheels: wheels4(F, B, R, 0.24, hw - 0.15), wb: F - B, lamps: [[0.64, 0.98, half], [-0.64, 0.98, half]] };
}
function bus(col) {
  const k = new Kit(), T = CARS.bus, W = T.W, hw = W / 2, F = 3.55, B = -2.45, R = 0.5, half = T.L / 2;
  k.prof([[-half, 0.42], [-half, 3.08], [-half + 0.14, 3.24], [half - 0.18, 3.24], [half - 0.02, 3.06], [half, 0.42]], W, col, { arches: [[F, 0.58], [B, 0.6]], hub: R });
  k.box(W + 0.02, 0.2, T.L - 0.2, 0, 0.66, 0, '#ffffff').box(W + 0.03, 0.07, T.L - 0.3, 0, 0.8, 0, '#ff4fd8'); // a stripe
  k.both((s) => {
    // the window band: glass with pillars, the curb side (+x) has two doors
    k.box(0.02, 1.15, T.L - 1.0, s * (hw + 0.006), 2.2, -0.2, GLASS);
    for (let z = -half + 0.4; z < half - 1.2; z += 1.12) k.box(0.03, 1.18, 0.1, s * (hw + 0.012), 2.2, z, col);
    k.box(0.02, 0.06, T.L - 0.8, s * (hw + 0.012), 2.8, -0.2, DARK);
    k.box(0.3, 0.4, 0.1, s * (hw + 0.14), 2.6, half - 0.1, DARK); // mirrors on stalks
    k.box(0.02, 0.12, T.L - 0.4, s * (hw + 0.012), 0.5, 0, TRIM);
    k.tail(0.22, 0.46, 0.05, s * (hw - 0.16), 0.95, -half - 0.01); k.ind(0.18, 0.12, 0.05, s * (hw - 0.16), 0.6, -half - 0.01); k.ind(0.18, 0.12, 0.05, s * (hw - 0.18), 0.62, half + 0.01);
    k.lamp(0.36, 0.2, 0.05, s * (hw - 0.4), 0.78, half + 0.01);
    for (const z of [F, B]) k.box(0.46, 0.4, 0.5, s * (hw - 0.4), 0.8, z, DARK);
  });
  for (const z of [4.85, -0.2]) { k.box(0.04, 2.2, 1.2, hw + 0.016, 1.55, z, '#3a4048'); k.box(0.045, 2.0, 0.5, hw + 0.02, 1.6, z - 0.28, GLASS); k.box(0.045, 2.0, 0.5, hw + 0.02, 1.6, z + 0.28, GLASS); }
  k.box(W - 0.2, 1.75, 0.03, 0, 2.06, half + 0.012, GLASS).box(W - 0.2, 0.3, 0.04, 0, 3.05, half + 0.015, '#111'); // windscreen + sign box
  decal(k, LIVERY.dest(), 1.7, 0.26, 0, 3.05, half + 0.04);
  k.box(W - 0.3, 1.0, 0.03, 0, 2.3, -half - 0.012, GLASS);
  k.box(W + 0.02, 0.3, 0.2, 0, 0.55, half + 0.02, TRIM).box(W + 0.02, 0.3, 0.2, 0, 0.55, -half - 0.02, TRIM);
  k.box(1.6, 0.34, 2.4, 0, 3.4, -2.6, '#d0d4da').box(0.5, 0.11, 0.02, 0, 0.82, -half - 0.02, PLATE);
  k.both((s) => decal(k, LIVERY.bus(), 4.4, 0.55, s * (hw + 0.05), 1.3, -3.0, s * Math.PI / 2));
  const wh = wheels4(F, B, R, 0.3, hw - 0.2); for (const w of wh) if (!w.front) w.dual = true;
  return { kit: k, wheels: wh, wb: F - B, lamps: [[hw - 0.4, 0.78, half], [-(hw - 0.4), 0.78, half]] };
}
function truck(col) {
  const k = new Kit(), T = CARS.truck, W = T.W, hw = W / 2, F = 3.15, B = -2.6, R = 0.5, half = T.L / 2;
  // cab
  k.prof([[2.5, 0.55], [2.5, 2.84], [3.7, 2.86], [4.24, 1.86], [half, 1.2], [half, 0.55]], W - 0.08, col, { arches: [[F, 0.58]], hub: R, bottom: 0.55 });
  k.prof([[3.72, 2.8], [4.2, 1.9], [4.25, 1.94], [3.77, 2.84]], W - 0.24, GLASS, { bev: 0.01 });
  k.both((s) => {
    k.prof([[2.95, 1.75], [2.95, 2.6], [3.62, 2.6], [4.0, 1.98], [4.0, 1.75]], 0.02, GLASS, { x: s * (hw - 0.03), bev: 0 });
    k.box(0.3, 0.42, 0.08, s * (hw + 0.12), 2.2, 4.0, DARK);
    k.cyl(0.32, 0.32, 1.1, 10, s * (hw - 0.4), 0.82, 0.8, '#b8bcc4', { rx: Math.PI / 2 }); // fuel tank
    k.box(0.12, 0.22, 2.0, s * (hw - 0.3), 0.85, -0.6, TRIM); // chassis rail
    k.lamp(0.38, 0.22, 0.05, s * (hw - 0.36), 0.95, half + 0.01); k.ind(0.16, 0.12, 0.05, s * (hw - 0.14), 0.95, half + 0.01);
    k.tail(0.24, 0.3, 0.05, s * (hw - 0.2), 0.8, -half - 0.02); k.ind(0.18, 0.12, 0.05, s * (hw - 0.2), 0.56, -half - 0.02);
    k.box(0.44, 0.44, 0.5, s * (hw - 0.36), 0.9, F, DARK);
    decal(k, LIVERY.cola(), 6.2, 1.9, s * (hw + 0.02), 2.4, -1.0, s * Math.PI / 2);
  });
  k.box(1.6, 0.4, 0.05, 0, 1.0, half + 0.01, DARK); for (let i = 0; i < 4; i++) k.box(1.5, 0.04, 0.06, 0, 0.85 + i * 0.1, half + 0.02, CHROME);
  k.box(W - 0.02, 0.32, 0.22, 0, 0.62, half, TRIM).box(0.5, 0.11, 0.02, 0, 0.62, half + 0.12, PLATE);
  // the box: ribbed roller door at the back, under-run bar
  k.box(W, 2.75, 6.7, 0, 2.47, -1.05, '#f4f4f0').box(W + 0.03, 0.12, 6.72, 0, 3.8, -1.05, '#d0d4da').box(W + 0.03, 0.12, 6.72, 0, 1.12, -1.05, '#c0c4ca');
  for (let i = 0; i < 9; i++) k.box(W - 0.2, 0.04, 0.03, 0, 1.3 + i * 0.28, -4.41, '#c8ccd2');
  k.box(W - 0.2, 0.12, 0.12, 0, 0.62, -4.45, '#c8a020');
  k.box(0.9, 0.16, 6.6, 0, 0.9, -1.05, '#2a2a30');
  const wh = wheels4(F, B, R, 0.3, hw - 0.22); for (const w of wh) if (!w.front) w.dual = true;
  return { kit: k, wheels: wh, wb: F - B, lamps: [[hw - 0.36, 0.95, half], [-(hw - 0.36), 0.95, half]] };
}
function wheels4(F, B, r, w, x) { return [[F, 1, 1], [F, -1, 1], [B, 1, 0], [B, -1, 0]].map(([z, s, f]) => ({ x: s * x, y: r, z, r, w, side: s, front: !!f })); }

const VANS = ['plumb', 'moving', 'hotdog', 'cola'];
const BUS_COLS = ['#ffc21a', '#2fb8b0', '#e8323c', '#f2f2ee'];
function design(ty, col, ci) {
  if (ty === 'sedan') return sedan(col, false);
  if (ty === 'taxi') return sedan('#ffd21a', true);
  if (ty === 'hatch') return hatch(col);
  if (ty === 'pickup') return pickup(col, ci % 3);
  if (ty === 'van') return van(VANS[ci % 4] === 'plumb' ? '#f2f2ee' : VANS[ci % 4] === 'moving' ? '#e86a22' : VANS[ci % 4] === 'hotdog' ? '#ffe14d' : '#ff2fa8', LIVERY[VANS[ci % 4]](), false);
  if (ty === 'icecream') return van('#bff5e4', null, true);
  if (ty === 'bus') return bus(BUS_COLS[ci % 4]);
  return truck(col);
}

// ------------------------------------------------------------ materials (one set for every car) and the build cache
export const carMats = {};
export function initCarMats(patch) {
  const lam = (o) => patch(new THREE.MeshLambertMaterial({ flatShading: true, ...o }));
  carMats.body = lam({ vertexColors: true });
  carMats.wreck = lam({ color: 0x2a2420, emissive: 0x1a0800 });
  carMats.wheel = lam({ vertexColors: true });
  carMats.lamp = new THREE.MeshBasicMaterial({ vertexColors: true, color: 0xfff6d8 });
  carMats.lampOff = lam({ color: 0x8a8a7a });
  carMats.tail = new THREE.MeshBasicMaterial({ color: 0x9a1010 });
  carMats.tailOn = new THREE.MeshBasicMaterial({ color: 0xff2a20 });
  carMats.ind = new THREE.MeshBasicMaterial({ color: 0x8a5010 });
  carMats.indOn = new THREE.MeshBasicMaterial({ color: 0xffa21a });
}
const built = new Map();
function buildDesign(ty, colHex, ci) {
  const key = `${ty}|${colHex}|${ty === 'van' || ty === 'pickup' || ty === 'bus' ? ci % 12 : 0}`;
  if (built.has(key)) return built.get(key);
  const d = design(ty, colHex, ci), k = d.kit;
  const out = {
    body: mergeGeometries(k.parts), lamps: k.lamps.length ? mergeGeometries(k.lamps) : null, tails: k.tails.length ? mergeGeometries(k.tails) : null,
    inds: k.inds.length ? mergeGeometries(k.inds) : null, decals: k.decals, wheels: d.wheels, wb: d.wb, lampPos: d.lamps,
  };
  out.body.computeBoundingSphere();
  built.set(key, out);
  return out;
}
const decalMats = new Map();
function decalMat(tex, patch) {
  if (!decalMats.has(tex)) decalMats.set(tex, patch(new THREE.MeshLambertMaterial({ map: tex, transparent: true, alphaTest: 0.1 })));
  return decalMats.get(tex);
}

// a car you can put in the scene: root (position + heading), body (pitch / roll / bounce), wheels (spin, steer)
export function makeCar(ty, colHex, ci, patch) {
  const d = buildDesign(ty, colHex, ci);
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const bodyMesh = new THREE.Mesh(d.body, carMats.body);
  body.add(bodyMesh);
  const lamps = d.lamps && new THREE.Mesh(d.lamps, carMats.lamp), tails = d.tails && new THREE.Mesh(d.tails, carMats.tail), inds = d.inds && new THREE.Mesh(d.inds, carMats.ind);
  for (const m of [lamps, tails, inds]) if (m) body.add(m);
  for (const dc of d.decals) body.add(new THREE.Mesh(dc.g, decalMat(dc.tex, patch)));
  const wheels = d.wheels.map((w) => {
    const pivot = new THREE.Group(), spin = new THREE.Group();
    pivot.position.set(w.x, w.y, w.z);
    const m = new THREE.Mesh(wheelGeo(w.r, w.w, w.dual), carMats.wheel);
    if (w.side < 0) m.rotation.y = Math.PI; // the rim faces out on both sides
    if (w.dual) m.position.x = w.side * 0.0;
    spin.add(m); pivot.add(spin); root.add(pivot);
    return { pivot, spin, ...w };
  });
  return { root, body, bodyMesh, lamps, tails, inds, wheels, wb: d.wb, lampPos: d.lampPos };
}
