// The Tall Guy From HR: the thing in the Scary Forest. Shared by the server (it owns him: where he is, who he's after,
// who is staring) and the client (draws him, the static, the sounds), so both agree on what "looking at him" means.
// Rules: he shows up far off between the trees, closer each time nobody is looking, never moves while watched.
// Looking right at him fills your meter (faster up close); full = he takes you. He likes people who are on their own.
export const HR = {
  name: 'Tall Guy From HR',
  // how often he visits, per room setting (seconds between visits). off = never (competitive)
  every: { off: null, rare: [150, 210], on: [65, 105], lots: [26, 42] },
  names: { off: 'off (competitive)', rare: 'rare', on: 'on', lots: 'lots (he loves it here)' },
  first: 25, // seconds into a round before his first visit
  life: 60, // seconds he hangs about before he gives up and leaves
  far: [36, 52], // how far from his target he turns up
  see: 66, // how far away you can make him out in the fog
  seeNVG: 115, // with night-vision goggles on (claude/new-gear): players with p.nvg / ME.nvg see him further out
  watchAng: 0.85, // inside this angle of where you look he's "in view": he can't move
  stareAng: 0.2, // looking right at him (plus his size at that distance): your meter fills
  rate: [0.13, 0.95], // meter per second while staring: far .. right in your face
  decay: 0.32, // meter per second back down when you look away
  step: [3.5, 6.5], // metres he blinks toward his target when nobody's looking
  stepEvery: [0.8, 1.6], // seconds between blinks
  reach: 2.4, // this close and unwatched: he's got you
  height: 3.55,
  takeKill: 0.6, // chance a take is a death (the rest get transferred somewhere awful)
};
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
// where someone looking along yaw/pitch is aiming (the same convention as the bots' aim)
export function lookDir(yaw, pitch) { const c = Math.cos(pitch); return [-Math.sin(yaw) * c, Math.sin(pitch), -Math.cos(yaw) * c]; }
// how an eye relates to him standing at feet: distance, the angle off your look, and whether that counts as in view / staring
export function hrSight(eye, yaw, pitch, feet, nvg) {
  const c = [feet[0], feet[1] + HR.height * 0.62, feet[2]];
  const dx = c[0] - eye[0], dy = c[1] - eye[1], dz = c[2] - eye[2], d = Math.hypot(dx, dy, dz) || 1e-6;
  const L = lookDir(yaw, pitch), dot = (L[0] * dx + L[1] * dy + L[2] * dz) / d;
  const ang = Math.acos(clamp(dot, -1, 1)), range = nvg ? HR.seeNVG : HR.see;
  const inRange = d < range;
  return { d, ang, c, dir: [dx / d, dy / d, dz / d], view: inRange && ang < HR.watchAng, stare: inRange && ang < HR.stareAng + Math.atan(HR.height * 0.4 / d) };
}
// how fast your meter fills while you stare, by distance (and goggles: you see more, so it gets you from further)
export function stareRate(d, nvg) {
  const k = 1 - clamp(d / (nvg ? HR.seeNVG : HR.see), 0, 1);
  return HR.rate[0] + (HR.rate[1] - HR.rate[0]) * k * k;
}
// the deadpan lines
export const HR_LINES = {
  feed: ['had a quick chat with HR', 'was let go', 'got invited to a meeting', 'signed the paperwork', 'was restructured', 'accepted the job offer', 'was asked to step into his office', 'got a performance review'],
  dead: ['you made eye contact with HR. you have been let go.', 'HR would like a word. forever.', 'you have been restructured.', 'your position has been eliminated.', 'mandatory fun: completed.'],
  stare: ["DON'T LOOK AT HIM", 'STOP STARING', 'HE SAW YOU SEE HIM', 'LOOK AWAY'],
};
