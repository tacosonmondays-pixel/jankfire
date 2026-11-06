// OVERDUE story engine, the browser host (WP8). Loaded by main.js only with the story flag (?story=1 or
// localStorage jfStory=1), so the live game never runs any of this. It owns: the story hub (shared/story/story.js) +
// its save, staging content on the map (actors, pickups, zones), turning world happenings into quest events (walking
// into zones, kills, pickups, talking), the talk UI, the quest HUD, the codex and (story/scene.js) cutscenes.
// main.js calls: init(), frame(dt, now, cam) before it renders, key(e) first in its key handler, locked() for input.
// Until the world lane's districts land, the content is the story lab on the Training range (shared/story/content/test).
import * as THREE from 'three';
import { G } from '../ctx.js';
import { ME, eye } from '../player.js';
import { MAP } from '/shared/map.js';
import { K } from '../keys.js';
import { sfx } from '../audio.js';
import { makeStory } from '/shared/story/story.js';
import { toSave, fromSave } from '/shared/story/state.js';
import * as lab from '/shared/story/content/test/lab.js';
import { actors, spawnActor, clearActors, updateActors, dropTo, play } from './actors.js';
import { startTalk, talkKey, talkFrame, talking } from './talk.js';
import { questHud, card as card0, toast } from './questhud.js';
import { toggleCodex, codexOpen } from './codex.js';
import { loadSlot, saveSlot, clearSlot } from './save.js';
import { takeCamera, shotOn } from './camctl.js';

const $ = (id) => document.getElementById(id);
// mission cards wait for a conversation or a scene to finish (they'd be hidden behind it)
const cardQ = [];
const card = (...a) => { if (locked()) cardQ.push(a); else card0(...a); };
export const ST = { S: null, slot: 0, bag: new Set(), staged: '', anchor: [0, 0, 0], things: new Map(), inZone: new Set(), kills: 0, saveT: 0, ready: false, scene: null };
const PACKS = [lab]; // the writing lane's packs join this list (shared/story/content/*)

function merge(packs) {
  const D = { npcs: {}, quests: {}, scenes: {}, codex: {}, zones: {}, things: {} };
  for (const p of packs) for (const k of Object.keys(D)) Object.assign(D[k], p[k] || {});
  return D;
}

export async function init() {
  const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = '/story.css'; document.head.append(css);
  const layer = document.createElement('div'); layer.id = 'stLayer'; document.body.append(layer);
  layer.innerHTML = '<div id="stPrompt" class="hidden"></div>';
  const q = new URLSearchParams(location.search);
  ST.slot = Math.max(0, Math.min(2, Number(q.get('slot')) || 0));
  if (q.get('fresh') === '1') clearSlot(ST.slot);
  const data = await loadSlot(ST.slot);
  const st = fromSave(data);
  if (data && Array.isArray(data.bagStub)) for (const i of data.bagStub.slice(0, 64)) if (typeof i === 'string') ST.bag.add(i);
  ST.S = makeStory({ content: merge(PACKS), state: st, host: HOST });
  ST.ready = true;
  ST.where = where;
  window.JF_STORY = ST; // (tests drive it from here)
  try { const sc = await import('./scene.js'); ST.scene = sc; sc.initScenes(ST); } catch (e) { console.warn('story scenes not loaded', e); }
}

