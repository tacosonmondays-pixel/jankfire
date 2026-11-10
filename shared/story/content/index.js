// OVERDUE story content: everything the quest / dialogue / scene engine loads, in one object.
//   import { CONTENT } from '../shared/story/content/index.js'
// Every file is plain data (ES modules exporting plain objects), documented at its top:
//   world.js (districts, factions, locations, the condition/action grammar) · cast_*.js (the cast bible)
//   missions/act*.js (main story) · side/*.js (side questlines) · scenes_act*.js (cutscenes) · endings.js
//   bosses.js · implants.js (incl. organ cores and secret bio upgrades) · loot.js (brands, modifiers, legendaries,
//   loot tables) · collectibles.js · activities.js · items.js (key/quest items) · flags.js (every story flag)
//   mechanics.js (the mechanics bible: every game mechanic and how the story uses it) · boss_fights.js (merged into bosses.js)
// validate.js checks that every id and reference resolves; tests/story/content.test.mjs runs it.
// Side quests use the mission schema with kind: 'side' (and optional `parts`: [{ id, title, if, steps, do }] for
// multi-part questlines that unlock over time).

import { DISTRICTS, FACTIONS, LOCATIONS, STANDING, ENDINGS, SPEAKERS } from './world.js';
import { CAST_MAIN } from './cast_main.js';
import { CAST_DISTRICTS } from './cast_districts.js';
import { MISSIONS_ACT1 } from './missions/act1.js';
import { MISSIONS_ACT2 } from './missions/act2.js';
import { MISSIONS_ACT3 } from './missions/act3.js';
import { MISSIONS_ACT4 } from './missions/act4.js';
import { MISSIONS_ACT5 } from './missions/act5.js';
import { SCENES_ACT1 } from './scenes_act1.js';
import { SCENES_ACT2 } from './scenes_act2.js';
import { SCENES_ACT3 } from './scenes_act3.js';
import { SCENES_ACT4 } from './scenes_act4.js';
import { SCENES_ACT5 } from './scenes_act5.js';
import { SIDE_BOTTOM } from './side/bottom.js';
import { SIDE_GUT } from './side/gut.js';
import { SIDE_PINSTRIPE } from './side/pinstripe.js';
import { SIDE_CHECKOUT } from './side/checkout.js';
import { SIDE_NUMBERWORKS } from './side/numberworks.js';
import { SIDE_CHROMEGRISTLE } from './side/chromegristle.js';
import { SIDE_EVERGREEN } from './side/evergreen.js';
import { SIDE_LATES } from './side/lates.js';
import { SIDE_MARGINS } from './side/margins.js';
import { SIDE_CORPHILL } from './side/corphill.js';
import { SIDE_COMMUTE } from './side/commute.js';
import { ENDING_SCRIPTS } from './endings.js';
import { BOSSES } from './bosses.js';
import { IMPLANTS } from './implants.js';
import { BRANDS, MODIFIERS, LEGENDARIES, LOOT_TABLES } from './loot.js';
import { COLLECTIBLE_SETS, COLLECTIBLES } from './collectibles.js';
import { ACTIVITIES } from './activities.js';
import { ITEMS } from './items.js';
import { FLAGS } from './flags.js';
import { MECHANICS, GRAPPLE } from './mechanics.js';

export const CAST = { ...CAST_MAIN, ...CAST_DISTRICTS };
export const MISSIONS = { ...MISSIONS_ACT1, ...MISSIONS_ACT2, ...MISSIONS_ACT3, ...MISSIONS_ACT4, ...MISSIONS_ACT5 };
export const SCENES = { ...SCENES_ACT1, ...SCENES_ACT2, ...SCENES_ACT3, ...SCENES_ACT4, ...SCENES_ACT5 };
export const SIDE = { ...SIDE_BOTTOM, ...SIDE_GUT, ...SIDE_PINSTRIPE, ...SIDE_CHECKOUT, ...SIDE_NUMBERWORKS, ...SIDE_CHROMEGRISTLE, ...SIDE_EVERGREEN, ...SIDE_LATES, ...SIDE_MARGINS, ...SIDE_CORPHILL, ...SIDE_COMMUTE };
// (two missions share n 6: m06_tickets_please closes Act I, m06_option_c opens Act II. the act breaks the tie)
export const MISSION_ORDER = Object.keys(MISSIONS).sort((a, b) => MISSIONS[a].n - MISSIONS[b].n || MISSIONS[a].act - MISSIONS[b].act);

export const CONTENT = {
  DISTRICTS, FACTIONS, LOCATIONS, STANDING, ENDINGS, SPEAKERS,
  CAST, MISSIONS, MISSION_ORDER, SCENES, SIDE, ENDING_SCRIPTS, BOSSES, IMPLANTS,
  BRANDS, MODIFIERS, LEGENDARIES, LOOT_TABLES, COLLECTIBLE_SETS, COLLECTIBLES, ACTIVITIES, ITEMS, FLAGS, MECHANICS, GRAPPLE,
};
