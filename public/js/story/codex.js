// OVERDUE codex (J): what you've learned. tabs: JOBS (active + done quests), PEOPLE (characters met), LORE, OPTION C
// (the fragments, on paper). Locked entries show as ??? so you know there's more.
import { organic } from '../organic.js';

const $ = (id) => document.getElementById(id);
let el = null, tab = 'jobs';
const TABS = [['jobs', 'JOBS'], ['char', 'PEOPLE'], ['lore', 'LORE'], ['frag', 'OPTION C']];
const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

export const codexOpen = () => !!el && !el.classList.contains('hidden');
export function toggleCodex(S, on = !codexOpen()) {
  if (!el) {
    el = document.createElement('div'); el.id = 'stCodex'; el.className = 'hidden';
    $('stLayer').append(el); organic(el, { rim: 6, lumps: 5, shadow: [10, 10] });
    el.addEventListener('mousedown', (e) => { const t = e.target.closest('[data-tab]'); if (t) { tab = t.dataset.tab; render(S); } e.stopPropagation(); });
  }
  el.classList.toggle('hidden', !on);
  if (on) { if (document.pointerLockElement) document.exitPointerLock(); render(S); }
}
function render(S) {
  const st = S.st, D = S.defs;
  let body = '';
  if (tab === 'jobs') {
    const q = Object.entries(st.quests).sort((a, b) => (a[1].done ? 1 : 0) - (b[1].done ? 1 : 0));
    body = q.map(([id, s]) => { const d = D.quests[id] || {}; const step = d.steps && d.steps.find((x) => x.id === s.step);
      return `<div class="ent"><b>${esc(d.title || id)}${s.done ? ' ✓' : s.failed ? ' ✗' : ''}</b>${esc(s.done ? (d.ends && s.end && d.ends[s.end] && d.ends[s.end].grade) || 'done.' : step ? step.text : d.blurb || '')}</div>`; }).join('') || '<div class="ent lock"><b>NO JOBS</b>go talk to someone.</div>';
  } else {
    const all = Object.entries(D.codex).filter(([, c]) => c.kind === tab);
    body = all.map(([id, c]) => st.codex[id] ? `<div class="ent ${tab === 'frag' ? 'frag' : ''}"><b>${esc(c.title)}</b>${esc(c.text)}</div>` : `<div class="ent lock"><b>???</b>not yet.</div>`).join('');
  }
  const n = (k) => Object.entries(D.codex).filter(([id, c]) => c.kind === k && st.codex[id]).length + '/' + Object.values(D.codex).filter((c) => c.kind === k).length;
  el.innerHTML = `<h2>THE BOOKS</h2><div class="tabs">${TABS.map(([k, t]) => `<span data-tab="${k}" class="${k === tab ? 'on' : ''}">${t}${k === 'jobs' ? '' : ' ' + n(k)}</span>`).join('')}</div><div class="list">${body}</div><div class="foot">J to close · written in crayon, so it's forever</div>`;
}
