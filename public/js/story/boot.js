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
import * as overdue from '/shared/story/content/overdue.js'; // the full script, as an engine pack (PR #76)
import { PLACES } from '/shared/city/slice.js'; // the world lane's real spots for the script's zones (the slice city)
import { npcSpot, HINTS } from '/shared/city/cast_slice.js';
import { RAMP } from '/shared/city/act1set.js'; // (the Unpaid's jump ramp over the collapse: JUMP IT) // ...and where the cast stands in it (per mission step)
import { actors, spawnActor, despawnActor, clearActors, updateActors, dropTo, play } from './actors.js';
import { otFrame } from './overtime.js'; // (mr. overtime's clips, marks, damage and fx)
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
// the content: the script (default), or the small engine lab (?lab=1, and always on the Training range ?storylab=1)
export const LAB = /[?&](lab|storylab)=1\b/.test(location.search);
const OTPREV = /[?&]otpreview=1\b/.test(location.search);
const PACKS = LAB ? [lab] : [overdue];

function merge(packs) {
  const D = { npcs: {}, quests: {}, scenes: {}, codex: {}, zones: {}, things: {}, bosses: {}, cast: {}, init: [], autostart: [] };
  for (const p of packs) for (const k of Object.keys(D)) { if (Array.isArray(D[k])) D[k].push(...(p[k] || [])); else Object.assign(D[k], p[k] || {}); }
  for (const [id, n] of Object.entries(D.npcs)) { const c = D.cast[id]; if (c) n.hint = { body: c.body, desc: c.look }; } // (a seeded look for anyone without a model yet)
  return D;
}

export async function init() {
  const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = '/story.css'; document.head.append(css);
  const layer = document.createElement('div'); layer.id = 'stLayer'; document.body.append(layer);
  layer.innerHTML = '<div id="stPrompt" class="hidden"></div>';
  const q = new URLSearchParams(location.search);
  ST.slot = Math.max(0, Math.min(2, Number(q.get('slot')) || 0));
  if (q.get('fresh') === '1') clearSlot(ST.slot);
  try { const { loadCast, LOOK_IDS } = await import('./looks.js'); await loadCast(LOOK_IDS, 12000); } catch (e) { console.warn('cast models', e); } // (the Blender cast; missing = code puppets)
  const data = await loadSlot(ST.slot);
  const st = fromSave(data);
  if (data && Array.isArray(data.bagStub)) for (const i of data.bagStub.slice(0, 64)) if (typeof i === 'string') ST.bag.add(i);
  ST.S = makeStory({ content: merge(PACKS), state: st, host: HOST });
  ST.ready = true;
  ST.where = where; ST.offYaw = (y) => offYaw(y); ST.sync = () => sync(true); // (sync: the engine's state to the sim right now, before a travel's save)
  window.JF_STORY = ST; ST.spots = SPOTS; // (tests drive it from here; spots: the glowing pick-up / use spots)
  try { const sc = await import('./scene.js'); ST.scene = sc; sc.initScenes(ST); } catch (e) { console.warn('story scenes not loaded', e); }
  try { const bf = await import('./bossfight.js'); ST.boss = bf.makeBoss(ST, { where, playScene: (id, o) => ST.scene && ST.scene.playScene(id, o) }); } catch (e) { console.warn('boss hooks not loaded', e); } // (phases, cutscenes, the boss's poses)
  try { const en = await import('./encounters.js'); ST.enc = en.makeEncounters(ST, { where }); } catch (e) { console.warn('encounters not loaded', e); } // (Act I's set pieces: the soup run, the ambush, the dogs, the collectors)
}

