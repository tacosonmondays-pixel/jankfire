// OVERDUE side questlines: THE MARGINS. Schema: see side/bottom.js.

export const SIDE_MARGINS = {
  sq_margins_lifeguard: {
    kind: "side", from: 4, title: "LIFEGUARD", giver: "janitor", district: "margins",
    locations: ["margins:edge", "margins:gnome_field"], cast: ["janitor", "old_pat"],
    requires: { missions: ["m26_exit_interview"], if: null },
    logline: "People fall into the void. Some of them wave. Pull them out with the lasso before they sink out of reach.",
    mechanic: { uses: ["lasso", "void_edges"], hook: "lasso rescues out of the void, falling in on purpose" },
    twist: "The ones you pull out are still employed. They've just lost the dental. And they're recent: Vacancy's survey teams have been 'clearing' squatters. The last one you pull out is the Janitor's wife, who went in sixty-one years ago with their house, and she's exactly as she was, mid-sentence. 'wendell, have you mopped' — and the void takes her back before she can finish. The Janitor says thank you. He means it. He keeps mopping.",
    beats: ["The lifeguard tower on the Edge. The Janitor: 'some of them wave. i wave back now.'", "Lasso rescues (timed; heavy ones drag you in: fall in on purpose and respawn at a gnome, keeping momentum).", "Eleven people out. Each gets a gnome with their name (Old Pat paints them).", "The twelfth wave."],
    steps: [
      { id: "tower", text: "climb the lifeguard tower", goal: { type: "talk", who: "janitor", talk: "wave" }, marker: "margins:edge" },
      { id: "rescue", text: "pull 11 people out of the void", goal: { type: "escort", who: "old_pat", zone: "margins:gnome_field" } },
      { id: "last", text: "", goal: { type: "talk", who: "janitor", talk: "mopped" } },
    ],
    talks: {
      wave: { with: "janitor", nodes: { start: { say: ["*squeak. squeak.*", "careful. floor's wet. it's the void. i mop it anyway. job's a job.", "some of them wave. i wave back now. i'm old. what's it going to do.", "you've got a rope. go on. they're still employed. they've just lost the dental."] } } },
      mopped: { with: "janitor", cam: "closeup", nodes: { start: { say: ["*The Janitor on the edge, the mop in both hands, looking at where she went back under.*", "she was going to say 'have you mopped the hall'. she always said it. i always hadn't.", "*a long time*", "...thank you. i got to hear the first half.", "*squeak. squeak.*"], do: ["flag:janitor_heard_her"] } } },
    },
    choices: [],
    reward: { coupons: 600, standing: { bottom: 4 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. everyone out.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you fell in. eleven times." },
  },

  sq_margins_staking_claims: {
    kind: "side", from: 4, title: "STAKING CLAIMS", giver: "old_pat", district: "margins",
    locations: ["margins:gnome_field", "margins:bus_stop", "margins:show_home"], cast: ["old_pat", "penny_plot"],
    requires: { missions: ["m26_exit_interview"], if: null },
    logline: "Plant gnomes to hold the ground. Vacancy can't sell what's occupied.",
    mechanic: { uses: ["void_edges", "grapple"], hook: "turn 412 gnomes under fire before sundown" },
    twist: "Vacancy's lawyers have found the loophole: a gnome counts as occupation only if it's 'facing the property'. The Margin Walkers have been planting them facing the void for years. You have to turn four hundred and twelve gnomes round, under fire from survey teams, before the lawyers' deadline. Old Pat, for the first time, looks at the names under them as she turns each one.",
    beats: ["Gnome planting (each gnome is a respawn point on the Margins).", "The loophole letter.", "Turn every gnome round before sundown (survey drones, hazmat agents)."],
    steps: [
      { id: "plant", text: "plant 20 gnomes on unclaimed ground", goal: { type: "interact", target: "margins:gnome_field" } },
      { id: "turn", text: "turn the gnomes to face the property before sundown", goal: { type: "survive", secs: 480 } },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 700, standing: { bottom: 4 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. occupied.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you planted a gnome in the void. it's gone." },
  },

  sq_margins_the_last_bus: {
    kind: "side", from: 4, title: "THE LAST BUS", giver: null, district: "margins",
    locations: ["margins:bus_stop", "bottom:lostfound"], cast: ["old_pat"],
    requires: { missions: ["m26_exit_interview"], if: null },
    logline: "The Last Bus Stop's timetable says the 17:42 is due. It's been due for sixty-one years.",
    mechanic: { uses: ["cars"], hook: "drive a bus out of the void against the clock" },
    twist: "At 17:42 on a foggy night, it comes: a city bus out of the void, the 17:42 from the Final Quarter, with the driver and nine passengers who don't know anything has happened. Their bus went into the void bomb's blast and came out the other side sixty-one years later. You have to get them to the Bottom before the void takes the bus back at 18:00, while they ask questions you don't want to answer. (The Lost & Found's 'one of them is a whole bus' lost-property tag was always this bus.)",
    beats: ["A timetable. Wait at the stop at 17:42 in fog.", "The bus arrives. Drive it (the driver lets you: 'i've had a long shift').", "Passengers' questions on the way (dialogue barks: where are the shops, why is it dark, is that a church breathing).", "The Lost & Found by 18:00."],
    steps: [
      { id: "wait", text: "wait for the 17:42", goal: { type: "reach", zone: "margins:bus_stop" }, if: "clock.margins=17:40-17:50" },
      { id: "drive", text: "get the bus to the lost & found before 18:00", goal: { type: "reach", zone: "bottom:lostfound" }, timer: 600 },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 800, flags: ["last_bus_home"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. on time.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. the bus is late. again." },
  },
};
