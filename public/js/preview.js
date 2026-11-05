// Spinning weapon preview for the cosmetics screen. Its own tiny renderer so it works from the menu.
import * as THREE from 'three';
import { buildWeapon, freeTree, M } from './models.js';
import { makeSkinSystems, emitSkinFx } from './skins.js';

let renderer, scene, cam, holder, cur = null, systems, canvas, fit = 1, sway = 0, res = 0.5, swayT = 0;
const scaleU = { value: 200 };

export function initPreview(c) {
  canvas = c;
  renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true });
  renderer.setPixelRatio(1);
  scene = new THREE.Scene();
  cam = new THREE.PerspectiveCamera(35, 1, 0.01, 50);
  cam.position.set(0, 0.3, 2.2);
  cam.lookAt(0, 0, 0);
  scene.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  sun.position.set(0.6, 1, 0.9);
  scene.add(sun);
  holder = new THREE.Group();
  scene.add(holder);
  systems = makeSkinSystems(scene, scaleU);
  resizePreview();
}

export function resizePreview() {
  if (!renderer) return;
  const w = canvas.clientWidth || 300, h = canvas.clientHeight || 180;
  renderer.setSize(Math.max(40, Math.floor(w * res)), Math.max(30, Math.floor(h * res)), false); // crunchy on purpose
  cam.aspect = w / h;
  cam.updateProjectionMatrix();
  scaleU.value = (h * res) / (2 * Math.tan((cam.fov * Math.PI) / 360));
}

export function showPreview(id, skin) {
  if (!holder) return;
  sway = 0; holder.rotation.y = 0; camHome();
  freeTree(holder); holder.clear(); // the last thing shown is gone for good
  const g = buildWeapon(id, skin);
  g.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(g);
  const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
  fit = 2.3 / Math.max(size.x, size.y, size.z, 0.05);
  if (g.userData.bare) fit = Math.min(fit, 1.15 / Math.max(size.y, 0.05)); // the Blood Cross hand is as tall as it is long: fit it top to bottom
  const wrap = new THREE.Group();
  g.position.sub(c);
  wrap.add(g);
  wrap.scale.setScalar(fit);
  wrap.rotation.y = Math.PI / 2;
  holder.add(wrap);
  cur = g;
}

// show a mannequin with a look instead of a weapon (character screen)
export function showCharacter(build, color, look) {
  if (!holder) return;
  sway = 0; holder.rotation.y = 0; camHome();
  freeTree(holder); holder.clear(); // the last thing shown is gone for good
  const ch = build(color, look);
  const wrap = new THREE.Group();
  wrap.userData.ch = ch;
  ch.root.rotation.y = Math.PI;
  ch.root.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(ch.root);
  const h = Math.max(0.5, box.max.y - box.min.y);
  const s = 1.25 / h; // whole mannequin fits, hat to feet
  ch.root.position.y = -(box.min.y + h / 2);
  wrap.add(ch.root);
  wrap.scale.setScalar(s);
  holder.add(wrap);
  cur = ch.body;
  cur.userData.effect = 'none';
  fit = 1;
}

export function renderPreview(dt) {
  if (!renderer || !cur) return;
  if (sway) { swayT += dt; holder.rotation.y = sway + Math.sin(swayT * 0.7) * 0.45; holder.position.y = Math.sin(swayT * 1.9) * 0.012; } // main menu: a slow idle sway, not a spin
  else holder.rotation.y += dt * 0.9;
  holder.updateMatrixWorld(true);
  emitSkinFx(systems, cur, dt, Math.min(2, fit * 0.6));
  systems.update(dt);
  renderer.render(scene, cam);
}

// render resolution (1 = full, 0.5 = the crunchy default)
export function setPreviewRes(r) { res = r; resizePreview(); }
// main menu hero: the mannequin with your gun up, swaying in place (it faces you, a bit to the side)
export function showArmed(build, color, look, weapon) {
  if (!holder) return;
  showCharacter(build, color, look);
  const wrap = holder.children[0];
  const ch = wrap && wrap.userData.ch;
  if (ch && weapon) {
    ch.arm.rotation.x = -0.12; ch.armL.rotation.x = -0.12; // gun up, pointing just under the camera
    weapon.scale.setScalar(1.5);
    ch.slot.add(weapon);
  }
  sway = 1.05; swayT = 0; // side on, so the gun reads in profile
  holder.add(plinth());
  cam.position.set(0, 0.12, 2.75); cam.lookAt(0, -0.1, 0); // pulled back a bit so the plinth fits under the feet
}
function camHome() { cam.position.set(0, 0.3, 2.2); cam.lookAt(0, 0, 0); }
// the turntable you stand on: a chunky 8-sided concrete slab, a pink trim band, a black lip, bolts. feet at y = -0.625
function speck(hex, n = 16) {
  const cv = document.createElement('canvas'); cv.width = cv.height = n;
  const g = cv.getContext('2d'), c = new THREE.Color(hex);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { const k = 0.72 + Math.random() * 0.45; g.fillStyle = `rgb(${(c.r * 255 * k) | 0},${(c.g * 255 * k) | 0},${(c.b * 255 * k) | 0})`; g.fillRect(x, y, 1, 1); }
  g.fillStyle = 'rgba(0,0,0,0.3)'; g.fillRect(0, 7, n, 1); g.fillRect(9, 0, 1, n); // slab seams
  const t = new THREE.CanvasTexture(cv); t.magFilter = t.minFilter = THREE.NearestFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 3); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function plinth() {
  const g = new THREE.Group(), top = -0.625, seg = 8;
  const conc = new THREE.MeshLambertMaterial({ map: speck(0x8a8890), flatShading: true });
  const slab = new THREE.Mesh(new THREE.CylinderGeometry(0.44, 0.48, 0.1, seg), conc); slab.position.y = top - 0.05;
  const trim = new THREE.Mesh(new THREE.CylinderGeometry(0.485, 0.5, 0.05, seg), M(0xff4fd8)); trim.position.y = top - 0.125;
  const lip = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.52, 0.05, seg), M(0x120818)); lip.position.y = top - 0.175;
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.36, 0.14, seg), conc); foot.position.y = top - 0.27;
  g.add(slab, trim, lip, foot);
  for (let i = 0; i < seg; i++) { // a bolt on every face of the trim
    const a = (i + 0.5) / seg * Math.PI * 2, b = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.035, 0.02), M(0xc8ccd2));
    b.position.set(Math.sin(a) * 0.49, top - 0.125, Math.cos(a) * 0.49); b.rotation.y = a; g.add(b);
  }
  const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.2, 8), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2; shadow.position.y = top + 0.002;
  g.add(shadow);
  return g;
}
