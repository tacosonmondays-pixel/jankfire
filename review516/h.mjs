// in-process harness for honesty probes
const R = process.env.ROOT || process.cwd();
export const { Room } = await import(R + '/server/room.js');
export const { WEAPONS } = await import(R + '/shared/weapons.js');
export const { raycast } = await import(R + '/shared/physics.js');
export function mk(mode = 'ffa', extra = {}) {
  const room = new Room('probe' + Math.random(), mode);
  const human = (name, j = {}) => { const sent = []; const p = room.addHuman({ readyState: 1, send: (x) => sent.push(JSON.parse(x)), bufferedAmount: 0 }, { t: 'join', name, mode, ...j }); p.sent = sent; return p; };
  return { room, human };
}
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const snap = (room, p, pos, o = {}) => room.handle(p, { t: 's', q: p.seq, p: pos, v: o.v || [0, 0, 0], y: o.y ?? 0, x: o.x ?? 0, w: o.w || p.w, f: o.f || 0 });
export const dmgOf = (p, t) => p.sent.filter((m) => m.t === 'dmg' && m.to === t.id).length;
