// a hit-stop that is counted in real time (story boss fights: trainfight.js). the game's frame dt is multiplied by
// scale() while one is on (story/main.js timeScale), so it must never be counted down with that same dt: a 0.09 s
// freeze counted in time slowed to 6% lasts a second and a half. pure (the clock is passed in), so node can test it
export function makeHitStop(now = () => performance.now(), cap = 0.25, slow = 0.06) {
  let until = 0;
  return {
    hit(s) { if (Number.isFinite(s) && s > 0) until = Math.max(until, now() + Math.min(s, cap) * 1000); }, // (cap: no single one is longer than this, in real seconds)
    on: () => now() < until,
    scale: () => (now() < until ? slow : 1),
    clear() { until = 0; },
  };
}
