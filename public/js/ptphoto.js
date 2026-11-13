// PATH-TRACED PHOTO (the RAY-TRACED LOOK, part 6; the owner: "anything that would come from ray tracing"). Everything
// else in the look fakes ray tracing so it runs at game speed. This one is the real thing, for a still: it freezes what
// your camera sees and traces actual light paths through it (sun, sky, the lamps; bounces, soft shadows, reflections),
// a sample at a time, until the picture settles. Slow on purpose and clearly labelled: nothing in the game waits for it.
// Settings > video > shaders "path-traced photo", or /photo in chat (/photo 256 for more samples).
//
// The tracer is three-gpu-pathtracer 0.0.23 (MIT License, Copyright (c) 2022 Garrett Johnson) on three-mesh-bvh 0.8.3
// (MIT License, Copyright (c) 2019 Garrett Johnson), pinned in package.json, the last versions for three 0.170. They load
// only when you take a photo (import() below), never during play.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAP } from '/shared/map.js';

export const PHOTO = { samples: 96, bounces: 4, skyK: 1.8, exposure: 1.8, maxInst: 3000, instR: 140, maxSamples: 1024 };
let busy = false, ui = null;

// the sky as light: the map's sky gradient wrapped round as an environment (the in-game dome is a shader the tracer can't read)
function skyEnv() {
  const W = 128, H = 64, d = new Float32Array(W * H * 4), s = MAP.sky || { top: 0x6fb8ff, mid: 0xbfe4ff, bot: 0xffe0f0 };
  const top = new THREE.Color(s.top), mid = new THREE.Color(s.mid), bot = new THREE.Color(s.bot), c = new THREE.Color();
  for (let y = 0; y < H; y++) {
    const v = 1 - (y + 0.5) / H, el = (v - 0.5) * 2; // +1 straight up, -1 straight down
    if (el > 0) c.copy(mid).lerp(top, Math.pow(el, 0.6)); else c.copy(mid).lerp(bot, Math.min(1, -el * 3)).multiplyScalar(0.7);
    for (let x = 0; x < W; x++) { const i = (y * W + x) * 4; d[i] = c.r * PHOTO.skyK; d[i + 1] = c.g * PHOTO.skyK; d[i + 2] = c.b * PHOTO.skyK; d[i + 3] = 1; }
  }
  const t = new THREE.DataTexture(d, W, H, THREE.RGBAFormat, THREE.FloatType);
  t.mapping = THREE.EquirectangularReflectionMapping; t.magFilter = t.minFilter = THREE.LinearFilter; t.needsUpdate = true;
  return t;
}

// the frame as the tracer should see it: no shader-only things (the sky dome, water, grass, glow cards), and the
// instanced props spread out into real copies (the tracer would draw one copy of each), the nearest ones first
function prepScene(scene, cam) {
  const hidden = [], extra = new THREE.Group(), m4 = new THREE.Matrix4(), p = new THREE.Vector3();
  const inst = [];
  const fog = scene.fog && scene.fog.far ? scene.fog.far : 1e9, bs = new THREE.Sphere();
  scene.traverse((o) => {
    if (!o.visible) return;
    // past the fog: in game it's fog colour, here it would be a wall of dark backdrop city in front of the sky
    if (o.isMesh && o.geometry && !o.isInstancedMesh) { if (!o.geometry.boundingSphere) o.geometry.computeBoundingSphere(); bs.copy(o.geometry.boundingSphere).applyMatrix4(o.matrixWorld); if (bs.distanceToPoint(cam.position) > fog || bs.radius > 400) { hidden.push(o); return; } } // (radius: the merged backdrop city round the edge)
    if (o.isMesh && [].concat(o.material).some((m) => m && (m.side === THREE.BackSide || m.fog === false))) { hidden.push(o); return; } // the sky dome, the sun cube, clouds: the sky light below stands in
    if (o.isInstancedMesh) { hidden.push(o); inst.push(o); return; }
    if ((o.isMesh || o.isPoints || o.isLine || o.isSprite) && [].concat(o.material).some((m) => !m || m.isShaderMaterial || m.blending === THREE.AdditiveBlending || m.isPointsMaterial)) hidden.push(o);
  });
  const near = [];
  for (const im of inst) for (let i = 0; i < im.count; i++) {
    im.getMatrixAt(i, m4); m4.premultiply(im.matrixWorld); p.setFromMatrixPosition(m4);
    const d = p.distanceTo(cam.position); if (d < PHOTO.instR) near.push([d, im, m4.clone()]);
  }
  near.sort((a, b) => a[0] - b[0]);
  for (const [, im, m] of near.slice(0, PHOTO.maxInst)) { const c = new THREE.Mesh(im.geometry, im.material); c.matrixAutoUpdate = false; c.matrix.copy(m); extra.add(c); }
  for (const o of hidden) o.visible = false;
  scene.add(extra); extra.updateMatrixWorld(true);
  return () => { scene.remove(extra); for (const o of hidden) o.visible = true; };
}

