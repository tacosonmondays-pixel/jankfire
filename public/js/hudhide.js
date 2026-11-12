// riding a killstreak that takes your guns away (mech drop + battle island hero mechs, wrecking ball, overdrive rig):
// the normal hotbar, item slot and ammo slide off screen. derived from state every frame (not enter/exit events), so
// death mid-streak, round end, leaving the match, spectating or a killcam can never leave it stuck hidden.
// the look is css: body.piloting in style.css
import { G } from './ctx.js';
import { mechOn, mechHeroOn } from './mech.js';
import { rigOn } from './rig.js';
import { ME, ballOn } from './player.js';

let was = false;
export const piloting = (now = performance.now()) => !!(G.joined && ME.alive && (mechOn() || mechHeroOn() || ballOn(now) || rigOn(now)));
export function hudHideTick(now = performance.now()) {
  const on = piloting(now);
  if (on === was) return;
  was = on;
  document.body.classList.toggle('piloting', on);
}
