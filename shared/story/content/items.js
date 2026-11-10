// OVERDUE key and quest items: things that go in the Tote Bag but aren't rolled loot (loot.js) or implants
// (implants.js). Pages, keys, documents, quest props.
// SCHEMA: ITEMS[id] = { name (ALL CAPS), kind: 'page' | 'key' | 'document' | 'quest' | 'weapon' | 'consumable',
//         desc (the item text, in the game's voice), base? (a shared/weapons.js id when kind is 'weapon'),
//         keep? (true = can't be sold or dropped) }

export const ITEMS = {
  // ---------------------------------------------------------------- the six pages of Option C
  page_family: { name: "OPTION C: PAGE (FAZZOLETTI)", kind: "page", keep: true, desc: "\"act of shareholders. no policy shall pay out on a loss caused by the policyholders' own board.\" signed by Nonna. her son smiled for the photo." },
  page_bigvalue: { name: "OPTION C: PAGE (BIG VALUE)", kind: "page", keep: true, desc: "\"members-only continuity. non-members to be treated as stock shrinkage.\" soft from sixty-one years in a receipt." },
  page_remainder: { name: "OPTION C: PAGE (REMAINDER)", kind: "page", keep: true, desc: "\"the forecast.\" target lists, casualty estimates, and a number in a child's pencil in the margin: 4,112,006,551." },
  page_gristle: { name: "OPTION C: PAGE (GRISTLE & SONS)", kind: "page", keep: true, desc: "\"post-event workforce recovery.\" Regrowth, to raise the dead as labour. It didn't work. It made the Gut. This was the patent." },
  page_vacancy: { name: "OPTION C: PAGE (VACANCY)", kind: "page", keep: true, desc: "\"non-productive land clearance.\" void bombs for districts that can't pay. the Bottom is listed as 'phase two'." },
  page_corp: { name: "OPTION C: PAGE (☺ CORP)", kind: "page", keep: true, desc: "\"approval and continuity. execution at close of business (17:30). final backup of all staff to be retained as workforce.\" signed: M. Hask." },
  // ---------------------------------------------------------------- act I
  lost_property_weapon: { name: "LOST PROPERTY", kind: "weapon", base: "pistol", desc: "Someone lost this. Now you've found it. That's how lost property works. (a guaranteed rare Plan B from the bins)" },
  soup_pot: { name: "THE RED POT", kind: "quest", desc: "Sharon's tomato soup, full to the top. Don't spill it. She'll ladle you." },
  medicine_crate: { name: "MEDICINE (MOSTLY)", kind: "quest", desc: "A crate of Gristle & Sons medicine. One box is labelled GROWTH ADJUSTMENT and is empty." },
  unpaid_lanyard: { name: "UNPAID LANYARD", kind: "key", desc: "\"INTERN.\" Low-rank raiders on the Commute sometimes wave you through. The lanyard is also an intern." },
  loop_train: { name: "THE TRAIN", kind: "key", keep: true, desc: "Dale's loco, a flatbed and half a wagon. \"it's more of a tractor. but it's on rails.\" Fast travel round the Under-Hill Loop to anywhere you've already been, and the way into the Gut." },
  // ---------------------------------------------------------------- act II
  family_premium: { name: "THE FAMILY'S PREMIUM", kind: "quest", desc: "A briefcase of ☺ CORP's protection money for the Family. It's very heavy and very insured." },
  mallrat_cart_cannon: { name: "RAT CART CANNON", kind: "weapon", base: "cart", desc: "A Shopping Cart Cannon painted with little green rat faces. Shoot carts into the Cart Mother. She can't help picking them up." },
  overtime_lanyard: { name: "OVERTIME'S LANYARD", kind: "key", keep: true, desc: "Employee #1's access, with ninety years of employee-of-the-month badges. Opens ☺ CORP service doors and the Big Escalator." },
  sevens_call_log: { name: "SEALED ENVELOPE", kind: "document", keep: true, desc: "From Mr. Sevens, 'as insurance against our mutual friend at the top'. A phone log: 17:10, to M. HASK, 4 minutes. Nothing about what was said." },
  // ---------------------------------------------------------------- act III
  schedule_printout: { name: "THE SCHEDULE", kind: "document", keep: true, desc: "Nine kilometres of ☺ CORP's city, booked to the minute. There's a white band across it at 03:00 where nobody is." },
  yellow_soup: { name: "THE YELLOW", kind: "quest", desc: "Sharon's yellow soup. Dot's favourite. It keeps the digesters talking." },
  late_memo: { name: "NEVILLE'S ENVELOPE", kind: "document", keep: true, desc: "REMAINDER INDUSTRIES · Q4 REVISED (09:00) · TARGET MET (+0.5%). Pencilled: 'the 17:30 thing won't be needed now. N.' Sixty-one years late." },
  // ---------------------------------------------------------------- act IV
  tall_guy_file: { name: "HR FILE: G. LONG", kind: "document", desc: "HR Business Partner, 31. On loan to Vacancy Holdings (void survey). Returned: —. An exit interview, unsigned." },
  sale_agreement: { name: "SALE AGREEMENT", kind: "document", keep: true, desc: "THE BOTTOM (ALL PLOTS, ALL OCCUPANTS). ☺ CORP TO VACANCY HOLDINGS. COMPLETION: ON RE-MERGER. Mr. Deposit's deed stapled to the back." },
  // ---------------------------------------------------------------- act V
  cale_tape: { name: "CALE'S TAPE", kind: "document", keep: true, desc: "A ☺ CORP tape cartridge. Option C, copied in the 60th-floor print room at 17:10 on the Final Quarter. Carried down sixty floors. It never got out of the building. Until now." },
  // ---------------------------------------------------------------- side quest props
  auntie_invoice: { name: "AUNTIE'S INVOICE", kind: "document", desc: "Forty pages, in crayon. 'Storage of a man. Wear and tear on the view. Emotional damp.' The total is circled four times." },
  fridge: { name: "FRIDGE", kind: "quest", desc: "A weight, at Lumps' Gym. It's also a fridge. Don't drop it on the Long Stairs." },
  lost_property_tag: { name: "LOST PROPERTY", kind: "quest", desc: "Something somebody lost on the last workday, with a name tag in Dale's handwriting." },
  voice_box: { name: "VOICE BOX", kind: "quest", desc: "From a dead switchboard operator's headset. It still says 'your call is important to us' when you shake it." },
  family_laundry: { name: "THE FAMILY'S LAUNDRY", kind: "quest", desc: "A basket of the Don's shirts. Every collar has the same grin stain. Keep it crisp." },
  declined_log: { name: "DECLINED TRANSACTIONS", kind: "document", keep: true, desc: "Big Value's membership-scan log, 17:30 to 17:34 on the Final Quarter. Every card refused at the doors. Eight thousand and forty names." },
  rule_card: { name: "THE RULE CARD", kind: "document", desc: "'ROUND ALL OUTSTANDING VALUES DOWN BY 0.5 UNTIL THE BOOKS BALANCE.' And under it: 'we hit it. tell the board.'" },
  fq_letter: { name: "UNDELIVERED LETTER", kind: "quest", desc: "Posted on the Final Quarter. Sixty-one years in a satchel. Still sealed." },
  corp_tie: { name: "☺ CORP TIE", kind: "quest", desc: "Regulation width. Regulation knot. Regulation sadness." },
  gary_reports: { name: "244 QUARTERLY REPORTS", kind: "quest", desc: "A crate of reports from the region (a crater). ATTENDANCE: PRESENT. All forty-one." },
  smiles_kite: { name: "A KITE", kind: "quest", desc: "A ☺ CORP banner, an umbrella and some of Gordo's string. Not scalable. Fun." },
};
