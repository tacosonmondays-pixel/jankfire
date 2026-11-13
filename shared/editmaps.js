// PLAY HERE WITH BOTS (the map editor, owner only): one fresh copy of one map with the shipped edits and the owner's
// edits on it, under its own id (ed_<map>_<n>), for one private bots room. The server builds it from a checked ticket
// (server/editplay.js); the owner's client builds the same copy from the room's cfg.edit. Never listed anywhere (not in
// MAP_ORDER, not enumerable), and dropped when the room closes.
import { MAPS, MAP_BUILDERS, unstick } from './map.js';
import { applyEdits, validEdits, saneMap, boxSigs } from './mapedit.js';
import { EDITS } from './mapedits/index.js';

export const MAX_EDIT_OPS = 2000;
export const isEditId = (id) => typeof id === 'string' && /^ed_[a-z0-9_]{1,40}_\d{1,9}$/.test(id);
export function okEdit(e) {
  return !!(e && typeof e === 'object' && typeof e.base === 'string' && Object.hasOwn(MAP_BUILDERS, e.base) && Array.isArray(e.ops) && e.ops.length <= MAX_EDIT_OPS && validEdits({ map: e.base, ops: e.ops }));
}
// build + register. returns the id, or null (a bad edit, an unknown map)
export function buildEdited(id, e) {
  if (!isEditId(id) || !okEdit(e)) return null;
  if (Object.hasOwn(MAPS, id)) return id;
  const def = MAP_BUILDERS[e.base]();
  if (EDITS[e.base]) applyEdits(def, EDITS[e.base]); // (the map as it ships, then yours on top)
  const keep = boxSigs(def);
  applyEdits(def, { ops: e.ops });
  if (!saneMap(def, keep)) return null; // (moves and sizes stacked op after op: every box must still be a sane size, in sane places)
  unstick(def.boxes, [...def.spawns, ...(def.teamSpawns ? [...def.teamSpawns.att, ...def.teamSpawns.def] : [])]);
  // (no sd / base link: a mode change must never swap the copy for the unedited map)
  def.name = (def.name || e.base) + ' (your edits)';
  Object.defineProperty(MAPS, id, { value: def, configurable: true, enumerable: false, writable: true });
  return id;
}
export function dropEdited(id) { if (isEditId(id) && Object.hasOwn(MAPS, id)) delete MAPS[id]; }
