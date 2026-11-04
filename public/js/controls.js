// SETTINGS > CONTROLS: every action in keys.js by group. click a key, press the new key or mouse button.
// Esc cancels, Backspace / Delete clears that slot, a key another action had gets swapped onto it (keys.js K.set).
import { K, ACTIONS, GROUPS } from './keys.js';

const $ = (id) => document.getElementById(id);
let cap = null, save = () => {}, wired = false, swallowClickUntil = 0, swallowUp = '', resetArm = 0;

// main.js calls this from show(): open = the controls screen is the one showing
export function controlsScreen(open, saveFn) {
  if (saveFn) save = saveFn;
  if (!open) { cap = null; return; }
  if (!wired) wire();
  msg('');
  render();
}
function msg(t, warn) { const el = $('ctlMsg'); el.textContent = t; el.className = warn ? 'warn' : ''; }
const movedText = (m) => (m ? ` · that was ${m.label}'s key, so ${m.label} is now ${m.to ? K.codeLabel(m.to) : 'unbound'}` : '');

function render() {
  const list = $('ctlList');
  list.innerHTML = '';
  for (const g of GROUPS) {
    const box = document.createElement('div'); box.className = 'ctlGroup';
    const h = document.createElement('h3'); h.textContent = g; box.append(h);
    for (const a of ACTIONS) {
      if (a.group !== g) continue;
      const row = document.createElement('div'); row.className = 'krow' + (K.isDefault(a.id) ? '' : ' changed');
      const nm = document.createElement('span'); nm.className = 'kname'; nm.textContent = a.label;
      row.append(nm);
      K.get(a.id).forEach((c, i) => {
        const waiting = cap && cap.id === a.id && cap.slot === i;
        const b = document.createElement('button');
        b.className = 'kb' + (c ? '' : ' empty') + (waiting ? ' wait' : '');
        b.textContent = waiting ? 'press a key' : c ? K.codeLabel(c) : i ? '+' : 'unbound';
        b.title = `${a.label}: ${i ? 'alternate' : 'primary'} key`;
        b.dataset.act = a.id; b.dataset.slot = i;
        b.addEventListener('click', () => { cap = { id: a.id, slot: i, label: a.label }; render(); msg(`press a key or mouse button for ${a.label} · Esc cancels · Backspace clears`); });
        row.append(b);
      });
      const r = document.createElement('button'); r.className = 'kreset'; r.textContent = '↺';
      r.title = `reset to default (${a.def.map(K.codeLabel).join(' / ')})`;
      r.disabled = K.isDefault(a.id);
      r.addEventListener('click', () => { const moved = K.reset(a.id); done(); msg(`${a.label}: back to ${K.labels(a.id)}${moved.map(movedText).join('')}`, moved.length > 0); });
      row.append(r);
      box.append(row);
    }
    list.append(box);
  }
  $('ctlSwap').checked = K.get('aim').includes('KeyE') && K.get('grapple').includes('Mouse2');
}
function done() { save(); render(); if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); }
function finish(code) {
  const { id, slot, label } = cap;
  cap = null;
  const moved = K.set(id, slot, code);
  done();
  msg(code ? `${label} → ${K.codeLabel(code)}${movedText(moved)}` : `${label}: ${slot ? 'alternate' : 'primary'} cleared`, !!moved);
}

function wire() {
  wired = true;
  // capture phase on window: while waiting for a key, nothing else (game, menu buttons, browser) sees it
  addEventListener('keydown', (e) => {
    if (!cap) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (e.repeat) return;
    swallowUp = e.code; // its keyup must not click the focused button either
    if (e.code === 'Escape') { cap = null; render(); msg('cancelled'); return; }
    if (e.code === 'Backspace' || e.code === 'Delete') { finish(null); return; }
    if (!e.code) { msg('that key has no code the game can read, try another', true); return; }
    finish(e.code);
  }, true);
  addEventListener('keyup', (e) => { if (swallowUp && e.code === swallowUp) { swallowUp = ''; e.preventDefault(); e.stopImmediatePropagation(); } }, true);
  addEventListener('mousedown', (e) => {
    if (!cap) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (e.button === 0) swallowClickUntil = performance.now() + 800; // the click that follows isn't a new "change this key" (only the left button makes one)
    finish('Mouse' + e.button);
  }, true);
  addEventListener('click', (e) => { if (performance.now() < swallowClickUntil) { swallowClickUntil = 0; e.preventDefault(); e.stopImmediatePropagation(); } }, true);
  $('ctlSwap').addEventListener('change', () => {
    const on = $('ctlSwap').checked;
    K.set('aim', 0, on ? 'KeyE' : 'Mouse2'); // aim takes grapple's key and grapple gets right click (the swap rule does the rest)
    done();
    msg(on ? 'right click grapples, E aims' : 'right click aims, E grapples');
  });
  $('ctlResetAll').addEventListener('click', () => {
    if (performance.now() > resetArm) { resetArm = performance.now() + 3000; msg('click RESET ALL again to put every key back to default', true); return; }
    resetArm = 0; cap = null; K.resetAll(); done(); msg('every key is back to default');
  });
}
