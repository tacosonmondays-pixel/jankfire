// OVERDUE endings: what each ending needs, its scenes, its comment panels, and one epilogue panel per district by
// who runs it (turf). The cinematics themselves are in scenes_act5.js (e1_on_time, e2_late, e3_off_books, e4_nap_time).
// SCHEMA: ENDING_SCRIPTS[id] = {
//   needs      a condition string (when the option shows in m32's the_choice) or null
//   scenes     scene ids, in order
//   panels     [{ if?, text }]  comic panels after the cinematic: fates, Drift, Overtime, allies (first matches show; all that match show)
//   districts  { districtId: { factionId | 'any': text } }  the epilogue panel for whoever runs it ('any' = fallback)
//   postgame   how the open city looks after this ending
// }

export const ENDING_SCRIPTS = {
  on_time: {
    needs: null,
    scenes: ["e1_on_time", "credits_drive"],
    panels: [
      { if: "drift>=4", text: "you'd make a perfect employee. you do. you've never once been late. you don't remember why that used to matter." },
      { if: "drift<2", text: "every morning at 09:00 you clock in, and for one second, before the schedule loads, you remember a strawberry keyring. then it's 09:00:01." },
      { if: "flag:plan_lumps", text: "the gut's people are on the staffing table. they're fed. they're safe. they have a slot. lumps says it's better than the wall. he says it every day, like he's checking." },
      { if: "!flag:plan_lumps", text: "the bottom's living weren't on the table. the bottom isn't on the map any more. pritchard keeps a list of their names in a drawer. he isn't supposed to." },
      { if: "flag:overtime_clocked_out", text: "edwin sallow clocked out. at 09:00 the next morning the restoration reloaded him from the backup. he's on shift. he doesn't remember leaving. you do." },
      { if: "fate.mina=freed", text: "mina sends a letter every new year's eve. 'you were late for me once. you can be late for them.' the schedule files it." },
      { if: "flag:stopped_gordo", text: "wee gordo was arrested at 03:00 in the first week, on schedule. he never spoke to you again." },
      { text: "R. CALE, HEAD OF TIMEKEEPING. ten thousand copies. one lanyard each." },
    ],
    districts: {
      bottom: { any: "the bottom: sold. folded into the void, one stacked house at a time. the down escalator was the last thing to go. it was going down." },
      gut: { any: "the gut: an organ farm on contract to the restoration. the choir sings to a schedule now. the walls are fed at 06:00 and 18:00." },
      pinstripe: { family: "pinstripe: the family insures the restoration at a premium. nonna's strings run all the way up to the spire now.", punchlines: "pinstripe: the punchlines were 'rescheduled'. pip is a jester again, at corporate events, and smiles very hard." },
      checkout: { bigvalue: "the checkout: the doors open at 09:00. everyone's a member now. membership is mandatory.", mallrats: "the checkout: the welded doors were cut open on day one. the mall rats are still in the vents. security leaves them a ration at 12:00, on schedule." },
      numberworks: { remainder: "number works: prices are fixed. forever. bread costs 3. it will always cost 3.", remainders: "number works: the union was dissolved into the workforce. nell got a number. it's 13." },
      chromegristle: { any: "chrome gristle: licensed. every clinic installs schedule chips. the neon is white now." },
      evergreen: { any: "evergreen acres: the model for the whole city. every window waves." },
      lates: { any: "the lates: scheduled. it's still tuesday. it's an efficient tuesday." },
      margins: { vacancy: "the margins: vacancy is selling again. it has a lot of new stock.", marginwalkers: "the margins: the gnome line held for three weeks. then a bulldozer came at 03:00." },
      corphill: { any: "corp hill: perfectly on time. it always was." },
      commute: { any: "the commute: the unpaid were hired as restoration security. employee of the month got a real award. he cried." },
    },
    postgame: "the city is lit and on schedule: Late Fees are permanent ★1, the dead work every street, food trucks arrive on the minute, the Bottom is void. You wear the lanyard.",
  },

  late: {
    needs: null,
    scenes: ["e2_late", "credits_drive"],
    panels: [
      { if: "drift>=4", text: "you've got so many parts that aren't yours, some nights you can't tell whose memories are whose. mina says it doesn't matter. she says you're on time now. that's new." },
      { if: "drift<2", text: "with the clock gone you remember more. the flat on hillside road. the green man at the crossing. mina's hand. you write it all down, in crayon." },
      { if: "fate.dot=freed", text: "dot grows tomatoes on the long stairs. they're the first green thing on the hill in sixty-one years. lumps cries every time one ripens. it's not the sunset. it's the tomatoes." },
      { if: "!fate.dot=freed", text: "lumps won't forgive you. his mum was in the gut when the clock stopped and the choir stopped singing. he watches the sunset alone." },
      { if: "flag:overtime_clocked_out", text: "edwin sallow sits on the bottom's stairs every evening. at 17:30 he stands up, then sits back down. the kids have started standing up with him." },
      { if: "flag:lumps_took_deal", text: "lumps signed a contract with a company that doesn't exist any more. he keeps it in his wallet. he says it's to remember what he nearly was." },
      { text: "nobody owns time. nobody keeps the lights on either. it's free, and it's dangerous, and it's yours." },
    ],
    districts: {
      bottom: { any: "the bottom: still here. the void stopped at the clock. someone's built a second floor on the lost & found. it leans." },
      gut: { gristle: "the gut: without ☺ corp's trucks gristle & sons is starving, and the gut is spreading. the bishop sings at the front of it.", bottom: "the gut: the bottom's now. raw, dangerous, warm. the freed digesters patrol it in choir robes, and the green on the long stairs is coming out of it." },
      pinstripe: { family: "pinstripe: the family runs protection in the dark. you're covered. you're always covered. the price has gone up.", punchlines: "pinstripe: the punchlines run it. red noses on every door. pranks instead of protection. it's fair. it's frightening. the don was buried with a whoopee cushion." },
      checkout: { bigvalue: "the checkout: gail switched off the pa and sat in the quiet. the doors didn't open at 09:00. nobody's sure if the store is closed or just late.", mallrats: "the checkout: the doors are welded shut and painted with the names of the stampede's dead. mina comes every week to read them." },
      numberworks: { remainder: "number works: mr. sevens prints whatever prices he likes. nobody has to pay them. he's losing at the fun fair.", remainders: "number works: prices went to zero for a week, then to whatever people agreed on. the meetings are very long. bread costs 2." },
      chromegristle: { any: "chrome gristle: still night, still raining. bev runs a free clinic. upsell runs an honest one, out of necessity." },
      evergreen: { any: "evergreen acres: the mannequins stopped waving at once. linda planted vegetables on her lawn. the hoa voted on it. it passed." },
      lates: { any: "the lates: wednesday. pauline cried at the date on her monitor. then she went outside." },
      margins: { vacancy: "the margins: vacancy collapsed. penny plot is selling car roofs on the commute.", marginwalkers: "the margins: the gnome line holds. children help paint the names." },
      corphill: { any: "corp hill: dark. the spire's windows are black. people climb dividend road at night to look at the stars." },
      commute: { any: "the commute: employee of the month gave the award to someone else for the first time. it was todd. they sit on the bus roof. neither of them knows what to say." },
    },
    postgame: "the city is dark: no clocks in the HUD (the district clock reads --:--), Corp Hill is unlit and lootable, the rot spreads faster everywhere nobody holds it, Late Fees are gone, warlords fight for the gaps.",
  },

  off_books: {
    needs: "pages>=6",
    scenes: ["e3_off_books", "credits_drive"],
    panels: [
      { if: "drift>=4", text: "you walked out with a backup you'll never restore. you're not sure there's much of rory left in it. that's all right. you're not sure there was much of rory in you either. you're someone. that'll do." },
      { if: "drift<2", text: "out on the commute, past the last digit, you find you can remember the whole of the last workday, and the morning before it, and mina's ninth birthday. you were late for that too. she forgave you then as well." },
      { if: "flag:overtime_clocked_out", text: "the bottom found an old man in a suit on its stairs. he asked the kids what day it was. they said wednesday. he seemed pleased." },
      { if: "!flag:overtime_clocked_out", text: "edwin sallow's backup went into the free sims. he works a normal day and goes home at 17:30 to a house june was never recorded in. some people think that's kind. dale doesn't." },
      { if: "flag:forgave_auntie", text: "auntie's notebook was published after option c. the last entry: 'forgiven. 1 entry.'" },
      { text: "a cold peace, with the people who ended the world still standing. but they're standing at a table now, and they're not the only ones at it." },
    ],
    districts: {
      bottom: { any: "the bottom: its sale is void. it's still at the bottom of the hill. it's started building up." },
      gut: { gristle: "the gut: page four bankrupted gristle & sons. the bishop kept the choir and lost the company.", bottom: "the gut: the bottom's. sister agenda's minutes were published with option c. they're the only list of names." },
      pinstripe: { family: "pinstripe: page one voided every policy. the family bargains at the table. nonna wins more than anyone.", punchlines: "pinstripe: pip takes a seat at the table in full makeup. nobody can tell when pip's joking. that's the point." },
      checkout: { bigvalue: "the checkout: gail read page two over the pa at 09:00, herself. then she unlocked the doors and left them open.", mallrats: "the checkout: page two is read out at the welded doors every morning at 09:00. wristband stands where he stood when he was five." },
      numberworks: { remainder: "number works: page three is printed on every price tag in the city. mr. sevens' 17:10 log was published. nobody shakes his hand.", remainders: "number works: the union's seat at the table is a stool marked 13. nell stands." },
      chromegristle: { any: "chrome gristle: the patent is public. every meat mechanic copies upsell's procedures for free. he's furious. bev gets her hands back." },
      evergreen: { any: "evergreen acres: the pilot is published. property values crash. the hoa holds a vote on whether the apocalypse happened. it passes, narrowly." },
      lates: { any: "the lates: wednesday. pauline audits the restoration's books for free, as a hobby. she finds everything." },
      margins: { vacancy: "the margins: page five voids every sale. penny plot's commission is zero. she takes it surprisingly well.", marginwalkers: "the margins: old pat plants a gnome for every plot given back. she runs out of gnomes. the bottom makes more." },
      corphill: { any: "corp hill: still lit, on a smaller schedule, for the people who live there. hask reads her ledger at the table. it takes four days." },
      commute: { any: "the commute: 'unpaid, inc.' won a contract at the table. it's paid. employee of the month framed the first payslip." },
    },
    postgame: "the city is at dawn: Late Fees are abolished (☺ CORP has no claim), shops are cheaper, the free sims are a new place in the Machine menu where the bots won't fight unless they want to, the companies and groups hold the turf you gave them.",
  },

  nap_time: {
    needs: "cats>=12",
    scenes: ["e4_nap_time"],
    panels: [
      { text: "everyone in the city is asleep. legally." },
      { text: "this didn't happen. the credits said so. (it unlocks the BOARD MEMBER outfit and lets you choose again.)" },
    ],
    districts: {},
    postgame: "non-canon: after the credits the game returns to C24 and you choose again. The NAP TIME unlock and the outfit stay on the save.",
  },
};
