// OVERDUE enemies: the people you fight who aren't bosses. The combat referee (systems lane: the story worker's Room)
// spawns these as bots and reads hp / weapon / look / tags from here; quests count them by id in kill goals
// ({ type: 'kill', who: '<id>' | 'any', n }), and the story host's `spawn:<id>@<zone>*<n>` action sends them in.
//
// SCHEMA: ENEMIES[id] = {
//   name      what the kill feed calls them
//   faction   world.js FACTIONS id (standing, Late Fees, who they hate)
//   hp        one player's worth (the referee scales for co-op)
//   weapon    a shared/weapons.js id they carry
//   look      looks.js id (a hand-made look) or { body: 'mannequin' | 'normal' | 'puppet', desc } for a seeded one
//   tags      for the referee and Late Fees: 'corp', 'civilian', 'important', 'melee', 'ranged', 'swarm', 'heavy', 'flying'
//   does      one plain sentence: how they fight
//   line      what they shout (lowercase, in the game's voice)
// }
// ADDS maps each boss fight's adds (boss_fights.js, by name) to an enemy id.

export const ENEMIES = {
  corp_temp: { name: "☺ CORP TEMP", faction: "corp", hp: 80, weapon: "pistol", look: "mannequin", tags: ["corp", "ranged"],
    does: "Walks at you smiling and shoots politely. Takes cover behind other temps.", line: "please hold. your call is important." },
  collector: { name: "TIMEKEEPING COLLECTOR", faction: "corp", hp: 120, weapon: "nailgun", look: "mannequin", tags: ["corp", "ranged"],
    does: "Clipboard in one hand, nail gun in the other. Loads people into trucks between shots.", line: "you're on the list. everyone's on the list." },
  timekeeping_drone: { name: "TIMEKEEPING DRONE", faction: "corp", hp: 50, weapon: "smg", look: { body: "mannequin", desc: "a wall clock with propellers" }, tags: ["corp", "flying", "swarm"],
    does: "A flying wall clock that strafes you and beeps on the hour.", line: "BEEP. you are 4 minutes late." },
  hr_tactical: { name: "HR TACTICAL", faction: "corp", hp: 160, weapon: "shotgun", look: "mannequin", tags: ["corp", "heavy"],
    does: "Riot shields made of policy binders. Pushes in pairs.", line: "this is a safe space. get on the floor." },
  recalled_security: { name: "RECALLED SECURITY", faction: "corp", hp: 140, weapon: "ar", look: "mannequin", tags: ["corp", "ranged"],
    does: "Old guards loaded from the backups, still on the shift they died on.", line: "badge. badge please. badge." },
  spare_overtime: { name: "SPARE OVERTIME", faction: "corp", hp: 900, weapon: "nailgun", look: "overtime", tags: ["corp", "heavy", "important"],
    does: "A half-printed copy of Mr. Overtime, slow and stapling, two sizes too small.", line: "this will only take a... this will only take a..." },
  intern: { name: "UNPAID INTERN", faction: "unpaid", hp: 70, weapon: "slapper", look: { body: "normal", desc: "office-chair armour, a lanyard, a laptop for a shield" }, tags: ["melee", "swarm"],
    does: "Charges in a pack, swinging whatever's to hand. Leaves when the pizza runs out.", line: "this is great experience!" },
  war_rig: { name: "UNPAID WAR-RIG", faction: "unpaid", hp: 600, weapon: "minigun", look: { body: "normal", desc: "a cubicle on wheels, a minigun on the partition" }, tags: ["heavy", "ranged"],
    does: "A cubicle bolted to a shopping trolley. Rams cars, then sprays.", line: "WE'RE DISRUPTING." },
  looper: { name: "LOOPER", faction: "loopers", hp: 90, weapon: "revolver", look: { body: "normal", desc: "dressed for a Tuesday sixty-one years ago" }, tags: ["ranged"],
    does: "Knows where you'll be because you were there last loop. Fires there first.", line: "you always go left. you always go left." },
  docent: { name: "MUSEUM DOCENT", faction: "corp", hp: 100, weapon: "scales", look: "mannequin", tags: ["corp", "melee"],
    does: "Guards the Punctuality Museum. Shushes, then swings the exhibit.", line: "please don't touch the past." },
  choir_singer: { name: "GUT CHOIR", faction: "gristle", hp: 90, weapon: "blower", look: { body: "puppet", desc: "a robe, a stretched smile, a huge mouth" }, tags: ["ranged"],
    does: "Sings in harmony. The harmony knocks you over.", line: "ahhhhhhh (in tune)" },
  stomach_dog: { name: "STOMACH-DOG", faction: "gristle", hp: 110, weapon: "claw", look: { body: "puppet", desc: "a dog made mostly of stomach" }, tags: ["melee"],
    does: "Bounds at you, bites, digests. Good boy.", line: "*gurgle*" },
  goon: { name: "PINSTRIPED GOON", faction: "family", hp: 130, weapon: "akimbo", look: { body: "normal", desc: "a pinstripe suit, a policy folder" }, tags: ["ranged"],
    does: "Shoots from behind cars, then offers you a quote.", line: "you're covered. you're so covered." },
  shopper: { name: "FOREVER SHOPPER", faction: "bigvalue", hp: 60, weapon: "cart", look: { body: "normal", desc: "a trolley, a list, no face left" }, tags: ["civilian", "melee", "swarm"],
    does: "Rams you with a trolley. There are always more of them.", line: "is this on offer?" },
  mall_security: { name: "MALL SECURITY", faction: "bigvalue", hp: 150, weapon: "taser", look: "mannequin", tags: ["heavy", "melee"],
    does: "Tasers and a whistle. Calls for backup on a walkie that's a banana.", line: "sir. SIR." },
  rounding_crew: { name: "ROUNDING CREW", faction: "remainder", hp: 120, weapon: "calc", look: { body: "normal", desc: "a hard hat with a price gun on it" }, tags: ["ranged"],
    does: "Rounds your health down to the nearest ten.", line: "call it an even number." },
  remainder: { name: "REMAINDER", faction: "remainders", hp: 80, weapon: "bread", look: { body: "puppet", desc: "a number nobody wanted stamped on the forehead" }, tags: ["melee", "swarm"],
    does: "Shows up in odd numbers and won't divide.", line: "we're still here." },
  hoa_militia: { name: "HOA MILITIA", faction: "hoa", hp: 140, weapon: "dmr", look: { body: "normal", desc: "a polo shirt, a lawn flag, a scope" }, tags: ["ranged"],
    does: "Snipes from the lawns. Fines you for the footprints.", line: "that's a violation." },
  mannequin_family: { name: "MANNEQUIN FAMILY", faction: "hoa", hp: 70, weapon: "slipper", look: "mannequin", tags: ["melee", "swarm"],
    does: "A whole family of display mannequins, moving when you don't look.", line: "(the sound of a smile)" },
  mascot: { name: "FERAL MASCOT", faction: "fundept", hp: 110, weapon: "rigpunch", look: { body: "puppet", desc: "a huge foam head, a too-small body" }, tags: ["melee"],
    does: "Hugs too hard. Fun is mandatory.", line: "HUG TIME!" },
  survey_agent: { name: "SURVEY AGENT", faction: "vacancy", hp: 100, weapon: "laser", look: { body: "normal", desc: "a theodolite for a head" }, tags: ["ranged"],
    does: "Measures you, then marks you for demolition.", line: "this plot is vacant. you're on it." },
};

// boss_fights.js adds (by name) -> enemy ids (the ones with no foot soldier stay with the boss's own lane)
export const ADDS = {
  "Timekeeping collectors": "collector", "Unpaid war-rigs": "war_rig", "Loopers": "looper", "spare Overtimes": "spare_overtime",
  "museum docents": "docent", "the Gut Choir": "choir_singer", "stomach-dogs": "stomach_dog", "pinstriped goons": "goon",
  "Forever Shoppers": "shopper", "Mall Security": "mall_security", "rounding crews": "rounding_crew", "the Remainders": "remainder",
  "mannequin families": "mannequin_family", "the HOA militia": "hoa_militia", "Timekeeping drones": "timekeeping_drone",
  "HR Tactical": "hr_tactical", "recalled security": "recalled_security", "interns": "intern", "feral mascots": "mascot", "survey agents": "survey_agent",
};
