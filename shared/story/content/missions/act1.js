// OVERDUE main missions, Act I: "Please Take Your Item" (The Bottom, The Gut). The act's question: what am I?
//
// SCHEMA: MISSIONS[id] = {
//   act, n (main-story order), title (ALL CAPS card), kind: 'main' | 'flashback'
//   giver       cast id who starts it (or null)
//   district    where it mostly happens (world.js DISTRICTS)
//   locations   LOCATIONS ids used (markers, scenes)
//   cast        cast ids who appear
//   requires    { missions: [ids], if: condition string or null }
//   logline     one sentence
//   beats       the story beats in order (plain prose, for the writer and the builder)
//   reveals     { learn: [...], suspect: [...], withheld: [...] }  the mystery, bit by bit
//   steps       [{ id, text (HUD objective, lowercase), goal: { type, ...params }, marker?, talk?, scene?, boss?, timer?, fail?, do?, if? }]
//               goal types (TECH_PLAN §6): reach{zone} pickup{item} deliver{item,zone} kill{who,n} killBoss{boss} talk{who,talk}
//               enterCar{} survive{secs} escort{who,zone} photo{target} interact{target} loseFees{} flag{flag}
//               fail: { type: 'flag', flag } or { type: 'death', who } or { type: 'timer' }
//   talks       { talkId: { with: castId, cam?, nodes: { nodeId: node } } }, the dialogue trees. A node is:
//               { who?, say: [line...], opts?: [[text, nextNode, { if?, do? }?]...], do?: [actions], next?: nodeId, cam? }
//               branch?: [[condition | null, nodeId]...]  (no player pick: the first true condition wins, null = default;
//               runs after say/do, instead of opts/next)
//               a line is a string (spoken by node.who or the talk's `with`) or [speaker, text]. "*...*" is a stage direction.
//               No opts and no next = the talk ends. `end` is not special here (unlike secrets.js).
//   choices     [{ id, prompt, options: [{ id, label, if?, do: [actions], consequence (prose) }] }]  the big decisions
//   scenes      SCENES ids that play in this mission, in order
//   startScene  optional: null = no scene plays on the mission card (default: the first of `scenes` does)
//   reward      { coupons?, items?: [itemIds], loot?: [lootTableIds], flags?: [flags], standing?: { corp?, bottom? }, implants?: [ids] }
//   grade       { exceeds, meets, see_me }  the performance-review end card lines (DESIGN §8.4)
//   notes       builder notes (optional)
// }

