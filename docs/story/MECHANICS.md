# OVERDUE mechanics bible

_Generated from `shared/story/content/mechanics.js`, the `mechanic` hooks on every mission and side quest, and the boss fight layer (`boss_fights.js`). Edit the data, then run `node tools/story/render_script.mjs`._

Everything here is a mechanic the game already has (the `src` column says where). The story is built to use all of it, and it teaches each one in a mission or side quest, usually with a joke. The grapple is the star: every district has a swing route, and every boss arena has grapple points.

## Coverage

| mechanic | kind | taught in | main missions | side quests | boss fights |
|---|---|---|---|---|---|
| THE GRAPPLE | movement | PLEASE TAKE YOUR ITEM | 22 | 21 | 25 |
| WASHING-LINE ZIPLINES | movement | PLEASE TAKE YOUR ITEM | 1 | 3 | 2 |
| SLIDE | movement | SOMETHING'S DIGESTING | 4 | 1 | 3 |
| BHOP AND INFINITE MOMENTUM | movement | RUSH HOUR | 3 | 1 | 1 |
| ROCKET AND SHOTGUN JUMPS | movement | THE PRICE OF EVERYTHING | 3 | 2 | 7 |
| VOID EDGES | movement | EXIT INTERVIEW | 2 | 2 | 2 |
| LOOPS | movement | THE WAITING ROOM | 2 | 2 | 2 |
| ON TIME | movement | 03:00 | 1 | 2 | 1 |
| MARBLE SLIP | weapon | LOST CHILD | 2 | 3 | 3 |
| BANANA PEELS | weapon | TWO JESTERS | 1 | 3 | 4 |
| KATANA PARRY AND GROWTH | weapon | FAMILY BUSINESS | 2 | 0 | 4 |
| SCALES OF JUSTICE (VERDICTS) | weapon | CLAIMS DEPARTMENT | 2 | 3 | 4 |
| THE REDLINE | weapon | CLOCKING IN | 3 | 0 | 3 |
| SOAK AND SHOCK | weapon | CLOCKING IN | 2 | 2 | 4 |
| FROST AND SHATTER | weapon | THE WAITING ROOM | 2 | 0 | 4 |
| TV REMOTE (PAUSE / REWIND) | weapon | GROUNDHOG LUNCH | 3 | 1 | 5 |
| THE SHREDDER | weapon | NINE KILOMETRES | 1 | 0 | 1 |
| THE LASSO | weapon | ONE SHOE GUY | 4 | 6 | 6 |
| SHOPPING CART CANNON | weapon | LOST CHILD | 2 | 1 | 1 |
| SHOVE AND KNOCKBACK | weapon | NEGATIVE SPACE | 3 | 3 | 8 |
| FIRE (THE CIGARETTE, FLAME ARROWS) | weapon | SECURITY DEPOSIT | 1 | 2 | 6 |
| NAIL TO THE WALL | weapon | ORGAN DONOR | 1 | 1 | 1 |
| BANK SHOTS | weapon | CARRY THE ONE | 2 | 1 | 4 |
| BIG LASER POINTER | weapon | 03:00 | 1 | 0 | 1 |
| CARD DECK | weapon | CLAIMS DEPARTMENT | 0 | 2 | 1 |
| BLOOD CROSS | weapon | THE MISSING | 2 | 0 | 2 |
| BLOOD DRIVE | weapon | TICKETS, PLEASE | 1 | 0 | 1 |
| INSTANT CAMERA | item | PRICE CHECK ON AISLE EVERYTHING | 3 | 4 | 1 |
| POP QUIZ | item | ROUNDING DOWN | 1 | 1 | 1 |
| NIGHT VISION GOGGLES | item | WORKFORCE RESTORATION | 1 | 3 | 2 |
| SPEED TRAP (RADAR GUN) | item | RUSH HOUR | 1 | 0 | 1 |
| BUBBLE WAND | item | TWO JESTERS | 0 | 1 | 2 |
| RUBBER DUCK (BLACK HOLE) | item | HAIRBALL | 0 | 2 | 1 |
| PARTY POPPER | item | MANDATORY FUN | 0 | 2 | 2 |
| REVERSE CARD | item | CLAIMS DEPARTMENT | 0 | 1 | 2 |
| FRAGS AND SMOKE | item | SAUCE RUN | 1 | 3 | 4 |
| OVERDRIVE RIG | streak | LEG DAY | 1 | 1 | 2 |
| WRECKING BALL | streak | HAIRBALL | 0 | 1 | 1 |
| MOON BOOTS | streak | UNLUCKY 13 | 0 | 1 | 1 |
| CHICKEN STRIKE | streak | MANDATORY FUN | 0 | 2 | 2 |
| SPY SATELLITE | streak | UNLUCKY 13 | 0 | 2 | 2 |
| GIANT DUCK | streak | MALL WALKER | 0 | 1 | 2 |
| SPINBOT | streak | ARCADE LEGEND | 0 | 1 | 1 |
| SCYTHE RIFLE | streak | BELLY BUTTON | 0 | 1 | 1 |
| CARS AND TRAFFIC | vehicle | SAUCE RUN | 5 | 12 | 5 |
| LATE FEES | system | AN OFFER | 2 | 0 | 1 |
| BIO-IMPLANTS | implant | SECOND STOMACH | 3 | 1 | 3 |
| HYPE | system | SOMETHING'S DIGESTING | 1 | 0 | 1 |

## The grapple

A 90 m rope that winds you toward the point as a pendulum: you keep momentum, swing in arcs, and a grapple jump (let go on the upswing, looking the way you swing) flings you on with a hop. Grappling a person tugs them toward you. Skins change the rope and hook.

### Swing routes (one per district)
- **THE BOTTOM:** THE SOCK LINE: forty-one washing lines from the Lost & Found to the Long Stairs, roof to roof, never touching the ground (the Washing Line Run).
- **THE GUT:** THE RIB RUN: swing the rib arches over Peristalsis Avenue and bounce the lungs between them, down to the Big Stomach's rim.
- **PINSTRIPE:** THE STRINGS: the marionette strings hanging over the district are free, infinite-length swings; ride them from Respect Bridge to the Villa roof.
- **THE CHECKOUT:** THE DOME: the cracked glass dome's ribs over the whole mall, from the Big Doors to the Food Court Colosseum.
- **NUMBER WORKS:** THE DIGIT LINE: grapple digit to digit along the conveyors to the Smokestacks and up their ladders.
- **CHROME GRISTLE:** THE SIGN LINE: neon sign letters are grapple points; shooting letters re-spells signs (and changes prices) as you pass.
- **EVERGREEN ACRES:** THE GUTTER RUN: porch gutters and basketball hoops around the cul-de-sac, sprinklers launching you between them.
- **THE LATES:** THE STRIP LIGHTS: ceiling strip-light rails through the repeating offices, falling through floors to build speed.
- **THE MARGINS:** THE CANOPY: pine branches above the Scary Forest, ending in a swing over the Edge.
- **CORP HILL:** THE GONDOLAS: window-cleaning gondolas on the Spire's outside, timed to the clocks (On Time).
- **THE COMMUTE:** THE GANTRIES: overhead road signs along the Ring Road; swing from sign to sign over the jams.

### Shortcuts
- the Long Stairs: a rope from the Lost & Found's roof to the Gut border saves 1,000 steps (Lumps refuses on principle)
- Big Escalator bypass: the dome rib over it gets you to Corp Hill's edge without employee access
- the Villa's ceiling hatch (Larry's crawlspace has a grapple hook on the end)
- the Spire's service shaft: from 41 to 90 on the cables (Act IV only; the elevator is quicker but sadder)

### Secrets
- Sock Tendons: ride all 41 washing lines in one go (sec_sock_tendons)
- Pendulum Inner Ear: twelve full swings on the Master Clock's pendulum, post-game (sec_pendulum_ear)
- the thirteenth wok (Satellite Ear) is only reachable by grapple from the gym chimney
- the Missing Texture's staircase to nowhere ends at a Lost Property tag only a grapple jump reaches (a bonus Lost Property item)

