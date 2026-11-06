// OVERDUE weapon wheel (WP3): hold Q for a ring of your 8 quick-bar slots, move the mouse toward one, let go to take
// it. time slows to 20% while it's open (solo; co-op will be 70%, it's shared time). while it's open nothing leaks
// through: no firing, no looking around, no jumping into a slot by accident.
import { IV, itemCell, useBar } from './bar.js';
import { itemAt, infoOf, kindOf, INV } from '/shared/story/items.js';

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const TAGS = { gun: 'GUNS', melee: 'MELEE', gear: 'GEAR', streak: 'STREAKS', snack: 'SNACKS' };
let root = null, open = false, aim = [0, 0], pick = -1;
export const wheelOpen = () => open;
export const wheelScale = (coop) => (open ? (coop ? 0.7 : 0.2) : 1);

export function openWheel() {
  if (open || !IV.inv) return;
  open = true; aim = [0, 0]; pick = -1;
  if (!root) { root = el('div', 'st-wheel'); root.id = 'storyWheel'; document.body.append(root); }
  root.innerHTML = '';
  const R = 150;
  for (let i = 0; i < INV.bar; i++) {
    const a = (i / INV.bar) * Math.PI * 2 - Math.PI / 2, u = IV.inv.bar[i], it = u == null ? null : itemAt(IV.inv, u);
    const c = itemCell(it, String(i + 1));
    c.classList.add('st-wedge');
    c.style.left = `calc(50% + ${Math.cos(a) * R}px)`; c.style.top = `calc(50% + ${Math.sin(a) * R}px)`;
    if (it) c.append(el('em', 'st-tag', TAGS[kindOf(it.b)] || ''));
    c.dataset.i = i;
    root.append(c);
  }
  root.append(el('div', 'st-wname', 'pick something'));
  root.classList.remove('hidden');
}
// mouse movement while it's open steers the pick instead of the camera
export function wheelLook(dx, dy) {
  if (!open) return false;
  if (Math.abs(dx) > 250 || Math.abs(dy) > 250) return true; // (pointer lock's one-off giant fake jumps, like main.js drops)
  aim[0] += dx; aim[1] += dy;
  const L = Math.hypot(aim[0], aim[1]);
  if (L > 140) { aim[0] *= 140 / L; aim[1] *= 140 / L; }
  if (L > 30) {
    let a = Math.atan2(aim[1], aim[0]) + Math.PI / 2;
    if (a < 0) a += Math.PI * 2;
    pick = Math.round(a / (Math.PI * 2 / INV.bar)) % INV.bar;
  }
  for (const c of root.querySelectorAll('.st-wedge')) c.classList.toggle('pick', Number(c.dataset.i) === pick);
  const u = pick >= 0 ? IV.inv.bar[pick] : null, it = u == null ? null : itemAt(IV.inv, u);
  root.querySelector('.st-wname').textContent = it ? infoOf(it).name : pick >= 0 ? 'empty' : 'pick something';
  return true;
}
// let go of Q: take what you pointed at (nothing if you didn't move)
export function closeWheel(take = true) {
  if (!open) return;
  open = false;
  root.classList.add('hidden');
  if (take && pick >= 0) useBar(pick);
}
