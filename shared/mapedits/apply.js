// Puts the shipped map edits (shared/mapedits/index.js) onto the built maps, once, before anything else reads them.
// Imported first thing by the server (server.js) and the client (main.js, editor.js), so collision, bots, hits and the
// drawing all get the same edited map. Replay is deterministic (shared/mapedit.js); an edit whose thing is gone (the map
// was remodelled since) is skipped and reported, never applied to something else.
import { MAPS, unstick } from '../map.js';
import { applyEdits, validEdits } from '../mapedit.js';
import { EDITS } from './index.js';

// maps built in their own files register themselves when imported: only pulled in when there's an edit for them
const LATE = { school: '../zmschool.js', hospital: '../zmhospital.js', jankburg: '../jankburg.js', battleisland: '../battleisland.js' };
export const EDIT_REPORT = {}; // map id -> { ops, stale } (tests, the editor)
for (const id of Object.keys(EDITS)) {
  try {
    if (!Object.hasOwn(MAPS, id) && Object.hasOwn(LATE, id)) await import(LATE[id]);
    const def = MAPS[id], e = EDITS[id];
    if (!def || def.stream || !validEdits(e) || e.map !== id) { EDIT_REPORT[id] = { ops: 0, stale: -1 }; console.warn('map edits: skipped', id); continue; }
    const { stale } = applyEdits(def, e);
    unstick(def.boxes, [...def.spawns, ...(def.teamSpawns ? [...def.teamSpawns.att, ...def.teamSpawns.def] : [])]); // (an edit may have put a box on a spawn)
    EDIT_REPORT[id] = { ops: e.ops.length, stale: stale.length };
    if (stale.length) console.warn(`map edits: ${stale.length} of ${e.ops.length} on ${id} no longer fit the map (skipped)`);
  } catch (err) { EDIT_REPORT[id] = { ops: 0, stale: -1 }; console.error('map edits failed on', id, err); } // (a bad edit never stops the game)
}