// the overlay: comic panel, progress, then the picture with SAVE / CLOSE
function panel() {
  if (ui) return ui;
  const el = document.createElement('div');
  el.style.cssText = 'position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.55);font-family:var(--font),sans-serif;';
  el.innerHTML = `<div style="background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:14px 16px;max-width:94vw;color:#fff;text-align:center">
    <div style="font-weight:bold;font-size:20px;color:#ffe14d">PATH-TRACED PHOTO</div>
    <div data-k="sub" style="font-size:13px;opacity:0.85;margin:2px 0 10px">real ray tracing. slow on purpose. the game keeps going behind this.</div>
    <canvas data-k="pic" style="display:none;max-width:88vw;max-height:66vh;border:3px solid #000;image-rendering:auto"></canvas>
    <div data-k="msg" style="font-weight:bold;font-size:16px;margin:8px 0">LOADING THE TRACER...</div>
    <div style="display:flex;gap:10px;justify-content:center">
      <button data-k="save" style="display:none;background:#ffe14d;border:3px solid #000;box-shadow:4px 4px 0 #ff4fd8;transform:rotate(-1.5deg);font:bold 16px var(--font),sans-serif;padding:6px 14px;cursor:pointer">SAVE</button>
      <button data-k="close" style="background:#fff;border:3px solid #000;box-shadow:4px 4px 0 #000;font:bold 16px var(--font),sans-serif;padding:6px 14px;cursor:pointer">CLOSE</button>
    </div></div>`;
  const q = (k) => el.querySelector(`[data-k="${k}"]`);
  ui = { el, msg: q('msg'), pic: q('pic'), save: q('save'), close: q('close'), stop: false };
  ui.close.onclick = () => { ui.stop = true; el.remove(); ui = null; };
  document.body.append(el);
  return ui;
}

// the traced picture (linear light) -> a normal picture: a filmic curve, then screen colours
function toCanvas(r, tex, w, h, canvas) {
  const rt = new THREE.WebGLRenderTarget(w, h), quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({
    uniforms: { t: { value: tex }, k: { value: PHOTO.exposure } }, depthTest: false, depthWrite: false,
    vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4( position.xy, 0.0, 1.0 ); }',
    fragmentShader: `uniform sampler2D t; uniform float k; varying vec2 vUv;
vec3 aces( vec3 x ) { return clamp( ( x * ( 2.51 * x + 0.03 ) ) / ( x * ( 2.43 * x + 0.59 ) + 0.14 ), 0.0, 1.0 ); }
void main() { vec3 c = aces( texture2D( t, vUv ).rgb * k ); gl_FragColor = vec4( pow( c, vec3( 1.0 / 2.2 ) ), 1.0 ); }` }));
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), prev = r.getRenderTarget(), px = new Uint8Array(w * h * 4);
  r.setRenderTarget(rt); r.render(quad, cam); r.readRenderTargetPixels(rt, 0, 0, w, h, px); r.setRenderTarget(prev);
  rt.dispose(); quad.geometry.dispose(); quad.material.dispose();
  canvas.width = w; canvas.height = h;
  const g = canvas.getContext('2d'), img = g.createImageData(w, h);
  for (let y = 0; y < h; y++) img.data.set(px.subarray((h - 1 - y) * w * 4, (h - y) * w * 4), y * w * 4); // (GL rows go up)
  g.putImageData(img, 0, 0);
}

