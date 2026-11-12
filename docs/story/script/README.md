# JANKFIRE: OVERDUE: the script

The complete story script, generated from the data the game loads (`shared/story/content/`). The data is the source of truth: edit it, then run `node tools/story/render_script.mjs`. `node --test tests/story/content.test.mjs` checks every reference resolves and that these docs are up to date.

Start with [CANON.md](CANON.md): the timeline, why Change is free, the six pages, the reveal order.

| file | what | size |
|---|---|---|
| [CAST.md](CAST.md) | the cast bible: 56 characters | 20024 words |
| [ACT_1.md](ACT_1.md) | Act 1: "Please Take Your Item": 6 missions | 12644 words |
| [ACT_2.md](ACT_2.md) | Act 2: "Hostile Takeovers": 12 missions | 14161 words |
| [ACT_3.md](ACT_3.md) | Act 3: "Off the Clock": 8 missions | 9607 words |
| [ACT_4.md](ACT_4.md) | Act 4: "Quarterly Review": 5 missions | 5887 words |
| [ACT_5.md](ACT_5.md) | Act 5: "Overdue": 2 missions | 4678 words |
| [ENDINGS.md](ENDINGS.md) | ON TIME, LATE, OFF THE BOOKS, NAP TIME | 4059 words |
| [BOSSES.md](BOSSES.md) | 25 fights, 21 named bosses | 21051 words |
| [SIDE_QUESTS.md](SIDE_QUESTS.md) | 48 side questlines, 15 activities | 15562 words |
| [IMPLANTS.md](IMPLANTS.md) | 56 implants (17 secret) and the Drift rules | 5383 words |
| [LOOT.md](LOOT.md) | 8 brands, 44 named legendaries | 3384 words |
| [../MECHANICS.md](../MECHANICS.md) | the mechanics bible: 48 mechanics, the grapple, coverage | 9477 words |
| [../GRUDGES.md](../GRUDGES.md) · [../GRUDGE_LEDGER.md](../GRUDGE_LEDGER.md) | the Grudge Ledger: enemies who remember you, 33 adaptations | 5606 words |
| [COLLECTIBLES.md](COLLECTIBLES.md) | 69 collectibles in 6 sets | 3189 words |

**Total: about 135k words, 33 main missions, 39 scenes.**

## Main story at a glance

