// the worlds a story run can be in, by map id: the streamed city slice (the Bottom, WP1/WP2: shared/city/storyworld.js)
// and the test lot (shared/story/testmap.js, for tests: ?storytest=1). same shape for both: { id, spawn, yaw, killY,
// terminal (the Machine), locker, clinic }. pure: safe in the sim worker and on the server.
import { TEST } from './testmap.js';
import { STORY_SLICE } from '../city/storyworld.js';

// the slice has no Locker or clinic of its own yet: they stand by the Machine at the Lost & Found until the world
// lane builds them (a world's own locker / clinic wins)
const near = (p, dx, dz) => [p[0] + dx, p[1], p[2] + dz];
const SLICE = { ...STORY_SLICE, locker: STORY_SLICE.locker || { p: near(STORY_SLICE.terminal.p, 3.5, 0), r: 2.6 }, clinic: STORY_SLICE.clinic || { p: near(STORY_SLICE.terminal.p, -4, 0), r: 2.8 }, stand: true };
export const WORLDS = { [SLICE.id]: SLICE, [TEST.id]: TEST };
export const DEFAULT_WORLD = SLICE.id;
export const worldOf = (id) => WORLDS[id] || WORLDS[DEFAULT_WORLD];
