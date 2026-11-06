# Side questlines and activities

_Generated from `side/*.js` and `activities.js`._

## THE BOTTOM

### SECURITY DEPOSIT `sq_bottom_deposit`
_Mr. Deposit has taken a deposit off everyone who's slept near his rubble pile for fifty years. Nobody has ever got one back._

**Where:** The Deposit Pile (THE BOTTOM), Sharon's Soup Kitchen (THE BOTTOM), The Lost & Found (THE BOTTOM)  
**Who:** BIG SAUCE SHARON, MR. DEPOSIT, AUNTIE SPREADSHEET  
**Giver:** BIG SAUCE SHARON · **Needs:** m02_sauce_run

**The twist:** He can't stand up: the armchairs grew into him. The deposits are all he has. And his deed is the one Vacancy will staple to the Bottom's sale in Act IV.

**Beats**
- Sharon wants her deposit back (she paid it in soup in her twenties).
- Auntie gives you her itemised invoice: forty years of rent he owes the Lost & Found for 'storage of a man'.
- Serve it. He laughs so hard a key falls out.
- Collect three tenants' receipts (each a small errand: a lost cat, a stuck washing line, a roof leak).
- Boss: MR. DEPOSIT.
- His box bursts: fifty years of deposits rain on the Bottom.

**Objectives**
1. ask sharon about the landlord
2. get auntie's invoice
3. serve mr. deposit the invoice
4. collect 3 tenants' receipts
5. get the deposits back · **boss: MR. DEPOSIT**

#### Talk: `deposit` (with BIG SAUCE SHARON)
- **[start]**
  - **BIG SAUCE SHARON:** i paid that man a deposit when i was twenty-two. in soup. forty litres.
  - **BIG SAUCE SHARON:** i want it back. i don't want the soup back, it'd be off. i want the principle back.

#### Talk: `serve` (with MR. DEPOSIT)
- **[start]**
  - _A mountain of armchairs and keys, with a rubber face at the top wearing reading glasses._
  - **MR. DEPOSIT:** a visitor! a tenant? no? a prospective tenant.
  - _You hand him Auntie's invoice. He reads it. It's forty pages. It's in crayon. The total is circled four times._
  - **MR. DEPOSIT:** 'storage of a man'. 'wear and tear on the view'. 'emotional damp'. ha! HA! *a key falls out of him* she's good. she's very good.
  - **MR. DEPOSIT:** you're not getting it back, tenant. nobody gets their deposit back. it's the one law that survived the war.

**Reward:** 800 coupons, lt_boss_landlord
**Review card:** EXCEEDS EXPECTATIONS. full refund. / MEETS EXPECTATIONS. partial refund. / SEE ME. you paid a deposit.

---

### ONE SHOE GUY `sq_bottom_one_shoe`
_A man by the Down Escalator sells one shoe for 10,000 coupons. He doesn't want to sell it. He wants the other one._

**Where:** The Down Escalator (THE BOTTOM), Tooth Market (THE GUT), Peristalsis Avenue (THE GUT)  
**Who:** ONE SHOE GUY  
**Giver:** ONE SHOE GUY · **Needs:** m03_somethings_digesting

**The twist:** The other shoe is in the Gut, and it's alive now: it walks, it has a tongue, and it doesn't want to go back. And Clement was born in a shoe shop on the first night of the Long Dark; the shoes were his dad's.

**Beats**
- Clement and his one brogue.
- Rumours: a shoe has been seen in Tooth Market, walking.
- Chase a living brogue down Peristalsis Avenue (it rides the contractions better than you).
- Catch it with the lasso. It cries.
- Choice: bring it back, or let it go.

**Objectives**
1. talk to the man with one shoe
2. find the other shoe in the gut
3. catch the shoe

#### Talk: `shoe` (with ONE SHOE GUY)
- **[start]**
  - **ONE SHOE GUY:** one shoe. very good shoe. ten thousand coupons.
  - **ONE SHOE GUY:** no, you can't have the pair. that's the problem.
  - ➤ _"why don't you want to sell it?"_ → why
  - ➤ _"where's the other one?"_ → where
- **[why]**
  - _He puts a hand on it.* they were my dad's. he had a shoe shop on hillside road. i was born in it, the first night of the long dark. mum said the shoes were the only warm thing._
  - **ONE SHOE GUY:** the other one walked off when i was ten. the gut got into it.
  - → where
- **[where]**
  - **ONE SHOE GUY:** i'll know it when i see it. it'll be the one walking.

#### Choice: The brogue squirms in your lasso. It has a little tongue. It's crying.
- **bring it back to Clement**: Clement puts it on. It stops crying when it's next to the other one. He limps anyway, out of habit, and gives you the Walking Sole (a secret implant).
- **let it go**: It runs off into the Gut. Clement laughs for the first time in years: 'good for it.' He gives you his one shoe 'for luck'. It's a legendary throwable (Sole Survivor). Weeks later, both shoes are seen walking together in Tooth Market.

**Reward:** 300 coupons
**Review card:** EXCEEDS EXPECTATIONS. a pair. / MEETS EXPECTATIONS. / SEE ME. you lost the other one too.

---

### LEG DAY `sq_bottom_leg_day`
_Help Lumps train by carrying fridges up the Long Stairs. Drop one and it rolls all the way down._

**Where:** Lumps' Gym (THE BOTTOM), The Long Stairs (THE BOTTOM), Top of the Long Stairs (THE GUT)  
**Who:** LUMPS, DUMPLING  
**Giver:** LUMPS · **Needs:** m02_sauce_run

**The twist:** It isn't training. Lumps is carrying the fridges up to the top of the stairs so that one day he can carry his mum down them. He's been practising the weight.

**Beats**
- Lumps' Gym: all the weights are fridges.
- Carry fridges up the Long Stairs (physics: drop one and it bounces down 1,000 steps, flattening bins; Dumpling commentates).
- Ten fridges. At the top, Lumps lines them up and looks over at the Gut.
- He tells you why.

**Objectives**
1. spot lumps at the gym
2. carry 10 fridges up the long stairs

#### Talk: `fridge` (with LUMPS)
- **[start]**
  - **LUMPS:** leg day. you carry one, i carry one. we go up. we don't drop them.
  - **DUMPLING:** last time he dropped one it went all the way down and through mrs. abara's kitchen.
  - **LUMPS:** i said sorry. i bought her a fridge. it was the one i dropped.

#### Talk: `why` (with LUMPS)
- **[start]**
  - _Ten fridges in a row at the top of the stairs. Lumps sits on the last one, looking at the pink edge of the Gut._
  - **LUMPS:** mum's about a fridge and a half. i weighed her once. she hit me.
  - **LUMPS:** one day i'm going to carry her down these. all of them. so i practise the weight.
  - _he wipes his eyes* it's not the sunset. we're facing the wrong way for the sunset._
  - _does: flag:leg_day_why, standing.bottom:+2_

**Reward:** 250 coupons, lumps_ring
**Review card:** EXCEEDS EXPECTATIONS. no fridges were dropped. / MEETS EXPECTATIONS. most fridges. / SEE ME. mrs. abara wants a word.

---

### WOK THE DISH `sq_bottom_wok_the_dish`
_The Bottom's satellite dishes are woks. A storm has knocked them all out. Fix them by grappling between roofs while it's still blowing._

**Where:** The Wok Roofs (THE BOTTOM), The Crayon School (THE BOTTOM)  
**Who:** DUMPLING, AUNTIE SPREADSHEET  
**Giver:** DUMPLING · **Needs:** m01_return_to_sender

**The twist:** When the last wok is aligned, every TV in the Bottom picks up the same thing: a dead ☺ CORP channel that only broadcasts at 03:00. A test card, and a voice reading the Schedule. It's the first time anyone in the Bottom has heard the Missing Hour mentioned (and the start of the Satellite Ear trail).

**Beats**
- A storm: wind, rain, washing lines whipping.
- Twelve wok dishes across the stacked roofs. Each one needs aligning (aim it at the Spire) while the wind pushes you.
- Dumpling holds the TV aerial at the Crayon School and shouts.
- The last one: every TV shows a ☺ CORP test card.

**Objectives**
1. wait for a storm
2. realign 12 wok dishes

#### Talk: `test_card` (with DUMPLING)
- **[start]**
  - _Every TV in the Crayon School flickers to a ☺ CORP test card. A smiling clock. A tinny voice:_
  - **VOICE:** ...03:00. no bookings. 03:00. no bookings. 03:00...
  - **DUMPLING:** ghost, what's 03:00?
  - **AUNTIE SPREADSHEET:** *from the doorway* turn it off, dumpling.
  - **AUNTIE SPREADSHEET:** *after a moment* ...no. leave it on. write down what it says.
  - _does: flag:heard_test_card_

**Reward:** 300 coupons
**Review card:** EXCEEDS EXPECTATIONS. perfect reception. / MEETS EXPECTATIONS. one channel. / SEE ME. you're on the roof. you're in the wok.

---

### LOST PROPERTY `sq_bottom_lost_property`
_Return ten items from the Lost & Found to their owners all over the city. One of them is a whole bus._

**Where:** The Lost & Found (THE BOTTOM), Returns Desk Zero (THE CHECKOUT), The Ring Road (THE COMMUTE), Mamma Polizza's (PINSTRIPE), Prime Lane (NUMBER WORKS)  
**Who:** DALE, WRISTBAND, GARY  
**Giver:** DALE · **Needs:** m01_return_to_sender

**The twist:** Item ten is a lunchbox with a note taped to it: 'don't be late tonight. it's our forty. love, j.' It has no owner left to return it to. Dale knows whose it is. It's one of Overtime's six memory fragments.

