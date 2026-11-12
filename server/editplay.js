// PLAY HERE WITH BOTS, the server's half. Owner only: the account named in the JF_OWNER env var (set on Render; nothing
// in the database). The editor POSTs its edits once to /api/edit-ticket with the owner's login token; we check the
// token, the account, the size and every op, and hand back a one-use ticket (5 minutes). The game's join then carries
// only the ticket (cfg.editTicket), and room.js builds that edited map for one private bots room. Anyone else gets 403
// and no room ever takes edits from a player in a match.
import crypto from 'node:crypto';
import { okEdit } from '../shared/editmaps.js';

const OWNER = (process.env.JF_OWNER || '').trim().toLowerCase();
const tickets = new Map(); // ticket -> { acct, edit: { base, ops }, t }
const TTL = 5 * 60 * 1000, MAX_BODY = 1500000;
export const ownerSet = () => !!OWNER;
export const isOwner = (acctName) => !!OWNER && typeof acctName === 'string' && acctName === OWNER;

function readBody(req) {
  return new Promise((res, rej) => {
    let n = 0; const parts = [];
    req.on('data', (c) => { n += c.length; if (n > MAX_BODY) { rej(new Error('too big')); req.destroy(); } else parts.push(c); });
    req.on('end', () => { try { res(JSON.parse(Buffer.concat(parts).toString('utf8'))); } catch (e) { rej(e); } });
    req.on('error', rej);
  });
}
export async function editTicketHttp(req, res, accounts) {
  const send = (code, obj) => { res.writeHead(code, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(obj)); };
  try {
    if (req.method !== 'POST') return send(405, { error: 'POST' });
    if (!OWNER) return send(403, { error: 'no owner set on this server (JF_OWNER)' });
    const auth = (req.headers.authorization || '').replace(/^Bearer /, '');
    const u = auth ? await accounts.verify(auth).catch(() => null) : null;
    if (!u || !isOwner(u.name_lower)) return send(403, { error: 'only the owner can do this' });
    let body = null;
    try { body = await readBody(req); } catch { return send(400, { error: 'bad or too big' }); }
    const edit = body && typeof body === 'object' ? { base: body.map, ops: body.ops } : null;
    if (!okEdit(edit)) return send(400, { error: 'those edits look broken' });
    const now = Date.now();
    for (const [k, v] of tickets) if (now - v.t > TTL || v.acct === u.name_lower) tickets.delete(k); // (one live ticket per owner)
    const ticket = crypto.randomBytes(12).toString('hex');
    tickets.set(ticket, { acct: u.name_lower, edit, t: now });
    return send(200, { ticket });
  } catch (e) { console.error('edit-ticket', e); return send(500, { error: 'server error' }); }
}
// the join's ticket -> the edit (once), only for the same account
export function takeTicket(ticket, acctName) {
  if (typeof ticket !== 'string' || ticket.length !== 24) return null;
  const t = tickets.get(ticket);
  if (!t) return null;
  tickets.delete(ticket);
  if (Date.now() - t.t > TTL || !isOwner(acctName) || t.acct !== acctName) return null;
  return t.edit;
}
