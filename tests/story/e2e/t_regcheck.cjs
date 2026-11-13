// playwright e2e: a regression pass over every Act I chapter start in the slice city (a fresh run, each mission
// started at its first step, you stood a few metres from its first marker). at each one: a screenshot for the contact
// sheet, and the checks that keep breaking when lots merges at once:
//   the story bar shows and multiplayer's hotbar / killstreak tray don't (walking) · no two HUD panels overlap ·
//   Mina isn't standing about before m04 · no page errors · no "leave site?" dialog in a test run · the quest HUD is
//   showing this mission
// run: SP=<dir with pwlock.cjs> PORT=<port> OUT=<dir> [JANK=3] node tests/story/e2e/t_regcheck.cjs   (needs a running server)
const { boot, jump, settle, step, sleep } = require('./enc_util.cjs');
const skipIntro = require('./skipintro.cjs');
const fs = require('fs');
const OUT = process.env.OUT || (process.env.SP + '/shots');
const MISSIONS = ['m01_return_to_sender', 'm02_sauce_run', 'm03_somethings_digesting', 'm04_clocking_in', 'm05_second_stomach', 'm06_tickets_please'];
let fails = 0;
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fails++; };
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const W = Number(process.env.W || 1280), H = Number(process.env.H || 720);
  const { b, pg, ev, errs } = await boot({ hd: process.env.JANK !== '0', size: [W, H] });
  const dialogs = []; pg.on('dialog', async (d) => { dialogs.push(d.type() + ': ' + d.message()); try { await d.dismiss(); } catch { /* gone */ } });
  for (const [n, q] of MISSIONS.entries()) {
    const e0 = errs.length;
    ok(await jump(ev, q), `${q}: started`);
    await sleep(800);
    // where it starts: its first objective's marker (or the first goal's), else stay put
    const at = await ev((q) => {
      const ST = window.JF_STORY, o = ST.S.quests.objectives().find((x) => x.quest === q);
      if (!o) return null;
      const ids = [o.marker, ...(o.goals || []).map((g) => g.marker || g.zone || g.who || g.target)].filter(Boolean);
      for (const id of ids) { const p = ST.where(id); if (p) return { id, p: p.slice(), step: o.step, text: o.text || '' }; }
      return { id: null, p: null, step: o.step, text: o.text || '' };
    }, q);
    if (at && at.p) await settle(ev, [at.p[0] + 3, at.p[1] + 1.5, at.p[2] + 3], 5000);
    await skipIntro(pg, 6); await sleep(1500);
    await ev(async (p) => { const { ME } = await import('/js/player.js'); if (p) ME.yaw = Math.atan2(-(p[0] - ME.pos[0]), -(p[2] - ME.pos[2])); ME.pitch = -0.05; }, at && at.p);
    await sleep(1500);
    await pg.screenshot({ path: `${OUT}/chap_${n + 1}_${q}.png`, timeout: 180000 }); // (Too HD in software graphics: a frame can take a while)
    const c = await ev(async (q) => {
      const vis = (el) => { if (!el) return false; const s = getComputedStyle(el), r = el.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > 0.05 && r.width > 2 && r.height > 2; };
      const $ = (s) => document.querySelector(s);
      const { actors } = await import('/js/story/actors.js'); const { G } = await import('/js/ctx.js');
      const ids = ['#stQuest', '#storyBar', '#ammo', '#hpbox', '#weaponName', '#encHud', '#streak', '#feed', '#scores', '.st-coupons'];
      const boxes = ids.map((id) => [id.slice(1), document.querySelector(id)]).filter(([, el]) => vis(el)).map(([id, el]) => [id, el.getBoundingClientRect()]);
      const over = [];
      for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
        const [a, A] = boxes[i], [bb, B] = boxes[j];
        const w = Math.min(A.right, B.right) - Math.max(A.left, B.left), h = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
        if (w > 2 && h > 2) over.push(`${a}x${bb} (${Math.round(w)}x${Math.round(h)})`);
      }
      const qh = $('#stQuest');
      return { mode: G.mode, bar: vis($('#storyBar')), hotbar: vis($('#hotbar')), tray: vis($('#streakTray')), over, mina: actors.has('mina'), quest: qh ? qh.innerText.replace(/\s+/g, ' ').slice(0, 90) : '', shown: boxes.map(([id]) => id) };
    }, q);
    console.log(`  ${q} step ${at && at.step} at ${at && at.id} · hud: ${c.shown.join(',')} · quest: ${c.quest}`);
    ok(c.mode === 'story', `${q}: still in story mode`);
    ok(c.bar && !c.hotbar && !c.tray, `${q}: story bar shown, multiplayer hotbar + tray hidden (${JSON.stringify({ bar: c.bar, hotbar: c.hotbar, tray: c.tray })})`);
    ok(!c.over.length, `${q}: no HUD overlaps ${c.over.join(' ')}`);
    ok(n >= 3 || !c.mina, `${q}: no Mina before m04 (${c.mina})`);
    ok(!!c.quest, `${q}: the quest HUD shows something`);
    ok(errs.length === e0, `${q}: no page errors (${errs.slice(e0, e0 + 3).join(' | ')})`);
  }
  ok(!dialogs.length, 'no leave-site dialogs in a test run: ' + dialogs.join(' | '));
  console.log(`regcheck: ${fails} failed · ERRORS ${errs.length} ${errs.slice(0, 6).join('\n')}`);
  await b.close();
  process.exitCode = fails ? 1 : 0;
})();
