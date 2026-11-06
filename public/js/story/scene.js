// OVERDUE scene player (DESIGN §8, TECH_PLAN §6): data-driven timelines, played in-engine with the game's own models.
// The six kinds:
//   cinematic: camera tracks (shot presets on actors, or spline paths), letterbox bars in pink, babble subtitles + jaw
//              flap, faces, gesture clips, walks, fx / sfx, shakes, hit-stop, red impact frames, fades, titles
//   panels:    the scene freezes into 3-6 tilted comic panels (each a render of a camera shot), halftone, captions,
//              speech bubbles and SFX words, slammed in one by one
//   talk:      a scripted conversation with the talk cam (talk.js), the world running behind it
//   boss:      whip to the boss, time stops, the huge title card (name, job, deadpan subtitle, REHIRED on refights)
//   moment:    1-3 s gameplay-camera micro scenes (slow-mo orbit, a red frame, a sting): juice, barely blocks control
//   recap:     "PREVIOUSLY ON OVERDUE": the last 3 story beats as crayon-captioned panels, on loading a save
// Hold SPACE (the jump key) to skip any of them (co-op: the skip vote, later). Every scene ends by blending back into
// the player's own camera. Track list: see TRACKS below.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { ME, eye } from '../player.js';
import { K } from '../keys.js';
import { sfx, synth } from '../audio.js';
import { hud } from '../hud.js';
import { actors, spawnActor, despawnActor, walkTo, play, setFace, headPos, dropTo } from './actors.js';
import { voice } from './babble.js';
import { wantShot } from './camctl.js';
import { startTalk, talking } from './talk.js';
import { organic } from '../organic.js';
import { buildPanels } from './panels.js';
import { shotPose } from './shots.js';

const $ = (id) => document.getElementById(id);
let ST = null, P = null; // P = the scene playing now
const queue = [];
const ss = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

export function initScenes(st) {
  ST = st;
  const L = $('stLayer');
  for (const [id, cls] of [['stFade', ''], ['stImpact', ''], ['stBars', ''], ['stSub', 'hidden'], ['stTitle', 'hidden'], ['stBoss', 'hidden'], ['stPanels', 'hidden'], ['stSkip', 'hidden']]) {
    const d = document.createElement('div'); d.id = id; if (cls) d.className = cls; L.append(d);
  }
  $('stSkip').innerHTML = `<svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="14" fill="none" stroke="#000" stroke-width="7"/><circle id="stSkipRing" cx="18" cy="18" r="14" fill="none" stroke="#ffe14d" stroke-width="5" stroke-dasharray="88" stroke-dashoffset="88" transform="rotate(-90 18 18)"/></svg><span>hold <b>${K.label('jump')}</b> skip</span>`;
}
export const playing = () => !!P;
export const sceneList = () => Object.keys(ST.S.defs.scenes);

