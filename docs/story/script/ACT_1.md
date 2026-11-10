# Act 1: "Please Take Your Item"
_What am I?_

_Generated from `shared/story/content/missions/act1.js` and `scenes_act1.js`._

### 1. PLEASE TAKE YOUR ITEM `m01_return_to_sender`
_You win a training sim, the camera pulls out through the Machine's glass, and for the first time in sixty-one years the Machine gives something back: you._

**Where:** Suburb (sim) (THE TRAINING SIMS), The Machine (THE BOTTOM), The Lost & Found (THE BOTTOM), The Wok Roofs (THE BOTTOM), The Crayon School (THE BOTTOM), The Down Escalator (THE BOTTOM)  
**Who:** CHANGE, DALE, AUNTIE SPREADSHEET, LUMPS, WEE GORDO, DUMPLING, PALLET JACK  
**Giver:** — · **Needs:** —

**Mechanic hook:** the tutorial is a grapple lesson in disguise: Dumpling's tour is swing onto the Wok Roofs, ride a washing line back, and land somewhere Dumpling can score out of ten _(uses: the grapple, washing-line ziplines, bhop and infinite momentum)_

**Beats**
- A normal-looking PvP match on the Suburb map. The player wins. TRAINING COMPLETE. The bots stand and stare.
- C1: the pull-back through the glass, up the hill to the Spire and back down. Dale presses the button. You drop into the tray.
- First words with Dale and Auntie. Auntie sees the barcode on your neck and drops her crayon; she covers it.
- Pallet Jack carries the Machine's tray, with you in it, up the down escalator. First line of his you hear: the weight.
- Lumps and Wee Gordo arrive. Gordo scans the barcode with a stolen ☺ CORP scanner: NO RECORD. He doesn't trust you. Lumps does.
- The Bottom names you CHANGE.
- Tutorial with Dumpling: grab a weapon from the Lost Property bins, shoot a dead vending machine for loot, grapple onto the Wok Roofs (scored out of ten) and ride a washing line back.
- Dinner. Auntie tells you how the world ended (P1b). You go to sleep in a box marked RETURNS.

**The mystery**
- _learn:_ You were inside the Machine, in a training sim. The sims are the world before the end. The world ended sixty-one years ago in a war the companies fought, ending in something called Option C at 17:30. You're a mannequin. Your barcode has no record.
- _suspect:_ Auntie knows something about you (the crayon). Dale has been waiting a long time to press that button.
- _withheld:_ Who you were. Why the barcode has no record. What Option C actually says.

**Objectives**
1. win the match
2. _(scene)_ · scene `c1_please_take_your_item`
3. take your item
4. talk to the old man
5. grab something from the lost property bins
6. shoot the dead vending machine
7. grapple onto the wok roofs (dumpling is scoring you)
8. ride a washing line back to the lost & found
9. dinner at the lost & found
10. sleep

#### Scene: `c1_please_take_your_item` (cinematic, 95 s, music: overdue_main_theme)
- `  0` _It starts as a normal JANKFIRE match on the Suburb map: the real HUD, the kill feed, the timer at 0:04. The player gets the last kill._
- `  2` **TRAINING COMPLETE**
- `  4` _The bots don't respawn. They stand where they died, get up slowly, and turn to look at the player. All of them. The kill feed keeps scrolling the same line: CALE R. 4417 has left the match. CALE R. 4417 has left the match._
- `  9` _The camera pulls back from the player. The sky of the Suburb map has a reflection on it, like glass. The camera goes through the glass._
- ` 15` _We're outside a vending machine. The whole Suburb match is inside its window, tiny, still running. The machine is the original ☺ vending machine, glowing, humming, in a ruined returns depot. Rain through the roof._
- ` 20` _The camera keeps pulling back: out of the Lost & Found, over the stacked pastel houses of the Bottom, up the rubble hill. Washing lines. Wok dishes. Here and there a door standing open with a white slip stapled to it at head height. A kid on a basket scooter looks up._
- ` 30` **JANKFIRE: OVERDUE** _The title slams over the hill._
- ` 34` _Still pulling back and up: the Gut breathing in its valley, ribcage arches over glowing pink streets; the Lates' dead clock tower; giant fallen digits glowing green in the ash; a flyover wall with a bus queue burnt onto it, eleven shadows and no bus; the ring road, still nose to tail from the evening it stopped; and at the very top, the ☺ Spire, white and lit, the only lit building in the dark._
- ` 50` _Every public clock on Corp Hill ticks in sync. The camera stops on the Spire's Master Clock: 23:58._
- ` 53` _Whip pan: we fall back down the hill, through the depot roof, to the Machine._
- ` 56` _Dale, eighty-three, with his hand over a big round button on the Machine's service panel. It has a sticker on it: DISPENSE (ENGINEER ONLY). The sticker is sixty years old. He has never pressed it. Auntie Spreadsheet is behind him with a torch and a notebook._
- ` 60` **AUNTIE SPREADSHEET:** dale. you've been looking at that button for twenty minutes.
- ` 64` **DALE:** it's been looking at me for sixty years.
- ` 68` _Inside the glass, the tiny Suburb match is glitching: one mannequin keeps walking off the edge of the map, and the map keeps putting it back._
- ` 71` **DALE:** that one won't stay in. every match. it walks off the edge. it wants out.
- ` 75` **AUNTIE SPREADSHEET:** then let it out.
- ` 77` _Dale looks at her for a long moment. Something unspoken. He presses the button._
- ` 79` **MACHINE:** BEEP.
- ` 80` **MACHINE:** CLUNK.
- ` 81` _A mannequin, folded impossibly small, drops into the dispensing tray and unfolds, joint by joint, with a wrong knee._
- ` 85` **MACHINE:** please take your item.
- ` 87` **AUNTIE SPREADSHEET:** it's never given anything.
- ` 90` **DALE:** it gave change.
- ` 93` _Blend to the player's first-person view from inside the tray, looking up at the two of them. Control._

#### Scene: `p1b_final_quarter` (panels, 40 s, music: auntie_theme_crayon)
- `  0` _Auntie Spreadsheet's crayon captions, in her handwriting, over halftone panels. She's telling the story across a soup table._
- `  1` [panel 1] _first they bought the politicians. then the parties. then the countries. ☺ CORP bought ours at an auction. it was the only bidder._ (SOLD) _A politician at a podium with a ☺ price tag dangling off his collar._
- `  7` [panel 2] _then they merged. every company was a division, every country belonged to one, and every quarter the bottom division got cut. so they went to war over market share._ _A war map shaped like a sales chart, armies in division colours: pink, yellow, red, orange, black._
- ` 14` [panel 3] _the last day of the last quarter. every division was going to miss its number. at 16:59 six boards signed something called option c._ (SCRITCH) _Six pens over six signature lines, six logos on the letterheads. A clock: 16:59._
- ` 21` [panel 4] _at 17:30 they launched everything at once. the bombs first. then the things that weren't bombs. every product line they had._ (DONG) _Three images in one panel: a street frozen mid-step (the Lates), a battlefield standing back up (Regrowth), a city going black._
- ` 27` [panel 5] _the long dark. billions dead. the companies waited it out in their towers. the spire had the only lit windows for thirty years._ _Ash falling on a dark city. One tower lit._
- ` 33` [panel 6] _and we built houses on the hill. the hill is everybody who didn't have a tower. it breathes. you get used to it._ _Survivors stacking pastel shipping-container houses on a hill of rubble and bone. A kid sleeping on a washing line._
- ` 38` **AUNTIE SPREADSHEET:** that was the end of the world. sixty-one years ago. you hungry?

#### Talk: `first_words` (with DALE)
- **[start]**
  - _Dale crouches by the tray. Up close he's older than the button._
  - **DALE:** ...easy. easy. you're out. you're in the depot. nobody's going to hurt you.
  - **AUNTIE SPREADSHEET:** can it hear you?
  - **DALE:** she can hear everything. this one can probably hear.
  - ➤ _"where am i?"_ → where
  - ➤ _"who are you?"_ → who
  - ➤ _"*try to stand up*"_ → stand