// ---------------------------------------------------------------- the host: what the engine asks the world to do
const S0 = () => ST.S;
// the inventory: the systems lane's real bag (G.story.inv, WP3/WP5) when it's there, else the stand-in bag (bagStub)
const INV = () => (G.story && G.story.inv && typeof G.story.inv.has === 'function' ? G.story.inv : null);
export const bag = {
  has: (b) => (INV() ? INV().has(b.startsWith('implant.') ? b.slice(8) : b, 1) || ST.bag.has(b) : ST.bag.has(b)), // (has.implant.X asks for the implant)
  give: (b, n = 1) => { if (INV()) INV().give(b, n); else ST.bag.add(b); },
  take: (b, n = 1) => { if (INV()) INV().take(b, n); else ST.bag.delete(b); },
};
ST.inv = bag;
const HOST = {
  has: (item) => bag.has(item),
  act(a) {
    const arg = a.arg ?? '';
    switch (a.do) {
      case 'give': { const it = a.item ? (a.item.id || a.item.roll || 'item') : arg; bag.give(String(it)); toast(`you got <b>${String(it).replace(/_/g, ' ').toUpperCase()}</b>`); break; }
      case 'take': bag.take(arg); break;
      case 'coupons': { const n = Number(arg) || 0; if (INV() && INV().coupons) INV().coupons(n); ST.S.st.vars.coupons = (ST.S.st.vars.coupons || 0) + n; toast(`<b>${n >= 0 ? '+' : ''}${n}</b> ☺ coupons`); break; }
      case 'toast': toast(arg); break;
      case 'scene': if (ST.scene) ST.scene.playScene(arg); break;
      case 'anim': { const [who, clip] = arg.split('/'); const ac = actors.get(who); if (ac) play(ac, clip); break; }
      // the script's host actions (docs/story/SCHEMA.md "Additions from the script"). the systems behind most of these
      // (bosses, loot, implants, late fees, the pager) belong to other lanes: until they land, a toast says what happened
      case 'talk': { const [n, node] = arg.split('/'); if (S0().defs.npcs[n]) (ST.talkQ ||= []).push([n, node || 'start']); break; } // (opens next frame, after whatever's talking now)
      case 'turf': { const [d, f] = arg.split('='); toast(`<b>${String(d).toUpperCase()}</b> is run by <b>${String(f).toUpperCase()}</b> now`); break; }
      case 'boss': { const b = S0().defs.bosses[arg] || {}; const [name, job] = String(b.card || arg).split(' · '); if (ST.scene) ST.scene.playScene({ id: 'boss_' + arg, kind: 'boss', skip: true, boss: { name, job: job || '', sub: b.subtitle || '' } }); break; }
      // enemies, for the systems lane's referee (the story worker's Room): spawn:<kind>@<zone>*<n> despawn:<kind|id> hurt:<id>=<dmg>
      case 'spawn': { const m = /^([a-z0-9_]+)(?:@([^*]+))?(?:\*(\d+))?$/.exec(arg); if (!m) break; const at = m[2] ? where(m[2]) : [ME.pos[0], ME.pos[1], ME.pos[2]];
        if (at && G.story && G.story.send) G.story.send('spawn', { kind: m[1], at: [...at], n: Math.min(20, Number(m[3]) || 1), ...(S0().defs.npcs[m[1]] ? { id: m[1], look: m[1] } : {}) }); break; }
      case 'despawn': if (G.story && G.story.send) G.story.send('despawn', /^[a-z0-9_]+$/.test(arg) ? (actors.has(arg) || S0().defs.npcs[arg] ? { id: arg } : { kind: arg }) : {}); break;
      case 'hurt': { const [id, d] = arg.split('='); const dmg = Number(d); if (G.story && G.story.send && /^[a-z0-9_]+$/.test(id) && Number.isFinite(dmg)) G.story.send('damage', { id, dmg, why: 'script' }); break; }
      case 'loot': toast(`LOOT DROP: <b>${arg.replace(/_/g, ' ')}</b>`); break;
      case 'implant': if (INV()) INV().give(arg, 1); ST.bag.add('implant.' + arg); toast(`IMPLANT: <b>${arg.replace(/_/g, ' ')}</b>`); break;
      case 'fees': S0().st.vars.fees = Math.max(0, (S0().st.vars.fees || 0) + (Number(arg) || 0)); toast(`LATE FEES <b>${'☺'.repeat(Math.min(5, S0().st.vars.fees))}</b>`); break;
      case 'call': toast(`☺ PAGER: <b>${(S0().defs.npcs[arg] || { name: arg }).name}</b> is calling`); break;
      case 'unlock': toast(`unlocked: <b>${(S0().defs.zones[arg] || { name: arg }).name}</b>`); break;
      case 'collect': toast(`collected: <b>${arg.replace(/_/g, ' ')}</b>`); break;
      case 'music': break;
      default: console.info('story action for the host:', a);
    }
  },
  event(e) {
    const S = ST.S;
    switch (e.type) {
      case 'questStart': card(e.kind === 'main' ? 'start' : 'side', e.title); { const d = S.defs.quests[e.quest]; if (d && d.scenes && d.scenes.start && ST.scene) ST.scene.playScene(d.scenes.start); } break;
      case 'questDone': setTimeout(autostart, 0); card('done', e.title, '', (ST.enc && ST.enc.grade(e.quest)) || e.grade || 'MEETS EXPECTATIONS', 3.2); { const d = S.defs.quests[e.quest]; if (d && d.scenes && d.scenes.end && ST.scene) setTimeout(() => ST.scene.playScene(d.scenes.end), 600); } save(); break;
      case 'questFail': card('fail', e.title); break;
      case 'stepFail': card('fail', (e.why || 'nope').toUpperCase(), 'back to the last checkpoint', '', 2); break;
      case 'stepDone': sfx.click && sfx.click(); save(); break;
      case 'stepStart': { const h = ST.city && HINTS[`${e.quest}.${e.step}`]; if (h) setTimeout(() => { card('step', h.call, '', '', 1.8); toast(h.how.replace(/\{(\w+)\}/g, (_, k) => K.label(k)), 6); }, 900); break; } // (the tutorial's moves: cast_slice.js HINTS)
      case 'codex': if (e.entry) toast(`${e.entry.kind === 'frag' ? 'OPTION C FRAGMENT' : 'NEW IN THE BOOKS'}: <b>${e.entry.title}</b> (J)`); break;
      case 'meet': toast(`met <b>${e.name}</b>`); break;
      case 'warn': console.warn('story:', e.text); break;
    }
  },
};

