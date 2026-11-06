// OVERDUE comic panels (DESIGN §8.1 "Comic Panels" + "Previously on"): the scene freezes into 3-6 tilted panels, each
// a real render of a camera shot of the world (posterized + halftone, so it reads as print), slammed in one by one
// with captions, speech bubbles and SFX words in the zine UI.
// a panel: { at (s), shot: { target, shot, ... } (shots.js), cap, say: [who, text], sfx: 'SPLUT', sound, face: [who, face],
//            anim: [who, clip, t], rect: [x, y, w, h] (0..1, optional), tilt }
import * as THREE from 'three';
import { G } from '../ctx.js';
import { CLIPS, setFace } from './actors.js';
import { shotPose } from './shots.js';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
// layouts by panel count: [x, y, w, h] in screen fractions (with gutters), and a tilt each
const LAYOUT = {
  1: [[0.12, 0.14, 0.76, 0.72]],
  2: [[0.05, 0.16, 0.44, 0.66], [0.52, 0.2, 0.43, 0.64]],
  3: [[0.04, 0.14, 0.42, 0.4], [0.5, 0.1, 0.46, 0.44], [0.12, 0.58, 0.76, 0.34]],
  4: [[0.04, 0.12, 0.44, 0.39], [0.52, 0.1, 0.44, 0.41], [0.05, 0.55, 0.42, 0.38], [0.51, 0.56, 0.45, 0.37]],
  5: [[0.03, 0.12, 0.3, 0.39], [0.36, 0.1, 0.3, 0.41], [0.69, 0.12, 0.28, 0.39], [0.05, 0.55, 0.43, 0.38], [0.52, 0.56, 0.44, 0.37]],
  6: [[0.03, 0.12, 0.3, 0.38], [0.36, 0.1, 0.29, 0.4], [0.68, 0.12, 0.29, 0.38], [0.03, 0.55, 0.3, 0.38], [0.36, 0.56, 0.29, 0.37], [0.68, 0.55, 0.29, 0.38]],
};
const TILT = [-1.6, 1.2, -0.8, 1.5, -1.2, 0.9];
let rt = null, buf = null;