- **[where]**
  - **DALE:** the lost & found. the bottom of the hill. ...the bottom of everything, really.
  - **DALE:** you were in her. the machine. in a match. you kept walking off the map.
  - ➤ _"it felt real."_ → real
  - ➤ _"who are you?"_ → who
- **[real]**
  - **DALE:** it's a recording. a good one. the world as it was. ...you don't know yet. agnes, you tell it. you're better at this.
  - → auntie
- **[who]**
  - **DALE:** dale. i fix her. i've been fixing her since... a long time.
  - **DALE:** and that's agnes. don't call her that, she'll make you count something.
  - → auntie
- **[stand]**
  - _your knee bends the wrong way. You go down. Dale catches your elbow._
  - **DALE:** yeah. they all do that. returned stock.
  - → auntie
- **[auntie]**
  - _She steps into the light with the torch and looks at you properly for the first time. She looks at your face. Then at the back of your neck._
  - _Her crayon falls out of her hand and rolls under the Machine. She doesn't pick it up._
  - **AUNTIE SPREADSHEET:** ...right. well. you'll be hungry. everyone's hungry.
  - **DALE:** it's plastic, agnes.
  - **AUNTIE SPREADSHEET:** everyone's hungry, dale.
  - ➤ _"what am i?"_ → what
  - ➤ _"i'm not hungry."_ → nothungry
  - ➤ _"why are you looking at my neck?"_ → neck
- **[what]**
  - **AUNTIE SPREADSHEET:** you're the first thing that machine has ever given anybody. which makes you very valuable or very lost.
  - **AUNTIE SPREADSHEET:** the bottom's good with lost. come on.
  - _does: flag:met_auntie, flag:met_dale_
- **[nothungry]**
  - **AUNTIE SPREADSHEET:** you will be. it's a habit. bodies remember things.
  - **AUNTIE SPREADSHEET:** ...come on.
  - _does: flag:met_auntie, flag:met_dale_
- **[neck]**
  - _a pause slightly too long_
  - **AUNTIE SPREADSHEET:** you've got a barcode. i used to work somewhere that had barcodes. old habits.
  - **AUNTIE SPREADSHEET:** come on. before lumps finds you. he'll want to hug you and you're not built for it.
  - _does: flag:met_auntie, flag:met_dale, flag:asked_auntie_neck_

#### Talk: `barcode` (with WEE GORDO)
- **[start]**
  - _Pallet Jack carries the Machine's tray, with you in it, up the down escalator._
  - **PALLET JACK:** you're about forty kilos, light one. lightest friend i've got.
  - **LUMPS:** *filling the doorway* is that it? is that the thing?
  - **LUMPS:** hello. i'm lumps. sorry. *he hugs you. Something in your shoulder pops back in.* sorry.
  - **WEE GORDO:** move, ambrose.
  - _Wee Gordo pushes past him with a chunky ☺ CORP barcode scanner held together with tape. He doesn't ask. He scans the back of your neck._
  - _BEEP.* NO RECORD._
  - _BEEP.* NO RECORD._
  - **WEE GORDO:** a ☺ corp product with a ☺ corp barcode that ☺ corp doesn't have a record of. that's either a miracle or a trap. and i don't believe in miracles.
  - ➤ _"i don't know what i am either."_ → honest
  - ➤ _"you scan everyone like that?"_ → everyone
  - ➤ _"*say nothing*"_ → silent
- **[honest]**
  - _He looks at you for a long time._
  - **WEE GORDO:** ...ok. that's the first honest thing anyone's said in this depot all week.
  - **WEE GORDO:** i'm still checking your pockets.
  - → naming
  - _does: standing.bottom:+2_
- **[everyone]**
  - **WEE GORDO:** only the ones that fall out of corp machines.
  - **LUMPS:** he scanned me once. i'm a tin of beans.
  - **LUMPS:** ...i was holding a tin of beans.
  - → naming
- **[silent]**
  - **WEE GORDO:** great. a quiet one. the quiet ones are the ones that report you.
  - **LUMPS:** gordo.
  - **WEE GORDO:** fine. fine.
  - → naming
- **[naming]**
  - **AUNTIE SPREADSHEET:** it needs a name. we can't call it 'it'. it's rude and it's confusing.
  - **LUMPS:** steve.
  - **WEE GORDO:** no.
  - **DUMPLING:** *from somewhere under a table* GHOST.
  - **DALE:** *from the Machine, without looking round* change.
  - **AUNTIE SPREADSHEET:** dale?
  - **DALE:** sixty-one years. she never gave anybody their change. then she gave them.
  - **AUNTIE SPREADSHEET:** ...change. right. welcome to the bottom, change.
  - _does: flag:named_change_

#### Talk: `dumpling_tour` (with DUMPLING)
- **[start]**
  - **DUMPLING:** ghost! ghost! auntie says i'm doing the tour because i'm the most annoying. that's a job.
  - **DUMPLING:** this is the lost property. everything anybody ever lost. there's a whole bus out the back. take something. something that shoots.
  - **DUMPLING:** not the top shelf! the top shelf's people who went on the truck. auntie says that's not lost, that's owed.
  - ➤ _"what do you shoot out here?"_ → shoot
  - ➤ _"is any of this yours?"_ → yours
- **[shoot]**
  - **DUMPLING:** raiders. corp. dogs from the gut. not the nice dogs. the stomach ones.
  - **DUMPLING:** and the machines. the old vending machines. if you shoot them they give you stuff. dale says don't. dale does it every day.
- **[yours]**
  - **DUMPLING:** my dad's hat's in there. he's not lost. he's at work. he'll come and get it.
  - _Dumpling's ears go flat for a second, then pop up.* come ON._

#### Talk: `dumpling_score` (with DUMPLING)
- **[start]**
  - **DUMPLING:** grapple the wok on that roof. no, the wok. the WOK. the round thing.
  - **DUMPLING:** let go when you're going up, not when you're going down. going down is how mr. abara broke his everything.
  - **DUMPLING:** bev put him back together. the hip's off a different man. he says goodnight to it.
  - _you land, roughly, on a roof covered in woks_
  - **DUMPLING:** ...four out of ten. you swung like a fridge. lumps swings like a fridge and he IS a fridge.
  - ➤ _"let me go again."_ → again
  - ➤ _"four?"_ → four
- **[again]**
  - **DUMPLING:** you can't go again. it's a tour. tours go forwards. ride the washing line back. don't drop a sock.
- **[four]**
  - **DUMPLING:** four's good. i gave dale a one. he grappled a pigeon.

#### Talk: `dinner` (with AUNTIE SPREADSHEET)
- **[start]**
  - _A long table in the depot. Soup in mismatched bowls. Twelve places laid, seven people. Nobody sits at the other five and nobody clears them. Lumps eats four. Gordo reads a binder while he eats. Dale doesn't come; he never leaves the Machine at night._
  - **AUNTIE SPREADSHEET:** eat. you're plastic. eat anyway. it's how we know you're one of us.
  - _You eat. It goes somewhere. Nobody asks where._
  - ➤ _"what happened to the world?"_ → world
  - ➤ _"why do you keep the books in crayon?"_ → crayon
  - ➤ _"what's the spire?"_ → spire
- **[world]**
  - _She takes a crayon from behind her ear, opens her notebook to a page she's clearly drawn on many times, and turns it round._
  - → after
  - _does: scene:p1b_final_quarter_
- **[crayon]**
  - **AUNTIE SPREADSHEET:** because ☺ corp owned every pen in the city. crayons were the kids'. nobody ever thought to sell those back to us.
  - **AUNTIE SPREADSHEET:** and because when you write in crayon, it's very hard to pretend you didn't write it.
  - ➤ _"what happened to the world?"_ → world
  - ➤ _"what's the spire?"_ → spire
