# The endings

_Generated from `endings.js` and `scenes_act5.js`._

## ON TIME
_You sign. The Restoration runs. Everyone is fed, and nobody is free, including you._

**Available:** always

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

**Panels**
- _(if drift>=4)_ you'd make a perfect employee. you do. you've never once been late. you don't remember why that used to matter.
- _(if drift<2)_ every morning at 09:00 you clock in, and for one second, before the schedule loads, you remember a strawberry keyring. then it's 09:00:01.
- _(if flag:plan_lumps)_ the gut's people are on the staffing table. they're fed. they're safe. they have a slot. lumps says it's better than the wall. he says it every day, like he's checking.
- _(if !flag:plan_lumps)_ the bottom's living weren't on the table. the bottom isn't on the map any more. pritchard keeps a list of their names in a drawer. he isn't supposed to.
- _(if flag:overtime_clocked_out)_ edwin sallow clocked out. at 09:00 the next morning the restoration reloaded him from the backup. he's on shift. he doesn't remember leaving. you do.
- _(if fate.mina=freed)_ mina sends a letter every new year's eve. 'you were late for me once. you can be late for them.' the schedule files it.
- _(if flag:stopped_gordo)_ wee gordo was arrested at 03:00 in the first week, on schedule. he never spoke to you again.
- R. CALE, HEAD OF TIMEKEEPING. ten thousand copies. one lanyard each.

**District epilogues**
- THE BOTTOM: the bottom: sold. folded into the void, one stacked house at a time. the down escalator was the last thing to go. it was going down.
- THE GUT: the gut: an organ farm on contract to the restoration. the choir sings to a schedule now. the walls are fed at 06:00 and 18:00.
- PINSTRIPE (FAZZOLETTI FAMILY INSURANCE): pinstripe: the family insures the restoration at a premium. nonna's strings run all the way up to the spire now.
- PINSTRIPE (THE PUNCHLINES): pinstripe: the punchlines were 'rescheduled'. pip is a jester again, at corporate events, and smiles very hard.
- THE CHECKOUT (BIG VALUE RETAIL): the checkout: the doors open at 09:00. everyone's a member now. membership is mandatory.
- THE CHECKOUT (THE MALL RATS): the checkout: the welded doors were cut open on day one. the mall rats are still in the vents. security leaves them a ration at 12:00, on schedule.
- NUMBER WORKS (REMAINDER INDUSTRIES): number works: prices are fixed. forever. bread costs 3. it will always cost 3.
- NUMBER WORKS (THE REMAINDERS): number works: the union was dissolved into the workforce. nell got a number. it's 13.
- CHROME GRISTLE: chrome gristle: licensed. every clinic installs schedule chips. the neon is white now.
- EVERGREEN ACRES: evergreen acres: the model for the whole city. every window waves.
- THE LATES: the lates: scheduled. it's still tuesday. it's an efficient tuesday.
- THE MARGINS (VACANCY HOLDINGS): the margins: vacancy is selling again. it has a lot of new stock.
- THE MARGINS (THE MARGIN WALKERS): the margins: the gnome line held for three weeks. then a bulldozer came at 03:00.
- CORP HILL: corp hill: perfectly on time. it always was.
- THE COMMUTE: the commute: the unpaid were hired as restoration security. employee of the month got a real award. he cried.

**Post-game:** the city is lit and on schedule: Late Fees are permanent ★1, the dead work every street, food trucks arrive on the minute, the Bottom is void. You wear the lanyard.

## LATE
_You smash the Master Clock. Nobody owns time. Nobody keeps the lights on either._

**Available:** always

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

