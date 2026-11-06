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
  // ---------------------------------------------------------------- act II
  family_premium: { name: "THE FAMILY'S PREMIUM", kind: "quest", desc: "A briefcase of ☺ CORP's protection money for the Family. It's very heavy and very insured." },
  mallrat_cart_cannon: { name: "RAT CART CANNON", kind: "weapon", base: "cart", desc: "A Shopping Cart Cannon painted with little green rat faces. Shoot carts into the Cart Mother. She can't help picking them up." },
  overtime_lanyard: { name: "OVERTIME'S LANYARD", kind: "key", keep: true, desc: "Employee #1's access, with ninety years of employee-of-the-month badges. Opens ☺ CORP service doors and the Big Escalator." },
  sevens_call_log: { name: "SEALED ENVELOPE", kind: "document", keep: true, desc: "From Mr. Sevens, 'as insurance against our mutual friend at the top'. A phone log: 17:10, to M. HASK, 4 minutes. Nothing about what was said." },
};
