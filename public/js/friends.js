// FRIENDS on the client (server/friends.js has the rules): the FRIENDS button in the party strip opens this panel.
// FRIENDS / REQUESTS tabs, add by username, each friend with where they are (in the menu, in a lobby, in a match) and
// INVITE (to your party) / JOIN (theirs); requests get ACCEPT / NAH. Accounts only; when the server has no friends table
// yet ({ off: 1 }) the button isn't shown at all.
import { account } from './account.js';
import { send as partySend, P } from './party.js';

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
export const FR = { off: false, list: null, err: '' }; // list: the server's last answer
let box = null, tab = 'friends', pollT = 0, opts = {};
export function initFriends(o) { opts = o; } // { toast(text, ms), click() }

async function api(path, body) {
  const r = await fetch('/api/' + path, { method: body ? 'POST' : 'GET', headers: { 'content-type': 'application/json', ...(account.token ? { authorization: 'Bearer ' + account.token } : {}) }, body: body ? JSON.stringify(body) : undefined });
  let d = {}; try { d = await r.json(); } catch { /* empty */ }
  if (!r.ok) throw new Error(d.error || 'friends: something broke');
  return d;
}
// the list (and whether friends are on at all). quiet: no toast on failure
export async function friendsLoad(quiet = true) {
  if (!account.token) { FR.list = null; return FR; }
  try { const d = await api('friends'); FR.off = !!d.off; FR.list = d.off ? null : d; FR.err = ''; }
  catch (e) { FR.err = e.message; if (!quiet) opts.toast(e.message, 2400); }
  return FR;
}
export const friendsOnline = () => (FR.list ? FR.list.friends.filter((f) => f.on).length : 0);
export const friendsShown = () => !FR.off; // (guests see the button too: it tells them to log in)

export function openFriends() {
  if (!box) {
    box = el('div', 'fr-panel'); box.id = 'friendsPanel';
    document.getElementById('menu').append(box);
    box.addEventListener('keydown', (e) => e.stopPropagation()); // (typing a name isn't a hotkey)
  }
  box.classList.remove('hidden');
  render();
  refresh();
}
export function closeFriends() { if (box) box.classList.add('hidden'); clearTimeout(pollT); }
const isOpen = () => box && !box.classList.contains('hidden') && !document.getElementById('menu').classList.contains('hidden');
async function refresh() { clearTimeout(pollT); if (!isOpen()) return; await friendsLoad(); render(); pollT = setTimeout(refresh, 8000); }

const where = (on) => !on ? 'offline' : on.where === 'match' ? `in a match${on.what ? ': ' + on.what : ''}` : on.where === 'lobby' ? `in lobby: ${on.what} (${on.size}/6)` : on.size > 1 ? `in the menu, party of ${on.size}` : 'in the menu';
const dot = (on) => (!on ? '#555' : on.where === 'match' ? '#ff4f6a' : on.where === 'lobby' ? '#ffe14d' : '#7dff4f');
async function act(path, body, okText) {
  opts.click && opts.click();
  try { const d = await api(path, body); if (okText) opts.toast(okText, 1800); if (d.friends) opts.toast(`you and ${body.name} are friends now`, 2000); }
  catch (e) { opts.toast(e.message, 2600); }
  await friendsLoad(); render();
}

function render() {
  if (!box) return;
  box.innerHTML = '';
  const head = el('div', 'fr-head'); head.append(el('span', 'hub-tag', 'FRIENDS'));
  const x = el('button', 'mid', 'X'); x.addEventListener('click', () => { opts.click && opts.click(); closeFriends(); }); head.append(x);
  box.append(head);
  if (!account.token) { box.append(el('p', 'fr-note', 'friends need an account. log in (top left) and they show up here. guests can still join a party with its code.')); return; }
  if (FR.off) { box.append(el('p', 'fr-note', 'friends aren\'t switched on on this server yet.')); return; }
  const L = FR.list || { friends: [], incoming: [], outgoing: [] };
  const tabs = el('div', 'fr-tabs');
  for (const [k, label] of [['friends', `FRIENDS ${L.friends.length}`], ['req', `REQUESTS ${L.incoming.length}`]]) {
    const b = el('button', k === tab ? 'on' : '', label);
    if (k === 'req' && L.incoming.length) b.classList.add('new');
    b.addEventListener('click', () => { tab = k; render(); }); tabs.append(b);
  }
  box.append(tabs);
  const add = el('div', 'fr-add'), inp = el('input'); inp.placeholder = 'add by username'; inp.maxLength = 24; inp.autocomplete = 'off'; inp.spellcheck = false;
  const ab = el('button', 'mid', 'ADD');
  const go = () => { const n = inp.value.trim(); if (n) { act('friends/add', { name: n }, `asked ${n}. now we wait`); inp.value = ''; } };
  ab.addEventListener('click', go); inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
  add.append(inp, ab); box.append(add);
  const list = el('div', 'fr-list');
  const inMine = new Set(P.ms.map((m) => m.name.toLowerCase()));
  if (tab === 'friends') {
    if (!L.friends.length) list.append(el('p', 'fr-note', 'no friends yet. add someone by their username. it\'s not weird.'));
    for (const f of L.friends) {
      const r = el('div', 'fr-row' + (f.on ? '' : ' off')), d = el('span', 'fr-dot'); d.style.background = dot(f.on);
      const t = el('div', 'fr-who'); t.append(el('b', null, f.name), el('small', null, inMine.has(f.name.toLowerCase()) ? 'in your party' : where(f.on)));
      r.append(d, t, el('span', 'fr-sp'));
      if (f.on && !inMine.has(f.name.toLowerCase())) {
        const iv = el('button', 'mid', 'INVITE'); iv.addEventListener('click', () => { opts.click && opts.click(); partySend({ t: 'pinvite', name: f.name }); });
        r.append(iv);
        if (!f.on.full) { const jn = el('button', 'mid', 'JOIN'); jn.title = 'join their party'; jn.addEventListener('click', () => { opts.click && opts.click(); partySend({ t: 'pjoinf', name: f.name }); setTimeout(() => { if (isOpen()) closeFriends(); }, 400); }); r.append(jn); }
      }
      const rm = el('button', 'fr-rm', '×'); rm.title = 'remove ' + f.name;
      rm.addEventListener('click', () => { if (rm.dataset.sure) act('friends/remove', { name: f.name }, `${f.name} removed`); else { rm.dataset.sure = 1; rm.textContent = 'SURE?'; setTimeout(() => { if (rm.isConnected) { delete rm.dataset.sure; rm.textContent = '×'; } }, 2500); } });
      r.append(rm);
      list.append(r);
    }
  } else {
    if (!L.incoming.length) list.append(el('p', 'fr-note', 'nobody wants to be friends right now. it happens.'));
    for (const n of L.incoming) {
      const r = el('div', 'fr-row'), d = el('span', 'fr-dot'); d.style.background = '#7dff4f';
      const t = el('div', 'fr-who'); t.append(el('b', null, n), el('small', null, 'wants to be friends'));
      const y = el('button', 'mid fr-yes', 'ACCEPT'), no = el('button', 'mid danger', 'NAH');
      y.addEventListener('click', () => act('friends/answer', { name: n, yes: true }, `you and ${n} are friends now`));
      no.addEventListener('click', () => act('friends/answer', { name: n, yes: false }, ''));
      r.append(d, t, el('span', 'fr-sp'), y, no); list.append(r);
    }
    if (L.outgoing.length) list.append(el('p', 'fr-note', 'waiting on: ' + L.outgoing.join(', ')));
  }
  box.append(list);
}
