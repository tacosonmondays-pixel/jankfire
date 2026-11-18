// The web game's player mannequin in its DEFAULT look (shared/looks.js DEFAULT_LOOK: Sash + Shorts, default skin, the
// first LOOK_COLORS pink), built by the web's own code, then every triangle written out in world space with its colour.
// buildCharacter (public/js/models.js) is copied below line for line (its non-GLB branch; hair, accessories and the
// joke body are all "none" / 0 in the default look). The clothes are the web's own clothes.js, run as is.
// The stand is the web character screen's plinth (public/js/preview.js plinth()), at the size it has under a mannequin.
// usage: node --import ./tools/roblox/hub_egg_register.mjs tools/roblox/hub_egg_dump.mjs <out.json>
//   (env THREE_DIR: a three 0.170.0 folder; WEB_DIR: the web repo. then tools/roblox/hub_egg_mannequin.py)
import * as THREE from 'three';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const WEB = process.env.WEB_DIR || 'D:/Robloxd/jankfire/';
const { wearTop, wearBottom, topCap, topOwn } = await import(pathToFileURL(WEB + 'public/js/clothes.js').href);
const { DEFAULT_LOOK, LOOK_COLORS } = await import(pathToFileURL(WEB + 'shared/looks.js').href);

// ---- models.js helpers (M without jankify / caching: only the colour matters here)
const M = (color, basic = false) => (basic ? new THREE.MeshBasicMaterial({ color }) : new THREE.MeshLambertMaterial({ color, flatShading: true }));
function bx(w, h, d, color, x = 0, y = 0, z = 0, basic = false) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(color, basic)); m.position.set(x, y, z); return m; }
function cylZ(r, len, color, x = 0, y = 0, z = 0, seg = 6, basic = false) { const g = new THREE.CylinderGeometry(r, r, len, seg); g.rotateX(Math.PI / 2); const m = new THREE.Mesh(g, M(color, basic)); m.position.set(x, y, z); return m; }
function ball(r, color, x = 0, y = 0, z = 0, basic = false) { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 6, 4), M(color, basic)); m.position.set(x, y, z); return m; }
const SKIN = 0xe6cba2, JOINT = 0xbf9f74; // (JOINT: only for a GLB body)
function limb(r0, r1, len, color, y) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, len, 6), M(color)); m.position.y = y; return m; }
const RUN_YELLOW = 0xffd20f;
const skinCopy = (m) => m; // (softskin.js: a shader term only, same colour)
const overallsColor = (lk, c) => (lk && lk.bottomColor ? new THREE.Color(lk.bottomColor).getHex() : lk && lk.teamed ? c : 0x3b64a8);

