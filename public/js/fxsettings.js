// Settings > video > shaders: a fidelity level (auto follows the quality preset) or your own mix of bloom, soft skin and
// punchy colours. Potato and Crusty stay off on auto: the shaders are for machines with frames to spare.
import { setPost, setPostFail, setPostAO, setPostSSR, setPostSky } from './post.js';
import { setBounce } from './bounce.js';
import { setNeon } from './neon.js';
import { setReflect, setReflectSSR } from './reflect.js';
import { hud } from './hud.js';
import { skinU } from './softskin.js';

const BLOOM = ['off', 'low', 'med', 'high'];
export const FX_LEVELS = { off: [0, false, false, false, false, false, false], low: [1, true, false, false, false, false, false], med: [2, true, true, false, false, false, false], high: [3, true, true, false, false, false, false], rt: [2, true, true, true, true, true, true] }; // bloom, soft skin, punch, contact shadows, bounce light, reflections, sun shafts + haze (rt: the RAY-TRACED LOOK: everything that fakes what ray tracing gives)
const AUTO = ['off', 'off', 'low', 'rt']; // Potato, Crusty, Mid, Too HD (not high on auto: high bloom washes out bright skies and signs, it stays a choice)
export function fxResolve(S) {
  const lv = S.fx || 'auto';
  if (lv === 'custom') return [Math.max(0, BLOOM.indexOf(S.fxBloom)), !!S.fxSkin, !!S.fxPunch, !!S.fxAO, !!S.fxBounce, !!S.fxRefl, !!S.fxSky];
  return FX_LEVELS[lv === 'auto' ? AUTO[S.jank] || 'off' : lv] || FX_LEVELS.off;
}
setPostFail(() => hud.msg('SHADERS BROKE. SHADERS OFF.', 2.6, 'brag')); // once: post.js switches itself off for the session (and /gfx says why)
export function applyFx(S) {
  const [bloom, skin, punch, ao, bounce, refl, sky] = fxResolve(S);
  setPostSky(sky && S.jank >= 2); // (sun shafts + haze: Mid and Too HD)
  setReflect(refl && S.jank >= 2); // (mirrors: Mid and Too HD)
  const ssr = refl && S.jank >= 3; setPostSSR(ssr); setReflectSSR(ssr); // (floor mirrors from the screen: Too HD only)
  setBounce(bounce && S.jank >= 2); setNeon(bounce && S.jank >= 2); // (the neon's light rides with the bounce: both are light off things)
  // (light off the buildings: never on Potato or Crusty)
  setPost(bloom, punch || ao || (refl && S.jank >= 3) || (sky && S.jank >= 2)); // (contact shadows need the shader pass even with no bloom or punch)
  setPostAO(ao && S.jank >= 2); // (never on Potato or Crusty)
  skinU.value = skin ? 1 : 0;
}
// the four controls. picking a level shows what it turns on; touching one of the three makes it "custom"
export function fxUI($, S, save) {
  const sync = () => {
    const [bloom, skin, punch, ao, bounce, refl, sky] = fxResolve(S);
    $('fxLevel').value = FX_LEVELS[S.fx] || S.fx === 'custom' ? S.fx : 'auto';
    $('fxBloom').value = BLOOM[bloom]; $('fxSkin').checked = skin; $('fxPunch').checked = punch; $('fxAO').checked = ao; $('fxBounce').checked = bounce; $('fxRefl').checked = refl; $('fxSky').checked = sky;
    applyFx(S);
  };
  $('fxLevel').addEventListener('change', () => {
    if ($('fxLevel').value === 'custom') { const [b, s, p, a, bo, rf, sk] = fxResolve(S); S.fxBloom = BLOOM[b]; S.fxSkin = s; S.fxPunch = p; S.fxAO = a; S.fxBounce = bo; S.fxRefl = rf; S.fxSky = sk; } // start from what you had
    S.fx = $('fxLevel').value; sync(); save();
  });
  const custom = () => { S.fx = 'custom'; S.fxBloom = $('fxBloom').value; S.fxSkin = $('fxSkin').checked; S.fxPunch = $('fxPunch').checked; S.fxAO = $('fxAO').checked; S.fxBounce = $('fxBounce').checked; S.fxRefl = $('fxRefl').checked; S.fxSky = $('fxSky').checked; sync(); save(); };
  for (const id of ['fxBloom', 'fxSkin', 'fxPunch', 'fxAO', 'fxBounce', 'fxRefl', 'fxSky']) $(id).addEventListener('change', custom);
  $('jank').addEventListener('change', sync); // auto follows the quality preset (main.js's own listener has set S.jank by now)
  sync();
  return sync;
}