// story mode (WP0's shell): the engine's state goes to the sim, which writes the real save slot. outside it (the
// Training-range lab, ?storylab=1) a local stand-in slot
let synced = '';
function sync(force) {
  if (!inStory() || !ST.S) return;
  const st = toSave(ST.S.st), key = JSON.stringify([st, [...ST.bag], ST.S.st.vars.coupons | 0]);
  if (!force && key === synced) return;
  synced = key;
  G.story.send('engine', INV() ? { st } : { st, bag: [...ST.bag], coupons: Math.max(0, ST.S.st.vars.coupons | 0) }); // (with the real bag the sim owns items + coupons)
}
const inStory = () => !!(G.story && G.joined && G.mode === 'story');
export async function save(why = 'quest') {
  if (!ST.S) return false;
  if (inStory()) { sync(true); G.story.save(why); return true; }
  const data = { ...toSave(ST.S.st), bagStub: [...ST.bag] };
  return saveSlot(ST.slot, data);
}

// ---------------------------------------------------------------- staging the content on the map
// where the lab goes: the story test lot (WP0), turned to face you from the spawn; or the Training range (?storylab=1)
const LABS = { story_test: { o: [0, 0, 6], rot: Math.PI }, range: { o: [0, 0, 10], rot: 0 } };
let labAt = LABS.range;
const off = (p) => { const c = Math.cos(labAt.rot), sn = Math.sin(labAt.rot); return [labAt.o[0] + p[0] * c + p[2] * sn, labAt.o[1] + p[1], labAt.o[2] - p[0] * sn + p[2] * c]; };
const offYaw = (y) => y + labAt.rot;
function stage() {
  const key = G.joined ? MAP.id + (inStory() ? ':story' : '') : '';
  if (key === ST.staged) return;
  ST.staged = key;
  clearActors(); for (const t of ST.things.values()) G.scene.remove(t.mesh); ST.things.clear(); ST.inZone.clear();
  for (const sp of SPOTS.values()) G.scene.remove(sp.mesh); SPOTS.clear(); for (const s0 of REH.signs) G.scene.remove(s0); REH.signs = [];
  const where0 = G.joined && ((MAP.id === 'story_test' || MAP.id === 'story_slice' || MAP.id === 'story_train') && inStory() && !LAB ? MAP.id : MAP.id === 'story_test' && inStory() ? 'story_test' : MAP.id === 'range' && LAB && /[?&]storylab=1\b/.test(location.search) ? 'range' : '');
  if (!where0) { ST.on = false; return; }
  ST.on = true;
  labAt = LABS[where0] || LABS.story_test;
  ST.city = where0 === 'story_slice';
  if (inStory() && G.story.cur) { // the save slot the shell loaded: pick up exactly where it was
    const d = G.story.cur.data || {};
    ST.S.st = fromSave(d); ST.bag.clear();
    if (Array.isArray(d.bagStub)) for (const i of d.bagStub.slice(0, 64)) if (typeof i === 'string') ST.bag.add(i);
    ST.S.st.vars.coupons = G.story.cur.coupons || ST.S.st.vars.coupons || 0;
    synced = '';
    if (ST.scene && Object.keys(ST.S.st.quests).length && ST.S.st.log.length && !ST.recapped) { ST.recapped = true; setTimeout(() => ST.scene.playScene({ id: 'recap', kind: 'recap', skip: true }), 1500); } // PREVIOUSLY ON OVERDUE
  }
  const D = ST.S.defs;
  if (inStory() && G.story.fromSim) { G.story.fromSim = false; ST.simBack = performance.now() + 1500; } // back from a sim match (main.js onMain): you won the opening sim (frame() sets it, after the save has loaded)
  if (!LAB) { // the script: lay it out, start a new game once, offer the quests that can start
    rehearse();
    if (!ST.S.st.flags.init_done) { ST.S.run(D.init || []); ST.S.st.flags.init_done = true; for (const z of Object.values(D.zones)) if (z.district) ST.S.st.vars[`clock.${z.district}`] ??= 17 * 60 + 29; }
    autostart();
    ST.kills = G.kills || 0;
    return;
  }
  for (const [id, n] of Object.entries(D.npcs)) {
    if (!n.home) continue;
    const a = spawnActor(id, n, off(n.home.p), offYaw(n.home.face || 0));
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
  if (Array.isArray(m)) return LAB ? off(m) : m;
  const a = actors.get(m); if (a) return a.pos;
  const mk = ST.marks && ST.marks[m]; if (mk) return LAB ? off(mk) : mk; // (the world lane's arena marks: ot_enter, arena.boss...)
  const z = ST.S.defs.zones[m]; if (z) return z.p ? (LAB ? off(z.p) : z.p) : REH.zones[m] || null;
  const r = ROSTER.get(m); if (r) return r.p;
  return null;
}

// ---------------------------------------------------------------- the rehearsal: the script on the test lot
// until the world lane's districts give the zones coordinates, every zone gets a labelled spot on the lot (districts
// clustered), people stand at their home zone (spawned when you're near), and whatever the current step needs to be
// picked up or used shows up as a glowing spot at its zone. R fakes the tracked step's next goal (for the parts the
// other lanes haven't built yet: the sims, cars, bosses, Late Fees...).
const REH = { zones: {}, signs: [] }, ROSTER = new Map(), SPOTS = new Map();
function rehearse() {
  const D = ST.S.defs;
  REH.zones = {}; for (const s0 of REH.signs) G.scene.remove(s0); REH.signs = [];
  if (MAP.id === 'story_train') { ROSTER.clear(); return; } // the train (m06's fight): no streets to lay the script out on, nobody standing about
  // in the slice city the world lane's PLACES are the real spots; on the test lot (or for zones it doesn't have yet)
  // the rehearsal grid round the Lost & Found
  const city = ST.city, c0 = city ? PLACES['bottom:lostfound'].p : [0, 0, -4];
  const fixed = city ? {} : { 'bottom:machine': [0, 0, -11.8], 'bottom:lostfound': [0, 0, -4] };
  if (city) for (const [id, pl] of Object.entries(PLACES)) if (D.zones[id] && !D.zones[id].p) fixed[id] = pl.p.slice();
  const ids = Object.keys(D.zones).filter((z) => !D.zones[z].p).sort((a, b) => (D.zones[a].district || '').localeCompare(D.zones[b].district || '') || a.localeCompare(b));
  const slots = [], span = city ? 30 : 34;
  for (let z = -span; z <= span; z += 6.5) for (let x = -span; x <= span; x += 6.5) if (city || (Math.hypot(x, z - 6) > 6 && Math.hypot(x, z + 12) > 6 && Math.hypot(x, z + 4) > 4)) slots.push([c0[0] + x, c0[1], c0[2] + (city ? 34 + z : z + 4)]); // (city: the rehearsal yard is the street south of the depot)
  slots.sort((a, b) => Math.hypot(a[0] - c0[0], a[2] - c0[2]) - Math.hypot(b[0] - c0[0], b[2] - c0[2])); // act I's districts sort first, so they land nearest the Lost & Found
  let i = 0;
  // (a real place in the city keeps its height: dropped from just above it, not from 30 m up onto a roof; and its own reach: a car, a roof, a doorway)
  for (const id of ids) { const p = fixed[id] || slots[i++] || c0.slice(); p[1] = dropTo([p[0], p[1], p[2]], city && fixed[id] ? 1.5 : 30); REH.zones[id] = p; D.zones[id].r = city && PLACES[id] && PLACES[id].r ? PLACES[id].r : Math.min(D.zones[id].r || 2.5, city && fixed[id] ? 4 : 2.5); if (city ? fixed[id] : !fixed[id] || id === 'bottom:lostfound') REH.signs.push(sign(D.zones[id].name || id, p)); } // (the city: only real places get a sign; the rest of the script's zones wait in the yard unseen)
  ROSTER.clear();
  const at = {};
  for (const [id, n] of Object.entries(D.npcs)) {
    if (id === 'choice' || id === 'change') continue;
    const sp = city && npcSpot(id, ST.S.quests.objectives()); // (the slice: an exact spot, not a ring round the place)
    if (sp) { ROSTER.set(id, { id, n, p: sp.p.slice(), face: sp.face, spot: sp }); continue; }
    if (!n.home) continue;
    const zp = n.home.p ? n.home.p : REH.zones[n.home.zone];
    if (!zp) continue;
    const k = (at[n.home.zone] = (at[n.home.zone] || 0) + 1) - 1, a = k * 2.1 + 0.6;
    ROSTER.set(id, { id, n, p: [zp[0] + Math.sin(a) * (k ? 1.7 : 1.2), zp[1], zp[2] + Math.cos(a) * (k ? 1.7 : 1.2)], face: a + Math.PI, yard: city && !PLACES[n.home.zone] });
  }
}
function sign(text, p) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 48;
  const g = c.getContext('2d'); g.fillStyle = 'rgba(18,8,24,0.85)'; g.fillRect(0, 0, 256, 48); g.strokeStyle = '#ff4fd8'; g.lineWidth = 4; g.strokeRect(2, 2, 252, 44);
  g.font = 'bold 20px "Comic Neue", cursive'; g.fillStyle = '#ffe14d'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(text).slice(0, 26).toUpperCase(), 128, 25);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false })); sp.scale.set(2.6, 0.5, 1); sp.position.set(p[0], p[1] + 3.1, p[2]);
  G.scene.add(sp); return sp;
}
// people near you are in the world, the rest wait (59 of them would be a lot of draw calls)
function roster(e) {
  if (ST.city) { // a mission step can move someone (cast_slice.js STAGE): they're there when you arrive (not mid-talk or mid-scene)
    const objs = ST.S.quests.objectives();
    for (const r of ROSTER.values()) { const sp = npcSpot(r.id, objs); if (!sp || sp === r.spot) continue; const a = actors.get(r.id); if (a && (a.inScene || a.boss || talking())) continue; r.spot = sp; r.p = sp.p.slice(); r.face = sp.face; if (a) despawnActor(r.id); }
  }
  // (the city: someone whose home isn't a real place yet only stands in the rehearsal yard while a step wants them)
  const want = ST.city ? new Set(ST.S.quests.objectives().flatMap((o) => [o.marker, ...o.goals.map((g) => g.marker)])) : null;
  for (const r of ROSTER.values()) {
    const d = Math.hypot(e[0] - r.p[0], e[2] - r.p[2]), a = actors.get(r.id);
    if (r.yard && !want.has(r.id)) { if (a && !a.inScene && !a.boss && !talking()) despawnActor(r.id); continue; }
    if (!a && d < 34) spawnActor(r.id, r.n, r.p, r.face);
    else if (a && d > 44 && !a.inScene && !a.boss && !a.enc && !talking()) despawnActor(r.id); // (a boss in a fight stays: the referee has him. so does anyone an encounter stood somewhere: encounters.js)
  }
}
// what the current steps want picked up / used, as spots at their zones (+ collectibles you can find)
function spots() {
  const S = ST.S, D = S.defs, want = new Map();
  for (const o of S.quests.objectives()) {
    const q = D.quests[o.quest], st = q && q.steps.find((x) => x.id === o.step);
    if (!st) continue;
    for (const g of st.goals || (st.goal ? [st.goal] : [])) {
      if (g.type === 'pickup') { const z = g.zone || g.marker || st.marker; if (z && where(z)) want.set('p:' + g.item, { kind: 'pickup', item: g.item, zone: z, name: String(g.item).replace(/_/g, ' ') }); }
      if (g.type === 'interact') { const th = D.things[g.thing], z = th ? th.zone : D.zones[g.thing] ? g.thing : g.marker; if (z && where(z)) want.set('i:' + g.thing, { kind: 'interact', thing: g.thing, zone: z, name: (th && th.name) || (D.zones[z] && D.zones[z].name) || g.thing }); }
    }
  }
  for (const [id, th] of Object.entries(D.things)) if (th.zone && REH.zones[th.zone] && !S.st.flags['used.' + id] && (!th.if || S.test(th.if)) && th.do) want.set('t:' + id, { kind: 'thing', thing: id, zone: th.zone, name: th.name || id, th });
  for (const [k, sp] of SPOTS) if (!want.has(k)) { G.scene.remove(sp.mesh); SPOTS.delete(k); }
  let n = 0;
  for (const [k, w] of want) if (!SPOTS.has(k)) { const p = where(w.zone).slice(); const j = n++ * 1.3, rr = w.kind === 'thing' && ST.city ? 3 : 1.4; p[0] += Math.sin(j) * rr; p[2] += Math.cos(j) * rr; // (city: collectibles a step further out than the quest's own spot)
     p[1] = dropTo(p); const mesh = w.kind === 'pickup' && w.item === 'soup_pot' ? thingMesh('pot') : spotMesh(w.kind); mesh.position.set(...p); G.scene.add(mesh); SPOTS.set(k, { ...w, p, mesh }); }
}
function spotMesh(kind) {
  const g = new THREE.Group();
  const col = kind === 'pickup' ? 0xffe14d : kind === 'thing' ? 0x4fd8ff : 0xff4fd8;
  if (kind === 'pickup') { const b = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.4, 0.4), new THREE.MeshStandardMaterial({ color: 0x8a6a3a, roughness: 0.7 })); b.position.y = 0.2; g.add(b); const lid = new THREE.Mesh(new THREE.BoxGeometry(0.54, 0.06, 0.44), new THREE.MeshStandardMaterial({ color: col })); lid.position.y = 0.43; g.add(lid); }
  else { const o = new THREE.Mesh(new THREE.OctahedronGeometry(0.22), new THREE.MeshBasicMaterial({ color: col })); o.position.y = 1.1; g.add(o); g.userData.spin = o; }
  const glow = new THREE.Mesh(new THREE.RingGeometry(0.45, 0.6, 24), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.6, side: THREE.DoubleSide })); glow.rotation.x = -Math.PI / 2; glow.position.y = 0.03; g.add(glow); g.userData.glow = glow;
  return g;
}
// R in the rehearsal: fake the tracked step's next goal (with the events a finished system would send)
function fakeGoal() {
  const S = ST.S, o = S.quests.objectives()[0];
  if (!o) return false;
  const q = S.defs.quests[o.quest], st = q.steps.find((x) => x.id === o.step), G0 = st.goals || (st.goal ? [st.goal] : []);
  const i = G0.findIndex((g, k) => !o.goals[k].done && !g.optional);
  const g = G0[i < 0 ? 0 : i];
  if (!g) { S.tick(st.timer ? 0 : 0.01); return true; }
  const map = { reach: 'reach', leave: 'leave', talk: 'talk', kill: 'kill', killBoss: 'killBoss', pickup: 'pickup', interact: 'interact', photo: 'photo', escort: 'reach', loseFees: 'loseFees', enterCar: 'enterCar', use: 'use', scene: 'sceneEnd', deliver: 'talk' };
  if (g.type === 'flag') S.run([`flag:${String(g.flag || '').replace(/^flag\./, '')}`]);
  else if (g.type === 'wait' || g.type === 'survive') S.tick((g.t || 0) + 0.1);
  else { if (g.type === 'deliver' || g.item) ST.bag.add(g.item); S.emit({ type: map[g.type], zone: g.zone, npc: g.npc || g.to, node: g.node, kind: Array.isArray(g.kind) ? g.kind[0] : g.kind, item: g.item, thing: g.thing, boss: g.boss, car: g.car, target: g.target, scene: g.scene, n: g.n || 1 }); }
  toast(`REHEARSAL: faked <b>${(g.text || o.text || g.type).slice(0, 60)}</b>`);
  return true;
}
function autostart() { if (LAB) return; for (const id of ST.S.defs.autostart) ST.S.quests.start(id); }

