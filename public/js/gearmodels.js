// Models for the new gear, from real references then made fun:
//   Big Laser Pointer  an office laser pointer (aluminium pen body, knurled head, pocket clip, push button) scaled to
//                      the size of a leg, with a toy pistol grip and two D-cells duct-taped on, a charge meter, a cat charm
//   Instant Camera     a boxy instant camera (lens barrel, flash window, viewfinder, shutter, print slot, strap)
//   photo frame        the giant instant print it spits out: thick bottom chin, a kickstand, two bits of tape
//   calculator         a scientific calculator (solar strip, LCD, 6 x 7 keys, big orange =)
//   NV goggles         dual-tube night vision goggles on a flip-down mount (eyecups, objectives, IR lamp, battery)
// Weapon space like every gun: forward = -Z, up = +Y, the grip at the origin. Real sizes in metres.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { box, cyl, sphere, ring, lathe, slab, strip, tube, mat } from './blades/kit.js';
import { jankify } from './jank.js';
import { authored, ownMat, nodeIn } from './glbkit.js'; // the Blender versions (tools/blender/make_laser.py, make_gear.py)

const glowMat = (color) => { const m = new THREE.MeshBasicMaterial({ color }); return m; }; // own copy: these get brightened
const noWrap = (m) => { m.userData.noWrap = true; return m; };
function rbox(w, h, d, r, color, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 2, r), mat(color));
  m.position.set(x, y, z);
  return m;
}
function canvasTex(w, h, draw, nearest = false) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  if (nearest) t.magFilter = THREE.NearestFilter;
  t.anisotropy = 4;
  return t;
}
// a texture on a patch of a cylinder's surface round the z axis (stickers on round things). theta 0 = +x side... see below
function wrapPatch(r, len, a0, a1, z, tex) {
  // CylinderGeometry: x = r sin(theta), z = r cos(theta); rotated so its axis is z: y = -r cos(theta).
  // theta = PI/2: +x side, 3PI/2: -x side, PI: top (+y), 0: bottom
  const g = new THREE.CylinderGeometry(r, r, len, 10, 1, true, a0, a1 - a0);
  g.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(g, jankify(new THREE.MeshLambertMaterial({ map: tex, transparent: true, alphaTest: 0.3 })));
  m.position.z = z;
  return m;
}

