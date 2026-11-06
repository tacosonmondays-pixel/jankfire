# Act 5: "Overdue"
_What do you become?_

_Generated from `shared/story/content/missions/act5.js` and `scenes_act5.js`._

### 31. OVERDUE `m31_fully_billable`
_Mr. Overtime, wired into the Master Clock, holds the door one last time. If you found the end of his shift, you can give it back to him._

**Where:** The Master Clock (CORP HILL)  
**Who:** MR. OVERTIME, JUNE, LUMPS, WEE GORDO  
**Giver:** — · **Needs:** m30_the_lobby

**Beats**
- C21: the Clock opens like a ribcage. Overtime plugs his stapler arms into the gears. 'your appointment is now.'
- Boss fight: MR. OVERTIME, FULLY BILLABLE (overtime_4). A vertical gearwork arena; every phase changes the clock speed (slow-mo rounds, fast-forward rounds).
- At the phase 2 break, he stops to 'process' you, and you get to talk. With all six of his memory fragments, you can show him the end of his shift.
- Talk-down: C22. He clocks out. 'first time i've left on time.' He gives you Cale's tape. Otherwise: phase 3, and you destroy him.

**The mystery**
- _learn:_ (talk-down) Overtime killed Cale at 17:29, then stood at the door at 17:30 with his coat on, on the phone to June: 'i'm on my way.' He kept Cale's tape in his chest slot for sixty-one years. He never handed it in.
- _suspect:_ —
- _withheld:_ —

**Objectives**
1. _(scene)_ · scene `c21_fully_billable`
2. stop the master clock · **boss: MR. OVERTIME**

#### Scene: `c21_fully_billable` (cinematic, 58 s, music: fully_billable)
- `  0` _Through the glass door into the Master Clock: gearwork the size of a cathedral, going up and up into the dark, teeth as big as buses, a pendulum like a falling building. Every tick shakes dust out of the air._
- `  6` _(if flag:let_gordo_go)_ _Gordo's charges have done their work: half the gears are dead and dark, the emergency lights are red. The Clock limps._
- ` 10` _In the middle of it, on a platform at the heart of the mechanism, Mr. Overtime. His suit is in tatters. His time card, torn, is taped back together in his chest slot. Cables run from the Clock into his back._
- ` 16` **MR. OVERTIME:** you're late.
- ` 19` **MR. OVERTIME:** everyone's late. everyone's been late for so long. i've been holding the door.
- ` 24` _The Clock opens around him like a ribcage. He lifts his stapler arms and drives them, one, two, into the gears. Sparks. The pendulum stops dead, then swings back the other way._
- ` 30` **MR. OVERTIME:** ms. hask says if the clock restarts, everyone comes back. everyone who's absent. they'll all be on time.
- ` 37` **MR. OVERTIME:** june will be on time.
- ` 40` _(if flag:overtime_reached)_ **MR. OVERTIME:** *a glitch, his voice slipping* i don't... i don't think june worked here.
- ` 45` **MR. OVERTIME:** your appointment is now.
- ` 49` **MR. OVERTIME:** the meeting is now. the meeting is forever.
- ` 54` _Every clock face in the cathedral of gears lights up at once._
- ` 57` → BOSS INTRO: MR. OVERTIME · FULLY BILLABLE