### Chases
- Overtime 2 on the Spiral Freeway (grapple his tie and get towed)
- the living shoe down Peristalsis Avenue
- the Perpetual Tuesday up Tuesday Tower
- Reply All through the Spire's pneumatic tubes

### Swinging fights
- Overtime 1 on the Gut border roofs (his staples become grapple points)
- the Tall Guy in the canopy
- Overtime 4 on the pendulum and gears
- the convoy (rig to rig on gantries)
- Penny Plot (falling chunks over the void)

### Grapple puzzles
- rip armour plates off (Overtime 1 and 2, Upsell's arms, the Cart Mother's carts)
- yank enemies off ledges and roofs (the grapple's tug; Hook Hand makes it a void kill)
- zip to weak points (Unlucky 13's crown, Overtime 4's back cables)
- pull things: a meatball, a tooth, a house, a briefcase, a cable out of a wall

### Races
GRAPPLE TIME TRIALS (activities.js grapple_trials): one signature route per district, timed, with bronze / silver / gold ghosts; the Washing Line Run is the first (sq_bottom_line_run).

### Upgrades
- Tendon Line (shop, arms): +30% range, faster reel
- Hook Hand (shop, arms): yanking people is twice as strong and off-ledge yanks count as void kills
- Peristaltic Reel (shop, guts): harder grapple-jump flings, double HYPE from long grapples
- Sock Tendons (secret, legs): faster rail riding, chain grapples in the air
- Pendulum Inner Ear (secret, head): perfect swing momentum
- The First Staple (legendary nailgun): pinned enemies become grapple points
- The Washing Line (legendary lasso): peg enemies out to dry and ride the rope

### Grapple points in every boss arena
- **MR. OVERTIME** (THE GUT BORDER GATE): washing-line poles on every roof (swing between them); the truck's loading crane; his own staples: every staple that misses stays in the wall as a grapple point
- **MR. OVERTIME** (THE SPIRAL FREEWAY): overhead gantry signs on every loop; the cars he staples together (each barricade is a grapple anchor); his bungee-cord tie: grapple it to ride behind him like a water-skier
- **MR. OVERTIME** (THE LATES CAR PARK): strip-light rails on every ceiling; the stairwell's handrail spiral; parked cars (they reset every loop, so a car you shoved comes back)
- **MR. OVERTIME** (THE MASTER CLOCK): the pendulum (ride it across the whole arena); gear axles everywhere; the cables in his back (grapple them to pull them out: each one slows the Clock)
- **MR. OVERTIME** (THE PUNCTUALITY MUSEUM): the mezzanine rail; the Pendulum of Punctuality; the hanging FIRST TIME CARD exhibit
- **MR. DEPOSIT** (THE DEPOSIT PILE): washing lines (ride them round the pile); his key-ring chains; chimney stacks on the houses
- **THE STOMACH BISHOP** (THE BIG STOMACH): the rib arches over the lake (swing across it); the femur baton (yank it out of his hand); the Choir's bell ropes on the rim
- **THE FOUNDING PARTNER** (BEHIND THE BELLY BUTTON): the arms themselves (they're grapple rails while they're still); his reading-glasses chain; the vaulted ribs
- **DON GRINALDI FAZZOLETTO** (THE VILLA BALLROOM): the chandeliers (swing them into him); his strings themselves: grapple a string and it goes taut, and you ride it up; the gallery balustrade
- **THE CART MOTHER** (FOOD COURT COLOSSEUM): the dome's ribs (swing across the whole court); SALE banners on cables; her own carts (grapple one out of her pile)
- **FOREMAN REMAINDER** (THE NUMBER YARD): the digits (ride them along the belts); his crane arms (yank him off balance); the Smokestacks' ladders
- **DOCTOR UPSELL** (UPSELL'S CLINIC): neon sign letters (the Chrome Gristle gimmick: shooting letters changes the words); the surgical lamp rig over the chairs; his arms: grapple one and he drops its tool
- **THE HOA** (THE CUL-DE-SAC): porch gutters; the basketball hoops on every drive; the hedge's PLEASE KEEP OFF THE GRASS signs (pull them off)
- **THE PERPETUAL TUESDAY** (TUESDAY TOWER): the tower's ledges; the lift cables (inside the shaft); the clock's missing-hand sockets
- **EMPLOYEE 4417** (THE RESTORATION WAREHOUSE): the cable trunks (swing the whole row); the racks; the mannequins' neck cables (yank one out to wake it, or switch it off)
- **THE TALL GUY FROM HR** (THE SCARY FOREST): pine branches everywhere (a swing route through the canopy); the lifeguard tower; his arms (when they stretch, they're a rope)
- **PENNY PLOT** (THE EDGE): the SOLD sign poles; the Show Home's gutters; falling chunks (swing between them as they drop)
- **THE MEETING ROOM** (THE CATHEDRAL OF SHAREHOLDER VALUE): the Cathedral spires; the Meeting Room's landing skids; the projector arm
- **THE TWINS** (THE SPIRE LOBBY): the mezzanine rail; the chandelier; the open elevator shaft's cables
- **MARION HASK** (THE CLOCK'S CONTROL ROOM): the archive cable (pull it out of the wall); the console's lever arms; the gears below the glass
- **EMPLOYEE OF THE MONTH** (THE CONVOY): the rigs' desk-stack towers; overhead gantries (swing from rig to rig); his plaques (rip them off)
- **THE MORALE OFFICER** (THE FUN FAIR): the Ferris wheel's spokes; the big top's trapeze; bunting lines between the stalls
- **UNLUCKY 13** (THE FALLEN 13): the 13's display panels; the orbiting digits (ride them); the relay dishes' masts
- **THE MISSING TEXTURE** (THE UNFINISHED BIT): half-loaded cars in the air; the staircase to nowhere; the T-posed man's arms
- **REVENUE PROTECTION** (THE LAST TWO CARS): the wagon's rail and the flatbed's chains (to get back on when a Sweeper puts you over the side); the signal gantries a Brakeman drops; a Snatcher's wrist (zip to the crewmate it's holding)

## Every mechanic

### THE GRAPPLE `grapple`
_movement · shared/hookphys.js, public/js/player.js, public/js/grapple.js_

A 90 m rope that winds you toward the point as a pendulum: you keep momentum, swing in arcs, and a grapple jump (let go on the upswing, looking the way you swing) flings you on with a hop. Grappling a person tugs them toward you. Skins change the rope and hook.

- **traversal:** the city is built for it: every district has swing points and a signature swing route (GRAPPLE.routes)
- **puzzles:** pull things (crates, levers, a meatball), rip armour plates off, open hatches from below
- **combat:** yank enemies off ledges and roofs; zip to weak points; swing past snipers
- **bosses:** every boss arena lists grapple points; a dozen bosses have armour you tear off or a weak point you zip to
- **side:** grapple races, rooftop deliveries, the Washing Line Run
- **taught:** PLEASE TAKE YOUR ITEM (`m01_return_to_sender`): Dumpling's tour: 'grapple the wok on that roof. no, the wok. the WOK.' You swing onto the Wok Roofs and the kid scores your landing out of ten.
- **main missions:** PLEASE TAKE YOUR ITEM, SOMETHING'S DIGESTING, CLOCKING IN, OPTION C, AN OFFER, FAMILY BUSINESS, LOST CHILD, NO REFUNDS, RUSH HOUR, ROUNDING DOWN, NINE KILOMETRES, ORGAN DONOR, THE MISSING, PROPERTY VALUES, WORKFORCE RESTORATION, TUESDAY AGAIN, EXIT INTERVIEW, NEGATIVE SPACE, THE PLAN, 03:00, THE LOBBY, OVERDUE
- **side quests:** WOK THE DISH, LOST PROPERTY, THE WASHING LINE RUN, CHOIR PRACTICE, BELLY BUTTON, THE MEATBALL RUN, PRICE CHECK ON AISLE EVERYTHING, THE NAMES, DIVIDE BY ZERO, SPARE PARTS, BUY BACK, RETURN ADDRESS, STAKING CLAIMS, THE PUNCTUALITY MUSEUM, REPLY ALL, TEAM BUILDING, SMILES, THE FIRST INTERN, PERFORMANCE REVIEW, MANDATORY FUN, UNLUCKY 13
- **boss fights:** MR. OVERTIME, MR. OVERTIME, MR. OVERTIME, MR. OVERTIME, MR. OVERTIME, MR. DEPOSIT, THE STOMACH BISHOP, THE FOUNDING PARTNER, DON GRINALDI FAZZOLETTO, THE CART MOTHER, FOREMAN REMAINDER, DOCTOR UPSELL, THE HOA, THE PERPETUAL TUESDAY, EMPLOYEE 4417, THE TALL GUY FROM HR, PENNY PLOT, THE MEETING ROOM, THE TWINS, MARION HASK, EMPLOYEE OF THE MONTH, THE MORALE OFFICER, UNLUCKY 13, THE MISSING TEXTURE, REVENUE PROTECTION

### WASHING-LINE ZIPLINES `washing_lines`
_movement · public/js/story (the Bottom's traversal gimmick)_

Every washing line in the Bottom is a grapple rail: ride it at speed, dropping socks.

- **traversal:** the Bottom's whole skyline is a zipline network
- **combat:** Mr. Deposit's arena, Overtime fight 1's roofs
- **side:** the Washing Line Run (a timed full-network race)
- **taught:** PLEASE TAKE YOUR ITEM (`m01_return_to_sender`): the tutorial's last step: ride a line across the Wok Roofs. Dumpling: 'don't look down. there's a man down there. he lives there.'
- **main missions:** PLEASE TAKE YOUR ITEM
- **side quests:** SECURITY DEPOSIT, WOK THE DISH, THE WASHING LINE RUN
- **boss fights:** MR. OVERTIME, MR. DEPOSIT

### SLIDE `slide`
_movement · public/js/player.js_

Crouch while fast to slide; slides keep momentum and the Slinky Spine doubles them.

- **traversal:** slide on the Gut's peristalsis beat for huge speed
- **combat:** slide under staple fans, through Upsell's legs
- **bosses:** Bishop phase 2, Overtime's Staple Fan, Upsell's back
- **taught:** SOMETHING'S DIGESTING (`m03_somethings_digesting`): Peristalsis Avenue: Lumps, deadly serious: 'slide on the squeeze. it likes it.'
- **main missions:** SOMETHING'S DIGESTING, TICKETS, PLEASE, THE LAST WORKDAY: 17:20, THE MISSING
- **side quests:** ONE SHOE GUY
- **boss fights:** MR. OVERTIME, THE STOMACH BISHOP, REVENUE PROTECTION

### BHOP AND INFINITE MOMENTUM `bhop`
_movement · public/js/player.js_

Jump on the first tick of landing to skip friction: momentum is forever, no speed cap. W-only air steering keeps all of it.

- **traversal:** the Commute's car roofs (Jams) are a bhop road
- **combat:** outrun Late Fees on foot
- **side:** races, the Mall Walkers (you're not allowed to run, so you're not allowed to bhop: the HUD fines you)
- **taught:** RUSH HOUR (`m13_rush_hour`): out of the car on the Jams: Gordo, 'stopping's a paid add-on. todd never bought it. don't stop.'
- **main missions:** PLEASE TAKE YOUR ITEM, RUSH HOUR, MINUTES OF THE MEETING
- **side quests:** MALL WALKER
- **boss fights:** MR. OVERTIME

### ROCKET AND SHOTGUN JUMPS `rocket_jump`
_movement · shared/weapons.js · weapons: chicken, shotgun, sawnoff, bread_

Chicken Rocket at your feet rocket-jumps; shotgun and sawn-off at the floor launch you; the Bread pogos off walls and floors.

- **traversal:** shortcuts up Number Works' smokestacks and the Spire's outside
- **puzzles:** reach things no ladder reaches
- **bosses:** Foreman's Calculator roof, Meeting Room's skids
- **taught:** THE PRICE OF EVERYTHING (`m14_price_of_everything`): Nell, holding a vote: 'motion: the plastic person shoots their own feet to get on the roof. all in favour?' It passes.
- **main missions:** SAUCE RUN, THE PRICE OF EVERYTHING, THE PLAN
- **side quests:** DIVIDE BY ZERO, TEAM BUILDING
- **boss fights:** MR. DEPOSIT, THE STOMACH BISHOP, THE CART MOTHER, FOREMAN REMAINDER, PENNY PLOT, THE MEETING ROOM, EMPLOYEE OF THE MONTH

### VOID EDGES `void_edges`
_movement · the Margins' traversal gimmick_

At the Margins, falling into the void respawns you at the nearest staked gnome, keeping your momentum.

- **traversal:** fall in on purpose to slingshot along the coast
- **bosses:** Tall Guy, Penny Plot
- **side:** Lifeguard, Staking Claims
- **taught:** EXIT INTERVIEW (`m26_exit_interview`): Old Pat pushes you off the Edge. 'there. ken caught you. say thank you to ken.'
- **main missions:** EXIT INTERVIEW, NEGATIVE SPACE
- **side quests:** LIFEGUARD, STAKING CLAIMS
- **boss fights:** THE TALL GUY FROM HR, PENNY PLOT

### LOOPS `loops`
_movement · the Lates' traversal gimmick_

Walk off one edge of a Lates street and arrive at the other with your momentum: infinite falls build insane speed.

- **traversal:** build speed by falling forever between floors
- **bosses:** Perpetual Tuesday, Overtime fight 3
- **side:** Copy of a Copy
- **taught:** THE WAITING ROOM (`m22_the_waiting_room`): Pauline drops a stapler off the roof and it lands on your head from above. 'you'll get used to it. i didn't.'
- **main missions:** THE WAITING ROOM, TUESDAY AGAIN
- **side quests:** GROUNDHOG LUNCH, HOLD MUSIC
- **boss fights:** MR. OVERTIME, THE PERPETUAL TUESDAY

### ON TIME `on_time`
_movement · Corp Hill's traversal gimmick_

On Corp Hill walkways, lifts and window gondolas move on the clocks' beat: be on time and you fly, be late and doors shut.

- **traversal:** Corp Hill is a rhythm level
- **side:** Casual Friday, Team Building
- **bosses:** the Meeting Room's approach
- **taught:** 03:00 (`m29_the_missing_hour`): the raid: Gordo counting the ticks out loud under his breath as everyone runs between them.
- **main missions:** 03:00
- **side quests:** REPLY ALL, CASUAL FRIDAY
- **boss fights:** THE MEETING ROOM

### MARBLE SLIP `marbles`
_weapon · shared/marbles.js · weapons: marbles_

The Marble Shotgun leaves marbles on the floor; anyone running over them slips (crouch-walk to cross).

- **combat:** floor a charge; a slip is a stagger
- **bosses:** the Bishop (loses the beat), Employee 4417 (it has never slipped), the Missing Texture
- **puzzles:** slip a patrol off a ledge
- **taught:** LOST CHILD (`m10_doorbusters`): a Mall Rat kid rolls marbles under a Security segway: 'that's how we've been winning since before you were made.'
- **main missions:** LOST CHILD, THE MISSING
- **side quests:** TWO JESTERS, QUALITY CONTROL, THE FIRST INTERN
- **boss fights:** THE STOMACH BISHOP, EMPLOYEE 4417, THE MISSING TEXTURE

### BANANA PEELS `peels`
_weapon · shared/weapons.js · weapons: banana_

The Peel Shooter bonks and slips; misses stay as peels.

- **combat:** trap doorways
- **bosses:** the Don's strings tangle, the Missing Texture can't tell a peel from the floor
- **side:** Two Jesters' first prank
- **taught:** TWO JESTERS (`sq_pinstripe_two_jesters`): prank one: peel the Bocce Pit before a 'settlement'. The settlement is settled by slapstick.
- **main missions:** FAMILY BUSINESS
- **side quests:** TWO JESTERS, QUALITY CONTROL, THE FIRST INTERN
- **boss fights:** THE STOMACH BISHOP, DON GRINALDI FAZZOLETTO, EMPLOYEE 4417, THE MISSING TEXTURE

### KATANA PARRY AND GROWTH `parry`
_weapon · public/js/parry.js, shared/weapons.js PARRY · weapons: katana_

Right click parries bullets, rockets and swords from the front; a perfect parry sends bullets back. Every kill grows the blade.

- **combat:** parry staples, slaps and missiles
- **bosses:** a perfect staple parry opens Overtime's heart in fight 4; the katana cuts the Don's strings in one swing
- **taught:** FAMILY BUSINESS (`m08_family_business`): the Don slaps; a goon whispers 'it's polite to parry'.
- **main missions:** FAMILY BUSINESS, OVERDUE
- **boss fights:** MR. OVERTIME, MR. OVERTIME, DON GRINALDI FAZZOLETTO, THE PERPETUAL TUESDAY

### SCALES OF JUSTICE (VERDICTS) `verdict`
_weapon · shared/verdict.js · weapons: scales_

Hits as hard as the target deserves: leaders, streakers and your killer take up to x3 (GUILTY / NOT GUILTY / HUNG JURY).

- **bosses:** the guilty: Hask (she signed it), Overtime's rehire (he killed you), the Founding Partner, the Twins (two verdicts in one hit)
- **side:** Claims Department
- **combat:** the scales always rate the people who ended the world GUILTY
- **taught:** CLAIMS DEPARTMENT (`sq_pinstripe_claims_department`): the claims queue: the scales hang in the office as decoration until you pick them up and the adjusters start getting what they deserve.
- **main missions:** THE LOBBY, FULLY VESTED
- **side quests:** BELLY BUTTON, CLAIMS DEPARTMENT, THE PUNCTUALITY MUSEUM
- **boss fights:** MR. OVERTIME, THE FOUNDING PARTNER, THE TWINS, MARION HASK

### THE REDLINE `redline`
_weapon · shared/weapons.js · weapons: redline_

The lower your HP, the faster it fires.

- **bosses:** the weapon for fights against time: Overtime and Hask are weak to a low-HP Redline
- **taught:** CLOCKING IN (`m04_clocking_in`): Lumps, stapled to the truck, tosses it to you: 'it likes it when you're nearly dead. sorry.'
- **main missions:** CLOCKING IN, OVERDUE, FULLY VESTED
- **boss fights:** MR. OVERTIME, MR. OVERTIME, MARION HASK

### SOAK AND SHOCK `water_taser`
_weapon · shared/weapons.js · weapons: water, taser_

The Water Pistol soaks (slip, slow, puts out fire); a taser jumps through everyone wet.

- **bosses:** Overtime fights 1 and the rehire (wet clockwork runs slow), Unlucky 13
- **puzzles:** short out a generator; put out the Gut's gas fires
- **combat:** wet a crowd, tase once
- **taught:** CLOCKING IN (`m04_clocking_in`): the collectors' truck has a water tank; Dumpling: 'mr. overtime hates baths. everybody knows that.'
- **main missions:** CLOCKING IN, ROUNDING DOWN
- **side quests:** THE PUNCTUALITY MUSEUM, UNLUCKY 13
- **boss fights:** MR. OVERTIME, MR. OVERTIME, FOREMAN REMAINDER, UNLUCKY 13

### FROST AND SHATTER `frost`
_weapon · shared/weapons.js · weapons: snowball_

Four snowball hits freeze; a frozen target shatters.

- **bosses:** freezing desyncs loop bosses (Overtime 3, the Perpetual Tuesday)
- **combat:** freeze a goon into a block and push it
- **taught:** THE WAITING ROOM (`m22_the_waiting_room`): the Lates' water cooler has been freezing for 22,000 days: Pauline hands you snowballs made of it.
- **main missions:** THE WAITING ROOM, TUESDAY AGAIN
- **boss fights:** MR. OVERTIME, THE PERPETUAL TUESDAY, MARION HASK, THE MORALE OFFICER

### TV REMOTE (PAUSE / REWIND) `remote`
_weapon · public/js/remote.js · weapons: remote_

Left click pauses someone for a second; right click rewinds them 2 s.

- **bosses:** pause Upsell's twelve arms; rewind the Perpetual Tuesday into his own copies; make Hask late
- **puzzles:** rewind a falling bridge
- **taught:** GROUNDHOG LUNCH (`sq_lates_groundhog_lunch`): the canteen remote: rewind Gus's dropped fork back onto the table.
- **main missions:** ORGAN DONOR, THE WAITING ROOM, FULLY VESTED
- **side quests:** GROUNDHOG LUNCH
- **boss fights:** MR. OVERTIME, DOCTOR UPSELL, THE PERPETUAL TUESDAY, MARION HASK, THE MORALE OFFICER

### THE SHREDDER `shredder`
_weapon · public/js/shredder.js · weapons: shredder_

An industrial vacuum-shredder: hold to suck people in; the intake shreds them.

- **puzzles:** suck the paper storm clear; shred the Schedule printout's copies
- **bosses:** the Steering Committee's minutes, the Tall Guy's folder storm
- **taught:** NINE KILOMETRES (`m18_nine_kilometres`): the Timekeeping relay's backup shredder: Gordo, 'they shred everything. take theirs.'
- **main missions:** NINE KILOMETRES
- **boss fights:** MR. OVERTIME

### THE LASSO `lasso`
_weapon · shared/lasso.js, public/js/lasso.js · weapons: lasso_

Throw a loop, catch someone, swing them on the rope, flick and let go: they fly. Walls and floors hurt.

- **combat:** fling enemies into the void, acid, the stampede
- **puzzles:** pull a giant tooth, tow a car, drag a briefcase
- **bosses:** Penny Plot's briefcase, Overtime 4's escapement, Employee 4417
- **taught:** ONE SHOE GUY (`sq_bottom_one_shoe`): catching the living shoe in the Gut: it's the only thing small and fast enough to learn on.
- **main missions:** THE MISSING, EXIT INTERVIEW, NEGATIVE SPACE, OVERDUE
- **side quests:** ONE SHOE GUY, THE MEATBALL RUN, SPARE PARTS, QUALITY CONTROL, LIFEGUARD, PERFORMANCE REVIEW
- **boss fights:** MR. OVERTIME, EMPLOYEE 4417, THE TALL GUY FROM HR, PENNY PLOT, EMPLOYEE OF THE MONTH, THE MISSING TEXTURE

### SHOPPING CART CANNON `cart`
_weapon · shared/weapons.js · weapons: cart_

Fires a cart that runs people over; it stays as cover or you ride it.

- **bosses:** the Cart Mother (carts make her heavy)
- **traversal:** cart-surfing down escalators
- **taught:** LOST CHILD (`m10_doorbusters`): Wristband hands you the Rat Cart Cannon: 'she can't help picking them up.'
- **main missions:** LOST CHILD, NO REFUNDS
- **side quests:** RETURNS DESK ZERO
- **boss fights:** THE CART MOTHER

### SHOVE AND KNOCKBACK `knockback`
_weapon · shared/weapons.js · weapons: minigun, blower, sniper, bowling, slapper_

The minigun shoves and you can fly on its recoil; the Leaf Blower pushes and hovers; sniper body shots send people flying; bowling balls bowl people over; the Hand Slapper launches and slips.

- **combat:** the void, acid lakes and the stampede are weapons if you shove people into them
- **bosses:** Overtime 2 (shove him off pace), the Cart Mother, the HOA
- **taught:** NEGATIVE SPACE (`m27_negative_space`): Penny Plot, cheerfully: 'please don't blow my agents off the edge.' You do.
- **main missions:** NO REFUNDS, RUSH HOUR, NEGATIVE SPACE
- **side quests:** HAIRBALL, THE MEATBALL RUN, PERFORMANCE REVIEW
- **boss fights:** MR. OVERTIME, DON GRINALDI FAZZOLETTO, THE CART MOTHER, THE HOA, THE TALL GUY FROM HR, PENNY PLOT, THE MEETING ROOM, EMPLOYEE OF THE MONTH

### FIRE (THE CIGARETTE, FLAME ARROWS) `fire`
_weapon · shared/weapons.js · weapons: cig, bow_

Smoke the Cigarette and breathe fire; bow arrows roll random tips (flame, explosion, gas, sleep...).

- **bosses:** Mr. Deposit's upholstery, the HOA's hedge, Penny's hazmat suit
- **puzzles:** light oil slicks for fire walls
- **taught:** SECURITY DEPOSIT (`sq_bottom_deposit`): Sharon: 'he's mostly sofa. you know what sofas don't like.'
- **main missions:** PROPERTY VALUES
- **side quests:** SECURITY DEPOSIT, LAWN ORDER
- **boss fights:** MR. OVERTIME, MR. DEPOSIT, DOCTOR UPSELL, THE HOA, PENNY PLOT, THE MORALE OFFICER

### NAIL TO THE WALL `nailgun`
_weapon · shared/weapons.js · weapons: nailgun_

Enough nails in a row pin someone to the wall like a poster.

- **bosses:** pin the Founding Partner's arms; the First Staple legendary turns pinned enemies into grapple points
- **taught:** ORGAN DONOR (`m19_organ_donor`): Bev pins a runaway kidney to her wall to demonstrate. It's fine. It's used to it.
- **main missions:** ORGAN DONOR
- **side quests:** BELLY BUTTON
- **boss fights:** THE FOUNDING PARTNER

### BANK SHOTS `bounce_shots`
_weapon · shared/weapons.js · weapons: tennis, revolver, slipper_

Tennis balls bounce up to 5 times (harder each bounce), revolver ricochets twice, the slipper boomerangs into the nearest enemy and back.

- **bosses:** bank shots round the Twins' shield, into Unlucky 13's crown, and the slipper round the Tall Guy while you look away
- **taught:** CARRY THE ONE (`sq_numberworks_carry_the_one`): a union rep banks a tennis ball off three digits into a rounding crew: 'geometry. we're the remainder. we know angles.'
- **main missions:** THE PRICE OF EVERYTHING, THE LOBBY
- **side quests:** CARRY THE ONE
- **boss fights:** FOREMAN REMAINDER, THE TALL GUY FROM HR, THE TWINS, UNLUCKY 13

### BIG LASER POINTER `laser_beam`
_weapon · public/js/laserglb.js · weapons: laser_

Hold to charge; a fat beam goes through everyone in a line.

- **bosses:** the Meeting Room (do point it at aircraft)
- **combat:** corridors full of HR Tactical
- **taught:** 03:00 (`m29_the_missing_hour`): Hask's own desk pointer is in the post-game; in the raid a Remainder hands you one: 'we used it to point at forecasts.'
- **main missions:** 03:00
- **boss fights:** THE MEETING ROOM

### CARD DECK `cards`
_weapon · public/js/cards.js · weapons: cards_

Five cards: hearts heal, spades throw, clubs blast, diamonds dash, aces teleport, face cards ultimate, jokers random.

- **side:** the Parking Permit's laminated deck; the Receipt legendary
- **combat:** an ace teleport is an escape from a grab
- **taught:** CLAIMS DEPARTMENT (`sq_pinstripe_claims_department`): an adjuster deals you a hand to decide your claim. You win with a joker.
- **side quests:** CLAIMS DEPARTMENT, PARKING PERMIT
- **boss fights:** THE MISSING TEXTURE

### BLOOD CROSS `bloodcross`
_weapon · public/js/bloodcross.js · weapons: bloodcross_

Shoot blood out of your fingertip (12 HP a shot); a kill pays it back.

- **combat:** a desperate low-HP weapon that pairs with the Redline
- **bosses:** the Stomach Bishop (blood is sacrament: x1.5)
- **taught:** THE MISSING (`m20_the_missing`): Sister Agenda, quietly: 'the choir doesn't like it when you give blood back. it's rude in a church.'
- **main missions:** TICKETS, PLEASE, THE MISSING
- **boss fights:** THE STOMACH BISHOP, REVENUE PROTECTION

### BLOOD DRIVE `blooddrive`
_weapon · not built yet (docs/story/TRAIN.md §3): reuses public/js/bloodcross.js bolts and bursts_

The Blood Cross, six times over, on a motor. Hold fire: the ring spins up over 0.8 s, then 14 bolts a second. Small bolts (18 damage), each one sticks. Every sixth bolt in the same target blooms a blood cross. 2 HP a bolt: that is 28 HP a second, so on your own blood you get about three seconds before you're dying. A severed arm or a kill pays blood back.

- **combat:** before Jack, a thing you can't afford. After Jack (Pallet Jack's Marrow) it's free while the ring is spinning, and crosses chain to anything within 3 m. After the mission it stays as OVERDUE's heavy weapon: found on the train's rear car, carried like a streak
- **bosses:** REVENUE PROTECTION: sever the arms at the wrist, then break the mask plate by plate; the finish is one blood cross that touches the tunnel on all four sides
- **taught:** TICKETS, PLEASE (`m06_tickets_please`): Bev, plumbing six lines into your hand: 'this is that, six at a time, on a motor. it'll empty you in three seconds. don't hold it down unless you mean it.'
- **main missions:** TICKETS, PLEASE
- **boss fights:** REVENUE PROTECTION

### INSTANT CAMERA `camera`
_item · public/js/photo.js_

Snap a photo; print it as a frame you can walk into: it puts you back where you took it.

- **puzzles:** a portable checkpoint for climbs; take a photo at the top, walk into it from the bottom
- **side:** Price Check on Aisle Everything (scan barcodes)
- **bosses:** photograph the boss's weak spot before a loop (Overtime 3) to walk back to it
- **taught:** PRICE CHECK ON AISLE EVERYTHING (`sq_checkout_price_check`): Gail: 'price check on aisle everything.' The camera scans prices. And rats.
- **main missions:** THE LAST WORKDAY: 16:00, THE LAST WORKDAY: 16:45, TUESDAY AGAIN
- **side quests:** PRICE CHECK ON AISLE EVERYTHING, ROUNDING ERROR, COPY OF A COPY, PARKING PERMIT
- **boss fights:** MR. OVERTIME

### POP QUIZ `quiz`
_item · public/js/quiz.js_

Throw a calculator: whoever it hits gets a maths question; wrong or slow and they die.

- **bosses:** Foreman Remainder answers every quiz correctly and heals; Employee 4417 answers instantly; the HOA answers by committee (slowly)
- **side:** Divide by Zero (the quiz is NaN)
- **taught:** ROUNDING DOWN (`m15_rounding_down`): a Remainder apprentice throws one at a rounding crew: '13 × 7?' The crew rounds it. Boom.
- **main missions:** ROUNDING DOWN
- **side quests:** DIVIDE BY ZERO
- **boss fights:** FOREMAN REMAINDER

### NIGHT VISION GOGGLES `nvg`
_item · public/js/goggles.js_

The dark goes green and people glow; middle click flashes everyone you see.

- **traversal:** the Lates' basement and the Missing Hour's grey
- **bosses:** the Tall Guy's forest at night; the Fun Fair
- **side:** Hold Music (the Backrooms Stairwell)
- **taught:** WORKFORCE RESTORATION (`m23_workforce_restoration`): Pauline hands you a pair from the Lates' lost property: 'the hour's grey. you'll want green.'
- **main missions:** WORKFORCE RESTORATION
- **side quests:** CHOIR PRACTICE, BUY BACK, HOLD MUSIC
- **boss fights:** THE TALL GUY FROM HR, THE MORALE OFFICER

### SPEED TRAP (RADAR GUN) `radar`
_item · shared/weapons.js SPEED_

Point it at someone: over 100 km/h they get 3 s to slow down or they're jailed.

- **bosses:** clock Overtime on the Spiral Freeway: at exactly 70 he's never speeding, but jail an Unpaid war-rig
- **side:** Late Fees: Timekeeping cruisers use it on you
- **taught:** RUSH HOUR (`m13_rush_hour`): a Timekeeping cruiser's radar gun, fallen off in the chase: Gordo, 'point it at him. no, he's doing exactly the limit. of course he is.'
- **main missions:** RUSH HOUR
- **boss fights:** MR. OVERTIME

### BUBBLE WAND `bubble_wand`
_item · shared/wand.js_

Bubbles seal enemies and float them away for 5 s; over the void, a kill.

- **combat:** float adds over the void at the Margins
- **bosses:** Mr. Deposit's moth swarm
- **side:** Larry's joke
- **taught:** TWO JESTERS (`sq_pinstripe_two_jesters`): Long Larry blows one, very slowly, and puts himself in it by mistake.
- **side quests:** TWO JESTERS
- **boss fights:** MR. DEPOSIT, PENNY PLOT

### RUBBER DUCK (BLACK HOLE) `duck`
_item · public/js/duck.js_

Sticks to an enemy and opens a black hole on them: drags their friends in, eats momentum, snaps ropes.

- **bosses:** snap the Don's strings, eat the Cart Mother's swarm; careful: it snaps your grapple too
- **taught:** HAIRBALL (`sq_gut_hairball`): the man in the house down Peristalsis Avenue has a bath duck. It's not a normal duck.
- **side quests:** HAIRBALL, TWO JESTERS
- **boss fights:** DON GRINALDI FAZZOLETTO

### PARTY POPPER `popper`
_item · shared/weapons.js_

A confetti blast shoves everyone in front away and launches you backwards: zero damage, all void kills and escapes.

- **combat:** escape a grab (Punch In, the HOA's vote), void kills
- **side:** Mandatory Fun
- **taught:** MANDATORY FUN (`sq_commute_mandatory_fun`): it's the Fun Department's sidearm. Obviously.
- **side quests:** TWO JESTERS, MANDATORY FUN
- **boss fights:** MR. OVERTIME, THE MORALE OFFICER

### REVERSE CARD `reverse`
_item · shared/weapons.js_

For 3 s every bullet, blast and shove aimed at you goes back to whoever sent it.

- **bosses:** send a Price Strike back into Unlucky 13; send Hask's Signature line back at her
- **taught:** CLAIMS DEPARTMENT (`sq_pinstripe_claims_department`): the Claims Office's only 'approved' form is a Reverse Card. Nonna keeps it in her knitting.
- **side quests:** CLAIMS DEPARTMENT
- **boss fights:** MARION HASK, UNLUCKY 13

### FRAGS AND SMOKE `frag_smoke`
_item · shared/weapons.js_

Frags bounce and blow up after 2 s, knocking people (and you) flying; smoke blinds for 10 s.

- **bosses:** feed a frag to every mouth (the Bishop's phase 3, Mr. Deposit's box)
- **combat:** smoke out a Late Fees roadblock
- **taught:** SAUCE RUN (`m02_sauce_run`): Employee of the Month's interns throw 'business cards'. They're frags.
- **main missions:** SAUCE RUN
- **side quests:** SECURITY DEPOSIT, QUARTERLY GROWTH, BLOCK PARTY
- **boss fights:** MR. OVERTIME, MR. DEPOSIT, THE STOMACH BISHOP, EMPLOYEE OF THE MONTH

### OVERDRIVE RIG `rig`
_streak · public/js/rig.js, shared/rig.js_

A scrap-built juggernaut: rocket punch, block, sky jumps, thrusters, homing missiles, until its armour breaks.

- **bosses:** the Rig's punch knocks the Twins' shield aside and the Meeting Room's skids off
- **side:** Leg Day as a speedrun (carry two fridges)
- **taught:** LEG DAY (`sq_bottom_leg_day`): Lumps lends you his gym's 'big one': a scrap exo-frame he built to carry fridges. 'don't punch the stairs. they're old.'
- **main missions:** TICKETS, PLEASE
- **side quests:** LEG DAY
- **boss fights:** THE MEETING ROOM, THE TWINS

### WRECKING BALL `wrecking_ball`
_streak · public/js/player.js, public/js/wreck.js_

Become a steel ball: roll with momentum, swing on a chain, slam the floor from the air.

- **bosses:** slam the Cart Mother's swarm; swing on the Master Clock's pendulum
- **puzzles:** break down the Lates' locked office (Copy of a Copy alt)
- **side:** Hairball (push the house through as a ball)
- **taught:** HAIRBALL (`sq_gut_hairball`): the house is stuck. You become a wrecking ball. It's the obvious answer.
- **side quests:** HAIRBALL
- **boss fights:** MR. OVERTIME

### MOON BOOTS `moon_boots`
_streak · shared/weapons.js STREAKS_

Low gravity and huge jumps for 25 s.

- **traversal:** the Spire's outside in one go; the Fallen 13
- **bosses:** Unlucky 13's crown, the Ferris wheel
- **taught:** UNLUCKY 13 (`sq_commute_unlucky_13`): found in the 13's crater: the orbital billboard's maintenance boots, still working.
- **side quests:** UNLUCKY 13
- **boss fights:** UNLUCKY 13

### CHICKEN STRIKE `chicken_strike`
_streak · shared/weapons.js STREAKS_

Rain exploding chickens where you aim.

- **bosses:** the HOA's block party; the convoy
- **combat:** the 03:00 raid's barricades
- **taught:** MANDATORY FUN (`sq_commute_mandatory_fun`): the Fun Department's carnival finale is a chicken strike. It's mandatory.
- **side quests:** BLOCK PARTY, MANDATORY FUN
- **boss fights:** THE HOA, THE MORALE OFFICER

### SPY SATELLITE `satellite`
_streak · shared/weapons.js STREAKS_

See every enemy through walls for 20 s.

- **side:** the Names (find Big Value's log through the walls)
- **bosses:** the Tall Guy (see him while you're not looking)
- **taught:** UNLUCKY 13 (`sq_commute_unlucky_13`): the 13 is a satellite. You borrow its eye.
- **side quests:** THE NAMES, UNLUCKY 13
- **boss fights:** THE TALL GUY FROM HR, UNLUCKY 13

### GIANT DUCK `giant_duck`
_streak · shared/weapons.js STREAKS_

A giant black hole where you aim that pulls in everyone but you and eats their momentum.

- **bosses:** pull the Perpetual Tuesday's copies into one place; stop the stampede dead
- **taught:** MALL WALKER (`sq_checkout_mall_walker`): a Mall Walker grandmother keeps one in her handbag for emergencies. This is an emergency.
- **side quests:** MALL WALKER
- **boss fights:** THE CART MOTHER, THE PERPETUAL TUESDAY

### SPINBOT `spinbot`
_streak · shared/weapons.js STREAKS_

Aimbot and spinbot for 10 s: 'you are now a cheater.'

- **side:** Arcade Legend (the cabinet runs the old JANKFIRE: Todd says it's cheating; it is)
- **bosses:** Employee 4417 calls it unscheduled and freezes
- **taught:** ARCADE LEGEND (`sq_chromegristle_arcade_legend`): the arcade cabinet's 'cheat code' printed on its side.
- **side quests:** ARCADE LEGEND
- **boss fights:** EMPLOYEE 4417

### SCYTHE RIFLE `scythe`
_streak · shared/weapons.js STREAKS_

Wide reaping swings; X folds it into a rifle; hold V to glitch dash.

- **bosses:** the Morale Officer's heads; the Founding Partner's arm storm
- **taught:** BELLY BUTTON (`sq_gut_belly_button`): the Founding Partner's office has one on the wall, for 'harvest season'.
- **side quests:** BELLY BUTTON
- **boss fights:** THE FOUNDING PARTNER

### CARS AND TRAFFIC `cars`
_vehicle · server/traffic.js, public/js/cars.js_

Traffic cars become drivable: yank drivers out, drift, boost, keep momentum, grapple from a car to slingshot it, crash into each other.

- **traversal:** the Commute
- **bosses:** Overtime 2, Employee of the Month, the HOA golf carts
- **side:** deliveries, races, Keeping Up
- **taught:** SAUCE RUN (`m02_sauce_run`): steal a car: Gordo, 'he means steal a car.' The car belongs to Sharon's cousin. He's asleep on it.
- **main missions:** SAUCE RUN, RUSH HOUR, PROPERTY VALUES, THE PLAN, 03:00
- **side quests:** LOST PROPERTY, REFLUX, QUARTERLY GROWTH, WET WORK, CARRY THE ONE, LAWN ORDER, KEEPING UP, RETURN ADDRESS, THE LAST BUS, THE REGION, SMILES, PERFORMANCE REVIEW
- **boss fights:** MR. OVERTIME, MR. OVERTIME, THE CART MOTHER, THE HOA, EMPLOYEE OF THE MONTH

### LATE FEES `late_fees`
_system · docs/story/DESIGN.md §6.2_

The wanted level: Punctuality Officers, cruisers, Collections vans, HR Tactical, then Mr. Overtime.

- **combat:** chases
- **side:** Late Desks
- **bosses:** Overtime is the ★5 boss
- **taught:** AN OFFER (`m07_an_offer`): the tax-office job on the Bleach Line: your first ★2.
- **main missions:** AN OFFER, NINE KILOMETRES
- **boss fights:** MR. OVERTIME

### BIO-IMPLANTS `implants`
_implant · shared/story/implants.js_

Body slots, the Body Budget, Drift, organ cores, downsides (WP5): Spring Knees, Pigeon Eyes, Second Stomach, the Punch-Clock...

- **traversal:** Spring Knees, Balloon Lungs, the grapple implants (Tendon Line, Hook Hand, Peristaltic Reel)
- **combat:** every organ core
- **side:** the secret bio upgrades
- **bosses:** every boss drops a core
- **taught:** SECOND STOMACH (`m05_second_stomach`): Bev's back room: 'they're all terrible ideas. this one works.'
- **main missions:** SECOND STOMACH, TICKETS, PLEASE, THE SPLIT
- **side quests:** SECOND OPINION
- **boss fights:** DOCTOR UPSELL, EMPLOYEE 4417, REVENUE PROTECTION

### HYPE `hype`
_system · shared/story/bodysys.js_

Kills, stylish kills, crashes and long grapples fill HYPE; streak items cost it.

- **combat:** long grapples are the fastest way to fill it
- **bosses:** fast-forward rounds in Overtime 4 fill it double
- **taught:** SOMETHING'S DIGESTING (`m03_somethings_digesting`): a long swing over the Gut's rib arches: the HYPE bar fills and Lumps says 'ooh'.
- **main missions:** SOMETHING'S DIGESTING
- **boss fights:** MR. OVERTIME

## Every mission's mechanic hook

| mission | uses | hook |
|---|---|---|
| PLEASE TAKE YOUR ITEM | grapple, washing_lines, bhop | the tutorial is a grapple lesson in disguise: Dumpling's tour is swing onto the Wok Roofs, ride a washing line back, and land somewhere Dumpling can score out of ten |
| SAUCE RUN | cars, frag_smoke, rocket_jump | a slosh meter on the soup pot turns every jump, drift and car-roof landing into a decision; the interns' 'business cards' are frags |
| SOMETHING'S DIGESTING | slide, grapple, hype | the Gut teaches flow: slide on Peristalsis Avenue's squeeze, swing the rib arches, bounce the lungs, and a long swing fills HYPE for the first time |
| CLOCKING IN | grapple, water_taser, redline | Overtime's missed staples stay in the walls as grapple points; the collectors' water tank soaks him (wet clockwork runs slow); Lumps throws you the Redline when you're low |
| SECOND STOMACH | implants | the first install: the clinic chair is the implant UI, and the Punch-Clock's tick is your first downside |
| TICKETS, PLEASE | bloodcross, rig, implants, slide, blooddrive | a boss you fight from the back of a moving train with a gun that fires your own blood; the fight is unwinnable until you take a dead friend's marrow |
| OPTION C | grapple | Gordo's den is up a grapple-only stack of containers; his string map doubles as the first look at every district's swing route |
| AN OFFER | late_fees, grapple | the tax-office run on the Bleach Line is your first ★2 chase, and Pinstripe's marionette strings are the escape route |
| FAMILY BUSINESS | parry, grapple, peels | cut the Don's strings with the katana, parry his slaps, and climb his own strings into the rafters |
| THE LAST WORKDAY: 16:00 | camera | no grapple in the sims of the last workday: Cale walks, carries six coffees, and spots a fake invoice; the lack of jank is the point |
| LOST CHILD | marbles, cart, grapple | the Mall Rats teach marbles under segways and give you the Rat Cart Cannon; the vents are a grapple maze above the dome |
| NO REFUNDS | cart, grapple, knockback | fire carts into the Cart Mother to make her heavy, grapple carts out of her pile, then cart-surf her own swarm |
| THE LAST WORKDAY: 16:45 | camera | a stealth level with a progress bar: copy the tape while an officer does rounds |
| RUSH HOUR | cars, grapple, bhop, radar, knockback | a chase where the boss chases you at the speed limit: grapple his tie to be towed, get out onto the bhop road of car roofs, and radar him at exactly 70 |
| THE PRICE OF EVERYTHING | rocket_jump, bounce_shots | the union votes you onto the press roof by rocket jump, and the print run is a fight on stamping presses |
| ROUNDING DOWN | grapple, quiz, water_taser | yank the Foreman's crane arms with the grapple to tip him face-down, tase his rolls into 13s, and quiz the rounding crews |
| THE LAST WORKDAY: 17:20 | slide | sixty floors of stairs against the sirens: slide down the banisters (Cale did it as a kid) |
| MINUTES OF THE MEETING | bhop | the last flashback's run across the lobby is the only time the game asks you to run as fast as you can and then takes it away |
| NINE KILOMETRES | shredder, late_fees, grapple | the Timekeeping relay is a stealth climb with grapple shortcuts, and the backup shredder clears the paper storm on the way out |
| ORGAN DONOR | nailgun, grapple, remote | Bev pins a kidney to show you the Nail Gun; Upsell's twelve arms are torn off one by one with the grapple |
| THE MISSING | slide, grapple, marbles, bloodcross, lasso | the rescue is an escort down Peristalsis Avenue on the beat; the Bishop's ulcers, the marble-slip weakness, and the lasso to drag digesters free |
| PROPERTY VALUES | fire, cars, grapple | mow lawns to stop the HOA regrowing, steal a militia golf cart, and swing the porch gutters round the cul-de-sac |
| THE WAITING ROOM | loops, frost, remote | the Lates teaches Loops (fall forever, keep the speed); freeze or rewind Neville to break his loop |
| WORKFORCE RESTORATION | nvg, grapple | the Missing Hour is grey: night vision goggles and a grapple swing down the cable trunks above the rows |
| THE SPLIT | implants | a talking mission: the split is about what you are, and your installed implants change which lines you're offered |
| TUESDAY AGAIN | loops, frost, camera, grapple | the loop fight: take a photo of where his weak point was and walk back into it next loop |
| EXIT INTERVIEW | void_edges, grapple, lasso | Old Pat pushes you into the void to teach Void Edges; the canopy is a grapple route; the Tall Guy only moves when you look away |
| NEGATIVE SPACE | knockback, lasso, void_edges, grapple | blow survey agents off the Edge, lasso Penny's briefcase, and grapple between falling plots |
| THE PLAN | grapple, rocket_jump, cars | each plan is a different playstyle: HEADCOUNT is stealth, DEMOLITION is a climb up the Big Escalator against its direction, PRINT RUN is a heist under the fountain |
| 03:00 | on_time, grapple, laser_beam, cars | the raid is a rhythm climb (On Time) up Dividend Road; grapple from the Cathedral spire onto the Meeting Room's skid |
| THE LOBBY | verdict, bounce_shots, grapple | the Twins' join opens when they spin; ricochet round the shield; the Scales find two people guilty in one hit |
| OVERDUE | grapple, parry, lasso, redline | the showpiece: climb the gears, ride the pendulum, tear the cables out of his back with the grapple, and parry staples into the teeth |
| FULLY VESTED | verdict, remote, redline | make the most punctual woman in the world late: pause her, slip her, freeze her; the Scales rate her GUILTY at x3 |
| SECURITY DEPOSIT | fire, washing_lines, frag_smoke | burn the armchairs off with the Cigarette, ride the washing lines round the shrinking pile, and post a grenade in the deposit box |
| ONE SHOE GUY | lasso, slide | learn the lasso on the only thing small and fast enough: a living shoe surfing peristalsis |
| LEG DAY | rig | fridge physics up 1,000 steps, and Lumps' 'big one', an Overdrive Rig he built for carrying fridges |
| WOK THE DISH | grapple, washing_lines | a storm grapple puzzle: aim twelve wok dishes at the Spire while the wind swings you |
| LOST PROPERTY | cars, grapple | ten deliveries across the city, one of them a whole bus, one of them only reachable by grapple |
| THE WASHING LINE RUN | washing_lines, grapple | the first grapple time trial: forty-one lines, never touch the floor |
| CHOIR PRACTICE | grapple, nvg | three overdue offices with grapple-only entrances; the Lates call centre is dark |
| REFLUX | cars | a driving puzzle: plug six acid vents with cars before the lake rises |
| HAIRBALL | wrecking_ball, duck, knockback | push a whole house down an intestine: knockback works, the wrecking ball works best |
| QUARTERLY GROWTH | cars, frag_smoke | escort or blow up Regrowth tankers |
| BELLY BUTTON | scythe, verdict, grapple, nailgun | the arm storm: grapple-run up the frozen arms, nail them to the vault, judge him guilty |
| TWO JESTERS | peels, marbles, popper, bubble_wand, duck | every prank is a weapon gimmick: peels, marbles, the popper, a bubble, a duck |
| WET WORK | cars | a crease meter: deliver laundry without landing hard |
| CLAIMS DEPARTMENT | verdict, cards, reverse | the Scales of Justice are the Claims Office's decoration until the adjusters get what they deserve |
| THE MEATBALL RUN | lasso, knockback, grapple | a physics escort: shove, lasso and grapple a car-sized meatball uphill |
| MALL WALKER | bhop, giant_duck | a walking race: bhop and you're fined; the grandmothers carry a Giant Duck for emergencies |
| PRICE CHECK ON AISLE EVERYTHING | camera, grapple | thirty barcodes hidden on the dome's ribs, the fountain and a rat |
| THE NAMES | satellite, grapple | a stealth break-in to Returns Desk Zero through the vents |
| RETURNS DESK ZERO | cart | wheel Brenda through a stampede on a trolley |
| CARRY THE ONE | bounce_shots, cars | escort a giant 1; the union banks tennis balls off digits |
| ROUNDING ERROR | camera | a stakeout in the Remainder Pit |
| DIVIDE BY ZERO | rocket_jump, grapple, quiz | an hour of NaN: gravity reverses, digits walk, and pop quizzes have no right answer |
| SPARE PARTS | grapple, lasso | chase a kidney along the neon sign line |
| SECOND OPINION | implants | the grid rash is Drift you can see |
| ARCADE LEGEND | spinbot | beat your own high score; the cabinet's cheat code is a Spinbot |
| BUY BACK | nvg, grapple | a pawn-shop heist past blinking jars |
| LAWN ORDER | fire, cars | mow fifty lawns to the millimetre |
| BLOCK PARTY | chicken_strike, frag_smoke | a wave survival block party with a three-legged race |
| KEEPING UP | cars | steal the right blue car from the Unpaid |
| RETURN ADDRESS | cars, grapple | follow the mailman at 4 km/h; the last letter is up the ruins by the Long Stairs |
| GROUNDHOG LUNCH | remote, loops | eleven chained interruptions in one loop; rewind the fork |
| COPY OF A COPY | camera | photocopy yourself out: a co-op puzzle with your own delayed copies |
| HOLD MUSIC | nvg, loops | follow a sound down the Backrooms Stairwell in the dark |
| QUALITY CONTROL | marbles, peels, lasso | beat a version of you with no jank by being janky |
| LIFEGUARD | lasso, void_edges | lasso rescues out of the void, falling in on purpose |
| STAKING CLAIMS | void_edges, grapple | turn 412 gnomes under fire before sundown |
| THE LAST BUS | cars | drive a bus out of the void against the clock |
| THE PUNCTUALITY MUSEUM | water_taser, grapple, verdict | flood the museum, ride the Pendulum of Punctuality into him |
| REPLY ALL | grapple, on_time | a chase through the Spire's pneumatic tubes |
| CASUAL FRIDAY | on_time | a stealth rhythm level: steal 300 ties on the clocks' beat |
| TEAM BUILDING | grapple, rocket_jump | a trust fall off a skyscraper you grapple out of at the last second |
| PARKING PERMIT | camera, cards | nineteen forms; the permit is a laminated Card Deck |
| THE REGION | cars | a heavy crate of reports the raiders want for armour |
| SMILES | grapple, cars | build a kite and fly it on the Spiral Freeway in a paper storm |
| THE FIRST INTERN | grapple, peels, marbles | extract Todd, then fight a bug that can't tell a banana from the floor |
| PERFORMANCE REVIEW | cars, grapple, lasso, knockback | a moving-convoy fight: grapple from rig to rig on the gantries |
| MANDATORY FUN | popper, chicken_strike, grapple | carnival games where losing is a fight; climb the Ferris wheel by grapple |
| UNLUCKY 13 | moon_boots, satellite, water_taser, grapple | a hot-zone climb up a fallen satellite; soak and tase its panels |

## Boss weaknesses

| boss | element | weapons that shine | weak points |
|---|---|---|---|
| MR. OVERTIME · HEAD OF TIMEKEEPING | water | water, taser, redline | the punch-clock face |
| MR. OVERTIME · HEAD OF TIMEKEEPING | knockback | minigun, blower, bowling | the steel plate over fight 1's wound |
| MR. OVERTIME · HEAD OF TIMEKEEPING | frost | snowball, remote, katana | the torn time card |
| MR. OVERTIME · FULLY BILLABLE | grapple | katana, lasso, redline | the heart (clock face), the back cables |
| MR. OVERTIME · REHIRED | water | water, taser, scales | the clock face |
| MR. DEPOSIT · THE LANDLORD | fire | cig, bow, chicken | the deposit box |
| THE STOMACH BISHOP · GUT CHOIR | slip | marbles, banana, bread | the ulcers, the baton hand |
| AUGUSTUS GRISTLE · FOUNDING PARTNER | verdict | scales, nailgun, lever | his open mouth |
| DON GRINALDI FAZZOLETTO · HEAD OF THE FAMILY | slip | katana, banana, slapper | the strings, the jaw |
| THE CART MOTHER · CUSTOMER SINCE 1999 | knockback | cart, bowling, shotgun | Brenda |
| FOREMAN REMAINDER · NUMBER WORKS | shock | taser, lever, burst | the calculator face |
| DOCTOR UPSELL · MEAT MECHANIC | sleep | bow, remote, akimbo | his back |
| THE HOA · HOMEOWNERS ASSOCIATION | fire | autoshot, cig, blower | the clipboard |
| THE PERPETUAL TUESDAY · LATE FOR A MEETING | frost | remote, snowball, katana | the envelope |
| R. CALE · EMPLOYEE OF THE QUARTER | slip | marbles, banana, lasso | the punch-clock heart |
| THE TALL GUY FROM HR · HUMAN RESOURCES | grapple | sniper, slipper, lasso | his face |
| PENNY PLOT · CLOSING AGENT | fire | cig, chicken, bow | the briefcase |
| THE MEETING ROOM · STEERING COMMITTEE | explosive | chicken, sniper, laser | the projector lens, the rotors |
| THE TWINS · VP OF SYNERGY | verdict | scales, revolver, slipper | the join |
| MARION HASK · CHIEF PUNCTUALITY OFFICER | verdict | scales, redline, remote | the donor organs, the archive cable |
| EMPLOYEE OF THE MONTH · THE UNPAID | grapple | lasso, blower, shotgun | the photocopier's green button |
| THE MORALE OFFICER · THE FUN DEPARTMENT | sleep | bow, snowball, remote | the lit head |
| UNLUCKY 13 · REMAINDER ORBITAL ASSET | water | water, taser, tennis | the targeting crown |
| THE MISSING TEXTURE · TODO | slip | banana, marbles, lasso | the patched squares |
| REVENUE PROTECTION · TICKETS, PLEASE | blood | bloodcross | the wrist joints, the eye housings, the Inspector |
