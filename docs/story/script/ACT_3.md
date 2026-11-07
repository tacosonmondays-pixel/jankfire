# Act 3: "Off the Clock"
_What are they planning?_

_Generated from `shared/story/content/missions/act3.js` and `scenes_act3.js`._

### 18. NINE KILOMETRES `m18_nine_kilometres`
_With Overtime's lanyard you can pull ☺ CORP's master Schedule off the network. Printed out, it's nine kilometres long, and it has a hole in it._

**Where:** Gordo's Den (THE BOTTOM), The Bleach Line (CORP HILL), The Price Press (NUMBER WORKS), The Smokestacks (NUMBER WORKS)  
**Who:** WEE GORDO, NELL THIRTEEN, MR. SEVENS, FOREMAN REMAINDER  
**Giver:** WEE GORDO · **Needs:** m17_minutes

**Mechanic hook:** the Timekeeping relay is a stealth climb with grapple shortcuts, and the backup shredder clears the paper storm on the way out _(uses: the shredder, late fees, the grapple)_

**Beats**
- Gordo: if ☺ CORP keeps the dead for a reason, the reason's in the Schedule. Overtime's lanyard opens the Timekeeping relay on the Bleach Line.
- A stealth-or-loud job at the relay: plug the lanyard in, download the Schedule to a tape. Late Fees ★3.
- Number Works prints it (Sevens grudgingly if you made a DEAL; the union gleefully if they run it). P12: the paper waterfall.
- Gordo finds the gap: 03:00-04:00, the Missing Hour. Nobody's booked, not even ☺ CORP.
- Two odd entries in it: Evergreen Acres is the only district with slots at 03:00 ('CHARGE'), and the Lates has a single entry at 03:00 every night: 'DOOR'.
- Gordo, on the paper in the yard, tells you he was born at 03:14.

**The mystery**
- _learn:_ The Schedule has a blind spot: 03:00-04:00, an hour nobody is booked into. Evergreen charges something at 03:00. The Lates opens a 'door' at 03:00. Gordo was born in the Missing Hour; the Schedule put his family outside for it.
- _suspect:_ Whatever ☺ CORP is building happens in that hour.
- _withheld:_ Workforce Restoration (m23).

**Objectives**
1. talk to gordo
2. download the schedule at the timekeeping relay
3. lose the late fees
4. print it at number works
5. _(scene)_ · scene `p12_nine_kilometres`

#### Scene: `p12_nine_kilometres` (panels, 20 s, music: numberworks_press)
- `  0` [panel 1] _the schedule. every minute of every day of ☺ corp's city, booked._ (KA-CHUNK) _The Price Press runs a single endless sheet. It feeds up and out of the Smokestacks and unrolls down the chimneys like a paper waterfall._
- `  5` [panel 2] **WEE GORDO:** nine kilometres of it. every slot's got a name in it. every single one. _Gordo on his knees on the sheet in the yard, running a finger down columns of tiny names and times._
- ` 10` [panel 3] (...) _His finger stops. A white band across the paper, all the way across: no names, no slots. 03:00-04:00._
- ` 14` [panel 4] **WEE GORDO:** 03:00. nobody's booked. not even them. _Gordo looks up. He isn't triumphant. He looks like someone who's just read their own name._
- ` 18` **THE MISSING HOUR**

#### Talk: `relay_plan` (with WEE GORDO)
- **[start]**
  - _Gordo's den has a new piece of string, from the wall of pages to a picture of a clock._
  - **WEE GORDO:** auntie's right about one thing. corp doesn't keep anything for continuity. it keeps things to sell.
  - **WEE GORDO:** so if it's kept the dead sixty-one years, it's got a plan for them. and corp writes every plan in the schedule. every minute of every day, booked.
  - **WEE GORDO:** overtime's lanyard opens the timekeeping relay on the bleach line. you plug it in, it thinks employee number one wants a copy. nobody's ever said no to employee number one.
  - ➤ _"and then what?"_ → then
  - ➤ _"what if it's a trap?"_ → trap
- **[then]**
  - **WEE GORDO:** then we print it. the whole thing. and we read it. all of it. every line.
  - _he looks almost happy* i've wanted to read it my whole life._
- **[trap]**
  - **WEE GORDO:** it's corp. everything's a trap. the trick is to be a trap they haven't priced in.

#### Talk: `print` (with NELL THIRTEEN)
- **[start]** _branch: turf.numberworks=remainders → union; else → sevens_
- **[union]**
  - _Nell, on the press floor, megaphone in hand.* motion: we print ☺ corp's schedule and read it out loud in the yard. all in favour?_
  - _every hand in the yard._
  - **NELL THIRTEEN:** motion carried. RUN IT.
- **[sevens]**
  - **MR. SEVENS:** *touches wood twice* you want to print their schedule on my press. you want to print the one thing they'd kill us for.
  - **MR. SEVENS:** ...fine. a deal's a deal. but if anyone asks, it was a misprint. touch wood.

#### Talk: `born_late` (with WEE GORDO)
- **[start]**
  - _Later. The yard is empty. The Schedule is still lying across it in loops, kilometres of it, and Gordo is sitting in the middle of the white band where nobody is._
  - **WEE GORDO:** my mum was a cleaner in the spire. my dad fixed the lifts. they had a slot. a flat on floor 22. three rations a day.
  - **WEE GORDO:** she went into labour on a shift change. 02:40. the medical bay was booked. she had me in a stairwell at 03:14.
  - **WEE GORDO:** at 04:00 the schedule did its count and there were three of us in a slot for two. so they put us outside. a newborn, at night, in the ash.
  - ➤ _"gordo..."_ → gordo
  - ➤ _"that's why you want it burned."_ → burn
- **[gordo]**
  - **WEE GORDO:** don't. i'm not sad. i'm accurate.
  - **WEE GORDO:** i was born in the missing hour. the one hour corp can't see. it's the only reason they didn't count me till it was too late.
  - _he looks up the hill at the Spire.* and now i know what it's for._
  - _does: flag:gordo_told_birth, standing.bottom:+2_
- **[burn]**
  - **WEE GORDO:** that's why i want it burned. and that's why i'm right. a clock that can throw a baby outside for being early is a clock you don't fix.
  - _does: flag:gordo_told_birth_

**Reward:** 500 coupons, schedule_printout
**Review card:** EXCEEDS EXPECTATIONS. you read all nine kilometres. / MEETS EXPECTATIONS. you found the hole. / SEE ME. you tripped over the schedule and fell into a chimney.

---

### 19. ORGAN DONOR `m19_organ_donor`
_Gristle & Sons' page of Option C was stolen and sold. Doctor Upsell bought it, because he knew what it really was: a patent._

**Where:** Bev's Clinic (THE GUT), Organ Pawn (CHROME GRISTLE), Jar Alley (CHROME GRISTLE), Doctor Upsell's Clinic (CHROME GRISTLE)  
**Who:** BEV, DOCTOR UPSELL  
**Giver:** BEV · **Needs:** m17_minutes

**Mechanic hook:** Bev pins a kidney to show you the Nail Gun; Upsell's twelve arms are torn off one by one with the grapple _(uses: nail to the wall, the grapple, tv remote (pause / rewind))_

