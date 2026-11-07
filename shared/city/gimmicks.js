// The districts' traversal gimmicks, as pure logic over a chunk's triggers (shared: the client runs it for your own
// movement, the server can run the same thing to check it). Triggers come from the generators (chunk.js out.triggers):
//   zip      { a, b, sag }                 a washing line: grab it (use) and slide, downhill or the way you face
//   conveyor { box, dir, speed, beat? }    Peristalsis Avenue, the Down Escalator: the floor carries you
//   bounce   { box, v }                    lung trampolines: land on one and it throws you up
//   acid     { box, dps }                  the Big Stomach's lake: it digests you
//   hot      { box }                       fallout hot zones (the fallen 7)
//   paper    { box }                       the Commute's paper storms (weather)
//   pad      { box, v: [vx, vy, vz] }      jump pads (the PvP ones): step on and get thrown along v
//   slip     { box, what }                 banana peels / marbles in the markets: you go flying (the client's slip())
//   slide    { box, dir, speed }           slide chutes (THE BANISTER): the floor speeds you up along dir, more if you slide
// step() mutates the player state { pos, vel, ground, zip } and returns events for the client's juice.

export const GIM = { zipGrab: 2.6, zipMax: 24, zipAccel: 16, zipHang: 2.0, bounceCool: 0.35, padCool: 0.5, slipCool: 2.5, slideAcc: 18, slideAccSlide: 34 };

const inBox = (p, b, pad = 0) => p[0] > b[0] - pad && p[0] < b[3] + pad && p[1] > b[1] - pad && p[1] < b[4] + pad && p[2] > b[2] - pad && p[2] < b[5] + pad;

// the point on a sagging line at t (0..1), and its tangent
export function zipPoint(z, t) {
  const s = Math.sin(t * Math.PI) * z.sag;
  return [z.a[0] + (z.b[0] - z.a[0]) * t, z.a[1] + (z.b[1] - z.a[1]) * t - s, z.a[2] + (z.b[2] - z.a[2]) * t];
}
// nearest line within reach of the hands (eye height), and where along it
export function zipNear(trigs, eye) {
  let best = null, bd = GIM.zipGrab;
  for (const z of trigs) {
    if (z.kind !== 'zip') continue;
    const dx = z.b[0] - z.a[0], dz = z.b[2] - z.a[2], L2 = dx * dx + dz * dz || 1;
    const t = Math.max(0.02, Math.min(0.98, ((eye[0] - z.a[0]) * dx + (eye[2] - z.a[2]) * dz) / L2));
    const p = zipPoint(z, t), d = Math.hypot(p[0] - eye[0], (p[1] - eye[1]) * 0.7, p[2] - eye[2]);
    if (d < bd) { bd = d; best = { z, t }; }
  }
  return best;
}

