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

// item pictures (drawn, not rendered): grenade, medkit, bubble, duck, smoke
const itemCache = new Map();
export function itemIcon(id) {
  if (itemCache.has(id)) return itemCache.get(id);
  const c = document.createElement('canvas'); c.width = 96; c.height = 60;
  const x = c.getContext('2d');
  x.lineWidth = 3; x.strokeStyle = '#000';
  const circle = (cx, cy, r, fill) => { x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.fillStyle = fill; x.fill(); x.stroke(); };
  if (id === 'frag') {
    x.beginPath(); x.ellipse(48, 34, 16, 20, 0, 0, Math.PI * 2); x.fillStyle = '#5a6a2a'; x.fill(); x.stroke();
    x.fillStyle = '#3a4a1a'; for (let i = -1; i <= 1; i++) x.fillRect(34, 32 + i * 9, 28, 2);
    x.fillStyle = '#444'; x.fillRect(42, 10, 12, 8); x.strokeRect(42, 10, 12, 8);
    x.beginPath(); x.arc(62, 12, 6, 0, Math.PI * 2); x.strokeStyle = '#ddd'; x.stroke();
  } else if (id === 'medkit') {
    x.fillStyle = '#ffffff'; x.fillRect(24, 14, 48, 36); x.strokeRect(24, 14, 48, 36);
    x.fillStyle = '#ff3030'; x.fillRect(43, 20, 10, 24); x.fillRect(36, 27, 24, 10);
    x.fillStyle = '#ddd'; x.fillRect(40, 8, 16, 6); x.strokeRect(40, 8, 16, 6);
  } else if (id === 'bubble') {
    x.beginPath(); x.arc(48, 32, 22, 0, Math.PI * 2); x.fillStyle = 'rgba(79,216,255,0.35)'; x.fill(); x.strokeStyle = '#4fd8ff'; x.lineWidth = 4; x.stroke();
    x.beginPath(); x.arc(40, 24, 7, Math.PI, Math.PI * 1.6); x.strokeStyle = '#fff'; x.lineWidth = 3; x.stroke();
  } else if (id === 'duck') {
    circle(44, 38, 16, '#ffd23b'); circle(58, 22, 10, '#ffd23b');
    x.fillStyle = '#ff7a1a'; x.beginPath(); x.moveTo(66, 22); x.lineTo(78, 25); x.lineTo(66, 28); x.fill();
    x.fillStyle = '#000'; x.fillRect(58, 18, 3, 3);
  } else if (id === 'smoke') {
    x.fillStyle = '#9aa0a8'; x.fillRect(40, 26, 16, 26); x.strokeRect(40, 26, 16, 26);
    for (const [cx, cy, r] of [[40, 18, 9], [52, 14, 10], [62, 20, 8], [30, 22, 7]]) circle(cx, cy, r, '#d8dce0');
  }
  const url = c.toDataURL();
  itemCache.set(id, url);
  return url;
}