#### Scene: `c22_clocking_out` (cinematic, 70 s, music: clocking_out)
- `  0` _Only if you talked him down. The Clock has stopped. Overtime on his knees on the platform, cables hanging off him, steam drifting. You're holding his last backup: a small glowing ☺ CORP cartridge from the Machine's archive, labelled SALLOW E. · 17:30:00._
- `  6` _You put it in his chest slot, where the time card goes. It clicks._
- `  9` _The ☺ Spire lobby, 17:30:00, sixty-one years ago, seen through his eyes: the doors. His overcoat on. A beige lobby phone in his hand. Behind him, on the floor by the pillar, something he doesn't look at._
- ` 14` **JUNE:** ed? ed, are you there? it's half five.
- ` 18` **MR. OVERTIME:** i'm here. i'm... i'm on my way. i'm on my way, june.
- ` 22` **JUNE:** are you coming home?
- ` 25` _Back in the Clock. Overtime is looking at his watch, the real one on his wrist under the steel. He looks at it for a long time. The second hand moves._
- ` 34` **MR. OVERTIME:** 17:30.
- ` 37` **MR. OVERTIME:** that's the end of my shift.
- ` 41` _He reaches behind his back and unplugs the cables one by one. The punch-clock in his chest ticks, slower, slower._
- ` 49` _He reaches into his chest slot and takes out something else that was in there: an old ☺ CORP tape cartridge. Cale's copy of Option C. He holds it out to you._
- ` 53` **MR. OVERTIME:** you dropped this. in the lobby. i'm sorry. i should have handed it in.
- ` 58` **MR. OVERTIME:** first time i've left on time.
- ` 63` _He sits down on the edge of the platform, his huge legs hanging over the gears, like a man at the end of a long day. He closes his visor._
- ` 68` **MR. OVERTIME:** go on. she's waiting for you. ...the other one.

#### Talk: `processing` (with MR. OVERTIME)
- **[start]**
  - _Phase 2 ends. Overtime grabs you in a stapler arm and holds you in front of his chest slot. The clock face in his heart is huge, cracked, ticking unevenly. He doesn't punch you in. He waits._
  - **MR. OVERTIME:** please hold still. you're being processed.
  - **MR. OVERTIME:** ...i don't know what to process you as. you're not on my list. you've never been on my list. you're absent and you're here.
  - **MR. OVERTIME:** what are you?
  - ➤ _"(with all six fragments) i'm the one who's got your last backup."_ → frags (if frags.overtime>=6)
  - ➤ _"(with some fragments) you have a wife. june."_ → some (if frags.overtime>=3 !frags.overtime>=6)
  - ➤ _"i'm the one you killed."_ → killed
  - ➤ _"(cold) i'm your replacement."_ → cold (if drift>=4)
- **[frags]**
  - _You show him, one by one: his first day, the founder on his lap. June's lunchbox note. His employee-of-the-month photo, number one. Hask's order to hold the lobby. Cale running, 17:29. And the last one: 17:30:00, the door, his coat on, the phone._
  - _His grip loosens. The clock in his chest slows down._
  - **MR. OVERTIME:** that's... that's the end of my shift.
  - **MR. OVERTIME:** you've got the end of my shift.
  - ➤ _"*give it to him*"_ → give
- **[give]**
  - _He puts you down. Very carefully, like something that might break._
  - _does: flag:overtime_clocked_out, flag:overtime_resolved, scene:c22_clocking_out, give:cale_tape, fate:overtime=clocked_out, drift:-1_
- **[some]**
  - **MR. OVERTIME:** june.
  - _the grip tightens, then loosens, then tightens* june. june's at home. june's always at home. i'm always..._
  - **MR. OVERTIME:** no. no, i'm on shift. i can't remember the rest. i can't. you haven't got the rest.
  - → fight
  - _does: flag:overtime_almost_
- **[killed]**
  - _A long pause. The ticking stutters._
  - **MR. OVERTIME:** cale. 17:29. you were running.
  - **MR. OVERTIME:** ...it was policy. it was policy.
  - → fight
- **[cold]**
  - _Something like relief in his visor._
  - **MR. OVERTIME:** oh. good. good. they've sent someone. i'm so tired.
  - → fight
  - _does: drift:+1_
- **[fight]**
  - _He lifts you to the slot. Then he flings you across the gearwork instead, and the Clock speeds up. Phase 3._
  - _does: flag:overtime_destroyed_path_

