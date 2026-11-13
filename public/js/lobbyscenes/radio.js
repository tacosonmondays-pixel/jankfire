// The warehouse radio (Zombies' lobby, warehouse.js): Deb's boombox plays a little station of its own. Every note is
// synthesized here (web audio, no files) and goes through an AM-radio voice: a band-pass, a touch of drive, crackle and
// pops. It's quiet and positional (louder as you walk up to the desk, panned by where it is on screen), scaled by the
// music volume setting (0 = silent), and the menu music ducks under it when you're close. Every so often the dial
// drifts: a sweep of static and it's on the other station.
//   WZMB 66.6 · SMOOTH APOCALYPSE   lounge chords, a walking bass, brushes, a lazy vibraphone line
//   BRAAAINS FM                     a spooky surf polka: oom-pah bass, a twangy lead, a theremin wail every few bars
const mtof = (m) => 440 * 2 ** ((m - 69) / 12);
const STATIONS = [
  { id: 'wzmb', name: 'WZMB 66.6 · SMOOTH APOCALYPSE', bpm: 84,
    chords: [[57, 60, 64, 67], [50, 53, 57, 60], [55, 59, 62, 65], [48, 52, 55, 59]], // Am7 Dm7 G7 Cmaj7
    bass: [[45, 48, 52, 55], [38, 41, 45, 48], [43, 47, 50, 53], [36, 40, 43, 47]], // a walk up each bar, on the beats
    lead: [76, null, 74, null, 72, null, null, 69, 72, null, 74, null, 76, null, null, null] }, // a vibe line (16ths, one bar, repeats a 4th up every other bar)
  { id: 'brains', name: 'BRAAAINS FM', bpm: 132,
    chords: [[64, 67, 71], [60, 64, 67], [62, 66, 69], [59, 63, 66]], // Em C D B
    bass: [[40, 47], [36, 43], [38, 45], [35, 42]], // oom (root), pah (fifth)
    lead: [76, 79, 83, 79, 76, 79, 83, 86, 84, 83, 79, 76, 74, 76, 79, null] },
];
export const RADIO = { base: 1.1, near: 2.5, far: 14, drift: [70, 110] }; // loudness at the desk (x music volume); full within near m, gone by far; s between drifts

