// Marble Shotgun: the marbles left on the floor are a slip hazard. the server decides where the patches are and who
// slips (server.js marblePatch / tickMarbles), clients draw the marbles resting in them (public/js/marbles.js, mslip.js).
export const MSLIP = {
  life: 9, // seconds a patch stays on the floor
  land: 0.35, // s after the shot before it counts (the marbles are still flying)
  n: 90, rMin: 1.1, rMax: 2.5, // marbles + radius of a fresh patch (fewer when only some of the shot landed together)
  room: 10, per: 3, // live patches per room / per shooter (the oldest goes)
  cd: 0.8, // s between patches from one shooter (the gun fires every 0.9 s): fire spam can't carpet the map
  walk: 5.5, // m/s: faster than this slips. a crouch walk (4.5) is careful enough, walking (10) isn't
  crouch: 4.5, slide: 7, // crouch walk speed at speedMul 1, and where crouching turns into a slide (player.js slideMin)
  feet: 0.35, // how far above the patch's floor your feet can be and still be on it
  immune: 2000, // ms after a slip before marbles can get you again
  thin: 0.55, thinR: 0.85, minN: 10, minR: 0.8, // each slip scatters marbles: fewer, smaller, gone below minN
};

// is someone standing at pos (feet) on patch pt ({ c, r })
export function onPatch(pt, pos, pad = 0) {
  const dy = pos[1] - pt.c[1];
  return dy > -0.3 && dy < MSLIP.feet && Math.hypot(pos[0] - pt.c[0], pos[2] - pt.c[2]) < pt.r + pad;
}

// killcams: patches already on the floor when the clip starts (like trapPreroll for soap bubbles).
// ev = [{ s, m }] in time order; returns fresh 'mpatch' events at t0 with what was left of each by then
export function patchPreroll(ev, t0) {
  const live = new Map();
  for (const e of ev) {
    if (e.s >= t0) break;
    const m = e.m;
    if (m.t === 'mpatch') live.set(m.id, { s: e.s, m: { ...m } });
    else if (m.t === 'mslip' && live.has(m.id)) Object.assign(live.get(m.id).m, { n: m.n, r: m.r });
    else if (m.t === 'mpx') live.delete(m.id);
  }
  const out = [];
  for (const { s, m } of live.values()) {
    const left = m.left - (t0 - s);
    if (left > 300) out.push({ s: t0, m: { ...m, left } });
  }
  return out;
}
