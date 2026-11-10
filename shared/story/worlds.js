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