**Beats**
- Bev: Upsell has the Gristle page in a jar in his clinic. He bought it off the Choir black market years ago.
- Chrome Gristle at night: neon, rain, jars that blink. Book a consultation at Upsell's clinic (pawn something at Organ Pawn to afford it, or have Bev forge a referral).
- The consultation: Upsell sells you procedures while explaining, with pride, what the page is.
- He tries to 'harvest' your Punch-Clock. Boss fight: DOCTOR UPSELL. Rip out his bad temporary implants with melee.
- The page: 'post-event workforce recovery'. Regrowth was meant to raise the dead as workers, on contract to ☺ CORP. It made the Gut instead.
- Bev takes two of her old hands back off him.

**The mystery**
- _learn:_ Gristle page: the dead were always meant to be a workforce. The Gut was the first attempt, and it failed. ☺ CORP planned to own the dead's labour from the day it signed.
- _suspect:_ If Regrowth was attempt one, the warehouse is attempt two.
- _withheld:_ What attempt two looks like (m23).

**Objectives**
1. talk to bev
2. get an appointment with doctor upsell
3. attend your consultation
4. decline the procedure · **boss: DOCTOR UPSELL**
5. take the page from the jar
6. take the page to auntie

#### Talk: `jar` (with BEV)
- **[start]**
  - _Bev's clinic. She's re-stitching her apron with two hands and smoking with a third. The fourth points at you._
  - **BEV:** you want the gut's page. course you do. it's in a jar. upsell's clinic, chrome gristle, top shelf behind the till.
  - **BEV:** he bought it off the choir's back door years ago. paid a kidney. somebody's kidney.
  - **BEV:** he doesn't keep it because it's evidence. he keeps it because it's a patent.
  - ➤ _"how do i get to it?"_ → how
  - ➤ _"you used to work for him."_ → worked
- **[worked]**
  - **BEV:** eleven years. he paid me in arms. i had four of my own once. two of them are on him now. they wave at me. i want them to stop waving at me.
  - → how
  - _does: flag:bev_wants_hands_
- **[how]**
  - **BEV:** book a consultation. he'll see anyone with coupons or parts. pawn something at organ pawn, buy it back after. or bring me a nice jar from jar alley and i'll write you a referral he can't say no to. i still have his letterhead. i have his everything.

#### Talk: `consult` (with DOCTOR UPSELL)
- **[start]**
  - **DOCTOR UPSELL:** from the first day. corp didn't sign that page for the money. corp signed it for the staff.
  - _he smiles with the whole face.* and now look at you. corp's trying again, isn't it? with you plastic ones. i'd love a look inside. hold still._
  - → give
- **[procedure]**
  - **DOCTOR UPSELL:** ah, a value shopper. i'm offering, today only, the full workforce package: a reliability gland, a compliance lobe, and a lovely little cable port, here, at the back of the neck. you'll never be late again.
  - → jar
- **[jar]**
  - _Three arms stop. Nine keep going._
  - **DOCTOR UPSELL:** the patent. you've got a good eye.
  - _He takes the jar down himself. In it, floating, a page with the Gristle & Sons crest: POST-EVENT WORKFORCE RECOVERY._
  - **DOCTOR UPSELL:** gristle and sons signed this. regrowth, to raise the dead, on contract to ☺ corp. the war makes the bodies, regrowth makes them work, corp books their hours. growth!
  - **DOCTOR UPSELL:** it didn't work, of course. the dead got up and became the gut. the old man messed up the formula. but the idea. the idea's beautiful.
  - **DOCTOR UPSELL:** i've been trying to get it to work on the living. you'd be amazed how much a living person has to give.
  - ➤ _"they were going to make the dead work. from the start."_ → start
  - ➤ _"give me the page."_ → give
- **[give]**
  - **DOCTOR UPSELL:** no. but i'll take your punch-clock. it's a fascinating part. it's free. well. it's free for me.
  - _all twelve arms rise._
  - _does: flag:upsell_fight_

#### Talk: `wall` (with AUNTIE SPREADSHEET)
- **[start]**
  - _Auntie pins page four. She reads it twice, the second time with her finger under every word._
  - **AUNTIE SPREADSHEET:** post-event workforce recovery.
  - **AUNTIE SPREADSHEET:** they were never going to let the dead stay dead. from the first minute.
  - _she looks at you, and for once she doesn't look away.* ...they wanted you, rory. all of you. that was the point of the backup clause. it wasn't continuity. it was stock._
  - **AUNTIE SPREADSHEET:** that's four.

**Reward:** 700 coupons, page_gristle, lt_boss_upsell
**Review card:** EXCEEDS EXPECTATIONS. you declined every upgrade. / MEETS EXPECTATIONS. you kept your kidneys. / SEE ME. you bought a second spleen.

---

### 20. THE MISSING `m20_the_missing`
_Pages first, then mum. It's then. Go into the Gut for the nine, and for Mina._

**Where:** Sharon's Soup Kitchen (THE BOTTOM), The Choir Lung (THE GUT), The Digester Wall (THE GUT), The Big Stomach (THE GUT), The Feed Dock (THE GUT)  
**Who:** LUMPS, BIG SAUCE SHARON, SISTER AGENDA, THE STOMACH BISHOP, DOT, MINA, DUMPLING  
**Giver:** LUMPS · **Needs:** m17_minutes

**Mechanic hook:** the rescue is an escort down Peristalsis Avenue on the beat; the Bishop's ulcers, the marble-slip weakness, and the lasso to drag digesters free _(uses: slide, the grapple, marble slip, blood cross, the lasso)_

