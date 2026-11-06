// OVERDUE scenes, Act III: "Off the Clock". Same schema as scenes_act1.js.

export const SCENES_ACT3 = {
  p12_nine_kilometres: {
    kind: "panels", act: 3, mission: "m18_nine_kilometres", len: 20, music: "numberworks_press",
    cast: { gordo: "gordo", you: "change" },
    tracks: [
      { t: 0, panel: { n: 1, cap: "the schedule. every minute of every day of ☺ corp's city, booked.", sfx: "KA-CHUNK" }, dir: "The Price Press runs a single endless sheet. It feeds up and out of the Smokestacks and unrolls down the chimneys like a paper waterfall." },
      { t: 5, panel: { n: 2, say: [["gordo", "nine kilometres of it. every slot's got a name in it. every single one."]] }, dir: "Gordo on his knees on the sheet in the yard, running a finger down columns of tiny names and times." },
      { t: 10, panel: { n: 3, sfx: "..." }, dir: "His finger stops. A white band across the paper, all the way across: no names, no slots. 03:00-04:00." },
      { t: 14, panel: { n: 4, say: [["gordo", "03:00. nobody's booked. not even them."]] }, dir: "Gordo looks up. He isn't triumphant. He looks like someone who's just read their own name." },
      { t: 18, title: "THE MISSING HOUR" },
    ],
  },

  c13_workforce_restoration: {
    kind: "cinematic", act: 3, mission: "m23_workforce_restoration", len: 92, music: "missing_hour",
    cast: { you: "change", pauline: "pauline", gordo: "gordo" },
    tracks: [
      { t: 0, cam: { shot: "wide" }, dir: "The Lates, 02:59. Pauline from Accounts stands with you and Gordo on the roof of Tuesday Tower, holding her notebook. Everything is the yellow-beige Tuesday it always is." },
      { t: 4, say: ["pauline", "twenty-two thousand nights i've watched this. you're the first person i've watched it with."] },
      { t: 8, fx: "greyout", sfx: "silence", dir: "03:00. The Lates goes grey. Not dark: grey, like an unloaded texture. The hold music stops. Every Looper freezes mid-step. The loop has a gap in it, and you're standing in it." },
      { t: 14, dir: "In the sky over the waiting room, a rectangle of light opens: a door. A plain office door, fifty metres up, ajar." },
      { t: 18, say: ["gordo", "...i was born in this hour."] },
      { t: 21, cam: { path: "c13_door", dur: 10 }, dir: "A staircase of grey steps assembles itself under your feet, one at a time, as you walk up to the door. Through it." },
      { t: 31, cam: { shot: "wide", fov: 30 }, music: "missing_hour_swell", dir: "A warehouse the size of a district. Fluorescent strips to the horizon. Mannequin bodies in rows, standing, perfectly still, thousands, hundreds of thousands, each with a ☺ CORP lanyard, each with a cable running from the back of its neck up into the dark." },
      { t: 42, dir: "The cables run together into trunks, the trunks into one great cable that runs out of a wall marked ARCHIVE LINK: LOST & FOUND. The Machine." },
      { t: 48, cam: { shot: "dolly", target: "you", dur: 8 }, dir: "On the far wall, the size of a cliff, the Master Clock's schedule: every body has a slot. 09:00 START. 17:30 RECHARGE. 03:00 UPDATE. Forever. Under it, a banner: WORKFORCE RESTORATION. THE DEAD DON'T MIND." },
      { t: 58, say: ["gordo", "they're going to put everyone in the machine into these. everyone who died at 17:30."] },
      { t: 63, say: ["gordo", "a recording can be told what time it is. they'll never stop. they'll never ask for anything."] },
      { t: 68, cam: { shot: "closeup" }, dir: "A screen on a console near the door. A mannequin silhouette that's yours: your tilt, your wrong knee. A label." },
      { t: 72, title: "PROTOTYPE 0 (SCHEDULE NOT LOADED)" },
      { t: 76, dir: "Beside it, a status line: CALE R. 4417 · TERMINATED 17:29:41 · NO ACTIVE CONTRACT · SCHEDULE FIELD EMPTY · RECOMMEND: STUDY, THEN DELETE." },
      { t: 82, say: ["gordo", "...you're the one that doesn't work."] },
      { t: 86, sfx: "alarm_soft", dir: "Somewhere far down the rows, a single mannequin turns its head toward you. Then the next one. Then the row." },
      { t: 90, say: ["pauline", "*from the door, very calm* it's 03:04. we should go."] },
    ],
  },

  c14_the_offer: {
    kind: "cinematic", act: 3, mission: "m24_the_split", len: 64, music: "hask_theme",
    cast: { you: "change", hask: "hask", dale: "dale" },
    tracks: [
      { t: 0, cam: { shot: "wide" }, dir: "The Lost & Found, late. The Machine's terminal by Dale's shed flickers on by itself. Its little green screen goes white." },
      { t: 4, say: ["dale", "...that's not me."] },
      { t: 6, cam: { shot: "closeup", target: "hask" }, dir: "On the screen, in a white office with one window, Marion Hask: silver hair in a perfect knot, a white suit buttoned to the throat, a surgical scar just visible above the collar. Perfectly calm. A clock behind her. She is exactly on time." },
      { t: 12, say: ["hask", "Good evening. You are four minutes early. I appreciate that."] },
      { t: 17, say: ["hask", "You have been inside my warehouse. I would like to show you why it exists."] },
      { t: 21, cam: { shot: "insert" }, music: "long_dark", dir: "The screen cuts to old ☺ CORP security footage, grainy: the Long Dark. Ash falling for years. Crowds at the Spire's gates in the snow. Fires in the streets. A child eating paper. A food riot at a Big Value. Bodies stacked in the valley that's now the Gut." },
      { t: 33, say: ["hask", "That was the city without a schedule. I watched it from that window for thirty years."] },
      { t: 38, say: ["hask", "Inside the Spire, we rationed air, water, food and light to the minute. We were late to nothing. Nobody inside starved."] },
      { t: 44, say: ["hask", "The Restoration feeds everyone. The dead do not mind working. I have asked them."] },
      { t: 49, say: ["hask", "You could have a name, a job, and a life that does not end. Your name, if you like. Cale. It is in my records."] },
      { t: 55, say: ["hask", "Or you could go back in the bin."] },
      { t: 58, say: ["hask", "My assistant will book you. Good night."] },
      { t: 61, fade: "out", dir: "The screen goes green. Dale is staring at the terminal. Then at you. He knows exactly how she got in." },
    ],
  },

  c15_the_split: {
    kind: "cinematic", act: 3, mission: "m24_the_split", len: 66, music: "the_split",
    cast: { you: "change", auntie: "auntie", lumps: "lumps", gordo: "gordo", mina: "mina" },
    tracks: [
      { t: 0, cam: { shot: "wide" }, dir: "The Lost & Found, the next morning. Everyone at the long table. Four pages on the wall now. Auntie at the head. Lumps with his hands flat on the table. Gordo standing. If Mina was freed, she sits next to you, wrapped in a blanket." },
      { t: 6, say: ["lumps", "she's offering. hask. she's offering jobs. for the ones in the gut. pritchard wrote to me. they'd get them out. all of them. mum."] },
      { t: 13, say: ["gordo", "she's offering them a schedule. she's offering them a leash."] },
      { t: 17, say: ["lumps", "a leash is better than the wall, gordo."] },
      { t: 20, say: ["gordo", "is it? ask the mannequins in evergreen. oh, you can't. they're waving."] },
      { t: 24, say: ["gordo", "03:00. the missing hour. nobody's booked. we go up the hill in the one hour they can't see, and we blow up that clock. no clock, no schedule, no restoration. no new bosses."] },
      { t: 33, say: ["auntie", "and then what, gordon? who keeps the lights on? who feeds the spire's thousands? who stops the next one?"] },
      { t: 39, say: ["auntie", "we publish. all six pages. option c on every screen in the city. every debt they ever collected, void. then they have to sit at a table with us, because they've got nothing left to sell."] },
      { t: 47, say: ["gordo", "a table. with the people who ended the world."] },
      { t: 50, say: ["auntie", "yes. because the alternative is a world with nobody at the table at all."] },
      { t: 55, if: "fate.mina=freed", say: ["mina", "*quietly, to you* you've got that face. the one you made when you had to pick a cereal. pick, rory."] },
      { t: 58, dir: "Silence. Lumps, Gordo and Auntie all look at you. Nobody tells you what to say." },
      { t: 63, choice: "whose_plan" },
    ],
  },

  p16_tuesday_again: {
    kind: "panels", act: 3, mission: "m25_tuesday_again", len: 18, music: "overtime_theme_low",
    cast: { ot: "overtime" },
    tracks: [
      { t: 0, panel: { n: 1, sfx: "SLAM" }, dir: "Overtime mid-slam in the Lates' looping car park." },
      { t: 3, panel: { n: 2, sfx: "SLAM" }, dir: "The same panel. Identical. Except his tie is on the other shoulder." },
      { t: 6, panel: { n: 3, sfx: "sl..." }, dir: "The same panel. The slam stops halfway. Static on his visor." },
      { t: 9, panel: { n: 4 }, dir: "The same panel. He has stopped. His arms are by his sides. He's looking at his watch." },
      { t: 12, panel: { n: 5, say: [["ot", "i was going home at 17:30. why didn't i go home?"]] } },
      { t: 16, title: "END OF ACT III" },
    ],
  },
};
