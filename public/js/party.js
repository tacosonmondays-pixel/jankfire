// PARTIES on the client (server/party.js has the rules): the menu connection. It opens with the game and stays open
// through matches, so the party survives them. P is what the server last said; the hub draws it (hubmenu.js), the
// lineup stands it on the stage (lineup.js). When the leader starts, the server sends 'pgo' (a mode, a cfg with a
// one-use ticket to the party's room): in the menu you go straight in, in a match you get asked first.

// P.ms[i] = { id, name, look, gun (a primary's id or null), mf (mech frame), ready, acct, busy }: the lobby scenes read
// this too (onParty(fn) says when it changed). P.set = the leader's { side, mode } or null
export const P = { on: false, me: 0, code: '', lead: 0, ms: [], set: null, max: 6 };
let ws = null, opts = {}, retry = 0, busy = false, subs = [], lastMe = '';
export function initParty(o) {
  opts = o; // { hello() -> { name, look, token, gun, mf }, start(mode, cfg), joined() -> bool, toast(text, ms), ask(text, yes) }
  connect();
  setInterval(() => { const b = !!opts.joined(); if (b !== busy) { busy = b; send({ t: 'pbusy', on: b }); } }, 1500); // (in a match: the lineup greys you out)
}
export const onParty = (f) => subs.push(f);
const changed = (why) => { for (const f of subs) try { f(why); } catch (e) { console.error(e); } };
export const inParty = () => P.on && P.ms.length > 1;
export const isLead = () => !P.on || P.lead === P.me;
export const leadName = () => { const l = P.ms.find((m) => m.id === P.lead); return l ? l.name : ''; };
export function send(m) { if (ws && ws.readyState === 1) { ws.send(JSON.stringify(m)); return true; } return false; }

function connect() {
  try { ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws'); } catch { return later(); }
  ws.onopen = () => { retry = 0; const h = opts.hello(); lastMe = JSON.stringify([h.look, h.gun, h.mf]); send({ t: 'hub', name: h.name, look: h.look, token: h.token, gun: h.gun, mf: h.mf }); };
  ws.onmessage = (e) => {
    let m; try { m = JSON.parse(e.data); } catch { return; }
    if (m.t === 'party') {
      const was = P.set && JSON.stringify(P.set), grew = m.ms.length > P.ms.length && P.on;
      Object.assign(P, { on: true, me: m.me, code: m.code, lead: m.lead, ms: m.ms, set: m.set, max: m.max || 6 });
      changed(was !== (m.set && JSON.stringify(m.set)) ? 'set' : grew ? 'grew' : 'party');
    } else if (m.t === 'perr') opts.toast(String(m.m || 'nope').slice(0, 80), 2600);
    else if (m.t === 'pgo') go(m);
  };
  ws.onclose = () => { P.on = false; ws = null; changed('off'); later(); };
}
function later() { setTimeout(connect, Math.min(30000, 2000 * 2 ** retry++)); }
// a new name, look or login: say hello again (the server takes it from a fresh connection)
export function partyRehello() { if (ws && !inParty()) { const w = ws; ws = null; w.onclose = null; w.close(); connect(); } }

function go(m) {
  if (typeof m.mode !== 'string' || !m.cfg || typeof m.cfg !== 'object') return;
  if (isLead() || !opts.joined()) { opts.start(m.mode, m.cfg); return; }
  opts.ask(`${leadName() || 'your party'} is starting a match`, () => opts.start(m.mode, m.cfg)); // (you're mid-match: your call)
}
export const partyJoin = (code) => send({ t: 'pjoin', code: String(code || '').slice(0, 12) });
export const partyLeave = () => send({ t: 'pleave' });
export const partyKick = (id) => send({ t: 'pkick', id });
export const partyLead = (id) => send({ t: 'plead', id });
export const partyReady = (on) => send({ t: 'pready', on: !!on });
export const partySet = (side, mode) => { if (inParty() && isLead()) send({ t: 'pset', side, mode }); };
export const partyGo = (mode, cfg) => send({ t: 'pgo', mode, cfg });
export const meReady = () => { const me = P.ms.find((m) => m.id === P.me); return !!(me && me.ready); };
// back in the menu with a new outfit, primary or mech frame: tell the party (only when something changed)
export function partyMe() {
  if (!P.on || !opts.hello) return;
  const h = opts.hello(), k = JSON.stringify([h.look, h.gun, h.mf]);
  if (k !== lastMe && send({ t: 'pme', look: h.look, gun: h.gun, mf: h.mf })) lastMe = k;
}