// ---------------------------------------------------------------- the host: what the engine asks the world to do
const HOST = {
  has: (item) => ST.bag.has(item),
  act(a) {
    const arg = a.arg ?? '';
    switch (a.do) {
      case 'give': { const it = a.item ? (a.item.id || a.item.roll || 'item') : arg; ST.bag.add(String(it)); toast(`you got <b>${String(it).replace(/_/g, ' ').toUpperCase()}</b>`); break; }
      case 'take': ST.bag.delete(arg); break;
      case 'coupons': { const n = Number(arg) || 0; ST.S.st.vars.coupons = (ST.S.st.vars.coupons || 0) + n; toast(`<b>${n >= 0 ? '+' : ''}${n}</b> ☺ coupons`); break; }
      case 'toast': toast(arg); break;
      case 'scene': if (ST.scene) ST.scene.playScene(arg); break;
      case 'anim': { const [who, clip] = arg.split('/'); const ac = actors.get(who); if (ac) play(ac, clip); break; }
      default: console.info('story action for the host:', a);
    }
  },
  event(e) {
    const S = ST.S;
    switch (e.type) {
      case 'questStart': card(e.kind === 'main' ? 'start' : 'side', e.title); { const d = S.defs.quests[e.quest]; if (d && d.scenes && d.scenes.start && ST.scene) ST.scene.playScene(d.scenes.start); } break;
      case 'questDone': card('done', e.title, '', e.grade || 'MEETS EXPECTATIONS', 3.2); { const d = S.defs.quests[e.quest]; if (d && d.scenes && d.scenes.end && ST.scene) setTimeout(() => ST.scene.playScene(d.scenes.end), 600); } save(); break;
      case 'questFail': card('fail', e.title); break;
      case 'stepFail': card('fail', (e.why || 'nope').toUpperCase(), 'back to the last checkpoint', '', 2); break;
      case 'stepDone': sfx.click && sfx.click(); save(); break;
      case 'codex': if (e.entry) toast(`${e.entry.kind === 'frag' ? 'OPTION C FRAGMENT' : 'NEW IN THE BOOKS'}: <b>${e.entry.title}</b> (J)`); break;
      case 'meet': toast(`met <b>${e.name}</b>`); break;
      case 'warn': console.warn('story:', e.text); break;
    }
  },
};

export async function save() {
  if (!ST.S) return false;
  const data = { ...toSave(ST.S.st), bagStub: [...ST.bag] };
  return saveSlot(ST.slot, data);
}

// ---------------------------------------------------------------- staging the content on the map
const off = (p) => [ST.anchor[0] + p[0], ST.anchor[1] + p[1], ST.anchor[2] + p[2]];
function stage() {
  const key = G.joined ? MAP.id : '';
  if (key === ST.staged) return;
  ST.staged = key;
  clearActors(); for (const t of ST.things.values()) G.scene.remove(t.mesh); ST.things.clear(); ST.inZone.clear();
  if (!key || key !== 'range') return; // the lab lives on the Training range for now
  ST.anchor = [0, 0, 10];
  const D = ST.S.defs;
  for (const [id, n] of Object.entries(D.npcs)) {
    if (!n.home) continue;
    const a = spawnActor(id, n, off(n.home.p), n.home.face || 0);
    if (n.walk && n.walk.loop) a.loop = n.walk.loop.map(off);
  }
  for (const [id, t] of Object.entries(D.things)) {
    const z = D.zones[t.zone]; if (!z) continue;
    const p = off(z.p); p[1] = dropTo(p);
    const mesh = thingMesh(t.look); mesh.position.set(...p); G.scene.add(mesh);
    ST.things.set(id, { id, t, p, mesh });
  }
  ST.kills = G.kills || 0;
}
function thingMesh(look) { // a big red soup pot (things get real models with their district)
  const g = new THREE.Group();
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.28, 0.42, 14), new THREE.MeshStandardMaterial({ color: 0x8a8f99, roughness: 0.3, metalness: 0.6 })); pot.position.y = 0.21; g.add(pot);
  const soup = new THREE.Mesh(new THREE.CircleGeometry(0.29, 14), new THREE.MeshStandardMaterial({ color: 0xd02a2a, roughness: 0.2 })); soup.rotation.x = -Math.PI / 2; soup.position.y = 0.4; g.add(soup);
  for (const sx of [-1, 1]) { const h = new THREE.Mesh(new THREE.TorusGeometry(0.07, 0.02, 6, 10), pot.material); h.position.set(sx * 0.34, 0.33, 0); h.rotation.y = Math.PI / 2; g.add(h); }
  const glow = new THREE.Mesh(new THREE.RingGeometry(0.45, 0.6, 24), new THREE.MeshBasicMaterial({ color: 0xffe14d, transparent: true, opacity: 0.6, side: THREE.DoubleSide })); glow.rotation.x = -Math.PI / 2; glow.position.y = 0.03; g.add(glow); g.userData.glow = glow;
  return g;
}
// a marker (zone id, npc id or [x, y, z]) -> world point
export function where(m) {
  if (Array.isArray(m)) return off(m);
  const a = actors.get(m); if (a) return a.pos;
  const z = ST.S.defs.zones[m]; if (z) return off(z.p);
  return null;
}

