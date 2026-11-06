// OVERDUE collectibles: the history, found in pieces. Memos (paper), recordings (tapes, answering machines, held
// calls), Option C slides (the deck, scattered), memory fragments (Overtime's and Cale's), and the board cats.
// SCHEMA
//   COLLECTIBLE_SETS[id] = { name, desc, reward (what completing the set does) }
//   COLLECTIBLES[id]     = { set, name, where (LOCATIONS id), how (how it's found), text (what it says; the history),
//                          quest? (the quest that gives it), if? (a condition to appear), do? (actions on pickup) }
// Writing rule: memos and recordings are the war told by the people in it. Deadpan, specific, never a punchline about the dead.

export const COLLECTIBLE_SETS = {
  overtime: { name: "OVERTIME'S LOST BACKUPS", desc: "Six of Edwin Sallow's memories the Machine kept from bodies that died.", reward: "all six unlock the talk-down in Fully Billable (m31) and the Spare Tray secret implant" },
  cale: { name: "CALE'S MEMORIES", desc: "Twelve moments of Rory Cale's life, before the last workday.", reward: "each one plays a memory flash (at Drift under 4) and adds a line to Mina's scenes; all twelve add a final panel to every ending" },
  option_c: { name: "THE DECK", desc: "Twelve loose slides of the Option C presentation, printed to the wrong printer on the 58th floor and scattered.", reward: "all twelve make the published Option C (OFF THE BOOKS) include the full deck, and unlock a THEATRE replay of Hask presenting it" },
  memos: { name: "MEMOS", desc: "Paper. The war and the sixty-one years after it, in office voice.", reward: "every 10 memos: +1 Tote Bag row" },
  recordings: { name: "RECORDINGS", desc: "Tapes, voicemails, held calls and answering machines.", reward: "all of them unlock the Radio station OLD LINES (every recording on a loop)" },
  cats: { name: "THE BOARD", desc: "The board of directors' descendants, asleep across the ruins. Pet them: promotions.", reward: "+1 Body Budget per 3 cats; all twelve unlock NAP TIME" },
};

const C = (set, name, where, how, text, extra) => ({ set, name, where, how, text, ...(extra || {}) });