// render a shot of the world into a 2D canvas, posterized (comic ink)
function snap(cv, pose, fov, w, h) {
  const r = G.renderer;
  if (!rt || rt.width !== w || rt.height !== h) { if (rt) rt.dispose(); rt = new THREE.WebGLRenderTarget(w, h); rt.texture.colorSpace = THREE.SRGBColorSpace; buf = new Uint8Array(w * h * 4); }
  const cam = new THREE.PerspectiveCamera(fov, w / h, 0.05, 900);
  cam.position.copy(pose.pos); cam.lookAt(pose.look); if (pose.roll) cam.rotateZ(pose.roll); cam.updateMatrixWorld();
  const prev = r.getRenderTarget();
  r.setRenderTarget(rt); r.render(G.scene, cam); r.readRenderTargetPixels(rt, 0, 0, w, h, buf); r.setRenderTarget(prev);
  cv.width = w; cv.height = h;
  const g = cv.getContext('2d'), img = g.createImageData(w, h), d = img.data;
  for (let y = 0; y < h; y++) {
    const src = (h - 1 - y) * w * 4, dst = y * w * 4;
    for (let x = 0; x < w * 4; x += 4) {
      // posterize to 5 bands per channel, pushed saturated, so it reads like a printed comic
      for (let c = 0; c < 3; c++) { const v = buf[src + x + c] / 255; d[dst + x + c] = Math.min(255, Math.round(Math.pow(v, 0.9) * 4.2) / 4.2 * 255 * 1.05); }
      d[dst + x + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  // ink: darken edges where brightness jumps (a cheap outline)
  const L = (i) => d[i] * 0.3 + d[i + 1] * 0.59 + d[i + 2] * 0.11, out = g.createImageData(w, h), o = out.data;
  o.set(d);
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) { const i = (y * w + x) * 4; const e = Math.abs(L(i) - L(i + 4)) + Math.abs(L(i) - L(i + w * 4)); if (e > 70) { o[i] = o[i + 1] = o[i + 2] = 10; } }
  g.putImageData(out, 0, 0);
}

export function buildPanels(list, ctx) {
  const el = $('stPanels');
  el.innerHTML = '<div class="halftone"></div>' + (ctx.title ? `<div class="rtitle">${esc(ctx.title)}</div>` : '');
  const n = Math.max(1, Math.min(6, list.length)), lay = LAYOUT[n];
  const W = innerWidth, H = innerHeight;
  const items = list.slice(0, 6).map((p, i) => ({ ...p, i, at: p.at ?? 0.4 + i * 1.7, shown: false }));
  const last = items.length ? items[items.length - 1] : { at: 0 };
  const len = last.at + 2.6 + (last.say ? last.say[1].length * 0.04 : 0);
  let typing = [];
  function show(p) {
    p.shown = true;
    const rc = p.rect || lay[p.i] || lay[0], x = rc[0] * W, y = rc[1] * H, w = rc[2] * W, h = rc[3] * H;
    // pose the world for this panel (a face, a held gesture), then shoot it
    if (p.face) { const a = ctx.who(p.face[0]); if (a) { setFace(a, p.face[1]); for (let k = 0; k < 12; k++) a.face.update(0.06); } }
    if (p.anim) { const a = ctx.who(p.anim[0]); if (a && CLIPS[p.anim[1]]) CLIPS[p.anim[1]].f(a.ch, p.anim[2] ?? 0.5, 1); }
    for (const a of [ctx.who(p.shot && p.shot.target)].filter(Boolean)) a.ch.root.updateMatrixWorld(true);
    const pose = p.shot ? shotPose(p.shot, p.shot.u ?? 0.5, ctx.who, ctx.where, null) : null;
    const d = document.createElement('div'); d.className = 'pnl';
    const tf = `rotate(${p.tilt ?? TILT[p.i % 6]}deg)`;
    d.style.cssText = `left:${x}px;top:${y}px;width:${w}px;height:${h}px;--tf:${tf};transform:${tf}`;
    const cv = document.createElement('canvas'); d.append(cv);
    if (pose) snap(cv, pose, p.shot.fov || 40, Math.max(64, Math.round(w / 2)), Math.max(48, Math.round(h / 2)));
    else { cv.width = 8; cv.height = 8; const g = cv.getContext('2d'); g.fillStyle = p.bg || '#1a0828'; g.fillRect(0, 0, 8, 8); }
    d.insertAdjacentHTML('beforeend', '<div class="dots"></div>');
    if (p.cap) d.insertAdjacentHTML('beforeend', `<div class="cap${ctx.crayon || p.crayon ? ' crayon' : ''}">${esc(p.cap)}</div>`);
    if (p.say) { const b = document.createElement('div'); b.className = 'bub'; b.style.cssText = `right:${p.bubL ? 'auto' : '6%'};left:${p.bubL ? '6%' : 'auto'};top:${p.cap ? 34 : 8}%`; d.append(b); typing.push({ b, text: p.say[1], typed: 0, v: ctx.voiceOf(p.say[0]) }); }
    if (p.sfx) { const s = document.createElement('div'); s.className = 'sfx'; s.textContent = p.sfx; s.style.cssText = `right:${8 + (p.i % 3) * 6}%;bottom:${10 + (p.i % 2) * 14}%`; d.append(s); }
    el.append(d);
    ctx.playSfx(p.sound || (p.sfx ? 'whoosh' : 'whoosh'));
  }
  return {
    len,
    frame(t, dt) {
      for (const p of items) if (!p.shown && t >= p.at) show(p);
      for (const ty of typing) {
        if (ty.typed >= ty.text.length) continue;
        const b0 = Math.floor(ty.typed); ty.typed = Math.min(ty.text.length, ty.typed + dt * 34);
        if (ty.v) for (let i = b0; i < Math.floor(ty.typed); i++) ty.v.blip(ty.text[i], i, ty.text);
        ty.b.textContent = ty.text.slice(0, Math.floor(ty.typed));
      }
    },
  };
}
