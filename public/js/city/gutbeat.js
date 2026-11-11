// THE GUT'S BEAT: one clock for everything in the Gut that beats, so it all lands together: the Big Heart's ripple
// (bigheart.js), the district's fog closing in (ingame.js), the ground fog breathing (gutfog.js) and the thud you
// hear (audio.js sfx.bigHeart). t counts beats, ph is where we are in this one (0..1).
// The heart's shader puts the lub at the pacemaker (the top of the heart) at ph 0.12 and the wave takes `span` of a
// beat to reach the apex (the model's own curve: docs/story/gut/GUT_HEART_MODEL.md). At ph `lub` the whole heart gives
// its one big beat, the fog snaps shut and the thud lands, and the ripple sets off from the top as that peaks; the dub
// follows `dub` of a beat later on all of them.
export const gutBeat = { rate: 0.72, span: 0.55, lub: 0.06, dub: 0.21, t: 0, ph: 0, k: 0, fix: null }; // fix: hold the clock at this beat (tests, screenshots)
// lub-dub, then rest: the same curve as the shader's ghBeat (t = 0..1 through one beat)
export const lubDub = (t) => Math.exp(-(((t - 0.12) / 0.045) ** 2)) + 0.6 * Math.exp(-(((t - 0.33) / 0.06) ** 2));
// once a frame. k: how hard the fog is squeezed right now (1 on the lub, 0.6 on the dub, 0 at rest)
export function tickBeat() {
  const b = gutBeat;
  b.t = b.fix != null ? b.fix : performance.now() / 1000 * b.rate;
  b.ph = b.t - Math.floor(b.t);
  const ph = (b.ph - b.lub + 1) % 1;
  b.k = Math.exp(-ph * 9) + (ph > b.dub ? 0.6 * Math.exp(-(ph - b.dub) * 11) : 0);
  return b;
}