// ---------------------------------------------------------------- start / stop
// the script's scenes (shared/story/content/scenes_act*.js) are mostly directions, lines and comic-panel tracks with
// few cameras: this turns one into what the player runs. cast values that are strings name an npc; panel tracks become
// the panel list; tracks with `if` are dropped when false; a boss track names a boss; title is a string; flashbacks
// play as cinematics; and lines without a camera get coverage (a closeup on whoever speaks, a wide on the directions)
const SHOT_ALIAS = { overShoulder: 'over', insert: 'extreme', pov: 'closeup' };
function normScene(d) {
  const S = ST.S, out = { ...d, kind: d.kind === 'flashback' ? 'cinematic' : d.kind, cast: {}, tracks: [] };
  for (const [k, v] of Object.entries(d.cast || {})) out.cast[k] = typeof v === 'string' ? (k === 'you' || v === 'change' ? { look: 'mannequin', name: 'YOU' } : actors.has(v) ? { actor: v } : { npc: v }) : v;
  const panels = [];
  let lastCam = -9, lastSay = null, shotN = 0;
  const castKeys = Object.keys(out.cast);
  for (const t0 of d.tracks || []) {
    if (t0.if && !S.test(t0.if)) continue;
    const t = { ...t0 };
    delete t.if; delete t.dir;
    if (typeof t.title === 'string') t.title = [t.title, '', 2.5];
    if (t.cam) { t.cam = { ...t.cam }; if (SHOT_ALIAS[t.cam.shot]) { t.cam.from = t.cam.from || 'you'; t.cam.shot = SHOT_ALIAS[t.cam.shot]; } if (typeof t.cam.path === 'string') { t.cam = { shot: 'orbit', target: castKeys.find((k) => k !== 'you') || castKeys[0], dur: t.cam.dur || 8, turn: 0.8, r: 6, up: 2, fov: t.cam.fov }; } lastCam = t.t; }
    if (typeof t.boss === 'string') { const b = (S.defs.bosses || {})[t.boss] || {}; const [name, job] = String(b.card || t.boss).split(' · '); t.boss = { name, job: job || '', sub: b.subtitle || '', target: castKeys.find((k) => k !== 'you'), rehired: !!(S.st.flags[`beat.${t.boss}`]) }; }
    if (t.choice && !t.do) delete t.choice;
    if (t.panel) { const pn = { at: t.t, cap: t.panel.cap, sfx: t.panel.sfx, crayon: /auntie/.test(JSON.stringify(d.cast || {})) && d.kind === 'panels', shot: { target: castKeys[shotN % Math.max(1, castKeys.length)] || 'you', shot: ['closeup', 'lowAngle', 'wide', 'extreme'][shotN % 4] } }; shotN++; panels.push(pn); delete t.panel; }
    if (t.say && out.kind === 'panels' && panels.length) { const pn = panels[panels.length - 1]; if (!pn.say) pn.say = t.say; }
    // coverage: cut to whoever speaks (if nothing else has the camera right now)
    if (t.say && out.kind !== 'panels' && !t.cam && t.t - lastCam > 2.5 && t.say[0] !== lastSay && out.cast[t.say[0]]) { t.cam = { shot: shotN++ % 3 === 2 ? 'two' : 'closeup', target: t.say[0], from: castKeys.find((k) => k !== t.say[0] && k !== 'you'), dur: 4 }; lastCam = t.t; }
    if (t.say) lastSay = t.say[0];
    if (Object.keys(t).length > 1) out.tracks.push(t);
  }
  if (out.kind === 'cinematic' && !out.tracks.some((t) => t.cam && t.t < 1) && castKeys.length) out.tracks.unshift({ t: 0, cam: { shot: 'wide', target: castKeys.find((k) => k !== 'you') || castKeys[0], dur: 6 } });
  if (panels.length) { out.panels = panels.slice(0, 6); out.kind = 'panels'; if (panels.length > 6) out.panels = panels.slice(-6); }
  if (out.kind === 'panels' && !d.len) out.len = undefined;
  return out;
}

