// District music in the streamed city: one looping bed per district (public/music/story/<slug>.ogg, made by
// tools/music: lo-fi accordion in the Bottom, a humming choir on a heartbeat in the Gut, kazoo road-trip rock on the
// Commute), crossfaded by where you stand (the same 40 m blend as the sky and fog). Only the story's streamed maps
// run this; while it does, G.cityBeds is set and music.js leaves the match playlist off (no two songs at once).
import { G } from '../ctx.js';
import { audioOut } from '../audio.js';

const BEDS = { bottom: { story_bottom: 1 }, border: { story_bottom: 0.45, story_gut: 0.55 }, gut: { story_gut: 1 }, commute: { story_commute: 1 } };
const LEVEL = 0.55; // under the gameplay sounds: beds, not bangers
const cache = new Map(); // slug -> AudioBuffer | 'loading' | null
let live = new Map(); // slug -> { src, gain }

function load(ac, slug) {
  if (cache.has(slug)) return cache.get(slug);
  cache.set(slug, 'loading');
  fetch('/music/story/' + slug + '.ogg').then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(r.status)))).then((b) => ac.decodeAudioData(b))
    .then((buf) => cache.set(slug, buf)).catch(() => cache.set(slug, null));
  return 'loading';
}

// weights: [[district, w], ...] (plan.js districtWeights). call every frame or so
export function updateBeds(weights, dt) {
  const out = audioOut();
  if (weights && weights.length) G.cityBeds = true;
  if (!out) return;
  const { ac, master } = out, want = {};
  const on = G.settings ? G.settings.musicMatch !== false : true;
  for (const [d, w] of weights || []) for (const [slug, k] of Object.entries(BEDS[d.id] || {})) want[slug] = (want[slug] || 0) + w * k * (on ? LEVEL : 0);
  for (const slug of new Set([...Object.keys(want), ...live.keys()])) {
    const g = want[slug] || 0;
    let l = live.get(slug);
    if (!l && g > 0.01) {
      const buf = load(ac, slug);
      if (!buf || buf === 'loading') continue;
      const src = ac.createBufferSource(), gain = ac.createGain();
      src.buffer = buf; src.loop = true; gain.gain.value = 0;
      src.connect(gain); gain.connect(master);
      src.start(0, (ac.currentTime % buf.duration)); // everyone's district bed is on the same clock, roughly
      live.set(slug, (l = { src, gain }));
    }
    if (!l) continue;
    l.gain.gain.setTargetAtTime(g, ac.currentTime, 0.8);
    if (g <= 0.001 && l.gain.gain.value < 0.003) { l.src.stop(); l.src.disconnect(); l.gain.disconnect(); live.delete(slug); }
  }
  if (!(weights && weights.length) && !live.size) G.cityBeds = false; // faded out (back on the menu): the playlist's turn
  void dt;
}
export function stopBeds() {
  G.cityBeds = false;
  for (const l of live.values()) { try { l.src.stop(); } catch { /* already */ } l.src.disconnect(); l.gain.disconnect(); }
  live = new Map();
}
// what's playing (tools/city/musiccheck.cjs): [{ slug, gain }]
export const bedsState = () => [...live.entries()].map(([slug, l]) => ({ slug, gain: +l.gain.gain.value.toFixed(3) }));
