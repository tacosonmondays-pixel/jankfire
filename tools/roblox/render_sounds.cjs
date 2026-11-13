// render the web game's synth sounds (public/js/audio.js) that the Roblox weapons use to .ogg files for upload:
// each one plays into a fresh OfflineAudioContext in headless Chromium, then ffmpeg encodes it.
// run: node tools/roblox/render_sounds.cjs   (writes roblox/assets/sounds/*.ogg + list.json + SOUNDS.md)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const ROOT = path.join(__dirname, '..', '..'), OUT = path.join(ROOT, 'roblox', 'assets', 'sounds');
// name, the call, what it's for, volume in Roblox
const LIST = [
  ['gun_redline_k0', "sfx.gun('redline', null, 0)", 'Redline shot at full HP', 0.6],
  ['gun_redline_k5', "sfx.gun('redline', null, 0.5)", 'Redline shot at half HP', 0.6],
  ['gun_redline_k10', "sfx.gun('redline', null, 1)", 'Redline shot near death (screaming)', 0.6],
  ['gun_marbles', "sfx.gun('marbles')", 'Marble Shotgun shot (boom + glassy clinks)', 0.8],
  ['swing', 'sfx.swing()', 'melee whoosh (katana swing / draw / parry)', 0.7],
  ['bonk', 'sfx.bonk()', 'melee hit', 0.8],
  ['hit', 'sfx.hit()', 'hit marker tick (you hit someone)', 0.5],
  ['headshot', 'sfx.headshot(false)', 'DINK: you landed a headshot', 0.8],
  ['headshot_ko', 'sfx.headshot(true)', 'DINK, killing headshot', 0.8],
  ['headshot_taken', 'sfx.headshotTaken(false)', 'TONK: you took a headshot', 0.8],
  ['headshot_taken_ko', 'sfx.headshotTaken(true)', 'TONK, it killed you', 0.8],
  ['hurt', 'sfx.hurt()', 'you got hurt', 0.6],
  ['kill', 'sfx.kill()', 'you got a kill (brass fanfare)', 0.6],
  ['death', 'sfx.death()', 'you died (sad horn)', 0.6],
  ['parry', 'sfx.parry(null, false)', 'katana parry (struck blade)', 0.8],
  ['parry_perfect', 'sfx.parry(null, true)', 'katana PERFECT parry', 0.8],
  ['tink', 'sfx.tink()', 'small parry tink (more parries in one window)', 0.7],
  ['ricochet', 'sfx.ricochet()', 'perfect parry sends the bullets home', 0.7],
  ['ting', 'sfx.ting()', 'katana draw shing', 0.6],
  ['clatter', 'sfx.clatter()', 'MARBLES! a pile of marbles going everywhere (you slipped)', 0.8],
  ['whoops', 'sfx.whoops()', 'WHOOPS slide whistle (you slipped)', 0.7],
  ['marble', 'sfx.marble()', 'one marble clack', 0.5],
  ['click', 'sfx.click()', 'weapon swap click / reload click', 0.5],
  ['empty', 'sfx.empty()', 'dry fire', 0.5],
  ['reload', 'sfx.reload()', 'generic reload', 0.5],
  ['glug', "sfx.reloadFx('glug')", 'Redline reload: jerry can glug', 0.6],
  ['rev_up', "sfx.reloadFx('revUp')", 'Redline reload: VRRRAAP', 0.6],
  ['boing', "sfx.reloadFx('boing')", 'Marble Shotgun reload: a marble bounces out', 0.6],
  ['thwack', 'sfx.thwack()', 'Marble Shotgun reload: lid thwack', 0.6],
  ['round_start', 'sfx.roundStart()', 'ROUND START', 0.6],
  ['round_end', 'sfx.roundEnd()', 'match over', 0.6],
];
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const src = fs.readFileSync(path.join(ROOT, 'public/js/audio.js'), 'utf8');
  const b = await chromium.launch({ args: ['--mute-audio', '--autoplay-policy=no-user-gesture-required'] });
  const page = await b.newPage();
  await page.goto('about:blank');
  const out = [];
  for (const [name, call, what, vol] of LIST) {
    const data = await page.evaluate(async ({ src, call }) => {
      const SR = 44100;
      window.AudioContext = function () { return new OfflineAudioContext(1, SR * 4, SR); };
      const url = URL.createObjectURL(new Blob([src], { type: 'text/javascript' }));
      const m = await import(url);
      m.initAudio(0.9);
      const sfx = m.sfx; // eslint-disable-line no-unused-vars
      eval(call);
      const buf = await m.audioOut().ac.startRendering();
      const d = buf.getChannelData(0);
      let end = d.length - 1;
      while (end > 0 && Math.abs(d[end]) < 2e-4) end--;
      return Array.from(d.subarray(0, Math.min(d.length, end + Math.floor(SR * 0.03))));
    }, { src, call });
    // 16-bit wav -> ogg
    const n = data.length, wav = Buffer.alloc(44 + n * 2);
    wav.write('RIFF', 0); wav.writeUInt32LE(36 + n * 2, 4); wav.write('WAVEfmt ', 8); wav.writeUInt32LE(16, 16);
    wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22); wav.writeUInt32LE(44100, 24); wav.writeUInt32LE(88200, 28);
    wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34); wav.write('data', 36); wav.writeUInt32LE(n * 2, 40);
    let peak = 0;
    for (let i = 0; i < n; i++) { const v = Math.max(-1, Math.min(1, data[i])); peak = Math.max(peak, Math.abs(v)); wav.writeInt16LE(Math.round(v * 32767), 44 + i * 2); }
    const tmp = path.join(OUT, name + '.wav');
    fs.writeFileSync(tmp, wav);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', tmp, '-c:a', 'libvorbis', '-q:a', '6', path.join(OUT, name + '.ogg')]);
    fs.unlinkSync(tmp);
    out.push({ name, call, what, vol, secs: +(n / 44100).toFixed(2), peak: +peak.toFixed(2) });
    console.log(name, (n / 44100).toFixed(2) + ' s', 'peak', peak.toFixed(2));
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'list.json'), JSON.stringify(out, null, 1) + '\n');
  let md = '# JANKFIRE sounds for Roblox (step 2)\n\nRendered from the web game\'s synth (`public/js/audio.js`) by `tools/roblox/render_sounds.cjs`. Roblox only plays\n';
  md += 'uploaded audio, so: upload each `.ogg` (Studio: **View > Asset Manager > Bulk Import**, or Creator Hub > Development Items >\n';
  md += 'Audio), then paste its id into the Sound with the same name in **ReplicatedStorage > JankfireSounds** (property\n';
  md += '`SoundId`, as `rbxassetid://123...`). Until a Sound has an id, that sound just stays silent.\n\n| file | what it is | length |\n| --- | --- | --- |\n';
  for (const s of out) md += `| \`${s.name}.ogg\` | ${s.what} | ${s.secs} s |\n`;
  fs.writeFileSync(path.join(OUT, 'SOUNDS.md'), md);
})();