// ================================================================ Big Laser Pointer
let warnTex = null;
function laserWarning() { // the yellow class-whatever warning sticker every laser pointer has, in the game's voice
  return warnTex || (warnTex = canvasTex(256, 96, (x, w, h) => {
    x.fillStyle = '#ffd400'; x.fillRect(0, 0, w, h);
    x.strokeStyle = '#111'; x.lineWidth = 5; x.strokeRect(4, 4, w - 8, h - 8);
    // the starburst-in-a-triangle laser symbol
    x.fillStyle = '#111'; x.beginPath(); x.moveTo(48, 14); x.lineTo(86, 80); x.lineTo(10, 80); x.closePath(); x.fill();
    x.fillStyle = '#ffd400'; x.beginPath(); x.moveTo(48, 26); x.lineTo(76, 74); x.lineTo(20, 74); x.closePath(); x.fill();
    x.strokeStyle = '#111'; x.lineWidth = 3;
    for (let i = 0; i < 10; i++) { const a = (i / 10) * Math.PI * 2; x.beginPath(); x.moveTo(48 + Math.cos(a) * 5, 58 + Math.sin(a) * 5); x.lineTo(48 + Math.cos(a) * 13, 58 + Math.sin(a) * 13); x.stroke(); }
    x.beginPath(); x.moveTo(48, 58); x.lineTo(80, 58); x.stroke();
    x.fillStyle = '#111'; x.font = 'bold 22px sans-serif'; x.fillText('CAUTION', 98, 34);
    x.font = 'bold 13px sans-serif'; x.fillText('LASER RADIATION', 98, 52);
    x.fillText('DO NOT STARE INTO', 98, 67); x.fillText('BEAM. CLASS 9000', 98, 82);
  }));
}
export function laserBuild(g) {
  const BODY = 0xc2287e, CHROME = 0xd2d8e0, DARK = 0x1c1c22, TAPE = 0xa4aab2, RUBBER = 0x26262c;
  // the pen: tail cap, anodized body, flared head with knurling, a lens with the emitter in it
  g.add(lathe([[0, 0.322], [0.02, 0.32], [0.034, 0.312], [0.04, 0.3], [0.04, 0.262], [0.035, 0.257]], CHROME, { segs: 16 }));
  g.add(lathe([[0.035, 0.257], [0.042, 0.252], [0.042, -0.296], [0.044, -0.3]], BODY, { segs: 16 }));
  g.add(lathe([[0.044, -0.3], [0.05, -0.318], [0.053, -0.33], [0.053, -0.392], [0.05, -0.402], [0.041, -0.408], [0.036, -0.408]], CHROME, { segs: 16 }));
  for (let i = 0; i < 6; i++) g.add(ring(0.0535, 0.0028, 0x9aa1aa, { axis: 'z', z: -0.338 - i * 0.0095, segs: 16, tubeSegs: 4 }));
  g.add(ring(0.0425, 0.003, CHROME, { axis: 'z', z: -0.12, segs: 16, tubeSegs: 4 })); // a trim band
  const glass = new THREE.Mesh(new THREE.CircleGeometry(0.036, 16), mat(0x0c2414)); glass.position.z = -0.407; glass.rotation.y = Math.PI; g.add(glass);
  const emit = noWrap(new THREE.Mesh(new THREE.CircleGeometry(0.013, 12), glowMat(0x1d7a10))); emit.position.z = -0.4085; emit.rotation.y = Math.PI; g.add(emit);
  const glint = noWrap(new THREE.Mesh(new THREE.CircleGeometry(0.006, 6), glowMat(0xd8ffe0))); glint.position.set(0.014, 0.014, -0.4086); glint.rotation.y = Math.PI; g.add(glint);
  // pocket clip along the top from the tail cap (a pen clip, so it has the little ball at the end)
  g.add(box(0.016, 0.006, 0.05, CHROME, 0, 0.044, 0.27));
  g.add(box(0.012, 0.004, 0.17, CHROME, 0, 0.049, 0.17));
  const tipB = sphere(0.008, CHROME, 0, 0.047, 0.083); tipB.scale.set(1, 0.7, 1.4); g.add(tipB);
  // the push button: a chrome collar and a fat red rubber dome (pressed while you charge)
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.017, 0.019, 0.008, 14), mat(CHROME)); collar.position.set(0, 0.043, -0.07); g.add(collar);
  const btn = new THREE.Group(); btn.position.set(0, 0.047, -0.07); g.add(btn);
  const dome = sphere(0.0135, 0xff2d3a); dome.scale.set(1, 0.55, 1); btn.add(dome);
  g.userData.button = btn;
  // the warning sticker, on the side you can see
  g.add(wrapPatch(0.0428, 0.15, Math.PI * 1.5 - 0.55, Math.PI * 1.5 + 0.55, -0.2, laserWarning()));
  // charge meter: a strip of 5 LEDs on the visible side, near your hand. weapons.js lights them as you charge
  g.add(box(0.012, 0.022, 0.12, DARK, -0.043, 0.008, 0.11));
  const leds = [];
  for (let i = 0; i < 5; i++) { const l = noWrap(new THREE.Mesh(new THREE.BoxGeometry(0.004, 0.012, 0.016), glowMat(0x0b2a08))); l.position.set(-0.0495, 0.008, 0.16 - i * 0.024); g.add(l); leds.push(l); }
  g.userData.leds = leds;
  // a toy pistol grip, duct-taped on (two tape bands, a loose flap)
  g.add(slab([[0.04, -0.028], [-0.03, -0.028], [-0.022, -0.06], [0.0, -0.19], [0.055, -0.2], [0.07, -0.18], [0.045, -0.06]], 0.034, RUBBER, { bevel: 0.004 }));
  for (let i = 0; i < 5; i++) g.add(box(0.04, 0.004, 0.006, 0x3a3a42, 0, -0.08 - i * 0.022, 0.01 + i * 0.009)); // finger ridges
  for (const z of [-0.02, 0.05]) g.add(cyl(0.0455, 0.026, TAPE, 0, 0, z, 16));
  const flap = box(0.024, 0.002, 0.03, TAPE, 0.03, -0.042, 0.06); flap.rotation.set(0.4, 0.2, -0.6); g.add(flap);
  // the "capacitor": two D-cells taped under the front, a red + black wire into the body
  for (const sx of [-1, 1]) {
    const x = sx * 0.024, y = -0.064;
    g.add(cyl(0.022, 0.13, 0x2a2a2e, x, y, -0.21, 12));
    g.add(cyl(0.0225, 0.04, 0xe08a1a, x, y, -0.255, 12)); // copper top
    g.add(cyl(0.007, 0.008, 0xcfcfcf, x, y, -0.279, 8)); // + terminal
  }
  for (const z of [-0.17, -0.25]) { // tape round the pen and both cells: an oval sleeve
    const tg = new THREE.CylinderGeometry(1, 1, 0.026, 18, 1, true); tg.rotateX(Math.PI / 2);
    const t = new THREE.Mesh(tg, jankify(new THREE.MeshLambertMaterial({ color: TAPE, flatShading: true, side: THREE.DoubleSide }))); t.scale.set(0.05, 0.067, 1); t.position.set(0, -0.022, z); g.add(t);
  }
  g.add(tube([[0.024, -0.064, -0.283], [0.03, -0.05, -0.3], [0.022, -0.03, -0.3], [0.01, -0.03, -0.29]], 0.003, 0xe02020));
  g.add(tube([[-0.024, -0.064, -0.142], [-0.03, -0.045, -0.13], [-0.02, -0.035, -0.12]], 0.003, 0x151515));
  // lanyard loop + a little cat charm off the tail cap (it swings: weapons.js / remote.js)
  g.add(ring(0.012, 0.0025, CHROME, { axis: 'x', z: 0.33 }));
  const charm = new THREE.Group(); charm.position.set(0, -0.006, 0.338); g.add(charm);
  for (let i = 0; i < 3; i++) charm.add(ring(0.005, 0.0013, CHROME, { axis: i % 2 ? 'x' : 'z', y: -0.008 - i * 0.008 }));
  const cat = new THREE.Group(); cat.position.y = -0.04; charm.add(cat);
  const head = sphere(0.016, 0xffffff); head.scale.set(1.15, 1, 0.8); cat.add(head);
  for (const sx of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.ConeGeometry(0.007, 0.012, 4), mat(0xffffff)); ear.position.set(sx * 0.01, 0.015, 0); ear.rotation.z = -sx * 0.35; cat.add(ear);
    const eye = sphere(0.0028, 0x111111, sx * 0.0065, 0.002, -0.0125); cat.add(eye);
  }
  cat.add(sphere(0.003, 0xff7ab8, 0, -0.003, -0.0135));
  g.userData.charm = charm;
  g.userData.orb = laserOrb(g); g.userData.emit = emit;
  g.userData.muzzle = new THREE.Vector3(0, 0, -0.42);
  g.userData.len = 0.82;
}