export function playScene(id, opts = {}) {
  const def0 = typeof id === 'object' ? id : ST.S.defs.scenes[id];
  const def = def0 && def0.tracks && def0.tracks.some((t) => t.dir || t.panel || typeof t.title === 'string' || typeof t.boss === 'string' || t.if) || def0 && Object.values(def0.cast || {}).some((v) => typeof v === 'string') ? normScene(def0) : def0;
  if (!def) { console.warn('no scene', id); return false; }
  if (P || (talking() && def.kind !== 'talk')) { queue.push([def, opts]); return true; } // (a scene waits for the one playing, or for the conversation to end)
  P = { def, t: 0, i: 0, tracks: [...(def.tracks || [])].sort((a, b) => a.t - b.t), cast: new Map(), temp: [], hold: 0, stop: 0, slow: 1, sub: null, opts, kind: def.kind || 'cinematic', len: def.len ?? 10, skipK: 0, done: false };
  ST.S.st.seen[def.id] = true;
  document.body.classList.add('st-cine');
  if (P.kind !== 'moment') $('stSkip').classList.toggle('hidden', def.skip === false);
  if (P.kind === 'cinematic' || P.kind === 'boss') bars(def.bars !== false);
  if (G.vmScene) G.vmScene.visible = false;
  // cast: existing actors by id, or temporary ones spawned at a mark. 'you' = a stand-in for the player
  for (const [k, c] of Object.entries(def.cast || {})) castOne(k, c);
  if (def.hideOthers) for (const a of actors.values()) if (![...P.cast.values()].includes(a) && !a.hidden) { a.hidden = true; P.hid = (P.hid || []).concat(a); } // (extras out of the shot)
  if (P.kind === 'panels' || P.kind === 'recap') startPanels();
  if (P.kind === 'talk') { const t = def.talk || {}; P.len = 9e9; startTalk(ST.S, t.npc, t.node || 'start', () => { P && (P.len = P.t); }); }
  if (P.kind === 'boss') { bossCard(def.boss || def); P.len = def.len ?? 4.8; }
  if (P.kind === 'moment') P.len = Math.min(3, def.len ?? 1.6);
  return true;
}
function castOne(k, c) {
  if (c.actor || actors.has(k)) { const a = actors.get(c.actor || k); if (a) { P.cast.set(k, a); a.inScene = true; if (c.at) { a.pos = [...where(c.at)]; a.r.pos = a.pos; } if (c.face != null) a.yaw = a.faceTarget = ST.offYaw(c.face); } return; }
  const at = c.at ? where(c.at) : k === 'you' ? [ME.pos[0], ME.pos[1], ME.pos[2]] : [ME.pos[0], ME.pos[1], ME.pos[2] - 3];
  const def = ST.S.defs.npcs[c.npc] || { look: c.look || (k === 'you' ? 'mannequin' : 'mannequin'), voice: c.voice || { kind: 'beep' }, name: c.name || k.toUpperCase() };
  const id = '_scene_' + k;
  const a = spawnActor(id, { ...def, look: c.look || def.look }, at, c.face != null ? ST.offYaw(c.face) : k === 'you' ? ME.yaw : 0);
  a.inScene = true; a.sceneName = c.name || def.name;
  if (c.scale) a.ch.root.scale.multiplyScalar(c.scale);
  if (c.hidden) a.hidden = true;
  P.cast.set(k, a); P.temp.push(id);
}
function endScene(skipped) {
  if (!P) return;
  const p = P; P = null;
  for (const id of p.temp) despawnActor(id);
  for (const a of p.hid || []) a.hidden = false;
  for (const a of p.cast.values()) { a.inScene = false; a.faceTarget = null; a.talking = false; a.lookAt = null; a.lookTarget = null; a.hold = false; a.clip = null; a.hidden = false; setFace(a, 'neutral'); if (Math.hypot(a.pos[0] - a.home.p[0], a.pos[2] - a.home.p[2]) > 0.3) walkTo(a, [a.home.p], 1.4); } // (back to their spot)
  bars(false); sub(null); title(null);
  $('stBoss').classList.add('hidden'); $('stPanels').classList.add('hidden'); $('stPanels').innerHTML = ''; $('stSkip').classList.add('hidden');
  $('stFade').style.transition = 'opacity 0.35s'; $('stFade').style.opacity = 0; $('stImpact').style.opacity = 0;
  document.body.classList.remove('st-cine');
  wantShot(null);
  ST.slowmo = 1;
  if (p.def.onEnd) ST.S.run(p.def.onEnd, `scene ${p.def.id}`);
  ST.S.emit({ type: 'sceneEnd', scene: p.def.id });
  if (p.opts.done) p.opts.done(skipped);
}
export function skipScene() { if (P && P.def.skip !== false) endScene(true); }

// a mark: [x, y, z] (lab offsets), a zone id, an actor id, or { near: actor, d, side }
function where(m) {
  if (m && m.near) { const a = P.cast.get(m.near) || actors.get(m.near); if (!a) return [0, 0, 0]; const y = a.yaw + (m.side || 0); return [a.pos[0] - Math.sin(y) * (m.d || 2), a.pos[1], a.pos[2] - Math.cos(y) * (m.d || 2)]; }
  return (P && typeof m === 'string' && P.cast.get(m) && P.cast.get(m).pos) || ST.where(m) || [0, 0, 0];
}
const who = (k) => (P && P.cast.get(k)) || actors.get(k);

