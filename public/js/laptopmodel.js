// The Laptop's code model (the Blender w_laptop.glb swaps in over it and keeps these spots). Game space: x right, y up,
// -z forward, metres. You hold it backwards: the hinge is at your end, the screen faces whoever you point it at, and you
// get the lid's back (stickers). A 14 inch office laptop at life size: 32 x 22 cm deck, 21 cm lid.
import * as THREE from 'three';
import { M } from './models.js';

const tag = (m, wz) => { m.userData.wz = wz; return m; };
function bx(w, h, d, c, x, y, z, wz = 'a', basic = false) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c, basic)); m.position.set(x, y, z); return tag(m, wz); }
function canvasTex(w, h, draw) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  draw(cv.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
// what the victim is about to get, in miniature: a desktop buried in pop-ups
export function adScreenTex() {
  return canvasTex(128, 80, (x, w, h) => {
    x.fillStyle = '#12081a'; x.fillRect(0, 0, w, h);
    const win = (px, py, pw, ph, bar, txt) => {
      x.fillStyle = '#000'; x.fillRect(px + 3, py + 3, pw, ph);
      x.fillStyle = '#fff'; x.fillRect(px, py, pw, ph);
      x.fillStyle = bar; x.fillRect(px, py, pw, 9);
      x.fillStyle = '#ff3030'; x.fillRect(px + pw - 9, py + 1, 7, 7);
      x.fillStyle = '#000'; x.font = 'bold 9px sans-serif'; x.fillText(txt, px + 4, py + 22);
      x.fillStyle = '#ffe14d'; x.fillRect(px + 4, py + ph - 12, pw - 8, 8);
    };
    win(6, 6, 62, 40, '#ff4fd8', 'YOU WON');
    win(52, 22, 66, 42, '#4fd8ff', 'BREAD');
    win(18, 38, 58, 36, '#39ff14', 'CLICK');
  });
}
function lidTex() {
  return canvasTex(128, 84, (x, w, h) => {
    x.fillStyle = '#c9ccd4'; x.fillRect(0, 0, w, h);
    x.save(); x.translate(64, 40); x.rotate(-0.12);
    x.fillStyle = '#000'; x.fillRect(-45, -13, 96, 30);
    x.fillStyle = '#ffe14d'; x.fillRect(-48, -16, 96, 30);
    x.fillStyle = '#000'; x.font = 'bold 13px sans-serif'; x.textAlign = 'center'; x.fillText('AD SUPPORTED', 0, 4);
    x.restore();
    x.fillStyle = '#ff4fd8'; x.beginPath(); x.arc(104, 66, 10, 0, 7); x.fill();
    x.fillStyle = '#fff'; x.font = 'bold 8px sans-serif'; x.textAlign = 'center'; x.fillText('IT', 104, 69);
    x.fillStyle = '#4fd8ff'; x.fillRect(8, 60, 30, 14); x.fillStyle = '#000'; x.font = 'bold 7px sans-serif'; x.fillText('ASSET 404', 23, 70);
  });
}
export const LAPTOP_WB = {
  laptop(g) {
    const SIL = 0xc9ccd4, DARK = 0x1a1a22, KEY = 0x2a2a34;
    g.add(bx(0.32, 0.016, 0.22, SIL, 0, 0, -0.11));
    g.add(bx(0.28, 0.003, 0.105, DARK, 0, 0.009, -0.075, 'n')); // keyboard well
    for (let r = 0; r < 4; r++) for (let c = 0; c < 10; c++) g.add(bx(0.022, 0.004, 0.02, (r === 1 && c === 3) || (r === 3 && c === 8) ? 0xff4fd8 : KEY, -0.123 + c * 0.0273, 0.011, -0.036 - r * 0.026, 'n'));
    g.add(bx(0.09, 0.002, 0.055, 0xaeb2bd, 0, 0.009, -0.172, 'n')); // trackpad
    g.add(bx(0.3, 0.014, 0.014, DARK, 0, 0.012, -0.004, 'n')); // hinge barrel
    const lid = new THREE.Group(); lid.position.set(0, 0.012, 0); lid.rotation.x = 0.26; // open past upright, leaning back at you
    lid.add(bx(0.32, 0.21, 0.01, SIL, 0, 0.105, 0, 'b'));
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.29, 0.18), new THREE.MeshBasicMaterial({ map: adScreenTex(), toneMapped: false }));
    scr.rotation.y = Math.PI; scr.position.set(0, 0.108, -0.0056); scr.userData.noWrap = true; scr.userData.wz = 'n'; lid.add(scr);
    const back = new THREE.Mesh(new THREE.PlaneGeometry(0.31, 0.2), new THREE.MeshBasicMaterial({ map: lidTex(), toneMapped: false }));
    back.position.set(0, 0.105, 0.0056); back.userData.noWrap = true; back.userData.wz = 'n'; lid.add(back);
    lid.add(bx(0.012, 0.006, 0.004, 0x39ff14, 0, 0.203, -0.006, 'n', true)); // webcam light: it is on. it is always on
    g.add(lid);
    g.userData.screen = scr; g.userData.lid = lid;
    g.userData.muzzle = new THREE.Vector3(0, 0.12, -0.06);
    g.userData.len = 0.3;
  },
};
