// The map editor's tool in your hand (first person, G.vmScene): one chunky sci-fi body, glossy candy paint and chrome
// like the game's Blender guns, with a head per tool: the GRABBY BEAM's claw, the PLOP CANNON's funnel, the YEET RAY's
// tuning fork, the EDIT WAND's crystal. It bobs when you fly, sways when you look, kicks when you fire, dips when you
// swap tools, and the claw shakes while it holds something.
import * as THREE from 'three';

export const TOOLS = {
  grab: { name: 'GRABBY BEAM', col: 0x4fd8ff },
  plop: { name: 'PLOP CANNON', col: 0xffe14d },
  yeet: { name: 'YEET RAY', col: 0xff3030 },
  wand: { name: 'EDIT WAND', col: 0xff4fd8 },
};
const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, metalness: o.m ?? 0.25, roughness: o.r ?? 0.32, emissive: o.e ?? 0x000000, emissiveIntensity: o.ei ?? 1, flatShading: !!o.flat });
const box = (p, w, h, d, m, x = 0, y = 0, z = 0) => { const k = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); k.position.set(x, y, z); p.add(k); return k; };
const cyl = (p, rt, rb, h, seg, m, x = 0, y = 0, z = 0, rx = Math.PI / 2) => { const k = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), m); k.position.set(x, y, z); k.rotation.x = rx; p.add(k); return k; };

let root = null, heads = {}, glowMats = [], core = null, screen = null, scrTex = null, ring = null, prongs = [];
const st = { tool: 'grab', bob: 0, kick: 0, swap: 0, swayX: 0, swayY: 0, hold: 0, t: 0, moving: 0 };
export const MUZZLE = new THREE.Vector3(0, 0.012, -0.33); // in the tool's own frame (the beam starts here)

