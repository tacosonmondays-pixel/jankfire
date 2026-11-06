// OVERDUE side questlines: THE CHECKOUT. Schema: see side/bottom.js.
// The Stampede is never a joke: the Forever Shoppers' sale is goofy; the dead outside the doors are not.

export const SIDE_CHECKOUT = {
  sq_checkout_mall_walker: {
    kind: "side", from: 2, title: "MALL WALKER", giver: null, district: "checkout",
    locations: ["checkout:queue", "checkout:food_court", "checkout:escalator"], cast: [],
    requires: { missions: ["m10_doorbusters"], if: null },
    logline: "Race the Mall Walkers' club: twelve terrifyingly fast grandmothers in matching tracksuits who have walked the mall's loop every morning since the Stampede.",
    twist: "They walk to remember: every lap passes the Big Doors, and on every lap the club leader, Dorothea, touches the glass. After you beat them (it takes three races), she invites you to walk a lap with them, slowly, and tells you the names they say at the doors.",
    beats: ["Race 1: the food court loop (no running: walking only; the HUD fines you if your feet leave the floor).", "Race 2: the escalators (walk up the down one).", "Race 3: the whole Infinite Queue (14 laps of the district).", "A slow lap."],
    steps: [
      { id: "r1", text: "beat the mall walkers (food court)", goal: { type: "reach", zone: "checkout:food_court" }, timer: 120 },
      { id: "r2", text: "beat the mall walkers (escalators)", goal: { type: "reach", zone: "checkout:escalator" }, timer: 150 },
      { id: "r3", text: "beat the mall walkers (the infinite queue)", goal: { type: "reach", zone: "checkout:queue" }, timer: 600 },
      { id: "lap", text: "walk a lap with them", goal: { type: "reach", zone: "checkout:doors" }, talk: "lap" },
    ],
    talks: {
      lap: { with: "shopper", nodes: { start: { say: [["shopper", "*Dorothea, eighty-two, tracksuit, walking slowly beside you. At the Big Doors she puts her hand on the glass.*"], ["shopper", "we do the names. one a lap. we've done every name we know about four hundred times."], ["shopper", "today's is arthur. he was my brother. he wasn't a member."], ["shopper", "*she takes her hand off the glass and walks on, fast again.* keep up, love."]], do: ["flag:walked_with_walkers"] } } },
    },
    choices: [],
    reward: { coupons: 500, loot: ["lt_district_checkout"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you kept up.", meets: "MEETS EXPECTATIONS. you nearly kept up.", see_me: "SEE ME. you ran." },
  },

  sq_checkout_price_check: {
    kind: "side", from: 2, title: "PRICE CHECK ON AISLE EVERYTHING", giver: "gail", district: "checkout",
    locations: ["checkout:queue", "checkout:returns", "checkout:vents"], cast: ["gail"],
    requires: { missions: ["m10_doorbusters"], if: null },
    logline: "Gail needs a price check. Scan 30 hidden barcodes across the Checkout with the Instant Camera.",
    twist: "The barcodes are on things no shop would sell: a fountain, a dead escalator, a rat (a live one, very offended), a tree, a Forever Shopper, you. The 30th is on the inside of the PA booth's door, and when you scan it, it comes up as GAIL PRENTICE · ASSISTANT MANAGER · PRICE: 17:31. She's been waiting for someone to scan her for sixty-one years.",
    beats: ["Gail on the PA: 'price check on aisle everything.'", "30 barcodes hidden around the dome, vents, escalators and the queue (photo goal).", "The last one."],
    steps: [
      { id: "scan", text: "scan 30 hidden barcodes", goal: { type: "photo", target: "checkout:queue", subject: "barcode", n: 30 } },
      { id: "gail", text: "", goal: { type: "talk", who: "gail", talk: "scanned" }, marker: "checkout:pa_booth" },
    ],
    talks: {
      scanned: { with: "gail", nodes: { start: { say: ["*off-mic* oh. oh, you scanned me.", "price: 17:31. that's about right. that's what i cost.", "*on-mic, to the whole mall* attention shoppers. price check complete. all items have been accounted for.", "*off-mic* thank you, love."] } } },
    },
    choices: [],
    reward: { coupons: 600, standing: { bottom: 1 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. 30/30.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you scanned the rat twice. it remembers." },
  },

  sq_checkout_the_names: {
    kind: "side", from: 2, title: "THE NAMES", giver: "wristband", district: "checkout",
    locations: ["checkout:vents", "checkout:doors", "checkout:returns"], cast: ["wristband", "mina"],
    requires: { missions: ["m11_no_refunds"], if: null },
    logline: "The Mall Rats have spent sixty-one years collecting the names of the people who died outside the Big Doors. They have 3,211. They know there are more.",
    twist: "Big Value has the list. It always had it: a membership-scan log from 17:30 to 17:34 of every card that was refused at the door. It's in Returns Desk Zero, the only returns desk that's never taken a return, filed as 'declined transactions'. With it, the Mall Rats can finish the wall. If the Mall Rats run the Checkout, they paint the names on the welded doors; if Big Value does, Gail reads them on the PA, one a day, for as long as it takes.",
    beats: ["The vent classroom's wall of names, in chalk.", "Wristband: there are gaps. People who weren't known.", "Break into Returns Desk Zero (stealth: Mall Security, then a vault of unreturned items).", "The log.", "If Mina is free, she reads the log with Milo, in the vents, holding his hand."],
    steps: [
      { id: "wall", text: "talk to wristband", goal: { type: "talk", who: "wristband", talk: "gaps" }, marker: "checkout:vents" },
      { id: "desk", text: "get into returns desk zero", goal: { type: "reach", zone: "checkout:returns" } },
      { id: "log", text: "find the declined transactions", goal: { type: "pickup", item: "declined_log" } },
      { id: "back", text: "bring the log to the vents", goal: { type: "deliver", item: "declined_log", zone: "checkout:vents" }, talk: "complete" },
    ],
    talks: {
      gaps: { with: "wristband", cam: "closeup", nodes: { start: { say: ["*A classroom in the vents. One wall is names, in chalk, floor to ceiling, in a hundred handwritings.*", "three thousand two hundred and eleven. we've found them from letters, from families, from people who were there.", "there are more. people nobody came looking for. people who were alone.", "big value knew who it turned away. it had a list. it always had a list. that's what a membership is."] } } },
      complete: { with: "wristband", nodes: { start: { say: ["*Wristband turns the log's pages very slowly.*", "eight thousand and forty.", "*he doesn't cry. He gets a piece of chalk and starts at the next empty brick.*", ["mina", "*if she's free, sitting beside him with the second piece of chalk* i'll do the other side, milo."]], do: ["flag:names_complete"] } } },
    },
    choices: [],
    reward: { coupons: 0, standing: { bottom: 8 } },
    grade: { exceeds: "", meets: "", see_me: "" },
    notes: "no performance-review card and no coupons: the Mall Rats offer, you can refuse; the game doesn't make a reward of this.",
  },

  sq_checkout_returns_desk_zero: {
    kind: "side", from: 2, title: "RETURNS DESK ZERO", giver: null, district: "checkout",
    locations: ["checkout:returns"], cast: ["cart_mother"],
    requires: { missions: ["m11_no_refunds"], if: null },
    logline: "Returns Desk Zero has never accepted a return. A sign says so. A clerk-bot has been waiting behind it since the Stampede for its first customer.",
    twist: "The first thing it will accept is Brenda's receipt. Brenda (the Cart Mother, beaten) has to bring it herself. She does, if you help her through the mall on a trolley. The clerk-bot scans it and says the only thing it has ever been programmed to say: 'refund approved.' It hands her a single bottle of water. She sits down on the floor and drinks it.",
    beats: ["The desk, the bot, the sign: RETURNS DESK ZERO · NO RETURNS SINCE 17:31.", "Find Brenda (she's in the Cart Corral since her defeat, if not dismantled).", "Wheel her to the desk on a trolley through a sale stampede.", "The refund."],
    steps: [
      { id: "desk", text: "visit returns desk zero", goal: { type: "reach", zone: "checkout:returns" } },
      { id: "brenda", text: "bring brenda", goal: { type: "escort", who: "cart_mother", zone: "checkout:returns" } },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 200, flags: ["brenda_refunded"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. refund approved.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you tried to return yourself." },
  },
};