export function makeRadio(synth, G) {
  const ac = synth.ac;
  if (!ac || !synth.out) return null;
  const R = { d: 99, st: Math.random() < 0.5 ? 0 : 1, step: 0, next: 0, driftT: RADIO.drift[0] + Math.random() * 20 };
  // the chain: voices -> station -> radio voice (hp, bp, drive) -> level -> pan -> the game's master
  const station = ac.createGain(); station.gain.value = 1;
  const hp = ac.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 240;
  const bp = ac.createBiquadFilter(); bp.type = 'peaking'; bp.frequency.value = 1500; bp.gain.value = 6; bp.Q.value = 0.8;
  const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 3400;
  const drive = ac.createWaveShaper(); { const n = 256, c = new Float32Array(n); for (let i = 0; i < n; i++) { const x = (i / (n - 1)) * 2 - 1; c[i] = Math.tanh(x * 2.2) / Math.tanh(2.2); } drive.curve = c; }
  const level = ac.createGain(); level.gain.value = 0;
  const pan = ac.createStereoPanner ? ac.createStereoPanner() : null;
  station.connect(hp); hp.connect(bp); bp.connect(lp); lp.connect(drive); drive.connect(level);
  if (pan) { level.connect(pan); pan.connect(synth.out); } else level.connect(synth.out);
  // noise: one buffer for brushes, snares, crackle and the static
  const nb = ac.createBuffer(1, ac.sampleRate, ac.sampleRate); { const d = nb.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
  const crk = ac.createBufferSource(); crk.buffer = nb; crk.loop = true;
  const crkF = ac.createBiquadFilter(); crkF.type = 'highpass'; crkF.frequency.value = 2400;
  const crkG = ac.createGain(); crkG.gain.value = 0.018;
  crk.connect(crkF); crkF.connect(crkG); crkG.connect(drive); crk.start();
  const voices = new Set();
  function note(type, f, t, dur, v, { att = 0.01, rel = 0.08, glide = 0, det = 0 } = {}) {
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = type; o.frequency.setValueAtTime(f, t); if (glide) o.frequency.exponentialRampToValueAtTime(f * glide, t + dur); if (det) o.detune.value = det;
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + att); g.gain.setValueAtTime(v, t + Math.max(att, dur - rel)); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(station); o.start(t); o.stop(t + dur + 0.02);
    voices.add(o); o.onended = () => { voices.delete(o); g.disconnect(); };
  }
  function hiss(t, dur, v, f0, type = 'highpass', q = 1) {
    const s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain();
    s.buffer = nb; s.playbackRate.value = 0.8 + Math.random() * 0.4; f.type = type; f.frequency.value = f0; f.Q.value = q;
    g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    s.connect(f); f.connect(g); g.connect(station); s.start(t, Math.random() * 0.5); s.stop(t + dur + 0.02);
    voices.add(s); s.onended = () => { voices.delete(s); g.disconnect(); };
  }
  // one 16th step of the current station at time t
  function play(step, t) {
    const S = STATIONS[R.st], bar = Math.floor(step / 16) % 4, s = step % 16, six = 60 / S.bpm / 4;
    if (S.id === 'wzmb') {
      if (s === 0) for (const m of S.chords[bar]) note('triangle', mtof(m + 12), t, six * 5, 0.022, { att: 0.006, rel: 0.35 }); // (lounge piano comping, up where a little speaker can play it)
      if (s === 6 || s === 11) for (const m of S.chords[bar]) note('triangle', mtof(m + 12), t, six * 1.6, 0.016, { att: 0.005, rel: 0.12 });
      if (s % 4 === 0) note('triangle', mtof(S.bass[bar][s / 4]), t, six * 3.4, 0.11, { att: 0.01, rel: 0.15 });
      if (s % 4 === 2) hiss(t, six * 1.4, 0.05, 5200, 'bandpass', 0.7); // (brushes on the offbeat)
      const l = S.lead[s]; if (l && (bar % 2 === 1 || s < 10)) note('sine', mtof(l + (bar % 2 ? 5 : 0)), t, six * 2.6, 0.05, { att: 0.004, rel: 0.4, det: 6 });
    } else {
      if (s === 0 || s === 8) note('square', mtof(S.bass[bar][0]), t, six * 1.8, 0.1, { rel: 0.05 });
      if (s === 4 || s === 12) { note('square', mtof(S.bass[bar][1]), t, six * 1.8, 0.085, { rel: 0.05 }); for (const m of S.chords[bar]) note('sawtooth', mtof(m), t, six * 1.4, 0.02, { rel: 0.05 }); hiss(t, six * 1.2, 0.09, 1800, 'bandpass', 0.9); }
      const l = S.lead[s]; if (l && s % 2 === 0) note('sawtooth', mtof(l - 12), t, six * 1.9, 0.034, { att: 0.003, rel: 0.12, det: (Math.random() - 0.5) * 20 }); // (the surf twang, a bit out of tune)
      if (s === 0 && step % 128 === 64) note('sine', mtof(76), t, six * 14, 0.05, { att: 0.3, rel: 1.2, glide: 0.5 }); // the theremin wails, every eight bars
    }
    if (Math.random() < 0.06) hiss(t + Math.random() * six, 0.012, 0.25, 3000); // pops
  }
  function drift() { // a sweep of static, a whistle, the other station
    const t = ac.currentTime + 0.02;
    hiss(t, 1.1, 0.35, 900, 'bandpass', 0.4); note('sine', 2200, t, 0.9, 0.025, { glide: 0.35, att: 0.05, rel: 0.3 });
    station.gain.setValueAtTime(station.gain.value, t); station.gain.linearRampToValueAtTime(0.15, t + 0.2); station.gain.linearRampToValueAtTime(1, t + 1.1);
    R.st = 1 - R.st; R.step = 0; R.next = t + 1.0;
  }
  return {
    // every frame: d = metres from the camera to the radio, x = where it is across the screen (-1 left .. 1 right).
    // returns how much the menu music should duck (1 = not at all)
    update(dt, d, x, playing = true) {
      const now = ac.currentTime, mv = Number(G.settings && G.settings.musicVol), vol = Number.isFinite(mv) ? Math.max(0, Math.min(1, mv)) : 0.35; // (the music volume setting, read the way music.js reads it)
      R.d = d;
      const near = playing ? Math.max(0, Math.min(1, (RADIO.far - d) / (RADIO.far - RADIO.near))) : 0;
      const want = RADIO.base * vol * near * near; // (it falls off fast: a radio across a warehouse is a murmur)
      level.gain.setTargetAtTime(want, now, 0.25);
      if (pan) pan.pan.setTargetAtTime(Math.max(-0.85, Math.min(0.85, x * 0.85)), now, 0.1);
      if (ac.state !== 'running' || want <= 0.0005) { R.next = 0; return 1; } // (silent: don't schedule notes nobody hears)
      if (!R.next || R.next > now + 3 || R.next < now - 2) R.next = now + 0.05; // (back after a long pause: start from now)
      while (R.next < now + 0.02) { R.step++; R.next += 60 / STATIONS[R.st].bpm / 4; } // (a stall: skip the notes we missed but keep the beat)
      const six = 60 / STATIONS[R.st].bpm / 4;
      const ahead = Math.min(1.5, Math.max(0.5, dt * 2)); // (a slow frame mustn't leave a gap in the tune)
      while (R.next < now + ahead) { play(R.step, R.next); R.step++; R.next += six; }
      if ((R.driftT -= dt) <= 0) { drift(); R.driftT = RADIO.drift[0] + Math.random() * (RADIO.drift[1] - RADIO.drift[0]); }
      return 1 - 0.75 * near * near; // (right at the desk: the menu music down to a quarter)
    },
    station: () => STATIONS[R.st].name,
    tap: () => pan || level, // (tests: the radio's own output, to meter)
    info: () => ({ station: STATIONS[R.st].id, d: +R.d.toFixed(2), level: +level.gain.value.toFixed(3), pan: pan ? +pan.pan.value.toFixed(2) : 0, voices: voices.size, step: R.step }),
    dispose() {
      level.gain.cancelScheduledValues(ac.currentTime); level.gain.setTargetAtTime(0, ac.currentTime, 0.05);
      setTimeout(() => { try { crk.stop(); } catch { /* already */ } for (const v of voices) { try { v.stop(); } catch { /* already */ } } for (const n of [station, hp, bp, lp, drive, level, pan, crkF, crkG]) if (n) n.disconnect(); }, 300);
    },
  };
}
