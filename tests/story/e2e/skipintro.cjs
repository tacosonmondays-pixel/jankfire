// e2e helper: since the story engine landed (WP8), a New Game opens with the intro cinematic (and may open a talk).
// those hold the keys while they play (by design), so tests that check other systems skip them first.
module.exports = async function skipIntro(pg, tries = 20) {
  for (let i = 0; i < tries; i++) {
    const locked = await pg.evaluate(async () => {
      const boot = await import('/js/story/boot.js').catch(() => null);
      if (!boot || !boot.locked()) return false;
      const sc = await import('/js/story/scene.js'), tk = await import('/js/story/talk.js');
      if (sc.playing()) sc.skipScene();
      if (tk.talking && tk.talking() && tk.endTalk) tk.endTalk();
      return true;
    });
    if (!locked) { await quiet(pg); return true; }
    await new Promise((r) => setTimeout(r, 700));
  }
  return false;
};
// the test lot also holds the whole cast in a grid (one of them stands on the clinic chair), and the story engine's F
// (talk to the nearest person) runs before the systems' F. tests of other systems hide them so F reaches the thing.
async function quiet(pg) {
  await pg.evaluate(async () => {
    if (!/storytest=1/.test(location.search)) return;
    const { actors } = await import('/js/story/actors.js');
    clearInterval(window.__quiet); window.__quiet = setInterval(() => { for (const a of actors.values()) a.hidden = true; }, 100);
  });
}
module.exports.quiet = quiet;
// quest markers and memories sit on the test lot too, and they also take F first. use them up (F until the story
// engine's own prompt is gone, skipping whatever that starts) so the next F reaches the system under test
module.exports.clearF = async function clearF(pg, tries = 6) {
  for (let i = 0; i < tries; i++) {
    await new Promise((r) => setTimeout(r, 400));
    const busy = await pg.evaluate(() => { const p = document.getElementById('stPrompt'); return !!(p && !p.classList.contains('hidden') && p.textContent); });
    if (!busy) return true;
    await pg.keyboard.down('KeyF'); await new Promise((r) => setTimeout(r, 80)); await pg.keyboard.up('KeyF');
    await new Promise((r) => setTimeout(r, 500)); await module.exports(pg, 6);
  }
  return false;
};
