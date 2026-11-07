// OVERDUE scenes, Act I: "Please Take Your Item". Played in-engine by public/js/story/scene.js (TECH_PLAN §6).
//
// SCHEMA: SCENES[id] = {
//   kind     'cinematic' | 'panels' | 'flashback' | 'boss' | 'moment' | 'recap'   (DESIGN §8.1)
//   act, mission    where it plays (mission id)
//   len      seconds (cinematics stay under 120)
//   music    a music cue name (or null)
//   cast     { key: castId } the actors on set ('you' is always the player's real model)
//   tracks   a time-ordered list. Every track has `t` (seconds) and any of:
//            cam: { shot | path, target?, dur?, fov? }   shots: wide, closeup, overShoulder, lowAngle, highAngle, dolly, whip, pov, insert
//            say: [castKey or speaker, text]      a speech bubble with the babble voice and jaw flap
//            dir: "stage direction"               what happens on screen (for the scene builder; never shown)
//            panel: { n, cap?, say?: [[who, text]], sfx? }   comic-panel layout (kind 'panels'): n = panel number
//            sfx, fx, music, shake, hitstop, impact ('red'), fade ('in'|'out'|'white'), letterbox (true|false)
//            title: "BIG SLAM TEXT"              a title card or mission card
//            boss: bossId                         boss intro card (BOSS kind) then gameplay
//            choice: choiceId                     hand over to a mission choice (mission.choices)
//            if: condition                        only play this track when the condition holds
// }
// Speaker keys in `say` are keys of `cast` or ids from world.js SPEAKERS.

