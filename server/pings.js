// PINGS: "over here" marks dropped from the big map (M) or the ping key. the server only relays them, to the sender
// and the humans on their side: friendly() decides (team, squad, co-op), from server state, never from the client.
// solo modes: only you see yours. rate limited, inside the map, plain numbers only. Mixed into Room by installPings.
import { PING, inPingBox } from '../shared/pings.js';

let H; // helpers from room.js (now, send)
const num = (v) => typeof v === 'number' && Number.isFinite(v);
const r1 = (v) => Math.round(v * 10) / 10;

export function installPings(Room, helpers) {
  H = helpers;
  const P = Room.prototype, handle = P.handle;
  Object.assign(P, {
    handle(p, m) {
      if (m && m.t === 'mping') { this.onPing(p, m); return; }
      return handle.call(this, p, m);
    },
    // who sees a ping from p: p, and the humans friendly() puts on p's side (never a spectator cam: it's friends with all)
    pingMates(p) { return [...this.players.values()].filter((o) => !o.isBot && (o === p || (!p.cam && !o.cam && this.friendly(p, o)))); },
    onPing(p, m) {
      if (!p || p.isBot || p.watch || !this.players.has(p.id)) return;
      if (!['x', 'y', 'z'].every((k) => Object.hasOwn(m, k) && num(m[k]))) return;
      const { x, y, z } = m;
      if (y < PING.y[0] || y > PING.y[1] || !inPingBox(this.map, x, z)) return;
      const n = H.now(), ts = (p.pingTs || []).filter((t) => n - t < PING.win);
      p.pingTs = ts;
      if (ts.length >= PING.burst || n - (ts[ts.length - 1] || 0) < PING.gap) { if (n - (p.pingNoT || 0) > PING.win) { p.pingNoT = n; H.send(p, { t: 'mping', no: 1 }); } return; }
      ts.push(n);
      const msg = { t: 'mping', id: (this.nextPing = (this.nextPing || 0) + 1), by: p.id, p: [r1(x), r1(y), r1(z)] };
      for (const o of this.pingMates(p)) H.send(o, msg);
    },
  });
}