**Beats**
- Lumps doesn't ask. He's standing at the Long Stairs with a crowbar and a pot of the yellow soup.
- Sharon tells you what the soup is for: Gristle doesn't eat it. It feeds the digester wall. Her soup has kept the Bottom's missing alive.
- Sister Agenda trades her minutes (a voice box if you did Choir Practice, or your word). The truck number (if you chased it) finds them fast; otherwise you search.
- The digester wall, deep. Mina, grown in to her waist, a grey braid, climbing gloves. 'you're late.' The reunion.
- To free anyone the Gut has to let go. The Choir's song holds it. Stop the Bishop.
- Boss fight: THE STOMACH BISHOP. In the acid lake, then inside him, then just a mouth.
- P6b: DEAL (Gristle stays; stops buying from ☺ CORP; releases the outer wall, keeps Dot as collateral) or TAKEOVER (the Bottom takes the Gut; the Choir stops singing; everyone can come out, but the oldest digesters won't survive leaving).
- Mina comes out either way. If Lumps gets his mum, he carries her down the Long Stairs.

**The mystery**
- _learn:_ The Bottom's soup keeps the digesters alive. Mina is alive. She remembers Rory. She forgives them in one second.
- _suspect:_ Hask is buying organs from the Gut (Agenda: 'UP THE HILL, priority').
- _withheld:_ Whose body the organs go into (Hask, Act V).

**Objectives**
1. meet lumps at the long stairs
2. get the choir's minutes
3. find the bottom's missing in the digester wall
4. stop the choir: stop the stomach bishop · **boss: THE STOMACH BISHOP**
5. decide who runs the gut · scene `p6b_deal_or_takeover`
6. get them out

#### Scene: `p6b_deal_or_takeover` (panels, 10 s, music: deal_sting)
- `  0` _Used at every district's DEAL / TAKEOVER choice. Split panels: the company boss with a contract on the left, the local group's leader with a crowbar on the right. The engine fills the faces from the district (Nonna / Pip, Gail / Wristband, Sevens / Nell, the Bishop / Lumps, Penny Plot / Old Pat)._
- `  1` [panel 1] _DEAL: they stay in charge. they owe you. they'll remember._ (SIGN)
- `  3` [panel 2] _TAKEOVER: the little guys run it. the company won't forget._ (CRACK)
- `  6` _the mission's own district_choice choice runs here; the pick slams in as a stamp: DEAL or TAKEOVER_ → CHOICE: district_choice

#### Talk: `then` (with LUMPS)
- **[start]**
  - _Lumps at the bottom of the Long Stairs with a crowbar in one hand and the yellow soup in the other._
  - **LUMPS:** pages first. then mum. you said.
  - **LUMPS:** it's then.
  - ➤ _"it's then."_ → go
  - ➤ _"(if you promised Dot) i promised her."_ → promised (if flag:promised_dot)
- **[promised]**
  - _He nods, once. His eyes are wet and it isn't sunset._
  - **LUMPS:** she told you not to. i heard her. she says that about all the good promises.
  - → go
- **[go]**
  - **LUMPS:** ok. nine hundred and ninety-nine stairs. then the gut. then mum. i'll count.

#### Talk: `soup_truth` (with BIG SAUCE SHARON)
- **[start]**
  - _Sharon stops you at the kitchen door with a ladle across the doorway._
  - **BIG SAUCE SHARON:** before you go in. you should know what the soup's for. you asked me once and i didn't say.
  - **BIG SAUCE SHARON:** gristle don't eat it. they feed it to the wall. to the ones in the wall. so they don't go soft. so they keep talking.
  - **BIG SAUCE SHARON:** i found out a year ago. a choir lass let it slip. every pot i've sent up that hill for twenty years has been dinner for dot. for everyone.
  - _her voice cracks* i could've stopped. i'd have starved them. so i didn't stop._
  - ➤ _"you kept them alive."_ → alive
  - ➤ _"why didn't you tell lumps?"_ → tell
- **[alive]**
  - **BIG SAUCE SHARON:** i kept them in the wall. that's not the same.
  - _she pushes a pot into your arms* take this. the yellow. it's dot's favourite._
  - _does: give:yellow_soup_
- **[tell]**
  - **BIG SAUCE SHARON:** because he'd have gone in. and he'd be in the wall. and then who'd carry the fridges.
  - _she pushes a pot into your arms* take the yellow. it's her favourite._
  - _does: give:yellow_soup_

#### Talk: `trade` (with SISTER AGENDA)
- **[start]**
  - _Sister Agenda at her pew-desk. She's already open at the right page._
  - _sung* the nine, the nine... *not sung* you want the nine. and the old woman. truck forty-four. i wrote it all down._
  - ➤ _"(if you chased the truck) truck forty-four. i saw it."_ → saw (if flag:chased_truck)
  - ➤ _"(if you did Choir Practice) i brought your voice box."_ → voice (if done:sq_gut_choir_practice)
  - ➤ _"please. i'll owe you."_ → owe
- **[saw]**
  - **SISTER AGENDA:** you saw it. then you know. they're in the east wall, by the feed dock. go quickly. the wall's hungry today.
  - _does: flag:found_the_nine_fast_
- **[voice]**
  - _She takes the voice box and holds it against her throat, and for one line she sings in a voice that is completely her own.* thank you. east wall. by the feed dock. go._
  - _does: flag:found_the_nine_fast_
- **[owe]**
  - **SISTER AGENDA:** everyone owes. it's the only thing this city makes. ...east wall. somewhere. i'll mark the pages. it'll take you longer.

#### Talk: `late` (with MINA)
- **[start]**
  - _The east wall, by the feed dock. The nine, grown into the warm pink tissue at different depths, some chatting, some asleep. Dumpling's dad, waving. Old Ken. And further in, up to her waist, an old woman with a grey braid and Mall Rat climbing gloves, her eyes closed, her lips moving._
  - _Dot, nearby, sees you first* oh! plastic! mina, mina love, wake up. it's them. it's the one i told you about._
  - _The old woman opens her eyes. She looks at your face for a long time. Then at the barcode. Then at your knee._
  - **MINA:** ...you're late.
  - ➤ _"i know."_ → know
  - ➤ _"mina?"_ → mina
  - ➤ _"(cold) do i know you?"_ → cold (if drift>=3)
- **[know]**
  - _Something in her face gives way and is put back, fast, the way you'd put a plate back on a shelf before it falls._
  - **MINA:** sixty-one years. you'd better have a good excuse.
  - _she reaches out with a gloved hand. You take it. It's warm. The wall is warm. Her hand is warmer._
  - → memory
- **[mina]**
  - _She laughs, one short laugh, and it turns into something else halfway._
  - **MINA:** mina. yes. you used to say it like that when you couldn't find me in the shop. 'mina?' like a question you already knew the answer to.
  - _she reaches out with a gloved hand. You take it._
  - → memory
- **[cold]**
  - _She holds your gaze. She doesn't flinch._
  - **MINA:** no. no, you don't. that's all right.
  - **MINA:** i remember enough for both of us. take my hand anyway. humour an old woman.
  - → memory
  - _does: flag:mina_cold_meeting_
- **[memory]**
  - _If Drift is low, a flash: a strawberry keyring on a backpack, a small hand in yours at a crossing, a voice saying 'rory, the green man'. If Drift is high, nothing. Just her hand._
  - **MINA:** i waited at the gate till mrs. okafor made me go. then i waited in the vents. then i waited here.
  - **MINA:** don't you dare apologise. you were coming. i know you were coming. you'd have been on time if anyone had let you.
  - ➤ _"i was coming. i'm here now."_ → here
  - ➤ _"i don't remember you. i'm sorry."_ → sorry
- **[here]**
  - _She squeezes your hand twice, quickly, like a signal from a long time ago._
  - **MINA:** then get me out of this wall, rory. my legs have gone to sleep for two months.
  - _does: flag:mina_reunited, drift:-1_
- **[sorry]**
  - **MINA:** that's all right. you've got a lot of me missing. i've got a lot of you. we'll swap.
  - **MINA:** now get me out of this wall. my legs have gone to sleep for two months.
  - _does: flag:mina_reunited_

#### Talk: `home` (with MINA)
- **[start]**
  - _The Long Stairs, going down. The freed come out of the Gut blinking, wrapped in Choir robes, held up by Bottom people who've come up the stairs for them._
  - _If Dot is free: Lumps carries her down on his back, counting out loud, both of them crying, Dot telling him off for crying._
  - _If Dot was kept as collateral: Lumps walks down beside you, empty-handed, not counting._
  - _Dumpling runs up the stairs three at a time to their dad and stops calling you ghost._
  - **DUMPLING:** CHANGE! change! you got him! you got my dad!
  - _Mina, leaning on you, watching all of it._
  - **MINA:** this is the bottom, then. i lived on the top terrace forty years. i never once looked at it from up here.
  - ➤ _"i'll get you a blanket."_ → blanket
  - ➤ _"mina. tell me about me."_ → tell
- **[blanket]**
  - **MINA:** get me tea. a blanket's for old people.
- **[tell]**
  - _She thinks for a long time._
  - **MINA:** you were always running. you ran for buses you didn't need. you ran to the shop. you ran up the stairs to the flat so you could say you'd done it in forty seconds.
  - **MINA:** and you always came back for me. every single time. except once.
  - **MINA:** ...i'll tell you the rest over tea. there's a lot of rest.
  - _does: flag:mina_told_rory_

#### Choice: The Bishop is down. The Choir has stopped mid-note. The Gut is holding its breath. Who runs it?
- **DEAL: Gristle & Sons stays, stops buying from ☺ CORP, lets the outer wall go**: The Bishop, smiling through a broken jaw, agrees: no more trucks from ☺ CORP, and the outer wall is released (Mina, Dumpling's dad and seven others). Dot is in the deep wall; he keeps her 'as collateral' until the contract is honoured. Lumps hears it. The Choir keeps singing, so the old digesters live. Gristle sells you organs at a discount and sends a choir to the raid.
- **TAKEOVER: the Bottom takes the Gut**: Lumps puts the crowbar into the deep wall and the Gut, without its song, lets go. Everyone from the Bottom comes out, Dot on Lumps' back. But the Choir stops singing for good, and the digesters who've been in the wall for forty years and more don't survive coming out; Sister Agenda writes every name. The Gut becomes the Bottom's, raw and dangerous, and Gristle & Sons is hostile everywhere.

**Reward:** 900 coupons, lt_boss_bishop
**Review card:** EXCEEDS EXPECTATIONS. you brought the missing home. / MEETS EXPECTATIONS. / 

---

### 21. PROPERTY VALUES `m21_property_values`
_Evergreen Acres is the only district on the Schedule with something booked at 03:00: 'CHARGE'. Every window has a mannequin family waving._

**Where:** The Cul-de-sac (EVERGREEN ACRES), The HOA Clubhouse (EVERGREEN ACRES), Garage 03 (EVERGREEN ACRES), The Shelter (EVERGREEN ACRES)  
**Who:** LINDA FAIRWAY, THE HOA, WEE GORDO, THE MAILMAN  
**Giver:** WEE GORDO · **Needs:** m18_nine_kilometres

**Mechanic hook:** mow lawns to stop the HOA regrowing, steal a militia golf cart, and swing the porch gutters round the cul-de-sac _(uses: fire (the cigarette, flame arrows), cars and traffic, the grapple)_

**Beats**
- Evergreen: perfect lawns, a laugh track you can hear in the street, a mannequin family in every window waving at the same time.
- Linda Fairway and the HOA: 'your lawn is 2 mm too long.' You're fined on sight. Every fine is a debuff.
- Garage 03 behind any house: a charging dock with a ☺ CORP cable. At 03:00 the families walk into their garages and plug themselves in.
- Down into the shelter where Evergreen waited out the Long Dark: the pilot agreement on the wall. The families are recordings of the dead, loaded with the Schedule. Some of them are Linda's own family.
- Linda, in the shelter, is eleven years old again. The first thing she saw when they came up was the dead city, and she decided it wasn't there.
- The HOA rises from the lawns. Boss fight: THE HOA.
- Choice: unplug Evergreen's pilot (the families stop, forever) or leave them waving.

**The mystery**
- _learn:_ Workforce Restoration has a pilot: Evergreen's mannequin families are the Machine's dead with the Schedule loaded. They're delivered through the Lates at 03:00 and update every night. Loaded with the Schedule, the dead are cheerful, tidy and never ask anything.
- _suspect:_ The Lates' 03:00 'door' is the delivery route.
- _withheld:_ The scale of it (m23).

**Objectives**
1. find out what evergreen charges at 03:00
2. look in a garage at 03:00 · if clock.evergreen=03:00-03:30
3. get into the shelter
4. survive the homeowners association · **boss: THE HOA**
5. decide about the pilot

#### Talk: `fined` (with LINDA FAIRWAY)
- **[start]**
  - _A perfect cul-de-sac. Sprinklers ticking. A laugh track from nowhere. In every window, a mannequin family: mum, dad, two kids, waving. At exactly the same time._
  - _Linda Fairway walks up the drive, smiling, clipboard out._
  - **LINDA FAIRWAY:** hello! you must be new. we don't get new.
  - **LINDA FAIRWAY:** your lawn is 2 mm too long.
  - **LINDA FAIRWAY:** i'm sorry? oh, you don't have a lawn. that's worse. that's a fine.
  - ➤ _"what are the people in the windows?"_ → windows
  - ➤ _"what happens at 03:00?"_ → three
- **[windows]**
  - **LINDA FAIRWAY:** the families? they wave. isn't that nice? they always wave.
  - **LINDA FAIRWAY:** they're so tidy. they never complain. property values have never been higher.
  - → three
- **[three]**
  - _The smile doesn't move at all._
  - **LINDA FAIRWAY:** per section four, the bylaws are not to be discussed after dark. and per section nine, the dark is not to be discussed.
  - _does: flag:fined_by_hoa_

#### Talk: `shelter` (with LINDA FAIRWAY)
- **[start]**
  - _The shelter under the cul-de-sac: concrete, bunks, a mural of a sunny street painted by children, thirty years of tally marks. On the wall, framed like a certificate: ☺ CORP WORKFORCE RESTORATION · PILOT AGREEMENT · EVERGREEN ACRES HOA. Signed: L. Fairway. Countersigned: M. Hask._
  - _Linda is sitting on a bottom bunk. She's taken her cardigan off. She looks small._
  - **LINDA FAIRWAY:** i was born down here. i was eleven when the door opened.
  - **LINDA FAIRWAY:** everyone went up the stairs cheering, and the first thing i saw was the city. all of it. the way it was. the valley. the bodies.
  - **LINDA FAIRWAY:** and i decided it wasn't there.
  - ➤ _"the families are the dead."_ → dead
  - ➤ _"you signed this."_ → signed
- **[dead]**
  - **LINDA FAIRWAY:** they're recordings. from the machine. the nice lady from the pilot programme sends them through the lates at three in the morning. they update at three. they charge.
  - _she looks at the mural.* the dad in number four is my dad. he died the day before we came up. he waves at me every morning. he's never once asked how i am._
  - → signed
  - _does: flag:knows_pilot_
- **[signed]**
  - **LINDA FAIRWAY:** the lawns are perfect. nobody complains. nothing bad has happened here in forty years.
  - _She looks at you, and she's eleven.* please don't make it be there again._
  - _does: flag:knows_pilot_

#### Choice: In every garage, a family is plugged into a ☺ CORP cable. You can pull Evergreen's main feed.
- **unplug the pilot**: Every mannequin in Evergreen stops mid-wave and stays like that, hand up, forever. Linda sits on her lawn beside her father and doesn't move for a day. ☺ CORP loses its pilot data (the Restoration's Act IV defences are slower to update). The HOA is hostile to you for the rest of the game; in LATE, Linda plants vegetables.
- **leave them waving**: The families keep waving. Linda thanks you very quietly and hates you a little. The HOA becomes a grudging ally (its militia holds Dividend Road's lower junction in the raid). Evergreen is the model for the ON TIME ending.

**Reward:** 700 coupons, lt_boss_hoa
**Review card:** EXCEEDS EXPECTATIONS. lawn mowed. / MEETS EXPECTATIONS. fined eleven times. / SEE ME. your lawn is 40 cm too long.

---

### 22. THE WAITING ROOM `m22_the_waiting_room`
_In the Lates it has been the same Tuesday for sixty-one years. Pauline from Accounts knows every second of it, and she knows a man who has been late for the same meeting twenty-two thousand times._

**Where:** The Waiting Room (THE LATES), The Canteen (THE LATES), Remainder Downtown Office (THE LATES), Tuesday Tower (THE LATES)  
**Who:** PAULINE FROM ACCOUNTS, THE PERPETUAL TUESDAY, GUS  
**Giver:** PAULINE FROM ACCOUNTS · **Needs:** m18_nine_kilometres

**Mechanic hook:** the Lates teaches Loops (fall forever, keep the speed); freeze or rewind Neville to break his loop _(uses: loops, frost and shatter, tv remote (pause / rewind))_

**Beats**
- The Waiting Room: infinite, with chairs. Pauline finds you, because you're new, and nobody is ever new.
- She knows the loop: 09:00-17:30, then 09:00 again. Loopers don't age. She's watched a door open in the sky at 03:00 in the gap of the loop.
- To get to 03:00 you have to get the loop to let you stay past 17:30. It resets every time Neville Brisk misses his meeting.
- Neville: the man who left the Remainder downtown office at 09:00 with an envelope for a 16:59 meeting in the Spire. He's become the Perpetual Tuesday: a hundred copies of himself, running.
- Boss fight: THE PERPETUAL TUESDAY. The fight loops every 60 s, damage carries over, your past self's bullets replay.
- Beaten, one man hands you the envelope: 'could you take this? i'm late.' Inside: Remainder's revised Q4 numbers. TARGET MET (+0.5%).

**The mystery**
- _learn:_ The Q4 numbers were revised that morning: the divisions hit target by 0.5%. Option C wasn't necessary. The memo never arrived.
- _suspect:_ Hask's 'half a percent' call at 17:10 was this. She knew. The world ended over a late memo, or over something worse.
- _withheld:_ That Hask launched knowing (Act V).

**Objectives**
1. find somebody who isn't waiting
2. have lunch with pauline (it's lasagne)
3. find neville at the remainder office before 09:01
4. get neville to his meeting · **boss: THE PERPETUAL TUESDAY**

#### Talk: `new` (with PAULINE FROM ACCOUNTS)
- **[1730]**
  - **PAULINE FROM ACCOUNTS:** it resets. everyone forgets. i don't. i don't know why. i think i'm too stubborn to reset.
  - **PAULINE FROM ACCOUNTS:** come and have lunch. it's lasagne. it's been lasagne for twenty-two thousand days.
- **[start]**
  - _The Waiting Room: chairs to the horizon, a ticket machine on ticket 0, fluorescent hum. A woman in a 61-year-old cardigan with a mug that says WORLD'S OKAYEST ACCOUNTANT stands up and stares at you._
  - **PAULINE FROM ACCOUNTS:** you're new.
  - **PAULINE FROM ACCOUNTS:** nobody's new. this is very exciting and i hate it.
  - **PAULINE FROM ACCOUNTS:** i'm pauline. accounts. i've been here since 09:00. that's twenty-two thousand days ago, give or take. i keep count.
  - ➤ _"how do you know it's been that long?"_ → count
  - ➤ _"what happens at 17:30?"_ → 1730
- **[count]**
  - _She shows you the notebook. Tiny handwriting. Every page the same day, timestamped to the second, with small differences circled._
  - **PAULINE FROM ACCOUNTS:** i write down everything. the lift dings at 09:04. it's empty. it's always empty. gus drops his fork at 12:41. at 17:30 it all goes back to 09:00. except me. i keep the notebook in my head.
  - → 1730

#### Talk: `loop` (with PAULINE FROM ACCOUNTS)
- **[start]**
  - _The canteen. Gus drops his fork at 12:41, exactly. Pauline doesn't look._
  - **PAULINE FROM ACCOUNTS:** the loop resets when one man misses one meeting. neville brisk. remainder industries. he leaves the downtown office at 09:00 with an envelope for a 16:59 in the spire. he never gets there.
  - **PAULINE FROM ACCOUNTS:** i've tried to help him four thousand times. i've driven him. i've carried him. once i tied him to a bus.
  - **PAULINE FROM ACCOUNTS:** he's not a man any more. he's... a lot of men. you'll see.
  - ➤ _"what's in the envelope?"_ → envelope
  - ➤ _"what's at 03:00?"_ → door
- **[envelope]**
  - **PAULINE FROM ACCOUNTS:** numbers. he says 'it's important, it's very important, it's numbers'. he's from remainder. it's always numbers.
  - → door
- **[door]**
  - _She puts her fork down._
  - **PAULINE FROM ACCOUNTS:** nobody else has ever asked me that.
  - **PAULINE FROM ACCOUNTS:** the loop has a gap. 17:30 jumps to 09:00, but if you're awake, you feel the bit in between. an hour where nobody is. i've been awake in it.
  - **PAULINE FROM ACCOUNTS:** at 03:00 a door opens in the sky over the waiting room. trucks come through it from nowhere. they go to evergreen.
  - **PAULINE FROM ACCOUNTS:** if neville gets to his meeting, the loop might let us stay past 17:30. then you can see the door for yourself.
  - _does: flag:pauline_told_door_

#### Talk: `envelope` (with THE PERPETUAL TUESDAY)
- **[start]**
  - _The copies peel away and fall, one by one, into the looping street, and fade. One man is left: thirty-four, brown suit, sweat-soaked, holding a manila envelope with REMAINDER INDUSTRIES · URGENT · BOARD 16:59 on it._
  - **THE PERPETUAL TUESDAY:** sorry i'm late. sorry. sorry i'm late.
  - **THE PERPETUAL TUESDAY:** could you take this? i'm late. it's important. it's very important. it's numbers.
  - _He presses it into your hands, and his face is the face of someone putting down something heavy for the first time in a very long time._
  - ➤ _"*open it*"_ → open
- **[open]**
  - _Inside: one sheet. REMAINDER INDUSTRIES · Q4 REVISED (09:00) · ALL DIVISIONS · TARGET MET (+0.5%). A pencilled note: 'the 17:30 thing won't be needed now. N.'_
  - _Neville sits down on a bench. He looks at his watch. It's moving._
  - **THE PERPETUAL TUESDAY:** they didn't need to do it. did they. whatever it was.
  - **THE PERPETUAL TUESDAY:** i was carrying the reason not to. all day. i was just late.
  - _does: give:late_memo, flag:read_late_memo_

**Reward:** 700 coupons, late_memo, lt_boss_perpetual_tuesday
**Review card:** EXCEEDS EXPECTATIONS. you've seen this one. / MEETS EXPECTATIONS. it's still tuesday. but less. / SEE ME. you were late.

---

### 23. WORKFORCE RESTORATION `m23_workforce_restoration`
_At 03:00, in the hour nobody's booked into, a door opens in the sky over the Lates. Behind it is what ☺ CORP has been planning for the dead._

**Where:** Tuesday Tower (THE LATES), The Door in the Sky (THE LATES), The Restoration Warehouse (THE LATES)  
**Who:** PAULINE FROM ACCOUNTS, WEE GORDO  
**Giver:** PAULINE FROM ACCOUNTS · **Needs:** m22_the_waiting_room, m21_property_values, m19_organ_donor

**Mechanic hook:** the Missing Hour is grey: night vision goggles and a grapple swing down the cable trunks above the rows _(uses: night vision goggles, the grapple)_

**Beats**
- With Neville delivered, the loop lets you stay past 17:30. You wait with Pauline and Gordo on Tuesday Tower.
- C13: 03:00, the grey, the door, the warehouse: mannequin bodies to the horizon, cables to the Machine's archive, the Master Clock's schedule. PROTOTYPE 0 (SCHEDULE NOT LOADED).
- Walk the rows (playable): lanyards with names from the archive. If you look, you can find Cale's colleagues, the man with the fish tank, a lanyard that says E. SALLOW (spare).
- The mannequins wake and turn. Restoration Security (HR Tactical) comes through the door. Escape down the grey stairs before 04:00, when the hour closes.
- Pauline on the tower after, watching 04:00 become 09:00: 'that's what they want the whole city to be. this. tuesday, forever. just tidier.'

**The mystery**
- _learn:_ Workforce Restoration: every recording in the Machine loaded into a mannequin body and run on the Master Clock, forever, unpaid, obedient. You were the prototype. Your recording came out without the Schedule because you were 'terminated'. ☺ CORP was studying you so it could delete you. There's a spare body for Overtime too.
- _suspect:_ The Bottom isn't in the plan at all. Living people who can't pay aren't on the schedule.
- _withheld:_ The living are being sold to Vacancy (Act IV).

**Objectives**
1. wait for 03:00 on tuesday tower
2. _(scene)_ · scene `c13_workforce_restoration`
3. walk the rows
4. get out before 04:00 · timer 300s

#### Scene: `c13_workforce_restoration` (cinematic, 92 s, music: missing_hour)
- `  0` _The Lates, 02:59. Pauline from Accounts stands with you and Gordo on the roof of Tuesday Tower, holding her notebook. Everything is the yellow-beige Tuesday it always is._
- `  4` **PAULINE FROM ACCOUNTS:** twenty-two thousand nights i've watched this. you're the first person i've watched it with.
- `  8` _03:00. The Lates goes grey. Not dark: grey, like an unloaded texture. The hold music stops. Every Looper freezes mid-step. The loop has a gap in it, and you're standing in it._
- ` 14` _In the sky over the waiting room, a rectangle of light opens: a door. A plain office door, fifty metres up, ajar._
- ` 18` **WEE GORDO:** ...i was born in this hour.
- ` 21` _A staircase of grey steps assembles itself under your feet, one at a time, as you walk up to the door. Through it._
- ` 31` _A warehouse the size of a district. Fluorescent strips to the horizon. Mannequin bodies in rows, standing, perfectly still, thousands, hundreds of thousands, each with a ☺ CORP lanyard, each with a cable running from the back of its neck up into the dark._
- ` 42` _The cables run together into trunks, the trunks into one great cable that runs out of a wall marked ARCHIVE LINK: LOST & FOUND. The Machine._
- ` 48` _On the far wall, the size of a cliff, the Master Clock's schedule: every body has a slot. 09:00 START. 17:30 RECHARGE. 03:00 UPDATE. Forever. Under it, a banner: WORKFORCE RESTORATION. THE DEAD DON'T MIND._
- ` 58` **WEE GORDO:** they're going to put everyone in the machine into these. everyone who died at 17:30.
- ` 63` **WEE GORDO:** a recording can be told what time it is. they'll never stop. they'll never ask for anything.
- ` 68` _A screen on a console near the door. A mannequin silhouette that's yours: your tilt, your wrong knee. A label._
- ` 72` **PROTOTYPE 0 (SCHEDULE NOT LOADED)**
- ` 76` _Beside it, a status line: CALE R. 4417 · TERMINATED 17:29:41 · NO ACTIVE CONTRACT · SCHEDULE FIELD EMPTY · RECOMMEND: STUDY, THEN DELETE._
- ` 82` **WEE GORDO:** ...you're the one that doesn't work.
- ` 86` _Somewhere far down the rows, a single mannequin turns its head toward you. Then the next one. Then the row._
- ` 90` **PAULINE FROM ACCOUNTS:** *from the door, very calm* it's 03:04. we should go.

#### Talk: `rows` (with WEE GORDO)
- **[start]**
  - _Barks as you walk the rows; each lanyard can be read:_
  - _a lanyard: K. OSEI · SENIOR ANALYST · 60TH FLOOR. You knew her. Her desk was by the window. She gave you a biscuit on your first day._
  - _a lanyard: D. PRYCE · FACILITIES. He's holding a fish tank. The body is holding a fish tank._
  - _a lanyard: E. SALLOW · SPARE (3 of 3)._
  - **WEE GORDO:** they've even got spares for him.
  - _a lanyard, at the end of a row, a single empty dock with no body in it: CALE R. 4417 · PROTOTYPE 0 · RETURN TO DOCK._
  - **WEE GORDO:** ...they kept you a parking space.

#### Talk: `tidier` (with PAULINE FROM ACCOUNTS)
- **[start]**
  - _Tuesday Tower, 04:00. The grey drains away. The door folds into nothing. The sky goes yellow-beige. 04:00 becomes 09:00 with a little jolt, and below, the Loopers start their Tuesday again._
  - **PAULINE FROM ACCOUNTS:** that's what they want the whole city to be. this. tuesday, forever.
  - **PAULINE FROM ACCOUNTS:** just tidier.
  - _She opens her notebook to a clean page for the first time in twenty-two thousand days and writes: 03:00. warehouse. tell someone._
  - **PAULINE FROM ACCOUNTS:** i'm telling you. i've never had anyone to tell.
  - ➤ _"we'll stop it."_ → stop
  - ➤ _"what happens to you if we do?"_ → you
- **[stop]**
  - **PAULINE FROM ACCOUNTS:** good. please. i'd like a wednesday. i'd like to find out it's horrible.
- **[you]**
  - **PAULINE FROM ACCOUNTS:** i find out i'm forty-six and everyone i knew outside is dead.
  - _she shrugs* i've had twenty-two thousand days to get used to the idea. i'm ready for one day to not get used to it._

**Reward:** 500 coupons
**Review card:** EXCEEDS EXPECTATIONS. you found your parking space. / MEETS EXPECTATIONS. you got out by 04:00. / SEE ME. you were restocked.

---

### 24. THE SPLIT `m24_the_split`
_Marion Hask calls you on the Machine's own terminal with an offer, and the Bottom splits three ways over what to do about it._

**Where:** The Lost & Found (THE BOTTOM), Dale's Shed (THE BOTTOM)  
**Who:** MARION HASK, DALE, AUNTIE SPREADSHEET, LUMPS, WEE GORDO, MINA, PRITCHARD  
**Giver:** AUNTIE SPREADSHEET · **Needs:** m23_workforce_restoration, m20_the_missing

**Mechanic hook:** a talking mission: the split is about what you are, and your installed implants change which lines you're offered _(uses: bio-implants)_

**Beats**
- C14: Hask on Dale's terminal. The Long Dark footage. 'the dead do not mind working.' The offer: a name, a job, a life that doesn't end.
- Pritchard rings back on the pager to book you a slot. You can talk to him.
- Dale's confession: the monthly maintenance reports, the batteries, forty years. That's how she got in. And Mina: she asked him every year.
- If Mina is free, she slaps Dale. He says thank you.
- If you deferred forgiving Auntie, you can do it now.
- C15: the split. Lumps: take the deal for the Gut's people. Gordo: blow up the Master Clock at 03:00. Auntie: publish all six pages.
- You choose whose plan the raid follows.

**The mystery**
- _learn:_ Dale has reported to ☺ CORP Facilities every month for forty years. Hask's case: the Long Dark, the famine; the Schedule kept the Spire alive. Lumps has been writing to Pritchard.
- _suspect:_ Hask needs you: a prototype that came out free is a flaw she can't afford.
- _withheld:_ Why you came out free, in her words (C20). What she did at 17:10 (Act V).

**Objectives**
1. _(scene)_ · scene `c14_the_offer`
2. answer the pager
3. talk to dale
4. the whole bottom's waiting · scene `c15_the_split`

#### Scene: `c14_the_offer` (cinematic, 64 s, music: hask_theme)
- `  0` _The Lost & Found, late. The Machine's terminal by Dale's shed flickers on by itself. Its little green screen goes white._
- `  4` **DALE:** ...that's not me.
- `  6` _On the screen, in a white office with one window, Marion Hask: silver hair in a perfect knot, a white suit buttoned to the throat, a surgical scar just visible above the collar. Perfectly calm. A clock behind her. She is exactly on time._
- ` 12` **MARION HASK:** Good evening. You are four minutes early. I appreciate that.
- ` 17` **MARION HASK:** You have been inside my warehouse. I would like to show you why it exists.
- ` 21` _The screen cuts to old ☺ CORP security footage, grainy: the Long Dark. Ash falling for years. Crowds at the Spire's gates in the snow. Fires in the streets. A child eating paper. A food riot at a Big Value. Bodies stacked in the valley that's now the Gut._
- ` 33` **MARION HASK:** That was the city without a schedule. I watched it from that window for thirty years.
- ` 38` **MARION HASK:** Inside the Spire, we rationed air, water, food and light to the minute. We were late to nothing. Nobody inside starved.
- ` 44` **MARION HASK:** The Restoration feeds everyone. The dead do not mind working. I have asked them.
- ` 49` **MARION HASK:** You could have a name, a job, and a life that does not end. Your name, if you like. Cale. It is in my records.
- ` 55` **MARION HASK:** Or you could go back in the bin.
- ` 58` **MARION HASK:** My assistant will book you. Good night.
- ` 61` _The screen goes green. Dale is staring at the terminal. Then at you. He knows exactly how she got in._

#### Scene: `c15_the_split` (cinematic, 66 s, music: the_split)
- `  0` _The Lost & Found, the next morning. Everyone at the long table. Four pages on the wall now. Auntie at the head. Lumps with his hands flat on the table. Gordo standing. If Mina was freed, she sits next to you, wrapped in a blanket._
- `  6` **LUMPS:** she's offering. hask. she's offering jobs. for the ones in the gut. pritchard wrote to me. they'd get them out. all of them. mum.
- ` 13` **WEE GORDO:** she's offering them a schedule. she's offering them a leash.
- ` 17` **LUMPS:** a leash is better than the wall, gordo.
- ` 20` **WEE GORDO:** is it? ask the mannequins in evergreen. oh, you can't. they're waving.
- ` 24` **WEE GORDO:** 03:00. the missing hour. nobody's booked. we go up the hill in the one hour they can't see, and we blow up that clock. no clock, no schedule, no restoration. no new bosses.
- ` 33` **AUNTIE SPREADSHEET:** and then what, gordon? who keeps the lights on? who feeds the spire's thousands? who stops the next one?
- ` 39` **AUNTIE SPREADSHEET:** we publish. all six pages. option c on every screen in the city. every debt they ever collected, void. then they have to sit at a table with us, because they've got nothing left to sell.
- ` 47` **WEE GORDO:** a table. with the people who ended the world.
- ` 50` **AUNTIE SPREADSHEET:** yes. because the alternative is a world with nobody at the table at all.
- ` 55` _(if fate.mina=freed)_ **MINA:** *quietly, to you* you've got that face. the one you made when you had to pick a cereal. pick, rory.
- ` 58` _Silence. Lumps, Gordo and Auntie all look at you. Nobody tells you what to say._
- ` 63` → CHOICE: whose_plan

#### Talk: `booking` (with PRITCHARD)
- **[start]**
  - **PAGER:** *BEEP BEEP BEEP. A tinny voice, fast, breathless.*
  - **PRITCHARD:** hello! hi. this is owen pritchard, executive assistant to the chief punctuality officer. sorry. sorry, that's my 23:00 alarm. and my 23:01.
  - **PRITCHARD:** ms. hask would like to offer you an onboarding interview. i have a four-minute window on the 3rd at 22:16. or i can make one. i'll make one.
  - ➤ _"are you the one who answers lumps' letters?"_ → lumps
  - ➤ _"what's onboarding?"_ → onboard
  - ➤ _"no."_ → no
- **[lumps]**
  - _a long silence on the pager_
  - **PRITCHARD:** ...he writes very nicely. he always asks how i am. nobody asks how i am. i'm booked.
  - **PRITCHARD:** i've been lowering his mother's price. don't tell anybody. i'll be deleted. i'll be rescheduled into a skip.
  - _does: flag:pritchard_soft_
- **[onboard]**
  - **PRITCHARD:** a name, a lanyard, a slot. you'd be... um. the template. for the rest. they'd all be a bit like you. but on time.
  - _quieter* there are eleven thousand four hundred and two people from the bottom who aren't on the staffing table. i typed every one. i just... thought you should know that._
  - _does: flag:pritchard_warned_
- **[no]**
  - **PRITCHARD:** that's... that's ok. i'll put you down as 'tentative'. i put everyone down as tentative. it's the kindest box.

#### Talk: `batteries` (with DALE)
- **[start]**
  - _Dale's shed. Forty years of batteries, stacked like bricks, floor to ceiling, every one stamped ☺ CORP FACILITIES. A pager on a nail._
  - **DALE:** ...she got in through my terminal. because my terminal reports to her. every month. 'machine status: humming. tray: empty. anomalies: none.' for forty years.
  - **DALE:** they pay me in batteries. look at them. that's what i cost. that's what she costs.
  - **DALE:** the month you came out i wrote 'anomalies: one'. i didn't think. sixty years of habit. that's how they knew where to look.
  - ➤ _"why?"_ → why
  - ➤ _"did mina ask you to let me out?"_ → mina (if flag:knows_mina)
- **[why]**
  - **DALE:** because the bottom needed light. and because she was going to keep humming whether i fixed her or not, and if i didn't fix her they'd send someone who'd ask fewer questions.
  - **DALE:** ...those are reasons. they're not excuses. i know the difference. i've had a long time to learn it.
  - → mina
- **[mina]** _branch: fate.mina=freed → slap_
  - _He doesn't look up._
  - **DALE:** every year. new year's eve. she'd come down the stairs with a bottle and sit where you're standing and say 'is rory in there, dale?'
  - **DALE:** and i'd say 'i don't know, love. she doesn't give anything back.'
  - **DALE:** i knew. i could see the sim on the menu. i just never pressed it.
  - **DALE:** then she stopped coming. she got old. and then they took her. and the next week you walked off the edge of the map for the four hundredth time. and i pressed it.
- **[slap]**
  - **MINA:** *Mina is in the doorway. She's heard all of it. She crosses the shed in four steps and slaps Dale across the face, hard, with a Mall Rat glove.*
  - _Dale doesn't move.* ...thank you._
  - **MINA:** *She sits down next to him on a stack of batteries and takes his hand, the same way she took yours.* idiot.
  - _does: flag:mina_slapped_dale_

#### Talk: `pending` (with AUNTIE SPREADSHEET)
- **[start]**
  - _Auntie, at the long table, writing. Her notebook is open at the page that says 'pending.'_
  - **AUNTIE SPREADSHEET:** you said ask you again.
  - ➤ _"i forgive you."_ → yes
  - ➤ _"not yet."_ → no
- **[yes]**
  - _She crosses out 'pending' and writes 'forgiven. 1 entry.' in crayon. Her hand is very steady until the last letter._
  - **AUNTIE SPREADSHEET:** ...thank you, rory.
  - _does: flag:forgave_auntie, unflag:deferred_forgiveness, drift:-1_
- **[no]**
  - _She nods, and leaves it.* pending. that's fair. i'll take pending._

#### Choice: Lumps, Wee Gordo and Auntie are all looking at you. Whose plan does the Missing Hour raid follow?
- **lumps: take what she's offering for the gut's people, then turn it on her**: Act IV's m28 is HEADCOUNT: you play Hask's onboarding to get the Bottom's people on the staffing table and Dot out (if she's still in), then use the access to open the Spire at 03:00. Lumps is with you in everything. Gordo goes off on his own with his charges. In ON TIME the Gut's people are spared and given jobs.
- **gordo: blow up the master clock in the missing hour**: Act IV's m28 is DEMOLITION: charges on the Clock's power feeds (the Number Works substation, the Big Escalator) and a route up for the raid. Gordo is with you in everything. Lumps, if Dot is still in the Gut, goes to meet Pritchard alone. The LATE ending is the natural end of this road.
- **auntie: get the last two pages and publish option c**: Act IV's m28 is PRINT RUN: seize ☺ CORP News' broadcast relay and get the Price Press ready to print six pages on every tag in the city. Auntie goes up the hill with the raid herself. Gordo goes with his charges anyway; Lumps may go to Pritchard. The OFF THE BOOKS ending is the natural end of this road.

**Reward:** —
_Builder notes: every ending is still possible whatever the plan; the plan changes Act IV's missions, who stands where in the raid, and the endings' details._

---

### 25. TUESDAY AGAIN `m25_tuesday_again`
_Overtime comes for you in the Lates, where every minute happens again, and every time it happens he remembers a little more._

**Where:** The Waiting Room (THE LATES), Tuesday Tower (THE LATES)  
**Who:** MR. OVERTIME, PAULINE FROM ACCOUNTS  
**Giver:** — · **Needs:** m24_the_split

**Mechanic hook:** the loop fight: take a photo of where his weak point was and walk back into it next loop _(uses: loops, frost and shatter, instant camera, the grapple)_

**Beats**
- The Lates. Pauline warns you: 'he came through the door at 03:00. he's never come through the door before.'
- Boss fight: overtime_3 in the loop. His attacks are telegraphed from your last loop; he glitches more every loop.
- Loop four: he stops attacking. P16. 'i was going home at 17:30. why didn't i go home?'
- A conversation with him in the empty car park. What you say plants the talk-down in Act V.
- His time card is torn: Late Fees can't reach ★5 for a while.
- END OF ACT III.

**The mystery**
- _learn:_ Overtime is remembering: the door, 17:30, home. He has a wife. He was going home.
- _suspect:_ You can reach him.
- _withheld:_ June, the anniversary, the last phone call (his fragments, Act V).

**Objectives**
1. survive mr. overtime (again, and again) · **boss: MR. OVERTIME**
2. _(scene)_ · scene `p16_tuesday_again`

#### Scene: `p16_tuesday_again` (panels, 18 s, music: overtime_theme_low)
- `  0` [panel 1] (SLAM) _Overtime mid-slam in the Lates' looping car park._
- `  3` [panel 2] (SLAM) _The same panel. Identical. Except his tie is on the other shoulder._
- `  6` [panel 3] (sl...) _The same panel. The slam stops halfway. Static on his visor._
- `  9` [panel 4] _The same panel. He has stopped. His arms are by his sides. He's looking at his watch._
- ` 12` [panel 5] **MR. OVERTIME:** i was going home at 17:30. why didn't i go home?
- ` 16` **END OF ACT III**

#### Talk: `door` (with PAULINE FROM ACCOUNTS)
- **[start]**
  - **PAULINE FROM ACCOUNTS:** he came through the door at 03:00. he's never come through the door before.
  - **PAULINE FROM ACCOUNTS:** he's in the car park. he's been in the car park since 09:00. he's been doing the same slam for six hours. it's very loud.
  - **PAULINE FROM ACCOUNTS:** i think he's waiting for you. i think it's the only appointment he's got left.

#### Talk: `home` (with MR. OVERTIME)
- **[start]**
  - _The looping car park, empty. Overtime standing still in the middle of it with his arms at his sides, steam coming off him in the rain. His punch-clock heart ticks unevenly. He's holding his time card. It's torn down the middle._
  - **MR. OVERTIME:** i was going home at 17:30.
  - **MR. OVERTIME:** why didn't i go home?
  - ➤ _"because something happened at 17:30."_ → happened
  - ➤ _"you were in the lobby. you stopped me."_ → lobby
  - ➤ _"(cold) you're still on shift. get back to work."_ → cold (if drift>=3)
- **[happened]**
  - **MR. OVERTIME:** something happened. yes. there was a... the clocks. the clocks cracked.
  - _his visor flickers* and then i was at my desk. and it was 09:00. and everyone was absent. everyone's been absent for a very long time._
  - **MR. OVERTIME:** where does everyone go?
  - ➤ _"they died. everyone died at 17:30. you did too."_ → died
  - ➤ _"home. they went home."_ → homegentle
- **[lobby]**
  - _He looks at you. Really looks._
  - **MR. OVERTIME:** cale. cale, r. you were running.
  - **MR. OVERTIME:** i... punched your card.
  - _the punch-clock skips three beats.* that's not... that's policy. that was policy._
  - → happened
  - _does: flag:overtime_remembers_cale_
- **[died]**
  - _A very long silence. The rain stops in mid-air, the Lates' loop catching on something._
  - **MR. OVERTIME:** no. no, i'd have been told. there'd be a memo.
  - _he looks at his time card, the tear down the middle._
  - **MR. OVERTIME:** ...there was a phone. at the door. somebody on the phone. she said...
  - → end
  - _does: flag:told_overtime_he_died, flag:overtime_reached_
- **[homegentle]**
  - **MR. OVERTIME:** home. yes. everyone went home. and i stayed. i always stay. june says i always stay.
  - **MR. OVERTIME:** ...june.
  - → end
  - _does: flag:overtime_said_june, flag:overtime_reached_
- **[cold]**
  - _His posture straightens. The clock steadies. He's relieved._
  - **MR. OVERTIME:** yes. yes, of course. thank you. i'm on shift.
  - _he walks away, perfectly on time._
  - _does: flag:overtime_sent_back, drift:+1_
- **[end]**
  - _His punch-clock heart ticks back up to speed. He backs away from you, as if you're something hot._
  - **MR. OVERTIME:** i have to... i have an appointment.
  - _He goes. He's late. For the first time, he's late._

**Reward:** 900 coupons, lt_boss_overtime_3
**Review card:** EXCEEDS EXPECTATIONS. he's late. / MEETS EXPECTATIONS. you've seen this one. / SEE ME. you were stapled to tuesday.

---
