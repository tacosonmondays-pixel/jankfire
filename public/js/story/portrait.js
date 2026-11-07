// OVERDUE portraits: the talk box shows the speaker's real 3D face, rendered live from the world (their actor, in its
// current light and pose: blinking, flapping, grinning) into a small render target, copied to a 2D canvas.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { headPos } from './actors.js';

const SZ = 192;
const PORT_BG = { puppet: '#ff4fd8', normal: '#4fd8ff', mannequin: '#ffe14d' };
let rt = null, px = null, img = null, tmp = null;
const cam = new THREE.PerspectiveCamera(24, 1, 0.05, 60), hp = new THREE.Vector3(), fw = new THREE.Vector3(), side = new THREE.Vector3();

// a: an actor. cv: the 2D canvas to draw into
export function drawPortrait(a, cv) {
  if (!G.renderer || !a) return false;
  if (!rt) { rt = new THREE.WebGLRenderTarget(SZ, SZ, { samples: 0 }); rt.texture.colorSpace = THREE.SRGBColorSpace; px = new Uint8Array(SZ * SZ * 4); }
  headPos(a, hp);
  const s = a.ch.root.scale.y, H = a.L.kind === 'puppet' && a.L.look === 'gordo' ? 1.35 : 1; // big faces need a step back
  hp.y -= 0.08 * s * H;
  fw.set(-Math.sin(a.yaw), 0, -Math.cos(a.yaw)); // where they face
  side.set(Math.cos(a.yaw), 0, -Math.sin(a.yaw));
  cam.position.copy(hp).addScaledVector(fw, 0.95 * s * H).addScaledVector(side, 0.32 * s * H); cam.position.y += 0.04;
  cam.lookAt(hp); cam.updateMatrixWorld();
  const r = G.renderer, prev = r.getRenderTarget(), auto = r.autoClear;
  const vis = a.ch.root.visible; a.ch.root.visible = true;
  const cc = r.getClearColor(new THREE.Color()), ca = r.getClearAlpha(), bg = G.scene.background, fog = G.scene.fog;
  r.setClearColor(0x000000, 0); G.scene.background = null; G.scene.fog = null; // (only the person: the backdrop is drawn in 2D)
  r.setRenderTarget(rt); r.autoClear = true; r.render(G.scene, cam);
  G.scene.background = bg; G.scene.fog = fog; r.setClearColor(cc, ca);
  r.readRenderTargetPixels(rt, 0, 0, SZ, SZ, px);
  r.setRenderTarget(prev); r.autoClear = auto; a.ch.root.visible = vis;
  const g = cv.getContext('2d');
  if (cv.width !== SZ) { cv.width = SZ; cv.height = SZ; }
  if (!tmp) { tmp = document.createElement('canvas'); tmp.width = tmp.height = SZ; img = tmp.getContext('2d').createImageData(SZ, SZ); }
  for (let y = 0; y < SZ; y++) img.data.set(px.subarray((SZ - 1 - y) * SZ * 4, (SZ - y) * SZ * 4), y * SZ * 4); // (gl rows are bottom-up)
  tmp.getContext('2d').putImageData(img, 0, 0);
  // the zine backdrop: flat colour per character + halftone dots, then the person on top
  g.fillStyle = a.def.portBg || PORT_BG[a.L.kind] || '#ff4fd8'; g.fillRect(0, 0, SZ, SZ);
  g.fillStyle = 'rgba(0,0,0,0.16)'; for (let y = 0; y < SZ; y += 8) for (let x = (y / 8) % 2 ? 4 : 0; x < SZ; x += 8) { g.beginPath(); g.arc(x, y, 1.8 + (y / SZ) * 1.4, 0, 6.3); g.fill(); }
  g.drawImage(tmp, 0, 0);
  return true;
}
