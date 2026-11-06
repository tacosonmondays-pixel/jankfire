// The story's streamed world, as plain data the sim can use the way it uses shared/story/testmap.js TEST (id, spawn,
// yaw, killY, terminal): pure, no map building, safe in the sim worker and on the server.
import { CITIES } from './plan.js';
import { SLICE } from './slice.js';

export const STORY_SLICE = {
  id: 'story_slice', name: 'Greater Jankburg (the slice)', city: 'slice', killY: -40,
  spawn: CITIES.slice.spawn.slice(), yaw: Math.PI, // out of the Machine's tray, facing the depot's open front
  // the Machine stands at the back of the Lost & Found (its box ends at z 183.6): the terminal spot is the floor in
  // front of its face, so a teleport 1.6 m further out is still clear of it. the Locker (the stash, ground floor right
  // of the Machine) and the clinic (Bev's chair under the mezzanine) are real spots with props (bottom.js lostFound)
  terminal: { p: [-189, 8.15, 185.2], r: 3.4 },
  locker: { p: [-181, 8.15, 184.4], r: 2.6 },
  clinic: { p: [-207, 8.15, 186.5], r: 2.8 },
  bounds: [SLICE.x0, SLICE.z0, SLICE.x1, SLICE.z1],
};
