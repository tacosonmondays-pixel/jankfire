// The story's streamed world, as plain data the sim can use the way it uses shared/story/testmap.js TEST (id, spawn,
// yaw, killY, terminal): pure, no map building, safe in the sim worker and on the server.
import { CITIES } from './plan.js';
import { SLICE } from './slice.js';

export const STORY_SLICE = {
  id: 'story_slice', name: 'Greater Jankburg (the slice)', city: 'slice', killY: -40,
  spawn: CITIES.slice.spawn.slice(), yaw: Math.PI, // out of the Machine's tray, facing the depot's open front
  terminal: { p: [-189, 8.15, 182.2], r: 3.2 }, // the Machine (SLICE.lostFound): use within r metres opens the sims
  bounds: [SLICE.x0, SLICE.z0, SLICE.x1, SLICE.z1],
};
