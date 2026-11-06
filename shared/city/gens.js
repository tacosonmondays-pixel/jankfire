// district generators by key (CITIES[*].districts[*].gen). add new districts here
import { blocks } from './blocks.js';
import { bottom } from './bottom.js';
import { gut, border, edges } from './gut.js';
import { commute } from './commute.js';
import { horizon } from './horizon.js';
import './slice.js'; // registers the slice city
export const GENS = { blocks, bottom, gut, border, edges, commute, horizon };