// ---------------------------------------------------------------- every frame
let nearAct = null, nearThing = null, wasSaveable = 0;
export function locked() { return talking() || (ST.scene && ST.scene.playing()) || codexOpen(); }

export function frame(dt, now, cam) {
  if (!ST.ready) return;
  stage();
  const S = ST.S, e = eye();
  if (ST.staged) {
    updateActors(dt * (ST.slowmo ?? 1), now, e);
    S.tick(dt);
    // zones: walking in / out
    for (const [id, z] of Object.entries(S.defs.zones)) {
      const p = off(z.p), inside = Math.hypot(ME.pos[0] - p[0], ME.pos[2] - p[2]) < (z.r || 2) && Math.abs(ME.pos[1] - p[1]) < 4;
      if (inside && !ST.inZone.has(id)) { ST.inZone.add(id); S.emit({ type: 'reach', zone: id }); }
      else if (!inside && ST.inZone.has(id)) { ST.inZone.delete(id); S.emit({ type: 'leave', zone: id }); }
    }
    // kills: every kill on the range is a dummy (the "interns")
    if ((G.kills || 0) > ST.kills) { S.emit({ type: 'kill', kind: 'dummy', n: G.kills - ST.kills }); ST.kills = G.kills; }
    else ST.kills = G.kills || 0;
    // what's in reach: a person (talk) or a thing (pick up)
    nearAct = null; nearThing = null;
    if (!locked() && ME.alive) {
      let bd = 3.0;
      for (const a of actors.values()) { const d = Math.hypot(e[0] - a.pos[0], e[2] - a.pos[2]); if (d < bd && S.defs.npcs[a.id] && S.defs.npcs[a.id].lines) { bd = d; nearAct = a; } }
      for (const t of ST.things.values()) {
        t.mesh.visible = S.test(t.t.if) && !ST.bag.has(t.t.item);
        if (t.mesh.visible) { t.mesh.userData.glow.material.opacity = 0.35 + Math.sin(now * 0.006) * 0.25; if (Math.hypot(ME.pos[0] - t.p[0], ME.pos[2] - t.p[2]) < 1.8) nearThing = t; }
      }
    }
  }
  const pr = $('stPrompt');
  const txt = nearThing ? `<b>${K.label('use')}</b> PICK UP ${nearThing.t.name}` : nearAct ? `<b>${K.label('use')}</b> TALK TO ${S.defs.npcs[nearAct.id].name}` : '';
  if (pr.innerHTML !== txt) pr.innerHTML = txt;
  pr.classList.toggle('hidden', !txt);
  talkFrame(dt, now, e);
  if (ST.scene) ST.scene.sceneFrame(dt, now, cam);
  questHud(S.quests.objectives(), where, cam, !ST.staged || (ST.scene && ST.scene.playing()) || talking());
  if (takeCamera(cam, dt)) G.vmScene.visible = false; // (the gun goes away for the shot)
  if (cardQ.length && !locked() && now > (ST.cardT || 0)) { card0(...cardQ.shift()); ST.cardT = now + 1500; }
  ST.saveT += dt;
}

export function key(e) {
  if (!ST.ready) return false;
  if (ST.scene && ST.scene.sceneKey(e)) return true;
  if (talkKey(e)) return true;
  if (e.code === 'KeyJ' && !e.repeat && e.type === 'keydown') { toggleCodex(ST.S); return true; }
  if (codexOpen()) { if (K.matches('menu', e)) toggleCodex(ST.S, false); return true; }
  if (K.matches('use', e) && !e.repeat) {
    if (nearThing) { const t = nearThing; ST.bag.add(t.t.item); sfx.cash && sfx.cash(); toast(`picked up <b>${t.t.name}</b>`); ST.S.emit({ type: 'pickup', item: t.t.item }); ST.S.emit({ type: 'interact', thing: t.id }); return true; }
    if (nearAct) { if (document.pointerLockElement) { /* keep the lock: answers are on the number keys */ } startTalk(ST.S, nearAct.id, 'start', () => save()); return true; }
  }
  return false;
}
