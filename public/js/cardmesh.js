// Card Deck: the 3D thrown card. a thin rounded slab with neon edges, the deck's back on one side and a big suit on the
// other. ONE geometry for everything and one set of materials per suit, made the first time they're asked for. built lying
// flat (face up, +y) with its long side along z, so it flies long side first
import * as THREE from 'three';
import { CARD_W, CARD_H, CARD_T, CARD_R, GLOW, SUIT_KEYS } from './cardpool.js';

const hex = (c) => '#' + c.toString(16).padStart(6, '0');
const INK = { s: '#141414', c: '#141414', h: '#e0202a', d: '#e0202a', j: '#8a3dff' };

// the suits as paths (no font needed, crisp at any size). (cx, cy) centre, s size, y down
export function suitPath(g, k, cx, cy, s) {
  g.beginPath();
  if (k === 'h') {
    g.moveTo(cx, cy + s * 0.45);
    g.bezierCurveTo(cx - s * 0.95, cy - s * 0.1, cx - s * 0.45, cy - s * 0.8, cx, cy - s * 0.28);
    g.bezierCurveTo(cx + s * 0.45, cy - s * 0.8, cx + s * 0.95, cy - s * 0.1, cx, cy + s * 0.45);
  } else if (k === 's') {
    g.moveTo(cx, cy - s * 0.52);
    g.bezierCurveTo(cx - s * 0.95, cy + s * 0.02, cx - s * 0.45, cy + s * 0.62, cx, cy + s * 0.18);
    g.bezierCurveTo(cx + s * 0.45, cy + s * 0.62, cx + s * 0.95, cy + s * 0.02, cx, cy - s * 0.52);
    g.moveTo(cx, cy + s * 0.05); g.lineTo(cx - s * 0.24, cy + s * 0.55); g.lineTo(cx + s * 0.24, cy + s * 0.55); g.closePath();
  } else if (k === 'c') {
    for (const [x, y] of [[0, -0.27], [-0.27, 0.07], [0.27, 0.07]]) { g.moveTo(cx + (x + 0.25) * s, cy + y * s); g.arc(cx + x * s, cy + y * s, s * 0.25, 0, 6.2832); }
    g.moveTo(cx + s * 0.14, cy); g.arc(cx, cy, s * 0.14, 0, 6.2832);
    g.moveTo(cx, cy); g.lineTo(cx - s * 0.22, cy + s * 0.55); g.lineTo(cx + s * 0.22, cy + s * 0.55); g.closePath();
  } else if (k === 'd') {
    g.moveTo(cx, cy - s * 0.56); g.lineTo(cx + s * 0.4, cy); g.lineTo(cx, cy + s * 0.56); g.lineTo(cx - s * 0.4, cy); g.closePath();
  } else { // joker: a star
    for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, r = (i % 2 ? 0.22 : 0.52) * s; g[i ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * r, cy + Math.sin(a) * r); }
    g.closePath();
  }
}

function canvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }
function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function tex(c) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }

// the face: cream card, a neon rim in the suit's glow, a fat suit with a hard offset comic shadow, little corner pips
function faceTex(k) {
  const [c, g] = canvas(128, 192), glow = hex(GLOW[k]);
  g.fillStyle = '#111'; g.fillRect(0, 0, 128, 192);
  rr(g, 3, 3, 122, 186, 12); g.fillStyle = '#fffaf0'; g.fill();
  rr(g, 9, 9, 110, 174, 8); g.lineWidth = 5; g.strokeStyle = glow; g.stroke();
  suitPath(g, k, 69, 101, 92); g.fillStyle = glow; g.fill(); // the comic shadow
  suitPath(g, k, 64, 96, 92); g.fillStyle = INK[k]; g.fill(); g.lineWidth = 4; g.strokeStyle = '#111'; g.stroke();
  for (const [x, y, r] of [[26, 30, 0], [102, 162, Math.PI]]) { g.save(); g.translate(x, y); g.rotate(r); suitPath(g, k, 0, 0, 24); g.fillStyle = INK[k]; g.fill(); g.restore(); }
  return tex(c);
}
// the back: the deck's hot pink with a yellow lattice and a star in the middle (one for every suit)
function backTex() {
  const [c, g] = canvas(128, 192);
  g.fillStyle = '#111'; g.fillRect(0, 0, 128, 192);
  rr(g, 3, 3, 122, 186, 12); g.fillStyle = '#fffaf0'; g.fill();
  rr(g, 10, 10, 108, 172, 6); g.fillStyle = '#ff2fc8'; g.fill();
  g.save(); rr(g, 10, 10, 108, 172, 6); g.clip();
  g.strokeStyle = '#ffe14d'; g.lineWidth = 3;
  for (let i = -200; i < 200; i += 18) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + 192, 192); g.moveTo(i + 192, 0); g.lineTo(i, 192); g.stroke(); }
  g.restore();
  rr(g, 10, 10, 108, 172, 6); g.lineWidth = 4; g.strokeStyle = '#ffe14d'; g.stroke();
  g.beginPath(); g.arc(64, 96, 30, 0, 6.2832); g.fillStyle = '#111'; g.fill(); g.lineWidth = 4; g.strokeStyle = '#ffe14d'; g.stroke();
  suitPath(g, 'j', 64, 98, 50); g.fillStyle = '#ffe14d'; g.fill();
  return tex(c);
}
// a soft round glow (one for all suits: the sprite's colour tints it)
function glowTex() {
  const [c, g] = canvas(64, 64), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); return t;
}
// a suit symbol for the puff off a hit: neon fill, fat black outline
function symTex(k) {
  const [c, g] = canvas(64, 64);
  suitPath(g, k, 32, 34, 54); g.lineWidth = 7; g.lineJoin = 'round'; g.strokeStyle = '#111'; g.stroke(); g.fillStyle = hex(GLOW[k]); g.fill();
  suitPath(g, k, 30, 31, 30); g.fillStyle = 'rgba(255,255,255,0.55)'; g.fill(); // a shine
  return tex(c);
}