export async function takePhoto(samples = PHOTO.samples) {
  if (busy || !G.renderer || !G.scene || !G.camera) return false;
  busy = true;
  const U = panel(), r = G.renderer, scene = G.scene, cam = G.camera.clone(), env0 = scene.environment, bg0 = scene.background;
  let pt = null, restore = null, env = null;
  try {
    const { WebGLPathTracer } = await import('three-gpu-pathtracer');
    if (U.stop) return false;
    U.msg.textContent = 'BUILDING THE SCENE FOR LIGHT...';
    await new Promise((res) => setTimeout(res, 30)); // (let the message show before the long build)
    const size = r.getDrawingBufferSize(new THREE.Vector2()), w = size.x, h = size.y;
    pt = new WebGLPathTracer(r);
    pt.renderToCanvas = false; pt.rasterizeScene = false; pt.synchronizeRenderSize = false; pt.renderDelay = 0; pt.fadeDuration = 0; pt.minSamples = 0;
    pt.bounces = PHOTO.bounces; pt.tiles.set(2, 2);
    env = skyEnv(); scene.environment = env; scene.background = env;
    restore = prepScene(scene, cam);
    pt.setScene(scene, cam);
    restore(); restore = null; // (the game's frame goes back as it was; the tracer has its copy. the sky light stays till the photo's done: the tracer reads it every sample)
    pt.setSize ? pt.setSize(w, h) : pt._pathTracer.setSize(w, h);
    const t0 = performance.now();
    for (let s = 0; !U.stop && pt.samples < samples; s++) {
      pt.renderSample();
      if (s % 2 === 0) { U.msg.textContent = `TRACING LIGHT... ${Math.floor(pt.samples)} / ${samples}`; await new Promise((res) => requestAnimationFrame(res)); }
    }
    if (U.stop) return false;
    toCanvas(r, pt.target.texture, w, h, U.pic);
    U.pic.style.display = 'block'; U.save.style.display = '';
    U.msg.textContent = `${samples} SAMPLES, ${((performance.now() - t0) / 1000).toFixed(1)} S. THAT'S REAL LIGHT.`;
    U.save.onclick = () => { const a = document.createElement('a'); a.download = `jankfire_${MAP.id || 'photo'}_${Date.now()}.png`; a.href = U.pic.toDataURL('image/png'); a.click(); };
    return true;
  } catch (e) {
    console.warn('photo failed:', e);
    if (U && U.msg) U.msg.textContent = 'THE PHOTO BROKE. YOUR GPU SAID NO. (the game is fine)';
    return false;
  } finally {
    if (restore) restore();
    scene.environment = env0; scene.background = bg0;
    if (pt) try { pt.dispose(); } catch (e) { /* gone already */ }
    if (env) env.dispose();
    busy = false;
  }
}
// main.js, when a chat line is sent: true = it was ours
export function photoCmd(text) {
  const m = /^\/photo(?:\s+(\d+))?$/i.exec(text);
  if (!m) return false;
  const n = m[1] ? Math.max(8, Math.min(PHOTO.maxSamples, Number(m[1]) | 0)) : PHOTO.samples;
  takePhoto(n);
  return true;
}
export const photoInfo = () => ({ busy, open: !!ui });
