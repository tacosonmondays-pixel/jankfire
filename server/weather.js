// Weather sync: the room picks its map's weather timeline (shared/weather.js) when the map or the match changes, sends it
// to everyone, and hands it to each player who joins (right after their welcome). Server -> client only: no client
// message is read here. Look only (rain, clouds, lightning): nothing in the match changes. Mixed into Room by installWeather.
import { wxPlan, wxMsg, WX_SPAN } from '../shared/weather.js';

let H; // helpers from room.js (now, send)
export function installWeather(Room, helpers) {
  H = helpers;
  const P = Room.prototype, tick = P.tick, addHuman = P.addHuman;
  Object.assign(P, {
    tick(dt) {
      tick.call(this, dt);
      this.wxCheck();
    },
    addHuman(ws, m) {
      const p = addHuman.call(this, ws, m);
      if (p && !this.wxCheck()) H.send(p, this.wxOut()); // (a fresh plan already went to everyone, them too)
      return p;
    },
    // a new plan when the map changed, a new match started, or the old plan is about to run out. true = sent one
    wxCheck() {
      const w = this.wx, r0 = this.round ? this.round.t0 || 0 : 0, n = H.now();
      if (w && w.plan.m === this.cfg.map && w.r0 === r0 && n - w.t0 < (WX_SPAN - 120) * 1000) return false;
      this.wx = { plan: wxPlan(this.cfg.map, (Math.random() * 4294967296) >>> 0, H.force || ''), t0: n, r0 };
      this.broadcast(this.wxOut());
      return true;
    },
    wxOut() { return wxMsg(this.wx.plan, (H.now() - this.wx.t0) / 1000); },
  });
}
