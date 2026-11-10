// OVERDUE scenes, Act I: "Please Take Your Item". Played in-engine by public/js/story/scene.js (TECH_PLAN §6).
//
// SCHEMA: SCENES[id] = {
//   kind     'cinematic' | 'panels' | 'flashback' | 'boss' | 'moment' | 'recap'   (DESIGN §8.1)
//   act, mission    where it plays (mission id)
//   len      seconds (cinematics stay under 120)
//   music    a music cue name (or null)
//   cast     { key: castId } the actors on set ('you' is always the player's real model)
//   notes    builder notes (optional; never shown)
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
      { t: 19, dir: "Behind him, a Gristle & Sons truck backs down the stairs on caterpillar tracks, and Timekeeping collectors with clipboards fan out." },
      { t: 22, dir: "Mr. Overtime stops at the bottom of the stairs. He takes out a clipboard. He checks his watch. He is exactly on time." },
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

  // ---- m06 TICKETS, PLEASE (docs/story/TRAIN.md). `notes` on a scene is for the builder (never shown).
  c6_mind_the_gap: {
    kind: "cinematic", act: 1, mission: "m06_tickets_please", len: 88, music: null,
    notes: "music: none until 61 s, then revenue_protection_theme: four hundred people humming one note",
    cast: { you: "change", jack: "pallet_jack", lumps: "lumps", gordo: "gordo", dale: "dale", auntie: "auntie", dumpling: "dumpling", rp: "revenue_protection" },
    tracks: [
      { t: 0, dir: "The service tunnel under the mall. A yellow maintenance loco the size of a van, a flatbed, a low open wagon. Dale in the cab with a flask. One headlamp. It lights about nine sleepers." },
      { t: 4, dir: "Jack kneels to Dumpling on the platform. Puts the hi-vis vest on him. It reaches the floor." },
      { t: 7, say: ["jack", "hold that for me. it's about three hundred grams. i'll want it back."] },
      { t: 10, dir: "Auntie, behind Dumpling, both hands on his shoulders. She looks at you. She doesn't say be careful. She has stopped saying it to people." },
      { t: 14, dir: "The train pulls out. The platform light gets small. Then it's a dot. Then the tunnel bends and it's gone." },
      { t: 19, say: ["lumps", "it's a lot of dark."] },
      { t: 21, say: ["gordo", "it's the same amount of dark as anywhere. there's just nothing in front of it."] },
      { t: 25, dir: "Jack sits on the back rail of the wagon with his legs hanging over the track, eating out of a pan. His boiler ticks as it cools. Your chest ticks. They're not in time and it bothers neither of you." },
      { t: 29, say: ["jack", "you kept the clock in, then. how's it sit?"] },
      { t: 32, say: ["jack", "first part's the worst one. you keep waiting to feel like someone else. *he eats.* then you've got nine and you can't remember which ones you came with."] },
      { t: 38, dir: "A second track swings in alongside. On it, standing in the dark, a commuter train: eight carriages, white, a ☺ on every door. Your headlamp slides down its windows. Every seat is empty. Every door is open. Coats on the hooks. A coffee on a table, grown over." },
      { t: 46, say: ["gordo", "*quiet* that's the last one out. new year's eve. it never got in."] },
      { t: 49, say: ["lumps", "where'd they all go?"] },
      { t: 51, dir: "Nobody answers. The dead train slides away behind you. Its last carriage has no back wall. The metal is bent outwards." },
      { t: 55, dir: "Jack has stopped eating. He is looking back down the tunnel, past the wagon's rail, at the tunnel lights: a string of weak bulbs running back the way you came." },
      { t: 58, dir: "The furthest one goes out." },
      { t: 59, dir: "Then the next one." },
      { t: 61, music: "revenue_protection_theme", dir: "Then they go out in order, towards you, quite fast. Under the sound of the train: breathing. A lot of it." },
      { t: 65, say: ["jack", "dale. faster."] },
      { t: 66, say: ["dale", "this is faster."] },
      { t: 68, dir: "Jack stands and his rig comes up with him: shins lock, stacks open, the forearm cocks. He turns to tell you to get behind him." },
      { t: 70, dir: "A black arm as thick as a lamp post comes out of the dark at the height of his belt, goes in under his ribs, and comes out through the boiler in his back. Red steam. It lifts him a metre off the deck. It is made of arms." },
      { t: 73, dir: "Jack looks down at it. He gets both hands on it. He breaks it. It takes him two tries." },
      { t: 76, dir: "He lands on his knees. The severed length of it is still through him. He stands up anyway." },
      { t: 78, say: ["jack", "that's... about two hundred kilo. *he breathes.* it's fine. it's just all at once."] },
      { t: 81, dir: "The last bulb before the wagon is still lit. Something white fills the tunnel behind it, wall to wall: a face. Two tall holes for eyes. Hands on the walls. On the roof. It hauls." },
      { t: 85, dir: "From behind the face, four hundred voices, not together:", say: ["rp", "tickets, please."] },
      { t: 87, boss: "revenue_protection_1" },
    ],
  },

  // the playable middle of the fight. the two prompts are `choice` tracks (the mission's `fire` and `take` choices, one
  // button each): the scene holds its timeline while one is open. times after 50 follow the player's press (TRAIN.md
  // writes them as +2, +4...): the absolute times here assume a press at 52 and are the builder's to retime
  mo_carry_the_bit_that_works: {
    kind: "moment", act: 1, mission: "m06_tickets_please", len: 70, music: null,
    notes: "playable, about 70 s, no music: the train, the breathing. Plays when phase 1 reaches its scripted end. The player keeps control of the camera and of one button.",
    cast: { you: "change", jack: "pallet_jack", lumps: "lumps", gordo: "gordo", rp: "revenue_protection" },
    tracks: [
      { t: 0, dir: "Jack's block fails. A Sweeper takes him across the chest and his armour goes: the collarbone weld, the shin locks, the stacks, all at once, the sound a rig makes when it's finished. He goes down against the fridge. THE GAP closes to 6 m and holds. Lumps and Gordo are on the Grabbers with a crowbar and a fire axe. They are losing." },
      { t: 5, dir: "You get to him. The arm is still through him. The boiler is split and what's coming out of it is not steam any more. Two Snatchers are walking down the walls towards him, in no hurry. They know which one of you has stopped." },
      { t: 9, say: ["jack", "light one. listen. i've done the sums."] },
      { t: 12, say: ["jack", "i'm two hundred and ten kilo and i'm not getting up. you can't carry me. he can't carry me, not with that arm."] },
      { t: 17, say: ["jack", "and that thing doesn't kill you. look at it. *behind the mask's rim, between the arms, faces.* it keeps you."] },
      { t: 22, say: ["jack", "i'm not going in there. i've got a boy at home holding my vest."] },
      { t: 26, dir: "He takes your right hand, the one in the cradle, and puts the heel of it on his own chest, left of the weld. He holds it there." },
      { t: 29, say: ["jack", "so you do it. then it's got nothing to keep."] },
      { t: 32, say: ["lumps", "*from the rail, not turning round* jack. no. sorry. no."] },
      { t: 35, say: ["jack", "ambrose. hold the rail. you're doing really well."] },
      { t: 38, dir: "He looks back at you. He's sweating. He's trying to do this properly." },
      { t: 40, say: ["jack", "and after. bev says the marrow's the only good thing in me. it's in the spine, low down, behind the boiler. it'll keep for a minute once i've stopped. take it. that gun'll run all day on it."] },
      { t: 47, say: ["jack", "don't carry me, light one. carry the bit that works."] },
      { t: 50, choice: "fire", dir: "The prompt appears: [FIRE]. Nothing else on the HUD. The game does not do it for you. The Snatchers are four metres away. If you wait, he says: PALLET JACK: go on. it's not heavy." },
      { t: 52, dir: "You fire. One bolt. It sticks. He breathes out. The cross comes, and it's small, and it's quick." },
      { t: 54, dir: "His hand comes off yours and stays open on the deck." },
      { t: 56, choice: "take", dir: "The prompt appears: [TAKE]. Your hand goes in through the split boiler, the same motion as the Heart Rip, slower. What comes out is a length of spine the colour of a traffic light, wet, and warm, and still making blood: it runs down your arm and into the cradle and all six barrels fill at once." },
      { t: 60, dir: "Your mannequin back opens along the seam. It goes in. No clinic, no chair, no Bev. The Blood Drive's ring starts to turn without you asking it to." },
      { t: 62, dir: "The Snatchers reach Jack. They pick him up. They turn him over. They put him down. There's nothing there for them." },
      { t: 64, dir: "Lumps has turned round. He is looking at you, and at your arm, and at Jack. It's the first time he's looked at you like you might be a thing." },
      { t: 66, say: ["gordo", "*hoarse* lumps. LUMPS. rail."] },
      { t: 67, dir: "The mask hauls. THE GAP reads 6 m. Your HP bar is full, and then past full, and it is not your colour." },
      { t: 68, title: "PENALTY FARE" },
    ],
  },

  c6b_terminus: {
    kind: "cinematic", act: 1, mission: "m06_tickets_please", len: 52, music: "auntie_theme_crayon",
    notes: "music: auntie_theme_crayon, one instrument",
    cast: { you: "change", lumps: "lumps", gordo: "gordo", dale: "dale", jack: "pallet_jack" },
    tracks: [
      { t: 0, dir: "The train coasts out onto a viaduct over The Commute. Sunset: the same one Lumps cries at. Dead traffic to the horizon, every windscreen red." },
      { t: 4, dir: "Behind you, the tunnel mouth. The broken face lying on the track in the last of the light. Behind it, in the dark, what's left: heaps, steaming, a few hands still opening and closing on nothing. Nothing follows. A click. One." },
      { t: 9, dir: "Dale stops the train. He doesn't get out of the cab. He has both hands on the brake and his forehead on his hands." },
      { t: 13, dir: "Gordo sits down where he's standing. He has the fire axe across his knees and can't open his fingers." },
      { t: 17, dir: "Lumps kneels by Jack. He closes the split in the boiler with his hands, the way you'd close a coat on someone. He gets his good arm under Jack's back and his bad arm under his knees." },
      { t: 23, say: ["gordo", "lumps. he's two hundred kilo. your arm."] },
      { t: 26, say: ["lumps", "two hundred and ten."] },
      { t: 28, dir: "He lifts him. The stitches in his forearm go, one at a time. He stands up." },
      { t: 32, dir: "He walks past you to the front of the flatbed and stops. He doesn't look at you." },
      { t: 35, say: ["lumps", "he asked you."] },
      { t: 37, say: ["lumps", "i know he asked you. i heard him."] },
      { t: 40, dir: "A long time." },
      { t: 43, say: ["lumps", "...is it warm? the bit of him."] },
      { t: 45, dir: "It is. Your arm is ticking over on its own, barrels filling and emptying, slow, like breathing." },
      { t: 48, say: ["lumps", "okay. *he nods.* okay. sorry."] },
      { t: 50, dir: "He carries Jack to the front of the train so he can see where it's going." },
      { t: 52, dir: "→ p5b_employee_4417, then END OF ACT I" },
    ],
  },

  // (moved from the end of m05 to the end of m06 when the train went in: END OF ACT I is still its last card)
  p5b_employee_4417: {
    kind: "panels", act: 1, mission: "m06_tickets_please", len: 18, music: "overtime_theme_low",
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