export function buildVM(scene) {
  root = new THREE.Group(); root.name = 'edtool';
  const paint = mat(0x6a2a9a, { m: 0.15, r: 0.28 }), chrome = mat(0xe8ecf4, { m: 0.35, r: 0.18 }), dark = mat(0x2a1a34, { m: 0.1, r: 0.55 }), pink = mat(0xff4fd8, { m: 0.1, r: 0.3 }); // (no reflection map in this scene: real metal would draw black)
  const glow = mat(0x4fd8ff, { e: 0x4fd8ff, ei: 1.4, m: 0, r: 0.5 }); glowMats.push(glow);
  const gun = new THREE.Group(); root.add(gun);
  // the body: a fat candy-paint block with a chrome spine and pink trim, a bit of a wedge at the front
  box(gun, 0.115, 0.12, 0.3, paint, 0, 0, -0.08);
  box(gun, 0.125, 0.03, 0.31, pink, 0, -0.06, -0.08);
  box(gun, 0.03, 0.025, 0.28, chrome, 0, 0.072, -0.08);
  box(gun, 0.09, 0.09, 0.06, paint, 0, 0.005, -0.25).rotation.x = 0.12;
  // the glass tank on top with the tool's goo glowing in it, two chrome bands
  const tank = cyl(gun, 0.038, 0.038, 0.16, 12, new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 0, roughness: 0.05, transparent: true, opacity: 0.35 }), 0, 0.115, -0.06);
  core = cyl(gun, 0.028, 0.028, 0.14, 10, glow, 0, 0.115, -0.06); void tank;
  for (const z of [-0.14, 0.02]) cyl(gun, 0.044, 0.044, 0.018, 12, chrome, 0, 0.115, z);
  // grip, trigger guard, a vent stack at the back
  const grip = box(gun, 0.065, 0.15, 0.075, dark, 0, -0.12, 0.03); grip.rotation.x = -0.32;
  box(gun, 0.02, 0.05, 0.07, chrome, 0, -0.085, -0.04);
  for (let i = 0; i < 3; i++) box(gun, 0.1, 0.01, 0.012, dark, 0, 0.03 - i * 0.025, 0.074);
  // a little screen on the side: the tool's name
  const c = document.createElement('canvas'); c.width = 128; c.height = 48; scrTex = new THREE.CanvasTexture(c); scrTex.colorSpace = THREE.SRGBColorSpace;
  screen = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.04), new THREE.MeshBasicMaterial({ map: scrTex })); screen.position.set(-0.0585, 0.015, -0.07); screen.rotation.y = -Math.PI / 2; gun.add(screen);
  // the emitter ring every head sits in
  ring = new THREE.Mesh(new THREE.TorusGeometry(0.048, 0.014, 6, 14), glow); ring.position.set(0, 0.012, -0.29); gun.add(ring);
  // heads: claw (grab), funnel (plop), fork (yeet), crystal (wand)
  const hg = new THREE.Group(); gun.add(hg); heads.grab = hg;
  for (let i = 0; i < 3; i++) { const a = (i / 3) * Math.PI * 2 + Math.PI / 2, pr = new THREE.Group(); pr.position.set(Math.cos(a) * 0.05, 0.012 + Math.sin(a) * 0.05, -0.3); pr.rotation.z = a - Math.PI / 2; const f = box(pr, 0.018, 0.012, 0.09, chrome, 0, 0, -0.04); f.rotation.x = -0.35; box(pr, 0.022, 0.02, 0.02, pink, 0, -0.016, -0.085); hg.add(pr); prongs.push(pr); }
  const hp = new THREE.Group(); gun.add(hp); heads.plop = hp;
  const fun = cyl(hp, 0.075, 0.045, 0.07, 12, chrome, 0, 0.012, -0.33); fun.rotation.x = -Math.PI / 2;
  cyl(hp, 0.068, 0.068, 0.012, 12, glow, 0, 0.012, -0.366);
  const hy = new THREE.Group(); gun.add(hy); heads.yeet = hy;
  for (const s of [-1, 1]) { box(hy, 0.016, 0.016, 0.11, chrome, s * 0.032, 0.012, -0.34); box(hy, 0.024, 0.024, 0.024, glow, s * 0.032, 0.012, -0.4); }
  box(hy, 0.08, 0.016, 0.016, chrome, 0, 0.012, -0.29);
  const hw = new THREE.Group(); gun.add(hw); heads.wand = hw;
  const cr = new THREE.Mesh(new THREE.OctahedronGeometry(0.045), mat(0xff4fd8, { e: 0xff4fd8, ei: 0.9, m: 0.1, r: 0.1, flat: true })); cr.scale.set(0.8, 0.8, 1.6); cr.position.set(0, 0.012, -0.36); hw.add(cr); glowMats.push(cr.material); heads.wandGem = cr;
  root.scale.setScalar(0.62);
  scene.add(root);
  setTool('grab', true);
  return root;
}
function drawScreen(t) {
  const c = scrTex.image, x = c.getContext('2d'), col = '#' + new THREE.Color(TOOLS[t].col).getHexString();
  x.fillStyle = '#120818'; x.fillRect(0, 0, 128, 48); x.strokeStyle = col; x.lineWidth = 4; x.strokeRect(2, 2, 124, 44);
  x.fillStyle = col; x.font = 'bold 15px "Comic Neue", "Comic Sans MS", cursive'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(TOOLS[t].name, 64, 25);
  scrTex.needsUpdate = true;
}
export function setTool(t, quiet) {
  if (!root || !TOOLS[t]) return;
  if (!quiet && t !== st.tool) st.swap = 1;
  st.tool = t;
  for (const k of Object.keys(TOOLS)) heads[k].visible = k === t;
  for (const m of glowMats) if (m !== (heads.wandGem && heads.wandGem.material)) { m.color.setHex(TOOLS[t].col); m.emissive.setHex(TOOLS[t].col); }
  drawScreen(t);
}
export const vmKick = (k = 1) => { st.kick = Math.min(1.5, st.kick + k); };
export const vmHold = (on) => { st.hold = on ? 1 : 0; };
export function vmLook(mx, my) { st.swayX += mx * 0.00012; st.swayY += my * 0.00012; }
export function vmVisible(v) { if (root) root.visible = v; }
// dt: seconds, moving: 0..1 (flying)
export function updateVM(dt) {
  if (!root) return;
  st.t += dt; st.kick = Math.max(0, st.kick - dt * 6); st.swap = Math.max(0, st.swap - dt * 4);
  const mv = st.moving; st.bob += dt * (4 + mv * 6);
  st.swayX *= Math.pow(0.0005, dt); st.swayY *= Math.pow(0.0005, dt);
  const dip = Math.sin(st.swap * Math.PI) * 0.18; // (down and back up when you swap)
  root.position.set(0.2 - st.swayX * 0.6 + Math.sin(st.bob) * 0.005 * (0.3 + mv), -0.165 + st.swayY * 0.6 - Math.abs(Math.cos(st.bob)) * 0.006 * (0.3 + mv) - dip, -0.42 + st.kick * 0.05);
  root.rotation.set(0.05 + st.kick * 0.18 + st.swayY * 2 + dip * 1.5, 0.16 + st.swayX * 2, -0.06 + Math.sin(st.bob * 0.5) * 0.01); // (pointed in at the crosshair, so you see its side)
  if (st.hold) { root.position.x += (Math.random() - 0.5) * 0.003; root.position.y += (Math.random() - 0.5) * 0.003; } // (straining)
  for (const [i, p] of prongs.entries()) p.rotation.y = st.hold ? Math.sin(st.t * 40 + i) * 0.08 : 0;
  ring.rotation.z += dt * (st.hold ? 9 : 1.5);
  const pulse = 1.1 + Math.sin(st.t * (st.hold ? 18 : 3)) * (st.hold ? 0.6 : 0.25);
  for (const m of glowMats) m.emissiveIntensity = pulse;
  if (heads.wandGem) heads.wandGem.rotation.z += dt * 1.2;
}
export const setVMMoving = (m) => { st.moving = m; };
// where the beam leaves the tool, on screen: NDC of the muzzle through the tool's own camera
const _v = new THREE.Vector3();
export function muzzleNDC(vmCam) { if (!root) return null; root.updateMatrixWorld(true); _v.copy(MUZZLE); root.children[0].localToWorld(_v); return _v.project(vmCam); }
