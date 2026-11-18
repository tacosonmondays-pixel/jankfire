// THE TALL GUY FROM HR, built by the web's own buildHR (public/js/hrguy.js, copied line for line below: that module
// pulls in the whole game client, this needs only the model), written per joint like lore_dump.mjs. His badge's canvas
// (a "☺ CORP" band, an egg photo, "HR") becomes shapes: a pale card, a blue band, a grey photo square with a pale egg.
// usage: node --import ./lore_register.mjs hr_dump.mjs <out_dir>
import './lore_dom_stub.mjs';
import * as THREE from 'three';
import fs from 'node:fs';
const K = 3;
const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
const lam = (color, o = {}) => new THREE.MeshLambertMaterial({ color, ...o });
const MATS = {
  suit: lam(0x565c6c), suitDark: lam(0x3a3f4c), pants: lam(0x2c2f38), shoe: lam(0x0c0c0e),
  shirt: lam(0xe8e8ea), tie: lam(0xb81a26), strap: lam(0x2a6cff), skin: lam(0xe6e0d6),
  badge: lam(0xf4f2ec), clip: lam(0x6a4a2a), paper: lam(0xf4f2ec), ear: lam(0x19a8ff), dark: lam(0x111114),
  band: lam(0x2a6cff), photo: lam(0xcfcac0), egg: lam(0xece8e0),
};
function part(parent, geo, mat, x, y, z) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); parent.add(m); return m; }
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
function buildHR() {
  const M = MATS, g = new THREE.Group(), body = new THREE.Group(); g.add(body); g.name = 'npc'; body.name = 'body';
  const legs = [];
  for (const s of [-1, 1]) {
    const L = new THREE.Group(); L.position.set(s * 0.11, 1.86, 0); body.add(L); legs.push(L);
    part(L, box(0.14, 0.95, 0.16), M.pants, 0, -0.47, 0);
    part(L, box(0.12, 0.92, 0.14), M.pants, 0, -1.38, 0.0);
    part(L, box(0.02, 1.8, 0.01), M.suitDark, 0, -0.92, -0.08);
    part(L, box(0.13, 0.09, 0.36), M.shoe, 0, -1.8, -0.08);
  }
  part(body, box(0.42, 0.52, 0.24), M.suit, 0, 2.12, 0);
  part(body, box(0.54, 0.6, 0.26), M.suit, 0, 2.66, 0);
  for (const s of [-1, 1]) part(body, box(0.16, 0.08, 0.28), M.suit, s * 0.3, 2.95, 0);
  part(body, box(0.44, 0.14, 0.25), M.suitDark, 0, 1.9, 0);
  part(body, box(0.16, 0.44, 0.02), M.shirt, 0, 2.74, -0.135);
  for (const s of [-1, 1]) { const lap = part(body, box(0.09, 0.42, 0.02), M.suitDark, s * 0.1, 2.75, -0.142); lap.rotation.z = s * 0.28; }
  part(body, box(0.07, 0.07, 0.03), M.tie, 0, 2.93, -0.15);
  const tie = part(body, box(0.06, 0.5, 0.02), M.tie, 0, 2.64, -0.152); tie.rotation.z = 0.04;
  part(body, box(0.09, 0.08, 0.02), M.tie, 0.01, 2.37, -0.152);
  for (const y of [2.3, 2.12]) part(body, box(0.03, 0.03, 0.01), M.dark, 0, y, -0.124);
  for (const s of [-1, 1]) { const st = part(body, box(0.025, 0.5, 0.01), M.strap, s * 0.07, 2.72, -0.16); st.rotation.z = -s * 0.12; }
  part(body, box(0.05, 0.04, 0.02), M.dark, 0, 2.47, -0.165);
  // the badge (web: a canvas card) as shapes
  part(body, box(0.15, 0.2, 0.012), M.badge, 0, 2.35, -0.17);
  part(body, box(0.152, 0.036, 0.014), M.band, 0, 2.432, -0.171);
  part(body, box(0.085, 0.072, 0.014), M.photo, 0, 2.36, -0.171);
  { const e = part(body, new THREE.SphereGeometry(1, 8, 6), M.egg, 0, 2.358, -0.178); e.scale.set(0.022, 0.03, 0.006); }
  part(body, box(0.09, 0.012, 0.014), M.dark, 0, 2.29, -0.171);
  part(body, box(0.1, 0.16, 0.1), M.skin, 0, 3.02, 0);
  const head = new THREE.Group(); head.position.set(0, 3.08, 0); body.add(head); head.name = 'head';
  const egg = part(head, new THREE.SphereGeometry(1, 9, 7), M.skin, 0, 0.25, 0); egg.scale.set(0.19, 0.27, 0.21);
  part(head, box(0.04, 0.07, 0.05), M.dark, 0.19, 0.24, -0.02);
  const earG = new THREE.Group(); earG.position.set(0.215, 0.27, -0.04); head.add(earG); earG.name = 'ear';
  part(earG, box(0.02, 0.02, 0.02), M.ear, 0, 0, 0);
  const arms = [];
  for (const s of [-1, 1]) {
    const A = new THREE.Group(); A.position.set(s * 0.33, 2.9, 0); body.add(A); arms.push(A); A.name = s < 0 ? 'armL' : 'armR';
    part(A, box(0.11, 0.78, 0.12), M.suit, 0, -0.39, 0);
    const F = new THREE.Group(); F.position.set(0, -0.78, 0); A.add(F); F.name = s < 0 ? 'foreL' : 'foreR';
    part(F, box(0.1, 0.74, 0.11), M.suit, 0, -0.37, 0);
    part(F, box(0.11, 0.06, 0.12), M.shirt, 0, -0.73, 0);
    part(F, box(0.08, 0.16, 0.06), M.skin, 0, -0.84, 0);
    for (let i = 0; i < 4; i++) part(F, box(0.016, 0.24 + (i === 1 || i === 2 ? 0.05 : 0), 0.016), M.skin, -0.03 + i * 0.02, -1.04, -0.01);
    A.userData.fore = F;
  }
  const clip = new THREE.Group(); clip.position.set(0, -0.92, -0.05); arms[1].userData.fore.add(clip);
  part(clip, box(0.24, 0.32, 0.015), M.clip, 0, -0.12, 0);
  part(clip, box(0.2, 0.26, 0.004), M.paper, 0, -0.14, -0.01);
  part(clip, box(0.08, 0.03, 0.025), M.dark, 0, 0.03, -0.005);
  clip.rotation.x = -0.15;
  return g;
}
const root = buildHR();
root.updateMatrixWorld(true);
const JOINTS = ['npc', 'body', 'head', 'ear', 'armL', 'foreL', 'armR', 'foreR'];
const nodes = []; root.traverse((n) => nodes.push(n));
const isJoint = (n) => JOINTS.includes(n.name);
const jointOf = (n) => { let p = n; while (p && !isJoint(p)) p = p.parent; return p; };
const joints = [];
for (const n of nodes) if (isJoint(n)) {
  const par = n === root ? null : jointOf(n.parent);
  const pm = par ? new THREE.Matrix4().compose(par.getWorldPosition(new THREE.Vector3()), par.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)) : new THREE.Matrix4();
  const nm = new THREE.Matrix4().compose(n.getWorldPosition(new THREE.Vector3()), n.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1));
  const rel = pm.clone().invert().multiply(nm); const rp = new THREE.Vector3(), rq = new THREE.Quaternion(); rel.decompose(rp, rq, new THREE.Vector3());
  joints.push({ name: n.name, parent: par ? par.name : null, cf: [...rp.multiplyScalar(K).toArray().map((v) => +v.toFixed(5)), ...rq.toArray().map((v) => +v.toFixed(6))],
    pos: n.position.toArray().map((v) => +v.toFixed(5)), rot: [n.rotation.x, n.rotation.y, n.rotation.z].map((v) => +v.toFixed(5)), order: 'XYZ', posScale: K, moves: true });
}
const pieces = {}; const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3();
root.traverse((m) => {
  if (!m.isMesh) return;
  const j = jointOf(m), jm = new THREE.Matrix4().compose(j.getWorldPosition(new THREE.Vector3()), j.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)).invert();
  const M = jm.multiply(m.matrixWorld), flip = M.determinant() < 0;
  const g = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry, pos = g.attributes.position;
  const list = (pieces[j.name] ||= []);
  for (let i = 0; i < pos.count; i += 3) {
    A.fromBufferAttribute(pos, i).applyMatrix4(M).multiplyScalar(K); B.fromBufferAttribute(pos, i + 1).applyMatrix4(M).multiplyScalar(K); C.fromBufferAttribute(pos, i + 2).applyMatrix4(M).multiplyScalar(K);
    const q = flip ? [A, C, B] : [A, B, C];
    list.push([...q.flatMap((v) => [+v.x.toFixed(4), +v.y.toFixed(4), +v.z.toFixed(4)]), m.material.color.getHexString(), 0]);
  }
});
const box3 = new THREE.Box3().setFromObject(root);
fs.writeFileSync(`${out}/hr.json`, JSON.stringify({ id: 'hr', name: 'Tall Guy From HR', K, joints, pieces, box: [box3.min.toArray().map((v) => v * K), box3.max.toArray().map((v) => v * K)] }));
console.log(JSON.stringify({ joints: joints.map((j) => j.name), tris: Object.fromEntries(Object.entries(pieces).map(([k, v]) => [k, v.length])), h: (box3.max.y - box3.min.y) * K }));
