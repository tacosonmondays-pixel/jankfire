// The safety net for "everything renders as black" (owner report, 2026-11-10: the map and palms pitch black while the sky,
// far mountains, water and gun were fine; never reproduced). Everything that went black was lit, fogged and textured with
// the map's little canvas textures, so three things are watched, cheaply, and put back when they break:
//   1. the graphics context dying and coming back (a driver hiccup, the laptop waking up): textures repainted, shadows redrawn.
//      (the best match: blanking the map's canvas textures by hand gives exactly that screenshot, gun and all, while a
//      broken light also blacks out the clouds and the gun. a graphics reset can hand the canvases back empty)
//   2. a light, the fog or the haze holding a number that isn't one (one NaN turns every lit thing black)
//   3. the map's canvas textures gone blank
// and `/gfx` in chat shows a readout to screenshot (`/gfx fix` runs every repair, `/gfx tex|light|shadow` one at a time, so
// the one that fixes it tells us the cause).
import { G } from './ctx.js';
import { MAP } from '/shared/map.js';
import { lightingRefresh, shadowLevel } from './lighting.js';
import { hud } from './hud.js';

const S = { hooks: null, lost: 0, back: 0, fixes: 0, log: [], n: 0, el: null, on: false, shaderErrs: 0, t0: 0 };
const fin = Number.isFinite;
const note = (what) => { S.log.unshift(`${((performance.now() - S.t0) / 1000).toFixed(0)}s ${what}`); S.log.length = Math.min(S.log.length, 8); console.warn('[gfx]', what); if (S.on) draw(); };
const badColor = (c) => !c || !fin(c.r) || !fin(c.g) || !fin(c.b);

export function initGfxGuard(canvas, hooks) {
  S.hooks = hooks; S.t0 = performance.now();
  // three already stops the default and rebuilds its own state; these run after it
  canvas.addEventListener('webglcontextlost', () => { S.lost++; note('graphics context LOST'); });
  canvas.addEventListener('webglcontextrestored', () => { S.back++; note('graphics context back'); fixTex('context came back'); fixShadow(); hud.msg('GRAPHICS CRASHED. GRAPHICS BACK.', 2, 'brag'); });
  const dbg = G.renderer.debug;
  if (dbg && !dbg.onShaderError) dbg.onShaderError = (gl, prog, vs, fs) => { // keep three's own console report, count it for the readout
    S.shaderErrs++;
    const log = (gl.getProgramInfoLog(prog) || gl.getShaderInfoLog(fs) || gl.getShaderInfoLog(vs) || '').trim().slice(0, 300);
    console.error('[gfx] shader failed:', log); note('a shader failed: ' + log.slice(0, 70));
  };
}

// ---- the repairs
function fixTex(why) { const n = S.hooks.repaint(); S.fixes++; note(`map textures repainted (${n}): ${why}`); }
function fixLight(why) {
  // pooled / extra lights have no map default: a broken one just goes dark
  for (const o of G.scene.children) {
    if (!o.isLight) continue;
    if (badColor(o.color)) o.color.setHex(0xffffff);
    if (o.groundColor && badColor(o.groundColor)) o.groundColor.setHex(0x7a4a6a);
    if (!fin(o.intensity)) o.intensity = 0;
    if (!fin(o.position.x + o.position.y + o.position.z)) o.position.set(0, 50, 0);
  }
  const ok = S.hooks.relight();
  S.fixes++; note(`lights + fog reset${ok ? '' : ' (streamed map: lights only)'}: ${why}`);
}
function fixShadow() { lightingRefresh(); } // the cached sun shadow gets drawn again

// ---- the checks (world.js renderFrame, before drawing). ~once a second; the texture look every 4 s
function lightTrouble() {
  const sc = G.scene, f = sc.fog;
  if (f && (!fin(f.near) || !fin(f.far) || !(f.far > f.near) || badColor(f.color))) return 'fog';
  for (const o of sc.children) if (o.isLight && (!fin(o.intensity) || badColor(o.color) || (o.groundColor && badColor(o.groundColor)) || !fin(o.position.x + o.position.y + o.position.z))) return o.type;
  return '';
}
function blank(tex) { // a canvas texture whose canvas is empty (every pixel see-through)
  const c = tex && tex.image;
  if (!c || !c.getContext) return false;
  try {
    const d = c.getContext('2d').getImageData(0, 0, Math.min(8, c.width), Math.min(8, c.height)).data;
    for (let i = 3; i < d.length; i += 4) if (d[i]) return false;
    return true;
  } catch (e) { return false; }
}
function texTrouble() {
  const M = S.hooks.mats();
  if (!M) return '';
  for (const k of ['sand', 'stone', 'grass', 'wood']) if (M[k] && blank(M[k].mat.map)) return k;
  return '';
}
export function gfxGuard() {
  if (!S.hooks || !G.scene) return;
  const n = ++S.n;
  if (n % 60 === 0) { const w = lightTrouble(); if (w) { fixLight(`${w} held a broken number`); hud.msg('LIGHTS BACK ON', 1.4, 'brag'); } }
  if (n % 240 === 120) { const w = texTrouble(); if (w) { fixTex(`'${w}' went blank`); hud.msg('REPAINTED THE WORLD', 1.4, 'brag'); } }
  if (S.on && n % 30 === 0) draw();
}