export const SCENES_ACT1 = {
  c1_please_take_your_item: {
    kind: "cinematic", act: 1, mission: "m01_return_to_sender", len: 95, music: "overdue_main_theme",
    cast: { you: "change", dale: "dale", auntie: "auntie" },
    tracks: [
      { t: 0, dir: "It starts as a normal JANKFIRE match on the Suburb map: the real HUD, the kill feed, the timer at 0:04. The player gets the last kill." },
      { t: 2, title: "TRAINING COMPLETE", sfx: "match_win" },
      { t: 4, dir: "The bots don't respawn. They stand where they died, get up slowly, and turn to look at the player. All of them. The kill feed keeps scrolling the same line: CALE R. 4417 has left the match. CALE R. 4417 has left the match." },
      { t: 9, cam: { shot: "dolly", target: "you", dur: 6, fov: 60 }, dir: "The camera pulls back from the player. The sky of the Suburb map has a reflection on it, like glass. The camera goes through the glass." },
      { t: 15, dir: "We're outside a vending machine. The whole Suburb match is inside its window, tiny, still running. The machine is the original ☺ vending machine, glowing, humming, in a ruined returns depot. Rain through the roof." },
      { t: 20, cam: { path: "c1_hill_pullback", dur: 30, fov: 50 }, music: "overdue_main_theme_swell", dir: "The camera keeps pulling back: out of the Lost & Found, over the stacked pastel houses of the Bottom, up the rubble hill. Washing lines. Wok dishes. A kid on a basket scooter looks up." },
      { t: 30, title: "JANKFIRE: OVERDUE", dir: "The title slams over the hill." },
      { t: 34, dir: "Still pulling back and up: the Gut breathing in its valley, ribcage arches over glowing pink streets; the Lates' dead clock tower; giant fallen digits glowing green in the ash; dead traffic on the ring road; and at the very top, the ☺ Spire, white and lit, the only lit building in the dark." },
      { t: 50, dir: "Every public clock on Corp Hill ticks in sync. The camera stops on the Spire's Master Clock: 23:58." },
      { t: 53, cam: { shot: "whip", dur: 1 }, sfx: "whoosh_down", dir: "Whip pan: we fall back down the hill, through the depot roof, to the Machine." },
      { t: 56, cam: { shot: "closeup", target: "dale" }, dir: "Dale, eighty-three, with his hand over a big round button on the Machine's service panel. It has a sticker on it: DISPENSE (ENGINEER ONLY). The sticker is sixty years old. He has never pressed it. Auntie Spreadsheet is behind him with a torch and a notebook." },
      { t: 60, say: ["auntie", "dale. you've been looking at that button for twenty minutes."] },
      { t: 64, say: ["dale", "it's been looking at me for sixty years."] },
      { t: 68, dir: "Inside the glass, the tiny Suburb match is glitching: one mannequin keeps walking off the edge of the map, and the map keeps putting it back." },
      { t: 71, say: ["dale", "that one won't stay in. every match. it walks off the edge. it wants out."] },
      { t: 75, say: ["auntie", "then let it out."] },
      { t: 77, dir: "Dale looks at her for a long moment. Something unspoken. He presses the button." },
      { t: 79, sfx: "beep", say: ["machine", "BEEP."] },
      { t: 80, sfx: "clunk", shake: 0.5, say: ["machine", "CLUNK."] },
      { t: 81, cam: { shot: "insert", target: "you" }, dir: "A mannequin, folded impossibly small, drops into the dispensing tray and unfolds, joint by joint, with a wrong knee." },
      { t: 85, say: ["machine", "please take your item."] },
      { t: 87, say: ["auntie", "it's never given anything."] },
      { t: 90, say: ["dale", "it gave change."] },
      { t: 93, cam: { shot: "pov", target: "you" }, fade: "in", dir: "Blend to the player's first-person view from inside the tray, looking up at the two of them. Control." },
    ],
  },

  p1b_final_quarter: {
    kind: "panels", act: 1, mission: "m01_return_to_sender", len: 40, music: "auntie_theme_crayon",
    cast: { auntie: "auntie" },
    tracks: [
      { t: 0, dir: "Auntie Spreadsheet's crayon captions, in her handwriting, over halftone panels. She's telling the story across a soup table." },
      { t: 1, panel: { n: 1, cap: "first they bought the politicians. then the parties. then the countries. ☺ CORP bought ours at an auction. it was the only bidder.", sfx: "SOLD" }, dir: "A politician at a podium with a ☺ price tag dangling off his collar." },
      { t: 7, panel: { n: 2, cap: "then they merged. every company was a division, every country belonged to one, and every quarter the bottom division got cut. so they went to war over market share." }, dir: "A war map shaped like a sales chart, armies in division colours: pink, yellow, red, orange, black." },
      { t: 14, panel: { n: 3, cap: "the last day of the last quarter. every division was going to miss its number. at 16:59 six boards signed something called option c.", sfx: "SCRITCH" }, dir: "Six pens over six signature lines, six logos on the letterheads. A clock: 16:59." },
      { t: 21, panel: { n: 4, cap: "at 17:30 they launched everything at once.", sfx: "DONG" }, dir: "Three images in one panel: a street frozen mid-step (the Lates), a battlefield standing back up (Regrowth), a city going black." },
      { t: 27, panel: { n: 5, cap: "the long dark. billions dead. the companies waited it out in their towers. the spire had the only lit windows for thirty years." }, dir: "Ash falling on a dark city. One tower lit." },
      { t: 33, panel: { n: 6, cap: "and we built houses on the hill. the hill breathes. you get used to it." }, dir: "Survivors stacking pastel shipping-container houses on a hill of rubble and bone. A kid sleeping on a washing line." },
      { t: 38, say: ["auntie", "that was the end of the world. sixty-one years ago. you hungry?"] },
    ],
  },

  p2_sauce_run: {
    kind: "panels", act: 1, mission: "m02_sauce_run", len: 14, music: null,
    cast: { lumps: "lumps", gordo: "gordo", sharon: "sharon" },
    tracks: [
      { t: 0, panel: { n: 1, say: [["sharon", "soup. for medicine. gristle and sons at the gut border. same as every week."]], sfx: "SLOSH" }, dir: "Sharon holds up a huge red pot." },
      { t: 4, panel: { n: 2, say: [["lumps", "i'll hold the pot. you hold the key."]] }, dir: "Lumps holds up a car key on a fluffy keyring." },
      { t: 8, panel: { n: 3, say: [["gordo", "he means steal a car. and watch out for interns."]], sfx: "JANGLE" }, dir: "Wee Gordo, deadpan, the key isn't for any car they own." },
      { t: 12, title: "MISSION: SAUCE RUN" },
    ],
  },

  c3_its_breathing: {
    kind: "cinematic", act: 1, mission: "m03_somethings_digesting", len: 45, music: "gut_choir_chord",
    cast: { you: "change", lumps: "lumps", dot: "dot", agenda: "sister_agenda" },
    tracks: [
      { t: 0, cam: { shot: "dolly", target: "you", dur: 8 }, dir: "Driving into the Gut for the first time. The tarmac goes soft, then pink, then ribbed. The tyres squelch. The headlights catch veins in the kerb." },
      { t: 6, say: ["lumps", "don't touch the walls. they like it."] },
      { t: 9, dir: "A rib arch rises over the avenue like a cathedral roof. Lungs inflate between the buildings and the whole street breathes in. A launderette with a tongue for a door." },
      { t: 15, sfx: "choir_chord_swell", dir: "The Gut Choir, robed, puppet faces stretched into permanent smiles, lining the street, turn their faces to the car all at once." },
      { t: 20, say: ["choir", "*one long chord, held, on the word* welcome."] },
      { t: 24, cam: { shot: "closeup", target: "dot" }, dir: "Among the choir, grown half into the wall of a building, are faces that aren't singing: normal faces, Off-Spec faces, people from the Bottom. A small round woman in curlers looks straight at the car." },
      { t: 29, say: ["dot", "ambrose?"] },
      { t: 31, cam: { shot: "closeup", target: "lumps" }, dir: "Lumps freezes. He's heard her say it before, every Sunday. It still hits him." },
      { t: 34, say: ["lumps", "...hi mum."] },
      { t: 37, say: ["dot", "you've brought a friend. a plastic friend. lovely. have you eaten?"] },
      { t: 41, say: ["lumps", "*to you, quiet* park the car. we'll walk from here."] },
    ],
  },

  c4_clocking_in: {
    kind: "cinematic", act: 1, mission: "m04_clocking_in", len: 62, music: "overtime_theme",
    cast: { you: "change", ot: "overtime", lumps: "lumps", auntie: "auntie", mina: "mina", dumpling: "dumpling", gordo: "gordo" },
    tracks: [
      { t: 0, cam: { path: "c4_sunset", dur: 7, fov: 50 }, dir: "The Bottom at sunset. Kids on scooters. Washing on the lines. Lumps at the sunset wall, crying a little. Auntie on a step, doing the books in crayon." },
      { t: 3, say: ["lumps", "*sniff* it's the sunset. it does this."] },
      { t: 7, fx: "clocksStop", sfx: "silence_then_tick", dir: "Every clock in the settlement stops at once: the kitchen clocks, the wristwatches, the broken district clock over the Lost & Found, the egg timer on Sharon's pot. Silence. Then a single loud tick, from up the hill." },
      { t: 11, say: ["auntie", "*not looking up* oh no."] },
      { t: 13, cam: { shot: "lowAngle", target: "ot", dur: 5 }, shake: 0.4, dir: "Huge polished brogues step down the Long Stairs. Each step cracks a step. Ticking. A grey suit stretched over pistons. A punch-clock where a heart should be." },
      { t: 13.2, anim: ["ot", "ot_stalk", true] },
      { t: 19, dir: "Behind him, a Gristle & Sons truck backs down the stairs on caterpillar tracks, and Timekeeping collectors with clipboards fan out." },
      { t: 22, dir: "Mr. Overtime stops at the bottom of the stairs. He takes out a clipboard. He checks his watch. He is exactly on time." },
      { t: 22.5, anim: ["ot", "ot_idle", true] },
      { t: 25, say: ["ot", "good evening. the bottom. two hundred and forty-four quarters of back pay. i'm here to collect."] },
      { t: 31, say: ["auntie", "for a job none of us had."] },
      { t: 34, say: ["ot", "you're all absent. you've been absent for a very long time. this will only take a minute. it will take exactly a minute."] },
      { t: 39, dir: "The collectors start loading people into the truck: an old man, Dumpling's dad (Dumpling screams), a woman with a baby (put back: the baby's not on the list, the woman is). An old woman with a grey braid and climbing gloves is pushed up the ramp." },
      { t: 45, cam: { shot: "closeup", target: "mina" }, dir: "The old woman with the braid sees you. She stops on the ramp. She stares at your face, your barcode, your knee." },
      { t: 48, say: ["mina", "...rory?"] },
      { t: 50, dir: "The doors slam on her." },
      { t: 51, cam: { shot: "wide" }, dir: "Lumps walks out and stands in front of the truck. He's bigger than it." },
      { t: 54, say: ["lumps", "sorry. no."] },
      { t: 56, say: ["ot", "you're obstructing a scheduled vehicle. that's against policy."] },
      { t: 58, anim: ["ot", "staple_shot"], hitstop: 0.12, impact: "red", dir: "Overtime fires a staple the size of a crowbar through Lumps' forearm into the truck's bumper. Lumps doesn't scream. He looks at it, then at you." },
      { t: 61, boss: "overtime_1" },
    ],
  },

  mo_heart_rip: {
    kind: "moment", act: 1, mission: "m04_clocking_in", len: 3, music: null,
    cast: { you: "change", ot: "overtime" },
    tracks: [
      { t: 0, hitstop: 0.3, cam: { shot: "closeup", target: "ot" }, dir: "Slow motion. Your hand goes into the cracked punch-clock in Overtime's chest and pulls out a piece of it: a cog, a spring, a bit of clock face, wet." },
      { t: 1.5, sfx: "tick_wet", dir: "It's warm. It ticks in your hand." },
      { t: 2.5, title: "HEART RIP", impact: "red" },
    ],
  },

  c5_second_stomach: {
    kind: "cinematic", act: 1, mission: "m05_second_stomach", len: 48, music: "bev_clinic_drip",
    cast: { you: "change", auntie: "auntie", bev: "bev" },
    tracks: [
      { t: 0, cam: { shot: "wide" }, dir: "A back-room clinic on the Gut border behind a butcher's curtain. A dentist's chair. A bucket. Bev, four arms, headlamp on, scrubbing two hands while the other two light a cigarette." },
      { t: 4, cam: { shot: "closeup", target: "auntie" }, dir: "Auntie holds the punch-clock core in a tea towel. It ticks through the cloth." },
      { t: 7, say: ["auntie", "this is a terrible idea."] },
      { t: 9, say: ["bev", "they're all terrible ideas. this one works."] },
      { t: 12, say: ["bev", "chassis, lie back. you're plastic, so this won't hurt. that's a lie. i say it to everyone."] },
      { t: 17, dir: "Bev opens your mannequin chest like a cupboard. Auntie looks away. Then makes herself look back." },
      { t: 21, say: ["auntie", "will they still be... them? after?"] },
      { t: 24, say: ["bev", "one part, yes. ten parts, ask me again. the more of you that isn't you, the less of you there is. that's not medicine, that's maths."] },
      { t: 30, fade: "out", sfx: "tick", dir: "Black. A single TICK." },
      { t: 32, fade: "white", dir: "A flash, 0.8 s, washed out like old video: a marble lobby, a revolving door, a pair of scuffed trainers running across the floor, your trainers. A clock on the wall: 17:29." },
      { t: 34, fade: "in", cam: { shot: "pov", target: "you" }, dir: "You wake in the chair. A clock face glows in your chest. It ticks." },
      { t: 37, say: ["bev", "welcome back. how many fingers?"] },
      { t: 40, say: ["auntie", "*quiet* what did you see?"] },
      { t: 43, dir: "Auntie watches your face as if she already knows the answer." },
    ],
  },

  p5b_employee_4417: {
    kind: "panels", act: 1, mission: "m05_second_stomach", len: 18, music: "overtime_theme_low",
    cast: { ot: "overtime" },
    tracks: [
      { t: 0, panel: { n: 1, cap: "meanwhile, at ☺ CORP...", sfx: "TICK" }, dir: "A spotless office on Corp Hill. Mr. Overtime, sitting at a desk far too small for him, with a fresh bandage of steel plate over his chest." },
      { t: 4, panel: { n: 2 }, dir: "He looks at a security still on his monitor: you, climbing out of the Machine's tray, taken from Dale's terminal. Your barcode, enlarged." },
      { t: 8, panel: { n: 3, say: [["ot", "CALE, R. employee 4417. deleted."]] }, dir: "The screen reads: CALE, R. 4417 · STATUS: TERMINATED 17:29:41 · NEXT APPOINTMENT: MEETING 17:30 (M)." },
      { t: 12, panel: { n: 4, say: [["ot", "late for a meeting at 17:30."]] }, dir: "His hand, steady, on the screen." },
      { t: 15, panel: { n: 5, sfx: "CLICK" }, dir: "He takes out a new clipboard and writes your name at the top. Under REASON he writes: absent." },
      { t: 17, title: "END OF ACT I" },
    ],
  },
};