// one step. me = { pos, vel, ground, zip: null | { z, t, v, dir } }, use = the grab key went down this frame,
// jump = the jump key went down. trigs = the triggers round you (stream.triggersNear). returns [{ kind, ... }]
export function stepGimmicks(me, trigs, dt, input = {}) {
  const ev = [];
  const feet = me.pos, eye = [feet[0], feet[1] + 1.6, feet[2]];
  // ziplines: grab, ride, let go
  if (me.zip) {
    const zp = me.zip, z = zp.z, L = Math.hypot(z.b[0] - z.a[0], z.b[1] - z.a[1], z.b[2] - z.a[2]) || 1;
    const slope = (z.b[1] - z.a[1]) / L * zp.dir; // going down the line speeds you up
    zp.v = Math.min(GIM.zipMax, zp.v + (GIM.zipAccel * 0.4 - slope * 9.8) * dt);
    zp.t += (zp.v * dt / L) * zp.dir;
    const p = zipPoint(z, Math.max(0, Math.min(1, zp.t))), t2 = Math.max(0, Math.min(1, zp.t + 0.01 * zp.dir)), q = zipPoint(z, t2);
    const tl = Math.hypot(q[0] - p[0], q[1] - p[1], q[2] - p[2]) || 1;
    me.pos[0] = p[0]; me.pos[1] = p[1] - GIM.zipHang; me.pos[2] = p[2];
    me.vel[0] = (q[0] - p[0]) / tl * zp.v; me.vel[1] = (q[1] - p[1]) / tl * zp.v; me.vel[2] = (q[2] - p[2]) / tl * zp.v;
    zp.sock = (zp.sock || 0) + dt;
    if (zp.sock > 0.35) { zp.sock = 0; ev.push({ kind: 'sock', p: [p[0], p[1] - 0.4, p[2]] }); } // you knock the washing off as you go
    if (zp.t <= 0 || zp.t >= 1 || input.jump || input.use) {
      me.zip = null; me.vel[1] = Math.max(me.vel[1], input.jump ? 7 : 2); // fling off the end with all that speed
      ev.push({ kind: 'zipOff', speed: zp.v });
    }
    return ev;
  }
  if (input.use) {
    const n = zipNear(trigs, eye);
    if (n) {
      const z = n.z, dx = z.b[0] - z.a[0], dz = z.b[2] - z.a[2], face = input.face || [0, 0, -1];
      const along = dx * face[0] + dz * face[2], down = z.b[1] < z.a[1] ? 1 : -1;
      const dir = Math.abs(along) > Math.hypot(dx, dz) * 0.25 ? Math.sign(along) : down; // the way you face, else downhill
      me.zip = { z, t: n.t, v: Math.max(6, Math.hypot(me.vel[0], me.vel[2])), dir };
      ev.push({ kind: 'zipOn', name: 'ZIPLINE' });
      return ev;
    }
  }
  for (const g of trigs) {
    if (!g.box) continue;
    if (g.kind === 'conveyor' && inBox(feet, g.box, 0.1) && me.ground) {
      // the floor moves: on the beat (peristalsis) it surges
      const k = g.beat ? 0.45 + 1.4 * (input.beat || 0) : 1;
      me.pos[0] += g.dir[0] * g.speed * k * dt; me.pos[2] += g.dir[2] * g.speed * k * dt;
      if (input.sliding && g.beat && (input.beat || 0) > 0.6) { me.vel[0] += g.dir[0] * 30 * dt; me.vel[2] += g.dir[2] * 30 * dt; ev.push({ kind: 'surf' }); } // slide in on the beat: huge speed
      ev.push({ kind: 'carry', name: g.name });
    } else if (g.kind === 'bounce' && inBox(feet, g.box) && me.vel[1] <= 2 && !(me.bounceT > 0)) {
      me.vel[1] = g.v + Math.max(0, -me.vel[1]) * 0.35; me.ground = false; me.bounceT = GIM.bounceCool; // fall from higher, go higher
      ev.push({ kind: 'bounce', name: g.name, v: me.vel[1] });
    } else if (g.kind === 'acid' && inBox(feet, g.box)) ev.push({ kind: 'acid', dmg: g.dps * dt });
    else if (g.kind === 'hot' && inBox(feet, g.box)) ev.push({ kind: 'hot' });
    else if (g.kind === 'paper' && inBox(feet, g.box)) ev.push({ kind: 'paper' });
    else if (g.kind === 'pad' && inBox(feet, g.box, 0.15) && !(me.padT > 0)) {
      me.vel[0] = g.v[0]; me.vel[1] = g.v[1]; me.vel[2] = g.v[2]; me.ground = false; me.padT = GIM.padCool;
      ev.push({ kind: 'pad', name: g.name, v: g.v[1] });
    } else if (g.kind === 'slip' && me.ground && inBox(feet, g.box, 0.1) && !(me.slipT > 0) && Math.hypot(me.vel[0], me.vel[2]) > 2.5) {
      me.slipT = GIM.slipCool; ev.push({ kind: 'slip', what: g.what || 'banana' }); // the client throws you (player.js slip())
    } else if (g.kind === 'slide' && me.ground && inBox(feet, g.box, 0.2)) {
      // the chute: speeds you up along it to its top speed (slide on it to get there faster), never slows you down
      const along = me.vel[0] * g.dir[0] + me.vel[2] * g.dir[2], top = g.speed * (input.sliding ? 1.25 : 1);
      if (along < top) { const a = (input.sliding ? GIM.slideAccSlide : GIM.slideAcc) * dt; me.vel[0] += g.dir[0] * a; me.vel[2] += g.dir[2] * a; }
      ev.push({ kind: 'slide', name: g.name, v: along });
    }
  }
  if (me.bounceT > 0) me.bounceT -= dt;
  if (me.padT > 0) me.padT -= dt;
  if (me.slipT > 0) me.slipT -= dt;
  return ev;
}