// ---- the readout (`/gfx` in chat)
const hex = (c) => (c ? '#' + c.getHexString() : '?');
const num = (v) => (fin(v) ? (Math.round(v * 100) / 100).toString() : String(v) + ' !!');
function lines() {
  const r = G.renderer, gl = r.getContext(), sc = G.scene, f = sc.fog, out = [];
  let gpu = '?';
  try { const e = gl.getExtension('WEBGL_debug_renderer_info'); gpu = e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); } catch (e) { /* hidden */ }
  const st = G.settings || {}, cv = r.domElement;
  out.push(`gpu: ${String(gpu).slice(0, 90)}`);
  out.push(`quality: ${S.hooks.preset()} (${st.jank}) · shadows: ${st.shadows || 'auto'} -> ${shadowLevel()} · ${cv.width}x${cv.height} of ${innerWidth}x${innerHeight}`);
  out.push(`map: ${MAP.id} · mode: ${G.mode} · joined: ${!!G.joined}`);
  out.push(`context: lost ${S.lost}, back ${S.back}, lost now: ${gl.isContextLost()} · gl error: ${gl.isContextLost() ? '-' : gl.getError()} · shader fails: ${S.shaderErrs}`);
  out.push(`fog: ${f ? `${hex(f.color)} ${num(f.near)}..${num(f.far)}` : 'none'}`);
  for (const o of sc.children) if (o.isLight && (o.intensity > 0.001 || !fin(o.intensity) || o.isHemisphereLight || o.isDirectionalLight)) out.push(`${o.type.replace('Light', '')}: ${num(o.intensity)} ${hex(o.color)}${o.groundColor ? '/' + hex(o.groundColor) : ''}${o.visible ? '' : ' (off)'}${o.castShadow ? ' shadow' : ''}`);
  const M = S.hooks.mats(), ks = M ? Object.keys(M) : [];
  let tx = 0, bl = 0;
  for (const k of ks) { const t = M[k].mat.map; if (t) { tx++; if (blank(t)) bl++; } }
  const lit = M && M.stone ? M.stone.mat : null;
  out.push(`map materials: ${ks.length} · textures: ${tx}, blank: ${bl}${lit ? ` · stone: ${lit.type.replace('Mesh', '').replace('Material', '')} vc:${!!lit.vertexColors} fog:${!!lit.fog} col:${hex(lit.color)}` : ''}`);
  const i = r.info;
  out.push(`drawn: ${i.render.calls} calls, ${i.render.triangles} tris · gpu memory: ${i.memory.textures} tex, ${i.memory.geometries} geo, ${i.programs ? i.programs.length : '?'} shaders`);
  out.push(`trouble now: lights/fog '${lightTrouble() || 'ok'}', textures '${texTrouble() || 'ok'}' · auto repairs: ${S.fixes}`);
  for (const l of S.log) out.push('· ' + l);
  out.push('/gfx fix = try every repair · /gfx tex · /gfx light · /gfx shadow · /gfx = close');
  return out;
}
function draw() {
  if (!S.el) {
    const el = S.el = document.createElement('pre');
    el.id = 'gfxBox';
    el.style.cssText = 'position:fixed;left:12px;top:12px;z-index:9999;margin:0;max-width:min(760px,94vw);white-space:pre-wrap;pointer-events:none;font:bold 12px/1.35 var(--font),monospace;color:#fff;background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:8px 12px;';
    document.body.append(el);
  }
  S.el.style.display = 'block';
  S.el.textContent = 'GFX READOUT (screenshot me)\n' + lines().join('\n');
}
// main.js, when a chat line is sent: true = it was ours (don't send it to the room)
export function gfxCmd(text) {
  const m = /^\/gfx(?:\s+(\w+))?$/i.exec(text);
  if (!m || !S.hooks) return false;
  const a = (m[1] || '').toLowerCase();
  if (a === 'fix') { fixTex('asked'); fixLight('asked'); fixShadow(); note('shadows redrawn: asked'); S.on = true; }
  else if (a === 'tex') { fixTex('asked'); S.on = true; }
  else if (a === 'light') { fixLight('asked'); S.on = true; }
  else if (a === 'shadow') { fixShadow(); note('shadows redrawn: asked'); S.on = true; }
  else S.on = !S.on;
  if (S.on) draw(); else if (S.el) S.el.style.display = 'none';
  return true;
}
