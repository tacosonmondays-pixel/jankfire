// Gun Game on your screen: your rung, what you hold now and what's next, the whole ladder as pips,
// who's closest to the spoon, and the callouts (level up, HUMILIATED, someone has the spoon).
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { WEAPONS } from '/shared/weapons.js';
import { LADDER } from '/shared/modes.js';

const $ = (id) => document.getElementById(id);
const N = LADDER.length;
G.gg = new Map(); // player id -> rung (0 = the first weapon, N = won)
const on = () => !!(G.joined && G.round && G.round.game === 'gun');
const wOf = (n) => WEAPONS[LADDER[Math.max(0, Math.min(N - 1, n))]];
const nameOf = (id) => (id === G.myId ? G.myName : (G.names.get(id) || {}).name || '???');
const rungOf = (id) => G.gg.get(id) || 0;

net.on('gg', (m) => {
  if (m.all) { G.gg.clear(); for (const [id, n] of m.all) G.gg.set(id, n); return; }
  G.gg.set(m.id, m.n);
  const me = m.id === G.myId, name = nameOf(m.id);
  if (m.k === 'up' && me) { hud.msg(`${wOf(m.n).name.toUpperCase()} · ${m.n + 1}/${N}`, 1.6, 'brag'); sfx.rankUp(); }
  else if (m.k === 'last') {
    hud.msg(me ? 'YOU HAVE THE SPOON · ONE KILL WINS' : `${name.toUpperCase()} HAS THE SPOON`, 2.6, 'brag');
    hud.chat(null, null, me ? 'last rung: one kill with the spoon wins it' : `${name} made it to the spoon. one kill and they win`);
    if (me) sfx.rankUp(); else sfx.ting();
  } else if (m.k === 'down') {
    if (me) { hud.msg('HUMILIATED', 2.4, 'slip'); sfx.sad(); }
    hud.chat(null, null, `${nameOf(m.by)} humiliated ${me ? 'you' : name}: back to ${wOf(m.n).name} (${m.n + 1}/${N})`);
  } else if (m.k === 'win') hud.chat(null, null, `${name} won gun game with the spoon`);
});

// top of the screen: 7/16 · Marble Shotgun · next: Sniper, then a pip per rung (the leader gets a marker)
export function updateGunGame() {
  const bar = $('ggBar');
  const show = on() && !G.round.over;
  document.body.classList.toggle('mode-gun', on());
  bar.classList.toggle('hidden', !show);
  if (!on() && bar.dataset.key) { bar.dataset.key = ''; for (const id of ['ggRung', 'ggNow', 'ggNext', 'ggLead', 'ggPips']) $(id).textContent = ''; } // left gun game: no stale numbers
  if (!show) return;
  const mine = Math.min(rungOf(G.myId), N - 1);
  let lead = G.myId, ln = rungOf(G.myId);
  for (const [id, n] of G.gg) if (n > ln && G.names.has(id)) { ln = n; lead = id; }
  const key = `${mine}|${lead}|${ln}`;
  if (bar.dataset.key === key) return;
  bar.dataset.key = key;
  const w = wOf(mine), nx = mine + 1 < N ? wOf(mine + 1) : null;
  $('ggRung').textContent = `${mine + 1}/${N}`;
  $('ggNow').textContent = w.name;
  $('ggNow').style.color = w.color;
  $('ggNext').textContent = nx ? `next: ${nx.name}` : 'LAST RUNG · one kill wins';
  $('ggNext').style.color = nx ? nx.color : '#ffe14d';
  const pips = $('ggPips');
  pips.innerHTML = '';
  LADDER.forEach((id, i) => {
    const p = document.createElement('i');
    p.style.setProperty('--c', WEAPONS[id].color);
    p.className = (i < mine ? 'done' : i === mine ? 'on' : '') + (lead !== G.myId && i === Math.min(ln, N - 1) ? ' lead' : '');
    p.title = WEAPONS[id].name;
    pips.append(p);
  });
  $('ggLead').textContent = lead === G.myId ? (ln > 0 ? 'you are in the lead' : '') : `leader: ${nameOf(lead)} ${Math.min(ln, N - 1) + 1}/${N}`;
}

// the clock line under the mode label (the bar shows the rest)
export function ggRoundText(r) {
  if (r.game !== 'gun' || r.over) return null;
  const s = Math.ceil(r.left / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; // (the line above already says Gun Game)
}
// TAB scores: ordered by rung, with the rung next to the name
export function ggScoreRows(rows) {
  if (!on()) return;
  const n = (r) => (r.me ? rungOf(G.myId) : rungOf(r.id));
  rows.sort((a, b) => n(b) - n(a) || b.k - a.k);
  for (const r of rows) r.name = `${r.name}  ${Math.min(n(r), N - 1) + 1}/${N}`;
}
// end screen: where everyone got to
export function ggRowNote(id, m) {
  if (m.game !== 'gun') return '';
  const n = rungOf(id);
  return n >= N ? 'SPOON KILL' : `rung ${n + 1}/${N}`;
}
export function resetGunGame() {
  G.gg.clear();
  document.body.classList.remove('mode-gun');
  $('ggBar').classList.add('hidden');
  $('ggBar').dataset.key = '';
  for (const id of ['ggRung', 'ggNow', 'ggNext', 'ggLead', 'ggPips']) $(id).textContent = ''; // no stale numbers when it shows again
}
