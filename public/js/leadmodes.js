// LEADERBOARD tabs: OVERALL (the old boards, drawn by main.js) + one tab per mode, each with its own boards
// (shared/modestats.js). The per-mode boards come from /api/leaderboard/<mode> and use the same columns as OVERALL.
import { MODE_STATS, MODE_IDS, fmtBoard } from '/shared/modestats.js';

const $ = (id) => document.getElementById(id);
const TABS = [['all', 'OVERALL'], ...MODE_IDS.map((m) => [m, MODE_STATS[m].name])];
let cur = 'all', bar = null, drawOverall = null, ask = 0;
const CSS = `
#leadTabs { margin: 0 0 12px; padding-left: 0; justify-content: center; }
.leadgrid.mode6 { grid-template-columns: repeat(6, 1fr); }
@media (max-width: 1000px) { .leadgrid.mode6 { grid-template-columns: repeat(3, 1fr); } }
.leadgrid ol { padding-left: 0; }
.leadgrid li { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; list-style-position: inside; } /* one line each: long names get ... */
.leadgrid .lbNote { grid-column: 1 / -1; color: #aaa; font-size: 12px; text-align: center; }
`;

export function initLeaderTabs(overall) {
  drawOverall = overall;
  if (bar) return;
  const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
  bar = document.createElement('div'); bar.id = 'leadTabs'; bar.className = 'es-tabbar';
  for (const [id, name] of TABS) {
    const b = document.createElement('button'); b.className = 'es-tab'; b.dataset.lb = id; b.textContent = name;
    b.addEventListener('click', () => { cur = id; showLeaders(); });
    bar.append(b);
  }
  $('leaders').before(bar);
}

export async function showLeaders() {
  for (const b of bar.children) b.classList.toggle('on', b.dataset.lb === cur);
  const el = $('leaders');
  el.classList.toggle('mode6', cur !== 'all' && MODE_STATS[cur].boards.length > 5);
  if (cur === 'all') { drawOverall(); return; }
  const mode = cur, me = ++ask;
  el.textContent = 'loading...';
  try {
    const res = await fetch('/api/leaderboard/' + mode);
    if (!res.ok) throw new Error('bad');
    const data = await res.json();
    if (me !== ask) return; // clicked another tab meanwhile
    el.innerHTML = '';
    for (const b of MODE_STATS[mode].boards) {
      const c = document.createElement('div');
      const h = document.createElement('h4'); h.textContent = b.title; c.append(h);
      const ol = document.createElement('ol'), rows = (data.boards && data.boards[b.id]) || [];
      for (const r of rows) {
        const li = document.createElement('li'); li.textContent = r.name + ' ';
        const sp = document.createElement('span'); sp.textContent = fmtBoard(b, r.value); li.append(sp);
        ol.append(li);
      }
      if (!rows.length) { const li = document.createElement('li'); li.textContent = 'nobody yet'; ol.append(li); }
      c.append(ol); el.append(c);
    }
    const note = document.createElement('div'); note.className = 'lbNote';
    note.textContent = `real matches only, accounts only. ${MODE_STATS[mode].note || ''}`;
    el.append(note);
  } catch { if (me === ask) el.textContent = 'could not load the leaderboard'; }
}