// ---------------------------------------------------------------- tracks
// { t, cam } { t, say: [who, text, face?] } { t, face: [who, face] } { t, anim: [who, clip] } { t, move: [who, [marks], speed] }
// { t, look: [who, target] } { t, fx: name, at } { t, sfx: name } { t, shake } { t, hitstop: s } { t, impact: 'red' | 'white' }
// { t, fade: [to 0..1, dur] } { t, letterbox: bool } { t, title: [big, small, dur] } { t, boss: id | {...} } { t, slowmo: [k, dur] }
// { t, do: [actions] } { t, hide: who } { t, show: who } { t, wait: cond } (holds the timeline until the condition is true)
function runTrack(tr) {
  if (tr.cam) setCam(tr.cam);
  if (tr.say) say(tr.say);
  if (tr.face) { const a = who(tr.face[0]); if (a) setFace(a, tr.face[1]); }
  if (tr.anim) { const a = who(tr.anim[0]); if (a) play(a, tr.anim[1], { hold: !!tr.anim[2] }); }
  if (tr.move) { const a = who(tr.move[0]); if (a) walkTo(a, tr.move[1].map(where), tr.move[2] || 1.4); }
  if (tr.look) { const a = who(tr.look[0]); if (a) a.lookTarget = tr.look[1]; }
  if (tr.hide) { const a = who(tr.hide); if (a) a.hidden = true; }
  if (tr.show) { const a = who(tr.show); if (a) a.hidden = false; }
  if (tr.sfx) playSfx(tr.sfx);
  if (tr.fx) worldFx(tr.fx, tr.at ? where(tr.at) : null);
  if (tr.shake != null) G.shake = Math.max(G.shake || 0, tr.shake * 2);
  if (tr.hitstop) P.stop = Math.max(P.stop, tr.hitstop);
  if (tr.impact) impact(tr.impact);
  if (tr.fade) { const f = $('stFade'); f.style.transition = `opacity ${tr.fade[1] ?? 0.5}s`; f.style.opacity = tr.fade[0]; }
  if (tr.letterbox != null) bars(tr.letterbox);
  if (tr.title) title(tr.title);
  if (tr.boss) bossCard(tr.boss);
  if (tr.slowmo) { P.slow = tr.slowmo[0]; P.slowEnd = P.t + (tr.slowmo[1] ?? 1); }
  if (tr.do) ST.S.run(tr.do, `scene ${P.def.id}`);
  if (tr.wait) P.waitFor = tr.wait;
}

// camera: a shot preset aimed at actors, or a spline path. built every frame (actors move)
function setCam(c) { P.cam = { ...c, t0: P.t }; if (c.cut !== false && P.camN++ > 0) P.cam.cut = true; }
function camFrame() {
  const c = P.cam; if (!c) return;
  const sp = shotPose(c, c.dur ? Math.min(1, (P.t - c.t0) / c.dur) : 1, who, where, eye());
  if (!sp) return;
  wantShot({ pos: sp.pos, look: sp.look, fov: c.fov || 45, roll: sp.roll, cut: !!c.cut, blend: c.blend ?? 0.5, follow: c.follow ?? 10 });
  c.cut = false;
}

// subtitles: a name tag + the line typing out with the speaker's babble and jaw
function say([k, text, face]) {
  const a = who(k);
  const name = k === 'you' ? 'YOU' : (a && (a.sceneName || (ST.S.defs.npcs[a.id] || {}).name)) || (ST.S.defs.npcs[k] || {}).name || k.toUpperCase();
  for (const x of P.cast.values()) x.talking = false;
  if (a) { a.talking = true; if (face) setFace(a, face); }
  const act = text.startsWith('*');
  P.sub = { a, name, text: act ? text.replace(/\*/g, '') : text, typed: 0, act, until: P.t + 1.2 + text.length * 0.055 };
  sub(P.sub);
}
function sub(s) {
  const el = $('stSub');
  if (!s) { el.classList.add('hidden'); return; }
  el.classList.remove('hidden'); el.classList.toggle('act', s.act);
  el.innerHTML = `${s.act ? '' : `<b>${esc(s.name)}</b><br>`}<span>${esc(s.text.slice(0, Math.floor(s.typed)))}</span>`;
}
function bars(on) { $('stBars').classList.toggle('on', !!on); }
function title(t) {
  const el = $('stTitle');
  if (!t) { el.classList.add('hidden'); return; }
  el.innerHTML = `<div class="st-card" style="position:static;transform:rotate(-3deg)"><div class="t">${esc(t[0])}</div>${t[1] ? `<div class="s">${esc(t[1])}</div>` : ''}</div>`;
  el.classList.remove('hidden'); organic(el.firstChild, { rim: 5, lumps: 4, shadow: [9, 9] });
  if (P) P.titleEnd = P.t + (t[2] ?? 2.5);
}
function impact(kind) {
  const el = $('stImpact');
  el.style.transition = 'none';
  el.style.background = kind === 'white' ? '#fff' : 'radial-gradient(circle at 50% 50%, transparent 0 18%, #ff1030 19% 100%)';
  el.style.opacity = kind === 'white' ? 0.85 : 0.95;
  if (hud.impact) hud.impact(1);
  requestAnimationFrame(() => requestAnimationFrame(() => { el.style.transition = 'opacity 0.35s'; el.style.opacity = 0; }));
}
function playSfx(name) {
  if (name === 'tick') { for (let i = 0; i < 4; i++) synth.tone('square', 2400, 2300, 0.02, 0.25, null, i * 0.5); return; }
  if (name === 'tick_loud') { for (let i = 0; i < 6; i++) { synth.tone('square', 1800, 1700, 0.03, 0.45, null, i * 0.45); synth.noise(0.02, 0.35, 'highpass', 4000, 4000, null, i * 0.45); } return; }
  if (name === 'stinger') { synth.tone('sawtooth', 110, 55, 0.9, 0.35); synth.tone('square', 220, 110, 0.6, 0.18, null, 0.02); synth.noise(0.5, 0.4, 'lowpass', 900, 200); return; }
  if (name === 'clunk') { synth.tone('square', 90, 40, 0.25, 0.45); synth.noise(0.15, 0.5, 'lowpass', 600, 200); return; }
  if (name === 'beep') { synth.tone('sine', 880, 880, 0.18, 0.3); return; }
  if (name === 'whoosh') { synth.noise(0.35, 0.35, 'bandpass', 600, 3000); return; }
  if (name === 'splut') { synth.noise(0.3, 0.6, 'lowpass', 700, 120); synth.tone('sine', 160, 60, 0.25, 0.4); return; }
  if (name === 'ding') { synth.tone('sine', 1320, 1320, 0.6, 0.25); synth.tone('sine', 1980, 1980, 0.4, 0.12); return; }
  if (sfx[name]) sfx[name]();
}
function worldFx(name, at) {
  if (name === 'clocksStop') { $('stFade').style.transition = 'none'; $('stFade').style.background = '#1a0828'; $('stFade').style.opacity = 0.35; requestAnimationFrame(() => { $('stFade').style.transition = 'opacity 2s'; $('stFade').style.opacity = 0; setTimeout(() => { $('stFade').style.background = '#000'; }, 2000); }); }
  if (name === 'confetti' && at) import('../fx.js').then(({ fx }) => { for (let i = 0; i < 4; i++) fx.sparks && fx.sparks([at[0], at[1] + 1.5, at[2]], 0xff4fd8, 18); });
}

