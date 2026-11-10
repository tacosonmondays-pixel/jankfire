# OVERDUE, Act I climax: TICKETS, PLEASE (the train and the mask)

**Status: APPROVED by the owner (2026-11-10). Decisions are in section 8. Being built: data first, then models, then the fight.**
The owner's idea and sketch (2026-11-10): a train, your crew, a crewmate with a built-in Overdrive Rig who you kill at
his own request and whose bio material you take, a Blood Cross minigun, and a mask the size of the tunnel that drags
itself after you on black arms. Tone: serious, gory, dark. Characters die.

Concept sheet: `docs/story/train/revenue_protection_sheet.png` (a blockout in the game's renderer, not the final model).

This page is written to slot into the existing script: it obeys [CANON.md](script/CANON.md) and the Act I reveal order
(you learn *what* ☺ CORP does to people, not yet *why*). Once approved it goes into `shared/story/content/` as mission 6
of Act I, and `ACT_1.md`, `BOSSES.md`, `CAST.md` and `IMPLANTS.md` are regenerated from it.

---

## 1. Where it sits

| # | mission | what changes |
|---|---|---|
| 4 | CLOCKING IN | unchanged (first Overtime fight). The demo goal still ends here |
| 5 | SECOND STOMACH | unchanged, except panel scene `p5b_employee_4417` loses its last line (END OF ACT I) |
| **6** | **TICKETS, PLEASE** (new) | the train, the crewmate's death, the mask. **END OF ACT I** moves to the end of this |

**Why a train.** After m04 the Gut wall has grown shut behind the truck: nine people are inside, Mina among them, and
there is no way in on foot. Wee Gordo has the other way: the **Under-Hill Loop**, the commuter line that runs under
the whole hill, through the Gut's basement and round to every district. Dale has spent eleven years fixing a
maintenance loco in the service tunnel under the mall. Nobody uses the Loop, because trains that go in don't come out.
The Bottom's word for it is "the tunnel eats". Everyone assumes cave-ins.

**What winning gets you.** The train. From Act II it is the Bottom's fast travel between districts (it replaces
walking The Commute for anywhere you've already been), and it is the route into the Gut that m20 THE MISSING uses.
That is the reason the crew pays for it.

**What it costs.** Pallet Jack.

---

## 2. New cast: PALLET JACK

`pallet_jack` · Jack Marsh, 41 · the Bottom's delivery man · body: cyborg (Off-Spec, Bev-built)

- **Look.** A wide, cheerful man built like the thing he's named after. Bev has been putting an Overdrive Rig *into*
  him for fifteen years, one part a year, paid for in soup: piston shins, a boiler the size of a beer keg sunk into
  his lower back with two thruster stacks, a rocket-punch right forearm with the skin worn off the knuckles, a welded
  steel collarbone. No cockpit and no suit: where a rig has armour plates, he has scar tissue over plate. A hi-vis
  vest with MARSH DELIVERIES in marker pen. A hand truck he doesn't need.
- **What powers it.** Not fuel. Bev replaced his bone marrow with a Gristle & Sons strain that makes blood four times
  too fast, and the rig runs on the pressure. He eats eleven meals a day. Sharon keeps a tab.
- **Speech.** Rates everything by weight. Unhurried. Calls Change "light one". Never complains about a load.
  - "you're about forty kilos, light one. lightest friend i've got."
  - "that pot's ninety. the soup's another sixty. the worry's free."
  - "bev says i've got ten years left in the knees. she said that ten years ago."
  - "it's not heavy. it's just all at once."
- **Ties to the cast we have.**
  - Lumps' gym partner and the reason the side quest LEG DAY exists: Lumps' "big one" (the fridge-carrying rig) is his
    copy of Jack, built on the outside because Lumps wouldn't let Bev cut him.
  - Dumpling's uncle. Dumpling's dad was one of the nine taken in C4, so Jack has had Dumpling for exactly one night.
  - Bev built him and is fond of him in a way she'd bill you for mentioning.
- **So the death lands, he has to be around first.** Small additions to missions already written (no cutscene is
  re-recorded, these are lines and background placement):
  - m01: he carries the Machine's tray, with you in it, up the down escalator. First line of his you hear: the weight.
  - m02: he lifts Sharon's pot into the car with one hand and tells Lumps his squat form is "a bit sad".
  - m04 aftermath: he comes back from a delivery up the Long Stairs to find nine gone. He picks Dumpling up off the
    floor from under the table and says nothing at all.
  - m05: in Bev's waiting room, getting his boiler bled. Bev: "you're next, jack. you're always next."

---

## 3. The weapon: BLOOD DRIVE (the Blood Cross as a minigun)

The Blood Cross already exists: you shoot blood out of your fingertip, every shot costs 12 HP, the bolt sticks, a
cross bursts out of them, a kill pays the blood back. The Blood Drive is that, six times over, on a motor.

- **The loaner.** Jack's old training frame, the one he wore before the parts went inside: a spine brace, a shoulder
  yoke and a right-arm cradle. Bev's addition: six glass syringe barrels in a ring around your forearm, each plumbed
  to a fingertip and the heel of your hand, on a belt-drive off a washing machine. It is a basic Overdrive Rig with
  everything but the arm taken off. Mannequin fingers were made to come off and go back on.
- **How it shoots.** Hold fire: the ring spins up over 0.8 s, then 14 bolts a second. Small bolts (18 damage), each
  one sticks. Every sixth bolt in the same target blooms a blood cross (the existing burst and pop).
- **What it costs.** 2 HP a bolt. That is 28 HP a second: on your own blood you get about three seconds before you're
  dying. A severed arm or a kill pays blood back. This is on purpose. Before Jack, the gun is a thing you can't afford.
- **After Jack** (section 5): it's free while the ring is spinning, and crosses chain to anything within 3 m.
- **Sound and look.** A dentist's drill winding up into a wet sewing machine. Tracer colour is the Blood Cross red
  (`#ff1f3d`). The barrels fill and empty in turn so you can read your own HP off your arm.
- **After the mission** it stays as OVERDUE's heavy weapon: found on the train's rear car, carried like a streak.

---

## 4. The boss: REVENUE PROTECTION

Boss card: **REVENUE PROTECTION · TICKETS, PLEASE**

**What you see.** A round mask that fills the tunnel wall to wall, nine metres across, coming up the track behind the
train. White enamel, chipped. Two tall oval eye holes with nothing in them. No mouth. Long black arms come out from
behind its rim, flat against the tunnel walls and roof, and it moves by grabbing the walls and hauling: reach, grip,
drag. The rim scrapes sparks off the brickwork all the way round. It doesn't roar. It breathes, and under the
breathing, from somewhere behind the face, a lot of people are saying "tickets, please" slightly out of time.

**What it is (the designer's truth; the player doesn't get all of this in Act I).**
- The mask is the ☺: the fallen company sign off the front of Hill Central station, a nine-metre enamel disc bolted
  together from twelve plates. The smile was painted on and has worn off. The two eye holes are the sign's old
  lamp housings.
- Behind it is the 17:32. The last commuter train of the Final Quarter was in this tunnel at 17:30 with four hundred
  people on it. They burned. Gristle & Sons' first Regrowth trial raised them, and it raised them as one thing: a plug
  of fused commuters that fills the tunnel like a cork, charred black, still in lanyards. The arms are their arms,
  braided together a dozen at a time into ropes twelve metres long, ending in hands made of hands.
- At the middle of it is the one who was checking tickets when it happened: the Inspector, cap fused to his head,
  still holding the punch. He is the only part of it that knows what it's for.
- ☺ CORP found it, bolted the sign to its front, and left it in the Loop. It keeps people off the line for free.
- **Act I reveal rules:** you *see* the lanyards and the faces. You *suspect* they were passengers. *Withheld:* that
  this is what Regrowth was for (Act III, the Gristle page), and that the Gut is the same failure at a larger size.

**Design notes.** Original design: it is a railway sign and a rail disaster, built from real references (enamel
station roundels, a tunnelling machine's segmented shield, charred timber, lanyards). It is not a spirit in a mask and
it has no body under the face, only more of itself. The eyes are two ovals to match the owner's sketch.

### The arena
The last two cars of a short train: a flatbed (crates, a chained-down fridge, the hand truck) and a low open wagon
behind it. The train moves; the tunnel scrolls. The boss holds a distance behind you shown on the HUD as **THE GAP**
(starts at 30 m). Arms that get a grip on the train close it. At 0 m it has you.

### Arms (all phases)
Each arm has a glowing wrist joint (a knot of lanyards and ID cards). That's the weak point: sever it and the hand
drops onto the track and the stump whips back.

| arm | what it does | answer |
|---|---|---|
| **Grabber** | walks along the wall, grips the wagon's rail. While it holds, THE GAP closes 1 m/s | shoot the wrist. A severed Grabber gives blood back |
| **Snatcher** | goes for a crewmate and lifts them. 6 s before it pulls them in | shoot the wrist. They drop back on the deck, hurt |
| **Sweeper** | flat along the deck, wall to wall, knee height or head height | jump or slide. Jack blocks one for you in phase 1 |
| **Brakeman** | reaches past the train and rips up track ahead, or drops a signal gantry | Dale shouts the side. Shoot it before it gets a grip, or brace |

### Phase 1: TICKETS, PLEASE
- Jack fights at the back rail in full rig: rocket punches on Grabbers, blocks Sweepers, thrusters to get back on
  when one throws him. He is already hurt (see the scene) and it shows: his boiler vents red steam, his punches slow
  down, his block gets shorter. He's a health bar you can't heal.
- You have the Blood Drive and not enough blood. Gordo throws you blood bags (Sharon's soup bags, relabelled) on a
  timer; Lumps, one arm still stitched from the staple, hauls crates into cover and pulls Snatchers' victims back.
- The mask shrugs bolts off. Sever four arms inside ten seconds and it flinches: the eye housings swing open for a
  moment and you can put bolts *into* it. That is the only damage it takes in this phase.
- Phase 1 is not winnable. At 60% the scripted beat happens: Jack's armour breaks. On a rig that means the rig is
  done. On Jack it means Jack is.

### The middle: `mo_carry_the_bit_that_works` (section 5)

### Phase 2: PENALTY FARE
You have Jack's marrow. The Blood Drive is free while it spins. Now the mask breaks, in three stages:
1. **Hairline.** Sustained fire on a plate crazes it, then it falls away and smashes on the track (each plate is a
   real piece of geometry: twelve of them, the hole stays). Under the first lost plates: packed black bodies, a hand
   flat against the inside like a face at a window.
2. **The left eye.** The left lamp housing blows out. Behind it, a cluster of real eyes, all looking at you. It
   starts throwing lost property out of the hole: briefcases, umbrellas, a pushchair. The voices get clearer:
   "is this seat taken", "i'm going to be late", "seventeen thirty-two", a child asking how many stops.
3. **The smile.** The bottom plates crack along one curved line, left to right. For a second the ☺ has its smile
   back. Then the lower third of the mask drops off and the crack is a mouth: a wall of mouths, and arms come out of
   *that* too, two at a time, faster.
- Snatchers now come in pairs. If one takes Gordo or Lumps all the way in, they are not killed (they're needed in
  Acts II to IV) but they come back out of it changed: a scar the rest of the game remembers, and a line in Act II.

### Phase 3: END OF THE LINE
- The mask is hanging off one bolt, swinging, half a face. Everything behind it is in the open: four hundred people
  in one piece, the lanyards, the faces moving, and in the middle the Inspector in his cap, punching a ticket that
  isn't there, over and over. He is the crit spot.
- It stops hauling politely and lunges. First lunge bites the open wagon in half: Lumps pulls the coupling pin, the
  arena is now one car. Daylight is a dot ahead of you. Dale: "ninety seconds. it doesn't come outside. i think. i
  think it doesn't come outside."
- Arms come from every side. Sever, cross, sever. Every cross that blooms inside it lights the tunnel red from within
  and you see the outline of everyone in there.
- **The finish.** With the Inspector's bar empty: hold fire. The ring overspins, all six barrels at once, and one
  blood cross grows out of the middle of it until it touches the tunnel on all four sides. **BLOOD CROSSED.** The
  mask's last bolt goes. The face falls forward flat onto the track and the train leaves the tunnel into a red
  evening on The Commute.
- The cross is what stops it. The thing behind the face comes apart along the cross's four arms: the braids
  unravel, the ropes of arms let go of the walls one hand at a time, and the plug that filled the tunnel slumps into
  four heaps across the track, steaming. The chase is over. Nothing is hauling any more.
- The last thing you see in the tunnel mouth: in the middle of the wreck the Inspector, on his own now, the size of a
  man. He lifts his punch, and clicks it once.
- It is broken apart, not gone. The pieces are still in the Loop and they were grown to grow back. (Owner: it can
  come back later. Act III, when you take the Loop into the Gut for the nine, is the obvious place.)

### Failure
THE GAP at 0 m: the hands close over the camera, one at a time. Death line: "fare evaded. briefly."

---

## 5. The script

Format matches `ACT_1.md`. Times in seconds.

### 6. TICKETS, PLEASE `m06_tickets_please`
_The only other way into the Gut is the commuter line under the hill. Nobody takes it, because the tunnel eats. Four of you go in. The thing that follows you out is wearing the company's face._

**Where:** The Lost & Found (THE BOTTOM), The Service Tunnel (THE BOTTOM), The Under-Hill Loop (THE COMMUTE), The Tunnel Mouth (THE COMMUTE)
**Who:** WEE GORDO, LUMPS, PALLET JACK, DALE, BEV, AUNTIE SPREADSHEET, DUMPLING, REVENUE PROTECTION
**Giver:** WEE GORDO · **Needs:** m05_second_stomach

**Mechanic hook:** a boss you fight from the back of a moving train with a gun that fires your own blood; the fight is unwinnable until you take a dead friend's marrow _(uses: blood cross, overdrive rig, bio-implants, slide)_

**Beats**
- Gordo's plan, on the back of a soup label: the Loop goes under the Gut. Dale has a loco. Jack has a spare frame.
- Bev fits you with the Blood Drive. Jack says goodbye to Dumpling like it's a delivery.
- The ride in: the dark, the banter, and on the next track a dead commuter train, every seat empty, every door open.
- The lights go out behind you, one at a time. Something takes Jack through the back before anyone sees what it is.
- Boss: REVENUE PROTECTION, phase 1. Jack holds the rail until his armour breaks.
- Jack asks you to kill him before it gets him, and to take his marrow. You do it yourself. Lumps can't.
- Phases 2 and 3: the mask breaks, the thing behind it, daylight.
- The Commute at dusk. Lumps carries Jack off the train. Nobody talks. END OF ACT I.

**The mystery**
- _learn:_ There is a line under the hill and now it's yours. Something made of people lives in it, and it wears a ☺ CORP sign. A part taken from a friend works the same as a part taken from an enemy.
- _suspect:_ They were passengers. Someone put that face on them. Whatever grew the Gut grew this.
- _withheld:_ Regrowth, and what the dead were for (Act III). That it grows back, and that the Inspector can be talked to (Act III).

**Objectives**
1. meet gordo at the lost & found · talk `the_loop`
2. get fitted · talk `loaner`
3. board the train
4. _(scene)_ · scene `c6_mind_the_gap`
5. keep it off the train · **boss: REVENUE PROTECTION** (phase 1)
6. _(scene, playable)_ · scene `mo_carry_the_bit_that_works`
7. break its face · **boss: REVENUE PROTECTION** (phases 2 and 3)
8. _(scene)_ · scene `c6b_terminus`
9. _(scene)_ · scene `p5b_employee_4417` (moved here)

#### Talk: `the_loop` (with WEE GORDO)
- **[start]**
  - _The Lost & Found, early. Nine names on the wall in crayon. Gordo has a soup label flattened on the table with a line drawn round a hill._
  - **WEE GORDO:** the wall's shut. grown over. i went and looked. it's like a scar.
  - **WEE GORDO:** so we don't go through the wall. we go under it. there's a railway under this whole hill. goes under the gut, comes up on the commute, goes round again.
  - **AUNTIE SPREADSHEET:** nobody takes the loop, gordon.
  - **WEE GORDO:** nobody had a train.
  - _Dale, in the doorway, holding a brake handle like a cup of tea._
  - **DALE:** it's more of a tractor. but it's on rails.
  - ➤ _"why does nobody take it?"_ → eats
  - ➤ _"who's coming?"_ → who
- **[eats]**
  - **AUNTIE SPREADSHEET:** because the tunnel eats. forty years ago six of ours went in to salvage copper. we found a boot.
  - **WEE GORDO:** cave-ins.
  - **AUNTIE SPREADSHEET:** a boot with the laces done up, gordon. on the track. like someone had been taken out of it.
  - → who
- **[who]**
  - **WEE GORDO:** dale drives. lumps lifts. i think. you shoot. and jack, because if a roof comes down jack can hold up a roof.
  - _Pallet Jack, by the door, Dumpling sitting on his hand truck._
  - **PALLET JACK:** roof's about four tonne a metre. i can hold a metre.
  - **PALLET JACK:** i'll want my dinner first.

#### Talk: `loaner` (with BEV)
- **[start]**
  - _Bev's clinic. A frame of scaffold pole and seatbelt webbing hanging off a hook: a brace, a yoke, an arm cradle with six glass barrels round it._
  - **BEV:** that was his. before i started putting it on the inside. he grew out of it. literally.
  - **BEV:** arm.
  - _She takes your right hand off at the wrist, the way you'd take a lid off a jar, plumbs six lines into it, and puts it back on._
  - **BEV:** you know the finger trick. the blood one. this is that, six at a time, on a motor. it'll empty you in three seconds. don't hold it down unless you mean it.
  - ➤ _"then what's the point of it?"_ → point
  - ➤ _"how does jack run his all day?"_ → jack
- **[point]**
  - **BEV:** three seconds of that is a lot of problem solved. and you get it back off whatever you kill. it's a loan. everything i sell is a loan.
- **[jack]**
  - _Bev looks through the curtain at Jack, who is showing Dumpling how to carry a fridge that isn't there._
  - **BEV:** i took his marrow out and put better in. gristle stock. he makes blood like a tap. it's the only reason that boiler hasn't killed him.
  - **BEV:** it's the best work i've ever done and it's wasted on a man who carries soup.
  - _does: flag:bev_explained_marrow_

#### Scene: `c6_mind_the_gap` (cinematic, 88 s, music: none until 61 s, then revenue_protection_theme: four hundred people humming one note)
- `  0` _The service tunnel under the mall. A yellow maintenance loco the size of a van, a flatbed, a low open wagon. Dale in the cab with a flask. One headlamp. It lights about nine sleepers._
- `  4` _Jack kneels to Dumpling on the platform. Puts the hi-vis vest on him. It reaches the floor._
- `  7` **PALLET JACK:** hold that for me. it's about three hundred grams. i'll want it back.
- ` 10` _Auntie, behind Dumpling, both hands on his shoulders. She looks at you. She doesn't say be careful. She has stopped saying it to people._
- ` 14` _The train pulls out. The platform light gets small. Then it's a dot. Then the tunnel bends and it's gone._
- ` 19` **LUMPS:** it's a lot of dark.
- ` 21` **WEE GORDO:** it's the same amount of dark as anywhere. there's just nothing in front of it.
- ` 25` _Jack sits on the back rail of the wagon with his legs hanging over the track, eating out of a pan. His boiler ticks as it cools. Your chest ticks. They're not in time and it bothers neither of you._
- ` 29` **PALLET JACK:** you kept the clock in, then. how's it sit?
- ` 32` **PALLET JACK:** first part's the worst one. you keep waiting to feel like someone else. *he eats.* then you've got nine and you can't remember which ones you came with.
- ` 38` _A second track swings in alongside. On it, standing in the dark, a commuter train: eight carriages, white, a ☺ on every door. Your headlamp slides down its windows. Every seat is empty. Every door is open. Coats on the hooks. A coffee on a table, grown over._
- ` 46` **WEE GORDO:** *quiet* that's the last one out. new year's eve. it never got in.
- ` 49` **LUMPS:** where'd they all go?
- ` 51` _Nobody answers. The dead train slides away behind you. Its last carriage has no back wall. The metal is bent outwards._
- ` 55` _Jack has stopped eating. He is looking back down the tunnel, past the wagon's rail, at the tunnel lights: a string of weak bulbs running back the way you came._
- ` 58` _The furthest one goes out._
- ` 59` _Then the next one._
- ` 61` _Then they go out in order, towards you, quite fast. Under the sound of the train: breathing. A lot of it._
- ` 65` **PALLET JACK:** dale. faster.
- ` 66` **DALE:** this is faster.
- ` 68` _Jack stands and his rig comes up with him: shins lock, stacks open, the forearm cocks. He turns to tell you to get behind him._
- ` 70` _A black arm as thick as a lamp post comes out of the dark at the height of his belt, goes in under his ribs, and comes out through the boiler in his back. Red steam. It lifts him a metre off the deck. It is made of arms._
- ` 73` _Jack looks down at it. He gets both hands on it. He breaks it. It takes him two tries._
- ` 76` _He lands on his knees. The severed length of it is still through him. He stands up anyway._
- ` 78` **PALLET JACK:** that's... about two hundred kilo. *he breathes.* it's fine. it's just all at once.
- ` 81` _The last bulb before the wagon is still lit. Something white fills the tunnel behind it, wall to wall: a face. Two tall holes for eyes. Hands on the walls. On the roof. It hauls._
- ` 85` _From behind the face, four hundred voices, not together:_ **tickets, please.**
- ` 87` → BOSS INTRO: REVENUE PROTECTION · TICKETS, PLEASE

#### Scene: `mo_carry_the_bit_that_works` (moment, playable, about 70 s, no music: the train, the breathing)
_Plays when phase 1 reaches its scripted end. The player keeps control of the camera and of one button._
- `  0` _Jack's block fails. A Sweeper takes him across the chest and his armour goes: the collarbone weld, the shin locks, the stacks, all at once, the sound a rig makes when it's finished. He goes down against the fridge. THE GAP closes to 6 m and holds. Lumps and Gordo are on the Grabbers with a crowbar and a fire axe. They are losing._
- `  5` _You get to him. The arm is still through him. The boiler is split and what's coming out of it is not steam any more. Two Snatchers are walking down the walls towards him, in no hurry. They know which one of you has stopped._
- `  9` **PALLET JACK:** light one. listen. i've done the sums.
- ` 12` **PALLET JACK:** i'm two hundred and ten kilo and i'm not getting up. you can't carry me. he can't carry me, not with that arm.
- ` 17` **PALLET JACK:** and that thing doesn't kill you. look at it. *behind the mask's rim, between the arms, faces.* it keeps you.
- ` 22` **PALLET JACK:** i'm not going in there. i've got a boy at home holding my vest.
- ` 26` _He takes your right hand, the one in the cradle, and puts the heel of it on his own chest, left of the weld. He holds it there._
- ` 29` **PALLET JACK:** so you do it. then it's got nothing to keep.
- ` 32` **LUMPS:** *from the rail, not turning round* jack. no. sorry. no.
- ` 35` **PALLET JACK:** ambrose. hold the rail. you're doing really well.
- ` 38` _He looks back at you. He's sweating. He's trying to do this properly._
- ` 40` **PALLET JACK:** and after. bev says the marrow's the only good thing in me. it's in the spine, low down, behind the boiler. it'll keep for a minute once i've stopped. take it. that gun'll run all day on it.
- ` 47` **PALLET JACK:** don't carry me, light one. carry the bit that works.
- ` 50` _The prompt appears: **[FIRE]**. Nothing else on the HUD. The game does not do it for you. The Snatchers are four metres away. If you wait, he says:_ **PALLET JACK:** go on. it's not heavy.
- ` — ` _You fire. One bolt. It sticks. He breathes out. The cross comes, and it's small, and it's quick._
- ` +2` _His hand comes off yours and stays open on the deck._
- ` +4` _The prompt appears: **[TAKE]**. Your hand goes in through the split boiler, the same motion as the Heart Rip, slower. What comes out is a length of spine the colour of a traffic light, wet, and warm, and still making blood: it runs down your arm and into the cradle and all six barrels fill at once._
- ` +8` _Your mannequin back opens along the seam. It goes in. No clinic, no chair, no Bev. The Blood Drive's ring starts to turn without you asking it to._
- `+10` _The Snatchers reach Jack. They pick him up. They turn him over. They put him down. There's nothing there for them._
- `+12` _Lumps has turned round. He is looking at you, and at your arm, and at Jack. It's the first time he's looked at you like you might be a thing._
- `+14` **WEE GORDO:** *hoarse* lumps. LUMPS. rail.
- `+15` _The mask hauls. THE GAP reads 6 m. Your HP bar is full, and then past full, and it is not your colour._
- `+16` **PENALTY FARE**

#### Scene: `c6b_terminus` (cinematic, 52 s, music: auntie_theme_crayon, one instrument)
- `  0` _The train coasts out onto a viaduct over The Commute. Sunset: the same one Lumps cries at. Dead traffic to the horizon, every windscreen red._
- `  4` _Behind you, the tunnel mouth. The broken face lying on the track in the last of the light. Behind it, in the dark, what's left: heaps, steaming, a few hands still opening and closing on nothing. Nothing follows. A click. One._
- `  9` _Dale stops the train. He doesn't get out of the cab. He has both hands on the brake and his forehead on his hands._
- ` 13` _Gordo sits down where he's standing. He has the fire axe across his knees and can't open his fingers._
- ` 17` _Lumps kneels by Jack. He closes the split in the boiler with his hands, the way you'd close a coat on someone. He gets his good arm under Jack's back and his bad arm under his knees._
- ` 23` **WEE GORDO:** lumps. he's two hundred kilo. your arm.
- ` 26` **LUMPS:** two hundred and ten.
- ` 28` _He lifts him. The stitches in his forearm go, one at a time. He stands up._
- ` 32` _He walks past you to the front of the flatbed and stops. He doesn't look at you._
- ` 35` **LUMPS:** he asked you.
- ` 37` **LUMPS:** i know he asked you. i heard him.
- ` 40` _A long time._
- ` 43` **LUMPS:** ...is it warm? the bit of him.
- ` 45` _It is. Your arm is ticking over on its own, barrels filling and emptying, slow, like breathing._
- ` 48` **LUMPS:** okay. *he nods.* okay. sorry.
- ` 50` _He carries Jack to the front of the train so he can see where it's going._
- ` 52` → `p5b_employee_4417`, then **END OF ACT I**

**Reward:** the train (fast travel), marrow_pallet_jack, the Blood Drive
**Review card:** all three grades read the same: NO REVIEW TODAY.
_Builder notes: the only mission whose grade card has no joke. Jack's vest stays on Dumpling for the rest of the game (it never fits). LEG DAY's intro changes: Lumps is carrying fridges up the Long Stairs because someone has to do Jack's round._

---

## 6. What taking his bio material gives you

**PALLET JACK'S MARROW** `marrow_pallet_jack` · slot: spine · kind: inheritance (new kind: a part from a friend. This is the only one in Act I)

- **Perk.** Blood weapons cost nothing while you are firing them (Blood Cross, Blood Drive). Outside a fight you make
  blood back: 3 HP a second up to full. You can carry the Blood Drive, and in story mode the Overdrive Rig streak
  lasts twice as long on you, because you've got the plumbing for it now.
- **Downside.** You weigh more: jump height down 10%, fall damage up. You are hungry: every ten minutes of play the
  HUD tells you what something nearby weighs. If you stand still for a while your right hand closes around a
  hand-truck handle that isn't there.
- **Drift.** +1 permanent, whatever your Body Budget is. It isn't over-budget Drift; it's the kind you get from a
  choice. Bev's rule from m05 applies: you won't notice. The people who love you notice.
- **Look.** A line of traffic-light red down the mannequin's spine that shows through the plastic when you fire.
- **Text.** "The only good thing in him, according to the woman who put it there. She was wrong about that."
- **Echoes later (cheap, one line each).** Bev in Act II won't charge you for the next install and won't say why.
  Dumpling asks why you sound like his uncle when you're tired. In Act III, Lumps' split choice is harder to steer if
  you never spoke to him after the train (`talk: after_jack`, optional, at the sunset wall).

---

## 7. Building it (after the OK, not before)

| piece | lane | effort | notes |
|---|---|---|---|
| mission, scenes, talks, cast, implant, boss data | story | medium | into `shared/story/content/`, docs regenerated, validator green |
| REVENUE PROTECTION model | story + art | high | Blender: 12 enamel plates as separate parts with damage states, the mass behind, the Inspector; arms are code-driven chains of one Blender segment and one hand |
| arms, the haul cycle, the mask breaking | story | high | pose sheets and clips first, same method as Overtime |
| Pallet Jack model and clips | story + art | high | on the cast mannequin rig with rig parts; needs a death pose and the carried pose |
| Blood Drive model, fire, sound | story | high | reuses `bloodcross.js` bolts and bursts |
| the train arena, scrolling tunnel, THE GAP | story | high | a treadmill: the train stays still, the tunnel and the boss move |
| referee: the fight's rules | story | high | after the Overtime bosses PR, reusing its part-hitbox format |

## 8. The owner's decisions (2026-11-10)
1. **Who dies:** Pallet Jack. Lumps and Wee Gordo live.
2. **The player pulls the trigger**, with a button. No cutscene does it for them.
3. **The boss:** you stop it and it breaks apart. The chase ends for good here; it can come back later.
4. **Names:** PALLET JACK, BLOOD DRIVE, REVENUE PROTECTION and TICKETS, PLEASE are kept.