export const COLLECTIBLES = {
  // ================================================================ OVERTIME'S SIX
  ot_first_day: C("overtime", "FRAGMENT: FIRST DAY", "sims:warehouse", "In the training sims, in the Warehouse map's site office: a vending machine in the corner that isn't in any other match. Shoot it.",
    "A mall, a long time ago. A young man in a grey suit restocking a single vending machine. It has never once given anyone change. A large grey-and-white cat walks across the keys of the till and sits on his lap. A voice off-screen: 'the founder likes you, ed. you're hired.' He's never been so proud."),
  ot_lunchbox: C("overtime", "FRAGMENT: THE LUNCHBOX", "bottom:lostfound", "Lost Property's tenth item (sq_bottom_lost_property).",
    "A dented lunchbox. A note taped to the lid: 'don't be late tonight. it's our forty. love, j.' He never ate it.", { quest: "sq_bottom_lost_property" }),
  ot_eotm_photo: C("overtime", "FRAGMENT: EMPLOYEE OF THE MONTH", "corphill:museum", "The EMPLOYEE #1 case in the Punctuality Museum (sq_corphill_punctuality_museum).",
    "A framed photo: the very first Employee of the Month. A cat on his lap. At the edge of the frame, out of focus, a woman laughing at him for being so serious.", { quest: "sq_corphill_punctuality_museum" }),
  ot_lobby_order: C("overtime", "FRAGMENT: THE ORDER", "lates:warehouse", "In the Restoration Warehouse (m23 or after), the dock labelled E. SALLOW · SPARE (3 of 3): a memo clipped to the empty body's lanyard.",
    "A ☺ CORP memo, 15:00, Final Quarter: 'Head of Timekeeping: hold the lobby until close of business. Nobody leaves before 17:30. This is for their safety. M. Hask.' Handwritten under it, in his own hand: 'for their safety. ok.'", { if: "done:m23_workforce_restoration" }),
  ot_1729: C("overtime", "FRAGMENT: 17:29", "lates:stairwell", "A held call on the Lates switchboard (sq_lates_hold_music).",
    "A lobby phone, left off the hook at the security desk. Footsteps, running, on marble. A polite voice: 'cale. you're running. that's against policy.' A clunk, like a card being punched. Then nothing for nineteen seconds.", { quest: "sq_lates_hold_music" }),
  ot_1730: C("overtime", "FRAGMENT: 17:30", "bottom:long_stairs", "The answering machine at 14 Hillside Road, in the ruins by the Long Stairs (sq_evergreen_return_address).",
    "'june, it's ed. i'm, i'm here. it's 17:30. i'm on my way.' The end of his shift.", { quest: "sq_evergreen_return_address" }),

  // ================================================================ CALE'S TWELVE
  cale_strawberry: C("cale", "MEMORY: THE STRAWBERRY", "bottom:lostfound", "Dale's Lost Property ledger lists 'keyring, strawberry, felt'. It's in the RETURNS box you sleep in. It's been there the whole game.",
    "Mina, aged six, sewing a felt strawberry with her tongue out. 'it's for your bag. so you remember to come home.'"),
  cale_green_man: C("cale", "MEMORY: THE GREEN MAN", "bottom:down_escalator", "At the bottom of the Down Escalator, a pedestrian crossing button from before the war, half buried. Press it.",
    "A crossing, a small hand in yours. 'rory, the green man.' 'i know, mina.' 'you always say you know.'"),
  cale_flat: C("cale", "MEMORY: FLOOR 9", "bottom:rooftops", "Overdraft Heights collapsed into the Bottom. On the Wok Roofs, one container's door has a faded number: 9B. Open it.",
    "A tiny flat on the ninth floor, a pull-out bed, school drawings on the fridge. Running up the stairs to say you'd done it in forty seconds."),
  cale_long_ward: C("cale", "MEMORY: THE LONG WARD", "gut:campus", "In the Gristle & Sons campus, a hospital wing grown shut: a ward sign, 'LONG WARD'. A bed with a name tag.",
    "Visiting hours. Mum in the long ward, asleep. A nurse saying 'are you the eldest? you're doing very well.' You were nineteen."),
  cale_first_day: C("cale", "MEMORY: FIRST DAY", "corphill:spire_lobby", "In the Spire lobby (Act IV), the revolving door. Walk through it the 'wrong way'.",
    "A first day. A lanyard that says CALE R. 4417. A huge polite man at the security desk who catches it when it falls out of the revolving door. 'you'll want this, cale. you'll need it to leave.'"),
  cale_audit: C("cale", "MEMORY: THE AUDIT", "corphill:spire_60", "On the 60th floor (Act IV raid or post-game), Agnes's old desk by the window. A sticky note under the drawer.",
    "Agnes: 'that's the third fake invoice you've caught this week. you're good at this, rory.' 'i just like it when things add up.'"),
  cale_lunch: C("cale", "MEMORY: LUNCH BREAK", "chromegristle:arcade", "Arcade Legend: beat CALE R.'s high score and enter RC (sq_chromegristle_arcade_legend).",
    "'you're wasting your break, rory.' 'it's the only bit of the day that's mine.'", { quest: "sq_chromegristle_arcade_legend" }),
  cale_birthday: C("cale", "MEMORY: THE BIRTHDAY", "checkout:food_court", "A burned-out party shop on the Food Court's upper level. A balloon still inflated, sixty-one years later, in a glass case.",
    "Mina's ninth birthday, in a food court. Rory late, running, with a balloon. 'you're late.' 'i'm here though.' 'you're always here though.'"),
  cale_bus: C("cale", "MEMORY: THE NIGHT BUS", "margins:bus_stop", "On The Last Bus (sq_margins_the_last_bus), the back seat.",
    "A night bus home after a late shift. Asleep against the window. A woman across the aisle wakes you at your stop. 'you looked like you needed it.'", { quest: "sq_margins_the_last_bus" }),
  cale_letter: C("cale", "MEMORY: THE LETTER", "evergreen:culdesac", "The Mailman's satchel (sq_evergreen_return_address): a letter to MINA CALE, FLAT 9B.",
    "A note in a lunchbox, from Rory to Mina: 'back at half five. eat your apple. not the core. R.'", { quest: "sq_evergreen_return_address" }),
  cale_promise: C("cale", "MEMORY: THE PROMISE", "lates:canteen", "In the Lates canteen, a payphone. Lift the receiver at 12:41, when Gus drops his fork.",
    "The night before. Mina in the pull-out bed. 'are you picking me up tomorrow?' 'half five. i promise.' 'you always say you promise.' 'i always do, though.'"),
  cale_shoes: C("cale", "MEMORY: THE TRAINERS", "sims:stairwell", "In the Last Workday 17:20 flashback, on the 52nd floor landing: stop and change into your trainers (an interaction most players run past).",
    "You change into your trainers on the stairs because the work shoes pinch and you're going to have to run. You always kept them in your bag for running for buses."),

  // ================================================================ THE DECK (Option C slides)
  slide_01: C("option_c", "SLIDE 1: TITLE", "corphill:spire_60", "The 58th floor print room (Act IV), in the wrong printer's tray.", "OPTION C: STRATEGIC WRITE-OFF. CONFIDENTIAL. BOARD EYES ONLY. Six logos. Clip art of a handshake."),
  slide_04: C("option_c", "SLIDE 4: THE PROBLEM", "numberworks:archive", "The Forecast Archive's spools.", "Q4 FORECAST: ALL DIVISIONS MISS. A bar chart going down. A footnote: 'revision expected 09:00. do not wait for it.'"),
  slide_09: C("option_c", "SLIDE 9: OPTIONS", "pinstripe:claims", "The Claims Office's filing cabinet, under 'C'.", "OPTION A: CUT THE BOTTOM DIVISION (rejected: 'they are all the bottom division'). OPTION B: MERGE AGAIN (rejected: 'there is nobody left to merge with'). OPTION C: see appendix."),
  slide_14: C("option_c", "SLIDE 14: LIABILITIES", "corphill:cathedral", "The Cathedral of Shareholder Value's pulpit.", "LIABILITIES EXTINGUISHED AT CLOSE OF BUSINESS: WAGES (TODAY), PENSIONS (ALL), DEBTS (ALL DIVISIONS). A smiley face drawn on the slide in biro."),
  slide_18: C("option_c", "SLIDE 18: CONTINUITY", "bottom:machine", "Inside the Machine's service panel (Dale opens it after m24).", "CONTINUITY OF WORKFORCE: FINAL BACKUP AT 17:30 VIA THE ORIGINAL UNIT. STAFF RETAINED AS ASSETS. 'they'll never know.'"),
  slide_22: C("option_c", "SLIDE 22: SHELTERS", "checkout:pa_booth", "Gail's booth, taped to the back of a cassette case.", "SHELTER CAPACITY: MEMBERS ONLY. NON-MEMBERS: STOCK SHRINKAGE. A marketing note: 'tell them every big value is a shelter. it tests well.'"),
  slide_26: C("option_c", "SLIDE 26: RECOVERY", "chromegristle:jar_alley", "In a jar in Jar Alley, folded.", "POST-EVENT WORKFORCE RECOVERY (GRISTLE): REGROWTH APPLIED TO CASUALTIES. ESTIMATED YIELD: 60%. A pencil note: 'never tested on the dead. G.'"),
  slide_31: C("option_c", "SLIDE 31: THE FORECAST", "commute:digit_13", "In the Fallen 13's control cabin, after Unlucky 13.", "FORECAST: POST-EVENT HEADCOUNT REDUCTION: 4,112,006,551. A list of cities.", { if: "done:sq_commute_unlucky_13" }),
  slide_33: C("option_c", "SLIDE 33: CLEARANCE", "margins:show_home", "The Show Home's map, behind the pins.", "NON-PRODUCTIVE LAND CLEARANCE (VACANCY): PHASE ONE: DIVISIONS IN DEFAULT. PHASE TWO: WHEREVER THE POOR END UP."),
  slide_36: C("option_c", "SLIDE 36: THE SCHEDULE", "lates:tuesday_tower", "At the top of Tuesday Tower, in the clock with no hands.", "SCHEDULE DEPLOYMENT (☺ CORP): THE LATES (TEST SITE). 'lock the district at 17:30 and see if it holds.'"),
  slide_39: C("option_c", "SLIDE 39: TIMING", "corphill:spire_top", "Hask's office, in the shredder (post-game).", "EXECUTION: 17:30 TODAY (CLOSE OF BUSINESS). A cheerful clip-art clock. 'so everybody's home.'"),
  slide_41: C("option_c", "SLIDE 41: SIGN-OFF", "corphill:master_clock", "On the Master Clock's control console (m32 or post-game).", "SIGN-OFF: 16:59. Six signature blocks. ☺ CORP's is the only one with the time written beside it."),

  // ================================================================ MEMOS
  col_memo_wok: C("memos", "MEMO: DISHES", "bottom:lostfound", "Pinned in Dale's shed.", "'thirteen dishes installed. one faces the lates. do not adjust. facilities.'"),
  col_memo_choir: C("memos", "MEMO: NEW HYMN", "gut:choir_lung", "On Sister Agenda's desk after Belly Button.", "'new hymn approved. no conductor. the back pew is reserved.'", { if: "flag:choir_new_song" }),
  col_memo_knuckle: C("memos", "MEMO: THE KITCHEN", "pinstripe:restaurant", "Mamma Polizza's kitchen wall.", "'knuckles from the bocce pit only. never lose thirteen in a row. never win thirteen in a row either.'"),
  col_memo_cat: C("memos", "MEMO: COLLAR TAG", "bottom:lostfound", "On the collar of whichever board cat you pet sixth.", "'promotions are awarded in person. while you sleep.'"),
  col_memo_nan: C("memos", "MEMO: THE INCIDENT", "numberworks:archive", "In the Forecast Archive.", "'lost: one rib, thirteenth. last seen tallest stack during the incident. do not recover during NaN.'"),
  col_memo_smiles: C("memos", "NOTICE: MISSING MASCOT", "commute:smiles_hideout", "Stapled to the overpass.", "'missing mascot. last seen smiling. reward: fun.'"),
  memo_ration_cut: C("memos", "MEMO: RATION ADJUSTMENT", "corphill:museum", "A Punctuality Museum display: 'THE SCHEDULE SAVES LIVES'.", "Year 2 of the Long Dark: 'non-essential staff who miss their slot three times will be released to the exterior. this is not a punishment. it is arithmetic. M.H.' Agnes Pell's name is on the release list. So is a Facilities couple, floor 22, 'plus one (unscheduled)'."),
  memo_backpay: C("memos", "MEMO: BACK PAY", "bottom:school", "On the Crayon School wall, in a frame Auntie made.", "The first Late Fees notice the Bottom ever got, forty years ago: 'BACK PAY OWED SINCE THE FINAL QUARTER: 160 QUARTERS.' Auntie's crayon annotation: 'for a job none of us had.'"),
  memo_gut_contract: C("memos", "MEMO: SUPPLY CONTRACT", "gut:feed_dock", "The feed dock's clipboard.", "'☺ CORP to Gristle & Sons: feedstock, monthly, from overdue districts. Organs: priority delivery UP THE HILL. Recipient: confidential (CPO).'"),
  memo_pilot: C("memos", "MEMO: PILOT PROGRAMME", "evergreen:clubhouse", "The HOA Clubhouse notice board.", "'Restoration pilot: Evergreen Acres. Units update 03:00. Residents report satisfaction 100%. Units report satisfaction 100%. (Units cannot report anything else.)'"),
  memo_lates_test: C("memos", "MEMO: TEST SITE", "lates:remainder_office", "The Remainder downtown office, Neville's desk.", "'Schedule Bomb trial (downtown, 17:30): lock the district in one moment and see if it holds. Staff in the area are not to be informed. It's only a test.'"),
  memo_merger_vote: C("memos", "MEMO: THE VOTE", "corphill:cathedral", "Framed in the Cathedral's vestry.", "'Merger vote: carried. Founder's vote: yyyyyyyyyyyy (legally a yes). Minutes taken by E. Sallow, who brought the founder in.'"),
  memo_stampede_ad: C("memos", "AD COPY: SHELTER", "commute:carnival", "In the Fun Department's ghost train, framed.", "Marketing proof, approved 16:48: 'EVERY BIG VALUE IS A SHELTER! Don't panic. Shop!' Initialled D.G. A note: 'tested very well.'"),
  memo_upsell_kid: C("memos", "SCRAP: A CHILD'S LIST", "chromegristle:upsell_clinic", "Behind the till, in a frame.", "In a child's handwriting, sixty years old: 'things in the gut: a watch, a ring, a hand, two kidneys (good), a lanyard. sell to the man on the stairs.' Upsell kept it."),
  memo_vacancy_postcard: C("memos", "POSTCARD", "margins:edge", "Pinned to the Janitor's lifeguard tower.", "A Vacancy Holdings anniversary postcard: 'Congratulations on 60 years at your Premium Negative Space! Your plot is doing great.' Addressed to W. Mopes. Stamped every year."),
  memo_hask_ledger: C("memos", "LEDGER PAGE", "corphill:spire_top", "Hask's desk, post-game.", "A page of her ledger: names, organs, dates, in tiny handwriting. Beside each one, a small tick: read."),
  memo_unpaid_charter: C("memos", "THE UNPAID CHARTER", "commute:unpaid_camp", "Nailed to the main desk-wall at Camp Onboarding.", "'1. the grind never stops. 2. we're a family. 3. every month, someone is employee of the month. 4. it's craig. 5. pray to the first intern (do not bother him).'"),
  memo_sevens_wood: C("memos", "A NOTE ON WOOD", "numberworks:press", "Under Mr. Sevens' piece of real wood.", "'17:10. called M.H. re: revised. thanked me for my time. touch wood. touch wood. touch wood.'"),

  // ================================================================ RECORDINGS
  rec_long_dark: C("recordings", "TAPE: THE GATES", "corphill:bleach_line", "A Timekeeping relay's archive (m18).", "Spire gate security, year 1 of the Long Dark: a crowd in the snow. 'open the gates. there are children.' A calm voice on a speaker: 'the next available slot is in 2,400 days. thank you for your patience.'"),
  rec_gail_first: C("recordings", "TAPE: THE FIRST ANNOUNCEMENT", "checkout:pa_booth", "Gail's oldest cassette, labelled DAY 1.", "'attention shoppers. the doors will remain closed. we're sorry for any inconvenience.' Then, off-mic, a young woman crying, and the tape keeps running for forty minutes."),
  rec_choir_first: C("recordings", "TAPE: THE FIRST HYMN", "gut:choir_lung", "Sister Agenda's Filofax has a cassette in the back.", "Year 3. The Gristle & Sons staff, still at their desks, the building's walls starting to grow. Someone starts humming to cover the sound. Everyone joins in. They don't stop."),
  rec_evergreen_door: C("recordings", "TAPE: OPENING DAY", "evergreen:shelter", "The shelter's PA system.", "Year 30. A shelter door opening. Cheering. Then a child's voice, very quiet: 'mum, what's in the valley?' and an adult voice, after a long time: 'nothing, linda. there's nothing there.'"),
  rec_neville_voicemail: C("recordings", "VOICEMAIL: NEVILLE", "lates:waiting_room", "The Waiting Room's ticket machine has a voicemail button.", "'it's neville from remainder, i'm stuck in traffic, the lifts are, i'll be there by 16:59, tell them not to sign anything, tell them we hit it, we HIT it—'"),
  rec_todd_onboarding: C("recordings", "TAPE: ONBOARDING", "commute:todd_shrine", "Todd's laptop with no screen still plays audio.", "A young man's voice, nervous: 'ok. physics. day one. gravity is... about 26? ish. stopping things costs extra. they didn't buy it. so things just keep going. ok. that's fine. that'll be fine.'"),
  rec_dale_report: C("recordings", "PAGER LOG: ANOMALIES", "bottom:dale_shed", "Dale's pager on its nail (after m24).", "Forty years of monthly reports in one beep each: 'MACHINE STATUS: HUMMING. TRAY: EMPTY. ANOMALIES: NONE.' The last one: 'ANOMALIES: ONE.'"),
  rec_mina_letters: C("recordings", "TAPE: MINA'S LETTERS", "checkout:vents", "Wristband recorded himself reading every letter Mina sent him (in the vents' classroom).", "Sixty years of New Year's letters, read by an old man: 'dear milo. i went to see dale again. he says the machine doesn't give anything back. i think it's just late. love, m.'"),
  rec_hask_1710: C("recordings", "CALL: 17:10", "numberworks:press", "In Mr. Sevens' safe (DEAL in m15: his envelope; TAKEOVER: the union opens it in Act IV).", "'Ms. Hask, it's Lucius Sevens at Remainder. The revised numbers. We hit target. Half a percent.' 'Thank you for letting me know. No. That will not change anything. Good afternoon.'", { if: "done:m15_rounding_down" }),

  // ================================================================ THE BOARD (twelve cats in the city; the five sim cats are in shared/secrets.js)
  cat_marmalade: C("cats", "MARMALADE · VP OF NAPS", "bottom:lostfound", "Asleep in the RETURNS box.", "A ginger cat. It's yours now. Well. You're its."),
  cat_doubloon: C("cats", "DOUBLOON · TREASURER", "pinstripe:rafters", "In Nonna's nest, among the pulleys.", "A black cat with a gold collar. Nonna pretends it isn't there."),
  cat_toast: C("cats", "TOAST · HEAD OF CATERING", "bottom:soup_kitchen", "On Sharon's warm stove (not lit).", "A cream cat that smells of tomato."),
  cat_parcel: C("cats", "PARCEL · LOGISTICS", "checkout:returns", "On the counter of Returns Desk Zero.", "A tabby, curled in a returns tray. The only thing ever returned there."),
  cat_ledger: C("cats", "LEDGER · AUDIT", "corphill:spire_60", "On Agnes's old desk on the 60th floor.", "A grey cat with huge eyes. It looks at you like an auditor."),
  cat_static: C("cats", "STATIC · BROADCAST", "corphill:fountain", "On top of Chad Tempo's news desk.", "A white cat that sheds on camera. Chad reads around it."),
  cat_sevens: C("cats", "LUCKY · RISK", "numberworks:press", "On Mr. Sevens' piece of real wood.", "A black cat. Mr. Sevens is terrified of it. It's very friendly."),
  cat_gristle: C("cats", "GIBLET · R&D", "gut:choir_lung", "In the back pew.", "A hairless pink cat. It fits right in."),
  cat_loop: C("cats", "TUESDAY · OPERATIONS", "lates:canteen", "On Gus's tray. Every day.", "A tortoiseshell. It's on the tray at 12:40 every Tuesday. It eats the last bite."),
  cat_gnome: C("cats", "MOSS · ESTATES", "margins:gnome_field", "Among the gnomes, sitting very still.", "A grey cat pretending to be a gnome. It's very good at it."),
  cat_neon: C("cats", "CHROME · CLINICAL", "chromegristle:noodle_shrine", "On the Noodle Shrine's offering plate.", "A cat with one robot leg, installed by Bev. It's fine. It's very fast."),
  cat_hedge: C("cats", "TOPIARY · PROPERTY", "evergreen:pumpkin", "On the Prize Pumpkin.", "A tuxedo cat. Linda has fined it 400 times."),
};
