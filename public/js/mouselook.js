// Mouse look under pointer lock, shared by the game (main.js) and the map editor (editor/editor.js) so they can't drift
// apart: raw mouse (no OS acceleration) when the browser has it, and the two Chrome glitches dropped. Without these the
// camera snaps: right after locking the first events are garbage, and now and then Chrome reports one giant fake jump
// (often the wrong way) when you move far or fast.
export function lockPointer(el) {
  try {
    const p = el.requestPointerLock({ unadjustedMovement: true });
    if (p && p.catch) p.catch(() => { try { const q = el.requestPointerLock(); if (q && q.catch) q.catch(() => {}); } catch { /* no lock */ } });
  } catch { /* headless or denied */ }
}
// one per canvas: locked() when the lock starts, take(mx, my) per event -> false = drop it
export function lookFilter() {
  let lockedAt = 0, avg = 8;
  return {
    locked(now = performance.now()) { lockedAt = now; },
    take(mx, my, now = performance.now()) {
      const mag = Math.abs(mx) + Math.abs(my);
      if (now - lockedAt < 120) return false; // first events after locking are often garbage
      if (mag > 90 && mag > avg * 6) { avg = Math.max(avg, mag / 6) * 0.5 + avg * 0.5; return false; } // one event way bigger than how you've been moving
      avg = avg * 0.85 + mag * 0.15;
      return true;
    },
  };
}
