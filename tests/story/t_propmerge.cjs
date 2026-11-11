// every prop model (story s_*.glb + props-lane p_*.glb) through city/props.js: none may log a mergeGeometries error
// (that drops the material's pieces: the hand truck lost its toe plate to mixed packed/float uvs) and every one ends
// up as a Blender model, not the code boxes. needs a running server. usage: node tests/story/t_propmerge.cjs
require(__dirname + '/../rig/pwlock.cjs');
const { chromium } = require('playwright');
const PORT = process.env.PORT || 3000;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage();
  await pg.addInitScript(() => { window.__merr = []; const e0 = console.error.bind(console); console.error = (...a) => { const s = a.map(String).join(' '); if (/mergeGeometries/.test(s)) window.__merr.push(window.__cur + ': ' + s); e0(...a); }; });
  await pg.goto(`http://localhost:${PORT}/`); await pg.waitForTimeout(1500);
  const r = await pg.evaluate(async () => {
    const P = await import('/js/city/props.js');
    const story = await (await fetch('/models/story/index.json')).json(), list = await (await fetch('/models/list')).json();
    const ids = [...new Set([...story.filter((s) => s.startsWith('s_')).map((s) => s.slice(2)), ...list.map((m) => m.id).filter((s) => s.startsWith('p_')).map((s) => s.slice(2))])];
    const bad = [];
    for (const id of ids) { // one at a time, so an error names its model
      window.__cur = id; const e = P.propModel(id);
      for (let t = 0; t < 200 && e.state === 'loading'; t++) await new Promise((res) => setTimeout(res, 50));
      if (e.state !== 'glb') bad.push(id + ' is ' + e.state);
    }
    return { n: ids.length, merr: window.__merr, bad };
  });
  await b.close();
  console.log(`${r.n} prop models`);
  for (const l of [...r.merr, ...r.bad]) console.log('FAIL ' + l);
  if (r.merr.length || r.bad.length) process.exit(1);
  console.log('PASS: no merge errors, every model loaded');
})();
