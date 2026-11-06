// OVERDUE Tote Bag (WP3): the inventory grid (20 cells, up to 60 later), the quick bar under it, and the Locker when
// you're standing at one. drag a thing onto a bar slot to put it there, onto another cell to move it, onto DROP to
// leave it on the floor, onto the Locker to stash it (and back). click one thing, then a slot, if dragging is a pain.
// every move is a request: the sim checks it and sends the inventory back.
import { IV, itemCell, atLocker, heldItem } from './bar.js';
import { lootCard } from './lootfx.js';
import { itemAt, infoOf, INV } from '/shared/story/items.js';

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
let story = null, root = null, open = false, held = null; // held: what you clicked first { from: 'bag'|'bar'|'locker', i, u }
export const bagOpen = () => open;

export function initBag(st) { story = st; IV.on(() => { if (open) draw(); }); }
export function toggleBag(on = !open) {
  open = on;
  if (!root) { root = el('div', 'st-pick st-bagwrap hidden'); root.id = 'storyBag'; document.body.append(root); }
  root.classList.toggle('hidden', !open);
  held = null;
  if (open) { if (document.pointerLockElement) document.exitPointerLock(); draw(); }
}

const send = (o) => story.send('inv', o);
// what a drop (or a second click) of `src` onto `dst` means
function act(src, dst) {
  if (!src || !dst) return;
  if (dst.to === 'bar') send({ op: 'bar', slot: dst.i, u: src.u });
  else if (dst.to === 'bag' && src.from === 'bag' && src.i !== dst.i) send({ op: 'move', from: src.i, to: dst.i });
  else if (dst.to === 'bag' && src.from === 'bar') send({ op: 'bar', slot: src.i, u: null }); // off the bar (it stays in the bag)
  else if (dst.to === 'bag' && src.from === 'locker') send({ op: 'unstash', i: src.i });
  else if (dst.to === 'drop' && src.u != null) send({ op: 'drop', u: src.u });
  else if (dst.to === 'locker' && src.u != null) send({ op: 'stash', u: src.u });
}
function wire(c, src, dst) {
  if (src && src.u != null || src && src.from === 'locker') {
    c.draggable = true;
    c.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/plain', JSON.stringify(src)); e.dataTransfer.effectAllowed = 'move'; c.classList.add('drag'); });
    c.addEventListener('dragend', () => c.classList.remove('drag'));
  }
  if (dst) {
    c.addEventListener('dragover', (e) => { e.preventDefault(); c.classList.add('over'); });
    c.addEventListener('dragleave', () => c.classList.remove('over'));
    c.addEventListener('drop', (e) => { e.preventDefault(); c.classList.remove('over'); let s = null; try { s = JSON.parse(e.dataTransfer.getData('text/plain')); } catch { /* not ours */ } act(s, dst); });
  }
  c.addEventListener('click', (e) => {
    e.stopPropagation(); // (a locker cell sits inside the locker's drop area)
    if (held) { const h = held; held = null; if (dst) act(h, dst); draw(); return; }
    if (src && (src.u != null || src.from === 'locker')) { held = src; draw(); }
  });
  if (held && src && held.from === src.from && held.i === src.i) c.classList.add('held');
}

function draw() {
  const inv = IV.inv;
  root.innerHTML = '';
  if (!inv) return;
  const panel = el('div', 'st-panel st-bag');
  const head = el('div', 'st-bagtop');
  head.append(el('h2', null, 'TOTE BAG'), el('span', 'st-sub', `${inv.bag.filter(Boolean).length}/${inv.cap} · it's a bag. it holds things.`));
  const close = el('button', 'st-btn', 'CLOSE');
  close.addEventListener('click', () => toggleBag(false));
  head.append(close);
  panel.append(head);
  const info = el('div', 'st-info', held ? 'now click where it goes.' : 'drag things around. click one, then a slot, works too.');
  const grid = el('div', 'st-grid');
  const cardBox = el('div', 'st-bagcard'); // the item card for whatever you point at (▲▼ against what you hold)
  inv.bag.forEach((it, i) => {
    const c = itemCell(it);
    c.dataset.cell = i;
    wire(c, { from: 'bag', i, u: it ? it.u : null }, { to: 'bag', i });
    if (it) c.addEventListener('mouseenter', () => { const n = infoOf(it); info.textContent = `${n.name} · ${it.r}${it.q > 1 ? ' · x' + it.q : ''}`; cardBox.innerHTML = ''; cardBox.append(lootCard(it, heldItem())); });
    grid.append(c);
  });
  panel.append(grid, info);
  const row = el('div', 'st-barrow');
  row.append(el('b', 'st-lbl', 'QUICK BAR'));
  for (let i = 0; i < INV.bar; i++) {
    const u = inv.bar[i], it = u == null ? null : itemAt(inv, u);
    const c = itemCell(it, String(i + 1));
    c.dataset.bar = i;
    wire(c, { from: 'bar', i, u: it ? u : null }, { to: 'bar', i });
    row.append(c);
  }
  const drop = el('div', 'st-cell st-drop', 'DROP');
  drop.dataset.drop = 1;
  wire(drop, null, { to: 'drop' });
  row.append(drop);
  panel.append(row);
  if (atLocker()) {
    const lk = el('div', 'st-locker');
    lk.dataset.locker = 1;
    lk.append(el('b', 'st-lbl', `LOCKER · ${inv.locker.length} thing${inv.locker.length === 1 ? "" : "s"}. drop stuff here to keep it safe.`));
    const lg = el('div', 'st-grid small');
    inv.locker.forEach((it, i) => { const c = itemCell(it); c.dataset.lk = i; wire(c, { from: 'locker', i }, null); lg.append(c); });
    lk.append(lg);
    wire(lk, null, { to: 'locker' });
    panel.append(lk);
  }
  root.append(panel, cardBox);
}