**Panels**
- _(if drift>=4)_ you've got so many parts that aren't yours, some nights you can't tell whose memories are whose. mina says it doesn't matter. she says you're on time now. that's new.
- _(if drift<2)_ with the clock gone you remember more. the flat on hillside road. the green man at the crossing. mina's hand. you write it all down, in crayon.
- _(if fate.dot=freed)_ dot grows tomatoes on the long stairs. they're the first green thing on the hill in sixty-one years. lumps cries every time one ripens. it's not the sunset. it's the tomatoes.
- _(if !fate.dot=freed)_ lumps won't forgive you. his mum was in the gut when the clock stopped and the choir stopped singing. he watches the sunset alone.
- _(if flag:overtime_clocked_out)_ edwin sallow sits on the bottom's stairs every evening. at 17:30 he stands up, then sits back down. the kids have started standing up with him.
- _(if flag:lumps_took_deal)_ lumps signed a contract with a company that doesn't exist any more. he keeps it in his wallet. he says it's to remember what he nearly was.
- nobody owns time. nobody keeps the lights on either. it's free, and it's dangerous, and it's yours.

**District epilogues**
- THE BOTTOM: the bottom: still here. the void stopped at the clock. someone's built a second floor on the lost & found. it leans.
- THE GUT (GRISTLE & SONS BIOLOGICS): the gut: without ☺ corp's trucks gristle & sons is starving, and the gut is spreading. the bishop sings at the front of it.
- THE GUT (THE BOTTOM): the gut: the bottom's now. raw, dangerous, warm. the freed digesters patrol it in choir robes, and the green on the long stairs is coming out of it.
- PINSTRIPE (FAZZOLETTI FAMILY INSURANCE): pinstripe: the family runs protection in the dark. you're covered. you're always covered. the price has gone up.
- PINSTRIPE (THE PUNCHLINES): pinstripe: the punchlines run it. red noses on every door. pranks instead of protection. it's fair. it's frightening. the don was buried with a whoopee cushion.
- THE CHECKOUT (BIG VALUE RETAIL): the checkout: gail switched off the pa and sat in the quiet. the doors didn't open at 09:00. nobody's sure if the store is closed or just late.
- THE CHECKOUT (THE MALL RATS): the checkout: the doors are welded shut and painted with the names of the stampede's dead. mina comes every week to read them.
- NUMBER WORKS (REMAINDER INDUSTRIES): number works: mr. sevens prints whatever prices he likes. nobody has to pay them. he's losing at the fun fair.
- NUMBER WORKS (THE REMAINDERS): number works: prices went to zero for a week, then to whatever people agreed on. the meetings are very long. bread costs 2.
- CHROME GRISTLE: chrome gristle: still night, still raining. bev runs a free clinic. upsell runs an honest one, out of necessity.
- EVERGREEN ACRES: evergreen acres: the mannequins stopped waving at once. linda planted vegetables on her lawn. the hoa voted on it. it passed.
- THE LATES: the lates: wednesday. pauline cried at the date on her monitor. then she went outside.
- THE MARGINS (VACANCY HOLDINGS): the margins: vacancy collapsed. penny plot is selling car roofs on the commute.
- THE MARGINS (THE MARGIN WALKERS): the margins: the gnome line holds. children help paint the names.
- CORP HILL: corp hill: dark. the spire's windows are black. people climb dividend road at night to look at the stars.
- THE COMMUTE: the commute: employee of the month gave the award to someone else for the first time. it was todd. they sit on the bus roof. neither of them knows what to say.

**Post-game:** the city is dark: no clocks in the HUD (the district clock reads --:--), Corp Hill is unlit and lootable, the rot spreads faster everywhere nobody holds it, Late Fees are gone, warlords fight for the gaps.

## OFF THE BOOKS
_You publish Option C. The debts die. The people who ended the world have to bargain._

**Available:** pages>=6

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

**Panels**
- _(if drift>=4)_ you walked out with a backup you'll never restore. you're not sure there's much of rory left in it. that's all right. you're not sure there was much of rory in you either. you're someone. that'll do.
- _(if drift<2)_ out on the commute, past the last digit, you find you can remember the whole of the last workday, and the morning before it, and mina's ninth birthday. you were late for that too. she forgave you then as well.
- _(if flag:overtime_clocked_out)_ the bottom found an old man in a suit on its stairs. he asked the kids what day it was. they said wednesday. he seemed pleased.
- _(if !flag:overtime_clocked_out)_ edwin sallow's backup went into the free sims. he works a normal day and goes home at 17:30 to a house june was never recorded in. some people think that's kind. dale doesn't.
- _(if flag:forgave_auntie)_ auntie's notebook was published after option c. the last entry: 'forgiven. 1 entry.'
- a cold peace, with the people who ended the world still standing. but they're standing at a table now, and they're not the only ones at it.