// ---- buildCharacter, the web's own (jank fixed instead of random: a tilted head, a high shoulder, a slight lean)
function buildCharacter(color, look, jank) {
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const c = new THREE.Color(color).getHex();
  const legL = new THREE.Group(), legR = new THREE.Group(), kneeL = new THREE.Group(), kneeR = new THREE.Group();
  const head = new THREE.Group(), arm = new THREE.Group(), armL = new THREE.Group(), slot = new THREE.Group();
  const lk = look || {};
  const SK = lk.skin ? new THREE.Color(lk.skin).getHex() : SKIN;
  const JT = new THREE.Color(SK).multiplyScalar(0.82).getHex();
  const TOP = lk.topColor ? new THREE.Color(lk.topColor).getHex() : c;
  const BOT = lk.bottomColor ? new THREE.Color(lk.bottomColor).getHex() : c;
  const top = lk.top || 'tank', bottom = lk.bottom || 'shorts';
  const WP = { body, head, arm, armL, legL, legR, kneeL, kneeR };
  const legs = bottom === 'pants' || bottom === 'overalls' || bottom === 'checks' || bottom === 'pjpants' || bottom === 'chickenlegs';
  const LEG = bottom === 'overalls' ? overallsColor(lk, c) : BOT;
  for (const [leg, knee, sx] of [[legL, kneeL, -1], [legR, kneeR, 1]]) {
    leg.position.set(0.1 * sx, 0.92, 0);
    leg.add(ball(0.075, JT));
    leg.add(limb(0.07, 0.058, 0.42, SK, -0.22));
    knee.position.y = -0.44;
    knee.add(ball(0.062, JT));
    knee.add(limb(0.056, 0.045, 0.4, SK, -0.21));
    knee.add(bx(0.1, 0.06, 0.22, legs ? (bottom === 'overalls' ? 0x6b3a1a : 0x222222) : SK, 0, -0.43, -0.05));
    leg.add(knee);
    body.add(leg);
  }
  const MAID = lk.topColor ? TOP : lk.teamed ? c : 0x17141c;
  body.add(limb(0.1, 0.12, 0.16, top === 'none' || top === 'tank' ? SK : top === 'maid' ? MAID : TOP, 1.13)); // waist
  const chest = ball(0.2, SK, 0, 1.34, 0); chest.scale.set(1.2, 1.1, 0.72); body.add(chest);
  const TOPC = top === 'runner' ? (lk.topColor ? TOP : lk.teamed ? c : RUN_YELLOW) : top === 'maid' ? MAID : topOwn(top) != null && !lk.topColor && !lk.teamed ? topOwn(top) : TOP;
  body.add(limb(0.045, 0.05, 0.12, SK, 1.57));
  head.position.set(0, 1.62, 0);
  const egg = ball(0.14, SK, 0, 0.14, 0); egg.scale.set(0.85, 1.22, 0.95); head.add(egg);
  head.add(bx(0.005, 0.2, 0.3, JT, 0, 0.14, 0)); // seam where the mold met
  head.rotation.z = jank.tilt;
  body.add(head);
  for (const sx of [-1, 1]) body.add(ball(0.068, topCap(lk, TOPC) ?? JT, 0.25 * sx, 1.45 + (sx > 0 ? jank.shoulder : 0), 0));
  arm.add(cylZ(0.048, 0.28, SK, 0, 0, -0.14));
  arm.add(ball(0.05, JT, 0, 0, -0.29));
  arm.add(cylZ(0.042, 0.24, SK, -0.03, -0.01, -0.42));
  arm.add(ball(0.045, SK, -0.04, -0.02, -0.55));
  const tag = bx(0.05, 0.07, 0.005, 0xffffff, 0.05, -0.06, -0.2); tag.rotation.z = 0.5; arm.add(tag); // price tag still on
  armL.position.set(-0.25, 1.45, 0);
  const upper = cylZ(0.048, 0.3, SK, 0.07, -0.02, -0.14); upper.rotation.y = -0.45; armL.add(upper);
  armL.add(ball(0.05, JT, 0.14, -0.04, -0.28));
  const fore = cylZ(0.042, 0.3, SK, 0.27, -0.04, -0.4); fore.rotation.y = -0.9; armL.add(fore);
  wearTop(WP, lk, TOPC, legs);
  if (!wearBottom(WP, lk, LEG) && top !== 'maid') body.add(bx(0.34, 0.18, 0.23, LEG, 0, 0.98, 0));
  body.add(armL);
  arm.position.set(0.25, 1.45 + jank.shoulder, 0);
  slot.position.set(-0.03, -0.03, -0.56);
  arm.add(slot);
  body.add(arm);
  body.rotation.z = jank.lean * 0.3;
  return { root, body, legL, legR, kneeL, kneeR, head, arm, armL, slot, jank };
}

// ---- the locker mannequin's idle (loco.js idlePose), held at the top of its weight shift (onto the right leg)
function idlePose(ch, t) {
  const sh = Math.sin(t * 0.5), b = Math.sin(t * 2.1);
  ch.body.position.y = b * 0.006 - 0.01 * Math.abs(sh);
  ch.kneeL.rotation.x = -(0.05 + Math.max(0, sh) * 0.2); ch.kneeR.rotation.x = -(0.05 + Math.max(0, -sh) * 0.2);
  ch.legL.rotation.x = Math.max(0, sh) * 0.08; ch.legR.rotation.x = Math.max(0, -sh) * 0.08;
  ch.body.rotation.z = ch.jank.lean * 0.3 + sh * 0.035;
  ch.head.rotation.x = b * 0.015;
}

// ---- preview.js plinth (its concrete is a speckled 16x16 picture with two seams: here each face gets a speckle tone)
function plinth() {
  const g = new THREE.Group(), top = -0.625, seg = 8;
  const conc = new THREE.MeshLambertMaterial({ color: 0x8a8890, flatShading: true }); conc.userData.speck = true;
  const slab = new THREE.Mesh(new THREE.CylinderGeometry(0.44, 0.48, 0.1, seg), conc); slab.position.y = top - 0.05;
  const trim = new THREE.Mesh(new THREE.CylinderGeometry(0.485, 0.5, 0.05, seg), M(0xff4fd8)); trim.position.y = top - 0.125;
  const lip = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.52, 0.05, seg), M(0x120818)); lip.position.y = top - 0.175;
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.36, 0.14, seg), conc); foot.position.y = top - 0.27;
  g.add(slab, trim, lip, foot);
  for (let i = 0; i < seg; i++) {
    const a = (i + 0.5) / seg * Math.PI * 2, b = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.035, 0.02), M(0xc8ccd2));
    b.position.set(Math.sin(a) * 0.49, top - 0.125, Math.cos(a) * 0.49); b.rotation.y = a; g.add(b);
  }
  return g;
}

