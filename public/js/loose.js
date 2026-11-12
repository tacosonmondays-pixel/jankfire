// Loose pieces on this map (remote.js's gibs, zmlimbs.js's limbs and hats): the rule is shared/loose.js
import { BOXES } from '/shared/map.js';
import { looseStep as step, floorUnder as under } from '/shared/loose.js';
export const floorUnder = (x, y, z) => under(BOXES, x, y, z);
export const looseStep = (o, p, dt, rest, bounce, drag) => step(BOXES, o, p, dt, rest, bounce, drag);
