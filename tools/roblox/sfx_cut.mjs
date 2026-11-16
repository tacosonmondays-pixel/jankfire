// look at and cut recorded sounds (the Freesound downloads, as WAV from audio_to_wav.py)
//   node tools/roblox/sfx_cut.mjs info a.wav b.wav ...      -> length, peak, loudness (LUFS), onsets (s)
//   node tools/roblox/sfx_cut.mjs cut in.wav out.wav <start> <end> [fadeOutMs=30]
//       -> that slice, a 2 ms fade in, the fade out, rumble below 25 Hz off, peak at -1 dBFS
import path from 'node:path';
import { SR, readWav, writeWav, loudness, hp, norm, db } from './sfx_dsp.mjs';

const env5 = (d) => { const F = Math.round(SR * 0.005), e = []; for (let i = 0; i < d.length; i += F) { let p = 0; for (let j = i; j < Math.min(d.length, i + F); j++) p = Math.max(p, Math.abs(d[j])); e.push(20 * Math.log10(p + 1e-9)); } return e; };
function onsets(d) {
  const e = env5(d), top = Math.max(...e), out = [];
  let last = -1;
  for (let i = 1; i < e.length; i++) {
    let mn = 1e9; for (let j = Math.max(0, i - 12); j < i; j++) mn = Math.min(mn, e[j]);
    if (e[i] - mn > 12 && e[i] > top - 20 && (i - last) * 0.005 > 0.07) { out.push(`${(i * 0.005).toFixed(2)}(${e[i].toFixed(0)})`); last = i; }
  }
  return { top, list: out };
}
const [cmd, ...a] = process.argv.slice(2);
if (cmd === 'info') {
  for (const f of a) {
    const { sr, data } = readWav(f);
    if (sr !== SR) { console.log(f, 'sample rate', sr); continue; }
    const o = onsets(data);
    console.log(`${path.basename(f, '.wav')} ${(data.length / SR).toFixed(2)}s pk ${o.top.toFixed(0)} L ${loudness(data).toFixed(1)} onsets ${o.list.join(',') || '-'}`);
  }
} else if (cmd === 'cut') {
  const [inp, out, st, en, fo] = a;
  const { data } = readWav(inp);
  const s0 = Math.max(0, Math.round(Number(st) * SR)), s1 = Math.min(data.length, Math.round(Number(en) * SR));
  const b = data.slice(s0, s1);
  hp(b, 25, 0.7);
  const fi = Math.round(SR * 0.002), fon = Math.min(b.length, Math.round(SR * Number(fo || 30) / 1000));
  for (let i = 0; i < fi && i < b.length; i++) b[i] *= i / fi;
  for (let i = 0; i < fon; i++) b[b.length - 1 - i] *= i / fon;
  norm(b, db(-1));
  writeWav(out, b);
  console.log(`${path.basename(out)} ${(b.length / SR).toFixed(2)}s L ${loudness(b).toFixed(1)}`);
}
