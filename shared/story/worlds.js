// the worlds a story run can be in, by map id: the streamed city slice (the Bottom, WP1/WP2: shared/city/storyworld.js)
// and the test lot (shared/story/testmap.js, for tests: ?storytest=1). same shape for both: { id, spawn, yaw, killY,
// terminal (the Machine), locker, clinic }. pure: safe in the sim worker and on the server.
import { TEST } from './testmap.js';
import { TRAIN } from './train.js'; // the last two cars in the Under-Hill Loop (m06's boss arena)
import { STORY_SLICE } from '../city/storyworld.js';

// the slice has no Locker or clinic of its own yet: they stand by the Machine at the Lost & Found until the world
// lane builds them (a world's own locker / clinic wins). on the open floor in front of it, either side (checked by e2e)
const near = (p, dx, dz) => [p[0] + dx, p[1], p[2] + dz];
const SLICE = { ...STORY_SLICE, locker: STORY_SLICE.locker || { p: near(STORY_SLICE.terminal.p, 4.5, 4), r: 2.6 }, clinic: STORY_SLICE.clinic || { p: near(STORY_SLICE.terminal.p, -4.5, 4), r: 2.8 }, stand: true };
export const WORLDS = { [SLICE.id]: SLICE, [TEST.id]: TEST, [TRAIN.id]: TRAIN };
export const DEFAULT_WORLD = SLICE.id;
export const worldOf = (id) => WORLDS[id] || WORLDS[DEFAULT_WORLD];
// moving a run between worlds (story/main.js travel / travelBack). pure: they return the save to start the run from
const okAt = (at) => !!at && typeof at === 'object' && typeof at.map === 'string' && Object.hasOwn(WORLDS, at.map) && Array.isArray(at.p) && at.p.length === 3 && at.p.every(Number.isFinite);
// to another world's spawn. where you left from goes into the save (data.travelFrom), kept if one is already there
export function travelTo(save, map) {
  if (!save || !Object.hasOwn(WORLDS, map)) return null;
  const W = WORLDS[map], d = save.data || {};
  const from = okAt(d.travelFrom) ? d.travelFrom : okAt(save.at) && save.at.map !== map ? { map: save.at.map, p: save.at.p.slice(), yaw: Number.isFinite(save.at.yaw) ? save.at.yaw : 0 } : null;
  return { ...save, at: { map, p: W.spawn.slice(), yaw: W.yaw || 0, fresh: true }, data: { ...d, ...(from ? { travelFrom: from } : {}) } };
}
// back to where the last travelTo left from; with nothing (or nonsense) there, the default world's spawn
export function travelHome(save) {
  if (!save) return null;
  const data = { ...(save.data || {}) }, from = okAt(data.travelFrom) ? data.travelFrom : null, W = WORLDS[DEFAULT_WORLD];
  delete data.travelFrom;
  return { ...save, data, at: from ? { map: from.map, p: from.p.slice(), yaw: Number.isFinite(from.yaw) ? from.yaw : 0 } : { map: DEFAULT_WORLD, p: W.spawn.slice(), yaw: W.yaw || 0, fresh: true } };
}
