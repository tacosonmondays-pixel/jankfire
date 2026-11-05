// browser test for the music system: menus -> a bots match -> killcam duck -> plant & defuse (competitive) -> new match.
// also decodes every track in Chromium and checks the decoded length is exactly the rendered length (gapless loops).
// usage: PORT=3011 node server.js & node tools/music/t_music.cjs 3011 [shots-dir]
const { chromium } = require('playwright');
const port = process.argv[2] || '3000', shots = process.argv[3] || null;
const fs = require('fs'), path = require('path');
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--autoplay-policy=no-user-gesture-required'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message)); pg.on('console', (m) => { if (m.type() === 'warning' && /music/.test(m.text())) errs.push(m.text()); });
  await pg.addInitScript(() => localStorage.setItem('jankfire', JSON.stringify({ name: 'dj', killcam: false })));
  await pg.goto(`http://localhost:${port}/`); await pg.waitForTimeout(800);
  const st = () => pg.evaluate(async () => (await import('/js/music.js')).musicState());
  const wait = async (fn, ms = 15000) => { const t = Date.now(); let s; while (Date.now() - t < ms) { s = await st(); if (fn(s)) return s; await pg.waitForTimeout(250); } return s; };

  // 1. every file decodes in chromium, at the exact rendered length
  const dec = await pg.evaluate(async () => {
    const { TRACKS } = await import('/js/music.js');
    const out = [];
    for (const t of TRACKS) {
      try {
        const buf = await (await fetch('/music/' + t.file)).arrayBuffer();
        const a = await new OfflineAudioContext(2, 44100, 44100).decodeAudioData(buf);
        const d = a.getChannelData(0);
        out.push({ file: t.file, loop: !!t.loop, len: a.length, dur: a.duration, first: d[0], last: d[d.length - 1] });
      } catch (e) { out.push({ file: t.file, err: String(e) }); }
    }
    return out;
  });
  for (const d of dec) {
    if (d.err) { ok(false, `${d.file} decodes (${d.err})`); continue; }
    const want = d.loop ? JSON.parse(fs.readFileSync(path.join(__dirname, '.cache', 'work', 'lengths.json'), 'utf8'))[d.file] : null;
    ok(!d.loop || d.len === want, `${d.file} decodes, ${d.dur.toFixed(2)} s${d.loop ? `, ${d.len} samples (rendered ${want})` : ''}`);
    if (d.loop) ok(Math.abs(d.first - d.last) < 0.2, `${d.file} loop seam: first ${d.first.toFixed(3)} / last ${d.last.toFixed(3)}`);
  }

  // 2. menus: first click starts music at the menu volume, "now playing" shows
  await pg.mouse.click(5, 5);
  let s = await wait((x) => x.track && x.gain > 0.3);
  ok(s.where === 'menu' && s.track && Math.abs(s.level - 0.35) < 1e-6, `menu music: ${s.track} (level ${s.level}, gain ${s.gain.toFixed(2)})`);
  ok(await pg.evaluate(() => { const e = document.getElementById('nowPlaying'); return !!e && e.classList.contains('on') && !e.classList.contains('match'); }), 'now playing shown in the menu');
  if (shots) await pg.screenshot({ path: path.join(shots, 'np_menu.png') });

  // 3. a bots match: in-match music on by default, a new song, quieter, sticker top-left
  const menuTrack = s.track;
  await pg.click('#scr-main [data-go="setup"]');
  await pg.locator('#setupBots').fill('2');
  await pg.click('#setupGo');
  s = await wait((x) => x.where === 'match' && x.track && x.track === x.matchTrack && x.gain > 0.1);
  ok(s.where === 'match' && !s.comp && Math.abs(s.level - 0.15) < 1e-6, `bots match: music on at ${s.level}`);
  ok(s.track === s.matchTrack && s.track !== menuTrack, `match song "${s.track}" is new (menu was "${menuTrack}")`);
  await pg.waitForTimeout(600);
  ok(await pg.evaluate(() => { const e = document.getElementById('nowPlaying'); return e.classList.contains('on') && e.classList.contains('match'); }), 'now playing sticker in the match');
  if (shots) await pg.screenshot({ path: path.join(shots, 'np_match.png') });

  // 4. killcam ducks it
  await pg.evaluate(async () => { (await import('/js/replay.js')).RP.mode = 'killcam'; (await import('/js/music.js')).musicUpdate(); });
  s = await st(); ok(Math.abs(s.level - 0.15 * 0.3) < 1e-6, `killcam ducks to ${s.level.toFixed(3)}`);
  await pg.evaluate(async () => { (await import('/js/replay.js')).RP.mode = null; (await import('/js/music.js')).musicUpdate(); });

  // 5. music off in matches -> silent; back on
  await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); G.settings.musicMatch = false; (await import('/js/music.js')).musicUpdate(); });
  s = await st(); ok(s.level === 0, 'match music toggle off -> level 0');
  await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); G.settings.musicMatch = true; (await import('/js/music.js')).musicUpdate(); });

  // 6. quit, plant & defuse = competitive: off by default, on with the toggle, and a different song than last match
  const lastMatch = s.matchTrack;
  await pg.evaluate(() => document.getElementById('quit').click());
  await pg.waitForTimeout(1500);
  s = await st(); ok(s.where === 'menu', 'back in the menu after quitting');
  await pg.click('#scr-main [data-go="setup"]');
  await pg.selectOption('#setupMap', 'bazaar'); await pg.selectOption('#setupGame', 'bomb'); // bomb needs a map with sites
  await pg.locator('#setupBots').fill('3');
  await pg.click('#setupGo');
  s = await wait((x) => x.where === 'match' && x.comp, 12000);
  ok(s.comp && s.level === 0, `plant & defuse is competitive: music off (level ${s.level})`);
  await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); G.settings.musicComp = true; (await import('/js/music.js')).musicUpdate(); });
  s = await wait((x) => x.track && x.gain > 0.1);
  ok(s.level > 0 && s.track === s.matchTrack, `...on with the competitive toggle: "${s.track}"`);
  ok(s.matchTrack !== lastMatch, `new match, new song ("${lastMatch}" -> "${s.matchTrack}")`);

  // 7. the settings UI exists and is wired
  const ui = await pg.evaluate(() => ['musicVol', 'musicMatch', 'musicComp', 'musicMatchVol'].map((id) => !!document.getElementById(id)));
  ok(ui.every(Boolean), 'settings: music volume, music in matches, competitive toggle, match volume');
  ok(errs.length === 0, 'no page errors / music warnings' + (errs.length ? ': ' + errs.join(' | ') : ''));
  await b.close();
  console.log(fails ? `${fails} FAILED` : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})();