// charge orb at the lens (hidden till you charge): additive, grows with the charge
function laserOrb(g) {
  const orb = noWrap(new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), new THREE.MeshBasicMaterial({ color: 0x39ff14, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false })));
  orb.position.z = -0.42; orb.scale.setScalar(0.001); orb.visible = false; g.add(orb);
  return orb;
}

// ================================================================ Instant Camera
let camLabel = null;
export function instantCamera() {
  const bl = authored('x_camera');
  if (bl) { // the Blender camera: the same hooks on its own nodes (photo.js flashes it, kicks the shutter, slides the print out)
    const g = new THREE.Group(); g.add(bl.obj);
    const pm = new THREE.MeshBasicMaterial({ color: 0x222222 });
    const flash = ownMat(g, 'flash', glowMat(0xcfc8b8)), pic = ownMat(g, 'pic', pm), shutter = nodeIn(g, 'shutter'), print = nodeIn(g, 'print');
    if (flash && pic && shutter && print) {
      print.visible = false;
      Object.assign(g.userData, { flash, shutter, print, pic, lensAt: new THREE.Vector3(...(Array.isArray(bl.meta.lensAt) ? bl.meta.lensAt : [0, -0.006, -0.065])), glb: 'blender' });
      return g;
    }
  }
  const g = new THREE.Group();
  const CREAM = 0xf3eee2, CHAR = 0x2c2c33, LILAC = 0xc9a7ff;
  // body: a chunky two-tone brick, the top deck sloping back over the film door
  g.add(rbox(0.118, 0.07, 0.078, 0.011, CREAM, 0, -0.012, 0));
  g.add(rbox(0.118, 0.034, 0.07, 0.009, CHAR, 0, 0.034, 0.004));
  g.add(rbox(0.11, 0.01, 0.07, 0.004, CHAR, 0, -0.049, 0.002)); // base plate
  // the stripes down the front (game palette), lens over the top of them
  ['#ff4fd8', '#ffe14d', '#4fd8ff'].forEach((c, i) => g.add(box(0.008, 0.07, 0.002, new THREE.Color(c).getHex(), -0.012 + i * 0.008, -0.012, -0.0395)));
  // lens barrel: a stepped tube with a rubber grip ring, black glass with a highlight
  g.add(lathe([[0.034, -0.039], [0.034, -0.046], [0.031, -0.048], [0.031, -0.06], [0.029, -0.064], [0.025, -0.064]], 0x3a3a42, { segs: 20, y: -0.006 }));
  g.add(cyl(0.0345, 0.01, 0x18181c, 0, -0.006, -0.052, 20)); // rubber grip ring
  const lens = new THREE.Mesh(new THREE.CircleGeometry(0.025, 20), jankify(new THREE.MeshLambertMaterial({ color: 0x0b0e1a, emissive: 0x05060a }))); lens.position.set(0, -0.006, -0.0635); lens.rotation.y = Math.PI; g.add(lens);
  const hi = noWrap(new THREE.Mesh(new THREE.CircleGeometry(0.007, 10), glowMat(0x6a7aa8))); hi.position.set(0.009, 0.003, -0.064); hi.rotation.y = Math.PI; g.add(hi);
  g.add(ring(0.016, 0.0016, 0x55607a, { axis: 'z', y: -0.006, z: -0.0636, segs: 16 }));
  // flash window top left (it fires when you snap), viewfinder top right, red shutter button on the front
  g.add(box(0.044, 0.022, 0.004, CHAR, -0.033, 0.034, -0.032));
  const flash = noWrap(new THREE.Mesh(new THREE.BoxGeometry(0.038, 0.016, 0.003), glowMat(0xcfc8b8))); flash.position.set(-0.033, 0.034, -0.0345); g.add(flash);
  for (let i = 0; i < 5; i++) g.add(box(0.001, 0.016, 0.0035, 0xb8b0a0, -0.049 + i * 0.008, 0.034, -0.0352)); // the ridges in the flash diffuser
  g.add(box(0.018, 0.014, 0.004, 0x111114, 0.04, 0.036, -0.033));
  g.add(box(0.012, 0.009, 0.002, 0x2a3a5a, 0.04, 0.036, -0.0352));
  const shutter = new THREE.Group(); shutter.position.set(0.042, 0.008, -0.04); g.add(shutter);
  const sb = cyl(0.008, 0.008, 0xff2d6a, 0, 0, -0.002, 14); shutter.add(sb); shutter.add(ring(0.0085, 0.0015, 0xb01a40, { axis: 'z', z: 0.001, segs: 14 }));
  // print slot under the lens: the photo slides out of here
  g.add(box(0.09, 0.006, 0.004, 0x0a0a0c, 0, -0.04, -0.039));
  // strap lugs + a wrist strap (pink, of course)
  for (const sx of [-1, 1]) g.add(ring(0.006, 0.0018, 0xb8bcc4, { axis: 'z', x: sx * 0.061, y: 0.03, z: 0.02 }));
  g.add(tube([[0.061, 0.026, 0.02], [0.075, 0.0, 0.03], [0.07, -0.05, 0.04], [0.05, -0.075, 0.035], [0.035, -0.07, 0.025]], 0.004, 0xff4fd8, { segs: 18 }));
  // name on the top deck
  const lab = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.012), new THREE.MeshBasicMaterial({ map: camLabel || (camLabel = canvasTex(256, 52, (x, w, h) => { x.fillStyle = '#2c2c33'; x.fillRect(0, 0, w, h); x.fillStyle = '#ffe14d'; x.font = 'bold italic 34px sans-serif'; x.textAlign = 'center'; x.fillText('SNAPPY 9000', w / 2, 38); })) }));
  lab.position.set(0.012, 0.052, -0.01); lab.rotation.x = -Math.PI / 2; g.add(lab);
  // the back (what you see when you take a photo): rubber viewfinder eyepiece, a film counter, the film door seam, a sticker
  g.add(box(0.026, 0.02, 0.008, 0x111114, 0.038, 0.036, 0.04));
  g.add(box(0.016, 0.011, 0.002, 0x2a3a5a, 0.038, 0.036, 0.0445));
  const ctr = noWrap(new THREE.Mesh(new THREE.PlaneGeometry(0.012, 0.009), new THREE.MeshBasicMaterial({ map: canvasTex(32, 24, (x) => { x.fillStyle = '#101010'; x.fillRect(0, 0, 32, 24); x.fillStyle = '#ff8a2a'; x.font = 'bold 20px monospace'; x.fillText('1', 10, 19); }, true) })));
  ctr.position.set(-0.04, 0.036, 0.0396); g.add(ctr);
  g.add(box(0.1, 0.002, 0.002, 0x8a8478, 0, -0.005, 0.0395)); // film door seam
  g.add(box(0.016, 0.006, 0.006, 0x8a8478, -0.045, -0.025, 0.04)); // door latch
  const smile = new THREE.Mesh(new THREE.PlaneGeometry(0.05, 0.022), new THREE.MeshBasicMaterial({ map: canvasTex(200, 88, (x, w, h) => { x.fillStyle = '#ffe14d'; x.fillRect(0, 0, w, h); x.strokeStyle = '#111'; x.lineWidth = 6; x.strokeRect(3, 3, w - 6, h - 6); x.fillStyle = '#111'; x.font = 'bold 26px sans-serif'; x.textAlign = 'center'; x.fillText('SAY', w / 2, 38); x.fillText('CHEESE', w / 2, 70); }) }));
  smile.position.set(0.012, -0.024, 0.0396); smile.rotation.z = -0.12; g.add(smile);
  // the print (hidden till it comes out): a white card, the picture on it
  const print = new THREE.Group(); print.visible = false; g.add(print);
  const card = new THREE.Mesh(new THREE.BoxGeometry(0.086, 0.0012, 0.104), mat(0xf8f6ee)); card.position.z = -0.052; print.add(card);
  const pic = new THREE.Mesh(new THREE.PlaneGeometry(0.076, 0.076), new THREE.MeshBasicMaterial({ color: 0x222222 })); pic.rotation.x = -Math.PI / 2; pic.position.set(0, 0.0008, -0.058); print.add(pic);
  print.position.set(0, -0.04, -0.03);
  Object.assign(g.userData, { flash, shutter, print, pic, lensAt: new THREE.Vector3(0, -0.006, -0.065) });
  return g;
}

