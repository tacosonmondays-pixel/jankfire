// usage: node --import ./tools/roblox/lore_register.mjs tools/roblox/lore_dump.mjs <dump_dir> [ids]   (THREE_DIR: a three 0.170.0 folder)
// THE HIDDEN NPCS (web shared/secrets.js + public/js/lorenpcs.js), built by the web's own code in Node, written out per
// moving piece: every node the web's update() moves is a joint; every mesh goes with its nearest joint, in that joint's
// own frame (studs). The rig (joint tree, rest transforms) goes with it, for the Roblox client's port of update().
// usage: node --import ./lore_register.mjs lore_dump.mjs <out_dir> [ids...]
import './lore_dom_stub.mjs';
import * as THREE from 'three';
import fs from 'node:fs';
const { buildNpc } = await import('file:///C:/Users/soup2/jankfire-port/public/js/lorenpcs.js');
const { SECRETS } = await import('file:///C:/Users/soup2/jankfire-port/shared/secrets.js');
const K = 3; // studs per web metre (the hub egg's)
const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
const ids = process.argv.slice(3).length ? process.argv.slice(3) : ['gary', 'dale', 'janitor', 'smiles', 'todd'];
// names for the joints buildCharacter doesn't name, in the order the dump finds them (printed on each run)
const NAMES = {
  gary: ['turn'], dale: ['machine', 'door', 'turn'], janitor: ['turn', 'mop'],
  smiles: ['balloon1', 'string1', 'balloon2', 'string2', 'balloon3', 'string3'], todd: ['bug'],
};
const hex = (c) => '#' + c.getHexString();
function colourOf(mat, uv, i) {
  const map = mat.map;
  if (map && map.isDataTexture && uv) { const cell = Math.floor(uv.getX(i) * map.image.width), d = map.image.data; return '#' + [d[cell * 4], d[cell * 4 + 1], d[cell * 4 + 2]].map((v) => Math.round(v).toString(16).padStart(2, '0')).join(''); }
  if (map && map.userData && map.userData.canvas) { const c = map.userData.canvas; const s = c.bg || c.first; if (s) { try { return hex(new THREE.Color(s)); } catch {} } }
  return hex(mat.color);
}
// Mr. Smiles' painted face (the web draws it on a canvas wrapped round the big head ball; uploads can't carry a face
// picture, so the same marks are made as shapes on the ball: two tall black eyes with a white glint, the smile, cheeks)
function smilesFace(root) {
  let head = null; root.traverse((n) => { if (n.name === 'head') head = n; });
  const R = 0.33, C = new THREE.Vector3(0, 0.17, 0);
  const at = (az, el, r = R) => new THREE.Vector3(Math.sin(az) * Math.cos(el) * r, Math.sin(el) * r, -Math.cos(az) * Math.cos(el) * r).add(C);
  const mat = (c) => new THREE.MeshLambertMaterial({ color: c });
  const put = (geo, c, az, el, sx, sy, sz, r) => { const m = new THREE.Mesh(geo, mat(c)), p = at(az, el, r), n = at(az, el, r + 1); m.position.copy(p); m.quaternion.setFromRotationMatrix(new THREE.Matrix4().lookAt(n, p, new THREE.Vector3(0, 1, 0))); m.scale.set(sx, sy, sz); head.add(m); return m; };
  const ball = new THREE.SphereGeometry(1, 10, 8);
  const d = Math.PI / 180;
  for (const s of [-1, 1]) {
    put(ball, 0x120818, s * 36 * d, 18 * d, 0.033, 0.06, 0.02, R * 0.985); // eye
    put(ball, 0xffffff, s * 36 * d - 3.5 * d, 26 * d, 0.012, 0.012, 0.01, R * 1.02); // glint
    put(ball, 0xf0a8c0, s * 64 * d, -16 * d, 0.05, 0.03, 0.012, R * 0.99); // cheek
  }
  for (let i = 0; i <= 16; i++) { // the smile: a lower arc, beads close enough to read as one thick line
    const a = 0.2 * Math.PI + (0.6 * Math.PI) * (i / 16), x = Math.cos(a) * 34, y = Math.sin(a) * 34;
    put(ball, 0x120818, (x / 256) * 2 * Math.PI, -(y / 128) * Math.PI * 0.62 - 4 * d, 0.03, 0.024, 0.016, R * 0.99);
  }
}
// Todd's bug: the web's purple and black missing-texture cube (a 4x4 picture per face) as 4x4x4 little cubes
function checker(size) {
  const out = [], n = 4, c = size / n, g = new THREE.BoxGeometry(c, c, c).toNonIndexed(), p = g.attributes.position, v = new THREE.Vector3();
  for (let x = 0; x < n; x++) for (let y = 0; y < n; y++) for (let z = 0; z < n; z++) {
    if (x > 0 && x < n - 1 && y > 0 && y < n - 1 && z > 0 && z < n - 1) continue;
    const col = (x + y + z) % 2 ? '000000' : 'ff00dc', o = new THREE.Vector3((x + 0.5) * c - size / 2, (y + 0.5) * c - size / 2, (z + 0.5) * c - size / 2);
    for (let i = 0; i < p.count; i += 3) { const t = []; for (let j = 0; j < 3; j++) { v.fromBufferAttribute(p, i + j).add(o); t.push(+v.x.toFixed(4), +v.y.toFixed(4), +v.z.toFixed(4)); } out.push([...t, col, 0]); }
  }
  return out;
}
const report = {};
for (const id of ids) {
  const s = SECRETS[id];
  const o = buildNpc(s);
  const root = o.root; root.name = 'npc';
  if (id === 'smiles') smilesFace(root);
  root.updateMatrixWorld(true);
  // build-time state of every node
  const nodes = []; root.traverse((n) => nodes.push(n));
  const snap = new Map(nodes.map((n) => [n, { p: n.position.clone(), q: n.quaternion.clone(), s: n.scale.clone(), e: n.rotation.clone(), vis: n.visible }]));
  // run the web's update() through still, near, talking, for 25 s: whatever moves is a joint
  const moved = new Set();
  const eyes = [null, [0, 1.6, -3], [2.5, 1.7, -1.5], [-2, 1.4, 2]];
  let now = 0;
  for (let f = 0; f < 1500; f++) {
    now += 1000 / 60;
    const e = eyes[Math.floor(f / 375) % eyes.length], near = e ? 1 : 0;
    o.update(1 / 60, now, { eye: e, near, talk: !!e, say: e && (f % 200) < 120, dist: e ? 3 : 40, pos: [0, 0, 0] });
    if (f % 25 === 0) for (const n of nodes) { const a = snap.get(n); if (!n.position.equals(a.p) || !n.quaternion.equals(a.q) || !n.scale.equals(a.s)) moved.add(n); }
  }
  // back to the build-time state for the export
  for (const n of nodes) { const a = snap.get(n); n.position.copy(a.p); n.quaternion.copy(a.q); n.scale.copy(a.s); n.visible = a.vis; }
  root.updateMatrixWorld(true);
  const CH = ['root', 'body', 'head', 'arm', 'armL', 'legL', 'legR', 'kneeL', 'kneeR'];
  const isJoint = (n) => n === root || moved.has(n) || CH.includes(n.name);
  let k = 0; const unnamed = [];
  for (const n of nodes) if (n !== root && isJoint(n) && !CH.includes(n.name)) { const nm = (NAMES[id] || [])[k++] || `j${k}`; unnamed.push(`${nm}<-${n.type}:${n.name || '?'} parent=${n.parent.name || n.parent.type} kids=${n.children.length}`); n.name = nm; }
  const joints = [];
  const jointOf = (n) => { let p = n; while (p && !isJoint(p)) p = p.parent; return p; };
  const wsc = (n) => n.getWorldScale(new THREE.Vector3()).x;
  for (const n of nodes) if (isJoint(n)) {
    const par = n === root ? null : jointOf(n.parent);
    // its frame relative to its parent joint's frame (both without scale), studs
    const pm = par ? new THREE.Matrix4().compose(par.getWorldPosition(new THREE.Vector3()), par.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)) : new THREE.Matrix4();
    const nm = new THREE.Matrix4().compose(n.getWorldPosition(new THREE.Vector3()), n.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1));
    const rel = pm.clone().invert().multiply(nm);
    const rp = new THREE.Vector3(), rq = new THREE.Quaternion(); rel.decompose(rp, rq, new THREE.Vector3());
    // direct parent is the parent joint? then the web's own local numbers drive it (update() writes rotation.x etc.)
    const direct = par && n.parent === par;
    joints.push({
      name: n.name, parent: par ? par.name : null, direct: !!direct,
      cf: [...rp.multiplyScalar(K).toArray().map((v) => +v.toFixed(5)), ...rq.toArray().map((v) => +v.toFixed(6))],
      pos: snap.get(n).p.toArray().map((v) => +v.toFixed(5)), rot: [snap.get(n).e.x, snap.get(n).e.y, snap.get(n).e.z].map((v) => +v.toFixed(5)), order: snap.get(n).e.order,
      posScale: +((n.parent ? wsc(n.parent) : 1) * K).toFixed(5), moves: moved.has(n),
    });
  }
  // every visible mesh into its joint's frame
  const pieces = {};
  const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3();
  root.traverse((m) => {
    if (!m.isMesh) return;
    for (let p = m; p; p = p.parent) if (!p.visible) return;
    const j = jointOf(m), jm = new THREE.Matrix4().compose(j.getWorldPosition(new THREE.Vector3()), j.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)).invert();
    const M = jm.multiply(m.matrixWorld), flip = M.determinant() < 0;
    const g0 = m.geometry, g = g0.index ? g0.toNonIndexed() : g0, pos = g.attributes.position, uv = g.attributes.uv;
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    const groups = g.groups && g.groups.length ? g.groups : [{ start: 0, count: pos.count, materialIndex: 0 }];
    const list = (pieces[j.name] ||= []);
    for (const gr of groups) {
      const mat = mats[gr.materialIndex || 0] || mats[0];
      if (mat.visible === false || (mat.transparent && mat.opacity < 0.2)) continue;
      const glass = mat.transparent && mat.opacity < 0.9;
      for (let i = gr.start; i < gr.start + gr.count; i += 3) {
        A.fromBufferAttribute(pos, i).applyMatrix4(M).multiplyScalar(K); B.fromBufferAttribute(pos, i + 1).applyMatrix4(M).multiplyScalar(K); C.fromBufferAttribute(pos, i + 2).applyMatrix4(M).multiplyScalar(K);
        const q = flip ? [A, C, B] : [A, B, C];
        list.push([...q.flatMap((v) => [+v.x.toFixed(4), +v.y.toFixed(4), +v.z.toFixed(4)]), colourOf(mat, uv, i).slice(1), glass ? 1 : 0]);
      }
    }
  });
  if (id === 'todd' && pieces.bug) pieces.bug = checker(0.32 * K);
  for (const k2 of Object.keys(pieces)) if (/^string/.test(k2)) delete pieces[k2]; // (strings: ropes in Roblox)
  const box = new THREE.Box3().setFromObject(root);
  const data = { id, name: s.name, K, face: s.face, joints, pieces, box: [box.min.toArray().map((v) => v * K), box.max.toArray().map((v) => v * K)] };
  fs.writeFileSync(`${out}/${id}.json`, JSON.stringify(data));
  report[id] = { joints: joints.map((j) => j.name + (j.moves ? '*' : '')).join(' '), unnamed, tris: Object.fromEntries(Object.entries(pieces).map(([k2, v]) => [k2, v.length])), height: +((box.max.y - box.min.y) * K).toFixed(2) };
}
console.log(JSON.stringify(report, null, 1));
