// district generators by key (CITIES[*].districts[*].gen). add new districts here
import { blocks } from './blocks.js';
import { bottom } from './bottom.js';
import { gut, border, edges } from './gut.js';
import { commute } from './commute.js';
import { horizon } from './horizon.js';
import './slice.js'; // registers the slice city
import { gtaInto } from './roads.js';
// the slice's city-wide pass: the void edges, then the road net / pavements / parking (roads.js)
const slicepost = (B, C, r, city) => { edges(B, C, r, city); gtaInto(B); };
export const GENS = { blocks, bottom, gut, border, edges, commute, horizon, slicepost };
