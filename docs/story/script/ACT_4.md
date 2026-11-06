# Act 4: "Quarterly Review"
_Who do you stand with?_

_Generated from `shared/story/content/missions/act4.js` and `scenes_act4.js`._

### 26. EXIT INTERVIEW `m26_exit_interview`
_At the edge of the world, the Tall Guy From HR can't be killed in his own forest. He just wants somebody to sign._

**Where:** The Last Bus Stop (THE MARGINS), The Gnome Field (THE MARGINS), The Edge (THE MARGINS), The Scary Forest (THE MARGINS), HR Cabin (THE MARGINS)  
**Who:** OLD PAT, THE JANITOR, THE TALL GUY FROM HR  
**Giver:** OLD PAT · **Needs:** m25_tuesday_again

**Mechanic hook:** Old Pat pushes you into the void to teach Void Edges; the canopy is a grapple route; the Tall Guy only moves when you look away _(uses: void edges, the grapple, the lasso)_

**Beats**
- The Last Bus Stop. The road ends in the void. Old Pat and the Margin Walkers stake gnomes to hold the ground. The Janitor mops the edge.
- Pat: Vacancy's Closing Agent keeps her page in a briefcase at the Show Home, and the Tall Guy walks the forest between here and there.
- The forest: he only moves when you don't look. You can't hurt him: his file says the forest is his place of work.
- The HR Cabin: filing cabinets to the ceiling. His file: Gerald Long, HR Business Partner, 31, volunteered for the void survey team on the Final Quarter. On loan to Vacancy. Never returned.
- In the file, an EXIT INTERVIEW form, unsigned. He's needed someone to sign him out for sixty-one years.
- Choice: sign it (he's released; a talk-down) or use the file to make him killable and fight him.
- C17: either way, at the edge, he gives you the SALE AGREEMENT: ☺ CORP has sold the Bottom to Vacancy, on completion of the Re-Merger.

**The mystery**
- _learn:_ ☺ CORP has already sold the Bottom, all plots and all occupants, to Vacancy Holdings. Completion: on Re-Merger. The living who can't pay aren't staff, so they're land. The void comes up the hill.
- _suspect:_ Vacancy's page of Option C is the Bottom's title deed.
- _withheld:_ —

**Objectives**
1. find the margin walkers
2. cross the forest
3. find his file in the hr cabin
4. his exit interview
5. _(automatic)_ · **boss: THE TALL GUY FROM HR** · if flag:fought_tall_guy
6. _(scene)_ · scene `c17_negative_space`

#### Scene: `c17_negative_space` (cinematic, 44 s, music: margins_drone)
- `  0` _The Margins at dusk. A road that ends in a glossy black nothing. On the edge, a little pastel house, half over the void. It creaks. It slides, very slowly, and goes in without a sound. The void reflects nothing._
- `  8` **OLD PAT:** that's the hendersons'. i had a gnome on it. it wasn't enough.
- ` 12` _Between the pines, the Tall Guy From HR, folding himself down to your height, which takes a while. He holds out a manila folder with both very long hands._
- ` 18` **THE TALL GUY FROM HR:** i'm sorry. i thought you should have this. somebody should read it before it happens.
- ` 23` _The folder: SALE AGREEMENT. THE BOTTOM (ALL PLOTS, ALL OCCUPANTS). ☺ CORP TO VACANCY HOLDINGS. COMPLETION: ON RE-MERGER. Mr. Deposit's old deed is stapled to the back as proof of title._
- ` 30` **THE TALL GUY FROM HR:** the living who can't pay aren't on the schedule. so they're not staff. so they're... land.
- ` 35` **THE TALL GUY FROM HR:** the void comes up the hill on completion. i'm very sorry. i'm only on loan.
- ` 40` _Behind him, at the edge, another house tilts._

#### Talk: `gnomes` (with OLD PAT)
- **[start]**
  - _The Gnome Field: hundreds of garden gnomes in rows on the last of the ground, facing the void like they're on guard. A tiny old woman in wellies hammers another one in._
  - **OLD PAT:** that's ken. he's holding the bus stop. good lad, ken.
  - **OLD PAT:** the void can't take what's occupied. vacancy's lawyers haven't found a way round it. so we occupy.
  - _she turns a gnome over: a name is painted under its feet. MARGARET ELLIS.* four hundred and twelve. one for everyone who's gone in._
  - ➤ _"i'm looking for vacancy's page."_ → page
  - ➤ _"*help her plant one*"_ → plant
- **[plant]**
  - _You hammer one in. She paints a name under it without asking you.* there. that's the hendersons. they went in this morning._
  - **OLD PAT:** you're a good lad. lass. lump. whatever you are. you're good.
  - → page
  - _does: standing.bottom:+2_
- **[page]**
  - **OLD PAT:** the closing agent keeps her papers in a briefcase at the show home. she never puts it down. she sleeps with it.
  - **OLD PAT:** between here and there's the forest. and in the forest's him. hr. you can't shoot him. people've tried. he just... asks for a quick word.
  - **OLD PAT:** the janitor says he's lonely. the janitor says goodnight to him. nobody else does.

#### Talk: `interview` (with THE TALL GUY FROM HR)
- **[start]**
  - _The HR Cabin. You've got his file open on a desk. GERALD LONG. HR BUSINESS PARTNER. AGE 31. PHOTO: a nervous young man with big ears and a kind face. STATUS: ON LOAN (VACANCY HOLDINGS · VOID SURVEY). RETURNED: —._
  - _The cabin door opens and he folds himself in, joint by joint, until his head is level with yours._
  - **THE TALL GUY FROM HR:** you found my file. nobody reads the files.
  - **THE TALL GUY FROM HR:** i volunteered. they said it was a two-week secondment. the void stretched me a bit. a lot. and nobody ever came to collect me.
  - **THE TALL GUY FROM HR:** you can't leave a job until someone signs you out. that's policy. i've been asking everyone. they run.
  - ➤ _"*sign the exit interview*"_ → sign
  - ➤ _"(read the file) your place of work is the forest. if i strike that out, you can be hurt."_ → fight
  - ➤ _"why didn't you just leave?"_ → leave
- **[leave]**
  - _He looks genuinely confused._
  - **THE TALL GUY FROM HR:** without signing out? that's... that's absence. i'd be absent.
  - **THE TALL GUY FROM HR:** i'm HR. i can't be absent. who would i report myself to?
  - → start2
- **[start2]**
  - _He holds out a pen, very gently, with a hand at the end of a very long arm._
  - ➤ _"*sign the exit interview*"_ → sign
  - ➤ _"(cross out his place of work) fight him"_ → fight
- **[sign]**
  - _You sign. Reason for leaving: you write whatever you like. (The game keeps it.)_
  - _He reads it. He reads it again. His shoulders come down about a metre._
  - **THE TALL GUY FROM HR:** thank you. thank you. that's... a very good exit interview. i'd give it a five.
  - **THE TALL GUY FROM HR:** i'll walk you to the edge. there's something you should see before i go. it's in my outbox. it's been in my outbox for a while.
  - _does: flag:signed_tall_guy, flag:tall_guy_resolved, standing.bottom:+3, drift:-1_
- **[fight]**
  - _You strike out PLACE OF WORK: THE FOREST. The cabin goes cold._
  - **THE TALL GUY FROM HR:** oh.
  - **THE TALL GUY FROM HR:** oh, that's... that's a disciplinary.
  - _his arms start to get longer._
  - _does: flag:fought_tall_guy, flag:tall_guy_resolved_

**Reward:** 600 coupons, sale_agreement, lt_boss_tall_guy
**Review card:** EXCEEDS EXPECTATIONS. you signed someone out. HR thanks you. / MEETS EXPECTATIONS. you had a quick word. / SEE ME. you looked away.

---

### 27. NEGATIVE SPACE `m27_negative_space`
_The deal closes today. Vacancy's Closing Agent is selling the Bottom to the void, and her page of Option C is the deed._

**Where:** The Show Home (THE MARGINS), The Edge (THE MARGINS), The Deposit Pile (THE BOTTOM), The Lost & Found (THE BOTTOM)  
**Who:** PENNY PLOT, OLD PAT, THE TALL GUY FROM HR, MR. DEPOSIT, AUNTIE SPREADSHEET  
**Giver:** OLD PAT · **Needs:** m26_exit_interview

**Mechanic hook:** blow survey agents off the Edge, lasso Penny's briefcase, and grapple between falling plots _(uses: shove and knockback, the lasso, void edges, the grapple)_

**Beats**
- The Show Home: a perfect show house on the edge, every plot sold marked by a pin on a map of the void. The Bottom is a cluster of red pins with 'PHASE TWO' written over it.
- Penny Plot: cheerful, monstrous, in a pink blazer over a hazmat suit. She tries to sell you a plot. She sold her own house at nineteen.
- Boss fight: PENNY PLOT, from the Show Home out onto the Edge, as she drops void bombs shaped like keyrings and the ground under you is sold off in chunks.
- Her briefcase: Vacancy's page. 'non-productive land clearance.' The Bottom listed as phase two.
- P6b: DEAL (Vacancy keeps the Margins, cancels the Bottom's sale, stops selling ground) or TAKEOVER (the Margin Walkers hold the edge).
- Back at the Lost & Found: five pages on the wall. Auntie: 'one left. it's on her desk.'

**The mystery**
- _learn:_ Vacancy page: void bombs for 'non-productive' districts that can't pay. The Bottom was always phase two. Option C planned for the living poor to be deleted, not just the dead to work.
- _suspect:_ The last page, on Hask's desk, ties it all together.
- _withheld:_ Page 6 (Act V).

**Objectives**
1. find the closing agent at the show home
2. stop the sale · **boss: PENNY PLOT**
3. take vacancy's page from the briefcase
4. decide who runs the margins · scene `p6b_deal_or_takeover`
5. take the page to auntie

#### Scene: `p6b_deal_or_takeover` (panels, 10 s, music: deal_sting)
- `  0` _Used at every district's DEAL / TAKEOVER choice. Split panels: the company boss with a contract on the left, the local group's leader with a crowbar on the right. The engine fills the faces from the district (Nonna / Pip, Gail / Wristband, Sevens / Nell, the Bishop / Lumps, Penny Plot / Old Pat)._
- `  1` [panel 1] _DEAL: they stay in charge. they owe you. they'll remember._ (SIGN)
- `  3` [panel 2] _TAKEOVER: the little guys run it. the company won't forget._ (CRACK)
- `  6` _the mission's own district_choice choice runs here; the pick slams in as a stamp: DEAL or TAKEOVER_ → CHOICE: district_choice

#### Talk: `viewing` (with PENNY PLOT)
- **[start]**
  - _The Show Home: scatter cushions, a bowl of plastic lemons, a kettle that's never been plugged in. On the wall, a huge map of the void with thousands of pins. Penny Plot in a pink blazer over a white hazmat suit, visor up, smile on._
  - **PENNY PLOT:** hello! you must be here for the viewing. come in, come in. mind the floor. there isn't one past the rug.
  - **PENNY PLOT:** open plan! lots of light! well. no light. lots of plan.
  - ➤ _"what's phase two?"_ → phase
  - ➤ _"i'm here for your page."_ → page
- **[phase]**
  - _She taps the cluster of red pins.* the bottom! lots of potential. characterful. very... occupied. but on completion, all plots and all occupants transfer to vacancy, and vacancy transfers them to the void. location, location, nothing._
  - **PENNY PLOT:** it's not personal. it's a buyer's market. the buyer is the void.
  - → page
- **[page]**
  - _The briefcase is handcuffed to her wrist. She pats it._
  - **PENNY PLOT:** oh, the deed. you can't have the deed. the deed's the whole sale.
  - **PENNY PLOT:** i sold my own house at nineteen. right over there. it's void now. that's how you know i'm good.
  - **PENNY PLOT:** the deal closes today. so do you.
  - _does: flag:penny_fight_

#### Talk: `five` (with AUNTIE SPREADSHEET)
- **[start]**
  - _The Lost & Found. Auntie pins the fifth page. Five frames full. One empty, under the ☺._
  - **AUNTIE SPREADSHEET:** non-productive land clearance.
  - **AUNTIE SPREADSHEET:** the bottom was always phase two. before any of us were born. before the bottom existed. they planned for wherever the poor would end up, and they planned to delete it.
  - _she puts the crayon down. She looks at the empty frame for a long time._
  - **AUNTIE SPREADSHEET:** one left. it's on her desk.
  - _quietly, to the wall* i've always known where it was. i just never had the stairs in me._

#### Choice: Penny Plot is clinging to a SOLD sign over the void. Old Pat has a wheelbarrow of gnomes. Who runs the Margins?
- **DEAL: Vacancy keeps the Margins, and cancels the Bottom's sale**: Penny signs a cancellation with a pen shaped like a key and a smile you don't trust. Vacancy stops selling ground at the Margins and sends survey teams to the raid. The Bottom's sale is cancelled on paper, which means that if ☺ CORP wins, ☺ CORP just signs a new one.
- **TAKEOVER: the Margin Walkers hold the edge**: Pat plants a gnome on the Show Home's doorstep: PENNY'S MUM. The Margin Walkers occupy every plot Vacancy hadn't sold yet; the void stops coming. Vacancy is hostile everywhere; Penny comes back as a raider estate agent on the Commute. The Bottom's sale still exists on ☺ CORP's side until the Clock is dealt with.

**Reward:** 900 coupons, page_vacancy, lt_boss_penny_plot
**Review card:** EXCEEDS EXPECTATIONS. the deal didn't close. / MEETS EXPECTATIONS. / SEE ME. you bought a plot.

---

### 28. THE PLAN `m28_the_plan`
_Whatever you chose at the split, now it has to be built: a headcount, a demolition, or a print run. And whoever you didn't choose does something anyway._

**Where:** The Lost & Found (THE BOTTOM), The Price Press (NUMBER WORKS), The Big Escalator (THE CHECKOUT), The Smiling Fountain (CORP HILL), The Digester Wall (THE GUT), The Bleach Line (CORP HILL)  
**Who:** LUMPS, WEE GORDO, AUNTIE SPREADSHEET, PRITCHARD, CHAD TEMPO, DOT  
**Giver:** — · **Needs:** m27_negative_space

**Mechanic hook:** each plan is a different playstyle: HEADCOUNT is stealth, DEMOLITION is a climb up the Big Escalator against its direction, PRINT RUN is a heist under the fountain _(uses: the grapple, rocket and shotgun jumps, cars and traffic)_

**Beats**
- One of three versions plays, by plan (parts below). Each ends with the Bottom ready for 03:00.
- Whoever's plan you didn't follow acts on their own: Gordo takes his charges up the hill anyway; Lumps, if his mum is still in the Gut, goes to meet Pritchard.
- Pritchard, if he's been treated kindly, leaks the elevator override (1730) and the Twins' rotation.

**The mystery**
- _learn:_ The elevator override is 1730. Of course it is. (HEADCOUNT) The Restoration staffing table has the Bottom's dead on it, and none of its living. (DEMOLITION) The Master Clock runs on the Number Works substation and the Big Escalator's motor. (PRINT RUN) ☺ CORP News reaches every screen in the city from one relay under the Smiling Fountain.
- _suspect:_ Lumps might really take the deal.
- _withheld:_ Page 6 and the 17:10 call (Act V).

**Objectives**
1. do the plan
2. get some sleep. it's 03:00 tomorrow.

**Part: HEADCOUNT (Lumps' plan)** _(if flag:plan_lumps)_
1. attend hask's onboarding interview at the bleach line
2. get the bottom's people onto the staffing table
3. get dot out of the deep wall with the new paperwork · if fate.dot=gut

**Part: DEMOLITION (Gordo's plan)** _(if flag:plan_gordo)_
1. plant charges at the number works substation
2. plant charges on the big escalator's motor

**Part: PRINT RUN (Auntie's plan)** _(if flag:plan_auntie)_
1. seize the ☺ corp news relay under the smiling fountain
2. get the price press ready to print six pages

#### Talk: `onboarding` (with PRITCHARD)
- **[start]**
  - _A white onboarding office on the Bleach Line. Pritchard, in person for the first time: thin, three watches, a blazer too big for him. He stands up when you come in and knocks his chair over._
  - **PRITCHARD:** hi. hi. sorry. you're... you're early. that's good. that's very good. she'll like that.
  - _He lowers his voice to nothing.* lumps told me. in his letter. what you're really doing. i burned the letter. then i felt bad and taped it back together. then i burned it again._
  - ➤ _"will you help us?"_ → help
  - ➤ _"why would you risk it?"_ → why
- **[why]**
  - **PRITCHARD:** because he asks how i am.
  - _he says it in one breath, like he's been holding it for years* and because i typed eleven thousand four hundred and two names that aren't on the table, and i can't stop seeing them when i close my eyes, and i've never had a minute to myself to think about it until right now._
  - → help
- **[help]**
  - **PRITCHARD:** the table's on that terminal. i'll keep the guards on a 'compliance briefing'. i'll make it very long. i'm good at long.
  - **PRITCHARD:** type fast. and... if you get his mum out. tell him i said hello.
  - _does: flag:pritchard_ally_

#### Talk: `detonator` (with WEE GORDO)
- **[start]**
  - _Gordo on the roof of the Lost & Found, at night, holding a detonator made from a ☺ CORP pager. The Spire is lit up on the hill._
  - **WEE GORDO:** two charges. substation and escalator. at 03:15 the clock loses power for nine minutes. enough to break its teeth.
  - _he turns the detonator over in his hands.* you know what i keep thinking? who sweeps up after. that's never been in my plans. who sweeps up._
  - ➤ _"the bottom. together."_ → together
  - ➤ _"you don't have to know yet."_ → know
- **[together]**
  - _He snorts, which is as close as Gordo gets to crying._
  - **WEE GORDO:** the bottom couldn't sweep a porch together. ...we'll learn. we'll have to.
  - _does: standing.bottom:+2_
- **[know]**
  - **WEE GORDO:** i'm a planner. i always have to know.
  - **WEE GORDO:** ...ok. tomorrow i'll not know. one day. as a treat.

#### Talk: `chad` (with CHAD TEMPO)
- **[start]**
  - _Under the Smiling Fountain: a broadcast relay, and at the desk, a mannequin news anchor with perfect hair reading the Schedule to an empty studio._
  - **CHAD TEMPO:** it's 21:14 on corp hill, and everybody's on time.
  - _You unplug his autocue and plug Auntie's tape in. He reads the first line of it perfectly, without understanding a word._
  - **CHAD TEMPO:** option c. strategic write-off. confidential. board eyes only.
  - _he smiles* in other news, traffic is fine._
  - _does: flag:relay_seized_

#### Talk: `print` (with AUNTIE SPREADSHEET)
- **[start]**
  - _The Price Press at night. Auntie stands at the feed tray with the five pages in a folder, running her finger along the press like she's auditing it._
  - **AUNTIE SPREADSHEET:** five pages. six when we get hers. on every price tag in the city by 06:00, and on every screen by 06:01.
  - **AUNTIE SPREADSHEET:** they'll say it's forged. they always say it's forged. so we print the signatures big.
  - ➤ _"you're coming up the hill?"_ → coming
- **[coming]**
  - **AUNTIE SPREADSHEET:** i'm coming up the hill.
  - _she says it the way other people say 'i'm going to die', and she knows you heard it that way._
  - **AUNTIE SPREADSHEET:** i've been not going up that hill for sixty-one years, rory. i'm eighty-five. i'm out of excuses and i'm out of crayons.
  - _does: flag:auntie_coming_

#### Talk: `leak` (with PRITCHARD)
- **[start]**
  - **PAGER:** *BEEP. A text message on the pager, typed very fast.*
  - **PRITCHARD:** the lift override is 1730. of course it's 1730. the twins rotate at 03:20. ms hask has a 03:41 with you. please be on time. please. i booked you lunch after. real lunch. sorry. P.
  - _does: flag:have_override_

#### Talk: `night_before` (with AUNTIE SPREADSHEET)
- **[start]**
  - _The Lost & Found, the night before. Everyone who's coming up the hill is asleep on the floor in coats. Lumps snores like a tuba. Gordo is asleep sitting up with a map on his face. If she's free, Mina is asleep against your shoulder._
  - _Auntie is awake at the long table, writing._
  - **AUNTIE SPREADSHEET:** can't sleep either? good. sit with me.
  - **AUNTIE SPREADSHEET:** i used to do this the night before audits. write down everything i knew. in case.
  - ➤ _"what are you writing?"_ → writing
  - ➤ _"*sit with her in silence*"_ → silence
- **[writing]**
  - _She turns the notebook round. It's names. Everyone in the Bottom, everyone you've met, in crayon, with a line each.* 'lumps: eats four bowls.' 'gordo: right, mostly.' 'dale: sorry.' 'mina: waiting.' 'rory: late. came anyway.'_
  - **AUNTIE SPREADSHEET:** in case.
  - _she closes it.* go to sleep. it's 03:00 tomorrow._
- **[silence]**
  - _You sit. The Machine hums. Your heart ticks. After a while she puts a hand over yours on the table, and leaves it there, and keeps writing with the other one._
  - _does: standing.bottom:+1_

#### Choice: (if it wasn't his plan) Gordo is going up the hill alone tonight with his charges. _(only if !flag:plan_gordo)_
- **stop him**: You find him on the Big Escalator with the charges and take the detonator. He lets you, which is worse than if he hadn't. He comes on the raid; he won't look at you until the Clock. In ON TIME he never speaks to you again before they take him.
- **let him go**: His charges go off at 03:15 during the raid: the Clock loses power for nine minutes whatever plan you followed (the Fully Billable fight starts in the dark), and Corp's reserves are cut off at the escalator. He's hurt in the blast and is carried into the lobby.

#### Choice: (if it wasn't his plan and Dot is still in the Gut) Lumps is going to meet Pritchard and take Hask's deal for his mum. _(only if !flag:plan_lumps fate.dot=gut)_
- **go with him and make it a rescue instead**: You go into the deep wall with him that night instead. Dot comes out. Lumps carries her down the Long Stairs and comes on the raid.
- **let him take the deal**: Lumps signs. Dot is released into ☺ CORP's care, and Lumps is on the staffing table. In the raid he stands with you until the lobby, then he has to choose; his line at the elevator changes ('i signed. i'm still coming up.'). In LATE he never forgives himself; in ON TIME he's your first hire.

**Reward:** 500 coupons
**Review card:** EXCEEDS EXPECTATIONS. the plan survived contact. / MEETS EXPECTATIONS. / SEE ME. you set off the charges in the lost & found.

---

### 29. 03:00 `m29_the_missing_hour`
_At 03:00, in the one hour nobody is booked into, the whole Bottom climbs Corp Hill with every ally you earned._

**Where:** The Bleach Line (CORP HILL), Dividend Road (CORP HILL), The Smiling Fountain (CORP HILL), The Cathedral of Shareholder Value (CORP HILL), The ☺ Spire Lobby (CORP HILL)  
**Who:** AUNTIE SPREADSHEET, LUMPS, WEE GORDO, THE STEERING COMMITTEE, MINA, PIP GRINSWORTH, WRISTBAND, NELL THIRTEEN, OLD PAT  
**Giver:** WEE GORDO · **Needs:** m28_the_plan

**Mechanic hook:** the raid is a rhythm climb (On Time) up Dividend Road; grapple from the Cathedral spire onto the Meeting Room's skid _(uses: on time, the grapple, big laser pointer, cars and traffic)_

**Beats**
- C18: the Bleach Line at 02:59, the allies, the clocks turning to face Dividend Road.
- The climb: a big set piece up Dividend Road. Allies fight at junctions (each district's ruler holds one).
- Shaky company allies (from DEALs) turn if your Corp Standing is low: they'd rather be on ☺ CORP's side if they don't trust you to win. A goon, a segway, a forklift tank switches sides mid-fight.
- Boss fight: THE MEETING ROOM, a flying conference room gunship over the Cathedral of Shareholder Value, flown by the Steering Committee.
- The Spire's doors. Into the lobby.

**The mystery**
- _learn:_ Everyone you helped shows up. Everyone you didn't, doesn't.
- _suspect:_ —
- _withheld:_ —

**Objectives**
1. _(scene)_ · scene `c18_0300`
2. get up dividend road before 04:00 · timer 900s
3. bring down the meeting room · **boss: THE MEETING ROOM**
4. get into the spire

#### Scene: `c18_0300` (cinematic, 62 s, music: raid_theme)
- `  0` _02:59. The Bleach Line at the bottom of Dividend Road. On one side, white: perfect lawns, clocks ticking in sync. On the other, the Bottom: sofa-cars, fridges on trolleys, kids on basket scooters, Off-Spec families with crowbars and soup ladles. Silent._
- `  6` _(if turf.pinstripe=punchlines)_ _The Punchlines in full makeup in a convoy of clown limos, red noses on the bonnets. Pip on the roof of the first one._
- `  6` _(if turf.pinstripe=family)_ _The Family's bocce-ball limos, idling, goons with tiny hands on the running boards. Nobody sure who they're really with._
- `  9` _(if turf.checkout=mallrats)_ _The Mall Rats on rocket carts, goggles down, Wristband at the front._
- `  9` _(if turf.checkout=bigvalue)_ _Big Value Security on segways, Gail's voice on a loudhailer: 'please do not run.'_
- ` 12` _(if turf.numberworks=remainders)_ _The Remainders with a banner: WE ARE THE REMAINDER. Nell with the megaphone._
- ` 12` _(if turf.numberworks=remainder)_ _Remainder forklift tanks with lucky 7s painted on them._
- ` 15` _(if turf.margins=marginwalkers)_ _The Margin Walkers with wheelbarrows of gnomes._
- ` 15` _(if turf.gut=bottom)_ _Freed digesters in Choir robes, still pink at the edges, holding hands._
- ` 18` **WEE GORDO:** *very quietly* 03:00 in three. two. one.
- ` 21` _03:00. The Missing Hour. Corp Hill doesn't go grey like the Lates: it just stops counting. Every public clock on the hill freezes. And then, all together, every clock turns on its pole to face Dividend Road._
- ` 28` **AUNTIE SPREADSHEET:** they can't see us. they can't book us. they don't know we're here.
- ` 32` **LUMPS:** they know. look at the clocks.
- ` 35` _The Bottom climbs Dividend Road in silence: the whole hill at once, past the Smiling Fountain, the Cathedral of Shareholder Value, under the clocks, toward the ☺ Spire, the only lit building._
- ` 50` _(if fate.mina=freed)_ **MINA:** *beside you, quietly* sixty-one years late, rory. let's be on time for once.
- ` 55` _Over the Spire, a flying conference room rises on four rotors, its projector turning on like an eye. A voice over a loudspeaker: 'can everyone see my screen?'_
- ` 60` → BOSS INTRO: THE MEETING ROOM · STEERING COMMITTEE

#### Talk: `turncoat` (with PA)
- **[start]** _branch: flag:pinstripe_deal standing.corp<-20 → family; flag:checkout_deal standing.corp<-20 → bigvalue; flag:numberworks_deal standing.corp<-20 → remainder; else → loyal_
- **[family]**
  - **RADIO:** *Nonna, on a limo radio* merchandise. i priced it. you lose. the family is sorry. the family is never sorry. *the limos turn their guns*
  - _does: flag:family_turned_
- **[bigvalue]**
  - **PA:** *Gail, on the loudhailer, crying* i'm sorry. head office rang. we're sorry for any inconvenience. *the segways turn*
  - _does: flag:bigvalue_turned_
- **[remainder]**
  - **RADIO:** *Mr. Sevens, on a forklift tank radio* nothing personal. the odds moved. touch wood. *the forklifts turn*
  - _does: flag:remainder_turned_
- **[loyal]**
  - **RADIO:** *static, then Pip, or Nell, or Wristband, or whoever's leading the nearest ally* we're still here, darling. we're still here.

**Reward:** 1000 coupons, lt_boss_meeting_room
**Review card:** EXCEEDS EXPECTATIONS. that meeting could have been an email. / MEETS EXPECTATIONS. you're in. / SEE ME. it's 04:00.

---

### 30. THE LOBBY `m30_the_lobby`
_The same lobby as 17:29. The Twins hold the elevator. Auntie sits down behind the reception desk._

**Where:** The ☺ Spire Lobby (CORP HILL), The Top Floor (CORP HILL)  
**Who:** THE TWINS, AUNTIE SPREADSHEET, LUMPS, WEE GORDO, MARION HASK, PRITCHARD  
**Giver:** — · **Needs:** m29_the_missing_hour

**Mechanic hook:** the Twins' join opens when they spin; ricochet round the shield; the Scales find two people guilty in one hit _(uses: scales of justice (verdicts), bank shots, the grapple)_

**Beats**
- The lobby: the marble, the revolving door, the pillar Overtime stepped out from. The game plays the lobby's music from F4.
- Boss fight: THE TWINS, holding the elevator.
- C19: Auntie stays to hold the lobby. Her last line depends on the forgiveness choice. The elevator doesn't stop at 41.
- C20: the top floor. Hask explains why you're free: fired nineteen seconds before the end of the world. The lanyard on the desk. The last page, under it.
- The Master Clock opens behind the glass.

**The mystery**
- _learn:_ Why you're free, from Hask herself. The Restoration would use your recording as the template for all the dead. Auntie Spreadsheet doesn't come back.
- _suspect:_ The last page has the 17:30 backup clause.
- _withheld:_ The 17:10 call (Act V).

**Objectives**
1. get to the elevator · **boss: THE TWINS**
2. _(scene)_ · scene `c19_the_lobby`
3. go up
4. _(scene)_ · scene `c20_final_offer`

#### Scene: `c19_the_lobby` (cinematic, 64 s, music: lobby_1729_reprise)
- `  0` _The ☺ Spire lobby. The same lobby as 17:29: the marble, the revolving door, the pillars, the security desk. Sixty-one years older, perfectly kept. The Twins are down. The elevator doors are open._
- `  6` _Below, through the glass, ☺ CORP's reserves coming up Dividend Road: HR Tactical, Timekeeping cruisers, the rest of the Fun Department if it was hired._
- ` 10` _Auntie walks past the elevator to the old reception desk, slowly, the way she walks up stairs. She sits down behind it. She puts a shotgun on the desk, and her crayon notebook beside it._
- ` 17` **LUMPS:** nan. nan, come on. the lift's here.
- ` 20` **AUNTIE SPREADSHEET:** somebody has to hold the lobby. they'll come up behind you. they'll stop the lift.
- ` 25` **WEE GORDO:** then i'll stay.
- ` 27` **AUNTIE SPREADSHEET:** you won't, gordon. you'll go up and you'll be right about everything. that's your job.
- ` 32` **AUNTIE SPREADSHEET:** ambrose. go with them. carry them if they need carrying. you always do.
- ` 37` _Lumps can't speak. He kneels down, which makes him her height, and puts his forehead against hers. Then he gets in the lift._
- ` 43` **AUNTIE SPREADSHEET:** i sent you up these stairs once. this time i'm staying.
- ` 49` _(if flag:forgave_auntie)_ **AUNTIE SPREADSHEET:** thank you for the stairs, rory. i'd have done them for you.
- ` 49` _(if flag:blamed_auntie)_ **AUNTIE SPREADSHEET:** it balances now. go on.
- ` 49` _(if flag:deferred_forgiveness)_ **AUNTIE SPREADSHEET:** pending. that's all right. that's fair. i'll take pending.
- ` 49` _(if flag:cold_to_auntie)_ **AUNTIE SPREADSHEET:** you sound like them. i'm sorry. that's on me too.
- ` 55` _The elevator doors close on her. The last thing you see is her opening the notebook and picking up a crayon, and the lobby doors behind her starting to shake._
- ` 60` _The lift goes up. The floor counter starts at 1. It does not stop at 41._

#### Scene: `c20_final_offer` (cinematic, 96 s, music: hask_theme)
- `  0` _The top floor. Marion Hask's office: white, one huge window over the whole dark city, and behind the far wall, through glass, the gearwork of the Master Clock turning, cathedral-sized. On her desk: a lanyard that says R. CALE · HEAD OF TIMEKEEPING, a leather ledger, and a single page of heavy paper with the ☺ CORP crest._
- `  8` _Hask stands at the window with her back to you. Pritchard in the corner, very still, three watches beeping softly. Lumps and Gordo behind you, weapons up. She doesn't turn round._
- ` 14` **MARION HASK:** You are on time. I appreciate that. It is 03:41.
- ` 18` **MARION HASK:** Your friend in the lobby is still alive. She has a shotgun and a notebook. She is doing better than my staff expected.
- ` 24` _She turns round. Up close, the surgical scar runs from her collar to her jaw. Her skin is too smooth in some places and too old in others. She looks at you the way an auditor looks at a number._
- ` 30` **MARION HASK:** You want to know why you came out of the Machine without a schedule. I will tell you, because you should hear it from someone who is not guessing.
- ` 37` **MARION HASK:** Every lanyard synced its wearer to the Machine for continuity. At 17:30 it kept the last sync of every employee.
- ` 43` **MARION HASK:** You were terminated at 17:29 and 41 seconds, by my Head of Timekeeping, for running. The Schedule does not load into people who do not work here.
- ` 50` **MARION HASK:** You were fired nineteen seconds before the end of the world. It is the only reason nobody can tell you what time it is.
- ` 56` **MARION HASK:** It makes you a flaw in my design. It also makes you the only one of them who could choose this job. So I am offering it.
- ` 62` _She slides the lanyard across the desk._
- ` 64` **MARION HASK:** Head of Timekeeping. Mr. Sallow is tired. You would replace him. Your recording would be the template for the Restoration: the dead would wake up a little bit like you. The Bottom's people on the staffing table would be fed.
- ` 73` _(if plan=lumps)_ **MARION HASK:** Including your friend's mother. Pritchard has typed her in.
- ` 76` _(if drift>=4)_ **MARION HASK:** You have changed so many of your parts. You would make a perfect employee.
- ` 76` _(if drift<4)_ **MARION HASK:** You still have most of your own parts. That is a pity. It will make the first year harder.
- ` 82` **MARION HASK:** Or you can do whatever you came up here to do. The Clock is through that door. Mr. Sallow is waiting in it.
- ` 88` **WEE GORDO:** *low* don't touch the lanyard.
- ` 90` **LUMPS:** *low* ...don't touch it yet.
- ` 93` _Behind the glass the Master Clock opens like a ribcage. Steam. A ticking you can feel in your teeth._

#### Talk: `lift` (with LUMPS)
- **[start]**
  - _The elevator. Mirrored walls. Ninety floors. The floor counter climbs past 41 and doesn't stop._
  - _Lumps has his face to the wall. His shoulders are shaking. He's counting floors under his breath and losing count._
  - ➤ _"*put a hand on his back*"_ → hand
  - ➤ _"she chose it, lumps."_ → chose
  - ➤ _"(if Lumps took Hask's deal) are you still with me?"_ → deal (if flag:lumps_took_deal)
- **[hand]**
  - _He doesn't turn round. After a few floors he says, very quietly:* she didn't eat. this morning. she gave me hers._
  - **LUMPS:** ...i'm going to be so angry later. i'm not angry yet. i'm counting.
- **[chose]**
  - **LUMPS:** i know she chose it. she chose it sixty years ago. she just took a long time to get there.
  - _the counter: 88. 89. 90._
- **[deal]**
  - _He wipes his face with a forearm the size of a door._
  - **LUMPS:** i signed. i'm still coming up. i don't know what that makes me. ask me at the top.

**Reward:** lt_boss_twins
_Builder notes: no grade card after the lobby. END OF ACT IV plays over the Master Clock opening._

---