// ================================================================ the printed photo: a giant instant print on a kickstand
// faces -Z (the way it was printed toward). opening = the picture: PIC x PIC, its bottom edge CHIN up off the floor
export const FRAME = { pic: 1.9, side: 0.1, top: 0.1, chin: 0.36, thick: 0.05 };
let backTex = null;
const PORTAL_VS = `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
// the picture: wobbles like it's not quite solid, develops in from brown when printed, sparkles round the edge, fades at the end
const PORTAL_FS = `
uniform sampler2D map; uniform float uT, uDev, uFade, uHave;
varying vec2 vUv;
float hash(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5); }
void main() {
  vec2 uv = vUv;
  float w = 0.006 * sin(uv.y * 18.0 + uT * 3.1) + 0.004 * sin(uv.x * 23.0 - uT * 2.3);
  uv += vec2(w, w * 0.7);
  vec3 c = uHave > 0.5 ? texture2D(map, clamp(uv, 0.002, 0.998)).rgb : vec3(0.45, 0.36, 0.3);
  vec3 brown = vec3(0.23, 0.15, 0.1);
  c = mix(brown, c, smoothstep(0.0, 1.0, uDev));
  float e = min(min(vUv.x, 1.0 - vUv.x), min(vUv.y, 1.0 - vUv.y));
  float rim = smoothstep(0.06, 0.0, e) * (0.55 + 0.45 * sin(uT * 6.0 + (vUv.x + vUv.y) * 30.0));
  float sp = step(0.985, hash(floor(vUv * 60.0) + floor(uT * 8.0))) * smoothstep(0.12, 0.0, e);
  c += vec3(1.0, 0.31, 0.85) * rim * 0.9 + vec3(1.0) * sp;
  c += vec3(0.6, 0.9, 1.0) * 0.02 * sin(uv.y * 140.0 + uT * 9.0); // faint scanlines: it's not just paper
  gl_FragColor = vec4(c, uFade);
  #include <colorspace_fragment>
}`;
export function photoFrame(tex) {
  const g = new THREE.Group(), F = FRAME, W = F.pic + F.side * 2, Hh = F.chin + F.pic + F.top;
  const inner = new THREE.Group(); inner.rotation.x = 0.06; g.add(inner); // leans back on its stand a little
  const bl = authored('x_photoframe'); // the Blender print: card, back, tape, kickstand, feet (the picture is ours)
  if (bl) { inner.add(bl.obj); g.userData.glb = 'blender'; } else frameCard(inner, F, W, Hh);
  // the picture, both ways round (from behind you see it mirrored, like a window)
  const pm = new THREE.ShaderMaterial({
    uniforms: { map: { value: tex || null }, uT: { value: 0 }, uDev: { value: 0 }, uFade: { value: 1 }, uHave: { value: tex ? 1 : 0 } },
    vertexShader: PORTAL_VS, fragmentShader: PORTAL_FS, side: THREE.DoubleSide, transparent: true,
  });
  const pic = noWrap(new THREE.Mesh(new THREE.PlaneGeometry(F.pic, F.pic), pm));
  pic.position.set(0, F.chin + F.pic / 2, 0); pic.rotation.y = Math.PI; // its front faces -Z
  inner.add(pic);
  // a soft pink glow on the floor in front of it
  const pool = noWrap(new THREE.Mesh(new THREE.CircleGeometry(1.1, 20), new THREE.MeshBasicMaterial({ color: 0xff4fd8, transparent: true, opacity: 0.25, blending: THREE.AdditiveBlending, depthWrite: false })));
  pool.rotation.x = -Math.PI / 2; pool.position.set(0, 0.03, -0.6); pool.scale.set(1, 0.6, 1); g.add(pool);
  Object.assign(g.userData, { pic, pm, inner, pool, height: Hh });
  return g;
}
// the code-built card: one slab with a square hole for the picture so the edges have thickness, its back, tape, stand
function frameCard(inner, F, W, Hh) {
  // the card: one slab with a square hole for the picture so the edges have thickness
  const outer = new THREE.Shape([[-W / 2, 0], [W / 2, 0], [W / 2, Hh], [-W / 2, Hh]].map((p) => new THREE.Vector2(p[0], p[1])));
  const hole = new THREE.Path([[-F.pic / 2, F.chin], [-F.pic / 2, F.chin + F.pic], [F.pic / 2, F.chin + F.pic], [F.pic / 2, F.chin]].map((p) => new THREE.Vector2(p[0], p[1])));
  outer.holes.push(hole);
  const cg = new THREE.ExtrudeGeometry(outer, { depth: F.thick, bevelEnabled: true, bevelThickness: 0.008, bevelSize: 0.008, bevelSegments: 1 });
  cg.translate(0, 0, -F.thick / 2);
  inner.add(new THREE.Mesh(cg, mat(0xf8f5ec)));
  // the back: dark film backing with the print on it
  const bm = new THREE.MeshBasicMaterial({ map: backTex || (backTex = canvasTex(256, 290, (x, w, h) => {
    x.fillStyle = '#26262c'; x.fillRect(0, 0, w, h);
    x.fillStyle = '#d8d4cc'; x.textAlign = 'center'; x.font = 'bold 22px sans-serif'; x.fillText('JANKFIRE', w / 2, 120);
    x.font = 'bold 14px sans-serif'; x.fillText('INSTANT FILM', w / 2, 142); x.fillText('DO NOT BEND · DO NOT ENTER', w / 2, 162);
    x.font = '12px sans-serif'; x.fillText('(you can enter)', w / 2, 180);
    for (let i = 0; i < 30; i++) x.fillRect(70 + i * 4, 220, i % 3 ? 2 : 3, 26);
  })) });
  const back = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.04, Hh - 0.04), bm);
  back.position.set(0, Hh / 2, F.thick / 2 + 0.011);
  inner.add(back);
  // two strips of tape across the top corners (it's a photo: someone stuck it up)
  for (const sx of [-1, 1]) {
    const t = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.12, 0.006), new THREE.MeshLambertMaterial({ color: 0xe8e2c8, transparent: true, opacity: 0.78 }));
    t.position.set(sx * (W / 2 - 0.08), Hh - 0.05, -F.thick / 2 - 0.014); t.rotation.z = -sx * 0.7; inner.add(t);
  }
  // kickstand behind it + rubber feet
  const leg = box(0.14, Hh * 0.82, 0.035, 0x5a4a3a, 0, 0, 0); leg.geometry.translate(0, -Hh * 0.41, 0);
  const legP = new THREE.Group(); legP.position.set(0, Hh * 0.82, F.thick / 2 + 0.02); legP.rotation.x = -0.42; legP.add(leg); inner.add(legP);
  legP.add(box(0.06, 0.06, 0.02, 0x8a7a68, 0, -0.04, -0.02)); // hinge
  for (const sx of [-1, 1]) inner.add(box(0.12, 0.05, 0.12, 0x222226, sx * (W / 2 - 0.12), 0.02, 0));
}

// ================================================================ calculator
let keyTex = null, keyGeo = null;
const KEYS = [ // 6 x 7, top to bottom. [label, colour]
  [['SHIFT', '#ffd23b'], ['ALPHA', '#ff4f7a'], ['◀', '#4a4e66'], ['▶', '#4a4e66'], ['MODE', '#4a4e66'], ['ON', '#4a4e66']],
  [['x²', '#4a4e66'], ['√', '#4a4e66'], ['xʸ', '#4a4e66'], ['log', '#4a4e66'], ['ln', '#4a4e66'], ['sin', '#4a4e66']],
  [['7', '#e3e6ee'], ['8', '#e3e6ee'], ['9', '#e3e6ee'], ['DEL', '#5b8cff'], ['AC', '#ff5a4a'], ['(', '#4a4e66']],
  [['4', '#e3e6ee'], ['5', '#e3e6ee'], ['6', '#e3e6ee'], ['×', '#a8b0d4'], ['÷', '#a8b0d4'], [')', '#4a4e66']],
  [['1', '#e3e6ee'], ['2', '#e3e6ee'], ['3', '#e3e6ee'], ['+', '#a8b0d4'], ['−', '#a8b0d4'], ['%', '#4a4e66']],
  [['0', '#e3e6ee'], ['.', '#e3e6ee'], ['EXP', '#e3e6ee'], ['Ans', '#a8b0d4'], ['=', '#ff8a2a'], ['=', '#ff8a2a']],
];
// one atlas for every key top, one merged mesh for all the keys (bodies take the top's colour from the atlas too)
function calcKeys() {
  if (keyGeo) return keyGeo;
  const cols = 6, rows = KEYS.length, cw = 64, ch = 48;
  keyTex = canvasTex(cols * cw, rows * ch, (x) => {
    KEYS.forEach((row, r) => row.forEach(([lab, col], c) => {
      const X = c * cw, Y = r * ch;
      x.fillStyle = col; x.fillRect(X, Y, cw, ch);
      x.fillStyle = 'rgba(255,255,255,0.25)'; x.fillRect(X + 3, Y + 3, cw - 6, 6);
      x.fillStyle = 'rgba(0,0,0,0.25)'; x.fillRect(X, Y + ch - 5, cw, 5);
      const light = col === '#e3e6ee' || col === '#ffd23b' || col === '#a8b0d4';
      x.fillStyle = light ? '#1a1c28' : '#ffffff'; x.font = `bold ${lab.length > 3 ? 15 : lab.length > 1 ? 20 : 28}px sans-serif`;
      x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(lab, X + cw / 2, Y + ch / 2 + 1);
    }));
  });
  const parts = [];
  const W = 0.021, Hk = 0.016, gx = 0.0235, gy = 0.0215;
  KEYS.forEach((row, r) => row.forEach((k, c) => {
    if (r === KEYS.length - 1 && c === 5) return; // the = key is two wide
    const wide = r === KEYS.length - 1 && c === 4;
    const kw = wide ? W + gx : W;
    const b = new THREE.BoxGeometry(kw, Hk, 0.007);
    const u0 = c / 6, u1 = (c + (wide ? 2 : 1)) / 6, v1 = 1 - r / KEYS.length, v0 = 1 - (r + 1) / KEYS.length;
    const uv = b.attributes.uv;
    for (let i = 0; i < uv.count; i++) uv.setXY(i, u0 + (u1 - u0) * (0.1 + 0.8 * uv.getX(i)), v0 + (v1 - v0) * (0.1 + 0.8 * uv.getY(i)));
    b.translate((c - 2.5) * gx + (wide ? gx / 2 : 0), -0.032 - r * gy, -0.0175);
    parts.push(b);
  }));
  keyGeo = mergeGeometries(parts);
  return keyGeo;
}
// the LCD: a canvas we can write sums on. lines = [big, small]
export function lcdTexture(lines = ['0.', ''], w = 256, h = 112) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.userData = { c, write(L) {
    const x = c.getContext('2d');
    x.fillStyle = '#b9c8a2'; x.fillRect(0, 0, w, h);
    x.fillStyle = 'rgba(0,0,0,0.06)'; for (let i = 0; i < w; i += 4) x.fillRect(i, 0, 1, h); // the segment grid you can just see
    x.fillStyle = '#1d2418'; x.textAlign = 'right'; x.textBaseline = 'alphabetic';
    x.font = `bold ${Math.round(h * 0.2)}px monospace`; x.fillText(L[1] || '', w - 10, h * 0.3);
    let fs = Math.round(h * 0.5); x.font = `bold ${fs}px monospace`;
    while (x.measureText(L[0]).width > w - 20 && fs > 12) { fs -= 2; x.font = `bold ${fs}px monospace`; }
    x.fillText(L[0], w - 10, h * 0.86);
    t.needsUpdate = true;
  } };
  t.userData.write(lines);
  return t;
}
let lcdShared = null;
export function calculator(lcd) {
  const bl = authored('x_calc');
  if (bl) { // the Blender calculator: its LCD shows the live sum (quiz.js writes the texture)
    const g = new THREE.Group(); g.add(bl.obj);
    const lm = new THREE.MeshBasicMaterial({ map: lcd || lcdShared || (lcdShared = lcdTexture()) });
    if (ownMat(g, 'screen', lm)) { g.userData.screen = lm; g.userData.glb = 'blender'; return g; }
  }
  const g = new THREE.Group();
  const BODY = 0x23263a, FACE = 0x2f3350;
  g.add(rbox(0.152, 0.3, 0.026, 0.01, BODY, 0, -0.05, 0));
  g.add(rbox(0.142, 0.135, 0.004, 0.0015, FACE, 0, 0.032, -0.0135)); // top bezel
  // solar strip, a name, the LCD
  g.add(box(0.07, 0.018, 0.003, 0x3a2416, 0.02, 0.083, -0.016));
  for (let i = 1; i < 4; i++) g.add(box(0.0012, 0.018, 0.0035, 0x6a4a2a, 0.02 - 0.035 + i * 0.0175, 0.083, -0.0162));
  const lm = new THREE.MeshBasicMaterial({ map: lcd || lcdShared || (lcdShared = lcdTexture()) });
  const scr = noWrap(new THREE.Mesh(new THREE.PlaneGeometry(0.124, 0.055), lm)); scr.position.set(0, 0.04, -0.0172); scr.rotation.y = Math.PI; g.add(scr);
  g.add(box(0.13, 0.062, 0.002, 0x15161f, 0, 0.04, -0.016)); // the frame round it
  const nm = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.012), new THREE.MeshBasicMaterial({ map: canvasTex(200, 40, (x, w, h) => { x.fillStyle = '#2f3350'; x.fillRect(0, 0, w, h); x.fillStyle = '#d8dcef'; x.font = 'bold italic 26px sans-serif'; x.fillText('SUM-THING', 6, 29); x.fillStyle = '#ff8a2a'; x.font = 'bold 20px sans-serif'; x.fillText('3000', 138, 29); }) }));
  nm.position.set(-0.035, 0.083, -0.0158); nm.rotation.y = Math.PI; g.add(nm);
  // the keys (atlas-mapped boxes, the key tops face -Z)
  const keys = new THREE.Mesh(calcKeys(), jankify(new THREE.MeshLambertMaterial({ map: keyTex })));
  keys.rotation.y = Math.PI; keys.position.z = -0.035; // built facing +z: turned to face the front
  g.add(keys);
  // back: battery door, four rubber feet
  g.add(box(0.08, 0.06, 0.002, 0x1a1c2a, 0, -0.14, 0.0135));
  for (const sx of [-1, 1]) for (const y of [0.07, -0.18]) g.add(cyl(0.008, 0.004, 0x111111, sx * 0.055, y, 0.0145, 8));
  g.userData.screen = lm;
  return g;
}

// ================================================================ night vision goggles
// centred between the eyes, tubes forward (-Z). the mount pivots at the forehead (userData.pivot): rotate x to flip up
export function nvGoggles(o = {}) {
  const bl = authored('x_nvg');
  if (bl) { // the Blender goggles: flip on `pivot`, glowing lenses + IR lamp, the head strap only on someone's head
    const root = new THREE.Group(); root.add(bl.obj);
    const pivot = nodeIn(root, 'pivot'), lmL = glowMat(0x1a3a24), lmR = glowMat(0x1a3a24), irm = glowMat(0x3a0808);
    if (pivot && ownMat(root, 'lensL', lmL) && ownMat(root, 'lensR', lmR)) {
      ownMat(root, 'ir', irm);
      const strap = nodeIn(root, 'strap');
      if (strap && !o.strap) strap.removeFromParent();
      if (o.big && o.big !== 1) { // chunkier on a cartoon head: scaled about the eyes (the root), not the knuckle
        const sg = new THREE.Group(); sg.position.set(-pivot.position.x, -pivot.position.y, -pivot.position.z); pivot.add(sg);
        root.updateMatrixWorld(true);
        for (const c of [...pivot.children]) if (c !== sg) sg.attach(c);
        sg.scale.setScalar(o.big);
      }
      Object.assign(root.userData, { pivot, lenses: [lmL, lmR], ir: irm, glb: 'blender' });
      return root;
    }
  }
  const root = new THREE.Group(), pivot = new THREE.Group(); root.add(pivot);
  pivot.position.set(0, 0.07, 0.015); // the knuckle on the forehead
  const g = new THREE.Group(); g.position.set(0, -0.07, -0.015); g.scale.setScalar(o.big || 1); pivot.add(g); // cartoon heads want chunkier goggles
  const OD = 0x48503a, OD2 = 0x3a4030, BLK = 0x151517, PINK = 0xff4fd8;
  const lenses = [];
  for (const sx of [-1, 1]) {
    const x = sx * 0.034;
    // eyecup (rubber, flared to the face) -> tube -> objective bell -> lens
    g.add(lathe([[0.024, 0.012], [0.026, 0.004], [0.021, -0.006]], BLK, { segs: 14, x }));
    g.add(lathe([[0.021, -0.006], [0.0215, -0.06], [0.023, -0.066]], OD, { segs: 14, x }));
    g.add(lathe([[0.023, -0.066], [0.0265, -0.075], [0.0265, -0.098], [0.024, -0.102]], OD2, { segs: 14, x }));
    for (let i = 0; i < 4; i++) g.add(ring(0.0268, 0.0018, BLK, { axis: 'z', x, z: -0.079 - i * 0.0055, segs: 14, tubeSegs: 3 })); // focus ring grip
    const lm = glowMat(0x1a3a24);
    const ln = noWrap(new THREE.Mesh(new THREE.CircleGeometry(0.0225, 14), lm)); ln.position.set(x, 0, -0.1025); ln.rotation.y = Math.PI; g.add(ln);
    const hl = noWrap(new THREE.Mesh(new THREE.CircleGeometry(0.006, 8), glowMat(0x9fe8c0))); hl.position.set(x + 0.008, 0.009, -0.103); hl.rotation.y = Math.PI; g.add(hl);
    lenses.push(lm);
  }
  // the bridge between the tubes, the power knob, a battery box on top, the IR lamp on the side
  g.add(rbox(0.044, 0.032, 0.06, 0.006, OD, 0, 0.004, -0.04));
  const knob = cyl(0.007, 0.01, BLK, 0, 0.02, -0.07, 10); knob.rotation.x = Math.PI / 2; knob.position.set(0, 0.025, -0.05); g.add(knob);
  g.add(rbox(0.05, 0.022, 0.04, 0.005, OD2, 0, 0.03, -0.03));
  g.add(box(0.03, 0.004, 0.025, 0xb8bcc4, 0, 0.042, -0.03)); // battery cap
  const ir = cyl(0.008, 0.016, BLK, 0.06, 0.006, -0.085, 10); g.add(ir);
  g.add(box(0.012, 0.012, 0.02, OD, 0.05, 0.006, -0.075));
  const irm = glowMat(0x3a0808), irl = noWrap(new THREE.Mesh(new THREE.CircleGeometry(0.0065, 10), irm)); irl.position.set(0.06, 0.006, -0.0935); irl.rotation.y = Math.PI; g.add(irl);
  // the mount arm up to the knuckle
  g.add(box(0.016, 0.06, 0.012, BLK, 0, 0.05, -0.016));
  pivot.add(cyl(0.01, 0.034, 0x2a2a2e, 0, 0, 0, 10).rotateY(Math.PI / 2));
  // a tiny sticker on the bridge
  const st = new THREE.Mesh(new THREE.PlaneGeometry(0.03, 0.012), new THREE.MeshBasicMaterial({ map: canvasTex(128, 52, (x, w, h) => { x.fillStyle = '#ffe14d'; x.fillRect(0, 0, w, h); x.fillStyle = '#111'; x.font = 'bold 24px sans-serif'; x.textAlign = 'center'; x.fillText('NV-2000', w / 2, 34); }) }));
  st.position.set(0, 0.004, -0.0705); st.rotation.y = Math.PI; g.add(st);
  if (o.strap) { // head strap round the back + over the top (for people wearing them), and the forehead plate
    root.add(rbox(0.07, 0.04, 0.012, 0.004, BLK, 0, 0.07, 0.022));
    const band = new THREE.Mesh(new THREE.TorusGeometry(1, 0.08, 4, 22), mat(PINK)); band.scale.set(0.135, 0.135, 0.15); band.rotation.x = Math.PI / 2 - 0.25; band.position.set(0, 0.06, 0.12); root.add(band);
    const over = new THREE.Mesh(new THREE.TorusGeometry(1, 0.07, 4, 16, Math.PI), mat(PINK)); over.scale.set(0.13, 0.13, 0.13); over.rotation.y = Math.PI / 2; over.position.set(0, 0.07, 0.12); root.add(over);
  }
  Object.assign(root.userData, { pivot, lenses, ir: irm });
  return root;
}
