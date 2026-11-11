// Water that reacts (owner, 2026-11-11: "Like actual physics with water can we do that"). A PROOF, off unless
// Settings > video > "water physics (test)" is ticked, and only at Mid and Too HD.
// What it is: a heightfield. The wave equation on a small square of surface (N x N cells, a WIN metre window that
// follows the camera), stepped on the GPU by ping-ponging two float textures. Anything that splashes pokes it; the
// ripples spread, bounce off the banks (the shore map liquids.js already bakes) and die out. The water shader reads
// the result for its light and reflections.
// What it is not: a fluid. No flow, no pouring, no breaking waves, nothing pushed around by it, no water moving from
// one pool to another. It is look only: nothing here touches movement, the server or other players' screens.
import * as THREE from 'three';
import { SH } from './liquidmats.js';

const N = 128, WIN = 28, CELLM = WIN / N, STEPS_PER_S = 60, MAX_STEPS = 3, DROPS = 8;
const W = { on: false, dead: false, why: '', a: null, b: null, mat: null, mesh: null, cam: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), cx: 1e9, cz: 1e9, acc: 0, q: [], steps: 0, ms: 0 };
export const waterSimInfo = () => ({ on: W.on && !W.dead, dead: W.dead, why: W.why, n: N, win: WIN, steps: W.steps, ms: W.ms, mem: N * N * 8 * 2 });
function fail(why) { W.dead = true; W.why = why; SH.uSim.value = null; console.warn('[gfx] water physics switched off:', why); if (W.onChange) W.onChange(); }

const VERT = 'varying vec2 vUv;\nvoid main() { vUv = uv; gl_Position = vec4( position.xy, 0.0, 1.0 ); }';
// r = height now, g = height one step ago
const STEP = `uniform sampler2D tPrev; uniform sampler2D uMask; uniform vec4 uMR; uniform vec3 uWin; uniform vec2 uShift; uniform vec4 uDrops[${DROPS}];
varying vec2 vUv;
const float T = ${(1 / N).toFixed(8)};
bool wall( vec2 uv ) { // a bank, a rock, a pier leg: where the shore map says "not liquid"
  vec2 mu = ( uWin.xy + uv * uWin.z - uMR.xy ) * uMR.zw;
  if ( mu.x < 0.0 || mu.y < 0.0 || mu.x > 1.0 || mu.y > 1.0 ) return false; // open water beyond the map of shores
  return texture2D( uMask, mu ).b < 0.5;
}
float hAt( vec2 uv, float self ) { // a neighbour's height; a wall hands your own height back (the wave bounces)
  if ( uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0 ) return 0.0;
  return wall( uv ) ? self : texture2D( tPrev, uv + uShift ).r;
}
void main() {
  vec2 src = vUv + uShift; // the window moved with the camera: read from where this bit of water was
  vec2 p = ( src.x < 0.0 || src.y < 0.0 || src.x > 1.0 || src.y > 1.0 ) ? vec2( 0.0 ) : texture2D( tPrev, src ).rg;
  float h = p.r;
  float lap = hAt( vUv + vec2( T, 0.0 ), h ) + hAt( vUv - vec2( T, 0.0 ), h ) + hAt( vUv + vec2( 0.0, T ), h ) + hAt( vUv - vec2( 0.0, T ), h ) - 4.0 * h;
  float hn = ( 2.0 * h - p.g + 0.24 * lap ) * 0.988; // the wave equation, losing a little each step so it settles
  vec2 wp = uWin.xy + vUv * uWin.z;
  for ( int i = 0; i < ${DROPS}; i ++ ) { vec4 d = uDrops[ i ]; if ( d.z > 0.0 ) { vec2 o = wp - d.xy; hn += d.w * exp( - dot( o, o ) / ( d.z * d.z ) ); } }
  vec2 e = min( vUv, 1.0 - vUv ); hn *= smoothstep( 0.0, 0.06, min( e.x, e.y ) ); // soaks away at the window's edge (no echo off it)
  if ( wall( vUv ) ) { hn = 0.0; h = 0.0; }
  gl_FragColor = vec4( clamp( hn, -2.0, 2.0 ), h, 0.0, 1.0 );
}`;