const look = { ...DEFAULT_LOOK }, color = LOOK_COLORS[0];
const ch = buildCharacter(color, look, { tilt: 0.2, shoulder: 0.045, lean: 0.12, wrongKnee: false });
idlePose(ch, Math.PI); // sin(0.5t) = 1: weight on the right leg, the left knee eased
const scene = new THREE.Group();
scene.add(ch.root);
scene.updateMatrixWorld(true);
const box = new THREE.Box3().setFromObject(ch.root);
const h = box.max.y - box.min.y, s = 1.25 / h; // the character screen: mannequin 1.25 tall, feet on the plinth's top (-0.625)
const pl = plinth();
pl.scale.setScalar(1 / s);
pl.position.y = box.min.y + 0.625 / s; // its top (-0.625 in screen units) at the lowest foot
scene.add(pl);
scene.updateMatrixWorld(true);

// ---- every triangle, world space, with its colour (sRGB hex) and which part it belongs to
let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
const tris = [], A = new THREE.Vector3(), B = new THREE.Vector3(), Cv = new THREE.Vector3();
const hexOf = (col) => col.getHexString();
scene.traverse((o) => {
  if (!o.isMesh) return;
  const part = pl.children.includes(o) || o.parent === pl ? 'stand' : 'body';
  const g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry;
  const p = g.attributes.position, uv = g.attributes.uv, mat = o.material;
  const flip = o.matrixWorld.determinant() < 0;
  for (let i = 0; i < p.count; i += 3) {
    A.fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld);
    B.fromBufferAttribute(p, i + 1).applyMatrix4(o.matrixWorld);
    Cv.fromBufferAttribute(p, i + 2).applyMatrix4(o.matrixWorld);
    let hex;
    if (mat.map && mat.map.isDataTexture && uv) { // clothes.js: the uv picks a palette cell
      const cell = Math.floor(uv.getX(i) * mat.map.image.width), d = mat.map.image.data;
      hex = [d[cell * 4], d[cell * 4 + 1], d[cell * 4 + 2]].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
    } else if (mat.userData.speck) {
      const k = 0.72 + rnd() * 0.45, c = [0x8a, 0x88, 0x90];
      hex = c.map((v) => Math.min(255, Math.round(v * k)).toString(16).padStart(2, '0')).join('');
    } else hex = hexOf(mat.color);
    const q = flip ? [A, Cv, B] : [A, B, Cv];
    tris.push([...q.flatMap((v) => [+v.x.toFixed(5), +v.y.toFixed(5), +v.z.toFixed(5)]), hex, part]);
  }
  // remote.js: how everyone else saw a player. every body piece but the small trim gets a copy 1.12x about its own
  // middle, drawn inside out (BackSide) in the player's colour: the outline. inside out here = the winding turned
  if (part !== 'body' || o.userData.noShell) return;
  const sm = o.matrixWorld.clone().multiply(new THREE.Matrix4().makeScale(1.12, 1.12, 1.12)), ol = new THREE.Color(color).getHexString();
  for (let i = 0; i < p.count; i += 3) {
    A.fromBufferAttribute(p, i).applyMatrix4(sm); B.fromBufferAttribute(p, i + 1).applyMatrix4(sm); Cv.fromBufferAttribute(p, i + 2).applyMatrix4(sm);
    const q = flip ? [A, B, Cv] : [A, Cv, B];
    tris.push([...q.flatMap((v) => [+v.x.toFixed(5), +v.y.toFixed(5), +v.z.toFixed(5)]), ol, 'shell']);
  }
});
const all = new THREE.Box3().setFromObject(scene);
const out = { look, color, height: h, standScale: 1 / s, box: [all.min.toArray(), all.max.toArray()], count: tris.length, tris };
fs.writeFileSync(process.argv[2], JSON.stringify(out));
const cols = {}; for (const t of tris) cols[t[9] + ' ' + t[10]] = (cols[t[9] + ' ' + t[10]] || 0) + 1;
console.log(JSON.stringify({ count: tris.length, height: h, box: out.box, cols }, null, 0));
