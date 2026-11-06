// OVERDUE side questlines: THE GUT. Schema: see side/bottom.js.

export const SIDE_GUT = {
  sq_gut_choir_practice: {
    kind: "side", from: 1, title: "CHOIR PRACTICE", giver: "sister_agenda", district: "gut",
    locations: ["gut:choir_lung", "gut:campus", "lates:waiting_room"], cast: ["sister_agenda", "bishop"],
    requires: { missions: ["m03_somethings_digesting"], if: null },
    logline: "The Choir needs a tenor. Collect three voice boxes from overdue ☺ CORP offices.",
    mechanic: { uses: ["grapple", "nvg"], hook: "three overdue offices with grapple-only entrances; the Lates call centre is dark" },
    twist: "Sister Agenda doesn't want a tenor. She wants her own voice back: the Bishop made every singer sing on his note, and a voice box from outside the Gut is the only thing that can sing off it. The first time she uses it, she sings a single line of her own, out of tune, and the whole Choir stops to listen.",
    beats: ["Three overdue offices: a Gristle & Sons campus annexe grown shut, a Lates call centre, a Corp Hill switchboard room (Late Fees).", "Each voice box is in a dead switchboard operator's headset; each office has a short, odd encounter (a phone that keeps ringing; a hold queue of 4,000 callers; a recorded voice that still says 'your call is important').", "Bring them to Sister Agenda. She keeps one."],
    steps: [
      { id: "ask", text: "talk to sister agenda", goal: { type: "talk", who: "sister_agenda", talk: "tenor" }, marker: "gut:choir_lung" },
      { id: "boxes", text: "collect 3 voice boxes from overdue offices", goal: { type: "pickup", item: "voice_box" }, notes: "gut:campus, lates:waiting_room, a Corp Hill switchboard" },
      { id: "give", text: "bring them to the choir", goal: { type: "talk", who: "sister_agenda", talk: "own_voice" } },
    ],
    talks: {
      tenor: { with: "sister_agenda", nodes: { start: { say: ["*sung* we need a tenor, a tenor, a tenor... *not sung* we don't. sorry. that's what i'm supposed to say.", "bring me voice boxes. from the old offices up the hill, the ones that went overdue. three. i'll explain when you're back. if i explain now he'll hear."] } } },
      own_voice: { with: "sister_agenda", cam: "closeup", nodes: { start: { say: ["*She holds one voice box against her throat. She takes a breath. The Choir Lung breathes with her.*", "*she sings, off his note, a single line, badly:* my name is felicity marsh and i was in accounts.", "*The Choir stops. Every stretched face turns to her. Far below, the Bishop's baton stops in the air.*", "*not sung, shaking* ...thank you. that's the first thing i've said for myself in sixty-one years."], do: ["flag:agenda_own_voice"] } } },
    },
    choices: [],
    reward: { coupons: 400, flags: ["choir_practice_done"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. perfectly out of tune.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you put a voice box on hold." },
  },

  sq_gut_reflux: {
    kind: "side", from: 1, title: "REFLUX", giver: "bev", district: "gut",
    locations: ["gut:big_stomach", "gut:border"], cast: ["bev"],
    requires: { missions: ["m03_somethings_digesting"], if: null },
    logline: "The acid lake in the Big Stomach is rising. Plug the burping vents with cars before it reaches Bev's clinic.",
    mechanic: { uses: ["cars"], hook: "a driving puzzle: plug six acid vents with cars before the lake rises" },
    twist: "It's rising because something's been feeding it: the Unpaid have been dumping stolen ☺ CORP paperwork into it, and the Gut can't digest forms. The last vent is plugged with a filing cabinet full of Late Fees notices addressed to the Bottom. Bev reads one and laughs until she has to sit down.",
    beats: ["Six vents round the crater, burping acid on a rhythm.", "Drive cars into them (meat buggies work best: they bleed instead of smoking).", "The last vent: a filing cabinet. Late Fees notices."],
    steps: [
      { id: "ask", text: "talk to bev", goal: { type: "talk", who: "bev", talk: "acid" }, marker: "gut:border" },
      { id: "plug", text: "plug 6 vents with cars", goal: { type: "interact", target: "gut:big_stomach" }, timer: 360, notes: "a timed driving puzzle; the lake level is the timer" },
      { id: "cabinet", text: "", goal: { type: "talk", who: "bev", talk: "notices" } },
    ],
    talks: {
      acid: { with: "bev", nodes: { start: { say: ["the lake's coming up. it gets to my clinic, i lose my chairs. i lose my chairs, i lose my patients. well. the patients go in the lake.", "plug the vents. with cars. it's the only thing it won't eat. it's tried."] } } },
      notices: { with: "bev", nodes: { start: { say: ["*Bev with a handful of soggy Late Fees notices.* 'final notice: the bottom: 244 quarters'. 'final final notice'. 'final final final notice: we mean it'.", "*she laughs until she has to sit down on a stomach-dog, which doesn't mind* the gut's choking on corp's bills. even the gut won't swallow them."] } } },
    },
    choices: [],
    reward: { coupons: 450, loot: ["lt_district_gut"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. no chairs lost.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you drove into the lake." },
  },

  sq_gut_hairball: {
    kind: "side", from: 1, title: "HAIRBALL", giver: "dot", district: "gut",
    locations: ["gut:peristalsis", "gut:digester_wall"], cast: ["dot"],
    requires: { missions: ["m03_somethings_digesting"], if: null },
    logline: "Something's stuck in Peristalsis Avenue and the whole street is backed up. It's a guy's whole house.",
    mechanic: { uses: ["wrecking_ball", "duck", "knockback"], hook: "push a whole house down an intestine: knockback works, the wrecking ball works best" },
    twist: "The house's owner is still in it, making tea. He's been travelling down the Gut's digestive tract in his house for nine years and thinks it's a very slow train. When you push the house through, he arrives at the Big Stomach, looks out of the window, and says 'oh. this isn't leeds.'",
    beats: ["Dot mentions the street's been 'a bit blocked'.", "A whole terraced house wedged in the intestine-tube avenue.", "Push it with a car, a lasso, the Shopping Cart Cannon, rockets (all work; the funniest is the sofa-car).", "The man inside offers you tea throughout."],
    steps: [
      { id: "dot", text: "", goal: { type: "talk", who: "dot", talk: "blocked" }, marker: "gut:digester_wall" },
      { id: "push", text: "unblock peristalsis avenue", goal: { type: "reach", zone: "gut:peristalsis" }, notes: "a physics push: anything with knockback moves it; the peristalsis beat helps if you push on it" },
    ],
    talks: {
      blocked: { with: "dot", nodes: { start: { say: ["the avenue's been ever so blocked. you can feel it in the wall. like when you've had too much bread.", "there's a house in it. with a man in it. he waves. nice man. offers everyone tea. nobody's ever been able to take him up on it."] } } },
    },
    choices: [],
    reward: { coupons: 350, items: [], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you had the tea.", meets: "MEETS EXPECTATIONS. it's moving.", see_me: "SEE ME. you're in the house now." },
  },

  sq_gut_quarterly_growth: {
    kind: "side", from: 2, title: "QUARTERLY GROWTH", giver: "bishop", district: "gut",
    locations: ["gut:feed_dock", "gut:campus", "bottom:long_stairs"], cast: ["bishop", "sister_agenda", "lumps"],
    requires: { missions: ["m06_option_c"], if: null },
    logline: "Gristle & Sons wants the Gut to hit its growth target this quarter. Feed it, or sabotage the feeding tubes.",
    mechanic: { uses: ["cars", "frag_smoke"], hook: "escort or blow up Regrowth tankers" },
    twist: "The 'feed' isn't people this time: it's the Gut's own regrowth tubes, pumping Regrowth toward the Long Stairs. Hitting the target means the Gut grows into the Bottom's top terraces. Sabotaging it means the Choir loses a quarter's bonus, and the Bishop makes Sister Agenda write it down as her fault.",
    beats: ["The Bishop himself offers you a contract: 2,000 coupons to escort feeding tankers.", "Sister Agenda, quietly: the tankers go to the Long Stairs.", "Escort them (the Gut spreads) or blow the tubes (the Gut stays put; Agenda takes the blame unless you go back and speak for her)."],
    steps: [
      { id: "offer", text: "hear the bishop's offer", goal: { type: "talk", who: "bishop", talk: "growth" }, marker: "gut:campus" },
      { id: "choice", text: "the tankers", goal: { type: "flag", flag: "growth_choice_made" } },
    ],
    talks: {
      growth: { with: "bishop", cam: "lowAngle", nodes: { start: { say: ["*The Bishop, out of his lake, kindly, enormous.* growth is a prayer. this quarter, we are a little short of answered.", "escort my tankers to the edge of the long stairs. two thousand coupons. and the gratitude of the body.", ["sister_agenda", "*sung, very low, behind him* the stairs, the stairs, the top terrace..."]] } } },
    },
    choices: [
      { id: "growth", prompt: "The tankers are full of Regrowth, headed for the Bottom's top terraces.", options: [
        { id: "feed", label: "escort the tankers", do: ["flag:growth_choice_made", "flag:gut_grew", "coupons:+2000", "standing.bottom:-5"], consequence: "The Gut hits its target. The Bottom's top terrace grows skin over the next act: warm walls, a pulse in the stairs. People move down a terrace. In Act III the Bishop is stronger (+10% HP). In LATE the green on the Long Stairs grows slower." },
        { id: "sabotage", label: "blow the feeding tubes", do: ["flag:growth_choice_made", "flag:gut_starved", "standing.bottom:+5"], consequence: "The Gut misses its target. The Bottom stays pastel. Sister Agenda is blamed in the minutes; go back and tell the Bishop it was you (a short talk) and she keeps her desk. If you don't, she's moved to the deep wall, and you find her there in m20." },
      ] },
    ],
    reward: { coupons: 300, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you fed the tankers to the lake." },
  },

  sq_gut_belly_button: {
    kind: "side", from: 3, title: "BELLY BUTTON", giver: null, district: "gut",
    locations: ["gut:big_stomach", "gut:belly_button"], cast: ["gristle_senior", "bishop"],
    requires: { missions: ["m20_the_missing"], if: null },
    logline: "There's a door at the bottom of the Big Stomach. Don't press it.",
    mechanic: { uses: ["scythe", "verdict", "grapple", "nailgun"], hook: "the arm storm: grapple-run up the frozen arms, nail them to the vault, judge him guilty" },
    twist: "You press it. Behind it is the founding partner of Gristle & Sons, Augustus Gristle, grown into the district's oldest organ, still holding pens. The Bishop sings to him every night. Augustus wants one more contract, and someone to tell his son the truth.",
    beats: ["Signs everywhere around the crater floor, in every hand: DON'T PRESS IT. PLEASE DON'T. IT'S NOT A BUTTON. (It is a button.)", "Drain the lake (side effect of sq_gut_reflux, or after m20) and walk down to it.", "Press it.", "Secret boss: THE FOUNDING PARTNER.", "He signs your arm and asks you to tell his son it was a failure. Optional: tell the Bishop."],
    steps: [
      { id: "door", text: "don't press it", goal: { type: "interact", target: "gut:belly_button" }, notes: "the objective text is 'don't press it' and pressing it completes it" },
      { id: "boss", text: "", goal: { type: "killBoss", boss: "founding_partner" }, boss: "founding_partner" },
      { id: "tell", text: "tell the bishop (optional)", goal: { type: "talk", who: "bishop", talk: "failure" } },
    ],
    talks: {
      failure: { with: "bishop", cam: "closeup", nodes: { start: { say: ["*The Bishop, in the Choir Lung, conducting. You tell him what his father said.*", "*His baton stops. His smile, for the first time, gets smaller.*", "a failure.", "he said that? he... he said that to you?", "*a long silence. The Choir watches him.*", "*very quietly* then we've been singing to the wrong thing. haven't we."], opts: [["sing something else.", "else"]] },
        else: { say: ["*He lifts the baton. He doesn't know what to conduct. Sister Agenda, at her desk, starts a single out-of-tune line, and the Choir follows her instead.*"], do: ["flag:choir_new_song"] } } },
    },
    choices: [],
    reward: { coupons: 1000, loot: ["lt_boss_founding_partner"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you pressed it.", meets: "MEETS EXPECTATIONS. you pressed it.", see_me: "SEE ME. you pressed it. we said don't." },
  },
};