function build(r) {
  const ok = r.capabilities.isWebGL2 && (r.extensions.has('EXT_color_buffer_float') || r.extensions.has('EXT_color_buffer_half_float'));
  if (!ok) { fail('this GPU cannot draw into float textures'); return false; }
  const rt = () => new THREE.WebGLRenderTarget(N, N, { type: THREE.HalfFloatType, format: THREE.RGBAFormat, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: false, wrapS: THREE.ClampToEdgeWrapping, wrapT: THREE.ClampToEdgeWrapping });
  W.a = rt(); W.b = rt();
  const tri = new THREE.BufferGeometry();
  tri.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3)); tri.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
  W.mat = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: STEP, depthTest: false, depthWrite: false, toneMapped: false,
    uniforms: { tPrev: { value: null }, uMask: SH.uMask, uMR: SH.uMR, uWin: { value: new THREE.Vector3() }, uShift: { value: new THREE.Vector2() }, uDrops: { value: Array.from({ length: DROPS }, () => new THREE.Vector4()) } } });
  W.mesh = new THREE.Mesh(tri, W.mat); W.mesh.frustumCulled = false;
  const gl = r.getContext(), prev = r.getRenderTarget();
  r.setRenderTarget(W.a); const st = gl.checkFramebufferStatus(gl.FRAMEBUFFER); r.setClearColor(0x000000, 1); r.clear();
  r.setRenderTarget(W.b); r.clear(); r.setRenderTarget(prev);
  if (st !== gl.FRAMEBUFFER_COMPLETE) { fail('the float frame buffer is not complete (' + st + ')'); return false; }
  return true;
}
// Settings switch + the quality preset (liquids.js passes both)
export function setWaterSim(on, onChange) {
  W.on = !!on; if (onChange) W.onChange = onChange;
  if (!W.on) { SH.uSim.value = null; W.q.length = 0; if (W.onChange) W.onChange(); }
}
// something disturbed the water at (x, z): r metres wide, s how hard (negative pushes down, like a thing landing)
export function simDrop(x, z, r, s) { if (W.on && !W.dead && W.q.length < 32) W.q.push(x, z, r, s); }
// liquids.js, every frame, before the scene is drawn
export function simStep(r, cam, dt) {
  if (!W.on || W.dead || SH.uQ.value < 2 || !SH.uMask.value) { if (SH.uSim.value) { SH.uSim.value = null; if (W.onChange) W.onChange(); } return; }
  try {
    if (!W.a && !build(r)) return;
    const t0 = performance.now();
    // the window follows the camera, a whole cell at a time, so the field can be carried along exactly
    const cx = Math.round(cam.position.x / CELLM) * CELLM, cz = Math.round(cam.position.z / CELLM) * CELLM;
    let sx = 0, sz = 0;
    if (Math.abs(cx - W.cx) > WIN || Math.abs(cz - W.cz) > WIN) { sx = 9; sz = 9; } else { sx = (cx - W.cx) / WIN; sz = (cz - W.cz) / WIN; } // (a jump further than the window: start flat)
    W.cx = cx; W.cz = cz;
    W.acc = Math.min(MAX_STEPS, W.acc + Math.min(0.1, dt) * STEPS_PER_S);
    let n = Math.floor(W.acc); W.acc -= n;
    if (!n && (sx || sz)) n = 1; // a move has to be applied even on a frame that owes no step
    const U = W.mat.uniforms, prev = r.getRenderTarget();
    U.uWin.value.set(cx - WIN / 2, cz - WIN / 2, WIN);
    for (let i = 0; i < n; i++) {
      for (let k = 0; k < DROPS; k++) { const d = U.uDrops.value[k]; if (i === 0 && W.q.length) d.set(W.q.shift(), W.q.shift(), W.q.shift(), W.q.shift()); else d.set(0, 0, 0, 0); }
      U.tPrev.value = W.a.texture; U.uShift.value.set(i === 0 ? sx : 0, i === 0 ? sz : 0);
      r.setRenderTarget(W.b); r.render(W.mesh, W.cam);
      const t = W.a; W.a = W.b; W.b = t; W.steps++;
    }
    r.setRenderTarget(prev);
    const first = !SH.uSim.value;
    SH.uSim.value = W.a.texture; SH.uSimW.value.set(cx - WIN / 2, cz - WIN / 2, 1 / WIN, 1 / N);
    if (first && W.onChange) W.onChange();
    W.ms = W.ms * 0.95 + (performance.now() - t0) * 0.05;
  } catch (e) { try { r.setRenderTarget(null); } catch (e2) { /* nothing left to try */ } fail('it threw: ' + (e && e.message)); }
}
