// OVERDUE cast bible, part 1: the main cast, the villains and the people from the last workday.
// Strings use double quotes because the dialogue is full of apostrophes.
//
// SCHEMA: CAST_MAIN[id] = {
//   name        what the HUD and subtitles call them (ALL CAPS)
//   full        their real full name (or null)
//   title       one-line role, in the game's voice
//   role        'player' | 'main' | 'villain' | 'faction' | 'boss' | 'district' | 'minor' | 'lore' | 'secret' | 'flashback'
//   body        'mannequin' | 'normal' | 'puppet' | 'cyborg' | 'cat' | 'thing'   (ART_BIBLE §1)
//   age         years, or null
//   look        what the modeller needs (one or two sentences)
//   voice       the babble voice for audio.js: { kind, pitch, rate } (DESIGN §8.1)
//   home        a LOCATIONS id where they can usually be found (or null)
//   met         the mission or side quest id where the player first meets them
//   wants, fears, secret, arc   one paragraph each, plain prose
//   speech      how they talk (rules a writer can follow)
//   samples     6-10 lines in their voice, for writers and for barks
//   rel         { castId: how they feel about that person }
//   fate        { on_time, late, off_books, nap_time }: where they end up in each ending (see endings.js)
// }

export const CAST_MAIN = {
  change: {
    name: "CHANGE", full: "Rory Cale (recording)", title: "the first thing the Machine ever gave back", role: "player", body: "mannequin", age: null,
    look: "The game's jointed mannequin, wearing whatever the player wears, with the built-in jank (a tilt, a wrong knee). Implants show on the body. A faint ☺ CORP barcode on the back of the neck that doesn't scan.",
    voice: null, home: "bottom:lostfound", met: "m01_return_to_sender",
    wants: "First, to find out who they were. Then, once they know, to decide what happens to everyone else still inside the Machine, and what to be now.",
    fears: "That there's nothing under the plastic: that they're a copy, a product, a returned item, and that the people who care about them care about someone who died sixty-one years ago.",
    secret: "Change is the recording of Rory Cale, a junior auditor who was killed in the ☺ Spire lobby at 17:29:41 on the Final Quarter carrying a copy of Option C. Cale was fired by Overtime's punch-clock the second they died, so the Schedule never loaded into the recording. That's why the Machine couldn't keep them in.",
    arc: "From an object that fell out of a vending machine to the one person who decides what the city's time is worth. The player chooses whether Change becomes Cale again (low Drift, forgiving, remembering Mina), something new (the middle), or the perfect employee (high Drift, signing). Nothing is locked; the story just talks to them differently.",
    speech: "Change never speaks unprompted. Their lines are the player's dialogue choices: short, plain, lowercase. Choice text offers three registers when it matters: warm (Cale), dry (Change), cold (Drift). Cold lines only appear at Drift 2+.",
    samples: [
      "who was i?", "i don't remember you. i'm sorry.", "that's not my name. it might be.", "i'll get them out.",
      "(warm) you didn't kill me. he did.", "(dry) the machine never gave change. now it has to live with it.", "(cold) the schedule's efficient. i'll give it that.",
    ],
    rel: {
      auntie: "The first face they saw. Feels safe with her long before they know why that's complicated.",
      lumps: "A friend from the first hour. Lumps treats them like a person before anyone else does.",
      gordo: "Wary respect. Gordo is the only one who says out loud that Change might be a Corp product.",
      dale: "He pressed the button. Change owes him everything and doesn't know what he's paid for it.",
      mina: "A stranger who says their name before they know it. Then a sister they can't remember.",
      overtime: "The man who killed them. The thing they become if they sign.",
      hask: "The woman who decided they'd be property, and the only one who offers them a future that doesn't end.",
    },
    fate: {
      on_time: "R. CALE, HEAD OF TIMEKEEPING. Copied ten thousand times. Every copy clocks in at 09:00.",
      late: "Walks the dark city with no clock in the HUD for the first time. Helps the Bottom build. Nobody knows how long they'll last; that's normal now.",
      off_books: "Walks out onto The Commute alone with a backup they choose never to restore. Dale leaves the tray empty.",
      nap_time: "Asleep on the floor of the clock room with a cat on their chest.",
    },
  },

  auntie: {
    name: "AUNTIE SPREADSHEET", full: "Agnes Pell", title: "keeps the Bottom's books, in crayon", role: "main", body: "normal", age: 85,
    look: "A small old woman in a grid-patterned dress, huge glasses on a chain, a crayon behind each ear, an old ☺ CORP Internal Audit badge pinned on upside down. Carries a fat notebook bound with tape.",
    voice: { kind: "clarinet", pitch: 1.1, rate: 1.0 }, home: "bottom:lostfound", met: "m01_return_to_sender",
    wants: "To open the books: to prove every debt, every Late Fee and every quarter of back pay ☺ CORP collects is a lie written into Option C, and to cancel it. Underneath that, to make what she did on the Final Quarter balance.",
    fears: "Stairs. Not the climbing: the landing on the 41st floor where she stopped. And being found out by the one person she can't stand to be found out by.",
    secret: "She was Rory Cale's boss. At 15:40 on the Final Quarter she found Option C, at 16:00 she showed it to Cale, and at 17:20 she froze on the stairs and sent Cale down alone. She has been feeding the Machine's terminal a note every year on the 31st of December for sixty-one years: \"sorry. A.\" She knew who Change was the moment the barcode on their neck didn't scan.",
    arc: "Guilt kept quiet for sixty-one years, then confessed (m17), then paid. In the Act IV raid she stays in the Spire lobby, behind the same reception desk Cale ran past, and holds it so Change can go up. She doesn't come back. Her last line depends on whether Change forgave her.",
    speech: "Short declarative sentences, lowercase, auditor's vocabulary used for everything (debits, balances, write-offs, \"that doesn't reconcile\"). Asks people if they're hungry instead of asking if they're all right. Never swears. When she's frightened her sentences get shorter, not louder.",
    samples: [
      "you hungry? sit down. you're a debit until you've eaten.",
      "write it down. if it isn't written down, they'll say it didn't happen.",
      "that doesn't reconcile. nothing they send us reconciles.",
      "two hundred and forty-four quarters of back pay. for a job none of us had.",
      "i've audited worse. i can't think of when.",
      "stairs. why is it always stairs.",
      "i sent you up these stairs once. this time i'm staying.",
      "every debt they collect is a lie with a signature on it. i want the signatures.",
    ],
    rel: {
      change: "She knows exactly who they are from the first minute and lets them believe she doesn't. Love and guilt in equal columns.",
      lumps: "Raised him after his parents were put outside the Spire's ration line. He calls her nan. She'd die for him and nearly says so.",
      gordo: "Respects his brain, fears his matches. Taught him to read; regrets teaching him about pressure.",
      dale: "Old friends, old accomplices. They have kept each other's secrets so long they've stopped saying them out loud.",
      hask: "Signed the page Agnes found. Agnes has rehearsed what she'd say to her for sixty-one years.",
      mina: "Knew Mina in the early years of the Bottom and never told her what happened to her sibling. That's the second debt.",
    },
    fate: {
      on_time: "Dead in the Spire lobby. ☺ CORP lists her as a no-show. Her notebook is filed under LOST PROPERTY.",
      late: "Dead in the Spire lobby. The Bottom buries her on the Long Stairs, on the step she'd marked in crayon years ago. Gordo carves the number.",
      off_books: "Dead in the Spire lobby. Her crayon notebook is the first thing published after Option C. The last page says: \"his name was Rory. he was late because of me.\"",
      nap_time: "Asleep behind the reception desk with the shotgun across her knees. Snoring. Alive. This didn't happen.",
    },
  },

  lumps: {
    name: "LUMPS", full: "Ambrose Pell", title: "the Bottom's muscle, cries at sunsets", role: "main", body: "puppet", age: 34,
    look: "A big Off-Spec man: small head, gigantic veiny forearms covered in gold rings, a tie-dye tee, sunglasses pushed up on a rubbery bald scalp, tiny legs. Moves carefully, like the world is made of glass.",
    voice: { kind: "tuba", pitch: 0.6, rate: 0.8 }, home: "bottom:gym", met: "m01_return_to_sender",
    wants: "For his people to be safe. Specifically: his mum, Dot, out of the Gut wall where Overtime's collectors put her two years ago. He would take any deal, from anyone, if it meant nobody else he loves gets fed to the Gut.",
    fears: "Being the reason someone gets hurt. He's so big that every fight he's been in has been the wrong size. Also heights, which he has never told anyone, because he lives on a hill.",
    secret: "He has been sending ☺ CORP a letter every month asking how much it would cost to buy his mum back. Two months ago they answered, with a price and a contact: Pritchard, Hask's assistant. He hasn't told nan.",
    arc: "The loyal friend who might go the other way. In Act III he wants Hask's deal if it saves the Gut's people; if you choose his plan the raid is a rescue, and if you don't, he may take the deal anyway in Act IV (m28) unless you've already freed Dot. If Auntie dies and the Gut's people die with her, he never forgives you.",
    speech: "Slow, short, kind. Apologises before he hits anything and after. Counts things out loud (reps, stairs, people). Says exactly what he means and nothing else, which makes him funnier than everyone and sadder than everyone. Calls Auntie \"nan\".",
    samples: [
      "sorry. *thud*. sorry.",
      "that's a lot of stairs. good for the legs.",
      "nine hundred and ninety-eight. nine hundred and ninety-nine. that's the stairs.",
      "i'm not crying. it's the sunset. it does this.",
      "my mum's in there. in the wall. she says it's warm. she would say that.",
      "you came out of a machine. so what. i came out of a woman who sells soup.",
      "i'll carry it. i'll carry you if you want. i carry nan sometimes.",
      "if they give me her back, i don't care whose side i'm on.",
    ],
    rel: {
      change: "Decides in the first hour that Change is a person, and never changes his mind, even when Change gives him reasons to.",
      auntie: "Nan. The only parent he has left above ground.",
      gordo: "Best friends since they were kids. Gordo plans, Lumps lifts. They have the same argument every week and both mean it.",
      dot: "His mum. He visits the Gut wall on Sundays and brings her soup she can't eat.",
      overtime: "The man who took his mum. Lumps doesn't hate him; he's scared of what he'd do if he let himself.",
    },
    fate: {
      on_time: "If his plan was followed, he runs the Gut's new staff canteen, with his mum on the next shift. It's still a job. If not, his mum is processed into feedstock and he leaves the Bottom; nobody sees him again.",
      late: "If Dot was freed, he builds the first greenhouse on the Long Stairs and grows the green thing. If she wasn't, he won't speak to you; you see him at the sunset wall in the credits, alone.",
      off_books: "Carries his mum down the Long Stairs on his back and rebuilds Sharon's soup kitchen. He's the one who says goodbye on The Commute.",
      nap_time: "Asleep on the sunset wall. Crying slightly. It's the sunset. It does this.",
    },
  },

  gordo: {
    name: "WEE GORDO", full: "Gordon Hale", title: "the Bottom's planner, born late", role: "main", body: "puppet", age: 29,
    look: "Small and hunched, with a huge sagging lipped face, spiky black hair, a pink knitted sweater with the elbows out, and pockets full of chalk, string and stolen ☺ CORP binder clips.",
    voice: { kind: "kazoo", pitch: 1.5, rate: 1.4 }, home: "bottom:gordo_den", met: "m01_return_to_sender",
    wants: "To burn the Spire down. No deals, no new bosses, no restoring anything. He believes, correctly, that every company that comes out of the rubble will do it again, and, wrongly, that nothing worse than ☺ CORP can grow in the gap.",
    fears: "Becoming the thing he's fighting. He has a plan for everything, including what to do if the Bottom ever makes him its boss: leave. He'd never admit he's afraid of being wanted.",
    secret: "He was born in the Spire. His mum went into labour on a shift change, missed her slot, and the Schedule put the whole family outside at 03:00 with a newborn. He knows the Missing Hour exists because he was born in it. He's never told anyone the time on his birth certificate: 03:14.",
    arc: "The radical: right about ☺ CORP, wrong about what comes after. If the raid follows his plan, he gets his fire, and in the LATE ending he's the first to understand what it costs (\"ok. now the hard part.\"). If you don't follow his plan he goes up the Spire with his charges anyway in m28 and you choose whether to stop him.",
    speech: "Fast, cutting, numerical. Talks in plans (\"three ways in, two ways out, one of them's on fire\"). Contempt for ☺ CORP comes out as precision rather than shouting. When he's moved he gets sarcastic; when he's scared he makes a list.",
    samples: [
      "right. listen. three ways in, two ways out, one of them's on fire.",
      "he means steal a car. and watch out for interns.",
      "every company in this city killed the world and then opened a gift shop.",
      "i was born late. cost my family the hill.",
      "you came out of their machine with their barcode. so forgive me if i check your pockets.",
      "a deal is a leash you sign yourself.",
      "plan b is plan a but faster.",
      "ok. now the hard part.",
    ],
    rel: {
      change: "Suspicious first (a ☺ CORP product with a ☺ CORP barcode), then the closest thing he has to an equal. He tests them constantly because he wants them to pass.",
      lumps: "Best friend. Would never say it. Says it once, in Act IV.",
      auntie: "The person who taught him to read and then had to watch him read about bombs.",
      hask: "The woman whose Schedule put his family outside. He has her photo on his wall with the eyes crossed out in crayon he borrowed from Auntie.",
      dale: "Thinks Dale is a coward. Is half right.",
    },
    fate: {
      on_time: "Arrested at 03:00 in the first week, on schedule. The Restoration files him under OVERDUE. If you stopped his charges in m28, he never speaks to you again before they take him.",
      late: "Stands on the Long Stairs looking at the dark city: \"ok. now the hard part.\" Becomes the Bottom's very reluctant organiser; leaves the job every month and comes back every month.",
      off_books: "Hates the cold peace. Takes a seat at the bargaining table anyway, as the Bottom's voice, and spends the epilogue shouting at a Fazzoletti lawyer. He's good at it.",
      nap_time: "Asleep on a pile of maps, still holding a lit match. Someone blows it out.",
    },
  },

  dale: {
    name: "DALE", full: "Dale Ostrowski", title: "fixes the Machine", role: "main", body: "normal", age: 83,
    look: "The sim Dale sixty-one years on: the same overalls with the Dale patch, now patched over themselves, a wrench worn smooth, thick grey eyebrows, a hearing aid made from a radio. He touches the Machine like a horse.",
    voice: { kind: "oboe", pitch: 0.8, rate: 0.7 }, home: "bottom:machine", met: "m01_return_to_sender",
    wants: "To make up for knowing what's in the Machine and keeping quiet for sixty-one years. He wants one thing he can say he did on purpose.",
    fears: "That the Machine is a grave and he's been tending it like a garden. That every voice he's heard through the glass was someone asking him for help.",
    secret: "He was servicing the Machine in the mall basement at 17:30, which is why he lived. ☺ CORP Facilities has paid him ever since, in batteries, to keep it running and to file a maintenance report every month by pager. That's how Hask knows where the prototype went. And Mina Cale asked him every year for forty years to get her sibling out; he told her it was impossible. It wasn't. He just never pressed the button.",
    arc: "The one who let you out, and the one who has to admit why it took so long. He confesses about the reports in m24, after Hask calls through his terminal. In the OFF THE BOOKS ending he leaves the tray empty.",
    speech: "Slow, with long pauses written as \"...\". Talks about the Machine as \"she\" and about everything in maintenance terms (seized, leaking, needs a part). Doesn't finish sentences that hurt.",
    samples: [
      "careful. she bites.",
      "sixty-one years i've been fixing her. she's never once said thank you. ...fair.",
      "i've been fixing this one since tuesday. you'd think that'd be a joke by now.",
      "you hear them, if you put your ear on the glass. they're having a nice day. every day.",
      "it gave change.",
      "the batteries. yeah. they pay me in batteries. forty years of batteries. look at them. that's what i cost.",
      "she asked me every year. every year i said i couldn't. ...i could.",
      "you're not a refund. you're a recall.",
    ],
    rel: {
      change: "Pressed the button. Feels like their father and their jailer at once, and acts like neither.",
      auntie: "Fifty years of shared silence. He knows what she did on the stairs. She knows what he does with the pager.",
      mina: "Owes her the most and has told her the least. If she comes out of the Gut, she slaps him. He says thank you.",
      hask: "His real employer. He's never met her. He's seen her signature on every battery delivery.",
    },
    fate: {
      on_time: "Keeps the Machine running for the Restoration, now with a proper salary and a clean uniform. He stops putting his ear to the glass.",
      late: "Sits with the Machine in the dark when the power dies. She keeps humming. Nothing can kill her.",
      off_books: "Opens the sims to the dead as their own place, and leaves the tray empty. \"no more returns.\"",
      nap_time: "Asleep against the Machine with his ear on the glass. Smiling.",
    },
  },

  mina: {
    name: "MINA", full: "Mina Cale", title: "waited at the school gate", role: "main", body: "normal", age: 70,
    look: "A wiry old woman with a grey braid, a hand-knitted cardigan, Mall Rat climbing gloves she never takes off, and on her wrist a faded Big Value wristband that isn't hers. In the Gut, half grown into the digester wall up to her waist.",
    voice: { kind: "recorder", pitch: 1.2, rate: 1.1 }, home: "gut:digester_wall", met: "m04_clocking_in",
    wants: "For her sibling to come and get her. She stopped wanting it at about forty and started again at about sixty-five, when the Machine started glitching.",
    fears: "That Rory didn't come because Rory didn't want to. She's had sixty-one years to build that fear and it's very well built.",
    secret: "At the Stampede, nine years old, she lifted a five-year-old boy into an air vent and climbed in after him. That boy is Wristband, who runs the Mall Rats. She was the first Mall Rat. She left the mall at twenty to find the Spire and got as far as the Bottom.",
    arc: "The person the player can save, or not. Seen in C4 as an old woman loaded onto the truck who says \"rory?\". Named by Wristband in m10. Found in the Gut wall in m20. If freed she becomes the one person who remembers Rory, and her scenes with Change are the warmest in the game, and the hardest at high Drift, when Change can't remember her at all.",
    speech: "Brisk and dry, a Mall Rat's economy of words. No self-pity. She talks to Change like they're still twenty-two and she's still nine, and keeps catching herself.",
    samples: [
      "rory?",
      "you're late.",
      "i'm seventy. you're twenty-two and made of plastic. we'll call it even.",
      "i waited at the gate till the teacher made me go. then i waited in the vents. then i waited here.",
      "milo still wears that wristband? silly boy. it's mine. i gave it to him so the grown-ups would know he was lost.",
      "the wall's warm. that's the worst thing about it. you stop minding.",
      "don't you dare apologise. you were coming. i know you were coming.",
      "you don't remember me. that's all right. i remember enough for both of us.",
    ],
    rel: {
      change: "Her big sibling, sixty-one years late. She forgives them in one second and spends the rest of the game making sure they forgive themselves.",
      wristband: "Her little brother in every way but blood. She held his hand in the dark for three days.",
      dale: "Asked him for help every year for forty years. Doesn't know yet that he could have.",
      auntie: "Knew her for years in the Bottom and never knew she'd been Rory's boss. When she finds out, she's quiet for a long time.",
      dot: "Her neighbour in the wall. They've been keeping each other awake so neither of them dissolves.",
    },
    fate: {
      on_time: "If freed: given a pension and a flat on Corp Hill, which she refuses; she goes back to the vents with Milo. If not: processed as feedstock. Her name is in Hask's ledger.",
      late: "If freed: teaches the Bottom's kids to climb, and sits with Change on the Long Stairs every evening at 17:30, \"so you're on time for once\".",
      off_books: "If freed: walks with Change to the edge of The Commute and lets them go. \"go on. i'm good at waiting. i'll be terrible at it this time.\"",
      nap_time: "Asleep in a vent with Milo, both of them snoring in the same rhythm.",
    },
  },

  hask: {
    name: "MARION HASK", full: "Marion Hask", title: "Chief Punctuality Officer, ☺ CORP", role: "villain", body: "cyborg", age: 101,
    look: "Tall, straight-backed, a white suit buttoned to the throat, silver hair in a perfect knot, a surgical scar under her collar. Under the suit: a body of other people's organs held in a clear corporate frame, all of them still working, each tagged with a name.",
    voice: { kind: "glass", pitch: 1.0, rate: 0.95 }, home: "corphill:spire_top", met: "m24_the_split",
    wants: "Order. After the Final Quarter she watched the city starve in the dark while the Spire, rationed to the minute, survived. She believes the Schedule is mercy, that the dead won't mind working, and that the Restoration will feed everyone. She wants to restart the world on time, once, properly.",
    fears: "The dark. Riots. A crowd at a door. Being late, which to her has always meant people dying.",
    secret: "At 17:10 on the Final Quarter, Remainder Industries phoned her: the revised numbers hit target by 0.5%. The launch was no longer necessary. She launched anyway, because by then the write-off of every wage, pension and debt was worth more than hitting the number. She also wrote the backup clause: the dead were always meant to be retained as a workforce. And she keeps a ledger of every donor whose organ is in her body, and reads the names every night \"for continuity\".",
    arc: "A villain with a point and a body made of the people she sold. She's offered as a voice of reason in C14, calmly right about the famine; the pages slowly show what her order cost. In Act V the suit opens and you see it. She never begs. Her last scene depends on the ending: she outlives the Clock (LATE), she wins (ON TIME), or she has to sit at a table with the Bottom (OFF THE BOOKS).",
    speech: "The only character who speaks in full sentence case, with capitals and full stops, like a memo. Never uses contractions. Exact times, never approximations. Never raises her voice. Never insults anyone; she describes them.",
    samples: [
      "Good evening. You are four minutes early. I appreciate that.",
      "The Restoration feeds everyone. The dead do not mind working. I have asked them.",
      "You could have a name, a job, and a life that does not end. Or you could go back in the bin.",
      "I was there for the Long Dark. You were in a vending machine.",
      "You were terminated at 17:29 and 41 seconds. The Schedule does not load into people who do not work here. That is the only reason you are free.",
      "Hitting the number would have cost us more than ending the world. I did the arithmetic. I am very good at arithmetic.",
      "Every one of them is written down. I read them every night. Somebody should.",
      "You would make a perfect employee.",
    ],
    rel: {
      overtime: "Her first manager, when she was a temp. She reloads him because he is the only person who has never once asked her why.",
      change: "The prototype she was going to delete, and the proof that the Restoration has a flaw. She'd rather hire the flaw than lose the argument.",
      auntie: "Remembers Agnes Pell as a promising auditor. Signed the order that put her outside the Spire's ration line.",
      pritchard: "Trusts him the way she trusts a clock: completely, and without thinking about it.",
      bishop: "Her supplier. She finds him disgusting and has never once missed a delivery.",
    },
    fate: {
      on_time: "Retires on schedule, in a perfect white office, with her ledger. Her organs are renewed every quarter from the Bottom's former residents.",
      late: "Outlives the Clock by eleven days in a dark office, reading the ledger by candlelight. The Bottom finds her sitting upright at 17:30 on the twelfth day. The ledger is open at the last name.",
      off_books: "Sits at the bargaining table in the ruins, across from the Bottom, and is made to read the ledger out loud. It takes four days.",
      nap_time: "Asleep at her desk with her head on the ledger. Late for the first time in her life.",
    },
  },

  overtime: {
    name: "MR. OVERTIME", full: "Edwin Sallow", title: "Head of Timekeeping Enforcement. Employee #1", role: "villain", body: "cyborg", age: null,
    look: "A 4.5 m corporate cyborg in a grey suit stretched over pistons, a huge punch-clock in his chest (the clock face is his heart and it ticks loudly), two heavy-duty stapler arms, a small human head sunk between his shoulders with a stretched puppet smile and a desk-lamp visor, a lanyard of ninety years of employee-of-the-month badges, brogues the size of cars, a bungee-cord tie. He steams when angry.",
    voice: { kind: "dialtone", pitch: 0.7, rate: 0.9 }, home: "corphill:museum", met: "m04_clocking_in",
    wants: "To do his job. To clock everyone in on time, collect what's owed, and go home at 17:30.",
    fears: "Nothing he knows about. Underneath: the door. Every reload ends with him standing at the lobby door at 17:30 with his coat on, and he doesn't know why that image makes his hands shake.",
    secret: "He is the first recording ☺ CORP ever made and the first ever loaded into a body. He's reloaded from his last pre-war backup every time he dies, so he has never learned the world ended. He killed Rory Cale at 17:29 because running was against policy. At 17:30 he was at the door, coat on, on the phone to his wife June: it was their fortieth anniversary and he'd promised to be home. He never went home.",
    arc: "Your mirror: what you become if you sign. Over four fights he slowly remembers he died. His lines change, his moves glitch, and by the Lates he stops mid-fight to ask why he didn't go home. In the final fight, with all six of his memory fragments, you can show him the end of his shift and he clocks out.",
    speech: "Polite, tired, bureaucratic. Lowercase. Speaks in policy and precise durations. Never threatens; informs. Repeats himself when he glitches. In later fights his sentences break off and restart, like a tape.",
    samples: [
      "this will only take a minute. it will take exactly a minute.",
      "the bottom. two hundred and forty-four quarters of back pay. i'm here to collect.",
      "you're running. that's against policy.",
      "you're absent. everyone's absent. i don't know where everyone goes.",
      "please hold still. you're being processed.",
      "i was going home at 17:30. why didn't i go home?",
      "june's making the... june's making... she's making something. it's our... it's our something.",
      "first time i've left on time.",
    ],
    rel: {
      hask: "His best hire. He trained her when she was a temp. He's proud of her. He doesn't know what she did.",
      change: "To him, at first, a deleted employee who shouldn't be clocking anything. Later, the only person who knows something about him that he doesn't.",
      june: "His wife. Dead sixty-one years. Still waiting for him, as far as he knows.",
      founder: "He was hired by the cat. He is the only employee who has always known the founder is a cat, and has never thought it was strange.",
    },
    fate: {
      on_time: "If talked down: clocked out, and then re-hired by the Restoration the next morning, from the backup. He's back on shift by 09:00. If destroyed: reloaded the next morning anyway. You have his job; he has yours.",
      late: "If talked down: sits on the Bottom's stairs at sunset, an old man in a suit with nowhere to be. Every evening at 17:30 he stands up, then sits back down. If destroyed: the Clock is gone, so nothing reloads him. That's the end of Edwin Sallow.",
      off_books: "If talked down: the Bottom finds him on its stairs at sunset, an old man in a suit. He asks the kids what day it is. They say Wednesday. He seems pleased. If destroyed: his backup goes into the free sims, where he works a normal day and goes home at 17:30 to a house June was never recorded in. Some people think that's kind. Dale doesn't.",
      nap_time: "Asleep standing up, steaming gently, a cat on his visor.",
    },
  },

  pritchard: {
    name: "PRITCHARD", full: "Owen Pritchard", title: "executive assistant to the Chief Punctuality Officer", role: "main", body: "normal", age: 41,
    look: "A thin arcology-born man in a too-big ☺ CORP blazer, a headset, three watches on one arm (one per time zone that no longer exists), and a tablet showing Hask's calendar.",
    voice: { kind: "flute", pitch: 1.3, rate: 1.3 }, home: "corphill:spire_top", met: "m24_the_split",
    wants: "For Ms. Hask's day to go to plan. Underneath that, for anything in his own life to go to his plan. He has never had a minute of unbooked time.",
    fears: "Being outside. He's been outside the arcology twice and both times he was sick from the smell of the rain.",
    secret: "He answers Lumps' letters. He has been quietly lowering the price of Dot Pell for six months, and he wrote the Restoration's staffing table: he knows exactly how many people from the Bottom are on it.",
    arc: "A quiet conscience inside the machine. In m24 he's the voice that books your call with Hask. In Act IV, if Lumps' letters were answered kindly (flag pritchard_ally), he leaks the elevator override code and the Twins' rotation. In the endings he either keeps the Schedule or walks out of the Spire for the first time.",
    speech: "Fast, nervous, padded with calendar language (\"she has a four-minute window\", \"can i put you in for 03:00\"). Apologises to doors. When he finally says something true, he says it in one breath.",
    samples: [
      "ms. hask has a four-minute window at 22:16. please be on time. please.",
      "sorry. sorry, that's my 14:00 alarm. and my 14:01 alarm.",
      "can i put you in for later? there isn't a later. i'll make one.",
      "i've never had lunch. i've had lunch slots.",
      "the staffing table has eleven thousand four hundred and two names from the bottom on it. i typed every one.",
      "the override is 1730. of course it's 1730.",
    ],
    rel: {
      hask: "Worships her and is terrified of her and is starting, very slowly, to understand her.",
      lumps: "His pen pal. He has never met Lumps and thinks of him as the kindest person in the city.",
      change: "The prototype on his calendar. He's booked their deletion three times and postponed it three times.",
    },
    fate: {
      on_time: "Runs the Restoration's calendar. Ten thousand Change copies on it. He books himself one minute of unscheduled time per year and spends it crying in a supply cupboard.",
      late: "Walks out of the Spire in the first dark morning and down the hill. Gets rained on. Isn't sick.",
      off_books: "Becomes the bargaining table's minute-taker. He's very good at it. He books everyone lunch. Real lunch.",
      nap_time: "Asleep under his desk, all three watches beeping.",
    },
  },

  cale: {
    name: "R. CALE", full: "Rory Cale", title: "junior analyst, Internal Audit (in the flashbacks)", role: "flashback", body: "normal", age: 22,
    look: "In the sims: a young ☺ CORP analyst in a cheap grey suit with the sleeves too long, a lanyard reading CALE R. 4417, a backpack with a primary-school keyring on it (a felt strawberry), scuffed trainers they change into at 17:00.",
    voice: { kind: "clarinet", pitch: 1.15, rate: 1.2 }, home: "sims:spire_60", met: "m09_workday_1600",
    wants: "On the last workday: to pick their little sister Mina up from Hillside Primary at 17:30. Then, from 16:00: to get Option C out of the building before it can happen.",
    fears: "Being late for Mina. Being the kind of person who keeps their head down. They've been both, and they're about to be neither.",
    secret: "None. Cale is the least secretive person in the story. That's the point.",
    arc: "Played in four flashbacks, 16:00 to 17:29. A nervous junior who's never broken a rule becomes someone who runs down sixty floors with the end of the world in a backpack. Their calendar entry for 17:30 says \"M\", which ☺ CORP logged as a meeting. It was the school gate.",
    speech: "Young, quick, self-deprecating, says \"sorry\" and \"ok, ok, ok\" when panicking. Talks to themselves on the stairs. Kind to everyone, including the people in their way.",
    samples: [
      "ok. ok, ok, ok. it's fine. it's a printer. printers are fine.",
      "i'm picking my sister up at half five. it's in my calendar. it's the only thing in my calendar.",
      "agnes, this is a launch order. this is a launch order with a spreadsheet.",
      "sorry! sorry. excuse me. end of the world, sorry.",
      "forty-one floors. you can do forty-one floors. you did forty-one floors this morning. in the lift. it counts.",
      "mina, i'm coming. i'm coming. i'm coming.",
    ],
    rel: {
      agnes: "Their boss, two years older, the smartest person they know. Cale would follow her anywhere, and does, until she stops.",
      mina: "Nine years old. Cale has been her parent since their mum went into the Long Ward. She's the only appointment that matters.",
      overtime: "The nice old man in the lobby who once found Cale's lanyard and gave it back without writing them up.",
    },
    fate: {
      on_time: "Their name goes on a lanyard. The lanyard goes on ten thousand bodies.",
      late: "Remembered by Mina, and by whoever Change chooses to be.",
      off_books: "The name on the last page of Auntie's notebook.",
      nap_time: "This didn't happen.",
    },
  },

  agnes: {
    name: "AGNES", full: "Agnes Pell (age 24)", title: "senior auditor, 60th floor (in the flashbacks)", role: "flashback", body: "normal", age: 24,
    look: "Auntie Spreadsheet at twenty-four: the same huge glasses, sharper, a grid-patterned blazer, a ☺ CORP Internal Audit badge pinned on the right way up, a red pen she taps on her teeth.",
    voice: { kind: "clarinet", pitch: 1.25, rate: 1.15 }, home: "sims:spire_60", met: "m09_workday_1600",
    wants: "To be right, and to be promoted for it. Then, at 15:40, to not be the only person who knows.",
    fears: "That she's the kind of person who stops on a landing. She finds out at 17:20.",
    secret: "She chose Cale to carry the copy because Cale was the person she trusted most and the person she'd miss least on her team's headcount. She's hated herself for both halves of that sentence for sixty-one years.",
    arc: "Seen in three flashbacks: confident at 16:00, desperate at 16:45, frozen at 17:20. Her last line in F3 is the line Auntie can't say in the present until m17.",
    speech: "Brisk, clever, slightly showing off, with an auditor's habit of reading numbers aloud. Uses the red pen as a pointer. Her fear makes her talk faster, and then stop.",
    samples: [
      "cale. close the door. no, the other door. both doors.",
      "look at slide thirty-one. read me the number in the corner. out loud.",
      "that's not a forecast, that's a target list. those are cities.",
      "you're faster than me. you're faster than everyone. that's not a compliment, it's logistics.",
      "i'm right behind you. i'm... i'm right behind you.",
      "go. go. i'll... go.",
    ],
    rel: {
      cale: "Her favourite. She'd never say so on a performance review.",
      hask: "The executive she admires most on the 100th floor, until 15:40.",
    },
    fate: {
      on_time: "See Auntie Spreadsheet.", late: "See Auntie Spreadsheet.", off_books: "See Auntie Spreadsheet.", nap_time: "See Auntie Spreadsheet.",
    },
  },

  june: {
    name: "JUNE", full: "June Sallow", title: "on the phone, 17:30", role: "flashback", body: "normal", age: 63,
    look: "Never seen. A voice on a lobby phone, and a lunchbox note in neat handwriting.",
    voice: { kind: "cello", pitch: 1.0, rate: 0.9 }, home: null, met: "m31_fully_billable",
    wants: "For Edwin to come home on time, once, for their fortieth anniversary.",
    fears: "Nothing she says. She's been married to a punctual man for forty years; she's learned to say what she wants plainly.",
    secret: "She's made his mother's stew. It's on the table at 17:30. She's put the candles in.",
    arc: "Heard only in Overtime's memory fragments. The last fragment is her on the phone at 17:30: \"are you coming home?\"",
    speech: "Warm, wry, plain. Calls him \"ed\".",
    samples: ["are you coming home?", "ed. it's half five. the stew won't wait and neither will i.", "don't be late tonight. it's our forty. love, j.", "i've put the candles in. don't make me light them on my own."],
    rel: { overtime: "Her husband of forty years. The most punctual man she ever met, and never once on time for her." },
    fate: { on_time: "Dead sixty-one years.", late: "Dead sixty-one years.", off_books: "Dead sixty-one years. She was never an employee, so the Machine never recorded her. She's the one thing nobody can give back.", nap_time: "This didn't happen." },
  },
};
