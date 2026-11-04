// Spinning weapon preview for the cosmetics screen. Its own tiny renderer so it works from the menu.
import * as THREE from 'three';
import { buildWeapon, freeTree } from './models.js';
import { makeSkinSystems, emitSkinFx } from './skins.js';

let renderer, scene, cam, holder, cur = null, systems, canvas, fit = 1;
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
  renderer.setSize(Math.max(40, Math.floor(w * 0.5)), Math.max(30, Math.floor(h * 0.5)), false); // crunchy on purpose
  cam.aspect = w / h;
  cam.updateProjectionMatrix();
  scaleU.value = (h * 0.5) / (2 * Math.tan((cam.fov * Math.PI) / 360));
}

export function showPreview(id, skin) {
  if (!holder) return;
  freeTree(holder); holder.clear(); // the last thing shown is gone for good
  const g = buildWeapon(id, skin);
  g.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(g);
  const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
  fit = 2.3 / Math.max(size.x, size.y, size.z, 0.05);
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
  freeTree(holder); holder.clear(); // the last thing shown is gone for good
  const ch = build(color, look);
  const wrap = new THREE.Group();
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
  holder.rotation.y += dt * 0.9;
  holder.updateMatrixWorld(true);
  emitSkinFx(systems, cur, dt, Math.min(2, fit * 0.6));
  systems.update(dt);
  renderer.render(scene, cam);
}
