// Where the cast stands in the slice city (the world lane's half of NPC placement). The story's cast data says which
// place someone calls home ('bottom:gym'); this says the exact spot and facing in the streets, so nobody spawns in a
// wall, on a roof or behind a stall. STAGE moves people for a mission step (Lumps waits on Peristalsis Avenue for the
// escort, then stands by his mum at the wall). public/js/story/boot.js reads both; tests/story/act1world.test.mjs
// checks every spot is standing room you can walk to.
// face: yaw (0 looks north, -z; PI looks south, +z; PI/2 looks west; -PI/2 looks east)
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
  dot: { p: [-87, 40, -139.9], face: S }, // IN the digester wall, up to her chest
  mina: { p: [-80.5, 40, -139.9], face: S }, // a few faces along from Dot
  sister_agenda: { p: [-264, 40, -199], face: S }, // just inside the Choir Lung's door
  bev: { p: [-84.3, 36.12, -7.2], face: S }, // in her back room, between the chair and the door
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
  'm01_return_to_sender.swing': { call: 'GRAPPLE UP!', how: 'aim at the yellow ring on the roofs and hold <b>{grapple}</b>. let go at the top' },
  'm01_return_to_sender.line': { call: 'RIDE IT HOME', how: 'walk to the end of the roof, <b>{use}</b> on the washing line, hang on' },
};
