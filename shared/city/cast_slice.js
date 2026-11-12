// Where the cast stands in the slice city (the world lane's half of NPC placement). The story's cast data says which
// place someone calls home ('bottom:gym'); this says the exact spot and facing in the streets, so nobody spawns in a
// wall, on a roof or behind a stall. STAGE moves people for a mission step (Lumps waits on Peristalsis Avenue for the
// escort, then stands by his mum at the wall). public/js/story/boot.js reads both; tests/story/act1world.test.mjs
// checks every spot is standing room you can walk to.
// face: yaw (0 looks north, -z; PI looks south, +z; PI/2 looks west; -PI/2 looks east)
import { BEV } from './act1set.js';
const N = 0, S = Math.PI, W = Math.PI / 2, E = -Math.PI / 2;

export const NPC_SPOTS = {
  // the Lost & Found (the hub): Dale by his Machine, Auntie at the barrel where dinner is, Gordo at the returns counter,
  // Dumpling by the lost-property shelves (the tutorial's bins)
  dale: { p: [-185.6, 8.15, 189.6], face: 2.6 },
  auntie: { p: [-180.4, 8.15, 198.2], face: E },
  gordo: { p: [-202, 8.15, 194.6], face: S },
  dumpling: { p: [-175.2, 8.15, 190.5], face: W },
  lumps: { p: [24, 16.2, 140], face: S }, // his gym (the npc.lumps mark)
  sharon: { p: [-104.6, 0, 236.2], face: N }, // in front of her soup stall, looking up the hill at you coming down
  dot: { p: [-87, 40, -139.5], face: S }, // IN the digester wall, up to her chest, in her niche (act1set.js DIGESTER: the model's built round this spot; 0.4 m out from the office face, so her back clears it and she stands on the street, not on the lung pad buried in the wall behind her)
  mina: { p: [-83.5, 40, -139.62], face: S, look: 'mina_wall', if: 'flag.fate.mina.gut' }, // a few faces along from Dot, in the wall up to her waist (look: the walled model), her back to the wall's niche (act1set.js DIGESTER); inside the gap in Peristalsis Avenue's tube (x -93..-81) so you can see her. if: only while her fate is 'gut' (m04's truck sets it; freed in act III clears it)
  sister_agenda: { p: [-264, 40, -199], face: S }, // just inside the Choir Lung's door
  bev: { p: [-83.25, 36.02, -9.4], face: S }, // in her surgery, beside the dentist's chair (act1set.js BEV), facing the curtain
};

// [quest, step] -> { npc: spot } while that step is the one being played (the tracked objective)
export const STAGE = [
  ['m03_somethings_digesting', 'walk', { lumps: { p: [-114, 40, -138.4], face: E } }], // waits on the avenue: follow him east to the wall
  ['m03_somethings_digesting', 'dot', { lumps: { p: [-90.5, 40, -137.6], face: N } }], // by his mum
  ['m04_clocking_in', 'sunset__at', { lumps: { p: [-199, 32, 4.5], face: N } }], // waiting at the Sunset Wall (the arrive step: overdue.js ARRIVE)
  ['m04_clocking_in', 'sunset', { lumps: { p: [-199, 32, 4.5], face: N } }],
];

// the spot an npc should stand at now. objs: the engine's objectives (S.quests.objectives())
export function npcSpot(id, objs) {
  for (const o of objs || []) for (const [q, st, who] of STAGE) if (o.quest === q && o.step === st && who[id]) return who[id];
  return NPC_SPOTS[id] || null;
}

// a callout when a step starts, where the world teaches a move (the m01 tutorial). {grapple} / {use}: the player's keys
export const HINTS = {
  'm01_return_to_sender.swing': { call: 'GRAPPLE UP!', how: 'aim at the yellow ring over the roofs, hold <b>{grapple}</b>, let go at the top and push forward' },
  'm01_return_to_sender.line': { call: 'RIDE IT HOME', how: 'walk to the end of the roof, <b>{use}</b> on the washing line, hang on' },
};

// people sitting about (set dressing: no lines, not the cast's roster): Bev's waiting room is always full, like a
// barber's (m05: a woman holding her own jaw in a tea towel, a man with the price still chalked on his new arm, Pallet
// Jack with a tube in his back and a bucket under it). seat: [x, y, z] hip height; if: a story condition (who's still
// alive to be waiting). look: a cast look id, or hint: a seeded stand-in (looks.js generic)
export const SITTERS = [
  { id: 'wait_jaw', seat: BEV.seats[0], face: BEV.seatFace, hint: { body: 'normal', desc: 'a woman in a headscarf holding her own jaw in a tea towel' } },
  { id: 'wait_chalk', seat: BEV.seats[1], face: BEV.seatFace, hint: { body: 'normal', desc: 'a big man in a vest, the price still chalked on his new arm' } },
  { id: 'wait_jack', seat: BEV.seats[2], face: BEV.seatFace, look: 'pallet_jack', if: '!flag.fate.pallet_jack.dead' },
];

// the Gut Choir in the Choir Lung (public/js/story/choir.js): set dressing like the sitters, no lines. two rows of
// stalls facing each other across the aisle up from the door (the lung's ring is centred x -268, z -218; its door is
// to the south), so walking in you see them side-on, and every head turns to you at once. look: choir (tall) / choir_b
export const CHOIR = [
  { look: 'choir', p: [-270.7, 40, -209.4], face: E }, { look: 'choir_b', p: [-270.7, 40, -210.7], face: E }, { look: 'choir', p: [-270.7, 40, -212.0], face: E },
  { look: 'choir_b', p: [-265.3, 40, -210.0], face: W }, { look: 'choir', p: [-265.3, 40, -211.35], face: W },
];
