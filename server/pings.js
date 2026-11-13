// PINGS: "over here" marks dropped from the big map (M) or the ping key. the server only relays them, to the sender
// and the humans on their side: friendly() decides (team, squad, co-op), from server state, never from the client.
// solo modes: only you see yours. rate limited, inside the map, plain numbers only. Mixed into Room by installPings.
import { PING, DRAW, drawQ, inPingBox } from '../shared/pings.js';

let H; // helpers from room.js (now, send)
const num = (v) => typeof v === 'number' && Number.isFinite(v);
const r1 = (v) => Math.round(v * 10) / 10;
const DRAW_LIFE = Number(process.env.JF_DRAW_LIFE) > 0 ? Number(process.env.JF_DRAW_LIFE) : DRAW.life; // test knob: ms a pencil stroke lives (the per-person cap counts live ones)

export function installPings(Room, helpers) {
  H = helpers;
  const P = Room.prototype, handle = P.handle;
  Object.assign(P, {
    handle(p, m) {
      if (m && m.t === 'mping') { this.onPing(p, m); return; }
      if (m && m.t === 'mdraw') { this.onDraw(p, m); return; }
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
    // the pencil: {t:'mdraw', pts:[x0, z0, ...]} draws a stroke, {t:'mdraw', clr:1} rubs out all of yours. same audience as a
    // ping. every point a plain number inside the map, snapped to DRAW.q, repeats dropped; 2..DRAW.pts points; a 7th live
    // stroke rubs out your oldest (gone: its id) so nobody can paper over the map
    onDraw(p, m) {
      if (!p || p.isBot || p.watch || !this.players.has(p.id)) return;
      const n = H.now();
      p.strokes = (p.strokes || []).filter((s) => n - s.t < DRAW_LIFE);
      if (Object.hasOwn(m, 'clr')) {
        if (m.clr !== 1 || n - (p.drawClrT || 0) < 500) return;
        p.drawClrT = n;
        if (!p.strokes.length) return;
        p.strokes = [];
        const msg = { t: 'mdraw', clr: 1, by: p.id };
        for (const o of this.pingMates(p)) H.send(o, msg);
        return;
      }
      const a = Object.hasOwn(m, 'pts') ? m.pts : null;
      if (!Array.isArray(a) || a.length < 4 || a.length > DRAW.pts * 2 || a.length % 2) return;
      const pts = [];
      for (let i = 0; i < a.length; i += 2) {
        const x = a[i], z = a[i + 1];
        if (!num(x) || !num(z) || !inPingBox(this.map, x, z)) return; // one bad point: the whole stroke goes
        const qx = drawQ(x), qz = drawQ(z);
        if (pts.length && pts[pts.length - 2] === qx && pts[pts.length - 1] === qz) continue;
        pts.push(qx, qz);
      }
      if (pts.length < 4) return;
      const ts = (p.drawTs || []).filter((t) => n - t < DRAW.win);
      p.drawTs = ts;
      if (ts.length >= DRAW.burst || n - (ts[ts.length - 1] || 0) < DRAW.gap) { if (n - (p.drawNoT || 0) > DRAW.win) { p.drawNoT = n; H.send(p, { t: 'mdraw', no: 1 }); } return; }
      ts.push(n);
      const id = (this.nextDraw = (this.nextDraw || 0) + 1);
      p.strokes.push({ id, t: n });
      const msg = { t: 'mdraw', id, by: p.id, pts };
      if (p.strokes.length > DRAW.keep) msg.gone = p.strokes.shift().id;
      for (const o of this.pingMates(p)) H.send(o, msg);
    },
  });
}
