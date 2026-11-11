// Settings > video > shaders: a fidelity level (auto follows the quality preset) or your own mix of bloom, soft skin and
// punchy colours. Potato and Crusty stay off on auto: the shaders are for machines with frames to spare.
import { setPost, setPostFail } from './post.js';
import { hud } from './hud.js';
import { skinU } from './softskin.js';

const BLOOM = ['off', 'low', 'med', 'high'];
export const FX_LEVELS = { off: [0, false, false], low: [1, true, false], med: [2, true, true], high: [3, true, true] }; // bloom, soft skin, punch
const AUTO = ['off', 'off', 'low', 'med']; // Potato, Crusty, Mid, Too HD (not high on auto: high bloom washes out bright skies and signs, it stays a choice)
export function fxResolve(S) {
  const lv = S.fx || 'auto';
  if (lv === 'custom') return [Math.max(0, BLOOM.indexOf(S.fxBloom)), !!S.fxSkin, !!S.fxPunch];
  return FX_LEVELS[lv === 'auto' ? AUTO[S.jank] || 'off' : lv] || FX_LEVELS.off;
}
setPostFail(() => hud.msg('SHADERS BROKE. SHADERS OFF.', 2.6, 'brag')); // once: post.js switches itself off for the session (and /gfx says why)
export function applyFx(S) {
  const [bloom, skin, punch] = fxResolve(S);
  setPost(bloom, punch);
  skinU.value = skin ? 1 : 0;
}
// the four controls. picking a level shows what it turns on; touching one of the three makes it "custom"
export function fxUI($, S, save) {
  const sync = () => {
    const [bloom, skin, punch] = fxResolve(S);
    $('fxLevel').value = FX_LEVELS[S.fx] || S.fx === 'custom' ? S.fx : 'auto';
    $('fxBloom').value = BLOOM[bloom]; $('fxSkin').checked = skin; $('fxPunch').checked = punch;
    applyFx(S);
  };
  $('fxLevel').addEventListener('change', () => {
    if ($('fxLevel').value === 'custom') { const [b, s, p] = fxResolve(S); S.fxBloom = BLOOM[b]; S.fxSkin = s; S.fxPunch = p; } // start from what you had
    S.fx = $('fxLevel').value; sync(); save();
  });
  const custom = () => { S.fx = 'custom'; S.fxBloom = $('fxBloom').value; S.fxSkin = $('fxSkin').checked; S.fxPunch = $('fxPunch').checked; sync(); save(); };
  for (const id of ['fxBloom', 'fxSkin', 'fxPunch']) $(id).addEventListener('change', custom);
  $('jank').addEventListener('change', sync); // auto follows the quality preset (main.js's own listener has set S.jank by now)
  sync();
  return sync;
}
