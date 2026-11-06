// OVERDUE quest HUD: the tracker (top right: the mission, the step, its goals with ticks, a red timer), waypoints over
// the world (a yellow diamond + metres; off screen it sticks to the edge and turns pink), the mission start / end cards
// (graded like a performance review, DESIGN §8.4), failure cards and small toasts (codex entries, people met).
import * as THREE from 'three';
import { organic, organicRedraw } from '../organic.js';
import { sfx } from '../audio.js';

const $ = (id) => document.getElementById(id);
let Q = null, wps = [], lastKey = '';
const v = new THREE.Vector3();

function ui() {
  if (Q) return Q;
  const el = document.createElement('div'); el.id = 'stQuest'; el.className = 'hidden';
  $('stLayer').append(el); organic(el, { rim: 4, lumps: 3, shadow: [6, 6] });
  Q = { el };
  return Q;
}
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

// objs: S.quests.objectives(). where(marker) -> [x, y, z] | null. cam: the camera
export function questHud(objs, where, cam, hidden) {
  ui();
  const o = objs[0];
  if (!o || hidden) { Q.el.classList.add('hidden'); for (const w of wps) w.el.remove(); wps = []; lastKey = ''; return; }
  const key = JSON.stringify([o.quest, o.step, o.goals.map((g) => g.n), o.timer != null ? Math.ceil(o.timer) : -1, objs.length]);
  if (key !== lastKey) {
    const fresh = !lastKey.startsWith(JSON.stringify([o.quest, o.step]).slice(0, -1));
    lastKey = key;
    const goals = o.goals.length > 1 || (o.goals[0] && (o.goals[0].of > 1 || o.goals[0].text)) ? o.goals.map((g) => `<div class="q-goal${g.done ? ' done' : ''}">${esc(g.text || '')}${g.of > 1 ? ` ${g.n}/${g.of}` : ''}${g.optional ? ' (bonus)' : ''}</div>`).join('') : '';
    const t = o.timer != null ? `<div class="q-timer">${Math.floor(o.timer / 60)}:${String(Math.ceil(o.timer % 60) % 60).padStart(2, '0')}</div>` : '';
    Q.el.innerHTML = `<div class="q-title"><i>${o.kind === 'main' ? '★' : '◆'}</i>${esc(o.title)}</div><div class="q-step">${esc(o.text)}</div>${goals}${t}${objs.length > 1 ? `<div class="q-more">+${objs.length - 1} more (J)</div>` : ''}`;
    Q.el.classList.remove('hidden');
    organicRedraw(Q.el);
    if (fresh) { Q.el.classList.remove('flash'); void Q.el.offsetWidth; Q.el.classList.add('flash'); }
  }
  // waypoints: the tracked step's markers
  const pts = [];
  if (o.marker) pts.push(o.marker);
  for (const g of o.goals) if (!g.done && g.marker && !pts.includes(g.marker)) pts.push(g.marker);
  while (wps.length < pts.length) { const el = document.createElement('div'); el.className = 'st-wp'; el.innerHTML = '<span class="pin"><b>!</b></span><span class="d"></span>'; $('stLayer').append(el); wps.push({ el }); }
  while (wps.length > pts.length) wps.pop().el.remove();
  const W = innerWidth, H = innerHeight;
  pts.forEach((m, i) => {
    const p = where(m), w = wps[i];
    if (!p) { w.el.style.display = 'none'; return; }
    w.el.style.display = '';
    v.set(p[0], p[1] + 2.4, p[2]);
    const d = cam.position.distanceTo(v);
    v.project(cam);
    let x = (v.x * 0.5 + 0.5) * W, y = (-v.y * 0.5 + 0.5) * H;
    const behind = v.z > 1, off = behind || x < 30 || x > W - 30 || y < 60 || y > H - 30;
    if (behind) { x = W - x; y = H - 40; }
    x = Math.max(30, Math.min(W - 30, x)); y = Math.max(60, Math.min(H - 30, y));
    w.el.classList.toggle('off', off);
    w.el.style.left = x + 'px'; w.el.style.top = y + 'px';
    w.el.querySelector('.d').textContent = `${Math.round(d)}m`;
  });
}

// the big slammed cards. kind: 'start' | 'done' | 'fail' | 'step'
export function card(kind, title, sub = '', grade = '', dur = 2.6) {
  const el = document.createElement('div');
  el.className = 'st-card' + (kind === 'fail' ? ' fail' : '');
  const k = { start: 'MISSION', done: 'MISSION COMPLETE', fail: 'MISSION FAILED', step: '', side: 'SIDE JOB' }[kind] ?? kind;
  el.innerHTML = `<div class="k">${esc(k)}</div><div class="t">${esc(title)}</div>${sub ? `<div class="s">${esc(sub)}</div>` : ''}${grade ? `<div class="grade">${esc(grade)}</div>` : ''}`;
  $('stLayer').append(el); organic(el, { rim: 5, lumps: 4, shadow: [9, 9] });
  if (kind === 'start' || kind === 'side') sfx.rankUp && sfx.rankUp(); else if (kind === 'done') sfx.cash && sfx.cash(); else if (kind === 'fail') sfx.hurt && sfx.hurt();
  setTimeout(() => el.classList.add('out'), dur * 1000);
  setTimeout(() => el.remove(), dur * 1000 + 450);
  return el;
}
let toastY = 0;
export function toast(html, dur = 3.2) {
  const el = document.createElement('div'); el.className = 'st-toast'; el.innerHTML = html;
  el.style.top = `calc(46% + ${toastY * 54}px)`; toastY = (toastY + 1) % 4;
  $('stLayer').append(el); organic(el, { rim: 4, lumps: 2, shadow: [5, 5] });
  setTimeout(() => el.remove(), dur * 1000);
}