// ---------------------------------------------------------------- every frame
let nearAct = null, nearThing = null, wasSaveable = 0;
export function locked() { return talking() || (ST.scene && ST.scene.playing()) || codexOpen(); }

export function frame(dt, now, cam) {
  if (!ST.ready) return;
  // capture mode (tools/scene.cjs): the story advances one fixed step per recorded frame, however slow the renderer is
  if (ST.capture) { dt = ST.capStep || 0; ST.capStep = 0; now = ST.capNow = (ST.capNow || now) + dt * 1000; }
  stage();
  const S = ST.S, e = eye();
  if (!ST.on && ST.boss && ST.boss.train) ST.boss.train.tick(dt); // (left the train for a sim or the menu: it takes its tunnel down)
  if (ST.on) {
    if (inStory() && (ST.syncT = (ST.syncT || 0) + dt) > 2) { ST.syncT = 0; sync(); } // (the shell's own auto / pause saves get it too)
    if (!LAB && (ST.rT = (ST.rT || 0) + dt) > 0.25) { ST.rT = 0; roster(e); spots(); }
    if (ST.boss && ST.boss.tick) ST.boss.tick(dt); // (the referee's boss: the actor stands where the room has him)
    if (ST.enc) ST.enc.frame(dt, now); // (before the actors move: whoever rides in a car is placed this frame)
    updateActors(dt * (ST.slowmo ?? 1), now, e);
    otFrame(dt * (ST.slowmo ?? 1), cam);
    if (ST.boss && (ST.bT = (ST.bT || 0) + dt) > 0.25) { ST.bT = 0; ST.boss.frame(); }
    { const busy = !!(ST.scene && ST.scene.playing()) || talking(); if (busy !== !!ST.held) { ST.held = busy; if (G.story && G.story.send) G.story.send('hold', { all: true, on: busy }); } } // (the referee freezes enemies through cutscenes and talks)
    if (OTPREV && (ST.otW = (ST.otW || 0) + dt) > 3) { if (!ST.otPrev) { ST.otPrev = import('./otpreview.js').then((m) => { m.start(); ST.otPrevM = m; }); } else if (ST.otPrevM) ST.otPrevM.previewFrame(dt * (ST.slowmo ?? 1)); } // (?otpreview=1: overtime's rehearsal)
    if (ST.talkQ && ST.talkQ.length && !talking()) { const [n, node] = ST.talkQ.shift(); startTalk(ST.S, n, node, () => save('talk')); }
    if (ST.simBack && now > ST.simBack) { ST.simBack = 0; if (!S.st.flags.sim_won) { S.run(['flag:sim_won']); card('step', 'TRAINING COMPLETE', 'the machine hums. something is coming out.', '', 2.4); } }
    S.tick(dt);
    // zones: walking in / out
    for (const [id, z] of Object.entries(S.defs.zones)) {
      const p = where(id); if (!p) continue;
      const inside = Math.hypot(ME.pos[0] - p[0], ME.pos[2] - p[2]) < (z.r || 2) && Math.abs(ME.pos[1] - p[1]) < 4;
      if (inside && !ST.inZone.has(id)) { ST.inZone.add(id); S.emit({ type: 'reach', zone: id }); }
      else if (!inside && ST.inZone.has(id)) { ST.inZone.delete(id); S.emit({ type: 'leave', zone: id }); }
    }
    // cars: getting in a driver's seat (drive.js) is the enterCar goal (m02's "steal a car")
    { const drv = !!(G.story && G.story.hideVM && G.story.hideVM()); if (drv && !ST.drv) S.emit({ type: 'enterCar' }); ST.drv = drv; if (drv && ST.city) rampCalls(); }
    // kills: every kill on the range is a dummy (the "interns")
    if ((G.kills || 0) > ST.kills) { S.emit({ type: 'kill', kind: 'dummy', n: G.kills - ST.kills }); ST.kills = G.kills; }
    else ST.kills = G.kills || 0;
    // what's in reach: a person (talk) or a thing (pick up)
    nearAct = null; nearThing = null;
    if (!locked() && ME.alive) {
      let bd = 9;
      // the one you're looking at wins over the one who's merely closest (people stand in groups)
      const fx = -Math.sin(ME.yaw), fz = -Math.cos(ME.yaw);
      for (const a of actors.values()) {
        const dx = a.pos[0] - e[0], dz = a.pos[2] - e[2], d = Math.hypot(dx, dz);
        if (d > 3.0 || a.hidden || !S.defs.npcs[a.id] || !S.defs.npcs[a.id].lines) continue;
        const score = d + (1 - (dx * fx + dz * fz) / Math.max(0.01, d)) * 1.5;
        if (score < bd) { bd = score; nearAct = a; }
      }
      let sd = 1.8; // (the nearest spot gets F; a quest's spot beats a collectible lying next to it)
      for (const sp of SPOTS.values()) { sp.mesh.visible = true; sp.mesh.userData.glow.material.opacity = 0.35 + Math.sin(now * 0.006) * 0.25; if (sp.mesh.userData.spin) sp.mesh.userData.spin.rotation.y += dt * 2; const d = Math.hypot(ME.pos[0] - sp.p[0], ME.pos[2] - sp.p[2]) + (sp.kind === 'thing' ? 0.5 : 0); if (d < sd) { sd = d; nearThing = { spot: sp, t: { name: sp.name.toUpperCase() } }; } }
      for (const t of ST.things.values()) {
        t.mesh.visible = S.test(t.t.if) && !bag.has(t.t.item);
        if (t.mesh.visible) { t.mesh.userData.glow.material.opacity = 0.35 + Math.sin(now * 0.006) * 0.25; if (Math.hypot(ME.pos[0] - t.p[0], ME.pos[2] - t.p[2]) < 1.8) nearThing = t; }
      }
    }
  }
  if (locked()) for (const sp of SPOTS.values()) sp.mesh.visible = false; // (markers stay out of the talk and scene shots)
  const pr = $('stPrompt');
  const txt = nearThing ? `<b>${K.label('use')}</b> ${nearThing.spot && nearThing.spot.kind !== 'pickup' ? 'USE' : 'PICK UP'} ${nearThing.t.name}` : nearAct ? `<b>${K.label('use')}</b> TALK TO ${S.defs.npcs[nearAct.id].name}` : '';
  if (pr.innerHTML !== txt) pr.innerHTML = txt;
  pr.classList.toggle('hidden', !txt);
  talkFrame(dt, now, e);
  if (ST.scene) ST.scene.sceneFrame(dt, now, cam);
  questHud(hudObjs(S), where, cam, !ST.on || (ST.scene && ST.scene.playing()) || talking());
  if (takeCamera(cam, dt)) G.vmScene.visible = false; // (the gun goes away for the shot)
  if (cardQ.length && !locked() && now > (ST.cardT || 0)) { card0(...cardQ.shift()); ST.cardT = now + 1500; }
  ST.saveT += dt;
}

