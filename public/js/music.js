// Music. Unlike the sfx these are real files: mp3s in public/music/, fetched + decoded with web audio only when
// they're first needed, played through the sfx master gain so the main volume slider scales them too.
// web audio instead of an <audio> tag: gapless loops, sample-accurate fades, and no need for http Range requests.
import { G } from './ctx.js';
import { RP } from './replay.js';
import { initAudio, audioOut } from './audio.js';

// THE TRACK LIST. to add a song: drop the file in public/music/ and add a line here. menus shuffle them; each match
// picks one at random and keeps it. lufs = the file's loudness (ffmpeg ebur128), so every song plays equally loud.
// loop: the file is cut to loop seamlessly (tools/music renders them that way), so it repeats with no gap.
// the generated ones are made by tools/music (re-render with `python tools/music/render.py`).
export const TRACKS = [
  { file: 'untitled.mp3', title: 'Untitled', artist: 'JANKFIRE', lufs: -14.3 },
  { file: 'jank_cola_rave.ogg', title: 'Jank Cola Rave', artist: 'DJ Wrong Knee', lufs: -8.1, loop: true },
  { file: 'spoon_fight_tekno.ogg', title: 'Spoon Fight Tekno', artist: 'Soundsystem Spoon', lufs: -8.1, loop: true },
  { file: 'rubber_duck_hardcore.ogg', title: 'Rubber Duck Hardcore', artist: 'MC Squeaky', lufs: -8.1, loop: true },
  { file: 'hung_jury_hardcore.ogg', title: 'Hung Jury Hardcore', artist: 'The Honourable DJ Gavel', lufs: -8.1, loop: true },
  { file: 'banana_peel_acid.ogg', title: 'Banana Peel Acid', artist: 'Slip Daddy', lufs: -8.1, loop: true },
  { file: 'wrecking_ball_warmup.ogg', title: 'Wrecking Ball Warm-Up', artist: 'Coach Ball', lufs: -8.1, loop: true },
];
const REF_LUFS = -14; // everything is levelled to this (the music volume default was set by ear on Untitled)

const DUCK = 0.3;      // music drops to this while a killcam plays
const FADE = 0.45;     // fade in/out time constant (s): ~1.5s to get there
const TAIL = 0.45;     // the next song starts this long before the current one ends, over its decay
const RESUME_MS = 30000; // music back within 30s picks up where it stopped, later starts the next song

let armed = false, bus = null, ac = null, cur = null, nxt = null, loading = false;
let goal = -1, zeroAt = 0, resume = null, lastI = -1, order = [], toastAt = {};
let matchI = -1, swap = false, forced = -1, gen = 0, pickedAt = -1e9, joinedAt = -1e9; // this match's song, a new match asked for a new song, the song to start next
const cache = new Map(), dead = new Set();

// competitive = real people in the Online room, or Plant & Defuse anywhere: music stays off there unless you ask
export function competitive() { return G.mode === 'ffa' || G.game === 'bomb' || !!(G.round && G.round.game === 'bomb'); }
function where() {
  if (!G.joined && !document.getElementById('menu').classList.contains('hidden')) return 'menu'; // (menu hidden + not joined = connecting)
  if (G.joined && G.roundOver) return 'menu'; // scoreboard, play of the round, the map vote: menu music, menu volume
  return 'match';
}
function matchOn() { return competitive() ? !!G.settings.musicComp : G.settings.musicMatch !== false; }
function num(v, d) { v = Number(v); return Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : d; }
function vol() { return num(G.settings.musicVol, 0.35); }
// how loud the music bus should be right now (0 = off)
function level() {
  if (where() === 'menu') return RP.mode === 'hl' ? vol() * DUCK : vol(); // the play of the round talks over it too
  if (!matchOn()) return 0;
  const v = num(G.settings.musicMatchVol, 0.15);
  return RP.mode === 'killcam' ? v * DUCK : v; // your killcam (epic ones too) talks over it
}
function trim(i) { const l = Number(TRACKS[i].lufs); return Number.isFinite(l) ? Math.min(2, 10 ** ((REF_LUFS - l) / 20)) : 1; }