function cardShape() {
  const s = new THREE.Shape(), w = CARD_W / 2, h = CARD_H / 2, r = CARD_R;
  s.moveTo(-w + r, -h); s.lineTo(w - r, -h); s.absarc(w - r, -h + r, r, -Math.PI / 2, 0);
  s.lineTo(w, h - r); s.absarc(w - r, h - r, r, 0, Math.PI / 2);
  s.lineTo(-w + r, h); s.absarc(-w + r, h - r, r, Math.PI / 2, Math.PI);
  s.lineTo(-w, -h + r); s.absarc(-w + r, -h + r, r, Math.PI, Math.PI * 1.5);
  return s;
}

let K = null; // everything shared, made once
export function cardKit() {
  if (K) return K;
  const shape = cardShape();
  const slab = new THREE.ExtrudeGeometry(shape, { depth: CARD_T, bevelEnabled: false, curveSegments: 3 });
  slab.translate(0, 0, -CARD_T / 2).rotateX(-Math.PI / 2);
  const flat = new THREE.ShapeGeometry(shape, 3), uv = flat.attributes.uv, pos = flat.attributes.position;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, pos.getX(i) / CARD_W + 0.5, pos.getY(i) / CARD_H + 0.5);
  const face = flat.clone().translate(0, 0, CARD_T / 2 + 0.0012).rotateX(-Math.PI / 2); // up (+y)
  const back = flat.clone().rotateY(Math.PI).translate(0, 0, -CARD_T / 2 - 0.0012).rotateX(-Math.PI / 2); // down (-y)
  const paper = new THREE.MeshBasicMaterial({ color: 0xfffaf0 });
  const backMat = new THREE.MeshBasicMaterial({ map: backTex() });
  const gt = glowTex();
  const S = {};
  for (const k of SUIT_KEYS) {
    const edge = new THREE.MeshBasicMaterial({ color: GLOW[k] }); // neon edges: an edge-on card is still a bright line
    S[k] = {
      slab: [paper, edge], face: new THREE.MeshBasicMaterial({ map: faceTex(k) }), back: backMat,
      glow: new THREE.SpriteMaterial({ map: gt, color: GLOW[k], blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, opacity: 0.85 }),
      trail: new THREE.MeshBasicMaterial({ color: GLOW[k], vertexColors: true, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, side: THREE.DoubleSide }),
      sym: new THREE.SpriteMaterial({ map: symTex(k), transparent: true, depthWrite: false }),
    };
  }
  K = { slab, face, back, S };
  return K;
}

// one card: an outer group to aim, an inner one to spin, the slab and its two faces
export function buildCard3D(suit = 's') {
  const k = cardKit(), m = k.S[suit] || k.S.s;
  const spin = new THREE.Group();
  const slab = new THREE.Mesh(k.slab, m.slab), face = new THREE.Mesh(k.face, m.face), back = new THREE.Mesh(k.back, m.back);
  spin.add(slab, face, back);
  const root = new THREE.Group(); root.add(spin);
  root.userData.card = { spin, slab, face, back };
  return root;
}
export function dressCard(root, suit) { // a pooled card changes suit: just swap materials
  const m = cardKit().S[suit] || cardKit().S.s, c = root.userData.card;
  c.slab.material = m.slab; c.face.material = m.face; c.back.material = m.back;
}