- **[spire]**
  - **AUNTIE SPREADSHEET:** the top of the hill. ☺ corp. the only lit building for thirty years. i costed those lights once. they'd have kept this whole hill warm. they're still there. still on time.
  - **WEE GORDO:** *without looking up* still sending us the bill.
  - ➤ _"what bill?"_ → bill
  - ➤ _"what happened to the world?"_ → world
- **[bill]**
  - **AUNTIE SPREADSHEET:** back pay. for the time the world spent ending. two hundred and forty-four quarters of it.
  - **AUNTIE SPREADSHEET:** for a job none of us had. a job most of us weren't born for.
  - **AUNTIE SPREADSHEET:** it doesn't reconcile. nothing they send us reconciles.
  - **WEE GORDO:** *still not looking up* they don't want it in coupons.
  - _Auntie looks down the table at the empty places. Then she passes you the bread._
  - ➤ _"what happened to the world?"_ → world
- **[after]**
  - _The panels fade. The soup's gone cold._
  - **LUMPS:** she tells it every time someone new comes. she cries at the dark bit.
  - **AUNTIE SPREADSHEET:** i do not.
  - **LUMPS:** you do, nan.
  - **AUNTIE SPREADSHEET:** ...go to bed, all of you. change, there's a box by the machine. it says returns. it's the nicest box we've got.
  - ➤ _"auntie. did you know me?"_ → knew (if flag:asked_auntie_neck)
  - ➤ _"goodnight."_ → night
- **[knew]**
  - _She looks at the soup._
  - **AUNTIE SPREADSHEET:** i've known a lot of people, change. i'm eighty-five. go to sleep.
  - _She doesn't go to bed. From the box you can see her at the table, saying something to the cold soup, too quiet to hear. She says it twice._
  - _does: flag:auntie_dodged_
- **[night]**
  - **AUNTIE SPREADSHEET:** goodnight. *quietly, when she thinks you've gone* ...goodnight.
  - _The depot goes dark. The Machine doesn't. Through its glass, very small, a match is starting. Somebody in there is laughing._

**Reward:** 50 coupons, lost_property_weapon
**Review card:** EXCEEDS EXPECTATIONS. you came out of a vending machine and ate soup. very adaptable. / MEETS EXPECTATIONS. returned in good condition. / SEE ME. you fell off the washing line four times. dumpling is telling everyone.
_Builder notes: the sim match should use the real multiplayer HUD so the cut out through the glass lands. Dale's terminal grabs a security still of the tray drop: that's the still Overtime has in P5b._

---

### 2. SAUCE RUN `m02_sauce_run`
_The Bottom trades soup to Gristle & Sons for medicine. Steal a car, cross the edge of The Commute without spilling it, and survive the Unpaid._

**Where:** Sharon's Soup Kitchen (THE BOTTOM), The Ring Road (THE COMMUTE), The Gut Border (THE GUT)  
**Who:** BIG SAUCE SHARON, LUMPS, WEE GORDO, EMPLOYEE OF THE MONTH, PALLET JACK  
**Giver:** BIG SAUCE SHARON · **Needs:** m01_return_to_sender

**Mechanic hook:** a slosh meter on the soup pot turns every jump, drift and car-roof landing into a decision; the interns' 'business cards' are frags _(uses: cars and traffic, frags and smoke, rocket and shotgun jumps)_