// next song: shuffled, never the same one twice in a row (unless it's the only one)
function pick(not = -1) {
  if (not >= 0) { const i = pick(); if (i === not && TRACKS.length - dead.size > 1) return pick(); return i; }
  const ok = TRACKS.map((_, i) => i).filter((i) => !dead.has(i));
  if (!ok.length) return -1;
  if (!order.length) { order = ok.sort(() => Math.random() - 0.5); if (order.length > 1 && order[0] === lastI) order.push(order.shift()); }
  const i = order.shift();
  return dead.has(i) ? pick() : (lastI = i);
}

function load(i) {
  if (cache.has(i)) return Promise.resolve(cache.get(i));
  const tr = TRACKS[i];
  return fetch(new URL('../music/' + tr.file, import.meta.url))
    .then((r) => { if (!r.ok) throw new Error('http ' + r.status); return r.arrayBuffer(); })
    .then((b) => new Promise((ok, no) => { const p = ac.decodeAudioData(b, ok, no); if (p && p.catch) p.catch(no); }))
    .then((buf) => {
      cache.set(i, buf);
      for (const k of cache.keys()) if (cache.size > 2 && k !== i && (!cur || k !== cur.i)) cache.delete(k); // ~30MB per decoded song
      return buf;
    })
    .catch((e) => { dead.add(i); console.warn(`music: couldn't load ${tr.file} (${(e && e.message) || e}), skipping it`); return null; });
}

function voice(i, buf, at, off) {
  const src = ac.createBufferSource(), g = ac.createGain();
  src.buffer = buf; src.connect(g); g.connect(bus); g.gain.value = trim(i);
  src.onended = () => { try { g.disconnect(); } catch { /* gone */ } };
  src.start(at, off);
  return { i, src, g, t0: at - off, end: at - off + buf.duration };
}

// a small "now playing" sticker, not spammed when the same song comes back (a new match always shows it)
let npEl = null, npT = 0;
function nowPlaying(i, force) {
  if (level() <= 0) return;
  const now = performance.now();
  if (!force && now - (toastAt[i] || -1e9) < 60000) return;
  toastAt[i] = now;
  const tr = TRACKS[i];
  if (!npEl) { npEl = document.createElement('div'); npEl.id = 'nowPlaying'; document.body.append(npEl); }
  npEl.innerHTML = '<span class="np-k">♪ now blasting</span> <b></b> <i></i>';
  npEl.querySelector('b').textContent = tr.title || tr.file;
  npEl.querySelector('i').textContent = tr.artist ? '· ' + tr.artist : '';
  npEl.classList.toggle('match', where() === 'match');
  npEl.classList.add('on');
  clearTimeout(npT); npT = setTimeout(() => npEl.classList.remove('on'), 5200);
}

