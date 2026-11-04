// Music. Unlike the sfx these are real files: mp3s in public/music/, fetched + decoded with web audio only when
// they're first needed, played through the sfx master gain so the main volume slider scales them too.
// web audio instead of an <audio> tag: gapless loops, sample-accurate fades, and no need for http Range requests.
import { G } from './ctx.js';
import { RP } from './replay.js';
import { initAudio, audioOut } from './audio.js';

// THE TRACK LIST. to add a song: drop the mp3 in public/music/ and add a line here. more than one = shuffle.
export const TRACKS = [
  { file: 'untitled.mp3', title: 'Untitled', artist: 'JANKFIRE' },
];

const MATCH = 0.4;     // in a match (if allowed): sits under the gunfire
const DUCK = 0.3;      // and drops further while your killcam plays
const FADE = 0.45;     // fade in/out time constant (s): ~1.5s to get there
const TAIL = 0.45;     // the next song starts this long before the current one ends, over its decay
const RESUME_MS = 30000; // music back within 30s picks up where it stopped, later starts the next song

let armed = false, bus = null, ac = null, cur = null, nxt = null, loading = false;
let goal = -1, zeroAt = 0, resume = null, lastI = -1, order = [], toastAt = {};
const cache = new Map(), dead = new Set();

// how loud music should be right now, before the music volume: 1 = menus, 0 = off
function level() {
  if (!G.joined && !document.getElementById('menu').classList.contains('hidden')) return 1; // (menu hidden + not joined = connecting)
  if (G.joined && G.roundOver) return 1; // scoreboard, play of the round, the map vote
  if (!G.settings.musicMatch) return 0;
  return RP.mode === 'killcam' ? MATCH * DUCK : MATCH;
}
function vol() { const v = Number(G.settings.musicVol); return Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0.35; }

// next song: shuffled, never the same one twice in a row (unless it's the only one)
function pick() {
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
  src.buffer = buf; src.connect(g); g.connect(bus);
  src.onended = () => { try { g.disconnect(); } catch { /* gone */ } };
  src.start(at, off);
  return { i, src, g, t0: at - off, end: at - off + buf.duration };
}

// a small "now playing" note in the corner, menus only, not spammed when the same song comes back
let npEl = null, npT = 0;
function nowPlaying(i) {
  if (level() !== 1) return;
  const now = performance.now();
  if (now - (toastAt[i] || -1e9) < 60000) return;
  toastAt[i] = now;
  const tr = TRACKS[i];
  if (!npEl) { npEl = document.createElement('div'); npEl.id = 'nowPlaying'; document.body.append(npEl); }
  npEl.innerHTML = '<span class="np-k">♪ now playing</span> <b></b> <i></i>';
  npEl.querySelector('b').textContent = tr.title || tr.file;
  npEl.querySelector('i').textContent = tr.artist ? '· ' + tr.artist : '';
  npEl.classList.add('on');
  clearTimeout(npT); npT = setTimeout(() => npEl.classList.remove('on'), 4200);
}

function start() {
  let i, off = 0;
  if (resume && performance.now() - resume.at < RESUME_MS && !dead.has(resume.i)) { i = resume.i; off = resume.off; } else i = pick();
  resume = null;
  if (i < 0) return;
  loading = true;
  load(i).then((buf) => {
    loading = false;
    if (!buf) { start(); return; } // that one's broken, try the next (dead ones are skipped, so this ends)
    if (cur || goal <= 0) { if (goal <= 0) resume = { i, off, at: performance.now() }; return; }
    cur = voice(i, buf, ac.currentTime + 0.05, off % buf.duration);
    if (off === 0) nowPlaying(i);
  });
}
function stop() {
  const t = ac.currentTime;
  if (cur) resume = { i: cur.i, off: Math.max(0, t - cur.t0), at: performance.now() };
  for (const v of [cur, nxt]) if (v) { try { v.src.stop(); } catch { /* not started */ } }
  cur = nxt = null;
}
// queue the next song (or the same one again) so it starts right as this one decays
function chain() {
  const t = ac.currentTime;
  if (nxt && t >= nxt.t0) { cur = nxt; nxt = null; nowPlaying(cur.i); }
  if (!cur || nxt || loading || cur.end - t > 6) return;
  const i = pick();
  if (i < 0) return;
  loading = true;
  load(i).then((buf) => {
    loading = false;
    if (!buf || !cur || nxt) return;
    nxt = voice(i, buf, Math.max(ac.currentTime + 0.05, cur.end - TAIL), 0);
  });
}

function tick() {
  if (!armed) return;
  const out = audioOut();
  if (!out) return; // no web audio at all: no music, no fuss
  if (!bus) { ac = out.ac; bus = ac.createGain(); bus.gain.value = 0; bus.connect(out.master); }
  const want = vol() * level(), t = ac.currentTime;
  if (want !== goal) {
    const p = bus.gain;
    p.cancelScheduledValues(t); p.setValueAtTime(p.value, t);
    p.setTargetAtTime(want, t, goal > 0 && want > 0 ? FADE / 2 : FADE); // volume moves and ducks are quicker than fades in/out
    if (want === 0) zeroAt = t;
    goal = want;
  }
  if (ac.state !== 'running') return;
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
// for tests and poking around in the console
export function musicState() {
  return { armed, goal, gain: bus ? bus.gain.value : 0, ctx: ac ? ac.state : null, t: ac ? ac.currentTime : 0, track: cur ? TRACKS[cur.i].title : null, pos: cur && ac ? ac.currentTime - cur.t0 : 0, next: nxt ? TRACKS[nxt.i].title : null, cached: cache.size, dead: [...dead].map((i) => TRACKS[i].file) };
}
