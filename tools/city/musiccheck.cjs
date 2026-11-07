// music handover between the menu, the story's district beds and PvP: node tools/city/musiccheck.cjs <port>
// menu -> the menu song plays; story (the streamed slice) -> the playlist fades out and a district bed plays;
// quit to the menu -> the beds stop and the menu song is back; a PvP bots match -> match music, no beds. Exit 1 on a fail.
const { chromium } = require('playwright');
const [port = 3107] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio', '--autoplay-policy=no-user-gesture-required'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 540 } });
  const errs = [], oggs = [];
  pg.on('pageerror', (e) => errs.push(e.message));
  pg.on('response', (r) => { if (/\/music\//.test(r.url())) oggs.push(r.url().split('/music/')[1]); });
  await pg.addInitScript(() => { localStorage.setItem('jfStory', '1'); localStorage.setItem('jankfire', JSON.stringify({ name: 'musiccheck', jank: 1, loadout: { primary: 'ar', secondary: 'revolver', melee: 'knife' } })); });
  await pg.goto(`http://localhost:${port}/`);
  await pg.waitForSelector('#storyBtn', { timeout: 60000 });
  await pg.mouse.click(5, 5); // a gesture: the audio unlocks
  const state = () => pg.evaluate(async () => {
    const m = await import('/js/music.js'), { G } = await import('/js/ctx.js'), beds = await import('/js/city/beds.js');
    const s = m.musicState();
    return { where: s.where, track: s.track, gain: +s.gain.toFixed(3), level: +s.level.toFixed(3), ctx: s.ctx, cityBeds: !!G.cityBeds, beds: beds.bedsState ? beds.bedsState() : null, map: (await import('/shared/map.js')).MAP.id };
  });
  const res = {}, fails = [];
  const want = (k, ok, why) => { if (!ok) fails.push(k + ': ' + why); };
  await sleep(6000);
  res.menu = await state();
  want('menu', res.menu.where === 'menu' && res.menu.track && res.menu.gain > 0.02, 'no menu song playing');
  // into the story, on the streamed slice (what ingame.cjs does)
  await pg.click('#storyBtn');
  await pg.waitForSelector('#storyPick .st-btn.yellow', { timeout: 30000 });
  await pg.click('#storyPick .st-btn.yellow');
  await pg.waitForFunction(async () => { const { G } = await import('/js/ctx.js'); return G.joined && G.mode === 'story'; }, null, { timeout: 60000 });
  await sleep(1500);
  await pg.evaluate(async () => {
    const { MAPS } = await import('/shared/map.js'); const w = await import('/js/world.js'); const { ME } = await import('/js/player.js'); const sm = await import('/js/city/storymap.js');
    sm.registerStoryMaps(MAPS); w.loadMap('story_slice');
    ME.pos = sm.STORY_SLICE.spawn.slice(); ME.vel = [0, 0, 0];
    document.getElementById('menu').classList.add('hidden');
  });
  await pg.waitForFunction(async () => { const m = await import('/js/city/ingame.js'); const s = m.cityStream(); return s && s.ready(-189, 196); }, null, { timeout: 90000 });
  await sleep(9000);
  res.story = await state();
  want('story', res.story.cityBeds && res.story.level === 0 && res.story.gain < 0.03, 'the playlist is still up in the story (gain ' + res.story.gain + ')');
  want('story beds', res.story.beds && res.story.beds.some((x) => x.slug === 'story_bottom' && x.gain > 0.05), 'no district bed playing');
  // back to the menu
  await pg.evaluate(() => window.JANK.quitToMenu());
  await sleep(6000);
  res.quit = await state();
  want('quit', !res.quit.cityBeds && res.quit.beds && res.quit.beds.length === 0, 'the beds are still playing on the menu');
  want('quit menu', res.quit.where === 'menu' && res.quit.track && res.quit.gain > 0.02, 'the menu song is not back');
  // a PvP bots match
  for (let i = 0; i < 30; i++) { const j = await pg.evaluate(async () => { const { G } = await import('/js/ctx.js'); if (!G.joined) document.getElementById('setupGo').click(); return G.joined && G.mode !== 'story'; }); if (j) break; await sleep(2000); }
  await pg.evaluate(() => document.getElementById('menu').classList.add('hidden'));
  await sleep(9000);
  res.pvp = await state();
  want('pvp', !res.pvp.cityBeds && res.pvp.beds && res.pvp.beds.length === 0 && !/^story/.test(res.pvp.map), 'story beds or map leaked into PvP');
  want('pvp music', res.pvp.where === 'match' && res.pvp.track && res.pvp.level > 0, 'no match music');
  console.log(JSON.stringify({ ...res, fetched: oggs, pageErrors: errs.slice(0, 5) }, null, 1));
  console.log(fails.length ? 'FAIL\n  ' + fails.join('\n  ') : 'OK: menu -> story beds -> menu -> PvP, the music hands over every time');
  await b.close();
  process.exit(fails.length ? 1 : 0);
})();