**Reward:** cale_tape, lt_boss_overtime_4
_Builder notes: if destroyed: no C22; a Moment where his punch-clock stops, his visor goes dark, and the tape falls out of the slot onto the platform (give:cale_tape, flag:overtime_destroyed, fate:overtime=terminated)._

---

### 32. FULLY VESTED `m32_fully_vested`
_Marion Hask shows you the last page and the body under her suit, and then it's your choice._

**Where:** The Master Clock (CORP HILL), The Top Floor (CORP HILL), The Clock Room (CORP HILL)  
**Who:** MARION HASK, LUMPS, WEE GORDO, MINA, THE FOUNDER  
**Giver:** — · **Needs:** m31_fully_billable

**Beats**
- C23: page six on the console. 'I signed at 16:59. At 17:10 Remainder telephoned me.' They'd hit target by half a percent. She launched anyway. The suit opens: a body of other people's organs, each one tagged with a name.
- If you hold Mr. Sevens' call log and Neville's envelope, extra lines: you can read them back to her.
- Boss fight: MARION HASK at the Clock's controls.
- C24: the ledger. The three choices in front of you (and the fourth, if the cats are all petted).
- The choice. Then the ending, the district epilogues, the credits drive.

**The mystery**
- _learn:_ ☺ CORP page: the launch at 17:30 was timed so a full day's wages, every pension and every debt was written off at close of business, and the final backup was taken to keep the dead as workforce. At 17:10 Hask knew the launch wasn't needed. She launched because it was cheaper than not.
- _suspect:_ —
- _withheld:_ —

**Objectives**
1. _(scene)_ · scene `c23_fully_vested`
2. stop marion hask · **boss: MARION HASK**
3. _(scene)_ · scene `c24_the_choice`
4. choose

#### Scene: `c23_fully_vested` (cinematic, 46 s, music: hask_final)
- `  0` _The Clock's control room: a white cockpit at the top of the gearwork, a console of a thousand switches labelled with districts, and the Machine's archive link humming in the wall. Hask walks in from her office, perfectly calm. She has page six of Option C in her hand. She puts it face up on the console, where you can read it._
- `  8` **MARION HASK:** You will want to read that. Everyone always wants to read the last page.
- ` 12` _APPROVAL AND CONTINUITY. EXECUTION AT CLOSE OF BUSINESS (17:30) SO THAT THE DAY'S WAGES, ALL PENSIONS AND ALL OUTSTANDING DEBTS ARE EXTINGUISHED. FINAL BACKUP OF ALL STAFF TO BE RETAINED AS WORKFORCE. Signed: M. Hask, Chief Punctuality Officer. 16:59._
- ` 20` **MARION HASK:** I signed at 16:59. At 17:10 Remainder telephoned me. The revised numbers had come in that morning. We had hit our target by half a percent.
- ` 28` **MARION HASK:** The launch was no longer necessary. I thanked them for their time.
- ` 32` **MARION HASK:** Hitting the number would have cost us more than ending the world. I did the arithmetic. I am very good at arithmetic.
- ` 38` _She unbuttons her white jacket at the throat. Then the next button. The suit opens like a cabinet. Under it, behind a clear frame of ☺ CORP plastic: a body made of other people's organs, all of them pink and working, each one tagged with a small paper label with a name in tiny handwriting._
- ` 44` → BOSS INTRO: MARION HASK · CHIEF PUNCTUALITY OFFICER

