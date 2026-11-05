// Spinning weapon preview for the cosmetics screen. Its own tiny renderer so it works from the menu.
import * as THREE from 'three';
import { buildWeapon, freeTree } from './models.js';
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
  sway = 0; holder.rotation.y = 0;
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
  sway = 0; holder.rotation.y = 0;
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
}
