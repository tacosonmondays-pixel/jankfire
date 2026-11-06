// The /skip vote's callout: SKIP VOTE · Duck Rain · 2/3 · type /skip in chat · 24s. The server runs the vote
// (server/skip.js): this only shows it, and calls out when the match gets skipped.
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { organic } from './organic.js';

let box = null, endsAt = 0, timer = 0;
function ensure() {
  if (box) return box;
  box = document.createElement('div');
  box.id = 'skipBox'; box.className = 'hidden';
  box.innerHTML = '<b class="t">SKIP VOTE</b><span class="mode"></span><b class="n"></b><span class="how">type <kbd>/skip</kbd> in chat</span><span class="left"></span>';
  document.getElementById('hud').append(box);
  organic(box, { tex: false, bits: false, rim: 4, pad: 6, shadow: [6, 6], wob: 1, lumps: 2, lumpA: 2 });
  return box;
}
function tick() {
  const s = Math.max(0, Math.ceil((endsAt - performance.now()) / 1000));
  box.querySelector('.left').textContent = `${s}s`;
  if (s <= 0) { clearInterval(timer); timer = 0; }
}
// m: { name, n, need, left } while it's on, { end: 1, ok, name, quiet } when it's over, null to hide
export function skipVote(m) {
  const b = ensure();
  if (!m || m.end) {
    b.classList.add('hidden'); clearInterval(timer); timer = 0;
    if (m && m.ok) { hud.msg(`SKIPPED: ${String(m.name || '').toUpperCase()}`, 2.4, 'brag'); sfx.gavel(); }
    else if (m && !m.quiet) { hud.msg('SKIP VOTE FAILED', 1.6); sfx.error(); }
    return;
  }
  const fresh = b.classList.contains('hidden');
  b.classList.remove('hidden');
  b.querySelector('.mode').textContent = m.name || '';
  b.querySelector('.n').textContent = `${m.n}/${m.need}`;
  endsAt = performance.now() + (m.left || 0);
  tick();
  clearInterval(timer); timer = setInterval(tick, 250);
  b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump');
  if (fresh) sfx.gavel(); else sfx.pop();
}
export function skipReset() { if (box) box.classList.add('hidden'); clearInterval(timer); timer = 0; }