#### Scene: `c24_the_choice` (cinematic, 60 s, music: the_choice)
- `  0` _The control room after the fight. Hask is sitting on the floor against the console, the frame cracked, her ledger open in her lap. She isn't dying yet. She's reading names._
- `  6` **MARION HASK:** Dorothy Pell. Kidney, left. Ian Brightwater. Lung, right. Kenneth Abara. Liver.
- ` 12` _(if fate.dot=freed)_ **LUMPS:** *very quietly* she's only got one kidney. she said she sold it. she said it was for my birthday.
- ` 12` _(if fate.dot=gut)_ **LUMPS:** *very quietly* ...mum?
- ` 16` **MARION HASK:** Every one of them is written down. I read them every night. Somebody should.
- ` 21` _Three things in front of you. The lanyard, R. CALE · HEAD OF TIMEKEEPING, on the console. The Master Clock's great lever, behind a glass panel marked RESTART · DO NOT BREAK. And the archive link, with Auntie's six pages beside it and a broadcast switch labelled ALL SCREENS._
- ` 28` _(if has:cale_tape)_ _And in your hand, the tape cartridge Cale ran down sixty floors with, sixty-one years late._
- ` 31` _(if cats>=12)_ _And, through a small door at the back of the control room that wasn't there before, a soft sound. Purring._
- ` 35` **WEE GORDO:** smash it.
- ` 37` _(if !fate.auntie=alive)_ **WEE GORDO:** *after a moment, quieter* ...or do hers. i'm not her. you know what she'd want.
- ` 41` _(if fate.mina=freed)_ **MINA:** you're doing the cereal face again. whatever you pick, i'm here.
- ` 46` **MARION HASK:** You can sign. Everyone is fed by Friday. Or you can be right. Both are allowed. Only one of them has ever kept anybody alive.
- ` 54` _Nobody tells you what to do._
- ` 58` → CHOICE: the_choice

#### Scene: `e1_on_time` (cinematic, 150 s, music: on_time_theme)
- `  0` _You pick up the lanyard. You put it on. It's lighter than you expected. Hask watches you do it, and for the first time in the game, she smiles. It's a very small smile._
- `  6` **MARION HASK:** Welcome to the company, Cale.
- `  9` _You pull the lever. The Master Clock restarts. The tick goes out over the city like a heartbeat._
- ` 14` _From the top of the Spire: the lights come on across the ruins, district by district, on the beat. Corp Hill. Number Works. The Checkout. Pinstripe. Chrome Gristle's neon goes white. The Lates' clock tower gets its hands back and they point to 09:00. Even the Gut's veins glow cyan._
- ` 44` _Food trucks roll out of the Spire's garage onto Dividend Road at 06:00 exactly, and arrive at every district at 06:30 exactly. People in the Bottom stand in queues that move._
- ` 52` _The Restoration Warehouse: the dead walk out in neat rows through the door in the sky, down the grey steps, onto the Commute, and go to work. They wave. They're a little bit like you: a tilt, a knee that bends the wrong way, then fixed._
- ` 64` _(if flag:plan_lumps)_ _In the Gut, the digesters are cut free and given lanyards. Lumps in a canteen apron, serving soup to the Restoration's first shift. Dot on the next shift. It's still a job._
- ` 64` _(if !flag:plan_lumps)_ _In the Gut, a Gristle & Sons truck backs up to the digester wall. On the side: ORGAN SUPPLY · CONTRACT RENEWED._
- ` 72` _The Bottom. One by one, the stacked pastel houses fold into the void, like closing books. The washing lines go last. Vacancy's survey team plants a SOLD sign on the Lost & Found._
- ` 82` _(if flag:margins_takeover)_ _At the Margins, the gnome line holds a little longer than it should. Then a ☺ CORP bulldozer pushes the gnomes into the void in a skip._
- ` 88` _The Machine is carried up the hill on a flatbed, humming, still humming, and plugged into the Clock. Dale walks behind it in a clean uniform with a name badge._
- ` 96` _Your lanyard, close up: R. CALE · HEAD OF TIMEKEEPING._
- `100` _(if fate.mina=freed)_ _Mina, in the vents with Milo, turns a flat on Corp Hill down by letter. The letter is addressed to you. You read it at your desk at 12:00, on your lunch slot: 'you were late for me once. you can be late for them.'_
- `108` _(if drift>=4)_ _At high Drift you file the letter without opening it. The Schedule says it isn't important._
- `112` **PRITCHARD:** *on the pager, very quietly* your 09:00 is here. all of them.
- `118` _Last shot: the warehouse floor at 09:00. Ten thousand of you, in rows, in ☺ CORP uniform, every one with your tilt fixed and your knee straight, lift ten thousand time cards and clock in at the same moment._
- `128` _CLUNK._
- `132` **ENDING: ON TIME**
- `136` _Then the district epilogue panels (endings.js) and the credits drive._

