// The story's streamed maps, as entries in shared/map.js MAPS (client only: never in MAP_ORDER, no menu lists them).
// A streamed map has no boxes of its own: `stream` names the city, and world.js hands it to the streamer (ingame.js).
// The story shell calls registerStoryMaps(MAPS) at start-up; the sim says which map you're on (welcome cfg.map).
import { CITIES } from '/shared/city/plan.js';
import { STORY_SLICE } from '/shared/city/storyworld.js';

export { STORY_SLICE };

export function registerStoryMaps(MAPS) {
  if (MAPS[STORY_SLICE.id]) return;
  const d = CITIES.slice.districts.find((q) => q.id === 'bottom');
  MAPS[STORY_SLICE.id] = {
    name: STORY_SLICE.name, size: 'story', boxes: [], deco: [], stream: 'slice', killY: STORY_SLICE.killY, floorY: -4,
    bounds: STORY_SLICE.bounds, sky: d.sky, fogNear: d.fogNear, fogFar: d.fogFar, spawns: [STORY_SLICE.spawn.slice()], story: true, night: true,
  };
}