| # | act | mission | logline |
|---|---|---|---|
| 1 | 1 | PLEASE TAKE YOUR ITEM | You win a training sim, the camera pulls out through the Machine's glass, and for the first time in sixty-one years the Machine gives something back: you. |
| 2 | 1 | SAUCE RUN | The Bottom trades soup to Gristle & Sons for medicine. Steal a car, cross the edge of The Commute without spilling it, and survive the Unpaid. |
| 3 | 1 | SOMETHING'S DIGESTING | It's Sunday. Lumps visits his mum in the Gut, and the Choir tells you where Gristle & Sons gets its feedstock: ☺ CORP sells it the people who fall behind on their back pay. |
| 4 | 1 | CLOCKING IN | Mr. Overtime comes down the Long Stairs to collect two hundred and forty-four quarters of back pay, in people. First nemesis fight. |
| 5 | 1 | SECOND STOMACH | A Meat Mechanic installs the piece of Overtime's heart in your chest. Implants unlocked. For a second you remember a lobby, a pair of running shoes, and the time: 17:29. |
| 6 | 1 | TICKETS, PLEASE | The only other way into the Gut is the commuter line under the hill. Nobody takes it, because the tunnel eats. Four of you go in. The thing that follows you out is wearing the company's face. |
| 6 | 2 | OPTION C | Auntie lays out her wall of evidence: six companies signed the end of the world, each one kept its page, and with all six she can prove every debt they collect is a lie. |
| 7 | 2 | AN OFFER | In Pinstripe the Don makes you an offer you could refuse, and his jesters make you a different one. |
| 8 | 2 | FAMILY BUSINESS | The Family's page is up in Villa Fazzoletto. So is whoever works the Don's strings. |
| 9 | 2 | THE LAST WORKDAY: 16:00 | The first page unlocks a sim nobody has ever played: you, as R. Cale, on the 60th floor of the ☺ Spire, on the last afternoon of the world. |
| 10 | 2 | LOST CHILD | In the Big Value mall's air vents, the lost child from the Stampede is sixty-six now. He reads the barcode on your neck and goes white. |
| 11 | 2 | NO REFUNDS | The doors open at 09:00, like they have every day since the Stampede, and every lost cart in the city comes for you. |
| 12 | 2 | THE LAST WORKDAY: 16:45 | 16:45 on the last workday. Copy the end of the world onto a tape drive that is very, very slow. |
| 13 | 2 | RUSH HOUR | On the Spiral Freeway, in a paper storm, Mr. Overtime chases your car on foot, at exactly the speed limit. |
| 14 | 2 | THE PRICE OF EVERYTHING | Number Works prints the city's prices every morning at 06:00. The union stamped with the unwanted numbers wants a vote. Management wants a strike broken. |
| 15 | 2 | ROUNDING DOWN | Foreman Remainder comes down for the print run, and the page is in his face. |
| 16 | 2 | THE LAST WORKDAY: 17:20 | Sixty floors of Stairwell B at 17:20, with the sirens going and the clocks starting to crack. |
| 17 | 2 | MINUTES OF THE MEETING | 17:29. Cale reaches the lobby with the copy, and Mr. Overtime is waiting. Then Auntie tells you the truth. |
| 18 | 3 | NINE KILOMETRES | With Overtime's lanyard you can pull ☺ CORP's master Schedule off the network. Printed out, it's nine kilometres long, and it has a hole in it. |
| 19 | 3 | ORGAN DONOR | Gristle & Sons' page of Option C was stolen and sold. Doctor Upsell bought it, because he knew what it really was: a patent. |
| 20 | 3 | THE MISSING | Pages first, then mum. It's then. Go into the Gut for the nine, and for Mina. |
| 21 | 3 | PROPERTY VALUES | Evergreen Acres is the only district on the Schedule with something booked at 03:00: 'CHARGE'. Every window has a mannequin family waving. |
| 22 | 3 | THE WAITING ROOM | In the Lates it has been the same Tuesday for sixty-one years. Pauline from Accounts knows every second of it, and she knows a man who has been late for the same meeting twenty-two thousand times. |
| 23 | 3 | WORKFORCE RESTORATION | At 03:00, in the hour nobody's booked into, a door opens in the sky over the Lates. Behind it is what ☺ CORP has been planning for the dead. |
| 24 | 3 | THE SPLIT | Marion Hask calls you on the Machine's own terminal with an offer, and the Bottom splits three ways over what to do about it. |
| 25 | 3 | TUESDAY AGAIN | Overtime comes for you in the Lates, where every minute happens again, and every time it happens he remembers a little more. |
| 26 | 4 | EXIT INTERVIEW | At the edge of the world, the Tall Guy From HR can't be killed in his own forest. He just wants somebody to sign. |
| 27 | 4 | NEGATIVE SPACE | The deal closes today. Vacancy's Closing Agent is selling the Bottom to the void, and her page of Option C is the deed. |
| 28 | 4 | THE PLAN | Whatever you chose at the split, now it has to be built: a headcount, a demolition, or a print run. And whoever you didn't choose does something anyway. |
| 29 | 4 | 03:00 | At 03:00, in the one hour nobody is booked into, the whole Bottom climbs Corp Hill with every ally you earned. |
| 30 | 4 | THE LOBBY | The same lobby as 17:29. The Twins hold the elevator. Auntie sits down behind the reception desk. |
| 31 | 5 | OVERDUE | Mr. Overtime, wired into the Master Clock, holds the door one last time. If you found the end of his shift, you can give it back to him. |
| 32 | 5 | FULLY VESTED | Marion Hask shows you the last page and the body under her suit, and then it's your choice. |