// the Unpaid's ramp over the collapse: JUMP IT when you line up on it, then how the landing went
function rampCalls() {
  const c = G.story.car && G.story.car(); if (!c) return;
  const R = RAMP, inLane = c.x > R.x0 - 1 && c.x < R.x1 + 1, north = Math.cos(c.h) < -0.6, J = (ST.jump ||= { t: 0 });
  if (inLane && north && c.z > R.z1 && c.z < R.z1 + 30 && performance.now() > J.t) { J.t = performance.now() + 15000; card('step', 'JUMP IT!', 'the unpaid built a ramp. it is mostly desks.', '', 1.6); sfx.rankUp && sfx.rankUp(); }
  if (!c.ground && c.z < R.z0 && c.z > R.exit[0] - 4 && inLane) J.air = true;
  if (J.air && c.ground) { J.air = false; const made = c.z < R.exit[0] + 1; card('step', made ? 'NAILED IT' : 'SHORT!', made ? 'the soup is fine. probably.' : 'drive up the planks at the far end', '', 1.6); (made ? sfx.cash : sfx.hurt) && (made ? sfx.cash() : sfx.hurt()); }
}
// the tracked steps for the HUD, with a waypoint where the script gave none but the world has an answer: "steal a car"
// points at the nearest parked car
function hudObjs(S) {
  const objs = S.quests.objectives();
  for (const o of objs) {
    if (o.marker) continue;
    const q = S.defs.quests[o.quest], st = q && q.steps.find((x) => x.id === o.step);
    if (st && (st.goals || [st.goal]).some((g) => g && g.type === 'enterCar') && G.story && G.story.carNear) { const c = G.story.carNear(); if (c) o.marker = c; }
  }
  return objs;
}
export function key(e) {
  if (!ST.ready) return false;
  if (ST.scene && ST.scene.sceneKey(e)) return true;
  if (talkKey(e)) return true;
  if (e.code === 'KeyJ' && !e.repeat && e.type === 'keydown') { toggleCodex(ST.S); return true; }
  if (e.code === 'KeyR' && e.type === 'keydown' && !e.repeat && !LAB && ST.on && e.shiftKey) { fakeGoal(); return true; } // shift+R: rehearsal skip (R alone reloads)
  if (codexOpen()) { if (K.matches('menu', e)) toggleCodex(ST.S, false); return true; }
  if (K.matches('use', e) && !e.repeat) {
    if (nearThing && nearThing.spot) { const sp = nearThing.spot; sfx.cash && sfx.cash();
      if (sp.kind === 'pickup') { bag.give(sp.item); toast(`picked up <b>${sp.name.toUpperCase()}</b>`); ST.S.emit({ type: 'pickup', item: sp.item, zone: sp.zone }); }
      else { if (sp.th) { ST.S.st.flags['used.' + sp.thing] = true; ST.S.run(sp.th.do || [], 'thing'); toast(`found <b>${sp.name}</b>`); } ST.S.emit({ type: 'interact', thing: sp.thing, zone: sp.zone }); }
      G.scene.remove(sp.mesh); for (const [k, v] of SPOTS) if (v === sp) SPOTS.delete(k); return true; }
    if (nearThing) { const t = nearThing; bag.give(t.t.item); sfx.cash && sfx.cash(); toast(`picked up <b>${t.t.name}</b>`); ST.S.emit({ type: 'pickup', item: t.t.item }); ST.S.emit({ type: 'interact', thing: t.id }); return true; }
    if (nearAct) { if (document.pointerLockElement) { /* keep the lock: answers are on the number keys */ } startTalk(ST.S, nearAct.id, 'start', () => save()); return true; }
  }
  return false;
}
