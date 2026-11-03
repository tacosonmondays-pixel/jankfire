// Weapon pictures for the hotbar: each weapon (with your skin, wrap and hat) rendered side-on into a small
// transparent image, cached until something about it changes.
import * as THREE from 'three';
import { buildWeapon } from './models.js';

const IW = 160, IH = 96;
let r = null, scene = null, cam = null;
const cache = new Map();
const box = new THREE.Box3(), size = new THREE.Vector3(), center = new THREE.Vector3();

function init() {
  r = new THREE.WebGLRenderer({ antialias: false, alpha: true, preserveDrawingBuffer: true });
  r.setPixelRatio(1);
  r.setSize(IW, IH, false);
  r.setClearColor(0x000000, 0);
  scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a6a8a, 3.2));
  const sun = new THREE.DirectionalLight(0xffffff, 2.0);
  sun.position.set(0.4, 1, 1.2);
  scene.add(sun);
  cam = new THREE.PerspectiveCamera(28, IW / IH, 0.01, 50);
}

export function clearIcons() { cache.clear(); }

export function weaponIcon(id, skin) {
  const key = id + '|' + (Array.isArray(skin) ? skin.join(',') : '');
  if (cache.has(key)) return cache.get(key);
  try {
    if (!r) init();
    const g = buildWeapon(id, skin);
    const holder = new THREE.Group();
    const flat = id === 'cards' || id === 'reverse'; // flat things look at you, everything else side-on
    g.rotation.y = flat ? 0 : -Math.PI / 2; // muzzle to the right, like an inventory picture
    holder.add(g);
    holder.rotation.x = flat ? -0.15 : 0.28; // a little from above
    holder.rotation.z = flat ? 0 : 0.06;
    scene.add(holder);
    holder.updateMatrixWorld(true);
    box.setFromObject(holder);
    box.getSize(size); box.getCenter(center);
    holder.position.sub(center);
    const fit = Math.max(size.x / cam.aspect, size.y) * 1.04;
    cam.position.set(0, 0, fit / (2 * Math.tan((cam.fov * Math.PI) / 360)) + size.z / 2);
    cam.lookAt(0, 0, 0);
    r.render(scene, cam);
    const url = r.domElement.toDataURL('image/png');
    scene.remove(holder);
    cache.set(key, url);
    return url;
  } catch (e) {
    console.warn('icon', id, e);
    return '';
  }
}
