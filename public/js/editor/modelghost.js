// What you hold in the map editor: the real Blender model, fitted onto its boxes the same way propfield.js draws the
// map's props (so a grabbed car looks like the car, not a pile of boxes), plus a cyan outline. Buildings and plain boxes
// (and a model that hasn't landed yet) are see-through pink boxes. Built round a pivot o: the group's own origin.
import * as THREE from 'three';
import { authored } from '../glbkit.js';

const hash = (x, z) => { const s = Math.sin(x * 12.9898 + z * 78.233) * 43758.5453; return s - Math.floor(s); }; // (propfield.js)
const stripN = (n) => String(n || '').replace(/\.\d+$/, '');
const isLod1 = (o) => { for (let p = o; p; p = p.parent) if (stripN(p.userData.name ?? p.name) === 'lod1') return true; return false; };
// which model draws a placement, like propfield.js modelFor (a parked car picks its model by where it stands)
function modelOf(p) {
  if (p.id === 'car' && p.a) {
    const list = p.t === 'caryellow' ? ['p_car_taxi', 'p_car_sedan', 'p_car_hatch'] : ['p_car_sedan', 'p_car_hatch'], k = p.t === 'caryellow' ? 0 : (hash(p.a[0], p.a[2]) * list.length) | 0;
    for (let i = 0; i < list.length; i++) { const a = authored(list[(k + i) % list.length]); if (a) return { a, turn: Math.PI / 2 }; }
  }
  const a = authored('p_' + p.id);
  return a ? { a, turn: 0 } : null;
}
const _m = new THREE.Matrix4(), _r = new THREE.Matrix4(), _s = new THREE.Matrix4(), _t = new THREE.Matrix4();
// the model of a prop placement, placed in world space (null: no model, or not loaded yet)
export function propModel(p) {
  const mf = modelOf(p);
  if (!mf) return null;
  const root = mf.a.obj, base = new THREE.Matrix4().makeRotationY(mf.turn);
  root.updateMatrixWorld(true);
  const inner = new THREE.Group(); inner.add(root); inner.matrixAutoUpdate = false; inner.matrix.copy(base);
  root.traverse((o) => { if (isLod1(o)) o.visible = false; if (o.isMesh) o.castShadow = o.receiveShadow = false; });
  // its near bounds after the turn, or the box it was built against (meta.box)
  const ref = new THREE.Box3(), tmp = new THREE.Box3(), inv = new THREE.Matrix4().copy(root.matrixWorld).invert();
  root.traverse((o) => { if (o.isMesh && o.geometry && o.visible && !isLod1(o)) { o.geometry.computeBoundingBox(); tmp.copy(o.geometry.boundingBox).applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld).premultiply(base)); ref.union(tmp); } });
  const mb = mf.a.meta && mf.a.meta.box;
  if (Array.isArray(mb) && mb.length === 2) ref.set(new THREE.Vector3(...mb[0]), new THREE.Vector3(...mb[1])).applyMatrix4(base);
  if (ref.isEmpty()) return null;
  const g = new THREE.Group(); g.add(inner); g.matrixAutoUpdate = false;
  if (!p.a) { // round 1: position, quarter turns, scale
    g.matrix.makeRotationY(-(p.r || 0) * Math.PI / 2).premultiply(_t.makeTranslation(p.p[0], p.p[1], p.p[2]));
    if (p.s) g.matrix.multiply(_s.makeScale(p.s, p.s, p.s));
    return g;
  }
  const ml = ref.min, mh = ref.max, ex = (i) => p.hi[i] - p.lo[i], md = (i) => [mh.x - ml.x, mh.y - ml.y, mh.z - ml.z][i];
  const sc = (i) => (md(i) > 1e-3 && ex(i) > 1e-3 ? ex(i) / md(i) : 1);
  if (p.f !== undefined) {
    const sh = (sc(0) + sc(2)) / 2, sy = sc(1);
    g.matrix.makeTranslation(0, -ml.y, 0).premultiply(_s.makeScale(sh, sy, sh)).premultiply(_r.makeRotationY(p.y)).premultiply(_t.makeTranslation(p.a[0], p.a[1] + p.lo[1], p.a[2]));
  } else {
    g.matrix.makeTranslation(-ml.x, -ml.y, -ml.z).premultiply(_s.makeScale(sc(0), sc(1), sc(2))).premultiply(_t.makeTranslation(p.lo[0], p.lo[1], p.lo[2]))
      .premultiply(_r.makeRotationY(p.y || 0)).premultiply(_m.makeTranslation(p.a[0], p.a[1], p.a[2]));
  }
  return g;
}

const pinkMat = new THREE.MeshBasicMaterial({ color: 0xff4fd8, transparent: true, opacity: 0.28, depthWrite: false });
// ts: the things, o: the pivot. see: see-through models (the plop cannon's preview). edges: the outline geometry
export function ghostOf(ts, o, edges, see = false) {
  const g = new THREE.Group(), body = new THREE.Group(); body.position.set(-o[0], -o[1], -o[2]); g.add(body);
  for (const t of ts) {
    const m = t.prop ? propModel(t.prop) : null;
    if (m) {
      if (see) m.traverse((x) => { if (x.isMesh) { const mats = Array.isArray(x.material) ? x.material : [x.material]; x.material = mats.map((mm) => { const c = mm.clone(); c.transparent = true; c.opacity = 0.62; c.depthWrite = false; c.userData.ghost = true; return c; }); if (x.material.length === 1) x.material = x.material[0]; } });
      body.add(m); continue;
    }
    for (const b of t.boxes.length ? t.boxes : []) {
      const sx = b.max[0] - b.min[0], sy = b.max[1] - b.min[1], sz = b.max[2] - b.min[2], mm = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), pinkMat);
      mm.position.set((b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2); mm.rotation.y = b.rot || 0; mm.userData.own = true;
      body.add(mm);
    }
  }
  if (edges) { const el = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x4fd8ff, depthTest: false, transparent: true, opacity: 0.8 })); el.renderOrder = 999; el.userData.own = true; body.add(el); }
  return g;
}
// throw a ghost away (its own geometry + see-through material copies; the models' shared parts stay)
export function dropGhost(g) {
  if (!g) return;
  if (g.parent) g.parent.remove(g);
  g.traverse((x) => {
    if (x.userData.own && x.geometry) x.geometry.dispose();
    if (x.isLineSegments && x.material) x.material.dispose();
    const mats = x.material ? (Array.isArray(x.material) ? x.material : [x.material]) : [];
    for (const m of mats) if (m.userData && m.userData.ghost) m.dispose();
  });
}
