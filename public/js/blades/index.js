// Knife and sword models, one file each, built with kit.js to real-world proportions.
// knife + katana are base weapons; knife_* are knife skins (shared/cosmetics.js COSMETICS.model).
import * as combat from './combat.js';
import * as kitchen from './kitchen.js';
import * as bowie from './bowie.js';
import * as cleaver from './cleaver.js';
import * as switchblade from './switch.js';
import * as karambit from './karambit.js';
import * as butterfly from './butterfly.js';
import * as katana from './katana.js';
import * as shirasaya from './shirasaya.js';
import * as bokken from './bokken.js';

export const BLADES = {
  knife: combat, katana,
  knife_kitchen: kitchen, knife_bowie: bowie, knife_cleaver: cleaver, knife_switch: switchblade, knife_karambit: karambit, knife_butterfly: butterfly,
  katana_shirasaya: shirasaya, katana_bokken: bokken,
};