#### Scene: `e2_late` (cinematic, 160 s, music: late_theme)
- `  0` _You break the glass. You don't pull the lever. You put your shoulder into the great gear behind it, and Gordo puts his in next to yours, and Lumps puts in both arms._
- `  6` **WEE GORDO:** on three. ...no. just push.
- `  9` _The Master Clock's escapement breaks. A tooth the size of a car snaps off and falls a hundred metres through the gearwork. The pendulum stops halfway._
- ` 15` _Every clock in the city stops at once. The public clocks on Corp Hill. The kitchen clocks in the Bottom. The egg timer on Sharon's pot. Pauline's watch in the Lates. The Restoration warehouse's wall-sized schedule goes blank, and two hundred thousand mannequins sit down where they're standing, gently, like people at the end of a long day._
- ` 39` _And then nothing tells anyone what time it is._
- ` 43` _Corp Hill goes dark, for the first time in sixty-one years. The Spire's windows go out floor by floor, top to bottom. In the dark, you can see the stars over the city. Nobody alive has ever seen them from here._
- ` 54` _Hask in her dark office, a candle, the ledger. She doesn't look up as you leave. She's reading names._
- ` 60` _(if flag:overtime_clocked_out)_ _On the way down, the Bottom's stairs at sunset, days later: an old man in a torn grey suit sits on a step, too big for it, with nowhere to be. Every evening at 17:30 he stands up, and then he sits back down. The kids bring him tea. He asks what day it is. They tell him. He nods._
- ` 60` _(if !flag:overtime_clocked_out)_ _The Restoration spares are dark. Nothing reloads Edwin Sallow. His empty brogues stand on the platform at the top of the Clock, side by side, polished._
- ` 72` _One epilogue panel per district, by who runs it (endings.js). The rot spreads where nobody holds it._
- ` 80` _The Long Stairs, one evening. Something green is growing out of the corpse-crust between the steps: not pink, not flesh. Green. A weed, then a vine, then a tomato plant._
- ` 88` _(if fate.dot=freed)_ _Dot is kneeling by it with a watering can, telling Lumps off for crying._
- ` 88` _(if !fate.dot=freed)_ _Lumps is kneeling by it alone. When you come down the stairs, he gets up and walks away. He doesn't say anything. He doesn't have to._
- ` 96` _(if fate.mina=freed)_ _Mina sits on the step next to you at 17:30, the way she will every evening. 'so you're on time for once.'_
- `104` _Dale, in the Lost & Found, in the dark, his ear against the glass of the Machine. The power's gone. It's still humming. Nothing can kill it._
- `112` **DALE:** they're still having a nice day in there. ...that's all right. it's all right for them to have a nice day.
- `120` _Wee Gordo at the top of the Long Stairs, looking out over the dark city, no lights anywhere except fires and the stars._
- `128` **WEE GORDO:** ok.
- `131` **WEE GORDO:** now the hard part.
- `138` **ENDING: LATE**
- `142` _Then the district epilogue panels and the credits drive._