**Beats**
- P2 briefing: Sharon, the pot; Lumps, the key; Gordo, 'he means steal a car'.
- Steal a car (any car; Lumps suggests the sofa-car, which belongs to Sharon's cousin, who is asleep on it).
- Pallet Jack lifts Sharon's pot into the car with one hand and tells Lumps his squat form is "a bit sad".
- Load the pot. Lumps rides shotgun holding it in his lap. Don't spill it: hard landings slosh it, and a full spill fails the delivery (but not the mission).
- In the car Lumps talks about the Gut, the trade and his mum, who is 'at work in the Gut'. He doesn't explain.
- The Unpaid ambush on the Ring Road: war-rigs made of desks. Employee of the Month robs you and offers you an internship.
- Deliver to the Gristle & Sons trade post at the Gut border. A Choir clerk counts the soup and hands over a crate of medicine.

**The mystery**
- _learn:_ The companies still run the city's districts. Gristle & Sons runs the Gut and trades medicine for soup. The Unpaid are interns' grandchildren who worship 'the First Intern'. Lumps' mum is in the Gut.
- _suspect:_ Why does Gristle & Sons want soup at all?
- _withheld:_ What the soup is for (m20).

**Objectives**
1. get the soup from sharon · scene `p2_sauce_run`
2. steal a car
3. load the soup pot
4. drive the soup to the gut border (don't spill it)
5. survive the unpaid
6. deliver the soup to the gristle & sons trade post

#### Scene: `p2_sauce_run` (panels, 14 s)
- `  0` [panel 1] **BIG SAUCE SHARON:** soup. for medicine. gristle and sons at the gut border. same as every week. (SLOSH) _Sharon holds up a huge red pot._
- `  4` [panel 2] **LUMPS:** i'll hold the pot. you hold the key. _Lumps holds up a car key on a fluffy keyring._
- `  8` [panel 3] **WEE GORDO:** he means steal a car. and watch out for interns. (JANGLE) _Wee Gordo, deadpan, the key isn't for any car they own._
- ` 12` **MISSION: SAUCE RUN**

#### Talk: `pot` (with BIG SAUCE SHARON)
- **[start]**
  - **BIG SAUCE SHARON:** you'll take the red pot and you'll not spill it.
  - **BIG SAUCE SHARON:** it's the tomato. gristle like the tomato. they pay double for the tomato.
  - **LUMPS:** they pay in medicine.
  - **BIG SAUCE SHARON:** they pay in medicine. i didn't say it was a good double.
  - **BIG SAUCE SHARON:** there's forty people's medicine in that pot. spill a cup and one of them goes without. i know which one. i'm not telling you.
  - ➤ _"why do they want soup?"_ → why
  - ➤ _"i'll be careful."_ → careful
- **[why]**
  - _Sharon stirs the pot for a long second._
  - **BIG SAUCE SHARON:** they've got a lot of mouths over there, love. don't ask me how many. go on.
  - _does: flag:asked_sharon_soup_
- **[careful]**
  - **BIG SAUCE SHARON:** you'll be careful or you'll be ladled.

#### Talk: `car_ride` (with LUMPS)
- **[start]**
  - _Pallet Jack lifts Sharon's pot into the car with one hand. The boiler in his back hisses when he bends and nobody on the street looks round. He tells Lumps his squat form is "a bit sad"._
  - **PALLET JACK:** that pot's ninety. the soup's another sixty. the worry's free.
  - _Lumps sits with the pot in his lap, both enormous forearms around it like a baby._
  - **LUMPS:** slower on the bumps. she's full to the top.
  - _the car goes over a bump. A little soup jumps out. He catches it in his hand and puts it back._
  - **LUMPS:** ...nobody saw that.
  - ➤ _"what's the gut?"_ → gut
  - ➤ _"why do you go there?"_ → why
  - ➤ _"how did you get those arms?"_ → arms
- **[gut]**
  - **LUMPS:** it's where they put the dead. after. millions of them. gristle and sons had this stuff, regrowth. made to bring soldiers back.
  - **LUMPS:** it brought them back. just not as soldiers. as... a place.
  - **LUMPS:** it's warm. it digests. you'll see. try not to touch the walls.
  - **LUMPS:** it's still in the rain, nan says. leave a chair out for a year and it gets a pulse. so we don't leave things out. or people.
  - ➤ _"why do you go there?"_ → why
- **[why]**
  - **LUMPS:** sundays. i visit my mum.
  - _He looks out of the window. The Ring Road is still the evening rush of the last day: three lanes, nose to tail, for sixty-one years. There is somebody at every wheel. Every one of them has a lanyard on._
  - **LUMPS:** she's at work in the gut. two years. it's a long shift.
  - ➤ _"what kind of work?"_ → work
  - ➤ _"*leave it*"_ → leave
- **[work]**
  - **LUMPS:** ...the kind where you don't come home.
  - _he holds the pot tighter.* watch the road. there's interns._
  - _does: flag:lumps_mentioned_mum_
- **[leave]**
  - _He nods, grateful._
  - **LUMPS:** watch the road. there's interns.
  - _does: flag:lumps_mentioned_mum, standing.bottom:+1_
- **[arms]**
  - **LUMPS:** born with them. my mum's got them too. smaller.
  - **LUMPS:** the doctors in chrome gristle said they'd buy them off me. a year of medicine for the left one. i said they're my arms. they said not for long.
  - **LUMPS:** i hit one. by accident. i said sorry.
  - ➤ _"why do you go to the gut?"_ → why

#### Talk: `eotm_robbery` (with EMPLOYEE OF THE MONTH)
- **[start]**
  - _The Ring Road, under a flyover. The wall has a bus queue burnt onto it: eleven shadows, waiting. The Unpaid have drawn a lanyard on each one in marker pen._
  - _War-rigs made of buses and forty office desks block the Ring Road. Interns in office-chair armour pile out. A huge man in filing-cabinet armour covered in plaques of his own face climbs on a car roof._
  - **EMPLOYEE OF THE MONTH:** HALT. YOU ARE ENTERING A WORKSPACE.
  - **EMPLOYEE OF THE MONTH:** i am EMPLOYEE OF THE MONTH. every month. since the end of the world.
  - **EMPLOYEE OF THE MONTH:** you're robbed. also: would you like an internship? it's unpaid.
  - ➤ _"what does the internship involve?"_ → intern
  - ➤ _"you can have the coupons. not the soup."_ → pay
  - ➤ _"*draw a weapon*"_ → fight
- **[intern]**
  - **EMPLOYEE OF THE MONTH:** exposure. networking. a lanyard. a fun office culture. we're a family.
  - **EMPLOYEE OF THE MONTH:** you'd start in robbery and work your way up to also robbery.
  - **LUMPS:** we're delivering soup.
  - **EMPLOYEE OF THE MONTH:** SOUP IS A CORE PRODUCT. fine. take the lanyard anyway. think about it. the grind never stops.
  - _He takes it off a hook on the rig. There are a few hundred on the hook. The INTERN sticker on yours is stuck over somebody's name._
  - → leave
  - _does: give:unpaid_lanyard, flag:eotm_offered_internship_
- **[pay]**
  - _he weighs the coupons in a gauntlet made of a stapler._
  - **EMPLOYEE OF THE MONTH:** a strong negotiator. that's a soft skill. i respect soft skills.
  - **EMPLOYEE OF THE MONTH:** go. tell the first intern i sent you.
  - → leave
  - _does: coupons:-40, flag:paid_the_unpaid_
- **[fight]**
  - **EMPLOYEE OF THE MONTH:** oh, a disruptor. we LOVE disruptors. INTERNS. ONBOARD THEM.
  - _does: flag:fought_the_unpaid_
- **[leave]**
  - _The rigs pull back, honking. Then a second wave of interns who didn't get the memo come screaming over the cars anyway._
  - **LUMPS:** i think there's two departments.

#### Talk: `trade_post` (with SISTER AGENDA)
- **[start]**
  - _A trade post on the Gut border, where the last lamp post has grown a fingernail. A turnstile grown over with skin, a counter, a robed Choir clerk with a stretched smile who sings her words on one note. Her staff lanyard is still on, under the robe._
  - _sung* the soup, the soup, the tomato soup... *not sung* thank you. one pot. we'll count it._
  - _She tips a little out and tastes it with a ladle that has a tongue._
  - ➤ _"what's it for?"_ → for (if flag:asked_sharon_soup)
  - ➤ _"is this all the medicine?"_ → short
  - ➤ _"*take the medicine*"_ → take
- **[for]**
  - _sung* for the mouths, for the mouths... *not sung* sorry. i'm not allowed to say. it's a supply chain thing._
  - → take
- **[short]**
  - **SISTER AGENDA:** it's... one box is for a 'growth adjustment'. it's empty. i'm sorry. it's policy. i don't write the policy. i write it down.
  - → take
  - _does: flag:medicine_short_
- **[take]**
  - _A crate of medicine slides across the counter._
  - **SISTER AGENDA:** same time next week. the tomato. the bishop likes the tomato.
  - _Somewhere behind the counter, a long way in, a truck is reversing. It beeps. She sings a little louder until it stops._
  - _Lumps is looking past her, deeper into the Gut, at the pink streets._
  - **LUMPS:** ...it's sunday tomorrow.
  - _does: give:medicine_crate_

#### Choice: Employee of the Month robs you and offers an internship.
- **ask about the internship**: You keep the Unpaid lanyard. Low-rank raiders sometimes wave you through on The Commute. EOTM remembers you as 'our newest intern' in his world-boss fight.
- **pay them off**: Costs 40 coupons. The Unpaid leave the Bottom's soup runs alone for the rest of Act I.
- **fight**: A bigger ambush. Better loot. The Unpaid raid the Bottom's next soup run without you (a short side activity in Act II).

**Reward:** 300 coupons, medicine_crate, lt_mission_rare
**Review card:** EXCEEDS EXPECTATIONS. not a drop spilled. sharon is suspicious. / MEETS EXPECTATIONS. most of the soup arrived. / SEE ME. you delivered a pot of nothing. the choir sang about it.
_Builder notes: soup slosh: a hidden 0-100 meter; hard landings, car-on-car hits and barrel rolls take chunks; at 0 set soup_spilled (Sharon's next lines change, the medicine is short). It should be hard to fail on purpose and very funny to fail by accident._

---

### 3. SOMETHING'S DIGESTING `m03_somethings_digesting`
_It's Sunday. Lumps visits his mum in the Gut, and the Choir tells you where Gristle & Sons gets its feedstock: ☺ CORP sells it the people who fall behind on their back pay._

**Where:** The Gut Border (THE GUT), Peristalsis Avenue (THE GUT), The Choir Lung (THE GUT), The Digester Wall (THE GUT), The Feed Dock (THE GUT)  
**Who:** LUMPS, DOT, SISTER AGENDA, THE STOMACH BISHOP, MINA  
**Giver:** LUMPS · **Needs:** m02_sauce_run

**Mechanic hook:** the Gut teaches flow: slide on Peristalsis Avenue's squeeze, swing the rib arches, bounce the lungs, and a long swing fills HYPE for the first time _(uses: slide, the grapple, hype)_

**Beats**
- C3: driving into the Gut. Skin streets, rib arches, the Choir turning. A woman in the wall says 'ambrose?'
- On foot: peristalsis streets carry you, lungs bounce you. Lumps knows the way and hates it.
- Dot in the digester wall. Chatty, warm, half absorbed. She does her names every morning so she doesn't dissolve: 'sharon, dumpling's dad, old ken, the twins from the top terrace, mina...' (the last name means nothing to you yet).
- Lumps tries to pull her out, as he does every week. The wall holds on. Dot tells him to stop.
- Sister Agenda in the Choir Lung: she keeps the real minutes. The trucks come at four. They're from your hill. ☺ CORP sells Gristle & Sons the people who fall behind on back pay. Dot was one.
- From the gallery you see the Stomach Bishop conducting, far below, over the acid lake. He sees you. He smiles, very wide.
- Stomach-dogs chase you out. Lumps carries you over the last lung.

**The mystery**
- _learn:_ ☺ CORP sells people who can't pay their 'back pay' to Gristle & Sons as feedstock. The Bottom's missing people are in the Gut wall, alive. Lumps' mum is one of them.
- _suspect:_ The name 'mina' in Dot's list is someone you'll meet. The Bishop knows exactly who you are.
- _withheld:_ What the feedstock is for (the organs; Hask). The soup keeps the digesters alive (m20).

**Objectives**
1. drive into the gut · scene `c3_its_breathing`
2. follow lumps down peristalsis avenue
3. talk to lumps' mum
4. find out where the trucks come from
5. get out of the gut

#### Scene: `c3_its_breathing` (cinematic, 45 s, music: gut_choir_chord)
- `  0` _Driving into the Gut for the first time. The tarmac goes soft, then pink, then ribbed. The tyres squelch. The headlights catch veins in the kerb._
- `  6` **LUMPS:** don't touch the walls. they like it.
- `  9` _A rib arch rises over the avenue like a cathedral roof. It isn't one big rib. It's a great many ordinary ones grown end to end, and there's a helmet in it. Lungs inflate between the buildings and the whole street breathes in. A launderette with a tongue for a door._
- ` 15` _The Gut Choir, robed, puppet faces stretched into permanent smiles, staff lanyards still on under the robes, lining the street, turn their faces to the car all at once._
- ` 20` **CHOIR:** *one long chord, held, on the word* welcome.
- ` 24` _Among the choir, grown half into the wall of a building, are faces that aren't singing: normal faces, Off-Spec faces, people from the Bottom. A small round woman in curlers looks straight at the car._
- ` 29` **DOT:** ambrose?
- ` 31` _Lumps freezes. He's heard her say it before, every Sunday. It still hits him._
- ` 34` **LUMPS:** ...hi mum.
- ` 37` **DOT:** you've brought a friend. a plastic friend. lovely. have you eaten?
- ` 41` **LUMPS:** *to you, quiet* park the car. we'll walk from here.

#### Talk: `sunday` (with DOT)
- **[start]**
  - **DOT:** ambrose! you came. it's sunday, isn't it? i can tell by your face. you've got your sunday face.
  - **LUMPS:** brought you soup, mum. the yellow.
  - **DOT:** oh, the yellow. lovely. put it there, i'll have it later.
  - _There's a row of untouched bowls along the foot of the wall. Every week's soup: a hundred and three of them, the oldest grown over. Lumps puts this one at the end of the row. He counts them. He always counts them._
  - **DOT:** and who's this? oh, look at your knee. it goes the wrong way. that's character.
  - ➤ _"i'm change. i came out of a machine."_ → machine
  - ➤ _"are you all right in there?"_ → allright
  - ➤ _"how long have you been in the wall?"_ → long
- **[machine]**
  - **DOT:** a machine! well, we all came out of something. ambrose came out of me and he was the size of a fridge.
  - **LUMPS:** mum.
  - **DOT:** he was.
  - → names
- **[allright]**
  - **DOT:** oh, it's warm. don't make that face, it is. the worst bit is you stop minding.
  - **DOT:** that's why i do my names. every morning.
  - → names
- **[long]**
  - **DOT:** two years in may. or is it june. the wall doesn't have months. it has... digestion.
  - → names
- **[names]**
  - **DOT:** i do the names every morning so i don't go soft at the edges. everyone in here. everyone i know.
  - _She closes her eyes, like a prayer._
  - **DOT:** sharon. dumpling's dad. old ken. the twins from the top terrace. little pim's nan. ambrose. ambrose. ambrose. ...and mina. mina's further in. she's quiet but she's there.
  - _She opens her eyes.* see? all there._
  - → pull
  - _does: flag:heard_dot_names_
- **[pull]**
  - **LUMPS:** *grabs her hands* i'm getting you out. i'll pull. i'm strong. i've been training.
  - _He pulls. The wall pulls back. Something wet tears and Dot gasps and Lumps lets go like he's been burned._
  - **DOT:** ambrose. ambrose, love. stop. it doesn't let go, it just hurts.
  - **LUMPS:** *very quiet* sorry. sorry, mum.
  - ➤ _"we'll find a way to get you out."_ → promise
  - ➤ _"is there anything we can do?"_ → anything
  - ➤ _"*put a hand on Lumps' shoulder*"_ → shoulder
- **[promise]**
  - _She looks at you, then at her son._
  - **DOT:** don't promise him things, plastic. he holds on to promises. look at his arms. he holds on to everything.
  - **DOT:** ...but thank you.
  - → bye
  - _does: flag:promised_dot, standing.bottom:+3_
- **[anything]**
  - **DOT:** find out who keeps sending the trucks. the singing lady upstairs writes it all down. she's got a book.
  - → bye
- **[shoulder]**
  - _Lumps doesn't look round. He puts his huge hand over yours._
  - **DOT:** that's nice. that's a nice friend you've got there, ambrose.
  - → bye
  - _does: standing.bottom:+1_
- **[bye]**
  - **DOT:** go on. both of you. and eat something. i mean it. i can see your ribs from here, ambrose. and yours, plastic. you've got the plastic kind.
  - _As you go she turns to the wall beside her, to a face that's in up to the eyes, and starts telling it what you were wearing._

#### Talk: `minutes` (with SISTER AGENDA)
- **[start]**
  - _The Choir Lung: a cathedral that breathes in and out, robes swaying with it. Sister Agenda sits at an office desk grown into a pew, with a Filofax grown into her hand._
  - _sung* the meeting is moved, the meeting is moved... *not sung* oh. you. from the trade post. sorry about the box._
  - **SISTER AGENDA:** you want to know about the trucks. everyone who comes to this desk wants to know about the trucks.
  - ➤ _"where do they come from?"_ → where
  - ➤ _"who's in them?"_ → who
  - ➤ _"why do you write it down?"_ → why
- **[where]**
  - **SISTER AGENDA:** your hill. the bottom. the lates sometimes, and the commute. wherever people owe.
  - **SISTER AGENDA:** ☺ corp counts who's behind on their back pay. when you're far enough behind, they don't send a letter. they send mr. overtime. and then a truck.
  - → sold
- **[who]**
  - **SISTER AGENDA:** the ones who owe the most. or the biggest. or the slowest. it's a list. i don't make the list. i get a copy.
  - _She opens the Filofax. Hundreds of pages of names in tiny neat handwriting. Dates. Truck numbers. A weight beside each name, to the nearest half kilo._
  - → sold
- **[why]**
  - **SISTER AGENDA:** somebody should. the bishop sings it. i write it. singing is how you forget a thing. writing is how you keep it.
  - → sold
- **[sold]**
  - **SISTER AGENDA:** they're sold. ☺ corp sells them to us. gristle and sons. as feedstock.
  - **SISTER AGENDA:** each one is credited against your hill's back pay. then the interest goes back on. i've checked. the balance has never gone down.
  - **SISTER AGENDA:** the gut grows on them. and we... harvest.
  - _She looks at her own hand, the Filofax grown into it._
  - **SISTER AGENDA:** i'm not proud. i'm just still at my desk.
  - ➤ _"harvest what?"_ → harvest
  - ➤ _"who buys what you harvest?"_ → buys
- **[harvest]**
  - _sung, very quietly* organs, organs, fresh and new... *not sung* the good ones go up the hill. i don't know who to. i only get the outgoing copy._
  - → end
  - _does: flag:learned_feedstock_
- **[buys]**
  - **SISTER AGENDA:** up the hill. that's all it ever says. UP THE HILL. priority. someone up there needs a lot of parts.
  - → end
  - _does: flag:learned_feedstock_
- **[end]**
  - _Far below, past the gallery rail, the Stomach Bishop conducts the whole district with a femur. He stops. He looks straight up at you. His smile keeps going after it should have stopped._
  - _sung* oh dear. he's seen you. *not sung* he likes new faces. go home. go home before four._

**Reward:** 200 coupons, lt_mission_rare
**Review card:** EXCEEDS EXPECTATIONS. you didn't touch the walls once. / MEETS EXPECTATIONS. you touched the walls. they liked it. / SEE ME. a stomach-dog has your shoe.

---

### 4. CLOCKING IN `m04_clocking_in`
_Mr. Overtime comes down the Long Stairs to collect two hundred and forty-four quarters of back pay, in people. First nemesis fight._

**Where:** The Sunset Wall (THE BOTTOM), The Long Stairs (THE BOTTOM), The Gut Border (THE GUT), Top of the Long Stairs (THE GUT)  
**Who:** MR. OVERTIME, LUMPS, AUNTIE SPREADSHEET, MINA, DUMPLING, WEE GORDO, PALLET JACK  
**Giver:** AUNTIE SPREADSHEET · **Needs:** m03_somethings_digesting

**Mechanic hook:** Overtime's missed staples stay in the walls as grapple points; the collectors' water tank soaks him (wet clockwork runs slow); Lumps throws you the Redline when you're low _(uses: the grapple, soak and shock, the redline)_

**Beats**
- C4: sunset, the clocks stop, the brogues on the stairs. The collectors load people into a Gristle & Sons truck: Dumpling's dad, others, and an old woman with a braid who looks at you and says 'rory?'.
- Lumps stands in front of the truck. Overtime staples his arm to it.
- Boss fight: MR. OVERTIME (overtime_1) on the Gut border, where the stairs go soft and the lungs bounce you over his slams.
- At half HP he takes a coffee break.
- The Heart Rip: you tear a piece of the punch-clock out of his chest. He staggers, checks his watch, and retreats up the hill. 'this isn't finished. it's rescheduled.'
- The truck is already gone, into the Gut. You can chase it or stay with Lumps (a choice; both cost something).
- Aftermath: Pallet Jack comes back from a delivery up the Long Stairs to find nine gone. He picks Dumpling up off the floor from under the table and says nothing at all.

**The mystery**
- _learn:_ Mr. Overtime is ☺ CORP's collector, polite and unstoppable. Someone on the truck knows a name that might be yours: 'rory'.
- _suspect:_ Overtime treats everyone as 'absent', like he doesn't know the world ended. The old woman knew you.
- _withheld:_ Who Mina is (Act II, m10). That Overtime is a recording too (Act II).

**Objectives**
1. _(scene)_ · scene `c4_clocking_in`
2. stop mr. overtime · **boss: MR. OVERTIME**
3. _(scene)_ · scene `mo_heart_rip`
4. the truck
5. go back to the lost & found

#### Scene: `c4_clocking_in` (cinematic, 62 s, music: overtime_theme)
- `  0` _The Bottom at sunset. Kids on scooters. Washing on the lines. Lumps at the sunset wall, crying a little. Auntie on a step, doing the books in crayon._
- `  3` **LUMPS:** *sniff* it's the sunset. it does this.
- `  7` _Every clock in the settlement stops at once: the kitchen clocks, the wristwatches, the broken district clock over the Lost & Found, the egg timer on Sharon's pot. Silence. Then a single loud tick, from up the hill._
- ` 11` **AUNTIE SPREADSHEET:** *not looking up* oh no.
- ` 13` _Huge polished brogues step down the Long Stairs. Each step cracks a step. Ticking. A grey suit stretched over pistons. A punch-clock where a heart should be._
- `13.2` 
- ` 19` _Behind him, a Gristle & Sons truck backs down the stairs on caterpillar tracks, and Timekeeping collectors with clipboards fan out._
- ` 22` _Mr. Overtime stops at the bottom of the stairs. He takes out a clipboard. He checks his watch. He is exactly on time._
- `22.5` 
- ` 25` **MR. OVERTIME:** good evening. the bottom. two hundred and forty-four quarters of back pay. i'm here to collect.
- ` 31` **AUNTIE SPREADSHEET:** for a job none of us had.
- ` 34` **MR. OVERTIME:** you're all absent. you've been absent for a very long time. this will only take a minute. it will take exactly a minute.
- ` 39` _The collectors start loading people into the truck: an old man, Dumpling's dad (Dumpling screams), a woman with a baby (put back: the baby's not on the list, the woman is). An old woman with a grey braid and climbing gloves is pushed up the ramp._
- ` 45` _The old woman with the braid sees you. She stops on the ramp. She stares at your face, your barcode, your knee._
- ` 48` **MINA:** ...rory?
- ` 50` _The doors slam on her._
- ` 51` _Lumps walks out and stands in front of the truck. He's bigger than it._
- ` 54` **LUMPS:** sorry. no.
- ` 56` **MR. OVERTIME:** you're obstructing a scheduled vehicle. that's against policy.
- ` 58` _Overtime fires a staple the size of a crowbar through Lumps' forearm into the truck's bumper. Lumps doesn't scream. He looks at it, then at you._
- ` 61` → BOSS INTRO: MR. OVERTIME · HEAD OF TIMEKEEPING

#### Scene: `mo_heart_rip` (moment, 3 s)
- `  0` _Slow motion. Your hand goes into the cracked punch-clock in Overtime's chest and pulls out a piece of it: a cog, a spring, a bit of clock face, wet._
- `1.5` _It's warm. It ticks in your hand._
- `2.5` **HEART RIP**

#### Talk: `rescheduled` (with MR. OVERTIME)
- **[start]**
  - _Overtime on one knee, steam pouring out of the hole in his chest. The ticking has a limp in it. He looks at his watch. Then at you. Then at the watch._
  - **MR. OVERTIME:** you've damaged company property.
  - **MR. OVERTIME:** that's... that's me. i'm company property.
  - _He stands. It takes a while.* this isn't finished. it's rescheduled._
  - _He walks back up the Long Stairs, exactly on time, a little lopsided. At the top he stops and looks back at you for a long moment, like he's trying to remember where he put something._
  - _When his ticking has gone up the hill the clocks don't start again straight away. Nobody comes out. A washing line is still swinging where somebody let go of it._

#### Talk: `aftermath` (with AUNTIE SPREADSHEET)
- **[start]**
  - _The walk down. Nine doors standing open. On each one a ☺ CORP slip, stapled at head height: COLLECTED, a name, a time to the second, BALANCE CARRIED FORWARD. The dinners are still on the tables. The egg timer on Sharon's pot has started again._
  - _The Lost & Found. Gordo stitching Lumps' arm with fishing line. Dumpling asleep under the table with his dad's hat out of the lost property bins. Auntie, writing names in crayon on the wall, one under another._
  - **AUNTIE SPREADSHEET:** nine. they took nine.
  - _She writes the eighth name. Under it, after a pause, she writes the ninth: 'mina'. Just the first name. She knew it._
  - _Pallet Jack comes back from a delivery up the Long Stairs to find nine gone. He picks Dumpling up off the floor from under the table and says nothing at all._
  - ➤ _"the old woman on the truck called me rory."_ → rory
  - ➤ _"we'll get them back."_ → back
  - ➤ _"who's mina?"_ → mina (if flag:heard_dot_names)
- **[rory]**
  - _The crayon stops._
  - **AUNTIE SPREADSHEET:** did she.
  - **AUNTIE SPREADSHEET:** ...people say a lot of names when they're being put on a truck, change. they say the names of whoever they wish was there.
  - **WEE GORDO:** *not looking up* that's not an answer, auntie.
  - **AUNTIE SPREADSHEET:** it's the one i've got, gordon.
  - → end
  - _does: flag:asked_about_rory_
- **[mina]**
  - _She doesn't turn round._
  - **AUNTIE SPREADSHEET:** mina's lived on the top terrace for forty years. she climbs better than the kids. she taught half of them.
  - **AUNTIE SPREADSHEET:** she's seventy. they took a seventy-year-old woman for back pay.
  - → end
- **[back]**
  - **AUNTIE SPREADSHEET:** from the gut? nobody's ever come back from the gut, change.
  - **LUMPS:** nobody's ever ripped his heart out before.
  - _Auntie looks at Lumps' arm. At the hole in it._
  - **AUNTIE SPREADSHEET:** ...no. nobody had.
  - → end
  - _does: standing.bottom:+2_
- **[end]**
  - _Dale comes in from the Machine for the first time anyone can remember. He's holding the core in a tea towel. It ticks._
  - **DALE:** it's still going. his heart. well, a bit of it.
  - **WEE GORDO:** we could sell it. chrome gristle'd give a year of medicine for that. same as they offered for his arm.
  - **DALE:** or we could put it in someone who doesn't mind ticking.
  - _Everyone looks at you. Auntie looks at the wall first._

#### Choice: The truck is getting away into the Gut. Lumps is pinned to the ground by a staple through his arm.
- **chase the truck**: You catch the truck as it passes under the first rib arch. You can't open it: the doors have grown shut. Through the slot the old woman with the braid looks out and says 'rory' again, quieter, like a question she's sure of. You learn the truck's number (it matters in m20). Lumps gets himself free by tearing the staple out of the bumper; it leaves a scar he shows people.
- **stay with lumps**: You pull the staple out of Lumps' arm. He doesn't cry until it's out, then he does. 'thanks. sorry. thanks.' Lumps trusts you more (his Act III choice is easier to steer). You don't get the truck number; Sister Agenda has to find it for you in m20.

**Reward:** 500 coupons, core_cracked_punch_clock
**Review card:** EXCEEDS EXPECTATIONS. you made employee #1 take a coffee break. the truck left on time. / MEETS EXPECTATIONS. he's been rescheduled. / SEE ME. you were stapled to a truck for eleven seconds.
_Builder notes: people taken in C4 stay taken unless m20 frees them (DESIGN §7.1). Nine names on the wall: they are the m20 rescue list. The nine doors stay open with their COLLECTED slips on them until m20 (older slips on other doors are already there in C1)._

---

### 5. SECOND STOMACH `m05_second_stomach`
_A Meat Mechanic installs the piece of Overtime's heart in your chest. Implants unlocked. For a second you remember a lobby, a pair of running shoes, and the time: 17:29._

**Where:** Bev's Clinic (THE GUT), The Lost & Found (THE BOTTOM)  
**Who:** AUNTIE SPREADSHEET, BEV, DALE, MR. OVERTIME, PALLET JACK  
**Giver:** DALE · **Needs:** m04_clocking_in

**Mechanic hook:** the first install: the clinic chair is the implant UI, and the Punch-Clock's tick is your first downside _(uses: bio-implants)_

**Beats**
- Auntie takes you to Bev's clinic on the Gut border.
- In Bev's waiting room: Pallet Jack, getting his boiler bled. Bev: 'you're next, jack. you're always next.'
- C5: the install. 'this is a terrible idea.' 'they're all terrible ideas. this one works.' Bev explains Drift in one line: the more of you that isn't you, the less of you there is.
- The first memory flash: a lobby, running trainers, 17:29.
- Implant tutorial: body slots, Body Budget, the Cracked Punch-Clock's perk and downside (it ticks).
- Back at the Lost & Found Auntie tries to say something and doesn't.
- P5b (moved: it plays at the end of m06, TICKETS, PLEASE): Overtime in his office looks at the still of you. CALE, R. employee 4417. deleted. late for a meeting at 17:30.

**The mystery**
- _learn:_ Your body takes organs that aren't yours. The more you take, the more you drift. You have memories. You were in a marble lobby at 17:29, running. (P5b, at the end of m06) Your name, according to ☺ CORP, is CALE, R., employee 4417. Deleted.
- _suspect:_ 'rory' and 'cale, r.' are the same person. Auntie is scared of what you'll remember.
- _withheld:_ Who Cale was, and what they were running with (Act II).

**Objectives**
1. take the core to the meat mechanic on the gut border
2. _(scene)_ · scene `c5_second_stomach`
3. check your new part
4. go home

#### Scene: `c5_second_stomach` (cinematic, 48 s, music: bev_clinic_drip)
- `  0` _A back-room clinic on the Gut border behind a butcher's curtain. A dentist's chair. A bucket. Bev, four arms, headlamp on, scrubbing two hands while the other two light a cigarette._
- `  4` _Auntie holds the punch-clock core in a tea towel. It ticks through the cloth._
- `  7` **AUNTIE SPREADSHEET:** this is a terrible idea.
- `  9` **BEV:** they're all terrible ideas. this one works.
- ` 12` **BEV:** chassis, lie back. you're plastic, so this won't hurt. that's a lie. i say it to everyone.
- ` 17` _Bev opens your mannequin chest like a cupboard. It's empty: a bracket where a heart would go, and a stock number. Auntie looks away. Then makes herself look back._
- ` 21` **AUNTIE SPREADSHEET:** will they still be... them? after?
- ` 24` **BEV:** one part, yes. ten parts, ask me again. the more of you that isn't you, the less of you there is. that's not medicine, that's maths.
- ` 30` _Black. A single TICK._
- ` 32` _A flash, 0.8 s, washed out like old video: a marble lobby, a revolving door, a pair of scuffed trainers running across the floor, your trainers. A clock on the wall: 17:29._
- ` 34` _You wake in the chair. A clock face glows in your chest. It ticks._
- ` 37` **BEV:** welcome back. how many fingers?
- `38.5` _She is holding up four hands. Two of them are a different colour from the rest of her. One has the dent of a wedding ring._
- ` 40` **AUNTIE SPREADSHEET:** *quiet* what did you see?
- ` 43` _Auntie watches your face as if she already knows the answer._

#### Talk: `bev_intro` (with BEV)
- **[start]**
  - _Bev's waiting room. A bench of car seats, full: a woman holding her own jaw in a tea towel, a man with the price still chalked on his new arm, Pallet Jack with a tube in his back and a bucket under it, getting his boiler bled. Nobody is nervous. It's like a barber's._
  - **BEV:** you're next, jack. you're always next.
  - _Bev doesn't look up from a jar.* close the curtain. the flies are union._
  - _She is writing on the jar's tape: a date, a truck number. The shelf behind her goes up to the ceiling. A few of the jars have a first name on as well._
  - **BEV:** the named ones go half price. same part. people just don't like being introduced.
  - **BEV:** so you're the thing from the machine. huh. thought you'd be taller.
  - **AUNTIE SPREADSHEET:** can you put this in it? them. in them.
  - _Bev takes the tea towel, unwraps the ticking core with two hands, and lights a cigarette with a third._
  - **BEV:** a bit of overtime's heart. you know how many people have walked in here with a bit of overtime? none. you know why? he doesn't come apart.
  - ➤ _"will it hurt?"_ → hurt
  - ➤ _"what will it do to me?"_ → do
  - ➤ _"how much?"_ → much
- **[hurt]**
  - **BEV:** you're plastic. no. that's a lie. i say it to everyone. lie back.
- **[do]**
  - **BEV:** make you tick. make you fast when you're dying. make you late if you don't clock in. it's a heart. it's got opinions.
- **[much]**
  - **BEV:** depends what you want. everything on that shelf, somebody's already paid for once. you'd only be paying me.
  - **BEV:** first one's free. that's not kindness, that's marketing. lie back.

#### Talk: `parts` (with BEV)
- **[start]**
  - **BEV:** right. listen, chassis, because i only say this once and then i charge.
  - **BEV:** you've got slots. head, eyes, mouth, heart, lungs, guts, spine, arms, legs, skin. that's ten places to put a bad decision.
  - **BEV:** and don't go precious on me. half your hill's got something of mine in. jack's whole back. ken abara's hip, and that went up on the truck with him, so that's twice somebody's lost it. lumps is the only one who ever said no, and he said sorry first.
  - **BEV:** your body's got a budget. three parts now. more as you... go up in the world. promotions. ask the cats.
  - **BEV:** go over the budget and it'll still work. you'll lump. you'll twitch. and you'll drift.
  - ➤ _"drift?"_ → drift
  - ➤ _"the cats?"_ → cats
  - ➤ _"why does it tick?"_ → tick
- **[drift]**
  - _She takes the cigarette out._
  - **BEV:** you came out of that machine as somebody. a recording of somebody. every part that isn't yours pushes that somebody a bit further off.
  - **BEV:** you won't notice. that's the thing. the people who love you notice.
  - **AUNTIE SPREADSHEET:** *very quietly* ...yes.
  - _does: flag:bev_explained_drift_
- **[cats]**
  - **BEV:** the board of directors. cats. they're all over the city. pet one, your body takes it as a promotion. don't ask me why. i'm a mechanic, not a vet.
- **[tick]**
  - **BEV:** it's a punch-clock. it wants you to clock in. once an hour, stand still and let it. or it'll fine you.
  - _Your chest goes TICK. Then TICK. Loudly._
  - **BEV:** yeah. everybody's going to hear you coming. welcome to having a heart.

#### Talk: `night` (with AUNTIE SPREADSHEET)
- **[start]**
  - _The walk back from Bev's. Auntie went ahead; she said she had a column to finish. The Long Stairs at night, nobody on them. Every tick comes back off the houses a little late. The nine doors are still open._
  - _The Lost & Found at night. The Machine hums. Your chest ticks, and after a minute the hum has moved to be in time with it. Auntie at the table with the notebook open and no crayon in her hand._
  - **AUNTIE SPREADSHEET:** you saw something. in the chair. bev said you went somewhere.
  - ➤ _"a lobby. someone running. 17:29."_ → lobby
  - ➤ _"nothing."_ → nothing
- **[lobby]**
  - _She closes the notebook._
  - **AUNTIE SPREADSHEET:** 17:29.
  - _For a moment she looks like she's going to say a lot of things. She picks up a crayon. Puts it down._
  - **AUNTIE SPREADSHEET:** ...it's late. sixty-one years late, everything in this city. go to sleep, change.
  - _does: flag:told_auntie_1729_
- **[nothing]**
  - _She looks at you over her glasses, the look she gives a bad invoice._
  - **AUNTIE SPREADSHEET:** you're a terrible liar. good. keep it that way. go to sleep.
  - _does: flag:lied_to_auntie_1_

**Reward:** 200 coupons, core_cracked_punch_clock
**Review card:** EXCEEDS EXPECTATIONS. one heart, installed, ticking. / MEETS EXPECTATIONS. you have a pulse. it's not yours. / SEE ME. you asked bev for a refund.

---

### 6. TICKETS, PLEASE `m06_tickets_please`
_The only other way into the Gut is the commuter line under the hill. Nobody takes it, because the tunnel eats. Four of you go in. The thing that follows you out is wearing the company's face._

**Where:** The Lost & Found (THE BOTTOM), The Service Tunnel (THE BOTTOM), The Under-Hill Loop (THE COMMUTE), The Tunnel Mouth (THE COMMUTE)  
**Who:** WEE GORDO, LUMPS, PALLET JACK, DALE, BEV, AUNTIE SPREADSHEET, DUMPLING, REVENUE PROTECTION  
**Giver:** WEE GORDO · **Needs:** m05_second_stomach

**Mechanic hook:** a boss you fight from the back of a moving train with a gun that fires your own blood; the fight is unwinnable until you take a dead friend's marrow _(uses: blood cross, overdrive rig, bio-implants, slide, blood drive)_

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
1. meet gordo at the lost & found
2. get fitted
3. board the train
4. _(scene)_ · scene `c6_mind_the_gap`
5. keep it off the train · **boss: REVENUE PROTECTION**
6. _(scene)_ · scene `mo_carry_the_bit_that_works`
7. break its face · **boss: REVENUE PROTECTION**
8. _(scene)_ · scene `c6b_terminus`
9. _(scene)_ · scene `p5b_employee_4417`

#### Scene: `c6_mind_the_gap` (cinematic, 88 s)
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
- ` 85` _From behind the face, four hundred voices, not together:_ **REVENUE PROTECTION:** tickets, please.
- ` 87` → BOSS INTRO: REVENUE PROTECTION · TICKETS, PLEASE

#### Scene: `mo_carry_the_bit_that_works` (moment, 70 s)
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
- ` 50` _The prompt appears: [FIRE]. Nothing else on the HUD. The game does not do it for you. The Snatchers are four metres away. If you wait, he says: PALLET JACK: go on. it's not heavy._ → CHOICE: fire
- ` 52` _You fire. One bolt. It sticks. He breathes out. The cross comes, and it's small, and it's quick._
- ` 54` _His hand comes off yours and stays open on the deck._
- ` 56` _The prompt appears: [TAKE]. Your hand goes in through the split boiler, the same motion as the Heart Rip, slower. What comes out is a length of spine the colour of a traffic light, wet, and warm, and still making blood: it runs down your arm and into the cradle and all six barrels fill at once._ → CHOICE: take
- ` 60` _Your mannequin back opens along the seam. It goes in. No clinic, no chair, no Bev. The Blood Drive's ring starts to turn without you asking it to._
- ` 62` _The Snatchers reach Jack. They pick him up. They turn him over. They put him down. There's nothing there for them._
- ` 64` _Lumps has turned round. He is looking at you, and at your arm, and at Jack. It's the first time he's looked at you like you might be a thing._
- ` 66` **WEE GORDO:** *hoarse* lumps. LUMPS. rail.
- ` 67` _The mask hauls. THE GAP reads 6 m. Your HP bar is full, and then past full, and it is not your colour._
- ` 68` **PENALTY FARE**

#### Scene: `c6b_terminus` (cinematic, 52 s, music: auntie_theme_crayon)
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
- ` 52` _→ p5b_employee_4417, then END OF ACT I_

#### Scene: `p5b_employee_4417` (panels, 18 s, music: overtime_theme_low)
- `  0` [panel 1] _meanwhile, at ☺ CORP..._ (TICK) _A spotless office on Corp Hill. Mr. Overtime, sitting at a desk far too small for him, with a fresh bandage of steel plate over his chest._
- `  4` [panel 2] _He looks at a security still on his monitor: you, climbing out of the Machine's tray, taken from Dale's terminal. Your barcode, enlarged._
- `  8` [panel 3] **MR. OVERTIME:** CALE, R. employee 4417. deleted. _The screen reads: CALE, R. 4417 · STATUS: TERMINATED 17:29:41 · NEXT APPOINTMENT: MEETING 17:30 (M)._
- ` 12` [panel 4] **MR. OVERTIME:** late for a meeting at 17:30. _His hand, steady, on the screen._
- ` 15` [panel 5] (CLICK) _He takes out a new clipboard and writes your name at the top. Under REASON he writes: absent._
- ` 17` **END OF ACT I**

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

#### Choice: The Snatchers are four metres away.
- **[FIRE]**: You fire. One bolt. It sticks. He breathes out. The cross comes, and it's small, and it's quick.

#### Choice: His hand comes off yours and stays open on the deck.
- **[TAKE]**: Your hand goes in through the split boiler, the same motion as the Heart Rip, slower. What comes out is a length of spine the colour of a traffic light, wet, and warm, and still making blood: it runs down your arm and into the cradle and all six barrels fill at once.

**Reward:** loop_train, blood_drive, marrow_pallet_jack
**Review card:** NO REVIEW TODAY. / NO REVIEW TODAY. / NO REVIEW TODAY.
_Builder notes: the only mission whose grade card has no joke. Jack's vest stays on Dumpling for the rest of the game (it never fits). LEG DAY's intro changes: Lumps is carrying fridges up the Long Stairs because someone has to do Jack's round._

---
