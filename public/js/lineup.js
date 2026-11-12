// The party, stood in a row on the hub's stage (CoD style): each member in their own outfit on a plinth (the leader's is
// yellow), names, a crown, READY, "in a match" over their heads. Its own little renderer, drawn once per change (no loop:
// it's a picture), over the home's hero slot or the lobby's stage. A party of one keeps the usual hero (you, armed).
import * as THREE from 'three';
import { buildCharacter, freeTree } from './models.js';
import { DEFAULT_LOOK } from '/shared/looks.js';

let ren = null, scene = null, cam = null, cv = null, tags = null, holder = null, key = '';
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

function init() {
  cv = el('canvas', 'lineup-cv'); tags = el('div', 'lineup-tags');
  ren = new THREE.WebGLRenderer({ canvas: cv, alpha: true, antialias: false }); ren.setPixelRatio(1);
  scene = new THREE.Scene(); cam = new THREE.PerspectiveCamera(30, 1, 0.1, 60);
  scene.add(new THREE.HemisphereLight(0xffe8ff, 0x3a2040, 1.7));
  const sun = new THREE.DirectionalLight(0xffffff, 2.1); sun.position.set(2, 4, 5); scene.add(sun);
  holder = new THREE.Group(); scene.add(holder);
}
const plMat = { lead: new THREE.MeshLambertMaterial({ color: 0xffe14d }), mate: new THREE.MeshLambertMaterial({ color: 0xff4fd8 }), rim: new THREE.MeshLambertMaterial({ color: 0x120818 }) };
const plGeo = new THREE.CylinderGeometry(0.5, 0.56, 0.16, 10), rimGeo = new THREE.CylinderGeometry(0.58, 0.58, 0.05, 10);
plGeo.userData.shared = rimGeo.userData.shared = true;

// slot: the element to stand them in (null = take the lineup away). ms: [{ id, name, look, ready, busy }], lead: id, me: id
export function showLineup(slot, ms, lead, me, myLook) {
  if (!slot || !ms || ms.length < 2) { if (cv && cv.parentNode) { cv.remove(); tags.remove(); } key = ''; return false; }
  if (!ren) init();
  if (cv.parentNode !== slot) { slot.append(cv, tags); key = ''; }
  const W = slot.clientWidth || 600, H = slot.clientHeight || 400;
  const k = JSON.stringify([W, H, ms, lead, me, myLook]);
  if (k === key) return true;
  key = k;
  ren.setSize(Math.round(W * 0.75), Math.round(H * 0.75), false); // (a bit crunchy, like the hero)
  cv.style.width = W + 'px'; cv.style.height = H + 'px';
  cam.aspect = W / H; cam.updateProjectionMatrix();
  freeTree(holder); holder.clear();
  const n = ms.length, gap = 1.1, D = 2.6 + n * 1.05;
  cam.position.set(0, 1.35, D); cam.lookAt(0, 0.8, 0);
  tags.innerHTML = '';
  ms.forEach((m, i) => {
    const off = i - (n - 1) / 2, g = new THREE.Group();
    g.position.set(off * gap, 0, -Math.abs(off) * 0.35);
    const look = m.id === me && myLook ? myLook : { ...DEFAULT_LOOK, ...(m.look || {}) };
    const C = buildCharacter(look.color || '#ff4fd8', look), ch = C.root;
    ch.rotation.y = Math.PI - off * 0.2 + (i % 2 ? 0.1 : -0.06);
    if (C.arm) C.arm.rotation.x = -1.35 - (i % 2) * 0.15; if (C.armL) C.armL.rotation.x = -1.4; // (arms down: nobody's armed in the lobby)
    ch.updateMatrixWorld(true);
    const bx = new THREE.Box3().setFromObject(ch), s = 1.75 / Math.max(0.5, bx.max.y - bx.min.y);
    ch.scale.setScalar(s); ch.position.y = -bx.min.y * s;
    g.add(ch);
    const pl = new THREE.Mesh(plGeo, m.id === lead ? plMat.lead : plMat.mate); pl.position.y = -0.08; g.add(pl);
    const rim = new THREE.Mesh(rimGeo, plMat.rim); rim.position.y = -0.17; g.add(rim);
    holder.add(g);
    g.updateMatrixWorld(true);
    const top = new THREE.Box3().setFromObject(ch).max.y, v = new THREE.Vector3(g.position.x, top + 0.1, g.position.z).project(cam);
    const t = el('div', 'lineup-tag' + (m.id === me ? ' me' : '') + (m.busy ? ' busy' : ''));
    t.style.left = ((v.x + 1) / 2 * 100) + '%'; t.style.top = ((1 - v.y) / 2 * 100) + '%';
    t.append(el('b', null, (m.id === lead ? '👑 ' : '') + m.name));
    t.append(el('i', m.busy ? 'lt-busy' : m.id === lead ? 'lt-lead' : m.ready ? 'lt-ready' : 'lt-wait', m.busy ? 'IN A MATCH' : m.id === lead ? 'LEADER' : m.ready ? 'READY' : 'not ready'));
    tags.append(t);
  });
  ren.render(scene, cam);
  return true;
}