#### Scene: `e3_off_books` (cinematic, 165 s, music: off_books_theme)
- `  0` _You lay the six pages on the archive console's scanner, one by one, the way Auntie laid them in their masking-tape frames: Fazzoletti, Big Value, Remainder, Gristle & Sons, Vacancy, ☺ CORP._
- `  8` _(if has:cale_tape)_ _Then you put Cale's tape cartridge in the slot beside them. It's slow. It's ancient. It still works. The copy gets out of the building, sixty-one years late._
- `  8` _(if has:late_memo)_ _And Neville's envelope, TARGET MET (+0.5%), on top._
- ` 15` _You flip the broadcast switch: ALL SCREENS._
- ` 18` _Every screen in the city: the billboards on Corp Hill, Chrome Gristle's neon, the TVs in the Checkout's windows, the Machine terminals, the fallen digits on the Commute flickering back to life. Option C, all six pages, the signatures printed big. Chad Tempo reads it on ☺ CORP News perfectly, without understanding a word._
- ` 46` _(if flag:print_ready)_ _At 06:00 the Price Press runs it on every price tag in the city. People in the Bottom read it off the tin of beans._
- ` 52` _The debts die. Every Late Fee, every quarter of back pay, every deed and every sale, void, because the paper that made them says in its own words that it wrote off the world on purpose. The Bottom's sale to Vacancy is void. The trucks stop._
- ` 62` _In the Suburb sim, inside the Machine, the bots stop fighting. One by one they put their guns down and sit on the lawn in the sun. Dale opens the sims to the dead as their own place: no work, no Schedule, an afterlife they run themselves. The PvP keeps going, because some of them like it. They're free now._
- ` 76` **DALE:** *his ear to the glass* they're asking what day it is. ...i told them it's whatever they want.
- ` 82` _A long table in the ruins at the bottom of Dividend Road, on the Bleach Line. On one side: Hask, Nonna, Gail or the Bishop or whoever's left of each company. On the other: the Bottom, the groups, the Unpaid. Pritchard taking minutes. Gordo shouting at a Fazzoletti lawyer. Hask reading her ledger aloud. It takes four days._
- ` 98` _The companies survive, weakened. They have to bargain, because they have nothing left to sell that people don't now know the price of._
- `104` _The Lost & Found. Auntie's crayon notebook, published after Option C, open on the long table at its last page: 'his name was rory. he was late because of me.'_
- `112` _The Machine's tray. Dale has his hand over the DISPENSE button. He takes it away. He leaves the tray empty._
- `116` **DALE:** no more returns.
- `120` _The edge of the Commute at dawn, where the dead highway goes out past the last digit toward somewhere nobody's mapped._
- `124` _(if fate.mina=freed)_ _Mina walks with you to the last car. She lets go of your hand._
- `128` _(if fate.mina=freed)_ **MINA:** go on. i'm good at waiting. i'll be terrible at it this time.
- `134` _(if fate.lumps=alive)_ _Lumps hugs you, which pops your shoulder back in, and says sorry._
- `140` _You walk out onto the Commute alone. The Bottom has to build the rest. That was always the deal._
- `150` **ENDING: OFF THE BOOKS**
- `154` _Then the district epilogue panels and the credits drive._