export const MISSIONS_ACT1 = {
  // ------------------------------------------------------------------ 1
  m01_return_to_sender: {
    act: 1, n: 1, title: "PLEASE TAKE YOUR ITEM", kind: "main", giver: null, district: "bottom",
    locations: ["sims:suburb", "bottom:machine", "bottom:lostfound", "bottom:rooftops", "bottom:school", "bottom:down_escalator"],
    cast: ["change", "dale", "auntie", "lumps", "gordo", "dumpling", "pallet_jack"],
    requires: { missions: [], if: null },
    logline: "You win a training sim, the camera pulls out through the Machine's glass, and for the first time in sixty-one years the Machine gives something back: you.",
    mechanic: { uses: ["grapple", "washing_lines", "bhop"], hook: "the tutorial is a grapple lesson in disguise: Dumpling's tour is swing onto the Wok Roofs, ride a washing line back, and land somewhere Dumpling can score out of ten" },
    beats: [
      "A normal-looking PvP match on the Suburb map. The player wins. TRAINING COMPLETE. The bots stand and stare.",
      "C1: the pull-back through the glass, up the hill to the Spire and back down. Dale presses the button. You drop into the tray.",
      "First words with Dale and Auntie. Auntie sees the barcode on your neck and drops her crayon; she covers it.",
      "Pallet Jack carries the Machine's tray, with you in it, up the down escalator. First line of his you hear: the weight.",
      "Lumps and Wee Gordo arrive. Gordo scans the barcode with a stolen ☺ CORP scanner: NO RECORD. He doesn't trust you. Lumps does.",
      "The Bottom names you CHANGE.",
      "Tutorial with Dumpling: grab a weapon from the Lost Property bins, shoot a dead vending machine for loot, grapple onto the Wok Roofs (scored out of ten) and ride a washing line back.",
      "Dinner. Auntie tells you how the world ended (P1b). You go to sleep in a box marked RETURNS.",
    ],
    reveals: {
      learn: ["You were inside the Machine, in a training sim. The sims are the world before the end.", "The world ended sixty-one years ago in a war the companies fought, ending in something called Option C at 17:30.", "You're a mannequin. Your barcode has no record."],
      suspect: ["Auntie knows something about you (the crayon).", "Dale has been waiting a long time to press that button."],
      withheld: ["Who you were.", "Why the barcode has no record.", "What Option C actually says."],
    },
    steps: [
      { id: "sim", text: "win the match", goal: { type: "flag", flag: "sim_won" }, marker: "sims:suburb", notes: "a Training-style local bots match on Suburb, the real multiplayer HUD; any kill count wins; the last kill triggers C1" },
      { id: "c1", text: "", goal: { type: "flag", flag: "seen_c1" }, scene: "c1_please_take_your_item" },
      { id: "tray", text: "take your item", goal: { type: "interact", target: "bottom:machine" }, marker: "bottom:machine" },
      { id: "first", text: "talk to the old man", goal: { type: "talk", who: "dale", talk: "first_words" } },
      { id: "name", text: "", goal: { type: "talk", who: "gordo", talk: "barcode" } },
      { id: "bins", text: "grab something from the lost property bins", goal: { type: "pickup", item: "lost_property_weapon" }, marker: "bottom:lostfound", talk: "dumpling_tour" },
      { id: "vend", text: "shoot the dead vending machine", goal: { type: "interact", target: "bottom:lostfound" }, notes: "the tutorial loot drop: guaranteed rare" },
      { id: "swing", text: "grapple onto the wok roofs (dumpling is scoring you)", goal: { type: "reach", zone: "bottom:rooftops" }, talk: "dumpling_score", notes: "teaches the grapple: swing, let go on the upswing, land; Dumpling scores the landing out of ten" },
      { id: "line", text: "ride a washing line back to the lost & found", goal: { type: "reach", zone: "bottom:lostfound" }, notes: "teaches the washing-line ziplines" },
      { id: "dinner", text: "dinner at the lost & found", goal: { type: "talk", who: "auntie", talk: "dinner" }, marker: "bottom:lostfound" },
      { id: "sleep", text: "sleep", goal: { type: "interact", target: "bottom:lostfound" }, do: ["flag:act1_started"] },
    ],
    talks: {
      first_words: {
        with: "dale", cam: "overShoulder",
        nodes: {
          start: { say: ["*Dale crouches by the tray. Up close he's older than the button.*", "...easy. easy. you're out. you're in the depot. nobody's going to hurt you.", ["auntie", "can it hear you?"], "she can hear everything. this one can probably hear."], opts: [["where am i?", "where"], ["who are you?", "who"], ["*try to stand up*", "stand"]] },
          where: { say: ["the lost & found. the bottom of the hill. ...the bottom of everything, really.", "you were in her. the machine. in a match. you kept walking off the map."], opts: [["it felt real.", "real"], ["who are you?", "who"]] },
          real: { say: ["it's a recording. a good one. the world as it was. ...you don't know yet. agnes, you tell it. you're better at this."], next: "auntie" },
          who: { say: ["dale. i fix her. i've been fixing her since... a long time.", "and that's agnes. don't call her that, she'll make you count something."], next: "auntie" },
          stand: { say: ["*your knee bends the wrong way. You go down. Dale catches your elbow.*", "yeah. they all do that. returned stock."], next: "auntie" },
          auntie: { who: "auntie", say: ["*She steps into the light with the torch and looks at you properly for the first time. She looks at your face. Then at the back of your neck.*", "*Her crayon falls out of her hand and rolls under the Machine. She doesn't pick it up.*", "...right. well. you'll be hungry. everyone's hungry.", ["dale", "it's plastic, agnes."], "everyone's hungry, dale."], opts: [["what am i?", "what"], ["i'm not hungry.", "nothungry"], ["why are you looking at my neck?", "neck"]] },
          what: { who: "auntie", say: ["you're the first thing that machine has ever given anybody. which makes you very valuable or very lost.", "the bottom's good with lost. come on."], do: ["flag:met_auntie", "flag:met_dale"] },
          nothungry: { who: "auntie", say: ["you will be. it's a habit. bodies remember things.", "...come on."], do: ["flag:met_auntie", "flag:met_dale"] },
          neck: { who: "auntie", say: ["*a pause slightly too long*", "you've got a barcode. i used to work somewhere that had barcodes. old habits.", "come on. before lumps finds you. he'll want to hug you and you're not built for it."], do: ["flag:met_auntie", "flag:met_dale", "flag:asked_auntie_neck"] },
        },
      },
      barcode: {
        with: "gordo", cam: "closeup",
        nodes: {
          start: { say: ["*Pallet Jack carries the Machine's tray, with you in it, up the down escalator.*", ["pallet_jack", "you're about forty kilos, light one. lightest friend i've got."], ["lumps", "*filling the doorway* is that it? is that the thing?"], ["lumps", "hello. i'm lumps. sorry. *he hugs you. Something in your shoulder pops back in.* sorry."], "move, ambrose.", "*Wee Gordo pushes past him with a chunky ☺ CORP barcode scanner held together with tape. He doesn't ask. He scans the back of your neck.*", "*BEEP.* NO RECORD.", "*BEEP.* NO RECORD.", "a ☺ corp product with a ☺ corp barcode that ☺ corp doesn't have a record of. that's either a miracle or a trap. and i don't believe in miracles."], opts: [["i don't know what i am either.", "honest"], ["you scan everyone like that?", "everyone"], ["*say nothing*", "silent"]] },
          honest: { say: ["*He looks at you for a long time.*", "...ok. that's the first honest thing anyone's said in this depot all week.", "i'm still checking your pockets."], next: "naming", do: ["standing.bottom:+2"] },
          everyone: { say: ["only the ones that fall out of corp machines.", ["lumps", "he scanned me once. i'm a tin of beans."], ["lumps", "...i was holding a tin of beans."]], next: "naming" },
          silent: { say: ["great. a quiet one. the quiet ones are the ones that report you.", ["lumps", "gordo."], "fine. fine."], next: "naming" },
          naming: { say: [["auntie", "it needs a name. we can't call it 'it'. it's rude and it's confusing."], ["lumps", "steve."], "no.", ["dumpling", "*from somewhere under a table* GHOST."], ["dale", "*from the Machine, without looking round* change."], ["auntie", "dale?"], ["dale", "sixty-one years. she never gave anybody their change. then she gave them."], ["auntie", "...change. right. welcome to the bottom, change."]], do: ["flag:named_change"] },
        },
      },
      dumpling_tour: {
        with: "dumpling", cam: "overShoulder",
        nodes: {
          start: { say: ["ghost! ghost! auntie says i'm doing the tour because i'm the most annoying. that's a job.", "this is the lost property. everything anybody ever lost. there's a whole bus out the back. take something. something that shoots."], opts: [["what do you shoot out here?", "shoot"], ["is any of this yours?", "yours"]] },
          shoot: { say: ["raiders. corp. dogs from the gut. not the nice dogs. the stomach ones.", "and the machines. the old vending machines. if you shoot them they give you stuff. dale says don't. dale does it every day."] },
          yours: { say: ["my dad's hat's in there. he's not lost. he's at work. he'll come and get it.", "*Dumpling's ears go flat for a second, then pop up.* come ON."] },
        },
      },
      dumpling_score: {
        with: "dumpling", cam: "wide",
        nodes: {
          start: { say: ["grapple the wok on that roof. no, the wok. the WOK. the round thing.", "let go when you're going up, not when you're going down. going down is how mr. abara broke his everything.", "*you land, roughly, on a roof covered in woks*", "...four out of ten. you swung like a fridge. lumps swings like a fridge and he IS a fridge."], opts: [["let me go again.", "again"], ["four?", "four"]] },
          again: { say: ["you can't go again. it's a tour. tours go forwards. ride the washing line back. don't drop a sock."] },
          four: { say: ["four's good. i gave dale a one. he grappled a pigeon."] },
        },
      },
      dinner: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*A long table in the depot. Soup in mismatched bowls. Lumps eats four. Gordo reads a binder while he eats. Dale doesn't come; he never leaves the Machine at night.*", "eat. you're plastic. eat anyway. it's how we know you're one of us.", "*You eat. It goes somewhere. Nobody asks where.*"], opts: [["what happened to the world?", "world"], ["why do you keep the books in crayon?", "crayon"], ["what's the spire?", "spire"]] },
          world: { say: ["*She takes a crayon from behind her ear, opens her notebook to a page she's clearly drawn on many times, and turns it round.*"], do: ["scene:p1b_final_quarter"], next: "after" },
          crayon: { say: ["because ☺ corp owned every pen in the city. crayons were the kids'. nobody ever thought to sell those back to us.", "and because when you write in crayon, it's very hard to pretend you didn't write it."], opts: [["what happened to the world?", "world"], ["what's the spire?", "spire"]] },
          spire: { say: ["the top of the hill. ☺ corp. the only lit building for thirty years. they're still there. still on time.", ["gordo", "*without looking up* still sending us the bill."]], opts: [["what bill?", "bill"], ["what happened to the world?", "world"]] },
          bill: { say: ["back pay. for the time the world spent ending. two hundred and forty-four quarters of it.", "for a job none of us had. a job most of us weren't born for.", "it doesn't reconcile. nothing they send us reconciles."], opts: [["what happened to the world?", "world"]] },
          after: { say: ["*The panels fade. The soup's gone cold.*", ["lumps", "she tells it every time someone new comes. she cries at the dark bit."], "i do not.", ["lumps", "you do, nan."], "...go to bed, all of you. change, there's a box by the machine. it says returns. it's the nicest box we've got."], opts: [["auntie. did you know me?", "knew", { if: "flag:asked_auntie_neck" }], ["goodnight.", "night"]] },
          knew: { say: ["*She looks at the soup.*", "i've known a lot of people, change. i'm eighty-five. go to sleep."], do: ["flag:auntie_dodged"] },
          night: { say: ["goodnight. *quietly, when she thinks you've gone* ...goodnight."] },
        },
      },
    },
    choices: [],
    scenes: ["c1_please_take_your_item", "p1b_final_quarter"],
    reward: { coupons: 50, items: ["lost_property_weapon"], flags: ["met_lumps", "met_gordo"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you came out of a vending machine and ate soup. very adaptable.", meets: "MEETS EXPECTATIONS. returned in good condition.", see_me: "SEE ME. you fell off the washing line four times. dumpling is telling everyone." },
    notes: "the sim match should use the real multiplayer HUD so the cut out through the glass lands. Dale's terminal grabs a security still of the tray drop: that's the still Overtime has in P5b.",
  },

  // ------------------------------------------------------------------ 2
  m02_sauce_run: {
    act: 1, n: 2, title: "SAUCE RUN", kind: "main", giver: "sharon", district: "commute",
    locations: ["bottom:soup_kitchen", "commute:ring_road", "gut:border"],
    cast: ["sharon", "lumps", "gordo", "eotm", "pallet_jack"],
    requires: { missions: ["m01_return_to_sender"], if: null },
    logline: "The Bottom trades soup to Gristle & Sons for medicine. Steal a car, cross the edge of The Commute without spilling it, and survive the Unpaid.",
    mechanic: { uses: ["cars", "frag_smoke", "rocket_jump"], hook: "a slosh meter on the soup pot turns every jump, drift and car-roof landing into a decision; the interns' 'business cards' are frags" },
    beats: [
      "P2 briefing: Sharon, the pot; Lumps, the key; Gordo, 'he means steal a car'.",
      "Steal a car (any car; Lumps suggests the sofa-car, which belongs to Sharon's cousin, who is asleep on it).",
      "Pallet Jack lifts Sharon's pot into the car with one hand and tells Lumps his squat form is \"a bit sad\".",
      "Load the pot. Lumps rides shotgun holding it in his lap. Don't spill it: hard landings slosh it, and a full spill fails the delivery (but not the mission).",
      "In the car Lumps talks about the Gut, the trade and his mum, who is 'at work in the Gut'. He doesn't explain.",
      "The Unpaid ambush on the Ring Road: war-rigs made of desks. Employee of the Month robs you and offers you an internship.",
      "Deliver to the Gristle & Sons trade post at the Gut border. A Choir clerk counts the soup and hands over a crate of medicine.",
    ],
    reveals: {
      learn: ["The companies still run the city's districts. Gristle & Sons runs the Gut and trades medicine for soup.", "The Unpaid are interns' grandchildren who worship 'the First Intern'.", "Lumps' mum is in the Gut."],
      suspect: ["Why does Gristle & Sons want soup at all?"],
      withheld: ["What the soup is for (m20)."],
    },
    steps: [
      { id: "brief", text: "get the soup from sharon", goal: { type: "talk", who: "sharon", talk: "pot" }, marker: "bottom:soup_kitchen", scene: "p2_sauce_run" },
      { id: "car", text: "steal a car", goal: { type: "enterCar" } },
      { id: "pot", text: "load the soup pot", goal: { type: "pickup", item: "soup_pot" }, marker: "bottom:soup_kitchen" },
      { id: "drive", text: "drive the soup to the gut border (don't spill it)", goal: { type: "reach", zone: "commute:ring_road" }, talk: "car_ride", fail: { type: "flag", flag: "soup_spilled" } },
      { id: "ambush", text: "survive the unpaid", goal: { type: "survive", secs: 90 }, talk: "eotm_robbery" },
      { id: "deliver", text: "deliver the soup to the gristle & sons trade post", goal: { type: "deliver", item: "soup_pot", zone: "gut:border" }, marker: "gut:border", talk: "trade_post" },
    ],
    talks: {
      pot: {
        with: "sharon",
        nodes: {
          start: { say: ["you'll take the red pot and you'll not spill it.", "it's the tomato. gristle like the tomato. they pay double for the tomato.", ["lumps", "they pay in medicine."], "they pay in medicine. i didn't say it was a good double."], opts: [["why do they want soup?", "why"], ["i'll be careful.", "careful"]] },
          why: { say: ["*Sharon stirs the pot for a long second.*", "they've got a lot of mouths over there, love. don't ask me how many. go on."], do: ["flag:asked_sharon_soup"] },
          careful: { say: ["you'll be careful or you'll be ladled."] },
        },
      },
      car_ride: {
        with: "lumps", cam: "overShoulder",
        nodes: {
          start: { say: ["*Pallet Jack lifts Sharon's pot into the car with one hand and tells Lumps his squat form is \"a bit sad\".*", ["pallet_jack", "that pot's ninety. the soup's another sixty. the worry's free."], "*Lumps sits with the pot in his lap, both enormous forearms around it like a baby.*", "slower on the bumps. she's full to the top.", "*the car goes over a bump. A little soup jumps out. He catches it in his hand and puts it back.*", "...nobody saw that."], opts: [["what's the gut?", "gut"], ["why do you go there?", "why"], ["how did you get those arms?", "arms"]] },
          gut: { say: ["it's where they put the dead. after. millions of them. gristle and sons had this stuff, regrowth. made to bring soldiers back.", "it brought them back. just not as soldiers. as... a place.", "it's warm. it digests. you'll see. try not to touch the walls."], opts: [["why do you go there?", "why"]] },
          why: { say: ["sundays. i visit my mum.", "*he looks out of the window.*", "she's at work in the gut. two years. it's a long shift."], opts: [["what kind of work?", "work"], ["*leave it*", "leave"]] },
          work: { say: ["...the kind where you don't come home.", "*he holds the pot tighter.* watch the road. there's interns."], do: ["flag:lumps_mentioned_mum"] },
          leave: { say: ["*He nods, grateful.*", "watch the road. there's interns."], do: ["flag:lumps_mentioned_mum", "standing.bottom:+1"] },
          arms: { say: ["born with them. my mum's got them too. smaller.", "the doctors in chrome gristle said they'd buy them off me. i said they're my arms. they said not for long.", "i hit one. by accident. i said sorry."], opts: [["why do you go to the gut?", "why"]] },
        },
      },
      eotm_robbery: {
        with: "eotm", cam: "lowAngle",
        nodes: {
          start: { say: ["*War-rigs made of buses and forty office desks block the Ring Road. Interns in office-chair armour pile out. A huge man in filing-cabinet armour covered in plaques of his own face climbs on a car roof.*", "HALT. YOU ARE ENTERING A WORKSPACE.", "i am EMPLOYEE OF THE MONTH. every month. since the end of the world.", "you're robbed. also: would you like an internship? it's unpaid."], opts: [["what does the internship involve?", "intern"], ["you can have the coupons. not the soup.", "pay"], ["*draw a weapon*", "fight"]] },
          intern: { say: ["exposure. networking. a lanyard. a fun office culture. we're a family.", "you'd start in robbery and work your way up to also robbery.", ["lumps", "we're delivering soup."], "SOUP IS A CORE PRODUCT. fine. take the lanyard anyway. think about it. the grind never stops."], do: ["give:unpaid_lanyard", "flag:eotm_offered_internship"], next: "leave" },
          pay: { say: ["*he weighs the coupons in a gauntlet made of a stapler.*", "a strong negotiator. that's a soft skill. i respect soft skills.", "go. tell the first intern i sent you."], do: ["coupons:-40", "flag:paid_the_unpaid"], next: "leave" },
          fight: { say: ["oh, a disruptor. we LOVE disruptors. INTERNS. ONBOARD THEM."], do: ["flag:fought_the_unpaid"]  },
          leave: { say: ["*The rigs pull back, honking. Then a second wave of interns who didn't get the memo come screaming over the cars anyway.*", ["lumps", "i think there's two departments."]] },
        },
      },
      trade_post: {
        with: "sister_agenda", cam: "overShoulder",
        nodes: {
          start: { say: ["*A trade post on the Gut border: a turnstile grown over with skin, a counter, a robed Choir clerk with a stretched smile who sings her words on one note.*", "*sung* the soup, the soup, the tomato soup... *not sung* thank you. one pot. we'll count it.", "*She tips a little out and tastes it with a ladle that has a tongue.*"], opts: [["what's it for?", "for", { if: "flag:asked_sharon_soup" }], ["is this all the medicine?", "short"], ["*take the medicine*", "take"]] },
          for: { say: ["*sung* for the mouths, for the mouths... *not sung* sorry. i'm not allowed to say. it's a supply chain thing."], next: "take" },
          short: { say: ["it's... one box is for a 'growth adjustment'. it's empty. i'm sorry. it's policy. i don't write the policy. i write it down."], do: ["flag:medicine_short"], next: "take" },
          take: { say: ["*A crate of medicine slides across the counter.*", "same time next week. the tomato. the bishop likes the tomato.", "*Lumps is looking past her, deeper into the Gut, at the pink streets.*", ["lumps", "...it's sunday tomorrow."]], do: ["give:medicine_crate"] },
        },
      },
    },
    choices: [
      { id: "unpaid_offer", prompt: "Employee of the Month robs you and offers an internship.", options: [
        { id: "intern", label: "ask about the internship", do: ["give:unpaid_lanyard", "flag:eotm_offered_internship"], consequence: "You keep the Unpaid lanyard. Low-rank raiders sometimes wave you through on The Commute. EOTM remembers you as 'our newest intern' in his world-boss fight." },
        { id: "pay", label: "pay them off", do: ["coupons:-40", "flag:paid_the_unpaid"], consequence: "Costs 40 coupons. The Unpaid leave the Bottom's soup runs alone for the rest of Act I." },
        { id: "fight", label: "fight", do: ["flag:fought_the_unpaid"], consequence: "A bigger ambush. Better loot. The Unpaid raid the Bottom's next soup run without you (a short side activity in Act II)." },
      ] },
    ],
    scenes: ["p2_sauce_run"],
    reward: { coupons: 300, loot: ["lt_mission_rare"], items: ["medicine_crate"], flags: ["met_choir", "met_eotm"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. not a drop spilled. sharon is suspicious.", meets: "MEETS EXPECTATIONS. most of the soup arrived.", see_me: "SEE ME. you delivered a pot of nothing. the choir sang about it." },
    notes: "soup slosh: a hidden 0-100 meter; hard landings, car-on-car hits and barrel rolls take chunks; at 0 set soup_spilled (Sharon's next lines change, the medicine is short). It should be hard to fail on purpose and very funny to fail by accident.",
  },

  // ------------------------------------------------------------------ 3
  m03_somethings_digesting: {
    act: 1, n: 3, title: "SOMETHING'S DIGESTING", kind: "main", giver: "lumps", district: "gut",
    locations: ["gut:border", "gut:peristalsis", "gut:choir_lung", "gut:digester_wall", "gut:feed_dock"],
    cast: ["lumps", "dot", "sister_agenda", "bishop", "mina"],
    requires: { missions: ["m02_sauce_run"], if: null },
    logline: "It's Sunday. Lumps visits his mum in the Gut, and the Choir tells you where Gristle & Sons gets its feedstock: ☺ CORP sells it the people who fall behind on their back pay.",
    mechanic: { uses: ["slide", "grapple", "hype"], hook: "the Gut teaches flow: slide on Peristalsis Avenue's squeeze, swing the rib arches, bounce the lungs, and a long swing fills HYPE for the first time" },
    beats: [
      "C3: driving into the Gut. Skin streets, rib arches, the Choir turning. A woman in the wall says 'ambrose?'",
      "On foot: peristalsis streets carry you, lungs bounce you. Lumps knows the way and hates it.",
      "Dot in the digester wall. Chatty, warm, half absorbed. She does her names every morning so she doesn't dissolve: 'sharon, dumpling's dad, old ken, the twins from the top terrace, mina...' (the last name means nothing to you yet).",
      "Lumps tries to pull her out, as he does every week. The wall holds on. Dot tells him to stop.",
      "Sister Agenda in the Choir Lung: she keeps the real minutes. The trucks come at four. They're from your hill. ☺ CORP sells Gristle & Sons the people who fall behind on back pay. Dot was one.",
      "From the gallery you see the Stomach Bishop conducting, far below, over the acid lake. He sees you. He smiles, very wide.",
      "Stomach-dogs chase you out. Lumps carries you over the last lung.",
    ],
    reveals: {
      learn: ["☺ CORP sells people who can't pay their 'back pay' to Gristle & Sons as feedstock.", "The Bottom's missing people are in the Gut wall, alive.", "Lumps' mum is one of them."],
      suspect: ["The name 'mina' in Dot's list is someone you'll meet.", "The Bishop knows exactly who you are."],
      withheld: ["What the feedstock is for (the organs; Hask).", "The soup keeps the digesters alive (m20)."],
    },
    steps: [
      { id: "drive", text: "drive into the gut", goal: { type: "reach", zone: "gut:peristalsis" }, scene: "c3_its_breathing" },
      { id: "walk", text: "follow lumps down peristalsis avenue", goal: { type: "escort", who: "lumps", zone: "gut:digester_wall" }, notes: "teaches peristalsis surfing and lung trampolines" },
      { id: "dot", text: "talk to lumps' mum", goal: { type: "talk", who: "dot", talk: "sunday" }, marker: "gut:digester_wall" },
      { id: "agenda", text: "find out where the trucks come from", goal: { type: "talk", who: "sister_agenda", talk: "minutes" }, marker: "gut:choir_lung" },
      { id: "bishop", text: "", goal: { type: "reach", zone: "gut:choir_lung" }, notes: "a 6 s view from the gallery: the Bishop far below conducting, he looks up and smiles at you" },
      { id: "out", text: "get out of the gut", goal: { type: "reach", zone: "gut:border" }, notes: "stomach-dog chase; lungs as trampolines; Lumps carries you over the last one in a short Moment" },
    ],
    talks: {
      sunday: {
        with: "dot", cam: "closeup",
        nodes: {
          start: { say: ["ambrose! you came. it's sunday, isn't it? i can tell by your face. you've got your sunday face.", ["lumps", "brought you soup, mum. the yellow."], "oh, the yellow. lovely. put it there, i'll have it later.", "*There's a row of untouched bowls by the wall. Every week's soup. Lumps puts this one at the end of the row.*", "and who's this? oh, look at your knee. it goes the wrong way. that's character."], opts: [["i'm change. i came out of a machine.", "machine"], ["are you all right in there?", "allright"], ["how long have you been in the wall?", "long"]] },
          machine: { say: ["a machine! well, we all came out of something. ambrose came out of me and he was the size of a fridge.", ["lumps", "mum."], "he was."], next: "names" },
          allright: { say: ["oh, it's warm. don't make that face, it is. the worst bit is you stop minding.", "that's why i do my names. every morning."], next: "names" },
          long: { say: ["two years in may. or is it june. the wall doesn't have months. it has... digestion."], next: "names" },
          names: { say: ["i do the names every morning so i don't go soft at the edges. everyone in here. everyone i know.", "*She closes her eyes, like a prayer.*", "sharon. dumpling's dad. old ken. the twins from the top terrace. little pim's nan. ambrose. ambrose. ambrose. ...and mina. mina's further in. she's quiet but she's there.", "*She opens her eyes.* see? all there."], do: ["flag:heard_dot_names"], next: "pull" },
          pull: { say: [["lumps", "*grabs her hands* i'm getting you out. i'll pull. i'm strong. i've been training."], "*He pulls. The wall pulls back. Something wet tears and Dot gasps and Lumps lets go like he's been burned.*", "ambrose. ambrose, love. stop. it doesn't let go, it just hurts.", ["lumps", "*very quiet* sorry. sorry, mum."]], opts: [["we'll find a way to get you out.", "promise"], ["is there anything we can do?", "anything"], ["*put a hand on Lumps' shoulder*", "shoulder"]] },
          promise: { say: ["*She looks at you, then at her son.*", "don't promise him things, plastic. he holds on to promises. look at his arms. he holds on to everything.", "...but thank you."], do: ["flag:promised_dot", "standing.bottom:+3"], next: "bye" },
          anything: { say: ["find out who keeps sending the trucks. the singing lady upstairs writes it all down. she's got a book."], next: "bye" },
          shoulder: { say: ["*Lumps doesn't look round. He puts his huge hand over yours.*", "that's nice. that's a nice friend you've got there, ambrose."], do: ["standing.bottom:+1"], next: "bye" },
          bye: { say: ["go on. both of you. and eat something. i mean it. i can see your ribs from here, ambrose. and yours, plastic. you've got the plastic kind."] },
        },
      },
      minutes: {
        with: "sister_agenda", cam: "overShoulder",
        nodes: {
          start: { say: ["*The Choir Lung: a cathedral that breathes in and out, robes swaying with it. Sister Agenda sits at an office desk grown into a pew, with a Filofax grown into her hand.*", "*sung* the meeting is moved, the meeting is moved... *not sung* oh. you. from the trade post. sorry about the box.", "you want to know about the trucks. everyone who comes to this desk wants to know about the trucks."], opts: [["where do they come from?", "where"], ["who's in them?", "who"], ["why do you write it down?", "why"]] },
          where: { say: ["your hill. the bottom. the lates sometimes, and the commute. wherever people owe.", "☺ corp counts who's behind on their back pay. when you're far enough behind, they don't send a letter. they send mr. overtime. and then a truck."], next: "sold" },
          who: { say: ["the ones who owe the most. or the biggest. or the slowest. it's a list. i don't make the list. i get a copy.", "*She opens the Filofax. Hundreds of pages of names in tiny neat handwriting. Dates. Truck numbers.*"], next: "sold" },
          why: { say: ["somebody should. the bishop sings it. i write it. singing is how you forget a thing. writing is how you keep it."], next: "sold" },
          sold: { say: ["they're sold. ☺ corp sells them to us. gristle and sons. as feedstock.", "the gut grows on them. and we... harvest.", "*She looks at her own hand, the Filofax grown into it.*", "i'm not proud. i'm just still at my desk."], opts: [["harvest what?", "harvest"], ["who buys what you harvest?", "buys"]] },
          harvest: { say: ["*sung, very quietly* organs, organs, fresh and new... *not sung* the good ones go up the hill. i don't know who to. i only get the outgoing copy."], do: ["flag:learned_feedstock"], next: "end" },
          buys: { say: ["up the hill. that's all it ever says. UP THE HILL. priority. someone up there needs a lot of parts."], do: ["flag:learned_feedstock"], next: "end" },
          end: { say: ["*Far below, past the gallery rail, the Stomach Bishop conducts the whole district with a femur. He stops. He looks straight up at you. His smile keeps going after it should have stopped.*", "*sung* oh dear. he's seen you. *not sung* he likes new faces. go home. go home before four."] },
        },
      },
    },
    choices: [],
    scenes: ["c3_its_breathing"],
    reward: { coupons: 200, loot: ["lt_mission_rare"], flags: ["visited_gut"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you didn't touch the walls once.", meets: "MEETS EXPECTATIONS. you touched the walls. they liked it.", see_me: "SEE ME. a stomach-dog has your shoe." },
  },

  // ------------------------------------------------------------------ 4
  m04_clocking_in: {
    act: 1, n: 4, title: "CLOCKING IN", kind: "main", giver: "auntie", district: "bottom",
    locations: ["bottom:sunset_spot", "bottom:long_stairs", "gut:border", "gut:stairs_top"],
    cast: ["overtime", "lumps", "auntie", "mina", "dumpling", "gordo", "pallet_jack"],
    requires: { missions: ["m03_somethings_digesting"], if: null },
    logline: "Mr. Overtime comes down the Long Stairs to collect two hundred and forty-four quarters of back pay, in people. First nemesis fight.",
    mechanic: { uses: ["grapple", "water_taser", "redline"], hook: "Overtime's missed staples stay in the walls as grapple points; the collectors' water tank soaks him (wet clockwork runs slow); Lumps throws you the Redline when you're low" },
    beats: [
      "C4: sunset, the clocks stop, the brogues on the stairs. The collectors load people into a Gristle & Sons truck: Dumpling's dad, others, and an old woman with a braid who looks at you and says 'rory?'.",
      "Lumps stands in front of the truck. Overtime staples his arm to it.",
      "Boss fight: MR. OVERTIME (overtime_1) on the Gut border, where the stairs go soft and the lungs bounce you over his slams.",
      "At half HP he takes a coffee break.",
      "The Heart Rip: you tear a piece of the punch-clock out of his chest. He staggers, checks his watch, and retreats up the hill. 'this isn't finished. it's rescheduled.'",
      "The truck is already gone, into the Gut. You can chase it or stay with Lumps (a choice; both cost something).",
      "Aftermath: Pallet Jack comes back from a delivery up the Long Stairs to find nine gone. He picks Dumpling up off the floor from under the table and says nothing at all.",
    ],
    reveals: {
      learn: ["Mr. Overtime is ☺ CORP's collector, polite and unstoppable.", "Someone on the truck knows a name that might be yours: 'rory'."],
      suspect: ["Overtime treats everyone as 'absent', like he doesn't know the world ended.", "The old woman knew you."],
      withheld: ["Who Mina is (Act II, m10).", "That Overtime is a recording too (Act II)."],
    },
    steps: [
      { id: "sunset", text: "", goal: { type: "flag", flag: "seen_c4" }, scene: "c4_clocking_in", marker: "bottom:sunset_spot", do: ["fate:mina=gut"] },
      { id: "fight", text: "stop mr. overtime", goal: { type: "killBoss", boss: "overtime_1" }, boss: "overtime_1", marker: "gut:border" },
      { id: "rip", text: "", goal: { type: "flag", flag: "heart_ripped" }, scene: "mo_heart_rip", do: ["give:core_cracked_punch_clock"] },
      { id: "after", text: "", goal: { type: "talk", who: "overtime", talk: "rescheduled" } },
      { id: "truck", text: "the truck", goal: { type: "flag", flag: "truck_choice_made" }, notes: "the truck_choice choice below" },
      { id: "home", text: "go back to the lost & found", goal: { type: "reach", zone: "bottom:lostfound" }, talk: "aftermath" },
    ],
    talks: {
      rescheduled: {
        with: "overtime", cam: "lowAngle",
        nodes: {
          start: { say: ["*Overtime on one knee, steam pouring out of the hole in his chest. The ticking has a limp in it. He looks at his watch. Then at you. Then at the watch.*", "you've damaged company property.", "that's... that's me. i'm company property.", "*He stands. It takes a while.* this isn't finished. it's rescheduled.", "*He walks back up the Long Stairs, exactly on time, a little lopsided. At the top he stops and looks back at you for a long moment, like he's trying to remember where he put something.*"] },
        },
      },
      aftermath: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*The Lost & Found. Gordo stitching Lumps' arm with fishing line. Dumpling asleep under the table with a hat. Auntie, writing names in crayon on the wall, one under another.*", "nine. they took nine.", "*She writes the ninth name. Under it, after a pause, she writes: 'mina'. Just the first name. She knew it.*", "*Pallet Jack comes back from a delivery up the Long Stairs to find nine gone. He picks Dumpling up off the floor from under the table and says nothing at all.*"], opts: [["the old woman on the truck called me rory.", "rory"], ["we'll get them back.", "back"], ["who's mina?", "mina", { if: "flag:heard_dot_names" }]] },
          rory: { say: ["*The crayon stops.*", "did she.", "...people say a lot of names when they're being put on a truck, change. they say the names of whoever they wish was there.", ["gordo", "*not looking up* that's not an answer, auntie."], "it's the one i've got, gordon."], do: ["flag:asked_about_rory"], next: "end" },
          mina: { say: ["*She doesn't turn round.*", "mina's lived on the top terrace for forty years. she climbs better than the kids. she taught half of them.", "she's seventy. they took a seventy-year-old woman for back pay."], next: "end" },
          back: { say: ["from the gut? nobody's ever come back from the gut, change.", ["lumps", "nobody's ever ripped his heart out before."], "*Auntie looks at Lumps' arm. At the hole in it.*", "...no. nobody had."], do: ["standing.bottom:+2"], next: "end" },
          end: { say: ["*Dale comes in from the Machine for the first time anyone can remember. He's holding the core in a tea towel. It ticks.*", ["dale", "it's still going. his heart. well, a bit of it."], ["gordo", "we could sell it."], ["dale", "or we could put it in someone who doesn't mind ticking."], "*Everyone looks at you.*"] },
        },
      },
    },
    choices: [
      { id: "truck_choice", prompt: "The truck is getting away into the Gut. Lumps is pinned to the ground by a staple through his arm.", options: [
        { id: "chase", label: "chase the truck", do: ["flag:chased_truck", "flag:truck_choice_made", "flag:saw_mina_twice"], consequence: "You catch the truck as it passes under the first rib arch. You can't open it: the doors have grown shut. Through the slot the old woman with the braid looks out and says 'rory' again, quieter, like a question she's sure of. You learn the truck's number (it matters in m20). Lumps gets himself free by tearing the staple out of the bumper; it leaves a scar he shows people." },
        { id: "stay", label: "stay with lumps", do: ["flag:stayed_with_lumps", "flag:truck_choice_made", "standing.bottom:+3"], consequence: "You pull the staple out of Lumps' arm. He doesn't cry until it's out, then he does. 'thanks. sorry. thanks.' Lumps trusts you more (his Act III choice is easier to steer). You don't get the truck number; Sister Agenda has to find it for you in m20." },
      ] },
    ],
    scenes: ["c4_clocking_in", "mo_heart_rip"],
    reward: { coupons: 500, items: ["core_cracked_punch_clock"], flags: ["beat_overtime_1"], standing: { bottom: 10, corp: -10 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you made employee #1 take a coffee break.", meets: "MEETS EXPECTATIONS. he's been rescheduled.", see_me: "SEE ME. you were stapled to a truck for eleven seconds." },
    notes: "people taken in C4 stay taken unless m20 frees them (DESIGN §7.1). Nine names on the wall: they are the m20 rescue list.",
  },

  // ------------------------------------------------------------------ 5
  m05_second_stomach: {
    act: 1, n: 5, title: "SECOND STOMACH", kind: "main", giver: "dale", district: "gut",
    locations: ["gut:clinic_bev", "bottom:lostfound"],
    cast: ["auntie", "bev", "dale", "overtime", "pallet_jack"],
    requires: { missions: ["m04_clocking_in"], if: null },
    logline: "A Meat Mechanic installs the piece of Overtime's heart in your chest. Implants unlocked. For a second you remember a lobby, a pair of running shoes, and the time: 17:29.",
    mechanic: { uses: ["implants"], hook: "the first install: the clinic chair is the implant UI, and the Punch-Clock's tick is your first downside" },
    beats: [
      "Auntie takes you to Bev's clinic on the Gut border.",
      "In Bev's waiting room: Pallet Jack, getting his boiler bled. Bev: 'you're next, jack. you're always next.'",
      "C5: the install. 'this is a terrible idea.' 'they're all terrible ideas. this one works.' Bev explains Drift in one line: the more of you that isn't you, the less of you there is.",
      "The first memory flash: a lobby, running trainers, 17:29.",
      "Implant tutorial: body slots, Body Budget, the Cracked Punch-Clock's perk and downside (it ticks).",
      "Back at the Lost & Found Auntie tries to say something and doesn't.",
      "P5b (moved: it plays at the end of m06, TICKETS, PLEASE): Overtime in his office looks at the still of you. CALE, R. employee 4417. deleted. late for a meeting at 17:30.",
    ],
    reveals: {
      learn: ["Your body takes organs that aren't yours. The more you take, the more you drift.", "You have memories. You were in a marble lobby at 17:29, running.", "(P5b, at the end of m06) Your name, according to ☺ CORP, is CALE, R., employee 4417. Deleted."],
      suspect: ["'rory' and 'cale, r.' are the same person.", "Auntie is scared of what you'll remember."],
      withheld: ["Who Cale was, and what they were running with (Act II)."],
    },
    steps: [
      { id: "clinic", text: "take the core to the meat mechanic on the gut border", goal: { type: "reach", zone: "gut:clinic_bev" }, marker: "gut:clinic_bev", talk: "bev_intro" },
      { id: "install", text: "", goal: { type: "flag", flag: "seen_c5" }, scene: "c5_second_stomach", do: ["implant:core_cracked_punch_clock", "flag:implants_unlocked"] },
      { id: "tutorial", text: "check your new part", goal: { type: "talk", who: "bev", talk: "parts" } },
      { id: "home", text: "go home", goal: { type: "reach", zone: "bottom:lostfound" }, talk: "night" },
    ],
    talks: {
      bev_intro: {
        with: "bev",
        nodes: {
          start: { say: ["*Bev's waiting room. Pallet Jack, getting his boiler bled.*", "you're next, jack. you're always next.", "*Bev doesn't look up from a jar.* close the curtain. the flies are union.", "so you're the thing from the machine. huh. thought you'd be taller.", ["auntie", "can you put this in it? them. in them."], "*Bev takes the tea towel, unwraps the ticking core with two hands, and lights a cigarette with a third.*", "a bit of overtime's heart. you know how many people have walked in here with a bit of overtime? none. you know why? he doesn't come apart."], opts: [["will it hurt?", "hurt"], ["what will it do to me?", "do"], ["how much?", "much"]] },
          hurt: { say: ["you're plastic. no. that's a lie. i say it to everyone. lie back."] },
          do: { say: ["make you tick. make you fast when you're dying. make you late if you don't clock in. it's a heart. it's got opinions."] },
          much: { say: ["first one's free. that's not kindness, that's marketing. lie back."] },
        },
      },
      parts: {
        with: "bev",
        nodes: {
          start: { say: ["right. listen, chassis, because i only say this once and then i charge.", "you've got slots. head, eyes, mouth, heart, lungs, guts, spine, arms, legs, skin. that's ten places to put a bad decision.", "your body's got a budget. three parts now. more as you... go up in the world. promotions. ask the cats.", "go over the budget and it'll still work. you'll lump. you'll twitch. and you'll drift."], opts: [["drift?", "drift"], ["the cats?", "cats"], ["why does it tick?", "tick"]] },
          drift: { say: ["*She takes the cigarette out.*", "you came out of that machine as somebody. a recording of somebody. every part that isn't yours pushes that somebody a bit further off.", "you won't notice. that's the thing. the people who love you notice.", ["auntie", "*very quietly* ...yes."]], do: ["flag:bev_explained_drift"] },
          cats: { say: ["the board of directors. cats. they're all over the city. pet one, your body takes it as a promotion. don't ask me why. i'm a mechanic, not a vet."] },
          tick: { say: ["it's a punch-clock. it wants you to clock in. once an hour, stand still and let it. or it'll fine you.", "*Your chest goes TICK. Then TICK. Loudly.*", "yeah. everybody's going to hear you coming. welcome to having a heart."] },
        },
      },
      night: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*The Lost & Found at night. The Machine hums. Your chest ticks in time with it. Auntie at the table with the notebook open and no crayon in her hand.*", "you saw something. in the chair. bev said you went somewhere."], opts: [["a lobby. someone running. 17:29.", "lobby"], ["nothing.", "nothing"]] },
          lobby: { say: ["*She closes the notebook.*", "17:29.", "*For a moment she looks like she's going to say a lot of things. She picks up a crayon. Puts it down.*", "...it's late. sixty-one years late, everything in this city. go to sleep, change."], do: ["flag:told_auntie_1729"] },
          nothing: { say: ["*She looks at you over her glasses, the look she gives a bad invoice.*", "you're a terrible liar. good. keep it that way. go to sleep."], do: ["flag:lied_to_auntie_1"] },
        },
      },
    },
    choices: [],
    scenes: ["c5_second_stomach"],
    reward: { coupons: 200, implants: ["core_cracked_punch_clock"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. one heart, installed, ticking.", meets: "MEETS EXPECTATIONS. you have a pulse. it's not yours.", see_me: "SEE ME. you asked bev for a refund." },
  },

  // ------------------------------------------------------------------ 6 (the train: docs/story/TRAIN.md, approved 2026-11-10)
  m06_tickets_please: {
    act: 1, n: 6, title: "TICKETS, PLEASE", kind: "main", giver: "gordo", district: "commute",
    locations: ["bottom:lostfound", "bottom:service_tunnel", "commute:underhill_loop", "commute:tunnel_mouth"],
    cast: ["gordo", "lumps", "pallet_jack", "dale", "bev", "auntie", "dumpling", "revenue_protection"],
    requires: { missions: ["m05_second_stomach"], if: null },
    startScene: null, // the first scene is the ride in (step 4), not the mission's opening: it must not play on the mission card
    logline: "The only other way into the Gut is the commuter line under the hill. Nobody takes it, because the tunnel eats. Four of you go in. The thing that follows you out is wearing the company's face.",
    mechanic: { uses: ["bloodcross", "rig", "implants", "slide", "blooddrive"], hook: "a boss you fight from the back of a moving train with a gun that fires your own blood; the fight is unwinnable until you take a dead friend's marrow" },
    beats: [
      "Gordo's plan, on the back of a soup label: the Loop goes under the Gut. Dale has a loco. Jack has a spare frame.",
      "Bev fits you with the Blood Drive. Jack says goodbye to Dumpling like it's a delivery.",
      "The ride in: the dark, the banter, and on the next track a dead commuter train, every seat empty, every door open.",
      "The lights go out behind you, one at a time. Something takes Jack through the back before anyone sees what it is.",
      "Boss: REVENUE PROTECTION, phase 1. Jack holds the rail until his armour breaks.",
      "Jack asks you to kill him before it gets him, and to take his marrow. You do it yourself. Lumps can't.",
      "Phases 2 and 3: the mask breaks, the thing behind it, daylight.",
      "The Commute at dusk. Lumps carries Jack off the train. Nobody talks. END OF ACT I.",
    ],
    reveals: {
      learn: ["There is a line under the hill and now it's yours.", "Something made of people lives in it, and it wears a ☺ CORP sign.", "A part taken from a friend works the same as a part taken from an enemy."],
      suspect: ["They were passengers.", "Someone put that face on them.", "Whatever grew the Gut grew this."],
      withheld: ["Regrowth, and what the dead were for (Act III).", "That it grows back, and that the Inspector can be talked to (Act III)."],
    },
    steps: [
      { id: "plan", text: "meet gordo at the lost & found", goal: { type: "talk", who: "gordo", talk: "the_loop" }, marker: "bottom:lostfound" },
      { id: "fitted", text: "get fitted", goal: { type: "talk", who: "bev", talk: "loaner" }, marker: "gut:clinic_bev", do: ["give:blood_drive"] },
      { id: "board", text: "board the train", goal: { type: "reach", zone: "bottom:service_tunnel" }, marker: "bottom:service_tunnel" },
      { id: "ride", text: "", goal: { type: "flag", flag: "seen_c6_mind_the_gap" }, scene: "c6_mind_the_gap" },
      { id: "hold", text: "keep it off the train", goal: { type: "flag", flag: "rp_phase1_done" }, boss: "revenue_protection_1", marker: "commute:underhill_loop", notes: "boss phase 1. Not winnable: the fight sets rp_phase1_done at 60%, when Jack's armour breaks" },
      { id: "jack", text: "", goal: { type: "flag", flag: "seen_mo_carry" }, scene: "mo_carry_the_bit_that_works", do: ["fate:pallet_jack=dead", "implant:marrow_pallet_jack"], notes: "playable: the scene's [FIRE] and [TAKE] prompts are the `fire` and `take` choices below (one button each, no timer). The marrow's +1 Drift is on the implant" },
      { id: "break", text: "break its face", goal: { type: "killBoss", boss: "revenue_protection_1" }, boss: "revenue_protection_1", marker: "commute:underhill_loop", notes: "boss phases 2 and 3" },
      { id: "terminus", text: "", goal: { type: "flag", flag: "seen_c6b" }, scene: "c6b_terminus", marker: "commute:tunnel_mouth" },
      { id: "p5b", text: "", goal: { type: "flag", flag: "seen_p5b" }, scene: "p5b_employee_4417", do: ["flag:act1_done"], notes: "moved here from m05: END OF ACT I is this scene's last card" },
    ],
    talks: {
      the_loop: {
        with: "gordo",
        nodes: {
          start: { say: ["*The Lost & Found, early. Nine names on the wall in crayon. Gordo has a soup label flattened on the table with a line drawn round a hill.*", "the wall's shut. grown over. i went and looked. it's like a scar.", "so we don't go through the wall. we go under it. there's a railway under this whole hill. goes under the gut, comes up on the commute, goes round again.", ["auntie", "nobody takes the loop, gordon."], "nobody had a train.", "*Dale, in the doorway, holding a brake handle like a cup of tea.*", ["dale", "it's more of a tractor. but it's on rails."]], opts: [["why does nobody take it?", "eats"], ["who's coming?", "who"]] },
          eats: { say: [["auntie", "because the tunnel eats. forty years ago six of ours went in to salvage copper. we found a boot."], "cave-ins.", ["auntie", "a boot with the laces done up, gordon. on the track. like someone had been taken out of it."]], next: "who" },
          who: { say: ["dale drives. lumps lifts. i think. you shoot. and jack, because if a roof comes down jack can hold up a roof.", "*Pallet Jack, by the door, Dumpling sitting on his hand truck.*", ["pallet_jack", "roof's about four tonne a metre. i can hold a metre."], ["pallet_jack", "i'll want my dinner first."]] },
        },
      },
      loaner: {
        with: "bev",
        nodes: {
          start: { say: ["*Bev's clinic. A frame of scaffold pole and seatbelt webbing hanging off a hook: a brace, a yoke, an arm cradle with six glass barrels round it.*", "that was his. before i started putting it on the inside. he grew out of it. literally.", "arm.", "*She takes your right hand off at the wrist, the way you'd take a lid off a jar, plumbs six lines into it, and puts it back on.*", "you know the finger trick. the blood one. this is that, six at a time, on a motor. it'll empty you in three seconds. don't hold it down unless you mean it."], opts: [["then what's the point of it?", "point"], ["how does jack run his all day?", "jack"]] },
          point: { say: ["three seconds of that is a lot of problem solved. and you get it back off whatever you kill. it's a loan. everything i sell is a loan."] },
          jack: { say: ["*Bev looks through the curtain at Jack, who is showing Dumpling how to carry a fridge that isn't there.*", "i took his marrow out and put better in. gristle stock. he makes blood like a tap. it's the only reason that boiler hasn't killed him.", "it's the best work i've ever done and it's wasted on a man who carries soup."], do: ["flag:bev_explained_marrow"] },
        },
      },
    },
    choices: [
      { id: "fire", prompt: "The Snatchers are four metres away.", options: [
        { id: "fire", label: "[FIRE]", do: ["flag:jack_fired"], consequence: "You fire. One bolt. It sticks. He breathes out. The cross comes, and it's small, and it's quick." },
      ] },
      { id: "take", prompt: "His hand comes off yours and stays open on the deck.", options: [
        { id: "take", label: "[TAKE]", do: ["flag:jack_marrow_taken"], consequence: "Your hand goes in through the split boiler, the same motion as the Heart Rip, slower. What comes out is a length of spine the colour of a traffic light, wet, and warm, and still making blood: it runs down your arm and into the cradle and all six barrels fill at once." },
      ] },
    ],
    scenes: ["c6_mind_the_gap", "mo_carry_the_bit_that_works", "c6b_terminus", "p5b_employee_4417"],
    reward: { items: ["loop_train"], loot: ["blood_drive"], implants: ["marrow_pallet_jack"], flags: ["beat_revenue_protection_1", "train_unlocked", "act1_done"] },
    grade: { exceeds: "NO REVIEW TODAY.", meets: "NO REVIEW TODAY.", see_me: "NO REVIEW TODAY." },
    notes: "the only mission whose grade card has no joke. Jack's vest stays on Dumpling for the rest of the game (it never fits). LEG DAY's intro changes: Lumps is carrying fridges up the Long Stairs because someone has to do Jack's round.",
  },
};
