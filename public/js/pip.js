// The first-person corner box (owner, 2026-11-07: "what about the first person corner box for spectate"). While you
// spectate in a mode that watches from behind (one in the chamber out of lives, jank royale), a small picture-in-picture
// box shows what the watched player sees through their own eyes. Cheap on purpose: a 320x180 render target, refreshed
// every other frame, drawn into a corner of the frame; off on Potato, and Settings can hide it.
import * as THREE from 'three';
import { G } from './ctx.js';
import { FLAGS } from '/shared/weapons.js';
import { PH } from '/shared/physics.js';

const P = { rt: null, cam: null, quad: null, qcam: null, el: null, id: 0, yaw: 0, pitch: 0, n: 0, on: false };
const RT_W = 320, RT_H = 180, SHARE = 0.2; // render target size; the box is a fifth of the screen wide
const wrapA = (a) => { while (a > Math.PI) a -= Math.PI * 2; while (a < -Math.PI) a += Math.PI * 2; return a; };
const sz = new THREE.Vector2();

function init() {
  P.rt = new THREE.WebGLRenderTarget(RT_W, RT_H, { depthBuffer: true });
  P.cam = new THREE.PerspectiveCamera(80, RT_W / RT_H, 0.1, 2000);
  P.cam.rotation.order = 'YXZ';
  const sc = new THREE.Scene();
  sc.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ map: P.rt.texture, depthTest: false, depthWrite: false, toneMapped: false })));
  P.quad = sc; P.qcam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const el = P.el = document.createElement('div');
  el.id = 'pipBox';
  el.innerHTML = '<span></span>';
  document.getElementById('hud').append(el);
  const st = document.createElement('style');
  st.textContent = `#pipBox { position: absolute; right: 14px; pointer-events: none; border: 4px solid #ff4fd8; box-shadow: 6px 6px 0 #4fd8ff; transform: rotate(0.8deg); display: none; box-sizing: border-box; }
#pipBox span { position: absolute; left: -4px; top: -26px; background: #ffe14d; color: #000; border: 3px solid #000; font: bold 13px var(--font); padding: 0 8px; white-space: nowrap; transform: rotate(-2deg); }`;
  document.head.append(st);
}

// main.js, right after the frame is drawn: id = who you're watching (0 = nobody: the box goes away)
export function pipFrame(dt, id) {
  const S = G.settings || {}, r = id && G.remotes.get(id);
  const want = !!r && r.alive && !S.noPip && S.jank !== 0; // (Potato: no box, it would be mush anyway)
  if (!want) { if (P.on) { P.on = false; P.el.style.display = 'none'; } return; }
  if (!P.rt) init();
  const R = G.renderer;
  R.getSize(sz);
  const w = Math.round(sz.x * SHARE), h = Math.round((w * RT_H) / RT_W), x = sz.x - w - Math.round(sz.x * 0.012), y = Math.round(sz.y * 0.47); // (under the royale stat box and the minimap)
  if (id !== P.id || !P.on) { P.id = id; P.yaw = r.yaw; P.pitch = r.pitch; P.n = 0; P.el.querySelector('span').textContent = `${r.name}'s eyes`; }
  P.on = true;
  // their eyes (smoothed a little, like the first-person spectate)
  const k = Math.min(1, dt * 20);
  P.yaw += wrapA(r.yaw - P.yaw) * k; P.pitch += (r.pitch - P.pitch) * k;
  if (P.n++ % 2 === 0) { // every other frame is plenty for a corner box
    P.cam.position.set(r.pos[0], r.pos[1] + ((r.f & FLAGS.CROUCH) ? 1.05 : PH.eye), r.pos[2]);
    P.cam.rotation.set(P.pitch, P.yaw, 0);
    P.cam.fov = G.camera ? G.camera.fov : 80; P.cam.updateProjectionMatrix();
    const vis = [r.ch.root.visible, r.tag && r.tag.visible, r.shadow && r.shadow.visible];
    r.ch.root.visible = false; if (r.tag) r.tag.visible = false; if (r.shadow) r.shadow.visible = false; // (not the inside of their head)
    R.setRenderTarget(P.rt); R.clear(); R.render(G.scene, P.cam); R.setRenderTarget(null);
    r.ch.root.visible = vis[0]; if (r.tag) r.tag.visible = vis[1]; if (r.shadow) r.shadow.visible = vis[2];
  }
  // into the corner of the frame (y counts up from the bottom here)
  R.setScissorTest(true); R.setScissor(x, sz.y - y - h, w, h); R.setViewport(x, sz.y - y - h, w, h);
  R.render(P.quad, P.qcam);
  R.setScissorTest(false); R.setViewport(0, 0, sz.x, sz.y);
  // the comic frame on top, in CSS pixels
  const cw = innerWidth / sz.x, el = P.el;
  el.style.display = 'block';
  el.style.width = `${Math.round(w * cw) + 8}px`; el.style.height = `${Math.round(h * cw) + 8}px`;
  el.style.right = `${Math.round((sz.x - x - w) * cw) - 4}px`; el.style.top = `${Math.round(y * (innerHeight / sz.y)) - 4}px`;
}
export const pipOn = () => P.on;