#### Scene: `e4_nap_time` (cinematic, 70 s, music: nap_time_lullaby)
- `  0` _The small door at the back of the control room. Behind it: the clock room, a tiny round room full of old ☺ CORP furniture, and in the middle a second, smaller Machine, the size of a microwave. Asleep on top of it, enormous, ancient, grey and white: the founder. Its collar badge says OUR FOUNDER._
- `  8` **WEE GORDO:** ...is that a cat.
- ` 10` **MARION HASK:** Do not touch the founder.
- ` 12` _You pet the founder. A counter in the corner of the screen, in the zine font: 1. You keep going. 2. 3. The purring gets louder, like a server room. 7. 8. Hask has sat down on the floor. 11._
- ` 26` _12. The founder stands up, stretches for a very long time, and walks slowly across the second Machine's keyboard._
- ` 32` **zzzzzzzzzzzz**
- ` 36` **MACHINE:** INPUT ACCEPTED. MOTION: NAP. CARRIED.
- ` 39` _Legally, that's a nap. Every contract in the city is suspended. Every clock in the city shows zzzz._
- ` 43` _Everyone lies down. Hask, with her head on the ledger. Overtime on his platform, standing, steaming gently, a cat on his visor. The Twins, one snoring. Auntie behind the reception desk with the shotgun across her knees, snoring, alive. The Bottom on its stairs. The Gut, the whole district, snoring as one. The Loopers. Linda in a deckchair. The Cart Mother in a trolley. Dale against the Machine, smiling._
- ` 62` _The founder curls up on your chest. You're asleep too._
- ` 65` **ENDING: NAP TIME**
- ` 67` **(this didn't happen.)**

#### Scene: `credits_drive` (cinematic, 240 s, music: credits_drive)
- `  0` _A playable drive down the hill in the sofa-car, in the ending's light (ON TIME: lit, on schedule; LATE: dark, fires and stars; OFF THE BOOKS: dawn; NAP TIME: everyone asleep in the road). Credits scroll in the zine style down the side of the screen._
- `  5` _Everyone who's still alive is somewhere on the route, doing what their fate in the cast bible says, and waves (or doesn't). Allies' banners on the districts they hold. The gnome line at the Margins. The green thing on the Long Stairs, if it grew. Overtime on the stairs, if he clocked out._
- `230` _The drive ends at the Lost & Found. The Machine is humming. The tray is (or isn't) empty. Fade._
- `238` **JANKFIRE: OVERDUE**

#### Talk: `evidence` (with MARION HASK)
- **[start]** _branch: has:sevens_call_log has:late_memo → both; has:late_memo → memo; else → none_
- **[both]**
  - _Before the suit opens, you put two things on the console: Mr. Sevens' call log (17:10, to M. HASK, 4 minutes) and Neville's envelope (TARGET MET +0.5%)._
  - _Hask looks at them for exactly as long as it takes to read them._
  - **MARION HASK:** Mr. Sevens kept a log. Of course he did. He touches wood.
  - **MARION HASK:** And Mr. Brisk's envelope. He was very late. It would not have mattered if he had been on time. I would have thanked him for his time too.
  - _does: flag:confronted_hask_evidence_
- **[memo]**
  - _You put Neville's envelope on the console: TARGET MET (+0.5%)._
  - **MARION HASK:** Mr. Brisk. He was very late. It would not have mattered if he had been on time.
  - _does: flag:confronted_hask_evidence_
- **[none]**
  - _She doesn't need you to bring proof. She tells you, because she has never once been ashamed of arithmetic._

#### Choice: The lanyard. The lever behind the glass. The six pages and the broadcast switch. (And, if you petted the whole board, a purring from the clock room.)
- **ON TIME: put on the lanyard and restart the Clock**: The Restoration runs. Everyone is fed on schedule. The dead go to work forever with your recording as their template. The Bottom is sold to the void (unless its living are on the staffing table: Lumps' plan). Nobody in the city is free, including you.
- **LATE: break the Master Clock**: Nobody owns time again. The Restoration dies with the Clock. The companies lose their grip, the districts belong to whoever holds them, the rot spreads, and something green grows on the Long Stairs. No lights on Corp Hill, no food on schedule, nobody to stop the next warlord.
- **OFF THE BOOKS: publish Option C to every screen** _(if pages>=6)_: All six pages, on every screen. The debts are void. The sims are opened to the dead as their own place. The companies survive, weakened, and have to bargain at a table with the people they wrote off. You walk out onto the Commute alone.
- **NAP TIME: open the small door** _(if cats>=12)_: The founder walks across the keyboard and types zzzzzzzzzzzz. Legally, that's a nap. Non-canon: after the credits the game asks you to choose again (the save keeps the NAP TIME unlock and the outfit).

**Reward:** page_corp, lt_boss_hask
_Builder notes: after any canon ending the city stays open (post-game) with the ending's look applied (endings.js). The Machine keeps running the sims._

---