**Beats**
- Dale's ledger of lost things. Ten tags with names on them.
- Items: a pram (to a grandmother in Number Works), a trombone (a Punchline), a dog lead (the dog's still waiting), a wedding ring (Gary's), a bus (to the Unpaid, who are thrilled), a teddy (Wristband's, from the Stampede: he cries and gives it back to you to keep)...
- Item ten: the lunchbox. No owner. Dale tells you.

**Objectives**
1. get the lost property ledger from dale
2. return 9 items to their owners

#### Talk: `ledger` (with DALE)
- **[start]**
  - **DALE:** sixty-one years of lost things. people leave them, i keep them. it's a lost and found. the found's the hard bit.
  - **DALE:** ten tags. ten names. some of them are still around. take them back. ...not the last one. bring the last one to me.

#### Talk: `lunchbox` (with DALE)
- **[start]**
  - _A dented metal lunchbox. A note taped to the lid, in neat handwriting._
  - **DALE:** found it in the lobby of the spire. the day i went up there to fix the vending machines, years after. it was on the security desk.
  - **DALE:** 'don't be late tonight. it's our forty. love, j.'
  - **DALE:** it's his. overtime's. sallow's. he never went home to eat it.
  - **DALE:** keep it. he might want it back one day. ...people do, sometimes.
  - _does: collect:ot_lunchbox_

**Reward:** 600 coupons
**Review card:** EXCEEDS EXPECTATIONS. everything found its way home. / MEETS EXPECTATIONS. most things. / SEE ME. you kept the bus.

---

## THE GUT

### CHOIR PRACTICE `sq_gut_choir_practice`
_The Choir needs a tenor. Collect three voice boxes from overdue ☺ CORP offices._

**Where:** The Choir Lung (THE GUT), Gristle & Sons Campus (THE GUT), The Waiting Room (THE LATES)  
**Who:** SISTER AGENDA, THE STOMACH BISHOP  
**Giver:** SISTER AGENDA · **Needs:** m03_somethings_digesting

**The twist:** Sister Agenda doesn't want a tenor. She wants her own voice back: the Bishop made every singer sing on his note, and a voice box from outside the Gut is the only thing that can sing off it. The first time she uses it, she sings a single line of her own, out of tune, and the whole Choir stops to listen.

**Beats**
- Three overdue offices: a Gristle & Sons campus annexe grown shut, a Lates call centre, a Corp Hill switchboard room (Late Fees).
- Each voice box is in a dead switchboard operator's headset; each office has a short, odd encounter (a phone that keeps ringing; a hold queue of 4,000 callers; a recorded voice that still says 'your call is important').
- Bring them to Sister Agenda. She keeps one.

**Objectives**
1. talk to sister agenda
2. collect 3 voice boxes from overdue offices
3. bring them to the choir

#### Talk: `tenor` (with SISTER AGENDA)
- **[start]**
  - _sung* we need a tenor, a tenor, a tenor... *not sung* we don't. sorry. that's what i'm supposed to say._
  - **SISTER AGENDA:** bring me voice boxes. from the old offices up the hill, the ones that went overdue. three. i'll explain when you're back. if i explain now he'll hear.

#### Talk: `own_voice` (with SISTER AGENDA)
- **[start]**
  - _She holds one voice box against her throat. She takes a breath. The Choir Lung breathes with her._
  - _she sings, off his note, a single line, badly:* my name is felicity marsh and i was in accounts._
  - _The Choir stops. Every stretched face turns to her. Far below, the Bishop's baton stops in the air._
  - _not sung, shaking* ...thank you. that's the first thing i've said for myself in sixty-one years._
  - _does: flag:agenda_own_voice_

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. perfectly out of tune. / MEETS EXPECTATIONS. / SEE ME. you put a voice box on hold.

---

### REFLUX `sq_gut_reflux`
_The acid lake in the Big Stomach is rising. Plug the burping vents with cars before it reaches Bev's clinic._

**Where:** The Big Stomach (THE GUT), The Gut Border (THE GUT)  
**Who:** BEV  
**Giver:** BEV · **Needs:** m03_somethings_digesting

**The twist:** It's rising because something's been feeding it: the Unpaid have been dumping stolen ☺ CORP paperwork into it, and the Gut can't digest forms. The last vent is plugged with a filing cabinet full of Late Fees notices addressed to the Bottom. Bev reads one and laughs until she has to sit down.

**Beats**
- Six vents round the crater, burping acid on a rhythm.
- Drive cars into them (meat buggies work best: they bleed instead of smoking).
- The last vent: a filing cabinet. Late Fees notices.

**Objectives**
1. talk to bev
2. plug 6 vents with cars · timer 360s

#### Talk: `acid` (with BEV)
- **[start]**
  - **BEV:** the lake's coming up. it gets to my clinic, i lose my chairs. i lose my chairs, i lose my patients. well. the patients go in the lake.
  - **BEV:** plug the vents. with cars. it's the only thing it won't eat. it's tried.

#### Talk: `notices` (with BEV)
- **[start]**
  - _Bev with a handful of soggy Late Fees notices.* 'final notice: the bottom: 244 quarters'. 'final final notice'. 'final final final notice: we mean it'._
  - _she laughs until she has to sit down on a stomach-dog, which doesn't mind* the gut's choking on corp's bills. even the gut won't swallow them._

**Reward:** 450 coupons, lt_district_gut
**Review card:** EXCEEDS EXPECTATIONS. no chairs lost. / MEETS EXPECTATIONS. / SEE ME. you drove into the lake.

---

### HAIRBALL `sq_gut_hairball`
_Something's stuck in Peristalsis Avenue and the whole street is backed up. It's a guy's whole house._

**Where:** Peristalsis Avenue (THE GUT), The Digester Wall (THE GUT)  
**Who:** DOT  
**Giver:** DOT · **Needs:** m03_somethings_digesting

**The twist:** The house's owner is still in it, making tea. He's been travelling down the Gut's digestive tract in his house for nine years and thinks it's a very slow train. When you push the house through, he arrives at the Big Stomach, looks out of the window, and says 'oh. this isn't leeds.'

**Beats**
- Dot mentions the street's been 'a bit blocked'.
- A whole terraced house wedged in the intestine-tube avenue.
- Push it with a car, a lasso, the Shopping Cart Cannon, rockets (all work; the funniest is the sofa-car).
- The man inside offers you tea throughout.

**Objectives**
1. unblock peristalsis avenue

#### Talk: `blocked` (with DOT)
- **[start]**
  - **DOT:** the avenue's been ever so blocked. you can feel it in the wall. like when you've had too much bread.
  - **DOT:** there's a house in it. with a man in it. he waves. nice man. offers everyone tea. nobody's ever been able to take him up on it.

**Reward:** 350 coupons
**Review card:** EXCEEDS EXPECTATIONS. you had the tea. / MEETS EXPECTATIONS. it's moving. / SEE ME. you're in the house now.

---

### QUARTERLY GROWTH `sq_gut_quarterly_growth`
_Gristle & Sons wants the Gut to hit its growth target this quarter. Feed it, or sabotage the feeding tubes._

**Where:** The Feed Dock (THE GUT), Gristle & Sons Campus (THE GUT), The Long Stairs (THE BOTTOM)  
**Who:** THE STOMACH BISHOP, SISTER AGENDA, LUMPS  
**Giver:** THE STOMACH BISHOP · **Needs:** m06_option_c

**The twist:** The 'feed' isn't people this time: it's the Gut's own regrowth tubes, pumping Regrowth toward the Long Stairs. Hitting the target means the Gut grows into the Bottom's top terraces. Sabotaging it means the Choir loses a quarter's bonus, and the Bishop makes Sister Agenda write it down as her fault.

**Beats**
- The Bishop himself offers you a contract: 2,000 coupons to escort feeding tankers.
- Sister Agenda, quietly: the tankers go to the Long Stairs.
- Escort them (the Gut spreads) or blow the tubes (the Gut stays put; Agenda takes the blame unless you go back and speak for her).

**Objectives**
1. hear the bishop's offer
2. the tankers

#### Talk: `growth` (with THE STOMACH BISHOP)
- **[start]**
  - _The Bishop, out of his lake, kindly, enormous.* growth is a prayer. this quarter, we are a little short of answered._
  - **THE STOMACH BISHOP:** escort my tankers to the edge of the long stairs. two thousand coupons. and the gratitude of the body.
  - **SISTER AGENDA:** *sung, very low, behind him* the stairs, the stairs, the top terrace...

#### Choice: The tankers are full of Regrowth, headed for the Bottom's top terraces.
- **escort the tankers**: The Gut hits its target. The Bottom's top terrace grows skin over the next act: warm walls, a pulse in the stairs. People move down a terrace. In Act III the Bishop is stronger (+10% HP). In LATE the green on the Long Stairs grows slower.
- **blow the feeding tubes**: The Gut misses its target. The Bottom stays pastel. Sister Agenda is blamed in the minutes; go back and tell the Bishop it was you (a short talk) and she keeps her desk. If you don't, she's moved to the deep wall, and you find her there in m20.

**Reward:** 300 coupons
**Review card:** EXCEEDS EXPECTATIONS. / MEETS EXPECTATIONS. / SEE ME. you fed the tankers to the lake.

---

### BELLY BUTTON `sq_gut_belly_button`
_There's a door at the bottom of the Big Stomach. Don't press it._

**Where:** The Big Stomach (THE GUT), The Belly Button (THE GUT)  
**Who:** THE FOUNDING PARTNER, THE STOMACH BISHOP  
**Giver:** — · **Needs:** m20_the_missing

**The twist:** You press it. Behind it is the founding partner of Gristle & Sons, Augustus Gristle, grown into the district's oldest organ, still holding pens. The Bishop sings to him every night. Augustus wants one more contract, and someone to tell his son the truth.

**Beats**
- Signs everywhere around the crater floor, in every hand: DON'T PRESS IT. PLEASE DON'T. IT'S NOT A BUTTON. (It is a button.)
- Drain the lake (side effect of sq_gut_reflux, or after m20) and walk down to it.
- Press it.
- Secret boss: THE FOUNDING PARTNER.
- He signs your arm and asks you to tell his son it was a failure. Optional: tell the Bishop.

**Objectives**
1. don't press it
2. _(automatic)_ · **boss: THE FOUNDING PARTNER**
3. tell the bishop (optional)

#### Talk: `failure` (with THE STOMACH BISHOP)
- **[start]**
  - _The Bishop, in the Choir Lung, conducting. You tell him what his father said._
  - _His baton stops. His smile, for the first time, gets smaller._
  - **THE STOMACH BISHOP:** a failure.
  - **THE STOMACH BISHOP:** he said that? he... he said that to you?
  - _a long silence. The Choir watches him._
  - _very quietly* then we've been singing to the wrong thing. haven't we._
  - ➤ _"sing something else."_ → else
- **[else]**
  - _He lifts the baton. He doesn't know what to conduct. Sister Agenda, at her desk, starts a single out-of-tune line, and the Choir follows her instead._
  - _does: flag:choir_new_song_

**Reward:** 1000 coupons, lt_boss_founding_partner
**Review card:** EXCEEDS EXPECTATIONS. you pressed it. / MEETS EXPECTATIONS. you pressed it. / SEE ME. you pressed it. we said don't.

---

## PINSTRIPE

### TWO JESTERS `sq_pinstripe_two_jesters`
_Pip and Long Larry want you to prank the Family until it falls apart. Every prank is a weapon gimmick._

**Where:** The Green Room (PINSTRIPE), Mamma Polizza's (PINSTRIPE), The Bocce Pit (PINSTRIPE), The Sauce Works (PINSTRIPE)  
**Who:** PIP GRINSWORTH, LONG LARRY, DON GRINALDI FAZZOLETTO, NONNA FAZZOLETTO  
**Giver:** PIP GRINSWORTH · **Needs:** m07_an_offer

**The twist:** Larry writes every prank, Pip takes the credit, and the last prank is Larry's idea alone: he wants the Don, just once, to laugh at one of his jokes. In the last part it's Nonna who laughs. Up in the rafters, out loud, for the first time anyone can remember. Larry cries for an hour.

**Beats**
- Prank 1: banana-peel the Bocce Pit before a 'settlement' (Peel Shooter). The goons slip; the dispute is settled by slapstick.
- Prank 2: marbles in the Sauce Works (Marble Shotgun): the red river carries goons into the vats.
- Prank 3: the Party Popper in the restaurant's dessert trolley.
- Part 2 (after m08): Larry's joke. Set it up across the Villa with the Bubble Wand, a Rubber Duck and a meatball. The joke is very long. The punchline is a man walking into a bar.

**Objectives**
1. join the punchlines in the green room
2. peel the bocce pit
3. marble the sauce works
4. pop the dessert trolley

**Part: LARRY'S JOKE** _(if done:m08_family_business)_
1. set up larry's joke across the villa

#### Talk: `pranks` (with PIP GRINSWORTH)
- **[start]**
  - **PIP GRINSWORTH:** darling! the merchandise! we're doing pranks. pranks are like gunfights with better timing.
  - **LONG LARRY:** i wrote them.
  - **PIP GRINSWORTH:** LARRY wrote them. i perform them. it's a partnership. like a horse. i'm the front.
  - **LONG LARRY:** i'm the long bit.

#### Talk: `punchline` (with LONG LARRY)
- **[start]**
  - _The joke runs across the whole Villa: a bubble, a duck, a meatball, a chandelier, a goon. Everyone in the house watches. It ends with a man walking into a metal bar._
  - **LONG LARRY:** ...he's hurt. that's the joke.
  - _silence. Then, from the rafters, high and cracked and real: an old woman laughing._
  - _Larry looks up. His droopy nose shakes. He sits down on the marble floor and cries for a long time, and Pip sits next to him and, for once, doesn't say anything._

**Reward:** 700 coupons, lt_district_pinstripe
**Review card:** EXCEEDS EXPECTATIONS. ha. / MEETS EXPECTATIONS. ha ha. / SEE ME. you explained the joke.

---

### WET WORK `sq_pinstripe_wet_work`
_The Family needs some wet work done. Deliver the laundry. Actual laundry. They're very clean._

**Where:** Villa Fazzoletto (PINSTRIPE), Respect Bridge (PINSTRIPE), Mamma Polizza's (PINSTRIPE)  
**Who:** NONNA FAZZOLETTO  
**Giver:** NONNA FAZZOLETTO · **Needs:** m07_an_offer

**The twist:** The laundry is the Don's: shirts, a hundred of them, every one with the same grin stain on the collar. Nonna has been washing her dead son's shirts every week for fifty years. The last basket has a note pinned to it for whoever did the delivery: 'thank you. he always liked them crisp.'

**Beats**
- A laundry basket that must arrive dry, uncreased and on time to five addresses (it's a driving delivery with a crease meter).
- Goons try to 'help' and drop it.
- The note.

**Objectives**
1. pick up the family's laundry
2. deliver it crisp · timer 300s

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. crisp. / MEETS EXPECTATIONS. damp. / SEE ME. you wore one.

---

### CLAIMS DEPARTMENT `sq_pinstripe_claims_department`
_Help survivors file claims on their apocalypse cover. Every claim is denied. Every denial is a gunfight._

**Where:** The Claims Office (PINSTRIPE)  
**Who:** NONNA FAZZOLETTO  
**Giver:** — · **Needs:** m07_an_offer

**The twist:** After eight denials the ninth claimant is a little old man whose claim is for a single cat, lost on the Final Quarter. It's denied (act of shareholders). You can take it to Nonna in person. If you hold the Fazzoletti page, she reads it, looks at it for a long time, and approves it: the only claim the Family has ever paid. It pays 3 coupons. He frames it.

**Beats**
- The Claims Office queue. Each claim: a survivor, a policy, a reason for denial (act of shareholders, act of god, act of god's shareholders, 'you didn't read clause 9', 'clause 9 is blank').
- Each denial sends adjusters with tiny hands and big guns.
- The ninth claim.

**Objectives**
1. help 8 survivors file their claims
2. the ninth claim · if has:page_family

#### Talk: `approve` (with NONNA FAZZOLETTO)
- **[start]**
  - _Nonna, in her nest, reads the little old man's claim. One cat, ginger, called Pickle, lost at 17:30 on the Final Quarter._
  - **NONNA FAZZOLETTO:** act of shareholders.
  - _she looks at the page in your hand, the page with her signature on it._
  - **NONNA FAZZOLETTO:** ...approved.
  - _she stamps it. The stamp says APPROVED; it has never been used; the ink is dry. She licks it.* three coupons. the family pays nothing. the family has paid three coupons. don't tell anyone._
  - _does: flag:first_claim_paid_

**Reward:** 500 coupons
**Review card:** EXCEEDS EXPECTATIONS. a claim was paid. historians are confused. / MEETS EXPECTATIONS. claims denied. adjusters adjusted. / SEE ME. you filed a claim on yourself.

---

### THE MEATBALL RUN `sq_pinstripe_meatball_run`
_A meatball the size of a car got loose on Respect Bridge. Roll it home to Mamma Polizza's._

**Where:** Respect Bridge (PINSTRIPE), Mamma Polizza's (PINSTRIPE)  
**Who:**   
**Giver:** — · **Needs:** m07_an_offer

**The twist:** The meatball is Mamma Polizza's sixty-year-old sourdough-style 'mother meatball', from which every meatball in Pinstripe has been made. If it rolls into the river, Pinstripe's cuisine ends. The goons are weeping openly. A goon tells you the recipe in exchange (a secret implant clue: 'the secret ingredient is a knuckle').

**Beats**
- It's rolling. Downhill. Toward the river.
- Push it with knockback, block it with cars, lasso it (it drags you).
- Get it up the restaurant's stairs.

**Objectives**
1. roll the meatball home

**Reward:** 350 coupons
**Review card:** EXCEEDS EXPECTATIONS. not a crumb lost. / MEETS EXPECTATIONS. a bit of gravel. / SEE ME. it's in the river. pinstripe is in mourning.

---

## THE CHECKOUT

### MALL WALKER `sq_checkout_mall_walker`
_Race the Mall Walkers' club: twelve terrifyingly fast grandmothers in matching tracksuits who have walked the mall's loop every morning since the Stampede._

**Where:** The Infinite Queue (THE CHECKOUT), Food Court Colosseum (THE CHECKOUT), The Big Escalator (THE CHECKOUT)  
**Who:**   
**Giver:** — · **Needs:** m10_doorbusters

**The twist:** They walk to remember: every lap passes the Big Doors, and on every lap the club leader, Dorothea, touches the glass. After you beat them (it takes three races), she invites you to walk a lap with them, slowly, and tells you the names they say at the doors.

**Beats**
- Race 1: the food court loop (no running: walking only; the HUD fines you if your feet leave the floor).
- Race 2: the escalators (walk up the down one).
- Race 3: the whole Infinite Queue (14 laps of the district).
- A slow lap.

**Objectives**
1. beat the mall walkers (food court) · timer 120s
2. beat the mall walkers (escalators) · timer 150s
3. beat the mall walkers (the infinite queue) · timer 600s
4. walk a lap with them

#### Talk: `lap` (with SHOPPER)
- **[start]**
  - **SHOPPER:** *Dorothea, eighty-two, tracksuit, walking slowly beside you. At the Big Doors she puts her hand on the glass.*
  - **SHOPPER:** we do the names. one a lap. we've done every name we know about four hundred times.
  - **SHOPPER:** today's is arthur. he was my brother. he wasn't a member.
  - **SHOPPER:** *she takes her hand off the glass and walks on, fast again.* keep up, love.
  - _does: flag:walked_with_walkers_

**Reward:** 500 coupons, lt_district_checkout
**Review card:** EXCEEDS EXPECTATIONS. you kept up. / MEETS EXPECTATIONS. you nearly kept up. / SEE ME. you ran.

---

### PRICE CHECK ON AISLE EVERYTHING `sq_checkout_price_check`
_Gail needs a price check. Scan 30 hidden barcodes across the Checkout with the Instant Camera._

**Where:** The Infinite Queue (THE CHECKOUT), Returns Desk Zero (THE CHECKOUT), The Vents (THE CHECKOUT)  
**Who:** GAIL ON THE PA  
**Giver:** GAIL ON THE PA · **Needs:** m10_doorbusters

**The twist:** The barcodes are on things no shop would sell: a fountain, a dead escalator, a rat (a live one, very offended), a tree, a Forever Shopper, you. The 30th is on the inside of the PA booth's door, and when you scan it, it comes up as GAIL PRENTICE · ASSISTANT MANAGER · PRICE: 17:31. She's been waiting for someone to scan her for sixty-one years.

**Beats**
- Gail on the PA: 'price check on aisle everything.'
- 30 barcodes hidden around the dome, vents, escalators and the queue (photo goal).
- The last one.

**Objectives**
1. scan 30 hidden barcodes

#### Talk: `scanned` (with GAIL ON THE PA)
- **[start]**
  - _off-mic* oh. oh, you scanned me._
  - **GAIL ON THE PA:** price: 17:31. that's about right. that's what i cost.
  - _on-mic, to the whole mall* attention shoppers. price check complete. all items have been accounted for._
  - _off-mic* thank you, love._

**Reward:** 600 coupons
**Review card:** EXCEEDS EXPECTATIONS. 30/30. / MEETS EXPECTATIONS. / SEE ME. you scanned the rat twice. it remembers.

---

### THE NAMES `sq_checkout_the_names`
_The Mall Rats have spent sixty-one years collecting the names of the people who died outside the Big Doors. They have 3,211. They know there are more._

**Where:** The Vents (THE CHECKOUT), The Big Doors (THE CHECKOUT), Returns Desk Zero (THE CHECKOUT)  
**Who:** WRISTBAND, MINA  
**Giver:** WRISTBAND · **Needs:** m11_no_refunds

**The twist:** Big Value has the list. It always had it: a membership-scan log from 17:30 to 17:34 of every card that was refused at the door. It's in Returns Desk Zero, the only returns desk that's never taken a return, filed as 'declined transactions'. With it, the Mall Rats can finish the wall. If the Mall Rats run the Checkout, they paint the names on the welded doors; if Big Value does, Gail reads them on the PA, one a day, for as long as it takes.

**Beats**
- The vent classroom's wall of names, in chalk.
- Wristband: there are gaps. People who weren't known.
- Break into Returns Desk Zero (stealth: Mall Security, then a vault of unreturned items).
- The log.
- If Mina is free, she reads the log with Milo, in the vents, holding his hand.

**Objectives**
1. talk to wristband
2. get into returns desk zero
3. find the declined transactions
4. bring the log to the vents

#### Talk: `gaps` (with WRISTBAND)
- **[start]**
  - _A classroom in the vents. One wall is names, in chalk, floor to ceiling, in a hundred handwritings._
  - **WRISTBAND:** three thousand two hundred and eleven. we've found them from letters, from families, from people who were there.
  - **WRISTBAND:** there are more. people nobody came looking for. people who were alone.
  - **WRISTBAND:** big value knew who it turned away. it had a list. it always had a list. that's what a membership is.

#### Talk: `complete` (with WRISTBAND)
- **[start]**
  - _Wristband turns the log's pages very slowly._
  - **WRISTBAND:** eight thousand and forty.
  - _he doesn't cry. He gets a piece of chalk and starts at the next empty brick._
  - **MINA:** *if she's free, sitting beside him with the second piece of chalk* i'll do the other side, milo.
  - _does: flag:names_complete_

**Reward:** —
_Builder notes: no performance-review card and no coupons: the Mall Rats offer, you can refuse; the game doesn't make a reward of this._

---

### RETURNS DESK ZERO `sq_checkout_returns_desk_zero`
_Returns Desk Zero has never accepted a return. A sign says so. A clerk-bot has been waiting behind it since the Stampede for its first customer._

**Where:** Returns Desk Zero (THE CHECKOUT)  
**Who:** THE CART MOTHER  
**Giver:** — · **Needs:** m11_no_refunds

**The twist:** The first thing it will accept is Brenda's receipt. Brenda (the Cart Mother, beaten) has to bring it herself. She does, if you help her through the mall on a trolley. The clerk-bot scans it and says the only thing it has ever been programmed to say: 'refund approved.' It hands her a single bottle of water. She sits down on the floor and drinks it.

**Beats**
- The desk, the bot, the sign: RETURNS DESK ZERO · NO RETURNS SINCE 17:31.
- Find Brenda (she's in the Cart Corral since her defeat, if not dismantled).
- Wheel her to the desk on a trolley through a sale stampede.
- The refund.

**Objectives**
1. visit returns desk zero
2. bring brenda

**Reward:** 200 coupons
**Review card:** EXCEEDS EXPECTATIONS. refund approved. / MEETS EXPECTATIONS. / SEE ME. you tried to return yourself.

---

## NUMBER WORKS

### CARRY THE ONE `sq_numberworks_carry_the_one`
_Escort a giant 1 across Number Works. Everybody wants it: you can't carry anything without one._

**Where:** The Number Yard (NUMBER WORKS), Prime Lane (NUMBER WORKS), The Big Calculator (NUMBER WORKS)  
**Who:** NELL THIRTEEN  
**Giver:** NELL THIRTEEN · **Needs:** m14_price_of_everything

**The twist:** Halfway, the 1 gets a 3 attached to it by Remainder's 'rounding' crews and becomes a 13, and the union refuses to touch an unlucky number. Nell holds a vote, mid-ambush, on whether a 13 is still a 1 with friends. It passes 7-6. You carry the 13.

**Beats**
- A building-sized 1 on a flatbed, from the Smokestacks to the Big Calculator.
- Ambushes by rounding crews.
- The vote.

**Objectives**
1. carry the one to the big calculator

#### Talk: `vote` (with NELL THIRTEEN)
- **[start]**
  - _mid-firefight, through the megaphone* motion: a thirteen is just a one with friends. all in favour?_
  - _seven hands, some of them holding guns._
  - **NELL THIRTEEN:** against?
  - _six hands._
  - **NELL THIRTEEN:** motion carried. KEEP CARRYING.

**Reward:** 450 coupons, lt_district_numberworks
**Review card:** EXCEEDS EXPECTATIONS. carried. / MEETS EXPECTATIONS. carried, mostly. / SEE ME. you dropped the one. now it's a zero.

---

### ROUNDING ERROR `sq_numberworks_rounding_error`
_Someone's been stealing halves. Every worker's wage has been rounded down by 0.5 coupons for sixty-one years. Find out who._

**Where:** The Forecast Archive (NUMBER WORKS), The Remainder Pit (NUMBER WORKS), The Price Press (NUMBER WORKS)  
**Who:** NELL THIRTEEN, MR. SEVENS, FOREMAN REMAINDER  
**Giver:** NELL THIRTEEN · **Needs:** m14_price_of_everything

**The twist:** It's the Price Press itself: Remainder's oldest program, still running the rule it was given on the Final Quarter: 'round all outstanding values down by 0.5 until the books balance'. The books will never balance, because the 0.5 it's trying to make up is the 0.5% Q4 revision that came in that morning and was ignored. In the Forecast Archive you find the original rule card, with a note from the 09:00 forecasting team: 'we hit it. tell the board.' (A clue toward the Act III memo, and a Cale memory flash if Drift is low: Agnes saying 'remainder's always half a percent out.')

**Beats**
- Payslips from union members: every one 0.5 short.
- A stakeout in the Remainder Pit (where leftover numbers go): a conveyor of halves going into the Price Press.
- The Forecast Archive: spools of paper, a rule card.
- Choice: turn the rule off (wages go up 0.5; Remainder notices) or leave it and take the card to Mr. Sevens (he pays you to keep quiet).

**Objectives**
1. check the payslips
2. stake out the remainder pit
3. follow the halves to the archive
4. the rule

#### Talk: `half` (with NELL THIRTEEN)
- **[start]**
  - _Nell slaps a stack of payslips on the table.* every one. half a coupon short. every week. sixty-one years._
  - **NELL THIRTEEN:** management calls it rounding. we call it theft. find out where the halves go.

#### Choice: The rule card: 'ROUND ALL OUTSTANDING VALUES DOWN BY 0.5 UNTIL THE BOOKS BALANCE.' And a note: 'we hit it. tell the board.'
- **turn the rule off**: Wages go up by 0.5 coupons. The union throws you a party with exactly 13 balloons. Mr. Sevens touches wood very hard.
- **sell the card to mr. sevens**: He pays 1,500 coupons and burns the card on his one piece of real wood. The halves keep going. (He keeps a copy of the note, for luck; it turns up in his call-log envelope if you DEAL in m15.)

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. it balances. a bit. / MEETS EXPECTATIONS. rounded. / SEE ME. you rounded yourself down.

---

### DIVIDE BY ZERO `sq_numberworks_divide_by_zero`
_There's a button on top of the Big Calculator labelled ÷0. Every sign in Number Works says don't._

**Where:** The Big Calculator (NUMBER WORKS), The Smokestacks (NUMBER WORKS)  
**Who:** FOREMAN REMAINDER  
**Giver:** FOREMAN REMAINDER · **Needs:** m15_rounding_down

**The twist:** You do. For one in-game hour Number Works stops making sense: gravity's a suggestion, prices are NaN (everything costs nothing and also infinity, so shops give you whatever you can carry), smokestacks puff the wrong way, and the giant digits get up and walk around. The Foreman (rehired) shows up and, for the first time since he was nine, laughs. 'i always wanted to press that.' The secret: at the top of the tallest Smokestack, a Lucky Thirteenth Rib (secret implant) is just sitting there, because in NaN-time nothing is unlucky.

**Beats**
- Climb the Big Calculator (conveyors, digit-riding).
- Press ÷0.
- An hour of chaos: loot the shops, ride the digits.
- The Foreman on the roof.

**Objectives**
1. climb the big calculator
2. don't
3. survive an hour of NaN

**Reward:** lt_district_numberworks
**Review card:** EXCEEDS EXPECTATIONS. NaN. / MEETS EXPECTATIONS. NaN. / SEE ME. NaN.

---

## CHROME GRISTLE

### SPARE PARTS `sq_chromegristle_spare_parts`
_A kidney got up and left Bev's clinic before its install. Retrieve it._

**Where:** Jar Alley (CHROME GRISTLE), Arcade Row (CHROME GRISTLE), The Noodle Shrine (CHROME GRISTLE)  
**Who:** BEV  
**Giver:** BEV · **Needs:** m17_minutes

**The twist:** The kidney has been regrown so many times by different Meat Mechanics that it's become a little person: it has a job (it's working the noodle stall at the Noodle Shrine), friends, and a tiny paper hat. Its original owner, a man on the Commute, doesn't want it back: 'it's got a life now. i've got two.' You can leave it be, and it waves at you every time you pass.

**Beats**
- A chase through Jar Alley (jars blink at you).
- Arcade Row: it's been playing the old JANKFIRE cabinet and has the high score.
- The Noodle Shrine: it's working the stall.
- Talk to its original owner by pager.

**Objectives**
1. follow the kidney's trail
2. find the kidney

#### Choice: The kidney, in a paper hat, serving noodles, looks at you.
- **leave it be**: Bev shrugs: 'organs have rights now, do they. fine.' The kidney gives you free noodles forever (a 25% heal snack, restocks daily).
- **take it back to bev**: Bev installs it in a paying customer. The noodle stall closes. Arcade Row's high score stays forever.

**Reward:** 200 coupons
**Review card:** EXCEEDS EXPECTATIONS. / MEETS EXPECTATIONS. / SEE ME. you ate the noodles. you ate a lot of them.

---

### SECOND OPINION `sq_chromegristle_second_opinion`
_Get two Meat Mechanics to diagnose the same rash. They disagree violently._

**Where:** Organ Pawn (CHROME GRISTLE), Doctor Upsell's Clinic (CHROME GRISTLE), Bev's Clinic (THE GUT)  
**Who:** BEV, DOCTOR UPSELL  
**Giver:** BEV · **Needs:** m17_minutes

**The twist:** The rash is on you: a pattern spreading under your plastic where your implants join, shaped exactly like the Schedule's grid. Both diagnoses are right. Bev says it's rejection; Upsell says it's 'the body accepting the schedule'. It's the first visible sign of Drift, and it fades if you uninstall parts or lower your Drift (the game tells you, in Bev's words, without a number).

**Beats**
- A rash. Bev's diagnosis.
- Upsell's diagnosis (book a consultation, or if he's beaten, his rehired self).
- They meet. They fight (a gunfight between two clinics).
- The truth.

**Objectives**
1. get bev's opinion
2. get a second opinion
3. survive the disagreement

#### Talk: `rash` (with BEV)
- **[start]**
  - _Bev looks at the grid-shaped rash spreading from your implants with a magnifier._
  - **BEV:** that's rejection, chassis. your body doesn't know where it ends any more. it's drawing itself a map.
  - **BEV:** the more parts that aren't you, the more of this.
  - **BEV:** go and ask upsell. he'll tell you it's a feature. he's half right, which is the worst amount of right.

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. both opinions obtained. / MEETS EXPECTATIONS. / SEE ME. you scratched it.

---

### ARCADE LEGEND `sq_chromegristle_arcade_legend`
_Beat the high score on an Arcade Row cabinet that runs the old JANKFIRE._

**Where:** Arcade Row (CHROME GRISTLE)  
**Who:**   
**Giver:** — · **Needs:** m17_minutes

**The twist:** The cabinet is a tiny piece of the Machine's sims, salvaged. The high score belongs to CALE R. 4417, from sixty-one years ago, set on a lunch break. You're trying to beat yourself. When you do, the cabinet asks for initials, and if you type RC it plays a ten-second Cale memory: a lunch break, a cheap sandwich, Agnes leaning on the cabinet saying 'you're wasting your break, rory.' 'it's the only bit of the day that's mine.'

**Beats**
- The cabinet. The score: 4417 points, CALE R.
- Play (a short arcade-rules match against bots on a tiny map).
- Beat it. Enter initials.

**Objectives**
1. beat the high score

**Reward:** 300 coupons
**Review card:** EXCEEDS EXPECTATIONS. NEW HIGH SCORE. / MEETS EXPECTATIONS. / SEE ME. insert coin.

---

### BUY BACK `sq_chromegristle_organ_pawn`
_Organ Pawn has a kidney in its window with a tag: D. PELL. Lumps saw it._

**Where:** Organ Pawn (CHROME GRISTLE)  
**Who:** LUMPS  
**Giver:** — · **Needs:** m20_the_missing

**The twist:** Dot sold it, years ago, to pay for Lumps' tenth birthday (a bike made of a shopping trolley). The pawn tag has accrued sixty-one per cent a year in fees. It costs more than the Bottom earns in a year. Lumps can't afford it and won't let you pay. The only way is a Pawn Heist (a stealth job) or the Gold Member legendary's loot magnet, or simply... letting it go. Dot, told, says: 'it was a lovely bike.'

**Beats**
- Lumps, frozen at the shop window.
- The price.
- The choice: heist it, buy it with your own coupons (Lumps is cross and grateful), or leave it.

**Objectives**
1. the kidney in the window

#### Talk: `window` (with LUMPS)
- **[start]**
  - _Lumps, standing in front of Organ Pawn's window, very still. A kidney in a jar. A tag: D. PELL. PAWNED. FEES ACCRUING._
  - **LUMPS:** she said she sold it. for my birthday. i got a bike. it was a trolley with pedals.
  - **LUMPS:** i thought she meant she sold her earrings.
  - _he puts a hand on the glass.* it's very expensive. it got more expensive every year i didn't know._

#### Choice: Dot's kidney, in Organ Pawn's window.
- **steal it back**: A stealth heist (alarm jars, blink sensors, a guard with too many arms). Dot gets her kidney back from Bev that week. 'well. i'll have to get another birthday out of you, ambrose.'
- **buy it (8,000 coupons)**: Lumps refuses, then cries, then lets you. He carries the jar home on his lap like the soup pot.
- **leave it**: Lumps nods. When he tells Dot, she laughs: 'it was a lovely bike.'

**Reward:** —

---

## EVERGREEN ACRES

### LAWN ORDER `sq_evergreen_lawn_order`
_Mow 50 lawns with the Lawn Mower, perfectly. The HOA measures each one to the millimetre._

**Where:** The Cul-de-sac (EVERGREEN ACRES), The Prize Pumpkin (EVERGREEN ACRES)  
**Who:** LINDA FAIRWAY  
**Giver:** LINDA FAIRWAY · **Needs:** m21_property_values

**The twist:** Lawn 50 belongs to the Prize Pumpkin, which has won every year because it's the only entry. Linda asks you not to mow too close to it. It's grown over the shelter's old air vent, and the pumpkin is the only thing on the street that came up from the shelter with them. Linda planted it at eleven. It's sixty years old, enormous, and very slightly alive.

**Beats**
- 50 lawns, each with a target height in mm (the Lawn Mower legendary or any autoshot works; other weapons scorch).
- Mannequin families wave at you while you mow.
- The Pumpkin.

**Objectives**
1. mow 50 lawns to regulation
2. the prize pumpkin's lawn

#### Talk: `pumpkin` (with LINDA FAIRWAY)
- **[start]**
  - _Linda, by a pumpkin the size of a car, with a rosette on it that's sixty years of rosettes stapled together._
  - **LINDA FAIRWAY:** not too close, please. that's not in the bylaws. that's... me asking.
  - **LINDA FAIRWAY:** i planted it the day we came up. i was eleven. it was the only seed in the shelter. it's never lost.
  - _she pats it. It's warm._

**Reward:** 700 coupons, keep_off_the_grass
**Review card:** EXCEEDS EXPECTATIONS. 0 mm deviation. / MEETS EXPECTATIONS. 2 mm. you've been fined. / SEE ME. you mowed a dog.

---

### BLOCK PARTY `sq_evergreen_block_party`
_Evergreen is having a block party. Attendance is compulsory. Survive it._

**Where:** The Cul-de-sac (EVERGREEN ACRES), The HOA Clubhouse (EVERGREEN ACRES)  
**Who:** LINDA FAIRWAY  
**Giver:** LINDA FAIRWAY · **Needs:** m21_property_values

**The twist:** It's a survival wave mode with BBQ dads, a bouncy castle that's a trap, a three-legged race (you and a mannequin tied together) and a talent show. The last act of the talent show is the pilot families singing in perfect harmony, a song from before the war, and if you left them plugged in, Linda's dad sings the lead. She mouths along. It's beautiful and it's horrible and it's both on purpose.

**Beats**
- Waves of compulsory fun.
- The talent show.

**Objectives**
1. survive the block party

**Reward:** 600 coupons
**Review card:** EXCEEDS EXPECTATIONS. you won the three-legged race. with a mannequin. / MEETS EXPECTATIONS. you attended. / SEE ME. you left early. it's been noted.

---

### KEEPING UP `sq_evergreen_keeping_up`
_Evergreen's safehouse comes with a rule: you need the same car as the neighbours, or they call Late Fees on you._

**Where:** The Cul-de-sac (EVERGREEN ACRES)  
**Who:** LINDA FAIRWAY  
**Giver:** LINDA FAIRWAY · **Needs:** m21_property_values

**The twist:** The neighbours' car is a pastel-blue estate that hasn't been made in sixty-one years. The only one left outside Evergreen is in the Unpaid's camp, as their 'company car'. Stealing it is a heist; trading for it costs you an internship. When you park it on the drive, the mannequin family next door waves, and for one frame its wave is out of sync.

**Beats**
- The safehouse's welcome pack: a bylaw.
- Find the car.
- Park it.

**Objectives**
1. get a car like the neighbours'
2. park it on the drive

**Reward:** 300 coupons
**Review card:** EXCEEDS EXPECTATIONS. you blend in. / MEETS EXPECTATIONS. / SEE ME. it's the wrong blue.

---

### RETURN ADDRESS `sq_evergreen_return_address`
_Evergreen's mailman never stops walking. His satchel is full of letters posted on the Final Quarter that were never delivered._

**Where:** The Cul-de-sac (EVERGREEN ACRES), The Long Stairs (THE BOTTOM), Gary's Site Office (THE COMMUTE), Remainder Downtown Office (THE LATES)  
**Who:** THE MAILMAN, GARY, PAULINE FROM ACCOUNTS  
**Giver:** THE MAILMAN · **Needs:** m21_property_values

**The twist:** One of them is addressed to MRS. JUNE SALLOW, 14 HILLSIDE ROAD. Hillside Road collapsed into the Bottom; number 14 is a ruin by the Long Stairs, and in it, on a dead hallway table, an answering machine still holds one message, 17:30:00 on the Final Quarter. It's the last of Overtime's six memory fragments: 'i'm here. i'm on my way, june.' The letter in your hand is a card from Edwin to June, posted at lunch: 'happy forty. i'll be on time. E.'

**Beats**
- Follow the mailman (he never stops; you read the envelopes as he walks).
- Deliver six letters to whoever's left: one to Gary (his own handwriting, a memo to himself), one to Pauline in the Lates (from her mother: she reads it 22,000 days late), others.
- The last: Mrs. June Sallow.
- 14 Hillside Road. The answering machine.

**Objectives**
1. keep up with the mailman
2. deliver the final quarter's letters
3. the letter for mrs. june sallow

#### Talk: `machine` (with JUNE)
- **[start]**
  - _14 Hillside Road: a ruin, half a hallway, a table, a beige answering machine with a red light that has been blinking for sixty-one years on a battery somebody kept changing. (Dale? You'll never know.)_
  - _You press play._
  - **VOICE:** *a man's voice, a lobby echo behind it* june, it's ed. i'm, i'm here. it's 17:30. i'm on my way.
  - _June's own outgoing message, warm, wry:* "ed. it's half five. the stew won't wait and neither will i."_
  - _The message ends. You have the end of Edwin Sallow's shift._

**Reward:** 500 coupons
**Review card:** EXCEEDS EXPECTATIONS. all delivered. / MEETS EXPECTATIONS. / SEE ME. you read them all first. it's a crime.

---

## THE LATES

### GROUNDHOG LUNCH `sq_lates_groundhog_lunch`
_Gus has been trying to finish the same lasagne for 22,000 days. Something interrupts him at the last bite every time._

**Where:** The Canteen (THE LATES)  
**Who:** GUS, PAULINE FROM ACCOUNTS  
**Giver:** GUS · **Needs:** m22_the_waiting_room

**The twist:** Every interruption is a different Looper's small Tuesday disaster (a fire alarm, a dropped tray, a fight over a stapler), and fixing one makes the next one happen. When you finally clear all eleven, Gus holds up the last bite and doesn't eat it. 'if i finish it, it'll be wednesday. and my wife will be dead.' You can tell him to eat it, or not. Either is kind.

**Beats**
- Gus and the lasagne.
- Eleven interruptions, each a micro-puzzle across one loop (a chain: fix the alarm at 12:31 and the tray falls at 12:33).
- The last bite.

**Objectives**
1. have lunch with gus
2. stop 11 interruptions in one loop

#### Talk: `lasagne` (with GUS)
- **[start]**
  - **GUS:** it's lasagne!
  - **GUS:** nearly got the last bite yesterday. well. today. it's always today.
  - **PAULINE FROM ACCOUNTS:** *not looking up* he's said that twenty-two thousand times.
  - **GUS:** and i'll say it again! it's lasagne!

#### Talk: `bite` (with GUS)
- **[start]**
  - _The canteen, 12:59. Nothing has interrupted. Gus holds the last bite on his fork._
  - **GUS:** ...if i finish it, it'll be wednesday. won't it.
  - **GUS:** my wife makes it better. made. makes. on wednesday i'll find out which.
  - ➤ _"eat it, gus."_ → eat
  - ➤ _"you don't have to. not today."_ → wait
- **[eat]**
  - _He eats it. He chews for a long time._
  - **GUS:** ...it's quite bad, actually.
  - _he laughs, and it turns into something else, and Pauline puts her hand on his._
  - _does: flag:gus_finished_
- **[wait]**
  - _He puts the fork down. Relieved._
  - **GUS:** tomorrow. well. today. thanks.
  - _does: flag:gus_waited_

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. / MEETS EXPECTATIONS. it's lasagne. / SEE ME. you ate his lasagne.

---

### COPY OF A COPY `sq_lates_copy_of_a_copy`
_You're locked in an office in the Lates. The only way out is to photocopy yourself._

**Where:** Remainder Downtown Office (THE LATES), The Waiting Room (THE LATES)  
**Who:** PAULINE FROM ACCOUNTS  
**Giver:** PAULINE FROM ACCOUNTS · **Needs:** m22_the_waiting_room

**The twist:** Each copy is a little worse (blurrier, a wrong colour, a knee that bends two ways), and each copy needs to stand on a pressure plate. By copy six you're arguing with yourself. The last copy, very faded, asks the original: 'are we the same person?' The puzzle's answer is no; the door opens when you say so.

**Beats**
- An office, a copier, six pressure plates.
- Copies follow your inputs with a delay (a co-op puzzle with yourself).
- The faded copy's question.

**Objectives**
1. photocopy yourself out

#### Talk: `copy` (with CHANGE)
- **[start]**
  - **VOICE:** *your sixth copy, faint grey, a wrong knee both ways* are we the same person?
  - ➤ _"yes."_ → yes
  - ➤ _"no."_ → no
- **[yes]**
  - **VOICE:** *the door stays shut* ...then why am i so faint?
  - → start
- **[no]**
  - **VOICE:** *the door clicks* good. i didn't think so. good luck, original.
  - _does: flag:copy_puzzle_done_

**Reward:** 350 coupons
**Review card:** EXCEEDS EXPECTATIONS. one of you got out. / MEETS EXPECTATIONS. / SEE ME. you're still in there. all six.

---

### HOLD MUSIC `sq_lates_hold_music`
_The Lates' hold music plays everywhere, all day. Nobody knows where it comes from. Find the source._

**Where:** The Waiting Room (THE LATES), The Backrooms Stairwell (THE LATES), Tuesday Tower (THE LATES)  
**Who:** PAULINE FROM ACCOUNTS  
**Giver:** PAULINE FROM ACCOUNTS · **Needs:** m22_the_waiting_room

**The twist:** It's a woman in the Backrooms Stairwell, deep down, at a switchboard, humming into the line to keep 4,000 callers company: the Lates' Remainder call centre has had 4,000 people on hold since 17:29. She's been humming for sixty-one years. One of the held calls is from the Spire's lobby security desk, 17:29: in the background, a running man's footsteps and a polite voice saying 'that's against policy'. It's one of Overtime's memory fragments.

**Beats**
- Follow the music (it gets louder near certain walls; a Backrooms descent).
- The switchboard.
- The held calls; one from the lobby.

**Objectives**
1. find where the hold music comes from
2. listen to the held calls

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. your call is important. / MEETS EXPECTATIONS. please hold. / SEE ME. you hung up on 4,000 people.

---

### QUALITY CONTROL `sq_lates_quality_control`
_Go back through the door at 03:00. At the end of a row there was an empty dock with your name on it. It isn't empty any more._

**Where:** The Door in the Sky (THE LATES), The Restoration Warehouse (THE LATES)  
**Who:** EMPLOYEE 4417  
**Giver:** — · **Needs:** m23_workforce_restoration

**The twist:** Hask had a copy of you built with the Schedule forced in, to see what you'd be on the payroll. It's happy. It remembers Mina and doesn't think she's important. Beating it gets you its chip: the strongest head implant in the game, which loads a little of the Schedule into you. It costs two permanent Drift. The game asks you twice.

**Beats**
- Any night after m23, at 03:00, the door is there for anyone who knows.
- The dock: CALE R. 4417 · EMPLOYEE OF THE QUARTER.
- Secret boss: EMPLOYEE 4417.
- It asks what time it is.

**Objectives**
1. go back through the door at 03:00 · if clock.lates=03:00-04:00
2. _(automatic)_ · **boss: EMPLOYEE 4417**

**Reward:** 1000 coupons, lt_boss_prototype
**Review card:** EXCEEDS EXPECTATIONS. you were better than you. / MEETS EXPECTATIONS. / SEE ME. you lost to you.

---

## THE MARGINS

### LIFEGUARD `sq_margins_lifeguard`
_People fall into the void. Some of them wave. Pull them out with the lasso before they sink out of reach._

**Where:** The Edge (THE MARGINS), The Gnome Field (THE MARGINS)  
**Who:** THE JANITOR, OLD PAT  
**Giver:** THE JANITOR · **Needs:** m26_exit_interview

**The twist:** The ones you pull out are still employed. They've just lost the dental. And they're recent: Vacancy's survey teams have been 'clearing' squatters. The last one you pull out is the Janitor's wife, who went in sixty-one years ago with their house, and she's exactly as she was, mid-sentence. 'wendell, have you mopped' — and the void takes her back before she can finish. The Janitor says thank you. He means it. He keeps mopping.

**Beats**
- The lifeguard tower on the Edge. The Janitor: 'some of them wave. i wave back now.'
- Lasso rescues (timed; heavy ones drag you in: fall in on purpose and respawn at a gnome, keeping momentum).
- Eleven people out. Each gets a gnome with their name (Old Pat paints them).
- The twelfth wave.

**Objectives**
1. climb the lifeguard tower
2. pull 11 people out of the void

#### Talk: `wave` (with THE JANITOR)
- **[start]**
  - _squeak. squeak._
  - **THE JANITOR:** careful. floor's wet. it's the void. i mop it anyway. job's a job.
  - **THE JANITOR:** some of them wave. i wave back now. i'm old. what's it going to do.
  - **THE JANITOR:** you've got a rope. go on. they're still employed. they've just lost the dental.

#### Talk: `mopped` (with THE JANITOR)
- **[start]**
  - _The Janitor on the edge, the mop in both hands, looking at where she went back under._
  - **THE JANITOR:** she was going to say 'have you mopped the hall'. she always said it. i always hadn't.
  - _a long time_
  - **THE JANITOR:** ...thank you. i got to hear the first half.
  - _squeak. squeak._
  - _does: flag:janitor_heard_her_

**Reward:** 600 coupons
**Review card:** EXCEEDS EXPECTATIONS. everyone out. / MEETS EXPECTATIONS. / SEE ME. you fell in. eleven times.

---

### STAKING CLAIMS `sq_margins_staking_claims`
_Plant gnomes to hold the ground. Vacancy can't sell what's occupied._

**Where:** The Gnome Field (THE MARGINS), The Last Bus Stop (THE MARGINS), The Show Home (THE MARGINS)  
**Who:** OLD PAT, PENNY PLOT  
**Giver:** OLD PAT · **Needs:** m26_exit_interview

**The twist:** Vacancy's lawyers have found the loophole: a gnome counts as occupation only if it's 'facing the property'. The Margin Walkers have been planting them facing the void for years. You have to turn four hundred and twelve gnomes round, under fire from survey teams, before the lawyers' deadline. Old Pat, for the first time, looks at the names under them as she turns each one.

**Beats**
- Gnome planting (each gnome is a respawn point on the Margins).
- The loophole letter.
- Turn every gnome round before sundown (survey drones, hazmat agents).

**Objectives**
1. plant 20 gnomes on unclaimed ground
2. turn the gnomes to face the property before sundown

**Reward:** 700 coupons
**Review card:** EXCEEDS EXPECTATIONS. occupied. / MEETS EXPECTATIONS. / SEE ME. you planted a gnome in the void. it's gone.

---

### THE LAST BUS `sq_margins_the_last_bus`
_The Last Bus Stop's timetable says the 17:42 is due. It's been due for sixty-one years._

**Where:** The Last Bus Stop (THE MARGINS), The Lost & Found (THE BOTTOM)  
**Who:** OLD PAT  
**Giver:** — · **Needs:** m26_exit_interview

**The twist:** At 17:42 on a foggy night, it comes: a city bus out of the void, the 17:42 from the Final Quarter, with the driver and nine passengers who don't know anything has happened. Their bus went into the void bomb's blast and came out the other side sixty-one years later. You have to get them to the Bottom before the void takes the bus back at 18:00, while they ask questions you don't want to answer. (The Lost & Found's 'one of them is a whole bus' lost-property tag was always this bus.)

**Beats**
- A timetable. Wait at the stop at 17:42 in fog.
- The bus arrives. Drive it (the driver lets you: 'i've had a long shift').
- Passengers' questions on the way (dialogue barks: where are the shops, why is it dark, is that a church breathing).
- The Lost & Found by 18:00.

**Objectives**
1. wait for the 17:42 · if clock.margins=17:40-17:50
2. get the bus to the lost & found before 18:00 · timer 600s

**Reward:** 800 coupons
**Review card:** EXCEEDS EXPECTATIONS. on time. / MEETS EXPECTATIONS. / SEE ME. the bus is late. again.

---

## CORP HILL

### THE PUNCTUALITY MUSEUM `sq_corphill_punctuality_museum`
_☺ CORP keeps printing new Overtimes. The newest one stands in the Punctuality Museum, among exhibits about being on time._

**Where:** The Punctuality Museum (CORP HILL)  
**Who:** MR. OVERTIME  
**Giver:** — · **Needs:** m13_rush_hour

**The twist:** One exhibit is EMPLOYEE #1: A LIFE ON TIME, a glass case of Edwin Sallow's things, including a framed photo: Employee of the Month, the very first, with a cat on his lap and a woman out of focus at the edge of the frame, laughing. It's one of his six memory fragments. Every rehired Overtime stops in front of that case for exactly one second before he fights you. He doesn't know why.

**Beats**
- The museum: exhibits (THE FIRST TIME CARD, LATENESS THROUGH THE AGES, THE PENDULUM OF PUNCTUALITY), a gift shop that sells clocks.
- The EMPLOYEE #1 case.
- Boss: OVERTIME (REHIRED). Refightable every midnight: POSITION REFILLED.

**Objectives**
1. visit the punctuality museum
2. look at the employee #1 exhibit
3. _(automatic)_ · **boss: MR. OVERTIME**

**Reward:** 900 coupons, lt_boss_overtime_rehire
**Review card:** EXCEEDS EXPECTATIONS. exhibit closed. / MEETS EXPECTATIONS. / SEE ME. you touched the exhibits.

---

### REPLY ALL `sq_corphill_reply_all`
_An email that will doom ☺ CORP is about to be sent. Chase it down the Spire's pneumatic tubes before it reaches everyone._

**Where:** Spire, 60th Floor (CORP HILL), The Cathedral of Shareholder Value (CORP HILL)  
**Who:** PRITCHARD  
**Giver:** PRITCHARD · **Needs:** m24_the_split

**The twist:** Pritchard sent it. By accident. It's his resignation letter, typed at 03:00 one night and saved as a draft for six years, and the Spire's mail system is pneumatic: it's a physical capsule racing through 400 km of tubes to every desk. You catch it at the last junction. He asks you to read it. It's one line: 'i would like a minute to myself.' He asks you to put it back in the tube. Or not.

**Beats**
- Pritchard on the pager, hyperventilating.
- A chase through the Spire's tube network (riding capsules, grappling junctions).
- The capsule.
- Choice: send it, or give it back to him.

**Objectives**
1. catch the email · timer 240s

#### Talk: `oh_no` (with PRITCHARD)
- **[start]**
  - **PAGER:** *BEEP BEEP BEEP BEEP BEEP*
  - **PRITCHARD:** i've sent something. i've sent something to everyone. it's in the tubes. it's going to every desk in the spire. please. please. it's a capsule. it's blue.

#### Choice: The blue capsule. One line: 'i would like a minute to myself.'
- **put it back in the tube**: It reaches 11,000 desks. Nobody replies. At 09:00 Hask's calendar has a new entry: 'PRITCHARD: 1 MINUTE.' She approved it. He spends it on a bench by the Smiling Fountain. (He's still her assistant. It's a start.)
- **give it back to him**: He keeps it in his blazer pocket. 'not yet. but thank you for reading it.'

**Reward:** 500 coupons
**Review card:** EXCEEDS EXPECTATIONS. delivered. or not. / MEETS EXPECTATIONS. / SEE ME. you replied all.

---

### CASUAL FRIDAY `sq_corphill_casual_friday`
_Ruin ☺ CORP's dress code: steal every tie in an office of 300 synced mannequin workers without being seen._

**Where:** Spire, 60th Floor (CORP HILL), The Smiling Fountain (CORP HILL)  
**Who:** PIP GRINSWORTH  
**Giver:** PIP GRINSWORTH · **Needs:** m24_the_split

**The twist:** Without ties, the mannequin workers lose sync. They start walking at their own pace. One sits down. One looks out of the window. One, very slowly, loosens its collar and laughs. Pip, who set it up as a prank, watches through binoculars and goes quiet.

**Beats**
- Pip's challenge (Pip needs ties for a costume. 300 ties.)
- Stealth: the office moves on the beat of the clocks (On Time traversal).
- The workers out of sync.

**Objectives**
1. steal 300 ties

**Reward:** 450 coupons
**Review card:** EXCEEDS EXPECTATIONS. smart casual. / MEETS EXPECTATIONS. / SEE ME. you're wearing all 300.

---

### TEAM BUILDING `sq_corphill_team_building`
_Survive a ☺ CORP team-building exercise: a trust fall off a skyscraper._

**Where:** The Cathedral of Shareholder Value (CORP HILL), Dividend Road (CORP HILL)  
**Who:** THE TWINS  
**Giver:** — · **Needs:** m24_the_split

**The twist:** It's run by the Twins (before the raid), who explain that this is how they were merged: a trust fall in the Merger's integration week, into a Gristle & Sons fusion vat. The exercise's 'catchers' are a Facilities team with a bleach cannon. You can fall (and grapple out at the last second), or push the Twins off instead and see who catches whom. Nobody catches anybody. They land in the Smiling Fountain, still agreeing.

**Beats**
- A rooftop. A whiteboard: TRUST.
- The fall (a skydiving grapple challenge down the Spire's side).
- Or the push.

**Objectives**
1. trust

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. you trusted nobody. correctly. / MEETS EXPECTATIONS. / SEE ME. you caught the twins. why.

---

### PARKING PERMIT `sq_corphill_parking_permit`
_Get a parking permit on Corp Hill. It's the hardest quest in the game._

**Where:** The ☺ Spire Lobby (CORP HILL), Spire, 60th Floor (CORP HILL), The Cathedral of Shareholder Value (CORP HILL), The Punctuality Museum (CORP HILL), The Smiling Fountain (CORP HILL)  
**Who:** PRITCHARD, CHAD TEMPO  
**Giver:** — · **Needs:** m24_the_split

**The twist:** It's a 19-step bureaucratic odyssey across every office on Corp Hill: forms that need forms, a queue that's a sim of a queue, a stamp that's in the museum, a signature from someone who died in the war (you have to go to the Lates for it), and finally an appointment with Pritchard, who looks at the form and says 'oh, you didn't need one of these. there's no parking on corp hill. there aren't any cars allowed.' The permit is a legendary (it's laminated).

**Beats**
- Form 1. Form 1a. Form 1a (revised).
- A queue (60 s of standing still; any movement sends you to the back).
- The stamp in the Punctuality Museum.
- A dead man's signature (the Lates).
- Pritchard.

**Objectives**
1. complete the permit application (19 steps)
2. attend your permit appointment

#### Talk: `permit` (with PRITCHARD)
- **[start]**
  - _He reads all nineteen forms carefully. It takes four minutes. He's very thorough._
  - **PRITCHARD:** this is wonderful. this is the most complete application i've ever seen.
  - **PRITCHARD:** oh. you didn't need one. there's no parking on corp hill. cars aren't allowed.
  - **PRITCHARD:** ...i'll laminate it for you. you deserve that.
  - _does: give:premium_parking_permit_

**Reward:** 50 coupons, premium_parking_permit
**Review card:** EXCEEDS EXPECTATIONS. permitted. / MEETS EXPECTATIONS. pending. / SEE ME. form 1a (revised) (revised).

---

## THE COMMUTE

### THE REGION `sq_commute_the_region`
_Gary, ninety-eight, still runs his site office on the lip of a crater. He's filed a quarterly report every quarter for sixty-one years. Deliver them._

**Where:** Gary's Site Office (THE COMMUTE), The ☺ Spire Lobby (CORP HILL)  
**Who:** GARY  
**Giver:** GARY · **Needs:** m02_sauce_run

**The twist:** 244 reports. Every one lists, under ATTENDANCE, the same forty-one names, all marked PRESENT. They're his warehouse floor team. They were on the floor at 17:30; he was in the office, eating lunch late. The region is the crater. He's been taking the register for sixty-one years. When you deliver the reports to the Spire's inbox (a chute in the lobby), the clerk-bot stamps them RECEIVED, and Gary, told, says: 'oh. good. good. it's fine.' and, for once, it is.

**Beats**
- The portacabin, the mug, the walking frame. The sim Gary's voice, older.
- Carry 244 reports (a crate, heavy, on the Commute: raiders want the paper for armour).
- The Spire's inbox chute.
- Back to Gary.

**Objectives**
1. visit the site office
2. deliver 244 quarterly reports to the spire's inbox
3. tell gary

#### Talk: `region` (with GARY)
- **[start]**
  - **GARY:** oh. a visitor. nobody comes to the site office. that's why i picked it. sixty-one years ago.
  - **GARY:** i'm gary. regional manager. the region's that hole.
  - _he points out of the window at the crater. He says it the way you'd point at a car park._
  - ➤ _"what happened to the region?"_ → what
  - ➤ _"what are all these folders?"_ → folders
- **[what]**
  - **GARY:** it's fine. i've been fine for eighty years.
  - _long pause* i was eating lunch late. in here. the floor was on the floor._
  - → folders
- **[folders]**
  - **GARY:** quarterly reports. every quarter. two hundred and forty-four of them. nobody's ever come to collect.
  - **GARY:** attendance: present. all of them. i don't care what the crater says.
  - **GARY:** would you take them up the hill? the inbox is in the spire lobby. i'd go myself. *he looks at the walking frame* the frame's on a deadline.
  - _does: give:gary_reports_

#### Talk: `received` (with GARY)
- **[start]**
  - **GARY:** received? they stamped it? 'received'?
  - **GARY:** oh. good. good.
  - _he looks out at the crater for a while_
  - **GARY:** it's fine.
  - _and, for once, it is._
  - _does: flag:gary_reports_received_

**Reward:** 500 coupons
**Review card:** EXCEEDS EXPECTATIONS. all present. / MEETS EXPECTATIONS. / SEE ME. you used them as armour.

---

### SMILES `sq_commute_smiles`
_Under a collapsed overpass, a man in the old Mr. Smiles suit is hiding from the Fun Department. He wants to do one fun thing that isn't a job._

**Where:** The Overpass Hideout (THE COMMUTE), The Fun Fair (THE COMMUTE), The Spiral Freeway (THE COMMUTE)  
**Who:** MR. SMILES, THE MORALE OFFICER  
**Giver:** MR. SMILES · **Needs:** m06_option_c

**The twist:** He was in the suit at a Big Value shelter event at 17:30. The suit saved him from the flash; the face under it didn't make it. He can't take the head off. The fun thing is a kite. He's never flown one; the Fun Department always said kites weren't 'scalable'. You get him to the top of the Spiral Freeway in a paper storm, which is perfect kite weather, and he flies it for a whole minute before the Morale Officer's convoy finds him. (If you've beaten her, it never comes, and he flies it until dark.)

**Beats**
- The hideout: a big round shadow, a little gas stove, mascot gloves drying on a line.
- He tells you about mandatory fun, and a little about 17:30.
- Build a kite (scavenge: a ☺ CORP banner, an umbrella, Gordo's string).
- The Spiral Freeway in a paper storm. The kite.
- The Fun Department arrives (or doesn't).

**Objectives**
1. find the shadow under the overpass
2. build a kite
3. take mr. smiles to the top of the spiral freeway in a paper storm

#### Talk: `hiding` (with MR. SMILES)
- **[start]**
  - **MR. SMILES:** oh! a fan! nobody comes under here. that's the point of under here.
  - **MR. SMILES:** i used to be the mascot. mr. smiles. now i'm a guy in a hot suit under a bridge. hiding from my old department.
  - ➤ _"why are they after you?"_ → why
  - ➤ _"take the head off."_ → head
- **[why]**
  - **MR. SMILES:** they want me back. delphine wants me back. she wants a witness.
  - **MR. SMILES:** i was in the suit at a big value on the high street at half five. the shelter event. she wrote the ad. 'every big value is a shelter.' i was handing out balloons.
  - → fun
- **[head]**
  - **MR. SMILES:** no.
  - **MR. SMILES:** i can't take it off. i don't know what's under there. neither of us want to find out.
  - _the big painted smile looks at you. Inside it, a long breath._
  - → fun
- **[fun]**
  - **MR. SMILES:** if fun is mandatory it's a job. i did the maths. the maths broke me. then the world did.
  - **MR. SMILES:** i'd like to do one fun thing that isn't a job. a kite. i've never flown a kite. they said kites weren't scalable.

**Reward:** 400 coupons
**Review card:** EXCEEDS EXPECTATIONS. it flew. / MEETS EXPECTATIONS. it flew a bit. / SEE ME. you flew it into a digit.

---

### THE FIRST INTERN `sq_commute_first_intern`
_Todd, about a hundred and twenty, sits in a lawn chair on a bus roof while the Unpaid worship him. Get him off the roof for one day._

**Where:** The Shrine of the First Intern (THE COMMUTE), Camp Onboarding (THE COMMUTE), The Unfinished Bit (THE COMMUTE)  
**Who:** TODD, EMPLOYEE OF THE MONTH, THE MISSING TEXTURE  
**Giver:** TODD · **Needs:** m06_option_c

**The twist:** Todd wrote the world's physics on his first day, from memory, and never finished it. There's a bit of the Commute that's just purple and black squares. It's been growing. In part 2 Todd takes you there to finish it, and it fights back. In part 3, if you've fought Employee of the Month, Todd finds out the warlord's intern badge says TODD: Craig is his grandson.

**Beats**
- The shrine: offerings of staplers and mugs; the Unpaid chanting 'the grind never stops'.
- Todd asks you, in a whisper, to get him down. A stealth extraction (or a fight, or an internship: with the Unpaid lanyard you can just walk him down as 'his assistant').
- Part 2: the Unfinished Bit. Secret boss: THE MISSING TEXTURE.
- Part 3: the badge.

**Objectives**
1. climb the shrine
2. get todd off the bus roof

**Part: THE UNFINISHED BIT** _(if flag:todd_off_the_roof)_
1. take todd to the unfinished bit
2. _(automatic)_ · **boss: THE MISSING TEXTURE**

**Part: THE BADGE** _(if flag:texture_patched done:sq_commute_eotm)_
1. show todd employee of the month's badge

#### Talk: `prophet` (with TODD)
- **[start]**
  - **TODD:** oh hey! sorry, i'm on a deadline. the deadline was before the end of the world.
  - **TODD:** please stop praying at me. *to the raiders below* PLEASE STOP PRAYING AT ME.
  - **RAIDER:** *chanting* the first intern speaks. the grind never stops.
  - **TODD:** they feed me regrowth with a spoon. it tastes like pennies and guilt.
  - _whispering* get me down. one day. i want to finish something. i never finish anything._

#### Talk: `badge` (with TODD)
- **[start]**
  - _You hand Todd the badge you took off Employee of the Month: an old ☺ CORP intern badge, cracked. It says TODD._
  - **TODD:** that's... that's mine. that's my old one. i lost it in... i gave it to my son. when he was little. so he'd have something from my work.
  - **TODD:** where did you...
  - _he looks across the Commute at the war-rig, at the huge man in the plaques._
  - **TODD:** ...oh.
  - _he sits down on the bus roof. After a while, Craig climbs up and sits next to him. Neither of them knows what to say. They sit._

**Reward:** 600 coupons
**Review card:** EXCEEDS EXPECTATIONS. finished. / MEETS EXPECTATIONS. mostly finished. / SEE ME. // TODO

---

### PERFORMANCE REVIEW `sq_commute_eotm`
_The Unpaid want to become a company. A company needs a big win. Employee of the Month has decided the big win is you._

**Where:** Camp Onboarding (THE COMMUTE), The Ring Road (THE COMMUTE)  
**Who:** EMPLOYEE OF THE MONTH, TODD  
**Giver:** EMPLOYEE OF THE MONTH · **Needs:** m02_sauce_run, act>=2

**The twist:** What he actually wants is a performance review: someone, anyone, to tell him how he's doing. If you took his internship in m02, you're 'staff' and you can give him one after the fight (a dialogue). Whatever you say, he takes it seriously. 'MEETS EXPECTATIONS' makes him cry. He takes one plaque off his chest and gives it to you. It has your face on it.

**Beats**
- Camp Onboarding: a bus depot made of desks. A job fair that's an ambush.
- World boss: EMPLOYEE OF THE MONTH on his war-rig.
- The review.

**Objectives**
1. attend camp onboarding's job fair
2. _(automatic)_ · **boss: EMPLOYEE OF THE MONTH**
3. give him a performance review

#### Talk: `review` (with EMPLOYEE OF THE MONTH)
- **[start]**
  - _On the stalled war-rig's roof, plaques cracked, Craig sits with his helmet off._
  - **EMPLOYEE OF THE MONTH:** is this... is this a performance review?
  - ➤ _"exceeds expectations."_ → exceeds
  - ➤ _"meets expectations."_ → meets
  - ➤ _"see me."_ → see
- **[exceeds]**
  - _He stares.* nobody's ever... nobody's ever said that. i've said it. i've said it seven hundred and thirty-two times._
  - → plaque
- **[meets]**
  - _His lip wobbles. He cries, enormously.* MEETS. i MEET them. i meet expectations._
  - → plaque
- **[see]**
  - _He nods slowly.* ...that's fair. that's honest feedback. i'll take it on board. the board is a desk._
  - → plaque
- **[plaque]**
  - _He unbolts one plaque from his chest and holds it out. It's been re-engraved, badly, with a nail: EMPLOYEE OF THE MONTH: THE MACHINE THING. Your face, scratched in._
  - _does: flag:eotm_reviewed_

**Reward:** 1200 coupons, lt_boss_eotm
**Review card:** EXCEEDS EXPECTATIONS. / MEETS EXPECTATIONS. / SEE ME.

---

### MANDATORY FUN `sq_commute_mandatory_fun`
_The Fun Department's carnival comes out at night on the Commute. Every game is rigged, and losing one is a fight._

**Where:** The Fun Fair (THE COMMUTE)  
**Who:** THE MORALE OFFICER, MR. SMILES  
**Giver:** MR. SMILES · **Needs:** m06_option_c

**The twist:** The Morale Officer wrote 'every Big Value is a shelter'. The carnival's noise is so she never has to hear the quiet. The way to beat her for good is to stop shooting and wait. Mr. Smiles, if he's with you, takes his own glove off (just the glove) and holds her hand while she takes her heads off.

**Beats**
- The Fun Fair: ring toss, hook-a-duck, whack-a-mole with real moles, a ghost train that's a real ghost train.
- Win three games (each loss is a mascot brawl).
- World boss: THE MORALE OFFICER.
- The quiet.

**Objectives**
1. win 3 games at the fun fair · if clock.commute=20:00-04:00
2. _(automatic)_ · **boss: THE MORALE OFFICER**

**Reward:** 1100 coupons, lt_boss_morale_officer
**Review card:** EXCEEDS EXPECTATIONS. FUN! / MEETS EXPECTATIONS. fun. / SEE ME. you had fun. it was mandatory.

---

### UNLUCKY 13 `sq_commute_unlucky_13`
_The fallen 13 on the Commute is waking up. It was one of Remainder's orbital billboards that guided the missiles, and its last target list is still loaded._

**Where:** The Fallen 13 (THE COMMUTE), Union Hall 13 (NUMBER WORKS)  
**Who:** NELL THIRTEEN, UNLUCKY 13  
**Giver:** NELL THIRTEEN · **Needs:** m15_rounding_down

**The twist:** Its last target is the Bottom. It's been trying to fire for sixty-one years and never had the power. The fights you've had near it have been charging it. Nell's union were stamped with 13s because the satellite was a 13: 'they put the number on us that they put on the thing that killed us. management's sense of humour.'

**Beats**
- Nell: the Remainders want it dead. It's personal.
- The hot zone: radiation, glassed craters, toxic green glow.
- World boss: UNLUCKY 13.
- Its last panel: the target list, crossed out.

**Objectives**
1. shut down the 13 · **boss: UNLUCKY 13**

#### Talk: `thirteen` (with NELL THIRTEEN)
- **[start]**
  - _Nell, without the megaphone for once._
  - **NELL THIRTEEN:** you know why they stamp us with thirteen? because the satellite was a thirteen. the one on the commute. it guided the first launch.
  - **NELL THIRTEEN:** they put the number on us that they put on the thing that killed us. management's sense of humour.
  - **NELL THIRTEEN:** it's waking up. the meters in the hot zone are climbing. motion: we turn it off. all in favour? *she raises her own hand.* carried.

**Reward:** 1300 coupons, lt_boss_unlucky_13
**Review card:** EXCEEDS EXPECTATIONS. target cancelled. / MEETS EXPECTATIONS. / SEE ME. you were rounded up.

---

## Repeatable activities

### RAIDER CAMPS `raider_camps`
Clear an Unpaid camp on the Commute, then hand it to any ally as an outpost (fast travel, a safe garage). Camps get re-staffed by the Unpaid at midnight unless an ally holds them.

_midnight · from Act 1 · Camp Onboarding (THE COMMUTE), The Ring Road (THE COMMUTE)_  
**Pays:** coupons, a district-brand weapon, an outpost · _"camp onboarding is hiring. you're the opportunity."_

### SIM CONTRACTS `sim_contracts`
A faction pays you to win a particular training sim, checked server-side from the match result: 'Big Value wants a Dead Mall win with the Shopping Cart Cannon', 'the Family wants a Plant & Defuse win where you never bought a gun', 'the Remainders want a Gun Game finish with exactly 13 kills'.

_daily · from Act 1 · The Machine (THE BOTTOM)_  
**Pays:** coupons, standing with that faction, containers in the tray · _"the machine's taking bookings."_

### FIGHT CLUBS `fight_clubs`
The existing modes as bot fights in the ruins, run by the rulers: Gun Game in Number Works, Plant & Defuse in the Bocce Pit, Infection in the Food Court, Floor Is Lava on the acid lake.

_always · from Act 2 · The Number Yard (NUMBER WORKS), The Bocce Pit (PINSTRIPE), Food Court Colosseum (THE CHECKOUT), The Big Stomach (THE GUT)_  
**Pays:** loot by placement, a weekly legendary for a perfect run · _"first rule of fight club: it's in the bylaws. second rule: per section four."_

### OVERTIME! `rampages`
Kill-frenzy challenges with a weapon the game hands you (a Rat Cart Cannon in Corp Hill, a Ladle in the Gut), against the clock.

_always · from Act 1 · The Deposit Pile (THE BOTTOM), Jar Alley (CHROME GRISTLE), The Smiling Fountain (CORP HILL), The Ring Road (THE COMMUTE)_  
**Pays:** HYPE, coupons, a spray · _"OVERTIME! you're on the clock!"_

### DELIVERY RUNS `deliveries`
Silly vehicles, fragile cargo: a soup van (slosh meter), an ice-cream van (melt meter), a hearse full of balloons (it floats if you go over 80), a pizza moped in Pinstripe (respect meter).

_daily · from Act 1 · Sharon's Soup Kitchen (THE BOTTOM), Food Court Colosseum (THE CHECKOUT), The Sauce Works (PINSTRIPE)_  
**Pays:** coupons, Bottom standing · _"don't spill it. she'll ladle you."_

### RACES `races`
Street races up the Spiral Freeway, rooftop grapple races across the Wok Roofs, cart races down the Big Escalator, peristalsis surfing in the Gut (slide on the beat).

_always · from Act 1 · The Spiral Freeway (THE COMMUTE), The Wok Roofs (THE BOTTOM), The Big Escalator (THE CHECKOUT), Peristalsis Avenue (THE GUT)_  
**Pays:** coupons, car paint, a race-winner wrap · _"the speed limit is 70. so is he."_

### STUNT JUMPS `stunt_jumps`
Huge ramps with MLG overlays. The Margins' one goes into the void on purpose (you land at a gnome).

_always · from Act 1 · The Spiral Freeway (THE COMMUTE), The Smokestacks (NUMBER WORKS), The Edge (THE MARGINS)_  
**Pays:** HYPE, sprays, the 'NO SCOPE' horn · _"SICK. ok it was a bit sick."_

### BOCCE `bocce`
Bocce against the Family's goons. The balls are heavy and the Peel Shooter is technically allowed. Win 13 in a row for a secret (the Bocce Knuckles).

_always · from Act 2 · The Bocce Pit (PINSTRIPE)_  
**Pays:** coupons, Family standing · _"settled in the pit. like gentlemen. with tiny hands."_

### WISDOM TOOTH `wisdom_tooth`
A giant tooth grows in Tooth Market square every midnight. Pull it out with the lasso and a car. The Tooth Market pays in teeth.

_midnight · from Act 1 · Tooth Market (THE GUT)_  
**Pays:** teeth (Tooth Market currency) · _"everything costs teeth. this one's free. if you can get it out."_

### JOBS `jobs`
Taxi (fares from every district, some of them strange), repo man (steal back cars ☺ CORP repossessed), Corp mail runner (pneumatic capsules on a timer; Late Fees if you're late).

_always · from Act 1 · The Lost & Found (THE BOTTOM), Dividend Road (CORP HILL), The Ring Road (THE COMMUTE)_  
**Pays:** coupons · _"taxi! take me to the void. no, the nice bit."_

### GRAFFITI `graffiti`
Tag ☺ CORP's clean walls with sprays (Z). Cleaners with bleach cannons come within 30 s. Tags that survive a day count for a reward.

_always · from Act 1 · The Bleach Line (CORP HILL), The Infinite Queue (THE CHECKOUT), The Cul-de-sac (EVERGREEN ACRES)_  
**Pays:** sprays, Bottom standing · _"the bleach line, but with art."_

### THE BOARD `cat_hunt`
Find and pet the board's twelve cats across the city (collectibles.js set 'cats'). +1 Body Budget per 3. All twelve unlock NAP TIME.

_always · from Act 1 · The Lost & Found (THE BOTTOM)_  
**Pays:** promotions · _"pet the board. it's how you get promoted."_

### LATE DESKS `late_desk`
Pay off Late Fees in coupons (the price scales with stars). The clerk is always very sorry. The Bottom's Late Desk is a cardboard box with 'NO' written on it.

_always · from Act 1 · The Bleach Line (CORP HILL), The Infinite Queue (THE CHECKOUT), The Down Escalator (THE BOTTOM)_  
**Pays:** a clean schedule · _"your fees are important to us."_

### RADIO REQUESTS `radio_requests`
Station DJs ask for stunts on air: Gut Choir FM wants a car through the Choir Lung; Pinstripe's crooner Vinnie Vowels wants a meatball delivered by grapple; Chad Tempo wants 'nothing to happen at all for one minute on Corp Hill' (impossible).

_daily · from Act 2 · The Lost & Found (THE BOTTOM)_  
**Pays:** coupons, radio shout-outs · _"someone stapled a guy to the fountain. traffic is fine."_