**District epilogues**
- THE BOTTOM: the bottom: its sale is void. it's still at the bottom of the hill. it's started building up.
- THE GUT (GRISTLE & SONS BIOLOGICS): the gut: page four bankrupted gristle & sons. the bishop kept the choir and lost the company.
- THE GUT (THE BOTTOM): the gut: the bottom's. sister agenda's minutes were published with option c. they're the only list of names.
- PINSTRIPE (FAZZOLETTI FAMILY INSURANCE): pinstripe: page one voided every policy. the family bargains at the table. nonna wins more than anyone.
- PINSTRIPE (THE PUNCHLINES): pinstripe: pip takes a seat at the table in full makeup. nobody can tell when pip's joking. that's the point.
- THE CHECKOUT (BIG VALUE RETAIL): the checkout: gail read page two over the pa at 09:00, herself. then she unlocked the doors and left them open.
- THE CHECKOUT (THE MALL RATS): the checkout: page two is read out at the welded doors every morning at 09:00. wristband stands where he stood when he was five.
- NUMBER WORKS (REMAINDER INDUSTRIES): number works: page three is printed on every price tag in the city. mr. sevens' 17:10 log was published. nobody shakes his hand.
- NUMBER WORKS (THE REMAINDERS): number works: the union's seat at the table is a stool marked 13. nell stands.
- CHROME GRISTLE: chrome gristle: the patent is public. every meat mechanic copies upsell's procedures for free. he's furious. bev gets her hands back.
- EVERGREEN ACRES: evergreen acres: the pilot is published. property values crash. the hoa holds a vote on whether the apocalypse happened. it passes, narrowly.
- THE LATES: the lates: wednesday. pauline audits the restoration's books for free, as a hobby. she finds everything.
- THE MARGINS (VACANCY HOLDINGS): the margins: page five voids every sale. penny plot's commission is zero. she takes it surprisingly well.
- THE MARGINS (THE MARGIN WALKERS): the margins: old pat plants a gnome for every plot given back. she runs out of gnomes. the bottom makes more.
- CORP HILL: corp hill: still lit, on a smaller schedule, for the people who live there. hask reads her ledger at the table. it takes four days.
- THE COMMUTE: the commute: 'unpaid, inc.' won a contract at the table. it's paid. employee of the month framed the first payslip.

**Post-game:** the city is at dawn: Late Fees are abolished (☺ CORP has no claim), shops are cheaper, the free sims are a new place in the Machine menu where the bots won't fight unless they want to, the companies and groups hold the turf you gave them.

## NAP TIME (non-canon)
_The founder walks across the keyboard. This didn't happen._

**Available:** cats>=12

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

**Panels**
- everyone in the city is asleep. legally.
- this didn't happen. the credits said so. (it unlocks the BOARD MEMBER outfit and lets you choose again.)

**Post-game:** non-canon: after the credits the game returns to C24 and you choose again. The NAP TIME unlock and the outfit stay on the save.

#### Scene: `credits_drive` (cinematic, 240 s, music: credits_drive)
- `  0` _A playable drive down the hill in the sofa-car, in the ending's light (ON TIME: lit, on schedule; LATE: dark, fires and stars; OFF THE BOOKS: dawn; NAP TIME: everyone asleep in the road). Credits scroll in the zine style down the side of the screen._
- `  5` _Everyone who's still alive is somewhere on the route, doing what their fate in the cast bible says, and waves (or doesn't). Allies' banners on the districts they hold. The gnome line at the Margins. The green thing on the Long Stairs, if it grew. Overtime on the stairs, if he clocked out._
- `230` _The drive ends at the Lost & Found. The Machine is humming. The tray is (or isn't) empty. Fade._
- `238` **JANKFIRE: OVERDUE**