// ---------------------------------------------------------------- boss title card (DESIGN §8.2)
function bossCard(b) {
  const el = $('stBoss');
  el.style.setProperty('--bc', b.color || '#ff3030');
  el.innerHTML = `<div class="band"></div><div class="speed"></div><div class="job">${esc(b.job || '')}</div><div class="name">${esc(b.name || '')}</div><div class="sub">"${esc(b.sub || '')}"</div>${b.rehired ? '<div class="stamp">REHIRED</div>' : ''}`;
  el.classList.remove('hidden');
  impact('red'); playSfx('stinger'); G.shake = Math.max(G.shake || 0, 1.4);
  if (P) { P.stop = Math.max(P.stop, 0.25); P.bossEnd = P.t + (b.dur ?? 3.6); P.frozen = true; }
  // the name slams in, then the sub
  const nm = el.querySelector('.name'), sb = el.querySelector('.sub'), jb = el.querySelector('.job');
  nm.animate([{ transform: 'translateX(-60vw) rotate(-4deg) skewX(-20deg)' }, { transform: 'translateX(2vw) rotate(-4deg) skewX(8deg)', offset: 0.7 }, { transform: 'translateX(0) rotate(-4deg)' }], { duration: 380, easing: 'cubic-bezier(.2,1.4,.4,1)' });
  jb.animate([{ opacity: 0, transform: 'translateY(-30px) rotate(-4deg)' }, { opacity: 1, transform: 'rotate(-4deg)' }], { duration: 250, delay: 280, fill: 'both' });
  sb.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, delay: 700, fill: 'both' });
  const st = el.querySelector('.stamp'); if (st) st.animate([{ transform: 'rotate(14deg) scale(3)', opacity: 0 }, { transform: 'rotate(14deg) scale(1)', opacity: 0.92 }], { duration: 260, delay: 1000, fill: 'both', easing: 'cubic-bezier(.2,1.6,.4,1)' });
}

