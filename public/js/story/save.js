// OVERDUE save slot interface for the story engine. The systems lane (claude/overdue-systems, WP0) owns the real save
// slot + /api/story/*; until that lands this keeps the story's part in localStorage behind the same two calls, so the
// swap is one file. The engine only stores its own keys (shared/story/state.js toSave) under data.story... merged at
// the top level of the slot's data, as TECH_PLAN §7 lays out.
const KEY = (slot) => `jfStorySave${slot | 0}`;
let backend = null; // set by WP0: { load(slot) -> Promise<data|null>, save(slot, data) -> Promise<bool> }

export function useSaveBackend(b) { backend = b; }
export async function loadSlot(slot = 0) {
  if (backend) return backend.load(slot);
  try { const s = localStorage.getItem(KEY(slot)); return s ? JSON.parse(s) : null; } catch { return null; }
}
export async function saveSlot(slot = 0, data) {
  if (backend) return backend.save(slot, data);
  try { const s = JSON.stringify(data); if (s.length > 64 * 1024) return false; localStorage.setItem(KEY(slot), s); return true; } catch { return false; }
}
export function clearSlot(slot = 0) { try { localStorage.removeItem(KEY(slot)); } catch { /* private mode */ } }