function start() {
  let i, off = 0;
  if (forced >= 0 && !dead.has(forced)) { i = forced; forced = -1; } else if (resume && performance.now() - resume.at < RESUME_MS && !dead.has(resume.i)) { i = resume.i; off = resume.off; } else i = pick();
  resume = null;
  if (where() === 'match') matchI = i;
  if (i < 0) return;
  loading = true;
  const g = gen;
  load(i).then((buf) => {
    loading = false;
    if (g !== gen) { if (!cur && goal > 0) start(); return; } // a new match came in while this loaded
    if (!buf) { start(); return; } // that one's broken, try the next (dead ones are skipped, so this ends)
    if (cur || goal <= 0) { if (goal <= 0) resume = { i, off, at: performance.now() }; return; }
    cur = voice(i, buf, ac.currentTime + 0.05, off % buf.duration);
    if (off === 0) nowPlaying(i, where() === 'match');
  });
}
function stop() {
  const t = ac.currentTime;
  if (cur) resume = { i: cur.i, off: Math.max(0, t - cur.t0), at: performance.now() };
  for (const v of [cur, nxt]) if (v) { try { v.src.stop(); } catch { /* not started */ } }
  cur = nxt = null;
}
// queue the next song so it starts right as this one decays. in a match the match's song loops (seamlessly, if it
// was made to); in the menus they shuffle
function chain() {
  const t = ac.currentTime;
  if (nxt && t >= nxt.t0) { const same = cur && nxt.i === cur.i; cur = nxt; nxt = null; if (!same) nowPlaying(cur.i); }
  if (!cur || nxt || loading || cur.end - t > 6) return;
  const i = where() === 'match' && matchI === cur.i ? cur.i : pick();
  if (i < 0) return;
  loading = true;
  const g = gen;
  load(i).then((buf) => {
    loading = false;
    if (g !== gen || !buf || !cur || nxt) return;
    const seam = i === cur.i && TRACKS[i].loop ? 0 : TAIL; // a loop-cut file joins its own start exactly
    nxt = voice(i, buf, Math.max(ac.currentTime + 0.05, cur.end - seam), 0);
  });
}
// a new match: fade out whatever's playing, the match gets a fresh random song
function newSong() {
  const why = swap; swap = false;
  // joining a room is followed by its match start: that's one match, so one new song, not two back to back
  if (why === 'start' && performance.now() - joinedAt < 30000 && pickedAt >= joinedAt) return;
  pickedAt = performance.now(); gen++;
  const old = cur ? cur.i : lastI;
  forced = pick(old); resume = null; matchI = forced;
  if (!cur) return;
  const t = ac.currentTime;
  for (const v of [cur, nxt]) if (v) {
    v.g.gain.cancelScheduledValues(t); v.g.gain.setValueAtTime(v.g.gain.value, t); v.g.gain.setTargetAtTime(0, t, 0.35);
    try { v.src.stop(t + 2.5); } catch { /* already stopped */ }
  }
  cur = nxt = null;
}

function tick() {
  if (!armed) return;
  const out = audioOut();
  if (!out) return; // no web audio at all: no music, no fuss
  if (!bus) { ac = out.ac; bus = ac.createGain(); bus.gain.value = 0; bus.connect(out.master); }
  const want = level(), t = ac.currentTime;
  if (want !== goal) {
    const p = bus.gain;
    p.cancelScheduledValues(t); p.setValueAtTime(p.value, t);
    p.setTargetAtTime(want, t, goal > 0 && want > 0 ? FADE / 2 : FADE); // volume moves and ducks are quicker than fades in/out
    if (want === 0) zeroAt = t;
    goal = want;
  }
  if (ac.state !== 'running') return;
  if (swap && where() === 'match') newSong();
  if (goal > 0) { if (!cur && !loading) start(); else chain(); } else if (cur && t - zeroAt > FADE * 8) stop(); // fully faded (well under -60dB): let go
}

// browsers block audio until you click or press a key, so the first one starts the music
function gesture() {
  initAudio(G.settings.vol);
  const out = audioOut();
  if (out && out.ac.state === 'suspended') out.ac.resume().catch(() => {});
  armed = true;
  tick();
  if (out && out.ac.state === 'running') for (const e of ['pointerdown', 'keydown']) removeEventListener(e, gesture, true);
}
for (const e of ['pointerdown', 'keydown']) addEventListener(e, gesture, true);
setInterval(() => { try { tick(); } catch (e) { console.warn('music:', e); armed = false; } }, 250);

// apply a settings change right away instead of on the next tick
export function musicUpdate() { try { tick(); } catch { /* next tick logs it */ } }
// joined a room / a new match started: next time we're in the match, it gets a new random song
export function musicNewMatch(start) { swap = start ? 'start' : 'join'; if (!start) joinedAt = performance.now(); musicUpdate(); }
// for tests and poking around in the console
export function musicState() {
  return { armed, goal, gain: bus ? bus.gain.value : 0, ctx: ac ? ac.state : null, t: ac ? ac.currentTime : 0, track: cur ? TRACKS[cur.i].title : null, where: where(), comp: competitive(), level: level(), matchTrack: matchI >= 0 ? TRACKS[matchI].title : null, pos: cur && ac ? ac.currentTime - cur.t0 : 0, next: nxt ? TRACKS[nxt.i].title : null, cached: cache.size, dead: [...dead].map((i) => TRACKS[i].file) };
}