// ---------------------------------------------------------------- panels + recap (panels.js renders the shots)
function startPanels() {
  const d = P.def;
  let list = d.panels || [];
  if (P.kind === 'recap') list = recapPanels();
  P.panels = buildPanels(list, { who, where, headPos, title: P.kind === 'recap' ? 'PREVIOUSLY ON OVERDUE' : d.title || '', crayon: P.kind === 'recap' || d.crayon, playSfx, voiceOf: (k) => (who(k) || {}).voice });
  P.len = d.len ?? P.panels.len;
  $('stPanels').classList.remove('hidden');
}
// the last 3 beats: log entries 'npc|caption' (written by quests / scenes with log:...), newest last
function recapPanels() {
  const log = ST.S.st.log.slice(-3);
  if (!log.length) log.push('auntie|you came out of the machine. you don\'t remember a thing. that\'s fine. nobody here does either.');
  return log.map((l, i) => { const [k, cap] = l.includes('|') ? l.split('|') : ['auntie', l]; return { shot: { target: actors.has(k) ? k : 'auntie', shot: i % 2 ? 'low' : 'closeup' }, cap, at: i * 3.2 }; });
}

// ---------------------------------------------------------------- every frame
export function sceneFrame(dt, now, cam) {
  if (!P && queue.length && !talking()) { const [d, o] = queue.shift(); playScene(d, o); }
  if (!P) return;
  // skip: hold jump
  const hold = K.isDown('jump') && P.def.skip !== false && P.t > 0.3;
  const rd = Math.min(0.5, (now - (P.lastNow ?? now)) / 1000); P.lastNow = now; // (real time: a slow frame rate doesn't make you hold longer)
  P.skipK = hold ? P.skipK + rd / 0.9 : Math.max(0, P.skipK - rd * 2);
  const ring = $('stSkipRing'); if (ring) ring.setAttribute('stroke-dashoffset', String(88 * (1 - Math.min(1, P.skipK))));
  if (P.skipK >= 1) { endScene(true); return; }
  // hit-stop: everything holds (actors, the timeline, the camera)
  if (P.stop > 0) { P.stop -= dt; ST.slowmo = 0; return; }
  if (P.slowEnd && P.t > P.slowEnd) { P.slow = 1; P.slowEnd = 0; }
  ST.slowmo = P.slow;
  const sdt = dt * P.slow;
  if (P.waitFor) { if (ST.S.test(P.waitFor)) P.waitFor = null; else return; }
  if (talking() && P.kind !== 'talk') return; // (a choice opened mid-scene: the scene waits for it)
  P.t += sdt;
  if (P.camN == null) P.camN = 0;
  while (P.i < P.tracks.length && P.tracks[P.i].t <= P.t) runTrack(P.tracks[P.i++]);
  if (!P) return;
  // subtitles type out, the speaker babbles
  if (P.sub) {
    const s = P.sub, before = Math.floor(s.typed);
    s.typed = Math.min(s.text.length, s.typed + sdt * (s.act ? 60 : 30));
    if (s.a && !s.act) for (let i = before; i < Math.floor(s.typed); i++) s.a.voice.blip(s.text[i], i, s.text);
    sub(s);
    if (P.t > s.until && s.typed >= s.text.length) { if (s.a) s.a.talking = false; P.sub = null; sub(null); }
  }
  if (P.titleEnd && P.t > P.titleEnd) { title(null); P.titleEnd = 0; }
  if (P.bossEnd && P.t > P.bossEnd) { $('stBoss').classList.add('hidden'); P.bossEnd = 0; P.frozen = false; }
  for (const a of P.cast.values()) if (a.lookTarget) { const p = typeof a.lookTarget === 'string' ? (who(a.lookTarget) ? headPos(who(a.lookTarget), new THREE.Vector3()) : null) : new THREE.Vector3(...where(a.lookTarget)); if (p) a.lookAt = [p.x, p.y, p.z]; }
  if (P.panels) P.panels.frame(P.t, sdt);
  else if (P.kind === 'boss' && !P.cam) { const b = P.def.boss || P.def; if (b.target) { P.cam = { shot: 'whip', target: b.target, t0: 0 }; } }
  else if (P.kind === 'moment' && !P.cam && P.def.target) P.cam = { shot: 'orbit', target: P.def.target, t0: 0, dur: P.len, turn: 1.2, r: P.def.r ?? 3.6, up: 0.5 };
  if (!P.panels && P.kind !== 'talk') camFrame();
  if (P.t >= P.len && !talking()) endScene(false);
}

export function sceneKey(e) {
  if (!P) return false;
  if (K.matches('menu', e)) return false;
  if (P.kind === 'talk' || talking()) return false; // the talk box takes its own keys
  return true; // a scene eats every other key (hold jump to skip is read in sceneFrame)
}
